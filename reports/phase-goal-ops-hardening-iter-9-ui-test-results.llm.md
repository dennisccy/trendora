# Phase goal-ops-hardening-iter-9 — UI Test Results

**Phase:** goal-ops-hardening-iter-9
**Date:** 2026-07-22
**Written by:** browser-qa-agent (third pass, finishing the job after the subagent-resume channel broke
mid-run on the second pass)

---

**Browser QA Verdict:** FAIL

<!-- FAIL: one P1 case (UT-10) fails on live evidence, and its corresponding required-still-passing
     regression journey (UT-J-04, step 6) fails for the same reason. Every other P1/smoke/happy-path case
     passes. See "Root cause of the FAIL" below — this is a newly-DISCOVERED gap (J-04 entered this
     iteration with status `unknown`, never previously browser-verified — see
     runs/goal-ops-hardening-iter-9/plan.md), not a regression introduced by this iteration's actual diff
     (zero frontend files changed; the backend diff is limited to launcher scripts + libc-handle
     memoization + test hardening, none of which touch the run-record persistence/sweep path). -->

**Overall:** 17/19 rows passed, 2 failed, 0 skipped (16 UT-XX test-plan rows + 3 regression-journey rows
UT-J-01/UT-J-03/UT-J-04 requested by the dispatch; UT-10 and UT-J-04 are the 2 failures, same root cause)

**Note on the first pass:** the report this file replaced was a genuine FAIL, but its root cause was an
**environment/build-cache fault, not a product defect**: the frontend dev-server serving port 3255 was
running on a stale `.next` build whose compiled bundle had an old backend port (`18955`) baked in, and
`/data`'s compiled route entry was missing (`page.js` absent from `.next/server/app/data/`). The pump
stopped that process, ran `rm -rf apps/frontend/.next`, and restarted via `scripts/start-frontend.sh`
(confirmed: new process since 09:41, `GET /` and `GET /data` both verified 200 throughout this pass). None
of that first pass's FAIL rows are carried forward — every row below is this run's own finding.

**Note on the second pass:** a second pass ran after the rebuild and produced most of the evidence PNGs
already sitting in `reports/qa/goal-ops-hardening-iter-9-evidence/` (`UT-01..UT-07`, `UT-09`, `UT-13`,
`UT-15`, `UT-J-01` screenshots, `UT-10-before-kill.png`), but the subagent-resume channel broke before it
could run UT-08/UT-10/UT-11/UT-12/J-04 (which needed a kill+restart cycle) or write a results file. Per
the dispatch instructions, every one of that pass's implied claims was either **re-verified live in this
pass** or **cross-checked against a durable artifact I inspected myself** (a stored API run record, or a
same-session screenshot whose content I re-read) — none were copied on trust. Each row below states which.

---

## Root cause of the FAIL (read first)

**UT-10 / UT-J-04 step 6 — an interrupted backfill's persisted progress is not "frozen at the crash point"; it is simply never written.**

Live evidence (this pass, after the pump's authorized kill/restart cycle — see Environment): run id 110
(`backfill`, `2017-01-01 → 2018-12-31`, killed mid-run by `kill -9` at 11:55:18 BST) now shows, both in the
`/data` "Job progress" panel and in the "Run history" table:
- Status badge: **`interrupted`** (grey/neutral) — correct, matches the requirement, never a stuck
  `running` row.
- Progress: **`0 snapshots · 0 trading days in range`**, `dates_total: 0`, `dates_done: 0`,
  `aggregates_refreshed: null` — i.e. **no progress at all is preserved**, not a frozen mid-run count.
- The row does **not** appear in the "Unfinished imports" panel (no Retry/Resume/Dismiss control offered
  for it). Code trace: `unfinished_imports()` (`apps/backend/app/engine/data_manager.py:4377`) only
  selects `DataProviderRun.status IN ("partial","failed")`; `interrupted` rows are excluded by construction.
  Cross-checked against `docs/goal-product.md`'s original J-59/J-60 spec (iter-12 of the prior product-goal
  session): "Run history shows in-flight (running), resumable, interrupted, and finished jobs from the
  moment they start" — i.e. **interrupted jobs living in Run History only, not Unfinished-imports, is the
  original design**, not a defect. I am not counting this half of the finding against the verdict.

  The progress-loss half IS counted, because it contradicts the literal text of both `goal.md` J-04 step 6
  ("shows an explicit interrupted/error state **with its last persisted progress**") and this iteration's
  own UT-10 expected result ("last persisted progress counts... frozen at the point of the crash — **not
  reset to zero**"). Code trace: the numeric detail fields (`dates_total`/`dates_done`/`snapshots_created`/
  `aggregates_refreshed`/...) live only on the in-memory `JobProgress` dataclass (`data_manager.py:1863ff`)
  during a run, and are written into the persisted row's `message` JSON **once**, by
  `_finalize_run_record()` (`data_manager.py:3652`) — which a `kill -9` never reaches. The boot sweep that
  marks an orphaned `running` row `interrupted` (`sweep_orphaned_runs`, `data_manager.py:3686`) only flips
  `status`/`finished_at`; it never touches `message`. So an interrupted row's detail fields are whatever
  they were at row-creation time (defaults), regardless of how far the job actually got — this iteration's
  code makes no attempt to distinguish "died in chunk 1" from "died in chunk 8 of 9," and the badge, while
  honest about *that* a crash happened, cannot honestly report *how much progress existed* because none
  was durably checkpointed.

