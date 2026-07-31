# Phase goal-ops-hardening-iter-42 — UI Test Results

**Phase:** goal-ops-hardening-iter-42
**Date:** 2026-07-31
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: both P1 target-journey tests executed this run (UT-J-05, UT-J-07) FAILED with live,
     reproduced-today backend evidence (stuck ingest job; MemoryError/thread-exhaustion crash
     cascade; /api/health and /backtest returning HTTP 500 then becoming fully unresponsive). -->

**Overall:** 0/2 tests passed (0 skipped) — this run's scope

**Scope note:** Per the dispatch's goal-mode regression-lane instructions, J-01/J-03/J-04/J-06/J-08/J-09
were ALREADY re-verified this iteration via deterministic golden-script replay before this dispatch
started (evidence: `reports/qa/goal-ops-hardening-iter-42-evidence/J-01-verify.png` …
`J-09-verify.png`, timestamped 07:32–07:34) and are explicitly out of this agent's scope — no rows
for them are emitted here; their rows merge in automatically. This report covers ONLY the two
**target journeys** this iteration's own spec exists to guarantee fresh verification for: **UT-J-05**
and **UT-J-07** (`docs/phases/goal-ops-hardening-iter-42.md` DoD items 2–3, TC-3/TC-4/TC-5).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | Aggregates precomputed at ingest, never on the fly (target) | regression | P1 | Single-day backfill job accepted, reaches a terminal status, badge stays "Ready" throughout, `/scanner-runs` shows the new date with a populated leaderboard | Job accepted correctly, badge stayed "Ready" — but the job NEVER left `status:"running"` (`dates_done` stuck at 0/1, `last_progress_at` frozen at its own start timestamp) for the full ~10 min observed; a second, independent job on a different date reproduced the same zero-progress stall; the backend then became fully unresponsive, blocking any further steps | FAIL | `reports/qa/goal-ops-hardening-iter-42-evidence/UT-J-05-fail.png` (+ raw job-status JSON quoted in Failed Tests below) |
| UT-J-07 | Heavy aggregate warm never takes health/`/backtest` down (target) | regression | P1 | `GET /api/health` returns 200 for the whole 60+s warm window; `/backtest` shows real values or the "Refreshing" banner, never down | First 76s of polling during the live warm: 34/34 = 200 (clean). But the SAME warm window later crashed (`background_compute` outcome `"failed"`, `MemoryError` in `forward_aggregates_ingest_cached`/`compute_drawdown_expectations_cached`, `RuntimeError: can't start new thread`), producing real HTTP 500s on `/api/health` (3×), `/api/backtest` (2×), `/api/stocks`, `/api/themes`, `/api/runs`, `/api/methodology`; `/backtest` and `/data` both rendered "Backend unavailable"; `/api/health` then went fully unresponsive (5 consecutive timeouts, HTTP code 000, 10–30s each) for several minutes | FAIL | `reports/qa/goal-ops-hardening-iter-42-evidence/UT-J-07-fail.png` (+ backend log excerpts quoted below) |

---

## Passed Tests

None this run.

---

## Failed Tests

### UT-J-05 — Aggregates precomputed at ingest, never on the fly (target journey)

**Verdict:** FAIL
**Evidence:** `reports/qa/goal-ops-hardening-iter-42-evidence/UT-J-05-fail.png` (screenshot capture
returned a solid blank frame at the moment of capture — verified via `document.body.innerText` that
the DOM itself held its full ~84KB of real page text at that same moment, so this is a renderer-paint
symptom coincident with severe host resource pressure — see UT-J-07 below for the concrete crash
evidence — not a claim of an application-level blank page. The stuck-job state itself is evidenced by
the raw API JSON quoted below, which is unambiguous.)

**Steps taken:**
1. Navigated to `/scanner-runs`; confirmed extensive existing coverage (1919 runs, contiguous
   2026-04-01…2026-07-22 plus older ranges) and picked `2023-01-05` — confirmed NOT already listed
   (`2023-01-05` absent from the full `/api/runs?limit=5000` date set fetched directly).
2. Navigated to `/data`; set both "Start date" and "End date" (`data-testid="job-start-date"` /
   `job-end-date`) to `2023-01-05`.
