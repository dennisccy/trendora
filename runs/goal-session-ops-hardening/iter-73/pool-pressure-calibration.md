# iter-73 — pool-pressure worker-count calibration (developer pass, 2026-08-13)

TC-1 requires a "realistic number of simultaneous DB-connection-holding requests materially closer to the
68-connection ceiling than a handful" run concurrently with the deep-basis forward-aggregate warm. Before
committing the full ~20-30 minute live drill, this session ran short (45-90s) calibration passes on this
same host to find a worker count that (a) meaningfully exceeds "a handful" and (b) does not itself break
`GET /api/health`/job-status responsiveness — a DoD requirement independent of the memory question TC-1
targets. Scripts used (scratchpad, not committed — throwaway calibration tooling, not the actual test):
`calibrate_pressure.py` (no job) and `calibrate_pressure_with_job.py` (real `rebuild` job running
concurrently). Both against a throwaway copy of the real committed dev DB, via `scripts/start-backend.sh`
(AG-10 caps applied).

## Pass 1 — pressure workers ALONE, no heavy job running

| Workers | Endpoints | Pacing | Window | Pressure non-200 | Health non-200 |
|---|---|---|---|---|---|
| 15 | backtest/watchlist/sectors/themes | 0.5-1.0s | 45s | 0/747 | 0/42 |
| 24 | + stocks + data/availability | 0.4-0.8s | 50s | 0/1526 | 0/48 |

Clean at both levels — the pressure load alone, without a concurrent CPU-bound job, is well within this
host's capacity even at 24 workers on all 6 endpoints.

## Pass 2 — pressure workers CONCURRENT WITH a real `rebuild` job (2024-01-01/2024-01-01), 90s window each

| Workers | Pacing | Pressure requests / non-200 | Health polls / non-200 | Job-status polls / non-200 |
|---|---|---|---|---|
| 10 | 0.5-1.0s | 340 / 36 | 88 / **0** | 43 / **0** |
| 13 | 0.6-1.2s | 410 / 46 | 80 / **1** (1 timeout) | 40 / **1** (1 disconnect) |
| 16 | 0.5-1.0s | 519 / 60 | 69 / **10** (timeouts + HTTP 503) | 34 / **5** |
| 24 | 0.4-0.8s | 1433 / 673 | 70 / **29** (timeouts + HTTP 503) | 34 / **14** |

The failure mode at 16+ workers is a mix of plain `httpx.ReadTimeout` (server too CPU-starved on this
4-core sandboxed host to answer within 10s) and genuine HTTP 503 "Exceeded concurrency limit" responses —
the SAME already-disclosed admission-control finding `reports/perf-budgets.md` Addendum 37 recorded,
triggered here by this round's OWN concurrency-generating load rather than an extra polling loop. This is
a DISTINCT, host-CPU-bound finding from the DB-pool/memory question TC-1 targets (per TC-8, never
conflated with it).

## Decision

`_POOL_PRESSURE_WORKERS = 10` (pacing 0.5-1.0s jittered, all 6 endpoints) is the largest calibrated worker
count that keeps `GET /api/health` and the job-status poll perfectly clean under a REAL concurrent heavy
job on this host — the binding DoD requirement ("zero health non-answers... on the SAME drill") takes
precedence over reaching literally as close to 68 as possible. 10 is still a >3x increase over the "a
handful" (2-3) connections iter-72's own drill exercised, sustained for the whole warm across a diverse
endpoint mix. Going higher (13+) was tried and found to break the health/job-status requirement on this
specific sandboxed host — reported here honestly per the iteration spec's own NOTES ("the goal is a
trustworthy measurement, not a clean-looking one") rather than silently discarded.
