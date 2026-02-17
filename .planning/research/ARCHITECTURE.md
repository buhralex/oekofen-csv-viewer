# Architecture Research

**Domain:** Client-side interactive time-series chart viewer (browser-only, single HTML file)
**Researched:** 2026-02-17
**Confidence:** HIGH (patterns are well-established; library-specific details verified via Context7/official docs)

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        UI / Shell Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  Drop Zone   │  │  View Tabs   │  │  Control Bar       │    │
│  │  (file entry)│  │  (presets +  │  │  (zoom reset,      │    │
│  │              │  │   custom)    │  │   param toggles)   │    │
│  └──────┬───────┘  └──────┬───────┘  └────────┬───────────┘    │
│         │                 │                    │                 │
├─────────┴─────────────────┴────────────────────┴────────────────┤
│                        App State (Central Store)                 │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────────┐  │
│  │ rawData     │  │ activeView       │  │ chartState        │  │
│  │ (parsed     │  │ (preset name or  │  │ (zoom range,      │  │
│  │  CSV rows)  │  │  custom params)  │  │  cursor pos,      │  │
│  │             │  │                  │  │  series visible)  │  │
│  └──────┬──────┘  └────────┬─────────┘  └────────┬──────────┘  │
│         │                  │                      │              │
├─────────┴──────────────────┴──────────────────────┴─────────────┤
│                        Chart Layer                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    uPlot instance                         │   │
│  │  (canvas 2D, aligned columnar data, hooks/plugins for    │   │
│  │   zoom-wheel, zoom-drag, cursor sync, legend values)     │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                        Data Pipeline                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐     │
│  │ CSV Parser  │  │  Normalizer  │  │  Series Builder    │     │
│  │ (PapaParse) │→ │  (German     │→ │  (columnar arrays  │     │
│  │             │  │   decimals,  │  │   for uPlot,       │     │
│  │             │  │   timestamps)│  │   param metadata)  │     │
│  └─────────────┘  └──────────────┘  └────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Drop Zone | Accept File objects from drag-and-drop and file picker; fire "file selected" event | `dragover`/`drop` event listeners on a `<div>`; passes `File` to CSV Parser |
| CSV Parser | Read raw file bytes and produce structured row arrays with header metadata | PapaParse with `delimiter:";"`, `header:true`, `skipEmptyLines:true` |
| Normalizer | Convert German locale decimals (`,` → `.`), parse `DD.MM.YYYY HH:MM:SS` timestamps to Unix epoch integers, validate columns | Plain JS string replacement + `Date.parse` or manual epoch math |
| Series Builder | Convert normalized row-oriented data into uPlot's columnar format; attach per-column metadata (unit, group, display name) | Transposes rows→columns; extracts metadata from header strings like `HK1 VL Ist[C]` |
| App State Store | Single source of truth for: parsed dataset, active view definition, chart zoom window, cursor position, per-series visibility | Plain JS object + setter functions that call `renderChart()` (no framework needed at this scale) |
| View Manager | Define and resolve preset views (Boiler, HK, WW, Buffer, PE1) to lists of column names; support custom selection | Object map: `{ "boiler": ["KT", ...], "hk1": ["HK1 VL Ist[C]", ...] }` |
| Chart Renderer | Accept state slice (columns subset + visible flags + zoom range) and create/update a uPlot instance | Builds `opts` from series metadata + applies zoom plugins; calls `u.setData()`/`u.setScale()` on state change |
| Control Bar | Render series checkboxes, zoom reset button, cursor value display; dispatch state changes on user interaction | HTML + event listeners delegated to state store setters |

---

## Recommended Project Structure

```
/                          # Single distributable directory
├── index.html             # Entry point — loads all scripts, defines DOM skeleton
├── app.js                 # App shell: wires components together, owns state store
├── parser/
│   ├── csvParser.js       # PapaParse wrapper: File → raw PapaParse result
│   └── normalizer.js      # German decimals, timestamp conversion, column metadata extraction
├── model/
│   ├── dataModel.js       # Row-oriented store; exposes getColumn(name), getTimestamps()
│   └── viewDefinitions.js # Preset view configurations (param group → column list mappings)
├── chart/
│   ├── seriesBuilder.js   # dataModel → uPlot-format columnar arrays + series opts
│   ├── chartRenderer.js   # uPlot lifecycle: create, setData, setScale, destroy
│   └── plugins/
│       ├── zoomPlugin.js  # Wheel zoom + drag-to-zoom via uPlot hooks
│       └── cursorPlugin.js# Crosshair + tooltip value display via uPlot cursor hooks
├── ui/
│   ├── dropZone.js        # Drag-and-drop and file picker: fires "file-loaded" event
│   ├── viewTabs.js        # Preset + custom tab rendering and click handling
│   ├── paramPanel.js      # Series checkboxes, show/hide dispatch
│   └── controls.js        # Zoom reset button, status messages
└── lib/
    ├── uplot.min.js       # Vendored uPlot (no CDN dependency for offline use)
    └── papaparse.min.js   # Vendored PapaParse
```

