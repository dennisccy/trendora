# Goal Iteration 33 — Fix the frontend launcher's dev/prod bug, then close J-06's real-browser TTI sweep

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 33
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: `scripts/start-frontend.sh` is the shared serving
  infrastructure every browser-qa evidence capture and all 8 golden journey-scripts depend on;
  switching it from `next dev` to a real `next build` + `next start` can change rendered markup
  broadly (dev-overlay removal, CSS-module/hydration differences) in ways no single journey's own
  test covers — this is exactly the kind of interaction that crosses agent/journey boundaries.
- **Frontend Present:** yes
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-08, J-09 (the full passing set — the
  launcher change is shared infrastructure for every page across every journey, so a full smoke
  pass is warranted rather than a narrow subset)
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

Fix `scripts/start-frontend.sh` so it genuinely serves production mode (it has execed `npx next dev`
since it was written, contradicting its own "prod mode" label), then run and record the real-browser
11-page time-to-interactive sweep that bug has blocked for the entire session, closing J-06.

## BACKGROUND

Two consecutive evaluators (iter-31, iter-32) named the SAME blocking item first in their next-step
recommendation: `scripts/start-frontend.sh:28` execs `npx next dev`, so the one remaining piece of J-06
— a real-browser TTI sweep — would today measure Next.js dev-mode on-demand compilation, not production
page-load time. `scripts/measure-perf.sh`'s own header independently calls the same script "PROD MODE
ONLY" and documents refusing to trust dev-mode timings. Per the iter-31 lesson ("any iteration that
measures page-load/TTI performance, writes to `reports/perf-budgets.md`, touches
`scripts/start-frontend.sh`..."), this iteration fixes the launcher first, then performs the
measurement — not the other way around, since a dev-mode sweep would still be unmeasurable-as-specified.

**Rule-5 deviation, stated:** the iter-32 evaluator's next-step recommendation bundles this J-06 fix
together with J-07's two remaining steps (health-poll latency recording, the induced-memory-pressure
drill) into one recommended pass. This spec deliberately splits them: the launcher-mode change is
cross-cutting infrastructure risk (it can alter rendered markup for every page and every golden
script's assertions), and J-07's induced-pressure drill is itself a heavy-compute, host-guard-relevant
load event (AG-10). Bundling both risky items in one iteration would make a joint failure
undiagnosable (rule 5). J-07's remaining steps are explicitly carried to iteration 34.

A second, small, orthogonal fix rides along: `merge_ui_test_results.py`'s `_ROW_RE` has been flagged by
four consecutive evaluators as capable of silently dropping a `TC-`-prefixed headline FAIL from the
merged QA report — "must be fixed before any achievement run." It is bundled here because it is
low-risk, mechanical, and touches no product code or the launcher, so it does not add to this
iteration's one risky change.

**Lessons applied:** iter-31 (launcher/perf-budgets pairing, above); iter-28 (a golden `expect` must
assert stable content — a heading/label — never a status/verdict string or incidental markup; if any
golden script's assertion breaks purely because dev-vs-prod markup differs, repair to stable content,
never weaken silently); iter-32 (a memory/size-bound test must measure the named term, not the whole
call — not directly triggered here, but the same "measure the actual thing, not a proxy" discipline
applies to the TTI sweep: it must be a genuine browser measurement, not another curl proxy).

## IN SCOPE

### Backend
- None — no backend code path changes. This iteration is a frontend-launcher + measurement +
  documentation pass. `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched`, and `stock_obs`'s bounded design (all binding
  "Do not redo") are untouched.

### Frontend
- [ ] Rewrite `scripts/start-frontend.sh` to genuinely serve production mode: run `next build` only
  when the existing `.next` build is missing or stale relative to `apps/frontend`'s sources /
  `package.json` / lockfile, then `exec npx next start -p "$FRONTEND_PORT"` — preserve the existing
  port-detection (`CHAIN_FRONTEND_PORT` / deterministic offset) and `NEXT_PUBLIC_API_URL` /
  `NEXT_PUBLIC_API_PORT` export logic byte-for-byte.
