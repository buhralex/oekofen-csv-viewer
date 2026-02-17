# Stack Research

**Domain:** Client-side time-series CSV visualization (no-server, pure browser)
**Researched:** 2026-02-17
**Confidence:** HIGH (core choices verified against npm registry, official docs, and live demos)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| uPlot | 1.6.32 | Interactive time-series chart rendering | Purpose-built for time-series; ~50 KB minified; renders 166,650 points in 25 ms; native cursor sync and zoom; the only Canvas-based library at this scale that does not need a build step (ships `uPlot.iife.js` for script-tag use). [HIGH confidence] |
| PapaParse | 5.5.3 | CSV parsing with semicolon delimiter and dynamic typing | De-facto standard browser CSV parser; `delimiter: ";"` config covers German locale; `dynamicTyping` converts numeric strings to numbers automatically; streaming mode prevents OOM on large files; single-file CDN delivery. [HIGH confidence] |
| Vanilla JS (ES2020+) | — | Application glue, state, DOM | No framework overhead needed; `<input type="file">` + `FileReader` API is sufficient for drag-and-drop; keeps the deliverable a single HTML file with no runtime dependencies beyond the two libraries above. [HIGH confidence] |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| uPlot wheel-zoom plugin | (bundled inline, ~80 LOC) | Scroll-wheel zoom + middle-click drag pan | Always — uPlot ships no built-in pan; the official demo plugin (`zoom-wheel.html`) is copy-pasteable inline; no separate package needed. [HIGH confidence] |
| Day.js | 1.11.x | Timestamp parsing / display formatting | Only if German-locale date strings (`DD.MM.YYYY HH:mm`) need parsing beyond `Date.parse`; weighs 2 KB; load via CDN if added. [MEDIUM confidence — may not be needed if timestamps are Unix epoch in CSV] |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| No build tool (runtime) | Project constraint | The deliverable must open as a bare HTML file; CDN script tags satisfy this fully. No Vite/Webpack/Rollup at runtime. |
| Live Server (VS Code extension) | Local dev server | Avoids `file://` CORS restrictions during development; not shipped to users. |
| ESLint (optional) | Lint JS in the HTML file | Inline scripts can be linted with eslint-plugin-html if needed; not mandatory. |

---

## Installation

This project delivers a single `.html` file. "Installation" means adding CDN script tags:

```html
<!-- uPlot: chart rendering -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/uplot@1.6.32/dist/uPlot.min.css">
<script src="https://cdn.jsdelivr.net/npm/uplot@1.6.32/dist/uPlot.iife.min.js"></script>

<!-- PapaParse: CSV parsing -->
<script src="https://cdn.jsdelivr.net/npm/papaparse@5.5.3/papaparse.min.js"></script>
```

Inline wheel-zoom/pan plugin (copy from official uPlot demo — ~80 lines of vanilla JS):

```javascript
// Paste wheelZoomPlugin() function directly into a <script> block
function wheelZoomPlugin(opts) {
  let factor = opts.factor || 0.75;
  // ... (see https://leeoniya.github.io/uPlot/demos/zoom-wheel.html)
}
```

No npm, no Node.js, no build pipeline required.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| uPlot 1.6.32 | Apache ECharts 6.0.0 | When you need richer built-in chart types (bar, pie, heatmap), declarative config, or a larger ecosystem. ECharts full build is ~1 MB+ minified — acceptable, but 20x heavier than uPlot for the same time-series line chart. Prefer if the chart variety requirement expands significantly. |
| uPlot 1.6.32 | Chart.js 4.x | When audience expects a well-known library and ~70 time-series columns with toggle is the full scope. Chart.js is heavier (~254 KB), slower on large datasets, but more beginner-friendly and better documented for non-time-series types. |
| uPlot 1.6.32 | Plotly.js 2.x | When users need scientific annotations, 3D charts, or built-in statistical traces. Plotly.js is 3.6 MB minified, renders 310 ms for comparable data, and is overkill for a sensor data viewer. |
| PapaParse 5.5.3 | Native `String.split` | Only for trivially small files with no edge cases. PapaParse handles quoted fields, escaped delimiters, mixed line endings, and BOM — all of which appear in real OekoFEN exports. Do not hand-roll a CSV parser. |
| Vanilla JS | Alpine.js 3.15.8 | If the UI grows to need reactive show/hide of 70 series checkboxes, Alpine.js (15 KB) provides clean x-data/x-model bindings without a build step. Not needed for MVP; add it if vanilla DOM manipulation becomes unwieldy. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| React / Vue / Svelte (full framework) | All require a build step; conflict with the "open HTML file" constraint. Svelte ships compiled output but the dev workflow still needs Node. | Vanilla JS or Alpine.js (CDN) |
| Plotly.js | 3.6 MB download; 310 ms render for datasets this project handles in < 30 ms with uPlot; no meaningful advantage for line charts with zoom. | uPlot |
| D3.js (for charting) | D3 is a low-level drawing primitives library, not a charting library. Building zoom, crosshairs, tooltips, and multi-series from D3 alone is a multi-week effort. D3's strength is custom novel visualizations — not interactive line charts. | uPlot |
| native `<canvas>` drawing | Requires re-implementing everything uPlot already provides: hit testing, scale management, cursor sync, responsive resize. | uPlot |
| Moment.js | Deprecated by its own authors; 67 KB; superseded by Day.js (2 KB) or native `Intl` APIs. | Day.js or `Intl.DateTimeFormat` |
| WebGL-based charting (LightningChart, SciChart) | Powerful but commercial / licensed; significant integration complexity; unnecessary for 70 series at 1-minute intervals (~1,440 points/day per series). | uPlot |

