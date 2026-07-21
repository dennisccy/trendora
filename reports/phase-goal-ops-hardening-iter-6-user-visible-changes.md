# Phase goal-ops-hardening-iter-6 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-6
**Date:** 2026-07-21
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- None. This iteration was scoped as a pure request-timing fix closing J-06 ("Pages load only what they
  need") — no new endpoint, no new displayed value, no new button, form, or navigation entry was added
  anywhere in the product. Every value the Dashboard and Data Manager show was already visible before this
  iteration; only WHEN the underlying network requests fire changed.

---

## What Changed in the Visible UI

- Nothing changed in appearance, labels, or layout. Both touched components (`PhaseCrossViewCard` on `/`
  and the availability heatmap's data loader on `/data`) render their existing loading skeleton, error
  card, and empty state exactly as before — confirmed live by the developer via screenshot and DOM-text
  checks. A user looking at either page cannot tell, by sight alone, that anything changed — the only
  difference is how quickly the real data replaces the loading placeholder.

---

## What Old Behavior Changed

- **Dashboard (`/`) — the "Regime × phase cross-view" chart card now finishes loading noticeably faster
  under real browser use.** Previously, this below-the-fold card's own data (index history, regime
  history, market-phase timeline) could take up to ~2.2 seconds to arrive after page load, occasionally
  spilling past the page's committed budget while competing with the rest of the page's on-load requests.
  It now consistently arrives in under a second (821–872ms across 3 real-browser reloads). The card's
  existing `animate-pulse` skeleton placeholder covers the whole wait either way — before or after this
  fix, the card was never blank — but the wait itself is shorter. As an intentional side effect of how the
  fix works, the card's own fetch now deliberately waits an extra 250ms after the page mounts before it
  even starts (to let the page's other on-load requests clear first) — invisible to the user because the
  skeleton already covers that window, and still a net speed win overall.
- **Data Manager (`/data`) — the coverage/availability heatmap now finishes loading faster too, and gains
  its first documented speed commitment.** Previously this heatmap's data could take 2.8–3.0 seconds to
  arrive under real browser use (a number never previously tracked as a budget). It now arrives in
  roughly 1.0–1.05 seconds (3/3 real-browser reloads), matching the page's other data. As with the
  Dashboard, the fix works by deliberately delaying this specific fetch — this time by 2.5 seconds after
  the page's overview data starts loading — so a user watching closely will see the heatmap's own
  `Loader2` spinner and "Loading availability…" text for a bit longer before its own request fires; the
  heatmap's total time-to-data is still faster than the old, unstaggered behavior because the old version
  suffered a worse queuing/contention delay instead.
- **Not fixed this iteration — flagged, still present:** while re-measuring every J-06 page for this
  iteration, the developer found that the Evidence Ledger (`/evidence`) and one `/research` event-study
  lab page (`view=episodes`) are now severely over their ≤1.5s load budget for reasons unrelated to this
  iteration's code changes — a pre-existing backend computation that scales badly as the live database has
  grown across recent iterations. `/evidence` measured **555.97 seconds** (over 9 minutes) to first load
  with a cold cache (previously ~9.3–9.6s as of iter-5); the `/research` event-study lab measured **~92
  seconds** cold (previously ~0.003–0.005s) and **~1.46 seconds** even once warm/cached (previously also
  near-instant). Anyone opening either page today should expect this multi-second-to-multi-minute wait.
  This was discovered, not caused, by this iteration — no file under `apps/frontend/app/evidence/`,
  `apps/frontend/app/research/`, or any backend module was touched — and is explicitly left unfixed,
  flagged for a dedicated follow-up iteration rather than folded into this one's scope.

---

## Not Visible Yet

- None. No new backend capability was introduced this iteration that would need a UI wiring step — the
  fetch-timing fix is entirely internal to the existing render contract of two already-shipped components.
