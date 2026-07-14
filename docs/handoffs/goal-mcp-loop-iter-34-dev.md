# goal-mcp-loop-iter-34 Dev Handoff

**Phase:** goal-mcp-loop-iter-34
**Date:** 2026-07-14
**Agent:** developer
**Status:** complete

## What Was Built

**Nothing — this is a deliberate zero-code verification-only iteration, and the DoD is satisfied
by an empty product diff.** Per the iter spec: "This iteration changes no source code... the
developer step is a no-op (no code), and the value comes from the browser-qa step's replay lane."

iter-33 was CONTINUE but ended CLOSURE-FAIL: 6 of its 7 required-still-passing journeys
(J-01/J-02/J-04/J-05/J-13/J-18) were only byte-identity-carried, never deterministically replayed,
because a FULL iteration routes through `run-phase.sh`, which has zero replay-lane machinery (that
lane exists only in `goal-iter-lean.sh`). iter-34's job is to run that replay lane — widened by the
spec to all 17 built, golden-scripted journeys as a periodic full regression after four consecutive
FULL iterations (30-33) — and produce the `regression-replay-results.md` artifact iter-33 never
created. That replay + the J-20 LLM re-confirmation are the browser-qa step's work, which runs after
this developer pass in the lean pipeline. My job this pass was to confirm there is genuinely nothing
to build, and that the stack is in a clean, verified-bootable state before that step runs.

### Verification performed

1. **Product-source / ledger byte-identity.** `git diff HEAD --stat` over the exact DoD-named paths
   (`apps/backend/app`, `apps/frontend`, `config.yaml`, `apps/backend/data/seed`,
   `runs/goal-session-mcp-loop/state/certified-claims.jsonl`,
   `runs/goal-session-mcp-loop/state/staging-ledger.jsonl`) → **empty output**. The only tree changes
   present are harness bookkeeping the pipeline itself owns (`runs/goal-session-mcp-loop/telemetry.jsonl`
   append, `runs/goal-session-mcp-loop/dispatch/req.*` files) plus the iter-34 spec doc itself, all
   written before this pass started.