- [ ] Verify `next build` completes clean (no TypeScript/build-only errors) against the current
  `apps/frontend` tree; if the production build surfaces an error dev mode tolerated, fix only what's
  needed to make the build pass — no page's rendered content or behavior changes otherwise.
- [ ] If a build fails for a reason that cannot be resolved this iteration, the script must exit
  non-zero with the build's own error output — never silently fall back to `next dev` or serve a stale
  `.next` build.
- [ ] Re-confirm `scripts/dev.sh`'s frontend subshell is untouched (still `next dev`, still the
  existing AG-10 `ulimit -v` exemption for the reason already documented there) — this fix is scoped
  to `start-frontend.sh` only.
- [ ] Correct `scripts/measure-perf.sh`'s header comment (documentation only) that currently says
  there is "no reliable way to detect [next dev]" as a known limitation — the frontend genuinely is
  prod mode now, so the caveat no longer applies; no change to the timing/measurement code itself.

### Measurement (J-06 steps 1-3)
- [ ] Run a real-browser (not curl) time-to-interactive + on-load-API-latency sweep of all 11 J-06
  step-1 pages (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`,
  `/scanner-runs`, `/backtest`, `/watchlist`, one `/research` lab) against the fixed prod-mode
  frontend plus a warm backend on the committed-seed DB, alongside a fresh ≤5s boot-to-health
  reading; append the results as a new dated `## Iteration 33` section in `reports/perf-budgets.md`
  (same file, no second artifact).
- [ ] Any reading over its committed budget is recorded as an honest WARN with a one-line stated
  cause — never silently dropped, mirroring this file's existing WARN convention.
- [ ] Write J-06 step 3's code-level audit into the dev handoff: for every on-load endpoint the 11
  pages call, name the persisted table/cache it reads and confirm none performs an unbounded
  `daily_prices` scan or recomputes an already-ingest-warmed aggregate.

### Golden-script hygiene (only if the launcher change requires it)
- [ ] Replay all 8 existing golden journey-scripts (J-01, J-03, J-04, J-05, J-06, J-07, J-08, J-09)
  against the now-prod-mode frontend. If — and only if — an assertion breaks purely because
  dev-vs-prod markup differs (never because of a behavior change), repair that one assertion to check
  stable content (a heading or label, per the iter-28 lesson), and document the specific diff that
  motivated the repair. Any FAIL that reflects a real behavior difference is a signal, not something
  to paper over.

### Framework / tooling (non-journey, bundled — low risk, orthogonal to the launcher change)
- [ ] Widen `_ROW_RE` in `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` (the
  only copy in this checkout; `scripts/` is a symlink to `incredible_auto_dev/scripts`) to match both
  `UT-` and `TC-` prefixed row ids, and ensure a headline FAIL present in either input file survives
  into the merged output's headline — never silently downgraded to PASS because one file's rows
  failed to parse.
- [ ] Add a test case to that module's existing test file proving a `TC-`-prefixed FAIL row survives
  the merge (RED before the fix, GREEN after).

### New user-facing capability
None — this iteration changes how the frontend is served for automated evidence capture and
measurement; it does not change any page's user-visible behavior beyond removing the Next.js
dev-mode error-overlay pill (a defect fix, not a new capability).

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — no new component, no new page; existing pages now render without the dev-mode overlay.

### Product surface delta
None beyond the console-error-pill removal (a correctness fix to an existing honest-status
expectation, not a new surface).

### Blueprint conformance
No new page or nav entry. J-06 keeps its existing cross-cutting Information Architecture home —
`reports/perf-budgets.md` as the canonical measurement artifact (not a UI page) — per
`runs/goal-session-ops-hardening/state/blueprint.md`'s Feature/journey-homes table. This iteration's
blueprint update paragraph (iter-33) has been appended additively; no Information Architecture change.

### Data-contract additions
None. This iteration re-times values already registered in the Data Contract (Regime score / market
phase / forward-returns row, Index series row, Coverage payload row, Job history row, Membership
timeline / research hot-key row) under corrected launch-mode conditions and appends to the SAME
`reports/perf-budgets.md` artifact (Page performance budgets row) — no second computing module, no
second serving endpoint, no second measurement file.

## OUT OF SCOPE

- J-07's two remaining steps (recording `GET /api/health`'s LATENCY through a live warm; the
  induced-memory-pressure abort drill) — deliberately deferred to iteration 34 (rule 5: one
  risky/heavy-compute change per iteration; this iteration's one risky change is the launcher's build
  mode). The J-07 "crash-free warm + healthy health" demo `[NEW]` walkthrough steps ride along with
  that iteration too, not this one (rule 7: ride-alongs piggyback on real work, never drive an
  iteration).