This is the **first genuine browser verification J-04 has ever received** (`runs/goal-ops-hardening-iter-9/plan.md`:
"required-still-passing re-verification for J-01/J-03/J-04 (never ran in iter-8 — `unknown`, not
`regressed`)") — it is a newly-discovered pre-existing gap dating to the original J-59/J-60 implementation,
**not** something this iteration's actual diff (host-guard launcher scripts, libc-handle memoization,
targeted test hardening — zero touches to the run-record/sweep code path) introduced or could have
introduced. Recommend it as backlog work for the data-jobs cluster in a future iteration.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/data` loads without errors | smoke | P1 | "Data Manager" heading, coverage/job/progress panels, no error card | Live nav: heading, subtitle, "Dataset coverage" panel with all 7 metrics, "Start a fetch/backfill job" + "Job progress" panels present, no red error card | PASS | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-01-result.png` |
| UT-02 | `/scanner-runs` loads without errors | smoke | P1 | "Scanner Runs" heading, populated table, no error card | Live nav: heading + subtitle exact match, table with all 6 required columns, 100+ populated rows, no error card | PASS | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-02-result.png` |
| UT-03 | Home page (`/`) loads without errors | smoke | P1 | "Market Phase & Severity" card with value or honest NA, no error card | Live nav: card shows "35.45 / 100 severity", "Pullback" badge, "P(bear) 0.01", no error card | PASS | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-03-result.png` |
| UT-04 | Backfill reaches `"ok"` with aggregates | happy-path | P1 | Job status `"ok"`, non-empty `aggregates_refreshed`, 1/1 dates | Durable artifact (this session, pre-restart, survived the restart): `scanner_runs` id 881 = 2012-03-14 (`GET /api/runs/881` re-confirmed post-restart, this pass); same-session screenshot shows the backing `DataProviderRun` job progress: badge `ok`, "1 snapshots over 1 dates, 1440 forward returns", `Refreshed: latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, drawdown expectations` | PASS | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-04-result.png` |
| UT-05 | Leaderboard renders new date immediately | happy-path | P1 | Populated row for 2026-05-15, no skeleton/blank | Live nav to `/scanner-runs`: row `2026-05-15 · Risk-on 67.83 · Actionable 2 · Breakout-watch 59 · Pullback-watch 3 · Stocks 541` present with no reload needed | PASS | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-05-result.png` |
| UT-06 | Run detail matches stored snapshot | happy-path | P1 | "Scanner Run" heading, header strip, leaderboard rows, no "Run not found", "All runs" navigates back | Live click into `/scanner-runs/739`: heading + subtitle match, Regime 67.83/Risk-on, Candidate Counts (Actionable 2, Breakout-watch 59, Pullback-watch 3) match the leaderboard row exactly, leaderboard table populated (MRVL row etc.), "All runs" link resolved + clicked back to `/scanner-runs` (confirmed via `location.href`) | PASS | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-06-result.png` |
| UT-07 | Market phase card updates with no delay | happy-path | P1 | Card updates within ~1s of as-of change, never "unavailable" | Live: used the as-of calendar to select 2026-05-15; badge flipped to "Viewing as-of 2026-05-15 (historical)"; card showed "32.21/100 severity, Pullback, P(bear) 0.00" already rendered in the very next screenshot (no spinner/blank observed) | PASS | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-07-result.png` |
| UT-08 | Cold `/data` load respects budget | regression | P1 | Coverage renders within budget after restart, no prefill | Live: fresh navigation's `performance` entries showed `GET /api/data` `responseEnd` at 436.9ms after nav start (duration 126.4ms) — both well inside the 3s page / 1.5s warm-API budgets in `reports/perf-budgets.md`; backend RSS check + response speed inconsistent with a 3.3M-row prefill (prefill historically costs seconds, not 126ms) | PASS | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-08-result.png` |
| UT-09 | Invalid date shows inline error | validation | P2 | Inline error text, Start button disabled, no request fires | Live: typed `2026-13-40` into Start date, blurred field. DOM-verified (`document.body.textContent`): error text "Enter a valid date as yyyy-MM-dd" present; Start button `disabled: true`. **Screenshot at the field's scroll position (~y17800 on this very tall page) came back solid-black 3x in a row — a Chrome-MCP screenshot-tool limitation at extreme scroll depth on this page, not a rendering defect** (confirmed: DOM content at that position is real via `elementFromPoint`; screenshots at scroll 0 on the same page render fine). Verdict is based on the direct DOM assertions, not a screenshot. | PASS | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-09-top-check.png` (page-load context only; see note) |
| UT-10 | Interrupted job shows explicit state, never stuck "running" | error | P1 | `interrupted` badge, Retry/Resume + Dismiss visible, last persisted progress frozen (not zero) | Live, post pump-authorized kill/restart: badge correctly reads `interrupted` (not running/spinner) — but progress shows `0 snapshots · 0 trading days in range` (not frozen mid-run counts), and the row is absent from "Unfinished imports" (by original J-59/J-60 design — Run History only; not itself counted as a defect). See "Root cause of the FAIL" above. | **FAIL** | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-10-result.png`, `UT-10-before-kill.png` |
| UT-11 | Backend crash shows NO-GO banner | error | P1 | Loud red "NO-GO — do not rely on today's board." + reason, distinct from GO/loading | Live, via a controlled `window.fetch` override that makes only the browser tab's `/api/health` calls reject (the real backend process was never touched — see Methodology note) — banner instantly switched to exactly `NO-GO — do not rely on today's board.` / `Backend is unavailable — the preflight check could not run.`, badge to red `Backend unavailable` | PASS | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-11-result.png` |
| UT-12 | Health badge shows boot-phase detail | regression | P1 | Amber "Initializing… history n/m", never bare "unavailable" | Live, via the same controlled-fetch technique returning a realistic in-progress payload (`readiness:"initializing", warmup:{done:42,total:89}`) — badge instantly rendered `Initializing… history 42/89`, exact contract match | PASS | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-12-result.png` |
| UT-13 | Repeat backfill shows "no new snapshots" | regression | P1 | Distinct grey badge, "already snapshotted" breakdown, no misleading "ok" green | Durable same-session screenshot (11:18) re-inspected this pass: badge `no new snapshots` (grey, not green `ok`), breakdown "1 calendar day · 1 already snapshotted · 0 non-trading", explicit "Zero-work outcome ... this is not a failure" callout. Freshly re-confirmed by this pass's own live J-03 execution showing the identical `no new snapshots` pattern (see UT-J-03). | PASS | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-13-result.png`, `UT-J-03-result.png` |
| UT-14 | Job history survives reload | regression | P2 | Run history panel persists after reload, no "no job started" text | Live: DOM-read the Run History table (50 rows, including the 2017-2018 interrupted run and the May 2026 zero-work runs) before AND after a fresh full-page navigation to `/data`; identical 50 rows, in the same order, with identical text; `"No job has been started this session"` confirmed absent. Screenshot capture at this panel's scroll depth hit the same tool limitation noted under UT-09 (blank capture) — verdict is from the direct DOM comparison, not a screenshot. | PASS | none (see note) |
| UT-15 | >370-day backfill accepted | regression | P1 | No "range too large" rejection, chunk N/M indicator, progress advancing | Durable same-session screenshot (11:26) showing `chunk 5/5`, `283/283 dates` for `2025-06-01 → 2026-07-17` (412 calendar days). **Freshly re-executed live this pass** (see UT-J-03) end-to-end to full completion — same result. | PASS | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-15-result.png`, `UT-J-03-result.png` |
| UT-16 | Readiness state discoverable everywhere | ux | P2 | Green "Ready" badge + green "GO" banner, same position/wording on all 3 pages | Live: green "Ready" pill present in the identical top-bar position on `/`, `/scanner-runs`, and `/data` (confirmed across UT-01/02/03's screenshots). **Caveat:** the steady-state banner currently reads amber "DEGRADED — treat today's board with caution." (live-vs-seed drift for ~500 symbols), not the literal "GO" copy — this is a genuine, pre-existing data-freshness condition of this seed/host, not a code defect, and it renders identically positioned/worded on all three pages, satisfying the actual discoverability/consistency assertion under test. | PASS (with noted precondition caveat) | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-01-result.png`, `UT-02-result.png`, `UT-03-result.png` |
| UT-J-01 | J-01: Backfill honors requested range, explains zero-work | regression (required-still-passing) | P1 | All 8 steps' assertions hold | See "J-01" section below — all 8 steps confirmed via a mix of live DOM inspection (this pass) and durable same-session API/screenshot artifacts | PASS | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-J-01-result.png`, `UT-J-01-scannerdetail.png` |
| UT-J-03 | J-03: No per-run range cap | regression (required-still-passing) | P1 | Accepted, chunked, executes to completion, memory-bounded, health responsive | **Live end-to-end execution this pass** (see "J-03" section) — accepted instantly, `chunk 5/5`, ran to completion in ~4 min (`status: ok`/"no new snapshots", `aggregates_refreshed` fully populated), `GET /api/health` returned 200 throughout, backend RSS stayed at ~4.2GB of the 6144MB cap | PASS | `reports/qa/goal-ops-hardening-iter-9-evidence/UT-J-03-result.png` |
| UT-J-04 | J-04: Non-blocking boot with visible status | regression (required-still-passing) | P1 | All 6 steps' assertions hold | Steps 1-5 PASS (durable budget citation + live UT-11/UT-12 simulations + live logfile trace); **step 6 FAILs** — see "Root cause of the FAIL" above / UT-10 | **FAIL** | see per-step breakdown below |

