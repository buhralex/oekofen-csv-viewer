# Quick Task 1: make page scrollable

## Task
Remove `overflow: hidden` from `html, body` and enable `overflow-y: auto` on body so the stats and analysis panels scroll properly. Increase panel bottom padding to clear the fixed status bar.

## Changes
1. `html, body` — remove `overflow: hidden`
2. `body` — add `overflow-y: auto`
3. `#stats-panel`, `#analysis-panel` — increase `padding-bottom` from `20px` to `48px` (clears 28px status bar)
