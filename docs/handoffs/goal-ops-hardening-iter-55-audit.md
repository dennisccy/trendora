# goal-ops-hardening-iter-55 Audit Report

**Date:** 2026-08-10
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's headline deliverable — the honest-status completeness fix — is **correct, tightly tested, and independently re-verified by this audit** against the source, the unit tests, and a live run's own DB row and log lines. Nothing in the shipped product code is defective. But the phase GOAL is a three-clause conjunction and only the first clause landed cleanly: TC-5 (zero `/api/health` non-answers) is measurably **NOT MET** (11/1,839, up from 6/1,821 — honestly disclosed and root-caused), and the "give J-04/J-05/J-07's goldens their first real replay execution" clause ended in a **worse** state than it started for J-05: the goldens *were* executed (~01:49–02:09 local, primary evidence survives), but a second, five-journey replay lane at 02:32 **overwrote** `regression-replay-results.md` and destroyed the J-05/J-07 rows, and J-05's single-use target date was consumed without rotation, so its golden is now guaranteed to fail on every future replay.

**Downstream readers must not treat this as a clean pass.** The browser lane's own merged artifact carries **`Browser QA Verdict: BLOCKED`** with "no test case executed for J-05/J-07 by any lane" (`reports/phase-goal-ops-hardening-iter-55-ui-test-results.md:8,35-36`), while the QA report (`reports/qa/goal-ops-hardening-iter-55-qa.md:7,110`) records **PASS** and cites J-05/J-07 rows that do not exist in the file it cites. Three DoD items are unmet. This verdict certifies the **code**, not the iteration's evidence completeness.

---

## 2. Findings

Per the phase spec's binding TC-11 / lane-ordering rule (spec lines 54, 98, 121) — carried verbatim from iter-53/54 — every defect found in this post-lane audit is **filed as an iter-56 note, not applied**. See §4.

### Backend Findings

**B1 — VERIFIED CORRECT (no defect): the honest-status fix does what it claims.**
Full code trace, not a handoff read. `apps/backend/app/engine/data_manager.py:4244-4245` replaces the latching bool with `_forward_horizons_total`/`_forward_horizons_completed`; `:4281` increments only on a genuinely completed horizon; `:4300` computes `forward_aggregates_warmed = _forward_horizons_completed == _forward_horizons_total` **after** the loop, so a `MemoryError` `break` at `:4288` can no longer be outrun by an earlier horizon's success; `:4301-4302` gates the `refreshed.append`. Isolate-and-continue (AG-8) is intact — the `break` still falls through to `research_hot_keys`/`index_series`/`factor_lab_all`/`drawdown_expectations`, and the run's own `status` is untouched. I checked the obvious escape hatch (an **empty** horizons list would make `0 == 0` → `True` and silently re-open the exact hole this fix closes): it is **unreachable**, because `apps/backend/app/config.py:766` declares `horizons: list[int] = Field(min_length=1)`. Duplicate horizons also count consistently on both sides. No escape hatch found.
Evidence I ran myself: `.venv/bin/python -m pytest tests/test_data_manager.py -k forward_aggregates -q` → **5 passed in 1.46s**.
Live success-path evidence (not inherited): run `6f19678a…` = `data_provider_runs.id=365` logged all five horizons — `logs/backend.log:240045,240080,240115,240143,240176` (h1 41.75s, h5 23.13s, h10 23.10s, h20 22.92s, h60 22.73s) — and its persisted row lists `forward_aggregates` among eight categories. TC-3's success path is therefore proven live, not only in a fixture.

**B2 — GAP (not fixed, filed): the GIL-holding fix's profile-first requirement is not evidenced, and the fix moved no metric.**
The spec (line 44) binds the iter-48/50/53 discipline: *"profile the per-horizon compute call chain … do not assume the cause or force-fit a prior iteration's specific mechanism."* The shipped constant's docstring at `apps/backend/app/engine/forward_testing.py:1124` cites *"24,272-51,778 rows live against the real committed DB (iter-55 profiling note, `reports/perf-budgets.md`)"* — **that note does not exist**. `grep -rn "24,272\|51,778\|24272\|51778"` over the repo returns the code comment, the dev handoff, and the review packet only; nothing in `reports/perf-budgets.md`, and `runs/goal-ops-hardening-iter-55/` contains no profiler artifact of any kind (only the four unmodified drill scripts and `tc5-drill-out/`). A code comment citing a measurement to an artifact that does not contain it is a dangling citation.
The consequence is measurable: the treated stretch was **not** the dominant one. `logs/backend.log` horizon=10 elapsed, concurrent-load runs: **336.67s** and **437.89s pre-fix**, **438.40s post-fix** (`53449eb…`, the Addendum 19 drill). Non-answers went **6 → 11**. Addendum 19 says this itself, to the developer's credit. So the applied mechanism (`_FORWARD_AGG_ROW_YIELD_CHUNK = 5_000` at `forward_testing.py:1139`, used at `:1169-1170` and `:1325-1326`) is the *plan's candidate*, applied and then found not to be the cause — which is what a profile was supposed to establish beforehand. The change is byte-identity-safe (B3) and harmless, but it is **unvalidated scheduling code shipped into the two hottest row loops**.
Secondary observation, not established as a regression: solo h10 reads 19.82s (2026-08-08, pre-fix) vs 23.10s (2026-08-10 03:08, post-fix) — a ~15% delta confounded by DB growth to 8.37 GB. Worth re-measuring, not worth acting on now.

