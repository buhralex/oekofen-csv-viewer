# Phase 4: Parameter Management - Research

**Researched:** 2026-02-19
**Domain:** uPlot v1.6.32 series management APIs, localStorage persistence, vanilla JS modal overlay
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**View tabs:**
- Six tabs total — "All" + five system views: Boiler, Heating Circuit, Hot Water, Buffer, Pellet Unit
- "All" tab = DEFAULT_SERIES (9-column curated set)
- System tabs = all columns in the group's `dataModel.columns` filtered by `.group`, plus AT always appended (deduplicated)
- Group-based resolution (not hardcoded rawNames) so any OekoFEN file works
- Tab placement: inside existing `#toolbar-row`, to the left of the Reset Zoom button
- Tab switching: uses `setSeries()` to show/hide — does NOT recreate the chart; zoom range fully preserved
- Default on file load: "All" tab active
- "Custom" indicator: text label (not a tab) appears in toolbar when active series list does not match any preset
- Click on active tab: no-op
- Empty view guard: if a system tab's group has zero columns in the file, that tab is not rendered

**Series show/hide toggling:**
- Trigger: click on a legend row (`.u-legend tr`) toggles that series
- Implementation: event delegation on `.u-legend` table after chart creation; extract series index from row position; call `u.setSeries(idx, { show: !currentShow })`
- Visual feedback: hidden series legend row gets `opacity: 0.35` and `text-decoration: line-through` on label; restored to normal on re-show; applied via inline style to avoid CSS specificity conflicts
- Zoom preservation: guaranteed — `setSeries()` does not affect x-scale or y-scale
- No minimum visible series enforced
- Minimap behavior: always shows full DEFAULT_SERIES regardless of show/hide state on main chart

**Custom parameter picker:**
- Entry point: "Parameters..." button in toolbar row (right side, after Reset button); ghost/tertiary button style
- UI: modal dialog overlay; title "Add Parameters"; content = all `dataModel.columns` in group sections with collapsible headers and checkboxes; pre-checked = currently visible; binary columns get "binary" badge; column labels = rawName
- Apply: rebuilds active series list from checked columns; calls `setSeries()` per changed column; modal closes
- Cancel: closes without changes
- After Apply: if resulting series matches a preset exactly → that tab becomes active; otherwise → "Custom" indicator
- No minimum selection enforced

**Persistence (localStorage):**
- Key: `oekofen-viewer-prefs` (single JSON object)
- Shape: `{ "activeView": "All", "visibleSeries": ["AT [°C]", ...] }`
- `activeView`: tab name or `"Custom"`
- `visibleSeries`: array of rawNames currently shown
- Persist on: every change — tab switch, series toggle, custom picker Apply
- Restore on: file load, after `createChart()` returns and minimap is wired
- Restore logic: read saved list → verify each rawName exists in `dataModel.columns` → show matching columns → if zero survive → fall back to DEFAULT_SERIES + toast "Saved settings could not be applied — using defaults"

### Claude's Discretion

- Tab overflow on narrow screens: CSS flex-wrap (simple, no horizontal scroll)
- Legend row click target: entire `<tr>` is clickable; `cursor: pointer` on the row
- Modal animation: fade in with 150ms ease-out opacity + scale transition; backdrop: `rgba(0,0,0,0.5)`
- Group section collapse default: all groups expanded by default when picker opens
- Picker "Select All" / "Clear" per group: NOT included

### Deferred Ideas (OUT OF SCOPE)

None raised. All discussion stayed within Phase 4 scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PARM-01 | User can select a pre-built view to show parameters grouped by system (Boiler, Heating Circuit, Hot Water, Buffer, Pellet Unit) | `setSeries(idx, {show: bool})` enables show/hide without chart recreation; `dataModel.columns.filter(c => c.group === g)` resolves group membership; tab DOM goes in existing `#toolbar-row` |
| PARM-02 | User can show/hide individual parameters on the chart via legend clicks, with zoom preserved | `setSeries()` is zoom-safe (does not touch x-scale); legend click requires removing `pointer-events: none !important` from `.u-legend`; series index = tbody row index + 1 (when legend.live:false) |
| PARM-03 | User can select custom parameters beyond the pre-built views | Modal overlay with group-organized checkboxes; no library needed; Apply calls `setSeries()` per changed column |
| PARM-04 | User's visible series and active view are persisted in localStorage across page reloads | `localStorage.setItem('oekofen-viewer-prefs', JSON.stringify(prefs))` + try/catch; restore after `createChart()` returns; validate rawNames against `dataModel.columns` before applying |
</phase_requirements>

---

## Summary

Phase 4 adds parameter management to the existing single-file viewer. The entire implementation is vanilla JS within `index.html` — no new libraries needed. The core workhorse is uPlot's `setSeries(idx, {show: bool})` API, which toggles series visibility without recreating the chart or affecting the x-scale (zoom is fully preserved). This method is verified from the official TypeScript definitions and uPlot source.

