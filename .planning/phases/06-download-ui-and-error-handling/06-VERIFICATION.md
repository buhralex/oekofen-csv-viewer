---
phase: 06-download-ui-and-error-handling
verified: 2026-02-25T10:30:00Z
status: human_needed
score: 5/5 success criteria verified
re_verification: true
  previous_status: gaps_found
  previous_score: 4/5
  gaps_closed:
    - "try Firefox text gone — handleFetchNetworkError() else branch now shows 'Could not reach the heater. Check the IP address and port in Settings.'"
    - "fetchCsv() routes through /proxy?url=encodeURIComponent(heaterUrl) — CORS block bypassed via server-side proxy"
    - "file:// pre-flight toast updated to reference 'Double-click start.bat or run: python server.py'"
    - "server.py created — Python stdlib HTTP server with /proxy endpoint and Access-Control-Allow-Origin: * header"
    - "start.bat created — Windows double-click launcher"
    - "REQUIREMENTS.md updated — CONN-06 added, proxy removed from Out of Scope, ERR-01 updated, coverage count updated to 16"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Download button loads CSV from real OekoFEN heater into chart via proxy"
    expected: "Chart renders with heater data — identical visual result to dragging the same CSV file. DevTools Network tab shows request to /proxy?url=... with HTTP 200."
    why_human: "End-to-end download through the proxy to a real OekoFEN heater on LAN is required to fully satisfy CONN-02. The code path is correctly implemented and the human checkpoint in plan 06-05 was approved, but this verifier cannot confirm hardware behavior programmatically. The 06-05 SUMMARY.md states the checkpoint was approved — but per our critical rules, we do not trust SUMMARY claims alone. If the user already ran this test and approved it, they may mark this item closed."
---

# Phase 6: Download UI and Error Handling — Re-Verification Report

**Phase Goal:** Complete the download UI and error handling — users can download CSV data directly from OekoFEN heater via local proxy server, with clear error messages when things go wrong.
**Verified:** 2026-02-25T10:30:00Z
**Status:** human_needed (all automated checks passed; one item pending human confirmation)
**Re-verification:** Yes — gap closure after previous score 4/5

---

## Summary of Gap Closure

The previous verification (2026-02-24) found one BLOCKER gap: the "try Firefox" text in `handleFetchNetworkError()`. Plans 06-04 and 06-05 were executed to close it. This re-verification confirms every automated claim is correct.

**What was added since the previous verification:**
- `server.py` — Python stdlib proxy server (68 lines, stdlib only)
- `start.bat` — Windows double-click launcher (2 lines)
- `.planning/REQUIREMENTS.md` — CONN-06 added, proxy removed from Out of Scope, ERR-01 updated, coverage count 15 -> 16
- `index.html` — three targeted changes: proxy URL construction, file:// toast message, handleFetchNetworkError() else branch

---

## Goal Achievement

### Observable Truths (from Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | When settings are configured, log period selector + download button appear; when not configured, controls hidden | VERIFIED | `#fetch-controls` at line 867 with `display:none` default; `showFetchControls()`/`hideFetchControls()` called from `saveSettings()` (lines 972-977) and init block (lines 2929-2931) gated on `_settings.ip && _settings.password` |
| 2 | Clicking Download fetches selected log period CSV from heater via proxy and loads into chart | VERIFIED (code) / HUMAN NEEDED (hardware) | Code path: `fetchCsv()` builds `/proxy?url=encodeURIComponent(heaterUrl)` (line 2846) -> `fetch(url, { signal: AbortSignal.timeout(10000) })` (line 2850) -> `arrayBuffer()` + `TextDecoder('windows-1252')` (lines 2860-2861) -> `onCsvStringAccepted()` (line 2873). Proxy: `server.py` lines 41-49 — `urlopen(target_url)` server-side, returns bytes with `Access-Control-Allow-Origin: *`. Human checkpoint in 06-05 SUMMARY stated approved. |
| 3 | Download button disabled 2500ms after each request; second click shows "please wait" | VERIFIED | `_lastFetchAt` written at line 2839 before fetch; rate-limit guard at lines 2833-2837; `finally` block at lines 2877-2882 restores button via `setTimeout` |
| 4 | When fetch fails due to file:// origin, user sees actionable message referencing server.py/start.bat | VERIFIED | Protocol pre-flight at line 2821 (`window.location.protocol === 'file:'`); toast at lines 2823-2826 says "Double-click start.bat or run: python server.py then open http://localhost:8080 in your browser." "python -m http.server" appears 0 times in index.html. |
| 5 | Heater unreachable/timeout: clear error; wrong password (404): directed to check settings; rate-limited (401): wait message | VERIFIED | Timeout: `AbortSignal.timeout(10000)` line 2850, dual `TimeoutError`/`AbortError` catch line 2802, message line 2805 correct. HTTP 404: line 2793 correct. HTTP 401: line 2790 correct. Network failure/unreachable: line 2812 "Could not reach the heater. Check the IP address and port in Settings." — "try Firefox" appears 0 times. |

