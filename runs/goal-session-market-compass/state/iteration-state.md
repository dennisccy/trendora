# Iteration State — market-compass

**After iteration:** 8 · **Date:** 2026-08-21 · **Verdict:** CONTINUE

## Journeys

2 passing (J-01 J-04, carried on iter-4 evidence, NOT re-verified) · 6 partial (J-02 J-03 J-05 J-06 J-09 J-10) · 2 failing (J-07 J-08) · 1 unknown (J-11, new owner insert) — 11 total

## Active blockers

- **Forbidden lane runs at BOTH depths — fix FIRST, before any DB write.** The J-01/J-04 deterministic replay ran twice this iteration (lean 01:40, then full 12:54), starting a frontend + backend on the host that froze 2026-08-20 and overwriting AG-17-protected evidence. Depth-arbiter fix `046dd956` did NOT close it (audit P2). Owner: dev, `incredible_auto_dev/scripts/automation/`; required by `docs/goal.md` J-11 step 10.
- **J-10 incomplete at 20/587.** Owner amendment (steps 2b/2c/2d) authorises continuing: judge the
  remaining 567 one-by-one under the same fixed gate; skip the restored 20 idempotently; no
  population-level pass; no invented "enough" threshold. Owner: dev, `apps/backend/app/engine/j10_recovery.py`.
- **Owner-only:** `docs/goal.md` J-10 "Recorded finding" credits Stooq for prices Yahoo supplied — the
  gate compared Yahoo vs Yahoo. Needs the owner's pen.
- **Lane gate stays shut** until J-11 Stage G: no browser/replay/research/proposer lane on J-01–J-08.
  Carried non-blocking owner questions: J-09 3.44 GB · J-06 wording · J-01 test steps · empty focus
  section · MNST inclusion.

## Last 2 verdicts

- iter 8: CONTINUE — first real restoration (40 rows, 20/587) through a correctly fail-closed gate;
  J-10 still incomplete per the owner's Completion rule; AG-17 breached and fixed in-lane.
- iter 7: CONTINUE — gate built and correctly refused to write; auditor found and fixed a critical
  fail-open before it touched real data.

## Do not redo

- **Do NOT restart recovery or delete the restored 20 symbols** — 40 rows on 2026-08-11/12 are valid;
  continue from 20/587 (`docs/goal.md` J-10 step 2d).
- **Do NOT re-derive `RECOVERY_SYMBOLS` (587, MNST excluded) or `RECOVERY_SOURCE` ("yahoo")** — settled.
- **Do NOT weaken or skip the convention gate** — the 1.0 bridge factors are same-vendor, explicitly NOT grounds for removing it (`docs/goal.md` J-10 Acceptance).
- **B1/B2/B3/B5/B6 audit fixes are DONE** (min-evidence floor, one-series end-to-end, persisted per-pair evidence, non-overridable thresholds, authorized-date assertion) — do not regress; DO add the 3 remaining gaps: mandatory `evidence_path`, `fetch_provider` guard, un-gated fetch back door.
- **J-11 may NOT start** before J-10 reaches its accepted terminal state (`docs/goal.md` hard gate).
