---
phase: 04-parameter-management
plan: 04
subsystem: ui
tags: [uplot, localstorage, persistence, legend, tooltip, picker]

requires:
  - phase: 04-parameter-management-03
    provides: openPickerModal()/closePickerModal(), parameter picker modal with group sections and Apply/Cancel

provides:
  - localStorage persistence: savePrefs()/loadPrefs()/applyRestoredPrefs()
  - Picker can show/hide any of the 64+ CSV columns (not just DEFAULT_SERIES 9)
  - Chart built with all dataModel columns; DEFAULT_SERIES visible, rest hidden
  - Legend rows: faded/unchecked when hidden within view; display:none when out-of-view
  - Tooltip bottom-clamped to stay inside chart area above minimap
affects: []

tech-stack:
  added: []
  patterns:
    - in-view vs out-of-view legend row distinction (faded vs display:none)
    - localStorage prefs with validation on restore (rawName vs dataModel.columns)
    - all-columns chart build with DEFAULT_SERIES as initial visible set

key-files:
  created: []
  modified:
    - index.html

key-decisions:
  - "Chart built with ALL dataModel columns (not just DEFAULT_SERIES) — picker can show/hide any parameter"
  - "DEFAULT_SERIES placed first in series order; non-DEFAULT follow with show:false"
  - "Legend row hidden states: faded (in-view but unchecked) vs display:none (out-of-view) — distinct semantics"
  - "applyLegendRowStyle uses faded only; setActiveView and applyRestoredPrefs apply display:none for out-of-view directly"
  - "applyRestoredPrefs computes matchedView before legend sync loop so viewSet is available for in/out distinction"
  - "Tooltip vertical clamp: Math.min(top-20, chartH-tooltipH) prevents overflow onto minimap"
  - "DEFAULT_SERIES names corrected from Phase 2 placeholders to real CSV column names (e.g. KT Ist [°C] not KT Ist[°C])"
  - "Legend click handler uses capture phase (true) + e.stopPropagation() to prevent uPlot double-toggle"

patterns-established:
  - "viewSet pattern: named presets use preset list as viewSet; Custom uses visible series as viewSet"
  - "Legend two-state hide: applyLegendRowStyle for in-view faded, direct display:none for out-of-view"

requirements-completed:
  - PARM-04

duration: ~90min (multi-session including verification and bug fixes)
completed: 2026-02-21
---

# Phase 04-04: localStorage Persistence Summary

**Full parameter persistence across reloads with all-columns chart build, two-state legend hiding, and tooltip overflow fix**

## Performance

- **Duration:** ~90 min (multi-session: Task 1 committed 2026-02-19, verification + bug fixes 2026-02-21)
- **Tasks:** 2 (Task 1: implementation; Task 2: human verification checkpoint)
- **Files modified:** 1

## Accomplishments

- `savePrefs()` / `loadPrefs()` / `applyRestoredPrefs()` implement full round-trip persistence: tab state and visible series survive page reload and CSV re-load, with rawName validation against new file columns
- Chart now built with all 64+ dataModel columns (DEFAULT_SERIES first and visible; rest hidden) — picker can show/hide any parameter without recreating the chart
- System tabs (Boiler, Heating Circuit, etc.) now show ALL columns in their group, not just the DEFAULT_SERIES overlap
- Two-state legend hiding: faded (opacity 0.35) for in-view hidden rows — still clickable to restore; `display:none` for out-of-view rows — clean legend per tab
- Tooltip bottom-clamped: no longer overlaps the minimap when cursor is near bottom of chart

## Task Commits

1. **Task 1: Implement savePrefs/loadPrefs/applyRestoredPrefs** — `47c1761` (feat)
2. **Checkpoint pause** — `fe3b7d4` (wip — 2 bugs found during 29-check verification)
3. **Bug fix: DEFAULT_SERIES names + legend double-toggle** — `0e63f0f` (fix)
4. **Bug fix: tooltip bottom clamp + picker add-parameter** — `3ef73ab` (fix)
5. **Bug fix: legend faded vs display:none distinction** — `4188e87` (fix)

## Files Created/Modified

