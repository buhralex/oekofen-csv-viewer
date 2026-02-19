---
phase: 03-navigation-and-interaction
plan: 03
subsystem: ui
tags: [uplot, tooltip, cursor, crosshair, plugins]

# Dependency graph
requires:
  - phase: 03-02
    provides: wheelZoomPlugin() in plugins array, cursor.show:true, createChart() structure ready for additional plugins
provides:
  - tooltipPlugin() function with init and setCursor hooks
  - Tooltip CSS rules (#chart-tooltip, .tt-time, .tt-row, .tt-swatch, .tt-label, .tt-val)
  - Cursor crosshair + floating tooltip showing HH:MM time and raw series values
  - Left/right flip positioning to avoid chart boundary overflow
affects:
  - 03-04 (minimap — shares u.over with tooltip, must not conflict)
  - 04 (series toggle — tooltip already skips show:false series)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - uPlot plugin pattern with hooks.init (DOM setup) and hooks.setCursor (live update)
    - Tooltip left/right flip: check (left + ttW + OFFSET) > chartW before placing
    - s.stroke function resolution: typeof s.stroke === 'function' ? s.stroke(u, i) : s.stroke

key-files:
  created: []
  modified:
    - index.html

key-decisions:
  - "OFFSET=12px gap between cursor line and tooltip edge — enough clearance without feeling detached"
  - "tooltip.offsetWidth || 180 fallback: first render may have zero width before display is set; 180px is a safe default"
  - "Math.max(0, top - 20) for vertical position: offset upward by 20px so tooltip header aligns near cursor rather than below it"
  - "s.stroke function check: uPlot allows stroke to be a function (e.g. gradients); resolve before inserting into HTML style attribute"
  - "No forced rounding on displayed values: raw CSV values shown as-is per CONTEXT.md decision"

patterns-established:
  - "Plugin pattern: function returning { hooks: { init: [...], setCursor: [...] } } — same structure as wheelZoomPlugin"
  - "DOM append to u.over: tooltip lives inside the chart overlay, participates in chart coordinate system"

requirements-completed: [NAVG-04]

# Metrics
duration: 1min
completed: 2026-02-19
---

# Phase 3 Plan 03: Cursor Tooltip Summary

**uPlot tooltipPlugin() with setCursor hook delivering HH:MM time header and per-series raw values, with left/right flip to stay within chart bounds**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-19T19:37:23Z
- **Completed:** 2026-02-19T19:38:37Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Added all 6 tooltip CSS rules (#chart-tooltip, .tt-time, .tt-row, .tt-swatch, .tt-label, .tt-val) for dark-themed floating tooltip
- Implemented tooltipPlugin() function with init hook (DOM creation, mouseleave/mouseenter wiring) and setCursor hook (live value display)
- Wired tooltipPlugin() into createChart() plugins array alongside wheelZoomPlugin()
- NAVG-04 satisfied: users can now read exact values at any cursor position including time, all visible series with color swatches

## Task Commits

Each task was committed atomically:

1. **Task 1: Add tooltip CSS rules to the style block** - `7feb5fc` (feat)
2. **Task 2: Implement tooltipPlugin() and wire into createChart()** - `20fa8e9` (feat)

**Plan metadata:** *(final docs commit)*

## Files Created/Modified
- `index.html` - Tooltip CSS rules added to style block; tooltipPlugin() function added below wheelZoomPlugin(); plugins array updated to include tooltipPlugin()

## Decisions Made
- OFFSET=12px gap between cursor line and tooltip edge
- tooltip.offsetWidth || 180 fallback for first-render width
- Math.max(0, top - 20) for vertical clamping to chart top
- s.stroke function resolution handles uPlot gradient stroke patterns
- No forced rounding on values: raw CSV numbers shown as-is per CONTEXT.md

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Tooltip plugin complete and operational — Phase 3 plan 04 (minimap) can proceed
- tooltipPlugin appends to u.over — minimap uses a separate uPlot instance on #minimap-area, no conflict expected
- Phase 4 series toggle (setSeries with show:false) will be correctly handled by tooltip: hidden series are already filtered out via `if (s.show === false) continue`

---
*Phase: 03-navigation-and-interaction*
*Completed: 2026-02-19*
