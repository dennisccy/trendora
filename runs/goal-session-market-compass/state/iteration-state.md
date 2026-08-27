# Iteration State — market-compass

**After iteration:** 22 · **Date:** 2026-08-27 · **Verdict:** STALLED

## Journeys

3 passing (J-01 J-04 J-10) · 6 partial (J-02 J-03 J-05 J-06 J-09 J-11) · 2 failing (J-07 J-08) — 11 total. Iter-22 ran under MAINTENANCE ISOLATION: browser QA + replay lane forbidden by contract, so every journey KEEPS its prior status (no `pending_infra`). Spot-checks: J-01 screenshot, J-10 live read-only — both consistent. J-04 keeps `evidence_makeup` (4th iter).

## Active blockers

- **HUMAN-OWNED, THE ONLY REAL BLOCKER: may the application be booted again?** J-11 Stage G PASSED live (12/12 categories, `FULLY REPAIRED`), and the maintenance boundary is now **INACTIVE** (`active=0`, row preserved, 11 dates still listed, `updated_at 2026-08-27 09:27:08`). The owner has NOT decided whether the app may start. Ten journeys can only be verified in a browser, so nothing moves until this is answered. Resume options are enumerated in `iter-22/eval.md` "Halt Justification".
- **BOOT RISK, verified live by the evaluator — read before authorizing:** the quarantine is gone, so **7** unguarded request-path writers are unguarded in fact (`scanner.py::resolve_run`, `data_manager.py:3762 _do_backfill._persist` — ruling item 5's actual two — plus `app/api/compass.py::compass`, `scanner.py::_bootstrap`, `data_manager.refresh_coverage_snapshot`, `_persist_per_date_coverage_snapshots`, `_refresh_ingest_aggregates`). Seven damaged days still have NO manifest (2026-05-12, 05-13, 07-10, 07-13, 07-24, 07-27, 08-03): one page request would permanently mint one. 16 dates in the window have prices but no run: a request would mint a 12th run carrying the rebuild stamp. Two serve-prior-generation caches are empty, so the first post-boot request can compute heavily on the request path — let warmup finish, record peak memory.
- **GOAL-TEXT CONTRADICTION, owner decision:** `docs/goal.md:1408` calls Stage G "final serving/replay verification" while ruling item 4 forbids the boot until Stage G passes. Evaluator ruling (assumptions.md, iter-22): the ATTEMPT honestly reached its owner-defined SUCCESS state; the JOURNEY stays `partial` until the serving check runs.
- **Human-owned, non-blocking:** 5 open owner questions (J-09 3.44 GB; J-06 wording; J-01 test-step wording; empty "next-session focus"; MNST).

## Last 2 verdicts

- iter 22: STALLED — Stage G executed live and passed; incident `FULLY REPAIRED`, boundary deactivated; every figure re-derived read-only by the evaluator; halted because every remaining path needs the owner's boot decision, the boot is irreversible-risky, and goal.md contradicts itself about Stage G's scope.
- iter 21: CONTINUE — Stage F executed live and clean (1,643 stale cache rows deleted across 5 tables); evaluator found a then-unguarded coverage self-heal write path, which iter-22 closed.

## Do not redo

- **Stages D (iter-19), E (iter-20), F (iter-21), G (iter-22) are DONE and live-verified** — never re-run, re-clear or re-regenerate. Evidence: `runs/goal-market-compass-iter-{19,20,21,22}/j11-stage-*.json`. A Stage G re-run would halt at its own preflight anyway (boundary now inactive).
- **The 11 rebuilt runs are frozen**: ids 3148–3158, identity `53d2ffd1…`, created 2026-08-26 10:52:55.552946 → 10:53:02.010362; exactly 11 runs carry that identity and 3158 is the table max. Never restamp or touch. Membership comes from the ids + execution evidence, NEVER from the stamp.
- **Verified untouched — do not re-verify from scratch:** `daily_prices` 3,310,374 rows, fingerprint `80441b37f816d41c…`; all 24 manifests field-identical across 28 columns vs the certified iter-16 baseline, all `prospective_eligible=0`; both ledgers 7 entries all FAIL; `data_provider_runs` 549; `watchlist` 6; caches 0/0/0/0/0 + `index_series_cache` 1 + `membership_timeline_cache` 0.
- **Settled, do not re-litigate:** goal.md step 5's premise that retained runs carry forward-return holes is FALSE for this codebase — population (b) = 0 is CORRECT (iter-20). `membership_timeline_cache`'s row was proven STALE (2026-08-10 `exits`) and deleted per Stage F's pre-approved fallback (iter-22) — do not restore it.
- **Now ELIGIBLE (Stage G has passed), previously deferred:** the 7-path write-path hardening pass; re-pointing the 4 mis-cited traps (auditor B2); `goal_gate.py`'s duplicate-journey defect (it emitted J-10 twice in iter-22's slice — must be fixed before any GOAL_ACHIEVED certification); the `scripts/automation/` forbidden-lane defect.
- **Do not amend `docs/goal.md`** to resolve the Stage G wording — that is an owner edit, not an agent edit.
