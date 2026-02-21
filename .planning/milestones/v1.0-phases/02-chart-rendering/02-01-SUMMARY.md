---
phase: 02-chart-rendering
plan: 01
subsystem: ui
tags: [uplot, chart, visualization, timeseries, dark-theme]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: AppState.dataModel shape (timestamps[], columns[], isOekoFEN, rowCount, parseIssues)
provides:
  - buildChartData(dataModel, seriesNames) — converts dataModel to uPlot columnar format
  - createChart() — constructs uPlot instance with dual axes, 9 default series, binary band
  - destroyChart() — tears down uPlot instance and clears chart-area DOM
  - DEFAULT_SERIES constant — 9 rawNames for default visible series
  - AppState.chart — uPlot instance handle for Phase 3 zoom integration
  - AppState.chartSeries — series opts array for Phase 4 series management
  - AppState.onZoomChange / AppState.zoomRange stubs — Phase 3 hook points
affects:
  - 03-zoom-cursor
  - 04-parameter-management

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dual-axis uPlot construction: left 'y' (auto-scale continuous), right 'binary' (fixed 0-1)"
    - "buildChartData() bridge: dataModel -> uPlot columnar arrays + series opts in single call"
    - "Group-based color assignment with per-series override map for visual hierarchy"
    - "Binary series rendered as stepped fill band (scale:'binary', width:0, fill:rgba)"
    - "createChart/destroyChart lifecycle: always destroy before recreating — idempotent"

key-files:
  created: []
  modified:
    - index.html

key-decisions:
  - "uPlot.paths.stepped({ align: 1 }) used for BR binary series — step interpolation not linear"
  - "chart-area top:90px to clear both header (50px) and data-summary (~40px) panels"
  - "cursor.show:false and select.show:false — Phase 3 owns all interactive overlay behavior"
  - "legend.live:false — Phase 3 cursor plugin will handle live value display"
  - "X-axis uses getUTCHours/Minutes — CSV timestamps are UTC, local timezone would shift display"
  - "AppState.onZoomChange and AppState.zoomRange stubs initialized as null — Phase 3 assigns"

patterns-established:
  - "Pattern 1: All chart opts are set at uPlot construction time — dual axes cannot be added after"
  - "Pattern 2: buildChartData() resolves rawNames gracefully — missing series log warning, don't throw"
  - "Pattern 3: Phase N lifecycle extension via AppState fields — consumers null-check before use"

requirements-completed: [CHRT-01, CHRT-02]

# Metrics
duration: 25min
completed: 2026-02-18
---

# Phase 2 Plan 1: uPlot Chart Instance with Dual Axes and Binary Band Rendering Summary

**uPlot chart with dual-axis architecture (continuous auto-scale left, binary fixed-0-1 right), stepped BR fill band, group-based color scheme, and floating legend on dark navy theme**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-02-18T20:02:45Z
- **Completed:** 2026-02-18T20:27:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- `buildChartData()` converts `AppState.dataModel` to uPlot's columnar data format with per-series opts (scale, color, width, paths) in a single call
- `createChart()` constructs a uPlot instance with dual Y-axes: left auto-scales to temperature/percentage series, right fixed 0-1 for BR binary burner state
- BR series rendered as a filled semi-transparent stepped band (not interpolated line) using `uPlot.paths.stepped({ align: 1 })`
- Chart title formatted as DD.MM.YYYY from filename date, X-axis displays HH:MM in UTC
- CSS dark theme overrides applied for `.u-wrap`, `.u-legend` (floating top-left), `.u-title`
- `destroyChart()` cleanly tears down uPlot and clears DOM — idempotent on Load Another

## Task Commits

Each task was committed atomically:

1. **Task 1: buildChartData() series builder and DEFAULT_SERIES** - `9c518c8` (feat)
2. **Task 2: createChart/destroyChart and wire into onFileAccepted** - `53b6ee3` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `index.html` — Added DEFAULT_SERIES, GROUP_COLORS, SERIES_COLOR_OVERRIDES, buildChartData(), destroyChart(), createChart(); expanded AppState; updated #chart-area CSS and uPlot dark theme overrides; rewired onFileAccepted() and Load Another handler

## Decisions Made
- `uPlot.paths.stepped({ align: 1 })` for BR binary series — renders as step function (0 or 1), not a smoothed line between values
- `chart-area` top set to 90px — accounts for both app-header (50px) and data-summary (~40px) above
- `cursor.show: false` and `select.show: false` — Phase 3 owns all interactive crosshair and zoom-selection behavior
- `legend.live: false` — Phase 3 cursor plugin will populate live values; for now legend shows series labels only
- X-axis formatted via `getUTCHours()`/`getUTCMinutes()` — timestamps are UTC, local timezone would shift the display
- `AppState.onZoomChange` and `AppState.zoomRange` initialized as `null` stubs for Phase 3 to populate

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
None. The `createChart()` function is placed before `buildDataModel()` in the file (because it was inserted before the STEP 7 comment), but since all are `function` declarations they hoist correctly — no execution order issues.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- `AppState.chart` is the live uPlot instance — Phase 3 can call `AppState.chart.setScale()` for zoom and attach a cursor plugin
- `AppState.chartSeries` holds the series opts array — Phase 4 can call `AppState.chart.setSeries(idx, { show: false })` to toggle visibility
- `AppState.onZoomChange` stub ready for Phase 3 minimap to subscribe
- The chart's `padding: [10, 0, 0, 0]` leaves top room for the title; Phase 3 minimap will require a layout change (separate container, not padding)

---
*Phase: 02-chart-rendering*
*Completed: 2026-02-18*

## Self-Check: PASSED

- FOUND: index.html
- FOUND: .planning/phases/02-chart-rendering/02-01-SUMMARY.md
- FOUND: commit 9c518c8 (Task 1 - buildChartData)
- FOUND: commit 53b6ee3 (Task 2 - createChart/destroyChart)
- VERIFIED: buildChartData, createChart, destroyChart, DEFAULT_SERIES, AppState.chart all present in index.html
