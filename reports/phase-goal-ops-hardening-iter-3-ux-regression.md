# Phase goal-ops-hardening-iter-3 — UX Regression Review

**Date:** 2026-07-20

**Verdict:** UX-REGRESSION-FAIL

---

## Summary

This iteration shipped zero frontend file changes by design — it is a backend correctness fix
(audit findings B1/B2) plus a live health/memory measurement. On that narrow question ("did the
iteration wire a new capability into the UI properly?") there is nothing to fail: no new
capability was promised, and none was silently left unwired.

But this iteration's own DEFINITION OF DONE required, for the first time this session, driving a
genuinely heavy live job and an ordinary "Fetch EOD prices" action through the actual browser
(TC-8/TC-9/TC-11). Doing so surfaced two reproducible, evidence-backed breaks in shared,
cross-journey UI components that previously looked fine only because no iteration had exercised
them this hard before:

1. The **global readiness header** (every page) can be driven into the exact same visual state as
   a real backend crash ("Backend unavailable" / "NO-GO — do not rely on today's board") by an
   ordinary, single-symbol "Fetch EOD prices" — the precise everyday action this iteration's own
   headline fix is built around — with no discoverable in-app recovery path.
2. The **Job progress panel's heartbeat indicator** (relied on by J-01's and J-04's "visible,
   accurate progress" promise) freezes for 83-84% of a real heavy job's duration and visibly
   displays a false "· possibly stalled" warning for minutes, reproduced twice.

Both are rooted in pre-existing code this iteration's diff did not touch (`app.engine.readiness`
and `_refresh_ingest_aggregates` respectively) — but both are shared components this iteration's
own ui-surface-map explicitly flagged for regression-checking, both were caught via that exact
check, and both directly undermine a required-still-passing journey's (J-04) core trust promise
app-wide. Per this review's mandate ("flags existing user journeys that may have regressed" via
shared components), these are in scope and severe enough to fail this review, independent of
where the auditor ultimately assigns root-cause responsibility.

---

## New Capability Discoverability

Per `runs/goal-ops-hardening-iter-3/plan.md`'s UI Evolution section and
`reports/phase-goal-ops-hardening-iter-3-user-visible-changes.md`: **no new user-facing capability
this iteration** ("New user-facing capability: none new"; "UI surface changes: none"). The
existing `/data` coverage panel (built iter-2) is unchanged code — 0 frontend files touched, 0
modified components, 0 new pages/routes, 0 navigation changes, per the ui-surface-map's own
Summary table. There is accordingly no new nav path to assess for reachability-within-2-clicks —
the entry point (`/data`, Data Manager nav section) is exactly where it was, and browser QA
confirms it still loads correctly (UT-01 PASS).

However, the iteration's *changed behavior* does need a discoverability read, because its entire
value proposition is "a fetch now visibly keeps the coverage panel honest" — and that promise only
partially materializes in the browser:

- **What does show:** the "Price history" stat tile's end-date visibly advances immediately after
  a fetch that lands a new bar, and the new value survives a hard reload — direct, confirmed
  evidence the underlying storage-refresh mechanism (B1) fires (`reports/phase-goal-ops-hardening-iter-3-ui-test-results.llm.md`
  UT-02, steps 3 and 5).
- **What doesn't show, under the single most common condition:** the three tiles a typical user
  would treat as the "did my fetch do anything" signal — Symbols, Trading days, Snapshot dates —
  do **not** move for an ordinary top-up fetch (extending existing symbols' history rather than
  discovering a wholly new symbol), by architectural design, not by bug (root-caused precisely in
  UT-02: Trading days is keyed strictly to the benchmark SPY's own bar dates; Symbols only moves
  for a symbol with zero prior bars, and none currently exist in this DB; Snapshot dates never
  moves for a fetch-kind job by design).

This is a **legibility gap**, not a broken feature: the fix works, but a user running the single
most common ingest action (a plain top-up fetch) and eyeballing the panel's most prominent numeric
tiles has a real chance of concluding "nothing happened," because 3 of the 4 tiles they'd
naturally check will not move. Nothing in the panel's copy points a user toward "Price history" as
the tell-tale sign for this specific action. See Flags → Undiscoverable Capabilities.

**Visual consistency:** not applicable this iteration — zero frontend files changed, so there is no
new component, layout, or effect to check against the DESIGN SYSTEM. Existing pages render exactly
as before (confirmed by UT-01/UT-05/UT-10 all passing their visual/rendering assertions).

---

## Regression Risk

