# Phase goal-mcp-loop-iter-18 — UX Regression Review

**Date:** 2026-07-07

**Verdict:** UX-REGRESSION-FAIL

## Summary

The three new journeys this iteration ships (J-10 deep-history chart toggle, J-11 regenerated
evidence ledger, J-12 staleness gate) are genuinely well built, well integrated visually, and — where
the canonical browser-qa-agent lane actually reached them — verified working with clean, convincing
screenshots. That is the good news and it is substantial.

However, this iteration's own headline data change (broadening the candidate pool from ~122 to ~548
names, most of which have no GICS sector mapping) **crashes the `/stocks` leaderboard** — the
product's single most prominent, one-click-from-home page — the moment a user clicks the pre-existing
"Sector" column header to sort. This is not a hypothetical: the crash is captured in this iteration's
own QA evidence (`UT-21-fail-crash.png`) and independently reproducible by inspection of the
unmodified source. It is a clear regression of an established prior-iteration journey (leaderboard
sorting, live since iter-2), triggered directly by this iteration's data-basis change, and it remains
unfixed. That alone is FAIL-grade under this review's rubric ("clear regression in a prior user
journey").

Compounding this, the canonical browser-qa-agent lane — the artifact this review is instructed to
treat as authoritative ("what was tested and found") — did not finish. Its designated output,
`reports/phase-goal-mcp-loop-iter-18-ui-test-results.md`, is a SKIPPED stub, and a live query of the
task tracker (not just the stale note in `status.json`) confirms the Watchlist negative-path tests,
the Backtest/as-of-floor tests, and — most importantly — 3 of 4 quadrants of the P1 anti-goal sweep
(no buy/sell/price-target language) never ran. `status.json` and the separate coarse `reports/qa/
goal-mcp-loop-iter-18-qa.md` report both assert full completion and a clean PASS; neither claim
survives contact with the evidence directory both reports cite.

## New Capability Discoverability

| Capability | Path from home | Clicks | Verified? |
|---|---|---|---|
| Chart range toggle ("Recent"/"Full history") on `/stocks/{ticker}` | Dashboard → Stocks (1) → click a ticker row (2) → toggle sits inline in the chart header | 2 | **Yes** — clean, non-blank screenshots (`UT-05-full-history-result.png`, `UT-07-*`, `UT-08-*`) show the toggle, the correct caption text ("history since 1996-01-02 · older bars weekly-sampled"), and the deep chart rendering. Sits directly beside the pre-existing (J-45) Regime toggle, same idiom, same `usePersistedToggle` pattern — label is unambiguous to a non-technical user. |
| Depth-disclosure caption (first-available-date + downsampling note) | Same page, no extra click — inline under the chart controls | 2 | **Yes** — same screenshots as above; AAPL/NVDA/ARM captions all match spec exactly. |
| Broadened watchlist ticker acceptance | Dashboard → Watchlist (1) → type ticker → Add | 1 | **Partially.** Happy path confirmed: `UT-09-added.png` / `UT-09-persisted-after-refresh.png` show ABBV (a broadened-pool, non-legacy name) added and surviving a refresh, scores rendering correctly. Negative paths (unknown-ticker reject, duplicate-ticker reject) were never reached by the canonical lane — see Flags. |
| `/data` "Stale series" reason card + 5-column diagnostic grid | Dashboard → Data Manager (1) → inline in the existing Universe Diagnostic panel | 1 | **Not confirmed.** Every `/data`-page screenshot found in the evidence directory (`UT-03-result.png`, `UT-03-retry.png`, `UT-03-still-loading-check.png`) shows either a loading skeleton or a "Backend unavailable" honest-error card — none shows the actual populated 5-column grid or the new card's content. The backend staleness-gate logic itself is confirmed by the (green) backend test suite, so this reads as an environment interruption rather than a broken feature, but the specific new UI element has no clean visual confirmation in this iteration's evidence. |
| `/methodology` staleness rule text + membership timeline `stale` column | Dashboard → Methodology (1) | 1 | **Yes, indirectly** — `qa.md` TC-08/TC-16/TC-18 confirm the membership count and timeline mechanics; the coarse pass's own screenshots weren't captured for this specific page, but the underlying counts (587 symbols) are corroborated in `UT-09-added.png`'s header chip and elsewhere. |
| Broadened `/stocks` leaderboard row count | Dashboard → Stocks (1) | 1 | **Yes** — `UT-02-leaderboard-top.png` and header chips across many screenshots consistently show "587 symbols." |

