# Project Research Summary

**Project:** OekoFEN CSV Viewer — v1.1 Direct HTTP Download
**Domain:** Client-side time-series CSV visualization with direct device HTTP integration
**Researched:** 2026-02-21 (v1.1 update; v1.0 research: 2026-02-17)
**Confidence:** HIGH — with one explicitly bounded LOW-confidence gap (OekoFEN heater CORS headers, empirically unverifiable without a physical device)

## Executive Summary

The OekoFEN CSV Viewer v1.1 adds direct HTTP download from a local pellet heater to an already-shipped single-file vanilla JS app (`index.html`, 2,542 lines, v1.0). The core v1.0 stack (uPlot 1.6.32, PapaParse 5.5.3, vanilla JS) is correct, proven, and unchanged. The v1.1 addition requires zero new libraries — only browser-native APIs already in use or universally available: `fetch()`, `TextDecoder('windows-1252')`, `AbortController`, and `localStorage`. The dominant architectural move is extracting the existing `onFileAccepted()` pipeline body into a new shared `onCsvStringAccepted()` function so both the file-drop path and the new fetch path converge into a single validated pipeline without duplication. All v1.1 additions are additive — no existing v1.0 functionality changes except `onFileAccepted()` becoming a thin wrapper.

The recommended implementation sequence (settings persistence → settings modal → pipeline extraction → fetch logic → UI wiring) reflects hard code dependencies: `fetchCsv()` reads `_settings` which must be populated before any fetch attempt, and `onCsvStringAccepted()` must be verified regression-free before a second caller is added. The settings subsystem lives at module level in a dedicated `_settings` object with its own `'oekofen-viewer-settings'` localStorage key, explicitly isolated from `AppState` (which resets on every file load) and from `'oekofen-viewer-prefs'` (view state).

The single biggest risk is CORS. When `index.html` is opened as `file://`, browsers classify the origin as `null` (opaque) and block `fetch()` calls to the heater unless the heater responds with `Access-Control-Allow-Origin: *`. No community documentation confirms OekoFEN heaters return this header — all existing community integrations are server-side and never involve a browser. The correct mitigation is to serve the app from `http://localhost` via `python -m http.server` and document this clearly in the UI. Using `mode: 'no-cors'` is not a mitigation — it produces unreadable opaque responses. A second browser-specific risk is Chrome 142's Local Network Access permission prompt; the mitigation is to document Firefox as a fully functional alternative and monitor Chrome 138+ release notes for the `file://` edge-case outcome.

## Key Findings

### Recommended Stack

The v1.1 stack adds zero new libraries. All required functionality is in baseline browser APIs widely available since January 2020. The fetch pattern is `fetch(url, { signal: AbortSignal.timeout(10000) })` → `response.arrayBuffer()` → `new TextDecoder('windows-1252').decode(new Uint8Array(buffer))`. The `arrayBuffer()` path is mandatory because `response.text()` assumes UTF-8 and will corrupt German characters in the heater CSV. The rate limiter is a 6-line module-level timestamp guard — no queue, no library, no `setInterval`. Settings persistence extends the existing `localStorage` pattern with a new dedicated key to avoid lifecycle conflicts with view prefs.

See `.planning/research/STACK.md` for complete patterns with code examples.

**Core technologies:**
- Vanilla JS (ES2020+): all logic, state, DOM, fetch — sufficient for single-file constraint; no framework overhead
- uPlot 1.6.32: chart rendering — unchanged from v1.0; fastest canvas-based option for 70-series CSV data at this scale
- PapaParse 5.5.3: CSV parsing — unchanged; shared by both file-drop and fetch paths via `onCsvStringAccepted()`
- `fetch()` + `AbortController` / `AbortSignal.timeout()`: HTTP requests to heater — baseline widely available; 10s timeout mandatory to prevent UI hang on unreachable device
- `TextDecoder('windows-1252')`: decode heater CSV — heater uses Windows-1252; `response.text()` assumes UTF-8 and corrupts German characters; `arrayBuffer()` + `TextDecoder` is the only correct path
- `localStorage` (extended): settings persistence — new `'oekofen-viewer-settings'` key, kept strictly separate from existing `'oekofen-viewer-prefs'` to avoid lifecycle conflicts

