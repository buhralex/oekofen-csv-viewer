# Project Research Summary

**Project:** OekoFEN CSV Viewer
**Domain:** Client-side time-series chart viewer for pellet heater diagnostic data
**Researched:** 2026-02-17
**Confidence:** HIGH

## Executive Summary

The OekoFEN CSV Viewer is a browser-only diagnostic tool that replaces the heater's static PNG output with an interactive time-series chart. Experts build this class of tool as a single distributable HTML file — no server, no build pipeline, no framework — using a purpose-built Canvas charting library (uPlot) and a reliable CSV parser (PapaParse). The delivery constraint (open from filesystem, no CDN required) shapes every technology decision: both libraries are vendored locally, the application glue is vanilla ES2020 JavaScript, and all state lives in a simple central object rather than a reactive framework. This is a well-understood domain with established patterns; the research finds no exotic unknowns.

The recommended architecture is a strict one-way data pipeline: File drop → CSV parse → German-locale normalization → columnar data model → view-driven series selection → uPlot render. The single highest-risk component is the normalizer, which must handle three known OekoFEN-specific quirks simultaneously: UTF-8 BOM on the first header, comma decimal separators, and date/time split across two columns. If the normalizer is wrong, every downstream phase is wrong. Build and test it against a real heater file before writing any charting code.

The primary UX challenge is that the CSV contains ~70 columns mixing continuous values (temperatures, percentages) and discrete binary states (pump on/off, mode codes). Showing all 70 simultaneously produces an unreadable chart and measurable performance lag. The correct mitigation — pre-built views grouped by heater subsystem (Boiler, HK1, WW1, PE1, Buffer) — is both the key differentiator over generic tools like Grafana and the architectural guard against the shared-axis visibility problem for binary states. These two concerns must be resolved together in Phase 1, not retrofitted.

## Key Findings

### Recommended Stack

The stack is intentionally minimal. uPlot 1.6.32 is the clear choice for the charting engine: it is Canvas-based (~50 KB), renders 166,650 points in 25 ms, ships with an IIFE build for script-tag delivery, and provides native cursor sync, zoom hooks, and plugin patterns. No other library at comparable size delivers this combination for time-series line charts. PapaParse 5.5.3 handles CSV parsing — it is the de-facto standard, handles quoted fields, mixed line endings, and BOM recovery — but `dynamicTyping` must be disabled for German locale data. The wheel-zoom/pan plugin (~80 lines) is copied inline from the official uPlot demo and requires no separate package.

**Core technologies:**
- **uPlot 1.6.32**: Chart rendering — only Canvas-based library at this scale with native zoom/cursor hooks and no build step requirement
- **PapaParse 5.5.3**: CSV parsing — handles BOM, quoted fields, mixed line endings; `dynamicTyping: false` is mandatory for German locale
- **Vanilla JS (ES2020+)**: Application glue — no framework needed; FileReader API is sufficient; keeps deliverable as a single directory of files
- **uPlot wheel-zoom plugin (inline)**: Scroll zoom + pan — copy from official demo, no package needed

**What not to use:** React/Vue/Svelte (require build step), Plotly.js (3.6 MB, 310 ms render), D3.js (low-level primitives, not a charting library), Moment.js (deprecated), Chart.js (heavier, slower, worse for time-series at this scale).

### Expected Features

The feature set divides cleanly into a core diagnostic pipeline (all P1 for v1) and usability enhancements (P2 for v1.x).

**Must have (table stakes):**
- Drag-and-drop file load + file picker fallback — entry point to everything
- CSV parse: semicolon delimiter, German decimal (comma → period), `DD.MM.YYYY HH:MM:SS` timestamp parsing
- Line chart render of selected series against a time axis (HH:MM display)
- Pre-built parameter groups by heater subsystem (Boiler, HK1, WW1, Buffer, PE1) — one-click coherent view
- Show/hide individual series via legend click
- Zoom via drag-range and scroll wheel (cursor-centered)
- Reset zoom to full day (double-click or button)
- Cursor crosshair with tooltip showing values of all visible series
- Step rendering for binary/discrete columns (pump states, mode codes)

**Should have (competitive differentiators):**
- Dual Y-axis: temperatures on left, binary states on right — prevents binary series invisibility
- Overview/minimap (context brush) — spatial orientation while zoomed
- Keyboard zoom/pan — fine-grained navigation for power users
- Friendly column name display with toggle to raw CSV name

