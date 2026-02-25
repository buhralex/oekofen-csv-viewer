# Roadmap: OekoFEN CSV Viewer

## Milestones

- ✅ **v1.0 MVP** — Phases 1-4 (shipped 2026-02-21)
- ✅ **v1.1 Direct Download** — Phases 5-6 (complete 2026-02-25)
- 🔄 **v1.2 AI Heater Analysis** — Phases 7-11 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) — SHIPPED 2026-02-21</summary>

- [x] Phase 1: Foundation (3/3 plans) — completed 2026-02-17
- [x] Phase 2: Chart Rendering (2/2 plans) — completed 2026-02-18
- [x] Phase 3: Navigation and Interaction (4/4 plans) — completed 2026-02-19
- [x] Phase 4: Parameter Management (4/4 plans) — completed 2026-02-21

Full details: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### ✅ v1.1 Direct Download (Complete 2026-02-25)

**Milestone Goal:** Enable users to download CSV files directly from the OekoFEN heater HTTP API, eliminating the need for manual file export.

- [x] **Phase 5: Settings and Pipeline Foundation** — Settings modal, onboarding prompt, localStorage persistence, and shared CSV pipeline
- [x] **Phase 6: Download UI and Error Handling** — Fetch UI on drop zone, rate limiting, log period selector, and all error conditions (complete 2026-02-25)

### 🔄 v1.2 AI Heater Analysis (In Progress)

**Milestone Goal:** Enable users to get actionable, AI-powered recommendations for pellet savings by analyzing multi-day usage data against their heater's baseline settings.

- [ ] **Phase 7: Data Accumulation** — IndexedDB storage for multi-day CSVs, history UI, clear action, and server-side auto-fetch schedule
- [ ] **Phase 8: Settings Baseline** — Load and parse the heater `.txt` settings export into structured sections
- [ ] **Phase 9: Data Aggregation** — Compute per-day statistics and identify multi-day patterns from stored history
- [ ] **Phase 10: AI Integration** — Configure AI backend, build structured context payload, and trigger analysis
- [ ] **Phase 11: Analysis Panel** — Full-screen panel showing prioritized recommendations, maintenance alerts, and analysis metadata

## Phase Details

### Phase 5: Settings and Pipeline Foundation
**Goal**: Users can configure and persist heater connection settings, see an onboarding prompt on first load, and the existing file-drop pipeline is safely refactored to accept CSV from any source
**Depends on**: Phase 4
**Requirements**: ONBD-01, ONBD-02, ONBD-03, SET-01, SET-02, SET-03, CONN-04, CONN-05
**Success Criteria** (what must be TRUE):
  1. On first load (no settings saved), the user sees a prompt alongside the drop zone inviting them to set up a heater connection; the prompt does not reappear once dismissed or settings are saved
  2. Clicking "Connect to heater" in the prompt, or the gear icon in the app header, opens a settings panel with IP Address, Port, and API Password fields
  3. Connection settings entered in the panel survive a page reload and pre-fill the fields on re-open
  4. Drag-and-drop and file picker loading continue to work exactly as before — no regression in v1.0 file loading behavior
  5. Internally, a single `onCsvStringAccepted()` function processes CSV text from any source, replacing the duplicated pipeline that previously existed only inside `onFileAccepted()`
**Plans**: 3 plans

Plans:
- [x] 05-01-PLAN.md — Settings persistence (_settings, SETTINGS_KEY, loadSettings, saveSettings) and onboarding prompt
- [x] 05-02-PLAN.md — Settings modal UI (openSettingsModal, closeSettingsModal) and gear icon entry points in drop zone and header
- [x] 05-03-PLAN.md — Pipeline extraction (onCsvStringAccepted refactor) and regression verification checkpoint

