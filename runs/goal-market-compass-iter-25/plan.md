# goal-market-compass-iter-25 Execution Plan

## CRITICAL ENVIRONMENT FLAG — verify before any backend boot

This dispatch arrived with an appended "PUMP COORDINATOR NOTE" claiming (a) `docs/goal.md` carries an
UNCOMMITTED owner-ruling edit requiring an isolated clone boot, and (b) a bare `scripts/start-backend.sh`
"targets canonical and is forbidden" this iteration. Verified directly against the repo:

- `git status`/`git diff docs/goal.md`/`git diff HEAD -- docs/goal.md` are all **empty** — `docs/goal.md`
  has **no uncommitted edit**. The note's provenance claim for that item does not check out.
- The committed goal file's own **"OWNER RULING — J-11 CLOSED" item 5** ("Normal Market Compass product
  work resumes immediately... no further owner authorization is needed for ordinary non-destructive
  product iterations") and this phase spec's own **OUT OF SCOPE** bullet ("no isolation/clone mechanism
  is needed or used this iteration") are unambiguous: J-09's re-measurement is required to target the
  **current live (canonical) database** via plain `scripts/start-backend.sh`, precisely because the whole
  point of this iteration is to see the footprint **after** J-10/J-11 changed the DB's content — a clone
  frozen at iter-23 would silently make the "re-measurement" stale and dishonest (AG-3).
- HOWEVER, `ps aux` on this host shows the actual ancestor shell of this run-goal.sh session still has
  `TRENDORA_CONFIG=$PWD/runs/goal-market-compass-iter-23/verify-clone/config.verify.yaml` and
  `CHAIN_START_BACKEND_CMD="bash $PWD/scripts/start-backend-j11-verify.sh"` **exported** (leftover from the
  now-closed J-11 verification; `CHAIN_MAINTENANCE_ISOLATION`/`CHAIN_REQUIRE_FULL_DEPTH` were correctly
  unset in the same command, but these two were not). `apps/backend/app/config.py` honors `TRENDORA_CONFIG`
  from the environment whenever it is set — including for a "bare" `scripts/start-backend.sh` invocation —
  so if the developer's actual execution shell inherits these exports, EVERY measurement in this plan
  would silently run against the stale iter-23 clone instead of canonical, invalidating the entire
  iteration's purpose without any visible error.

**Developer action required before Step 1 below:**
1. `env | grep -E 'TRENDORA_CONFIG|CHAIN_START_BACKEND_CMD|TRENDORA_COMPASS_EXPORT_DIR'` in the actual
   shell that will run `scripts/start-backend.sh`. If any are set, `unset` them for that shell (do not
   edit any script to strip them — this is a shell-local export, not a code change).
