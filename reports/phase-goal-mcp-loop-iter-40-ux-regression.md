# Phase goal-mcp-loop-iter-40 — UX Regression Review

**Date:** 2026-07-15

**Verdict:** UX-REGRESSION-PASS

---

## New Capability Discoverability

**New capability: the "Risk budget" card on `/stocks/{ticker}`** (J-24 / B-201) — ATR%, downside
volatility, worst historical 20-day window, distance-to-invalidation, and an overnight-gap profile
(p95 headline + median/worst as supporting text), plus overnight share of 20-day variance, each with a
"pXX of universe" percentile chip.

- **Navigation path:** none new. `/stocks/{ticker}` is the pre-existing Stock Detail page, reached from
  the persistent sidebar "Stocks" entry (`apps/frontend/components/sidebar.tsx` — confirmed untouched
  this iteration via `git status`) → click any stock row. The card is inserted directly into the
  existing detail page's vertical stack, immediately after `ThemeAndInvalidationCard` and before the
  VCP/pattern cards (confirmed via `git diff`: a single `<RiskBudgetCard row={row} />` line inserted,
  no surrounding JSX touched).
- **Click count:** 2 clicks from the dashboard (sidebar "Stocks" → a stock row), identical to every
  other card on this page (scores, Theme/Invalidation, VCP, Pullback, price chart) — not a regression
  in discoverability depth, since no per-stock content on this product has ever been reachable in fewer
  clicks than "open the stock."
