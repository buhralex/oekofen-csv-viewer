# Feature Research

**Domain:** Settings panel + direct HTTP device fetch for browser-based IoT diagnostic tool (v1.1 milestone)
**Researched:** 2026-02-21
**Confidence:** HIGH (UX patterns from NN/G, Smashing Magazine, LogRocket; browser security from Chrome dev docs; OekoFEN API from community repositories)

---

## Context

This document covers **new features only** for v1.1. The v1.0 feature landscape (drag-drop, chart, zoom, minimap, persistence) is documented in the original FEATURES.md dated 2026-02-17. This file focuses entirely on:

1. Settings panel (IP, Port, API Password)
2. Direct CSV download from OekoFEN HTTP API
3. Log period selector (Today / Yesterday / Log 0–3)

The tool is a single `index.html` opened directly from disk (`file://` origin). It talks to a heater at a local network IP address over HTTP. This context drives every UX and technical decision below.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that any "connect to a local device" settings flow must have. Missing any of these makes the flow feel broken or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Settings form: IP, Port, Password fields | Every local-device tool requires these three values; users expect them together in one place | LOW | Text inputs; Port defaults to `4321`; Password is text (not hidden — device credential, not user auth) |
| Save settings to localStorage | Settings must survive page reload; re-entering credentials every time is a hard failure | LOW | Save on "Save" button click, not on every keystroke |
| Pre-fill form from saved settings on open | Opening settings a second time should not require retyping; shows the currently saved values | LOW | Read from localStorage at modal/panel open time |
| Clear visual entry point to settings | Users need to find settings before they can use direct download; if it is buried, the feature does not exist | LOW | Two entry points: a gear/settings button on the drop-zone card AND an icon in the app header |
| Download feedback: loading state on the button | Fetching over a local network takes 0.5–5 seconds; without a spinner the user does not know if the click registered | LOW | Disable button, show spinner or "Downloading…" label during fetch |
| Error feedback: human-readable message | "Failed to fetch" is a browser internal error string, not user feedback; users need to know what went wrong and what to do | MEDIUM | See error cases section below |
| Log period selector with labeled options | Users need to pick between Today, Yesterday, and older archived logs; the option names must be self-explanatory | LOW | Dropdown (`<select>`) with six options: Today, Yesterday, Log 0, Log 1, Log 2, Log 3 |
| Rate-limit enforcement (2500ms between requests) | The OekoFEN API documentation and community implementations show the device has documented rate limits; violating them causes the device to stop responding | LOW | Track `lastFetchTime`, disable download button for remainder of cooldown window |
| Auto-load chart after successful download | Fetching a CSV and then requiring the user to also drag it somewhere defeats the purpose; the fetch-and-load must be one action | LOW | On successful fetch, pipe the CSV text directly into the existing parse pipeline |

### Differentiators (Competitive Advantage)

Features beyond the minimum that meaningfully improve the experience for this specific tool's users.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| "Test connection" button in settings | Lets users verify IP/Port/Password before attempting a log download; surfaces configuration errors immediately with a clear diagnosis | MEDIUM | Fetches `/{password}/all` (JSON endpoint, small payload); checks HTTP status; shows success/failure inline in the settings panel |
| Cooldown progress indicator | Shows time remaining before next request is allowed; prevents confusion when button is disabled after a fetch | LOW | A small text label "Available in 2s" updating every 500ms, or a disabled button with a timer badge |
| Persist last-used log period | If a user always downloads "Today", remembering that selection avoids a dropdown interaction every time | LOW | Store last-used `logCommand` in localStorage alongside connection settings |
| Settings panel shows current connection status | After a successful download, show a small status indicator (IP + last fetched time) so user knows what is connected | LOW | Cosmetic label in header or settings panel |
| Graceful file:// CORS instruction | The browser may block HTTP fetches from a `file://` origin depending on browser version and OS; a clear actionable message ("Open in a local server" or "Use Chrome with --allow-file-access-from-files") beats a blank error | HIGH | Detecting CORS vs network-down vs bad password requires careful error classification; see Pitfalls |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Password field masked (type="password") | "It's a password, hide it" | This is a device API token embedded in the URL, not a user account credential. Masking it makes copy-paste harder and provides no security benefit (the password is in localStorage in plaintext and appears in the URL in network requests anyway). Users need to see it to verify they typed it correctly | Use `type="text"`; label it clearly as "API Password" not "User Password" |
| Auto-save on every keystroke | "Feels more responsive" | Mid-typing state gets saved; if the user types half a new IP, the old working settings are destroyed and future fetches break silently | Save only on explicit "Save" action; validate format first |
| HTTPS/mixed-content proxy | "Just proxy through a server to avoid CORS" | Violates the zero-server constraint; introduces a dependency that breaks the single-file deployment model | Accept that the tool must be served from HTTP (not `file://`) for direct download to work; document this clearly |
| Auto-retry on failure | "If it fails, just try again" | The heater rate-limits; retrying immediately will hit the rate limit and make the error worse; retry after a timeout looks like a hang | Show the error immediately, let the user decide to retry; enforce the 2500ms cooldown between attempts |
| Real-time polling / auto-refresh | "Refresh the chart every 5 minutes automatically" | Polling adds background network activity, breaks the on-demand diagnostic model, and fights the rate limit; the heater produces a complete 1-day CSV at any point in the day (not real-time streams) | Keep fetch as an explicit user-triggered action |
| Multi-device support (save multiple heaters) | "What if I have two heaters?" | Complexity of a device list for an edge case; complicates the settings UI; the current user has one heater | Single connection profile is correct for the stated use case; no evidence of multi-device need |