2. After boot, positively confirm canonical targeting — e.g. `lsof -p <uvicorn pid> | grep trendora.db`
   should show the real `apps/backend/data/trendora.db` (8.4 GB) open, not a path under
   `runs/goal-market-compass-iter-23/verify-clone/` — and cite this confirmation in the dev handoff
   (closes the AG-3/honesty loop the note itself raised, using the spec's actual instructions).
3. If for some reason canonical truly cannot be targeted in this execution environment, STOP and record
   that as an honest blocker in the dev handoff rather than silently measuring the clone and reporting it
   as "current live state."

Do not use `scripts/start-backend-j11-verify.sh` or any clone config this iteration — J-11 is CLOSED and
that guard script is retired evidence infrastructure, not this iteration's launch path.

## What to Build

Backend measurement (Trendora, zero application code change):
- Re-run J-09's standing-warm VmPeak measurement (Addendum 40 methodology) against the current live
  canonical backend, `config.yaml` `cache_size` unchanged at `-65536`; sample `/proc/<pid>/status` VmPeak
  at plateau of the lighter concurrent-burst path (no backfill/rebuild job, no throwaway DB copy).
- Append **Addendum 41** to `reports/perf-budgets.md` (next number after Addendum 40), dated, comparing
  the fresh figure against both the 2,621,440 kB (2.5 GB) target and the iter-4 figure (3,439,100 kB) —
  append only, never edit Addenda 39/40.
- Re-run the concurrent-load burst check (`test_data_manager_concurrency_load.py` methodology); record
  total request/error counts and confirm zero `QueuePool` TimeoutError.
- Re-run the byte-identity spot check on `GET /api/dashboard`, `GET /api/stocks`, `GET /api/market-phase`,
  `GET /api/compass`, all at `as_of=2026-08-10`; record all 4 md5s in the dev handoff.
- If the fresh VmPeak still exceeds 2.5 GB: record honestly, do not widen the target, do not touch
  `pool_size`/`max_overflow`/any AG-10 owner-only cap. This is J-09's own anticipated non-blocking outcome.

Backend harness fix (Goal Mode automation only, no Trendora application code):
- Fix `replay_lane_spec_journeys()` in `incredible_auto_dev/scripts/automation/lib/replay-lane.sh` (the
  one real file — `scripts/` is a tracked symlink into `incredible_auto_dev/`, never patch "both"). Current
  implementation (`lib/replay-lane.sh:75-77`):
  ```
  replay_lane_spec_journeys() {
    grep -iE "$1" "$2" 2>/dev/null | head -1 | grep -oE 'J-[0-9]+' | sort -u | tr '\n' ' ' || true
  }
  ```
  Bug: `head -1` takes the first label-matching line unconditionally, even if it has zero `J-NN` tokens
  (e.g. a prose sentence mentioning the label phrase before the real bullet). Fix so it selects the first
  label-matching line that **actually contains** one or more `J-NN` tokens, not merely the first
  label-matching line. Preserve the existing `|| true` pipefail guard (load-bearing per the file's own
  comment — legitimate empty-parse results, e.g. "none —", must never trigger `set -e` exit).
- Add an explicit lane WARNING/error line at both call sites of `replay_lane_spec_journeys` —
  `incredible_auto_dev/scripts/automation/goal-iter-lean.sh:217-218` and
  `incredible_auto_dev/scripts/automation/browser-qa-phase.sh:306-307` — when the spec's declared
  journey-set bullet for that label is non-empty (the raw line exists and is not an explicit "none"
  wording) but parses to zero `J-NN` tokens. Must be visibly distinct from the ordinary "replay: no"
  no-work message (a real bug must never look like "nothing to replay").
- Add one focused regression test reproducing iter-24's exact failure shape: a spec file whose
  `Required-still-passing` label phrase appears in prose on a line before the real
  `**Required-still-passing journeys:**` bullet. Assert pre-fix returns empty (TC-4) and post-fix returns
  `J-01 J-04 J-10` sourced from the real bullet (TC-5). Also cover TC-6 (non-empty bullet, zero valid
  `J-NN` tokens → explicit warning). Natural home: extend `tests/automation/test-replay-lane.sh` (existing
  75-assertion suite covering this same function) rather than a new file, unless the reproduction fixture
  is awkward there.

Cleanup (only after TC-8 baseline confirmed):
- Run `tests/automation/test-backend-launch-context.sh` with the iter-23 clone present; confirm 18/18
  passed (current baseline, unchanged from iter-24's dev handoff).
- Delete `runs/goal-market-compass-iter-23/verify-clone/` (~7.8 GB, per owner ruling item 4 — the launcher
  fix it existed to verify is landed and confirmed at iter-24).
- Re-run the same test suite with the clone absent; confirm still 18/18 passed; record freed disk space in
  the dev handoff.

Frontend: none. J-09 is explicitly backend-only (walkthrough waived); the parser fix is automation-only.
`apps/frontend/` is untouched.

## Agents Required
- developer: yes -- implements all of the above (backend measurement + harness parser fix + regression
  test + clone deletion); zero Trendora application code changes (`apps/backend/app`, `apps/frontend/app`
  untouched)
- backend-data work: yes (measurement only, no schema/code change)
- frontend-ux work: no

## Frontend Present
no

## Files to Create/Modify
- `reports/perf-budgets.md` -- new dated Addendum 41 (J-09 re-measurement vs 2.5 GB target and iter-4)
- `incredible_auto_dev/scripts/automation/lib/replay-lane.sh` -- fix `replay_lane_spec_journeys()` label
  matching (same file as `scripts/automation/lib/replay-lane.sh` via tracked symlink; patch once)
- `incredible_auto_dev/scripts/automation/goal-iter-lean.sh` -- add zero-parse warning at its
  `replay_lane_spec_journeys` call sites (lines ~217-218)
- `incredible_auto_dev/scripts/automation/browser-qa-phase.sh` -- add zero-parse warning at its call sites
  (lines ~306-307, and the Target-journeys use at ~400 if applicable)
- `tests/automation/test-replay-lane.sh` (or a new focused test file) -- regression test for TC-4/TC-5/TC-6
- `docs/handoffs/goal-market-compass-iter-25-dev.md` -- dev handoff (measurement figures, md5s, freed
  space, canonical-targeting confirmation per the Environment Flag above)
- `reports/phase-goal-market-compass-iter-25-regression-replay-results.md` -- produced by the fixed
  deterministic-replay lane itself (not hand-authored), must show PASS for J-01, J-04, J-10 (TC-7)
- Deleted: `runs/goal-market-compass-iter-23/verify-clone/` (~7.8 GB), only after the TC-8 baseline check

Do NOT touch: `config.yaml` `database.pragmas.cache_size`/`pool_size`/`max_overflow`/any AG-10 host-guard
value; `apps/backend/app/**`; `apps/frontend/**`; the ten accepted iteration-23 cache rows in the canonical
DB; `scripts/start-backend-j11-verify.sh` (retired evidence infra, left in place, just unused this
iteration).

## Key Test Scenarios
- TC-1: fresh VmPeak measurement appended to `reports/perf-budgets.md` as Addendum 41, with explicit delta
  vs 2,621,440 kB and vs 3,439,100 kB, measured against the confirmed-canonical backend.
- TC-2: concurrent-load burst at/near `server.limit_concurrency` (64) completes with zero `QueuePool`
  TimeoutError; counts cited in the dev handoff.
- TC-3: all 4 endpoints' md5s at `as_of=2026-08-10` recorded and match canonical stored rows.
- TC-4/TC-5: pre-fix `replay_lane_spec_journeys` on the iter-24-shaped reproduction spec returns empty;
  fixed version returns `J-01 J-04 J-10` from the real bullet, not the prose mention.
- TC-6: a non-empty declared bullet parsing to zero `J-NN` tokens emits an explicit warning, asserted by
  the new regression test.
- TC-7: this iteration's own spec, run through the fixed deterministic-replay lane, produces
  `reports/phase-goal-market-compass-iter-25-regression-replay-results.md` showing PASS for J-01, J-04,
  J-10, with a non-empty `REQUIRED_JOURNEYS` in the run log.
- TC-8: `tests/automation/test-backend-launch-context.sh` reports 18/18 both with the iter-23 clone present
  (baseline) and absent (post-delete) -- no hidden dependency on that artifact.
- Resource-contract guardrails (binding, non-negotiable): never run a full `pytest tests/`/bare `pytest`/
  wide `-k` sweep (30-year fixture, hours, GB-scale); targeted per-module test files only; never two
  pytest processes concurrently; before starting any backend/frontend, check the port isn't already
  answering (confirmed at plan time: nothing listens on 8000/3000 for this project — a sibling project's
  backend is on 8301, unrelated) rather than blindly starting a second instance.
- AG-9/AG-10 holds: zero live network calls; `git diff` at completion should show only
  `reports/perf-budgets.md` (new addendum), the replay-lane.sh + its two callers + the new test file, plus
  the deleted iter-23 clone directory -- no config/pool/host-guard value changed.