- `run_rows` (`forward_testing.py:1195`) — a recorded WATCH ITEM (iter-32/f), not a blocker; binding
  "Do not redo," left untouched.
- The stray `GET /research/factor-lab?all=true` 404 — binding "Do not redo": iter-32 already
  established it has no call site in `apps/frontend`; not re-investigated.
- `warmup.py:194` (the badge decision after a permanently failed warm-up) and `prices.py:141` (the
  ingest coverage refresh's whole-table `daily_prices` prefill) — both carried, minor, unresolved AG-8
  findings; unrelated to this iteration's surface, not touched.
- `J-07.json`'s literal `n=8869` assertion (needs a stable assertion or a recorded provenance line) —
  deferred to the iteration that next touches J-07 (iteration 34), since it is that journey's own
  golden script.
- `test_no_magic_numbers.py` red on `indicators.py`/`forward_testing.py`; UT-04's fresh-install DB
  fixture or a written waiver; `test_forward_testing_serving_split.py`'s four `is_latest`
  monkeypatches — all carried, unrelated to this iteration.
- Amending `docs/goal.md` to accept dev-mode TTI numbers — considered and rejected (see
  `assumptions.md` iter-33): the goal's own step-1 text already calls this script "prod mode," so the
  more goal-faithful fix is the script, not the wording.
- Applying host-guard CPU/memory caps to the frontend build step, or adding `start-frontend.sh` to
  `HOST_GUARD_MARKER_FILES` — out of scope; the frontend has always been host-guard-exempt (dev.sh's
  own documented carve-out), and expanding that is a separate, unrequested decision.
- Any change to `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched`, or `stock_obs`'s bounded accumulation shape —
  binding "Do not redo."

## DEFINITION OF DONE

- [ ] J-06 passes via browser-qa-agent: prod-mode 11-page real-browser TTI + on-load-latency sweep
  recorded in `reports/perf-budgets.md`; every measurement within budget or an honest disclosed WARN;
  dev handoff's step-3 code-level on-load audit written.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-08, J-09 remain green (deterministic
  replay + LLM fallback) against the now-prod-mode frontend.
- [ ] No anti-goal violation introduced: AG-8 (no new unbounded scan introduced by this iteration),
  AG-10 (the HOST-GUARD blocks in `scripts/dev.sh` and `scripts/start-backend.sh` are byte-unchanged),
  AG-3 (served values byte-identical to before the launcher change).
- [ ] Unit tests pass; no regressions; `merge_ui_test_results.py` accepts `TC-`/`UT-` prefixed rows and
  preserves a headline FAIL from either input file.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-33-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-06 (target, all 11 step-1 pages); J-01, J-03, J-04, J-05, J-08, J-09
  (required-still-passing, deterministic golden replay).
- Unit/integration: `merge_ui_test_results.py`'s test module (new `TC-`-prefixed-FAIL-survives-merge
  case); a smoke check that `scripts/start-frontend.sh` produces a `next start` process (not
  `next dev`) on the configured port, mirroring the existing `test_start_backend_script.py` pattern.
- Error cases: a `next build` failure must surface its own error and exit non-zero, never silently
  fall back to `next dev` or serve a stale `.next` build; a merged QA report whose ONLY input file
  uses `TC-` ids and reports a headline FAIL must show that FAIL in the merged output, never a
  laundered PASS.

