# goal-ops-hardening-iter-49 Audit Report

**Date:** 2026-08-05
**Auditor:** Hard audit pass — skeptical, evidence-based (THIRD audit of this iteration; the two prior
audit reports for iter-49 no longer exist on disk, so this one is written from the artifacts and the code,
not from them. Their dispositions survive in `runs/goal-ops-hardening-iter-49/status.json`'s
`audit_fix_pass` / `audit_fix_pass_2` blocks and in `reports/perf-budgets.md` Addenda 5-6, both of which
I re-verified rather than assumed.)

---

## 1. Executive Verdict

**Verdict:** FAIL

The product change is real, correctly diagnosed, provably byte-identical, and I verified its central
claim independently: the finalize tail's cost is now attributable per horizon and per claim in the live
log, the per-claim numbers sum exactly to the whole-phase total, and TC-1's 1,200 s bound is met on 3/3
committed live runs. **The FAIL is not about that code.** It is that four of the seven DEFINITION OF DONE
items are still unmet, all for the same structural reason as the previous two audits: the 8-journey lane
has never run against this build. Its artifacts are timestamped 10:07 / 10:46 — *earlier* than the newest
product-code mtime (12:34:46), so TC-7(a) fails by construction; J-04, J-08 and J-09 have zero executed
rows, so TC-7(b) fails for the fourth consecutive round; and the one lane run that did execute recorded
the backend **crashing** with an uncaught `MemoryError` and staying down 6+ minutes during exactly the
finalize tail this iteration targets — J-07's own promise, falsified live, by a function this iteration
deliberately did not touch. Two IMPORTANT findings were new to this pass and are fixed below; both are
test-asset-only, so the product-code mtime is still 12:34:46 and the pending lane can still satisfy
TC-7(a).

---

## 2. Findings

### Backend Findings

**B1 — CRITICAL (carried, not fixed): an uncaught `MemoryError` in `compute_factor_lab_all` takes the
whole backend down during the finalize tail — J-07 falsified live this round**
`apps/backend/app/engine/research.py:1051` (`ordered = sorted(obs, ...)` inside `compute_factor_lab_all`,
defined at `:990`) materialises and sorts a full per-factor/per-horizon observation list with no
`MemoryError` handling and no bound. During this round's own browser lane
(`reports/phase-goal-ops-hardening-iter-49-ui-test-results.md`, "Critical Finding") an operator-realistic
page load of `/research/factor-lab` while a backfill's `drawdown_expectations_warm` was running produced:
this iteration's own graceful memory-pressure abort (caught, logged — the isolation convention working),
then an *uncaught* `MemoryError` at `research.py:1051`, then `OpenBLAS error: Memory allocation still
failed after 10 retries, giving up` and process death; `logs/backend.log` stops at that line, nothing
listened on 8255 for 6m39s, and the job (`data_provider_runs.id=312`) never reached a terminal status.
I confirmed the aftermath directly in the committed DB: run 312 shows `status='interrupted'`,
`finished_at='2026-08-05 09:48:50'` — i.e. it only reached a terminal value because a *later restart*
reaped it, not because the job finished.
*Not fixed.* It is outside this iteration's diff (`git diff` confirms `compute_factor_lab_all` untouched)
and a second risky change on the concurrency/memory axis against goal.md's binding "one risky change per
iteration". This is now the **fifth** concurring judgment to carry it (two prior audits, both fix passes,
reviewer MINOR-2, and this audit). It is the real J-07 blocker and must be the next iteration's primary
scope, bundled with B2 as ONE change.

**B2 — IMPORTANT (carried, not fixed): the boot-path drawdown warm gets neither the memoization nor an
interlock**
`apps/backend/app/engine/warmup.py:198` calls `forward_testing.compute_drawdown_expectations_cached(
session, claim, cfg)` per claim with no `phases=` argument and no coordination with the ingest loop, so
every MISSing claim on the boot path still pays its own all-history `phase_context_by_date` read —
measured at ~23.6 s live (`reports/perf-budgets.md` Addendum 6, correction 1), i.e. ~118 s of redundant
boot work for 5 MISSing claims, and a second uncoordinated heavy loop that can stack against the ingest
loop under memory pressure. Carried with B1 per the same recommendation.

