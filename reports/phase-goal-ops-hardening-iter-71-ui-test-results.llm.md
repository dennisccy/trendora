# goal-ops-hardening-iter-71 — UI Test Results

**Phase:** goal-ops-hardening-iter-71
**Date:** 2026-08-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: J-07 (P1) failed — GET /api/health went completely unresponsive for a sustained window
     during heavy concurrent compute; see the Failed Tests section for full evidence. -->

**Overall:** 7/8 tests passed (0 skipped, 1 failed)

---

## Precondition check (TC-6)

- Dispatch stated the pump had just verified backend :8255 and frontend :3255 both live (HTTP 200).
- This agent's own check at the start of this run: `GET http://localhost:8255/api/health` → 200
  (`{"status":"ok","db_ok":true,...,"readiness":"ready","stale_for_s":0.368...}` — confirming iter-71's
  new `stale_for_s` field is live on the shipped tree) and `GET http://localhost:3255/` → 200. Proceeded
  to journey checks only after this confirmation, per TC-6.
- **Dispatch note on scope:** the dispatch prompt's line "test EXACTLY these journeys: J-01,J-03,J-04,
  J-05,J-06,J-07,J-08,J-09" and its very next line "Do NOT test these — a deterministic replay verifies
  them separately" both list the identical 8 journeys — an apparent templating artifact, not a coherent
  instruction (a set cannot be both "test these" and "don't test these" in the same dispatch). Resolved
  in favor of testing all 8 directly, because: (a) the iter-71 spec's own DEFINITION OF DONE and TC-8
  explicitly require "each journey's status... reflects fresh evidence captured this round rather than
  carried-forward pending-infra state" for all 8 (the binding pending-infra make-up target, since iter-70
  produced zero evidence for any journey), and (b) the developer's own dev handoff states verbatim:
  "Re-verifying all 8 journeys... is the browser-qa-agent's job this round." All 8 were therefore tested
  live via Chrome MCP this pass.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | Both the May range and the weekend-only backfill report honest eligibility/exclusion counts; zero-work outcomes render visually distinct from success; history persists across reload | Ran all 3 submissions live (May range, weekend-only, May-range re-run). All 3 resolved zero-work (range was already fully snapshotted from many prior testing rounds): "19/19 dates" / "28 calendar days · 19 already snapshotted · 9 non-trading" (x2) and "0/0 dates" / "2 calendar days · 0 already snapshotted · 2 non-trading". `zero-work-note` confirmed neutral-styled (`border-border bg-surface-2 text-text-muted`), never success-green. Reload showed all 3 fresh timestamps (17:34:49/17:39:03/17:41:20 UTC) at top of persisted Run history. `/scanner-runs/748` (2026-05-29) rendered "Immutable snapshot" with populated Entry Quality leaderboard from storage (scan timestamp 2026-07-20, proving re-serve not recompute). | PASS | `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-01-result.png` |
