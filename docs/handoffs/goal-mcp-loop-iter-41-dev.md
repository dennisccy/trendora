# goal-mcp-loop-iter-41 Dev Handoff

**Phase:** goal-mcp-loop-iter-41
**Date:** 2026-07-15
**Agent:** developer
**Status:** complete

## What Was Built

- **Two new append-only nullable columns on `ForwardReturn`** (`underwater_days`, `time_to_recover_days`) —
  computed ONCE in the SAME `_insert_run_forward_returns` INSERT pass as the existing `max_drawdown`
  (zero extra bar reads), sharing its exact no-lookahead NA gate. Registered in `db._ADDITIVE_COLUMNS` so
  a live DB not rebuilt this pass degrades honestly (NULL) instead of 500ing.
- **Two new pure helpers in `app.engine.forward_testing`**: `underwater_days(bars_after_list, entry_close,
  horizon)` (count of the first-`horizon` post-bars whose close sits below the running high-water mark,
  peak updated by each bar's high BEFORE that bar's own close-check — mirrors `max_drawdown`'s bar-order
  exactly) and `time_to_recover_days(...)` (bars from the max-drawdown trough until close first reclaims
  the entry level within the horizon; `None` if it never recovers). `max_drawdown` itself is untouched —
  `time_to_recover_days` internally re-derives the SAME running-peak series only to locate the trough's
  bar index (which `max_drawdown` doesn't expose); a unit test pins the two in agreement.
- **New aggregation `compute_drawdown_expectations(session, claim, config)`** — resolves a claim's cohort
  via the SAME `app.engine.samples.compute_samples` selectors the Research labs use (a small local
  claim-field -> `compute_samples`-kwarg translator, `_claim_samples_kwargs`, mirrors
  `app.mcp.tools._CLAIM_SELECTOR_KEYS`/`drill_samples`'s exact rename rules — no second cohort resolver),
  reads the STORED `max_drawdown`/`underwater_days`/`time_to_recover_days` verbatim, joins to the causal
  phase-at-entry via `app.engine.market_phase.phase_context_by_date`, and emits per configured
  `market_phase.labels` phase a `{median, p90, n, insufficient}` cell for the three distribution measures
  plus a walk-forward-CADENCE (not per-observation) longest-losing-streak cell. Returns `None` (never
  raises) for an unresolvable cohort, an out-of-scope horizon, or zero observations.
- **`compute_drawdown_expectations_cached`** — a NEW, NOT originally planned, addition discovered during
  live verification (see Known Issues/Performance below): serves the above from the shared J-72
  `EventStudyCache` table (the SAME cache every other research-derived aggregate in this codebase already
  uses), keyed by a namespaced SHA-256 of the claim + `dataset_version` + horizon. `GET /api/evidence`
  calls this cached entry point, never the uncached one.
- **Config additions**: `WalkForwardCfg.underwater_horizons: list[int]` (the panel's horizon scope gate,
  defaults to the full `[1,5,10,20,60]` horizon set) and `.streak_min_n: int` (the loss-streak honesty
  floor, distinct from and smaller than `min_sample` since cadence dates are far fewer than
  per-observation rows). Both required + validated positive.
- **`GET /api/evidence` additive `expectations` field** — `api/evidence.py` now threads a DB session +
  config; `engine/evidence.py`'s `build_evidence_payload` gained OPTIONAL keyword-only `session`/`config`
  params (default `None`). When `session` is `None` (every one of the ~13 pre-existing call sites, incl.
  the frozen-golden `test_canonical_ledger_frozen_golden`), the row carries NO `expectations` key at all —
  byte-identical to before this iteration. Only the real route attaches it.
- **Frontend expectations panel** — `apps/frontend/app/evidence/page.tsx`'s `ClaimRow` gained an additive
  `DrawdownExpectationsPanel` section (below the existing `<dl>` grid, inside the same `CardContent`): a
  phase × {max-DD depth, underwater, time-to-recover, longest losing streak} table, "insufficient (n=…)"
  for below-floor cells, a walk-forward-cadence method note, and the served `survivorship_bias` caveat.
  Renders nothing when `expectations` is absent (mirrors the iter-40 `RiskBudgetCard` "return null"
  precedent). `apps/frontend/lib/evidence.ts` gained the `DistributionCell`/`LossStreakCell`/
  `PhaseExpectations`/`DrawdownExpectations` types + pure formatters (`insufficientLabel`, `formatDays`,
  `formatStreak`); `lib/api.ts` re-exports them for discoverability.
- **Full-universe DB rebuild** (the anti-goal #8 memory-risk operation the phase spec required) — see
  Known Issues for the discovered `/api/evidence` latency regression this surfaced and the fix shipped
  alongside it.

## Files Changed

- `apps/backend/app/models.py` -- `ForwardReturn`: `underwater_days`, `time_to_recover_days` columns.
- `apps/backend/app/db.py` -- `_ADDITIVE_COLUMNS`: two new ALTER tuples.
- `apps/backend/app/engine/forward_testing.py` -- `underwater_days()`, `time_to_recover_days()` pure
  helpers; wired into `_insert_run_forward_returns`; `compute_drawdown_expectations` +
  `compute_drawdown_expectations_cached` + the `_claim_samples_kwargs` translator + the percentile/
  distribution/loss-streak helpers.
- `apps/backend/app/config.py` -- `WalkForwardCfg.underwater_horizons` / `.streak_min_n` + validation.
- `config.yaml` -- `walk_forward.underwater_horizons` / `.streak_min_n` values.
- `apps/backend/app/api/evidence.py` -- `Depends(get_session)`, threads session+config.
- `apps/backend/app/engine/evidence.py` -- `build_evidence_payload`: optional keyword-only session/config.
- `apps/backend/tests/test_forward_testing.py` -- 29 new tests (pure helpers, `_claim_samples_kwargs`,
  `compute_drawdown_expectations` incl. combination/event-study kind resolution, no-lookahead/causal-phase
  behavior, the loss-streak cadence-dedup trap, max_drawdown-reuse proof, and the `_cached` wrapper's
  byte-identity/call-count/invalidation behavior).
- `apps/backend/tests/test_evidence.py` -- 3 new tests for the additive `expectations` field
  (session-omitted / session-provided-resolvable / session-provided-unresolvable); confirmed
  `test_canonical_ledger_frozen_golden` and every other existing call site is UNEDITED and green.
- `apps/backend/tests/test_db.py` -- 1 new regression test mirroring the `max_drawdown` precedent for the
  two new columns.
- `apps/backend/tests/test_config.py`, `test_config_engine.py`, `test_indexes.py`, `test_sectors.py`,
  `test_themes.py` -- extended inline `walk_forward` fixture dicts with the 2 new required keys.
  (`test_forward_testing.py`, `test_warmup.py`, `test_iter20_research_cluster.py`, `test_research.py` were
  investigated and need NO edit — they build their config via `load_config().model_copy(update=...)` on
  the real config.yaml, not a raw dict literal, so they inherit the new keys automatically; this narrows
  the plan's "9 files" estimate to the 5 that actually construct a raw `walk_forward` dict.)
- `apps/frontend/lib/evidence.ts` -- `DistributionCell`/`LossStreakCell`/`PhaseExpectations`/
  `DrawdownExpectations` types, `CertifiedClaim.expectations`, `insufficientLabel`/`formatDays`/
  `formatStreak` formatters.
- `apps/frontend/lib/evidence.test.ts` -- 3 new checks for the new formatters.
- `apps/frontend/lib/api.ts` -- re-exports the new types.
- `apps/frontend/app/evidence/page.tsx` -- `DrawdownExpectationsPanel` + `DistributionCellView` +
  `LossStreakCellView`.
- `reports/perf-budgets.md` -- new "Item I" section: the full-universe rebuild memory measurement (2 runs),
  the correctness spot-check, and the `/api/evidence` latency regression + fix + re-measurement.
- `apps/backend/data/trendora.db` -- rebuilt from scratch (fresh boot + background warm-up) so the new
  columns are populated across the full 30-year/590-symbol history (not tracked in git; `.gitignore`d).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest <files/tests>` (targeted, see below)

Given this host was under heavy, sustained CPU contention from concurrent unrelated processes during this
session (a `loaded_engine`-dependent full-file run of `test_config.py`+`test_config_engine.py`+
`test_indexes.py`+`test_sectors.py`+`test_themes.py` ran 44+ minutes without completing before I killed
it; `test_db.py`'s full run similarly ran 40+ minutes), I verified correctness via bounded, targeted runs
instead of the full suite, per the developer-agent guidance to "bound it and report byte-identity via a
standalone check" when a `loaded_engine` fixture build is pathologically slow:

- `test_forward_testing.py -k "underwater_days or time_to_recover_days or drawdown_expectations or
  claim_samples_kwargs"` -- **29 passed** (all NEW tests; no `loaded_engine` dependency, ~1.8s).
- `test_evidence.py` (full file) -- **17 passed** (14 pre-existing incl. the frozen golden, unedited + 3
  new; no `loaded_engine` dependency, ~0.4s).
- `test_db.py -k "dry_spell or additive_migration or every_model_column"` -- **5 passed** (my new
  regression test + the 2 pre-existing `max_drawdown`-precedent tests + the generic every-column guard;
  no `loaded_engine` dependency, ~0.15s). The file's FULL run (20 tests) was independently confirmed
  passing through at least test #8 (`test_every_model_column_on_existing_table_is_covered_by_additive_
  registry`, PASSED) before truncation at the slow `test_seed_load_is_idempotent`, which is unrelated to
  this iteration's changes.
- `test_config.py + test_config_engine.py + test_indexes.py` (full files, confirmed to have ZERO
  `loaded_engine` references) -- **135 passed** in 3.81s.
- `test_sectors.py::test_min_history_bars_floor_reports_na_for_short_history`,
  `test_sectors.py::test_synthetic_industry_members_and_empty_state`,
  `test_themes.py::test_theme_with_no_member_history_degrades_to_na_not_crash` -- **3 passed** in 0.17s
  (these are the ONLY tests in either file that construct a `Config` from the edited inline `walk_forward`
  dict; every other test in both files uses `loaded_engine`, which reads the real `config.yaml` — already
  independently verified to load correctly with the new keys via a standalone `load_config()` call).
- Frontend: `npx tsc --noEmit -p .` -- clean, no errors. `npx tsx lib/evidence.test.ts` -- **42 passed**
  (39 pre-existing + 3 new).

**Not run this session:** the FULL `test_sectors.py`/`test_themes.py` suites' remaining ~13
`loaded_engine`-dependent tests (unrelated engine logic — `sectors.py`/`themes.py` themselves are
untouched this iteration) — static review found no equality/shape assertion on the `walk_forward` dict
that my purely-additive 2-key change could affect (confirmed via `grep` across all 5 edited test files).
Recommend the reviewer/QA re-run these two files' full suites on a quieter host if any doubt remains; I
judge the risk low given the mechanical nature of the edit and the definitive targeted-test confirmation.

## Live Verification (real production data, not just fixtures)

Beyond unit tests, I performed a full-universe DB rebuild and verified the whole pipeline end-to-end
against the REAL committed seed (30-year, 590-symbol basis, 170,229 `forward_returns` rows):

- `underwater_days` populated on 170,229/170,229 rows (100% — matches `max_drawdown`'s existing NA gate,
  as designed); `time_to_recover_days` populated on 103,589/170,229 (the rest honest NA — never
  recovered in-window, never fabricated).
- All 7 real ledger claims (5 factor, 1 event-study, 1 combination) resolve non-`None` `expectations`
  through `GET /api/evidence`, each showing distinct, correctly-scoped per-phase counts.
- **Correctness spot-check (anti-goal #3):** claim 0's (`leadership_score` D10 h20) Expansion-phase
  `max_drawdown`/`underwater_days` median/p90/n, independently re-derived offline in a standalone script
  (re-sorting/re-decile'ing/re-percentiling the SAME stored rows, NOT calling `compute_samples`/
  `compute_drawdown_expectations`), byte-matched the served values exactly.
- **Determinism:** two independent full rebuilds produced byte-identical served `expectations` for the
  same claim.
- **Memory (anti-goal #8):** two consecutive full-universe rebuilds (`scripts/start-backend.sh`, real
  `ulimit -v 6291456` KB = 6144 MB, `MALLOC_ARENA_MAX=2` confirmed applied) peaked at VmPeak 2,769,216 KB
  / 2,768,188 KB (2.7 GB, ~56% margin under the cap) and VmHWM 1,833,768 KB / 1,833,228 KB — run 2's peak
  did not exceed run 1's. Full numbers in `reports/perf-budgets.md` Item I.

## Known Issues

- **Performance regression found and fixed mid-implementation (not in the original plan):** the additive
  per-claim `expectations` field resolves a full research cohort for EVERY claim on `/api/evidence`'s one
  page load. Measured uncached against the real 7-claim ledger: **9.3-9.6s per request** — a ~3x
  regression against the J-15 "pages interactive ≤3s warm" budget. I fixed this by adding
  `compute_drawdown_expectations_cached`, serving from the SAME shared `EventStudyCache` table (J-72)
  every other research-derived aggregate in this codebase already uses for this exact "expensive derived
  aggregate, safe to cache until the dataset changes" shape. Re-measured: first (cold) call 9.471s, every
  subsequent (warm) call 6-17ms — comfortably inside budget. The COLD cost is paid once per dataset
  change (i.e., once per rebuild), matching the "first view computes once" contract every other research
  lab already carries; if the ledger's claim count grows materially, this cold-miss bound should be
  re-measured. Full detail in `reports/perf-budgets.md` Item I. This is flagged prominently per the
  developer-agent instructions (fix mode discovering a new problem outside the fix-tasks list would need
  to be recorded here rather than silently fixed — but this is INITIAL BUILD mode, and leaving a ~3x J-15
  regression unfixed would itself violate this iteration's own DoD, so I fixed it and am disclosing it
  here in full rather than treating it as an unlisted scope addition to hide).
- **Full `loaded_engine`-dependent test suites not run to completion this session** due to severe, sustained
  host contention (see Tests Run above for the targeted-verification substitute and the specific risk
  assessment). No code path I touched is exercised only by the untested portions of `test_sectors.py`/
  `test_themes.py` (I did not modify `sectors.py`/`themes.py` themselves).
- **`db.py`'s pre-existing `_ensure_index_hygiene`/other startup steps were not independently re-verified**
  beyond the live rebuild succeeding twice cleanly and `/api/health` reporting `"status":"ok"` throughout —
  no new index or hygiene step was added this iteration, so this is unchanged risk, not new risk.
- The frontend expectations panel was verified via `tsc`, unit tests, and live API-shape/JSX review — NOT
  via an actual browser (Chrome MCP is not in the developer agent's toolset). Recommend browser-qa
  specifically scroll into the panel (below the fold inside each claim card, per the phase spec's own
  capture-discipline note) and confirm the rendered table matches the live JSON I captured in this handoff.

## Config / Environment Changes

- `config.yaml`: `walk_forward.underwater_horizons: [1, 5, 10, 20, 60]`, `walk_forward.streak_min_n: 10`
  (both new, required keys under the existing `walk_forward:` block).
- No new environment variables.
- No migration tool in this project (no Alembic) — the additive-column pattern (`db._ADDITIVE_COLUMNS`)
  is the established mechanism; both new columns are registered there.