### Structure Rationale

- **parser/:** Isolated from chart code. Easily unit-tested with a fixture CSV. German locale quirks are contained here.
- **model/:** Separates storage from rendering. seriesBuilder reads from model; chart never touches raw parse output.
- **chart/:** uPlot-specific code stays here. If the charting library ever changes, only this directory is replaced.
- **ui/:** All DOM manipulation. Each file owns exactly one UI surface. No UI file touches chart state directly — it dispatches to app.js.
- **lib/:** Vendored dependencies. The app must work by opening `index.html` from the filesystem (no CDN, no build step).

---

## Architectural Patterns

### Pattern 1: Columnar Data Store (aligned arrays)

**What:** Store all time-series data as parallel arrays after parsing. One array of Unix epoch timestamps (integers), one array per numeric column. This is uPlot's native format.

**When to use:** Always, for this project. uPlot requires aligned columnar data; building it during series selection rather than at parse time adds unnecessary latency.

**Trade-offs:**
- Pro: Zero transformation cost at render time; uPlot receives data directly.
- Pro: Memory-efficient for 1440 x 70 columns (~100K numbers) — well within browser limits.
- Con: All columns must be pre-allocated; sparse series need null-fill (not an issue here since OekoFEN CSV is fully aligned — all rows have all columns).

**Example:**
```javascript
// dataModel.js
const model = {
  timestamps: Int32Array,   // Unix epoch seconds, length=1440
  columns: {
    "KT [C]":   Float32Array,  // Boiler temp
    "HK1 VL Ist[C]": Float32Array,
    // ...one Float32Array per numeric column
  },
  meta: {
    "KT [C]": { group: "boiler", unit: "C", label: "KT" },
    // ...
  }
};
```

### Pattern 2: One-Way Data Flow (parse → model → chart)

**What:** Data flows in a single direction. The CSV Parser writes to the model once. The View Manager selects a subset. The Series Builder transforms that subset. The Chart Renderer consumes the result. No component writes back upstream.

**When to use:** Always for this project. Without a framework, explicit one-way flow prevents the subtle bugs that arise when chart interactions accidentally mutate parse state.

**Trade-offs:**
- Pro: State changes are traceable — a bug is always in exactly one stage of the pipeline.
- Pro: Any stage can be replaced or tested in isolation.
- Con: Slightly more boilerplate than allowing components to read/write freely. Acceptable at this project size.

**Example:**
```javascript
// app.js — the only file that orchestrates flow
async function onFileLoaded(file) {
  const raw = await csvParser.parse(file);        // stage 1
  const normalized = normalizer.process(raw);     // stage 2
  dataModel.load(normalized);                     // stage 3: model stores columns
  applyView(state.activeView);                    // stage 4: select subset
}

function applyView(viewName) {
  const columns = viewDefinitions[viewName];      // resolve preset
  const chartData = seriesBuilder.build(dataModel, columns, state.visible);
  chartRenderer.render(chartData);                // stage 5: uPlot renders
}
```

### Pattern 3: uPlot Hooks for Interaction (Plugins)

**What:** Use uPlot's lifecycle hooks (`init`, `setCursor`, `setScale`) to implement zoom and cursor inspection as self-contained plugin objects rather than code scattered in the renderer.

**When to use:** Zoom-drag, zoom-wheel, and crosshair cursor all require responding to uPlot's internal state. Hooks are the official extension mechanism — using them keeps chart renderer code clean.

**Trade-offs:**
- Pro: Plugins are reusable and testable in isolation.
- Pro: Avoids monkey-patching uPlot or duplicating canvas event handling.
- Con: Requires understanding uPlot's hook execution order (documented but non-obvious).

**Example:**
```javascript
// plugins/zoomPlugin.js
export function wheelZoomPlugin() {
  return {
    hooks: {
      init(u) {
        u.over.addEventListener("wheel", (e) => {
          e.preventDefault();
          const factor = e.deltaY > 0 ? 1.1 : 0.9;
          const xScale = u.scales.x;
          const center = u.posToVal(u.cursor.left, "x");
          const halfSpan = (xScale.max - xScale.min) / 2 * factor;
          u.setScale("x", { min: center - halfSpan, max: center + halfSpan });
        });
      }
    }
  };
}
```

---

## Data Flow

### File-to-Chart Pipeline

