# Iteration Summary — goal-i_can_see_the_wealthy_future-iter-11

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-05-31
**Iteration:** 11

## In plain words

**What you can do now:** Open a daily after-market dashboard that reads the market's mood, breadth, and the day's top sectors and themes; browse and filter a ranked list of stocks where each carries three plain grades (strength, buy-point quality, risk) and a one-line reason; and open any stock for its chart, its themes, and the price that would prove the idea wrong. You can rank investing themes and every sector and industry, keep a personal watchlist that remembers your own notes and survives a restart, and rewind the whole dashboard to any past trading day — including a Backtest page that shows how that day's top-graded picks actually performed afterward. You can also check a System Health page that honestly grades whether its high grades led to better returns, and now filter the stock list to names showing a "volatility contraction" chart pattern.

**What changed this time:** Trendora now spots its first chart pattern — a "volatility contraction", where a stock's pullbacks get progressively smaller and trading volume dries up toward a breakout price. You can filter the stock list down to just these names, see a clear badge and a plain-language explanation on each one (including the breakout level and the price that would prove the idea wrong), and check on the System Health page whether stocks showing this pattern actually went on to do better — shown honestly, including when the sample is too small to be sure.

**What's next:** Next, a plain-language glossary page will spell out what every grade and pattern means — including this new one — with quick info tips throughout, finishing the last planned capability.

## Headline

VCP detection — the product's first detected price pattern: flagged, explained, filterable, and forward-tested.

## Direction

**Signal:** improving
**Why:** This iter added J-16 (VCP detection) cleanly on existing seams — `patterns.py:detect_vcp` rides each immutable snapshot row *alongside* (never replacing) the setup status, surfaced on `/stocks`, `/stocks/[ticker]`, and `/system-health` — taking the session to 15/16 Must-haves passing. No regressions (J-01–J-15 all held; engine read-paths and `models.py` were append-only, COHERENCE-PASS, review PASS, QA 17/17 functional). Only J-12 (the `/methodology` glossary) remains, sequenced last by design so it can document the VCP entry — one tractable journey from a legitimate GOAL_ACHIEVED check.

**Trend (last 5 iters):**
- Newly passing this iter: J-16
- Newly passing in last 5 iters total: J-11 (iter-7), J-13 + J-15 (iter-8), J-14 (iter-10), J-16 (iter-11)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 1 of 5 (iter-9 — silent developer no-op; re-executed in iter-10)

