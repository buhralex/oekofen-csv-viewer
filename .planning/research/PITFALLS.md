# Pitfalls Research

**Domain:** Client-side time-series chart viewer for OekoFEN pellet heater CSV data
**Researched:** 2026-02-17
**Confidence:** HIGH (critical pitfalls verified via multiple sources and official docs)

---

## Critical Pitfalls

### Pitfall 1: UTF-8 BOM Corrupts the First Column Header

**What goes wrong:**
The OekoFEN heater exports CSV files that may include a UTF-8 BOM (Byte Order Mark, `\uFEFF`) at the start of the file. When the file is read with `FileReader.readAsText()` defaulting to UTF-8, the BOM is prepended to the first column name. The header `AT [C]` becomes `\uFEFFAT [C]`. All code that looks up this column by exact name will silently fail — the column appears to be missing, returns `undefined`, or the series never renders.

**Why it happens:**
Windows tools (including whatever firmware the OekoFEN heater runs) commonly emit UTF-8-BOM files. The BOM is invisible in most text editors. PapaParse has a known issue (GitHub issue #840, #372) where UTF-8-BOM causes the first property name to be enclosed in an invisible character that breaks normal property access.

**How to avoid:**
After reading the file as `ArrayBuffer`, decode with `TextDecoder` and strip the BOM explicitly before passing to the parser:
```javascript
const decoder = new TextDecoder('utf-8');
let text = decoder.decode(arrayBuffer);
if (text.charCodeAt(0) === 0xFEFF) {
  text = text.slice(1);
}
```
Alternatively, use `FileReader.readAsText(file, 'utf-8')` and strip `\uFEFF` from the result string before parsing. Test with an actual heater-exported file, not a hand-crafted test file.

**Warning signs:**
- First column (date/time or outside temperature `AT [C]`) never appears in the chart
- `console.log(Object.keys(row)[0])` shows a key that looks correct but has length 1 greater than expected
- Charting series tied to the first column silently render empty

**Phase to address:**
CSV parsing phase (Phase 1 / foundation). Write a test that loads a real OekoFEN CSV file and asserts `Object.keys(parsed[0])[0] === 'AT [C]'` (no invisible prefix).

---

### Pitfall 2: German Decimal Commas Are Not Auto-Converted — Silent Wrong Values

**What goes wrong:**
The OekoFEN CSV uses commas as decimal separators (German locale): `23,5` means 23.5 degrees. JavaScript's `parseFloat('23,5')` returns `23` (truncates at the comma). If `dynamicTyping: true` is used in PapaParse, the values are silently parsed as integers. Temperature `23,5°C` becomes `23`, pump modulation `67,3%` becomes `67`. Charts render but show incorrect stepped/truncated data — hard to notice unless you know the expected values.

**Why it happens:**
`parseFloat()` and JavaScript's type coercion are not locale-aware. PapaParse's `dynamicTyping` uses `parseFloat` internally (confirmed in PapaParse GitHub issue #143). Developers test with their own locale and miss the bug.

**How to avoid:**
Never use `dynamicTyping: true` for this CSV. Parse all fields as strings, then apply a locale-aware numeric conversion:
```javascript
function parseGermanFloat(str) {
  if (str === '' || str === null || str === undefined) return null;
  // Replace thousand-separator dots first, then decimal commas
  return parseFloat(str.replace(/\./g, '').replace(',', '.'));
}
```
Apply this transform in a post-processing pass over every column that should be numeric. Validate by asserting a known temperature value from a real file (e.g., outside temp in winter should be a plausible fractional degree, not an integer).

**Warning signs:**
- All temperature and percentage values appear as whole numbers in charts
- The cursor tooltip shows `23` instead of `23.5` for a temperature reading
- Step-like artifacts in otherwise smooth temperature curves

**Phase to address:**
CSV parsing phase (Phase 1). Include a unit test: parse `"23,5"` through the conversion pipeline and assert the result is `23.5`.

---

### Pitfall 3: Timestamp Parsing Shifts by Hours Due to Timezone Interpretation

**What goes wrong:**
The OekoFEN CSV stores timestamps as `DD.MM.YYYY` date and `HH:MM:SS` time in separate columns. When reconstructed into a JavaScript `Date`, the naive approach produces a UTC-interpreted timestamp that shifts all data points by the local UTC offset. A user in UTC+1 (Germany) sees data shifted 1 hour forward; a user in a different timezone sees different shifts. A chart labeled "12:00" shows data that was recorded at 11:00 or 13:00.

**Why it happens:**
Per MDN: date-only ISO strings (e.g., `"2024-01-15"`) are interpreted as UTC midnight. Date-time strings without explicit timezone are interpreted as local time. Reconstructing timestamps from the CSV's `DD.MM.YYYY HH:MM:SS` format without explicit timezone handling means the result depends on the browser's local timezone. The heater data is inherently local time (the heater is in the user's house) but JavaScript `Date` has no notion of "local time without a timezone."

**How to avoid:**
Parse the date and time fields manually and store timestamps as Unix epoch milliseconds (local time relative to midnight, or as a fractional day offset). Do not use `new Date('YYYY-MM-DDTHH:MM:SS')` without explicitly appending a timezone. Since the data is local-time single-day data, the safest approach is to treat timestamps as minutes-since-midnight (a number 0–1439) for all internal chart indexing, and format display labels from the raw time string directly.

**Warning signs:**
- The first data point (00:00:00) appears at a non-zero position on the time axis
- The axis labels show times that are off by a whole number of hours from what the tooltip shows
- The chart looks correct in one timezone but wrong for a user in a different timezone

**Phase to address:**
CSV parsing phase (Phase 1). Charting axis configuration phase. Test by parsing a file and asserting the first row's timestamp maps to `00:00` and the last row's timestamp maps to `23:59`.

---

### Pitfall 4: Mixed Continuous/Discrete Series on the Same Y-Axis Makes Binary States Invisible

**What goes wrong:**
The CSV contains both continuous values (temperatures 0–90°C, percentages 0–100%) and discrete binary states (pump on/off: 0 or 1, status codes: 0–5). When all series share the same auto-scaled Y-axis, the binary state series become a flat line near zero that is visually indistinguishable from zero temperature. Users cannot see pump state changes at all.

**Why it happens:**
Chart libraries auto-scale the Y-axis to fit all visible series. If a boiler temperature of 80°C is visible alongside a pump state of 0 or 1, the axis spans 0–80+ and the binary series occupies only 1/80th of the chart height — effectively invisible. This is not a bug; it is the default correct behavior for a shared axis.

**How to avoid:**
Separate series into axis groups before the charting phase:
- **Left Y-axis:** Temperature values (°C range 0–100)
- **Right Y-axis or overlay band:** Percentage values (0–100%)
- **Step-plot overlay:** Binary states (0/1) rendered as shaded bands or step series on a fixed 0–1 sub-axis

For binary states, use a step-type series (not a line series) and render them as shaded background bands (e.g., a semi-transparent bar when the pump is ON). This communicates state more clearly than a thin line.

**Warning signs:**
- Pump or status series are flat lines at the bottom of the chart regardless of zoom level
- Users report "the pump state doesn't show up"
- Toggling a binary series on/off has no visible effect on the chart

**Phase to address:**
Chart rendering phase (Phase 2 / charting). Must be designed before choosing axis configuration. The parameter view grouping feature (Boiler, Heating Circuit, etc.) should pre-separate continuous vs. discrete series.

---

### Pitfall 5: 70-Series Re-render on Toggle Causes Perceptible Lag

**What goes wrong:**
When a user toggles a single series on or off in a chart with ~70 series, the library re-renders all visible series from scratch. On mid-range hardware this causes 200–800ms of jank per toggle, making the UI feel unresponsive. With animations enabled, this is worse — every toggle triggers a full animation cycle.

**Why it happens:**
Most charting libraries (Chart.js, Plotly) rebuild the entire canvas on any data or visibility change. At 70 series × 1440 points = 100,800 data points being re-rendered, Canvas 2D rendering without GPU acceleration is CPU-bound. Plotly is documented to struggle with performance beyond 10k points with overlays and tooltips (confirmed by SciChart blog comparison).

**How to avoid:**
- **Disable animations immediately** — `animation: false` or equivalent. This is a must, not optional. Re-rendering without animation is 3–5x faster.
- **Use a canvas-based library** — uPlot renders ~100k points at 10% CPU vs. Chart.js at 40% and ECharts at 70% (uPlot GitHub benchmarks).
- **Limit concurrent visible series** — Pre-built views should show only 5–10 relevant series, not all 70 simultaneously.
- **Defer full re-render** — Debounce toggle events by 50ms so rapid toggling of multiple series triggers only one re-render.

**Warning signs:**
- Toggling a series checkbox causes visible freeze of 0.5+ seconds
- Browser DevTools shows long tasks (>50ms) during toggle
- Frame rate drops below 30fps during zoom or pan

**Phase to address:**
Chart rendering phase (Phase 2). Performance benchmark with all 70 series loaded must be run early, before UX polish. If the chosen library fails the benchmark, switch libraries before building features on top of it.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Use `split(';')` for CSV parsing instead of a proper library | No dependency | Fails on quoted fields, BOM, encoding edge cases — requires rewrite for any real OekoFEN file | Never — always use PapaParse or equivalent |
| Enable `dynamicTyping: true` in PapaParse | Fewer lines of code | Silent wrong values for German decimal commas | Never for this CSV format |
| Read file as `readAsText()` without BOM stripping | Simpler code | First column header broken on real heater files | Never — always strip BOM |
| Show all 70 series by default | Seems complete | Unreadable chart, performance problems, overwhelms users | Never — always use pre-built grouped views as default |
| Share one Y-axis for all series | Fewer config lines | Binary states become invisible lines | Never — axis grouping must be designed in from the start |
| Use `new Date(dateString)` directly | Concise code | Timezone-shifted timestamps, subtle off-by-hours bugs | Never — always parse date/time fields manually |
| Leave chart animations enabled | Polished look | Severe performance penalty with 70 series | MVP: disable immediately. Revisit only if library supports partial-series animation |

---

## Integration Gotchas

Common mistakes when connecting to external data sources (the OekoFEN CSV file).

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OekoFEN CSV encoding | Assume UTF-8 without BOM | Read as ArrayBuffer, detect and strip BOM before parsing |
| OekoFEN decimal format | Use JS `parseFloat()` or `dynamicTyping` | Custom `parseGermanFloat()` replacing `,` with `.` after stripping `.` thousand separators |
| OekoFEN timestamp format | Concatenate date+time and pass to `new Date()` | Parse `DD.MM.YYYY` and `HH:MM:SS` manually; store as minutes-since-midnight integer |
| OekoFEN header format | Assume clean ASCII column names | Normalize headers: strip BOM, trim whitespace, preserve brackets (e.g., `AT [C]` is a valid key) |
| OekoFEN status codes | Treat as numeric continuous values | Identify integer-only columns and classify as discrete/categorical before charting |
| File drag & drop | Only handle `drop` event | Must also call `event.preventDefault()` on `dragover` or the browser will navigate to the file |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| All 70 series rendered simultaneously | 500ms+ toggle lag, browser freeze on load | Pre-built views with 5–10 series; toggle adds one at a time | At 20+ series with animations enabled |
| SVG-based charting library | Smooth at 5 series, sluggish at 20+ | Use Canvas 2D (uPlot) or WebGL (LightningChart) | Beyond 10 series, 1440 points each |
| Chart.js `animation: true` with many series | Every data change triggers multi-frame animation cycle | `animation: false` from day one | With 10+ series on update |
| No data decimation during zoom-out | All 1440 points rendered at full density when zoomed out to see only 100px range | Apply LTTB decimation: Chart.js has built-in plugin; uPlot does this automatically | Visible when user zooms out to full-day view with 20+ series |
| Tooltip showing all series values on cursor move | Tooltip renders 70 entries per mousemove, 60x/second | Limit tooltip to 5–10 closest/visible series; use amCharts `maxTooltipDistance` pattern | Any time all 70 series are visible |
| Re-parsing CSV on every chart interaction | 1440 rows × 70 columns re-parsed on series toggle | Parse once on load, store in typed arrays; never re-parse | Immediately noticeable — parse on load only |

---

## UX Pitfalls

Common user experience mistakes in interactive time-series chart viewers.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing all 70 parameters at once with no grouping | Unreadable rainbow spaghetti chart; user cannot find relevant data | Pre-built views grouped by system (Boiler, Heating Circuit, Hot Water, Buffer, Pellet Unit) as primary entry point |
| Zoom resets when toggling a series | User loses their zoom context, has to zoom in again | Preserve zoom state across series visibility changes; only reset on explicit "Reset Zoom" action |
| No "Reset Zoom" affordance | User gets lost after deep zoom, cannot return to full day view | Always-visible "Reset Zoom" button, or double-click to reset |
| Cursor tooltip listing 70 values | Information overload; key values hidden in scroll | Show only values for currently visible series; collapse identical/zero values |
| Using line series for binary on/off states | Pump ON renders as a thin flat line at 1.0 — nearly invisible | Use step-type series + shaded background band for binary states |
| German column names renamed in UI without disambiguation | `HK1 VL Ist[C]` → "Flow Temperature" — user cannot verify which CSV column it is | Show original German CSV column name in tooltip or info panel alongside friendly label |
| Scroll zoom conflicts with page scroll | User tries to scroll down page, accidentally zooms chart instead | Require modifier key (Ctrl/Cmd) for scroll-to-zoom, or confine scroll zoom to within chart bounds with explicit focus |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **CSV parsing:** Visually seems to work — verify that the parsed first header key has no invisible BOM prefix (`key.charCodeAt(0) !== 0xFEFF`)
- [ ] **German decimals:** Chart renders temperatures — verify `23,5` in the source becomes `23.5` in the parsed data, not `23`
- [ ] **Timestamp axis:** Chart shows a time axis — verify the first data point maps to `00:00` and the 1440th maps to `23:59` regardless of the user's system timezone
- [ ] **Binary series visible:** Pump and status series are listed in legend — verify they are visually distinct when the state changes (not a flat invisible line)
- [ ] **Toggle performance:** Series toggle works — verify toggle completes in under 100ms with all 70 series loaded (measure with browser DevTools Performance tab)
- [ ] **Zoom state preserved:** Zoom works — verify toggling a series while zoomed in does not reset the zoom range
- [ ] **File drop on whole page:** Drop zone accepts files — verify that dropping outside the explicit drop zone does not navigate the browser away from the app (requires `dragover` prevention on `document`)
- [ ] **Umlaut headers render:** Parameters like `Außentemperatur` display correctly — verify no mojibake (`Ã¤` instead of `ä`) by loading a real file with umlauts

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| BOM corruption discovered after charting built | LOW | Add one-line BOM strip at file read stage; all downstream code unaffected if keys were normalized |
| German decimal truncation found late | MEDIUM | Replace `dynamicTyping` with a post-parse transform pass; all consumers of parsed data need re-testing |
| Timezone shift discovered in production | MEDIUM | Replace `Date` usage with minutes-since-midnight integers throughout; axis formatting needs update |
| SVG library chosen and found too slow | HIGH | Replace charting library entirely; rebuild series config, zoom plugin, and tooltip integration |
| All-70-series-on-one-axis discovered late | MEDIUM | Axis grouping can be added without data model changes; requires chart config refactor and parameter view redesign |
| Chart animations causing lag found in testing | LOW | Single config change (`animation: false`); no architecture impact |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| BOM corrupts first column header | Phase 1: CSV Parsing | Unit test: parse real OekoFEN file, assert first key has no BOM prefix |
| German decimal commas silently truncated | Phase 1: CSV Parsing | Unit test: `parseGermanFloat("23,5") === 23.5` |
| Timestamp timezone shift | Phase 1: CSV Parsing | Integration test: first row timestamp = 00:00, last = 23:59, timezone-independent |
| Binary states invisible on shared Y-axis | Phase 2: Chart Rendering | Manual review: pump ON/OFF must be visually distinct from flat-zero |
| 70-series toggle performance lag | Phase 2: Chart Rendering | Benchmark: toggle 1 series in 70-series chart completes < 100ms |
| SVG library scale failure | Phase 2: Library Selection | Benchmark before first feature built on top of library |
| Scroll zoom conflicts with page scroll | Phase 3: UX Interactions | Manual test: scrolling the page near the chart does not trigger zoom |
| Tooltip overcrowding | Phase 3: UX Interactions | Manual test: cursor over chart with 10 visible series shows readable tooltip |
| Zoom resets on series toggle | Phase 3: UX Interactions | Test: zoom to a 1-hour window, toggle any series, verify zoom range unchanged |
| File drop navigates browser away | Phase 1: File Loading | Test: drop file outside drop zone, browser stays on app page |

---

## Sources

- [PapaParse GitHub Issue #840 — UTF-8-BOM string parsing corrupts first header](https://github.com/mholt/PapaParse/issues/840)
- [PapaParse GitHub Issue #372 — Unicode BOM messes up first property name](https://github.com/mholt/PapaParse/issues/372)
- [PapaParse GitHub Issue #143 — Numeric value with comma (European-formatted numbers)](https://github.com/mholt/PapaParse/issues/143)
- [uPlot GitHub — Performance benchmarks vs Chart.js and ECharts](https://github.com/leeoniya/uPlot)
- [Chart.js Performance Documentation — Decimation and animation flags](https://www.chartjs.org/docs/latest/general/performance.html)
- [MDN Date.parse() — UTC vs local time interpretation for date-only strings](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/parse)
- [SciChart Blog — Most charting libraries break at scale (Chart.js vs ECharts CPU/memory benchmarks)](https://www.scichart.com/blog/scale-up-with-high-performance-charting-library/)
- [amCharts Cursor Documentation — maxTooltipDistance for many-series tooltip control](https://www.amcharts.com/docs/v5/charts/xy-chart/cursor/)
- [CSVBox Blog — CSV encoding detection, BOM vs non-BOM accuracy](https://blog.csvbox.io/csv-detect-encoding/)
- [Chrome Developers — ArrayBuffer to String via TextDecoder encoding API](https://developer.chrome.com/blog/easier-arraybuffer-string-conversion-with-the-encoding-api)
- [Phare.io — Downsampling time series data, LTTB algorithm explained](https://phare.io/blog/downsampling-time-series-data/)
- [Chart.js Data Decimation Configuration — LTTB built-in support](https://www.chartjs.org/docs/latest/samples/advanced/data-decimation)
- [Grafana Documentation — Mixed time series data visualization, dual-axis guidance](https://grafana.com/docs/grafana/latest/visualizations/panels-visualizations/visualizations/time-series/)
- [SciChart Memory Best Practices — Destroy patterns for canvas-based charts](https://www.scichart.com/documentation/js/current/MemoryBestPractices.html)

---
*Pitfalls research for: Client-side time-series chart viewer (OekoFEN CSV)*
*Researched: 2026-02-17*