---

## Feature Dependencies

```
[Settings: IP + Port + Password saved]
    └──required-by──> [Test Connection button]
    └──required-by──> [Log Period Selector + Download button]
                          └──required-by──> [Rate Limit Enforcement]
                          └──required-by──> [Download Loading State]
                          └──required-by──> [Error Feedback]
                          └──on-success──> [CSV Parse pipeline (existing v1.0)]
                                               └──on-success──> [Chart render (existing v1.0)]

[Rate Limit Enforcement]
    └──enhances──> [Cooldown Progress Indicator]

[Settings Entry Point (drop zone + header)]
    └──requires──> [Settings panel/modal exists]
```

### Dependency Notes

- **Settings must exist before download can be attempted:** There is no point rendering the download UI if the user has no saved connection. Consider auto-opening settings if connection fields are empty when the user first interacts with the download area.
- **Rate limit enforcement is mandatory, not optional:** The OekoFEN device rate limits are a hard technical constraint, not a UX nicety. If enforcement is skipped, users who double-click or retry quickly will hit a silent API failure.
- **The download flow feeds the existing v1.0 CSV pipeline:** No new parse logic is needed. The fetched CSV text can be handed directly to the PapaParse call that drag-drop uses. This dependency means the download result must be a string in the same format as a drag-dropped file.
- **Test connection is independent of log download:** It uses a different endpoint (`/all` JSON) and is only a diagnostic helper. Build it after the download flow works.

---

## MVP Definition

### Launch With (v1.1)

Minimum viable direct-download feature — what gets the user from "no files" to "chart loaded from heater" without requiring manual file export.

- [ ] Settings panel (modal) — IP, Port, API Password fields, Save button, loads from localStorage
- [ ] Settings entry point on drop-zone card ("Connect to heater" button)
- [ ] Log period selector dropdown on drop-zone (Today, Yesterday, Log 0, Log 1, Log 2, Log 3)
- [ ] Download button: triggers `fetch()` to `http://{ip}:{port}/{password}/{command}`, loads result into chart
- [ ] Loading state on download button during fetch
- [ ] Error feedback for: wrong IP/offline, wrong password (403 vs connection refused), timeout
- [ ] Rate limit enforcement: 2500ms cooldown between requests
- [ ] Settings entry point in app header (for accessing settings after a file is loaded)

### Add After Validation (v1.1.x)

Add once the basic download flow is confirmed working against a real device.

- [ ] Test connection button in settings panel — trigger: users report trouble knowing if their settings are correct
- [ ] Cooldown timer indicator — trigger: users confused by disabled button after a fetch
- [ ] Persist last-used log period — trigger: observed repeated same-period selections in use

### Future Consideration (v2+)

- [ ] Graceful file:// origin detection with actionable instructions — requires understanding actual browser behavior across Chrome/Firefox/Edge; defer until real user reports confirm it is needed
- [ ] Connection status indicator in header — cosmetic; defer until core flow is stable

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Settings form (IP, Port, Password) | HIGH | LOW | P1 |
| Save / load from localStorage | HIGH | LOW | P1 |
| Settings entry point (drop zone) | HIGH | LOW | P1 |
| Log period dropdown | HIGH | LOW | P1 |
| Download button + fetch | HIGH | MEDIUM | P1 |
| Loading state during fetch | HIGH | LOW | P1 |
| Error feedback (human-readable) | HIGH | MEDIUM | P1 |
| Rate limit enforcement (2500ms) | HIGH | LOW | P1 |
| Settings entry point (app header) | MEDIUM | LOW | P1 |
| Test connection button | MEDIUM | MEDIUM | P2 |
| Cooldown progress indicator | LOW | LOW | P2 |
| Persist last-used log period | LOW | LOW | P2 |
| Connection status in header | LOW | LOW | P3 |
| file:// origin detection + instructions | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for v1.1 launch
- P2: Add once v1.1 download flow is validated
- P3: Nice to have, future consideration

