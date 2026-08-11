# Goal ops-hardening — Iteration 62 — UI Test Results

**Phase:** goal-ops-hardening-iter-62
**Date:** 2026-08-11
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 3/3 tests passed (0 skipped)

---

## Scope note

Per the dispatch's "GOAL-MODE LEAN MODE" instruction, this pass live-verifies exactly J-01, J-04, J-07
via Chrome MCP against the running app (`http://localhost:3255`, backend on `:8255`). This iteration's
own diff (`apps/backend/app/api/health.py`'s `last_run_date` fix, `apps/frontend/app/data/page.tsx`'s
ambient-refresh `.catch` handlers) touches neither J-01's job-submission path, J-04's readiness
computation, nor J-07's aggregate-warm code path — all three journeys are pure regression checks this
iteration.

The deterministic-replay lane ran the same journey set independently this iteration
(`reports/phase-goal-ops-hardening-iter-62-regression-replay-results.md`, 5/7 passed) and reported J-01
FAILING at its step 09 (`zero-work-note` expect not satisfied) and J-04 FAILING at its step 02
(`readiness-badge[data-state="ready"]` `wait_for` timeout at 20000ms); it reported J-07 PASSING. This
browser-qa pass is the LLM fallback for the two replay failures, per the golden-replay design ("that
journey just falls back to you next time"), plus an independent live check of J-07. Both replay failures
resolved cleanly on live re-verification (see below) — judged transient replay-lane flakiness, not
product regressions: `GET /api/health` timing was normal (8-140ms across repeated samples) and both
badge/zero-work states were live and correct with no unusual wait required.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | Backfill of 2026-05-02→2026-05-29 reports dates_total=19 with exclusion reasons; a weekend-only span (05-02→05-03) reports 0/0 with a per-reason breakdown; both zero-work outcomes render an explicit, visually-distinct explanatory note (not a fabricated success); results persist across reload; `/scanner-runs/748` shows the stored 2026-05-29 leaderboard | Both backfills resolved as honest zero-work (data already fully backfilled from many prior iterations): job progress showed "no new snapshots", "19/19 dates", "28 calendar days · 19 already snapshotted · 9 non-trading", and a `zero-work-note` element with text "Zero-work outcome — every requested trading day already had a snapshot... this is not a failure", styled with neutral `border-border bg-surface-2 text-text-muted` classes (never a success-green treatment). Weekend-only run showed "0/0 dates" / "2 calendar days · 0 already snapshotted · 2 non-trading". Reload of `/data` showed both new runs at the top of the persisted Run history table (2026-08-11 14:12:11 and 14:10:58 entries), never "no job started this session". `/scanner-runs/748` rendered "Immutable snapshot — as of 2026-05-29" with a populated leaderboard (component breakdown, candidate counts, ticker rows led by MU 97.06) — stored values, not a recompute. | PASS | `reports/qa/goal-ops-hardening-iter-62-evidence/UT-J-01-result.png` |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | Readiness badge reads `data-state="ready"`; preflight banner shows a real verdict; `/data`'s persisted `last-run-status` field renders; persistent backend logfile contains boot events | `[data-testid="readiness-badge"]` read `{text:"Ready", state:"ready"}` immediately, no wait needed; `[data-testid="preflight-banner"]` read "GO — today's board is current."; on a fresh `/data` navigation `[data-testid="last-run-status"]` read "no new snapshots" (a real `data_provider_runs`-backed value, matching the zero-work backfill run just completed under UT-J-01); `logs/backend.log` directly confirmed to contain repeated "Uvicorn running on http://0.0.0.0:8255" boot lines including one immediately preceding the currently-running process's 2026-08-11 14:24:30 start. Crash/kill-9/interrupted-job re-simulation (goal steps 4-6) NOT re-executed this pass — restarting the live backend is forbidden for this role (standing hard rule, same as iter-58/60/61's J-04 handling); that exact behavior remains evidenced live by iter-53's UT-05/06/07 captures, unaffected by this iteration's diff. | PASS | `reports/qa/goal-ops-hardening-iter-62-evidence/UT-J-04-result.png` |
| UT-J-07 | Heavy aggregates never take the service down | regression | P1 | Readiness badge `ready`; background-compute panel discloses real (non-fabricated) state; persisted `last-run-status` and `aggregates-refreshed` fields render from `data_provider_runs` | `[data-testid="readiness-badge"]` read `data-state="ready"`; `[data-testid="background-compute-panel"]` present (no active warm at check time — 5 direct `GET /api/health` samples at ~1s apart all answered HTTP 200 in 9-19ms with `background_compute.active=[]`, i.e. an earlier warm this same long-lived process had run at ~14:06 had already finished cleanly by this pass, itself supporting evidence the process survives heavy compute without wedging); `[data-testid="last-run-status"]` read "no new snapshots"; `[data-testid="aggregates-refreshed"]` read "Refreshed: forward aggregates, research hot keys, factor lab all, drawdown expectations". Fault-injected memory-pressure abort (goal step 4) NOT re-run this pass — requires a backend restart, forbidden for this role (same standing rule as iter-60/61); this iteration's diff does not touch the warm/aggregate code path, so no new risk to that acceptance clause. | PASS | `reports/qa/goal-ops-hardening-iter-62-evidence/UT-J-07-result.png` |

---

## Passed Tests

### UT-J-01 — Backfill honors the requested range and explains zero-work
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-62-evidence/UT-J-01-result.png`
- Navigated to `/data`; set job-start-date=2026-05-02, job-end-date=2026-05-29 (React-controlled inputs
  set via the native value setter + `input`/`change` events so React state stays in sync), kind left at
  its default `backfill`, clicked the form's sole `button[type="submit"]`.
- Job progress panel resolved within ~5s to a zero-work outcome: `19/19 dates`, `0 snapshots · 0 forward
  returns inserted`, `28 calendar days · 19 already snapshotted · 9 non-trading`, and
  `[data-testid="stage-timings"]` showing `Elapsed 5.2s`, `Dates 19`, `Concurrency 4x`.
  `[data-testid="zero-work-note"]` present with the explanatory text, styled distinctly from success
  (neutral gray, no green/checkmark treatment) — confirmed via direct DOM/class inspection, not just a
  screenshot.
- Set start=2026-05-02, end=2026-05-03 (weekend-only span), submitted again: job progress showed
  `0/0 dates`, `2 calendar days · 0 already snapshotted · 2 non-trading`, same `zero-work-note` treatment.
- Reloaded `/data` (fresh navigation): the persisted "Run history" table's top two rows were
  `2026-08-11 14:12:11 backfill 2026-05-02 → 2026-05-03` and `2026-08-11 14:10:58 backfill
  2026-05-02 → 2026-05-29`, both with the same outcomes as just observed — confirms persistence across
  reload.
- Navigated to `/scanner-runs/748`: rendered "Immutable snapshot — as of 2026-05-29", Market Regime
  75.20/100, a full component breakdown, candidate counts (Actionable 0 / Breakout-watch 54 /
  Pullback-watch 1 / Risk-off-watchlist 0), and a leaderboard led by MU (Leadership 97.06) — stored
  values rendered from the snapshot, not recomputed.
- Note: both requested ranges resolved as zero-work rather than a first-time productive run, because
  this exact May range has been backfilled repeatedly across many prior QA iterations on this
  long-lived seed DB — this is expected given the session's history and does not weaken the honesty
  check (the zero-work presentation, breakdown arithmetic, and persistence are exactly what the
  Acceptance criteria require).
- Screenshot note: the "Job progress"/`zero-work-note` panel sits ~5800px down this data-dense page
  (14449px tall, 591-row per-symbol coverage table). A screenshot taken at that scroll depth (both via
  `scrollIntoView` and via the tool's native `scroll` action) rendered solid black three times in a row
  — a headless-Chromium capture artifact at extreme scroll offsets on this page, not a product defect
  (confirmed: an eval-driven capture at `scrollY=0` on the SAME page/state renders correctly). All
  `zero-work-note`/stage-timings/Run-history assertions above were verified via direct DOM/`textContent`
  reads (stronger evidence than a screenshot), not screenshots; `UT-J-01-result.png` therefore shows the
  same page at `scrollY=0` (readiness badge "Ready", dataset coverage panel) captured immediately after
  the reload that confirmed persistence, rather than the deep-scrolled panel.

### UT-J-04 — Non-blocking boot with visible status
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-62-evidence/UT-J-04-result.png`
- On `/`, `[data-testid="readiness-badge"]` read `data-state="ready"` / text "Ready"; `[data-testid=
  "preflight-banner"]` read "GO — today's board is current." — both read instantly with no polling wait
  required.
- On `/data`, `[data-testid="last-run-status"]` read "no new snapshots", a real persisted
  `data_provider_runs`-backed value (the same run UT-J-01 just produced), not a fabricated placeholder.
- Confirmed via direct file read that `logs/backend.log` is a persistent, growing logfile containing
  repeated boot lines ("Uvicorn running on http://0.0.0.0:8255") and ingest-heavy-warm-window log lines
  timestamped through the current session, including one immediately preceding this process's own
  2026-08-11 14:24:30 start.
- `GET /api/health` sampled directly 3x: 200/25ms, 200/140ms, 200/19ms — no latency regression from this
  iteration's added `last_run_date` query.
- Did NOT restart or kill the live backend process this pass (hard rule for this role) — so goal steps
  3-6 (pre-ready phase/progress capture, simulated crash, interrupted-job row) were not re-simulated;
  that behavior remains evidenced live by iter-53's UT-05/06/07 captures and is unaffected by this
  iteration's diff (`health.py`'s `last_run_date` addition sits inside the existing `db_ok` try/except
  and does not touch `app.engine.readiness`).

