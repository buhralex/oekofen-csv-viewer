# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-17)

**Core value:** Enable the user to visually diagnose why and when the heater fires by interactively exploring temperature curves, pump states, and pellet unit behavior across a single day's data.
**Current focus:** Phase 4 - Parameter Management

## Current Position

Phase: 4 of 4 (Parameter Management) — IN PROGRESS
Plan: 1 of 4 complete
Status: 04-01 complete — Phase 4 state machine + view tab bar live; pointer-events fix applied; ready for 04-02 (legend click toggle)
Last activity: 2026-02-19 — 04-01 executed: VIEW_GROUPS, buildViewPresets, setActiveView, tab bar DOM wired to createChart/destroyChart

Progress: [██████████] 75% (3/4 phases complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 10
- Average duration: ~15 min
- Total execution time: ~1h 38m

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 3/3 | ~80 min | ~27 min |
| 2. Chart Rendering | 2/2 | ~33 min | ~16 min |
| 3. Navigation and Interaction | 4/4 | ~40 min | ~10 min |

**Recent Trend:**
- Last 5 plans: 03-01 (~2 min), 03-02 (~1 min), 03-03 (~1 min), 03-04 (~36 min with verification)
- Trend: Phase 3 avg inflated by 03-04 human checkpoint; implementation itself was fast

*Updated after each plan completion*
| Phase 04-parameter-management P01 | 2 | 2 tasks | 1 files |

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
- [03-01]: Reset button uses inline style display toggle (not CSS class) — avoids conflicts with toolbar-row flex layout
- [03-01]: destroyChart() nulls AppState.zoomRange and AppState.onZoomChange — prevents stale minimap callbacks after file reload
- [03-01]: cursor.drag.dist:3 minimum pixel distance before zoom activates — prevents accidental zoom from mis-clicks
- [03-01]: Double-click wired explicitly on u.over as backup — ensures consistent cross-browser behavior alongside uPlot native dblclick reset
- [03-02]: factor:0.75 per scroll tick — 25% range change per zoom step, matches uPlot demo pattern
- [03-02]: MIN_RANGE=300s enforces 5-minute minimum visible window for scroll zoom
- [03-02]: Range-shift clamping at data edges: shifts entire window to preserve requested range width (not truncation)
- [03-03]: tooltipPlugin() uses init hook to append #chart-tooltip div to u.over and setCursor hook for live value display
- [03-03]: OFFSET=12px gap between cursor line and tooltip edge; tooltip.offsetWidth || 180 fallback for first-render width
- [03-03]: Left/right flip: (left + ttW + OFFSET) > chartW triggers tooltip to render left of cursor line
- [03-03]: s.stroke resolved via typeof check — handles uPlot gradient stroke functions; no forced rounding on raw values (per CONTEXT.md)
- [Phase 03]: setSelect(opts, false) is CRITICAL for minimap: second argument false prevents minimap setSelect hook re-firing and infinite zoom loop
- [Phase 03]: Minimap series cloned with Object.assign(), width:0.5 for continuous / width:0 for binary — avoids visual noise at 72px
- [03-04]: cursor.show:true + cursor.drag.setScale:false in minimap — cursor.show:false silently disables drag in uPlot
- [03-04]: Reset zoom requires explicit {min: dataMin, max: dataMax} — {min:null,max:null} not recognized by uPlot 1.6.32
- [03-04]: Drag-zoom 300s floor via pre-clamped values before setScale — hook-based approaches failed due to uPlot re-entrancy
- [03-04]: display:block required for tooltip show — display:'' inherits CSS display:none from stylesheet
- [04-01]: pointer-events:auto on .u-legend — tooltip reads u.series[i].show, does not depend on legend being non-interactive; required for 04-02 legend click events
- [04-01]: buildViewPresets() queries dataModel.columns at runtime — tabs only for groups present in file; AT column appended via name-part regex for context
- [04-01]: setSeries(i, {show}, false) third-arg false during batch tab switch suppresses hooks; updateViewState() called once after loop
- [04-01]: #params-btn placed in HTML as display:none stub, shown/hidden with tab bar; wiring deferred to 04-03

### Pending Todos

None.

### Blockers/Concerns

- [Phase 1 RESOLVED]: CSV schema validated — ISO-8859-1, semicolon delimiter, trailing semicolons, trailing spaces in column names. Plans reflect actual file format.
- [Phase 1 RESOLVED]: Column group rules hardcoded from real file inspection — HK1, WW1, PU1, PE1 prefix-based; Boiler explicit list.
- [Advisory]: PARS-03 implemented via TextDecoder('windows-1252') not BOM stripping — real file has no BOM. Excel-generated UTF-8 BOM files not handled (future concern if needed).
- [Advisory 02-01]: DEFAULT_SERIES rawNames are based on the known real OekoFEN CSV schema. If a file has different column names, buildChartData() will warn and skip unresolved series. Phase 4 will make series selection dynamic.

## Session Continuity

Last session: 2026-02-19
Stopped at: Completed 04-01-PLAN.md (Phase 4 state machine + view tab bar)
Resume file: .planning/phases/04-parameter-management/04-02-PLAN.md
