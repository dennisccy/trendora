# Iteration 13 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-30 (volatility as a first-class Factor-Lab family) landed cleanly and is **newly passing**: three NEW
stored volatility factor values (`hv`, `vcp_contraction`, `downside_vol`) are computed once in the
scoring/snapshot path from as-of bars (≤ D, no lookahead), stored as append-only `ScannerResult`
columns, and read verbatim by the existing read-only Factor Lab — so all four volatility measures
(ATR%, HV, VCP-style contraction, downside/semivol) render a populated decile table (raw mean +
downside-risk-adjusted + n), a numeric rank-IC, and the by-regime split with honest NA. The single
biggest risk — a volatility value leaking into a weighted score and shifting J-06/J-07 — did **not**
materialize: the critical post-DB-regen gates hold (Risk-Off → Actionable=0; NVDA scores byte-identical
across leaderboard↔detail), proven both in source (score-invariance keystone + no-weight-leak) and live
against the regenerated DB. Coherence is PASS. Not GOAL_ACHIEVED — 5 journeys remain failing
(J-22/J-23/J-24 externally Yahoo-429 data-walled; J-29/J-31 unbuilt).

## Journey Results This Iteration

26/31 passing (J-30 newly passing). 5 failing (J-22, J-23, J-24, J-29, J-31).

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| **J-30** (TARGET) | failing | **passing** | `UT-03-hv-selected.png`, `UT-04-vcp-decile.png`, `UT-05-downside-regime-NA.png`, `UT-06-vcp-regime-split.png`, `TC-09-{atr_pct,hv,vcp_contraction,downside_vol}.png` + live-API cross-check (rank-IC hv +0.028 / vcp_contraction −0.015 / downside_vol +0.116; n=1217 excludes 1 NULL; 422 on unknown) |
| **J-07** (CRITICAL re-verify after regen) | passing | passing | `UT-10-riskoff-actionable-zero.png` + API: both Risk-Off runs Actionable=0 (all 122 → Risk-off-watchlist) |
| **J-06** (CRITICAL re-verify after regen) | passing | passing | `UT-11-12-nvda-detail.png`, `UT-11-leaderboard-top.png` + API nested: `/row/{leadership 47.48 E, entry_quality 66.24 D, risk 33.79 E}` == leaderboard |
| J-05 | passing | passing (re-verified) | `UT-11-12-nvda-detail.png` — chart + 3 score component breakdowns render |
| J-25 | passing | passing (re-verified) | `UT-09-atr-reselected.png` — decile + rank-IC re-point on factor change (ATR% −0.01 → HV +0.03 → downside +0.12 → ATR% −0.01) |
| J-27 | passing | passing (re-verified) | `UT-06-vcp-regime-split.png` — 7-col by-regime table renders, populated numeric + empty-regime NA |
| J-18 | passing | passing (re-verified) | `UT-08-asof-historical-lab-unchanged.png` — as-of toggle leaves lab byte-identical, zero as_of requests |
| J-02 | passing | passing (surface re-rendered) | `UT-10`/`UT-11-leaderboard-top.png` — ranked bucketed rows + setup status + filter controls render |
| J-12 | passing | passing (carried) | `/methodology` catalog + inline badge path untouched; NVDA detail shows setup badge |
| J-09, J-19 | passing | passing (carried) | `forward_testing.py` (attribution + by-bucket/setup/regime aggregates) UNCHANGED in diff |
| J-16, J-28 | passing | passing (carried) | `patterns.py`/`detect_vcp`/scoring pattern path untouched; `vcp_contraction` FACTOR is distinct from the VCP pattern flag |
| J-08 | passing | passing (carried) | scanner write-path is append-only (3 new typed columns); lab is SELECT-only |
| J-01, J-03, J-04, J-10, J-11, J-13, J-14, J-15, J-17, J-20, J-21 | passing | passing (carried) | their paths (dashboard/themes/sectors/control-group/watchlist/as-of/backtest/prices/data) untouched by the additive diff |
| J-22 | failing | failing | externally Yahoo-429 data-walled — do NOT autonomously retry |
| J-23, J-24 | failing | failing | unbuilt + data-walled (intraday Yahoo fetch) |
| J-29 | failing | failing | unbuilt — next target (needs MAE/MFE excursion path) |
| J-31 | failing | failing | unbuilt — synthesis, requires J-29 |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead (critical) | OK | `hv`/`vcp_contraction`/`downside_vol` computed from `inv_closes = closes(bars_asof(...,asof))` (scoring.py:325,353-357) — the same ≤ D series used for invalidation/VCP; no future bar touched |
| Single source of truth / no recompute (critical) | OK | None of the 3 keys in any `config.scores.*.weights` (yaml-verified: leadership 7 / entry_quality 5 / risk 8, LEAK=none); appended to row dict AFTER `_build_score`; keystone `test_volatility_values_ride_the_row_but_enter_no_score` forces a constant → scores/buckets/setup/rank byte-identical; NVDA byte-identical list↔detail live |
| Research lab is read-only & not predictive | OK | `research.py` diff is docstring-only; imports only `SURVIVORSHIP_BIAS_LABEL` (a constant) + models; forbidden-call grep hits only docstrings (lines 15, 406); reads stored column via `getattr`; descriptive caveat visible |
| Risk-adjusted is downside-only | OK | risk-adjusted column = mean ÷ downside deviation; signed (UT-05 shows D4 −0.06, D7 +0.93); never total volatility; downside-undefined → NA |
| No magic numbers | OK | 4 windows + 3 factor labels live in `config.yaml`; `test_no_magic_numbers` green (only structural literals 0/1/2/100 in new math) |
| No fabricated data | OK | NULL volatility obs excluded honestly (n drops 1218→1217); empty regimes show NA + n=0, never a fabricated 0 |
| Risk-Off gates Actionable (critical) | OK | both seeded Risk-Off runs Actionable=0 after regen (API + UT-10) |
| Snapshots immutable (critical) | OK | scanner write-path append-only (3 typed columns); lab SELECT-only; no run/result row mutated |
| Honest limitations surfaced | OK | survivorship-bias + universe-relative caveat banner visible (UT-07) |
| Exactly one date selector | OK | no new date/as-of state on `/research`; UT-08 toggle leaves lab byte-identical (RESOLVED since iter-1, still holding) |
| VCP is a pattern, not a status (critical) | OK | `vcp_contraction` is a continuous FACTOR, distinct from `detect_vcp`/`is_vcp` (untouched); never enters the setup enum or any score |

