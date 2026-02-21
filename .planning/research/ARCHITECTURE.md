# Architecture Research

**Domain:** Single-file vanilla JS app — HTTP API fetch integration (v1.1)
**Researched:** 2026-02-21
**Confidence:** HIGH (code read directly; patterns derived from existing implementation, not assumptions)

> This document replaces the v1.0 ARCHITECTURE.md (2026-02-17).
> That file described the ideal multi-file structure. This document describes the
> actual shipped architecture (`index.html`, 2,542 lines, single file) and how v1.1
> features integrate with it. Read the code, not theory.

---

## Standard Architecture

### System Overview — v1.0 (Shipped)

```
┌─────────────────────────────────────────────────────────────────┐
│                     UI Layer (DOM)                               │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────────────┐   │
│  │  Drop Zone │  │  App Header  │  │  Toolbar Row           │   │
│  │  (file     │  │  #app-header │  │  (view tabs,           │   │
│  │   entry)   │  │  + filename  │  │   reset zoom,          │   │
│  └─────┬──────┘  └──────┬───────┘  │   params btn)          │   │
│        │                │          └───────────────────────┘   │
├────────┴────────────────┴──────────────────────────────────────┤
│                     App State (plain JS object)                  │
│  AppState = {                                                    │
│    dataModel, filename, fileDate,                               │
│    chart (uPlot), chartSeries,                                  │
│    onZoomChange, zoomRange, minimap                             │
│  }                                                              │
├─────────────────────────────────────────────────────────────────┤
│                     Data Pipeline                                │
│  File (from FileReader)                                          │
│    → readFileAsText()   [TextDecoder windows-1252]              │
│    → parseCSVString()   [PapaParse, delimiter:";"]              │
│    → normalizeHeaders() [trim, drop empty trailing col]         │
│    → buildDataModel()   [columnar arrays, timestamps]           │
│    → onFileAccepted()   [orchestrator — sets AppState]          │
├─────────────────────────────────────────────────────────────────┤
│                     Chart Layer                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  uPlot instance (canvas) — created by createChart()       │  │
│  │  Minimap uPlot instance — created by createMinimap()      │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                     Persistence Layer                            │
│  localStorage: 'oekofen-viewer-prefs'                           │
│    { activeView: string, visibleSeries: string[] }              │
└─────────────────────────────────────────────────────────────────┘
```

### System Overview — v1.1 (New Features)

