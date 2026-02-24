---
phase: 06-download-ui-and-error-handling
plan: "02"
subsystem: ui
tags: [fetch, download, drop-zone, settings, show-hide, event-wiring]

# Dependency graph
requires:
  - phase: 06-download-ui-and-error-handling
    plan: "01"
    provides: "fetchCsv(command), setFetchButtonState(), handleFetchHttpError(), handleFetchNetworkError(), _lastFetchAt rate-limit state"
  - phase: 05-settings-and-pipeline-foundation
    provides: "_settings object (ip/port/password), saveSettings(), loadSettings()"
provides:
  - "#fetch-controls div in #drop-message with log-selector (6 options) and fetch-btn"
  - "showFetchControls() and hideFetchControls() toggle functions"
  - "fetch-btn click listener calling fetchCsv(log-selector.value)"
  - "saveSettings() integration: show/hide controls on ip && password"
  - "init block integration: show controls on load when saved settings present"
affects:
  - "06-03 — Error handling / final polish will build on this wired UI"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Show/hide gate: _settings.ip && _settings.password (both required) prevents URL double-slash bug"
    - "Controls hidden by default (display:none in HTML); shown only after auth gate passes"
    - "Fetch controls added inside existing #drop-message div — no new container elements needed"

key-files:
  created: []
  modified:
    - index.html

key-decisions:
  - "Both ip AND password required to show fetch controls (not just ip) — prevents empty password creating malformed URL http://ip:port//command"
  - "fetch-btn event listener uses null guard (if fetchBtn) matching existing settings-btn-drop pattern"
  - "showFetchControls() sets display to empty string (not 'block') to inherit natural flow layout"

patterns-established:
  - "show/hide toggle pair: showX()/hideX() with getElementById + style.display = '' | 'none'"
  - "Init guard pattern: if (_settings.ip && _settings.password) { showFetchControls(); } after loadSettings()"

requirements-completed: [CONN-01, CONN-03]

# Metrics
duration: 1min
completed: 2026-02-24
---

# Phase 6 Plan 02: Fetch Controls UI Summary

**#fetch-controls div wired into drop zone with log period selector, download button, show/hide toggle functions, and saveSettings/init integration — fetchCsv() is now user-triggerable**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-24T21:24:07Z
- **Completed:** 2026-02-24T21:25:21Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- `#fetch-controls` div inserted into `#drop-message` with `display:none` default, containing a 6-option `#log-selector` and `#fetch-btn`
- `showFetchControls()` and `hideFetchControls()` functions added before `setFetchButtonState()` in the Fetch CSV block
- `#fetch-btn` click listener added reading `#log-selector` value and calling `fetchCsv(command)`
- `saveSettings()` updated to call `showFetchControls()` or `hideFetchControls()` based on `_settings.ip && _settings.password`
- Init block updated to call `showFetchControls()` after `loadSettings()` when saved settings include both ip and password

## Task Commits

Each task was committed atomically:

1. **Task 1: Add #fetch-controls HTML and showFetchControls/hideFetchControls functions** - `89da487` (feat)
2. **Task 2: Wire fetch-btn listener, saveSettings visibility, and init block** - `8b74ed3` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `index.html` - Added 43 lines: #fetch-controls HTML (15 lines), show/hide functions (9 lines), fetch-btn listener (8 lines), saveSettings block (6 lines), init guard (3 lines + comment)

## Decisions Made

- Both `_settings.ip` AND `_settings.password` required to show fetch controls — prevents the URL double-slash bug (`http://ip:port//command`) documented in RESEARCH.md Pitfall 4 when password is empty
- `el.style.display = ''` (empty string) used in `showFetchControls()` to restore default flow layout rather than hardcoding `'block'`
- Fetch button wiring uses same `if (fetchBtn)` null guard pattern as existing `settingsBtnDrop` wiring

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Full CONN-01 user flow is complete: Settings gear icon -> modal -> save -> fetch controls appear -> Download button -> fetchCsv fires
- CONN-03 rate-limit guard confirmed working: clicking Download twice within 2500ms triggers "Please wait" toast
- Phase 6 Plan 03 (if any) can test end-to-end error handling against a real OekoFEN heater
- Blocker from STATE.md remains: CORS header behavior of OekoFEN heater empirically unverified; test on real device needed

---
*Phase: 06-download-ui-and-error-handling*
*Completed: 2026-02-24*
