# Goal Iteration 25 — Close J-09: session-live manifest, honest "unknown" copy, deflake T1

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 25
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-09
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-06, J-07, J-08
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
    optimize away. *(critical)*

## GOAL

Close J-09's one remaining gap — its unbuilt Walkthrough acceptance clause — plus the two agent-owned audit
findings (F1, T1) iter-24's evaluator identified, so J-09 can be scored `passing` and the session can reach
GOAL_ACHIEVED with all 8 journeys green.

## BACKGROUND

Iter-24 built J-09 (background-compute disclosure: badge detail + `/data` panel) correctly and re-derived its
numbers from the database, but scored it `partial` for one reason: the goal.md Walkthrough acceptance bullet
("a `[NEW]`-flagged walkthrough … viewable via `demo.sh ops-hardening --session-live`") was never mapped into
iter-24's IN SCOPE/DoD, so nothing built it, and `reports/goal-session-ops-hardening-demo.json` (the file that
command actually reads) still holds iter-23's 12 steps with zero J-09 entries. This is the exact clause the
iter-22 second-key CONFIRM rejected GOAL_ACHIEVED on, one journey later — the iter-24 lesson on record states
plainly: "enumerate EVERY Acceptance bullet, especially the walkthrough/demo-manifest one, before declaring
scope." This spec does that explicitly (IN SCOPE below). The evaluator also left two smaller, agent-tractable
findings open: audit F1 (the `/data` panel asserts "No background compute running…" even when the health poll
itself failed and the state is genuinely unknown) and audit T1 (two new tests compare two live reads of
in-memory registry state, a false-alarm risk on any whole-file run). All three items were named
non-blocking-but-tractable in iter-24's Next-Step Recommendation and its own eval.md ("LEAN depth, no new
features"). No journey regressed; the last coherence.md was COHERENCE-PASS, so this is not a forced
consolidation pass — it is the smallest, most direct unblocker: closing J-09 is the ONLY thing standing between
this session and GOAL_ACHIEVED (rubric step 3, "unblockers next"), and its change set (a JSON manifest append,
one frontend copy branch, two test rewrites) is small and low-risk (rubric step 4/5 — one journey, no risky
cross-cutting change). Per the assumptions ledger (iter-23 — goal-decomposer, un-vetoed since), the Walkthrough
clause is satisfied by a complete, accurate manifest — not an actual witnessed `--session-live` playback, which
stays correctly out of scope as a non-autonomous act.

Explicitly deferred, per iter-24's own guidance that it is "DECOMPOSER-PLANNED, not an opportunistic patch":
audit B2 (a `Thread.start()` failure would leave the badge reading "running (1)" forever) — fixing it requires
deliberately lifting the freeze on `ensure_historical_forward_aggregates_dispatched`, which deserves its own
scoped iteration, not a casual bundle here.

## IN SCOPE

### Backend
- [ ] Rewrite the two new background-compute-registry tests introduced in iter-24 —
  `apps/backend/tests/test_health.py` (~line 113) and `apps/backend/tests/test_readiness.py` (~line 292) — so
  they compare two reads on **identity/shape** (same active-window keys/count, same `recent_outcomes`
  ordering/length) **excluding** the volatile `elapsed_ms` timing field, instead of comparing values that can
  legitimately differ between two live reads (closes audit T1).
- [ ] No other backend/product-code changes. `app.engine.forward_testing` (including
  `ensure_historical_forward_aggregates_dispatched`'s keying/single-flight semantics,
  `get_background_compute_status()`), `app.engine.readiness.compute_readiness`, `compute_forward_aggregates`,
  and `resolved_forward_aggregate_evidence` stay byte-unchanged (binding "Do not redo" — iteration-state.md).

### Frontend
- [ ] `apps/frontend/app/data/page.tsx`'s `BackgroundComputePanel` (~lines 3593/3603): add a distinct copy
  branch for when the readiness poll itself failed / the background-compute field is unavailable — reading
  the SAME existing poll-failure signal `apps/frontend/components/readiness-provider.tsx:87` already sets to
  "unknown" — rendering an explicit message that the background-compute state is unknown because the backend
  is unreachable. Never fall through to the idle "No background compute running…" sentence for this case
  (closes audit F1).
- [ ] Preserve the existing idle-state copy exactly unchanged for the genuine idle case (poll succeeded, zero
  active windows) — regression guard, no visual/copy change there.

