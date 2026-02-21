# Phase 3: Navigation and Interaction - Context

**Gathered:** 2026-02-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Add interactive navigation to the Phase 2 uPlot chart: drag-to-zoom, scroll-wheel zoom, cursor crosshair with tooltip, minimap overview, and reset. Does NOT include parameter management (view tabs, series toggling, custom selection, localStorage) — those are Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Zoom behavior
- Drag direction: any direction selects a time range and zooms in — the range is determined by the min/max of the drag endpoints regardless of direction (left-to-right or right-to-left both work)
- After-drag behavior: Claude's Discretion (instant snap is uPlot's native behavior and is preferred for responsiveness)
- Scroll-wheel zoom centering: Claude's Discretion (cursor-centered is the standard for data exploration tools)
- Min/max zoom limits: Claude's Discretion (sensible limits for 1-minute sample interval data — e.g., no zooming in past a few data points, no zooming out past the full 24h day)

### Cursor tooltip
- Shows values for ALL currently visible series (not just nearest-to-cursor)
- Tooltip header: shows exact time at cursor position in HH:MM format (e.g., "14:32") at the top of the value list
- Value format: raw value as parsed from CSV (variable precision — no forced rounding)
- Tooltip placement: Claude's Discretion (should not obscure the chart area where the cursor is active)

### Reset & navigation controls
- Reset zoom method: BOTH a visible button AND double-click on the chart
- Reset button placement: new toolbar row below the header bar, above the chart — this row will also hold Phase 4 view tabs later
- Reset button visibility: hidden when at full day view (not zoomed), appears when zoomed in
- Toolbar contents for Phase 3: reset button only — Phase 4 adds view tabs to the same row

### Minimap (not discussed — see Claude's Discretion)
- User did not select minimap for discussion — all minimap decisions at Claude's Discretion

### Claude's Discretion
- **Drag-zoom after behavior**: instant snap (no animation) — uPlot's native `setScale` is synchronous and instant
- **Scroll zoom centering**: cursor-centered — the timestamp under the cursor stays fixed while the visible range contracts around it
- **Zoom limits**: minimum ~5 minutes visible (5 data points at 1-min interval), maximum full 24h day
- **Tooltip placement**: snapping panel — floats near the cursor but flips left/right to stay inside the chart boundary and avoid covering the active area
- **Minimap height and style**: secondary uPlot instance or canvas-based; height approximately 60–80px below the main chart; renders a simplified version of the same series; the zoom selection region is highlighted as a semi-transparent overlay; draggable to pan
- **Scroll-wheel page guard**: prevent the scroll event from scrolling the page when the cursor is over the chart (event.preventDefault())
- **Zoom state storage**: `AppState.zoomRange = { min, max }` (already stubbed in Phase 2); `AppState.onZoomChange(min, max)` called after each zoom to notify minimap

</decisions>

<specifics>
## Specific Ideas

- The toolbar row for the reset button is being designed to also accommodate Phase 4 view tabs — plan accordingly so Phase 4 doesn't need to restructure the toolbar
- The minimap was not discussed by user — Claude has full discretion on implementation approach (secondary uPlot, canvas brush, etc.)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 3 scope.

</deferred>

---

*Phase: 03-navigation-and-interaction*
*Context gathered: 2026-02-18*
