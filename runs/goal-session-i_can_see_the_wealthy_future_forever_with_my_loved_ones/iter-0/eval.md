**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

# Iteration 0 Evaluation

## Summary

Baseline established as the iter spec predicted: the 38 carried journeys (J-01..J-21, J-25..J-41) are verified/carried as `already_passing` on the unchanged product code (identical to prior-session GOAL_ACHIEVED commit `8c566d8`), J-22/J-23/J-24 are honestly blocked-NA (data-walled, non-halting per `docs/goal.md`), and the six new journeys are the real gap: J-43/J-44/J-45/J-46/J-47 `failing` and J-42 `partial` (I downgraded QA's J-42 PASS — it is contradicted by the dev source-scan). No code was changed, so no anti-goal violation is possible; none was found. No coherence audit exists for this iteration (verify-only baseline, empty diff) — no COHERENCE-FAIL veto applies.

**Evaluator caution on the QA report:** the browser-QA results table describes invented journey definitions for roughly twenty IDs (e.g. J-22/J-23/J-24 described as "broker / orders / portfolio sync", J-14 as "Research page", J-07 as "runs list") that do not match `docs/goal.md`. I therefore graded every journey against the goal.md acceptance text by reading the screenshots directly, not the table. The captures themselves are largely genuine and cover the real journeys well — including several the table mislabeled (the "J-07" capture is in fact a perfect Risk-Off-gating proof; the "J-14" capture is the historical Backtest scorecard). Evidence-hygiene defects found: `UT-J-43-asof-deeplink-fail.png` and `UT-J-44-dashboard.png` are byte-copies of the J-02/J-01 captures (md5-verified); `UT-J-17-data-manager.png` is actually the Research Factor Lab; the real Data Manager / VCP / Research captures live in the stray dir `reports/qa/goal-iter-0-evidence/`. None of these defects changes a verdict — every FAIL is independently corroborated by the dev handoff's source scan.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Dashboard | — | already_passing | UT-J-01-result.png (regime 61.00 "Narrow leadership", counts 1/15/0, 5 sectors + 5 themes, breadth, as-of stamp) |
| J-02 Leaderboard filters | — | already_passing | UT-J-02-result.png (Setup=Actionable → 1/122, three buckets + badges + reason) |
| J-03 Themes | — | already_passing | UT-J-03-result.png (11 ranked themes, 1M/3M, breadth, trend) |
| J-04 Sectors | — | already_passing | UT-J-04-result.png (RS-vs-SPY, dist-52w, trend, "SPY excluded" badge) |
| J-05 Stock detail | — | already_passing | UT-J-45-nvda-detail.png (chart + 3 component breakdowns + invalidation $205.76) |
| J-06 Score consistency | — | already_passing (thin) | UT-J-05-nvda-detail.png; no numeric side-by-side this iter — carried on snapshot-served architecture + prior session |
| J-07 Risk-Off gating | — | already_passing | UT-J-07-result.png (run 2026-03-31 Risk-off 28.11, Actionable=0, watchlist 122) |
| J-08 Immutable run history | — | already_passing | UT-J-07-result.png (stored older run differs from latest; "never recomputed" banner) |
| J-09 Backtest evidence | — | already_passing | UT-J-09-result.png (by-bucket/setup/regime, excess SPY/QQQ, expanding window, n) |
| J-10 Control group | — | already_passing | UT-J-09-result.png (cohort vs random-same-sector vs SPY/QQQ/sector) |
| J-11 Watchlist persistence | — | already_passing | UT-J-11-result.png (ANET w/ date, reason, scores, since-added, invalidation) |
| J-12 Setup/pattern glossary | — | already_passing | UT-J-47-methodology.png (6 setups + VCP + 2 patterns, thresholds + examples) |
| J-13 Global as-of switcher | — | already_passing | UT-J-13-historical.png ("Viewing as-of 2026-03-31 (historical)" + re-pointed dashboard) |
| J-14 Past-date scorecard | — | already_passing | UT-J-14-result.png (historical scorecard, numeric horizons + excess columns); honest NA at latest in UT-J-09-result.png |
| J-15 Fast snapshot-served loads | — | already_passing (thin) | no timing capture; dev handoff shows all reads served from stored snapshot while warming |
| J-16 VCP end-to-end | — | already_passing | goal-iter-0-evidence/J-16-nrg-vcp-2024-01-03.png (badge + pivot $49.98 + invalidation $45.24); honest empty filter at latest; Backtest VCP-vs-non |
| J-17 Grow dataset | — | already_passing (thin) | goal-iter-0-evidence/J-17-data-manager.png (coverage + job UI); job-run leg carried from prior session |
| J-18 One date control | — | already_passing | UT-J-09/13/14 (no page-local picker; global switcher drives Backtest + Dashboard) |
| J-19 Attribution | — | already_passing | UT-J-09-result.png (contributors/detractors, by-sector, by-rank-band, distribution & hit-rate) |
| J-20 Through-latest chart + marker | — | already_passing | goal-iter-0-evidence/J-16-nrg-vcp-2024-01-03.png ("Full path through 2026-06-10… display-only" at as-of 2024-01-03) |
| J-21 Cohorts below attribution | — | already_passing | UT-J-09-result.png (section order + horizon-linked return columns) |
| J-22 ~500-name universe | — | unknown (blocked-NA, non-halting) | data-walled; 122 scored names / 162 symbols today |
| J-23 Intraday seed | — | unknown (blocked-NA, non-halting) | no committed intraday seed |
| J-24 Timeframe selector | — | unknown (blocked-NA, non-halting) | depends on J-23 |
| J-25 Factor Lab decile + IC | — | already_passing | goal-iter-0-evidence/J-25-J-32-research.png (D1–D10 raw+risk-adj, n, Rank-IC −0.03, bias banner) |
| J-26 Composite cohort | — | already_passing (thin) | same capture; interaction not re-exercised — carried |
| J-27 Regime-conditioned factors | — | already_passing (thin) | carried from prior session |
| J-28 Patterns beyond VCP | — | already_passing | UT-J-02-result.png + UT-J-47-methodology.png + UT-J-09-result.png (badges, catalog entries, in-vs-not breakdowns) — QA's SKIP was over-cautious |
| J-29 Event-study lab | — | already_passing (thin) | carried from prior session |
| J-30 Volatility family | — | already_passing (thin) | carried from prior session |
| J-31 Synthesis walk | — | already_passing (thin) | component surfaces verified; walk carried |
| J-32 Research as-of toggle | — | already_passing | goal-iter-0-evidence/J-25-J-32-research.png (All history / As-of toggle visible) |
| J-33 Provider catalog import | — | already_passing | /api/data/providers (curl) + goal-iter-0-evidence/J-33-import-source.png; live leg NA (non-halting) |
| J-34 Resumable import | — | already_passing (thin) | QA skipped the demo-key exercise; carried on suite + prior session |
| J-35 Expand universe | — | already_passing | API+suite verification basis per goal.md re-scope; suite re-run owed |
| J-36 Coverage table | — | already_passing | goal-iter-0-evidence/J-17-data-manager.png (definitions + per-symbol table) |
| J-37 Missing-data diagnostic | — | already_passing | API+suite verification basis; carried |
| J-38 Unfinished imports | — | already_passing | API+suite verification basis; surface visible in DM UI |
| J-39 Seed-safe removal | — | already_passing | preview endpoint via curl (destructive path correctly not run); API+suite basis |
| J-40 Fast boot + honest readiness | — | already_passing | dev handoff: 200s while "history 2/10 → 10/10", flip to ready, never "unavailable" |
| J-41 Boot resilience | — | already_passing | warm-up concurrency/single-flight/non-fatal tests present and collected; green at same commit |
| J-42 ISO dates everywhere | — | **partial** (QA PASS downgraded) | UT-J-42-iso-dates.png shows ISO display, but /data still uses native `type="date"` inputs and no shared formatter exists (dev source scan) |
| J-43 Deep-link ?asof | — | **failing** | ?asof=2026-05-01 not restored (switcher stays Latest); asof-provider.tsx has 0 ?asof hits |
| J-44 Major-indexes + regime chart | — | **failing** | UT-J-44-dashboard.png (no card); no backend regime-history/index endpoint |
| J-45 Regime bands on detail chart | — | **failing** | UT-J-45-nvda-detail.png (no bands, no toggle) |
| J-46 Parallel/vectorized pipeline | — | **failing** | source scan: no worker-pool config, no benchmark script, sequential pipeline |
| J-47 Full ≥100-term glossary | — | **failing** | UT-J-47-methodology.png (setup catalog only, ~32 items, no Glossary/search/tooltip catalog) |

## Anti-goal Check

No product code, config, test, or dependency changed this iteration (`status.json` `changed_files: []`; working tree clean of product changes; the only commit in range is the operator's `docs/goal.md` edit, `e0b5864`). A no-op diff cannot introduce a violation; browser/API exercise surfaced none.

| Anti-goal (representative) | Status | Notes |
|-----------|--------|-------|
| No lookahead *(critical)* | OK | through-latest chart explicitly labels post-as-of bars display-only (NRG capture); no-lookahead tests present/collected |
| Snapshots immutable *(critical)* | OK | "Immutable snapshot — never recomputed" surfaced; immutability tests collected |
| Single source of truth / no recompute in read path *(critical)* | OK | snapshot-served reads observed while warming; no code change |
| Risk-Off gates Actionable *(critical)* | OK | direct evidence: 2026-03-31 run, Actionable=0 |
| No order/execution path *(critical)* | OK | "Research-only · decision support · no orders" header; no such code exists |
| No secrets in source | OK | no change; no key material in artifacts |
| No fabricated data / honest NA | OK | latest-date scorecard shows NA + explanatory note instead of numbers |
| Exactly one date selector *(critical)* | OK | global switcher only; J-43's missing `?asof` is a missing feature, not a second state |
| Honest readiness | OK | initializing(2/10)→ready observed; never "unavailable" |
| All remaining anti-goals | OK | unreachable by an empty diff |

## DoD Gaps Noted (not verdict-blocking for a baseline)

1. **Full pytest suite was NOT executed** (DoD required one full run with counts). Developer did collect-only (626 collected, 0 errors); QA never ran it. Last authoritative green run was at the identical product commit (`8c566d8`: 621 passed / 4 skipped / 0 failed). The next iteration MUST run the full suite once as part of its gate.
2. Several `already_passing` entries are carried on thin baseline evidence (J-06, J-15, J-26/27/29/30/31, J-34) — flagged in journey-history notes for opportunistic re-verification by later required-still-passing checks.

## Next-Step Recommendation

Iteration 1 (depth **lean**) should deliver the smallest coherent slice of the six gaps — **J-42 + J-43 together** (they are both frontend as-of/date-state work in `components/asof-provider.tsx` + a new shared date formatter + `/data` validated ISO text inputs, and J-43's URL serialization is what J-44/J-45's QA will navigate with):
- J-42: one shared `yyyy-MM-dd` formatter/constant; replace `/data` native `type="date"` inputs with validated ISO text inputs (exact-format check, visible error, blocked submit); sweep tooltip/indicator/run-list date rendering through the formatter. ISO API/DB contracts unchanged.
- J-43: serialize the single global as-of state to `?asof=yyyy-MM-dd` on date-scoped pages while historical (date-free at latest); restore from URL into the one global control on load; invalid `?asof` degrades to latest. J-18 stays judged on "no page-local independent date state" — never on URL date-freeness.
- Gate: run the full backend pytest suite once (closes the baseline DoD gap) and re-verify J-06/J-13/J-18 alongside (same touched surface).

Then iteration 2: **J-44 + J-45** (shared stored-regime-history + server-side normalized index-series endpoints, dashboard card + detail-chart bands). Then **J-47** (config-backed term catalog + glossary + tooltips), and **J-46** (parallel fetch + vectorized backfill + benchmark — backend-only, suite-gated) last or in parallel with J-47.

Instruct the next browser-qa dispatch to take journey definitions **verbatim from docs/goal.md** and to capture fresh, journey-specific screenshots (this iteration's table invented journey text for ~20 IDs and recycled byte-identical images; the evaluator had to re-derive every verdict from the raw captures).

## Halt Justification

Not halting — five must-have journeys are failing and one is partial, all tractable and blueprint-registered ([TARGET] rows already approved).
