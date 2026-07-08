# Phase goal-mcp-loop-iter-22 — UX Regression Review

**Date:** 2026-07-08

**Verdict:** UX-REGRESSION-FAIL

---

## New Capability Discoverability

| Capability | Path from home | Clicks | Label clarity | Visual feedback | Verdict |
|---|---|---|---|---|---|
| Per-series vendor label on Dashboard chart legend/tooltip | Dashboard `/` → "Regime × phase cross-view" card (first chart below the summary cards) | 0 | Clear — vendor text appended in parentheses/`·` suffix directly on the series name (e.g. "S&P 500 Index (^SPX) (Stooq)"); QA (UT-04/UT-05) confirms byte-exact rendering, all 3 vendor categories present | Immediate, faint-gray inline text, no interaction required | **Discoverable — PASS** |
| `/data` "Index & benchmark data provenance" panel | Dashboard `/` → sidebar "Data Manager" → scroll to below "Macro feed" | 1 | Self-explanatory: title + hint text quoting the exact data contract ("the same GET /api/indexes payload the Dashboard chart reads"); QA (UT-19) independently timed this at exactly 1 click | Dedicated loading skeleton / error alert / empty state, independent of the rest of the page | **Discoverable — PASS** |
| **Deep `^SPX`/`^NDX`/`^DJI`/`^VIX` benchmark history (1996–2018) on the Dashboard chart** — the capability that gives this iteration its name ("Deep... index/macro context") and is DoD item (a) | Dashboard `/`, same chart, same pane | Technically 0, but **not reachable in practice** | N/A — nothing labels or hints at the hidden range | **None** — no scrollbar, minimap, "view full history" control, or default/max-zoom-out state exposes it | **HIDDEN — FAIL** |

The third row is the load-bearing finding of this review. Per `reports/phase-goal-mcp-loop-iter-22-ui-test-results.md` (UT-03, FAIL, P1 happy-path, reproduced 3× at 1440×900 plus independently re-checked at 1920×1080 and 3840×1200):
- The chart's freshly-loaded default view spans only ~2018–2026 (1440×900) or ~2015–2026 (1920×1080) — decades short of the committed 1996-01-02 start that `meta.json` and the `/data` panel both correctly disclose.
- The library's effective maximum zoom-out (400 synthetic wheel events) lands on the exact same boundary as the default — it is not merely under-zoomed, it is capped there.
- The 1996 data **does** render correctly once a user drags the chart ~10 full-pane-widths toward the past — but there is no scrollbar, minimap, position indicator, "jump to start"/"view full history" button, or any other affordance suggesting this is possible or how far to go. The card's only control is a "Hide" button.
- QA's root-cause read (`apps/frontend/components/phase-cross-view-chart.tsx:315`, `chart.timeScale().fitContent()` colliding with `lightweight-charts`' minimum bar-spacing floor against ~7,674 daily bars in a ~1,000px pane) indicates this is a genuine rendering constraint, not a data problem — `GET /api/indexes?full=true` and the `/data` panel both confirm the underlying data is correct and complete.

This is precisely a "hidden capability" under this review's own test: the feature exists in the frontend (it is on the canvas, reachable by drag) but has **no navigation or interaction path a normal user could discover**. It is also the single named DoD acceptance criterion ((a): "a deep benchmark line (^SPX) that extends before SPY's 2005 start") that browser-qa-agent's own verdict rule already marks as the reason for its overall FAIL.

**Documentation accuracy note:** `reports/phase-goal-mcp-loop-iter-22-user-visible-changes.md` (written before the browser-qa-agent ran) states the deep lines "render automatically on page load... no new click or control is required." Live QA (UT-03) has since disproven this specific claim. That document should not be read as an accurate record of this capability until corrected — it currently overstates what a user actually sees.

---

## Regression Risk

