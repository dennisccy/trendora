# Phase goal-mcp-loop-iter-23 — UI Surface Map

**Phase:** goal-mcp-loop-iter-23
**Date:** 2026-07-08
**Written by:** ui-impact-analyst

---

## File Classification

Per `.claude/skills/diff-to-ui-impact.md`. The dev handoff lists exactly one changed file. Independently re-verified against the working tree (`git status`, `git diff HEAD`) and cross-checked against the reviewer's report and `runs/goal-mcp-loop-iter-23/status.json`'s `changed_files` field — all three sources agree on this single file, with zero diff anywhere under `apps/backend/` or `apps/frontend/`.

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `runs/goal-session-mcp-loop/journey-scripts/J-13.json` | config (QA test fixture) | none | A golden-replay script consumed only by the project's own automated browser-QA tooling — not application code, not served to end users. The one-line edit updates an expected-text assertion (`"587 symbols"` → `"590 symbols"`) to match a pool count that already changed in iter-22's additive index-symbol load (confirmed live: `apps/backend/app/data/page.tsx`'s "Symbols" stat card renders `c.symbol_count`, independently confirmed as 590 in the dev handoff's live DB query). |

**No frontend-direct, backend-api, or backend-internal application files changed.** This is a genuine zero-application-diff iteration — called out explicitly here rather than leaving the table looking incomplete.

---

## Note on how to read this iteration's surface-map rows

Because no code changed, none of the rows below represent a *changed* surface in the usual sense — no "New page," "New component," "Changed behavior," etc. actually applies. Instead, this iteration's entire deliverable is the **formal, canonical, browser-executed re-verification** of surfaces that already existed at the end of iter-22, whose evidence-of-record (the `browser-qa-agent` and `ux-regression-reviewer` reports) had gone stale after a bug fix and were blocking phase closure. Rows are included below — Change Type labeled **"Re-verification only (no code change)"** — because these are exactly the surfaces this iteration's dispatched `browser-qa-agent` must exercise LIVE. Each "What to Test" action is grounded in the phase spec's Key Test Scenarios and `reports/qa/goal-mcp-loop-iter-23-test-plan.md`, and cross-checked against the actual current component source (`phase-cross-view-chart.tsx`, `index-vendor-panel.tsx`, `availability-heatmap.tsx`, `app/data/page.tsx`).

## Affected UI Surfaces