The most significant codebase-specific finding: the existing `.u-legend { pointer-events: none !important; }` CSS rule in `index.html` was added in Phase 2/3 to prevent accidental legend interaction. Phase 4 MUST remove or override this rule to enable legend click events. This is the single most likely source of a "legend clicks don't work" bug during implementation.

The legend DOM structure with `legend.live: false` creates a critical index offset: uPlot does NOT create a row for series[0] (x-axis), so tbody row 0 corresponds to `u.series[1]`. The click handler must add 1 to the tbody row index to get the correct `setSeries()` index. The localStorage implementation is straightforward but requires try/catch around both `setItem` (QuotaExceededError) and `JSON.parse` (corruption/invalid JSON).

**Primary recommendation:** Use `setSeries(idx, {show: bool})` for all visibility changes (tabs, legend clicks, picker Apply), with a shared `updateViewState()` function that persists to localStorage and updates the active tab indicator after every change. All four requirements can be addressed in a single implementation pass since they share the same state model.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| uPlot | 1.6.32 (vendored IIFE) | Series visibility via setSeries(), series state via u.series[i].show | Already in use; the only correct API for show/hide without chart recreate |
| localStorage | Web Platform | Persist prefs across page reloads | Already in scope; browser-native, no install |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| None (vanilla JS/CSS) | N/A | Tabs, modal, click handlers | Project is deliberately dependency-free |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| setSeries() for tab switching | Rebuild uPlot with new series | Rebuild destroys zoom, is slower, loses cursor state — setSeries is correct |
| setSeries() for picker Apply | setData() with filtered data | setData resets scales; setSeries preserves x-scale zoom — use setSeries |
| Vanilla modal | dialog element | `<dialog>` has better native accessibility; but this project has no deps and the glass theme needs custom styling anyway — vanilla div is fine |

**Installation:** No new packages. Everything in `index.html`.

---

## Architecture Patterns

### Recommended Code Organization (all in index.html script block)

```
// ─── Phase 4: Parameter Management ────────────────────────────
// State
let _activeView = 'All';                  // current tab name or 'Custom'

// View preset definitions
function buildViewPresets(dataModel)      // returns Map<string, rawName[]>

// Core state machine
function setActiveView(viewName)          // called by tabs, picker Apply, restore
function updateViewState(visibleRawNames) // shared: sets tabs, persists, calls setSeries
function getVisibleRawNames()             // reads current u.series[i].show state

// Tab UI
function buildViewTabs(dataModel)         // creates tab DOM, wires click handlers
function destroyViewTabs()                // cleanup on destroyChart()

// Legend click toggle
function wireLegendClicks(u)              // event delegation on .u-legend
function unwireLegendClicks()            // stores/removes listener ref

// Picker modal
function openPickerModal()                // creates and shows modal
function closePickerModal()               // removes modal from DOM

// Persistence
function savePrefs()                      // localStorage.setItem (try/catch)
function loadPrefs()                      // localStorage.getItem (try/catch)
function applyRestoredPrefs(dataModel)    // called after createChart()
```

### Pattern 1: setSeries() for Series Visibility Toggle

**What:** The uPlot API for toggling a single series visible/hidden without chart recreation.
**When to use:** ALL visibility changes — tab switches, legend clicks, picker Apply.

```javascript
// Source: uPlot dist/uPlot.d.ts (official TypeScript definitions)
// Signature: setSeries(seriesIdx: number | null, opts: {show?: boolean, focus?: boolean}, fireHook?: boolean): void

// Toggle series i visible:
u.setSeries(i, { show: true });

// Toggle series i hidden:
u.setSeries(i, { show: false });

// Read current visibility:
const isShown = u.series[i].show !== false;   // uPlot defaults show to true when not set
```

**Critical:** `seriesIdx` is 0-based into `u.series[]`. Index 0 is always the x-axis placeholder. The first data series is index 1. Never call `setSeries(0, ...)`.

**Side effects of setSeries:**
- Adds/removes the CSS class `u-off` on the corresponding `legendRows[i]` DOM element
- Does NOT trigger a scale change — x-scale (zoom) is fully preserved
- Fires the `setSeries` hook (can be suppressed with `fireHook: false` if needed)
- The uPlot built-in CSS (already in `uPlot.min.css`) applies `.u-legend .u-off > * { opacity: 0.3; }` automatically

### Pattern 2: Legend Click with Correct Index Mapping

**What:** Event delegation on the legend table to intercept row clicks and call setSeries.
**When to use:** PARM-02 — per-series toggle via legend click.

