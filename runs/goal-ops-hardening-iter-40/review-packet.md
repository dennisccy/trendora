# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 34438519..76a84e49 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -260,17 +260,32 @@ def _missing_data_diagnostic(session: Session, cfg: Config) -> dict:
     }
 
     # item H (iter-24 fast-platform pass): ONE bulk query for every universe member's own dates, bounded
-    # to `universe` (~len(config.universe.symbols) members — no unbounded whole-table scan) — replaces
-    # the FORMER one-`DailyPrice.date`-query-per-member loop (a query per member that HAS data, run on
-    # every cold `/api/data` coverage compute). Grouped in Python into per-symbol date sets BEFORE the
-    # existing gap-diff logic below, which is otherwise UNCHANGED — byte-identical output (a symbol's
-    # bars outside its own [first, last] range, if any, are irrelevant to that logic either way, so
-    # narrowing the query to `[first, last]` per symbol would have been equivalent; fetching the full
-    # per-symbol series here is simpler and still strictly bounded to the universe).
+    # to `universe` (~len(config.universe.symbols) members — its SCOPE is bounded, never a whole-table
+    # scan) — replaces the FORMER one-`DailyPrice.date`-query-per-member loop (a query per member that
+    # HAS data, run on every cold `/api/data` coverage compute). Grouped in Python into per-symbol date
+    # sets BEFORE the existing gap-diff logic below, which is otherwise UNCHANGED — byte-identical output
+    # (a symbol's bars outside its own [first, last] range, if any, are irrelevant to that logic either
+    # way, so narrowing the query to `[first, last]` per symbol would have been equivalent; fetching the
+    # full per-symbol series here is simpler and still strictly bounded to the universe).
+    #
+    # iter-40 (J-07 last blocker): being bounded IN SCOPE (the `WHERE ... IN (universe)` clause) is NOT
+    # the same as being bounded IN MEMORY. Iterating `session.exec(select(...))` directly makes SQLAlchemy
+    # materialize the WHOLE result via `cursor._raw_all_rows()` before this loop's body ever runs (see
+    # `sqlalchemy/orm/loading.py::chunks`) — on the deep basis that is ~3.3M `(symbol, date)` rows held
+    # live in one Python list, confirmed as the ACTUAL wedge site in iter-39's trial-3 drill (a `MemoryError`
+    # raised from this exact line's `_raw_all_rows()` call,
+    # `runs/goal-ops-hardening-iter-39/mem-drill/trial3-2650mb-wedge-evidence.txt:17-29`) and the reason
+    # three separate cap trials could never reach the aggregate-warm handlers this drill was actually
+    # targeting. `.yield_per(cfg.research.read_batch_size)` streams the SAME query in bounded-size batches
+    # instead — the SAME knob `prices.py`'s `_BarCache.prefill` / `research.py` / `forward_testing.py`
+    # already use for this exact pattern (see `prices.py:132-141`). The grouping into
+    # `own_dates_by_symbol` below and every downstream consumer are UNCHANGED — only the fetch strategy
+    # (materialize-then-iterate vs. stream-in-batches) changes; the output is byte-identical (TC-1).
     own_dates_by_symbol: dict[str, set[date_cls]] = {}
+    _diag_batch = cfg.research.read_batch_size
     for symbol, d in session.exec(
         select(DailyPrice.symbol, DailyPrice.date).where(DailyPrice.symbol.in_(universe))
-    ):
+    ).yield_per(_diag_batch):
         own_dates_by_symbol.setdefault(symbol, set()).add(d)
 
     no_history: list[dict] = []
@@ -4052,7 +4067,22 @@ def _has_open_run_record(engine: Engine, job_id: Optional[str]) -> bool:
 # ops-hardening iter-9 (F1) — how often a long-running backfill re-writes its CURRENT progress onto its
 # OPEN run-history row. One small UPDATE per interval bounds the write amplification regardless of how
 # fast dates complete, while keeping a killed job's persisted progress at most one interval stale.
