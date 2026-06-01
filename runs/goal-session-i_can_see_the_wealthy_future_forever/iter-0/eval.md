# Iteration 0 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The verify-only baseline executed correctly as an intentional zero-diff no-op (review PASS; `git diff HEAD` empty; backend boots offline on the seed, frontend builds, 248/0 unit suite green). Browser QA exercised all 19 must-have journeys: **10 verified passing**, **6 partial** (data contract + page render confirmed, but interaction proofs were blocked by a severely degraded Chrome-MCP tool layer — none observed failing), and **3 genuinely failing** (J-17, J-18, J-19). This is iteration 0, so nothing can regress and no anti-goal was *introduced* — the baseline simply records the true starting state and three concrete gaps for later iterations.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Daily dashboard | (none) | **already_passing** | UT-J-01-dashboard.png — Risk-on 74.32 + 5-component breakdown; counts A0/BO8/PB1; 5 top sectors + 5 top themes w/ A–E; breadth 65.57% "universe-relative"; as-of 2026-05-28 |
| J-02 Leaderboard + filters | (none) | partial | UT-J-02-J15-J16-stocks.png — ranked rows + sector/setup/VCP filter controls in DOM; per-row scores/bucket/setup/reason in /api/stocks; filter *interaction* not executed |
| J-03 Theme Leaderboard | (none) | **already_passing** | UT-J-03-themes.png — 11 themes ranked non-increasing (Semis A100 → Nuclear E3); top theme 1m +28.38%/3m +61.22%/breadth 100%/Strong uptrend |
| J-04 Sector Leaderboard | (none) | **already_passing** | UT-J-04-sectors.png — ranked by score; SOXX rs_vs_spy 45.49, dist −0.11%, trend; SPY as benchmark not ranked |
| J-05 Stock Detail (explainable) | (none) | **already_passing** | UT-J-05-J06-stock-detail-NVDA.png — price+MA+volume chart (1356 bars); themes chips; "Invalid below 50-DMA at $198.73"; setup Avoid + reason; VCP block; 3 scores w/ components via API |
| J-06 Score consistency | (none) | partial | UT-J-05-J06-stock-detail-NVDA.png — /api/stocks ↔ /api/stocks/NVDA serve identical canonical values; visual leaderboard-vs-detail compare not completed |
| J-07 Risk-Off gates Actionable *(critical)* | (none) | **already_passing** | UT-J-07-J08-scanner-runs.png — 2025-04-04 Risk-off (6.30) → **Actionable 0**; 2022-10-07 Risk-off (8.34) → **0**; gate holds |
| J-08 Immutable run history | (none) | **already_passing** | UT-J-07-J08-scanner-runs.png — 11 distinct dated runs; older runs differ from latest |
| J-09 System Health evidence | (none) | **already_passing** | UT-J-09-J10-J19-system-health.png — by-bucket A–E (+6.00% n=24 … +2.05% n=772), excess vs SPY/QQQ, by-setup, by-regime, all w/ n + survivorship banner |
| J-10 Control-group honesty | (none) | **already_passing** | UT-J-09-J10-J19-system-health.png — top-ranked +3.02% n=200 vs random same-sector +1.52% n=285 vs SPY/QQQ/sector ETF (API-confirmed) |
| J-11 Watchlist persistence | (none) | partial | UT-J-11-watchlist.png — add-form + empty-state citing date/reason/scores/price-since/invalidation/persist; add + backend-restart *not executed* |
| J-12 Glossary + inline | (none) | **already_passing** | UT-J-12-methodology.png — all 6 setups + VCP w/ meaning + config thresholds + worked example; config-backed |
| J-13 Global as-of switcher | (none) | partial | UT-J-01-dashboard.png — switcher present in top bar across all pages; past-date *selection* interaction not executed |
| J-14 Backtest scorecard (NA honesty) | (none) | **already_passing** | UT-J-14-J18-backtest.png — as-of cohort + 1/5/10/20/60d scorecard scaffold; latest date honestly shows NA n=0, "Nothing is fabricated" |
| J-15 Fast loads from snapshots | (none) | partial | UT-J-02-J15-J16-stocks.png — snapshot-served renders; sub-1.5s budget not measurable under degraded tool |
| J-16 VCP detected/filterable/FT | (none) | partial | UT-J-02-J15-J16-stocks.png + system-health — glossary VCP ✓, SH VCP-vs-non-VCP ✓ (VCP +3.18% n=27), filter control in DOM; filter+badge interaction not executed |
| J-17 Data Manager (grow dataset) | (none) | **failing** | UT-J-17-data-404.png — `/data` and `/api/data` both **404**; page/router/engine/config all absent |
| J-18 One date control (no duplicate) | (none) | **failing** | UT-J-14-J18-backtest.png + backtest/page.tsx:53-58,112-118,175-208 — Backtest keeps its OWN date state + `BacktestDatePicker`; never reads the global control |
| J-19 Attribution slices | (none) | **failing** | UT-J-09-J10-J19-system-health.png — none of the 4 attribution layers (per-stock contributors/detractors, by-sector, by-rank-band, distribution/hit-rate) appear on System Health or Backtest, nor in /api/system-health |