**Defer (v2+):**
- Load state persistence (localStorage) — personal tool, low re-selection friction
- Custom column selection UI beyond pre-built views
- Multi-file comparison — doubles state complexity, out-of-scope constraint

**Anti-features to reject:** Real-time streaming (violates client-only constraint), data annotation saving (no server), AI anomaly detection (domain-complex, trust-eroding), user accounts (localStorage sufficient), PDF export (browser screenshot handles the use case).

### Architecture Approach

The application follows a strict one-way pipeline through five layers: UI Shell (drag-drop, tab bar, control bar) → App State Store (plain JS object with setter functions) → Data Pipeline (PapaParse → Normalizer → Columnar Data Model) → View Manager (preset name to column list) → Chart Layer (uPlot instance + zoom/cursor plugins). No component writes upstream; the chart never reads from the data model directly; UI components never touch the chart renderer directly. This design makes every bug locatable to exactly one stage.

**Major components:**
1. **CSV Parser + Normalizer** — highest-risk; handles BOM, German decimals, timestamp reconstruction; must be verified with real heater file before charting begins
2. **Data Model** — columnar Float32Arrays per column, computed once at load, never re-parsed; `Int32Array` for timestamps
3. **View Manager** — maps preset names to column lists; the UX mechanism that prevents 70-series overload
4. **Chart Renderer** — uPlot lifecycle wrapper; creates instance once per file load; uses `setData()`, `setSeries()`, `setScale()` for updates — never recreates the instance for zoom or toggle operations
5. **UI Components** — each owns one surface; dispatch to app.js state setters only; never touch the model or renderer directly

**Build order mandated by dependencies:** Parser → Normalizer → Data Model → View Definitions → Series Builder → Chart Renderer → Plugins → UI Components → App Shell → Integration test.

### Critical Pitfalls

1. **UTF-8 BOM corrupts the first column header** — The heater emits BOM-prefixed files; PapaParse makes the first key `\uFEFFAT [C]` instead of `AT [C]`, silently breaking all lookups. Fix: read as `ArrayBuffer`, decode with `TextDecoder`, strip `charCodeAt(0) === 0xFEFF` before parsing. Test: assert first parsed key has no invisible prefix using a real heater file.

2. **German decimal commas are silently truncated to integers** — `parseFloat('23,5')` returns `23`; `dynamicTyping: true` does the same. Fix: never use `dynamicTyping`; apply a custom `parseGermanFloat()` (replace `.` thousand separators, then `,` decimal) in the Normalizer. Test: `parseGermanFloat('23,5') === 23.5`.

3. **Timestamp timezone shift makes data appear offset by hours** — `new Date('DD.MM.YYYY HH:MM:SS')` interprets ambiguous strings relative to browser timezone. Fix: parse date and time fields manually; store as minutes-since-midnight integer (0–1439); format display labels from raw time string. Test: first timestamp → `00:00`, last → `23:59`, independent of system timezone.

4. **Binary states invisible on shared Y-axis** — Pump on/off (0/1) alongside boiler temp (80°C) means the Y-axis spans 0–80; binary series flatten to a 1/80th-height line. Fix: separate series into axis groups at design time; binary states get a dedicated step-series with shaded band rendering on a fixed 0–1 sub-axis. Must be designed before the chart layer, not retrofitted.

5. **70-series toggle causes perceptible lag** — With animations enabled, full re-render at 70 series × 1440 points causes 200–800 ms jank. Fix: disable animations from day one (`animation: false` equivalent in uPlot config); use pre-built views to limit visible series to 5–10; uPlot handles the rendering CPU load far better than Chart.js or Plotly. Benchmark with all 70 series loaded before building UX on top.

## Implications for Roadmap

Based on research, the dependency graph and pitfall phase mapping converge on a 4-phase structure.

### Phase 1: Foundation — File Loading and Data Pipeline

**Rationale:** Every other phase depends on correctly parsed, normalized data. The normalizer is the highest-risk component in the entire project; the three locale-specific pitfalls (BOM, German decimals, timezone) all live here. No charting phase can be trusted until this phase is verified against a real OekoFEN CSV file.

**Delivers:** A working parse-to-model pipeline: drag-drop file load → BOM-stripped UTF-8 reading → PapaParse (semicolon delimiter, `dynamicTyping: false`) → German decimal normalization → manual timestamp reconstruction → columnar Float32Array data model. Also delivers the view definition map (preset name → column list) because column names are known only after parse.

**Addresses:** File load (drag-drop + picker), CSV parse (locale-aware), column discovery, pre-built view definitions (Boiler, HK1, WW1, Buffer, PE1 column lists defined as data).

