# Phase goal-market-compass-iter-22 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-22
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Before you start

This iteration is **backend-only** (`Frontend Present: no`) and ran under **maintenance
isolation** for its entire duration: the backend, the frontend, and a browser were all forbidden
from running for the whole iteration. There is nothing at `http://localhost:3255` to click, and
**that is still true right now** — do not start the backend or frontend to run this guide.

Iteration 22 executed J-11 **Stage G** — the terminal acceptance gate — and it passed: the incident
is now reported `J-11 INCIDENT STATUS: FULLY REPAIRED`, and Stage G performed its one authorized
write, deactivating the `j11-incident-recovery` maintenance boundary (`active: 1 → 0`). **This is
real, verified progress, but it is not the same thing as "safe to boot."** Two request-path write
routes remain unguarded by design — `scanner.py::resolve_run` and `compass.py::get_or_create_manifest`
— and whether to authorize a boot is an explicit owner decision that has not been made. A single live
request against one of the 7 formerly-quarantined dates that still has zero manifest could
permanently mint a manifest outside the normal pipeline (manifests are immutable once created).

Instead, this guide verifies iteration 22's actual work — J-11 Stage G's full 12-category
verification plus its one write — using the evidence files it already produced, plus a couple of
read-only database queries. Steps 1-6 are files/queries you check; none requires the app to be
running. Steps 7-9 tell you what to do once the app IS bootable (an explicit future owner decision,
not this iteration).

---

## Prerequisites

- A terminal with read access to the repo at `/home/dennis-chan/Git/trendora`.
- No running backend, frontend, or browser needed for steps 1-6.
- `sqlite3` available on the PATH for steps 5-6 (read-only mode only).

---

## Steps

1. Open `docs/handoffs/goal-market-compass-iter-22-dev.md` and find the status block near the top.
   - **Expect:** exactly these five lines — `J-11 STAGE D EXECUTED: YES`,
     `J-11 STAGE E COMPLETE: YES`, `J-11 STAGE F COMPLETE: YES`, `J-11 STAGE G VERIFIED: YES`,
     `J-11 INCIDENT STATUS: FULLY REPAIRED`. This is the first time any iteration in this arc
     (19 through 22) has reached `FULLY REPAIRED` — iterations 19-21 each ended
     `NOT REPAIRED — ATTEMPT INCOMPLETE`.

2. Open `runs/goal-market-compass-iter-22/j11-stage-g-verify-verdict.json` and find `full_pass` and
   `category_results`.
   - **Expect:** `"full_pass": true`, `"failing_categories": []`, and all 12 category keys read
     `true`. **One thing to know before trusting this file:** the reviewer initially FAILED this
     iteration because one category (`membership_timeline_reconciled`) was computed by an
     always-true tautology, and the boundary-deactivation write ran before the one real check that
     did exist. A same-day fix pass added a genuine check and reordered the script so it runs before
     the write, then proved — by independently replaying this run's own recorded evidence through the
     corrected logic — that the same `true` result holds for the real reason (the corrective delete
     genuinely happened and a live recount genuinely confirmed it). 71 tests pass after the fix. No
     second database write occurred — the live database still reflects only the original run's one
     write.

3. Open `runs/goal-market-compass-iter-22/j11-stage-g-verify-membership-timeline-check.json` and
   `...-membership-timeline-delete-action.json`.
   - **Expect:** of the 4 already-cached incident dates re-checked, 3 matched exactly and 1 did not —
     `2026-08-10`'s stored `exits` field was `["AMSC", "MARA"]`, but the fresh recompute is `["MARA"]`.
     `"disposition": "explicit_delete"` and the delete-action file reads `"deleted": true`. This is a
     genuine staleness this iteration's own check found and repaired, not a residual problem.

4. Open `runs/goal-market-compass-iter-22/j11-stage-g-verify-write-path-classification.json` and
   find `counts_by_classification`.
   - **Expect:** `{"guarded": 4, "stage_d_authorized_write": 1, "still_open_and_deferred": 7}` across
     12 total call sites, zero unclassified. Look for the entry at `app/api/compass.py:61`
     (`get_or_create_manifest`) and `app/engine/scanner.py:348` (`run_scan`, inside `resolve_run`) —
     both read `"still_open_and_deferred"`. These two are exactly why booting is still not
     authorized, regardless of the boundary now being inactive.

5. Run this read-only query (never opens the database for write):
   `sqlite3 "file:apps/backend/data/trendora.db?mode=ro" "SELECT id, name, active, quarantined_dates_json FROM maintenance_boundaries;"`
   - **Expect:** one row — `1|j11-incident-recovery|0|["2026-05-12", "2026-05-13", "2026-07-10",
     "2026-07-13", "2026-07-24", "2026-07-27", "2026-08-03", "2026-08-05", "2026-08-10",
     "2026-08-11", "2026-08-12"]`. `active` is `0` (deactivated), and the row still lists all 11
     dates — the boundary was deactivated, never deleted.

