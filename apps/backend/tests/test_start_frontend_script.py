"""Script-level checks for `scripts/start-frontend.sh` (ops-hardening iter-33, the J-06 unblocker): two
consecutive evaluators (iter-31, iter-32) named this script's `next dev` fallback as the top blocker for
J-06's real-browser TTI sweep — a dev-mode sweep measures on-demand per-route compilation, not real
production page-load time. This iteration rewrote the launcher to build-if-stale then `exec next start`,
never falling back to `next dev` or serving a stale build. There is nothing to mock here: the assertions
are about a REAL LAUNCHED PROCESS's actual build output / listening socket / environment, so this spawns
the real script as a subprocess against the real repo checkout, on an isolated test-only port range so it
never collides with an already-running dev/QA frontend on this machine (or with
`test_start_backend_script.py`'s own 18000-19999 port range).

TC-1 (missing/stale build -> `next build` runs, then a real `next start` process is bound to the
configured port), TC-2 (an existing, current build -> the rebuild is skipped, `next start` execs
directly), TC-3 (a deliberately broken `apps/frontend` source file -> the script exits non-zero, the
build's own error output is captured, and no stray process is left listening on the port afterward).

Design notes (verified by direct inspection this session, not assumed):

- **Process-ancestry cmdline, not `/proc/<pid>/environ`, is the dev/prod signal.** The process actually
  bound to the listening socket is a further-forked "next-server (vX.Y.Z)" worker in BOTH `next dev` and
  `next start` (Next.js labels it identically via `process.title` either way), so cmdline text on THAT
  pid alone cannot distinguish them. `NODE_ENV` was also tried and REJECTED: although
  `node_modules/next/dist/bin/next`'s `preAction` hook does set
  `process.env.NODE_ENV = NODE_ENV || (commandName === 'dev' ? 'development' : 'production')`, a direct
  live probe this session showed that mutation is NOT visible via `/proc/<pid>/environ` on EITHER the
  wrapper process or the forked worker (both show no `NODE_ENV` key at all) -- `/proc/<pid>/environ`
  reflects the environment at `execve()` time, not later in-process `process.env` writes. The reliable
  signal, confirmed by direct inspection of the real process tree this session, is the worker's PARENT
  process: `next start`'s "sh -c next start -p PORT" (and `next dev`'s equivalent "sh -c next dev -p
  PORT") literally contains the subcommand as a cmdline argument. `_resolve_dev_or_start` below walks up
  the process ancestry from the listening-socket PID (found the same "resolve via the socket, not a
  launching-shell PID guess" way as `test_start_backend_script.py::_owning_pid`) until it finds an
  ancestor whose cmdline names the subcommand.
- **Scratch build directories are relative names directly under `apps/frontend`, never an absolute
  `tmp_path`.** `next.config.mjs` resolves `NEXT_DIST_DIR` via Node's `path.join(projectDir, distDir)`,
  which does NOT treat a leading `/` in `distDir` as "reset to filesystem root" (confirmed empirically:
  `path.join('/a/b', '/tmp/x')` -> `/a/b/tmp/x`) — passing pytest's own absolute `tmp_path` would build
  into an unintended NESTED directory under `apps/frontend`, not the scratch location the test believes
  it is inspecting. Every scratch dir here is therefore a short relative name (mirroring this project's
  own pre-existing `.next-alt-qa` / `.next-verify` convention), created and `shutil.rmtree`'d directly
  under `apps/frontend`.
- **A real `next build` against a distDir name it has not seen before REWRITES the committed
  `apps/frontend/tsconfig.json`** (Next auto-appends `<distDir>/types/**/*.ts` to `compilerOptions`'s
  `include` list, confirmed by direct observation this session — this is also why the two pre-existing
  entries `.next-alt-qa`/`.next-verify` are already present in this repo's committed tsconfig.json from
  earlier iterations' own scratch builds). An autouse fixture below snapshots and restores
  `tsconfig.json` around every test in this module so these test-only scratch names never leak into the
  committed file — content AND mtime, since `start-frontend.sh`'s staleness check compares source mtimes
  against `BUILD_ID` and a content-identical rewrite would otherwise invalidate the real `.next` build.
- **All cleanup is FIXTURE teardown, and the same cleanup also runs at fixture SETUP.** A previous run of
  this module was hard-killed mid-build (pytest SIGKILLed -> no `finally` block, no teardown runs at all),
  which left `__tc3_intentionally_broken.ts` and several `.next-test-*` directories in the real source
  tree; the next run then failed TC-3 on its own "refusing to overwrite" guard, and a stray broken `.ts`
  in the tree would have failed the next production build. In-test `finally` blocks cannot survive a
  SIGKILL, so the module additionally SELF-HEALS: `_purge_test_residue()` runs on the way IN as well as on
  the way OUT, and the launcher subprocess is owned by a fixture (killed in ITS teardown) rather than by
  an end-of-test statement, so a failure anywhere in a test body can never leave a process behind.
- **The build timeout is generous and host-overridable.** A cold scratch-dir `next build` (no webpack
  cache to reuse) on this host-guard-CPU-masked box measured ~1 minute idle but >5 minutes while the live
  QA backend/frontend were running — the previous 300 s ceiling turned ordinary contention into three
  spurious failures. `TRENDORA_FRONTEND_BUILD_TIMEOUT_S` raises/lowers it per host. The waits also fail
  FAST (with the launcher's own log tail) when the launcher process has already exited, instead of
  burning the whole ceiling polling a port nothing will ever bind.
"""
from __future__ import annotations

import json
import os
import random
import re
import shutil
import signal
import string
import subprocess
import time
from pathlib import Path

import httpx
import pytest

# apps/backend/tests/test_start_frontend_script.py -> tests -> backend -> apps -> <repo root>
REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "start-frontend.sh"
FRONTEND_DIR = REPO_ROOT / "apps" / "frontend"
TSCONFIG = FRONTEND_DIR / "tsconfig.json"

# A deterministic-but-distinct port range, well clear of `test_start_backend_script.py`'s 18000-19999
# range and this project's real deterministic offset ports (3000+offset / 8000+offset), so these tests
# never collide with an already-running dev/QA instance or with that other test module's own spawns.
_offset = int(__import__("hashlib").sha1(str(REPO_ROOT).encode()).hexdigest()[:4], 16) % 1000
_TC1_PORT = 21000 + _offset
_TC2_PORT = 21100 + _offset
_TC3_PORT = 21200 + _offset
# ops-hardening iter-77: distinct port ranges for the goal-spec's OWN "TC-1"/"TC-2" (the intermittent
# asset-less-frontend defect, iter-72/c) -- not to be confused with this module's pre-existing
# iter-33-era TC-1 ("test_missing_build_triggers_build_then_next_start")/TC-2
# ("test_current_build_skips_rebuild") above, which are about a DIFFERENT thing (the build/skip-rebuild
# branch taken by a single invocation). 21400/21500 are clear of every range already claimed above.
_TC1_77_PORT = 21400 + _offset
_TC2_77_PORT = 21500 + _offset
# ops-hardening iter-77 AUDIT: the out-of-band-build regression test's own range (21600), clear of
# every range claimed above.
_TC3_77_PORT = 21600 + _offset
# ops-hardening iter-77 AUDIT FIX ROUND 2: the build-guard (21700) and backend-retarget (21800) tests.
_TC4_77_PORT = 21700 + _offset
_TC5_77_PORT = 21800 + _offset
# ops-hardening iter-78: the launcher's own residue-purge regression test's range (21900), clear of
# every range claimed above.
_TC6_78_PORT = 21900 + _offset
# ops-hardening iter-78 AUDIT FIX (finding B1): the live-server-aware purge test's range (22000),
# clear of every range claimed above.
_TC7_78_PORT = 22000 + _offset

# A cold scratch-dir `next build` (a distDir name Next has never seen -> no webpack cache to reuse) on
# this host-guard-CPU-masked host measured ~1 minute with the box idle, but blew past 300 s while the live
# QA backend + frontend were running -- which is exactly how the previous run turned ordinary contention
# into three spurious failures. The ceiling is therefore generous by default and overridable per host, in
# the same accepted-cost category as this project's other slow real-process tests (per the execution
# plan's own Testing Notes).
_BUILD_TIMEOUT_S = float(os.environ.get("TRENDORA_FRONTEND_BUILD_TIMEOUT_S", "900"))
# Booting `next start` against an ALREADY-built dist dir needs no compile at all ("Ready in 266ms"
# observed); this bounds only that no-build path, so TC-2's skip-rebuild proof stays a genuinely fast
# assertion rather than silently passing on a rebuild it was supposed to catch.
_START_TIMEOUT_S = float(os.environ.get("TRENDORA_FRONTEND_START_TIMEOUT_S", "120"))

