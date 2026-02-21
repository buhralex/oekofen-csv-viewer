# Stack Research

**Domain:** Client-side time-series CSV visualization — v1.1 Direct HTTP Download addition
**Researched:** 2026-02-21
**Confidence:** HIGH (core fetch/CORS mechanics verified against MDN, WICG spec, and Chrome developer blog; OekoFEN CORS header behavior is LOW confidence — undocumented by vendor, must be empirically confirmed)

---

## Overview

This document covers the stack additions required for v1.1 (direct OekoFEN HTTP API download). The v1.0 stack (uPlot, PapaParse, vanilla JS) is unchanged and documented separately. This update adds: `fetch()` for HTTP requests, `TextDecoder` for Windows-1252 decoding, a rate-limit timing pattern, and a settings UI pattern. No new libraries are required.

---

## CORS Reality Check: file:// Origin Fetching from 192.168.x.x

This is the most important concern. Here is the precise analysis.

### What browsers do when file:// fetches from http://192.168.x.x

**Origin classification:**
- A `file://` page has the origin `null` (opaque origin) in standard CORS terminology
- Per the Local Network Access (LNA) spec (WICG, Feb 2026 draft), `file://` URLs are explicitly classified as "local" — the same tier as loopback (127.0.0.1)
- Per MDN Secure Contexts, `file://` IS a "potentially trustworthy" origin — `window.isSecureContext` returns `true` for `file://` pages in Chrome and Firefox

**The critical rule:**
- LNA restricts requests that cross from a higher-privilege tier (public) to a lower-privilege tier (local/loopback)
- A `file://` page (classified as local) fetching from a local network device (192.168.x.x, also local) does NOT cross privilege tiers
- Therefore, Chrome's Local Network Access permission prompt does NOT apply to this scenario

**What actually blocks the request:**
The request will succeed or fail based on standard CORS rules, not LNA:

| Scenario | Outcome | Reason |
|----------|---------|--------|
| OekoFEN heater responds with `Access-Control-Allow-Origin: *` | SUCCESS | Standard CORS satisfied |
| OekoFEN heater responds with `Access-Control-Allow-Origin: null` | SUCCESS | Matches file:// opaque origin |
| OekoFEN heater returns no CORS headers | BLOCKED | Browser enforces standard CORS even for file:// origins |
| fetch with `mode: 'no-cors'` | USELESS | Response is opaque — body is unreadable, cannot parse CSV |

**OekoFEN heater CORS header status: LOW CONFIDENCE**
No community documentation, forum posts, or third-party integrations found that report what CORS headers the OekoFEN heater HTTP API actually returns. All existing community integrations (Python scripts, Perl, PHP, Home Assistant) are server-side and never run in a browser — CORS is irrelevant to them. The user must empirically verify by opening browser DevTools and checking the Network tab when the app makes a request.

**How to test empirically:**
```
1. Open the app in the browser (file:// or localhost)
2. Open DevTools → Network tab
3. Attempt a download
4. If blocked: the Console shows the specific CORS error
5. If "Access-Control-Allow-Origin" header is present in the response: it works
```

**Mitigation options if CORS is missing:**
1. Serve the app via `python -m http.server` (localhost origin) — some heaters may respond to `http://localhost` requests differently; no guaranteed fix
2. Use a minimal local proxy (Node.js one-liner or Caddy reverse proxy) — violates the "no server" constraint
3. Accept the limitation and document: "requires CORS-permissive firmware or user to serve via local server"
4. Browser extension approach — not viable for a distributed tool

**Recommended approach in requirements:**
- Implement the fetch logic unconditionally
- Detect the CORS failure and show a specific error message with actionable guidance: "If you see a CORS error in browser DevTools, your heater firmware may not allow browser access. Try serving this file via a local web server: `python -m http.server 8080`"

### Chrome Local Network Access (LNA) — Future risk

