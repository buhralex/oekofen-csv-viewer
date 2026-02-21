---
phase: 01-foundation
plan: 03
subsystem: ui
tags: [javascript, papaparse, csv-parsing, textdecoder, windows-1252, data-model, german-locale, timestamps]

# Dependency graph
requires:
  - phase: 01-01
    provides: "index.html with AppState singleton, PapaParse vendored, dark theme CSS"
  - phase: 01-02
    provides: "onFileAccepted(file) handoff boundary — Plan 03 replaces stub body with full parse pipeline"
provides:
  - "readFileAsText(file): ArrayBuffer → TextDecoder('windows-1252') → string (PARS-03)"
  - "parseCSVString(csvString): PapaParse with delimiter:';', header:true (PARS-01)"
  - "normalizeHeaders(papaResult): trims column names, drops empty trailing column from trailing semicolons"
  - "parseGermanValue(str): German decimal comma converter — '23,5' → 23.5, '-2147483648' → integer (PARS-02)"
  - "buildUnixTimestamp(datum, zeit): Date.UTC() from DD.MM.YYYY + HH:MM:SS → Unix seconds (PARS-04)"
  - "classifyColumn(rawName): group (Boiler/HK1/WW1/PU1/PE1) + type (continuous/discrete), IGNORED_COLUMNS excluded"
  - "buildDataModel(fields, rows): AppState.dataModel with timestamps[], columns[] — rawName/displayName/unit/group/type/data (PARS-05)"
  - "showDataSummary(dataModel, filename): DOM panel with file, row/column counts, time range, group breakdown"
  - "AppState.dataModel: fully verified columnar data model ready for Phase 2 chart builder"
affects:
  - 02-charting
  - 03-navigation
  - 04-parameter-management

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TextDecoder('windows-1252') for ISO-8859-1 CSV files — never use UTF-8 for OekoFEN files (no BOM present)"
    - "PapaParse post-processing pattern: normalize headers after parse, do not rely on PapaParse trimming"
    - "German decimal converter: replace comma with dot only after ruling out pure integer (regex /^-?\\d+$/)"
    - "Date.UTC() for timezone-safe timestamp reconstruction — row's own Datum+Zeit columns, never filename date"
    - "Columnar data model: AppState.dataModel.timestamps[] (shared X axis) + columns[] (Y data per series)"
    - "IGNORED_COLUMNS set: Fehler1, Fehler2, Fehler3, Zubrp1 Pumpe — excluded from data model, not charted"
    - "BINARY_COLUMNS set: BR, Sperrzeit — type:'discrete', rendered as step charts in Phase 2"

key-files:
  created: []
  modified:
    - "index.html"

key-decisions:
  - "IGNORED_COLUMNS hardcoded as Set(['Fehler1','Fehler2','Fehler3','Zubrp1 Pumpe']) per CONTEXT.md — excluded at parse time, never enter data model"
  - "BINARY_COLUMNS hardcoded as Set(['BR','Sperrzeit']) — type:'discrete' signals Phase 2 to render as step chart"
  - "PE1 group kept unified as 'Pellet Unit (PE1)' — NOT split into sub-groups (per CONTEXT.md locked decision)"
  - "displayName equals rawName throughout — German CSV names preserved without translation (INTF-02)"
  - "Non-OekoFEN CSV (missing Datum/Zeit) aborts parse with toast; CSV with Datum/Zeit but no AT column shows warning toast but proceeds"
  - "INT32_MIN value (-2147483648 for PE1 Motor RA) treated as valid integer, not a parse error — regex /^-?\\d+$/ handles it"

patterns-established:
  - "AppState.dataModel is the canonical shared data structure: { isOekoFEN, timestamps, columns, parseIssues, rowCount }"
  - "Column descriptor shape: { rawName, displayName, unit, group, type, data } — all Phase 2+ code consumes this"
  - "showDataSummary() renders to #data-summary — Phase 2 may extend this panel with chart controls"

requirements-completed: [PARS-01, PARS-02, PARS-03, PARS-04, PARS-05]

# Metrics
duration: ~35min
completed: 2026-02-17
---

# Phase 1 Plan 03: CSV Parse and Normalize Pipeline Summary

**Windows-1252 TextDecoder + PapaParse semicolon parsing + German decimal conversion + Date.UTC timestamp reconstruction + columnar data model with group/type classification — all five PARS requirements verified against real OekoFEN touch_20260216.csv**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-02-17
- **Completed:** 2026-02-17
- **Tasks:** 2 (1 auto + 1 human-verify checkpoint)
- **Files modified:** 1

