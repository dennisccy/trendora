# Iteration State — ops-hardening

**After iteration:** 63 · **Date:** 2026-08-11 · **Verdict:** CONTINUE

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-08 J-09) · 1 partial (J-07 — availability met 983/983 HTTP 200, but
53 answers over the 2.0 s ceiling vs 1 last round; step 4 fault case not run for 4 rounds) — 8 total

## Active blockers

- **OWNER (15th round):** does the ≤2 s health ceiling apply to a 15-20 min background job, or only the
  "order ~30 s" window the amendment describes? J-07 cannot close without this sentence.
- **OWNER-gated:** `scripts/automation/browser-qa-phase.sh` line 286-before-272 fix (target journeys still
  never replayed on the FULL path); plus the cost of the replay lane's real 15-18 min ingest every round.
- **(dev)** The 1 → 53 health-latency change is UNATTRIBUTED (52 of 53 in `factor_lab_all_warm`, zero
  breaches there in the method-identical iter-61 drill). Control re-run on unchanged code comes first.
- **(dev)** `journey-scripts/J-05.json` still hand-rotated (now `2010-11-22`, verified fresh). Four rounds
  running the date was eaten by the round that set it — needs run-time date selection in the lane.
- **(dev)** Demo lane clicks Start after its own fills fail — launched a real 5-date backfill
  (`data_provider_runs` id=420) and narrated it as instant.

## Last 2 verdicts

- iter 63: CONTINUE — 7/7 required journeys replayed PASS with distinct fresh frames; J-07's DoD ("zero
  polls > 2.0 s") NOT met and its metric measured worse; coherence PASS, no critical anti-goal.
- iter 62: ESCALATE — a lean round surfaced verification-substrate defects (replay restart race, a golden
  consuming its own reserved date) that no lane reported.

## Do not redo

- The `time.sleep(0)` cooperative yield in `_missing_data_diagnostic` (`data_manager.py:325-331`) is DONE,
  byte-identity tested and profiled — do not re-guess the bottleneck; if more is needed, profile under
  live concurrent load and prefer `Result.partitions(size)` (audit B3).
- The replay-lane readiness gate `_wait_for_backend_readiness` EXISTS and fired live (`lib/common.sh`,
  `lib/replay-lane.sh`; `engine.log:10692-93`) — only its 60 s default needs raising.
- `data-overview-refresh.test.ts` header now documents `npx tsx …` (TC-6 verified, 3/3) — settled.
- J-05's golden is already rotated to `2010-11-22` — do NOT re-rotate by hand; fix the mechanism.
- iter-60/a (stale `/data` counts) is VOID — a UTC-vs-local misreading, not a defect. J-05 stays
  `passing` (real 18m13s backfill id=419 → `scanner_runs` id=2960 this round); do not re-open.