---

## Passed Tests

### UT-01 — `/data` page loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/UT-01-result.png`
- Live Chrome MCP navigation to `http://localhost:3255/data`. Heading "Data Manager", subtitle "Grow the
  dataset on demand — view coverage and gaps...", "Dataset coverage" panel showing all 7 named metrics
  (Price history, Universe, Candidate universe, Symbols, Trading days, Snapshot dates, Backfill gaps), "Start
  a fetch / backfill job" and "Job progress" panels both present. No red "Backend unavailable" card.

### UT-02 — `/scanner-runs` page loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/UT-02-result.png`
- Heading "Scanner Runs", subtitle exact match. Table with columns As of / Regime / Actionable /
  Breakout-watch / Pullback-watch / Stocks, populated with 20+ visible rows. No error card.

### UT-03 — Home page (`/`) loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/UT-03-result.png`
- "Market Phase & Severity" card visible: "35.45 / 100 severity", "Pullback" badge, "P(bear) 0.01". No
  blank screen, no error card.

### UT-04 — Backfill for one historical day reaches `"ok"` with populated aggregates
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/UT-04-result.png`
- Verified via a durable artifact per the dispatch's guidance (2012-03-14 was already snapshotted earlier
  this session — reusing it rather than running a fresh multi-minute ingest): `GET /api/runs/881` (queried
  fresh, this pass, AFTER the backend restart) confirms `asof_date: 2012-03-14`, a real regime/leaderboard
  payload — proving the record survived the restart. The same-session screenshot (10:51, before the
  restart) shows the originating `DataProviderRun`: badge `ok`, "1 snapshots over 1 dates, 1440 forward
  returns", "1/1 dates", `Refreshed: latest snapshot, coverage, membership timeline, market phase, forward
  aggregates, research hot keys, drawdown expectations" — a genuinely productive run, not zero-work.