```
User drops file
    |
    v
[dropZone.js]
    | File object
    v
[csvParser.js]  ← PapaParse(file, { delimiter:";", header:true })
    | { data: [{col: val, ...}, ...], meta: { fields: [...] } }
    v
[normalizer.js]
    | Replaces "," with "." in numeric strings
    | Parses "DD.MM.YYYY HH:MM:SS" → Unix epoch int
    | Extracts unit from header: "KT [C]" → { name:"KT", unit:"C" }
    v
[dataModel.js]  ← stores columnar Float32Arrays + metadata map
    |
    v
[viewDefinitions.js]  ← resolves preset name → column list
    |
    v
[seriesBuilder.js]
    | Builds uPlot data: [ timestamps[], col1[], col2[], ... ]
    | Builds uPlot series opts: [ {}, {label, stroke, show}, ... ]
    v
[chartRenderer.js]  ← new uPlot(opts, data, element)
    |
    v
Canvas renders time-series chart
```

### State Change Flow (interaction → chart update)

```
User interaction (tab click, checkbox, zoom reset)
    |
    v
[ui/*.js]  — event handler
    | calls state setter in app.js
    v
[app.js state store]
    | mutates state.activeView / state.visible / state.zoomRange
    | calls applyView() or chartRenderer.update()
    v
[chartRenderer.js]
    | u.setData(newData)  OR  u.setScale("x", newRange)  OR  u.setSeries(idx, {show})
    v
uPlot redraws (incremental — does not destroy/recreate instance)
```

### Key State Transitions

1. **File load:** Drop Zone → Parser → Normalizer → Model → View applied → Chart created (first render)
2. **Preset tab switch:** View tab click → View Manager resolves columns → Series Builder → Chart `setData` (model unchanged)
3. **Series toggle:** Checkbox → `u.setSeries(idx, { show: bool })` (no data rebuild needed)
4. **Zoom (drag/scroll):** uPlot internal → hook fires → `u.setScale("x", ...)` (uPlot handles redraw)
5. **Zoom reset:** Reset button → `u.setScale("x", { min: dayStart, max: dayEnd })` (restore full extent)

---

## Anti-Patterns

### Anti-Pattern 1: Rebuilding the uPlot Instance on Every State Change

**What people do:** Call `new uPlot(opts, data, el)` whenever the view, zoom, or series visibility changes — often because it feels simpler.

**Why it's wrong:** uPlot instantiation is fast but not free. More importantly, it resets zoom state, animation state, and cursor position. Users lose their context. Also, this couples chart options (static) to data (dynamic) unnecessarily.

**Do this instead:** Create the uPlot instance once per file load. Use `u.setData()` to change series data, `u.setSeries(idx, opts)` to toggle visibility, and `u.setScale("x", range)` to change zoom. Only recreate the instance when the chart axes or series count fundamentally change (e.g., switching from a 5-series preset to a 10-series custom view).

---

### Anti-Pattern 2: Row-Oriented Data at Render Time

**What people do:** Keep parsed CSV rows as an array of objects `[{timestamp, KT, HK1_VL, ...}, ...]` and extract columns only when building chart series — often inside a render loop.

**Why it's wrong:** Extracting a column from 1440 row-objects on every render is 1440 property lookups, every time the view changes. It also makes the German decimal conversion run multiple times if not carefully cached.

**Do this instead:** Transpose to columnar format once, immediately after parsing. Store `Float32Array` per column. All downstream code operates on pre-computed arrays at zero additional cost.

---

### Anti-Pattern 3: Decimal Conversion via `dynamicTyping: true` Alone

**What people do:** Pass `dynamicTyping: true` to PapaParse and expect it to handle German decimals (e.g., `"23,5"` → `23.5`).