**What not to use:**
- `fetch({ mode: 'no-cors' })` — response is opaque, body is unreadable
- `response.text()` for heater response — assumes UTF-8; incorrect for Windows-1252
- Any rate-limit library (bottleneck, p-throttle) — adds a dependency for 6 lines of logic
- External CORS proxy services — exposes heater password to third-party; violates no-server constraint

### Expected Features

The v1.1 feature set has a clear and well-reasoned P1/P2/P3 split. The MVP is tight. See `.planning/research/FEATURES.md` for the full prioritization matrix, UX pattern decisions, and error case coverage table.

**Must have — v1.1 launch (P1):**
- Settings modal (IP, Port, API Password) with localStorage save/load and pre-fill on re-open
- Settings entry points: gear icon on drop-zone card (before any file is loaded) and in app header (after chart is loaded)
- Log period selector dropdown: Today, Yesterday, Log 0, Log 1, Log 2, Log 3 (native `<select>`, six fixed options)
- Download button with loading state (spinner/disabled during fetch) — 0.5–5s latency requires visible feedback
- Error feedback covering all 8 failure modes: wrong IP/offline, wrong password (404), timeout, CORS block, rate limit hit, empty response, non-CSV response, settings not configured
- Rate limit enforcement: 2500ms minimum between requests — hard device constraint, not a UX preference; disable button for cooldown window

**Should have — post-validation additions (P2):**
- Test connection button in settings panel — uses `/all` JSON endpoint to validate settings without downloading a log
- Cooldown progress indicator — "Available in Xs" countdown label after a fetch attempt
- Persist last-used log period — reduces dropdown interaction for repetitive use

**Defer — v2+ (P3):**
- file:// origin detection with actionable per-browser instructions — complex browser-specific branching; defer until real user reports confirm need
- Connection status indicator in app header — cosmetic; build after core flow is confirmed stable

**Confirmed anti-features (do not build):**
- `type="password"` on API password field — credential appears in URL path anyway; masking impedes verification with no security gain
- Auto-save settings on keystroke — mid-typing state destroys working configuration
- Auto-retry on failure — hits rate limit immediately, making the error worse
- Real-time polling / auto-refresh — fights the 2500ms rate limit; heater produces a complete daily CSV on demand
- Multi-device support (multiple connection profiles) — unnecessary complexity for the stated single-heater use case

### Architecture Approach

The v1.1 integration is minimal-change. The shipped `index.html` is modified in exactly three places: `#drop-zone` HTML (add `<select>` + fetch button + settings gear), `#app-header` HTML (add gear icon), and `onFileAccepted()` (extract body to `onCsvStringAccepted()`). All new code is additive. Settings live at module level in a dedicated `_settings` object, isolated from `AppState` because settings must survive file reloads while `AppState` resets on each new file load. The dynamic modal pattern (create in JS on demand, destroy on close) is already established by the existing picker modal — the settings modal reuses it exactly.

See `.planning/research/ARCHITECTURE.md` for component table, data flow diagrams, build order, anti-patterns, and scaling considerations.

**Major components — v1.1 additions:**
1. `_settings` (module-level object) — single source of truth for IP/Port/Password during session; populated from `localStorage` at startup; read by `fetchCsv()` at call time with no reactive binding
2. Settings Modal — dynamically created/destroyed in JS following the existing picker modal pattern; pre-populates fields from `_settings` on open; writes to `_settings` + `localStorage` on Save
3. `onCsvStringAccepted(csvString, displayName, fileDate)` — new shared pipeline entry point extracted from `onFileAccepted()`; called identically by both file-drop and fetch paths; zero pipeline duplication
4. `fetchCsv(logPeriod)` — async function; rate limiter check → settings validation → `fetch()` with 10s timeout → `arrayBuffer()` + `TextDecoder` → `onCsvStringAccepted()`
5. Rate limiter — module-level `_lastFetchAt` timestamp + `FETCH_COOLDOWN_MS = 2500`; non-blocking (immediate early return + toast if too soon); timestamp written only when fetch actually starts

**Build order within v1.1 (hard dependencies):**
1. Settings persistence — `_settings`, `SETTINGS_KEY`, `loadSettings()`, `saveSettings()`
2. Settings modal UI — `openSettingsModal()`, `closeSettingsModal()`, gear icon in HTML
3. Pipeline extraction — `onCsvStringAccepted()` from `onFileAccepted()`; verify file-drop regression before continuing
4. `fetchCsv()` + rate limiter + `synthesizeDateFromLogPeriod()`
5. Drop zone fetch UI — `<select>`, fetch button, event wiring

