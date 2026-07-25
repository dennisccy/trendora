# Iteration 21 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-21
**Date:** 2026-07-25
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration

Confirmed independently (not merely trusting the spec's or dev handoff's own framing) that this is a
zero-product-code, evidence-consolidation iteration:

- `runs/goal-session-ops-hardening/iter-21/iter-diff.md` (bounded diff vs snapshot
  `a9b3835beb149619199c3561b5c256e0a3de2a3b`): **"(no changes)"**.
- Re-ran the noise-excluded `git diff a9b3835beb149619199c3561b5c256e0a3de2a3b -- . <exclusions>` myself:
  empty output.
- Scoped independently to product source: `git diff a9b3835... --stat -- 'apps/*'` → empty;
  `git status --porcelain -- apps/` → empty (no untracked files under `apps/` either). Zero backend,
  zero frontend changes, tracked or untracked.
- `git diff a9b3835... --stat` on the excluded paths shows only harness/measurement bookkeeping:
  `reports/goal-session-ops-hardening-index.html`, `reports/goal-session-ops-hardening-retro.md`,
  `reports/perf-budgets.md`, and `runs/goal-session-ops-hardening/*` state files. No lockfile changed.
- New untracked artifacts this iteration: `docs/handoffs/goal-ops-hardening-iter-21-dev.md`,
  `docs/phases/goal-ops-hardening-iter-21.md`, `reports/phase-goal-ops-hardening-iter-21-regression-replay-results.md`,
  `reports/qa/goal-ops-hardening-iter-21-evidence/{J-01,J-03,J-05}-verify.png`,
  `reports/reviews/goal-ops-hardening-iter-21-review.md`, and
  `runs/goal-ops-hardening-iter-21/{operator-tc13-tc14-evidence.md,status.json,tc13-backtest-poll.csv}` —
  all handoff/report/evidence artifacts, none of them product source.
- No `reports/phase-goal-ops-hardening-iter-21-ui-surface-map.md` exists — consistent with the agent
  instructions' no-op clause for an iteration with no frontend change.
- The dev handoff (`docs/handoffs/goal-ops-hardening-iter-21-dev.md`) independently states "Both empty.
  Zero files under `apps/backend/` or `apps/frontend/` changed, staged, or left untracked," and the
  reviewer's PASS verdict (`reports/reviews/goal-ops-hardening-iter-21-review.md`) confirms the same —
  both agree with my own independent `git` check above.
- `runs/goal-session-ops-hardening/state/blueprint.md`'s own iter-21 narrative paragraph states: "ships
  NO new Data Contract value, NO new computing module, and NO Information Architecture change."

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Regime score, market phase, realized forward-returns (`evidence_status`/`evidence_by_horizon`/`evidence_generated_at`/`evidence_asof`) | OK — re-measured/re-confirmed only, no new producer | `app.engine.forward_testing` is untouched (`git diff --stat -- apps/backend` empty). TC-13's stress proof (`reports/perf-budgets.md` §"Post-STALL owner-authorized measurements", 0/4096 breaches, max 429 ms) and this iteration's forthcoming browser capture both read the SAME existing `GET /api/backtest` / MCP `query_backtest` endpoints via the SAME unchanged resolver (`resolved_forward_aggregate_evidence`) — no second producer, no client-side recompute. |
| Job history & per-date exclusion reasons (interrupted-run checkpoint) | OK — re-measured only, no new producer | TC-14's operator evidence (`runs/goal-ops-hardening-iter-21/operator-tc13-tc14-evidence.md`: `kill -9` → restart → `ok/ready`; wide backfill checkpointed to `dates_done 1366/2904`, `kill -9` mid-run, `status: interrupted` with checkpoint preserved) reads the SAME already-registered `_checkpoint_run_record`/`_run_detail()` mechanism (`data_manager.py`, unchanged since iter-9) via the SAME `GET /api/data` / `GET /api/data/jobs/{job_id}` endpoints. No second derivation. |
| Page performance budgets (measurement artifact) | OK — same single artifact | `reports/perf-budgets.md` gains the "Post-STALL owner-authorized measurements — TC-13 + TC-14" section only; `blueprint.md`'s Notes cell for this row gets one added sentence pointing to it. Same file as every prior iteration (iter-2/3/5/6/7/8/11/12/14/15) — no second budgets artifact created. This row's own contract is `N/A — a measurement artifact, not a served runtime value`, so it cannot itself be duplicated as a *displayed* value. |
| Golden-replay regression evidence (J-01/J-03/J-05) | OK — reads existing pages, no new value | `reports/phase-goal-ops-hardening-iter-21-regression-replay-results.md`: 3/3 PASS, evidence at `reports/qa/goal-ops-hardening-iter-21-evidence/{J-01,J-03,J-05}-verify.png`. These replay the SAME `/data` / `/scanner-runs`-class flows against their existing canonical endpoints; no new page or endpoint involved. |

