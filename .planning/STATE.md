# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-17)

**Core value:** Enable the user to visually diagnose why and when the heater fires by interactively exploring temperature curves, pump states, and pellet unit behavior across a single day's data.
**Current focus:** Phase 1 - Foundation

## Current Position

Phase: 1 of 4 (Foundation)
Plan: 1 of 3 in current phase (01-01 complete, 01-02 and 01-03 remaining)
Status: In progress
Last activity: 2026-02-17 — 01-01 complete: scaffold, vendor libs, AppState singleton

Progress: [█░░░░░░░░░] 7%

## Performance Metrics

**Velocity:**
- Total plans completed: 1
- Average duration: 15 min
- Total execution time: 0.25 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 1/3 | 15 min | 15 min |

**Recent Trend:**
- Last 5 plans: 01-01 (15 min)
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: Web-based client-side only approach confirmed; uPlot 1.6.32 + PapaParse 5.5.3 selected as the stack
- [Init]: One-way data pipeline architecture mandated: File drop → Parse → Normalize → Data Model → View → Chart
- [Init]: Phase 1 must be verified against a real OekoFEN CSV file before Phase 2 begins — normalizer is highest-risk component
- [01-01]: Dark navy theme (#1a1a2e, #4fc3f7 accent) chosen for chart readability
- [01-01]: CSS custom properties established as theming system — all plans extend :root vars
- [01-01]: UI transition functions showDropZone() / showAppView(filename) defined as the state transition pair for Plans 02+
- [01-01]: showToast() / setStatus() established as feedback primitives for all subsequent plans

### Pending Todos

None.

### Blockers/Concerns

- [Phase 1 RESOLVED]: CSV schema validated — ISO-8859-1, semicolon delimiter, trailing semicolons, trailing spaces in column names. Plans reflect actual file format.
- [Phase 1 RESOLVED]: Column group rules hardcoded from real file inspection — HK1, WW1, PU1, PE1 prefix-based; Boiler explicit list.
- [Advisory]: PARS-03 implemented via TextDecoder('windows-1252') not BOM stripping — real file has no BOM. Excel-generated UTF-8 BOM files not handled (future concern if needed).

## Session Continuity

Last session: 2026-02-17
Stopped at: Completed 01-01-PLAN.md — scaffold, vendor libs, AppState complete. Next: 01-02 (file loading).
Resume file: None
