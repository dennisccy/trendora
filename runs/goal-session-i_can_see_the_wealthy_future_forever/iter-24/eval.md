# Iteration 24 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-36 (per-symbol coverage table + plain-language definitions + universe-vs-symbols clarity) landed and is **passing** — backend logic is green (73 J-36/J-39 tests pass; consistency invariant 162 symbol rows == `symbol_count`, 122 in-universe rows == `universe_count`), and the QA MODE-2 screenshot `TC-01-coverage-defs.png` is a genuine fully-hydrated render of the definitions block + universe-vs-symbols prose + the per-symbol table with thin/missing badges. J-39 (seed-safe Remove-data) is **partial**: its destructive cascade boundary is verified sound IN SOURCE (whole-row deletes, no in-place snapshot overwrite, no recompute, seed protection + refusal) and integration-proven, but its defining browser flow (preview → protected-seed breakdown + cascade → confirm/refusal) was **not captured** — the dedicated browser-qa-agent SKIPPED all 26 tests (frontend down), and the only J-39 QA shot (`TC-07-remove-data-control.png`) is blank. J-35 stays **partial** — its end-to-end expand capture was again explicitly deferred. GOAL_ACHIEVED is not reachable (J-37/J-38 remain unbuilt buildable Must-haves; J-39/J-35 partial). No regressions; coherence PASS; no new anti-goal violation.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-36 | failing | **passing** | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-24-evidence/TC-01-coverage-defs.png (hydrated render: 6 definition blocks + universe-vs-symbols prose + per-symbol table w/ thin/missing badges); 73 backend tests green; consistency invariant 162==symbol_count / 122==universe_count (QA TC-03/04/21/22, source-confirmed) |
| J-39 | failing | **partial** | Source: data_manager.py:480-513 (`remove_data` whole-row `delete()` on ForwardReturn/ScannerResult/SectorScoreRow/ThemeScoreRow/ScannerRun/DailyPrice — NO UPDATE, no recompute), :305-349 `_cascade_targets` "derives-solely" predicate, seed-protection + refusal; 73 tests green (cascade-solely / fully-covered-snapshot-untouched / seed-only-refused / audit-recorded / no-recompute). BUT defining browser flow UNCAPTURED — dedicated browser-qa SKIPPED; `TC-07-remove-data-control.png` is blank. |
| J-35 | partial | partial (carry) | Defining end-to-end expand capture again deferred (QA report: "deferred to live session, not blocking"); dedicated browser-qa SKIPPED. Machinery integration-proven (carries iter-23). |
| J-18 | passing | passing (re-confirmed) | TC-01 shows exactly one date `<select>` in nav (top-right "2026 ▾"); Remove-data date inputs are action params; coverage table adds no date state (coherence PASS) |
| J-17 / J-33 / J-34 | passing | passing (carry — fetch/backfill/expand/resume paths git-untouched) | data_manager fetch/backfill/expand/resume branches unchanged; 73 tests green |
| J-06 / J-07 / J-08 / J-15 | passing | passing (carry — structural) | scoring/scanner/regime/buckets/forward_testing/snapshot_serving git-untouched; remove cascade is whole-row delete, never in-place overwrite (J-08); no DB regen → byte-identical |
| J-01–J-05, J-09–J-14, J-16, J-19–J-21, J-25–J-32 | passing | passing (carry) | Working-tree diff is exactly 6 app files (data_manager.py, api/data.py, 2 tests, page.tsx, api.ts); /stocks·/backtest·/research·/themes·/sectors paths git-untouched; cannot have regressed |
| J-22 / J-23 / J-24 | failing | failing (carry — data-walled, NON-HALTING/NON-VETOING) | Not re-probed (spec forbids); recorded honestly NA |
| J-37 / J-38 | failing | failing (out of scope iter-24; iter-25 targets) | CONFIRMED unbuilt; explicitly deferred by the iter-24 spec |

