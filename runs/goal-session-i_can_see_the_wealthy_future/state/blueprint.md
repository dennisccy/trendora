# App Blueprint — i_can_see_the_wealthy_future (Trendora)

<!--
Coherence contract for the whole app. Drafted by the goal-decomposer at baseline; you approve it once
(edit anything, then `--resume`); the coherence-auditor enforces it every iteration.

REVIEW CHECKLIST (before you resume):
  1. Information Architecture — are the nav sections sensible, and does every journey have an obvious
     home reachable in <=2 clicks? Stock Detail and Run Detail are intentionally reached from a row,
     not the top nav.
  2. Data Contract — is every "same-number-everywhere" value listed with exactly ONE computing module
     and ONE serving path? The six canonical scores + A-E bucket + setup status are the critical ones
     (J-06). Add any I missed; fix any wrong source. Module paths (app.engine.*) are proposals for
     iter-1+ to create — rename here if you prefer a different layout.
-->

## Information Architecture

**Layout shell:** Left persistent sidebar (nav) + main content area — a dense, dark analytical
workstation. Numbers are monospace/tabular; every score shows its **A–E bucket first, raw 0–100
secondary**. Single mobile breakpoint ~640px (wide tables scroll horizontally). The backend is the
single source of truth; every page only re-formats server-computed values and never recomputes a
score, bucket, or return.

**Navigation skeleton** (the persistent sidebar — every feature lives under one of these):

```
Trendora
├── Dashboard        /                       (J-01)
├── Stocks           /stocks                 (J-02, J-06)
│   └── Stock Detail /stocks/[ticker]        (J-05, J-06)   — opened from a leaderboard row, not the nav
├── Themes           /themes                 (J-03)
├── Sectors          /sectors                (J-04)
├── Scanner Runs     /scanner-runs           (J-08)
│   └── Run Detail   /scanner-runs/[runId]   (J-07, J-08)   — opened from a run row
├── System Health    /system-health          (J-09, J-10)
└── Watchlist        /watchlist              (J-11)
```

**Feature / journey homes** (each reachable in ≤2 clicks from the sidebar):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 Daily dashboard at a glance | `/` | Dashboard |
| J-02 Stock Leaderboard + working filters | `/stocks` | Stocks |
| J-05 Stock Detail with explainable scores | `/stocks/[ticker]` | Stocks (row → detail) |
| J-06 Score consistency across pages | `/stocks` ↔ `/stocks/[ticker]` | Stocks |
| J-03 Theme Leaderboard | `/themes` | Themes |
| J-04 Sector / industry Leaderboard | `/sectors` | Sectors |
| J-08 Immutable scanner-run history | `/scanner-runs` | Scanner Runs |
| J-07 Risk-Off regime suppresses Actionable | `/scanner-runs/[runId]` | Scanner Runs (row → detail) |
| J-09 System Health forward-tested evidence | `/system-health` | System Health |
| J-10 Control-group honesty (selection vs sector beta) | `/system-health` | System Health |
| J-11 Watchlist with persistence | `/watchlist` | Watchlist |

## Data Contract

Every value below is computed **once** by the scoring / regime / forward-testing engine during a scan
(or the forward-returns job), **stored** on an append-only snapshot table, and only re-formatted by the
API/UI. No page recomputes or re-fetches a value from a second code path; the frontend never recomputes
a score, bucket, or return. Module paths under `apps/backend/app/`.

| Value / entity | Computed by (single module/function) | Served by (canonical endpoint) | Notes |
|---|---|---|---|
| Market Regime score + label | `app.engine.regime:score_regime` | `GET /api/runs/{run_id}` | 0–100 + one of 6 labels; stored on `scanner_runs`. Dashboard shows the latest run's **stored** value via `GET /api/dashboard` (no recompute). |
| Candidate counts (# Actionable / Breakout-watch / Pullback-watch) + market breadth % + last-scan ts | `app.engine.scanner:summarize_run` | `GET /api/dashboard` | counts derived once from the run's stored setup statuses; breadth labelled **universe-relative**. Same stored summary on run-detail. |
| Sector / industry score | `app.engine.sectors:score_sector` | `GET /api/sectors` | per sector/industry ETF, per run; stored on `sector_scores`. Row also carries RS-vs-SPY, dist-from-52w-high, trend label (J-04). SPY shown as 0% RS reference, not ranked vs itself. |
| Theme score | `app.engine.themes:score_theme` | `GET /api/themes` | per theme, per run; stored on `theme_scores`. Row also carries members, 1m/3m basket return, breadth %, trend label (J-03). Price-confirmed, not news-driven. |
| Leadership / Entry Quality / Risk score (per stock) | `app.engine.scoring:score_stock` | `GET /api/stocks` (list) **and** `GET /api/stocks/{ticker}` (detail) | each 0–100 with named component breakdown; stored once on `scanner_results`. Leaderboard and detail read the **same stored row** → J-06. Never collapsed into one "buy" number. |
| A–E bucket | `app.engine.buckets:to_bucket` (config edges) | (rides on each score it labels) | derived once from a stored score by the single bucketing fn; never re-derived in the API or UI. |
| Setup status (per stock) | `app.engine.setups:classify_setup` | (rides on the stock rows above) | one of: Actionable / Pullback-watch / Breakout-watch / Extended / Avoid / Risk-off-watchlist. **Risk-Off regime ⇒ zero "Actionable"** (J-07). |
| Score component breakdown + reason + invalidation | (emitted by the scoring fns above) | (same stock endpoints) | stored as `components_json`; the source of the reason summary. Every displayed score carries it — no bare numbers. |
| Forward-return aggregates (by bucket A–E / by setup / by regime; excess vs SPY/QQQ/sector; control-group cohorts) | `app.engine.forward_testing:compute_forward_aggregates` | `GET /api/system-health` | from stored snapshots + **post-snapshot** prices only (no-lookahead); each cell carries sample size `n`; evidence labelled as carrying survivorship bias. Stored in the append-only `forward_returns` table — snapshots never mutated. |
| Watchlist entry (date-added, reason, current score/setup, price-since-added, invalidation) | reuses stored `scanner_results` (current score/setup) + `app.engine.indicators` (price-since-added) | `GET /api/watchlist` (`POST` add, `DELETE` remove) | persisted in DB (survives restart, J-11); current score/setup READ the canonical stored values — no second computation. |

Health probe: `GET /api/health` → `{"status":"ok", ...}` (no canonical value).

### Iteration serving notes (additive; no nav/source change)

- **Module home:** the `app.engine.*` computing modules above live under **`apps/backend/app/engine/`** (reconciles the design doc's flat `app/<module>/` with this contract's `app.engine.*` — resolved in iter-2 when the first engine modules were created).
- **iter-2 (Regime + Sectors) serving model:** the Market Regime score+label and the Sector/industry scores are computed **on-request, deterministically** from the frozen seed via an as-of accessor (`bars_asof`, date ≤ d) and served by their canonical endpoints (`/api/dashboard`, `/api/sectors`). **Persistence** of these values into the append-only snapshot tables (`scanner_runs`, `sector_scores`) and the "scan ran at" run timestamp arrive with the scanner in **iter-5**; until then the displayed "Data as-of <date>" is the latest seed date. Single-source-of-truth still holds: one computing module + one serving endpoint per value, deterministic output.
- **Dashboard ↔ Sectors:** the Dashboard's "Top Sectors" list **reads the canonical `GET /api/sectors`** (frontend slices the top N) — it does NOT recompute or re-serve the sector score from a second path.
