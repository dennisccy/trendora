# Iteration State — market-compass

**After iteration:** 23 · **Date:** 2026-08-27 · **Verdict:** STALLED

## Journeys

4 passing (J-01 J-04 J-10 **J-11 new**) · 5 partial (J-02 J-03 J-05 J-06 J-09) · 2 failing (J-07 J-08) — 11 total

## Active blockers

- **HUMAN — owner decision required before ANY next iteration.** The replay lane booted and wrote to the
  protected canonical DB (`scripts/automation/goal-iter-lean.sh:256-257` starts `scripts/start-backend.sh`
  with no `TRENDORA_CONFIG`). 10 rows in 5 derived caches of `apps/backend/data/trendora.db`; zero
  canonical-data change. Owner must rule: (1) leave or remove those rows; (2) authorise the launcher fix
  (ruling items 7/9 defer tooling work); (3) confirm J-11 closure. Unresolved-critical in
  `state/journey-history.json`.
- **Plan no browser iteration until (2) is done** — every iteration re-tests the passing set, which is the
  lane that boots the canonical DB; a request for a manifest-less date would mint a manifest there.
- Non-blocking: delete the 7.8 GB clone at `runs/goal-market-compass-iter-23/verify-clone/`; J-02/J-03
  repaired-state replay never run; J-04 capture crops above the candidate card (`evidence_makeup`).

## Last 2 verdicts

- iter 23: STALLED — J-11's clone-backed serving verification PASSED and J-11 closes, but the same run
  silently booted and wrote to the protected canonical database; every fix path needs the owner.
- iter 22: STALLED — Stage G passed at the database level; the serving check was still owed and only the
  owner could authorise restarting the app.

## Do not redo

- **J-11 is CLOSED** — `J-11 SERVING/REPLAY VERIFICATION: PASS` / `J-11 STATUS: PASSING` (ruling item 8).
  Stages D–G and the clone-backed serving check are DONE; do not reopen or re-verify.
- **Clone tooling exists and works**: `app/engine/j11_disposable_clone.py`,
  `apps/backend/scripts/run_j11_disposable_clone.py`, `scripts/start-backend-j11-verify.sh` (the guard that
  correctly refuses a canonical boot), 27 passing tests. Reuse it; do not rebuild it.
- **Canonical integrity re-proven live (iter-23)**: 24 manifests field-identical, all
  `prospective_eligible: 0`, 0 manifests for the 7 manifest-less incident dates, runs 3148–3158 intact,
  `daily_prices` 3,310,374 rows / ohlcv_sum 52,367,098,848,872.56. Do not re-audit.
- **`/market` 404 is a J-08 gap, not a J-11 defect**; **a `.db` sha256 does NOT prove a WAL-mode SQLite DB
  unchanged** (bracket `.db`+`-wal`+`-shm`). Spec depth was `full`, dispatch ran `lean` — request full.
