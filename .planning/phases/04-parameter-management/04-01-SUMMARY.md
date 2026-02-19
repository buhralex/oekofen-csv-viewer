---
phase: 04-parameter-management
plan: 01
subsystem: ui
tags: [uplot, setSeries, view-tabs, css, state-machine]

# Dependency graph
requires:
  - phase: 03-navigation-and-interaction
    provides: createChart(), destroyChart(), AppState.chart uPlot instance, setSeries hook
  - phase: 01-foundation
    provides: classifyColumn(), dataModel.columns with group field, DEFAULT_SERIES
provides:
  - VIEW_GROUPS constant (6 system group mappings)
  - buildViewPresets() — builds Map<tabName, rawName[]> at runtime from dataModel
  - matchPreset() — detects preset match or 'Custom'
  - getVisibleRawNames() — reads live chart series visibility
  - updateViewState() — central visibility state updater (hook point for 04-04 savePrefs)
  - updateTabHighlight() — syncs tab active class and Custom indicator
  - setActiveView() — batch setSeries() switch, zoom-safe
  - applyLegendRowStyle() — shared legend row visual helper (used by 04-02 legend click)
  - buildViewTabs() / destroyViewTabs() — tab bar DOM lifecycle
  - #params-btn stub (shown/hidden with tab bar; wired in 04-03)
  - All picker-* CSS classes (ready for 04-03 modal)
  - .u-legend pointer-events:auto (required for 04-02 legend click events)
affects:
  - 04-02 (legend click handler uses applyLegendRowStyle + updateViewState)
  - 04-03 (params-btn click wires picker modal)
  - 04-04 (updateViewState is savePrefs hook point)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "View preset as Map<tabName, rawName[]> built at runtime — not hardcoded"
    - "Event delegation on #view-tabs container for all tab clicks"
    - "setSeries(i, {show}, false) third-arg false suppresses hooks during batch update"
    - "destroyViewTabs() called as first line of destroyChart() — before uPlot.destroy()"

key-files:
  created: []
  modified:
    - index.html

key-decisions:
  - "pointer-events:auto on .u-legend — tooltip reads u.series[i].show, does not depend on legend being non-interactive; auto required for 04-02 legend click events"
  - "buildViewPresets() queries dataModel.columns at runtime — tabs only rendered for groups present in the file, no hardcoded rawNames"
  - "AT column appended to each system group tab (found by matching name-part 'AT') for cross-system context"
  - "setSeries third-arg false (suppress hooks) during batch tab switch — avoids N redundant updateViewState calls, one call after loop"
  - "#params-btn placed in HTML with display:none — shown/hidden by buildViewTabs/destroyViewTabs; not wired until 04-03"

patterns-established:
  - "Phase 4 state (_viewPresets, _activeView) is module-level — accessible by all subsequent Phase 4 functions"
  - "updateViewState() is the single entry point after any visibility change — normalize state once"
  - "applyLegendRowStyle() is the shared helper for legend row visual state — do not duplicate in 04-02"

requirements-completed: [PARM-01]

# Metrics
duration: 2min
completed: 2026-02-19
---

# Phase 4 Plan 01: Parameter Management State Machine and View Tabs Summary

**View tab bar with 6 system presets (All/Boiler/HK1/WW1/PU1/PE1) wired to setSeries() for zoom-safe switching, plus full Phase 4 CSS scaffold and legend pointer-events fix**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-19T21:24:42Z
- **Completed:** 2026-02-19T21:26:50Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Fixed `.u-legend { pointer-events: auto !important }` — unblocks legend click events for 04-02
- Added complete Phase 4 CSS: view tabs, custom indicator, Parameters button, all picker-* modal classes with animations
- Implemented full Phase 4 state machine: VIEW_GROUPS, buildViewPresets(), matchPreset(), getVisibleRawNames(), updateViewState(), updateTabHighlight(), setActiveView(), applyLegendRowStyle()
- Built tab bar DOM lifecycle (buildViewTabs / destroyViewTabs) wired to createChart / destroyChart
- "All" tab active on load; absent-group tabs not rendered; clicking active tab is a no-op; zoom fully preserved on tab switch

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix pointer-events CSS and add Phase 4 tab/modal CSS rules** - `d1113e8` (feat)
2. **Task 2: Add Parameters button to toolbar HTML and Phase 4 state machine + tab functions** - `098c6c8` (feat)

**Plan metadata:** `[pending final commit]` (docs: complete plan)

## Files Created/Modified

- `index.html` - pointer-events fix, 191 lines CSS (Task 1) + 222 lines JS + HTML (Task 2)

## Decisions Made

- Used `setSeries(i, {show}, false)` third-arg false during batch tab switch to suppress redundant hook calls; call `updateViewState()` once after the loop
- `buildViewPresets()` queries `dataModel.columns` at runtime so absent groups are naturally excluded (no hardcoded column names)
- AT column appended to system group tabs via name-part regex match on `rawName` — provides ambient temperature context in every system view
- `#params-btn` placed in HTML as `display:none` stub, shown/hidden alongside tab bar — wiring deferred to 04-03 as designed

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 04-02 can immediately use `applyLegendRowStyle()` and `updateViewState()` for legend click toggling
- 04-03 can wire `#params-btn` click to open the picker modal (all CSS classes already present)
- 04-04 `savePrefs()` has a clearly marked insertion point in `updateViewState()`
- All Phase 4 CSS scaffold in place — no style additions needed in subsequent plans

## Self-Check: PASSED

- FOUND: `.planning/phases/04-parameter-management/04-01-SUMMARY.md`
- FOUND: commit `d1113e8` (Task 1 — CSS changes)
- FOUND: commit `098c6c8` (Task 2 — JS state machine + HTML)

---
*Phase: 04-parameter-management*
*Completed: 2026-02-19*
