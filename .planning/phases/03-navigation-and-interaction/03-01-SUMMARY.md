---
phase: 03-navigation-and-interaction
plan: 01
subsystem: ui
tags: [uPlot, drag-zoom, zoom-reset, css-layout, chart-interaction]

# Dependency graph
requires:
  - phase: 02-chart-rendering
    provides: createChart() with uPlot instance in AppState.chart, AppState.zoomRange/onZoomChange stubs
provides:
  - Drag-to-zoom via native uPlot cursor.drag.setScale:true
  - Reset zoom via #reset-zoom-btn button and double-click on chart
  - CSS layout structure: #toolbar-row (90px-122px), #chart-area (122px to 100px from bottom), #minimap-area (72px above status bar)
  - AppState.zoomRange updated on every zoom change
  - AppState.onZoomChange callback called on every zoom change
  - updateResetButtonVisibility() helper for Phase 3 plans to call
affects:
  - 03-02 (minimap — subscribes to AppState.onZoomChange, uses #minimap-area)
  - 03-03 (crosshair/tooltip — uses cursor already enabled here)
  - 03-04 (keyboard navigation — depends on zoom infrastructure)
  - 04-parameter-management (no direct dependency, but layout is stable)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "uPlot cursor.drag.setScale:true for native drag-to-zoom without custom plugin"
    - "hooks.setScale to intercept zoom changes and write to AppState"
    - "CSS class .visible toggled by showAppView()/showDropZone() for all new elements"
    - "Inline display:none on #reset-zoom-btn controlled by updateResetButtonVisibility() — not by CSS class"
    - "1-second float tolerance in updateResetButtonVisibility() to avoid rounding false-positives"

key-files:
  created: []
  modified:
    - index.html

key-decisions:
  - "Reset button uses inline style display toggle (not CSS class) — avoids CSS specificity conflicts with toolbar-row flex layout"
  - "destroyChart() now nulls AppState.zoomRange and AppState.onZoomChange — prevents stale minimap callbacks after file reload"
  - "Double-click wired explicitly on u.over as backup even though uPlot 1.6.x has native dblclick reset — ensures consistent cross-browser behavior"
  - "cursor.drag.dist:3 minimum pixel distance before zoom activates — prevents accidental zoom from mis-clicks"

patterns-established:
  - "updateResetButtonVisibility(u): checks data min/max vs scale min/max with 1s tolerance, shows/hides #reset-zoom-btn"
  - "AppState.onZoomChange and AppState.zoomRange are always null after destroyChart(), set on every setScale('x') event"

requirements-completed: [NAVG-01, NAVG-03]

# Metrics
duration: 2min
completed: 2026-02-19
---

# Phase 3 Plan 01: Navigation Foundation Summary

**Native uPlot drag-to-zoom with reset button, double-click reset, and Phase 3 CSS layout (toolbar row + minimap placeholder) wired to AppState.zoomRange**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-19T19:28:42Z
- **Completed:** 2026-02-19T19:30:43Z
- **Tasks:** 3
- **Files modified:** 1

## Accomplishments
- CSS layout restructured: #toolbar-row at 90-122px, #chart-area from 122px top to 100px from bottom, #minimap-area 72px strip above status bar
- #toolbar-row and #minimap-area HTML added, wired into showAppView()/showDropZone() toggle cycle
- createChart() cursor opts fixed (show:true, drag.setScale:true), select.show:true, hooks.setScale wired to AppState
- updateResetButtonVisibility() helper established; reset button and double-click wired after chart construction
- destroyChart() now clears AppState.zoomRange and AppState.onZoomChange on every chart tear-down

## Task Commits

Each task was committed atomically:

1. **Task 1: CSS layout — add toolbar and minimap rows with CSS variables** - `550eba5` (feat)
2. **Task 2: HTML structure — add toolbar row and minimap placeholder** - `d2d3b46` (feat)
3. **Task 3: Enable drag-to-zoom, zoom state tracking, and reset button in createChart()** - `424080c` (feat)

## Files Created/Modified
- `index.html` - CSS variables, #toolbar-row CSS, #minimap-area CSS, #chart-area layout update, HTML elements, showAppView/showDropZone updates, updateResetButtonVisibility(), modified createChart() opts, reset wiring, destroyChart() AppState cleanup

## Decisions Made
- Reset button uses `btn.style.display` toggle (not CSS class) — avoids conflicts with the `#toolbar-row { display: flex }` layout when .visible is present
- `destroyChart()` now nulls both `AppState.zoomRange` and `AppState.onZoomChange` to prevent stale minimap callbacks firing after a new CSV file is loaded
- `cursor.drag.dist: 3` (min 3px before zoom) prevents accidental zooms from single-pixel mis-clicks
- Double-click handler wired explicitly on `AppState.chart.over` as a reliable backup alongside any uPlot native dblclick behavior

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 3 plans 03-02 through 03-04 can now proceed:
  - 03-02 (minimap): #minimap-area DOM element is ready; AppState.onZoomChange subscription point is live
  - 03-03 (crosshair/tooltip): cursor is now enabled (show:true), crosshair/tooltip can be overlaid
  - 03-04 (keyboard navigation): zoom infrastructure in place for keyboard zoom steps
- No blockers. All NAVG-01 and NAVG-03 requirements satisfied.

---
*Phase: 03-navigation-and-interaction*
*Completed: 2026-02-19*
