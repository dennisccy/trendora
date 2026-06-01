# UI Test Results — goal-i_can_see_the_wealthy_future_forever-iter-0 (Baseline)

**Browser QA Verdict:** FAIL

<!-- FAIL is driven by two genuinely-unmet must-have journeys: J-17 (Data Manager — /data and /api/data
     both 404) and J-19 (return attribution — the four attribution layers do not appear on the rendered
     System Health or Backtest pages). 10 journeys PASS, 7 are PARTIAL (page + data confirmed; only an
     interaction step — filter/hover/date-switch/restart — could not be completed because the Chrome-MCP
     tool layer was under severe intermittent latency this run, so per agent rules they are PARTIAL, not
     FAIL). -->

**Iteration:** goal-i_can_see_the_wealthy_future_forever-iter-0 (baseline / verify-only)
**Overall:** 10 PASS · 7 PARTIAL · 2 FAIL  (of 19 must-have journeys)
**Frontend:** http://localhost:3835 — HTTP 200 all routes except `/data` (404)
**Backend:** http://localhost:8835 — `/api/health` ok, provider=seed, db_ok=true, 158 symbols, seed_latest_date=2026-05-28
**Test Date:** 2026-06-01
**Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-0-evidence/` (10 page screenshots UT-J-01…UT-J-17 + NVDA detail capture in session dir)

---

## Execution-environment note (for the evaluator)

The Chrome-MCP browser rendered **all 11 pages** (`001`…`011-navigate.{png,md,html}`), but the tool/exec
layer had **severe intermittent latency** (each action took minutes to flush), so multi-step
*interactions* (apply a filter and watch rows change, hover a tooltip, switch the global as-of date, add a
watchlist row + restart backend) could not be completed. Verdicts therefore combine **browser render**
(captured page markdown/screenshots) with **backend API ground truth** (the single source of truth — all
endpoints curl-verified). Journeys fully satisfied by render+API → PASS; journeys needing an
un-completed interaction → PARTIAL (none were observed to fail). The two FAILs are real product gaps, not
tool artifacts.

---

## Results table

| Test ID | Journey | Verdict | Evidence basis |
|---------|---------|---------|----------------|
| UT-J-01 | Daily dashboard at a glance | **PASS** | regime "Risk-on" 74.32 (6-label set) + components; counts A0/BO8/PB1/Ext11/Avoid102; breadth 65.57%/59.02%/NNH 9.02%; 5 top sectors+scores; 5 top themes+scores; asof 2026-05-28 |
| UT-J-02 | Stock Leaderboard + filters | PARTIAL | ranked rows render; sector/setup/**VCP** filter controls present in DOM (filter×4, select×9, vcp×18); per-row scores/bucket/setup/reason present in `/api/stocks`; filter *interaction* not executed |
| UT-J-03 | Theme Leaderboard | **PASS** | 9 themes ranked **non-increasing** (Semiconductors A100→Homebuilders E20.5); top theme: members[], 1m +28.38%, 3m +61.22%, breadth 100% (universe-relative), trend "Strong uptrend" |
| UT-J-04 | Sector/industry Leaderboard | **PASS** | ranked by score; top row SOXX rs_vs_spy 45.49, dist_from_52w_high −0.11%, trend "Strong uptrend"; SPY is the benchmark (not ranked as a leader) |
| UT-J-05 | Stock Detail (explainable) | **PASS** | `/stocks/NVDA` rendered (heading "NVDA"); `/api/stocks/NVDA`: Leadership 47.48 (E, 7 components), Entry 66.24 (D, 5), Risk 33.79 (E, 8), setup "Avoid" + reason — each score has ≥3 named components + bucket. (Chart/invalidation visual rendered but not text-re-verified) |
| UT-J-06 | Score consistency across pages | PARTIAL | snapshot-served single source; `/api/stocks` and `/api/stocks/NVDA` serve the same canonical values for asof 2026-05-28; explicit leaderboard-vs-detail *visual* compare not completed |
| UT-J-07 | Risk-Off suppresses Actionable | **PASS** | run **2025-04-04 = Risk-off (score 6.30)** shows **Actionable 0** and 122 Risk-off-watchlist (gate forces watchlist-only) — confirmed in run list + `/api/runs` |
| UT-J-08 | Immutable run history | **PASS** | 11 dated immutable runs; older (2026-02-27 Narrow-leadership, Actionable 1) differs from latest (2026-05-28 Risk-on, Actionable 0); distinct per-date snapshots |
| UT-J-09 | System Health evidence | **PASS** | by-bucket A–E 20d (A +6.00% n=24 … E +2.05% n=772); excess vs SPY +2.03% / QQQ +2.03%; by-setup + by-regime tables; every cell shows n (⚠ <30); survivorship-bias labelled |
| UT-J-10 | Control-group honesty | **PASS** | control group: top-ranked +3.02% n=200, random same-sector +1.52% n=285, SPY +1.52%, QQQ +1.99%, sector-ETF +1.43% — all numeric+labelled |
| UT-J-11 | Watchlist persistence | PARTIAL | `/watchlist` renders add-form (form+3 inputs) + empty-state copy citing date-added/reason/scores/price-since/invalidation/persist-across-restart; add + backend-restart *not executed* |
| UT-J-12 | Glossary + inline | **PASS** | `/methodology` lists all 6 setups + VCP, each with meaning + config thresholds + worked example; `/api/methodology` config-backed. (Inline badge tooltip not separately hovered) |
| UT-J-13 | Global as-of switcher | PARTIAL | as-of switcher present in top bar across pages (asof markers on every page); past-date *selection* interaction not executed |
| UT-J-14 | Backtest scorecard (NA honesty) | **PASS** | `/backtest` shows as-of cohort + scorecard scaffold (1/5/10/20/60d, cohort, vs-SPY, control); latest date **honestly shows NA n=0**: "no post-snapshot bars… every horizon NA… No numbers are fabricated". (Numeric scorecard for an older date not switched-to in-browser; structure confirmed via `/api/backtest`) |
| UT-J-15 | Fast loads from snapshots | PARTIAL | pages served from persisted snapshots and render; sub-1.5s budget not measurable under the degraded tool layer |
| UT-J-16 | VCP detected/filterable/FT | PARTIAL | **glossary VCP entry ✓** + **System-Health VCP-vs-non-VCP ✓** (VCP +3.18% n=27, non-VCP +2.01% n=1191); VCP filter control present in DOM; applying the filter + per-row badge/detail *not executed* |
| UT-J-17 | Data Manager (grow dataset) | **FAIL** | `/data` → **404** and `/api/data` → **404**; surface absent (matches decomposer file-scan) |
| UT-J-18 | One date control (no dup) | PARTIAL | backtest reads the resolved as-of date; rendered page shows no separate date dropdown in content, but "exactly one control" could not be proven via date-switch interaction |
| UT-J-19 | Attribution slices | **FAIL** | the four attribution layers (per-stock contributors/detractors, by-sector, by-rank-band, distribution/hit-rate) **do not appear** on the rendered System Health or Backtest pages, nor in the `/api/system-health` payload (which has by_bucket/by_setup/by_regime/by_vcp/excess/control_group only). Consistent with the decomposer's J-19 caution |

---

## FAIL details

### UT-J-17 — Data Manager — **FAIL**
`/data` browser nav returns "404: This page could not be found." (heading "404"); `/api/data` → 404. The
Data Manager page + API + engine are absent. Genuine unmet must-have journey.

### UT-J-19 — Return attribution — **FAIL**
J-19 requires four attribution layers on System Health (aggregate) and Backtest (per-date): (a) per-stock
top contributors & detractors, (b) by-sector, (c) by-rank-band (1–10/11–50/51+), (d) distribution &
hit-rate (median/% positive/dispersion). The fully-captured System Health page renders by-bucket, excess,
by-setup, by-regime, VCP-vs-non-VCP and control-group — **but none of the four attribution layers**. The
Backtest page renders the as-of summary + horizon scorecard — **but no attribution**. `/api/system-health`
exposes no attribution keys. So the attribution journey is not surfaced. (If an attribution endpoint
exists below the captured truncation it is at minimum not wired into the UI, which fails the journey.)

---

## PASS highlights worth noting for coherence
- **Single-source/no-recompute** looks healthy: dashboard regime/counts, leaderboard, themes, sectors,
  runs and system-health all read consistent canonical values for asof 2026-05-28.
- **Risk-off gating (anti-goal, critical) holds**: the seeded 2025-04-04 Risk-off run has 0 Actionable.
- **Honest forward-test (anti-goal)**: Backtest shows NA/n=0 for the un-elapsed latest date and states
  nothing is fabricated; System Health marks low-sample cells with n and ⚠ and labels survivorship bias.
- **Config-driven vocabulary (anti-goal)**: Methodology renders all setups + VCP with config thresholds.

---

## Recommendation (next iterations)
1. **J-17** — build the Data Manager (`/data` page + `/api/data` + engine + config section).
2. **J-19** — add the four attribution layers to System Health (aggregate) and Backtest (per-date),
   derived from stored per-observation forward returns (read-only, no recompute).
3. **Re-run browser QA on a healthy tool layer** to convert the 7 PARTIALs — the data contract is already
   present for all of them; only the interaction proofs are outstanding (J-02 filters change rows, J-06
   leaderboard==detail, J-11 add+restart, J-13 as-of re-points pages, J-15 <1.5s, J-16 VCP filter+badge,
   J-18 backtest has no local date picker).

---

## Environment
- **Frontend:** http://localhost:3835 (Next.js dev) — all routes 200 except `/data` (404)
- **Backend:** http://localhost:8835 — provider=seed, 158 symbols, asof 2026-05-28, 11 immutable runs
- **Browser:** Chrome via MCP — 11 pages rendered; captures in `…/session-1780269244530/00N-navigate.{png,md,html}`
- **Test Date:** 2026-06-01
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-0-evidence/`

---

**Browser QA Verdict:** FAIL
