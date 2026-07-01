# Phase goal-mcp-loop-iter-13 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-13
**Date:** 2026-07-01
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can see a "Proven" / "Not yet proven" evidence badge on the Multi-factor combination lab's composite cohort row at `/research/factor-combination`. The badge reads "Proven" only when the user selects the certified pair — relative-strength leaders (rs_spy_3m / top / quintile) combined with proximity-to-52-week-high (high_proximity / top / tertile) — at the 20-day horizon. Every other combination the user composes reads "Not yet proven".
- Users can click the "Proven" badge on the combination lab to jump directly to its backing evidence row on the Evidence page (`/evidence#combination-high_proximity-rs_spy_3m-h20`), auditing exactly why the combination is considered proven.
- Users can read a new 6th certified-claim row on the Evidence page (`/evidence`) for the rs_spy_3m × high_proximity composite combination at the 20-day horizon. The row shows the two condition chips, the out-of-sample PASS verdict, the holdout edge (+4.69%), the control comparison versus SPY (+4.69% better out-of-sample), the registration date (2026-07-01), the forward-walk status ("Pending"), and a "Backs: Multi-factor combination lab →" linkback.
- Users can compose any other 2-factor combination on the combination lab (including the default rs_spy_3m × atr_pct pair, or the certified legs at any horizon other than 20) and confirm the composite badge honestly reads "Not yet proven" with no deep-link — demonstrating that exactly one pre-registered combination has passed the referee.

---

## What Changed in the Visible UI

- **`/research/factor-combination` — composite cohort row**: The Combined (composite rank-blend) row now includes an inline evidence chip alongside the existing cohort statistics. An accent ShieldCheck "Proven" chip with a deep-link appears only for the certified selection; a muted Shield "Not yet proven" chip with no link appears for all other selections. The chip is reactive — it updates immediately when the user changes either leg or the horizon.
- **`/evidence` — certified-claim list**: Now shows 6 rows instead of 5. The new 6th row is the rs_spy_3m × high_proximity combination. It is rendered through the same `ClaimRow` layout as all prior rows — it was previously absent because the combination branch of `claimSurface` / `claimAnchorId` did not exist; it now renders with an honest composite title and the "Backs: Multi-factor combination lab →" linkback instead of the earlier "Unmapped signal" fallback text.

---

## What Old Behavior Changed

- **Evidence page (`/evidence`)**: Previously listed exactly 5 certified claims (1 score, 3 factor, 1 event-study). Now lists 6 — the 6th is the new combination claim. The prior 5 rows are byte-identical and display unchanged.
- **Multi-factor combination lab (`/research/factor-combination`)**: The composite cohort row was previously purely statistical (cohort percentile data only). It now also carries an evidence badge. The cohort statistics themselves are unchanged; the badge is an additive element on the same row.

---

## Not Visible Yet

None — all implemented capabilities are accessible via the UI. The combination evidence is fully surfaced on both target routes reading the same live API feed. No backend capability was added without a corresponding UI surface.
