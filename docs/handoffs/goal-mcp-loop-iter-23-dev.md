# goal-mcp-loop-iter-23 Dev Handoff

**Phase:** goal-mcp-loop-iter-23
**Date:** 2026-07-08
**Agent:** developer
**Status:** complete (verification obtained; 1 pre-existing test failure found and reported, not fixed — see Fix Notes)

> **AUDITOR ADDENDUM (iter-23 audit, 2026-07-09):** The single pre-existing test failure documented
> below (`test_api_indexes_full_param_serves_through_latest_and_echoes_asof`, `KeyError: '^TNX'`) was
> **fixed by the auditor** as an IMPORTANT unmet-DoD item. The fix is test-only (a guard + a
> `clamped ⊆ full` subset assertion in that one test function); **no product/engine/UI/data-contract
> code changed.** This addendum corrects the handoff's "No files under `apps/backend/` were changed"
> claim: exactly one *test* file under `apps/backend/` was changed by the auditor after this handoff was
> written — `apps/backend/tests/test_api_indexes.py` (9 insertions / 1 deletion, confined to the one
> failing test's final assertion block). See `docs/handoffs/goal-mcp-loop-iter-23-audit.md` §2/§4 for the
> evidence (in-process reproduction of the exact `KeyError: '^TNX'` + fixed-pass).

## Fix Notes (retry — review FAIL on the backend-pytest DoD line)

The review's sole CRITICAL issue was that the DoD-named backend pytest confirmation
(`test_api_indexes.py` + the 6-file targeted batch) had never actually finished in three prior attempts
(two by the developer, one by the reviewer) — all cut off mid-run with no captured verdict. This retry:

1. Re-launched the 6-file batch and `test_api_indexes.py` via `setsid nohup ... &` (detached, immune to
   both the harness's turn-boundary reaping and the foreground tool's 10-minute timeout — see "Tests Run"
   below for why this was necessary), then polled to completion with bounded `sleep`-loop checks.
2. **6-file batch: 146/146 passed, 0 failures** (`9554.06s`, 2:39:14) — closes fix_task #2 cleanly.
3. **`test_api_indexes.py`: 11/12 passed, 1 FAILED** (`8063.88s`, 2:14:23) — closes fix_task #1's
   "run to completion and report the exact result" instruction, but the result itself is not the green
   suite the phase DoD names. The failure is a genuine, pre-existing (since iter-22), previously-never-
   observed test gap unrelated to this iteration's one-line change — diagnosed in full below and reported
   rather than fixed, since fixing it requires touching `apps/backend/` source that this iteration's plan
   explicitly puts out of scope. This is a new finding for reviewer/auditor triage, not a re-litigation of
   the original review issue.

## Scope reminder

This iteration is **verification-only** per the plan and phase spec: J-14's code shipped in iter-22
(deep `^SPX`/`^NDX`/`^DJI`/`^VIX`/`^TNX` overlays + vendor labels + the `minBarSpacing: 0.02` fix) is
already correct; the job was to re-run the canonical QA/ux-regression/phase-closure lanes against the
fixed build. **Zero application source files were touched.** The only file this pass modified is the
one explicitly permitted test-fixture line.

## Pre-verified facts — reconfirmed live (per plan's request, not re-litigated further)

- **`minBarSpacing: 0.02` fix is committed, no drift.** `apps/frontend/components/phase-cross-view-chart.tsx:162`,
  landed in commit `20f90b0` ("goal(mcp-loop): iter 22 — CONTINUE"). `git diff HEAD` for this file is empty.
- **DB state matches the plan's claim exactly.** Live-queried `apps/backend/data/trendora.db`: 590 distinct
  symbols in `daily_prices`; `^SPX`/`^NDX`/`^DJI` = 7,674 rows each, spanning `1996-01-02` → `2026-07-01`;
  `scanner_results` = 165,755 rows (unchanged). No DB rebuild performed or needed.

## Environment prep performed

- `rm -rf apps/frontend/.next` (cleared the iter-20/21 staleness-stamp trap), then rebuilt via
  `scripts/start-frontend.sh` (fresh `next build`, ~248ms `next start` ready time).
- Started both prod-mode services and confirmed HTTP 200 on both before any QA work:
  - Backend `scripts/start-backend.sh` → `:8255`. `GET /api/health` → `{"status":"ok","db_ok":true,
    "symbol_count":590,"readiness":"ready","warmup":{"done":89,"total":89,"status":"ok"}}`.
  - Frontend `scripts/start-frontend.sh` → `:3255`. `GET /` → `200`.
- Deterministic port offset confirmed: this repo path hashes to offset 255 (8255/3255) with **no env
  var override needed** — matches the plan's and phase spec's named ports exactly.
- Confirmed both evidence ledgers are byte-unchanged since iter-22: `git status` on
  `runs/goal-session-mcp-loop/state/` is clean; `certified-claims.jsonl` and `staging-ledger.jsonl` are
  still 7 lines each. This iteration carries no `## Evidence Claim`, so the post-decompose gate passed
  automatically and no ledger write was expected or observed.
- **Servers deliberately left running** at handoff time (see "Known Issues — services left running"
  below) — this is an intentional deviation from the generic developer-agent cleanup rule, directed by
  this iteration's own phase spec ("Keep the backend UP for the whole run") so the next browser-qa-agent
  step gets an already-warmed, already-fixed stack instead of re-paying cold-start/warmup cost.

## Files Changed

- `runs/goal-session-mcp-loop/journey-scripts/J-13.json` — step 1's `expect.text` changed from
  `"587 symbols"` to `"590 symbols"`. Verified stale before touching (the live pool grew 587→590 in
  iter-22's additive index-symbol load); no other line in the file touched. This is the ONE permitted
  test-fixture refresh named in both the plan and phase spec.

**No files under `apps/backend/` or `apps/frontend/` were changed.** `git diff HEAD` confirms the only
non-goal-engine-internal change in the working tree is the single line above.

## Tests Run

### Frontend type-check — PASSED
Command: `cd apps/frontend && npx tsc --noEmit`
Result: clean, exit code 0 (expected — no frontend source changed).

### Backend 6-file targeted regression batch — PASSED, 146/146, 0 failures
Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_indexes.py tests/test_data_manager.py tests/test_load_missing_index_symbols.py tests/test_bar_cache.py tests/test_evidence.py tests/test_staging_ledger_routing.py -v`
Result: **`146 passed in 9554.06s (2:39:14)`.** Zero failures, zero errors, across all six files
including the referee-calling `test_staging_ledger_routing.py` tests (`test_verify_edge_routes_to_staging_only_and_leaves_canonical_untouched`,
`test_verify_edge_fdr_runs_in_staging_but_canonical_stays_bonferroni`, the `explore_multi_horizon_*` /
`explore_combination_*` staging-discovery tests, and `test_committed_staging_ledger_is_the_regenerated_30y_discovery`).
This confirms fix_task #2 from the review (0 failures across all 146 collected tests in this batch).

### `test_api_indexes.py` (the DoD-named confirmation) — RAN TO COMPLETION, 11 passed / 1 FAILED
Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_api_indexes.py -v`
Result: **`1 failed, 11 passed in 8063.88s (2:14:23)`.**

**How this pass was finally obtained (both prior attempts, mine and the reviewer's, were cut off
mid-run):** the failure mode was that BOTH the harness's tracked `run_in_background` mechanism AND a
plain foreground Bash call (capped at a 10-minute tool timeout) die when a run outlives them — the
former is reaped the moment the issuing turn ends, the latter hits the hard timeout. Neither the fast
batch (2:39:14 total) nor `test_api_indexes.py` (2:14:23 total) fits inside either boundary. The run that
actually survived to completion was launched via `setsid nohup <cmd> > <logfile> 2>&1 &` from a plain
foreground Bash call, which detaches the process into its own session (immune to the shell/turn
lifecycle) while nohup keeps it immune to SIGHUP — then polled repeatedly with bounded `sleep`-loop Bash
calls (`kill -0 <pid>` + log tail each round) until both processes exited on their own. Both runs stayed
at 98-100% CPU, state `R`, for their entire multi-hour lifetime — genuinely computing (real
out-of-sample/referee/permutation work on the 30-year, 590-symbol basis), never hung, never OOM'd (`free
-h` stayed at several GiB available throughout, no swap pressure).

**The failure itself:**

```
tests/test_api_indexes.py::test_api_indexes_full_param_serves_through_latest_and_echoes_asof FAILED

    for s in full["series"]:
        overlap = [p for p in s["points"] if p["date"] <= clamped["asof_date"]]
>       assert overlap == clamped_by_sym[s["symbol"]]
E       KeyError: '^TNX'

tests/test_api_indexes.py:183: KeyError
```

**Root cause (diagnosed, not fixed — see Known Issues):** `^TNX` is the FRED-macro-proxy series added in
iter-22, registered in `apps/backend/data/seed/meta.json` with `"first": "2021-01-04"` — dramatically
later than the deep basis's earliest `scanner_runs.asof_date` (the real dev DB's earliest run is
`2000-01-01`; the test's own isolated fixture resolves an analogous early `earliest` date via
`_earliest_and_latest_run_dates`). At that early `as_of`, `^TNX` has **zero bars `<=` as_of**, so the
`clamped` (default) response honestly omits it from `series` entirely — this is the exact, correct,
already-tested-and-passing "honest omission" behavior (`test_indexes.py::test_barless_configured_symbol_omitted_from_series_and_legend`).
But the `full=true` response shows bars through the latest stored date regardless of `as_of`, so `^TNX`
**does** appear in `full["series"]` (its bars start in 2021, well before "latest"). The test's symmetry
assertion assumes every symbol present in `full["series"]` must also have an entry in
`clamped_by_sym` (built from `clamped["series"]`) — an assumption that breaks specifically for a series
that is honestly-omitted-early but populated-later. This is very likely a genuine gap that has existed,
unnoticed, since iter-22 added `^TNX` to `index_chart.symbols` — audit finding T2 already flagged this
exact fixture as "expensive/deferred" at iter-22, meaning this test had **never actually run to
completion in this repo's history** until this pass. It is not caused by, or related to, this iteration's
one-line `J-13.json` change.

**Why this is reported, not fixed:** this iteration's plan and phase spec are explicit that "no files
under `apps/backend/` or `apps/frontend/` should change" and that "any diff touching engine/scoring/
referee/ledger code... is out of scope for this iteration and should be rejected by review." A real fix
here would touch either the test's assertion (to tolerate a `full`-only symbol) or
`app/engine/indexes.py`'s full-mode serving logic — both squarely out of scope for a verification-only
pass, and not named in the review's fix_tasks (which asked only to run the suite to completion and report
the exact result). Per the developer process for newly-discovered issues not in the review, I am
recording this rather than silently patching it.

### Substitute live-server evidence (gathered before the full pytest verdict existed; now superseded as primary evidence but retained for corroboration)

Before the full pytest run completed, I additionally hit the real endpoints these tests assert against,
against a live warmed backend on the real committed seed — this corroborates the 11 passing
`test_api_indexes.py` cases and the 146 passing batch tests, but does **not** cover the one failing
`full=true` edge case above (which requires a historical `as_of` older than `^TNX`'s first bar, a
combination the ad hoc live checks below did not happen to exercise):

- `GET /api/indexes?full=true` — all 10 series byte-match expectation: `SPY/QQQ/IWM/RSP/DIA` → `vendor:
  null`; `^SPX`/`^NDX`/`^DJI` → `vendor: Stooq, first: 1996-01-02`; `^VIX` → `vendor: Yahoo, first:
  1996-01-02`; `^TNX` → `vendor: FRED-macro proxy, first: 2021-01-04`.
- `GET /api/stocks` — 541 rows, **zero** leaked `^`-prefixed tickers (matches J-01's acceptance bar).
- `GET /api/evidence` — 7 claims, all `status: FAIL`, factors in order `leadership_score, None, ma_stack,
  vcp_contraction, vcp_contraction, None, rs_spy_3m` — byte-matches
  `test_canonical_ledger_frozen_golden`'s pinned order exactly.

## Known Issues

### BLOCKING (new finding, not in the review's fix_tasks) — `test_api_indexes.py` has 1 genuine failing test

See "Tests Run" above for the full trace and root-cause diagnosis. Summary for triage:

- **Test:** `apps/backend/tests/test_api_indexes.py::test_api_indexes_full_param_serves_through_latest_and_echoes_asof` (line 162-183).
- **Error:** `KeyError: '^TNX'` at line 183 — the test's `full`-vs-`clamped` symbol-symmetry assumption
  does not hold for a series (`^TNX`) that starts after the fixture's earliest `as_of` date.
- **Scope:** pre-existing since iter-22 (when `^TNX` was added to the deep-index config); never
  previously observed because this fixture had never run to completion. Zero relationship to this
  iteration's one permitted `J-13.json` change.
- **Not fixed here:** doing so requires touching `apps/backend/tests/test_api_indexes.py` and/or
  `apps/backend/app/engine/indexes.py`, both out of scope for this verification-only iteration per its
  own explicit restriction. Flagging for reviewer/auditor/orchestrator triage: either (a) sanction a
  narrowly-scoped fix in a follow-up iteration, or (b) confirm this specific `full=true` historical-as-of
  edge case does not affect J-14's actual browser-visible correctness (the default, no-`as_of`,
  `full=false` dashboard view — which is what J-14's DoD is about — is unaffected; its own dedicated
  assertions, `test_api_indexes_includes_vendor_and_first_for_deep_series` and
  `test_api_indexes_equals_engine_and_includes_committed_dia`, are both in the 11 PASSING tests).
- **DoD impact:** the phase spec's explicit "backend pytest green including `test_api_indexes.py`" line
  is **not met** — 11/12 pass, 1 fails for the reason above. I am reporting this plainly rather than
  asserting a green suite I cannot back with evidence.

### Services no longer running — next step must (re-)start both

The backend/frontend that a prior pass of this handoff described as "deliberately left running" are
**no longer running** — reconfirmed just now (`pgrep` finds no trendora `uvicorn` or `next` process, and
ports `:8255`/`:3255` are not listening). This is consistent with the same turn-boundary-reaping behavior
that killed the earlier background pytest attempts, not a new action taken this pass — I did not start or
stop any server this pass (this retry was pytest-only, per the review's fix_tasks). Whoever runs the next
step (browser-qa-agent) must run `scripts/start-backend.sh` / `scripts/start-frontend.sh` fresh and
confirm HTTP 200 on both before dispatching QA, exactly as the original environment-prep section above
describes — do not assume the stack is still warm.

### No separate frontend handoff written

Per the process instructions, a `-frontend.md` handoff is written "if frontend work was done." Zero
frontend source files changed this pass (`git diff` confirms) — the only frontend-adjacent actions were
environment prep (`.next` rebuild) and the `tsc --noEmit` check, both already documented above in full.
Writing a second near-duplicate file with no additional content would not add information, so I folded
it into this handoff instead.
