# Goal Iteration 79 — Closeout confirmation under the settled completion rule

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 79
- **Mode:** next
- **Depth:** evidence
- **Frontend Present:** no
- **Target journeys:** J-01, J-03, J-04, J-05, J-06, J-07, J-08, J-09
- **Required-still-passing journeys:** (same 8 — this is a full-session closeout confirmation; there are no other Must-have journeys in this session)
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

Re-verify all 8 Must-have journeys fresh, under the now-fixed closure gate and browser-qa harness, and hand the evaluator a clean, ungated round so it can apply the owner's 2026-08-13 completion-rule amendment and — if the deterministic conditions hold — declare GOAL_ACHIEVED.

## BACKGROUND

`journey-history.json` shows **zero remaining FAILING or PARTIAL journeys**: all 8 (J-01, J-03,
J-04, J-05, J-06, J-07, J-08, J-09) are `passing`, each with evidence produced fresh at iter-78
(replay 5/5 first-pass, LLM lane 11/11, coherence COHERENCE-PASS, 0 unresolved critical anti-goal
violations). Per this agent's own rule for that state, this iteration does not manufacture new
product work — it targets all 8 journeys for a closeout-confirmation pass rather than the usual
1-3, because the session's actual remaining blocker was never a failing journey: it was (a) which
reading of "no unresolved anti-goal violations" governs GOAL_ACHIEVED, and (b) a false-positive in
`closure_gate.py` and a routing-order bug in `browser-qa-phase.sh` that recorded complete,
correct rounds as `blocked`. The owner answered both in the 2026-08-13 "Additional binding notes"
amendment to `docs/goal.md`: the completion rule now scopes "unresolved anti-goal violations" to
**critical** severity only (146 standing minor ledger entries are reported at close, not gated
on), and both harness files are owner-approved and already fixed (quoted-span + negated
backend-only exclusions in `closure_gate.py`; `TARGET_JOURNEYS` now assigned before
`replay_lane_partition_and_verify` in `browser-qa-phase.sh`). `CHAIN_EVIDENCE_MICRO_PATH=false`
is also set for the remainder of this session. No journey text or anti-goal text changed.

Depth is **evidence** because the evaluator's recommendation is binding by default and no escape
condition holds here: the prior verdict was STALLED (not ESCALATE/REGRESSION), the last coherence
verdict was COHERENCE-PASS, the hardening cadence counter is 0/6, and no brand-new full-stack
journey exists. Nothing in `apps/backend/app` or `apps/frontend` has changed since iter-78's
fresh evidence was captured (confirmed: `git diff` against HEAD touches only `docs/goal.md`,
`closure_gate.py`, `browser-qa-phase.sh`, and session bookkeeping/report files) — so this round's
job is to run capture + evaluation only, under the corrected harness, and let the evaluator score.
This is the rule-7 exception in substance even though iter-78's own next-step framed it as two
options: the owner's amendment resolves that framing decisively toward "go straight to the success
confirmation — every journey holds fresh, independently checked evidence" (iter-78 eval, option a).

**Binding carries from `iteration-state.md` — do NOT redo:** J-07 steps 3-4 (VmPeak margin,
induced-pressure abort) and J-04 steps 3/5/6 (restart/crash/logfile) stand on their 2026-07-31 and
prior-round drills while `apps/backend/app/` stays out of the diff; never regenerate the J-05..J-09
goldens (`HOST-GUARD`/`flock` in `start-frontend.sh` are byte-frozen, 21/21 lines verified); J-07's
`[NEW]` walkthrough is not owed (session demo step 9 already carries it).

**Lesson applied (iter-78, both entries):** do not copy a "carried, Nth round owed" note forward
without re-opening the artifact, and do not treat a self-maintained minor-violation count as a
gating criterion — both are exactly why the owner amendment exists; this spec does not ask the
evaluator to clear the 146-entry backlog, only to report it.

## IN SCOPE

### Backend
(none — no code changes this iteration)

### Frontend
(none — no code changes this iteration)

### New user-facing capability
None — this is a re-verification round, not a feature round.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — no product surface changes. The only "delta" is procedural: this round's browser-qa /
closure-gate artifacts are produced under the corrected `closure_gate.py` / `browser-qa-phase.sh`,
so the round is recorded `closed` rather than `blocked` for reasons unrelated to product defects.

### Blueprint conformance
No new surfaces. All 8 journeys keep their existing homes per `state/blueprint.md`'s Information
Architecture (global readiness badge, `/data`, `/backtest`, and the existing nav pages) — unchanged
since the iter-78 entry. No blueprint edit is made this iteration (nothing new to register).

### Data-contract additions
None.

## OUT OF SCOPE

- Any code change to `apps/backend/app` or `apps/frontend` — this round verifies, it does not build.
- Re-litigating the completion-rule reading — settled by the 2026-08-13 owner amendment; the
  evaluator applies it, does not re-derive it.
- Further edits to `scripts/automation/lib/closure_gate.py` or `scripts/automation/browser-qa-phase.sh`
  beyond the two owner-approved, already-applied fixes named above.
- Clearing the 146-entry minor anti-goal ledger backlog — no longer gates GOAL_ACHIEVED per the
  amendment; report it, do not spend a round chasing it to zero.
- The recurring owner questions that remain genuinely open and non-blocking for completion (cost
  sanction acceptance, B-1107 concurrency cap, whether the 2s health-ceiling scope should widen to
  short jobs) — carry these into the closing summary as backlog, do not re-ask mid-round.