-_RUN_RECORD_CHECKPOINT_INTERVAL_S = 10.0
+#
+# iter-40 (iter-39/w, AG-3 checkpoint honesty): tightened 10.0 -> 1.0. At 10s, a job whose ENTIRE run
+# completes faster than one interval only ever writes its first checkpoint (the pre-loop plan write, or
+# the first per-date call — whichever lands first after process start, since `time.monotonic()` at boot
+# is already far past 10s) and then throttles away every later per-date call for the rest of the job, so
+# a `kill -9` anywhere after that leaves the persisted row stuck near the START regardless of how far the
+# job really got — iter-39's live drill measured 18/18 dates done in memory against a persisted row still
+# reading single digits, an order-of-magnitude gap (`runs/goal-ops-hardening-iter-39/live-restart/
+# kill-test-mid-flight-state.json` vs `pre-kill-runs-state.json`). At ~1-2.5s observed per-date wall time
+# (`kill-test-mid-flight-state.json`: 18 dates / 45.18s elapsed), a 1.0s interval checkpoints roughly once
+# per date instead of once per 4-10 dates — the SAME throttled-write mechanism (unchanged call sites,
+# unchanged `message` field, unchanged `_run_detail()` serializer), just dense enough that a fast job's
+# kill-time progress is never stale by more than about one date. 1.0s also matches `job_progress.
+# poll_interval_seconds` (no UI consumer reads the row faster than that anyway, so sub-second precision
+# would buy nothing); write amplification stays bounded to at most one UPDATE per second per running job.
+_RUN_RECORD_CHECKPOINT_INTERVAL_S = 1.0
 
 
 def _checkpoint_run_record(engine: Engine, prog: JobProgress) -> None:
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 0a34b6ce..05e15a52 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -4408,6 +4408,131 @@ def test_diagnostic_query_count_does_not_scale_with_universe_size(tmp_path):
     assert small_count <= 4  # sanity bound: calendar (2) + grouped stats (1) + bulk own-dates (1)
 
 
