# Phase goal-market-compass-iter-18 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-18
**Time required:** ~3 minutes for steps 1-3 (evidence files, runnable right now, no app needed); ~5
minutes more for steps 4-8 once maintenance isolation lifts and the app can be booted
**Written by:** ui-test-designer

---

## Before you start

Maintenance isolation is still active this iteration — the backend, frontend, browser QA, and the
deterministic replay lane were all forbidden from running, so nothing below has actually been clicked
through yet. **But do not read "not clicked through" as "nothing happened."** Unlike iteration 17 (which
made zero live database writes), this iteration made exactly **two authorized, permanent writes** to the
real production database, `apps/backend/data/trendora.db`: it created a new `maintenance_boundaries`
table and switched on (armed) one `j11-incident-recovery` row inside it. The eleven trading days damaged
by the 2026-08 data-recovery incident are now genuinely quarantined at the database level — starting
Trendora can no longer silently recompute and overwrite results for any of them, from either of the two
ways a backend boot could previously reach that data (one of which — a second call site inside the
background warm-up's forward-return backfill step — was only discovered and closed during this
iteration). Stage D itself (the actual repair of those eleven days) remains exactly as unauthorized as
before; this iteration only switched on the safety mechanism Stage D will eventually depend on, then
stopped, per the owner's mandatory-stop instruction.

Steps 1-3 below verify that switch is genuinely on, using only files already committed to this
checkout — no running app required, doable right now. Steps 4-8 re-check the three journeys this
iteration is required to keep passing (J-01, J-04, J-10) plus one J-11-specific browser spot check; they
need the app running, which presumes maintenance isolation has, by the time you run them, been
legitimately lifted by the owner.

**One safety rule that applies to every browser step below (4-8):** the app has 11 "incident dates" with
no fresh derived data behind them: `2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24,
2026-07-27, 2026-08-03, 2026-08-05, 2026-08-10, 2026-08-11, 2026-08-12`. **Never type one of these into
the `?asof=` part of the URL.** This iteration's new safety switch does not make that safe to do — it
only stops the app's own background startup routine from silently overwriting those dates on its own; it
does not gate what happens if a person manually asks the app for one of them by URL. Doing so would still
mint a permanent data artifact the system isn't supposed to create yet.

**Do not repeat J-01's original delivery mechanism** (the seed-safe `/data` Remove-panel + backfill) to
"test" sector attribution — that was a one-time setup step from an earlier iteration, not a repeatable
regression check, and repeating it is a destructive action against committed data.

## Prerequisites

- For steps 1-3: just this git checkout, on branch `goal/market-compass`. No app needs to be running.
- For steps 4-8: frontend running at `http://localhost:3255`, backend running (prod scripts). No login
  required. At least one completed scan session exists (true today — 3,117 stored sessions, confirmed
  unchanged this iteration).

---

## Steps

1. Open `docs/handoffs/goal-market-compass-iter-18-dev.md` and find the "Final status" section
   - **Expect:** exactly these four lines appear:
     ```
     J-11 MAINTENANCE BOUNDARY: ACTIVE
     J-11 LIVE PRE-BOOT GUARD: ARMED
     J-11 STAGE D READY: YES
     J-11 STAGE D AUTHORIZED: NO
     ```

2. Open `runs/goal-market-compass-iter-18/j11-iter18-live-preboot-guard-verification.json`
   - **Expect:** `"armed": true`, `"all_eleven_incident_dates_blocked": true`,
     `"control_date_not_blocked": true` (control date `"2026-07-23"`), `"background_warmup_site_blocked":
     true`, and `"zero_scanner_runs_created_by_this_verification": true`.

3. Open `runs/goal-market-compass-iter-18/j11-iter18-full-table-sweep-diff.json`
   - **Expect:** `"clean": true`, `"expected_new_tables_present": ["maintenance_boundaries"]`,
     `"changed_existing_tables": []`, and `"unexpected_new_tables": []` — together proving the ONLY
     change anywhere in the (now 25-table) database is the one new table this iteration was authorized
     to add.

