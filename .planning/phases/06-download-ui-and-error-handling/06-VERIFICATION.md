---
phase: 06-download-ui-and-error-handling
verified: 2026-02-24T22:30:00Z
status: gaps_found
score: 4/5 success criteria verified
re_verification: false
gaps:
  - truth: "When fetch fails due to CORS/network error, the user sees accurate, actionable guidance"
    status: partial
    reason: "handleFetchNetworkError() shows a CORS error toast but includes 'try Firefox' which is empirically wrong — Firefox enforces CORS identically to Chrome; this gives users incorrect troubleshooting advice"
    artifacts:
      - path: "index.html"
        issue: "Line 2814: 'try Firefox, or verify the heater IP in Settings.' — Firefox does not bypass CORS; this advice is misleading and was confirmed incorrect by real-device testing against the OekoFEN heater"
    missing:
      - "Replace 'try Firefox, or verify the heater IP in Settings.' with accurate guidance: direct the user to open the heater URL in a new browser tab for manual download, e.g. 'To download manually, open the heater URL directly in your browser tab and drag the file in.'"
human_verification:
  - test: "Download button loads CSV from real OekoFEN heater into chart"
    expected: "Chart renders with heater data — identical visual result to dragging the same CSV file"
    why_human: "OekoFEN heater empirically confirmed to NOT return Access-Control-Allow-Origin headers; direct browser fetch is blocked by CORS at the network layer. Success criterion 2 cannot be verified programmatically or with a real device without a CORS proxy. The code path is correct but hardware prevents end-to-end verification."
---

# Phase 6: Download UI and Error Handling — Verification Report

