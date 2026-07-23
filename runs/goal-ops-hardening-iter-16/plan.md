# goal-ops-hardening-iter-16 Execution Plan

## What to Build
- Split the existing `forward_aggregates_cached` (`apps/backend/app/engine/forward_testing.py:1016`) into
  two roles:
  - **Ingest-only compute-and-persist** — the SOLE remaining caller of `compute_forward_aggregates`
    (line 782, byte-identical, untouched); invoked only from `_refresh_ingest_aggregates`'s existing
    per-horizon warm loop (`data_manager.py:3215-3242`, loop/trigger unchanged); keeps iter-15's
    single-flight lock/in-flight-event guard (lines 1002-1013) UNCHANGED.
  - **Read-only serving path** — the only code `GET /api/backtest` and MCP `query_backtest` call from
    now on; structurally incapable of calling `compute_forward_aggregates` (no compute-fallback branch
    at all, including on a lock-wait timeout).
- Read-only resolution must run ONCE per request across ALL configured horizons together (not as today's
  per-horizon-independent dict comprehension — this is the crux of the redesign). For the requested
  `asof_key`, find the latest `dataset_version` for which every horizon in `cfg.walk_forward.horizons`
  (5 today) has a stored row ("complete"), then serve:
  - `ready` — that complete version IS the current global `_dataset_version` stamp.
  - `refreshing` — the current stamp isn't complete yet, but a PRIOR complete version exists; serve that
    older version's full row set byte-identically (all 5 horizons from the SAME version — never mixed),
    labeled with its own `created_at`.
  - `not_yet_computed` — no complete version has ever existed for this `asof_key`: `evidence_by_horizon
    == {}`, `evidence_generated_at == null`, HTTP 200 (never 500/503, never a synchronous compute).
- Change `ForwardAggregateCache` pruning from per-horizon-write deletion to a cutover: a superseded
  version's rows for an `asof_key` survive until the NEW version's full horizon set is confirmed
  complete. (Today's bug, confirmed live, not hypothetical: `asof_key='2026-07-17'` is already split
  across two `dataset_version`s across its 5 rows — proof a naive newest-row-per-horizon read already
  mixes versions today.)
- The completeness-lookup query is filtered by the requested `asof_key` only — never an unfiltered scan
  of `forward_aggregate_cache` (AG-8 spirit; TC-18).
- `backtest.py` (`GET /api/backtest`, lines 71-79) and `mcp/tools.py` (`query_backtest`, lines 204-211):
  both switch their per-horizon dict-comprehension call site to the new read-only resolver and both add
  `evidence_status` + `evidence_generated_at` to the response dict.
- `data_manager.py:3230`'s one call site (inside the existing horizon loop; loop/trigger/MemoryError
  handling unchanged) switches to the new ingest-only function.
