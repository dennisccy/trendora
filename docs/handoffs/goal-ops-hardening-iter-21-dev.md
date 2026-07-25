# goal-ops-hardening-iter-21 Dev Handoff

**Phase:** goal-ops-hardening-iter-21
**Date:** 2026-07-25
**Agent:** developer
**Status:** complete

## What Was Built

Nothing. This iteration is a zero-code, evidence-consolidation pass per the spec's own framing
("Close J-08 on complete evidence (TC-13/TC-14 consolidation, zero code changes)"). The developer's actual
deliverable this iteration is (1) an independent, read-only re-verification of a coherence-auditor advisory
from iter-20, and (2) this handoff, which cites the operator's already-recorded TC-13/TC-14 evidence by exact
path for the goal-evaluator. No backend or frontend source file was created, edited, or deleted.

**Explicit statement (TC-9): zero product source files changed this iteration.** Confirmed below under
"Verification."

## Files Changed

- `docs/handoffs/goal-ops-hardening-iter-21-dev.md` -- this handoff (new).
- `runs/goal-ops-hardening-iter-21/status.json` -- current_step updated to `dev_complete`.
- Nothing under `apps/backend/` or `apps/frontend/`.

## Investigation — independent re-verification of the iter-20 coherence-auditor's dangling-import advisory

