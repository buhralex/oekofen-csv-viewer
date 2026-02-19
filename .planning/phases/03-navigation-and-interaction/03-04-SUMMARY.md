---
phase: 03-navigation-and-interaction
plan: "04"
subsystem: ui
tags: [uplot, minimap, zoom, overview, canvas, javascript]

# Dependency graph
requires:
  - phase: 03-01
    provides: AppState.onZoomChange stub, setScale hook wired to AppState.onZoomChange, drag-to-zoom, reset button
  - phase: 03-02
    provides: scroll-wheel zoom with MIN_RANGE=300s enforcement
  - phase: 03-03
    provides: tooltipPlugin() cursor crosshair with value display
  - phase: 02-01
    provides: uPlot instance in AppState.chart, buildChartData(), DEFAULT_SERIES
provides:
  - createMinimap() function rendering secondary uPlot instance at 72px in #minimap-area
  - AppState.minimap object with instance and updateSelection() function
  - Bidirectional sync between main chart zoom and minimap highlight overlay
  - Minimap drag-to-pan: user drags minimap to reposition main chart zoom window
  - onWindowResize() extended to resize minimap alongside main chart
  - destroyChart() extended to destroy minimap and clear #minimap-area
  - Accent-blue select overlay CSS rule on #minimap-area .u-select for dark theme visibility
affects: [04-series-management]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "setSelect(opts, false) second-arg pattern to prevent minimap setSelect hook re-firing and infinite loop"
    - "Object.assign() series clone for minimap: width:0.5 continuous / width:0 binary to reduce visual noise at 72px"
    - "cursor.show:true + cursor.drag.setScale:false in minimap — allows drag events while suppressing uPlot's built-in zoom-on-drag"
    - "valToPos / posToVal conversion for pixel-to-timestamp mapping in minimap updateSelection and setSelect hook"
    - "Pre-clamp zoom min/max before setScale for reliable floor enforcement — more reliable than hook-based clamping"

key-files:
  created: []
  modified:
    - index.html

key-decisions:
  - "setSelect(opts, false) is CRITICAL for the minimap anti-loop pattern: the false second argument suppresses the minimap setSelect hook from firing when updateSelection() is called programmatically"
  - "cursor.show:false disables drag in uPlot — minimap drag requires cursor.show:true with cursor.drag.setScale:false"
  - "display:block required for tooltip show — display:'' inherits CSS display:none from stylesheet rule"
  - "Minimap select overlay styled with rgba(79,195,247,0.3) accent blue for visibility on dark navy theme"
  - "Reset zoom must pass explicit {min: dataMin, max: dataMax} to setScale — {min:null, max:null} does not trigger full-range reset in uPlot 1.6.32"
  - "300s drag-zoom floor implemented via pre-clamped values before calling setScale — hook-based approaches failed due to uPlot re-entrancy"

patterns-established:
  - "Anti-loop pattern: minimap.setSelect(opts, false) — always pass false when calling setSelect programmatically to suppress the hook"
  - "Minimap lifecycle: createMinimap() in createChart(), destroy in destroyChart(), resize in onWindowResize()"
  - "Zoom floor enforcement: pre-clamp computed extents before setScale call, not in hooks"

requirements-completed:
  - NAVG-05

# Metrics
duration: 36min
completed: 2026-02-19
---

# Phase 3 Plan 04: Minimap Overview Summary

**uPlot secondary minimap at 72px showing full day with accent-blue zoom-region highlight and bidirectional drag-to-pan; 5 bugs found and fixed during human verification of all 23 checks**

## Performance

- **Duration:** 36 min
- **Started:** 2026-02-19T20:42:18+01:00
- **Completed:** 2026-02-19T21:18:35+01:00
- **Tasks:** 2 (1 auto implementation + 1 human-verify checkpoint)
- **Files modified:** 1

## Accomplishments

- createMinimap() implemented: secondary uPlot at 72px height with full-day data, no axes, no legend
- Bidirectional sync: main chart setScale hook calls minimap.updateSelection() via AppState.onZoomChange; minimap setSelect hook calls AppState.chart.setScale()
- Anti-loop pattern: setSelect(opts, false) prevents infinite sync cycle between main chart and minimap
- Minimap drag-to-pan working: user drags on minimap strip to reposition main chart zoom window
- Minimap selection overlay styled with accent blue (rgba(79,195,247,0.3)) for visibility on dark navy theme
- onWindowResize() and destroyChart() extended to handle minimap lifecycle correctly
- All 23 Phase 3 verification checks passed with a real OekoFEN CSV file — all 5 NAVG requirements satisfied

## Task Commits

Task commit:

1. **Task 1: Implement createMinimap() and wire into createChart() and onWindowResize()** - `10dac1e` (feat)

Auto-fix commits applied during human checkpoint verification (Rule 1 bugs found in real browser):

- `bd9a844` — Fix reset zoom uses explicit data extents (not null/null)
- `7129750` — Fix 300s minimum zoom for drag-to-zoom (attempt 1: setSelect hook)
- `ab3f619` — Fix tooltip display:block not display:''
- `0bd7f2c` — Fix minimap zoom highlight visibility on dark theme
- `a26f6ed` — Fix minimap drag (cursor.show:false disables drag)
- `25a736a` — Fix drag zoom floor via setSelect hook (attempt 2)
- `d23c97a` — Fix 300s zoom floor in setScale hook (attempt 3, partial)
- `27cd4f0` — Fix drag-zoom pre-clamped values enforce 300s floor (FINAL)

