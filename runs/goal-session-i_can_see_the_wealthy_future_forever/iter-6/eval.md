# Iteration 6 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

Iter-6 opens the new wave (J-20…J-31) with its two lowest-risk members, and both land cleanly: **J-20** (Stock-Detail chart full path through latest, display-only, with an as-of divider + labelled forward region) and **J-21** (Backtest leadership cohorts relocated below Return Attribution, each carrying a horizon-linked realized-return column driven by the single lifted horizon view-selector). Both critical anti-goal seams hold **in source** (no-lookahead: the chart's `bars_through_latest` is never referenced by scoring/scanner/patterns; read-only: `_leadership_returns` takes no Session, runs no query, recomputes no return — pure projection of the stored `forward_returns` the scorecard already read), and no required-still-passing journey regressed. This is **not** GOAL_ACHIEVED — J-22…J-31 (10 of 31 must-haves) are confirmed unbuilt — so the loop continues onto the heavier wave members.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-20 (target) | failing (unbuilt, wave) | **passing** | UT-02-UT-03-chart-divider-zoom.png (historical: through-latest + divider + "Forward (display only)" legend + caption + ≤D invalidation $121.27); UT-07-latest-no-forward.png (latest: no forward, $198.73); source: `bars_through_latest` not in scoring path |
| J-21 (target) | failing (unbuilt, wave) | **passing** | UT-10-11-12-leadership-returns-h1.png + UT-14-leadership-returns-h60.png (one selector re-points attribution + all 3 lists at fixed as-of 2025-04-04); UT-08 section order; UT-15 honest NA; source: `_leadership_returns` no Session/query/recompute |
| J-05 (req) | passing | passing | UT-01-latest-nvda.png / UT-06 (scores 47.48/66.24/33.79 + components render; detail reads `fetchStock`) |
| J-06 (req) | passing | passing | UT-06 (displayed @2025-04-04 = `GET /api/stocks/NVDA?as_of=2025-04-04` byte-equal; chart change is display-only) |
| J-13 (req) | passing | passing | exercised by every J-20/J-21 test via the global as-of switcher + in-app nav |
| J-14 (req) | passing | passing | UT-08-UT-09 (Forward-test scorecard section present + as-of summary) |
| J-15 (req) | passing | passing | carried — no recompute introduced (read-only projection); snapshot-serving path untouched (additive diff, COHERENCE-PASS) |
| J-16 (req) | passing | passing | UT-01/UT-06 ("No VCP pattern detected" renders; VCP path untouched — `detect_vcp` never sees `bars_through_latest`) |
| J-18 (req) | passing | passing | UT-17 + source: lifted `viewHorizon` is a VIEW selector (no refetch/date param/date state); 0 date inputs, one global `<select>`; old `BacktestAttributionSection` deleted |
| J-19 (req) | passing | passing | UT-14 (Return Attribution by-sector re-points on the same horizon selector; `_attribution_slices` untouched) |
| J-01,02,03,04,07,08,09,10,11,12,17 | passing | passing (spot-check) | UT-18 / TC-18 — all pages render at Latest, in-app nav preserves as-of, no error boundary; additive diff cannot reach them |
| J-22…J-31 | (new this wave) | **failing (unbuilt)** | confirmed out of scope: `/research` absent (J-25–J-31), 158-symbol universe not ~500 (J-22), no intraday/timeframe in `prices.py` (J-23/J-24), only VCP detector (J-28) |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead (critical) | OK | `bars_through_latest` referenced only by `prices.py` + `api/stocks.py` (grep) — never in `scoring.py`/`scanner.py`/`patterns.py`; source-seam test `test_bars_through_latest_not_in_scoring_path_source_seam`; ≤D MA byte-identical w/ or w/o forward extension; default `/bars` contract unchanged (TC-02). UI: displayed ≤D scores/setup/VCP/invalidation = snapshot (UT-06). Chart carve-out (display-only) honored. |
| Single source of truth / No recompute in read path (critical) | OK | `_leadership_returns(ret_by_symbol: dict, cfg)` — no Session, no `select(`, no return math; pure projection of the stored `forward_returns` the scorecard built. No new endpoint (`api/backtest.py` unchanged). |
| Attribution is read-only | OK | leadership returns mirror `_attribution_slices` discipline — derived from the same stored per-observation rows; recomputes-nothing keystone test passes. |
| Exactly one date selector | OK | horizon selector is a lifted VIEW selector (no date state); global as-of switcher is the only date control (UT-17, source). The historical minor violation (iter-0) stays RESOLVED and re-confirmed holding. |
| No fabricated data / Honest partial windows | OK | missing (row, horizon) → `mean_return: None` / `n: 0` → "—" NA in UI (UT-15: TPH `mean_return=null` cross-checked at `/api/backtest?as_of=2026-02-27`); no fabricated 0%. |
| Snapshots immutable | OK | no scanner_run/result write path touched; diff is a display accessor + a read-only projection. |
| No order/execution path; no secrets | OK | diff grep: only `.order_by(DailyPrice.date)` (SQL); no broker/order/key/secret added. |
| No magic numbers | OK | sectors via `cfg.etfs.sector`, themes via `cfg.themes`, cohort via `cfg.universe.symbols`; `test_no_magic_numbers` passes (complete keyed projection, no row-cap literal). |

**Coherence:** COHERENCE-PASS (no veto). Both new values reuse a single canonical source; both refine existing nav homes; nav skeleton unchanged; no `blueprint.reapproval-requested` (correct — `/research` deferred).

## Next-Step Recommendation

**Continue the new wave at `full` depth.** With the two existing-page refinements in, the natural next target is the foundational data-layer member **J-22 (expand to the rule-based ~500-name universe)** — a config screen + real committed seed expansion that grows forward-test sample sizes and unblocks the downstream labs; it adds no new nav home (surface the screen on `/methodology` or `/data`) but must hold *No fabricated data* (real committed bars only) and keep breadth/walk-forward labels "universe-relative / survivorship-biased." A reasonable alternative is **J-23/J-24 (multi-timeframe bars + the Stock-Detail timeframe selector)**, which builds directly on this iteration's chart work and carries a new per-timeframe no-lookahead seam. Either is full-depth (new infra/data, critical anti-goal seams). Sequence the **`/research` labs (J-25–J-31)** *after* the data groundwork — they introduce a new sidebar home and **require a blueprint nav re-approval** before being built.

## Halt Justification (if halting)

N/A — not halting. CONTINUE: two journeys (J-20, J-21) newly passing with directly-verified source seams + distinct evidence; zero regressions; no anti-goal violation; COHERENCE-PASS. GOAL_ACHIEVED is blocked because J-22…J-31 (10 of 31 must-have journeys) are confirmed unbuilt and explicitly out of scope this iteration.

## Process note

Consistent with the iter-2/iter-3 pattern, this full-depth iter produced **no `status.json`** under `iter-6/` (only `coherence.md` + `snapshot-sha`) and **no `auditor` handoff**, yet the QA report's Step-1 artifact table claims `status.json` present — a QA inaccuracy, not an app defect. I substituted my own source-level verification of both critical seams (grep no-lookahead seam + read `_leadership_returns` signature/body) rather than trust the missing artifact. Evidence-hygiene: the `qa` agent's `TC-15-before/after-horizon.png` are **byte-identical** (same sha256, 6859 bytes — the iter-3 duplicate-shot bug recurring in the qa agent's captures); the defining J-21 one-selector proof is instead grounded by the browser-qa-agent's **distinct** `UT-10-11-12` (1d) vs `UT-14` (60d) shots + a `window.fetch` spy showing no `/api/backtest` refetch on the switch. Neither gap changes the verdict.
