# Phase goal-mcp-loop-iter-11 — UX Regression Review

**Date:** 2026-07-01

**Verdict:** UX-REGRESSION-PASS

---

## New Capability Discoverability

### Capability 1: Per-horizon evidence chip strip on `/research/factor-lab`

**Navigation path:** Sidebar → "Research" → "Factor Lab" (2 clicks from home). The Evidence column is immediately visible in the factor-lab table on page load — no expansion, no secondary nav, no scroll required to reach the column header.

**Label:** The column header changed from "Evidence (D10 · 20d)" to "Evidence (D10 · per horizon)". The new label is clear to any Factor Lab user: it signals that the column now spans all five served horizons (1d/5d/10d/20d/60d). Browser QA UT-03 confirmed the exact text.

**Discovery within 2 clicks:** Yes. The chip strip for each factor row is in column 2 (right after the Factor name). The five chips ("1d Not yet proven" / "20d Proven" / "60d Proven" etc.) are visible without expansion for each row.

**Visual feedback:** Clicking the "60d Proven" chip navigates to `/evidence#factor-vcp_contraction-d10-h60` (UT-06 PASS). The chip strip uses hover/focus/active states on proven chips; non-proven chips are intentionally non-interactive (no link). The `stopPropagation` guard prevents the chip click from toggling the row's decile-grid expander (iter-5 hazard, preserved).

**Assessment: discoverable, label clear, feedback confirmed.**

---

### Capability 2: vcp_contraction h60 "Proven" deep-link badge

**Navigation path:** `/research/factor-lab` → find `vcp_contraction` row → the "60d Proven" chip is a clickable link. Alternatively: `/evidence` → locate the 5th claim row directly from the sidebar (1 click). Both paths land the user at the h60 certified claim.

**Label:** The chip reads "60d Proven" — consistent with the existing "20d Proven" pattern and with the stated design direction (calm, data-dense, never hype). The `data-proven="true"` and `data-horizon="60"` attributes are not visible to ordinary users but power the per-horizon selection.

**Discovery:** Discoverable within 2 clicks from home via either route.

**Assessment: discoverable, label clear.**

---

### Capability 3: New h60 claim row on `/evidence`

**Navigation path:** Sidebar → "Evidence" (1 click from home). The new row is the 5th claim in the ledger list, auto-rendered by the existing `ClaimRow` component. No expansion needed.

**Label:** Row title "vcp_contraction — top decile (D10)", subtitle "Out-of-sample edge — factor top decile · 60-day hold". The "· 60-day hold" suffix clearly distinguishes this row from the existing h20 row ("Out-of-sample edge — factor top decile" with no suffix). The horizon=60 hypothesis chip further disambiguates. UT-05 confirmed all required fields render (PASS, +8.91%, +8.91% vs SPY, registration date, "Pending" forward-walk, "Backs: Research factor lab →" linkback).

**Assessment: discoverable in 1 click, label self-distinguishing, all fields present.**

---

## Regression Risk

### `_labs.tsx` — shared by J-06 (vcp_contraction h20 badge, iter-8)

The per-horizon chip strip modification replaced the single-chip render with a loop over `data.horizons`. The h20 chip is rendered as part of the loop with the same `resolveCohortEvidence` call and the same `stopPropagation` deep-link guard. Browser QA UT-10 PASS confirmed: `[data-factor="vcp_contraction"][data-horizon="20"]` → `data-proven="true"`, href `/evidence#factor-vcp_contraction-d10-h20`. **Risk: LOW — explicitly regression-tested and passing.**

### `_labs.tsx` — shared by J-06 (leadership_score h20 badge, iter-8)

The `resolveCohortEvidence` matcher was not special-cased. leadership_score h20 still reads "Proven" and links to `/evidence#signal-leadership_score`. UT-11 PASS confirmed. **Risk: LOW — explicitly regression-tested and passing.**

### `lib/evidence.ts` — shared by J-05 (all prior evidence rows) and J-01/J-02/J-03 (stocks badges)

The only change to `evidence.ts` was the `claimSurface` subtitle disambiguation for h60 (adding "· 60-day hold" to the h60 branch only; the h20 branch is preserved byte-identical via the new `DEFAULT_FACTOR_COHORT_HORIZON = 20` constant). The `resolveEvidenceStatus`, `evidenceAnchor`, `cohortClaimId`, and `claimAnchorId` functions were not changed. The `proven_signals` field is confirmed `{leadership_score}` (byte-identical). UT-12 and UT-13 (browser QA PASS) confirmed the four prior claim rows are unchanged and the h20 subtitle contains no "60-day" text. **Risk: LOW — explicitly regression-tested and passing.**

