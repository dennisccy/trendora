# Goal Iteration 10 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-10
**Date:** 2026-06-02
**Written by:** developer

---

## Features Implemented

- **Research → Factor Lab (new page, `/research`)**: A new "Research" entry appears in the left sidebar.
  Opening it shows the **Factor Lab** — a tool that answers "does this signal actually rank future
  returns?" for any factor in the catalog. The user picks a **factor** (e.g. Leadership score, Entry
  Quality, Risk, Relative strength vs SPY 3-month, Moving-average stack, Proximity to 52-week high,
  Up/down volume, or ATR% volatility) and a **forward horizon** (1 / 5 / 10 / 20 / 60 trading days).
- **Decile table (D1…D10)**: For the chosen factor + horizon, the lab sorts every stored historical
  observation into ten equal-size buckets from the lowest factor value (D1) to the highest (D10) and
  shows, per bucket: the **mean realized forward return** (raw) and a **downside-risk-adjusted** column
  beside it, each with the sample size **n**. Colour grading (green positive / red negative) makes a
  monotone D1→D10 progression visible at a glance.
- **Rank Information Coefficient (rank-IC)**: A single number (with sign and n) summarising how well the
  factor's ranking lines up with the ranking of realized forward returns — positive means a higher
  factor went with a higher return in this universe; negative is the opposite; NA when the sample is too
  thin.
- **Downside-only risk adjustment**: The risk-adjusted column divides the mean return by *downside*
  deviation (only the negative moves count), never total volatility — so a healthy, all-upside bucket is
  not penalised for being volatile. It shows **NA** (not a huge number) when a bucket has no downside.
- **Honest labelling**: Every view carries a survivorship-bias caveat and a "descriptive, not predictive
  / universe-relative" caveat. Buckets with fewer observations than the minimum-sample threshold (30)
  render **"NA" + the sample size** rather than a fabricated number.

---

## Changed Behavior

- **Left sidebar**: gains one new item, **Research** (between System Health and Watchlist). Every other
  page and its navigation are unchanged.

<!-- No existing page's data, contract, or behaviour changed. -->

---

## Backend-Only Items

<!-- None — the new endpoint is fully wired to the new /research page. -->

- None. The new `GET /api/research/factor-lab` endpoint is fully surfaced by the new `/research` page.

---

## Incomplete Items

- None of *this iteration's* scope is deferred. The Factor Lab decile/rank-IC entry point is complete.
- **By design, out of scope** (later `/research` iterations, not this one): multi-factor combination
  cohorts (J-26), regime-conditioned factor effectiveness (J-27), the Setup & Pattern event study with
  MAE/MFE (J-29), the full volatility family (J-30), and the end-to-end synthesis (J-31). The page and
  the read-only analytics engine were built to grow into these without rework.
- **Return/MAE risk ratios** are intentionally deferred to J-29 (they need the post-snapshot daily
  high/low excursion path, which is not yet extracted); this iteration's risk-adjusted column uses
  downside deviation of the stored returns.

---

## Config and Environment Changes

- **`config.yaml` → new `research.factor_lab` block** — holds the **decile count** (`deciles: 10`) and
  the ordered **factor catalog** (8 factors, each with a key, label, family, expected direction, and a
  `source` that says where its stored value is read from). Adding a factor row here makes it appear in
  the dropdown and the API with **no code change**; the decile count is read from here, never hard-coded.
- No environment variables added. No database schema change and **no database regeneration** — the lab
  reads values already stored in `scanner_results` / `forward_returns` from prior iterations.

---

## Known Limitations

- The evidence is **survivorship-biased** (measured on the current-membership universe) and
  **universe-relative**, and is **descriptive, not predictive** — these caveats are shown on the page.
- At the **longest horizon (60 days)** there are fewer historical observations, so deciles are often
  below the 30-sample threshold and honestly render **NA + n** rather than a number. Shorter horizons
  (e.g. 20 days) have enough samples to show real decile means. This is correct, not a defect.
- The factor catalog currently spans the three scores plus five named components (including one
  volatility factor, ATR%). It is deliberately a starter set; more factors are a config-only addition.
- This is a **verify-by-source** session: prior full-depth iterations here have sometimes finished
  without a `status.json` or auditor handoff. This iteration **does** write `status.json`
  (`current_step: dev_complete`); if the downstream auditor handoff is absent, reviewers should verify
  the read-only seam directly in `apps/backend/app/engine/research.py` (SELECT-only; no scoring/return/
  factor call) and de-duplicate any browser evidence by sha256.
