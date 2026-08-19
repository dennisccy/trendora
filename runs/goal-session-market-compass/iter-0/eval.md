# Iteration 0 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

This was a baseline check with no code changes, and it did what it was meant to do: it
measured where the product stands today against all eight Must-have journeys. The result is
that the whole "Today compass" feature set does not exist yet — there is no `/api/compass`
endpoint, no `/market` page, and the home page is still the old Dashboard. One journey, J-01
"Sector labels are honest and nearly complete", is partly there: the honesty rules already
hold, but 78.4% of stocks still show "Unassigned" instead of the 5% the goal asks for. No
anti-goal was broken, because nothing in the product was changed this iteration.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest and nearly complete | (none — first seen) | partial | reports/phase-goal-market-compass-iter-0-ui-test-results.md UT-J-01; reports/qa/goal-market-compass-iter-0-evidence/UT-J-01-result.png |
| J-02 What changed since previous session | (none — first seen) | failing | UT-J-02 row; reports/qa/goal-market-compass-iter-0-evidence/UT-J-02-fail.png |
| J-03 Plain-English summary with cited facts | (none — first seen) | failing | UT-J-03 row; reports/qa/goal-market-compass-iter-0-evidence/UT-J-03-fail.png |
| J-04 Candidates explain why and why-not | (none — first seen) | failing | UT-J-04 row; reports/qa/goal-market-compass-iter-0-evidence/UT-J-04-fail.png |
| J-05 Each close freezes one manifest | (none — first seen) | failing | UT-J-05 row; reports/qa/goal-market-compass-iter-0-evidence/UT-J-05-fail.png |
| J-06 A frozen manifest never changes | (none — first seen) | failing | UT-J-06 row; reports/qa/goal-market-compass-iter-0-evidence/UT-J-06-fail.png |
| J-07 Today page answers the ten-second read | (none — first seen) | failing | UT-J-07 row; reports/qa/goal-market-compass-iter-0-evidence/UT-J-07-fail.png |
| J-08 Market page moves over intact | (none — first seen) | failing | UT-J-08 row; reports/qa/goal-market-compass-iter-0-evidence/UT-J-08-fail.png |

Evidence notes (honesty):
- J-02, J-03, J-04 and J-07 share one identical capture of `/` (same md5 `9dfcc1cf…`). It is
  above-the-fold only, so it shows the legacy "Dashboard" heading but cannot by itself prove
  the absence claims. Those claims rest on the results file's full-page-text sweeps AND on my
  own independent code check: no `compass` module under `apps/backend/app/engine/`, no
  `api/compass` or `next_session_manifest` reference anywhere in `apps/backend/app/`.
- J-01's capture shows `/stocks` above the fold, not the Unassigned filter with 424 rows. The
  78.4% figure is corroborated three ways: the results row's DOM count and API cross-check,
  `docs/goal.md`'s own Ground Truth measurement, and `apps/backend/app/engine/scoring.py:445`
  (`"sector": cfg.stock_sectors.get(ticker)` is the only source; `pool_sector_aliases` has zero
  matches in `apps/backend/`).
- J-08 and J-05 captures are journey-specific and clear: `/market` renders "404: This page could
  not be found." with the sidebar still opening at "Dashboard".
- The backend was already stopped by the time of this evaluation, so the 424/541 count could not
  be re-measured live; the three corroborations above stand in its place. No status depends on a
  claim I could not cross-check.
- J-01 is `partial`, not `failing`, because some acceptance steps genuinely passed (spot-checked
  DELL and GRMN labels are identical across leaderboard, detail header and API; unknown stays
  null / "Unassigned", never invented). This is a factual record, not credit toward the
  deliverable: the coverage wiring and the methodology disclosure are entirely absent.

## Anti-goal Check

