# Phase goal-ops-hardening-iter-31 — UX Regression Review

**Date:** 2026-07-29

**Verdict:** UX-REGRESSION-PASS

Backend-only phase. No UI regression review required.

---

## Basis for the backend-only classification (verified, not just cited)

The phase spec states `Frontend Present: no`. I did not take that on faith — I checked the
actual diff against `HEAD`:

```
git diff --stat -- apps/backend/app/engine/research.py apps/backend/app/config.py config.yaml \
  apps/backend/tests/test_factor_lab_all.py apps/backend/tests/test_research_streaming.py
  5 files changed, 584 insertions(+), 86 deletions(-)

git diff --stat -- apps/frontend
  (empty — zero frontend files touched)
```

All five changed files are backend engine/config/test files. No `.tsx`, `.ts`, or CSS file
under `apps/frontend/` differs from `HEAD`. (Note: the session's working tree also carries
uncommitted `apps/frontend/lib/evidence.ts` / `evidence.test.ts` / `app/evidence/page.tsx`
modifications visible in a raw `git status`, but those are iter-29's frontend work — already
merged into commit `4de46ad8` per `docs/handoffs/goal-ops-hardening-iter-29-dev.md`'s Files
Changed list — and are unrelated to this iteration's diff.)

`user-visible-changes.md`, `ui-surface-map.md`, and the developer's own
`implementation-summary.md` (Backend-Only Items: "None... there is no new capability requiring
UI wiring") all independently agree: this iteration fixes a crash (`MemoryError` on
`/research/factor-lab?all=true`) and adds a concurrency guard, both invisible to the UI layer
because the page's route, component, label, and layout are unchanged and the response payload
is contractually byte-identical per `(factor, horizon, decile)` tuple to the pre-fix reference.

## New Capability Discoverability

No new capability was added. The change is availability hardening for an *existing* route
(`/research/factor-lab`) that previously 500'd on the all-factors view. There is nothing new
to place in navigation.

## Regression Risk

Zero regression surface, by construction — no frontend file changed, so no shared component
(nav bar, layout shell, data-fetch hook, chart renderer) used by any prior-phase feature was
touched. The only two consumers of the restructured backend function
(`_all_factor_observations_by_horizon` → `compute_factor_lab_all` → `factor_lab_all_cached`)
are `GET /research/factor-lab?all=true` and the MCP tool in `app.mcp.tools`; neither route nor
tool signature changed.

Beyond the diff-based argument, this was also checked empirically. QA's merged
`reports/phase-goal-ops-hardening-iter-31-ui-test-results.md` (browser-qa + deterministic
replay, verdict PASS, 9/9 journeys) includes a live navigation to the exact page this
iteration touches:

> UT-FL-01 — Factor Lab all-factors view loads without MemoryError: "Page loaded via real
> browser navigation; extracted page text shows all 11 catalog factors each with real
> rank-IC, N=771129 (or the factor's own real N), risk-adjusted, and FWD/MDD values populated
> for all 5 horizons (1d/5d/10d/20d/60d); console capture showed only a React-DevTools info
> line, zero errors; backend log shows 0 MemoryError since this run's boot banner."

All six required-still-passing journeys (J-01, J-03, J-04, J-05, J-08, J-09) and both target
journeys (J-06, J-07) show PASS in the same report via golden-script replay or live navigation,
with zero FAIL rows. This directly confirms no prior-phase user journey regressed as a side
effect of the backend restructuring — the previously-crashing page now renders the same
content that was always intended, and every other journey's golden replay is unaffected.

No coherence-auditor artifact exists yet for iter-31 (`runs/goal-session-ops-hardening/iter-31/
coherence.md` is absent) — nothing to cite there, and nothing in the QA report or ui-test-
results contradicts it, so there is no "audit contradiction" to flag.

## UI vs Backend Parity

| Backend capability (this iteration) | UI exposure |
|---|---|
| Bounded memory representation for `_all_factor_observations_by_horizon`'s return value | N/A — internal implementation detail, correctly not surfaced |
| Single-flight de-dup guard on `factor_lab_all_cached` (concurrent MISS → 1 compute) | N/A — internal concurrency mechanism, correctly not surfaced |
| New config knob `research.factor_pool_max_observations` (safety-tripwire log warning) | N/A — operator/log-only signal, no user-facing meaning |
| `/research/factor-lab?all=true` now returns HTTP 200 instead of 500 | Fully surfaced — the existing page simply renders instead of crashing; verified live (UT-FL-01) |

No gap: the only end-user-observable effect (a page that used to 500 now loads) is already
what the existing Factor Lab UI shows, with no new information, action, or affordance implied
by the phase spec that would need new UI.

## Flags

### Hidden Capabilities
- None.

### Undiscoverable Capabilities
- None.

### Potential Regressions
- None identified. Zero frontend diff; all prior-phase journeys (J-01, J-03, J-04, J-05, J-06,
  J-07, J-08, J-09) show PASS in this iteration's merged UI test results with live/replay
  evidence.

### Visual Consistency
- Not applicable — no page, component, or style was added or modified this iteration.

## Recommendation

No action required.