No new pages were added and no navigation changed this iteration (confirmed against `ui-surface-map.md`
and every sidebar visible across the reviewed screenshots: Dashboard, Stocks, Themes, Sectors, Scanner
Runs, Backtest, Research, Evidence, Watchlist, Methodology, Data Manager — identical in every capture).
Nothing here is hidden or mislabeled; the discoverability mechanics of the new capabilities are sound.

## Regression Risk

| Shared component | Prior feature it serves | This iteration's effect | Risk |
|---|---|---|---|
| `apps/frontend/app/stocks/page.tsx` — `SORT_COMPARATORS.sector` / `sectors` vocabulary memo | `/stocks` leaderboard column sort + "Filter by sector" dropdown (live since iter-2, per `git log`) | **Confirmed crash.** See Flags → Potential Regressions below. File is byte-unmodified this iteration (`git diff HEAD` empty) — the code didn't change, but the data flowing into it did, and nobody re-validated the old code against the new data shape. | **HIGH — confirmed, not hypothetical** |
| `RegimeToggle` / `usePersistedToggle` (J-45, `stocks/[ticker]/page.tsx`) | Existing chart regime-band toggle | New `ChartRangeControl` sits beside it, reuses the identical pattern (aria-pressed, persisted localStorage key, hover/focus states). Untouched itself. | LOW — additive, same idiom, visually confirmed working alongside it in every detail-page screenshot reviewed |
| `ClaimRow` / evidence-status badge components (`/evidence`, live since iter-1) | Evidence ledger audit (J-05), FAIL/Proven badges (J-01/J-03) product-wide | Content-only regeneration (7 rows, new dates/verdicts); component structure untouched per `ui-surface-map.md` and confirmed visually (`UT-01`, `UT-04`, `TC-04`, `TC-06` all show the same badge styling as prior iterations, now uniformly "Not yet proven"). | LOW — verified working |
| `POST /api/watchlist` ticker resolution | Watchlist add (live since early iterations) | Swapped from a direct `config.universe.symbols` membership check to the shared `resolve_servable_symbol` (the same resolver the chart endpoint already uses) — a sound, single-source-of-truth change on inspection. Happy path verified; 404/409 negative paths not exercised in-browser this run. | MEDIUM (verification gap, not a suspected defect) |
| Global app shell / error handling | Every page | No `error.tsx` or `global-error.tsx` exists anywhere under `apps/frontend/app/` — confirmed by direct search. This means the sector-sort crash (and any future uncaught client exception, anywhere in the app) degrades to a full blank page with the sidebar and all navigation wiped, not a contained error card. Pre-existing condition, not introduced this iteration, but it is what turns the sector bug from "one broken widget" into "the whole page is gone." | Contextual — raises the stakes of the HIGH item above |

## UI vs Backend Parity

All backend capabilities intentionally not surfaced this iteration are explicitly, honestly disclosed
in `user-visible-changes.md`'s "Not Visible Yet" section and match the phase spec's own OUT OF SCOPE
list — none of these are flagged as parity gaps:

- Per-series data-vendor labels (`meta.json`) — deferred to J-14, correctly undisplayed.
- Deep `_SPX`/`_NDX`/`_DJI`/`_VIX` index/macro overlays — loaded into the DB, not wired to any chart — explicitly deferred (J-14 steps 2–3).
- Sector labels for the ~422 broadened-pool names — intentionally absent this iteration (J-13/J-14 follow-on). **This is the one parity gap that has a real, unaddressed side effect**: the backend was correctly changed to honestly omit sector data, but the pre-existing frontend sort/filter code was never updated to defensively handle that omission (see Flags). The *decision* to leave sector data unpopulated is fine and honest; the *frontend not being hardened against it* is the actual bug.
- Bounded snapshot-density cadence — no UI control, acceptable (internal operational policy, not a user journey).
- `/data` Fetch/Expand-universe still describes the legacy ~122 default — explicitly deferred to iter-19/J-13, correctly scoped out.