```
┌─────────────────────────────────────────────────────────────────┐
│                     UI Layer (DOM)                               │
│  ┌────────────┐  ┌────────────────────────────────────────────┐ │
│  │  Drop Zone │  │  App Header #app-header                    │ │
│  │            │  │   [existing: filename, load-another-btn]   │ │
│  │  [NEW]     │  │   [NEW: gear icon → opens settings modal]  │ │
│  │  log-period│  └────────────────────────────────────────────┘ │
│  │  dropdown  │                                                  │
│  │  + "Fetch" │  ┌────────────────────────────────────────────┐ │
│  │    button  │  │  Settings Modal (NEW)                       │ │
│  └─────┬──────┘  │   IP, Port, Password fields                │ │
│        │         │   Save → localStorage                       │ │
│        │         └───────────────┬────────────────────────────┘ │
├────────┴───────────────────────┬─┴──────────────────────────────┤
│                     App State  │                                  │
│  AppState = {                  │                                  │
│    ... (existing)              │                                  │
│    [NO new fields needed]      │                                  │
│  }                             │                                  │
│                                │                                  │
│  Settings (module-level var):  │                                  │
│    _settings = { ip, port, password }  ← loaded from localStorage│
├────────────────────────────────┴──────────────────────────────────┤
│                     Data Sources (NEW: two entry points)          │
│                                                                   │
│  [Entry 1 — existing]         [Entry 2 — new]                    │
│  File from FileReader          fetch('http://ip:port/pass/cmd')  │
│         │                               │                         │
│         └──────────┬────────────────────┘                        │
│                    ▼                                              │
│             csvString (plain text)                                │
│                    │                                              │
│             parseCSVString()   [shared, unchanged]               │
│             normalizeHeaders()  [shared, unchanged]               │
│             buildDataModel()    [shared, unchanged]               │
│             onCsvStringAccepted() [NEW: renamed bridge fn]        │
├───────────────────────────────────────────────────────────────────┤
│                     Rate Limiter (NEW, module-level)              │
│  _lastFetchAt = 0  (timestamp)                                    │
│  FETCH_COOLDOWN_MS = 2500                                         │
│  Non-blocking: check before fetch, reject early if too soon       │
└───────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### Existing Components (v1.0) — Modified or Untouched

| Component | Responsibility | v1.1 Change |
|-----------|----------------|-------------|
| `#drop-zone` | File entry — drag/drop + file picker | Add log-period `<select>` + "Fetch from Heater" button below existing controls |
| `#app-header` | Shows filename + "Load Another" button | Add gear icon `<button id="settings-btn">` to right end |
| `onFileAccepted(file)` | Full pipeline orchestrator — File → chart | **Refactor**: extract inner body to `onCsvStringAccepted(csvString, displayName, fileDate)`. Becomes a thin wrapper. |
| `readFileAsText(file)` | Reads File as windows-1252 text | Untouched. Not called for fetch path (API response is already UTF-8 string). |
| `parseCSVString(csvString)` | PapaParse wrapper | **Untouched** — receives plain text string; works identically for both paths |
| `normalizeHeaders()` | Trims headers, drops empty trailing col | **Untouched** |
| `buildDataModel()` | Builds columnar data model | **Untouched** |
| `AppState` | Central runtime state object | **Untouched** — no new fields needed |
| `PREFS_KEY` / `savePrefs()` / `loadPrefs()` | View + series persistence | **Untouched** — separate key from settings |
| `showToast()` | User notifications | Used for fetch error states (unchanged function) |

### New Components (v1.1)

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| `_settings` | In-memory settings object. Single source of truth for IP/Port/Password during session. | Module-level `const _settings = { ip: '', port: '', password: '' }` — populated from localStorage at startup |
| `SETTINGS_KEY` | localStorage key for settings | `'oekofen-viewer-settings'` — separate from `PREFS_KEY` to avoid collision |
| `loadSettings()` | Read settings from localStorage into `_settings` | Called once at script init. Validates shape. Falls back to empty string defaults silently. |
| `saveSettings(ip, port, password)` | Persist settings to localStorage | Called when user clicks Save in settings modal |
| Settings Modal | Form UI: IP + Port + Password fields + Save + Cancel | Created/destroyed dynamically in JS (same pattern as existing picker modal). Injected into `document.body`. |
| `#settings-btn` | Gear icon in `#app-header`. Also accessible from drop zone. | `<button>` in app header HTML. Wire click → `openSettingsModal()`. Visible always (not just when chart is loaded). |
| Log-period `<select>` | Dropdown in `#drop-zone` for selecting which log to fetch | Static HTML inside `#drop-message`. Options: Today, Yesterday, Log 0–Log 3. Hidden when settings not configured. |
| `fetchCsv(logPeriod)` | HTTP fetch to `http://{ip}:{port}/{password}/csv?file={logPeriod}` then parse response as text | `async function`. Checks rate limiter, validates settings, calls `fetch()`, pipes text into shared pipeline |
| Rate limiter | Enforce 2500ms minimum between fetch calls | Module-level `let _lastFetchAt = 0`. Checked inside `fetchCsv()`. Non-blocking — returns early with toast if too soon. |
| `onCsvStringAccepted(csvString, displayName, fileDate)` | Shared pipeline entry — replaces the inner body of `onFileAccepted` | New function. Both `onFileAccepted` and `fetchCsv` call this. |

---

## Recommended Project Structure

The project stays single-file. Structure refers to logical sections inside `<script>` block, ordered as they appear:

