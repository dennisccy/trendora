# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14
**Date:** 2026-06-13
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Switch the event study on `/research` between **Episodes** (default) and **Pooled** counting by clicking the "Episodes / Pooled" segmented button group next to the subject selector — no page reload required.
- Read the honest disclosure line beside the event-study figures in both modes: the current view's observation count (n), the number of distinct stock symbols, and the number of distinct first-trigger episodes are always shown.
- Open a mode-correct samples drill-down (in a new tab) by clicking any "N=" chip in either Episodes or Pooled mode — the drill-down total always equals the clicked N and the cohort line states which view it reproduces.
- Look up the definitions of **Episode** and **Pooled (per-signal-day)** on the `/methodology` glossary page, or via the inline tooltip that appears next to the view label in the disclosure line on `/research`.

---

## What Changed in the Visible UI

- The `/research` Setup & Pattern Lab now shows an **Episodes / Pooled** segmented toggle (button group with an active pill) positioned next to the subject selector. It defaults to **Episodes** on every page load.
- A new **disclosure line** (`data-testid="event-study-disclosure"`) appears beside the event-study figures in both Episodes and Pooled modes, showing three values: n, Unique symbols, and Episodes. The old "Pooled occurrences" meta figure was replaced by this view-aware line.
- Per-horizon, by-regime, and by-sector **N= chips** now carry the active view in their link, and their label reads "episodes" or "occurrences" to match the current mode.
- The `/research/samples` drill-down page now shows a cohort detail line that states the overlap view the drill-down reproduces ("Episodes (first-trigger)" or "Pooled (per-signal-day)").
- The `/methodology` glossary now includes two new entries: **Episode** and **Pooled (per-signal-day)**.

---

## What Old Behavior Changed

- **Event-study default observation count**: Previously the lab counted every per-signal-day occurrence (pooled) by default. It now defaults to Episodes (first-trigger), which is a lower count. For example, "Risk-off-watchlist" shows 707 by default instead of 2,242. The prior 2,242 figure is exactly one click away via the Pooled toggle.
- **Event-study samples drill-down rows**: Previously the drill-down always listed every signal-day (pooled) regardless of context. Now it lists the rows for whichever view the N= chip was clicked under (episodes or pooled), and defaults to Episodes when no view is specified.
- **Samples drill-down cohort header**: The cohort header now states the overlap view ("Episodes (first-trigger)" or "Pooled (per-signal-day)") rather than showing no view label.

---

## Not Visible Yet

- None. Every backend addition in this iteration (the `view` parameter, the three disclosure values, the glossary entries) is wired into the UI.
