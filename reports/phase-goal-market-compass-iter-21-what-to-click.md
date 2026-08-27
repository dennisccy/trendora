# Phase goal-market-compass-iter-21 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-21
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Before you start

This iteration is **backend-only** (`Frontend Present: no`) and ran under **maintenance
isolation**: the backend, the frontend, and a browser were all forbidden from running for the whole
iteration, and remain off now. There is nothing at `http://localhost:3255` to click. Do not start
the backend or frontend to run this guide — a single live request against certain historical dates
right now could mint bad data (`scanner.resolve_run` is unguarded from any `?as_of=` read path, and
`compass.get_or_create_manifest` mints a manifest on any ordinary `GET /api/compass?as_of=<date>`
request).

Instead, this guide verifies iteration 21's actual work — J-11 Stage F, a live derived-cache
deletion across five of seven cache tables — using the evidence files it already produced, plus one
read-only database query. Steps 1-5 are files/a query you check; none requires the app to be
running. Steps 6-8 tell you what to do once the app IS bootable again (not this iteration).

---

## Prerequisites

- A terminal with read access to the repo at `/home/dennis-chan/Git/trendora`.
- No running backend, frontend, or browser needed for steps 1-5.
- `sqlite3` available on the PATH for step 4 (read-only mode only).

---

## Steps

1. Open `docs/handoffs/goal-market-compass-iter-21-dev.md` and find the status block near the top.
   - **Expect:** exactly these seven lines — `J-11 STAGE D EXECUTED: YES`,
     `J-11 STAGE E COMPLETE: YES`, `J-11 STAGE F COMPLETE: YES`, `J-11 STAGE G VERIFIED: NO`,
     `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE`,
     `J-11 MAINTENANCE BOUNDARY: ACTIVE`, `J-11 LIVE PRE-BOOT GUARD: ARMED`. `STAGE F COMPLETE: YES`
     is real progress, but do not read it as "the incident is fixed" — the very next line says it
     isn't yet. Only Stage G may ever declare it fixed.

2. Open `runs/goal-market-compass-iter-21/j11-stage-f-execute-execution-result.json` and find
   `total_rows_deleted` and the `per_table` object.
   - **Expect:** `"total_rows_deleted": 1643`. Five tables (`event_study_cache`,
     `market_phase_cache`, `forward_aggregate_cache`, `coverage_snapshot`, `availability_cache`)
     show `"attempted_write": true` with `rows_deleted` equal to `pre_count` (18 + 1290 + 333 + 1 +
     1 = 1643). Two tables (`index_series_cache`, `membership_timeline_cache`) show
     `"attempted_write": false` — they were deliberately preserved, not deleted.

3. Open `runs/goal-market-compass-iter-21/j11-stage-f-execute-verification-result.json` and find
   `ok` and each table's `post_count`.
   - **Expect:** `"ok": true`; `post_count` is `0` for the five deleted tables and `1` for each of
     the two preserved tables.

4. Run this read-only query (never opens the database for write):
   `sqlite3 "file:apps/backend/data/trendora.db?mode=ro" "SELECT (SELECT COUNT(*) FROM event_study_cache), (SELECT COUNT(*) FROM market_phase_cache), (SELECT COUNT(*) FROM forward_aggregate_cache), (SELECT COUNT(*) FROM coverage_snapshot), (SELECT COUNT(*) FROM availability_cache), (SELECT COUNT(*) FROM index_series_cache), (SELECT COUNT(*) FROM membership_timeline_cache), (SELECT COUNT(*) FROM scanner_runs), (SELECT COUNT(*) FROM forward_returns);"`
   - **Expect:** `0|0|0|0|0|1|1|3128|6814320` — the live database matches the evidence files exactly
     (steps 2-3), and the two untouched invariants (`scanner_runs`, `forward_returns`) are unchanged.

