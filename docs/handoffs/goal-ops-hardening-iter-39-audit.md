# goal-ops-hardening-iter-39 Audit Report

**Date:** 2026-07-31
**Auditor:** Hard audit pass — skeptical, evidence-based (post-fix-pass re-audit)

> This is the **second** audit of iter-39. The first returned **FAIL** (findings B1-B9); the
> developer ran a fix pass (B2/B3/B5/B6 fixed, B8 corrected, B1/B4 already fixed by that audit,
> B7/B9 carried), the reviewer re-passed, and QA re-passed. This report re-verifies the phase
> against the FINAL code state and re-numbers its own findings.

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal was achieved. J-07 step 4 — the single unrun item this full-depth pass was mandated
to close — is now proven in a **live server process**: the named per-horizon forward-aggregate
`except MemoryError` handler fired (its own distinctive log line, job-scoped), the abort was
isolated to that one loop (`aggregates_refreshed` honestly omits `forward_aggregates` while
`research_hot_keys` and `drawdown_expectations`, which run after it, completed), and the same
process served 68/68 health polls and 1,246/1,246 cached `/api/backtest` reads — one of which
literally brackets the abort instant — with zero non-200s and no restart. The replay-lane repair,
env-toggle guard, root-logger fix and `read_pool()` in-situ measurement are all real, tested, and
independently re-verified here. Four documented limitations remain (the trial-3 process wedge is
unretired and its cause unattributed, the AG-8 unbounded `_missing_data_diagnostic` scan is open,
the browser-level regression evidence predates the fix pass's own code, and the *merged* results
headline can still under-report a BLOCKED run) — none defeat the phase goal, none are new
regressions, and all are honestly disclosed by the developer rather than glossed over.

---

## 2. Findings

### Backend Findings

**B1 — GAP (documented): the trial-3 process wedge is unretired and its cause remains unattributed.**
`runs/goal-ops-hardening-iter-39/mem-drill/trial3-2650mb-wedge-evidence.txt:50` records an
**uncaught** `MemoryError` in a background thread followed by 7+ minutes of total `/api/health`
unresponsiveness in a process whose backfill job had already persisted `status: ok`. The fix pass's
B2 remediation (`data_manager.py:3182-3226`, `_compute_one_isolated`) closes a real gap in the
per-item isolation convention, but the developer's own Known Issues (fix pass, item 1) correctly
**retracts** the prior audit's attribution of the wedge to a `backfill_workers` thread: by the time
trial 3's `MemoryError` fired inside `refresh_coverage_snapshot` → `_missing_data_diagnostic`, the
`with ThreadPoolExecutor` in `_do_backfill` (`data_manager.py:3245`) had already joined every
worker, so no backfill worker thread existed. That retraction is correct on the code — I re-read
the block — and the honest consequence is that a live counterexample to J-07's own headline claim
("heavy aggregates never take the service down") is still standing under an artificially tightened
cap. It is NOT reachable at the committed `memory_cap_mb: 6144` (`config.yaml:1363`, unchanged),
which is why this is a GAP and not a blocker: no failure is demonstrated in shipped configuration.
**No fix applied** — reproducing it requires re-inducing genuine host memory exhaustion, which is
the host-hazardous, wrong-direction action this iteration deliberately abandoned (AG-10).
This should gate any GOAL_ACHIEVED disposition that leans on J-07's broad wording.

**B2 — GAP (documented, out of scope): unbounded whole-table materialization on the ingest path.**
`_missing_data_diagnostic` (`apps/backend/app/engine/data_manager.py:271`) iterates
`select(DailyPrice.symbol, DailyPrice.date)` across the universe and SQLAlchemy buffers the entire
result before the loop body sees a row (~3.3 M rows; the traceback in
`mem-drill/trial3-2650mb-wedge-evidence.txt:17-29` shows `loading.py:220 chunks` →
`result.py:580 _raw_all_rows`). This is an AG-8-class "unbounded whole-table ORM materialization",
and it is the mechanical reason TC-1's live cap window was unreachable at all. Correctly **not**
fixed here: the phase spec's OUT OF SCOPE explicitly defers the sibling item (iter-29/d) under
rule 5, and a bounded `yield_per` change is a second structural change alongside the drill. Both
the developer (Known Issues fix pass, item 2) and the reviewer flagged it. Highest-value candidate
for the next iteration.

