# Phase goal-mcp-loop-iter-11 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-11
**Date:** 2026-07-01
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see whether a factor's top-decile edge has been referee-certified at **each individual holding period** (1, 5, 10, 20, and 60 trading days) directly in the Factor Lab table at `/research/factor-lab` — the evidence column shows one chip per horizon instead of a single chip.
- Users can now click the `vcp_contraction` 60-day "Proven" chip on the Factor Lab to deep-link directly to its certified claim on the Evidence page at `/evidence#factor-vcp_contraction-d10-h60`.
- Users can now read the honest evidence status for every horizon at a glance: `vcp_contraction`'s 1-day, 5-day, and 10-day chips read "Not yet proven" (with no link), while its 20-day and 60-day chips read "Proven" (each linking to its own Evidence row).
- Users can now view the first non-20-day certified edge on the Evidence page: a new `vcp_contraction — top decile (D10)` row at the 60-day horizon, showing the out-of-sample result (+8.91%), the SPY benchmark comparison (+8.91%), the registration date, a "Pending" forward-walk score, and a link back to the Factor Lab.

---

## What Changed in the Visible UI

- The Evidence column header on the Factor Lab table changed from "Evidence (D10 · 20d)" to **"Evidence (D10 · per horizon)"**, reflecting that it now covers all five served horizons.
- Each factor row in the Factor Lab now shows a **compact chip strip of five evidence pills** (one per horizon: 1d, 5d, 10d, 20d, 60d) instead of the previous single chip — making every factor row slightly taller.
- A new certified-claim row appeared on the Evidence page (`/evidence`) for **`vcp_contraction — top decile (D10)` at 60 days** — the 5th row in the ledger. Its subtitle reads "Out-of-sample edge — factor top decile · 60-day hold" to distinguish it from the existing 20-day row.
- Each evidence chip on the Factor Lab now carries a `data-horizon` attribute (e.g. `data-horizon="60"`) alongside its `data-proven` and `data-factor` attributes, enabling per-horizon browser selection. This is not directly visible to ordinary users but is the mechanism behind the precise per-horizon proven/not-proven display.

---

## What Old Behavior Changed

- **Factor Lab evidence column**: Previously showed a single "Proven" or "Not yet proven" badge per factor, resolved at the 20-day default horizon. Now shows five chips — one per horizon — each resolved independently. The 20-day chip behavior is unchanged; only the single-chip presentation is replaced by the per-horizon strip.
- **Evidence page claim count**: Previously listed four certified claims (leadership_score PASS, Breakout-watch PASS, ma_stack FAIL, vcp_contraction h20 PASS). Now lists five — the prior four rows are unchanged, and the new 60-day `vcp_contraction` row is additive.

---

## Not Visible Yet

- None. All capabilities implemented in this iteration are fully surfaced in the UI. The 60-day certified claim is read from the existing `GET /api/evidence` endpoint (no new backend code) and is rendered both on `/evidence` (new row) and on `/research/factor-lab` (new h60 chip). No backend application code was written or modified; all test-file updates are internal and carry no UI surface.
