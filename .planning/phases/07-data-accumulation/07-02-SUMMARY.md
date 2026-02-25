---
phase: 07-data-accumulation
plan: "02"
subsystem: server
tags: [scheduled-fetch, history-storage, http-endpoints, argparse, threading]
dependency_graph:
  requires: []
  provides: [server-side-history-accumulation, /history-list-endpoint, /history-csv-serve-endpoint]
  affects: [server.py]
tech_stack:
  added: [argparse, datetime, json, time, threading.Thread]
  patterns: [background-daemon-thread, scheduled-polling, path-traversal-guard, rest-endpoints]
key_files:
  created: []
  modified:
    - server.py
decisions:
  - "Non-csv /history/* requests return 404 to prevent path traversal fallthrough to SimpleHTTPRequestHandler (which normalizes paths and would serve arbitrary files)"
  - "daemon=True on schedule thread ensures clean exit on Ctrl+C with no explicit cleanup"
  - "settings.json is separate from browser localStorage — Python cannot access browser storage"
  - "5-second initial delay before first fetch ensures server socket is bound before first network request"
metrics:
  duration: "9min"
  completed: "2026-02-25"
  tasks_completed: 2
  files_modified: 1
---

# Phase 7 Plan 02: Scheduled Auto-Fetch + /history Endpoints Summary

**One-liner:** server.py --schedule N starts a daemon thread that fetches log_today every N minutes into ./history/YYYYMMDD.csv; /history lists available dates as JSON; /history/YYYYMMDD.csv serves stored CSVs with path-traversal protection.

## What Was Built

Extended `server.py` with:

1. **CLI argument:** `--schedule MINUTES` (via argparse, default 0 = disabled)
2. **Helper functions:** `load_schedule_settings()`, `fetch_and_store_today()`, `run_schedule()`
3. **Background thread:** daemon thread calling `run_schedule()` every N minutes when `--schedule` is set
4. **Disk storage:** `./history/YYYYMMDD.csv` files written from raw heater response bytes
5. **GET /history:** returns JSON array of date strings for all stored `.csv` files
6. **GET /history/YYYYMMDD.csv:** serves stored file with `text/plain; charset=windows-1252` Content-Type
7. **Path traversal protection:** any `/history/*` request not ending in `.csv` returns 404 immediately, preventing fallthrough to `SimpleHTTPRequestHandler` which would normalize `../` and serve arbitrary files

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | `--schedule` flag + background fetch thread + disk storage | aadee46 | server.py |
| 2 | `/history` list endpoint + `/history/*.csv` serve endpoint | aadee46 | server.py |

Note: Both tasks were implemented atomically in a single file write since they both modify `server.py`. The commit covers both tasks.

## Verification Results

All static code checks passed (19/19):
- HISTORY_DIR constant, fetch_and_store_today, run_schedule, load_schedule_settings all present
- argparse, json, time, datetime imports added
- daemon=True thread, /history route, /history/*.csv route, JSON response, windows-1252 Content-Type all present
- os.path.basename traversal guard and non-csv 404 guard present

Live endpoint tests (from first successful test run):
- `GET /history` with empty directory: returns `[]`
- `GET /history` with `20260115.csv` in HISTORY_DIR: returns `["20260115"]`
- `GET /history/20260115.csv`: Content-Type `text/plain; charset=windows-1252`, correct content
- Path traversal `/history/../server.py`: returns HTTP 404

`--schedule` without `settings.json`: prints actionable error, server continues to start normally (confirmed).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Path traversal through SimpleHTTPRequestHandler fallthrough**
- **Found during:** Task 2 verification
- **Issue:** Plan documented path traversal protection via `os.path.basename()`, but `/history/../server.py` doesn't match the `.csv` suffix check, so it falls through to `super().do_GET()` (SimpleHTTPRequestHandler), which normalizes the path to `/server.py` and serves the file — status 200, not 404.
- **Fix:** Added an outer `if parsed.path.startswith('/history/'):` guard that returns 404 immediately for any non-`.csv` path, before the `.csv` suffix check. This prevents any `/history/*` path from reaching `super().do_GET()`.
- **Files modified:** server.py
- **Commit:** aadee46 (included in the same commit)

## Decisions Made

1. **Non-csv /history/* guard returns 404 before suffix check** — prevents path traversal via SimpleHTTPRequestHandler normalization
2. **daemon=True on schedule thread** — no explicit cleanup on Ctrl+C required; Python exits cleanly
3. **settings.json for credentials** — browser localStorage is inaccessible from Python; `settings.json` in same directory as server.py is the correct approach for server-side scheduled fetching
4. **5-second initial delay** — ensures HTTPServer socket is bound before the first fetch attempt

## Self-Check

### Files Exist
- [x] server.py — modified (confirmed)
- [x] .planning/phases/07-data-accumulation/07-02-SUMMARY.md — this file

### Commits Exist
- [x] aadee46 — feat(07-02): add --schedule flag, background fetch thread, and disk storage

## Self-Check: PASSED
