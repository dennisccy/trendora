# Goal Iteration 78 — close iter-77's CLOSURE-FAIL, defend the launcher, tick the badge live

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 78
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior evaluator verdict was ESCALATE (mandatory full; also matches this
  iteration's own binding depth recommendation)
- **Frontend Present:** yes
- **Target journeys:** J-04, J-07, J-09
- **Required-still-passing journeys:** J-01, J-03, J-05, J-06, J-08 (full regression widen — prior
  verdict was ESCALATE)
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
    envelope — re-set by the dated "Additional binding notes" entry in `docs/goal.md` — while this
    paragraph's prohibition on agents removing, weakening, or bypassing caps is unchanged.)*
    *(critical)*

## GOAL

Close iter-77's CLOSURE-FAIL by re-verifying J-04/J-07/J-09 into this iteration's own canonical
evidence file, permanently defend the frontend launcher against the test-residue failure mode that
made the app unstartable this round (iter-77/c), make the readiness badge/preflight banner's "as of
Ns ago" staleness annotation tick live between polls instead of freezing (iter-77/d), and recapture
J-09's background-compute walkthrough frame so it actually shows compute in flight (iter-77/e).

## BACKGROUND

Prior verdict was ESCALATE, which is a mandatory full-depth trigger (rule 3, no exceptions) and
matches this iteration's own binding depth recommendation — no escape condition needed to be found,
only avoided contradicting. All 8 Must-have journeys are currently `passing`, so per rule 1/3 there
is no regression to chase and no unblocker journey to pick between; the priority instead falls on
the concrete, agent-owned items iter-77's evaluator itself flagged as blocking the round from
closing cleanly. Per rule 6, this spec deliberately excludes every item the evaluator or
iteration-state marked owner-blocked/awaiting-permission: `closure_gate.py:72`'s backend-only regex
false positive, `scripts/automation/browser-qa-phase.sh`'s carried ordering bug, B-1107 (limiting
concurrent heavy computes), the 2-second health-ceiling scope question, and the
finish-now-vs-clear-140-notes question — all restated in NOTES below, none coded here.

Three agent-owned items remain, all landing on the SAME journey cluster (J-04/J-07/J-09's shared
global-badge + boot-availability surface), so this is one coherent consolidation pass, not two
bundled risky changes (rule 5): (1) iter-77/c — a test-residue file
(`apps/frontend/__tc3_intentionally_broken.ts`) left in the LIVE frontend tree by an interrupted
test run made `next build` fail and the launcher exit 1, i.e. no frontend at all; this happened
inside iter-77 and per its own evaluator was "fixed inside the round; NOT defended against
recurrence." Applying the iter-77 lesson verbatim ("Sabotage-style fixtures must write outside the
served tree, or the launcher must be taught to ignore their filenames") — see NOTES for why this
iteration picks a stronger reading of the second option. (2) iter-77/d — `stale_for_s` (registered
`GET /api/health` field, first rendered by iter-77) only updates on poll landing, so the annotation
can read "as of <1s ago" for up to the full poll-idle interval before the next poll refreshes it;
this is the first user-visible product change this iteration ships. (3) iter-77/e — J-09's own
"background compute in flight" walkthrough frame shows an idle Ready state with no compute chip,
misrepresenting the journey it exists to demonstrate.

Also applying the iter-77 lesson on fix-mode passes: if any lane in this round needs a re-run
mid-iteration (e.g. a reviewer-triggered QA retry), it MUST write its results back into THIS
iteration's canonical `goal-ops-hardening-iter-78-ui-test-results.md`, never a side file — the exact
mistake that left iter-77 recorded `blocked` despite passing evidence existing on disk.

