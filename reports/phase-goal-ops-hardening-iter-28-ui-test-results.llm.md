# Phase goal-ops-hardening-iter-28 — UI Test Results

**Phase:** goal-ops-hardening-iter-28
**Date:** 2026-07-27
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: all P1 tests pass -->

**Overall:** 8/9 tests passed (1 skipped — P3, unreachable in this seeded environment)

---

## Scope

Lean-mode dispatch (per `docs/phases/goal-ops-hardening-iter-28.md` and the dispatch prompt): browser-verify
EXACTLY J-05, J-06, J-07, J-08 by re-running the iter-27 UT-01..UT-09 plan
(`reports/phase-goal-ops-hardening-iter-27-ui-test-plan.md`) against the UNCHANGED iter-27 build (this
iteration's only product change is a byte-identical drift-report path relocation, already confirmed by the
coherence auditor to touch no Data Contract value). J-01, J-03, J-04, J-09 are verified separately by
deterministic golden replay and are explicitly OUT of this run's scope — not tested here, no verdict claimed
on them.

Mapping (per iter-28 spec's Definition of Done / Test-first contract):
- **J-05** (TC-1..TC-4) ⊃ UT-01, UT-02, UT-03, UT-04
- **J-06** (TC-9) ⊃ browser-verified 11-page load sweep (the exact steps in
  `runs/goal-session-ops-hardening/journey-scripts/J-06.json`, already fixed this iteration by the developer
  to assert stable Dashboard content instead of a preflight-derived string)
- **J-07** (TC-5, TC-8) ⊃ UT-05, UT-08
- **J-08** (TC-6, TC-7) ⊃ UT-06, UT-07

Two never-scanned historical trading days were freshly selected for this run (avoiding the lesson's banned
`2011-03-10` / `2015-09-09`, and also avoiding `2025-05-15` / `2026-05-02..29`, which a prior interrupted
browser-qa/dev-verification attempt this same iteration had already consumed — confirmed absent-then-present
via `GET /api/runs` before use):
- **2018-02-15** — J-05's single-day backfill target (unsnapshotted; month 2018-02 had only one prior
  snapshot, 2018-02-01)
