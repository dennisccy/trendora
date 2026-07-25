# Goal Iteration 22 — Re-score J-06/J-07 against the owner's BCW budget amendment (zero code changes)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 22
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-06, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-08
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
    **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
    values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or
    alpha claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's
    computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars >
    as-of; never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from
    the post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader
    pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing
    consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest
    "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are
    forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the
    committed seed / local provider fixtures — no live external network calls or paid data services may be
    introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills, full-universe
    rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched only via the project
    launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those scripts MUST apply the host
    caps declared in `project-extensions/host-guard/host-guard.env` whenever that file is present
    (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`, `malloc_arena_max`). Never remove, weaken, or
    bypass these caps: stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless
    of test outcomes. The ceilings are a physical constraint of the current host (two instant hardware
    resets under all-core vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance
    budget to optimize away. *(critical)*

## GOAL

Re-score J-06 ("Pages load only what they need") and J-07 ("Heavy aggregates never take the service down")
against the owner's dated, committed 2026-07-25 background-compute-window (BCW) budget amendment in
`reports/perf-budgets.md`, adding one fresh iter-22-dated confirming measurement (plus J-07 step 3's overdue
`VmPeak` reading) — with zero product source changes.

## BACKGROUND

**What changed since the iter-21 STALL.** iter-21 correctly halted with the smallest residual yet: J-08 and
J-04 closed (5 of 7 journeys passing), and the sole remaining blocker for J-06/J-07 was a human-owned budget
decision (decision tree C.2) — the transient in-process CPU/GIL contention during the bounded ~30 s historical
background-compute window (`ensure_historical_forward_aggregates_dispatched`, iter-20), which breaches the
steady-state ≤1.5 s `/backtest` / ≤0.1 s `/api/health` budgets by latency alone (never availability — no
wedge, readiness never drops). The owner picked **direction 1 — accept-and-log** (per the coordinator's
operational note and `reports/perf-budgets.md` § "OWNER BUDGET AMENDMENT — reads during a bounded
background-compute window (2026-07-25)"): a new named BCW exception — `/backtest` ≤ 8.0 s, `/api/health`
≤ 2.0 s, window ≤ 60 s — layered onto the SAME budgets file goal.md's J-06 Acceptance names as the single
source of budget numbers. Steady-state budgets (≤1.5 s / ≤0.1 s) and the concurrent-INGEST case (TC-13,
0/4096 breaches) are explicitly **unchanged** by the amendment; `docs/goal.md` was deliberately not edited.
**No new technical fix for the transient contention is authorized** — the owner explicitly declined
direction 2 (off-process/precompute redesign).

**The amendment's ceiling is already derived from numbers on file.** Its own "Why these numbers" section
cites the exact iter-20 measurements: `/backtest` worst observed during a BCW = 6.32 s (→ 8.0 s ceiling),
`/api/health` worst observed = 1.60 s (→ 2.0 s ceiling), BCW duration ≈ 30 s (→ 60 s bound). All three already
sit inside the new ceiling with margin. This iteration therefore does two things, not one: (a) the cheap,
zero-risk part — cite those already-recorded numbers against the amended table so the evaluator has the
arithmetic re-score explicitly stated; and (b) one proportionate, fresh confirming measurement — because this
session's own recurring lesson (iter-15: "any 'the fix fully accounts for X' claim not yet reconciled against
a live full-scale measurement") and iter-21's own precedent (it added a fresh J-08 state-machine capture
alongside citing TC-13 rather than relying on citation alone) both argue against resting a goal-closing score
solely on iter-20-vintage numbers when a single lightweight re-trigger is cheap and safe to obtain on the
current, byte-unchanged build. This is evidence-gathering *inside* the explicitly authorized re-score task —
not a new mitigation, not new scope. The BCW trigger itself is a **plain `GET /api/backtest?as_of=<date>`
read**, not an ingest/backfill job — iter-20 already produced the original numbers this way, autonomously,
inside its own FULL-depth dispatch, with no owner/operator gating (unlike TC-13/TC-14, which needed
authorization because they specifically exercise the AG-10 ingest-trigger classifier's disruptive/concurrent
scenarios — a concurrent-ingest overlay and a `kill -9`, respectively). This fresh pass is therefore
agent-tractable within this iteration's own lean dispatch, no owner sign-off required.

**Target-selection rubric applied.** Rule 1 (regressed first): N/A — iter-21's eval recorded no
`passing→failing` transitions. Rule 2 (consolidation before features): N/A — iter-21's `coherence.md` is
`COHERENCE-PASS`, no mandate. Rule 3 (unblockers): J-06 and J-07 are the correct — and only remaining —
pick: they are the last two `partial` journeys, share the EXACT SAME residual blocker (the BCW latency
numbers), and closing both is the direct, intended effect of the owner's amendment. Rule 4 (smallest spec
wins ties): no tie — bundling J-06+J-07 together is not "bundling two risky journeys" (Rule 5, which does not
apply — zero code changes ship, so there is no blast radius to separate) but the minimal honest unit of work,
since one fresh measurement pass evidences both simultaneously (J-06 step 2 and J-07 step 2 are the same
`/backtest` + `/api/health` reads). Rule 6 (don't pick a human-blocked journey): J-06/J-07 were human-blocked
through iter-21, but the human already resolved the blocker (the amendment is committed) — this iteration is
now purely agent-tractable re-scoring/measurement work, not a re-plan of the same blocked item.

**Depth: lean — no full trigger holds.** (1) Structural/cross-cutting: N/A, zero source files change this
iteration. (2) Data model: N/A, no Data-Contract value's computing module or serving endpoint changes — this
iteration only reads/reports existing values into the existing measurement artifact. (3) Prior ESCALATE: the
last dispatched verdict was `STALLED`, not `ESCALATE` — the mandatory-full trigger does not fire. (4)
Hardening cadence: 1 consecutive lean iteration dispatched (iter-21); dispatching this iteration lean makes 2,
still below the cadence-4 backstop. **Deviation from the prior evaluator's advisory noted, not silently
dropped:** iter-21's eval.md recommended resuming at full depth ("the next iteration is goal-closing (audit +
closure + ux-regression before the two-key confirm)") but explicitly carved out this exact scenario: *"If the
owner picks option 1 or 3 and the next iteration is a pure re-score with zero diff, lean is a defensible
override."* The owner picked option 1, and this iteration is designed to ship zero product diff — the carved
-out condition is met on the merits, not merely invoked. Running the full 11-step pipeline (planner, test-plan
generation, UI-impact, UI-test-design, ux-regression, auditor, phase-closure-auditor) for a citation-plus
-one-lightweight-measurement pass would itself cut against Simplicity First; the lean cycle
(developer → reviewer → browser-qa) is sized to (a) have the developer independently re-verify the cited
iter-20 numbers and run the one fresh confirming pass, and (b) have browser-qa exercise the
Required-still-passing regression set. Note for the evaluator: goal-mode's coherence-auditor step runs at
BOTH depths (unaffected by this choice, per iter-21's own `coherence.md` precedent).

**Lessons applied.** **iter-11/iter-12**: "any iteration whose DoD says 'record X in `reports/perf-budgets.md`'
while X is produced by browser-qa rather than by the developer" / "any evaluator tempted to accept a
downstream agent's 'may be scored passing' when the recorded measurement breaches the acceptance metric" —
this spec assigns the measurement-and-recording work explicitly to the **developer** (not browser-qa), and
requires the recorded numbers to be read against the amended ceiling literally, not asserted in prose.
**iter-20** (meta-lesson): "an iteration can be a complete, correct success at its stated target yet move NO
journey to passing... STALLED is the honest verdict even after real progress" — the mirror applies here: if
the fresh measurement reproduces contention above the amended ceiling, or a poll returns non-200/untruthful
readiness, that is a real, reportable finding, not something to round away. **iter-21**: the `/backtest`
`RefreshingEvidenceBanner` renders BELOW the fold — any browser capture of it must be full-page or
element-scoped (binding, `iteration-state.md` "Do not redo").

## IN SCOPE

### Backend

- [ ] No product/backend source changes. Independently re-verify (read-only) the amendment's cited iter-20
  numbers against the amended ceiling before writing the dev handoff's re-score section.
- [ ] Run ONE fresh BCW re-trigger: issue `GET /api/backtest?as_of=<a historical date whose evidence_status is
  not `"ready"` under the CURRENT `dataset_version` stamp>` against a backend launched via
  `scripts/start-backend.sh` (host-guard caps intact). If every tried candidate date already reads `"ready"`
  (unlikely — the global stamp has advanced multiple times since iter-20 via TC-13/TC-14/iter-21's own
  small backfill), submit ONE small single-day `backfill` job against the committed `"seed"` provider via
  `/data` to bump the stamp, mirroring iter-21's own TC-1 precedent — never a concurrent-ingest overlay or a
  disruptive kill/restart.
- [ ] While the dispatched background compute is in flight, poll `GET /api/backtest?as_of=<same date>` and
  `GET /api/health` at ~1 request/second until the requested date's `evidence_status` reaches `"ready"` (or
  60 s elapses, whichever comes first); record every sample's latency, HTTP status, and (`/api/health`)
  `readiness` value.
- [ ] Capture the backend process's `VmPeak` via `/proc/<pid>/status` during this pass and compute its margin
  under the configured `server.memory_cap_mb` (closes J-07 step 3's carried gap — not re-recorded since
  TC-13, per iter-21's non-blocking carry-over).
- [ ] Record a new, dated "Iteration 22" section in `reports/perf-budgets.md` containing: the re-score
  citation of iter-20's numbers against the amended ceiling, this iteration's fresh sample series, the
  window-completion time, and the `VmPeak` margin. Do not edit the existing "Iteration 20" or "OWNER BUDGET
  AMENDMENT" sections.
- [ ] Confirm via `git status`/`git diff` at completion that zero files under `apps/backend/` changed.

### Frontend

- [ ] No frontend source changes.
- [ ] Confirm via `git status`/`git diff` at completion that zero files under `apps/frontend/` changed.

### New user-facing capability

None. Zero product code changes this iteration.

### New information displayed

None. `reports/perf-budgets.md` gains one new dated section (a measurement artifact, already registered in
the Data Contract's "Page performance budgets" row) — not a new served/displayed value.

### New user actions

None.

### UI surface changes

None. `/backtest` (existing) is the only page whose behavior is exercised, via its existing, unchanged states.

### Product surface delta

None — a re-score/evidence-consolidation iteration. The product surface is unchanged; only the currency and
completeness of J-06/J-07's evidence against the newly-amended budget table changes.

### Blueprint conformance

No new surfaces. J-06 and J-07 keep their existing cross-cutting homes (`reports/perf-budgets.md` as the
canonical measurement artifact; the global readiness badge + `/backtest` for J-07) already registered in
`blueprint.md`'s Information Architecture table. `blueprint.md` has been updated this iteration: a new
"iter-22 update" paragraph appended to the comment block, and one sentence appended to the "Page performance
budgets" row's Notes cell. No nav-skeleton change — `blueprint.reapproval-requested` was NOT written.

### Data-contract additions

None. This iteration reads and re-confirms values already registered (the `/backtest` + MCP `query_backtest`
evidence payload, `GET /api/health`'s readiness payload); it introduces no second producer, no second
endpoint, no new field.

## OUT OF SCOPE

- **Re-running TC-13 or TC-14.** Both are DONE and PASS, dated 2026-07-25, owner-authorized (binding, "Do not
  redo"). This iteration's fresh trigger is a single historical-as-of `GET`, never a concurrent-ingest overlay
  and never a `kill -9` disruption.
- **Any technical mitigation for the transient in-process contention** (off-process compute, full historical
  precompute, thread-priority/GIL-pacing experiments, or any other untested option). Both concrete mitigations
  were already evaluated and rejected as unbounded (iter-15/iter-20); the owner's chosen resolution IS the
  budget amendment already committed, not a new fix — this iteration does not reopen that question.
- **Renegotiating or editing the `OWNER BUDGET AMENDMENT` section itself.** It is already committed, dated,
  and owner-authorized; this iteration reads and cites it, never edits it. No `docs/goal.md` edit either — J-06's
  Acceptance already declares the budgets file the single source.
- **Removing `mcp/tools.py:38`'s or `backtest.py:75`'s `forward_aggregates_ingest_cached` imports** or
  retargeting the four `is_latest`-never-computes monkeypatches — flagged for a future, properly-scoped
  test-hardening pass (iter-21 finding), not this one.
- Any backfill/fetch/rebuild job beyond the ONE small single-day fallback described in IN SCOPE — no
  full-universe rebuild, no wide-range backfill, no concurrent overlay.
- `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`'s cross-`asof_key`/version fallback
  logic, and `ensure_historical_forward_aggregates_dispatched` — untouched (binding, "Do not redo").
- `main.py`'s boot sequence, `app/api/health.py`, `app/engine/readiness.py`, `app/engine/warmup.py`,
  `scripts/*` — untouched (existing launch scripts are used, not edited).
- J-08's serving split, resolver, or empty state — PASSING, do not reopen (binding, "Do not redo").
- The `demo.sh ops-hardening --session-live` walkthrough — settled non-autonomous deliverable since iter-12;
  not part of this iteration's DoD.
- The `loaded_engine`-dependent heavy test fixtures (`test_api_backtest.py`'s full fixture,
  `test_data_manager.py`'s heavy-ingest cases) and the full pytest suite — never run wholesale (binding).
- The oldest-date (2005) `scorecard_ms` + `resolved_run_ms` optimization (`backtest.py:162-177`) —
  agent-tractable but closes no journey alone; not manufactured as busywork here.
- **Declaring GOAL_ACHIEVED.** This spec does not itself score any journey passing or declare the goal
  achieved — that is the evaluator's and the engine's deterministic-gate/two-key-confirm decision, not this
  decomposer's or this iteration's.

## DEFINITION OF DONE

- [ ] J-06 step 2 and J-07 step 2 are re-scored against the amended BCW budget table, citing the
  already-recorded Iteration-20 numbers (6.32 s / 3.40 s / 3.08 s `/backtest`, max 1.60 s `/api/health`,
  ~30 s window) as already within the new ceiling (TC-1, TC-6)
- [ ] A fresh, iter-22-dated BCW re-trigger is measured: every `/backtest` sample during the window ≤ 8.0 s,
  every `/api/health` sample ≤ 2.0 s, the window completes ≤ 60 s, all HTTP 200 with truthful `readiness`
  throughout (TC-2, TC-3, TC-4)
- [ ] J-07 step 3's `VmPeak` is re-captured during the same fresh pass and its margin under
  `server.memory_cap_mb` recorded (TC-5)
- [ ] TC-13/TC-14 are NOT re-run; no ingest-overlay or kill/restart trigger produces this iteration's evidence
  (TC-7, TC-12)
- [ ] No technical mitigation for the transient contention is attempted — the resolution is the already
  -committed budget amendment, not new code (TC-13)
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-08 remain green (deterministic replay where a
  golden script exists; LLM browser-qa fallback otherwise) (TC-8, TC-9, TC-10)
- [ ] Zero files under `apps/backend/` or `apps/frontend/` changed (TC-11)
- [ ] No anti-goal violation introduced: AG-9 (the BCW trigger is a read, or at most one small seed-provider
  backfill, never a live network call), AG-10 (launched via `scripts/start-backend.sh`, host-guard caps
  intact), AG-3 (served evidence matches the stored row exactly) (TC-12, TC-14)
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-22-dev.md`, stating explicitly whether the
  fresh BCW re-trigger succeeded (and citing exact numbers) or fell back to citation-only (and why) (TC-15)

## TESTING REQUIREMENTS

- Browser: Required-still-passing regression only — deterministic golden replay for J-01/J-03/J-05; the LLM
  browser-qa lane for J-04 (expected to SKIP the disruptive steps again, per the established session pattern
  since iter-15 — TC-14's operator evidence is the substitute, not a gap) and for J-08 (full-page or
  element-scoped capture of the `is_latest=true` state machine, binding "Do not redo"). J-06/J-07 themselves
  have no dedicated UI flow beyond the pages already covered by this regression set — their canonical evidence
  artifact is `reports/perf-budgets.md`, not a browser journey (per `blueprint.md`'s Feature/journey-homes
  table).
- Unit/integration: none new — zero source changes are planned. If the developer's independent re-verification
  finds this spec's cited numbers inaccurate in any detail, correct ONLY the dev handoff's documentation of it
  — do not expand into a code change without a fresh spec.
- Error cases: if the fresh BCW re-trigger cannot be produced this dispatch (e.g., every candidate historical
  date unexpectedly still reads `"ready"` even after the fallback backfill, or the environment cannot sustain
  a ~30-60 s live poll), the dev handoff must say so explicitly and the re-score falls back to citation-only
  (TC-1/TC-6) — never silently invent numbers.

Test-first contract:

- TC-1: given `reports/perf-budgets.md`'s amended BCW ceiling (`/backtest` ≤ 8.0 s, `/api/health` ≤ 2.0 s,
  window ≤ 60 s) and the already-recorded "Iteration 20" section (6.32 s / 3.40 s / 3.08 s `/backtest`, max
  1.60 s `/api/health`, ~30 s window), when the dev handoff cites both together, then it states explicitly
  that all three iter-20 numbers already fall within the amended ceiling.
- TC-2: given a historical `as_of` date whose `evidence_status` is not `"ready"` under the CURRENT
  `dataset_version` stamp, when `GET /api/backtest?as_of=<that date>` is issued, then it dispatches
  `ensure_historical_forward_aggregates_dispatched`'s background compute AND the triggering request itself
  returns HTTP 200 in under 1.5 s (no request-path recompute, J-08's unchanged guarantee).
- TC-3: given TC-2's dispatched background compute, when `GET /api/backtest?as_of=<same date>` and
  `GET /api/health` are each polled at ~1 request/second for the duration of the window, then every
  `/backtest` sample returns HTTP 200 within 8.0 s and every `/api/health` sample returns HTTP 200 with
  `readiness == "ready"` within 2.0 s.
- TC-4: given TC-3's polling series, when the elapsed time from the TC-2 dispatch to the first poll showing
  the requested date's `evidence_status == "ready"` is measured, then it is ≤ 60 s.
- TC-5: given TC-2 through TC-4 are running, when the backend process is inspected via `/proc/<pid>/status`
  during the compute, then `VmPeak` is recorded in `reports/perf-budgets.md` together with its margin under
  the configured `server.memory_cap_mb`.
- TC-6: given the fresh measurement (TC-2 through TC-5) completes, when it is recorded in
  `reports/perf-budgets.md`, then it appears in a NEW dated "Iteration 22" section citing the amended-table
  ceilings it is scored against, without editing the existing "Iteration 20" or "OWNER BUDGET AMENDMENT"
  sections.
- TC-7: given the binding "Do not redo" list (TC-13 and TC-14 done and PASS, never re-run), when this
  iteration's dev handoff and diff are inspected, then neither contains a concurrent-ingest-overlay trigger
  nor a kill/restart trigger — only the single historical-as-of read of TC-2 (or its documented small-backfill
  fallback).
- TC-8: given J-01's and J-03's stored golden-replay scripts, when executed via deterministic replay against
  the current (zero-product-diff) build, then each records a PASS outcome in the regression-replay-results
  artifact.
- TC-9: given J-04's disruptive kill/restart scope-gate (unchanged since iter-15) and its TC-14 evidence dated
  2026-07-25, when this iteration's regression pass runs, then J-04 is carried passing without a fresh
  disruptive replay, while its non-disruptive steps (crashed-state banner absence, logfile inspection,
  run-history rendering) are exercised live via the LLM browser-qa lane.
- TC-10: given J-08's binding "PASSING — do not reopen" status, when this iteration's regression pass runs,
  then a lightweight re-verification (deterministic replay if available, else the LLM browser-qa lane)
  confirms the same `is_latest=true` ready/refreshing/not_yet_computed state machine renders without any code
  change, using a full-page or element-scoped capture for the below-the-fold `RefreshingEvidenceBanner`.
- TC-11: given zero source files are planned to change, when `git status --porcelain` and
  `git diff --stat` are run for `apps/backend/` and `apps/frontend/` at completion, then both are empty.
- TC-12: given AG-9 and AG-10, when TC-2's triggering request and the backend process used for TC-2 through
  TC-5 are inspected, then the request submits no ingest/backfill job (a plain `GET` only, or — in the
  documented fallback — one small single-day `backfill` against the committed `"seed"` provider) and the
  backend was launched via `scripts/start-backend.sh` with host-guard CPU/memory caps applied (verified via
  `/proc`).
- TC-13: given the transient contention's root cause (in-process CPU/GIL contention during the background
  compute, proven in iter-20), when this iteration's dev handoff is inspected, then it contains no off-process
  or full-historical-precompute mitigation attempt and no budget number outside the already-committed
  amendment.
- TC-14: given TC-4's post-warm `ready` state for the fresh as-of date, when its served
  `evidence_generated_at`/`evidence_by_horizon` values are spot-checked against the stored
  `forward_aggregate_cache` row for the same `(asof_key, dataset_version)`, then they match exactly (AG-3
  byte-identity preserved, no code path changed).
- TC-15: given this iteration reaches completion, when `docs/handoffs/goal-ops-hardening-iter-22-dev.md` is
  inspected, then it exists, states explicitly whether the fresh BCW re-trigger (TC-2 through TC-5) succeeded
  or fell back to citation-only (and why, if so), and cites `reports/perf-budgets.md`'s exact new section
  heading by name.

## NOTES

- **OWNER DECISION already made, not to be revisited by any agent:** the transient-contention budget
  treatment is settled — direction 1, accept-and-log — and is now the committed contract via
  `reports/perf-budgets.md`'s "OWNER BUDGET AMENDMENT" section. This iteration applies it; it does not
  re-litigate it.
- **This spec does not declare GOAL_ACHIEVED.** If the evaluator scores J-06 and J-07 both `passing` this
  iteration based on the amended budget plus this iteration's evidence, all 7 Must-have journeys would be
  `passing` — but declaring GOAL_ACHIEVED and running any deterministic-gate/two-key-confirm process is the
  evaluator's/engine's decision, not this decomposer's or this iteration's DEFINITION OF DONE.
- **If J-06/J-07 do NOT both cross this iteration** (e.g., the fresh measurement reproduces a breach beyond
  the amended ceiling, or falls back to citation-only and the evaluator wants live evidence before crediting a
  pass), the honest next decomposer move is the "holding spec" pattern iter-12/iter-21 established: do not
  manufacture new technical-fix scope against a residual the owner already resolved by budget amendment — a
  short spec naming exactly what fresh evidence remains missing is appropriate.
- Depth deviates from the prior evaluator's advisory recommendation (full); see BACKGROUND for the explicit
  trigger-by-trigger justification and the evaluator's own "defensible override" carve-out this iteration
  satisfies on the merits (owner picked option 1; zero product diff planned).
- Non-blocking carry-overs, unaffected by this iteration (unchanged from iter-21's list): retarget
  `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches before removing the now-dangling
  imports; `demo.sh ops-hardening --session-live` walkthrough (settled non-autonomous owner deliverable); run
  `test_api_backtest.py`'s TC-11 + `test_data_manager.py`'s heavy fixtures off the constrained box.
- No `assumptions.md` entry this iteration: the owner's amendment is explicit and unambiguous (a dated,
  scoped table addition), and this spec's choice to add one fresh confirming measurement alongside the pure
  citation is a routine scoping decision, not a resolution of a goal-text ambiguity.
