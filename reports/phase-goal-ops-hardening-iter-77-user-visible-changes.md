# Phase goal-ops-hardening-iter-77 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-77
**Date:** 2026-08-13
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see how old the readiness/status information they are looking at is: whenever the
  top-bar status badge (present on every page) reflects a cached read rather than a fresh one, it now
  shows a short "as of Ns ago" note (e.g. "as of 3s ago") right next to the "Ready"/"Initializing…"/etc.
  pill. This never appears for a fresh/synchronous read (`stale_for_s === 0`) and never appears if the
  backend can't be reached — no fabricated number is ever shown.
- Users can now see the same "as of Ns ago" staleness note on the preflight banner (the thin strip under
  the top bar reading "GO — today's board is current." or the louder DEGRADED/NO-GO banner) — confirmed
  live: `GO — today's board is current.  (as of 0s ago)`.
- At a 1280×800 browser window, users can now still see the "Ready"/status pill at the same time as a
  "background compute running (N)" chip. Previously the pill could be pushed off the visible top bar and
  disappear when both were competing for the same row's width; the row now wraps onto a second line
  instead.

---

## What Changed in the Visible UI

- The global top-bar badge row (every page, rendered from `app/layout.tsx` + `components/health-badge.tsx`)
  now shows an inline "as of Ns ago" text annotation (`data-testid="readiness-staleness"`) next to the
  readiness pill, whenever the polled status is genuinely stale.
- The preflight banner (every page, rendered from `components/preflight-banner.tsx`, directly under the
  top bar) now shows the same "(as of Ns ago)" annotation (`data-testid="preflight-staleness"`) appended
  to its "GO — today's board is current." text, or to its "DEGRADED — treat today's board with caution."
  / "NO-GO — do not rely on today's board." heading, whenever stale.
- The top-bar badge row (readiness pill + staleness note + background-compute chip + provider/seed/symbol
  badges) now wraps onto a second line when its combined content doesn't fit at the current window width
  — visually confirmed at 1280×800 with a live screenshot showing the pill, the staleness note, and the
  "background compute running (5)" chip together on the first line and the remaining badges wrapping to a
  second line, instead of any of them being cut off/hidden.
- The `/backtest` page's forward-test scorecard table rows each gained a hidden `data-testid` attribute
  (`scorecard-row-1d`, `scorecard-row-5d`, `scorecard-row-10d`, `scorecard-row-20d`, `scorecard-row-60d`)
  — this is a QA/automation hook only; nothing a user sees changes on this page.

---

## What Old Behavior Changed

- **Top-bar badge row at narrow/crowded widths**: previously, at a 1280×800 window with a
  background-compute chip also displayed, the "Ready"/status pill could be pushed past the visible top
  bar and effectively disappear (iter-76 regression). Now the row wraps onto a second line and the pill
  stays visible. The header itself grows slightly taller (a fixed `min-h-14` that expands only when
  wrapping actually happens) instead of staying a strict single 56px line in that specific crowded case;
  on every page/width where content already fit on one line, nothing changes.
- **Frontend launch script reliability (`scripts/start-frontend.sh`)**: previously, if the frontend was
  launched twice in close succession (or two launch processes overlapped), a visitor could occasionally
  land on a broken/unstyled version of the page (a partially-built payload served mid-rebuild) — an
  intermittent defect that had gone unfixed for four prior rounds. The script now serializes its
  build-then-serve sequence with a lock, so two overlapping launches can no longer race on the same build
  output. This is a launch-time reliability fix, not a click-path a user can trigger from within the
  running app — it cannot be exercised through normal browsing, only by launching the script concurrently
  (which is what the accompanying automated regression tests do).

---

## Not Visible Yet

- None. The `stale_for_s` value has been computed and served by `GET /api/health` since a prior round
  (iter-71); this iteration is its first and only UI consumer, so there is no remaining backend-only gap
  for this capability.
- The walkthrough-recorder fix (`scripts/automation/lib/demo_runner.py`) is an internal showcase/QA
  tooling change (fixes before/after screenshots used in generated demo walkthroughs) — it has no
  end-user-facing surface at all; it is not a product capability, so it is not listed as a UI gap.
