# Iteration State — ops-hardening

**After iteration:** 69 · **Date:** 2026-08-12 · **Verdict:** ESCALATE

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-08 J-09) · 1 partial (J-07) — 8 total. Replay 8/8, zero overturns.

## Active blockers

- **Dev (the round's finding):** `GET /api/health` recomputes `compute_readiness` + `compute_preflight` on
  EVERY request (`apps/backend/app/api/health.py:128-184`) — dominant in all 74 answered breaches (43 / 31),
  ~256x / ~89x above idle at p90 while `factor_lab_all_warm` is live.
- **Human (owner), 21st round:** does the ≤2 s health-check ceiling apply to a 17-minute job, or only to the
  ~30 s job it was written for? J-07's last gap is exactly this (`docs/goal.md`, 2026-07-31 amendment). The
  session's FIRST 3 non-answers (5 s client timeout) landed this round, so the question got sharper.
- **Human (owner):** may `scripts/automation/*` change to arm the browser-QA lane's backend (iter-69/e, 4th
  round)? Plus the `browser-qa-phase.sh` sign-off and a cost sanction — 9th over-budget round (~6,988 s).

## Last 2 verdicts

- iter 69: ESCALATE — the sub-spans named the slow part as the health handler's OWN readiness+preflight
  work, so the next step becomes a design change to a canonical producer, not more measurement.
  Availability went backwards: 83 of 1,402 polls over 2 s and the session's first 3 non-answers.
- iter 68: CONTINUE — the third watchdog sample named 79.4 % of the one breach; 1,609/1,609 HTTP 200 but
  10 over 2.0 s, so J-07 stayed partial. `test_health.py` finally ran: 17 passed.

## Do not redo

- **Re-running a suspect compute chain in a STANDALONE script** — three null results (iter-52/53, 65, 66).
  Extend the live instrument instead: `apps/backend/app/engine/health_watchdog.py`.
- **A second health-poll counter, JSONL writer, or env flag** — `scripts/qa/poll_health.py`,
  `ledger.append_entry`, `TRENDORA_HEALTH_WATCHDOG` are canonical; both lanes shared the script again.
- **Re-proving flag on/off byte-identity** (`test_health_watchdog.py` 15 passed twice) **or re-deriving the
  pre-receive gap / watchdog write cost** (Addendum 35 TC-5 / TC-7 — iter-68/a, /b, /c closed).
- **RELEASED, not banned:** the "diagnostic only until the handler-body sub-timing names a component"
  condition on bounding `factor_lab_all_warm` is MET (`readiness_s` 43 of 74, `preflight_s` 31) — a
  legitimate alternative target if the health-handler fix proves insufficient.
- **Touching `config.yaml` caps, `project-extensions/host-guard/`, or the HOST-GUARD blocks in the launch
  scripts** — owner-set envelope (AG-10), verified clean again this round.
