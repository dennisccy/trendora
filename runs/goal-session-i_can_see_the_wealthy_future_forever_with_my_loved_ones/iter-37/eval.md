# Iteration 37 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** lean

## Summary

iter-37 is the GOAL_ACHIEVED close-out of the iter-35 J-94 regression. It restored the J-46 load-once-per-job bar-cache invariant that the iter-36 cold-miss optimization silently broke for zero-bar candidate-pool symbols (served values byte-identical), and the live `/data` re-verify renders J-94's per-date universe-resolution diagnostic and J-96's rising membership timeline. The standing GREEN-full-suite gate is met (977 passed, 4 skipped, 0 failed, PYTEST_EXIT=0), coherence is COHERENCE-PASS, no anti-goal is violated, and every buildable Must-have (93/96) is passing/already_passing — only J-22/J-23/J-24 stay honestly blocked-NA (data-walled), which goal.md designates non-vetoing.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-94 — Per-date universe-resolution diagnostic | regressed | **passing** | reports/qa/goal-…-iter-37-evidence/UT-04-result.png (ADMITTED=544 + below-history=1/below-price=2/below-ADV, non-NaN) |
| J-96 — Membership-timeline + honesty labels | partial | **passing** | reports/qa/goal-…-iter-37-evidence/UT-03-result.png + UT-04-coverage-bottom.png (varying per-date size 500..514; entries/exits +1 GEHC / -2 HBAN VTRS / -3 HOOD NDSN RIOT; 3 honesty labels) |
| J-46 — Load-once-per-job backfill invariant | passing | passing (restored) | apps/backend/tests/test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once (max-load==1, assertion UNCHANGED, GREEN suite) |
| J-93 — Dynamic universe slides on /stocks | passing | passing (re-smoked, fast path) | UT-05-stocks-loaded.png (544/544 at as-of 2026-06-16) |
| J-06 — Score consistency / single source | passing | passing (re-smoked) | UT-06-nvda-detail.png; served /stocks 544 == J-94 diagnostic admitted 544 |
| J-07 — Risk-Off gates Actionable (CRITICAL) | passing | passing (re-smoked) | UT-08-dashboard.png |
| J-18 — Exactly one date selector (CRITICAL) | passing | passing (re-smoked) | UT-05-stocks-loaded.png (0 native input[type=date]; one global as-of) |
| J-87 / J-88 — Dashboard market-phase / P(bear) | passing | passing (re-smoked) | UT-08-dashboard.png |
| J-36 / J-37 — /data coverage + missing-data | passing | passing (re-smoked) | UT-04-result.png / UT-04-coverage-bottom.png |
| J-39 / J-85 — /data remove / rebuild panels | passing | passing (re-smoked) | UT-J39-remove-section.png / UT-J85-rebuild-panel.png |
| J-15 — Fast snapshot reads | already_passing | passing (re-smoked live) | UT-05-stocks-loaded.png |
| J-22 / J-23 / J-24 — expanded universe / intraday | unknown | unknown (blocked-NA) | — data-walled; non-vetoing per goal.md:105-108 |

All other Must-haves (J-01..J-21, J-25..J-92 not listed above) carry their prior passing/already_passing status; the iter-37 diff is backend-only and value-preserving (byte-identical served values), so none could regress. Total: **93/96 passing or already_passing; 3 blocked-NA (non-vetoing).**

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead (critical) | OK | No resolver-math/scoring change; `bars_asof`/`trailing_count` still slice ≤ D. A zero-bar symbol → 0 trailing bars → `below_history`, identical to the grouped-count path. |
| Snapshots are immutable (critical) | OK | No snapshot write/update/rebuild this iter; no `kind:"rebuild"` triggered; data_manager change is cache-sourcing only. |
| Single source of truth (critical) | OK | Served `membership_timeline` + `score_stocks(D)` byte-identical before/after (proven in tests + dev byte-identity scripts); the J-94 diagnostic admitted=544 reconciles with the served /stocks 544. |
| No recompute in the read path | OK | Change is HOW trailing-bar count is sourced (once-loaded cache vs per-date re-load), never WHAT is served. |
| Coverage & missing-data descriptive & honest | OK | Recording a no-bar symbol as an empty series is descriptive ("no bars at/through D"), not fabricated; exclusion reasons unchanged. |
| No fabricated data | OK | Empty series ⇒ honest 0 trailing bars; no synthesized prices/scores. |
| No magic numbers | OK | Diff adds no float/threshold literal in calc code (grep clean); the one ever-recorded violation (iter-20 minor) stays resolved since iter-21. |
| Risk-Off must gate Actionable (critical) | OK | J-07 re-smoked green; scanner/regime path untouched. |
| Exactly one date selector (J-18) (critical) | OK | Backend-only diff; J-18 re-smoked green (0 native date inputs, single global as-of). |
| No secrets in source | OK | Diff grep clean (no api_key/secret/token/crumb literal); no new committed credential. |

