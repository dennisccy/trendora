# Phase goal-mcp-loop-iter-19 — UX Regression Review

**Date:** 2026-07-07

**Verdict:** UX-REGRESSION-PASS

## Summary

This iteration is a fix-and-verify pass (no net-new capability, per the phase spec's own "Blueprint
conformance" section) that repairs the exact regression the iter-18 UX-regression review caught and
FAILed: the `/stocks` leaderboard's Sector-sort crash on the broadened ~78%-null-sector pool, plus the
`/api/data` prefill OOM that blocked verification of it. I independently re-derived every claim in
`user-visible-changes.md` and `ui-surface-map.md` against the actual working tree (not just the
narrative reports) — reading the real diffs for all three touched pages, re-running `tsc --noEmit`
myself, grepping the whole frontend for every other `.sector` consumer, reading the new `error.tsx` /
`global-error.tsx` sources, reading the new backend `Bar` record and its docstring, confirming
`test_bar_cache.py` is a real 401-line/13-test suite (not a stub), and confirming `sidebar.tsx` is
byte-unchanged with all 11 nav entries intact. Everything checks out: the fix is surgically scoped, the
new capabilities are discoverable exactly where users would already look, no navigation changed, and no
prior-phase journey shows a regression signal. One residual verification gap — noted below and already
self-disclosed by the browser-qa-agent — is flagged for the auditor's awareness but does not change the
verdict.

## New Capability Discoverability

| Capability | Path from home | Clicks | Label | Visual feedback | Verified? |
|---|---|---|---|---|---|
| `/stocks` Sector column sort (restored, no longer crashes) | Dashboard → Stocks (1) → click "Sector" column header (existing control, same location since iter-2) | 1 (already on the page) | "Sector" — unchanged, unambiguous | `aria-sort`/arrow-icon direction indicator; table visibly re-orders | **Yes** — browser QA UT-02/UT-03: clicked ascending then descending, confirmed genuine re-ordering (not a no-op) and no crash, nav fully intact both times. This is the exact click that crashed the whole app in iter-18. |
| "Unassigned" option in the Sector filter dropdown (new value, existing control) | Dashboard → Stocks (1) → open "Filter by sector" dropdown (existing control) | 1 (already on the page) | "Unassigned" — plain, non-technical, immediately understandable; never a blank/`null` option | Filtered row count updates live ("422 / 541") | **Yes** — UT-04 confirms exact alphabetical position (between Technology/Utilities) via a full DOM option dump; UT-05 confirms the filtered set is byte-exact (422 rows, all Unassigned) against a direct `/api/stocks` count. |
| `/stocks/{ticker}` and `/scanner-runs/{runId}` sector display (now "Unassigned" instead of blank) | Reached via existing row-click / existing nav (1-2 clicks, unchanged paths) | 1-2 (unchanged) | "Unassigned" — same label, same helper (`sectorLabel`), consistent everywhere it appears | Chip/cell renders text instead of a blank space | **Yes** — UT-08 (`/stocks/GL` shows "Extended · Unassigned · as of..."), UT-09 (NVDA unaffected, still "Technology"), UT-11 (`/scanner-runs/410`, 0 blanks across all 541 rows). |
| `/data` reliability (no OOM/hang on first cold load or concurrent load) | Dashboard → Data Manager (1) — same page, no new UI | 1 (unchanged) | N/A — no new copy, existing page | Page loads with real numbers instead of hanging/crashing | **Partially** — UT-12/13 confirm a **warm** reload completes fast (~6s) with byte-identical coverage numbers across two consecutive loads, and the developer's own report cites a fresh 6-way-concurrent measurement (10.5s single / 18.5s six-way) recorded in `reports/perf-budgets.md`. See "Regression Risk" below for the one caveat: a genuine cold-process-restart was not independently reproduced by the browser agent itself. |
| Contained error card (`app/error.tsx`) | Not navigated to — activates automatically in place of any page's content on an uncaught client exception; sidebar/header stay visible around it | N/A (automatic safety net, not a sought-out feature) | "Something went wrong on this page" / "Try again" — calm, clear, non-technical | Warning-triangle icon + card + working retry button; I independently read the source and confirm it reuses the existing `Card` component and the exact `border-neg bg-surface` / `AlertTriangle` / `text-neg` / `text-text-muted` token vocabulary already used by `stocks/page.tsx`'s pre-existing "Backend unavailable" card (verified both files directly, not just the handoff's self-description) | **Yes** — UT-16 (forced exception via `Array.prototype.sort` monkeypatch → card renders, all 11 nav `href`s still present in DOM) and UT-17 ("Try again" recovers the page, full leaderboard re-renders). |
| Root-shell fallback (`app/global-error.tsx`) | Not navigated to — only fires if the root layout itself fails; deliberately has no sidebar (Next.js requirement, since it replaces the root layout that would render the sidebar) | N/A | "Trendora hit an unexpected error" / "Try again" | Standalone card, same design tokens as raw Tailwind classes (`bg-bg`, `border-neg`, `bg-surface`, `text-neg`, `text-text-muted`) since it cannot depend on the app's component tree | **Statically verified only** (UT-18 SKIPPED — triggering it requires editing `app/layout.tsx`, outside the QA agent's "no source edits" rule; source read confirms correct `<html>/<body>` structure and exact copy match). Reasonable substitution given the constraint; this is P3/non-gating per the test plan. |

No hidden capabilities, no undiscoverable capabilities, no label confusion found. This iteration adds
zero navigation surface (confirmed independently: `sidebar.tsx` shows no diff in `git status`, and I
read the file directly — the same 11 entries from Dashboard through Data Manager are all present,
matching what iter-18's own ux-regression review saw). The "automatic safety net" framing for
`error.tsx`/`global-error.tsx` is the correct discoverability model for this class of feature — a crash
boundary is not something a user seeks out via navigation, and its "path" is that it appears exactly
when and where needed, which is what was verified.

## Regression Risk

| Shared component | Prior feature it serves | This iteration's change | Risk |
|---|---|---|---|
| `apps/frontend/app/stocks/page.tsx` (`SORT_COMPARATORS.sector`, `sectors` filter memo, `visible` filter predicate, Sector `<td>`) | `/stocks` leaderboard (J-01, live since iter-2), evidence status badges (J-03) | I read the full diff directly: only the 4 sector-specific lines changed (comparator now calls `compareSectors`, filter vocabulary now maps through `sectorLabel`, filter predicate now compares through `sectorLabel`, cell now renders `sectorLabel(row.sector)`). Every other column's comparator (rank/ticker/leadership/entry_quality/risk/setup/proximity/1D-60D), the evidence-badge rendering, and the search/pattern filters are untouched. | **LOW** — surgical diff confirmed by direct read; UT-01 (541/541 rows, all columns present), UT-07 (1623/1623 evidence badges correct) corroborate with real structured DOM parsing, not just a visual glance. |
| `apps/frontend/app/stocks/[ticker]/page.tsx` (sector chip only) | Chart Range Control (J-10, iter-18), Regime toggle (J-45, pre-iter-18), per-stock evidence score cards | Diff confirmed: only the one `<span>{sectorLabel(row.sector)}</span>` line changed. Chart/toggle/score-card code is untouched. | **LOW** — UT-08/09 confirm the chip works both null and non-null; UT-10 independently confirms the Full-history/Recent chart toggle still works both directions after the *backend* prefill rewrite this same iteration made (a cross-cutting risk this table's next row addresses). |
| `apps/frontend/app/scanner-runs/[runId]/page.tsx` (Sector `<td>` only) | Scanner Run detail / "Immutable snapshot" banner | Diff confirmed: single-line change, same pattern as above. | **LOW** — UT-11 confirms the banner text and all other columns/scores are intact across all 541 constituent rows. |
| `apps/frontend/lib/api.ts` (`StockRow.sector: string` → `string | null`) | Foundational type consumed anywhere a `StockRow` is rendered | I independently grepped the **entire** frontend (`app`, `components`, `lib`) for every `.sector` reference beyond the three files above, and independently re-ran `npx tsc --noEmit` myself (not just trusting the handoff's claim) — **0 errors**. The other hits found (`BySectorRow.sector: string`, `EventStudySectorRow.sector: string` in `research/_labs.tsx`/`samples-link.ts`/`research/samples/page.tsx`, and `PerStockRow.sector: string | null` in `return-attribution.tsx`) are all structurally distinct, non-padded "by stored sector with members" groupby types that exclude the null bucket by construction, or (for `PerStockRow`) an already pre-existing nullable field that was already correctly guarded (`row.sector ? <span>...</span> : null` at `return-attribution.tsx:52`, untouched this iteration). | **LOW** — independently corroborated, not just narrative. |
| `apps/backend/app/engine/prices.py` `_BarCache.prefill()` rewrite + new `Bar(NamedTuple)` | Every bar-consuming surface: `/stocks/{ticker}` charts (J-10), `/backtest`, `/scanner-runs` scores, VCP/pattern detectors | Read the `Bar` class docstring and definition directly: exposes exactly `.date/.open/.high/.low/.close/.volume`, explicitly no `.id`/`.symbol` (cache already partitions by symbol as the dict key). I grepped `prices.py`/`forward_testing.py`/`scanner.py`/`warmup.py`/`market_phase.py` for any per-bar `.symbol` access and found none — consistent with the docstring's claim that no consumer needs it. `test_bar_cache.py` is a real 401-line, 13-test suite with names matching the claimed correctness gate (`test_prefill_returns_bar_records_matching_plain_query_row_level`, `test_cached_snapshot_equals_uncached_row_level`, etc.), not a stub. | **LOW** — mechanism is structurally sound on inspection; UT-10 (byte-identical chart bar count/date range) and UT-13 (byte-identical `/data` coverage numbers across reloads) are real functional corroboration, not just narrative trust. |
| Root app shell (new `error.tsx`/`global-error.tsx`) | Every existing page/route | New files only — no existing route file was modified to add them (Next.js's file-based special-name convention). `error.tsx` renders inside `RootLayout`'s `{children}` slot (I read `layout.tsx` directly: `<Sidebar />` sits in the same tree, outside `{children}`), so it cannot un-render the sidebar. No pre-existing `not-found.tsx`/`loading.tsx` exists to conflict with the new files. | **LOW** — additive, non-invasive; UT-16 independently confirms the sidebar survives an in-page crash. |

**Flagged verification gap (not a regression, already self-disclosed):** the single riskiest, most novel
claim this iteration makes — that a **genuine cold-process-restart** `/api/data` load survives without
OOM/hang — was not independently reproduced by the browser-qa-agent. Its own report states plainly (Note
2, "Notes/Observations for the auditor"): UT-12/13 ran against an already-warm shared backend process,
because restarting it was judged outside a browser agent's remit. The "before" ~6.8 GB figure is carried
over from the incident report, not re-triggered this session (reasonably — deliberately reintroducing a
crash in a working shared environment is bad practice, and the developer's own implementation summary
discloses this plainly rather than hiding it). The "after" numbers (10.5s / 18.5s six-way) were measured
fresh. This is a legitimate, already-transparent verification-completeness gap, not a hidden defect —
unlike iter-18, where a real crash sat undisclosed in the evidence folder while `status.json` claimed
zero blockers, here every party (developer, QA agent) proactively surfaced the caveat. I am forwarding it
per the phase's own explicit request (plan.md risk #6) that this review reconcile cleanly with the
auditor rather than let a gap go unmentioned. It does not meet this rubric's WARN bar ("could be more
discoverable") or FAIL bar ("hidden/inaccessible... clear regression") since the page IS discoverable,
DOES work under every condition actually tested, and the gap is about a specific untested condition, not
a broken or hidden feature — so it does not change the verdict, but the auditor should treat the
cold-start OOM claim specifically as "well-reasoned and partially measured" rather than "browser-verified
end-to-end."

## UI vs Backend Parity

| Backend capability | UI exposure | Assessment |
|---|---|---|
| Sector-sort/filter null-safety fix | `/stocks` comparator, filter dropdown, table cell all updated via the shared `sectorLabel`/`compareSectors` helper | Matches — full parity |
| `StockRow.sector` contract widened to `string \| null` | Every consumer re-validated (`stocks/page.tsx`, `stocks/[ticker]/page.tsx`, `scanner-runs/[runId]/page.tsx`) — independently confirmed via `tsc --noEmit` (0 errors) and a manual grep sweep | Matches — full parity |
| `/api/data` prefill streaming rewrite (OOM fix) | No new UI; manifests as the existing `/data` page loading reliably instead of hanging | Correctly classified as backend-only reliability — no new information to surface, appropriately not listed as a new capability |
| `compute_coverage` single-flight / double-scan fix | Same — no new UI | Correctly classified as backend-only |
| `config.yaml` comment correction | None | Correctly classified as backend-only, zero user impact |
| `error.tsx` / `global-error.tsx` crash containment | New UI (contained card / standalone fallback) | Matches — full parity |
| Optional `prefill(symbols=, min_date=)` growth-leeway params (phase spec's "cheap, optional" item) | None — internal, forward-looking, no current caller passes them | Correctly not surfaced; nothing for a user to see today |

No parity gap found. `user-visible-changes.md`'s "Not Visible Yet: None" and
`implementation-summary.md`'s "Backend-Only Items: None" both hold up against my independent review of
the diff — every backend change this iteration either has a direct UI manifestation or is legitimately
invisible internal plumbing with no user-facing value to surface.

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None.

### Potential Regressions
None confirmed. All shared-component touches this iteration are surgically scoped (independently
verified via direct diff reads, not just the handoffs' self-description), and the specific prior
journeys at risk (J-01/J-03 on `/stocks`; J-10/J-45 on `/stocks/{ticker}`; the Scanner Run detail
banner) all show passing, evidence-backed regression-smoke results (UT-07, UT-09, UT-10, UT-11) rather
than mere "no diff so probably fine" assumptions — which is precisely the failure mode iter-18 fell into
and this iteration is designed to avoid repeating.

### Visual Consistency
- `error.tsx` matches the established visual language exactly: same `Card` component, same
  `border-neg bg-surface` / `AlertTriangle` / `text-neg` / `text-text-muted` tokens as the pre-existing
  "Backend unavailable" card on `stocks/page.tsx` (I compared both sources directly — the token
  vocabulary and structure are near-identical, differing only in alignment (`items-start` vs
  `items-center`) to accommodate the added retry button).
- `global-error.tsx` cannot reuse the `Card` component (a deliberate, well-justified exception — it must
  not depend on the very layout/provider tree it substitutes for) but still uses the same raw design
  tokens (`bg-bg`, `border-neg`, `bg-surface`, `text-neg`, `text-text-muted`, `bg-surface-2`,
  `border-border`) as plain Tailwind classes, so the maximally-degraded fallback still reads as Trendora
  rather than a generic browser crash page. No arbitrary colors/spacing observed in either file.
- The "Unassigned" label is applied identically (via the one shared `sectorLabel` helper) everywhere a
  stock's sector is displayed this iteration — no divergent wording across `/stocks`,
  `/stocks/{ticker}`, `/scanner-runs/{runId}`.
- **Minor, non-blocking, pre-existing (not introduced this iteration):** `components/return-attribution.tsx`'s
  `PerStockColumn` (untouched this iteration, confirmed absent from `git status`) uses a different
  convention for the same underlying concept — a null sector there renders as nothing at all
  (`row.sector ? <span>...</span> : null`) rather than an explicit "Unassigned" label. This predates
  iter-19, is not broken (it doesn't crash), and was correctly out of this iteration's scope — but it is
  now a slight terminology inconsistency across the product for the identical concept ("no mapped
  sector" = an explicit word in three places, a blank omission in a fourth). Worth a future-iteration
  note, not a blocker for this one.
- The `/stocks/{ticker}` Full-history chart's x-axis gridlines not visually extending to a deep-history
  name's true first bar (e.g., NVDA's 1999 start) is explicitly named in the phase spec as the
  non-blocking "F1" carry-over item, confirmed still present by UT-10's own observation. This is
  pre-disclosed and explicitly out of this iteration's Definition of Done — correctly not a blocking flag
  here.

## Recommendation

No action required to ship this iteration from a UX-regression standpoint. For the auditor's
reconciliation (per plan.md risk #6):

1. Treat the cold-process-restart `/api/data` OOM claim as "mechanism verified by code inspection +
   `test_bar_cache.py` + a warm-load/6-way-concurrent-warm-load browser test," not as "browser-verified
   under a genuine cold restart" — the gap is honestly disclosed by both the developer and QA agent, not
   hidden, but should be named precisely rather than rounded up to "fully verified."
2. Optional, non-blocking, future-iteration item: reconcile the "Unassigned" vs. blank-omission
   inconsistency between the new `sectorLabel` convention (`/stocks`, `/stocks/{ticker}`,
   `/scanner-runs/{runId}`) and the older, untouched `return-attribution.tsx` per-stock sector display.
