# Iteration 40 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-40
**Date:** 2026-07-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| **Per-stock risk-budget components** (ATR%, downside vol, overnight-gap profile median/p95/worst + overnight variance share, worst-20d window, distance-to-invalidation %) — NEW value, pre-registered in blueprint.md's Data Contract this iteration | OK | Computed once: `apps/backend/app/engine/scoring.py:418` (`overnight_gap_profile`), `:425` (`worst_20d_window`), `:429` (`_pct_from_ma` reframe), `:431-440` (assembled dict), using genuinely new pure functions `apps/backend/app/engine/indicators.py:235` / `:286` — no pre-existing function with this name/math exists elsewhere (`grep -rn "def overnight_gap_profile\|def worst_20d_window"` returns exactly one hit each). Served: `apps/backend/app/api/stocks.py:59` (`GET /stocks`) and `:64` (`GET /stocks/{ticker}`), both delegating to `apps/backend/app/engine/snapshot_serving.py:204` / `:244`, which rehydrate the SAME `record_json` blob (`:176`, `:238`) — no second endpoint, no strict schema that would drop the field. |
| ATR% (existing contract value, part of the Risk score's components) | OK — reused, not recomputed | `scoring.py:432` reuses `raws["atr_pct"]` (pass-1's already-computed value); test `apps/backend/tests/test_scoring.py:557-589` (`test_risk_budget_atr_and_downside_vol_are_reused_not_recomputed`) asserts `ind.atr_pct` fires exactly once per member. |
| Downside volatility (existing contract value) | OK — reused, not recomputed | `scoring.py:433` reuses the pre-existing local `downside_vol` variable (unchanged context line in the diff, computed earlier in the same pass-3 block) — no second `ind.downside_vol` call; same test as above confirms call count. |
| Invalidation level (existing contract value) | OK — reused, not recomputed | `scoring.py:429` reads `invalidation["price"]`/`invalidation["level"]` (already built earlier in pass-3) through the existing `_pct_from_ma` helper — only reframed as a percent, the level itself is not recomputed. |
| Leadership / Entry Quality / Risk scores (existing contract value) | OK — untouched | `risk_budget` enters no weight; percentile pass `scoring.py:471-478` operates on `rows` after scores are already assigned, and is disjoint from `_build_score`. `test_scoring.py` (`test_risk_budget_values_ride_the_row_but_enter_no_score`) forces the two new indicator functions to an absurd constant and asserts every row's scores/buckets/setup/rank stay byte-identical to baseline. |

No new UI surface fetches any of the above from a non-canonical endpoint, and no client-side recomputation exists: `apps/frontend/lib/risk-budget.ts:15,23,31` (`fmtRiskValue`, `fmtRiskPercentile`, `isRiskBudgetNa`) only round/append units on server-supplied numbers — re-format, not re-derive — which the skill explicitly permits.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `RiskBudgetCard` on `/stocks/{ticker}` | OK | Additive section on the EXISTING Stock Detail route (`apps/frontend/app/stocks/[ticker]/page.tsx:198,324`), which the blueprint's IA homes table already lists as J-24's canonical home. `git diff --stat` against snapshot `b8b9dd4f2f90db1b63730b7937126a0b211d9fdd` for `sidebar*`/`nav*`/`layout.tsx` is empty — no nav file touched, consistent with "no new page, no nav change." |
| `RISK_BUDGET_COLUMNS` on `/stocks` leaderboard | OK | Additive columns on the EXISTING leaderboard route (`apps/frontend/app/stocks/page.tsx:80-92,709,987`), the other half of J-24's IA home. Same no-nav-file-touched evidence applies. |

No new route was created (`git status` shows zero new files under `apps/frontend/app/`), no duplicate home for an existing entity, and no parallel shell — both surfaces reuse the page's existing `Card`/table structure.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Minor label-wording variance across the two surfaces for the same values.** The detail-card tiles read "ATR %", "Downside volatility", "Distance to invalidation" (`apps/frontend/app/stocks/[ticker]/page.tsx:328-335`) while the leaderboard column headers read "ATR%", "Downside vol", "Dist. to invalidation" (`apps/frontend/app/stocks/page.tsx:84-92`). This is the expected full-label-vs-narrow-column abbreviation pattern already established by this same page's "High proximity" column, and both surfaces link to the identical `config.methodology` glossary term string (e.g. `"downside volatility (semivol)"`), so there is no ambiguity about which concept each label names. No action required; noted only for completeness.
- **Adjacent naming, not a duplicate.** The new "Risk budget" card sits on the same detail page as the existing weighted "Risk" score and both use the word "Risk," even though they are fully independent values (risk-budget enters no weighted score — see Data Contract check above). The card's own copy ("Descriptive only; not a recommendation.") and distinct "Risk budget" title already disambiguate this in the UI; flagging only as a forward-looking note in case a future copy pass wants an even more distinct name.

## Basis for this audit

- Blueprint: `runs/goal-session-mcp-loop/state/blueprint.md` (IA homes table row "J-24", Data Contract row "Per-stock risk-budget components," and the "iter-40 clarification" paragraph — all three already present, registered ahead of/alongside this iteration's dev work).
- Iteration spec: `docs/phases/goal-mcp-loop-iter-40.md` ("Data-contract additions" / "Blueprint conformance" sections — both claim zero new surfaces/endpoints; confirmed against the diff).
- Diff: `runs/goal-session-mcp-loop/iter-40/iter-diff.md` did not exist for this iteration, so this audit used `git diff b8b9dd4f2f90db1b63730b7937126a0b211d9fdd -- . <exclusions>` (1028 lines) plus the untracked new file `apps/frontend/lib/risk-budget.ts` (not visible to `git diff` since it was never staged/tracked at the snapshot SHA — read directly). The stat of excluded paths showed only `runs/*`/`reports/*` harness churn and one line-count change to `runs/goal-session-mcp-loop/state/blueprint.md` (+4, 0 deletions — consistent with a pure append of the new IA row + Data Contract row + clarification paragraph, not a rewrite of any existing row); no lockfiles changed.
- UI surface map: `reports/phase-goal-mcp-loop-iter-40-ui-surface-map.md` (cross-checked against the diff; consistent).
- Corroborating greps run directly against the working tree: no second `overnight_gap_profile`/`worst_20d_window`/`atr_pct`/`downside_vol` definition anywhere in `apps/backend/app/engine/*.py`; no `risk_budget`/`RiskBudget` reference outside the files listed above; no sidebar/nav/layout diff.
