# Goal Iteration 75 — Repair the QA-frontend intermittent asset-less serving defect, then re-verify J-08/J-09

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 75
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-08, J-09
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-06, J-07
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
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

Diagnose and fix the harness defect that intermittently serves the QA browser lane an unstyled, asset-less
frontend shell mid-session, then use the repaired lane to get J-08 and J-09 — carried on evidence
durability, unverified for two consecutive rounds — their own fresh, trustworthy pass.

## BACKGROUND

The iter-74 evaluator named this "the single highest-value item" and put it first in its next-step order:
J-08 and J-09's goldens have FAILed into the mass-void for two rounds running, and every opened frame
(iter-72, iter-73, iter-74) shows the same signature — a fully-styled app early in the session, then an
unstyled/asset-less shell frozen on "Checking backend…"/"Checking board status…" for a contiguous window,
then healthy again minutes later with no restart. This is confirmed to be the frontend serving defect, not
selector drift (`state/goldens-regen-pending` still lists J-05..J-09 and MUST NOT be acted on — the binding
"Do not redo" from iteration-state). Lessons iter-72(2/2), iter-73, and iter-74(2/2) all bind here: open
every frame in a voided batch, sort by capture time, and never accept a lane's own "transient/concurrent
load" label without checking timestamps and log content. `scripts/automation/lib/common.sh` already names
this exact failure class in its own comments (`_next_build_is_corrupt`, lines ~802-821: "a stale/corrupt
.next build (a 'next build' likely ran against the live 'next dev' .next)"), and offers a `NEXT_DIST_DIR`
isolation escape hatch — but its self-heal (`_start_service_with_retries`) only fires during BOOT-time
health probing (5xx + `MODULE_NOT_FOUND` grep), not against an already-running, already-healthy session that
degrades mid-run. `scripts/start-frontend.sh`'s build-if-stale step (`_build_is_stale_or_missing` → `next
build`) writes into the SAME `.next` `DIST_DIR` a live `next start` process may already be bound to and
serving from — the first concrete mechanism to rule in or out. This iteration is depth `lean` per the
evaluator's binding recommendation: no full trigger holds (prior verdict CONTINUE not ESCALATE, prior
coherence PASS, only 2 consecutive lean iterations against a cadence of 6, and this is a harness repair on
already-passing journeys, not a brand-new full-stack journey).

## IN SCOPE

### Backend / Harness (test infrastructure — not application code)
- [ ] Root-cause the intermittent unstyled/asset-less QA-frontend window (iter-72/c, carried iter-72 →
  iter-74, 3 rounds) by correlating `QA_FRONTEND_LOG` / the frontend start-command's own log against the
  timestamp of any broken frame this iteration captures. Confirm or rule out: a `next build` invocation
  (triggered by `scripts/start-frontend.sh`'s `_build_is_stale_or_missing` check) writing into the same
  `.next` `DIST_DIR` a live `next start` process is already serving from, mid-session.
- [ ] Fix the confirmed mechanism (candidates: refuse to re-run build-if-stale against a port that is
  already answering healthy; build into a staging `NEXT_DIST_DIR` and atomically swap in; or the actual
  cause found by the log correlation above) so a full browser-qa capture pass across J-01..J-09 produces
  zero unstyled/asset-less frames. Byte-identical served content for unchanged routes is required — this
  is a serving-mechanics fix, not a content change.
- [ ] Do NOT regenerate the J-05..J-09 golden scripts (binding "Do not redo"; `state/goldens-regen-pending`
  points at the wrong fix — confirmed cause is the frontend, not selector drift).
- [ ] TC-10 (iter-72/b, carried): with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=data_overview_endpoint` armed,
  capture the `/data` honest-fallback screenshot showing `GET /api/data`'s graceful/contained failure state
  (the unguarded fault hook at `apps/backend/app/api/data.py:119` exists specifically for this evidence) —
  OR, if this evidence is judged no longer needed, remove that unguarded fault-injection call and its
  docstring, and remove/adjust any test asserting on it.
- [ ] Delete the stray zero-byte `=` file at the repo root (iter-74/c; created 2026-08-13, unrelated to any
  tracked change).

### Frontend
- [ ] No product UI/behavior change anticipated. If the confirmed root cause requires a frontend build
  script/config change (e.g. `NEXT_DIST_DIR` isolation), it is serving-mechanics only — no page, component,
  or displayed-value change.

### New user-facing capability
None — this is a harness/evidence-integrity fix. No new capability ships to end users.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — `/data`, `/backtest`, and the global readiness badge keep their existing rendering; only the QA
capture harness's reliability changes.

### Product surface delta
None visible to a real user; the deliverable is trustworthy regression evidence for J-08 and J-09 and for
the replay lane generally.

### Blueprint conformance
No new surfaces. J-08 keeps its existing home (`/backtest`, `GET /api/backtest`'s `evidence_by_horizon` +
`evidence_status`/`evidence_generated_at`); J-09 keeps its existing homes (global readiness badge + `/data`
BackgroundComputePanel); TC-10's coverage-payload honest-fallback evidence is the already-registered
Coverage payload Data Contract row's existing `/data` home. No edit to `blueprint.md` is needed this
iteration.

### Data-contract additions
None. No new displayed value, computing module, or serving endpoint is introduced. TC-10's screenshot
documents EXISTING behavior of the already-registered Coverage payload row (`data_manager.coverage_from_
storage`, served by `GET /api/data`) under an already-armed test-only fault hook — no second producer.

## OUT OF SCOPE

- The `scripts/automation/browser-qa-phase.sh` TARGET_JOURNEYS line-ordering bug — a DIFFERENT, long-
  standing, explicitly owner-gated build-system-script fix (25+ rounds asked, still unanswered). Do not
  touch it this iteration; it is not the same defect as the frontend-serving issue above.
- Rendering `stale_for_s` on the readiness badge/preflight banner (iter-72/f) — queued for its own **full**
  round after this verification repair, per iter-74's own ordering.
- J-07's `[NEW]` walkthrough steps, J-05's walkthrough, and J-06's page timings into `reports/perf-
  budgets.md` — rides-along-only per the evaluator, never this iteration's goal; do not let them block DoD.
- iter-33/g (Regime Lab) — deferred a 41st time; do not schedule without explicit owner direction.
- J-07 step 3's VmPeak margin, `pool_size`/`max_overflow`/`pragmas.cache_size` — DONE (binding "Do not
  redo"); do not re-measure or re-tune.
- Any uninterrupted full-`rebuild` drill on this host — defeated 4x; not needed for this iteration's scope
  anyway.
- Owner-gated decisions (2s health-ceiling policy for long jobs, B-1107 concurrent-heavy-compute cap, cost-
  budget sanction) — carried forward in the owner paragraph, not agent-actionable this iteration.
- Full-depth lanes (audit, ux-regression, functional test plan) — this is lean depth; the TC- scenarios
  below are this iteration's test plan.

## DEFINITION OF DONE

- [ ] The QA-frontend intermittent unstyled/asset-less serving defect is root-caused with log evidence
  (timestamp-correlated) and fixed — verified by a zero-broken-frame capture pass.
- [ ] Target journeys J-08, J-09 pass via browser-qa-agent on FRESH, non-durability-carried evidence
  (`last_verified_iter` advances to `goal-ops-hardening-iter-75`; `evidence_makeup` clears on both).
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-06, J-07 remain green (deterministic replay
  + LLM fallback).
- [ ] No anti-goal violation introduced.
- [ ] TC-10 evidence is filed at `reports/qa/goal-ops-hardening-iter-75-evidence/` (or the unguarded fault
  hook is removed with its test correspondingly updated).
- [ ] The stray zero-byte `=` file no longer exists at the repo root.
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-75-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-08, J-09 (targets, must get fresh non-carried evidence); J-01, J-03, J-04, J-05, J-06, J-07
  (required-still-passing, replay-first with LLM fallback).
- Unit/integration: if `scripts/start-frontend.sh` / `scripts/automation/lib/common.sh` gains a code change,
  extend that file's own self-test harness (the `[common.sh self-test]` block) with a case covering the
  fixed behavior; if `apps/backend/app/api/data.py:119`'s fault hook is removed, update/remove its
  corresponding assertion in `apps/backend/tests/test_api_data.py` (or wherever TC-10's coverage lives).
- Error cases: with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=data_overview_endpoint` armed, `GET /api/data` must
  degrade to a contained, honest failure state — never an unhandled 500 with no UI fallback, and never a
  blank application-error page (AG-8).

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps to at
least one concrete scenario line, numbered sequentially:

- TC-1: given the shared frontend service is already running mid-iteration, when the deterministic replay
  lane captures J-05 through J-09 sequentially, then every resulting frame shows the fully-styled app (no
  frame frozen on "Checking backend…"/"Checking board status…", no missing CSS/JS asset) — zero frames
  match the iter-72/73/74 unstyled-shell signature.
- TC-2: given the harness fix is applied, when the frontend's start-command log is inspected across the
  capture window, then it shows no `next build` invocation overlapping a live `next start` process already
  bound to the same `DIST_DIR`/port — OR, if a different root cause was confirmed instead, the log/evidence
  shows that specific mechanism is closed.
- TC-3: given the harness fix, when browser-qa captures J-09's frame, then the frame's URL and rendered
  content match J-09's actual home (`/data`'s BackgroundComputePanel or the global badge state it is
  testing) rather than a stale `/backtest` URL carried over from a prior journey's navigation (closes the
  iter-74-observed defect).