| Route/Page | Component/Element | Change Type | Why Changed | What to Test |
|-----------|------------------|------------|-------------|--------------|
| `/` | "Regime × phase cross-view" card — deep default view (`phase-cross-view-chart.tsx`) | Re-verification only (no code change) | J-14 target: this exact case FAILed in iter-22's stale QA report before the `minBarSpacing: 0.02` fix (confirmed present at `phase-cross-view-chart.tsx:162`); must now be proven live against the fixed build | Load `/` with no zoom or pan applied (default view). Confirm the chart's leftmost visible x-axis date is on or before 1997-12-31 (not ~2018, the pre-fix symptom), and that a legend entry reads "S&P 500 Index (^SPX) (Stooq)". Capture a full-page or element-clip screenshot (never a scrolled viewport) and md5-check the `^SPX` line pixels are actually in-frame — a PASS label or DOM-text legend line alone is not proof. |
| `/` | same chart — legend + hover-tooltip vendor suffixes (`phase-cross-view-chart.tsx:369,450`) | Re-verification only (no code change) | J-14: vendor attribution must render on both the legend (`(vendor)` suffix) and the tooltip (`· vendor` suffix) | Hover the chart on any date. Confirm the tooltip lists "^SPX · Stooq", "^VIX · Yahoo", and "^TNX · FRED-macro proxy" suffixes, and that the 5 pre-existing ETF lines (SPY/QQQ/IWM/RSP/DIA) show no vendor suffix at all (honest omission, not a blank guess). |
| `/data` | "Index & benchmark data provenance" panel (`index-vendor-panel.tsx`, `data-testid="index-vendor-panel"`) | Re-verification only (no code change) | J-14: panel must byte-match `apps/backend/data/seed/meta.json` | Load `/data` and locate the provenance table (`data-testid="index-vendor-table"`). Confirm the `^SPX` row reads vendor "Stooq" / first bar "1996-01-02", the `^VIX` row reads "Yahoo" / "1996-01-02", and the `^TNX`/`^DXY`/`^VXN` rows read "FRED-macro proxy" / "2021-01-04" (never "market index"). Confirm ETF rows (SPY, QQQ, IWM, RSP, DIA) show "—" in the vendor column rather than a fabricated vendor label. |
| `/data` | Availability heatmap — two-group legend, density ramp, snapshot ring (`availability-heatmap.tsx`; dedicated J-13 replay) | Re-verification only (no code change) | J-13: last dedicated pixel-level replay was iter-21; this iteration closes that gap and confirms the refreshed `journey-scripts/J-13.json` fixture | On `/data`, hover one calendar cell that has price bars but no scored snapshot, then hover a second cell that has both bars and a snapshot. Confirm the two tooltips render distinctly different text, the legend shows two separately labeled groups — "Price data — cell fill" and "Scored snapshot — indicator" (confirmed exact strings at `availability-heatmap.tsx:247,260`) — the density ramp's top bucket is not amber-colored, and the snapshot indicator renders as a violet ring. Capture md5-distinct screenshots of both hover states. |
| `/stocks` | Leaderboard — row count and caret leakage | Re-verification only (no code change) | J-01 regression check | Load `/stocks` and count the rendered rows. Confirm exactly 541 rows, and confirm zero rows begin with a `^` caret (which would indicate an index/macro symbol leaking into the equity leaderboard). |
| `/stocks` | Leaderboard — evidence badges | Re-verification only (no code change) | J-03 regression check | On the same leaderboard, inspect the Leadership / Entry-Quality / Risk score cells for 3–5 spot-checked rows. Confirm every visible score badge reads "Not yet proven" and none read "Proven". |
| `/` | Regime/phase summary card + Evidence link | Re-verification only (no code change) | J-04 regression check | On `/`, confirm the regime/phase card displays a current label, then click its "Evidence" link. Confirm the browser navigates to `/evidence` and the page returns HTTP 200. |
| `/evidence` | Certified-claims ledger table | Re-verification only (no code change) | J-05 regression check | Load `/evidence`. Confirm exactly 7 rows render, every row shows a FAIL verdict, and clicking any row's linkback (e.g. "Backs: Research factor lab →") navigates to the correct research surface. |
| `/stocks/{ticker}` | Full ↔ Recent history toggle (e.g. `/stocks/AAPL`) | Re-verification only (no code change) | J-10 regression check | On `/stocks/AAPL`, click "Full". Confirm the chart re-renders to a leftmost date on or before 1997-12-31 with no console error, then click "Recent" and confirm it returns to a window of 5 years or less. |
| `/evidence` + factor-lab pages | Ledger rows + cohort badges | Re-verification only (no code change) | J-11 regression check | On `/evidence` and a factor-lab page (e.g. `/research/factor-lab` for `vcp_contraction`), confirm no row or badge displays a stale pre-iter-22 "Proven" value (e.g. old figures like +21.34%, p=0.0004998). Confirm every visible cohort badge reads "Not yet proven". |
| `/data` vs `/stocks` | "Symbols" stat card vs. leaderboard row count | Re-verification only (no code change) | J-12 regression check | Navigate to `/data` and read the "Symbols" stat card value (should read 590 — every ticker with stored bars, including ETFs/`^VIX`/macro proxies, per its own on-page definition). Navigate to `/stocks` and confirm exactly 541 rows (the point-in-time scored-equity universe). Confirm these two independently-computed counts are internally consistent with their documented definitions (590 total pool ⊇ 541 scored equities). |
| `/data` | Whole-page backend-down state | Re-verification only (no code change) | Anti-goal / error-case check: honest degradation is required, never a blank error page | Stop the backend service, then reload `/data`. Confirm an honest, human-readable message (e.g. "Backend unavailable") renders somewhere on the page — never a blank white screen or an unhandled application-error page. Restart the backend, reload, and confirm the page recovers normally. |
| `/` and `/data` | ETF rows with no vendor record (honest-omission check) | Re-verification only (no code change) | Anti-goal / honesty check: never fabricate a vendor label | Inspect an ETF line (e.g. SPY) in both the Dashboard chart legend/tooltip and the `/data` provenance table row. Confirm neither location shows a fabricated vendor name — both must show no suffix / "—" for a series absent from `meta.json`'s vendor field. |

---

## Backend-Only Changes (No UI Impact)

- `runs/goal-session-mcp-loop/journey-scripts/J-13.json` — QA-tooling fixture (expected-text string for the automated replay of J-13), not application code; no UI surface reads this file. This is the only file changed in the entire iteration.
- `apps/backend/tests/test_api_indexes.py` — no source edit was made to this file this iteration; listed here only because *running* it (unchanged) surfaced a pre-existing test-assertion gap (`KeyError: '^TNX'` on a `full=true` + historical-`as_of` combination — see the companion `user-visible-changes.md` report's "Not Visible Yet" section). No production code changed, and no UI surface is affected: the default Dashboard view this iteration's DoD cares about is covered by other, passing assertions in the same file (`test_api_indexes_includes_vendor_and_first_for_deep_series`, `test_api_indexes_equals_engine_and_includes_committed_dia`).
- No backend production source, migrations, or models changed this iteration. No new or modified API endpoints. No config/env changes.

---

## Summary

- **Frontend surfaces changed:** 0 (zero frontend source diff — every row above is a re-verification of an already-existing, unmodified surface, not a change)
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 1 file touched (test fixture only; 0 production backend files changed)
- **Surfaces re-verified live this iteration (informational, not "changed"):** 8 distinct routes/pages, covering J-14 (target, 3 rows), J-13 (dedicated replay, 1 row), the J-01/J-03/J-04/J-05/J-10/J-11/J-12 regression set (7 rows), and 2 anti-goal/error-case checks
