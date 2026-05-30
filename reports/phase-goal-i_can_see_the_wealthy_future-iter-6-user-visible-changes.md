# Phase goal-i_can_see_the_wealthy_future-iter-6 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future-iter-6 — Walk-forward forward-testing engine + System Health evidence (J-09, J-10)
**Frontend Present:** yes
**Date:** 2026-05-30
**Analyst:** ui-impact-analyst

> Note: this report was authored under a degraded tool harness (the read/bash result channel went empty after the initial artifact reads — exactly the "queuing/flaky tool harness" the spec anticipates). It is derived from the phase spec, the dev handoff, and the frontend handoff, all of which were read in full.

---

## Summary

Trendora's **System Health** page (`/system-health`) graduates from an empty placeholder ("EmptyState stub") into a populated, forward-tested **evidence dashboard**. For the first time, the user can open one page and read hard, walk-forward evidence about whether the scanner's own rankings actually predicted better realized stock returns — broken out by score bucket, setup type, and market regime, measured against SPY/QQQ/sector ETFs and against random same-sector peers, at a horizon the user chooses. Every figure carries its sample size `n` and a prominent survivorship-bias caveat so nothing is overstated.

This is the product's "prove its own usefulness" milestone: Trendora moves from "it ranks and explains" to "it ranks, explains, **and shows whether the rankings have positive forward-tested evidence**."

---

## What users can now do

1. **Open System Health and read forward-tested return evidence.** The previously empty `/system-health` page now shows real numbers derived from replaying past scans and measuring their realized forward returns.
2. **Choose a forward-return horizon (1d / 5d / 10d / 20d / 60d).** A segmented horizon selector (default 20) re-fetches and updates every panel on the page. Horizon options come from the server payload, not a hard-coded list.
3. **See forward return by score bucket (A–E).** A table shows the mean realized forward return and the sample size `n` for each grade bucket, so the user can judge whether higher-graded buckets actually returned more.
4. **See excess return vs benchmarks.** "Excess vs SPY" and "Excess vs QQQ" panels show the cohort mean return, the benchmark mean, and the excess (difference) — each with `n`.
5. **See forward return by setup type and by market regime.** Two breakdown tables show mean return + `n` per setup and per regime; both Risk-on and Risk-off regime rows appear.
6. **Compare against a control group (J-10).** A control-group panel shows, at the selected horizon, the top-ranked cohort (highlighted) alongside a random same-sector cohort, SPY, QQQ, and the sector ETF — each numeric, labelled, and with `n`.
7. **Read the honesty context.** A prominent survivorship-bias banner (server-provided text), per-figure sample sizes, and a low-sample flag (`n < min_sample ⚠`) make the strength and limits of the evidence explicit. Positive returns render in the positive palette, negative in the negative palette.

---

## What changed in the visible UI

| Surface | Before | After |
|---------|--------|-------|
| `/system-health` page | iter-1 EmptyState stub (placeholder, no data) | Multi-panel evidence dashboard (~4.44 kB route) |
| Horizon selector | did not exist | segmented 1/5/10/20/60 button group (default 20), `aria-pressed`, re-fetches on change |
| By-bucket table | did not exist | A–E rows, colour-graded bucket badge, mean return + `n` |
| Excess vs benchmarks | did not exist | Excess vs SPY and vs QQQ, each: cohort mean, benchmark mean, excess, `n` |
| By-setup / by-regime breakdowns | did not exist | two tables, mean + `n`; Risk-on and Risk-off both present |
| Control-group panel | did not exist | top-ranked (highlighted) vs random same-sector vs SPY / QQQ / sector-ETF, each numeric + `n` |
| Survivorship-bias banner | did not exist | prominent warn-toned banner rendering server text verbatim |
| Summary strip | did not exist | snapshots contributing, as-of date range, overall mean forward return, low-sample legend |
| Loading / error / empty states | n/a (stub) | skeleton on load; red alert when backend unavailable (no fabricated figures); explicit EmptyState when `n_runs === 0` or horizon has no data |

---

## What behavior changed (existing features that work differently)

- **Scanner Runs history (J-08) now lists more dated runs.** The walk-forward backfill persists additional immutable `scanner_run` snapshots (8 quarterly cadence as-of dates over 2 years, on top of the 3 existing bootstrap runs = 11 runs total). These new as-of snapshots will appear in the Scanner Runs history. Per the spec this is **intended product behavior** (immutable as-of history), **not a regression** — existing run rows are unchanged and INSERT-only.
- **No other page changes.** The sidebar is unchanged (the System Health link already existed). All other endpoints/pages (`/api/dashboard`, `/api/stocks`, `/api/sectors`, `/api/themes`, bars, `/api/runs`) are untouched — J-01–J-08 are required to stay green.

---

## What is NOT visible yet (backend capability without dedicated UI)

- **`GET /api/system-health?horizon=` endpoint** — fully consumed by the new page, so its aggregates ARE visible; but its lower-level building blocks are backend-only:
  - **`forward_returns` append-only table** and the per-`(run, symbol, horizon)` realized returns — not directly browsable; surfaced only in aggregate form.
  - **`bars_after` / `close_on` price accessors** and the `forward_return` pure function — internal no-lookahead machinery, no UI.
  - **`backfill_forward_returns` lifespan job** — runs at server boot (~223 s on a fresh DB; idempotent and fast thereafter); no UI, but its effect is the populated dashboard and the extra Scanner Runs entries.
- **Control-group RNG seed / config parameters** (`walk_forward.control_group.{seed, top_n, peers_per_sector}`, `default_horizon`, `asof_cadence`) — config-only; their effect is visible in the cohorts shown, but the parameters themselves are not exposed in the UI.

---

## Anti-goal / honesty checks reflected in the UI

- **Survivorship-bias label** is prominent and per-payload — evidence is the current-membership universe (an upper bound).
- **Sample size `n`** is shown beside every figure; figures with `n < min_sample` are visibly flagged (warn token), never hidden.
- **No fabrication:** a run with zero post-snapshot bars (the latest seed date) contributes `n=0` and no figure; low-sample and no-data states are explicit (EmptyState / flags), and backend-down renders a red alert, not zeros.
- **Single source of truth:** the page re-formats the one `/api/system-health` payload and never recomputes a return, excess, or bucket.

---

## Suggested user journey to verify (for QA / browser-QA)

1. Navigate to `/system-health` (allow generous readiness time if the backend was restarted on a fresh DB — first boot runs the ~223 s backfill).
2. Confirm the page is populated (not the old EmptyState) and the survivorship-bias banner is visible.
3. Read the A–E bucket table, excess-vs-SPY/QQQ, by-setup, and by-regime panels — each shows numbers and an `n` (J-09).
4. Confirm the control-group panel shows top-ranked vs random-same-sector vs SPY/QQQ/sector-ETF, each numeric and labelled (J-10).
5. Change the horizon selector (e.g. 20 → 5) and confirm the figures update.