### Non-product artifacts (demo / QA)
- [ ] Append `[NEW]`-flagged, `"verified": true` steps for J-09 to
  `reports/goal-session-ops-hardening-demo.json` (the file `demo.sh ops-hardening --session-live` reads, per
  `demo-phase.sh:78` and the iter-23 precedent for J-06/J-07/J-08) — at minimum three scenes: (1) steady-state
  `Ready` + a steady-state `GET /api/health` poll; (2) an in-flight background-compute window showing the
  badge's inline detail alongside `Ready` and the `/data` panel's in-flight state (elapsed, horizons
  done/total, as-of/dataset identity); (3) the post-completion idle/last-outcome state. Source `expect`/
  `point_out` figures from already evaluator-verified iter-24 evidence (`UT-02-badge-active.png`,
  `013-eval.html`, `015-eval.html`, `040-navigate.html`, and the DB cross-check in iter-24's eval.md) unless a
  fresh capture is cheaper — purely additive; existing steps n=1–12 stay byte-unchanged, and the existing
  `highlights`-section cap is not disturbed.

### New user-facing capability
None new this iteration — J-09's disclosure capability (badge + `/data` panel) was already built and working
as of iter-24. This iteration makes it (a) honestly labeled in one more edge case (backend/poll unreachable)
and (b) fully documented in the session's guided tour, closing the only gap keeping it `partial`.

### New information displayed
The `BackgroundComputePanel`'s new copy branch for the poll-failure/unknown case is new TEXT, not a new data
value — it reads the SAME existing readiness-poll success/failure signal already registered under the
"Backend readiness / boot phase + preflight verdict" Data Contract row.

### New user actions
None.

### UI surface changes
`/data` page's `BackgroundComputePanel` gains one new copy branch (poll-failure state). No new component, no
new page, no new route.

### Product surface delta
J-09 becomes fully closeable: same two surfaces (global readiness badge, `/data` panel), now honest about one
more edge case, with a complete guided-tour manifest entry.

### Blueprint conformance
`(global)` / Data Manager — the same canonical homes J-04/J-07/J-09 already have in `blueprint.md`'s
Feature/journey-homes table. No new page, no nav-skeleton change.

### Data-contract additions
None. The poll-failure copy branches on an EXISTING signal (readiness-poll success/failure, already part of
the "Backend readiness / boot phase + preflight verdict" row's producer/endpoint —
`app.engine.readiness.compute_readiness` / `GET /api/health`); no second producer, no second endpoint. The
demo manifest is a pipeline/QA artifact, not a Data Contract row (matches the iter-18/23 precedent already
recorded in `blueprint.md`: "a log line is not a served/displayed value").

## OUT OF SCOPE

- Audit B2 (a `Thread.start()` failure leaving the badge reading "running (1)" forever) — explicitly deferred;
  per iter-24's own recommendation it needs the `ensure_historical_forward_aggregates_dispatched` freeze
  lifted deliberately, which deserves its own scoped spec, not a casual patch bundled here.
- Audit B5 / whether the at-rest `<= 0.1s` `/api/health` budget stands as written — owner-owned, not
  re-litigated this iteration.
- Backlog card B-1107 (global background-compute concurrency cap) — owner-optional, unchanged.
- Retargeting `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches before removing the
  dangling imports at `backtest.py:75` / `mcp/tools.py:38`; running `test_api_backtest.py` TC-11 and
  `test_data_manager.py`'s heavy fixtures off the constrained box — carried, non-blocking, not required for
  this iteration's closure.
- Any change to `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, J-08's
  `ready`/`refreshing`/`not_yet_computed` serving state machine, or
  `ensure_historical_forward_aggregates_dispatched`'s keying/single-flight semantics — binding "Do not redo."
- Re-running TC-13/TC-14 (owner-authorized, dated 2026-07-25, DONE/PASS) — binding "Do not redo."
- Editing or re-litigating the owner's BCW budget amendment (`reports/perf-budgets.md` § "OWNER BUDGET
  AMENDMENT" + "Revision 1") — binding "Do not redo."
- Triggering a fresh live background-compute window purely for the demo manifest — reuse iter-24's already
  evaluator-verified evidence per the iter-23 precedent unless the developer finds a fresh capture materially
  cheaper (not required).
- Running the full backend pytest suite concurrently — per the standing session lesson, run only the targeted
  test files.

## DEFINITION OF DONE

- [ ] J-09 passes via browser-qa-agent (all six goal.md steps remain verified AND the Walkthrough acceptance
  bullet is satisfied by the completed manifest)
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-06, J-07, J-08 remain green (deterministic
  replay where a golden script exists; LLM fallback for J-07)
- [ ] No anti-goal violation introduced (scan-report CLEAN; coherence-auditor returns COHERENCE-PASS; the
  `background_compute` value keeps exactly one producer and one serving endpoint)
- [ ] Unit tests pass; no regressions (T1's two rewritten tests are deterministic across 5 consecutive reruns;
  targeted test files only, not the full suite)
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-25-dev.md`

## TESTING REQUIREMENTS

- Browser: J-09 (full six-step walkthrough, including the badge in-flight detail and the `/data` panel's
  in-flight/idle/poll-failure states); regression smoke on J-01, J-03, J-04, J-05, J-06, J-07, J-08 (replay
  where golden scripts exist, LLM lane for J-07).
- Unit/integration: `apps/backend/tests/test_health.py` (~line 113), `apps/backend/tests/test_readiness.py`
  (~line 292) rewritten per TC-5 below; extend or add a frontend component test for
  `BackgroundComputePanel` covering both the poll-failure branch (TC-3) and the existing idle-case branch
  (TC-4).
- Error cases: a readiness-poll failure / backend-unreachable state must never be misrepresented by the
  `/data` panel as "idle / nothing running" (TC-3); a background-compute internal error must continue
  degrading `GET /api/health` to `{"active": [], "recent_outcomes": []}` (unchanged from iter-24; verify no
  regression).

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps to at
least one concrete scenario line below.

- TC-1: given the pre-iteration `reports/goal-session-ops-hardening-demo.json` holds 12 steps with zero J-09
  entries, when this iteration appends J-09's three walkthrough beats (steady-state Ready; in-flight
  background-compute window with badge detail + `/data` panel; post-completion idle/last-outcome), then the
  file contains at least 3 new entries with `"journey": "J-09"`, `"new": true`, `"verified": true`, and each
  `expect` matches text/state actually observed in verified J-09 evidence.
- TC-2: given the same manifest file, when diffed against the iter-23/iter-24 committed version, then the
  diff is purely additive — steps n=1 through n=12 are byte-unchanged and the existing `highlights`-section
  entry count is undisturbed.
- TC-3: given the `/data` page is open and the readiness poll (`GET /api/health`) fails or the backend is
  unreachable, when `BackgroundComputePanel` renders, then it displays a distinct message stating the
  background-compute state is unknown because the backend is unreachable, and it does NOT render the idle
  "No background compute running…" sentence.
- TC-4: given the `/data` page is open, the readiness poll succeeds, and zero background-compute windows are
  active, when `BackgroundComputePanel` renders, then it displays the existing idle sentence "No background
  compute running…" unchanged.
- TC-5: given `test_health.py`'s and `test_readiness.py`'s new background-compute-registry tests (introduced
  iter-24) are rewritten to compare identity/shape excluding `elapsed_ms`, when each test is run 5 times
  consecutively, then all 5 runs pass with zero flake.
- TC-6: given the seven previously-passing journeys (J-01, J-03, J-04, J-05, J-06, J-08 via deterministic
  golden replay; J-07 via the LLM browser-qa lane), when re-verified this iteration, then all seven return
  PASS with fresh iter-25-dated evidence and `last_verified_iter` advances to iter-25 for each.
- TC-7: given J-09's six numbered goal.md steps are already verified passing as of iter-24 and this
  iteration's manifest/panel work is complete, when browser-qa-agent re-walks J-09 end to end, then all six
  steps assert as before AND the Walkthrough acceptance bullet is satisfied, yielding a `passing` (not
  `partial`) evaluator score for J-09.
- TC-8: given this iteration's diff (frontend copy branch, two test rewrites, demo-manifest append), when
  scanned by the security scan-report and the coherence-auditor, then the scan-report is CLEAN, coherence
  returns COHERENCE-PASS, and zero product-code diff touches `app.engine.forward_testing`,
  `app.engine.readiness.compute_readiness`, `compute_forward_aggregates`, or
  `resolved_forward_aggregate_evidence`.
- TC-9: given the developer's work this iteration is complete, then `docs/handoffs/goal-ops-hardening-iter-25-dev.md`
  exists and documents the manifest steps added, the exact F1 copy text, and the T1 test rewrite.
- TC-10: given the targeted test files (`test_health.py`, `test_readiness.py`, plus any frontend
  `BackgroundComputePanel` test), when run individually (never the full suite, per the standing session
  lesson against concurrent full-suite pytest on this host), then all tests pass with zero new failures and
  zero new skips.

## NOTES

- Applies iter-24's lesson verbatim: "A goal-proposer auto-appended journey (J-09) inherited this session's
  standard Acceptance clauses verbatim — including the `demo.sh --session-live` walkthrough clause — but the
  iteration spec's IN SCOPE / DEFINITION OF DONE never mapped that clause to any task… enumerate EVERY
  Acceptance bullet, especially the walkthrough/demo-manifest one, before declaring scope." This spec does so
  explicitly above.
- Applies the assumptions ledger (iter-23 — goal-decomposer, un-vetoed): the Walkthrough clause is satisfied
  by a complete, accurate JSON manifest with live-checked `expect`s — not an actual witnessed
  `--session-live` playback, which stays correctly out of scope as a non-autonomous act.
- Applies the iter-24 lesson on Chrome-MCP blank scrolled screenshots on this host: if any fresh capture is
  needed for the below-the-fold `/data` panel, use the raw DOM capture
  (`~/.cache/superpowers/browser/<date>/session-*/NNN-*.html`) read verbatim, not a scrolled screenshot.
- Applies the standing pump lesson: never run the full/concurrent pytest suite as the pump; run only the
  targeted files named above.
- This is expected to be the goal-closing iteration for J-09. If the evaluator scores J-09 `passing` with no
  other open journey, the next step is GOAL_ACHIEVED (deterministic gates + two-key confirm), not a new
  feature iteration.
- Depth is `lean`: no full trigger holds. This is not a structural/cross-cutting change (one frontend copy
  branch + two test rewrites + one additive JSON append), it adds no persisted schema and no new
  computing-module/endpoint for any Data Contract value, the prior verdict was CONTINUE (not ESCALATE), and
  the hardening cadence is disabled (0) per this dispatch's "Consecutive lean iterations dispatched: 0".
