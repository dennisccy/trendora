# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

```diff
diff --git a/apps/backend/tests/test_start_frontend_script.py b/apps/backend/tests/test_start_frontend_script.py
index 65173dc9..151e4b04 100644
--- a/apps/backend/tests/test_start_frontend_script.py
+++ b/apps/backend/tests/test_start_frontend_script.py
@@ -103,6 +103,12 @@ _TC3_77_PORT = 21600 + _offset
 # ops-hardening iter-77 AUDIT FIX ROUND 2: the build-guard (21700) and backend-retarget (21800) tests.
 _TC4_77_PORT = 21700 + _offset
 _TC5_77_PORT = 21800 + _offset
+# ops-hardening iter-78: the launcher's own residue-purge regression test's range (21900), clear of
+# every range claimed above.
+_TC6_78_PORT = 21900 + _offset
+# ops-hardening iter-78 AUDIT FIX (finding B1): the live-server-aware purge test's range (22000),
+# clear of every range claimed above.
+_TC7_78_PORT = 22000 + _offset
 
 # A cold scratch-dir `next build` (a distDir name Next has never seen -> no webpack cache to reuse) on
 # this host-guard-CPU-masked host measured ~1 minute with the box idle, but blew past 300 s while the live
@@ -118,6 +124,14 @@ _START_TIMEOUT_S = float(os.environ.get("TRENDORA_FRONTEND_START_TIMEOUT_S", "12
 
 _BROKEN_SOURCE_REL = "__tc3_intentionally_broken.ts"
 _SCRATCH_DIST_GLOB = ".next-test-*"
+# ops-hardening iter-78: `_BROKEN_SOURCE_REL` above is now ALSO the exact name
+# `scripts/start-frontend.sh` reserves for its own residue purge (kept in lockstep by hand --
+# see that script's "TEST-RESIDUE PURGE" block) -- a real launcher invocation now unconditionally
+# DELETES that filename before building, so it can no longer be used to prove "a genuinely broken
+# source file makes `next build` fail" (the purge would silently remove it first). TC-3 below uses
+# this SEPARATE name instead -- still a throwaway `.ts` file cleaned by the same
+# `_purge_test_residue()` self-heal, but deliberately outside the launcher's own reserved/purged set.
+_BROKEN_BUILD_SOURCE_REL = "__tc3_broken_build_source.ts"
 
 
 def _scratch_dist_name(tag: str) -> str:
@@ -132,9 +146,10 @@ def _purge_test_residue() -> None:
     repo's pre-existing `.next-alt-qa`/`.next-verify` dirs. Called on fixture SETUP as well as teardown --
     see the module docstring: a SIGKILLed pytest runs no teardown, so the next run must self-heal rather
     than fail on residue it did not create."""
-    broken = FRONTEND_DIR / _BROKEN_SOURCE_REL
-    if broken.exists():
-        broken.unlink()
+    for name in (_BROKEN_SOURCE_REL, _BROKEN_BUILD_SOURCE_REL):
+        broken = FRONTEND_DIR / name
+        if broken.exists():
+            broken.unlink()
     for scratch in FRONTEND_DIR.glob(_SCRATCH_DIST_GLOB):
         shutil.rmtree(scratch, ignore_errors=True)
 
@@ -539,12 +554,18 @@ def test_broken_source_fails_build_and_leaves_no_stray_process(launcher):
     outcome -- including a failed assertion, an unexpected exception, or an interrupted run -- is a single
     unconditional delete, performed by the autouse `_pristine_frontend_tree` fixture's teardown (and again
     at the NEXT run's setup, since a SIGKILLed pytest runs no teardown at all -- exactly how a previous
-    run left this file behind and made this test fail on its own guard assertion)."""
+    run left this file behind and made this test fail on its own guard assertion).
+
+    ops-hardening iter-78: uses `_BROKEN_BUILD_SOURCE_REL`, NOT `_BROKEN_SOURCE_REL` -- the launcher now
+    unconditionally purges `_BROKEN_SOURCE_REL` as reserved test-residue (see
+    `test_launcher_purges_leftover_test_residue_from_a_different_process` below) before it ever runs
+    `next build`, so that name can no longer be used to prove a genuine build failure propagates; this
+    test needs a name the purge does NOT touch."""
     if not (FRONTEND_DIR / "node_modules").exists():
         pytest.skip("apps/frontend/node_modules not installed -- cannot build the frontend")
 
     dist_rel = _scratch_dist_name("tc3")
-    broken_file = FRONTEND_DIR / _BROKEN_SOURCE_REL
+    broken_file = FRONTEND_DIR / _BROKEN_BUILD_SOURCE_REL
     assert not broken_file.exists(), f"{broken_file} already exists -- refusing to overwrite"
     broken_file.write_text(
         "// Deliberately invalid TypeScript -- ops-hardening iter-33 TC-3 smoke test.\n"
@@ -569,6 +590,121 @@ def test_broken_source_fails_build_and_leaves_no_stray_process(launcher):
         _owning_pid(_TC3_PORT, timeout=3.0)
 
 
+def test_launcher_purges_leftover_test_residue_from_a_different_process(launcher):
+    """ops-hardening iter-78 -- closes iter-77/c ('fixed inside the round; NOT defended against
+    recurrence'): a hard-killed run of THIS test module leaves `__tc3_intentionally_broken.ts` /
+    `.next-test-*` scratch dirs behind in the live `apps/frontend` tree (module docstring); this
+    module's own autouse `_pristine_frontend_tree` fixture already self-heals its OWN next run, but the
+    REAL launcher previously had no such defense and took the whole frontend down the moment `next
+    build` type-checked the stray file (reproduced by TC-3 immediately above).
+
+    This test proves the LAUNCHER's own defense, not this module's self-heal: the residue is written
+    directly in the test BODY -- i.e. strictly AFTER the autouse fixture's own setup-purge already ran
+    -- simulating "a different process wrote it and this module is not the next thing invoked" (the
+    module was already clean when this test started; nothing here relies on the module's own leftover
+    cleanup). It then runs the REAL `scripts/start-frontend.sh` end-to-end (never a mock) and asserts a
+    clean build (rc reaching `next start`, never TC-3's failure path), a fully-styled served page, and
+    that the launcher's own log records the purge -- proving the fix is in the LAUNCH SCRIPT, not merely
+    this test module's pre-existing residue cleanup (which already ran before this file even existed)."""
+    if not (FRONTEND_DIR / "node_modules").exists():
+        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")
+
+    dist_rel = _scratch_dist_name("residue")
+    broken_file = FRONTEND_DIR / _BROKEN_SOURCE_REL
+    assert not broken_file.exists(), f"{broken_file} already exists -- refusing to overwrite"
+    # Written HERE, in the test body -- after the autouse `_pristine_frontend_tree` fixture's own
+    # setup-purge already ran -- so this residue is provably NOT something this module's own setup left
+    # behind; it stands in for a DIFFERENT process's interrupted run.
+    broken_file.write_text(
+        "// Deliberately invalid TypeScript -- simulates leftover residue from an interrupted\n"
+        "// test_start_frontend_script.py run (ops-hardening iter-78 residue-defense regression test).\n"
+        "// Removed by the LAUNCHER itself (this test's own subject), independent of this module's own\n"
+        "// autouse cleanup, which would also remove it at teardown regardless of this test's outcome.\n"
+        "const __trendora_test_residue_broken__: string = 12345;\n"
+    )
+    orphan_scratch = FRONTEND_DIR / _scratch_dist_name("orphan")
+    orphan_scratch.mkdir()
+    (orphan_scratch / "sentinel.txt").write_text("leftover scratch dist dir from a different process\n")
+
+    launched = launcher(dist_rel, _TC6_78_PORT, _TC6_78_PORT + 1000, "residue-defense.log")
+    _wait_for_port_answering(
+        _TC6_78_PORT, timeout=_BUILD_TIMEOUT_S, proc=launched.proc, log_path=launched.log_path
+    )
+    assert (launched.dist_abs / "BUILD_ID").exists(), (
+        "expected the launcher's own `next build` to succeed once the residue is purged"
+    )
+    _assert_page_fully_styled(_TC6_78_PORT)
+
+    log_text = launched.log_text()
+    assert "purged leftover test-residue" in log_text, (
+        f"expected the launcher's own purge log line; got:\n{log_text[-4000:]}"
+    )
+    assert "next build FAILED" not in log_text, (
+        f"the residue must never reach `next build` at all; got:\n{log_text[-4000:]}"
+    )
+    assert not broken_file.exists(), "the launcher must have deleted the residue file before building"
+    assert not orphan_scratch.exists(), "the launcher must have deleted the orphan scratch dist dir too"
+
+
+def test_residue_purge_spares_a_scratch_dist_dir_another_live_server_is_serving(launcher):
+    """ops-hardening iter-78 AUDIT FIX (finding B1). The residue purge above deletes every
+    `.next-test-*` dir EXCEPT this invocation's own `$NEXT_DIST_DIR`. That exclusion is not sufficient:
+    two launcher invocations pointed at DIFFERENT scratch dirs (two overlapping runs of this very module
+    on one host -- the contention iter-78's own dev handoff records hitting) would each classify the
+    OTHER's dir as abandoned leftover and `rm -rf` it out from under a LIVE `next start`, tearing a
+    running server's assets mid-flight. That is exactly the harm the iter-77 `.trendora-serving` marker
+    exists to prevent, and the purge ran before that guard was ever consulted.
+
+    Proven against the REAL script, with a real live process: a scratch dir carrying a serving marker
+    for a live, node-like pid must SURVIVE, while an unmarked sibling in the same glob is still purged
+    -- so the fix is a genuine narrowing (leftover residue still goes), never a blanket disable."""
+    if not (FRONTEND_DIR / "node_modules").exists():
+        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")
+
+    # Stand-in for ANOTHER launcher's live `next start`: a real long-lived process whose /proc cmdline
+    # satisfies the same node/next/npx/taskset PID-reuse guard the script applies.
+    live_server = subprocess.Popen(
+        ["node", "-e", "setTimeout(() => {}, 900000)"],
+        stdout=subprocess.DEVNULL,
+        stderr=subprocess.DEVNULL,
+    )
+    protected = FRONTEND_DIR / _scratch_dist_name("live-served")
+    orphan = FRONTEND_DIR / _scratch_dist_name("orphan-unserved")
+    try:
+        protected.mkdir()
+        (protected / "sentinel.txt").write_text("another live server's dist dir -- must never be purged\n")
+        (protected / ".trendora-serving").write_text(
+            f"pid={live_server.pid}\nport=1\ndist={protected.name}\nstarted_at=now\n"
+        )
+        orphan.mkdir()
+        (orphan / "sentinel.txt").write_text("abandoned leftover -- must still be purged\n")
+
+        dist_rel = _scratch_dist_name("live-guard")
+        launched = launcher(dist_rel, _TC7_78_PORT, _TC7_78_PORT + 1000, "residue-live-guard.log")
+        _wait_for_port_answering(
+            _TC7_78_PORT, timeout=_BUILD_TIMEOUT_S, proc=launched.proc, log_path=launched.log_path
+        )
+
+        log_text = launched.log_text()
+        assert (protected / "sentinel.txt").exists(), (
+            "the launcher must NOT purge a scratch dist dir another live server is serving; log:\n"
+            f"{log_text[-4000:]}"
+        )
+        assert "another live server is serving it" in log_text, (
+            f"expected the launcher to log why it spared that dir; got:\n{log_text[-4000:]}"
+        )
+        assert not orphan.exists(), (
+            "an unmarked leftover scratch dir must STILL be purged -- the guard narrows the purge, it "
+            f"does not disable it; log:\n{log_text[-4000:]}"
+        )
+        assert (launched.dist_abs / "BUILD_ID").exists(), "the launcher's own build must still succeed"
+    finally:
+        live_server.kill()
+        live_server.wait(timeout=10)
+        shutil.rmtree(protected, ignore_errors=True)
+        shutil.rmtree(orphan, ignore_errors=True)
+
+
 # ==================================================================================================
 # ops-hardening iter-43 (goal.md "Additional binding notes", the iter-33/i owner item) -- TC-5:
 # start-frontend.sh now carries the SAME HOST-GUARD cap block scripts/start-backend.sh already applies.
diff --git a/apps/frontend/components/readiness-provider.tsx b/apps/frontend/components/readiness-provider.tsx
index afcdde72..99eaf14f 100644
--- a/apps/frontend/components/readiness-provider.tsx
+++ b/apps/frontend/components/readiness-provider.tsx
@@ -9,6 +9,7 @@ import {
   type ReadinessState,
   type WarmupProgress,
 } from "@/lib/api";
+import { deriveLiveStaleForS } from "@/lib/staleness-tick";
 
 /**
  * Global backend readiness state (iter-28, J-40). A single client context, mounted in the app shell, that
@@ -51,7 +52,13 @@ export interface ReadinessContextValue {
    *  served readiness/preflight/background-compute payload was computed; 0 for a fresh synchronous
    *  compute), first rendered by the readiness badge/preflight banner's "as of {N}s ago" annotation.
    *  Null before the first poll resolves / on a failed poll — readers must never render a stale or
-   *  fabricated number in that case (mirrors every sibling field's honesty convention). */
+   *  fabricated number in that case (mirrors every sibling field's honesty convention).
+   *
+   *  ops-hardening iter-78 — this value now TICKS between polls: a local 1-second interval re-derives
+   *  it (`lib/staleness-tick.ts`'s `deriveLiveStaleForS`, the last poll's own base + elapsed client
+   *  seconds since it was received) so it grows smoothly instead of freezing at the last-polled number
+   *  for up to the full poll-idle interval. Still the SAME single value, re-formatted only by the
+   *  existing `formatStaleAnnotation` — no second poll, no second endpoint, no second formatter. */
   staleForS: number | null;
 }
 
@@ -74,6 +81,13 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
   // freshest value without re-subscribing.
   const activeMs = useRef(BOOTSTRAP_ACTIVE_MS);
   const idleMs = useRef(BOOTSTRAP_ACTIVE_MS);
+  // ops-hardening iter-78 — the last poll's own `stale_for_s` base and the client wall-clock time (ms
+  // since epoch) it was RECEIVED at, so the 1-second tick below can re-derive a live value between
+  // polls without re-fetching or re-subscribing. Refs (not state): the tick interval reads the freshest
+  // pair on every fire, and writing them never itself needs to trigger a render (setStaleForS below does
+  // that instead).
+  const staleBaseRef = useRef<number | null>(null);
+  const staleReceivedAtMsRef = useRef<number | null>(null);
 
   useEffect(() => {
     let active = true;
@@ -90,6 +104,10 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
         setBackgroundCompute(data.background_compute);
         setPollIdleIntervalSeconds(data.poll_idle_interval_seconds);
         setStaleForS(data.stale_for_s);
+        // record this poll's own base + receipt time for the 1-second tick effect below to derive
+        // from between now and the next poll landing.
+        staleBaseRef.current = data.stale_for_s;
+        staleReceivedAtMsRef.current = Date.now();
         // adopt the config-derived poll cadences (seconds → ms); never a client-side literal.
         activeMs.current = Math.max(250, Math.round(data.poll_interval_seconds * 1000));
         idleMs.current = Math.max(activeMs.current, Math.round(data.poll_idle_interval_seconds * 1000));
@@ -103,6 +121,8 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
         setBackgroundCompute(null); // honest — readers render their own empty/idle state, never fabricated
         setPollIdleIntervalSeconds(null); // honest — a caller's own idle-refresh loop must not schedule on this
         setStaleForS(null); // honest — never render a stale/fabricated "as of Ns ago" for a failed poll
+        staleBaseRef.current = null; // honest — the tick effect must not resume ticking a stale base
+        staleReceivedAtMsRef.current = null;
         nextDelay = activeMs.current; // keep retrying at the active cadence until the backend answers
       } finally {
         if (active) {
@@ -119,6 +139,19 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
     };
   }, []);
 
+  // ops-hardening iter-78 (iter-77/d) — a separate, independent 1-second interval that re-derives the
+  // LIVE staleness value from the last poll's own base + elapsed client time (`deriveLiveStaleForS`),
+  // so the badge/banner annotation grows smoothly between polls instead of freezing at the last-polled
+  // number for up to the full poll-idle interval. Deliberately its own effect (not folded into the poll
+  // loop above): the poll cadence is config-derived and can be tens of seconds; this tick is a fixed,
+  // purely client-side re-render cadence that never itself fetches or schedules a poll.
+  useEffect(() => {
+    const interval = setInterval(() => {
+      setStaleForS(deriveLiveStaleForS(staleBaseRef.current, staleReceivedAtMsRef.current, Date.now()));
+    }, 1_000);
+    return () => clearInterval(interval);
+  }, []);
+
   const value = useMemo<ReadinessContextValue>(
     () => ({ state, warmup, preflight, backgroundCompute, loading, pollIdleIntervalSeconds, staleForS }),
     [state, warmup, preflight, backgroundCompute, loading, pollIdleIntervalSeconds, staleForS],
diff --git a/incredible_auto_dev/scripts/automation/lib/demo_runner.py b/incredible_auto_dev/scripts/automation/lib/demo_runner.py
index 16c61600..bbe63841 100644
--- a/incredible_auto_dev/scripts/automation/lib/demo_runner.py
+++ b/incredible_auto_dev/scripts/automation/lib/demo_runner.py
@@ -952,6 +952,10 @@ class _FakeLocator:
         return self
 
     def wait_for(self, state: str = "visible", timeout: float = 0):
+        # ops-hardening iter-78: record the timeout each caller actually threaded through, so a
+        # test can assert a step's own `timeout_ms` reaches Playwright's `.wait_for()` unclamped
+        # (see `_t_record_steps_honors_an_explicit_per_step_timeout_above_the_default_ceiling`).
+        self._spy.setdefault("wait_for_timeouts", []).append(timeout)
         if self._fail:
             raise TimeoutError(f"fake: {self._name} did not become visible")
 
@@ -1125,6 +1129,54 @@ def _t_settle_for_capture_before_after_frames_differ_when_state_changes() -> Non
     assert any("02" in note and "did not appear" in note for note in soft_notes), soft_notes
 
 
+def _t_record_steps_honors_an_explicit_per_step_timeout_above_the_default_ceiling() -> None:
+    """ops-hardening iter-78 (iter-77/e): a step MAY opt into a longer wait than the ordinary default
+    ceiling by setting its own `timeout_ms` — needed for content (e.g. the J-09 background-compute badge
+    chip) that only updates on the frontend's own NEXT readiness-badge poll, up to
+    `health_poll_idle_interval_seconds` (30s, config.yaml). Before this fix, `_record_steps` hard-capped
+    EVERY step's timeout at 20000ms regardless of what `timeout_ms` it named, so such a step could never
+    wait long enough for its own content to appear — the walkthrough captured whatever was on screen at
+    the 20s mark, not the real post-change state. Proven directly against the ACTUAL value threaded to
+    Playwright's own `.wait_for()` (via `_FakeLocator`'s new `wait_for_timeouts` spy), not just an
+    indirect pass/fail outcome."""
+    import tempfile
+    spy: dict = {}
+    page = _FakePage(spy)
+    steps = [
+        {"n": 1, "title": "Step back to a historical as-of date", "journey": "J-09",
+         "action": {"type": "click", "target": {"testid": "asof-step-prev"}},
+         "expect": {"target": {"testid": "background-compute-indicator"}},
+         "timeout_ms": 35000},
+    ]
+    with tempfile.TemporaryDirectory() as tmp:
+        _record_steps(page, steps, "http://localhost:3000", 8000, Path(tmp), None)
+    timeouts = spy.get("wait_for_timeouts", [])
+    assert 35000 in timeouts, (
+        f"expected the step's own timeout_ms=35000 to reach Playwright unclamped (not silently capped "
+        f"to 20000); recorded wait_for() timeouts: {timeouts}"
+    )
+
+
+def _t_record_steps_default_ceiling_unchanged_for_steps_without_explicit_timeout() -> None:
+    """Companion to the fix above: a step that does NOT set its own `timeout_ms` must still be bounded
+    by the ordinary (lower) default ceiling — this fix is additive (a step opts in explicitly), never a
+    blanket slow-down of every existing demo/replay step that has no reason to wait longer."""
+    import tempfile
+    spy: dict = {}
+    page = _FakePage(spy)
+    steps = [
+        {"n": 1, "title": "Open the home page", "action": {"type": "goto", "url": "/"},
+         "expect": {"text": "Ready"}},
+    ]
+    with tempfile.TemporaryDirectory() as tmp:
+        _record_steps(page, steps, "http://localhost:3000", 8000, Path(tmp), None)
+    timeouts = spy.get("wait_for_timeouts", [])
+    assert timeouts, "expected at least one wait_for() call to have been recorded"
+    assert all(t <= 8000 for t in timeouts), (
+        f"a step without its own timeout_ms must stay bounded by the script's default ceiling: {timeouts}"
+    )
+
+
 def _t_run_record_never_clicks_after_failed_precondition() -> None:
     # TC-4: given a fake page/script fixture where step N's `fill` raises and step N+1 is a
     # `click` on `role: button`, when the record loop executes that script, then step N+1's
@@ -1329,6 +1381,8 @@ _SELF_TEST_CHECKS = [
     _t_run_record_never_clicks_after_failed_precondition,
     _t_run_record_click_still_fires_without_a_prior_failure,
     _t_settle_for_capture_before_after_frames_differ_when_state_changes,
+    _t_record_steps_honors_an_explicit_per_step_timeout_above_the_default_ceiling,
+    _t_record_steps_default_ceiling_unchanged_for_steps_without_explicit_timeout,
     _t_derive_happy,
     _t_derive_rejects_untagged_journey,
     _t_derive_rejects_no_expect,
@@ -1550,6 +1604,21 @@ _LOADING_SELECTOR = (
     '.loading, .spinner, .skeleton, [class*="skeleton"], [class*="Skeleton"]'
 )
 
+# ops-hardening iter-78 (iter-77/e — the J-09 "background compute in flight" walkthrough frame
+# captured an idle Ready-only state): most demo steps settle within a couple of seconds, so the
+# ORDINARY per-step ceiling stays the original 20000ms (`_default_timeout`'s own cap, applied to the
+# SCRIPT-WIDE `default_timeout_ms` fallback and to any step that omits its own `timeout_ms` — both
+# UNCHANGED below). But a step whose expected content only updates on the frontend's own NEXT
+# readiness-badge poll cannot be observed sooner than that poll lands: `health_poll_idle_interval_
+# seconds` (config.yaml) is 30s once the badge is in its steady "Ready" idle cadence, so a click
+# landing just after a poll waits up to a FULL cycle before the badge/panel reflects it — well past
+# the previous hard 20000ms ceiling, which capped EVERY step regardless of what `timeout_ms` it asked
+# for. A step now opts into this higher ceiling explicitly, by setting its own `timeout_ms` above the
+# ordinary default; a step that omits `timeout_ms` is completely unaffected (still bounded by
+# `_default_timeout`'s 20000ms ceiling), so this is additive, never a blanket slow-down of every
+# existing demo/replay script.
+_STEP_TIMEOUT_HARD_CEILING_MS = 45000
+
 
 def _settle_for_capture(page, budget_ms: int, exp: "dict | None" = None) -> None:
     """Best-effort wait for the page to finish loading — and, when `exp` is given, for the
@@ -1782,7 +1851,7 @@ def _record_steps(page, steps: list[dict], base_url: str, default_tmo: int,
     for step in steps:
         n = int(step.get("n", 0))
         section = step.get("section", "highlights")
-        tmo = max(1000, min(int(step.get("timeout_ms", default_tmo)), 20000))
+        tmo = max(1000, min(int(step.get("timeout_ms", default_tmo)), _STEP_TIMEOUT_HARD_CEILING_MS))
         action = step["action"]
         is_mutating_click = (action.get("type") == "click"
                              and (action.get("target") or {}).get("role") == "button")
@@ -1909,7 +1978,7 @@ def run_live(script: dict, opts, base_url: str) -> int:
             print(f"\n── Step {i:02d}/{total:02d} ─ {title}{tag}")
             if step.get("narration"):
                 print(f"   {step['narration']}")
-            tmo = max(1000, min(int(step.get("timeout_ms", default_tmo)), 20000))
+            tmo = max(1000, min(int(step.get("timeout_ms", default_tmo)), _STEP_TIMEOUT_HARD_CEILING_MS))
             action = step["action"]
             loc = None
             target = action.get("target")
@@ -2050,7 +2119,7 @@ def run_verify(opts, base_url: str) -> int:
                 exp = None  # last step's expect, if any -- passed to the final evidence capture below
                 for step in steps:
                     n = int(step.get("n", 0))
-                    tmo = max(1000, min(int(step.get("timeout_ms", default_tmo)), 20000))
+                    tmo = max(1000, min(int(step.get("timeout_ms", default_tmo)), _STEP_TIMEOUT_HARD_CEILING_MS))
                     try:
                         _do_action(page, step["action"], base_url, tmo)
                     except Exception as exc:  # noqa: BLE001
diff --git a/incredible_auto_dev/scripts/start-frontend.sh b/incredible_auto_dev/scripts/start-frontend.sh
index 8499170c..74860b77 100755
--- a/incredible_auto_dev/scripts/start-frontend.sh
+++ b/incredible_auto_dev/scripts/start-frontend.sh
@@ -57,6 +57,87 @@ if [[ -f "$HOST_GUARD_ENV" ]]; then
 fi
 # ==== end HOST-GUARD =================================================================================
 
+# ==== TEST-RESIDUE PURGE (ops-hardening iter-78, closes iter-77/c) ==================================
+# A hard-killed run of apps/backend/tests/test_start_frontend_script.py (pytest SIGKILLed mid-build --
+# no `finally` block, no teardown at all) can leave `__tc3_intentionally_broken.ts` / `.next-test-*`
+# scratch dirs behind in the LIVE apps/frontend tree. That test module already self-heals its OWN next
+# run (its autouse `_pristine_frontend_tree` fixture purges on setup as well as teardown), but this real
+# launcher had no such defense — iter-77 hit exactly this: a stray broken `.ts` file made THIS script's
+# real `next build` fail (Next's prod build type-checks the whole project), taking the whole frontend
+# down, "fixed inside the round; NOT defended against recurrence." Purge unconditionally, before the
+# staleness check even runs, independent of whether/when that test module is next invoked.
+#
+# The two names below are kept in lockstep BY HAND with
+# apps/backend/tests/test_start_frontend_script.py's `_BROKEN_SOURCE_REL` / `_SCRATCH_DIST_GLOB` (a bash
+# script cannot import a Python constant) — deliberately the SAME two names that module already reserves
+# and cleans on its own setup/teardown, never a new name, so the two stay in lockstep. A purge failure
+# (e.g. a permission error on the stray file) must never be silently swallowed into "serve whatever
+# happens to build" — fail loud and non-zero instead, matching the `next build FAILED` refusal below.
+#
+# `_RESIDUE_OWN_DIST_DIR` excludes THIS invocation's own build target from the scratch-glob purge below.
+# `NEXT_DIST_DIR` (read again here — the real `DIST_DIR="${NEXT_DIST_DIR:-.next}"` assignment is further
+# down, after this block) also matches the `.next-test-*` convention whenever a caller points a launch at
+# a scratch dist dir (every real-process test in test_start_frontend_script.py does exactly this, often
+# invoking the launcher SEVERAL TIMES in a row against the SAME scratch dir on purpose — e.g. to prove a
+# second invocation skips the rebuild, or correctly detects an out-of-band/wrong-backend build already
+# there). That directory is this invocation's own current, legitimate target, never someone else's
+# abandoned leftover — purging it unconditionally wiped the very state (BUILD_ID, the launch-build/serving
+# markers) those scenarios depend on, forcing a needless rebuild every single launch and defeating the
+# out-of-band/backend-mismatch detection they exist to prove (caught by a real, non-mocked pytest run of
+# the existing module, not merely reasoned about).
+#
+# ops-hardening iter-78 AUDIT FIX (finding B1) — excluding only THIS invocation's own dist dir is not
+# enough: two launcher invocations pointed at DIFFERENT scratch dirs (two overlapping runs of
+# test_start_frontend_script.py on one host — exactly the contention this iteration's own dev handoff
+# records hitting) would each classify the OTHER's dir as abandoned leftover and `rm -rf` it out from
+# under a LIVE `next start`, tearing a running server's assets mid-flight. That is the very harm the
+# iter-77 `.trendora-serving` marker exists to prevent (`_dist_dir_has_live_server` below), and the
+# purge — which runs before that function is even defined, and outside the build lock — bypassed it.
+# A directory some live process is currently SERVING is by definition not "leftover", so consult the
+# same marker, with the same PID-reuse cmdline guard, before deleting anything.
+_residue_dir_has_live_server() {
+  local marker="$1/.trendora-serving" pid
+  [[ -f "$marker" ]] || return 1
+  pid="$(grep -m1 '^pid=' "$marker" 2>/dev/null | cut -d= -f2)"
+  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
+  [[ "$pid" != "$$" ]] || return 1
+  kill -0 "$pid" 2>/dev/null || return 1
+  tr '\0' ' ' <"/proc/$pid/cmdline" 2>/dev/null | grep -qE '(^|[ /])(next|npx|node|taskset)( |$)'
+}
+_RESIDUE_BROKEN_SOURCE="__tc3_intentionally_broken.ts"
+_RESIDUE_SCRATCH_GLOB=".next-test-*"
+_RESIDUE_OWN_DIST_DIR="${NEXT_DIST_DIR:-.next}"
+if [[ -e "$_RESIDUE_BROKEN_SOURCE" ]]; then
+  if rm -f "$_RESIDUE_BROKEN_SOURCE"; then
+    echo "[start-frontend.sh] purged leftover test-residue file: $_RESIDUE_BROKEN_SOURCE" >&2
+  else
+    echo "[start-frontend.sh] FATAL: found leftover test-residue file '$_RESIDUE_BROKEN_SOURCE' but" \
+         "failed to remove it (permission error?) — refusing to build/serve a possibly-broken tree." >&2
+    exit 1
+  fi
+fi
+shopt -s nullglob
+_residue_scratch_dirs=($_RESIDUE_SCRATCH_GLOB)
+shopt -u nullglob
+for _residue_dir in "${_residue_scratch_dirs[@]}"; do
+  if [[ "$_residue_dir" == "$_RESIDUE_OWN_DIST_DIR" ]]; then
+    continue  # this invocation's own build target, not another process's leftover -- never purge it
+  fi
+  if _residue_dir_has_live_server "$_residue_dir"; then
+    echo "[start-frontend.sh] leaving scratch dist dir '$_residue_dir' in place — another live server is" \
+         "serving it right now (not abandoned residue)." >&2
+    continue
+  fi
+  if rm -rf "$_residue_dir"; then
+    echo "[start-frontend.sh] purged leftover test-residue scratch dir: $_residue_dir" >&2
+  else
+    echo "[start-frontend.sh] FATAL: found leftover test-residue scratch dir '$_residue_dir' but failed" \
+         "to remove it (permission error?) — refusing to build/serve a possibly-broken tree." >&2
+    exit 1
+  fi
+done
+# ==== end TEST-RESIDUE PURGE =========================================================================
+
 # ==== build-if-stale, then serve PRODUCTION mode (ops-hardening iter-33) ============================
 # Previously this script execed `npx next dev` unconditionally, despite every other doc calling it
 # "prod mode" (measure-perf.sh's own header, goal.md's J-06 step-1 text) — two consecutive evaluators
diff --git a/apps/frontend/lib/staleness-tick.test.ts b/apps/frontend/lib/staleness-tick.test.ts
new file mode 100644
index 00000000..c0550961
--- /dev/null
+++ b/apps/frontend/lib/staleness-tick.test.ts
@@ -0,0 +1,85 @@
+/**
+ * Unit tests for the J-04/J-07 readiness-badge/preflight-banner LIVE staleness tick derivation
+ * (lib/staleness-tick.ts). No test framework is installed in this frontend; these run under Node's
+ * native TS type-stripping:
+ *   node lib/staleness-tick.test.ts
+ * (mirrors `lib/staleness-annotation.test.ts`'s existing convention -- see that file's own header note
+ * on the documented dev-box `node lib/*.test.ts` limitation.)
+ *
+ * ops-hardening iter-78 (iter-77/d): `stale_for_s` previously only updated on poll landing, so the
+ * "as of Ns ago" annotation could read stale for up to the full poll-idle interval before the next poll
+ * refreshed it. `deriveLiveStaleForS` re-derives the live value between polls; these tests cover TC-3
+ * (a positive base ticks up smoothly) and TC-4 (null/0/negative/non-finite bases never start ticking,
+ * so `formatStaleAnnotation`'s own null-rendering guards keep applying to the derived value unchanged).
+ */
+import assert from "node:assert";
+
+import { deriveLiveStaleForS } from "./staleness-tick.ts";
+import { formatStaleAnnotation } from "./staleness-annotation.ts";
+
+let passed = 0;
+function check(name: string, fn: () => void) {
+  fn();
+  passed += 1;
+  console.log(`  ok - ${name}`);
+}
+
+check("a positive base ticks up by the elapsed client seconds since receipt", () => {
+  const receivedAt = 1_000_000;
+  assert.strictEqual(deriveLiveStaleForS(5, receivedAt, receivedAt), 5);
+  assert.strictEqual(deriveLiveStaleForS(5, receivedAt, receivedAt + 10_000), 15);
+  assert.strictEqual(deriveLiveStaleForS(5, receivedAt, receivedAt + 500), 5.5);
+});
+
+check(
+  "TC-3: 'as of 5s ago' from a landed poll, 10 more seconds elapse with no new poll -> ~15s, not frozen",
+  () => {
+    const receivedAt = 2_000_000;
+    const live = deriveLiveStaleForS(5, receivedAt, receivedAt + 10_000);
+    assert.strictEqual(formatStaleAnnotation(live), "as of 15s ago");
+  },
+);
+
+check("a null base (no poll landed yet / failed poll) never starts ticking, whatever the elapsed time", () => {
+  assert.strictEqual(deriveLiveStaleForS(null, 1_000_000, 2_000_000), null);
+  assert.strictEqual(deriveLiveStaleForS(null, null, 2_000_000), null);
+});
+
+check("TC-4: stale_for_s === 0 (fresh/synchronous compute) never starts ticking upward", () => {
+  const receivedAt = 3_000_000;
+  const live = deriveLiveStaleForS(0, receivedAt, receivedAt + 60_000);
+  assert.strictEqual(live, 0);
+  assert.strictEqual(formatStaleAnnotation(live), null);
+});
+
+check("TC-4: staleForS === null (failed poll) renders nothing even as the tick timer fires", () => {
+  const live = deriveLiveStaleForS(null, null, 5_000_000);
+  assert.strictEqual(formatStaleAnnotation(live), null);
+});
+
+check("a negative base (defensive, unexpected payload shape) is never ticked into a positive number", () => {
+  const receivedAt = 4_000_000;
+  const live = deriveLiveStaleForS(-3, receivedAt, receivedAt + 60_000);
+  assert.strictEqual(live, -3);
+  assert.strictEqual(formatStaleAnnotation(live), null);
+});
+
+check("a non-finite base (NaN/Infinity) is passed through unchanged, never fabricated into a number", () => {
+  assert.strictEqual(deriveLiveStaleForS(Number.NaN, 1_000_000, 2_000_000), Number.NaN);
+  assert.strictEqual(
+    deriveLiveStaleForS(Number.POSITIVE_INFINITY, 1_000_000, 2_000_000),
+    Number.POSITIVE_INFINITY,
+  );
+});
+
+check("a positive base with a missing/invalid receipt anchor falls back to the base, unticked", () => {
+  assert.strictEqual(deriveLiveStaleForS(5, null, 2_000_000), 5);
+  assert.strictEqual(deriveLiveStaleForS(5, Number.NaN, 2_000_000), 5);
+});
+
+check("elapsed time never goes negative even if `now` somehow precedes the receipt timestamp", () => {
+  const receivedAt = 5_000_000;
+  assert.strictEqual(deriveLiveStaleForS(5, receivedAt, receivedAt - 2_000), 5);
+});
+
+console.log(`${passed} passed`);
diff --git a/apps/frontend/lib/staleness-tick.ts b/apps/frontend/lib/staleness-tick.ts
new file mode 100644
index 00000000..2a36810e
--- /dev/null
+++ b/apps/frontend/lib/staleness-tick.ts
@@ -0,0 +1,37 @@
+/**
+ * Pure numeric derivation for the readiness badge / preflight banner's LIVE staleness value
+ * (ops-hardening iter-78, iter-77/d) -- the "as of Ns ago" annotation (`lib/staleness-annotation.ts`'s
+ * `formatStaleAnnotation`) previously only updated on poll landing, so it could read "as of <1s ago" for
+ * up to the full poll-idle interval (`health_poll_idle_interval_seconds`, 30s in config.yaml) before the
+ * next poll refreshed it -- an annotation that looks frozen even though real time is passing.
+ *
+ * This function does NO formatting -- it only re-derives the numeric seconds-stale value that
+ * `formatStaleAnnotation` is fed, from the last poll's own `stale_for_s` base plus how much client
+ * wall-clock time has elapsed since that poll was received. `ReadinessProvider` calls it once a second
+ * from a local tick interval; `formatStaleAnnotation` remains the single formatting authority downstream
+ * -- never a second formatter.
+ *
+ * Ticking is intentionally a no-op (returns the base UNCHANGED) whenever the base itself is one of
+ * `formatStaleAnnotation`'s own null-rendering cases -- `null` (no poll has landed yet, or the last poll
+ * failed), `0` (a fresh/synchronous compute, a SENTINEL for "not stale" rather than a literal age to
+ * count up from), or a non-finite/negative value (defensive, unexpected payload shape). Ticking those
+ * upward would let a value that should never render start rendering once enough time passed -- a
+ * fabricated annotation from an input that was never a real age. Only a genuinely positive, finite base
+ * ticks.
+ */
+export function deriveLiveStaleForS(
+  baseStaleForS: number | null,
+  receivedAtMs: number | null,
+  nowMs: number,
+): number | null {
+  if (baseStaleForS === null || !Number.isFinite(baseStaleForS) || baseStaleForS <= 0) {
+    return baseStaleForS;
+  }
+  if (receivedAtMs === null || !Number.isFinite(receivedAtMs) || !Number.isFinite(nowMs)) {
+    // No valid receipt anchor to tick from -- fall back to the last-known base, unticked, rather
+    // than guess or fabricate an elapsed duration.
+    return baseStaleForS;
+  }
+  const elapsedS = Math.max(0, (nowMs - receivedAtMs) / 1000);
+  return baseStaleForS + elapsedS;
+}
```
