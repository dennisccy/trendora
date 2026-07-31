# Iteration State — ops-hardening

**After iteration:** 41 · **Date:** 2026-07-31 · **Verdict:** ESCALATE

## Journeys

6 passing (J-01 J-03 J-04 J-06 J-08 J-09) · 1 partial (J-07) · 1 unknown (J-05) — 8 total

## Active blockers

- **TOP — target journeys get NO verification.** Coverage gates key off the spec's
  `Required-still-passing journeys:` line only, so iter-41 headlined `PASS 6/6` while J-05 and J-07
  had zero rows. Fix BOTH halves: a `UT-J-XX` case for targets on backend-only specs
  (`agents/ui-test-designer/body.md`) AND extend `merge_ui_test_results.py`'s guard to them. Dev.
- **2nd — J-05 `unknown`, LESS proof than at iter-39.** Replay via the existing
  `runs/goal-session-ops-hardening/journey-scripts/J-05.json` (and `J-07.json`). Owner: dev.
- **3rd — "no whole-table load" undecided after 12 iterations (iter-29/d).** `_BarCache.prefill` is
  51.5% cheaper/row, still whole-table resident: bound it OR amend goal.md to a per-row budget. Dev.
- **OWNER (blocks any achievement run):** iter-34/j — `/api/health` ≤ 0.1 s budget missed an 8th time
  (58 polls, max 1.73 s): ratify honest-WARN, rescope for the background window, or commission the
  cached-readiness fix. iter-33/i — `start-frontend.sh` → `HOST_GUARD_MARKER_FILES`?

## Last 2 verdicts

- iter 41: ESCALATE — verification lane genuinely repaired (6 fresh replay rows + screenshots; J-01,
  J-04, J-06 recovered from `unknown`), but J-07 missed `passing` a 7th time and the audit caught a
  CRITICAL that review + QA both passed (5th consecutive audit-only catch).
- iter 40: ESCALATE — seven required journeys shipped with ZERO evidence; only the auditor caught it.

## Do not redo

- **Required-still-passing verification lane FIXED and proven** (iter-40/y resolved): shell-gate
  carve-outs + `resolve_backend_health_url` in `common.sh` + `ui-test-designer` rewrite. Targets left.
- **All-SKIP + missing-row merge guard DONE with tests** (`merge_ui_test_results.py`; `BLOCKED` in
  `verdicts.py`, `goal_gate.py`, `closure_gate.py`, 4 grep sites in `goal-iter-lean.sh`).
- **`_BarCache.prefill` columnar rewrite DONE, byte-identity-proven** — open question is the BOUND.
- **Checkpoint count floor (D9), `faulthandler` SIGUSR1 (C7), post-terminal polling (C8) DONE.** Never
  retune `server.memory_cap_mb`.
- **iter-33/g (Regime Lab cold `view=pooled`) deferred 6 times — deferred, not forgotten.** J-07's
  `[NEW]` walkthrough is capture-only, never an iteration's goal (11 rounds unrecorded).
