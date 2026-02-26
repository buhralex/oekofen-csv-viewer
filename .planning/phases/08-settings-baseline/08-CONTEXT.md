# Phase 8: Settings Baseline - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Load, parse, and persistently store the heater's `.txt` settings export as a structured baseline. Users can load it during onboarding and reload it at any time from Settings. Phase scope ends at storage — no AI analysis, no aggregation. The stored baseline will be consumed by Phase 10 (AI Integration) when assembling the analysis payload.

</domain>

<decisions>
## Implementation Decisions

### UI Entry Point
- **Primary path:** Onboarding step after connection setup. After the user saves their heater IP/port/password, the onboarding flow advances to a second step asking: "Want AI analysis? Upload your .txt settings file." This step has a Skip option.
- **Secondary path (reload):** A reload action in the Settings modal for when the user updates settings on the device. Claude decides the specific reload UX within the modal.
- Claude decides the layout and UX of the onboarding step (whether it's a second screen in the same modal or a subsequent prompt).

### Confirmation Feedback
- Persistent status indicator inside the Settings modal (near the reload action): shows filename and loaded state.
- After successful load in onboarding, the step completes and the modal closes/advances automatically — no manual dismiss needed.
- Claude decides what specific info to surface in the confirmation (filename, section count, etc.).

### Persistence
- Stored in `localStorage`, consistent with existing `_settings` storage pattern.
- Full parsed structure stored as JSON — see **Data Structure** below. Phase 10 filters/selects what to include in the AI prompt.
- A module-level `_baseline` variable is loaded from `localStorage` at page startup (like `_settings`). If no baseline is stored, `_baseline` is `null`.

### Data Structure

The OekoFEN `.txt` format contains 5 distinct line types: section headers, key-value settings, options lists (sometimes multi-line), schedule `Tag:` entries, and time blocks (`HH:MM  HH:MM [mode]`). The parser must handle all of them.

Parsed output shape:

```json
{
  "filename": "P0060B5_4C74FE.txt",
  "sectionCount": 6,
  "sections": {
    "Heizkreis HK1": {
      "settings": [
        { "key": "Raumtemp Heizen", "value": "23,0 °C", "options": null },
        { "key": "Solares Heizen / Einschalttemperatur", "value": "80,0 °C", "options": null },
        { "key": "Partyprogramm / Partyprogramm", "value": "Aus", "options": ["Aus", "Ein"] }
      ],
      "schedules": [
        {
          "name": "Heizkreis HK1 Zeit 1",
          "groups": [
            { "days": ["Mo", "Di", "Fr", "Sa", "So"], "blocks": [
                { "from": "00:00", "to": "06:00", "mode": "CF -1°" },
                { "from": "06:00", "to": "22:00", "mode": "CF 0°" }
            ]}
          ]
        }
      ]
    }
  }
}
```

- **Settings**: sub-section settings get path-qualified keys (`Solares Heizen / Einschalttemperatur`) so the AI has context without nested tree traversal. Sub-subsection settings use full path (`Ausgangseinstellungen / Saugturbine / Stromschwelle Min`).
- **Options**: array of allowed values for a setting, or `null` if the setting has no options list. The AI uses this to know what it can suggest.
- **Schedules**: collected per named schedule block (e.g. `Heizkreis HK1 Zeit 1`), grouped by `Tag:` day entries. `mode` on time blocks is `null` for warmwater schedules (plain time windows with no mode suffix).
- **Options lists can be multi-line** — the parser must accumulate lines starting with `[` until the closing `]` is found.

### Parser Design

Use an indent-aware, stack-based parser:
- Track the current sub-section path using an indent-level stack (reset on unindent).
- Detect line types by leading whitespace level and content pattern:
  - `/^-{10,}/` → separator (reset sub-section state)
  - Indent 0, not separator, not `Anlagennummer` → top-level section header
  - `Anlagennummer ...` → file header line, skip
  - Content starts with `[` OR previous options line didn't close `]` yet → options list (accumulate until `]` found)
  - Content matches `/^Tag:\s+(.+)/` → start of a Tag group within current schedule
  - Content matches `/^(\d{2}:\d{2})\s{2,}(\d{2}:\d{2})(?:\s{2,}(.+))?$/` → time block entry
  - Content has 2+ space gap between key and right-side value → setting (key path-qualified by current sub-section stack)
  - Content has no right-side value → sub-section header (push to indent stack)

### Error Handling
- Accept any `.txt` file; attempt to parse it; **fail only if zero top-level sections are detected** after parsing the whole file. Option lists, time blocks, and sub-section headers are expected format elements — do not treat them as parse errors.
- Error messages appear inline within the onboarding step or Settings modal — not as toasts.
- On failed parse, the previously loaded baseline is kept intact (`_baseline` and `localStorage` are not overwritten).

### Claude's Discretion
- Layout and UX of the onboarding step (second screen in modal vs. separate prompt)
- Reload UX inside the Settings modal (button vs. drop zone)
- What specific details appear in the persistent status indicator (filename, section count, date)
- Confirmation display after successful onboarding load

</decisions>

<specifics>
## Specific Ideas

- No specific references — open to standard approaches for the onboarding step and Settings modal UI.

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope.

</deferred>

---

*Phase: 08-settings-baseline*
*Context gathered: 2026-02-26*
