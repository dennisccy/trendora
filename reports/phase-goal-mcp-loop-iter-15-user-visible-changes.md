# Phase goal-mcp-loop-iter-15 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-15
**Date:** 2026-07-01
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On `/research/factor-lab`, select the `rs_spy_3m` (3-month relative-strength) factor and look at the 60-day hold horizon — the cohort cell now shows a "Proven" badge where it previously said "Not yet proven". Clicking the badge navigates to the matching Evidence ledger row.
- On `/evidence`, view a 7th certified-claim row for `rs_spy_3m` top decile at the 60-day hold, including the out-of-sample edge (+21.34%), the SPY control benchmark, the p-value, the registration date, and a "Backs: Research factor lab →" link that returns to the factor lab.
- Follow the audit trail end-to-end: from the "Proven" badge on the factor lab, through the deep-link to the `/evidence` row, and read the exact statistical values that prove the edge is out-of-sample and control-beating — without leaving the app.

---

## What Changed in the Visible UI

- The `/evidence` ledger now shows **7 rows** instead of 6. The new 7th row is for `rs_spy_3m`, titled "rs_spy_3m — top decile (D10)" with subtitle "Out-of-sample edge — factor top decile · 60-day hold", and includes a "Backs: Research factor lab →" linkback.
- On `/research/factor-lab`, the `rs_spy_3m` factor's **60-day-horizon evidence chip** changed from a muted "Not yet proven" pill to a quiet proven-checkmark "Proven" pill. The chip carries a deep-link to `/evidence#factor-rs_spy_3m-d10-h60`.
- The `rs_spy_3m` factor's 1-day, 5-day, 10-day, and 20-day horizon chips on the factor lab are unchanged — all four still read "Not yet proven". Proven-ness did not leak to uncertified horizons.
- The `/stocks` leaderboard and its per-stock inline score badges are unchanged. `rs_spy_3m` is not one of the three scored columns, so no stock entry gained or lost a score badge.

---

## What Old Behavior Changed

- `/research/factor-lab`, `rs_spy_3m` factor, h60 cell: previously showed a muted "Not yet proven" state. Now shows a "Proven" pill badge with a deep-link to `/evidence#factor-rs_spy_3m-d10-h60`. All other cells of that factor row are unchanged.
- The Bonferroni statistical bar governing future certifications tightened permanently (divisor moved 6 → 7, required p-value threshold moved from ~0.00833 to ~0.00714). This is reflected on the `/evidence` row for this new entry (`deflation_divisor: 7`). Users who previously saw 6 ledger entries now see 7.

---

## Not Visible Yet

None. Every change in this iteration — the new factor-lab badge and the new Evidence ledger row — is served by the existing `GET /api/evidence` endpoint and rendered by the existing general frontend machinery. No backend capability was added that lacks a UI access point.
