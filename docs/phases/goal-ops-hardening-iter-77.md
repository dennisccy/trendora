# Goal Iteration 77 — Restore the code lane: fix the frontend race, render `stale_for_s`, fix the badge wrap, strengthen J-07/J-09 goldens

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 77
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict was ESCALATE (mandatory, no exceptions); it is also the only
  deterministic escape from the SPEED-9 evidence backstop (`scripts/automation/run-goal.sh:2509-2539`)
  that silently demotes every `lean` spec to `evidence` while all 8 journeys are `passing` — a
  `CONTINUE` + "full" recommendation is NOT reliably honored by the engine (falls through to the
  legacy allowlist and can be demoted back to lean/evidence).
- **Frontend Present:** yes
- **Target journeys:** J-04, J-07, J-09
- **Required-still-passing journeys:** J-01, J-03, J-05, J-06, J-08
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

Restore this session's code lane (blocked for two rounds by the SPEED-9 evidence backstop) and use it
to root-cause the intermittent asset-less-frontend defect, give the readiness badge/preflight banner
their first new user-visible disclosure (`stale_for_s`, "how stale is what I'm showing you"), fix a
display defect that hides the "Ready" pill at common viewport widths during a compute window, and
strengthen the J-07/J-09 goldens against real, shipped selectors instead of a text token.

## BACKGROUND

The last two rounds (iter-75, iter-76) both ran an empty diff against specs that ordered real code
work: `scripts/automation/run-goal.sh:2509-2539` (SPEED-9) demotes every `lean` spec to `evidence`
whenever all Target journeys are already `passing`, which they now all are. The iter-76 evaluator
verified in the engine source that ESCALATE is the only deterministic escape (`run-goal.sh:2427`/
`:2482` grant a full pass on `prior-verdict-ESCALATE`), chose ESCALATE for exactly that mechanical
effect, and ordered a full round. This spec is that round — depth `full` is not optional here (Full
trigger 3).

