You are the iteration-summarizer agent.

mode: normal
Phase id: goal-ops-hardening-iter-28
Output path (iteration summary): /home/dennis-chan/Git/trendora/reports/phase-goal-ops-hardening-iter-28-iteration-summary.md
Output path (project story, GOAL MODE ONLY): /home/dennis-chan/Git/trendora/runs/goal-session-ops-hardening/state/project-story.md
Agent instructions: .claude/agents/iteration-summarizer.md  <-- read this first
Template: templates/iteration-summary.md  <-- exact section structure your output must follow
(CLAUDE.md is already in your system prompt -- do not Read it again.)

Read every relevant input listed in your agent instructions. Files that don't
exist should be silently skipped. Use what is present. The dispatch wrapper
has pre-trimmed evaluator-log.md below — use the inline content.

Recent evaluator log entries (last 300 lines, pre-trimmed):
---
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: none — all 8 were already `passing`, and all 8 were RE-VERIFIED with this-iteration
  evidence, so `last_verified_iter` advances iter-25 -> iter-26 for every journey (J-01/J-03/J-04/J-05/
  J-06/J-07/J-08 by deterministic golden replay 7/7 PASS, zero FAIL rows; J-09 by the LLM lane).
- **Both iter-25 CONFIRM-REJECT gaps CLOSED** (the whole point of this iteration): (a) `reports/perf-budgets.md`
  now carries a new dated quiet-host `/api/health` section with an explicit Holds? column — all 4 statistics
  hold (official 0.092222 s, min 0.087875 s, mean 0.092081 s, max 0.094309 s; 11 raw readings, 11/11 HTTP 200)
  — plus the plain "this is the CURRENT BINDING figure, superseding iter-24" sentence TC-2 required; the diff
  is append-only (`@@ -3797,3 +3797,73 @@`, 70 insertions / 0 deletions, OWNER BUDGET AMENDMENT byte-unchanged).
  (b) J-09 step 4's failure branch now has citable evidence: a backend round-trip test asserting a crafted
  `failed` outcome is served verbatim, plus a frontend pure-function test I re-ran myself.
- Newly failing: none. Regressed (passing->failing): none. Unknown: none.
- **Anti-goal violations: TWO NEW, both `minor`, both `resolved: false`** — AG-8 (an unhandled
  `sqlite3.IntegrityError` escaped as "Exception in ASGI application" on `GET /api/backtest`) and AG-3 (the
  `/data` coverage panel showing PRICE HISTORY "— → —" / UNIVERSE 0 for a 4.9 GB populated database). Neither
  was introduced by this diff (zero `apps/backend/app/**` change); both are pre-existing paths exercised for
  the first time by this iteration's own QA. The 9 historical records stay `resolved: true`. scan-report CLEAN;
  coherence COHERENCE-PASS; all 8 `spec_hash`es match `goal_gate hash-journeys`; no `journeys-changed.md`.