_BROKEN_SOURCE_REL = "__tc3_intentionally_broken.ts"
_SCRATCH_DIST_GLOB = ".next-test-*"
# ops-hardening iter-78: `_BROKEN_SOURCE_REL` above is now ALSO the exact name
# `scripts/start-frontend.sh` reserves for its own residue purge (kept in lockstep by hand --
# see that script's "TEST-RESIDUE PURGE" block) -- a real launcher invocation now unconditionally
# DELETES that filename before building, so it can no longer be used to prove "a genuinely broken
# source file makes `next build` fail" (the purge would silently remove it first). TC-3 below uses
# this SEPARATE name instead -- still a throwaway `.ts` file cleaned by the same
# `_purge_test_residue()` self-heal, but deliberately outside the launcher's own reserved/purged set.
_BROKEN_BUILD_SOURCE_REL = "__tc3_broken_build_source.ts"


def _scratch_dist_name(tag: str) -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f".next-test-{tag}-{suffix}"


def _purge_test_residue() -> None:
    """Remove EVERY artefact this module can write into the real `apps/frontend` source tree: the TC-3
    throwaway broken source file and any `.next-test-*` scratch build directory. Deliberately keyed to
    this module's own naming (never a broad wildcard), so it can never touch the real `.next` or the
    repo's pre-existing `.next-alt-qa`/`.next-verify` dirs. Called on fixture SETUP as well as teardown --
    see the module docstring: a SIGKILLed pytest runs no teardown, so the next run must self-heal rather
    than fail on residue it did not create."""
    for name in (_BROKEN_SOURCE_REL, _BROKEN_BUILD_SOURCE_REL):
        broken = FRONTEND_DIR / name
        if broken.exists():
            broken.unlink()
    for scratch in FRONTEND_DIR.glob(_SCRATCH_DIST_GLOB):
        shutil.rmtree(scratch, ignore_errors=True)


def _scrub_tsconfig_scratch_entries() -> None:
    """Belt-and-braces for the byte-snapshot restore below: surgically strip any leaked `.next-test-*`
    scratch-dist `include` entries from the committed `tsconfig.json`, independent of the byte-snapshot
    restore. Observed once (1 of ~4 full-module runs, on a host also busy with an unrelated project's
    processes): a killed `next build`'s TypeScript-checker write can land between this fixture's `before`
    snapshot and its restore write, so a pure "restore to the instant-captured snapshot" can race. This
    scrub is idempotent and order-independent -- it does not depend on catching every write at exactly the
    right instant, only on recognising this module's own naming (`_SCRATCH_DIST_GLOB`) in `include` and
    dropping it. A no-op (no file write at all) whenever nothing needs stripping, so the common clean case
    never risks reformatting the file."""
    if not TSCONFIG.exists():
        return
    try:
        data = json.loads(TSCONFIG.read_text())
    except (OSError, ValueError):
        return
    include = data.get("include")
    if not isinstance(include, list):
        return
    cleaned = [e for e in include if not (isinstance(e, str) and e.startswith(".next-test-"))]
    if cleaned != include:
        data["include"] = cleaned
        TSCONFIG.write_text(json.dumps(data, indent=2) + "\n")


@pytest.fixture(autouse=True)
def _pristine_frontend_tree():
    """Guarantee this module never leaves the real `apps/frontend` tree modified, and never inherits
    residue from a hard-killed previous run.

    Setup: purge this module's own residue (see `_purge_test_residue`), then scrub any scratch `include`
    entry a previous run's race (see `_scrub_tsconfig_scratch_entries`) left behind, so this test's own
    `before` snapshot is always captured on an already-clean file.
    Teardown: purge again, restore `tsconfig.json` byte-for-byte AND to its original mtime -- a real
    `next build` against a new distDir name rewrites that file (module docstring), and even a
    content-restoring rewrite would bump its mtime, which `start-frontend.sh`'s staleness check reads as
    "sources changed" and would trigger one gratuitous rebuild of the real `.next` afterwards -- then scrub
    once more as a final safety net in case a race (see above) landed a write after the byte-restore."""
    _purge_test_residue()
    _scrub_tsconfig_scratch_entries()
    before = TSCONFIG.read_bytes() if TSCONFIG.exists() else None
    before_mtime_ns = TSCONFIG.stat().st_mtime_ns if TSCONFIG.exists() else None
    try:
        yield
    finally:
        _purge_test_residue()
        if before is not None:
            if TSCONFIG.read_bytes() != before:
                TSCONFIG.write_bytes(before)
            os.utime(TSCONFIG, ns=(before_mtime_ns, before_mtime_ns))
        _scrub_tsconfig_scratch_entries()


def _owning_pid(port: int, timeout: float = 30.0) -> int:
    """The PID actually bound to `port`'s listening socket (mirrors
    `test_start_backend_script.py::_owning_pid` exactly: `next start`, like `next dev`, forks a further
    "next-server" worker, so the launching shell's own PID is not reliably the one holding the socket)."""
    deadline = time.monotonic() + timeout
    ss_pattern = re.compile(rf":{port}\s.*pid=(\d+)")
    while True:
        out = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=5)
        pids = [int(p) for p in out.stdout.split() if p.strip()]
        if pids:
            return pids[0]
        ss_out = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True, timeout=5)
        for line in ss_out.stdout.splitlines():
            m = ss_pattern.search(line)
            if m:
                return int(m.group(1))
        if time.monotonic() >= deadline:
            raise AssertionError(
                f"no process found listening on :{port} (lsof and `ss -tlnp` both empty) within {timeout}s"
            )
        time.sleep(0.5)


def _log_tail(log_path: Path, limit: int = 4000) -> str:
    try:
        return log_path.read_text(errors="replace")[-limit:]
    except OSError:
        return "(launcher log unreadable)"


def _wait_for_port_answering(
    port: int, timeout: float, proc: "subprocess.Popen | None" = None, log_path: "Path | None" = None
) -> None:
    """Wait until ANY HTTP response comes back from `port` -- proof something is bound and serving.

    Fails FAST (with the launcher's own log tail) the moment the launcher process exits without binding:
    once `start-frontend.sh` is gone nothing will ever answer, so polling out the full build ceiling would
    only turn a clear "the build failed, here is its error" into an opaque timeout."""
    deadline = time.monotonic() + timeout
    last_exc: Exception | None = None
    while time.monotonic() < deadline:
        try:
            httpx.get(f"http://127.0.0.1:{port}/", timeout=3.0)
            return
        except Exception as exc:  # noqa: BLE001 -- keep polling until the deadline
            last_exc = exc
        if proc is not None and proc.poll() is not None:
            tail = _log_tail(log_path) if log_path is not None else "(no log captured)"
            raise AssertionError(
                f"start-frontend.sh exited with rc={proc.returncode} without ever binding :{port}. "
                f"Launcher log tail:\n{tail}"
            )
        time.sleep(0.5)
    tail = _log_tail(log_path) if log_path is not None else "(no log captured)"
    raise AssertionError(
        f"nothing answered on :{port} within {timeout}s (last error: {last_exc}). "
        f"If the build simply needs longer on this host, raise TRENDORA_FRONTEND_BUILD_TIMEOUT_S. "
        f"Launcher log tail:\n{tail}"
    )


_ASSET_HREF_RE = re.compile(r'(?:href|src)="(/_next/static/[^"]+)"')


def _assert_page_fully_styled(port: int, timeout: float = 30.0) -> None:
    """Fetch `/` and at least one of its OWN referenced `/_next/static/...` build assets, asserting BOTH
    return HTTP 200 with a non-empty body. The concrete 'asset-less' failure this closes (iter-72/c) would
    serve the HTML shell fine (200) while a stylesheet/script chunk 404s or comes back truncated -- a torn
    build served mid-write by a racing `next build`. Mirrors this iteration's own TC-1 wording ('CSS/asset
    requests return 200; no bare "Checking backend..." shell')."""
    resp = httpx.get(f"http://127.0.0.1:{port}/", timeout=timeout)
    assert resp.status_code == 200, f"GET / -> HTTP {resp.status_code}"
    html = resp.text
    assets = _ASSET_HREF_RE.findall(html)
    assert assets, f"expected >=1 /_next/static/... asset reference in the served HTML; got:\n{html[:2000]}"
    for asset_path in assets[:3]:  # a handful is enough to catch a torn/partial build
        aresp = httpx.get(f"http://127.0.0.1:{port}{asset_path}", timeout=timeout)
        assert aresp.status_code == 200, f"GET {asset_path} -> HTTP {aresp.status_code} (asset-less page)"
        assert len(aresp.content) > 0, f"GET {asset_path} returned an empty body (asset-less page)"