**Plan metadata:** (this commit)

## Files Created/Modified

- `index.html` — createMinimap() function, AppState.minimap wiring, onWindowResize() and destroyChart() minimap lifecycle, tooltip display:block fix, minimap select overlay accent color CSS, reset zoom explicit data extents, drag-zoom 300s floor via pre-clamped values before setScale

## Decisions Made

- Used `setSelect(opts, false)` second argument to suppress minimap hook re-firing — the standard uPlot anti-loop pattern; not prominently documented but required for bidirectional sync
- Switched minimap cursor config from `cursor.show:false` to `cursor.show:true` with `cursor.drag.setScale:false` — uPlot ties drag functionality to cursor visibility; show:false silently disables drag
- Tooltip show fix: `element.style.display = 'block'` not `display = ''` — empty string falls back to the CSS stylesheet rule which specifies `display: none`
- Reset zoom: `{min: dataMin, max: dataMax}` explicitly — `{min: null, max: null}` is not recognized by uPlot 1.6.32 as a full-range reset
- Drag-zoom 300s floor: pre-clamp computed extents before calling setScale; hook-based approaches (setSelect hook, setScale hook) both suffered from uPlot re-entrancy

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Reset zoom did not return to full day**
- **Found during:** Task 2 (human checkpoint, Check 7)
- **Issue:** Passing `{min: null, max: null}` to setScale did not trigger full-range reset; chart stayed at previously zoomed range
- **Fix:** Changed to `{min: dataMin, max: dataMax}` using explicit data array first/last timestamps
- **Files modified:** index.html
- **Verification:** Check 7 passed — Reset Zoom button and double-click return to full day
- **Committed in:** bd9a844

**2. [Rule 1 - Bug] Drag-zoom had no minimum range enforcement**
- **Found during:** Task 2 (human checkpoint, Check 12)
- **Issue:** Drag-zoom allowed zooming below the 5-minute minimum established for scroll zoom in 03-02; inconsistent behavior across zoom methods
- **Fix:** Three attempts required. Final fix pre-clamps computed min/max values before the setScale call to ensure at least 300s span
- **Files modified:** index.html
- **Verification:** Check 12 passed — cannot drag-zoom below ~5 minutes
- **Committed in:** 7129750 (attempt 1), 25a736a (attempt 2), d23c97a (attempt 3), 27cd4f0 (FINAL)

**3. [Rule 1 - Bug] Tooltip not appearing on cursor move**
- **Found during:** Task 2 (human checkpoint, Checks 14+15)
- **Issue:** `element.style.display = ''` (empty string) inherits the CSS `display: none` applied to `#chart-tooltip` in the stylesheet; tooltip was never visible
- **Fix:** Changed to `element.style.display = 'block'`
- **Files modified:** index.html
- **Verification:** Checks 14 and 15 passed — tooltip appears with crosshair and shows all series values
- **Committed in:** ab3f619

**4. [Rule 1 - Bug] Minimap zoom-region highlight nearly invisible on dark theme**
- **Found during:** Task 2 (human checkpoint, Check 18)
- **Issue:** Default uPlot select overlay uses grey fill that blends with the dark navy theme (#1a1a2e)
- **Fix:** Added CSS rule for `#minimap-area .u-select` with `background: rgba(79,195,247,0.3)` matching the app's --accent-color variable
- **Files modified:** index.html
- **Verification:** Check 18 passed — zoom highlight clearly visible as blue band on minimap
- **Committed in:** 0bd7f2c

**5. [Rule 1 - Bug] Minimap drag broken — cursor.show:false disables drag**
- **Found during:** Task 2 (human checkpoint, Check 19)
- **Issue:** Plan specified `cursor.show:false` for the minimap. In uPlot, cursor visibility gates drag event processing — with show:false, drag events are silently ignored and drag-to-pan did not work
- **Fix:** Changed to `cursor.show:true` with `cursor.drag.setScale:false` to enable drag events while suppressing uPlot's built-in zoom-on-drag; the minimap setSelect hook handles the zoom redirect
- **Files modified:** index.html
- **Verification:** Check 19 passed — dragging in minimap pans main chart correctly
- **Committed in:** a26f6ed

---

**Total deviations:** 5 auto-fixed bugs (all Rule 1 — incorrect behavior found during human verification)
**Impact on plan:** All 5 fixes were direct corrections to the minimap implementation and pre-existing interaction features (tooltip, reset zoom) verified in a real browser for the first time during this plan's checkpoint. No scope creep.

## Issues Encountered

- The 300s drag-zoom floor required three iterations: the setSelect hook fires before setScale completes a drag, causing wrong clamping; the setScale hook triggered uPlot re-entrancy; the final pre-clamp approach (computing clamped values before passing to setScale) proved reliable across all zoom sources.
- uPlot's `cursor.show:false` silently disabling drag is undocumented behavior — required runtime diagnosis by observing drag events not firing during the verification checkpoint.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 5 NAVG requirements (NAVG-01 through NAVG-05) satisfied and human-verified with a real OekoFEN CSV file
- Phase 3 complete — all navigation and interaction features working together without conflict or regression
- Phase 4 (Series Management) can proceed: AppState.chart, AppState.minimap, buildChartData(), DEFAULT_SERIES all available
- Phase 4 should decide whether minimap reflects only active (visible) series or always shows full DEFAULT_SERIES — currently always shows full set

---
*Phase: 03-navigation-and-interaction*
*Completed: 2026-02-19*
