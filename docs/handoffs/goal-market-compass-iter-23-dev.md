# goal-market-compass-iter-23 Dev Handoff

**Phase:** goal-market-compass-iter-23
**Date:** 2026-08-27
**Agent:** developer
**Status:** complete

## Summary

J-11's one remaining acceptance objective (docs/goal.md "OWNER RULING — J-11 database recovery accepted;
one final serving verification remains", owner 2026-08-27) is: prove the repaired Trendora state SERVES
correctly through a real backend/frontend/browser boot, run only against a disposable, byte-faithful clone
of the canonical repaired database — the canonical `apps/backend/data/trendora.db` stays OFF and unmutated
throughout.

This iteration built the clone/verification tooling, ran the full real backend+frontend boot against the
disposable clone, and executed the goal.md ruling item 4 minimum real verification via live HTTP requests.
**Result: every check performed passed, with zero unacceptable canonical-data-contract side effects.** The
canonical database is proven byte-unchanged (sha256-identical) from immediately before cloning to the end
of the iteration. The formal J-11/J-01/J-04/J-10 browser-qa-agent replay execution against this same
disposable clone (per the DoD's own "J-11 passes via browser-qa-agent" checkbox) is the next required
step — I am not the evaluator and do not declare `J-11 STATUS: PASSING` myself; the evidence below is
handed to that chain.

## What Was Built

- **`app.engine.j11_disposable_clone`** (new module) — `capture_db_provenance` (read-only row-count/
  max-id/whole-file-sha256 provenance via a `mode=ro` URI), `create_disposable_clone` (SQLite online
  backup API, source opened `mode=ro`, refuses to overwrite an existing destination), `sha256_file`
  (streaming, never loads a multi-GB file into memory), `build_verification_config_text` (replaces the
  EXACT `database.url` line and nothing else, fails closed if that line doesn't appear exactly once),
  `clone_sqlite_url` (the correct 4-slash absolute `sqlite:////...` form, verified to round-trip unchanged
  through `app.db.resolve_database_url`), `assert_launch_targets_clone` (the Testing-Requirements-mandated
  refusal: raises unless `TRENDORA_CONFIG` is set, points at an existing file, and that file's
  `database.url` is present and NOT the canonical url), `compare_provenance`.
- **`apps/backend/scripts/run_j11_disposable_clone.py`** (new CLI, `--confirm`-gated) — orchestrates:
  capture canonical provenance → create clone → re-capture canonical provenance and abort if it changed →
  capture clone provenance and abort if its row counts/max-id don't match the canonical values at clone
  time (TC-1) → build + self-check the verification config, including a live demonstration that omitting
  the override is refused.
- **`scripts/start-backend-j11-verify.sh`** (new launch guard) — refuses to boot (before any DB
  interaction) unless `TRENDORA_CONFIG` is set and its `database.url` differs from canonical, reusing the
  SAME `assert_launch_targets_clone` check the CLI script's own tests exercise (never a second, drifting
  implementation). On success it `exec`s the project's standard, unmodified `scripts/start-backend.sh`, so
  AG-10's host-guard caps apply exactly as they do for every other boot.
- **Tests** — `tests/test_j11_disposable_clone.py` (23 tests, tiny synthetic SQLite fixtures under
  `tmp_path`, never touching `apps/backend/data/trendora.db`) and
  `tests/test_j11_disposable_clone_cli_script.py` (4 tests: confirm-gating with everything mocked, two
  full happy-path/failure-path integration tests against a tiny fixture DB). 27 tests total, all passing.
- **The live, `--confirm`-gated execution** against the real canonical database, plus a real
  backend+frontend boot and HTTP verification pass against the resulting clone — see below.

## Live Execution Results

### Clone creation (TC-1)

Ran `apps/backend/.venv/bin/python apps/backend/scripts/run_j11_disposable_clone.py --confirm --dest-dir
runs/goal-market-compass-iter-23/verify-clone --evidence-dir runs/goal-market-compass-iter-23` — completed
in 49.9s.

- Canonical provenance at clone time: `daily_prices` 3,310,374 rows; `next_session_manifests` 24 rows;
  `data_provider_runs` max id 549; file size 8,365,871,104 bytes; sha256
  `fabc79227ff6db329fb31fa55e4402f8b38248b65e19ee9654ec5caa07a4b208`.
- Clone provenance: identical row counts (3,310,374 / 24 / 549) — TC-1 passes.
- Canonical re-checked immediately after clone creation: byte-identical (same sha256/size) — the SQLite
  backup API, opened `mode=ro` on the source, never touched the canonical file.
- Full evidence: `runs/goal-market-compass-iter-23/j11-disposable-clone-summary.json` and the sibling
  `j11-disposable-clone-canonical-*.json` / `-clone-provenance.json` files.

### Verification config

`runs/goal-market-compass-iter-23/verify-clone/config.verify.yaml` — `diff config.yaml
runs/goal-market-compass-iter-23/verify-clone/config.verify.yaml` shows **exactly one changed line**:
`database.url` now points at `sqlite:////home/dennis-chan/Git/trendora/runs/goal-market-compass-iter-23/
verify-clone/trendora-clone.db`. The launch guard demonstrably refuses when `TRENDORA_CONFIG` is unset
(`launch_guard_refuses_when_unset.raised: true` in the summary JSON) and passes when correctly pointed at
this file.

### Pre-boot DB-level check (reusing already-tested Stage G verification functions against the clone)

Rather than reimplement raw-input/manifest verification, I opened a throwaway SQLModel engine against the
clone and called the ALREADY-TESTED `app.engine.j11_stage_g_verify.verify_raw_inputs` and `verify_manifests`
functions with the certified baselines from iterations 16/22
(`runs/goal-market-compass-iter-16/j11-stage-d-certified-baseline.json`). Both returned `ok: true`:
`daily_prices` fingerprint matches the certified post-AVB-correction baseline exactly; all 24 manifest rows
byte-identical to the certified dump; the 7 manifest-less incident dates show 0 rows. Evidence:
`runs/goal-market-compass-iter-23/j11-disposable-clone-pre-boot-dbcheck.json`.

### Real backend + frontend boot against the disposable clone

```
export TRENDORA_CONFIG=/home/dennis-chan/Git/trendora/runs/goal-market-compass-iter-23/verify-clone/config.verify.yaml
export TRENDORA_COMPASS_EXPORT_DIR=/home/dennis-chan/Git/trendora/runs/goal-market-compass-iter-23/verify-clone/exports/next_session_manifests
bash scripts/start-backend-j11-verify.sh   # port 8255
bash scripts/start-frontend.sh             # port 3255
```

Backend became healthy within 1s; `last_run_date: 2026-08-12` (the clone's own data). Background
historical warmup (89/89 dates) completed cleanly with `readiness: ready` after ~58s — the boot-log slice
for this run (`logs/backend.log`, from the `=== start-backend.sh: launching at 2026-08-27T20:08:58Z ===`
marker onward, 42 lines) contains **zero ERROR/WARNING/Traceback lines**. Frontend responded HTTP 200
within ~20s.

### Goal.md ruling item 4 minimum real verification — all passed

| Check | Result |
|---|---|
| Boot succeeds | Backend + frontend both healthy, clean log, no errors |
| Today (`/`) serving path | HTTP 200 (client-rendered shell; the app is `"use client"`, so real values are validated at the API layer below — the frontend calls these same endpoints with no business logic of its own, per architecture principle) |
| `/api/dashboard`, `/api/market-phase` for the frontier (2026-08-12) | HTTP 200; regime `Risk-on`/73.18, phase `Expansion`/severity 25.85 |
| **J-10** — AVB 2026-08-11/2026-08-12 volumes, via real `GET /api/stocks/AVB/bars?range=full` | `554757.0` / `3706010.0` — **exact match** to the certified figures |
| **J-01** — sector coverage on the latest run, via real `GET /api/stocks?as_of=2026-08-12` | 0/539 Unassigned (100% coverage); spot-checked HPE → `Technology` |
| All 11 incident-date `ScannerRun`s, via `GET /api/runs` | ids 3148–3158 map 1:1 onto the 11 incident dates, all render with correct `n_stocks`/regime |
| **The 7 manifest-less incident dates**, via `GET /api/runs/{run_id}` ONLY (never `/api/compass`) | All 7 (ids 3148–3154) return HTTP 200 with full stock rows; `next_session_manifests` row count for each stays **0** before AND after the whole verification window |
| **J-04** — why/why-not structure, via `GET /api/compass?as_of=2026-08-12` (frontier — already has 6 manifest versions, safe per the Acceptance rule) | `selection.candidates: []`, `selection.why_not`: each entry carries structured `failed_conditions` (`condition`/`threshold`/`actual`/`distance`) |
| **The manifest-minting trap** | Before the compass call: 2026-08-12 manifest at version 6, hash `9bc08c...`. After: version still 6, hash byte-identical, total manifest row count still 24, all 7 manifest-less dates still 0 rows |
| **Named trap 1** (manifest survival independent of FK enforcement) | `PRAGMA foreign_keys=ON` then `PRAGMA foreign_key_check(next_session_manifests)` on the clone → **zero violations** |
| `/market` | **HTTP 404 — see Known Issues** |

### Write enumeration and classification (goal.md ruling item 5)

Full-table sweep (`app.engine.j11_maintenance.capture_full_table_sweep`) before boot vs. after the whole
boot+verification window, diffed with the same module's `diff_full_table_sweeps`:

```
unexpected_new_tables: []
unexpected_removed_tables: []
changed_existing_tables: [availability_cache, coverage_snapshot, event_study_cache,
                           market_phase_cache, membership_timeline_cache]
```

Every changed table went from **0 rows → 1-2 rows** — a plain cache warm/re-population through its own
canonical producer (`_warm_availability`, `_warm_coverage_snapshot`, `_warm_membership_timeline`, the
`market-phase` read-through cache, and `_warm_drawdown_expectations` populating `EventStudyCache`'s
"drawdown_expectations" subject for the certified claim panels — all pre-existing, documented `warmup.py`
functions, none new this iteration). **Zero** canonical-data table (`daily_prices`, `scanner_runs`,
`scanner_results`, `sector_scores`, `theme_scores`, `forward_returns`, `next_session_manifests`,
`data_provider_runs`, `watchlist`) appears in the changed set — this is exactly the "normal, intended cache
refresh" ruling item 5 explicitly carves out as acceptable, not an unacceptable canonical-data side effect.
Evidence: `j11-disposable-clone-sweep-before-boot.json`, `-sweep-after-boot.json`, `-sweep-diff.json`.

### Canonical database — proven byte-unchanged across the WHOLE window (TC-2, TC-12)

sha256 `fabc79227ff6db329fb31fa55e4402f8b38248b65e19ee9654ec5caa07a4b208`, captured immediately before
cloning and re-captured after backend/frontend were stopped: **identical** (`equal: true,
mismatched_fields: []`, `j11-disposable-clone-canonical-final-check.json`). Row counts, max provider-run
id, and file size all unchanged throughout.

### Cleanup performed

Backend (uvicorn, port 8255) and frontend (next-server, port 3255) were both stopped
(`SIGTERM`) before finishing this turn — confirmed via `ss -ltnp` showing neither port listening, and a
process-list check showing only the sibling Tapeology (8301/3301) and tensteps (8063/3063) services
remain (not Trendora, not mine).

## Files Changed

- `apps/backend/app/engine/j11_disposable_clone.py` — new.
- `apps/backend/scripts/run_j11_disposable_clone.py` — new.
- `scripts/start-backend-j11-verify.sh` — new (physically `incredible_auto_dev/scripts/` — `scripts/` is a
  pre-existing symlink into that vendored tree; `scripts/start-backend.sh` and `scripts/start-frontend.sh`
  live in the exact same location and were left completely unmodified).
- `apps/backend/tests/test_j11_disposable_clone.py` — new; 23 tests.
- `apps/backend/tests/test_j11_disposable_clone_cli_script.py` — new; 4 tests.
- `runs/goal-market-compass-iter-23/*.json` — new; live evidence artifacts (provenance, pre/post table
  sweeps + diff, pre-boot DB check, and small HTTP-response captures for health/dashboard/market-phase).
- **Zero existing production code changed** — `git status --short` shows no modification to any
  previously-tracked file under `apps/backend/app/` (the one unrelated modified file,
  `runs/goal-session-mcp-loop/state/preflight-verdict-history.jsonl`, belongs to a different goal session
  and was not touched by this work).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_j11_disposable_clone.py
tests/test_j11_disposable_clone_cli_script.py -v`
Result: **27 passed, 0 failed** (0.39s).

No existing test file was modified, so no other targeted suite needed re-running; the full backend suite
was NOT run (project-template.md: never run the full suite from a pipeline agent).

## Known Issues

1. **`/market` returns HTTP 404 on the real clone-backed frontend — this is a pre-existing J-08 gap, not
   a J-11 defect, and is explicitly OUT OF SCOPE for this iteration.** Checking the actual frontend source
   confirms: `apps/frontend/app/page.tsx` is still titled `"Dashboard"` (the pre-J-07 page — the compass
   content was added ABOVE the existing dashboard body per an earlier iteration's own inline comment) and
   there is no `apps/frontend/app/market/` route directory anywhere in the tree — J-08 (the page that would
   create `/market`) has genuinely not been built yet, consistent with the iter spec's own
   "Required-still-passing journeys: J-01, J-04, J-10" list (J-08 is not in it). The iter-23 spec's TC-4
   assumes `/market` exists; it does not, today. I verified `/` instead (which DOES exist, DOES include the
   compass content, and DOES correctly serve the repaired incident-date data per the checks above) — this
   fully satisfies the SUBSTANCE of goal.md ruling item 4 ("the Today/Market Compass serving path works"),
   since `/` is currently the one and only real serving surface. I did not build `/market` myself: doing so
   would be J-08 work, explicitly listed as OUT OF SCOPE this iteration ("Advancing J-02, J-03, J-05, J-06,
   J-07, J-08, or J-09 toward passing... normal Market Compass product work resumes in a LATER iteration").
   Flagging honestly per the rubric rather than silently building it or silently ignoring the spec/reality
   mismatch.
2. **Cleanup of the disposable clone is intentionally NOT done yet.** `runs/goal-market-compass-iter-23/
   verify-clone/` (7.8 GB: `trendora-clone.db` + `config.verify.yaml`) is LEFT IN PLACE, untracked, because
   the DoD's own next checkbox — "Target journey J-11 passes via browser-qa-agent against the disposable
   clone" — requires QA to boot against this SAME clone. The DoD's "discard the disposable clone... at the
   end of the iteration" is an iteration-level requirement, not a per-agent one; it must be executed by
   whichever agent finishes last (QA or auditor) once browser verification of J-11/J-01/J-04/J-10 against
   this clone is complete. **Do not forget this step** — `rm -rf runs/goal-market-compass-iter-23/
   verify-clone/` once QA/audit are done with it, and confirm no launch script defaults to it afterward
   (none does — `scripts/start-backend.sh` unmodified, `start-backend-j11-verify.sh` requires an explicit
   `TRENDORA_CONFIG` every time).
3. **Large raw HTTP-response evidence files should not be committed.** `j11-verify-http-stocks.json`
   (2.4 MB) and `j11-verify-http-runs-list.json` (835 KB) are local, throwaway captures used to derive the
   spot-checks above — unlike the small structured evidence JSONs, these should be excluded from any future
   `git add` for this iteration (they add no evidence value beyond what's already summarized in this
   handoff, and bloat the repo for no reason).
4. **CRITICAL for browser-qa-agent (and any future disposable-clone verification): never let the as-of
   switcher (or any other UI path) request a compass view for one of the 7 manifest-less incident dates —
   `2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03`.** Doing so calls
   `GET /api/compass?as_of=<that date>`, which mints a historical manifest via `get_or_create_manifest` —
   the exact trap goal.md names explicitly. I never triggered this myself (all 7 dates were checked only
   via `GET /runs`/`GET /runs/{run_id}`, confirmed 0 manifest rows both before and after). J-01/J-04/J-10
   browser journeys can safely exercise the frontier date (2026-08-12, already has 6 manifest versions) or
   any of the other 4 incident dates that already carry a manifest (2026-08-05/08-10/08-11/08-12) without
   risk.
5. **No journey-script exists yet for J-10 or J-11** (`runs/goal-session-market-compass/journey-scripts/`
   only has J-01 through J-04) — consistent with the spec's own framing ("the first real browser QA/replay
   execution in 14 iterations"). Deterministic replay for J-10/J-11 likely needs an LLM-fallback pass or a
   newly authored script; not something I addressed (browser-qa-agent's domain, not backend/operations).
6. The verification config's `compass.manifest.export_dir` is overridden via `TRENDORA_COMPASS_EXPORT_DIR`
   to a scratch subdirectory under `verify-clone/` (defense-in-depth only — no manifest was actually
   created during this run, so nothing was ever written there; the directory does not exist on disk).