No anti-goal violation introduced. The single historical minor one (Exactly one date selector) stays RESOLVED.

## Next-Step Recommendation

**Next iteration: full depth, target J-29 (Setup & Pattern research lab — event study across all
snapshots).** This is the last large autonomous lift before the J-31 synthesis. It requires extracting
and storing the **post-snapshot daily high/low excursion path (MAE/MFE)** first — the larger lift prior
evaluators flagged — then pooling every historical occurrence of a setup/pattern to report the
forward-return distribution, hit-rate, **expectancy**, **MAE/MFE**, best exit-horizon, and regime/sector
slices, plus the `return/MAE` risk-adjusted ratio that J-30 deferred. The "Setup & Pattern Lab" lives on
the **already-approved `/research` home** per the goal's IA (no nav re-approval), but the decomposer
should determine up front whether MAE/MFE needs a new stored excursion path on the snapshot (likely —
forward_testing currently stores realized returns, not daily-high/low excursions) and keep the read-only
seam intact (derive once from stored data; the API/view recomputes nothing). Full depth: new backend
excursion computation/storage + new lab analytics + new `/research` surface on the critical read-only
research path. After J-29, **J-31 (synthesis)** becomes buildable (needs J-25/J-26/J-27/J-29 + the
leaderboard→detail travel).

**Strategic:** GOAL_ACHIEVED is NOT autonomously reachable while J-22/J-23/J-24 stay externally
Yahoo-429 data-walled. After J-29 → J-31, expect either operator confirmation of a reachable no-key
egress (J-22 auto-heals via its committed finish runbook) or a correct STALLED on the data-walled
remainder. **Do NOT autonomously retry J-22/J-23/J-24.**

## Process Notes

- As predicted by the iter-13 spec (and the iters 3/6/9/10/11/12 pattern), **no `-audit.md`** handoff was
  produced; `status.json` exists at the **phase-namespace** path
  `runs/goal-i_can_see_the_wealthy_future_forever-iter-13/status.json` (status:complete,
  current_step:qa_complete, browser_checks_run:true, changed_files == the 15-file diff), NOT under
  `runs/goal-session-.../iter-13/` (which holds only `coherence.md` + this `eval.md`). I substituted
  source-level verification of every critical seam + independent live-API cross-checks. No verdict impact.
- Diff is purely additive (15 app/config files, +398/−11) — `forward_testing.py`, `patterns.py`,
  `regime.py`, `api/`, `prices.py`, `backtest/page.tsx`, the as-of provider, watchlist, and the `/stocks`
  UI are all untouched, so the carried-passing journeys cannot have regressed.
- Evidence hygiene: 18 PNGs, 17 distinct sha256. The single collision (`TC-15-nvda-leaderboard.png` ==
  `UT-11-leaderboard-top.png`) is cross-agent corroboration of the SAME deterministic leaderboard render
  (qa's TC vs browser-qa's UT), not the iter-3/6 same-agent duplicate-shot bug.
- Honest descriptive finding (not a defect): `vcp_contraction`'s rank-IC ≈ −0.015 (essentially flat) — the
  continuous contraction measure shows no meaningful forward-return edge in this seed. Per J-30's
  acceptance ("rather than assuming the textbook relationship"), reporting a near-zero/contrary direction
  honestly is a PASS, not a failure.
