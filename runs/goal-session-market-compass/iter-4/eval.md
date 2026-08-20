# Iteration 4 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

This iteration made one change: each database connection now keeps 64 MB of pages in memory
instead of 256 MB. The backend's peak memory really did drop — from 4,837,420 kB to
3,439,100 kB, a 28.9% cut — but the goal asked for 2.5 GB or less, and 3.44 GB is 31% above
that. The team reported the miss honestly and did not touch any of the owner-only limits to
make the number look better. Nothing the user sees changed: four important pages were checked
before and after and returned exactly the same bytes. The four working journeys still work.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels are honest and nearly complete | passing | passing (re-verified) | `reports/phase-goal-market-compass-iter-4-ui-test-results.md` UT-J-01 PASS; `reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png` (opened: GRMN row reads "Consumer Discretionary", 1/539, as-of 2026-08-12); `reports/qa/goal-market-compass-iter-4-evidence/UT-J-01-result.png` (opened: `/methodology` "Stock sector labels" two-source + current-only disclosure) |
| J-02 What changed since the previous session | passing | passing (re-verified) | UT-J-02 PASS; `reports/qa/goal-market-compass-iter-4-evidence/J-02-verify.png` (opened: earliest stored session, "there is no prior session to compare against") |
| J-03 Plain-English summary with cited facts | passing | passing (re-verified) | UT-J-03 PASS (replay end-to-end); `reports/qa/goal-market-compass-iter-4-evidence/J-03-verify.png` |
| J-04 Each candidate explains why and why-not | passing | passing (re-verified) | UT-J-04 PASS (replay end-to-end); `reports/qa/goal-market-compass-iter-4-evidence/J-04-verify.png` |
| J-05 Each close freezes one manifest | partial | partial (not tested — out of scope) | carried; `reports/qa/goal-market-compass-iter-3-evidence/UT-02-manifest-historical-badges.png` |
| J-06 A frozen manifest never changes | partial | partial (not tested — out of scope) | carried; `reports/qa/goal-market-compass-iter-3-evidence/UT-02-manifest-historical-badges.png` |
| J-07 The Today page answers the ten-second read | failing | failing (not tested — out of scope) | carried; `reports/qa/goal-market-compass-iter-0-evidence/UT-J-07-fail.png` |
| J-08 Market page moves over intact | failing | failing (not tested — out of scope) | carried; `reports/qa/goal-market-compass-iter-1-evidence/UT-J-08-fail.png` |
| J-09 The backend fits the host | unknown | **partial** (target MISSED) | `reports/perf-budgets.md:12114-12236` (Addendum 40); `docs/handoffs/goal-market-compass-iter-4-dev.md`; merged row UT-J-09 SKIPPED (no UI surface — walkthrough waived by goal.md) |

### J-09 step-by-step (why `partial`, not `passing` and not `failing`)

| Step | Result | Evidence I checked myself |
|------|--------|---------------------------|
| 1. Change only `database.pragmas.cache_size` `-262144` → `-65536` | MET | `iter-4/iter-diff.md`: the whole product diff is 2 files; `config.yaml`'s only hunk is that line. `pool_size: 24` / `max_overflow: 44` still read 24/44 (`config.yaml:126-127`) |
| 2. Measured standing-warm VmPeak ≤ 2,621,440 kB | **NOT MET** | 3,439,100 kB primary (5 flat samples t+40s→t+140s, 465 requests, 0 errors); 4,493,232 kB on the 24-worker stress variant — `reports/perf-budgets.md:12141-12164` |
| 3. Append the dated figure beside the old one, never overwrite | MET | `git diff` on `reports/perf-budgets.md` = 123 insertions, **0 deletions**; the 4,837,420 kB baseline is still at `reports/perf-budgets.md:12018-12025` |
| 4. Concurrent-load burst, zero `QueuePool` TimeoutError | MET | 4,705 burst requests, zero errors; `test_data_manager_concurrency_load.py` 3 passed (`reports/perf-budgets.md:12196-12206`) |
| 5. Same-as-of byte-identity spot check | MET | `/api/dashboard`, `/api/stocks`, `/api/market-phase`, `/api/compass` at `as_of=2026-08-10`, four matching md5 pairs, `cmp` zero-diff (`docs/handoffs/goal-market-compass-iter-4-dev.md:95-102`) |

