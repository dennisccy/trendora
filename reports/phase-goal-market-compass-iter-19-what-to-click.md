# Phase goal-market-compass-iter-19 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-19
**Time required:** ~4 minutes for steps 1-5 (evidence files, runnable right now, no app needed); ~5
minutes more for steps 6-10 once maintenance isolation lifts and the app can be booted
**Written by:** ui-test-designer

---

## Before you start

Maintenance isolation is still active this iteration — the backend, frontend, browser QA, and the
deterministic replay lane were all forbidden from running, so nothing below has actually been clicked
through yet. **But do not read "not clicked through" as "nothing happened."** This iteration performed
the **largest live write of the whole J-11 recovery so far**: it regenerated all 11 quarantined incident
dates' scanner data (market scores, sector scores, theme scores, and stock-level results) — data that had
sat empty since an earlier maintenance cleanup — by running the normal, unmodified scanning engine once
for each date, all under one freshly frozen "batch marker" (execution identity) that lets this specific
repair always be told apart from any earlier or later one.

The attempt **succeeded**: all 11 dates are now populated, and every safety check before, during, and
after the write passed. But the overall J-11 incident is **still not closed** — three more steps
(refilling forward-looking research data, refreshing internal caches, and a final full verification) have
not run yet. The safety lock that has kept these 11 dates quarantined from normal use stays exactly where
it was. Nothing about this iteration makes it safe to view those 11 dates in the app yet.

Steps 1-5 below verify the write succeeded and stayed inside its authorized bounds, using only files
already committed to this checkout — no running app required, doable right now. Steps 6-10 re-check the
three journeys this iteration is required to keep passing (J-01, J-04, J-10) plus one J-11 safety spot
check; they need the app running, which presumes maintenance isolation has, by the time you run them,
been legitimately lifted by the owner.

**One safety rule that applies to every browser step below (6-10):** the app has 11 "incident dates" that
now have fresh derived data behind them for the first time, but are still not cleared for normal viewing:
`2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03, 2026-08-05,
2026-08-10, 2026-08-11, 2026-08-12`. **Never type one of these into the `?asof=` part of the URL.** The
data existing now does not make it safe to serve — that determination is reserved for a later stage
(Stage G) that has not run.

**Do not repeat J-01's original delivery mechanism** (the seed-safe `/data` Remove-panel + backfill) to
"test" sector attribution — that was a one-time setup step from an earlier iteration, not a repeatable
regression check, and repeating it is a destructive action against committed data.

## Prerequisites

- For steps 1-5: just this git checkout, on branch `goal/market-compass`. No app needs to be running.
- For steps 6-10: frontend running at `http://localhost:3255`, backend running (prod scripts). No login
  required. At least one completed scan session exists (true today — 3,128 stored sessions, up from 3,117
  before this iteration).

---

## Steps

1. Open `docs/handoffs/goal-market-compass-iter-19-dev.md` and find the "Terminal status" section
   - **Expect:** exactly these 8 lines appear:
     ```
     J-11 STAGE D AUTHORIZED: YES
     J-11 STAGE D EXECUTED: YES
     J-11 STAGE E COMPLETE: NO
     J-11 STAGE F COMPLETE: NO
     J-11 STAGE G VERIFIED: NO
     J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE
     J-11 MAINTENANCE BOUNDARY: ACTIVE
     J-11 LIVE PRE-BOOT GUARD: ARMED
     ```

2. Open `runs/goal-market-compass-iter-19/j11-stage-d-execute-gate-verdict.json`
   - **Expect:** `"proceed": true`, `"avb_classification": "AVB-A"`, `"blocking_reasons": []` — the
     fresh safety gate agreed to proceed before any write happened.

3. Open `runs/goal-market-compass-iter-19/j11-stage-d-execute-historical-identity-comparison.json`
   - **Expect:** `"fresh_engine_identity"` starts with `"53d2ffd1..."`, and
     `"comparisons"."iteration_10"."matches_fresh"` is `false` (this run's identity is genuinely new
     compared to the oldest historical one on record).

4. Open `runs/goal-market-compass-iter-19/j11-stage-d-execute-mutation-accounting.json`
   - **Expect:** every field under `"checks"` reads `true` (9 fields total), and
     `"table_sweep_diff"."changed_existing_tables"` is **exactly**
     `["scanner_results", "scanner_runs", "sector_scores", "theme_scores"]` — no other table appears
     anywhere in the diff. (The same file's `"table_sweep_diff"."clean"` field reads `false` — that's
     correct, not a bug: `clean` means zero tables changed at all, and this iteration is authorized to
     change exactly those 4.)

