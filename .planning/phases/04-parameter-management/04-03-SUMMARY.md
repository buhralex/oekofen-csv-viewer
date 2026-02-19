---
phase: 04-parameter-management
plan: 03
subsystem: ui
tags: [uplot, setSeries, modal, parameter-picker, event-delegation]

# Dependency graph
requires:
  - phase: 04-parameter-management/04-01
    provides: buildViewTabs/destroyViewTabs, updateViewState(), getVisibleRawNames(), VIEW_GROUPS, applyLegendRowStyle()
  - phase: 04-parameter-management/04-02
    provides: wireLegendClicks/unwireLegendClicks, unwireLegendClicks() cleanup ordering
  - phase: 03-navigation-and-interaction
    provides: createChart(), destroyChart(), AppState.chart uPlot instance
provides:
  - openPickerModal() — builds and shows full dialog DOM on each open
  - closePickerModal() — removes #picker-modal from DOM; safe to call when modal is not open
  - #params-btn click handler wired in buildViewTabs() using _paramsHandler pattern
  - closePickerModal() called as third cleanup in destroyChart()
affects:
  - 04-04 (savePrefs() fires via updateViewState() called after Apply)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Modal built from DOM elements on each open (not cached) — chart is source of truth at open time"
    - "_paramsHandler DOM property pattern — removes previous listener before re-attaching on file reload"
    - "Escape listener self-removes via document.removeEventListener after closePickerModal() fires"
    - "Backdrop click closes on e.target === backdrop — not on dialog click"
    - "seriesIdx via AppState.chartSeries.findIndex((s, i) => i > 0 && s.label === rawName)"

key-files:
  created: []
  modified:
    - index.html

key-decisions:
  - "closePickerModal() positioned as third cleanup in destroyChart() — before AppState.chart.destroy() so it's safe to call even if chart is null"
  - "openPickerModal() uses function declaration (not arrow fn) — hoisted, callable from destroyChart() defined earlier in file"
  - "groupOrder from Object.values(VIEW_GROUPS).filter(g => g !== null) — preserves VIEW_GROUPS insertion order for group display"
  - "seriesIdx lookup uses AppState.chartSeries (not u.series directly) — chartSeries is stable across setSeries calls"
  - "Escape listener removed after closePickerModal() fires — prevents lingering global keydown listener"

patterns-established:
  - "Phase 4 cleanup order in destroyChart(): destroyViewTabs() -> unwireLegendClicks() -> closePickerModal() -> chart.destroy()"
  - "Modal Apply reads live chart state at Apply time (cb.checked vs u.series[i].show) — single source of truth"

requirements-completed: [PARM-03]

# Metrics
duration: 1min
completed: 2026-02-19
---

# Phase 4 Plan 03: Parameter Picker Modal Summary

**DOM-built picker modal with group sections, pre-checked live chart state, Apply/Cancel/Escape/backdrop dismiss, and binary badges for discrete columns**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-19T21:34:02Z
- **Completed:** 2026-02-19T21:35:30Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Added `openPickerModal()` — builds full picker dialog DOM on each open; reads `getVisibleRawNames()` at open time so pre-check state reflects live chart visibility
- Added `closePickerModal()` — removes `#picker-modal` from DOM; safe to call when modal is not open (guard: `if (modal) modal.remove()`)
- Group sections ordered by `VIEW_GROUPS` order (Boiler, Heating Circuit, Hot Water, Buffer, Pellet Unit); collapsible on header click with chevron rotation
- Binary badge (`'binary'`) rendered for `col.type === 'discrete'` columns (BR, Sperrzeit)
- Apply loop: finds `seriesIdx` via `AppState.chartSeries.findIndex((s, i) => i > 0 && s.label === rawName)`, calls `u.setSeries(seriesIdx, { show: wantShow })` for changed series only, syncs legend row styles via `applyLegendRowStyle()`, calls `updateViewState()` once after loop
- Cancel button, backdrop click (`e.target === backdrop`), and Escape key all close without changes
- Escape listener self-removes after `closePickerModal()` fires — no lingering global keydown listener
- `#params-btn._paramsHandler` pattern prevents click listener accumulation across file reloads
- `closePickerModal()` added as third cleanup in `destroyChart()` (after `unwireLegendClicks()`, before `AppState.chart.destroy()`)

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement openPickerModal() and closePickerModal() and wire to #params-btn** - `3e66e16` (feat)

**Plan metadata:** `[pending final commit]` (docs: complete plan)

## Files Created/Modified

- `index.html` — 209 lines added: `openPickerModal()`, `closePickerModal()`, `closePickerModal()` in `destroyChart()`, `_paramsHandler` wiring in `buildViewTabs()`

## Decisions Made

- `closePickerModal()` placed as third cleanup in `destroyChart()` — before `AppState.chart.destroy()` ensures the call is safe whether or not chart exists, since `closePickerModal()` only touches `#picker-modal` DOM
- `groupOrder` derived from `Object.values(VIEW_GROUPS).filter(g => g !== null)` — reuses the canonical group order defined in 04-01 without duplication
- Escape listener is a named function `onEscape` that removes itself — avoids the common bug of a permanent document-level keydown listener that fires after modal is closed

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 04-04 can add `savePrefs()` to `updateViewState()` — the hook point is already marked in a comment inside that function
- All three visibility change paths (tab click, legend click, picker Apply) call `updateViewState()` consistently — `savePrefs()` will fire for all of them automatically

## Self-Check: PASSED

- FOUND: `.planning/phases/04-parameter-management/04-03-SUMMARY.md`
- FOUND: commit `3e66e16` (Task 1 — openPickerModal + closePickerModal)

---
*Phase: 04-parameter-management*
*Completed: 2026-02-19*