- `index.html` — savePrefs/loadPrefs/applyRestoredPrefs, all-columns chart build, two-state legend row styling, tooltip clamp

## Decisions Made

**DEFAULT_SERIES names corrected:** Phase 2 used placeholder column names (e.g. `KT Ist[°C]`, `HK1 RL Ist[°C]`) before the real CSV was inspected. Fixed against `touch_20260216.csv`: space before `[`, RT not RL, TPO/TPM not oben/unten, PE1 KT/PE1 FRT not PE1 Kessel/PE1 HK.

**All-columns chart build:** `buildChartData` was called with only DEFAULT_SERIES (9 series), making the picker unable to add non-DEFAULT columns. Changed to pass all dataModel columns; DEFAULT_SERIES set via `show:false` for non-DEFAULT series. DEFAULT_SERIES placed first in allRawNames so they render first in the legend.

**Two-state legend hiding:** `applyLegendRowStyle` (called by legend click and picker Apply) uses faded — rows stay in the legend and are re-clickable. Tab switches and restore use `display:none` directly for out-of-view series — legend shows only the current tab's series. `applyRestoredPrefs` computes `matchedView` before the legend loop so the `viewSet` is available to distinguish in-view (shown/faded) from out-of-view (hidden).

**Tooltip bottom clamp:** `top - 20` was unclamped at the bottom; replaced with `Math.min(top-20, chartH-tooltipH)` to prevent overflow onto the minimap.

**Legend click double-toggle fix:** uPlot registers a built-in `<th>` click handler; our delegation handler fired in addition, causing double-toggle with no net change. Fixed: register in capture phase with `e.stopPropagation()`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] DEFAULT_SERIES names didn't match actual CSV columns**
- **Found during:** Task 2 (29-check verification, Check 6)
- **Issue:** 6 of 9 DEFAULT_SERIES rawNames were Phase 2 placeholders; only 3 matched the real file
- **Fix:** Corrected all 6 names verified against `touch_20260216.csv`; updated SERIES_COLOR_OVERRIDES keys
- **Committed in:** `0e63f0f`

**2. [Rule 1 - Bug] Legend clicks double-toggled (no visible change)**
- **Found during:** Task 2 (29-check verification, Checks 7–10)
- **Issue:** uPlot's built-in `<th>` handler + our delegation handler both fired → double-toggle → no net change
- **Fix:** Capture phase + `e.stopPropagation()` in `onLegendClick`; `removeEventListener` updated to also pass `true`
- **Committed in:** `0e63f0f`

**3. [Rule 1 - Bug] Picker could only remove series, not add**
- **Found during:** Post-approval verification
- **Issue:** Chart built with DEFAULT_SERIES only; non-DEFAULT columns returned `findIndex = -1` in picker Apply
- **Fix:** Build chart with all dataModel columns; non-DEFAULT initialized with `show:false`
- **Committed in:** `3ef73ab`

**4. [Rule 1 - Bug] Tooltip hidden by minimap when cursor near bottom**
- **Found during:** Post-approval verification
- **Issue:** Vertical position unclamped at bottom; tooltip overflowed `u.over` onto minimap
- **Fix:** `Math.min(Math.max(0, top-20), Math.max(0, chartH-ttH))`
- **Committed in:** `3ef73ab`

**5. [Rule 1 - Bug] Legend click removed rows instead of unchecking them**
- **Found during:** Post-approval verification
- **Issue:** `applyLegendRowStyle` used `display:none` — rows disappeared; couldn't restore via legend
- **Fix:** Reverted to faded for `applyLegendRowStyle`; `setActiveView` and `applyRestoredPrefs` use `display:none` directly for out-of-view rows only
- **Committed in:** `4188e87`

---

**Total deviations:** 5 auto-fixed (all Rule 1 — bugs found during verification)
**Impact on plan:** All fixes necessary for correctness. No scope creep.

## Issues Encountered

None beyond the 5 bugs documented above.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

Phase 4 is complete. All four PARM requirements (PARM-01 through PARM-04) are delivered and verified. The viewer is feature-complete against all active requirements.

---
*Phase: 04-parameter-management*
*Completed: 2026-02-21*