**B3 — VERIFIED CORRECT (no defect): byte-identity of the yield fix.**
`enumerate(...)` + `row_i % N` + `time.sleep(0)` cannot alter a value, an order, or a grouping; the test proves it rather than asserting it. I ran the file myself: `pytest tests/test_forward_testing_aggregates_streaming.py -q` → **58 passed in 16.87s**, including `test_compute_forward_aggregates_byte_identical_with_row_yield_firing_every_row` (`:395`), which monkeypatches the chunk width to **1** so the new yield fires on *every* row, across all five horizons × {`as_of=None`, historical} = 10 cases against the pinned pre-rewrite oracle. AG-3/AG-5 hold.

**B4 — GAP (not fixed, filed): TC-5 is not met; the owner-rescoped J-07 acceptance clause is also not met under concurrent load.**
I re-derived Addendum 19's numbers from the raw drill CSV rather than trusting the prose: `runs/goal-ops-hardening-iter-55/evidence-drill/tc5-drill-out/health-polls.csv` → **1,839 polls, 1,828×200, 11×`000`, 57 answered slower than 2.0s, worst answered 4.788s** — matching `reports/perf-budgets.md` Addendum 19 (line 8808+) exactly. The root-cause evidence also verifies: `research-load.csv` rows 1-3 show `/api/research/factor-lab?all=true` receiving **no response in 600.008s** (then 600.101s on a later attempt) and `/api/research/factor-combination` taking **429.412s**, straddling `forward_aggregates_warm[10]`'s window. The GIL-convoy diagnosis is supported by first-hand data, and re-treating `compute_factor_lab_all`/`compute_factor_combination` is genuinely outside this iteration's IN SCOPE list.
The honest consequence the artifacts do not state plainly: the owner's own rescoped J-07 acceptance clause (`goal-slice-bqa.md`: *"during a bounded background-compute window … every poll answers HTTP 200 under a relaxed ≤2s ceiling; a frozen or unresponsive window … remains a failure"*) is **failed** on these conditions (11 non-answers, 57 polls >2.0s) and **met** on the no-concurrent-research-load conditions (F3 below). J-07 should be scored with that distinction, not as a flat pass or a flat fail.

### Frontend Findings

None. `git status --porcelain -- apps/frontend` is empty; Frontend Present is `no`; the `/data` run-detail `aggregates_refreshed` list simply loses a member on the partial-completion path, with no markup change. AG-10's five frozen host-guard paths (`config.yaml`, `project-extensions/host-guard/host-guard.env`, `scripts/start-backend.sh`, `scripts/dev.sh`, `scripts/start-frontend.sh`) are clean on **both** `git status --porcelain` and `git diff --stat` — re-verified by this audit, not inherited (TC-12/AG-10 ✓). AG-9 re-verified independently: all 30 most-recent `data_provider_runs` rows, which covers every row this iteration created (ids 352-365), read `provider = 'seed'`.

### Test / Verification-Infrastructure Findings

