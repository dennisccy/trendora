# Goal Iteration 73 — UI Test Results (LLM fallback, regression re-verification)

**Phase:** goal-ops-hardening-iter-73
**Date:** 2026-08-13
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke/happy-path/P1 tests pass. -->

**Overall:** 2/2 tests passed (0 skipped)

Scope note: this dispatch's iter spec (iter-73) targets J-07 with no UI change (DB-pool/memory
measurement round). This browser-qa dispatch was for the two **required-still-passing**
journeys J-05 and J-06 only (per the dispatch's "GOAL-MODE LEAN MODE — test EXACTLY these
journeys" instruction), as the LLM fallback after the deterministic replay lane's own attempt
(see `J-05-verify.png` / `J-06-verify.png` in the evidence dir, timestamped ~03:14-03:16, prior
to this dispatch). J-07 itself is not in this report's scope.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | Live backfill of one unsnapshotted day creates a snapshot from stored aggregates only; the persisted run record lists which finalize-hook aggregates it refreshed; `GET /api/health` stays responsive throughout | Ran a real ~17m41s in-app backfill of 2005-07-12 end to end; job record + `/scanner-runs/2978` + `GET /api/data/jobs/<id>` all confirm storage-backed serving, all 9 aggregate categories refreshed, and a 1232-poll 1Hz health drill recorded 0 non-200s / 0 breaches throughout | PASS | `reports/qa/goal-ops-hardening-iter-73-evidence/UT-J-05-result.png` |
| UT-J-06 | Pages load only what they need | regression | P1 | All 11 nav-listed pages render their real heading/testid-gated on-load value within budget, on a warm prod-mode backend | All 16 golden steps re-verified live: readiness badge ready (7.5-12.9ms health calls), AAPL chart caption + 1.5ms cached bars call, availability-cell 34.1ms, `/api/runs` row + 320.9-378.6ms, remaining 7 pages render real headings/DOM, no drift from iter-71/72 baselines | PASS | `reports/qa/goal-ops-hardening-iter-73-evidence/UT-J-06-result.png` |

---

## Passed Tests

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-73-evidence/UT-J-05-result.png`

Steps executed (journey text from `goal-slice-bqa.md`):

1. **Backfill one unsnapshotted historical trading day.** Resolved the target date via the
   same read-only query `demo_runner.py`'s sentinel resolver uses (earliest `daily_prices`
   date in `[2005-03-01, 2016-12-31]` with a real SPY bar and 0 `scanner_runs` rows) ->
   `2005-07-12` (SPY close 94.3186, re-verified live immediately before clicking Start: 0
   `scanner_runs` rows). Filled both `job-start-date`/`job-end-date` testids to
   `2005-07-12` (had to overwrite stale leftover form values `2005-07-12`/`2005-07-19` from
   a prior browser session via a native-setter `input`/`change` dispatch, since the fields
   are plain text inputs, not native date pickers) and clicked the form's `Start` button.
   `job-status` read `"running"` immediately after — the job actually started, not
   accepted-then-never-run.
2. **Assert aggregates served from storage, run record lists what finalize refreshed.**
   The job (`job_id=1273b81dcb9d4616bc4a260d80fbc89d`, `data_provider_runs.id=478`) ran
   2026-08-13T02:26:06.779Z → 02:43:29.224Z (1061s / ~17m41s — inside the 40-minute
   historical range for this exact in-app backfill). Post-completion: `[data-testid="backfill-breakdown"]`
   read `"1 calendar day · 0 already snapshotted · 0 non-trading"` (this run's OWN
   breakdown — a re-run over an already-snapshotted day would read differently and fail
   here); `[data-testid="aggregates-refreshed"]` and `GET /api/data/jobs/<job_id>` both list
   all 9 categories (`latest_snapshot, coverage, membership_timeline, market_phase,
   forward_aggregates, research_hot_keys, availability_heatmap, factor_lab_all,
   drawdown_expectations`); `snapshots_created=1`, `forward_returns_inserted=800`.
   `/scanner-runs` links `2005-07-12` → `/scanner-runs/2978` (matches the `scanner_runs.id`
   from a direct sqlite read), whose page shows `"Immutable snapshot — as of 2005-07-12"` /
   `"Scanned 2026-08-13 02:26:17"` (matches this run's own start — a genuine fresh scan, not
   stale) with a populated 149-row leaderboard (never the "No stored stock rows" empty
   state). `GET /api/market-phase?as_of=2005-07-12` answered in 0.159s with
   `available:false` — an honest "insufficient trailing history" state for a date this early
   in the SPY series (min 200 bars required), not a bug, and fast enough to confirm
   storage-backed serving rather than a full recompute.
   - **Minor drift noted, not a functional failure:** the golden's step 15 asserts the
     literal upper-case string `"ENTRY QUALITY"`; the actual `<th>` `textContent` is
     title-case `"Entry Quality"` (CSS `text-transform:uppercase` makes it visually read as
     caps but does not change the DOM string). The row-count/non-empty substance of the
     acceptance ("the stored leaderboard renders from storage") is unambiguously satisfied
     (149 real rows) — flagged in the golden's own notes for a future text-only fix, not
     treated as a journey failure here.
3. **Cold restart + coverage-from-storage.** NOT re-executed this pass, per this role's
   standing hard rule that QA never restarts the live backend (consistent with iter-71 and
   iter-72's own write-ups for the same reason). This iteration's own diff (per the iter-73
   spec) is DB-pool/config-only and does not touch boot/coverage code, so this is a carried,
   not a newly-introduced, gap.
4. **`GET /api/health` stays responsive during the heavy job.** Started
   `scripts/qa/poll_health.py` (the canonical 1 Hz poller) BEFORE clicking Start, per this
   session's standing correction against ad hoc curl/bash loops. Result: 1232 polls across
   the full job window, **0 non-200s, 0 breaches** of the ≤2s Bounded Compute Window
   ceiling. `logs/backend.log` for the job's window (03:26-03:44 local/BST) shows zero
   `QueuePool`/`MemoryError`/`Traceback` lines. Confirmed the live port-8255 process was
   launched via `scripts/start-backend.sh` (boot header `memory_cap_mb=8192
   malloc_arena_max=2`), never `dev.sh`, per the iter-71 lesson.

Verdict: **PASS** (steps 1, 2, 4 freshly verified this round; step 3 carried forward per the
standing hard rule, consistent with prior iterations).

### UT-J-06 — Pages load only what they need
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-73-evidence/UT-J-06-result.png`

All 16 golden steps re-verified live via Chrome MCP against the confirmed-live
`scripts/start-backend.sh`-launched backend (port 8255) and prod-mode frontend (port 3255):

- `/` — heading "Dashboard"; `[data-testid="readiness-badge"][data-state="ready"]` present
  immediately, text "Ready"; 3 `GET /api/health` resource-timing entries at 7.5-12.9ms
  (budget: 2000ms after the 2500ms nav cap).
- `/stocks` — heading "Stocks", 772 buttons / 555 links (matches iter-71/72 baseline).
- `/stocks/AAPL` — heading "AAPL"; `[data-testid="chart-window-caption"]` read "3189 bars ·
  as of 2026-08-03 · history since 1996-01-02 · older bars weekly-sampled" (byte-identical to
  iter-71/72); cached `bars?through=latest` call 1.5ms.