### `/evidence` page — shared by J-05 (all prior certified-claim rows, iters 1/3/7/8)

The new h60 row is purely additive — rendered by the same `ClaimRow` component used for all prior rows. The Breakout-watch row (J-04), ma_stack row, leadership_score row, and vcp_contraction h20 row are all confirmed present with correct statuses by UT-12. **Risk: LOW — explicitly regression-tested and passing.**

### `/stocks` leaderboard (J-01/J-02/J-03, iter-1) — not explicitly browser-tested this iteration

No code in `app/stocks/page.tsx` or `components/evidence-status-badge.tsx` was touched in iter-11. The h60 claim carries no `signal` key and therefore cannot appear in `proven_signals`, which is confirmed `{leadership_score}` by a live API check. The signal-less design makes a `/stocks` badge regression architecturally blocked without a code change. However, no explicit browser screenshot of the `/stocks` page was captured in iter-11's browser QA. This is a minor observability gap, not a functional concern. **Risk: LOW — protected by the signal-less claim design and unchanged code surface; note the absence of explicit browser evidence.**

---

## UI vs Backend Parity

| Backend capability | UI exposure | Status |
|---|---|---|
| `GET /api/evidence` serves 5 claims (new h60 entry) | `/evidence` 5th claim row auto-rendered by `ClaimRow` | Fully surfaced |
| h60 claim data: holdout +8.91%, SPY +8.91%, p=0.00049975, status=PASS | `/evidence` h60 row fields confirmed verbatim (UT-05 PASS) | Fully surfaced |
| h60 PASS claim matched by `resolveCohortEvidence` | Factor Lab h60 chip reads "Proven" with correct deep-link (UT-04 PASS) | Fully surfaced |
| Uncertified horizons h1/h5/h10 (no canonical entry) | Factor Lab chips read "Not yet proven" (UT-07 PASS) | Correctly not surfaced |
| `proven_signals == {leadership_score}` (signal-less h60 claim excluded) | No new inline `/stocks` badge from h60 claim | Correctly not surfaced |
| `GET /api/evidence` prior 4 entries unchanged | `/evidence` prior 4 rows unchanged (UT-12 PASS) | Preserved |

The user-visible-changes report states: "None. All capabilities implemented in this iteration are fully surfaced in the UI." This is confirmed. The intentional non-surfacing (h60 claim not appearing on `/stocks`) is correct per the anti-goal contract.

---

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None.

### Potential Regressions
None at material risk. All shared-component regression paths were explicitly browser-tested (UT-10 through UT-13) and passed. The sole observability gap (no `/stocks` browser screenshot in iter-11) is low-risk given the architectural signal-less safeguard and zero diff on the stocks surface.

### Visual Consistency
- All new UI elements reuse existing design-system components: the `Badge` component (`accent` variant for "Proven", `default` for "Not yet proven"), `lucide-react` `ShieldCheck`/`Shield` icons, the `num` mono class, and Next.js `<Link>` — no raw HTML, no invented hex colors, no new visual effects.
- The chip strip extends the existing Evidence column in-place; no layout rewrite, no new page, no nav change.
- The new h60 claim row on `/evidence` renders via the identical `ClaimRow` component used by all four prior rows — visually indistinguishable from its siblings except by content.
- The design-dense, calm, "proven / not yet proven" evidence-first style is consistent across both affected surfaces and matches the prior-phase visual baseline from iter-8.
- No arbitrary CSS values observed; all styling deferred to existing token classes (per iter-11 frontend handoff: "no arbitrary colors").

---

## Recommendation

No action required. The UX evolution is correct and complete for this iteration:

1. Both new surfaces (`/research/factor-lab` per-horizon chips, `/evidence` h60 row) are reachable within 2 clicks from home via clear sidebar navigation.
2. All 15 browser QA tests passed, covering the new capability (UT-01 through UT-09, UT-14, UT-15) and every required regression guard (UT-10 through UT-13).
3. No backend capability is hidden or undiscoverable — the signal-less h60 claim is intentionally absent from `/stocks` and that is the correct, anti-goal-compliant behavior.
4. Design system conformance is maintained; visual style is consistent with the iter-8 baseline.
5. The only advisory note — no explicit `/stocks` browser screenshot in the iter-11 test run — is low-risk given that no stocks-surface code was modified and the h60 claim is architecturally prevented from entering `proven_signals`.