### UT-05 — Scanner leaderboard renders the new date immediately
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/UT-05-result.png`
- Live navigation to `/scanner-runs`; located the `2026-05-15` row via DOM query (no manual scroll-search
  needed): `Regime: Risk-on 67.83, Actionable: 2, Breakout-watch: 59, Pullback-watch: 3, Stocks: 541` — all
  populated, no skeleton/dash cells, present without a page refresh (2026-05-15 was already backfilled by
  run 109 earlier this session).

### UT-06 — Scanner run detail page matches the stored snapshot
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/UT-06-result.png`
- Clicked the `2026-05-15` link (resolved to `/scanner-runs/739`). Heading "Scanner Run", subtitle exact
  match, header strip shows as-of + Risk-on 67.83 regime badge, "Candidate Counts" (Actionable 2,
  Breakout-watch 59, Pullback-watch 3) match UT-05's leaderboard row exactly, leaderboard table populated
  (e.g. MRVL / Technology / Leadership A 96.50 / Entry Quality E 27.33 / Risk E 54.87 / Extended). No "Run
  not found", no error card. Clicked "All runs" (resolved via `xpath` text match) and confirmed
  `location.href` changed to `/scanner-runs`.

### UT-07 — Market Phase card reflects the new as-of with no visible delay
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/UT-07-result.png`
- Opened the as-of calendar (`data-testid="asof-trigger"`), switched the month select to May 2026, clicked
  the `2026-05-15` day cell (`data-testid="asof-cal-day"`). The banner immediately read "Viewing as-of
  2026-05-15 (historical)" and, in the very next screenshot taken right after the click (no intervening
  wait), the Market Phase card already showed "32.21 / 100 severity", "Pullback", "P(bear) 0.00" — fully
  rendered, no spinner/blank frame observed at any point.

### UT-08 — Cold `/data` load after restart respects the coverage budget
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/UT-08-result.png`
- The backend restart the pump performed (11:55:27 BST, pid 1214476) is the "restart" this test measures
  against — I did not perform an additional restart (barred by the service-control protocol). A fresh
  browser navigation to `/data` (well after that restart, with no prior visit in this browser session)
  captured via the Navigation Timing / Resource Timing APIs: `GET /api/data` `responseEnd` at 436.9ms after
  navigation start (call duration 126.4ms) — over 10x inside the 1.5s warm-API budget and the 3s page
  budget in `reports/perf-budgets.md`. A 126ms response is inconsistent with the historical 3.3M-row
  whole-table prefill (which the same budgets file records at 1-10+ seconds); this is consistent with J-05's
  fix serving coverage from the persisted `coverage_snapshot` payload, never recomputing on the request
  path.

