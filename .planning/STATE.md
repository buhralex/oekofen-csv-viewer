# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-25 after v1.2 started)

**Core value:** Enable the user to visually diagnose why and when the heater fires by interactively exploring temperature curves, pump states, and pellet unit behavior across a single day's data.
**Current focus:** Phase 7 — (v1.2 roadmap pending)

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-02-25 — Milestone v1.2 started

Progress: [░░░░░░░░░░] 0%

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

**v1.1 Plans Completed: 6/7**

| Plan | Name | Duration | Tasks | Status |
|------|------|----------|-------|--------|
| 05-01 | Settings Data Layer + Onboarding Prompt | 2min | 2 | Complete |
| 05-02 | Settings Modal UI + Gear Icon Entry Points | 15min | 2 | Complete |
| 05-03 | Pipeline Extraction (onCsvStringAccepted) | 10min | 2 | Complete |
| 06-01 | Fetch Engine (fetchCsv + error helpers) | 8min | 2 | Complete |
| 06-02 | Fetch Controls UI + Wiring | 1min | 2 | Complete |
| 06-03 | Empirical Device Verification | 10min | 1 | Complete |
| 06-04 | Python Proxy Server (server.py + start.bat) | 2min | 3 | Complete |

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
- **OekoFEN heater confirmed to block CORS (empirical, 06-03)** — no Access-Control-Allow-Origin header returned; direct browser fetch() is impossible; the heater IS reachable (http://10.10.30.3:4321/ctT9/log_today opens in browser tab) but CORS is a server-side block
- **Firefox does NOT bypass CORS (empirical, 06-03)** — both Chrome and Firefox enforce CORS identically; "try Firefox" advice in handleFetchNetworkError is wrong and needs a gap-closure fix
- **Proxy server is now required startup method (06-04)** — server.py provides /proxy?url= endpoint; server-side urlopen bypasses CORS; binds to 127.0.0.1:8080; proxy timeout=15s > fetchCsv timeout=10s so browser-side abort fires first
- **start.bat is the Windows double-click launcher (06-04)** — two-line bat file: @echo off + python server.py; replaces python -m http.server 8080
- **fetchCsv() proxy URL pattern (06-05)** — constructs /proxy?url=encodeURIComponent(heaterUrl); local var renamed heaterUrl; all other fetch logic (rate-limit, timeout, TextDecoder, error mapping) unchanged
- **handleFetchNetworkError() TypeError is heater-unreachable not CORS (06-05)** — message updated to "Could not reach the heater. Check the IP address and port in Settings."; "try Firefox" removed; proxy makes CORS irrelevant
- **file:// pre-flight toast references server.py/start.bat (06-05)** — "Double-click start.bat or run: python server.py" replaces obsolete "python -m http.server 8080"

### Pending Todos

None.

### Blockers/Concerns

- **[RESOLVED 2026-02-24] CORS header behavior of OekoFEN heater** — empirically confirmed: heater does NOT return Access-Control-Allow-Origin headers. Direct browser fetch() is permanently impossible without a CORS proxy or heater firmware update. The heater IS reachable via browser tab (CSV opens at http://10.10.30.3:4321/ctT9/log_today) — the block is strictly CORS. python -m http.server resolves file:// origin errors but NOT CORS from heater.
- **[RESOLVED 2026-02-25 via 06-04] handleFetchNetworkError error message** — proxy server now unblocks CORS permanently; 06-05 will wire fetchCsv to use /proxy and update error messages
- **[RESOLVED as N/A 2026-02-24] Chrome 142 Local Network Access** — CORS block from heater occurs before LNA becomes relevant; LNA is not a separate concern given current architecture.

## Session Continuity

Last session: 2026-02-25
Stopped at: Completed 06-05-PLAN.md (fetchCsv Proxy Wiring) — proxy routing, error messages, and file:// guidance updated; human checkpoint approved end-to-end download; Phase 6 complete
Resume file: none
