# Phase goal-mcp-loop-iter-8 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-8
**Date:** 2026-06-30
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see whether a research factor has certified out-of-sample evidence for its top-decile cohort by navigating to `/research/factor-lab` and reading the new "Evidence (D10 · 20d)" column that appears on every factor row.
- Users can now click the "Proven" badge on the vcp_contraction factor row to jump directly to its backing ledger entry at `/evidence#factor-vcp_contraction-d10-h20`, without needing to search the Evidence page manually.
- Users can now read the full certified evidence for the vcp_contraction top-decile edge on `/evidence`: the out-of-sample holdout edge (+3.33%), statistical significance (p 0.01149), the SPY control label, the registration date (2026-06-30), and the forward-walk status.
- Users can now navigate from the vcp_contraction row on `/evidence` back to the Research factor lab by clicking "Backs: Research factor lab →" — a round-trip between the two pages.

---

## What Changed in the Visible UI

- The Research factor lab (`/research/factor-lab`) table gained a new "Evidence (D10 · 20d)" column. Every factor's top-decile summary row now shows a status chip.
- The vcp_contraction factor row on `/research/factor-lab` shows an accent-colored "Proven" chip with a ShieldCheck icon. Clicking it deep-links to the vcp_contraction evidence row — clicking does NOT expand or collapse the factor row (that behavior is preserved for clicks on the row itself).
- The Leadership score factor row on `/research/factor-lab` also shows a "Proven" chip, linking to its existing `signal-leadership_score` evidence entry. This is accurate: its score edge is already certified.
- All other factor rows (including ma_stack, whose edge was tested and rejected) show a muted "Not yet proven" chip with an outline Shield icon and no link.
- The `/evidence` page now lists a fourth claim row for the vcp_contraction top-decile cohort. The row shows an honest factor title, the OOS verdict with holdout edge and significance, the SPY control label, the registration date, the forward-walk status, and a "Backs: Research factor lab →" linkback.

---

## What Old Behavior Changed

- `/evidence` row for ma_stack: previously appeared without a factor-specific title or linkback. Now shows the factor title "ma_stack — top decile (D10)", the subtitle "Out-of-sample edge — factor top decile", and a "Backs: Research factor lab →" link. The verdict remains "Not yet proven" (FAIL status from the referee is unchanged).
- `/evidence` ClaimRow anchor IDs: signal-less factor cohort rows (vcp_contraction, ma_stack) now carry a `factor-<name>-d<decile>-h<horizon>` anchor id. Previously these rows had no anchor. Score rows (e.g. leadership_score) still use `signal-leadership_score`. The event-study row still carries no anchor. Existing deep-links from `/stocks` to `/evidence#signal-leadership_score` are unaffected.

---

## Not Visible Yet

None. All capabilities implemented in this iteration are accessible via the UI. The vcp_contraction certified edge is surfaced on both `/research/factor-lab` (as an evidence badge) and `/evidence` (as a claim row). No backend application code changed; no new backend capability was added without UI exposure.