5. Open `runs/goal-market-compass-iter-21/j11-stage-f-execute-mutation-accounting.json` and find
   `table_sweep_diff.changed_existing_tables`.
   - **Expect:** the list contains exactly five entries — `availability_cache`, `coverage_snapshot`,
     `event_study_cache`, `forward_aggregate_cache`, `market_phase_cache` — and nothing else. If any
     other table name appears here (e.g. `scanner_runs`, `daily_prices`, `maintenance_boundaries`,
     `next_session_manifests`), that is a serious problem — this iteration was authorized to write
     only to those five cache tables.

6. **Deferred — do this on the next iteration where the app is allowed to run, NOT now.** Once
   maintenance isolation lifts: start the backend and frontend via the project's prod launch
   scripts, navigate to `http://localhost:3255/data`, and look at the "Per-date availability" card.
   - **Expect:** the card shows the empty state — title **"No availability yet"**, description
     "There are no stored trading days to chart. Fetch real EOD prices to populate the dataset, then
     the per-date availability appears here." This is the actual payoff of this iteration's work:
     before Stage F, this card would have silently shown the OLD pre-incident heatmap with no
     warning banner, looking completely current. Stage F deleted that stale row, so the page now
     tells the truth instead of a silent wrong answer. (If a later iteration's data job has already
     refreshed this card by the time you check, a populated grid is fine too — just confirm it does
     NOT show a stale-looking grid with no stale banner and mismatched dates.)

7. **Also deferred.** Once the app is bootable: navigate to `http://localhost:3255/stocks`, filter
   by Sector = "Unassigned".
   - **Expect:** Unassigned share of resolved members is at most 5%. This journey (J-01) was not
     touched by iteration 21 — `git status --porcelain -uall` grepped against `scoring.py`,
     `compass.py`, `data_manager.py` shows zero matches (recorded in the dev handoff's "Files
     Changed" section, independently re-confirmed while writing this guide) — so this should read
     exactly as it did before iteration 21.

8. **Also deferred.** Once the app is bootable: navigate to `http://localhost:3255/`, open one
   candidate card.
   - **Expect:** its Leadership/Entry/Risk words, score, and bucket match the `GET /api/stocks` row
     for the same ticker at the same as-of, and every reason/caution cites a threshold plus the
     stored actual value. This journey (J-04) was also untouched by iteration 21, for the same
     file-proof reason as step 7.

---

## What "Working Correctly" Looks Like

- The seven status lines in step 1 read as an honest, further-along partial success: Stages D/E/F
  all complete, Stage G still pending, incident still marked not-repaired. That combination is the
  CORRECT outcome for this iteration — do not treat a `NOT REPAIRED` line as a failure of iteration
  21's own scope, and do not treat `STAGE F COMPLETE: YES` as "J-11 is done."
- Every number in steps 2-5 cross-checks against another number in the same or a sibling file (and
  against a fresh live query in step 4) with no discrepancy — that reconciliation, not any single
  figure alone, is what proves the deletion was scoped correctly and nothing else was touched.
- Step 6 is the one genuinely new user-facing consequence of this iteration: an honest "not yet
  computed" message replacing what used to be a silently-stale-but-labeled-current heatmap.

## If Something Looks Wrong

- **Numbers don't reconcile (e.g., step 2's total ≠ the sum of its own five per-table deletions, or
  step 4's live query disagrees with steps 2-3):** stop and report it — do not assume rounding or a
  stale file; the evidence files were generated seconds apart by the same run (`generated_at`
  timestamps in each JSON confirm this).
- **`table_sweep_diff.changed_existing_tables` (step 5) contains anything besides the five named
  cache tables:** this means a write escaped its authorized scope. Do not start the app. Do not
  attempt any fix. Report it immediately — this is exactly the class of error the maintenance
  boundary exists to catch.
- **Tempted to start the backend/frontend to "just double-check" something visually:** don't, until
  a later iteration explicitly authorizes app boot (no earlier than J-11 Stage G). Steps 1-5 above
  need no running app; steps 6-8 are explicitly deferred, not "try it now anyway" — a single request
  against one of the 11 quarantined incident dates could permanently write bad data.
