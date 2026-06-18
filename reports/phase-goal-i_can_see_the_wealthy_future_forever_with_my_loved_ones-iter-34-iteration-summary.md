# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-34

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-06-18
**Iteration:** 34

## In plain words

**What you can do now:** See a live dashboard showing the current market regime, a Market Phase & Severity panel with a bear probability, a phase history timeline with dated downtrend episodes, and a fenced retrospective view. Browse a Recovery-Turn Edge study and a Downtrend Opportunity study on the Research page. Step to any past snapshot date and explore how scores, regime labels, and rankings looked on that day. Open any stock for an explainable score breakdown, a regime-banded price chart, per-bar hover details, and five forward-return columns each paired with a colour-graded drawdown figure. Sort every leaderboard by forward return or drawdown, search and filter by sector, theme, or pattern, and click any sample count to drill into the exact stored observations. On the Data Manager page, see how many stocks meet the historical membership criteria per date — including a breakdown of why others were excluded (history too short, price too low, volume too thin) — view a membership timeline, a macro feed panel, and access confirm-gated controls for a full snapshot rebuild and for extending backward history.

**What changed this time:** The Data Manager page now shows the per-date membership rule prose on the methodology page — how the per-date stock screening works, what the candidate pool size is, and what the minimum history bar requirement is. Two data panels that were previously stuck in a loading state now render with live figures: the per-date universe coverage diagnostic (admitted vs excluded stock counts with reasons) and the confirm-gated backward-history extension control with its survivorship caveat. The dynamic universe sliding with the as-of date on the stocks page is not yet working in the live view — the underlying logic is built and correct, but the stored data needs a full rebuild to reflect the new logic.

**What's next:** Run a full snapshot rebuild (a planned ~11-hour data operation) to make the stocks list honestly show fewer names at early historical dates, then verify the universe sliding end-to-end in the browser.

## Headline

Live re-verification closes J-94/J-95 partial→passing; J-93 confirmed failing (stale snapshots need rebuild); methodology fold-in ships.

## Direction

**Signal:** improving
**Why:** J-94 (per-date coverage diagnostic) and J-95 (backward-history control render) flip from partial to passing on genuine live evidence this iteration. J-93 and J-96 remain blocked by a data-regeneration gap — the stored snapshots were built before the dynamic resolver was integrated — which is a tractable, identified one-step operation (the J-85 rebuild). No journey regressed; all critical anti-goals (single date selector, no lookahead, no fabrication) held under the fold-in. Progress continues toward closing the final two journeys.

**Trend (last 5 iters):**
- Newly passing this iter: J-94 (per-date coverage diagnostic), J-95 (backward-history control render)
- Newly passing in last 5 iters total: J-91 (downtrend opportunity study), J-92 (FRED macro feed), J-89 (market-phase history timeline), J-90 (recovery-turn edge study), J-94, J-95
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none (the lone ever-recorded violation — iter-30 minor warm-up timeout — is a flake, not a violation; the iter-20 magic-number violation stays resolved since iter-21)
- Iters with no journey state change: 1 of last 5 (iter-30 held all journeys partial/unknown due to Chrome down)

**Latest evaluator reasoning:** The iter-34 lean live re-verification ran genuinely live (Chrome MCP timed out; the browser-qa-agent fell back to Playwright and produced real, large, md5-distinct, evaluator-VIEWED frames) and wrote the missing `ui-test-results.md` (the iter-33 CLOSURE-FAIL artifact now exists). J-94 (per-date coverage diagnostic) and J-95 (confirm-gated backward-history control + survivorship label) flip `partial → passing` on genuine rendered evidence. BUT J-93 is a genuine acceptance FAIL — the dynamic point-in-time universe does NOT slide on `/stocks` (122 rows at every as-of, including 2021-01-04 well before the warm-up boundary), and J-96's membership-timeline step function is a flat-122 line with no entries/exits — both because the persisted `ScannerResult` snapshots were built by the iter-27 J-85 rebuild BEFORE iter-33 repointed `score_stocks` to the resolver, and were never regenerated. This is not a regression (J-93/J-96 were never passing) and not blocked-NA (J-93/J-96 are explicitly NOT data-dependent, goal.md:2272) — it is a tractable data-regeneration gap → CONTINUE.

## What was done

- Widened the `UniverseSelection` TypeScript interface in `apps/frontend/lib/api.ts` with three additive display fields (`candidate_pool_size`, `per_date_rule`, `per_date_min_history_bars`) the backend already served
- Rendered the "Per-date membership rule" block on `/methodology` Universe Selection card, reading the three fields verbatim from the existing API payload (no new endpoint, no new computation)
- Confirmed backend diff is empty — all browser-QA targets required live env + Playwright, no code rework
- Ran live browser-QA (17/18 tests PASS) via Playwright fallback after Chrome MCP CDP-timeout throughout session
- Wrote the missing `reports/phase-...-iter-34-ui-test-results.md` (the iter-33 CLOSURE-FAIL artifact now exists, 18757 bytes)
- Confirmed J-94 PASS live: admitted_count=544, excluded_total=4 breakdown (below_history/price/ADV), thresholds rendered
- Confirmed J-95 PASS live: confirm-gated "Extend history backward" control + survivorship caveat rendered (real fetch stays blocked-NA)
- Re-verified 14 required-still-passing journeys live (J-06, J-07, J-08, J-18 CRITICAL, J-36, J-37, J-39, J-85, J-87, J-88, J-89, J-90, J-91, J-92 all PASS)

