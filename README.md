# OekoFEN CSV Viewer

An interactive chart viewer for ÖkoFEN pellet heater diagnostic data. Load a daily CSV export from your heater — by dragging a saved file onto the page, or by fetching live data directly from the heater — and explore temperature curves, pump states, and pellet unit behavior across the day.

---

## Features

- **Live fetch from heater** — enter your heater's IP address, port, and API password in Settings and download today's log (or any other date) directly from the device
- **Drag & drop** a saved `touch_YYYYMMDD.csv` file to load — or use the file picker
- **Interactive time-series chart** with a HH:MM time axis
- **6 pre-built diagnostic views** — All, Boiler, Heating Circuit, Hot Water, Buffer, Pellet Unit
- **Custom parameter picker** — add any of the 64+ CSV columns to the chart
- **Legend click toggle** — show/hide individual series
- **Drag-to-zoom** — select a time range by clicking and dragging on the chart
- **Scroll-wheel zoom** — zoom in/out centered on the cursor position
- **Full-day minimap** — shows the complete day with the current zoom range highlighted; drag to reposition
- **Cursor tooltip** — shows values of all visible series at the cursor time position
- **Reset zoom** — button or double-click to return to full day view
- **localStorage persistence** — heater settings and active view are remembered across page reloads

---

## Usage

### Option A — Live fetch from heater (recommended)

Fetching directly from the heater requires a local web server to work around browser CORS restrictions. A minimal Python server is included.

**Requirements:** Python 3 (included with most systems)

1. Double-click **`start.bat`** — or run `python server.py` in a terminal
2. Open **http://localhost:8080** in your browser
3. Click the **gear icon** and enter your heater's IP address, port (default `4321`), and API password
4. Click **Fetch today** (or select a different log from the dropdown) to load data

### Option B — Load a saved file

No server required for this mode.

1. Open `index.html` directly in any modern browser
2. Drag your `touch_YYYYMMDD.csv` file onto the page — or click **Choose file**

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
- **`server.py`** — minimal Python 3 stdlib HTTP server that proxies requests to the heater server-side, bypassing browser CORS restrictions; no third-party packages required
- **`start.bat`** — Windows double-click launcher for `server.py`; opens http://localhost:8080 automatically
- **Vendored libraries** — [uPlot 1.6.32](https://github.com/leeoniya/uPlot) (canvas charting) and [PapaParse 5.5.3](https://www.papaparse.com/) (CSV parsing) are included in the repository; no CDN required
- **Client-side only** — all data processing happens in the browser; no data is sent to any external server
- **Dual Y-axis** — continuous values (temperatures, percentages) on the left; binary states (on/off) on the right

---

## License

MIT