**B3 — GAP: the merged results artifact can render `PASS` for a run whose journeys were all BLOCKED-adjacent.**
`merge_ui_test_results.parse_rows` (`incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py:78,87`)
recognizes only `PASS`/`FAIL`/`SKIP`/`SKIPPED`, so a `BLOCKED` row parses with `verdict=""`.
`merge()` (lines 156-167) then counts it in `total` but in neither `n_pass` nor `n_skip`, and
`compute_overall` (line 122) drops it entirely — so in the mixed case (one journey PASSed via the
LLM lane, every regression journey BLOCKED) the authoritative merged file the goal-evaluator reads
carries `**Browser QA Verdict:** PASS`. I reproduced the all-BLOCKED case end to end: the merged
headline read `SKIPPED` with `Overall: 0/3 journeys passed (0 skipped)` — the blocked count is
invisible in the summary line either way.
**Why this is a GAP and not IMPORTANT** (I weighed both): the row-level truth survives verbatim —
`merge()` writes `r["raw"]` unmodified, so every `| BLOCKED |` cell reaches the merged file — and
the auditor's B2 fix to `goal_gate.py` (`_BLOCKED_CELL_RE`, lines 80 and 150) makes the
deterministic achievement gate return **1** on any such cell. I verified that end to end on my own
merged artifact (`goal_gate.py results <merged> → rc 1`). The DoD's own clause is about the replay
lane's artifact, which correctly reads `**Browser QA Verdict:** BLOCKED`. So the machine gate is
genuinely closed; the residual is an LLM-readable honesty gap in a secondary artifact.
**No fix applied** — teaching `parse_rows` a BLOCKED class is a framework-wide verdict-vocabulary
change, well beyond this iteration's scope.

**B4 — OBSERVATION: the memory-pressure latch is job-wide, across all date windows.**
`memory_pressure` (`data_manager.py:3180`) is created once per `_do_backfill` call, outside the
`for ws, we in windows` loop (line 3273), so the first `MemoryError` on any date short-circuits
every remaining date in **every** remaining window, each recorded as an `error_other` failure. This
is the deliberate iter-8 convention applied consistently, it is honestly reported (the accounting
invariant `snapshots_created + already_snapshotted + error_other == dates_total` still holds
exactly, asserted by the new tests), and continuing to allocate under pressure is the confirmed
worse outcome. Worth recording only because on a long J-03 unbounded backfill one transient
`MemoryError` now costs the whole remaining range where each date was previously attempted
independently. Deliberate and documented in the code — no action.

**B5 — OBSERVATION: the root INFO handler widens what lands in `logs/backend.log`.**
`configure_app_logging()` (`apps/backend/app/logging_config.py:56-78`) attaches a root
`StreamHandler` at INFO, so every third-party library's INFO records now reach the log too. Live
check of the post-fix log region shows only `trendora.*` loggers in practice (uvicorn carries its
own handlers and is filtered out by `_already_handled_by_own_logger`), and a grep of every
`logger.info`/`logger.debug` call under `apps/backend/app` for key/token/secret/password/url
material returned exactly one benign line (`warmup.py:147`). No secret-exposure risk. The B4
duplicate-write fix is confirmed working live: the last doubled `backtest_timing` pair is at
`logs/backend.log:146433-146490` (pre-fix); every post-fix launch writes the single bare copy only
(e.g. `logs/backend.log:149326`).

### Frontend Findings

None. `Frontend Present: no`; `git diff --stat` confirms zero frontend files touched. J-04/J-05
verification read existing rendered panels via their own data source (`GET /api/data`) unchanged.

### Test Findings

