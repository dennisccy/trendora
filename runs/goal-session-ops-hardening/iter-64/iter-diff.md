# Iteration diff (bounded)

Files changed: 4. Shown in full: 3.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `incredible_auto_dev/scripts/automation/lib/demo_runner.py` (210 lines not shown)

```diff
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 6a2c7d34..1bb28266 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -6057,19 +6057,27 @@ def test_missing_data_diagnostic_cooperative_yield_byte_identical(diagnostic_eng
     """TC-2/TC-5 (ops-hardening iter-63, J-07 GIL-hold bound) -- the `time.sleep(0)` cooperative yield
     added at each `_diag_batch` chunk boundary of the own-dates scan (data_manager.py, just above the
     `for symbol, d in session.exec(...)` loop) is a SCHEDULING-ONLY change: it must never change which
-    rows are read, how they group, or the served diagnostic payload. Proven against a PINNED pre-fix
-    reference oracle -- the SAME query consumed with NO cooperative yield, replicated here exactly as it
-    ran before this iteration (mirrors test_universe_resolver.py's iter-53 reference-oracle pattern, and
-    this same file's own `test_diagnostic_own_dates_streamed_fetch_byte_identical_to_whole_result`, which
-    proved the streaming-vs-materialize choice was invisible; this test proves the ADDED yield point is
+    rows are read, how they group, or the served diagnostic payload.
+
+    Corrected (ops-hardening iter-64, TC-8): only the ROW-COUNT SANITY CHECK below (item 1 -- the
+    fixture's own-dates shape, 11 rows) is pre-fix-equivalent -- it reproduces the plain `session.exec`
+    grouping with no yield involved at all, so it would group identically whether or not the fix exists.
+    The BYTE-IDENTICAL assertion itself (item 2) is NOT compared against any pre-fix oracle: both sides
+    are POST-fix calls to the real `_missing_data_diagnostic` (which always yields, unconditionally --
+    there is no pre-fix code path left to call), one with `read_batch_size` forced to 2 and one with the
+    default (much larger) batch size, so the comparison instead proves the batch width -- and therefore
+    how many times the yield fires -- never leaks into the served payload (mirrors this same file's own
+    `test_diagnostic_own_dates_streamed_fetch_byte_identical_to_whole_result`, which proved the
+    streaming-vs-materialize choice was invisible the same way; this test proves the ADDED yield point is
     invisible too):
 
-      1. the reference oracle's `own_dates_by_symbol` grouping (no yield) is reproduced by the fixture's
-         known shape (AAA 6 + BBB 2 + CCC 3 + DDD 0 = 11 rows);
+      1. the fixture's own-dates grouping (a plain, yield-free `session.exec`) is exactly its known shape
+         (AAA 6 + BBB 2 + CCC 3 + DDD 0 = 11 rows) -- a sanity check on the fixture, not a comparison
+         target for item 2;
       2. the real (post-fix) `_missing_data_diagnostic`, run with `read_batch_size` forced to 2 -- so the
          11-row result genuinely crosses MULTIPLE `yield_per` chunks, not one -- serves the BYTE-IDENTICAL
-         payload the default (much larger) batch size serves, proving the batch width (and therefore how
-         many times the yield fires) never leaks into the output;
+         payload the default (much larger) batch size's own (also post-fix) call serves, proving the batch
+         width (and therefore how many times the yield fires) never leaks into the output;
       3. `time.sleep(0)` is actually invoked the expected number of times (5 -- floor(11/2), rows 2/4/6/
          8/10 hit the modulo boundary; row 11 does not reach a 6th multiple of 2) and ALWAYS with argument
          0 (never a real pause) -- proving the cooperative-yield code path is genuinely exercised by this
diff --git a/incredible_auto_dev/scripts/automation/lib/common.sh b/incredible_auto_dev/scripts/automation/lib/common.sh
index da3e04e9..53220802 100644
--- a/incredible_auto_dev/scripts/automation/lib/common.sh
+++ b/incredible_auto_dev/scripts/automation/lib/common.sh
@@ -1431,7 +1431,7 @@ _wait_for_frontend_ready() {
 # Returns 0 once the payload's `readiness` field == "ready", 1 on timeout or an empty/unset url (a no-op
 # in that case — nothing to gate on).
 _wait_for_backend_readiness() {
-  local url="$1" max_wait="${2:-${CHAIN_BACKEND_READY_WAIT_S:-60}}" tag="${3:-wait}"
+  local url="$1" max_wait="${2:-${CHAIN_BACKEND_READY_WAIT_S:-90}}" tag="${3:-wait}"
   [[ -n "$url" ]] || return 0
   local waited=0 state=""
   echo "[$tag] Waiting for backend readiness (the 'readiness' field of $url) to reach 'ready' (max ${max_wait}s)..."
diff --git a/incredible_auto_dev/scripts/automation/lib/demo_runner.py b/incredible_auto_dev/scripts/automation/lib/demo_runner.py
index dba151b2..304204be 100644
--- a/incredible_auto_dev/scripts/automation/lib/demo_runner.py
+++ b/incredible_auto_dev/scripts/automation/lib/demo_runner.py
@@ -17,7 +17,8 @@ needs no changes.
 Self-test (no browser, no network):
   python3 demo_runner.py self-test
 
-Exit codes: 0 ok/soft-skip · 2 bad args/JSON · 3 playwright missing · 4 no DISPLAY (live)
+Exit codes: 0 ok/soft-skip · 2 bad args/JSON, or (record/live) the `{{AUTO_UNSNAPSHOTTED_DATE}}`
+sentinel could not be resolved (see `resolve_sentinel_date`) · 3 playwright missing · 4 no DISPLAY (live)
 · 5 verify found ≥1 FAIL · 6 browser infrastructure failure (launch/crash — verify only;
 callers route replay journeys back to the LLM lane so nothing is silently unverified)
 · 7 verify: backend unreachable BEFORE any journey ran — every journey is written BLOCKED
@@ -32,6 +33,7 @@ from __future__ import annotations
 import datetime
 import json
 import os
+import sqlite3
 import struct
 import sys
 import urllib.error
@@ -200,6 +202,133 @@ def probe_backend_health(url: str, timeout: float = 5.0) -> bool:
         return False
 
 
+
+# ── sentinel-date resolver (ops-hardening iter-64) ────────────────────────────
+#
+# WHY: four consecutive rounds (iter-58, iter-59 x2, iter-62/63, iter-63-audit) hand-rotated
+# J-05's golden onto a date that the SAME round's own replay lane then consumed, arming a
+# guaranteed false FAIL on a currently-passing journey next round. The durable fix is a
+# run-time self-selecting mechanism, not another hand rotation (J-05.json's own `_notes`
+# call for this verbatim). A golden carrying the token below has that date resolved fresh,
+# every replay, against whatever the DB's `scanner_runs` table looks like AT THAT MOMENT —
+# so a date consumed by any run (this iteration's own drill, a prior replay, a manual
+# verification) is automatically excluded, with no file edit required.
+
+SENTINEL_TOKEN = "{{AUTO_UNSNAPSHOTTED_DATE}}"
+
+# The benchmark symbol every `scanner_runs` row is computed against (its own `benchmark`
+# column — confirmed live, 2026-08-11: every existing row reads "SPY", never anything else).
+# A resolved date is useless for a real backfill unless a SPY bar exists for it, so the query
+# below requires one explicitly.
+_SENTINEL_BENCHMARK_SYMBOL = "SPY"
+
+# A bounded historical window, not the full 1996-2026 basis. Deliberately starts AFTER SPY's
+# own earliest row in this seed (measured 2026-08-11: SPY's first daily_prices bar is
+# 2005-02-25 — a real, if unusual, property of this committed seed, not a gap: 1996-2004 has
+# OTHER symbols' bars but no SPY at all, which would silently break a resolved date's backfill
+# were it not excluded by the `_SENTINEL_BENCHMARK_SYMBOL` join below). 2005-03-01..2016-12-31
+# carries 2,195 SPY trading days with zero `scanner_runs` rows as of this iteration (measured
+# the same day) — a bounded slice of the committed seed, never a whole-table scan, with years
+# of headroom at the historical ~1 consumed date/iteration rate before it would need widening.
+_SENTINEL_WINDOW_START = "2005-03-01"
+_SENTINEL_WINDOW_END = "2016-12-31"
+
+
+def resolve_sentinel_date(db_path: "str | os.PathLike",
+                          window_start: str = _SENTINEL_WINDOW_START,
+                          window_end: str = _SENTINEL_WINDOW_END,
+                          benchmark_symbol: str = _SENTINEL_BENCHMARK_SYMBOL) -> str:
+    """Read-only resolution of `SENTINEL_TOKEN`: the earliest trading day inside
+    `[window_start, window_end]` that BOTH carries a `daily_prices` bar for
+    `benchmark_symbol` (the symbol every `scanner_runs` row is computed against — a date
+    without one cannot produce a real backfill row) AND carries ZERO `scanner_runs` rows for
+    that date, i.e. is eligible for a single-date J-05 backfill.
+
+    Opened `mode=ro` — this never mutates the database. Fails EXPLICITLY (raises
+    RuntimeError naming the reason) when the db file is missing or the window is exhausted
+    (every eligible day in it already snapshotted) — the caller must never fall back to
+    guessing or silently reusing a consumed date; per this iteration's spec, that failure is
+    the whole point of the resolver over another hand-picked date."""
+    path = Path(db_path)
+    if not path.exists():
+        raise RuntimeError(f"sentinel resolution failed: database not found at {path}")
+    uri = f"file:{path.resolve()}?mode=ro"
+    try:
+        conn = sqlite3.connect(uri, uri=True)
+    except sqlite3.OperationalError as exc:
+        raise RuntimeError(f"sentinel resolution failed: could not open {path} read-only: {exc}") from exc
+    try:
+        row = conn.execute(
+            "SELECT date FROM daily_prices WHERE symbol = ? AND date >= ? AND date <= ? "
+            "AND date NOT IN (SELECT asof_date FROM scanner_runs) "
+            "ORDER BY date ASC LIMIT 1",
+            (benchmark_symbol, window_start, window_end),
+        ).fetchone()
+    finally:
+        conn.close()
+    if row is None:
+        raise RuntimeError(
+            "sentinel resolution failed: no eligible unsnapshotted trading day (with a "
+            f"{benchmark_symbol} bar) in [{window_start}, {window_end}] — every eligible day "
+            "in the window already has a scanner_runs row; widen the window rather than "
+            "reusing a consumed date")
+    return row[0]
+
+
+def script_needs_sentinel(script: object, token: str = SENTINEL_TOKEN) -> bool:
+    """True iff `token` appears anywhere in the script's JSON (any step's fill text, expect
+    text, click-target text, or the script's own `name`) — checked structurally so no field
+    is missed, never by assuming which fields might carry it."""
+    return token in json.dumps(script)
+
+
+def substitute_sentinel_in_script(script: dict, resolved_date: str,
+                                  token: str = SENTINEL_TOKEN) -> dict:
+    """Return a NEW script with every occurrence of `token` in every string value replaced by
+    `resolved_date` — recursively, so fill targets, expect text, click-target text, and the
+    script's own `name` field all receive the SAME resolved date, however deeply nested.
+    `script` itself is left untouched."""
+    def _walk(node):
+        if isinstance(node, str):
+            return node.replace(token, resolved_date) if token in node else node
+        if isinstance(node, dict):
+            return {k: _walk(v) for k, v in node.items()}
+        if isinstance(node, list):
+            return [_walk(v) for v in node]
+        return node
+    return _walk(script)
+
+
+def resolve_and_substitute_sentinel(script: dict, db_path: "str | os.PathLike",
+                                    token: str = SENTINEL_TOKEN) -> "tuple[dict, str | None]":
+    """If `token` appears anywhere in `script`, resolve it ONCE against `db_path` and
+    substitute the SAME resolved date everywhere it appears. Returns `(script, None)`
+    unchanged when the token is absent (the common case — most goldens carry no sentinel).
+    Propagates `resolve_sentinel_date`'s RuntimeError when the token IS present but
+    resolution fails — callers must treat that as a real failure, never a silent SKIP."""
+    if not script_needs_sentinel(script, token):
+        return script, None
+    resolved = resolve_sentinel_date(db_path)
+    return substitute_sentinel_in_script(script, resolved, token), resolved
+
+
+def default_sentinel_db_path(repo_root: "str | None") -> Path:
+    """The committed dev DB the sentinel resolver reads. `repo_root` is the SAME value every
+    caller already passes as `--repo-root` (demo-phase.sh, replay-lane.sh); fall back to a
+    path derived from this file's own location so an unaugmented CLI call (e.g. a developer
+    running the self-test or a manual `--mode verify`) still resolves correctly.
+
+    Deliberately `Path(__file__).absolute()`, NOT `.resolve()`: `scripts/` is a git-tracked
+    symlink to `incredible_auto_dev/scripts/` (same physical file, two paths), and `.resolve()`
+    follows it — which would climb out through the framework subtree's OWN root
+    (`incredible_auto_dev/`, which has no `apps/`) instead of this project's repo root. Every
+    real caller invokes this file through the unresolved `scripts/...` path (bash's `pwd`
+    stays logical by default), so `__file__` already carries the right ancestry without
+    resolving it."""
+    root = Path(repo_root) if repo_root else Path(__file__).absolute().parents[3]
+    return root / "apps" / "backend" / "data" / "trendora.db"
+
+
 def _today() -> str:
     return datetime.date.today().isoformat()
 
@@ -616,6 +745,139 @@ def _t_probe_backend_health() -> None:
         thread.join(timeout=2.0)
 
 
+def _make_sentinel_fixture(tmp_dir: str, dates_with_bars: list, snapshotted_dates: tuple = (),
+                           non_benchmark_dates: tuple = ()) -> str:
+    """A throwaway sqlite fixture with the same two tables/columns the real committed DB
+    carries (`daily_prices.date`/`.symbol`, `scanner_runs.asof_date`) — enough for
+    `resolve_sentinel_date` to run its real query against, without touching
+    `apps/backend/data/trendora.db`. `dates_with_bars` get a SPY row (the default benchmark);
+    `non_benchmark_dates` get a bar for a DIFFERENT symbol only — reproducing the real
+    committed seed's own shape (1996-2004 has other symbols' bars but no SPY at all)."""
+    db_path = os.path.join(tmp_dir, "sentinel-fixture.db")
+    conn = sqlite3.connect(db_path)
+    conn.execute("CREATE TABLE daily_prices (id INTEGER PRIMARY KEY, symbol TEXT, date TEXT)")
+    conn.execute("CREATE TABLE scanner_runs (id INTEGER PRIMARY KEY, asof_date TEXT)")
+    for d in dates_with_bars:
+        conn.execute("INSERT INTO daily_prices (symbol, date) VALUES (?, ?)", ("SPY", d))
+    for d in non_benchmark_dates:
+        conn.execute("INSERT INTO daily_prices (symbol, date) VALUES (?, ?)", ("AAPL", d))
+    for d in snapshotted_dates:
+        conn.execute("INSERT INTO scanner_runs (asof_date) VALUES (?)", (d,))
+    conn.commit()
+    conn.close()
+    return db_path
+
+
+def _t_resolve_sentinel_date_requires_benchmark_bar() -> None:
+    # Real bug this test locks in (found live against apps/backend/data/trendora.db,
+    # 2026-08-11): a date can have SOME symbol's bar without carrying a SPY bar (this
+    # committed seed's own 1996-2004 span is exactly that shape) -- a resolver that only
+    # checked "any daily_prices row" would hand back a date the real backfill/scanner_runs
+    # computation cannot use (every scanner_runs row is computed against `benchmark`="SPY").
+    import tempfile
+    with tempfile.TemporaryDirectory() as tmp:
+        db = _make_sentinel_fixture(
+            tmp, dates_with_bars=["2005-01-05"], non_benchmark_dates=["2005-01-03", "2005-01-04"])
+        got = resolve_sentinel_date(db, "2005-01-01", "2005-01-31")
+        assert got == "2005-01-05", got  # the two non-SPY dates must be skipped, not returned
+
+
+def _t_resolve_sentinel_date_picks_earliest_eligible() -> None:
+    import tempfile
+    with tempfile.TemporaryDirectory() as tmp:
+        db = _make_sentinel_fixture(
+            tmp, ["2000-01-05", "2000-01-04", "2000-01-06"], snapshotted_dates=["2000-01-04"])
+        got = resolve_sentinel_date(db, "2000-01-01", "2000-01-31")
+        assert got == "2000-01-05", got  # earliest date that is NOT already snapshotted
+
+
+def _t_resolve_sentinel_date_fails_when_window_exhausted() -> None:
+    # Error case (Testing Requirements): zero eligible dates in the window must fail
+    # explicitly, never silently reuse an already-snapshotted date.
+    import tempfile
+    with tempfile.TemporaryDirectory() as tmp:
+        db = _make_sentinel_fixture(tmp, ["2000-01-05"], snapshotted_dates=["2000-01-05"])
+        try:
+            resolve_sentinel_date(db, "2000-01-01", "2000-01-31")
+            raise AssertionError("expected RuntimeError: window exhausted")
+        except RuntimeError as exc:
+            assert "no eligible" in str(exc), exc
+
+
+def _t_resolve_sentinel_date_missing_db() -> None:
+    try:
+        resolve_sentinel_date("/nonexistent/path/does-not-exist-demo-runner-fixture.db")
+        raise AssertionError("expected RuntimeError: db not found")
+    except RuntimeError as exc:
+        assert "not found" in str(exc), exc
+
+
+def _t_resolve_sentinel_date_self_renews_after_consumption() -> None:
+    # TC-3: given a throwaway sqlite fixture seeded with a scanner_runs row for the date the
+    # resolver most recently returned, when the resolver is invoked again against that same
+    # fixture, then it returns a DIFFERENT date (not the just-consumed one) with 0
+    # scanner_runs rows for it -- proven at the unit level, not a second live 20-minute
+    # browser replay (this iteration's own OUT OF SCOPE note).
+    import tempfile
+    with tempfile.TemporaryDirectory() as tmp:
+        db = _make_sentinel_fixture(tmp, ["2000-01-05", "2000-01-06", "2000-01-07"])
+        first = resolve_sentinel_date(db, "2000-01-01", "2000-01-31")
+        assert first == "2000-01-05", first
+        conn = sqlite3.connect(db)
+        conn.execute("INSERT INTO scanner_runs (asof_date) VALUES (?)", (first,))
+        conn.commit()
+        conn.close()
+        second = resolve_sentinel_date(db, "2000-01-01", "2000-01-31")
+        assert second != first, (first, second)
+        assert second == "2000-01-06", second
+
+
+def _t_script_needs_sentinel_detects_token() -> None:
+    assert script_needs_sentinel(
+        {"steps": [{"action": {"type": "fill", "text": SENTINEL_TOKEN}}]}) is True
+    assert script_needs_sentinel(
+        {"steps": [{"action": {"type": "fill", "text": "2010-01-01"}}]}) is False
+
+
+def _t_substitute_sentinel_in_script() -> None:
+    script = {
+        "name": f"... target date {SENTINEL_TOKEN} must have 0 snapshot rows ...",
+        "steps": [
+            {"n": 1, "action": {"type": "fill", "target": {"testid": "x"}, "text": SENTINEL_TOKEN}},
+            {"n": 2, "action": {"type": "click", "target": {"text": SENTINEL_TOKEN}},
+             "expect": {"text": f"Immutable snapshot — as of {SENTINEL_TOKEN}"}},
+        ],
+    }
+    out = substitute_sentinel_in_script(script, "2000-01-05")
+    assert SENTINEL_TOKEN not in json.dumps(out)
+    assert out["steps"][0]["action"]["text"] == "2000-01-05"
+    assert out["steps"][1]["action"]["target"]["text"] == "2000-01-05"
+    assert out["steps"][1]["expect"]["text"] == "Immutable snapshot — as of 2000-01-05"
+    assert "2000-01-05" in out["name"], out["name"]
+    # the SAME resolved date landed everywhere the token appeared.
+    assert SENTINEL_TOKEN in script["name"], "original script must be left untouched"
+
+
+def _t_resolve_and_substitute_sentinel_noop_without_token() -> None:
+    script = {"name": "plain", "steps": [{"n": 1, "action": {"type": "goto", "url": "/"}}]}
+    out, resolved = resolve_and_substitute_sentinel(script, "/nonexistent/does-not-matter.db")
+    assert out is script, "unchanged script object when the token is absent (no DB touched)"
+    assert resolved is None
+
+
+def _t_resolve_and_substitute_sentinel_propagates_failure() -> None:
+    script = {"name": SENTINEL_TOKEN, "steps": [{"n": 1, "action": {"type": "goto", "url": "/"}}]}
+    try:
+        resolve_and_substitute_sentinel(script, "/nonexistent/does-not-matter.db")
+        raise AssertionError("expected RuntimeError to propagate when the token IS present")
+    except RuntimeError:
+        pass
+
+
+def _t_default_sentinel_db_path_repo_root() -> None:
+    assert default_sentinel_db_path("/x/y") == Path("/x/y/apps/backend/data/trendora.db")
+
+
 def _t_run_verify_blocked_when_backend_unreachable() -> None:
     # TC-5 end-to-end (no real browser launch reached — the probe short-circuits BEFORE
     # Playwright ever opens a page): backend unreachable -> rc 7, every journey BLOCKED, never
@@ -675,6 +937,114 @@ def _t_launch_chromium_retries() -> None:
     assert _DeadChromium.calls == 2
 
 
+class _FakeLocator:
+    """Duck-typed Playwright Locator, just enough surface for `_do_action`/`_find` to work
+    against it: `.first`, `.wait_for(...)` (raises TimeoutError when `fail=True`, else
+    no-ops), `.click(...)` / `.fill(...)` (spy-recorded)."""
+
+    def __init__(self, spy: dict, name: str, fail: bool = False):
+        self._spy = spy
+        self._name = name
+        self._fail = fail
+
+    @property
+    def first(self):
+        return self
+
+    def wait_for(self, state: str = "visible", timeout: float = 0):
+        if self._fail:
+            raise TimeoutError(f"fake: {self._name} did not become visible")
+
+    def click(self, timeout: float = 0):
+        self._spy["click_calls"] = self._spy.get("click_calls", 0) + 1
+        self._spy.setdefault("clicked", []).append(self._name)
+
+    def fill(self, text: str, timeout: float = 0):
+        if self._fail:
+            raise TimeoutError(f"fake: cannot fill {self._name}")
+        self._spy.setdefault("filled", []).append((self._name, text))
+
+
+class _FakePage:
+    """Duck-typed Playwright Page — only the methods `_do_action`/`_settle_for_capture`
+    actually call. Every method NOT defined here (e.g. `.locator()`, `.evaluate()`,
+    `.wait_for_load_state()`) is absent on purpose: every real call site wraps those in a
+    bare `except Exception: pass`, so a missing attribute is silently swallowed exactly like
+    a real best-effort miss — no need to fake the whole Playwright surface."""
+
+    def __init__(self, spy: dict, fail_target: "tuple | None" = None):
+        self._spy = spy
+        self._fail_target = fail_target
+
+    def _loc(self, kind: str, value) -> _FakeLocator:
+        return _FakeLocator(self._spy, f"{kind}:{value}", fail=(kind, value) == self._fail_target)
+
+    def get_by_role(self, role: str, name: str = ""):
+        return self._loc("role", (role, name))
+
+    def get_by_text(self, text: str):
+        return self._loc("text", text)
+
+    def get_by_label(self, label: str):
+        return self._loc("label", label)
+
+    def get_by_placeholder(self, placeholder: str):
+        return self._loc("placeholder", placeholder)
+
+    def get_by_test_id(self, testid: str):
+        return self._loc("testid", testid)
+
+    def goto(self, url: str, wait_until: "str | None" = None, timeout: float = 0):
+        self._spy.setdefault("goto", []).append(url)
+
+    def wait_for_timeout(self, ms: int):
+        pass
+
+    def screenshot(self, path: "str | None" = None):
+        self._spy.setdefault("screenshots", []).append(path)
+
+
+def _t_run_record_never_clicks_after_failed_precondition() -> None:
+    # TC-4: given a fake page/script fixture where step N's `fill` raises and step N+1 is a
+    # `click` on `role: button`, when the record loop executes that script, then step N+1's
+    # click is NEVER invoked (asserted via a call-count spy), a screenshot is still captured
+    # for step N+1, and the results write-up carries a soft note naming the skip.
+    import tempfile
+    spy: dict = {}
+    steps = [
+        {"n": 1, "title": "Target one unsnapshotted historical trading day", "journey": "J-05",
+         "action": {"type": "fill", "target": {"testid": "job-start-date"}, "text": "2010-11-22"}},
+        {"n": 2, "title": "Start the backfill", "journey": "J-05",
+         "action": {"type": "click", "target": {"role": "button", "name": "Start"}}},
+    ]
+    page = _FakePage(spy, fail_target=("testid", "job-start-date"))
+    with tempfile.TemporaryDirectory() as tmp:
+        captured, soft_notes, script_steps = _record_steps(
+            page, steps, "http://localhost:3000", 4000, Path(tmp), None)
+    assert spy.get("click_calls", 0) == 0, "the mutating click must never be invoked"
+    assert len(captured) == 2, captured  # a screenshot is still captured for BOTH steps
+    assert len(spy.get("screenshots", [])) == 2, spy
+    assert any("step 02" in note.lower() and "skipped" in note.lower() for note in soft_notes), soft_notes
+    assert len(script_steps) == 2
+
+
+def _t_run_record_click_still_fires_without_a_prior_failure() -> None:
+    # Control case: no preceding failure -> the mutating click IS performed normally.
+    spy: dict = {}
+    steps = [
+        {"n": 1, "title": "Open the Data Manager", "action": {"type": "goto", "url": "/data"}},
+        {"n": 2, "title": "Start the backfill", "action": {
+            "type": "click", "target": {"role": "button", "name": "Start"}}},
+    ]
+    page = _FakePage(spy)
... [diff_bound] incredible_auto_dev/scripts/automation/lib/demo_runner.py: 210 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
index fa4aab00..5bc39ca7 100644
--- a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
+++ b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
@@ -338,7 +338,7 @@ replay_lane_partition_and_verify() {
     # yet (J-01 step 09 / J-04 step 02, iter-62). Best-effort only — a timeout logs a warning and this
     # still proceeds (never a new hang/hard-fail mode for a project or backend state where `readiness`
     # never reaches "ready").
-    _wait_for_backend_readiness "${QA_BACKEND_HEALTH_URL:-}" "${CHAIN_BACKEND_READY_WAIT_S:-60}" "replay-lane" || true
+    _wait_for_backend_readiness "${QA_BACKEND_HEALTH_URL:-}" "${CHAIN_BACKEND_READY_WAIT_S:-90}" "replay-lane" || true
     _replay_lane_log "Regression (deterministic replay): $R_REPLAY"
     local _replay_csv _replay_rc=0
     _replay_csv="$(echo "$R_REPLAY" | tr ' ' ',' | sed 's/^,*//;s/,*$//')"
```
