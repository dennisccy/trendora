# Phase goal-mcp-loop-iter-8 — UX Regression Review

**Date:** 2026-06-30

**Verdict:** UX-REGRESSION-PASS

---

## New Capability Discoverability

### Capability 1: vcp_contraction "Proven" evidence badge on `/research/factor-lab`

- **Navigation path:** Sidebar → Research (1 click) → Factor Lab card (2 clicks) → "Evidence (D10 · 20d)" column visible in the factors table without row expansion or horizontal scrolling.
- **Clicks from home:** 2 (within acceptable threshold).
- **Label clarity:** "Proven" with a ShieldCheck icon in accent color is clear and unambiguous. The column header "Evidence (D10 · 20d)" communicates the scope (top decile, 20-day horizon) without requiring technical knowledge.
- **Visual feedback:** Accent-colored chip (`border-accent bg-surface-2 text-accent`) with `cursor-pointer` on the vcp_contraction row. UT-18 confirms the column and badge are above the fold and visible at 1681 px viewport width without any extra steps.
- **Assessment:** Discoverable. UT-03 and UT-18 confirm correct styling and in-viewport visibility.

### Capability 2: vcp_contraction claim row on `/evidence`

- **Navigation path:** Sidebar → Evidence (1 click) → scroll down to the 4th claim row (the row is below the fold at viewport height 1308 px; the page offset is ~991 px per UT-06).
- **Clicks from home:** 1 (Evidence is a direct sidebar link); the row requires a scroll, but it is not hidden.
- **Label clarity:** Title "vcp_contraction — top decile (D10)" is honest and derived from the claim selectors. Subtitle "Out-of-sample edge — factor top decile" is a plain-language description. No buy/sell or return-promise language.
- **Visual feedback:** The row renders all five fields (holdout edge, p-value, control label "vs SPY", registration date, forward-walk status) and the "Backs: Research factor lab →" linkback. UT-05 confirms all fields present and byte-matching `GET /api/evidence`.
- **Assessment:** Discoverable. Anchor-based deep-link (`/evidence#factor-vcp_contraction-d10-h20`) lands the row directly in-viewport without scrolling (UT-06 PASS).

### Capability 3: Round-trip deep-link between factor lab and evidence ledger

- **Factor lab → evidence:** Click the vcp_contraction "Proven" badge → navigates to `/evidence#factor-vcp_contraction-d10-h20`; row scrolls into view (UT-04 PASS). Click does NOT toggle the factor row expansion (UT-17 PASS — `stopPropagation()` guard works correctly for the "Proven" link).
- **Evidence → factor lab:** Click "Backs: Research factor lab →" on the vcp_contraction row → navigates to `/research/factor-lab` (UT-07 PASS).
- **Assessment:** Both directions of the cross-page round-trip work and are discoverable within 1 additional click from either page.

### Capability 4: Updated framing on the ma_stack FAIL row on `/evidence`

- The ma_stack row now carries an honest factor title ("ma_stack — top decile (D10)"), the subtitle "Out-of-sample edge — factor top decile", and a "Backs: Research factor lab →" linkback. Verdict chip still reads "Not yet proven" (FAIL — no regression).
- Previously this row had no title and no linkback. The framing improvement is discoverable without any navigation change (UT-12 PASS).
- **Assessment:** Enhancement to existing content. No navigation path change required; users visiting `/evidence` naturally see the updated row.

---

## Regression Risk

### Shared component: `apps/frontend/lib/evidence.ts`

**Prior features served:** J-01/J-02/J-03 (score-based evidence status on `/stocks` and `/stocks/{ticker}`), J-04 (regime label + Breakout-watch framing on `/evidence`), J-05 (leadership score row + "Backs: Stocks leaderboard →" on `/evidence`).

**Current change:** Added `resolveCohortEvidence`, `cohortClaimId`, `cohortEvidenceAnchor`, `claimAnchorId`, `factorCohortFromClaim`, `CohortEvidenceStatus`, `FactorCohort`, and the `claimSurface` factor branch. All existing exports (`resolveEvidenceStatus`, `regimeLabel`, prior `claimSurface` score/event-study branches) are byte-identical per dev handoff and unit-asserted by 10 new evidence test cases.

**Risk level:** Low. Changes are purely additive. Browser QA confirms no regression:
- UT-15 PASS: `/stocks` Leadership "Proven", Entry Quality + Risk "Not yet proven", no vcp_contraction mention.
- UT-16 PASS: `/stocks/{ticker}` Leadership proof drill-down renders OOS test, SPY control, and claim id/date.

### Shared component: `apps/frontend/app/evidence/page.tsx` (`ClaimRow`)

**Prior features served:** J-04 (Breakout-watch regime row), J-05 (leadership_score score row, "Backs: Stocks leaderboard →", `signal-leadership_score` anchor).

**Current change:** `ClaimRow` derives its row `id` from the shared `claimAnchorId` helper. For signal-bearing rows this returns `signal-${signal}` (unchanged); for signal-less factor cohorts it returns the new cohort anchor; for the event-study row it returns `undefined` (unchanged).

