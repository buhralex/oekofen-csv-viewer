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

### Error Handling (ERR)

- [x] **ERR-01**: User sees an actionable message when fetch fails due to CORS (`file://` origin), with instruction to use `python -m http.server`
- [x] **ERR-02**: User sees a clear error when the heater is unreachable or request times out (10s timeout)
- [x] **ERR-03**: User sees a clear error when the API password is wrong (heater returns 404)
- [x] **ERR-04**: User sees a clear error when the rate limit is exceeded (heater returns 401)

## v2 Requirements

### Connection Enhancements

- **CONN-EXT-01**: Rate limit cooldown countdown indicator on the download button
- **CONN-EXT-02**: "Test connection" button in settings panel to verify connectivity before downloading
- **CONN-EXT-03**: Last-used log period is remembered across page reloads

## Out of Scope

| Feature | Reason |
|---------|--------|
| HTTPS / SSL for heater connection | Embedded device firmware — no control over TLS |
| Multiple heater profiles | Single-user, single-heater tool |
| Auto-refresh / polling | Manual trigger only; rate limit makes polling impractical |
| Password masking (type="password") | API password is a URL token, not a user credential — masking provides no benefit |
| Proxy server / backend | Client-side only constraint; users must serve from localhost if CORS is an issue |

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
| CONN-01 | Phase 6 | Complete |
| CONN-02 | Phase 6 | Complete |
| CONN-03 | Phase 6 | Complete |
| ERR-01 | Phase 6 | Complete |
| ERR-02 | Phase 6 | Complete |
| ERR-03 | Phase 6 | Complete |
| ERR-04 | Phase 6 | Complete |

**Coverage:**
- v1.1 requirements: 15 total
- Mapped to phases: 15 (Phase 5: 8, Phase 6: 7)
- Unmapped: 0

---
*Requirements defined: 2026-02-21*
*Last updated: 2026-02-21 — traceability populated after roadmap creation*
