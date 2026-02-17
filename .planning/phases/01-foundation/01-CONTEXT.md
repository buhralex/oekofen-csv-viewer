# Phase 1: Foundation - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Project scaffold, file loading (drag-and-drop + file picker), and the complete CSV parse/normalize pipeline. Delivers a verified in-memory columnar data model ready for charting. No chart rendering, no zoom, no parameter toggling — those are Phases 2-4.

</domain>

<decisions>
## Implementation Decisions

### Drop zone appearance
- Claude decides landing page layout (full-page drop zone vs compact)
- Claude decides theme (dark vs light) — optimize for chart readability
- Drag-over visual feedback is required: highlight the drop zone when a file is being dragged over the page
- After file loads, drop zone collapses to a compact header bar showing filename + "Load another" option
- The chart area takes over the main viewport after loading

### Error feedback
- Wrong file type: toast notification that auto-dismisses after a few seconds
- If user drops a .png image: show specific message "This is a graph image. Drop the CSV file (touch_*.csv) instead"
- Non-OekoFEN CSV: warn "This doesn't look like OekoFEN data" but proceed with parsing anyway
- Parse errors (unparseable values): skip the bad values (treat as null/gap in chart), show count in status bar: "3 rows had parse issues"
- Only accept .csv files as valid input; all other file types get a toast error

### Post-load experience
- Show a data summary after successful load: file date and name, row & column counts, time range, column groups found with counts
- Claude decides whether summary is a standalone screen or compact info bar
- When loading a new file (replacing current), keep the current view settings (don't reset to defaults)

### Column grouping rules
- Prefix-based auto-grouping:
  - **Boiler**: AT, ATakt, KT (Ist/Soll), BR (burn status 0/1), Sperrzeit (lock boolean), PE1_BR1
  - **Heating Circuit (HK1)**: all columns starting with `HK1`
  - **Hot Water (WW1)**: all columns starting with `WW1`
  - **Buffer (PU1)**: all columns starting with `PU1`
  - **Pellet Unit (PE1)**: all columns starting with `PE1` (kept as one group, ~30 columns)
- Datum and Zeit are timestamp columns — used for the X-axis, not selectable as chart parameters
- Fehler1/2/3 (error columns): ignored for now — not shown in any pre-built view
- Zubrp1 Pumpe: ignored for now
- BR is a binary column (1=burning, 0=off) — must be classified as discrete/step for chart rendering
- Sperrzeit is a binary column (1=blocked, 0=allowed) — same treatment as BR
- PE1 group stays as one group (not split into sub-groups)

### Claude's Discretion
- Landing page layout and visual design
- Theme choice (dark vs light)
- Data summary layout (standalone vs info bar)
- Exact toast notification styling and timing
- Column ignore/configuration mechanism (if implemented)

</decisions>

<specifics>
## Specific Ideas

- User described BR as "BuRn" — 1 means heater is burning, 0 means off. This is a key diagnostic signal.
- Sperrzeit represents user-defined schedule blocking — when the heater is not allowed to run. Another key diagnostic column.
- User suggested a .ignore file or config file for disabling columns by default — worth considering as a simple JSON config that excludes columns from views.
- The sample file `./Files/touch_20260216.csv` must be used as the real test file for verifying BOM stripping, German decimal conversion, and timestamp parsing.

</specifics>

<deferred>
## Deferred Ideas

- Column ignore/config file (.ignore or JSON) to disable columns by default — could be Phase 4 (parameter management) or a simple v1.x addition
- Fehler (error) column visualization — future phase or v2
- Zubrp1 Pumpe handling — future investigation

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-02-17*