- TC-4: given J-09's evidence is captured fresh this iteration, when the goal-evaluator scores J-09, then
  `journey-history.json`'s J-09 entry shows `last_verified_iter: goal-ops-hardening-iter-75` and
  `evidence_makeup` absent/false.
- TC-5: given J-08's evidence is captured fresh this iteration, when the goal-evaluator scores J-08, then
  `journey-history.json`'s J-08 entry shows `last_verified_iter: goal-ops-hardening-iter-75` and
  `evidence_makeup` absent/false.
- TC-6: given `TRENDORA_FAULT_INJECT_MEMORY_ERROR=data_overview_endpoint` is armed, when a request hits
  `GET /api/data`, then the `/data` page renders a contained fallback state (not a blank crash page) and a
  screenshot of that state is filed under `reports/qa/goal-ops-hardening-iter-75-evidence/` — OR the
  unguarded fault-injection call at `apps/backend/app/api/data.py:119` is removed along with its docstring
  and any test asserting on it.
- TC-7: given the repo root's stray zero-byte `=` file exists at iteration start, when this iteration's
  diff lands, then `ls -la /home/dennis-chan/Git/trendora/=` returns "No such file or directory".
- TC-8: given the six Required-still-passing journeys (J-01, J-03, J-04, J-05, J-06, J-07), when the
  deterministic replay lane re-verifies them under the fixed harness, then all six report PASS with no new
  FAIL introduced by this iteration's change.

