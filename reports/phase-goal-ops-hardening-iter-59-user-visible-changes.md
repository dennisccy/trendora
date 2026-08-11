# Phase goal-ops-hardening-iter-59 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-59
**Date:** 2026-08-11
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open `http://localhost:3255/research/regime-lab` while the server is under heavy
  concurrent memory pressure (e.g., a large historical backfill/warm running in the background) and still
  get a working page. Previously this specific condition could return an unhandled server error with no
  data at all; now the page loads, every horizon that computed successfully shows its real numbers, and
  only the horizon(s) that genuinely could not be computed at that moment show an honest "temporarily
  unavailable" placeholder instead of a blank/crashed page.
- This is a resilience improvement, not a new feature the user opts into — there is no new button, toggle,
  or setting. The user's only new observable option is that the Regime Lab page keeps working (in a
  degraded-but-honest form) in a situation where it previously could fail outright.

---

## What Changed in the Visible UI

- On `/research/regime-lab`, both the "By regime label" table and the "By regime-score decile" table's
  forward-return ("Fwd 1d/5d/10d/20d/60d") and max-drawdown ("MDD 1d/5d/10d/20d/60d") cells can now show a
  new, distinct NA reason: hovering an "NA" cell that is unavailable due to memory pressure shows the
  tooltip **"Temporarily unavailable — degraded under memory pressure"** — worded differently from the two
  pre-existing NA tooltips ("Low sample — n below the 30 minimum" and "No observations" / "No stored
  drawdown — NA") so a user (or an operator reading a screenshot) can tell a genuine data gap apart from a
  transient server-load condition.
- Under normal operating conditions (the server not near its memory ceiling), nothing on `/research/regime-lab`
  looks or behaves any differently than before this phase — every displayed number is proven
  byte-identical to the pre-phase computation (verified by an automated equality test against a pinned
  reference, across every configured horizon, with and without an as-of date).
- One row type on the "By regime-score decile" table — the "Rank-IC" header row — does **not** get the new
  distinct tooltip. If its horizon degrades, it still renders as plain "NA" with the existing generic
  tooltip ("Not enough independent observations to rank-correlate — NA, not a fabricated 0"), not the new
  "Temporarily unavailable" wording. This is a disclosed, intentional scope gap (see "Not Visible Yet"
  below) — the cell is still honestly NA, just without the more specific explanation.

---

## What Old Behavior Changed

- **Regime Lab page under memory pressure:** previously, if the backend hit its declared memory ceiling
  while computing Regime Lab (which retained every configured horizon's full observation set in memory at
  once), the request could raise an unhandled error. The user-visible result was the page's generic error
  card — "Backend unavailable — The Regime-Lab evidence could not load from the API. No figures are shown
  rather than fabricated values. Confirm the backend is running and retry." with a "Retry" button — losing
  **all** horizons' data, even ones that would have computed fine. Now, under the same memory-pressure
  condition, the page loads normally: every horizon that can complete shows its real numbers, and only the
  horizon(s) that genuinely could not complete show the contained "temporarily unavailable" NA cells
  described above. The rest of the page is unaffected.
- No other page's visible behavior changed. The backend restart / cold-load verification also executed
  this iteration (killing and restarting the backend, then loading `/data`, `/scanner-runs`, and the home
  market-phase card) exercised already-shipped, unchanged code — it confirmed those pages still serve
  stored data quickly after a real restart, but no code driving what those pages look like or do was
  modified this iteration.

---

## Not Visible Yet

- The backend payload's degraded-horizon signal is also present on each `rank_ic_by_horizon[]` entry
  (`status: "unavailable"`), but the frontend's Rank-IC row does not yet read that field — it falls back to
  its pre-existing null-value NA handling with generic wording (see above). This is a disclosed, deliberate
  scope boundary (the phase plan named only the by-label and by-decile cells), not an oversight discovered
  late.
- The underlying reliability fix — bounding `compute_regime_lab` to process one horizon at a time instead
  of holding every horizon's data in memory simultaneously — has no user-visible surface of its own; it
  only becomes observable indirectly, through the "temporarily unavailable" cells described above, and only
  during genuine memory pressure. There is no settings page, admin panel, or indicator anywhere in the UI
  that shows current memory usage or whether this safeguard has ever triggered.
