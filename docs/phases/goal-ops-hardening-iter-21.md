# Goal Iteration 21 — Close J-08 on complete evidence (TC-13/TC-14 consolidation, zero code changes)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 21
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-08
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05
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

With the owner-authorized TC-13 (`/backtest` ≤1.5 s budget under a concurrent-ingest overlay — PASS, 0/4096
breaches) and TC-14 (disruptive J-04 kill/restart + checkpoint survival — PASS) measurements now in hand from
the operator, this iteration adds the one missing piece — a fresh, current-build browser confirmation of
`/backtest`'s literal small-single-day-backfill ready→refreshing→ready state-machine — so the goal-evaluator
can score J-08 on complete evidence; J-06/J-07 stay exactly where they are, pending the owner's still-open
transient-contention budget decision. No product code changes ship this iteration.

## BACKGROUND

**What changed since the iter-20 STALL.** iter-20 correctly halted because every remaining path to
`passing` for J-06/J-07/J-08 was owner-owned (decision tree C.2): (1) authorize TC-13, (2) authorize TC-14,
(3) decide the transient-contention budget treatment. The owner chose **direction 1** and the operator ran
TC-13 and TC-14 under the full host-guard ritual (`reports/perf-budgets.md` §"Post-STALL owner-authorized
measurements", `runs/goal-ops-hardening-iter-21/operator-tc13-tc14-evidence.md`): **TC-13 PASS** (0/4096
breaches, max 429 ms, vs. the iter-16 baseline 11/68 @ 12,655 ms — a ~30× margin under the *exact*
concurrent-ingest condition J-08 steps 1–2 describe) and **TC-14 PASS** (Part A: `kill -9` → restart →
`ok/ready` in ~25 s; Part B: a wide backfill checkpointed to `dates_done 1366/2904`, `kill -9` mid-run,
restart shows `status: interrupted`, the checkpoint preserved, not reset). Per the explicit operator note,
this evidence is fresh and owner-authorized — **this iteration does not re-run either measurement.** Item
(3) — the transient in-process contention during the SEPARATE historical background-compute window
(3.0–6.3 s `/backtest`, max 1.60 s `/api/health`, `reports/perf-budgets.md` "Iteration 20") — is **still
open**; the operator's evidence note is explicit that it is "separate from and not contradicted by TC-13."

