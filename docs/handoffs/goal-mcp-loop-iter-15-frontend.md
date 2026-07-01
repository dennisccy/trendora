# goal-mcp-loop-iter-15 Frontend Handoff

**Phase:** goal-mcp-loop-iter-15
**Date:** 2026-07-01
**Agent:** developer
**Status:** complete

## What Was Built (UI)

**No frontend source change.** J-09 surfaces the 7th certified edge (`rs_spy_3m` D10 h60) entirely through
the read-side machinery already built by J-06/J-07 (iter-8/iter-11):

- **Research factor lab (`/research/factor-lab`)** — the general per-horizon matcher `resolveCohortEvidence`
  (already resolved for each horizon in `[1,5,10,20,60]` since iter-11) now matches the served `claims[]`
  for `rs_spy_3m` at h60 → the **h60 cohort reads "Proven"** and deep-links to
  `/evidence#factor-rs_spy_3m-d10-h60`. Its **h1/h5/h10/h20 cohorts stay "Not yet proven"** (no cross-horizon
  leak). No factor-specific branch was added (iter-8 "don't special-case" lesson).
- **Evidence ledger (`/evidence`)** — the `ClaimRow` renders the new row through the EXISTING signal-less
  `factor` branch: title "rs_spy_3m — top decile (D10)", subtitle "Out-of-sample edge — factor top decile ·
  60-day hold" (horizon-disambiguated), and the "Backs: Research factor lab →" linkback. The ledger grows
  6 → **7** rows.
- **`/stocks` unchanged** — `rs_spy_3m` ∉ the three score columns, so the claim is signal-less and NEVER
  enters `proven_signals` (stays `{leadership_score}`). Zero new inline score badges light
  (J-01/J-02/J-03 unaffected).

## Files Changed (UI)

- `apps/frontend/lib/evidence.test.ts` -- TEST-ONLY. Added the J-09 unit block: a `rsSpy3mH60Row()` PASS
  fixture (byte-matches `certified-claims.jsonl` row 7), a `ledgerClaims7()` full-current-ledger accessor,
  check (ee) asserting `resolveCohortEvidence` resolves `rs_spy_3m` h60 → "Proven" + the horizon-distinct
  href and "Not yet proven" at h1/h5/h10/h20 (with vcp_contraction h60 unperturbed), and check (ff)
  asserting the `/evidence` row's honest `claimSurface` title/subtitle/linkback + the `claimAnchorId`
  deep-link anchor. Reconciled the negative case (o) so its now-backed `rs_spy_3m` example is a
  no-cross-horizon-leak negative against the 7-entry ledger.

**NOT edited (byte-identical):** `apps/frontend/lib/evidence.ts`, `apps/frontend/lib/factor-lab-evidence.ts`,
`apps/frontend/app/research/_labs.tsx`, `apps/frontend/app/evidence/page.tsx`.

## Design System Conformance

Reuses the EXISTING components unchanged — the `/evidence` `ClaimRow` (verdict-status Badge + `<dl>` fields)
and the factor-lab per-horizon evidence chip strip (compact `{h}d {status}` pills carrying
`data-factor`/`data-horizon`/`data-proven`). No new components, colors, effects, or layout. States handled by
the existing code: **Proven** (`rs_spy_3m` h60, quiet proven-✓ pill) and **Not yet proven** (`rs_spy_3m`
h1/h5/h10/h20, honest muted state) — calm, evidence-first, never hype (goal.md Design Direction).

## Tests Run (UI)

- `cd apps/frontend && npx --offline tsx lib/evidence.test.ts` → **39 passed** (37 prior + 2 new J-09 cases).
  The new cases pass against the UNCHANGED `evidence.ts` — proof the general matcher lights the new certified
  cohort with no source change.

## Known Issues (UI)

- Live browser verification of the "Proven" badge + `/evidence` row (md5-distinct screenshots) is the
  browser-qa-agent's lane. The read path was verified live: `GET /api/evidence` returned 200 OK and the
  payload's `rs_spy_3m` h60 row byte-matches the ledger with `proven_signals=['leadership_score']`.
- No frontend source change ⇒ no browser re-run was triggered during development. Open the ACTUAL "Proven"
  frame during browser QA and confirm it is the `rs_spy_3m` **h60** cohort (not a relabeled default-state or
  other-horizon frame; iter-13 lesson), against a LIVE backend (no "Backend unavailable" pill; iter-14
  lesson).
