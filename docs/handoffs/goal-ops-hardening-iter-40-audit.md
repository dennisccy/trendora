# goal-ops-hardening-iter-40 Audit Report

**Date:** 2026-07-31
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's one risky change is real, not cosmetic: I independently measured that
`.yield_per()` on this codebase's `session.exec(...)` genuinely bounds materialization
(**+4.6 MB RSS and 14–26 ms to first row, versus +349 MB and 1,372 ms without it, on a
1,000,000-row `daily_prices` table**), and `research.read_batch_size` is 2,000 — a truly small
batch, not a nominal one. Output byte-identity is structurally guaranteed, not merely
asserted. The checkpoint-honesty fix, the `perf-budgets.md` retraction, and the
`merge_ui_test_results.py` `BLOCKED` class all hold up under trace. Two gaps remain: the
TC-4 cadence test could not detect a revert of the very constant it guards (**found and
fixed during this audit, verified in both directions**), and DoD item 8 / TC-9 — the
required-still-passing journeys' deterministic replay — **was never executed**: all seven
journeys are recorded `SKIP`, and no replay artifact exists for this iteration.

---

## 2. Findings

### Backend Findings

**B1 — GAP (disclosed, not fixed): a process wedge at 2,650 MB is still reachable post-fix, and
its dying thread is still unidentified.**
`runs/goal-ops-hardening-iter-40/wedge-drill/README.md:11-26` — the drill's run 1 wedged at the
same cap the fix targets (all 14 threads in `futex_do_wait`, `VmPeak` pinned at 2,713,600 kB,
uncaught `"Exception ignored in thread ... MemoryError:"` with no traceback), and the thread was
**not** positively identified: `gdb` attach was refused by this host's `kernel.yama.ptrace_scope`
policy and no `py-spy` is installed. The dev's reading — that run 1 tested a *different*
condition (boot warmup racing the triggered job for the same ceiling), so TC-3's branch (b)
"identify the dying thread" was not actually triggered — is defensible, disclosed in three places
(`README.md`, `run1-notes.md`, `reports/perf-budgets.md`'s new Iteration 40 section), and was
endorsed by the reviewer. I record it as a GAP rather than IMPORTANT because the unmet part
requires an owner-level host-policy change or a new dev dependency, both outside an agent's
authority, and because it does not occur at the committed `memory_cap_mb: 6144`. **I was unsure
between GAP and IMPORTANT**: an uncaught background-thread `MemoryError` that hangs the whole
process is precisely what J-07 forbids, and this iteration closes with that hazard open,
unreproduced and undiagnosed.

**B2 — GAP: the "wedge did not recur" claim is strongly evidenced *during* the job and thinly
evidenced *after* it — which is the window the previous wedge actually used.**
`runs/goal-ops-hardening-iter-40/wedge-drill/monitor.py:96-99` breaks its poll loop the moment
`job_status in ("ok","partial","failed")`. iter-39's trial-3 wedge, by that ledger's own words
(`reports/perf-budgets.md:4996`), appeared **"shortly after the job's own DB row was written
`ok`"**. Run 2's 28 clean polls therefore all land *before* the window that previously failed.
The post-completion evidence is exactly one probe: I verified it exists in the live log
(`logs/backend.log:149730-149731`, a job poll and a `GET /api/health` both `200`) — the README's
"confirmed by a follow-up `GET /api/health`" is true and not overstated, but it is one probe, and
no clean-shutdown line follows for that process. TC-3(a) asks for coverage "for the drill's full
duration"; a reasonable reading of "duration" includes the post-terminal tail. Recommendation for
the next such drill: keep polling for a fixed interval past terminal status rather than stopping
on it. Not fixed here — re-running the drill is out of audit scope and the spec forbids a second
trial this iteration.

**B3 — OBSERVATION (verified clean, recorded so it is not re-litigated): the streaming change is
genuinely bounded and genuinely output-neutral.** Independently confirmed, not taken from the
handoff:
- Materialization is real. Measured on a 1,000,000-row table using this repo's own
  `DailyPrice` model, SQLAlchemy 2.0.51 / SQLModel 0.0.22, RSS sampled at the delivery of row 1:
  `yield_per` +4,608 kB / 26.0 ms and +4,860 kB / 14.1 ms across two runs, versus whole-result
  +348,860 kB / 1,371.8 ms. Extrapolated to the ~3.3 M-row deep basis that is ~1.1 GB avoided —
  consistent with iter-39's wedge account.
- The batch knob is small: `config.yaml:891` `read_batch_size: 2000`, so a batch is negligible.
- Byte-identity is structural, not incidental: the output lists are built by iterating
  `sorted(universe_set)` (`data_manager.py:295`) and testing membership in a `set`
  (`data_manager.py:327-330`), so neither row order nor fetch strategy can reach the output.
- The corrected comment (`data_manager.py:262-283`) now states scope-vs-materialization plainly
  and cites the evidence file — DoD item 1's second clause satisfied.
- No write occurs on the streaming session inside the loop, so the longer-held read cursor
  introduces no new lock exposure.

**B4 — OBSERVATION: the checkpoint cadence change is correctly placed and correctly bounded.**
`_checkpoint_run_record` is invoked only from `data_manager.py:3049` (pre-loop plan write) and
`:3134` (inside `_persist_isolated`), both on the orchestrating thread — the parallel arm fans out
only compute and drains persists on the main thread (`:3268-3284`), so the 10× denser cadence adds
no cross-thread contention on `prog._last_checkpoint_monotonic`. Note the execution plan's cited
call sites (`3237`/`3268`) were stale line numbers; the actual sites are as above and the plan's
substantive claim ("the call site is not the gap; the 10 s throttle is") is correct. I also
reconstructed the live drill arithmetic from
`runs/goal-ops-hardening-iter-40/checkpoint-drill/trigger-poll-kill.csv`: at the observed ~264 ms/date
the 1.0 s throttle writes at t≈24.03 (`dates_done=2`), t≈25.12 (`6`), t≈26.33 (`11`), and the kill
lands at t=26.59 with M=12 — the persisted `11` in `post-restart-persisted-row.txt` is exactly what
the mechanism predicts. The reported 1-date gap is a favorable sample of a mechanism whose true
bound at that rate is ~4 dates (still within one 1.0 s interval); the dev handoff's Known Issue #2
already discloses the time-based nature of the bound.

### Frontend Findings

None — no frontend file changed and none was required (spec: "Frontend: None").

### Test Findings

**T1 — IMPORTANT (fixed): the TC-4 cadence test derived its entire tolerance from the production
constant, so it passed unchanged at the pre-iter-40 value it exists to guard.**
`apps/backend/tests/test_data_manager.py:4492` read
`interval = data_manager._RUN_RECORD_CHECKPOINT_INTERVAL_S` and then computed
`allowed_staleness = ceil(interval/dt)` from it (`:4521`), so both density assertions hold for *any*
interval; the throttle assertion `0 < write_count < n_dates` (`:4530`) is likewise satisfied by a
single write. **Verified, not inferred:** with the constant monkeypatched back to `10.0` the test
reported `1 passed` — the exact iter-39/w honesty defect this iteration exists to close would have
regressed silently, with the live `kill -9` drill (a one-off, not repeatable in CI) as the only
evidence. Fixed — see section 4.

**T2 — IMPORTANT (gap, not fixable in audit scope): DoD item 8 / TC-9 was never executed — the
seven required-still-passing journeys were not replayed, and nothing in the pipeline surfaced
that as a gap.**
`reports/phase-goal-ops-hardening-iter-40-ui-test-results.md` records `**Browser QA Verdict:**
SKIPPED`, `0/8 tests passed (8 skipped)`, and a `SKIP` row for every one of UT-J-01, UT-J-03,
UT-J-04, UT-J-05, UT-J-06, UT-J-08, UT-J-09, each reading *"Not executed — dispatch instructions
state frontend is not available."* The deterministic replay lane did not run either: no
iter-40 replay artifact exists and every golden script in
`runs/goal-session-ops-hardening/journey-scripts/` is dated 2026-07-30 or earlier (that file's own
"Golden replay scripts" section confirms none was written). The spec is explicit and this is not a
technicality — DoD item 8 requires "Required-still-passing journeys ... remain green via
deterministic replay + LLM fallback", TESTING REQUIREMENTS names "standard replay/spot-check" for
all seven, and TC-9 spells out the assertion. The mechanism is an escape hatch worth naming: the
metadata `Frontend Present: no` (correct — no frontend code changed) propagated into the browser-QA
dispatch as "frontend is NOT available ... Do NOT attempt to run browser tests", which silently
waived the *regression* verification the same spec demanded. The QA report's PASS
(`reports/qa/goal-ops-hardening-iter-40-qa.md:205-209`) treats this as "Browser checks: SKIPPED — no
frontend present" and does not disclose that a DoD checkbox went unverified. Not fixed here:
executing seven live journey replays means bringing up both services plus Chrome MCP — the browser-QA
lane's work, not a surgical audit fix. **The evaluator must not score J-01, J-03, J-04, J-05, J-06,
J-08 or J-09 as re-verified by this iteration's evidence.** Mitigation on record: the change is
backend-only with no serving-shape change, and 142 + 26 backend tests pass.

**T3 — OBSERVATION: `BLOCKED` is now emittable as a headline token that the framework's own
verdict vocabulary does not declare.** `merge_ui_test_results.py:187` can now write
`**Browser QA Verdict:** BLOCKED`, but `verdicts.py::BrowserQAVerdict` declares only
`PASS`/`FAIL`/`SKIPPED`, and `goal-iter-lean.sh`'s four extraction sites (`:484`, `:531`, `:890`,
`:1221`) all pipe through `grep -oE 'PASS|FAIL|SKIPPED'`, yielding an empty value for a `BLOCKED`
headline. I traced this to a non-issue behaviorally: every one of those sites gates on
`== "PASS" || == "FAIL"`, so `BLOCKED` and the pre-fix `SKIPPED` fall through identically (the
browser-QA checkpoint is simply not marked done — fail-safe, not fail-open), and the hard gate
`goal_gate.py:_BLOCKED_CELL_RE` matches row cells, not the headline, so achievement blocking is
unaffected. `lint_contracts.py lint` still reports `OK (20 agents, 23 templates)`. Worth one
follow-up line so the vocabulary stops disagreeing across two files.