Four of five steps are met. The one that is the journey's headline promise — the memory number —
is not. Per the status vocabulary, that is `partial`, and the unmet step is written out in full
above so nothing is hidden.

### Notes on the other lanes

- The deterministic replay lane returned FAIL for J-01 with the exact same message as iter-3
  ("step 03 expected 'Consumer Discretionary' did not appear"). The merged file overturned it and
  carries the reconciliation footer. I did not take that on trust: I opened `J-01-verify.png` and
  the row plainly shows GRMN with sector "Consumer Discretionary" (wrapped onto two lines, which
  is almost certainly why the stored script's text match failed). The screenshot wins; the overturn
  is correct. This is now the second iteration in a row this same stale script has cried wolf.
- The merged headline reads **BLOCKED** only because J-09 has a SKIP row under "Missing Target
  Journeys". That is structural, not a defect: `docs/goal.md` waives J-09's walkthrough
  ("deliberately backend-only (no UI surface changes)") and replaces it with the dated VmPeak
  measurement, which was delivered. It does not weaken J-01–J-04.
- All five screenshots are byte-distinct with correct dimensions (md5-checked). Iter-3's
  duplicate/blank-frame problem did not recur.
- Review verdict is PASS (`reports/reviews/goal-market-compass-iter-4-review.md`), so there is no
  fail-open signal. Lean depth meant no audit, QA, ux-regression or demo lane ran.

## Anti-goal Check

Worked from `iter-4/scan-report.md` (**CLEAN** — no secret, dependency or license findings) and
`iter-4/iter-diff.md` (2 files: `config.yaml` one value, `apps/backend/tests/test_db.py` one
assertion). No engine, API, or frontend file was touched at all.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials (AG-7) | OK | scan-report CLEAN; no new env/config file; the one `config.yaml` change is a numeric pragma |
| Paid / external SaaS | OK | no manifest in the diff (`package.json`, `requirements*.txt`, `pyproject.toml` all untouched) |
| License changes | OK | no LICENSE file or license field in the 2-file diff |
| Fabricated / substituted data | OK | the opposite happened: the over-budget figure was recorded verbatim (`perf-budgets.md:12158-12178`) instead of being massaged |
| AG-1 not-yet-proven display | OK | no scoring or display code touched; `J-01-verify.png` still shows every score chip reading "Not yet proven" |
| AG-2 decision-quality only | OK | no candidate/narrative string touched; iter-2's minor wording finding stays closed |
| AG-3 displayed numbers correct | OK | strongest possible evidence: 4 endpoints byte-identical before vs after (`dev handoff:95-102`) |
| AG-4 no overfit edges | OK | no evidence-ledger or claim path touched |
| AG-5 determinism / no-lookahead | OK | no producer, scoring, or forward-return code in the diff |
| AG-6 referee gate | OK | no Evidence Claim introduced this cycle |
| AG-8 data-scale resilience | OK | this iteration reduces memory. `_BarCache.prefill`'s unbounded cold path is a pre-existing open item named in goal.md's own Constraints (c), not introduced here |
| AG-9 offline-deterministic ingest | OK | both bursts were local HTTP GETs against the running backend and the committed seed; zero external network calls (`perf-budgets.md:12230-12231`) |
| **AG-10 host resource ceiling** | OK | verified by me directly in `config.yaml`: `memory_cap_mb: 8192` (:1377), `malloc_arena_max: 2` (:1378), `pool_size: 24` (:126), `max_overflow: 44` (:127), `limit_concurrency: 64` (:1374) — all unchanged. No launch script or `host-guard.env` in the diff. The target was missed and **not** compensated by widening any cap |
| AG-11 no new composite number | OK | no candidate or manifest field added |
| AG-12 manifest immutability | OK | no manifest writer/reader touched; the iter-3 critical stays resolved |
| AG-13 system-vs-market separation | OK | no vocabulary or chrome file touched |
| AG-14 no Tapeology coupling | OK | no import, network call, or write to that repository anywhere in the diff |
| AG-15 no outcome-tuned selection | OK | no selection threshold touched. Note the same discipline was applied to the memory target itself — it was not moved to make the result pass |
| AG-16 cohorts are not controls | OK | no cohort code or caveat text touched |

Result: **no new violation, critical or minor.** Ledger stays at 2 entries, both resolved.

**Coherence:** `iter-4/coherence.md` = **COHERENCE-PASS**. No Data Contract row moved, no new
route or page, blueprint byte-unchanged. No consolidation pass is owed.

**Goal-edit drift:** no `journeys-changed.md` this iteration, so no recorded pass was voided.

## Next-Step Recommendation

Two things need the owner, and one of them is new and important.

**NEW — please rule on the memory result.** The goal says the backend must peak at 2.5 GB or
less. After the change it peaks at 3.44 GB. That is a real 28.9% improvement and it is well
inside the 8 GB safety ceiling, but it is not what the goal asked for. There is a good reason to
think the 2.5 GB figure was set against the wrong cause: this project's own earlier records show
the backend already peaking between 2.69 GB and 3.69 GB on the 30-year data basis long before
anyone looked at connection caches (`config.yaml:1377`). So a floor near 2.5 GB probably existed
already. Please choose one: (a) accept 3.44 GB and mark J-09 "The backend fits the host" done;
(b) keep the 2.5 GB target and authorise more work — the one lever that could actually move it is
re-bounding the `_BarCache.prefill` warm-up, which goal.md already lists as Constraint (c); or
(c) set a different, measured target. The team must not pick for you: the goal forbids moving the
target to make the number pass.

**Still open from earlier turns** (unchanged, none of them block the next build): approve
rewording J-01 "Sector labels are honest and nearly complete" test steps 1 and 2; decide whether
an empty "next-session focus" on the newest date is an acceptable honest result; and decide the
J-06 "A frozen manifest never changes" wording, where the page can never say "the underlying run
is unavailable" because opening it quietly rebuilds the missing day.

**Next iteration.** Build the make-up run for J-05 "Each close freezes one next-session manifest"
and J-06 "A frozen manifest never changes", at FULL depth. Remove and re-add the last two trading
days and actually watch the close seal the record ("at ingest", version 1, "prospective-eligible")
— nobody has ever seen that happen live, and it is the flagship promise of J-05. Then delete a
day, restore it, and watch the "where this came from" line change. Full depth is needed because
the independent auditor found a real breach in exactly this feature last time it ran, and because
the short walkthrough recordings for J-01 through J-04 are now three turns overdue and only the
full pipeline records them. That run will be the first to start two backends at once, so carry two
small safety jobs with it: cap the frontend build at 4 workers (goal.md Constraint (b) — it
currently fans out 16 ways and helped freeze the machine), and make the three memory-pressure test
files skip by default instead of copying the 7.8 GB database. Also fix the stored J-01 test script
that has now wrongly failed twice on wrapped text.

One sentence to act on: **tell the team whether 3.44 GB is good enough, then let it run the
J-05/J-06 make-up at full depth with the frontend-build cap included.**

## Halt Justification (if halting)

Not halting. Two points are worth stating, because both were close calls.

J-09's own text says that if the 2.5 GB target is missed the team must "record the honest measured
figure and stop for owner review". I read "stop" as "stop tuning and report", not "stop the whole
session", because the sentence ends "— never widen the target to pass", which is plainly a warning
against fiddling with numbers until they pass. The iteration's own written plan read it the same
way and treated an honest miss as a finished iteration. Halting everything would also freeze
J-05 through J-08, none of which depend on this number, and there is still real work the team can
do without the owner. The owner decision is instead flagged at the top of the recommendation above
so it cannot be missed.

This is also not a REGRESSION. Nothing that worked stopped working, no owner-set limit was
touched, and the security scan was clean.