Diff is exactly 3 source files (`prices.py`, `data_manager.py`, `tests/test_bar_cache.py`) — no resolver-math/scoring/snapshot change, no new table, no frontend change. **No critical anti-goal violated; no minor violation introduced.**

## Halt Justification

All three GOAL_ACHIEVED conditions hold, plus the standing flushed-GREEN-suite gate:

1. **Every Must-have journey positive-evidenced.** 93/96 passing/already_passing. J-94 flips regressed→passing and J-96 partial→passing on LIVE Playwright evidence I viewed (UT-02/03/04 frames — hydrated /data, no skeleton, /api/data HTTP 200 at ~21s, stats [544,548,122,585,1369,1370] == iter-36 baseline). Required-still-passing all re-smoked green. The only non-passing journeys are J-22/J-23/J-24 — data-walled `unknown`, which goal.md (lines 105-108, reiterated in the J-92 acceptance) explicitly makes **non-vetoing** ("never halt the loop or veto completion of the buildable journeys"). The J-84 cookie+crumb expand path that unblocks J-22 is already built and passing, so J-22 auto-unblocks with no code change once a provider is reachable.
2. **Zero unresolved anti-goal violations.** The lone ever-recorded violation (iter-20 minor magic-number) is resolved since iter-21; iter-37 introduces none.
3. **COHERENCE-PASS** (no structural veto; same module/endpoint, byte-identical served values, 0 new routes/pages/nav).
4. **Standing gate met:** the full backend pytest suite flushed `977 passed, 4 skipped, 0 failed, PYTEST_EXIT=0` (/tmp/iter37_full_suite_pump.log, zero FAILED lines). The iter-36 `test_bar_cache` load-once regression is fixed in this green run; the iter-36 `test_warmup.py` failures were contention timeouts that pass clean here (iter-29/34 lesson).

The descoped `/api/data` coverage optimization (~10-12s warm) is a documented, non-user-facing perf note — the page fetches `/api/data` once on load with no polling and hydrates on a single patient load; it does not block J-94/J-96 acceptance because the diagnostic and timeline ARE rendered live and viewed.

## Next-Step Recommendation

Halt — goal achieved. No tractable code work remains for the buildable journeys (93/96 positive-evidenced). J-22/J-23/J-24 require a real cap-capable / intraday provider fetch (provider-walled on this host today); best handled by a future in-place resume scoped to a data fetch (lean), not a code iteration — J-22 auto-unblocks via the already-built J-84 path with no code change once a provider is reachable. Do NOT re-trigger the J-85 `kind:"rebuild"` (~11h destructive; the data is correct). If the owner extends goal.md with new journeys and resumes in-place (as in prior extensions), regenerate/re-approve the blueprint on resume; the lean depth recommendation applies to a consolidation-style follow-up. A descoped `/api/data` coverage optimization remains available (cache the coverage block on the existing `research._dataset_version` stamp + warm-up precompute + register any new table in `test_db.py`'s expected-tables guard) if `/api/data` concurrency-robustness is ever required — non-blocking, not needed for GOAL_ACHIEVED.
