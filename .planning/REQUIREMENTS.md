# Requirements: OekoFEN CSV Viewer

**Defined:** 2026-02-21
**Core Value:** Enable the user to visually diagnose why and when the heater fires by interactively exploring temperature curves, pump states, and pellet unit behavior across a single day's data.

## v1.1 Requirements

### Onboarding (ONBD)

- [x] **ONBD-01**: On first load (no settings configured), the app presents a prompt inviting the user to set up a heater connection, alongside the existing drop zone
- [x] **ONBD-02**: Choosing "Connect to heater" from the prompt opens the settings panel
- [x] **ONBD-03**: The onboarding prompt is not shown again once settings are saved or the prompt is dismissed

### Settings (SET)

- [x] **SET-01**: User can open a settings panel to enter heater connection details (IP Address, Port, API Password)
- [x] **SET-02**: Connection settings are persisted to localStorage and restored on page load
- [x] **SET-03**: Settings panel is accessible from a gear icon in the app header at all times

### Connection (CONN)

- [x] **CONN-01**: When settings are configured, a log period selector (Today, Yesterday, Log 0–3) and download button are shown alongside the drop zone
- [x] **CONN-02**: User can trigger a direct CSV download from the heater API for the selected log period
- [x] **CONN-03**: The download button is disabled for 2500ms after each request to enforce the API rate limit
- [x] **CONN-04**: Downloaded CSV is loaded into the chart using the same pipeline as drag-and-drop
- [x] **CONN-05**: Drag-and-drop and file picker loading remain available at all times regardless of settings
- [x] **CONN-06**: A local Python proxy server (`server.py`) is provided that serves the app and proxies heater API requests server-side, bypassing browser CORS restrictions. Phase 06-03 empirical testing confirmed the OekoFEN heater returns no `Access-Control-Allow-Origin` headers, making a server-side proxy the only viable fetch strategy.

### Error Handling (ERR)

- [x] **ERR-01**: User sees an actionable message when fetch fails due to `file://` origin (app opened directly as a file instead of via server.py), with instruction to run `python server.py` or double-click `start.bat`
- [x] **ERR-02**: User sees a clear error when the heater is unreachable or request times out (10s timeout)
- [x] **ERR-03**: User sees a clear error when the API password is wrong (heater returns 404)
- [x] **ERR-04**: User sees a clear error when the rate limit is exceeded (heater returns 401)

## v1.2 Requirements

### Data Accumulation (DACC)

- [x] **DACC-01**: App stores each day's CSV in IndexedDB as the user fetches from the heater or manually uploads — data persists across sessions
- [x] **DACC-02**: App shows how many days are stored and the date range covered
- [x] **DACC-03**: User can clear stored history
- [x] **DACC-04**: Server can automatically fetch and store each day's log on a schedule for always-on VM use

### Settings Baseline (BASE)

- [x] **BASE-01**: User can load the heater settings `.txt` export (drag-drop or file picker) as a one-time baseline
- [x] **BASE-02**: App parses the settings text into structured key-value pairs by section (Heizkreis, Warmwasser, CONDENS, etc.)
- [x] **BASE-03**: User can reload settings at any time after changing them on the heater

### Data Aggregation (AGGR)

- [x] **AGGR-01**: App computes per-day statistics from stored CSVs: starts/day, pellet consumption, burner runtime, average outdoor temp, flow/return temp efficiency
- [x] **AGGR-02**: App identifies multi-day patterns: start frequency trend, consumption normalized to outdoor temperature

### AI Integration (AICO)

- [x] **AICO-01**: User configures AI backend in Settings — Ollama endpoint (local) or Claude API key (cloud)
- [x] **AICO-02**: AI receives structured context only — aggregated statistics and parsed settings; raw CSV rows are never sent
- [x] **AICO-03**: System prompt encodes curated OekoFEN expert knowledge: start frequency norms, heating curve interpretation, pellet consumption benchmarks, maintenance indicators — no Öko Modus recommendations
- [x] **AICO-04**: User triggers analysis with one button and receives structured recommendations

