# Goal Iteration 19 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-19
**Date:** 2026-06-04
**Written by:** developer

---

## Features Implemented

- **Research "All history ⟷ As of date" mode toggle (J-32)**: The `/research` analysis labs gain a single
  page-level toggle. In **All history** (the default) every figure pools every stored snapshot, exactly as
  before. In **As of date** mode, every Factor-Lab decile / rank-IC / regime split, every multi-factor
  combination cohort, and every Setup & Pattern event-study figure is restricted to **only** the snapshots
  dated on or before the date chosen in the existing global top-bar as-of switcher — a point-in-time
  (walk-forward) view. Setting the switcher to an earlier trading day shrinks the sample and shows honest
  "NA" where the early-date evidence is too thin.

- **Inline point-in-time context label**: When As-of mode is active the page shows, in plain language, what
  is being pooled — e.g. "pooling only snapshots dated ≤ 2024-03-15" — reading the date from the single
  global switcher. At the latest date, As-of mode equals All history (and the label says so).

- **Point-in-time scoping on the three research read endpoints (backend)**: `GET /api/research/factor-lab`,
  `/factor-combination`, and `/event-study` now accept an optional `as_of=YYYY-MM-DD` query parameter that
  scopes each lab to snapshots dated ≤ that date. Omitted ⇒ all-history (unchanged default). The scoped
  payload echoes the resolved `asof_date` so the page can label the context.

---

## Changed Behavior

- **`/research` labs**: Previously each lab was a fixed cross-date aggregate over every snapshot with no date
  awareness. Now the same labs additionally offer a point-in-time mode driven by the existing global as-of
  date. The default (All history) view is **byte-identical** to before — no figure changes unless the user
  opts into As-of mode.

- **Research API payloads**: Previously the three research endpoints returned no date field. Now each payload
  carries an `asof_date` field — `null` in all-history mode, the resolved cutoff date when scoped. (This is an
  intentional, J-32-driven contract change; the three `*_no_date_control_present` invariant tests were
  **updated** to the new truth, not deleted.)

- **All-history mode does not refetch on a global-date change**: Moving the global as-of switcher while the
  labs are in All-history mode leaves the research figures unchanged and triggers **no** research network
  call — the read-path discipline (J-15) and the genuine cross-date nature of all-history are preserved.

---

## Backend-Only Items

- None. Every backend capability added this iteration (the optional `as_of` scoping cutoff on the three lab
  functions and endpoints) is wired to the new `/research` mode toggle and visible to the user.

---

## Incomplete Items

- None of the in-scope J-32 items are deferred. (Out of scope and intentionally untouched: J-22 / J-23 / J-24,
  which are externally data-walled and non-halting — no code change here, per the re-scoped goal.)

---

## Config and Environment Changes

- None. No new scoring weight, threshold, cutoff, or config value was introduced. The point-in-time cutoff is
  the existing global as-of date; the "All history" default is a UI mode default, not a magic number. No DB
  regeneration (the scoring/snapshot path is untouched).

---

## Known Limitations

- **Thin samples at early dates are honest, not hidden.** At an early as-of date only a few snapshots qualify,
  so deciles / cohorts / regime cells fall below the configured minimum sample and render "NA + n" rather than
  a number. This is intentional (no fabricated figure fills the gap), but it means very early as-of dates can
  show mostly NA — which is the correct, honest result for a thin point-in-time window.
- **As-of mode at the latest date equals All history.** Choosing As-of mode while the global switcher is on
  the latest date pools every snapshot (the cutoff is "≤ latest"), so it looks identical to All history. This
  is correct (it matches the J-09 "latest equals the full aggregate" rule); the context label explains it and
  invites the user to pick an earlier date to actually restrict the window.
- A production `.next` build exists from the developer typecheck (`npm run build`); browser QA should start a
  fresh `next dev` server (the default of `start-frontend.sh`), which regenerates `.next` for dev mode — avoid
  running `npm run build` against a live dev server (see the dead-shell cache lesson).
