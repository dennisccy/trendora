# goal-mcp-loop-iter-11 Dev Handoff

**Phase:** goal-mcp-loop-iter-11
**Date:** 2026-07-01
**Agent:** developer
**Status:** complete

## What Was Built

Surfaced **J-07**: the referee-certified `vcp_contraction` D10 @ **h60** signal-less edge (5th canonical
ledger entry, PASS, holdout **+8.91%**, block-bootstrap p 0.0004998 < the divisor-5 bar 0.010) is now
visible end-to-end. The Research Factor Lab evolves from a single-horizon (h20-only) evidence marker to an
honest **per-horizon** view.

- **Per-horizon factor-lab evidence badges** — the Evidence column on `/research/factor-lab` now renders one
  evidence chip PER served horizon (`data.horizons` = `[1,5,10,20,60]`) instead of a single chip at the
  default horizon. On the `vcp_contraction` row: **h60 → "Proven"** (deep-links to
  `/evidence#factor-vcp_contraction-d10-h60`), **h20 → "Proven"** (deep-links to `…-h20`, unchanged — J-06),
  h1/h5/h10 → "Not yet proven" (no link). Each chip is a compact `{h}d {status}` pill in a wrapped strip.
- **`data-horizon` selector** — every badge now carries `data-horizon={h}` alongside the existing
  `data-testid="factor-evidence-badge"` / `data-proven` / `data-factor`, so each per-horizon chip is
  independently selectable (`[data-factor="vcp_contraction"][data-horizon="60"]` → `data-proven="true"`).
- **`/evidence` h60 claim row** — auto-renders from the new 5th ledger entry via the existing `ClaimRow`
  (no new component). Its subtitle is horizon-disambiguated (`"Out-of-sample edge — factor top decile ·
  60-day hold"`) so it is self-distinguishing from the h20 vcp_contraction row (whose wording stays
  byte-identical — J-06).
- **No new data path** — the h60 badge + row read the canonical `GET /api/evidence` payload verbatim through
  the EXISTING `resolveCohortEvidence` matcher. No new backend module, no new endpoint, no recompute.

The 5th canonical ledger entry itself was written by the **post-decompose gate** (not by this developer) and
was already on disk. No `apps/backend/app/**` code was touched.

## Files Changed

- `apps/frontend/lib/factor-lab-evidence.ts` — **NEW** pure module. `factorHorizonBadges(factor, topDecile,
  horizons, claims)` → one `FactorHorizonBadge` descriptor per horizon (resolved via the existing
  `resolveCohortEvidence`). Extracted so the per-horizon logic is unit-testable under the repo's TS type-strip
  convention (no React renderer is installed).
- `apps/frontend/lib/factor-lab-evidence.test.ts` — **NEW** 5 checks: one badge per horizon in order; vcp
  h60/h20 "Proven" with horizon-distinct hrefs + h1/h5/h10 "Not yet proven"; ma_stack FAIL never "Proven";
  leadership_score (score column) honestly "Proven" at h20 → `signal-…` row; empty/null claims fail-safe.
- `apps/frontend/app/research/_labs.tsx` — `FactorEvidenceBadge` is now presentational (consumes a
  descriptor, adds `data-horizon`); `FactorRows` renders the per-horizon chip strip via `factorHorizonBadges`;
  the Evidence column header reads `Evidence (D10 · per horizon)`. The "Proven" `<Link>` keeps its
  `stopPropagation()` guard (iter-5 nested-interactive hazard). Removed now-unused evidence imports.
- `apps/frontend/lib/evidence.ts` — `claimSurface` factor-cohort subtitle horizon-disambiguation ONLY (new
  `DEFAULT_FACTOR_COHORT_HORIZON = 20` constant; h20 stays bare, h60 gains "· 60-day hold"). No other function
  changed.
