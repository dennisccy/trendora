# Iteration 32 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-32
**Date:** 2026-07-29
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

Backend-only, no-frontend iteration (`Frontend Present: no`). It restructures `compute_forward_
aggregates`'s internal accumulation (`stock_obs`, the last unbounded per-observation accumulator, is
replaced with bounded per-group/per-run/per-ticker accumulators — `_ExactMeanAcc`, `_GroupAcc`,
`_ControlGroupBuilder`, `_AttributionAccumulator`) without changing the function's public contract, its
callers, or any served value. No `apps/frontend/` file is touched (confirmed via `git diff --stat` and
`reports/phase-goal-ops-hardening-iter-32-ui-surface-map.md`). This is exactly the shape of change the
Data Contract exists to keep safe — internals may move as long as the canonical producer and its
endpoints stay singular and the output stays byte-identical — and the iteration, plus the audit pass
that followed it, went further than usual to prove that byte-identity independently.

## Data Contract check

The touched value is the blueprint's "Regime score, market phase, realized forward-returns" row
(`runs/goal-session-ops-hardening/state/blueprint.md:345`), whose registered canonical module is
`app.engine.forward_testing` (specifically `compute_forward_aggregates`) and whose registered serving
endpoints are `GET /api/backtest` and MCP `query_backtest`.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Forward-aggregate evidence (`by_bucket`/`by_setup`/`by_regime`/`by_vcp`/`control_group`/`attribution`/`overall`/`excess`) | OK | `apps/backend/app/engine/forward_testing.py:1154-1372` — same function, same three call sites (`GET /api/backtest`, MCP `query_backtest`, ingest finalize warm) unchanged; no second producer, no second endpoint introduced. |
| `_attribution_slices` signature lift `(stock_obs, cfg)` → `(acc: _AttributionAccumulator, cfg)` | OK (authorized) | `apps/backend/app/engine/forward_testing.py:351-388`; spec explicitly authorizes this ("frozen ... signature is lifted ON PURPOSE", `docs/phases/goal-ops-hardening-iter-32.md` IN SCOPE bullet 4); `compute_run_scorecard`'s own separate per-run `stock_obs` stays byte-unchanged and reaches the same function only through the new convenience constructor (`forward_testing.py:2120-2128`, TC-7). |
| Byte-identity of the restructured output vs. the pre-change reference | OK, independently verified | `apps/backend/tests/test_forward_testing_aggregates_streaming.py:66-110,225` — the audit (`docs/handoffs/goal-ops-hardening-iter-32-audit.md`, finding T2) caught that the developer's first version of the oracle called the *new* `_attribution_slices` on both sides of the comparison (self-comparison, blind to a real attribution defect) and fixed it by pinning the verbatim pre-iter-32 `_per_stock_attribution`/`_attribution_slices` bodies as an independent `_reference_*` pair. Post-fix, a mutation probe (swapped contributors/detractors) is caught (39 failed / 8 passed) where it previously passed 47/47. The audit additionally re-derived byte-identity at live scale (SHA-256 match on a real cached `2026-07-21` horizon-20 payload, 771,129 observations) — not just on the fixture. |

No new displayed value or entity is introduced (spec: "New information displayed: None"; confirmed —
the only new content anywhere is an engineering measurement section in `reports/perf-budgets.md`, which
the blueprint's Data Contract already carries as "N/A — a measurement artifact, not a served runtime
value" at row `blueprint.md:352`, same file, no second artifact). No duplicate computation and no
non-canonical source were found in the diff.

## Information Architecture check

No new page, route, or nav change. `apps/frontend/` is untouched (`git diff --stat` against this
iteration's snapshot SHA shows zero frontend files; `reports/phase-goal-ops-hardening-iter-32-ui-surface-map.md`
independently confirms "No UI surfaces affected"). J-07 keeps its existing IA home (global readiness
badge + `/backtest`, per `blueprint.md`'s Feature/journey homes table) — nothing to check for a new
feature this iteration.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route this iteration) | OK | n/a — `apps/frontend` diff is empty |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `runs/goal-session-ops-hardening/journey-scripts/J-07.json` (a test-harness golden-replay asset, not
  product code) was rewritten this iteration: its two steps now hit `/backtest` twice, asserting
  "Forward-tested evidence" and a specific `n=8869` count, replacing the prior version's `/evidence`
  (`-7.48%`) and `/data` (`drawdown expectations`) checks. This actually points the script at J-07's
  IA-registered home (`/backtest`) rather than away from it, so it is a coherence *improvement*, not a
  drift — but neither the dev handoff nor the audit report mentions or justifies this specific edit, and
  the file has been rewritten with different page targets at least twice before (iter-29 moved it from
  `/backtest`+`/`+`/data` to `/evidence`+`/data`). Recommend the next iteration that touches J-07's
  journey script add one sentence of rationale/provenance for the asserted values (e.g. where `n=8869`
  was read from) so this churn stops being silent.
- Audit finding B2 (`docs/handoffs/goal-ops-hardening-iter-32-audit.md`): the module docstring at
  `apps/backend/app/engine/forward_testing.py:1172-1174` and the dev handoff both still claim
  `_group_means`/`_group_mdd` are "used by `compute_run_scorecard`'s own already-small per-run
  `stock_obs`" — no longer true after this iteration (that path now goes through
  `_AttributionAccumulator.from_observations`; `_group_means`/`_group_mdd` are reachable only from the
  test oracle). Pure documentation drift with no Data Contract consequence — both functions are
  intentionally kept as the byte-identity oracle's independent reference — but worth a one-line docstring
  fix in a future lean pass so a "dead code" sweep doesn't delete the oracle's reference implementation.
- Audit finding B3: one wrong boot-banner timestamp in the new `reports/perf-budgets.md` section
  (`4032-4033`, off by exactly one hour vs. the log line it cites) — cosmetic, no data-contract or IA
  impact.