def _parent_pid(pid: int) -> "int | None":
    out = subprocess.run(["ps", "-o", "ppid=", "-p", str(pid)], capture_output=True, text=True, timeout=5)
    txt = out.stdout.strip()
    return int(txt) if txt.isdigit() else None


def _cmdline(pid: int) -> str:
    with open(f"/proc/{pid}/cmdline", "rb") as fh:
        raw = fh.read()
    return " ".join(a for a in raw.decode(errors="replace").split("\x00") if a)


def _resolve_dev_or_start(owning_pid: int, max_depth: int = 6) -> str:
    """Walk up the process ancestry from the listening-socket PID until an ancestor's cmdline literally
    names the `next` subcommand (`dev` or `start`) -- see module docstring for why this, not
    `/proc/<pid>/environ`'s `NODE_ENV`, is the reliable signal. Returns 'dev' or 'start'."""
    pid = owning_pid
    for _ in range(max_depth):
        try:
            joined = _cmdline(pid)
        except FileNotFoundError:
            break
        if re.search(r"\bnext\b.*\bstart\b", joined):
            return "start"
        if re.search(r"\bnext\b.*\bdev\b", joined):
            return "dev"
        ppid = _parent_pid(pid)
        if ppid is None or ppid <= 1:
            break
        pid = ppid
    raise AssertionError(
        f"could not resolve 'next dev' vs 'next start' from process ancestry starting at pid {owning_pid} "
        f"(cmdline: {_cmdline(owning_pid)!r})"
    )


def _spawn_launcher(dist_rel: str, frontend_port: int, backend_port: int, log_path: Path):
    """Launch the real `scripts/start-frontend.sh` as a subprocess in its OWN process group (so teardown
    can kill the whole tree `next build`/`next start`/npx may have forked -- mirrors
    `test_start_backend_script.py::test_dev_script_applies_host_guard_caps_to_backend_only`'s
    `os.setsid` + `os.killpg` discipline). stdout/stderr go to a real logfile (never a pipe -- a real
    `next build`'s output is large enough to deadlock a `subprocess.PIPE` that nothing is draining)."""
    if not SCRIPT.exists():
        pytest.skip(f"{SCRIPT} not found")
    env = dict(os.environ)
    env["CHAIN_FRONTEND_PORT"] = str(frontend_port)
    env["CHAIN_BACKEND_PORT"] = str(backend_port)
    env["NEXT_DIST_DIR"] = dist_rel
    log_fh = open(log_path, "wb")
    proc = subprocess.Popen(
        ["bash", str(SCRIPT)],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
    )
    return proc, log_fh


def _kill_process_group(proc: subprocess.Popen, log_fh) -> None:
    """SIGTERM then SIGKILL the whole process group, wait for it to actually be gone, then close the
    logfile handle. Never leaves a stray `next build`/`next start` process running (mirrors
    `test_start_backend_script.py`'s `finally`-block SIGKILL + reap discipline)."""
    try:
        pgid = os.getpgid(proc.pid)
    except ProcessLookupError:
        pgid = None
    if pgid is not None:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(pgid, sig)
            except ProcessLookupError:
                break
            deadline = time.monotonic() + 10.0
            gone = False
            while time.monotonic() < deadline:
                try:
                    os.killpg(pgid, 0)
                except ProcessLookupError:
                    gone = True
                    break
                time.sleep(0.2)
            if gone:
                break
    try:
        proc.wait(timeout=10)
    except (ChildProcessError, subprocess.TimeoutExpired):
        pass
    try:
        log_fh.close()
    except Exception:  # noqa: BLE001 -- best-effort close, never masks a real test failure
        pass


class _Launcher:
    """One launched `start-frontend.sh`: its process, its own logfile, and the scratch dist dir it was
    pointed at. Returned by the `launcher` fixture, which OWNS the teardown kill; `stop()` exists only for
    the one test that must sequence two invocations against the same dist dir, and is idempotent so the
    fixture's own teardown can always run it again safely."""

    def __init__(self, proc: subprocess.Popen, log_path: Path, log_fh, dist_abs: Path):
        self.proc = proc
        self.log_path = log_path
        self.log_fh = log_fh
        self.dist_abs = dist_abs

    def log_text(self) -> str:
        return self.log_path.read_text(errors="replace")

    def stop(self) -> None:
        _kill_process_group(self.proc, self.log_fh)


@pytest.fixture
def launcher(tmp_path):
    """Spawn `scripts/start-frontend.sh` and guarantee the whole process group is killed in FIXTURE
    TEARDOWN -- not in an end-of-test statement. A failed assertion (or an error raised anywhere in the
    test body, including before the body's own try block) can therefore never leave a `next build` or
    `next start` alive on a shared port. Teardown runs before the autouse `_pristine_frontend_tree`
    fixture's own purge (pytest finalises in reverse setup order), so the scratch dist dirs are removed
    only once nothing is still writing to them."""
    spawned: list[_Launcher] = []

    def _launch(dist_rel: str, frontend_port: int, backend_port: int, log_name: str) -> _Launcher:
        log_path = tmp_path / log_name
        proc, log_fh = _spawn_launcher(dist_rel, frontend_port, backend_port, log_path)
        launched = _Launcher(proc, log_path, log_fh, FRONTEND_DIR / dist_rel)
        spawned.append(launched)
        return launched

    try:
        yield _launch
    finally:
        for launched in reversed(spawned):
            launched.stop()


def test_scrub_tsconfig_scratch_entries_removes_only_scratch_dist_entries():
    """Guards `_scrub_tsconfig_scratch_entries` (the fixture's belt-and-braces scrub, added after a leaked
    `.next-test-tc2-<random>` entry was observed to survive one full-module run out of ~4 on a host also
    busy with an unrelated project's processes -- see that function's docstring). Fast and deterministic:
    no real build, no subprocess. It must strip ONLY entries matching this module's own scratch-dist
    naming, leave every legitimate entry (including the repo's real pre-existing `.next-alt-qa` /
    `.next-verify` / `.next` entries) untouched and in order, and be a true no-op -- no write, no mtime
    bump -- once the file is already clean."""
    original = json.loads(TSCONFIG.read_text())
    polluted = json.loads(TSCONFIG.read_text())
    polluted["include"] = [*polluted["include"], ".next-test-tc2-deadbeef/types/**/*.ts"]
    TSCONFIG.write_text(json.dumps(polluted, indent=2) + "\n")

    _scrub_tsconfig_scratch_entries()

    after = json.loads(TSCONFIG.read_text())
    assert after["include"] == original["include"], (
        "expected the scratch entry to be stripped and every legitimate include entry preserved in order"
    )

    mtime_before = TSCONFIG.stat().st_mtime_ns
    _scrub_tsconfig_scratch_entries()
    assert TSCONFIG.stat().st_mtime_ns == mtime_before, "scrub must be a no-op once nothing needs stripping"


def test_missing_build_triggers_build_then_next_start(launcher):
    """TC-1 -- a brand-new scratch NEXT_DIST_DIR (never built) is missing entirely, so
    `start-frontend.sh` must run `next build` before `next start`. Verified: the script's own log shows
    the "running 'next build'" branch was taken; the build actually produced a BUILD_ID; and the process
    resolved via the LISTENING SOCKET (not a launching-shell PID guess) ancestrally resolves to `start`,
    never `dev` (see module docstring for why this, not `NODE_ENV`, is the reliable signal)."""
    if not (FRONTEND_DIR / "node_modules").exists():
        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")
    dist_rel = _scratch_dist_name("tc1")
    assert not (FRONTEND_DIR / dist_rel).exists(), "the scratch dist dir must not exist before launching"
    launched = launcher(dist_rel, _TC1_PORT, _TC1_PORT + 1000, "tc1.log")

    _wait_for_port_answering(
        _TC1_PORT, timeout=_BUILD_TIMEOUT_S, proc=launched.proc, log_path=launched.log_path
    )
    assert (launched.dist_abs / "BUILD_ID").exists(), "expected `next build` to have produced a BUILD_ID"

    pid = _owning_pid(_TC1_PORT)
    mode = _resolve_dev_or_start(pid)
    assert mode == "start", (
        f"expected the process bound to :{_TC1_PORT} to resolve (via its process ancestry) to a "
        f"real `next start` (prod), got {mode!r}"
    )

    log_text = launched.log_text()
    assert "running 'next build'" in log_text, (
        f"expected the script's own missing-build log line; got:\n{log_text[-4000:]}"
    )


