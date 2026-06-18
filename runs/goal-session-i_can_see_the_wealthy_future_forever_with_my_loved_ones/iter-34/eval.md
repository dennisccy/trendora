# Iteration 34 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The iter-34 lean live re-verification ran genuinely live (Chrome MCP timed out; the browser-qa-agent fell back to Playwright and produced real, large, md5-distinct, evaluator-VIEWED frames) and wrote the missing `ui-test-results.md` (the iter-33 CLOSURE-FAIL artifact now exists). J-94 (per-date coverage diagnostic) and J-95 (confirm-gated backward-history control + survivorship label) flip `partial → passing` on genuine rendered evidence. BUT J-93 is a genuine acceptance FAIL — the dynamic point-in-time universe does NOT slide on `/stocks` (122 rows at every as-of, including 2021-01-04 well before the warm-up boundary), and J-96's membership-timeline step function is a flat-122 line with no entries/exits — both because the persisted `ScannerResult` snapshots were built by the iter-27 J-85 rebuild BEFORE iter-33 repointed `score_stocks` to the resolver, and were never regenerated. This is not a regression (J-93/J-96 were never passing) and not blocked-NA (J-93/J-96 are explicitly NOT data-dependent, goal.md:2272) — it is a tractable data-regeneration gap → CONTINUE.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-93 | partial | **failing** | reports/qa/.../UT-J-93-2021-01-04.png, UT-J-93-full-2022.png, UT-J-93-early.png — all show 122/122 rows; resolver admits 0 at 2021-01-04 but `/stocks` serves stored 122 |
| J-94 | partial | **passing** | reports/qa/.../UT-J-94-universe-resolution.png (admitted=544, below-history=1/below-price=2/below-ADV=1, thresholds 200/10.0/50000000.0) |
| J-95 | partial | **passing** | reports/qa/.../UT-J-95-extend-history-section.png (Extend-history-backward confirm-gated control + survivorship caveat; real fetch blocked-NA) |
| J-96 | partial | **partial** | reports/qa/.../UT-J-96-membership-timeline-section.png — 3 honesty labels render, but the step function is a FLAT 122 line, SIZE=122 all dates, entries/exits all "—" (same stale-snapshot root cause as J-93) |
| J-06 | passing | passing | reports/qa/.../UT-J-06-stocks-list.png, UT-J-06-nvda-detail.png (Leadership=37.19/Entry=62.23/Risk=32.04 identical both surfaces) |
| J-18 (CRITICAL) | passing | passing | reports/qa/.../UT-J-18-backtest.png (0 `input[type=date]`; single global switcher) |
| J-07 (CRITICAL) | already_passing | passing | reports/qa/.../UT-J-07-risk-off-run-1317.png (Risk-off → 0 Actionable, 122 Risk-off-watchlist) |
| J-87 | passing | passing | reports/qa/.../UT-J-87-dashboard-full.png (Expansion, severity 28.75/100) |
| J-88 | passing | passing | reports/qa/.../UT-J-87-dashboard.png |
| J-89 | passing | passing | reports/qa/.../UT-J-89-dashboard-detail.png |
| J-90 | passing | passing | reports/qa/.../UT-J-90-research-detail.png |
| J-91 | passing | passing | reports/qa/.../UT-J-91-samples.png |
| J-92 | passing | passing | reports/qa/.../UT-J-92-backtest-detail.png |
| J-08 | passing | passing | reports/qa/.../UT-J-08-scanner-runs-detail.png (1371 runs, regime labels) |
| J-36 | passing | passing | reports/qa/.../UT-J-36-per-symbol-table.png (585 symbols, 122 in_universe) |
| J-37 | already_passing | passing | reports/qa/.../UT-J-37-missing-data-panel.png (affected_count=0) |
| J-39 | passing | passing | reports/qa/.../UT-J-39-remove-data-panel.png (preview only, non-destructive) |
| J-85 | passing | passing | reports/qa/.../UT-J-85-rebuild-panel.png (absent_count=424 of 544 resolved; confirm-gated, NOT triggered) |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead (membership uses bars ≤ D) | OK | Resolver `universe_resolver.resolve_with_reasons` admits 0 at 2021-01-04 / 496 at 2022-01-03 — correctly causal; unit-asserted iter-33. The `/stocks` gap is the OPPOSITE of lookahead (stale stored membership), not a violation. |
| Single source of truth (one module, one endpoint, FE reformats) | OK (with a live data-consistency NOTE) | The fold-in reads the three methodology fields verbatim from `GET /api/methodology` (no recompute; coherence COHERENCE-PASS). NOTE: the live system is internally inconsistent — the J-94 diagnostic reports admitted=544 at latest while `/stocks`+J-96 timeline serve 122 — because the persisted snapshots predate the resolver. This is a regeneration gap, not a second computation. |
| Snapshots immutable; committed seed never deleted | OK | iter-34 triggered NO destructive `/data` action; J-85/J-95 controls verified render-only. Backend diff EMPTY. |
| No magic numbers | OK | No calc code touched (backend byte-unchanged); fold-in is presentation-only. |
| No fabricated data | OK | Early-date `/stocks` is NOT padded — it (incorrectly) shows the stale 122, but those are real stored rows, not fabricated. J-94/J-96 excluded-by-reason counts are honest. |
| Exactly one date control (CRITICAL) | OK | UT-J-18: 0 `input[type=date]` on /backtest; fold-in adds no date state (coherence + review confirm). |
| Honest limitations surfaced | OK | J-96 renders all three caveats (survivorship / warm-up / universe-relative) verbatim; J-95 real fetch blocked-NA. |
| No secrets in source | OK | No provider/index-feed key touched; fold-in is frontend display only. |