**Why it's wrong:** PapaParse's `dynamicTyping` assumes English locale (period as decimal). `"23,5"` will be typed as the string `"23,5"` or parsed as integer `23` depending on context — both silently wrong. [Confirmed in PapaParse issue #143 and #327.]

**Do this instead:** Use `dynamicTyping: false` in PapaParse. In the Normalizer, explicitly replace commas with periods in numeric fields before `parseFloat()`. Validate that the result is a finite number; otherwise store `null`.

---

### Anti-Pattern 4: Mixing UI State into the Data Model

**What people do:** Attach `visible: true/false` flags, color assignments, or display labels directly to the parsed column data objects.

**Why it's wrong:** The data model is reused across all views and should be stateless. Mixing UI state into it means switching views corrupts previous UI state, or requires defensive copying.

**Do this instead:** Keep UI state (series visibility, colors) in the App State Store, keyed by column name. The Series Builder reads both: column arrays from the data model, and visibility/color from the state store.

---

## Integration Points

### External Libraries (Vendored in `/lib/`)

| Library | Integration Pattern | Notes |
|---------|---------------------|-------|
| uPlot (~50 KB) | Instantiated in `chartRenderer.js`; plugins via hooks array in `opts` | Requires aligned columnar data; x-axis must be Unix epoch seconds (integer) |
| PapaParse (~50 KB) | Called once per file load; synchronous or async with `complete` callback | Use `Papa.parse(file, { ... })` with a File object directly from drop event |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| dropZone → app.js | Custom DOM event `"file-loaded"` with `event.detail.file` | Decouples file entry from parse logic |
| app.js → parser/* | Direct function calls (synchronous normalize; async parse) | Parser returns plain data structures, not DOM elements |
| app.js → dataModel | `dataModel.load(normalized)` write; `dataModel.getColumn(name)` read | Model is a module singleton — one dataset in memory at a time |
| app.js → chartRenderer | `chartRenderer.create(opts, data, el)` and `chartRenderer.update(patch)` | Renderer never reads from model directly |
| ui/* → app.js | Call exported state setters (e.g., `app.setView("boiler")`) | UI never writes to model or renderer directly |

---

## Build Order Implications

The component dependency graph dictates this build order:

```
1. CSV Parser + Normalizer
       ↓  (depends on nothing)
2. Data Model
       ↓  (depends on normalized data shape)
3. View Definitions
       ↓  (depends on column names from CSV)
4. Series Builder
       ↓  (depends on data model + view definitions)
5. Chart Renderer (uPlot wrapper)
       ↓  (depends on series builder output format)
6. Chart Plugins (zoom, cursor)
       ↓  (depends on uPlot instance existing)
7. UI Components (dropZone, viewTabs, paramPanel, controls)
       ↓  (depends on app.js state API existing)
8. App Shell (app.js)
       ↓  (wires all above together)
9. Integration / End-to-End (full file-drop to chart render path)
```

**Key dependency insight:** The Normalizer must handle German decimals correctly before anything else can work. It is the highest-risk component and should be implemented and tested with a real OekoFEN CSV file before building the chart layer. If timestamp parsing or decimal conversion is wrong, all downstream work is invalid.

---

## Scalability Considerations

This is a single-user, single-file, client-side application. Traditional scalability (users, servers) does not apply. The relevant scaling axis is **data volume**:

| Scale | Architecture Adjustment |
|-------|--------------------------|
| 1440 rows x 70 cols (one day — current) | No optimization needed. Float32Array per column fits in ~400 KB total. uPlot renders 1440 points in <5 ms. |
| 10,000+ rows (multi-day, if added later) | Switch to streaming parse (PapaParse `step` callback) to avoid blocking UI during parse. Consider Web Worker for normalizer. |
| 100,000+ rows | Move to Web Worker for entire parse+normalize pipeline; use uPlot's downsampling or LTTB algorithm to reduce render point count. |

For the defined scope (single day, ~1440 rows), no optimization beyond typed arrays is needed.

---

## Sources

- uPlot GitHub README and docs: [https://github.com/leeoniya/uPlot](https://github.com/leeoniya/uPlot) — HIGH confidence (official repository)
- uPlot DeepWiki architecture overview: [https://deepwiki.com/leeoniya/uPlot](https://deepwiki.com/leeoniya/uPlot) — MEDIUM confidence (derived from source)
- uPlot docs/README.md (columnar format, scales, series): [https://github.com/leeoniya/uPlot/blob/master/docs/README.md](https://github.com/leeoniya/uPlot/blob/master/docs/README.md) — HIGH confidence (official)
- PapaParse official docs (delimiter, header, dynamicTyping, File object): [https://www.papaparse.com/docs](https://www.papaparse.com/docs) — HIGH confidence (official)
- PapaParse issue #143 (German decimal comma not handled by dynamicTyping): [https://github.com/mholt/PapaParse/issues/143](https://github.com/mholt/PapaParse/issues/143) — HIGH confidence (official issue tracker)
- PapaParse issue #327 (dynamicTyping + decimal points): [https://github.com/mholt/PapaParse/issues/327](https://github.com/mholt/PapaParse/issues/327) — HIGH confidence (official issue tracker)
- AWS Synchro Charts (time-series viewer component architecture): [https://aws.amazon.com/blogs/opensource/visualizing-time-series-data-with-the-open-source-synchro-charts/](https://aws.amazon.com/blogs/opensource/visualizing-time-series-data-with-the-open-source-synchro-charts/) — MEDIUM confidence (AWS reference architecture)
- Vanilla JS state management patterns 2026: [https://medium.com/@chirag.dave/state-management-in-vanilla-js-2026-trends-f9baed7599de](https://medium.com/@chirag.dave/state-management-in-vanilla-js-2026-trends-f9baed7599de) — LOW confidence (blog, single source)

---
*Architecture research for: Client-side interactive time-series chart viewer (OekoFEN CSV Viewer)*
*Researched: 2026-02-17*
