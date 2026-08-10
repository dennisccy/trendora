# Goal Iteration 57 — Close J-06: fix the Data page's during-a-job lie, the last two budget breaches, and give the golden real teeth

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 57
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — the last evaluator verdict (iter-56) was ESCALATE, which mandates full depth with no exceptions.
- **Frontend Present:** yes
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-08, J-09
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
    **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
    values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha
    claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
    never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the
    post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every
    existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error
    boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded
    whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only
    against the committed seed / local provider fixtures — no live external network calls or
    paid data services may be introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills,
    full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched
    only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those
    scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env`
    whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`,
    `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD
    marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings
    are a physical constraint of the current host (two instant hardware resets under all-core
    vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to
    optimize away. *(Owner amendment 2026-07-31, two corrections of record — nothing above is
    relaxed: `memory_cap_mb` / `malloc_arena_max` live in `config.yaml`, not in `host-guard.env`;
    and the 2026-07-20/21 resets were subsequently attributed to an uncorrected hardware
    data-fabric fault (`host-guard.env`, 2026-07-30), so the ceiling VALUES are an owner-set
    envelope — re-set by the dated entry in "Additional binding notes" below — while this
    paragraph's prohibition on agents removing, weakening, or bypassing caps is unchanged.)*
    *(critical)*

## GOAL

Close J-06 ("Pages load only what they need") for real: stop the Data page from telling the operator
there is no data while a job is running, close the last two over-budget page calls
(`GET /api/health`, `GET /api/stocks/{ticker}/bars?through=latest`), and make J-06's own golden assert
real budgets instead of page headings — so the journey's PASS is finally trustworthy.

## BACKGROUND

Iter-56's own verdict was **ESCALATE** (mandatory full depth, trigger 3, no exceptions): it was
dispatched **lean** against its own `Depth: full` spec, so no audit ran, and its real headline fix — the
ingest-time `availability_from_storage` cache — introduced a NEW honesty defect no lane caught: for the
entire duration of any ingest job (~20 minutes), `/data` renders "No availability yet — Fetch real EOD
prices" over a 3.3M-row database, because the cache's MISS path only ever checked the row for the
CURRENT dataset_version stamp and that stamp changes on the job's first committed bar (iter-56 lesson,
first entry). The same round's own evaluator confirmed two of J-06's four historically over-budget calls
are now fixed (`/api/runs`, `/api/data/availability`, both PASS) but the other two — `GET /api/health`
(241ms/0.16s vs a committed ≤0.1s steady-state ceiling) and `/api/stocks/{ticker}/bars?through=latest`
(6.2s, Addendum 18, never re-measured) — were never named in the iter-56 spec (iter-56 lesson, second
entry: "a journey's gap list lives in `journey-history.json`, not in the previous round's prose"). This
iteration is built from `journey-history.json`'s own authoritative J-06 gap list plus the iter-56 eval's
explicit next-step order, not from any summarized prose.

**Priority rubric applied.** No journey regressed (rule 1). The last coherence verdict was
COHERENCE-WARN, not FAIL (rule 2 — no mandatory consolidation-only iteration, though this iteration does
close the coherence-auditor's one advisory finding, the MCP `list_runs` stale duplicate, as a
low-risk rider). J-06 is the clear **unblocker** pick (rule 3): it is the session's longest-open Must-have
journey (`last_passing=iter-45`), its remaining gaps are all named and agent-actionable (not human-
blocked), and its closing fix shares the Availability heatmap / Backend readiness Data-Contract surfaces
this iteration must touch anyway. Only ONE risky journey is targeted (rule 5) — J-05 and J-07 are
deliberately NOT targeted this round (see OUT OF SCOPE); J-05's own remediation work is already
"Do not redo"-complete and gets a re-verification ride in Required-still-passing rather than new scope.

**Lessons applied (matched by "Applies to"):** (1) iter-56's first lesson — any ingest-time cache must
decide explicitly whether a stamp-miss means "serve the previous value with an as-of marker," "say
updating," or "say empty"; this iteration picks "serve the previous row with an honest `stale`/
`served_dataset_version` marker," reserving the empty sentinel strictly for a DB where no row has EVER
been persisted. (2) iter-56's second lesson — this spec's target list comes from `journey-history.json`'s
own note, not a prior round's summary. (3) iter-52's first lesson — a golden must assert a value the
endpoint actually produced, never a bare heading; J-06's golden gains real budget assertions this round.
(4) iter-55's first lesson — J-05's golden is a single-use, date-consuming fixture; including it in
Required-still-passing this round will consume its rotated date (2010-11-10) again, and a future
iteration must rotate it before J-05 is next replayed (flagged in NOTES, not this iteration's job to
pre-empt). (5) iter-53's first lesson — a recurring pipeline-ordering failure is fixed by writing it into
the DoD as a binding rule, not by exhortation; TC-14 below restates the lane-runs-last / audit-fix-
findings-only rule as a checkbox, mirroring iter-53's own TC-7/TC-9 (which held the one round it was
written this way).

## IN SCOPE

### Backend

- [ ] Extend `availability_from_storage` (`app.engine.data_manager`) so that on a stamp mismatch it
      first checks whether ANY `AvailabilityCache` row exists (regardless of dataset_version) and, if
      one does, serves that row's `cells`/`total_symbols`/`trading_day_count` with `stale: true` and
      `served_dataset_version` set to that row's own stamp — instead of the not-yet-computed empty
      sentinel. Reserve the empty sentinel strictly for a DB where no `AvailabilityCache` row has ever
      been persisted (`stale: false`, `served_dataset_version: null`). No schema change, no second
      producer, no second endpoint (`compute_availability` and `GET /api/data/availability` unchanged).
- [ ] Profile `GET /api/health` (`app/api/health.py`) first, then remove its per-call database cost
      (candidate, to be confirmed by profiling: the per-request `count(distinct(symbol))` scan has no
      supporting index for a fast DISTINCT count and can likely be served from an already-computed
      universe count instead) so steady-state reads return to the committed ≤0.1s ceiling. Preserve the
      owner-amended relaxed ≤2s ceiling for polls during a bounded background-compute window unchanged —
      this is a steady-state fix only, not a change to that separate contract clause.
- [ ] Profile `GET /api/stocks/{ticker}/bars?through=latest` (`app/api/stocks.py` →
      `app.engine.prices.bars_through_latest`) first — record the query plan / row count / wall-clock
      breakdown in the dev handoff — then fix whatever the profiling names as the bottleneck, keeping
      the existing lazy-indexed-query convention (no precompute, no whole-table load; this endpoint is
      explicitly user-parameterized per goal.md's "cannot be precomputed" list).
- [ ] Fix `availability_cached_with_status` (`data_manager.py:1660-1663`) and its sibling
      `index_series_cached_with_status` (`indexes.py:275-278`) so that when their `try: session.commit()`
      raises and the `except` block rolls back, both return `persisted_this_call=False` — never `True`
      for a write that did not durably persist (closes an AG-3 honesty gap feeding the existing
      `aggregates_refreshed` field; no field/schema change).
- [ ] Point `app.mcp.tools.list_runs` (`tools.py:706-731`) at the same grouped
      `GROUP BY ScannerResult.run_id` aggregate query `app.api.runs.runs` already uses, replacing the
      per-run `ScannerResult` COUNT-in-a-loop pattern the coherence-auditor flagged as a stale duplicate
      (`coherence.md` iter-56 advisory). Same tool, same response shape, byte-identical `n_stocks`.
- [ ] Correct the measurement-note calendar-span label named in the iter-56 eval (`reports/perf-
      budgets.md` Addendum 20 reads "1996-2026"; `compute_availability`'s actual SPY-benchmark trading
      calendar spans ~2005-2026, ~5,391 days). `reports/perf-budgets.md` is append-only — add a dated
      correction note; do not rewrite the historical entry.
- [ ] Rewrite `journey-scripts/J-06.json` so its steps for the pages that call `/api/runs`,
      `/api/data/availability`, `/api/health`, and `/api/stocks/AAPL/bars?through=latest` each assert a
      measured latency at or under that call's committed budget, in addition to their existing heading
      text — not a heading-only match (closes the same defect class the iter-52 lesson named for the
      Regime Lab golden).
- [ ] Run `apps/backend/tests/test_api_runs.py` ALONE, FIRST — before any other test file and before any
      other dev work this iteration — and record its result (pass/fail, honestly) in the dev handoff
      before proceeding; it has been killed twice at 30+ minutes when run inside the full suite.
- [ ] Add/extend unit tests: byte-identity for the availability stale-serving fallback, for the fixed
      `/api/health` field, and for the fixed `/api/stocks/{ticker}/bars` path (each against the pre-fix
      live computation for the same DB state); a fault-injection test for the `persisted_this_call`
      rollback fix in both `data_manager.py` and `indexes.py`; a byte-identity test for the `list_runs`
      MCP fix.

### Frontend

- [ ] `apps/frontend/components/availability-heatmap.tsx`: when the `/api/data/availability` response
      has `stale: true`, render the existing heatmap cells (never the empty state) plus a visible
      "Data as of `<served_dataset_version>` — updating" banner. When `stale: false` and `cells` is
      non-empty, render unchanged (today's behavior). When `stale: false` and `cells` is empty (the
      genuinely never-ingested case), keep today's "No availability yet — Fetch real EOD prices" message
      — this is the ONLY case that message is honest for.

### New user-facing capability

During an active ingest job, `/data`'s availability heatmap now shows the real previous heatmap with an
honest "as of / updating" banner instead of falsely claiming no data exists. `GET /api/health` and the
single-stock bars call return within their committed budgets.

### New information displayed

A "Data as of `<served_dataset_version>` — updating" banner on the availability heatmap widget, shown
only while a stamp-mismatch (in-progress ingest) is being served from the prior cache row.

### New user actions

None — this is a passive display-honesty fix; no new buttons/forms.

### UI surface changes

`/data`'s existing `AvailabilityHeatmap` component gains one conditional banner state. No new page,
route, or nav entry.

### Product surface delta

The Data page never again shows a false "no data" message while an ingest is running; `GET /api/health`
and `/api/stocks/{ticker}/bars?through=latest` return to their committed budgets; J-06's own golden can
no longer report PASS while measuring nothing.

### Blueprint conformance

All work lives under the ALREADY-registered "Availability heatmap" and "Backend readiness / boot phase"
Data Contract rows, served from their existing `/data` (Data Manager) and global-readiness-badge homes
(`runs/goal-session-ops-hardening/state/blueprint.md`, Information Architecture table). No new page,
route, or nav entry; no nav-skeleton change; no `blueprint.reapproval-requested` file needed.
`blueprint.md` has already been updated this iteration (additive-only): a new "iter-57 update" changelog
paragraph, and the "Availability heatmap" Data Contract row's Notes cell extended with the two new
fields below, tagged `[TARGET, iter-57 building]` until the evaluator confirms J-06 passing.

### Data-contract additions

- `stale: bool` — true when the `GET /api/data/availability` response's `cells`/`total_symbols`/
  `trading_day_count` predate the current `_membership_dataset_version` stamp (an ingest is mid-flight
  and the finalize warm has not yet re-run); false otherwise. Computed by the SAME
  `app.engine.data_manager.availability_from_storage` (extended MISS-fallback logic — still the sole
  reader of `AvailabilityCache`, still calling `compute_availability` only via the existing
  `availability_cached_with_status` writer, no second producer). Served by the SAME
  `GET /api/data/availability` endpoint.
- `served_dataset_version: Optional[str]` — the dataset_version the served payload actually reflects;
  `null` only when no `AvailabilityCache` row has ever been persisted. Same module, same endpoint as
  above.

Both fields are additive extensions of the ALREADY-registered "Availability heatmap" Data Contract row
(added iter-56) — no second computing module, no second serving endpoint, no schema/table change.

## OUT OF SCOPE

- **J-07's per-compute-yield lever.** Iter-56 evaluator's own item (5): "five rounds have tried the same
  lever … this round's data shows it is finished." Not retried. J-07 stays out of Target and
  Required-still-passing this iteration.
- **J-05 as a Target.** Its remediation (aggregates-at-ingest fix, golden-date rotation) is already
  "Do not redo"-complete per iteration-state.md; no new J-05-specific dev work this round. It rides
  Required-still-passing instead (see `assumptions.md`, iter-57, for the reasoning logged).
- **Moving heavy compute to a separate process/worker boundary; whether the 20-minute finalize-tail
  budget applies while the app is also serving traffic.** Unresolved owner decisions, asked at rounds
  50, 51, 53, 54, 55, and 56 — still unanswered, still human-owned, not replanned here (rule 6).
- **The framework-level replay-lane/QA-verdict-reading defects** (the replay lane overwriting its own
  results wholesale; the quality report not reading the browser report's verdict line first) — confirmed
  by direct search (iter-56 decomposer's own `assumptions.md` entry) to live only in the vendored
  `incredible_auto_dev/scripts/automation/` tree, not this product's `apps/backend`/`apps/frontend`/
  `scripts/automation/` — framework-maintenance track, not product-iteration scope.
- **The broken demo-recorder script** (no walkthrough exists for J-04/J-05/J-06/J-07 because the
  recorder itself errors) — capture-only per rule 7, not a round's goal. Once fixed (framework track),
  the showcase pipeline auto-captures this iteration's `[NEW]`-flagged J-06 walkthrough steps
  retroactively; this iteration does not chase the recorder bug itself.
- **Long-carried backlog items** (iter-29/b through iter-48/bj, ledger-tracked; iter-33/g the Regime
  Lab, deferred a 22nd time) — untouched, not re-litigated here.
- **A third `status` value or per-item completeness field** on `data_provider_runs` beyond the existing
  `aggregates_refreshed` omission mechanism — the `persisted_this_call` fix above closes the ONE named
  honesty hole in that existing mechanism; no new representation introduced (consistent with iter-46/49/
  50/54's repeated "no new field" precedent for comparable honest-omission fixes).

## DEFINITION OF DONE

- [ ] `GET /api/data/availability` never returns the not-yet-computed empty sentinel while a prior
      `AvailabilityCache` row exists — it serves that row with `stale: true` +
      `served_dataset_version` set (TC-1, TC-2, TC-3).
- [ ] `/data`'s availability heatmap renders the previous chart + an honest "updating" banner during a
      job, never the false "No availability yet" message while data exists (TC-4).
- [ ] `GET /api/health` answers in ≤0.1s at rest (curl and real-browser), with the relaxed ≤2s
      bounded-window ceiling unchanged (TC-5, TC-6, TC-7).
- [ ] `GET /api/stocks/{ticker}/bars?through=latest` is profiled, fixed, and answers in ≤1.5s, with
      byte-identical output to the pre-fix computation (TC-8, TC-9).
- [ ] `availability_cached_with_status` and `index_series_cached_with_status` both return
      `persisted_this_call=False` on a rolled-back commit (TC-10).
- [ ] MCP `list_runs` uses the same grouped-aggregate query as `app.api.runs.runs`, byte-identical
      `n_stocks`, under the ≤1.5s budget (TC-11).
- [ ] `journey-scripts/J-06.json` asserts real budgets for all four historically over-budget calls, not
      just headings (TC-12).
- [ ] `test_api_runs.py` runs alone, first, and completes with its result recorded before other test
      files or dev work proceed (TC-13).
- [ ] The 8-journey deterministic-replay + browser-qa lane is dispatched LAST against a tree frozen
      after this iteration's code lands; if the audit step subsequently finds a defect needing a
      product-code change, it is filed as a note for iter-58 rather than applied as a code-changing
      audit-fix (TC-14).
- [ ] Target journey J-06 passes via browser-qa-agent / deterministic replay, scored against real
      measurements (TC-1–TC-12, TC-15).
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-08, J-09 remain green — deterministic
      replay + LLM fallback (TC-15).
- [ ] No anti-goal violation introduced: AG-3/AG-8 honesty on the availability serving path (TC-1–TC-4);
      AG-9 all ingest rows created this iteration read `provider='seed'`; AG-10's five frozen
      launch-script/config surfaces show an empty `git diff`/`git status --porcelain` (TC-16).
- [ ] Unit tests pass; no regressions in the existing backend test suite.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-57-dev.md`, naming the profiling
      result for both fixed endpoints, the availability stale-serving mechanism, and all small items
      closed, honestly (met or not met).

