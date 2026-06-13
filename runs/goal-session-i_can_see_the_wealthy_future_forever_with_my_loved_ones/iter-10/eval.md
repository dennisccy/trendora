# Iteration 10 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

Iter-10 (lean, frontend-only 2-file diff) newly passes both target journeys J-64 (samples table
client-side sort + ticker filter as an honest "x of N" view transform) and J-65 (`N=` chips open the
drill-down in a new tab), with zero backend diff, COHERENCE-PASS, and zero regressions across the eight
required-still-passing journeys. The remaining lowest-risk view-transform vein is now exhausted — every
remaining failing journey (J-58..J-63, J-66, J-67) is backend/config-touching and needs the full
pipeline with a pytest gate, so the next iteration should be full.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-64 (samples sort + ticker filter) | failing | **passing** | reports/qa/goal-…-iter-10-evidence/UT-J-64-ticker-filter-aapl.png (+ sort-forward-return-asc, filter-empty-state, filter-sort-compose, samples-loaded) |
| J-65 (`N=` chips new tab) | failing | **passing** | UT-J-65-research-historical-chips.png + source (sample-link.tsx target=_blank/rel) |
| J-25 (Factor Lab) | passing | passing | UT-J-25-J-26-J-29-research.png |
| J-26 (combination cohort) | passing | passing | UT-J-25-J-26-J-29-research.png (caveat: shared /research bytes) |
| J-29 (Setup & Pattern Lab) | passing | passing | UT-J-25-J-26-J-29-research.png |
| J-32 (research as-of scope mode) | passing | passing | UT-J-32-asof-mode.png |
| J-43 (`?asof` URL serialization) | passing | passing | UT-J-43-J-50-stocks-historical.png |
| J-50 (hrefs embed `?asof`) | passing | passing | UT-J-43-J-50-stocks-historical.png |
| J-51 (drill-down total == published N) | passing | passing | UT-J-64-ticker-filter-aapl.png (total 2376) + source |
| J-52 (row ticker → dated detail, new tab) | passing | passing | UT-J-64-ticker-filter-aapl.png (28 AAPL rows) + source |

**Evidence directly evaluator-viewed:** UT-J-64-samples-loaded, UT-J-64-sort-forward-return-asc,
UT-J-64-ticker-filter-aapl, UT-J-64-filter-empty-state, UT-J-64-filter-sort-compose,
UT-J-25-J-26-J-29-research, UT-J-32-asof-mode, UT-J-43-J-50-stocks-historical.

**Source-level confirmation (not trusting the QA table):**
- `apps/frontend/app/research/samples/page.tsx` — filter-THEN-sort memos over `data.rows` (:338-344);
  `samples-total` renders served `data.total` verbatim (:252); fetch effect keyed only on
  `[fetchParams, asofCutoff]` (:159, no refetch on sort/filter); 3rd-click clears to served order; the
  `SortHeader` keeps the sort `<button>` and `TermInfo` as SIBLINGS in the `<th>` (:533-555 — iter-5
  nested-interactive hazard avoided); `TickerLink` keeps `target="_blank"`+`rel` (:568-585, J-52).
- `apps/frontend/components/sample-link.tsx` — `target="_blank"` + `rel="noopener noreferrer"` (:49-50)
  with the href construction byte-unchanged (`buildSamplesHref` + `useAsOfHref`, :44-45).
- `git diff … --name-only -- apps/backend/` returns **empty** — frontend-only contract honored.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Leaderboard sorting/searching/table filtering are view transforms (no recompute, no re-rank, no new endpoint, "x of N", cohort total untouched) | OK | `samples-total` reads served `data.total` verbatim; sort/filter operate over `data.rows` only; no refetch; backend diff empty; coherence audit ruled the comparators read already-served fields. Captures show "Showing 28/19/0 of 2376", total stays 2376. |
| Sample drill-downs are read-only and count-coherent | OK | QA: API total=2376 == published N (D1 chip), len(rows)==total, same instant. View-empty state explicitly "the cohort itself is unchanged". |
| No fabricated data | OK | Honest view-empty state on no-match ("No observations match this filter"), distinct from the n=0 cohort empty state; zero fabricated rows. |
| `?asof` is a serialization, not a second date state | OK | J-65 href construction byte-unchanged; `target`/`rel` only added; asof-provider not in the diff. |

No anti-goal violation introduced. `anti_goal_violations` remains empty.

## Next-Step Recommendation

Continue. The lean view-transform vein (J-48/J-55/J-56/J-64/J-65) is now fully delivered. The remaining
eight failing journeys are all backend/config-touching and tractable (none is data-walled — distinct
from J-22/23/24 blocked-NA):
- **J-58** — Sectors page config industry catalog (ticker→name/description + stock→industry-group
  mapping) + backend serving. New config reference data + backend → **full depth with a pytest gate**.
- **J-61 / J-62** — per-date availability heatmap (read-only descriptive endpoint + `/data` heatmap) and
  the as-of calendar popover (presentation of the same single global state). Backend endpoint → full.
- **J-63** — event-study first-trigger-episode default with the pooled view one toggle away
  (byte-identical figures); backend research-module change → full.
- **J-59 / J-60 / J-66 / J-67** — the jobs-pipeline cluster (stage-resumable zero-refetch resume,
  start-inserted run-history + interrupted boot sweep, fine-grained honest progress incl. the 318/159
  counter fix, transactionally-sound concurrent backfill). FULL-depth backend work; bundle per the
  decomposer's working plan; J-66 also carries the iter-8 coherence-WARN residual (move the frontend
  `speedupFactor` division into the backend stages payload when touching `data_manager.py`).

Recommended next target: **J-58** at full depth (smallest backend surface, unblocks the Sectors page),
or the J-59/J-60/J-66/J-67 jobs cluster if the decomposer prefers to clear the highest-risk backend work
first. Either way the next iteration is full, not lean.

## Halt Justification

Not halting — this is a CONTINUE. Two journeys newly passing, zero regressions, no critical anti-goal
violation, COHERENCE-PASS, eight tractable failing journeys remain (not stalled, not goal-achieved). The
three `unknown` journeys (J-22/J-23/J-24) are data-walled blocked-NA and explicitly non-vetoing per
goal.md "Data-dependent journeys never block the rest" — they do not gate GOAL_ACHIEVED but the goal is
not achieved regardless while J-58..J-67 remain unbuilt.