**Phase Goal:** Users can trigger a direct CSV download from the heater for any log period, see clear feedback for all failure conditions, and the rate limit is enforced transparently
**Verified:** 2026-02-24T22:30:00Z
**Status:** gaps_found (1 gap — one-line fix in handleFetchNetworkError)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | When settings are configured, log period selector + download button appear; when not configured, controls hidden | VERIFIED | `#fetch-controls` HTML at line 867 has `display:none` default; `showFetchControls()`/`hideFetchControls()` called from `saveSettings()` (lines 973-977) and init block (lines 2927-2930) gated on `_settings.ip && _settings.password` |
| 2 | Clicking Download fetches selected log period CSV from heater and loads into chart | VERIFIED (code path) / HARDWARE-BLOCKED (real device) | Code path complete: `fetchCsv()` -> `AbortSignal.timeout(10000)` -> `arrayBuffer()` -> `TextDecoder('windows-1252')` -> `onCsvStringAccepted()` (lines 2847-2872). Heater empirically confirmed to block CORS — direct fetch impossible on real device without proxy. Not a code gap. |
| 3 | Download button disabled for 2500ms after each request; second click within window shows "please wait" | VERIFIED | `_lastFetchAt` written at line 2841 before fetch; rate-limit guard at lines 2835-2838 returns with toast; `finally` block at lines 2876-2881 restores button via `setTimeout` after remaining window; verified by human testing |
| 4 | When fetch fails due to CORS (file:// origin), user sees actionable message instructing `python -m http.server` | VERIFIED | Protocol pre-flight at line 2823 (`window.location.protocol === 'file:'`); correct message at lines 2825-2828; verified by human testing (Test E confirmed passing) |
| 5 | Heater unreachable/timeout: clear actionable error; API password wrong (404): directed to check settings | PARTIAL | Timeout: VERIFIED — `AbortSignal.timeout(10000)` at line 2849, dual `TimeoutError`/`AbortError` catch at line 2802, message at line 2805 confirmed correct. HTTP 404: VERIFIED — line 2793 toast "Check Settings." confirmed correct. CORS/network TypeError: PARTIAL — message at line 2813-2814 contains "try Firefox" which is empirically incorrect advice |

**Score:** 4/5 success criteria fully verified (Criterion 5 partial due to incorrect CORS error message text)

---

## Required Artifacts

### Plan 06-01 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `index.html` | `fetchCsv` async function + `_lastFetchAt`/`_rateLimitTimer` module-level vars + `setFetchButtonState` | VERIFIED | Lines 940-941: vars at module scope between `_settings` and `loadSettings()`. Line 2821: `async function fetchCsv`. Line 2776: `function setFetchButtonState`. |
| `index.html` | `handleFetchHttpError` and `handleFetchNetworkError` helpers | VERIFIED (with gap) | Line 2788: `handleFetchHttpError` — correct 401/404 mapping. Line 2801: `handleFetchNetworkError` — correct timeout branch; CORS branch has "try Firefox" gap. |

### Plan 06-02 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `index.html` | `#fetch-controls` div in `#drop-message` with `display:none` default | VERIFIED | Line 867: `<div id="fetch-controls" style="display:none; ...">` inside `#drop-message`. |
| `index.html` | `showFetchControls()` and `hideFetchControls()` functions | VERIFIED | Lines 2766-2774: both functions defined, toggle `style.display` on `#fetch-controls` element. |
| `index.html` | `fetch-btn` click event listener wired to `fetchCsv()` | VERIFIED | Lines 2916-2922: listener reads `#log-selector` value, calls `fetchCsv(command)`. |

### Plan 06-03 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `index.html` | Complete Phase 6 implementation verified against real device | VERIFIED (with documented gap) | Human verification completed; all 5 error paths tested; gap in CORS message text identified and documented. |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `fetchCsv()` | `onCsvStringAccepted()` | `await onCsvStringAccepted(csvString, displayName, fileDate)` on HTTP 200 | WIRED | Line 2872: exact call present; `onCsvStringAccepted` defined at line 1924. |
| `fetchCsv()` | `AbortSignal.timeout(10000)` | `fetch(url, { signal: AbortSignal.timeout(10000) })` | WIRED | Line 2849: exact pattern present. |
| `fetchCsv()` | `_lastFetchAt` | Written before fetch call at module scope | WIRED | Line 2841: `_lastFetchAt = Date.now()` written before `await fetch(...)` at line 2849. |
| `#fetch-btn click handler` | `fetchCsv()` | `addEventListener('click', () => fetchCsv(document.getElementById('log-selector').value))` | WIRED | Lines 2916-2922: listener confirmed; `fetchCsv(command)` called with `log-selector` value. |
| `saveSettings()` | `showFetchControls()`/`hideFetchControls()` | Called at end of `saveSettings()` based on `ip && password` | WIRED | Lines 972-977: both branches present; runs after `dismissOnboarding()`. |
| Init block | `showFetchControls()` | Called after `loadSettings()` based on `_settings.ip && _settings.password` | WIRED | Lines 2924-2930: `loadSettings()` then conditional `showFetchControls()`. |

---

## Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| CONN-01 | 06-02, 06-03 | Log period selector + download button shown when configured, hidden when not | SATISFIED | `#fetch-controls` HTML with `display:none`; `showFetchControls()`/`hideFetchControls()` wired to `saveSettings()` and init block |
| CONN-02 | 06-01, 06-03 | User can trigger direct CSV download from heater API for selected log period | SATISFIED (code) / HARDWARE-BLOCKED (real device) | `fetchCsv(command)` with correct URL construction, encoding, and pipeline handoff. Hardware CORS limitation is documented, not a code gap. |
| CONN-03 | 06-01, 06-02, 06-03 | Download button disabled 2500ms after each request | SATISFIED | Rate-limit guard, `_lastFetchAt` timestamp, `finally` block with `setTimeout` restore; confirmed by human test D |
| ERR-01 | 06-01, 06-03 | User sees actionable message for CORS/file:// fetch failure with `python -m http.server` instruction | SATISFIED | Protocol pre-flight check at line 2823; correct message confirmed by human test E |
| ERR-02 | 06-01, 06-03 | Clear error when heater unreachable or request times out (10s timeout) | SATISFIED | `AbortSignal.timeout(10000)` at line 2849; dual `TimeoutError`/`AbortError` handling at lines 2802-2808; timeout message confirmed |
| ERR-03 | 06-01, 06-03 | Clear error when API password wrong (heater returns 404) | SATISFIED | Line 2793: `showToast('Heater returned 404 — API password may be incorrect. Check Settings.', 'error', 8000)` |
| ERR-04 | 06-01, 06-03 | Clear error when rate limit exceeded on heater (heater returns 401) | SATISFIED | Line 2790: `showToast('Rate limit active on heater — wait 2.5 seconds before retrying.', 'warning', 5000)` |

**Orphaned requirements check:** REQUIREMENTS.md maps CONN-01, CONN-02, CONN-03, ERR-01, ERR-02, ERR-03, ERR-04 to Phase 6. All 7 are claimed in plan frontmatter (06-01 and/or 06-02 and/or 06-03). None orphaned.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `index.html` | 2814 | "try Firefox" in CORS error message — incorrect advice, empirically disproved | BLOCKER | Users following this advice will be confused; Firefox enforces CORS identically to Chrome; advice is wrong and was confirmed incorrect by real OekoFEN heater test. One-line fix. |

---

## Human Verification Required

### 1. End-to-End Download with Real OekoFEN Heater

**Test:** With a real OekoFEN heater on LAN, configure settings, select a log period, click Download from Heater.
**Expected:** Chart loads with heater data, identical to drag-and-dropping the same CSV file.
**Why human:** OekoFEN heater confirmed to NOT return `Access-Control-Allow-Origin` headers (empirically verified in 06-03 checkpoint). Direct `fetch()` from any browser is blocked by CORS. Success criterion 2 requires end-to-end download to chart, which cannot occur on this heater without a CORS proxy. The code is correctly implemented; the hardware is the constraint. This is documented as a permanent known limitation.

---

## Gaps Summary

**One gap found.** The gap is a single-line content error in `handleFetchNetworkError()`, confirmed by human testing during the 06-03 checkpoint.

**Location:** `index.html` line 2814, inside `handleFetchNetworkError()`, the else branch (TypeError — covers CORS from `http://localhost` and genuine network failure).

**Current text (incorrect):**
```
'Cannot reach heater. If the heater does not support browser requests (CORS), try Firefox, or verify the heater IP in Settings.'
```

**Why it is wrong:** The OekoFEN heater was empirically confirmed to NOT return `Access-Control-Allow-Origin` headers. Firefox enforces the CORS specification identically to Chrome, Edge, and Safari. Telling users to "try Firefox" will cause confusion — Firefox will show the same error.

**Fix required:** Replace "try Firefox, or verify the heater IP in Settings." with accurate guidance. The recommended replacement directs the user to open the heater URL directly in a browser tab for manual CSV download.

**Scope:** This is a one-line fix in a single file. No architecture changes needed. All other Phase 6 functionality is fully implemented and verified.

**Assessment of remaining success criteria:** Criteria 1, 3, 4, and 5 (timeout + 404 branches) are fully satisfied. Criterion 2 and the CORS branch of criterion 5 have this one-line messaging gap. Once fixed, the CORS error message will be accurate and Phase 6 will be fully complete pending the hardware limitation note.

---

_Verified: 2026-02-24T22:30:00Z_
_Verifier: Claude (gsd-verifier)_
