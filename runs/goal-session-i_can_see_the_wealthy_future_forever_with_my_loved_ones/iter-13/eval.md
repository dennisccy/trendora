# Iteration 13 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

Iter-13 (full depth) ships J-61 (per-date availability heatmap on `/data` via a new read-only `GET /api/data/availability`) and J-62 (as-of calendar popover replacing the flat `<select>`), both verified passing from primary evidence — evaluator-viewed heatmap + calendar screenshots, a diff-verified read-only availability derivation, and the byte-unchanged `asof-provider.tsx` that proves the single-date-state invariant holds. No anti-goal violation, COHERENCE-PASS, full backend suite GREEN (767 passed / 4 skipped / 0 failed). Not GOAL_ACHIEVED: J-63 (event-study first-trigger episodes) remains the last buildable failing Must-have; J-22/23/24 stay blocked-NA (data-walled, non-vetoing).

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-61 — Per-date availability heatmap | failing | **passing** | reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13-evidence/UT-01-fullpage.png |
| J-62 — As-of switcher is a calendar that shows what is selectable | failing | **passing** | reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13-evidence/UT-08-historical-selected.png |
| J-13 — One date control (req-still-passing) | passing | passing (no regression) | asof-provider.tsx byte-unchanged (not in iter-13 diff) |
| J-18 — One date control, no duplicate (req-still-passing) | passing | passing (no regression) | heatmap click writes only setStart/setEnd, never setAsOf (UT-17 DOM-verified) |
| J-43 — `?asof` URL serialization (req-still-passing) | passing | passing (no regression) | UT-08/UT-15: select 2026-05-01 -> /stocks?asof=2026-05-01, new tab same state |
| J-50 — href stamping (req-still-passing) | passing | passing (no regression) | href stamping untouched (asof-provider unchanged) |
| J-42 — ISO yyyy-MM-dd (req-still-passing) | passing | passing (no regression) | calendar uses shared formatIsoDate (coherence Step 1) |
| J-36/J-17/J-37 — coverage / data-manager on /data (req-still-passing) | passing | passing (no regression) | /api/data overview + existing data endpoints byte-unchanged |
| J-08/J-06/J-15/J-40 (req-still-passing) | passing/already_passing | unchanged (no regression) | no backend canonical path touched |
| J-63 — Event study overlap-honest | failing | failing (not targeted this iter) | next target |
| J-22/J-23/J-24 — data-walled | unknown | unknown (blocked-NA, non-vetoing) | no work this iter per spec |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Exactly one date selector (no second date state) | OK | `asof-provider.tsx` byte-unchanged (NOT in the iter-13 diff; git status shows only `asof-switcher.tsx` modified + `asof-calendar.tsx` new). Switcher's only new local state is `open` (popover visibility); calendar's only local state is `view` (month-navigation cursor, never an as-of value). All selection routes through the existing `setAsOf`. Coherence COHERENCE-PASS verified this explicitly. |
| Coverage & missing-data are descriptive & honest | OK | `compute_availability` is a diff-verified read-only derivation: reuses the SAME `_trading_days` SPY calendar + `COUNT(DISTINCT DailyPrice.symbol)` (== coverage `symbol_count` 159) + `ScannerRun.asof_date` set `compute_coverage` reads. No second derivation of a coverage figure. |
| No recompute in the read path | OK | No INSERT/UPDATE/session.add/commit/persist/run_scan/recompute in the new function; recomputes no canonical score/return/bucket/setup. |
| No fabricated data | OK | Honest empty-DB path: `cells == []`, `total_symbols == 0` (no fabricated cells); a zero-bar trading day renders `symbols_with_bars=0`, never omitted-as-covered (TC-17). |
| No magic numbers | OK | No `config.yaml` / `config.py` change in the iter-13 diff. The density->color ramp is frontend presentation only (coherence confirmed no matching backend classification logic). |
| No new stored column (iter-12 `_ADDITIVE_COLUMNS` trap) | OK | `models.py` / `db.py` / `config.py` / `config.yaml` are NOT in the iter-13 changed set — no new column, so the trap does not apply. |

## Next-Step Recommendation

Target **J-63** at **full** depth — the final buildable Must-have that closes the session.

J-63: the Setup & Pattern Lab (`/research`) defaults to a **first-trigger episode** view (consecutive same-symbol signal-days collapse into one observation), with the current pooled per-signal-day view one toggle away and **byte-identical to today's figures**. Both modes must disclose n, unique symbols, and episode count.

Full depth is warranted: it is a backend research-module change with a hard byte-identity guard (the pooled toggle must reproduce the prior figures exactly), the episode collapse must come from the SAME observation builders (one membership rule, a deterministic stored-data-only grouping — never a recompute), and it must stay count-coherent with the J-64/J-65 `N=` samples drill-downs in both modes. Required-still-passing for that iter: **J-29** (event-study lab), **J-51/J-64/J-65** (samples drill-down count-coherence), and **J-25/J-26/J-32** (the other `/research` labs must read unchanged). After J-63 passes with no regression and a clean coherence audit, the session becomes a GOAL_ACHIEVED candidate (J-22/23/24 stay blocked-NA, non-vetoing).

## Halt Justification (if halting)

N/A — not halting. CONTINUE: two Must-have journeys (J-61, J-62) are newly passing with positive primary evidence, no regression, no anti-goal violation, and one tractable buildable journey (J-63) remains. The loop continues to iter-14.