- **2018-03-15** — UT-06/UT-07/UT-08's concurrent-race date (unsnapshotted; month 2018-03 had only one prior
  snapshot, 2018-03-01)

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | Aggregates precomputed at ingest, never on the fly | happy-path | P1 | Single-day backfill (2018-02-15) persists snapshot + aggregates; `/scanner-runs` and market phase serve from storage; cold restart serves coverage from storage within budget with no whole-table prefill; `/api/health` stays responsive during ingest | See "J-05 detail" below | PASS | `J-05-scanner-run-2018-02-15.png`, `J-05-cold-data-restart.png` |
| UT-J-06 | Pages load only what they need | regression | P1 | All 11 pages in the golden script (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/event-study`) load and each step's `expect.text` appears | See "J-06 detail" below | PASS | `J-06-dashboard-market-regime.png` |
| UT-J-07 | Heavy aggregates never take the service down | smoke/ux | P1 | `/backtest` latest view loads clean (smoke baseline); stale-coverage notice reads calm/factual, never alarm styling (UX regression guard) | See "J-07 detail" below | PASS | `UT-05-backtest-latest.png`, `UT-02-UT-08-stale-coverage.png` |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | error/regression | P1 | Two concurrent `/backtest` requests for the SAME never-scanned historical date both return 200 with zero ASGI exceptions; an already-scanned historical view renders consistently with what the race established | See "J-08 detail" below | PASS | `UT-06-backtest-2018-03-15.png`, `UT-07-backtest-already-scanned.png` |
| UT-04 (J-05's P3 sub-case) | Coverage panel "not yet computed" state | regression | P3 | Only reachable on a genuinely fresh-install DB with zero `CoverageSnapshot` rows | This session's seeded dev database cannot exhibit this state (confirmed: 1872+ snapshot rows exist) — no fresh-install environment available to point the frontend at | SKIP | none (documented-only, per iter-27's own test plan) |

**P1 tests:** UT-J-05, UT-J-06, UT-J-07, UT-J-08 — all PASS. Browser QA Verdict is PASS.

---

## J-05 detail — Aggregates are precomputed at ingest, never on the fly

1. **Backfill submission (step 1):** On `/data`, set Start date / End date to `2018-02-15` (confirmed
   unsnapshotted beforehand via `GET /api/runs`), kind `backfill` (default), clicked Start. Job id 190
   started (`dates_total: 1`).
2. **Completion + aggregate disclosure (step 2b):** Polled `GET /api/data` every 15s; job completed after
   6m41s wall time (`started_at` 18:48:26 → `finished_at` 18:55:08), `status: "ok"`, `snapshots_created: 1`.
   The persisted run record's `aggregates_refreshed` field lists exactly: `latest_snapshot`, `coverage`,
   `membership_timeline`, `market_phase`, `forward_aggregates`, `research_hot_keys`, `drawdown_expectations`
   — matching the acceptance's named inventory (latest-date snapshot, coverage payload, membership timeline,
   market phase, research hot-key caches) plus two additional consistently-refreshed items.
3. **Storage-served evidence (step 2a):** `GET /api/runs` immediately listed a new run (`run_id: 1872`,
   `asof_date: "2018-02-15"`, `regime: {"label": "Risk-on", "score": 75.13}`) with no perceptible delay,
   consistent with a stored value rather than a compute-on-read. Navigated to `/scanner-runs/1872` in the
   browser: the leaderboard rendered real stored ranked names (NFLX, KDP, MSI, NOW, BA, PNC, AMZN, CSCO,
   MSCI) — not blank, not fabricated.
4. **Cold restart (step 3):** Stopped the backend (`kill -15`, confirmed port free), relaunched via
   `scripts/start-backend.sh` (never `dev.sh`). Once `readiness: ready`, fired the FIRST `GET /api/data`
   since restart: **HTTP 200 in 0.074 s** (committed budget ≤ 1.5 s) with `coverage_status: "current"`,
   `universe_count: 540`, real `price_start`/`price_end` — not the all-zero/"not yet computed" sentinel.
   Backend RSS immediately after this cold hit: **~1.18 GB** (`ps` `RSS` column), consistent with
   iter-27's AG-3 fix (`coverage_from_storage`) — historically the old uncached whole-table prefill path
   spiked RSS to 1.8–6.8 GB on a cold `/api/data` hit (`reports/perf-budgets.md`); this run shows no such
   spike. The frontend `/data` page loaded the SAME real coverage instantly on first paint (screenshot:
   `J-05-cold-data-restart.png`).
5. **Health during heavy ingest (step 4):** During the entire 6m41s backfill job (step 1-2), `GET
   /api/health` was polled continuously and returned **HTTP 200 on every single poll**, no timeout, no
   degraded/unreachable state.
6. **No new backend error:** `logs/backend.log` from the current boot banner (`2026-07-27T18:29:53Z`)
   forward shows **zero** `Exception in ASGI application` and **zero** `MemoryError` lines through this
   entire test (verified by line-count diff against the banner) — the pre-existing `research.py:215`
   MemoryError signature that appears elsewhere in the log file is from an OLDER boot, before this banner,
   confirmed by line-number position, not something this run's activity triggered.

## J-06 detail — Pages load only what they need

Executed all 11 steps of `runs/goal-session-ops-hardening/journey-scripts/J-06.json` (already fixed this
iteration by the developer: step 1's assertion moved off the preflight-derived `"DEGRADED"` string onto
stable Dashboard content, `"Market Regime"`) directly via Chrome MCP, using `await_text` before each
extraction (first-paint captures on this app are client-fetch skeletons — `animate-pulse` placeholders — so
each page needs its data fetch awaited before the text check is meaningful):

| Step | URL | Expected text | Result |
|---|---|---|---|
| 1 | `/` | `Market Regime` | Found — page's preflight state was `GO` this run (proving the OLD `"DEGRADED"` assertion was incidental/fragile exactly as diagnosed; the new assertion holds regardless of preflight verdict) |
| 2 | `/stocks` | `TRV` | Found |
| 3 | `/stocks/AAPL` | `$304.89` | Found |
| 4 | `/sectors` | `HACK` | Found |
| 5 | `/themes` | `Cybersecurity` | Found |
| 6 | `/data` | `Data Manager` | Found |
| 7 | `/evidence` | `certified-claims ledger` | Found |
| 8 | `/scanner-runs` | `2026-07-17` | Found |
| 9 | `/backtest` | `Time-machine` | Found |
| 10 | `/watchlist` | `JNJ` | Found |
| 11 | `/research/event-study` | `Setup & Pattern event study` | Found |

All 11/11 steps pass. No console errors, no "Backend unavailable" card on any page. This directly confirms
TC-9: the deterministic golden replay of the fixed `J-06.json` will hold end-to-end (I independently
reproduced every one of its steps live in the browser this run).

## J-07 detail — Heavy aggregates never take the service down

- **UT-05 (smoke baseline):** `/backtest` at the default (latest) view loads with heading "Backtest", badge
  `data-testid="asof-indicator"` reading exactly `Latest` (not historical), both the "As-of scan summary" and
  "Forward-test scorecard" headings present, no console error, no "Backend unavailable" card.
- **UT-08 (UX guard):** With the coverage panel in the "stale" state (see J-08/UT-02 below), the stale
  notice (`data-testid="coverage-stale-notice"`) carries CSS classes `border-b border-border bg-surface-2
  px-4 py-2 text-xs text-text-muted` — the SAME muted/neutral tone class (`text-text-muted`) used by the
  panel's other plain descriptive captions. By contrast, the panel's own amber/warning-tone figure
  ("Backfill gaps") uses a visibly distinct `text-warn` class. This confirms the stale notice is NOT styled
  as an alarm — no red error tone, no amber warning tone, exactly the acceptance's "honest status, never
  hype" requirement. Reached in exactly 1 click from Dashboard (the "Data Manager" sidebar link) and 0
  further scroll — it sits directly under the "Dataset coverage" title, above the metric grid, matching the
  test's discoverability requirement.

## J-08 detail — Backtest evidence serves from storage only — never a cold recompute on request

- **UT-06 (concurrent race, the AG-8 fix):** Confirmed `2018-03-15` absent from `GET /api/runs` immediately
  before the test. Fired two concurrent `GET http://localhost:8255/api/backtest?as_of=2018-03-15` requests
  (backgrounded via `setsid nohup` + polled, since the request legitimately runs the create-once historical
  scan and forward-return compute — this took ~273 s, well beyond a naive foreground wait, so the requests
  were dispatched in the background and polled in bounded loops per the coordinator's operational
  guidance). **Both returned HTTP 200** (273.484 s and 273.511 s — 27 ms apart, genuinely concurrent).
  `grep -c "Exception in ASGI application"` over the exact log line-range spanning both requests = **0**.
  A new `ScannerRun` (`run_id: 1873`) was created exactly once (no duplicate). Navigating the frontend to
  `/backtest?asof=2018-03-15` (only after the backend-direct race, per the frontend's `?asof` validation
  behavior) showed the `Viewing as-of 2018-03-15 (historical)` badge (`data-testid="backtest-asof"`), and
  both the full-page screenshot and a DOM-text cross-check confirmed the "As-of scan summary" and
  "Forward-test scorecard" headings plus real per-horizon figures (1d: `+0.09% n=20`), matching the live
  `GET /api/backtest?as_of=2018-03-15` JSON's `mean_return: 0.0008558359312401065` for the same horizon. The
  screenshot's md5 differs from UT-05's latest-view screenshot, confirming it is a real, distinct capture,
  not a blank/frozen frame.
- **UT-07 (already-scanned regression guard):** Re-navigated to the SAME `/backtest?asof=2018-03-15` URL
  (now an already-scanned date per UT-06). The badge and full scorecard rendered **identically** to UT-06's
  values (Actionable 0 / Breakout-watch 52 / Pullback-watch 0; scorecard 1d/5d/10d/20d/60d unchanged).
  **Note on screenshot md5:** `UT-06-backtest-2018-03-15.png` and `UT-07-backtest-already-scanned.png` are
  byte-identical (same md5). Per the plan's own screenshot-blindness caution, an identical hash between two
  *different* test steps would normally be flagged as a possible blank/frozen capture — but here it is the
  CORRECT and expected outcome: UT-07's entire point is that the SAME as-of, now already-scanned, renders
  the SAME stored values with nothing having changed in between (no ingest ran). This was independently
  cross-checked against the DOM text (identical scorecard figures) and the live API (unchanged
  `mean_return`), not inferred from the screenshot alone.

## Coverage-panel state transitions (UT-02/UT-03, informing J-05/J-07/J-08's shared precondition)

- **UT-01 (baseline, before any state change):** `/data` loaded cleanly, "Data Manager" heading, "Dataset
  coverage" panel visible with no scroll, no console errors, no "Backend unavailable" card.
- **UT-02 (stale disclosure):** After UT-06 bumped the dataset version via a request-path historical
  `ScannerRun` with no ingest finalize, `GET /api/data`'s `coverage.coverage_status` read `"stale"` with
  `stale_dataset_version: "r1872-rc1872-b2026-07-22-bc3301686-h200"`. The frontend showed the exact expected
  notice: `Coverage as of a prior scan (version r1872-rc1872-b2026-07-22-bc3301686-h200) — refreshes on the
  next data job` under `data-testid="coverage-stale-notice"`, with "Price history" still showing the real
  `1996-01-02 → 2026-07-22` range (not `— → —`) and "Universe (as of date)" still `540` (not `0`).
- **UT-03 (current-state regression guard):** To restore "current" state, submitted a fresh single-day
  backfill for the already-snapshotted latest date (`2026-07-22`) rather than the full "Rebuild snapshots
  for current universe" flow (that flow clears and recomputes ALL ~1872 historical snapshots from scratch —
  a multi-hour, host-resource-heavy operation disproportionate to this regression check; a zero-work
  single-day backfill exercises the identical finalize-hook coverage-refresh path at a fraction of the
  cost). **Note:** an earlier click on the rebuild confirmation modal's header close (✕) button was
  misidentified as the confirm action and actually cancelled that dialog — no rebuild job was started by
  that click; the single-day-backfill approach below is what actually produced the "current" state. Job 191
  completed (`status: "ok"`, `already_snapshotted: 1`, `aggregates_refreshed`: `[coverage, membership_timeline,
  forward_aggregates, research_hot_keys, drawdown_expectations]`). Afterward, `coverage_status` read
  `"current"`, the stale notice was absent (0 occurrences of `coverage-stale-notice` in the DOM), and the
  same real figures (universe 540, price range unchanged) rendered.