3. Confirmed "Job kind" (`aria-label="Job kind"`) read "Backfill snapshots" — the default, unchanged.
4. Clicked "Start". Job accepted immediately: `job-status` flipped to `"running"`; readiness badge
   (`data-testid="readiness-badge"`) stayed `data-state="ready"` / text "Ready" — matches Step 6's
   acceptance.
5. Polled the job (`GET /api/data/jobs/cbf08538775d486faac7b8e0b4008715`) repeatedly over ~10 minutes:

   | Check time (UTC) | status | dates_done | last_progress_at |
   |---|---|---|---|
   | 06:40:53 (start) | running | 0/1 | 06:40:53.096 |
   | 06:44:58 | running | 0/1 | 06:40:53.096 (unchanged) |
   | 06:48:14 | running | 0/1 | 06:40:53.096 (unchanged) |
   | 06:49:39 | running | 0/1 | 06:40:53.096 (unchanged) |
   | 06:50:38 | running | 0/1 | 06:40:53.096 (unchanged) |

   `symbols_total`/`symbols_ok`/`bars_fetched` remained `0` throughout — not merely slow, genuinely
   zero forward progress for the entire observed window, spanning both a period when a concurrent
   background-compute window was active (06:33:56–06:46:53 UTC) AND ~4 more minutes after that window
   had already finished/failed and the system was otherwise idle (`background_compute.active: []`).
6. To rule out "this one job/date is a fluke," started a SECOND, independent single-day backfill
   (`2023-02-14`, confirmed unsnapshotted; job_id `8ef1cdd470344e4084dd327f62446170`) once the system
   showed no active background compute. Job accepted, badge stayed "Ready." Polled again:
   - 06:51:52 (start): running, 0/1, `last_progress_at` = 06:51:52.327
   - 06:52:49 (57s later): running, 0/1, unchanged
   - By the time of a later browser check the panel read **"updated 5m 47s ago · possibly stalled"**
     (`data-testid="job-heartbeat"` / `job-live-activity`) — same zero-progress pattern reproduced
     independently, on a different date, with no contention from another background-compute window.
7. Shortly after job 2 stalled, the backend became fully unresponsive (see UT-J-07 evidence below),
   which prevented observing either job's eventual fate, and made Steps 8–9 (Refreshed: text,
   `/scanner-runs` listing) and Steps 10–11 (cold-restart log check) unreachable this session.

**Expected:** "The job reaches a terminal status (not stuck on running indefinitely)."

**Actual:** Neither of two independently-started single-day backfill jobs left `status:"running"` or
showed ANY forward progress (`dates_done`, `symbols_ok`, `bars_fetched` all stayed at `0`) for the
entire observed window (~10 min for job 1, ~6+ min for job 2 before the backend itself stopped
responding). This directly contradicts the acceptance criterion.

