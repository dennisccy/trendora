# goal-mcp-loop-iter-8 Dev Handoff

**Phase:** goal-mcp-loop-iter-8
**Date:** 2026-06-30
**Agent:** developer
**Status:** complete

## What Was Built

J-06 — surface the **vcp_contraction top-decile (D10 @ horizon-20)** certified out-of-sample edge as a
"Proven" evidence badge on the Research factor lab and as a new claim row on `/evidence`, both reading the
canonical `GET /api/evidence` payload verbatim. The Evidence Claim was already certified PASS by the
post-decompose gate (4th ledger entry; holdout edge **+3.33%**, p **0.01149** < required_p 0.0125).

- **Read-side cohort-selector matcher** `resolveCohortEvidence(cohort, claims)` in `lib/evidence.ts` — the
  signal-less successor to `resolveEvidenceStatus`. Scans the served `claims[]` for a `proven` (PASS) entry
  whose cohort selectors match the queried factor cohort on `factor` + `slice_kind` + `decile` + `horizon` +
  `direction`. Reads `entry.proven` verbatim; never recomputes. Fail-safe: no match / matched-but-non-PASS
  (the ma_stack FAIL row) / empty/null list → `{ proven:false, label:"Not yet proven", href:null }`.
- **Cohort anchor helpers** `cohortClaimId(cohort)` / `cohortEvidenceAnchor(cohort)` — a stable,
  collision-free `/evidence#factor-<factor>-d<decile>-h<horizon>` anchor derived from a factor cohort's
  selectors.
- **Shared `claimAnchorId(claim)`** — the single `/evidence` row-id contract both the `ClaimRow` and every
  "Proven" badge agree on: a score-column claim (carries `signal`) keeps its `signal-${signal}` id; a
  signal-less factor cohort derives its `cohortClaimId`; any other row (event-study) has no id. This is what
  makes every deep-link land (a score-column factor like leadership_score in the factor lab links to its
  real `signal-…` row, NOT a cohort anchor its row never carries).
- **`claimSurface` `kind === "factor"` branch** — a signal-less factor cohort gets an honest title
  (`"vcp_contraction — top decile (D10)"`, derived from selectors — never "Unmapped signal"), an honest
  historical-evidence subtitle (`"Out-of-sample edge — factor top decile"` — never a buy/return promise), and
  a "Backs: Research factor lab →" linkback to `/research/factor-lab`. The score-signal branch and the
  event-study branch are byte-identical (J-04/J-05 unchanged — unit-asserted).
- **`/evidence` `ClaimRow` cohort anchor** — the row `id` now flows through the shared `claimAnchorId`:
  signal-less factor cohorts (vcp_contraction, ma_stack) get a `factor-…` anchor; score rows keep
  `signal-…`; the event-study row stays `undefined`.
