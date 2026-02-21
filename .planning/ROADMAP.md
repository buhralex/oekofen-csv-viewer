# Roadmap: OekoFEN CSV Viewer

## Milestones

- ✅ **v1.0 MVP** — Phases 1-4 (shipped 2026-02-21)
- 🚧 **v1.1 Direct Download** — Phases 5-6 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) — SHIPPED 2026-02-21</summary>

- [x] Phase 1: Foundation (3/3 plans) — completed 2026-02-17
- [x] Phase 2: Chart Rendering (2/2 plans) — completed 2026-02-18
- [x] Phase 3: Navigation and Interaction (4/4 plans) — completed 2026-02-19
- [x] Phase 4: Parameter Management (4/4 plans) — completed 2026-02-21

Full details: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### 🚧 v1.1 Direct Download (In Progress)

**Milestone Goal:** Enable users to download CSV files directly from the OekoFEN heater HTTP API, eliminating the need for manual file export.

- [ ] **Phase 5: Settings and Pipeline Foundation** — Settings modal, onboarding prompt, localStorage persistence, and shared CSV pipeline
- [ ] **Phase 6: Download UI and Error Handling** — Fetch UI on drop zone, rate limiting, log period selector, and all error conditions

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
- [ ] 05-03-PLAN.md — Pipeline extraction (onCsvStringAccepted refactor) and regression verification checkpoint

### Phase 6: Download UI and Error Handling
**Goal**: Users can trigger a direct CSV download from the heater for any log period, see clear feedback for all failure conditions, and the rate limit is enforced transparently
**Depends on**: Phase 5
**Requirements**: CONN-01, CONN-02, CONN-03, ERR-01, ERR-02, ERR-03, ERR-04
**Success Criteria** (what must be TRUE):
  1. When settings are configured, a log period selector (Today, Yesterday, Log 0–3) and download button appear alongside the drop zone; when settings are not configured, these controls are not shown
  2. Clicking the download button fetches the selected log period's CSV from the heater and loads it into the chart — identical result to drag-and-dropping the same file
  3. The download button is visibly disabled for 2500ms after each request; a second click within that window shows a user-friendly "please wait" message, not a raw error
  4. When fetch fails due to CORS (file:// origin), the user sees a message explaining the issue and instructing them to serve the app via `python -m http.server`
  5. When the heater is unreachable or the request times out, the user sees a clear actionable error; when the API password is wrong (heater returns 404), the user is directed to check their password in settings
**Plans**: TBD

Plans:
- [ ] 06-01-PLAN.md — fetchCsv() with rate limiter, timeout, and TextDecoder pipeline
- [ ] 06-02-PLAN.md — Drop zone fetch UI (selector, button, loading state) and event wiring
- [ ] 06-03-PLAN.md — Error handling — all failure modes mapped to user-readable messages

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 3/3 | Complete | 2026-02-17 |
| 2. Chart Rendering | v1.0 | 2/2 | Complete | 2026-02-18 |
| 3. Navigation and Interaction | v1.0 | 4/4 | Complete | 2026-02-19 |
| 4. Parameter Management | v1.0 | 4/4 | Complete | 2026-02-21 |
| 5. Settings and Pipeline Foundation | v1.1 | 2/3 | In Progress | - |
| 6. Download UI and Error Handling | v1.1 | 0/3 | Not started | - |