- **Label clarity:** heading "Risk budget" with subtitle copy "How much plausible damage this name
  carries — volatility, overnight-gap exposure the invalidation level cannot protect against, the worst
  historical 20-day window, and distance from where the thesis is wrong. Descriptive only; not a
  recommendation." (confirmed present in the JSX at `apps/frontend/app/stocks/[ticker]/page.tsx`, one
  `<p>`). Tile labels ("ATR %", "Downside volatility," "Worst 20-day window," "Distance to
  invalidation," "Overnight gap · p95," "Overnight share of 20d variance") are plain language except
  "ATR %," which is pre-existing product terminology (the same label the Risk score card already uses
  for the same underlying value — not new jargon introduced by this phase) and is tooltip-linked to a
  `/methodology` glossary definition like every other technical term on this page.
- **Visual feedback:** confirmed with a real, non-null render — `reports/qa/goal-mcp-loop-iter-40-evidence/TC-01-risk-budget-card-liquid.png`
  (captured 2026-07-15 19:27, before Chrome MCP broke for the later browser-qa-agent pass — see
  "Evidence-completeness note" below) shows AAPL's Risk budget card with all 6 tiles populated with real
  values (ATR % 2.84%, Downside volatility 1.15%, Worst 20-day window −67.03%, Distance to invalidation
  0.58%, Overnight gap · p95 1.44% with median 0.44%/worst 1.94% supporting text, Overnight share of 20d
  variance 11.66%), each with a "pXX of universe" chip, styled with the same `Card`/tile pattern as the
  page's other cards. No blank tiles, no fabricated "0%".

**New capability: 5 risk-budget columns on the `/stocks` leaderboard.**

- **Navigation path:** none new. `/stocks` is the pre-existing leaderboard, 1 click from the sidebar.
  The 5 new columns ("ATR%", "Downside vol", "Gap p95", "Worst 20d", "Dist. to invalidation") are
  inserted into the existing sortable table between "High proximity" and "Setup" (confirmed via
  `git diff`: `RISK_BUDGET_COLUMNS.map(...)` inserted as a sibling before the pre-existing `Setup`
  `SortHeader`/`<td>`, which is otherwise byte-identical).
- **Click count:** 1 click from the dashboard (sidebar "Stocks"). The table already scrolls
  horizontally past its viewport (a pre-existing pattern from the `fwd_<horizon>`/`mdd_<horizon>`
  columns), so a user on a narrow viewport must scroll right to see the 5 new columns — this is the
  same discovery cost every existing rightward column already carries, not a new problem this phase
  introduces.
- **Label clarity:** abbreviated headers ("Gap p95", "Worst 20d") follow this table's existing
  dense-column convention and are each tooltip-linked (via `TermInfo`, same mechanism as "High
  proximity") to a full-text `/methodology` definition.
- **Visual feedback:** NOT independently browser-screenshotted this iteration (see
  "Evidence-completeness note" below) — asserted via API-level check (QA TC-04/TC-05: both endpoints
  return byte-identical `risk_budget` fields; comparator logic mirrors the already-shipped
  `high_proximity` NA-last pattern) and by direct diff inspection, not a rendered screenshot.

**New capability: 3 `/methodology` glossary entries** ("overnight-gap profile," "worst 20-day window,"
"distance-to-invalidation %").

- **Navigation path:** none new. `/methodology` is a pre-existing sidebar entry; the Glossary section's
  existing search box surfaces the new terms (config-driven content only — `apps/frontend`'s
  methodology page component itself has zero diff this iteration, confirmed by its absence from
  `git status` and from the ui-surface-map's "Modified components" list).
- **Visual feedback:** NOT independently browser-screenshotted this iteration — confirmed via
  `GET /api/methodology` (QA TC-06/TC-07) showing the 3 entries present under `factor_stats` with
  `where`/`thresholds` fields populated, served through the same unmodified glossary renderer every
  pre-existing term already uses.

No new capability from this iteration lacks a navigation path, and none requires more than the
product's standard 1–2-click "open a stock" pattern. No developer-only or undocumented access path was
required for anything in scope.

---

## Regression Risk

Per the ui-regression-scout method: intersect this iteration's touched files against the shared
surfaces required-still-passing journeys J-01, J-02, J-03, J-05, J-10, J-12, J-13, J-20 depend on
(journey definitions + `first_seen_iter` read from `docs/goal.md` and
`runs/goal-session-mcp-loop/state/journey-history.json`).

| Shared surface | Prior feature it serves | This iteration's touch | Risk |
|---|---|---|---|
| `apps/frontend/app/stocks/[ticker]/page.tsx` | J-01/J-02 score + evidence-status badges (first seen iter-0); J-10 deep price chart (first seen iter-16) — all rendered lower on this SAME page file | `git diff` shows +92/−3 lines: the only removal is one import-line edit (`useEffect, useState` → `useEffect, useState, type ReactNode`); every other change is new functions (`RiskMetricTile`, `RiskBudgetCard`) appended after existing code and a single `<RiskBudgetCard row={row} />` line inserted between `<ThemeAndInvalidationCard row={row} />` and the VCP/pattern-card block. No line inside the score cards, evidence-badge block, or price-chart block was touched. | **Low.** Diff-confirmed additive-only. Also corroborated by QA TC-12/TC-13/TC-14 (API-level score/chart-placement checks, PASS) and the what-to-click.md operator guide's step 9/10 (explicit "scores unchanged" + "chart not pushed off-screen" checks). |
| `apps/frontend/app/stocks/page.tsx` | J-01/J-03 leaderboard scores + evidence badges (first seen iter-0) | `git diff` shows +83/−3: the only removals are a comment-line reword and the `SortKey` type widened to include the 5 new column-key literals (additive union, no key removed). The pre-existing "Setup" column's `SortHeader` and `<Badge variant={setupVariant(...)}>` are unchanged, just now preceded by the new cells. | **Low.** Diff-confirmed additive-only; `comparatorFor`'s new branch is inserted before the existing `SORT_COMPARATORS[key as BaseSortKey]` fallback, not replacing it. |
| `apps/frontend/lib/api.ts` | `StockRow` — every page that reads a stock row (leaderboard, detail, watchlist enrichment) | `git diff` shows pure addition: 3 new exported interfaces + one new optional field `risk_budget?: RiskBudget` appended to `StockRow`. No existing field renamed, retyped, or removed. | **Low.** Optional field, additive only; TypeScript compiled clean (`tsc --noEmit`, 0 errors, confirmed in both dev and frontend handoffs). |
| `apps/backend/app/engine/scoring.py` | Every score-bearing journey (J-01/J-02/J-03 Leadership/Entry Quality/Risk; indirectly J-10/J-12 via the same row) | `git diff` shows +76/−2: the only removals are an import-line reorganization (`opens` added to the `bars_asof`/`bars_asof_window`/`closes`/`highs`/`lows`/`volumes` import, `Optional` import relocated). `atr_pct`/`downside_vol` are reused from already-computed locals (per dev handoff), not recomputed. New `risk_budget` fields enter no weighted-score sum. | **Low.** Diff-confirmed additive-only. Independently corroborated 3 ways: (1) dev's automated score-invariance test (monkeypatching the new indicator functions to return `999.0` and confirming every row's score/bucket/rank is byte-identical), (2) reviewer's independent full re-run of `test_scoring_window.py`'s byte-identity harness (4 passed, 533s, real seed), (3) QA's TC-10/TC-12 direct API comparison of `/api/stocks` vs `/api/stocks/{ticker}` scores. |
| `apps/backend/app/engine/indicators.py`, `apps/backend/app/engine/prices.py` | Shared indicator/extractor functions consumed by scoring across every journey | `git diff` shows zero removed lines in `indicators.py`; `prices.py`'s only change is a new `opens()` function inserted before the pre-existing `closes()` — the existing `closes`/`highs`/`lows`/`volumes` extractors are byte-unchanged. | **Low.** Pure insertion, confirmed by diff. |
| `apps/backend/app/config.py`, `config.yaml` | Every config-consuming code path (boot-time validation for the whole engine) | `config.py` diff: 0 removed lines (two new `IndicatorsCfg` fields + validator folding). `config.yaml` diff: 0 removed lines (2 new keys under the existing `indicators:` block + 3 new glossary entries appended after the pre-existing `downside volatility (semivol)` entry). | **Low.** A config predating this key still loads unchanged in shape; new fields are required-but-additive (existing `test_config*.py`/`test_sectors.py`/`test_themes.py`/`test_indexes.py` fixtures were mechanically extended, not logically changed, per the dev handoff). |
| `apps/frontend/app/layout.tsx` → `PreflightBanner` (J-20, first seen iter-29 — must render on `/stocks`, a stock detail, `/watchlist`, `/evidence`) | J-20 | **Not in this iteration's diff at all** — confirmed absent from `git status --short`. The Risk budget card is added inside the page components `layout.tsx` wraps, not the layout itself. | **None.** Architecturally independent; also the what-to-click.md guide's step 9 explicitly re-checks the green "GO" strip on the touched detail page. |
| `apps/frontend/components/sidebar.tsx` | Navigation for every journey | Not in this iteration's diff — confirmed absent from `git status --short`. | **None.** No nav entry added, removed, or relabeled. |
| `apps/backend/app/api` routes (`/api/stocks`, `/api/stocks/{ticker}`) | J-01/J-02/J-03/J-10/J-12 data contract | No route file in the diff (confirmed via `git status`) — `scanner.py`'s `record_json = json.dumps(row)` and `snapshot_serving.py`'s verbatim re-serve already carried the new field through with zero code change (verified by the dev handoff reading both files; not contradicted by anything found here). | **None.** No endpoint code touched. |
| `/evidence` page + evidence ledger files (J-05, first seen iter-0) | J-05 | Not in this iteration's diff — confirmed via `git status` (no file under `runs/goal-session-mcp-loop/state/{certified-claims,staging-ledger,pre-registrations}.jsonl` or any `/evidence` frontend file changed). | **None.** |
| `/data` Data Manager page (J-13, first seen iter-16) | J-13 | Not in this iteration's diff or ui-surface-map at all. | **None.** |
| Universe/membership resolution (`resolve_members`, J-12, first seen iter-16) | J-12 | Not touched — this iteration only adds fields to an already-resolved row; no membership-count or admission logic changed. | **None.** |

**Conclusion: no potential-regression flags.** Every shared surface this iteration's diff touches was
verified by direct `git diff` inspection to be additive-only (new siblings/fields/functions inserted,
not existing logic edited), and the two areas of highest inherent risk — score computation
(`scoring.py`) and the Stock Detail/leaderboard page bodies carrying J-01/J-02/J-03/J-10 — have
multi-source corroboration beyond the diff itself (automated invariance test, independent reviewer
re-run, QA API cross-check).

**Note on the working tree's other pending diff.** `git status` at the start of this review also shows
uncommitted changes to `apps/backend/app/engine/warmup.py` (plus a few other files) that iter-40's own
`docs/handoffs/goal-mcp-loop-iter-40-dev.md` does not list under "Files Changed." Per the execution
plan's own "Context" section, this is parked iter-26 windowing work that predates iter-40 and that
iter-40's dev built on top of without itself modifying `warmup.py` further. Since this parked diff was
already present in the working tree throughout iter-40's own dev/review/QA passes (it is not something
this UX review is newly discovering), whatever behavior it carries was already exercised by the same
pipeline that validated this iteration — it is a commit-hygiene question for the reviewer/release step,
not a UX regression introduced by iter-40.

---

## UI vs Backend Parity

`scoring.py` computes 8 leaf `risk_budget` values per stock (`atr_pct`, `downside_vol`,
`gap_profile.{median,p95,worst,overnight_variance_share}`, `worst_20d_window`,
`distance_to_invalidation_pct` — matching the dev handoff's "called 8 times, once per leaf" percentile
pass). Cross-checked against both frontend surfaces:

| Backend leaf | Surfaced on `/stocks/{ticker}` card? | Surfaced on `/stocks` leaderboard? |
|---|---|---|
| `atr_pct` | Yes — "ATR %" tile | Yes — "ATR%" column |
| `downside_vol` | Yes — "Downside volatility" tile | Yes — "Downside vol" column |
| `gap_profile.median` | Yes — supporting text inside the "Overnight gap · p95" tile | No |
| `gap_profile.p95` | Yes — "Overnight gap · p95" tile (headline) | Yes — "Gap p95" column |
| `gap_profile.worst` | Yes — supporting text inside the "Overnight gap · p95" tile | No |
| `gap_profile.overnight_variance_share` | Yes — "Overnight share of 20d variance" tile | No |
| `worst_20d_window` | Yes — "Worst 20-day window" tile | Yes — "Worst 20d" column |
| `distance_to_invalidation_pct` | Yes — "Distance to invalidation" tile | Yes — "Dist. to invalidation" column |

8/8 leaves are surfaced on the detail card (6 tiles; gap median/worst ride as supporting text inside
the p95 tile rather than getting a dedicated tile — the value is visible, not hidden). 5/8 leaves are
surfaced on the leaderboard (gap median/worst/overnight-variance-share are card-only). This asymmetry is
explicit in both `docs/goal.md`'s J-24 acceptance text and the phase spec ("New risk-budget leaderboard
columns" names 5, not 8) and matches this product's existing precedent — e.g. "High proximity" is a
single leaderboard column backed by a richer score-card breakdown elsewhere. Every backend value has at
least one UI home; nothing is computed and served with zero display slot anywhere. No parity gap to
flag.

Also confirmed intentionally out of scope this phase (not a lagging gap, since no backend work exists
for these either): feeding `risk_budget` into any weighted score, a `ScannerResult` schema
migration/new sort-filter surface, a full-universe historical backfill of the new fields, B-203
(position-risk calculator), and B-202 (invalidation-style evidence study) — all named explicitly in
`docs/goal.md`'s J-24 entry and the phase's OUT OF SCOPE section.

---

## Flags

### Hidden Capabilities
None. The Risk budget card and the 5 leaderboard columns are both reachable via the product's existing,
unmodified navigation (sidebar → Stocks → a stock row; sidebar → Stocks). No capability in this
iteration's scope has zero navigation path.

### Undiscoverable Capabilities
None. Both new surfaces sit on pages already 1–2 clicks from the dashboard, matching this product's
established per-stock-detail and leaderboard-column conventions exactly — this iteration does not
introduce a new or deeper navigation pattern than what already exists for sibling capabilities.

### Potential Regressions
None found. See the Regression Risk table above — every touched shared surface (score cards, evidence
badges, price chart, leaderboard Setup column, config loading, `StockRow` type) was confirmed
additive-only by direct diff inspection, with the two highest-risk surfaces (`scoring.py`'s
score computation and the Stock Detail/leaderboard page bodies) carrying independent multi-source
corroboration beyond the diff.

### Visual Consistency
- **Matches the established style.** The new card reuses the existing `Card`/`CardHeader`/`CardTitle`/
  `CardContent` primitives verbatim (confirmed in the diff — no new UI primitive was created). Tile
  labels use `text-xs uppercase tracking-wide text-text-faint` and values use the `num` class, matching
  `ThemeAndInvalidationCard`'s and `ScoreCard`'s existing conventions exactly (per the plan's Visual
  Requirements and confirmed present in the diff). The NA state (`text-warn`, "NA — insufficient
  history") mirrors the pre-existing `naInvalidation` short-history treatment on the same page rather
  than inventing a new warning style.
- **No glassmorphism/glow/gradient.** A scan of the new/changed frontend code
  (`grep`-checked for `backdrop-blur`/`shadow-glow`/`animate-glow`/`gradient` across
  `stocks/page.tsx`, `stocks/[ticker]/page.tsx`, `lib/risk-budget.ts`) found none — consistent with this
  page's existing dense, data-first look and with the plan's explicit "no new visual effects" 
  requirement.
- **No arbitrary/new color scale.** All classes used by the new components
  (`bg-surface-2`, `border-border`, `text-text-faint`, `text-text`, `text-warn`) are pre-existing
  DESIGN SYSTEM tokens already in use elsewhere on this same page — no arbitrary hex/rgb values.
- **No anti-goal language leak.** A targeted grep of the new/changed frontend files for
  proven/buy/sell/trim/reduce/rebalance found matches only in pre-existing, unrelated code (other
  scores' "Not yet proven" badge logic first shipped in iter-1/iter-2; `query.trim()` string-method
  calls) — none inside the new `RiskBudgetCard`/`RiskMetricTile`/`RiskBudgetCell`/`risk-budget.ts` code.
  The card's own copy is "Descriptive only; not a recommendation," confirmed present in the JSX.

---

## Evidence-completeness note (does not change the verdict)

This iteration's canonical `reports/phase-goal-mcp-loop-iter-40-ui-test-results.md`
(browser-qa-agent) recorded **0/16 tests PASS — all 16 SKIPPED** because Chrome MCP could not bind its
DevTools port in that session (6 attempts across 2 profiles, cross-checked against 2 unrelated
pre-existing Chrome instances also failing to bind, full diagnostic trail in that report). That report
itself frames this as an environment condition, not a product signal, and independently reconfirmed via
`curl` that `/api/stocks/AAPL` serves real, non-null `risk_budget` values.

This review did not re-attempt Chrome MCP (the prior agent's 6-attempt, cross-checked diagnostic already
establishes it was down for this session; a 7th attempt would not add information). Instead, this review
leaned on:
- `reports/qa/goal-mcp-loop-iter-40-qa.md` (the separate functional `qa` agent), which DID successfully
  drive Chrome MCP ~17 minutes before it broke, and left a real screenshot
  (`TC-01-risk-budget-card-liquid.png`) showing the Risk budget card correctly rendered on `/stocks/AAPL`
  with real data — reviewed directly as part of this UX assessment (see "New Capability Discoverability"
  above).
- Direct `git diff` inspection of every touched file (this review's own work, not delegated to any
  other agent's claim).

What remains **not independently screenshot-verified** by any agent this iteration: the leaderboard's 5
new columns actually rendering/sorting/tooltip-popping in a live browser, the `/methodology` page
actually rendering the 3 new glossary rows, and the NA/short-history tile state actually rendering (the
QA test plan and what-to-click.md both independently note the current seed has no ticker short enough to
trigger it — ARM has 25+ years of history in this seed, not a true short-history case). These rest on
API-level checks and code-pattern-matching to already-proven precedents (the `high_proximity`
NA-last comparator; the unmodified glossary renderer), not a rendered screenshot. This is a real
test-coverage gap worth closing with a live browser pass once Chrome MCP is healthy again, but it does
not indicate anything is actually broken — no evidence anywhere (diff, API, screenshot, or prior QA)
points the other way — so it does not change this review's PASS verdict.

Separately, `reports/phase-goal-mcp-loop-iter-40-user-visible-changes.md`'s "Not Visible Yet" section
(written 18:51–18:52, before the QA agent's DB rebuild at ~19:27–19:30) describes the risk-budget fields
as not-yet-populated on the running instance. That gap has since been resolved and reconfirmed twice
(QA's TC-18 at 19:29, and the browser-qa-agent's own precondition check at 19:51) — real values are
being served. Flagging this so the auditor does not read that report's stale snapshot at face value.

---

## Recommendation

No action required to ship this iteration. Two non-blocking follow-ups for a future pass:

1. When Chrome MCP is next healthy, run a live browser pass specifically covering the `/stocks`
   leaderboard's 5 new columns (position, sort direction, NA-last ordering, info-tooltip popup) and the
   `/methodology` glossary search for the 3 new terms — these were verified via API/diff reasoning this
   iteration but never actually screenshotted.
2. The NA/short-history tile state has no reproducible fixture in the current seed universe (every
   ticker has ≥20 trading days of history). If a future iteration wants to close this specific test gap,
   it would need either a synthetic short-history fixture or an explicit, permanent waiver note (the
   what-to-click.md guide already documents this as a known, non-blocking limitation — consider
   promoting that note into the phase spec's own Testing Requirements so it doesn't need
   re-discovering each time).