## TESTING REQUIREMENTS

- Browser: J-06 (all four previously over-budget calls, plus the during-a-job availability banner) as
  primary target; J-01, J-03, J-04, J-05, J-08, J-09 as required-still-passing deterministic replay.
- Unit/integration: `test_data_manager.py` (availability stale-serving fallback, `persisted_this_call`
  rollback fix), `test_indexes.py` (`persisted_this_call` rollback fix), `test_api_health.py` (fixed
  endpoint byte-identity), `test_api_stocks.py` (fixed `bars` endpoint byte-identity), `test_mcp_tools.py`
  (`list_runs` byte-identity), `test_api_runs.py` (run alone, first, completion recorded).
- Error cases: a rolled-back cache commit must never report `persisted_this_call=True`; a stamp-mismatch
  request for `GET /api/data/availability` on a DB that has NEVER completed an ingest must still serve
  the honest empty sentinel (`stale: false`), never a fabricated non-empty payload.

Test-first contract:

- TC-1: given a backfill/fetch job has committed at least one new price bar but the finalize-tail
  `availability_heatmap` warm has not yet re-run, when a client calls `GET /api/data/availability`, then
  the response has `stale: true`, `served_dataset_version` equal to the PRIOR warm's dataset_version
  (not the in-progress one), and non-empty `cells`/`total_symbols` from that prior warm — never
  `{"total_symbols":0,"trading_day_count":0,"cells":[]}`.