### Spec / Evidence-Hygiene Verifications (all clean)

- **TC-5 complete.** I enumerated every `backfill_workers` mention in `reports/perf-budgets.md`
  (lines 4996, 5018, 5022, 5186, 5207, 5304, 5306). The two that asserted causation now carry
  inline `[RETRACTED …]` notes at the point of assertion; the rest are the Audit B2 hardening
  description and the already-qualified "most plausibly". No unqualified sentence still names it.
- **iter-34 lesson honored (verified, not trusted).** `sed -n '149620,149729p' logs/backend.log`
  diffs **identical** to `run2-live-log-lines-149620-149729.txt`. The traceback names
  `data_manager.py:898 _compute_coverage_body` and is caught by the existing non-fatal handler;
  `_raw_all_rows`, `_missing_data_diagnostic` and `:271` appear nowhere in it — TC-2's literal
  assertion holds.
- **AG-10 respected.** Every drill launch banner in the live log carries the host-guard block
  (`memory_cap_mb=2650|6144 malloc_arena_max=2`, `host-guard: cpu_list=0-15 blas_threads=8`);
  `scripts/` is untouched by this diff, so `HOST_GUARD_REQUIRE_MARKERS=1` stays satisfied.
- **AG-9 / secrets clean.** Both `config.scratch.yaml` files contain only env-var *names*
  (`TIINGO_API_KEY` etc.), never values; `git check-ignore` confirms `drill.db`, `drill.db-wal`,
  `drill.db-shm` and `__pycache__` are all ignored, so the 1.2 GB of drill databases cannot be
  committed.
