# Iteration 24 Evaluation

**Verdict:** REGRESSION
**Depth Recommendation For Next Iteration:** full

## Summary

iter-24 shipped its intended fast-platform mechanical backend pass (items B/C/D/G/H) + the item-K
storage-footprint card correctly on a WARM backend, but item B's SQLite tuning introduced a **critical
anti-goal #8 violation**: `mmap_size_bytes=1 GB` per connection × `pool_size=10/max_overflow=20`
exhausts the `ulimit -v` cap, OOM-crashing the backend (MemoryError → PyO3 panic that kills uvicorn)
on the very first cold `GET /api/data` load after any restart — reproduced 2/2 by the canonical
browser-qa lane. This broke required-still-passing **J-13** (its `/data` surface crashes cold) and
failed target **J-15**'s own "cold /api/data completes ≤60 s without OOM" acceptance criterion. Both
independent gates fired (UX-REGRESSION-FAIL, CLOSURE-FAIL) while the QA report fail-opened to PASS —
the exact iter-18 pattern. The auditor applied the fix in-tree (`mmap_size_bytes=0`) and engine-ablation-
verified it, but the DoD-named canonical browser-qa lane has NOT re-verified it, so on the evidence the
framework trusts the violation is unresolved. Per decision-tree rule 1 (a prior-passing journey now
failing AND a critical anti-goal violated) → REGRESSION; halt for human review.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Every score shows a status | passing | passing (warm replay) | `reports/qa/goal-mcp-loop-iter-24-evidence/UT-08-stocks-leaderboard-AAPL.png` (opened) |
| J-02 Drill into the proof | partial | partial (by design; no evidence work) | ledgers git-unchanged, all-FAIL |
| J-03 Unproven honestly marked | passing | passing (byte-identity carry; not clean-replayed) | engine-core zero-diff; UT-08 warm corroboration |
| J-04 Regime-conditioned evidence | passing | passing (byte-identity carry; not clean-replayed) | regime.py zero-diff; UT-08 "Risk-on 72.25" |
| J-05 Audit the ledger | passing | passing (byte-identity carry; not clean-replayed) | app/evidence + ledger.py zero-diff |
| J-06 vcp_contraction edge | partial | partial (by design; no evidence work) | canonical row FAIL −0.38%, unchanged |
| J-07 Multi-horizon edge | partial | partial (by design; no evidence work) | canonical row FAIL −1.64%, unchanged |
| J-08 Combination edge | partial | partial (by design; no evidence work) | canonical row FAIL +0.01%, unchanged |
| J-09 rs_spy_3m h60 edge | partial | partial (by design; no evidence work) | canonical row FAIL −1.42%, unchanged |
| J-10 Deep price history | passing | passing (warm replay) | `reports/qa/goal-mcp-loop-iter-24-evidence/UT-09-full-history-toggle.png` |
| J-11 No stale edge survives | passing | passing (byte-identity carry; not clean-replayed) | both ledgers git-unmodified, all-FAIL; no `## Evidence Claim` |
| J-12 Broad point-in-time universe | passing | passing (warm corroboration UT-07) | `reports/qa/goal-mcp-loop-iter-24-evidence/UT-01-UT-02-storage-footprint.png` (opened); 541==541/541 |
| **J-13 Data Manager page** | **passing** | **REGRESSED** | `reports/qa/goal-mcp-loop-iter-24-evidence/UT-16-backend-crash-log-excerpt.txt` (opened) — cold `/data` OOM-crash 2/2; UT-06 (P1) FAIL |
| J-14 Deep index/macro vendor context | passing | passing (byte-identity carry; not clean-replayed) | chart components + config index symbols zero-diff |
| **J-15 Fast platform (TARGET)** | unknown | **partial** (NOT passing) | warm: UT-01/02/15 + perf-budgets.md (opened UT-01-UT-02); cold-path FAIL: UT-16 crash log |
| J-16 Fast data jobs | unknown | unknown (deliberately deferred) | out of scope (rubric rule 5) |

Notes on carried-passing journeys: the canonical browser-qa run **FAILED mid-run** (the backend
crashed on the cold `/data` path), so the required-still-passing live replay is INCOMPLETE. J-01 (UT-08)
and J-10 (UT-09) got clean warm pixels; J-03/J-04/J-05/J-11/J-14 are carried on byte-identity only
(engine-core + their frontend surfaces are git-diff-empty vs snapshot; iter-24 changes are query/plan/
cache/introspection with no scoring or displayed-value change) and must be freshly replayed in the
fix-verification pass.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| #1 No proven/confident without a passing certified-claim | OK | No evidence work; ledgers git-unchanged, all-FAIL; UT-08 shows every score "Not yet proven" |
| #2 No return/price-target/buy-sell/order language | OK | "Research-only · decision support · no orders" header present (UT-01/UT-08); storage card is pure metadata |
| #3 Displayed numbers correct / byte-identical | OK | Existing API byte-identity tests pass UNEDITED; UT-02/07/08/10 values cross-checked; item K = real DB introspection (1.22 GB / 3,293,160 / 165,755 / 821,054) |
| #4 No overfit edges | OK | No `## Evidence Claim`, no ledger change |
| #5 Determinism + no-lookahead | OK | No scoring/referee change; items are query/plan/cache only; coherence COHERENCE-PASS |
| #6 No ship without a passing referee verdict | OK | No claims carried; post-decompose gate passes automatically |
| #7 No hard-coded credentials | OK | scan-report.md CLEAN (secrets/deps/license); `.gitignore` added `*.db-shm`/`*.db-wal` only |
| **#8 Resilience to data-scale change (no crash / no memory exhaustion)** | **VIOLATED — CRITICAL** | Cold `GET /api/data` OOM-crashes the backend (MemoryError → PyO3 panic; VmSize pinned at the 6144 MB `ulimit -v`, VmRSS ~2.9 GB = virtual-address-space exhaustion), reproduced 2/2. Root cause: item B `config.yaml` `mmap_size_bytes=1073741824` × `pool_size=10`/`max_overflow=20`. Confirmed by UX-REGRESSION-FAIL + CLOSURE-FAIL. Fix applied in-tree (`config.yaml:108` → 0) + auditor ablation (471 MB peak), **but NOT re-verified by the canonical browser-qa lane** → `resolved=false` |