| Shared component | Prior feature it serves | This iteration's touch | Risk level | Evidence |
|---|---|---|---|---|
| `CoveragePanel` / `PerSymbolCoverageTable` (fed by `GET /api/data`) | J-05 (iter-2): ingest-time coverage maintenance | B1 widens the finalize trigger; B2 widens the stale-row delete in the same shared `_upsert_coverage_snapshot` | **Low** | UT-01 PASS (loads fine); UT-05 PASS (backfill still updates panel correctly); `test_api_data.py` TC-5 re-run green (unit level). **But** UT-04 (the live fresh-boot all-zero regression check) was **skipped** this round — no spare pristine DB in this environment — so the cold-boot guarantee rests on unit tests only this iteration, not a fresh live click-through. |
| `BackfillBreakdown`'s "Refreshed: ..." line | iter-2: `aggregates_refreshed` transparency field | None directly — contract explicitly preserved (fetch/expand must not set `prog.aggregates_refreshed`) | **None** | UT-09 PASS: every fetch run showed `aggregates_refreshed: []`/no line; every backfill run showed the populated line, exactly the designed two-kind distinction. |
| J-01 (backfill honors range, explains zero-work) | iter-1 | Shares `_upsert_coverage_snapshot`'s widened delete path | **None** | UT-J-01 PASS via both deterministic replay and LLM QA. |
| J-03 (chunked execution, no per-run cap) | iter-1/iter-2 | Same shared finalize/upsert path | **None** | UT-J-03 PASS via both deterministic replay and LLM QA. |
| J-04 boot lifecycle steps (restart timing, crash detection, interrupted-job presentation) | iter-1 | Not touched | **None** | UT-J-04 PASS on all 6 literal steps. |
| **`JobProgressPanel`'s heartbeat / staleness indicator** ("· possibly stalled") | iter-1 (J-01's visible-progress UI; tied to J-04's "visible status stays accurate" acceptance) | Not touched by this iteration's diff, but sits directly downstream of the SAME finalize-hook region B1/B2 modify (`_run_job`), and this iteration's own DoD is what first drove a long-enough job through the browser to expose it | **High — confirmed broken** | UT-06 FAIL, reproduced twice: heartbeat frozen for ~264-272s of a ~316-327s job (83-84%), UI literally rendered "updated 33s ago · possibly stalled" while `status` was still `"running"` and the job was healthy. Root cause: `_refresh_ingest_aggregates` (pre-existing, untouched) contains zero `tick()` calls during its per-date market-phase warm loop. |
| **Global `HealthBadge` / `PreflightBanner`** (every page; core to J-04) | iter-1 (J-04: non-blocking boot, visible/trustworthy status) | Not touched by this iteration's diff (`app.engine.readiness` is a separate module), but is directly, easily triggered by the exact "run an ordinary fetch" action this iteration's own new capability is built around and actively promotes | **High — confirmed broken** | Additional Finding (ui-test-results.llm.md): a bare "Fetch EOD prices" landing one `^VIX` bar for a date beyond SPY's latest snapshot flipped the header to "Backend unavailable" / banner to "NO-GO — do not rely on today's board" — visually identical to a genuine crash — while the backend was fully healthy. No ordinary in-app action (a same-date backfill honestly reported "0 snapshots over 0 dates") could clear it; only "Remove imported data" (a data-deletion control) worked. |

---

## UI vs Backend Parity

| Backend capability (this iteration) | UI exposure | Assessment |
|---|---|---|
| B1 — fetch/expand refreshes `coverage_snapshot` | Automatic via existing `/data` panel; confirmed live via the "Price history" tile advancing + persisting through reload | **Partial** — mechanism proven, but the panel's more prominent tiles (Symbols/Trading days/Snapshot dates) don't move under the tested, common condition (see Discoverability above). Not a backend gap; a UI legibility gap. |
| B2 — stale `coverage_snapshot` rows pruned via one bulk `DELETE` | None | **Correctly backend-only** — internal storage housekeeping with no reasonable UI representation; honestly disclosed as such in `user-visible-changes.md`'s "Not Visible Yet" section. No gap. |
| "expand" job kind's half of the B1/B2 fix (fully unit-tested: `test_expand_that_lands_new_bar_refreshes_coverage_snapshot`) | None — no button/form/control anywhere in `apps/frontend` submits `kind="expand"` (confirmed by ui-impact-analyst's full-repo search) | **Pre-existing gap, honestly disclosed, out of this iteration's stated frontend scope** (spec: "Frontend: None"). Technically meets this review's "hidden capability" definition (exists in backend, no nav path), but it is long-standing (not introduced this iteration) and consistently documented in both `user-visible-changes.md` and the ui-surface-map. Flagged for backlog visibility, not counted against this iteration. |
| Live health/memory measurement (TC-8/TC-9, `reports/perf-budgets.md` Item L) | None | **Correctly backend/ops-only** — an internal engineering measurement, not a product capability; users experience only its effect (app doesn't crawl/crash during a heavy job — itself undermined by the heartbeat finding above). No gap. |

---

## Flags

### Hidden Capabilities
- **"expand" job kind** — exists in the backend (and now carries the identical coverage-freshness
  fix as "fetch"), fully unit-tested, but zero navigation path anywhere in the frontend (confirmed
  by a full-repo string search per the ui-surface-map). Pre-existing across at least this and the
  prior iteration, not introduced now, and explicitly out of this iteration's frontend scope — kept
  as a backlog item, not scored as a new fault.

### Undiscoverable Capabilities
- **Recovery from the false "Backend unavailable" state** (see Regression Risk table): the only
  working fix is the "Remove imported data" by-date-range control on `/data`
  (`apps/frontend/app/data/page.tsx:3208+`), but nothing in the `HealthBadge`/`PreflightBanner`
  text points a user toward it, and the equally-plausible first instinct — running a "Backfill
  snapshots" job for the affected date — reports a misleadingly clean "0 snapshots over 0 dates"
  rather than surfacing the real mismatch. A user who hits this state via an everyday fetch has no
  in-app trail to the correct remedy.
- **The B1 fix's own visible proof point** — a user must specifically know to check the "Price
  history" tile's end-date to see confirmation that an ordinary fetch worked; the three tiles most
  readers would treat as primary "freshness" signals (Symbols/Trading days/Snapshot dates) will not
  move for the most common fetch scenario, by design, with no in-panel copy explaining why.

### Potential Regressions
- **Job progress panel heartbeat ("· possibly stalled")** — confirmed broken under a real heavy
  job, reproduced twice (UT-06): frozen 83-84% of total duration while the job is healthy and
  actively computing. Shares the finalize-hook region this iteration's B1/B2 work modifies (though
  the specific missing-`tick()` code path itself, `_refresh_ingest_aggregates`, is pre-existing and
  untouched). Directly threatens the "job is actually progressing" trust signal relied on by J-01's
  and J-04's visible-progress acceptance for any future long backfill/rebuild.