**B3 — GAP (new this pass, not fixed): the `phase_context_by_date` precompute is unconditional — it runs
before the ledger is known to be non-empty and regardless of whether every claim will be a cache HIT**
`apps/backend/app/engine/data_manager.py:4117` computes the timeline at the head of the
`drawdown_expectations_warm` block; the ledger read is at `:4100-4104` (degrading to `ledger_entries = []`
on failure) and the loop guard is at `:4143`. Consequences, both measurable: an ingest whose ledger is
missing/corrupt, and a **zero-work re-run** (J-01's own journey — every claim a cache HIT, since the
dataset version does not bump), now pay ~23.6 s of pure waste in the finalize tail, and that window is a
single uninterrupted blocking stretch that breaches J-07's ≤2 s health ceiling (13 slow polls land inside
it, 3/3 runs — Addendum 6). Net across a real gap-insert it is still a large *win* (1 call replacing 5),
which is why this is a GAP and not a regression. Deliberately **not** fixed: guarding it is a product-code
edit, which would reset `data_manager.py`'s mtime and re-open TC-7(a) for the lane that still has to run.
(A prior audit recorded the empty-ledger half of this as B5/OBSERVATION; the cache-HIT half and the health
-stall consequence are new.)

**B4 — GAP (new this pass, not fixed): the per-claim timing identity is not guaranteed unique**
`apps/backend/app/engine/data_manager.py:4152` builds `_claim_id` from
`kind : (factor|subject|cohort|signal) : h<horizon>` and omits `slice_kind`/`decile`. Two decile-scoped
claims on the same factor and horizon (e.g. D1 and D10 of `leadership_score` at h20 — a shape the live
ledger already uses for 5 of its 7 claims) would emit an identical identity, and TC-2's attribution would
be undecidable for that pair while still *looking* satisfied. Not reachable today: I read all 7 per-claim
lines from a live drill in `logs/backend.log` and every identity is distinct
(`factor:leadership_score:h20`, `event-study:Breakout-watch:h20`, `factor:ma_stack:h20`,
`factor:vcp_contraction:h20`, `factor:vcp_contraction:h60`, `combination:composite:h20`,
`factor:rs_spy_3m:h60`). `forward_testing._drawdown_expectations_cache_subject(claim)` — which the plan
itself named as an alternative — is collision-free and would be the fix. Product-code edit; deferred for
the same TC-7(a) reason as B3.

**B5 — OBSERVATION: the threaded timeline is pinned for the whole ~800 s loop**
`_dd_phases` is computed once and reused across a loop that ran 789-801 s live. If a concurrent writer
bumped the dataset version mid-loop, claims computed after the bump would be persisted into
`event_study_cache` under the *new* version stamp while having been computed against the *pre-bump*
timeline (before this iteration each claim self-computed and was self-consistent). Unreachable today —
the job engine serialises data jobs — and the divergence would be minute. Recorded, not fixed.

### Frontend / Evidence-lane Findings

**F1 — CRITICAL (gap, not developer-fixable): DoD items 1-4 — the 8-journey lane has not run against this
build**
Mtimes: `reports/phase-goal-ops-hardening-iter-49-regression-replay-results.md` = 10:07,
`...-ui-test-results.md` = 10:46; newest product-code mtime (`data_manager.py`/`forward_testing.py`/
`research.py`) = **12:34:46**. The lane therefore predates the last product-code-adjacent event and
**TC-7(a) fails by construction**. TC-7(b) fails too: the deterministic replay lane was BLOCKED 0/5
("backend unreachable"), and in the browser lane J-04 = SKIP (structurally — that agent is forbidden from
restarting services), J-08 = SKIP, J-09 = SKIP; J-05 (UT-02) and J-07 (UT-05) executed and **FAILED**.
That is three journeys at zero executed rows, the exact gap written into the spec for the fourth
consecutive round.
Both preconditions for a clean re-run now hold, and I verified them rather than trusting the handoff:
backend UP and healthy on 8255 (`GET /api/health` → 200 in 0.090 s, `readiness: "ready"`, warmup 89/89,
pid 667310 started 13:24:52), frontend UP on 3255, **no `data_provider_runs` row left in `running`**
(checked directly — the crashed run 312 was correctly reaped to `interrupted`), and no product code
touched since 12:34:46 (this audit's own fixes are test assets only). The lane is not developer work and
must not be produced by whoever scores it.

**F2 — IMPORTANT (FIXED in this audit): J-05's golden still targeted a date this round's own lane had
already consumed — a re-run would have reported PASS on work it did not do**
`runs/goal-session-ops-hardening/journey-scripts/J-05.json` targeted `2012-01-05` in 5 places. That date
was consumed at 09:21 UTC today by the browser lane's UT-02 (`data_provider_runs.id=312`,
`snapshots_created: 1`); `scanner_runs` now holds exactly 1 row for `2012-01-05`. A re-run as written
would have executed a **zero-work** job while steps 6/8 ("1/1 dates", "1 snapshots") matched the
persisted history panel's own text and steps 9/10 matched the snapshot the *previous* run created — a
fabricated PASS on this iteration's own target journey, and precisely the combination of the iter-48
audit's F2 (page-wide-text scoping, out of scope this round: it needs a frontend testid) and the binding
iter-48 lesson ("a journey's PASS must rest on a row the work itself caused"). The phase spec's TESTING
REQUIREMENTS anticipate exactly this and mandate rotation; nobody had performed it, because the
consumption happened in the lane, after the dev pass.
*Fix applied:* rotated to `2012-01-04`, verified before the edit against the committed DB — 480 symbols
carry bars for that date and `scanner_runs` has **no** row for it, so it is a genuine historical-gap
insert (it now sits between the snapshotted `2012-01-03` and `2012-01-05`). JSON re-parsed after the edit.
Rotation logged here per the iter-46 lesson.