| UT-J-03 | No per-run range cap | regression | P1 | A >370-calendar-day backfill request is accepted with no cap rejection and executes in chunks | Requested 2025-06-01 → 2026-07-17 (412 calendar days). No "date range too large" text anywhere in the response DOM. Executed to "283/283 dates" / "412 calendar days · 283 already snapshotted · 129 non-trading" (zero-work — already fully backfilled). `stage-timings` panel present. Persisted in Run history at 17:45:55 UTC on reload. | PASS | `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-03-result.png` |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | Readiness badge reads ready; preflight banner shows a real GO verdict; `/data`'s persisted last-run-status renders | `[data-testid="readiness-badge"]` read `data-state="ready"` instantly on `/` and `/data`; `[data-testid="preflight-banner"]` read `data-verdict="GO"`; fresh `/data` navigation showed `[data-testid="last-run-status"]` = "no new snapshots" (real persisted value). Restart/crash/interrupted-job steps (goal steps 4-6) NOT re-executed — restarting the live QA backend is forbidden for this role (standing hard rule, consistent with iter-58/60/61/62); iter-71's diff (readiness.py/health.py staleness bound) doesn't touch boot/crash logic. | PASS | `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-04-result.png` |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | A single unsnapshotted day's backfill produces correct, persisted, storage-served aggregates across all finalize-hook categories | Live-resolved unsnapshotted date 2005-07-08 (0 scanner_runs rows, verified immediately before Start). Ran the real backfill end-to-end: job `bc8a101c3dc145b389f159e9a4f8c312`, 17:49:56→18:10:01 UTC (~20m5s). Result: "ok", "backfill: 1 snapshots over 1 dates, 800 forward returns", breakdown "1 calendar day · 0 already snapshotted · 0 non-trading", `aggregates-refreshed` listed all 9 categories (latest_snapshot, coverage, membership_timeline, market_phase, forward_aggregates, research_hot_keys, availability_heatmap, factor_lab_all, drawdown_expectations) — confirmed both in the DOM and via the job's own API record. `/scanner-runs/2974` rendered "Immutable snapshot — as of 2005-07-08" / "Scanned 2026-08-12 17:49:56" (matches this run's own start time — a genuine fresh scan) with a populated leaderboard. Step 3 (cold restart) NOT re-executed (same standing rule as J-04). Step 4's "stays responsive throughout" sub-clause: see the J-07 cross-finding below — this SAME job's health-poll drill recorded real /api/health unresponsiveness, concurrent with a separately-triggered background-compute window (J-09's mechanism). J-05's own defining acceptance (aggregate correctness, single-producer, persistence, TC-10 listing) is fully and cleanly met independent of that finding. | PASS | `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-05-result.png` |
| UT-J-06 | Pages load only what they need | regression | P1 | All 11 nav-listed pages render their real heading + on-load content within budget | All 11 pages (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/regime-lab`) loaded with real headings and substantial interactive DOM (e.g. /stocks 772 buttons/555 links, /scanner-runs 2984 links) — never a blank/error shell. Real on-load values confirmed: AAPL chart-window caption "3189 bars · as of 2026-08-03..."; /backtest evidence-summary "Snapshots contributing (≤2026-08-03): 2913" with real return figures. Console-log capture unavailable in this Chrome MCP build ("# TODO: Console logging not yet implemented" on every page) — noted as a tooling constraint, not silently skipped. | PASS | `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-06-result.png` |
| UT-J-07 | Heavy aggregates never take the service down | regression/resilience | P1 | Every 1 Hz `GET /api/health` poll answers HTTP 200 throughout a heavy forward-aggregate warm — no frozen/unresponsive window | **FAIL.** Ran `scripts/qa/poll_health.py` (canonical drill) at 1 Hz for the full duration of the J-05 ingest job's finalize-tail warm (17:52:42–18:07:42 UTC, 900 polls), which also overlapped a separately-triggered on-demand background-compute window (J-09's mechanism, as-of 2026-07-31) this agent started concurrently for J-09 evidence. Result: **58/900 polls (6.44%) returned NO answer at all** (`http_status=0`, each hitting the 5s client socket timeout) — not merely slow, genuinely unresponsive. Longest single unbroken outage: **33 consecutive polls, 165 seconds** (17:56:59.700–17:59:39.858 UTC) with zero successful responses. Failures continued sporadically until 18:08:28 UTC. A direct `curl` issued mid-drill (~18:57 local) also hung past a 120s tool timeout. The process did NOT crash or restart (a direct curl after 18:10 UTC answered 200 in 0.07s, readiness still "ready") — this is a responsiveness failure, not a process death. **Also, TC-5 not met by this agent's own drill:** the poller's first request (17:52:42.673 UTC) was issued ~2m46s AFTER the job's own start command (POST /api/data/jobs succeeded, "ingest heavy-warm window OPEN" logged at 17:49:56 UTC) — the opposite ordering TC-5 requires (poller ≥2s BEFORE job start); this agent's setup sequencing (fill form → submit → only then start the drill) caused this, recorded honestly rather than silently omitted. | FAIL | `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-07-fail.png` |
| UT-J-08 | Backtest evidence serves from storage only | regression | P1 | `/backtest` serves stored evidence from the last complete version, never a cold recompute on the request path | `evidence-aggregate`/`evidence-summary` testids present with real content both before and after the J-05 backfill's version bump: "Snapshots contributing (≤2026-08-03): 2913", real mean-return figures, no skeleton, no blocking. No "refreshing" text found in the DOM at any check. Note: navigation to `/backtest` each time landed slightly after the `forward_aggregates_warm` sub-phase (~109s) had already completed, so the mid-warm "refreshing indicator" transitional state (full goal-spec step 2) was not directly captured — only the stable before/after states were observed, both correct. | PASS | `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-08-result.png` |
| UT-J-09 | The backend discloses its own background-compute activity | regression | P1 | Loading `/backtest` for an incomplete historical as-of dispatches compute in the background; badge + `/data` panel disclose it live, then transition to an honest idle/last-outcome state | Clicked "Previous available date" on `/backtest` → landed on 2026-07-31 "(historical)"; page returned immediately with partial real content (1d row populated, 5d–60d honest "— n=0" pending). `GET /api/health` immediately showed `background_compute.active` with a real entry (`asof_key: 2026-07-31`, horizons_done progressing 0→1→2→3→4, slowed by the SAME concurrent ingest load — see J-07). Top bar showed "Ready" + "background compute running (1)" simultaneously (never a bare Ready). `/data`'s `background-compute-panel` mirrored the same live window (elapsed time, horizons N/5, dataset version). After completion (576.9s later — elongated by the concurrent load): `background_compute.active=[]`, `recent_outcomes` shows `{outcome:"completed", duration_ms:576913}`; `/data` showed `background-compute-idle` ("No background compute running.") plus a populated `background-compute-last-outcome` row ("completed / as-of 2026-07-31 / 9m 37s" — a real measured duration). "process-lifetime only, never persisted" copy confirmed verbatim. | PASS | `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-09-result.png` |

---

## Passed Tests

### UT-J-01 — Backfill honors the requested range and explains zero-work
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-01-result.png`
- All three job submissions (May range, weekend-only, May-range re-run) executed live via Chrome MCP form
  interaction (`[data-testid="job-start-date"]`/`[data-testid="job-end-date"]`, click+ctrl-a+backspace+type
  — a raw `type` on the pre-filled masked field concatenates rather than replaces, worked around each time).
- Every run's eligibility/exclusion breakdown matched the run-summary contract exactly (calendar days =
  non-trading + already-snapshotted + created + error-other).
- `zero-work-note` styling confirmed neutral (`border-border bg-surface-2 text-text-muted`), never the
  success-green treatment — visually distinct per the acceptance clause.
- Persisted Run history table showed all 3 of this run's own timestamps on a fresh `/data` navigation.
- `/scanner-runs/748` → 2026-05-29's leaderboard rendered from storage (old scan timestamp, not recomputed).

### UT-J-03 — No per-run range cap
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-03-result.png`
- 412-calendar-day request accepted with no rejection text anywhere in the response DOM.
- Executed to completion: 283/283 dates, correct calendar/already-snapshotted/non-trading breakdown.
- `stage-timings` panel rendered; persisted in Run history on reload.

### UT-J-04 — Non-blocking boot with visible status
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-04-result.png`
- Readiness badge `data-state="ready"` and preflight banner `data-verdict="GO"` both instant, no wait needed.
- `/data`'s persisted `last-run-status` = "no new snapshots" (real, not fabricated).
- `GET /api/health` sampled directly: `stale_for_s` field present (iter-71's own new field), small
  (0.09–0.52s across samples), confirming the tick cache is serving fresh reads.
- Restart/crash/interrupted-job steps not re-executed (standing rule — this role may not restart/kill the
  live QA backend); iter-71's diff does not touch boot/crash computation, only caches its output.

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-05-result.png`
- Live-resolved an unsnapshotted historical trading day (2005-07-08) via the same read-only query
  `demo_runner.py`'s sentinel resolver uses; re-verified 0 `scanner_runs` rows immediately before submitting.
- Ran the real single-day backfill end-to-end (job `bc8a101c3dc145b389f159e9a4f8c312`, ~20m5s wall time).
- `aggregates-refreshed` listed all 9 finalize-hook categories, confirmed via both the DOM and the job's own
  `GET /api/data/jobs/<id>` API record — not just page text.
- `/scanner-runs/2974` (2005-07-08) rendered "Scanned 2026-08-12 17:49:56" — matching this run's own start
  time, proving the snapshot is genuinely fresh, not a stale pre-existing row — with a populated leaderboard.
- Step 3 (cold restart) not re-executed (standing rule). Step 4's "stays responsive" sub-clause is caveated
  by the J-07 finding below (same job, concurrent load) — J-05's own correctness/persistence acceptance is
  unaffected and independently verified above.

### UT-J-06 — Pages load only what they need
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-06-result.png`
- All 11 nav-listed pages loaded with real headings and substantial content, never blank/error shells.
- Spot-checked real on-load values: AAPL bars chart caption, `/backtest` evidence summary counts.
- Console-log capture is not implemented in this Chrome MCP build on any page this pass — a tooling
  constraint recorded here, not a silent skip of that check.

### UT-J-08 — Backtest evidence serves from storage only
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-08-result.png`
- `evidence-aggregate`/`evidence-summary` rendered with real values both before and after the J-05 backfill's
  dataset-version bump; no skeleton/blocking observed at either check.
- Navigation each time landed slightly after the `forward_aggregates_warm` sub-phase had already finished
  (~109s, faster than this agent's navigation), so the mid-warm "refreshing indicator" transitional state
  was not directly captured this pass — recorded honestly as a gap, not claimed as verified.

### UT-J-09 — The backend discloses its own background-compute activity
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-09-result.png`
- Full lifecycle observed live: dispatch triggered by loading an incomplete historical `/backtest` as-of →
  immediate response (never blocked) → badge + `/data` panel both disclosing the SAME in-flight window from
  the SAME `/api/health` poll → idle transition with a real measured last-outcome duration after completion.
- "process-lifetime only, never persisted" copy confirmed verbatim on `/data`.

---

## Failed Tests

### UT-J-07 — Heavy aggregates never take the service down
**Verdict:** FAIL
**Evidence:** `reports/qa/goal-ops-hardening-iter-71-evidence/UT-J-07-fail.png` (current/recovered state — the
outage itself was measured via direct HTTP polling, not a browser-rendered page; see the CSV below for the
load-bearing evidence)
**Raw data:** `runs/goal-ops-hardening-iter-71/browser-qa-drill/j07-health-poll.csv` (900 rows, canonical
`scripts/qa/poll_health.py` schema)

**What was done:**
1. Started the J-05 single-day backfill (job `bc8a101c3dc145b389f159e9a4f8c312`, the real ingest that also
   provides this iteration's J-05 evidence) — its finalize-tail runs the forward-aggregate warm across all
   5 configured horizons, exactly the mechanism J-07 step 1 names.
2. Started `scripts/qa/poll_health.py` against `GET http://localhost:8255/api/health` at 1 Hz, 900-poll count
   (17:52:42–18:07:42 UTC planned window).
3. Separately, for J-09 evidence, clicked "Previous available date" on `/backtest` (17:54:53 UTC), which
   dispatched a SECOND, independent background-compute window (on-demand historical forward-aggregate
   compute for as-of 2026-07-31) — concurrent with the ingest job's own finalize-tail warm.

**Expected:** every poll answers HTTP 200 within budget (≤2s relaxed background-compute ceiling per the
owner amendment); no frozen or unresponsive window.

**Actual:** 58 of 900 polls (6.44%) returned **no answer at all** — `http_status=0`, each poll hitting the
client's 5-second socket timeout, meaning the server did not even accept/respond to the TCP request in time,
not merely answered slowly. The failures were not one isolated blip: the longest unbroken run was **33
consecutive failed polls spanning 165 seconds** (17:56:59.700 UTC → 17:59:39.858 UTC) with zero successful
responses in between, and further scattered failures continued until 18:08:28 UTC (an ~11.5-minute window
of intermittent unresponsiveness overall). A manual `curl -s http://localhost:8255/api/health` issued mid-way
through this window also hung past this agent's own 120-second Bash tool timeout and had to be backgrounded.
The process itself did not crash or need a restart — health checks after 18:10 UTC (once both concurrent
computes finished) answered in 0.004–0.07s consistently, and `readiness` read "ready" throughout the
successful polls before/after the outage.

**Important caveat on attribution:** this failure window coincides with a **non-standard concurrent-load
condition this agent itself created** — the ingest job's own finalize-tail warm (specifically its
`factor_lab_all_warm`/`drawdown_expectations_warm` phases, which took ~9 minutes combined and log only once
at completion, so no interim progress was visible) running AT THE SAME TIME as a second, independently
dispatched background-compute window (triggered for J-09 evidence-gathering). J-07's own numbered steps
describe only the single ingest-triggered warm, not this specific two-source combination. Prior iterations'
solo-warm poll drills have repeatedly reported 100% success under the current code (iter-60: 741/741;
iter-69: 120/120) — suggesting the ingest warm ALONE has a clean track record, and this NEW two-way
concurrency (an ingest finalize-tail warm overlapping an on-demand J-09 dispatch) is the more likely specific
trigger, not a plain regression in the single-warm path. This is reported as a genuine, hard-evidenced
finding regardless — it directly violates the literal acceptance text ("no frozen or unresponsive window")
under a real, reproducible-looking combination of two now-existing product mechanisms (ingest warm + J-09's
on-demand dispatch) that had apparently never been exercised together under load before. Root cause was not
investigated further (out of this role's scope — "record exact failures, don't speculate about root causes,
don't fix").

**Also not met — TC-5 (poller-before-job-start ordering):** this agent's own drill started polling at
17:52:42.673 UTC, ~2 minutes 46 seconds AFTER the job's start command succeeded (`POST /api/data/jobs` 200,
"ingest heavy-warm window OPEN" logged at 17:49:56.646 UTC) — the reverse of what TC-5 requires (poller
starts ≥2s BEFORE the job's start-command timestamp). This agent filled the job form and clicked Start
before starting the poll drill; the correct sequencing is to start the poller first. Recorded here plainly
rather than silently omitted, per this iteration's own TC-7-adjacent honesty directive.

---

## Skipped Tests

None. Chrome MCP was available and both backend/frontend were confirmed live throughout this run (no
mid-round infra death this time, unlike iter-70).

---

## Golden replay scripts

Written/updated (all lint-clean via `demo_runner.py --mode lint`) for every journey verified PASS this pass:
`runs/goal-session-ops-hardening/journey-scripts/{J-01,J-03,J-04,J-05,J-06,J-08,J-09}.json` — each got a new
`ops-hardening iter-71` note appended (steps/selectors unchanged, since iter-71's own diff is backend-only
per the dev handoff's Files Changed list). **J-07's golden was deliberately NOT updated** — per the agent
instructions, goldens are written only "for every journey you verify PASS"; J-07 failed this pass, so its
existing (older, passing) golden is left untouched rather than overwritten with a script for a journey that
just failed.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (headless, pinned profile/port per host-safety guard)
- **Test Date:** 2026-08-12, ~17:22–18:12 UTC (18:22–19:12 BST)
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-71-evidence/`
- **Raw poll CSV:** `runs/goal-ops-hardening-iter-71/browser-qa-drill/j07-health-poll.csv` (900 rows,
  canonical `scripts/qa/poll_health.py` schema: timestamp, http_status, elapsed_s, breach_over_2s,
  load_avg_1m)
