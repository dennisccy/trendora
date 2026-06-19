# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37
**Date:** 2026-06-19
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

No new user capabilities were added in this iteration. All changed files are backend engine internals.

---

## What Changed in the Visible UI

No UI elements changed. The `/data` Data Manager page layout, components, and displayed values are identical to iter-36. The same coverage-diagnostic cards (admitted count, excluded-by-reason: below-history / below-price / below-ADV) and the membership-timeline step-function chart are present and unmodified.

---

## What Old Behavior Changed

**`/data` page — render reliability (indirect, not a UI change):** The bar-cache load-once invariant broken by the iter-36 cold-miss optimization is now restored. A candidate-pool symbol with zero bars was previously re-loaded on every snapshot date and every parallel-worker session during a K-date backfill job, causing unnecessary database pressure. After this fix, such symbols are recorded once in the shared prefill cache and resolve to a trailing count of 0 (`below_history`) from cache — never re-loaded. The served `membership_timeline` payload and all coverage-diagnostic values are byte-identical to what was served before; no displayed number changes.

The practical user-visible effect is that the `/data` page hydrates reliably within the ~30 s live-verify window without the risk of connection-pool exhaustion under a concurrent reader that the iter-36 regression introduced.

---

## Not Visible Yet

- **Residual `GET /api/data` latency (~10–12 s on the full 1370-date database):** The optional coverage-block precompute/cache optimization was descoped by the developer. The `_resolved_universe` / `_coverage_diagnostic_absent` single-as-of resolve inside `compute_coverage` still runs per-request. A second concurrent reader during that window can still pressure the SQLAlchemy connection pool (size 5 + overflow 10). This is documented as a Known Issue in the dev handoff; it does not affect a single sequential page load.