### Test Findings

**T1 — IMPORTANT (FIXED in this audit): nothing in the suite asserted either new sub-phase timing log
line, and nothing pinned the memoization the iteration's bound depends on**
The phase spec's TESTING REQUIREMENTS list "per-horizon/per-claim sub-phase timing tests" as required
work, and the DoD requires "new tests from TESTING REQUIREMENTS added and green". A grep of
`apps/backend/tests/` for the log text, for `sub-phase`, and for `phase_context_by_date` call-counting
found **no** such test: TC-2's only evidence was three live-log reads. The same gap covered the actual
bound — `phases` is threaded into every claim, but nothing proved the timeline is computed *once per
finalize invocation* rather than once per claim, and the byte-identity proofs cannot catch it (both paths
are byte-identical **by construction**; deleting `phases=_dd_phases` restores the per-claim cost with
every existing assertion still green). The QA report additionally credits TC-2 to
`test_research_streaming.py`'s new tests and `test_data_manager.py`'s error-isolation tests — neither
asserts anything about sub-phase timing.
*Fix applied:* `apps/backend/tests/test_data_manager.py:2070`,
`test_finalize_hook_sub_phase_timing_names_each_horizon_and_claim_and_memoizes_phase_context` — asserts a
sub-phase line for every configured horizon (1/5/10/20/60), exactly one per-claim line naming
`factor:leadership_score:h20` (and explicitly rejecting a bare loop index), that both pre-existing
whole-phase lines still fire (additive, not replaced), and that `phase_context_by_date` is called
**exactly once** for an invocation whose claim genuinely produced a payload. Mutation-proven, see §4.

**T2 — GAP (carried, disclosed, not fixed): `test_warmup.py::test_warmup_loads_each_symbol_at_most_once_
across_cadence_and_forward_returns` fails.** Proven pre-existing by the fix pass via restore-to-HEAD
reproduction (identical failure in 82.62 s, files then restored byte-identically). Correct disposition —
new scope, not an audit-fix item.

**T3 — GAP (carried): `test_forward_testing.py::test_walk_forward_asof_dates_are_real_trading_days_with_
full_horizon` has still never been run.** Its session-scoped `loaded_engine` fixture is a multi-hour build
on the 30 y basis, and starting one now is the same concurrent-load mechanism behind B1's crash with a
lane re-run pending. Correct disposition; it covers code this diff does not touch.

### QA-artifact Finding

**Q1 — IMPORTANT (not fixable by an auditor — must be re-run, not patched): the QA report asserts a
Definition of Done that every artifact it cites contradicts**
`reports/qa/goal-ops-hardening-iter-49-qa.md` (12:55) records **Verdict: PASS**, "Definition of Done ✓
Met", and "Blockers: **None**". Against the record: (a) it never mentions
`reports/phase-goal-ops-hardening-iter-49-ui-test-results.md` — the browser QA verdict **FAIL**, 6/15,
with a 6-minute backend outage — for the same phase; (b) it states "Frontend Present: yes" where the spec
and plan both say **no**; (c) it states `current_step: review_passed` where `status.json` reads
`dev_complete`; (d) it describes the review it cites as having a "single disclosed gap" when that review
(12:48/13:23) records `definition_of_done: partial` and three issues, none of them the health-poll gap;
(e) it credits TC-2 to tests that assert nothing about it (T1); and (f) its own TC-4 table reports "PASS
on run 1 (0 non-200)" — true but not the same claim as clean: I recomputed from the committed
`-health.csv` samples and run 1 contains 6 polls over the 2 s ceiling including one of 7.931 s. This
artifact must be regenerated after the lane, not edited.

---

## 3. Domain Assessment

The domain work is the strongest part of this iteration, and I verified it rather than accepting it.