## Next-Step Recommendation

Halt for human review. On `--acknowledge-regression`, **iter-25 (FULL) is a fix-VERIFICATION pass, NO
new feature code** (the `mmap_size_bytes=0` fix is already applied and correct in the working tree):

1. `rm -rf apps/frontend/.next`; bring up BOTH prod-mode services (`start-backend.sh`/`start-frontend.sh`)
   and confirm HTTP-200 on `:8255`/`:3255` BEFORE dispatching QA.
2. Re-run the canonical browser-qa lane, specifically re-driving the **UT-16 → UT-06 → UT-05** cold-path
   sequence (stop backend → cold-start → load `/data` as the FIRST request, at least twice) and confirm
   all flip FAIL→PASS, with a non-empty md5-distinct evidence dir. This is the only evidence that
   converts the auditor's engine-level ablation into journey-level proof.
3. Complete the required-still-passing live replay the crash aborted: J-03, J-04, J-05, J-11, J-14 (only
   byte-identity carry this iteration).
4. Correct `reports/perf-budgets.md`'s cold-path claim with a REAL fresh-restart `/data` measurement
   (audit B2); add the crash/fix/re-verify note to `implementation-summary.md` + `user-visible-changes.md`
   (closure Blocking Issue 2); regenerate `status.json` (it predates the FAIL findings; `qa_verdict=PASS`
   + `blockers=[]` while `current_step=closure_failed` is stale/contradictory).
5. Re-run ux-regression → UX-REGRESSION-PASS and phase-closure → CLOSURE-PASS.

On a clean cold-path run, **J-13 returns to passing and J-15 flips partial→passing**. GOAL_ACHIEVED still
not reachable that iteration: J-02/J-06/J-07/J-08/J-09 remain sanctioned-partial (need a new-basis staging
winner clearing Bonferroni divisor-8; none does today) and J-16 (data-jobs perf, item F) is deliberately
unbuilt. Non-blocking, do NOT bundle: F1 (add auto-retry to `/data`'s error state so a transient failure
doesn't strand the page beside a green readiness badge — P3); T1 (cadence-aware backfill range in
`measure-perf.sh`). Process note for the rubric: the QA agent graded TC-10 ("cold path no OOM") PASS from
the dev handoff's later-INVALIDATED claim while its own browser-qa lane read FAIL — a fail-open that
would have shipped a critical crash had the ux-regression + closure gates not read the browser-qa content.

## Halt Justification

Halting with **REGRESSION** (decision-tree rule 1 — first match wins):

- **A prior-passing journey is now failing.** J-13 (Data Manager `/data`, passing since iter-16, last
  clean at iter-23) crashes the backend on its cold load. I personally opened
  `UT-16-backend-crash-log-excerpt.txt`: `MemoryError` in `cursor.fetchmany()` (`prices.py:141` prefill)
  then a fatal PyO3 panic terminating uvicorn, `VmSize` pinned at exactly the 6144 MB `ulimit -v` while
  `VmRSS` is ~2.9 GB. Reproduced 2/2. Both independent gates confirm it broken: UX-REGRESSION-FAIL
  ("CRITICAL — confirmed, not potential") and CLOSURE-FAIL.
- **A critical anti-goal was violated (`resolved=false`).** The crash is a direct anti-goal #8 violation
  ("must never crash an existing page or exhaust a service's memory"). The auditor's fix
  (`mmap_size_bytes=0`, git-verified in the working tree) is engine-ablation-verified (471 MB peak) but
  the DoD-named canonical browser-qa lane has NOT re-verified it — its last word is FAIL with the crash
  reproduced. Per the fail-closed rule for critical anti-goals and the session's own repeated lesson
  (iter-13/20/22: an engine/code-level fix is not a substitute for the canonical lane), the violation is
  not verifiably resolved.

Why not the alternatives: **Not CONTINUE** — a critical anti-goal was violated and a prior-passing
journey broke, so the framework halts for human review rather than auto-looping (iter-18 precedent: same
anti-goal #8 crash class, same UX-REGRESSION-FAIL + CLOSURE-FAIL + fail-open `status.json`, verdict was
REGRESSION). **Not GOAL_ACHIEVED** — J-13 regressed, J-15 partial, J-02/06/07/08/09 sanctioned-partial,
J-16 unknown, CLOSURE-FAIL. **Not STALLED** — the fix is a config change already applied, not a
human-owned blocker; the next step is a mechanical verification re-run. **Not ESCALATE** — already full
depth; the review stage PASSED (not fail-open), and no journey has failed two consecutive iterations.
Coherence is COHERENCE-PASS, so there is no structural veto — the defect is operational, not IA/data-
contract drift. Resume after acknowledging the regression; the applied fix carries forward and iter-25
is the verification-only pass described above.
