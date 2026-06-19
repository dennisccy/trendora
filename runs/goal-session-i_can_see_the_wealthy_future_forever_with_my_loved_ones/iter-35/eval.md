# Iteration 35 Evaluation

**Verdict:** REGRESSION
**Depth Recommendation For Next Iteration:** full

## Summary

The out-of-band J-85 confirm-gated regenerate-from-scratch rebuild (job `eb48cbf1`, 1369/1369 dates; **not** re-triggered this iteration — the source diff is empty vs both HEAD and the coherence snapshot SHA) genuinely **fixed J-93**: the persisted `ScannerResult` snapshots now ARE the per-date dynamic membership and the universe slides `0 → 494 → 504 → 544` on `/stocks`, proven by three byte-distinct, evaluator-viewed frames. But the same rebuild **regressed the `/data` page**: the J-96 membership-timeline computation (`_membership_timeline`, a 1369-date uncached resolver loop co-located in `compute_coverage`) now makes `GET /api/data` hang >300 s, so the `/data` page that rendered J-94 fully in iter-34 no longer hydrates at all (skeleton-only). A previously-passing Must-have (J-94) is now broken in the browser ⇒ REGRESSION; J-96 stays partial (data correct, page un-rendered).

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-93 Per-as-of-date dynamic universe slides on /stocks | failing | **passing** | UT-J-93a-stocks-2021-01-04.png (viewed: 0 rows, honest empty), UT-J-93b-stocks-2022-02-01.png (viewed: 6.0MB, 504/504 rows), UT-J-93c-stocks-latest.png + UT-J-06a (544/544); md5-distinct e6595c7b/8d43b252/dfd985fd |
| J-94 Min-history sufficiency gate + warm-up (per-date coverage diagnostic) | passing | **regressed** | UT-J-96a-data-top.png (viewed: /data header renders, all panels un-hydrated skeleton — GET /api/data hangs >300s). Was passing iter-34 via the fully-rendered UT-J-94-universe-resolution.png |
| J-96 Membership timeline + survivorship/coverage labels | partial | **partial** (data now correct, render still fails) | UT-J-96a-data-top.png (viewed: skeleton); DB-direct confirms rising step 0→544, entries/exits populated, 3 labels verbatim, but no pixel evidence of the rendered timeline |
| J-06 Single source (NVDA list == detail) | passing | passing | UT-J-06b-stocks-detail-NVDA.png (viewed: Avoid/Pullback, as-of 2026-06-16, themes/invalidation/fwd-returns NA) |
| J-07 Risk-Off → 0 Actionable (CRITICAL) | passing | passing | UT-J-07-stocks-risk-off.png; dev re-verify: 195 Risk-off dates, 0 Actionable, non-vacuous (166 Actionable under Risk-on) |
| J-18 Exactly one date selector (CRITICAL) | passing | passing | UT-J-18-backtest-no-date.png (0 input[type=date]) |
| J-15 /stocks leaderboard speed | already_passing | already_passing (re-verified) | UT-J-15-stocks-speed.png (544/544 at latest) |
| J-87 Dashboard market-phase | passing | passing | UT-J-87-dashboard-market-phase.png (Defensive 32.87) |
| J-88 Dashboard bear-probability | passing | passing | UT-J-88-dashboard-bear-prob.png (Risk-off 6.33) |
| J-22 / J-23 / J-24 | unknown (blocked-NA) | unknown (blocked-NA, non-vetoing) | n/a — data-walled per goal.md:105-109, 2282 |