4. Open `http://localhost:3255/` in your browser (do not add any `?asof=` to the URL)
   - **Expect:** the page loads normally. The date shown as the current session is **not** one of the 11
     incident dates listed above (it was `2026-07-23` when this guide was written — a later date is
     fine).

5. Click into one card under "Next-session focus"
   - **Expect:** the opened card shows named reasons and cautions, each with both a threshold and an
     actual value (e.g. "ADV $2.1M vs. $1M minimum") — not a bare claim with no number.

6. Navigate to `http://localhost:3255/stocks` and select the Sector filter's `"Unassigned"` option
   - **Expect:** Unassigned rows are **≤ 5%** of the total resolved-member count.

7. Clear the filter, search for symbol `AVB`, and open its stock detail page
   - **Expect:** the page loads without error. If the price/volume chart's date range reaches back to
     `2026-08-11`/`2026-08-12`, those two days' volume bars look consistent with the surrounding week —
     no visible spike (iteration 16's correction; this iteration's own mutation-accounting sweep proves
     `daily_prices` was not touched again). If the chart doesn't reach that far, that's fine — this check
     simply doesn't apply today.

8. Navigate to `http://localhost:3255/data` and look at the manifest count
   - **Expect:** still shows 24 manifests total, unchanged. (Do not confuse this with the database's
     table count, which this iteration correctly moved from 24 to 25 — two different numbers that
     happened to coincide before this iteration and no longer do.)

---

## What "Working Correctly" Looks Like

- **Steps 1-3 (right now, no app needed):** the dev handoff's four status lines read exactly
  `ACTIVE`/`ARMED`/`YES`/`NO`, the live verification file shows all eleven incident dates blocked and a
  normal control date still not blocked, and the table-sweep diff file shows the ONLY database change
  anywhere is the one new `maintenance_boundaries` table.
- **Steps 4-8 (once the app can run):** `/`, `/stocks`, `/data`, and AVB's stock detail page all look and
  behave exactly as they did in iteration 17 — this iteration's work is a database-level safety switch
  with no UI surface of its own, so nothing should look visibly different, and that is the correct
  outcome, not a sign the work didn't happen.

## If Something Looks Wrong

- **Step 1 reads `MAINTENANCE BOUNDARY: NOT ACTIVE` or `LIVE PRE-BOOT GUARD: NOT ARMED`**: a real,
  reportable finding — this iteration's live arm was supposed to succeed and its own evidence says it
  did; seeing the "not armed" state now would mean something reverted it since. Escalate.
- **Step 1 reads `STAGE D AUTHORIZED: YES` (or anything other than `NO`)**: the single most severe
  possible finding on this journey — Stage D was never authorized this iteration, under any framing, even
  given full arming success. Stop and escalate immediately; do not interpret it as progress.
- **Step 3 shows a non-empty `changed_existing_tables` list, or any `unexpected_new_tables`**: a real
  finding — some table outside the one authorized `maintenance_boundaries` addition was touched.
  Escalate with the exact table name(s) listed.
- **One of the 11 incident dates shows up anywhere in the app as a normal, undisclosed session** (steps
  4-8): a real, reportable finding — it would mean derived data was regenerated for a quarantined date
  before J-11 Stage D was ever authorized. Stop and escalate; do not try to fix it yourself.
- **AVB's `2026-08-11`/`2026-08-12` volume looks spiked (~2.8x neighbors) or different from iteration
  16's corrected figures (`554,757`/`3,706,010`)**: a real finding — report it, don't fix the data
  yourself.
- **Unassigned sector share is high (back near ~78%) on `/stocks`**: a genuine regression of J-01 — file
  it with the specific ticker(s) you spot-checked.
- **Blank page / error screen** on steps 4-8: confirm the backend is actually running before assuming a
  regression.
- For longer, exact steps and the full escalation criteria, see the full test plan
  (`reports/phase-goal-market-compass-iter-18-ui-test-plan.md`, cases `UT-J-01`, `UT-J-04`, `UT-J-10`,
  `UT-J-11`) — this quick guide was distilled from it.
