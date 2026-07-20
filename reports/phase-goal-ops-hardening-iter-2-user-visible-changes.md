# Phase goal-ops-hardening-iter-2 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-2
**Date:** 2026-07-19
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- See, on the `/data` page, exactly which downstream aggregates a completed backfill/`both`/rebuild run refreshed — a new line reading "Refreshed: coverage, market phase, membership timeline, research hot keys" (or whichever subset actually ran) appears directly under the existing calendar-days/already-snapshotted/non-trading breakdown line, on the live Job progress panel, the reduced Last-run summary card (shown when no job has started this browser session), and that run's row in the Run history table.
- Load `/data` as the very first request after a backend restart and see the "Dataset coverage" panel (Price history, Universe, Candidate universe, Symbols, Trading days, Snapshot dates, Backfill gaps stat tiles) populate in well under a second, instead of the multi-second (previously ~9.4-10.5s), memory-heavy live scan that used to run on that same request.
- Step the app-wide as-of switcher back to an older, already-ingested date on `/data` and still see that date's genuine, non-zero coverage numbers — not a false "nothing here yet" panel. (This specific behavior was very nearly a regression introduced by this same iteration's first pass — the code-review step caught it before this handoff, and it is now fixed; still worth a deliberate operator check since no automated browser test exercised it before the fix.)
- (Edge case, brand-new/never-ingested database only) Load `/data` before any backfill/fetch has ever completed and see an honest all-zero coverage panel — never a hung request, blank page, or 500 error — then, once the background warm-up finishes a few seconds later, reload and see it filled in with real numbers, with no manual job run required.

---

## What Changed in the Visible UI

- `/data`'s Job progress panel (live job card), Last-run summary card (persisted-run fallback shown when no job started this session), and Run history table: each of the three now renders a second, independent inline line — `Refreshed: <comma-joined, space-separated list>` — immediately below the existing "N calendar days · N already snapshotted · N non-trading" breakdown line, in the identical muted `text-xs text-text-faint` treatment (no new color, badge, or emphasis). It appears only for a `backfill`/`both`/`rebuild` run whose finalize hook actually populated the list; it is omitted entirely (not shown as an empty or dashed line) for `fetch`/`expand` runs and for a not-yet-computed or interrupted row.
- Nothing else on `/data` changed structurally: same cards, same table, same form, same stat-tile layout for "Dataset coverage." No new page, panel, nav entry, button, or form was added anywhere in the product.

---

## What Old Behavior Changed

- **`/data`'s "Dataset coverage" panel:** previously recomputed live (a full scan of the stored price-history table) on every page load and every as-of-switcher step. Now it reads a persisted snapshot that is refreshed automatically at the end of each backfill/both/rebuild job (and, for an older date ingested before this feature existed, computed once on first view and stored from then on). The numbers shown are the same — only *when* they get computed changed, and the one visible symptom of the old behavior (a slow, occasionally risky page load) is gone.
- **A brand-new, never-ingested database's `/data` visit:** previously would have triggered that same live, multi-second scan even on an empty dataset. Now it serves an instant, honest zero/empty state instead, until the background warm-up (or the first backfill) fills it in.
- **Not pixel-visible, but a real operator-facing behavior change:** `scripts/start-backend.sh` now actually applies the memory ceiling and writes a permanent boot/crash log (`logs/backend.log`) that `config.yaml` already claimed it enforced — previously neither was true (confirmed false by a direct read of the script before this iteration, which was only 34 lines with no such logic at all). This has no on-screen UI, but it changes what an operator can rely on and inspect outside the browser.

---

## Not Visible Yet

- `/`, `/scanner-runs`, and `/research/*` continue to render byte-identical numbers from the same pre-existing market-phase/membership-timeline/research-hot-key caches as before this iteration — none of those pages' routes or components changed. What changed is invisible: those caches are now warmed proactively when a backfill finishes, instead of being computed on whichever request happens to ask for them first. There is no observable pixel difference on these pages to point to.
- The `computed_at` timestamp stored on every coverage snapshot is not rendered anywhere — no "coverage last refreshed at HH:MM" freshness indicator exists in the UI (explicitly out of scope this iteration).
- The enforced memory cap and the persistent logfile have no UI representation anywhere in the web app — they are verifiable only by inspecting the running process (`/proc/<pid>/limits`, `/proc/<pid>/environ`) or reading `logs/backend.log` directly, never by clicking through the product.
- Whether the backend stays responsive and within its memory cap during a genuinely HEAVY backfill/rebuild (as opposed to the light single-day backfill this iteration verified live) was reasoned about from the code but not measured against a live heavy job this pass — deferred to QA/browser verification (see dev handoff "Known Issues" / TC-11 / TC-12).
