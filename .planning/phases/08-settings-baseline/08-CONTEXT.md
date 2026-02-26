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
- Full parsed sections stored as structured JSON — all sections and all key-value pairs. Phase 10 filters/selects what to include in the AI prompt.
- A module-level `_baseline` variable is loaded from `localStorage` at page startup (like `_settings`). If no baseline is stored, `_baseline` is `null`.

### Error Handling
- Accept any `.txt` file; attempt to parse it; show an error if no recognizable OekoFEN sections are found.
- Parser is strict: fail the entire file on any parse error (a malformed line rejects the whole file, not just that line).
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