Chrome 142 is shipping a user permission prompt for "websites making requests to local network devices." However:
- This is targeted at **public** websites fetching local devices (to prevent CSRF attacks on routers)
- `file://` origin is classified as "local" in the LNA spec, not "public"
- The spec explicitly states local-to-local requests should not be subject to LNA gating
- The LNA spec (Feb 2026 draft) says it uses a permission prompt, NOT preflight — so no server-side `Access-Control-Allow-Private-Network` header is needed

**Confidence:** MEDIUM — the spec is clear but Chrome's implementation of the `file://` edge case has a note "Reevaluate after implementation experience." Monitor Chrome 138–142 release notes.

---

## Recommended Stack

### Core Technologies (unchanged from v1.0)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Vanilla JS (ES2020+) | — | All logic, state, DOM, fetch | Sufficient; no framework overhead; single-file constraint |
| uPlot | 1.6.32 | Chart rendering | Unchanged from v1.0 |
| PapaParse | 5.5.3 | CSV parsing | Unchanged from v1.0 |

### APIs Required for v1.1 (already in every modern browser — no new libraries)

| API | Purpose | Browser Availability | Notes |
|-----|---------|---------------------|-------|
| `fetch()` | HTTP GET requests to heater API | Baseline "Widely Available" since Jan 2020 (Chrome 42+, Firefox 39+, Safari 10.1+, Edge 14+) [HIGH confidence] | No polyfills needed. Replaces XHR with Promise-based API. |
| `TextDecoder('windows-1252')` | Decode heater CSV response (Windows-1252 encoding) | Baseline "Widely Available" since Jan 2020; `windows-1252` label is required by spec — all compliant browsers must support it [HIGH confidence] | Required because heater CSV uses Windows-1252. Use `response.arrayBuffer()` then `new TextDecoder('windows-1252').decode(new Uint8Array(buffer))`. |
| `localStorage` | Persist heater settings (IP, port, password) | Universal in all browsers supporting the app [HIGH confidence] | Already used in v1.0 for prefs. Extend same pattern. |
| `AbortController` | Timeout/cancel in-flight fetch requests | Baseline "Widely Available" since Jan 2020 [HIGH confidence] | Implement a timeout (e.g., 10s) on every fetch to prevent hung UI if heater is unreachable. |
| `setTimeout` | Rate-limit enforcement (2500ms minimum between requests) | Universal [HIGH confidence] | No library needed — see pattern below. |

### Supporting Libraries

**No new libraries recommended.** All required functionality is available via built-in browser APIs. Adding a dependency for rate-limiting or settings UI would be disproportionate for this scope.

---

## Patterns

### 1. Fetch with Timeout and Windows-1252 Decoding

```javascript
const FETCH_TIMEOUT_MS = 10_000; // 10 seconds

async function fetchHeaterCsv(ip, port, password, command) {
  const url = `http://${ip}:${port}/${password}/${command}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

  try {
    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    // Decode Windows-1252 (heater CSV encoding)
    const buffer = await response.arrayBuffer();
    return new TextDecoder('windows-1252').decode(new Uint8Array(buffer));

  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') throw new Error('Request timed out — heater unreachable');
    throw err; // Re-throw for caller to handle (CORS, network errors, etc.)
  }
}
```

**Why `arrayBuffer()` not `text()`:** `response.text()` assumes UTF-8. The heater CSV uses Windows-1252 (confirmed by v1.0 file loading experience with German special characters). `arrayBuffer()` + `TextDecoder` is the only correct approach.

### 2. Rate-Limit Pattern (2500ms minimum interval)

The requirement is a minimum 2500ms between requests — not a queue, since this is a single-user manual trigger app. A simple "last request timestamp" guard is sufficient. No queue implementation needed.

```javascript
let lastRequestTime = 0;
const MIN_REQUEST_INTERVAL_MS = 2500;