**T1 — GAP: the browser-level regression evidence predates the fix pass's own code.**
The 7-journey deterministic replay that satisfies DoD item 2
(`reports/phase-goal-ops-hardening-iter-39-regression-replay-results.md`, 7/7 PASS against a live
stack at `http://localhost:3255`) has mtime **2026-07-30 23:31:56**. The fix pass's edits to
`apps/backend/app/engine/data_manager.py` (mtime **2026-07-31 00:05:31**) and
`incredible_auto_dev/scripts/automation/lib/replay-lane.sh` (**00:03:25**) landed afterward. So
J-01/J-03/J-04/J-05/J-06/J-08/J-09 were replayed against a code state that no longer exists, and
`_compute_one_isolated` sits directly in the backfill hot path those journeys exercise.
**Why this is a GAP and not IMPORTANT:** I traced the delta and it is inert on every non-
`MemoryError` path — the serial arm's old `except Exception as exc: compute_error = str(exc)` and
the parallel arm's old drain-loop `except Exception as exc: pending[d] = (None, 0.0, str(exc))`
both now resolve to the wrapper's own `except Exception as exc: return d, None, 0.0, str(exc)`
(`data_manager.py:3225-3226`), producing the identical error string; the only added per-call work
is one `os.environ.get` and one `Event.is_set()`. And `tests/test_data_manager_backfill_parallel.py`
re-ran green after the change (12/12, my own run below). No regression is demonstrated — only that
the UI-level evidence is one code state stale.

**T2 — OBSERVATION: the full backend suite was not run, by standing project constraint.**
This project's memory notes record the full pytest suite as a ~10-11 h run that must not be invoked
from the pipeline roles. Targeted suites were re-run independently in this audit (below) rather
than accepted on the handoff's word.

**Test quality assessment — strong.** The new tests are tight, not loose: every fault-injection
test carries its own control arm so a silently-disabled injector fails rather than passes green
(`test_ingest_finalize_fault_injection.py:136-153`); assertions pin the *specific* stage's
distinctive log line and explicitly assert the OTHER stage's line is absent (lines 182-188), so a
test cannot pass on the wrong stage aborting; isolation is proven positively via a later-category
call spy (lines 130-133); and the backfill tests assert exact counts and the exact accounting
invariant, plus that recorded errors carry the *wrapper's* wording — a raw injected-exception
string would prove the `MemoryError` escaped the thread boundary
(`test_data_manager_backfill_parallel.py:353-362`). `goal_gate.py`'s new self-test includes a
false-positive guard proving `BLOCKED` matches a whole cell only, not prose. The developer also ran
and reverted negative controls (neutering each handler fails exactly the tests that claim it); the
reviewer independently reproduced those.

---

## 3. Domain Assessment