This iteration touches only `scripts/start-frontend.sh` (frontend launch script),
`apps/frontend/components/readiness-provider.tsx` / a new pure helper, and a walkthrough-capture
script/fixture — it does NOT touch `app.engine.readiness`'s cache/staleness/tick logic or
`compute_forward_aggregates` (binding "Do not redo"), so J-07's carried steps 3-4 (VmPeak margin,
induced-pressure abort, from the 2026-07-31/iter-74 drill) remain valid per the same reasoning the
iter-77 evaluator already applied (A.6 tests whether the JOURNEY's backend runtime surfaces
changed — none did). The J-08/J-09 deep database cross-check drills (run fresh at iters 75-76) are
likewise not repeated. No golden is regenerated (binding "Never regenerate the J-05..J-09
goldens").

## IN SCOPE

### Backend

- [ ] `scripts/start-frontend.sh`: before the existing staleness-check/build-if-stale step, actively
  purge the two known test-residue artifacts `test_start_frontend_script.py`'s own self-heal already
  reserves — the exact filename `apps/frontend/__tc3_intentionally_broken.ts` and the
  `apps/frontend/.next-test-*` scratch-dir glob — if present, logging what was purged, so a leftover
  sabotage file from an interrupted test run can never make the live launcher's real `next build`
  fail again, independent of whether/when `test_start_frontend_script.py` itself is next invoked.
  The existing HOST-GUARD block and build-lock (`flock`) stay byte-unchanged (binding "Do not
  redo").
- [ ] Add a regression test (extend `apps/backend/tests/test_start_frontend_script.py` or add a
  sibling script-level test) that creates the residue file directly — bypassing the module's own
  autouse setup-purge, to simulate "a different process wrote it and this module is not the next
  thing invoked" — then runs the REAL `scripts/start-frontend.sh` directly and asserts a clean build
  (rc 0) and a live-serving `next start` process. This proves the LAUNCHER's own defense, not merely
  the test module's pre-existing self-heal.
- [ ] Fix J-09's "background compute in flight" walkthrough-capture step (currently captures an
  idle "Ready"-only frame with no compute chip, per iter-77/e) so it triggers a genuine in-flight
  background compute — e.g. requesting an as-of date whose evidence needs on-demand dispatch — and
  waits for the compute to actually be running before capturing. Locate this session's per-iteration
  walkthrough-gallery capture mechanism (distinct from `reports/goal-session-ops-hardening-demo.json`'s
  narrated demo steps, which already capture this scene correctly per iter-25). Timing/trigger fix
  only — no change to `get_background_compute_status()` or any Data Contract value.

### Frontend

- [ ] `apps/frontend/components/readiness-provider.tsx`: on each successful `GET /api/health` poll,
  record the server's `stale_for_s` alongside the client wall-clock time it was received at. Add a
  local 1-second interval that re-derives a LIVE staleness value (`base stale_for_s` + elapsed
  client seconds since receipt) between polls, so the readiness badge's and preflight banner's
  "as of Ns ago" annotation increases smoothly instead of freezing at the last-polled number for up
  to the full poll-idle interval.
- [ ] Extract the tick derivation into a small pure, unit-testable function (new export, e.g.
  alongside `lib/staleness-annotation.ts`) so the math is covered by this project's existing
  plain-`node` test convention without a browser harness. `formatStaleAnnotation`'s existing
  null/0/negative/non-finite guards stay the single formatting authority — the derived live value is
  fed through that SAME function, never a second formatter.

### New user-facing capability

None new this iteration — refines the existing "as of Ns ago" staleness annotation (added iter-77)
to update continuously instead of appearing frozen between polls, and removes a known way the whole
frontend could fail to start.

### New information displayed

None. No new field, no new payload key.

### New user actions

None.

### UI surface changes

The global readiness badge and preflight banner (present on every page) now tick their staleness
text every second instead of only refreshing it on poll landing. No new page, panel, or card.

### Product surface delta

The badge/banner's honesty about payload age becomes continuously accurate rather than periodically
looking stale/frozen; the frontend launcher becomes resilient to a known test-residue recurrence
that this round proved can take the whole app down; J-09's own walkthrough evidence becomes
representative of the behavior it is meant to demonstrate; and this round's own browser-qa evidence
for J-04/J-07/J-09 lands in the canonical artifact of record instead of risking a repeat of iter-77's
unmerged side-file mistake.

### Blueprint conformance

All changes render on already-registered homes in `blueprint.md`'s Information Architecture: the
global readiness badge / preflight banner (J-04/J-07/J-09's existing home) and `/data`'s
background-compute walkthrough context (J-09's existing home). No new page, route, or nav entry.

### Data-contract additions

None. The client-side tick is a purely local re-derivation of the ALREADY-registered `stale_for_s`
field (`blueprint.md`'s "Backend readiness / boot phase + preflight verdict" row) — same computing
modules (`compute_readiness` / `compute_preflight`), same endpoint (`GET /api/health`), no new
field, no second producer, no second endpoint. The launcher residue-purge and the walkthrough-capture
timing fix touch no served/displayed value at all.

## OUT OF SCOPE

- `scripts/automation/lib/closure_gate.py`'s backend-only regex false positive — owner sign-off
  explicitly requested by the last three evaluators and still pending (iteration-state "Human-owned,
  unanswered"); not touched this round (rule 6).
- `scripts/automation/browser-qa-phase.sh`'s carried one-line ordering bug — same
  owner-permission-pending status; not touched.
- B-1107 (limiting how many heavy computes run concurrently), the 2-second health-ceiling scope
  question (long jobs only vs. all jobs), and the finish-now-vs-clear-140-minor-notes question —
  owner decisions restated in NOTES, not decided or coded here.
- J-05's and J-07's own `[NEW]` walkthrough captures (owed 19+ rounds) and J-06's page-timings entry
  into `reports/perf-budgets.md` (owed 8 rounds) and J-01's zero-work-outcome-panel photograph —
  stay carried; excluded to keep this iteration's diff small (rule 4) since real code work already
  fills it.
- The Regime Lab feature backlog (iter-33/g, deferred 44+ times) — stays deferred; outside this
  session's Key Capabilities.
- Any change to `app.engine.readiness`'s cache/staleness/tick SERVER logic or
  `compute_forward_aggregates` — binding "Do not redo"; this iteration's staleness fix is
  client-side only.
- Any change to the `journey-scripts/J-*.json` goldens — binding "Never regenerate the J-05..J-09
  goldens."
- Re-running J-07 steps 3-4's memory drill or the J-08/J-09 deep database cross-check — both valid
  carries per this iteration's diff staying out of their backend runtime files (see BACKGROUND).

## DEFINITION OF DONE

- [ ] J-04 passes via browser-qa-agent, with fresh evidence merged into THIS iteration's canonical
  `goal-ops-hardening-iter-78-ui-test-results.md` (not a side file).
- [ ] J-07 passes via browser-qa-agent, same canonical-file requirement.
- [ ] J-09 passes via browser-qa-agent, same canonical-file requirement, AND its "background compute
  in flight" walkthrough frame shows the background-compute chip (not an idle Ready-only frame).
- [ ] Required-still-passing journeys J-01, J-03, J-05, J-06, J-08 remain green (deterministic
  replay + LLM fallback).
- [ ] `scripts/start-frontend.sh` builds and serves successfully even when the reserved
  test-residue filename/scratch-dir is present in `apps/frontend` (new regression test passes).
- [ ] The readiness badge/preflight banner's staleness annotation visibly increases between polls
  (client-side tick), verified by a unit test and one direct browser observation.
- [ ] This iteration's own closure verdict is not `blocked`/`closure_failed` for any reason this
  iteration controls (i.e., not a missing/unmerged browser-qa result for J-04/J-07/J-09).
- [ ] No anti-goal violation introduced; `scripts/start-frontend.sh`'s HOST-GUARD block and build
  lock stay byte-unchanged (AG-10).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-78-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-04, J-07, J-09 (named targets); full regression replay of J-01, J-03, J-05, J-06, J-08
  (post-ESCALATE full-widen).
- Unit/integration: `apps/backend/tests/test_start_frontend_script.py`'s new residue-defense test;
  a new plain-`node` unit test for the staleness-tick pure function (mirrors
  `lib/staleness-annotation.test.ts`'s existing convention).
- Error cases: residue present AND the purge step itself fails (e.g. permission error) → the
  launcher must fail LOUD with a clear log line, never silently serve a broken/stale build;
  `stale_for_s` is `null` (failed poll) → the tick must render nothing, never a fabricated growing
  number.

Test-first contract:

- TC-1: given `apps/frontend/__tc3_intentionally_broken.ts` exists in the live tree (simulating
  leftover test residue) and no other change, when `scripts/start-frontend.sh` is invoked directly,
  then it purges the file, `next build` exits 0, and `next start` binds `$FRONTEND_PORT` and serves
  HTTP 200 on `/`.
- TC-2: given a normal `apps/frontend` tree with no residue files, when `scripts/start-frontend.sh`
  runs, then its build/skip-rebuild decision is byte-identical to pre-iteration behavior (the purge
  step deletes nothing).
- TC-3: given the readiness badge has just rendered "as of 5s ago" from a landed poll, when 10 more
  seconds elapse with no new poll response, then the badge's displayed annotation reads
  approximately "as of 15s ago" (ticking every 1s), not frozen at "as of 5s ago".
- TC-4: given `stale_for_s` is `0` (fresh synchronous compute) or the last poll failed
  (`staleForS === null`), when the 1-second tick timer fires, then no staleness annotation renders
  (unchanged null-rendering contract from `formatStaleAnnotation`).
- TC-5: given a browser session where a `/backtest` request targets a historical as-of date whose
  evidence requires on-demand dispatch, when the J-09 walkthrough capture runs its "background
  compute in flight" step, then the captured frame shows "background compute running (N)" alongside
  the "Ready" pill — not an idle Ready-only frame.
- TC-6: given this iteration's fresh full regression pass, when J-04/J-07/J-09 are re-verified, then
  the results land in `goal-ops-hardening-iter-78-ui-test-results.md` (the canonical artifact of
  record) with a PASS row for each — not solely in a `devfix-replay`/side-file location.
- TC-7: given J-01, J-03, J-05, J-06, J-08 already pass, when this iteration's post-ESCALATE full
  regression runs, then all five remain PASS via deterministic replay or LLM fallback with no
  `pending_infra`.
- TC-8: given `scripts/start-frontend.sh`'s HOST-GUARD block and build-lock (`flock`), when this
  iteration's diff is reviewed, then both are byte-identical to their pre-iteration form (no
  weakening, per AG-10).

## NOTES

- **Lessons applied:** iter-77's lesson on `test_start_frontend_script.py`'s live-tree residue
  ("Sabotage-style fixtures must write outside the served tree, or the launcher must be taught to
  ignore their filenames") directly motivates the Backend scope above — see the assumption-ledger
  entry below for why this iteration picks active purge over a literal "ignore for staleness"
  reading. iter-77's second lesson (a fix pass must write its re-run results back into the artifact
  of record, never a side file) is restated as a binding instruction in BACKGROUND for any mid-round
  QA retry.
- **Owner questions still open, not decided here (see iteration-state.md "Human-owned, unanswered"):**
  disable the evidence shortcut (`CHAIN_EVIDENCE_MICRO_PATH=false`) or accept an ESCALATE every
  round; the cost sanction (this session has run over its time budget for 17 consecutive rounds);
  finish-now-with-138-housekeeping-notes-as-a-to-do-list vs. spend 2-3 more rounds clearing them;
  the 2-second health-ceiling scope (long jobs only vs. all jobs); B-1107; permission to fix
  `scripts/automation/browser-qa-phase.sh`'s ordering bug; permission to fix
  `closure_gate.py:72`'s regex.
- **Carried, untouched this round:** the full carried list from iter-77's log (iter-29/b through
  iter-76/f) stays carried unchanged; not re-listed here per the anti-restatement rule — see
  `iter-77/eval.md` and iteration-state.md for the authoritative list.
- An assumption-ledger entry is appended to `runs/goal-session-ops-hardening/state/assumptions.md`
  explaining why this iteration reads iter-77/c's second remedy ("teach the launcher's staleness
  check to ignore `__tc3_*`") as requiring active purge rather than a mere staleness-comparison
  exemption — a literal "ignore" would not prevent `next build`'s whole-tree TypeScript check from
  still failing on the stray file.