## Flags

### Hidden Capabilities

None. Every new capability listed in `user-visible-changes.md` has a navigation path within budget
(see table above).

### Undiscoverable Capabilities

None. The chart toggle, watchlist field, and `/data` reason card are all inline, labeled controls on
already-prominent pages — no capability requires developer knowledge or more than 2 clicks to find.

### Potential Regressions

- **CONFIRMED, not potential: `/stocks` leaderboard crashes when sorted by Sector.** `SORT_COMPARATORS.sector` at `apps/frontend/app/stocks/page.tsx:93` reads `(a, b) => a.sector.localeCompare(b.sector)` with no null guard. `apps/frontend/lib/api.ts:279` types `StockRow.sector` as a non-nullable `string`, but this iteration's own dev handoff confirms the backend now legitimately returns `sector: None` for 422 of 541 rows (the broadened pool has no GICS mapping outside the legacy ~122 names) — `scoring.py:377` does `cfg.stock_sectors.get(ticker)`, returning `None` by design. Clicking the "Sector" column header on `/stocks` — a plain, obvious, pre-existing sort control reachable in one click from home — invokes this comparator across the full row set; with ~78% of rows now null, an uncaught `TypeError` (`null.localeCompare is not a function`) is thrown almost immediately. Because no `error.tsx`/`global-error.tsx` exists anywhere in the app, the failure is not contained: it wipes the entire page, including the sidebar, down to Next.js's generic "Application error: a client-side exception has occurred" line. This is captured directly in this iteration's own evidence: `reports/qa/goal-mcp-loop-iter-18-evidence/UT-21-fail-crash.png`. A second, related but non-crashing defect sits in the same file: `const sectors = useMemo(() => Array.from(new Set(rows.map((r) => r.sector))).sort(), [rows])` (line 355-357) will include a literal `null` entry in the Sector filter dropdown's option list, which the phase's own `ui-surface-map.md` explicitly says must never render as literal "null"/"None"/"undefined." Neither defect is mentioned in the dev handoff's Known Issues, the review report, or the QA report — it is not a disclosed, accepted risk, it is a miss. The responsible file has zero diff this iteration (pre-existing since iter-2), so this is squarely a "shared component whose upstream data contract changed without the component being re-validated" regression — precisely the class of defect this review exists to catch, and it is not a rare edge case: it is now the *default* state of the leaderboard's most common sector distribution (78% null).
- **Canonical browser-qa-agent lane did not complete.** `reports/phase-goal-mcp-loop-iter-18-ui-test-results.md` is a SKIPPED stub ("Claude CLI invocation exited with code 70... transient Anthropic streaming error," timestamped 2026-07-07 05:34, i.e. hours after `status.json`'s "qa_complete" note). A live `TaskList` query (not the stale system-reminder snapshot) confirms task #18 ("Watchlist tests UT-09,23,24,26,29b") is still `in_progress` and tasks #19-22 (Backtest/as-of tests, the Homepage anti-goal sweep, golden-replay scripts, final report) are `pending`. Evidence trail (`UT-03-still-loading-check.png`: "Backend unavailable — Dataset coverage could not load from the API") plus the fact that neither backend (`:8255`) nor frontend (`:3255`) responds right now suggests the dev backend went down partway through the run (~00:45 on 2026-07-07) and was never recovered — an environment interruption, not necessarily a discovered defect in the untested areas. Net effect: the P1 anti-goal sweep (UT-29 — "no buy/sell/price-target language anywhere," which `docs/goal.md` marks *critical*) is only 25% executed (only the `/stocks`-leaderboard quadrant, UT-29a, actually ran); Watchlist's negative paths (unknown-ticker 404, duplicate-ticker 409) and the Backtest 2005-02-25 as-of-floor claim are unverified in-browser. The Watchlist backend change looks structurally sound on code inspection (reuses the same resolver as the chart endpoint), so this reads as a lower-severity verification gap rather than a suspected defect — but it should not be reported as done.
- **Pipeline self-reporting overstates completion.** `runs/goal-mcp-loop-iter-18/status.json` (`browser_checks_run: true`, "All 18 functional test cases passed... Zero blockers") and `reports/qa/goal-mcp-loop-iter-18-qa.md` ("Verdict: PASS," "UI evolution audit... UI-PASS," "No blockers identified") both describe a fully green state that does not reconcile with the crash screenshot sitting in the very evidence folder `qa.md` itself cites, nor with the incomplete canonical lane above. The auditor should not take either artifact's completion claim at face value.

### Visual Consistency

- New UI (`ChartRangeControl`, depth captions) matches the established dark theme, badge/pill styling,
  and typography seen across every screenshot reviewed — no arbitrary colors or spacing observed.
- The new toggle correctly reuses the pre-existing J-45 Regime-toggle idiom (segmented control,
  `aria-pressed`, `usePersistedToggle`), exactly as the plan specified — a good example of visual/
  interaction-pattern discipline.
- Evidence-status badges ("Not yet proven") are styled identically to badges seen in prior-iteration
  screenshots — no inconsistency detected.
- One screenshot-hygiene lapse (separate from the crash above, in the coarser QA pass, not the
  canonical lane): `reports/qa/goal-mcp-loop-iter-18-evidence/TC-01-full-history.png` is a 1.7 KB blank/
  solid-color image, yet `reports/qa/goal-mcp-loop-iter-18-qa.md`'s TC-01 row cites it as evidence that
  "Full history toggle renders correctly with weekly-sample disclosure." This is exactly the "blank
  frame is a verification gap, not evidence" failure mode the phase spec's own NOTES section calls out
  by name (citing iter-3/11/13/14/15). I do not believe the underlying feature is actually broken — the
  canonical lane's own equivalent captures (`UT-05-full-history-result.png`, `UT-07-full-history.png`,
  `UT-08-full-history.png`) are legitimate, well-composed, and clearly show it working — but this
  specific report's supporting evidence for that specific claim should not be trusted as-is.