**Score:** 5/5 truths verified (Criterion 2 hardware end-to-end requires human confirmation — code path is complete and correct)

---

## Required Artifacts

### Plan 06-01 Artifacts (regression check)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `index.html` | `fetchCsv` async function + `_lastFetchAt`/`_rateLimitTimer` module-level vars + `setFetchButtonState` | VERIFIED | Lines 940-941: vars at module scope. Line 2819: `async function fetchCsv`. Line 2776: `function setFetchButtonState`. |
| `index.html` | `handleFetchHttpError` and `handleFetchNetworkError` helpers | VERIFIED | Line 2788: `handleFetchHttpError` — correct 401/404 mapping. Line 2801: `handleFetchNetworkError` — timeout branch correct; else branch updated to "Could not reach the heater" — no "try Firefox". |

### Plan 06-02 Artifacts (regression check)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `index.html` | `#fetch-controls` div in `#drop-message` with `display:none` default | VERIFIED | Line 867: `<div id="fetch-controls" style="display:none; ...">` inside `#drop-message`. 6 options present: log_today, log_yesterday, log0, log1, log2, log3. |
| `index.html` | `showFetchControls()` and `hideFetchControls()` functions | VERIFIED | Lines 2766-2774: both functions defined. |
| `index.html` | `fetch-btn` click event listener wired to `fetchCsv()` | VERIFIED | Lines 2917-2922: listener reads `#log-selector` value, calls `fetchCsv(command)`. |

### Plan 06-04 Artifacts (new — gap closure)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `server.py` | Python stdlib proxy server, min 30 lines | VERIFIED | 69 lines. Contains: `urlopen`, `/proxy` route, `webbrowser.open`, `SimpleHTTPRequestHandler`, `Access-Control-Allow-Origin: *`. Binds to `127.0.0.1:8080`. Uses only stdlib: `http.server`, `urllib.request`, `urllib.parse`, `webbrowser`, `threading`, `os`. |
| `start.bat` | Windows double-click launcher, min 2 lines | VERIFIED | 2 lines: `@echo off` and `python server.py`. No other content. |
| `.planning/REQUIREMENTS.md` | Contains CONN-06 | VERIFIED | Line 27: CONN-06 defined. "Proxy server / backend" appears 0 times. Coverage count: 16 total (Phase 6: 8). Last updated: 2026-02-25. |

### Plan 06-05 Artifacts (new — gap closure)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `index.html` | `fetchCsv()` uses `/proxy?url=` | VERIFIED | Line 2846: `const url = '/proxy?url=' + encodeURIComponent(heaterUrl);` — exact pattern present. |
| `index.html` | file:// pre-flight toast references server.py/start.bat | VERIFIED | Lines 2823-2826: "Double-click start.bat or run: python server.py then open http://localhost:8080 in your browser." |
| `index.html` | `handleFetchNetworkError()` shows "Could not reach the heater" | VERIFIED | Lines 2811-2813: exact text present. "try Firefox" appears 0 times. |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `fetchCsv()` | `/proxy endpoint` | `/proxy?url=encodeURIComponent(heaterUrl)` built at line 2846, fetched at line 2850 | WIRED | Line 2845: `heaterUrl` constructed; line 2846: proxy URL built; line 2850: `fetch(url, ...)` |
| `server.py /proxy handler` | `urllib.request.urlopen` | `urlopen(target_url, timeout=15)` at line 42 of server.py | WIRED | Lines 41-43: `with urllib.request.urlopen(target_url, timeout=15) as resp: data = resp.read()` |
| `server.py /proxy handler` | `Access-Control-Allow-Origin: *` | `send_header('Access-Control-Allow-Origin', '*')` at line 45 of server.py | WIRED | Line 45: header set before `end_headers()` at line 48. |
| `server.py` | `webbrowser.open` | `threading.Timer(0.5, lambda: webbrowser.open(url)).start()` | WIRED | Line 64: exact pattern present. |
| `fetchCsv()` | `onCsvStringAccepted()` | `await onCsvStringAccepted(csvString, displayName, fileDate)` on HTTP 200 | WIRED | Line 2873: exact call; `onCsvStringAccepted` defined at line 1924. |
| `fetchCsv()` | `AbortSignal.timeout(10000)` | `fetch(url, { signal: AbortSignal.timeout(10000) })` | WIRED | Line 2850: exact pattern present. |
| `fetchCsv()` | `_lastFetchAt` | Written before fetch call at module scope | WIRED | Line 2839: `_lastFetchAt = Date.now()` before `await fetch(...)` at line 2850. |
| `#fetch-btn click handler` | `fetchCsv()` | `addEventListener('click', () => fetchCsv(...))` | WIRED | Lines 2917-2922: confirmed. |
| `saveSettings()` | `showFetchControls()`/`hideFetchControls()` | Called at end of `saveSettings()` based on `ip && password` | WIRED | Lines 972-977: both branches. |
| Init block | `showFetchControls()` | Called after `loadSettings()` based on `_settings.ip && _settings.password` | WIRED | Lines 2926-2931: `loadSettings()` then conditional `showFetchControls()`. |

