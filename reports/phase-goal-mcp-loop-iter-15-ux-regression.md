# Phase goal-mcp-loop-iter-15 — UX Regression Review

**Date:** 2026-07-01

**Verdict:** UX-REGRESSION-PASS

---

## New Capability Discoverability

This iteration adds two user-visible capabilities: a 7th row on `/evidence` and a "Proven" badge state on `/research/factor-lab` for `rs_spy_3m` at the 60-day horizon. Both live on existing, already-navigable pages — no new route, page, or nav entry was needed.

**Capability 1 — `/evidence` 7th claim row (`rs_spy_3m` D10 h60)**

- Navigation path: `/evidence` is a direct sidebar link. Reaching the new row requires 1 click from any page that has the main nav visible. Browser QA confirmed 18 interactive links are rendered in the nav (UT-01) and 11 sidebar links are present even in the backend-unavailable error state (UT-04), confirming the page is always reachable.
- Click depth from home: 1 click.
- Label clarity: The row title "rs_spy_3m — top decile (D10)" and subtitle "Out-of-sample edge — factor top decile · 60-day hold" are specific. The verdict text, edge value, Bonferroni divisor, and registration date are all present without blank fields (UT-02 PASS). The "Backs: Research factor lab →" linkback is self-explanatory.
- Visual feedback: The row appears at the bottom of the list; the deep-link anchor (`#factor-rs_spy_3m-d10-h60`) auto-scrolls the row into the viewport when reached via the factor-lab chip (UT-03 PASS, scrollY=1331, element at 591px in 900px viewport).
- Assessment: Discoverable. No flag.

**Capability 2 — `/research/factor-lab` `rs_spy_3m` h60 "Proven" chip**

- Navigation path: `/research/factor-lab` is reachable from the main nav Research section. On the page, the `rs_spy_3m` row and its per-horizon chip strip are visible in the factor table without any additional interaction — all five horizon chips are rendered by default on the factor row (UT-06 PASS: "1d Not yet proven", "5d Not yet proven", "10d Not yet proven", "20d Not yet proven", "60d Proven").
- Click depth from home: 1-2 clicks (to reach the factor lab page; the chip is then immediately visible).
- Label clarity: "Proven" is unambiguous. The chip's styling distinguishes it from the muted "Not yet proven" state (UT-07 confirms `data-proven="true"` and distinct proven-checkmark pill styling on h60; `data-proven="false"` and muted state on h1/h5/h10/h20). A non-technical user can read at a glance which horizons are certified and which are not.
- Visual feedback: Clicking the chip navigates to `/evidence#factor-rs_spy_3m-d10-h60` and scrolls the matching row into view (UT-08 PASS). Full round-trip back to the factor lab via the "Backs: Research factor lab →" link works without dead ends (UT-10 PASS).
- Assessment: Discoverable. No flag.

**End-to-end audit trail (factor lab → proven badge → evidence row → back)**

The full audit trail is reachable in at most 3 total clicks from the home page: home → factor lab (1-2 clicks) → proven chip (1 click) → evidence row (automatic scroll). The reverse linkback ("Backs: Research factor lab →") returns to the factor lab in 1 more click. UT-10 verified the full round-trip without dead ends.

---

## Regression Risk

No frontend or backend application source files were modified in this iteration. The behavior change is driven exclusively by the addition of row 7 to `runs/goal-session-mcp-loop/state/certified-claims.jsonl` by the pre-build referee gate. All display components (`ClaimRow`, per-horizon chip strip, `resolveCohortEvidence`, `factorHorizonBadges`, `_labs.tsx`, `evidence/page.tsx`) are byte-identical to their prior-iteration state.

**Shared component: `ClaimRow` on `/evidence`**

- Prior features using this component: J-01 (leadership_score row), J-02 (Breakout-watch row), J-03 (ma_stack FAIL row), J-04/J-05 (vcp_contraction h20 row), J-07 (vcp_contraction h60 row), J-08 (rs_spy_3m×high_proximity combination row).
- Change applied this iteration: additive data only (new row 7 appended to the ledger); the `ClaimRow` component and the `GET /api/evidence` endpoint are byte-identical.
- Regression risk: LOW. Browser QA explicitly re-verified all 6 prior rows in UT-05 (all present in correct order with correct values and "Backs" links, PASS).

**Shared component: per-horizon evidence chip strip on `/research/factor-lab` (`factorHorizonBadges`, `_labs.tsx`)**

