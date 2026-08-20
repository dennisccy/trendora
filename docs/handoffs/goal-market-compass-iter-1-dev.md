# goal-market-compass-iter-1 Dev Handoff

**Phase:** goal-market-compass-iter-1
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete

## What Was Built

J-01 ("Sector attribution is honest and near-complete on new runs"): a pool-CSV fallback for the
stock sector label, plus a `/methodology` disclosure of the two-source basis.

- `universe.pool_sector_aliases` (`dict[str, str]`, default `{}`) added to `UniverseCfg` and to
  `config.yaml`'s `universe:` block — a normalization seam for a future pool-CSV sector-name
  mismatch (today's 11 pool sector names already equal `etfs.sector`'s 11 names verbatim, so it is
  a genuine no-op identity map today; TC-6 proves this both at the unit level and against the real
  committed pool).
- Two new pure functions in `app.engine.universe_screen`, beside the existing `read_pool()` reader
  (reusing that ONE CSV parser — never a second reader):
  - `resolve_pool_sector(raw_sector, *, aliases, valid_sectors)` — normalizes one raw pool-CSV
    sector name through the alias map, then validates membership in the caller's valid-sector set;
    degrades to `None` for a missing/blank/unresolvable name (never raises, never a fabricated or
    stray string).
  - `pool_sector_map(*, aliases, valid_sectors, seed_dir=None)` — ticker -> resolved sector for the
    whole pool, built once from `read_pool()`; a not-yet-built pool degrades to an empty map.
- `scoring.score_stocks` now computes `pool_sectors = pool_sector_map(...)` ONCE per call (not
  per-stock) and the row's `"sector"` field is `cfg.stock_sectors.get(ticker) or
  pool_sectors.get(ticker)` — curated map first, pool-CSV fallback second, else `None`
  ("Unassigned"). `Stock.sector_id`, `stock_sector_etf`, and every `rs_sector` / score input are
  completely untouched (separate machinery at `scoring.py:296-331`, verified unmodified) — this
  remains a descriptive-only field, proven by the TC-4 byte-identity fixture
  (`test_pool_sector_fallback_never_changes_any_score_bucket_or_setup` in `test_scoring.py`).
- `UniverseSelectionCfg` gained a required `sector_basis: str` field (plain prose, resolved live —
  same pattern as the existing `membership_rule`); `config.yaml`'s
  `methodology.universe_selection.sector_basis` carries the two-source disclosure prose (curated
  first, pool-CSV fallback second, current-only limitation, B-114 referenced as still open).
- `app.engine.methodology._universe_selection` now includes `sector_basis` in its returned dict,
  served verbatim through the existing `GET /api/methodology` -> `universe_selection` block (no new
  endpoint, no gating change).
- `/methodology`'s `UniverseSelectionCard` renders a new "Stock sector labels" subsection (mirrors
  the existing "Per-date membership rule" bordered-subsection pattern) showing `sector_basis`
  verbatim.
- Zero code change to `/stocks` (leaderboard Sector cell, "Unassigned" filter, stock detail header)
  — confirmed by direct grep that no line in `apps/frontend/app/stocks/` or the stock detail page
  references sector resolution logic; they already read the stored value as-is (iter-0's binding
  "Do not redo").

## Files Changed

- `apps/backend/app/config.py` -- added `pool_sector_aliases: dict[str, str]` to `UniverseCfg`
  (default `{}`); added required `sector_basis: str` to `UniverseSelectionCfg`.
- `config.yaml` -- added `universe.pool_sector_aliases: {}`; added
  `methodology.universe_selection.sector_basis` prose.
- `apps/backend/app/engine/universe_screen.py` -- added `resolve_pool_sector()` and
  `pool_sector_map()` beside `read_pool()`.
- `apps/backend/app/engine/scoring.py` -- imported `pool_sector_map`; computed it once per
  `score_stocks` call; wired the fallback into the row's `"sector"` field (the only line changed
  besides the import and the one new computed-once block).
- `apps/backend/app/engine/methodology.py` -- `_universe_selection()` now includes `sector_basis`
  in its returned dict.
- `apps/frontend/lib/api.ts` -- `UniverseSelection` interface gained `sector_basis: string`.
- `apps/frontend/app/methodology/page.tsx` -- `UniverseSelectionCard` renders the new
  `sector_basis` subsection.
- `apps/backend/tests/test_universe_screen.py` -- new tests for `resolve_pool_sector` /
  `pool_sector_map` (TC-3, TC-6, TC-7 unit-level coverage); see below for the file-placement note.
- `apps/backend/tests/test_scoring.py` -- new tests: TC-4 byte-identity fixture, an engine-level
  TC-1 coverage companion, a curated-wins-over-pool spot-check, and a TC-8 historical-immutability
  proof; updated one stale pre-J-01 comment.
- `apps/backend/tests/test_methodology.py` -- new TC-5 tests (content + config-only-no-hardcoding).
- `apps/backend/tests/test_api_methodology.py` -- new TC-5 test at the API layer (skips honestly
  when the pre-existing `universe.json` gate is closed — see Known Issues).

**Deliberate deviation from the execution plan:** the plan suggested putting the new sector-lookup
unit tests in `apps/backend/tests/test_sectors.py`. That file tests `app.engine.sectors`
(sector-ETF ranking), a different module from `app.engine.universe_screen` (where the new
`resolve_pool_sector`/`pool_sector_map` functions live). Following this codebase's own established
one-file-per-module test convention (confirmed: `test_universe_screen.py` already tests
`universe_screen.py`'s `read_pool`/`screen_reasons`), I added the new tests to
`test_universe_screen.py` instead. Same test scenarios (TC-3, TC-6, TC-7), different file, for
consistency with the codebase's existing organization.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/<file> -v`

