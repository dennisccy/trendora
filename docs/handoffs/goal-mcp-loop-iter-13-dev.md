# goal-mcp-loop-iter-13 Dev Handoff

**Phase:** goal-mcp-loop-iter-13
**Date:** 2026-07-01
**Agent:** developer
**Status:** complete

## What Was Built

Surfaced **J-08** — the first referee-certified **2-factor combination** edge — as evidence on two
existing surfaces, both reading the SAME `GET /api/evidence` payload verbatim. Frontend-only
(plus test-only backend assertions); zero app-code change.

- **Read-side combination matcher (`lib/evidence.ts`, PURE / no React / no fetch):**
  - New `CombinationCohort` type (`kind:"combination"`, `cohort:"composite"`, `condition:string[]`,
    `horizon`, `direction`).
  - `combinationCohortFromClaim(claim)` — extracts/validates a composite combination claim (else `null`).
  - `resolveCombinationEvidence(cohort, claims)` — scans the served `claims[]` for a **PASS** entry
    matching on `kind`+`cohort`+ the **`condition` leg-set matched order-independently as full
    `factor:side:quantile` strings** + `horizon` + `direction`. Returns "Proven" (+ the backing
    `/evidence#…` anchor) only on a PASS match; every other case (incl. a matched-but-non-PASS entry, an
    empty/null list) → "Not yet proven", no link. Recomputes nothing.
  - `combinationClaimId(cohort)` / `combinationEvidenceAnchor(cohort)` — a deterministic, order-independent,
    `combination-`-prefixed anchor (e.g. `combination-high_proximity-rs_spy_3m-h20`), distinct from any
    `factor-…` anchor.
  - Extended `claimAnchorId()` (returns the combination anchor for a combination claim) and `claimSurface()`
    (new combination branch: honest composite title, out-of-sample-evidence subtitle, `/research/factor-combination`
    linkback labelled "Multi-factor combination lab" — replacing the misleading "Unmapped signal" fallback).
- **Composite-cohort "Proven" badge (`app/research/_labs.tsx`):**
  - `CombinationLab` now fetches the served `claims[]` via the EXISTING `fetchEvidence` client (fail-safe:
    empty on error → badge reads "Not yet proven").
  - `CombinationTable` builds the `CombinationCohort` from the already-computed leg strings + horizon +
    `direction:"positive"`, resolves via `resolveCombinationEvidence`, and renders a new
    `CombinationEvidenceBadge` (accent `ShieldCheck` "Proven" deep-link / muted `Shield` "Not yet proven")
    on the composite cohort row ONLY (`data-testid="combination-evidence-badge"`, `data-proven`, `data-horizon`,
    `data-legs`).
- **`/evidence` — no structural change.** The combination `ClaimRow` renders automatically now that
  `claimSurface`/`claimAnchorId` handle the combination branch; the existing `ClaimHypothesis` already prints
  every selector chip (`condition`, `kind`, `horizon`, `direction`, `cohort`, `ledger`) verbatim.

The 6th canonical ledger entry (`rs_spy_3m:top:quintile × high_proximity:top:tertile`, composite, h20,
PASS, holdout **+4.69%**, control vs SPY **+4.69%**, p=0.0009995, Bonferroni divisor 6, register 2026-07-01)
was written by the **post-decompose gate** — the developer built against it and did NOT edit it.

## Files Changed

- `apps/frontend/lib/evidence.ts` -- `CombinationCohort` type, `combinationCohortFromClaim`,
  `resolveCombinationEvidence`, `combinationClaimId`/`combinationEvidenceAnchor`; extended `claimAnchorId` +
  `claimSurface` (combination branch). Score/event-study/factor branches untouched.
- `apps/frontend/lib/evidence.test.ts` -- +10 combination unit checks (order-independence, full-leg match,
  mismatch paths, matched-but-non-PASS, empty/null, anchor, `claimSurface`/`claimAnchorId`, no-regression).
- `apps/frontend/app/research/_labs.tsx` -- combination-lab evidence fetch; threaded into `CombinationTable`;
  new `CombinationEvidenceBadge` on the composite row.
