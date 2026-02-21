# Phase 1: Foundation - Research

**Researched:** 2026-02-17
**Domain:** Single-file web app; CSV parsing (semicolon-delimited, ISO-8859-1, German locale); drag-and-drop file loading; in-memory columnar data model
**Confidence:** HIGH (verified against real CSV file + official docs)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Drop zone appearance**
- Claude decides landing page layout (full-page drop zone vs compact)
- Claude decides theme (dark vs light) — optimize for chart readability
- Drag-over visual feedback is required: highlight the drop zone when a file is being dragged over the page
- After file loads, drop zone collapses to a compact header bar showing filename + "Load another" option
- The chart area takes over the main viewport after loading

**Error feedback**
- Wrong file type: toast notification that auto-dismisses after a few seconds
- If user drops a .png image: show specific message "This is a graph image. Drop the CSV file (touch_*.csv) instead"
- Non-OekoFEN CSV: warn "This doesn't look like OekoFEN data" but proceed with parsing anyway
- Parse errors (unparseable values): skip the bad values (treat as null/gap in chart), show count in status bar: "3 rows had parse issues"
- Only accept .csv files as valid input; all other file types get a toast error

**Post-load experience**
- Show a data summary after successful load: file date and name, row & column counts, time range, column groups found with counts
- Claude decides whether summary is a standalone screen or compact info bar
- When loading a new file (replacing current), keep the current view settings (don't reset to defaults)

**Column grouping rules**
- Prefix-based auto-grouping:
  - **Boiler**: AT, ATakt, KT (Ist/Soll), BR (burn status 0/1), Sperrzeit (lock boolean), PE1_BR1
  - **Heating Circuit (HK1)**: all columns starting with `HK1`
  - **Hot Water (WW1)**: all columns starting with `WW1`
  - **Buffer (PU1)**: all columns starting with `PU1`
  - **Pellet Unit (PE1)**: all columns starting with `PE1` (kept as one group, ~30 columns)
- Datum and Zeit are timestamp columns — used for the X-axis, not selectable as chart parameters
- Fehler1/2/3 (error columns): ignored for now — not shown in any pre-built view
- Zubrp1 Pumpe: ignored for now
- BR is a binary column (1=burning, 0=off) — must be classified as discrete/step for chart rendering
- Sperrzeit is a binary column (1=blocked, 0=allowed) — same treatment as BR
- PE1 group stays as one group (not split into sub-groups)

### Claude's Discretion
- Landing page layout and visual design
- Theme choice (dark vs light)
- Data summary layout (standalone vs info bar)
- Exact toast notification styling and timing
- Column ignore/configuration mechanism (if implemented)

### Deferred Ideas (OUT OF SCOPE)
- Column ignore/config file (.ignore or JSON) to disable columns by default — could be Phase 4 (parameter management) or a simple v1.x addition
- Fehler (error) column visualization — future phase or v2
- Zubrp1 Pumpe handling — future investigation
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LOAD-01 | User can load a CSV file via drag-and-drop onto the page | MDN Drag and Drop File API: use `dragover`+`drop` on drop zone, `preventDefault()` on both events |
| LOAD-02 | User can load a CSV file via a file picker button | `<input type="file" accept=".csv">` with `change` event; or programmatic `click()` on hidden input |
| LOAD-03 | Dropping a file outside the drop zone does not navigate the browser away | Window-level `dragover` + `drop` with `preventDefault()` guards against browser navigation |
| PARS-01 | Parser handles semicolon-delimited CSV format | PapaParse `delimiter: ";"` config option |
| PARS-02 | Parser converts German locale decimals (comma separator) to correct numeric values | PapaParse `transform` callback: `val.replace(',', '.')` then `parseFloat` |
| PARS-03 | Parser strips UTF-8 BOM from file start without corrupting the first column header | File is ISO-8859-1, NO BOM present. Column names have trailing spaces that need trimming. |
| PARS-04 | Parser extracts date (DD.MM.YYYY) and time (HH:MM:SS) columns into timezone-safe timestamps | Manual date parse from Datum+Zeit columns; use UTC Date.UTC() to avoid local timezone shifts |
| PARS-05 | Parser extracts column metadata (name, unit, group) from header strings like `HK1 VL Ist[C]` | Regex `/^(.+?)\s*\[(.+)\]\s*$` to split name from unit; prefix matching for group assignment |
| INTF-01 | UI is in English | English strings hardcoded in HTML; German CSV param names displayed as-is |
| INTF-02 | Original German CSV parameter names are displayed (not translated) | Preserve raw column names from CSV after trimming trailing space |
</phase_requirements>

---

## Summary

Phase 1 builds a single-file web application (one `.html` file with vendored JS/CSS inlined or locally referenced) that loads an OekoFEN pellet boiler CSV file, parses it, and produces an in-memory columnar data model. The stack is locked to uPlot 1.6.32 + PapaParse 5.5.3. No framework or build tool is used — pure vanilla JavaScript.

The most critical engineering detail discovered by inspecting the real `touch_20260216.csv` file: the file is encoded in **ISO-8859-1 (Latin-1)**, not UTF-8, and has **no BOM**. This means PapaParse cannot be called with a string obtained by default FileReader UTF-8 reading — the file must be read as an `ArrayBuffer` and decoded with `new TextDecoder('windows-1252')` before passing to PapaParse. The `encoding` config option in PapaParse only works when PapaParse controls the FileReader internally (i.e., when you pass a `File` object directly to `Papa.parse(file, {encoding: 'windows-1252'})`); that approach is also valid but requires testing.

Additional non-obvious CSV details found by inspecting the actual file: (1) every row ends with a trailing semicolon creating a spurious empty column, (2) column header names have trailing spaces (e.g., `"Datum "`, `"BR "`), (3) timestamps start at `00:02:44` — not midnight — and the last row of a day file can cross midnight to the next calendar date, and (4) column names with units appear in two styles: `AT [°C]` (space before bracket) and `HK1 VL Ist[°C]` (no space).

**Primary recommendation:** Use a two-pass approach: (1) read the File as ArrayBuffer, decode with `TextDecoder('windows-1252')`, (2) pass the decoded string to `Papa.parse(text, {delimiter:';', header:true, skipEmptyLines:true})`, then (3) post-process: trim all column names, drop the empty trailing column, convert German decimals, build Unix timestamps with `Date.UTC()`, and assign groups via prefix matching.

---

## Real CSV File Analysis

**File:** `./Files/touch_20260216.csv`
**Confirmed properties (verified by hex dump + `file` command):**

| Property | Value | Implication |
|----------|-------|-------------|
| Encoding | ISO-8859-1 (Latin-1) | Must use TextDecoder('windows-1252') — NOT UTF-8 |
| BOM | None (no EF BB BF bytes) | No BOM stripping needed |
| Delimiter | Semicolon `;` | PapaParse `delimiter: ";"` |
| Line count | 1441 lines (1 header + 1439 data rows + 1 blank) | ~1440 data points per day (~1 per minute) |
| Trailing semicolon | Yes, every row | Creates empty last column; must be filtered |
| Column count | 71 split items, 70 named columns, 1 empty | Filter out columns where trimmed name === "" |
| Column name trailing spaces | Yes (e.g., `"Datum "`, `"BR "`, `"Fehler1 "`) | Trim all header names |
| Unit encoding | `[°C]` unit in brackets; degree = 0xB0 (Latin-1) | TextDecoder handles this correctly |
| Date format | `DD.MM.YYYY` (e.g., `16.02.2026`) | Split on `.`, use index [2], [1], [0] for year/month/day |
| Time format | `HH:MM:SS` (e.g., `00:02:44`) | Split on `:` |
| Decimal separator | Comma (e.g., `1,4`, `63,6`) | Replace `,` with `.` before parseFloat |
| Midnight crossover | Last row can be next calendar day (`17.02.2026;00:00:44`) | Timestamps ascend monotonically; this is correct |
| Integer values | Some columns are always integers (e.g., `BR `, `HK1 Pumpe`) | dynamicTyping not helpful; manual parse handles both |
| Large negative int | `PE1 Motor RA` contains `-2147483648` | INT32_MIN — valid integer, not a parse error |

**Column name patterns (verified from actual file):**

```
With unit [brackets]:    AT [°C], ATakt [°C], KT Ist [°C], HK1 VL Ist[°C]
With % unit:             PU1 Pumpe[%], PE1 Modulation[%], PE1 Luefterdrehzahl[%]
With special unit:       PE1 Einschublaufzeit[zs], PE1 Saug-Int[min]
Without unit:            BR, Sperrzeit, PE1_BR1, HK1 Pumpe, HK1 Status
Ignored columns:         Fehler1, Fehler2, Fehler3, Zubrp1 Pumpe
Empty (trailing semi):   "" (last item after split)
```

**Unit extraction regex:** `/^(.+?)\s*\[([^\]]+)\]$|^(.+?)$/` applied to trimmed header name. When `[unit]` is present: name = group 1, unit = group 2. When no brackets: name = group 3, unit = "".

---

## Standard Stack

### Core (Locked — do not change)

| Library | Version | Purpose | Source |
|---------|---------|---------|--------|
| uPlot | 1.6.32 | Canvas-based time-series charting | CDN: `cdn.jsdelivr.net/npm/uplot@1.6.32/dist/` |
| PapaParse | 5.5.3 | CSV parsing (semicolon, header mode, streaming) | CDN or vendored |

**No framework. No build tool. Pure vanilla JavaScript in a single HTML file.**

### CDN / File URLs

```
uPlot JS:  https://cdn.jsdelivr.net/npm/uplot@1.6.32/dist/uPlot.iife.min.js  (49.88 KB)
uPlot CSS: https://cdn.jsdelivr.net/npm/uplot@1.6.32/dist/uPlot.min.css      (1.81 KB)
PapaParse: https://cdn.jsdelivr.net/npm/papaparse@5.5.3/papaparse.min.js
```

For a vendored (offline-capable) setup: download these files and reference locally.

### Delivery approach for single-file output

Since the app is one HTML file, choose between:
1. **CDN script tags** (simplest; requires internet for first load)
2. **Vendored files alongside index.html** (works offline; 3 files total: `index.html`, `uPlot.iife.min.js`, `uPlot.min.css`, `papaparse.min.js`)

Recommendation: vendored files alongside HTML. The project already has a `Files/` directory, suggesting local file conventions.

---

## Architecture Patterns

### Recommended File Structure

```
index.html              # Single HTML entry point — all app logic here
uPlot.iife.min.js       # Vendored uPlot (49 KB minified)
uPlot.min.css           # Vendored uPlot styles (2 KB)
papaparse.min.js        # Vendored PapaParse (51 KB minified)
Files/
  touch_20260216.csv    # Sample test file (do not ship)
```

### Pattern 1: One-Way Data Pipeline

Per locked architectural decision:

```
File drop/pick
  → readAsArrayBuffer (FileReader)
  → TextDecoder('windows-1252') → string
  → Papa.parse(string, {delimiter:';', header:true, skipEmptyLines:true})
  → normalizeHeaders(rawResult)     # trim names, drop empty col
  → convertValues(rows)             # German decimals, parse ints
  → buildTimestamps(rows)           # Datum+Zeit → Unix seconds UTC
  → classifyColumns(headers)        # assign group, unit, type
  → AppState.dataModel              # columnar {timestamps:[], series:{}}
  → (Phase 2+) renderChart()
```

State is updated only by loading a new file. Chart state (which columns are visible, zoom range) is separate and persists across file loads.

### Pattern 2: App State Store (Singleton Object)

```javascript
// Source: standard vanilla JS module pattern
const AppState = {
  // Data model (set after parse)
  dataModel: null,    // { timestamps: Float64Array, columns: Column[] }
  filename: null,
  fileDate: null,

  // View state (persists across file loads — Phase 2+)
  visibleColumns: [],
  zoomRange: null,
};

// Column descriptor shape
// { rawName: string, displayName: string, unit: string, group: string, type: 'continuous'|'discrete', data: Float32Array|Int16Array }
```

### Pattern 3: uPlot Data Format

uPlot requires **columnar aligned data** — all arrays must be the same length, x-values must be ascending numbers (Unix timestamps in seconds):

```javascript
// Source: uPlot official demos (leeoniya.github.io/uPlot/demos/)
const uPlotData = [
  [1708038164, 1708038224, 1708038284, ...],  // data[0]: Unix timestamps (seconds)
  [1.4, 1.4, 1.4, ...],                        // data[1]: first y-series (AT)
  [55.4, 55.4, 55.4, ...],                     // data[2]: second y-series (HK1 VL Ist)
  // null values for gaps/parse errors
];

const opts = {
  width: 1200,
  height: 400,
  series: [
    {},                           // x-axis placeholder (always empty object)
    { label: "AT [°C]", stroke: "red" },
    { label: "HK1 VL Ist[°C]", stroke: "blue" },
  ],
  scales: {
    x: { time: true }            // treat x-values as Unix timestamps
  },
};

const chart = new uPlot(opts, uPlotData, document.getElementById('chart'));
```

**Key uPlot requirements (verified from TypeScript definitions + demos):**
- `data[0]` must be numbers (Unix timestamps in seconds, not milliseconds)
- All data arrays must be equal length
- x-values must be ascending (no duplicates)
- `null` or `undefined` in y-arrays = gap in line (don't render that point)
- `scales.x.time: true` activates timestamp x-axis formatting

### Pattern 4: File Drop Zone with Navigation Guard

```javascript
// Source: MDN — File drag and drop API
// (developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API/File_drag_and_drop)

// CRITICAL: Window-level guard prevents browser from navigating when user
// drops a file OUTSIDE the drop zone
window.addEventListener('dragover', (e) => {
  if ([...e.dataTransfer.items].some(item => item.kind === 'file')) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'none'; // show "no drop" cursor outside zone
  }
});
window.addEventListener('drop', (e) => {
  if ([...e.dataTransfer.items].some(item => item.kind === 'file')) {
    e.preventDefault(); // prevent browser navigation
  }
});

// Drop zone specific handler
const dropZone = document.getElementById('drop-zone');

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'copy';
  dropZone.classList.add('drag-over'); // visual feedback
});
dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('drag-over');
});
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

// File picker alternative
const fileInput = document.createElement('input');
fileInput.type = 'file';
fileInput.accept = '.csv';
fileInput.addEventListener('change', (e) => {
  if (e.target.files[0]) handleFile(e.target.files[0]);
});
```

### Pattern 5: ISO-8859-1 File Reading

```javascript
// Source: MDN FileReader + WHATWG Encoding spec
// The label 'windows-1252' covers 'iso-8859-1' per WHATWG spec —
// they are the same encoding on the web.

async function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      // e.target.result is ArrayBuffer
      const decoder = new TextDecoder('windows-1252');
      resolve(decoder.decode(e.target.result));
    };
    reader.onerror = reject;
    reader.readAsArrayBuffer(file);
  });
}
```

**Why not `FileReader.readAsText(file, 'windows-1252')`?**
The `readAsText` encoding parameter behavior is inconsistent across browser implementations for legacy encodings. Using `readAsArrayBuffer` + `TextDecoder` is the reliable modern approach.

**Alternative: Pass File directly to PapaParse with `encoding` option.**
PapaParse's `encoding` option only works when you pass a File (not a string). It internally uses FileReader with the specified encoding. This is simpler but less transparent:

```javascript
Papa.parse(file, {
  encoding: 'windows-1252',
  delimiter: ';',
  header: true,
  // ...
});
```

This approach requires verifying it works correctly in the target browsers — LOW confidence. Prefer the ArrayBuffer + TextDecoder approach.

### Pattern 6: German Decimal Conversion + Timestamp Building

```javascript
// Source: analysis of touch_20260216.csv (verified)

function parseGermanFloat(str) {
  if (str === null || str === undefined || str.trim() === '') return null;
  const normalized = str.trim().replace(',', '.');
  const val = parseFloat(normalized);
  return isNaN(val) ? null : val;
}

function buildUnixTimestamp(datumStr, zeitStr) {
  // datumStr: "16.02.2026", zeitStr: "00:02:44"
  const [day, month, year] = datumStr.trim().split('.');
  const [hour, min, sec] = zeitStr.trim().split(':');
  // Date.UTC avoids local timezone offset — always UTC
  return Date.UTC(
    parseInt(year, 10),
    parseInt(month, 10) - 1,  // month is 0-indexed
    parseInt(day, 10),
    parseInt(hour, 10),
    parseInt(min, 10),
    parseInt(sec, 10)
  ) / 1000;  // uPlot needs seconds, not milliseconds
}
```

**Timezone safety:** `Date.UTC()` never applies local timezone. The CSV timestamps are "local time of the boiler" with no timezone info — we treat them as UTC for display purposes so the x-axis shows `00:02` to `23:59` regardless of the viewer's local timezone. This matches PARS-04 exactly.

### Pattern 7: Column Header Parsing + Group Assignment

```javascript
// Source: analysis of touch_20260216.csv (verified)

const UNIT_REGEX = /^(.+?)\s*\[([^\]]+)\]\s*$|^(.+?)\s*$/;

function parseColumnHeader(rawHeader) {
  const trimmed = rawHeader.trim();
  const match = trimmed.match(UNIT_REGEX);
  const name = (match[1] || match[3]).trim();
  const unit = match[2] || '';
  return { rawName: rawHeader, displayName: name, unit };
}

const BINARY_COLUMNS = new Set(['BR', 'Sperrzeit']);
const IGNORED_COLUMNS = new Set(['Fehler1', 'Fehler2', 'Fehler3', 'Zubrp1 Pumpe', '']);

const GROUP_RULES = [
  { prefix: 'HK1',  group: 'Heating Circuit (HK1)' },
  { prefix: 'WW1',  group: 'Hot Water (WW1)' },
  { prefix: 'PU1',  group: 'Buffer (PU1)' },
  { prefix: 'PE1',  group: 'Pellet Unit (PE1)' },
  // Boiler: everything else (including AT, ATakt, KT*, BR, Sperrzeit, PE1_BR1)
];
const BOILER_NAMES = new Set(['AT', 'ATakt', 'KT Ist', 'KT Soll', 'BR', 'Sperrzeit', 'PE1_BR1']);

function assignGroup(displayName) {
  for (const rule of GROUP_RULES) {
    if (displayName.startsWith(rule.prefix)) return rule.group;
  }
  if (BOILER_NAMES.has(displayName)) return 'Boiler';
  return 'Other';
}

function classifyType(displayName) {
  return BINARY_COLUMNS.has(displayName) ? 'discrete' : 'continuous';
}
```

### Recommended Project Structure (single HTML file variant)

```
index.html              # App entry point — HTML structure + all JS inline
uPlot.iife.min.js       # Vendored — uPlot IIFE bundle
uPlot.min.css           # Vendored — uPlot default styles
papaparse.min.js        # Vendored — PapaParse
Files/                  # Sample files (dev only, not shipped)
```

**All JavaScript lives in `<script>` tags within `index.html`**. No modules, no import/export. Functions defined in order: utilities first, then pipeline functions, then event handlers, then init.

### Anti-Patterns to Avoid

- **Reading as UTF-8:** `new FileReader().readAsText(file)` without encoding = garbled degree signs and special characters from this ISO-8859-1 file.
- **Using `new Date()`** for timestamp parsing: `new Date('16.02.2026 00:02:44')` fails in all browsers — German date format is not standard. Use manual split + `Date.UTC()`.
- **Relying on `dynamicTyping: true`** in PapaParse: PapaParse's German decimal `"1,4"` is NOT auto-converted to a number. It stays as the string `"1,4"` because `1,4` is not a valid JavaScript number literal. Must use the `transform` callback or post-process.
- **Passing milliseconds to uPlot:** uPlot's `scales.x.time: true` expects **seconds** (Unix epoch seconds). Passing `Date.UTC()` directly (which returns ms) will display incorrect timestamps. Divide by 1000.
- **Appending empty column:** PapaParse with `header: true` and the trailing semicolon will create a column with an empty-string key `""`. Filter it out before building the data model.
- **Not trimming column names:** Column names like `"Datum "` and `"BR "` have trailing spaces in the raw CSV. All header names must be trimmed before use.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSV parsing | Custom split-based parser | PapaParse 5.5.3 | Handles quoted fields, edge cases, trailing semicolons, empty lines |
| Time-series chart | Canvas/SVG chart engine | uPlot 1.6.32 | Canvas-optimized, handles 1440+ points at 60fps, zoom built-in |
| Toast notifications | Custom CSS animation system | Simple `setTimeout` + CSS class toggle | For this app, a basic auto-dismiss pattern suffices — no library needed |
| Encoding detection | Custom byte detection | `TextDecoder('windows-1252')` | Known encoding from boiler firmware; no detection needed |

**Key insight:** The CSV parsing problem looks simple (it's just semicolons!) but the combination of ISO-8859-1 encoding + trailing semicolons + trailing-space column names + German decimals + German date format creates exactly 5 distinct failure modes that each break silently. PapaParse handles the CSV structure; the normalizer must handle all 5 format quirks.

---

## Common Pitfalls

### Pitfall 1: Silent ISO-8859-1 Mojibake
**What goes wrong:** Degree symbols (`°C`) appear as `Â°C` or `?C` in column headers. `HK1 VL Ist[°C]` becomes `HK1 VL Ist[Â°C]`.
**Why it happens:** FileReader defaults to UTF-8. Byte `0xB0` (Latin-1 degree) is invalid in UTF-8 and gets replaced.
**How to avoid:** Use `readAsArrayBuffer` + `new TextDecoder('windows-1252')`.
**Warning signs:** If column headers contain `Â` or `?` characters after parsing.

### Pitfall 2: uPlot Receives Millisecond Timestamps
**What goes wrong:** Chart x-axis shows dates in year 58,000 CE instead of 2026.
**Why it happens:** `Date.UTC()` returns milliseconds. uPlot `time: true` scale expects seconds.
**How to avoid:** Always divide `Date.UTC(...)` result by `1000` before storing.
**Warning signs:** X-axis labels show obviously wrong years.

### Pitfall 3: German Decimal Not Converted
**What goes wrong:** All temperature values parse as `NaN` or `null`.
**Why it happens:** `parseFloat("1,4")` returns `1` in Chrome (stops at comma). Other implementations return `NaN`.
**How to avoid:** Replace comma with period BEFORE parseFloat: `parseFloat(str.replace(',', '.'))`.
**Warning signs:** Data model shows all `null` for continuous columns.

### Pitfall 4: Trailing Semicolon Empty Column
**What goes wrong:** Data model has a column with key `""` containing all empty strings. Group assignment crashes on empty display name.
**Why it happens:** PapaParse `header: true` creates a key for every header, including the empty string after the last `;`.
**How to avoid:** Filter columns where `trimmed name === ""` during normalization.
**Warning signs:** `AppState.dataModel.columns` contains a column named `""`.

### Pitfall 5: Browser Navigation on Outside Drop
**What goes wrong:** User misses the drop zone; browser navigates away and shows the raw CSV file. The app is gone.
**Why it happens:** Browser default behavior for file drops is to open the file.
**How to avoid:** `window.addEventListener('dragover', e => e.preventDefault())` AND `window.addEventListener('drop', e => e.preventDefault())` — BOTH events must be cancelled at window level.
**Warning signs:** Test by dragging a CSV file to the browser toolbar area or outside the drop zone.

### Pitfall 6: Midnight Crossover Timestamps
**What goes wrong:** A file named `touch_20260216.csv` has its last row dated `17.02.2026;00:00:44`. Timestamp parsing may fail if the date is assumed to always be the file date.
**Why it happens:** The boiler logs every minute, and the last log entry for the "day" may cross midnight into the next calendar day.
**How to avoid:** Always parse `Datum` and `Zeit` from the row itself — never infer the date from the filename. The timestamps will be strictly ascending even across midnight.
**Warning signs:** Check that the last timestamp > first timestamp; a crossover causes a discontinuity if date is wrong.

### Pitfall 7: dragenter/dragleave Visual Glitch
**What goes wrong:** The drop zone highlight flickers when the cursor moves over child elements inside the drop zone.
**Why it happens:** `dragleave` fires when cursor enters a child element, even within the drop zone boundary.
**How to avoid:** Use a counter (increment on `dragenter`, decrement on `dragleave`, apply class when counter > 0) or use CSS `pointer-events: none` on child elements inside the drop zone.
**Warning signs:** Drop zone highlight flashes on and off as user moves mouse over text inside the zone.

---

## Code Examples

### Complete CSV Parse + Normalize Pipeline

```javascript
// Source: verified against touch_20260216.csv (2026-02-17)

async function loadAndParse(file) {
  // Step 1: Read as ArrayBuffer to handle ISO-8859-1 encoding
  const arrayBuffer = await file.arrayBuffer();
  const text = new TextDecoder('windows-1252').decode(arrayBuffer);

  // Step 2: Parse with PapaParse
  const result = Papa.parse(text, {
    delimiter: ';',
    header: true,
    skipEmptyLines: true,
    // Do NOT use dynamicTyping — German decimals "1,4" won't convert
    // Do NOT use transform here — transform runs per cell, which is slow
    //   for 1440 rows x 70 columns = 100,800 cells; post-process instead
  });

  // Step 3: Normalize headers — trim names, drop empty column
  const rawHeaders = result.meta.fields;
  const columnMeta = rawHeaders
    .map(parseColumnHeader)
    .filter(col => col.displayName !== ''); // drop trailing semicolon ghost column

  // Step 4: Build columnar data model
  const timestamps = [];
  const seriesData = columnMeta
    .filter(col => col.displayName !== 'Datum' && col.displayName !== 'Zeit')
    .map(col => ({ ...col, group: assignGroup(col.displayName), type: classifyType(col.displayName), data: [] }));

  let parseIssues = 0;

  for (const row of result.data) {
    // Build timestamp
    const datum = row['Datum '] || row['Datum'];   // handle trailing space key
    const zeit  = row['Zeit ']  || row['Zeit'];
    if (!datum || !zeit) { parseIssues++; continue; }
    timestamps.push(buildUnixTimestamp(datum, zeit));

    // Build series values
    for (const col of seriesData) {
      const raw = row[col.rawName];
      const val = parseGermanFloat(raw);
      col.data.push(val);  // null if unparseable
      if (val === null && raw !== undefined && raw.trim() !== '') parseIssues++;
    }
  }

  return { timestamps, columns: seriesData, filename: file.name, parseIssues };
}
```

### File Type Validation

```javascript
// Source: standard web pattern, consistent with locked decisions

function validateFile(file) {
  if (!file.name.toLowerCase().endsWith('.csv')) {
    if (/\.(png|jpg|jpeg|gif|bmp|webp)$/i.test(file.name)) {
      showToast('This is a graph image. Drop the CSV file (touch_*.csv) instead');
    } else {
      showToast(`Invalid file type. Please drop a .csv file.`);
    }
    return false;
  }
  return true;
}
```

### OekoFEN Heuristic Detection

```javascript
// Detect non-OekoFEN CSVs — warn but proceed (per locked decision)
function detectOekoFEN(columnMeta) {
  const names = columnMeta.map(c => c.displayName);
  const hasExpectedColumns = names.includes('AT') && names.includes('Datum') && names.includes('Zeit');
  return hasExpectedColumns;
}
// Usage: if (!detectOekoFEN(columnMeta)) { showToast("This doesn't look like OekoFEN data"); }
// Then continue parsing regardless
```

### Toast Notification (No Library)

```javascript
// Source: standard pattern for vanilla JS auto-dismiss notifications

function showToast(message, duration = 4000) {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  document.body.appendChild(toast);

  // Trigger CSS animation
  requestAnimationFrame(() => toast.classList.add('toast--visible'));
  setTimeout(() => {
    toast.classList.remove('toast--visible');
    toast.addEventListener('transitionend', () => toast.remove(), { once: true });
  }, duration);
}
```

### Data Summary Generation

```javascript
// Produces the post-load summary (compact info bar recommended for chart readability)
function buildSummary(model) {
  const startTs = model.timestamps[0];
  const endTs   = model.timestamps[model.timestamps.length - 1];
  const startDate = new Date(startTs * 1000).toISOString().slice(0, 10);
  const endDate   = new Date(endTs * 1000).toISOString().slice(0, 10);
  const startTime = new Date(startTs * 1000).toISOString().slice(11, 16);
  const endTime   = new Date(endTs * 1000).toISOString().slice(11, 16);

  const groups = {};
  for (const col of model.columns) {
    if (!IGNORED_COLUMNS.has(col.displayName)) {
      groups[col.group] = (groups[col.group] || 0) + 1;
    }
  }

  return {
    filename: model.filename,
    fileDate: startDate,
    rows: model.timestamps.length,
    columns: model.columns.length,
    timeRange: `${startTime} – ${endTime}`,
    groups: Object.entries(groups).map(([name, count]) => ({ name, count })),
    parseIssues: model.parseIssues,
  };
}
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| D3.js for time series | uPlot for performance-critical charts | 10x+ faster at 1000+ points |
| FileReader.readAsText with encoding param | readAsArrayBuffer + TextDecoder | Reliable encoding for non-UTF-8 files |
| Assuming CSV is UTF-8 or BOM-prefixed | Inspect actual file encoding | Avoids silent data corruption |
| `new Date(dateString)` for non-ISO dates | Manual split + `Date.UTC()` | Portable; no browser-specific date parsing bugs |

---

## Open Questions

1. **PapaParse `encoding` option vs manual TextDecoder**
   - What we know: PapaParse supports an `encoding` option that uses FileReader internally when a File object is passed
   - What's unclear: Whether `Papa.parse(file, {encoding: 'windows-1252'})` reliably handles the OekoFEN ISO-8859-1 file across browsers vs the `readAsArrayBuffer + TextDecoder` approach
   - Recommendation: Use `readAsArrayBuffer + TextDecoder('windows-1252')` as primary approach (more transparent). If PapaParse streaming is needed later, switch to `encoding` option.

2. **PapaParse header key lookup for trimmed vs untrimmed names**
   - What we know: PapaParse creates header keys exactly as they appear in the CSV. `"Datum "` (with trailing space) is the key, not `"Datum"`.
   - What's unclear: Whether `skipEmptyLines` interacts with trailing-space header keys in any special way
   - Recommendation: After parsing, rebuild a trimmed-key lookup map. Do not assume PapaParse auto-trims header names.

3. **dragenter counter approach vs CSS solution for flicker**
   - What we know: dragleave fires on child element entry causing flicker
   - What's unclear: Which approach is cleanest for a single-file no-framework app
   - Recommendation: Use a `dragDepth` counter (increment `dragenter`, decrement `dragleave`, apply class when > 0). Simple and reliable.

---

## Sources

### Primary (HIGH confidence)
- Real file: `./Files/touch_20260216.csv` — hex dump + `file` command confirmed ISO-8859-1, no BOM, trailing semicolons, column name trailing spaces
- MDN: `developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API/File_drag_and_drop` — drag-and-drop code patterns
- MDN: `developer.mozilla.org/en-US/docs/Web/API/FileReader/readAsText` — encoding parameter behavior
- WHATWG Encoding spec: `encoding.spec.whatwg.org` — confirmed `iso-8859-1` and `windows-1252` are valid TextDecoder labels (both map to Windows-1252)
- uPlot TypeScript definitions + demos: `leeoniya.github.io/uPlot/demos/` — AlignedData format, time scale, null gaps, series config
- jsDelivr CDN: `cdn.jsdelivr.net/npm/uplot@1.6.32/dist/` — confirmed file names and sizes
- PapaParse docs: `papaparse.com/docs` — config options confirmed (delimiter, encoding, header, skipEmptyLines, transform, beforeFirstChunk)

### Secondary (MEDIUM confidence)
- uPlot demos (fetched via WebFetch): missing-data.html confirms null values create gaps; data[0] must be Unix seconds
- MDN drag-drop example: window-level guard pattern with `dragover`+`drop` preventDefault confirmed

### Tertiary (LOW confidence)
- WebSearch: reports that `FileReader.readAsText(file, encoding)` is unreliable for legacy encodings in some browsers — prefer ArrayBuffer + TextDecoder

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — locked decisions, CDN file sizes confirmed
- CSV format: HIGH — analyzed real CSV file with hex dump
- PapaParse config: HIGH — verified from official docs
- uPlot data format: HIGH — verified from TypeScript definitions and live demos
- Drag-and-drop: HIGH — verified from MDN official docs
- Encoding approach: MEDIUM — TextDecoder approach verified from spec; PapaParse `encoding` option reliability is LOW

**Research date:** 2026-02-17
**Valid until:** 2026-04-17 (stable libraries; 60 days)
