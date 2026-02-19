---
phase: 03-navigation-and-interaction
plan: 04
subsystem: ui
tags: [uplot, minimap, zoom, overview, canvas]

# Dependency graph
requires:
  - phase: 03-01
    provides: AppState.onZoomChange stub, setScale hook wired to AppState.onZoomChange
  - phase: 02-01
    provides: uPlot instance in AppState.chart, buildChartData(), DEFAULT_SERIES
provides:
  - createMinimap() function: secondary uPlot at 72px height with full-day data
  - AppState.minimap { instance, updateSelection } — wired after createChart()
  - Bidirectional zoom sync: main chart zoom highlights minimap; minimap drag zooms main chart
  - Infinite loop prevention via setSelect(..., false)
  - Minimap resize in onWindowResize()
  - Minimap cleanup in destroyChart()
affects: [04-parameter-management]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "setSelect(opts, false) to suppress hook re-fire — prevents bidirectional infinite loop"
    - "Thin series clone for minimap: width:0.5 for continuous, width:0 for binary"
    - "bbox.height / devicePixelRatio to get CSS pixel height for setSelect"

key-files:
  created: []
  modified:
    - index.html

key-decisions:
  - "setSelect(opts, false) is CRITICAL — second argument false prevents minimap setSelect hook from re-firing and causing an infinite zoom loop"
  - "Minimap series cloned from main series with width reduced (0.5/0) to avoid visual noise at 72px height"
  - "minimap-area.innerHTML cleared in destroyChart() to remove uPlot DOM artifacts after destroy()"
  - "buildChartData called second time for minimap data — same DEFAULT_SERIES, same data model"

patterns-established:
  - "Secondary uPlot for overview: legend:false, axes:all hidden, cursor:false, select:true"
  - "Clamp min/max timestamps before valToPos to prevent out-of-bounds setSelect calls"

requirements-completed: [NAVG-05]

# Metrics
duration: 2min
completed: 2026-02-19
---

# Phase 3 Plan 04: Minimap Overview Summary

**Secondary uPlot minimap at 72px showing full-day data with zoom region highlight overlay and drag-to-pan, bidirectional sync via setSelect(opts, false) to prevent infinite loop**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-19T19:41:06Z
- **Completed:** 2026-02-19T19:42:29Z
- **Tasks:** 1 of 2 (Task 2 is human verification checkpoint — paused)
- **Files modified:** 1

## Accomplishments
- `createMinimap()` added: secondary uPlot instance at 72px with full-day data, no legend, no axes, no crosshair
- Bidirectional sync: main chart `setScale` hook calls `minimap.updateSelection()`, minimap `setSelect` hook calls `AppState.chart.setScale()`
- Infinite loop prevented: `uMinimap.setSelect(opts, false)` suppresses the hook re-fire
- `destroyChart()` updated to destroy minimap instance and clear `#minimap-area` DOM
- `onWindowResize()` updated to resize both main chart and minimap on window resize
- `AppState.minimap` stub added to AppState declaration

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement createMinimap() and wire into createChart() and onWindowResize()** - `10dac1e` (feat)

_Task 2 is a checkpoint:human-verify — no code changes, awaits human visual verification._

**Plan metadata:** _(pending — will be committed after checkpoint passes)_

## Files Created/Modified
- `index.html` - createMinimap() function added (~90 lines), AppState.minimap stub, destroyChart() minimap cleanup, onWindowResize() minimap resize, createChart() minimap wiring

## Decisions Made
- `setSelect(opts, false)` is the key infinite-loop guard: the second argument `false` tells uPlot not to fire the `setSelect` hook, so the minimap updating the main chart does not then re-trigger minimap update
- Minimap series are cloned from the main series array with `Object.assign()`, then `width` reduced to `0.5` (continuous) or `0` (binary) to avoid visual noise in the compressed 72px view
- `uMinimap.bbox.height / devicePixelRatio` correctly converts physical canvas pixels to CSS pixels for the `setSelect` height parameter

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- NAVG-05 implementation complete — pending human visual verification (Task 2 checkpoint)
- All 5 NAVG requirements implemented: drag zoom (01), scroll zoom (02), reset button (03), tooltip (04), minimap (05)
- Phase 3 complete after checkpoint approval
- Phase 4 (parameter management) can begin: AppState.chart, AppState.minimap, AppState.chartSeries all available

---
*Phase: 03-navigation-and-interaction*
*Completed: 2026-02-19*
