# Pitfalls Research

**Domain:** Client-side time-series chart viewer for OekoFEN pellet heater CSV data
**Researched:** 2026-02-17 (v1.0), 2026-02-21 (v1.1 HTTP API addendum)
**Confidence:** HIGH (critical pitfalls verified via multiple sources and official docs)

---

## Critical Pitfalls

### Pitfall 1: UTF-8 BOM Corrupts the First Column Header

**What goes wrong:**
The OekoFEN heater exports CSV files that may include a UTF-8 BOM (Byte Order Mark, `\uFEFF`) at the start of the file. When the file is read with `FileReader.readAsText()` defaulting to UTF-8, the BOM is prepended to the first column name. The header `AT [C]` becomes `\uFEFFAT [C]`. All code that looks up this column by exact name will silently fail — the column appears to be missing, returns `undefined`, or the series never renders.

**Why it happens:**
Windows tools (including whatever firmware the OekoFEN heater runs) commonly emit UTF-8-BOM files. The BOM is invisible in most text editors. PapaParse has a known issue (GitHub issue #840, #372) where UTF-8-BOM causes the first property name to be enclosed in an invisible character that breaks normal property access.

**How to avoid:**
After reading the file as `ArrayBuffer`, decode with `TextDecoder` and strip the BOM explicitly before passing to the parser:
```javascript
const decoder = new TextDecoder('utf-8');
let text = decoder.decode(arrayBuffer);
if (text.charCodeAt(0) === 0xFEFF) {
  text = text.slice(1);
}
```
Alternatively, use `FileReader.readAsText(file, 'utf-8')` and strip `\uFEFF` from the result string before parsing. Test with an actual heater-exported file, not a hand-crafted test file.

**Warning signs:**
- First column (date/time or outside temperature `AT [C]`) never appears in the chart
- `console.log(Object.keys(row)[0])` shows a key that looks correct but has length 1 greater than expected
- Charting series tied to the first column silently render empty

**Phase to address:**
CSV parsing phase (Phase 1 / foundation). Write a test that loads a real OekoFEN CSV file and asserts `Object.keys(parsed[0])[0] === 'AT [C]'` (no invisible prefix).

---

### Pitfall 2: German Decimal Commas Are Not Auto-Converted — Silent Wrong Values

**What goes wrong:**
The OekoFEN CSV uses commas as decimal separators (German locale): `23,5` means 23.5 degrees. JavaScript's `parseFloat('23,5')` returns `23` (truncates at the comma). If `dynamicTyping: true` is used in PapaParse, the values are silently parsed as integers. Temperature `23,5°C` becomes `23`, pump modulation `67,3%` becomes `67`. Charts render but show incorrect stepped/truncated data — hard to notice unless you know the expected values.

**Why it happens:**
`parseFloat()` and JavaScript's type coercion are not locale-aware. PapaParse's `dynamicTyping` uses `parseFloat` internally (confirmed in PapaParse GitHub issue #143). Developers test with their own locale and miss the bug.

**How to avoid:**
Never use `dynamicTyping: true` for this CSV. Parse all fields as strings, then apply a locale-aware numeric conversion:
```javascript
function parseGermanFloat(str) {
  if (str === '' || str === null || str === undefined) return null;
  // Replace thousand-separator dots first, then decimal commas
  return parseFloat(str.replace(/\./g, '').replace(',', '.'));
}
```
Apply this transform in a post-processing pass over every column that should be numeric. Validate by asserting a known temperature value from a real file (e.g., outside temp in winter should be a plausible fractional degree, not an integer).

**Warning signs:**
- All temperature and percentage values appear as whole numbers in charts
- The cursor tooltip shows `23` instead of `23.5` for a temperature reading
- Step-like artifacts in otherwise smooth temperature curves

**Phase to address:**
CSV parsing phase (Phase 1). Include a unit test: parse `"23,5"` through the conversion pipeline and assert the result is `23.5`.

---

### Pitfall 3: Timestamp Parsing Shifts by Hours Due to Timezone Interpretation

**What goes wrong:**
The OekoFEN CSV stores timestamps as `DD.MM.YYYY` date and `HH:MM:SS` time in separate columns. When reconstructed into a JavaScript `Date`, the naive approach produces a UTC-interpreted timestamp that shifts all data points by the local UTC offset. A user in UTC+1 (Germany) sees data shifted 1 hour forward; a user in a different timezone sees different shifts. A chart labeled "12:00" shows data that was recorded at 11:00 or 13:00.

**Why it happens:**
Per MDN: date-only ISO strings (e.g., `"2024-01-15"`) are interpreted as UTC midnight. Date-time strings without explicit timezone are interpreted as local time. Reconstructing timestamps from the CSV's `DD.MM.YYYY HH:MM:SS` format without explicit timezone handling means the result depends on the browser's local timezone. The heater data is inherently local time (the heater is in the user's house) but JavaScript `Date` has no notion of "local time without a timezone."

**How to avoid:**
Parse the date and time fields manually and store timestamps as Unix epoch milliseconds (local time relative to midnight, or as a fractional day offset). Do not use `new Date('YYYY-MM-DDTHH:MM:SS')` without explicitly appending a timezone. Since the data is local-time single-day data, the safest approach is to treat timestamps as minutes-since-midnight (a number 0–1439) for all internal chart indexing, and format display labels from the raw time string directly.

**Warning signs:**
- The first data point (00:00:00) appears at a non-zero position on the time axis
- The axis labels show times that are off by a whole number of hours from what the tooltip shows
- The chart looks correct in one timezone but wrong for a user in a different timezone

**Phase to address:**
CSV parsing phase (Phase 1). Charting axis configuration phase. Test by parsing a file and asserting the first row's timestamp maps to `00:00` and the last row's timestamp maps to `23:59`.

---

### Pitfall 4: Mixed Continuous/Discrete Series on the Same Y-Axis Makes Binary States Invisible

**What goes wrong:**
The CSV contains both continuous values (temperatures 0–90°C, percentages 0–100%) and discrete binary states (pump on/off: 0 or 1, status codes: 0–5). When all series share the same auto-scaled Y-axis, the binary state series become a flat line near zero that is visually indistinguishable from zero temperature. Users cannot see pump state changes at all.

**Why it happens:**
Chart libraries auto-scale the Y-axis to fit all visible series. If a boiler temperature of 80°C is visible alongside a pump state of 0 or 1, the axis spans 0–80+ and the binary series occupies only 1/80th of the chart height — effectively invisible. This is not a bug; it is the default correct behavior for a shared axis.

**How to avoid:**
Separate series into axis groups before the charting phase:
- **Left Y-axis:** Temperature values (°C range 0–100)
- **Right Y-axis or overlay band:** Percentage values (0–100%)
- **Step-plot overlay:** Binary states (0/1) rendered as shaded bands or step series on a fixed 0–1 sub-axis

For binary states, use a step-type series (not a line series) and render them as shaded background bands (e.g., a semi-transparent bar when the pump is ON). This communicates state more clearly than a thin line.

**Warning signs:**
- Pump or status series are flat lines at the bottom of the chart regardless of zoom level
- Users report "the pump state doesn't show up"
- Toggling a binary series on/off has no visible effect on the chart

**Phase to address:**
Chart rendering phase (Phase 2 / charting). Must be designed before choosing axis configuration. The parameter view grouping feature (Boiler, Heating Circuit, etc.) should pre-separate continuous vs. discrete series.

---

### Pitfall 5: 70-Series Re-render on Toggle Causes Perceptible Lag

**What goes wrong:**
When a user toggles a single series on or off in a chart with ~70 series, the library re-renders all visible series from scratch. On mid-range hardware this causes 200–800ms of jank per toggle, making the UI feel unresponsive. With animations enabled, this is worse — every toggle triggers a full animation cycle.

**Why it happens:**
Most charting libraries (Chart.js, Plotly) rebuild the entire canvas on any data or visibility change. At 70 series × 1440 points = 100,800 data points being re-rendered, Canvas 2D rendering without GPU acceleration is CPU-bound. Plotly is documented to struggle with performance beyond 10k points with overlays and tooltips (confirmed by SciChart blog comparison).

**How to avoid:**
- **Disable animations immediately** — `animation: false` or equivalent. This is a must, not optional. Re-rendering without animation is 3–5x faster.
- **Use a canvas-based library** — uPlot renders ~100k points at 10% CPU vs. Chart.js at 40% and ECharts at 70% (uPlot GitHub benchmarks).
- **Limit concurrent visible series** — Pre-built views should show only 5–10 relevant series, not all 70 simultaneously.
- **Defer full re-render** — Debounce toggle events by 50ms so rapid toggling of multiple series triggers only one re-render.

**Warning signs:**
- Toggling a series checkbox causes visible freeze of 0.5+ seconds
- Browser DevTools shows long tasks (>50ms) during toggle
- Frame rate drops below 30fps during zoom or pan

**Phase to address:**
Chart rendering phase (Phase 2). Performance benchmark with all 70 series loaded must be run early, before UX polish. If the chosen library fails the benchmark, switch libraries before building features on top of it.

---

## v1.1 Addendum: HTTP API Direct Download Pitfalls

*Added: 2026-02-21. Applies to: Settings panel + direct CSV download from OekoFEN HTTP API.*

The following pitfalls are specific to the v1.1 milestone: fetching CSV directly from the OekoFEN heater's HTTP API (`http://{ip}:{port}/{password}/{command}`) from a browser-loaded HTML file.

---

### Pitfall 6: CORS Blocks All Fetch Requests from file:// Origin to Local HTTP Devices

**What goes wrong:**
When the app is opened as `file://` and `fetch()` is called against `http://192.168.x.x:PORT/PASSWORD/log_today`, the browser blocks the request with a CORS error. The OekoFEN heater returns no `Access-Control-Allow-Origin` header (it is an embedded device with no CORS configuration), so the browser's preflight or response check fails. The error in the browser console is:

```
Access to fetch at 'http://192.168.x.x:4321/...' from origin 'null' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

The origin of a `file://` page is reported as `null` (opaque origin), per the Fetch Standard. A server that returns `Access-Control-Allow-Origin: *` would allow this, but the OekoFEN heater returns no such header. The request is therefore always rejected by the browser security model, regardless of what the heater actually returns.

**Why it happens:**
Modern browsers (Chrome, Firefox) treat all `file://` pages as having opaque origins (a security change introduced after CVE-2019-11730). Cross-origin requests from opaque origins are blocked unless the server explicitly allows them via CORS headers. Since the OekoFEN heater is an embedded device that cannot be configured to add response headers, there is no way to make the server compliant.

**How to avoid:**
Serve `index.html` from a local HTTP server (`localhost`) instead of opening it as `file://`. When the page origin is `http://localhost`, it can make cross-origin requests to a local IP address. This does NOT require any changes to the heater. The user simply opens `http://localhost:8080` in their browser rather than opening the file directly.

Recommended: Include a one-line startup command in the UI or README:
```bash
# Python 3
python -m http.server 8080
# Then open http://localhost:8080 in browser
```

The app does not require a Node.js runtime or any server-side code — a static file server is sufficient.

**Warning signs:**
- Fetch calls immediately return a `TypeError: Failed to fetch` with no HTTP status code
- Browser console shows `CORS policy` or `null origin` in the error message
- The error appears before the heater has any chance to respond (blocked by browser, not by network)

**Phase to address:**
Phase 1 (Settings + HTTP foundation). This is a blocker that must be discovered and documented BEFORE any download code is written. The phase requirement must specify that users serve the app from localhost for the download feature to work. Do not defer this discovery — it changes the deployment model.

---

### Pitfall 7: Chrome Local Network Access Blocks Requests Even from localhost (Chrome 142+)

**What goes wrong:**
Chrome 142 (released late 2025) introduced the Local Network Access (LNA) permission prompt. Even when served from `http://localhost`, fetching `http://192.168.x.x` requires the user to explicitly grant "local network access" permission via a browser permission dialog. If the user denies this prompt, or if the browser silently blocks the request before showing the prompt (e.g., because the heater does not respond to LNA preflight requests), all fetch calls fail with a network error.

The LNA specification requires the target device to respond to an OPTIONS preflight with `Access-Control-Allow-Private-Network: true`. The OekoFEN heater does not support this header. Chrome may block the request outright before showing any permission dialog.

**Why it happens:**
Chrome 142 added LNA as part of Private Network Access protections to prevent CSRF attacks against local devices. The permission is restricted to secure contexts. Whether `http://localhost` qualifies as a secure context for LNA purposes depends on Chrome's implementation, which treats localhost as a "potentially trustworthy origin." The heater's inability to respond with the required preflight header is the hard blocker.

**How to avoid:**
Test the app in Chrome 142+ with the LNA restriction enabled (`chrome://flags#local-network-access-check` set to "Blocking"). If blocked, serve the app from `https://localhost` using a self-signed certificate, which is more explicitly treated as a secure context. Alternatively, document that Firefox remains fully functional for the download feature (Firefox does not implement LNA as of early 2026). For Chrome specifically, users can grant the permission via site settings.

Note: Firefox 84+ allows `http://localhost` to make requests to local IP addresses without restriction.

**Warning signs:**
- Fetch works in Firefox but fails in Chrome 142+
- Chrome DevTools shows a request blocked with a "Private Network Access" or "Local Network Access" warning
- The permission prompt appears but disappears before the user can respond (caused by the heater not supporting the required preflight response)

**Phase to address:**
Phase 1 (Settings + HTTP foundation). Test explicitly in Chrome 142+ as part of phase acceptance criteria. Firefox should be documented as the primary supported browser for the download feature if Chrome LNA cannot be resolved.

---

### Pitfall 8: Rate Limit Violations Cause Silent Failure or 401 Response

**What goes wrong:**
The OekoFEN API enforces a minimum 2500ms interval between requests. Verified behavior (from community reports): exceeding this limit returns HTTP 401 with the body `"Wait at least 2500ms during requests"`. The developer writes `fetch()` calls in a loop or calls them in rapid succession when testing, receives 401 responses, and either does not check the status code (silently loads nothing) or writes confusing "Authentication failed" error messages to the user.

**Why it happens:**
During development, the natural impulse is to test by rapidly clicking the "Download" button or calling the fetch in a dev console. Each rapid invocation hits the rate limit. The 401 status is confusing because it is also the status code for authentication failure — a developer who gets 401 might add input validation or debug the URL format for hours before realizing it is a rate limit response.

**How to avoid:**
- Enforce the 2500ms minimum in code, not just in documentation. Store `lastFetchTimestamp` in module scope. Before any fetch, check `Date.now() - lastFetchTimestamp < 2500` and either queue the request or reject with a user-visible message ("Please wait before downloading again").
- Treat 401 responses as potentially rate-limit errors, not just authentication errors. Read the response body and display it: `"Wait at least 2500ms during requests"` is a clear, user-intelligible message if surfaced.
- Do not use automatic retry on 401. Retrying immediately will hit the rate limit again.

```javascript
const MIN_INTERVAL_MS = 2500;
let lastFetchTime = 0;

async function fetchFromHeater(url) {
  const now = Date.now();
  const elapsed = now - lastFetchTime;
  if (elapsed < MIN_INTERVAL_MS) {
    throw new Error(`Rate limit: wait ${Math.ceil((MIN_INTERVAL_MS - elapsed) / 1000)}s before next request`);
  }
  lastFetchTime = now;
  const response = await fetch(url, { signal: AbortSignal.timeout(10000) });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`HTTP ${response.status}: ${body || response.statusText}`);
  }
  return response.text();
}
```

**Warning signs:**
- Download button works the first time but fails on rapid subsequent clicks
- Error messages say "401" or "Unauthorized" when the password is definitely correct
- Logs show HTTP 401 with a 2500ms-related response body

**Phase to address:**
Phase 1 (HTTP fetch layer). Rate-limit enforcement must be part of the first working fetch implementation, not added later. Acceptance test: clicking "Download" twice in under 2500ms shows a user-friendly "please wait" message, not a cryptic error.

---

### Pitfall 9: Wrong Password Returns Ambiguous Response — Indistinguishable from Other Errors

**What goes wrong:**
When the user enters an incorrect API password, the OekoFEN heater returns an HTTP 404 or serves an empty response (exact behavior varies by firmware version and endpoint). The browser receives a 404 and the developer's generic error handler shows "Network error" or "File not found" — neither message communicates "the password is wrong." The user assumes the IP address is incorrect or the heater is offline, leading to hours of network debugging.

**Why it happens:**
The OekoFEN API uses the password as a URL path segment (`http://ip:port/PASSWORD/command`). A wrong password simply results in a path that does not exist on the device's HTTP server, which returns a 404 or empty body rather than an explicit authentication error. There is no `401 Unauthorized` response for a wrong password (the 401 is reserved for the rate-limit response, confusingly).

**How to avoid:**
- On 404: Do not say "Not found." Say "Could not retrieve data. Check that the API Password in Settings is correct, and that the IP address and port are reachable."
- On empty response body (HTTP 200 but zero bytes): Treat as a configuration error, not a parsing error. Message: "Heater returned no data — verify password and log period selection."
- On successful response: Validate that the first line looks like an OekoFEN CSV header (contains semicolons and expected column names) before passing to the CSV parser. A wrong password that returns an HTML error page would otherwise be parsed as a malformed CSV.

**Warning signs:**
- The error message says "404" or "Not Found" but the IP address and port are definitely reachable
- An empty string or HTML page is passed to the CSV parser, which produces zero rows or throws
- Switching from wrong to correct password "fixes" a 404 error

**Phase to address:**
Phase 1 (Settings UX + error handling). Error messages for 404, empty body, and non-CSV content must be written as specific user-facing strings, not generic HTTP status codes. Include a "Test Connection" button in the settings panel that validates the settings before the user attempts a download.

---

### Pitfall 10: fetch() Has No Default Timeout — Offline Heater Hangs UI Indefinitely

**What goes wrong:**
`fetch()` has no built-in timeout. If the heater's IP address is unreachable (heater powered off, wrong IP, network issue), the fetch promise never rejects — it simply waits. On a local network this can take 60–90 seconds before the OS TCP stack gives up. The user sees no feedback and eventually hard-refreshes the page, losing their current chart state.

**Why it happens:**
The browser's default TCP connection timeout is controlled by the operating system, not by the `fetch()` API. JavaScript code that does not explicitly set a timeout via `AbortController` gets no timeout at all. Many developers forget this because on fast stable networks fetch calls resolve within milliseconds.

**How to avoid:**
Always pass `AbortSignal.timeout(ms)` to every fetch call targeting the heater:

```javascript
const response = await fetch(url, {
  signal: AbortSignal.timeout(10000)  // 10 seconds
});
```

`AbortSignal.timeout()` is supported in all modern browsers (Chrome 103+, Firefox 100+, Safari 16+). On timeout, the fetch rejects with a `TimeoutError` DOMException (not a standard `Error`). Catch it specifically:

```javascript
try {
  const response = await fetch(url, { signal: AbortSignal.timeout(10000) });
} catch (err) {
  if (err.name === 'TimeoutError') {
    showError('Heater did not respond within 10 seconds. Check IP address and network connection.');
  } else if (err.name === 'TypeError') {
    showError('Network error: could not connect to heater. Is the IP address correct?');
  } else {
    throw err;  // unexpected — re-raise
  }
}
```

A `TypeError: Failed to fetch` (distinct from `TimeoutError`) means the connection was refused outright or the CORS check failed.

**Warning signs:**
- The download button appears to "do nothing" for a long time with no loading indicator
- Fetch calls never reject during testing when the target IP is unroutable
- Network tab in DevTools shows a request in "Pending" state for over 30 seconds

**Phase to address:**
Phase 1 (HTTP fetch layer). Timeout must be applied at the first implementation of any fetch call. Acceptance test: disconnect from the network or target a non-existent IP; the UI should display an error message within 10–15 seconds.

---

### Pitfall 11: localStorage Stores the API Password in Plaintext — Visible to Anyone with DevTools

**What goes wrong:**
The API password is stored in `localStorage` as plaintext. Any person who opens the browser on the user's computer can open DevTools (F12 → Application → Local Storage) and read the password. On a shared family or work computer, this exposes the heater's control password to every other user of the browser profile.

**Why it happens:**
`localStorage` provides no encryption. It is always accessible to any JavaScript running on the page and to anyone using DevTools. Developers use it because it is simple and persistent, without considering that credentials stored there are equivalent to a plaintext file on disk accessible to all browser users.

**How to avoid:**
Assess the actual threat model before deciding on mitigation:

- **If the threat is "other people using the same computer":** `localStorage` is adequate. The OekoFEN API password is a low-stakes credential — it provides read access to heating log data and could allow someone to query the heater, not access anything outside the local network. For a single-user diagnostic tool on a home computer, the simplicity of `localStorage` is acceptable.
- **If the threat is "XSS on the page":** This is a single-file static HTML app with no CDN dependencies. The XSS attack surface is minimal. `sessionStorage` (erased on tab close) would reduce persistence but not XSS risk.
- **If the threat is meaningful:** Use `sessionStorage` so the password is not persisted after the browser tab is closed. Require re-entry each session.

For v1.1, use `localStorage` with explicit documentation that the password is stored unencrypted. The settings panel should display a note: "Password saved locally (unencrypted)." Do not implement encryption — Web Crypto with a user-derived key would add complexity without meaningfully increasing security in a browser-only app where the key must also be stored somewhere.

**Warning signs:**
- No mention of storage security in the settings UI
- Users asking "is my password secure?" — indicates the concern exists and should be addressed in copy

**Phase to address:**
Phase 1 (Settings panel). The UX copy must include a note about plaintext storage. The phase must make a documented decision about `localStorage` vs. `sessionStorage` for the password field. Do not leave this as an implicit default.

---

### Pitfall 12: Showing Raw Network Error Messages to the User Destroys UX

**What goes wrong:**
When fetch fails, the developer propagates the raw error message to the UI: `"TypeError: Failed to fetch"`, `"NetworkError when attempting to fetch resource"`, or `"Blocked by CORS policy: No 'Access-Control-Allow-Origin' header"`. These messages mean nothing to a heater owner who does not know what CORS is. The user cannot diagnose the problem and contacts support or gives up.

**Why it happens:**
Error handling is added quickly by catching the rejection and displaying `error.message` directly. The developer sees a meaningful message in the console during development and assumes users will understand it.

**How to avoid:**
Map every distinct failure mode to a user-friendly string before it reaches the UI:

| Error Condition | Raw Error | User-Facing Message |
|----------------|-----------|---------------------|
| CORS blocked (file:// origin) | `TypeError: Failed to fetch` | "Could not connect. Serve the app from a local web server (see instructions) instead of opening the file directly." |
| Network unreachable (wrong IP) | `TypeError: Failed to fetch` | "Could not reach the heater. Check the IP address and port in Settings." |
| Timeout (heater unresponsive) | `TimeoutError` | "Heater did not respond within 10 seconds. Is it powered on and connected to your network?" |
| Rate limit exceeded | `HTTP 401` | "Please wait a moment before downloading again (minimum 2.5s between requests)." |
| Wrong password | `HTTP 404` | "Could not retrieve log data. Verify the API Password in Settings matches the heater's configured password." |
| Empty response | `HTTP 200, 0 bytes` | "Heater returned no data. The log for this period may not be available yet." |
| Non-CSV response | `HTTP 200, HTML content` | "Unexpected response from heater. Check IP address and API Password." |

The `TypeError: Failed to fetch` case is particularly dangerous because it covers both "CORS blocked" and "network unreachable" — two very different problems. To distinguish: if the app is opened as `file://`, the CORS explanation is the likely cause. Check `window.location.protocol === 'file:'` before surfacing the error.

**Warning signs:**
- Error messages contain the words "TypeError", "CORS", "NetworkError", "Access-Control-Allow-Origin"
- Error handling uses `catch (e) { showError(e.message) }` without any mapping
- Testers report not knowing what to do when they see an error

**Phase to address:**
Phase 1 (HTTP fetch layer + Settings UX). All fetch error paths must be mapped to user-facing strings before the feature is considered done. Include an error message review as part of the phase acceptance criteria.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Use `split(';')` for CSV parsing instead of a proper library | No dependency | Fails on quoted fields, BOM, encoding edge cases — requires rewrite for any real OekoFEN file | Never — always use PapaParse or equivalent |
| Enable `dynamicTyping: true` in PapaParse | Fewer lines of code | Silent wrong values for German decimal commas | Never for this CSV format |
| Read file as `readAsText()` without BOM stripping | Simpler code | First column header broken on real heater files | Never — always strip BOM |
| Show all 70 series by default | Seems complete | Unreadable chart, performance problems, overwhelms users | Never — always use pre-built grouped views as default |
| Share one Y-axis for all series | Fewer config lines | Binary states become invisible lines | Never — axis grouping must be designed in from the start |
| Use `new Date(dateString)` directly | Concise code | Timezone-shifted timestamps, subtle off-by-hours bugs | Never — always parse date/time fields manually |
| Leave chart animations enabled | Polished look | Severe performance penalty with 70 series | MVP: disable immediately. Revisit only if library supports partial-series animation |
| Propagate raw `error.message` to the UI | Zero extra code | User sees "TypeError: Failed to fetch" — cannot diagnose the problem | Never — always map to a user-facing message |
| No fetch timeout (bare `fetch(url)`) | Simpler code | Browser hangs indefinitely when heater is offline | Never — always use `AbortSignal.timeout()` |
| No rate-limit check before fetch | Simpler code | User gets confusing 401 on rapid retries; heater may become unresponsive | Never — enforce 2500ms minimum in code |
| Store password in localStorage with no disclosure | Zero extra UX | Users don't know the password is plaintext; no informed consent | Only acceptable if the settings panel includes a plaintext-storage disclosure note |

---

## Integration Gotchas

Common mistakes when connecting to external data sources.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OekoFEN CSV encoding | Assume UTF-8 without BOM | Read as ArrayBuffer, detect and strip BOM before parsing |
| OekoFEN decimal format | Use JS `parseFloat()` or `dynamicTyping` | Custom `parseGermanFloat()` replacing `,` with `.` after stripping `.` thousand separators |
| OekoFEN timestamp format | Concatenate date+time and pass to `new Date()` | Parse `DD.MM.YYYY` and `HH:MM:SS` manually; store as minutes-since-midnight integer |
| OekoFEN header format | Assume clean ASCII column names | Normalize headers: strip BOM, trim whitespace, preserve brackets (e.g., `AT [C]` is a valid key) |
| OekoFEN status codes | Treat as numeric continuous values | Identify integer-only columns and classify as discrete/categorical before charting |
| File drag & drop | Only handle `drop` event | Must also call `event.preventDefault()` on `dragover` or the browser will navigate to the file |
| OekoFEN HTTP API from file:// | Call `fetch()` directly | Serve app from `http://localhost` — file:// origin is opaque and CORS-blocked by all browsers |
| OekoFEN HTTP API rate limit | Call API freely during testing | Enforce 2500ms minimum in code; treat 401 as rate-limit, not auth failure |
| OekoFEN wrong password | Show 404 as "Not Found" | Show "Check your API Password in Settings" — 404 is the wrong-password response |
| Fetch error messages | Display `error.message` directly | Map each error type to a specific user-facing string before display |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| All 70 series rendered simultaneously | 500ms+ toggle lag, browser freeze on load | Pre-built views with 5–10 series; toggle adds one at a time | At 20+ series with animations enabled |
| SVG-based charting library | Smooth at 5 series, sluggish at 20+ | Use Canvas 2D (uPlot) or WebGL (LightningChart) | Beyond 10 series, 1440 points each |
| Chart.js `animation: true` with many series | Every data change triggers multi-frame animation cycle | `animation: false` from day one | With 10+ series on update |
| No data decimation during zoom-out | All 1440 points rendered at full density when zoomed out to see only 100px range | Apply LTTB decimation: Chart.js has built-in plugin; uPlot does this automatically | Visible when user zooms out to full-day view with 20+ series |
| Tooltip showing all series values on cursor move | Tooltip renders 70 entries per mousemove, 60x/second | Limit tooltip to 5–10 closest/visible series; use amCharts `maxTooltipDistance` pattern | Any time all 70 series are visible |
| Re-parsing CSV on every chart interaction | 1440 rows × 70 columns re-parsed on series toggle | Parse once on load, store in typed arrays; never re-parse | Immediately noticeable — parse on load only |
| Fetch without timeout on offline heater | UI hangs for 60–90 seconds | Always use `AbortSignal.timeout(10000)` | Every time heater is unreachable |

---

## Security Mistakes

Domain-specific security issues for this project.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Password in localStorage with no disclosure | User not aware of plaintext storage; shared-computer exposure | Show "Password saved locally (unencrypted)" in settings UI |
| Logging password to console | Password visible in DevTools console to anyone who opens it | Never log the password or full API URL (which contains password as path segment) |
| Exposing full API URL in error messages | URL contains the API password as a path segment | Redact the password segment in any logged or displayed URL: `http://ip:port/****/command` |
| Fetching from public CORS proxy | CSV data (heating patterns) sent to third-party server | Never use external CORS proxies — serve app from localhost instead |

---

## UX Pitfalls

Common user experience mistakes in interactive time-series chart viewers.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing all 70 parameters at once with no grouping | Unreadable rainbow spaghetti chart; user cannot find relevant data | Pre-built views grouped by system (Boiler, Heating Circuit, Hot Water, Buffer, Pellet Unit) as primary entry point |
| Zoom resets when toggling a series | User loses their zoom context, has to zoom in again | Preserve zoom state across series visibility changes; only reset on explicit "Reset Zoom" action |
| No "Reset Zoom" affordance | User gets lost after deep zoom, cannot return to full day view | Always-visible "Reset Zoom" button, or double-click to reset |
| Cursor tooltip listing 70 values | Information overload; key values hidden in scroll | Show only values for currently visible series; collapse identical/zero values |
| Using line series for binary on/off states | Pump ON renders as a thin flat line at 1.0 — nearly invisible | Use step-type series + shaded background band for binary states |
| German column names renamed in UI without disambiguation | `HK1 VL Ist[C]` → "Flow Temperature" — user cannot verify which CSV column it is | Show original German CSV column name in tooltip or info panel alongside friendly label |
| Scroll zoom conflicts with page scroll | User tries to scroll down page, accidentally zooms chart instead | Require modifier key (Ctrl/Cmd) for scroll-to-zoom, or confine scroll zoom to within chart bounds with explicit focus |
| Settings panel with no "Test Connection" button | User enters wrong IP and only discovers the error when trying to download | Include a "Test Connection" button that runs a quick fetch and shows pass/fail before user attempts a download |
| Download button with no loading state | User clicks download, sees nothing happen, clicks again — triggers rate limit | Show spinner/progress indicator from first click; disable button during active fetch |
| Generic "Network error" on fetch failure | User cannot diagnose whether the issue is IP, password, or CORS | Detect `file://` protocol and offer specific guidance; map 404 to password hint |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **CSV parsing:** Visually seems to work — verify that the parsed first header key has no invisible BOM prefix (`key.charCodeAt(0) !== 0xFEFF`)
- [ ] **German decimals:** Chart renders temperatures — verify `23,5` in the source becomes `23.5` in the parsed data, not `23`
- [ ] **Timestamp axis:** Chart shows a time axis — verify the first data point maps to `00:00` and the 1440th maps to `23:59` regardless of the user's system timezone
- [ ] **Binary series visible:** Pump and status series are listed in legend — verify they are visually distinct when the state changes (not a flat invisible line)
- [ ] **Toggle performance:** Series toggle works — verify toggle completes in under 100ms with all 70 series loaded (measure with browser DevTools Performance tab)
- [ ] **Zoom state preserved:** Zoom works — verify toggling a series while zoomed in does not reset the zoom range
- [ ] **File drop on whole page:** Drop zone accepts files — verify that dropping outside the explicit drop zone does not navigate the browser away from the app (requires `dragover` prevention on `document`)
- [ ] **Umlaut headers render:** Parameters like `Außentemperatur` display correctly — verify no mojibake (`Ã¤` instead of `ä`) by loading a real file with umlauts
- [ ] **CORS tested from file://:** Download button works — verify behavior when app is opened as `file://` (must show the "serve from localhost" instruction, not a cryptic CORS error)
- [ ] **Rate limit enforced in code:** Download works once — verify that clicking download twice within 2500ms shows a user-friendly message, not a 401 error
- [ ] **Timeout set on fetch:** Download works on reachable heater — verify that fetching a non-existent IP shows an error within 10–15 seconds (not 90 seconds or forever)
- [ ] **Wrong password gives actionable error:** Download fails with wrong password — verify the error message says "Check your API Password" not "404 Not Found"
- [ ] **Password not logged:** Settings are saved — verify the browser console shows no log lines containing the API password or the full heater URL
- [ ] **No sensitive data in error messages:** An error occurs — verify the displayed error does not contain the raw API URL with the password as a path segment

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| BOM corruption discovered after charting built | LOW | Add one-line BOM strip at file read stage; all downstream code unaffected if keys were normalized |
| German decimal truncation found late | MEDIUM | Replace `dynamicTyping` with a post-parse transform pass; all consumers of parsed data need re-testing |
| Timezone shift discovered in production | MEDIUM | Replace `Date` usage with minutes-since-midnight integers throughout; axis formatting needs update |
| SVG library chosen and found too slow | HIGH | Replace charting library entirely; rebuild series config, zoom plugin, and tooltip integration |
| All-70-series-on-one-axis discovered late | MEDIUM | Axis grouping can be added without data model changes; requires chart config refactor and parameter view redesign |
| Chart animations causing lag found in testing | LOW | Single config change (`animation: false`); no architecture impact |
| CORS blocking discovered after download feature built | MEDIUM | Add localhost-serving instructions to README and UI; no code changes needed, but UX copy needs updating |
| Chrome LNA blocks requests in Chrome 142+ | LOW–MEDIUM | Document Firefox as primary browser for download feature; add a browser detection note in the UI |
| Rate limit violations discovered during QA | LOW | Add `lastFetchTime` guard before fetch call; 10 lines of code |
| Indefinite hang discovered when heater is offline | LOW | Add `AbortSignal.timeout(10000)` to the fetch call; one-line fix |
| Password visible in console logs | LOW | Remove `console.log` lines containing the URL or password; add password-redaction to URL display |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| BOM corrupts first column header | Phase 1: CSV Parsing | Unit test: parse real OekoFEN file, assert first key has no BOM prefix |
| German decimal commas silently truncated | Phase 1: CSV Parsing | Unit test: `parseGermanFloat("23,5") === 23.5` |
| Timestamp timezone shift | Phase 1: CSV Parsing | Integration test: first row timestamp = 00:00, last = 23:59, timezone-independent |
| Binary states invisible on shared Y-axis | Phase 2: Chart Rendering | Manual review: pump ON/OFF must be visually distinct from flat-zero |
| 70-series toggle performance lag | Phase 2: Chart Rendering | Benchmark: toggle 1 series in 70-series chart completes < 100ms |
| SVG library scale failure | Phase 2: Library Selection | Benchmark before first feature built on top of library |
| Scroll zoom conflicts with page scroll | Phase 3: UX Interactions | Manual test: scrolling the page near the chart does not trigger zoom |
| Tooltip overcrowding | Phase 3: UX Interactions | Manual test: cursor over chart with 10 visible series shows readable tooltip |
| Zoom resets on series toggle | Phase 3: UX Interactions | Test: zoom to a 1-hour window, toggle any series, verify zoom range unchanged |
| File drop navigates browser away | Phase 1: File Loading | Test: drop file outside drop zone, browser stays on app page |
| CORS blocks file:// fetch to HTTP device | v1.1 Phase 1: HTTP Foundation | Test fetch from file:// — must show localhost instruction; test from localhost — must succeed |
| Chrome LNA blocks localhost fetch | v1.1 Phase 1: HTTP Foundation | Test in Chrome 142+ with LNA flags; document Firefox as fallback |
| Rate limit violation returns confusing 401 | v1.1 Phase 1: HTTP Fetch Layer | Test: two clicks within 2500ms shows user-friendly message |
| Wrong password returns ambiguous 404 | v1.1 Phase 1: Settings UX | Test: wrong password shows "Check API Password" message, not "404" |
| fetch() hangs on offline heater | v1.1 Phase 1: HTTP Fetch Layer | Test: unreachable IP shows error within 10–15 seconds |
| Raw network errors shown to user | v1.1 Phase 1: Error Handling | Review all catch blocks: zero instances of raw `error.message` in UI |
| Password stored without disclosure | v1.1 Phase 1: Settings Panel | Settings UI shows "stored locally unencrypted" note |

---

## Sources

**v1.0 Sources:**
- [PapaParse GitHub Issue #840 — UTF-8-BOM string parsing corrupts first header](https://github.com/mholt/PapaParse/issues/840)
- [PapaParse GitHub Issue #372 — Unicode BOM messes up first property name](https://github.com/mholt/PapaParse/issues/372)
- [PapaParse GitHub Issue #143 — Numeric value with comma (European-formatted numbers)](https://github.com/mholt/PapaParse/issues/143)
- [uPlot GitHub — Performance benchmarks vs Chart.js and ECharts](https://github.com/leeoniya/uPlot)
- [Chart.js Performance Documentation — Decimation and animation flags](https://www.chartjs.org/docs/latest/general/performance.html)
- [MDN Date.parse() — UTC vs local time interpretation for date-only strings](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/parse)
- [SciChart Blog — Most charting libraries break at scale (Chart.js vs ECharts CPU/memory benchmarks)](https://www.scichart.com/blog/scale-up-with-high-performance-charting-library/)
- [amCharts Cursor Documentation — maxTooltipDistance for many-series tooltip control](https://www.amcharts.com/docs/v5/charts/xy-chart/cursor/)
- [CSVBox Blog — CSV encoding detection, BOM vs non-BOM accuracy](https://blog.csvbox.io/csv-detect-encoding/)
- [Chrome Developers — ArrayBuffer to String via TextDecoder encoding API](https://developer.chrome.com/blog/easier-arraybuffer-string-conversion-with-the-encoding-api)
- [Phare.io — Downsampling time series data, LTTB algorithm explained](https://phare.io/blog/downsampling-time-series-data/)
- [Chart.js Data Decimation Configuration — LTTB built-in support](https://www.chartjs.org/docs/latest/samples/advanced/data-decimation)
- [Grafana Documentation — Mixed time series data visualization, dual-axis guidance](https://grafana.com/docs/grafana/latest/visualizations/panels-visualizations/visualizations/time-series/)
- [SciChart Memory Best Practices — Destroy patterns for canvas-based charts](https://www.scichart.com/documentation/js/current/MemoryBestPractices.html)

**v1.1 Sources:**
- [MDN — Reason: CORS request not HTTP (file:// origin behavior)](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS/Errors/CORSRequestNotHttp)
- [MDN — Cross-Origin Resource Sharing (CORS)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)
- [WICG Local Network Access Specification — file:// treated as local secure context](https://wicg.github.io/local-network-access/)
- [Chrome Developers — New permission prompt for Local Network Access (Chrome 142)](https://developer.chrome.com/blog/local-network-access)
- [Chrome Developers — PNA deprecation trial ending (Chrome 132)](https://developer.chrome.com/blog/pna-permission-prompt-ot-end)
- [gHacks — Google Chrome 142 restricts local network access](https://www.ghacks.net/2025/10/29/google-chrome-142-restricts-local-network-access-and-changes-sync-on-desktop/)
- [OekoFEN JSON API community documentation — irregular connection issues, rate limit behavior](https://github.com/thannaske/oekofen-json-documentation/issues/3)
- [OekoFEN community API library (ckarrie)](https://github.com/ckarrie/oekofen-api)
- [MDN — AbortSignal.timeout() static method](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/timeout_static)
- [OWASP HTML5 Security — localStorage and sensitive data](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html)
- [Snyk — Is localStorage safe to use?](https://snyk.io/blog/is-localstorage-safe-to-use/)
- [MDN — HTTP 429 Too Many Requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/429)

---
*Pitfalls research for: Client-side time-series chart viewer (OekoFEN CSV) + v1.1 HTTP API direct download*
*Researched: 2026-02-17 (v1.0), 2026-02-21 (v1.1 addendum)*