**T1 — IMPORTANT (not fixed, filed): J-05's single-use golden was consumed this iteration and not rotated — every future replay is now guaranteed to FAIL.**
`runs/goal-session-ops-hardening/journey-scripts/J-05.json:16` (step 10) asserts the run's own breakdown reads `"1 calendar day · 0 already snapshotted · 0 non-trading"`, and the script's own `_notes:28` states the contract: *"the target date must have 0 snapshot rows when this runs … Rotate to another 0-row trading day (and update steps 2/3/13/14) if a later lane consumes this one."* This iteration's own replay consumed it: `scanner_runs.id=2940, asof_date='2010-11-08', created_at='2026-08-10 00:49:13'` (UTC), written by `data_provider_runs.id=356` (`snapshots_created=1, already_snapshotted=0`). A second, concurrent `demo_runner` instance then hit the same date and recorded `already_snapshotted=1` (`data_provider_runs.id=359`) — i.e. the failure mode is already demonstrated in this iteration's own data. The golden was left un-rotated, so the next lane will read `"1 already snapshotted"` and fail step 10, which will present as a J-05 product regression when it is a fixture-exhaustion artifact.
To make the follow-up cheap I verified candidate replacements directly against the DB (bars present in the committed seed, zero `scanner_runs` rows): **2010-11-10, 2010-11-11, 2010-11-12, 2010-11-15, 2010-11-16** (466 `daily_prices` rows each, 0 snapshots). Rotation must update steps 2/3/13/14 as the script's notes require, and be re-verified live before use.

**T2 — IMPORTANT (not fixed, filed): the J-05/J-07 result rows were destroyed by a second lane run, and QA reported PASS over a BLOCKED lane.**
Reconstructed from mtimes and the DB, not from prose. The developer's replay ran ~01:49–02:09 local and produced `J-05-verify.png` / `J-07-verify.png` (both 02:09) plus a 7-row results file the reviewer read at 02:25 (the review report cites J-05/J-07 as PASS). A **second**, five-journey replay lane then ran at 02:32 and **overwrote** `reports/phase-goal-ops-hardening-iter-55-regression-replay-results.md`, which now reads `**Overall:** 5/5 journeys passed` with rows for J-01/J-03/J-04/J-08/J-09 only (`:11,19-23`) — no J-05 row, no J-07 row, and no trace of the dev handoff's "6/7 PASS + reconciliation note". `runs/goal-ops-hardening-iter-55/replay-lane/verify-run.log` is **0 bytes**, so the run log is gone too.
The merge step caught it correctly: `reports/phase-goal-ops-hardening-iter-55-ui-test-results.md:8` reads **`Browser QA Verdict: BLOCKED`**, and `:35-36` lists *"`UT-J-05` — no test case executed for J-05 by any lane"* / *"`UT-J-07` — no test case executed for J-07 by any lane"*, under a guard whose own text names the precedent (*"ops-hardening iter-41 audit finding B2 … iter-41 itself shipped a clean PASS 6/6 headline while its two target journeys had zero rows anywhere"*). Despite that, `reports/qa/goal-ops-hardening-iter-55-qa.md:7` records **PASS**, `:110` asserts *"Target journeys J-05 and J-07 were executed (both PASS per regression-replay-results.md)"* — a citation to rows that were **already absent** from that file when QA wrote at 02:38 — and `runs/goal-ops-hardening-iter-55/status.json:9-11` lists only TC-5 as a blocker, omitting the BLOCKED lane entirely. DoD items 1 and 7 (spec lines 90, 96; TC-8/TC-9) are therefore **unmet as artifacts**.
Mitigating, and the reason this is IMPORTANT rather than CRITICAL: the *behavioral* evidence DoD item 1 actually asks for ("DB rows, HTTP statuses, log phase-timing lines") **does** survive this iteration, independently of any lane table — see F3.

**T3 — GAP (not fixed, filed): three LLM-lane rows share one screenshot.**
`reports/qa/goal-ops-hardening-iter-55-evidence/` — `UT-01-result.png`, `UT-02-result.png` and `UT-04-result.png` are byte-identical (`md5 4b6046907870798099348cfa77b17e2e`), and `UT-03-result.png` is 2,105 bytes (effectively empty). Three distinct assertions in `ui-test-results.md:23,24,26` are evidenced by a single image. The underlying claims for UT-02/UT-04 are separately corroborated (F3), so this is an evidence-hygiene gap rather than a false claim, but the screenshots themselves prove nothing.

**T4 — GAP (not fixed, filed): `test_forward_testing.py` (93 tests) never completed.**
Disclosed by dev and reviewer; I did not re-attempt it (session-scoped `loaded_engine` over the 30-year basis; the session-wide ~10-11h suite cost is documented). The four files exercising the touched functions all pass, including the two I re-ran myself. Recommend a dedicated early-session run.

**T5 — GAP: the DoD's "SAME drill" byte-identity was proven at unit level, not on the live basis.**
Spec line 95 asks for byte-identity *"the SAME drill's `forward_aggregates_warm`"*; what exists is the oracle test on the `multi_run_engine` fixture with the yield forced every row (B3). For a `time.sleep(0)` insertion the unit-level proof is arguably the stronger one — it makes the yield fire on 100% of rows, which the live drill never would — so I record this as a documented substitution, not a hole. Unsure between GAP and OBSERVATION; recorded as the higher.

