# goal-ops-hardening-iter-17 Execution Plan

Spec: `docs/phases/goal-ops-hardening-iter-17.md` · Target journeys: J-06, J-07, J-08 ·
Required-still-passing: J-01, J-03, J-04, J-05 · Depth: **full**

## What to Build

1. **Cross-`asof_key` last-good fallback (the load-bearing fix).** Widen
   `resolved_forward_aggregate_evidence` (`apps/backend/app/engine/forward_testing.py:1163-1242`) so that
   when the REQUESTED `asof_key` has no complete `dataset_version`, it searches OLDER `asof_key`s (never a
   later one — AG-5) and serves the most recent one that IS complete, labeled `refreshing`. Reserve
   `not_yet_computed` for the true fresh-install shape (no `asof_key` has ever had a complete version).
   Today the completeness read is filtered to exactly one `asof_key` (line 1209) while `backtest.py:70`
   resolves the default view to the latest run — so the common single-latest-date backfill wrongly serves
   `not_yet_computed`. Any new live test MUST use an as-of-**advancing** ingest date, never a historical gap
   date (both iter-16 live passes used gap dates and structurally could not hit this — iter-16's own
   lesson).
2. **New `evidence_asof` field** on the SAME returned dict (`ready` → the requested as-of; `refreshing` →
   the older served as-of; `not_yet_computed` → `null`). Thread it through `GET /api/backtest`
   (`apps/backend/app/api/backtest.py:87-93`) and MCP `query_backtest`
   (`apps/backend/app/mcp/tools.py:215-221`) — both already destructure this dict; extend it, never add a
   second source.
3. **New backend tests** in `apps/backend/tests/test_forward_testing_serving_split.py`: as-of-advancing
   fallback (TC-1), regression guard for the true-empty fresh-install shape (TC-3, existing
   `test_evidence_not_yet_computed_before_any_warm` fixture unchanged), multi-older-key tie-break (TC-4),
   no-lookahead SQL inspection mirroring the existing TC-18 test's `before_cursor_execute` technique
   (`test_completeness_query_is_filtered_by_asof_key`) (TC-5), historical create-once-and-cache regression
   guard mirroring `test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior` (TC-6).
4. **Root-cause the 11/68 `/backtest` latency breaches** (max 12.655s, all inside the ingest window).
   `config.yaml:106-108`'s `database.pragmas` already runs WAL+NORMAL with a 30s `busy_timeout_ms` — treat
   that as read-only context, not the fix target; investigate the ingest finalize hook's write pattern
   (`data_manager._refresh_ingest_aggregates` / `_persist_per_date_coverage_snapshots`) for
   writer/checkpoint-lock contention (iter-11's lesson: rule it in/out with `logs/backend.log` +
   `logs/hwmon/hwmon.csv`, not a plausible story). Apply a bounded mitigation if tractable in scope, else
   record the residual as a disclosed, unavoidable contention cost. Take audit **B5** regardless (cheap,
   adjacent): the historical branch (`backtest.py:80-87`, `tools.py:208-215`) reads and deserializes each
   horizon payload twice.
5. **Frontend:** `RefreshingEvidenceBanner` (`apps/frontend/app/backtest/page.tsx:263-282`) gains an
   `evidenceAsof` prop and displays which as-of's evidence is being shown, not only the generation
   timestamp (the literal J-08 step-2 wording).
6. **Frontend hygiene:** reword the `not_yet_computed` `EmptyState` (`page.tsx:236-240`) — de-duplicate the
   repeated opening sentence (audit F3) and soften the "run an ingest" phrasing so it never presumes a
   user hasn't already started one (audit F2). Should already be moot once item 1 lands; confirm and tidy
   regardless.
7. **Non-blocking:** add a UTC timezone designator to `evidence_generated_at`'s ISO-8601 serialization
   (audit B3) while the field is young.
8. **Live browser evidence:** the as-of-advancing `refreshing` case via a small ADVANCING-date backfill
   through the existing `/data` job form (TC-8 — agent/QA-performable, no service start/stop) and the
   `not_yet_computed` case on a disposable DB copy (TC-9 — **OPERATOR-only**, throwaway backend boot).
