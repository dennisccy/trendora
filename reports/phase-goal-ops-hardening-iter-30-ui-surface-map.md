# Phase goal-ops-hardening-iter-30 — UI Surface Map

**Status:** N/A — Backend-only phase (Frontend Present: no)

No UI surfaces affected.

## Basis for this classification

All five changed/created files this iteration classify as **backend-internal** or **config** per
`.claude/skills/diff-to-ui-impact.md` — none touch a route, page, component, form, chart, modal, table, or
CSS, and none introduce or change an API contract the frontend consumes:

| File | Classification | Why |
|------|----------------|-----|
| `apps/backend/app/engine/forward_testing.py` | backend-internal | Rewrites `compute_forward_aggregates`'s internal accumulation (adds `_forward_agg_runs_with_fr`, `_forward_agg_slice_map`, chunked walk) to bound RAM. Same public signature, same call sites, byte-identical output payload — an implementation detail invisible to any consumer. |
| `apps/backend/app/config.py` | config | Adds `WalkForwardCfg.forward_agg_run_chunk` (int, default 100, boot-validated `>= 1`). A server-side tuning knob with no UI-exposed setting or display. |
| `config.yaml` | config | Sets `walk_forward.forward_agg_run_chunk: 100` with a measurement comment. Not read or rendered by the frontend. |
| `apps/backend/tests/test_forward_testing_aggregates_streaming.py` | backend-internal (test) | Unit/fixture tests only; no UI coupling. |
| `reports/perf-budgets.md` | backend-internal (measurement artifact) | A committed report file documenting curl-based latency/PASS-WARN scoring; not served to or rendered by any page. |

`compute_forward_aggregates` already served `GET /api/backtest` and MCP `query_backtest` before this
iteration; those endpoints and the pages that consume them (`/backtest`) are unchanged in shape, and this
iteration's own byte-identity tests (TC-2) exist specifically to prove the response payload is unchanged.
Per the diff-to-ui-impact skill, an unchanged backend-api response with an unchanged existing frontend
consumer produces no new surface-map row — there is nothing new for the UI to expose and nothing existing
to re-describe.

| Route/Page | Component/Element | Change Type | Why Changed | What to Test |
|-----------|------------------|------------|-------------|--------------|
| N/A | N/A | N/A | No UI surface changed this iteration | N/A |

No regression risk to `/backtest` or `/research/factor-lab` display is introduced by this iteration's
diff (both pages' contracts are asserted unchanged by the byte-identity tests); any regression check on
those pages belongs to QA/browser-qa-agent's TC-5 spot-check, not to a new surface-map entry, since no
code in this iteration touches `research.py` or any frontend file.
