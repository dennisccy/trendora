# goal-mcp-loop-iter-39 Dev Handoff

**Phase:** goal-mcp-loop-iter-39
**Date:** 2026-07-15
**Agent:** developer
**Status:** complete

## What Was Built

**Nothing — this is a deliberate zero-code verification-only iteration, and the DoD is satisfied
by an empty product diff.** Per the iter spec: "No backend source changes... No frontend source
changes... the developer step is a no-op on product code."

iter-38 (FULL) delivered J-23 (the watchlist concentration X-ray, backlog B-204) cleanly but ended
**CLOSURE-FAIL** on one Definition-of-Done line: the required-still-passing set (J-01/02/03/05/10/13/20)
was carried on byte-identity and never golden-replayed, because a FULL iteration routes through
`run-phase.sh`, which has zero deterministic-replay-lane machinery — that lane exists only in
`goal-iter-lean.sh` (the recurring iter-33/36/38 structural gap). iter-39's job is to run that
replay lane — widened to the **full on-disk golden set, J-01–J-14 + J-17–J-23 (21 journeys)** —
folding in the new **J-23.json** golden for its first replay, and to correct the iter-38 QA lane's
TC-17 row (which graded the required-still-passing set PASS on a bare HTTP-200 smoke instead of a
golden replay). That replay + report-writing + record-correction is the browser-qa step's work
(Step 3 of `goal-iter-lean.sh`, which runs `demo_runner.py --mode verify` and
`merge_ui_test_results.py`), which runs after this developer pass. My job this pass — matching the
proven iter-33→34 and iter-36→37 lean-closeout precedent — was to confirm there is genuinely
nothing to build, and that the stack is in a clean, verified-bootable state before that step runs.

### Verification performed

