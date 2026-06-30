# Phase goal-mcp-loop-iter-4 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-4
**Date:** 2026-06-30
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see a certified market-regime-conditioned edge on the Evidence page: the second claim row reads "Breakout-watch setup", is labeled "Regime: Risk-on", and displays the out-of-sample holdout edge (+6.12% vs SPY) with its registration date and significance — all sourced verbatim from the evidence API.
- Users can now navigate directly from the Dashboard regime panel to the Evidence page by clicking the new "See evidence proven in this regime →" link, which appears below the regime component-breakdown disclosure in the Market Regime card.
- Users can now read an honest framing for the setup (non-score) claim on the Evidence page: the subtitle "Out-of-sample edge in the Risk-on regime" makes the historical, regime-conditioned nature of the result explicit.
- Users can now follow a link from the Breakout-watch claim row directly to the Research event-study lab ("/research/event-study") by clicking "Backs: Research event-study lab →" — the correct research surface for this type of evidence.

---

## What Changed in the Visible UI

- The Evidence page (`/evidence`) second claim row now displays a "Regime: Risk-on" badge in the row header beside the verdict badge; it was absent before because regime-conditioned claims were not labeled.
- The Evidence page second claim row title changed from "Unmapped signal" (a developer placeholder) to "Breakout-watch setup" (the actual subject of the claim).
- The Evidence page second claim row now shows a subtitle line "Out-of-sample edge in the Risk-on regime" where no subtitle appeared before.
- The Evidence page second claim row linkback changed from "Backs: Stocks leaderboard →" (misleading — this claim backs no score) to "Backs: Research event-study lab →" pointing to `/research/event-study`.
- The Dashboard (`/`) Market Regime card now contains a "See evidence proven in this regime →" link to `/evidence` below the component-breakdown disclosure area; the regime number (76.05) and label (Risk-on) are unchanged.

---

## What Old Behavior Changed

- Evidence page — setup (non-score) claim row: previously the row showed "Unmapped signal" and linked to the Stocks leaderboard, which was both meaningless and misleading. Now the row shows "Breakout-watch setup" with an accurate framing line and links to the Research event-study lab.
- Evidence page — claim rows without a `regime` selector (the leadership/score row): no visible change — the regime badge does not appear, and the leadership row title, verdict, and "Backs: Stocks leaderboard →" link remain byte-identical to before.

---

## Not Visible Yet

- None. All capabilities implemented this iteration are directly accessible from the running UI. The backend confirming test (a pytest addition to `test_evidence.py`) is a test-only guard with no user-visible surface.
