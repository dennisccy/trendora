# Iteration State — ops-hardening

**After iteration:** 77 · **Date:** 2026-08-13 · **Verdict:** ESCALATE

## Journeys

8 passing (J-01 J-03 J-04 J-05 J-06 J-07 J-08 J-09) · 0 failing · 0 unknown — 8 total; all re-verified this round; `evidence_makeup` on J-01 J-05 J-07 J-09 (capture/walkthrough only).

## Active blockers

- **Round 77 ended BLOCKED — closure gate FAIL** (`…-iter-77-closure-verdict.md`; `status.json` = `blocked`/`closure_failed`). Blocker 1 (dev): `…-iter-77-ui-test-results.md` still reads BLOCKED with J-04/J-07/J-09 "no test case executed"; the post-fix replay that PASSed all three sits unmerged at `reports/qa/goal-ops-hardening-iter-77-evidence/devfix-replay/replay-fast-results.md`. Re-merge or re-run, then re-run closure.
- **Blocker 2 is a harness false positive (human sign-off):** `scripts/automation/lib/closure_gate.py:72` greps `backend-only` and flags line 68 of `…-user-visible-changes.md`, a sentence DENYING such a gap.
- **iter-77/c (dev):** `apps/backend/tests/test_start_frontend_script.py:533` plants `apps/frontend/__tc3_intentionally_broken.ts` in the LIVE tree; an interrupted run leaves the frontend unbuildable and `scripts/start-frontend.sh` exits 1. Happened this round; not defended.
- **Human-owned, unanswered:** disable the evidence shortcut (`CHAIN_EVIDENCE_MICRO_PATH=false`) or accept an ESCALATE every round; cost sanction (20,207 s vs 3,600 s budget, 5.6×, 17th overrun); finish-now vs clear the 140 minor ledger notes; 2 s health-ceiling scope; B-1107; `browser-qa-phase.sh` sign-off.

## Last 2 verdicts

- iter 77: ESCALATE — code lane restored and all 8 journeys re-verified, but the round failed its own closure gate and only a full round can clear it (a CONTINUE would be demoted to evidence, no developer).
- iter 76: ESCALATE — two consecutive empty-diff rounds; SPEED-9 backstop named as the cause, ESCALATE used as the documented escape (it worked — iter-77 ran full with a developer).

## Do not redo

- **Shipped + verified this round:** `stale_for_s` "as of Ns ago" on badge/preflight banner; 1280×800 header wrap fix; `data-testid="scorecard-row-<h>d"`; `start-frontend.sh` build lock + `next.config.mjs` guard; demo recorder settle-for-capture fix.
- **Closed, do not re-plan:** stray `=` deleted; `state/goldens-regen-pending` empty; `/data` honest-fallback capture filed (`…-evidence/TC-8-data-fault-injection-honest-fallback.png`); iter-76/d; iter-76/e.
- **J-07 steps 3-4** carried from the 2026-07-31/iter-74 drill — valid while no backend runtime file changes; **J-08/J-09 deep database cross-check drills** run fresh at iters 75-76; do not repeat either.
- **Never regenerate the J-05..J-09 goldens**; do not touch `app.engine.readiness` cache/staleness logic or `compute_forward_aggregates` (frozen).
