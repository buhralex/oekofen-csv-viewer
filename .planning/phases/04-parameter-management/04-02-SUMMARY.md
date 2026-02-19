---
phase: 04-parameter-management
plan: 02
subsystem: ui
tags: [uplot, setSeries, legend, event-delegation, series-toggle]

# Dependency graph
requires:
  - phase: 04-parameter-management/04-01
    provides: applyLegendRowStyle(), updateViewState(), buildViewTabs/destroyViewTabs, .u-legend pointer-events:auto
  - phase: 03-navigation-and-interaction
    provides: createChart(), destroyChart(), AppState.chart uPlot instance
provides:
  - wireLegendClicks(u) — event delegation on .u-legend for per-series show/hide toggle
  - unwireLegendClicks() — removes click handler stored on legend._phase4ClickHandler
  - Legend rows have cursor:pointer applied on chart creation
  - Zoom-safe series toggle via u.setSeries() (no chart recreate)
affects:
  - 04-03 (no direct dependency, but legend state consistent with picker modal changes)
  - 04-04 (updateViewState() already wired — savePrefs hook will fire on legend clicks)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Event delegation on .u-legend element — single listener, not per-row"
    - "Handler reference stored on DOM element (legend._phase4ClickHandler) for targeted cleanup"
    - "rowIndex + 1 offset for uPlot series index — series[0] is x-axis with no legend row when legend.live:false"
    - "unwireLegendClicks() called BEFORE AppState.chart.destroy() in destroyChart()"

key-files:
  created: []
  modified:
    - index.html

key-decisions:
  - "Event delegation pattern on .u-legend (not per-row listeners) — simpler cleanup, no risk of multiple listeners per row"
  - "Handler stored on legend._phase4ClickHandler (DOM property) — avoids closure variable issues across reloads"
  - "unwireLegendClicks() positioned before AppState.chart.destroy() — legend DOM must still exist for removeEventListener"
  - "currentShow = u.series[seriesIdx].show !== false — reads live uPlot state, not a local cache"

patterns-established:
  - "Cleanup functions must access DOM through AppState.chart.root before chart.destroy() tears down DOM"
  - "Phase 4 cleanup order: destroyViewTabs() → unwireLegendClicks() → AppState.chart.destroy()"

requirements-completed: [PARM-02]

# Metrics
duration: 1min
completed: 2026-02-19
---

# Phase 4 Plan 02: Legend Click Toggle Summary

**Event delegation on .u-legend for zoom-safe per-series show/hide toggle with opacity/line-through visual feedback and cleanup on file reload**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-19T21:30:30Z
- **Completed:** 2026-02-19T21:31:47Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Added `wireLegendClicks(u)` — event delegation on `.u-legend` table; applies `cursor:pointer` to all series rows; toggles series via `u.setSeries(seriesIdx, { show: newShow })`
- Added `unwireLegendClicks()` — removes the click handler stored on `legend._phase4ClickHandler`, preventing listener accumulation on file reload
- Correct `rowIndex + 1` index offset applied (series[0] is the x-axis, has no legend row when `legend.live:false`)
- `applyLegendRowStyle()` called after each toggle for opacity 0.35 + line-through visual feedback
- `updateViewState()` called after each toggle so tab indicator stays accurate (e.g., hiding a series from "All" shows "Custom")
- `destroyChart()` cleanup order correct: `destroyViewTabs()` → `unwireLegendClicks()` → `AppState.chart.destroy()`

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire legend click delegation and integrate into createChart()/destroyChart()** - `a97cf06` (feat)

**Plan metadata:** `[pending final commit]` (docs: complete plan)

## Files Created/Modified

- `index.html` — 70 lines added: `wireLegendClicks()`, `unwireLegendClicks()`, call sites in `createChart()` and `destroyChart()`

## Decisions Made

- Used event delegation on `.u-legend` (not per-row listeners) — single handler to add/remove, no risk of stale per-row listeners accumulating across reloads
- Stored handler reference on `legend._phase4ClickHandler` DOM property — avoids closure variable scope issues when `unwireLegendClicks()` is called from a different execution context
- `unwireLegendClicks()` called before `AppState.chart.destroy()` — the legend DOM element (and its stored handler reference) must still exist for `removeEventListener` to function

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 04-03 can wire `#params-btn` click to open the picker modal — legend click state and updateViewState() are fully operational
- 04-04 `savePrefs()` will automatically fire on legend clicks because `updateViewState()` is already called after each toggle

## Self-Check: PASSED

- FOUND: `.planning/phases/04-parameter-management/04-02-SUMMARY.md`
- FOUND: commit `a97cf06` (Task 1 — wireLegendClicks + unwireLegendClicks)

---
*Phase: 04-parameter-management*
*Completed: 2026-02-19*