## Recommendation

**Blocking (must fix before this iteration ships):**
1. Harden `apps/frontend/app/stocks/page.tsx`'s Sector sort comparator and filter-vocabulary builder
   against `sector === null` (e.g. `(a.sector ?? "").localeCompare(b.sector ?? "")` and filter nulls
   out of the `sectors` dropdown vocabulary, or render an explicit "Unassigned" bucket) — and update
   `apps/frontend/lib/api.ts:279`'s `sector: string` type to `sector: string | null` so the type system
   would have caught this the moment the backend contract changed. Re-run the browser-qa lane
   specifically against `/stocks` with the broadened pool loaded (click the Sector header, open the
   filter) before re-closing this iteration.
2. Finish the canonical browser-qa-agent lane: Watchlist UT-23/24/26/29b, Backtest UT-11/22/29c, and —
   highest priority given it is P1 and goal.md marks it critical — the Homepage/product-wide anti-goal
   sweep (UT-29d, zero buy/sell/price-target language). Confirm the dev backend is actually up and
   staying up before restarting this (the evidence trail suggests it went down mid-run last time).
3. Reconcile `runs/goal-mcp-loop-iter-18/status.json` and `reports/qa/goal-mcp-loop-iter-18-qa.md`
   against the above — both currently claim a completeness that the evidence directory they cite does
   not support.

**Non-blocking, worth tracking:**
4. Consider adding a route-level `error.tsx` (or at least a root `global-error.tsx`) so a future
   uncaught client exception degrades to a contained message instead of wiping the entire page and
   navigation — this is what turned one comparator bug into a full page loss.