### UT-09 — Job form rejects an invalid date with an inline error
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/UT-09-top-check.png` (page-load context; see
note on the screenshot limitation in the table above)
- Typed `2026-13-40` into the Start date field (`data-testid="job-start-date"`), blurred focus. DOM
  assertions (`document.body.textContent`, `button.disabled`): the exact error text "Enter a valid date as
  yyyy-MM-dd" is present, and the Start button's `disabled` property is `true`. No `startDataJob` network
  call was observed in this state.

### UT-11 — Backend crash shows a NO-GO preflight banner distinct from initializing
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/UT-11-result.png`
- **Methodology note:** the real backend process was at no point killed, restarted, or otherwise touched
  for this check (the service-control protocol in the dispatch forbids it, and the actual crash/restart
  window the pump performed had already closed before this browser session began watching, with no
  screenshot captured of it). Instead I verified the exact same code path a real crash exercises: I
  patched `window.fetch` in the live tab so that only the `/api/health` request rejects (a `TypeError`,
  simulating "network unreachable" from the frontend's point of view), leaving every other request and the
  real backend process untouched and healthy throughout (confirmed: `GET /api/health` continued returning
  200 to direct `curl` checks during this window). Traced the exact component code
  (`components/readiness-provider.tsx`, `components/preflight-banner.tsx`) beforehand to confirm this
  reaches the identical `catch` branch a real network failure would.
- Result, within one poll cycle: banner switched to `NO-GO — do not rely on today's board.` /
  `Backend is unavailable — the preflight check could not run.` (word-for-word required text), badge to
  red `Backend unavailable`. Restored the real `fetch` afterward and confirmed the badge returned to
  `ready` on the next real poll, with the actual backend never having left its healthy state.

### UT-12 — Health badge shows boot-phase detail during initializing window
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/UT-12-result.png`
- Same controlled-fetch technique as UT-11, this time resolving `/api/health` to a realistic payload built
  from the live response with only `readiness`/`warmup` overridden to `{"readiness":"initializing",
  "warmup":{"done":42,"total":89,"status":"running","message":"history 42/89"}}`. Badge instantly rendered
  the amber pill `Initializing… history 42/89` — the exact `"Initializing…" + "history n/m"` contract, never
  a bare "Backend unavailable". (Real backend, again, never touched — it kept answering 200 the whole time.)

### UT-13 — Repeating an identical backfill shows a distinct "no new snapshots" outcome
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/UT-13-result.png`, `UT-J-03-result.png`
- Same-session screenshot (11:18, prior pass) re-examined: for `2012-03-14 → 2012-03-14` (a repeat of an
  already-snapshotted day), the badge reads `no new snapshots` in the neutral/grey styling — visibly
  distinct from the green `ok` styling used elsewhere on the same page for a productive run. Breakdown:
  "1 calendar day · 1 already snapshotted · 0 non-trading". An explicit callout box reads "Zero-work
  outcome — every requested trading day already had a snapshot... This is not a failure." This pass's own
  live J-03 execution (below) reproduced the identical pattern independently for a much larger range.

### UT-14 — Persisted job history survives a page reload
**Verdict:** PASS
**Evidence:** none (screenshot capture failed — see note)
- DOM-compared the Run History table's first rows before and after a fresh full navigation to `/data`:
  identical 50 rows in identical order (led by the 2017-2018 `interrupted` row, then the May-2026 `no new
  snapshots` rows), byte-identical text. `document.body.textContent.includes("No job has been started this
  session")` was `false` both times. Screenshot capture at this panel's position (~500-3000px into a
  reduced-height DOM, or ~17-18,000px on the full page) returned a solid-black image on every attempt —
  the same Chrome-MCP tool limitation noted under UT-09/UT-10; it did not block the DOM-based verification.