Test-first contract:

- TC-1: given `apps/frontend`'s `.next` build is missing or older than its sources/`package.json`,
  when `scripts/start-frontend.sh` runs, then it runs `next build` before `next start`, and `ps aux`
  shows a `next start` process (not `next dev`) bound to the configured `FRONTEND_PORT`.
- TC-2: given an existing, current `.next` build (sources unchanged since the last build), when
  `scripts/start-frontend.sh` runs again, then it skips the rebuild and execs `next start` directly.
- TC-3: given a deliberately broken `apps/frontend` source file, when `scripts/start-frontend.sh` runs,
  then the script exits non-zero and prints the `next build` error output, and no `next dev` or stale
  `.next` fallback process is left running.
- TC-4: given a warm backend on the committed-seed DB and the fixed prod-mode frontend, when each of
  the 11 J-06 step-1 pages is loaded in a real browser, then time-to-interactive and each page's
  on-load API latencies are recorded, and a fresh ≤5s boot-to-health reading is captured, all appended
  as a new dated section in `reports/perf-budgets.md`.
- TC-5: given a reading in that sweep exceeds its committed budget, when it is recorded, then the row
  shows an explicit WARN with a one-line stated cause rather than being omitted from the table.
- TC-6: given the dev handoff for this iteration, when it is opened, then it lists every on-load
  endpoint the 11 pages call, names the persisted table/cache each reads, and states plainly that none
  performs an unbounded `daily_prices` scan or recomputes an already-ingest-warmed aggregate.
- TC-7: given the fixed prod-mode frontend, when a browser DevTools console is opened on each of the
  11 pages after load, then zero error-level console entries are present (no Next.js dev-overlay pill).
- TC-8: given the golden replay scripts for J-01, J-03, J-04, J-05, J-08, J-09, when replayed against
  the now-prod-mode frontend, then all 6 report PASS with no assertion regression from their
  `last_passing_iter=32` baseline.
- TC-9: given `git diff` against `project-extensions/host-guard/host-guard.env`'s
  `HOST_GUARD_MARKER_FILES` (`scripts/dev.sh scripts/start-backend.sh`), when this iteration's diff is
  inspected, then both listed files' HOST-GUARD blocks are byte-unchanged.
- TC-10: given a QA input file whose rows use `TC-`-prefixed ids and whose headline is FAIL, when
  `merge_ui_test_results.py` runs, then the merged output includes those rows and its headline shows
  FAIL (not a laundered PASS) — a RED-before/GREEN-after test proves this.
- TC-11: given the fixed prod-mode launcher, when `scripts/measure-perf.sh --help`/header text is
  read, then it no longer states the unresolved "no reliable way to detect [next dev]" caveat as an
  open limitation.

## NOTES

- Two consecutive evaluators (iter-31, iter-32) put this launcher decision FIRST in their next-step
  recommendation, ahead of everything else remaining in the session — treated here as an unblocker
  (priority rubric rule 3), not a human-owned blocker (rule 6): both remedies goal.md offers (fix the
  script, or amend the wording) are agent-executable; this spec picks the fix, logged as an
  interpretation call in `assumptions.md` (iter-33).
- `runs/goal-session-ops-hardening/state/blueprint.md` has an additive iter-33 paragraph appended
  documenting this decision — no Information Architecture or Data Contract row changed its
  computing module/serving endpoint.
- If the golden-script hygiene pass (above) finds MORE than a small, markup-only diff — i.e., any
  journey's actual behavior looks different under prod mode versus dev mode — stop and treat that as
  a genuine finding for the evaluator, not something to quietly patch around in a golden script.
- Carried forward unchanged for iteration 34: J-07's health-latency recording + induced-pressure
  drill (and its demo `[NEW]` walkthrough steps); `J-07.json`'s `n=8869` provenance/stability fix;
  `warmup.py:194`; `prices.py:141`; the owner's `GET /api/health` ≤0.1s budget-vs-0.127787s-measured
  gap (non-blocking today, per iteration-state.md).
