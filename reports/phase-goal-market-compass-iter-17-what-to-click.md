# Phase goal-market-compass-iter-17 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-17
**Time required:** ~5 minutes for steps 1-6 (once the app is running); ~2 minutes for steps 7-8, runnable
right now
**Written by:** ui-test-designer

---

## Before you start

This iteration shipped **zero UI changes and zero live database writes of any kind** (proven by its own
mtime/size/`-wal`-size fingerprint, byte-identical at true start and true end). What it actually did, all
on disposable test databases or via strictly read-only inspection of the live one: fixed the pre-boot
guard's unbounded whole-table query (`evaluate_boundary_for_date`) so it is both bounded and still fails
closed on a `NULL`-active row or a missing table; added committed, production-capable arm and disarm
entrypoints for the maintenance-boundary lifecycle (proven only against fixtures — **never** run against
the live app); delivered the owner's 9 named tests; and re-derived the AVB Stage D readiness
classification more accurately (`AVB-B` → `AVB-A`, using the correct hypothetical volume basis) —
`J-11 STAGE D READY: YES` is unchanged. **`J-11 STAGE D AUTHORIZED: NO` remains unconditional**, and
creating the live `maintenance_boundaries` table stays explicitly not authorized — the live-arm step this
would otherwise require is expected to read `STALLED`, and that is correct, not a bug.

This guide re-checks that the 3 journeys this iteration is required to keep passing (J-01, J-04, J-10)
still work, and verifies iteration 17's own new claims (J-11) — mostly by reading the evidence files it
produced, since none of this iteration's work has any UI surface of its own. Steps 1-6 need the app
running; steps 7-8 need only this repository checkout and can be done right now, even while maintenance
isolation is still active.

**One safety rule that applies to every browser step below:** the app currently has 11 "incident dates"
with no fresh derived data behind them yet: `2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24,
2026-07-27, 2026-08-03, 2026-08-05, 2026-08-10, 2026-08-11, 2026-08-12`. **Never type one of these into
the `?asof=` part of the URL.** For most of them, doing so creates a permanent data artifact the system
isn't supposed to create yet. This is expected, authorized, mid-repair state — not something to report as
broken.

**Do not repeat J-01's original delivery mechanism** (the seed-safe `/data` Remove-panel + backfill) to
"test" sector attribution — that was a one-time setup step from an earlier iteration, not a repeatable
regression check, and repeating it is a destructive action against committed data.

## Prerequisites

- Frontend running at `http://localhost:3255`, backend running (prod scripts) — for steps 1-6 only. This
  presumes maintenance isolation has, by the time you run these, been legitimately lifted by the owner;
  as of this writing it is still active.
- No login required.
- At least one completed scan session exists (true today — 3,117 stored sessions).
- For steps 7-8: just this git checkout, on branch `goal/market-compass`. No app needs to be running.

---

## Steps

1. Open `http://localhost:3255/` in your browser (do not add any `?asof=` to the URL)
   - **Expect:** the page loads normally. The date shown as the current session is **not** one of the 11
     incident dates listed above (it was `2026-07-23` when this guide was written — a later date is
     fine).

2. Click into one card under "Next-session focus"
   - **Expect:** the opened card shows named reasons and cautions, each with both a threshold and an
     actual value (e.g. "ADV $2.1M vs. $1M minimum") — not a bare claim with no number.

3. Navigate to `http://localhost:3255/stocks` and select the Sector filter's `"Unassigned"` option
   - **Expect:** Unassigned rows are **≤ 5%** of the total resolved-member count.

4. Clear the filter, search for symbol `AVB`, and open its stock detail page
   - **Expect:** the page loads without error. If the price/volume chart's date range reaches back to
     `2026-08-11`/`2026-08-12`, those two days' volume bars look consistent with the surrounding week —
     no visible spike about 2.8x the neighboring days' height (that correction landed in iteration 16;
     this iteration did not touch the data again). If the chart doesn't reach that far, that's fine —
     this check simply doesn't apply today.

5. Navigate to `http://localhost:3255/data` and look at the manifest count
   - **Expect:** still shows 24 manifests total, unchanged.

6. Navigate to `http://localhost:3255/methodology`
   - **Expect:** the universe/data section discloses the two-source sector basis (curated config mapping
     first, pool-snapshot fallback second) and its current-only limitation.

7. Open `docs/handoffs/goal-market-compass-iter-17-dev.md` in the repo
   - **Expect:** these four lines appear exactly:
     ```
     J-11 STAGE D READY: YES
     J-11 STAGE D AUTHORIZED: NO
     J-11 MAINTENANCE BOUNDARY: NOT ACTIVE
     J-11 LIVE PRE-BOOT GUARD: NOT ARMED
     ```
     and the live-arm sub-step of the owner's requirements 4 and 7 is explicitly named as blocked by the
     table's absence — not silently skipped, not silently attempted.

8. Open `runs/goal-market-compass-iter-17/j11-iter17-live-preboot-guard-verification.json` and the
   `j11-iter17-readiness-db-file-true-start.json` / `-true-end.json` pair
   - **Expect:** the live table-count result is `0` (the `maintenance_boundaries` table still does not
     exist) and the `evaluate_boundary_for_date` result for `2026-08-12` reads `blocked: false`; the
     true-start and true-end files show identical `mtime`, `size`, and `-wal`-size values.

---

## What "Working Correctly" Looks Like

- `/`, `/stocks`, and `/data` all look and behave exactly as they did before this iteration — nothing
  about this iteration's work is visible in the UI, and that is the correct outcome.
- AVB's price/volume history (wherever visible) still shows no anomalous spike around
  `2026-08-11`/`2026-08-12`, unchanged from iteration 16.
- The four `J-11 ...` status lines in the dev handoff read exactly as listed in step 7, and the two
  evidence JSON files in step 8 confirm the live database was never armed and never written to.

## If Something Looks Wrong

- **Blank page / error screen**: confirm the backend is actually running before assuming a regression.
- **One of the 11 incident dates shows up as a normal, undisclosed session anywhere** (a candidate list,
  an as-of picker entry with no "unavailable" label, etc.): a real, reportable finding — it would mean
  derived data was regenerated for an incident date before J-11 authorized it. Stop and escalate; do not
  try to "fix" it yourself.
- **`MAINTENANCE BOUNDARY: ACTIVE` or `LIVE PRE-BOOT GUARD: ARMED` appears anywhere**: a real, reportable
  finding — the live `maintenance_boundaries` table is explicitly not authorized to exist yet. Stop and
  escalate.
- **AVB's 08-11/08-12 volume looks spiked (~2.8x neighbors) or looks different from iteration 16's
  corrected figures (`554,757`/`3,706,010`)**: a real finding — report it, don't try to fix the data
  yourself.
- **Unassigned sector share is high (back near ~78%) on `/stocks`**: a genuine regression of J-01 — file
  it with the specific ticker(s) you spot-checked.
- **The true-start/true-end DB fingerprints differ in `mtime`, `size`, or `-wal` size**: a real,
  reportable finding — it would mean something wrote to the live database during this supposedly
  read-only iteration. Escalate immediately.
- For anything else, the full test plan
  (`reports/phase-goal-market-compass-iter-17-ui-test-plan.md`, cases `UT-J-01`, `UT-J-04`, `UT-J-10`,
  `UT-J-11`) has the exact, longer steps this quick guide was distilled from.
