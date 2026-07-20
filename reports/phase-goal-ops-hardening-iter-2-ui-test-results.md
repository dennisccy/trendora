# Phase goal-ops-hardening-iter-2 — UI Test Results

**Phase:** goal-ops-hardening-iter-2
**Date:** 2026-07-19 / 2026-07-20
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 11/11 tests passed (0 skipped) — 9 test-plan cases (UT-01…UT-09) + 2 goal-mode regression journeys (J-01, J-03)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/data` loads without errors | smoke | P1 | Heading + subtitle visible; 7 coverage tiles populated (no undefined/NaN); form, Job progress panel, Run history table visible; no error card | "Data Manager" heading + subtitle rendered; all 7 tiles showed real values (Price history 1996-01-02→2026-07-17, Universe 540, Candidate universe 122, Symbols 590, Trading days 5380, Snapshot dates 758, Backfill gaps 4622); form/panels/table all visible; no "Backend unavailable" card; no console errors | PASS | `reports/qa/goal-ops-hardening-iter-2-evidence/UT-01-result.png` |
| UT-02 | Backfill completion shows Refreshed line, live + persisted | happy-path | P1 | "Refreshed: …" line appears live beneath the breakdown line and identically after reload | Ran a fresh single-day backfill on a genuine gap date (2025-05-30): status "ok", live panel showed "Refreshed: latest snapshot, coverage, membership timeline, market phase, research hot keys" directly under "1 calendar day · 0 already snapshotted · 0 non-trading"; reloaded page — identical text persisted in the Run history row's Snapshots column | PASS | `reports/qa/goal-ops-hardening-iter-2-evidence/UT-02-live.png`, `UT-02-result.png` |
| UT-03 | Persisted run history renders with no session job started | regression | P2 | Fallback shows the persisted run's status/message/breakdown (not the "no job started" placeholder); Refreshed line absent for a pre-iteration run | Before starting any job in-session, panel showed "backfill job · 2012-01-01 → 2013-06-01 · from a previous session" with its breakdown line rendering normally; the "Refreshed:" line / `aggregates-refreshed` testid was completely absent (0 occurrences) — correctly, since that run predates this iteration's field | PASS | `reports/qa/goal-ops-hardening-iter-2-evidence/UT-03-before.png` |
| UT-04 | Cold restart serves coverage instantly, unchanged numbers | happy-path | P1 | Tiles populate well under a second; all 7 values identical to pre-restart | Restarted the backend via `scripts/start-backend.sh` (kill + relaunch, same env). `GET /api/data` measured 0.086–0.088s across 3 consecutive calls immediately after restart (vs. the iteration's own documented ~9–10s pre-fix baseline); all 7 coverage values identical before/after (540 / 122 / 590 / 5380 / 759 / 4621 / 1996-01-02→2026-07-17); readiness badge read "Ready"; no spinner hang, no error card | PASS | `reports/qa/goal-ops-hardening-iter-2-evidence/UT-04-result.png` |
| UT-05 | As-of switcher shows real numbers for older dates | regression (AG-3-critical) | P1 | Older dates show genuine non-zero numbers matching the engine, not a false-empty panel; returning to Latest restores original values | Selected 2015-04-01 → Universe tile read 360 (verified byte-identical to a direct `GET /api/data?as_of=2015-04-01` call); stepped back to 2015-01-16 → Universe read 354 (matched direct API call exactly), with a distinct, real Universe-resolution breakdown (76 below-min-history, 96 below-min-liquidity, etc. — plausible for an early date); returned to Latest via the "Latest" chip → all 7 tiles matched the originally recorded Latest values exactly. (One transient observation, not a defect: the very first paint immediately after a click briefly showed the previous date's numbers while the async re-fetch was in flight, then self-corrected within ~1–2s on every trial — normal stale-while-revalidating behavior, not the false-empty-zero bug this test guards against.) | PASS | `reports/qa/goal-ops-hardening-iter-2-evidence/UT-05-older-date.png`, `UT-05-result.png` |
| UT-06 | Brand-new/never-ingested DB shows honest empty state, no crash | error | P2 | Zero-row `coverage_snapshot` state renders honest zeros (never a crash); background warm-up fills in real values automatically | Stood up an ISOLATED backend+frontend pair (new ports, `TRENDORA_CONFIG` pointed at a brand-new empty sqlite file) so the shared pipeline DB was never touched. Immediately after boot (readiness "Initializing… history 51/89"): Price history "— → —", Universe 0, Symbols 0, Trading days 0, Snapshot dates 0, Backfill gaps 0 with "Every trading day with bars already has an immutable snapshot — no backfill gaps."; Candidate universe correctly showed a real non-zero 122 (config-sourced, not DB-sourced) — exactly per the test's own carve-out. No crash, no blank screen, no "Backend unavailable" card. After warm-up completed (readiness "Ready", ~2 min total incl. one-time seed load), reload showed full real values with no manual job run: Universe 541, Symbols 590, Trading days 5369, Snapshot dates 90, Backfill gaps 5279, Price history 1996-01-02→2026-07-01. Isolated instance torn down cleanly afterward; shared pipeline pair (8255/3255) confirmed undisturbed by this sub-test in isolation (see QA Process Note below for a related side effect and its fix) | PASS | `reports/qa/goal-ops-hardening-iter-2-evidence/UT-06-empty-state.png`, `UT-06-warmed-state.png` |
| UT-07 | "Refreshed" line never appears for fetch/expand or interrupted runs | validation | P2 | No "Refreshed:" line and no breakdown line for a `fetch` run; none for an interrupted run either | Ran a fresh "Fetch EOD prices" job (2026-07-17→2026-07-17): reached status "partial" (589/591 ok, 2 failed), `aggregates_refreshed: null` at the API level, and the DOM row's `textContent` contained no "Refreshed" and no "calendar day" text. Also inspected a persisted "interrupted" row (2012-01-01→2013-06-01) — same absence confirmed | PASS | `reports/qa/goal-ops-hardening-iter-2-evidence/UT-08-result.png` (shows the interrupted row directly under the passing backfill row) |
| UT-08 | "Refreshed" line reads clearly and sits logically | ux | P3 | Plain comma-separated words (no underscores); identical muted small-text style to the breakdown line; no new color/badge/icon | Line read "Refreshed: latest snapshot, coverage, membership timeline, market phase, research hot keys" — no underscores anywhere. Computed style: `className="text-xs text-text-faint"`, byte-identical to the breakdown line's own `"num text-xs text-text-faint"` (same size/color, just without the tabular-number class since it's prose). Sits directly beneath the breakdown line in both the live panel and the Run history row | PASS | `reports/qa/goal-ops-hardening-iter-2-evidence/UT-08-result.png` |
| UT-09 | Other reader pages unaffected by the caching change | regression | P3 | Dashboard's Market Phase card and Scanner Runs list/detail still render correctly | Dashboard: Market Regime 59.12/100 "Narrow leadership", Market Phase & Severity "Pullback" / P(bear) 0.01 — not "Market phase unavailable". Scanner Runs: list included the newly-backfilled 2025-05-30 (no "No scanner runs yet" message); opened the 2025-05-30 detail page — full stored leaderboard rendered (Market Regime 63.61, breadth %, candidate counts, per-stock rows) | PASS | `reports/qa/goal-ops-hardening-iter-2-evidence/UT-09-dashboard.png`, `UT-09-scanner-runs.png`, `UT-09-scanner-run-detail.png` |
| UT-J-01 | (goal.md J-01) Backfill honors the requested range and explains zero-work | regression (goal-mode journey) | P1 | Requested range honored exactly; zero-work outcomes explained and visually distinct from success; persists across reload | Fresh productive backfill on a genuine 3-day gap (2025-05-27→2025-05-29): `dates_total=3`, `snapshots_created=3` — range honored exactly, green "ok" badge. Immediate re-run of the identical range: `snapshots_created=0`, `already_snapshotted=3`, badge read "no new snapshots" (visually distinct: unfilled gray vs. green-outlined "ok") — matches the persisted weekend-only case already in history (2026-05-02→2026-05-03: `dates_total=0`, 2 non-trading) and the persisted full-May re-run (2026-05-02→2026-05-29: 0 created / 19 already-snapshotted / 9 non-trading). `/scanner-runs` lists 2026-05-04, 2026-05-15, 2026-05-29 (all named in the journey); opened 2026-05-15 — full stored leaderboard rendered. Reload confirmed all of the above persisted | PASS | `reports/qa/goal-ops-hardening-iter-2-evidence/J-01-productive-run.png`, `J-01-zero-work-vs-success.png` |
| UT-J-03 | (goal.md J-03) No per-run range cap | regression (goal-mode journey) | P1 | A >370-calendar-day request is accepted (no rejection) and completes | Submitted 2025-06-01→2026-07-17 (412 calendar days, >370): request accepted immediately, no "date range too large" error anywhere in the response; resolved to status "ok", `dates_total=283` (= 412 calendar − 129 non-trading), fully self-consistent breakdown persisted after reload. Confirmed at the config level: `max_range_days` is fully removed from `config.yaml` (explicit comment documenting the removal); `import_chunking.date_window_days: 90` is the only remaining span-safety mechanism | PASS | `reports/qa/goal-ops-hardening-iter-2-evidence/J-03-large-range-accepted.png` |

---

## Passed Tests

All 11 executed tests passed. See the Results Table above for expected/actual detail per test; full narrative evidence below only where it adds context beyond the table.

### UT-02 — Backfill completion shows Refreshed line, live + persisted
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-2-evidence/UT-02-live.png`, `UT-02-result.png`
- This is the iteration's flagship change. Verified byte-for-byte identical "Refreshed: …" text in the live Job progress panel and, after a full page reload, in the Run history table's Snapshots column — proving the value is genuinely persisted server-side (in the run's JSON detail), not a client-only artifact.

### UT-05 — As-of switcher shows real numbers for older dates (AG-3-critical)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-2-evidence/UT-05-older-date.png`, `UT-05-result.png`
- This guards the single highest-risk defect in the phase spec (introduced and fixed within this same iteration, per the dev handoff). Cross-checked every displayed Universe count against a direct `curl .../api/data?as_of=<date>` call for two different historical dates (2015-04-01 → 360, 2015-01-16 → 354) — both matched exactly, confirming the per-date persist + self-healing read for legacy dates works correctly, not just for the current/latest as-of.

### UT-06 — Brand-new/never-ingested database shows an honest empty state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-2-evidence/UT-06-empty-state.png`, `UT-06-warmed-state.png`
- Built a fully isolated backend+frontend pair (separate ports, separate `TRENDORA_CONFIG` pointing at a brand-new sqlite file) specifically so this destructive-by-nature test never touched the shared pipeline database. Confirmed the boot sequence's synchronous `load_seed` step means "brand-new DB" in practice means "daily_prices populated within ~110s, but `coverage_snapshot` genuinely empty" — and the honest-zero state is scoped correctly to exactly the fields sourced from `coverage_snapshot` (Candidate universe, which is config-sourced, correctly stayed real/non-zero throughout).

---

## Failed Tests

None. All 11 tests passed.

---

## Skipped Tests

None. Frontend and Chrome MCP were both available throughout.

---

## Additional Finding (discovered incidentally; not gating this verdict)

**Title:** A `fetch` job that changes bar/symbol counts silently blanks the Dataset coverage panel until the next backfill/rebuild or a backend restart.

**Discovered during:** UT-07 (running a "Fetch EOD prices" job as that test requires).

**Mechanism (confirmed at the code and data level, not just observed):**
- `CoverageSnapshot` rows are keyed by `(asof_key, dataset_version)`; `dataset_version` is a live fingerprint of the dataset (`_membership_dataset_version`, e.g. `r772-rc759-b2026-07-17-bc3299789-h200` — embeds bar count, run count, latest date, history threshold).
- `fetch`-kind jobs are (correctly, per this iteration's own spec) never gated through the ingest finalize hook `_refresh_ingest_aggregates` — only `backfill`/`both`/`rebuild` are.
- My UT-07 fetch job added exactly 1 new bar (589/591 ok, "1 new bars"), which changed `daily_prices` from 3,299,789→3,299,790 rows and distinct symbols from 590→591 — changing the `dataset_version` fingerprint.
- Every existing `CoverageSnapshot` row (verified via direct sqlite3 query: all 4 rows) was still stamped with the OLD `dataset_version`, so the next `GET /api/data` found no matching row for ANY as-of date and correctly-but-surprisingly served the same all-zero honest-empty payload as a brand-new database (Universe/Symbols/Trading days/Snapshot dates/Backfill gaps all 0), even though the underlying dataset is fully populated.
- Confirmed this is not a frontend caching artifact — a direct `curl` to the backend API showed the same zeros.
- Confirmed the self-healing path: restarting the backend (which the boot-time `_warm_coverage_snapshot` safety net treats as "no row exists yet for the current stamp") recomputed and persisted a fresh row within about a minute, restoring correct values (and, correctly, the now-accurate 591 symbol count).

**Why this is worth flagging:** "Fetch EOD prices" is a routine, lower-risk, everyday action (distinct from "Backfill", which does trigger the refresh). An operator running a plain fetch on a long-uptime instance (no restarts, no subsequent backfill) would see the coverage panel go from fully populated to all-zero with no explanation and no path back to correct values except "restart the backend" or "run an unrelated backfill" — neither of which is discoverable from the UI. This is squarely inside this iteration's own headline feature (coverage-from-storage) and touches the same honest-zero-state code path UT-06 exercises, just reached through a different, more mainstream trigger.

**Action taken:** Restored the shared pipeline backend via one restart (confirmed self-healed: `symbol_count` settled at the correct 591) before continuing with the remaining tests. No source files were modified — this is a report-only finding per the QA agent's rules.

**Suggested scope:** Not a P1/blocking regression against anything in this iteration's own test plan (no test case specifies fetch-then-check-coverage), but a strong candidate for a follow-up iteration item: either have `fetch` also refresh `coverage_snapshot` opportunistically when it changes bar/symbol counts, or make `_warm_coverage_snapshot`'s safety net run periodically (not only at boot).

---

## QA Process Note (infrastructure, not a product defect)

While standing up the isolated UT-06 instance, its `next dev -p <isolated-port>` process was launched from the same `apps/frontend` working directory as the shared pipeline frontend, so both processes wrote to the same `.next/` build-cache directory. This clobbered the shared frontend's build manifest for the `/` route (`GET http://localhost:3255/` started returning a genuine 404, confirmed both via `curl` and via the browser) once the isolated instance's own compiler flushed a manifest that never included `/`. Diagnosed via manifest/chunk timestamps, fixed by restarting the shared frontend process with its original command and env (`npm exec next dev -p 3255`, `NEXT_PUBLIC_API_URL=http://localhost:8255`) — confirmed `/` and `/data` both back to HTTP 200 and rendering correctly before continuing. No source files, database, or persisted job history were affected. Noted here for transparency; not a finding about the product under test.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (viewport widened to 1440×900 partway through for evidence legibility; earlier default was 776×488)
- **Test Date:** 2026-07-19 → 2026-07-20 (session crossed local midnight)
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-2-evidence/`
- **Golden replay scripts written:** `runs/goal-session-ops-hardening/journey-scripts/J-01.json`, `J-03.json` (both lint-clean via `demo_runner.py --mode lint`)
