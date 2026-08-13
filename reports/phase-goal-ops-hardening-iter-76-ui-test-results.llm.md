# Goal Iteration 76 — UI Test Results (LLM lane)

**Phase:** goal-ops-hardening-iter-76
**Date:** 2026-08-13
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->

**Overall:** 3/3 tests passed (0 skipped)

Scope note: per dispatch, this run is the LLM re-confirmation lane for exactly J-01, J-07, J-09 —
J-01 because the deterministic replay lane FAILed it this round; J-07/J-09 as this iteration's
target journeys. J-03, J-04, J-05, J-06, J-08 are covered separately by the deterministic replay
lane (`reports/phase-goal-ops-hardening-iter-76-regression-replay-results.md`, all 6 PASS) and were
intentionally NOT re-driven here.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression re-confirm | P1 | All 3 backfill submissions (full May range, weekend-only, May re-run) resolve with correct `dates_total`/exclusion breakdowns, zero-work rendered as an explanatory neutral state (never green success), persisted across reload, and a spot-checked scanner run's leaderboard renders stored values | All 3 submissions resolved exactly as expected; zero-work note confirmed neutrally styled; Run history persisted all 3 runs after reload; `/scanner-runs/748` (2026-05-29) rendered a populated, stored leaderboard; `/scanner-runs` confirmed 2026-05-04/05-15 present and 2026-05-25 (Memorial Day) absent | PASS | reports/qa/goal-ops-hardening-iter-76-evidence/UT-J-01-result.png |
| UT-J-07 | Heavy aggregates never take the service down | target | P1 | Readiness badge stays Ready/responsive and the Forward-test scorecard serves real content while heavy background compute runs; service never freezes | Badge `data-state="ready"` confirmed on `/`; `/backtest` scorecard renders (honest empty state at Latest, populated 1d row at historical as-of 2026-07-31); a real background-compute window (09:01:19–09:09:03 UTC, 463.7s) ran to completion WHILE this session concurrently submitted and completed 3 live backfill jobs — service stayed fully responsive throughout; 10/10 steady-state `GET /api/health` polls 0.022–0.032s (well under the ≤0.1s budget) | PASS | reports/qa/goal-ops-hardening-iter-76-evidence/UT-J-07-result.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | target | P1 | Badge shows "Ready" + a background-compute detail simultaneously during a window; `/data` panel mirrors the same window with elapsed/horizons, then transitions to idle + a real measured last-outcome duration; process-lifetime scope disclosed | Observed a full live active→idle lifecycle: badge showed "Ready" + "background compute running (1)" simultaneously; `/data`'s `background-compute-active-row` showed as-of 2026-07-31, elapsed 2m40s, horizons 1/5, dataset r2988-f6601195, matching `GET /api/health` exactly; after completion, panel correctly rendered the `background-compute-idle` sub-state (not the `background-compute-unknown` backend-unreachable branch) with `LAST OUTCOME: Completed / as-of 2026-07-31 / 7m 44s` — exact match to the API's duration_ms 463745; verbatim "Since the last backend restart — this history is process-lifetime only, never persisted" disclosure confirmed | PASS | reports/qa/goal-ops-hardening-iter-76-evidence/UT-J-09-result.png |

---

## Passed Tests

### UT-J-01 — Backfill honors the requested range and explains zero-work

