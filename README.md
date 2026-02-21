# OekoFEN CSV Viewer

An interactive chart viewer for ÖkoFEN pellet heater diagnostic data. Drag and drop a daily CSV export from your heater and explore temperature curves, pump states, and pellet unit behavior across the day.

**No install. No server. Open `index.html` in a browser.**

---

## Features

- **Drag & drop** a `touch_YYYYMMDD.csv` file to load — or use the file picker
- **Interactive time-series chart** with a HH:MM time axis
- **6 pre-built diagnostic views** — All, Boiler, Heating Circuit, Hot Water, Buffer, Pellet Unit
- **Custom parameter picker** — add any of the 64+ CSV columns to the chart
- **Legend click toggle** — show/hide individual series
- **Drag-to-zoom** — select a time range by clicking and dragging on the chart
- **Scroll-wheel zoom** — zoom in/out centered on the cursor position
- **Full-day minimap** — shows the complete day with the current zoom range highlighted; drag to reposition
- **Cursor tooltip** — shows values of all visible series at the cursor time position
- **Reset zoom** — button or double-click to return to full day view
- **localStorage persistence** — active view and visible series are remembered across page reloads

---

## Usage

1. Download or clone this repository
2. Open `index.html` in any modern browser (Chrome, Firefox, Edge, Safari)
3. Drag your `touch_YYYYMMDD.csv` file onto the page

That's it. No server, no build step, no dependencies to install.

---

## CSV Format

ÖkoFEN pellet heaters export daily diagnostic files with the naming pattern `touch_YYYYMMDD.csv`. The viewer handles the specific format of these files:

| Property | Detail |
|----------|--------|
| Delimiter | Semicolon (`;`) |
| Encoding | Windows-1252 / ISO-8859-1 |
| Decimal separator | German locale comma (`,`) → e.g. `23,5` = 23.5 |
| Date column | `DD.MM.YYYY` format |
| Time column | `HH:MM:SS` format |
| Columns | ~70 parameters including temperatures (°C), percentages, and binary states |
| Rows | ~1,440 per file (one per minute across 24 hours) |

Column groups recognized:

| Group | Prefix |
|-------|--------|
| Boiler | `AT`, `KT`, and general boiler params |
| Heating Circuit | `HK1` |
| Hot Water | `WW1` |
| Buffer | `PU1` |
| Pellet Unit | `PE1` |

---

## Technical Notes

- **Single HTML file** — all application code is in `index.html` (~2,500 lines of vanilla JS + CSS)
- **Vendored libraries** — [uPlot 1.6.32](https://github.com/leeoniya/uPlot) (canvas charting) and [PapaParse 5.5.3](https://www.papaparse.com/) (CSV parsing) are included in the repository; no CDN required
- **Client-side only** — works offline, no data leaves the browser
- **Dual Y-axis** — continuous values (temperatures, percentages) on the left; binary states (on/off) on the right

---

## License

MIT
