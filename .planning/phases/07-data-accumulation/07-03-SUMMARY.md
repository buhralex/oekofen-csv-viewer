---
phase: 07-data-accumulation
plan: "03"
subsystem: browser
tags: [indexeddb, server-history, startup-fetch, history-sync, accumulation]

# Dependency graph
requires:
  - phase: 07-data-accumulation
    plan: "01"
    provides: openHistoryDb, upsertHistoryDay, getAllHistoryDays, updateHistoryIndicator functions in index.html
  - phase: 07-data-accumulation
    plan: "02"
    provides: /history list endpoint and /history/YYYYMMDD.csv serve endpoint in server.py
provides:
  - loadHistoryFromServer() function wired to page startup in index.html
  - DACC-04 full loop: server.py --schedule writes to disk, browser imports via /history on page load
affects:
  - 08-settings-baseline
  - 09-aggregation
  - 10-ai-analysis

# Tech tracking
tech-stack:
  added: [AbortSignal.timeout (native browser API)]
  patterns:
    - silent-startup-import (loadHistoryFromServer called without await — runs in background, does not delay page render)
    - file-protocol-guard (loadHistoryFromServer no-ops on file:// origin to prevent console errors)
    - dedup-before-import (existing IndexedDB dates excluded from import batch before any fetch)
    - timeout-on-startup-fetch (3s AbortSignal.timeout on /history, 5s on individual CSV fetches — prevents page hang if server.py is old version)

key-files:
  created: []
  modified:
    - index.html

key-decisions:
  - "loadHistoryFromServer() called without await in startup block — fire-and-forget so it does not delay initial page render"
  - "file:// protocol guard at top of loadHistoryFromServer() — no-op when opened as local file; prevents fetch error in console"
  - "3-second timeout on /history fetch — old server.py versions without /history endpoint will time out cleanly without error toast"
  - "console.debug (not console.warn) for the outer catch — treated as trace-level noise, not a visible warning"
  - "TextDecoder('windows-1252') used for individual CSV fetches — matches fetchCsv() pattern; OekoFEN CSVs are windows-1252 encoded"

patterns-established:
  - "Pattern: silent startup sync — loadHistoryFromServer() uses fire-and-forget + file:// guard + timeout + console.debug catch for zero-visible-impact background import"
  - "Pattern: dedup before import — getAllHistoryDays() queried first, existing dates excluded; never overwrites or duplicates IndexedDB records"

requirements-completed: [DACC-04]

# Metrics
duration: 5min
completed: 2026-02-26
---

# Phase 7 Plan 03: loadHistoryFromServer() Startup Wiring Summary

**loadHistoryFromServer() added to index.html — browser silently imports server-stored history CSVs from /history on page load, closing the DACC-04 always-on VM accumulation loop**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-02-26T06:20:00Z (estimated — continuation after human-verify checkpoint)
- **Completed:** 2026-02-26T06:28:33Z
- **Tasks:** 2 (Task 1 auto, Task 2 human-verify checkpoint — approved)
- **Files modified:** 1 (index.html)

## Accomplishments

- Added `loadHistoryFromServer()` async function to index.html with file:// guard, 3s/5s timeouts, dedup logic, and silent error handling
- Wired `loadHistoryFromServer()` into the startup initialization block (called without `await` after `updateHistoryIndicator()` so it runs in background without delaying page render)
- Human checkpoint confirmed all four DACC requirements verified end-to-end: upsert (DACC-01), indicator (DACC-02), clear (DACC-03), server schedule loop (DACC-04)
- Full Phase 7 Data Accumulation stack confirmed working: server.py --schedule writes to ./history/, browser reads via /history endpoint on load, both paths populate same IndexedDB store

## Task Commits

Each task was committed atomically:

1. **Task 1: loadHistoryFromServer() + startup wiring** - `88a760e` (feat)
2. **Task 2: Verify Phase 7 end-to-end** - human-verify checkpoint, approved by user

**Plan metadata:** (pending — docs commit)

## Files Created/Modified
- `index.html` - Added `loadHistoryFromServer()` function and wired to startup initialization block after `updateHistoryIndicator()`

## Decisions Made

- `loadHistoryFromServer()` is fire-and-forget (no `await` at call site) — background import must not delay initial page render; `updateHistoryIndicator()` is called internally when imports complete
- `file://` protocol check at function top — prevents fetch error in console when user opens index.html directly as a local file without server.py running
- 3-second timeout on `/history` list fetch — old server.py versions (pre-07-02) do not have a `/history` endpoint; call must time out cleanly without showing an error toast
- `console.debug` (not `console.warn`) for the outer try/catch — this is expected trace-level noise in environments without server.py, not an actionable warning
- `TextDecoder('windows-1252')` for individual CSV fetches — same encoding as `fetchCsv()` in Phase 6; OekoFEN CSVs contain degree sign characters that are corrupted by UTF-8 default

## Deviations from Plan

None - plan executed exactly as written. The plan provided complete implementation code and all behaviors to preserve; no unplanned changes were required.

## Issues Encountered

None. Task 1 implemented as specified. Human checkpoint (Task 2) approved with all 6 verification scenarios passing:
1. Server starts normally (backward compat confirmed)
2. DACC-01: IndexedDB upsert confirmed — drop CSV creates record, drop again stays at 1
3. DACC-02: History indicator shows date range, persists across reload
4. DACC-03: Clear removes all records, indicator resets
5. DACC-04: history/20260101.csv present, browser loads it on startup via /history endpoint
6. Security: server.py and settings.json blocked (404)

## User Setup Required

None - no external service configuration required. All functionality uses native browser APIs (IndexedDB, fetch) and the existing server.py.

## Next Phase Readiness

- All four DACC requirements satisfied: DACC-01 (upsert), DACC-02 (indicator), DACC-03 (clear), DACC-04 (server schedule loop)
- Phase 7 Data Accumulation complete — IndexedDB store populated from both browser drop/fetch and server-accumulated CSVs
- Phase 8 (Settings Baseline Parser) can proceed independently — no dependency on Phase 7 output
- Phase 9 (Aggregation) can read history via `getAllHistoryDays()` which is available at module scope and now includes server-accumulated data

## Self-Check: PASSED

- index.html: FOUND (modified in commit 88a760e)
- .planning/phases/07-data-accumulation/07-03-SUMMARY.md: this file
- Commit 88a760e: FOUND (feat(07-03): add loadHistoryFromServer() and wire to page startup)

---
*Phase: 07-data-accumulation*
*Completed: 2026-02-26*