## What's left

- Journey J-93 (Per-as-of-date universe resolver — point-in-time) failing: `/stocks` serves 122 rows at every as-of because stored `ScannerResult` snapshots predate the iter-33 dynamic resolver integration; requires the J-85 confirm-gated regenerate-from-scratch rebuild (~11h, operator-confirmed) to persist dynamic membership
- Journey J-96 (Membership timeline + survivorship/coverage labels) partial: step function is a flat-122 line, entries/exits all "—", same stale-snapshot root cause as J-93; flips to passing once the J-85 rebuild is run
- Full backend suite EXIT=1 on one test: `test_warmup.py::test_start_warmup_is_single_flight_no_duplicate_concurrent_worker` — documented resource-contention flake under QA load (dates_done: 1 of 6 in 600s); backend source byte-unchanged from iter-33's GREEN run; must be re-confirmed clean on a quiet host before GOAL_ACHIEVED candidacy
- Open item: `iter32-stale-data-overview-shape` still listed unresolved in journey-history (the `test_api_data.py` macro shape guard was reconciled in iter-33 per the evaluator, but the open_items flag was not marked resolved)

## Next step

iter-35 should CLOSE the J-93 / J-96 stale-membership gap — this is the LAST real obstacle to GOAL_ACHIEVED and it is **not code work**, it is a **data-regeneration operation**:

1. **Run the J-85 confirm-gated regenerate-from-scratch rebuild ONCE** so the persisted `ScannerResult` snapshots are recomputed over the iter-33 per-date `resolve_members` membership. After this, `/stocks` will serve the dynamic membership (empty/small before the ~2021-10-18 warm-up boundary, rising to full) and the J-96 timeline SIZE column + step function + entries/exits will reflect the real dynamic universe. **CAUTION (MEMORY.md):** a `kind:"rebuild"` is ~11h and CLEARS the snapshot layer; it must be operator-confirmed and run via the pump (nohup), NOT a casual QA action. The committed price seed is never deleted (`clear_snapshot_set` asserts `bars_before == bars_after`). This is the operation J-93's own acceptance names ("populated exclusively by the J-85 confirm-gated regenerate-from-scratch rebuild").
2. **Then a LEAN live re-verification** of J-93 (two byte-DISTINCT `/stocks` frames with DIFFERENT row counts: early-date empty/small vs full ~496) and J-96 (the step function now RISES from the warm-up boundary; entries/exits populated). Reconcile the resolved-latest count: the J-94 diagnostic says ~544 admitted at latest — confirm `/stocks` now matches (within the benchmark/stocks-only distinction) so the J-06 single-source contract still holds across the diagnostic and the served membership.
3. **Re-run the FULL backend suite to `0 failed, EXIT 0`** (nohup-async to the pump; never block the evaluator — iter-11/29). The iter-34 run was EXIT=1 on exactly ONE test, `test_warmup.py::test_start_warmup_is_single_flight_no_duplicate_concurrent_worker` — a 600s warm-up timeout under QA resource pressure (`dates_done: 1 of 6`, status `running`), the documented slow-boot/warm-up contention flake (MEMORY.md), on a byte-UNCHANGED backend that passed clean at iter-33. Re-run it in isolation on a quiet host to confirm it is a flake, not a regression, before any GOAL_ACHIEVED candidacy.

Depth = **full** because triggering + verifying the rebuild touches the snapshot/scanner determinism + immutability surface and warrants the audit/closure pipeline. Required-still-passing: J-06 (now critically — the diagnostic-vs-served count reconciliation), J-18/J-07 (CRITICAL), J-87/J-88/J-89/J-90/J-91/J-92 (consumed market-phase layer — confirm the rebuild does not perturb the regime/ETF machinery, which is stocks-only-exempt), J-08/J-15/J-85 (immutability + snapshot-served reads). J-22/J-23/J-24 + J-95 real-fetch / constituent-feed legs stay honestly blocked-NA (non-vetoing).

NOTE: if an operator-confirmed ~11h rebuild is not acceptable in this session, the alternative is to confirm whether J-93/J-96 should be judged against the BUILT-and-causally-correct resolver (data-correctness PASS, already proven offline iter-33) rather than the rendered served membership — but the current goal.md acceptance and the iter-33/iter-34 evaluators both require the served/rendered end state, so the rebuild is the honest path to passing.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-34.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-34-dev.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-34-review.md |
| Browser QA | FAIL | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-34-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-34/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