## Next-Step Recommendation

iter-35 should CLOSE the J-93 / J-96 stale-membership gap — this is the LAST real obstacle to GOAL_ACHIEVED and it is **not code work**, it is a **data-regeneration operation**:

1. **Run the J-85 confirm-gated regenerate-from-scratch rebuild ONCE** so the persisted `ScannerResult` snapshots are recomputed over the iter-33 per-date `resolve_members` membership. After this, `/stocks` will serve the dynamic membership (empty/small before the ~2021-10-18 warm-up boundary, rising to full) and the J-96 timeline SIZE column + step function + entries/exits will reflect the real dynamic universe. **CAUTION (MEMORY.md):** a `kind:"rebuild"` is ~11h and CLEARS the snapshot layer; it must be operator-confirmed and run via the pump (nohup), NOT a casual QA action. The committed price seed is never deleted (`clear_snapshot_set` asserts `bars_before == bars_after`). This is the operation J-93's own acceptance names ("populated exclusively by the J-85 confirm-gated regenerate-from-scratch rebuild").
2. **Then a LEAN live re-verification** of J-93 (two byte-DISTINCT `/stocks` frames with DIFFERENT row counts: early-date empty/small vs full ~496) and J-96 (the step function now RISES from the warm-up boundary; entries/exits populated). Reconcile the resolved-latest count: the J-94 diagnostic says ~544 admitted at latest — confirm `/stocks` now matches (within the benchmark/stocks-only distinction) so the J-06 single-source contract still holds across the diagnostic and the served membership.
3. **Re-run the FULL backend suite to `0 failed, EXIT 0`** (nohup-async to the pump; never block the evaluator — iter-11/29). The iter-34 run was EXIT=1 on exactly ONE test, `test_warmup.py::test_start_warmup_is_single_flight_no_duplicate_concurrent_worker` — a 600s warm-up timeout under QA resource pressure (`dates_done: 1 of 6`, status `running`), the documented slow-boot/warm-up contention flake (MEMORY.md), on a byte-UNCHANGED backend that passed clean at iter-33. Re-run it in isolation on a quiet host to confirm it is a flake, not a regression, before any GOAL_ACHIEVED candidacy.

Depth = **full** because triggering + verifying the rebuild touches the snapshot/scanner determinism + immutability surface and warrants the audit/closure pipeline. Required-still-passing: J-06 (now critically — the diagnostic-vs-served count reconciliation), J-18/J-07 (CRITICAL), J-87/J-88/J-89/J-90/J-91/J-92 (consumed market-phase layer — confirm the rebuild does not perturb the regime/ETF machinery, which is stocks-only-exempt), J-08/J-15/J-85 (immutability + snapshot-served reads). J-22/J-23/J-24 + J-95 real-fetch / constituent-feed legs stay honestly blocked-NA (non-vetoing).

NOTE: if an operator-confirmed ~11h rebuild is not acceptable in this session, the alternative is to confirm whether J-93/J-96 should be judged against the BUILT-and-causally-correct resolver (data-correctness PASS, already proven offline iter-33) rather than the rendered served membership — but the current goal.md acceptance and the iter-33/iter-34 evaluators both require the served/rendered end state, so the rebuild is the honest path to passing.

## Halt Justification (if halting)

Not halting. CONTINUE: progress was made (J-94, J-95 newly passing on genuine live evidence), no journey regressed (J-93/J-96 were `partial`, never `passing`), no critical anti-goal violation, coherence COHERENCE-PASS. J-93/J-96 carry a tractable, identified next step (the J-85 rebuild to persist the dynamic membership). Not GOAL_ACHIEVED: J-93 is `failing` and J-96 is `partial` with verified-deficient end-state evidence, and the full suite is EXIT=1 (warm-up flake) — the gate is unmet.
