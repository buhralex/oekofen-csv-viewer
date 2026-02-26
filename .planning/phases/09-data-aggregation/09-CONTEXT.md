# Phase 9: Data Aggregation - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

The app derives actionable statistics from stored CSV history — per-day metrics (burner starts, pellet consumption, runtime, temperatures) and multi-day trend patterns. Phase 9 includes both the computation backend (SQLite persistence) and a full Statistics UI tab. Phase 11 (Analysis UI) is a separate concern and not in scope here.

</domain>

<decisions>
## Implementation Decisions

### Burner start detection
- A "start" = rising edge on the burner state column (transition from off → on); each such transition counts as one start
- CSV gaps (missing rows): ignore them — count transitions only on adjacent rows, never infer a start/stop from a gap
- Runtime is read from the `L_runtime` cumulative counter column: daily runtime = last row value − first row value for that day
- State column name and any other burner-related column names: researcher must auto-detect from actual CSV headers (do not hardcode)

### Pellet consumption
- Researcher must inspect CSV headers for a direct pellet consumption counter column (similar to `L_runtime`)
- If a direct counter column exists: use delta (last − first row) per day
- If no direct counter column is found: show N/A — do NOT fall back to runtime-based estimation
- Normalization formula: consumption per degree-day = kg / (18°C − avg_outdoor_temp_for_day)
- Degree-day base temperature: fixed at 18°C (no user configuration)

### Start frequency trend
- Window: all stored complete days (not a rolling window)
- Algorithm: linear regression slope on starts-per-day over time; positive slope = trending up, negative = trending down
- Minimum days before showing trend: 3 complete days; show N/A if fewer days stored
- Partial days excluded from trend calculations (see below)
- Display format in summary: directional indicator + numeric value, e.g. "↑ +0.3 starts/day" or "→ stable"

### Stats storage
- Computed stats stored persistently in SQLite (a `daily_stats` table alongside existing CSV cache)
- Aggregation triggered on two events: (1) after each new CSV download completes, (2) on app startup, backfill any stored days that lack computed stats

### Stats UI — placement and layout
- New "Statistics" tab added alongside the existing chart/daily-view tab
- Layout: summary section at top (period totals + trend indicators), per-day table below
- Table columns (all shown by default): Date, Starts, Runtime, Consumption, Avg Outdoor Temp, Flow/Return Delta
- Table rows are clickable: clicking a row loads that day in the chart tab

### Flow/return temperature delta
- Column names: researcher auto-detects flow and return temperature columns from CSV headers
- Per-day value = daily average of (flow_temp − return_temp) computed across all rows for that day (not limited to active-burner rows)

### Partial-day data handling
- Partial day definition: less than 20 hours of data in the stored CSV
- Partial days: include in the stats table with a visual indicator (e.g. asterisk or "partial" label)
- Partial days: exclude from trend calculations to avoid skewing the regression slope

### Claude's Discretion
- Exact SQLite schema for `daily_stats` table
- How "stable" is defined for the trend indicator (e.g. slope magnitude threshold)
- Visual styling of the partial-day indicator in the table
- Summary section layout details (which totals to show beyond trend)

</decisions>

<specifics>
## Specific Ideas

- `L_runtime` is a known cumulative counter — pellet consumption column (if it exists) should follow the same pattern and be treated identically
- The Statistics tab should let the user drill down: click a day in the table → jump to that day's chart. This is the primary workflow.
- Trend display modeled on compact indicators: "↑ +0.3 starts/day" — not a full chart, just a number with direction

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-data-aggregation*
*Context gathered: 2026-02-26*
