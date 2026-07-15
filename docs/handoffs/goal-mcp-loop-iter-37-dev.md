# goal-mcp-loop-iter-37 Dev Handoff

**Phase:** goal-mcp-loop-iter-37
**Date:** 2026-07-15
**Agent:** developer
**Status:** complete

## What Was Built

**Nothing — this is a deliberate zero-code verification-only iteration, and the DoD is satisfied
by an empty product diff.** Per the iter spec: "This iteration changes no source code... the
developer step is a no-op (no code), and the value comes from the browser-qa step's replay lane."

iter-36 was CONTINUE but ended CLOSURE-FAIL on a single Definition-of-Done line: the
required-still-passing journeys were not deterministically replayed. The closure auditor named
**J-05 and J-11** as the two unverified rows (QA over-claimed "all live-verified" with unevidenced
TC-19/TC-20 conclusions, no screenshot), because a FULL iteration routes through `run-phase.sh`,
which has zero deterministic-replay-lane machinery — that lane exists only in `goal-iter-lean.sh`.
Replay debt has now accumulated across two iterations: J-21.json (iter-35) and J-22.json (iter-36)
have never run through the deterministic lane either. iter-37's job is to run that replay lane —
widened by the spec to **all 20 built, golden-scripted journeys** as the periodic full regression
after two consecutive FULL feature iterations — and produce the `regression-replay-results.md`
artifact iter-36 never created. That replay is the browser-qa step's work (Step 3 of
`goal-iter-lean.sh`), which runs after this developer pass. My job this pass was to confirm there
is genuinely nothing to build, and that the stack is in a clean, verified-bootable state before
that step runs.

### Verification performed

1. **Product-source / ledger byte-identity.** `git diff HEAD --stat` over the exact DoD-named paths
   (`apps/backend/app`, `apps/frontend`, `config.yaml`, `apps/backend/data/seed`,
   `runs/goal-session-mcp-loop/state/certified-claims.jsonl`,
   `runs/goal-session-mcp-loop/state/staging-ledger.jsonl`) → **empty output**. The only tree
   changes present (`git status --porcelain`) are harness bookkeeping the pipeline itself owns
   (`runs/goal-session-mcp-loop/telemetry.jsonl` append, `runs/goal-session-mcp-loop/dispatch/req.*`
   files) plus the iter-37 spec doc itself, all written before this pass started.
2. **No Evidence Claim registered.** `grep -n "## Evidence Claim" docs/phases/goal-mcp-loop-iter-37.md`
   matches nothing as a heading (only the OUT-OF-SCOPE bullet's prose mention of the phrase). The
   post-decompose gate passes automatically; canonical Bonferroni divisor stays **8**. Verified both
   ledgers directly: `certified-claims.jsonl` and `staging-ledger.jsonl` each hold exactly 7 entries,
   divisors 1..7, **every entry `status: FAIL`**, 0 PASS anywhere in either file.
3. **Blueprint conformance already satisfied.** `runs/goal-session-mcp-loop/state/blueprint.md`
   already carries the "iter-37 clarification (verification-only regression-replay closeout — ZERO
   contract change...)" paragraph (written when the spec was decomposed, matching the
   iter-23/25/28/29/34 precedent pattern) — no edit needed or made by this pass.
