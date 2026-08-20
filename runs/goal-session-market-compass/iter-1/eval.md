# Iteration 1 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The sector work behind J-01 "Sector labels are honest and nearly complete" now really works. On a
fresh run dated 2026-08-12, all 539 stocks show a real sector and none say "Unassigned" — down from
about 78 in every 100. The Methodology page now explains, in plain words, that sector labels come
from the curated list first and the candidate-pool file second, and that they describe today only. I
checked both of these myself against the running app, not just from the reports. J-01 is still not
finished, for one reason only: the picture evidence is missing. The browser test run failed early
(its clean-up-and-rebuild step destroyed two days of data it could not put back) and it was run
against a stale copy of the app, so no screenshot shows the stock list with the new labels, and no
walkthrough video was recorded.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest and nearly complete | partial | partial (advanced; capture-defect, `evidence_makeup`) | `reports/qa/goal-market-compass-iter-1-evidence/AUDIT-01-methodology-sector-basis-visible.png` (disclosure card visible); `reports/phase-goal-market-compass-iter-1-ui-test-results.md` UT-J-01 = FAIL, UT-08 = PASS; `docs/handoffs/goal-market-compass-iter-1-audit.md` §3 (live API + 539-row DOM sweep); evaluator re-measure of `GET /api/stocks` = 0/539 null, DELL=Technology, GRMN=Consumer Discretionary |
| J-02 What changed since previous session | failing | failing (not re-tested — out of scope) | iter-0 evidence still valid; no file in `iter-1/iter-diff.md` touches this surface |
| J-03 Plain-English summary with cited facts | failing | failing (not re-tested — out of scope) | as above |
| J-04 Candidate explains why and why-not | failing | failing (not re-tested — out of scope) | as above |
| J-05 Close freezes one manifest | failing | failing (not re-tested — out of scope) | as above |
| J-06 A frozen manifest never changes | failing | failing (not re-tested — out of scope) | as above |
| J-07 Today page ten-second read | failing | failing (not re-tested — out of scope) | as above |
| J-08 Market page moves over intact | failing | failing (re-tested, unchanged — NOT a regression) | `reports/qa/goal-market-compass-iter-1-evidence/UT-J-08-fail.png` (/market 404, sidebar unchanged) |

No journey regressed. No journey has ever been `passing` in this session, so rule 1 of the decision
tree cannot fire on status alone.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language gate | OK | Added prose is descriptive only; `UT-08-result.png` still shows "Not yet proven" badges on all three scores; grep of added lines for proven/forecast terms returned nothing |
| AG-2 decision-quality only | OK | Grep of added lines for `buy/sell/price target/forecast/expected return/alpha` returned nothing; no order path touched |
| AG-3 displayed numbers correct | OK | Verified at three levels: audit §3 (production expression over the real 539-member universe, live API, full DOM sweep) plus my own independent `GET /api/stocks` re-measure (0/539 null; DELL=Technology; GRMN=Consumer Discretionary) |
| AG-4 no overfit edges | OK | Not implicated — no pattern or edge claim added this iteration |
| AG-5 determinism / no-lookahead | OK | `apps/backend/app/engine/scoring.py:453-458` — the fallback only fills the row's display `"sector"` field; auditor traced that `row["sector"]` is never read again; TC-4 byte-identity fixture passes |
| AG-6 referee gate | OK | This cycle introduces no Evidence Claims (goal.md Loop mechanics) — gate passes automatically |
| AG-7 no credentials | OK | `iter-1/scan-report.md` = CLEAN (no secret, dependency, or license findings on added lines) |
| AG-8 resilience to data-shape change | OK | TC-7 degrades an unrecognized pool sector to "Unassigned" rather than crashing; auditor exercised the widened field's real downstream consumer live (`GET /api/research/event-study` → HTTP 200, honest `low_sample: true`) |
| AG-9 offline-deterministic ingest | OK | Fallback reads the committed `apps/backend/data/seed/universe_pool.csv`; grep of added lines for `requests/httpx/urllib/http(s)://` returned nothing; fresh run 3081 was produced with `provider: seed`; the browser-QA agent correctly refused the live "Fetch + backfill" job under AG-9 |
| AG-10 host resource ceiling | OK | `git diff <snapshot>..HEAD -- scripts/ project-extensions/` is empty — no HOST-GUARD block touched or weakened |
| AG-11 no new composite number | OK | Change adds one descriptive string field; no fit/conviction/probability value introduced |
| AG-12 manifest immutability | n/a | No `next_session_manifests` store exists yet (J-05 territory) |
| AG-13 system-vs-market separation | n/a | No market-state prose added; readiness vocabulary untouched |
| AG-14 no Tapeology coupling | OK | Grep of added lines for `tapeology` returned nothing |
| AG-15 no outcome-tuned selection | n/a | No selection rule or threshold introduced this iteration |
| AG-16 cohorts are not controls | n/a | No cohorts exist yet |

**Not an anti-goal violation, but flag for the owner:** the browser test run permanently destroyed
1,174 price bars, 18 snapshots and 30,439 forward returns for 2026-08-13 and 2026-08-14. Those were
user-added bars from an earlier live fetch, not committed seed data, and the committed seed (through
2026-08-12) is untouched, so no rule was broken and no journey depended on them. Only a live network
fetch could restore them, which the anti-goals forbid without your approval. The app behaved
correctly throughout — it refused to invent snapshots for dates that no longer had bars.

**Coherence:** `runs/goal-session-market-compass/iter-1/coherence.md` = **COHERENCE-PASS** (one home
for the sector value, one producer for the disclosure prose, no new route). No structural veto.

## Next-Step Recommendation

Move on to the next group of journeys: J-02 "What changed since the previous session", J-03
"Plain-English summary with cited facts" and J-04 "Each next-session candidate explains why and
why-not". These three share one producer, so building them together avoids doing the same work
twice. Run that iteration at full depth, because it puts brand-new cards on the home page for the
first time.

Carry three small clean-up jobs alongside that work — none of them is big enough to be an iteration
of its own:

1. Take the missing pictures for J-01. Open the stock list at date 2026-08-12, capture the sector
   column with no "Unassigned" rows and GRMN showing "Consumer Discretionary", and record the short
   walkthrough. No data clean-up is needed first — the run already exists.
2. Fix the walkthrough recorder. It produced nothing this time because of a file-reading error
   (`reports/phase-goal-market-compass-iter-1-demo-results.md` records the parse error).
3. Keep the two small housekeeping items the auditor listed: restore the row the TC-8 test changes,
   and build the valid-sector set once instead of once per row.

**One decision is yours, and the next iteration should not start J-01's re-test until you make it:**
J-01's written steps in `docs/goal.md` tell the tester to delete the last two trading days and
rebuild them. In this setup that deletes data that cannot be rebuilt offline, which is exactly what
happened this run. Please approve changing those words to use a date range the committed data still
covers (or to drop the delete step, since the app already builds the newest day by itself), and to
only click the "Unassigned" filter when that option is actually on screen.
