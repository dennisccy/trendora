# Iteration 8 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

iter-8's backend fix for J-05's regression is real, correctly scoped, and independently audited: all four
ingest-finalize warm loops now catch `MemoryError` distinctly and back off instead of hammering the next
allocation, the audit found and fixed a serious test-integrity defect on top of it, and the literal DoD
test command now reports 134 passed / 1 skipped / 0 failures. **But the iteration verified nothing** — the
browser-qa lane was skipped outright on a "Frontend Present: no" rule, so J-05's spec-mandated four-step
re-verification never happened and the J-01/J-03/J-04 replay lane never ran. There is no
`reports/qa/goal-ops-hardening-iter-8-evidence/` directory, no raw `.llm.md`, and
`status.json` records `browser_checks_run: false`. Audit (V1/V2) and closure (CLOSURE-FAIL) independently
reached the same conclusion, and the audit states explicitly: *"The evaluator must not flip J-05
`regressed → passing` on this handoff alone."* I did not.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | **unknown** (evidence gap) | No lane ran. `reports/phase-goal-ops-hardening-iter-8-ui-test-results.md` = "SKIPPED"; `runs/goal-ops-hardening-iter-8/status.json` `browser_checks_run: false`; no `...-iter-8-regression-replay-results.md` (iter-7 has one); QA TC-09 "INDIRECT — Not directly executed"; audit V2; closure Blocking Issue 2. Last real evidence: `reports/qa/goal-ops-hardening-iter-7-evidence/J-01-verify.png` (spot-checked — healthy, but iter-7 build). |
| J-03 | passing | **unknown** (evidence gap) | Same missing lane (QA TC-09 INDIRECT, audit V2). Range-cap logic confirmed untouched by the diff (audit §3), but a long-span backfill still runs the modified finalize hook. Last evidence: `reports/qa/goal-ops-hardening-iter-7-evidence/J-03-verify.png`. |
| J-04 | passing | **unknown** (evidence gap) | TC-10 LLM acceptance never executed (QA line 96 "INDIRECT", audit V2). `health.py` / `readiness.py` / `main.py` confirmed untouched (audit §3, coherence.md Data Contract table) — no visible regression mechanism, but no fresh evidence. Last evidence: `reports/qa/goal-ops-hardening-iter-7-evidence/J-04-initializing-badge.png`. |
| J-05 | regressed | **regressed** (carried over, NOT re-verified) | Fix verified in tree: `apps/backend/app/engine/data_manager.py:3049, 3143, 3186, 3245` (four `except MemoryError` branches) + audit B1 fix at `:3067-3068`; 10 injected-`MemoryError` tests pass with a negative control. Live step-4 run: `reports/perf-budgets.md` iter-8 section — 468/468 health polls 200, 0 timeouts, VmPeak 3,465.6 MB (43.6% margin under 6,144 MB), thermals independently corroborated by the audit against `logs/hwmon/hwmon.csv`. **No browser-qa, no screenshot, steps 1–3 unverified** (audit V1, closure Blocking Issue 1). |
| J-06 | partial | **partial** (unchanged, out of scope) | iter-8 spec targets J-05 only; the on-load `/api/backtest` `MemoryError` was deliberately not bundled (rule 6) and is carried in the dev handoff's Known Issues per DoD item 9. |

**No journey moved `passing` → `failing` this iteration.** Three moved `passing` → `unknown`, which is a
missing-evidence gap, not an observed failure. J-05's `regressed` is iter-7's already-adjudicated,
human-acknowledged regression carried forward unchanged.

### Why J-05 is not scored `passing` or `partial`

Three independent reasons, in descending weight:

1. The spec-mandated lane never ran (DoD item 1, TESTING REQUIREMENTS: "Browser: J-05, all 4 steps"). No
   evidence directory, no raw `.llm.md`, `browser_checks_run: false`. Steps 1–3 have zero evidence.
2. Step 4's evidence was produced and reported by the same agent that wrote the code — the audit
   corroborated its thermal half from `logs/hwmon/hwmon.csv` but explicitly declined to treat it as
   sufficient to flip the journey.
3. **My own finding, beyond audit/closure:** `reports/perf-budgets.md`'s iter-8 section states the clean
   run "never hit enough memory pressure to trigger the new `MemoryError`-specific branch at all", and
   that run executed under host-guard CPU-affinity (`0-3,8-11`) plus 4-thread BLAS/OMP caps that did
   **not** exist during iter-7's failing run (the mask was "inherited from the pump session — not
   independently re-created here"). So the 43.6% margin is a clean result under *changed host conditions*,
   not an isolated demonstration that iter-8's diff fixed it. Recovery is plausible and well-supported;
   it is not proven.