def test_current_build_skips_rebuild(launcher):
    """TC-2 -- an existing, CURRENT build (produced by a PRIOR run of this SAME launcher; sources
    unchanged since) -> a second `start-frontend.sh` invocation skips the rebuild and execs `next start`
    directly.

    Both invocations here go through the LAUNCHER itself (never a raw `next build` as the "setup" step).
    A raw `next build` against a brand-new distDir name rewrites `tsconfig.json` (see module docstring)
    with a write that can land AFTER `BUILD_ID`'s own write within that SAME build -- which would make the
    very NEXT staleness check see `tsconfig.json` (a real tracked source file, correctly in scope for the
    staleness scan) as newer than `BUILD_ID` and trigger one incorrect rebuild. This is a genuine one-time
    edge case confirmed by direct observation this session -- it is harmless for the real default `.next`
    dir (already present in the committed `tsconfig.json` from a past iteration's own scratch build, so
    real steady-state restarts never hit it), but a fresh scratch distDir name hits it on its FIRST ever
    build. Running the first invocation through the launcher (rather than a bare `next build`) means that
    one-time settling happens during invocation 1, so invocation 2's check is a true skip-rebuild proof --
    which is also a more faithful reading of the spec's own wording ("an existing, current build...";
    TC-2 is about repeat launcher invocations, not a launcher invocation following an out-of-band build).
    """
    if not (FRONTEND_DIR / "node_modules").exists():
        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")

    dist_rel = _scratch_dist_name("tc2")
    build_id = FRONTEND_DIR / dist_rel / "BUILD_ID"

    first = launcher(dist_rel, _TC2_PORT, _TC2_PORT + 1000, "tc2-first.log")
    _wait_for_port_answering(
        _TC2_PORT, timeout=_BUILD_TIMEOUT_S, proc=first.proc, log_path=first.log_path
    )
    assert build_id.exists(), "expected the first invocation's own `next build` to produce a BUILD_ID"
    # Stop invocation 1 before invocation 2 starts (the fixture would otherwise only reap it at teardown);
    # the fixture's own teardown kill is idempotent, so this is a sequencing step, not the cleanup itself.
    first.stop()

    mtime_before = build_id.stat().st_mtime_ns

    # The second invocation runs on a different FRONTEND port (the first server is stopped, but a fresh
    # port keeps the two launches trivially independent) and the SAME BACKEND port. The backend port has
    # to match for this scenario to be the one TC-2 describes -- "an existing, current build ... sources
    # unchanged": Next inlines NEXT_PUBLIC_API_URL into the bundle at BUILD time, so pointing the second
    # launch at a DIFFERENT backend makes the build on disk genuinely out of date for that launch, and
    # `start-frontend.sh` now (ops-hardening iter-77 audit fix round 2) rebuilds instead of serving an app
    # that cannot reach its configured backend -- covered by
    # `test_launcher_rebuilds_a_bundle_built_for_a_different_backend`. Before that check existed, this test
    # passed while silently exercising exactly the "served build points at the wrong backend" state that
    # broke iter-77.
    second = launcher(dist_rel, _TC2_PORT + 1, _TC2_PORT + 1000, "tc2-second.log")
    _wait_for_port_answering(  # no build needed on this path -> a short ceiling is the point of TC-2
        _TC2_PORT + 1, timeout=_START_TIMEOUT_S, proc=second.proc, log_path=second.log_path
    )

    assert build_id.stat().st_mtime_ns == mtime_before, (
        "BUILD_ID was rewritten -- a rebuild ran even though the existing build was current"
    )

    log_text = second.log_text()
    assert "skipping rebuild" in log_text, (
        f"expected the script's own skip-rebuild log line; got:\n{log_text[-4000:]}"
    )

    pid = _owning_pid(_TC2_PORT + 1)
    mode = _resolve_dev_or_start(pid)
    assert mode == "start", f"expected the skip-rebuild path to still be `next start`, got {mode!r}"


def test_broken_source_fails_build_and_leaves_no_stray_process(launcher):
    """TC-3 -- a deliberately broken `apps/frontend` source file makes the real `next build` fail (Next's
    prod build type-checks the WHOLE project, unlike `next dev`). The launcher must exit non-zero, its
    log must contain the build's own error output (never just a swallowed failure), and no stray
    `next dev`/`next start`/stale-build process may be left listening on the port. The broken file is a
    brand-new throwaway `.ts` file (never a mutated existing file), so restoring the real tree on ANY
    outcome -- including a failed assertion, an unexpected exception, or an interrupted run -- is a single
    unconditional delete, performed by the autouse `_pristine_frontend_tree` fixture's teardown (and again
    at the NEXT run's setup, since a SIGKILLed pytest runs no teardown at all -- exactly how a previous
    run left this file behind and made this test fail on its own guard assertion).

    ops-hardening iter-78: uses `_BROKEN_BUILD_SOURCE_REL`, NOT `_BROKEN_SOURCE_REL` -- the launcher now
    unconditionally purges `_BROKEN_SOURCE_REL` as reserved test-residue (see
    `test_launcher_purges_leftover_test_residue_from_a_different_process` below) before it ever runs
    `next build`, so that name can no longer be used to prove a genuine build failure propagates; this
    test needs a name the purge does NOT touch."""
    if not (FRONTEND_DIR / "node_modules").exists():
        pytest.skip("apps/frontend/node_modules not installed -- cannot build the frontend")

    dist_rel = _scratch_dist_name("tc3")
    broken_file = FRONTEND_DIR / _BROKEN_BUILD_SOURCE_REL
    assert not broken_file.exists(), f"{broken_file} already exists -- refusing to overwrite"
    broken_file.write_text(
        "// Deliberately invalid TypeScript -- ops-hardening iter-33 TC-3 smoke test.\n"
        "// Removed by the autouse `_pristine_frontend_tree` fixture regardless of outcome.\n"
        "const __trendora_test_tc3_broken__: string = 12345;\n"
    )

    launched = launcher(dist_rel, _TC3_PORT, _TC3_PORT + 1000, "tc3.log")
    rc = launched.proc.wait(timeout=_BUILD_TIMEOUT_S)
    assert rc != 0, "expected start-frontend.sh to exit non-zero on a real build failure"

    log_text = launched.log_text()
    assert "next build FAILED" in log_text, (
        f"expected the script's own failure message; got:\n{log_text[-4000:]}"
    )
    assert "__trendora_test_tc3_broken__" in log_text or "Type error" in log_text, (
        f"expected the build's OWN TypeScript error to be present (not swallowed); "
        f"got:\n{log_text[-4000:]}"
    )

    with pytest.raises(AssertionError):
        _owning_pid(_TC3_PORT, timeout=3.0)