---

## Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| CONN-01 | 06-02, 06-03 | Log period selector + download button shown when configured, hidden when not | SATISFIED | `#fetch-controls` HTML line 867; `showFetchControls()`/`hideFetchControls()` wired to `saveSettings()` and init block |
| CONN-02 | 06-01, 06-03, 06-04, 06-05 | User can trigger direct CSV download from heater API for selected log period | SATISFIED (code + proxy) / HUMAN NEEDED (end-to-end hardware) | `fetchCsv()` routes through `/proxy?url=`; `server.py` proxies server-side with CORS header; 06-05 SUMMARY states human checkpoint approved |
| CONN-03 | 06-01, 06-02, 06-03 | Download button disabled 2500ms after each request | SATISFIED | Rate-limit guard, `_lastFetchAt` timestamp, `finally` block with `setTimeout` restore |
| CONN-04 | (inherited Phase 5) | Downloaded CSV loaded into chart using same pipeline as drag-and-drop | SATISFIED | Line 2873: `await onCsvStringAccepted(csvString, displayName, fileDate)` — shared pipeline |
| CONN-05 | (inherited Phase 5) | Drag-and-drop and file picker remain available regardless of settings | SATISFIED | `handleFileDrop` and file-input paths in `index.html` unchanged |
| CONN-06 | 06-04 | Local Python proxy server provided; bypasses browser CORS restrictions | SATISFIED | `server.py` 69 lines, stdlib only, `/proxy` endpoint with `Access-Control-Allow-Origin: *` |
| ERR-01 | 06-01, 06-03, 06-05 | User sees actionable message when opening as file://, referencing server.py/start.bat | SATISFIED | Protocol pre-flight at line 2821; correct message at lines 2823-2826; "python -m http.server" = 0 matches |
| ERR-02 | 06-01, 06-03 | Clear error when heater unreachable or request times out (10s) | SATISFIED | `AbortSignal.timeout(10000)` line 2850; dual `TimeoutError`/`AbortError` handling lines 2802-2808 |
| ERR-03 | 06-01, 06-03 | Clear error when API password wrong (heater returns 404) | SATISFIED | Line 2793: correct toast |
| ERR-04 | 06-01, 06-03 | Clear error when rate limit exceeded (heater returns 401) | SATISFIED | Line 2790: correct toast |

**Orphaned requirements check:** REQUIREMENTS.md now maps 8 requirements to Phase 6 (CONN-01, CONN-02, CONN-03, CONN-06, ERR-01, ERR-02, ERR-03, ERR-04). All 8 are claimed in plan frontmatter across 06-01 through 06-05. CONN-04 and CONN-05 are claimed by Phase 5. None orphaned.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| _(none)_ | — | — | — | — |

The previous BLOCKER ("try Firefox") is confirmed eliminated. No new anti-patterns found in modified files.

---

## Human Verification Required

### 1. End-to-End Download with Real OekoFEN Heater via Proxy

**Test:**
1. In the project directory run: `python server.py`
2. Verify terminal prints: "OekoFEN Viewer running at http://localhost:8080 — Press Ctrl+C to stop"
3. Browser auto-opens to http://localhost:8080
4. Click the gear icon, enter heater IP, port (4321), and API password, click Save Settings
5. The "Download from Heater" button and log period selector appear
6. Select "Today", click "Download from Heater"
7. Confirm in DevTools Network tab: request URL is `/proxy?url=http%3A%2F%2F{ip}...` (not direct to heater)

**Expected:** Chart renders with heater data — identical visual result to dragging the same CSV file. HTTP 200 in Network tab.

**Why human:** The proxy routes the request server-side; the browser never touches the heater directly. The code path is complete and verified. The 06-05 SUMMARY states the human checkpoint was approved. This verifier cannot confirm hardware behavior programmatically. If the user already ran and approved this test, this item can be marked closed.

---

## Gaps Summary

No gaps remain. All automated checks passed.

**Previous gap (now closed):** The "try Firefox" BLOCKER in `handleFetchNetworkError()` is confirmed eliminated — 0 matches in index.html. The broader solution (proxy server) also makes CORS a non-issue at the browser layer entirely.

**Verification approach on gap closure:**
- "try Firefox" in index.html: 0 matches — confirmed closed
- "python -m http.server" in index.html: 0 matches — confirmed closed
- `/proxy?url=` in fetchCsv: present at line 2846 — confirmed wired
- `server.py` exists, 69 lines, all required patterns present — confirmed
- `start.bat` exists, 2 lines, correct content — confirmed
- `REQUIREMENTS.md` CONN-06 present, proxy row absent, ERR-01 updated, count = 16 — confirmed
- All previously-verified items (fetch controls UI, rate-limit guard, HTTP error map, init block wiring) pass regression check — confirmed

---

_Verified: 2026-02-25T10:30:00Z_
_Verifier: Claude (gsd-verifier)_
_Re-verification of: 06-VERIFICATION.md (previous status: gaps_found, score: 4/5)_