---

## UX Pattern Decisions

### Settings panel: modal, not slide-in

**Decision:** Modal dialog, not a slide-in side panel.

**Rationale:** Settings configuration requires focused attention — the user should not be looking at the chart or drop zone while changing credentials. The modal's blocking nature is correct here. Slide-in panels are better for non-blocking workflows where users need to reference underlying content simultaneously. Settings for a connection profile is a discrete, complete action: open, fill, save, close. The existing picker modal in v1.0 establishes this pattern as the project's standard.

**Implementation:** Reuse the existing modal component structure from the v1.0 picker modal. Same backdrop, same close behavior (X button + backdrop click + Escape key).

### Log period selector: `<select>` dropdown

**Decision:** A native HTML `<select>` element with six labeled options.

**Rationale:** Six fixed options is exactly the use case where a `<select>` dropdown is correct. There is no free-text entry, no date math, no calendar needed. The options are named by the device's own API commands; mapping them to human labels (Today, Yesterday, Log 0–3) is the only needed abstraction. A segmented button control would require six segments — too wide. A custom dropdown adds JavaScript for no gain.

**Labels:**
- `log_today` → "Today"
- `log_yesterday` → "Yesterday"
- `log0` → "Log 0 (2 days ago)"
- `log1` → "Log 1 (3 days ago)"
- `log2` → "Log 2 (4 days ago)"
- `log3` → "Log 3 (5 days ago)"

Note: The exact age of log0–log3 depends on the device's rolling log behavior. The labels above are approximate. Consider labeling them "Archive Log 0–3" to avoid committing to specific age claims.

### Error states: inline in drop zone, not browser alert

**Decision:** Show error messages inline below the download button / selector area, not as `alert()` or a separate toast.

**Rationale:** The drop zone card already has visual space and the user's attention is there. Inline errors keep the context (which log period was selected, which button was clicked) visible alongside the error message. `alert()` is deprecated in practice for this use case. Toasts disappear before the user can act on them.

**Error message format:** Icon + short description + actionable hint.
- Connection refused / no response: "Cannot reach heater at {ip}:{port}. Check the IP and Port in Settings."
- 403 / unauthorized: "Access denied. Check the API Password in Settings."
- Timeout (>10 seconds): "Request timed out. The heater may be busy or rate-limited. Wait a moment and try again."
- CORS / fetch blocked: "Download blocked by browser. Open this file via a local HTTP server (e.g., python -m http.server)."
- Response not valid CSV: "Downloaded data is not a valid CSV file. The log period may be empty."

### Validation: on Save, not on keystroke

**Decision:** Validate settings fields only when the user clicks "Save", not while typing.

**Rationale:** IP address and port validation during typing interrupts users mid-entry (typing "192." triggers a false error before the address is complete). The form is short (3 fields). On-save validation is acceptable for a settings form that is opened infrequently. Remove the error state as soon as the user starts editing the field again.

**Validation rules:**
- IP: non-empty; loose format check (four octets or hostname)
- Port: numeric, 1–65535
- Password: non-empty

### Rate limit: disable button, show countdown

**Decision:** After any download attempt (success or failure), disable the Download button for 2500ms. Show a small "Available in Xs" label that counts down.

**Rationale:** The 2500ms cooldown is a device constraint, not a UX preference. Users who click again immediately need to understand why the button is not responding. A countdown communicates both "I know you want to click again" and "this is temporary." Without a countdown, a disabled button looks like a bug.

---

## Error Case Coverage

The full set of error states the download flow must handle:

| Error Condition | Root Cause | Detection Method | User Message |
|----------------|------------|------------------|--------------|
| Heater offline / wrong IP | Device not reachable at that IP | `fetch()` throws `TypeError: Failed to fetch` | "Cannot reach heater. Check IP and Port in Settings." |
| Wrong port | TCP connection refused | Same as above (browser does not distinguish) | Same message — "Check IP and Port" |
| Wrong API password | HTTP 4xx response (device returns error page) | `response.ok === false` or status 403/401 | "Access denied. Check the API Password in Settings." |
| Rate limit hit on device | Device stops responding or returns error | HTTP 429 or connection drop within 2500ms window | "Too many requests. Wait and try again." (should not occur if client enforces 2500ms) |
| Request timeout | Slow local network, device busy | `AbortController` with 10s timeout | "Request timed out. The heater may be busy." |
| CORS / mixed content block | Browser blocks HTTP fetch from file:// or HTTPS origin | `fetch()` throws, no response object, error message contains "CORS" | "Browser blocked the download. Serve this file over HTTP instead of opening directly." |
| Empty log period | Requested log (log2, log3) doesn't exist yet | HTTP 200 but response body is empty or minimal | "No data for this log period. The heater may not have recorded it yet." |
| Response is not CSV | Device returns HTML error page instead of CSV | HTTP 200 but body does not parse as semicolon-delimited CSV | "Downloaded data is not a valid CSV file." |
| Settings not configured | User clicks Download before entering settings | No IP in localStorage | Auto-open settings modal with a prompt: "Set up your heater connection first." |