## Anti-goal Check

Worked from `runs/goal-session-ops-hardening/iter-8/scan-report.md` (**CLEAN**) plus `iter-diff.md`
(8 files: `data_manager.py`, 2 test files, `docs/goal.md`, `run-goal.sh`, 3 `project-extensions/host-guard/` files).

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (no unbacked "proven") | OK | No scoring, ledger, or badge code in the diff; product diff is one function's error handling. |
| AG-2 (decision-quality only) | OK | No return/price/order code touched. |
| AG-3 (displayed numbers correct) | OK | Diff adds only `except MemoryError` branches, a flag and a gate — no computation, cache key, or persisted value changed (audit §3). Byte-identity guard `test_finalize_hook_drawdown_expectations_byte_identical_to_fresh_compute` + the new partial-abort test re-asserting `stored == fresh` both pass. |
| AG-4 (no overfit edges) | OK | No referee/holdout code in the diff. |
| AG-5 (determinism / no-lookahead) | OK | No scoring or forward-return path touched. |
| AG-6 (referee gate) | OK | Ops/performance journeys carry no Evidence Claims (goal.md Loop mechanics). |
| AG-7 (no hard-coded credentials) | OK | scan-report CLEAN on added lines; grepped the new untracked `host-guard.env` + `hwmon-log.sh` for key/token/secret/password — only the word "KEY=VALUE" in a comment. |
| AG-8 (resilience / no memory exhaustion) | **UNRESOLVED (critical, carried from iter-7)** | Materially mitigated, not closed — see journey-history entry. Fix is real and unit-proven; live run clean; but no browser-qa re-verification, the new branch never fired live, host conditions differed, and the deferred on-load `/api/backtest` → `forward_aggregates_cached` → `ScannerResult` `MemoryError` (same AG-8 dimension) is still open. Kept fail-closed. |
| AG-9 (offline-deterministic ingest) | OK | No manifest change (no `package.json` / `requirements*.txt` / `pyproject.toml` in the diff), no network code, no provider substitution. Live measurement ran offline against a throwaway copy of the committed dev DB. |
| AG-10 (host resource ceiling) | **OPEN GAP (minor, not diff-introduced)** | `host-guard.env` is present, but the MUST-apply clause is unmet: `scripts/start-backend.sh` applies only config-derived `ulimit -v` (line 48) + `MALLOC_ARENA_MAX` (line 52) — no `taskset` mask, no BLAS/OMP caps from `host-guard.env`; `scripts/dev.sh` applies **nothing** (grep returns no `ulimit`/`MALLOC_ARENA_MAX`/`taskset`/`OMP_NUM_THREADS`). Nothing was stripped or weakened by this diff, and `docs/goal.md` itself schedules this as "in-scope launcher work for the next iteration" — hence minor, but it blocks GOAL_ACHIEVED. Positive note: the live measurement itself honored AG-10 (real `start-backend.sh`, verified affinity/limits/env on the live PID, armed thermal watchdog, never tripped). |

**Coherence:** `runs/goal-session-ops-hardening/iter-8/coherence.md` = **COHERENCE-PASS** (no new value,
no second producer, no frontend diff; `_release_process_memory()` reuse is the existing helper at the
existing call-site pattern). No structural veto, no consolidation mandate.

**Pipeline health:** review PASS_WITH_NOTES, QA PASS_WITH_NOTES, audit PASS_WITH_GAPS, closure
**CLOSURE-FAIL**, `status.json` = `blocked` / `closure_failed`. The pipeline did **not** fail open — the
closure gate correctly blocked on the same evidence gap the audit had already surfaced. No ESCALATE
signal.

**Process-honesty finding (not an anti-goal violation):**
`reports/phase-goal-ops-hardening-iter-8-implementation-summary.md` narrates the fix as having "passed
cleanly … the status indicator stayed responsive throughout", as though the phase's completion criterion
were met, while `ui-test-results.md` is a SKIPPED stub. The QA report's "Recommendation: PASS — ready to
ship" and the dev handoff's "Status: complete" overstate readiness identically. Flagged by the closure
auditor and endorsed here — the artifacts must be corrected when the verification lanes are re-run.