1. **Product-source / ledger byte-identity.** `git diff HEAD --stat` and `git status --porcelain`
   over the exact DoD-named paths (`apps/backend/app`, `apps/frontend`, `config.yaml`,
   `apps/backend/data/seed`, `runs/goal-session-mcp-loop/state/certified-claims.jsonl`,
   `runs/goal-session-mcp-loop/state/staging-ledger.jsonl`,
   `runs/goal-session-mcp-loop/state/pre-registrations.jsonl`) → **empty output on all**. The only
   tree changes present (`git status --porcelain`) are harness bookkeeping the pipeline itself owns
   (`runs/goal-session-mcp-loop/telemetry.jsonl` append, `runs/goal-session-mcp-loop/dispatch/req.*`
   files) plus the iter-39 spec doc itself, all written before this pass started. Git HEAD is
   `9f48117` (iter-38 showcase artifacts, on top of the `66bb348` J-23 delivery commit named in the
   spec's BACKGROUND).
2. **No Evidence Claim registered.** `grep -n "^## Evidence Claim" docs/phases/goal-mcp-loop-iter-39.md`
   matches nothing — the spec's own metadata states "Evidence Claim: none". The post-decompose gate
   passes automatically; canonical Bonferroni divisor stays **8**. Verified both ledgers directly:
   `certified-claims.jsonl` and `staging-ledger.jsonl` each hold exactly 7 entries, every entry
   `status: FAIL`, 0 PASS anywhere in either file; `pre-registrations.jsonl` holds 11 entries,
   untouched.
3. **Blueprint conformance already satisfied.** `runs/goal-session-mcp-loop/state/blueprint.md` has
   **zero diff vs HEAD** (byte-identical) — consistent with the spec's own "Blueprint conformance"
   section ("No new surfaces... No Information-Architecture change; no nav-skeleton change; no
   `blueprint.reapproval-requested`"). Unlike some prior lean closeouts, no iter-39-specific
   clarification paragraph was needed or added at decompose time; the file being wholly untouched
   this iteration is itself the correct evidence of zero contract/IA change.
4. **Golden-script coverage.** `runs/goal-session-mcp-loop/journey-scripts/` holds exactly the 21
   files the DoD names — J-01 through J-14, plus J-17 through **J-23** (no J-15/J-16, the
   golden-less perf journeys carried on byte-identity per the spec's OUT OF SCOPE) — confirming the
   browser-qa step's replay lane has a script to run for every required row, including the
   newly-folded **J-23.json** golden (linted clean at iter-38, replayed for the first time here).
5. **Targeted frozen-golden ledger tests** (fast, targeted — NOT the full ~10-11h 30-year suite,
   which the spec's own TESTING REQUIREMENTS explicitly says not to pin as a DoD gate since no code
   path changed):
   ```
   cd apps/backend && .venv/bin/python -m pytest \
     tests/test_evidence.py::test_canonical_ledger_frozen_golden \
     tests/test_staging_ledger_routing.py::test_committed_staging_ledger_is_the_regenerated_30y_discovery \
     -v
   ```
   Result: **2 passed in 0.22s** — both ledgers pinned byte-for-byte.
6. **Pre-replay service-readiness confirmation** (the iter-20/iter-35-lesson precondition the
   spec's NOTES call out — done on isolated ports 18471/18472 so it doesn't collide with the live
   goal-mode engine or the browser-qa step's own port allocation that follows):
   - `rm -rf apps/frontend/.next` (forces a genuine cold rebuild, not a stale-bundle reuse) —
     confirmed removed before rebuild.
   - Started both services in **prod mode** (`scripts/start-backend.sh` / `scripts/start-frontend.sh`
     — never `dev.sh`) with `CHAIN_BACKEND_PORT=18471 CHAIN_FRONTEND_PORT=18472`.
   - Backend: `GET http://localhost:18471/api/health` → **HTTP 200** after 1s. Body:
     `"readiness": "ready"`, `"warmup": {"done": 89, "total": 89, "status": "ok"}`,
     `"symbol_count": 590`, and — directly relevant to this iteration's replay set —
     `"preflight": {"verdict": "GO", "reasons": []}` with all four components (`servability`,
     `freshness`, `integrity`, `drift`) `"ok": true`. Backend log clean: no
     error/exception/traceback/fail lines.
   - Frontend: cold `next build` completed clean from the removed `.next` (compiled every route
     with zero build errors/warnings, including the newer `/watchlist` X-ray page), then
     `next start` served `GET http://localhost:18472/` → **HTTP 200** after 2s (`Ready in 263ms`).
     Frontend log clean: no error/warn/fail lines.
   - Spot-checked **18 pages**, all **HTTP 200**: `/`, `/stocks`, `/stocks/AAPL`, `/sectors`,
     `/themes`, `/backtest`, `/evidence`, `/data`, `/watchlist`, `/research`, `/research/registry`,
     `/research/graveyard`, `/research/budget`, `/research/referee-audit`, `/research/samples`,
     `/research/factor-lab`, `/scanner-runs`, `/methodology` — covering the end-state page of every
     one of the 21 golden-scripted journeys.
   - Confirmed `.next/BUILD_ID` postdates every frontend source file (`find ... -newer BUILD_ID`
     returned empty) — the stale-prod-build caution from lessons.md iter-20/35, satisfied trivially
     here since the build was forced fresh from a removed `.next` and no frontend source changed.
   - Clean shutdown: both processes killed, both ports (18471/18472) confirmed free via `ss -ltnp`,
     `ps aux` confirms no stray `uvicorn`/`next-server`/`next start` process of mine remains. (The
     unrelated `next dev -p 3301` / `next-server` belonging to a different project, tapeology,
     continues running independently on this host — left untouched, matching iter-37's precedent.)
   - Post-cleanup `git status --porcelain` re-checked: identical to the pre-verification state (only
     the harness telemetry append + the iter-39 spec + dispatch files) — the verification pass left
     no stray artifacts (`.next` is gitignored).

   This is a genuine bring-up smoke test (forced-fresh production build, not a reused bundle) — it
   gives the browser-qa step reasonable confidence the stack it starts next (on its own
   `ensure_phase_ports`-computed ports) will come up clean, without leaving any process of mine
   running to conflict with it.

### TC-17 over-claim — confirmed context (correction itself is the browser-qa/merge step's output)

Read `reports/qa/goal-mcp-loop-iter-38-qa.md:105` to confirm the spec's characterization: the iter-38
QA lane's **TC-17** row ("J-23 Required-Still-Passing: J-01..J-20 Green") graded **PASS** on the
evidence "Regression check on /, /stocks, /evidence, /sectors, /research/factor-lab, /data all 200;
watchlist add/remove untouched" — a bare HTTP-200 smoke, not a golden/deterministic replay. This
matches the exact iter-33/iter-36 over-claim pattern the spec names. The corrected row (reflecting
actual deterministic-replay evidence per journey) belongs in the merged
`reports/phase-goal-mcp-loop-iter-39-ui-test-results.md`, which — like the
`regression-replay-results.md` report itself — is produced by the browser-qa step
(`goal-iter-lean.sh` Step 3: `demo_runner.py --mode verify` + `merge_ui_test_results.py`), not by
this developer pass. Flagging it here for traceability; the iter spec (which the browser-qa step
also reads) already carries the correction instruction verbatim.

### Why the replay/merge artifacts are not written here

`reports/phase-goal-mcp-loop-iter-39-regression-replay-results.md` and
`reports/phase-goal-mcp-loop-iter-39-ui-test-results.md` are the deterministic-replay step's output
(Step 3 of `goal-iter-lean.sh`), which runs after this developer step and reads the golden scripts
in `runs/goal-session-mcp-loop/journey-scripts/*.json`. This pass does not drive a browser and does
not write those files — it confirms (git diff, ledger content check, targeted tests, live service
boot with a forced-cold frontend rebuild) that there is a stable, unchanged, cleanly-bootable
product surface for that step to replay all 21 journeys against, including the first-ever replay of
the newly-folded J-23 golden.

## Files Changed

None (product code). `git diff HEAD` is empty on all product source (`apps/backend/app/**`,
`apps/frontend/**`, `config.yaml`, `apps/backend/data/seed/**`) and on all three evidence/registry
ledgers. The only files written by this developer pass are this handoff and
`runs/goal-mcp-loop-iter-39/status.json`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_evidence.py::test_canonical_ledger_frozen_golden tests/test_staging_ledger_routing.py::test_committed_staging_ledger_is_the_regenerated_30y_discovery -v`

Result: **2 passed, 0 failed** (0.22s). Matches the iter spec's own TESTING REQUIREMENTS
("Unit/integration: none new... do NOT introduce or pin any slow, rarely/never-completed test... as
a hard DoD gate") — this targeted pair is extra byte-identity evidence for the DoD's ledger claim,
not a required regression run, and does not touch the full ~30-year suite.

Additionally, both backend and frontend were live-booted in prod mode from a forced-cold frontend
build (see "Pre-replay service-readiness confirmation" above) and cleanly shut down — no server
process was left running.

## Known Issues

- None introduced by this pass — zero product code touched.
- **SYSTEMIC / framework flag, recorded (not owed to this iter, per the spec's own NOTES):** the
  "required-still-passing deterministic replay" DoD line remains structurally unsatisfiable by any
  FULL iteration since `run-phase.sh` has no replay lane — it has now CLOSURE-FAILed three times
  (iter-33, iter-36, iter-38). The durable fix (add the replay lane to `run-phase.sh` / the full path
  of `run-goal.sh`, or run the closure one-liner replay inline inside full iters) is recording-only
  per the spec; not attempted here.
- `.claude/project-template.md` (symlinked to `incredible_auto_dev/.claude/project-template.md`)
  still reads as the generic, unfilled framework template (a pre-existing, previously-flagged gap —
  see iter-34/iter-37 dev handoffs). Not this pass's scope; test/start commands were sourced from the
  actual `apps/`/`scripts/` structure and prior dev handoffs instead, as before.
- The PASS/FAIL determination for the 21 golden-scripted journeys — including the first-ever replay
  of the newly-folded **J-23** golden and the re-verification of the seven closure-named
  required-still-passing journeys (J-01/02/03/05/10/13/20) — depends on the browser-qa step's
  deterministic replay, which runs next. This developer pass confirms the product surface is
  byte-identical to HEAD, both evidence ledgers + the pre-registration registry are frozen/untouched
  (7/7 FAIL in each ledger, divisor stays 8), all 21 required golden scripts are present on disk, and
  both services boot cleanly from a forced-fresh production build with the backend's own
  `/api/health` preflight reading GO; it does not itself drive a browser or produce the
  replay/merge result artifacts or the TC-17 record correction, per this lean iteration's explicit
  "developer step is a no-op on product code" scope.
