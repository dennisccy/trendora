# Iteration 25 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-25
**Date:** 2026-07-26
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

This iteration's only touched Data Contract row is "Backend readiness / boot phase + preflight
verdict" (`app.engine.readiness.compute_readiness` / `GET /api/health`), and it is touched by copy
only, never by computation.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `background_compute` (active windows / recent outcomes) | OK | Producer/endpoint unchanged. `git diff --stat` against snapshot `e14a39f2` shows zero touches to `apps/backend/app/engine/readiness.py`, `apps/backend/app/engine/forward_testing.py`, or `apps/backend/app/api/health.py` — confirmed directly (only `README.md`, `apps/backend/tests/test_health.py`, `apps/backend/tests/test_readiness.py`, `apps/frontend/app/data/page.tsx` changed against tracked files, plus two new frontend `lib/` files). |
| Readiness `state` (`"unavailable"` on poll failure) | OK — reformat, not recomputation | New pure function `apps/frontend/lib/background-compute-panel-branch.ts:28-41` (`resolveBackgroundComputePanelBranch`) takes the SAME `state`/`backgroundCompute` values already returned by `useReadiness()` (`apps/frontend/components/readiness-provider.tsx:32-33`, populated from the one `GET /api/health` poll, `unavailable` set at `readiness-provider.tsx:84`) and only decides which of three existing-signal-derived copy branches (`"unknown"`/`"idle"`/`"active"`) to render. No new fetch, no client-side recomputation of the value itself — this is the skill's explicit "re-format is fine" carve-out (deciding display text from an already-canonical signal), not a second producer. |
| Two rewritten background-compute-registry tests | OK — test-only | `apps/backend/tests/test_health.py` (diff around old line 113) and `apps/backend/tests/test_readiness.py` (diff around old line 292) both add a local `_background_compute_identity()` helper that strips the read-time-volatile `elapsed_ms` field before comparing two live reads. No production code path touched; confirmed by reading both diff hunks in full. |
| Demo manifest (`reports/goal-session-ops-hardening-demo.json`) | OK — not a Data Contract row | 4 new `n=13..16`, `"journey": "J-09"`, `"new": true`, `"verified": true` entries appended after the existing 12; diff is purely additive (steps 1-12 byte-unchanged, confirmed by reading the full hunk — every changed line is a `+`). Matches the iter-18/23 precedent recorded in `blueprint.md`: "a log line is not a served/displayed value" — a demo/QA artifact is out of Data Contract scope by design. |

No new displayed value/entity is introduced this iteration (spec's own "New information displayed" /
"New user-facing capability" fields both say "None" — verified true against the diff: the only
user-visible product-code change is the new copy sentence in `BackgroundComputePanel`, which reads an
already-registered signal).

## Information Architecture check

No new page/route/feature this iteration — spec, blueprint iter-25 comment block, and the diff all
agree.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/data` `BackgroundComputePanel` (new copy branch) | OK | Same component, same file (`apps/frontend/app/data/page.tsx:3593-3644`), same canonical home the blueprint's Feature/journey-homes table already assigns to J-09 (`(global) / Data Manager`). No new route added; `apps/frontend/components/sidebar.tsx` was not touched (absent from the diff/stat entirely) — no nav change was needed or made. |

No `ui-surface-map` report exists for this lean iteration (expected — the agent instructions note it
is present for "full and most lean iterations," not all); surfaces were derived directly from the
diff and spec instead, per the fallback rule.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None specific to this iteration's product/test diff. (The reviewer's own NOTE — that the targeted
  pytest reruns for the two rewritten tests, plus the 5x TC-5 repetition, had not finished within the
  review session due to the project's known 1h+ `loaded_engine` fixture cost — is a testing/QA
  completeness concern, not a coherence-drift concern; it does not bear on data-contract or
  navigation structure and is left for QA/the evaluator to resolve.)
- `git status` additionally shows an unstaged modification to
  `runs/goal-session-mcp-loop/state/preflight-verdict-history.jsonl` (a different, already-archived
  goal session's state file, plausibly touched by the developer's live backend-restart repro for
  TC-3). This is harness/session bookkeeping under `runs/*`, explicitly out of this audit's scope per
  the invocation prompt's exclusion list — noted here only so it isn't mistaken for an untouched
  file, not as a coherence finding.