**Steps not reached (backend restart, out of this agent's scope regardless):** Steps 10–11
("restart the backend via `scripts/start-backend.sh`, tail `logs/backend.log`") were not attempted —
restarting/debugging the backend is outside browser-qa-agent's hard rules ("never restart the app").
That specific sub-check is properly backend/dev-measurement scope; `reports/perf-budgets.md`'s
"Iteration 42" section (developer's own TC-4/TC-6/T2 measurements, read for this report) already
documents the shipped `prefill` symbol-filter is live and does not do a full 3.3M-row scan on a cold
`/data` load, while also honestly disclosing the bound is "modest… not a fundamental
order-of-magnitude fix" and that `_SymbolColumns` reads are "~70–80× slower per call" (T2, unfixed)
— the live stall and crash observed above in this browser session are consistent with, and appear to
be a direct live manifestation of, that same dev-acknowledged, unfixed regression.

---

### UT-J-07 — Heavy aggregate warm never takes the health endpoint or `/backtest` down (target journey)

**Verdict:** FAIL
**Evidence:** `reports/qa/goal-ops-hardening-iter-42-evidence/UT-J-07-fail.png` (`/backtest` showing
"Backend unavailable" with the badge still reading "Ready" and "background compute running (1)")

**Deviation from the literal script (disclosed):** rather than launching a brand-new wide
(2025-06-01→2026-07-17) backfill myself, I used a heavy forward-aggregate warm that was ALREADY
live-running when this session started (`background_compute.active`: `asof_key=2026-07-21`,
`dataset_version=r1919-f4017590`, started 06:33:56 UTC) — chosen deliberately given this host's
documented history of hardware resets under concurrent heavy compute (goal.md AG-10 background) and
to avoid stacking a second self-triggered heavy job on top of one already running. This substitution
exercises the exact same acceptance surface (health polling + `/backtest` during a live warm) with
genuine live evidence.

**Steps taken:**
1. Confirmed via `GET /api/health` that `background_compute.active` held a real, in-progress
   forward-aggregate warm (elapsed growing across repeated checks: 49.6s → 214.8s → 481.6s →
   662.9s, `horizons_done` 1→2 of 5).
2. Polled `GET /api/health` once per ~2.3s for 76 seconds (06:37:45–06:39:01 UTC) while that warm ran:
   **34/34 polls returned HTTP 200, zero failures** — this window, taken alone, PASSES Step 4's literal
   bar.
3. In parallel, checked the readiness badge on `/`: `data-state="ready"`, text "Ready" — matches
   Step 5.
4. Navigated to `/backtest`: page text included `"Refreshing — showing the last complete evidence…
   evidence as of 2026-07-22, generated 2026-07-30 13:33:40"` and `"background compute running (1)"`
   — the sanctioned degraded-but-honest state, matching Step 6's acceptance (captured via page-text
   extraction, not a screenshot, at this specific moment).
5. Continued observing. The active background-compute window ran a total of 776,726 ms (~13 min) and
   then **finished with `"outcome":"failed"`** (`GET /api/health`'s `background_compute.recent_outcomes`,
   `started_at`=06:33:56, `finished_at`=06:46:53 UTC). Its tail end coincided with a burst of backend
   errors — confirmed by direct inspection of `logs/backend.log` (absolute paths, timestamps in the
   file's local clock, UTC+1 relative to the API's UTC timestamps):
   ```
   2026-07-31 07:46:52,971 ERROR trendora.evidence: evidence per-claim drawdown-expectations compute
   aborted — memory pressure, continuing to the next claim:
   ...MemoryError (forward_testing.py:2304 compute_drawdown_expectations → samples.py:923
   _factor_samples → research.py:302 _factor_observations → research.py:221 _fr_slice_map →
   sqlalchemy .../cursor.py fetchmany → MemoryError)

   2026-07-31 07:46:53,010 ERROR trendora.forward_testing: historical forward-aggregate background
   dispatch failed (non-fatal, will re-dispatch on the next request for this identity,
   key=('2026-07-21', 'r1919-f4017590'))
   ...MemoryError (forward_testing.py:1616 _run_historical_forward_aggregates_dispatch →
   compute_forward_aggregates → _forward_agg_slice_map → same yield_per/fetchmany → MemoryError)
   ```
   Counting the ~1,278-line log window around this crash: **222× HTTP 200 vs. 11× HTTP 500**,
   including **`GET /api/health` → 500 three separate times** and `GET /api/backtest` → 500 twice, plus
   `/api/stocks`, `/api/themes`, `/api/runs`, `/api/methodology` each hit once or twice. Also present in
   this window: dozens of `RuntimeError: can't start new thread` tracebacks
   (`anyio/_backends/_asyncio.py` worker-thread pool, `fastapi/concurrency.py
   contextmanager_in_threadpool`) — the process ran out of OS threads to service new requests.
6. Reloaded `/backtest` in the browser at this point — screenshot `UT-J-07-fail.png`:
   > **Backend unavailable** — "The backtest scorecard could not load from the API. No figures are
   > shown rather than fabricated values. Confirm the backend is running and retry."

   (`lib/api.ts`'s `getJSON` throws this exact UI state only on a non-2xx HTTP response or a network
   fetch failure — confirmed by reading the source — so this is not a client-side artifact.)
7. A reload of `/backtest` immediately after DID recover once. But `/data` (a completely different
   page) then ALSO rendered **"Backend unavailable — Dataset coverage could not load from the API"**
   on its own fresh load, and subsequent direct `curl` checks of `GET /api/health` (bypassing the
   browser entirely) returned **complete non-response** — `HTTP:000` (curl's code for "no response
   received") — on 5 consecutive attempts with generous per-attempt timeouts (10s, 30s, 15s, 20s, 25s),
   spanning at least 06:53–06:58 UTC and still unresponsive at the time this report was written
   (final check: `HTTP:000 TIME:10.0s`, immediately before writing this report).
8. Host-level cross-check (to rule out "this is just an unrelated host-wide OOM"): `free -h` showed
   12 GiB available system RAM at the time of the outage — NOT a host-wide memory crisis. The
   Trendora backend process itself (PID 2451515) was at 152% CPU and 5.59 GB RSS, pressed directly
   against its own configured `memory_cap_mb=6144` (6 GB) host-guard ceiling (`logs/backend.log`'s own
   startup banner: `memory_cap_mb=6144 malloc_arena_max=2`) — i.e. a genuine, Trendora-specific,
   per-process resource-exhaustion bug under this iteration's own host-guard budget, not incidental
   contention from another process on the shared host.

**Expected:** "Every polled response returns HTTP 200 for the whole 60+ second window — no connection
refused, no timeout, no non-200 status" and "`/backtest` renders promptly — either normal evidence
values, or the 'Refreshing' banner — never a blank page or an indefinitely-frozen skeleton, even
while the heavy warm runs in the background."

**Actual:** An initial 76-second polling window was clean (34/34 = 200), but continued observation of
the SAME live heavy warm showed it end in `outcome:"failed"` with live `MemoryError` tracebacks,
cascading into real HTTP 500s on `/api/health` (3×) and `/api/backtest` (2×) among others, `/backtest`
and `/data` both surfacing the explicit "Backend unavailable" failure state (not the sanctioned
"Refreshing" state), and finally `/api/health` becoming completely non-responsive (connection/read
timeout, not even a 500) for several sustained minutes. This is a direct, reproduced-live violation of
this journey's own acceptance criteria, and ties directly to this iteration's own dev-acknowledged,
NOT-fixed T2 finding (`_SymbolColumns` reads ~70–80× slower per call — `reports/perf-budgets.md`,
"Iteration 42" section) as the most plausible proximate cause of the memory/CPU exhaustion under
sustained forward-aggregate compute.

**Note on the badge:** even during the confirmed multi-minute `/api/health` outage, the readiness
badge in the already-loaded browser tab continued to display stale `data-state="ready"` / "Ready"
text rather than flipping to "unavailable" — the badge's own recovery-detection behavior under a
sustained outage (as opposed to a clean crash-then-restart, which is J-04's scope and was not
re-tested here) is not itself scored by this test case, but is flagged here as a related observation
for the evaluator/auditor.

---

## Skipped Tests

None — both in-scope test cases (UT-J-05, UT-J-07) executed to a definitive FAIL verdict with direct
evidence. No selector-not-found or environment-unavailable conditions were hit; the failures are
product/backend behavior, not test-execution problems.

**Note on golden replay scripts:** per this agent's instructions, a golden replay script is written
only "for every journey you verify PASS." Since both UT-J-05 and UT-J-07 failed, no new/overwritten
script was written to `runs/goal-session-ops-hardening/journey-scripts/J-05.json` or `J-07.json` this
run — the existing scripts on disk are left untouched, and both journeys fall back to full
browser/LLM re-verification next time.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (became unresponsive during testing — see UT-J-07 above;
  confirmed still down, `HTTP:000`, at report-writing time)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned profile,
  headless
- **Test Date:** 2026-07-31
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-42-evidence/`
  (`UT-J-05-fail.png`, `UT-J-07-fail.png`, `UT-J-07-result.png` [duplicate capture of the same
  failure moment — page had already degraded to "Backend unavailable" by the time this screenshot
  was taken, despite the filename; the genuinely healthy "Refreshing" state seen in Step 4 above was
  captured via page-text extraction, not a screenshot])
- **Backend log referenced:** `logs/backend.log` (host-guard startup banner confirms
  `memory_cap_mb=6144 malloc_arena_max=2`; crash tracebacks quoted above are verbatim from this file)