```
index.html
├── <style>               # All CSS (no change)
├── <body>                # DOM skeleton
│   ├── #drop-zone        # [MODIFIED: add <select> + fetch button]
│   ├── #app-header       # [MODIFIED: add #settings-btn gear icon]
│   ├── #data-summary     # [unchanged]
│   ├── #toolbar-row      # [unchanged]
│   ├── #toast-container  # [unchanged]
│   ├── #chart-area       # [unchanged]
│   ├── #minimap-area     # [unchanged]
│   └── #status-bar       # [unchanged]
├── <script>              # All JS (sections in order)
│   ├── AppState          # [unchanged]
│   ├── Settings          # [NEW] SETTINGS_KEY, _settings, loadSettings(), saveSettings()
│   ├── Toast / Status    # [unchanged]
│   ├── UI state trans.   # showDropZone(), showAppView() [unchanged]
│   ├── Drop zone DnD     # [unchanged handlers]
│   ├── CSV pipeline      # readFileAsText → parseCSVString → normalizeHeaders
│   │                     # → buildDataModel (all unchanged)
│   ├── onCsvStringAccepted()  # [NEW] extracted from onFileAccepted body
│   ├── onFileAccepted()  # [MODIFIED] thin wrapper: readFileAsText → onCsvStringAccepted
│   ├── fetchCsv()        # [NEW] rate limiter check → fetch → onCsvStringAccepted
│   ├── Settings Modal    # [NEW] openSettingsModal(), closeSettingsModal()
│   ├── Chart lifecycle   # destroyChart(), createChart() [unchanged]
│   ├── Minimap           # createMinimap() [unchanged]
│   ├── View management   # buildViewPresets(), setActiveView(), etc. [unchanged]
│   ├── Legend / Picker   # wireLegendClicks(), openPickerModal() [unchanged]
│   ├── Persistence       # savePrefs(), loadPrefs(), applyRestoredPrefs() [unchanged]
│   ├── Event wiring      # pick-file-btn, load-another-btn [unchanged]
│   ├── Fetch button wire # [NEW] fetch-btn click → fetchCsv()
│   └── Init              # loadSettings(); setStatus('Ready...') [MODIFIED: add loadSettings()]
```

### Structure Rationale

- **Settings section placed early** — before pipeline functions, because `fetchCsv()` reads `_settings` and must come after it.
- **`onCsvStringAccepted()` placed before both callers** — `onFileAccepted()` and `fetchCsv()` both call it; JS `function` declarations are hoisted but keeping declaration order logical avoids confusion in a 2600-line file.
- **Settings Modal code grouped with other modal code** — near the picker modal for consistency. Both follow the same create/destroy-in-JS pattern.
- **Rate limiter lives inside `fetchCsv()`** — not a separate abstraction. 2 variables + 1 check. No module needed.

---

## Architectural Patterns

### Pattern 1: Extract Pipeline Entry Point (The Core Integration Pattern)

**What:** The existing `onFileAccepted(file)` does: `readFileAsText(file)` → `parseCSVString` → `normalizeHeaders` → `buildDataModel` → `showAppView` → `createChart`. The fetch path produces a CSV string directly (no FileReader step needed). Extract everything from `parseCSVString` onwards into `onCsvStringAccepted(csvString, displayName, fileDate)`. The file path calls this via `onFileAccepted`. The fetch path calls it directly.

**When to use:** Whenever two entry points (file + network) must feed a shared pipeline. This is the minimum-change integration — zero pipeline code is duplicated, zero pipeline code is modified.

**Trade-offs:**
- Pro: Zero risk to existing file-load path — `onFileAccepted` becomes a 3-line wrapper.
- Pro: Network path inherits all validation (OekoFEN column check, AT check, error toasts) for free.
- Con: `displayName` and `fileDate` must be synthesized for the fetch path. Use the log command as display name (`log_today` → `"Heater: log_today"`). Synthesize `fileDate` from `new Date()` for today/yesterday or leave `null` (chart title falls back to first row timestamp).

