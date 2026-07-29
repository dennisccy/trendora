# Phase goal-ops-hardening-iter-33 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-33
**Date:** 2026-07-29
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

None. This iteration is a defect fix to the frontend launcher script, not a new capability. It does not
add any new page, button, form, chart, or data field. Per the plan's own UI Evolution section ("New
user-facing capability: none... a defect fix to the frontend's serving mode for automated evidence
capture/measurement, not a new user-visible capability") and the phase spec's Definition of Done, no
product action was added.

---

## What Changed in the Visible UI

- **Every page served through `scripts/start-frontend.sh`** (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`,
  `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/regime-lab`) now
  renders from a genuine Next.js **production build** instead of the dev-mode on-demand compiler. This is
  a launch-mode change, not a page-content change — the same components, same data, same layout.
- **The Next.js dev-mode error-overlay pill no longer appears** on any page served by this launcher
  (production builds don't ship that overlay). This is the one incidental visible difference the dev
  handoff and plan both call out — it only ever mattered if a page had errored while running under the
  old (mistakenly dev-mode) launcher.
- **First-visit page loads should feel faster** through this launcher, since pages are pre-compiled
  ahead of time rather than compiled on demand per-request the way `next dev` does. The dev handoff's own
  pre-handoff spot check (curl on all 11 pages, all HTTP 200, `GET /api/health` in 0.092s, `next start`
  reporting "Ready in 266ms") supports this, but the formal, dated real-browser time-to-interactive
  numbers for this iteration are not yet recorded (see "Not Visible Yet" below).
- **`npm run dev` / `scripts/dev.sh`'s own dev workflow is unchanged** — still plain `next dev`, still
  shows the dev overlay on errors as before. Only the separate `start-frontend.sh` launcher (used for
  automated evidence capture / measurement, and for any other "production mode" boot of the app) changed.

---

## What Old Behavior Changed

- **`scripts/start-frontend.sh`'s launch behavior**: previously it unconditionally executed `npx next
  dev` while labeling itself "prod mode" — every page it served was actually running in development
  mode regardless of what the script's own comments claimed. Now it checks whether the existing `.next`
  build is missing or stale (older than any tracked source file, `package.json`, or the lockfile), runs
  `next build` only when needed, and always execs `next start`. It never falls back to `next dev`.
- **A genuinely broken frontend source file now surfaces as a visible, actionable failure at launch
  time**: the script prints the `next build` error output and exits non-zero, and leaves no stray
  process running — previously (since it never ran a real build) there was no such failure path at all;
  a source error would have been silently tolerated by the dev-mode compiler and only surfaced later, per
  route, if a user happened to hit the broken code path.

---

## Not Visible Yet

- **The formal, dated real-browser TTI + on-load-API-latency sweep for all 11 pages** (this iteration's
  TC-4/TC-5) is not yet appended to `reports/perf-budgets.md` — confirmed by inspection, the file's last
  entry is still the iter-32 (`J-07` memory) section, no `## Iteration 33` section exists yet. The dev
  handoff is explicit that this measurement is intentionally left to the browser-qa-agent's pass, since a
  `curl` timing is not a substitute for a real-browser TTI reading.
- **The `merge_ui_test_results.py` fix** (widening `_ROW_RE` so a `TC-`-prefixed failing test row
  survives report merging) has no user-facing surface at all — it only changes how the automation
  pipeline's own internal QA report file gets merged, not anything in the product application.