| Shared component | Prior feature(s) served | This iteration's change (verified via `git diff`) | Risk |
|---|---|---|---|
| `apps/frontend/components/phase-cross-view-chart.tsx` (`PhaseCrossViewCard`) | J-97/J-101a (the Dashboard's sole consolidated chart, per the `app/page.tsx` code comment at line ~157); adjacent to J-04 (Market Regime card) and J-98 (dashboard reorg) | Additive only: `LINE_PALETTE_VARS` array extended 5→10 (existing 5 entries unchanged, same order); tooltip's per-line object gains an additive `vendor` field; legend line gains an additive vendor `<span>`. No change to the phase/severity/pBear pane or its data fetch. | **Low — empirically confirmed.** QA UT-01 (chart renders, zero console errors), UT-13 (5 original ETF lines/colors/order byte-identical; extensive pan/zoom/hover exercised without error), UT-15 (Regime card + `/evidence` link intact) all PASS on this exact shared surface. |
| `apps/frontend/app/data/page.tsx` | J-12 (universe count), J-13 (per-date availability legend + 548-symbol Fetch pool), plus Dataset coverage / Rebuild snapshots / Universe resolution / membership timeline / Missing-data diagnostic panels | Pure insertion: one new import + one new `<IndexVendorPanel />` line immediately after the existing `<MacroFeedPanel />`. No existing panel's markup, props, or order changed. `components/availability-heatmap.tsx` (J-13's own component) is untouched — absent from this iteration's `git diff`/`git status` entirely. | **Low for code; see coverage gap below.** QA UT-02 (full page renders, all pre-existing panels including "Per-date availability" present with real data) and UT-16 (universe count unchanged, J-12) PASS. |
| `apps/frontend/app/globals.css` | All pages using CSS custom properties | Purely additive: 4 new tokens (`--chart-orange`/`--chart-lime`/`--chart-blue`/`--chart-pink`); confirmed via full diff that no pre-existing token's value changed. | **None.** |
| `apps/frontend/lib/api.ts` (`IndexSeries` type) | Any typed consumer of `/api/indexes`, including the dead-code `major-indexes-card.tsx` | Additive optional fields (`vendor: string \| null`, `first: string`) | **None.** `tsc --noEmit` clean (dev handoff); no console errors observed on any tested page. |

**Coverage gap (process, not a confirmed functional regression):** the phase spec and plan both list J-13 ("`/data` availability legend + 548 reflection unchanged") as required-still-passing, alongside J-01/J-03/J-04/J-05/J-10/J-12, and the plan explicitly calls for it to be replayed live. The QA results table has a named, dedicated test for each of the other six (UT-14→J-01, UT-18→J-03/J-05, UT-15→J-04, UT-17→J-10, UT-16→J-12), but no equivalent dedicated test exercises J-13's specific acceptance criteria (the fill-vs-snapshot legend distinction, the hover-tooltip explanation, or the 548-symbol Fetch pool) — UT-02 only confirms the "Per-date availability" panel is present and populated as part of a generic full-page smoke check. Since `availability-heatmap.tsx` is unmodified by this iteration, the underlying code risk is low, but J-13 was not demonstrably live-replayed with the same rigor as its six peers, which is a gap against the plan's own instruction.

---

## UI vs Backend Parity

| Backend capability (this iteration) | Surfaced in UI? | Where |
|---|---|---|
| `vendor` field per index series | Yes | Dashboard chart legend + tooltip; `/data` provenance panel |
| `first` field (honest first-bar date) | Yes | `/data` provenance panel "First bar" column |
| `^SPX`/`^NDX`/`^DJI` deep price history loaded into `daily_prices` | **Partial** | Correctly disclosed in the `/data` panel (byte-matches `1996-01-02`), but the flagship surface this data was loaded for — the Dashboard chart's visible line — is not reachable in its default/practical state (see Hidden Capabilities above). The data reached one of its two intended UI surfaces, not both. |
| `^VIX`/`^TNX` overlay lines | Same partial-parity caveat | `/data` panel: fully visible. Chart: present but unreachable by default. |
| `load_missing_index_symbols.py` (CLI loader) | No — by design | Operator-only tooling; honestly disclosed in `user-visible-changes.md`'s "Not Visible Yet" section; no user-facing trigger is expected. Correctly scoped, not a gap. |
| Vendor/palette fix applied to `index-regime-chart.tsx` / `major-indexes-card.tsx` | No — dead code | Transparently disclosed in `user-visible-changes.md`: this pair has zero route reachability (confirmed independently in `ui-surface-map.md` via a repo-wide import grep — an earlier iteration already replaced it with `PhaseCrossViewCard`). Pre-existing orphan, not introduced by this iteration, not a new gap. |