**Target-selection rubric applied.** Rule 1 (regressed first): N/A — iter-20's eval recorded no
`passing→failing` transitions. Rule 2 (consolidation before features): N/A — iter-20's `coherence.md` is
`COHERENCE-PASS`, no mandate. Rule 3 (unblockers): J-08 is the correct pick — TC-13 directly closes the ONE
blocker (iter-20's item 1) that was specific to J-08's own step-1/2 scenario; J-06/J-07's blocker (item 3,
the transient-contention residual) is untouched by TC-13/TC-14, so picking J-08 alone is the honest "next
chunk," not a claim that J-06/J-07 also advance. Rule 4 (smallest spec wins): only one real candidate this
iteration; no tie to break. Rule 5 (never bundle two risky changes): moot — zero code changes ship. **Rule 6
(don't pick a human-blocked journey) governs why J-06/J-07 are NOT targeted**: their sole blocker is
explicitly an owner budget-amendment call (accept-and-log / sanction a redesign / rescope to steady-state
reads — iter-20 eval's 3-way fork), not agent work, and the operator's note reconfirms it is still open. I
do not re-plan either previously-rejected technical fix (off-process compute, full historical precompute)
and I do not invent a budget-amendment authorization on the owner's behalf — that would be exactly the kind
of silent loosening this session's evaluators have repeatedly refused to do (iter-12/15/16 precedent).

**Depth: lean — no full trigger holds.** (1) Structural/cross-cutting: N/A, zero source files change this
iteration. (2) Data model: N/A, no Data-Contract value's computing module or serving endpoint changes — this
iteration only reads/reports existing values. (3) Prior ESCALATE: the last dispatched verdict was `STALLED`,
not `ESCALATE` — the mandatory-full trigger does not fire (STALLED is a halt-for-owner-decision, not the
fail-open signal ESCALATE represents). (4) Hardening cadence: 0 consecutive lean iterations dispatched
(iter-20 was full, resetting the counter) — the cadence-4 backstop does not fire. Running the full 11-step
pipeline for a zero-diff evidence-consolidation pass would itself violate Simplicity First; the lean cycle
(developer → reviewer → browser-qa) is exactly sized to (a) have the developer independently re-verify this
spec's own investigation claims before writing the handoff, and (b) have browser-qa capture the one piece of
missing live evidence.

**Lessons applied.** **iter-17**: "is the cost proven, or merely unmeasured?" — a PROVEN hard cost routes to
the owner, an UNMEASURED one routes to an agent instrumentation pass first. The transient-contention residual
is proven (root-caused to in-process CPU/GIL contention during the bounded background compute, iter-20's own
measurement) — so it correctly stays owner-routed here, not reopened as a new agent investigation. **iter-20**
(meta-lesson): "an iteration can be a complete, correct success at its stated target yet move NO journey to
passing... STALLED is the honest verdict even after real progress" — the mirror image applies here: this
iteration may look small (zero code diff) yet still be exactly the right, honest unit of work, because it is
sized to what is actually agent-tractable right now. **iter-8** (test-file diff discipline, applied by
analogy): before proposing ANY change adjacent to an existing test's assumptions, re-verify what the test
actually depends on rather than trusting a superficial "this looks like dead code" read — this is exactly
what this iteration's own investigation (below) did with the iter-20 coherence-auditor's dangling-import
advisory, and exactly why that advisory is NOT applied this iteration.

**Investigation finding — the iter-20 coherence-auditor's advisory is NOT a safe pure-lint fix.** The iter-20
`coherence.md` flagged `apps/backend/app/mcp/tools.py:38`'s `forward_aggregates_ingest_cached` import as
"dangling/unused... flagging for the reviewer's or next iteration's lint pass." Direct verification this
iteration found two things the advisory missed: (a) the IDENTICAL unused-import shape also exists at
`apps/backend/app/api/backtest.py:75` (confirmed: zero call sites of `forward_aggregates_ingest_cached(` in
either file — both files now only reach it transitively via `ensure_historical_forward_aggregates_dispatched`,
which is a different function defined in `app.engine.forward_testing`); (b) BOTH imports are load-bearing
`monkeypatch.setattr` targets for four existing tests in `test_forward_testing_serving_split.py`
(`test_backtest_route_is_latest_never_reaches_ingest_or_compute`,
`test_backtest_route_is_latest_not_yet_computed_is_honest_200`,
`test_query_backtest_mcp_tool_is_latest_never_reaches_ingest_or_compute`,
`test_query_backtest_mcp_tool_not_yet_computed_mirrors_endpoint`), each of which does
`monkeypatch.setattr(<module>, "forward_aggregates_ingest_cached", _boom)` with pytest's default
`raising=True` — removing either import would raise `AttributeError` at that call, breaking all four tests
outright, not a safe no-op. A secondary, genuinely useful but NON-blocking finding: because iter-20's dispatch
refactor moved the actual historical compute call inside `forward_testing.py`'s own module-local name, these
four monkeypatches no longer guard the code path they were written to guard (the real guarantee now lives in
`backtest.py`'s `if not is_latest` gate + the dispatch function's own logic) — a legitimate test-hardening item
for a FUTURE, properly-scoped iteration, not this one. Both findings are written into `blueprint.md`'s
iter-21 comment-block paragraph and must be restated (not merely referenced) in this iteration's dev handoff.

## IN SCOPE

### Backend

- [ ] No product/backend source changes. Independently re-verify (read-only; do not trust this spec's claim
  blindly) that `apps/backend/app/mcp/tools.py:38` and `apps/backend/app/api/backtest.py:75`'s
  `forward_aggregates_ingest_cached` imports are each a `monkeypatch.setattr` target in
  `apps/backend/tests/test_forward_testing_serving_split.py` (the four tests named in BACKGROUND) before
  writing the dev handoff's investigation section.
- [ ] Confirm via `git status`/`git diff` at completion that zero files under `apps/backend/` changed.

### Frontend

- [ ] No frontend source changes. The J-08 state-machine confirmation (TC-1/TC-2 below) is browser-qa-agent's
  own Chrome-MCP pass against the existing, unchanged `RefreshingEvidenceBanner` and ready-state display —
  not a code change.
- [ ] Confirm via `git status`/`git diff` at completion that zero files under `apps/frontend/` changed.

### New user-facing capability

None. Zero product code changes this iteration.

### New information displayed

None. `reports/perf-budgets.md` gains no new dated section this iteration (TC-13/TC-14 are already recorded
there by the operator) beyond whatever raw timing browser-qa's own capture produces as supporting evidence —
a measurement artifact, not a served runtime value, already registered in the Data Contract.

### New user actions

None.

### UI surface changes

None. `/backtest` (existing) is the only page exercised, via its existing states.

### Product surface delta

None — a verification/evidence-consolidation iteration. The product surface is unchanged; only the
completeness and currency of J-08's evidence changes.

### Blueprint conformance

No new surfaces. This iteration's browser confirmation lives entirely inside J-08's existing home
(`/backtest` + MCP `query_backtest`) already registered in `blueprint.md`'s Information Architecture table.
`blueprint.md` has been updated this iteration: a new "iter-21 update" paragraph appended to the comment
block (documenting TC-13/TC-14 consolidation and the dead-import investigation finding), and a short sentence
appended to the "Page performance budgets" row's Notes cell pointing to the same. No nav-skeleton change —
`blueprint.reapproval-requested` was NOT written.

### Data-contract additions

None. `evidence_status` / `evidence_generated_at` / `evidence_asof` / `evidence_by_horizon` keep their exact
existing shape, same computing module (`app.engine.forward_testing`), same two serving endpoints
(`GET /api/backtest`, MCP `query_backtest`). This iteration reads and re-confirms values already registered;
it introduces no second producer, no second endpoint, no new field.

## OUT OF SCOPE

- **Re-running TC-13 or TC-14.** Both are DONE and PASS, dated 2026-07-25, owner-authorized. Do not re-plan
  or re-trigger either measurement this iteration.
- **Any technical mitigation for the transient in-process contention** (off-process compute, full historical
  precompute, thread-priority/GIL-pacing experiments, or any other untested third option). The only two
  concrete mitigations were already evaluated and rejected as unbounded across iter-15/iter-20 (see goal.md's
  own "cannot be precomputed" carve-out and iter-20's BACKGROUND); this iteration does not reopen that
  question or invent a new one without owner sanction.
- **Deciding the transient-contention budget treatment on the owner's behalf.** An explicit, still-open OWNER
  decision (3-way fork: accept-and-log / sanction a redesign / rescope to steady-state reads — iter-20 eval).
  No agent, and not this decomposer, may resolve it.
- **Removing `mcp/tools.py:38`'s or `backtest.py:75`'s `forward_aggregates_ingest_cached` import.**
  Investigated and confirmed NOT safe as a pure lint fix this iteration (see BACKGROUND) — flagged for a
  future, properly-scoped test-hardening pass, not this one.
- `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`'s cross-`asof_key`/version fallback
  logic, and `ensure_historical_forward_aggregates_dispatched` — untouched (binding, `iteration-state.md`
  "Do not redo").
- `main.py`'s boot sequence, `app/api/health.py`, `app/engine/readiness.py`, `app/engine/warmup.py`,
  `scripts/*` — untouched (binding, "Do not redo").
- The oldest-date (2005) `scorecard_ms` + `resolved_run_ms` optimization (`backtest.py:162-177`) —
  agent-tractable but closes NO journey alone per iter-20's own evaluator; not manufactured as busywork here.
- The `demo.sh ops-hardening --session-live` walkthrough — settled non-autonomous deliverable since iter-12;
  not part of this iteration's DoD.
- The `loaded_engine`-dependent heavy test fixtures (`test_api_backtest.py`'s full fixture,
  `test_data_manager.py`'s heavy-ingest cases) — carried, "cite, do not run wholesale" (binding, "Do not
  redo"); not run this iteration.
- The full pytest suite — never run wholesale; any targeted test invocation this iteration stays host-guard
  confined (AG-10 hygiene), and none is expected since no source changes ship.

## DEFINITION OF DONE

- [ ] `reports/perf-budgets.md` §"Post-STALL owner-authorized measurements — TC-13 + TC-14" and
  `runs/goal-ops-hardening-iter-21/operator-tc13-tc14-evidence.md` are cited by exact section/path in the
  dev handoff (TC-9)
- [ ] A fresh iter-21-dated browser-qa capture shows `/backtest`'s `is_latest=true` state-machine transition
  ready → refreshing (older `evidence_asof`, within budget) → ready (new `evidence_asof`, within budget)
  across a literal small single-day backfill (TC-1, TC-2, TC-5)
- [ ] The dev handoff states explicitly whether any source file changed (expected: none) and restates the
  dead-import investigation finding (both file locations, both test-coupling findings) rather than merely
  citing this spec (TC-6, TC-9)
- [ ] Required-still-passing journeys J-01, J-03, J-05 remain green via deterministic golden replay; J-04
  remains green via TC-14's fresh operator evidence (not a fresh browser-qa capture, which is expected to
  SKIP the disruptive steps as it always has) (TC-4, TC-7, TC-8)
- [ ] No anti-goal violation introduced — the triggered small backfill runs against the committed `"seed"`
  fixture (AG-9) via `scripts/start-backend.sh` with host-guard caps intact (AG-10); zero product-code diff
  otherwise (TC-11)
- [ ] Target journey J-08 is evaluated by the goal-evaluator against this iteration's combined evidence
  (TC-13 + this iteration's fresh TC-1/TC-2 capture + the carried TC-09 never-warmed empty state) — this
  spec does not itself declare J-08 passing (TC-3)
- [ ] J-06/J-07 remain explicitly flagged as blocked solely on the owner's still-open transient-contention
  budget-treatment decision — not silently dropped, not re-attempted via a previously-rejected fix (TC-10)
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-21-dev.md` (TC-9)

## TESTING REQUIREMENTS

- Browser: J-08 (target — fresh ready→refreshing→ready state-machine confirmation via a literal small
  single-day backfill, real Chrome via browser-qa-agent). Required-still-passing regression: deterministic
  golden replay for J-01/J-03/J-05; the LLM browser-qa lane for J-04 (expected to SKIP the disruptive steps
  again, per the established session pattern since iter-15 — TC-14's fresh operator evidence is the
  substitute, not a gap).
- Unit/integration: none new — zero source changes are planned. If the developer's independent re-verification
  (IN SCOPE) finds this spec's test-coupling claim inaccurate in some detail, correct ONLY the dev handoff's
  documentation of it — do not expand into a code change without a fresh spec.
- Error cases: N/A — no new input surface or behavior change this iteration.

Test-first contract:

- TC-1: given the current default (`is_latest=true`) `/backtest` view already serving `evidence_status ==
  "ready"`, when a small single-day backfill is submitted via `/data` (bumping `dataset_version` and
  scheduling the finalize warm) and `/backtest` is reloaded while that warm is still in flight, then the
  response returns HTTP 200 within 1.5 s with `evidence_status == "refreshing"` and `evidence_asof` equal to
  the PRIOR (not the new) as-of date.
- TC-2: given TC-1's triggered run's `aggregates_refreshed` list (read via `GET /api/data`) includes
  `"forward_aggregates"`, when `/backtest` is reloaded again, then the response returns HTTP 200 within 1.5 s
  with `evidence_status == "ready"` and `evidence_asof` equal to the NEW as-of date.
- TC-3: given `reports/perf-budgets.md`'s "TC-13" section (0/4096 breaches, max 429 ms, dated 2026-07-25) and
  TC-1/TC-2's fresh iter-21 capture, when the goal-evaluator reads both together, then J-08 steps 1–2's
  ≤1.5 s serving-budget clause has both a stress-tested numeric proof and a literal small-single-day
  rendered-state proof from the same unchanged build.
- TC-4: given `reports/perf-budgets.md`'s "TC-14" section (Part A: `kill -9` → restart via
  `scripts/start-backend.sh` → `ok/ready` in ~25 s; Part B: run 164 checkpointed to `dates_done 1366/2904`,
  `kill -9` mid-run, restart shows `status: interrupted`, `dates_done: 1366/2904` preserved, `finished_at`
  stamped by recovery), when the goal-evaluator reads it, then J-04's disruptive kill/restart +
  checkpoint-survival contract has evidence dated 2026-07-25, distinct from the carried iter-15 evidence it
  relied on through iter-20.
- TC-5: given TC-09's (iter-17) never-warmed `not_yet_computed` empty-state capture on a disposable DB copy,
  when this iteration's diff is inspected, then it shows zero changes to `resolved_forward_aggregate_evidence`,
  the `not_yet_computed` `EmptyState` component, or any file in the never-warmed code path, so TC-09's
  evidence remains valid without a fresh capture this iteration.
- TC-6: given the coherence-auditor's iter-20 advisory naming `apps/backend/app/mcp/tools.py:38` as a
  dangling unused import, when this iteration's dev handoff addresses it, then it states (a) the identical
  unused-import shape also exists at `apps/backend/app/api/backtest.py:75` (not previously named), and (b)
  that `test_forward_testing_serving_split.py`'s four `is_latest`-never-computes tests
  (`test_backtest_route_is_latest_never_reaches_ingest_or_compute`,
  `test_backtest_route_is_latest_not_yet_computed_is_honest_200`,
  `test_query_backtest_mcp_tool_is_latest_never_reaches_ingest_or_compute`,
  `test_query_backtest_mcp_tool_not_yet_computed_mirrors_endpoint`) `monkeypatch.setattr` those exact names
  with the pytest default `raising=True`, so neither import was removed this iteration.
- TC-7: given J-01's and J-03's stored golden-replay scripts, when executed via deterministic replay against
  the current build (which includes the small backfill TC-1 triggers), then each records a PASS outcome in
  the regression-replay-results artifact.
- TC-8: given J-05's acceptance steps (aggregates precomputed at ingest, never on the fly), when re-verified
  against the same small backfill TC-1 triggers, then the LLM browser-qa fallback confirms the run's
  `aggregates_refreshed` list is populated with no request-path recompute observed.
- TC-9: given this iteration reaches completion, when `docs/handoffs/goal-ops-hardening-iter-21-dev.md` is
  inspected, then it exists, states explicitly that zero product source files changed, cites
  `reports/perf-budgets.md` §"Post-STALL owner-authorized measurements — TC-13 + TC-14" and
  `runs/goal-ops-hardening-iter-21/operator-tc13-tc14-evidence.md` by exact path, and restates the dead-import
  investigation finding (TC-6) in its own words, not by reference only.
- TC-10: given the transient in-process contention residual recorded in `reports/perf-budgets.md`
  "Iteration 20" (3.0–6.3 s `/backtest`, max 1.60 s `/api/health` during the ~30 s historical
  background-compute window), when this iteration's diff and dev handoff are inspected, then neither
  contains an off-process or full-historical-precompute mitigation attempt (both previously rejected as
  unbounded) nor a silently loosened budget number, and the dev handoff/NOTES name it as the sole open item
  blocking J-06/J-07.
- TC-11: given TC-1's small single-day backfill is submitted, when its provider/source and launch process are
  inspected, then the job's `provider` is the committed local `"seed"` fixture (AG-9, not a live network call)
  and the backend serving it was launched via `scripts/start-backend.sh` with host-guard caps intact (AG-10)
  — matching every prior iteration's ritual, not a new exception.

## NOTES

- **OWNER DECISION still outstanding, not to be invented by any agent:** the transient-contention
  budget-treatment fork (iter-20 eval) — (a) accept-and-log a `perf-budgets.md` amendment for reads taken
  during the bounded ~30 s historical background-compute window, (b) sanction an off-process/precompute
  redesign despite its unbounded-cost concern, or (c) read ≤1.5 s/≤0.1 s as governing steady-state
  (non-background-window) reads only. This is the SOLE remaining blocker for J-06/J-07; nothing in this
  iteration attempts to resolve it.
- **GOAL_ACHIEVED is not reachable this iteration regardless of J-08's outcome** — J-06/J-07 stay `partial`
  pending the owner decision above. If the evaluator scores J-08 `passing` this iteration, the correct next
  decomposer move is the same "holding spec" pattern iter-12 pioneered: do not manufacture new scope while
  J-06/J-07 remain owner-blocked; a one-line "all remaining work is human-blocked" spec is appropriate if no
  other tractable journey exists.
- **A future, properly-scoped test-hardening item (not this iteration):** `test_forward_testing_serving_
  split.py`'s four `is_latest`-never-computes monkeypatches (see BACKGROUND) no longer guard the code path
  they were written to guard, post iter-20's dispatch refactor. A future iteration could retarget them at
  `app.engine.forward_testing`'s module-local `forward_aggregates_ingest_cached` name (or at
  `ensure_historical_forward_aggregates_dispatched`) to restore a live regression guard, and only then would
  removing the now-genuinely-dead imports in `backtest.py`/`mcp/tools.py` be safe. This is a real, non-blocking
  finding from this iteration's investigation — not itself a coherence violation, and not journey-blocking.
- **Operator resume note (informational, not actionable by this spec):** the operator's evidence file records
  that the interactive pump conversation which ran iters 16–20 hit its 200-subagent session cap producing the
  TC-13/TC-14 evidence, hence the `/goal-resume` that dispatches this iteration runs in a fresh conversation.
  No action needed from this spec; noted for continuity.
- No `assumptions.md` entry this iteration: no goal-text ambiguity was resolved by interpretation. The
  potential "does TC-13's wider ~52-day overlay satisfy J-08 step 1's literal 'small single-day backfill'
  wording" question is deliberately NOT resolved by asserting an interpretation — TC-1/TC-2 above supply the
  literal small-single-day scenario directly, so the evaluator has both readings' evidence rather than needing
  to accept one reading on my say-so.