def test_launcher_purges_leftover_test_residue_from_a_different_process(launcher):
    """ops-hardening iter-78 -- closes iter-77/c ('fixed inside the round; NOT defended against
    recurrence'): a hard-killed run of THIS test module leaves `__tc3_intentionally_broken.ts` /
    `.next-test-*` scratch dirs behind in the live `apps/frontend` tree (module docstring); this
    module's own autouse `_pristine_frontend_tree` fixture already self-heals its OWN next run, but the
    REAL launcher previously had no such defense and took the whole frontend down the moment `next
    build` type-checked the stray file (reproduced by TC-3 immediately above).

    This test proves the LAUNCHER's own defense, not this module's self-heal: the residue is written
    directly in the test BODY -- i.e. strictly AFTER the autouse fixture's own setup-purge already ran
    -- simulating "a different process wrote it and this module is not the next thing invoked" (the
    module was already clean when this test started; nothing here relies on the module's own leftover
    cleanup). It then runs the REAL `scripts/start-frontend.sh` end-to-end (never a mock) and asserts a
    clean build (rc reaching `next start`, never TC-3's failure path), a fully-styled served page, and
    that the launcher's own log records the purge -- proving the fix is in the LAUNCH SCRIPT, not merely
    this test module's pre-existing residue cleanup (which already ran before this file even existed)."""
    if not (FRONTEND_DIR / "node_modules").exists():
        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")

    dist_rel = _scratch_dist_name("residue")
    broken_file = FRONTEND_DIR / _BROKEN_SOURCE_REL
    assert not broken_file.exists(), f"{broken_file} already exists -- refusing to overwrite"
    # Written HERE, in the test body -- after the autouse `_pristine_frontend_tree` fixture's own
    # setup-purge already ran -- so this residue is provably NOT something this module's own setup left
    # behind; it stands in for a DIFFERENT process's interrupted run.
    broken_file.write_text(
        "// Deliberately invalid TypeScript -- simulates leftover residue from an interrupted\n"
        "// test_start_frontend_script.py run (ops-hardening iter-78 residue-defense regression test).\n"
        "// Removed by the LAUNCHER itself (this test's own subject), independent of this module's own\n"
        "// autouse cleanup, which would also remove it at teardown regardless of this test's outcome.\n"
        "const __trendora_test_residue_broken__: string = 12345;\n"
    )
    orphan_scratch = FRONTEND_DIR / _scratch_dist_name("orphan")
    orphan_scratch.mkdir()
    (orphan_scratch / "sentinel.txt").write_text("leftover scratch dist dir from a different process\n")

    launched = launcher(dist_rel, _TC6_78_PORT, _TC6_78_PORT + 1000, "residue-defense.log")
    _wait_for_port_answering(
        _TC6_78_PORT, timeout=_BUILD_TIMEOUT_S, proc=launched.proc, log_path=launched.log_path
    )
    assert (launched.dist_abs / "BUILD_ID").exists(), (
        "expected the launcher's own `next build` to succeed once the residue is purged"
    )
    _assert_page_fully_styled(_TC6_78_PORT)

    log_text = launched.log_text()
    assert "purged leftover test-residue" in log_text, (
        f"expected the launcher's own purge log line; got:\n{log_text[-4000:]}"
    )
    assert "next build FAILED" not in log_text, (
        f"the residue must never reach `next build` at all; got:\n{log_text[-4000:]}"
    )
    assert not broken_file.exists(), "the launcher must have deleted the residue file before building"
    assert not orphan_scratch.exists(), "the launcher must have deleted the orphan scratch dist dir too"