**T6 — OBSERVATION: J-04's `wait_for` fix is structurally right; "mid-boot at replay start" is not independently evidenced.**
`journey-scripts/J-04.json` step 2 now waits on the **same** `[data-testid="readiness-badge"][data-state="ready"]` CSS selector step 3 asserts, with a 20,000 ms budget, before the assertion — exactly what the binding iter-54 lesson specifies, and the wait is a real Playwright condition wait, not a sleep. It replayed PASS (`J-04-verify.png`, 02:32). The second half of DoD item 8 ("passes against a backend that is mid-boot at replay start") is not provable from the artifacts: `runs/goal-ops-hardening-iter-55/replay-lane/backend-launch.log` is 0 bytes. The race is closed by construction regardless.

---

## 3. Domain Assessment

The domain logic is sound and the fix is the right shape. The bug class was a **latching completeness flag**: a single bool set `True` inside a per-item loop, never reconciled against the loop's own exit path — so "at least one succeeded" masqueraded as "all succeeded" for a five-member set. The fix does not invent a new field, a new status value, or a second code path; it counts what completed and compares against what was configured, which is the minimal correct expression of the property and matches the drop-on-incomplete convention the sibling gates already use. The interpretation call (drop the member rather than introduce a literal `partial` marker) is logged with grounds at `runs/goal-session-ops-hardening/state/assumptions.md` iter-55 and is defensible.

One honesty cost of that interpretation is worth stating for the evaluator, since the iter-54 evaluator's phrasing was "say partial": after this fix, a run that genuinely warmed horizons 1/5/10 is now indistinguishable in `aggregates_refreshed` from a run that warmed **none** — the field under-claims in the other direction. The spec explicitly puts a tri-state marker OUT OF SCOPE (line 86), so this is an accepted, documented cost, not a defect; but "honest" here means "never over-claims", not "reports what actually happened". Downstream consumers that need the difference must read the per-horizon sub-phase timing lines (`logs/backend.log`, `phase=forward_aggregates_warm horizon=N`), which the code emits in a `finally` and therefore always writes.

The test suite around the fix is genuinely tight, not decorative. The new live-incident test (`tests/test_data_manager.py:2092`) pins `cfg.walk_forward.horizons == [1,5,10,20,60]` against the real config, asserts `calls["n"] == 4` (proving the loop ran three real computes and stopped at the raiser, so the test cannot pass via a signature mismatch that silently routes to the outer `except Exception`), asserts the omission, **and** asserts seven named siblings are still present — so a fix that over-narrowed and dropped a sibling would fail. The pre-existing partial-success test at `:2054` was correctly **inverted** rather than deleted, which is the strongest available proof that behavior actually changed: it previously encoded the buggy behavior as correct, and it now fails against pre-fix code by inspection.

The GIL work is where the domain reasoning is weakest. The mechanism is provably safe and provably useless on the measured evidence, and the profile that was supposed to select the target left no artifact (B2). The right conclusion — which Addendum 19 reaches honestly — is that this class of non-answer is not closable inside a single-process GIL-scheduled architecture once a second heavy compute is in flight, which is precisely the owner decision open since iter-50/51. Continuing to add yield points to individual computes is now demonstrated to be the wrong lever.

---

## 4. Fixes Applied During This Audit

**None — deliberately, and required.**

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No file was modified by this audit. |

The phase spec makes non-application a **Definition-of-Done item**, not a preference: spec line 98 requires that *"no `apps/backend/**`/`apps/frontend/**` file's mtime postdates the 8-journey lane's own artifacts"*, and TC-11 (line 121) requires audit findings be *"filed as a note for iter-56"*. I verified the invariant holds and preserved it: latest product-code mtime is `apps/backend/app/engine/forward_testing.py` at **00:31:42**, latest touched test at **00:35:21**, while the lane's earliest artifacts start at **01:49** (run 356) with lane screenshots at 02:09/02:32. **TC-11 ✓.** Applying even a one-line fix would have invalidated this iteration's own lane evidence for the tree it measured.

All verification I performed was read-only: `sqlite3` opened `file:…trendora.db?mode=ro`, and the two pytest runs (5 passed / 58 passed, cited above) touch no tracked file.

### Filed for iter-56