Every new backend field is wired to a rendering call site — this is not a case of "backend built, nothing shown." The gap is narrower: one of the two intended display surfaces for the deep-history capability (the chart) doesn't practically expose it, while the other (the `/data` table) does. That specific gap is captured under Hidden Capabilities, not counted twice here.

---

## Flags

### Hidden Capabilities
- **Deep 1996–2018 benchmark history on the Dashboard "Regime × phase cross-view" chart** (`/`, `phase-cross-view-chart.tsx`). The data is present and correctly loaded (confirmed via `GET /api/indexes?full=true` and the `/data` panel), and does render once a user performs ~10 undocumented full-pane drag gestures — but there is no navigation control, scrollbar, minimap, "view full history" button, or default/max-zoom state that exposes it. This is DoD item (a) and the specific reason browser-qa-agent's own verdict is FAIL (UT-03).

### Undiscoverable Capabilities
- None beyond the Hidden Capability above. The chart-legend vendor labels and the `/data` provenance panel are both reachable in 0–1 clicks with self-explanatory labels (QA UT-04/UT-05/UT-19).

### Potential Regressions
- None confirmed as broken. `phase-cross-view-chart.tsx` and `app/data/page.tsx` are both touched, but their diffs are narrowly additive and the shared surfaces they serve (J-97/J-101a, J-04, J-12) were live-verified without incident (UT-01, UT-13, UT-15, UT-02, UT-16).
- **J-13 replay coverage gap**: no dedicated live test for J-13's specific acceptance criteria (availability legend fill-vs-snapshot distinction, hover tooltip, 548-symbol Fetch pool) appears in the QA results, unlike its six required-still-passing peers. Code risk is low (component unmodified), but the plan's explicit instruction to replay it live is not demonstrably fulfilled in the current evidence set.

### Visual Consistency
- The new `/data` panel (`index-vendor-panel.tsx`) matches established conventions exactly: same `Card`/`PanelTitle` structure as neighboring panels (e.g. `MacroFeedPanel`), `Badge variant="default"` for the vendor tag, and exclusively semantic Tailwind tokens (`text-text-faint`, `text-text-muted`, `border-border`, `bg-surface-2`, `border-warn`/`text-warn` for its error state) — zero arbitrary hex values or inline styles (confirmed by direct source read and grep for `#[0-9a-f]{3,6}`/`style={{`, both empty).
- The 4 new chart-line tokens (`--chart-orange`/`--chart-lime`/`--chart-blue`/`--chart-pink` in `globals.css`) were derived via the project's documented `dataviz` skill method (OKLCH hue-gap search + CVD-separation validation script) and added additively — the full diff confirms no pre-existing token's value changed.
- No visual-consistency issues found.

---

## Recommendation

1. **Blocking:** fix the Dashboard chart's default/reachable view so the committed 1996 history is actually visible without undocumented drag gestures before this iteration is treated as having delivered J-14 — e.g., an explicit `setVisibleRange`/`setVisibleLogicalRange` call after `fitContent()`, a `minBarSpacing` override, or older-bar sampling on the cross-view chart (the `/stocks/{ticker}` detail chart already does the latter, per QA UT-17's "older bars weekly-sampled" caption, and may offer a directly reusable pattern). This is the specific defect behind both browser-qa-agent's FAIL and this report's FAIL.
2. Correct `reports/phase-goal-mcp-loop-iter-22-user-visible-changes.md`'s claim that the deep lines render "automatically on page load... no new click or control required" — live QA has disproven this and it should not stand as the shipped record.
3. Non-blocking: capture an explicit J-13 live replay (legend fill-vs-snapshot distinction, hover tooltip, 548-pool Fetch) in QA evidence to match the rigor already given to its six peer required-still-passing journeys — the diff suggests low risk, but the plan's instruction to replay it live is not yet demonstrably closed out.
4. No action needed on vendor-label discoverability, the `/data` provenance panel, or visual consistency — all verified solid by both this review and live browser QA.
