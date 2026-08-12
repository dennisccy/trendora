# Iteration State — ops-hardening

**After iteration:** 71 · **Date:** 2026-08-12 · **Verdict:** ESCALATE

## Journeys

6 passing (J-01 J-03 J-04 J-06 J-08 J-09) · 1 partial (J-05) · 1 failing (J-07) — 8 total. All 8 checked live this round; `pending_infra` cleared on every one.

## Active blockers

- **J-07 + J-05 step 4 — the app stopped answering `/api/health` 58 of 900 times during a heavy job (longest gap 165 s) and served one 500.** Owner: dev. Cause found in the round's real log: `QueuePool limit of size 10 overflow 20 reached` (`config.yaml:119-122` pool 30 vs `server.limit_concurrency` 64).
- **The measurement is not conforming.** It ran on `scripts/dev.sh`, which omits `--limit-concurrency` (`scripts/dev.sh:85-88` vs `scripts/start-backend.sh:107`). J-04/J-06 say "never dev.sh". Owner: dev — re-measure on `scripts/start-backend.sh` FIRST.
- **Suspect in this round's own change:** `readiness.py` `_tick_and_cache` recomputes with no post-lock recheck, so past 1.5 s staleness every request computes serially behind `_TICK_LOCK`. Owner: dev.
- **Owner-owned, 23rd round:** (a) keep the 2 s health promise for long jobs or apply it to short jobs only; (b) may we bound how many heavy computes run at once (card B-1107 — it is what bit); (c) sign-off on `scripts/automation/browser-qa-phase.sh`; (d) cost sanction (11th over-budget round, 2.9x).

## Last 2 verdicts

- iter 71: ESCALATE — six journeys newly passing, but the first measured multi-minute outage of the session, with a root cause spanning the DB pool, the ingest warm, J-09's dispatch and the launcher.
- iter 70: CONTINUE — the readiness cache fixed the breaches (0 of 1,030), but the QA backend died mid-round so nothing was journey-checked.

## Do not redo

- **Readiness/preflight background-refresh cache + staleness bound: DONE.** `readiness.py:127,165-194`, `config.yaml:1348-1349` (`refresh_interval_seconds` 0.5, `max_stale_intervals` 3), `health.py:174,208` (`cached = None`, `stale_for_s`). Reviewer PASS, coherence PASS, iter-70/d closed. Do not re-instrument `readiness_s`/`preflight_s` — proven near-zero.
- **Rendering `stale_for_s` in the UI: deliberately deferred**, not forgotten — it would be this cycle's first user-visible UI change (goal.md Loop Mechanics ties that to full depth). Next round IS full, so it may ship if scoped.
- **J-07 steps 3 (VmPeak) and 4 (memory-pressure abort): carry forward on evidence durability** — warm-path code byte-unchanged; do not re-run those drills.
- **AG-10 envelope (`config.yaml` caps, `project-extensions/host-guard/`, HOST-GUARD script blocks): untouched, owner-set.** Verified clean this round. Do not edit.
- **`scripts/automation/*` stays owner-gated** — the `browser-qa-phase.sh` ordering bug is still awaiting sign-off; do not edit it unprompted.
- **The Regime Lab (iter-33/g) is deferred** — 37th round; not scope.