**J-07 step 4 (the mandated item) — genuinely closed.** The substitution of a test hook for further
cap-tuning is not a shortcut: `docs/goal.md` J-07 step 4 sanctions it verbatim ("Induce memory
pressure during a warm (test hook or a tightened cap in a throwaway process)", `docs/goal.md:277`),
and after three live trials failed for a now-understood mechanical reason (B2 above), a fourth
cap probe would have been the wrong-direction pattern. The injector itself is sound domain
hygiene: `_fault_inject_memory_error` (`data_manager.py:2924-2938`) is gated on an env var read at
call time, restricted to a `frozenset` of three known site names so a typo injects nothing rather
than producing a clean run that reads like "the handler was never needed", and deliberately **not**
a `config.yaml` key — a fault injector must not be reachable through the product's own
configuration. I confirmed no committed script, config, or `.env` arms it anywhere in the repo.
Both injection points sit *inside* the pre-existing `try:` blocks whose `except MemoryError`
handlers J-07's acceptance names (`data_manager.py:3550` and `:3642`), which is the only placement
that actually exercises them.

**The live proof is the load-bearing part, and it holds.** `fault-drill/abort-log-excerpt.txt`
shows the liveness line for job `c67a6b0a…` at `00:10:52,524` and the forward-aggregate handler's
own line at `00:11:16,666` — job-scoped, and distinctive enough that prefill's or
`refresh_coverage_snapshot`'s generic handler could not have produced it.
`fault-drill/final-job-status.json` then proves isolation from the *outside*: `status: ok`, all
dates done, and `aggregates_refreshed` omitting `forward_aggregates` while including two categories
that run after it. That is the per-item isolation contract observed end to end in a server, not a
unit test.

**Containment evidence is literal, not prose.** `tc3-containment.json` records a single
`/api/backtest?as_of=2026-06-24` request whose interval (`…16.566Z` → `…17.118Z`) contains the
abort epoch (`…16.666Z`) and returned HTTP 200 with a 105,190-byte cached payload; 1,246 requests
total, 0 non-200, 500 of them after the abort. The health poll is genuinely unbounded now — 68
polls start-to-terminal, 0 non-200, max inter-poll gap 2.298 s, safety backstop never fired — which
closes the prior `MAX_SECONDS` blind spot. The developer kept the first 1 Hz run
(`fault-drill/run1-1hz/`) that missed containment by 74 ms rather than deleting it; that is the
honesty standard this project asks for.

**The replay-lane repair does what it claims.** I exercised it against a dead backend myself rather
than trusting the report: `demo_runner.py --mode verify` with an unreachable health URL returned
**rc 7**, wrote `**Browser QA Verdict:** BLOCKED` with three `| BLOCKED |` rows and zero `FAIL`
rows, and `goal_gate.py results` on the merged artifact returned **1**. `replay-lane.sh` routes
rc 7 to the LLM lane with its own distinct log line, so "backend down" can no longer read as "a
selector broke" (rc 5) or "the browser crashed" (rc 6). The reconciliation-footer fix is the right
shape twice over: the overturn *detection* now delegates to `merge_ui_test_results`' own tested
annotation-tolerant parser instead of a raw `grep -F '| PASS |'` (which is exactly how iter-38
omitted J-05 and J-04), and the footer *wording* is now derived per journey, so a flip to SKIP
reads "NOT re-verified — superseded, not disproven" instead of claiming a live re-confirmation.
The bash suite pins both directions, including a negative assertion that the "false positive"
phrasing is absent on the SKIP path.

**Anti-goals respected.** AG-10: `git diff -- scripts/ project-extensions/` is empty, both
HOST-GUARD markers are intact in `scripts/start-backend.sh` and `scripts/dev.sh`, and the drill ran
at the **committed** `memory_cap_mb: 6144` — the safest possible reading of the constraint, since
the fault-injection approach induces no real memory pressure at all. AG-9: `provider: seed`,
throwaway DB under `runs/`, no network. AG-3: every claimed number in the drill account traces to a
raw artifact I re-read; the one number that does not tell the whole story (`dates_done: 2` vs 18 in
memory) is disclosed inline at every mention rather than quietly presented as progress.

**Honesty of the handoff.** The developer overshot the prior audit's "take exactly one of the two
paths" advice by taking both — but the justification is correct on the merits (choosing fault
injection as the vehicle collapses them into one mechanism, and fixing only one could not produce a
defensible J-07 disposition), the total product-code delta is one env-gated injector plus one
`try/except`, and the reviewer independently reached the same conclusion. More notably, the fix
pass **retracted an attribution the audit itself had made** (the wedge → `backfill_workers`) rather
than accepting a convenient story that would have let B2 read as "wedge fixed". That is the
behavior the rubric asks for, and it is why the residual gaps here are trustworthy as stated.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT finding survived verification. Every finding above is a GAP or
OBSERVATION, and fixing those is scope creep per the auditor rules.

### Verification re-run independently in this audit (not accepted on the handoff's word)

| Command | Result |
|---|---|
| `pytest tests/test_ingest_finalize_fault_injection.py tests/test_logging_config.py -q` | **8 passed** (0.70 s) |
| `pytest tests/test_data_manager_backfill_parallel.py -q` (full file, not just the 2 new tests) | **12 passed** (298 s) |
| `demo_runner.py self-test` | **26 passed, 0 failed** |
| `merge_ui_test_results.py self-test` | **12 passed, 0 failed** |
| `goal_gate.py self-test` | **self-test passed** |
| `bash incredible_auto_dev/tests/automation/test-replay-lane.sh` | **65 passed, 0 failed** |
| Live rc-7 probe: `demo_runner.py --mode verify --backend-health-url http://127.0.0.1:1/api/health` | **rc 7**; 3 `\| BLOCKED \|` rows, 0 `FAIL`; merged → `goal_gate results` **rc 1** |
| TC-12 live: `grep "INFO trendora.data_manager: J-07 finalize-tail" logs/backend.log` | present (`:146563`, `:147787`) — `.info` reaches the logfile |
| B4 duplicate-suppression live: post-fix `backtest_timing` lines | single bare copy only (`:149326`); doubled pair only in the pre-fix region (`:146433-146490`) |