```javascript
// Source: uPlot GitHub issue #422 + uPlot source analysis
// CRITICAL: pointer-events: none !important must be removed from .u-legend first (see Pitfall 1)

function wireLegendClicks(u) {
  const legend = u.root.querySelector('.u-legend');
  if (!legend) return;

  function onLegendClick(e) {
    // Walk up to the .u-series tr row
    const row = e.target.closest('.u-series');
    if (!row) return;

    // tbody is legend.childNodes[0]; its childNodes are the series rows
    const tbody = legend.querySelector('tbody');
    const rowIndex = Array.from(tbody.childNodes).indexOf(row);
    if (rowIndex < 0) return;

    // CRITICAL INDEX OFFSET: with legend.live:false, series[0] (x-axis) has NO legend row.
    // tbody row 0 → u.series[1], tbody row 1 → u.series[2], etc.
    // Therefore: seriesIdx = rowIndex + 1
    const seriesIdx = rowIndex + 1;
    if (seriesIdx >= u.series.length) return;  // safety guard

    const currentShow = u.series[seriesIdx].show !== false;
    u.setSeries(seriesIdx, { show: !currentShow });

    // Apply custom visual feedback (opacity + line-through) via inline style
    // (uPlot adds u-off class with opacity:0.3; we override to 0.35 and add line-through)
    applyLegendRowStyle(row, !currentShow);

    // Persist and update view state
    updateViewState();
  }

  legend.addEventListener('click', onLegendClick);
  legend._phase4ClickHandler = onLegendClick;  // store ref for cleanup
}

function unwireLegendClicks(u) {
  const legend = u.root.querySelector('.u-legend');
  if (legend && legend._phase4ClickHandler) {
    legend.removeEventListener('click', legend._phase4ClickHandler);
    legend._phase4ClickHandler = null;
  }
}

function applyLegendRowStyle(row, isHidden) {
  // Applied via inline style — higher specificity than uPlot's .u-off stylesheet rule
  if (isHidden) {
    row.style.opacity = '0.35';
    const label = row.querySelector('.u-label');
    if (label) label.style.textDecoration = 'line-through';
    row.style.cursor = 'pointer';
  } else {
    row.style.opacity = '';
    const label = row.querySelector('.u-label');
    if (label) label.style.textDecoration = '';
  }
}
```

**Why NOT using `e.target.rowIndex`:** The HTMLTableRowElement.rowIndex property counts rows from the top of the table, but may include thead rows. The `indexOf()` approach against tbody.childNodes is safer.

### Pattern 3: View Preset Computation

**What:** Build the six preset series lists from `dataModel.columns` at runtime, not hardcoded.
**When to use:** On file load, before tab rendering; also to match picker result against presets.

```javascript
// Source: derived from existing classifyColumn() pattern in codebase

const VIEW_GROUPS = {
  'All':             null,    // special: uses DEFAULT_SERIES
  'Boiler':          'Boiler',
  'Heating Circuit': 'Heating Circuit (HK1)',
  'Hot Water':       'Hot Water (WW1)',
  'Buffer':          'Buffer (PU1)',
  'Pellet Unit':     'Pellet Unit (PE1)',
};

function buildViewPresets(dataModel) {
  // Find AT rawName (first column whose namePart starts with 'AT')
  const atColumn = dataModel.columns.find(c => {
    const namePart = c.rawName.match(/^(.+?)\s*(?:\[|$)/)?.[1]?.trim();
    return namePart === 'AT';
  });
  const atRawName = atColumn ? atColumn.rawName : null;

  const presets = new Map();

  // "All" tab: always DEFAULT_SERIES
  presets.set('All', DEFAULT_SERIES.filter(rn =>
    dataModel.columns.some(c => c.rawName === rn)
  ));

  // System tabs: group columns + AT (deduplicated)
  for (const [tabName, groupName] of Object.entries(VIEW_GROUPS)) {
    if (tabName === 'All') continue;
    const groupCols = dataModel.columns
      .filter(c => c.group === groupName)
      .map(c => c.rawName);

    // Empty group = no columns in file for this system → skip tab
    if (groupCols.length === 0) continue;

    // Append AT for context, deduplicated
    const seriesList = [...groupCols];
    if (atRawName && !seriesList.includes(atRawName)) {
      seriesList.push(atRawName);
    }
    presets.set(tabName, seriesList);
  }

  return presets;
}

// Match current visibility to a preset (for "Custom" detection)
function matchPreset(visibleRawNames, presets) {
  const visSet = new Set(visibleRawNames);
  for (const [name, list] of presets.entries()) {
    const listSet = new Set(list);
    if (visSet.size === listSet.size && [...visSet].every(r => listSet.has(r))) {
      return name;
    }
  }
  return 'Custom';
}
```

### Pattern 4: Tab DOM Building

**What:** Build tab buttons inside `#toolbar-row` to the left of the Reset Zoom button.
**When to use:** On file load, after presets are computed.

