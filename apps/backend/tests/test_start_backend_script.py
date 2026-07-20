"""Script-level checks for `scripts/start-backend.sh` (ops-hardening iter-2, J-04 remainder): the memory
cap / `MALLOC_ARENA_MAX` / persistent-logfile enforcement goal.md's binding note requires and this
iteration adds — previously this script set NO ulimit, exported NO env var, and wrote NO logfile
(confirmed by a direct read before this iteration). There is nothing to mock here: the assertions are
about a REAL LAUNCHED PROCESS's actual resource limits / environment / logfile, so this spawns the real
script as a subprocess against the real repo checkout, on an isolated test-only port so it never collides
with an already-running dev/QA backend on this machine.

TC-15 (RLIMIT_AS + MALLOC_ARENA_MAX), TC-16 (persistent logfile has boot events), TC-17 (a SIGKILL leaves
the logfile ending abruptly, no clean-shutdown entry)."""
from __future__ import annotations

import hashlib
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest

# apps/backend/tests/test_start_backend_script.py -> tests -> backend -> apps -> <repo root>
REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "start-backend.sh"
LOG_FILE = REPO_ROOT / "logs" / "backend.log"

# A deterministic-but-distinct port range (offset +10000 from the scripts' own 8000-8999 per-project
# range) so this test never collides with an already-running dev/QA backend on this machine, while still
# being reproducible across runs of the SAME checkout.
_offset = int(hashlib.sha1(str(REPO_ROOT).encode()).hexdigest()[:4], 16) % 1000
_TEST_PORT = 18000 + _offset


def _read_proc_limits_max_address_space_bytes(pid: int) -> int:
    """Parse `/proc/<pid>/limits`'s "Max address space" row -> the soft limit in bytes (RLIMIT_AS)."""
    with open(f"/proc/{pid}/limits") as fh:
        for line in fh:
            if line.startswith("Max address space"):
                parts = line.split()
                # "Max address space         <soft>         <hard>         bytes"
                return int(parts[3])
    raise AssertionError(f"no 'Max address space' row in /proc/{pid}/limits")


def _read_proc_environ(pid: int) -> dict[str, str]:
    with open(f"/proc/{pid}/environ", "rb") as fh:
        raw = fh.read()
    env: dict[str, str] = {}
    for entry in raw.split(b"\x00"):
        if b"=" in entry:
            k, _, v = entry.partition(b"=")
            env[k.decode(errors="replace")] = v.decode(errors="replace")
    return env