- `tests/test_universe_screen.py`: **15 passed, 3 skipped** (0 failed). The 3 skips are pre-existing
  tests gated on `data/seed/universe.json` (see Known Issues) — unrelated to this iteration.
- `tests/test_methodology.py` + `tests/test_api_methodology.py`: **22 passed, 1 skipped** (0
  failed). The skip is the new API-layer TC-5 test, honestly skipped for the same
  `universe.json`-gate reason (mirrors the existing `test_universe_selection_gated_on_committed_screen_record`
  test's pattern for the same file).
- `tests/test_scoring.py`: **23 passed, 1 failed** in 4071s (1:07:51 — this file's `loaded_engine`
  session fixture rebuilds the full historical cadence from scratch; host contention from an
  unrelated concurrent process on this shared machine slowed this particular run well past its
  normal ~45-50 min). **All 5 of the tests this iteration added or touched PASSED**:
  `test_pool_sector_fallback_never_changes_any_score_bucket_or_setup` (TC-4),
  `test_pool_sector_fallback_lifts_coverage_at_or_above_95_percent` (TC-1),
  `test_pool_sector_fallback_prefers_curated_map_when_both_resolve`,
  `test_historical_row_sector_not_rewritten_by_pool_fallback` (TC-8), and the pre-existing
  `test_each_stock_has_three_bucketed_explainable_scores` (whose stale comment I updated) all PASSED.
  **The 1 failure, `test_risk_budget_values_ride_the_row_but_enter_no_score`, is pre-existing and
  proven unrelated to this iteration** — full evidence below.
- `tests/test_no_magic_numbers.py`: **1 passed, 1 failed** — but the failure is **pre-existing and
  entirely unrelated to this iteration.** `test_engine_calc_code_has_no_magic_numbers` flags float
  literals in `indicators.py`, `forward_testing.py`, and `research.py` — three files this iteration
  makes ZERO changes to (`git diff --stat` against all three is empty). The two CALC_FILES-listed
  files this iteration DOES touch (`scoring.py`, `methodology.py`) are NOT among the reported
  offenders — confirming this iteration introduces no new magic-number violation. Flagging this so
  the reviewer doesn't misattribute a pre-existing, out-of-scope failure to this iteration's diff.

Frontend: `cd apps/frontend && node_modules/.bin/tsc --noEmit` -- exit code 0, zero type errors.
(`next lint` could not be run standalone — this project's `next.config.mjs` has a build guard that
refuses to load without `NEXT_PUBLIC_API_URL` set, by design, per an ops-hardening iter-77 lesson;
`tsc --noEmit` plus the live service-startup check below cover the same class of risk for this
minimal, pattern-matching change.)

## Pre-Handoff Verification

- **Service startup**: ran `scripts/dev.sh` twice in sequence (stop, then start again). Both times,
  backend (`GET /api/health` -> `200`, `preflight.verdict: "GO"`) and frontend (`/` -> `200`) came
  up cleanly with no errors in `logs/backend.log` or the frontend's stdout, and the second start hit
  no port conflicts (ports were fully released before the second launch). Both services were
  stopped cleanly afterward; verified via `ss -tln` that neither port 8255 nor 3255 is listening.
- **Live API spot-checks against the actual running app** (not just pytest):
  - `GET /api/methodology` today omits `universe_selection` entirely (see Known Issues) — confirmed
    this is a pre-existing condition unrelated to this change, not something this iteration broke.
  - `GET /api/stocks` on the currently-stored (pre-iteration) 2026-08-14 run still shows 424/541
    (78.4%) `sector: null`, with GRMN still `null` and DELL still `"Technology"` — i.e., the
    *already-persisted* snapshot is untouched by this code change, which is live, empirical
    confirmation of TC-8 (historical immutability): the stored run was scored under the old
    (pre-fallback) code and reads back byte-identical after this iteration shipped. A fresh
    backfill (J-01's own browser-journey step 1, on `/data`) is required to see the new mapping
    take effect on a *new* run — that live backfill+verification is the browser-qa-agent's step,
    per the plan.
- No new dependency was added (no `playwright install`-style post-install step, no native
  compilation) — this iteration is pure config/Python/TypeScript.

## Known Issues

> **SUPERSEDED FOR `sector_basis` BY THE AUDIT (2026-08-20) — see finding B1 in
> `docs/handoffs/goal-market-compass-iter-1-audit.md`.** Known Issue #1 below remains accurate for the
> *Universe Selection card* (membership rule, thresholds, per-date rule), which is still gated. It is NO
> LONGER true for this iteration's sector-basis disclosure: the audit moved `sector_basis` out of the
> gated `universe_selection` section into the sibling top-level `sector_basis` key that `build_catalog`
> now emits (the spec's own permitted "or a sibling section" alternative), so `GET /api/methodology`
> serves it unconditionally and `/methodology` renders it in its own `SectorBasisCard`. Verified live:
> `curl /api/methodology` top-level keys `['entries','glossary','intro','sector_basis']`, and the card
> renders at 1440x900 (`reports/qa/goal-market-compass-iter-1-evidence/AUDIT-01-methodology-sector-basis-visible.png`).
> The API-layer TC-5 test no longer skips.

1. **Pre-existing, out-of-scope gap: `/methodology`'s `universe_selection` section is not served in
   this environment today.**
   `GET /api/methodology`'s `universe_selection` block is served only when the committed offline
   screen record `apps/backend/data/seed/universe.json` exists (`app/api/methodology.py`'s
   documented "Honest universe gate", J-22 — the universe must not be presented as a reproducible
   screen result before the screen has actually run). That file is **not present** in this repo
   (confirmed via `git ls-files`, a direct `load_universe_screen_record()` call, and a live
   `GET /api/methodology` request against the running app — all three agree: absent). It is built
   only by the separate, manual, `data_manager.py` "Expand" job (J-35, a market-cap-capable-source
   screen), which is unrelated to and out of scope for J-01. **This means the new sector-basis
   disclosure is correctly implemented and unit-tested (`build_catalog()`-level tests pass
   completely, bypassing the API-level gate), but it cannot be visually verified on the live
   `/methodology` page, nor via a plain `GET /api/methodology` call, until someone runs the Expand
   job to build `universe.json`.** This gate predates this iteration and affects the *entire*
   Universe Selection card (membership rule, thresholds, per-date rule), not just the new
   subsection — three pre-existing tests in `test_universe_screen.py`
   (`test_committed_universe_members_all_pass_screen`,
   `test_committed_record_matches_config_universe`, `test_stock_market_cap_read_from_committed_record`)
   already `pytest.skip()` for this exact reason, unrelated to this change. Flagging this clearly
   so QA/browser-qa-agent does not misattribute an unreachable-card finding to this iteration's
   implementation.
2. **Minor, bounded performance note (not a regression risk, flagged for completeness):** the
   fallback adds one `pool_sector_map()` call (a fresh `read_pool()` CSV read + a 548-row dict
   build) to every `score_stocks` invocation. `resolve_members` (called earlier in the SAME
   function) already reads the pool once per call, so this is roughly a second, not a first, CSV
   read per invocation — consistent with this module's existing uncached-by-design convention
   (`read_pool()` is called fresh, uncached, from several call sites already). Not optimized further
   here, matching the "no premature optimization" simplicity bar; worth a look only if a future
   phase's perf budget work flags it specifically.
3. **Pre-existing test failure discovered during full-file verification, proven unrelated to this
   iteration — `test_scoring.py::test_risk_budget_values_ride_the_row_but_enter_no_score` FAILS on
   this iteration's branch, but the evidence shows it would fail identically on a clean `main`
   checkout with none of J-01's changes applied:**
   - The failing assertion (`assert not (risk_budget_keys & set(weights))`, where `risk_budget_keys`
     includes `"atr_pct"`) fails because `config.yaml`'s `scores.risk.weights` block contains
     `atr_pct: 0.15` (line 745).
   - `git diff --stat -- config.yaml` for this iteration shows **10 insertions, 0 deletions** — a
     purely additive diff (my two new keys only: `universe.pool_sector_aliases` at ~line 271 and
     `methodology.universe_selection.sector_basis` at ~line 1406). The `scores:` block (line 725+)
     is untouched.
   - `git blame -L 740,750 config.yaml` shows every line in the `scores.risk.weights` block,
     including the `atr_pct: 0.15` line, traces to commit `63cba98d7` (2026-05-29) and has not been
     touched since — three months before this iteration and long before the failing test existed.
   - `git log -S "test_risk_budget_values_ride_the_row_but_enter_no_score" --oneline` shows the test
     itself was introduced in commit `b6f22d49` ("goal(mcp-loop): iter 40"), an already-completed,
     since-archived session unrelated to market-compass.
   - **Likely root cause (diagnostic only — not fixed here, out of scope):** `scoring.py`'s own
     comments (search "REUSE the values already computed above") state that `risk_budget.atr_pct`
     and `risk_budget.downside_vol` are deliberately REUSED from the SAME raw values that already
     feed the Risk score's weighted blend — unlike `gap_profile`, `worst_20d_window`, and
     `distance_to_invalidation_pct`, which are genuinely new, score-independent values. The test's
     `risk_budget_keys` set appears to have included `atr_pct`/`downside_vol` by mistake alongside
     the three fields that actually need the "never overlaps a score weight" guarantee — this looks
     like a latent assertion bug from iter-40 itself, invisible until a full (not file-scoped) run
     of this specific test happened to be checked carefully, which — per this project's own
     documented "full suite is never run by pipeline agents" policy — apparently hadn't occurred
     since. **No code in this iteration touches `scores.risk.weights`, the risk_budget block, or
     this test.** Recommend the reviewer/auditor decide whether to file this as its own tracked
     issue; J-01's scope is sector attribution only, and this is a scoring-weights/risk-budget
     interaction from an unrelated, already-shipped feature.

## Suggested Next Phase

Per goal.md's own suggested build order and iter-1's own NOTES, the next iteration should tackle
the J-02/J-03/J-04 engine cluster (session delta, plain-English summary, next-session candidate
selection) that shares one manifest producer — or split into J-05/J-06 (the manifest freeze +
immutability pair) first if the decomposer judges the cluster too large for one iteration. Before
that work starts, the owner may also want to run the offline "Expand" job to build
`data/seed/universe.json` — not because any J-02..J-08 journey requires it, but because it would
let the pre-existing Universe Selection card (and this iteration's new sector-basis subsection)
actually render on the live `/methodology` page, closing the visibility gap documented above.