All other buildable Must-haves carry forward `passing`/`already_passing` (backend byte-unchanged; no regression observed elsewhere).

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead | OK | resolver admits only bars ≤ D; first populated date 2021-10-18; 0 at 2021-01-04 |
| Snapshots are immutable | OK | clear-then-create-once rebuild; no in-place UPDATE |
| The committed seed is never deletable | OK | daily_prices 793,218 bars == .pre-iter35-rebuild.bak (bars_before == bars_after) |
| Single source of truth | OK | NVDA leaderboard == detail; resolver-direct 544 == served /api/stocks 544 |
| No recompute in the read path | OK | /api/stocks serves stored ScannerResult rows; the /data timeline is a read-only descriptive derivation (the perf issue is slowness, not a canonical recompute) |
| No fabricated data | OK | 2021-01-04 honest empty "No rows are fabricated"; J-96 early dates n=0 |
| No magic numbers | OK | empty source diff — no new literals introduced |
| Risk-Off gates Actionable to zero (CRITICAL) | OK | J-07 re-verified non-vacuously (correct `Risk-off` casing) |
| Exactly one date selector (CRITICAL) | OK | J-18: /backtest has 0 input[type=date] |
| Honest limitations surfaced | OK | universe-relative breadth + survivorship labels present (DB-direct verbatim) |

No anti-goal violation. The regression is a read-path **performance** defect exposed by correct data growth, not a contract/anti-goal breach. Coherence: **COHERENCE-PASS** (zero IA/data-contract drift; no new computation path or endpoint). Review: **PASS**.

## Next-Step Recommendation

iter-36 **FULL** — make `GET /api/data` responsive WITHOUT changing any served value:
- Cache `universe_resolver.resolve_with_reasons()` per `(date, cfg)` and/or precompute the J-96 `membership_timeline` during the background warm-up daemon (the J-40/J-41 serve-fast lifespan precedent) and/or paginate the timeline so the first `/data` render is bounded.
- Assert **byte-identity** of the served coverage block before/after the perf fix (no value drift).
- LIVE re-verify **J-94** (the universe-resolution diagnostic renders again) and **J-96** (the rising step function from ~2021-10-18 with populated Entries/Exits + the three honesty labels scrolled into the viewport and VIEWED — md5sum the dir first; reject any skeleton frame).
- Re-smoke the co-located `/data` journeys **J-36/J-37/J-39/J-85**, re-confirm **J-93** still slides on `/stocks` (the fast `/api/stocks` snapshot path, unaffected), and the CRITICAL **J-18/J-07**.
- Do **NOT** re-trigger `kind:"rebuild"` (~11 h, destructive; the data is correct).
- Gate any GOAL_ACHIEVED candidacy on the FLUSHED full-suite `0 failed, EXIT 0` line, nohup-async to the pump, never blocking the evaluator (iter-11/29/30 lesson).

After J-94 re-renders and J-96 flips to passing with COHERENCE-PASS and a GREEN suite, the next evaluation is a GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing).

## Halt Justification

**REGRESSION — the loop halts for human review.** J-94 (the per-date coverage diagnostic / `/data` page) was verified **passing** in iter-34 with the fully-rendered, evaluator-viewed `UT-J-94-universe-resolution.png` (admitted=544, excluded 1/2/1, thresholds 200/$10/50M, plus the timeline panel). In iter-35 the `/data` page can no longer hydrate: `GET /api/data` hangs >300 s (0 bytes) because `compute_coverage` (`data_manager.py:531`) always computes the J-96 `_membership_timeline` (`data_manager.py:469-528`), which loops all 1369 snapshot dates calling `universe_resolver.resolve_with_reasons()` per date (`:514`) with no result cache — cheap when each date resolved a trivial static-122 set, intractable now that each date resolves up to 544 members post-rebuild. Every `/data` frame (7 captured + a Playwright re-drive) is an un-hydrated skeleton (viewed `UT-J-96a-data-top.png`). A previously-green user journey's rendered surface is broken in the browser, which is precisely what the REGRESSION verdict exists to surface.

This is honestly **not** a data error (the J-96 data is DB-direct-correct), **not** an anti-goal violation (coherence COHERENCE-PASS, review PASS, source diff empty), and **not** a stall (a clear, tractable code fix exists). The fix is a read-path cache/precompute/pagination, not another ~11 h rebuild and not a resolver-math change — so after applying it the owner resumes with `--acknowledge-regression`. Recorded as open_item `iter35-api-data-timeline-uncached`. Note the silver lining: the rebuild genuinely **fixed J-93** (the iter-34 flat-122 gap is closed with real differential evidence) and broke nothing on the fast `/api/stocks` path.