**Risk level:** Low. The shared `claimAnchorId` contract preserves the existing `signal-leadership_score` anchor for the leadership row and leaves the event-study row without an id.
- UT-13 PASS: `/evidence#signal-leadership_score` scrolls the leadership row into viewport; linkback reads "Backs: Stocks leaderboard →".
- UT-14 PASS: Breakout-watch row unchanged — "Regime: Risk-on" + "Backs: Research event-study lab →".

### Shared component: `apps/frontend/app/research/_labs.tsx` (`FactorLabPage` / `FactorsTable`)

**Prior features served:** Research factor lab prior to this iteration (no J-01–J-05 journeys depend on `_labs.tsx` directly, but the factor lab is an established product surface).

**Current change:** `FactorLabPage` now fetches the evidence payload via the existing `fetchEvidence()` client (fail-safe: empty on error → all badges "Not yet proven", no crash). `FactorsTable` adds the "Evidence (D10 · 20d)" column and the `FactorEvidenceBadge` per row. Column colSpan updated.

**Risk level:** Low. The fetch is additive (new call alongside existing data fetches). Fail-safe empty state verified by UT-11 (all 11 factor rows show "Not yet proven", no crash, no JS error when the evidence fetch is rejected). Existing factor-row expand/collapse behavior preserved (UT-09 partial note — see Flags section).

---

## UI vs Backend Parity

| Backend Capability | UI Exposure | Parity |
|---|---|---|
| 4th certified-claims ledger entry (vcp_contraction D10 h20, PASS, +3.33%, p=0.01149) served by existing `GET /api/evidence` | Rendered as a 4th claim row on `/evidence` with all required fields | Complete |
| `claim.proven == true` for the vcp_contraction entry in `claims[]` | Displayed as "Proven" badge (accent, ShieldCheck) on the factor-lab top-decile summary row for vcp_contraction | Complete |
| `claim.proven == false` for the ma_stack FAIL entry in `claims[]` | Displayed as "Not yet proven" badge (muted, outline Shield, no link) on the ma_stack row | Complete |
| `proven_signals == {leadership_score}` invariant (no vcp_contraction signal) | No vcp_contraction inline badge on `/stocks` (UT-15 confirms `document.body.innerText.includes('vcp_contraction') == false`) | Complete |
| `claimSurface` factor branch (honest title, honest subtitle, linkback to `/research/factor-lab`) | Visible on the vcp_contraction claim row and the ma_stack claim row on `/evidence` | Complete |
| Cohort anchor (`#factor-vcp_contraction-d10-h20`) | Set as row `id` on the vcp_contraction `ClaimRow`; the factor-lab "Proven" badge href points to this anchor | Complete |

The user-visible-changes report states "Not Visible Yet: None." All backend/test-only changes (the frontend unit test and the backend confirming test) have no UI surface impact by design. Parity is complete.

---

## Flags

### Hidden Capabilities

None.

### Undiscoverable Capabilities

None. All new capabilities are reachable in ≤2 clicks from the home page. The evidence badge is above the fold on `/research/factor-lab` (UT-18 PASS). The `/evidence` vcp_contraction row is below the fold but has a working anchor deep-link surfaced by the "Proven" badge click.

### Potential Regressions

None confirmed. All five required-still-passing journeys (J-01 through J-05) have explicit browser regression tests (UT-13 through UT-16 and UT-15), all of which PASS. The shared `lib/evidence.ts` changes are additive and unit-asserted.

### Visual Consistency

- **Badge chip:** The "Proven" chip uses `border-accent bg-surface-2 text-accent` (design system tokens); the "Not yet proven" chip uses `border-border text-text-faint` (muted design system tokens). Both mirror the existing `components/evidence-status-badge.tsx` pattern. No arbitrary values.
- **Link style:** The "Proven" badge is an `<a>` element with the accent color; confirmed by UT-03 CSS class inspection.
- **Layout:** No structural changes. The new "Evidence (D10 · 20d)" column sits to the right of existing statistics columns. The `/evidence` claim rows use the existing vertical Card list layout unchanged.
- **Icon usage:** ShieldCheck for "Proven" (filled), Shield for "Not yet proven" (outline) — consistent with the established evidence-status-badge pattern.
- **Minor UX note (P2, non-blocking):** UT-09 found that clicking a "Not yet proven" badge DIV propagates the click event to the parent factor-row toggle handler, causing the row to expand. The "Not yet proven" badge is a non-interactive `<div>` (no link, no navigation), so the row expansion is the parent row's existing click behavior leaking through. Only the "Proven" `<Link>` has a `stopPropagation()` guard (iter-5 nested-interactive lesson). This inconsistency — clicking a passive chip causes an unintended row toggle — is a P2 UX gap on 9 of the 11 factor rows. It does not affect discoverability or any journey's pass criteria (browser QA overall verdict: PASS).

---

## Recommendation

No blocking action required.

**Optional hardening (P2):** Add `e.stopPropagation()` and `e.preventDefault()` (for keyboard events) to the "Not yet proven" `<div>` badge wrapper in `FactorEvidenceBadge` in `apps/frontend/app/research/_labs.tsx`. This would prevent the unintended row expansion when a user clicks a passive "Not yet proven" chip (UT-09 partial fail). The fix is cosmetic — it does not gate any journey — but would make all 11 badge chips behave consistently.
