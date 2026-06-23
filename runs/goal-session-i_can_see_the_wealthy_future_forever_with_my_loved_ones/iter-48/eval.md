# Iteration 48 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** lean

## Summary

iter-48 completes the iter-47 J-105 streaming fix: the two still-unstreamed `select(ScannerResult)…all()` reads (`_factor_observations` research.py:232–236, `_combination_observations` :439–443) are now `yield_per(batch)`-streamed over the full ORM row (`record_json` preserved) with `.order_by(run_id, id)` — the byte-identical prior order that rides the existing `ix_scanner_results_run_id` index (no temp-B-tree spill on the 93%-full disk). Factor Lab (J-25) is RESTORED to passing on a genuine live rendered decile table; J-104 and J-105 flip partial → passing; every buildable Must-have (J-01..J-21, J-25..J-105) is positive-evidenced, the full backend suite flushed `1060 passed, 4 skipped, SUITE_EXIT=0`, coherence is COHERENCE-PASS, review PASS, with zero unresolved anti-goal violations. All GOAL_ACHIEVED conditions hold.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-25 — Factor Lab decile sort + rank-IC | regressed | passing | reports/qa/goal-…-iter-48-evidence/UT-02-decile-table.png |
| J-104 — research labs load reliably | partial | passing | UT-02-decile-table.png + UT-06-factor-combination.png + dev/QA HTTP-200 on all 5 labs |
| J-105 — read path never materializes an unbounded table | partial | passing | research.py:232–236/439–443 yield_per stream; test_research_streaming.py 29 passed |
| J-26 — multi-factor composite cohort | passing | passing | reports/qa/goal-…-iter-48-evidence/UT-06-factor-combination.png |
| J-29 — event-study | passing | passing (carried) | research/samples isolated green; HTTP 200 confirmed in backend log |
| J-77 / J-91 / J-103 | passing | passing (carried) | all five heavy labs HTTP 200 (one-at-a-time) |
| J-51 / J-63 / J-65 — N= count-coherence | passing | passing (carried) | UT-02 N= chips n=59827/decile → /research/samples links |
| J-72 / J-32 — streamed-builder byte-identity / as-of toggle | passing | passing (carried) | byte-identity tests green (29 streaming tests) |
| J-06 (CRITICAL single source) | passing | passing (carried) | snapshot-served fast path unperturbed by read-path refactor |
| J-18 (CRITICAL one date control) | passing | passing | UT-10: 0 native `input[type=date]` on /research (only a checkbox toggle) |
| J-07 (CRITICAL Risk-Off gate) | passing | passing (carried) | /api/runs invariant on the snapshot-served fast path, untouched |
| J-22 / J-23 / J-24 | unknown (blocked-NA) | unknown (blocked-NA) | data-walled; non-vetoing per goal.md:105–108 |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Single source of truth | OK | Streaming is a memory-safety refactor of the same canonical builders; figures byte-identical (29 streaming byte-identity tests green; reviewer confirmed the `(run_id,id)` order reproduces the prior implicit `.all()` order). |
| No recompute in read path | OK | Same endpoints serve the same canonical builders; no new computation, no second endpoint. |
| No magic numbers | OK | Reuses the existing `config.research.read_batch_size`; no new literal in a CALC_FILE (test_no_magic_numbers green). |
| No fabricated data | OK | The QueuePool-exhaustion SKIPs rendered an honest "Backend unavailable — No figures are shown rather than fabricated values" banner (UT-02-backend-unavailable.png); no synthesized figures. |
| No lookahead | OK | `as_of` membership filter unchanged; streamed reads honor `ScannerRun.asof_date <= as_of` identically. |
| Snapshots immutable | OK | Read-path-only change; no scanner_run/result write. |
| Risk-Off gates Actionable (CRITICAL) | OK | No scoring/gate change; backend-only read-path diff. |
| Honest forward-test for partial windows | OK | Zero-N cohort honest-NA path byte-identity tested. |

Lone ever-recorded violation (iter-20 minor magic-number) stays resolved since iter-21. No new violation this iteration.

## Next-Step Recommendation

Halt — goal achieved. Every buildable Must-have (J-01..J-21, J-25..J-105) is positive-evidenced; the iter-46 J-25/J-104/J-105 regression cluster is fully closed (all three flip to passing). J-22/J-23/J-24 stay honestly blocked-NA (provider-walled; non-vetoing per goal.md:105–108) — J-22 auto-unblocks via the already-built+passing J-84 cookie+crumb expand path with NO code change once a cap-capable provider is reachable, best handled by a future lean in-place resume scoped to a data fetch. Do NOT re-trigger the J-85 `kind:rebuild` (~11h destructive; the data is correct). Operational note: the host disk is ~93% full (4.3 GB free) — Factor Lab no longer needs a temp-sort file (the `(run_id,id)` ordering rides the index), but unrelated heavy ops could still hit disk limits; Factor Lab is intentionally uncached (~50–120s cold compute). If the owner extends goal.md and resumes in-place, regenerate/re-approve the blueprint on resume.

## Halt Justification

All four GOAL_ACHIEVED conditions are independently verified:
1. **Every Must-have positive-evidenced** — the only prior non-positive buildable journeys (J-25 regressed, J-104/J-105 partial) all flip to passing this iter; J-25 on a genuine evaluator-VIEWED live decile table (UT-02-decile-table.png: D1–D10 numeric means +0.82%..+0.61%, n≈59827/decile, Rank-IC +0.01, total 598271, no error banner), J-104 on all-five-labs HTTP 200, J-105 on the verified streaming diff + green byte-identity tests. J-22/J-23/J-24 are data-walled and explicitly non-vetoing.
2. **Zero unresolved anti-goal violations** — byte-identity preserved (Single-source / No-recompute hold); no magic number; honest error only; the lone iter-20 violation stays resolved.
3. **COHERENCE-PASS** — backend-only memory-safety refactor of registered canonical builders; no new value/route/duplicate-home (coherence.md SHA 6f7efa0).
4. **Flushed-GREEN full suite** — /tmp/iter48_full_suite.log: `1060 passed, 4 skipped in 5585.75s`, `SUITE_EXIT=0`, zero FAILED/ERROR lines, on a quiet backend.

Skeptical note on the 5 browser-QA SKIPs: they are a test-harness artifact (the browser-QA agent's own concurrent Playwright+Chrome traffic exhausted the 15-connection SQLite QueuePool mid-session), NOT a code regression — every research endpoint returned HTTP 200 earlier in the same backend session (confirmed in /tmp/iter48_backend2.log), the dev independently verified all five labs HTTP 200 on a quiet single-fetch backend (RSS bounded ~733 MB, zero MemoryError/disk-full), and the load-bearing J-25 journey has positive rendered evidence captured before exhaustion. Browser-QA verdict was PASS (7 passed, 5 skipped, 0 failed).