---

## Browser Security Constraints (Critical Context)

These constraints are not UX choices — they are hard browser security boundaries that determine whether direct download is technically possible.

**Constraint 1: file:// origin and CORS**
When `index.html` is opened directly from disk (`file://` origin), browsers enforce strict cross-origin rules. Chrome and Firefox differ:
- Chrome: blocks HTTP fetches from `file://` origins in most configurations
- Firefox: allows same-folder file access but blocks cross-origin HTTP fetches

**Implication:** Direct download from a `file://` origin is likely to fail on Chrome. The settings panel must either detect this and show the correct instruction, or the tool must document that users should serve `index.html` via a local HTTP server (e.g., `python -m http.server` or VS Code Live Server) to use direct download.

**Confidence:** MEDIUM — Chrome's Local Network Access policy (shipping Chrome 138+) adds a permission prompt for local network fetches. Whether this applies to `file://` origins is not explicitly documented. Needs testing against a real browser + device.

**Constraint 2: Chrome Local Network Access (Chrome 138+)**
Chrome is adding a permission prompt for fetches from public origins to local network IPs. For a `file://` origin the behavior is currently unclear. For an HTTP-served origin at a private IP (e.g., `http://192.168.1.x:8000/index.html`), the permission prompt will appear on first fetch.

**Implication:** The first time a user downloads from the heater, they may see a browser permission dialog ("Allow this site to access devices on your local network?"). This should be documented in the settings panel as expected behavior, not a bug.

**Source:** [Chrome Local Network Access blog post](https://developer.chrome.com/blog/local-network-access) — Chrome 138 opt-in, Chrome 142 full launch.

---

## Competitor Feature Analysis

The closest analogues to this feature set are browser-based router admin UIs (ASUS, OpenWrt LuCI, pfSense) and tools like Home Assistant's device connection forms. None are direct competitors — they are UX reference points.

| Feature | Router admin UIs | Home Assistant | Our Approach |
|---------|-----------------|----------------|--------------|
| Settings form for local device | Inline page, not modal | Modal in onboarding flow | Modal (reuses existing picker pattern) |
| Test connection | Common — "Check" button | Yes — during setup | Differentiator (P2) |
| Loading state on fetch | Usually spinner next to button | Progress bar | Spinner/label in button |
| Error feedback | Often cryptic (HTTP error codes) | Usually helpful | Human-readable messages with actionable hints |
| Rate limit handling | Device-dependent, rarely client-enforced | N/A | Client-enforced 2500ms cooldown |
| Log period selector | Not applicable | N/A | Dropdown with 6 named options |

---

## Sources

- Chrome Local Network Access (permission prompt, Chrome 138+): https://developer.chrome.com/blog/local-network-access
- MDN CORS documentation: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS
- NN/G Progress Indicators article: https://www.nngroup.com/articles/progress-indicators/
- LogRocket Form Validation UX: https://blog.logrocket.com/ux-design/ux-form-validation-inline-after-submission/
- Smashing Magazine Inline Validation: https://www.smashingmagazine.com/2022/09/inline-validation-web-forms-ux/
- Adobe Commerce Slide-out Panels vs Modals: https://developer.adobe.com/commerce/admin-developer/pattern-library/containers/slideouts-modals-overlays
- LogRocket Modal UX Design Patterns: https://blog.logrocket.com/ux-design/modal-ux-design-patterns-examples-best-practices/
- OekoFEN JSON API community documentation: https://github.com/thannaske/oekofen-json-documentation
- OekoFEN stats project (API URL patterns): https://github.com/ohitz/oekofen-stats
- OekoFEN Python API library: https://github.com/ckarrie/oekofen-api
- TrackJS "Failed to fetch" error handling: https://trackjs.com/javascript-errors/failed-to-fetch/
- Mockplus Button State Design 2025: https://www.mockplus.com/blog/post/button-state-design

---
*Feature research for: Settings panel + direct HTTP CSV download — OekoFEN CSV Viewer v1.1*
*Researched: 2026-02-21*