1. **Rotate J-05's golden target date (T1, IMPORTANT).** 2010-11-08 is consumed (`scanner_runs.id=2940`). Pick from the verified 0-snapshot candidates 2010-11-10/11/12/15/16 (466 seed bars each), update `J-05.json` steps 2/3/13/14, re-verify live before the lane runs. Without this, J-05's replay fails next iteration for a non-product reason.
2. **Re-execute and record J-05/J-07 rows, and make the replay lane non-destructive (T2, IMPORTANT).** The lane currently overwrites `regression-replay-results.md` wholesale, so a later narrower run silently erases a broader earlier one; `verify-run.log` was also truncated to 0 bytes. Either write per-run files or merge rows. Until then, **score J-05/J-07 from the primary evidence in F3 below, never from the current results table.**
3. **Reconcile the QA verdict with the browser lane (T2).** QA reported PASS citing rows absent from the cited file, over a lane whose own merged verdict is BLOCKED; `status.json` blockers omit it. The guard worked — the report did not read it.
4. **Do not add further yield points to individual computes (B2/B4).** The measured result (11 vs 6 non-answers; h10 438.40s vs 336-438s) says the lever is exhausted. Escalate owner decision (a) — move heavy compute to a separate process/worker boundary — which is now backed by first-hand data (a concurrent request starved for 600s+ in-process).
5. **Fix the dangling citation at `forward_testing.py:1124`** — either publish the iter-55 profiling note in `reports/perf-budgets.md` or amend the comment to state where the 24,272-51,778 row range came from.
6. **Re-run `test_forward_testing.py` early in a session (T4)** for a clean signal on the one file that never finished.

### Primary evidence that survives for J-05 / J-07 (for the goal-evaluator)

DoD item 1 asks for *"real behavioral evidence (DB rows, HTTP statuses, log phase-timing lines) — never a lane's sparse-poll summary alone."* That evidence exists this iteration and is independent of the lost lane rows. I verified each item directly:

- **J-05 (aggregates precomputed at ingest):** `data_provider_runs.id=356` — 2010-11-08, `snapshots_created=1`, `already_snapshotted=0`, `forward_returns_inserted=1370`, `status='ok'`, `aggregates_refreshed` includes `forward_aggregates`; producing `scanner_runs.id=2940`. And `data_provider_runs.id=365` — 2005-06-16→2005-06-22, 5 snapshots, 4,115 forward returns, `status='ok'`, all eight categories refreshed, with all five horizons logged at `logs/backend.log:240045-240176`.
- **J-07 (heavy aggregates never take the service down), favourable conditions:** during run 365's full finalize tail (`forward_aggregates_warm` 133.65s, `factor_lab_all_warm` 576.61s, `drawdown_expectations_warm` 347.66s), `reports/qa/goal-ops-hardening-iter-55-evidence/UT-04-health-poll.log` records **459/459 HTTP 200, zero non-answers, zero polls >2.0s, max 1.708s** — I re-parsed the raw log to confirm. Caveat: mean sampling interval **2.58s**, not 1 Hz, so it is sparser than the outage class it excludes (the binding iter-54 poll-density lesson) and must not be read as superseding the 1 Hz result below.
- **J-07, adversarial conditions:** Addendum 19's 1 Hz drill with a concurrent research load — **11/1,839 non-answers, 57 polls >2.0s** (re-derived from `health-polls.csv`). This is the honest ceiling.

Read together: the ingest-time-aggregates behavior is solid, and health survives a heavy finalize tail cleanly **unless** a second heavy request is computing at the same time.

---

## 5. Recommended Next Step

**Do not close this iteration as GOAL_ACHIEVED, and do not carry the "5/5 PASS" headline forward.** The product code is sound and materially stronger than before — the completeness hole that made run 351 lie is closed, proven by an inverted test, a live-incident-shape fault-injection test, and a live all-horizons run — but three DoD items (1, 5, 7) are unmet and the browser lane's own verdict is BLOCKED.

Proceed to **iter-56** with a narrow, evidence-repair scope: rotate J-05's golden date (note 1), re-execute J-05/J-07 and record their rows non-destructively (note 2), and make the QA step read the merged lane verdict rather than a stale citation (note 3). That is cheap, unblocks honest scoring of both target journeys, and does not touch product code.

Then stop iterating on the availability ceiling until the owner answers decision (a). This iteration produced the strongest evidence yet that further per-compute yield tuning cannot close it: a request starved for 600+ seconds *inside the same process* while every individual compute was already yielding cooperatively. Iterations 50, 52, 53, 54 and now 55 have each spent their risky change on this lever; the data now says the lever is exhausted and the decision is architectural. J-06's DB-growth latency regression (deferred with grounds this round) remains the other open front and should be profiled before it is touched.