**Avoids:** BOM corruption (Pitfall 1), German decimal truncation (Pitfall 2), timezone shift (Pitfall 3), re-parsing on interaction (performance trap).

**Verification gates before proceeding:** Unit tests for `parseGermanFloat`, BOM stripping, and timestamp parsing against a real heater file. The first parsed header key must equal `'AT [C]'` exactly.

### Phase 2: Chart Rendering and Axis Architecture

**Rationale:** Charting must be architected with dual-axis and binary-state rendering in mind from the start — these cannot be retrofitted without a chart config rewrite. This phase also serves as the library validation gate: if uPlot performs unacceptably on the actual dataset, the library must be swapped here before features are built on top.

**Delivers:** A working uPlot instance rendering the active view's series. Includes columnar-to-uPlot series builder, chart renderer lifecycle (create/setData/setSeries/setScale, no recreate-on-toggle), axis architecture (left axis for temperatures, right/overlay for binary states), step rendering for detected binary columns, and the wheel-zoom plugin inlined from the official demo.

**Uses:** uPlot 1.6.32 (vendored), Series Builder, Data Model column arrays, View Manager for initial series selection.

**Implements:** Chart Renderer, Series Builder, zoom plugin, cursor/crosshair plugin.

**Avoids:** Rebuild-on-toggle anti-pattern, row-oriented rendering anti-pattern, binary state invisibility (Pitfall 4), 70-series render lag (Pitfall 5), animations enabled by default.

**Verification gate:** Benchmark toggle latency with all 70 columns loaded — must complete under 100 ms. Binary pump series must be visually distinct when state changes.

### Phase 3: Interactive Controls and UX

**Rationale:** With a verified data pipeline and chart renderer, UX interactions are low-risk additions. Drag zoom, scroll zoom, and cursor inspection all attach via uPlot hooks — isolated from data logic. This phase also wires the pre-built view tabs and series checkboxes into the state store.

**Delivers:** Full interactive experience: drag-range zoom, scroll-wheel zoom centered on cursor, reset zoom (button + double-click), cursor crosshair with tooltip (visible series only), view tab switching (Boiler / HK1 / WW1 / Buffer / PE1), series show/hide checkboxes, zoom state preserved across series toggles.

**Avoids:** Scroll-zoom conflicting with page scroll (require chart focus or Ctrl modifier), tooltip overcrowding (limit to visible series), zoom reset on toggle (use `setSeries()` not recreate).

**Verification gates:** Scroll page near chart does not trigger zoom; toggle series while zoomed — zoom range unchanged; cursor tooltip readable with 10 visible series.

### Phase 4: Polish and v1.x Enhancements

**Rationale:** These features add value but have no dependency predecessors — they can be added or deferred without affecting core functionality. Add based on user feedback after Phase 3 is validated.

**Delivers:** Dual Y-axis for temperature/binary separation (if not fully implemented in Phase 2), overview/minimap brush widget, keyboard zoom/pan (arrow keys + +/-), friendly column name display with toggle to raw name, responsive resize behavior, UX edge cases (drop outside zone does not navigate, Umlaut header display).

**Note:** Dual Y-axis may partially overlap with Phase 2 depending on implementation approach — plan for it in Phase 2 axis configuration even if visual polish is deferred.

### Phase Ordering Rationale

- **Phase 1 before everything:** All pitfalls that can invalidate downstream work live in the parse/normalize layer. Research explicitly flags this as "test with a real OekoFEN file before building the chart layer."
- **Phase 2 before Phase 3:** Chart interactions (zoom, cursor) require a uPlot instance to exist; plugins attach via hooks at instantiation. The axis architecture decision (dual-axis, binary step rendering) must precede the series builder, not follow it.
- **Phase 4 last:** No other phase depends on polish features; they are additive and isolated.
- **Pre-built views straddle Phase 1 and Phase 2:** Column group definitions belong in Phase 1 (they are data, derived from the parsed headers), but the view tab UI and switching belongs in Phase 3.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 — Chart Axis Architecture:** The exact uPlot multi-axis configuration for mixing continuous and binary series is non-trivial. The uPlot docs cover dual-axis but the binary-overlay pattern (shaded bands vs. step series on secondary axis) may need prototyping. Recommend a `/gsd:research-phase` pass focused specifically on uPlot multi-axis and binary series rendering before writing the series builder.
- **Phase 1 — Timestamp Format Validation:** The exact column names and timestamp format in the actual OekoFEN CSV are assumed from the project description. If the real file differs (e.g., timestamp in one column vs. two, or Unix epoch instead of `DD.MM.YYYY`), the normalizer design changes significantly. Validate against a real file on day one.

