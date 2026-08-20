# Phase goal-market-compass-iter-1 — User-Visible Changes

**Phase:** goal-market-compass-iter-1
**Date:** 2026-08-20
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On the Stocks page (`/stocks`), users can now filter or search to a **real GICS sector** (Technology,
  Health Care, Financials, Utilities, etc.) for roughly 400 additional stocks that previously all fell
  into the catch-all "Unassigned" bucket. Example, confirmed live against this environment's currently
  stored run: **GRMN**, which today shows sector `null` / "Unassigned", carries `"Consumer Discretionary"`
  in the committed pool file and will show that real sector once a fresh scan/backfill runs. This works
  through the **existing** Sector column and Sector filter (`aria-label="Filter by sector"`) — no new
  button, form, or control was added; the same filter simply returns more useful results.
- No other new user action exists. Per the phase spec and both handoffs, this iteration adds zero new
  buttons, forms, filters, or navigation entries — it is a data-completeness and disclosure change layered
  onto existing surfaces only.

---

## What Changed in the Visible UI

- The `/stocks` leaderboard's **Sector** column and **Sector** filter dropdown will show far fewer
  "Unassigned" rows once a fresh scan/backfill has been produced under the new backend mapping. Measured
  live in this environment on the currently-stored run (as-of 2026-08-14, pre-fallback): **424 of 541
  resolved stocks (78.4%) show "Unassigned"** today; this iteration's target is **≤5%** after a fresh
  backfill (TC-1). The stock detail page (`/stocks/{ticker}`) shows the identical sector text in its
  header, in the small label next to the setup-status badge.
- No layout, control, or styling changed on `/stocks` — confirmed by `git diff` showing **zero changed
  lines** anywhere under `apps/frontend/app/stocks/`. This is purely a data-completeness upgrade to an
  existing column/filter.
- The Methodology page's (`/methodology`) `UniverseSelectionCard` component gained a new **"Stock sector
  labels"** subsection in code — a bordered subsection with a "Data basis" badge
  (`data-testid="universe-sector-basis"`), styled identically to the adjacent, already-shipped "Per-date
  membership rule" subsection. **In this environment today, this change is not actually visible on the
  live page** — see "Not Visible Yet" below for the full, pre-existing reason why.

---

## What Old Behavior Changed

- **`/stocks` Sector column and Sector filter**: previously, only the 122 names in Trendora's curated
  `config.stock_sectors` list ever showed a real sector; every other scored stock — the large majority,
  78.4% as measured live today — showed "Unassigned". After this iteration, a stock with no curated entry
  falls back to the sector recorded in the committed candidate-pool file (`universe_pool.csv`), so most of
  those stocks now show their real sector instead. A stock present in **neither** source still honestly
  shows "Unassigned" — nothing is guessed or fabricated.
- **This only takes effect on freshly-scored data — already-stored historical runs are not rewritten.** A
  stock's sector is written once, at scoring time, so a run already scored under the old code keeps
  showing its old (less-complete) value even after this iteration ships — confirmed live: the currently
  stored 2026-08-14 run still shows the pre-fallback 78.4% figure right now, unchanged by this code
  landing. Testers need to trigger a fresh backfill (the existing "Remove imported data" +
  "Start a fetch / backfill job" panels on `/data`) to see the improved coverage; simply reloading
  `/stocks` at today's latest as-of will still show the old numbers, which is expected, not a bug.
- Every other `/stocks` and stock-detail behavior (scores, buckets, setup status, sorting, other filters)
  is unchanged — the phase's own byte-identity fixture (TC-4,
  `test_pool_sector_fallback_never_changes_any_score_bucket_or_setup`) proves the fallback touches no
  score input.

---

## Not Visible Yet

- **The `/methodology` two-source sector-basis disclosure is built, UI-wired, and unit-tested, but does
  not currently render on the live page.** The entire "Universe Selection" card
  (`data-testid="universe-selection"`) — including this iteration's new subsection — only renders when the
  backend's `GET /api/methodology` response includes a `universe_selection` object, which itself requires
  the committed offline screen record `apps/backend/data/seed/universe.json` to exist. That file is **not
  present in this repository** — confirmed live while writing this report: `GET
  http://localhost:8255/api/methodology` on the running instance returns only `entries`, `intro`, and
  `glossary` keys, no `universe_selection` at all. **This is a pre-existing gate that predates this
  iteration** and hides the whole card (the membership-rule and threshold subsections too), not something
  this iteration introduced or broke — three pre-existing tests in `test_universe_screen.py` already skip
  themselves for the identical reason. There is no button or control anywhere in the app that builds
  `universe.json`; it is produced only by a separate, manual, out-of-scope backend job ("Expand", J-35).
  Until someone runs that job outside the browser, the evidence that the new disclosure text is correct
  comes from the passing backend tests instead of the live page:
  `test_universe_selection_sector_basis_present_and_matches_config` and
  `test_sector_basis_is_config_only_no_hard_coded_copy` (`test_methodology.py`), and
  `test_universe_selection_sector_basis_served_and_names_both_sources` (`test_api_methodology.py`, which
  itself honestly self-skips against this exact gate at the API layer).
- **`universe.pool_sector_aliases`** (new `config.yaml` / backend config key) has no UI surface — by
  design. It is a normalization seam for a future pool-CSV refresh whose sector names might not match one
  of Trendora's 11 sector names; it ships empty today (a verified no-op — TC-6), and editing it is not
  meant to be a UI action.
