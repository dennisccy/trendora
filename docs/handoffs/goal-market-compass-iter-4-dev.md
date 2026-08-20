# goal-market-compass-iter-4 Dev Handoff

**Phase:** goal-market-compass-iter-4 (J-09 — host resource-fit)
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete (target VmPeak honestly MISSED — see Known Issues; everything else in DEFINITION OF DONE is met)

## What Was Built

Backend-only, config-only change per J-09's Steps. No new code paths, no new tests beyond one existing
assertion updated to match the new value.

- `config.yaml`: `database.pragmas.cache_size` changed from `-262144` (256 MB SQLite page cache **per**
  pooled connection) to `-65536` (64 MB). Nothing else in the `database:` block was touched —
  `pool_size: 24` and `max_overflow: 44` (ops-hardening iter-72's sizing to clear
  `server.limit_concurrency` 64) are byte-unchanged. `apps/backend/app/db.py:61` already reads
  `pragmas.cache_size` from the typed config loader with no code change required.
- Re-measured standing-warm VmPeak via a **lighter concurrent-burst path** (no `backfill`/`rebuild` job,
  no throwaway copy of the 7.8 GB `trendora.db`) against a backend started via
  `bash scripts/start-backend.sh` with the new `cache_size`. Two burst profiles were run for
  cross-checking; both plateau well above the iteration's 2.5 GB target — see Known Issues for the full,
  honest result. A new dated Addendum 40 was appended to `reports/perf-budgets.md` (existing content
  untouched — verified via `git diff`, 123 insertions / 0 deletions).
- Re-ran the concurrent-load burst check (`apps/backend/tests/test_data_manager_concurrency_load.py`) and
  a byte-identity spot check across `/api/dashboard`, `/api/stocks`, `/api/market-phase`, `/api/compass` —
  both clean (details below).
- Updated one pre-existing test assertion (`apps/backend/tests/test_db.py::test_sqlite_pragmas_applied_on_connect`)
  that hardcoded the old `cache_size` value, to avoid self-inflicting a regression.

## Files Changed

- `config.yaml` -- `database.pragmas.cache_size` `-262144` -> `-65536` (+ its own inline comment updated
  to state 64 MB instead of 256 MB); every other `database:` key byte-unchanged. Full diff:
  ```diff
       journal_mode: "WAL"
       synchronous: "NORMAL"
       busy_timeout_ms: 30000
  -    cache_size: -262144          # negative = KiB -> 256 MB page cache
  +    cache_size: -65536           # negative = KiB -> 64 MB page cache (iter-4/J-09: was -262144/256 MB;
  +                                 # halved standing pool memory, see reports/perf-budgets.md)
       mmap_size_bytes: 0           # mmap DISABLED (iter-24 audit). ...
  ```
  Note: `mmap_size_bytes`'s own comment (a few lines below, untouched) says "The 256 MB page cache above
  keeps reads fast" — that cross-reference is now stale (should read 64 MB). Left untouched deliberately:
  the DEFINITION OF DONE requires "`pool_size`, `max_overflow`, and every other `database:` key are
  byte-unchanged," and `mmap_size_bytes` is one of those other keys. Flagged here rather than silently
  edited or silently left inconsistent — see Known Issues.
- `apps/backend/tests/test_db.py` -- `test_sqlite_pragmas_applied_on_connect`'s hardcoded
  `assert cache_size == -262144` updated to `-65536` (this test reads the REAL `config.yaml` via
  `make_engine()`'s default `get_config()`, so it would otherwise fail against the new value); its
  neighboring comment's stale "256 MB" reference removed (this is a test-file comment, not a
  `database:` key, so it is not covered by the "byte-unchanged" constraint above).
- `reports/perf-budgets.md` -- Addendum 40 appended (methodology, both VmPeak measurements, the honest
  miss vs. target, the 28.9% reduction from baseline, TC-4/TC-5/TC-7 citations). Purely additive:
  `git diff --stat` shows `123 insertions(+), 0 deletions(-)`; the existing `4,837,420 kB` entry (Addendum
  39, lines ~12018-12055) is untouched.
- `docs/handoffs/goal-market-compass-iter-4-dev.md` -- this file.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_db.py -v -k "pragma"`
Result: **2 passed** in 0.26s (`test_sqlite_pragmas_applied_on_connect`,
`test_sqlite_pragmas_are_config_sourced_not_a_literal`) — the two tests that directly exercise the
changed pragma value.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager_concurrency_load.py -v`
Result: **3 passed** in 1.08s — zero failures, zero `QueuePool` errors, against the NEW `cache_size`
(this file's `load_engine` fixture builds its engine via `make_engine()` with no explicit config, so it
reads the real, now-changed `config.yaml`).