**Latest evaluator reasoning:** J-16 (VCP — the product's first detected price pattern) landed cleanly and is the iteration's target journey: a config-driven `detect_vcp` rides each immutable snapshot row alongside (never replacing) the setup status — filterable + explained on `/stocks`, identical badge+card on `/stocks/[ticker]`, and a VCP-vs-non-VCP forward-return breakdown on `/system-health`. 15/16 Must-haves pass. Not GOAL_ACHIEVED only because J-12 (`/methodology` glossary) is unbuilt by design (sequenced last so it can document the VCP catalog entry).

## What was done

- Added **VCP detection** (the product's first detected price pattern): a config-driven `detect_vcp` (price + volume only, reads only data up to the scan date so it is no-lookahead by construction) composed onto each stored `score_stocks` row, carrying a plain-language reason, the pivot (breakout level), and a concrete invalidation level (last-contraction low).
- Added a **VCP filter** on the Stock Leaderboard (`/stocks`): All / VCP only / Non-VCP — narrows to the 4/122 flagged names (STX, TSLA, TSM, ORCL) on the latest seed snapshot as a pure client-side re-display; honest empty-state when a snapshot flags none.
- Added a **VCP badge** on flagged rows plus a dedicated **VCP card** on `/stocks/[ticker]` (reason + pivot + invalidation + contraction-depth chips), with the exact same values on leaderboard and detail; the badge always rides alongside the setup status and never promotes a name to Actionable.
- Added a **VCP-vs-non-VCP forward-return panel** on `/system-health`: VCP +3.18% (n=27 ⚠) vs non-VCP +2.01% (n=1191) at 20 days, with honest low-sample marker and the survivorship caveat.
- Kept it honest and single-source: new `config.patterns.vcp` block holds every threshold (`patterns.py` added to `CALC_FILES`, `8`/`35` added to forbidden ints); `models.py` gains only an append-only `is_vcp` mirror column; no new API endpoint; the local DB was deterministically rebuilt from the frozen seed.
- Verified by keystone tests (patch `detect_vcp` + `score_*` to raise → reads still serve stored; `VCP ∉ ALL_STATUSES`; forced-flag-every-name → setup statuses byte-identical; risk-off flagged rows stay watchlist-only; `is_vcp == record_json.vcp.flagged`).
- Browser-QA signal: the **dedicated browser-qa SKIPPED** (frontend down at QA time, HTTP-000 — 10th consecutive); **QA mode-2 self-healed both services and verified all 5 VCP browser flows + 17/17 functional test cases** (118 targeted backend tests green, frontend build clean), and the evaluator reconciled J-16 as passing from 4 md5-distinct evidence PNGs + source reads.

## What's left

- **Journey J-12 (Understand what each setup/pattern means — glossary + inline tooltips) failing** — the last remaining Must-have; unbuilt *by design*, sequenced next so it can document the just-landed VCP catalog entry (adds a new nav route → will need `blueprint.reapproval-requested`).
- **Not visible yet:** the `/methodology` glossary page and its VCP entry are intentionally deferred to the next iteration; the lower-level VCP numeric fields (volume ratio, distance-from-pivot) ride the API but are not individually rendered (only the badge/tooltip and the detail card's contraction chips are shown).
- **Known limitation:** the VCP forward-test cohort is small (n=27 at 20 days, below the 30 min-sample) — shown honestly with a ⚠ marker; the +3.18% vs +2.01% edge is indicative, not conclusive, and carries the same survivorship caveat as the rest of System Health.
- **Known limitation:** VCP detection is selective by design — some historical snapshots flag 0 names and correctly show an honest empty-state / NA rather than a fabricated pattern.
- **Known limitation:** the detector uses daily price + volume only (no intraday, no fundamentals); names with fewer than `min_history_bars` of history are reported as not-flagged (NA), never with a fabricated pivot.
- **Non-gating runner-script debt (chronic, NOT a product issue):** dedicated browser-qa SKIPPED a 10th consecutive time (runner probed `GET /health` 404 instead of canonical `/api/health`, and tore both services down before browser-qa ran); the audit handoff (`reports/audits/` / `docs/handoffs/...-audit.md`) is missing a 10th full-depth iteration (`status.json` stops at `qa_complete`). Durable fixes belong in `scripts/automation/*.sh`; neither affected this verdict.

## Next step

**iter-12 at full depth — J-12 (`/methodology` config-backed glossary + inline setup/pattern tooltips), the final Must-have.** Build a single config-backed catalog (setup statuses + the VCP pattern entry, each with plain-language meaning + the exact config thresholds + a worked example) surfaced as (a) a new `/methodology` nav route and (b) inline info tooltips on every setup/pattern badge — so an entry added to config appears in both places with no code change (the VCP reason/thresholds are already config-backed to make this trivial). It adds a **new nav route → requires `blueprint.reapproval-requested`**. Pair it with a **full 16-journey regression sweep + full-product coherence** so the next evaluation can legitimately reach GOAL_ACHIEVED (16/16). Full depth (new route + new IA home + reapproval + the goal-completing sweep is well beyond lean scope).

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future-iter-11-what-to-click.md`:

1. Open `http://localhost:3835/stocks`
2. In the `VCP` dropdown choose `VCP only`
3. Hover the teal `VCP` badge on the first row (wait ~1s for the tooltip)
4. Click that first ticker to open its detail page (`/stocks/<TICKER>`)
5. Confirm the pivot matches step 3

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future-iter-11.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future-iter-11-dev.md |
| Frontend handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future-iter-11-frontend.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future-iter-11-review.md |
| Browser QA | SKIPPED | reports/phase-goal-i_can_see_the_wealthy_future-iter-11-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-i_can_see_the_wealthy_future-iter-11-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_can_see_the_wealthy_future-iter-11-user-visible-changes.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future-iter-11-what-to-click.md |
| UI surface map | — | reports/phase-goal-i_can_see_the_wealthy_future-iter-11-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-i_can_see_the_wealthy_future-iter-11-ui-test-plan.md |
| QA | PASS | reports/qa/goal-i_can_see_the_wealthy_future-iter-11-qa.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future/iter-11/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future/state/journey-history.json |
