---
phase: 07-data-accumulation
plan: "01"
subsystem: database
tags: [indexeddb, browser-storage, csv, history, accumulation]

# Dependency graph
requires:
  - phase: 06-live-fetch
    provides: onCsvStringAccepted() pipeline, fetchCsv() function, onFileAccepted() function
provides:
  - IndexedDB store 'oekofen-history' with keyPath='date' (YYYYMMDD)
  - openHistoryDb / upsertHistoryDay / getAllHistoryDays / clearHistoryDb functions
  - parseDateFromCsvString() CSV date extraction helper
  - #history-indicator DOM element showing stored days count and date range
  - updateHistoryIndicator() function called after every CSV load and on page init
  - Clear button rendered inline by updateHistoryIndicator()
affects:
  - 08-settings-baseline
  - 09-aggregation
  - 10-ai-analysis

# Tech tracking
tech-stack:
  added: [IndexedDB (native browser API)]
  patterns:
    - upsert-by-date-key (IDBObjectStore.put with keyPath='date')
    - fire-and-forget storage (upsertHistoryDay uses .then().catch() so storage failure never blocks chart render)
    - inline Clear button (rendered by updateHistoryIndicator() — no permanent DOM element, shown only when data exists)
    - CSV date fallback (parseDateFromCsvString() used when filename/command lacks date)

key-files:
  created: []
  modified:
    - index.html

key-decisions:
  - "IndexedDB store uses keyPath='date' (YYYYMMDD) — same date always upserts, never duplicates"
  - "upsertHistoryDay called with .then().catch() not await — storage failure cannot block chart render pipeline"
  - "parseDateFromCsvString() added to extract date from CSV content for log_yesterday/log0-log3 commands that have no command-derived date"
  - "History indicator Clear button rendered inline by updateHistoryIndicator() — avoids permanent empty button in UI when no history exists"
  - "updateHistoryIndicator() called on page init — indicator reflects persisted data immediately on tab reload"

patterns-established:
  - "Pattern: CSV date fallback — try filename/command first, then parseDateFromCsvString() as fallback"
  - "Pattern: non-blocking storage — IndexedDB writes never await in the render pipeline; use .then().catch()"
  - "Pattern: self-contained history module — all IndexedDB functions in one script block, named consistently with HISTORY_ prefix constants"

requirements-completed: [DACC-01, DACC-02, DACC-03]

# Metrics
duration: 2min
completed: 2026-02-25
---

# Phase 7 Plan 01: IndexedDB Multi-Day CSV History Summary

**IndexedDB-backed CSV history with upsert-by-date, page-persistent indicator, and inline Clear button wired into the existing drop/fetch pipeline**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-25T19:34:34Z
- **Completed:** 2026-02-25T19:36:12Z
- **Tasks:** 2 (committed together — both modify index.html, Task 2 required by Task 1 pipeline wiring)
- **Files modified:** 1 (index.html)

## Accomplishments
- Added four IndexedDB async functions (openHistoryDb, upsertHistoryDay, getAllHistoryDays, clearHistoryDb) and constants (HISTORY_DB_NAME, HISTORY_DB_VERSION, HISTORY_STORE)
- Wired upsertHistoryDay() into onCsvStringAccepted() with fire-and-forget pattern so storage failure never blocks chart render
- Added parseDateFromCsvString() helper that reads Datum column (DD.MM.YYYY format) from first data row, enabling date storage for log_yesterday/log0-log3 fetch commands
- Added #history-indicator element in drop zone showing "{N} day(s) stored: YYYY-MM-DD [- YYYY-MM-DD] [Clear]" with inline Clear button that clears IndexedDB and resets indicator
- Called updateHistoryIndicator() on page init so previously stored data is reflected immediately on reload

## Task Commits

Each task was committed atomically:

1. **Task 1 + Task 2: IndexedDB module + pipeline wiring + history indicator UI** - `d737bf8` (feat)

_Note: Both tasks modify index.html only and are interdependent (Task 1 wiring calls updateHistoryIndicator from Task 2), so committed as one atomic change._

**Plan metadata:** (pending — docs commit)

## Files Created/Modified
- `index.html` - Added IndexedDB module, parseDateFromCsvString helper, history indicator HTML element (#history-indicator), updateHistoryIndicator() + formatHistoryDate() functions, pipeline wiring in onCsvStringAccepted/fetchCsv/onFileAccepted, page-init call

## Decisions Made
- Used fire-and-forget `.then().catch()` pattern for IndexedDB writes — storage failure should never block chart rendering (correctness-first)
- parseDateFromCsvString() searches from line index 1 onwards (skipping header), matches DD.MM.YYYY in first column — robust to leading metadata rows
- Clear button is rendered inline by updateHistoryIndicator() rather than as a permanent DOM element — keeps UI clean when no history exists
- Both fetchCsv() and onFileAccepted() use `fileDate = existing || parseDateFromCsvString(csvString)` pattern consistently

## Deviations from Plan

None - plan executed exactly as written. The plan explicitly specified both the .then().catch() pattern and parseDateFromCsvString() helper, so no unplanned auto-fixes were required.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. IndexedDB is a native browser API, zero setup needed.

## Next Phase Readiness
- DACC-01/02/03 satisfied: every CSV load (drop or fetch) persists to IndexedDB under date key; indicator reflects history; Clear resets all records
- Phase 8 (Settings Baseline Parser) can proceed independently — no dependency on this plan's output
- Phase 9 (Aggregation) can read history via getAllHistoryDays() which is now available at module scope

## Self-Check: PASSED

- index.html: FOUND
- 07-01-SUMMARY.md: FOUND
- Commit d737bf8: FOUND
- All 7 required functions/elements present in index.html (21 references verified)

---
*Phase: 07-data-accumulation*
*Completed: 2026-02-25*