No new function, service, or endpoint was added anywhere (`git diff --stat -- apps/` is empty), so there is
no candidate for duplicate computation or non-canonical source. No new displayed value/entity appears
(the spec's own "New information displayed" field states "None," independently confirmed by the empty
frontend diff — nothing new can be rendered to a user this iteration).

## Information Architecture check

No new page, route, or nav-reachable feature this iteration — confirmed three ways: (1) the iteration
spec's own "UI surface changes: None" / "Blueprint conformance: No new surfaces" fields; (2) zero files
under `apps/frontend/` appear in the diff (`sidebar.tsx` untouched); (3) no ui-surface-map artifact exists
to claim otherwise.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/backtest` (J-08's existing home, exercised by TC-1/TC-2's forthcoming browser confirmation) | OK | `apps/frontend/components/sidebar.tsx` not in the diff; blueprint's Feature/journey-homes table already lists `/backtest` + MCP `query_backtest` as J-08's canonical, unchanged home. No new panel, no parallel shell. |
| `/data`, `/scanner-runs` (J-01/J-03/J-05 golden-replay surfaces) | OK | Same — pre-existing nav entries, no route/component change this iteration. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Closes the iter-20 coherence advisory — correctly NOT applied, with a verified reason.** iter-20's
  `coherence.md` flagged `apps/backend/app/mcp/tools.py:38`'s `forward_aggregates_ingest_cached` import as
  a dangling/unused import worth a future lint pass. This iteration's dev handoff investigated it (not
  merely re-asserted the claim) and I independently re-verified both findings by direct grep against the
  current tree:
  - The identical unused-import shape also exists at `apps/backend/app/api/backtest.py:75` (not named by
    the iter-20 advisory) — confirmed, both imports have zero call sites in their own file today (both
    files now reach the historical-compute path only via `ensure_historical_forward_aggregates_dispatched`).
  - Both imports are load-bearing `monkeypatch.setattr` targets with pytest's default `raising=True` in
    four tests in `apps/backend/tests/test_forward_testing_serving_split.py` — confirmed at the exact cited
    lines: `test_backtest_route_is_latest_never_reaches_ingest_or_compute` (592, `backtest_module`),
    `test_backtest_route_is_latest_not_yet_computed_is_honest_200` (621, `backtest_module`),
    `test_query_backtest_mcp_tool_is_latest_never_reaches_ingest_or_compute` (657, `tools_module`),
    `test_query_backtest_mcp_tool_not_yet_computed_mirrors_endpoint` (680, `tools_module`). Removing either
    import would raise `AttributeError` at each of these four `monkeypatch.setattr` calls, not a safe no-op.
  The iter-20 advisory is therefore correctly left un-applied this iteration — this is the right call, not
  a new coherence gap. No action needed from the next iteration on this specific point.
- **New, genuinely non-blocking finding surfaced (not a coherence violation, not actioned this iteration):**
  the dev handoff notes that post iter-20's dispatch refactor, these same four monkeypatches no longer trap
  the live code path they were originally written to guard (the historical branch's actual compute call now
  resolves through `app.engine.forward_testing`'s own module-local name, a different binding from
  `backtest_module`'s / `tools_module`'s copy). This is a test-coverage quality observation, not a Data
  Contract or Information Architecture defect — no second producer or endpoint is implied either way. Worth
  a future, properly-scoped test-hardening iteration (retarget the monkeypatch, only then is removing the
  now-genuinely-dead imports safe), consistent with how the dev handoff itself frames it.
- No inconsistent labeling, no cross-page formatting drift, and no unregistered-but-new value were found —
  there is no UI surface changed this iteration for any of Part C's drift signals to apply to.