### Critical Pitfalls

The full pitfall set covers 12 issues across v1.0 and v1.1 domains. See `.planning/research/PITFALLS.md` for detection signals, recovery costs, phase mappings, and the "looks done but isn't" checklist.

**Top 5 for v1.1 (new work):**

1. **CORS blocks fetch from file:// origin** — `fetch()` from `file://` always produces opaque origin `null`; browser blocks unless heater returns `Access-Control-Allow-Origin: *`. Avoid by serving app from `python -m http.server 8080` and documenting this clearly in the download UI. Do NOT use `mode: 'no-cors'` (opaque response, unreadable body). Must be discovered and documented before writing fetch code — it changes the deployment model.

2. **Chrome 142 Local Network Access blocks even localhost fetch to LAN device** — Chrome 142+ may block `http://localhost` → `http://192.168.x.x` fetches if the heater cannot respond to LNA OPTIONS preflight with `Access-Control-Allow-Private-Network: true`. Avoid by testing Chrome 142+ explicitly during Phase 1; document Firefox as the primary supported browser for direct download if Chrome LNA cannot be resolved. Firefox has no LNA restriction as of early 2026.

3. **`fetch()` has no default timeout — offline heater hangs UI for 60–90 seconds** — A bare `fetch(url)` with an unreachable IP waits for the OS TCP stack timeout. Apply `AbortSignal.timeout(10000)` on every fetch call to the heater. Catch `TimeoutError` specifically (distinct from `TypeError: Failed to fetch`). Must be in the first fetch implementation, not added later.

4. **Rate limit violation returns ambiguous HTTP 401** — The heater returns 401 + body `"Wait at least 2500ms during requests"` when rate-limited — the same status code as authentication failure. Enforce 2500ms in code from day one; read and display the 401 response body; never auto-retry on 401. Acceptance test: two clicks within 2500ms must show a user-friendly "please wait" message, not a cryptic 401 error.

5. **Wrong password returns 404, not 401** — The OekoFEN API uses the password as a URL path segment; a wrong password makes the path non-existent, returning 404 or empty body. Map 404 to "Check your API Password in Settings" — never surface "404 Not Found". Validate that any HTTP 200 response contains semicolon-delimited CSV before passing to PapaParse.

**Carried-forward v1.0 pitfalls (already handled in existing code; must not regress):**
- UTF-8 BOM corrupts first column header (`\uFEFF` prefix on `AT [C]`) — strip before parse
- German decimal commas silently truncated by `parseFloat` — use custom `parseGermanFloat()`
- Timestamp timezone shift from naive `new Date()` — store as minutes-since-midnight integer

## Implications for Roadmap

The research points to a two-phase structure for v1.1. Phase 1 covers all backend mechanics, error surface, and CORS discovery (highest risk). Phase 2 covers post-validation UX additions (lowest risk, builds on proven Phase 1 infrastructure). This order is non-negotiable — ARCHITECTURE.md's build order derives it from hard dependency chains.

### Phase 1: HTTP Foundation, Settings, and Error Handling

**Rationale:** Everything in v1.1 depends on settings being loadable and `fetchCsv()` being reliable with correct error classification. CORS and timeout pitfalls are blockers that must be discovered and handled before any UX polish is built on top. The settings modal must exist before `fetchCsv()` is written because that function opens the modal automatically when settings are not configured.

**Delivers:** Working `fetchCsv()` that retrieves CSV from the heater, handles all 8 error conditions with user-friendly messages, enforces rate limiting, and pipes the result into the existing parse pipeline via `onCsvStringAccepted()`. Settings persisted across sessions. All failure modes mapped to actionable user messages. CORS behavior documented with clear deployment guidance.

**Addresses (from FEATURES.md P1):**
- Settings modal with localStorage persistence and entry points in drop zone and header
- Log period selector dropdown (Today, Yesterday, Log 0–3)
- Download button with loading state
- Rate limit enforcement (2500ms cooldown)
- Human-readable error feedback for all 8 failure modes