- TC-2: given a DB where `AvailabilityCache` has never held a row (no ingest has ever completed), when
  `GET /api/data/availability` is called, then the response is `stale: false`, `served_dataset_version:
  null`, `total_symbols: 0`, `trading_day_count: 0`, `cells: []` (the honest never-computed sentinel,
  unchanged from today).
- TC-3: given the backend is warm/idle and the cache row matches the current dataset_version, when
  `GET /api/data/availability` is called, then `stale: false`, `served_dataset_version` equals the
  current dataset_version, and `cells`/`total_symbols`/`trading_day_count` are byte-identical to
  iter-56's already-verified values (regression guard).
- TC-4: given `stale: true` is served during an ingest, when `/data`'s availability-heatmap component
  renders, then it shows the previous heatmap's cells plus a visible "Data as of
  `<served_dataset_version>` — updating" banner, and never renders "No availability yet — Fetch real EOD
  prices" while `cells` is non-empty.
- TC-5: given the backend is idle (no ingest running), when `GET /api/health` is measured by curl at
  rest, then it responds in ≤0.1s, recorded in a new dated `reports/perf-budgets.md` addendum.
- TC-6: given the same idle condition, when `GET /api/health` is measured via real-browser resource
  timing across at least 3 page loads, then every reading is ≤0.1s.
