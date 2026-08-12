# Goal Iteration 71 — Bound readiness-cache staleness + re-verify all 8 journeys after the infra death

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 71
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-01, J-03, J-04, J-05, J-06, J-07, J-08, J-09
- **Required-still-passing journeys:** none additional — this session's full Must-have set is exactly these 8, and all 8 are already Target journeys this round (BINDING pending-infra make-up; see BACKGROUND for the rubric-5 deviation this causes).
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the committed seed / local provider fixtures — no live external network calls or paid data services may be introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills, full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env` whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`, `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings are a physical constraint of the current host (two instant hardware resets under all-core vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to optimize away. *(Owner amendment 2026-07-31, two corrections of record — nothing above is relaxed: `memory_cap_mb` / `malloc_arena_max` live in `config.yaml`, not in `host-guard.env`; and the 2026-07-20/21 resets were subsequently attributed to an uncorrected hardware data-fabric fault (`host-guard.env`, 2026-07-30), so the ceiling VALUES are an owner-set envelope — re-set by the dated entry in "Additional binding notes" below — while this paragraph's prohibition on agents removing, weakening, or bypassing caps is unchanged.)* *(critical)*

## GOAL

Re-verify all eight ops-hardening journeys against a confirmed-live backend after last round's
mid-round infrastructure death produced zero journey evidence, while closing the one product
gap that death left unaddressed: bound the readiness/preflight cache's staleness so a
wedged/dead background-refresh tick can never serve a frozen "ready" state forever.

## BACKGROUND

iter-70 (full depth, ESCALATE-triggered) landed the readiness/preflight background-refresh
cache and proved it works (0 of 1,030 health-poll breaches vs 77 of 952 before), but the QA
backend shut down cleanly between the dev/reviewer lanes and the browser/replay lanes — every
one of the 8 journeys ended the round `partial`/`pending_infra`, meaning NONE were actually
checked. The engine's `pending_infra` mechanism makes re-verifying all 8 a BINDING make-up
target this round (see the dispatch prompt's "Pending-infra make-up targets" line) — this is
why Target journeys is 8, not the usual 1-3 (rubric-5 deviation, stated per the pre-write
self-check). iter-70 itself named a real, still-open product gap while shipping the cache
(iter-70/d): `readiness.py:567-575` serves the cache with no age check, so a dead tick thread
would answer 200 with a plausible-but-frozen readiness/preflight forever — "before this round
the endpoint could be slow but never wrong; it can now be fast and wrong." The evaluator's own
next-step order (1)-(4) asks for exactly this round's scope: re-verify all 8 (1), bound the
cache's staleness (2), fix the J-07 drill's late-starting poller (3), and land three small,
already-diagnosed fixes (4). The evaluator's depth recommendation for this round is **lean, and
binding** — no full trigger holds: the prior verdict was CONTINUE (not ESCALATE), the prior
coherence verdict was COHERENCE-PASS (no consolidation mandated), the hardening-cadence counter
is at 0/6 (reset by iter-70's own full round), and this round lands no user-visible UI change
(goal.md's own Loop Mechanics line ties full depth to a first UI change) — the staleness bound
is an additive backend field, not a UI surface (see Data-contract additions and the
assumption-ledger entry this iteration logs).

**Lessons applied:** iter-70(second)'s lesson — a clean uvicorn shutdown with no traceback is
infrastructure, never a product crash; this round's browser-qa-agent must confirm `GET
/api/health` returns 200 BEFORE beginning any journey check, and must not proceed past that
check on a dead backend. iter-70(first)'s lesson — never cache a truth-telling value without
bounding its staleness in the same change; this round closes exactly that gap. iter-64's lesson
— a replay/QA "transient" or "✓ verified" claim must be checked against the actual frame/results
file, never trusted at face value; this round directs the QA report writer accordingly (TC-7).

## IN SCOPE

### Backend
- [ ] `app.engine.readiness`: stamp each readiness/preflight cache entry with a monotonic
      computed-at timestamp. `GET /api/health` gains one additive field, `stale_for_s:
      float>=0`. A new bounded config knob `readiness.max_stale_intervals` (default 3) sets the
      synchronous-fallback threshold: when a request would otherwise be served a cache entry
      older than `max_stale_intervals × refresh_interval_seconds`, fall back to a synchronous
      `compute_readiness`/`compute_preflight` call (mirrors the existing cold-start fallback)
      instead of serving further-stale data. Same two producers, same one endpoint — no second
      implementation.
- [ ] `apps/backend/app/api/health.py:174`: assign `cached = None` explicitly in the
      preflight-fallback branch before use (reviewer/audit MINOR from iter-70).
- [ ] Add one integration test composing TC-4's two previously-separate halves: a real state
      flip triggered by the ingest finalize hook's immediate-refresh call is actually served by
      `GET /api/health` within one tick (audit T1 from iter-70).

### Frontend
None this iteration. `stale_for_s` is a backend-only diagnostic field, not rendered — see NOTES
and the iter-71 assumption-ledger entry for why surfacing it is deferred rather than shipped now.

### New user-facing capability
None. This round hardens an existing endpoint's honesty guarantee (never silently serve
arbitrarily-stale readiness data) and closes a verification gap; it does not add anything a
user can newly do.

### New information displayed
None visible. `stale_for_s` exists in the `GET /api/health` response body but is not read by
any frontend component this iteration.

### New user actions
None.

### UI surface changes
None — no page, badge, or banner changes.

### Product surface delta
None visible to a user this round. The delta is internal: the readiness/preflight value the
badge and preflight banner already read can no longer go silently stale without bound.

### Blueprint conformance
No new pages or nav entries. The staleness bound lives entirely inside the ALREADY-registered
"Backend readiness / boot phase + preflight verdict" row (Data Contract) and its existing homes
(global readiness badge + preflight banner, `/data`'s interrupted-job state) — no change to
Information Architecture.

### Data-contract additions
- `stale_for_s: float>=0` — seconds since the `GET /api/health` response's readiness/preflight/
  background_compute payload was computed (0 when computed synchronously for the current
  request). Computing module: `app.engine.readiness.compute_readiness` /
  `compute_preflight` (existing canonical producer, unchanged identity). Serving endpoint:
  `GET /api/health` (existing canonical endpoint, unchanged identity). Purely additive field on
  an already-registered Data Contract row — registered in `blueprint.md`'s "Backend readiness /
  boot phase + preflight verdict" row under an `iter-71` note.

## OUT OF SCOPE

- Rendering `stale_for_s` on the readiness badge or preflight banner — deferred; would be this
  cycle's first user-visible UI change, which goal.md's own Loop Mechanics rule ties to full
  depth, and this round's depth is binding lean.
- Re-instrumenting `readiness_s`/`preflight_s` any further — Do-not-redo: "DONE and PROVEN."
- Bounding `factor_lab_all_warm` / `coverage_membership_timeline_refresh` by code change —
  Do-not-redo: "NOT NEEDED," released-but-unused alternative.
- Re-measuring J-07 steps 3 (VmPeak) and 4 (memory-pressure abort) — carry forward on evidence
  durability per the standing Do-not-redo entry; the warm-path code they test is unchanged this
  round.
- Any edit to `config.yaml` caps, `project-extensions/host-guard/`, or any HOST-GUARD script
  block — AG-10 envelope stays owner-set and untouched.
- Any edit to `scripts/automation/*` — the `browser-qa-phase.sh` one-line ordering bug remains
  owner-gated pending explicit sign-off (still unanswered, per NOTES).
- The owner's standing 2-second-ceiling policy question and the cost-budget sanction decision —
  human-owned (rule 6), not re-litigated by this spec.
- The Regime Lab (iter-33/g) — deferred again, not this round's scope.
- Any change to `compute_forward_aggregates` / the warm-path beyond what iter-70 already shipped.

## DEFINITION OF DONE

- [ ] All 8 journeys (J-01, J-03, J-04, J-05, J-06, J-07, J-08, J-09) re-verified via
      browser-qa-agent against a backend confirmed live (`GET /api/health` HTTP 200) before the
      checking stage begins; `pending_infra` cleared for every journey actually tested this round.
- [ ] `GET /api/health` response includes `stale_for_s: float>=0`; a killed/wedged tick-thread
      scenario (test hook) is proven to fall back to a synchronous compute rather than serving
      indefinitely-stale data.
- [ ] `health.py:174` assigns `cached = None` explicitly; a unit test exercises that exact
      branch with no `NameError`.
- [ ] New integration test proves a real state flip is served within one refresh tick (composes
      TC-4's two halves, audit T1).
- [ ] The QA report never states "✓ Developer verified via replay" for a journey whose
      replay-results row reads BLOCKED or SKIPPED.
- [ ] J-07's TC-3 health-poll drill starts polling before the ingest job's start command is
      issued, closing the previously-unmeasured 32.1 s opening window.
- [ ] Unit/integration tests pass; no regression on any of the 8 journeys.
- [ ] No anti-goal violation introduced.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-71-dev.md`.

## TESTING REQUIREMENTS

- Browser: all 8 journeys by ID — J-01, J-03, J-04, J-05, J-06, J-07, J-08, J-09.
- Unit/integration: readiness-cache staleness-bound test (sync fallback past threshold),
  fresh-cache-serve test (`stale_for_s` populated, no sync fallback), `health.py:174`
  `cached = None` branch test, the TC-4-composition state-flip-within-one-tick test.
- Error cases: tick thread stopped/dead — endpoint must still answer 200 via synchronous
  fallback, never a `NameError`/500 from the uninitialized-`cached` path.

Test-first contract:

- TC-1: given the backend running with the readiness background-refresh tick thread stopped via
  a test hook, when the cache entry's age exceeds `readiness.max_stale_intervals ×
  refresh_interval_seconds` and a client calls `GET /api/health`, then the response is produced
  by a synchronous call to `compute_readiness`/`compute_preflight` (not the stale cache) and the
  response's `stale_for_s` field equals 0.
- TC-2: given the tick thread ticking normally and the cache entry was refreshed less than
  `readiness.max_stale_intervals × refresh_interval_seconds` ago, when a client calls `GET
  /api/health`, then the response is served from the cache (confirmed via call-count
  instrumentation showing zero synchronous compute calls) and `stale_for_s` is a non-negative
  number below that threshold.
- TC-3: given `apps/backend/app/api/health.py`'s preflight-fallback branch at line 174, when the
  cached preflight value is unavailable, then the code assigns `cached = None` explicitly
  before use, and a unit test exercising this exact branch asserts no `NameError` is raised and
  the response's preflight field equals the documented default value.
- TC-4: given an ingest finalize hook completes and changes `readiness.state` (e.g.
  `awaiting_snapshot` → `ready`), when `GET /api/health` is polled within one
  `refresh_interval_seconds` tick after the finalize hook returns, then the response's `state`
  field reflects the NEW value — one integration test asserts both the periodic-tick refresh and
  the finalize-triggered immediate refresh together (audit T1).
- TC-5: given the J-07 TC-3 health-poll drill script, when the drill runs for this round's
  re-verification, then the poller's first `GET /api/health` request timestamp precedes the
  ingest job's start-command timestamp (recorded in `logs/backend.log`) by at least 2 seconds,
  so the drill's CSV contains poll rows covering the job's opening window.
- TC-6: given the browser-qa-agent begins this round's checking stage, when it first calls `GET
  /api/health`, then it proceeds to journey checks only if the response is HTTP 200; if the
  response is not HTTP 200 (or times out), the agent records the failure explicitly in its
  report and does not mark any journey passing or failing on stale or absent evidence.
- TC-7: given the deterministic replay lane's results file for a required-still-passing journey,
  when the browser-qa-agent composes its QA report, then it writes "Developer verified via
  replay" for that journey only if the replay-results file's row for that journey reads PASS; if
  the row reads BLOCKED or SKIPPED, the report states that verbatim and does not claim
  verification.
- TC-8: given all 8 journeys with a live backend confirmed via TC-6, when the browser-qa-agent
  completes its pass, then `journey-history.json`'s `pending_infra` flag is set to false for
  every one of the 8 journeys, and each journey's status (passing/partial/failing) reflects
  fresh evidence captured this round rather than carried-forward pending-infra state.
- TC-9: given J-07's steps 3 (VmPeak) and 4 (memory-pressure abort) whose exercised code
  (`compute_forward_aggregates`, `research.py`) is byte-unchanged this round, when the evaluator
  scores J-07, then it carries those two steps forward on evidence durability per the standing
  Do-not-redo entry and does not re-run the memory-pressure drill this round.

## NOTES

- **Two-strike STALLED rule is live this round.** iter-70's written escalation trigger: "if the
  same lane is blocked a second consecutive round, the infrastructure becomes human-owned and
  the next evaluator should return STALLED." If the QA backend dies again mid-round before all 8
  journeys are checked, the evaluator should apply that rule rather than a third `pending_infra`
  cycle.
- **Human-owned items still open, not re-litigated here** (rule 6): the owner's 2-second
  health-ceiling policy choice (22nd round asked, per iter-70's owner paragraph — the app now
  meets the stricter reading so the cost of answering is zero); permission to fix the one-line
  ordering bug in `scripts/automation/browser-qa-phase.sh`; the cost-sanction decision (10
  consecutive over-budget full rounds). None of these block this round's lean scope.
- **Carried, untouched** (unchanged from iter-70's list, not restated in full — see
  `iteration-state.md`'s "Do not redo" / the evaluator log's carried-items line for the full
  roster): iter-29/b, iter-31/e, iter-32/f, iter-35/k, iter-36/n, iter-37/o, iter-37/q,
  iter-39/u, iter-46/az, iter-46/ba, iter-47/bd, iter-47/bf, iter-47/bi, iter-48/bj, iter-57/f,
  iter-57/l, iter-59/g, iter-59/h, iter-59/k, iter-62/e, iter-62/f, iter-63/a, iter-63/b,
  iter-63/d, iter-64/b, iter-64/e, iter-64/f, iter-65/b, iter-65/c, iter-65/d, iter-66/b,
  iter-66/e, iter-66/f, iter-66/g, iter-67/f, iter-67/g, iter-68/d, iter-68/e, iter-69/e, and
  iter-33/g (the Regime Lab, deferred a 36th time this round makes it 37 pending — genuinely out
  of this iteration's scope per rule 5's one-risky-action budget).
- An assumption-ledger entry (`runs/goal-session-ops-hardening/state/assumptions.md`, iter-71 —
  goal-decomposer) records the interpretation calls made for the staleness-bound mechanism
  (field name, default threshold multiplier, and the choice not to surface it in the UI this
  round).