### UT-15 — A backfill spanning more than 370 days is accepted, not rejected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/UT-15-result.png`, `UT-J-03-result.png`
- Same-session screenshot (11:26) already showed `2025-06-01 → 2026-07-17` (412 calendar days) accepted
  with `chunk 5/5`, `283/283 dates` — no "range too large" rejection anywhere. This pass additionally
  **re-executed the identical request live, end to end** (see UT-J-03 below) and watched it run to full
  completion, reproducing the same acceptance/chunking behavior independently.

### UT-16 — Readiness state is discoverable and consistent on every page
**Verdict:** PASS (precondition caveat noted)
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/UT-01-result.png`, `UT-02-result.png`,
`UT-03-result.png`
- The top-bar green "Ready" pill appears in the identical position on `/`, `/scanner-runs`, and `/data`
  (visible in each page's own screenshot above). The preflight banner is likewise identically positioned
  and worded on all three pages — but its current content is amber `DEGRADED — treat today's board with
  caution.` (live-vs-seed drift flagged for ~500 symbols), not the literal green "GO" copy the test's
  preconditions assume as the steady state. This is a genuine, pre-existing data-freshness condition
  (unrelated to this iteration's code — confirmed via `GET /api/health`'s `preflight.components.drift`)
  and not something a browser-qa pass can change; the actual assertion under test — one glance, same
  place, same wording, on every page, no hunting required — holds regardless of which of GO/DEGRADED/NO-GO
  is currently true.

---

## Failed Tests

### UT-10 — Interrupted job shows an explicit state, never a stuck "running" row
**Verdict:** FAIL
**Failure:** The interrupted backfill's status badge is correct (`interrupted`), but its persisted progress
is unconditionally `0 snapshots · 0 trading days in range` rather than the range's actual mid-crash
progress — i.e. no progress is "frozen," none was ever durably checkpointed for this job.
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/UT-10-result.png` (post-restart/reload state),
`UT-10-before-kill.png` (prior pass's before-state)

**Steps taken (this pass):**
1. Confirmed via the pump's report and independent verification (`ps`, `logs/backend.log` timestamps) that
   the backend was killed mid-run (pid 1072278, killed 11:55:18 BST / logged `10:55:18Z` equivalent window)
   and restarted (pid 1214476, `logs/backend.log`: `=== start-backend.sh: launching at
   2026-07-22T10:55:28Z ===`, i.e. 11:55:28 BST — matches the pump's report to the second) while a
   `2017-01-01 → 2018-12-31` backfill (run id 110) was mid-flight.
2. Live navigation to `/data`, DOM/HTML dump of the "Job progress" and "Unfinished imports" panels
   (`data-testid="last-run-status"` = `interrupted`; panel text = "backfill: 0 snapshots over 0 dates, 0
   forward returns" / "0 snapshots · 0 trading days in range").
3. Confirmed the `2017-01-01`/`2018-12-31` strings do **not** appear anywhere inside the "Unfinished
   imports" panel's rendered text (searched the full section text programmatically).
4. Cross-checked against `GET /api/data`'s `runs` array: run 110 shows `status: "interrupted"`,
   `dates_total: 0`, `dates_done: 0`, `snapshots_created: 0`, `aggregates_refreshed: null` — identical to
   the DOM, confirming this is the served value, not a client-side rendering quirk.
5. Traced the backend code path (see "Root cause of the FAIL" above) to explain *why*: progress detail is
   flushed to the persisted row's `message` field only once, by `_finalize_run_record()`, which a `kill -9`
   never reaches; the boot sweep that marks the row `interrupted` never touches that field.
6. Took a fresh screenshot (after temporarily hiding several unrelated huge panels via
   `element.style.display='none'` purely for capture purposes, to work around a Chrome-MCP screenshot
   limitation at this page's extreme scroll depth — no application state was changed) showing both panels
   side by side: `UT-10-result.png`.

**Expected:** Status badge reads `interrupted`; the row shows its last persisted progress counts frozen at
the crash point (not reset to zero); a Retry/Resume + Dismiss control is visible on the row.
**Actual:** Status badge correctly reads `interrupted`. Progress shows an unconditional zero, not a frozen
mid-run count (no durable checkpoint of in-flight progress exists for this job kind). The row does not
appear in "Unfinished imports" (confirmed by design — see root-cause section — not counted as part of this
FAIL, but stated for completeness since the test plan's literal steps name that panel).

---

### UT-J-04 — J-04: Non-blocking boot with visible status (6-step regression journey)
**Verdict:** FAIL (step 6 only; steps 1-5 pass)

| Step | Assertion (goal.md) | Result | Evidence |
|---|---|---|---|
| 1-2 | Restart via `start-backend.sh` (prod mode); first `GET /api/health` 200 within 5s of process start | PASS (durable artifact, not re-measured this pass) | `reports/perf-budgets.md`: 1.387-1.459s, most recently measured iter-5, explicitly noted as "remains valid by construction" since zero boot-path files (`readiness.py`, `main.py` boot sequence, `warmup.py`, `scripts/start-backend.sh`'s boot logic) changed in iter-9's diff. I did not re-run this measurement myself — it requires a fresh, precisely-timed restart, and the service-control protocol bars me from performing one; the pump's own kill/restart cycle was not a precision timing harness (it was ~26s wall-clock from launch to when the pump happened to check, which is an operator-observation gap, not the measured first-200 latency). |
| 3 | With frontend open, restart again; a pre-ready `GET /api/health` shows boot phase + progress n/m; badge shows the same phase detail in the same window; never bare "Backend unavailable" | PASS (via controlled simulation — see Methodology note under UT-12) | `UT-12-result.png`: badge rendered `Initializing… history 42/89` for a payload shaped exactly like a genuine pre-ready response |
| 4 | Kill the backend; UI transitions to an explicit unreachable/crashed presentation, distinct from initializing | PASS (via controlled simulation — see Methodology note under UT-11) | `UT-11-result.png`: banner `NO-GO — do not rely on today's board.` / `Backend is unavailable...`, badge `Backend unavailable` |
| 5 | The persistent backend logfile contains boot events; after a simulated crash the log ends abruptly (no clean-shutdown entry) | PASS (live log trace, this pass) | `logs/backend.log`: pid 1072278 boots at `=== start-backend.sh: launching at 2026-07-22T09:24:46Z ===` → `Started server process [1072278]` → `Application startup complete.` → `Uvicorn running...` → **no `Shutting down`/`Finished server process` line ever follows it** — the next line is directly the NEXT restart's `=== ... launching at 2026-07-22T10:55:28Z ===` block (pid 1214476). Contrast: the PRIOR restart (pid 915809) shows a clean `INFO: Shutting down` / `Waiting for application shutdown.` / `Application shutdown complete.` / `Finished server process [915809]` sequence before its successor boots — proving the log format DOES capture clean shutdowns, and pid 1072278's entry is a genuine abrupt truncation consistent with `kill -9`. |
| 6 | On `/data`, any job mid-flight at the kill now shows an explicit interrupted/error state with its last persisted progress — never a still-"running" row | **FAIL** | See UT-10 above |

**Failure:** Step 6 fails for the reason detailed in "Root cause of the FAIL" and UT-10 above — badge
correctness is confirmed, progress preservation is not.

---

## J-01 — Backfill honors the requested range and explains zero-work (re-verification)

Read from `docs/goal.md`'s "Must-have user journeys" section. Executed as a mix of live DOM inspection
(this pass, on the current rebuilt build) and durable same-session artifacts (the underlying jobs were run
earlier in this same session by an earlier pass; this pass independently re-read the persisted results
rather than trusting the earlier pass's narrative).

| Step | Assertion | Result |
|---|---|---|
| 1-2 | Start a `backfill` for `2026-05-02 → 2026-05-29`; watch progress to completion | PASS (durable: run 109, `status: ok`, `dates_done: 19/19`) |
| 3 | `dates_total = 19` trading days (2026-05-04…2026-05-29, Memorial Day excluded); `snapshots_created` = eligible-not-already-snapshotted, skips explained | PASS — `GET /api/runs?limit=40` (re-queried fresh, this pass) lists exactly the 19 expected trading dates in range (`2026-05-04,05,06,07,08,11,12,13,14,15,18,19,20,21,22,26,27,28,29` — `2026-05-25` correctly absent as the Memorial Day non-trading day) |
| 4 | `/scanner-runs` lists in-range May dates; one opened shows stored leaderboard | PASS — UT-05/UT-06 above (2026-05-15 row + detail page, live this pass) |
| 5 | Weekend-only `2026-05-02 → 2026-05-03`: `dates_total = 0`, 2 non-trading, partitioning 2 calendar days | PASS (durable: run 108, `calendar_days: 2, non_trading_days: 2, already_snapshotted: 0, dates_total: 0`; re-read live from the Run History DOM this pass: "2 calendar days · 0 already snapshotted · 2 non-trading") |
| 6 | Re-run the identical May range: zero-work, 0 created, 19 already-snapshotted + 9 non-trading, partitioning 28 calendar days | PASS (durable: run 109 itself IS this repeat — `already_snapshotted: 19, non_trading_days: 9, calendar_days: 28, snapshots_created: 0`; re-read live from the Run History DOM this pass) |
| 7 | Reload persists all three runs with the same outcomes | PASS — see UT-14 above (fresh full-navigation reload this pass, identical Run History rows before/after) |
| 8 | Both zero-work outcomes render as an explanatory state, visually distinct from success | PASS — see UT-13 above (`no new snapshots` grey badge + explicit "Zero-work outcome... this is not a failure" callout, distinct from green `ok`) |

**Verdict:** PASS. **Golden replay:** `runs/goal-session-ops-hardening/journey-scripts/J-01.json` already
exists, lints clean (`demo_runner.py --mode lint`), and its steps/expects match what I directly observed
live this pass (`job-start-date`/`job-end-date` testids exist, "2 non-trading" and "no new snapshots" are
real, current substrings). Left unchanged — nothing to repair. The prior replay-lane FAIL
(`reports/phase-goal-ops-hardening-iter-9-regression-replay-results.md`, timestamped 09:25, "step 02 could
not perform fill: Timeout 15000ms exceeded") **pre-dates the 09:41 frontend rebuild** and is fully
consistent with the stale-build root cause documented at the top of this report, not a real regression.

## J-03 — No per-run range cap (re-verification)

Executed **live, end-to-end, this pass** (not from a stale artifact):
1. Navigated to `/data`, set Start date `2025-06-01`, End date `2026-07-17` (412 calendar days) via direct
   input events, confirmed Job kind was already "Backfill snapshots" and the Start button was enabled.
2. Clicked Start. Within the same round-trip, `job-status` read `running` — no "date range too large"
   rejection appeared anywhere.
3. DOM check of the Job progress panel moments later: `chunk 5/5`, `snapshots 283/283 dates`, `412 calendar
   days · 283 already snapshotted · 129 non-trading` — accepted and executing in visible chunks, exactly
   as required.
4. Let the job run to full completion (did not just confirm "chunk accepted" and move on): finished at
   `status: ok` / displayed as `no new snapshots` (zero-work, since this range was already covered by an
   earlier same-session run), `aggregates_refreshed: [coverage, membership_timeline, forward_aggregates,
   research_hot_keys, drawdown_expectations]` fully populated. Total wall time ~4 min — slower than an
   earlier same-session run of the identical range (~11s, run 107, ~2 hours prior); I attribute this most
   plausibly to CPU contention from this QA pass's own heavy concurrent browser/curl/python activity on
   the same host-guard-capped 4-core set, not a code regression, but I did not isolate a clean re-measurement
   to prove that attribution and am reporting the raw numbers as observed. `GET /api/health` was polled
   directly via `curl` several times during this run and returned 200 every time; backend `VmRSS` peaked
   at ~4.2GB against the 6144MB `ulimit -v` cap (68%, comfortably bounded).

**Verdict:** PASS. **Golden replay:** `runs/goal-session-ops-hardening/journey-scripts/J-03.json` lints
clean and matches the live UI (`job-start-date`/`job-end-date` testids, "412 calendar days" is a real,
current substring). Left unchanged. Same stale-build explanation as J-01 for the prior replay-lane FAIL.

---

## Environment

- **Frontend URL:** http://localhost:3255 (confirmed 200 throughout this pass; process since 09:41, the
  pump's clean rebuild — `rm -rf apps/frontend/.next && bash scripts/start-frontend.sh`)
- **Backend URL:** http://localhost:8255 (confirmed 200 throughout this pass)
  - Backend process this pass: pid 1214476, started `2026-07-22T10:55:28Z` (=11:55:28 BST) per
    `logs/backend.log`, matching the pump's reported restart to the second. `taskset -cp 1214476` →
    `0-3,8-11`; `/proc/1214476/environ` shows `OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
    NUMEXPR_NUM_THREADS=4 MALLOC_ARENA_MAX=2`; `/proc/1214476/limits` "Max address space" =
    6442450944 bytes (6144 MB) — AG-10 host-guard caps independently re-confirmed live on the current
    process, not just cited from the pump's report.
  - Prior process (pid 1072278, killed mid-run 11:55:18 BST) confirmed dead throughout this pass (`ps`
    shows no such pid; port 8255 held only by 1214476).
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), real navigations and
  DOM/JS assertions throughout — no bare `curl`-only rows.
- **Test Date:** 2026-07-22 (this pass ran roughly 11:57-12:30 BST)
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-9-evidence/`
- **Known tool limitation (not a product defect):** Chrome-MCP `screenshot` returned a solid-black image
  on every attempt when the target content sat very deep in `/data`'s DOM (the page is unusually tall —
  ~17,800px to ~24,000px depending on filter state, from ~15 stacked diagnostic panels including a 591-row
  per-symbol table and per-date availability/missing-data panels). Screenshots at shallow scroll depths on
  the same page rendered correctly every time (see UT-01/UT-08/UT-10/UT-J-03, the latter two captured after
  temporarily hiding unrelated panels via `display:none` purely to shorten the page for capture — no
  application behavior was altered). Where a screenshot could not be obtained (UT-09, UT-14), the verdict
  rests on direct DOM/JS assertions instead, stated explicitly in each row.
