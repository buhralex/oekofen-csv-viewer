# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-21 after v1.1 started)

**Core value:** Enable the user to visually diagnose why and when the heater fires by interactively exploring temperature curves, pump states, and pellet unit behavior across a single day's data.
**Current focus:** Phase 6 — Download UI and Error Handling

## Current Position

Milestone v1.1 Direct Download — ROADMAP CREATED 2026-02-21
Phase: 6 of 6 (Download UI and Error Handling)
Plan: 2 of 3 complete
Status: Plan 06-02 complete, ready for Plan 06-03
Last activity: 2026-02-24 — Plan 06-02 complete

Progress: [█████░░░░░] 83% (5/6 plans complete)

## Performance Metrics

**Velocity (v1.0 reference):**
- Total plans completed: 13 (v1.0)
- v1.0 phases: 4 phases, 13 plans

**By Phase (v1.0):**

| Phase | Plans | Status |
|-------|-------|--------|
| 1. Foundation | 3/3 | Complete |
| 2. Chart Rendering | 2/2 | Complete |
| 3. Navigation and Interaction | 4/4 | Complete |
| 4. Parameter Management | 4/4 | Complete |

**v1.1 Plans Completed: 5/6**

| Plan | Name | Duration | Tasks | Status |
|------|------|----------|-------|--------|
| 05-01 | Settings Data Layer + Onboarding Prompt | 2min | 2 | Complete |
| 05-02 | Settings Modal UI + Gear Icon Entry Points | 15min | 2 | Complete |
| 05-03 | Pipeline Extraction (onCsvStringAccepted) | 10min | 2 | Complete |
| 06-01 | Fetch Engine (fetchCsv + error helpers) | 8min | 2 | Complete |
| 06-02 | Fetch Controls UI + Wiring | 1min | 2 | Complete |

## Accumulated Context

### Decisions

Full decision log archived in PROJECT.md Key Decisions table.

Key architectural decisions relevant to v1.1:
- **Single HTML file** — no build step; all v1.1 additions are inline edits to `index.html`
- **Settings isolated from AppState** — `_settings` lives at module level with its own `'oekofen-viewer-settings'` localStorage key; AppState resets on file load, settings must not
- **Pipeline extraction first** — `onCsvStringAccepted()` extracted and regression-verified; `fetchCsv()` can now call it as a second caller in Phase 6
- **CORS from file:// is a hard block** — must serve from `http://localhost`; `mode: 'no-cors'` is not a mitigation; document `python -m http.server` in the UI
- **Settings modal follows picker modal pattern** — create/destroy in JS on demand (lines 2326–2513 of index.html are the reference)
- **Rate limit: 2500ms, timestamp guard** — write `_lastFetchAt` only when fetch actually starts; never auto-retry
- **saveSettings() auto-calls dismissOnboarding()** — prompt never reappears after settings are persisted (05-01)
- **openSettingsModal() guarded by typeof check** — onboarding connect button safe until 05-02 adds the function (now defined — guard can remain or be simplified)
- **Settings modal create/destroy pattern** — openSettingsModal() creates modal on demand, closeSettingsModal() removes it; _settingsEscHandler stored at module level to prevent handler leaks
- **API Password uses type=text** — token appears in URL; masking impedes verification with no security gain
- **fetchCsv timestamp guard: _lastFetchAt written before fetch() call** — rate-limit accurate even on immediate network failures (06-01)
- **AbortSignal.timeout(10000) over manual AbortController** — browser handles cleanup; no try/finally needed for controller (06-01)
- **Both 'TimeoutError' and 'AbortError' caught** — Chrome 103-123 fires AbortError, Chrome 124+ fires TimeoutError; both checked for compat (06-01)
- **arrayBuffer() + TextDecoder('windows-1252') mandatory** — response.text() uses UTF-8 default, produces mojibake on OekoFEN CSV degree signs (06-01)
- **Both ip AND password required to show fetch controls** — prevents URL double-slash bug (http://ip:port//command) when password is empty (06-02)
- **showFetchControls() sets display='' (empty string)** — restores natural flow layout rather than hardcoding 'block' (06-02)

### Pending Todos

None.

### Blockers/Concerns

- **CORS header behavior of OekoFEN heater is empirically unverified** — all community integrations are server-side; must test on real device during Phase 6. If heater returns no CORS headers, `python -m http.server` becomes a hard prerequisite for direct download.
- **Chrome 142 Local Network Access** — may block localhost-to-LAN fetch; test Chrome 138+ during Phase 6; document Firefox as primary supported browser if Chrome LNA cannot be resolved.

## Session Continuity

Last session: 2026-02-24
Stopped at: Completed 06-02-PLAN.md (Fetch Controls UI + Wiring)
Resume file: none