*Diagnosis before fix (spec-mandated).* The developer profiled rather than guessed and reported a result
that contradicted the plan's own leading hypothesis (`phase_context_by_date` per claim measured 0.61 s
isolated, "ruled out as the dominant driver"), then found the real driver — 2.5 M SQLModel row
instantiations from a full-entity `select(ScannerResult)` in `_factor_decile_observations`. That is the
right epistemic order, and the later audit-derived correction (the same call costs **23.6 s** in the live
serving context, 39× the isolated figure — Addendum 6) is itself an honest self-correction that made the
fix look *better*, not worse.

*Byte-identity.* I traced both changes rather than trusting the claim.
`_ExactMeanAcc.add_ratio`/`_GroupAcc.add_ratio`/`_accumulate_group_ratio` hoist a pure, deterministic
IEEE-754 decomposition out of an inner loop; `add(value)` is now a thin wrapper, so every existing caller
is unchanged, and the `None` gates are identical to the originals (no new exception surface — the
unconditional `overall_returns.add(realized)` already required `as_integer_ratio`).
`_extract_factor_value_from_row` (`research.py:186-198`) is `_extract_factor_value`'s body verbatim over a
pre-selected value, and both call sites still apply `float(value)` downstream, so DBAPI-vs-ORM typing
cannot diverge. `phases` is read-only inside `compute_drawdown_expectations` (`phases.get(date_iso)` /
`ctx["phase"]`, `forward_testing.py:2515-2517`) — never mutated — and `compute_drawdown_expectations_cached`
passes it only on a MISS. The `data_manager` precompute and the in-function fallback resolve the *same*
`market_phase.phase_context_by_date`, which is why the new tests' monkeypatches are valid.

*Live proof, independently recomputed by me from the committed raw evidence, not from the handoff:*

| | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| elapsed → terminal (bound 1,200 s) | 1,012.71 s | 1,048.22 s | 1,044.77 s |
| peak VmPeak (cap 8,192 MB) | 4,577,812 kB = 4.47 GB (45.4 % margin) | 4,243,444 kB (49.4 %) | 4,281,968 kB (49.0 %) |
| health polls / non-200 | 449 / **0** | 460 / **1** (10.014 s timeout) | 459 / **1** (10.013 s timeout) |
| polls over the 2 s ceiling | **6** | **8** | **9** |
| polls over 5 s | 2 (5.577 / 7.931 s) | 2 (9.724 / timeout) | 2 (5.174 / timeout) |

TC-1 ✓ (3/3, ~15.6-15.8 % margin), TC-5 ✓, TC-4 ✗. I also verified TC-2 end-to-end in `logs/backend.log`
for drill job `8961bfbde04b4bb682f3ca554e1d431e`: five per-horizon lines (37.39/33.56/23.06/24.06/19.82 s)
and seven per-claim lines whose sum, 765.67 s, plus the 23.6 s precompute gap equals the 789.27 s
whole-phase total exactly — the attribution the iteration was scoped to produce genuinely exists and is
arithmetically closed. TC-10 ✓: `git diff` over `config.yaml`, `host-guard.env`, `scripts/start-backend.sh`,
`scripts/dev.sh` is empty, and `config.yaml:1363-1364` still reads `memory_cap_mb: 8192` /
`malloc_arena_max: 2`. TC-6 is honestly still `xfail(strict=False)` with a reason that now names the real
residual and carries the audit correction — no assertion was loosened.

The one domain-level caution worth carrying forward: the margin is ~15 %, and it is a margin measured on
an *otherwise-idle host* (which is what TC-1 specifies). The same round's realistic-usage run blew through
it and died. `drawdown_expectations_warm` also costs 789-801 s live against 266.76 s measured in isolation
— a 3× gap the handoff attributes plausibly (cold page cache, uvicorn scheduling, the sampler threads) but
does not prove. The bound is real; it is not yet a reliability promise under concurrency, and the handoff
says so.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_data_manager.py:2070` | New `test_finalize_hook_sub_phase_timing_names_each_horizon_and_claim_and_memoizes_phase_context` — TC-2's missing regression guard (a sub-phase line per configured horizon; one per-claim line naming `factor:leadership_score:h20`, never a bare index; both pre-existing whole-phase lines still firing) plus the first assertion anywhere that `phase_context_by_date` is called **exactly once** per finalize invocation. |
| 2 | Important | `runs/goal-session-ops-hardening/journey-scripts/J-05.json` | Target date rotated `2012-01-05` → `2012-01-04` (5 occurrences) because this round's own lane consumed `2012-01-05`; spec-mandated rotation, logged here per the iter-46 lesson. |

**Post-fix verification (commands and results, all with the dispatch `TMPDIR` exported):**

- Fix 1, targeted: `.venv/bin/python -m pytest tests/test_data_manager.py -k "sub_phase_timing" -q -p no:randomly` → **1 passed in 0.68 s**.
- Fix 1, **mutation-proven** (this is what makes it evidence rather than decoration): a throwaway probe
  monkeypatched `forward_testing.compute_drawdown_expectations_cached` to swallow the threaded timeline —
  exactly what a refactor dropping `phases=_dd_phases` would do — and asserted the call count becomes 2.
  It **passed**, i.e. the new guard's `== 1` assertion genuinely flips under the mutation. The probe file
  was deleted immediately (`tests/` re-checked: no `test_zz_audit_mutation_probe.py` remains).
- Fix 1, in company and under random ordering: `pytest tests/test_data_manager.py -k "sub_phase_timing or
  phase_context_warm or column_projected_read"` → **4 passed in 0.85 s** (randomised order, no
  `-p no:randomly`).