- **Factor-lab evidence badge** — `FactorLabPage` fetches the canonical payload via the existing
  `fetchEvidence()` client (fail-safe: empty on error → all badges "Not yet proven", no link) and renders a
  per-factor top-decile (D`deciles_count` @ `default_horizon`) `FactorEvidenceBadge` in a new "Evidence
  (D10 · 20d)" column. vcp_contraction reads "Proven" (deep-links to its ledger row); every unbacked factor
  (incl. ma_stack's FAIL) reads "Not yet proven" (no link). The "Proven" `<Link>` calls
  `stopPropagation()` on click + key events so a click deep-links rather than toggling the click-to-expand
  summary row (the iter-5 nested-interactive hazard).
- **Backend confirming test** (TEST-ONLY, zero `app/**` change) — a `build_evidence_payload` assertion over
  the 4-entry ledger.

### Honest design note (general, evidence-first matcher)
The matcher is general: any factor whose top-decile cohort has a PASS certified-claim reads "Proven" in the
factor lab. In practice that is **vcp_contraction** (the new claim) **and leadership_score** (the 1st ledger
entry — a score-column factor that is also a factor-lab row). Showing leadership_score "Proven" in the factor
lab is accurate (it IS certified) and consistent with goal.md Key Capability 1; its badge deep-links to its
real `signal-leadership_score` ledger row. No uncertified cohort reads "Proven" (ma_stack FAIL →
"Not yet proven"). This was NOT special-cased to vcp_contraction-only because suppressing a true "Proven"
status would be dishonest (anti-goal-adjacent). `/stocks` inline score badges are unaffected — they still key
on `proven_signals` (= `{leadership_score}`); vcp_contraction adds no signal.

## Files Changed

- `apps/frontend/lib/evidence.ts` — added `FactorCohort`, `factorCohortFromClaim`, `cohortClaimId`,
  `cohortEvidenceAnchor`, `claimAnchorId`, `CohortEvidenceStatus`, `resolveCohortEvidence`, and the
  `claimSurface` factor branch. Kept `resolveEvidenceStatus` + score/event-study branches byte-identical.
- `apps/frontend/lib/evidence.test.ts` — added 10 cases (cohort match/mismatch/non-PASS/empty, score-column
  deep-link, `claimAnchorId`, anchor stability/collision-free, `factorCohortFromClaim`, the factor
  `claimSurface` branch, and a score+event-study no-regression assertion).
- `apps/frontend/app/evidence/page.tsx` — `ClaimRow` derives its anchor `id` from the shared `claimAnchorId`.
- `apps/frontend/app/research/_labs.tsx` — `FactorLabPage` fetches evidence (fail-safe) and threads
  `claims[]`; `FactorsTable` adds the Evidence column (+ updates `colSpan`); new `FactorEvidenceBadge`
  component on each factor's top-decile summary row.
- `apps/backend/tests/test_evidence.py` — added `_vcp_contraction_pass_entry` / `_ma_stack_fail_entry`
  builders + `test_build_payload_vcp_contraction_factor_cohort_post_certification` (the 4-entry assertion).

No change under `apps/backend/app/**`; no change to the three scores, the engines, the referee, or
`GET /api/evidence`'s shape. `app/research/factor-lab/page.tsx` is unchanged (thin re-export).

## Tests Run

- Frontend unit: `cd apps/frontend && npx tsx lib/evidence.test.ts` → **25 passed** (15 prior + 10 new).
- Frontend types: `cd apps/frontend && npx tsc --noEmit` → clean (exit 0).
- Frontend build: `npx next build` → compiled successfully; `/research/factor-lab` and `/evidence` routes built.
- Backend unit: `cd apps/backend && .venv/bin/python -m pytest tests/test_evidence.py -q` → **11 passed**
  (10 prior + 1 new).
- Backend regression (this iteration's footprint): `pytest tests/test_evidence.py tests/test_api_evidence.py
  tests/test_factor_lab_all.py tests/test_referee.py tests/test_api_research.py -q` → **130 passed in 278s**
  — covers the evidence resolver, the `/api/evidence` contract, the factor-lab payload, the (untouched)
  referee, and the research API.
- Backend full suite: `pytest tests/ --collect-only` → **1267 tests collect cleanly** (my test-only change
  adds no collection errors). The full serial run takes ~45 min (130 tests = 4m38s), so it exceeds the
  harness timeout caps (SIGTERM/143 = time cap, NOT a test failure); the 130-test footprint run above is the
  meaningful regression signal for a zero-app-code change.
- Live integration: started backend (port 8255) + frontend (port 3255); `GET /api/evidence` returns 4 claims
  with `proven_signals == {leadership_score}` and the vcp_contraction row `proven:true / signal:null /
  holdout +0.0333 / p 0.01149 / register 2026-06-30`.
- Live browser (Chrome): `/research/factor-lab` vcp_contraction badge reads "Proven" → clicking deep-links to
  `/evidence#factor-vcp_contraction-d10-h20`; the row renders the honest title, subtitle, hypothesis chips,
  "PASS · holdout edge +3.33%", and "Backs: Research factor lab →". Regression: ma_stack "Not yet proven";
  `/evidence` leadership row keeps `signal-leadership_score` + "Stocks leaderboard" linkback; Breakout-watch
  keeps "Regime: Risk-on" + event-study linkback; `/stocks` 360 score badges, only leadership "Proven",
  no vcp_contraction mention.

## Known Issues

- The full backend suite (`pytest tests/`, 1267 tests) takes ~45 min serially and exceeds the harness
  timeout caps (the runs SIGTERM'd at the time cap, NOT on a test failure; the suite collects all 1267
  cleanly). The meaningful regression for this test-only change is the 130-test footprint run above
  (130/130 pass). To run the full suite, do it standalone with a long timeout and no concurrent services,
  ideally with `pytest-xdist` (`pip install pytest-xdist && pytest tests/ -n auto`) — xdist is not currently
  installed.
- Services were started for verification (backend `start-backend.sh` → :8255, frontend `start-frontend.sh`
  → :3255, both port-offset by the repo-path hash). They are stopped at the end of this run; QA should
  re-start via the standard scripts. `start-frontend.sh` serves a pre-built bundle and only rebuilds on a
  stamp mismatch — the fresh build for this iteration is stamped.
- The factor lab's top-decile cohort is built from `data.deciles_count` (top decile = D10) and
  `data.default_horizon` (20) — config-driven, no magic numbers. If config ever changes the default horizon
  away from the certified claim's horizon (20), the vcp_contraction badge would read "Not yet proven" until a
  claim is certified at the new default horizon (correct fail-safe, but worth noting).
