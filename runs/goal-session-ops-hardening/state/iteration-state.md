# Iteration State — ops-hardening

**After iteration:** 75 · **Date:** 2026-08-13 · **Verdict:** CONTINUE

## Journeys

8 passing (J-01 J-03 J-04 J-05 J-06 J-07 J-08 J-09) · 0 failing/partial/unknown — all re-verified this round (replay 8/8, 0 voided, 0 broken frames); J-08+J-09 FRESH since iter-72, makeup cleared.

## Active blockers

- **Spec unexecuted** (dev): `docs/phases/goal-ops-hardening-iter-75.md` says `Depth: lean` + code
  work; engine ran `evidence`, dev+reviewer skipped, diff "(no changes)". TC-1/2/6/7 all unmet.
- **Asset-less QA frontend un-root-caused** (dev, iter-72/c): did NOT recur, nothing diagnosed or
  changed. `scripts/start-frontend.sh` / `lib/common.sh` still the suspects.
- **Two goldens can't detect a regression** (dev, iter-75/c): `journey-scripts/J-07.json` is 2
  steps; `J-09.json` passes against an IDLE background-compute panel.
- **Walkthrough saves duplicates** (dev, iter-75/b): `reports/demo/goal-ops-hardening-iter-75/`
  step-04 ≡ step-07, step-05 ≡ step-06; J-05/J-07/J-08/J-09 `[NEW]` clauses unmet.
- **Carried one-liners** (dev): stray 0-byte `=` at repo root (iter-74/c); TC-10 shot or removal of
  the hook at `apps/backend/app/api/data.py:119`; stale `state/goldens-regen-pending` (J-05..J-09).
- **OWNER, blocking closure:** 133 unresolved MINOR ledger entries block GOAL_ACHIEVED literally
  while the loop opens ~4 / closes ~2 a round — pick (a) finish on journeys + no serious problem or
  (b) 2-3 housekeeping rounds. Also: 2s health ceiling; B-1107; `browser-qa-phase.sh`; cost (1.8x).

## Last 2 verdicts

- iter 75: CONTINUE — all 8 pass on fresh evidence and the 3-round evidence crisis ended, but no
  code lane ran, so the harness defect is unexplained rather than fixed and the DoD is unmet.
- iter 74: CONTINUE — J-07 `partial` → `passing` on a measured 4,724.0 MB / 42.33% margin; J-08 and
  J-09 still carried without evidence of their own for a 2nd round.

## Do not redo

- **J-07 step 3 DONE** — 4,724.0 MB vs 8192 cap = 42.33% (`iter-74/phase-vmpeak-samples.csv`): no
  re-measure, no `pool_size`/`max_overflow`/`cache_size` re-tune, no full-`rebuild` drill on this host.
- **Do NOT regenerate the J-05..J-09 goldens** — the cause was never selector drift; STRENGTHEN
  J-07's and J-09's assertions instead (iter-75/c), which is different work.
- **J-08 and J-09 verified fresh at iter-75** — not an iteration goal again; walkthrough rides along.
- **Ground truth + Addendum 38 corrected** (iter-74); **readiness serve-stale + post-lock recheck
  DONE** (iter-72); **iter-33/g Regime Lab stays deferred** (42nd) without owner direction.
