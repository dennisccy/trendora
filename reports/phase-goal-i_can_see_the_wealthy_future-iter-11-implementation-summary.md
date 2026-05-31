# Goal iter-11 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future-iter-11
**Date:** 2026-05-31
**Written by:** developer

---

## Features Implemented

- **VCP detection (the product's first detected price pattern)**: Trendora now flags stocks showing a
  **Volatility Contraction Pattern** — progressively-shallower pullbacks with volume drying up into a
  pivot near the recent high. The flag is computed once per scan (price + volume only, using only data
  up to the scan's date) and carries a plain-language reason, the **pivot** (breakout level) and a
  concrete **invalidation level** (the last-contraction low).
- **VCP filter on the Stock Leaderboard** (`/stocks`): a new "VCP" dropdown (All / VCP only / Non-VCP)
  narrows the table to flagged names. On the latest seed snapshot it shows the 4 flagged names
  (STX, TSLA, TSM, ORCL); when a snapshot has none it shows an honest empty-state.
- **VCP badge on flagged rows + the Stock Detail page**: a compact teal "VCP" badge sits next to the
  setup status (its tooltip carries the reason, pivot and invalidation). The detail page adds a
  dedicated "VCP — Volatility Contraction Pattern" card showing the reason, the pivot, the invalidation
  level and the contraction depths. The exact same values appear on the leaderboard and the detail page.
- **VCP-vs-non-VCP forward-return breakdown on System Health** (`/system-health`): a new panel showing
  the mean realized forward return of VCP-flagged names vs non-VCP names, each with its sample size `n`
  (flagged ⚠ when below the minimum sample). On the seed: VCP **+3.18% (n=27 ⚠)** vs non-VCP **+2.01%
  (n=1191)** at the 20-day horizon — VCP names historically outperformed, shown honestly as low-sample.

---

## Changed Behavior

- **Stock scan record**: every stored per-stock result now also carries the VCP block. The three
  scores, A–E buckets, setup status, reason and invalidation are **unchanged** — VCP is purely
  additive and never alters a name's setup status (e.g. STX is "Extended" + VCP; TSLA/TSM/ORCL are
  "Avoid" + VCP; none became "Actionable" from the flag).
- **System Health payload** gains one extra breakdown (`by_vcp`); all existing breakdowns
  (by bucket / setup / regime, excess vs SPY/QQQ, control groups) are unchanged.
- **The local database is rebuilt from the frozen seed** on this iteration's first boot so the new VCP
  mirror column is populated for every snapshot. This is a deterministic re-creation from the committed
  seed (reproducibility), not a mutation of any existing snapshot.

---

## Backend-Only Items

- None. Every backend capability added this iteration is surfaced in the UI (leaderboard filter + badge,
  detail card, System Health panel).

---

## Incomplete Items

- **`/methodology` glossary entry for VCP (J-12)** is intentionally **out of scope** this iteration and
  is sequenced as the next iteration (it adds a navigation route). The VCP reason/thresholds are
  config-backed so that page can render them with no code change. This deferral is by design, not a gap.

---

## Config and Environment Changes

- `config.yaml` — **new `patterns.vcp` block** holding every VCP threshold (no value is hard-coded in
  code): `lookback_bars`, `min_contractions`, `max_contractions`, `min_contraction_pct`,
  `max_base_depth_pct`, `contraction_shrink_ratio`, `max_last_contraction_pct`, `pivot_proximity_pct`,
  `volume_dryup_ratio`, `volume_window`, `min_history_bars`. Tuned against the committed seed so the
  latest snapshot flags a sensible, non-trivial set (4 names) — never loosened to fabricate flags.
- No new environment variables. No secrets. The offline seed remains the default data source.
- **Operational note for QA/operators**: the gitignored `apps/backend/data/trendora.db` must be deleted
  once so the backend re-creates it from the seed with the new `is_vcp` column (the schema is created on
  startup, not altered in place). The first boot runs the walk-forward backfill and takes a few minutes.

---

## Known Limitations

- **The VCP forward-test cohort is small (n=27 at 20 days, below the 30 min-sample).** This is shown
  honestly with an ⚠ low-sample marker — the edge (+3.18% vs +2.01%) is indicative, not conclusive, and
  inherits the same survivorship-bias caveat as the rest of System Health.
- **VCP detection is selective by design.** Whether a given snapshot flags any names depends on that
  date's market. The latest seed date flags 4; some historical snapshots flag 0 and correctly show an
  empty-state / NA rather than a fabricated pattern.
- **The detector evaluates daily price + volume only** (no intraday, no fundamentals), consistent with
  the product's end-of-day scope. Names with fewer than `min_history_bars` of history are reported as
  not-flagged (NA), never with a fabricated pivot.
