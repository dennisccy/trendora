# Iteration 11 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The iteration delivered real, honest work on a literally empty product diff: a fresh cold-boot
measurement (1.364 s, ≤5 s, under the host-guard-hardened launcher), a file:line code audit of four
Data-Contract rows, host-guard-confined pytest, and an 11-page real-browser sweep whose page TTIs are
all comfortably in budget. But J-06 does **not** close. Three gaps I verified myself: (1) the sweep's
numbers were never written into `reports/perf-budgets.md` (the artifact J-06's own "single source"
acceptance names) — that file was last written at 20:24 UTC, ~15 min *before* the sweep ran, and its own
scope note says the sweep is not attempted there; (2) `GET /api/indexes?full=true` on `/data` read
2066.3 ms and 2671.8 ms against a committed ≤1.5 s budget, and the one in-budget re-read (4.7 ms) is by
the lane's own admission a different call pattern, i.e. not a like-for-like control; (3) the `[NEW]`
`--session-live` walkthrough its Acceptance names is still unproduced with no human deferral on record.

More important: the browser lane's central claim — that all three anomalies were *environmental*
host contention — is **refuted by the backend's own logfile and host telemetry**. During the same
window the backend hit its own `ulimit -v` 6144 MB cap: two `ingest forward-aggregate warm aborted …
memory pressure` MemoryErrors from an unbounded `select(ScannerResult)…all()`, and two on-load
endpoints returned **HTTP 500** (`/api/methodology`, `/api/research/event-study`) via
`RuntimeError: can't start new thread`. The host had 12–20 GB free throughout, so ambient load cannot
explain a per-process address-space exhaustion. This is the carried, owner-deferred critical AG-8
dimension firing live — and the lean lanes both missed it. That is exactly the cross-cutting
complexity the tree routes to the full pipeline.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | `reports/phase-goal-ops-hardening-iter-11-regression-replay-results.md` UT-J-01 PASS; `reports/qa/goal-ops-hardening-iter-11-evidence/J-01-verify.png` (opened — `/data` live, Ready badge, real coverage tiles). Corroborated: `data_provider_runs` id 121 = 2026-05-02→2026-05-03, `status ok`, `dates_total 0`, `non_trading_days 2` — the exact zero-work weekend outcome. |
| J-03 | passing | passing | Same replay artifact, UT-J-03 PASS; `J-03-verify.png` (byte-identical to J-01's — both goldens end on `goto /data`; the discriminating assertions are the per-step text expects). Corroborated: run 122 = 2025-06-01→2026-07-17, `calendar_days 412`, `dates_done 283/283`, `status ok`, no cap rejection. |
| J-04 | passing | passing | `…-ui-test-results.llm.md` UT-J-04 PASS (6 steps). Steps 1-2 fresh (1.364 s boot, `reports/perf-budgets.md`). Steps 5-6 fresh; **I re-ran both claims myself**: `grep -c "Finished server process \[2080333\]" logs/backend.log` → 0, while `Finished server process [2100030]` is present at line 26838; boot banner + host-guard caps at `logs/backend.log:27066-27069`. Step 6 DOM capture matches `data_provider_runs` id 119 (`interrupted`, `snapshots_created 117`, `dates_done 158/504`, `calendar_days 729 / already 41 / non-trading 225`). Steps 3-4 carried from iter-9 on a provably zero-diff code path. |
| J-05 | passing | passing | Replay UT-J-05 PASS; `J-05-verify.png`. **Caveat recorded (not a failure):** the replay's own two backfills (runs 121/122) finalized with `aggregates_refreshed = [coverage, membership_timeline, research_hot_keys, drawdown_expectations]` — `forward_aggregates` is absent because its warm aborted on MemoryError (`logs/backend.log:27185`, `:27233`). J-05 step 2(b) names five aggregates and `forward_aggregates` is not among them, and the run record is *honest* about what it refreshed, so no literal acceptance step failed. |
| J-06 | partial | **partial** (unchanged — target not met) | `…-ui-test-results.llm.md` UT-J-06 PASS(claimed) + `UT-J-06-perf-sweep-summary.txt`; 11 screenshots (I opened `UT-J-06-06-data-top.png`, `-11-research-event-study.png` — both render fully and correctly, no blank/frozen frame). Gaps G1/G2/G3 below. |

### Why J-06 stays `partial`

- **G1 — measurements not recorded in the canonical artifact.** `reports/perf-budgets.md` mtime is
  20:24 UTC; the sweep ran 20:38–20:52 UTC. Its new section contains only TC-3 (boot) and TC-4 (audit)
  and states verbatim that "this developer pass does not attempt the real-browser 11-page TTI/on-load
  sweep." goal.md J-06 step 2 requires the measurements be recorded there; the Acceptance's
  "Consistency (single source)" bullet says budgets and fresh numbers live *only* in that file. The
  numbers currently exist only in a QA evidence `.txt`.
- **G2 — one on-load endpoint out of budget, with no valid control.** `/api/indexes?full=true` on
  `/data`: 2066.3 ms then 2671.8 ms vs ≤1.5 s. The "clean" 4.7 ms re-read is described in the lane's
  own file as "a single call, not the earlier two-call pattern" — a cache-shaped reading, not a
  repeat of the measured condition. The historical committed row for this endpoint on `/data` is
  ~0.9–1.0 s, so this is a 2–2.7× excursion. The WARN is disclosed (good) but not written to
  `perf-budgets.md` (TC-2's own requirement).
- **G3 — walkthrough.** The `[NEW]`-flagged `demo.sh ops-hardening --session-live` walkthrough of
  budgets-vs-live-loads is still unproduced (carried since iter-5/6). No human deferral on record.
- **Console check is a disclosed no-op** (`# TODO: Console logging not yet implemented`) — correctly
  disclosed, and not itself a J-06 acceptance item, so it does not add a gap.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials (AG-7) | OK | `iter-11/scan-report.md` CLEAN; `iter-diff.md` = "(no changes)"; no new config/env file exists to eyeball. |
| Paid/external SaaS (AG-9) | OK | No manifest touched — the product diff is empty (independently confirmed by coherence's `git diff --stat -- apps/` → empty). |
| License changes | OK | scan-report CLEAN; no LICENSE diff (empty diff). |
| Fabricated/substituted data (AG-3) | OK | TC-5 byte-identity ran live and passed (coverage/membership-timeline `stored == fresh`; forward-aggregates `json.dumps(fresh)==miss==hit`). Run records 119/121/122 read straight from sqlite match the rendered DOM strings. The `/research` page even in its error state showed a message, not fabricated figures. |
| AG-1 / AG-2 / AG-4 / AG-5 / AG-6 (proven-language, no-lookahead, referee) | OK | Zero source change; no new displayed value; coherence PASS. |
| **AG-8 — memory exhaustion / unbounded ORM loads** | **VIOLATED — carried critical entry, now live-observed (unresolved)** | `logs/backend.log`: 21 `MemoryError` occurrences; `:27185` and `:27233` = `ingest forward-aggregate warm aborted at horizon 1 — memory pressure`, raised at `apps/backend/app/engine/forward_testing.py:826` — `session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()`, an unbounded ORM materialization of the 329 MB `scanner_results` table, reached via `data_manager.py:3229 _refresh_ingest_aggregates → forward_aggregates_cached`. Downstream: `:27601 GET /api/methodology → 500` and `:27660 GET /api/research/event-study?view=episodes → 500` with `RuntimeError: can't start new thread`. NOT ambient: `logs/hwmon/hwmon.csv` over 20:35–21:00 UTC shows MemAvailable 12.2–20.6 GB and load1 0.4–3.1 — other processes cannot consume this process's `ulimit -v` 6144 MB. **Mitigation that is real:** iter-8's `except MemoryError` abort branches held — `/api/health` stayed 200 throughout, later requests returned 200, no manual restart (materially better than iter-7). |
| AG-10 — host resource ceiling | OK this iteration; iter-10's minor entry now **resolved** | Launcher compliance live in the boot banner (`logs/backend.log:27068 host-guard: cpu_list=0-3,8-11 blas_threads=4`). Pytest was confined this time (`taskset -c 0-3,8-11` + OMP/OPENBLAS/MKL/NUMEXPR=4, dev handoff "Tests Run") — the iter-10 finding's fix. My hwmon check over the pytest window (20:10–20:45 UTC, 1999 samples): peak Tctl 88 °C vs the 95 °C watchdog, no trip. |
| Coherence | COHERENCE-PASS | `iter-11/coherence.md`; git-verified empty `apps/` diff. No consolidation mandate. |

## Next-Step Recommendation

Next iteration **full depth** (audit + closure + ux-regression lanes), no new features:

1. **OWNER DECISION, item 1, do not let an agent invent it.** Scope or formally amend/defer the AG-8
   dimension: `forward_aggregates_cached → compute_forward_aggregates`
   (`forward_testing.py:826`) materializes an unbounded `ScannerResult` set and OOMs under the
   declared 6144 MB cap. It is no longer theoretical — it fired ~3× this iteration and produced two
   HTTP 500s on ordinary page loads. It hard-blocks GOAL_ACHIEVED. Options: (a) scope a bounded/
   streamed/chunked rewrite of that query, (b) amend goal.md to accept the graceful-abort behaviour
   explicitly, (c) raise the cap (does not fix the unbounded pattern). Also still open:
   `HOST_GUARD_REQUIRE_MARKERS`, and the J-05/J-06 `--session-live` walkthroughs (produce or defer).
2. **Close J-06's G1** — append the 11-page sweep (every reading, including both over-budget
   `/api/indexes` values and the `/api/health` outlier, with the WARNs) to `reports/perf-budgets.md`
   as a dated section. The data already exists in
   `reports/qa/goal-ops-hardening-iter-11-evidence/UT-J-06-perf-sweep-summary.txt`; this is
   transcription, not re-measurement.
3. **Close J-06's G2 honestly** — re-measure `/api/indexes?full=true` on `/data` with three
   consecutive cache-disabled loads on a quiet host **with no ingest running**, and record the result
   either way. Do not accept a 4.7 ms cached read as the control.
4. **Correct the record** — the auditor must re-examine TC-4's "No genuine violation found": the audit
   verified cache-HIT paths are bounded but never checked the MISS/compute path that is actually
   OOMing. The spec's own rule ("name it precisely, do not fix it inline") should have applied.
5. **Ask the auditor to confirm** that runs 120/121/122's `aggregates_refreshed` set of 4-of-7 on
   zero-new-date runs is by design (`latest_snapshot`/`market_phase` legitimately skipped) and that
   `forward_aggregates`' absence is solely the MemoryError abort — J-05's contract depends on it.
6. **Operator note:** the Trendora backend and frontend are **not running now** (no `uvicorn`/`next`
   process; nothing listening on :8255/:3255; `logs/backend.log` ends `INFO: Shutting down` with no
   `Finished server process` line). The next browser lane needs them restarted.

Carried framework items unchanged: `merge_ui_test_results.py` FAIL-cell drop (benign this iteration),
the `Frontend Present: no` browser-qa-skip misrouting, `runs/goal-ops-hardening-iter-11/status.json`
stuck at `dev_complete`/`browser_checks_run: false` despite a completed browser lane, and the
pre-existing `tests/test_db.py::test_create_all_produces_expected_tables` failure. Evidence-labelling
nit: the browser-qa artifacts stamp local times with a `Z` suffix (`21:38Z-21:52Z` is really
20:38–20:52 UTC).

## Halt Justification

Not halting. Tree walk: (1) no journey moved `passing`/`already_passing` → `failing`; the unresolved
critical AG-8 entry is the carried, human-known, three-times-deferred item and this iteration's product
diff is **empty** (scan-report CLEAN, `iter-diff.md` "(no changes)", coherence git-verified), so nothing
was introduced or worsened here — same reading iter-8/9/10 applied, logged again in `assumptions.md`.
(2) Not STALLED — items 2-5 above are concrete agent-owned work. (3) Not GOAL_ACHIEVED — J-06 is
`partial` and a critical anti-goal is unresolved. (4) **ESCALATE fires**: this lean iteration surfaced
cross-cutting complexity its own lanes mis-adjudicated — browser-qa attributed a live per-process
memory exhaustion (two 500s) to ambient host load, and the dev audit certified "no unbounded scan"
while an unbounded ORM load was OOMing in the same process. That needs the full pipeline's independent
auditor and closure gates, not another lean pass.

**If the owner reads decision-tree C.1's "a critical anti-goal violation is unresolved → REGRESSION"
literally, a halt here is defensible and I would not argue against it.** GOAL_ACHIEVED is unreachable
until AG-8 is scoped or amended, and no amount of agent work changes that.