## Accomplishments

- Full CSV parse pipeline implemented in index.html: readFileAsText → parseCSVString → normalizeHeaders → buildDataModel → showDataSummary, wired into onFileAccepted() replacing the Plan 02 stub
- All five PARS requirements satisfied and verified against the real OekoFEN file: ISO-8859-1 decoding without mojibake (PARS-03), semicolon delimiter (PARS-01), German decimal comma conversion (PARS-02), timezone-safe UTC second timestamps (PARS-04), full column metadata with group and type (PARS-05)
- AppState.dataModel populated with 1439 rows, 64 data columns (70 raw minus 2 timestamp columns minus 4 ignored), and 5 group categories — verified by user in browser console
- Data summary panel renders after file load: filename, row count, column count, UTC time range, per-group column counts
- All Phase 1 foundation work complete — AppState.dataModel is the verified handoff to Phase 2's chart builder

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement CSV parse and normalize pipeline** - `8b7814d` (feat)
2. **Task 2: Human-verify checkpoint** - User approved (no code commit — verification only)

## Files Created/Modified

- `index.html` - Full pipeline added: readFileAsText, parseCSVString, normalizeHeaders, parseGermanFloat, parseGermanValue, buildUnixTimestamp, parseColumnHeader, classifyColumn, buildDataModel, showDataSummary; onFileAccepted() stub replaced with complete async pipeline; data-summary CSS added

## Decisions Made

- TextDecoder('windows-1252') chosen over TextDecoder('utf-8') — real file has no BOM and is ISO-8859-1 encoded; UTF-8 would produce mojibake (Â°C instead of °C)
- Trailing semicolon handling: filter columns with empty key after trimming, done in normalizeHeaders() post-PapaParse — PapaParse does not do this automatically
- German decimal parsing separates pure integer detection (regex) from float conversion — required because INT32_MIN (-2147483648, PE1 Motor RA) must parse as integer, not fail as a German float
- Column groups and ignored columns hardcoded from real file inspection in RESEARCH.md, not dynamically inferred — deterministic and correct for OekoFEN format

## Deviations from Plan

### Column Count: Plan Estimated ~69, Actual is 64 (Expected and Correct)

**Context:** The plan's how-to-verify section estimated "~69 columns" and the checkpoint description mentioned "~1439 rows, ~69 columns". The actual verified count is 64 data columns.

**Why 64 is correct:**
- Raw CSV: 70 named columns
- Minus 2 timestamp columns: Datum, Zeit (excluded as X-axis, not data columns)
- Minus 4 ignored columns: Fehler1, Fehler2, Fehler3, Zubrp1 Pumpe (per CONTEXT.md IGNORED_COLUMNS)
- **Result: 64 data model columns**

The ~69 estimate in the plan did not account for the 4 IGNORED_COLUMNS being subtracted. The implementation correctly applies all exclusions. User confirmed this is correct behavior during the checkpoint verification.

**No code change was made** — the implementation was correct; only the plan's estimate was imprecise.

---

**Total deviations:** 0 code deviations — plan implemented exactly as specified. Column count discrepancy was a plan estimate error, not an implementation deviation.

## Issues Encountered

None — implementation passed all verification checks on first attempt. The only clarification needed was the column count explanation (64 vs ~69 estimate), which the user confirmed as correct behavior.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- AppState.dataModel is the verified, correct in-memory columnar data structure — Phase 2 chart builder consumes it directly
- Column descriptor shape (rawName, displayName, unit, group, type, data[]) is locked — Phase 2 builds uPlot series from this
- AppState.dataModel.timestamps[] is the shared X-axis array (Unix seconds, UTC) — uPlot uses this as its time axis
- All Phase 1 success criteria satisfied: drag-drop (Plan 02), file picker (Plan 02), outside-drop guard (Plan 02), correct parse (Plan 03), English UI / German names (Plans 01+03)
- Phase 2 can begin immediately: 01-01, 01-02, and 01-03 all complete

---
*Phase: 01-foundation*
*Completed: 2026-02-17*

## Self-Check: PASSED

| Item | Status |
|------|--------|
| 01-03-SUMMARY.md exists | FOUND |
| index.html modified | FOUND |
| Commit 8b7814d exists | FOUND |
