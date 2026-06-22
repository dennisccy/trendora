# Iteration 46 Evaluation

**Verdict:** REGRESSION
**Depth Recommendation For Next Iteration:** full

## Summary

This verify-only lean re-verification pass (zero source diff, COHERENCE-PASS, review PASS_WITH_NOTES) surfaced a GENUINE standing defect that I independently reproduced: the two heavy research labs `/api/research/event-study` (J-29) and `/api/research/factor-lab` (J-25/J-26) raise `MemoryError` on the live 3.3 GB / 3,081,454-row `forward_returns` DB because `_event_study_members_by_horizon` (apps/backend/app/engine/research.py:823-828) materializes the entire `select(ForwardReturn).where(horizon.in_(horizons)).all()` into ORM objects. These three journeys plus J-104's "labs load reliably without error" acceptance were `passing` in prior iterations and are now user-observably broken on the live system, so per the REGRESSION rule the loop halts for human review. The break is NOT introduced by this iteration's code (zero diff; the unbounded `.all()` is byte-identical from iter-20 through the iter-43/45 GOAL_ACHIEVED states) — it is a data-scale + host-RAM exposure of pre-existing code that needs a deliberate code fix (server-side bounding/streaming of the all-history fetch), which the human should consciously authorize.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-25 (Factor Lab — decile/rank-IC) | passing | **regressed** (failing) | reports/qa/.../iter-46-evidence/UT-J-25-factor-lab.png (FACTOR selector stuck "Loading…", skeleton, no data) + my live probe peak RSS 5466 MiB |
| J-26 (Factor Lab — multi-factor composite) | passing | **regressed** (failing) | same factor-lab MemoryError path; UI shell only, no data |
| J-29 (Setup & Pattern event study) | passing | **regressed** (failing) | reports/qa/.../iter-46-evidence/UT-J-63-event-study-shell.png (SUBJECT "Loading…", skeleton rows, no data) |
| J-104 (Research labs load reliably — page split) | passing | **partial** (5/7 labs OK; event-study + factor-lab MemoryError → reliability acceptance UNMET) | UT-J-104-research-hub.png (hub IA intact, 7 cards) |
| J-103 (Severity-velocity × regime study) | passing | passing (dev live probe: 3×3 matrix, As-of N 1147→301 at ?as_of=2022-12-31, N= count-coherent, verbatim caveats) | dev handoff live probe; iter-45 UT-02-result.png |
| J-06 (score consistency) | passing | passing (live) | reports/qa/.../iter-46-evidence/UT-J-06-detail.png (NVDA Avoid/Pullback, themes, $208.21, single source) |
| J-07 (Risk-Off gate, CRITICAL) | passing | passing (live) | reports/qa/.../iter-46-evidence/UT-J-07-riskoff-run.png (Risk-off 28.11, Actionable=0, 540 watchlist) |
| J-18 (one date control, CRITICAL) | passing | passing (live) | reports/qa/.../iter-46-evidence/UT-J-18-backtest-asof.png (0 native date inputs; ?asof=2022-06-30 historical) |
| J-101/J-102/J-97/J-98 (Dashboard) | passing | passing (deterministic replay J-101/J-102; carried byte-unchanged) | J-101-verify.png, J-102-verify.png |
| J-77/J-91/J-90/J-63/J-65/J-51/J-32/J-72 | passing | unknown this iter (SKIPPED — backend contention/warm-up MemoryError); carried passing | isolated test_research/test_samples 108/108 on quiet host (dev) |
| J-22/J-23/J-24 | unknown (blocked-NA) | unknown (blocked-NA, non-vetoing) | n/a — data-walled |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No recompute in read path | OK | zero source diff; no read-path recompute introduced |
| Single source of truth (critical) | OK | J-06 live: NVDA detail == leaderboard; no value diverges |
| No lookahead (critical) | OK | zero diff; J-103 As-of samples all ≤ D (dev probe) |
| No fabricated data | OK | the failing labs return an honest HTTP 500 / "Backend unavailable" banner — they never synthesize figures (the MemoryError surfaces as an honest error, not fake data) |
| Honest limitations surfaced | OK | survivorship/descriptive disclaimers render on the lab shells |
| Risk-Off gates Actionable (critical) | OK | UT-J-07 live: Risk-off → 0 Actionable |
| Exactly one date selector (critical) | OK | UT-J-18 live: 0 native input[type=date] |
| No order/execution path (critical) | OK | zero diff; "Research-only · no orders" header intact |
| No magic numbers | OK | lone ever-recorded iter-20 minor violation stays resolved since iter-21 |

