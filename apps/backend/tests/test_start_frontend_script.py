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
    broken = FRONTEND_DIR / _BROKEN_SOURCE_REL
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

    second = launcher(dist_rel, _TC2_PORT + 1, _TC2_PORT + 1001, "tc2-second.log")
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
    run left this file behind and made this test fail on its own guard assertion)."""
    if not (FRONTEND_DIR / "node_modules").exists():
        pytest.skip("apps/frontend/node_modules not installed -- cannot build the frontend")

    dist_rel = _scratch_dist_name("tc3")
    broken_file = FRONTEND_DIR / _BROKEN_SOURCE_REL
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
