# Iteration 20 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-20
**Date:** 2026-07-24
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration

Diffed against snapshot `2a29547ef71c918973ce52c408eaa6e19a5c6494` (noise-excluded). Exactly 7 files
changed, all backend/test except one frontend page:

```
apps/backend/app/api/backtest.py                            |  81 ++++---
apps/backend/app/engine/forward_testing.py                  | 110 +++++++++   (0 deletions)
apps/backend/app/mcp/tools.py                                |  25 +-
apps/backend/tests/test_api_backtest.py                      |  24 +-
apps/backend/tests/test_forward_testing_concurrency.py       | 265 +++++++++++++++++++++ (new tests)
apps/backend/tests/test_forward_testing_serving_split.py     | 113 ++++++---
apps/frontend/app/backtest/page.tsx                          |  52 ++--
```

No sidebar/nav/router/layout file appears in the diff (verified with a scoped `--stat` against
`*sidebar*`/`*nav*`/`*router*`/`*layout*` — empty). No new frontend route file. No
`blueprint.reapproval-requested` flag exists on disk. The excluded-path stat shows only harness
bookkeeping (`runs/*`, `reports/*`, `docs/handoffs/*`) — no lockfile/dependency-manifest changes.

## Data Contract check

Registered row touched: **"Regime score, market phase, realized forward-returns"**
(`app.engine.forward_testing` → `GET /api/backtest` + MCP `query_backtest`).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Forward-aggregate evidence (`evidence_status`/`evidence_by_horizon`/`evidence_generated_at`/`evidence_asof`) | OK | `forward_testing.py:1235` `ensure_historical_forward_aggregates_dispatched` and its worker `forward_testing.py:1205` `_run_historical_forward_aggregates_dispatch` are orchestration only — the worker's sole compute call is the pre-existing `forward_aggregates_ingest_cached(session, h, cfg, as_of=as_of)` (inside the `for h in cfg.walk_forward.horizons` loop at the worker body), the exact same function that was previously called inline on the request thread. `compute_forward_aggregates` and `forward_aggregates_ingest_cached` are byte-unchanged — confirmed directly from the diff: `forward_testing.py` shows **110 insertions / 0 deletions**, i.e. every pre-existing line (both functions' bodies) is untouched, not merely "claimed" unchanged. |
| Same value, serving side | OK | Both callers still build the served payload from the SAME resolver read, never a second one: `backtest.py:186` `evidence = resolved_forward_aggregate_evidence(session, run.asof_date, cfg)` and `mcp/tools.py:291` (identical call). The new dispatch call (`backtest.py:211`, `mcp/tools.py:299`) is fire-and-forget — its return value is never read, `evidence` is not reassigned afterward in either file (confirmed by the diff: the old `evidence = resolved_forward_aggregate_evidence(...)` re-resolve line after the loop was deleted, not added-to). Both endpoints stay behaviorally identical (TC-6's parity intent). |
| New frontend surface for this value | OK | The only frontend change, `apps/frontend/app/backtest/page.tsx`, adds no new fetch. It branches existing display copy on the already-fetched `backtest.is_latest` field (`page.tsx:246`, `257`) — confirmed against `reports/phase-goal-ops-hardening-iter-20-ui-surface-map.md` ("no new API field, fetch, or component") and against the diff itself (no new `fetch`/`useQuery`/`useEffect` call added). Re-labeling for display only — rule 3 (re-format is fine), not a violation. |
| New displayed value/entity | N/A — none introduced | The iteration spec's "New information displayed" section states "None," and the `backtest.py` response-dict construction is untouched by this diff (only the docstring, the ensure-loop body, and the log-field's *meaning* changed — no new key added to the returned payload). `ensure_loop_ms` is repurposed in-place (same log-line field name, same log line) — it is an internal timing log, not a served/displayed API value, consistent with the iter-18 precedent already on record in the blueprint ("a log line is not a served/displayed value"). No unregistered-value WARN applies. |

No duplicate computation, no non-canonical source, no new unregistered displayed value.

## Information Architecture check

No new page/route/feature this iteration — the spec's own "UI surface changes" / "Blueprint
conformance" sections state "None new," and this was independently verified:

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/backtest` (J-06/J-07/J-08 existing home) | OK | `apps/frontend/components/sidebar.tsx` does not appear in the diff (confirmed via scoped `git diff --stat` against nav/sidebar/router/layout globs — empty output); the blueprint's Feature/journey-homes table already lists `/backtest` + MCP `query_backtest` as the canonical, unchanged home for J-06/J-07/J-08. The iteration's work (backend dispatch mechanism + a frontend copy branch) lives entirely inside that existing home — same route, same components (`RefreshingEvidenceBanner`, the `not_yet_computed` `EmptyState`), no new panel. |
| MCP `query_backtest` (sibling home) | OK | `apps/backend/app/mcp/tools.py` gained one new import and one call-site swap (`tools.py:37`, `299`) mirroring the HTTP endpoint identically — no new MCP tool registered, no new file. |

No hidden feature, no reachability regression, no duplicate home, no parallel shell.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Out-of-scope code-hygiene observation (not a coherence violation):** `apps/backend/app/mcp/tools.py:38`
  still imports `forward_aggregates_ingest_cached`, but the diff removed its only call site inside
  `query_backtest` (replaced by `ensure_historical_forward_aggregates_dispatched` at `tools.py:299`) —
  `grep` confirms no remaining use anywhere else in the file. This is a dangling/unused import (dead
  code), not a duplicate-computation or non-canonical-source problem — it doesn't create a second path to
  the value, it's simply orphaned. Flagging for the reviewer's or next iteration's lint pass; it does not
  affect this verdict.
- No inconsistent labeling, no cross-page formatting drift, and no unregistered-but-new value were found.