## NOTES

- Binding "Do not redo" carried from iteration-state (unless `docs/goal.md` changed for that item): J-07
  step 3 is DONE (margin 42.3%, `config.yaml` byte-unchanged, no re-tuning `pool_size`/`max_overflow`/
  `pragmas.cache_size`); do not run an uninterrupted full-`rebuild` drill on this host (fire the finalize
  tail from a single-date `backfill` if any measurement is ever needed again — not expected this round); do
  not regenerate the J-05..J-09 goldens; `docs/goal.md` Ground truth + Addendum 38's test count are already
  corrected; the readiness serve-stale + post-lock recheck (iter-72) is DONE, no code touch; iter-33/g
  (Regime Lab) stays deferred.
- Lessons directly binding this iteration: iter-72 (2 of 2) — a lane's own "transient/concurrent load"
  label is a hypothesis, cite timestamps and open the frame; iter-73 — a deterministic-replay lane runs
  SEQUENTIALLY, so an environment break mid-way masquerades as a per-journey defect, sort FAILed frames by
  capture time before accepting any lane's automatic explanation; iter-74 (2 of 2) — open EVERY frame in a
  voided batch, not a sample, since a genuine per-journey defect can hide inside an otherwise-harness batch.
  Given this iteration's own job IS fixing the breaker these lessons describe, its own regression-replay
  results this round should get the same "open every frame" scrutiny before being trusted.
- If the log correlation in TC-2 does NOT confirm the `next build`/`next start` clobber hypothesis, do not
  force that fix — follow the log evidence to whatever mechanism it actually shows, and record the
  ruled-out hypothesis plainly in the dev handoff so the next reader doesn't re-chase it.
- Uncommitted working-tree changes present at iteration start (`apps/backend/app/engine/data_manager.py`,
  `apps/backend/app/engine/research.py`, `apps/backend/tests/test_regime_lab.py`,
  `apps/frontend/app/research/_labs.tsx`, `apps/frontend/lib/api.ts`) are NOT part of this iteration's scope
  (Regime Lab / research-lab surfaces are unrelated to J-08/J-09 and iter-33/g stays deferred) — do not
  build on top of them without first confirming with `git log`/`git blame` whether they are stray leftovers
  from a prior interrupted run; if they are stray, they should be reverted/stashed before this iteration's
  own diff is authored so the iteration's diff stays attributable to this iteration's own scope.
- Owner paragraph carries forward unchanged (not agent-actionable): the 2-second health-ceiling policy for
  long vs. short jobs; B-1107 (bounding concurrent heavy computations); permission to fix the DIFFERENT,
  owner-gated `browser-qa-phase.sh` TARGET_JOURNEYS ordering bug; and a cost-budget sanction decision (14
  consecutive over-budget rounds on file as of iter-74).