Phases with standard patterns (skip research-phase):
- **Phase 3 — Interactive Controls:** uPlot zoom/cursor hooks are well-documented in the official repo and demos; the wheel-zoom plugin is copy-pasteable. No novel integration.
- **Phase 4 — Polish:** All features are standard browser patterns (localStorage, keyboard events, CSS responsive layout).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | uPlot, PapaParse verified via npm registry, official GitHub, and live demos; version compatibility confirmed; alternatives benchmarked with data |
| Features | HIGH | Table stakes confirmed across Grafana, ThingsBoard, amCharts docs; domain analysis of OekoFEN use case is solid; MVP boundary is clearly reasoned |
| Architecture | HIGH | One-way pipeline and columnar data patterns are established; uPlot hook/plugin API verified in official docs; anti-patterns confirmed via PapaParse issue tracker |
| Pitfalls | HIGH | BOM and decimal issues confirmed via official PapaParse GitHub issues (#143, #372, #840); timezone behavior confirmed via MDN; performance benchmarks from uPlot GitHub |

**Overall confidence:** HIGH

### Gaps to Address

- **Actual OekoFEN CSV schema:** Research assumes ~70 columns, semicolon delimiter, German decimals, `DD.MM.YYYY` + `HH:MM:SS` split across two columns, UTF-8 BOM. If the real file differs in any of these respects, normalizer design changes. Validate on day one of Phase 1 with a real exported file. Do not build the normalizer against a hand-crafted test fixture.
- **Column name corpus for semantic grouping:** The pre-built view definitions (Boiler, HK1, WW1, Buffer, PE1 → column list mappings) require knowing the actual column names. Research used naming patterns from the project description. The real column names must be extracted from an actual CSV before view definitions can be coded. This is a Phase 1 deliverable, not a Phase 3 addition.
- **Alpine.js threshold:** Research flags Alpine.js as appropriate if 70-checkbox DOM manipulation becomes unwieldy in vanilla JS. There is no firm rule for when to add it. Plan for it as a Phase 3 or 4 addition if paramPanel.js grows beyond ~150 lines of DOM manipulation.
- **Day.js necessity:** Whether Day.js is needed depends on the exact timestamp format in the real CSV. If timestamps are already Unix epoch integers, Day.js is unnecessary. Decide in Phase 1 after examining a real file.

## Sources

### Primary (HIGH confidence)

- **uPlot GitHub** (https://github.com/leeoniya/uPlot) — features, bundle size, performance benchmarks, plugin API, zoom demo
- **uPlot docs/README.md** (https://github.com/leeoniya/uPlot/blob/master/docs/README.md) — columnar format, scales, series, hooks
- **PapaParse official docs** (https://www.papaparse.com/docs) — delimiter, header, dynamicTyping, File object API
- **PapaParse GitHub Issue #143** — numeric comma (German decimal) not handled by dynamicTyping
- **PapaParse GitHub Issue #372** — BOM corrupts first property name
- **PapaParse GitHub Issue #840** — UTF-8-BOM string parsing corrupts first header
- **MDN Date.parse()** — UTC vs local time interpretation for date-only strings
- **npm registry** — uPlot 1.6.32, PapaParse 5.5.3, Alpine.js 3.15.8, ECharts 6.0.0 confirmed

### Secondary (MEDIUM confidence)

- **Grafana time series panel docs** — feature expectations for interactive chart viewers
- **ThingsBoard time series chart docs** — IoT viewer feature baseline
- **amCharts cursor docs** — tooltip distance limiting pattern
- **uPlot DeepWiki** (https://deepwiki.com/leeoniya/uPlot) — architecture overview
- **npm trends** — uPlot 34 ms, Chart.js 38 ms, Plotly.js 310 ms render benchmarks (snapshot data)
- **Chart.js performance docs** — decimation and animation flags
- **SciChart blog** — charting library scale benchmarks (CPU/memory)

### Tertiary (LOW confidence)

- **Vanilla JS state management patterns 2026** (medium.com blog) — state store patterns for no-framework apps; single source, used only to validate vanilla approach
- **AWS Synchro Charts blog** — reference architecture for time-series viewer component structure

---
*Research completed: 2026-02-17*
*Ready for roadmap: yes*