**Example:**
```javascript
// New shared entry point
async function onCsvStringAccepted(csvString, displayName, fileDate) {
  const papaResult = parseCSVString(csvString);
  const { fields, rows } = normalizeHeaders(papaResult);
  const dataModel = buildDataModel(fields, rows);
  // ... rest of existing onFileAccepted body, unchanged ...
  AppState.filename = displayName;
  AppState.fileDate = fileDate;
  showAppView(displayName);
  createChart();
}

// Existing path — now a thin wrapper
async function onFileAccepted(file) {
  setStatus('Loading\u2026');
  try {
    const csvString = await readFileAsText(file);
    const dateMatch = file.name.match(/(\d{8})/);
    await onCsvStringAccepted(csvString, file.name, dateMatch ? dateMatch[1] : null);
  } catch (err) {
    showToast('Failed to load file: ' + err.message, 'error');
    setStatus('Error: ' + err.message);
  }
}

// New fetch path
async function fetchCsv(logPeriod) {
  const now = Date.now();
  if (now - _lastFetchAt < FETCH_COOLDOWN_MS) {
    const remaining = Math.ceil((FETCH_COOLDOWN_MS - (now - _lastFetchAt)) / 1000);
    showToast('Please wait ' + remaining + 's before fetching again.', 'warning');
    return;
  }
  if (!_settings.ip || !_settings.password) {
    showToast('Configure heater connection in Settings first.', 'warning');
    openSettingsModal();
    return;
  }
  _lastFetchAt = now;
  setStatus('Fetching from heater\u2026');
  try {
    const url = 'http://' + _settings.ip + ':' + _settings.port + '/'
              + encodeURIComponent(_settings.password) + '/csv?file=' + logPeriod;
    const response = await fetch(url);
    if (!response.ok) throw new Error('HTTP ' + response.status);
    const csvString = await response.text();
    const displayName = 'Heater: ' + logPeriod;
    // Synthesize fileDate for log_today / log_yesterday
    const fileDate = synthesizeDateFromLogPeriod(logPeriod);
    await onCsvStringAccepted(csvString, displayName, fileDate);
  } catch (err) {
    showToast('Fetch failed: ' + err.message, 'error');
    setStatus('Fetch error: ' + err.message);
  }
}
```

---

### Pattern 2: Separate localStorage Keys for Settings vs. View Prefs

**What:** Use `'oekofen-viewer-settings'` for connection settings and keep the existing `'oekofen-viewer-prefs'` for view state. Never merge them into one key.

**When to use:** Always. These have different lifecycles: settings persist across all sessions regardless of which file is loaded; prefs are file-context-dependent and validated against the loaded data model on restore.

**Trade-offs:**
- Pro: No risk of settings being wiped when prefs are reset (e.g., if a file with different columns invalidates saved series).
- Pro: Settings can be read before any file is loaded (at init time, before `AppState.dataModel` exists).
- Con: None. Two keys is trivially more code than one.

**Example:**
```javascript
const SETTINGS_KEY = 'oekofen-viewer-settings';  // new
const PREFS_KEY    = 'oekofen-viewer-prefs';      // existing, unchanged

const _settings = { ip: '', port: '4321', password: '' };

function loadSettings() {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object') {
      _settings.ip       = parsed.ip       || '';
      _settings.port     = parsed.port     || '4321';
      _settings.password = parsed.password || '';
    }
  } catch (e) {
    console.warn('[loadSettings] failed:', e.name);
  }
}
// Called once at script bottom: loadSettings();
```

---

### Pattern 3: Dynamic Modal (Same Pattern as Existing Picker Modal)

**What:** The settings modal is created in JS on demand and destroyed on close — same pattern as `openPickerModal()` / `closePickerModal()`. No hidden `<div>` in HTML that needs to be shown/hidden.

**When to use:** This project's convention for overlays. The picker modal already validates this pattern works well.

**Trade-offs:**
- Pro: No stale state in hidden DOM. Modal always renders fresh from `_settings`.
- Pro: Consistent with existing code style — reviewers recognize the pattern.
- Con: Fields are not persistent across open/close within a session (by design — Save writes to `_settings`, Cancel discards).