5. Open `runs/goal-market-compass-iter-19/j11-stage-d-execute-db-file-true-start.json` and
   `-db-file-true-end.json` side by side
   - **Expect:** `"size_bytes"` is identical in both (`8365871104`) — the main database file didn't grow;
     only `"wal"."size_bytes"` grew (from `0` to `5475512`), which is the expected, harmless way SQLite
     records new committed writes before they're folded into the main file.

6. Open `http://localhost:3255/` in your browser (do not add any `?asof=` to the URL)
   - **Expect:** the page loads normally. The date shown as the current session is **not** one of the 11
     incident dates listed above (it was `2026-07-23` when this guide was written — a later date is
     fine).

7. Click into one card under "Next-session focus"
   - **Expect:** the opened card shows named reasons and cautions, each with both a threshold and an
     actual value (e.g. "ADV $2.1M vs. $1M minimum") — not a bare claim with no number.

8. Navigate to `http://localhost:3255/stocks` and select the Sector filter's `"Unassigned"` option
   - **Expect:** Unassigned rows are **≤ 5%** of the total resolved-member count.

9. Clear the filter, search for symbol `AVB`, and open its stock detail page
   - **Expect:** the page loads without error and shows a continuous price history with no unexplained
     gap.

10. Navigate to `http://localhost:3255/data` and look at the manifest count
    - **Expect:** still shows 24 manifests total, unchanged. (This iteration added 11 new scanner
      sessions, but zero new manifests — those are two different, unrelated counts.)

---

## What "Working Correctly" Looks Like

- **Steps 1-5 (right now, no app needed):** the dev handoff's 8 status lines read exactly
  `AUTHORIZED: YES` / `EXECUTED: YES` / `E/F/G: NO` / `NOT REPAIRED — ATTEMPT INCOMPLETE` /
  `BOUNDARY: ACTIVE` / `GUARD: ARMED`; the gate-verdict file shows the safety gate said yes before any
  write; the identity-comparison file shows a genuinely fresh batch marker; the mutation-accounting file
  shows the ONLY tables touched anywhere are the 4 this iteration was authorized to touch; the db-file
  brackets show the main file didn't grow (only the pending-write WAL sidecar did).
- **Steps 6-10 (once the app can run):** `/`, `/stocks`, `/data`, and AVB's stock detail page all look and
  behave exactly as they did in iteration 18 — this iteration's work regenerated historical data that
  isn't served anywhere in the UI yet, so nothing should look visibly different, and that is the correct
  outcome, not a sign the work didn't happen.

## If Something Looks Wrong

- **Step 1 reads `STAGE E COMPLETE`, `STAGE F COMPLETE`, or `STAGE G VERIFIED` as anything other than
  `NO`**: a real, reportable finding — this iteration's scope was Stage D alone; seeing any later stage
  marked complete would mean scope crept beyond what was authorized. Escalate.
- **Step 1 reads `INCIDENT STATUS` as anything other than `NOT REPAIRED — ATTEMPT INCOMPLETE`**: the
  single most severe possible finding on this journey — Stage D succeeding does NOT mean the incident is
  closed. Stop and escalate immediately; do not interpret it as full repair.
- **Step 1 reads `MAINTENANCE BOUNDARY` as anything other than `ACTIVE`**: a real finding — the boundary
  must stay on regardless of Stage D's outcome. Escalate.
- **Step 4 shows a `changed_existing_tables` list containing anything besides `scanner_results`,
  `scanner_runs`, `sector_scores`, or `theme_scores`, or any `checks` field is `false`**: a real
  finding — some table outside the authorized four was touched. Escalate with the exact table name(s).
- **One of the 11 incident dates shows up anywhere in the app as a normal, undisclosed session** (steps
  6-10): a real, reportable finding — it would mean Stage-G-level serving happened before Stage G ever
  ran. Stop and escalate; do not try to fix it yourself.
- **Unassigned sector share is high (back near ~78%) on `/stocks`**: a genuine regression of J-01 — file
  it with the specific ticker(s) you spot-checked.
- **Blank page / error screen** on steps 6-10: confirm the backend is actually running before assuming a
  regression.
- For longer, exact steps and the full escalation criteria, see the full test plan
  (`reports/phase-goal-market-compass-iter-19-ui-test-plan.md`, cases `UT-J-01`, `UT-J-04`, `UT-J-10`,
  `UT-J-11`) — this quick guide was distilled from it.