6. Run this read-only query:
   `sqlite3 "file:apps/backend/data/trendora.db?mode=ro" "SELECT (SELECT COUNT(*) FROM scanner_runs), (SELECT COUNT(*) FROM forward_returns WHERE run_id BETWEEN 3148 AND 3158), (SELECT COUNT(*) FROM next_session_manifests), (SELECT COUNT(*) FROM event_study_cache)+(SELECT COUNT(*) FROM market_phase_cache)+(SELECT COUNT(*) FROM forward_aggregate_cache)+(SELECT COUNT(*) FROM coverage_snapshot)+(SELECT COUNT(*) FROM availability_cache), (SELECT COUNT(*) FROM index_series_cache), (SELECT COUNT(*) FROM membership_timeline_cache);"`
   - **Expect:** `3128|16592|24|0|1|0` — `scanner_runs` (3,128) and the 11 incident runs' forward
     returns (16,592) and `next_session_manifests` (24) are unchanged carry-forward figures; the five
     explicit-delete cache tables sum to 0; `index_series_cache` still holds its one preserved row;
     `membership_timeline_cache` now holds 0 (the step-3 finding). If any of these disagrees with the
     file-based evidence in steps 2-4, treat it as a problem, not a rounding difference.

7. **Deferred — do this only once the owner explicitly authorizes app boot, NOT now.** Start the
   backend and frontend via the project's prod launch scripts, navigate to
   `http://localhost:3255/data`, and look at the "Per-date availability" card for the eleven
   formerly-quarantined dates (2026-05-12 through 2026-08-12, listed in step 5).
   - **Expect:** either the honest empty state ("No availability yet" — all five explicit-delete
     cache tables including `availability_cache` currently hold 0 rows), or, if a normal warm-up job
     has since repopulated it, a grid showing genuinely current, correct values for all eleven
     dates — never the old pre-incident values silently presented as current with no stale banner.
     That specific combination (a populated-looking grid, no stale notice, but actually-stale
     content) is the exact bug this whole J-11 arc exists to prevent.

8. **Also deferred.** Once the app is bootable: navigate to `http://localhost:3255/stocks`, filter
   by Sector = "Unassigned".
   - **Expect:** Unassigned share of resolved members is at most 5%. This journey (J-01) was not
     touched by iteration 22 — `git diff --stat -- apps/backend/app/engine/scoring.py` shows zero
     output, independently re-confirmed while writing this guide — so this should read exactly as it
     did before iteration 22.

9. **Also deferred.** Once the app is bootable: navigate to `http://localhost:3255/`, open one
   candidate card.
   - **Expect:** its Leadership/Entry/Risk words, score, and bucket match the `GET /api/stocks` row
     for the same ticker at the same as-of, and every reason/caution cites a threshold plus the
     stored actual value. This journey (J-04) was also untouched by iteration 22 — `compass.py`
     shows zero diff, for the same reason as step 8, and is separately one of the two files this
     iteration deliberately left the `get_or_create_manifest` gap in (step 4).

---

## What "Working Correctly" Looks Like

- Step 1's five lines read as a clean, all-YES success — this is the correct outcome for this
  iteration, and the first time the arc has reached it. Do not mistake the boundary's deactivation
  (step 5) for permission to boot; those are two separate decisions.
- Every number in steps 2-6 cross-checks against another file or a fresh live query with no
  discrepancy — that reconciliation, not any single figure alone, is what proves Stage G's
  verification actually held.
- Step 4's 7 `still_open_and_deferred` entries (including the 2 named ones you specifically checked)
  showing up is EXPECTED and CORRECT — it means the write-path re-enumeration is honest about what
  remains open, not that something is broken.

## If Something Looks Wrong

- **`full_pass` in step 2 is `false`, or any category reads `false`:** stop and report it — the
  boundary should still read `active=1` in that case (a FAIL performs zero further writes per
  `docs/goal.md` ruling item 14), so a `false` verdict alongside an already-inactive boundary (step 5)
  is a serious inconsistency, not a formality.
- **Numbers don't reconcile (e.g., step 6's live query disagrees with steps 2-4's file contents):**
  stop and report it — do not assume a stale file; the evidence files were generated seconds apart by
  the same run.
- **`write-path-classification.json` (step 4) shows fewer than 7 `still_open_and_deferred` entries,
  or shows `app/api/compass.py:61`/`app/engine/scanner.py:348` as anything other than
  `still_open_and_deferred`:** this means either an unauthorized fix was silently made to an
  out-of-scope file, or the classification itself is wrong. Either way, do not treat the app as safer
  to boot than documented — report it.
- **Tempted to start the backend/frontend to "just double-check" something visually:** don't. The
  boundary being inactive is progress, not authorization. Steps 1-6 above need no running app; steps
  7-9 are explicitly deferred to a future, separately-authorized iteration — a single request against
  one of the 7 still-manifest-less incident dates could permanently mint a manifest outside the
  normal pipeline.
