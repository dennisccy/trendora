# Iteration State — ops-hardening

**After iteration:** 11 · **Date:** 2026-07-22 · **Verdict:** ESCALATE

## Journeys

4 passing (J-01 J-03 J-04 J-05) · 1 partial (J-06 — target, 3 gaps) · 0 failing — 5 total.

## Active blockers

- **AG-8 critical, UNRESOLVED — OWNER call, hard-blocks GOAL_ACHIEVED.** `forward_aggregates_cached` →
  `compute_forward_aggregates` does an unbounded `ScannerResult` load (`forward_testing.py:826`) and OOMs
  under the 6144 MB cap. FIRED LIVE iter-11: ingest-warm aborts (`logs/backend.log:27185`, `:27233`) + two
  on-load 500s (`:27601` `/api/methodology`, `:27660` `/api/research/event-study`); health held 200, self-
  recovered. Owner: bounded fix, amendment, or formal deferral — plus `HOST_GUARD_REQUIRE_MARKERS` and the
  `[NEW] demo.sh --session-live` walkthroughs (J-06 Acceptance names one).
- **J-06 G1 (dev).** The 11-page sweep numbers never reached `reports/perf-budgets.md` (mtime 20:24Z, sweep
  20:38–20:52Z). Transcribe from `…iter-11-evidence/UT-J-06-perf-sweep-summary.txt`, incl. both WARNs.
- **J-06 G2 (dev).** `/api/indexes?full=true` on `/data`: 2066.3 ms & 2671.8 ms vs ≤1.5 s; the 4.7 ms "clean"
  re-read is a different call pattern, not a control. Re-measure cache-disabled ×3, quiet host, no ingest.
- **Environment (operator).** Backend/frontend DOWN — nothing on :8255/:3255; `logs/backend.log` ends
  `INFO: Shutting down`. Restart before the next browser lane.

## Last 2 verdicts

- iter 11: ESCALATE — J-06 stayed `partial`; the lean lanes mis-read a live per-process memory exhaustion
  (two user-facing 500s) as ambient host load → full-pipeline auditor/closure gates needed.
- iter 10: CONTINUE — J-04 partial→passing on a live rendered-surface read of run 119's `interrupted` row.

## Do not redo
- **iter-11 product diff is EMPTY** (scan-report CLEAN, `iter-diff.md` "(no changes)", coherence-verified).
- **Boot budget DONE** — 1.364 s, host-guard launcher, `perf-budgets.md` TC-3 (closes iter-10's J-04 caveat).
  **AG-10 RESOLVED both sides** (banner `logs/backend.log:27068`; iter-11 pytest under `taskset -c 0-3,8-11`
  /BLAS=4, hwmon peak 88 °C). **J-04 step 6 CLOSED** (`data_manager.py:3677-3712`) — no new crash cycle.
- **TC-4 audit exists** (`perf-budgets.md`, 4 rows, file:line) but "no violation found" is INCOMPLETE — it
  audited cache-HIT paths only. Re-open the MISS/compute path; do not redo the HIT tables.
- **Heavy-ingest test settled, do NOT re-run** (iter-9: 1092.93 s, 439/439 health-200, 24.7 % under cap).
  **Do NOT touch** `health.py`, `readiness.py`, `main.py` boot, `warmup.py`, `max_range_days`, the
  `/evidence` drawdown warm, `server.memory_cap_mb` (supersedes iter-10's "/api/indexes in budget" — G2).
  **Process:** never hand-edit past artifacts; never patch `scripts/automation/*`.
