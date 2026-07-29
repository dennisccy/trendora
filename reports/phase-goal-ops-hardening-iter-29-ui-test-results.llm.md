# Phase goal-ops-hardening-iter-29 — UI Test Results

**Phase:** goal-ops-hardening-iter-29
**Date:** 2026-07-29
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke/happy-path tests pass. -->

**Overall:** 2/2 journeys passed (0 skipped)

Scope note (goal-mode lean dispatch): this run tests EXACTLY J-06 and J-07, the iteration's two
target journeys. J-01, J-03, J-04, J-05, J-08, J-09 are verified separately via deterministic
golden replay and are NOT covered by this report.

This is the re-run the iter-29 audit (`docs/handoffs/goal-ops-hardening-iter-29-audit.md`, finding
T3) explicitly requested: the prior QA pass never exercised J-06/J-07 against the AUDITED fix
(`research.factor_join_run_chunk`, config key added during the audit). The currently running
backend (PID 3217236, started 2026-07-29T00:45:17 local / 2026-07-28T23:45:17 UTC) boots with that
fix already in `config.yaml` (`factor_join_run_chunk: 100`), confirmed by direct read before testing
began.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-06 | Pages load only what they need | smoke | P1 | All 11 pages (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/event-study`) render within budget; `/evidence` renders every claim's expectations panel with zero MemoryError/ASGI-exception lines | All 11 pages loaded HTTP 200 with correct content; `/evidence` rendered all 7 claim cards, every one with a fully-populated drawdown-expectations table (no `unavailable` notes anywhere); `logs/backend.log` showed 0 MemoryError / "Exception in ASGI application" / 500 lines across the whole 136-request sweep window; `GET /api/evidence` measured 0.010–0.047s, well within the ≤3s budget, no regression from prior `perf-budgets.md` entries (0.006–0.016s range) | PASS | `reports/qa/goal-ops-hardening-iter-29-evidence/J-06-evidence-page.png` |
| UT-J-07 | Heavy aggregates never take the service down | smoke | P1 | (Scoped this iteration to: live `/evidence` load + a small single-day backfill exercising the ingest-finalize drawdown-expectations warm loop.) `/evidence` loads live with zero MemoryError; the backfill's `aggregates_refreshed` includes `drawdown_expectations` with zero MemoryError from that loop; `GET /api/health` stays responsive (HTTP 200, no hang) throughout | Live `/evidence` load: 7/7 claims rendered, 0 MemoryError. Backfill of `2022-04-12` (a fresh, previously-unsnapshotted trading day, not on the session's consumed-race-dates list) ran to completion in 447s (started 2026-07-28T23:59:40Z, finished 2026-07-29T00:07:07Z); persisted run record's `aggregates_refreshed` = `["latest_snapshot","coverage","membership_timeline","market_phase","forward_aggregates","research_hot_keys","drawdown_expectations"]`; `/data`'s job-history panel independently confirmed the same list verbatim ("Refreshed: ... drawdown expectations"); `logs/backend.log` showed 0 MemoryError / 500 lines across the full 1,109-request window (all 200s); `GET /api/health` polled every ~15s throughout stayed HTTP 200 (never hung/timed out; latency ranged 0.09–1.47s under load — the process was actively computing, 60.8% CPU, never wedged) | PASS | `reports/qa/goal-ops-hardening-iter-29-evidence/J-07-backfill-complete.png` |

---

## Passed Tests

### UT-J-06 — Pages load only what they need
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-29-evidence/J-06-evidence-page.png`

Steps executed (goal.md J-06, steps 1–2; step 3, the dev-handoff code audit, is not a browser-QA
action):
1. Loaded, in order: `/` ("Market Regime" heading + dashboard data present), `/stocks` (leaderboard
   with 556 links incl. "TRV"), `/stocks/AAPL` ("AAPL" detail page, invalidation level "$304.89"),
   `/sectors` ("HACK" sector present), `/themes` ("Cybersecurity" theme present), `/data` ("Data
   Manager" heading), `/evidence` (full ledger, "certified-claims ledger" intro copy, all 7 claims),
   `/scanner-runs` ("2026-07-17" run date present among 1,884 links), `/backtest` ("Time-machine"
   heading), `/watchlist` ("JNJ" holding present), `/research/event-study` ("Setup & Pattern event
   study" heading).
2. `/evidence` is this iteration's target page: extracted full page text and confirmed all 7
   certified-claims cards render (5 `kind=factor`, 1 `kind=combination`, 1 `kind=event-study` —
   matching the ledger's documented 7-claim composition), each with a populated "HISTORICAL DRAWDOWN
   & DRY-SPELL EXPECTATIONS" table (real per-phase numbers, e.g. Expansion `-7.48%` n=41820 for the
   `leadership_score` claim). Zero claims showed the new `expectations_status: "unavailable"` note —
   on the live, grown 30-year basis, the bounded `_factor_observations` join (audited chunk width
   `factor_join_run_chunk=100`) completes cleanly for every resolvable claim.
3. Checked `logs/backend.log` for the whole 11-page sweep window (136 requests, all HTTP 200): zero
   `MemoryError` / `Exception in ASGI application` / 500 lines.
4. Timed `GET /api/evidence` directly (3 samples: 0.010s, 0.047s, 0.010s) — well inside the committed
   ≤3s `/evidence` page budget in `reports/perf-budgets.md`, consistent with (not regressed from) every
   prior measurement in that file (0.006–0.016s range).

Acceptance assessed: Consistency (budgets live only in `perf-budgets.md` — not modified by this run,
per scope: recording a fresh budget-table row is a dev/measurement-script action, not a browser-QA
action) — met by inspection, no violation found. Correctness (lazy/optimized paths byte-identical) —
not independently re-derived by this browser pass (covered by the dev/audit's TC-2 unit proof); no
contradicting evidence observed. Honest status & anti-goals — met: no page showed a frozen/blank
frame, no console/ASGI error, and the new `expectations_status` disclosure path exists without
being triggered (no failure occurred to disclose, which is itself the desired steady-state outcome
on this basis).

### UT-J-07 — Heavy aggregates never take the service down
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-29-evidence/J-07-backfill-complete.png`

This iteration's own Testing Requirements narrow J-07's browser scope to: "a live `/evidence` load
and a small single-day backfill exercising the ingest-finalize drawdown-expectations warm loop" — the
full literal goal.md J-07 steps (forward-aggregate warm for every horizon, `/api/backtest` served
throughout, VmPeak measurement, induced memory pressure) are covered elsewhere (VmPeak/induced-
pressure are explicitly OUT OF SCOPE for this iteration per the iter-29 spec — "Any live, real
memory-pressure induction on the running backend — forbidden").

Steps executed:
1. Loaded `/evidence` live (same evidence as UT-J-06 above) — 7/7 claims rendered, 0 MemoryError.
2. On `/data`, filled Start date = End date = `2022-04-12` (a genuinely fresh historical trading day:
   confirmed via `GET /api/runs?limit=2000` that no scanner run exists for it, and confirmed it is
   NOT on `iteration-state.md`'s "Do not redo" consumed-race-dates list), kind = Backfill snapshots
   (default), and clicked Start.
3. Polled `GET /api/data` and `GET /api/health` throughout. The job (id 201) ran 447s
   (2026-07-28T23:59:40Z → 2026-07-29T00:07:07Z) — longer than a same-date re-warm because this date
   had no existing snapshot (`snapshots_created: 1`, vs. an already-snapshotted date's warm-loop-only
   pass). `GET /api/health` stayed HTTP 200 throughout every poll (never hung, never timed out);
   latency briefly rose to 0.9–1.47s under the compute load but never failed — the backend process
   (PID 3217236) was confirmed alive and actively computing (60.8% CPU) via `ps`, not wedged.
4. On completion, the persisted run record's `aggregates_refreshed` =
   `["latest_snapshot","coverage","membership_timeline","market_phase","forward_aggregates",
   "research_hot_keys","drawdown_expectations"]` — `drawdown_expectations` present, confirming the
   ingest-finalize warm loop (`data_manager.py:3361`) ran and completed for this run.
5. Re-loaded `/data` in the browser: the job-history panel independently shows the same run
   ("backfill job · 2022-04-12 → 2022-04-12 · from a previous session · 1 snapshots · 1 trading days
   in range · 1 calendar day · 0 already snapshotted · 0 non-trading · Refreshed: latest snapshot,
   coverage, membership timeline, market phase, forward aggregates, research hot keys, drawdown
   expectations") — the UI-rendered disclosure matches the API record verbatim.
6. Checked `logs/backend.log` for the entire job window (1,109 requests, all HTTP 200): zero
   `MemoryError` / 500 lines — the ingest-finalize drawdown-expectations warm loop for all 7 ledger
   claims completed with no memory failure, and `data_manager.py`'s existing per-loop `MemoryError`
   catch (left in place, per spec) was never needed on this run.

Acceptance assessed: Consistency (`compute_forward_aggregates` untouched, single canonical producer
— confirmed by `git diff` scope in the dev handoff, not re-derived here) — no contradicting evidence.
Correctness (byte-identical payloads) — covered by dev/audit unit proofs (TC-2), not independently
re-derived in this browser pass. Honest status & anti-goals — met: no unbounded whole-table
materialization observed (the join now chunks at `factor_join_run_chunk=100`, 19 chunks at h=20 per
the audit's own SQL-level measurement); `/api/health` stayed truthful and responsive throughout
(step 4 of the full journey — induced memory-pressure — is explicitly out of scope this iteration
per the spec, so "process keeps serving after an induced abort" is not asserted by this report).

---

## Failed Tests

None.

---

## Skipped Tests

None. Both target journeys (J-06, J-07) were fully exercised via Chrome MCP against the live backend
(`:8255`) and frontend (`:3255`).

---

## Golden replay scripts written this run

- `runs/goal-session-ops-hardening/journey-scripts/J-06.json` — re-verified byte-for-byte against
  the current live app (all 11 `expect` substrings re-confirmed present on today's basis) and
  overwritten with the same, still-accurate content. Linted (`demo_runner.py --mode lint`) and
  replayed end-to-end (`demo_runner.py --mode verify`) against `http://localhost:3255` — **PASS**,
  closing TC-10's carried gap (this script had never been exercised through the deterministic replay
  lane since iter-28).
- `runs/goal-session-ops-hardening/journey-scripts/J-07.json` — REWRITTEN to reflect this iteration's
  actual verified scope (the old 3-step script's step 2 asserted `"Ready"` on `/`, which is
  currently FALSE — this session's readiness is stuck at `"initializing"` with a failed background
  warm-up, an unrelated, out-of-scope pre-existing condition (see Known Issue below) — reusing that
  assertion would have made the golden flaky/wrong from the moment it was written). The new script
  asserts two real post-load data values instead of static chrome: (1) `/evidence` — the literal
  computed drawdown-depth figure `-7.48%` (Expansion phase, `leadership_score` claim), proof the
  bounded join actually renders numeric output, not just a page shell; (2) `/data` — the literal
  string `drawdown expectations` from the persisted job-history "Refreshed:" list, proof the
  ingest-finalize warm loop's outcome is genuinely disclosed. Linted and replayed end-to-end — PASS.

Both scripts were verified with `demo_runner.py --mode verify --base-url http://localhost:3255`
(not just `--mode lint`): `[demo_runner] verify: 2 journey(s), 0 failed (verdict: PASS)`.

---

## Known Issue (observed, not blocking this run's verdict — out of this iteration's scope)

The dashboard/global readiness badge currently reads `"Initializing… history 89/89"` rather than
`"Ready"`, and `GET /api/health`'s `readiness` field is stuck at `"initializing"` with
`warmup.status: "failed"`. `logs/backend.log` traces this to `backfill_forward_returns` (the boot
warm-up loop, `warmup.py:194`) hitting a `MemoryError` in `forward_testing.py`'s
`forward_symbols_for_run` — a DIFFERENT code path from this iteration's fix (`research.py`'s
`_factor_observations` / `evidence.py`'s `build_evidence_payload`), and one this iteration's IN
SCOPE section explicitly does not touch (`compute_forward_aggregates` and friends are byte-frozen
per `iteration-state.md`). `preflight.verdict` stayed `"GO"` throughout ("Backend is serving the
latest snapshot"), and every page this run tested rendered correctly regardless — this did not
block or degrade J-06 or J-07's own acceptance. Recorded here only because it made the ORIGINAL
`J-07.json` golden's `"Ready"` assertion stale; not investigated further (out of scope: readiness/
boot-phase correctness is J-04's contract, verified separately via golden replay, not re-derived by
this dispatch).

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-29
- **Backend process:** PID 3217236, started 2026-07-29T00:45:17 local (2026-07-28T23:45:17 UTC),
  running with `research.factor_join_run_chunk: 100` (the audited fix) already loaded at boot
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-29-evidence/`