```javascript
// Source: existing index.html toolbar-row pattern

function buildViewTabs(presets) {
  const toolbar = document.getElementById('toolbar-row');
  const resetBtn = document.getElementById('reset-zoom-btn');

  // Container for tabs (inserted before Reset Zoom button)
  const tabContainer = document.createElement('div');
  tabContainer.id = 'view-tabs';
  tabContainer.style.cssText = 'display:flex; gap:4px; flex-wrap:wrap; align-items:center;';

  for (const [tabName] of presets.entries()) {
    const btn = document.createElement('button');
    btn.className = 'view-tab';
    btn.dataset.view = tabName;
    btn.textContent = tabName;
    tabContainer.appendChild(btn);
  }

  // Custom indicator label (not a tab)
  const customIndicator = document.createElement('span');
  customIndicator.id = 'custom-indicator';
  customIndicator.textContent = 'Custom';
  customIndicator.style.cssText = 'display:none; font-size:11px; color:var(--text-3); padding: 0 6px;';
  tabContainer.appendChild(customIndicator);

  toolbar.insertBefore(tabContainer, resetBtn);

  // Event delegation on the container
  tabContainer.addEventListener('click', (e) => {
    const btn = e.target.closest('.view-tab');
    if (!btn) return;
    const viewName = btn.dataset.view;
    if (viewName === _activeView) return;  // no-op if already active
    setActiveView(viewName);
  });
}

function destroyViewTabs() {
  const el = document.getElementById('view-tabs');
  if (el) el.remove();
}

// CSS for tabs (add to <style> block):
// .view-tab {
//   padding: 2px 10px;
//   background: var(--bg-l2);
//   color: var(--text-2);
//   border: none;
//   border-radius: var(--r-pill);
//   font-size: 11px; font-weight: 500;
//   cursor: pointer;
//   transition: background 0.15s;
// }
// .view-tab.active {
//   background: var(--blue-dim);
//   color: var(--blue);
// }
// .view-tab:hover:not(.active) { background: var(--bg-l3); }
```

### Pattern 5: localStorage Persistence

**What:** Persist and restore the active view and visible series.
**When to use:** After every visibility change; restore after `createChart()` on file load.

```javascript
// Source: MDN Web API documentation — localStorage
const PREFS_KEY = 'oekofen-viewer-prefs';

function savePrefs(activeView, visibleSeries) {
  try {
    localStorage.setItem(PREFS_KEY, JSON.stringify({
      activeView,
      visibleSeries,
    }));
  } catch (e) {
    // QuotaExceededError or SecurityError (e.g., private browsing with storage blocked)
    console.warn('[savePrefs] localStorage write failed:', e);
    // Silently fail — losing persistence is non-critical
  }
}

function loadPrefs() {
  try {
    const raw = localStorage.getItem(PREFS_KEY);
    if (!raw) return null;
    const prefs = JSON.parse(raw);
    // Basic shape validation
    if (!Array.isArray(prefs.visibleSeries)) return null;
    return prefs;
  } catch (e) {
    // JSON.parse error, or localStorage access blocked
    console.warn('[loadPrefs] localStorage read failed:', e);
    return null;
  }
}

function applyRestoredPrefs(dataModel, presets) {
  const prefs = loadPrefs();
  if (!prefs) return;  // no saved prefs — stay with defaults

  // Validate: only keep rawNames that exist in current data model
  const validSeries = prefs.visibleSeries.filter(rn =>
    dataModel.columns.some(c => c.rawName === rn)
  );

  if (validSeries.length === 0) {
    // All saved series are absent in the new file
    showToast('Saved settings could not be applied — using defaults', 'warning');
    return;
  }

  // Apply visibility to chart
  const u = AppState.chart;
  for (let i = 1; i < u.series.length; i++) {
    const rawName = AppState.chartSeries[i]?.label;
    const shouldShow = validSeries.includes(rawName);
    u.setSeries(i, { show: shouldShow });
  }

  // Restore tab state
  const matchedView = matchPreset(validSeries, presets);
  _activeView = matchedView;
  updateTabHighlight(matchedView);
}
```

### Pattern 6: Modal Picker

**What:** Full-screen modal overlay with grouped checkboxes for all columns.
**When to use:** When user clicks "Parameters..." button.

```javascript
// Source: vanilla JS modal pattern — no library needed

function openPickerModal() {
  if (document.getElementById('picker-modal')) return;  // already open

  const backdrop = document.createElement('div');
  backdrop.id = 'picker-modal';
  backdrop.style.cssText = [
    'position:fixed; inset:0; z-index:200;',
    'background:rgba(0,0,0,0.5);',
    'display:flex; align-items:center; justify-content:center;',
    'animation: backdrop-in 150ms ease-out both;',
  ].join('');

  const dialog = document.createElement('div');
  dialog.className = 'picker-dialog';
  // ... build dialog content (group sections + checkboxes) ...

  // Close on backdrop click
  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) closePickerModal();
  });

  // Close on Escape
  const onKeyDown = (e) => {
    if (e.key === 'Escape') { closePickerModal(); document.removeEventListener('keydown', onKeyDown); }
  };
  document.addEventListener('keydown', onKeyDown);

  backdrop.appendChild(dialog);
  document.body.appendChild(backdrop);
}

function closePickerModal() {
  const modal = document.getElementById('picker-modal');
  if (modal) modal.remove();
}
```