+def test_diagnostic_own_dates_streamed_fetch_byte_identical_to_whole_result(diagnostic_engine):
+    """TC-1 (iter-40, J-07 last blocker) -- `_missing_data_diagnostic`'s own-dates scan
+    (`data_manager.py:271`) now streams via `.yield_per(cfg.research.read_batch_size)` instead of
+    materializing the whole result (the iter-39 trial-3 wedge site: a `MemoryError` inside
+    `cursor._raw_all_rows()` on this exact line,
+    `runs/goal-ops-hardening-iter-39/mem-drill/trial3-2650mb-wedge-evidence.txt:17-29`). This proves the
+    fetch-STRATEGY change is output-neutral:
+
+      1. the SAME (symbol, date) rows collected via the OLD whole-result `.all()` path (replicated here
+         as the reference -- it is no longer production code) and via the streamed `.yield_per()` path
+         group into byte-identical per-symbol date sets, and
+      2. the actual `_missing_data_diagnostic` output (`no_history`/`thin`/`intra_series_gaps`) is
+         unaffected by the batch size -- forced tiny here (3) so the fixture's rows genuinely cross
+         multiple yield_per batches, not just one, proving the streaming boundary never splits a
+         symbol's dates across an inconsistent partial read."""
+    engine, _days = diagnostic_engine
+    cfg = _diag_cfg()
+    universe = list(cfg.universe.symbols)
+
+    with Session(engine) as session:
+        # the PRE-FIX fetch strategy, replicated as the reference (no longer live in data_manager.py).
+        whole_result_dates: dict[str, set] = {}
+        for symbol, d in session.exec(
+            select(DailyPrice.symbol, DailyPrice.date).where(DailyPrice.symbol.in_(universe))
+        ).all():
+            whole_result_dates.setdefault(symbol, set()).add(d)
+
+    with Session(engine) as session:
+        # the POST-FIX fetch strategy, batch size forced small to exercise >= 2 yield_per fetches.
+        streamed_dates: dict[str, set] = {}
+        for symbol, d in session.exec(
+            select(DailyPrice.symbol, DailyPrice.date).where(DailyPrice.symbol.in_(universe))
+        ).yield_per(3):
+            streamed_dates.setdefault(symbol, set()).add(d)
+
+    assert streamed_dates == whole_result_dates  # same rows, same grouping -- fetch strategy is invisible
+    assert streamed_dates  # sanity: the fixture actually has rows to compare (not a vacuous pass)
+
+    # and the real function, driven by a config with a tiny read_batch_size, serves the SAME categorized
+    # payload as the default (much larger) batch size -- the fetch strategy never leaks into the output.
+    cfg_tiny_batch = cfg.model_copy(
+        update={"research": cfg.research.model_copy(update={"read_batch_size": 3})}
+    )
+    with Session(engine) as session:
+        diag_default = _missing_data_diagnostic(session, cfg)
+    with Session(engine) as session:
+        diag_tiny_batch = _missing_data_diagnostic(session, cfg_tiny_batch)
+    assert diag_default == diag_tiny_batch
+
+
+# ==================================================================================================
+# iter-40 (iter-39/w, AG-3) — checkpoint cadence: per-date density + throttle still bounds writes
+# ==================================================================================================
+def test_checkpoint_cadence_density_and_throttle_control(tmp_path, monkeypatch):
+    """TC-4 (iter-40) -- `_checkpoint_run_record`'s tightened interval (`_RUN_RECORD_CHECKPOINT_INTERVAL_S`,
+    10.0 -> 1.0) must land per-date checkpoints densely enough that a `kill -9` at any point never leaves
+    the persisted `dates_done` more than one checkpoint interval's worth of dates behind true in-memory
+    progress -- iter-39's live drill measured an order-of-magnitude gap (18/18 dates done in memory vs a
+    persisted row stuck in single digits) at the old 10s interval
+    (`runs/goal-ops-hardening-iter-39/live-restart/kill-test-mid-flight-state.json` vs
+    `pre-kill-runs-state.json`). Two things proven on ONE simulated run (a fake monotonic clock ticks a
+    fixed `dt` per simulated date, so the test is deterministic and fast, not wall-clock-flaky):
+
+      1. density  -- after EVERY simulated date, the persisted `dates_done` is within
+         `ceil(interval / dt)` dates of the CURRENT true `dates_done` (never further stale than the
+         interval mathematically allows for this per-date speed).
+      2. throttle -- the total write count across N dates stays well under N (the throttle still bounds
+         write amplification -- this is NOT "a write on every single date regardless of interval", which
+         would defeat the whole point of a throttle; see the pre-existing
+         `test_run_record_checkpoint_is_throttled_open_ended_and_never_fatal` in
+         test_data_manager_jobs_pipeline.py for the throttle's own unit-level contract)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'cadence.db'}")
+    create_db_and_tables(engine)
+    cfg = load_config()
+
+    fake_now = [1_000_000.0]  # start far past any interval so the FIRST checkpoint call always writes
+
+    def _fake_monotonic() -> float:
+        return fake_now[0]
+
+    monkeypatch.setattr(data_manager.time, "monotonic", _fake_monotonic)
+    interval = data_manager._RUN_RECORD_CHECKPOINT_INTERVAL_S  # the tightened production value (1.0)
+    dt = 0.3  # simulated wall-clock seconds per date -- faster than the interval (the "fast job" case
+              # iter-39 actually hit: 18 dates / 45.18s elapsed ~= 2.5s/date average, but per-date compute
+              # can be much faster than the write-serialized average once workers overlap -- 0.3s stresses
+              # the density guarantee harder than the observed case).
+    n_dates = 20
+
+    prog = JobProgress(job_id="cadence-probe", kind="backfill", start=date(2024, 1, 1), end=date(2024, 1, 20))
+    prog.dates_total = n_dates
+    data_manager._create_run_record(engine, cfg, prog)
+
+    def _persisted_dates_done() -> int:
+        with Session(engine) as session:
+            row = session.exec(select(DataProviderRun).where(DataProviderRun.job_id == "cadence-probe")).one()
+        return json.loads(row.message)["dates_done"]
+
+    write_count = 0
+    max_staleness = 0
+    for i in range(1, n_dates + 1):
+        prog.dates_done = i
+        fake_now[0] += dt
+        before = _persisted_dates_done()
+        data_manager._checkpoint_run_record(engine, prog)
+        after = _persisted_dates_done()
+        if after != before:
+            write_count += 1
+        max_staleness = max(max_staleness, prog.dates_done - after)
+
+    # density: never more than ceil(interval/dt) dates stale at any point in the simulated run.
+    allowed_staleness = -(-interval // dt)  # ceil via floor-division negation
+    assert max_staleness <= allowed_staleness, (
+        f"persisted dates_done fell {max_staleness} dates behind true progress -- more than the "
+        f"{allowed_staleness}-date budget the {interval}s interval / {dt}s-per-date rate allows"
+    )
+    # a kill "at date N" (the last iteration above) must leave persisted progress close to the true end.
+    assert n_dates - _persisted_dates_done() <= allowed_staleness
+
+    # throttle control: NOT a write on every single date -- well under n_dates writes for n_dates calls.
+    assert 0 < write_count < n_dates, (
+        f"expected the throttle to still bound writes (fewer than {n_dates} for {n_dates} calls), got "
+        f"{write_count} -- either the throttle stopped working or nothing ever wrote"
+    )
+
+
 # ==================================================================================================
 # J-37 — Pull-missing job constructor (gap-exact, dispatched through the EXISTING J-34 chunked engine)
 # ==================================================================================================
diff --git a/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py b/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
index 8f925cdb..3f2372fc 100644
--- a/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
+++ b/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
@@ -75,7 +75,12 @@ def parse_rows(text: str) -> "list[dict]":
         verdict = ""
         for c in cells:
             cu = _norm_verdict_cell(c)
-            if cu in ("PASS", "FAIL", "SKIP", "SKIPPED"):
+            # ops-hardening iter-40: BLOCKED joins the recognized verdict words, mirroring
+            # demo_runner.py's already-shipped class (a journey never checked — e.g. the backend was
+            # unreachable — distinct from FAIL, where it WAS checked and did not hold). Previously an
+            # unrecognized BLOCKED cell fell all the way through to the empty-verdict default below,
+            # silently dropping the row from `compute_overall`'s reckoning.
+            if cu in ("PASS", "FAIL", "SKIP", "SKIPPED", "BLOCKED"):
                 verdict = "SKIP" if cu == "SKIPPED" else cu
                 break
         if not verdict:
@@ -84,7 +89,7 @@ def parse_rows(text: str) -> "list[dict]":
             # the free-prose Actual column) wins over any prose that happens to
             # start with a verdict word. \b keeps "FAILED ..." prose non-matching.
             for c in reversed(cells):
-                mv = re.match(r"(PASS|FAIL|SKIPPED|SKIP)\b", _norm_verdict_cell(c))
+                mv = re.match(r"(PASS|FAIL|SKIPPED|SKIP|BLOCKED)\b", _norm_verdict_cell(c))
                 if mv:
                     cu = mv.group(1)
                     verdict = "SKIP" if cu == "SKIPPED" else cu
@@ -118,17 +123,29 @@ def verdict_for(text: str, test_id: str) -> str:
 
 def compute_overall(rows: "list[dict]", file_verdicts: "list[str] | None" = None) -> str:
     """Overall verdict. Surviving rows are authoritative; only when NO rows could
