# Iteration State — ops-hardening

**After iteration:** 4 · **Date:** 2026-07-20 · **Verdict:** CONTINUE

## Journeys

4 passing (J-01 J-03 J-04 J-05) · 1 failing (J-06) — 5 total

## Active blockers

- none blocking. Next target: **J-06** ("Pages load only what they need" — measurement
  capstone, last failing journey), dev-owned, no human blocker.
- Closure-gate item (not blocking now): J-05 + J-06 `[NEW]` `demo.sh --session-live`
  walkthrough bullets are deferred showcase artifacts — produce both (or human accepts
  deferral) before the final GOAL_ACHIEVED gate. See assumptions.md.
- Reporting defect (not product): `merge_ui_test_results.py` drops the browser-qa `## Notes`
  section + mis-sums the header — read the `.llm.md` raw file, not the merged one.

## Last 2 verdicts

- iter 4: CONTINUE — J-05 partial→passing; B3 (false "Backend unavailable" on ordinary fetch)
  + F1 (frozen finalize heartbeat) fixed and live-verified across all lanes; J-06 last failing.
- iter 3: CONTINUE — J-05 stayed partial; B1/B2 backend correct but browser story blocked by
  B3/F1 + a skipped cold-boot check (all closed this iter).

## Do not redo

- B3 fix: readiness servability is benchmark-scoped (`_latest_benchmark_bar_date`, one indexed
  per-symbol query) + 4th `awaiting_snapshot` state + `readiness_detail` field — readiness.py /
  health.py / api.ts / health-badge.tsx. Do NOT revert to whole-table `latest_data_date`.
- F1 fix: bare `prog.tick()` in BOTH finalize per-date loops (coverage + market-phase) in
  data_manager.py `_refresh_ingest_aggregates` / `_persist_per_date_coverage_snapshots`.
- J-05 backend (iter-2/3): `coverage_snapshot` table + ingest finalize hooks + fetch/expand
  finalize gate + `aggregates_refreshed` nullability — settled, do not touch.
- Cold-boot check (UT-08) now executed; literal "all-zero DB" precondition is architecturally
  unreachable (main.py lifespan seeds before serving) — don't re-chase that framing.
- start-backend.sh memory-cap / malloc-arena / logfile enforcement (iter-2) — done.
- `ensure_latest_snapshot` + boot warm-up loop — left unchanged by design; dormant vs offline seed.