**Modal CSS (add to `<style>` block):**
```css
@keyframes backdrop-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

@keyframes dialog-in {
  from { opacity: 0; transform: scale(0.95); }
  to   { opacity: 1; transform: scale(1); }
}

.picker-dialog {
  background: var(--bg-l1);
  border: 0.5px solid var(--sep-strong);
  border-radius: var(--r-xl);
  width: 480px;
  max-width: calc(100vw - 32px);
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: dialog-in 150ms ease-out both;
  box-shadow: 0 24px 64px rgba(0,0,0,0.6);
}

.picker-header {
  padding: 16px 20px 12px;
  border-bottom: 0.5px solid var(--sep);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-1);
}

.picker-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 20px;
}

.picker-group-header {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-3);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 10px 0 6px;
  cursor: pointer;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 6px;
}

.picker-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
  cursor: pointer;
}

.picker-row label {
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--text-2);
  cursor: pointer;
  flex: 1;
}

.picker-badge-binary {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: rgba(255,159,10,0.8);
  background: rgba(255,159,10,0.12);
  border-radius: 3px;
  padding: 1px 4px;
}

.picker-footer {
  padding: 12px 20px;
  border-top: 0.5px solid var(--sep);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
```

### Anti-Patterns to Avoid

- **Rebuilding the uPlot instance for tab switches:** `setSeries()` is specifically designed for this. Rebuilding destroys zoom state, cursor state, and is 10-100x slower.
- **Using `setData()` to filter series:** `setData()` is for replacing the underlying data arrays (different rows), not for show/hide. It resets scales.
- **Calling `setSeries(0, ...)` on the x-axis:** Series[0] is the x-axis placeholder. Toggling it is undefined behavior.
- **Event listener accumulation:** Each `createChart()` call sets up new DOM elements. Tabs and modal click handlers must be torn down in `destroyChart()`.
- **Attaching click handlers to legend without removing `pointer-events: none !important`:** The existing CSS blocks all pointer events on the legend. Phase 4 MUST change this rule.
- **Using `localStorage` without try/catch:** In some browsers or configurations (Safari private mode, storage quota exceeded), localStorage throws. Always wrap.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Show/hide a chart series | Custom canvas redraw or chart recreate | `u.setSeries(idx, {show: bool})` | setSeries is atomic, zoom-safe, legend-synced via u-off class |
| Series visibility persistence | Complex state machine | localStorage with simple JSON object | One key, one write on every change, validated on restore |
| Picker "is checked?" state | Maintaining a separate checked Set | Read current `u.series[i].show` at modal open time | The chart is the source of truth for current visibility |
| Tab "which preset matches?" | Manual loop after every change | `matchPreset(visibleRawNames, presets)` comparing two Sets | Centralizes the comparison logic to one function |
| Column grouping | Re-parse column headers | `dataModel.columns.filter(c => c.group === groupName)` | `classifyColumn()` already ran at parse time |

**Key insight:** `AppState.chart.series[i].show` is always the truth about what's visible. The picker, tabs, and persistence are all facades over this state. Read from `u.series[i].show` for current state; write via `u.setSeries(i, ...)`.

---

## Common Pitfalls

### Pitfall 1: `pointer-events: none !important` on `.u-legend` Blocks All Legend Clicks

**What goes wrong:** Legend row clicks silently do nothing. No error. `addEventListener('click', ...)` on the legend fires, but `e.target` is the chart's `.u-over` element because events pass through the legend entirely.
**Why it happens:** Phase 2/3 added `pointer-events: none !important` to `.u-legend` in the CSS to prevent accidental hover/focus interference with the cursor crosshair system. This was correct for Phase 2/3 but directly conflicts with Phase 4's requirement.
**How to avoid:** Change `.u-legend { pointer-events: none !important; }` to `pointer-events: auto !important;`. The cursor tooltip system reads `u.series[i].show` to filter series — it does not depend on the legend being non-interactive.
**Warning signs:** Click listeners attached to `.u-legend` never fire; `console.log` in the click handler never appears; event inspection shows target is `.u-over` not a legend element.

### Pitfall 2: Wrong Series Index in Legend Click Handler (Off-by-One)

**What goes wrong:** The wrong series is toggled — off by one series. Clicking the first series row hides the second series (or throws an error).
**Why it happens:** With `legend: { show: true, live: false }`, uPlot does NOT create a legend row for series[0] (the x-axis placeholder). This is confirmed in the uPlot source: `initLegendRow` returns `nullNullTuple` when `i == 0 && !legend.live`. The tbody's first `<tr>` is for series[1]. So `indexOf(clickedRow)` in tbody returns 0, but the correct `setSeries()` index is 1.
**How to avoid:** Always add 1 to the tbody row index: `const seriesIdx = rowIndex + 1;`. Add a bounds check: `if (seriesIdx >= u.series.length) return;`.
**Warning signs:** Wrong series highlighted/hidden when clicking a legend row; series appear to shift by one.

