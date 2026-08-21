# Iteration 8 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

This iteration put real data back for the first time. Twenty of the 587 missing company codes now
have prices again on both 11 and 12 August — 40 rows, and not one row outside those two days. I
checked the database myself, read-only, instead of believing the reports: 20 rows on each day, zero
rows on or after 13 August, and every sealed briefing record still untouched. The safety gate the
owner designed was built correctly and behaved correctly. But J-10 "Put back the two days the drill
deleted" is **not finished**, and the owner's own rule now says so in plain words: 20 out of 587 does
not close it, and nobody may invent a "good enough" number. Two other things must be carried
forward, and neither is small: the gate's clean result was measured against the **same supplier**, so
it proves the gate is built, not that it can tell two suppliers apart; and a browser test lane that
this project's rules forbid ran **twice**, the second time during the very re-run that was meant to
add the missing safety review, and it overwrote two protected evidence pictures before the reviewer
put them back.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels are honest and nearly complete | passing | passing (carried, NOT re-verified) | Durable: `reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png` (I re-opened it; GRMN shows "Consumer Discretionary"). Iter-8's own row is quarantined: `reports/qa/goal-market-compass-iter-8-evidence/INVALID-forbidden-lane.md` |
| J-02 What changed since the previous session | partial | partial (carried, not tested) | Blocker re-measured by my own read-only query: 20 of 587 symbols present on 2026-08-11/12 vs 587 on 2026-08-10 |
| J-03 Plain-English summary with cited facts | partial | partial (carried, not tested) | Same as J-02 |
| J-04 Each candidate explains why and why-not | passing | passing (carried, NOT re-verified) | Durable: `reports/qa/goal-market-compass-iter-4-evidence/J-04-verify.png` (weak spot-check — see note). Iter-8's own row quarantined, same file as J-01 |
| J-05 Each close freezes one manifest | partial | partial (carried, not tested) | `reports/qa/goal-market-compass-iter-3-evidence/UT-02-manifest-historical-badges.png` |
| J-06 A frozen manifest never changes | partial | partial (carried, not tested) | Same as J-05; incidental positive observation in `docs/handoffs/goal-market-compass-iter-8-dev.md` step 5(f) |
| J-07 The Today page answers the ten-second read | failing | failing (carried, not tested) | `reports/qa/goal-market-compass-iter-0-evidence/UT-J-07-fail.png` |
| J-08 Market page moves over intact | failing | failing (carried, not tested) | `reports/qa/goal-market-compass-iter-1-evidence/UT-J-08-fail.png` |
| J-09 The backend fits the host | partial | partial (carried, not tested) | `reports/perf-budgets.md:12114-12236`; `config.yaml` re-confirmed git-clean by me |
| **J-10 Bounded recovery of the two deleted days** (TARGET) | partial | **partial — advanced, not complete (20/587)** | `docs/handoffs/goal-market-compass-iter-8-dev.md` steps 4 and 5; `runs/goal-market-compass-iter-8/j10-convention-evidence.json` (88 per-pair records); `docs/handoffs/goal-market-compass-iter-8-audit.md` §2; my own read-only SQL |
| **J-11 Incident-bounded clean regeneration** (NEW) | — | **unknown** (owner insert, spec-only) | `docs/goal.md` commits b6587a71 / c96fc20f / 2227ccd8 / 51ae56d2, all after this iteration's product commit `47d50d04` |

Notes on the two carried `passing` rows: neither was tested this iteration. Their product code is
byte-unchanged (the whole product diff is 4 backend files: `j10_recovery.py`, `yahoo_provider.py`
and two test files — no frontend, no API, no scoring), and their goal text is byte-unchanged
(hashes still match), so evidence durability (methodology A.6) keeps them at `passing`. The only
rows either has this iteration came from the forbidden lane and are discarded **symmetrically** —
not read as a pass, and not readable as a failure — following the iter-7 evaluator's precedent.