## Next-Step Recommendation

**Iteration 9, `full` depth — a pure VERIFICATION-AND-COMPLIANCE closeout. No new features, no new
product behavior.** Note `session.json` `max_iterations: 9`, so this is the last budgeted iteration; scope
it tightly, in this order:

1. **Run browser-qa for J-05's four acceptance steps** against the current (audit-repaired) build with
   host-guard protections active — the single blocking item. Step 4's heavy-ingest condition can be driven
   by the now-repaired opt-in test:
   `TRENDORA_RUN_HEAVY_INGEST_TEST=1 apps/backend/.venv/bin/pytest apps/backend/tests/test_start_backend_script.py::test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap`
   (never executable before the audit's T1/T3 fixes — run it at least once so the regression guard is
   proven, not assumed). Read the **raw** `...-ui-test-results.llm.md`, not the merged summary
   (iter-3/iter-4 lesson). Copy the VmPeak sampler CSV into `runs/goal-ops-hardening-iter-9/` (audit V3).
   Then replace the "SKIPPED — backend-only phase" stub with the real outcome.
2. **Run the regression lanes for J-01/J-03 (golden replay) and J-04 (LLM acceptance)** and emit a
   `phase-goal-ops-hardening-iter-9-regression-replay-results.md` (iter-7 precedent) — this is what moves
   all three out of `unknown`. Without it GOAL_ACHIEVED is impossible.
3. **Close the AG-10 launcher gap** (`docs/goal.md` names it in-scope for this iteration): add
   HOST-GUARD-marked blocks applying `host-guard.env`'s SMT-aware `taskset` mask + BLAS/OMP/numexpr caps
   to `scripts/start-backend.sh` and to `scripts/dev.sh`'s **backend subshell only** (mirror prod's
   `ulimit -v` + `MALLOC_ARENA_MAX` there too; never the frontend subshell). Values from `host-guard.env`,
   no magic numbers.
4. **Fix the harness misrouting that caused this iteration to verify nothing:** `Frontend Present: no`
   must not suppress browser-qa when the iteration spec's TESTING REQUIREMENTS name browser journeys.
5. Small carry-ins if capacity allows: audit B2 (memoize the libc handle so `_release_process_memory()`
   stops fork/exec-ing `ldconfig` on the memory-pressure path) and T4 (tighten the heavy test to reject
   `"partial"` and assert no `MemoryError` in the job record).
6. Still deferred, and correctly so: the on-load `/api/backtest` → `forward_aggregates_cached` →
   `ScannerResult` `MemoryError` (J-06/AG-8), and the `[NEW]` `demo.sh --session-live` walkthroughs for
   J-05/J-06 — both need explicit scope or human deferral before the GOAL_ACHIEVED gate.

**Do not redo:** the four-loop `MemoryError` fix, the audit's B1/T1/T2/T3 repairs, iter-7's `/evidence`
drawdown warm, `readiness.py` / `main.py` / `warmup.py`, `max_range_days` / `snapshot_cadence` /
range-cap logic.

## Halt Justification

Not halting.

- **REGRESSION rejected.** Decision tree C.1 fires on a journey that *moved* `passing`/`already_passing` →
  `failing` **this iteration**; none did. J-05's `regressed` is iter-7's regression, already halted on and
  human-acknowledged, with iter-8 dispatched as the sanctioned recovery — re-halting on it with zero new
  damage would put the human in front of a decision they have already made. The one unresolved critical
  violation (AG-8) is that same carried-over finding; the diff introduced no new violation (scan-report
  CLEAN), and the AG-10 gap was neither created nor worsened by this diff. Recorded as an interpretation
  call in `assumptions.md`.
- **STALLED rejected.** Every unblock path is agent-owned: run browser-qa, run the replay lane, add the
  HOST-GUARD blocks, fix the skip rule. The host-crash gate that previously made this human-owned is
  green — the owner ran the host-guard verification ladder Stages 0/A/B on 2026-07-21 ~21:35 and a
  supervised live heavy-ingest measurement has since completed without a thermal trip or reset.
- **GOAL_ACHIEVED impossible.** One journey `regressed`, three `unknown`, one `partial`; two anti-goal
  violations unresolved.
- **ESCALATE not applicable.** iter-8 was already `full`, the pipeline did not proceed fail-open (closure
  correctly blocked), and J-05 did not *fail* in two consecutive iterations — it failed in iter-7 and went
  unverified in iter-8.
