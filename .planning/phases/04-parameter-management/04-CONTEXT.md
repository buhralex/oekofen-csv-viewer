# Phase 4: Parameter Management - Context

**Gathered:** 2026-02-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Add parameter management to the Phase 3 viewer: pre-built system views (tabs), per-series show/hide toggling via the legend, a full column picker for custom selection, and localStorage persistence. Does NOT include multi-day comparison, data export, advanced filtering, or any server-side features.

</domain>

<decisions>
## Implementation Decisions

### View tabs

**Tab set:** Six tabs total — "All" + five system views:
- **All**: DEFAULT_SERIES (the curated 9-column set used today — AT, KT, HK1 VL/RL, PU1 top/bottom, PE1 Kessel/HK, BR)
- **Boiler**: all columns in the `Boiler` group + AT (outside air for context)
- **Heating Circuit**: all columns in the `Heating Circuit (HK1)` group + AT
- **Hot Water**: all columns in the `Hot Water (WW1)` group + AT
- **Buffer**: all columns in the `Buffer (PU1)` group + AT
- **Pellet Unit**: all columns in the `Pellet Unit (PE1)` group + AT

Group-based resolution (not hardcoded rawNames) so any OekoFEN file works. AT is always appended as context. Deduplication: if AT is already in the group, it appears once.

**Tab placement:** In the existing toolbar row (`.toolbar-row`) already created by Phase 3, to the left of the Reset Zoom button. The Phase 3 plan already reserved space here — no DOM restructuring needed.

**Tab switching:** Uses `setSeries()` to show/hide — does NOT recreate the chart. Zoom range is fully preserved when switching tabs. The chart is only rebuilt on file load.

Implementation: compute the target series list for the new tab, then for each series in the current chart call `u.setSeries(idx, { show: targetList.includes(rawName) })`.

**Default on file load:** "All" tab active.

**Active tab when switching to "Custom":** No tab is highlighted. A subtle "Custom" text indicator appears in the toolbar (not a tab itself — just an indicator label) when the active series list does not match any preset.

**Switching tab when already active:** No-op (click on active tab does nothing).

**Empty view guard:** If a system tab's group has zero columns in the file (e.g., no WW1 columns), the tab is not rendered — do not show tabs for groups absent from the data.

### Series show/hide toggling

**Trigger:** Click on a legend row (`.u-legend tr`) toggles that series. No double-click needed.

**Implementation:** Event delegation on the `.u-legend` table after chart creation. Extract series index from the clicked row's position among sibling `<tr>` elements. Call `u.setSeries(idx, { show: !currentShow })`.

**Visual feedback:** Hidden series legend row gets `opacity: 0.35` and `text-decoration: line-through` on the label text. Restored to normal on re-show. This is applied via inline style to avoid CSS specificity conflicts with the existing legend styling.

**Zoom preservation:** Guaranteed — `setSeries()` does not affect the x-scale or y-scale.

**Minimum visible series:** No minimum enforced. User can hide all series if they want.

**Minimap behavior:** Minimap always shows the full DEFAULT_SERIES regardless of show/hide state on the main chart. The minimap is a fixed overview reference — it reflects what data exists, not what's currently highlighted. This matches the Phase 3 decision that the minimap always shows full DEFAULT_SERIES.

### Custom parameter picker

**Entry point:** A "Parameters..." button in the toolbar row (right side, after the Reset button). Uses the same pill button style as Reset.

**UI:** A modal dialog overlay.
- Title: "Add Parameters"
- Content: all `dataModel.columns` organized into group sections (Boiler, Heating Circuit, Hot Water, Buffer, Pellet Unit), each with collapsible header and checkboxes per column
- Columns already visible in the current chart are pre-checked
- Binary columns (type: 'discrete') are marked with a small "binary" badge for visual distinction
- Column labels show the rawName (original German with units), same as the chart legend

**Apply behavior:** "Apply" button at the bottom rebuilds the active series list from the checked columns and calls setSeries() to show/hide accordingly. If only a few columns changed, setSeries is called per changed column (no full chart recreate). The modal closes after Apply.

**Cancel behavior:** Closes modal without any changes.

**After Apply — active view state:** If the resulting series list matches a preset exactly → that tab becomes active. Otherwise → no tab is highlighted and the "Custom" indicator appears. This way Apply can naturally select a preset.

**Minimum selection:** No minimum enforced in the picker. If all boxes are unchecked and user clicks Apply → all series hidden (chart shows empty — user can reopen picker to recover).

### Persistence (localStorage)

**Key:** `oekofen-viewer-prefs` (single JSON object)

**Stored shape:**
```json
{
  "activeView": "All",
  "visibleSeries": ["AT [°C]", "KT Ist[°C]", ...]
}
```

`activeView` is the tab name string ("All", "Boiler", etc.) or `"Custom"` when no preset matches.

`visibleSeries` is the array of rawNames that are currently shown (shown=true, others hidden). This is the source of truth for restore.

**Persist on:** Every change — tab switch, series toggle, custom picker Apply.

**Restore on:** File load (after chart is created and minimap is wired). Restore happens after `createChart()` returns.

**Restore logic:**
1. Read `visibleSeries` from localStorage
2. For each rawName in the saved list: verify it exists in `dataModel.columns`
3. Show only columns that exist in both the saved list and the data model
4. If zero columns survive validation → fall back to DEFAULT_SERIES silently (show a toast: "Saved settings could not be applied — using defaults")
5. Restore `activeView` label: if the restored series match a preset → set that tab active; otherwise set "Custom"

**No migration needed:** Single localStorage key, simple overwrite on every change.

### Claude's Discretion

- **Tab overflow on narrow screens:** If tabs don't fit in the toolbar row, they wrap to a second line. No horizontal scroll tab bar — simple CSS flex-wrap is correct.
- **Legend row click target size:** The entire `<tr>` is clickable (not just the label cell). `cursor: pointer` on the row.
- **Modal animation:** Fade in with a 150ms ease-out opacity + scale transition matching the Apple-style theme. Backdrop: `rgba(0,0,0,0.5)`.
- **Group section collapse default:** All groups expanded by default when the picker opens (no collapsed state on first open; collapsed state not persisted).
- **Picker "Select All" / "Clear" per group:** Not included — out of scope. Users pick individually.

</decisions>

<specifics>
## Specific Implementation Notes

- `setSeries(idx, {show: bool})` is the Phase 4 workhorse — understand it before planning. It does NOT accept rawName; it requires a 0-based index into `u.series[]` (which starts with the x-axis series at index 0, so the first data series is index 1).
- The existing `AppState.chartSeries` (set in buildChartData's return) contains the series definitions in order — use this to map rawName → series index.
- The `classifyColumn()` function already assigns groups at parse time. Phase 4 can use `dataModel.columns` directly filtered by `.group` property.
- Minimap stays on DEFAULT_SERIES — do not update minimap on tab switch or series toggle.
- The "Parameters..." button should be a tertiary/ghost button style (not the same prominence as a preset tab) to signal it's an advanced action.

</specifics>

<deferred>
## Deferred Ideas

None raised. All discussion stayed within Phase 4 scope.

</deferred>

---

*Phase: 04-parameter-management*
*Context gathered: 2026-02-19*
