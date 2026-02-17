# Feature Research

**Domain:** Interactive time-series chart viewer for sensor/IoT diagnostic data
**Researched:** 2026-02-17
**Confidence:** HIGH (table stakes confirmed across Grafana, ThingsBoard, SciChart, amCharts docs; differentiators from community patterns and domain analysis)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist in any interactive time-series viewer. Missing these causes the tool to feel broken or unfinished — users will not stay.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Drag-and-drop file load | Entry pattern for local-file tools; removing friction is non-negotiable | LOW | Also provide file picker as fallback for accessibility |
| CSV parse with correct locale | German decimals (comma) and semicolon delimiter are the data format; wrong parse = garbage chart | LOW | Must handle `1,5` as `1.5`; headers with units like `AT [C]` |
| Render line chart for selected columns | Core output of the tool; without this nothing else works | MEDIUM | ~1440 pts x 70 cols; Canvas-based rendering required for performance |
| X-axis as time (HH:MM) | Users reason about "what happened at 14:00"; numeric index is useless | LOW | Parse `DD.MM.YYYY HH:MM:SS` timestamps |
| Show/hide individual series | 70 columns cannot be shown simultaneously; selection is mandatory | LOW | Toggle via legend click; standard in all charting libraries |
| Pre-built parameter groups | "Boiler view", "Heating circuit view" etc. — users should not have to manually select 5 columns to see a coherent picture | MEDIUM | Requires understanding column semantics; one-time mapping effort |
| Zoom: click-drag range select | Standard interaction; users expect to draw a box or drag to zoom into an event | LOW | All major chart libs support this natively |
| Zoom: scroll wheel (centered on cursor) | Quick zoom without precise selection; essential for navigating a 24-hour view | LOW | Must center on cursor, not chart center — that's the expected UX |
| Reset to full day view | After zooming, users must be able to get back; double-click or a button | LOW | Double-click to zoom out is Grafana standard |
| Cursor inspection (crosshair + tooltip) | Users need exact values at a point in time to diagnose "what was the boiler temp when the pump fired?" | MEDIUM | Vertical crosshair snapping to nearest data point; tooltip showing all visible series values |
| Responsive to window size | Tool must work at various browser window sizes without breaking | LOW | Canvas must resize; no fixed pixel widths |

### Differentiators (Competitive Advantage)

Features that generic chart viewers do not provide out of the box for this specific use case. These are where the tool earns its keep against "just use Grafana."

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Semantic column grouping (Boiler/HK1/WW1/PE1) | OekoFEN columns have a naming convention; auto-grouping by prefix (`HK1`, `WW1`, `PE1`) makes it immediately navigable without reading the CSV header | LOW | Regex on column names; one-time classification logic |
| Dual-axis rendering (temperatures + binary states on same chart) | Pump on/off (0/1) overlaid on a temperature curve answers "did the pump fire when the boiler hit setpoint?" — this is the core diagnostic question | MEDIUM | Right Y-axis for 0/1 signals; left for temperatures; visual styling difference (dashed line or step chart for binary) |
| Step-interpolation for discrete/binary columns | Pump states and mode codes should render as steps, not interpolated lines — interpolation is actively misleading for on/off data | LOW | Per-column interpolation mode; detect or let user set |
| Overview / minimap (context window) | Full-day view at bottom so user can see where in the day they are while zoomed into an event | MEDIUM | Requires secondary chart or brush widget synced to main chart; uPlot supports this pattern |
| Keyboard zoom/pan | Arrow keys to pan, +/- to zoom; allows fine-grained navigation during diagnosis without mouse | LOW | Improves diagnostic workflow significantly |
| Column name cleanup display | Show `HK1 VL Ist [C]` as a readable label `HK1 Supply Actual (°C)` while preserving the raw name | LOW | Mapping table; toggle between raw and friendly names |
| Load state persistence (last file, visible series) | User reloads page after refreshing browser; restore which columns were visible | MEDIUM | localStorage for series visibility and zoom state; requires serializing column selection |
| Direct URL / file param via query string | Power users who have a workflow can automate opening a specific file path — but this is client-side so it is scoped to re-open last file | LOW | `?restore=last` pattern; not full URL-to-file (security limitation) |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem natural to request but would cost disproportionate implementation time relative to their diagnostic value, or actively make the tool worse for its specific purpose.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Multi-file comparison (load two CSVs) | "Compare today with yesterday" sounds useful | Doubles the state complexity: two parse pipelines, alignment of timestamps, visual clutter. Out of scope in PROJECT.md. Adds weeks of complexity for a rarely needed operation | Note the date in the filename (`touch_YYYYMMDD.csv`) in the UI; user can open two browser tabs |
| Real-time streaming from heater | "Why not connect directly?" | Requires a local server or WebSocket proxy — violates the client-side-only constraint. Is a completely different product | Keep as static file viewer; heater exports CSV daily anyway |
| Data editing / annotation saving | "Let me mark events on the chart" | Annotations need persistence. localStorage is fragile; file export adds complexity; annotations on client CSV data with no server means no sharing | Provide clipboard copy of values at cursor; user can note timestamps manually |
| AI/ML anomaly detection | "Flag unusual temperatures automatically" | Domain-specific heating behavior is complex (boiler temp dips during pellet loading are normal); false positives erode trust; adds model dependency | Let diagnostic UI show the data clearly; human interprets |
| Custom chart types (bar, pie, heatmap) | "Can I see a pie chart of mode distribution?" | Pie/bar charts for time-series data hide temporal relationships — the wrong tool for diagnosing when something happened | Stick to line/step charts; time-axis is the diagnostic lens |
| Alert thresholds / notifications | "Notify me if boiler exceeds X°C" | Static file viewer has no real-time trigger; implementing requires a background process; scope creep toward a monitoring product | Out of scope; use heater's own alarm system |
| Export to PDF or image | "I want to share this chart" | Adds canvas-to-image plumbing; browser screenshot (Ctrl+Shift+S) handles 95% of use cases for a personal diagnostic tool | Document that browser screenshot is the intended share mechanism |
| User accounts / login | "Save my configurations" | No server; localStorage is sufficient for a single-user personal tool | Use localStorage for all persistence |
| Column unit conversion (°C to °F) | "I prefer Fahrenheit" | The OekoFEN target user is European; adds UI complexity and potential confusion when reading raw parameter names | Display units as-is from CSV headers |