### Analysis Panel (ANLS)

- [ ] **ANLS-01**: Analysis panel is a full-screen view replacing the chart, with navigation back to the chart
- [ ] **ANLS-02**: Recommendations shown as a prioritized list — each with title, explanation, setting name, and suggested value
- [ ] **ANLS-03**: Maintenance alerts (fan speed drift, ash fill trend, start failure patterns) shown in a separate section
- [ ] **ANLS-04**: Panel shows when analysis was last run and how many days of data it used

## v2 Requirements

### Connection Enhancements

- **CONN-EXT-01**: Rate limit cooldown countdown indicator on the download button
- **CONN-EXT-02**: "Test connection" button in settings panel to verify connectivity before downloading
- **CONN-EXT-03**: Last-used log period is remembered across page reloads

## Out of Scope

> **Note (updated Phase 06):** The original "client-side only" constraint for proxy/backend was invalidated by empirical testing in Phase 06-03, which confirmed the OekoFEN heater returns no CORS headers. `server.py` is now the required startup method. See CONN-06.

| Feature | Reason |
|---------|--------|
| HTTPS / SSL for heater connection | Embedded device firmware — no control over TLS |
| Multiple heater profiles | Single-user, single-heater tool |
| Auto-refresh / polling | Manual trigger only; rate limit makes polling impractical |
| Password masking (type="password") | API password is a URL token, not a user credential — masking provides no benefit |
| `.save` ZIP as data source | The ZIP bundles CSVs that duplicate what the API already provides; settings come from `.txt` only |
| Öko Modus recommendations | Known to underperform in practice per community feedback; excluded from AI knowledge base |
| Writing settings back to heater | Heater has no write API; settings changes must be made on the device |
| Multi-season / year-over-year comparison | Out of scope until multi-day history is proven useful |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ONBD-01 | Phase 5 | Complete |
| ONBD-02 | Phase 5 | Complete |
| ONBD-03 | Phase 5 | Complete |
| SET-01 | Phase 5 | Complete |
| SET-02 | Phase 5 | Complete |
| SET-03 | Phase 5 | Complete |
| CONN-04 | Phase 5 | Complete |
| CONN-05 | Phase 5 | Complete |
| CONN-06 | Phase 6 | Complete |
| CONN-01 | Phase 6 | Complete |
| CONN-02 | Phase 6 | Complete |
| CONN-03 | Phase 6 | Complete |
| ERR-01 | Phase 6 | Complete |
| ERR-02 | Phase 6 | Complete |
| ERR-03 | Phase 6 | Complete |
| ERR-04 | Phase 6 | Complete |
| DACC-01 | Phase 7 | Complete |
| DACC-02 | Phase 7 | Complete |
| DACC-03 | Phase 7 | Complete |
| DACC-04 | Phase 7 | Complete |
| BASE-01 | Phase 8 | Complete |
| BASE-02 | Phase 8 | Complete |
| BASE-03 | Phase 8 | Complete |
| AGGR-01 | Phase 9 | Complete |
| AGGR-02 | Phase 9 | Complete |
| AICO-01 | Phase 10 | Complete |
| AICO-02 | Phase 10 | Complete |
| AICO-03 | Phase 10 | Complete |
| AICO-04 | Phase 10 | Complete |
| ANLS-01 | Phase 11 | Pending |
| ANLS-02 | Phase 11 | Pending |
| ANLS-03 | Phase 11 | Pending |
| ANLS-04 | Phase 11 | Pending |

**Coverage:**
- v1.1 requirements: 16 total
- Mapped to phases: 16 (Phase 5: 8, Phase 6: 8)
- v1.2 requirements: 13 total
- Mapped to phases: 13 (Phase 7: 4, Phase 8: 3, Phase 9: 2, Phase 10: 4, Phase 11: 4)
- Unmapped: 0

---
*Requirements defined: 2026-02-21*
*Last updated: 2026-02-25 — v1.2 requirements mapped to Phases 7-11*
