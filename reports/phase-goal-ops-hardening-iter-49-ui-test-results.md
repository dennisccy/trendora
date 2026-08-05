# Phase goal-ops-hardening-iter-49 — UI Test Results

**Phase:** goal-ops-hardening-iter-49
**Date:** 2026-08-05
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: P1 tests UT-02, UT-03, UT-05 all fail/blocked — the backend process crashed with a
     MemoryError mid-run and did not recover during this dispatch. -->

**Overall:** 6/15 tests passed (3 failed, 6 skipped)

**Headline finding:** This report supersedes the earlier SKIPPED report for this phase (backend was
down at that dispatch time). This time the backend was confirmed up and healthy at dispatch start
(`GET /api/health` → 200, `readiness: ready`) and the full test plan was executed for real. However,
partway through — during UT-02's live historical-gap backfill, ~14m53s into its run, deep in the
finalize tail this iteration targets — the backend process **crashed** with a `MemoryError` and a
fatal `OpenBLAS error: Memory allocation still failed after 10 retries, giving up.` It did not recover
for the remainder of this dispatch (confirmed down for 6+ minutes via direct polling plus a dedicated
4-minute automated recovery-check that timed out with no recovery). This is a genuine, reproducible
regression, not the test plan's disclosed "known ~10s health-check blip" caveat — the backend never
came back. Per my instructions I did not restart it myself; it is recorded factually below, including
full causal attribution. See "Critical Finding" for the timeline and evidence.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/data` loads without errors | smoke | P1 | Heading, job form, readiness badge "Ready", no errors | All present; `readiness-badge` `data-state="ready"` | PASS | `reports/qa/goal-ops-hardening-iter-49-evidence/UT-01-result.png` |
| UT-02 | Historical-gap backfill reaches terminal status for its ENTIRE finalize tail | happy-path | P1 | Job reaches a terminal status within ~17-18 min (budget 20 min) | Immediate `running` state confirmed correct; job was still `running` (never terminal) at 14m53s when the **backend process crashed** (MemoryError); job never reached a terminal status; backend still down 6+ min later | FAIL | `reports/qa/goal-ops-hardening-iter-49-evidence/UT-02-stuck-running-precrash.png`, `UT-02-fail.png` |
| UT-03 | Backfilled historical date renders on Scanner Runs | happy-path | P1 | `2012-01-05` row appears, leaderboard renders | Blocked — UT-02 never reached terminal status; backend down, page cannot be tested | SKIP | none |
| UT-04 | Job form blocks Start with incomplete date range | validation | P3 | Start button stays disabled | Blocked — backend down; the job form does not render at all in the backend-unavailable state (only the NO-GO banner shows) | SKIP | none |
| UT-05 | Backend stays responsive during finalize tail | error | P1 | `readiness-badge` shows `ready` almost throughout; only a brief (~10s), self-recovering blip is acceptable | Badge read `ready` on every direct check through ~14m45s; then genuinely flipped to `data-state="unavailable"` / "Backend unavailable" with preflight `NO-GO`, and **stayed down continuously for 6+ minutes** (confirmed via a 4-minute automated recovery-check that timed out) — a genuine failure condition, not the disclosed brief blip | FAIL | `reports/qa/goal-ops-hardening-iter-49-evidence/UT-05-fail.png` |
| UT-06 | Evidence drawdown-expectations panel renders correctly | regression | P2 | `evidence-expectations-table` renders real rows, no `evidence-expectations-unavailable` fallback | Confirmed: real rows (e.g. "-7.87% (p90 -3.73%) n=58993") under an `evidence-claim-regime` card; no unavailable fallback present | PASS | `reports/qa/goal-ops-hardening-iter-49-evidence/UT-06-result.png` |
| UT-07 | Factor Lab loads and decile drill-down link still works | regression | P3 | Page loads without error card; "N=" link navigates to `/research/samples` with cohort data | Page loaded without an error card (honest "Still computing" state, by design) — but the underlying `compute_factor_lab_all` computation hit a `MemoryError` that was the proximate trigger for the fatal crash below. The decile table never rendered and the "N=" link was never reachable | FAIL | `reports/qa/goal-ops-hardening-iter-49-evidence/UT-07-fail.png` |
| UT-08 | Zero-work re-run reads honestly | ux | P2 | `no new snapshots` badge (neutral color), `zero-work-note` panel, `0` snapshots_created | Blocked — depends on UT-02 completing; backend down | SKIP | none |
| UT-09 | Backtest forward-aggregate numbers render correctly | regression | P2 | Real numeric values (hit rate, mean/median return, sample counts), no NaN/all-zero | Confirmed real, varied values across all breakdown tables (e.g. bucket A "+8.11% n=14810", VCP "+2.96% n=35942") | PASS | `reports/qa/goal-ops-hardening-iter-49-evidence/UT-09-result.png` |
| UT-J-01 | J-01: Backfill honors requested range and explains zero-work | regression (goal journey) | P1 | Persisted run history still lists the May-2026 backfill, the weekend zero-trading-day run, and the zero-work re-run, all with correct exclusion breakdowns and a neutral (non-green) badge for zero-work | Confirmed via persisted Run History table (verified pre-crash, before starting UT-02, to avoid job overlap): `2026-05-02 → 2026-05-29` row shows "28 calendar days · 19 already snapshotted · 9 non-trading"; `2026-05-02 → 2026-05-03` shows "2 calendar days · 0 already snapshotted · 2 non-trading"; both carry the neutral `run-status`="no new snapshots" badge (muted styling, not green) | PASS | `reports/qa/goal-ops-hardening-iter-49-evidence/UT-J-01-result.png` |
| UT-J-03 | J-03: No per-run range cap | regression (goal journey) | P1 | A >370-day request is accepted (no cap rejection) and completes | Confirmed via persisted Run History: `2025-06-01 → 2026-07-17` (412 calendar days) row present twice, both `status=ok`/`no new snapshots`, "283 already snapshotted, 129 non-trading" — accepted and executed to completion, no rejection | PASS | `reports/qa/goal-ops-hardening-iter-49-evidence/UT-J-03-result.png` |
| UT-J-04 | J-04: Non-blocking boot with visible status | regression (goal journey) | P1 | Restart→≤5s first 200, phase-aware polling, crash→honest unreachable, mid-flight job shows interrupted state | Not executed — restarting/killing the backend is out of scope for this browser-only QA agent (explicit instruction: never restart or debug services). Incidental partial evidence: the backend crashed **on its own** during this run, and the frontend showed exactly the honest "Backend unavailable" badge + "NO-GO" preflight banner J-04 expects for the crashed state (see UT-05 evidence) — but the restart-timing, phase-polling, logfile, and mid-flight-job-interrupted-state assertions were not performed | SKIP | `reports/qa/goal-ops-hardening-iter-49-evidence/UT-05-fail.png` (incidental) |
| UT-J-06 | J-06: Pages load only what they need | regression (goal journey) | P1 | All listed pages load without error cards | Confirmed pre-crash: `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/regime-lab` all loaded with correct headings, no error cards | PASS | `reports/qa/goal-ops-hardening-iter-49-evidence/UT-J-06-result.png` |
| UT-J-08 | J-08: Backtest evidence serves from storage only | regression (goal journey) | P1 | Instant serve of last-complete version; visible "refreshing" indicator during a warm; new version served after warm completes | Partial/inconclusive — confirmed (pre-crash, while UT-02's job was live) that `/backtest`'s `evidence-aggregate`/`evidence-summary` sections rendered instantly with real "Snapshots contributing" data (no cold-compute skeleton). Did not observe an `evidence-refreshing` state transition, and could not complete the full version-bump-then-reload check before the backend crashed | SKIP | none (see `UT-09-result.png` for the same page's healthy-serve state) |
| UT-J-09 | J-09: The backend discloses its own background-compute activity | regression (goal journey) | P1 | `/api/health` and `/data` panel disclose an in-flight background-compute window with identity/progress; idle state after | Not executed — the backend crashed before this journey was attempted | SKIP | none |

---

## Passed Tests

### UT-01 — `/data` loads without errors (smoke)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-49-evidence/UT-01-result.png`
- Navigated to `/data`; heading "Data Manager" visible.
- "Start a fetch / backfill job" panel present with `job-start-date`, `job-end-date` fields and a "Job kind" dropdown defaulted to "Backfill snapshots".
- `readiness-badge` showed `data-state="ready"` ("Ready", green).