- Call-count instrumentation (mirrors this test file's existing monkeypatch-counter idiom) proving
  `compute_forward_aggregates` is invoked ONLY by the ingest warm's horizon loop and ZERO times from
  either request-serving path, across ready / refreshing / not_yet_computed.
- Frontend: `lib/api.ts` adds the two new `BacktestResponse` fields; `backtest/page.tsx`'s
  `BacktestResults` renders a new refreshing banner (alongside the still-populated
  `EvidenceAggregateSection`) or the existing `EmptyState` component (replacing today's silent
  `{evidence ? (...) : null}` omission) or nothing extra when `ready` (regression guard).
- `reports/perf-budgets.md` gains one new dated section (all 3 serving states vs. the committed ≤1.5s
  `/backtest` budget) from the ONE operator-supervised pass (TC-16), sequenced strictly after targeted
  tests are green.
- Dev handoff at `docs/handoffs/goal-ops-hardening-iter-16-dev.md`.

This is squarely additive to goal.md's Improvement Direction (compute-at-ingest / serve-from-storage) and
reproduces J-08 verbatim — no scope creep or goal.md drift detected.

## Agents Required
- developer: yes -- implements the full backend split + frontend disclosure + targeted tests +
  perf-budgets.md update in ONE pass (this project's established single-developer convention since
  iter-7; no separate frontend-handoff file expected).
- backend-data: yes -- `forward_testing.py` compute/serve split + completeness/cutover pruning,
  `backtest.py`, `mcp/tools.py`, `data_manager.py` call-site update, `test_forward_testing_concurrency.py`
  (or a sibling file) extensions. (Same developer as above — not a second dispatch.)
- frontend-ux: yes -- `lib/api.ts` type addition + `backtest/page.tsx` refreshing-banner/empty-state
  rendering, additive to the existing `/backtest` page only. (Same developer as above — not a second
  dispatch.)

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/engine/forward_testing.py` -- split `forward_aggregates_cached` into the ingest-only
  compute-and-persist function (keeps the iter-15 single-flight guard) and a new read-only serving
  resolver (never calls `compute_forward_aggregates`); change pruning to a completeness-gated cutover;
  add the `asof_key`-filtered completeness query. `compute_forward_aggregates` itself (line 782) stays
  byte-identical — do not touch its body/signature/columns (binding "Do not redo").
- `apps/backend/app/models.py` -- touch ONLY if the cutover genuinely cannot be derived from
  `ForwardAggregateCache`'s existing `(horizon, asof_key, dataset_version, created_at)` columns; if so,
  add the smallest possible marker inside this SAME table (never a second cache table) and flag it
  plainly in the dev handoff (the spec's own escalation flag).
- `apps/backend/app/api/backtest.py` (lines 71-79) -- call the new read-only resolver ONCE per request
  for all configured horizons together (not a per-horizon loop); add `evidence_status` +
  `evidence_generated_at` to the response.
- `apps/backend/app/mcp/tools.py` (`query_backtest`, lines 204-211) -- identical switch, identical two
  new fields, mirroring the endpoint per this function's own docstring convention.
- `apps/backend/app/engine/data_manager.py` (line 3230, inside `_refresh_ingest_aggregates`) -- update
  the one call site to the new ingest-only function name; the surrounding per-horizon loop / trigger /
  `MemoryError` handling is UNCHANGED.
- `apps/backend/tests/test_forward_testing_concurrency.py` (or a small sibling file, matching this
  module's per-concern-file convention) -- add completeness/cutover tests, the never-computed test,
  call-count-zero tests for both serving paths, TC-17 (single-flight still holds on the ingest-only path
  post-split), TC-18 (completeness query is `asof_key`-filtered). Name tests descriptively — never
  `test_tc1_`/`test_tc2_` (this file already carries OTHER TCs' own locally-scoped numbering; iter-15's
  naming-collision lesson applies again to this iteration's own TC-1…TC-18).
- `apps/frontend/lib/api.ts` (`BacktestResponse`, ~line 1078) -- add
  `evidence_status: "ready" | "refreshing" | "not_yet_computed"` and
  `evidence_generated_at: string | null`.
- `apps/frontend/app/backtest/page.tsx` (`BacktestResults`, ~lines 183-236) -- on `refreshing`, render a
  new small banner (borrowing `WarmingState`'s Card + `Loader2` visual idiom as a LOOK reference only —
  do NOT wire it to `useReadiness()`, a distinct boot-time concept per the spec) alongside the
  still-rendered `EvidenceAggregateSection`; on `not_yet_computed`, render the existing `EmptyState`
  component (already imported line 7, already used elsewhere on this same page at line ~481) in place of
  the evidence section, copy along the lines of "Backtest evidence not yet computed — run an ingest"; on
  `ready`, render exactly as today (TC-12 regression guard).
- `reports/perf-budgets.md` -- new dated section, TC-16's operator-supervised numbers for all three
  states vs. the existing ≤1.5s `/backtest` budget (same file, no second artifact).
- `docs/handoffs/goal-ops-hardening-iter-16-dev.md` -- new dev handoff.
- `runs/goal-session-ops-hardening/state/blueprint.md` -- light-touch: confirm/correct the decomposer's
  already-pre-drafted J-08 paragraph to reflect what was ACTUALLY built, per this session's iter-15
  precedent — never upgrade its language to "evaluator-confirmed."

**Out of scope (do not touch):** the four sibling ingest-time caches (`event_study_cached`,
`market_phase_cached`, `compute_drawdown_expectations_cached`, `index_series_cached_with_status`);
`uvicorn --workers`; `compute_forward_aggregates`'s own body; the historical (`is_latest==false`)
`?as_of=` path's existing lazy create-once-and-cache behavior; `main.py`, `app/api/health.py`,
`app/engine/readiness.py`, `app/engine/warmup.py`, `scripts/automation/*`; any new DB table, nav entry,
page, or route; a full pytest-suite run.

## UI Evolution (required if Frontend Present: yes)
- New user-facing capability: none new to WHAT a user can do — read-only status disclosure only.
- New information displayed: the forward-aggregate evidence's serving status (`ready` / `refreshing` /
  `not_yet_computed`) and the served version's generation timestamp, on the EXISTING `/backtest` evidence
  section.
- New user actions: none — no new buttons, forms, or controls.
- UI surface changes: the existing `/backtest` page's bottom evidence section gains a status banner
  (refreshing) or an explicit empty state (not-yet-computed) in place of today's silent omission; no new
  page, panel, or route.
- Navigation changes: none.

## Visual Requirements (required if Frontend Present: yes)
- Component patterns: reuse `Card` (`components/ui/card`) + `Loader2` for the refreshing banner's LOOK
  ONLY (matching `WarmingState`'s / this same page's `SurvivorshipBanner`'s established warn-toned
  idiom) — a genuinely new, small presentational piece, not a reuse of `WarmingState`'s `useReadiness()`
  wiring. Reuse the existing `EmptyState` component directly via its `title`/`description`/`icon` props
  for `not_yet_computed` (same component this page already calls in `ScorecardSection`).
- Layout: refreshing banner renders ABOVE/alongside the still-fully-populated `EvidenceAggregateSection`
  (never replacing it, never a skeleton); `not_yet_computed` renders `EmptyState` IN PLACE of the
  evidence section (where `{evidence ? (...) : null}` silently renders nothing today); `ready` is
  unchanged (no banner, no empty state — TC-12).
- Key visual effects: warn-toned (`border-warn`/`text-warn`) card for refreshing, matching this page's
  own existing `SurvivorshipBanner`/`WarmingState` treatment — calm and factual, never alarming (goal.md
  Design Direction). Dashed-border neutral card (`border-dashed border-border-strong`) for the
  not-yet-computed empty state, matching `EmptyState`'s existing convention already used elsewhere on
  this same page.
- States to handle: `ready` (unchanged, regression guard TC-12), `refreshing` (banner + populated
  section, TC-10), `not_yet_computed` (empty state, no horizon numbers, rest of page — scorecard,
  leadership lists, as-of scan summary — unaffected, TC-11).

## Key Test Scenarios
- **Zero-compute correctness** (TC-1/2/6/7/8): `GET /api/backtest` and MCP `query_backtest`, called
  repeatedly (10x) in `ready` and `not_yet_computed` states, invoke `compute_forward_aggregates` exactly
  0 times; the ingest warm's own loop invokes it exactly once per horizon (5 total) when computing a
  fresh version.
- **Completeness/cutover correctness** (TC-3/4/5/18): with a new version's warm 2-of-5 horizons
  complete, `/backtest` keeps serving the PRIOR complete version byte-identically, labeled `refreshing`,
  within budget, with ALL 5 horizons from that SAME version (never mixed); once the new version's 5th
  horizon lands, cutover flips to `ready` and the old version's rows are pruned; the completeness query
  touches only the requested `asof_key`'s rows (never an unfiltered table scan).
- **Byte-identity** (TC-9, AG-3): a `ready`-state response's `evidence_by_horizon` diffs `==` against a
  direct test-only `compute_forward_aggregates` call for the same inputs, every horizon.
- **Single-flight guard survives the split** (TC-17): ≥4 concurrent ingest-only same-key calls still
  collapse to exactly one `compute_forward_aggregates` invocation within the existing bounded 45s wait —
  regression guard on iter-15's fix.
- **Historical as-of unaffected** (TC-13): a never-warmed historical `?as_of=` still
  computes-once-and-caches on first view, unchanged — the zero-compute guarantee is scoped to
  `is_latest==true` only.
- **Browser-visible states** (TC-10/11/12): refreshing banner + generation timestamp shown alongside the
  populated evidence section; not-yet-computed empty state with no horizon numbers and the rest of the
  page (scorecard/leadership lists) intact; ready renders with no banner/empty-state leak.
- **Anti-goal ties**: AG-3 (byte-identity, TC-9), AG-5 (the fallback never serves a mixed or
  newer-than-labeled state, TC-3/4), AG-8 (no unbounded scan in the new completeness lookup, TC-18) —
  all three must hold, not merely the functional TCs.
- **Targeted suite green** (TC-14): host-guard-confined only (`taskset -c 0-3,8-11`,
  BLAS/OMP/numexpr threads=4) — 0 new failures beyond the carried, unrelated
  `test_db.py::test_create_all_produces_expected_tables`. Never the `loaded_engine`-fixture files
  (`test_api_backtest.py`, `test_backtest_scorecard.py`, `test_mcp_window.py`) or a full suite this
  session — cite their coverage, do not execute them.
- **Regression replay** (TC-15): J-01/J-03/J-04/J-05 stay `passing` via deterministic replay / LLM
  fallback.
- **Live operator-supervised budget confirmation** (TC-16, AG-10-class, ONE pass) — OPERATOR-PERFORMED
  ONLY, sequenced strictly AFTER TC-1…14/17/18 are green: agents cannot start/stop services this session
  (permission classifier; subagent-resume channel broken) and services are currently DOWN. Write this
  step as "request the operator boot `scripts/start-backend.sh` under host-guard confinement (sampler +
  watchdog armed), run a small single-day `/data` backfill, poll `/backtest` through the version bump,
  and report console output / PIDs / timestamps verbatim" — never attempt it directly.

## Constraints & Operational Notes
- Before any command that writes temp files, whoever runs it must first
  `export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-ef08286a.372082" TMP="$TMPDIR" TEMP="$TMPDIR"`
  (this dispatch's environment note).
- No full pytest suite this iteration — targeted files only, host-guard-confined
  (`taskset -c 0-3,8-11`, BLAS/OMP/numexpr threads=4).
- `project-template.md` remains the unfilled generic template (a pre-existing, known condition, not new
  this iteration) — the stack/file details above were confirmed directly against the current codebase
  (FastAPI + SQLModel backend, Next.js App Router + TypeScript frontend, pytest), not that file.
