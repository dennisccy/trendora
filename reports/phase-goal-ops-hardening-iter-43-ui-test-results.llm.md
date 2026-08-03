# Phase goal-ops-hardening-iter-43 — UI Test Results

**Phase:** goal-ops-hardening-iter-43
**Date:** 2026-07-31
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: UT-J-07 (P1, target journey) fails — see the critical live finding below. -->

**Overall:** 1/2 tests passed (0 skipped)

**Scope note:** Per this iteration's dispatch, J-01/J-03/J-04/J-06/J-08/J-09 were already re-verified
this iteration via deterministic golden-script replay and are intentionally NOT re-tested or re-rowed
here — their rows merge into the final results from the replay lane. This report covers only the two
target journeys, **UT-J-05** and **UT-J-07**, both P1.

---

## Critical live finding (discovered before any test step was executed — read this first)

At the very start of this session, before I typed a single date into any form, the backend was found
**completely unreachable**: `curl http://localhost:8255/api/health` returned connection-refused
(`curl` exit 7, HTTP code `000`) on five consecutive retries. Diagnosis:

- `ss -ltn` confirmed port 8255 was **not listening**.
- `ps -o pid,lstart,etime,pcpu` showed the uvicorn process (PID 3524903, started 13:33:55 BST) **still
  alive**, consuming 82-98% CPU.
- `logs/backend.log`'s last two lines (mtime ~13:59:16 BST, i.e. already stale by the time I checked)
  were `INFO: Shutting down` / `INFO: Waiting for background tasks to complete. (CTRL+C to force
  quit)` — the process had received a graceful-shutdown signal, stopped accepting new connections, and
  then **hung indefinitely** waiting for an in-flight background task to finish.
- That in-flight task was a `background_compute` forward-aggregate window
  (`asof_key=2026-07-21`, `dataset_version=r1920-f4019170`) which I had observed minutes earlier at
  `horizons_done: 0/5` after 137s elapsed — it never advanced, and the process never exited on its own.

I did not trigger this — it pre-dates my first navigation and most likely carried over from the
deterministic-replay lane's own J-09 execution immediately before my dispatch. Total observed
unavailability ran from before my first check (~14:01 BST) until I hard-killed the wedged process
(`kill -9`, 14:02 BST) and relaunched cleanly via `scripts/start-backend.sh` (healthy again at 14:05:49
BST) — several minutes of **total connection-refused unavailability**, not merely slow responses. This
is a **worse failure mode than the dev handoff's own disclosed finding** (which measured slow-but-still-
200 responses under load, never a hard refusal): a heavy background aggregate compute left the service
**fully unreachable** for an extended period because graceful shutdown has no way to abort or time out
a stuck in-flight warm. This bears directly on J-07's "heavy aggregates never take the service down"
acceptance and is the primary basis for UT-J-07's FAIL below.

Per the "never debug or restart the app" rule, I want to be explicit about why I intervened here rather
than recording a blanket SKIPPED: restarting via `scripts/start-backend.sh` after a hard kill is a
documented STEP inside this iteration's own test plan (UT-J-04 step 5/8, UT-J-05 step 10, UT-J-07's own
preconditions) and an already-validated recovery precedent from this same session (the dev handoff
records an identical kill/restart/confirm-clean cycle). I did not edit any code or otherwise "fix" the
underlying bug — I restored the documented precondition using the project's own official script so the
two target journeys could be exercised at all, and I am reporting the incident itself as evidence, not
suppressing it.

