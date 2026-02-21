# OekoFEN CSV Viewer

## What This Is

A web-based interactive chart viewer for OekoFEN pellet heater CSV data. Users drag & drop a daily CSV file exported by their heater and explore temperature curves, pump states, and pellet unit behavior through interactive charts with zoom, parameter toggling, cursor inspection, and a minimap overview. Replaces the static PNG graphs the heater generates, which overlay all parameters and make it impossible to isolate specific heating events.

Shipped as a single self-contained `index.html` — no build step, no server, no dependencies beyond two vendored libraries (uPlot 1.6.32 + PapaParse 5.5.3).

## Core Value

Enable the user to visually diagnose why and when the heater fires by interactively exploring temperature curves, pump states, and pellet unit behavior across a single day's data.

## Requirements

### Validated

- ✓ Load OekoFEN CSV via drag & drop or file picker (client-side only, no server) — v1.0
- ✓ Parse semicolon-delimited CSV with German locale decimals and Windows-1252 encoding — v1.0
- ✓ Display interactive time-series charts for selected parameters against a HH:MM time axis — v1.0
- ✓ Pre-built parameter views grouped by system (Boiler, Heating Circuit, Hot Water, Buffer, Pellet Unit, All) — v1.0
- ✓ Custom parameter selection beyond pre-built views via picker modal — v1.0
- ✓ Show/hide individual parameters on the chart via legend click toggle — v1.0
- ✓ Zoom via click-drag (select time range) and scroll wheel (centered on cursor) — v1.0
- ✓ Cursor inspection showing values of all visible series at current time position — v1.0
- ✓ Reset zoom to full day view (button + double-click) — v1.0
- ✓ Full-day minimap overview with current zoom range highlighted — v1.0
- ✓ localStorage persistence of active view and visible series across page reloads — v1.0
- ✓ English UI with original German CSV parameter names preserved — v1.0

### Active

(None — all v1 requirements shipped. Define in next milestone.)

### Out of Scope

- Server-side processing — everything runs in the browser
- Multi-day comparison / loading multiple CSVs simultaneously — single day focus, browser tabs for comparison
- Data editing or annotations — read-only visualization; browser screenshot for sharing
- WPF desktop application — replaced by web approach
- Real-time data streaming from the heater — file-based only
- Unit conversion (°C to °F) — target user is European, original units correct
- User accounts / login — no server; localStorage is sufficient for single-user tool

## Context

**v1.0 shipped 2026-02-21.**

- Deliverable: `index.html` — 2,542 lines, fully self-contained
- Tech stack: Vanilla JS + HTML/CSS, uPlot 1.6.32 (canvas charting), PapaParse 5.5.3 (CSV)
- Data: OekoFEN CSV — semicolon-delimited, ~70 columns, 1,440 rows/day, Windows-1252 encoding
- Column categories: outside temp (AT), boiler (KT), heating circuit (HK1), hot water (WW1), buffer (PU1), pellet unit (PE1)
- Mix of continuous values (temperatures °C, percentages) and discrete states (pump on/off, binary 0/1)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Web-based instead of WPF | Simpler deployment, cross-platform, rich charting ecosystem | ✓ Good — works in any browser, zero install |
| Client-side only (no server) | Simplest possible deployment — just open a file | ✓ Good — users open `index.html` directly |
| English UI | User preference, German parameter names preserved from CSV | ✓ Good — clean compromise |
| uPlot for charting | Fast canvas rendering, lightweight, no framework dependency | ✓ Good — renders 70×1440 points without lag |
| Single HTML file (no build step) | Zero tooling overhead, easy distribution | ✓ Good — deploy by copying one file |
| Dual zoom (drag + scroll wheel) | Precise range selection and quick zoom both needed for diagnosis | ✓ Good — both modes heavily used |
| Dual Y-axis (continuous left, binary right) | Binary 0/1 states on same scale as temperatures would be invisible | ✓ Good — BR burner band clearly visible |
| Pre-built views + custom selection | Smart defaults for common scenarios, flexibility for edge cases | ✓ Good — All/Boiler/HK1/WW1/PU1/PE1 covers 90% of use cases |
| Event delegation for legend clicks | Single listener on parent, survives uPlot DOM rebuilds | ✓ Good — no listener leak issues |
| Build chart with all columns, hide non-defaults | Picker can show/hide without chart recreate | ✓ Good — zero-latency parameter add/remove |
| localStorage for persistence | No server; survives page reload for same file | ✓ Good — prefs validated against loaded file on restore |

## Constraints

- **Client-side only**: Must work by opening an HTML file in a browser — no Node.js server, no build step required at runtime
- **File format**: Must handle the specific OekoFEN CSV format (semicolon delimiter, German decimals, Windows-1252 encoding with special characters like °, ä, ö, ü)
- **Performance**: ~1440 data points per day (1-minute intervals × 24 hours) across ~70 columns — must render smoothly

---
*Last updated: 2026-02-21 after v1.0 milestone*