- TC-7: given a bounded background-compute window (an in-flight heavy ingest) is active, when
  `GET /api/health` is polled once per second throughout, then every poll answers HTTP 200 within the
  owner-amended relaxed ≤2s ceiling (unchanged — regression guard so the steady-state fix does not alter
  the separate bounded-window contract J-05 step 4 / J-07 step 2 depend on).
- TC-8: given `GET /api/stocks/AAPL/bars?through=latest` is profiled first (query plan / row count /
  wall-clock breakdown recorded in the dev handoff), when the measured bottleneck is fixed, then the
  endpoint responds in ≤1.5s in both curl and real-browser measurement, down from the 6.2s Addendum 18
  reading.
- TC-9: given the fix to `bars_through_latest`, when a unit test compares its output for a fixed
  `(symbol="AAPL", through="latest")` input against the pre-fix computation for the same DB state, then
  the two payloads are byte-identical.
- TC-10: given `availability_cached_with_status` (`data_manager.py:1660-1663`) and
  `index_series_cached_with_status` (`indexes.py:275-278`) each attempt a commit that a fault-injection
  test forces to raise, when the `except` block's rollback runs, then both functions return
  `persisted_this_call=False` — never `True` for a write that did not durably persist.
- TC-11: given `app.mcp.tools.list_runs` (`tools.py:706-731`) rewritten to use the same grouped
  `GROUP BY ScannerResult.run_id` aggregate `app.api.runs.runs` already uses, when a unit test compares
  its `n_stocks` per run against the pre-fix per-run-COUNT loop for every stored run, then the two are
  byte-identical, and a live timing check on the current DB shows it answering under the ≤1.5s budget
  (down from the coherence-audit's measured 6.8-10.7s).
- TC-12: given `journey-scripts/J-06.json`'s steps for `/data`, `/scanner-runs`, and any page issuing
  `GET /api/health` / `GET /api/stocks/AAPL/bars?through=latest`, when the golden is rewritten, then each
  of those steps asserts a measured latency at or under its committed budget in addition to its existing
  heading text — a replay against an artificially slowed endpoint must FAIL the golden, not silently PASS.
- TC-13: given `apps/backend/tests/test_api_runs.py` has been killed twice at 30+ minutes when run
  inside the full suite, when it is run alone and first, before any other test file or dev work this
  iteration, then it completes (pass or fail reported honestly) and its result is recorded in the dev
  handoff before any other test file runs.
- TC-14: given this iteration's product-code diff is complete and frozen, when the 8-journey
  deterministic-replay + browser-qa lane is dispatched, then every lane result file's mtime is strictly
  after the newest `apps/backend/**`/`apps/frontend/**` product-code mtime, and if the audit step
  subsequently finds a defect needing a code change, it is filed as a note for iter-58 rather than
  applied as a code-changing audit-fix (mirrors iter-53's TC-7/TC-9 precedent).
- TC-15: given J-06 as Target and J-01/J-03/J-04/J-05/J-08/J-09 as Required-still-passing, when the lane
  runs, then J-06's replay/browser-qa asserts real budget compliance (not headings) for all four
  previously over-budget endpoints, and the six required-still-passing journeys replay PASS with no
  journey moving from `passing`/`already_passing` to `failing`/`regressed`.
- TC-16: given AG-9/AG-10's five frozen launch-script/config surfaces (`config.yaml`, `host-guard.env`,
  `scripts/start-backend.sh`, `scripts/dev.sh`, `scripts/start-frontend.sh`), when this iteration's diff
  is checked, then `git diff --stat` and `git status --porcelain` over those five paths are both empty,
  and every `data_provider_runs` row created during this iteration's drills reads `provider='seed'`.
- TC-17: given the measurement note mislabeling `compute_availability`'s SPY-benchmark trading calendar
  as "1996-2026" (`reports/perf-budgets.md` Addendum 20), when the developer reads the actual calendar
  source (`_trading_days`, `app.engine.data_manager`) and its live min/max dates, then a new dated
  append-only correction note records the verified span — the historical entry itself is left unedited.

## NOTES

- **Depth-dispatch mismatch, flagged for visibility.** Iter-56 was the SECOND round in three where the
  engine dispatched lean against a spec's own `Depth: full`. This spec's `Depth: full` /
  `Full trigger: 3` line is unambiguous (prior verdict ESCALATE, mandatory, no exceptions); nothing
  further is in this decomposer's control to fix a dispatch-layer issue beyond stating the requirement
  clearly.
- **J-05's golden will consume its rotated date again.** `journey-scripts/J-05.json` targets
  2010-11-10 (rotated iter-56, live-verified 0 `scanner_runs` rows). Including J-05 in
  Required-still-passing this round replays it, consuming that date; a future iteration that next
  targets or replays J-05 must rotate to a fresh unsnapshotted date first (iter-55 lesson).
- **OWNER — two decisions and one open fact, carried again, unanswered since rounds 50/51/53/54/55/56:**
  (a) may a future round move the heavy calculation into a separate process — the iter-56 evaluator
  states this round gave the strongest evidence yet that it is the only remaining lever for J-07?
  (b) does the 20-minute finalize-tail budget apply while the app is also serving traffic, or only when
  idle? Neither is this iteration's job to resolve; both stay logged here so they are not lost.
- **Coherence:** iter-56's verdict was COHERENCE-WARN (0 blocking, 1 advisory — the MCP `list_runs`
  stale duplicate). This iteration closes that advisory as a low-risk rider (TC-11); no other
  coherence-blocking issue is carried.
- **`persisted_this_call` fix scope check:** both `data_manager.py` and `indexes.py` share the identical
  `try: commit / except: rollback` bug because they were built to "mirror" each other's honesty-gate
  contract exactly (iter-56's own docstring language); fixing only one would introduce a NEW
  inconsistency between functions the codebase itself documents as siblings, so both are fixed together
  in this iteration despite the eval naming only the availability side explicitly.
