"""ops-hardening iter-41 (C7) — `main.py`'s opt-in `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1` diagnostic.

Proves the ONE property the wedge-drill actually depends on: with the env var set, sending
`SIGUSR1` to a process that has imported `main` dumps an all-thread stack trace and the process
SURVIVES; without it, `main` never touches `SIGUSR1` at all (default disposition — the signal would
terminate a bare process, which is exactly how the test distinguishes "registered" from "not").

Runs `main.py`'s import in a SUBPROCESS (never in the pytest process itself) so this never mutates
the test runner's own signal handlers — `faulthandler.register` is process-global and irreversible
within the process that calls it."""
from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

# Matches faulthandler's per-thread header in BOTH forms it emits:
#   "Current thread 0x00007f... (most recent call first):"  (the signalled thread)
#   "Thread 0x00007f... (most recent call first):"          (every other live thread)
_THREAD_ID_LINE_RE = re.compile(r"^(?:Current )?thread 0x[0-9a-f]+ ", re.IGNORECASE | re.MULTILINE)

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_IMPORT_MAIN = (
    "import sys; sys.path.insert(0, %r); "
    "import main; "  # noqa -- imports the FastAPI app module under test, side effects are the point
    "import time; sys.stderr.write('READY\\n'); sys.stderr.flush(); time.sleep(10)"
) % str(_BACKEND_DIR)


def _spawn(env_extra: dict) -> subprocess.Popen:
    env = dict(os.environ)
    env.update(env_extra)
    # Isolate from any real backend DB/port env the host session may have exported.
    env.pop("CHAIN_BACKEND_PORT", None)
    return subprocess.Popen(
        [sys.executable, "-c", _IMPORT_MAIN],
        cwd=str(_BACKEND_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _wait_for_ready(proc: subprocess.Popen, timeout: float = 30.0) -> str:
    """Block until the subprocess writes READY to stderr (import + app construction done), or the
    process exits early (import failure) -- returns whatever stderr was captured so far either way."""
    deadline = time.time() + timeout
    buf = ""
    while time.time() < deadline:
        line = proc.stderr.readline()
        if line:
            buf += line
            if "READY" in line:
                return buf
        if proc.poll() is not None:
            buf += proc.stderr.read()
            return buf
    return buf


def test_sigusr1_armed_dumps_all_thread_stack_and_survives():
    proc = _spawn({"TRENDORA_DIAG_FAULTHANDLER_SIGUSR1": "1"})
    try:
        ready_log = _wait_for_ready(proc)
        assert proc.poll() is None, f"subprocess exited before READY (import failed?): {ready_log}"

        proc.send_signal(signal.SIGUSR1)
        time.sleep(1.0)  # faulthandler writes synchronously on signal receipt

        assert proc.poll() is None, "the process must SURVIVE SIGUSR1 when faulthandler is armed"

        proc.send_signal(signal.SIGTERM)
        _, stderr = proc.communicate(timeout=10)
        # faulthandler's all-threads dump heads each live thread's stack with a thread-id line:
        # "Current thread 0x<id> (most recent call first):" for the signalled thread and
        # "Thread 0x<id> (most recent call first):" for every other one. This subprocess is
        # single-threaded, so only the lowercase "Current thread" form appears -- match the
        # id line case-insensitively so BOTH forms satisfy it, then require at least one real
        # stack frame ('File "..." , line N in ...') so an empty header alone cannot pass.
        assert _THREAD_ID_LINE_RE.search(stderr) and 'File "' in stderr, (
            f"expected an all-thread stack dump on SIGUSR1, got stderr: {stderr!r}"
        )
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)


def test_sigusr1_unarmed_by_default_leaves_default_disposition():
    """The env var is opt-in: with it UNSET (the real-deployment default), `main` never touches
    SIGUSR1 -- the signal keeps its default disposition (terminate), proving nothing about this
    diagnostic is on by default."""
    proc = _spawn({})  # TRENDORA_DIAG_FAULTHANDLER_SIGUSR1 absent
    try:
        ready_log = _wait_for_ready(proc)
        assert proc.poll() is None, f"subprocess exited before READY (import failed?): {ready_log}"

        proc.send_signal(signal.SIGUSR1)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pytest.fail(
                "process survived SIGUSR1 with the diagnostic env var UNSET -- faulthandler must "
                "not be armed by default"
            )
        # default SIGUSR1 disposition terminates the process; Popen reports this as a negative
        # returncode equal to -SIGUSR1 on POSIX.
        assert proc.returncode == -signal.SIGUSR1, (
            f"expected default-disposition termination (-{int(signal.SIGUSR1)}), got {proc.returncode}"
        )
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