**Avoids (from PITFALLS.md):**
- Pitfall 6: CORS from `file://` — must be discovered, tested, and documented in this phase; changes deployment model
- Pitfall 7: Chrome 142 LNA — must be tested in this phase; Firefox fallback documented
- Pitfall 8: Rate limit → ambiguous 401 — 2500ms guard from first fetch implementation
- Pitfall 9: Wrong password → 404 — mapped to user-readable message; CSV validation before parse
- Pitfall 10: No fetch timeout — `AbortSignal.timeout(10000)` on every call
- Pitfall 11: Password in localStorage without disclosure — settings panel copy includes "stored locally unencrypted" note
- Pitfall 12: Raw network errors to user — all `catch` blocks map to user-facing strings; zero `error.message` propagated raw

**Research flag:** NEEDS EMPIRICAL VERIFICATION. OekoFEN heater CORS header behavior is the only LOW-confidence gap in all research. Phase 1 acceptance criteria must include a real-device CORS test: attempt fetch from `file://` origin (expect CORS error + correct user message) and from `http://localhost` (expect success). Cannot be validated against a mock or test fixture — requires physical OekoFEN device access.

### Phase 2: Post-Validation UX Additions

**Rationale:** These features are explicitly in the "add after validation" category from FEATURES.md. They enhance or observe the Phase 1 download flow, which must be confirmed working against a real device first. Building them before Phase 1 validation risks polishing a flow that needs to change.

**Delivers:** Test connection button that validates settings without downloading a log; cooldown progress indicator counting down after a fetch attempt; persistence of the last-used log period selection across sessions.

**Addresses (from FEATURES.md P2):**
- Test connection button — uses `/all` JSON endpoint; validates IP/Port/Password in settings panel before user attempts a download
- Cooldown progress indicator — "Available in Xs" label updating every 500ms; explains disabled button state
- Persist last-used log period — extends `SETTINGS_KEY` write with one additional field

**Avoids:** No new pitfall exposure in this phase. All pitfalls (CORS, timeout, rate limit, error messages) are already handled in Phase 1 infrastructure.

**Research flag:** STANDARD PATTERNS. These are straightforward UI enhancements over Phase 1 infrastructure with no new integration points. No research-phase needed. Build directly from FEATURES.md spec and the existing code patterns.

### Phase Ordering Rationale

- Settings before fetch: `fetchCsv()` reads `_settings` synchronously at call time — empty settings causes a malformed URL (`http://:4321//command`) which `fetch()` throws on with a cryptic error
- Pipeline extraction before new caller: `onCsvStringAccepted()` is a refactor of existing code; regression-verifying the file-drop path in isolation before adding `fetchCsv()` as a second caller eliminates risk of introducing bugs into the already-working v1.0 flow
- UI wiring last within Phase 1: pure HTML + event listener work; all logic exists by that point; no logic risk
- Phase 2 after real-device validation: P2 features (test connection, cooldown) enhance the download flow, which cannot be properly exercised without a physical heater

### Research Flags

**Needs empirical verification — Phase 1:**
- **CORS header behavior of actual OekoFEN heater** — the single LOW-confidence gap across all research. No public documentation or community integration reports what `Access-Control-Allow-Origin` header (if any) the heater returns in CSV responses. If the heater returns no CORS headers, the `file://` origin path is permanently blocked and serving from `http://localhost` becomes a hard prerequisite. This must be documented prominently in the download UI regardless of outcome.

**Standard patterns — no research-phase needed:**
- **Settings persistence:** The existing `'oekofen-viewer-prefs'` `localStorage` pattern in the codebase is the direct reference implementation; extend with a new key
- **Settings modal:** The existing picker modal in `index.html` (lines 2326–2513) is the reference implementation; reuse create/destroy-in-JS pattern
- **Pipeline extraction:** `onCsvStringAccepted()` signature is fully specified in ARCHITECTURE.md; mechanical refactor
- **Rate limiter:** Timestamp guard is 6 lines; fully specified in both STACK.md and ARCHITECTURE.md with code
- **Phase 2 features:** All are simple UI enhancements over Phase 1 infrastructure

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All APIs are baseline widely available (Jan 2020+); patterns verified against MDN and Chrome dev docs; `windows-1252` label is required by the Encoding API spec — all compliant browsers must support it |
| Features | HIGH | P1/P2/P3 split reasoned from UX research (NN/G, LogRocket, Smashing Magazine) and OekoFEN community API docs; feature dependencies explicitly mapped in FEATURES.md; anti-features clearly justified |
| Architecture | HIGH | Derived from direct code analysis of the shipped 2,542-line `index.html`; patterns match existing codebase conventions exactly; build order derived from hard dependency chains, not opinion |
| Pitfalls | HIGH (v1.0 pitfalls) / MEDIUM (v1.1 CORS/LNA) | v1.0 pitfalls verified via PapaParse GitHub issues, MDN, and benchmark data. v1.1 CORS/LNA pitfalls verified via WICG spec and Chrome dev blog — but OekoFEN heater header behavior is empirically unverified |

