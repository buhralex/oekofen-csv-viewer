# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-21 after v1.0 milestone)

**Core value:** Enable the user to visually diagnose why and when the heater fires by interactively exploring temperature curves, pump states, and pellet unit behavior across a single day's data.
**Current focus:** Planning next milestone

## Current Position

Milestone v1.0 MVP — SHIPPED 2026-02-21
All 4 phases complete. 13/13 plans executed.

## Milestone v1.0 Summary

- Phases 1-4 shipped (4 phases, 13 plans, 72 commits)
- Deliverable: `index.html` — 2,542 lines, self-contained browser app
- All 22 v1 requirements delivered
- See: `.planning/MILESTONES.md` for full details

## Accumulated Context

### Decisions

Full decision log archived in PROJECT.md Key Decisions table.

Key architectural decisions that remain relevant:
- **Single HTML file** — no build step; deploy by copying one file
- **uPlot 1.6.32** (vendored) — canvas rendering, dual-axis (left: continuous y, right: binary 0-1)
- **All columns pre-loaded at chart creation** — picker shows/hides without chart recreate
- **Event delegation on .u-legend** — single listener, no accumulation risk across reloads
- **setSelect(opts, false)** — second arg false is CRITICAL to prevent minimap ↔ main chart zoom loop

### Pending Todos

None.

### Blockers/Concerns

None active.

## Session Continuity

Last session: 2026-02-21
Stopped at: v1.0 milestone complete — archived and tagged.
Resume file: none