- **Re-verified live:** `merge_ui_test_results.py self-test` → 14 passed, 0 failed.

---

## 3. Domain Assessment

The domain reasoning is sound and, unusually, the hard part was reasoned about correctly rather
than patched around. The distinction the iteration turns on — *a query bounded in SCOPE by a
`WHERE ... IN (...)` clause is not bounded in MEMORY* — is genuinely true of SQLAlchemy's ORM
result path, is now stated correctly in the code where a future reader will hit it, and the fix
reuses the exact idiom (`prices.py:132-141`) and the exact config knob the rest of the codebase
already uses for this pattern rather than inventing a parallel mechanism. The choice to change
*only* the fetch strategy, leaving the grouping and every consumer untouched, is what makes the
byte-identity claim checkable rather than a matter of faith — and it checks out structurally
(sorted-universe iteration + set membership), which is stronger than the test alone.

The checkpoint fix is correctly diagnosed: the call sites were already per-date, and the defect
was purely that a 10 s throttle swallowed every call in a job shorter than 10 s. Tightening the
value while leaving the mechanism, the `message` field and the serializer alone is the minimum
change, and pinning it to the `/data` job card's own poll cadence gives it a principled rather
than arbitrary value.

The honesty discipline is the strongest part of this iteration. A confounded first drill run that
would have been easy to delete is retained, labelled, and explained in three places; the
non-recurrence is recorded as "signal, not certainty" with the reasoning for why certainty is not
available; the `MemoryError` that *did* fire is reported at its real site rather than folded into
the success story; and `coverage`'s honest absence from `aggregates_refreshed` is called out. That
is the standard AG-3 asks for. The one place the discipline does not reach is verification
*coverage* rather than verification *honesty*: T2's seven unreplayed journeys and T1's
self-satisfying tolerance both let an unverified thing read as verified, and neither the review
nor the QA pass caught either.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_data_manager.py` | In `test_checkpoint_cadence_density_and_throttle_control`, added a regression pin asserting `_RUN_RECORD_CHECKPOINT_INTERVAL_S <= cfg.data_manager.job_progress.poll_interval_seconds` — bounding the constant to the config knob its own in-code rationale cites (no magic number), so a revert to the pre-iter-40 10.0 now fails the test instead of passing it. |

**Post-fix verification (both directions, as required):**
- `pytest tests/test_data_manager.py -k "checkpoint_cadence_density"` at the production value →
  **1 passed** (0.61 s).
- Same test with `_RUN_RECORD_CHECKPOINT_INTERVAL_S` monkeypatched to the pre-iter-40 `10.0` via a
  scratch pytest plugin → **1 failed** at `tests/test_data_manager.py:4502`. Before the fix, the
  identical arm reported **1 passed** — that contrast is the finding and the proof of the fix.
- Full affected subset `pytest tests/test_data_manager.py -k "cadence or diagnostic"` →
  **9 passed** (94.70 s), unchanged from the dev/QA runs.
- `git diff` on my touched file contains only the added assertion block and its comment; nothing
  else. No dev-handoff claim was invalidated by this fix (it strengthens the test rather than
  contradicting anything the handoff states).

---

## 5. Recommended Next Step

Proceed to the evaluator, with two conditions carried forward explicitly.

1. **Do not treat J-01, J-03, J-04, J-05, J-06, J-08, J-09 as re-verified this iteration** (T2).
   Their `passing` status is inherited from prior iterations, not re-established here. Before any
   GOAL_ACHIEVED attempt, the deterministic replay lane must actually run against this build — and
   the underlying pipeline behavior deserves a framework item: `Frontend Present: no` should
   suppress *new-surface* UI tests, never the required-still-passing regression replay, and a
   browser-QA run in which every regression row is `SKIP` should be visible as an unmet DoD item
   rather than a clean `SKIPPED`.
2. **J-07's re-score should reflect what the drill can and cannot carry.** The
   no-unbounded-materialization clause is now genuinely closed and independently measured (B3).
   The service-availability clause is supported by 28 clean in-job polls but by a single probe in
   the post-completion window where iter-39's wedge actually appeared (B2), and a wedge remains
   reachable and undiagnosed at the drill cap (B1). Score the first clause on this iteration's
   evidence; treat the wedge as the open hazard the ledger already calls it.

The two long-standing owner decisions (iter-34/j's `/api/health` ≤0.1 s budget disposition,
iter-33/i's `start-frontend.sh` host-guard membership) remain unresolved and still gate any
GOAL_ACHIEVED attempt, as four prior evaluators have said.