### UT-J-07 — Heavy aggregates never take the service down
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-62-evidence/UT-J-07-result.png`
- On `/data`, `[data-testid="readiness-badge"]` read `data-state="ready"`.
- `[data-testid="background-compute-panel"]` present and rendering its real disclosure text; no job was
  actively running at the moment of this check — verified independently via 5 direct `GET /api/health`
  samples (~1s apart): all HTTP 200 in 9-19ms, `background_compute.active` empty each time. An earlier
  warm in this SAME long-lived backend process (asof_key 2026-07-31, first observed active with
  elapsed_ms≈62985 before this test pass began) had completed cleanly by the time of this check — the
  process kept serving normally throughout, consistent with the acceptance clause that a heavy warm
  never wedges the process.
- `[data-testid="last-run-status"]` read "no new snapshots"; `[data-testid="aggregates-refreshed"]` read
  "Refreshed: forward aggregates, research hot keys, factor lab all, drawdown expectations" — both real
  `data_provider_runs`-backed fields from the finalize tail, not fabricated.
- Did NOT re-run the fault-injected memory-pressure abort (goal step 4) — requires a backend restart,
  forbidden for this role. This iteration's diff does not touch `compute_forward_aggregates` or any
  warm/aggregate code path, so no new risk is introduced to that acceptance clause; prior iterations'
  live captures (iter-58 Addendum, iter-59 Addendum 26) remain the standing evidence for it.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned
  profile/CDP port, headless
- **Test Date:** 2026-08-11
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-62-evidence/`

---

## Golden replay scripts written/updated this pass

- `runs/goal-session-ops-hardening/journey-scripts/J-01.json` — rewritten with an iter-62 provenance
  note (steps/selectors unchanged from the iter-61 golden, all re-verified live). Lints clean.
- `runs/goal-session-ops-hardening/journey-scripts/J-04.json` — appended an iter-62 note documenting the
  replay-lane's step-02 timeout this pass vs. this agent's clean live re-verification (steps unchanged).
  Lints clean.
- `runs/goal-session-ops-hardening/journey-scripts/J-07.json` — appended an iter-62 note (this iteration's
  replay lane already passed this script; this agent's independent live check corroborates it, steps
  unchanged). Lints clean.