async function rateLimitedFetch(ip, port, password, command) {
  const now = Date.now();
  const elapsed = now - lastRequestTime;

  if (elapsed < MIN_REQUEST_INTERVAL_MS) {
    const wait = MIN_REQUEST_INTERVAL_MS - elapsed;
    await new Promise(resolve => setTimeout(resolve, wait));
  }

  lastRequestTime = Date.now();
  return fetchHeaterCsv(ip, port, password, command);
}
```

**Why not a queue:** A queue implies multiple callers competing. This app has one user clicking one button. A timestamp guard covers the requirement with 6 lines of code instead of a 40-line class. If the user clicks again while a request is in-flight, disable the button (simplest) or reject with a message.

**Why not `setInterval`:** Interval-based polling is not in scope — this is a manual on-demand download, not streaming.

### 3. Settings UI Pattern (Vanilla JS, No Framework)

A lightweight slide-in panel pattern using a `<dialog>` or `<aside>` element, toggled by a button, with `localStorage` read/write on open/save.

```javascript
// Save
function saveSettings(ip, port, password) {
  try {
    localStorage.setItem('oekofen_settings', JSON.stringify({ ip, port, password }));
  } catch (e) {
    console.warn('[saveSettings] localStorage unavailable:', e);
  }
}

// Load (with defaults)
function loadSettings() {
  try {
    const raw = localStorage.getItem('oekofen_settings');
    if (!raw) return { ip: '', port: '4321', password: '' };
    return JSON.parse(raw);
  } catch (e) {
    return { ip: '', port: '4321', password: '' };
  }
}
```

**Panel toggle:** Use CSS `transform: translateX(100%)` for hidden state, `transform: translateX(0)` for visible, with a `transition`. No JavaScript animation library needed.

**Form validation inline:** Validate IP format and port range on the `save` button click. Use `pattern` attribute on `<input>` for basic browser-native validation, plus JS check before `fetch()` is called.

**No `<dialog>` element:** While `<dialog>` is now widely supported (baseline 2022), a simple `<aside>` with CSS show/hide avoids focus-trapping complexity that is unnecessary for this single-panel settings use case. Use whichever approach matches the existing code style.

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `fetch({ mode: 'no-cors' })` | Response is opaque — body is `null`, status is 0; CSV cannot be read | Standard `fetch()` — if CORS fails, show specific error |
| XHR / `XMLHttpRequest` | Promise-based `fetch()` is cleaner; both have identical CORS behavior so there is no CORS advantage to using XHR instead | `fetch()` |
| Any rate-limit library (bottleneck, p-throttle, etc.) | Adds a dependency for 6 lines of logic; no `npm` in this project | `Date.now()` + `setTimeout` inline |
| `response.text()` for the heater response | Assumes UTF-8; heater returns Windows-1252 | `response.arrayBuffer()` + `TextDecoder('windows-1252')` |
| Proxy servers / CORS proxy services | Violates "no server" constraint; exposes heater password to third-party service | Serve locally via `python -m http.server` if needed |
| `targetAddressSpace: 'local'` fetch option | This is for mixed-content exemption (HTTPS page fetching HTTP device); irrelevant for file:// or http://localhost origin | Not needed |

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `fetch()` + `TextDecoder` | `XMLHttpRequest` with `responseType: 'arraybuffer'` | XHR works identically for this use case. Switch only if an older browser compatibility requirement emerges that predates Fetch (unlikely — Fetch is available everywhere the app already runs). |
| Timestamp-guard rate limiter | Full async queue (e.g., `p-queue`) | Use a queue only if the app ever needs to batch multiple automatic downloads in sequence. For manual single-click triggers, a timestamp guard is simpler and sufficient. |
| Custom `<aside>` settings panel | Alpine.js reactive form | Use Alpine.js if the number of settings grows significantly (>5 fields) or if reactivity between settings and download state becomes complex. Not needed for IP + port + password. |
| localStorage JSON blob for settings | Individual `localStorage` keys per setting | Individual keys work but make atomic save/restore harder. A single JSON key matches the existing `PREFS_KEY` pattern used in v1.0. |

---

## Stack Patterns by Variant

**If the heater returns no CORS headers (fetch blocked):**
- Show a specific error message identifying CORS as the cause
- Instruct user to serve the file via `python -m http.server 8080` and open `http://localhost:8080`
- Note: serving from localhost does NOT fix missing heater CORS headers — the heater must return `Access-Control-Allow-Origin` regardless of origin. The real fix is at the heater (firmware) or via a local proxy.

