# Requirements: OekoFEN CSV Viewer

**Defined:** 2026-02-17
**Core Value:** Enable the user to visually diagnose why and when the heater fires by interactively exploring temperature curves, pump states, and pellet unit behavior across a single day's data.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### File Loading

- [ ] **LOAD-01**: User can load a CSV file via drag-and-drop onto the page
- [ ] **LOAD-02**: User can load a CSV file via a file picker button
- [ ] **LOAD-03**: Dropping a file outside the drop zone does not navigate the browser away

### CSV Parsing

- [ ] **PARS-01**: Parser handles semicolon-delimited CSV format
- [ ] **PARS-02**: Parser converts German locale decimals (comma separator) to correct numeric values
- [ ] **PARS-03**: Parser strips UTF-8 BOM from file start without corrupting the first column header
- [ ] **PARS-04**: Parser extracts date (DD.MM.YYYY) and time (HH:MM:SS) columns into timezone-safe timestamps
- [ ] **PARS-05**: Parser extracts column metadata (name, unit, group) from header strings like `HK1 VL Ist[C]`

### Chart Rendering

- [ ] **CHRT-01**: User can view selected parameters as interactive line charts against a time axis (HH:MM)
- [ ] **CHRT-02**: Binary/discrete columns (pump on/off, status codes) render as step charts, not interpolated lines
- [ ] **CHRT-03**: Chart resizes responsively when the browser window is resized
- [ ] **CHRT-04**: Chart renders smoothly with up to 70 columns x 1440 data points

### Navigation

- [ ] **NAVG-01**: User can zoom into a time range by click-dragging on the chart
- [ ] **NAVG-02**: User can zoom in/out with the scroll wheel, centered on cursor position
- [ ] **NAVG-03**: User can reset zoom to the full day view
- [ ] **NAVG-04**: User can see a cursor crosshair with tooltip showing values of all visible series at the cursor time position
- [ ] **NAVG-05**: User can see an overview/minimap showing the full day with the current zoom range highlighted

### Parameter Management

- [ ] **PARM-01**: User can select a pre-built view to show parameters grouped by system (Boiler, Heating Circuit, Hot Water, Buffer, Pellet Unit)
- [ ] **PARM-02**: User can show/hide individual parameters on the chart via legend clicks
- [ ] **PARM-03**: User can select custom parameters beyond the pre-built views
- [ ] **PARM-04**: User's visible series and active view are persisted in localStorage across page reloads

### Interface

- [x] **INTF-01**: UI is in English
- [x] **INTF-02**: Original German CSV parameter names are displayed (not translated)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Chart Enhancements

- **CHRT-05**: Dual Y-axis rendering (temperatures on left, binary states/percentages on right)
- **NAVG-06**: Keyboard zoom/pan (arrow keys to pan, +/- to zoom)

### Display

- **DISP-01**: Friendly readable column name labels alongside raw German CSV names
- **DISP-02**: Column name mapping toggle (raw vs friendly)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Multi-file comparison | Doubles state complexity; user can open two browser tabs |
| Real-time streaming from heater | Requires server/WebSocket — violates client-side constraint |
| Data editing / annotations | Needs persistence; clipboard copy of cursor values is sufficient |
| AI/ML anomaly detection | Domain-specific heating behavior is complex; false positives erode trust |
| Custom chart types (bar, pie, heatmap) | Time-axis is the diagnostic lens; non-temporal charts hide when events happen |
| Alert thresholds / notifications | Static file viewer has no real-time trigger; use heater's alarm system |
| Export to PDF/image | Browser screenshot handles 95% of use cases for a personal tool |
| User accounts / login | No server; localStorage is sufficient for single-user tool |
| Unit conversion (C to F) | Target user is European; original units from CSV are correct |
| Server-side processing | Everything must run in the browser |
| WPF desktop application | Replaced by web approach |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| LOAD-01 | Phase 1 | Pending |
| LOAD-02 | Phase 1 | Pending |
| LOAD-03 | Phase 1 | Pending |
| PARS-01 | Phase 1 | Pending |
| PARS-02 | Phase 1 | Pending |
| PARS-03 | Phase 1 | Pending |
| PARS-04 | Phase 1 | Pending |
| PARS-05 | Phase 1 | Pending |
| INTF-01 | Phase 1 | Complete (01-01) |
| INTF-02 | Phase 1 | Complete (01-01) |
| CHRT-01 | Phase 2 | Pending |
| CHRT-02 | Phase 2 | Pending |
| CHRT-03 | Phase 2 | Pending |
| CHRT-04 | Phase 2 | Pending |
| NAVG-01 | Phase 3 | Pending |
| NAVG-02 | Phase 3 | Pending |
| NAVG-03 | Phase 3 | Pending |
| NAVG-04 | Phase 3 | Pending |
| NAVG-05 | Phase 3 | Pending |
| PARM-01 | Phase 4 | Pending |
| PARM-02 | Phase 4 | Pending |
| PARM-03 | Phase 4 | Pending |
| PARM-04 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0

---
*Requirements defined: 2026-02-17*
*Last updated: 2026-02-17 after 01-01 execution — INTF-01, INTF-02 complete*
