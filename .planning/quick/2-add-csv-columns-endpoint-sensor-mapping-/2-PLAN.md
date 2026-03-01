---
phase: quick-2
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - server.py
  - index.html
autonomous: false
requirements: []

must_haves:
  truths:
    - "GET /csv-columns returns column headers from the most recent CSV file"
    - "Sensor mapping dropdowns in Settings are populated with actual CSV column names"
    - "Buffer preset names display as Pellaqua (not PES)"
    - "Heater model list includes Pellematic Condens group with 20/25/32/45 kW options"
  artifacts:
    - path: "server.py"
      provides: "GET /csv-columns route returning {columns: [...]}"
      contains: "parsed.path == '/csv-columns'"
    - path: "index.html"
      provides: "Sensor mapping dropdowns populated from /csv-columns"
      contains: "fetch('/csv-columns')"
  key_links:
    - from: "index.html openSettingsModal()"
      to: "/csv-columns"
      via: "fetch in sensorSep block"
      pattern: "fetch\\('/csv-columns'\\)"
---

<objective>
Verify and confirm the four features described in the memory notes are fully implemented:

1. GET /csv-columns endpoint in server.py
2. Sensor mapping dropdowns populated from /csv-columns in Settings modal
3. Buffer preset names corrected to Pellaqua_xxx
4. Pellematic Condens heater models (20/25/32/45 kW) added

Purpose: Code inspection confirms all four items are already committed. This plan verifies they work end-to-end with the running server.

Output: Confirmed working state or identified gaps requiring a follow-up fix.
</objective>

<execution_context>
@C:/Users/buhra/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/buhra/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

<interfaces>
<!-- Already implemented — confirmed by code inspection before planning. -->

From server.py (lines 994-1021):
```python
# Route: GET /csv-columns — return column headers from most recent CSV
if parsed.path == '/csv-columns':
    import glob as _glob
    csv_files = sorted(_glob.glob(os.path.join(HISTORY_DIR, '*.csv')))
    columns = []
    if csv_files:
        with open(csv_files[-1], 'rb') as f:
            raw = f.read(8192)
        # tries windows-1252, utf-8, utf-8-sig
        first_line = next((l for l in text.splitlines() if l.strip()), '')
        columns = [h.strip() for h in first_line.split(';') if h.strip()]
    body = json.dumps({'columns': columns}).encode('utf-8')
    # returns 200 application/json
```

From index.html (lines 3857-3890) — sensor mapping dropdowns:
```javascript
SENSOR_TYPES.forEach(function(st) { /* builds <select> per sensor type */ });
if (window.location.protocol !== 'file:') {
    fetch('/csv-columns').then(r => r.json()).then(function(data) {
        var cols = data.columns || [];
        SENSOR_TYPES.forEach(function(st) {
            var sel = document.getElementById('sensor-map-' + st.key);
            cols.forEach(function(col) {
                var opt = document.createElement('option');
                opt.value = col; opt.textContent = col;
                sel.appendChild(opt);
            });
            sel.value = savedVal;
        });
    }).catch(function() {});
}
```

From index.html (lines 3699-3710) — BUFFER_PRESETS (already Pellaqua):
```javascript
const BUFFER_PRESETS = [
  { label: '— Select model —',               value: '',              volumeL: null },
  { label: 'Pellaqua 200 (200 L)',            value: 'Pellaqua_200', volumeL: 200  },
  // ... 300, 500, 750, 1000, 1500, 2000
  { label: 'Pellaqua Combi 800 (800 L + DHW)', value: 'PellaquaC_800',  volumeL: 800  },
];
```

From index.html (lines 3688-3692) — Pellematic Condens (already added):
```javascript
{ group: 'Pellematic Condens' },
{ label: 'Pellematic Condens 20 kW', value: 'PelleCondens_20', kw: 20 },
{ label: 'Pellematic Condens 25 kW', value: 'PelleCondens_25', kw: 25 },
{ label: 'Pellematic Condens 32 kW', value: 'PelleCondens_32', kw: 32 },
{ label: 'Pellematic Condens 45 kW', value: 'PelleCondens_45', kw: 45 },
```
</interfaces>
</context>

<tasks>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 1: Verify all four features end-to-end</name>
  <what-built>
    All four features are already implemented and committed in the current HEAD:
    1. GET /csv-columns endpoint (server.py lines 994-1021) — reads most recent CSV from ./history/, returns column headers as JSON
    2. Sensor mapping dropdowns (index.html lines 3857-3890) — each sensor type gets a <select> populated from /csv-columns; saved values restored on re-open
    3. Buffer presets (index.html lines 3699-3710) — all values use Pellaqua_xxx format, labels read "Pellaqua 200 (200 L)" etc.
    4. Pellematic Condens heater models (index.html lines 3688-3692) — 20/25/32/45 kW entries under "OkoFen Pellematic Condens" optgroup

    No code changes needed. Verification only.
  </what-built>
  <how-to-verify>
    1. Start server: `python server.py` in the project directory
    2. Open http://localhost:8080 in browser
    3. Open Settings modal (gear icon)
    4. Scroll to "System Configuration" section
    5. Check Heater model dropdown — confirm "OkoFen Pellematic Condens" group with 20/25/32/45 kW options
    6. Check Buffer type — select "ÖkoFen Pellaqua" and confirm preset dropdown shows "Pellaqua 200 (200 L)" etc. (not "PES_xxx")
    7. Check Sensor Mapping section — each sensor type row should have a dropdown. If at least one CSV exists in ./history/, the dropdowns should list actual column names from that CSV alongside "— Auto-detect —"
    8. To confirm /csv-columns directly: `curl http://localhost:8080/csv-columns` — should return `{"columns": [...]}` with column names if CSV files exist in ./history/, or `{"columns": []}` if not
  </how-to-verify>
  <resume-signal>Type "verified" if all features are working, or describe any issues found</resume-signal>
</task>

</tasks>

<verification>
- GET /csv-columns returns 200 with JSON body containing "columns" array
- Sensor mapping dropdowns populated with CSV column names (or show only Auto-detect if no CSV files in ./history/)
- Buffer preset dropdown under "ÖkoFen Pellaqua" shows Pellaqua_xxx labels
- Heater model dropdown includes "ÖkoFen Pellematic Condens" optgroup with 4 entries
</verification>

<success_criteria>
User confirms all four features work correctly via visual inspection of the Settings modal and curl verification of the /csv-columns endpoint.
</success_criteria>

<output>
After verification, create `.planning/quick/2-add-csv-columns-endpoint-sensor-mapping-/2-SUMMARY.md` noting all four features confirmed working (or listing any gaps found).
</output>