def _wait_for_health(port: int, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last_exc: Exception | None = None
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(f"http://127.0.0.1:{port}/api/health", timeout=1.0)
            if resp.status_code == 200:
                return
        except Exception as exc:  # noqa: BLE001 — keep polling until the deadline
            last_exc = exc
        time.sleep(0.25)
    raise AssertionError(f"backend on :{port} did not become healthy within {timeout}s (last error: {last_exc})")


def _pid_alive(pid: int) -> bool:
    """True iff `pid` (a DIRECT child of this pytest process, spawned via `subprocess.Popen` in the
    `spawned_backend` fixture) is still actually running. `os.kill(pid, 0)` alone is NOT sufficient here:
    once a child is killed but not yet reaped, it becomes a zombie — still present in the process table
    (so `os.kill(pid, 0)` keeps succeeding) until something calls `waitpid` on it. `os.waitpid(pid,
    os.WNOHANG)` both correctly distinguishes "still running" from "exited, zombie" and reaps it in the
    same call, so a dead child is never mistaken for a live one on a later check."""
    try:
        reaped_pid, _status = os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        return False  # already reaped (e.g., by Popen.wait() elsewhere) — definitely gone
    if reaped_pid == 0:
        return True  # still running (WNOHANG returns (0, 0) immediately when not yet exited)
    return False  # reaped just now — it had exited


@dataclass
class SpawnedBackend:
    """`pid` is the launched uvicorn process (see the fixture docstring for why this equals the launching
    shell's own pid). `log_offset_before` is `logs/backend.log`'s size (bytes) immediately BEFORE this
    fixture spawned anything — since the logfile is PERSISTENT and APPEND-mode BY DESIGN (this same
    iteration's own feature), it may already carry content from earlier boots/restarts in this same test
    session (or a developer's own manual verification pass); a test that cares about what THIS spawn wrote
    must slice from this offset, never blindly read "the tail of the whole file"."""

    pid: int
    log_offset_before: int


@pytest.fixture()
def spawned_backend():
    """Start the REAL `scripts/start-backend.sh` as a subprocess on the isolated test port, yield its pid
    (+ the pre-spawn logfile offset) once `/api/health` responds, and guarantee it is killed afterward
    (even on assertion failure) — never leaks a live backend process."""
    if not SCRIPT.exists():
        pytest.skip(f"{SCRIPT} not found")
    log_offset_before = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0
    env = dict(os.environ)
    env["CHAIN_BACKEND_PORT"] = str(_TEST_PORT)
    env["CHAIN_FRONTEND_PORT"] = str(_TEST_PORT + 1000)
    proc = subprocess.Popen(
        ["bash", str(SCRIPT)],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        # the script's own `exec` replaces the launching shell with uvicorn (same pid, new program image),
        # so `proc.pid` IS the uvicorn process once that exec has happened (well before health responds).
        _wait_for_health(_TEST_PORT, timeout=60.0)
        yield SpawnedBackend(pid=proc.pid, log_offset_before=log_offset_before)
    finally:
        if _pid_alive(proc.pid):
            os.kill(proc.pid, signal.SIGKILL)
            deadline = time.monotonic() + 10.0
            while _pid_alive(proc.pid) and time.monotonic() < deadline:
                time.sleep(0.1)
        # `_pid_alive` reaps via its own `os.waitpid` (see its docstring) — it may have ALREADY reaped the
        # child here (either just above, or earlier inside the test body itself, e.g. the simulated-crash
        # test). `Popen` has no way to know that happened, so `proc.wait()` would raise `ChildProcessError`
        # on an already-reaped child; that is the expected/harmless case here, not a real failure.
        try:
            proc.wait(timeout=10)
        except ChildProcessError:
            pass


def test_start_backend_enforces_memory_cap_and_malloc_arena_max(spawned_backend):
    """TC-15 — the launched process's RLIMIT_AS reflects `config.server.memory_cap_mb` (6144 MB) and
    `MALLOC_ARENA_MAX` (2) is present in its environment."""
    pid = spawned_backend.pid
    from app.config import get_config

    cfg = get_config()
    soft_limit_bytes = _read_proc_limits_max_address_space_bytes(pid)
    expected_bytes = cfg.server.memory_cap_mb * 1024 * 1024
    assert soft_limit_bytes == expected_bytes, (
        f"expected RLIMIT_AS soft limit {expected_bytes} bytes ({cfg.server.memory_cap_mb} MB), "
        f"got {soft_limit_bytes} bytes"
    )
    env = _read_proc_environ(pid)
    assert env.get("MALLOC_ARENA_MAX") == str(cfg.server.malloc_arena_max)


def test_start_backend_writes_persistent_logfile_with_boot_events(spawned_backend):
    """TC-16 — the documented persistent logfile (`logs/backend.log`, repo-relative) exists and contains
    THIS spawn's boot sequence's log lines (sliced from `log_offset_before` — the file is persistent/
    append-mode by design, so it may carry earlier boots' content too; this test only cares about what
    THIS spawn wrote), surviving past the launching shell (unlike the pre-iteration behavior of writing
    only to whatever terminal launched it)."""
    assert LOG_FILE.exists(), f"expected a persistent logfile at {LOG_FILE}"
    content = LOG_FILE.read_text(errors="replace")[spawned_backend.log_offset_before:]
    assert "start-backend.sh: launching at" in content
    # uvicorn's own startup lines land in the SAME redirected file (config load -> tables -> orphan sweep
    # -> readiness-ready all happen inside this same launched process's stdout/stderr stream).
    assert "Uvicorn running" in content or "Application startup complete" in content


def test_start_backend_logfile_ends_abruptly_after_simulated_crash(spawned_backend):
    """TC-17 — after a simulated crash (SIGKILL), the persistent logfile ends abruptly: no clean-shutdown
    entry follows THIS spawn's boot lines (a killed process gets no chance to run any shutdown/cleanup
    code, so uvicorn's normal graceful-shutdown log lines are absent). Sliced from `log_offset_before` —
    the file is persistent/append-mode by design and may already carry an EARLIER, genuinely clean
    shutdown from a prior boot in this same session; blindly tailing the whole file would wrongly attribute
    that older content to THIS spawn's kill."""
    pid = spawned_backend.pid
    os.kill(pid, signal.SIGKILL)
    deadline = time.monotonic() + 10.0
    while _pid_alive(pid) and time.monotonic() < deadline:
        time.sleep(0.1)
    assert not _pid_alive(pid), "the simulated-crash process should be gone after SIGKILL"

    content_after = LOG_FILE.read_text(errors="replace")[spawned_backend.log_offset_before:]
    assert "start-backend.sh: launching at" in content_after  # this spawn's own boot IS in its own slice
    for phrase in ("Shutting down", "Application shutdown complete", "Finished server process"):
        assert phrase not in content_after, (
            f"unexpected clean-shutdown phrase {phrase!r} after this spawn's own simulated SIGKILL"
        )