### UT-06 — Evidence page's drawdown-expectations panel renders correctly (regression)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-49-evidence/UT-06-result.png`
- Navigated to `/evidence`; found a card with `evidence-claim-regime` badge ("Regime: Risk-on").
- Its `evidence-expectations-table` rendered populated `evidence-expectations-phase-row` rows with real figures, e.g. Expansion: "-7.87% (p90 -3.73%) n=58993", "20.0d (p90 20.0d) n=58993".
- `evidence-expectations-unavailable` fallback was not present.

### UT-09 — Backtest page renders forward-aggregate numbers correctly (regression)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-49-evidence/UT-09-result.png`
- Navigated to `/backtest`. The per-date scorecard for the very latest as-of (2026-08-03) honestly showed all-NA (no elapsed bars yet — expected, disclosed behavior, not a bug).
- The "Forward-tested evidence (expanding window)" all-history aggregate section — the actual target of this iteration's `_ExactMeanAcc.add_ratio` accumulator change — rendered real, varied, non-degenerate numbers across every breakdown (score bucket, setup type, market regime, VCP, pullback-to-DMA, flat-base, control-group), e.g. bucket A "+8.11% n=14810", Strong risk-on "+1.44% n=279665". No NaN, no all-zero, no error card.

### UT-J-01 — J-01: Backfill honors the requested range and explains zero-work (regression)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-49-evidence/UT-J-01-result.png`
- Verified via the persisted Run History table on `/data` (read-only — did not re-trigger the journey's own backfills, since a live UT-02 job was in flight at the time and the test plan explicitly prohibits overlapping data jobs).
- `2026-05-02 → 2026-05-29`: "28 calendar days · 19 already snapshotted · 9 non-trading", `run-status`="no new snapshots" with neutral (border-border/text-muted) styling — matches J-01's zero-work re-run outcome.
- `2026-05-02 → 2026-05-03`: "2 calendar days · 0 already snapshotted · 2 non-trading" — matches the weekend-only zero-trading-day outcome.
- Both zero-work badges are visually neutral, not the green success color — confirms the "never fabricated success" acceptance criterion still holds.
- Did not re-execute the live click-through this run; the existing golden `runs/goal-session-ops-hardening/journey-scripts/J-01.json` (more thorough — includes the live click/fill sequence) was left untouched rather than overwritten with a weaker read-only replay.

### UT-J-03 — J-03: No per-run range cap (regression)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-49-evidence/UT-J-03-result.png`
- Verified via the persisted Run History table: `2025-06-01 → 2026-07-17` (412 calendar days, spanning >370 days) appears twice with `status` `ok`/`no new snapshots`, "412 calendar days · 283 already snapshotted · 129 non-trading" — the range was accepted (no "date range too large" rejection) and executed to completion both times.
- Existing golden `J-03.json` left untouched for the same reason as J-01 above.

### UT-J-06 — J-06: Pages load only what they need (regression)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-49-evidence/UT-J-06-result.png`
- Loaded `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/regime-lab` — all rendered their correct headings with no error cards, all captured before the backend crash.
- Existing golden `J-06.json` already matches this exact navigation sequence; left unchanged.

---

## Critical Finding — Backend crashed (MemoryError) during the finalize-tail warm, did not recover

**Severity:** High — directly causes the P1 UT-02/UT-05 failures and blocks UT-03/UT-08/J-09.

**Timeline (local host clock):**
- `10:21:10` — UT-02's backfill (`2012-01-05` → `2012-01-05`) started; confirmed `running` immediately, confirmed still `running` at multiple checks through `10:35:xx`.
- Around this same window I also loaded `/research/factor-lab` (UT-07) and `/backtest` (UT-09) and other pages (J-06) — normal, realistic concurrent usage of the app while a backfill runs; nothing in the UI prevents or warns against this.
- `10:36:03.525` — `logs/backend.log`: `ERROR trendora.data_manager: evidence drawdown-expectations warm aborted — memory pressure, stopping remaining claims: MemoryError()`. This is UT-02's **own** finalize-tail phase (`drawdown_expectations_warm`, this iteration's own target) hitting memory pressure — and it aborted **gracefully**, via a caught exception and a clean log line. This part behaved as intended (matches the "warm aborts honestly... never a deadlock" spirit of the existing isolation convention).
- Immediately after (same second-range), two more `MemoryError` tracebacks appear, the second one inside `apps/backend/app/engine/research.py:1051`, `compute_factor_lab_all` → `sorted(obs, ...)` — the code path behind `/research/factor-lab`'s "Factor Lab" overview table that I had loaded for UT-07. This is a **different, less-protected** function than the `_factor_decile_observations`/`_extract_factor_value_from_row` column-projection fix this iteration actually shipped (per the ui-surface-map) — `compute_factor_lab_all` still appears to materialize/sort a large in-memory list.
- ~`10:36:05` — `OpenBLAS error: Memory allocation still failed after 10 retries, giving up.` — a fatal, C-level allocation failure. `logs/backend.log` stops advancing at line 191721 immediately after this line.
- From this point on: `ss -tlnp` shows **no process listening on port 8255**; `ps aux` shows no uvicorn/backend process; every `curl --max-time 3..20 http://localhost:8255/api/health` returns connection failure (`HTTP:000`); the frontend's `readiness-badge` correctly and honestly flips to `data-state="unavailable"` ("Backend unavailable") with a `preflight-banner` `data-verdict="NO-GO"` / "Backend is unavailable — the preflight check could not run."
- I set up a 4-minute automated recovery-check (`curl` polling `/api/health` every 10s) — it timed out with no recovery. Direct manual checks confirmed the backend was still down as late as `10:42:44` (6m39s after the crash), with `logs/backend.log` unchanged (still 191,721 lines) — no restart attempt of any kind occurred during this window.
- Per my instructions I did **not** restart the backend myself.

