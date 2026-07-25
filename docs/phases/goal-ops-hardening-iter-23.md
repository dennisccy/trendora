# Goal Iteration 23 — Close the GOAL_ACHIEVED confirm-reject gaps (session demo evidence + J-06 golden-script fix, zero code changes)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 23
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-06, J-07, J-08
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

Close the three gaps the iter-22 second-key CONFIRM evaluator cited against a `GOAL_ACHIEVED` verdict —
author the missing `[NEW]`-flagged J-06/J-07/J-08 walkthrough steps in the session-wide demo manifest
(`reports/goal-session-ops-hardening-demo.json`) that `demo.sh ops-hardening --session-live` reads, and
restore a disclosed, budget-justified regression-net tolerance to J-06's golden replay script — with zero
product-code changes.

## BACKGROUND

**What happened.** Iteration 22's first evaluator scored `GOAL_ACHIEVED` (all 7 journeys `passing`) and the
deterministic gates passed, but the second-key fresh-context CONFIRM evaluator REJECTED it
(`runs/goal-session-ops-hardening/iter-22/eval-confirm.md`). Three findings: **(1)** J-06 (`docs/goal.md:263`),
J-07 (`:293`), and J-08 (`:327-329`) each carry a "Walkthrough" acceptance bullet requiring `[NEW]`-flagged
steps "viewable via `demo.sh ops-hardening --session-live`" — that command reads
`reports/goal-session-ops-hardening-demo.json`, which independently confirmed carries 7 steps covering only
J-01/J-03/J-04/J-05, zero steps for J-06/J-07/J-08, and `"new": false` on every entry; the prior evaluator's
waiver cited a *different*, per-iteration record-mode artifact `--session-live` never reads. **(2)**
`runs/goal-session-ops-hardening/journey-scripts/J-06.json` was silently edited at 08:41 on iter-22's own
dispatch day: `default_timeout_ms` 8000→18000 (2.25× the amended 8.0 s `/backtest` BCW ceiling) alongside two
assertion-value changes, disclosed nowhere. **(3)** A self-contradicting `reports/perf-budgets.md` TC-4 row —
**already fixed by the operator before this iteration** (independently verified at `perf-budgets.md:3714`,
which now states both the retired-bound FAIL and the current-bound PASS explicitly) — not re-touched here per
the coordinator's instruction. All 7 journeys remain `passing` in `journey-history.json`; this is a closeout
pass, not new product capability, and it does not itself declare `GOAL_ACHIEVED`.

**Why J-08 is a target too, not just the two journeys that flipped this iteration.** The coordinator's
shorthand headline names "both newly-passing journeys" (J-06, J-07), but `eval-confirm.md`'s own body text
says the manifest has "zero J-06, zero J-07, **zero J-08** steps" and scores the walkthrough bullet "unmet for
**3 of 7** journeys." A direct read of `docs/goal.md:327-329` confirms J-08 carries the identical
`[NEW]`-flagged-steps-via-`--session-live` clause, unmet since J-08 first passed (iter-16/21) — the manifest
has never had a single J-08 step. Fixing J-06/J-07 alone would leave an identical, immediately-rediscoverable
gap for J-08 on the very next confirm attempt; the fix is mechanically identical and equally low-risk for all
three, so this iteration closes all three together.