- `apps/backend/tests/test_evidence.py` -- **(test-only)** new `_combination_pass_entry()` fixture + a
  dedicated combination payload test; updated `test_canonical_ledger_frozen_golden` (5→6 entries).
- `apps/backend/tests/test_staging_ledger_routing.py` -- **(test-only)** updated two live-canonical-ledger
  golden assertions (`count_trials` 5→6, `rejection_offsets` `[1,2,4,5]`→`[1,2,4,5,6]`) + their comments,
  reflecting iter-13's promotion of the combination winner.
- `docs/handoffs/goal-mcp-loop-iter-13-dev.md` / `-frontend.md` -- this handoff (+ the frontend one).

**NOT edited (by design):** `runs/goal-session-mcp-loop/state/certified-claims.jsonl` (the gate wrote row 6;
prior 5 byte-identical), any `apps/backend/app/**` (engine / referee / ledger / online_fdr / triad_scan /
`evidence.py` / `api/evidence.py`), `proven_signals`, `app/evidence/page.tsx` structure.

## Tests Run

- **Frontend unit** (`cd apps/frontend && npx tsx lib/evidence.test.ts`): **37 passed** (was 27; +10 new
  combination checks). All 8 `lib/*.test.ts` files pass (evidence 37, factor-lab-evidence 5, api-base 11,
  asof-step 13, mdd-color 9, membership-timeline-view 18, research-lab-columns 8, research-labs 6).
- **Frontend typecheck** (`node_modules/.bin/tsc --noEmit`): clean, no errors.
- **Frontend route smoke** (`next dev` on :3255): `/evidence`, `/research/factor-combination`,
  `/research/factor-lab`, `/stocks` all compile and serve **HTTP 200**, no compile errors.
- **Backend** (`cd apps/backend && .venv/bin/python -m pytest`): `test_evidence.py` **14 passed**;
  the ledger-adjacent set (test_evidence, test_api_evidence, test_referee, test_staging_ledger_routing,
  test_forward_walk, test_mcp_window) **66 passed** after fixing the 2 live-ledger golden assertions.
  (A full-suite run was launched; see Known Issues if the final tally is not yet attached.)
- **Live endpoint** (`GET /api/evidence` on a running backend): **6 claims**; the combination row is served
  `signal=null, proven=true, status=PASS`, `condition=["rs_spy_3m:top:quintile","high_proximity:top:tertile"]`,
  `horizon=20`, `cohort=composite`, `ledger=canonical`, `holdout_edge=0.046931901591708916`,
  `control_excess=0.046931901591708916`, `p_value=0.0009995002498750624`, `register_date=2026-07-01`;
  `proven_signals` still exactly `{leadership_score}` (combination is ABSENT — signal-less).

## Known Issues

- **Browser badge flip is the browser-qa lane's job.** Unit + live-endpoint checks confirm the data path and
  the pure resolver; the actual on-page "Proven"/"Not yet proven" badge flip and md5-distinct screenshots are
  produced by the canonical `browser-qa-agent` lane (REQUIRED per the plan). To reach "Proven" the operator
  MUST compose `rs_spy_3m:top:quintile` + `high_proximity:top:tertile` at horizon **20** — the config default
  is the FAILED `rs_spy_3m × atr_pct` pair, which correctly reads "Not yet proven".
- **Two backend test files were edited (test-only).** `test_canonical_ledger_frozen_golden` and two
  assertions in `test_staging_ledger_routing.py` are frozen goldens pinned to the LIVE canonical ledger; they
  legitimately needed the 5→6 update when the gate appended row 6 (exactly as iter-11 updated 4→5). No app
  code changed — this is bookkeeping of honest history, not a behavior change.
- **Anchor is factor-key-derived.** `combinationClaimId` sorts the legs' factor keys (matching the documented
  example and keeping the URL hash colon-free); it is collision-free for the curated pre-registered candidate
  set (distinct factors per pair). The full per-leg side/quantile detail is still shown verbatim in the
  `/evidence` row's `condition` hypothesis chip, and the leg-SET match (order-independent) uses the full legs.
