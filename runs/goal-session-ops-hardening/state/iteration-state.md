# Iteration State — ops-hardening

**After iteration:** 47 · **Date:** 2026-08-04 · **Verdict:** ESCALATE

## Journeys

2 passing (J-08 J-09 — durability + evaluator live spot-check, NO lane row) · 5 partial (J-01 J-03
J-04 J-06 J-07) · 1 failing (J-05, 4th consecutive) — 8 total. **No journey was verified by any lane
against the shipped build**; the only browser artifact reads BLOCKED, zero rows for J-06 and J-07.

## Active blockers

- **Re-run browser-qa BEFORE any new code** (dev): lane ran 13:05-14:21Z, then code changed 15:00
  (`research.py`), 15:03 + 16:50 (`forward_testing.py`). `status.json` blocked / `next_action:
  browser_qa`; closure CLOSURE-FAIL. Services up and healthy. **No owner blockers.**
- **Five rebuilt goldens never executed** (dev): `journey-scripts/{J-01,J-03,J-05,J-08,J-09}.json`
  (15:46-16:05). J-04 + J-07 retired to `retired-journey-scripts/`, need the LLM lane.
- **J-05's rebuilt golden decays into a null test after one productive run** (dev): add the audit's
  `"1 snapshots"` assertion (`app/data/page.tsx:2785`) BEFORE running it.
- **J-05's real defect** (dev): snapshot written in ~12 s, then the finalize tail runs for minutes and
  the run row never leaves `running`. 4 rounds failing; the only product fault left.
- **`/research/regime-lab` hits the 8192 MB cap on one request** (dev): `research.py:3552`
  (iter-33/g, 13x deferred); starved the boot warm at 3/7 claims ~20 min.

## Last 2 verdicts

- iter 47: ESCALATE — J-05 failed a 4th round; the mandatory lane never re-ran, so the round's real
  win (Evidence page 163 s → 0.012 s) has no journey-level proof.
- iter 46: ESCALATE — J-05 failing 3 rounds; the browser lane predated the shipped build.

## Do not redo

- **Evidence-page cache thrash FIXED** (iter-46/av): `/api/evidence` 0.012 s live; serve-stale behind
  `expectations_status:"refreshing"` (`forward_testing.py:2694-2748`); byte-identity SHA-256-proven.
- **`samples.py` decile branch BOUNDED** (`_factor_decile_observations`, 5/5 pressure runs); STILL
  OPEN `samples.py:161`/`:168`. **`warmup.py:205`/`:212` guarded**; **date filter done** (TC-5).
- **Duplicate re-warm vs BOOT warm fixed** (audit B1, mutation-verified) — NOT fixed vs the ingest
  finalize tail (audit B2: one process-wide sentinel). **AG-10 caps intact, never re-tune.**
- **Replay goldens were NULL TESTS session-wide** (J-08's had ONE step) — never score a replay PASS
  without reading the script. Capture-only: J-07 `[NEW]` walkthrough, J-05 frames.
