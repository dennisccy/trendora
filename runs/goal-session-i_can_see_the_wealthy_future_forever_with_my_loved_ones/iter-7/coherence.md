**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-7 (J-51 / J-52)

Session: i_can_see_the_wealthy_future_forever_with_my_loved_ones
Iteration: 7
Snapshot SHA: 59d979c3371ff13d4cb2a48b5ad7dee3062ba178

## Files changed

- `apps/backend/app/api/research.py` — new `GET /api/research/samples` endpoint
- `apps/backend/app/engine/research.py` — extracted `_decile_member_slice` and `_combination_cohort_members` from existing inline code; both are still called verbatim from `compute_factor_lab` / `compute_factor_combination`
- `apps/backend/app/engine/samples.py` — new engine module `compute_samples` (SELECT-only)
- `apps/backend/tests/test_api_research.py` — new count-coherence + value-identity unit tests
- `apps/frontend/app/research/page.tsx` — `SampleSize` chips replaced by `SampleLink` links; no other change
- `apps/frontend/app/research/samples/page.tsx` — new page (new file)
- `apps/frontend/components/sample-link.tsx` — new component wrapping `SampleSize` as a link
- `apps/frontend/lib/api.ts` — new `fetchSamples` function + response type definitions
- `apps/frontend/lib/samples-link.ts` — new helper for building `/research/samples?…` hrefs

## Step 1 — Data Contract

The blueprint pre-registers the Research samples drill-down as:

> Computed read-only by `research:_factor_observations` / `_combination_observations` / `_event_study_members`; served by `GET /api/research/samples`.

**No duplicate computation found.** The new `apps/backend/app/engine/samples.py` imports and calls the SAME three builders directly from `app.engine.research` (line 47–54 of `samples.py`). It introduces no independent factor, return, or regime computation — only pure index arithmetic (`_decile_member_slice`) and set operations over already-assembled pools.

**No second membership rule.** The refactoring in `apps/backend/app/engine/research.py` extracted the combination-membership logic into `_combination_cohort_members` and the decile-slice logic into `_decile_member_slice`. Both helpers are:
  - Defined once in `research.py`.
  - Called from `compute_factor_combination` / `_deciles` (existing aggregates) and from `compute_samples` / `_factor_samples` / `_combination_samples` (new drill-down) — the same code path shared by both, which is the prescribed consolidation (blueprint invariant 13: "never a second membership rule").

**No non-canonical source.** `apps/frontend/lib/api.ts:fetchSamples` fetches exclusively from `GET /api/research/samples`. The page `apps/frontend/app/research/samples/page.tsx` calls only `fetchSamples` and re-formats stored values only — no client-side factor, return, or membership computation.

**No unregistered new values.** The per-observation fields (ticker, snapshot date, qualifying stored value, realized forward return) are all stored values passed through verbatim; no new derived metric is introduced.

## Step 2 — Information Architecture

**Blueprint registration:** `/research/samples` is pre-registered in the approved blueprint as "link-reached under Research" (tagged "[TARGET — iter-7 in flight]").

**Reachability check (static):**
- Sidebar (`apps/frontend/components/sidebar.tsx:37`) lists `/research` — 1 click from any page.
- Every `N=` chip on `/research` is now rendered as a `SampleLink` component that builds an href to `/research/samples?…`. From the sidebar click on "Research" (click 1), any `N=` chip drills into `/research/samples` (click 2). Reachable in exactly 2 clicks — within the ≤2 threshold.

**No parallel shell.** The new page `apps/frontend/app/research/samples/page.tsx` uses the same app-level layout (it lives under `app/research/` in the Next.js App Router, which inherits the root layout shell); it does not introduce its own sidebar or nav frame.

**No duplicate home.** There is no existing page for the research samples drill-down; this is the sole home for the new `/research/samples` surface.

## Step 3 — Subjective observations (advisory)

None. The page labels ("Research Samples — observation drill-down", cohort summary, survivorship banner) are consistent with the terminology used in the rest of the Research section.

## Summary

All Data Contract rules and Information Architecture rules pass. The iteration introduces no objective violation. The implementation correctly consolidates the single membership-derivation path and serves the new surface from the single registered endpoint.
