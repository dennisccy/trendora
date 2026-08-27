# Phase goal-market-compass-iter-20 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-20
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Before you start

This iteration is **backend-only** (`Frontend Present: no`) and ran under **maintenance
isolation**: the backend, the frontend, and a browser were all forbidden from running for the whole
iteration, and remain off now. There is nothing at `http://localhost:3255` to click. Do not start
the backend or frontend to run this guide — a single live request against certain historical dates
right now could mint bad data (see the last bullet under "If Something Looks Wrong").

Instead, this guide verifies iteration 20's actual work — a live database repair — using the
evidence files it already produced. Every step below is a file you open and a value you check; none
requires the app to be running. Steps 6-7 tell you what to do once the app IS bootable again.

---

## Prerequisites

- A terminal with read access to the repo at `/home/dennis-chan/Git/trendora`.
- No running backend, frontend, or browser needed for steps 1-5.

---

## Steps

1. Open `docs/handoffs/goal-market-compass-iter-20-dev.md` and find the status block near the top.
   - **Expect:** exactly these seven lines — `J-11 STAGE D EXECUTED: YES`,
     `J-11 STAGE E COMPLETE: YES`, `J-11 STAGE F COMPLETE: NO`, `J-11 STAGE G VERIFIED: NO`,
     `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE`,
     `J-11 MAINTENANCE BOUNDARY: ACTIVE`, `J-11 LIVE PRE-BOOT GUARD: ARMED`. `STAGE E COMPLETE: YES`
     is real progress, but do not read it as "the incident is fixed" — the very next line says it
     isn't yet.

2. Open `runs/goal-market-compass-iter-20/j11-stage-e-execute-mutation-accounting.json` and find the
   `forward_returns_count` object.
   - **Expect:** `"pre": 6797728`, `"post": 6814320`, `"observed_delta": 16592`,
     `"self_reported_total_inserted": 16592` — the last two numbers match each other exactly.

3. In the same file, find `table_sweep_diff.changed_existing_tables`.
   - **Expect:** the list contains exactly one entry, `"forward_returns"`. If any other table name
     appears here (e.g. `scanner_runs`, `daily_prices`, `maintenance_boundaries`), that is a serious
     problem — this iteration was authorized to write to `forward_returns` only.

4. In the same file, find `all_scanner_run_counts`, `manifest_diff`, and
   `maintenance_boundary_diff`.
   - **Expect:** `all_scanner_run_counts.pre` equals `all_scanner_run_counts.post` (both 3128);
     `manifest_diff.equal` is `true` with `pre_row_count`/`post_row_count` both 24;
     `maintenance_boundary_diff.equal` is `true` with `pre_row_count`/`post_row_count` both 1.

5. Open `runs/goal-market-compass-iter-20/j11-stage-e-execute-population-report.json` and find
   `population_a_total_newly_inserted` and `population_c_not_yet_mature.latest_run_check`.
   - **Expect:** `population_a_total_newly_inserted` is `16592`, matching step 2's
     `observed_delta`; `population_c_not_yet_mature.latest_run_check.ok` is `true` with
     `forward_return_row_count: 0` (the newest run correctly has zero forward returns — no trading
     day exists after it yet, so nothing should have been fabricated for it).

6. **Deferred — do this on the next iteration where the app is allowed to run, NOT now.** Once
   maintenance isolation lifts: start the backend and frontend via the project's prod launch
   scripts, navigate to `http://localhost:3255/stocks`, filter by Sector = "Unassigned".
   - **Expect:** Unassigned share of resolved members is at most 5%. This journey (J-01) was not
     touched by iteration 20 — `git status --porcelain -uall` grepped against `scoring.py`,
     `sectors.py`, `app/api/*`, and `compass.py` shows zero matches (recorded in the dev handoff's
     "Files Changed" section) — so this should read exactly as it did before iteration 20.

7. **Also deferred.** Once the app is bootable: navigate to `http://localhost:3255/`, open one
   candidate card.
   - **Expect:** its Leadership/Entry/Risk words, score, and bucket match the `GET /api/stocks` row
     for the same ticker at the same as-of, and every reason/caution cites a threshold plus the
     stored actual value. This journey (J-04) was also untouched by iteration 20 for the same
     file-proof reason as step 6.

---

## What "Working Correctly" Looks Like

- The seven status lines in step 1 read as an honest partial success: Stage E complete, Stages F/G
  still pending, incident still marked not-repaired. That combination is the CORRECT outcome for
  this iteration — do not treat a `NOT REPAIRED` line as a failure of iteration 20's own scope.
- Every number in steps 2-5 cross-checks against another number in the same or a sibling file with
  no discrepancy — that reconciliation, not any single figure alone, is what proves the repair was
  done correctly and nothing else was touched.

## If Something Looks Wrong

- **Numbers don't reconcile (e.g., step 2's delta ≠ step 5's population-A total):** stop and report
  it — do not assume rounding or a stale file; re-open both files fresh, they were generated
  seconds apart by the same run (`generated_at` timestamps in each JSON confirm this).
- **`table_sweep_diff.changed_existing_tables` (step 3) contains anything besides
  `"forward_returns"`:** this means a write escaped its authorized scope. Do not start the app. Do
  not attempt any fix. Report it immediately — this is exactly the class of error the maintenance
  boundary exists to catch.
- **Tempted to start the backend/frontend to "just double-check" something visually:** don't. Per
  the coordinator's operational note for this iteration, `compass.get_or_create_manifest` mints a
  manifest on any ordinary `GET /api/compass?as_of=<date>` request, and `scanner.resolve_run` is
  unguarded from any `?as_of=` read path — a single request against one of the 11 quarantined
  incident dates could permanently write bad data. Steps 1-5 above need no running app; steps 6-7
  are explicitly deferred, not "try it now anyway."