---

## Feature Dependencies

```
[File Load: drag-drop / picker]
    └──required-by──> [CSV Parse (locale-aware)]
                          └──required-by──> [Column Discovery & Grouping]
                                                └──required-by──> [Pre-built Views]
                                                └──required-by──> [Show/Hide Series]
                                                                      └──required-by──> [Line Chart Render]
                                                                                            └──required-by──> [Zoom: drag-range]
                                                                                            └──required-by──> [Zoom: scroll-wheel]
                                                                                            └──required-by──> [Cursor Inspection]
                                                                                            └──required-by──> [Reset Zoom]

[Line Chart Render]
    └──enables──> [Dual Y-Axis (temp + binary)]
    └──enables──> [Step Interpolation for binary columns]
    └──enables──> [Overview / Minimap]

[Cursor Inspection]
    └──enhances──> [Dual Y-Axis] (shows values for both axes simultaneously)

[Pre-built Views]
    └──enhances──> [Semantic Column Grouping]

[Column Name Cleanup]
    └──optional-enhancement-to──> [Show/Hide Series legend]
    └──optional-enhancement-to──> [Cursor Inspection tooltip]

[Load State Persistence]
    └──depends-on──> [Show/Hide Series] (what to persist)
    └──depends-on──> [Pre-built Views] (which view was active)
```

### Dependency Notes

- **CSV Parse requires File Load:** Parse cannot start without a file; both are Phase 1 foundations.
- **Column Discovery requires Parse:** Grouping logic reads parsed headers; pre-built views cannot exist without column names.
- **Chart Render requires Show/Hide:** The render layer must know which series are visible; show/hide is the control surface, not an add-on.
- **Zoom requires Chart Render:** Both zoom modes are interactions on the rendered canvas; they cannot be added before rendering exists.
- **Dual Y-Axis enhances Line Chart Render:** It is not a prerequisite for basic rendering, but requires the charting lib to support multiple y-axes configured at init time. Plan for it early even if implemented later.
- **Step Interpolation enhances Render:** Requires per-column metadata (is this binary?) available at render time. Detect at parse time (column has only 0/1 values) or let user toggle.
- **Load State Persistence is standalone:** No other feature depends on it; add post-MVP without touching core pipeline.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — what delivers the core diagnostic value: "zoom into an event and see what was happening."

- [ ] File load via drag-and-drop and file picker — entry point to everything
- [ ] CSV parse: semicolon delimiter, German decimal (comma), timestamp parsing (`DD.MM.YYYY HH:MM:SS`), ~70 column headers
- [ ] Line chart render of visible series against time axis (HH:MM)
- [ ] Pre-built parameter groups (Boiler, HK1, WW1, PU1, PE1) as one-click views
- [ ] Show/hide individual series via legend click
- [ ] Zoom via click-drag range selection
- [ ] Zoom via scroll wheel centered on cursor
- [ ] Reset zoom to full day
- [ ] Cursor crosshair with tooltip showing values of all visible series at cursor position
- [ ] Step rendering for binary/discrete columns (pump states, mode codes)