- **Global readiness badge false "Backend unavailable"** — confirmed broken, directly and easily
  triggered by the exact ordinary-fetch action this iteration's own new capability promotes.
  Visually indistinguishable from a genuine outage; no discoverable recovery path. This is the
  single highest-severity finding in this review: it is app-wide (every page), trust-critical for a
  decision-support product, and newly discovered specifically because this iteration's fix now
  makes "just run a fetch" a more attractive, more frequently-taken action.
- **UT-02's literal target-journey assertion failed** (Symbols/Trading days/Snapshot dates did not
  increase after either tested fetch). QA's own root-cause is credible and precise (a real-world
  Yahoo Finance data-timing ceiling for the benchmark symbol at test time; zero eligible zero-bar
  symbols currently in this DB; Snapshot dates is fetch-independent by design) and is independently
  corroborated by the Price History tile's persisted advance — this reads as a test-environment/
  test-design limitation rather than an additional functional defect. Noted for traceability; not
  counted as a separate regression beyond the legibility gap already flagged above.
- **UT-04 (cold-boot honest all-zero) was skipped**, not re-confirmed live this iteration (no spare
  pristine DB available in this environment). Coverage for this guarantee this round rests on the
  unit-level `test_api_data.py` re-run only. Low risk (the relevant code was not touched by this
  iteration's diff) but it is an unclosed verification loop worth naming.

### Visual Consistency
- Not applicable — 0 frontend files changed, 0 modified components (per the ui-surface-map's own
  Summary). No new page, panel, or effect exists to compare against the DESIGN SYSTEM. Existing
  visual treatment is confirmed unchanged by UT-01/UT-05/UT-10.

---

## Recommendation

1. **(Highest priority)** Fix or at minimum relabel `app.engine.readiness`'s `latest_servable`
   check so a forward-dated, single-symbol bar doesn't flip the app-wide badge into the identical
   "Backend unavailable"/"NO-GO" state as a real crash. At minimum, give this specific condition
   ("new data landed, snapshot pending") its own distinct, calmer label and an in-app pointer to
   the correct remedy — the QA finding itself suggests comparing `latest_servable` against the
   benchmark's own latest bar rather than any symbol's.
2. Add heartbeat (`tick()`) calls inside `_refresh_ingest_aggregates`'s per-date market-phase warm
   loop so the Job progress panel's staleness check stops false-positiving "possibly stalled"
   during the finalize phase of any sufficiently long backfill/rebuild.
3. Re-run UT-04 live against a genuinely fresh/never-ingested DB copy at the next opportunity one
   is available, to close this iteration's one skipped regression check.
4. Consider a small copy change on the "Dataset coverage" panel clarifying that a plain fetch's
   visible proof point is the "Price history" end-date, not the Symbols/Trading days/Snapshot
   dates tiles, for the common top-up case — so the fix's effect isn't misread as "nothing
   happened."
5. (Lower priority, longstanding, not new this iteration) If "expand universe" is ever meant to be
   user-facing, give it a control; otherwise, document its API-only status explicitly so its
   absence stays a deliberate decision rather than an open question raised anew each iteration.

Items 1 and 2 are what drive this review's FAIL verdict — both are shared, cross-journey UI
surfaces confirmed broken under realistic conditions this iteration's own testing was the first to
create.
