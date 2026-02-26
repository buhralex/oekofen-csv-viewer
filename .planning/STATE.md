# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-25 after v1.2 started)

**Core value:** Enable the user to visually diagnose why and when the heater fires by interactively exploring temperature curves, pump states, and pellet unit behavior across a single day's data.
**Current focus:** Phase 7 — Data Accumulation (v1.2 AI Heater Analysis)

## Current Position

Phase: 7 — Data Accumulation
Plan: 03 complete (07-03-SUMMARY.md)
Status: Complete — 3 of 3 plans complete
Last activity: 2026-02-26 — 07-03 loadHistoryFromServer() + Phase 7 end-to-end verification complete

Progress: [███░░░░░░░] 30%

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

**v1.1 Plans Completed: 8/8**

| Plan | Name | Duration | Tasks | Status |
|------|------|----------|-------|--------|
| 05-01 | Settings Data Layer + Onboarding Prompt | 2min | 2 | Complete |
| 05-02 | Settings Modal UI + Gear Icon Entry Points | 15min | 2 | Complete |
| 05-03 | Pipeline Extraction (onCsvStringAccepted) | 10min | 2 | Complete |
| 06-01 | Fetch Engine (fetchCsv + error helpers) | 8min | 2 | Complete |
| 06-02 | Fetch Controls UI + Wiring | 1min | 2 | Complete |
| 06-03 | Empirical Device Verification | 10min | 1 | Complete |
| 06-04 | Python Proxy Server (server.py + start.bat) | 2min | 3 | Complete |
| 06-05 | fetchCsv Proxy Wiring + Error Messages | —min | 2 | Complete |

**v1.2 Plans Completed: 3/?**

| Plan | Name | Duration | Tasks | Status |
|------|------|----------|-------|--------|
| 07-01 | IndexedDB History Storage + Indicator | 2min | 2 | Complete |
| 07-02 | Scheduled Auto-Fetch + /history Endpoints | 9min | 2 | Complete |
| 07-03 | loadHistoryFromServer() Startup Wiring | 5min | 2 | Complete |

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

Key architectural decisions relevant to v1.2:
- **IndexedDB for multi-day storage** — localStorage is too small for multiple full-day CSVs (~70 columns × 1440 rows each); IndexedDB is the correct browser storage for bulk structured data
- **Store CSVs keyed by date** — upsert on date key prevents duplicates when the same day is re-fetched
- **Aggregation computed from stored CSVs, not raw rows** — AGGR layer reads IndexedDB records and produces a compact statistics object; raw rows never leave the browser
- **AI payload is aggregated stats + parsed settings only** — raw CSV rows are never sent to any AI backend; context size stays manageable
- **Phases 7 and 8 are independent** — IndexedDB storage (Phase 7) and settings baseline parser (Phase 8) have no dependency on each other; both must complete before Phase 9 (aggregation) and Phase 10 (AI) can proceed
- **DACC-04 (server-side schedule) extends server.py** — auto-fetch loop added to existing proxy server; no new process needed
- [Phase 07-data-accumulation]: IndexedDB upsert-by-date: keyPath='date' (YYYYMMDD) prevents duplicates; fire-and-forget .then().catch() for storage so chart render never blocked
- [Phase 07-data-accumulation]: parseDateFromCsvString() added as fallback for log_yesterday/log0-log3 commands where command name yields no reliable date
- [Phase 07-data-accumulation]: History indicator Clear button rendered inline by updateHistoryIndicator() — no permanent empty button when history is empty
- [Phase 07-data-accumulation]: /history/* non-csv requests return 404 to prevent path traversal fallthrough to SimpleHTTPRequestHandler which normalizes ../ paths
- [Phase 07-data-accumulation]: loadHistoryFromServer() called without await at startup — fire-and-forget; does not delay page render; updates indicator internally after import
- [Phase 07-data-accumulation]: file:// protocol guard in loadHistoryFromServer() — no-op when opened as local file to prevent fetch console errors
- [Phase 07-data-accumulation]: 3s timeout on /history, 5s on individual CSV fetches — ensures clean fallthrough when server.py is old version without /history endpoint

### Pending Todos

None.

### Blockers/Concerns

- **[RESOLVED 2026-02-24] CORS header behavior of OekoFEN heater** — empirically confirmed: heater does NOT return Access-Control-Allow-Origin headers. Direct browser fetch() is permanently impossible without a CORS proxy or heater firmware update. The heater IS reachable via browser tab (CSV opens at http://10.10.30.3:4321/ctT9/log_today) — the block is strictly CORS. python -m http.server resolves file:// origin errors but NOT CORS from heater.
- **[RESOLVED 2026-02-25 via 06-04] handleFetchNetworkError error message** — proxy server now unblocks CORS permanently; 06-05 wired fetchCsv to use /proxy and updated error messages
- **[RESOLVED as N/A 2026-02-24] Chrome 142 Local Network Access** — CORS block from heater occurs before LNA becomes relevant; LNA is not a separate concern given current architecture.

## Session Continuity

Last session: 2026-02-26
Stopped at: Completed 07-03-PLAN.md — loadHistoryFromServer() startup wiring, Phase 7 end-to-end human verification; Phase 7 Data Accumulation complete
Resume file: none