Basis: `runs/goal-session-market-compass/iter-0/scan-report.md` (CLEAN) plus
`iter-diff.md` (1 file changed: `docs/goal.md`), plus my own
`git diff 42167cf5..HEAD --name-only`, which shows changes to `docs/goal.md`,
`docs/archive/goal-ops-hardening.md` and `docs/improvement-backlog.md` ONLY — no
`apps/`, `config.yaml`, `scripts/`, or dependency-manifest change exists. `git status
--porcelain apps/` is empty (TC-10 satisfied). With no product change there is no vehicle
for a violation; each row below was still checked against the actual diff scope.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language only from ledger | OK | No code/UI change. Evidence chips unchanged from the ops-hardening GOAL_ACHIEVED state; ledger still 7 FAIL entries so scores read "Not yet proven". |
| AG-2 decision-quality only (no advice) | OK | No new text shipped. QA observed no advice wording on the surfaces it visited. |
| AG-3 displayed numbers correct | OK | QA cross-checked `/stocks` DOM against `GET /api/stocks` (424/541) and DELL/GRMN labels against API rows; matched. |
| AG-4 no overfit edges | OK | No selection rule, model, or claim introduced (zero code diff). |
| AG-5 determinism / no-lookahead | OK | No engine, scoring, or ingest code touched. |
| AG-6 referee gate on evidence claims | OK | No Evidence Claim registered this iteration (`status.json` `evidence_claim_registered: false`). |
| AG-7 no hard-coded credentials | OK | scan-report CLEAN on added lines; diff is documentation-only, 0 untracked source files. |
| AG-8 data-shape/scale resilience | OK | No consumer, ORM query, or data-basis change. |
| AG-9 offline-deterministic ingest | OK | No dependency manifest change; QA used only localhost:8255 / localhost:3255; no ingest job run. |
| AG-10 host resource ceiling | OK | No `scripts/` or `project-extensions/host-guard/` change in the diff; launch scripts untouched. |
| AG-11 no new composite candidate number | OK | No candidate surface exists yet and none was added. |
| AG-12 manifest immutability | OK | No manifest store exists yet; nothing to mutate. |
| AG-13 system-vs-market vocabulary | OK | QA verified live that "Ready"/"GO" stay in the chrome strip and do not appear in market text (UT-J-07 step 3). Note this currently holds vacuously — there is no market-state prose yet to collide with. |
| AG-14 no Tapeology coupling | OK | No imports, network calls, or writes added; nothing outside this repo touched. |
| AG-15 no outcome-tuned selection | OK | No selection rule or threshold introduced. |
| AG-16 cohorts are not controls | OK | No cohort exists yet. |
| Licence changes | OK | No LICENSE or licence-field change in the diff file list. |
| Fabricated/substituted data | OK | Unmapped symbols still serve `sector: null` and render "Unassigned" (GRMN spot-check) — NA over fabrication. |

Coherence audit: `runs/goal-session-market-compass/iter-0/coherence.md` does not exist (not run
at baseline/lean depth). It is not a blocker here because GOAL_ACHIEVED is not in play — every
journey is failing or partial. It must exist and be clean before any future GOAL_ACHIEVED.

Pipeline health: review verdict is PASS (`reports/reviews/goal-market-compass-iter-0-review.md`),
so there is no fail-open signal. Browser QA verdict is FAIL, which is the honest expected result
for a pre-implementation baseline, not a defect introduced this iteration.

## Next-Step Recommendation

Start building. The next iteration should take J-01 "Sector labels are honest and nearly
complete", following the build order the goal itself suggests. Concretely that means: read a
stock's sector from the pool spreadsheet when the curated list does not have it, so that at most
5 in 100 stocks show "Unassigned" instead of today's 78 in 100; add a short paragraph on the
Methodology page saying the sector comes from two sources and only reflects today (not history);
keep unknown names showing "Unassigned" rather than a guess; and prove with a test that every
stock's three scores stay byte-for-byte the same as before, since the sector label is
descriptive only. J-05 "Each close freezes one next-session manifest" is the biggest single
piece of the session and should follow the J-02/J-03/J-04 engine work, because J-06 cannot be
tested at all until a manifest exists.

Run the next iteration at full depth: it is the first iteration of this session that changes
what the owner actually sees on screen, and the goal's own loop rules ask for full depth at that
point.

## Halt Justification (if halting)

Not halting.
