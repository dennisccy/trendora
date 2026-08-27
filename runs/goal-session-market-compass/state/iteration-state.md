# Iteration State — market-compass

**After iteration:** 21 · **Date:** 2026-08-27 · **Verdict:** CONTINUE

## Journeys

3 passing (J-01 J-04 J-10) · 6 partial (J-02 J-03 J-05 J-06 J-09 J-11) · 2 failing (J-07 J-08) — 11 total. Iter-21 ran under MAINTENANCE ISOLATION: browser QA + replay lane forbidden by contract, so every journey KEEPS its prior status (no `pending_infra`). Spot-checks: J-01 screenshot, J-10 live read-only — both consistent. J-04 keeps `evidence_makeup` (3rd iter).

## Active blockers

- **J-11 Stage G (the acceptance gate) is the ONLY remaining J-11 work — dev-owned, ALREADY AUTHORIZED** by `docs/goal.md` ruling item 9 (commit `5fe72f5c`). No owner sign-off needed; do NOT amend goal.md for it.
- **App/browser/replay must stay OFF through Stage G** (ruling item 4). Three unguarded write paths verified live: `data_manager.py:1544-1546` (self-heal WRITES a coverage row for any explicit `?as_of=` with a real run — would undo Stage F, found by the evaluator, recorded by NO lane); `scanner.py` (zero boundary refs; 16 runless dates 2026-05-14..08-07 would mint a 12th run with the same stamp); `compass.py:1041-1066` (mints a manifest for any of the 7 manifest-less incident dates).
- **J-01..J-09 product work stays blocked** by the loop-mechanics gate until Stage G passes (ruling item 12).
- **Human-owned, non-blocking:** 5 open owner questions (J-09 3.44 GB; J-06 wording; J-01 test-step wording; empty "next-session focus"; MNST). Two framework defects (`scripts/automation/` forbidden-lane bug; `goal_gate.py` duplicate-heading) deferred by the owner until after Stage G.

## Last 2 verdicts

- iter 21: CONTINUE — Stage F executed live and clean (1,643 stale cache rows deleted across 5 tables; `index_series_cache` + `membership_timeline_cache` preserved on live-proven grounds); all lanes PASS/PASS_WITH_GAPS/CLOSURE-PASS; evaluator re-derived every figure read-only and found one new unguarded write path back into a cleared table.
- iter 20: CONTINUE — Stage E executed live and clean (16,592 forward-return rows filled on the 11 rebuilt runs); population (b) = 0 proven structurally correct.

## Do not redo

- **Stage D (iter-19), Stage E (iter-20), Stage F (iter-21) are DONE and live-verified** — never re-run, re-delete or re-regenerate. Evidence: `runs/goal-market-compass-iter-{19,20,21}/j11-stage-{d,e,f}-execute-*.json`.
- **The 11 rebuilt runs are frozen**: ids 3148–3158, identity `53d2ffd1…`, created 2026-08-26 10:52:55.552946 → 10:53:02.010362, 539–542/31/11 derived rows each, forward-return counts 2771 2769 2216 2215 1659 1658 1103 1103 549 549 + run 3158 = 0. Exactly 11 runs carry that identity. Never restamp or touch.
- **Cache dispositions are settled**: 5 tables emptied; `index_series_cache` stamp `d2026-08-12-c60699` re-derived EQUAL to live; `membership_timeline_cache` preserved (`append_forward = False`, 7 new dates all earlier than the cached 2026-08-12 tail). Do not re-classify — Stage G only VERIFIES.
- **Settled facts, do not re-derive or re-litigate:** goal.md step 5's premise that retained runs carry forward-return holes is FALSE for this codebase — population (b) = 0 is the CORRECT answer (iter-20). Stage-D attempt membership must come from run ids 3148–3158 + execution evidence, NEVER `engine_identity` alone (iter-19 auditor B1).
- **Do not touch the goal-mode framework during the recovery** (owner ruling); propose the `journey_history_hash` fix only AFTER Stage G. The owner's `--stall-window 12` override treats repeated journey hashes as a known false positive from J-11's multi-stage progress under one `partial` status.
- **Do not "fix" the deferred guard gaps now** (ruling item 5) — record them, keep the app off; hardening is post-Stage-G work.
