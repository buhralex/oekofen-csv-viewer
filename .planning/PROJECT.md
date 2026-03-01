# OekoFEN CSV Viewer

## What This Is

A web-based tool for OekoFEN pellet heater owners to visualize daily operation data and get AI-powered efficiency recommendations. Users drag & drop (or auto-fetch) daily CSV logs, explore interactive temperature/pump/pellet charts, review multi-day statistics, and trigger an AI analysis that compares operating patterns against their heater's baseline settings to surface specific tuning recommendations.

Runs via `python server.py` + browser at `http://localhost:8080`. Single `index.html` + `server.py` — no build step, no cloud dependency.

## Core Value

Enable the user to visually diagnose why and when the heater fires — and get actionable AI recommendations for reducing pellet consumption — by interactively exploring temperature curves, pump states, and pellet unit behavior across accumulated daily data.

## Requirements

### Validated

- ✓ Load OekoFEN CSV via drag & drop or file picker — v1.0
- ✓ Parse semicolon-delimited CSV with German locale decimals and Windows-1252 encoding — v1.0
- ✓ Display interactive time-series charts with zoom, cursor inspection, minimap, parameter toggling — v1.0
- ✓ Pre-built diagnostic views (Boiler, Heating Circuit, Hot Water, Buffer, Pellet Unit, All) + custom picker — v1.0
- ✓ Settings panel for heater connection (IP, Port, API Password) with localStorage persistence — v1.1
- ✓ Direct CSV download from heater HTTP API for any log period (Today/Yesterday/Log 0–3) — v1.1
- ✓ Python proxy server (server.py) bypasses heater CORS; start.bat launcher — v1.1
- ✓ Full error handling: file:// origin, heater unreachable, wrong password, rate limit — v1.1
- ✓ Multi-day CSV history in IndexedDB (fetch or upload); auto-fetch schedule for always-on VM — v1.2
- ✓ Heater settings .txt baseline loaded and parsed into structured sections — v1.2
- ✓ Per-day stats (starts, runtime, pellet, outdoor temp) with multi-day trend; Statistics panel — v1.2
- ✓ AI backend (Ollama/Claude API) with structured context payload; OekoFEN expert system prompt — v1.2
- ✓ Analysis panel: prioritized recommendations (setting + value chips) + maintenance alerts + metadata — v1.2

### Active (v1.3 candidates)

- [ ] Sensor mapping UI: dynamic table showing all sensor types with column selector (currently text input only)
- [ ] GET /csv-columns endpoint: read most recent CSV headers to populate sensor mapping dropdowns
- [ ] Heater model selector: add Pellematic Condens series (20/25/32/45 kW) to Settings
- [ ] Buffer preset names: fix from PES_xxx to Pellaqua xxx (correct ÖkoFEN product name)
- [ ] Applied changes tracking: persistent log of user-confirmed setting changes (partially implemented as side feature in v1.2)

### Out of Scope

| Feature | Reason |
|---------|--------|
| HTTPS / SSL for heater connection | Embedded firmware — no TLS control |
| Multiple heater profiles | Single-user, single-heater tool |
| Auto-refresh / polling | Rate limit makes polling impractical |
| Writing settings back to heater | Heater has no write API |
| Multi-season / year-over-year comparison | Out of scope until multi-day history proven useful |
| Öko Modus recommendations | Known to underperform; excluded from AI knowledge base |
| `.save` ZIP as data source | Duplicates what the API provides |
| Offline mode | server.py is required; no standalone client mode |

## Context

**v1.2 shipped 2026-02-28.**

- Deliverable: `index.html` (4,560 LOC) + `server.py` (1,230 LOC)
- Tech stack: Vanilla JS + HTML/CSS, uPlot 1.6.32, PapaParse 5.5.3, Python 3 + SQLite
- AI backends: Ollama (local, llama3.2) + Claude API (claude-haiku-4-5)
- Storage: IndexedDB (CSV history), localStorage (settings/baseline/AI config/last analysis), SQLite stats.db
- Data: OekoFEN CSV — semicolon-delimited, ~70 columns, 1,440 rows/day, Windows-1252 encoding

**Known issues / tech debt:**
- `degree_day_consumption` always 0.0 until real pellet counter increments are stored (CSV window issue, not a bug)
- `flow_return_delta` computed but hidden — HK1 RT sensor disabled via firmware
- Sensor mapping UI is a single text input; full dropdown table deferred to v1.3

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Web-based instead of WPF | Simpler deployment, cross-platform | ✓ Good |
| Single HTML file + server.py | Zero tooling; server needed only for CORS proxy | ✓ Good |
| uPlot for charting | Fast canvas, lightweight, no framework | ✓ Good |
| IndexedDB for multi-day storage | localStorage too small for full-day CSVs | ✓ Good |
| SQLite stats engine in server.py | Aggregation in Python; browser gets compact JSON | ✓ Good |
| AI payload = aggregated stats only | Never sends raw CSV; context size manageable | ✓ Good |
| Ollama + Claude API dual backend | Local privacy option + cloud quality option | ✓ Good |
| parseBaselineTxt indent-aware parser | OekoFEN .txt has nested sub-sections | ✓ Good |
| _lastAnalysis persisted to localStorage | Analysis survives page reload | ✓ Good |
| escHtml() for AI content rendering | XSS safety for innerHTML with AI-generated text | ✓ Good |
| OekoFEN heater has no CORS headers (empirical) | Direct browser fetch impossible; proxy required | ✓ Confirmed |
| Öko Modus excluded from system prompt | Community reports it underperforms | ✓ Good |

## Constraints

- **Server required**: Must run via `python server.py`; browser-only mode not viable (CORS from heater)
- **File format**: OekoFEN CSV — semicolon delimiter, German decimals, Windows-1252 encoding
- **Performance**: ~1440 rows/day × ~70 columns — must render smoothly
- **Privacy**: Raw CSV rows never sent to AI; only aggregated stats + parsed settings

---
*Last updated: 2026-02-28 after v1.2 milestone*