-    be parsed do we fall back to the input files' headline verdicts."""
+    be parsed do we fall back to the input files' headline verdicts.
+
+    Priority FAIL > BLOCKED > PASS > SKIP/SKIPPED — ops-hardening iter-40, mirroring
+    demo_runner.py's already-shipped `compute_regression_verdict` (BLOCKED is a DISTINCT class from
+    FAIL: it means a journey's own assertions were never checked at all — e.g. the backend was
+    unreachable — not that they were checked and failed; goal_gate.py already blocks achievement on
+    any BLOCKED cell regardless of this headline, so this fixes the LLM-readable summary only). Before
+    this fix an all-BLOCKED merged run fell through both branches below to the SKIPPED default,
+    because BLOCKED matched neither "FAIL" nor "PASS" in either list — never a bare `PASS`."""
     verdicts = [r["verdict"] for r in rows if r["verdict"]]
     if verdicts:
         if "FAIL" in verdicts:
             return "FAIL"
+        if "BLOCKED" in verdicts:
+            return "BLOCKED"
         if "PASS" in verdicts:
             return "PASS"
         return "SKIPPED"
     file_verdicts = file_verdicts or []
     if "FAIL" in file_verdicts:
         return "FAIL"
+    if "BLOCKED" in file_verdicts:
+        return "BLOCKED"
     if "PASS" in file_verdicts:
         return "PASS"
     return "SKIPPED"
@@ -157,14 +174,18 @@ def merge(texts: "list[str]") -> str:
     overall = compute_overall(rows, file_verdicts)
     n_pass = sum(1 for r in rows if r["verdict"] == "PASS")
     n_skip = sum(1 for r in rows if r["verdict"] == "SKIP")
+    n_blocked = sum(1 for r in rows if r["verdict"] == "BLOCKED")
     total = len(rows)
 
+    overall_line = f"**Overall:** {n_pass}/{total} journeys passed ({n_skip} skipped"
+    overall_line += f", {n_blocked} blocked" if n_blocked else ""
+    overall_line += ")"
     out = ["# UI Test Results (merged)", "",
            f"**Date:** {_today()}",
            "**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)",
            "", "---", "",
            f"**Browser QA Verdict:** {overall}", "",
-           f"**Overall:** {n_pass}/{total} journeys passed ({n_skip} skipped)",
+           overall_line,
            "", "---", "", "## Results Table", "",
            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |",
            "|---------|------|------|----------|----------|--------|---------|----------|"]
@@ -174,6 +195,7 @@ def merge(texts: "list[str]") -> str:
 
     failed = [r for r in rows if r["verdict"] == "FAIL"]
     skipped = [r for r in rows if r["verdict"] == "SKIP"]
+    blocked = [r for r in rows if r["verdict"] == "BLOCKED"]
     if failed:
         out += ["## Failed Tests", ""]
         for r in failed:
@@ -187,6 +209,15 @@ def merge(texts: "list[str]") -> str:
             out += [f"### {r['test_id']} — {_cell(r, _C_NAME)}", "",
                     "**Verdict:** SKIPPED",
                     f"**Reason:** {_cell(r, _C_ACTUAL)}", ""]
+    if blocked:
+        out += ["## Blocked Tests", "",
+                "_Not a journey failure — its own assertions were never checked (e.g. the backend was "
+                "unreachable). Distinct from FAIL: FAIL means the journey's own assertions did not "
+                "hold; BLOCKED means they were never checked._", ""]
+        for r in blocked:
+            out += [f"### {r['test_id']} — {_cell(r, _C_NAME)}", "",
+                    "**Verdict:** BLOCKED",
+                    f"**Reason:** {_cell(r, _C_ACTUAL)}", ""]
     out += ["## Environment", "",
             "- **Browser:** Chromium (LLM browser-qa + deterministic replay)",
             f"- **Test Date:** {_today()}", ""]
@@ -465,6 +496,44 @@ def _self_test() -> int:
         new, voided = void_text(mass, ["J-99"])
         assert voided == [] and new == mass
 
+    def t_blocked_all_headlines_blocked():
+        # TC-6 (iter-40) — two input files whose surviving rows are ALL BLOCKED merge to a BLOCKED
+        # headline, never PASS (falls through both `verdicts`/`file_verdicts` "PASS" checks) or
+        # SKIPPED (the pre-fix default when nothing else matched).
+        f1 = (
+            "**Browser QA Verdict:** BLOCKED\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-01 | Backfill honors range | regression | P1 | e | backend unreachable | BLOCKED | none |\n")
+        f2 = (
+            "**Browser QA Verdict:** BLOCKED\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-03 | No per-run range cap | regression | P1 | e | backend unreachable | BLOCKED | none |\n")
+        rows = parse_rows(f1)
+        assert rows[0]["verdict"] == "BLOCKED", rows
+        md = merge([f1, f2])
+        assert file_top_verdict(md) == "BLOCKED", file_top_verdict(md)
+        assert "## Blocked Tests" in md and "UT-J-01" in md and "UT-J-03" in md
+        assert "## Failed Tests" not in md and "## Skipped Tests" not in md
+
+    def t_fail_still_wins_over_blocked():
+        # TC-7 (iter-40) — a merged set with at least one FAIL and at least one BLOCKED headlines FAIL
+        # (FAIL still wins), mirroring demo_runner.py's compute_regression_verdict ordering.
+        mixed = (
+            "**Browser QA Verdict:** FAIL\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-05 | Aggregates precomputed | regression | P1 | e | zeros shown | FAIL | a.png |\n"
+            "| UT-J-06 | Pages load lazily | regression | P1 | e | backend unreachable | BLOCKED | none |\n")
+        md = merge([mixed])
+        assert file_top_verdict(md) == "FAIL", file_top_verdict(md)
+        assert "## Failed Tests" in md and "## Blocked Tests" in md
+        # and directly against compute_overall, independent of any markdown rendering:
+        assert compute_overall([{"verdict": "FAIL"}, {"verdict": "BLOCKED"}]) == "FAIL"
+        assert compute_overall([{"verdict": "BLOCKED"}, {"verdict": "PASS"}]) == "BLOCKED"
+        assert compute_overall([{"verdict": "BLOCKED"}, {"verdict": "SKIP"}]) == "BLOCKED"
+
     def t_void_respects_escaped_pipes():
         # The replay renderer escapes '|' in cells; void must not split on it.
         esc = (
@@ -492,6 +561,8 @@ def _self_test() -> int:
               ("annotated_verdicts", t_annotated_verdicts),
               ("verdict_for_tolerates_annotated_cells", t_verdict_for_tolerates_annotated_cells),
               ("tc_prefixed_fail_survives", t_tc_prefixed_fail_survives),
+              ("blocked_all_headlines_blocked", t_blocked_all_headlines_blocked),
+              ("fail_still_wins_over_blocked", t_fail_still_wins_over_blocked),
               ("void_rewrites_and_recomputes", t_void_rewrites_and_recomputes),
               ("void_keeps_unlisted_fail", t_void_keeps_unlisted_fail),
               ("void_no_match_is_noop", t_void_no_match_is_noop),
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 126 ++++++++++++++++++++-
 .../state/preflight-verdict-history.jsonl          |   2 +
 .../state/drift-report.json                        |   2 +-
 runs/goal-session-ops-hardening/telemetry.jsonl    |   9 ++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |   2 +
 6 files changed, 140 insertions(+), 3 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
