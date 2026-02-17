# OekoFEN CSV Viewer

## What This Is

A web-based interactive chart viewer for OekoFEN pellet heater CSV data. Users drag & drop a daily CSV file exported by their heater and explore the data through interactive charts with zoom, parameter toggling, and cursor inspection. Replaces the static PNG graphs the heater generates, which are insufficient for diagnosing heating behavior.

## Core Value

Enable the user to visually diagnose why and when the heater fires by interactively exploring temperature curves, pump states, and pellet unit behavior across a single day's data.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Load OekoFEN CSV via drag & drop or file picker (client-side only, no server)
- [ ] Parse semicolon-delimited CSV with German locale decimals (comma as decimal separator)
- [ ] Display interactive time-series charts for selected parameters
- [ ] Pre-built parameter views grouped by system (Boiler, Heating Circuit, Hot Water, Buffer, Pellet Unit)
- [ ] Custom parameter selection beyond pre-built views
- [ ] Show/hide individual parameters on the chart
- [ ] Zoom via click-drag (select time range) and scroll wheel (centered on cursor)
- [ ] Cursor inspection showing values at the current time position
- [ ] Reset zoom to full day view
- [ ] English UI with original German CSV parameter names preserved

### Out of Scope

- Server-side processing — everything runs in the browser
- Multi-day comparison / loading multiple CSVs simultaneously — single day focus
- Data editing or export — read-only visualization
- WPF desktop application — replaced by web approach
- Real-time data streaming from the heater

## Context

- OekoFEN pellet heaters export daily CSV files with naming pattern `touch_YYYYMMDD.csv`
- CSV format: semicolon-separated, ~70 columns, 1-minute sample interval, German locale (commas for decimals)
- Column categories: outside temp (AT), boiler (KT), heating circuit (HK1), hot water (WW1), buffer (PU1), pellet unit (PE1), error codes
- Mix of continuous values (temperatures in C, percentages) and discrete states (pump on/off, status codes)
- First row is headers with units in brackets, e.g. `AT [C]`, `HK1 VL Ist[C]`, `PE1 Modulation[%]`
- Date format in data: `DD.MM.YYYY` with time `HH:MM:SS`
- Existing static PNG graphs from the heater overlay all parameters making it hard to isolate specific events

## Constraints

- **Client-side only**: Must work by opening an HTML file in a browser — no Node.js server, no build step required at runtime
- **File format**: Must handle the specific OekoFEN CSV format (semicolon delimiter, German decimals, encoding with special characters like umlauts)
- **Performance**: ~1440 data points per day (1-minute intervals x 24 hours) across ~70 columns — must render smoothly

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Web-based instead of WPF | Simpler deployment, cross-platform, rich charting ecosystem | -- Pending |
| Client-side only (no server) | Simplest possible deployment — just open a file | -- Pending |
| English UI | User preference, German parameter names preserved from CSV | -- Pending |
| Pre-built views + custom selection | Smart defaults for common diagnostic scenarios, flexibility for edge cases | -- Pending |
| Dual zoom (drag + scroll wheel) | Precise range selection and quick zoom both needed for diagnosis workflow | -- Pending |

---
*Last updated: 2026-02-17 after initialization*
