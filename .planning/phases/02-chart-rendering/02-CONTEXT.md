# Phase 2: Chart Rendering - Context

**Gathered:** 2026-02-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Render the AppState.dataModel from Phase 1 as an interactive uPlot chart with correct axis architecture, step/band rendering for binary columns, and responsive resize. Does NOT include zoom interactions, cursor tooltip, minimap, or parameter management — those are Phases 3 and 4.

</domain>

<decisions>
## Implementation Decisions

### Axis architecture
- Y-axis scale: auto-scale to the min/max of currently visible series (not fixed 0–100)
- X-axis time labels: adaptive tick density — more labels when zoomed in (uPlot auto-tick behavior)
- Binary y-axis and y-axis side placement: Claude's Discretion (see Claude's Discretion section)

### Default series on load
- Match the OekoFEN static PNG (`Files/graph_20260216.png`) exactly for the default series set
- Series shown: AT [C], KT Ist[C], HK1 flow temperature, HK1 return temperature, PU1 upper buffer temp, PU1 lower buffer temp, PE1 boiler temp, PE1 heating power [%], BR (burner running)
- Reference PNG for exact column names: `Files/graph_20260216.png`
- This is the initial chart state; Phase 4 will add view-switching tabs on top of this default

### Binary state rendering
- BR and Sperrzeit render as **filled bands** (not step lines), matching the OekoFEN PNG style
- Fill opacity: semi-transparent, approximately 30–50%, so temperature lines remain visible through the band
- When the column value is 1 (on), band spans the chart height; when 0 (off), nothing is drawn

### Series visual design
- Chart plot area background: same dark navy as the rest of the app (#1a1a2e) — no separate background for the chart canvas
- Fill opacity for binary bands: ~30–50% (see binary rendering above)
- Color scheme, line thickness, and per-group color assignments: Claude's Discretion (see below)

### Chart chrome
- Legend: floating overlay in the top-left corner of the chart, matching the OekoFEN PNG placement
- Grid lines: both horizontal and vertical, but minimal — low opacity (~15–20%), subtle presence rather than strong lines
- Chart title: formatted date parsed from the filename, e.g. "16.02.2026" (not the raw filename)
- Chart height: Claude's Discretion (see below)

### Claude's Discretion
- **Binary axis architecture**: whether BR/Sperrzeit get a dedicated right-side y-axis (0–1) or share the main axis — pick whichever cleanly separates boolean states from temperature/percentage values
- **Y-axis side**: single left axis, or mirrored — pick for readability in the dark navy theme
- **Color scheme**: assign colors so series groups (AT, Boiler, HK1, PU1, PE1) are visually distinguishable. Dark navy background (#1a1a2e) — avoid dark colors for lines
- **Line thickness**: pick 1–2px based on what's most readable for 8–10 simultaneous lines on dark background
- **Chart height**: size for readability now, but reserve approximately 100–150px at the bottom for the Phase 3 minimap that will be added below the main chart

</decisions>

<specifics>
## Specific Ideas

- "Use the series from the PNG as a starting point — they provide a great overview." Reference: `Files/graph_20260216.png`
- The PNG shows the burner state (BR) as blue filled rectangles — the interactive chart should match this visual pattern
- The OekoFEN PNG uses a floating legend block in the upper-left of the plot area; replicate this placement

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 2 scope.

</deferred>

---

*Phase: 02-chart-rendering*
*Context gathered: 2026-02-18*
