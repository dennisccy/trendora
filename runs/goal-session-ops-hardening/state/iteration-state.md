# Iteration State — ops-hardening

**After iteration:** 43 · **Date:** 2026-08-03 · **Verdict:** ESCALATE

## Journeys

6 passing (J-01 J-03 J-04 J-06 J-08 J-09) · 1 partial (J-05) · 1 failing (J-07) — 8 total

## Active blockers

- **dev — J-07: a stuck heavy calculation takes the whole app offline.** No shutdown deadline on the
  web server (`incredible_auto_dev/scripts/start-backend.sh:95`): one frozen job (`horizons_done: 0/5`
  after 137 s) left the port refusing connections for minutes, needing a hard kill — with 67.6% memory
  free, so a stall, not exhaustion.
- **dev — J-07: health checks too slow during heavy work.** 173 of 272 polls over the owner's new 2 s
  ceiling, worst 6.6 s, worsening. Suspect `_SymbolColumns` per-call slicing
  (`apps/backend/app/engine/prices.py`); the revert widened its exposure 548 → 591 symbols.
- **dev — J-05 has never been tested on a genuinely new day.** Every run used an already-snapshotted
  date (0 snapshots created); the one real attempt ran 1,001 s without finishing.
- **No owner/human blockers outstanding** — iter-33/i and iter-34/j both closed this iteration.

## Last 2 verdicts

- iter 43: ESCALATE — J-07 failed a 2nd consecutive round (total outage + health latency); for the
  7th round running only the audit lane caught the load-bearing defect, and a lean round has no auditor.
- iter 42: REGRESSION — J-05 broke (jobs accepted then never started) and J-07 went down under the
  then-6144 MB ceiling; halted for the owner's memory decision, which has since landed.

## Do not redo

- **Memory cap raise 6144 → 8192 is DONE and PROVEN** (owner commit `1376601c`): the post-revert warm
  held flat at 32.4% of cap for 1,001 s. Never re-tune `config.yaml` / `host-guard.env` caps.
- **iter-42's `_BarCache.prefill` symbol filter is REVERTED** (`app/engine/prices.py`), oracle-tested,
  `KeyError` publish-race fix preserved. No sixth prefill-bound attempt — "compression, not a bound".
- **Job-launch honesty is DONE** — `start_data_job`/`start_resume_job` catch `Exception`, record
  `failed` + message, re-raise; `api/data.py` returns 503 (covers `RuntimeError` AND `MemoryError`).
- **`start-frontend.sh` host-guard is DONE** — block at `:28-58`; `host-guard.env:89` lists all three
  launchers (owner item iter-33/i closed).
- **`/api/health` budget rescope SETTLED** (steady-state ≤0.1 s; ≤2 s in a bounded compute window) —
  meet it, do not re-litigate it. **iter-33/g deferred 9×; J-07's `[NEW]` walkthrough and J-05's
  acceptance frames are capture-only, never a round's goal.**