### Pitfall 3: setSeries Hook Fires Unexpectedly During Tab Switch

**What goes wrong:** If a `setSeries` hook was registered (e.g., for analytics or syncing), it fires for every series in the tab switch loop — potentially causing performance issues or re-entrant state updates.
**Why it happens:** `setSeries()` fires the hook by default. Tab switching calls `setSeries()` once per series in the chart — up to 9 times for DEFAULT_SERIES, potentially 20+ times for a full system tab.
**How to avoid:** Batch the persistence and view-state update ONCE after the full loop, not inside a setSeries hook. Alternatively, use `setSeries(idx, opts, false)` (third arg `false` suppresses the hook) during bulk operations and manually update state after the loop.
**Warning signs:** `updateViewState()` called 9 times per tab click; performance noticeable lag on tab switch.

### Pitfall 4: `AppState.chartSeries` Index vs `u.series` Index

**What goes wrong:** Mapping rawName → series index via `AppState.chartSeries` produces wrong index if the arrays are not exactly parallel.
**Why it happens:** `AppState.chartSeries` is set to the `series` array returned by `buildChartData()`. This array starts with the x-axis placeholder at index 0, exactly matching `u.series[]`. So `AppState.chartSeries[i].label` matches `u.series[i].label`. But `buildChartData()` may skip rawNames not found in `dataModel.columns` (with a console.warn). If a rawName in DEFAULT_SERIES doesn't exist in the file, the series array is shorter.
**How to avoid:** Always use `AppState.chartSeries` to map rawName → index (not a separate lookup array). Iterate `u.series` (not DEFAULT_SERIES) when reading current state. Use `u.series[i].label === rawName` for mapping.
**Warning signs:** setSeries called with wrong index; unexpected series hidden/shown.

### Pitfall 5: `localStorage` Access Throws in Private Mode / Storage Full

**What goes wrong:** `localStorage.setItem()` or `localStorage.getItem()` throws a `DOMException`. The uncaught exception prevents the rest of the file load from completing.
**Why it happens:** Safari private browsing disables localStorage entirely; some browsers throw `QuotaExceededError` when storage is full; `JSON.parse(null)` throws if key is missing (though `localStorage.getItem` returns `null` for missing keys, not an error).
**How to avoid:** Wrap every `localStorage` call in try/catch. Treat storage failures as silent — the feature degrades gracefully (persistence is a convenience, not required for the chart to work).
**Warning signs:** File loads fail silently in private/incognito mode; users report "app doesn't work in private browsing".

### Pitfall 6: Picker Pre-Check State Reads Stale Data

**What goes wrong:** The picker opens with wrong checkboxes — showing a series as checked that was hidden, or vice versa.
**Why it happens:** If picker pre-check state is computed from a snapshot taken at picker construction time but the chart state changed between opens, the snapshot is stale.
**How to avoid:** Always read `u.series[i].show !== false` at the moment the picker opens (inside `openPickerModal()`), not from cached state. The chart instance is the truth.
**Warning signs:** Picker checkboxes don't reflect current chart visibility; re-opening picker shows stale state.

### Pitfall 7: Event Listeners Accumulate Across File Reloads

**What goes wrong:** After loading a second file, legend clicks toggle series in the old (destroyed) chart, or multiple Apply handlers fire.
**Why it happens:** `destroyChart()` destroys the uPlot instance but does not remove Phase 4 event listeners added to non-uPlot DOM (tabs, "Parameters..." button), or legend listeners stored on the now-destroyed legend element.
**How to avoid:** In `destroyChart()`, call `destroyViewTabs()`, `unwireLegendClicks()`, and `closePickerModal()`. Store handler references so they can be removed with `removeEventListener`. The Reset Zoom button already uses the `_resetBtn._resetHandler` pattern — follow the same pattern for Phase 4.
**Warning signs:** Double-firing on legend click after second file load; console shows multiple log messages per click.

### Pitfall 8: Restore Applies Before Minimap is Wired

**What goes wrong:** Restored series visibility is ignored, or the minimap shows incorrect state.
**Why it happens:** If `applyRestoredPrefs()` is called before `createMinimap()` returns and `AppState.minimap` is set, the minimap hasn't been initialized yet.
**How to avoid:** Call `applyRestoredPrefs()` after all of `createChart()` completes, including the minimap wiring at the end of `createChart()`. The CONTEXT.md specifies this: "Restore on: File load (after chart is created and minimap is wired)."
**Warning signs:** Restored series state is correct but minimap doesn't show the right highlight; or restore silently fails.

---

## Code Examples

Verified patterns from official sources:

### 1. setSeries for Show/Hide (official TypeScript definition)
```javascript
// Source: uPlot dist/uPlot.d.ts (verified)
// Toggle series i hidden:
AppState.chart.setSeries(i, { show: false });
// Toggle series i visible:
AppState.chart.setSeries(i, { show: true });
// Read current state:
const isVisible = AppState.chart.series[i].show !== false;
```