**Example:**
```javascript
function openSettingsModal() {
  if (document.getElementById('settings-modal')) return; // prevent double-open
  const backdrop = document.createElement('div');
  backdrop.id = 'settings-modal';
  // ... same structure as picker modal (backdrop → dialog → header/body/footer) ...
  // Pre-populate fields from _settings
  ipInput.value       = _settings.ip;
  portInput.value     = _settings.port;
  passwordInput.value = _settings.password;
  // Save button writes to _settings + localStorage
  saveBtn.addEventListener('click', () => {
    _settings.ip       = ipInput.value.trim();
    _settings.port     = portInput.value.trim() || '4321';
    _settings.password = passwordInput.value.trim();
    saveSettings();
    closeSettingsModal();
    showToast('Settings saved.', 'info', 2000);
  });
  document.body.appendChild(backdrop);
}
```

---

### Pattern 4: Non-Blocking Rate Limiter (Timestamp Check, No setTimeout)

**What:** Store `_lastFetchAt` as a Unix ms timestamp. At the top of `fetchCsv()`, compare `Date.now() - _lastFetchAt` against `FETCH_COOLDOWN_MS = 2500`. If too soon, show a toast with remaining seconds and return immediately. No timer, no queue, no locked UI state.

**When to use:** When the external constraint is "don't hammer the device" not "guarantee exactly one request per N seconds." The OekoFEN heater is an embedded system; the user should be able to try again, not be locked out by a queuing mechanism.

**Trade-offs:**
- Pro: Zero UI thread blocking. `fetchCsv()` is async; early return is synchronous. UI stays responsive.
- Pro: The user sees feedback immediately (toast) and can retry after the cooldown naturally expires.
- Con: Does not prevent exactly-2500ms retries. Acceptable — this is a courtesy throttle, not security.
- Con: `_lastFetchAt` resets on page reload. Also acceptable — the heater recovers from a page reload delay.

**No setTimeout/setInterval needed.** The rate limiter does not need to track state between calls — it only needs to compare two numbers at call time.

---

## Data Flow

### File-to-Chart Pipeline (v1.0, unchanged)

```
User drops/picks file
    |
    v File object
onFileAccepted(file)
    |
    v readFileAsText(file) → windows-1252 ArrayBuffer decode
    |
    v csvString
    ↓
onCsvStringAccepted(csvString, file.name, fileDate)   ← NEW SPLIT POINT
    |
    v parseCSVString()  → PapaParse result
    |
    v normalizeHeaders() → { fields, rows }
    |
    v buildDataModel() → { timestamps[], columns[], isOekoFEN, ... }
    |
    v showAppView(displayName)
    |
    v createChart() → uPlot instance
    |
    Canvas renders
```

### Fetch-to-Chart Pipeline (v1.1, new)

```
User selects log period dropdown → clicks "Fetch from Heater"
    |
    v fetchCsv(logPeriod)
    |
    ├─ Rate limiter check: Date.now() - _lastFetchAt < 2500 → toast + return
    ├─ Settings check: !ip || !password → toast + openSettingsModal() + return
    |
    v fetch('http://ip:port/password/csv?file=logPeriod')
    |
    v response.text() → csvString (UTF-8 already — no TextDecoder step needed)
    |
    v onCsvStringAccepted(csvString, 'Heater: log_today', fileDate)
    |
    (same pipeline as file path from here on — zero duplication)
```

### Settings Flow

```
App init
    |
    v loadSettings() → _settings populated from localStorage

User clicks gear icon (#settings-btn)
    |
    v openSettingsModal()
    |
    (User edits IP/Port/Password fields)
    |
    v Save → _settings updated → saveSettings() → localStorage write
    v Cancel → _settings unchanged → modal destroyed
```

### Key Data Flows