9. **Operator-supervised deep-basis re-measurement** of `/backtest` latency (TC-10, AG-10-class, mirrors
   iter-16's TC-16 protocol exactly), recorded in a new dated `reports/perf-budgets.md` section directly
   comparable to iter-16's baseline (11/68 breaches, max 12.655s).
10. **Non-disruptive J-04 sanity check** (TC-11): one `GET /api/health` poll + a `logs/backend.log`
    crash-banner check — no kill/restart.
11. Dev handoff at `docs/handoffs/goal-ops-hardening-iter-17-dev.md` (+ a frontend handoff, matching this
    session's established convention of a separate `-frontend.md` whenever frontend copy/props change).

## Agents Required

- backend-data: yes -- items 1-4, 7, 9's report write-up, 10 above; new tests in
  `test_forward_testing_serving_split.py`; dev handoff.
- frontend-ux: yes -- items 5-6 above, `apps/frontend/app/backtest/page.tsx` only. (Frontend Present: yes —
  banner prop + empty-state copy only, no new page/route/component.)

## Frontend Present
yes

## Files to Create/Modify

- `apps/backend/app/engine/forward_testing.py` -- widen `resolved_forward_aggregate_evidence`'s
  completeness search across older `asof_key`s; add `evidence_asof` to its returned dict (~1163-1242)
- `apps/backend/app/api/backtest.py` -- add `evidence_asof` to the `/backtest` response dict (~87-93); B5
  cheap win in the historical branch (~80-87) if bundled here
- `apps/backend/app/mcp/tools.py` -- mirror the identical `evidence_asof` addition in `query_backtest`
  (~208-221)
- `apps/backend/app/engine/data_manager.py` -- **investigate only** (`_refresh_ingest_aggregates`,
  `_persist_per_date_coverage_snapshots`); edit only if a bounded write-pattern mitigation is found
- `apps/backend/tests/test_forward_testing_serving_split.py` -- add TC-1, TC-3, TC-4, TC-5, TC-6
- `apps/frontend/app/backtest/page.tsx` -- `RefreshingEvidenceBanner` `evidenceAsof` prop (~263-282);
  `EmptyState` copy fix, F2/F3 (~236-240)
- `reports/perf-budgets.md` -- new dated section: TC-10 measurement + the latency root-cause finding
- `docs/handoffs/goal-ops-hardening-iter-17-dev.md` -- new
- `docs/handoffs/goal-ops-hardening-iter-17-frontend.md` -- new (if frontend-ux follows this session's
  established separate-handoff pattern, e.g. iter-16/-14/-12/-8/-6/-4/-2)

Not for edit: `runs/goal-session-ops-hardening/state/blueprint.md` (the decomposer already appended the
iter-17 Data Contract paragraph with the `[TARGET, iter-17 building]` tag; only the evaluator removes that
tag once confirmed) and `config.yaml` (cited as context for item 4, not a mitigation target).

## UI Evolution

- New user-facing capability: `/backtest`'s evidence section stays populated with honest, labeled
  last-good evidence through the single most common ingest shape (latest-date advance) instead of going
  empty and misdirecting the user.
- New information displayed: `evidence_asof` — the served evidence's own as-of date — shown in the
  refreshing banner alongside the existing generation timestamp.
- New user actions: none — a correctness/disclosure fix to an existing read-only display, no new controls.
- UI surface changes: `RefreshingEvidenceBanner` text gains the as-of label; `not_yet_computed` `EmptyState`
  copy is de-duplicated and reworded. No new page, panel, or route.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the EXISTING `Card` + `Loader2` warn-toned banner pattern
  (`RefreshingEvidenceBanner`) and the EXISTING `EmptyState` component unchanged — no new component this
  iteration.
- Layout: unchanged — banner stays directly above the still-populated evidence section, at the bottom of
  `/backtest` (after the leadership lists, per the established J-21 order).
- Key visual effects: none new — the same warn border/background (`border-warn bg-surface`) and spinning
  `Loader2` icon carry over untouched; this is a copy/prop change only.
- States to handle: `refreshing` (now labeled with the older `evidence_asof`), `not_yet_computed` (reworded
  empty state; needs its first-ever live browser capture, TC-9), `ready` (unchanged). Keep the calm,
  factual, never-hype tone from goal.md's Design Direction; verify every new sentence against the code that
  would have to make it true (iter-16's own lesson on status-disclosure copy — two of its prior banner
  claims were false despite passing every styling/tone check).

## Key Test Scenarios

- TC-1 (backend-data, unit): older-`asof_key` complete + newer zero-row `asof_key` → resolver returns
  `refreshing`, `evidence_asof=<older>`, full horizon set from the older version — never
  `not_yet_computed`.
- TC-2 (backend-data, unit): same fixture — `GET /api/backtest` and MCP `query_backtest` both surface
  `evidence_asof` identically.
- TC-3 (backend-data, unit, regression guard): no `asof_key` ever complete → still `not_yet_computed` /
  `evidence_asof=None` / `{}` — unchanged from today.
- TC-4 (backend-data, unit): two older complete `asof_key`s → served `evidence_asof` is the MORE RECENT of
  the two, never mixed.
- TC-5 (backend-data, unit, no-lookahead/AG-5): the fallback never reads/serves a row dated AFTER the
  requested `as_of` — verify via the same `before_cursor_execute` technique as the existing TC-18 test.
- TC-6 (backend-data, unit, regression guard): historical (`is_latest=False`) fixture — still
  compute-once-then-cache, unchanged by the fallback search.
- TC-7 (frontend-ux): `refreshing` response with an older `evidence_asof` → `RefreshingEvidenceBanner`
  visibly displays the `evidence_asof` date text, not only the generation timestamp.
- TC-8 (agent/QA, browser, no service start/stop — services already up on :8255/:3255): a small
  single-day backfill through the existing `/data` job form for a date that ADVANCES the latest stored
  run; load `/backtest` while that date's warm is incomplete → renders within the ≤1.5s budget, showing
  `refreshing` labeled with the PRIOR `asof_key`'s date (screenshot) — never `not_yet_computed`.
- TC-9 (**OPERATOR-only** — new throwaway process): backend via `scripts/start-backend.sh` +
  `TRENDORA_CONFIG` pointed at a disposable, never-ingested copy of `trendora.db` on an unused port →
  `/backtest` renders the `not_yet_computed` `EmptyState` within budget (screenshot); working
  `trendora.db`'s row counts unchanged before/after. If impractical this session, a documented
  backend-only JSON capture (`evidence_status="not_yet_computed"`, HTTP 200) + confirmation the frontend's
  `EmptyState` call site is unconditionally reached is an acceptable fallback — state which was achieved.
- TC-10 (**OPERATOR-only**, AG-10-class, ONE pass): same deep-basis ingest-window concurrent-poll protocol
  as iter-16's TC-16 (cooled host, sampler, watchdog, `taskset -c 0-3,8-11`, BLAS/OMP=4) → fresh breach
  count + max latency recorded in a new dated `reports/perf-budgets.md` section, directly comparable to
  iter-16's baseline (11/68, max 12.655s).
- TC-11 (agent/QA, non-disruptive, no kill/restart): one `GET /api/health` poll → HTTP 200,
  `readiness:"ready"`; `logs/backend.log` shows no new crash/restart banner since the last recorded one.
- Regression guard: all pre-existing tests in `test_forward_testing_serving_split.py`,
  `test_forward_testing_concurrency.py`, `test_forward_testing.py`, `test_data_manager.py` keep passing;
  J-01/J-03/J-04/J-05 (required-still-passing) stay green via deterministic replay + LLM fallback. Carried,
  unrelated: `test_db.py::test_create_all_produces_expected_tables` (pre-existing, no schema change here).

## Out of Scope (binding — do not touch this iteration)

- `compute_forward_aggregates`'s body (byte-unchanged since iter-14, AG-8 resolved) — not reopened.
- The compute-vs-serve split itself and the cutover pruning logic (`forward_testing.py` ~1122-1160) —
  extend the read-side fallback only; never add a compute branch to the read path.
- `refreshing`'s no-self-heal behavior (audit B2) — a documented trade-off, not built this iteration.
- The `loaded_engine`-dependent test (`test_api_backtest.py::test_backtest_evidence_by_horizon_shape_and_keys`,
  ~80 min) — cite it, do not run it.
- A fresh J-04 kill/restart replay — TC-11's non-disruptive sanity check only; kill/restart stays
  operator-owned and deferred.
- `main.py`, `app/api/health.py`, `app/engine/readiness.py`, `app/engine/warmup.py`, `scripts/*`,
  `scripts/automation/*` — untouched.
- Full pytest suite — targeted, host-guard-confined runs only (`taskset -c 0-3,8-11`, BLAS/OMP=4).
- `demo.sh ops-hardening --session-live` — human-interactive only, not this iteration's deliverable.
- J-06's other 10 idle-host page budgets, the ≤5s boot budget, non-`/backtest` on-load audit — settled
  iter-9/11/13.

## Context Alignment

- Directly advances `docs/goal.md`: J-08's own acceptance criteria — "the refresh window is visibly
  disclosed (served as-of + refreshing indicator)" and "the fallback serves a complete OLDER snapshot,
  never partially newer data (AG-5 preserved)" — are exactly this iteration's B1 fix plus the new
  `evidence_asof` field.
- Builds on iter-16's precompute-before-serve split without reopening its architecture: extends the
  READ-side fallback search only, keeps the same sole-producer/pure-reader shape confirmed in
  `blueprint.md`'s Data Contract (the iter-17 paragraph is already appended there by the decomposer,
  tagged `[TARGET, iter-17 building]`).
- No drift found between the phase spec and `docs/goal.md` / `iteration-state.md`'s "Do not redo" list —
  the spec's own OUT OF SCOPE section already encodes every binding constraint on file; nothing to flag as
  scope creep.

## Operational Notes

- Backend (`:8255`) and frontend (`:3255`) are already running — use them directly for TC-8/TC-11. Agents
  cannot start or stop services this session (permission classifier). TC-9 (disposable-DB boot) and TC-10
  (deep-basis re-measurement) MUST be written in the dev handoff as OPERATOR-performed steps, never
  attempted by an agent.
- Before running tests or any command that writes temp files:
  `export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-b612f488.372082" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-b612f488.372082" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-b612f488.372082"`