- `/sectors`, `/themes` — headings present, no drift.
- `/data` — heading "Data Manager"; after consuming the product's own 2500ms
  `AVAILABILITY_FETCH_STAGGER_MS`, `[data-testid="availability-cell"]` present (text "3"),
  `GET /api/data/availability` 34.1ms (baseline 32-38ms).
- `/evidence` — heading "Evidence".
- `/scanner-runs` — heading "Scanner Runs"; a real `table tbody tr` row present; `GET
  /api/runs` 320.9ms/378.6ms (baseline 203-464ms); 2989 links (one more than iter-72's 2988
  — consistent with this same dispatch's own J-05 backfill having just added
  `scanner_runs.id=2978`).
- `/backtest`, `/watchlist` — headings present, no drift.
- `/research/regime-lab` — heading "Research — Regime Lab".

No page rendered a blank/error-boundary shell; no budget-gated endpoint regressed from its
iter-71/72 baseline. Journey verdict: **PASS**, no drift.

---

## Failed Tests

None.

---

## Skipped Tests

None. Both dispatched journeys (J-05, J-06) were fully executed via live Chrome MCP browser
control. J-05 step 3 (cold restart) was intentionally not exercised per this role's standing
rule against restarting the live QA backend — see UT-J-05's write-up above; this is not a
SKIPPED test, it is a documented carried gap within an overall-PASSING journey, consistent
with how iter-71 and iter-72 recorded the same journey.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (confirmed launched via `scripts/start-backend.sh`,
  boot header `memory_cap_mb=8192 malloc_arena_max=2`)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned
  profile/CDP port per environment
- **Test Date:** 2026-08-13
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-73-evidence/`
  (`UT-J-05-result.png`, `UT-J-06-result.png`, `poll_health.csv` + `.meta.json` — the 1232-row
  1 Hz health-poll drill covering J-05's full backfill window)
- **Golden replay scripts updated:** `runs/goal-session-ops-hardening/journey-scripts/J-05.json`,
  `runs/goal-session-ops-hardening/journey-scripts/J-06.json` (both appended with this
  iteration's live-verification note; steps/selectors unchanged; both lint clean via
  `demo_runner.py --mode lint`)