Command (full file, for extra confidence beyond the directly-relevant subset):
`cd apps/backend && .venv/bin/python -m pytest tests/test_db.py -v`
Result: **1 pre-existing, unrelated failure found and NOT fixed** (out of scope — see Known Issues); the
run was stopped before completing the file's `loaded_engine`-dependent tests (see Known Issues) because
of the project's "one pytest process at a time" rule and this run's own multi-tens-of-minutes cost from a
session-scoped full-historical-walk-forward fixture unrelated to this change.

VmPeak re-measurement (TC-1/TC-2, not a pytest run — `/proc/<pid>/status` read against a live backend):
- **Original-methodology replica** (5 workers, the same 6-endpoint mix as
  `test_start_backend_script.py`'s `_POOL_PRESSURE_ENDPOINTS`, same 1.0-2.0s pacing, 150s, matching
  Addendum 39's own drill shape minus the concurrent `backfill` job): plateaued at t+40s and held flat
  through t+140s. **3,439,100 kB.** 465 requests, 0 errors.
- **Stress variant** (24 workers ~= `pool_size`, 10-endpoint mix, 0.1-0.4s pacing, 90s): **4,493,232 kB.**
  4,240 requests, 0 errors.
- Host memory was monitored throughout both bursts (`free -h` / `/proc/meminfo` every 15-20s against the
  iteration's own abort rule: available < ~3 GB or swap used > ~2 GB); available memory never dropped
  below 17.8 GB and swap held flat at ~200 MB — no abort fired.

Byte-identity spot check (TC-5, one-time scripted comparison, not a permanent pytest per the spec's own
TESTING REQUIREMENTS): `GET /api/dashboard`, `GET /api/stocks`, `GET /api/market-phase`,
`GET /api/compass`, all at `as_of=2026-08-10` (a stored historical run — chosen over the frontier date to
avoid `/api/compass`'s `ManifestNotYetFrozen` 404 path, so the comparison exercises a real payload),
captured against two separate backend boots (before the config edit, and after):

| Endpoint | Bytes | md5 (before == after) |
|---|---|---|
| `/api/dashboard` | 915 | `3517776a0ed8ff00875de19266ac2702` |
| `/api/stocks` | 2,503,015 | `ad23a0a6fd0441375ccb097da6274e7a` |
| `/api/market-phase` | 15,064 | `21e448f53d9ee730c4eb041375ccdbbb` |
| `/api/compass` | 333,578 | `fc6c038ad655bbd6dbe5685d42d30b61` |

All four `cmp`-verified byte-identical (zero diff). TC-5 met in full.

TC-7 (single-source confirmation): repo-wide grep for `cache_size` shows exactly 4 real sites —
`apps/backend/app/db.py:61` (the effective-value read, unchanged), `apps/backend/app/config.py:1999`
(the typed loader's documented Python-side fallback default, deliberately left at `-262144` per this
iteration's own OUT OF SCOPE — never the effective value while `config.yaml` is present),
`config.yaml:109` (the one value changed), and `apps/backend/tests/test_db.py:371` (the assertion updated
above). No second hardcoded number determines the effective pragma anywhere.

Service startup / restart (pre-handoff checklist): backend started via `bash scripts/start-backend.sh`,
health-checked (200 within 1s), stopped cleanly (SIGTERM, exited within 2s each time), restarted on the
SAME port with no conflict, stopped again — repeated across every measurement cycle in this session (5
full start/stop cycles total) with zero port conflicts and zero leftover processes at the end (`pgrep -f
"uvicorn main:app"` empty; final `free -h`: 22 GiB available, swap 199 MiB). Frontend was NOT started —
`Frontend Present: no` for this iteration, no frontend code was touched, and starting an unrelated
service was judged an unnecessary resource risk on a host this iteration is specifically about protecting.

## Known Issues

**1. VmPeak target (<=2,621,440 kB / 2.5 GB) is HONESTLY MISSED by the config change alone — flagged for
owner review, per TC-6 / the DEFINITION OF DONE's own explicit "if missed" path.**

| Measurement | VmPeak (kB) | vs. 2.5 GB target |
|---|---|---|
| Addendum 39 baseline (old `cache_size`, heavy backfill+pool-pressure drill) | 4,837,420 | +2,215,980 kB over |
| **This pass, primary figure** (new `cache_size`, original-methodology replica) | **3,439,100** | **+817,660 kB (31.2%) over** |
| This pass, stress variant (new `cache_size`, 24 concurrent workers) | 4,493,232 | +1,871,792 kB over |

A real reduction WAS measured: 4,837,420 -> 3,439,100 kB is a **1,398,320 kB (28.9%) reduction** — but it
does not close the gap to <=2.5 GB. Per this iteration's binding instruction, `memory_cap_mb` (8192),
`malloc_arena_max` (2), `pool_size` (24), and `max_overflow` (44) were **left completely unchanged** —
none were widened or tuned to force the number (AG-10 reserves these to the owner). Both measurements
still carry comfortable margin against `memory_cap_mb` itself (41.0% / 46.4%), so this is a miss of this
iteration's own tighter standing-warm bar, not an AG-10 hard-cap risk.

Why the config change alone likely isn't enough: SQLite's `cache_size` is a soft ceiling a connection
grows into on demand, not a pre-allocation. Addendum 39's own OLD-config measurement (4,724 MB) already
sat below the theoretical "256 MB x 24 connections = 6,144 MB" worst case J-09's own "Why" cites — meaning
even the old, larger ceiling wasn't fully saturated by every connection in that drill. Consistent with
that, a freshly-booted backend with the NEW `cache_size` (no burst load at all) already peaked at
837,860-1,423,852 kB across two independent cold boots — a non-trivial floor `cache_size` cannot touch
(interpreter/uvicorn/anyio baseline + the existing `_BarCache.prefill` warmup, which goal.md's own Host
resource-fit Constraint (c) names as a SEPARATE, not-yet-assigned re-bound, explicitly out of scope for
J-09). Full methodology, both burst profiles, and the complete honest-miss writeup are in
`reports/perf-budgets.md` Addendum 40.

The heavier opt-in live drill (`test_start_backend_phase_by_phase_vmpeak_profile_under_pool_pressure`,
`TRENDORA_RUN_HEAVY_INGEST_TEST=1`, ~31 minutes, copies the 7.8 GB DB) was deliberately NOT run: the
lighter path reproduced a comparable, real, in-the-same-GB-neighborhood peak (not a suspiciously-low
under-measurement), so the spec's own fallback trigger ("if the lighter path does not reproduce a
comparable peak") was not met; this host was also sharing capacity with a second, concurrent goal-mode
engine (different project) throughout this iteration, and the DB-copy pattern that heavy drill uses is
exactly what J-09's own Host resource-fit constraints target for removal. This is a judgment call, not a
spec requirement dodge — recorded here for the reviewer/owner to weigh.

**2. `mmap_size_bytes`'s comment (config.yaml, ~3 lines below `cache_size`) still says "The 256 MB page
cache above keeps reads fast" — now stale (should read 64 MB).** Deliberately left untouched: the
DEFINITION OF DONE requires every OTHER `database:` key to be byte-unchanged, and `mmap_size_bytes` is
one of those keys. A cosmetic, non-functional documentation staleness — flagged, not silently fixed.

**3. `apps/backend/tests/test_db.py::test_create_all_produces_expected_tables` FAILS on this branch —
confirmed PRE-EXISTING and UNRELATED to this iteration's change, not fixed (out of scope).** Isolated
re-run (`pytest tests/test_db.py -k test_create_all_produces_expected_tables -v`, 0.04s):
`SQLModel.metadata.tables.keys()` now includes tables the test's own hardcoded union
(`ITER1_TABLES | SNAPSHOT_TABLES | ... | MEMBERSHIP_TIMELINE_CACHE_TABLES`) doesn't account for —
`coverage_snapshot`, `index_series_cache`, `next_session_manifests` (added by this session's own iter-2/3
compass work), `forward_aggregate_cache`, `availability_cache`, and more. This is a test-constant
staleness issue in `models.py`'s table registry vs. `test_db.py`'s own accounting, structurally
independent of `database.pragmas.cache_size` (this diff never touched `models.py` or any table-set
constant). Flagged for the reviewer/auditor to triage — not fixed here per "do not touch code outside
your task scope."

**4. The full `test_db.py` file was not run to completion.** Beyond the failure above, the file's
`loaded_engine` session fixture (`conftest.py:56`) performs a full historical walk-forward
(`bootstrap_runs` + `backfill_forward_returns` across the entire committed seed) — a legitimately
expensive, unrelated-to-this-change build that was still running after ~14 minutes of CPU time when it
happened to finish naturally (mid-test-list) as I was about to stop it to free the "one pytest process at
a time" slot for the required `test_data_manager_concurrency_load.py` run. The directly-relevant subset
(`-k "pragma"`, above) is verified passing; the remaining `loaded_engine`-dependent tests in this file
exercise seed-loading/pool-sizing/dialect-detection code this diff never touched, so they were not
re-verified this pass. If the reviewer wants full-file confirmation, budget ~15-30+ minutes for it
(matches this project's documented "30y test suite slow, not the product" characteristic) and run it in
isolation, one pytest process at a time.

**5. `test_no_magic_numbers.py` was not run.** No engine code changed this iteration (only `config.yaml`
+ two test files), so its `CALC_FILES` scan has nothing new to check; TC-7's actual ask (single-source
confirmation) was verified directly via grep instead (see Tests Run).