**Overall confidence:** HIGH — with one explicitly bounded gap.

### Gaps to Address

- **OekoFEN heater CORS headers (LOW confidence):** Cannot be determined from any public source. All community integrations (Python, Perl, PHP, Home Assistant) are server-side — CORS is irrelevant to them. Resolution: empirical test against a real device in Phase 1 using browser DevTools Network tab. If heater returns no CORS headers: serving from `http://localhost` becomes a hard prerequisite for the download feature; the UI must communicate this clearly; the README must document the `python -m http.server` startup command.

- **Exact OekoFEN CSV log endpoint URL format:** ARCHITECTURE.md's `fetchCsv()` uses `http://{ip}:{port}/{password}/csv?file={logPeriod}`. PROJECT.md milestone context states commands are `log_today`, `log_yesterday`, `log0`, `log1`, `log2`, `log3`. The exact URL structure should be cross-referenced against community repos (oekofen-stats, oekofen-api) and verified on the real device during Phase 1.

- **Chrome 142 LNA behavior with `file://` origin (MEDIUM confidence):** The WICG LNA spec classifies `file://` as "local" and states local-to-local requests should not be LNA-gated. However, the spec includes a note: "Reevaluate after implementation experience." Whether Chrome's implementation follows the spec for this specific edge case must be tested in Chrome 138 (opt-in flag available) during Phase 1 acceptance testing.

## Sources

### Primary (HIGH confidence)
- WICG Local Network Access spec (https://wicg.github.io/local-network-access/) — file:// tier classification as "local"; local-to-local request gating rules
- Chrome Developer Blog: Local Network Access (https://developer.chrome.com/blog/local-network-access) — Chrome 138 opt-in, Chrome 142 launch, permission prompt details
- MDN: TextDecoder (https://developer.mozilla.org/en-US/docs/Web/API/TextDecoder) — windows-1252 baseline availability; Encoding API required labels
- MDN: AbortSignal.timeout() (https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/timeout_static) — timeout pattern; `TimeoutError` vs `TypeError` distinction
- MDN: CORS Errors/CORSRequestNotHttp (https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS/Errors/CORSRequestNotHttp) — file:// opaque origin (`null`) behavior
- MDN: Secure Contexts (https://developer.mozilla.org/en-US/docs/Web/Security/Secure_Contexts) — file:// is "potentially trustworthy"; `window.isSecureContext === true`
- Direct code analysis of shipped `index.html` (2,542 lines) — all architecture descriptions; existing patterns for modal, localStorage, pipeline
- PapaParse GitHub Issues #840, #372, #143 — BOM corruption and German decimal truncation confirmed bugs
- uPlot GitHub (https://github.com/leeoniya/uPlot) — performance benchmarks; plugin API; columnar data format

### Secondary (MEDIUM confidence)
- OekoFEN JSON API community documentation (https://github.com/thannaske/oekofen-json-documentation) — API URL format; rate limit behavior (2500ms); irregular connection issues
- OekoFEN community API library (https://github.com/ckarrie/oekofen-api) — URL patterns; endpoint names
- OekoFEN stats project (https://github.com/ohitz/oekofen-stats) — URL format cross-reference
- NN/G Progress Indicators — loading state UX guidance
- LogRocket Form Validation UX — on-save vs on-keystroke validation decision
- Smashing Magazine Inline Validation — inline error message placement

### Tertiary (LOW confidence)
- OekoFEN heater CORS header behavior — **no empirical data found**; all community integrations are server-side; must be verified on actual device during Phase 1
- Exact OekoFEN log endpoint URL format — derived from community repos and PROJECT.md milestone context; must be confirmed on real device

---
*Research completed: 2026-02-21*
*Ready for roadmap: yes*