2. **No Evidence Claim registered.** `grep -n "## Evidence Claim" docs/phases/goal-mcp-loop-iter-34.md`
   matches nothing as a heading (only the OUT-OF-SCOPE bullet's prose mention). The post-decompose gate
   passes automatically; canonical Bonferroni divisor stays **8**.
3. **Blueprint conformance already satisfied.** `runs/goal-session-mcp-loop/state/blueprint.md` already
   carries the "iter-34 clarification (verification-only regression-replay closeout...)" paragraph
   (written when the spec was decomposed, matching the iter-23/25/28/29 precedent pattern) — no edit
   needed or made by this pass.
4. **Targeted frozen-golden ledger tests** (fast, targeted — NOT the full ~10-11h 30-year suite, which
   the spec's own TESTING REQUIREMENTS explicitly says not to run since no code path changed):
   ```
   cd apps/backend && .venv/bin/python -m pytest \
     tests/test_evidence.py::test_canonical_ledger_frozen_golden \
     tests/test_staging_ledger_routing.py::test_committed_staging_ledger_is_the_regenerated_30y_discovery \
     -v
   ```
   Result: **2 passed in 0.19s** — both ledgers pinned byte-for-byte (7 canonical entries, divisors
   1..7, all FAIL; 7 staging entries, all FAIL; 0 PASS anywhere).
5. **Pre-replay service-readiness confirmation** (the iter-20-lesson precondition the spec's TESTING
   REQUIREMENTS calls for, performed on isolated ports so it doesn't collide with anything else on the
   host):
   - `rm -rf apps/frontend/.next` (forces a genuine cold rebuild, not a stale-bundle reuse).
   - Started both services in **prod mode** (`scripts/start-backend.sh` / `scripts/start-frontend.sh`
     — never `dev.sh`) with `CHAIN_BACKEND_PORT=18471 CHAIN_FRONTEND_PORT=18472`.
   - Backend: `GET http://localhost:18471/api/health` → **HTTP 200** after 1s. Body confirms
     `"status": "ok"`, `"readiness": "ready"`, `"symbol_count": 590`, `"warmup": {"done": 89, "total":
     89, "status": "ok"}`, and — directly relevant to this iteration's one Target journey, J-20 —
     `"preflight": {"verdict": "GO", "reasons": []}` with all three components (`servability`,
     `freshness`, `integrity`) `"ok": true`.
   - Frontend: cold `next build` completed clean from the removed `.next` (produced every route,
     including the J-17/18/19/20-era pages: `/research/budget`, `/research/registry`,
     `/research/graveyard`, `/evidence`, `/stocks`, `/watchlist`, etc.), then `next start` served
     `GET http://localhost:18472/` → **HTTP 200** after 5s (`Ready in 275ms`).
   - Spot-checked five key pages, all **HTTP 200**: `/stocks`, `/evidence`, `/research/registry`,
     `/research/graveyard`, `/research/budget`.
   - Clean shutdown: both processes killed, ports 18471/18472 confirmed free, `ps aux` confirms no
     stray `uvicorn`/`next-server`/`next start` processes remain.

   This is a genuine bring-up smoke test (forced-fresh production build, not a reused bundle) — it
   gives the browser-qa step reasonable confidence the stack it starts next (on its own
   `ensure_phase_ports`-computed ports) will come up clean, without leaving any process of mine
   running to conflict with it.

### Why the replay/merge artifacts are not written here

`reports/phase-goal-mcp-loop-iter-34-regression-replay-results.md` and
`reports/phase-goal-mcp-loop-iter-34-ui-test-results.md` are the deterministic-replay + LLM browser-qa
step's output (Step 3 of `goal-iter-lean.sh`), which runs after this developer step and reads the
golden scripts in `runs/goal-session-mcp-loop/journey-scripts/*.json`. This pass does not drive a
browser and does not write those files — it confirms (git diff, targeted tests, live service boot)
that there is a stable, unchanged, cleanly-bootable product surface for that step to replay against.

## Files Changed

None (product code). `git diff HEAD` is empty on all product source (`apps/backend/app/**`,
`apps/frontend/**`, `config.yaml`, `apps/backend/data/seed/**`) and on both evidence ledgers. The only
files written by this developer pass are this handoff and `runs/goal-mcp-loop-iter-34/status.json`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_evidence.py::test_canonical_ledger_frozen_golden tests/test_staging_ledger_routing.py::test_committed_staging_ledger_is_the_regenerated_30y_discovery -v`

Result: **2 passed, 0 failed** (0.19s). Matches the iter spec's own TESTING REQUIREMENTS ("Unit/integration:
none required — zero product source diff, no code path changed. Do NOT run the slow 30-year backend
fixture.") — this targeted pair is extra byte-identity evidence for the DoD's ledger claim, not a
required regression run, and does not touch the full suite.

Additionally, both backend and frontend were live-booted in prod mode (see "Pre-replay
service-readiness confirmation" above) and cleanly shut down — no server process was left running.

## Known Issues

- None introduced by this pass — zero product code touched.
- **Carried forward from iter-33, explicitly OUT OF SCOPE this pass** (per the iter-34 spec's NOTES —
  do not bundle into a verify-only cycle): B1 (autouse `conftest.py`
  `READINESS_VERDICT_HISTORY_PATH` redirect so suite runs stop appending to the untracked
  `preflight-verdict-history.jsonl`); B2 (thread the already-computed readiness dict into
  `compute_preflight` to drop the redundant second `compute_readiness` call on the ~2s poll); T1
  (background `pytest tests/test_readiness.py tests/test_health.py -v` for the record); the
  readme-maintainer preflight + budget-panel bullets.
- **SYSTEMIC / framework flags already recorded in the iter-34 spec's own NOTES** (not re-litigated
  here, and not this lean cycle's dev scope): the QA + ux-regression report templates bake a false
  "replay lane runs in the next phase step" claim; the "required-still-passing deterministic replay"
  DoD line is structurally unsatisfiable by any FULL iteration since `run-phase.sh` has no replay
  lane.
- **Found but out of scope — not fixed:** `.claude/project-template.md` (symlinked to
  `incredible_auto_dev/.claude/project-template.md`) currently reads as the generic, unfilled
  framework template (placeholder `<e.g., ...>` values throughout), not Trendora's project-specific
  stack config. `git log --follow` on that path shows it WAS filled in for Trendora at commit
  `1357d97` ("Filled for this project... The full architecture/decision record is
  docs/trendora-design.md...") but a later framework re-vendor, `5aa1d08` ("chore(framework): vendor
  incredible_auto_dev @ feat/goal-mode-interactive", 2026-06-07), overwrote it back to the generic
  upstream placeholder. This predates iter-20 and has not blocked any iteration since — every
  developer pass (this one included) sources exact test/start commands from prior dev handoffs and
  the actual `apps/`/`scripts/` structure instead. Flagging for the human or framework maintainer per
  `.claude/maintenance-protocol.md`; genuinely out of this iteration's zero-code scope to fix.
- The PASS/FAIL determination for the 17 Required-still-passing journeys plus Target journey J-20
  depends on the browser-qa step's deterministic replay + LLM re-confirmation, which runs next. This
  developer pass confirms the product surface is byte-identical to HEAD and that both services boot
  cleanly from a forced-fresh production build; it does not itself drive a browser or produce the
  replay/merge result artifacts, per this lean iteration's explicit "developer step is a no-op" scope.
