# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-17)

**Core value:** Enable the user to visually diagnose why and when the heater fires by interactively exploring temperature curves, pump states, and pellet unit behavior across a single day's data.
**Current focus:** Phase 2 - Chart Rendering

## Current Position

Phase: 2 of 4 (Chart Rendering) — COMPLETE
Plan: 2 of 2 complete (02-01 complete, 02-02 complete)
Status: Phase 2 fully complete — all four CHRT requirements human-verified; Phase 3 planning is next
Last activity: 2026-02-18 — 02-02 complete: resize handler, benchmarkSeriesToggle(), human-verified (approved)

Progress: [██████░░░░] 60%

## Performance Metrics

**Velocity:**
- Total plans completed: 5
- Average duration: ~24 min
- Total execution time: ~1 hour

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 3/3 | ~80 min | ~27 min |
| 2. Chart Rendering | 2/3 | ~33 min | ~16 min |

**Recent Trend:**
- Last 5 plans: 01-01 (15 min), 01-02 (~30 min), 01-03 (~35 min), 02-01 (~25 min), 02-02 (~8 min)
- Trend: Steady

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: Web-based client-side only approach confirmed; uPlot 1.6.32 + PapaParse 5.5.3 selected as the stack
- [Init]: One-way data pipeline architecture mandated: File drop → Parse → Normalize → Data Model → View → Chart
- [Init]: Phase 1 must be verified against a real OekoFEN CSV file before Phase 2 begins — normalizer is highest-risk component
- [01-01]: Dark navy theme (#1a1a2e, #4fc3f7 accent) chosen for chart readability
- [01-01]: CSS custom properties established as theming system — all plans extend :root vars
- [01-01]: UI transition functions showDropZone() / showAppView(filename) defined as the state transition pair for Plans 02+
- [01-01]: showToast() / setStatus() established as feedback primitives for all subsequent plans
- [01-02]: Window-level dragover+drop guard must attach to window (not drop zone) — only then does LOAD-03 (outside-zone drops) work
- [01-02]: dragDepth counter pattern used to prevent flicker — increment on dragenter, decrement on dragleave, remove CSS class only at zero
- [01-02]: handleFileDrop() is the single validation entry point for both drag and file picker paths
- [01-02]: onFileAccepted(file) is the handoff boundary — Plan 03 replaces the stub body with the parse pipeline
- [01-03]: TextDecoder('windows-1252') required — real OekoFEN file is ISO-8859-1 with no BOM; UTF-8 produces mojibake
- [01-03]: IGNORED_COLUMNS Set(['Fehler1','Fehler2','Fehler3','Zubrp1 Pumpe']) — excluded at parse time, 64 data columns result from 70 raw minus 2 timestamp minus 4 ignored
- [01-03]: BINARY_COLUMNS Set(['BR','Sperrzeit']) — type:'discrete' signals Phase 2 to use step chart rendering
- [01-03]: PE1 group unified as 'Pellet Unit (PE1)', not split — per CONTEXT.md locked decision
- [01-03]: AppState.dataModel shape locked: { isOekoFEN, timestamps[], columns[], parseIssues, rowCount } — Phase 2 consumes this directly
- [02-01]: uPlot.paths.stepped({ align: 1 }) used for BR binary series — step interpolation not linear, renders as filled 0/1 band
- [02-01]: Dual-axis architecture set at construction time: left 'y' (auto-scale), right 'binary' (fixed 0-1) — cannot add axes after uPlot init
- [02-01]: cursor.show:false and select.show:false at construction — Phase 3 owns all interactive overlay behavior
- [02-01]: AppState.onZoomChange and AppState.zoomRange stubs initialized as null — Phase 3 assigns these
- [02-01]: X-axis formatted via getUTCHours/getUTCMinutes — timestamps are UTC, local timezone must not shift display
- [02-02]: Resize debounced at 100ms — plan's 200ms redraw budget leaves margin for uPlot render after debounce fires
- [02-02]: benchmarkSeriesToggle() runs 20 toggle iterations — stable average without prolonged visible flicker; restores series[1] to show:true at end

### Pending Todos

None.

### Blockers/Concerns

- [Phase 1 RESOLVED]: CSV schema validated — ISO-8859-1, semicolon delimiter, trailing semicolons, trailing spaces in column names. Plans reflect actual file format.
- [Phase 1 RESOLVED]: Column group rules hardcoded from real file inspection — HK1, WW1, PU1, PE1 prefix-based; Boiler explicit list.
- [Advisory]: PARS-03 implemented via TextDecoder('windows-1252') not BOM stripping — real file has no BOM. Excel-generated UTF-8 BOM files not handled (future concern if needed).
- [Advisory 02-01]: DEFAULT_SERIES rawNames are based on the known real OekoFEN CSV schema. If a file has different column names, buildChartData() will warn and skip unresolved series. Phase 4 will make series selection dynamic.

## Session Continuity

Last session: 2026-02-18
Stopped at: Phase 3 context gathered — ready for /gsd:plan-phase 3
Resume file: .planning/phases/03-navigation-and-interaction/03-CONTEXT.md