Target selection follows the evaluator's own next-step order items (1)-(5), picking the three
journeys whose surfaces those items touch (J-04: readiness badge; J-07: heavy-aggregate availability
badge + backtest scorecard; J-09: background-compute badge chip) and folding in the smaller carried
housekeeping items (goldens-regen-pending, the stray `=` file, TC-7's capture, the walkthrough
recorder) that ride along without being this round's goal, per rule 7. Per the priority rubric: no
journey is regressed (rule 1 n/a), coherence was PASS at iter-76 so no consolidation pass is required
(rule 2 n/a), the frontend-race root-cause is the clearest unblocker (rule 3 — it has voided goldens
in at least 3 prior rounds and threatens every future round's evidence quality), and this iteration
deliberately confines itself to ONE risk class (frontend launcher/badge/testid work) rather than
touching the frozen memory/warm code path (rule 5) — `app.engine.readiness`'s cache/staleness logic
and `compute_forward_aggregates` are explicitly NOT touched, per the binding "Do not redo" list.
Owner-blocked questions (B-1107, the 2s-ceiling scope, `browser-qa-phase.sh`'s sign-off, and the
finish-now-vs-clear-housekeeping-first policy) are excluded per rule 6 — none is re-planned here.

Applied lessons: (iter-73, iter-76-second) sort replay FAILs by capture time and open the frame before
accepting an automatic "transient/environment" explanation — a post-boot backfill can legitimately run
~18 minutes of zero-work before a golden that waits on job completion; (iter-72-second) the same
discipline for "concurrent load" labels; (iter-74) when a measurement keeps failing, change the
trigger, not the thing measured — applied here by pointing the frontend-race fix at the concurrent-
invocation trigger (two `start-frontend.sh` runs racing on the live `.next` dir) rather than at the
symptom (an unstyled shell) directly, since the script's own comments already show it isolates
verification builds via `NEXT_DIST_DIR` and the gap is plausibly the un-isolated live-serving path.

NOTE for the evaluator: iteration-state's "Do not redo" list carries J-07 step 3 (VmPeak/margin) and
step 4 (induced-pressure drill) "valid while the diff stays empty." This round's diff will NOT be
empty. None of this iteration's planned changes touch `compute_forward_aggregates`, the warm/memory
path, or `app.engine.readiness`'s cache logic, so the carry's SUBSTANCE plausibly still holds — but
the stated precondition is now literally false, and it is the evaluator's call whether that requires
fresh step-3/4 evidence or whether the disjoint-files argument is sufficient this round.

## IN SCOPE

### Backend / Launch scripts
- [ ] `scripts/start-frontend.sh`: root-cause the intermittent asset-less-frontend defect (iter-72/c,
      quiet for two rounds but never fixed) — instrument and confirm (or rule out) a race where two
      concurrent invocations of this script both write to / serve the SAME live `.next` directory (one
      process's `next build` still writing while another's `next start` serves), and close it (e.g. a
      lock/guard serializing the build-if-stale → build → start sequence per dist-dir). If
      instrumentation instead names a different cause, fix that instead — either way, name the cause
      explicitly and add a regression test.
- [ ] Clear `runs/goal-session-ops-hardening/state/goldens-regen-pending` of its stale J-05..J-09
      listing (iter-76/c) — all five pass on their current goldens; regeneration was never the fix.
- [ ] Delete the stray zero-byte `=` file at the repo root (iter-74/c, 6th carried round); confirm no
      script or test references it before removing.
- [ ] Capture the TC-7 `/data` honest-fallback live-browser evidence for the
      `TRENDORA_FAULT_INJECT_MEMORY_ERROR=data_overview_endpoint` hook (`apps/backend/app/api/data.py:119`)
      — per the iter-76 assumption-ledger decision, capture the evidence rather than remove the hook.

### Frontend
- [ ] `apps/frontend/app/backtest/page.tsx` (`ScorecardSection`): add
      `data-testid="scorecard-row-<horizon>d"` to each rendered per-horizon scorecard row (e.g.
      `scorecard-row-1d`, `scorecard-row-5d`, …), matching the horizons already in
      `backtest.scorecard.by_horizon`.
- [ ] `apps/frontend/components/health-badge.tsx` (+ `preflight-banner.tsx` / `readiness-provider.tsx`
      / `lib/api.ts` as needed): render the already-served `GET /api/health` `stale_for_s` field as a
      short "as of {N}s ago"-style annotation on the readiness badge and preflight banner, shown only
      when `stale_for_s > 0` (synchronous computes, `stale_for_s == 0`, show no annotation).
- [ ] Fix the badge-row layout (`apps/frontend/app/layout.tsx`'s header + `health-badge.tsx`) so the
      "Ready"/status pill stays visible alongside the "background compute running (N)" chip at a
      1280×800 viewport instead of being pushed out of the visible top bar (iter-76/e).

### Test / harness
- [ ] `runs/goal-session-ops-hardening/journey-scripts/J-07.json` step 4: upgrade from the text-token
      `"1d"` assertion to the new `data-testid="scorecard-row-1d"` selector now that the hook ships;
      re-run this golden and `J-09.json` (already strengthened at iter-76 but never executed) through
      the deterministic replay lane this round.
- [ ] Walkthrough recorder (the pipeline step under `scripts/automation/lib/demo_runner.py` that saves
      before/after frame pairs into `reports/demo/<id>/`): fix it saving byte-identical before/after
      frames (iter-76/d) — the "after" capture must happen once the state-changing action's effect is
      actually visible in the DOM/screenshot, not immediately after the action fires.

### New user-facing capability
Anyone viewing the readiness badge or preflight banner during a background-compute window can now see
how stale the displayed status is (an "as of Ns ago" annotation) instead of only a static "Ready" /
"background compute running" chip; the "Ready" pill no longer disappears at a 1280px viewport while a
compute window is in flight.

### New information displayed
`stale_for_s` (seconds since the served readiness/preflight/background-compute payload was computed)
as a short human-readable annotation on the global readiness badge and the preflight banner.

### New user actions
None — both surfaces remain read-only status displays.

### UI surface changes
Global readiness badge (top bar, every page) and preflight banner gain a staleness annotation and a
layout fix; `/backtest`'s scorecard rows gain a stable `data-testid` (no visible change).

### Product surface delta
The global status surface now discloses cache staleness and never hides the "Ready" state behind a
background-compute chip at common viewport widths.

### Blueprint conformance
All touched surfaces live under blueprint.md's existing Information Architecture homes: the global
readiness badge + preflight banner ("(global) / Data Manager", J-04/J-07/J-09's row) and `/backtest`
("Backtest", J-07/J-08's row). No new page, route, or nav entry. blueprint.md's iter-77 update note
(inserted after the iter-74 entry) and the Backend-readiness Data-Contract row document this
iteration's additive change.

### Data-contract additions
None new. `stale_for_s: float >= 0` is ALREADY registered in blueprint.md's "Backend readiness / boot
phase + preflight verdict" row (added iter-71; computed by `compute_readiness`/`compute_preflight` in
`app.engine.readiness`, served by `GET /api/health`) — this iteration adds its FIRST UI consumer only;
no second computing module, no second endpoint, no field change. The `scorecard-row-<horizon>d` testid
attaches to the ALREADY-registered `scorecard.by_horizon[]` values served by `GET /api/backtest` — a
test hook on an existing displayed value, not a new one.

## OUT OF SCOPE

- iter-33/g, the Regime Lab — deferred a 43rd time; needs owner direction, not re-planned here.
- Any change to `app.engine.readiness`'s cache/staleness/tick logic or to `compute_forward_aggregates`
  — both are frozen ("Do not redo"); this iteration only adds a UI consumer of already-served output.
- Re-running J-07 step 3 (VmPeak/margin) or step 4 (induced-pressure drill) as a fresh drill — carried
  per iteration-state, subject to the evaluator's own call given this round's non-empty diff (see
  BACKGROUND note above).
- Re-running J-08's or J-09's full database-cross-check acceptance drill — already done fresh at iters
  75/76; this round's J-09 browser-qa pass is scoped to confirming the badge/layout change doesn't
  disturb the already-verified background-compute disclosure, not a repeat of the deep drill.
- Owner-blocked items: the 2-second health-ceiling scope (long jobs only vs. all jobs), permission for
  B-1107's concurrency cap, sign-off to edit `scripts/automation/browser-qa-phase.sh`, and the
  finish-now-vs-clear-housekeeping-first policy question — all pending an explicit owner answer.
- Regenerating any golden script content beyond the two named selector upgrades (J-07 step 4) — golden
  regeneration is never the right remedy for a harness/environment defect (iter-73 lesson).
- The remaining ~60-item "CARRIED, untouched" backlog (iter-29/b onward, per iteration-state) — none
  is a regression or an unblocker for J-04/J-07/J-09; bundling it in would make a joint failure
  undiagnosable (rule 5).

## DEFINITION OF DONE

- [ ] J-04, J-07, J-09 pass via browser-qa-agent with fresh (non-carried) evidence for the surfaces
      this iteration changed (badge annotation, badge layout, scorecard testid)
- [ ] Required-still-passing journeys J-01, J-03, J-05, J-06, J-08 remain green (deterministic replay
      + LLM fallback)
- [ ] No anti-goal violation introduced (AG-3: the badge's displayed `stale_for_s` annotation matches
      the raw `GET /api/health` payload for the same poll; AG-10: `start-frontend.sh`'s HOST-GUARD
      block is untouched and still enforced)
- [ ] Unit tests pass; no regressions
- [ ] The intermittent asset-less-frontend defect (iter-72/c) is closed with a named cause and a
      regression test, or definitively ruled out with instrumentation evidence and a fresh named
      hypothesis for the next round
- [ ] `state/goldens-regen-pending` is cleared
- [ ] The stray zero-byte `=` file is removed
- [ ] TC-7's `/data` honest-fallback evidence is captured and filed
- [ ] J-07 step 4 and J-09 step 3 execute successfully via deterministic replay this round using their
      strengthened, real shipped selectors (not lint-checked only)
- [ ] The walkthrough recorder no longer saves byte-identical before/after frame pairs
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-77-dev.md`

## TESTING REQUIREMENTS

- Browser: J-04, J-07, J-09 (targets, fresh evidence); J-01, J-03, J-05, J-06, J-08 (required-still-
  passing, full regression set per the ESCALATE-triggered widening rule)
- Unit/integration: a `start-frontend.sh` regression test for the concurrent-invocation race (or the
  actually-named cause); a frontend component/unit test for the `stale_for_s` badge annotation and the
  1280px layout fix; a `demo_runner.py` unit test asserting before/after frames differ when the
  underlying state differs
- Error cases: `GET /api/health` unreachable → badge shows no staleness annotation (never a stale or
  fabricated number); the `data_overview_endpoint` fault-injection hook armed → `/data` shows the
  honest fallback copy, never fabricated coverage numbers

Test-first contract — TC- scenarios (seed for the functional test plan; full mode may still generate
its own, these are the binding minimum):

- TC-1: given the backend and frontend are freshly launched via `scripts/start-frontend.sh` with no
  concurrent invocation, when the harness requests `/` as soon as the port is listening, then the
  response is a fully styled page (CSS/asset requests return 200; no bare "Checking backend…" shell),
  repeated across 5 consecutive fresh launches with zero asset-less occurrences.
- TC-2: given two invocations of `scripts/start-frontend.sh` are started concurrently against the same
  `.next` dist directory, when the first invocation's `next build` is still in progress, then the
  second invocation does not serve (and the first does not serve) a partial/mid-build `.next` payload
  — verified by a regression test that simulates or directly exercises the race and asserts the served
  page is always fully built.
- TC-3: given a live backend with a background-compute window in flight, when `GET /api/health` is
  polled, then the JSON response's `stale_for_s: float >= 0` field is reflected on the readiness
  badge/preflight banner as a human-readable "as of {N}s ago" annotation whenever `stale_for_s > 0`,
  and no such annotation renders when `stale_for_s == 0`.
- TC-4: given the badge displays a staleness annotation per TC-3, when the rendered value is compared
  against the raw `GET /api/health` JSON for the same poll, then the two match exactly (AG-3).
- TC-5: given a 1280×800 browser viewport and a background-compute window in flight (the "background
  compute running (N)" chip is shown), when the readiness badge renders, then the "Ready"/status pill
  remains visible within the top bar alongside the compute chip — verified by a screenshot showing
  both elements on-screen.
- TC-6: given the `/backtest` page renders a populated forward-test scorecard, when the DOM is
  inspected, then each per-horizon row carries `data-testid="scorecard-row-<horizon>d"` matching the
  configured horizons (e.g. `scorecard-row-1d`, `scorecard-row-5d`).
- TC-7: given J-07.json's golden step 4 and J-09.json's golden step 3, when the deterministic replay
  lane executes them against this iteration's build, then both PASS using the new
  `scorecard-row-<horizon>d` selector (J-07) and the existing real sub-state testid (J-09), and the
  replay run's timestamp postdates this iteration's frontend deploy (exercising the new hook, not
  stale scripts).
- TC-8: given `TRENDORA_FAULT_INJECT_MEMORY_ERROR=data_overview_endpoint` is armed against a live
  backend, when `/data` is loaded, then the endpoint raises before other work, the page renders the
  honest-fallback copy ("Dataset coverage could not load from the API. No figures are shown rather
  than fabricated"), and a screenshot of that state is captured and filed.
- TC-9: given the walkthrough recorder captures a before/after frame pair for a journey whose state
  genuinely changes between captures (e.g. a J-05 backfill before/after), when the two frames are
  compared byte-for-byte, then they are NOT identical.
- TC-10: given `state/goldens-regen-pending` currently lists J-05..J-09, when this iteration completes
  with all eight journeys passing on their current or newly strengthened goldens, then the file is
  cleared of that stale listing.
- TC-11: given the repo root previously contained a stray zero-byte file named `=`, when this
  iteration's diff is inspected, then that file no longer exists and no test or script references it.
- TC-12: given J-01, J-03, J-05, J-06, J-08 each have a stored golden script, when the deterministic
  replay lane runs this iteration, then all five continue to PASS with no regression; any replay FAIL
  is corroborated by an LLM re-check citing an opened frame and a timestamp bracket before any
  "transient load" or "selector drift" label is accepted (iter-73/iter-76 lessons).

## NOTES

- This spec exists specifically to exercise the engine's `prior-verdict-ESCALATE` full-depth grant
  (`run-goal.sh:2427`/`:2482`) — if the code lane still produces nothing this round, the diagnosis in
  iter-76's log is wrong and the next evaluator should escalate to the owner for a config-level fix
  (`CHAIN_EVIDENCE_MICRO_PATH=false` or similar) rather than writing a third empty-diff spec.
- Do not read a clean replay/browser round as proof the frontend race is fixed unless this round's own
  regression test (TC-2) demonstrates the mechanism — "quiet for N rounds" is not evidence of a fix
  (iter-75 lesson, applied here to the SAME class of intermittent defect).
- Owner questions carried verbatim from iter-76 remain open and unaddressed by this spec: (a) finish
  the loop once all journeys pass and no serious problem is open, or spend 2-3 rounds clearing the 138
  housekeeping notes first; (b) 2-second health-answer ceiling during long jobs only, or all jobs;
  (c) permission for B-1107's concurrency cap; (d) sign-off to fix the ordering bug in
  `scripts/automation/browser-qa-phase.sh`; (e) this session is materially over its time budget
  (16 consecutive over-budget rounds) — a cost decision is still owed.
- Assumption-ledger entry logged for this iteration's interpretation call on the frontend-race
  root-cause direction (see `runs/goal-session-ops-hardening/state/assumptions.md`, iter-77 entry).
