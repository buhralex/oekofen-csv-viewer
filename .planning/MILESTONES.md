# Milestones

## v1.0 MVP (Shipped: 2026-02-21)

**Phases completed:** 4 phases, 13 plans
**Git range:** a897779 → ee4f650 (72 commits)
**Timeline:** 5 days (2026-02-17 → 2026-02-21)
**Deliverable:** `index.html` — 2,542 lines, fully self-contained browser app

**Key accomplishments:**
1. Complete OekoFEN CSV parsing pipeline — Windows-1252 decoding, German decimal normalization (comma→dot), timezone-safe UTC timestamp reconstruction from `DD.MM.YYYY`+`HH:MM:SS` columns, columnar data model with group/type classification
2. uPlot dual-axis interactive chart — 9 default series, group-based color palette, binary step-band rendering for burner state (BR), responsive resize via debounced `setSize()`
3. Full navigation suite — drag-to-zoom with 5-min floor, cursor-centered scroll-wheel zoom, floating value tooltip with left/right boundary flip, full-day minimap with bidirectional zoom sync and drag-to-pan
4. Pre-built diagnostic system views (All / Boiler / Heating Circuit / Hot Water / Buffer / Pellet Unit), legend click toggling via event delegation, custom parameter picker across all 64+ CSV columns, localStorage persistence of view and series state

**Requirements shipped:** 22/22 v1 requirements (LOAD, PARS, CHRT, NAVG, PARM, INTF)

---