### Phase 6: Download UI and Error Handling
**Goal**: Users can trigger a direct CSV download from the heater for any log period, see clear feedback for all failure conditions, and the rate limit is enforced transparently
**Depends on**: Phase 5
**Requirements**: CONN-01, CONN-02, CONN-03, ERR-01, ERR-02, ERR-03, ERR-04, CONN-06
**Success Criteria** (what must be TRUE):
  1. When settings are configured, a log period selector (Today, Yesterday, Log 0–3) and download button appear alongside the drop zone; when settings are not configured, these controls are not shown
  2. Clicking the download button fetches the selected log period's CSV from the heater and loads it into the chart — identical result to drag-and-dropping the same file
  3. The download button is visibly disabled for 2500ms after each request; a second click within that window shows a user-friendly "please wait" message, not a raw error
  4. When fetch fails due to CORS (file:// origin), the user sees a message explaining the issue and instructing them to serve the app via `python -m http.server`
  5. When the heater is unreachable or the request times out, the user sees a clear actionable error; when the API password is wrong (heater returns 404), the user is directed to check their password in settings
**Plans**: 5 plans (3 original + 2 gap closure)

Plans:
- [x] 06-01-PLAN.md — fetchCsv() core engine: _lastFetchAt/_rateLimitTimer state vars, all error handling (file://, rate-limit, timeout, HTTP 401/404)
- [x] 06-02-PLAN.md — Fetch controls UI: #fetch-controls HTML in drop zone, showFetchControls/hideFetchControls, event wiring, saveSettings + init block integration
- [x] 06-03-PLAN.md — Empirical device verification checkpoint: all 7 test scenarios including CORS behavior, rate-limit guard, and file-drop regression
- [x] 06-04-PLAN.md — Python proxy server (server.py + start.bat): bypasses OekoFEN heater CORS block server-side
- [x] 06-05-PLAN.md — fetchCsv() proxy wiring in index.html + accurate error messages + end-to-end human verification

### Phase 7: Data Accumulation
**Goal**: Users have a persistent multi-day CSV history that grows automatically as they fetch or upload logs, with visibility into what is stored and the ability to clear it
**Depends on**: Phase 6
**Requirements**: DACC-01, DACC-02, DACC-03, DACC-04
**Success Criteria** (what must be TRUE):
  1. After fetching or uploading a CSV, the day's data is stored in IndexedDB and survives a page reload — re-fetching the same day updates the existing record rather than creating a duplicate
  2. A visible indicator (e.g., "12 days stored: 2026-01-14 – 2026-02-25") shows how many days are in history and the date range covered
  3. Clicking "Clear history" removes all stored records from IndexedDB and resets the indicator to zero
  4. When running via server.py on an always-on VM, the server automatically fetches and stores each day's log on a configurable schedule without user interaction
**Plans**: 3 plans

Plans:
- [ ] 07-01-PLAN.md — IndexedDB storage layer (openHistoryDb, upsertHistoryDay, getAllHistoryDays, clearHistoryDb) + pipeline wiring in onCsvStringAccepted() + history indicator UI with Clear button
- [ ] 07-02-PLAN.md — server.py --schedule flag + background fetch thread + ./history/ disk storage + /history JSON endpoint + /history/YYYYMMDD.csv serve endpoint
- [ ] 07-03-PLAN.md — Browser loadHistoryFromServer() on startup + end-to-end human verification of all four DACC requirements

### Phase 8: Settings Baseline
**Goal**: Users can load their heater's configuration as a one-time baseline and reload it when they change settings on the device
**Depends on**: Phase 6
**Requirements**: BASE-01, BASE-02, BASE-03
**Success Criteria** (what must be TRUE):
  1. User can drag-drop or file-pick the heater's `.txt` settings export and see a confirmation that it was loaded (file name and section count)
  2. The loaded settings are parsed into named sections (Heizkreis, Warmwasser, CONDENS, etc.) with key-value pairs accessible to the rest of the app
  3. User can reload settings at any time — loading a new `.txt` file replaces the previously stored baseline without requiring a page reload
**Plans**: TBD

### Phase 9: Data Aggregation
**Goal**: The app derives actionable statistics from stored CSV history that characterize how the heater has been operating across multiple days
**Depends on**: Phase 7
**Requirements**: AGGR-01, AGGR-02
**Success Criteria** (what must be TRUE):
  1. For each stored day, the app has computed: number of burner starts, pellet consumption estimate, total burner runtime, average outdoor temperature, and average flow/return temperature delta
  2. Across all stored days, the app has identified: whether start frequency is trending up or down over the period, and consumption values normalized against outdoor temperature for fair day-to-day comparison
**Plans**: TBD

### Phase 10: AI Integration
**Goal**: Users can configure an AI backend and trigger an analysis that sends only structured, aggregated context — never raw CSV rows — and receive a structured response
**Depends on**: Phase 8, Phase 9
**Requirements**: AICO-01, AICO-02, AICO-03, AICO-04
**Success Criteria** (what must be TRUE):
  1. In Settings, user can choose between Ollama (local) and Claude API (cloud) as the AI backend and save the endpoint or API key
  2. Clicking "Run Analysis" assembles a payload of aggregated statistics and parsed settings (no raw CSV rows) and sends it to the configured backend
  3. The system prompt sent with every analysis request encodes OekoFEN expert knowledge: start frequency norms, heating curve interpretation, pellet consumption benchmarks, and maintenance indicators — with no Öko Modus recommendations
  4. The response from the AI backend is parsed into structured output (recommendations list and maintenance alerts) consumed by the analysis panel
**Plans**: TBD

### Phase 11: Analysis Panel
**Goal**: Users see a dedicated panel with prioritized, actionable recommendations and maintenance alerts derived from the AI analysis, with clear metadata about the analysis scope
**Depends on**: Phase 10
**Requirements**: ANLS-01, ANLS-02, ANLS-03, ANLS-04
**Success Criteria** (what must be TRUE):
  1. A navigation control switches the view between the chart and the analysis panel; the panel is full-screen and the chart is completely hidden while viewing it
  2. The recommendations section shows a prioritized list where each entry has a title, plain-language explanation, the specific setting name to change, and the suggested value
  3. A separate maintenance alerts section shows any flagged patterns (fan speed drift, ash fill trend, start failure sequences) detected in the analysis
  4. The panel header shows when the analysis was last run (date and time) and how many days of stored data were included in the analysis
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 3/3 | Complete | 2026-02-17 |
| 2. Chart Rendering | v1.0 | 2/2 | Complete | 2026-02-18 |
| 3. Navigation and Interaction | v1.0 | 4/4 | Complete | 2026-02-19 |
| 4. Parameter Management | v1.0 | 4/4 | Complete | 2026-02-21 |
| 5. Settings and Pipeline Foundation | v1.1 | 3/3 | Complete | 2026-02-24 |
| 6. Download UI and Error Handling | v1.1 | 5/5 | Complete | 2026-02-25 |
| 7. Data Accumulation | v1.2 | 0/3 | Not started | - |
| 8. Settings Baseline | v1.2 | 0/? | Not started | - |
| 9. Data Aggregation | v1.2 | 0/? | Not started | - |
| 10. AI Integration | v1.2 | 0/? | Not started | - |
| 11. Analysis Panel | v1.2 | 0/? | Not started | - |