- Prior features using this component: J-06 (vcp_contraction h20 chip), J-07 (vcp_contraction h60 chip).
- Change applied this iteration: none — `apps/frontend/lib/factor-lab-evidence.ts` and `apps/frontend/app/research/_labs.tsx` are byte-identical.
- Regression risk: LOW. Browser QA explicitly re-verified vcp_contraction h20 and h60 chips in UT-11 (`data-proven="true"` on both, correct hrefs, PASS).

**Shared component: `resolveCohortEvidence` matcher in `evidence.ts`**

- Prior features using this function: J-06, J-07 (factor cohort badge resolution).
- Change applied this iteration: none — `apps/frontend/lib/evidence.ts` is byte-identical.
- Regression risk: LOW. The existing unit test suite (37 prior cases) passed unmodified alongside the 2 new J-09 cases (39 total, all PASS).

**`/stocks` page and per-stock inline score badges**

- Prior features: J-01 (leadership_score inline badges), J-02 (Breakout-watch setup badge), J-03 (signal-less no-leak guard).
- Change applied this iteration: none — `rs_spy_3m` is not in the three score columns; `proven_signals` stays `{leadership_score}`.
- Regression risk: LOW. UT-12 confirmed column headers unchanged (LEADERSHIP, ENTRY QUALITY, RISK) and zero occurrences of `rs_spy_3m` in /stocks HTML. UT-13 confirmed `proven_signals` keys = `["leadership_score"]` only.

---

## UI vs Backend Parity

| Backend capability | UI exposure | Status |
|---|---|---|
| 7th canonical ledger row: `rs_spy_3m` D10 h60, PASS, holdout +21.34%, divisor 7, p=0.0004998, register 2026-07-01 | `/evidence` 7th `ClaimRow`, all fields rendered and byte-matching the ledger (UT-02 PASS) | Fully surfaced |
| `resolveCohortEvidence` match for `rs_spy_3m` h60 | `/research/factor-lab` h60 chip reads "Proven" with href deep-link (UT-07 PASS) | Fully surfaced |
| "Not yet proven" at uncertified `rs_spy_3m` horizons (h1/h5/h10/h20) | Four h1/h5/h10/h20 chips all read "Not yet proven" with `data-proven="false"` (UT-09 PASS) | Correctly surfaced (honest non-proven marking) |
| `proven_signals` = `{leadership_score}` (rs_spy_3m is signal-less) | `/stocks` unchanged; proven_signals API key contains only leadership_score (UT-13 PASS) | Correctly NOT surfaced (intentional non-signal) |
| Backend graceful error state | `/evidence` shows "Backend unavailable" with informative message and no fabrication (UT-04 PASS) | Correctly surfaced |

No backend capability is missing a UI access point. The `user-visible-changes.md` "Not Visible Yet" section is empty.

---

## Flags

### Hidden Capabilities

None.

### Undiscoverable Capabilities

None.

### Potential Regressions

None. No application source files were modified; all prior journeys (J-01 through J-08) were re-verified in browser QA with PASS verdicts.

### Visual Consistency

No new components, colors, effects, or layout were introduced. This iteration reuses the existing `ClaimRow` (verdict-status Badge + `<dl>` fields) and the existing per-horizon chip strip (compact `{h}d {status}` pills with `data-factor`/`data-horizon`/`data-proven` attributes), both established in prior iterations (J-05 through J-08). The frontend handoff explicitly confirms design-system conformance: "Reuses the EXISTING components unchanged... No new components, colors, effects, or layout."

The new "Proven" state for `rs_spy_3m` h60 uses the same proven-checkmark pill style as the prior `vcp_contraction` h20/h60 "Proven" chips — visually indistinguishable in treatment, which is intentional consistency. The "Not yet proven" states for the remaining horizons use the same muted styling as all other uncertified horizons across the factor lab.

---

## Recommendation

No action required.

All new capabilities are properly exposed, discoverable within 2 clicks of the main nav, and clearly labeled for non-technical users. No frontend source files were modified, eliminating source-code-introduced regression risk. Browser QA verified 13/13 tests as PASS, including explicit regression checks on all 6 prior evidence rows (UT-05), prior factor-lab "Proven" chips (UT-11), the /stocks badge set (UT-12), and the proven_signals guard (UT-13). The end-to-end audit trail (factor lab → Proven badge → evidence row → back) completes without dead ends (UT-10).

The documented yellow flag (rs_spy_3m h60 holdout edge +0.2134 being implausibly large) is a statistical audit concern for the coherence-auditor and phase auditor, not a UX discoverability issue. The value is correctly and honestly displayed in the Evidence row.