### 2. Legend Click Index Mapping (verified from uPlot source + issue #422)
```javascript
// Source: uPlot src/uPlot.js + GitHub issue #422
// IMPORTANT: legend.live:false means series[0] has no row.
// tbody row index 0 → u.series[1], row index N → u.series[N+1]

const legend = u.root.querySelector('.u-legend');
const tbody = legend.querySelector('tbody');

legend.addEventListener('click', function(e) {
  const row = e.target.closest('.u-series');
  if (!row) return;
  const rowIndex = Array.from(tbody.childNodes).indexOf(row);
  if (rowIndex < 0) return;
  const seriesIdx = rowIndex + 1;  // +1 offset because series[0] has no row
  if (seriesIdx >= u.series.length) return;
  u.setSeries(seriesIdx, { show: u.series[seriesIdx].show === false });
});
```

### 3. u-off CSS Class Behavior (verified from uPlot src/domClasses.js + uPlot.min.css)
```css
/* From uPlot.min.css (already in project) — applied when setSeries(i, {show:false}) */
.u-legend .u-off > * { opacity: 0.3; }

/* Phase 4 override in index.html <style> — applies our custom styling instead */
/* Note: u-off is on the <tr>; children are <th> and <td> */
/* We use inline styles on the row (not CSS class) to avoid specificity wars */
```

### 4. localStorage with Full Error Handling (MDN standard pattern)
```javascript
// Source: MDN Web API localStorage documentation
const PREFS_KEY = 'oekofen-viewer-prefs';

function savePrefs(prefs) {
  try {
    localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
  } catch (e) {
    // QuotaExceededError or SecurityError — degrade silently
    console.warn('[savePrefs] failed:', e.name);
  }
}

function loadPrefs() {
  try {
    const raw = localStorage.getItem(PREFS_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (typeof parsed !== 'object' || !Array.isArray(parsed.visibleSeries)) return null;
    return parsed;
  } catch (e) {
    console.warn('[loadPrefs] failed:', e.name);
    return null;
  }
}
```

### 5. AppState.chartSeries for rawName → Index Mapping (from existing codebase)
```javascript
// Source: existing index.html — AppState.chartSeries set in createChart()
// AppState.chartSeries[i].label === u.series[i].label (parallel arrays)
// series[0] is x-axis placeholder ({}) — label is undefined
// series[1..N] are data series — label is rawName

function rawNameToSeriesIdx(rawName) {
  return AppState.chartSeries.findIndex((s, i) => i > 0 && s.label === rawName);
  // returns -1 if not found
}

// Usage:
const idx = rawNameToSeriesIdx('AT [°C]');   // returns 1 for the first series
if (idx >= 1) AppState.chart.setSeries(idx, { show: true });
```

### 6. Get Current Visible Series as rawName Array (derived from existing pattern)
```javascript
// Source: derived from existing codebase series[] structure
function getVisibleRawNames() {
  const u = AppState.chart;
  if (!u) return [];
  const visible = [];
  for (let i = 1; i < u.series.length; i++) {
    if (u.series[i].show !== false) {
      visible.push(u.series[i].label);  // label === rawName
    }
  }
  return visible;
}
```

