# goal-mcp-loop-iter-8 — Implementation Summary

**Phase:** goal-mcp-loop-iter-8
**Date:** 2026-06-30
**Written by:** developer

---

## Features Implemented

- **"Proven" evidence badge on the Research factor lab**: each factor's top-decile row now carries a calm
  evidence chip. The `vcp_contraction` factor's top decile reads **"Proven"** — the first time a plain
  (non-score) research factor is marked proven — because a statistical referee certified, on a sealed
  out-of-sample holdout, that this cohort beat the SPY benchmark. Clicking the badge jumps to the backing
  entry on the Evidence ledger.
- **New Evidence-ledger row for the vcp_contraction edge**: the `/evidence` page now lists a fourth certified
  claim showing the hypothesis, the out-of-sample verdict (holdout edge **+3.33%**, significance p **0.0115**),
  the SPY control comparison, the registration date (2026-06-30), the forward-walk status, and a
  "Backs: Research factor lab →" link back to where the badge appears.
- **Honest "Not yet proven" everywhere else**: every other factor's top decile — including `ma_stack`, whose
  edge was tested and **rejected** by the referee — reads "Not yet proven" with no link, so an unproven
  pattern never looks confident.

---

## Changed Behavior

- **Research factor lab table**: previously every factor row showed only its statistics (rank-IC, downside,
  per-horizon returns/drawdowns). Now it also shows an "Evidence (D10 · 20d)" column with a Proven /
  Not-yet-proven status for each factor's top decile.
- **Evidence ledger page**: previously showed 3 rows (Leadership score, Breakout-watch regime setup, and the
  rejected ma_stack edge). Now shows 4 — the new vcp_contraction row is appended, and the two plain-factor
  rows (ma_stack, vcp_contraction) get a clear factor title and a link back to the factor lab.
- **Deep-link anchors**: a "Proven" badge always lands on the exact ledger row it backs. Score-based proofs
  (e.g. Leadership) still land on their existing per-score anchor; the new plain-factor proof lands on its
  own factor-cohort anchor. No existing link changed target.

---

## Backend-Only Items

- None. No backend application code changed. The vcp_contraction edge was certified by the post-decompose
  referee gate (already on the ledger) and is served by the existing `GET /api/evidence` endpoint unchanged;
  this iteration only adds front-end readers plus one confirming backend test.

---

## Incomplete Items

- None. All Definition-of-Done items for J-06 are implemented and verified live in the browser. The five
  required-still-passing journeys (J-01..J-05) were re-checked and remain green.

---

## Config and Environment Changes

- None. No new environment variables, no schema/migration changes, no new config keys. The badge reads the
  existing config values served in the factor-lab payload (top decile = 10, default horizon = 20 days).

---

## Known Limitations

- **The "Proven" status depends on the certified-claims ledger.** If the Evidence API is unreachable, every
  factor-lab badge safely falls back to "Not yet proven" with no link (it never invents a "Proven" status and
  never errors the page).
- **Honest side effect**: because the matcher is general, the `Leadership score` factor row — which is also a
  certified score — correctly reads "Proven" in the factor lab as well (linking to its existing ledger entry).
  This was intentional and is accurate; it was not narrowed to only vcp_contraction because hiding a true
  proven status would be misleading. The per-stock score badges on `/stocks` are unaffected (Leadership
  remains the only "Proven" score there; the vcp_contraction factor adds no per-stock signal).
- **Full backend regression suite**: the tests covering everything this iteration touches pass (130/130:
  evidence resolver, the evidence API, the factor-lab data, the referee, and the research API). The complete
  project test suite has 1267 tests and takes about 45 minutes to run end-to-end, so the automated harness's
  time limit stops it early — that is a time limit, not a test failure (no application code changed on the
  backend; only one test was added).
