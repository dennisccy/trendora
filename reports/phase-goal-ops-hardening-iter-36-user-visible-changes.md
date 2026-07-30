# Phase goal-ops-hardening-iter-36 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-36
**Date:** 2026-07-30
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On `/research/factor-lab`, when the Factor Lab data is slow to load (cold cache, past a 3-second grace window), users now see a labelled "Still computing — Ns elapsed" card with a spinner instead of a bare unlabelled grey skeleton.
- On the same page, if the backend is unreachable, users now see a "Backend unavailable" card with a working **Retry** button (previously the error card had no way to retry — the user had to manually reload the whole page).
- On `/research/phase-severity-lab`, the same two upgrades apply: a labelled "Still computing — Ns elapsed" card during a slow load, and a working Retry button on the error card.
- On `/research/regime-phase-factor`, the same two upgrades apply, using the page's own existing "Backend unavailable" card design (not the shared error card) — clicking its new **Retry** button re-attempts the fetch.
- On `/research/severity-velocity`, the same two upgrades apply: a labelled "Still computing — Ns elapsed" card during a slow load, and a working Retry button on the error card.
- All 5 Research labs (`/research/regime-lab` plus the 4 above) now behave identically on a slow or failed load — previously only Regime Lab had the computing notice and Retry button.

---

## What Changed in the Visible UI

- `/research/factor-lab`: the pre-data loading area now conditionally renders a `SlowComputeNotice` card ("Still computing — Ns elapsed", spinner, explanatory copy) once a fetch has been pending 3+ seconds; the error card now includes a "Retry" button.
- `/research/phase-severity-lab`: same change — `SlowComputeNotice` on a slow load; error card gains a "Retry" button.
- `/research/regime-phase-factor`: same computing notice added above its existing `CombinationSkeleton`; its own inline "Backend unavailable" card gains a new "Retry" button (`data-testid="rpf-error-retry"`).
- `/research/severity-velocity`: same change — `SlowComputeNotice` on a slow load; error card gains a "Retry" button.
- No navigation, layout, or new page was added. No new data field or number appears anywhere — the visual change is confined to the pre-data (loading/error) state of each of the 4 pages.
- `/data`'s coverage/membership-timeline panel and `/evidence`'s per-claim expectations panel show byte-identical numbers before and after this phase — the backend fixes behind them are internal memory-bound changes only; nothing about what a user sees on those two pages changed.

---

## What Old Behavior Changed

- On `/research/factor-lab`, `/research/phase-severity-lab`, and `/research/severity-velocity`: previously a slow load stayed on a plain, unlabelled skeleton indefinitely with no explanation and no way to retry a failure; now a slow load becomes an explicit, time-stamped notice, and an error state is retryable in place (click Retry re-enters the loading state — never a second frozen error card).
- On `/research/regime-phase-factor`: previously the error card had no Retry action; now it does, using the page's own existing card design.
- Backend-only: `/api/data`'s coverage/membership-timeline computation and `/api/evidence`'s per-claim drawdown-expectations computation now use bounded/chunked memory reads internally instead of loading the whole candidate pool or whole cohort at once — this reduces the chance either panel falls back to its existing "not available right now" placeholder under heavy load, but does not change what is displayed in the normal case (byte-identical payload).

---

## Not Visible Yet

- The reduced (but not eliminated) risk of the Evidence page's per-claim "drawdown & dry-spell expectations" panel showing its honest "not available right now" placeholder under very heavy concurrent load — this backend fix is a partial (~4%) memory reduction, not a full guarantee; the placeholder can still appear under sufficiently heavy load, exactly as it could before this phase (just less often). There is no new UI state for this — it reuses the existing `expectations_status: "unavailable"` disclosure from a prior phase.
- Regime Lab's own known cold-load background-dispatch issue (an intermittent HTTP-200 body carrying "Internal Server Error" text) is unchanged — explicitly out of scope for this phase.
