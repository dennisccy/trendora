# Phase goal-ops-hardening-iter-21 — UI Test Results

**Phase:** goal-ops-hardening-iter-21
**Date:** 2026-07-25
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 1/2 tests passed (1 skipped — capability/scope-gated, not a product failure)

This lean iteration's dispatch names exactly two journeys: **J-08** (target) and **J-04**
(required-still-passing regression lane). J-01/J-03/J-05 were explicitly out of this run's scope —
they are verified separately by deterministic golden replay
(`reports/phase-goal-ops-hardening-iter-21-regression-replay-results.md`, 3/3 PASS, dated
2026-07-25). UT-J-08 PASSED with a fresh, real Chrome MCP capture of the exact `ready → refreshing →
ready` state machine the iteration's Test-first contract (TC-1/TC-2) calls for. UT-J-04 is SKIPPED —
its four disruptive steps (backend restart/kill/restart) are explicitly out of scope this iteration
(`docs/phases/goal-ops-hardening-iter-21.md` OUT OF SCOPE: "Re-running TC-13 or TC-14... Do not
re-plan or re-trigger either measurement this iteration") and the iteration's own Definition of Done
and Testing Requirements state plainly that the browser-qa lane is "expected to SKIP the disruptive
steps as it always has" since TC-14's fresh 2026-07-25 operator evidence is the substitute. This
matches the dev handoff's identical treatment and the session's established pattern since iter-15.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-08 | J-08: Backtest evidence serves from storage only — never a cold recompute on request | functional (target journey) | P1 (target) | A literal small single-day backfill bumps the dataset version; `/backtest` (is_latest view) serves the last-complete stored version labeled "refreshing" within ≤1.5s while the finalize warm is in flight, then serves the freshly-warmed version "ready" within the same budget once `aggregates_refreshed` includes `forward_aggregates` — never a request-path recompute | Submitted a real single-day backfill (2025-05-27, a confirmed never-snapshotted trading day) via the `/data` UI. Caught the live "refreshing" window via Chrome MCP: `evidence-refreshing` banner present, exact expected copy, `/api/backtest` HTTP 200 in 0.061s with `evidence_status=refreshing`, `evidence_generated_at` unchanged (stale/prior version correctly served). ~6m47s later (host-guard-throttled finalize hook; run 167's `aggregates_refreshed` now included `forward_aggregates`), reloaded `/backtest` again: banner gone, HTTP 200 in 0.054s, `evidence_status=ready`, `evidence_generated_at` now a NEW timestamp (genuine fresh compute). See narrative below for the full evidence chain and one honest caveat on `evidence_asof`'s literal value | PASS | `reports/qa/goal-ops-hardening-iter-21-evidence/UT-J-08-01-before-ready.png`, `UT-J-08-02-data-manager-top.png`, `UT-J-08-03-refreshing.png`, `UT-J-08-04-ready-after-warm.png` |
| UT-J-04 | J-04: Non-blocking boot with visible status (required-still-passing regression lane) | regression | P1 (required-still-passing) | Journey's 6 numbered steps (backend restart timing, ≤250ms health polling through a second restart, kill→crashed presentation, logfile boot/abrupt-end evidence, restart→interrupted-job presentation) executed as a test case | NOT EXECUTED — steps 1, 3, 4, 6 all require restarting or forcibly killing the live, pump-verified backend. This iteration's spec puts re-triggering that exact disruptive replay explicitly OUT OF SCOPE (TC-14 already supplies fresh, owner-authorized 2026-07-25 evidence: Part A kill -9 → restart → ready in ~25s; Part B wide-backfill checkpoint survived a mid-run kill -9, `status: interrupted`, `dates_done` preserved) and its Definition of Done / Testing Requirements state the browser-qa lane is "expected to SKIP the disruptive steps as it always has." No non-disruptive partial substitute was attempted (matching this session's deliberate iter-17/19/20 precedent, which found no browser-observable subset of J-04's own acceptance criteria that doesn't require an actual restart/kill event) | SKIP | n/a — see Skipped Tests section below |

---

## Passed Tests

### UT-J-08 — Backtest evidence serves from storage only — never a cold recompute on request
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-21-evidence/UT-J-08-01-before-ready.png` (baseline ready state), `UT-J-08-02-data-manager-top.png` (Data Manager after the backfill — snapshot dates 1865, backfill gaps 3519), `UT-J-08-03-refreshing.png` (live refreshing state), `UT-J-08-04-ready-after-warm.png` (ready again, post-warm)

**Precondition / baseline (before any action).** Navigated to `http://localhost:3255/backtest`. DOM +
API both confirmed the starting state: top-bar `Ready` badge, `provider: seed`, `seed 2026-07-22`,
`591 symbols`; `backtest-asof` badge read "Viewing as-of 2026-07-22 (latest)"; no `evidence-refreshing`
banner present. `GET /api/backtest` (curl, out-of-band cross-check): `evidence_status="ready"`,
`evidence_asof="2026-07-22"`, `evidence_generated_at="2026-07-24T17:26:03.995280+00:00"`. This exact
timestamp is the marker I tracked through the rest of the test.

**Action — a real single-day backfill via the actual `/data` form.** Before touching the form I
independently confirmed (read-only query against `apps/backend/data/trendora.db`) that `2025-05-27` is
a genuine trading day with stored `daily_prices` bars for AAPL but **no** `scanner_runs` row yet — a
true, never-snapshotted gap, not a repeat of a date any earlier iteration (or this iteration's own
J-05 golden replay, which reused `2025-05-15` and was a documented zero-work re-run) had already
touched. On `/data`, set both `job-start-date` and `job-end-date` to `2025-05-27` (kind stayed at its
default `backfill`; no import-source selector is shown for `backfill` kind — it never calls a live
provider) and clicked **Start** through the real UI (React-controlled inputs set via the native-setter
+ `input`/`change` event pattern after `type` action's click-then-type sequence proved unreliable
against the pre-filled gap-prefill value — noted as a browser-automation quirk, not a product issue).

**TC-1 — caught the live "refreshing" window.** Immediately after submitting, curl-polled
`GET /api/data` until the new run (id 167) appeared with `status: "running"`,
`snapshots_created: 1`, `aggregates_refreshed: null` — i.e., the new `ScannerRun` + `ForwardReturn`
rows were already committed (bumping the engine's dataset-version stamp) but the finalize hook's
forward-aggregate warm had not yet completed. At that exact moment I reloaded `/backtest` in the
browser and captured, via DOM `eval`:
- `[data-testid="evidence-refreshing"]` **present**, full text verbatim: *"Refreshing — showing the
  last complete evidence / The dataset has changed since this evidence was generated, and the newer
  version is not complete yet. The forward-tested evidence below is the last complete version —
  evidence as of 2026-07-22, generated 2026-07-24 17:26:03 — no partial or fabricated figures are shown
  in the meantime. Reload this page after the next ingest finishes to pick up the new version."*
- `backtest-asof` badge unchanged: "Viewing as-of 2026-07-22 (latest)".
- Cross-checked `GET /api/backtest` in the same window: HTTP 200 in **0.061s** (well inside the ≤1.5s
  budget), `evidence_status="refreshing"`, `evidence_asof="2026-07-22"`, `evidence_generated_at`
  **identical** to the pre-backfill baseline — i.e., the genuinely stale/prior complete version was
  served, never a partial or fabricated figure, and never a blocking recompute (the response was fast,
  not slow-then-fresh).

**Finalize hook duration.** Run 167 (`started_at` 2026-07-25T01:57:50, `finished_at`
2026-07-25T02:04:37 — about 6m47s) took materially longer than a bare single-day scan because the
finalize hook's forward-aggregate warm runs under this host's AG-10 CPU/thread caps; the backend stayed
responsive to `/api/data` polls throughout (no freeze). This is expected host-guard behavior, not a
regression — TC-13's own operator evidence documents the same finalize hook completing during a live
poll window under identical caps.

**TC-2 — the fresh "ready" state, once `aggregates_refreshed` included `forward_aggregates`.** Polled
`GET /api/data` until run 167 read `status: "ok"` with
`aggregates_refreshed = ["latest_snapshot", "coverage", "membership_timeline", "market_phase",
"forward_aggregates", "research_hot_keys", "drawdown_expectations"]`. Reloaded `/backtest` again:
- `[data-testid="evidence-refreshing"]` **absent**.
- `backtest-asof` badge: "Viewing as-of 2026-07-22 (latest)" (unchanged).
- `GET /api/backtest`: HTTP 200 in **0.054s** (within budget), `evidence_status="ready"`,
  `evidence_asof="2026-07-22"`, `evidence_generated_at="2026-07-25T02:00:31.176595+00:00"` — a
  genuinely **new** timestamp, proving a real recompute landed (not a cache artifact of the stale row).

**Honest caveat on `evidence_asof`'s literal value (read the spec's "PRIOR/NEW as-of date" wording
precisely).** `evidence_asof` read `"2026-07-22"` in ALL THREE states (ready-before, refreshing,
ready-after) — it never became a numerically different calendar date. I verified this is the CORRECT,
documented behavior, not a gap: I read `resolved_forward_aggregate_evidence`'s own docstring
(`apps/backend/app/engine/forward_testing.py:1291-1420`) directly. Sub-case (a) — "SAME `asof_key`, a
PRIOR `dataset_version`... `evidence_asof` equals `as_of` (the served evidence genuinely IS for this
date, just from an older compute of it)" — is exactly what a backfill of a date OTHER than the current
latest triggers (since this seed-bounded environment has no bars beyond 2026-07-22, so the "latest"
calendar date itself cannot advance). Sub-case (b), where `evidence_asof` would fall back to a
genuinely OLDER date string, only fires when the asof_key being viewed has NEVER had any complete
version at all (a brand-new latest trading day's first-ever view) — not reachable here. So I read the
spec's TC-1/TC-2 "PRIOR (not the new) as-of date" / "NEW as-of date" language as referring to the
PRIOR vs NEW **evidence version** (status + `evidence_generated_at`) for the same as-of date, which is
exactly what was captured and is exactly what J-08's acceptance criteria (a version-bump fallback that
clears once the fresh version lands, never a request-path recompute) require. Flagging this explicitly
rather than silently asserting the calendar date changed when it did not.

**TC-11 (AG-9/AG-10 compliance).** The completed run record (`GET /api/data`, run id 167) shows
`"provider": "seed"` — the committed local fixture, not a live network call — confirming `backfill`
kind never touches an external provider (it only reads bars already in `daily_prices`; the "Import
source" selector is not even rendered for `backfill` kind in the form). The backend serving this
request was already running via `scripts/start-backend.sh` under the coordinator's pump-verified
session (health 200, readiness `ready`, warmup 89/89) — I did not restart or launch any backend process
myself; no host-guard cap was touched.

**TC-4 (zero request-path aggregate compute — call-count instrumentation).** Out of browser-QA's
reach by nature (an API/test-layer assertion, not a DOM-observable behavior). Already independently
covered by the dev handoff (`docs/handoffs/goal-ops-hardening-iter-21-dev.md`): a read-only re-run of
`tests/test_forward_testing_serving_split.py` reports **25 passed, 0 failed**, including the four
named `is_latest`-never-computes tests. Not re-derived here.

**TC-5 (never-warmed empty state).** Carried from iter-17's TC-09 capture per the spec's own
instruction — the dev handoff confirms zero diff to `resolved_forward_aggregate_evidence`, the
`not_yet_computed` `EmptyState`, or any file in that code path this iteration, so no fresh capture was
needed or attempted.

**Golden replay script: intentionally NOT written for J-08 this iteration.** I read
`scripts/automation/lib/demo_runner.py` directly before deciding: every replay step's timeout is hard-
capped at `min(step.timeout_ms or default_timeout_ms, 20000)` — 20 seconds, regardless of what
`default_timeout_ms` a script declares. This run's real finalize-hook wait between the "refreshing" and
"ready" captures was **~6m47s** under this host's AG-10 throttling — over 20× the runner's absolute
per-step ceiling. A scripted replay of the actual verified flow (submit backfill → wait for
`aggregates_refreshed` to include `forward_aggregates` → assert "ready") would not skip this wait, it
would simply time out and report a false FAIL on every future replay, which is worse than no script at
all. Writing a diminished script that only re-checks the static "ready" end state would not exercise
J-08's distinguishing claim (the refresh-then-recover cycle) and would misrepresent what was actually
verified. Per the agent instructions' explicit best-effort allowance ("if you can't produce a clean
script for a journey, skip it"), J-08 is skipped and falls back to the LLM browser-qa lane next time.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-J-04 — J-04: Non-blocking boot with visible status (required-still-passing regression lane)
**Verdict:** SKIPPED
**Reason:** scope-gated by this iteration's own spec, not attempted — not a product failure.

J-04's own numbered steps in `docs/goal.md` (§ Must-have user journeys) require, in order: (1) restart
the backend via `scripts/start-backend.sh` and time the first `GET /api/health` 200, (3) restart it
again while the frontend is open and poll `GET /api/health` at ≤250ms intervals to catch a pre-ready
boot-phase payload, (4) **kill the backend process** (simulated crash) and assert the UI shows an
explicit unreachable/crashed state, (5) inspect the persistent backend logfile for boot entries and an
abrupt (crash) ending, (6) restart the backend again and assert `/data`'s Run History shows the
interrupted job's last-checkpointed progress. Four of the six steps are inherently destructive
service-restart/kill actions.

This iteration's own spec (`docs/phases/goal-ops-hardening-iter-21.md`) is explicit and repeated on
this exact point:
- **OUT OF SCOPE:** *"Re-running TC-13 or TC-14. Both are DONE and PASS, dated 2026-07-25,
  owner-authorized. Do not re-plan or re-trigger either measurement this iteration."* TC-14 IS J-04's
  disruptive kill/restart + checkpoint-survival replay (Part A: `kill -9` → `scripts/start-backend.sh`
  restart → `ok/ready` in ~25s; Part B: a wide backfill checkpointed to `dates_done 1366/2904`,
  `kill -9` mid-run, restart shows `status: interrupted`, checkpoint preserved — both fresh,
  2026-07-25, in `reports/perf-budgets.md` § "Post-STALL owner-authorized measurements — TC-13 + TC-14"
  and `runs/goal-ops-hardening-iter-21/operator-tc13-tc14-evidence.md`).
- **Definition of Done:** *"Required-still-passing journeys J-01, J-03, J-05 remain green via
  deterministic golden replay; J-04 remains green via TC-14's fresh operator evidence (not a fresh
  browser-qa capture, which is expected to SKIP the disruptive steps as it always has)."*
- **Testing Requirements:** *"the LLM browser-qa lane for J-04 (expected to SKIP the disruptive steps
  again, per the established session pattern since iter-15 — TC-14's fresh operator evidence is the
  substitute, not a gap)."*

The dev handoff (`docs/handoffs/goal-ops-hardening-iter-21-dev.md`) states the identical routing and
confirms it did not restart/stop the backend or frontend itself this iteration for the same reason.
Consistent with that, and with this session's own deliberate iter-17/19/20 precedent (which each found
no browser-observable subset of J-04's acceptance criteria that does not require an actual restart/kill
event — a plain `GET /api/health` sanity check proves only that the CURRENTLY running process is
healthy, not any of J-04's actual restart/crash/recovery claims), I did not attempt a partial
substitute check. The backend and frontend were left exactly as the coordinator handed them off:
healthy, pump-verified, untouched by me.

No golden replay script was written for J-04 this run (nothing passed to script). It continues to fall
back to the LLM lane in a future iteration, unchanged from the iter-16 through iter-20 carried
treatment — golden scripts already exist only for J-01/J-03/J-05/J-06 in
`runs/goal-session-ops-hardening/journey-scripts/`.

---

## Observations for the evaluator (not failures)

1. **`/data` page screenshots came back blank twice** (form-filled state, and the Run History table
   scrolled into view) despite the DOM/API evidence confirming the correct content was rendered — this
   large page (a membership-timeline table renders ~5,400+ interactive elements) appears to hit a
   screenshot-capture quirk in the Chrome MCP tool at deep scroll depths on this specific page; a
   freshly-loaded (unscrolled) `/data` screenshot captured cleanly (`UT-J-08-02-data-manager-top.png`),
   and the Run History row was independently confirmed via a DOM text extract (`grep` on the saved
   extract): `2026-07-25 01:57:50  backfill  2025-05-27 → 2025-05-27  ok  0 / 0  1`, matching run 167
   exactly. Noted as a browser-automation limitation, not a product defect, per the agent rules ("Do
   NOT mark FAIL merely because browser automation had trouble").
2. **Pre-existing DEGRADED preflight banner** ("Live-vs-seed drift detected (adjustment seam)" for
   nearly the whole universe) was visible on every `/backtest`/`/data` load throughout this test. This
   is a long-standing, already-tracked condition unrelated to J-04/J-08's acceptance criteria (not
   introduced by this test's backfill) — mentioned for completeness, not raised as a new finding.
3. **Dataset state after this test:** `daily_prices`/`scanner_runs` now include a genuine snapshot for
   `2025-05-27` (run id 167, `provider: seed`, 2,725 forward returns written). This is additive,
   read/backfill-only activity consistent with AG-9 (offline seed fixture) and matches exactly what
   TC-1/TC-2 in this iteration's own Test-first contract asked browser-qa to do.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-25
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-21-evidence/`