**Correction to browser-QA:** QA marked J-18 PARTIAL ("rendered page shows no separate date dropdown"). That is wrong — `apps/frontend/app/backtest/page.tsx` carries an explicit page-local `BacktestDatePicker` (its own `selected` date state, line 53 comment "The page's OWN date picker (independent of the global top-bar switcher)") and the evidence screenshot shows a visible "AS-OF DATE" dropdown. The degraded tool layer caused the miss. J-18 is **failing**.

## Anti-goal Check

No code changed this iteration (verify-only no-op), so no anti-goal could be *introduced*. Critical anti-goals were independently corroborated as healthy:

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead *(critical)* | OK | `test_scanner::test_run_scan_no_lookahead`, `test_scoring::test_asof_bounds_..._no_lookahead` green (248/0 suite) |
| Snapshots immutable *(critical)* | OK | `test_scanner::test_run_scan_idempotent_and_immutable`, `..._distinct_as_of_snapshots` green; 11 distinct dated runs visible |
| Single source of truth *(critical)* | OK | Dashboard/leaderboard/themes/sectors/runs/SH read consistent canonical values for as-of 2026-05-28 |
| Risk-Off gates Actionable *(critical)* | OK | Verified directly: both seeded Risk-off runs show 0 Actionable (J-07) |
| No fabricated data | OK | Backtest shows NA/n=0 for un-elapsed latest date and states nothing is fabricated; SH marks n<30 ⚠ |
| Honest limitations surfaced | OK | Breadth labelled "universe-relative"; survivorship-bias banner on SH + Backtest |
| No order/execution path *(critical)* | OK | Research-only; no brokerage surfaces; "no orders" banner |
| No secrets in source | OK | Boots on seed provider, no keys/network |
| VCP is a pattern, not a status *(critical)* | OK | `test_scoring::test_vcp_is_a_pattern_not_a_status` green; NVDA detail shows VCP block separate from setup |
| **Exactly one date selector** *(extends SSoT)* | **VIOLATED (pre-existing, minor)** | Backtest maintains a 2nd independent date state + own picker (root cause of J-18). Not introduced this iter; tracked in journey-history `anti_goal_violations` (resolved:false) — fix as part of J-18 |

No coherence audit ran (`iter-0/coherence.md` absent) — expected for a zero-diff baseline with nothing to audit; therefore **no COHERENCE-FAIL** and no structural veto.

## Next-Step Recommendation

Three genuine gaps remain; recommend the next iteration run at **full** depth (these are multi-surface features touching the data contract + information architecture, warranting audit / ux-regression / closure). Suggested sequencing:

1. **J-18 — consolidate to one date control** (smallest, coherence/anti-goal fix): make `/backtest` consume the global `asof-provider`/`asof-switcher`; delete the page-local `BacktestDatePicker` and its independent date state so "which date am I viewing" has a single source. Clears the live "Exactly one date selector" anti-goal violation.
2. **J-19 — return attribution** on `/system-health` (aggregate) and `/backtest` (per-date): per-stock top contributors & detractors, by-sector, by-rank-band (1–10/11–50/51+), and distribution/hit-rate — **derived once from the stored per-observation forward returns** (read-only; no recompute in API or view, per the "Attribution is read-only" anti-goal), each with sample size n and honest NA below min-sample.
3. **J-17 — Data Manager** (largest net-new surface): `/data` page + `/api/data` router + data-manager engine module + a `data`/`data_manager` `config.yaml` section; an async background job with live progress (real-data-only live fetch; explicit error on provider failure, no fabricated prices) that auto-generates immutable, lookahead-free snapshots + forward returns for new dates.

Also: **re-run browser QA on a healthy tool layer** to convert the 6 partials (J-02 filters change rows, J-06 leaderboard==detail, J-11 add+restart, J-13 as-of re-points pages, J-15 <1.5s warm load, J-16 VCP filter+badge) — the data contract is already present for all of them; only the interaction proofs are outstanding.

## Halt Justification (if halting)

N/A — not halting. CONTINUE: the baseline established a verified starting state; 3 must-have journeys (J-17, J-18, J-19) are failing and tractable, and 6 partials need interaction re-verification. Not GOAL_ACHIEVED (failing journeys exist). Not REGRESSION (iter 0 — no prior passing state; no critical anti-goal introduced). Not STALLED (clear, specific next work identified).
