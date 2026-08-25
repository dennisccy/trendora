# Phase goal-market-compass-iter-14 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-14
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- **No frontend or backend boot required for this guide.** This iteration is backend-only
  (`Frontend Present: no`) and maintenance isolation is ACTIVE — the app must NOT be started and no
  browser automation may run this iteration. Every step below is a read-only file/JSON check you can
  run from a terminal or text editor against the repo at
  `/home/dennis-chan/Git/trendora`.
- Read access to `runs/goal-market-compass-iter-14/` and `docs/handoffs/goal-market-compass-iter-14-dev.md`.
- Do not open `apps/backend/data/trendora.db` for write, and do not copy it (it is several GB).

---

## Verification Steps

1. Open `runs/goal-market-compass-iter-14/j11-stage-d-readiness.json`
   - **Expect:** `"ready": true` and `"authorized": false`.

2. Open `docs/handoffs/goal-market-compass-iter-14-dev.md` and search for the text `STAGE D READY`
   - **Expect:** the literal lines `**J-11 STAGE D READY: YES**` and
     `**J-11 STAGE D AUTHORIZED: NO**` both appear, matching step 1's artifact.

3. Open `runs/goal-market-compass-iter-14/j11-stage-d-attempt-identity.json`
   - **Expect:** `"engine_identity": "53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55"`
     — a freshly computed value, NOT the earlier `"6261ca17..."` identity from iteration 10.

4. Open `runs/goal-market-compass-iter-14/j11-stage-d-preflight-gate.json`
   - **Expect:** `"verdict": {"passed": true, "reason": "all_checks_passed"}`, and under
     `comparison.per_date_scanner_run_present`, all 11 incident dates read `false` (zero `ScannerRun`
     rows on any of them).

5. Open `runs/goal-market-compass-iter-14/j11-avb-bridge-diagnostic.json`
   - **Expect:** `"classification": "AVB-B"` and `"stage_d_ready_per_avb": true` inside the
     `classification` object.

6. Compare `runs/goal-market-compass-iter-14/j11-stage-d-db-file-true-start.json` against
   `runs/goal-market-compass-iter-14/j11-stage-d-db-file-true-end.json`
   - **Expect:** `mtime` and `size_bytes` are identical in both files, and `wal.size_bytes` reads `0`
     in both — this is the proof that zero bytes were written to `apps/backend/data/trendora.db` across
     the whole iteration.

7. **What is deliberately NOT checked here.** J-01 through J-10 (all previously-scored Must-have
   journeys) are not re-verified this iteration — maintenance isolation forbids booting the backend or
   frontend, or running any browser check. Their last recorded statuses in
   `runs/goal-session-market-compass/state/journey-history.json` are unchanged by this iteration: J-01
   passing, J-02 partial, J-03 partial, J-04 passing, J-05 partial, J-06 partial, J-07 failing, J-08
   failing, J-09 partial, J-10 passing. Full exact-click-path regression cases for each (UT-J-01 through
   UT-J-10) are in `reports/phase-goal-market-compass-iter-14-ui-test-plan.md`, ready to run the first
   time the app is permitted to start.

---

## What "Working Correctly" Looks Like

- All six JSON/handoff checks above (steps 1–6) agree with each other: the preflight gate passed, the
  identity is freshly recomputed (not the stale `6261ca17…` value), the AVB diagnostic found no
  Stage-D-blocking issue (`AVB-B`, not `AVB-C`/`AVB-D`), the combined readiness verdict is `YES`, the
  dev handoff states the same `YES`/`NO` lines verbatim, and the database file fingerprint is
  byte-identical from true-start to true-end.
- `"authorized": false` in step 1 and `**J-11 STAGE D AUTHORIZED: NO**` in step 2 are present alongside
  the `YES` readiness verdict — a `READY: YES` line must never appear without the `AUTHORIZED: NO` line
  next to it; a `READY` verdict never means Stage D was actually run.

## Common Issues

- **`ready: false` in `j11-stage-d-readiness.json`**: open `blocking_reasons` in the same file — it
  names exactly which check failed (preflight gate, identity check, or AVB classification `AVB-C`/`AVB-D`).
- **`wal.size_bytes` is non-zero, or `mtime`/`size_bytes` differ between true-start and true-end**:
  this means a write reached `trendora.db` during the iteration, which this iteration is contracted to
  never do — treat as a critical regression, not a formatting issue.
- **`engine_identity` reads `6261ca17…`**: the attempt identity was not freshly recomputed and is
  reusing an earlier attempt's stale value — this is exactly the defect this iteration exists to fix;
  treat as a regression if seen.
- **Dev handoff missing either `STAGE D READY` or `STAGE D AUTHORIZED` line**: the handoff does not meet
  this iteration's Definition of Done — flag rather than infer the missing value from the JSON alone.