- The Regime Lab (`iter-33/g`) — not a Must-have journey; deferred, out of this session's scope.
- Re-running the J-07/J-04 carried drills or regenerating any golden — binding "Do not redo" above.

## DEFINITION OF DONE

- [ ] All 8 target journeys (J-01, J-03, J-04, J-05, J-06, J-07, J-08, J-09) re-verified `passing`
      via deterministic replay + LLM browser-qa this round, each with fresh evidence artifacts.
- [ ] `closure_gate.py` returns a non-`blocked` verdict on this round's `ui-test-results.md` (the
      quoted-span and negated-backend-only false positives from iters 77-78 do not recur).
- [ ] `browser-qa-phase.sh`'s target-journey replay routing executes live (all 8 target rows
      populated in the merged results file, none reading "no test case executed by any lane").
- [ ] Zero unresolved CRITICAL anti-goal violations confirmed for this round.
- [ ] `coherence.md` verdict is not `COHERENCE-FAIL`.
- [ ] The evaluator applies the 2026-08-13 owner completion rule and either declares GOAL_ACHIEVED
      (if all conditions hold) or states precisely which of the three conditions is unmet.
- [ ] No anti-goal violation introduced; no HOST-GUARD/AG-10 script block weakened or removed.

## TESTING REQUIREMENTS

- Browser: J-01, J-03, J-04, J-05, J-06, J-07, J-08, J-09 — full replay + LLM lane, merged into the
  canonical `ui-test-results.md` (not a side file — iter-77's lesson).
- Unit/integration: no new code, so no new test files; existing suite is not expected to change.
- Error cases: none newly introduced this round (verification only).

- TC-1: given J-01's `data_provider_runs` partition from iter-78 (dates_total = non-trading +
  snapshots_created + already-snapshotted) and no `apps/backend/app` diff since, when the replay
  lane re-runs J-01's golden this round, then the row reports PASS and the partition still holds
  against a live `data_provider_runs` query.
- TC-2: given J-03's no-range-cap acceptance and the retired `max_range_days` validation, when a
  multi-year-span backfill request is replayed, then no range-cap rejection occurs and the request
  completes in chunked execution.
- TC-3: given J-04's non-blocking-boot acceptance and its carried steps 3/5/6, when the readiness
  badge and `GET /api/health` boot-phase surface are replayed, then the badge shows a distinguishable
  starting/ready state and `/api/health` returns HTTP 200 with a truthful phase field.
- TC-4: given J-05's ingest-time-aggregate acceptance, when a backfill/rebuild is replayed, then the
  `aggregates_refreshed` field on the resulting `data_provider_runs` row lists the warmed keys and no
  request-time recompute is observed on any page load.
- TC-5: given J-06's committed page-load budgets in `reports/perf-budgets.md`, when the nav-listed
  pages are replayed, then each stays within its committed budget.
- TC-6: given J-07's carried steps 3-4 (VmPeak margin, induced-pressure abort, valid while
  `apps/backend/app/` stays out of the diff), when heavy background compute runs concurrently with
  `GET /api/health` polling this round, then every poll returns HTTP 200 within the owner-set ≤2s
  bounded-window ceiling (≤0.1s steady-state).
- TC-7: given J-08's storage-only backtest acceptance, when `/backtest` is loaded, then evidence
  renders from stored rows only, with no cold recompute triggered on the request path.
- TC-8: given J-09's background-compute disclosure acceptance, when a background compute is
  in-flight during replay, then `GET /api/health`'s `background_compute` field and the UI badge both
  disclose it truthfully and concurrently (not one without the other).
- TC-9: given `closure_gate.py`'s quoted-span and negated-backend-only exclusions are applied, when
  this round's `ui-test-results.md` contains a double-quoted "TODO"/"TBD" tool-message quote or a
  sentence negating a backend-only gap, then `closure_gate.py` does not flag it and the gate result
  is not `blocked`/`closure_failed` for that reason.
- TC-10: given `browser-qa-phase.sh` now assigns `TARGET_JOURNEYS` before calling
  `replay_lane_partition_and_verify`, when the pipeline runs at `evidence` depth, then all 8 target
  rows in the merged `ui-test-results.md` are populated with a real PASS/FAIL, none reading "no test
  case executed by any lane."
- TC-11: given all 8 journeys pass this round, 0 unresolved critical anti-goal violations, and
  `coherence.md` not `COHERENCE-FAIL`, when the evaluator applies the 2026-08-13 owner completion
  rule, then it records a GOAL_ACHIEVED verdict (or names precisely which of the three named
  conditions is unmet, with evidence).

## NOTES

- If this round's fresh replay/LLM pass reproduces all 8 journeys `passing` and the closure gate
  returns non-`blocked`, the evaluator has everything needed to apply the settled rule directly —
  no further iteration should be required to reach a verdict.
- If the evaluator finds any condition unmet (e.g., a fresh critical finding, a coherence FAIL, or
  a journey that does not replay clean this round), the NEXT iteration should target only that
  specific gap — do not fall back to broad re-verification again once a specific defect is named.
- The 146-entry minor ledger backlog, the cost-sanction question, B-1107, and the health-ceiling
  scope question are real and should be reported in the evaluator's closing summary as owner-owned
  backlog — they must not, per the amendment, be read as blocking this round's verdict.
- Per this agent's own rule for "zero remaining FAILING journeys," this iteration does not
  manufacture additional feature or hardening work; if the evaluator declares GOAL_ACHIEVED, no
  further iteration spec should be written by goal-decomposer for this session.