1. **Both entry points → same pipeline:** File read and fetch both produce a `csvString`. `onCsvStringAccepted()` is the single shared entry. All validation, error toasting, and chart creation happens once in that function.
2. **Settings → fetch gating:** `fetchCsv()` reads `_settings` at call time — no event subscription, no reactive binding. Simplest possible coupling.
3. **Settings → localStorage:** Written on Save, read once at init. No in-flight synchronization needed (single-tab, single-user).
4. **Rate limiter → no state in AppState:** `_lastFetchAt` is a plain module-level `let`. Not in `AppState` because it is not chart state — it is an operational concern of the fetch subsystem only.

---

## Integration Points

### New vs. Modified Components

| Component | Status | What Changes |
|-----------|--------|--------------|
| `#drop-zone` HTML | **Modified** | Add `<select id="log-period-select">` + `<button id="fetch-btn">` below `#pick-file-btn`. Also add `<button id="settings-btn-drop">` (gear) for settings access before a file is loaded. |
| `#app-header` HTML | **Modified** | Add `<button id="settings-btn">` (gear icon, right end). Always visible once chart is shown. |
| `onFileAccepted(file)` | **Modified** | Extract body to `onCsvStringAccepted()`. Becomes 5-line wrapper. |
| `AppState` | **Untouched** | No new fields. |
| `parseCSVString()` | **Untouched** | Receives plain string from both paths. |
| `normalizeHeaders()` | **Untouched** | No change. |
| `buildDataModel()` | **Untouched** | No change. |
| `PREFS_KEY` persistence | **Untouched** | No change. |
| `showDropZone()` / `showAppView()` | **Untouched** | Called by `onCsvStringAccepted()` same as before. |
| `SETTINGS_KEY` | **New** | `'oekofen-viewer-settings'` |
| `_settings` | **New** | Module-level object: `{ ip, port, password }` |
| `loadSettings()` | **New** | Called at init. Reads `SETTINGS_KEY` from localStorage. |
| `saveSettings()` | **New** | Called from settings modal Save. Writes `SETTINGS_KEY`. |
| `openSettingsModal()` | **New** | Dynamic modal (same pattern as picker modal). |
| `closeSettingsModal()` | **New** | Removes modal from DOM. |
| `onCsvStringAccepted()` | **New** | Extracted pipeline entry. Called by both `onFileAccepted` and `fetchCsv`. |
| `fetchCsv(logPeriod)` | **New** | Rate limiter + `fetch()` + pipe to `onCsvStringAccepted`. |
| `_lastFetchAt` | **New** | Module-level `let`. Rate limiter state. |
| `FETCH_COOLDOWN_MS` | **New** | `const = 2500` |
| `synthesizeDateFromLogPeriod()` | **New** | Returns `YYYYMMDD` string for `log_today`/`log_yesterday`, `null` for `log0`–`log3`. |

### External Service Integration

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| OekoFEN heater HTTP API | `fetch(url)` → `response.text()` → shared CSV pipeline | URL format: `http://{ip}:{port}/{password}/csv?file={logPeriod}`. Must be same-origin or heater must send CORS headers. **CORS is the primary risk** — see PITFALLS.md. |
| Browser localStorage | `getItem`/`setItem` with JSON | Two separate keys: `SETTINGS_KEY` (connection), `PREFS_KEY` (view state). Both wrapped in try/catch for Safari private mode / QuotaExceededError. |

### CORS Constraint

`fetch()` from a file opened locally (`file://`) or from a different origin (e.g., served from localhost) to the heater's IP will be blocked by the browser's CORS policy unless the heater responds with `Access-Control-Allow-Origin: *`.

**Known OekoFEN behavior:** The HTTP API is documented for use with the heater's own local network interface. CORS header behavior is not publicly documented. This is the highest-risk unknown in v1.1.

**Mitigation options (in order of preference):**
1. Test first — open `index.html` from the filesystem and attempt a fetch. Many embedded device APIs allow wildcard CORS.
2. If CORS blocks: serve `index.html` from a local minimal HTTP server (Python `http.server`, VS Code Live Server). The fetch URL is still the heater's IP directly — no proxy needed if CORS allows the origin.
3. If CORS blocks in all cases: the integration is not possible without a proxy. Do not implement a proxy — it violates the no-server constraint. Document the limitation and fall back to file export.