- Across this entire coverage-state-transition sequence, `logs/backend.log` recorded zero new ASGI
  exceptions and zero new MemoryErrors (verified against the current boot banner), and `GET /api/health`
  remained HTTP 200 throughout.

---

## Skipped Tests

### UT-04 — Coverage panel's "not yet computed" state (J-05's P3 sub-case)
**Verdict:** SKIPPED
**Reason:** Per the iter-27 UI test plan's own documentation, this state is "only reachable on a genuinely
fresh-install database — this session's seeded dev database cannot exhibit it." Confirmed: this instance has
1872+ persisted `CoverageSnapshot`-backed runs; no fresh-install/empty-DB environment was available to point
the frontend at during this run. P3 priority, does not affect the PASS verdict (P1 requirement only).

---

## Golden replay scripts

Per the goal-mode lean-mode instructions, a deterministic replay script was written/confirmed for every
journey verified PASS this run, in `runs/goal-session-ops-hardening/journey-scripts/`:

- **`J-05.json`** — REWRITTEN this run to use the freshly-verified `2018-02-15` / `scanner-runs/1872` values
  (the previous script referenced `2025-05-15` / `run 1436`, a date this run confirmed is now already
  consumed from a prior session — the new script reflects data this run independently verified end-to-end).
- **`J-06.json`** — already fixed by the developer this iteration (step 1 → `"Market Regime"`); independently
  reproduced all 11 steps live in the browser this run (see J-06 detail above); no further edit needed.
