---
phase: 06-download-ui-and-error-handling
plan: "05"
subsystem: ui
tags: [javascript, fetch, proxy, cors, error-handling, csv]

# Dependency graph
requires:
  - phase: 06-download-ui-and-error-handling
    provides: server.py /proxy endpoint (06-04) that fetchCsv now routes through
provides:
  - fetchCsv() wired to /proxy?url= — heater CORS block fully bypassed end-to-end
  - Accurate file:// pre-flight toast referencing server.py and start.bat
  - Accurate network-error toast ("Could not reach the heater") without misleading "try Firefox" advice
affects:
  - Phase 6 complete — all CONN/ERR requirements satisfied

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Proxy URL pattern: /proxy?url=encodeURIComponent(heaterUrl) constructed in fetchCsv before fetch()
    - Error message accuracy: TypeError from proxy means heater is unreachable, not CORS — message updated accordingly

key-files:
  created: []
  modified:
    - index.html

key-decisions:
  - "fetchCsv() renamed local var to heaterUrl, constructs proxyUrl as /proxy?url=encodeURIComponent(heaterUrl) — all other logic unchanged"
  - "handleFetchNetworkError() else branch message changed from CORS/Firefox advice to 'Could not reach the heater. Check the IP address and port in Settings.' — proxy makes CORS irrelevant"
  - "file:// pre-flight toast updated to reference 'Double-click start.bat or run: python server.py' — old python -m http.server 8080 text removed"
  - "Human checkpoint approved: real OekoFEN heater download loads chart end-to-end via proxy"

patterns-established:
  - "Proxy routing: all heater fetch requests go through /proxy?url= — never direct browser-to-heater"
  - "Error message philosophy: tell the user what is likely wrong (IP/port) not what the browser API returned (CORS/TypeError)"

requirements-completed: [CONN-01, CONN-02, CONN-03, ERR-01, ERR-02, ERR-03, ERR-04]

# Metrics
duration: ~5min (automated) + human checkpoint
completed: 2026-02-25
---

# Phase 06 Plan 05: fetchCsv Proxy Wiring Summary

**fetchCsv() routed through /proxy?url= to bypass OekoFEN CORS block, with corrected file:// guidance (server.py/start.bat) and accurate network-error message — human checkpoint approved end-to-end download from real heater**

## Performance

- **Duration:** ~5 min (Task 1 automated) + human checkpoint verification
- **Started:** 2026-02-25
- **Completed:** 2026-02-25
- **Tasks:** 2 (1 automated, 1 human-verify checkpoint)
- **Files modified:** 1

## Accomplishments
- Wired fetchCsv() to use /proxy?url=encodeURIComponent(heaterUrl) instead of fetching the heater URL directly — CORS block is permanently bypassed via server.py
- Replaced misleading "try Firefox" CORS guidance in handleFetchNetworkError() with accurate "Could not reach the heater. Check the IP address and port in Settings."
- Updated file:// pre-flight toast to reference correct startup commands (Double-click start.bat or run: python server.py) instead of the obsolete python -m http.server 8080
- Human checkpoint approved: real OekoFEN heater download loads chart end-to-end; all regression tests (rate-limit, file-drop, wrong IP, DevTools proxy check, file:// warning) passed

## Task Commits

Each task was committed atomically:

1. **Task 1: Update fetchCsv() to use proxy, fix file:// message, fix handleFetchNetworkError() error message** - `d38f3ad` (feat)
2. **Task 2: Verify proxy download end-to-end with real heater** - human checkpoint — approved by user

**Plan metadata:** (docs: complete plan — see final commit)

## Files Created/Modified
- `index.html` — Three targeted changes: (1) fetchCsv() URL construction now builds /proxy?url=encodeURIComponent(heaterUrl); (2) file:// pre-flight toast message updated to reference server.py/start.bat; (3) handleFetchNetworkError() else branch updated with accurate error message

## Decisions Made
- Retained the file:// pre-flight check block exactly — only the toast message text was updated; ERR-01 requirement (user gets actionable guidance when opening as file://) satisfied
- handleFetchNetworkError() TypeError is now definitively a proxy-to-heater failure (not a CORS failure) — message updated to reflect that reality
- No rate-limit, timeout, TextDecoder, HTTP error mapping, or onCsvStringAccepted changes — all unchanged as specified

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 6 (Download UI and Error Handling) is now complete — all 5 plans executed
- All CONN and ERR requirements (CONN-01 through CONN-06, ERR-01 through ERR-04) are satisfied
- The full download chain works: browser fetchCsv() -> GET /proxy?url= -> server.py urlopen -> heater -> CSV -> chart renders
- No open gaps or blockers

---
*Phase: 06-download-ui-and-error-handling*
*Completed: 2026-02-25*

## Self-Check: PASSED

- FOUND: index.html (modified with proxy wiring)
- FOUND commit d38f3ad (Task 1: wire fetchCsv to proxy)
- Human checkpoint Task 2: approved by user
