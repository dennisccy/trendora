# Iteration 38 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

iter-38 built J-97 (backend `?full=true` market-phase serialization + a two-pane synced regime×phase cross-view chart) and J-98 (Dashboard at-a-glance restructure), coherence COHERENCE-PASS, review PASS. But J-97's primary deliverable FAILS live: the evaluator independently confirmed `GET /api/market-phase?full=true` at the current as-of returns **no `timeline_full` key**, so the bottom pane renders no phase bands / severity line / P(bear) line — a stale-cache schema-versioning bug. J-98's restructure is built and DOM-confirmed but held PARTIAL because it embeds the broken J-97 chart and the evidence dir is empty (Chrome MCP timed out — zero screenshots). New journeys, never passing ⇒ not a regression; tractable single-cause fix ⇒ CONTINUE (this iter was never a GOAL_ACHIEVED candidate — J-99/J-100 unbuilt).

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-97 — two-pane synced regime×phase cross-view | (new) failing | **failing** | UT-09/UT-16 FAIL in ui-test-results.md; evaluator-confirmed live `GET /api/market-phase?full=true` → `has timeline_full key: False` (current as-of 2026-06-16) |
| J-98 — Dashboard at-a-glance restructure | (new) unknown | **partial** | UT-02/03/04/05/06/11/13/20 PASS (DOM+source); UT-08/10/12/18 SKIP (no screenshots — evidence dir empty); embeds the broken J-97 chart |
| J-18 — exactly one date selector (CRITICAL) | passing | passing | grep: 0 new date `useState`/keydown/`setAsOf` in new chart/card/page files; live `/` has 0 `input[type=date]`; synced zoom = view transform |
| J-07 — Risk-Off → 0 Actionable (CRITICAL) | passing | passing (untouched) | no regime/scanner/gate change in the additive diff |
| J-06 — single source | passing | passing | compact figures read `/api/dashboard` + `/api/market-phase` verbatim; no client recompute (coherence Step 1 PASS) |
| J-44/J-49 — pane 0 + as-of marker/full-history | passing | passing (carried) | top pane = unchanged index lines + stored-regime bands + as-of marker; backend additive only |
| J-87/J-88 — Market-Phase card phase/severity/P(bear) | passing | passing (carried) | `full=false` card payload byte-identical (default strips `timeline_full`); card endpoint unchanged |
| J-01/J-13/J-43/J-15/J-78/J-89/J-90 | passing | passing (carried) | additive diff; no behaviour change |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead | OK | full series strictly causal per point; J-89 smoothed/true-bear path structurally fenced (no code path into the full causal series); post-as-of points are display-only behind the marker |
| Single source of truth | OK | coherence Step 1 PASS — `timeline_full` read verbatim from `compute_market_phase`; figures re-display served values; no recompute |
| No recompute in the read path | OK | `market_phase_full_cached` is a pass-through over the existing cached path; no per-request recompute |
| No magic numbers | OK | `test_no_magic_numbers` PASS; the 3 hex in `lib/phase.ts` are the allowed frontend design-token mirror (annotated `--pos/--warn/--neg`, mirrors `lib/regime.ts`) — a frontend lib file, not a backend CALC_FILE |
| No fabricated data | OK | the stale-cache bug yields an EMPTY bottom pane (honest absence), never fabricated bands/values |
| Scores must be explainable | OK | both compact figures keep a named component-breakdown `<details>` (UT-04/UT-06) |
| Risk-Off gates Actionable (CRITICAL) | OK | untouched |
| Snapshots are immutable (CRITICAL) | OK | no snapshot/scanner_run write; no rebuild; no new table (`test_db` expected-tables guard PASS) |
| Pane-zoom/range-sync is a view transform, not a date control (CRITICAL, J-97) | OK | grep confirms no second date state / no global as-of write from the chart; live `/` = 0 native date inputs |
| No order/execution path (CRITICAL) | OK | no brokerage/order code added |

No new anti-goal violation introduced. The lone ever-recorded violation (iter-20 minor magic-number) stays resolved since iter-21.

## Coherence

