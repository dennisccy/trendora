# Iteration State — market-compass

**After iteration:** 29 · **Date:** 2026-09-01 · **Verdict:** ESCALATE

## Journeys

7 passing (J-01 J-04 J-05 J-06 J-08 J-10 J-11) · 4 partial (J-02 J-03 J-07 J-09) · 0 failing · 0 unknown — 11 total

## Active blockers

- **J-07 (dev, one bounded action):** direction badges show real words ONLY at `/?asof=2026-08-03`
  (`state_band_json` non-null on 1 of 27 rows); on `/` at the frontier 2026-08-12 all three read "NA"
  beside a Summary card stating a real comparison (`.../iter-29-evidence/UT-04-result.png`, auditor F1),
  yet goal.md requires direction "From `/` alone". Fix: mint a NEW VERSION of the 2026-08-12 manifest via
  the confirm-gated regenerate path iter-26 proved on 2025-04-15 — v1..v6 untouched (AG-12), new version
  `prospective_eligible=0` (AG-17); name that one date, permit no other, re-check the table after every lane.
- **J-07 guard missing (dev, small):** `journey-scripts/J-07.json` step 4 asserts a narrative sentence that
  predated `state_band` and landed AFTER the replay ran (23:50:41 vs 23:47:10); the three `compass-state-band-*-direction` testids appear in no golden. Point it at the badges.
- **Owner question that would close J-07 today:** is one real date enough, with "NA" accepted on the
  frontier landing view? See `state/assumptions.md` (iter-29 goal-evaluator).
- **Pre-existing red test (dev or waiver):** `test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` — literals in `indicators.py`/`forward_testing.py`/`research.py`, untouched since `0c445647`.

## Last 2 verdicts

- iter 29: ESCALATE — J-07's words are real on one date but the landing view still says "NA"; the next step
  writes permanently to the protected manifest table on the frontier date, so full depth is mandatory (a plain recommendation was demoted to lean at iters 2, 6, 8, 23, 24, 26, 28).
- iter 28: ESCALATE — J-07 built but invisible (`state_band` null on all 26 manifests); a `Depth: full`
  spec ran lean for the 7th time while permanently altering the protected table.

## Do not redo

- `build_state_band`, `_severity_at`, `compass.vocabulary.direction_words` — shipped, reviewed, green
  (11 tests), correct to the decimal, verified live at `/?asof=2026-08-03`.
- The 2026-08-03 mint — done (`next_session_manifests` id 27, v1, retrospective, eligible=0); do not
  re-mint it or mint further historical dates.
- AG-12/AG-9/AG-18 proof for iter-29 — re-derived after every lane: 27 rows, 26 byte-identical
  (`sha256 c070dcf1…`), exports untouched, no provider run since 2026-08-23, 29 columns.
- J-08 (`/market` relocation) and J-06 (frozen-manifest honesty) are CLOSED — do not rebuild.
- Passenger tasks, never an iteration goal: J-04 screenshot retake (11th owed); J-05/J-06/J-07/J-08
  walkthrough recordings (iter-29's J-07 recording is defective — clicks failed, frames show "NA").