---

## Build Order

Dependencies determine order. Earlier steps must be completed and working before later steps can be tested.

```
Step 1: Settings persistence (no UI yet)
        SETTINGS_KEY, _settings, loadSettings(), saveSettings()
        Verify: open browser console, call loadSettings(), check _settings populated.
        Why first: fetchCsv() depends on _settings being populated. Settings modal
        depends on saveSettings() existing.

Step 2: Settings modal UI
        openSettingsModal(), closeSettingsModal(), gear icon in HTML (#settings-btn)
        Verify: gear click opens modal; Save populates _settings and writes localStorage;
        Cancel leaves _settings unchanged; Escape closes.
        Why second: settings must be saveable before fetch can read valid values.

Step 3: onCsvStringAccepted() extraction
        Refactor onFileAccepted() → extract body → new onCsvStringAccepted()
        Verify: existing file-drop workflow is completely unaffected.
        Why third: this is the bridge. fetchCsv() calls onCsvStringAccepted().
        Must be proven working before adding the new caller.

Step 4: fetchCsv() + rate limiter
        fetchCsv(), _lastFetchAt, FETCH_COOLDOWN_MS, synthesizeDateFromLogPeriod()
        Verify: fetch succeeds with valid settings; rate limiter blocks second call
        within 2500ms with toast; invalid settings shows toast + opens modal.
        Why fourth: depends on onCsvStringAccepted() (Step 3) and _settings (Step 1).

Step 5: Drop zone fetch UI
        Log-period <select> + "Fetch from Heater" button in #drop-message
        Wire fetch-btn click → fetchCsv(select.value)
        Show/hide fetch controls based on settings completeness.
        Verify: dropdown visible; button triggers fetch; correct log period sent.
        Why last: pure UI wiring. All underlying logic exists. No logic risk.
```

**Rationale for this order:**
- Settings first because they gate everything. Without `_settings` populated, `fetchCsv()` always fails.
- Extraction (Step 3) before the new caller (Step 4) because it is a refactor of existing code — safest to verify in isolation before adding new callers that depend on it.
- UI wiring last because it is the lowest-risk step. HTML + a few event listeners. If the logic works, the UI will work.

---

## Anti-Patterns

### Anti-Pattern 1: Duplicating the CSV Pipeline for the Fetch Path

**What people do:** Write a separate `fetchAndProcessCsv()` that calls `parseCSVString → normalizeHeaders → buildDataModel → showAppView → createChart` directly, duplicating the existing `onFileAccepted` body.

**Why it's wrong:** Two copies of the pipeline immediately diverge. A bug fix or enhancement to one path is not applied to the other. The existing path has been validated against real OekoFEN CSV files with all its edge cases (German decimals, empty trailing columns, OekoFEN format validation). Duplicating loses those fixes.

**Do this instead:** Extract `onCsvStringAccepted(csvString, displayName, fileDate)`. Both entry points call it. One path. One place to fix bugs.

---

### Anti-Pattern 2: Storing Settings in AppState

**What people do:** Add `settings: { ip, port, password }` to the `AppState` object because it feels like "state."

**Why it's wrong:** `AppState` is chart runtime state — it is created per file load and reset when "Load Another" is clicked (`AppState.dataModel = null`, etc.). Connection settings must survive file reloads. Putting settings in `AppState` means they would need to be re-saved before every reload, or the reset logic needs to be changed to preserve settings. Both are error-prone.

**Do this instead:** Keep settings in a separate module-level variable (`_settings`) with its own localStorage key. `AppState` stays pure chart state.

---

### Anti-Pattern 3: Using setTimeout for the Rate Limiter

**What people do:** On fetch, set a timeout that disables the fetch button for 2500ms: `fetchBtn.disabled = true; setTimeout(() => fetchBtn.disabled = false, 2500)`.

