# Roadmap: OekoFEN CSV Viewer

## Overview

Four phases built on a strict one-way data pipeline. Phase 1 establishes the project scaffold and verifies the entire parse/normalize pipeline against a real OekoFEN file — every downstream phase depends on this being correct. Phase 2 creates the uPlot chart instance with the axis architecture locked in (dual-axis, step rendering for binary states) before any interactions are built on top. Phase 3 adds the full interactive experience: zoom, cursor inspection, and the minimap overview. Phase 4 completes the parameter management UX: pre-built views, series toggling, custom selection, and localStorage persistence.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Project scaffold, file loading, and the verified CSV parse/normalize pipeline
- [ ] **Phase 2: Chart Rendering** - uPlot instance with axis architecture, step rendering for binary columns, and series builder
- [ ] **Phase 3: Navigation and Interaction** - Zoom (drag + scroll), cursor crosshair with tooltip, and minimap overview
- [ ] **Phase 4: Parameter Management** - Pre-built views, series show/hide, custom parameter selection, and localStorage persistence

## Phase Details

### Phase 1: Foundation
**Goal**: Users can load an OekoFEN CSV file and the application correctly parses all data into a verified in-memory model ready for charting
**Depends on**: Nothing (first phase)
**Requirements**: LOAD-01, LOAD-02, LOAD-03, PARS-01, PARS-02, PARS-03, PARS-04, PARS-05, INTF-01, INTF-02
**Success Criteria** (what must be TRUE):
  1. User can drag and drop a `touch_YYYYMMDD.csv` file onto the page and the file is accepted without the browser navigating away
  2. User can click a file picker button and select a CSV file as an alternative to drag-and-drop
  3. Dropping a file outside the designated drop zone does not trigger browser navigation
  4. After loading a real OekoFEN CSV, the first parsed column header equals `AT [C]` exactly (no invisible BOM prefix), German decimal values like `23,5` parse to `23.5`, and timestamps reconstruct correctly as `00:00` to `23:59` independent of system timezone
  5. The UI displays in English and shows original German CSV parameter names (e.g., `HK1 VL Ist[C]`) without translation
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md — Project scaffold: single HTML file, vendored uPlot 1.6.32 and PapaParse 5.5.3, AppState singleton
- [x] 01-02-PLAN.md — File loading: drag-and-drop zone, file picker button, window-level navigation guard, toast error system
- [x] 01-03-PLAN.md — CSV parse and normalize pipeline: Windows-1252 decoding, semicolon delimiter, German decimal converter, UTC timestamp reconstruction, columnar data model

### Phase 2: Chart Rendering
**Goal**: Users can see loaded CSV data rendered as interactive line charts with correct axis architecture and visual distinction between continuous and binary series
**Depends on**: Phase 1
**Requirements**: CHRT-01, CHRT-02, CHRT-03, CHRT-04
**Success Criteria** (what must be TRUE):
  1. User can see selected parameters rendered as line charts against a time axis labeled in HH:MM format
  2. Binary and discrete columns (pump on/off, status codes) render as step charts, visually distinct from interpolated temperature lines
  3. The chart resizes and redraws correctly when the browser window is resized
  4. The chart renders without perceptible lag with up to 70 columns and 1440 data points loaded
**Plans**: 2 plans

Plans:
- [x] 02-01-PLAN.md — Series builder + uPlot instance: buildChartData(), createChart(), destroyChart(), dual-axis architecture, binary band rendering for BR
- [ ] 02-02-PLAN.md — Responsive resize, performance validation, and visual verification checkpoint [Task 1 complete, paused at human-verify checkpoint]

### Phase 3: Navigation and Interaction
**Goal**: Users can precisely navigate the time axis to isolate heating events using drag-zoom, scroll-zoom, cursor inspection, and the full-day minimap
**Depends on**: Phase 2
**Requirements**: NAVG-01, NAVG-02, NAVG-03, NAVG-04, NAVG-05
**Success Criteria** (what must be TRUE):
  1. User can drag on the chart to select a time range and zoom in to that range
  2. User can scroll the mouse wheel over the chart to zoom in/out centered on the cursor position without scrolling the page
  3. User can click a reset button (or double-click the chart) to return to the full-day view
  4. User can move the cursor over the chart and see a crosshair with a tooltip showing the values of all currently visible series at that time position
  5. User can see a minimap overview beneath the chart showing the full day with the current zoom range highlighted
**Plans**: TBD

Plans:
- [ ] 03-01: Drag-range zoom and reset — uPlot select hook, zoom state in app store, reset button wiring
- [ ] 03-02: Scroll-wheel zoom plugin — inline wheel-zoom plugin from uPlot demo, cursor-centered zoom, page-scroll conflict guard
- [ ] 03-03: Cursor crosshair and tooltip — uPlot cursor plugin, tooltip showing visible series values at cursor position
- [ ] 03-04: Minimap overview — secondary uPlot instance or canvas brush widget showing full day with zoom region highlighted

### Phase 4: Parameter Management
**Goal**: Users can switch between pre-built diagnostic views and customize exactly which parameters are visible, with their selections remembered across page reloads
**Depends on**: Phase 3
**Requirements**: PARM-01, PARM-02, PARM-03, PARM-04
**Success Criteria** (what must be TRUE):
  1. User can click a tab or button to switch to a pre-built view (Boiler, Heating Circuit, Hot Water, Buffer, Pellet Unit) and see only the relevant parameters for that system
  2. User can click individual series in the legend to show or hide them on the chart, with the zoom range preserved on toggle
  3. User can open a parameter selector and choose any column from the loaded CSV to add to the current view beyond the pre-built defaults
  4. After a page reload, the previously selected view and visible series are restored automatically from localStorage
**Plans**: TBD

Plans:
- [ ] 04-01: Pre-built view tabs — view definition map (preset name to column list), tab bar UI, view switching wired to series builder
- [ ] 04-02: Series show/hide — legend click handlers, setSeries() calls (no chart recreate), zoom preservation on toggle
- [ ] 04-03: Custom parameter selection — column list panel showing all parsed columns, add/remove to active view
- [ ] 04-04: localStorage persistence — serialize active view and visible series on change, restore on file load

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | Complete    | 2026-02-17 |
| 2. Chart Rendering | 1/2 | In progress (02-02 at checkpoint) | - |
| 3. Navigation and Interaction | 0/4 | Not started | - |
| 4. Parameter Management | 0/4 | Not started | - |