COHERENCE-PASS (`runs/.../iter-38/coherence.md`). `timeline_full` serves from the canonical `GET /api/market-phase?full=true` (no second computation/endpoint); J-98 is a pure IA reshuffle of already-served values on the single Dashboard home; the `phaseFillVar` consolidation into `lib/phase.ts` is a coherence improvement. One non-blocking WARN (`phaseBadgeVariant`/`phaseVariant` presentational badge-variant duplication). No structural veto.

## Next-Step Recommendation

iter-39 **FULL** — fix the J-97 stale-cache schema-versioning defect, then capture genuine LIVE evidence for J-97 + J-98 (the iter-38 evidence dir was empty).

1. **Cache fix (backend, root cause):** `market_phase_cached` (`apps/backend/app/engine/market_phase.py:810-811`) serves a HIT for `(asof_key, dataset_version)` verbatim, but `_dataset_version` tracks DATA changes (backfill/removal) — NOT the payload SCHEMA. iter-38 added `timeline_full` to the payload without changing the dataset, so every pre-iter-38 cache row (including the live current as-of `2026-06-16` under unchanged `r1370-f3078889`) is served without `timeline_full`, and `market_phase_full_cached` (a pass-through) returns it. Fix by invalidating for the schema bump: add a payload-schema-version component to the `MarketPhaseCache` key (preferred — survivor-proof for future additive fields), OR clear rows whose payload lacks `timeline_full` / one-time prune pre-iter-38 rows. Assert: `?full=true` at the live as-of now serves `timeline_full` (causal, byte-identical to `compute_market_phase`'s `timeline_full`), and `?full=false` (card) stays byte-identical. Apply the same fix to the `retrospective` cache path if it shares the schema risk.
2. **LIVE browser-QA (this iter had ZERO screenshots):** with a working Chrome MCP **or the Playwright fallback** (iter-34 precedent — do not accept API/source-only evidence; iter-36 lesson), md5sum the evidence dir FIRST and reject blank/skeleton/byte-identical frames. Capture: J-97 bottom pane with phase-colored bands + 0–100 severity line + filtered P(bear) line over the same index lines + the as-of marker; the SYNCHRONIZED zoom as **two byte-DISTINCT before/after frames** (UT-10, skipped this iter); an early-as-of honest-empty bottom pane; J-98 first-paint compact summary + the More-detail expand (UT-12) + as-of-change updating both figures (UT-18).
3. **Required-still-passing live smoke:** J-18 (0 native date inputs; synced zoom adds no date state), J-07 (Risk-Off → 0 Actionable), J-06 (figures == served values; pane-1 series == card series for the overlap), J-44/J-49 (pane 0 unchanged), J-87/J-88 (card phase/severity/P(bear) unchanged), J-13/J-43 (as-of switch drives both panes).
4. **Suite gate:** hand the FULL backend pytest suite to the pump nohup-async; gate the next evaluator on the FLUSHED `0 failed, EXIT 0` line — never block on the in-flight stream (iter-11/29/37); re-run any single `test_warmup.py` / `test_data_manager_jobs_pipeline.py` F in isolation before attributing it.

After J-97/J-98 close green on LIVE evidence with COHERENCE-PASS and the suite GREEN, build the remaining buildable Must-haves J-99 (lean, `/data` pagination + year/month filter) then J-100 (full, bounded-resource backend hardening + concurrency load test). Only after J-97..J-100 all pass with a GREEN suite, zero regression, and COHERENCE-PASS does the next evaluation become a GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing per goal.md:105-108).

## Halt Justification (if halting)

Not halting. CONTINUE: progress was partial (J-98 restructure built + DOM-confirmed; J-97 built but broken by a single tractable stale-cache bug), the defect is precisely root-caused and one-step-fixable, no previously-passing Must-have regressed, no critical anti-goal was violated, and coherence is COHERENCE-PASS. This iteration was explicitly not a GOAL_ACHIEVED candidate (J-99/J-100 remain unbuilt). Not REGRESSION (J-97/J-98 are new journeys, never passing). Not STALLED (a clear, productive next step exists).