**If the heater is on a non-standard port (not 4321):**
- Default port to `4321` in the settings UI (most common OekoFEN default)
- Allow user to change — do not hardcode

**If the user opens the file via a local web server (http://localhost):**
- `window.isSecureContext` is `true` (same as file://)
- Chrome LNA does not apply (localhost is in the loopback tier, same classification as file://)
- All CORS rules still apply identically — heater must still return CORS headers

**If Chrome 142 adds a permission prompt for local network access:**
- The prompt applies to public-origin pages fetching local devices
- `file://` is classified as local, not public — the prompt should NOT appear
- Monitor Chrome 138 release notes (opt-in testing available) to confirm empirically

---

## Version Compatibility

| API | Works With | Notes |
|-----|-----------|-------|
| `fetch()` | Chrome 42+, Firefox 39+, Safari 10.1+, Edge 14+ | All modern browsers that can run uPlot/PapaParse already have fetch. No compat gap. |
| `TextDecoder('windows-1252')` | All browsers that implement the Encoding API (same baseline as fetch, Jan 2020) | `windows-1252` label is required by spec; all compliant browsers must support it |
| `AbortController` | Chrome 66+, Firefox 57+, Safari 11.1+, Edge 16+ | Slightly newer than fetch, but still well within modern browser support |
| `localStorage` | Universal | Already in use by v1.0 |

---

## Sources

- **WICG Local Network Access spec** (https://wicg.github.io/local-network-access/) — file:// classified as "local" tier; local-to-local requests not gated by LNA [HIGH confidence — spec is the primary source]
- **Chrome Developer Blog: Local Network Access** (https://developer.chrome.com/blog/local-network-access) — Chrome 138 opt-in, Chrome 142 launch, permission prompt details [HIGH confidence]
- **Chrome Developer Blog: Private Network Access preflights** (https://developer.chrome.com/blog/private-network-access-preflight) — `Access-Control-Allow-Private-Network` header requirement [HIGH confidence]
- **MDN: Secure Contexts** (https://developer.mozilla.org/en-US/docs/Web/Security/Secure_Contexts) — file:// is a potentially trustworthy origin [HIGH confidence]
- **MDN: TextDecoder** (https://developer.mozilla.org/en-US/docs/Web/API/TextDecoder) — Baseline Widely Available since Jan 2020 [HIGH confidence]
- **MDN: Encoding API Encodings** (https://developer.mozilla.org/en-US/docs/Web/API/Encoding_API/Encodings) — windows-1252 is a required label; all compliant browsers must support it [HIGH confidence]
- **MDN: CORS error — request not HTTP** (https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS/Errors/CORSRequestNotHttp) — opaque origin behavior for file:// [HIGH confidence]
- **WebSearch: OekoFEN CORS headers** — No empirical data found; all community integrations are server-side [LOW confidence — must be verified on actual device]

---

## Open Questions (Require Empirical Verification)

1. **Does the OekoFEN heater return `Access-Control-Allow-Origin: *` in its CSV responses?**
   - Cannot be determined from any public documentation or community reports
   - Must be tested: open DevTools on the actual device's local network, trigger a download, inspect Network tab
   - This is the single most critical unknown for v1.1

2. **Does the heater use `Content-Type: text/csv; charset=windows-1252` or an unspecified charset?**
   - Determines whether `response.text()` could work (if heater correctly declares charset in Content-Type header) vs. `arrayBuffer()` + `TextDecoder`
   - Use `arrayBuffer()` + `TextDecoder` regardless — safer and correct even if Content-Type is wrong

3. **What are the exact OekoFEN CSV endpoint names and rate-limit behavior?**
   - The milestone context specifies: `log_today`, `log_yesterday`, `log0`, `log1`, `log2`, `log3`
   - The 2500ms rate-limit requirement comes from user/device knowledge, not found in any API docs
   - Confirm these names against the actual device if possible

---

*Stack research for: OekoFEN CSV Viewer v1.1 — direct HTTP download addition*
*Researched: 2026-02-21*