def test_residue_purge_spares_a_scratch_dist_dir_another_live_server_is_serving(launcher):
    """ops-hardening iter-78 AUDIT FIX (finding B1). The residue purge above deletes every
    `.next-test-*` dir EXCEPT this invocation's own `$NEXT_DIST_DIR`. That exclusion is not sufficient:
    two launcher invocations pointed at DIFFERENT scratch dirs (two overlapping runs of this very module
    on one host -- the contention iter-78's own dev handoff records hitting) would each classify the
    OTHER's dir as abandoned leftover and `rm -rf` it out from under a LIVE `next start`, tearing a
    running server's assets mid-flight. That is exactly the harm the iter-77 `.trendora-serving` marker
    exists to prevent, and the purge ran before that guard was ever consulted.

    Proven against the REAL script, with a real live process: a scratch dir carrying a serving marker
    for a live, node-like pid must SURVIVE, while an unmarked sibling in the same glob is still purged
    -- so the fix is a genuine narrowing (leftover residue still goes), never a blanket disable."""
    if not (FRONTEND_DIR / "node_modules").exists():
        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")

    # Stand-in for ANOTHER launcher's live `next start`: a real long-lived process whose /proc cmdline
    # satisfies the same node/next/npx/taskset PID-reuse guard the script applies.
    live_server = subprocess.Popen(
        ["node", "-e", "setTimeout(() => {}, 900000)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    protected = FRONTEND_DIR / _scratch_dist_name("live-served")
    orphan = FRONTEND_DIR / _scratch_dist_name("orphan-unserved")
    try:
        protected.mkdir()
        (protected / "sentinel.txt").write_text("another live server's dist dir -- must never be purged\n")
        (protected / ".trendora-serving").write_text(
            f"pid={live_server.pid}\nport=1\ndist={protected.name}\nstarted_at=now\n"
        )
        orphan.mkdir()
        (orphan / "sentinel.txt").write_text("abandoned leftover -- must still be purged\n")

        dist_rel = _scratch_dist_name("live-guard")
        launched = launcher(dist_rel, _TC7_78_PORT, _TC7_78_PORT + 1000, "residue-live-guard.log")
        _wait_for_port_answering(
            _TC7_78_PORT, timeout=_BUILD_TIMEOUT_S, proc=launched.proc, log_path=launched.log_path
        )

        log_text = launched.log_text()
        assert (protected / "sentinel.txt").exists(), (
            "the launcher must NOT purge a scratch dist dir another live server is serving; log:\n"
            f"{log_text[-4000:]}"
        )
        assert "another live server is serving it" in log_text, (
            f"expected the launcher to log why it spared that dir; got:\n{log_text[-4000:]}"
        )
        assert not orphan.exists(), (
            "an unmarked leftover scratch dir must STILL be purged -- the guard narrows the purge, it "
            f"does not disable it; log:\n{log_text[-4000:]}"
        )
        assert (launched.dist_abs / "BUILD_ID").exists(), "the launcher's own build must still succeed"
    finally:
        live_server.kill()
        live_server.wait(timeout=10)
        shutil.rmtree(protected, ignore_errors=True)
        shutil.rmtree(orphan, ignore_errors=True)


# ==================================================================================================
# ops-hardening iter-43 (goal.md "Additional binding notes", the iter-33/i owner item) -- TC-5:
# start-frontend.sh now carries the SAME HOST-GUARD cap block scripts/start-backend.sh already applies.
# Mirrors test_start_backend_script.py's own `_read_host_guard_env` / `_parse_cpu_list` /
# `_read_proc_status_cpus_allowed` / `_read_proc_environ` helpers exactly (duplicated, not imported --
# this module's own established convention; see e.g. `_owning_pid` above).
# ==================================================================================================
HOST_GUARD_ENV_FILE = REPO_ROOT / "project-extensions" / "host-guard" / "host-guard.env"
_HOST_GUARD_BLAS_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")
_HG_TEST_PORT = 21300 + _offset


def _read_host_guard_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        val = val.strip().strip('"').strip("'")
        values[key.strip()] = val
    return values


def _parse_cpu_list(spec: str) -> set[int]:
    cpus: set[int] = set()
    spec = spec.strip()
    if not spec:
        return cpus
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, _, hi = part.partition("-")
            cpus.update(range(int(lo), int(hi) + 1))
        else:
            cpus.add(int(part))
    return cpus


def _read_proc_status_cpus_allowed(pid: int) -> str:
    with open(f"/proc/{pid}/status") as fh:
        for line in fh:
            if line.startswith("Cpus_allowed_list:"):
                return line.split(":", 1)[1].strip()
    raise AssertionError(f"no 'Cpus_allowed_list' row in /proc/{pid}/status")


def _read_proc_environ(pid: int) -> dict[str, str]:
    with open(f"/proc/{pid}/environ", "rb") as fh:
        raw = fh.read()
    env: dict[str, str] = {}
    for entry in raw.split(b"\x00"):
        if b"=" in entry:
            k, _, v = entry.partition(b"=")
            env[k.decode(errors="replace")] = v.decode(errors="replace")
    return env


def test_start_frontend_applies_host_guard_and_skips_when_absent_or_disabled(tmp_path):
    """TC-5 -- `scripts/start-frontend.sh` carries the SAME HOST-GUARD cap block
    `scripts/start-backend.sh` already applies. Three cases share ONE real `next build` (against a
    single scratch dist dir) so only the FIRST boot pays the full build cost -- every later boot in
    this test takes the existing skip-rebuild fast path (seconds, not minutes):

      1. enabled (the real committed host-guard.env) -> the `next start` worker's CPU affinity matches
         `HOST_GUARD_CPU_LIST` and its environment carries the BLAS/OMP/numexpr thread-cap vars.
      2. absent (HOST_GUARD_ENV_FILE points at a nonexistent path, never the real committed file) -> no
         CPU-affinity restriction, no BLAS/OMP env change.
      3. disabled (a scratch copy of the real file with ONLY HOST_GUARD_ENABLED=0 changed) -> same as (2).
    """
    if not SCRIPT.exists():
        pytest.skip(f"{SCRIPT} not found")
    if not (FRONTEND_DIR / "node_modules").exists():
        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")
    if not HOST_GUARD_ENV_FILE.exists():
        pytest.skip(f"{HOST_GUARD_ENV_FILE} not present -- host-guard is optional, nothing to verify")
    hg = _read_host_guard_env(HOST_GUARD_ENV_FILE)
    if hg.get("HOST_GUARD_ENABLED") != "1":
        pytest.skip("HOST_GUARD_ENABLED != 1 in the committed host-guard.env -- nothing to verify")

    dist_rel = _scratch_dist_name("hg")
    own_cpus = os.sched_getaffinity(0)
    ambient_blas = {v: os.environ.get(v) for v in _HOST_GUARD_BLAS_VARS}

    def _boot(port: int, log_name: str, extra_env: dict) -> _Launcher:
        log_path = tmp_path / log_name
        env = dict(os.environ)
        env["CHAIN_FRONTEND_PORT"] = str(port)
        env["CHAIN_BACKEND_PORT"] = str(port + 1000)
        env["NEXT_DIST_DIR"] = dist_rel
        env.update(extra_env)
        log_fh = open(log_path, "wb")
        proc = subprocess.Popen(
            ["bash", str(SCRIPT)], cwd=str(REPO_ROOT), env=env,
            stdout=log_fh, stderr=subprocess.STDOUT, preexec_fn=os.setsid,
        )
        return _Launcher(proc, log_path, log_fh, FRONTEND_DIR / dist_rel)

    # --- case 1: enabled (real committed host-guard.env) -- pays for the one real build in this test ---
    launched = _boot(_HG_TEST_PORT, "hg-enabled.log", {})
    try:
        _wait_for_port_answering(
            _HG_TEST_PORT, timeout=_BUILD_TIMEOUT_S, proc=launched.proc, log_path=launched.log_path
        )
        assert (launched.dist_abs / "BUILD_ID").exists(), "expected the shared build to produce a BUILD_ID"
        pid = _owning_pid(_HG_TEST_PORT)
        expected_cpus = _parse_cpu_list(hg["HOST_GUARD_CPU_LIST"])
        actual_cpus = _parse_cpu_list(_read_proc_status_cpus_allowed(pid))
        assert actual_cpus == expected_cpus, (
            f"expected Cpus_allowed_list {sorted(expected_cpus)}, got {sorted(actual_cpus)}"
        )
        env = _read_proc_environ(pid)
        for var in _HOST_GUARD_BLAS_VARS:
            assert env.get(var) == hg["HOST_GUARD_BLAS_THREADS"], (
                f"expected {var}={hg['HOST_GUARD_BLAS_THREADS']!r}, got {env.get(var)!r}"
            )
    finally:
        launched.stop()

    # --- case 2: absent (nonexistent HOST_GUARD_ENV_FILE, never the real committed file) ---
    missing = tmp_path / "no-such-host-guard.env"
    assert not missing.exists()
    launched = _boot(_HG_TEST_PORT + 1, "hg-absent.log", {"HOST_GUARD_ENV_FILE": str(missing)})
    try:
        _wait_for_port_answering(
            _HG_TEST_PORT + 1, timeout=_START_TIMEOUT_S, proc=launched.proc, log_path=launched.log_path
        )
        pid = _owning_pid(_HG_TEST_PORT + 1)
        cpus = _parse_cpu_list(_read_proc_status_cpus_allowed(pid))
        assert cpus == own_cpus, "no CPU-affinity restriction should apply when host-guard.env is absent"
        penv = _read_proc_environ(pid)
        for var, ambient_val in ambient_blas.items():
            assert penv.get(var) == ambient_val, (
                f"host-guard.env absent must not change {var} (ambient {ambient_val!r}, got {penv.get(var)!r})"
            )
    finally:
        launched.stop()

    # --- case 3: disabled (scratch copy, ONLY HOST_GUARD_ENABLED=0 changed) ---
    real_text = HOST_GUARD_ENV_FILE.read_text()
    disabled_text, n = re.subn(
        r"^HOST_GUARD_ENABLED=.*$", "HOST_GUARD_ENABLED=0", real_text, count=1, flags=re.MULTILINE
    )
    assert n == 1, "expected exactly one HOST_GUARD_ENABLED= line in the committed host-guard.env"
    scratch = tmp_path / "host-guard-disabled.env"
    scratch.write_text(disabled_text)
    launched = _boot(_HG_TEST_PORT + 2, "hg-disabled.log", {"HOST_GUARD_ENV_FILE": str(scratch)})
    try:
        _wait_for_port_answering(
            _HG_TEST_PORT + 2, timeout=_START_TIMEOUT_S, proc=launched.proc, log_path=launched.log_path
        )
        pid = _owning_pid(_HG_TEST_PORT + 2)
        cpus = _parse_cpu_list(_read_proc_status_cpus_allowed(pid))
        assert cpus == own_cpus, "no CPU-affinity restriction should apply when HOST_GUARD_ENABLED=0"
        penv = _read_proc_environ(pid)
        for var, ambient_val in ambient_blas.items():
            assert penv.get(var) == ambient_val, (
                f"HOST_GUARD_ENABLED=0 must not change {var} (ambient {ambient_val!r}, got {penv.get(var)!r})"
            )
    finally:
        launched.stop()


def test_host_guard_marker_files_lists_start_frontend():
    """TC-5 (marker registration) -- `project-extensions/host-guard/host-guard.env`'s
    `HOST_GUARD_MARKER_FILES` lists `scripts/start-frontend.sh` alongside the two pre-existing launchers,
    so the framework's own generic marker check (`grep -q "HOST-GUARD" <file>`,
    `incredible_auto_dev/scripts/automation/run-goal.sh`) covers it too."""
    if not HOST_GUARD_ENV_FILE.exists():
        pytest.skip(f"{HOST_GUARD_ENV_FILE} not present -- nothing to verify")
    hg = _read_host_guard_env(HOST_GUARD_ENV_FILE)
    markers = (hg.get("HOST_GUARD_MARKER_FILES") or "").split()
    assert "scripts/start-frontend.sh" in markers, f"HOST_GUARD_MARKER_FILES={markers!r}"
    assert "scripts/dev.sh" in markers and "scripts/start-backend.sh" in markers, (
        "the two pre-existing launchers must still be listed too — never a replacement, an addition"
    )
    # the marker check itself is a plain substring grep — confirm the block is genuinely present, not
    # merely declared in the list above.
    assert "HOST-GUARD" in SCRIPT.read_text()


# ==================================================================================================
# ops-hardening iter-77 -- the goal-spec's OWN TC-1/TC-2: the intermittent asset-less-frontend defect
# (iter-72/c, un-root-caused and un-fixed for 4 rounds). Root-caused via direct code reading (this
# script had no lock against a second concurrent invocation racing `next build` against the SAME live
# dist dir -- see the "BUILD LOCK" block start-frontend.sh now carries) and closed with a `flock`
# serializing the staleness-check -> build decision per dist-dir. These two tests are the goal-spec's
# own scenarios -- NOT a duplicate of this module's pre-existing iter-33 TC-1/TC-2 above, which assert a
# DIFFERENT thing (which branch — build vs. skip-rebuild — a single invocation takes).
# ==================================================================================================


def test_five_consecutive_fresh_launches_serve_fully_styled_page(launcher):
    """iter-77 TC-1 -- 5 consecutive, NON-concurrent `start-frontend.sh` launches against the same dist
    dir must each serve a fully-styled page (the HTML plus its own referenced build assets, all HTTP 200
    with real content), zero asset-less occurrences. Builds the scratch dist dir once for real (like
    every other real-build test in this module — a `next build` per launch would be prohibitively slow)
    then stops/relaunches the SAME launcher four more times against that now-current build, proving the
    iter-77 build-lock addition does not regress the ordinary sequential-restart path (the ONLY path
    most real launches ever take)."""
    if not (FRONTEND_DIR / "node_modules").exists():
        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")
    dist_rel = _scratch_dist_name("tc1-77")
    port = _TC1_77_PORT
    for i in range(5):
        launched = launcher(dist_rel, port, port + 1000, f"tc1-77-{i}.log")
        timeout = _BUILD_TIMEOUT_S if i == 0 else _START_TIMEOUT_S
        _wait_for_port_answering(port, timeout=timeout, proc=launched.proc, log_path=launched.log_path)
        _assert_page_fully_styled(port)
        launched.stop()


def test_concurrent_invocations_never_serve_partial_build(launcher):
    """iter-77 TC-2 -- two invocations of `start-frontend.sh` launched CONCURRENTLY against the SAME
    brand-new (never-built) `NEXT_DIST_DIR`, on two different ports. Before the iter-77 build-lock fix,
    both would see the build as stale and run `next build` concurrently against the SAME output
    directory with no coordination -- the real race this iteration's spec requires a test to directly
    exercise (per its own note: 'quiet for N rounds' is not proof of a fix). This asserts (1) the lock's
    OWN log line proves the second invocation genuinely BLOCKED on the first's build rather than racing
    it — the concrete mechanism, not just a passing outcome that could happen to get lucky on timing —
    and (2) once both invocations are up and serving, EACH renders a fully-styled page — never a
    partial/mid-build payload — proving the shared dist dir was never served in a torn state."""
    if not (FRONTEND_DIR / "node_modules").exists():
        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")
    dist_rel = _scratch_dist_name("tc2-77")
    assert not (FRONTEND_DIR / dist_rel).exists(), "the scratch dist dir must not exist before launching"
    port_a, port_b = _TC2_77_PORT, _TC2_77_PORT + 1

    launched_a = launcher(dist_rel, port_a, port_a + 1000, "tc2-77-a.log")
    launched_b = launcher(dist_rel, port_b, port_b + 1000, "tc2-77-b.log")

    _wait_for_port_answering(
        port_a, timeout=_BUILD_TIMEOUT_S, proc=launched_a.proc, log_path=launched_a.log_path
    )
    _wait_for_port_answering(
        port_b, timeout=_BUILD_TIMEOUT_S, proc=launched_b.proc, log_path=launched_b.log_path
    )

    log_a, log_b = launched_a.log_text(), launched_b.log_text()
    assert ("waiting for its build lock" in log_a) or ("waiting for its build lock" in log_b), (
        "expected ONE of the two concurrent invocations to observe the OTHER already holding the build "
        f"lock (proves the race was genuinely exercised, not just luck) -- got:\nA:\n{log_a[-2000:]}"
        f"\nB:\n{log_b[-2000:]}"
    )
    assert "acquired build lock" in log_a and "acquired build lock" in log_b, (
        f"both invocations must eventually acquire the lock and proceed (never deadlock) -- got:\n"
        f"A:\n{log_a[-2000:]}\nB:\n{log_b[-2000:]}"
    )

    _assert_page_fully_styled(port_a)
    _assert_page_fully_styled(port_b)


def test_out_of_band_build_is_treated_as_stale_and_rebuilt(launcher):
    """ops-hardening iter-77 AUDIT -- a build the LAUNCHER did not produce must never be served as
    "current".

    The concrete defect this closes (reproduced live during the iter-77 audit, not hypothesised): a bare
    `npx next build` run inside `apps/frontend` as a verification step -- the exact command both this
    iteration's dev handoff and its QA report record themselves running -- rewrites the LIVE `.next` with
    a bundle built WITHOUT the `NEXT_PUBLIC_API_URL`/`NEXT_PUBLIC_API_PORT` exports `start-frontend.sh`
    sets, so Next bakes its own `http://localhost:8000` fallback into the client bundle. The staleness
    check compares SOURCE mtimes against BUILD_ID and therefore sees nothing wrong: the launcher logged
    "build is current ... skipping rebuild" and served a frontend that rendered the global "Backend
    unavailable" state on every page while the backend was healthy on its real port.

    Simulating (rather than really running) the out-of-band build keeps this test to two real builds: a
    bare `next build` always mints a FRESH `BUILD_ID` into the dist dir, which is exactly what step 2
    below reproduces -- the launcher must then rebuild rather than trust the foreign output."""
    if not (FRONTEND_DIR / "node_modules").exists():
        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")
    dist_rel = _scratch_dist_name("tc3-77")
    port, backend_port = _TC3_77_PORT, _TC3_77_PORT + 1000
    marker = FRONTEND_DIR / dist_rel / ".trendora-launch-build"
    build_id = FRONTEND_DIR / dist_rel / "BUILD_ID"

    # 1. A normal launcher build: the marker is written and names the backend this launch configured.
    first = launcher(dist_rel, port, backend_port, "tc3-77-first.log")
    _wait_for_port_answering(port, timeout=_BUILD_TIMEOUT_S, proc=first.proc, log_path=first.log_path)
    assert marker.exists(), f"expected the launcher to record its own build marker at {marker}"
    marker_text = marker.read_text()
    assert f"build_id={build_id.read_text().strip()}" in marker_text, marker_text
    assert f"api_url=http://localhost:{backend_port}" in marker_text, marker_text
    first.stop()

    # 2. Simulate an out-of-band `npx next build`: same dist dir, a fresh BUILD_ID, no launcher
    #    involvement (the marker is left in place on purpose -- the id comparison, not merely the file's
    #    presence, must be what catches this).
    build_id.write_text("out-of-band-build-id\n")

    # 3. The next launch must NOT trust it.
    second = launcher(dist_rel, port, backend_port, "tc3-77-second.log")
    _wait_for_port_answering(port, timeout=_BUILD_TIMEOUT_S, proc=second.proc, log_path=second.log_path)
    log = second.log_text()
    assert "was not built by this launcher" in log, (
        f"expected the foreign build to be detected and rebuilt, got:\n{log[-2000:]}"
    )
    assert "running 'next build'" in log, (
        f"expected the foreign build to trigger an actual rebuild, got:\n{log[-2000:]}"
    )
    _assert_page_fully_styled(port)
    assert f"build_id={build_id.read_text().strip()}" in marker.read_text(), (
        "the rebuild must refresh the marker so the NEXT launch skips correctly"
    )


# ==================================================================================================
# ops-hardening iter-77 AUDIT FIX ROUND 2 -- findings B2 ("an out-of-band `next build` can still tear /
# poison the LIVE dist dir; code cannot stop it") and B3 ("the shipped root cause was never
# instrumented").
#
# The audit's first fix taught the LAUNCHER to distrust a foreign build after the fact. These tests
# cover the two additions that stop it happening at all, and the one that detects it at launch:
#   * `apps/frontend/next.config.mjs` -- the ONE file every `next build` must load, whoever invokes it:
#     it now REFUSES a production build that would (a) write into the live `.next` without
#     NEXT_PUBLIC_API_URL (the bare `npx next build` that poisoned this round -> a bundle pointing at
#     http://localhost:8000, which nothing binds) or (b) write into ANY dist dir a live server is
#     currently serving (the half B2 called un-fixable in code).
#   * `scripts/start-frontend.sh` -- writes the `.trendora-serving` claim the guard reads, and now
#     verifies at launch that the build on disk actually references the backend this launch configured.
# ==================================================================================================

_GUARD_PROBE_JS = (
    "import('./next.config.mjs')"
    ".then((m) => m.default('phase-production-build'))"
    ".then(() => console.log('ALLOWED'),"
    " (e) => { console.log('REFUSED: ' + e.message); process.exitCode = 3; })"
)


def _guard_verdict(dist_rel: str | None, api_url: str | None) -> tuple[bool, str]:
    """Ask `next.config.mjs` DIRECTLY whether it would allow a production build into `dist_rel` (None =
    the live `.next`) -- the same call Next itself makes (`normalizeConfig(phase, config)` invokes the
    exported function with the phase). Seconds, not a real build, so the guard's PRECISION (it must
    allow every legitimate build) can be asserted broadly without paying for a webpack compile each
    time. Returns (allowed, output)."""
    env = dict(os.environ)
    env.pop("NEXT_DIST_DIR", None)
    env.pop("NEXT_PUBLIC_API_URL", None)
    env.pop("TRENDORA_LAUNCH_BUILD", None)
    if dist_rel is not None:
        env["NEXT_DIST_DIR"] = dist_rel
    if api_url is not None:
        env["NEXT_PUBLIC_API_URL"] = api_url
    proc = subprocess.run(
        ["node", "-e", _GUARD_PROBE_JS],
        cwd=str(FRONTEND_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    out = (proc.stdout + proc.stderr).strip()
    return ("ALLOWED" in proc.stdout), out


def test_build_guard_refuses_the_unconfigured_live_dist_build_and_leaves_it_untouched():
    """The EXACT command that broke iter-77 -- a bare `npx next build` inside `apps/frontend` -- must now
    fail instead of rewriting the live `.next`.

    Runs the real command (not a simulation): the guard lives in `next.config.mjs`, which Next loads
    before it touches the dist dir, so the refusal costs seconds and the live build's BUILD_ID must come
    back byte-identical. Both guard rules protect the same invariant here (the live dir may also be
    claimed by a running server), so the assertion accepts either refusal reason but requires the live
    build to be untouched -- that is the property that failed this round.

    If this test ever FAILS because the guard stopped working, the timeout below caps the damage at a
    partial build the launcher's provenance marker (`test_out_of_band_build_is_treated_as_stale_and_
    rebuilt`) will rebuild on the next launch."""
    if not (FRONTEND_DIR / "node_modules").exists():
        pytest.skip("apps/frontend/node_modules not installed -- cannot run `next build`")
    live_build_id = FRONTEND_DIR / ".next" / "BUILD_ID"
    before = live_build_id.read_text() if live_build_id.exists() else None

    env = dict(os.environ)
    for var in ("NEXT_PUBLIC_API_URL", "NEXT_PUBLIC_API_PORT", "NEXT_DIST_DIR", "TRENDORA_LAUNCH_BUILD"):
        env.pop(var, None)
    proc = subprocess.run(
        ["npx", "next", "build"],
        cwd=str(FRONTEND_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0, f"the bare `npx next build` must be REFUSED, not run:\n{out[-2000:]}"
    assert "TRENDORA BUILD GUARD" in out, f"expected the guard's own refusal, got:\n{out[-2000:]}"
    assert ("without" in out and "NEXT_PUBLIC_API_URL" in out) or "being SERVED right now" in out, (
        f"expected one of the two guard reasons, got:\n{out[-2000:]}"
    )
    # The message must be actionable -- the whole point is that the next caller knows what to do.
    assert "NEXT_DIST_DIR=.next-verify" in out, f"expected an actionable remedy, got:\n{out[-2000:]}"

    after = live_build_id.read_text() if live_build_id.exists() else None
    assert after == before, (
        "the refused build must not have touched the live `.next` -- "
        f"BUILD_ID went {before!r} -> {after!r}"
    )


def test_build_guard_allows_every_legitimate_build():
    """Precision, asserted directly against `next.config.mjs` (seconds, no webpack): the guard must NOT
    become a blanket block. A verification build into a throwaway dist dir -- the remedy its own message
    recommends -- is allowed with or without NEXT_PUBLIC_API_URL, and a configured build into the live
    dir is allowed as long as nothing is serving it."""
    allowed, out = _guard_verdict(".next-verify", None)
    assert allowed, f"a verification build into a throwaway dist dir must be allowed, got:\n{out}"
    allowed, out = _guard_verdict(".next-verify", "http://localhost:8255")
    assert allowed, f"a configured throwaway build must be allowed, got:\n{out}"
    # A never-served scratch dir with the backend configured: the shape `start-frontend.sh` itself uses.
    scratch = _scratch_dist_name("guard-precision")
    allowed, out = _guard_verdict(scratch, "http://localhost:8255")
    assert allowed, f"a configured build into an unserved scratch dist dir must be allowed, got:\n{out}"


def test_build_guard_refuses_building_into_a_dist_dir_a_live_server_is_serving(launcher):
    """finding B2's remaining half, closed in code: while `start-frontend.sh` is SERVING a dist dir, no
    other `next build` may rewrite it -- however it is invoked, and even when correctly configured.

    This is the mechanism that produced iter-77's five byte-identical full-page-crash demo frames: a
    verification build rewrote the assets out from under the running server. One real build pays for all
    three assertions:
      1. the launcher records its serving claim (`.trendora-serving`) with the pid that is actually
         serving -- the guard's input;
      2. a real, fully-configured `npx next build` into that same dist dir is REFUSED, the dist dir's
         BUILD_ID is unchanged, and the live server is still serving a fully-styled page afterwards;
      3. once that server stops, the SAME target is allowed again -- the claim expires with the process,
         so a hard-killed server can never wedge future builds."""
    if not (FRONTEND_DIR / "node_modules").exists():
        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")
    dist_rel = _scratch_dist_name("tc4-77")
    port, backend_port = _TC4_77_PORT, _TC4_77_PORT + 1000
    api_url = f"http://localhost:{backend_port}"

    launched = launcher(dist_rel, port, backend_port, "tc4-77.log")
    _wait_for_port_answering(port, timeout=_BUILD_TIMEOUT_S, proc=launched.proc, log_path=launched.log_path)

    # 1. the serving claim
    serving_marker = FRONTEND_DIR / dist_rel / ".trendora-serving"
    assert serving_marker.exists(), f"expected the launcher to claim its dist dir at {serving_marker}"
    marker_text = serving_marker.read_text()
    assert f"port={port}" in marker_text, marker_text
    claimed_pid = int(re.search(r"^pid=(\d+)$", marker_text, re.M).group(1))
    os.kill(claimed_pid, 0)  # raises if the claimed pid is not actually alive
    assert re.search(r"\b(next|npx|node)\b", _cmdline(claimed_pid)), (
        f"the claimed pid must be the serving process itself, got cmdline: {_cmdline(claimed_pid)!r}"
    )

    # 2. a correctly-configured foreign build into the SERVED dir is refused, and serving is unharmed
    build_id = FRONTEND_DIR / dist_rel / "BUILD_ID"
    before = build_id.read_text()
    env = dict(os.environ)
    env["NEXT_DIST_DIR"] = dist_rel
    env["NEXT_PUBLIC_API_URL"] = api_url
    env.pop("TRENDORA_LAUNCH_BUILD", None)
    proc = subprocess.run(
        ["npx", "next", "build"], cwd=str(FRONTEND_DIR), env=env, capture_output=True, text=True, timeout=180
    )
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0, f"a build into a SERVED dist dir must be refused:\n{out[-2000:]}"
    assert "being SERVED right now" in out, f"expected the serving-claim refusal, got:\n{out[-2000:]}"
    assert str(claimed_pid) in out, f"the refusal must name the serving process, got:\n{out[-2000:]}"
    assert build_id.read_text() == before, "the refused build must not have rewritten the served dist dir"
    _assert_page_fully_styled(port)  # the live server was never torn

    # 3. the claim expires with the process (no wedged dist dirs after a hard kill)
    launched.stop()
    allowed, verdict_out = _guard_verdict(dist_rel, api_url)
    assert allowed, (
        "once the serving process is gone its claim must expire -- a stale marker must never block a "
        f"later build:\n{verdict_out}"
    )


def test_launcher_rebuilds_a_bundle_built_for_a_different_backend(launcher):
    """finding B3 ("the shipped root cause was never instrumented"): the launcher now CHECKS, on every
    launch, that the build it is about to serve actually references the backend this launch configured
    -- the same `grep -rl "localhost:<port>" .next` the audit had to run by hand to diagnose B1.

    Exercised end-to-end: build+serve against backend A, stop, relaunch pointing at backend B. Nothing
    else changed -- sources are untouched and the provenance marker still matches -- so the ONLY thing
    that can catch the mismatch is the new bundle check. Before it, the launcher logged "build is current
    ... skipping rebuild" and served a frontend that could not reach its backend, which is precisely how
    this iteration shipped a broken app past every green gate."""
    if not (FRONTEND_DIR / "node_modules").exists():
        pytest.skip("apps/frontend/node_modules not installed -- cannot build/start the frontend")
    dist_rel = _scratch_dist_name("tc5-77")
    port = _TC5_77_PORT
    backend_a, backend_b = port + 1000, port + 1001

    first = launcher(dist_rel, port, backend_a, "tc5-77-a.log")
    _wait_for_port_answering(port, timeout=_BUILD_TIMEOUT_S, proc=first.proc, log_path=first.log_path)
    chunks = list((FRONTEND_DIR / dist_rel / "static").rglob("*.js"))
    assert any(f"http://localhost:{backend_a}" in c.read_text(errors="replace") for c in chunks), (
        "sanity: the built client bundle must inline the backend URL this launch configured "
        "(the fact the check below relies on)"
    )
    first.stop()

    second = launcher(dist_rel, port, backend_b, "tc5-77-b.log")
    _wait_for_port_answering(port, timeout=_BUILD_TIMEOUT_S, proc=second.proc, log_path=second.log_path)
    log = second.log_text()
    assert "was built for a different backend" in log, (
        f"expected the launcher to DETECT the backend mismatch, got:\n{log[-2000:]}"
    )
    assert "running 'next build'" in log, (
        f"expected the mismatch to force a rebuild rather than serve an unreachable app, got:\n{log[-2000:]}"
    )
    assert "skipping rebuild" not in log, f"the stale bundle must never be served as current:\n{log[-2000:]}"
    _assert_page_fully_styled(port)
    chunks = list((FRONTEND_DIR / dist_rel / "static").rglob("*.js"))
    assert any(f"http://localhost:{backend_b}" in c.read_text(errors="replace") for c in chunks), (
        "the rebuilt bundle must reference the backend the SECOND launch configured"
    )
