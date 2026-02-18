# Phase 3: Navigation and Interaction - Research

**Researched:** 2026-02-18
**Domain:** uPlot v1.6.32 interaction APIs — drag zoom, scroll zoom, cursor/tooltip, minimap, reset
**Confidence:** HIGH (TypeScript definitions verified, official demos reviewed, GitHub issue patterns confirmed)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Zoom behavior:**
- Drag direction: any direction selects a time range and zooms in — the range is determined by the min/max of the drag endpoints regardless of direction (left-to-right or right-to-left both work)
- After-drag behavior: instant snap (uPlot's native setScale is synchronous and instant)
- Scroll-wheel zoom centering: cursor-centered

**Cursor tooltip:**
- Shows values for ALL currently visible series
- Tooltip header: HH:MM time at cursor position
- Value format: raw value from CSV (variable precision — no forced rounding)

**Reset & navigation controls:**
- Reset method: BOTH a visible button AND double-click on the chart
- Button placement: new toolbar row below header bar, above chart (Phase 4 adds view tabs here)
- Button visibility: hidden at full day view, appears when zoomed

**Minimap:**
- Height approximately 60-80px below main chart
- Simplified series rendering, zoom region highlighted, draggable to pan

### Claude's Discretion

- Scroll zoom centering: cursor-centered, event.preventDefault() for page guard
- Zoom limits: minimum ~5 minutes visible (5 data points at 1-min interval), maximum full 24h day
- Tooltip placement: snapping panel that flips left/right to stay inside chart boundary
- Minimap: secondary uPlot instance or canvas-based brush widget
- Zoom state: AppState.zoomRange = { min, max }, AppState.onZoomChange(min, max) already stubbed in Phase 2

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within Phase 3 scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NAVG-01 | User can zoom into a time range by click-dragging on the chart | uPlot cursor.drag.setScale:true enables native drag-to-zoom; setSelect hook fires with u.select.left/width to read chosen range; bidirectional drag handled by reading posToVal and taking Math.min/max |
| NAVG-02 | User can zoom in/out with the scroll wheel, centered on cursor position, without scrolling the page | wheel event on u.over element, e.preventDefault(), cursor-centered math with posToVal/setScale, clamp to data bounds |
| NAVG-03 | User can reset zoom to the full day view | setScale('x', {min: null, max: null}) resets to auto-range; button shown/hidden via setScale hook; double-click via u.over addEventListener('dblclick', ...) |
| NAVG-04 | User can see a cursor crosshair with tooltip showing values of all visible series at cursor time position | cursor MUST be re-enabled (show:true) at chart creation or the chart MUST be recreated — cursor.show:false prevents crosshair DOM creation; setCursor hook provides idx for value lookup |
| NAVG-05 | User can see an overview/minimap showing the full day with the current zoom range highlighted | secondary uPlot instance with full data, setSelect called from main chart's setScale hook to highlight zoom region; drag on minimap calls main chart's setScale |
</phase_requirements>

---

## Summary

Phase 3 adds all interactive navigation to the uPlot chart created in Phase 2. The core interactions are: drag-to-zoom (native uPlot via `cursor.drag.setScale: true`), scroll-wheel zoom (custom wheel handler on the `.over` element), cursor crosshair with tooltip (`setCursor` hook), minimap (second uPlot instance synced via `setScale` hook), and reset (button + double-click).

**Critical blocker discovered:** Phase 2 set `cursor: { show: false }` and `select: { show: false }`. Per uPlot's internal architecture, `cursor.show: false` prevents creation of the crosshair DOM elements (`.cursor-x`, `.cursor-y`) and the cursor data tracking that the `setCursor` hook relies on. `select.show: false` prevents creation of the selection overlay used during drag-to-zoom. **Phase 3 MUST recreate the uPlot instance** with `cursor: { show: true, x: true, y: true }` and appropriate `select` / `cursor.drag` configuration. The existing `createChart()` function will be modified in-place by Phase 3 to enable these features.

**Layout impact:** The chart currently fills `#chart-area` (top:90px to bottom:28px). Phase 3 adds (a) a toolbar row between header and chart, and (b) a minimap below the main chart. The layout coordinates must be recalculated: toolbar ~32px, chart fills the middle, minimap ~72px above the status bar.

**Primary recommendation:** Use uPlot's native `cursor.drag.setScale: true` for drag zoom, a custom wheel plugin for scroll zoom, a custom tooltip div appended to `u.over` updated in the `setCursor` hook, a secondary uPlot minimap instance synced via the main chart's `setScale` hook, and reset via `setScale('x', {min: null, max: null})`.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| uPlot | 1.6.32 (vendored IIFE) | All charting AND interaction | Already in use; provides cursor.drag, hooks system, setScale |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| None (vanilla JS) | N/A | Tooltip positioning, zoom logic | No extra deps needed; tooltip flip logic is 4 lines |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Secondary uPlot minimap | Canvas brush widget | Canvas brush requires ~200 lines of raw canvas code; secondary uPlot reuses existing rendering with 40 lines of sync code — use uPlot |
| placement.min.js for tooltip | Manual left/right flip | The official uPlot cursor-tooltip demo uses an external placement library, but for a single "flip when too close to right edge" behavior, 3 lines suffices: `tooltip.style.left = (left > chartW / 2) ? (left - tooltip.offsetWidth - 10) + 'px' : (left + 10) + 'px'` |

---

## Architecture Patterns

### Recommended Layout Structure

```
#app-header         (position:fixed, top:0, height:50px)      — existing
#data-summary       (position:fixed, top:50px, height:40px)    — existing
#toolbar-row        (position:fixed, top:90px, height:32px)    — NEW Phase 3
#chart-area         (position:fixed, top:122px, bottom:100px)  — ADJUSTED (was top:90px, bottom:28px)
#minimap-area       (position:fixed, bottom:28px, height:72px) — NEW Phase 3
#status-bar         (position:fixed, bottom:0, height:28px)    — existing
```

The toolbar row at `top:90px, height:32px` shifts chart-area top to `122px`. Minimap occupies the bottom 72px above the status bar. The minimap uPlot instance is created at `width: container.clientWidth, height: 72` with no legend, no axes labels, simplified rendering.

### Pattern 1: Native Drag-to-Zoom via cursor.drag

**What:** uPlot's built-in drag selection that calls `setScale` on mouseup to zoom to the selected region.
**When to use:** This is the ONLY correct approach for drag zoom — do not hand-roll mousedown/mousemove/mouseup.

```javascript
// Source: uPlot dist/uPlot.d.ts + zoom-ranger demo
// In createChart() opts:
cursor: {
  show: true,           // MUST be true — Phase 2 had this false
  x: true,
  y: false,
  drag: {
    setScale: true,     // zoom x on mouseup
    x: true,            // drag x axis only
    y: false,
    dist: 3,            // min px before drag activates (prevents click-to-zoom)
  },
},
select: {
  show: true,           // show the selection rectangle during drag
},
```

**Important: bidirectional drag.** When `cursor.drag.setScale: true`, uPlot natively handles both left-to-right and right-to-left drags — it internally takes `Math.min(posToVal(left), posToVal(left+width))` when computing the scale range. The `u.select.left` and `u.select.width` values in the `setSelect` hook will always have a positive width (uPlot normalizes the selection rectangle). So no special bidirectional handling is needed.

**After drag hook — notify minimap:**
```javascript
// Source: TypeScript defs — Hooks.Defs.setScale
hooks: {
  setScale: [(u, scaleKey) => {
    if (scaleKey === 'x') {
      const min = u.scales.x.min;
      const max = u.scales.x.max;
      AppState.zoomRange = { min, max };
      if (AppState.onZoomChange) AppState.onZoomChange(min, max);
      updateResetButtonVisibility(min, max);
    }
  }],
},
```

### Pattern 2: Scroll-Wheel Zoom Plugin

**What:** Custom wheel event listener on `u.over` that computes cursor-centered zoom and calls `setScale`.
**When to use:** Always — uPlot has no built-in scroll zoom.

```javascript
// Source: zoom-wheel.html official demo + issue #389 fix pattern
function wheelZoomPlugin(opts = {}) {
  const factor = opts.factor ?? 0.75;
  let rect;
  let xMin, xMax; // full data range — captured on ready

  return {
    hooks: {
      ready: [u => {
        // Capture full data range ONCE for clamping
        xMin = u.data[0][0];
        xMax = u.data[0][u.data[0].length - 1];

        rect = u.over.getBoundingClientRect();

        u.over.addEventListener('wheel', e => {
          e.preventDefault();    // prevent page scroll

          const { left } = u.cursor;
          const xVal  = u.posToVal(left, 'x');
          const oxRange = u.scales.x.max - u.scales.x.min;
          const leftPct = left / u.over.clientWidth;

          // Zoom in (deltaY < 0) shrinks range; out (deltaY > 0) expands
          let nxRange = e.deltaY < 0 ? oxRange * factor : oxRange / factor;

          // Apply zoom limits: min 5 min (300s), max full day range
          const minRange = 300;                    // 5 minutes in seconds
          const maxRange = xMax - xMin;            // full day
          nxRange = Math.max(minRange, Math.min(maxRange, nxRange));

          let nxMin = xVal - leftPct * nxRange;
          let nxMax = nxMin + nxRange;

          // Clamp to data bounds
          if (nxMin < xMin) { nxMin = xMin; nxMax = nxMin + nxRange; }
          if (nxMax > xMax) { nxMax = xMax; nxMin = nxMax - nxRange; }

          u.batch(() => {
            u.setScale('x', { min: nxMin, max: nxMax });
          });
        }, { passive: false });  // passive:false required for preventDefault
      }],

      setSize: [u => {
        rect = u.over.getBoundingClientRect();   // keep rect current after resize
      }],
    },
  };
}
```

**Passive event listener warning:** Browsers default wheel listeners to passive for performance. You MUST pass `{ passive: false }` to `addEventListener` or `e.preventDefault()` will throw an error and the page will still scroll.

### Pattern 3: Cursor Crosshair + Tooltip

**What:** Custom tooltip div appended to `u.over`, updated in the `setCursor` hook. The crosshair lines are rendered by uPlot's native cursor (enabled when `cursor.show: true`).
**When to use:** Always — the setCursor hook fires on every mousemove.

```javascript
// Source: tooltips.html official demo — adapted
function tooltipPlugin() {
  let tooltip;
  const OFFSET = 12;

  function init(u) {
    tooltip = document.createElement('div');
    tooltip.id = 'chart-tooltip';
    // styled via CSS: position:absolute, pointer-events:none, z-index:100
    tooltip.style.cssText = 'display:none; position:absolute; pointer-events:none; z-index:100;';
    u.over.appendChild(tooltip);

    u.over.addEventListener('mouseleave', () => { tooltip.style.display = 'none'; });
    u.over.addEventListener('mouseenter', () => { tooltip.style.display = ''; });
  }

  function setCursor(u) {
    const { left, top, idx } = u.cursor;
    if (idx == null) return;

    const ts = u.data[0][idx];  // Unix seconds
    const d  = new Date(ts * 1000);
    const hh = String(d.getUTCHours()).padStart(2, '0');
    const mm = String(d.getUTCMinutes()).padStart(2, '0');

    // Build HTML — header + one row per visible series
    let html = `<div class="tt-time">${hh}:${mm}</div>`;
    for (let i = 1; i < u.series.length; i++) {
      const s = u.series[i];
      if (!s.show) continue;   // skip hidden series
      const val = u.data[i][idx];
      const disp = (val == null || isNaN(val)) ? '—' : val;
      html += `<div class="tt-row">
        <span class="tt-swatch" style="background:${s.stroke}"></span>
        <span class="tt-label">${s.label}</span>
        <span class="tt-val">${disp}</span>
      </div>`;
    }
    tooltip.innerHTML = html;

    // Left/right flip to stay inside chart
    const chartW = u.over.clientWidth;
    const ttW    = tooltip.offsetWidth || 160;  // estimate before first render
    const flipX  = (left + ttW + OFFSET) > chartW;
    tooltip.style.left = flipX ? (left - ttW - OFFSET) + 'px' : (left + OFFSET) + 'px';
    tooltip.style.top  = Math.max(0, top - 10) + 'px';
  }

  return { hooks: { init, setCursor } };
}
```

**Tooltip CSS** (in the `<style>` block):
```css
#chart-tooltip {
  background: rgba(22, 33, 62, 0.95);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 12px;
  color: #e0e0e0;
  min-width: 140px;
  max-width: 220px;
  pointer-events: none;
  z-index: 100;
}
.tt-time { font-weight: 600; color: #81d4fa; margin-bottom: 4px; }
.tt-row  { display: flex; align-items: center; gap: 6px; padding: 1px 0; }
.tt-swatch { width: 10px; height: 2px; flex-shrink: 0; }
.tt-label  { flex: 1; color: #a0a0b8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tt-val    { font-variant-numeric: tabular-nums; color: #e0e0e0; text-align: right; }
```

### Pattern 4: Minimap via Secondary uPlot Instance

**What:** A second `uPlot` instance created with the full day's data at 72px height, rendered in `#minimap-area`. A `setSelect` overlay highlights the current zoom window. When the main chart's x-scale changes (via the `setScale` hook), the minimap's selection overlay is updated. Dragging in the minimap changes the main chart's zoom.
**When to use:** The secondary uPlot approach reuses all rendering logic and handles resize, dark theme, and stepped series automatically.

```javascript
// Source: zoom-ranger.html official demo — adapted
function createMinimap(data, series) {
  const container = document.getElementById('minimap-area');
  if (!container) return null;

  const minimapOpts = {
    width:  container.clientWidth,
    height: container.clientHeight,
    series,                              // same series opts as main chart
    legend:  { show: false },           // no legend in minimap
    axes:    [{ show: false }, { show: false }, { show: false }],  // no axes
    cursor: {
      show:   false,   // no crosshair in minimap (only selection highlight)
      drag:   { setScale: false, x: true, y: false },
      sync:   { key: 'minimap-sync' },
    },
    select: {
      show: true,
      over: true,
    },
    scales: {
      x:      {},
      y:      { auto: true },
      binary: { range: [0, 1] },
    },
    padding: [2, 0, 2, 0],
  };

  const uMinimap = new uPlot(minimapOpts, data, container);

  // Initialize selection to full range (no zoom)
  // (called after main chart sets initial zoom, or immediately as full-range highlight)
  function updateSelection(minTs, maxTs) {
    const left   = Math.round(uMinimap.valToPos(minTs, 'x'));
    const right  = Math.round(uMinimap.valToPos(maxTs, 'x'));
    const width  = right - left;
    const height = uMinimap.bbox.height / devicePixelRatio;
    uMinimap.setSelect({ left, width, height, top: 0 }, false);  // false = don't fire hook
  }

  // Wire minimap drag to pan/zoom the main chart
  // When user drags in minimap, its setScale hook would fire — but we set drag.setScale:false
  // Instead, intercept the setSelect hook on the minimap
  // NOTE: drag.setScale:false + drag.x:true means drag draws a selection but doesn't auto-zoom
  // We handle it manually in the setSelect hook:
  // uMinimap hooks.setSelect fires → read u.select → call AppState.chart.setScale

  return { instance: uMinimap, updateSelection };
}
```

**Sync wiring — main chart setScale hook calls minimap.updateSelection:**
```javascript
// Added to main chart's hooks.setScale alongside the reset button logic
setScale: [(u, scaleKey) => {
  if (scaleKey === 'x') {
    const min = u.scales.x.min;
    const max = u.scales.x.max;
    AppState.zoomRange = { min, max };
    if (AppState.onZoomChange) AppState.onZoomChange(min, max);
    updateResetButtonVisibility(min, max);
  }
}],
```

`AppState.onZoomChange` is wired to `minimap.updateSelection(min, max)` during chart init.

**Minimap drag to pan main chart:**
```javascript
// In minimap opts hooks:
hooks: {
  setSelect: [(uMinimap) => {
    // Fires when user drags in minimap
    // Convert pixel selection to data values
    const newMin = uMinimap.posToVal(uMinimap.select.left, 'x');
    const newMax = uMinimap.posToVal(uMinimap.select.left + uMinimap.select.width, 'x');
    if (AppState.chart) {
      AppState.chart.setScale('x', { min: newMin, max: newMax });
    }
  }],
}
```

### Pattern 5: Reset Button + Double-Click

**What:** A button in `#toolbar-row` that calls `setScale('x', {min: null, max: null})` to reset to full day. Hidden when at full range (detected via setScale hook comparing min/max to data bounds). Also, a double-click listener on `u.over` for the same action.

```javascript
// Source: issue #924 (null/null resets auto-range), issue #138 (dblclick on .over)
function resetZoom(u) {
  u.setScale('x', { min: null, max: null });
}

// Wire button
document.getElementById('reset-zoom-btn').addEventListener('click', () => {
  if (AppState.chart) resetZoom(AppState.chart);
});

// Wire double-click — must use capturing phase to intercept before uPlot's own dblclick
// But NOTE: uPlot v1.6.x registers its OWN dblclick handler on u.over for zoom-reset.
// This means double-click ALREADY resets zoom natively! We just need to add the button.
// If we want to add custom behavior alongside, attach a non-capturing listener (no stopPropagation needed).
AppState.chart.over.addEventListener('dblclick', () => {
  // uPlot's native dblclick already resets zoom — this is a no-op backup in case behavior changes
  // The built-in dblclick handler on .over calls setScale with null/null automatically
});
```

**Reset button visibility:**
```javascript
function updateResetButtonVisibility(min, max) {
  const btn = document.getElementById('reset-zoom-btn');
  if (!btn || !AppState.chart) return;
  const dataMin = AppState.chart.data[0][0];
  const dataMax = AppState.chart.data[0][AppState.chart.data[0].length - 1];
  const isFullRange = (min <= dataMin + 1) && (max >= dataMax - 1);  // 1s tolerance
  btn.style.display = isFullRange ? 'none' : '';
}
```

### Anti-Patterns to Avoid

- **Not recreating chart after Phase 2 stubs:** `cursor.show: false` means NO crosshair DOM exists. Adding a `setCursor` hook will not show crosshairs. Phase 3 MUST modify `createChart()` to set `cursor: { show: true }`. This requires updating the Phase 2 opts object — not a separate step, just changing the options.
- **Attaching wheel listener to the canvas element directly:** The canvas is behind `.u-over`. Wheel events on the canvas may not fire in all browsers. Always attach to `u.over`.
- **Using passive wheel listener:** `addEventListener('wheel', handler)` defaults to passive in modern browsers. Must use `{ passive: false }` option or `e.preventDefault()` throws.
- **Reading u.select.width for bidirectional drag:** When `cursor.drag.setScale: true`, uPlot handles bidirectional drag internally. Do NOT intercept the setSelect hook to manually call setScale — uPlot already calls it. Use the setScale hook ONLY to react to zoom changes (notify minimap, update reset button).
- **Creating minimap before main chart is sized:** `new uPlot()` requires the container to have non-zero dimensions. Create minimap after `showAppView()` makes `#minimap-area` visible.
- **Not updating minimap rect on resize:** Call `uMinimap.setSize()` from the existing `onWindowResize` handler alongside `AppState.chart.setSize()`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Drag-to-zoom selection rectangle | Custom mousedown/mousemove/mouseup | `cursor.drag.setScale: true` + `select.show: true` | uPlot handles selection rect rendering, bidirectional drag, threshold, and scale update |
| X-axis zoom from drag | Manual posToVal conversion in mouseup | `cursor.drag.setScale: true` calls setScale automatically | uPlot normalizes the selection and calls setScale correctly |
| Scroll zoom clamping | Custom range validation logic | Simple min/max clamp in the wheel handler | 3 lines; no library needed |
| Tooltip positioning | Viewport-aware positioning library | Manual left/right flip check | Chart boundary is known (`u.over.clientWidth`); one if-statement suffices |
| Minimap canvas rendering | Raw canvas API brush widget | Secondary uPlot instance | uPlot handles stepped series, resize, dark theme; canvas brush is ~300 lines of raw canvas code |
| Double-click zoom reset | Custom dblclick state machine | uPlot native dblclick on `.over` + reset button | uPlot already has built-in dblclick-to-reset behavior |

**Key insight:** uPlot's drag-zoom is fully built-in when `cursor.drag.setScale: true`. The only interaction uPlot does NOT provide natively is scroll-wheel zoom — that requires a custom plugin, but the official demo provides the exact pattern.

---

## Common Pitfalls

### Pitfall 1: cursor.show:false Blocks Crosshair DOM

**What goes wrong:** Phase 2 set `cursor: { show: false }`. If Phase 3 just adds `cursor.drag` opts or a `setCursor` hook without recreating the chart, no crosshair lines will appear and `cursor.idx` will always be null.
**Why it happens:** uPlot creates the cursor DOM elements (`.cursor-x`, `.cursor-y` divs, cursor point circles) conditionally during construction based on `cursor.show`. If `false`, those elements are never created.
**How to avoid:** Modify `createChart()` to set `cursor: { show: true, x: true, y: true }` with the Phase 3 options. Since `createChart()` always calls `destroyChart()` first, the new opts take effect on the next chart creation.
**Warning signs:** No crosshair visible on hover; `u.cursor.idx` is always null in console; tooltip never appears.

### Pitfall 2: select.show:false Blocks Drag Selection Rectangle

**What goes wrong:** Phase 2 set `select: { show: false }`. The drag-to-zoom selection highlight box (the blue rectangle during drag) will not render.
**Why it happens:** `select.show: false` tells uPlot not to show or update the selection rectangle div (`.u-select`).
**How to avoid:** Change `select: { show: false }` to `select: { show: true }` in the new opts in `createChart()`.
**Warning signs:** Drag zoom still works (setScale is called on mouseup) but no visual feedback during drag.

### Pitfall 3: Passive Wheel Event Prevents Scroll Guard

**What goes wrong:** `e.preventDefault()` throws "Unable to preventDefault inside passive event listener" in Chrome, and the page still scrolls.
**Why it happens:** Chrome and Firefox default wheel event listeners to passive for scroll performance.
**How to avoid:** Always register: `u.over.addEventListener('wheel', handler, { passive: false })`.
**Warning signs:** Console error "Unable to preventDefault"; page scrolls when over chart.

### Pitfall 4: Stale Rect in Wheel Zoom Plugin

**What goes wrong:** Zoom math is wrong after the browser window is resized because `rect = u.over.getBoundingClientRect()` was only called in the `ready` hook.
**Why it happens:** The bounding rect changes when the page is resized; `cursor.left` is relative to the `.over` element, so rect is not needed for cursor position calculations — but it IS needed if using `e.clientX` for position. Since we use `u.cursor.left` directly (not `e.clientX - rect.left`), the rect is not needed in the wheel handler. But if you switch to `e.clientX`, you need the `setSize` hook to refresh it.
**How to avoid:** Use `u.cursor.left` (already chart-relative) instead of `e.clientX - rect.left`. Or refresh rect in the `setSize` hook.
**Warning signs:** Zoom math drifts after window resize; cursor appears to be at wrong position for zoom centering.

### Pitfall 5: double-zoom From setScale Hook Calling Minimap setScale

**What goes wrong:** Main chart setScale hook calls `minimap.updateSelection()` → minimap's setSelect fires → minimap's setSelect hook calls `AppState.chart.setScale()` → infinite loop.
**Why it happens:** The minimap sync creates a circular dependency if not guarded.
**How to avoid:** Pass `false` as the second argument to `minimap.setSelect({...}, false)` — this prevents the setSelect hook from firing during programmatic updates. This is explicitly documented in the TypeScript definitions: `setSelect(opts, fireHook?: boolean)`.
**Warning signs:** Chart freezes or browser becomes unresponsive; stack overflow errors in console.

### Pitfall 6: Minimap Series Not Simplified Enough

**What goes wrong:** Minimap renders all series at full detail, causing 70+ series to render in 72px height — indistinguishable and slow.
**Why it happens:** Using the same series opts as the main chart in the minimap.
**How to avoid:** For the minimap, use a simplified series array: show only the 2-3 most important series (KT Ist, AT, BR), or use all series but with thinner strokes (`width: 0.5`). The minimap is for navigation only — full detail is unnecessary.
**Warning signs:** Minimap renders as an indistinct mass of lines; performance degrades on 70-column files.

### Pitfall 7: uPlot Batch Not Used for Multi-Scale Updates

**What goes wrong:** Calling `u.setScale('x', ...)` and `u.setScale('y', ...)` separately causes two redraws.
**Why it happens:** Each `setScale` call triggers a full redraw.
**How to avoid:** In the scroll zoom handler, wrap both calls in `u.batch(() => { ... })`. For Phase 3 we only zoom the x-axis, so this is less critical — but it's still best practice.

---

## Code Examples

Verified patterns from official sources:

### 1. Reading cursor values in setCursor hook
```javascript
// Source: tooltips.html official demo
function setCursor(u) {
  const { left, top, idx } = u.cursor;
  if (idx == null) return;

  // Read raw data value for series i at cursor index
  const val = u.data[i][idx];

  // Check if series is visible
  const isVisible = u.series[i].show !== false;
}
```

### 2. Full setScale to reset zoom
```javascript
// Source: GitHub issue #924 — confirmed by maintainer
u.setScale('x', { min: null, max: null }); // auto-range back to full data
```

### 3. Convert pixel position to data value (for wheel zoom)
```javascript
// Source: zoom-wheel.html official demo
const xVal = u.posToVal(u.cursor.left, 'x');
```

### 4. Convert data value to pixel position (for minimap selection)
```javascript
// Source: zoom-ranger.html official demo
const left  = Math.round(u.valToPos(minTs, 'x'));
const width = Math.round(u.valToPos(maxTs, 'x')) - left;
const height = u.bbox.height / devicePixelRatio;
u.setSelect({ left, width, height, top: 0 }, false);
```

### 5. Attaching dblclick listener correctly
```javascript
// Source: GitHub issue #138 — maintainer confirmed
u.root.querySelector('.u-over').addEventListener('dblclick', handler);
// OR use u.over directly (same element):
u.over.addEventListener('dblclick', handler);
```

### 6. Wheel zoom with cursor-centering
```javascript
// Source: zoom-wheel.html official demo
const leftPct = u.cursor.left / u.over.clientWidth;
const xVal    = u.posToVal(u.cursor.left, 'x');
const oxRange = u.scales.x.max - u.scales.x.min;
const nxRange = e.deltaY < 0 ? oxRange * factor : oxRange / factor;
let nxMin = xVal - leftPct * nxRange;
let nxMax = nxMin + nxRange;
// clamp to data bounds...
u.batch(() => { u.setScale('x', { min: nxMin, max: nxMax }); });
```

### 7. Plugin structure
```javascript
// Source: uPlot TypeScript definitions + tooltips.html demo
const myPlugin = {
  hooks: {
    init:      [(u, opts, data) => { /* setup */ }],
    setCursor: [(u) => { /* cursor moved */ }],
    setScale:  [(u, scaleKey) => { /* scale changed */ }],
    setSize:   [(u) => { /* chart resized */ }],
    setSelect: [(u) => { /* drag selection completed */ }],
    destroy:   [(u) => { /* cleanup */ }],
  },
};

// In opts:
const opts = {
  // ...
  plugins: [myPlugin],
};
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Attaching events to canvas element | Attach to `u.over` div | uPlot restructured DOM in ~v1.4 | Canvas may not receive mouse events through uPlot's overlay |
| Static array for scale.range | Callback function for dynamic range | v1.x | Allows programmatic initial zoom without disabling user interaction |
| cursor.drag default (x only) | `cursor.drag.x: true, y: false` | v1.x | Y-axis drag removed to prevent accidental Y zoom in time series charts |

**Deprecated/outdated:**
- Setting `ondblclick` directly on canvas: uPlot restructured its DOM. Attach to `u.over` instead. (Confirmed in issue #138)
- Multiple calls to `setScale` outside `batch()`: Works but causes multiple redraws; use `batch()` for simultaneous x+y updates.

---

## Open Questions

1. **Does uPlot v1.6.32 double-click behavior reset to null/null automatically?**
   - What we know: The maintainer confirmed uPlot has a built-in dblclick reset, and it's mentioned in multiple issues. Issue #138 confirms dblclick is handled on `.over` div.
   - What's unclear: Whether v1.6.32 specifically calls `setScale(null, null)` on dblclick or does something slightly different (e.g., resetting to initial opts scale range).
   - Recommendation: Test in browser after chart creation. If native dblclick doesn't reset correctly, add our own: `u.over.addEventListener('dblclick', () => resetZoom(u))` with capture:true and stopPropagation to override. The reset button provides a reliable fallback regardless.

2. **Does cursor.drag handle bidirectional (right-to-left) drag natively in v1.6.32?**
   - What we know: uPlot's selection rectangle normalizes to always have positive width internally. The `u.select.left` and `u.select.width` in hooks are always normalized.
   - What's unclear: Whether the internal min/max calculation is guaranteed to swap correctly for right-to-left drag.
   - Recommendation: LOW risk — if it doesn't work natively, intercept in `setSelect` hook: `const min = Math.min(posToVal(left), posToVal(left+width)); const max = Math.max(...)` and call setScale manually with `drag.setScale: false`. Test in browser.

3. **Minimap height and `#chart-area` adjustment impact on Phase 4 toolbar**
   - What we know: CONTEXT.md says the toolbar row will also hold Phase 4 view tabs. The toolbar is at `top: 90px` (below header and data-summary).
   - What's unclear: The exact pixel height needed for the toolbar row — 32px is estimated for a button row, but Phase 4 may need more space for tabs.
   - Recommendation: Use CSS variables for layout heights. Define `--toolbar-height: 32px` and `--minimap-height: 72px` so Phase 4 can adjust without recalculating pixel math.

---

## Sources

### Primary (HIGH confidence)
- [uPlot dist/uPlot.d.ts](https://raw.githubusercontent.com/leeoniya/uPlot/master/dist/uPlot.d.ts) — TypeScript definitions: setScale, setSelect, setCursor, hooks, cursor.drag, batch, plugin structure
- [uPlot tooltips.html demo](https://raw.githubusercontent.com/leeoniya/uPlot/master/demos/tooltips.html) — Complete tooltip plugin source: setCursor hook, cursor.idx, posToVal, u.over event listeners
- [uPlot zoom-ranger.html demo](https://leeoniya.github.io/uPlot/demos/zoom-ranger.html) — Secondary chart minimap pattern: setSelect, valToPos, sync key

### Secondary (MEDIUM confidence)
- [GitHub issue #389](https://github.com/leeoniya/uPlot/issues/389) — Wheel zoom plugin: setSize hook for rect refresh, u.root.querySelector('.u-over'), passive:false requirement
- [GitHub issue #924](https://github.com/leeoniya/uPlot/issues/924) — Reset zoom: `setScale('x', {min: null, max: null})` confirmed by maintainer
- [GitHub issue #138](https://github.com/leeoniya/uPlot/issues/138) — Double-click: attach to `.over`, not canvas; use capturing phase with stopPropagation to override
- [GitHub issue #154](https://github.com/leeoniya/uPlot/issues/154) — cursor.show: confirmed DOM-structural setting (cannot be changed after init); cursor.x/y cannot be toggled post-init; CSS toggle workaround for visibility
- [GitHub issue #867](https://github.com/leeoniya/uPlot/issues/867) — setSelect hook: u.select.left/width available; posToVal usage; second argument `false` to prevent re-fire
- [GitHub issue #187](https://github.com/leeoniya/uPlot/issues/187) — Zoom limits: scale.range callback for min/max clamping

### Tertiary (LOW confidence)
- General WebSearch patterns for minimap drag-to-pan and zoom limit clamping — cross-verified against TypeScript definitions and official demos

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — uPlot APIs verified against TypeScript definitions and official demos
- Architecture (drag/scroll zoom): HIGH — verified against official demo code (zoom-wheel.html, zoom-ranger.html)
- Cursor/tooltip pattern: HIGH — complete source from tooltips.html demo
- Minimap pattern: MEDIUM — zoom-ranger.html confirms the secondary instance approach, but the full bidirectional sync code was inferred from the pattern (not fully shown in demo source)
- Pitfalls: HIGH — cursor.show and select.show behaviors confirmed by maintainer in GitHub issues
- Phase 2 compatibility (need to change cursor/select opts): HIGH — confirmed from issue #154 and source analysis

**Research date:** 2026-02-18
**Valid until:** 2026-06-01 (uPlot v1.6.32 is vendored and frozen — no staleness risk)