`UT-J-10` appears in the merged results file under **Missing Target Journeys** ("no test case
executed by any lane"). That is correct and expected: J-10's walkthrough is waived in `docs/goal.md`
because it has no screen of its own, so its evidence channel is the handoff + the persisted
per-pair artifact + database queries, exactly as J-09's was.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 no unbacked "proven" | OK | No displayed value changed. My query: `next_session_manifests` = 24 rows, `SUM(prospective_eligible)` = 0 |
| AG-2 decision-quality only | OK | No new text, no candidate framing change; backend-only diff |
| AG-3 displayed numbers correct | OK, with a recorded risk | No new displayed value. `GET /api/compass?as_of=2026-08-12` went 400 → 200 because data changed under an unchanged read. Risk recorded: the live "Latest" date moved to 2026-08-12, served by a run built on a 20-of-587 price basis. `docs/goal.md` itself calls those runs "known temporary / recovery-era derived state ... non-authoritative", and its lane gate keeps normal lanes shut until J-11 Stage G. I therefore scored no journey as passing on this iteration's data |
| AG-4 no overfit edges | OK | No edge or pattern surfaced |
| AG-5 determinism / no-lookahead | OK | Zero rows on or after 2026-08-13 (my query). The rebuilt runs carry SPY's last available bar forward through the existing no-lookahead accessor |
| AG-6 referee gate | OK | No Evidence Claim this cycle; ledger unchanged at 7 FAIL |
| AG-7 no hard-coded credentials | OK | `runs/goal-session-market-compass/iter-8/scan-report.md`: CLEAN — no secret, dependency or license finding on added lines |
| AG-8 data-shape / memory resilience | OK | Per-symbol bounded reads; no whole-table load added; reviewer and auditor both traced the module |
| AG-9 offline-deterministic ingest (+ dated exception) | OK — inside the exception | Exactly the two authorized dates, 20 symbols all inside the frozen 587, vendor `yahoo` (authorized), comparison fetch held outside the database. Exception correctly **not** declared exhausted on a partial result |
| AG-10 host resource ceiling | OK (letter); minor concern (spirit) | `config.yaml` git-clean — no owner-set cap moved. But the forbidden lane started a frontend and attempted a backend on a host that froze once. It used the project launch scripts, so the caps applied; no cap was removed, weakened or bypassed |
| AG-11 no new composite number | OK | Bridge factor and dispersion are internal orchestration values, never served, never attached to a candidate (coherence audit confirms) |
| AG-12 manifest immutability | OK | 24 rows, max as-of 2026-08-12, no row mutated or deleted (my query + dev + audit) |
| AG-13 system-vs-market separation | OK | No display change |
| AG-14 no Tapeology coupling | OK | No import, call or write |
| AG-15 no outcome-tuned selection | OK | The three thresholds were fixed in code before the live run and not touched after; the auditor re-derived all 20 verdicts from the persisted artifact alone |
| AG-16 cohorts are not controls | OK | No cohort claim made |
| **AG-17 repair never rewrites provenance** | **VIOLATED (critical) — fixed inside this iteration** | Provenance half held (eligibility, versions, hashes all unchanged; the iter-6 evidence folder is git-clean). The **incident-record half failed**: at 12:53-12:55 the forbidden replay lane overwrote the two quarantined pictures that `INVALID-forbidden-lane.md` names as preserved. The auditor restored them from commit `47d50d04` and kept the second run's bytes beside them. I verified the restore myself: current `J-01-verify.png` md5 `bd13782d00c37abd0a0ee4a17eeb852d` and `J-04-verify.png` md5 `9e9cc6fe68e08e08ab496d6be6c081bd` match `git show 47d50d04:<same path>` exactly, and the two `INVALID-rerun-*` files carry the distinct 12:54 hashes. No database write resulted. **The cause is not fixed** — audit finding P2 proves the forbidden lane runs at full depth too |

Ledger after this iteration: **4 entries, 0 unresolved.**

## Next-Step Recommendation

Do these three things in the next turn, in this order, at FULL depth.

**1. Fix the test lane that keeps running when it is banned — before anything else touches the
database.** A browser replay lane ran against the damaged data twice this iteration. The first time
was blamed on the pipeline quietly downgrading itself to the light mode; that was corrected, and
then the lane ran again anyway, in the careful mode, during the very re-run meant to add the missing
safety review. So the depth setting was never the whole cause. The pipeline simply does not know
that the goal file forbids these lanes right now. Until that is fixed, every future turn can silently
start a second web server and a second backend on the machine that froze on 20 August, and can
overwrite protected evidence. The goal file already demands this (J-11 step 10). This is small,
non-destructive work in the pipeline scripts, not in the product.

**2. Continue the recovery from 20 of 587 — do not restart it.** The owner has already answered the
question the developer stopped on: the rule against enlarging the *methodology test sample* was never
a cap on *how many companies get repaired*. Every one of the remaining 567 companies must be judged
one at a time by the same fixed safety gate, and each one either gets its prices back or is written
down by name with the reason it could not be. Skip the 20 that are already done; never re-fetch or
overwrite them. Three cheap safety fixes ride along, all named by the reviewer: make the evidence
file compulsory rather than optional on the real entry point, refuse a mismatched pair of data
sources, and lock the un-gated back door into the fetch function. Also commit the recovery script
this time — today's run cannot be reproduced from the repository.

**3. Correct one sentence in the goal file — this needs the owner.** The record currently says
Yahoo's prices matched Stooq's stored prices exactly. They did not, because the stored prices in that
window were **already Yahoo's**. The committed Stooq starter data stops on 1 July, and the only Stooq
download this project ever made failed with zero companies (I confirmed both from the database
myself). The gate therefore compared Yahoo against Yahoo and could not have failed. That makes the
40 restored rows *safer*, not riskier — no scale jump was introduced — but the sentence must not
stand as proof that two suppliers agree, and no future work may lean on it.

Also carried and still open, none of them blocking: is 3.44 GB acceptable for J-09; J-06's
"underlying run unavailable" wording; the rewording of J-01's first two test steps; whether an empty
"next-session focus" is an acceptable honest result; and whether MNST joins the recovery list. And
one new one worth knowing: there is a real, un-examined supplier change inside the stored price
history at 1/2 July, created by ordinary downloads back in mid-August — outside this repair's remit,
but any future supplier-comparison work must start from that fact.

In one sentence: **please approve fixing the runaway test lane first, then let the recovery finish
the remaining 567 companies one by one under the same rules, and correct the one sentence that
credits Stooq for prices Yahoo actually supplied.**
