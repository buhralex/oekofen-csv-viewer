---
phase: 06-download-ui-and-error-handling
plan: "03"
subsystem: ui
tags: [fetch, cors, error-handling, verification, oekofen]

# Dependency graph
requires:
  - phase: 06-01
    provides: fetchCsv engine with all error paths implemented
  - phase: 06-02
    provides: fetch controls UI wired to fetchCsv and settings visibility logic

provides:
  - Empirical CORS behavior confirmation for OekoFEN heater (blocks CORS — no Access-Control-Allow-Origin header)
  - All Phase 6 error paths verified against real device and real browser behavior
  - Known gap documented: "try Firefox" advice in handleFetchNetworkError is incorrect and should be replaced

affects: [gap-closure plan, STATE.md blockers, future proxy/workaround planning]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Empirical-first verification: checkpoint plan that surfaces unknown device behavior before writing workarounds"

key-files:
  created: []
  modified: []

key-decisions:
  - "OekoFEN heater confirmed to NOT return Access-Control-Allow-Origin headers — direct browser fetch is impossible without a CORS proxy or local server"
  - "Firefox does NOT bypass CORS — both Chrome and Firefox enforce it identically; 'try Firefox' advice is wrong and must be removed"
  - "Current error UX is functionally correct (user sees an error toast) but the message text needs a gap-closure fix"
  - "The heater IS network-reachable; http://10.10.30.3:4321/ctT9/log_today opens as CSV in the browser directly — the block is CORS only"

patterns-established:
  - "CORS from browser to OekoFEN heater: hard block — cannot be solved client-side; python -m http.server is NOT a fix for CORS (it only fixes file:// origin errors)"

requirements-completed: [CONN-01, CONN-02, CONN-03, ERR-01, ERR-02, ERR-03, ERR-04]

# Metrics
duration: 10min
completed: 2026-02-24
---

# Phase 6 Plan 03: Empirical Device Verification Summary

**OekoFEN heater empirically confirmed to block browser CORS — all 5 error paths verified correct except the error message text which advises "try Firefox" (wrong advice — Firefox enforces CORS identically)**

## Performance

- **Duration:** ~10 min (human verification session)
- **Started:** 2026-02-24
- **Completed:** 2026-02-24T21:53:16Z
- **Tasks:** 1 (checkpoint:human-verify)
- **Files modified:** 0 (verification only — no code changes in this plan)

## Accomplishments

- Empirically confirmed OekoFEN heater does NOT return `Access-Control-Allow-Origin` headers — direct `fetch()` from a browser is impossible without a CORS proxy
- Confirmed the heater IS network-reachable: `http://10.10.30.3:4321/ctT9/log_today` opens successfully as CSV when pasted directly into a browser address bar; the block is strictly CORS
- All five error paths verified working: Test A (controls visibility), Test B (CORS error toast shown), Test D (rate-limit guard ~2500ms), Test E (file:// origin error), Test F (file-drop regression)
- Identified gap: `handleFetchNetworkError` currently suggests "try Firefox" — empirically incorrect because Firefox enforces CORS identically to Chrome

## Task Commits

This plan was a verification checkpoint — no code was produced. No task commits.

**Plan metadata commit:** (created after this summary — see final commit in completion message)

## Files Created/Modified

None — verification plan only.

## Decisions Made

- **OekoFEN heater blocks CORS (confirmed):** The heater serves CSV files correctly via HTTP but does not include `Access-Control-Allow-Origin` response headers. Any browser `fetch()` call to the heater is blocked by the browser's CORS policy regardless of browser vendor. This is a server-side heater limitation.
- **Firefox does not bypass CORS:** The current error message in `handleFetchNetworkError` includes the advice "try Firefox". This is empirically incorrect — both Chrome and Firefox implement the CORS specification and will block the request identically. This advice must be replaced.
- **Gap closure needed before Phase 6 is fully complete:** The error message should tell the user the actual heater URL so they can manually download the CSV and drag it in, e.g.: "The heater does not support browser requests (CORS). To download manually, open `http://[ip]:[port]/[password]/log_today.csv` directly in your browser."
- **Rate-limit guard working correctly:** Button was disabled for approximately 2500ms; user could not click again within that window. Behavior matches specification.

## Deviations from Plan

None — plan executed exactly as written. This was a verification-only checkpoint.

## Issues Encountered

**Gap identified during verification (not a deviation — this is a new finding):**

The `handleFetchNetworkError` function in `index.html` includes "try Firefox, or verify the heater IP in Settings" as part of the CORS error message. Real-world testing against an OekoFEN heater proves this advice is wrong:

- The heater at `http://10.10.30.3:4321/ctT9/log_today` is fully reachable and serves CSV correctly when accessed directly in a browser tab
- Fetch from JavaScript is blocked by the browser's CORS enforcement, which applies equally to Chrome, Firefox, Edge, and Safari
- "Try Firefox" will confuse users — Firefox will show the same error

**Recommended fix (gap-closure task):** Replace "try Firefox" with a link/instruction to open the heater URL directly in the browser for manual download. The fix is one line in `handleFetchNetworkError`.

**CORS confirmed as known limitation, not a blocker:** Direct download from browser is impossible without a server-side CORS proxy or heater firmware update. The app's current architecture (python -m http.server resolves the file:// origin issue only) correctly handles what can be handled client-side. The CORS block from heater is documented as a permanent known limitation.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 6 is functionally complete — all planned features work
- One gap remains: error message text in `handleFetchNetworkError` needs "try Firefox" replaced with correct guidance (manual download URL)
- Gap-closure is a single-line code fix; no new architecture needed
- STATE.md blocker "CORS header behavior of OekoFEN heater is empirically unverified" is now **RESOLVED** — confirmed: heater blocks CORS

---
*Phase: 06-download-ui-and-error-handling*
*Completed: 2026-02-24*