- `apps/frontend/lib/evidence.test.ts` — updated case (o) (h60 is no longer a mismatch → swapped for the
  uncertified h5); added the positive h60 `resolveCohortEvidence` case (m2); added `formatEvidencePct(
  0.08909719710495288) === "+8.91%"`; added the `claimSurface` h60 disambiguation test (s2) that also pins
  h20 byte-identical. 27 checks (was 25).
- `apps/backend/tests/test_evidence.py` — **TEST-ONLY**: updated `test_canonical_ledger_frozen_golden` to the
  5-entry reality (statuses `[PASS,PASS,FAIL,PASS,PASS]`, divisors `[1..5]`, h60 bytes pinned, proven_signals
  still `{leadership_score}`); added `_vcp_contraction_h60_pass_entry()` + a new payload test asserting the h60
  row is served verbatim and stays signal-less. No `app/**` change.
- `apps/backend/tests/test_staging_ledger_routing.py` — **TEST-ONLY**: updated the two golden values that
  pinned the canonical ledger to 4 trials (`test_rejection_offsets_on_live_canonical_ledger` and the
  canonical-untouched assertions in `test_committed_staging_ledger_is_the_frozen_multi_horizon_discovery`) to
  the post-promotion reality (`count_trials == 5`, `rejection_offsets == [1,2,4,5]`), plus the stale module
  docstring. The staging-ledger assertions (still 4 candidates) are unchanged. No `app/**` change.

## Tests Run

- **Frontend unit** (Node TS type-strip convention): `cd apps/frontend && npx tsx lib/<name>.test.ts`
  - `lib/factor-lab-evidence.test.ts` → **5 passed**
  - `lib/evidence.test.ts` → **27 passed**
  - Full `lib/*.test.ts` sweep (8 files) → **all pass** (api-base 11, asof-step 13, evidence 27,
    factor-lab-evidence 5, mdd-color 9, membership-timeline-view 18, research-lab-columns 8, research-labs 6).
  - `npx tsc --noEmit` → **clean** (0 errors, `strict: true`).
- **Backend** (`cd apps/backend && .venv/bin/python -m pytest`):
  - `tests/test_evidence.py` → **13 passed** (was 12; +1 h60 payload test).
  - `tests/test_evidence.py tests/test_api_evidence.py` → **16 passed** (API layer serves the 5-entry ledger).
  - `tests/test_staging_ledger_routing.py` → **all pass** after the golden updates (the two pre-existing
    failures from the gate's 5th entry are resolved).
- **Live endpoint check** — started the backend (port 8255) and `curl http://localhost:8255/api/evidence`:
  serves **5 claims**, `proven_signals == {leadership_score}` (byte-identical), and both vcp_contraction rows
  (h20 + h60) present with edge/p/control **byte-matching** the ledger (h60: holdout `0.08909719710495288`,
  control `0.08909719710495288`, p `0.0004997501249375312`, signal `None`). Backend process was killed after.

## Known Issues

- **Browser verification is deferred to the canonical browser-qa lane** (Frontend Present: yes). This handoff
  verified the badge/row LOGIC (unit + live API), but the actual on-screen badge flip
  (`[data-horizon="60"]` reading "Proven", scrolled into the viewport per the iter-3 lesson — the table is
  wide) must be captured by `browser-qa-agent` writing
  `reports/phase-goal-mcp-loop-iter-11-ui-test-results.md`. Free port **:3255** and ensure the frontend can
  reach the backend (:8255) before the browser lane binds.
- **No React component renderer** is installed in `apps/frontend`, so the "per-horizon badge" logic is tested
  via the extracted pure `factorHorizonBadges` (its output is exactly the per-chip `data-horizon`/`data-proven`
  inputs the component renders). The visual render is browser-qa's responsibility.
- **Per-horizon row height**: every factor row now shows 5 evidence chips (honest per-horizon view, not
  special-cased to vcp). This is intentional (J-07 evolution) and matches the data-dense evidence-first design;
  rows are marginally taller. `leadership_score` legitimately reads "Proven" at h20 (it has a real PASS
  canonical entry) — this is honest, not a bug, and was deliberately NOT special-cased.