- No regression in the suites this diff touches:
  `pytest tests/test_data_manager.py -k "sub_phase_timing or phase_context_warm or column_projected_read or drawdown" tests/test_ingest_finalize_fault_injection.py tests/test_evidence.py` → **17 passed in 2.92 s**;
  `pytest tests/test_evidence.py tests/test_research_streaming.py tests/test_forward_testing_aggregates_streaming.py -q -p no:randomly` → **141 passed in 23.08 s**.
- Fix 2: JSON re-parsed after the edit (`json.loads` gate in the edit itself); target date confirmed
  against the committed DB — `2012-01-04` has bars for 480 symbols and **0** `scanner_runs` rows.
- Scope-creep check on my own diff (`git diff --stat`): the only files I touched are
  `tests/test_data_manager.py` (+95 lines, one test) and `J-05.json`. **No product code was modified** —
  `data_manager.py`, `forward_testing.py` and `research.py` still carry mtime `2026-08-05 12:34:46`, so
  TC-7(a) remains satisfiable by the pending lane. Nothing in the dev handoff is invalidated by these
  fixes; T1's finding corrects a claim in the **QA** report, which Q1 already requires be re-run.

Not fixed, by deliberate decision: B1/B2 (out of scope, fifth concurring judgment, and a second risky
change on the same axis), B3/B4/B5 (product-code edits that would reset the mtime the pending lane needs),
T2/T3 (new scope / multi-hour job that would recreate B1's crash mechanism), Q1 and F1 (not an auditor's
artifacts to produce).

---

## 5. Recommended Next Step

**Do not send this back for another developer fix pass on this diff.** Every finding a developer could
close on it is closed, and touching product code again would reset the mtime and re-open TC-7(a) for a
fifth round. The next event must be the lane, and the ONLY thing standing between this iteration and a
scoreable verdict is:

1. **Run the full 8-journey lane, LAST, against the running backend** (UP and healthy on 8255, frontend on
   3255, no job stuck in `running`, no product code changed since 12:34:46 — all four verified in §2/F1).
   Deterministic replay where a golden exists (J-01, J-03, J-05, J-06, J-08, J-09), LLM browser-qa
   otherwise (J-04's backend half already has real executed rows in `tests/test_start_backend_script.py`
   — 2 passed, boot-to-first-200 in 1.29 s and a crash/restart `interrupted` read-back — which is the
   honest substitute for a lane structurally forbidden from restarting services). **J-05 now targets
   `2012-01-04`**; if a drill consumes it again, rotate again and log it.
2. **Expect J-07 to fail again** if the lane browses `/research/factor-lab` during the backfill. That is
   B1. It is real, it is unfixed by design, and reproducing it is *correct evidence*, not a lane defect.
3. **Re-run QA after the lane** (Q1) — the current QA report contradicts its own cited review, the browser
   results, and `status.json`, and must not be read as this iteration's verdict.

Then score. On the evidence available today the honest journey picture is: **J-05 advanced but not proven**
(TC-1's bound met 3/3 live; the browser half — job reaching terminal in-app and the snapshot rendering from
storage — never executed), **J-07 failing** (health ceiling breached 6-9×/run in 3/3 runs, and the service
demonstrably went down for 6+ minutes under ordinary concurrent usage), **J-01/J-03/J-06 passing but on
read-only history-panel evidence (TC-8 gap)**, **J-04 passing on integration rather than lane evidence**,
and **J-08/J-09 unproven this round**. The next iteration's primary scope is already unambiguous and
five-times concurred: B1 + B2 as ONE change on the concurrency/memory axis.
