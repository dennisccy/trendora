# Iteration diff (bounded)

Files changed: 13. Shown in full: 12.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_start_frontend_script.py` (10 lines not shown)

```diff
diff --git a/= b/=
deleted file mode 100644
index e69de29b..00000000
diff --git a/apps/backend/tests/test_start_frontend_script.py b/apps/backend/tests/test_start_frontend_script.py
index 7b39960d..65173dc9 100644
--- a/apps/backend/tests/test_start_frontend_script.py
+++ b/apps/backend/tests/test_start_frontend_script.py
@@ -90,6 +90,19 @@ _offset = int(__import__("hashlib").sha1(str(REPO_ROOT).encode()).hexdigest()[:4
 _TC1_PORT = 21000 + _offset
 _TC2_PORT = 21100 + _offset
 _TC3_PORT = 21200 + _offset
+# ops-hardening iter-77: distinct port ranges for the goal-spec's OWN "TC-1"/"TC-2" (the intermittent
+# asset-less-frontend defect, iter-72/c) -- not to be confused with this module's pre-existing
+# iter-33-era TC-1 ("test_missing_build_triggers_build_then_next_start")/TC-2
+# ("test_current_build_skips_rebuild") above, which are about a DIFFERENT thing (the build/skip-rebuild
+# branch taken by a single invocation). 21400/21500 are clear of every range already claimed above.
+_TC1_77_PORT = 21400 + _offset
+_TC2_77_PORT = 21500 + _offset
+# ops-hardening iter-77 AUDIT: the out-of-band-build regression test's own range (21600), clear of
+# every range claimed above.
+_TC3_77_PORT = 21600 + _offset
+# ops-hardening iter-77 AUDIT FIX ROUND 2: the build-guard (21700) and backend-retarget (21800) tests.
+_TC4_77_PORT = 21700 + _offset
+_TC5_77_PORT = 21800 + _offset
 
 # A cold scratch-dir `next build` (a distDir name Next has never seen -> no webpack cache to reuse) on
 # this host-guard-CPU-masked host measured ~1 minute with the box idle, but blew past 300 s while the live
@@ -240,6 +253,26 @@ def _wait_for_port_answering(
     )
 
 
+_ASSET_HREF_RE = re.compile(r'(?:href|src)="(/_next/static/[^"]+)"')
+
+
+def _assert_page_fully_styled(port: int, timeout: float = 30.0) -> None:
+    """Fetch `/` and at least one of its OWN referenced `/_next/static/...` build assets, asserting BOTH
+    return HTTP 200 with a non-empty body. The concrete 'asset-less' failure this closes (iter-72/c) would
+    serve the HTML shell fine (200) while a stylesheet/script chunk 404s or comes back truncated -- a torn
+    build served mid-write by a racing `next build`. Mirrors this iteration's own TC-1 wording ('CSS/asset
+    requests return 200; no bare "Checking backend..." shell')."""
+    resp = httpx.get(f"http://127.0.0.1:{port}/", timeout=timeout)
+    assert resp.status_code == 200, f"GET / -> HTTP {resp.status_code}"
+    html = resp.text
+    assets = _ASSET_HREF_RE.findall(html)
+    assert assets, f"expected >=1 /_next/static/... asset reference in the served HTML; got:\n{html[:2000]}"
+    for asset_path in assets[:3]:  # a handful is enough to catch a torn/partial build
+        aresp = httpx.get(f"http://127.0.0.1:{port}{asset_path}", timeout=timeout)
+        assert aresp.status_code == 200, f"GET {asset_path} -> HTTP {aresp.status_code} (asset-less page)"
+        assert len(aresp.content) > 0, f"GET {asset_path} returned an empty body (asset-less page)"
+
+
 def _parent_pid(pid: int) -> "int | None":
     out = subprocess.run(["ps", "-o", "ppid=", "-p", str(pid)], capture_output=True, text=True, timeout=5)
     txt = out.stdout.strip()
@@ -468,7 +501,17 @@ def test_current_build_skips_rebuild(launcher):
 
     mtime_before = build_id.stat().st_mtime_ns
 
-    second = launcher(dist_rel, _TC2_PORT + 1, _TC2_PORT + 1001, "tc2-second.log")
+    # The second invocation runs on a different FRONTEND port (the first server is stopped, but a fresh
+    # port keeps the two launches trivially independent) and the SAME BACKEND port. The backend port has
+    # to match for this scenario to be the one TC-2 describes -- "an existing, current build ... sources
+    # unchanged": Next inlines NEXT_PUBLIC_API_URL into the bundle at BUILD time, so pointing the second
+    # launch at a DIFFERENT backend makes the build on disk genuinely out of date for that launch, and
+    # `start-frontend.sh` now (ops-hardening iter-77 audit fix round 2) rebuilds instead of serving an app
+    # that cannot reach its configured backend -- covered by
+    # `test_launcher_rebuilds_a_bundle_built_for_a_different_backend`. Before that check existed, this test
+    # passed while silently exercising exactly the "served build points at the wrong backend" state that
+    # broke iter-77.
+    second = launcher(dist_rel, _TC2_PORT + 1, _TC2_PORT + 1000, "tc2-second.log")
     _wait_for_port_answering(  # no build needed on this path -> a short ceiling is the point of TC-2
         _TC2_PORT + 1, timeout=_START_TIMEOUT_S, proc=second.proc, log_path=second.log_path
     )
@@ -707,3 +750,339 @@ def test_host_guard_marker_files_lists_start_frontend():
     # the marker check itself is a plain substring grep — confirm the block is genuinely present, not
     # merely declared in the list above.
     assert "HOST-GUARD" in SCRIPT.read_text()
+
+
+# ==================================================================================================
+# ops-hardening iter-77 -- the goal-spec's OWN TC-1/TC-2: the intermittent asset-less-frontend defect
+# (iter-72/c, un-root-caused and un-fixed for 4 rounds). Root-caused via direct code reading (this
+# script had no lock against a second concurrent invocation racing `next build` against the SAME live
+# dist dir -- see the "BUILD LOCK" block start-frontend.sh now carries) and closed with a `flock`
+# serializing the staleness-check -> build decision per dist-dir. These two tests are the goal-spec's
+# own scenarios -- NOT a duplicate of this module's pre-existing iter-33 TC-1/TC-2 above, which assert a
+# DIFFERENT thing (which branch — build vs. skip-rebuild — a single invocation takes).
+# ==================================================================================================
+
+
+def test_five_consecutive_fresh_launches_serve_fully_styled_page(launcher):
+    """iter-77 TC-1 -- 5 consecutive, NON-concurrent `start-frontend.sh` launches against the same dist
+    dir must each serve a fully-styled page (the HTML plus its own referenced build assets, all HTTP 200
+    with real content), zero asset-less occurrences. Builds the scratch dist dir once for real (like
+    every other real-build test in this module — a `next build` per launch would be prohibitively slow)
+    then stops/relaunches the SAME launcher four more times against that now-current build, proving the
+    iter-77 build-lock addition does not regress the ordinary sequential-restart path (the ONLY path
+    most real launches ever take)."""
+    if not (FRONTEND_DIR / "node_modules").exists():
+        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")
+    dist_rel = _scratch_dist_name("tc1-77")
+    port = _TC1_77_PORT
+    for i in range(5):
+        launched = launcher(dist_rel, port, port + 1000, f"tc1-77-{i}.log")
+        timeout = _BUILD_TIMEOUT_S if i == 0 else _START_TIMEOUT_S
+        _wait_for_port_answering(port, timeout=timeout, proc=launched.proc, log_path=launched.log_path)
+        _assert_page_fully_styled(port)
+        launched.stop()
+
+
+def test_concurrent_invocations_never_serve_partial_build(launcher):
+    """iter-77 TC-2 -- two invocations of `start-frontend.sh` launched CONCURRENTLY against the SAME
+    brand-new (never-built) `NEXT_DIST_DIR`, on two different ports. Before the iter-77 build-lock fix,
+    both would see the build as stale and run `next build` concurrently against the SAME output
+    directory with no coordination -- the real race this iteration's spec requires a test to directly
+    exercise (per its own note: 'quiet for N rounds' is not proof of a fix). This asserts (1) the lock's
+    OWN log line proves the second invocation genuinely BLOCKED on the first's build rather than racing
+    it — the concrete mechanism, not just a passing outcome that could happen to get lucky on timing —
+    and (2) once both invocations are up and serving, EACH renders a fully-styled page — never a
+    partial/mid-build payload — proving the shared dist dir was never served in a torn state."""
+    if not (FRONTEND_DIR / "node_modules").exists():
+        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")
+    dist_rel = _scratch_dist_name("tc2-77")
+    assert not (FRONTEND_DIR / dist_rel).exists(), "the scratch dist dir must not exist before launching"
+    port_a, port_b = _TC2_77_PORT, _TC2_77_PORT + 1
+
+    launched_a = launcher(dist_rel, port_a, port_a + 1000, "tc2-77-a.log")
+    launched_b = launcher(dist_rel, port_b, port_b + 1000, "tc2-77-b.log")
+
+    _wait_for_port_answering(
+        port_a, timeout=_BUILD_TIMEOUT_S, proc=launched_a.proc, log_path=launched_a.log_path
+    )
+    _wait_for_port_answering(
+        port_b, timeout=_BUILD_TIMEOUT_S, proc=launched_b.proc, log_path=launched_b.log_path
+    )
+
+    log_a, log_b = launched_a.log_text(), launched_b.log_text()
+    assert ("waiting for its build lock" in log_a) or ("waiting for its build lock" in log_b), (
+        "expected ONE of the two concurrent invocations to observe the OTHER already holding the build "
+        f"lock (proves the race was genuinely exercised, not just luck) -- got:\nA:\n{log_a[-2000:]}"
+        f"\nB:\n{log_b[-2000:]}"
+    )
+    assert "acquired build lock" in log_a and "acquired build lock" in log_b, (
+        f"both invocations must eventually acquire the lock and proceed (never deadlock) -- got:\n"
+        f"A:\n{log_a[-2000:]}\nB:\n{log_b[-2000:]}"
+    )
+
+    _assert_page_fully_styled(port_a)
+    _assert_page_fully_styled(port_b)
+
+
+def test_out_of_band_build_is_treated_as_stale_and_rebuilt(launcher):
+    """ops-hardening iter-77 AUDIT -- a build the LAUNCHER did not produce must never be served as
+    "current".
+
+    The concrete defect this closes (reproduced live during the iter-77 audit, not hypothesised): a bare
+    `npx next build` run inside `apps/frontend` as a verification step -- the exact command both this
+    iteration's dev handoff and its QA report record themselves running -- rewrites the LIVE `.next` with
+    a bundle built WITHOUT the `NEXT_PUBLIC_API_URL`/`NEXT_PUBLIC_API_PORT` exports `start-frontend.sh`
+    sets, so Next bakes its own `http://localhost:8000` fallback into the client bundle. The staleness
+    check compares SOURCE mtimes against BUILD_ID and therefore sees nothing wrong: the launcher logged
+    "build is current ... skipping rebuild" and served a frontend that rendered the global "Backend
+    unavailable" state on every page while the backend was healthy on its real port.
+
+    Simulating (rather than really running) the out-of-band build keeps this test to two real builds: a
+    bare `next build` always mints a FRESH `BUILD_ID` into the dist dir, which is exactly what step 2
+    below reproduces -- the launcher must then rebuild rather than trust the foreign output."""
+    if not (FRONTEND_DIR / "node_modules").exists():
+        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")
+    dist_rel = _scratch_dist_name("tc3-77")
+    port, backend_port = _TC3_77_PORT, _TC3_77_PORT + 1000
+    marker = FRONTEND_DIR / dist_rel / ".trendora-launch-build"
+    build_id = FRONTEND_DIR / dist_rel / "BUILD_ID"
+
+    # 1. A normal launcher build: the marker is written and names the backend this launch configured.
+    first = launcher(dist_rel, port, backend_port, "tc3-77-first.log")
+    _wait_for_port_answering(port, timeout=_BUILD_TIMEOUT_S, proc=first.proc, log_path=first.log_path)
+    assert marker.exists(), f"expected the launcher to record its own build marker at {marker}"
+    marker_text = marker.read_text()
+    assert f"build_id={build_id.read_text().strip()}" in marker_text, marker_text
+    assert f"api_url=http://localhost:{backend_port}" in marker_text, marker_text
+    first.stop()
+
+    # 2. Simulate an out-of-band `npx next build`: same dist dir, a fresh BUILD_ID, no launcher
+    #    involvement (the marker is left in place on purpose -- the id comparison, not merely the file's
+    #    presence, must be what catches this).
+    build_id.write_text("out-of-band-build-id\n")
+
+    # 3. The next launch must NOT trust it.
+    second = launcher(dist_rel, port, backend_port, "tc3-77-second.log")
+    _wait_for_port_answering(port, timeout=_BUILD_TIMEOUT_S, proc=second.proc, log_path=second.log_path)
+    log = second.log_text()
+    assert "was not built by this launcher" in log, (
+        f"expected the foreign build to be detected and rebuilt, got:\n{log[-2000:]}"
+    )
+    assert "running 'next build'" in log, (
+        f"expected the foreign build to trigger an actual rebuild, got:\n{log[-2000:]}"
+    )
+    _assert_page_fully_styled(port)
+    assert f"build_id={build_id.read_text().strip()}" in marker.read_text(), (
+        "the rebuild must refresh the marker so the NEXT launch skips correctly"
+    )
+
+
+# ==================================================================================================
+# ops-hardening iter-77 AUDIT FIX ROUND 2 -- findings B2 ("an out-of-band `next build` can still tear /
+# poison the LIVE dist dir; code cannot stop it") and B3 ("the shipped root cause was never
+# instrumented").
+#
+# The audit's first fix taught the LAUNCHER to distrust a foreign build after the fact. These tests
+# cover the two additions that stop it happening at all, and the one that detects it at launch:
+#   * `apps/frontend/next.config.mjs` -- the ONE file every `next build` must load, whoever invokes it:
+#     it now REFUSES a production build that would (a) write into the live `.next` without
+#     NEXT_PUBLIC_API_URL (the bare `npx next build` that poisoned this round -> a bundle pointing at
+#     http://localhost:8000, which nothing binds) or (b) write into ANY dist dir a live server is
+#     currently serving (the half B2 called un-fixable in code).
+#   * `scripts/start-frontend.sh` -- writes the `.trendora-serving` claim the guard reads, and now
+#     verifies at launch that the build on disk actually references the backend this launch configured.
+# ==================================================================================================
+
+_GUARD_PROBE_JS = (
+    "import('./next.config.mjs')"
+    ".then((m) => m.default('phase-production-build'))"
+    ".then(() => console.log('ALLOWED'),"
+    " (e) => { console.log('REFUSED: ' + e.message); process.exitCode = 3; })"
+)
+
+
+def _guard_verdict(dist_rel: str | None, api_url: str | None) -> tuple[bool, str]:
+    """Ask `next.config.mjs` DIRECTLY whether it would allow a production build into `dist_rel` (None =
+    the live `.next`) -- the same call Next itself makes (`normalizeConfig(phase, config)` invokes the
+    exported function with the phase). Seconds, not a real build, so the guard's PRECISION (it must
+    allow every legitimate build) can be asserted broadly without paying for a webpack compile each
+    time. Returns (allowed, output)."""
+    env = dict(os.environ)
+    env.pop("NEXT_DIST_DIR", None)
+    env.pop("NEXT_PUBLIC_API_URL", None)
+    env.pop("TRENDORA_LAUNCH_BUILD", None)
+    if dist_rel is not None:
+        env["NEXT_DIST_DIR"] = dist_rel
+    if api_url is not None:
+        env["NEXT_PUBLIC_API_URL"] = api_url
+    proc = subprocess.run(
+        ["node", "-e", _GUARD_PROBE_JS],
+        cwd=str(FRONTEND_DIR),
+        env=env,
+        capture_output=True,
+        text=True,
+        timeout=60,
+    )
+    out = (proc.stdout + proc.stderr).strip()
+    return ("ALLOWED" in proc.stdout), out
+
+
+def test_build_guard_refuses_the_unconfigured_live_dist_build_and_leaves_it_untouched():
+    """The EXACT command that broke iter-77 -- a bare `npx next build` inside `apps/frontend` -- must now
+    fail instead of rewriting the live `.next`.
+
+    Runs the real command (not a simulation): the guard lives in `next.config.mjs`, which Next loads
+    before it touches the dist dir, so the refusal costs seconds and the live build's BUILD_ID must come
+    back byte-identical. Both guard rules protect the same invariant here (the live dir may also be
+    claimed by a running server), so the assertion accepts either refusal reason but requires the live
+    build to be untouched -- that is the property that failed this round.
+
+    If this test ever FAILS because the guard stopped working, the timeout below caps the damage at a
+    partial build the launcher's provenance marker (`test_out_of_band_build_is_treated_as_stale_and_
+    rebuilt`) will rebuild on the next launch."""
+    if not (FRONTEND_DIR / "node_modules").exists():
+        pytest.skip("apps/frontend/node_modules not installed -- cannot run `next build`")
+    live_build_id = FRONTEND_DIR / ".next" / "BUILD_ID"
+    before = live_build_id.read_text() if live_build_id.exists() else None
+
+    env = dict(os.environ)
+    for var in ("NEXT_PUBLIC_API_URL", "NEXT_PUBLIC_API_PORT", "NEXT_DIST_DIR", "TRENDORA_LAUNCH_BUILD"):
+        env.pop(var, None)
+    proc = subprocess.run(
+        ["npx", "next", "build"],
+        cwd=str(FRONTEND_DIR),
+        env=env,
+        capture_output=True,
+        text=True,
+        timeout=180,
+    )
+    out = proc.stdout + proc.stderr
+    assert proc.returncode != 0, f"the bare `npx next build` must be REFUSED, not run:\n{out[-2000:]}"
+    assert "TRENDORA BUILD GUARD" in out, f"expected the guard's own refusal, got:\n{out[-2000:]}"
+    assert ("without" in out and "NEXT_PUBLIC_API_URL" in out) or "being SERVED right now" in out, (
+        f"expected one of the two guard reasons, got:\n{out[-2000:]}"
+    )
+    # The message must be actionable -- the whole point is that the next caller knows what to do.
+    assert "NEXT_DIST_DIR=.next-verify" in out, f"expected an actionable remedy, got:\n{out[-2000:]}"
+
+    after = live_build_id.read_text() if live_build_id.exists() else None
+    assert after == before, (
+        "the refused build must not have touched the live `.next` -- "
+        f"BUILD_ID went {before!r} -> {after!r}"
+    )
+
+
+def test_build_guard_allows_every_legitimate_build():
+    """Precision, asserted directly against `next.config.mjs` (seconds, no webpack): the guard must NOT
+    become a blanket block. A verification build into a throwaway dist dir -- the remedy its own message
+    recommends -- is allowed with or without NEXT_PUBLIC_API_URL, and a configured build into the live
+    dir is allowed as long as nothing is serving it."""
+    allowed, out = _guard_verdict(".next-verify", None)
+    assert allowed, f"a verification build into a throwaway dist dir must be allowed, got:\n{out}"
+    allowed, out = _guard_verdict(".next-verify", "http://localhost:8255")
+    assert allowed, f"a configured throwaway build must be allowed, got:\n{out}"
+    # A never-served scratch dir with the backend configured: the shape `start-frontend.sh` itself uses.
+    scratch = _scratch_dist_name("guard-precision")
+    allowed, out = _guard_verdict(scratch, "http://localhost:8255")
+    assert allowed, f"a configured build into an unserved scratch dist dir must be allowed, got:\n{out}"
+
+
+def test_build_guard_refuses_building_into_a_dist_dir_a_live_server_is_serving(launcher):
+    """finding B2's remaining half, closed in code: while `start-frontend.sh` is SERVING a dist dir, no
+    other `next build` may rewrite it -- however it is invoked, and even when correctly configured.
+
+    This is the mechanism that produced iter-77's five byte-identical full-page-crash demo frames: a
+    verification build rewrote the assets out from under the running server. One real build pays for all
+    three assertions:
+      1. the launcher records its serving claim (`.trendora-serving`) with the pid that is actually
+         serving -- the guard's input;
+      2. a real, fully-configured `npx next build` into that same dist dir is REFUSED, the dist dir's
+         BUILD_ID is unchanged, and the live server is still serving a fully-styled page afterwards;
+      3. once that server stops, the SAME target is allowed again -- the claim expires with the process,
+         so a hard-killed server can never wedge future builds."""
+    if not (FRONTEND_DIR / "node_modules").exists():
+        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")
+    dist_rel = _scratch_dist_name("tc4-77")
+    port, backend_port = _TC4_77_PORT, _TC4_77_PORT + 1000
+    api_url = f"http://localhost:{backend_port}"
+
+    launched = launcher(dist_rel, port, backend_port, "tc4-77.log")
+    _wait_for_port_answering(port, timeout=_BUILD_TIMEOUT_S, proc=launched.proc, log_path=launched.log_path)
+
+    # 1. the serving claim
+    serving_marker = FRONTEND_DIR / dist_rel / ".trendora-serving"
+    assert serving_marker.exists(), f"expected the launcher to claim its dist dir at {serving_marker}"
+    marker_text = serving_marker.read_text()
+    assert f"port={port}" in marker_text, marker_text
+    claimed_pid = int(re.search(r"^pid=(\d+)$", marker_text, re.M).group(1))
+    os.kill(claimed_pid, 0)  # raises if the claimed pid is not actually alive
+    assert re.search(r"\b(next|npx|node)\b", _cmdline(claimed_pid)), (
+        f"the claimed pid must be the serving process itself, got cmdline: {_cmdline(claimed_pid)!r}"
+    )
+
+    # 2. a correctly-configured foreign build into the SERVED dir is refused, and serving is unharmed
+    build_id = FRONTEND_DIR / dist_rel / "BUILD_ID"
+    before = build_id.read_text()
+    env = dict(os.environ)
+    env["NEXT_DIST_DIR"] = dist_rel
+    env["NEXT_PUBLIC_API_URL"] = api_url
+    env.pop("TRENDORA_LAUNCH_BUILD", None)
+    proc = subprocess.run(
+        ["npx", "next", "build"], cwd=str(FRONTEND_DIR), env=env, capture_output=True, text=True, timeout=180
+    )
+    out = proc.stdout + proc.stderr
+    assert proc.returncode != 0, f"a build into a SERVED dist dir must be refused:\n{out[-2000:]}"
+    assert "being SERVED right now" in out, f"expected the serving-claim refusal, got:\n{out[-2000:]}"
+    assert str(claimed_pid) in out, f"the refusal must name the serving process, got:\n{out[-2000:]}"
+    assert build_id.read_text() == before, "the refused build must not have rewritten the served dist dir"
+    _assert_page_fully_styled(port)  # the live server was never torn
+
+    # 3. the claim expires with the process (no wedged dist dirs after a hard kill)
+    launched.stop()
+    allowed, verdict_out = _guard_verdict(dist_rel, api_url)
+    assert allowed, (
+        "once the serving process is gone its claim must expire -- a stale marker must never block a "
+        f"later build:\n{verdict_out}"
+    )
+
+
+def test_launcher_rebuilds_a_bundle_built_for_a_different_backend(launcher):
+    """finding B3 ("the shipped root cause was never instrumented"): the launcher now CHECKS, on every
+    launch, that the build it is about to serve actually references the backend this launch configured
+    -- the same `grep -rl "localhost:<port>" .next` the audit had to run by hand to diagnose B1.
+
+    Exercised end-to-end: build+serve against backend A, stop, relaunch pointing at backend B. Nothing
+    else changed -- sources are untouched and the provenance marker still matches -- so the ONLY thing
+    that can catch the mismatch is the new bundle check. Before it, the launcher logged "build is current
+    ... skipping rebuild" and served a frontend that could not reach its backend, which is precisely how
+    this iteration shipped a broken app past every green gate."""
+    if not (FRONTEND_DIR / "node_modules").exists():
+        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")
+    dist_rel = _scratch_dist_name("tc5-77")
+    port = _TC5_77_PORT
+    backend_a, backend_b = port + 1000, port + 1001
+
+    first = launcher(dist_rel, port, backend_a, "tc5-77-a.log")
+    _wait_for_port_answering(port, timeout=_BUILD_TIMEOUT_S, proc=first.proc, log_path=first.log_path)
+    chunks = list((FRONTEND_DIR / dist_rel / "static").rglob("*.js"))
+    assert any(f"http://localhost:{backend_a}" in c.read_text(errors="replace") for c in chunks), (
+        "sanity: the built client bundle must inline the backend URL this launch configured "
+        "(the fact the check below relies on)"
+    )
+    first.stop()
+
+    second = launcher(dist_rel, port, backend_b, "tc5-77-b.log")
+    _wait_for_port_answering(port, timeout=_BUILD_TIMEOUT_S, proc=second.proc, log_path=second.log_path)
+    log = second.log_text()
+    assert "was built for a different backend" in log, (
+        f"expected the launcher to DETECT the backend mismatch, got:\n{log[-2000:]}"
... [diff_bound] apps/backend/tests/test_start_frontend_script.py: 10 more diff lines omitted — Read the file for full detail
diff --git a/apps/frontend/app/backtest/page.tsx b/apps/frontend/app/backtest/page.tsx
index fc0612ba..b7faa94f 100644
--- a/apps/frontend/app/backtest/page.tsx
+++ b/apps/frontend/app/backtest/page.tsx
@@ -616,7 +616,11 @@ function ScorecardSection({ data }: { data: BacktestResponse }) {
               const qqq = controlCohort(row, "qqq");
               const sectorEtf = controlCohort(row, "sector_etf");
               return (
-                <tr key={row.horizon} className="border-b border-border last:border-b-0">
+                <tr
+                  key={row.horizon}
+                  data-testid={`scorecard-row-${row.horizon}d`}
+                  className="border-b border-border last:border-b-0"
+                >
                   <td className="num px-5 py-2 font-semibold text-text">{row.horizon}d</td>
                   <td className="bg-surface-2 px-3 py-2 text-right">
                     <Return value={row.cohort.mean_return} n={row.cohort.n} min={min} />
diff --git a/apps/frontend/app/layout.tsx b/apps/frontend/app/layout.tsx
index d506f32b..8e0b3c25 100644
--- a/apps/frontend/app/layout.tsx
+++ b/apps/frontend/app/layout.tsx
@@ -35,11 +35,20 @@ export default async function RootLayout({ children }: { children: React.ReactNo
             <div className="flex min-h-screen">
               <Sidebar />
               <div className="flex min-w-0 flex-1 flex-col">
-                <header className="sticky top-0 z-10 flex h-14 items-center justify-between gap-4 border-b border-border bg-surface px-6">
+                {/* ops-hardening iter-77 (iter-76/e fix): `min-h-14` (was a fixed `h-14`) + `flex-wrap`
+                    on the badge row below — at 1280x800 the combined AsOfSwitcher + HealthBadge content
+                    (readiness pill + staleness annotation + background-compute chip + provider/seed/
+                    symbol badges) can exceed the row's available width; without a wrap allowance the
+                    row simply overflowed the header's right edge instead of wrapping, pushing the
+                    "Ready" pill off-screen. `min-h-14` keeps the header at its normal 56px height on
+                    every page/width where content already fits on one line (unchanged), and only grows
+                    to a second line when the row actually wraps — HealthBadge's own inner `flex-wrap`
+                    (unchanged) can now take effect because the outer row no longer blocks it. */}
+                <header className="sticky top-0 z-10 flex min-h-14 items-center justify-between gap-4 border-b border-border bg-surface px-6 py-2">
                   <span className="hidden text-sm text-text-muted lg:inline">
                     Research-only · decision support · no orders
                   </span>
-                  <div className="flex flex-1 items-center justify-end gap-3">
+                  <div className="flex flex-1 flex-wrap items-center justify-end gap-3">
                     <AsOfSwitcher />
                     <HealthBadge />
                   </div>
diff --git a/apps/frontend/components/health-badge.tsx b/apps/frontend/components/health-badge.tsx
index 0d767cc8..54c446c8 100644
--- a/apps/frontend/components/health-badge.tsx
+++ b/apps/frontend/components/health-badge.tsx
@@ -5,6 +5,7 @@ import { useEffect, useState } from "react";
 import { Badge } from "@/components/ui/badge";
 import { useReadiness } from "@/components/readiness-provider";
 import { fetchHealth, type HealthStatus } from "@/lib/api";
+import { formatStaleAnnotation } from "@/lib/staleness-annotation";
 
 type Detail =
   | { kind: "loading" }
@@ -20,7 +21,7 @@ type Detail =
  *  re-renders for, without a second polling loop. Re-checks of `state`/`warmup` themselves happen via the
  *  readiness provider's own config-derived poll. */
 export function HealthBadge() {
-  const { state, warmup, backgroundCompute, loading } = useReadiness();
+  const { state, warmup, backgroundCompute, loading, staleForS } = useReadiness();
   const [detail, setDetail] = useState<Detail>({ kind: "loading" });
 
   // The context detail (provider / seed date / symbol count / the `awaiting_snapshot` recovery-pointer
@@ -100,9 +101,22 @@ export function HealthBadge() {
   // (`useReadiness()`) -- no second fetch.
   const activeComputeCount = backgroundCompute?.active.length ?? 0;
 
+  // ops-hardening iter-77 (J-04/J-07): the FIRST UI consumer of GET /api/health's `stale_for_s` --
+  // a calm, factual "as of Ns ago" annotation naming how old the payload the badge/chip above are
+  // built from is. Shown only when genuinely stale (`stale_for_s > 0`); never shown for a fresh
+  // synchronous compute or when the health poll itself failed (formatStaleAnnotation's own honesty
+  // contract -- see lib/staleness-annotation.ts). Plain inline text next to the existing pill, not a
+  // new component type (this project's DESIGN SYSTEM convention for a small factual annotation).
+  const staleAnnotation = formatStaleAnnotation(staleForS);
+
   return (
     <div className="flex flex-wrap items-center gap-2">
       {pill}
+      {staleAnnotation ? (
+        <span className="num text-xs text-text-faint" data-testid="readiness-staleness">
+          {staleAnnotation}
+        </span>
+      ) : null}
       {activeComputeCount > 0 ? (
         <Badge variant="accent" className="num gap-1.5" data-testid="background-compute-indicator">
           <span className="h-2 w-2 animate-pulse rounded-full bg-accent" aria-hidden />
diff --git a/apps/frontend/components/preflight-banner.tsx b/apps/frontend/components/preflight-banner.tsx
index 3c6f5392..ff2a1504 100644
--- a/apps/frontend/components/preflight-banner.tsx
+++ b/apps/frontend/components/preflight-banner.tsx
@@ -1,6 +1,7 @@
 "use client";
 
 import { useReadiness } from "@/components/readiness-provider";
+import { formatStaleAnnotation } from "@/lib/staleness-annotation";
 import { cn } from "@/lib/utils";
 
 /**
@@ -17,7 +18,11 @@ import { cn } from "@/lib/utils";
  * buy/sell-order language (anti-goals #1/#2 — this gates trust, not orders).
  */
 export function PreflightBanner() {
-  const { preflight, loading } = useReadiness();
+  const { preflight, loading, staleForS } = useReadiness();
+  // ops-hardening iter-77 (J-04/J-07): the SAME "as of Ns ago" annotation the readiness badge renders,
+  // reading the SAME single `useReadiness()` poll (no second fetch) -- honest by construction: null
+  // (no annotation) for a fresh synchronous compute, a failed poll, or before the first poll resolves.
+  const staleAnnotation = formatStaleAnnotation(staleForS);
 
   if (loading) {
     // Mirrors HealthBadge's `loading` state: a neutral placeholder, never a fabricated GO.
@@ -35,10 +40,14 @@ export function PreflightBanner() {
 
   if (preflight === null) {
     // The health poll itself failed (backend unreachable) — an honest NO-GO, never a blank crash.
+    // No staleness annotation here either: `staleForS` is already null on a failed poll (the SAME
+    // honest-failure convention every sibling readiness field follows), so `staleAnnotation` above is
+    // already null too — nothing to pass.
     return (
       <LoudBanner
         verdict="NO-GO"
         reasons={["Backend is unavailable — the preflight check could not run."]}
+        staleAnnotation={null}
       />
     );
   }
@@ -53,14 +62,27 @@ export function PreflightBanner() {
       >
         <span className="h-1.5 w-1.5 rounded-full bg-pos" aria-hidden />
         GO — today&apos;s board is current.
+        {staleAnnotation ? (
+          <span className="text-pos/70" data-testid="preflight-staleness">
+            ({staleAnnotation})
+          </span>
+        ) : null}
       </div>
     );
   }
 
-  return <LoudBanner verdict={preflight.verdict} reasons={preflight.reasons} />;
+  return <LoudBanner verdict={preflight.verdict} reasons={preflight.reasons} staleAnnotation={staleAnnotation} />;
 }
 
-function LoudBanner({ verdict, reasons }: { verdict: "DEGRADED" | "NO-GO"; reasons: string[] }) {
+function LoudBanner({
+  verdict,
+  reasons,
+  staleAnnotation,
+}: {
+  verdict: "DEGRADED" | "NO-GO";
+  reasons: string[];
+  staleAnnotation: string | null;
+}) {
   const isNoGo = verdict === "NO-GO";
   return (
     <div
@@ -76,6 +98,11 @@ function LoudBanner({ verdict, reasons }: { verdict: "DEGRADED" | "NO-GO"; reaso
         {isNoGo
           ? "NO-GO — do not rely on today's board."
           : "DEGRADED — treat today's board with caution."}
+        {staleAnnotation ? (
+          <span className="ml-1.5 font-normal opacity-70" data-testid="preflight-staleness">
+            ({staleAnnotation})
+          </span>
+        ) : null}
       </p>
       {reasons.length > 0 ? (
         <ul className="mt-1 list-disc space-y-0.5 pl-5">
diff --git a/apps/frontend/components/readiness-provider.tsx b/apps/frontend/components/readiness-provider.tsx
index 821d440b..afcdde72 100644
--- a/apps/frontend/components/readiness-provider.tsx
+++ b/apps/frontend/components/readiness-provider.tsx
@@ -47,6 +47,12 @@ export interface ReadinessContextValue {
    *  second fetch. Null before the first poll resolves / on a failed poll (mirrors every sibling field's
    *  honesty convention) — callers must gate their own interval on a non-null value. */
   pollIdleIntervalSeconds: number | null;
+  /** ops-hardening iter-77 — the SAME `GET /api/health` payload's `stale_for_s` (seconds since the
+   *  served readiness/preflight/background-compute payload was computed; 0 for a fresh synchronous
+   *  compute), first rendered by the readiness badge/preflight banner's "as of {N}s ago" annotation.
+   *  Null before the first poll resolves / on a failed poll — readers must never render a stale or
+   *  fabricated number in that case (mirrors every sibling field's honesty convention). */
+  staleForS: number | null;
 }
 
 const ReadinessContext = createContext<ReadinessContextValue | null>(null);
@@ -63,6 +69,7 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
   const [backgroundCompute, setBackgroundCompute] = useState<BackgroundComputeStatus | null>(null);
   const [loading, setLoading] = useState(true);
   const [pollIdleIntervalSeconds, setPollIdleIntervalSeconds] = useState<number | null>(null);
+  const [staleForS, setStaleForS] = useState<number | null>(null);
   // the config-derived cadences (seconds) from the latest payload; refs so the polling loop reads the
   // freshest value without re-subscribing.
   const activeMs = useRef(BOOTSTRAP_ACTIVE_MS);
@@ -82,6 +89,7 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
         setPreflight(data.preflight);
         setBackgroundCompute(data.background_compute);
         setPollIdleIntervalSeconds(data.poll_idle_interval_seconds);
+        setStaleForS(data.stale_for_s);
         // adopt the config-derived poll cadences (seconds → ms); never a client-side literal.
         activeMs.current = Math.max(250, Math.round(data.poll_interval_seconds * 1000));
         idleMs.current = Math.max(activeMs.current, Math.round(data.poll_idle_interval_seconds * 1000));
@@ -94,6 +102,7 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
         setPreflight(null); // honest — the banner renders its own NO-GO for a null preflight, never blank
         setBackgroundCompute(null); // honest — readers render their own empty/idle state, never fabricated
         setPollIdleIntervalSeconds(null); // honest — a caller's own idle-refresh loop must not schedule on this
+        setStaleForS(null); // honest — never render a stale/fabricated "as of Ns ago" for a failed poll
         nextDelay = activeMs.current; // keep retrying at the active cadence until the backend answers
       } finally {
         if (active) {
@@ -111,8 +120,8 @@ export function ReadinessProvider({ children }: { children: React.ReactNode }) {
   }, []);
 
   const value = useMemo<ReadinessContextValue>(
-    () => ({ state, warmup, preflight, backgroundCompute, loading, pollIdleIntervalSeconds }),
-    [state, warmup, preflight, backgroundCompute, loading, pollIdleIntervalSeconds],
+    () => ({ state, warmup, preflight, backgroundCompute, loading, pollIdleIntervalSeconds, staleForS }),
+    [state, warmup, preflight, backgroundCompute, loading, pollIdleIntervalSeconds, staleForS],
   );
 
   return <ReadinessContext.Provider value={value}>{children}</ReadinessContext.Provider>;
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index b41f2e43..e5a462a9 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -205,6 +205,11 @@ export interface HealthStatus {
   preflight: PreflightStatus;
   // ops-hardening iter-24 (J-09): the historical background-compute dispatch disclosure (additive).
   background_compute: BackgroundComputeStatus;
+  // ops-hardening iter-71 (J-07 closure): seconds since THIS payload was computed (0.0 when computed
+  // synchronously for this request) -- see app.engine.readiness.get_readiness_and_preflight. iter-77 is
+  // this field's FIRST UI consumer (the readiness badge / preflight banner "as of {N}s ago" annotation);
+  // the backend has served it since iter-71 but nothing rendered it until now.
+  stale_for_s: number;
 }
 
 /** Fetch backend health + readiness. Throws on network error or non-200 so callers can render an
diff --git a/apps/frontend/next.config.mjs b/apps/frontend/next.config.mjs
index 682f8a6e..19c8dd9c 100644
--- a/apps/frontend/next.config.mjs
+++ b/apps/frontend/next.config.mjs
@@ -1,12 +1,159 @@
-/** @type {import('next').NextConfig} */
-const nextConfig = {
-  reactStrictMode: true,
-  // No ESLint config is shipped for the MVP; UI behaviour is covered by browser QA.
-  // Type-checking stays ON (the frontend "test" is `npm run build` = compile + typecheck).
-  eslint: { ignoreDuringBuilds: true },
+import { existsSync, readFileSync } from "node:fs";
+import { dirname, resolve } from "node:path";
+import { fileURLToPath } from "node:url";
+
+// ==== TRENDORA BUILD GUARD (ops-hardening iter-77 audit fix B2) ======================================
+// WHY THIS EXISTS: an out-of-band `npx next build` run inside `apps/frontend` as a *verification* step
+// (the exact command iter-77's own dev handoff and QA report each record running) rewrote the LIVE
+// `.next` that `next start` was serving at that moment. Two distinct harms, both reproduced during the
+// iter-77 audit:
+//   (1) the verification build carries no `NEXT_PUBLIC_API_URL`/`NEXT_PUBLIC_API_PORT` (only
+//       `scripts/start-frontend.sh` exports them), so Next inlines `lib/api.ts`'s
+//       `http://localhost:8000` fallback -- a port NOTHING in this project binds -- and every page then
+//       renders the global "Backend unavailable" state while the backend is perfectly healthy;
+//   (2) rewriting a dist dir a live `next start` is serving tears that server's assets mid-flight
+//       (the iteration's own demo gallery captured five consecutive full-page crash-boundary frames).
+// The launcher's build lock cannot serialize this (a bare `next build` is not a launcher invocation) and
+// its mtime-based staleness check cannot see it (the foreign build looks perfectly current).
+//
+// `next.config.mjs` is the ONE file every `next build` must load, whoever invokes it and however -- so
+// the guard lives here. It refuses the build with an actionable message instead of letting it corrupt a
+// live serving directory. The project already ships throwaway dist dirs (`.next-verify`, `.next-alt-qa`)
+// for exactly this; the message names them.
+// This is a BUILD-PHASE-ONLY guard: `next start` / `next dev` load this same config and are untouched.
+const LIVE_DIST_DIR = ".next";
+const SERVING_MARKER = ".trendora-serving";
+const PHASE_PRODUCTION_BUILD = "phase-production-build";
+// Next resolves a relative `distDir` against the PROJECT dir (where this config lives), not the caller's
+// cwd — resolve the same way so the guard reads the same directory Next is about to write.
+const PROJECT_DIR = dirname(fileURLToPath(import.meta.url));
+
+/** True iff `pid` is alive AND still looks like a Node/Next server process. The liveness check alone
+ *  would be fooled by PID reuse after a server exits without clearing its marker; the `/proc` cmdline
+ *  check makes a false "it is still being served" refusal effectively impossible. Hosts without `/proc`
+ *  fall back to liveness alone. */
+function looksLikeALiveServer(pid) {
+  try {
+    process.kill(pid, 0);
+  } catch (err) {
+    // EPERM = the process exists but belongs to another user -> still alive.
+    if (err?.code !== "EPERM") return false;
+  }
+  try {
+    const cmdline = readFileSync(`/proc/${pid}/cmdline`, "utf8").replace(/\0/g, " ");
+    return /(^|[\s/])(next|npx|node|taskset)(\s|$)/.test(cmdline);
+  } catch {
+    return true;
+  }
+}
+
+/** The `{pid, port}` of the process currently SERVING `distDir`, or null when nothing is. Written by
+ *  `scripts/start-frontend.sh` immediately before it `exec`s `next start` (so the recorded pid IS the
+ *  serving process), and self-invalidating: a marker whose pid is gone reads as "nothing is serving". */
+function liveServerOwning(distDir) {
+  const markerPath = resolve(PROJECT_DIR, distDir, SERVING_MARKER);
+  if (!existsSync(markerPath)) return null;
+  let raw;
+  try {
+    raw = readFileSync(markerPath, "utf8");
+  } catch {
+    return null;
+  }
+  const fields = {};
+  for (const line of raw.split("\n")) {
+    const eq = line.indexOf("=");
+    if (eq > 0) fields[line.slice(0, eq)] = line.slice(eq + 1);
+  }
+  const pid = Number.parseInt(fields.pid ?? "", 10);
+  if (!Number.isInteger(pid) || pid <= 0) return null;
+  if (!looksLikeALiveServer(pid)) return null;
+  return { pid, port: fields.port ?? "unknown" };
+}
+
+function assertProductionBuildMayTarget(distDir) {
+  // `scripts/start-frontend.sh` sets this for its OWN build. It is not an escape hatch for verification
+  // builds: the launcher holds the per-dist-dir build lock, always exports the backend URL, and is the
+  // process that will serve the result.
+  const launcherBuild = process.env.TRENDORA_LAUNCH_BUILD === "1";
+  const serving = liveServerOwning(distDir);
+
+  if (serving && !launcherBuild) {
+    throw new Error(
+      [
+        "",
+        `TRENDORA BUILD GUARD: refusing to build into '${distDir}' — it is being SERVED right now`,
+        `(next start, pid ${serving.pid}, port ${serving.port}).`,
+        "",
+        "Rewriting a dist directory a live server is serving tears that server's assets mid-flight:",
+        "chunk requests start 404-ing and the app renders a full-page error boundary (ops-hardening",
+        "iter-77 audit, finding B1/B2). Build somewhere else instead:",
+        "",
+        "    NEXT_DIST_DIR=.next-verify npx next build     # verification / typecheck build",
+        "",
+        "To rebuild what is actually served, restart it through the launcher (it holds the build lock,",
+        "exports this project's backend URL, and serves the result itself):",
+        "",
+        "    scripts/start-frontend.sh",
+        "",
+        `(If no server is really running, remove the stale marker: rm ${distDir}/${SERVING_MARKER})`,
+        "",
+      ].join("\n"),
+    );
+  }
+
+  if (serving && launcherBuild) {
+    // A launcher rebuild while ANOTHER launcher serves the same dist dir (two invocations on different
+    // ports — `test_concurrent_invocations_never_serve_partial_build`'s shape). Allowed, because the
+    // launcher owns this directory's lifecycle and refusing here could deadlock a legitimate restart —
+    // but never silently.
+    console.warn(
+      `[trendora build guard] WARNING: rebuilding '${distDir}' while pid ${serving.pid} is serving it ` +
+        `on port ${serving.port} — that server's in-flight asset requests may 404 until it restarts.`,
+    );
+  }
+
+  if (distDir === LIVE_DIST_DIR && !process.env.NEXT_PUBLIC_API_URL) {
+    throw new Error(
+      [
+        "",
+        `TRENDORA BUILD GUARD: refusing to build into the live dist dir '${LIVE_DIST_DIR}' without`,
+        "NEXT_PUBLIC_API_URL set.",
+        "",
+        "Next inlines that value into the client bundle at BUILD time. Without it, lib/api.ts falls back",
+        "to http://localhost:8000 — a port nothing in this project binds — and every page renders",
+        "'Backend unavailable' against a perfectly healthy backend (ops-hardening iter-77 audit, B1).",
+        "",
+        "For a verification / typecheck build, target a throwaway dir (never the live one):",
+        "",
+        "    NEXT_DIST_DIR=.next-verify npx next build",
+        "",
+        "To (re)build what is actually served, use the launcher — it derives this project's backend port",
+        "and exports NEXT_PUBLIC_API_URL/NEXT_PUBLIC_API_PORT for you:",
+        "",
+        "    scripts/start-frontend.sh",
+        "",
+      ].join("\n"),
+    );
+  }
+}
+// ==== end TRENDORA BUILD GUARD ========================================================================
+
+/** @type {(phase: string) => import('next').NextConfig} */
+export default function nextConfig(phase) {
   // `NEXT_DIST_DIR` lets a verification build write to a THROWAWAY dir instead of `.next`, so a CI/dev
-  // typecheck-build never clobbers a running `next dev` server's `.next` (defaults to `.next`).
-  distDir: process.env.NEXT_DIST_DIR || ".next",
-};
+  // typecheck-build never clobbers a running server's `.next` (defaults to `.next`).
+  const distDir = process.env.NEXT_DIST_DIR || LIVE_DIST_DIR;
+
+  // Build phase only — serving (`next start`) and `next dev` load this same config untouched.
+  if (phase === PHASE_PRODUCTION_BUILD || process.env.NEXT_PHASE === PHASE_PRODUCTION_BUILD) {
+    assertProductionBuildMayTarget(distDir);
+  }
 
-export default nextConfig;
+  return {
+    reactStrictMode: true,
+    // No ESLint config is shipped for the MVP; UI behaviour is covered by browser QA.
+    // Type-checking stays ON (the frontend "test" is `npm run build` = compile + typecheck).
+    eslint: { ignoreDuringBuilds: true },
+    distDir,
+  };
+}
diff --git a/incredible_auto_dev/scripts/automation/lib/demo_runner.py b/incredible_auto_dev/scripts/automation/lib/demo_runner.py
index 304204be..16c61600 100644
--- a/incredible_auto_dev/scripts/automation/lib/demo_runner.py
+++ b/incredible_auto_dev/scripts/automation/lib/demo_runner.py
@@ -1004,6 +1004,127 @@ class _FakePage:
         self._spy.setdefault("screenshots", []).append(path)
 
 
+class _FakeSettlingLocator:
+    """Duck-typed Locator whose visibility depends on the page's own simulated phase — the minimum
+    surface `_settle_for_capture`'s `exp`-aware wait (`_check_expect` -> `get_by_text(...).wait_for`)
+    needs. See `_FakeSettlingPage` for the model this exercises."""
+
+    def __init__(self, page: "_FakeSettlingPage", text: str):
+        self._page = page
+        self._text = text
+
+    @property
+    def first(self):
+        return self
+
+    def wait_for(self, state: str = "visible", timeout: float = 0):
+        page = self._page
+        if self._text == page.before_text:
+            if page.phase != "before":
+                raise TimeoutError(f"fake: {self._text!r} not visible in phase {page.phase!r}")
+            return
+        if self._text == page.gate_text:
+            n = page.attempts.get(self._text, 0) + 1
+            page.attempts[self._text] = n
+            if n >= page.ready_after:
+                page.phase = "after"
+                return
+            raise TimeoutError(f"fake: {self._text!r} not visible yet (poll {n}/{page.ready_after})")
+        raise TimeoutError(f"fake: unexpected text {self._text!r}")
+
+
+class _FakeAlwaysReadyLocator:
+    """Always-visible, always-clickable no-op locator for a step's MUTATING control target (e.g. a
+    'Start' button) in `_FakeSettlingPage` — always found and clicked; the state change it triggers is
+    observed later via the page's gate-text poll count (see `_FakeSettlingLocator`), not synchronously
+    at click time, mirroring how a real backfill's effect surfaces through a LATER read."""
+
+    @property
+    def first(self):
+        return self
+
+    def wait_for(self, state: str = "visible", timeout: float = 0):
+        return
+
+    def click(self, timeout: float = 0):
+        return
+
+
+class _FakeSettlingPage:
+    """Models a step whose real (backend-driven) content becomes visible only after >= `ready_after`
+    polls for its OWN expect text — an eventually-consistent read, the same shape a real async
+    re-render/poll-tick produces. `before_text` is trivially visible while `phase == "before"`;
+    `gate_text` only becomes visible (and flips `phase` to `"after"`) once it has been polled
+    `ready_after` times — enough to distinguish a settle that actively re-polls the step's own `exp`
+    from one that does not (ops-hardening iter-77 / iter-76/d: the byte-identical before/after
+    walkthrough-frame defect). `screenshot()` records the phase AT CAPTURE TIME, so a test can assert
+    the two captured frames reflect genuinely different states, not the same one twice."""
+
+    def __init__(self, before_text: str, gate_text: str, ready_after: int = 2):
+        self.phase = "before"
+        self.before_text = before_text
+        self.gate_text = gate_text
+        self.ready_after = ready_after
+        self.attempts: dict[str, int] = {}
+        self.screenshots: list[tuple[str, str]] = []
+
+    def get_by_text(self, text: str) -> _FakeSettlingLocator:
+        return _FakeSettlingLocator(self, text)
+
+    def get_by_role(self, role: str, name: str = "") -> _FakeAlwaysReadyLocator:
+        return _FakeAlwaysReadyLocator()
+
+    def goto(self, url: str, wait_until: "str | None" = None, timeout: float = 0):
+        pass
+
+    def wait_for_timeout(self, ms: int):
+        pass
+
+    def screenshot(self, path: "str | None" = None):
+        self.screenshots.append((path, self.phase))
+
+
+def _t_settle_for_capture_before_after_frames_differ_when_state_changes() -> None:
+    """TC-9 (ops-hardening iter-77, iter-76/d): a state-changing step's 'after' capture must reflect
+    the ACTUAL post-change content, never a stale pre-change frame identical to the 'before' capture —
+    the exact defect observed in iter-76's recorded gallery (`reports/demo/goal-ops-hardening-iter-76/`
+    step-05.png and step-06.png, and step-04.png/step-07.png, came back pairwise byte-identical).
+
+    `_FakeSettlingPage`'s gate text only becomes visible on its SECOND poll. The record loop's own
+    upstream `_check_expect` call (unrelated to this fix, unchanged) always performs poll #1 and always
+    finds it not-yet-visible on this fixture (a soft note is expected and asserted below). Only
+    `_settle_for_capture`'s NEW `exp`-aware re-poll (this iteration's fix) performs poll #2, which is
+    the one that actually observes the change — so this test FAILS against the pre-fix
+    `_settle_for_capture(page, budget_ms)` (no `exp` parameter at all, so the gate text is never polled
+    a second time and the 'after' step's screenshot is captured before the change lands), and PASSES
+    only once the fix threads `exp` through into an active re-poll."""
+    import tempfile
+    page = _FakeSettlingPage(before_text="No jobs yet", gate_text="Completed", ready_after=2)
+    steps = [
+        {"n": 1, "journey": "J-05", "title": "Before: job history is empty",
+         "action": {"type": "goto", "url": "/data"}, "expect": {"text": "No jobs yet"}},
+        {"n": 2, "journey": "J-05", "title": "After: the backfill has completed",
+         "action": {"type": "click", "target": {"role": "button", "name": "Start"}},
+         "expect": {"text": "Completed"}},
+    ]
+    with tempfile.TemporaryDirectory() as tmp:
+        _captured, soft_notes, _script_steps = _record_steps(
+            page, steps, "http://localhost:3000", 4000, Path(tmp), None)
+
+    assert len(page.screenshots) == 2, page.screenshots
+    before_phase = page.screenshots[0][1]
+    after_phase = page.screenshots[1][1]
+    assert before_phase == "before", page.screenshots
+    assert after_phase == "after", (
+        "the after-step capture must reflect the real post-change state, not a stale frame "
+        f"identical to the before capture: {page.screenshots}"
+    )
+    assert before_phase != after_phase, "before/after frames must not capture the same state"
+    # The record loop's OWN first poll (before this fix's re-poll ever runs) genuinely misses on this
+    # fixture, so a soft note for step 2 is the expected, honest behavior — not silently swallowed.
+    assert any("02" in note and "did not appear" in note for note in soft_notes), soft_notes
+
+
 def _t_run_record_never_clicks_after_failed_precondition() -> None:
     # TC-4: given a fake page/script fixture where step N's `fill` raises and step N+1 is a
     # `click` on `role: button`, when the record loop executes that script, then step N+1's
@@ -1207,6 +1328,7 @@ _SELF_TEST_CHECKS = [
     _t_launch_chromium_retries,
     _t_run_record_never_clicks_after_failed_precondition,
     _t_run_record_click_still_fires_without_a_prior_failure,
+    _t_settle_for_capture_before_after_frames_differ_when_state_changes,
     _t_derive_happy,
     _t_derive_rejects_untagged_journey,
     _t_derive_rejects_no_expect,
@@ -1429,16 +1551,40 @@ _LOADING_SELECTOR = (
 )
 
 
-def _settle_for_capture(page, budget_ms: int) -> None:
-    """Best-effort wait for the page to finish loading before a screenshot, so the
-    gallery never captures a spinner / empty skeleton. NEVER raises — the demo is a
-    showcase, not a gate.
-
-    Three guards, each bounded by the budget: (1) network goes idle so client-side
-    fetches land; (2) any visible loading indicator disappears; (3) web fonts are
-    ready, plus a short paint settle. An SPA that long-polls may never reach idle,
-    which is exactly why every step is best-effort and falls through on timeout."""
-    budget_ms = max(1000, min(int(budget_ms), 12000))
+def _settle_for_capture(page, budget_ms: int, exp: "dict | None" = None) -> None:
+    """Best-effort wait for the page to finish loading — and, when `exp` is given, for the
+    SPECIFIC post-action content the step names — before a screenshot, so the gallery never
+    captures a spinner / empty skeleton, and (iter-77 fix) never captures the PREVIOUS state
+    relabeled as the new one. NEVER raises — the demo is a showcase, not a gate.
+
+    ops-hardening iter-77 (iter-76/d): the recorded gallery was producing byte-identical
+    'before'/'after' frame pairs for state-changing steps (e.g. a background-compute window's
+    active-vs-completed /data view). Root cause: this function only ran GENERIC settle
+    heuristics (network idle / loading-indicator-hidden / fonts-ready / a flat paint pause)
+    that are blind to WHICH content a given step actually cares about — all four can resolve
+    instantly while the page is still showing the PRE-action state (a re-render that has not
+    landed yet, a poll that has not ticked). It also silently RE-CAPPED whatever budget the
+    caller passed down to a flat 12s, even when a step's own `timeout_ms` (honored everywhere
+    else in this file, up to 20s — see `_default_timeout`/`_record_steps`) asked for more.
+
+    The fix: when the caller passes the step's own `exp`(ect) — the same `{"text": ...}` /
+    `{"target": ...}` shape `_check_expect` already uses to grade the step — that becomes the
+    PRIMARY settle signal, actively (re-)polled for up to the caller's own budget (no longer
+    silently truncated) before the generic heuristics run. `exp=None` (steps with no expect,
+    e.g. `full_tour` framing shots) falls back to the prior generic-only behavior, budget cap
+    included, unchanged.
+
+    Four guards, each bounded by the budget: (0, new) the step's own expect condition becomes
+    visible; (1) network goes idle so client-side fetches land; (2) any visible loading
+    indicator disappears; (3) web fonts are ready, plus a short paint settle. An expect that
+    never resolves within the budget is not an error here (the caller's own soft-note bookkeeping
+    already covers that) — every guard, including the new one, falls through on timeout."""
+    if exp:
+        try:
+            _check_expect(page, exp, max(1000, int(budget_ms)))
+        except Exception:
+            pass  # best-effort — the generic heuristics below still run regardless
+    budget_ms = max(1000, min(int(budget_ms), 20000))
     try:
         page.wait_for_load_state("networkidle", timeout=budget_ms)
     except Exception:
@@ -1667,8 +1813,10 @@ def _record_steps(page, steps: list[dict], base_url: str, default_tmo: int,
         shot_rel = ""
         if section != "full_tour":
             # Settle (network idle + loading indicators gone + paint) so the
-            # gallery never captures a spinner / empty skeleton.
-            _settle_for_capture(page, tmo)
+            # gallery never captures a spinner / empty skeleton. iter-77: pass this
+            # step's own `exp` so a state-changing step's capture actively waits for
+            # ITS content, never a stale pre-action frame (iter-76/d fix).
+            _settle_for_capture(page, tmo, exp)
             shot_abs = out_dir / f"step-{n:02d}.png"
             try:
                 page.screenshot(path=str(shot_abs))
@@ -1779,7 +1927,9 @@ def run_live(script: dict, opts, base_url: str) -> int:
                 pass
             try:
                 _do_action(page, action, base_url, tmo)
-                _settle_for_capture(page, tmo)  # let content load before the human looks
+                # let content load before the human looks; iter-77: pass this step's own
+                # `exp` too, same iter-76/d fix as the record path.
+                _settle_for_capture(page, tmo, step.get("expect"))
                 if step.get("point_out"):
                     print(f"   ↳ Notice: {step['point_out']}")
             except Exception as exc:  # noqa: BLE001
@@ -1897,6 +2047,7 @@ def run_verify(opts, base_url: str) -> int:
                 context = browser.new_context(viewport={"width": 1280, "height": 800})
                 page = context.new_page()
                 verdict, actual = "PASS", "journey replayed end-to-end; all expects held"
+                exp = None  # last step's expect, if any -- passed to the final evidence capture below
                 for step in steps:
                     n = int(step.get("n", 0))
                     tmo = max(1000, min(int(step.get("timeout_ms", default_tmo)), 20000))
@@ -1914,7 +2065,10 @@ def run_verify(opts, base_url: str) -> int:
                         break
                 shot_rel = "none"
                 if evidence_dir:
-                    _settle_for_capture(page, default_tmo)
+                    # iter-77: pass the last-executed step's own `exp` too (same iter-76/d fix as the
+                    # record/live paths) so the evidence screenshot reflects the journey's real end
+                    # state rather than a frame settled purely on generic network/paint heuristics.
+                    _settle_for_capture(page, default_tmo, exp)
                     shot_abs = evidence_dir / f"{jid}-verify.png"
                     try:
                         page.screenshot(path=str(shot_abs))
diff --git a/incredible_auto_dev/scripts/start-frontend.sh b/incredible_auto_dev/scripts/start-frontend.sh
index 0250cce6..8499170c 100755
--- a/incredible_auto_dev/scripts/start-frontend.sh
+++ b/incredible_auto_dev/scripts/start-frontend.sh
@@ -66,6 +66,129 @@ fi
 # scratch directory instead of clobbering a live `.next`.
 DIST_DIR="${NEXT_DIST_DIR:-.next}"
 BUILD_ID_FILE="$DIST_DIR/BUILD_ID"
+# ops-hardening iter-77 AUDIT FIX — provenance marker for "this launcher produced the build now on
+# disk". WHY: the staleness check below compares SOURCE MTIMES against BUILD_ID, which cannot see that
+# the build itself was produced OUT OF BAND (a bare `npx next build` in apps/frontend — the exact
+# command this iteration's own dev handoff and QA report each record running as a verification step).
+# Such a build carries NO `NEXT_PUBLIC_API_URL`/`NEXT_PUBLIC_API_PORT` (this script exports them above;
+# a bare `next build` does not), so Next bakes the client fallback `http://localhost:8000` into the
+# bundle instead of this project's deterministic backend port — every page then renders the global
+# "Backend unavailable" state while the backend is perfectly healthy. Reproduced live during the
+# iter-77 audit: the tree's `.next` (built out of band) served that state to every fresh browser
+# session, this script logged "build is current ... skipping rebuild" over it, and the iteration's own
+# demo lane soft-failed all 7 steps against it; a rebuild through THIS script fixed it outright.
+# The marker is written INSIDE the dist dir, so any out-of-band `next build` (which rewrites the dist
+# dir and always mints a fresh BUILD_ID) invalidates it two ways over: the file is gone, or its
+# recorded build id no longer matches. A launcher-produced build always matches, so an ordinary
+# sequential restart still skips the rebuild exactly as before.
+# SCOPE NOTE (deliberate, not an oversight): the gate compares ONLY provenance + build id, not the
+# recorded api_url/api_port below. Gating on those too would make two CONCURRENT invocations that
+# differ only in backend port (`test_concurrent_invocations_never_serve_partial_build`'s fixture)
+# rebuild over each other's live dist dir — the very race the build lock above closes. The values are
+# recorded for diagnosis and can be promoted into the gate once that fixture pins one backend port.
+# ROUND-2 UPDATE: that promotion happened, without pinning the fixture — `_bundle_targets_configured_
+# backend` below checks the EMITTED BUNDLES (the ground truth, not this recorded value) and skips the
+# rebuild when another live server owns the dist dir, so the concurrent-invocation case stays safe.
+BUILD_ENV_FILE="$DIST_DIR/.trendora-launch-build"
+
+# ops-hardening iter-77 AUDIT FIX #2 (finding B2) — "who is SERVING this dist dir right now" marker.
+# Written immediately before this script `exec`s `next start`, so the pid it records IS the serving
+# process (exec keeps $$). `apps/frontend/next.config.mjs`'s build guard reads it and REFUSES any
+# non-launcher `next build` targeting a dist dir a live server is serving — the second half of B1 (a
+# foreign build tearing a running server mid-round, which is how iter-77's own demo lane captured five
+# consecutive full-page crash frames). Self-invalidating: a marker whose pid is gone reads as "nothing is
+# serving", so a hard-killed server never blocks a later build.
+SERVING_MARKER_FILE="$DIST_DIR/.trendora-serving"
+
+_write_launch_build_marker() {
+  {
+    printf 'launcher=start-frontend.sh\n'
+    printf 'build_id=%s\n' "$(cat "$BUILD_ID_FILE" 2>/dev/null || true)"
+    printf 'api_url=%s\n' "${NEXT_PUBLIC_API_URL}"
+    printf 'api_port=%s\n' "${NEXT_PUBLIC_API_PORT}"
+  } >"$BUILD_ENV_FILE"
+}
+
+_write_serving_marker() {
+  {
+    printf 'pid=%s\n' "$$"
+    printf 'port=%s\n' "$FRONTEND_PORT"
+    printf 'dist=%s\n' "$DIST_DIR"
+    printf 'started_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
+  } >"$SERVING_MARKER_FILE"
+}
+
+# True iff some OTHER live process is currently serving this dist dir (per its serving marker).
+_dist_dir_has_live_server() {
+  [[ -f "$SERVING_MARKER_FILE" ]] || return 1
+  local pid
+  pid="$(grep -m1 '^pid=' "$SERVING_MARKER_FILE" 2>/dev/null | cut -d= -f2)"
+  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
+  [[ "$pid" != "$$" ]] || return 1
+  kill -0 "$pid" 2>/dev/null || return 1
+  # Guard against PID reuse: the recorded pid must still look like a Node/Next server process.
+  tr '\0' ' ' <"/proc/$pid/cmdline" 2>/dev/null | grep -qE '(^|[ /])(next|npx|node|taskset)( |$)'
+}
+
+# ops-hardening iter-77 AUDIT FIX #3 (finding B3 — "the shipped root cause was never instrumented").
+# The concrete failure this DETECTS (rather than reasons about): the bundle on disk was built for a
+# DIFFERENT backend than this launch is configured for, so every page renders "Backend unavailable"
+# while the backend is healthy. Next inlines NEXT_PUBLIC_API_URL as a literal at build time
+# (`lib/api.ts`'s CONFIGURED_API_BASE), so its presence in the emitted client/server bundles is a direct,
+# checkable fact — exactly the `grep -rl "localhost:<port>" .next` the iter-77 audit had to run by hand
+# after the fact. Cheap (a grep over the emitted chunks) and runs on EVERY launch, so this class of
+# breakage now surfaces at startup in the launcher's own log instead of hours later in forensics.
+_bundle_targets_configured_backend() {
+  [[ -n "${NEXT_PUBLIC_API_URL:-}" ]] || return 0
+  grep -rqF "$NEXT_PUBLIC_API_URL" "$DIST_DIR/static" "$DIST_DIR/server" 2>/dev/null
+}
+
+# True iff the build currently on disk is one THIS launcher produced (marker present AND its recorded
+# build id is the one on disk right now).
+_launch_build_marker_matches() {
+  [[ -f "$BUILD_ENV_FILE" ]] || return 1
+  local recorded current
+  recorded="$(grep -m1 '^build_id=' "$BUILD_ENV_FILE" 2>/dev/null || true)"
+  current="build_id=$(cat "$BUILD_ID_FILE" 2>/dev/null || true)"
+  [[ -n "$recorded" && "$recorded" == "$current" ]]
+}
+
+# ==== BUILD LOCK (ops-hardening iter-77, closes the iter-72/c intermittent asset-less-frontend
+# defect) — serialize the staleness-check -> `next build` decision per dist-dir ===================
+# Root cause confirmed by direct code reading (this iteration's instrumentation target, per the
+# assumption-ledger's iter-77 entry): this script had NO lock against a SECOND concurrent invocation
+# targeting the SAME `$DIST_DIR`. Two overlapping invocations (e.g. an orchestration script restarting
+# the frontend while a still-running prior invocation's `next build` has not yet finished) would both
+# see the build as stale and both run `next build` concurrently against the SAME output directory —
+# `next build` is not safe for two concurrent writers into one dist dir (webpack/Next both write many
+# intermediate files throughout the build, not atomically, and there is no coordination between two
+# independent `next build` processes). Whichever invocation's build happens to finish (or appear to
+# finish) first `exec`s into `next start` and begins serving while the OTHER invocation's build may
+# still be mid-write to the exact same files — a client request landing in that window can be served a
+# torn mix of two builds' output (missing/corrupt static chunks, a manifest that does not match what is
+# actually on disk), which is exactly the asset-less/unstyled page symptom this closes.
+#
+# Fix: an exclusive `flock` keyed to the resolved dist-dir path wraps the ENTIRE staleness-check ->
+# build decision below. Whichever invocation acquires the lock first performs (or skips) its build to
+# completion before releasing it; every other concurrent invocation targeting the SAME dist dir blocks
+# until then, and its OWN staleness check (deliberately re-run AFTER acquiring the lock, not before)
+# then correctly observes a just-completed, fully-written build and skips the redundant/racing rebuild.
+# The lock is released before the final `exec ... next start` below — serving needs no cross-invocation
+# exclusivity once the build on disk is known-consistent, so a legitimate sequential restart is never
+# blocked by a stale lock hold. `TRENDORA_FRONTEND_LOCK_DIR` is a test-only seam (defaults to `/tmp`,
+# never changed in a real launch) so tests can inspect lock files without touching a shared path.
+LOCK_DIR="${TRENDORA_FRONTEND_LOCK_DIR:-/tmp}"
+mkdir -p "$LOCK_DIR"
+_dist_dir_abs="$REPO_ROOT/apps/frontend/$DIST_DIR"
+BUILD_LOCK_FILE="$LOCK_DIR/trendora-frontend-build-$(printf '%s' "$_dist_dir_abs" | sha1sum | cut -c1-16).lock"
+exec {BUILD_LOCK_FD}>"$BUILD_LOCK_FILE"
+if ! flock -n "$BUILD_LOCK_FD"; then
+  echo "[start-frontend.sh] another invocation is already building/checking '$DIST_DIR' —" \
+       "waiting for its build lock ($BUILD_LOCK_FILE) before proceeding..." >&2
+  flock "$BUILD_LOCK_FD"
+fi
+echo "[start-frontend.sh] acquired build lock for '$DIST_DIR'" >&2
+# ==== end BUILD LOCK acquisition ======================================================================
 
 _build_is_stale_or_missing() {
   # Missing entirely (never built, or a `next dev`-mode `.next` with no BUILD_ID at all) -> stale.
@@ -73,6 +196,33 @@ _build_is_stale_or_missing() {
   if [[ ! -f "$BUILD_ID_FILE" ]]; then
     return 0
   fi
+  # Built out of band (no launcher marker, or a marker for a different BUILD_ID) -> stale, whatever the
+  # source mtimes say: its baked NEXT_PUBLIC_* config is unknown and, for a bare `npx next build`,
+  # provably wrong for this project's ports (see BUILD_ENV_FILE's comment above).
+  if ! _launch_build_marker_matches; then
+    echo "[start-frontend.sh] '$DIST_DIR' was not built by this launcher (no matching build marker) —" \
+         "treating it as stale so its baked NEXT_PUBLIC_API_URL cannot silently point at the wrong backend." >&2
+    return 0
+  fi
+  # Built for a DIFFERENT backend than this launch is configured for -> stale, whatever the mtimes say
+  # (see _bundle_targets_configured_backend above). The one exception: another live server is already
+  # serving this dist dir, in which case rebuilding would tear ITS assets mid-flight — the exact harm
+  # finding B2 names — so we warn loudly and serve what is there instead. (This is the audit's own
+  # "can be promoted into the gate" note on the launch marker, promoted with that safety carve-out
+  # rather than by pinning the concurrent-launch fixture to one backend port.)
+  if ! _bundle_targets_configured_backend; then
+    if _dist_dir_has_live_server; then
+      echo "[start-frontend.sh] WARNING: the build in '$DIST_DIR' does not reference this launch's" \
+           "backend ($NEXT_PUBLIC_API_URL), but another live server is serving that directory —" \
+           "serving it as-is rather than tearing that server's assets. Pages may show 'Backend" \
+           "unavailable'; stop the other server and relaunch to rebuild." >&2
+    else
+      echo "[start-frontend.sh] '$DIST_DIR' was built for a different backend (no reference to" \
+           "$NEXT_PUBLIC_API_URL in its emitted bundles) — treating it as stale so the served app can" \
+           "actually reach this launch's backend." >&2
+      return 0
+    fi
+  fi
   # Otherwise stale iff any real source file (excluding node_modules/ and the dist dir itself) is
   # newer than the build marker — covers apps/frontend's tracked sources plus package.json/
   # package-lock.json, since none of those live under the excluded paths.
@@ -85,14 +235,32 @@ _build_is_stale_or_missing() {
 
 if _build_is_stale_or_missing; then
   echo "[start-frontend.sh] '$DIST_DIR' build missing or stale relative to sources — running 'next build'..." >&2
-  if ! "${HOST_GUARD_CMD_PREFIX[@]}" npx next build; then
+  # TRENDORA_LAUNCH_BUILD tells next.config.mjs's build guard that THIS build is the launcher's own: it
+  # holds the per-dist-dir build lock, exports NEXT_PUBLIC_API_URL/_PORT (above), and is the process that
+  # will serve the result. Every other `next build` targeting a live-served dist dir is refused there.
+  if ! TRENDORA_LAUNCH_BUILD=1 "${HOST_GUARD_CMD_PREFIX[@]}" npx next build; then
     echo "[start-frontend.sh] next build FAILED (see output above) — refusing to fall back to" \
          "'next dev' or serve a stale build." >&2
+    flock -u "$BUILD_LOCK_FD"
     exit 1
   fi
+  # Record that THIS launcher produced the build now on disk (see BUILD_ENV_FILE above). Written under
+  # the build lock, after a successful build, so a concurrent invocation's post-lock staleness re-check
+  # observes a fully-written build AND its marker together.
+  _write_launch_build_marker
 else
   echo "[start-frontend.sh] existing '$DIST_DIR' build is current relative to sources — skipping rebuild." >&2
 fi
+
+# Claim the dist dir as SERVED by this process (pid survives the `exec` below) BEFORE releasing the
+# build lock — a concurrent invocation that acquires the lock next then reliably observes the claim
+# instead of racing it. See SERVING_MARKER_FILE above.
+_write_serving_marker
+
+# Release the build lock — the dist dir is now known-consistent on disk; serving it needs no
+# cross-invocation exclusivity (see the lock-acquisition comment above).
+flock -u "$BUILD_LOCK_FD"
+exec {BUILD_LOCK_FD}>&-
 # ==== end build-if-stale =============================================================================
 
 exec "${HOST_GUARD_CMD_PREFIX[@]}" npx next start -p "$FRONTEND_PORT"
diff --git a/apps/frontend/lib/staleness-annotation.test.ts b/apps/frontend/lib/staleness-annotation.test.ts
new file mode 100644
index 00000000..1611d338
--- /dev/null
+++ b/apps/frontend/lib/staleness-annotation.test.ts
@@ -0,0 +1,61 @@
+/**
+ * Unit tests for the J-04/J-07 readiness-badge/preflight-banner staleness annotation formatter
+ * (lib/staleness-annotation.ts). No test framework is installed in this frontend; these run under
+ * Node's native TS type-stripping:
+ *   node lib/staleness-annotation.test.ts
+ * (per the project's documented dev-box limitation, `node lib/*.test.ts` may not execute on every Node
+ * build locally -- see docs/handoffs/*iter-49-dev.md; these run in the CI/QA Node environment either
+ * way, same as every other `lib/*.test.ts` file here.)
+ *
+ * TC-3/TC-4 (ops-hardening iter-77): `stale_for_s > 0` renders the annotation, `stale_for_s === 0`
+ * (fresh/synchronous) renders none, and a failed-poll `null` renders none -- never a stale or
+ * fabricated number.
+ */
+import assert from "node:assert";
+
+import { formatStaleAnnotation } from "./staleness-annotation.ts";
+
+let passed = 0;
+function check(name: string, fn: () => void) {
+  fn();
+  passed += 1;
+  console.log(`  ok - ${name}`);
+}
+
+check("stale_for_s > 0 renders 'as of Ns ago', rounded to the nearest second", () => {
+  assert.strictEqual(formatStaleAnnotation(12.4), "as of 12s ago");
+  assert.strictEqual(formatStaleAnnotation(0.6), "as of 1s ago");
+});
+
+check("sub-second staleness reads 'as of <1s ago', never the self-contradictory 'as of 0s ago'", () => {
+  // The steady state with `readiness.refresh_interval_seconds: 0.5` -- most live samples land here
+  // (audit finding F1). The annotation must stay visible (the payload IS stale) and stay truthful.
+  assert.strictEqual(formatStaleAnnotation(0.053), "as of <1s ago");
+  assert.strictEqual(formatStaleAnnotation(0.128), "as of <1s ago");
+  assert.strictEqual(formatStaleAnnotation(0.499), "as of <1s ago");
+  // The rounding boundary: >= 0.5 rounds up to a real second, so it keeps the numeric form.
+  assert.strictEqual(formatStaleAnnotation(0.505), "as of 1s ago");
+});
+
+check("stale_for_s === 0 (fresh/synchronous compute) renders no annotation", () => {
+  assert.strictEqual(formatStaleAnnotation(0), null);
+});
+
+check("stale_for_s === null (before first poll / failed poll) renders no annotation", () => {
+  assert.strictEqual(formatStaleAnnotation(null), null);
+});
+
+check("a negative value never renders a fabricated annotation (defensive, unexpected payload shape)", () => {
+  assert.strictEqual(formatStaleAnnotation(-3), null);
+});
+
+check("a non-finite value (NaN/Infinity) never renders a fabricated annotation", () => {
+  assert.strictEqual(formatStaleAnnotation(Number.NaN), null);
+  assert.strictEqual(formatStaleAnnotation(Number.POSITIVE_INFINITY), null);
+});
+
+check("a large staleness value still renders honestly (no cap/clamp hiding real age)", () => {
+  assert.strictEqual(formatStaleAnnotation(482.9), "as of 483s ago");
+});
+
+console.log(`${passed} passed`);
diff --git a/apps/frontend/lib/staleness-annotation.ts b/apps/frontend/lib/staleness-annotation.ts
new file mode 100644
index 00000000..6c7d8e3d
--- /dev/null
+++ b/apps/frontend/lib/staleness-annotation.ts
@@ -0,0 +1,23 @@
+/**
+ * Pure formatter for the readiness badge / preflight banner's "as of {N}s ago" staleness annotation
+ * (ops-hardening iter-77, J-04/J-07 disclosure) -- the FIRST UI consumer of `GET /api/health`'s
+ * `stale_for_s` field (served since iter-71, never rendered until now). Re-formats the server value
+ * ONLY -- no computation. Renders nothing (null) for a fresh/synchronous compute (`stale_for_s === 0`,
+ * per the spec's "no annotation for a synchronous/fresh compute" acceptance) and, defensively, for any
+ * non-finite/negative value, so a caller can never accidentally render a fabricated "as of 0s ago" or
+ * "as of NaNs ago" from an unexpected payload shape. `staleForS === null` (before the first poll
+ * resolves, or on a failed poll -- `useReadiness()`'s own honest-failure convention) also renders
+ * nothing -- callers must never show a stale or fabricated number when the backend is unreachable.
+ */
+export function formatStaleAnnotation(staleForS: number | null): string | null {
+  if (staleForS === null || !Number.isFinite(staleForS) || staleForS <= 0) return null;
+  const seconds = Math.round(staleForS);
+  // Sub-second staleness is the STEADY STATE here, not an edge case: the readiness cache refreshes
+  // every `readiness.refresh_interval_seconds` (0.5s), so a live sample of the served field reads e.g.
+  // 0.053 / 0.128 / 0.505 -- roughly 11 of 15 values round to zero (measured, ops-hardening iter-77
+  // audit finding F1). Rounding those to "as of 0s ago" printed a self-contradictory annotation ("it is
+  // stale... by no time at all") on almost every render. Say what is actually true instead -- the
+  // payload IS stale, by less than a second -- so the disclosure never reads as nonsense and never
+  // disappears while real staleness exists.
+  return seconds < 1 ? "as of <1s ago" : `as of ${seconds}s ago`;
+}
```
