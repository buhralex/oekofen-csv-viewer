# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-21 after v1.1 started)

**Core value:** Enable the user to visually diagnose why and when the heater fires by interactively exploring temperature curves, pump states, and pellet unit behavior across a single day's data.
**Current focus:** Phase 5 — Settings and Pipeline Foundation

## Current Position

Milestone v1.1 Direct Download — ROADMAP CREATED 2026-02-21
Phase: 5 of 6 (Settings and Pipeline Foundation)
Plan: 1 of 4 complete (ready for 05-02)
Status: In progress
Last activity: 2026-02-21 — Plan 05-01 complete

Progress: [█░░░░░░░░░] 17% (1/6 plans complete)

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

**v1.1 Plans Completed: 1/6**

| Plan | Name | Duration | Tasks | Status |
|------|------|----------|-------|--------|
| 05-01 | Settings Data Layer + Onboarding Prompt | 2min | 2 | Complete |

## Accumulated Context

### Decisions

Full decision log archived in PROJECT.md Key Decisions table.

Key architectural decisions relevant to v1.1:
- **Single HTML file** — no build step; all v1.1 additions are inline edits to `index.html`
- **Settings isolated from AppState** — `_settings` lives at module level with its own `'oekofen-viewer-settings'` localStorage key; AppState resets on file load, settings must not
- **Pipeline extraction first** — `onCsvStringAccepted()` must be verified regression-free before `fetchCsv()` is added as a second caller
- **CORS from file:// is a hard block** — must serve from `http://localhost`; `mode: 'no-cors'` is not a mitigation; document `python -m http.server` in the UI
- **Settings modal follows picker modal pattern** — create/destroy in JS on demand (lines 2326–2513 of index.html are the reference)
- **Rate limit: 2500ms, timestamp guard** — write `_lastFetchAt` only when fetch actually starts; never auto-retry
- **saveSettings() auto-calls dismissOnboarding()** — prompt never reappears after settings are persisted (05-01)
- **openSettingsModal() guarded by typeof check** — onboarding connect button safe until 05-02 adds the function

### Pending Todos

None.

### Blockers/Concerns

- **CORS header behavior of OekoFEN heater is empirically unverified** — all community integrations are server-side; must test on real device during Phase 6. If heater returns no CORS headers, `python -m http.server` becomes a hard prerequisite for direct download.
- **Chrome 142 Local Network Access** — may block localhost-to-LAN fetch; test Chrome 138+ during Phase 6; document Firefox as primary supported browser if Chrome LNA cannot be resolved.

## Session Continuity

Last session: 2026-02-21
Stopped at: Completed 05-01-PLAN.md (Settings Data Layer + Onboarding Prompt)
Resume file: none