**Configuration context:** `config.yaml`'s `server.memory_cap_mb` is `8192` (the owner's 2026-07-31 raise from 6144, made specifically after the iter-42 REGRESSION_HALT concurrent-compute OOM — see `docs/goal.md` "Additional binding notes"). This crash is the same failure signature repeating at the raised cap: multiple heavy computations (this iteration's own `drawdown_expectations_warm` finalize phase, plus a concurrently-requested `compute_factor_lab_all`) stacked enough memory pressure to exhaust the 8192 MB ceiling and take the whole process down via an uncatchable native allocation failure, not just the graceful per-phase abort the data_manager code already has.

**Honest attribution:** the FIRST MemoryError (this iteration's own `drawdown_expectations_warm`) was caught and handled gracefully — it did not by itself crash the process. The FATAL crash came from a second, concurrent, less-protected code path (`compute_factor_lab_all`, not part of this iteration's diff) that I triggered by loading `/research/factor-lab` while the backfill's finalize tail was still running. This is realistic concurrent usage — nothing in the UI prevents or warns against opening Factor Lab during a running backfill — and the resulting crash is a genuine, reproducible reliability gap: the finalize-tail warm is not resilient to ordinary concurrent read traffic, and a page unrelated to this iteration's own bounded-memory fix can still bring the entire backend down. This is directly relevant to J-07's "Heavy aggregates never take the service down" acceptance criterion and to AG-10's host-ceiling intent, even though J-07 itself was not in this dispatch's assigned regression lane.

---

## Failed Tests

### UT-02 — Historical-gap backfill reaches a terminal status for its ENTIRE finalize tail (happy path)
**Verdict:** FAIL
**Failure:** Backend crashed (see Critical Finding above) before the job reached a terminal status. The job never got past `running`.
**Evidence:** `reports/qa/goal-ops-hardening-iter-49-evidence/UT-02-stuck-running-precrash.png` (live `running` state, captured shortly before the crash), `UT-02-fail.png` (post-crash "Backend unavailable" state)

**Steps taken:**
1. Navigated to `/data`, set `job-start-date`/`job-end-date` to `2012-01-05` (confirmed not already in `snapshot_dates` via a pre-check), confirmed "Job kind" = "Backfill snapshots", clicked "Start".
2. Confirmed immediately: `job-status` badge showed spinning icon + "running", "Snapshots backfilled" `0/1 dates`.
3. Confirmed via the persisted Run History table's `run-status` badge (spinner + "running") at multiple points through ~14m45s of the run. (Note: the LIVE, same-session `job-status` badge on the Job progress panel is by design session-scoped — its React state is never persisted and is cleared on page navigation per `apps/frontend/app/data/page.tsx`'s own code comments — so once I navigated away to test other independent pages, that specific live widget fell back to a `LastRunSummary`/"from a previous session" view. The persisted Run History table's `run-status` badge is the durable, server-driven equivalent and was used for ongoing tracking instead.)
4. At ~14m53s, the backend crashed (see Critical Finding).

**Expected:** Job reaches a terminal status (`ok`, `no new snapshots`, `partial`, `failed at backfill`, or `failed`) within ~17-18 minutes, comfortably under the 20-minute budget.
**Actual:** Backend process crashed before any terminal status was written; the job remains permanently `running` in the database with no live process to ever update it, and the backend did not come back up during this dispatch.

---

### UT-05 — Backend stays responsive while a historical-gap backfill finalizes (error/resilience)
**Verdict:** FAIL
**Failure:** The readiness badge did not merely show the disclosed brief (~10s) blip — the backend genuinely crashed and `readiness-badge` stayed on `data-state="unavailable"` continuously for 6+ minutes (confirmed down as late as 10:42:44, with a 4-minute automated recovery poll timing out in between).
**Evidence:** `reports/qa/goal-ops-hardening-iter-49-evidence/UT-05-fail.png`

**Steps taken:**
1. Watched the `readiness-badge` from shortly after UT-02's job started; confirmed `data-state="ready"` on every direct in-browser check through the run (roughly the first 14m45s).
2. A secondary curl-based monitor (polling `/api/data`/`/api/health` every 5s, independent of the browser) additionally logged several shorter (~11-30s) connectivity gaps starting around the 2.5-13 minute mark. Given the backend was demonstrably still up and directly `curl`-reachable with a longer timeout at those same moments, I attribute most of these to that monitor's own aggressive 5s timeout colliding with real (but recovering) slow responses under concurrent load, not to confirmed badge failures — noting this honestly as a lower-confidence signal, distinct from the hard, directly-observed crash below.
3. At ~14m53s, directly observed (both via the actual frontend badge in-browser and via direct backend polling) the badge flip to `data-state="unavailable"` / "Backend unavailable" with the preflight banner reading "NO-GO — do not rely on today's board. Backend is unavailable."
4. This state persisted for the remainder of the dispatch (6+ minutes and counting), including through a dedicated 4-minute automated recovery check.

**Expected:** Badge shows `ready` almost the entire time; at most one brief (~10s), self-recovering flip to `unavailable` in an early window is acceptable per the disclosed caveat.
**Actual:** A genuine, sustained (6+ minute, non-recovering within this dispatch) outage — a clear "genuine failure condition" per the test plan's own explicit language ("the badge stays on unavailable for longer than roughly 15 seconds... these WOULD be new problems").

---

### UT-07 — Factor Lab still loads and its existing decile drill-down link still works (regression)
**Verdict:** FAIL
**Failure:** The page itself loaded without an error card (an honest "Still computing" state is by-design, not a bug), but the underlying `compute_factor_lab_all` computation threw a `MemoryError` that was the proximate trigger for the fatal backend crash described in the Critical Finding. The decile table never rendered and the "N=" drill-down link was never reachable.
**Evidence:** `reports/qa/goal-ops-hardening-iter-49-evidence/UT-07-fail.png`

**Steps taken:**
1. Navigated to `/research/factor-lab`; page loaded with heading, no error card, and an honest "Still computing — Ns elapsed" panel (documented, expected behavior when the stored result is invalidated by a dataset-version bump — UT-02's in-flight backfill was creating exactly such a bump).
2. Re-checked twice over the next ~2 minutes; each time still "Still computing" (once even having visibly restarted from a lower elapsed-time, consistent with repeated dataset-version bumps from UT-02's ongoing job).
3. Never reached a rendered decile table before the backend crashed (see Critical Finding) — could not attempt the "N=" link click at all.

**Expected:** Page loads without an error card; clicking a decile's "N=" link navigates to `/research/samples?...` with `cohort-summary`/`samples-total` and a member-observation table.
**Actual:** Page loaded cleanly (no error card), but the feature never became usable before the backend crashed — and the specific computation this page triggers was the immediate cause of the fatal `MemoryError`/OpenBLAS crash that took the whole backend down.

---

## Skipped Tests

### UT-03 — Backfilled historical date renders its stored snapshot on Scanner Runs (happy path)
**Verdict:** SKIPPED
**Reason:** Precondition (UT-02 reaching a terminal status) was never met — the backend crashed mid-run and did not recover during this dispatch.

### UT-04 — Job form still blocks Start with an incomplete date range (validation)
**Verdict:** SKIPPED
**Reason:** Backend down for the remainder of the dispatch. Confirmed the `/data` page's job form (including `job-start-date`) does not render at all while the backend is unavailable — only the heading and "NO-GO" preflight banner show — so the validation behavior cannot be exercised.

### UT-08 — A zero-work re-run reads honestly, never as a fabricated success (UX)
**Verdict:** SKIPPED
**Reason:** Precondition (UT-02's backfill completing with `snapshots_created >= 1`) was never met.

### UT-J-04 — J-04: Non-blocking boot with visible status
**Verdict:** SKIPPED
**Reason:** Restarting/killing the backend process is explicitly out of scope for this browser-only QA agent ("never restart or debug services yourself"). Incidental, unplanned evidence: the backend crashed on its own during this dispatch, and the frontend's crashed-state presentation (honest `unavailable` badge + `NO-GO` preflight banner, see UT-05 evidence) matches what J-04 expects for the crashed case — but the restart-timing (≤5s), phase-aware pre-ready polling, persistent logfile, and "job interrupted after backend restart" assertions were not performed.

### UT-J-08 — J-08: Backtest evidence serves from storage only
**Verdict:** SKIPPED
**Reason:** Partially observed (see table) but the full version-bump → refreshing-indicator → re-serve sequence could not be completed before the backend crashed.

### UT-J-09 — J-09: The backend discloses its own background-compute activity
**Verdict:** SKIPPED
**Reason:** Not yet attempted when the backend crashed; `/api/health`'s `background_compute` field was checked opportunistically earlier in the run and read `{"active": [], "recent_outcomes": []}` (idle), but the journey's own trigger step (loading `/backtest` for a historical date with incomplete forward-aggregate evidence) was never executed.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (confirmed HTTP 200 / `readiness: ready` at dispatch start; **crashed at approximately 10:36:05 local time and remained down through the end of this dispatch**, last checked 10:42:44 local, 6m39s post-crash, no recovery)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned profile
- **Test Date:** 2026-08-05
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-49-evidence/`
- **Backend crash log:** `logs/backend.log` (lines ~191510-191721): `drawdown_expectations_warm` graceful memory-pressure abort at 10:36:03.525, followed by an uncaught `MemoryError` in `research.py:1051` (`compute_factor_lab_all`), followed by `OpenBLAS error: Memory allocation still failed after 10 retries, giving up.` — the last line written to the log.
- **Config at time of crash:** `config.yaml` `server.memory_cap_mb: 8192` (owner-raised 2026-07-31 after the iter-42 REGRESSION_HALT).

**Golden replay scripts:** No new/changed scripts written this run. `J-01.json`, `J-03.json`, and
`J-06.json` in `runs/goal-session-ops-hardening/journey-scripts/` were verified consistent with the
persisted/live evidence gathered above and left untouched (each already matches what this dispatch
observed, and each represents a more thorough live-execution check than the read-only verification
this run performed for J-01/J-03). `J-08.json`/`J-09.json` were not touched — their journeys did not
reach a verified PASS this run.