- **`J-07.json`** — reviewed against this run's live verification (`/backtest` → "Time-machine", `/` →
  "Ready", `/data` → "Data Manager"); all three assertions confirmed still hold; no edit needed.
- **`J-08.json`** — reviewed against this run's live verification (`/backtest` → "Forward-tested evidence",
  confirmed present on the latest-view page); assertion confirmed still holds; no edit needed.

(J-01/J-03/J-04/J-09's golden scripts are out of this run's scope — not touched, not re-verified here.)

---

## Anti-goal / regression check

- No new `Exception in ASGI application` or `MemoryError` line appeared in `logs/backend.log` across this
  entire test session (verified against the current boot banner) — the pre-existing `research.py:215`
  MemoryError signature referenced in the iter spec's OUT OF SCOPE section is from an older boot, not this
  run's activity.
- No AG-1/AG-2/AG-4/AG-6 concern: no proven/confident claim was rendered anywhere touched by these tests; the
  stale-coverage notice and historical-backtest badge are both explicitly factual, non-hype disclosures.
- No AG-3 concern: every displayed figure cross-checked against its live API JSON matched (scanner-run
  regime/leaderboard, backtest scorecard per-horizon returns, coverage payload fields).
- No AG-5 concern: all forward-return figures observed are for as-of dates in the past relative to the
  seed's latest date (2026-07-22); no lookahead behavior was exercised or observed.
- No AG-8 concern: the cold `/api/data` RSS (~1.18 GB) shows no whole-table-prefill spike; `/api/health`
  never became unresponsive during the ~6m41s and ~4m33s heavy ingest/scan operations triggered by this
  test run.
- No AG-9/AG-10 concern: all ingest activity was triggered through the product's own `/data` UI and its
  backend API (no external network call), and the backend was running under `scripts/start-backend.sh`
  (host-guard caps applied) for the entire session.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-27
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-28-evidence/`
- **Backend restarted once mid-run** (for J-05 step 3's cold-boot check) via `scripts/start-backend.sh`
  (never `dev.sh`); frontend was never restarted.