**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-76-evidence/UT-J-01-result.png`

This journey's steps 1-4 (a "productive" fresh backfill) are, in the live shared dev DB, also
zero-work — the May 2026-05-02→05-29 range has been fully backfilled by many prior QA iterations —
matching the existing golden's own steps exactly (this is the same real-data condition every prior
verification of this journey since iter-62 has documented; not something this round changed).

- Navigated to `/data` (styled, fully rendered — not an asset-less shell).
- Set job kind = `backfill` (already the form default), start `2026-05-02`, end `2026-05-29`, clicked
  Start. Job progress panel resolved within ~5s: "no new snapshots", "19/19 dates", "0 snapshots · 0
  forward returns inserted", "28 calendar days · 19 already snapshotted · 9 non-trading", and the
  "Zero-work outcome — every requested trading day already had a snapshot... this is not a failure"
  paragraph, styled `rounded-md border border-border bg-surface-2 px-3 py-2 text-xs text-text-muted`
  (neutral — never the success-green treatment).
- Second submission, weekend-only `2026-05-02`→`2026-05-03`: resolved "no new snapshots", "2 calendar
  days · 0 already snapshotted · 2 non-trading" — matching the goal's contract that non-trading +
  dates_total = calendar days exactly (2 non-trading = 2 calendar days, 0 trading-day targets).
- Third submission, re-run identical May range: resolved identically to the first ("19/19 dates",
  "28 calendar days · 19 already snapshotted · 9 non-trading").
- Reloaded `/data` fresh (no eval/cache): the persisted Run history table showed all three of this
  session's own runs (2026-08-13 09:08:04 / 09:08:33 / 09:09:01 UTC) at the top with identical
  outcomes/breakdowns — never "no job started this session".
- Visited `/scanner-runs`: confirmed rows exist for 2026-05-04 and 2026-05-15 (in-range May dates)
  and confirmed 2026-05-25 (Memorial Day) is correctly absent (non-trading). Opened
  `/scanner-runs/748` (2026-05-29): rendered "Immutable snapshot — as of 2026-05-29 / Stored exactly
  as scanned; never recomputed for today. Scanned 2026-07-20 17:31:15" (an OLD scan timestamp, proving
  re-serve from storage, not a fresh recompute) with a populated leaderboard (Market Regime 75.20/100
  Risk-on; ticker rows led by MU 97.06 Leadership / 20.59 Entry Quality / 54.30 Risk).

**Note on this round's deterministic-replay FAIL:** the replay lane FAILed this golden at step 07
("Zero-work outcome" expect timed out). Cited evidence (not a vague "transient load" guess, per the
iter-72 (2 of 2) lesson): the replay's own failure screenshot
(`reports/qa/goal-ops-hardening-iter-76-evidence/J-01-verify.png`) shows the top-bar badge reading
"background compute running (1)" at the moment of failure. `GET /api/health` confirms a real J-09
background-compute window was in flight at exactly that time (asof_key 2026-07-31, dataset_version
r2988-f6601195, started 2026-08-13T09:01:19Z, finished 09:09:03Z, duration_ms 463745) — competing for
backend/DB resources. `demo_runner.py`'s per-step timeout is hard-capped at 20000ms regardless of the
script's `default_timeout_ms`, so a slow-but-real async job-status update racing that contention
plausibly missed the 20s window once. My own live re-run, submitted at 09:08:04 UTC — still inside
that same 09:01:19–09:09:03 BCW window — resolved the identical scenario correctly within ~5s each
time. Diagnosis: a timing/contention artifact of a real, correctly-functioning concurrent
background-compute feature (J-09), not a product regression. The golden's steps/selectors are
unchanged; only a fresh `_notes` entry was appended.

### UT-J-07 — Heavy aggregates never take the service down

**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-76-evidence/UT-J-07-result.png`

Per the iter-76 spec's own "OUT OF SCOPE" list, re-measuring VmPeak/margin or running a fresh full
warm/rebuild drill is explicitly "Do not redo" this round (closed at iter-74/iter-58). This pass is
the LLM re-confirmation of the structurally-verifiable steps plus incidental corroboration from real
concurrent load that happened during this session's other testing:

- `/` : readiness badge confirmed `data-state="ready"` (not just the visible "Ready" text).
- `/backtest` at Latest as-of (2026-08-03): correctly showed the honest "No elapsed forward window for
  this date yet" empty state (no forward window has elapsed for the newest snapshot yet — not a bug).
  Clicking "Previous available date" landed on "Viewing as-of 2026-07-31 (historical)" with the
  Forward-test scorecard table populated (1d: +0.70% n=20 ⚠; 5d–60d honestly "— n=0" since those
  windows genuinely haven't elapsed in the seed either — never fabricated).
- Incidental but directly relevant: a real background-compute window was active on arrival
  (`GET /api/health` `background_compute.active=[{asof_key:"2026-07-31", horizons_done:1,
  horizons_total:5, elapsed_ms:130148}]`) and ran to completion (09:01:19–09:09:03 UTC, 463.7s)
  **while this same session concurrently submitted and completed 3 live `/data` backfill jobs
  (J-01's own test, above)** — the service never froze, never returned a non-200, and both features
  (ingest jobs and background-compute dispatch) completed correctly and independently under real
  simultaneous load.
- Steady-state `GET /api/health`, 10 polls after the window went idle: 10/10 HTTP 200, 0.022–0.032s
  each — comfortably inside the ≤0.1s steady-state budget.
- Confirmed the iter-76 spec's planned `data-testid="scorecard-row-<horizon>d"` QA hook is **not**
  present in the shipped frontend (`document.querySelectorAll('[data-testid^="scorecard-row-"]').length
  === 0` on a live populated `/backtest` page, and `grep -n data-testid
  apps/frontend/app/backtest/page.tsx` returns nothing inside `ScorecardSection`) — consistent with
  this round's dev handoff stating "no code changes were made". The strengthened golden written this
  round therefore uses the real, already-shipped `data-state="ready"` attribute for step 1 and a
  structural horizon-label check ("1d") for the scorecard-populated check, instead of the
  not-yet-implemented testid.

### UT-J-09 — Disclose in-flight background-compute activity (badge + /data panel)

**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-76-evidence/UT-J-09-result.png`

- On `/data`, the badge simultaneously showed "Ready" and "background compute running (1)" — never a
  bare Ready hiding the activity, never a misstated initializing/unavailable.
- The SAME poll's `background-compute-panel` mirrored the SAME window: `background-compute-active-row`
  reading "as-of 2026-07-31, elapsed 2m 40s, horizons 1/5, dataset r2988-f6601195" — matching
  `GET /api/health`'s payload exactly (asof_key, dataset_version, horizons_done/total, elapsed).
- Waited out the window (blocking-polled `GET /api/health`): `active` emptied at 09:09:03 UTC
  (duration_ms 463745).
- Reloaded `/data`: directly confirmed via `querySelector` presence checks that the panel now renders
  the `background-compute-idle` sub-state (`idle: true, active: false, unknown: false`) — never
  silently falling through to `background-compute-unknown` (the backend-unreachable branch). Panel
  text: "No background compute running." + `LAST OUTCOME: Completed / as-of 2026-07-31 / 7m 44s` — an
  exact match (rounded) to the API's own measured `duration_ms: 463745`. No fabricated percentage or
  estimated finish time anywhere.
- Verbatim disclosure confirmed: "Since the last backend restart — this history is process-lifetime
  only, never persisted."
- Clicking "Previous available date" on `/backtest` landed on "Viewing as-of 2026-07-31 (historical)"
  instantly (content loaded async, never blocked on the dispatch) — matching this golden's steps 1-2.

This round's replayed golden (`journey-scripts/J-09.json` as it existed at the start of this pass)
only asserted the outer `background-compute-panel` container's presence, which would pass even against
a silent fall-through to the unknown/unreachable branch. Strengthened step 3 to require ONE of the two
real sub-state testids (`background-compute-idle` or `background-compute-active-row`), confirmed both
exist in shipped code before wiring them in, and lint-checked the result clean.

---

## Failed Tests

None.

---

## Skipped Tests

None. Backend (`:8255`) and frontend (`:3255`) were both live and fully styled/responsive throughout
this session — no asset-less/unstyled shells, no "Checking backend…" stalls, and services were not
swept away mid-run.

---

## Golden replay scripts written this round

All three overwrite the existing files at `runs/goal-session-ops-hardening/journey-scripts/`, keep
their prior `_notes` history, and append a fresh iter-76 entry. Lint-checked clean via
`python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir
runs/goal-session-ops-hardening/journey-scripts --journeys J-01,J-07,J-09` → `J-01 ok`, `J-07 ok`,
`J-09 ok`.

- `J-01.json` — steps/selectors unchanged (already correct); appended the FAIL-diagnosis note above.
- `J-07.json` — step 1 strengthened to require `[data-testid="readiness-badge"][data-state="ready"]`
  (a real, already-shipped selector); added steps 3-4 (click to historical as-of, assert a populated
  horizon-label token "1d" renders) since the spec's planned `scorecard-row-<horizon>d` testid does not
  exist in the shipped frontend this round.
- `J-09.json` — step 3 strengthened to require
  `[data-testid="background-compute-idle"], [data-testid="background-compute-active-row"]` (both real,
  already-shipped selectors) instead of only the outer panel container, so a silent fall-through to the
  `background-compute-unknown` branch now fails the replay.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned
  profile/port
- **Test Date:** 2026-08-13
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-76-evidence/`