The iter-20 `coherence.md` flagged `apps/backend/app/mcp/tools.py:38`'s `forward_aggregates_ingest_cached`
import as a dangling/unused import worth a lint-pass cleanup. This iteration's IN SCOPE explicitly required
independently re-verifying (read-only, not trusting the spec's own restatement of the claim) whether that is
actually a safe removal, before writing this section. I did not just re-read the spec's claim and transcribe
it — I re-derived it myself from the source and test files, and traced the actual call graph one level
further than the spec's own text does. Findings:

**Finding (a) — the identical unused-import shape exists in a SECOND file, not just the one iter-20 named.**
Both `apps/backend/app/api/backtest.py:75` and `apps/backend/app/mcp/tools.py:38` import
`forward_aggregates_ingest_cached` from `app.engine.forward_testing`, and in BOTH files that name has **zero
call sites** anywhere else in the file (verified by `grep -n "forward_aggregates_ingest_cached"` against each
file individually — the import line is the only hit in each). Both files instead call
`ensure_historical_forward_aggregates_dispatched` (imported one line above, at `backtest.py:74` /
`tools.py:37`) from their historical (`if not is_latest and evidence["evidence_status"] != "ready":`) branch —
`backtest.py:209-211` and `tools.py:297-299` respectively. `ensure_historical_forward_aggregates_dispatched`
is a different function, defined in `app.engine.forward_testing` (iter-20's own addition). So by direct call
graph, both imports are dead code today — but "dead by call graph" and "safe to delete" are not the same
claim, per finding (b).

**Finding (b) — both imports are load-bearing `monkeypatch.setattr` targets in four existing tests; removing
either breaks all four.** In `apps/backend/tests/test_forward_testing_serving_split.py`:
- `test_backtest_route_is_latest_never_reaches_ingest_or_compute` (line 576) and
  `test_backtest_route_is_latest_not_yet_computed_is_honest_200` (line 607) each locally
  `import app.api.backtest as backtest_module` and then call
  `monkeypatch.setattr(backtest_module, "forward_aggregates_ingest_cached", _boom)` (lines 592, 621).
- `test_query_backtest_mcp_tool_is_latest_never_reaches_ingest_or_compute` (line 641) and
  `test_query_backtest_mcp_tool_not_yet_computed_mirrors_endpoint` (line 670) each locally
  `import app.mcp.tools as tools_module` and call
  `monkeypatch.setattr(tools_module, "forward_aggregates_ingest_cached", _boom)` (lines 657, 680).

None of the four calls passes `raising=False`, so pytest's default `raising=True` applies:
`monkeypatch.setattr` itself checks `hasattr(target_module, name)` before assigning, and raises
`AttributeError` immediately if the attribute is absent. If either import line were deleted, the corresponding
module would no longer have `forward_aggregates_ingest_cached` as an attribute at all, and all four
`monkeypatch.setattr(...)` calls (two per module) would raise `AttributeError` at setup, before the tests'
own bodies even run — not a safe no-op, exactly as the spec claimed. I confirmed this is not merely a static
argument: I ran the file (see "Tests Run" below) and all 25 tests, including these four by name, currently
pass — live, behavioral proof that both attributes currently exist and are currently exercised by these
monkeypatch calls on today's build.

**Secondary finding (non-blocking, restated per the spec's explicit instruction) — the monkeypatch no longer
guards the code path it was written to guard, post iter-20's dispatch refactor.** Before iter-20, the
historical branch in both `backtest.py` and `tools.py` called `forward_aggregates_ingest_cached` directly, in
a loop, using each file's own imported reference to the name. That made monkeypatching
`backtest_module.forward_aggregates_ingest_cached` / `tools_module.forward_aggregates_ingest_cached` a
structurally sound trap: if the `is_latest` branch were ever mistakenly routed into the historical branch's
compute logic, the SAME name, in the SAME module namespace, would be hit and `_boom` would fire. Iter-20
replaced that direct loop-call with a call to `ensure_historical_forward_aggregates_dispatched`, whose
background worker (`_run_historical_forward_aggregates_dispatch`, `forward_testing.py:1205`) calls
`forward_aggregates_ingest_cached(session, h, cfg, as_of=as_of)` at `forward_testing.py:1224` — but that call
resolves through `forward_testing.py`'s OWN module-global reference to the name (it is defined in that same
file, at line 1036), a completely separate name binding from `backtest_module.forward_aggregates_ingest_cached`
or `tools_module.forward_aggregates_ingest_cached`. `monkeypatch.setattr` only rebinds the attribute on the
ONE module object passed to it, so patching `backtest_module`'s or `tools_module`'s copy of the name would
NOT intercept a call sourced from `forward_testing.py`'s own namespace. Concretely: if the `if not is_latest`
gate at `backtest.py:209` / `tools.py:297` were ever accidentally weakened so a LATEST request reached
`ensure_historical_forward_aggregates_dispatched`, these four tests would NOT catch it — the dispatch function
itself is not monkeypatched, and its eventual internal call to `forward_aggregates_ingest_cached` happens on a
background thread through a name these tests never touch. Today, the only thing preventing that misrouting is
the `if not is_latest` conditional itself (code-review discipline), not a test-enforced trap. This is a real
gap worth closing in a future, properly-scoped test-hardening iteration (retarget the monkeypatch at
`app.engine.forward_testing.forward_aggregates_ingest_cached`, or at
`ensure_historical_forward_aggregates_dispatched` directly) — but is explicitly OUT OF SCOPE here (no code or
test changes ship this iteration) and is not itself a coherence violation: the four tests still correctly
prove their literal claim (the `is_latest` branch's OWN code, as written today, never calls
`forward_aggregates_ingest_cached`), they just no longer double as a regression trap for a *different*,
adjacent invariant they used to incidentally cover before the refactor.

**Conclusion: the iter-20 coherence-auditor's advisory is confirmed NOT a safe pure-lint fix**, in both named
locations, matching the spec's claim in full plus the additional mechanism-level detail above. No import was
removed. No source file was touched.

## Evidence citations (TC-9)

Per the DoD, this handoff cites the following by exact section/path rather than re-describing the numbers:

- **`reports/perf-budgets.md` § "Post-STALL owner-authorized measurements — TC-13 + TC-14 (2026-07-25,
  operator, direction 1)"** (starts at line 3379) — TC-13: `/backtest` ≤1.5 s budget under a concurrent-INGEST
  overlay, **0 / 4096 breaches, max 429 ms**, vs. the iter-16 baseline 11/68 @ 12,655 ms. TC-14: Part A
  (`kill -9` → `scripts/start-backend.sh` restart → `ok/ready` in ~25 s), Part B (wide backfill checkpointed
  to `dates_done 1366/2904`, `kill -9` mid-run, restart shows `status: interrupted`, checkpoint preserved).
- **`runs/goal-ops-hardening-iter-21/operator-tc13-tc14-evidence.md`** — the operator's own narrative record
  of the same two measurements, including the host-guard ritual detail (affinity `0-3,8-11` + 6144 MB cap,
  hwmon sampler live, thermal watchdog re-armed, peak 89 °C) and the explicit AG-9 confirmation
  (`provider: "seed"` throughout, no live network fetch).
- Raw poll data: `runs/goal-ops-hardening-iter-21/tc13-backtest-poll.csv` (4096-row TC-13 capture, referenced
  by the perf-budgets.md section above).

I did not re-run either measurement (out of scope, per the spec's explicit instruction — both are dated
2026-07-25, fresh, and owner-authorized).

## Tests Run

Command (host-guard-confined, matching this session's standing invocation pattern — `taskset -c 0-3,8-11` +
BLAS/OMP/MKL/numexpr capped at 4 threads, from `project-extensions/host-guard/host-guard.env`'s
`HOST_GUARD_CPU_LIST`/`HOST_GUARD_BLAS_THREADS`; scoped to the one file relevant to this iteration's
investigation, never the full suite):

```
cd apps/backend
TMPDIR=<pipeline-isolated tmp dir> TMP=<same> TEMP=<same> \
taskset -c 0-3,8-11 env OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 \
  .venv/bin/python -m pytest tests/test_forward_testing_serving_split.py -q
```

Result: **25 passed, 0 failed, in 3.50s.** This is the whole file, including the exact four tests named in
Finding (b) above by name (`test_backtest_route_is_latest_never_reaches_ingest_or_compute`,
`test_backtest_route_is_latest_not_yet_computed_is_honest_200`,
`test_query_backtest_mcp_tool_is_latest_never_reaches_ingest_or_compute`,
`test_query_backtest_mcp_tool_not_yet_computed_mirrors_endpoint`) — matches iter-20's own count for this file
(25: 23 pre-existing + 2 updated), confirming nothing has drifted since. No source edit was made before or
during this run (this was a read-only confirmation that the currently-committed build passes, not a
RED/GREEN TDD cycle — the spec's IN SCOPE bullet explicitly scopes the re-verification method to "read-only,"
so I did not do a temporary edit-and-revert to force an `AttributeError` empirically, even though that would
have been possible; the behavioral proof above (25/25 pass today, including these four) is the read-only-
compatible equivalent).

I launched this via `setsid nohup ... &` from a foreground call and polled with a bounded loop (per the
coordinator's operational note), not `run_in_background`, and confirmed no stray `pytest`/`uvicorn`/`next`
processes remained afterward (`pgrep -af` clean).

## Verification (git status / diff at completion — IN SCOPE requirement)

```
$ git status --short --porcelain -- apps/backend apps/frontend
(no output)
$ git diff --stat -- apps/backend apps/frontend
(no output)
```

Both empty. Zero files under `apps/backend/` or `apps/frontend/` changed, staged, or left untracked by this
iteration.

## Required-still-passing journeys / owner-blocked items (TC-10)

- **J-01, J-03, J-05** — required-still-passing; their regression evidence is deterministic golden replay,
  which is the reviewer/browser-qa pipeline stage's own tooling, not a developer-invoked step for a zero-diff
  iteration. Since no source file changed, there is no code-level reason for any of the three to have moved.
- **J-04** — required-still-passing; per the DoD, its disruptive kill/restart + checkpoint-survival contract
  is satisfied by **TC-14's fresh operator evidence** (2026-07-25, cited above), not a fresh browser-qa
  capture (which is expected to SKIP the disruptive steps, as it always has since iter-15). Consistent with
  that routing, and because the operator already ran a full `kill -9` → `scripts/start-backend.sh` restart
  cycle today under the complete host-guard ritual on this exact (unchanged) build, I did **not** independently
  start/stop the backend or frontend service myself this iteration. This is a deliberate deviation from
  developer.md's general "service startup works" pre-handoff checklist item, made because: (1) that checklist
  exists to catch startup regressions introduced by the developer's OWN changes, and zero changes shipped;
  (2) TC-14 Part A already supplies fresher, more rigorous evidence (a genuine `kill -9`, not just a clean
  stop/start) than a redundant cycle by me would; (3) this host has a documented hard-reset history under load
  (AG-10) and the session's own ethos is to avoid gratuitous host cycles, not manufacture them. Flagging this
  judgment call explicitly rather than silently skipping the checklist item.
- **J-06, J-07** — remain explicitly `partial`/blocked, solely on the owner's still-open 3-way transient-
  contention budget-treatment decision (accept-and-log / sanction a redesign / rescope to steady-state reads —
  iter-20 eval's fork, restated in `reports/perf-budgets.md` "Iteration 20": 3.0–6.3 s `/backtest`, max
  1.60 s `/api/health` during the ~30 s historical background-compute window). Nothing in this iteration
  attempts to resolve that decision, silently loosen the budget, or re-propose either previously-rejected
  mitigation (off-process compute, full historical precompute) — per the spec's explicit OUT OF SCOPE list.
  This is not silently dropped: it is the one item this handoff calls out as still owner-gated.

## What's still owed by downstream stages (not developer scope this iteration)

- **TC-1, TC-2** — a fresh iter-21-dated browser capture of `/backtest`'s `is_latest=true`
  ready → refreshing → ready state machine across a literal small single-day backfill. Per the spec's own
  Frontend section, this is explicitly "browser-qa-agent's own Chrome-MCP pass against the existing,
  unchanged `RefreshingEvidenceBanner` and ready-state display — not a code change," so I did not attempt it.
- **TC-4, TC-5, TC-8** — golden-replay confirmation for J-01/J-03 and the LLM browser-qa fallback for J-05,
  both pipeline-stage tooling.
- **TC-3** — the goal-evaluator's synthesis of TC-13 (numeric stress proof) + this iteration's still-pending
  TC-1/TC-2 capture (literal small-single-day rendered-state proof) into a J-08 verdict. This handoff
  deliberately does not itself declare J-08 passing, per the DoD's own instruction.

## Known Issues

- No code-level issues — there is no code change to have issues. The one open item is the still-outstanding
  owner decision on the J-06/J-07 transient-contention budget treatment, which is not this iteration's or any
  agent's to resolve (see above).
- The browser-based TC-1/TC-2 capture that completes J-08's evidence picture has not happened as of this
  handoff — it is the next pipeline stage's job, not a gap in this iteration's own deliverable.