4. **Golden-script coverage.** `runs/goal-session-mcp-loop/journey-scripts/` holds exactly the 20
   files the DoD names — J-01 through J-14, plus J-17 through J-22 (no J-15/J-16, which are the
   golden-less perf journeys carried on byte-identity per the spec's OUT OF SCOPE) — confirming the
   browser-qa step's replay lane has a script to run for every required row, including the two newly
   folded-in goldens J-21.json and J-22.json.
5. **Targeted frozen-golden ledger tests** (fast, targeted — NOT the full ~10-11h 30-year suite,
   which the spec's own TESTING REQUIREMENTS explicitly says not to run since no code path changed):
   ```
   cd apps/backend && .venv/bin/python -m pytest \
     tests/test_evidence.py::test_canonical_ledger_frozen_golden \
     tests/test_staging_ledger_routing.py::test_committed_staging_ledger_is_the_regenerated_30y_discovery \
     -v
   ```
   Result: **2 passed in 0.21s** — both ledgers pinned byte-for-byte.
6. **Pre-replay service-readiness confirmation** (the iter-20/iter-35-lesson precondition the
   spec's TESTING REQUIREMENTS calls for explicitly: "do this BEFORE the browser-qa step" — done on
   isolated ports 18471/18472 so it doesn't collide with the live goal-mode engine or its own
   port allocation for the browser-qa step that follows):
   - `rm -rf apps/frontend/.next` (forces a genuine cold rebuild, not a stale-bundle reuse) —
     confirmed removed before rebuild.
   - Started both services in **prod mode** (`scripts/start-backend.sh` / `scripts/start-frontend.sh`
     — never `dev.sh`) with `CHAIN_BACKEND_PORT=18471 CHAIN_FRONTEND_PORT=18472`.
   - Backend: `GET http://localhost:18471/api/health` → **HTTP 200** after 3s. Body settled to
     `"readiness": "ready"`, `"warmup": {"done": 89, "total": 89, "status": "ok"}`, and —
     directly relevant to this iteration's replay set — `"preflight": {"verdict": "GO", "reasons":
     []}` with all four components (`servability`, `freshness`, `integrity`, `drift`) `"ok": true`.
     Backend log is clean: startup complete, three health probes served 200, clean shutdown, no
     errors/warnings.
   - Frontend: cold `next build` completed clean from the removed `.next` (compiled every route
     with zero build errors/warnings, including the newer J-21/J-22-era pages `/data` and
     `/research/referee-audit`), then `next start` served `GET http://localhost:18472/` → **HTTP
     200** after 8s (`Ready in 251ms`).
   - Spot-checked **16 pages**, all **HTTP 200**: `/`, `/stocks`, `/sectors`, `/themes`,
     `/backtest`, `/evidence`, `/data`, `/watchlist`, `/research`, `/research/registry`,
     `/research/graveyard`, `/research/budget`, `/research/referee-audit`, `/research/samples`,
     `/scanner-runs`, `/methodology` — covering the end-state page of every one of the 20
     golden-scripted journeys.
   - Clean shutdown: both processes killed (`pkill` + `fuser -k`), both ports (18471/18472)
     confirmed free, `ps aux` confirms no stray `uvicorn`/`next-server`/`next start` process of mine
     remains. (An unrelated `next-server` on port 3301 belongs to a different project, tapeology,
     running independently on this host — left untouched.)

   This is a genuine bring-up smoke test (forced-fresh production build, not a reused bundle) — it
   gives the browser-qa step reasonable confidence the stack it starts next (on its own
   `ensure_phase_ports`-computed ports) will come up clean, without leaving any process of mine
   running to conflict with it.

### Why the replay/merge artifacts are not written here

`reports/phase-goal-mcp-loop-iter-37-regression-replay-results.md` and
`reports/phase-goal-mcp-loop-iter-37-ui-test-results.md` are the deterministic-replay + LLM
browser-qa step's output (Step 3 of `goal-iter-lean.sh`), which runs after this developer step and
reads the golden scripts in `runs/goal-session-mcp-loop/journey-scripts/*.json`. This pass does not
drive a browser and does not write those files — it confirms (git diff, ledger content check,
targeted tests, live service boot with a forced-cold frontend rebuild) that there is a stable,
unchanged, cleanly-bootable product surface for that step to replay all 20 journeys against,
including a fresh, dedicated row for the two closure-named journeys J-05 and J-11.

## Files Changed

None (product code). `git diff HEAD` is empty on all product source (`apps/backend/app/**`,
`apps/frontend/**`, `config.yaml`, `apps/backend/data/seed/**`) and on both evidence ledgers. The
only files written by this developer pass are this handoff and `runs/goal-mcp-loop-iter-37/status.json`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_evidence.py::test_canonical_ledger_frozen_golden tests/test_staging_ledger_routing.py::test_committed_staging_ledger_is_the_regenerated_30y_discovery -v`

Result: **2 passed, 0 failed** (0.21s). Matches the iter spec's own TESTING REQUIREMENTS
("Unit/integration: none required — zero product source diff, no code path changed. Do NOT run the
slow 30-year backend fixture.") — this targeted pair is extra byte-identity evidence for the DoD's
ledger claim, not a required regression run, and does not touch the full suite.

Additionally, both backend and frontend were live-booted in prod mode from a forced-cold frontend
build (see "Pre-replay service-readiness confirmation" above) and cleanly shut down — no server
process was left running.

## Known Issues

- None introduced by this pass — zero product code touched.
- **Carried forward from iter-36, explicitly OUT OF SCOPE this pass** (per the iter-37 spec's OUT OF
  SCOPE / NOTES — do not bundle into a verify-only cycle): audit finding B1 (git-add
  `referee-audit-report.json` at the showcase step); F1 (tripwire prose / catchable temporal-leak
  deferred to the B-204 referee-settings sweep); B2 (push the contaminated assembler's cohort-date
  bound into SQL); the stale wording fixes in dev-handoff / what-to-click / ui-test-plan.
- **SYSTEMIC / framework flag already recorded in the iter-37 spec's own NOTES** (not
  re-litigated here, and not this lean cycle's dev scope): the "required-still-passing deterministic
  replay" DoD line is structurally unsatisfiable by any FULL iteration since `run-phase.sh` has no
  replay lane — it has now CLOSURE-FAILed twice (iter-33, iter-36); the QA + ux-regression report
  templates additionally bake a false "the replay lane runs in the next phase step" claim. Durable
  fixes are recorded in the spec's NOTES for the human/framework maintainer, not attempted here.
- `.claude/project-template.md` (symlinked to `incredible_auto_dev/.claude/project-template.md`)
  still reads as the generic, unfilled framework template (a pre-existing, previously-flagged gap —
  see iter-34's dev handoff). Not this pass's scope; test/start commands were sourced from the
  actual `apps/`/`scripts/` structure and prior dev handoffs instead, as before.
- The PASS/FAIL determination for the 20 golden-scripted journeys — including the fresh, dedicated
  rows for Target journeys J-05 and J-11 that close the iter-36 CLOSURE-FAIL gap, and the two newly
  folded-in goldens J-21/J-22 — depends on the browser-qa step's deterministic replay (and any LLM
  re-confirmation of a lint/selector-drift quarantine), which runs next. This developer pass
  confirms the product surface is byte-identical to HEAD, both ledgers are frozen all-FAIL, all 20
  required golden scripts are present on disk, and both services boot cleanly from a forced-fresh
  production build; it does not itself drive a browser or produce the replay/merge result
  artifacts, per this lean iteration's explicit "developer step is a no-op" scope.