**Board: 32 passing / 2 partial (J-35, J-39) / 5 failing (J-22/23/24 data-walled + J-37/J-38 unbuilt-buildable).**

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Coverage & missing-data descriptive & honest, no magic number | OK | `_per_symbol_coverage` reads stored bars + config; `thin` threshold from `indicators.min_history_bars` (no literal); missing member ⇒ NA range, never fabricated (73 tests incl. exact-value + thin-threshold + empty-dataset) |
| Data removal seed-safe & consistency-preserving | OK (verified, J-39 partial only on browser capture) | Seed classifier reads `data/seed/meta.json`; seed bars protected, wholly-seed scope refused; cascade deletes ONLY derived rows (data_manager.py:494-513); fabricates nothing |
| Snapshots are immutable (critical) | OK | Remove path is whole-row `delete()` only; NO `update()`/in-place overwrite of any ScannerRun/ScannerResult (grep: zero UPDATE on snapshot rows); fully-covered snapshot left untouched |
| No recompute in read path (critical) | OK | No `run_scan`/`score_stocks`/`forward_return`/`detect_*`/`score_regime` reachable from the remove/coverage path (only in fetch/backfill docstrings + `_do_backfill`); coverage recomputes no score/return/bucket |
| Single source of truth (critical) | OK | `in_universe` reads the same `config.universe.symbols` serving `universe_count`; no second universe computation (coherence PASS) |
| Risk-Off gates Actionable (critical) | OK | regime.py/scoring.py git-untouched; no DB regen → byte-identical |
| Exactly one date selector | OK (RESOLVED, held) | TC-01: one nav `<select>`; remove date inputs are action params; coverage table adds no date state |
| Import keys env-or-session, never persisted/echoed | OK (RESOLVED, held) | This iter touches no key-carrying provider path; J-39 removal error surface carries no secret (no URL/key in removal errors) |
| No fabricated data | OK | Missing/thin shown NA; preview/removal fabricate nothing |

No new anti-goal violation introduced. Both historical minor violations remain `resolved`.

Coherence: **COHERENCE-PASS** (no veto). The iteration is strictly additive on the existing `/data` page; all new values registered in the Data Contract.

## Next-Step Recommendation

**full** depth, iter-25. (1) **Re-capture the two partial browser flows on a clean hydrated build** (stop strays by port; `rm -rf apps/frontend/.next`; restart `next dev`; confirm `GET /_next/static/chunks/main-app.js` → 200 + health badge cleared BEFORE driving any UI; do NOT run a prod build against the live dev `.next`): **J-39** — open Remove data → enter a user-added scope → preview rendering removable bars + range + protected committed-seed breakdown + dependent cascade → seed-only scope refusal (use the **preview** path on the live host per MEMORY `j39-live-host-has-user-added-nvda-bars`; the destructive confirm is proven by the fixture, never run against a real symbol on the live host); **J-35** — injected-provider expand to completion → passers + omitted-with-reason → grown `universe-count`. (2) **Build the two remaining buildable Must-haves**: **J-37** (missing-data diagnostic + one-click pull-missing via the J-34 engine — diagnostic deterministic, pull partly data-dependent/non-halting) and **J-38** (unified Unfinished-imports — generalize the iter-22 Resumable panel to Resume/Retry/Remove with state explanation, on the J-34 ImportCheckpoint surface; provable offline). After J-37/J-38 land green offline and J-39/J-35 capture green, GOAL_ACHIEVED is reachable — with J-22/J-23/J-24/J-35 live-fetch outcomes recorded honestly NA/non-halting. Do NOT autonomously re-probe J-22/J-23/J-24; do NOT declare completion on a single import-journey landing (iter-20 re-scope trap).

Anti-goal watch for iter-25: J-37's pull-missing reuses the J-34 engine — re-confirm the iter-21/22 key-leak scrub holds on any new error string; J-38's Remove (an unfinished import) is distinct from J-39's seed-safe bar removal — keep the cascade boundaries separate.