---

## Stack Patterns by Variant

**If the CSV timestamp column is already a Unix timestamp (seconds or ms):**
- uPlot accepts Unix epoch timestamps natively; no date parsing library needed.
- PapaParse `dynamicTyping: true` will convert the column automatically.

**If the CSV timestamp is a German locale string (e.g., `01.02.2025 14:30`):**
- Parse with `new Date(str.split('.').reverse().join('-'))` inline, or add Day.js `customParseFormat` plugin.
- Pass the resulting Unix timestamp array to uPlot's `data[0]`.

**If the user needs to compare multiple days:**
- Load multiple CSVs into separate uPlot series arrays; uPlot's cursor sync API (`setSeries`, `setCursor`) handles multi-chart synchronization.
- This is an enhancement, not MVP scope.

**If 70 checkboxes become unmanageable as vanilla DOM:**
- Drop in Alpine.js via CDN: `<script src="https://cdn.jsdelivr.net/npm/alpinejs@3.15.8/dist/cdn.min.js" defer></script>`.
- Wrap the sidebar in `x-data="{ visible: {} }"` and bind `x-model` to series toggle state.
- No other changes to the architecture.

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| uplot@1.6.32 | papaparse@5.5.3 | No shared dependencies; both load via independent script tags. No conflicts. |
| uplot@1.6.32 | alpinejs@3.15.8 | Alpine operates on the DOM; uPlot owns its canvas element; no overlap. |
| papaparse@5.5.3 | All modern browsers (Chrome 90+, Firefox 90+, Edge 90+, Safari 15+) | Uses FileReader API (universal). |
| uplot@1.6.32 | All modern browsers | Canvas 2D API; no IE11 support (not a requirement for this project). |

---

## Sources

- **npm registry** (`registry.npmjs.org`) — uPlot 1.6.32, PapaParse 5.5.3, Alpine.js 3.15.8, ECharts 6.0.0 confirmed [HIGH confidence]
- **uPlot GitHub** (https://github.com/leeoniya/uPlot) — features, limitations, 50 KB bundle size, performance benchmarks (166,650 points in 25 ms) [HIGH confidence]
- **uPlot wheel-zoom demo** (https://leeoniya.github.io/uPlot/demos/zoom-wheel.html) — plugin API verified; middle-click drag + scroll zoom confirmed [HIGH confidence]
- **PapaParse docs** (https://www.papaparse.com/docs) — `delimiter`, `dynamicTyping`, streaming API [HIGH confidence]
- **Apache ECharts GitHub releases** (https://github.com/apache/echarts/releases) — v6.0.0 released July 30, 2024 [HIGH confidence]
- **npm trends** (https://npmtrends.com/chartjs-vs-plotly.js-vs-uplot) — performance benchmarks: uPlot 34 ms, Chart.js 38 ms, Plotly.js 310 ms; Plotly.js 3.6 MB bundle [MEDIUM confidence — snapshot data]
- **WebSearch** — ECharts CDN delivery, Alpine.js CDN pattern, no-build approaches [MEDIUM confidence]

---

*Stack research for: OekoFEN CSV Viewer — client-side time-series chart viewer*
*Researched: 2026-02-17*
