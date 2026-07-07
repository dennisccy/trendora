# Iteration 18 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-18
**Date:** 2026-07-07
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Diff base used

The recorded `runs/goal-session-mcp-loop/iter-18/snapshot-sha` (`7720e42c`) is confirmed to be exactly
the stale stash-merge WIP object the iter spec's NOTES warns about (`git log` shows it as `WIP on
goal/mcp-loop: 6f14598...`, not an ancestor of `HEAD`; diffing it against `HEAD` pulls in ~815 unrelated
vendored-framework files). Per the iter spec's explicit instruction ("Diff base for the
coherence-auditor / evaluator... diff against current `HEAD` + untracked files"), this audit instead
used `git diff HEAD` plus `git status` for untracked files — confirmed independently: ALL iter-18
product work is uncommitted (206 `M`, 591 `D`, 459 `??`, all consistent with the atomic seed swap +
code seams the spec describes).

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Evidence status / certified-claim (`certify_edge`→`verify_edge`→`certified-claims.jsonl`→`GET /api/evidence`) | OK | `app/engine/{referee,ledger,online_fdr,evidence}.py` + `app/mcp/tools.py`: `git diff HEAD --stat` empty (independently re-verified, not taken on faith from the spec). Ledger content regenerated (7 rows, all `FAIL`, `register_date 2026-07-03`, row 1 `signal=leadership_score`) via the unchanged engine — content-only, same module/endpoint. |
| Three per-stock scores (`scoring:score_stocks`) | OK — untouched | `app/engine/scoring.py` not in diff |
| Market regime score (`regime:score_regime`) | OK — untouched | `app/engine/regime.py` not in diff |
| Sector / theme scores | OK — untouched | `app/engine/{sectors,themes}.py` not in diff |
| Realized forward-return evidence (`forward_testing:compute_forward_aggregates`/`compute_run_scorecard`) | OK | `apps/backend/app/engine/forward_testing.py:53-58` — only the `SURVIVORSHIP_BIAS_LABEL` string constant changed (copy update to ~30y span); the compute functions themselves are untouched. |
| Research-lab cohorts (`research:compute_*`) | OK — untouched | `app/engine/research.py` not in diff |
| Daily prices / bars (`seed_loader`/`daily_prices` → `GET /api/stocks/{ticker}/bars`) | OK | `apps/backend/app/api/stocks.py:119-224` — same endpoint, gains `?range=` presentation param (`_visible_indices` selects INDICES over the already-served real bars; nothing synthesized). MA still the canonical `sma_series` over the FULL series (`stocks.py:192`), only sliced to the visible window (`stocks.py:216`) — never recomputed over a sample. `resolve_servable_symbol` (`stocks.py:65-81`) is a NEW SHARED function, and `watchlist.py:262-264` now IMPORTS it instead of keeping its own inline ticker-check — this CONSOLIDATES two previously-independent validation implementations into one, an improvement, not a duplication. |
| Membership (`resolve_members`/`resolve_candidate` → `/methodology`, `/data` diagnostics) | OK | `apps/backend/app/engine/universe_resolver.py:574-597` — same `resolve_candidate` function, one added gate (`REASON_STALE`) in the existing gate-order chain; `data_manager.py:406-401` (`_universe_diagnostic`, served by unchanged `app/api/data.py`) and `methodology.py:126` (served by unchanged `app/api/methodology.py`) both just read the extended `EXCLUSION_REASONS` tuple — no second computation, same serving endpoints (independently confirmed via grep on the calling API files). |

**New endpoints check:** `grep -nE '^\+.*@router\.(get|post|put|delete)'` across the full code diff returns
zero matches — no new route was added anywhere this iteration.

**Frontend fetch-path check:** `apps/frontend/lib/api.ts`'s `fetchStockBars` gained one optional `range`
param appended to the SAME URL (`api.ts:902-910`); `apps/frontend/app/stocks/[ticker]/page.tsx`'s new
`ChartRangeControl` (`page.tsx:815-847`) only flips a persisted boolean that feeds that same call
(`page.tsx:779`) — no client-side slicing/recompute. `apps/frontend/app/data/page.tsx`'s new
"Stale series" reason card and the Membership Timeline's added column both read a key
(`diagnostic.excluded.stale_series` / `p.excluded.stale_series`) already present on the existing served
payload — no new fetch.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Chart range control (`Recent`/`Full history` toggle) | OK | Lives inside the existing `/stocks/{ticker}` page (`apps/frontend/app/stocks/[ticker]/page.tsx`), the blueprint's registered J-10 home — not a new page. |
| `/data` diagnostic panel (+1 "Stale series" reason card) | OK | Same page (`apps/frontend/app/data/page.tsx`), same panel, one more card in an existing grid. |
| `/methodology` copy update (staleness gate) | OK | Same page/section, no structural change. |
| No new page/route this iteration | OK | `find apps/frontend/app -name page.tsx` enumerated 22 routes — every one matches the blueprint's IA table exactly (Dashboard, Stocks + detail, Themes, Sectors, Scanner Runs + detail, Backtest, Research + 9 labs/samples, Evidence, Watchlist, Methodology, Data Manager); `git status` shows zero untracked `page.tsx` files. |
| Nav skeleton | OK | `apps/frontend/components/sidebar.tsx` — `git diff HEAD --stat` is completely empty; zero nav changes this iteration, confirming the blueprint's "no nav-skeleton change" claim independently rather than on trust. |

No new feature/page was introduced this iteration to check for reachability or duplicate homes — every
UI change this iteration is content/copy/param changes to already-canonical-homed pages, per the
ui-surface-map (`reports/phase-goal-mcp-loop-iter-18-ui-surface-map.md`: "New pages/routes: 0... Navigation
changes: no").

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The new `stale_series` exclusion reason and the bars endpoint's new presentation fields (`range`,
  `first_available_date`, `window_start`, `downsampled`) are not separate rows in the Data Contract
  table, but the blueprint's own iter-18 clarification paragraph (already present in `blueprint.md`
  before this dispatch, per the established per-iteration-clarification convention used throughout this
  session's history) explicitly documents both as additive presentation/categorization extensions of
  already-registered values (`daily_prices`/bars endpoint; `resolve_members`/`resolve_candidate`) —
  verified against the actual diff above, not taken on faith. Not treated as "unregistered" since the
  registration mechanism this blueprint uses for incremental extensions is the clarification paragraph,
  and it is present and accurate.
- `resolve_servable_symbol` being pulled into a shared function that `watchlist.py` now imports from
  `app/api/stocks.py` is a small coherence *improvement* worth noting for the next iteration's context:
  two previously-divergent inline ticker-validation checks are now one canonical implementation.