### Add After Validation (v1.x)

Add once v1 is in use and core interactions are validated.

- [ ] Dual Y-axis (temperatures left, binary states right) — trigger: users report confusion about scale when mixing temp and binary columns
- [ ] Overview/minimap (context brush) — trigger: users report losing spatial context while zoomed in
- [ ] Keyboard zoom/pan — trigger: power user feedback on fine-grained navigation
- [ ] Friendly column name display (with toggle to raw) — trigger: German parameter names cause confusion

### Future Consideration (v2+)

Defer until core is stable and there is clear user demand.

- [ ] Load state persistence (localStorage) — personal tool, low friction to re-select
- [ ] Custom column selection beyond pre-built views — defer until pre-built views prove insufficient
- [ ] Semantic column auto-detection refinement — requires real-world column name corpus beyond the single known CSV format

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| File load (drag-drop + picker) | HIGH | LOW | P1 |
| CSV parse (locale + timestamps) | HIGH | LOW | P1 |
| Line chart render | HIGH | MEDIUM | P1 |
| Pre-built parameter groups | HIGH | MEDIUM | P1 |
| Show/hide series | HIGH | LOW | P1 |
| Zoom: drag range | HIGH | LOW | P1 |
| Zoom: scroll wheel | HIGH | LOW | P1 |
| Reset zoom | HIGH | LOW | P1 |
| Cursor inspection + tooltip | HIGH | MEDIUM | P1 |
| Step rendering for binary cols | MEDIUM | LOW | P1 |
| Dual Y-axis | HIGH | MEDIUM | P2 |
| Overview/minimap | MEDIUM | HIGH | P2 |
| Keyboard zoom/pan | MEDIUM | LOW | P2 |
| Friendly column names | MEDIUM | LOW | P2 |
| Load state persistence | LOW | MEDIUM | P3 |
| Custom column selection UI | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

Competitors are general-purpose time-series viewers — Grafana, ThingsBoard, and the existing OekoFEN static PNG — rather than domain-specific products. The OekoFEN heater produces static PNG overlays of all parameters, which is what this tool replaces.

| Feature | Grafana | ThingsBoard | OekoFEN static PNG | Our Approach |
|---------|---------|-------------|-------------------|--------------|
| File drag-drop load | No (server data sources) | No (server data sources) | No (generated by heater) | Yes — core differentiator for client-only |
| Pre-built domain views | Generic dashboards only | Generic templates | Fixed, shows everything | Domain-specific groups by heater subsystem |
| Step interpolation for binary | Manual per-series config | Not documented | Shows as line | Auto-detect and render as step chart |
| Dual Y-axis | Supported | Supported | Not applicable | Supported, with binary on right axis |
| Overview/minimap | Supported (timeline) | Not standard | Not applicable | Supported via brush widget |
| Zoom/pan | Full support | Full support | Not applicable | Full support |
| Cursor inspection | Full support | Full support | Not applicable | Full support |
| Client-side only | No | No | N/A | Yes — required constraint |

---

## Sources

- Grafana time series panel documentation: https://grafana.com/docs/grafana/latest/visualizations/panels-visualizations/visualizations/time-series/
- Grafana time range pan and zoom (Jan 2026): https://grafana.com/whats-new/2026-01-15-time-range-pan-and-zoom/
- ThingsBoard time series chart features: https://thingsboard.io/blog/enhancing-iot-data-visualization-introducing-new-time-series-charts/
- SciChart cross-chart synchronization (crosshair, zoom, pan): https://www.scichart.com/blog/how-to-link-javascript-charts-and-synchronise-zooming-panning-crosshairs/
- amCharts cursor documentation: https://www.amcharts.com/docs/v5/charts/xy-chart/cursor/
- uPlot (small, fast time-series canvas chart): https://github.com/leeoniya/uPlot
- IoT data visualization overview: https://www.influxdata.com/how-to-visualize-time-series-data/
- FusionCharts zoom/scroll/pan features: https://www.fusioncharts.com/features/zooming-and-scrolling
- CSV import UX patterns (drag-drop, validation): https://www.smashingmagazine.com/2020/12/designing-attractive-usable-data-importer-app/
- OekoFEN CSV Viewer PROJECT.md (project constraints and requirements): .planning/PROJECT.md

---
*Feature research for: Interactive time-series chart viewer for OekoFEN pellet heater diagnostic data*
*Researched: 2026-02-17*