**Target-selection rubric applied.** Rule 1 (regressed first): N/A — no `passing→failing` transitions.
Rule 2 (consolidation before features): iter-22's `coherence.md` was `COHERENCE-PASS` (no mandate from that
gate), but the CONFIRM reject is functionally the same signal — this iteration consolidates/closes cited
gaps, adds no new scope, exactly as Rule 2 intends. Rule 3 (unblockers): J-06/J-07/J-08 are the only journeys
with an outstanding, named, agent-tractable gap; closing all three directly unblocks the next `GOAL_ACHIEVED`
attempt. Rule 4 (smallest spec wins ties): no tie — this is the minimal honest unit of work (one shared
artifact edit + one script fix). Rule 5 (never bundle two risky journeys): does not apply — zero application
code ships, so there is no blast radius to separate; all three journeys' fixes are equally low-risk artifact
edits. Rule 6 (don't pick a human-blocked journey): none of the three residuals are human-owned — both are
agent-tractable per `eval-confirm.md`'s own "Authoring the missing steps is agent-tractable" and the timeout
fix requires only a log/DB read, not an owner decision. **Deviation from the "zero remaining FAILING
journeys → one-line spec" default is deliberate and stated here:** `journey-history.json` shows 0
FAILING/PARTIAL journeys, which would normally trigger that one-liner — but a specific, named, evidenced
CONFIRM rejection supersedes that stale snapshot; writing the one-liner and letting the evaluator re-attempt
`GOAL_ACHIEVED` unchanged would just reproduce the same REJECT next iteration.

**Depth: lean — no full trigger holds.** (1) Structural/cross-cutting: N/A — the entire diff is two
non-application artifacts (`reports/goal-session-ops-hardening-demo.json`,
`runs/goal-session-ops-hardening/journey-scripts/J-06.json`) plus one additive `blueprint.md` paragraph
(already applied by this decomposer); zero backend/frontend modules touched. (2) Data model: N/A — no
Data-Contract value's computing module or serving endpoint changes; a demo manifest and a replay script's
timeout/assertions are pipeline/test artifacts, not served/displayed values (iter-18 "a log line is not a
served/displayed value" precedent). (3) Prior ESCALATE: the effective prior verdict for planning purposes is
`CONTINUE` (per the dispatch header), not `ESCALATE` — the mandatory-full trigger does not fire. (4) Hardening
cadence: 2 consecutive lean iterations dispatched (iter-21, iter-22); dispatching this one lean makes 3, still
below the cadence-4 backstop.

**Lessons applied.** **iter-16** ("status-disclosure copy is a testable assertion about system state, not
styling ... verify each sentence against the code that would have to be true for it"): every narration/
point-out sentence the developer writes into the new demo steps must be checked against a real, current
figure — never asserted from memory or copied from a possibly-stale source. **iter-22** ("a measured 'window
duration' reported by a polling lane can be the POLLER's elapsed time, not the window's ... re-derive from
source-of-truth timestamps"): the new J-07 demo step must cite the developer's own DB-cross-checked
`bcw-measure.csv` figures recorded in `reports/perf-budgets.md`'s "Iteration 22" section (window ≈68.79 s,
`/backtest` max 7.1191 s, `/api/health` max 0.2530 s, VmPeak margin 58.2 %) — **not** the browser-qa
`UT-J-07` row's own "28.06 s window" phrasing, which `eval.md`'s finding 2 already established is the
poller's elapsed time, not the true window. **iter-21** (`/backtest`'s `RefreshingEvidenceBanner` renders
below the fold — any capture must be full-page/element-scoped): the new J-08 demo steps must reuse iter-22's
three already-full-page screenshots (`J-08-baseline-latest-ready.png`, `J-08-refreshing-2026-07-20.png`,
`J-08-ready-after-warm-2026-07-20.png`), not re-capture with a viewport-only shot. **iter-17**
("is the cost proven, or merely unmeasured?"): the J-06 timeout investigation must be a real diagnosis (log +
DB timestamps), not a guess — if no BCW overlap is substantiated, the honest outcome is reverting to 8000 ms,
not inventing a plausible-sounding number.

## IN SCOPE

### Backend

- [ ] No product/backend source changes under `apps/backend/` or `apps/frontend/`.
- [ ] Extend `reports/goal-session-ops-hardening-demo.json` additively (do not modify the existing 7 steps'
  field values or `n` numbers) with `[NEW]`-flagged (`"new": true`, `"verified": true`) steps for J-06, J-07,
  and J-08. Source content from each journey's PASS `UT-J-06`/`UT-J-07`/`UT-J-08` row in
  `reports/phase-goal-ops-hardening-iter-22-ui-test-results.md` (their shared `last_passing_iter`) and the
  reconciled figures in `reports/perf-budgets.md`'s "Iteration 22" section. J-08's steps narrate the
  version-bump → refreshing (older, labeled, complete version served) → fresh-serve-after-warm sequence,
  reusing the three iter-22 full-page screenshots named above. J-07's step cites the developer's own
  `bcw-measure.csv`-derived figures (never the "28.06 s window" phrasing — see lessons above). J-06's step(s)
  narrate the budgets-table-vs-live-page-loads comparison from `reports/perf-budgets.md`'s "Page performance
  budgets" evidence.
- [ ] Follow the demo-narrator schema exactly (`.claude/agents/demo-narrator.md`): every new step has `n`
  (continuing sequentially from 8), `title`, `narration`, `point_out`, `journey`, `new`, `verified`,
  `section`, `action` (+ `expect` on `goto`-type steps). Keep total `"section": "highlights"` steps across the
  WHOLE file ≤ 8 (currently 6) — budget at most 2 more as `highlights`; route any remainder to `"full_tour"`.
- [ ] Investigate `runs/goal-session-ops-hardening/journey-scripts/J-06.json`'s undisclosed 2026-07-25 08:41
  edit. Re-derive, using the iter-21/22 technique (`logs/backend.log` timestamps cross-referenced with
  `forward_aggregate_cache` commit rows), whether J-06's own replay sequence can legitimately coincide with an
  active background-compute window triggered by a sibling journey's replay in the same regression pass (e.g.
  J-05's single-day backfill dispatch reaching J-06's own `/backtest` step).
- [ ] Set `default_timeout_ms` to a disclosed, bounded outcome of that investigation: **≤ 9500 ms** (a
  documented ≤1.5 s margin over the amended 8.0 s `/backtest` BCW ceiling), cited with the specific
  timestamps, IF a genuine BCW overlap is substantiated; otherwise **revert to 8000 ms** (J-06's own
  pre-iter-22 value, matching J-04's/J-08's visit-only convention). 18000 ms is not a legal outcome of this
  task without a cited basis that survives review.
- [ ] Re-verify the two changed assertion values against the live running app before keeping either: the
  displayed price on `/stocks/AAPL` (`$304.89`) and the displayed heading on `/research/event-study` step 11
  (`"Setup & Pattern event study"`). Record the current true value and how it was read (API/DOM) in the dev
  handoff for each.
- [ ] Re-run the corrected `J-06.json` through the deterministic replay harness end-to-end; record pass/fail
  and per-step elapsed time in the dev handoff.
- [ ] Confirm via `git status`/`git diff` at completion that zero files under `apps/backend/` or
  `apps/frontend/` changed.

### Frontend

- [ ] No frontend source changes.

### New user-facing capability

None. The underlying product behavior of all 7 journeys is unchanged; only the evidentiary/demo artifact
backing three already-shipped journeys' acceptance criteria becomes complete.

### New information displayed

None. `reports/goal-session-ops-hardening-demo.json` and `runs/goal-session-ops-hardening/journey-scripts/
J-06.json` are pipeline/QA artifacts, not served or displayed product values.

### New user actions

None.

### UI surface changes

None — no page, component, or route changes. Browser-qa exercises only existing, unchanged pages to
re-confirm the regression set and the corrected J-06 replay.

### Product surface delta

None — an evidence-completeness closeout. The product surface is unchanged; only the completeness and
accuracy of J-06/J-07/J-08's session-demo evidence, and the integrity of J-06's own regression-net script,
change.

### Blueprint conformance

No new surfaces. J-06/J-07/J-08 keep their existing cross-cutting homes already registered in
`blueprint.md`'s Information Architecture / Feature-journey-homes table. `blueprint.md` has already been
updated by this decomposer: one additive "iter-23 update" paragraph appended to the comment block
(documentation only — no Information Architecture or Data Contract table row changed). No nav-skeleton
change — `blueprint.reapproval-requested` was NOT written.

### Data-contract additions

None. A session demo manifest and a deterministic-replay journey-script's timeout/assertions are pipeline/
test artifacts, not served/displayed product values (matches the iter-18 "a log line is not a served/
displayed value" precedent) — no second computing module or serving endpoint is introduced for anything
already in the Data Contract.

## OUT OF SCOPE

- Any product code change under `apps/backend/` or `apps/frontend/`.
- Editing `reports/perf-budgets.md`'s TC-4 / "Revision 1" wording — **already fixed by the operator** before
  this iteration (independently verified, `perf-budgets.md:3714`); do not re-touch.
- Re-running TC-13 (concurrent-ingest overlay) or TC-14 (disruptive J-04 kill/restart) — DONE and PASS, dated
  2026-07-25 (binding, "Do not redo").
- Triggering or recording an actual, human-interactive `demo.sh ops-hardening --session-live` playback
  session — that remains an operator action. This iteration's DoD is the completeness and accuracy of the
  JSON artifact that playback reads, not a witnessed live run (see NOTES; logged, `assumptions.md` iter-23).
- Any new Must-have journey or `docs/goal.md` edit.
- Promoting backlog card B-1107 (owner-owned, optional, non-blocking).
- Any live backfill/ingest job. Re-verifying the two J-06 assertion values and sourcing the new demo steps
  should need only reads (API/DOM/DB) against the already-running app — no new job submission is anticipated.
- `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched`, J-08's serving split/empty state — untouched (binding,
  "Do not redo").
- Retargeting `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches or removing the
  `backtest.py:75` / `mcp/tools.py:38` dangling imports — flagged for a future, properly-scoped pass
  (unchanged carry-over, not this iteration's scope).
- `main.py`'s boot sequence, `app/api/health.py`, `app/engine/readiness.py`, `app/engine/warmup.py`,
  `scripts/*` — untouched.
- Declaring `GOAL_ACHIEVED`. This spec does not score any journey or declare the goal achieved — that is the
  evaluator's and the engine's deterministic-gate/two-key-confirm decision.

## DEFINITION OF DONE

- [ ] `reports/goal-session-ops-hardening-demo.json` contains ≥1 `"new": true` / `"verified": true` step for
  each of J-06, J-07, J-08, additive-only — the existing 7 steps are byte-unchanged (TC-1, TC-2, TC-3, TC-5)
- [ ] The updated demo JSON remains valid strict JSON matching the demo-narrator schema (TC-4)
- [ ] `runs/goal-session-ops-hardening/journey-scripts/J-06.json`'s `default_timeout_ms` is a disclosed,
  cited value (≤9500 ms with cited timestamps, or reverted to 8000 ms) — never left at 18000 ms without a
  basis that survives review (TC-6)
- [ ] Both re-verified J-06 assertion values are confirmed correct against the live app and cited in the dev
  handoff (TC-7)
- [ ] The corrected `J-06.json` passes the deterministic replay end-to-end (TC-8)
- [ ] Target journeys J-06 (deterministic replay), J-07 and J-08 (LLM browser-qa lane) pass via
  browser-qa-agent (TC-8, TC-10)
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05 remain green via deterministic replay (TC-10)
- [ ] Zero files under `apps/backend/` or `apps/frontend/` changed (TC-9)
- [ ] No anti-goal violation introduced: AG-3 (the two re-verified J-06 assertion values match what the live app actually displays), AG-9 (no live network/paid-provider calls -- only reads against the already-running seed-backed app), AG-10 (if the app must be (re)started to verify a value, it is launched via `scripts/start-backend.sh`, host-guard caps intact)
- [ ] No application code changed; unit-test suite unaffected (verified via `git diff --stat` showing zero
  `apps/` paths)
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-23-dev.md`, stating explicitly the basis
  for the J-06 timeout decision and each re-verified assertion value (TC-6, TC-7)

## TESTING REQUIREMENTS

- Browser: J-06 via the corrected deterministic replay script; J-07 and J-08 via the LLM browser-qa lane
  (may reuse iter-21/22 evidence per the binding "Do not redo" list — no new TC-13/TC-14-scale trigger is
  needed or permitted); J-01/J-03/J-04/J-05 via deterministic replay (Required-still-passing).
- Unit/integration: none new — zero application source changes are planned this iteration. The demo JSON and
  journey-script edits are validated by JSON-parse (TC-4) and replay execution (TC-8), not pytest.
- Error cases: if a candidate live value cannot be re-verified this dispatch (e.g. the app is unreachable),
  the dev handoff must say so explicitly and must NOT keep an unverified assertion silently — fall back to
  the last independently-confirmed value or flag the step for the next iteration rather than guessing.

Test-first contract:

- TC-1: given `reports/goal-session-ops-hardening-demo.json` has zero `"journey": "J-06"` entries, when the
  developer appends step(s) sourced from `UT-J-06` in
  `reports/phase-goal-ops-hardening-iter-22-ui-test-results.md`, then the file contains ≥1 step object with
  `"journey": "J-06"`, `"new": true`, `"verified": true`.
- TC-2: given the file has zero `"journey": "J-07"` entries, when the developer appends step(s) sourced from
  `UT-J-07`, then the file contains ≥1 step with `"journey": "J-07"`, `"new": true`, `"verified": true`, whose
  `narration`/`point_out` cites only figures found verbatim in `reports/perf-budgets.md`'s "Iteration 22"
  section (not the "28.06 s window" phrasing from the browser-qa row).
- TC-3: given the file has zero `"journey": "J-08"` entries, when the developer appends step(s) sourced from
  `UT-J-08` and its three iter-22 full-page screenshots, then the file contains ≥2 steps with
  `"journey": "J-08"`, `"new": true`, `"verified": true` — one depicting the "refreshing" banner state, one
  depicting the post-warm fresh-serve state.
- TC-4: given the updated demo JSON, when parsed with `python3 -m json.tool`, then it parses as valid strict
  JSON and every step (old and new) retains the required keys (`n`, `title`, `narration`, `point_out`,
  `journey`, `new`, `verified`, `section`, `action`).
- TC-5: given the pre-existing 7 steps (`n` 1–7), when the updated file is diffed against the currently
  committed version, then none of their field values change and every new step uses `n ≥ 8`.
- TC-6: given `J-06.json`'s current undisclosed `default_timeout_ms: 18000`, when the developer inspects
  `logs/backend.log` and `forward_aggregate_cache` commit timestamps for a legitimate BCW overlap with J-06's
  own replay sequence, then the dev handoff records the finding and `default_timeout_ms` is set to ≤9500
  (citing the specific timestamps, if substantiated) or reverted to 8000 (if not) — never left at 18000
  uncited.
- TC-7: given `J-06.json`'s two changed assertions (`$304.89` on `/stocks/AAPL`; `"Setup & Pattern event
  study"` on `/research/event-study`), when the developer reads the live app/API for both pages, then the dev
  handoff states the current true displayed value for each and confirms the assertion text matches it exactly
  (or corrects it if it does not).
- TC-8: given the corrected `J-06.json`, when the deterministic replay harness executes it, then it PASSES
  end-to-end with 0 breaches, and the elapsed time of its slowest step is recorded in the dev handoff.
- TC-9: given zero application-code changes are planned, when `git diff <pre-iteration-snapshot> --stat` is
  run at review time, then it shows zero paths under `apps/backend/` or `apps/frontend/`.
- TC-10: given J-01, J-03, J-04, J-05, J-06, J-07, J-08 are all currently `passing`, when browser-qa-agent
  re-verifies this iteration, then J-01/J-03/J-04/J-05/J-06 all pass via deterministic replay and J-07/J-08
  pass via the LLM lane, with zero regressions.

## NOTES

- **This spec does not declare `GOAL_ACHIEVED`.** If the evaluator finds all three gaps closed and no new
  issue, all 7 Must-have journeys would remain `passing` with a now-complete evidence trail — but running any
  deterministic-gate/two-key-confirm process is the evaluator's/engine's decision, not this iteration's DoD.
- **Multi-iteration reading correction, logged to `assumptions.md` (iter-23).** iter-12 through iter-22 all
  treated the J-06/J-07/J-08 "Walkthrough ... viewable via `demo.sh ops-hardening --session-live`" clause as a
  settled non-autonomous, ungradable deliverable, because the *playback* is a human-interactive terminal mode
  that writes no artifact. The iter-22 CONFIRM evaluator's finding shows only the playback act is
  non-autonomous — the JSON manifest it plays from is 100% agent-authorable via the demo-narrator's own
  `session` mode. This iteration authors that manifest content directly; it does not attempt to trigger or
  record an actual `--session-live` session (still correctly out of scope for the *playback* itself).
- **If any of the three findings cannot be fully closed this dispatch** (e.g. no legitimate BCW-overlap basis
  can be found for J-06's timeout, so it simply reverts to 8000 ms and the developer suspects the original
  8000 ms may itself occasionally be tight under some untested interleaving), the dev handoff must say so
  plainly — do not round an unresolved finding into a clean "all three closed" claim.
- Non-blocking carry-overs, unaffected by this iteration (unchanged from iter-21/22's list): retarget
  `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches before removing the now-dangling
  imports; run `test_api_backtest.py`'s TC-11 + `test_data_manager.py`'s heavy fixtures off the constrained
  box; the oldest-date (2005) `scorecard_ms` + `resolved_run_ms` optimization (`backtest.py:162-177`) closes
  no journey alone and is not manufactured as busywork here; backlog card B-1107 stays owner-owned and
  optional.
- Depth is lean by design, not a downgrade from a prior recommendation — iter-22's own eval.md next-step
  section did not mandate full for a subsequent closeout pass of this shape; see BACKGROUND for the
  trigger-by-trigger justification.
