# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-17)

**Core value:** Enable the user to visually diagnose why and when the heater fires by interactively exploring temperature curves, pump states, and pellet unit behavior across a single day's data.
**Current focus:** Phase 1 - Foundation

## Current Position

Phase: 1 of 4 (Foundation)
Plan: 2 of 3 in current phase (01-01 and 01-02 complete, 01-03 remaining)
Status: In progress
Last activity: 2026-02-17 — 01-02 complete: file loading, navigation guard, toast validation, LOAD-01/02/03 satisfied

Progress: [██░░░░░░░░] 14%

## Performance Metrics

**Velocity:**
- Total plans completed: 2
- Average duration: ~23 min
- Total execution time: ~0.75 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 2/3 | ~45 min | ~23 min |

**Recent Trend:**
- Last 5 plans: 01-01 (15 min), 01-02 (~30 min)
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
- [01-02]: Window-level dragover+drop guard must attach to window (not drop zone) — only then does LOAD-03 (outside-zone drops) work
- [01-02]: dragDepth counter pattern used to prevent flicker — increment on dragenter, decrement on dragleave, remove CSS class only at zero
- [01-02]: handleFileDrop() is the single validation entry point for both drag and file picker paths
- [01-02]: onFileAccepted(file) is the handoff boundary — Plan 03 replaces the stub body with the parse pipeline

### Pending Todos

None.

### Blockers/Concerns

- [Phase 1 RESOLVED]: CSV schema validated — ISO-8859-1, semicolon delimiter, trailing semicolons, trailing spaces in column names. Plans reflect actual file format.
- [Phase 1 RESOLVED]: Column group rules hardcoded from real file inspection — HK1, WW1, PU1, PE1 prefix-based; Boiler explicit list.
- [Advisory]: PARS-03 implemented via TextDecoder('windows-1252') not BOM stripping — real file has no BOM. Excel-generated UTF-8 BOM files not handled (future concern if needed).

## Session Continuity

Last session: 2026-02-17
Stopped at: Completed 01-02-PLAN.md — file loading layer complete, LOAD-01/02/03 verified. Next: 01-03 (CSV parse/normalize pipeline).
Resume file: None