**Why it's wrong:** The button state is not the rate limiter — it is a visual symptom. If the button is re-enabled manually, or if `fetchCsv` is called from another code path, the limit is bypassed. Also, the timeout fires even if the fetch failed, leaving the user locked out after an error.

**Do this instead:** The rate limiter is a timestamp check inside `fetchCsv()`. `_lastFetchAt` is only written when the fetch actually starts (after all pre-flight checks pass). This is the authoritative gate regardless of how `fetchCsv()` is called.

---

### Anti-Pattern 4: Blocking the UI Thread During Fetch

**What people do:** Use `XMLHttpRequest` with `async: false`, or `await fetch()` inside a synchronous function, or display a modal spinner that prevents all interaction.

**Why it's wrong:** The OekoFEN heater is on the local network and typically responds in <200ms, but if it is slow or unreachable, a blocking call freezes the browser tab. The file-drop flow is already async (`async function onFileAccepted`). The fetch flow must match.

**Do this instead:** `fetchCsv()` is `async`. `setStatus('Fetching...')` gives feedback without blocking. `await fetch()` releases the event loop. The user can still interact with the page (scroll, inspect, etc.) during the fetch. If the heater is unreachable, the `catch` handler shows a toast within the timeout period.

---

### Anti-Pattern 5: Inline URL Construction Without Validation

**What people do:** Build the fetch URL as `'http://' + _settings.ip + ':' + _settings.port + '/' + _settings.password + '/csv?file=' + logPeriod` without checking for empty values first.

**Why it's wrong:** An empty IP produces `http://:4321/password/csv?file=log_today`, which is a malformed URL that `fetch()` throws on, producing a cryptic error message to the user.

**Do this instead:** At the top of `fetchCsv()`, check `_settings.ip && _settings.password` before constructing the URL. If either is empty, show a user-friendly toast ("Configure heater connection in Settings first") and open the settings modal. Never let an empty-settings fetch reach `fetch()`.

---

## Scaling Considerations

This is a single-user, single-tab, client-side application. Traditional user-count scaling is irrelevant. The relevant dimension for v1.1 is **connectivity resilience**:

| Scenario | Architecture Behavior |
|----------|-----------------------|
| Heater reachable, CORS allowed | Fetch succeeds. Full happy path. |
| Heater reachable, CORS blocked | `fetch()` throws a network error. `catch` handler shows toast. User falls back to file export. |
| Heater unreachable (timeout) | Browser's default fetch timeout (varies, typically 300s). Use `AbortController` with a 10s timeout to give fast feedback. |
| Repeated rapid clicks | Rate limiter rejects within 2500ms. Toast shows remaining time. No outstanding requests accumulate. |
| Settings not configured | Pre-flight check in `fetchCsv()` catches this before URL is built. Modal opens automatically. |

**AbortController recommendation:** Add a 10-second abort timeout to `fetchCsv()`. The heater is embedded hardware — if it does not respond in 10 seconds, it is not going to. A 5-minute browser hang is a worse UX than a fast "Fetch timed out" toast.

---

## Sources

- **Direct code analysis** of `index.html` (2,542 lines) — HIGH confidence. All component descriptions derived from reading the actual shipped implementation.
- **MDN Fetch API** (https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API) — `fetch()`, `response.text()`, `AbortController`, CORS behavior — HIGH confidence (official)
- **MDN CORS** (https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) — same-origin policy, `Access-Control-Allow-Origin` — HIGH confidence (official)
- **MDN localStorage** (https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage) — key/value persistence, try/catch for QuotaExceededError — HIGH confidence (official)
- **PROJECT.md** — v1.1 feature requirements, OekoFEN API URL format `http://{ip}:{port}/{password}/{command}` — HIGH confidence (project specification)
- Existing picker modal pattern in `index.html` (lines 2326–2513) — HIGH confidence (working implementation, reference for settings modal pattern)

---

*Architecture research for: OekoFEN CSV Viewer v1.1 — HTTP API fetch integration*
*Researched: 2026-02-21*
*Supersedes: 2026-02-17 v1.0 ARCHITECTURE.md*
