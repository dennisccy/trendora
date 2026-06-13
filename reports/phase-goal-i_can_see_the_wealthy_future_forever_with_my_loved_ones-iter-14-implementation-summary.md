# Goal Iteration 14 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14
**Date:** 2026-06-13
**Written by:** developer

---

## Features Implemented

- **Overlap-honest event study (Episodes by default)**: The Setup & Pattern Lab on `/research` now defaults to an "Episodes" view. When the same stock keeps qualifying for a setup or pattern across consecutive scan dates, those repeated signal-days are counted ONCE — at the first date it triggered — instead of being counted on every date. This stops the evidence from over-counting a name that simply keeps appearing for weeks.
- **One-click Episodes ⇄ Pooled toggle**: A segmented button group next to the subject selector flips between the new Episodes view and the original "Pooled" view (every signal-day counted). The Pooled view reproduces the exact numbers the lab published before this change, so nothing is lost — the prior figures are always one click away.
- **Honest disclosure line**: Beside the figures the lab now always shows three numbers in both views: the current view's sample size (n), how many distinct stock symbols are behind it, and how many distinct first-trigger episodes there are. This makes window overlap impossible to hide.
- **Mode-correct samples drill-down**: Clicking an "N=" figure opens the per-observation drill-down (in a new tab) for the SAME view it was clicked under — in Episodes mode a continuous run shows as a single first-trigger row; in Pooled mode it shows every signal-day. The drill-down total always equals the figure that was clicked.
- **Two new glossary entries**: "Episode" and "Pooled (per-signal-day)" are now defined on the `/methodology` glossary and appear as tooltips wherever those terms are shown.

---

## Changed Behavior

- **Event study default count**: Previously the event study counted every per-signal-day occurrence (pooled). Now it counts first-trigger episodes by default. For example, on the current seed data the "Risk-off-watchlist" subject shows 707 episodes by default versus 2,242 pooled signal-days. The Pooled toggle restores the prior 2,242 figure exactly.
- **Event-study samples drill-down**: Previously always listed every signal-day. Now it lists the rows for the selected view (episodes or pooled) and defaults to episodes.

---

## Backend-Only Items

- None. Every backend addition (`view` parameter, the three disclosure values, the glossary entries) is wired into the UI.

---

## Incomplete Items

- None. All IN SCOPE items from the spec are implemented: the episode-collapse helper, `view` threading through the event-study aggregate + the samples drill-down + both API endpoints (with 422 validation), the three disclosure values, the glossary entries, the frontend toggle + disclosure line + cohort serialization.

---

## Config and Environment Changes

- `config.yaml` — added two authored glossary terms under `methodology.terms` (category `forward_evidence`): "Episode" and "Pooled (per-signal-day)". These are plain catalog text — no numeric tunable, no threshold reference, no new validated config section.
- No new environment variables.
- No database migration. The episode collapse is a pure in-memory grouping of already-stored rows — NO new stored column, table, or migration was added (this deliberately avoids the iter-12 additive-column trap).

---

## Known Limitations

- **Consecutiveness is judged on the stored scan-date sequence, not the calendar.** Two of a symbol's signal-days are "consecutive" (and therefore one episode) when there is no intervening stored scan date on which the symbol did not trigger the subject. A large calendar gap with no intervening stored scan is still one continuous episode; a stored scan in between on which the symbol dropped out splits the run into two episodes. This is the intended, documented rule.
- **`episode_count` is identical in both views by design** (it counts first-trigger episodes regardless of which view renders), so in Pooled mode the disclosure line shows n (signal-days) > episodes, and in Episodes mode n == episodes.
- The full backend pytest suite (~46–59 min) was NOT run to completion inside the dev turn (it exceeds a single turn's time budget). The targeted modules touched were run to green; the full suite is handed to the pump (see the dev handoff for the exact command and the verified modules).
