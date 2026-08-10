# Iteration State — ops-hardening

**After iteration:** 56 · **Date:** 2026-08-10 · **Verdict:** ESCALATE

## Journeys

5 passing (J-01 J-03 J-04 J-08 J-09) · 3 partial (J-05 J-06 J-07) · 0 failing — 8 total

## Active blockers

- **The Data page lies during a job (dev, NEW, small, DO FIRST).** `availability_from_storage`
  (`data_manager.py:1676-1690`) serves an empty payload from the first bar an ingest commits until the
  finalize warm at the job's END, so `availability-heatmap.tsx:230-238` shows "No availability yet —
  Fetch real EOD prices" for ~20 min on a 3.3M-row DB. Serve the prior row with an as-of marker.
- **J-06's remaining two budget breaches (dev) — the ONLY things left in J-06.** `GET /api/health`
  0.16 s at rest / 241 ms in-browser vs a committed ≤0.1 s (still does DB work per call, noted since
  iter-54); `/api/stocks/AAPL/bars` last measured 6.2 s (Addendum 18), never re-measured.
- **The new J-06 golden is heading-only (dev, cheap).** `journey-scripts/J-06.json` = 11 `goto`+title
  steps; it asserts no budget, so it reports PASS forever without measuring anything.
- **`test_api_runs.py`'s full file never completed (dev)** — killed twice at 30+ min on `loaded_engine`; run it alone, early.
- **Availability ceiling (HUMAN — owner decision (a), open since iter-50).** J-07's per-compute-yield
  lever is evaluator-confirmed exhausted. Do not retry it.

## Last 2 verdicts

- iter 56: ESCALATE — lean run against its own `Depth: full` spec surfaced a cross-module defect no
  lane reported (the false "no data" heatmap its own fix introduced) plus a fail-open golden.
- iter 55: CONTINUE — honest-status fix verified 3 ways; no journey moved; TC-5 regressed 6→11.

## Do not redo

- **`/api/runs` N+1 fix DONE + verified** — `api/runs.py:38-44`, one `GROUP BY ScannerResult.run_id`;
  216-433 ms in-browser, `n_stocks` byte-identical across all 2,945 runs.
- **`/api/data/availability` ingest cache DONE + verified** — row read in sqlite (5,391 cells,
  `total_symbols=591`), 90 ms. Only its MISS *presentation* needs work (above).
- **J-05's golden date rotated + live-verified** — now targets 2010-11-10 (0 `scanner_runs` rows).
- **`forward_aggregates` completeness fix + intra-chunk GIL yield** settled (`data_manager.py:4300`,
  `forward_testing.py:1139`); the yield lever is exhausted, do not extend it.
- **AG-9/AG-10 re-verified** (all runs `provider='seed'`; both git checks empty on the 5 frozen paths;
  `config.yaml:1363-1364` = 8192 / 2); **lane-ordering rule held a 4th round**.
