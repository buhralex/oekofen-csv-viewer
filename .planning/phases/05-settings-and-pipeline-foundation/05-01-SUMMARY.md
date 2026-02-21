---
phase: 05-settings-and-pipeline-foundation
plan: "01"
subsystem: ui
tags: [localStorage, settings, onboarding, vanilla-js, single-file]

# Dependency graph
requires: []
provides:
  - "_settings object with ip/port/password at module level"
  - "SETTINGS_KEY = 'oekofen-viewer-settings' constant"
  - "loadSettings() — hydrates _settings from localStorage at init"
  - "saveSettings(ip, port, password) — persists to localStorage, hides onboarding"
  - "Onboarding prompt HTML in drop zone (#onboarding-prompt)"
  - "dismissOnboarding() — sets ONBD_KEY flag, hides prompt"
  - "initOnboardingPrompt() — show/hide prompt based on _settings.ip and ONBD_KEY"
affects:
  - "05-02 (settings modal will call saveSettings and openSettingsModal)"
  - "05-03 (fetchCsv will read _settings.ip, _settings.port, _settings.password)"
  - "06-01 (direct download integration reads _settings)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Module-level settings object isolated from AppState (different lifecycle — AppState resets on file load, settings persist)"
    - "try/catch around all localStorage reads and writes (Safari private mode / QuotaExceededError safety)"
    - "Onboarding visibility gated by two conditions: no _settings.ip AND ONBD_KEY !== 'dismissed'"
    - "Deferred function resolution — saveSettings calls dismissOnboarding() which is declared later; JS function hoisting handles this"

key-files:
  created: []
  modified:
    - "index.html — settings data layer (SETTINGS_KEY, _settings, loadSettings, saveSettings) and onboarding prompt (HTML + JS)"

key-decisions:
  - "_settings lives at module level, NOT inside AppState — AppState resets on file load, settings must persist across sessions"
  - "SETTINGS_KEY = 'oekofen-viewer-settings' kept separate from PREFS_KEY = 'oekofen-viewer-prefs' (different lifecycles)"
  - "saveSettings() auto-calls dismissOnboarding() so the prompt never reappears after settings are saved"
  - "openSettingsModal() guarded by typeof check in onboarding connect button handler — function added in plan 05-02"
  - "Default port stored as string '4321' for consistent URL construction downstream"

patterns-established:
  - "Onboarding pattern: HTML element hidden by default (display:none), initFn() shows it conditionally at runtime"
  - "Two-condition onboarding gate: ip present OR ONBD_KEY dismissed — either condition alone suppresses the prompt"

requirements-completed: [ONBD-01, ONBD-02, ONBD-03, SET-02]

# Metrics
duration: 2min
completed: 2026-02-21
---

# Phase 5 Plan 01: Settings Data Layer and Onboarding Prompt Summary

**localStorage settings persistence (_settings/SETTINGS_KEY/loadSettings/saveSettings) and first-run onboarding prompt in the drop zone with permanent dismiss logic**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-21T20:42:28Z
- **Completed:** 2026-02-21T20:44:22Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Settings data layer in place: `_settings`, `SETTINGS_KEY`, `loadSettings()`, `saveSettings()` — all isolated from AppState
- `loadSettings()` called at init so `_settings` is populated before any v1.1 feature code runs
- Onboarding prompt injected into drop zone, hidden by default, shown on first load when no IP is configured and not previously dismissed
- Prompt hides permanently on: "Connect to heater" click, "No thanks" click, or `saveSettings()` call
- All localStorage calls wrapped in try/catch for Safari private mode and QuotaExceededError safety

## Task Commits

Each task was committed atomically:

1. **Task 1: Settings data layer** - `cdb3106` (feat) — includes Task 2 HTML/JS (both applied to index.html before commit; changes are logically cohesive)

**Plan metadata:** pending (docs commit)

## Files Created/Modified
- `index.html` — Added Settings section (lines 915-990): SETTINGS_KEY, _settings, loadSettings(), saveSettings(), ONBD_KEY, isOnboardingDismissed(), dismissOnboarding(), initOnboardingPrompt(); added #onboarding-prompt HTML in drop zone; added loadSettings() + initOnboardingPrompt() calls at init

## Decisions Made
- `_settings` at module level, NOT AppState — AppState resets on file load, settings must not
- `saveSettings()` calls `dismissOnboarding()` at the end so the onboarding prompt is hidden once settings are persisted
- `openSettingsModal()` called with `typeof` guard in connect button handler — function added in plan 05-02
- Default port stored as string `'4321'` for consistent URL construction downstream

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `_settings`, `SETTINGS_KEY`, `loadSettings`, `saveSettings` are ready for plan 05-02 (settings modal) and plan 05-03 (pipeline extraction)
- `openSettingsModal()` referenced in onboarding button handler but not yet defined — will be added in plan 05-02 (typeof guard prevents runtime errors)
- All v1.0 file-drop functionality unchanged

---
*Phase: 05-settings-and-pipeline-foundation*
*Completed: 2026-02-21*
