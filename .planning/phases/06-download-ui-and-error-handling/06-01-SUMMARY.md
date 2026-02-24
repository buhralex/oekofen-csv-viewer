---
phase: 06-download-ui-and-error-handling
plan: "01"
subsystem: ui
tags: [fetch, cors, rate-limit, error-handling, windows-1252, AbortSignal]

# Dependency graph
requires:
  - phase: 05-settings-and-pipeline-foundation
    provides: "_settings object (ip/port/password), onCsvStringAccepted() pipeline entry point"
provides:
  - "fetchCsv(command) async fetch engine with all error handling"
  - "_lastFetchAt and _rateLimitTimer module-level rate-limit state"
  - "setFetchButtonState() for fetch-btn loading/ready states"
  - "handleFetchHttpError() mapping HTTP 401/404 to user toasts"
  - "handleFetchNetworkError() mapping TimeoutError/AbortError and CORS/TypeError to user toasts"
affects:
  - "06-02 — UI wiring plan will call fetchCsv() from Download button click handlers"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "AbortSignal.timeout(10000) for network timeout (no manual AbortController needed)"
    - "arrayBuffer() + TextDecoder('windows-1252') for OekoFEN CSV encoding (not response.text())"
    - "Rate-limit guard: _lastFetchAt written before fetch starts, finally block restores button after 2500ms window"
    - "file:// protocol pre-flight check before any fetch attempt"

key-files:
  created: []
  modified:
    - index.html

key-decisions:
  - "_lastFetchAt written before fetch() call, not after response — ensures rate-limit guard is accurate even on fast failures"
  - "AbortSignal.timeout() chosen over manual AbortController + setTimeout (simpler, no cleanup needed)"
  - "Both 'TimeoutError' and 'AbortError' checked in catch — Chrome 103-123 fires AbortError, Chrome 124+ fires TimeoutError"
  - "arrayBuffer() + TextDecoder('windows-1252') mandated — response.text() would produce mojibake on degree signs and umlauts"
  - "mode: 'no-cors' explicitly excluded — returns opaque response with unreadable body"
  - "No auto-retry on HTTP 401 — heater rate-limit must reset; retry without waiting would immediately 401 again"

patterns-established:
  - "Error helper pattern: handleFetchHttpError(status) and handleFetchNetworkError(err) keep fetchCsv body clean"
  - "Button state helper: setFetchButtonState('loading'|'ready') centralises DOM mutation"

requirements-completed: [CONN-02, CONN-03, ERR-01, ERR-02, ERR-03, ERR-04]

# Metrics
duration: 8min
completed: 2026-02-24
---

# Phase 6 Plan 01: Fetch Engine Summary

**Core fetch engine with file:// pre-flight, 2500ms rate-limit guard, 10-second AbortSignal timeout, windows-1252 decoding, and HTTP/network error helpers wired to user toasts**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-24T15:39:46Z
- **Completed:** 2026-02-24T15:47:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Module-level `_lastFetchAt` and `_rateLimitTimer` vars inserted at correct scope between `_settings` and `loadSettings()`
- `fetchCsv(command)` async function with all four error conditions: file:// origin, rate-limit guard, HTTP status errors, and network/timeout catch
- `handleFetchHttpError(status)` mapping HTTP 401 to rate-limit warning toast and 404 to password error toast
- `handleFetchNetworkError(err)` distinguishing timeout from CORS/network errors with browser-compat dual name check
- `setFetchButtonState()` for loading/ready button transitions with `fetch-btn` element
- Correct encoding path: `arrayBuffer()` + `TextDecoder('windows-1252')` to match the file-drop path

## Task Commits

Each task was committed atomically:

1. **Task 1: Add module-level rate-limit state vars** - `ae0d19f` (feat)
2. **Task 2: Implement fetchCsv, setFetchButtonState, handleFetchHttpError, handleFetchNetworkError** - `fc59538` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `index.html` - Added 115 lines: 4 module-level vars (lines 925-927) and 4 functions (lines 2744-2855)

## Decisions Made

- `_lastFetchAt` written before `await fetch()` so rate-limit is accurate even on immediate network failures
- `AbortSignal.timeout(10000)` preferred over manual AbortController pattern — browser handles cleanup automatically
- Catch block checks both `'TimeoutError'` and `'AbortError'` for Chrome 103-123 backward compatibility
- `response.text()` forbidden — always use `arrayBuffer()` + `TextDecoder('windows-1252')` for OekoFEN CSV files
- No `mode: 'no-cors'` — opaque responses have unreadable bodies, would silently swallow errors
- No auto-retry on 401 — per STATE.md decision: "never auto-retry"

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `fetchCsv(command)` is ready for Plan 06-02 to wire to the Download button click handler
- `setFetchButtonState` will manage the `fetch-btn` element that Plan 06-02 adds to the HTML
- All error conditions handled in the fetch layer; UI wiring plan can remain simple
- Blocker noted in STATE.md remains: CORS header behavior of OekoFEN heater empirically unverified; real device test needed

---
*Phase: 06-download-ui-and-error-handling*
*Completed: 2026-02-24*
