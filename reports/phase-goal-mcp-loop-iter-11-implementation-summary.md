# goal-mcp-loop-iter-11 — Implementation Summary

**Phase:** goal-mcp-loop-iter-11
**Date:** 2026-07-01
**Written by:** developer

---

## Features Implemented

- **Per-horizon "Proven / Not yet proven" badges on the Factor Lab**: On the Research Factor Lab page
  (`/research/factor-lab`), each factor's evidence status is now shown separately for every time horizon the
  platform tests (1, 5, 10, 20, and 60 trading days) instead of only one. This makes it visible that a factor
  can be proven at one holding period and unproven at others.
- **A newly proven long-horizon edge is now surfaced**: The `vcp_contraction` factor's top-decile group is
  shown as **"Proven" at the 60-day horizon** — the first edge the platform proves beyond the 20-day window.
  Its shorter horizons (1/5/10 days) honestly read **"Not yet proven"**. Clicking the 60-day "Proven" badge
  jumps to its supporting entry on the Evidence page.
- **A new row on the Evidence ledger** (`/evidence`): an auditable certified-claim for `vcp_contraction —
  top decile (D10)` at the 60-day horizon, showing the out-of-sample result (+8.91%), the comparison versus
  the SPY benchmark (+8.91%), the registration date, a "Pending" forward-walk score, and a link back to the
  Factor Lab. Its wording notes the "60-day hold" so it is not confused with the existing 20-day entry.

---

## Changed Behavior

- **Factor Lab evidence column**: Previously showed a single evidence badge per factor (at the 20-day default
  horizon). Now shows one badge per horizon (a compact strip), each with its own proven/not-proven status and
  its own link to the backing evidence. The 20-day badge behaves exactly as before (no regression).
- **Evidence ledger**: Previously listed four certified claims. Now lists five — the four prior ones are
  unchanged, plus the new 60-day `vcp_contraction` row.

---

## Backend-Only Items

- None. The one backend change was the certified-claim itself (the 5th ledger entry), which was produced by
  the automated evidence gate before development began — not by this work — and it is fully surfaced in the UI
  (Evidence row + Factor Lab badge). No backend application code was written or modified this phase.

---

## Incomplete Items

- None deferred within this phase's scope. The related **J-08** journey (a proven multi-factor *combination*
  on the Combination Lab) is intentionally out of scope and planned for a later iteration.

---

## Config and Environment Changes

- None. No new environment variables, no config file changes, no database migrations. The Evidence endpoint
  reads the same ledger file it always has; this phase only added one more row to that file (via the gate) and
  displayed it.

---

## Known Limitations

- **On-screen verification pending**: The logic and the live data feed were verified (unit tests + a live
  check of the Evidence API returning the new row with correct numbers). The actual visible badge flip in a
  real browser is confirmed by the separate automated browser-QA step later in the pipeline.
- **Every factor row now shows five status chips**: This is the intended "honest per-horizon" view — most
  factors will show "Not yet proven" at all five horizons, which is correct (they are genuinely unproven).
  Rows are slightly taller as a result. This is by design and matches the platform's evidence-first style.
- **The `leadership_score` factor row reads "Proven" at 20 days**: This is honest — it has a genuine passing
  certified claim — and was deliberately not hidden or special-cased.