TC-10/TC-11 (env-toggle, 2/2, ~95 s) accepted on the reviewer's re-run (review report `issues:` list
carries no spec-category entry) plus the QA row (`reports/qa/goal-ops-hardening-iter-39-qa.md`,
"Environment Toggle (TC-10/TC-11) … PASS 2/2"); the guard itself was read directly at
`data_manager.py:3166-3169`.

### DEFINITION OF DONE

| # | Item | Verdict | Basis |
|---|---|---|---|
| 1 | J-07 drill aborts in the aggregate-warm stage; health + cached backtest 200 during/after; poll covers whole job | **MET** | Full trace — `abort-log-excerpt.txt`, `final-job-status.json`, `health-monitor.csv` (68/68), `tc3-containment.json` (literal containment), injector + call sites read at `data_manager.py:2924-2938, 3550, 3642` |
| 2 | Required journeys green; J-04/J-05 via genuine live kill/restart | **MET (see T1)** | Full trace — replay artifact 7/7 PASS at `:3255`; `live-restart/` raw JSON re-read for TC-8 (`interrupted`, `dates_done: 2`, non-zero) and TC-9 (`coverage_status: "stale"`, `snapshot_count: 1902`) |
| 3 | No anti-goal violation (AG-8/9/10) | **MET** | Full trace (risk class) — `git diff -- scripts/` empty, HOST-GUARD markers present, `config.yaml:1363` = 6144 unchanged, `provider: seed`, throwaway DB, injector unarmed repo-wide |
| 4 | Unit tests pass; no regressions | **MET (see T2)** | Re-run independently — table above |
| 5 | Replay lane reports BLOCKED not FAIL; footer lists every overturned journey | **MET** | Full trace (gate correctness) — own live rc-7 run + `goal_gate` rc 1 + footer code read (`replay-lane.sh:461-511`) + TC-7 bash assertions for both annotated flips |
| 6 | Dev handoff written | **MET** | `docs/handoffs/goal-ops-hardening-iter-39-dev.md` present, with the B8 correction marked in place |

---

## 5. Recommended Next Step

**Proceed.** The iteration's mandated item is closed with this-iteration, live-server evidence, and
the bundled mechanical fixes are all real and tested. Two things for the evaluator to weigh before
any GOAL_ACHIEVED disposition on J-07 specifically:

1. **B1 — the trial-3 wedge is open and unattributed.** J-07's headline claim is broader than its
   four acceptance steps, and a 7+ minute unresponsive window exists on record under a tightened
   cap. It is not reachable at the shipped `memory_cap_mb: 6144`, so it does not block this
   iteration — but it should not be quietly retired by the B2 fix either, and the developer
   explicitly declined to claim it was.
2. **B2 — `_missing_data_diagnostic`'s unbounded whole-table materialization
   (`data_manager.py:271`)** is the single highest-value next target: it is an AG-8-class violation
   on the ingest path, it is the mechanical cause of the cap window that consumed two iterations,
   and a bounded `yield_per` fetch would be output-identical since the grouping loop is unchanged.
   It now has a clean, uncontested lane (rule 5's one-risky-change budget is free next iteration).

Lower priority: re-run the 7-journey deterministic replay once against the final code state to
retire T1, and consider teaching `merge_ui_test_results.parse_rows` the `BLOCKED` class so the
merged headline stops under-reporting it (B3) — the achievement gate already blocks correctly, so
this is a reporting-honesty cleanup, not a safety fix. The two owner decisions (iter-34/j health
budget, iter-33/i `start-frontend.sh` host-guard membership) remain open and un-actionable by any
agent path, as three prior evaluators have noted.