No new anti-goal violation (zero source diff). The MemoryError is a resource defect, NOT an anti-goal breach — the failing labs honor "No fabricated data" by returning an honest error state.

## Next-Step Recommendation

iter-47 FULL (resume with `--acknowledge-regression`) — bound the all-history `ForwardReturn` materialization so event-study (J-29) and factor-lab (J-25/J-26) load without `MemoryError` on the 3.08M-row live DB, restoring J-104's "labs load reliably" acceptance. The fix is a real, scoped code change (the spec's OUT-OF-SCOPE directive deliberately deferred it to the evaluator):

1. In `_event_study_members_by_horizon` (apps/backend/app/engine/research.py:823) STOP materializing `select(ForwardReturn).where(horizon.in_(horizons)).all()` (~3.08M ORM objects, ~5.3+ GiB peak RSS per request — independently reproduced). Options: (a) `session.exec(...).yield_per(N)` / server-side streaming so peak memory is bounded; (b) push the per-(subject, horizon) grouping into the cached `EventStudyCache` aggregate so the read path never materializes the full table; (c) project to lightweight columns/tuples (not full ORM rows) for the join. Whichever is chosen, the served per-horizon member lists and every downstream figure MUST stay byte-identical (the function's documented byte-identity contract; assert with a seeded test, and re-run `test_research.py`/`test_samples.py` count-coherence — J-29/J-63/J-51/J-65).
2. Apply the same bounding to any other unbounded `.all()` over `forward_returns`/`scanner_results` reachable from factor-lab / the heavy labs, and to the warm-up `backfill_forward_returns` step (warmup.py:155 also MemoryError'd — non-fatal by the J-40/J-41 serve-fast design, but it leaves warm-up `failed`).
3. Then LIVE re-verify on a quiet, warmed, single-fetch-at-a-time backend (Playwright fallback planned up front; md5sum the dir first; reject "Loading…"/"Backend unavailable"/skeleton frames): event-study (J-29), factor-lab (J-25/J-26), each rendering REAL figures + a working N= drill-down; plus the light labs (J-77/J-91/J-90/recovery) and J-103 As-of mode that this iter could not capture under contention. Required-still-passing: J-06/J-18/J-07 (CRITICAL), J-101/J-102/J-97/J-98, J-51/J-65 count-coherence.
4. Gate GOAL_ACHIEVED candidacy on the FLUSHED full-suite `0 failed, EXIT 0` (nohup-async; never block the evaluator; re-run any isolated test_warmup.py/test_watchlist_persistence.py E/F before attributing — slow-boot/warm-up contention flake). Do NOT re-trigger the J-85 `kind:rebuild`. J-22/J-23/J-24 stay blocked-NA (non-vetoing per goal.md:105-108).

## Halt Justification

The loop halts because three previously-`passing` Must-have journeys (J-25, J-26, J-29) and J-104's reliability acceptance are now genuinely `failing`/`partial` on the live system — the literal REGRESSION trigger (a journey with prior status `passing` is now `failing`). I did not trust the dev handoff: I independently reproduced the root cause by executing the exact `_event_study_members_by_horizon` all-history fetch against the live 3.3 GB DB, which materialized 3,081,454 ForwardReturn ORM objects at a **peak RSS of 5,466 MiB** in 172 s. On this shared multi-project host, available RAM oscillated between 3 GiB and 16 GiB during my checks; a single research request demanding 5.3+ GiB (and two concurrent heavy labs, or a concurrent warm-up `backfill_forward_returns`, each demanding similar) reliably overflows — confirming the dev's MemoryError on a freshly-warmed idle backend is a standing data-scale/host-RAM defect, NOT mere transient CPU contention (which separately accounts for the 12 SKIPPED journeys, re-verifiable on a quiet backend). `git log -S` and `git show` confirm the unbounded `.all()` originated in iter-20 (6733c1d) and is byte-identical through the iter-21/43/45 GOAL_ACHIEVED-candidate states, and this iteration's working tree carries ZERO source diff (only `runs/` telemetry + a `blueprint.reapproval-requested` marker) — so the regression was exposed by a deliberate data operation (the J-85 rebuild + restored daily-history backfills growing `forward_returns` to ~3.08M rows) plus the host's RAM ceiling dropping, not by code. GOAL_ACHIEVED is impossible while J-25/J-26/J-29/J-104 cannot be positive-evidenced, and the corrective is a real bounded-fetch code change that the human should consciously authorize. The failing labs return an honest HTTP 500 / "Backend unavailable" (no fabrication — the anti-goal contract holds); COHERENCE-PASS; no new anti-goal violation. Resume with `--acknowledge-regression` after the iter-47 fix is scoped.
