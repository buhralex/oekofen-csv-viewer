---
phase: 09-data-aggregation
plan: "01"
subsystem: database
tags: [sqlite, sqlite3, aggregation, stats, python, csv-parsing]

# Dependency graph
requires:
  - phase: 07-data-accumulation
    provides: "./history/YYYYMMDD.csv files written by scheduled auto-fetch"
  - phase: 06-proxy-server
    provides: "server.py with fetch_and_store_today() and do_GET() routing"

provides:
  - "SQLite stats.db with daily_stats table (11 columns, one row per day)"
  - "GET /stats endpoint returning JSON with days array + trend object"
  - "compute_and_store_stats(date): on-demand stat computation for one day"
  - "backfill_stats(): startup backfill for all unprocessed history CSVs"
  - "get_all_stats(): full stats retrieval with linear regression trend"

affects: [09-02-statistics-ui, 10-ai-integration]

# Tech tracking
tech-stack:
  added: [sqlite3 (Python stdlib), re (Python stdlib)]
  patterns:
    - "Open-connection-per-call pattern for SQLite thread safety"
    - "INSERT OR REPLACE for idempotent stats upsert"
    - "Rising-edge detection on BR column for burner start counting"
    - "Last-minus-first delta for cumulative counters (runtime, pellet)"

key-files:
  created: [stats.db (runtime artifact, auto-created alongside server.py)]
  modified: [server.py]

key-decisions:
  - "Open fresh SQLite connection per function call for thread safety — schedule thread and HTTP handler both call compute_and_store_stats() concurrently"
  - "detect_columns() uses case-insensitive regex on name-part (before '[') — handles column names like 'AT [°C]' and 'HK1 VL Ist[°C]'"
  - "AT outdoor temp detection is exact uppercase match ('AT' only) to avoid false-positives on ATakt or other AT-prefixed columns"
  - "burner starts = rising edge 0→1 on BR column (float comparison) — not total BR=1 rows"
  - "PE1 CntDig1 matched as pellet column via ^PE1.*cnt regex — actual device uses this counter column"
  - "backfill_stats() wrapped in try/except in __main__ — corrupt CSV never prevents server startup"
  - "Trend threshold: |slope| <= 0.05 treated as stable — avoids noise in 3-5 day windows"
  - "is_partial = hours_covered < 20 — day without 20+ hours of data is treated as incomplete for trend computation"

patterns-established:
  - "column auto-detection: split header on '[', match name-part with regex — reusable for any OekoFEN CSV column set"
  - "stats computation: purely functional (csv_string + date in, dict out) with no side effects — easy to test"

requirements-completed: [AGGR-01, AGGR-02]

# Metrics
duration: 3min
completed: 2026-02-26
---

# Phase 9 Plan 01: SQLite Aggregation Engine + /stats Endpoint Summary

**SQLite-backed per-day stats engine (starts, runtime, temp, pellet delta) with linear regression trend and GET /stats JSON endpoint in server.py**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-02-26T14:20:04Z
- **Completed:** 2026-02-26T14:22:46Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Extended server.py with a full SQLite aggregation pipeline: column auto-detection, per-day stat computation, persistence, and trend analysis
- GET /stats endpoint returns JSON with days array (per-day stats), trend object (direction/slope/label), total_days, and complete_days
- Startup backfill processes all unprocessed ./history/*.csv files synchronously before server begins serving requests
- Verified against real device CSVs: 4 days processed correctly, burner starts = 11/9/12/7, avg outdoor temps computed, trend=up (+0.50 starts/day)

## Task Commits

Each task was committed atomically:

1. **Task 1: SQLite stats schema + column auto-detection engine** - `7fecf4e` (feat)
2. **Task 2: Persistence layer + /stats endpoint + startup backfill + schedule hook** - `40fefdd` (feat)

**Plan metadata:** (docs commit after SUMMARY creation)

## Files Created/Modified
- `server.py` - Added sqlite3 import, STATS_DB_PATH, open_stats_db(), detect_columns(), parse_german_float(), compute_day_stats(), compute_and_store_stats(), backfill_stats(), get_all_stats(), GET /stats route, backfill call in __main__, stats hook in fetch_and_store_today()
- `stats.db` - Runtime artifact created alongside server.py on first run (not committed to git)

## Decisions Made
- **Open-connection-per-call for thread safety:** The HTTP handler thread and schedule thread both call compute_and_store_stats(). Opening a fresh sqlite3 connection per function call avoids shared state without needing locks.
- **detect_columns name-part extraction:** OekoFEN column headers contain units in brackets (e.g., "AT [°C]"). Splitting on '[' and matching the name part avoids false-positive regex matches on unit strings.
- **AT outdoor temp: exact uppercase match only:** Column "ATakt [°C]" exists in the CSV and must not be matched as outdoor temperature. Using exact match `name_part == 'AT'` prevents this.
- **Trend threshold ±0.05 starts/day = stable:** With only 3-5 days of history typically available, small fluctuations in starts should not trigger trend direction labels; 0.05 provides a noise floor.
- **backfill_stats wrapped in try/except in __main__:** A corrupt or unreadable CSV file must never prevent server startup. The try/except in __main__ and the per-file try/except in compute_day_stats provide two layers of protection.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None. The plan's column auto-detection regex (`^PE1.*cnt`) correctly matched the actual device column `PE1 CntDig1` as the pellet counter. The real CSV does not have an `L_runtime` column (uses `PE1 Runtime[h]` instead), so `runtime_minutes` is NULL for this device — this is expected behavior per the plan spec; `runtime` detection requires exact `L_runtime` match.

## User Setup Required

None — no external service configuration required. stats.db is created automatically alongside server.py on first run.

## Next Phase Readiness

- GET /stats endpoint is live and returns valid JSON with all required fields
- Phase 09-02 (Statistics UI) can consume /stats directly — the endpoint contract is stable
- Phase 10 (AI Integration) can use get_all_stats() or call /stats to build AI context payloads
- If a device uses `PE1 Runtime[h]` instead of `L_runtime`, runtime_minutes will be NULL — Phase 09-02 UI must handle null gracefully

---
*Phase: 09-data-aggregation*
*Completed: 2026-02-26*