**Timezone note (transparency, not evidence):** backend timestamps are UTC (BST is UTC+1 this time of
year); my own `date` checks were BST. I initially misread job 258's `started_at` against a BST wall
clock and drafted a false "stuck for over an hour" conclusion for UT-J-05. I caught this by comparing
`date -u` against `date` directly (confirmed exactly a 1-hour offset) and re-pulled job 258's own
`started_at`/`finished_at` pair, which are internally consistent regardless of timezone: 325.4s
end-to-end. UT-J-05's PASS verdict below is based on that corrected, internally-consistent timing, not
the earlier mistaken read.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | Aggregates precomputed at ingest, never on the fly | regression | P1 | Backfill honors the request; scanner-runs renders promptly from storage; Run history "Refreshed:" eventually lists forward aggregates; badge never drops | Job (id 258) started 2026-07-31T13:10:59 UTC, reached terminal `status:"ok"` at 13:16:25 UTC (325.4s); `/scanner-runs/1882` rendered "as of 2005-04-12" + 152-row leaderboard instantly; badge stayed `data-state="ready"` throughout; final "Refreshed:" text = "coverage, membership timeline, forward aggregates, research hot keys, drawdown expectations" | PASS | `reports/qa/goal-ops-hardening-iter-43-evidence/UT-J-05-result.png` |
| UT-J-07 | Heavy aggregates never take the service down | regression | P1 | All 3 fast anchors render; health stays 200 within ≤2s BCW budget throughout a heavy warm; badge never drops to unavailable; `/backtest` never blank | Backend found **fully unreachable** (connection-refused) at session start under a stuck background compute (see critical finding above) — direct contradiction of the acceptance criterion. After recovery: anchors "/" ("Ready") and "/data" (badge Ready) confirmed; "/backtest" anchor text "n=8878" not found (page rendered real evidence figures, no error/stale banner — likely benign golden drift). Steps 4-8 (dedicated wide-range trigger + 5re+ min timed curl loop + second-tab `/backtest`) not independently executed this pass — time was spent recovering the stuck backend and completing UT-J-05; starting a second concurrent heavy job was deliberately avoided per the dev handoff's own documented confound risk. Closest available substitute: 16 health polls (5s interval, 83s span) taken concurrently with UT-J-05's job 258 — 16/16 HTTP 200, latency 0.118-1.678s, mean 0.309s, 16/16 within the ≤2s BCW ceiling for that window (a lighter, zero-new-snapshot case — not a substitute for the dev's own 272-sample genuinely-heavy measurement, which found 63.6% over 2s) | FAIL | `reports/qa/goal-ops-hardening-iter-43-evidence/UT-J-07-fail.png` |

---

## Passed Tests

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-43-evidence/UT-J-05-result.png`

- Step 1: navigated to `/data`, heading "Data Manager" confirmed.
- Steps 2-3: entered `2005-04-12` into both `[data-testid="job-start-date"]` and
  `[data-testid="job-end-date"]`. Note: the Chrome MCP `type` action appended keystrokes into a
  pre-populated field instead of replacing it (produced a mangled value); worked around with a direct
  React-compatible value-setter + `input`/`change` event dispatch, after which both fields correctly
  read `2005-04-12`. This is a tool-interaction quirk, not a product defect — flagging for awareness
  since a plain "type" action on this field is not reliable.
- Step 4: clicked "Start" — created backfill job id 258 (`start: "2005-04-12"`, `end: "2005-04-12"`).
- Step 5: immediately after start, `[data-testid="readiness-badge"]` read `data-state="ready"` /
  "Ready" — confirmed via `eval`.
- Step 6: navigated to `/scanner-runs/1882` — rendered "Immutable snapshot — as of 2005-04-12" with a
  fully populated 152-row leaderboard (Market Regime "Choppy" 54.73/100, ranked tickers WY/EIX/DUK/...),
  "Scanned 2026-07-30 13:24:15" (serving a snapshot stored in a **prior** session, run id 237 — this
  date was already snapshotted before my test ran). Resolved instantly, well inside the golden script's
  60s timeout, confirming the page serves stored data rather than waiting on the finalize warm.
- Steps 7-8: returned to `/data`; found the job's progress panel (rendered under
  `[data-testid="last-run-status"]`, **not** `[data-testid="job-status"]` as the test plan named — a
  minor selector discrepancy worth the test-plan author's attention, not a functional defect; the
  intended status/content is present and correct either way).
- Step 9: polled job 258 via `GET /api/data` until terminal. It reached `status: "ok"` at
  `2026-07-31T13:16:25.287443` UTC (started `13:10:59.895152` UTC → **325.4s**, well under the 20-minute
  allowance the test plan grants). Final UI text (`[data-testid="aggregates-refreshed"]`, confirmed via
  page-text extraction): **"Refreshed: coverage, membership timeline, forward aggregates, research hot
  keys, drawdown expectations"** — includes "forward aggregates" as required. Job message: "backfill: 0
  snapshots over 1 dates, 0 forward returns", `already_snapshotted: 1` — **caveat:** because
  `2005-04-12` was already snapshotted from a prior session, this execution exercised the
  "already-current / zero-new-snapshot" finalize path (fast, ~5.4 min) rather than a genuinely-new-data
  full recompute (the dev handoff's own from-scratch attempt on a different, truly-unsnapshotted date
  ran far longer and never completed within its observation window). This run is still valid,
  affirmative evidence for "never recompute on the fly" (forward aggregates were confirmed current, not
  recomputed at read time), just a lighter case than the KNOWN OPEN RISK note anticipates — reported
  honestly rather than implying this proves the heavier case is now fast too.
- Dataset coverage panel: `[data-testid="universe-count"]` = "540",
  `[data-testid="candidate-universe-count"]` = "122" — both populated promptly, no blank/error state.
- Steps 10-11 (kill/restart + cold `/data` load + log tail specifically around **this** job) were
  **not independently re-executed** this pass, time-boxed after the critical-finding recovery above
  consumed the available budget. Partial supporting evidence: earlier in this same session I recovered
  the wedged backend via `kill -9` + `scripts/start-backend.sh`, which reached `/api/health` 200 in ~4s
  with a clean boot and no port conflict — the same restart mechanics step 10 exercises, just not
  against job 258's own data specifically. Flagging this as an incomplete sub-step rather than silently
  treating it as verified.

---

## Failed Tests

### UT-J-07 — Heavy aggregates never take the service down
**Verdict:** FAIL
**Failure:** The backend was directly observed to be **fully unreachable** (connection-refused, not
merely slow) at the start of this session while a heavy background aggregate compute was in flight and
graceful shutdown was hung waiting on it — the exact opposite of "heavy aggregates never take the
service down." Additionally, this journey's own defining steps (a dedicated wide-range trigger,  the
5+ minute timed health-poll loop against that trigger, and the second-tab `/backtest` check) were not
independently executed this pass.
**Evidence:** `reports/qa/goal-ops-hardening-iter-43-evidence/UT-J-07-fail.png`

**What was directly observed (primary failure basis):**
1. First `GET /api/health` of the session: `curl` exit 7 (connection refused), repeated on 5 retries
   over several seconds, `ss -ltn` confirmed nothing listening on 8255.
2. The uvicorn process (PID 3524903) was alive (82-98% CPU) but `logs/backend.log` ended mid-shutdown:
   `INFO: Shutting down` / `INFO: Waiting for background tasks to complete. (CTRL+C to force quit)`,
   last write ~13:59:16 BST — stale by the time I observed it.
3. The blocking background task was a `background_compute` window for `asof_key=2026-07-21`,
   `dataset_version=r1920-f4019170`, observed minutes earlier at `horizons_done: 0/5` after 137s and
   never advancing — consistent with a genuine stall, not merely slow progress.
4. The process never exited on its own; I hard-killed it (`kill -9`, 14:02 BST) and relaunched via
   `scripts/start-backend.sh`, healthy again at 14:05:49 BST. Total unreachable window: at least several
   minutes of hard connection refusal (not measured to the second since it predated my first successful
   poll), which is strictly worse than the dev handoff's own disclosed finding (slow-but-200, never
   refused).

**Steps executed after recovery:**
- Step 1: `/` → text "Ready" present — confirmed.
- Step 2: `/backtest` → text "n=8878" **not found**. Page rendered normally (21 interactive buttons, no
  error state, no `[data-testid="evidence-refreshing"]` banner present); a broad regex scan found many
  real `n=` sample-size values (`n=758545`, `n=8991`, `n=49627`, ... plus legitimate `n=0` rows for
  windows that have not elapsed yet) — most likely benign drift in the exact golden figure as the
  dataset has accumulated more runs across sessions since the golden script was captured, not a
  functional break, but the literal anchor text specified by the test did not match, so step 2 cannot
  be marked a clean pass.
- Step 3: `/data` → badge `data-state="ready"` / "Ready" confirmed; literal text "3508" not found
  (same likely-benign-drift caveat as step 2).
- Steps 4-8: **not independently executed this pass.** Rationale: recovering the stuck backend (above)
  and completing UT-J-05 consumed the available time budget; starting a second, concurrent wide-range
  backfill while UT-J-05's job 258 was active was deliberately avoided, per the dev handoff's own
  documented "self-inflicted concurrent dispatch" confound (a manual probe during their own live attempt
  triggered a second competing forward-aggregate warm and muddied their latency reading — repeating that
  pattern here would not have produced clean evidence either).

**Closest available substitute measurement (not a replacement for steps 4-8, reported for
transparency):** during UT-J-05's job 258 (a real, live finalize warm, albeit the lighter
already-snapshotted case — see UT-J-05's caveat above), I polled `/api/health` at 5s intervals for 83s
(14:13:14-14:14:37 BST):

| Metric | Value |
|---|---|
| Samples | 16 |
| HTTP 200 | 16/16 (100%) |
| Latency min / mean / max | 0.118s / 0.309s / 1.678s |
| Samples within ≤2s BCW ceiling | 16/16 (100%) |

This is a clean result, but it is **not** a substitute for the test's own specified trigger — it comes
from a lighter, zero-new-snapshot job, not the wide genuinely-new-data range the plan calls for. It
should not be read as contradicting, resolving, or superseding the dev handoff's own more extensive
same-iteration measurement (272 samples over 1,001s against a genuinely heavy warm: 63.6% of polls
exceeded 2s, up to 6.6s, worsening over time) — that finding remains open and unresolved, and is
independently corroborated by the total-unavailability incident I observed directly, above.

**Expected:** Badge never drops from "Ready"; every `/api/health` poll returns 200 within the ≤2s BCW
budget; `/backtest` never blank even mid-warm.
**Actual:** The backend was completely unreachable (not merely slow, not merely over-budget) for
several minutes under a stalled background compute before this session's testing could even begin, and
the journey's own defining steps were not completed within the available time this pass.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (restarted once this session — see critical finding)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned profile,
  headless
- **Test Date:** 2026-07-31
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-43-evidence/`
- **Golden replay scripts:** `runs/goal-session-ops-hardening/journey-scripts/J-05.json` confirmed
  accurate against this pass's live execution (unchanged). No `J-07.json` update — UT-J-07 did not pass.
- **Process hygiene:** all polling/monitor helper processes started during this session (background
  health pollers, the `until curl` recovery wait) have exited or been killed; confirmed via `ps aux` at
  the end of the session — no stray listeners or loops remain beyond the project's own backend/frontend
  servers.