**Reasoning:** I verified the gap closure on the merits — re-ran the frontend test (`npx tsx
lib/background-compute-last-outcome.test.ts` -> "2 passed"), proved the new backend test is not vacuous by
reading `readiness.py:252-255` (module-attribute lookup at call time, so the monkeypatch really binds),
confirmed the budgets section is append-only and that its window sits inside a real `start-backend.sh` boot at
18:11:43Z, and cross-checked the panel DOM against the same-moment `/api/health` payload (1623 ms -> "1.6s",
as-of 1999-11-02). Then I checked the browser-QA narrative against `logs/backend.log` and it did not hold: its
step 2 says the `/backtest` requests "returned immediately", while the log shows `total_ms` 16665.46 /
21949.24 / 23160.46 (`resolved_run_ms` 16423-23032 = a create-once `run_scan` on the request path), and
`logs/backend.log:81004` records an UNHANDLED `sqlite3.IntegrityError` ("UNIQUE constraint failed:
forward_returns.run_id, forward_returns.symbol, forward_returns.horizon") escaping to uvicorn from
`api/backtest.py:171` -> `backfill_run_forward_returns:1667` -> `_insert_run_forward_returns:390` — the first
such failure in the entire 81k-line logfile. Pulling that thread in the database (read-only) explained a second
thing I had noticed in the screenshots: `scanner_runs` 1866/1867 were created at 18:31:49.015 / 18:32:01.919 by
those two `/backtest` navigations, bumping the dataset version, while `coverage_snapshot` still holds only the
old key (newest `computed_at` 18:25:37.748) — so `/api/data` fell back to `_coverage_not_yet_computed_payload`
(`data_manager.py:908`) and `/data` displayed an empty dataset in this iteration's OWN
UT-J-09-01-data-page-top-badge.png (18:33Z), eight minutes after J-07-verify.png (18:25Z) showed
1996-01-02 -> 2026-07-22 / universe 540. Rejected REGRESSION (C.1): nothing went passing->failing, and I
classified both findings `minor` rather than critical on stated grounds — the service was never taken down
(every later request in the log answers 200 through a clean shutdown), no whole-table load occurred, and the
zero-coverage payload is a deliberate documented sentinel that self-heals at the next boot warm-up
(`warmup.py:122`) or ingest — while recording that the "UI degrades gracefully" half of AG-8 is UNVERIFIED
because nobody captured the browser at that moment. Rejected STALLED (C.2): every unblock path is
agent-tractable. Rejected GOAL_ACHIEVED (C.3): two anti-goal findings are unresolved, and certifying closure
over a server-side 500 and a screen reporting an empty database would be exactly the "met by interpretation"
pattern the iter-22 and iter-25 confirm runs rejected. Chose ESCALATE (C.4) over CONTINUE (C.5): this LEAN
iteration surfaced a cross-cutting issue — backend request path + `/data` presentation + an anti-goal
classification I could not settle from the artifacts — and the fix must lift the deliberate freeze on
`forward_testing`, so the next round needs the full pipeline (audit + ux-regression + closure), which
ESCALATE enforces mechanically.

**Next-step recommendation:** FULL depth, no new features. (1) Capture what a person actually sees when
`/backtest` is opened twice at once on a never-scanned historical date — full page, not viewport; a calm
contained error closes the AG-8 question, a blank error page is a real break. (2) Make the forward-returns
write idempotent/serialized so two concurrent requests for the same date cannot 500 — this touches
`forward_testing.backfill_run_forward_returns`, frozen since iter-24, so the planner must lift that freeze
deliberately. (3) Make `/data` honest after a time-machine visit: either refresh the stored coverage row when
a run is created outside ingest, or label the sentinel state "coverage not yet computed for this dataset
version" instead of rendering zeros. Non-blocking carries: correct the browser-QA "returned immediately"
sentence; fix the new perf-budgets section's `19:14:25Z` label (the readings are 18:14Z — local time written
as UTC); re-exercise J-09 steps 2 and 3 on a date that HAS a snapshot but incomplete aggregates (this run's
never-scanned dates made step 2 fail its own "returns immediately" wording and finished too fast for an
in-flight capture); `J-01-verify.png` == `J-03-verify.png` again (6th recurrence). OWNER, optional and
unchanged: backlog card B-1107, and whether the cold historical `/backtest` load (16-23 s measured today,
sanctioned by goal.md's "cannot be precomputed" list) should get its own written budget or move off the
request path.

## Iteration 27 — goal-ops-hardening-iter-27

**Date:** 2026-07-27T17:30:00Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: none. Re-verified passing with THIS-iteration evidence, so `last_verified_iter` advances
  iter-26 -> iter-27 for four: J-01, J-03, J-04, J-09 (deterministic golden replay, 4/4 PASS; I opened
  J-01-verify.png and J-09-verify.png myself).
- **Newly `unknown`: J-05, J-07, J-08** — this iteration's three TARGET journeys. The browser-QA agent was
  killed mid-run by an account usage limit before writing any row for them, and no `.llm.md` variant exists.
  The merged `ui-test-results.md` contains ONLY the 5-row deterministic replay lane; the ui-test-plan's own
  UT-02 (stale disclosure) and UT-06 (concurrent race) have no row, no screenshot and no DOM check. Their
  serving code CHANGED this iteration, so the iter-26 pass does not transfer. The phase-closure-auditor
  returned CLOSURE-FAIL on exactly this (DoD bullet 1); the auditor (T2) and the ux-regression reviewer each
  reached the same conclusion independently. This is an UNRUN check, not a failed one.
- **Newly `partial`: J-06** — the iteration's only FAIL row, and it is not a product regression. Detail below.
- Regressed (passing->failing): none.
- Anti-goal violations: **BOTH iter-26 findings CLOSED (now `resolved: true`); ONE NEW `minor`, unresolved.**
  New: two unhandled `MemoryError`s escaped to uvicorn on `GET /api/evidence` inside this iteration's own QA
  window (`logs/backend.log:81850`, `:81932`, both after the boot marker at `:81466`), plus the same failure
  in the background ingest-finalize path (`data_manager.py:3361`). scan-report CLEAN; coherence
  COHERENCE-PASS; all 8 `spec_hash`es match `goal_gate hash-journeys`; no `journeys-changed.md`.

**Reasoning:** I re-derived every load-bearing fact rather than inherit it. (1) **The J-06 FAIL is a stale
golden assertion, proven three ways:** I opened `J-06-verify.png` and the home page is fully rendered and
healthy (Market Regime 61.86, Market Phase 32.68, the cross-view chart) with the banner reading "GO — today's
board is current." and badges "Ready" / "provider: seed"; I read `J-06.json` and step n=1 is
`{goto "/", expect text "DEGRADED"}` — an incidental capture-time string, while steps 2-11 carry J-06's real
subject (`/stocks` "TRV", `/stocks/AAPL` "$304.89", `/sectors` "HACK", ...); and I read `config.yaml:1152`,
which points `readiness.drift.report_path` at ANOTHER session's file,
`runs/goal-session-mcp-loop/state/drift-report.json`, which is `{"status":"clean","affected":[]}` in the
working tree (git-modified away from HEAD's "drift", and re-written again today at 16:53) — a clean artifact
yields GO, so "DEGRADED" could not appear. I scored J-06 `partial` rather than `passing` because the replay
stopped at step 01, so its own per-page assertions never ran. (2) **The two iter-26 findings are genuinely
closed.** For AG-8 I re-derived the live proof from raw log lines: a genuine never-scanned-date pair on
`as_of=2015-09-09` (write_taken True/False) both answered 200, and the only IntegrityError in the 82,099-line
file is still iter-26's at `:81004`, which precedes both of this window's boot markers. For AG-3 I opened the
developer's `coverage-stale-panel.png` (cropped to the panel) and the all-zero sentinel is gone: real figures
under the calm label "Coverage as of a prior scan (version r1868-…) — refreshes on the next data job". I also
confirmed TC-10 myself — exactly one line changed in `perf-budgets.md` (19:14:25Z -> 18:14:25Z). (3) **I
corrected the audit's own attribution of the new MemoryErrors.** The auditor put both on `/api/evidence`; the
traceback ending just BEFORE the first ASGI header is actually a background thread via
`data_manager.py:3361 _refresh_ingest_aggregates`, and the two genuine ASGI ones (`:81850`, `:81932`) are both
`api/evidence.py:34 get_evidence` -> ... -> `research.py:215`. I then read `research.py:207-217` directly: the
row read IS `yield_per`-bounded, but `ret_by_run_symbol` accumulates an unbounded in-RAM dict over the whole
`forward_returns` scan — an unbounded whole-table materialization in substance, on a request path, on the deep
basis. Absent from this diff. Rejected REGRESSION (C.1): nothing went passing->failing (the only FAIL row is
an assertion the product passes by being healthier than the recording), and I classified the new AG-8 finding
`minor` on stated grounds — service never taken down (`/api/health` answered 200 between the two failures and
`/api/backtest` answered 200 right after), zero product code in this diff, host under this pipeline's own
200-test pytest against a `ulimit -v` cap, every unblock path agent-tractable. Rejected STALLED (C.2): no
human-owned blocker — the quota kill is transient (browser-QA ran normally last iteration) and all three work
items are agent work. Rejected GOAL_ACHIEVED (C.3): three Must-have journeys are `unknown`, one is `partial`,
one anti-goal finding is unresolved, and closure is CLOSURE-FAIL. Rejected ESCALATE (C.4): already full depth,
review PASS, no fail-open, no journey failed twice. **THREE THINGS I STATE PLAINLY RATHER THAN ROUND AWAY:**
(i) the developer's own evidence for both fixes is real, specific and I opened it — but it is
self-verification, and I refused to let it stand in for the DoD's browser-QA pass, because that is exactly the
substitution the iter-22 and iter-25 confirm runs rejected; (ii) QA's report is unreliable in two places the
audit caught and I re-verified — the ASGI count went 13 -> 15, not "unchanged", and QA's TC-01 re-used
`2011-03-10`, a date the developer had already scanned, so it reproduced no race (`resolved_run_ms` 1.16 /
13.47, both `write_taken=False`); (iii) nobody captured a browser on `/evidence` during either MemoryError,
and uvicorn logged no 500 access line either, so what the user actually saw is genuinely UNKNOWN — that half
of AG-8 is unverified for the third iteration running.

**Next-step recommendation:** FULL depth, no new features. (1) THE ONE BLOCKING ITEM: re-run browser-QA for
J-05, J-07 and J-08 — UT-02 (the /data prior-scan coverage disclosure), UT-06 (the concurrent `/backtest`
race, full-page capture, on a date not yet consumed — 2011-03-10 and 2015-09-09 are both used now), plus the
regression cases UT-03/UT-04/UT-07/UT-08. (2) Fix the J-06 golden, not the product: drop the incidental
"DEGRADED" expect from step 1 and move `readiness.drift.report_path` (`config.yaml:1152`) out of
`runs/goal-session-mcp-loop/`, so one session's data job cannot flip another's assertion; otherwise this FAIL
recurs every iteration and reads as a regression. (3) DECOMPOSER-PLANNED, not an opportunistic patch: bound
`research.py:215`'s `ret_by_run_symbol` accumulation and give `/api/evidence` an honest degraded response —
this is the new AG-8 finding and it also breaks the ingest finalize path. (4) OWNER, non-blocking: audit B5's
12-24 minute historical `/backtest` latencies (`:81685`, `:81766`, `:82013`) are 60-100x the 16-23 s figure
the open cold-`/backtest` budget question was framed around; B-1107 stays optional. (5) Carried, unchanged:
audit B2 (`_backfill`'s cross-call rollback residual — needs SAVEPOINT or per-run commits, its own iteration);
`test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches before removing the dangling imports
at `backtest.py:75` / `mcp/tools.py:38`; the blueprint's iter-27 rows still read "TARGETED this iteration, not
yet built" (reviewer NOTE, documentation only). (6) Framework nit, 7th recurrence:
`J-01/J-03/J-04-verify.png` are byte-identical (md5 `1fcaec8a`).

## Iteration 28 — goal-ops-hardening-iter-28

**Date:** 2026-07-27T20:45:00Z
**Verdict:** CONTINUE
**Depth dispatched:** lean
**Journey deltas:**
- **Newly passing: J-05, J-07, J-08** (`unknown` -> `passing`) and **J-06** (`partial` -> `passing`).
  The iter-27 evidence gap — its browser-QA lane was killed mid-run by an account usage limit — is
  closed by a completed re-run of the SAME plan against the UNCHANGED iter-27 build; merged file
  `reports/phase-goal-ops-hardening-iter-28-ui-test-results.md` shows 8/9 PASS, 1 SKIP (UT-04, P3).
- Re-verified passing with THIS-iteration evidence, so `last_verified_iter` advances iter-27 -> iter-28
  for J-01/J-03/J-04/J-09 (deterministic golden replay 4/4 PASS, zero FAIL rows, zero overturns).
- Newly failing: none. Regressed (passing->failing): none. Unknown: none. All 8 journeys now pass.
- Anti-goal violations: **no new finding; ONE carried, unresolved, minor** — iter-27's AG-8
  (`research.py:215`'s unbounded `ret_by_run_symbol`), deliberately out of scope per the iter spec.
  The 11 historical records stay `resolved: true`. scan-report CLEAN; coherence COHERENCE-PASS; all 8
  `spec_hash`es match `goal_gate hash-journeys`; no `journeys-changed.md`; no `browser-infra.json`.

**Reasoning:** I re-derived every load-bearing fact read-only instead of inheriting it. (1) The DB
confirms J-05 and J-08 exactly: `scanner_runs` 1872 = 2018-02-15 / 'Risk-on' / 75.13 / created
18:48:35.232536, which is precisely what `J-05-scanner-run-2018-02-15.png` renders; `data_provider_runs`
190 (18:48:26 -> 18:55:08, ok, snapshots_created 1) lists `aggregates_refreshed` = [latest_snapshot,
coverage, membership_timeline, market_phase, forward_aggregates, research_hot_keys,
drawdown_expectations], covering every aggregate J-05's acceptance names; and despite TWO concurrent
`/api/backtest` requests on the never-scanned 2018-03-15 there is EXACTLY ONE row (1873, 'Risk-on',
74.82) — matching the 74.82 rendered in `UT-06-backtest-2018-03-15.png`, a fully drawn page, not an
error page. That capture is the concurrent-race browser evidence the iter-26 AND iter-27 evaluators each
recorded as missing. (2) I verified the log claim myself: the last MemoryError/ASGI line is 82063, the
boot banner is 82115, and the file ends at 83431 — so zero errors across the whole QA window (two boots,
a 6m41s backfill, a 273 s deep-history scan, an `/evidence` load). (3) The coverage state machine
cross-checks: `coverage_snapshot` holds one row, now `r1873-…` computed 19:21:36 by job 191, while the
stale panel captured at 19:07Z is labelled `r1872-…` — exactly the version lineage the fix predicts, with
REAL figures (1996-01-02 -> 2026-07-22, universe 540), never the all-zero sentinel. (4) For J-06 I opened
the capture: the Dashboard renders `Market Regime` 61.86 under a `GO — today's board is current.` banner,
so the retired `DEGRADED` expect provably could not hold and the new one holds regardless of preflight.
Rejected REGRESSION (C.1): nothing went passing->failing, and the single open finding stays `minor` on the
iter-26/27 grounds plus new counter-evidence (no occurrence this window). Rejected STALLED (C.2): no
human-owned blocker; the remaining fix is agent work. Rejected GOAL_ACHIEVED (C.3): one anti-goal record
is unresolved, and I verified the defect is REAL and growing rather than stale — `research.py:207-217`
still accumulates `ret_by_run_symbol` over a basis I measured at 3,964,725 `forward_returns` rows /
803,042 distinct (run_id, symbol) pairs, which is the literal "unbounded whole-table load on the deep
basis" AG-8 forbids; certifying closure over it would repeat exactly the substitution the iter-22 and
iter-25 second-key CONFIRM runs rejected. Rejected ESCALATE (C.4): nothing new was surfaced — the
remaining item was already named and planned by iter-27 — so the tree lands on CONTINUE; the full-depth
need is carried in the depth recommendation instead. **FOUR THINGS I STATE PLAINLY RATHER THAN ROUND
AWAY:** (i) `UT-J-06`'s PASS row comes from the LLM lane's live 11-step reproduction, NOT from the
deterministic replay lane (which ran only the four required-still-passing journeys), so TC-9's substance
is met but its literal mechanism is still unexercised; (ii) J-07's steps 3-4 (VmPeak re-record, induced
memory-pressure abort) and J-08's steps 2/3/5 (refreshing marker, post-warm serve, never-warmed empty
state) were NOT re-run — I accepted them on carried evidence only after confirming from `git show 9928cdec`
that iter-27's hunks touch `_insert_run_forward_returns` and `coverage_from_storage` alone, leaving the
`/api/backtest` read path and `compute_forward_aggregates` untouched; (iii) `UT-07`'s screenshot is
byte-identical to `UT-06`'s (md5 75c7cbe0) — self-disclosed with a stated reason, but it means UT-07 has
no independent visual capture; (iv) DoD sub-case TC-4/UT-04 was SKIPPED as environmentally unreachable,
so one DoD checkbox is genuinely unmet.

**Next-step recommendation:** FULL depth. THE ONE BLOCKING ITEM: bound `research.py:215`'s
`ret_by_run_symbol` accumulation and give `GET /api/evidence` an honest degraded response — it is the
only unresolved anti-goal finding and it also breaks the ingest finalize path (`data_manager.py:3361`).
Full depth is right because that change lands a user-visible degraded state on the Evidence page, which is
goal.md's own written trigger ("full when an iteration first lands user-visible UI changes"), and because
it needs the audit + ux-regression + closure lanes. Ride-alongs: (2) run the FIXED `J-06.json` through the
deterministic replay lane once so TC-9's literal mechanism is exercised; (3) correct the record that
`test_readiness.py -k drift` is fixture-free — it pulled the 30-year `loaded_engine` fixture and cost
1h37m; (4) UT-04 needs a genuinely fresh-install DB fixture or an explicit written waiver. Carried,
unchanged: audit B2 (`_backfill`'s cross-call rollback residual); retarget
`test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches before removing the dangling
imports at `backtest.py:75` / `mcp/tools.py:38`. OWNER, non-blocking: the 12-24 minute historical
`/backtest` first-touch latency (this run measured 273 s for a concurrent pair on 2018-03-15) still has no
written budget; backlog card B-1107 stays optional. Framework nit, 8th recurrence: `J-01-verify.png` and
`J-04-verify.png` are byte-identical (md5 b8deb050) — J-03 was distinct this time.

## Iteration 28 — goal-ops-hardening-iter-28 (re-dispatched evaluation)

**Date:** 2026-07-27T21:20:00Z
**Verdict:** CONTINUE
**Depth dispatched:** lean
**Note on this entry:** the evaluate step for iteration 28 was dispatched a second time (the first run ended
before the engine recorded it; its `eval.md` was cleared by the re-dispatch prep and its `iteration-state.md`
was never written). I re-derived the whole evaluation from the artifacts rather than inheriting the entry
above it, and reached the same verdict. Both entries stand; this one is the completed evaluation.

**Journey deltas:**
- **Newly passing: J-05, J-07, J-08** (`unknown` -> `passing`) and **J-06** (`partial` -> `passing`).
  Iter-27's evidence gap — its browser-QA lane was killed mid-run by an account usage limit — is closed by a
  completed re-run of the SAME plan against the UNCHANGED iter-27 build. Merged file
  `reports/phase-goal-ops-hardening-iter-28-ui-test-results.md`: 8/9 PASS, 1 SKIP (UT-04, P3).
- Re-verified passing with THIS-iteration evidence, so `last_verified_iter` advances iter-27 -> iter-28 for
  J-01/J-03/J-04/J-09 (deterministic golden replay 4/4 PASS, zero FAIL rows, zero overturns).
- Newly failing: none. Regressed (passing->failing): none. Unknown: none. All 8 journeys now pass.
- Anti-goal violations: **no new finding; ONE carried, unresolved, minor** — iter-27's AG-8
  (`research.py:207-217`'s unbounded `ret_by_run_symbol`), deliberately out of scope per the iter spec. The
  11 other records stay `resolved: true`. scan-report CLEAN; coherence COHERENCE-PASS; all 8 `spec_hash`es
  match `goal_gate hash-journeys`; no `journeys-changed.md`; no `browser-infra.json`.

**Reasoning:** I re-derived every load-bearing fact read-only instead of inheriting it. (1) The database
confirms J-05 and J-08 exactly: `scanner_runs` 1872 = 2018-02-15 / 'Risk-on' / 75.13 / created
18:48:35.232536, which is precisely what `J-05-scanner-run-2018-02-15.png` renders; `data_provider_runs` 190
(18:48:26 -> 18:55:08, ok, snapshots_created 1, forward_returns_inserted 2190) lists `aggregates_refreshed` =
[latest_snapshot, coverage, membership_timeline, market_phase, forward_aggregates, research_hot_keys,
drawdown_expectations], covering every aggregate J-05's acceptance names; and for the never-scanned
2018-03-15 there is EXACTLY ONE row (1873, 'Risk-on', 74.82, created 19:01:47.200761), with `max(id)` =
`count` = 1873 — matching the 74.82 rendered in `UT-06-backtest-2018-03-15.png`, a fully drawn page, not an
error page. That capture is the concurrent-race browser evidence the iter-26 AND iter-27 evaluators each
recorded as missing. (2) I verified the log claim myself: the last MemoryError lines are 82012 / 82063 and
the last ASGI-exception lines are 81850 / 81932, all BEFORE this iteration's first boot banner at 82101;
across the window's boots at 82115 and 82797 through the file's end at 83431 there are zero of either, zero
non-200 responses of ANY kind, and 134/134 `GET /api/health` -> 200. (3) The coverage state machine
cross-checks: `coverage_snapshot` now holds one row, `r1873-…` computed 19:21:36 by job 191, while the stale
panel captured at 19:07 UTC is labelled `r1872-…` — exactly the version lineage the iter-27 fix predicts,
with REAL figures (1996-01-02 -> 2026-07-22, universe 540), never the all-zero sentinel. (4) For J-06 I
opened the capture: the Dashboard renders `Market Regime` 61.86 under a `GO — today's board is current.`
banner, so the retired `DEGRADED` expect provably could not hold and the new one holds regardless of
preflight. Rejected REGRESSION (C.1): nothing went passing->failing, and the single open finding stays
`minor` on the iter-26/27 grounds plus new counter-evidence (no occurrence this window, including a live
`/evidence` load). Rejected STALLED (C.2): no human-owned blocker; the remaining fix is agent work. Rejected
GOAL_ACHIEVED (C.3): one anti-goal record is unresolved and I confirmed the defect is REAL and sitting on a
deep basis — `research.py:207-217` still accumulates `ret_by_run_symbol` over a `forward_returns` table this
run's own `/data` panel reports at 3,964,725 rows — so certifying closure would repeat exactly the
substitution the iter-22 and iter-25 second-key CONFIRM runs rejected. Rejected ESCALATE (C.4): nothing new
was surfaced — the remaining item was already named and planned by iter-27 — so the tree lands on CONTINUE;
the full-depth need is carried in the depth recommendation instead. **FIVE THINGS I STATE PLAINLY RATHER
THAN ROUND AWAY:** (i) the QA narrative under-reports the race — the log shows FOUR overlapping requests on
2018-03-15 in two pairs, and the pair the report timed (273435.90 / 273479.83 ms) had `write_taken=False` on
BOTH, while an earlier pair (206104.88 `write_taken=True` / 207248.38) actually wrote run 1873; the claim
gets stronger, not weaker, but the report's account of it is inaccurate; (ii) `UT-J-06`'s PASS comes from
the LLM lane's live 11-step reproduction, NOT from the deterministic replay lane, so TC-9's substance is met
but its literal mechanism is still unexercised; (iii) J-07's steps 3-4 and J-08's steps 2/3/5 were NOT
re-run — I accepted them on carried evidence only after confirming from `git show 9928cdec` that iter-27's
hunks touch `_scanner_run_exists` / `coverage_from_storage` and `walk_forward_asof_dates` /
`_insert_run_forward_returns` alone, leaving `compute_forward_aggregates` and the `/api/backtest` read path
untouched; (iv) DoD sub-case TC-4/UT-04 was SKIPPED as environmentally unreachable, so one DoD checkbox is
genuinely unmet; (v) `UT-07`'s screenshot is byte-identical to `UT-06`'s (md5 75c7cbe0) — self-disclosed
with a stated reason, but UT-07 has no independent visual capture.

**Next-step recommendation:** FULL depth. THE ONE BLOCKING ITEM: bound `research.py:215`'s
`ret_by_run_symbol` accumulation and give `GET /api/evidence` an honest degraded response — it is the only
unresolved anti-goal finding and it also breaks the ingest finalize path (`data_manager.py:3361`). Full
depth is right because that change lands a user-visible degraded state on the Evidence page, which is
goal.md's own written trigger ("full when an iteration first lands user-visible UI changes"), and because it
needs the audit + ux-regression + closure lanes. Ride-alongs: (2) run the FIXED `J-06.json` through the
deterministic replay lane once so TC-9's literal mechanism is exercised; (3) correct the record that
`test_readiness.py -k drift` is fixture-free — it pulled the 30-year `loaded_engine` fixture and cost
1h37m; (4) UT-04 needs a genuinely fresh-install DB fixture or an explicit written waiver; (5) have QA
report the ACTUAL request count and each request's `write_taken` when it claims a concurrency result.
Carried, unchanged: audit B2 (`_backfill`'s cross-call rollback residual); retarget
`test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches before removing the dangling
imports at `backtest.py:75` / `mcp/tools.py:38`. OWNER, non-blocking: the historical `/backtest` first-touch
latency (this run measured 206 s and 273 s on 2018-03-15, down from iter-27's 738-1442 s but still large)
has no written budget; backlog card B-1107 stays optional. Framework nit, 8th recurrence:
`J-01-verify.png` and `J-04-verify.png` are byte-identical (md5 b8deb050) — J-03 was distinct this time.
---

Assumption ledger tail (recent entries, pre-trimmed; '(no assumptions recorded
yet)' means empty — see the 'Assumptions made' section of your instructions):
---
`MemoryError`. `docs/goal.md` does not say whether a required-still-passing journey verified while the host
was under our own test harness's memory pressure counts as verified.
**We chose:** accepted the overturn and scored J-07 `passing`, after establishing the cause myself rather
than accepting the reconciliation footer — `logs/backend.log:79986` (the only warm-up failure in the entire
logfile) plus `ps` showing the two detached pytest fixture builds started three minutes before that boot —
and after checking J-07's substance in the LLM lane's own post-restart run (12/12 HTTP 200 through a real
background window, `duration_ms 74689`, cross-checked against `forward_aggregate_cache` commit timestamps).
A human who requires every required-still-passing journey to pass its deterministic replay on the first
attempt, in-lane, would re-run the replay on a quiet box before crediting J-07.
**Reversible:** yes

## iter-26 — goal-decomposer

**Ambiguity:** the iter-25 GOAL_ACHIEVED second-key CONFIRM rejected J-09 step 4's "shows a failed background
compute with the recorded reason — never a silent failure" clause for having "no citable evidence" — every
captured panel to date renders only `completed`. `docs/goal.md` does not say whether that clause requires an
actual WITNESSED live capture of a genuinely triggered failure, or whether a deterministic code-level
round-trip (backend served-payload test + a frontend rendering unit test) is sufficient citable evidence. The
only known way to trigger a *genuine* failure on this host reproduces the unsafe 5-concurrent-BCW
memory-pressure pattern already tracked as owner-optional backlog card B-1107 (iter-22's incidental finding:
VmPeak plateaued 32 kB under the `ulimit -v` cap).
**We chose:** scoped this iteration to close the gap with (a) a new backend test that monkeypatches
`get_background_compute_status()` to return a crafted `failed` outcome and asserts `GET /api/health` serves it
verbatim, and (b) a new frontend pure-function unit test proving the panel's rendering logic shows the
`reason` string and a `danger` badge for a `failed` outcome — never re-triggering the actual unsafe failure
pattern. This mirrors the session's own established precedent (the branch-resolver `.test.ts` file was
accepted as adequate UI-behavior evidence for J-09's unknown/idle/active branches in iter-24/25) and is
bounded, safe, and fully agent-tractable without touching any byte-frozen module. A human who reads the
Acceptance clause as requiring an actual witnessed live failure capture would keep this specific sub-clause
open regardless of this iteration's test additions, and would need to authorize a bounded, safe live-trigger
mechanism (or accept B-1107's existing incidental evidence) before crediting it.
**Reversible:** yes

## iter-26 — goal-evaluator

**Ambiguity:** AG-8 (critical) forbids the deep basis "crash[ing] an existing page" and requires the UI to
degrade gracefully, "never a blank application-error page". This iteration's own evidence contains an
unhandled `sqlite3.IntegrityError` escaping as "ERROR: Exception in ASGI application" on `GET /api/backtest`
(`logs/backend.log:81004`), but nobody captured the browser at that moment, so what the user saw is unknown.
`docs/goal.md` does not say whether a server-side 500 on a request path is itself the violation, or only a
500 that reaches the user as a blank page. AG-3 (critical) is similarly open for the all-zero `/data`
coverage panel: the code calls it an honest "not yet computed" sentinel, yet the screen renders it as
ordinary figures (PRICE HISTORY "— → —", UNIVERSE 0) for a fully populated database.
**We chose:** recorded BOTH as anti-goal findings, `resolved: false`, but scored them `minor` rather than
`critical` — so the verdict is ESCALATE, not a REGRESSION halt. Grounds stated rather than assumed: the
service was never taken down (every request after the error in the logfile answers 200, through a clean
shutdown), no unbounded whole-table load occurred, the diff contains zero `apps/backend/app/**` product
code so nothing here was introduced this iteration, the zero-coverage payload is a deliberate documented
path (`data_manager.py:908`) that self-heals at the next boot warm-up or ingest, and no journey step covers
either scenario. I did not launder them: both are in `journey-history.json`, in eval.md's anti-goal table,
and they are the next iteration's first two work items. A human who reads AG-8's "never crash an existing
page" as satisfied only by a captured, contained UI error — or who reads AG-3 literally about the zeros —
would score one or both critical, which under decision tree C.1 means a REGRESSION halt for human review
instead of another agent iteration.
**Reversible:** yes

## iter-27 — goal-decomposer

**Ambiguity:** the iter-26 evaluator's AG-3 finding (a populated DB's `/data` coverage panel rendering
"— → —" / UNIVERSE 0 after a request-path historical `/backtest` view bumps `dataset_version`) and its
next-step recommendation offer two remedies: "(a) refresh the stored coverage figures when a run is created
this way, or (b) label the sentinel state ... instead of rendering zeros." `docs/goal.md`'s compute-at-ingest
principle ("boot and request paths serve stored values and never stream the full `daily_prices` table into
RAM") does not resolve which remedy is compliant, since option (a) — a live recompute triggered from the
request path — is exactly the whole-table-scan risk the Coverage payload's own iter-2/iter-3 redesign
eliminated (`_compute_coverage_uncached`'s prefill is the documented OOM/hang source).
**We chose:** option (b) — a stale-row fallback + honest `coverage_status` label, never a request-path
recompute. When the default view's exact-match `CoverageSnapshot` lookup misses (because a request-path
`ScannerRun` bumped the global `_membership_dataset_version` stamp), serve the most recent row that DOES
exist for the same `asof_key` under an older `dataset_version`, labeled `"stale"`, rather than falling to the
all-zero `not_yet_computed` sentinel or triggering a fresh `_compute_coverage_uncached` call. This keeps the
compute-at-ingest guarantee absolute (zero new DB writes/compute on the request path) while closing the
misleading-zeros defect. A human who reads goal.md's "zero silent zero-work jobs" / "displayed numbers are
correct" language as requiring the FIGURES to always reflect the CURRENT dataset version (not a labeled-stale
prior one) would instead require option (a) — an ingest-triggered refresh whenever a request-path run is
created outside ingest — accepting the request-path compute-timing exception that would introduce.
**Reversible:** yes

## iter-27 — goal-evaluator

**Ambiguity:** J-05, J-07 and J-08 were `passing` at iter-26, and this iteration changed the code that
serves them, but the browser-QA lane was killed by an account usage limit before producing any row for them.
`docs/goal.md` does not say whether a prior iteration's pass carries forward across a build that modified
that journey's own serving path, nor whether concrete developer self-verification (a real concurrent-curl
race with both requests 200, a real browser screenshot of the new label) can stand in for the browser-QA
pass the iteration spec's Definition of Done names explicitly.
**We chose:** scored all three `unknown` — not `passing`, not `failing` — and blocked GOAL_ACHIEVED on the
missing evidence rather than crediting the developer's own capture. Grounds: the methodology's own
rubber-stamp counterexample makes "no results row + no screenshot" mean `unknown` regardless of how
convincing the code evidence is; the phase-closure-auditor returned CLOSURE-FAIL on exactly this DoD bullet,
and the auditor (T2) and ux-regression reviewer independently ruled the self-verification insufficient; and
this session has twice had a GOAL_ACHIEVED rejected at the second-key CONFIRM for accepting a substitute
artifact. I did not launder the developer's evidence either — I opened it, confirmed it shows what it claims,
and recorded it inside each journey's history note as corroboration. A human who accepts developer
self-verification for a hardening-only diff (or who treats a quota kill as a harness event that should not
cost a journey its status) would score all three `passing` today and take GOAL_ACHIEVED, leaving the browser
re-run as a follow-up.
**Reversible:** yes

## iter-27 — goal-evaluator

**Ambiguity:** AG-8 (critical) forbids widening the data basis from "exhaust[ing] a service's memory" and
forbids "unbounded whole-table ORM loads ... on the deep basis". This iteration's own QA window contains two
unhandled `MemoryError`s escaping to uvicorn on `GET /api/evidence` (`logs/backend.log:81850`, `:81932`) and
two more in the background ingest-finalize path, all rooted in `research.py:215`'s unbounded
`ret_by_run_symbol` dict. `docs/goal.md` does not say whether a memory-exhaustion 500 on pre-existing,
untouched code — occurring while the host is under the pipeline's own test load against a `ulimit -v` cap —
is the critical violation AG-8 names, or a minor open finding.
**We chose:** recorded it as a NEW anti-goal finding, `resolved: false`, but scored it `minor` rather than
`critical`, so the verdict is CONTINUE and not a REGRESSION halt. Grounds stated rather than assumed: the
service was never taken down (`/api/health` answered 200 between the two failures and
`/api/backtest?as_of=2015-09-09` answered 200 immediately after), this iteration's 7-file diff contains none
of `research.py` / `samples.py` / `evidence.py` / `compute_drawdown_expectations`, the host was
simultaneously running this pipeline's own 200-test pytest under the declared memory cap, and every unblock
path is agent-tractable — a REGRESSION halt would spend a human cycle on work an agent can do. This follows
the iter-26 precedent, which classified a live 500 on a user-facing endpoint `minor` on the same reasoning
and was not vetoed. I did not launder it: it is the next iteration's second named work item, and I recorded
plainly that nobody captured a browser during either failure, so AG-8's "UI degrades gracefully / never a
blank application-error page" half is unverified for the third iteration running. A human who reads
"exhaust a service's memory" literally would score it critical, which under decision tree C.1 means a
REGRESSION halt for human review instead of another agent iteration.
**Reversible:** yes

## iter-28 — goal-evaluator

**Ambiguity:** J-07 and J-08 were `unknown` because iter-27 changed code on their path and no browser
evidence existed. This iteration's DoD mapped them to a SUBSET of their own goal.md steps (J-07 -> TC-5
smoke + TC-8 UX guard; J-08 -> TC-6 concurrent race + TC-7 already-scanned guard). Their remaining steps
were not re-run: J-07's step 3 (VmPeak re-record) and step 4 (induced memory-pressure abort), and J-08's
steps 2, 3 and 5 (last-good serve with a visible "refreshing" marker during a warm, fresh serve after the
warm, and the never-warmed empty state). `docs/goal.md` does not say how much of a journey must be
re-exercised to restore `passing` after a build touched part of its path.
**We chose:** scored both `passing` on a scope-of-change test rather than a re-run-everything test — I
confirmed from `git show 9928cdec` that iter-27's hunks are confined to
`forward_testing._insert_run_forward_returns` (plus a helper above it) and
`data_manager._scanner_run_exists` / `coverage_from_storage`, so `compute_forward_aggregates` and the
whole `/api/backtest` read path are untouched, and this iteration exercised the ONE path that did change
under a genuine concurrent race (two 273 s requests, both 200, exactly one `scanner_runs` row written).
The un-re-run steps rest on iter-22/iter-26 evidence that no code in this diff can affect. A human who
requires every step of a journey to be re-exercised whenever any part of its path changed would score
J-07 and J-08 `partial` today and order a full step-by-step re-run before closure.
**Reversible:** yes

## iter-28 — goal-evaluator

**Ambiguity:** the iteration's Definition of Done lists TC-4 (the coverage panel's "not yet computed"
state, UT-04) among J-05's pass criteria, but that state is only reachable on a genuinely fresh-install
database and this instance has 1872+ snapshot rows, so browser-QA marked it SKIP. `docs/goal.md` does not
say whether an environmentally unreachable DoD sub-case blocks the journey it was attached to.
**We chose:** scored J-05 `passing` with the skip recorded as an open, named gap rather than treating the
unmet DoD checkbox as disqualifying — because the "not yet computed" state is NOT one of J-05's four
goal.md steps (it is a third rendering state of the iter-27 coverage fix), all four of J-05's own steps
were verified this run, and the state remains covered at the API/test layer. A human who treats the
iteration's DoD as binding on the journey would score J-05 `partial` until a fresh-install database
fixture exists to point the frontend at, or until the sub-case is explicitly waived in writing.
**Reversible:** yes

## iter-28 — goal-evaluator

**Ambiguity:** J-07's Acceptance requires that "no unbounded whole-table ORM materialization remains on the
warm or serving path (`forward_returns` / `scanner_results` read column-projected and/or chunked into
bounded accumulators — AG-8)". The still-open AG-8 finding at `apps/backend/app/engine/research.py:207-217`
is literally that: a `forward_returns` scan whose rows accumulate into an unbounded in-RAM
`ret_by_run_symbol` dict, reached both from `GET /api/evidence` (a serving path) and from the ingest
finalize hook `data_manager.py:3361 _refresh_ingest_aggregates` (a warm path). `docs/goal.md` does not say
whether that clause is scoped to J-07's own named producer (`compute_forward_aggregates`) or to every warm
and serving path in the backend.
**We chose:** scored J-07 `passing`, reading the clause as scoped to J-07's own named producer and its
`/api/backtest` serving path — which this run exercised with zero non-200 responses and 134/134 healthy
`/api/health` polls through a 6m41s ingest — while treating `research.py`'s defect as what the session
already tracks it as: a separate, open AG-8 finding on a NEIGHBOURING aggregate (`drawdown_expectations` /
`GET /api/evidence`). I did not launder it: it stays `resolved: false` in journey-history, it is the single
reason GOAL_ACHIEVED is off the table this iteration, and it is the next iteration's one blocking work item.
A human who reads the clause as covering every warm/serving path would score J-07 `partial` today and hold
it there until `research.py:215` is bounded.
**Reversible:** yes

## iter-29 — goal-decomposer

**Ambiguity:** AG-8 requires the UI to "degrade gracefully (contained error boundary, honest '—'/NA
placeholder, never a blank application-error page)" when a data-basis-widening compute fails.
`docs/goal.md` does not say whether reusing the Evidence page's EXISTING silent-omission behavior (its
`DrawdownExpectationsPanel` already "renders NOTHING when `expectations` is absent/null" for a claim whose
cohort is legitimately unresolvable/out-of-scope) already satisfies "honest NA placeholder" for a NEW,
distinct failure cause (a caught per-claim compute exception), or whether that new cause must be visually
distinguishable from the pre-existing non-applicable case.
**We chose:** to make it distinguishable — this iteration's spec adds one new optional field
(`expectations_status: "unavailable"`) and a small, calm inline note on the affected claim's card,
rather than silently reusing the existing "render nothing" path for a new cause. Grounds: this session's
own established precedent for every prior "why is this value not what you'd expect" case always names the
new state explicitly instead of collapsing it into an existing one (Coverage's `coverage_status: "stale"`,
iter-27; Backtest's `evidence_status: "refreshing"`, iter-16) rather than reusing the pre-existing "not yet
computed"/absent-key convention; and AG-3's "displayed numbers are correct... not merely that the page
renders" spirit favors disclosure over silence when the reason is a defect rather than a design choice. I
did not launder the alternative: it is recorded here, and the developer/reviewer could reasonably choose
the cheaper "reuse the silent-omission" path instead if a human disagrees. A human who reads AG-8's
"honest NA placeholder" as already satisfied by the pre-existing silent-return-null behavior would drop
the new `expectations_status` field and this iteration's frontend bullet entirely, closing the finding
with a backend-only change (bound the accumulator + catch-and-continue, no new UI state).
**Reversible:** yes
---

Write the iteration summary to: /home/dennis-chan/Git/trendora/reports/phase-goal-ops-hardening-iter-28-iteration-summary.md

This is a GOAL-MODE iteration. After writing the iteration summary, also
maintain /home/dennis-chan/Git/trendora/runs/goal-session-ops-hardening/state/project-story.md per the 'Cumulative project story' section of your
agent instructions. Read the existing file if present, then rewrite it as one
flowing plain-language narrative that ends with this iteration.

Follow the section structure in templates/iteration-summary.md EXACTLY -- the
HTML renderer keys off the section headings. The verdict line must match the
form '**Verdict:** VALUE' where VALUE is one of: GOAL_ACHIEVED, CONTINUE,
ESCALATE, REGRESSION, STALLED, PASS, FAIL, IN-PROGRESS.

When finished, STOP.

Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-bed1d49d.11574" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-bed1d49d.11574" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-bed1d49d.11574"

Note: your agent definition (the .claude/agents/*.md file named above) is already loaded as your system prompt — do not Read it again; treat its 'read this first' pointer as satisfied.