### 7. Full updateViewState() Orchestrator
```javascript
// Source: derived from CONTEXT.md decisions — centralized state update
function updateViewState() {
  // 1. Read current visibility
  const visibleRawNames = getVisibleRawNames();

  // 2. Match to preset (or 'Custom')
  const matchedView = matchPreset(visibleRawNames, _viewPresets);
  _activeView = matchedView;

  // 3. Update tab highlight
  updateTabHighlight(matchedView);

  // 4. Persist
  savePrefs({ activeView: matchedView, visibleSeries: visibleRawNames });
}

function updateTabHighlight(viewName) {
  document.querySelectorAll('.view-tab').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.view === viewName);
  });
  const indicator = document.getElementById('custom-indicator');
  if (indicator) indicator.style.display = (viewName === 'Custom') ? '' : 'none';
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Rebuild uPlot for series changes | `setSeries(idx, {show})` | uPlot v1.x | No chart recreate; zoom preserved; 10-100x faster |
| Cookie-based persistence | localStorage | Modern web (2012+) | Simpler API, larger quota (~5MB), synchronous access |
| Separate "legend toggle" plugin | uPlot's built-in `u-off` class via `setSeries` | uPlot v1.x | toggleDOM() is internal; `setSeries` does everything |

**Deprecated/outdated:**
- Setting `show: false` at series init time (uPlot issue #59): Was buggy in early versions. Fixed and reliable in v1.6.32.
- `legend.onclick` callback in opts: Not a real uPlot API. Use event delegation on `.u-legend`.

---

## Open Questions

1. **Does `setSeries()` with `fireHook: false` (third arg) suppress the visual toggle too, or only the hook?**
   - What we know: The TypeScript definition shows `fireHook?: boolean` as the third argument. The uPlot source shows that `setSeries` calls `toggleDOM(si)` before firing the hook. `toggleDOM` applies/removes the `u-off` class.
   - What's unclear: Whether `fireHook: false` skips `toggleDOM()` as well (unlikely — the DOM update is not "a hook") or only skips firing the `setSeries` hook.
   - Recommendation: Assume `fireHook: false` only suppresses the hook event, not the visual DOM update. This is consistent with how `setSelect(opts, false)` works (suppresses hook, still updates DOM). Test in browser if batched setSeries calls produce visual glitches.

2. **Does `setSeries()` trigger a full canvas redraw each call?**
   - What we know: The uPlot source calls `commit()` after `setSeries()`, which triggers a redraw.
   - What's unclear: Whether 9 consecutive `setSeries()` calls (one per series on a tab switch) causes 9 redraws or whether uPlot batches them.
   - Recommendation: Wrap tab-switch setSeries loop in `u.batch(fn)`. This is the standard uPlot pattern for multiple state changes. If `batch` is not available in the vendored IIFE, the visual impact of 9 redraws is acceptable (~15-20ms total for 9 series).

3. **Can `AppState.chart.series[i].label` be undefined for series[0]?**
   - What we know: The x-axis series is created as `{}` (empty object) in `buildChartData()`. In uPlot, `series[0].label` is undefined or an empty string.
   - What's unclear: Whether `rawNameToSeriesIdx` using `findIndex((s, i) => i > 0 && s.label === rawName)` correctly skips series[0] in all cases.
   - Recommendation: Guard with `i > 0` in the findIndex predicate (already shown in example). The `i > 0` condition is sufficient.

---

## Sources

### Primary (HIGH confidence)
- [uPlot dist/uPlot.d.ts](https://raw.githubusercontent.com/leeoniya/uPlot/master/dist/uPlot.d.ts) — `setSeries()` full signature confirmed: `setSeries(seriesIdx: number | null, opts: {show?: boolean, focus?: boolean}, fireHook?: boolean): void`
- [uPlot src/uPlot.js](https://raw.githubusercontent.com/leeoniya/uPlot/master/src/uPlot.js) — Legend DOM structure verified: table > tbody > tr.u-series; series[0] skipped with `legend.live:false`; `toggleDOM()` applies `u-off` class; `legendRows` array is parallel to `series[]`
- [uPlot src/domClasses.js](https://raw.githubusercontent.com/leeoniya/uPlot/master/src/domClasses.js) — `OFF = "u-off"`, `LEGEND_SERIES = "u-series"`, `LEGEND_LABEL = "u-label"`, `LEGEND_MARKER = "u-marker"` confirmed
- [uPlot.min.css (vendored)](C:/Users/buhra/source/repos/oekofen_csv_viewer/OekoFEN_CSV_Viewer/uPlot.min.css) — `.u-legend .u-off > * { opacity: 0.3; }` confirmed; `.u-series th { cursor: pointer; }` confirmed
- [index.html (existing codebase)](C:/Users/buhra/source/repos/oekofen_csv_viewer/OekoFEN_CSV_Viewer/index.html) — `.u-legend { pointer-events: none !important; }` confirmed at line 439; `AppState.chartSeries` set in `createChart()`; `buildChartData()` structure; `destroyChart()` cleanup points; `showToast()` exists for fallback toast

### Secondary (MEDIUM confidence)
- [GitHub issue #422](https://github.com/leeoniya/uPlot/issues/422) — Legend click series index mapping: `closest('.u-series')` + `legend.childNodes[0].childNodes.indexOf(row)` pattern; confirmed legend DOM structure uses tbody
- [GitHub issue #988](https://github.com/leeoniya/uPlot/issues/988) — `setSeries` hook fires for both visibility toggle AND hover focus; `opts.show != null` vs `opts.focus != null` to distinguish
- [GitHub issue #59](https://github.com/leeoniya/uPlot/issues/59) — `series[i].show: false` at init time confirmed working (was buggy, fixed); safe to use in v1.6.32

### Tertiary (LOW confidence)
- WebSearch: localStorage try/catch patterns — cross-verified against MDN documentation; standard practice
- WebSearch: vanilla modal animation patterns — `opacity + scale` at 150ms ease-out is a widely used pattern; specific implementation is project-custom

---

## Metadata

**Confidence breakdown:**
- setSeries API: HIGH — TypeScript definitions + source code verified
- Legend DOM structure and index offset: HIGH — verified from uPlot source (initLegendRow) and issue #422
- pointer-events CSS conflict: HIGH — found directly in existing index.html at line 439
- localStorage: HIGH — Web Platform standard API, MDN-verified patterns
- Modal/tab UI patterns: HIGH — vanilla JS, no external dependencies, project-specific styling
- u-off class behavior: HIGH — verified from domClasses.js and uPlot.min.css

**Research date:** 2026-02-19
**Valid until:** 2026-06-01 (uPlot 1.6.32 is vendored/frozen — no staleness risk; localStorage is stable)
