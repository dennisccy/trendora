"""Script-level checks for `scripts/start-backend.sh` (ops-hardening iter-2, J-04 remainder): the memory
cap / `MALLOC_ARENA_MAX` / persistent-logfile enforcement goal.md's binding note requires and this
iteration adds — previously this script set NO ulimit, exported NO env var, and wrote NO logfile
(confirmed by a direct read before this iteration). There is nothing to mock here: the assertions are
about a REAL LAUNCHED PROCESS's actual resource limits / environment / logfile, so this spawns the real
script as a subprocess against the real repo checkout, on an isolated test-only port so it never collides
with an already-running dev/QA backend on this machine.

TC-15 (RLIMIT_AS + MALLOC_ARENA_MAX), TC-16 (persistent logfile has boot events), TC-17 (a SIGKILL leaves
the logfile ending abruptly, no clean-shutdown entry).

ops-hardening iter-8 (J-05 REGRESSION recovery, TC-1/TC-2) adds
`test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap`: a REAL full-universe `rebuild`
immediately followed by a second heavy `backfill` in the SAME long-lived spawned process — the exact
scenario that made `GET /api/health` hang 7+ minutes with a worker-thread `MemoryError` in iter-7
(`runs/goal-session-ops-hardening/iter-7/eval.md`). Runs against a THROWAWAY COPY of the real dev DB
(never the shared committed file — mirrors `reports/perf-budgets.md` Item L/H's own established
methodology) via a dedicated `spawned_backend_throwaway_db` fixture. This is a genuinely slow, heavy test
(a full rebuild alone measures ~16 minutes on the real dev DB's current size, Item L) — an accepted cost
for a real-process capacity proof, consistent with this project's existing slow real-engine tests (e.g.
`test_forward_testing.py`'s session-scoped 30-year seed rebuild)."""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest

# apps/backend/tests/test_start_backend_script.py -> tests -> backend -> apps -> <repo root>
REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "start-backend.sh"
LOG_FILE = REPO_ROOT / "logs" / "backend.log"
REAL_DB = REPO_ROOT / "apps/backend/data/trendora.db"
REAL_CONFIG = REPO_ROOT / "config.yaml"

# A deterministic-but-distinct port range (offset +10000 from the scripts' own 8000-8999 per-project
# range) so this test never collides with an already-running dev/QA backend on this machine, while still
# being reproducible across runs of the SAME checkout.
_offset = int(hashlib.sha1(str(REPO_ROOT).encode()).hexdigest()[:4], 16) % 1000
_TEST_PORT = 18000 + _offset
# A THIRD, further-distinct port for the throwaway-DB heavy-ingest test below — never shared with the
# other tests in this module (which may run in the same session) or with a real dev/QA instance.
_HEAVY_TEST_PORT = 18500 + _offset


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
    # iter-8 AUDIT (T2 fix): `log_offset_before` is a BYTE offset (`LOG_FILE.stat().st_size`); slicing it
    # against `read_text()`'s CHARACTER-indexed string drops the first N characters of this spawn's own
    # slice once the persistent logfile has accumulated any non-ASCII byte (it currently carries 6). Read
    # bytes, slice, THEN decode, so the offset and the slice are in the same unit.
    content = LOG_FILE.read_bytes()[spawned_backend.log_offset_before:].decode(errors="replace")
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

    # iter-8 AUDIT (T1 fix): these four lines are TC-17's actual assertions. The iter-8 dev diff inserted
    # the whole heavy-ingest block BETWEEN the line above and this one, which (a) left TC-17 asserting only
    # "the process died" — silently deleting the clean-shutdown-absence check it exists for, while still
    # reporting green — and (b) grafted them onto the new heavy test, where `spawned_backend` is not a
    # parameter (guaranteed NameError). Restored here, unchanged except for the byte-offset slice (T2).
    content_after = LOG_FILE.read_bytes()[spawned_backend.log_offset_before:].decode(errors="replace")
    assert "start-backend.sh: launching at" in content_after  # this spawn's own boot IS in its own slice
    for phrase in ("Shutting down", "Application shutdown complete", "Finished server process"):
        assert phrase not in content_after, (
            f"unexpected clean-shutdown phrase {phrase!r} after this spawn's own simulated SIGKILL"
        )


# ==================================================================================================
# ops-hardening iter-8 (J-05 REGRESSION recovery, TC-1/TC-2): a REAL back-to-back heavy ingest — a
# full-universe `rebuild` immediately followed by a second heavy `backfill` in the SAME long-lived
# process — must stay under the enforced `memory_cap_mb` `ulimit -v` ceiling with margin, and
# `GET /api/health` must stay responsive throughout. This is the literal scenario that broke in iter-7
# (`runs/goal-session-ops-hardening/iter-7/eval.md`: 7+ minute health hang, worker-thread `MemoryError`,
# manual restart required). Runs on a THROWAWAY COPY of the real dev DB (mirrors `reports/perf-budgets.md`
# Item L/H's own established methodology) — never the shared committed file.
# ==================================================================================================
@dataclass
class ThrowawayBackend:
    pid: int
    port: int
    scratch_db: Path
    scratch_config: Path


@pytest.fixture()
def spawned_backend_throwaway_db(tmp_path):
    """Like `spawned_backend`, but launched against a THROWAWAY COPY of the real dev DB (copied, along
    with its WAL/SHM sidecars, to `tmp_path`) via a scratch `config.yaml` with ONLY `database.url`
    rewritten — every other setting (`server.memory_cap_mb`, `malloc_arena_max`, `walk_forward.horizons`,
    `snapshot_cadence`, etc.) is the REAL committed config, unchanged, so the enforced `ulimit -v` and the
    finalize hook's warm scope exactly match production. Skips (never fails) if the real dev DB is not
    present — this test needs real, substantial seed-derived data to be a meaningful capacity proof, not a
    tiny hand-built fixture."""
    # iter-8 AUDIT (T3 fix): OPT-IN ONLY. Unguarded, this fixture makes every plain
    # `pytest tests/test_start_backend_script.py` run a REAL full-universe rebuild (~16 min, Item L) on a
    # 2.5 GB DB copy — which is exactly what the DoD's own TC-8 command does, and what QA observed timing
    # out mid-run. It is also the literal workload this host hard-reset under on 2026-07-21
    # (`project-extensions/host-guard/README.md`), so it must never start by accident. Set
    # TRENDORA_RUN_HEAVY_INGEST_TEST=1 to run it deliberately, under the host-guard protections.
    if os.environ.get("TRENDORA_RUN_HEAVY_INGEST_TEST") != "1":
        pytest.skip(
            "heavy real-process back-to-back ingest test is opt-in — set TRENDORA_RUN_HEAVY_INGEST_TEST=1 "
            "(run it only on an idle host with the host-guard protections active)"
        )
    if not SCRIPT.exists():
        pytest.skip(f"{SCRIPT} not found")
    if not REAL_DB.exists():
        pytest.skip(f"real dev DB not found at {REAL_DB} — nothing to copy for a real capacity measurement")

    scratch_db = tmp_path / "throwaway.db"
    for suffix in ("", "-wal", "-shm"):
        src = Path(str(REAL_DB) + suffix)
        if src.exists():
            shutil.copy2(src, Path(str(scratch_db) + suffix))

    scratch_config = tmp_path / "throwaway-config.yaml"
    real_cfg_text = REAL_CONFIG.read_text()
    new_cfg_text, n = re.subn(
        r'url:\s*"sqlite:///apps/backend/data/trendora\.db"',
        f'url: "sqlite:///{scratch_db}"',
        real_cfg_text,
        count=1,
    )
    assert n == 1, "expected exactly one database.url line to rewrite in the real config.yaml"
    scratch_config.write_text(new_cfg_text)

    env = dict(os.environ)
    env["CHAIN_BACKEND_PORT"] = str(_HEAVY_TEST_PORT)
    env["CHAIN_FRONTEND_PORT"] = str(_HEAVY_TEST_PORT + 1000)
    env["TRENDORA_CONFIG"] = str(scratch_config)
    proc = subprocess.Popen(
        ["bash", str(SCRIPT)], cwd=str(REPO_ROOT), env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_health(_HEAVY_TEST_PORT, timeout=60.0)
        yield ThrowawayBackend(
            pid=proc.pid, port=_HEAVY_TEST_PORT, scratch_db=scratch_db, scratch_config=scratch_config
        )
    finally:
        if _pid_alive(proc.pid):
            os.kill(proc.pid, signal.SIGTERM)
            deadline = time.monotonic() + 15.0
            while _pid_alive(proc.pid) and time.monotonic() < deadline:
                time.sleep(0.2)
            if _pid_alive(proc.pid):
                os.kill(proc.pid, signal.SIGKILL)
        try:
            proc.wait(timeout=10)
        except ChildProcessError:
            pass
        # tmp_path (pytest's own per-test fixture) is cleaned up by pytest itself; nothing else to remove.


def _read_proc_status_kb(pid: int) -> dict[str, int]:
    """Parse `/proc/<pid>/status`'s VmPeak/VmSize/VmRSS/VmHWM rows -> kB ints. Gone process -> {}."""
    out: dict[str, int] = {}
    try:
        with open(f"/proc/{pid}/status") as fh:
            for line in fh:
                for key in ("VmPeak", "VmSize", "VmRSS", "VmHWM"):
                    if line.startswith(key + ":"):
                        out[key] = int(line.split()[1])
    except (FileNotFoundError, ProcessLookupError):
        return {}
    return out


class _MemSampler(threading.Thread):
    """Background thread: samples `/proc/<pid>/status` every 0.25s until stopped (mirrors
    `reports/perf-budgets.md` Item L/H's own sampling cadence)."""

    def __init__(self, pid: int):
        super().__init__(daemon=True)
        self.pid = pid
        # NOTE: named `_stop_event`, NOT `_stop` — `threading.Thread` already owns a private `_stop()`
        # method internally; shadowing it with an instance attribute breaks `Thread.join()`.
        self._stop_event = threading.Event()
        self.samples: list[dict] = []

    def run(self) -> None:
        while not self._stop_event.is_set():
            row = _read_proc_status_kb(self.pid)
            if row:
                self.samples.append(row)
            time.sleep(0.25)

    def stop(self) -> None:
        self._stop_event.set()

    def peak(self, key: str) -> int:
        vals = [s[key] for s in self.samples if key in s]
        return max(vals) if vals else 0


class _HealthPoller(threading.Thread):
    """Background thread: polls `GET /api/health` every ~2s until stopped, recording status + elapsed."""

    def __init__(self, port: int):
        super().__init__(daemon=True)
        self.port = port
        self._stop_event = threading.Event()  # see `_MemSampler`'s note on why not `_stop`
        self.results: list[dict] = []

    def run(self) -> None:
        while not self._stop_event.is_set():
            start = time.monotonic()
            try:
                resp = httpx.get(f"http://127.0.0.1:{self.port}/api/health", timeout=10.0)
                self.results.append({"status": resp.status_code, "elapsed": time.monotonic() - start})
            except Exception as exc:  # noqa: BLE001 — a timeout/refused connect IS the failure signal
                self.results.append({"status": None, "elapsed": time.monotonic() - start, "error": str(exc)})
            time.sleep(2.0)

    def stop(self) -> None:
        self._stop_event.set()


def _post_job(port: int, kind: str, start: str, end: str) -> str:
    resp = httpx.post(
        f"http://127.0.0.1:{port}/api/data/jobs", json={"kind": kind, "start": start, "end": end},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["job_id"]


def _poll_job_to_terminal(port: int, job_id: str, timeout_s: float) -> dict:
    deadline = time.monotonic() + timeout_s
    last: dict = {}
    while time.monotonic() < deadline:
        resp = httpx.get(f"http://127.0.0.1:{port}/api/data/jobs/{job_id}", timeout=10.0)
        resp.raise_for_status()
        last = resp.json()
        if last.get("status") in ("ok", "partial", "failed"):
            return last
        time.sleep(1.0)
    raise AssertionError(f"job {job_id} did not reach terminal status within {timeout_s}s; last={last}")


def test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap(spawned_backend_throwaway_db):
    """TC-1/TC-2 — the literal iter-7 regression scenario, reproduced live and hardened: a full-universe
    `rebuild` (exercises the finalize hook's per-date coverage/market-phase loops + all configured
    forward-aggregate horizons + every ledger claim's drawdown-expectations warm at full scale — Item L
    measured ~378 snapshot dates / ~16 min on this real DB) immediately followed by a second heavy
    `backfill` for a genuine non-cadence historical date (`2010-07-15` — the SAME date iter-7's browser-qa
    session used, which the rebuild's monthly/daily cadence does not itself touch, so this creates real new
    snapshot/forward-return work through the SAME finalize hook a second time) in the SAME spawned process.
    `/proc/<pid>/status` is sampled every 0.25s throughout both jobs; `GET /api/health` is polled every 2s
    throughout. Asserts: both jobs reach a terminal (non-`failed`) status, peak VmPeak/VmSize stay under
    `server.memory_cap_mb` with margin, and every health poll returns HTTP 200 (zero timeouts, zero
    hangs)."""
    from app.config import get_config

    backend = spawned_backend_throwaway_db
    cfg = get_config()
    cap_kb = cfg.server.memory_cap_mb * 1024

    mem = _MemSampler(backend.pid)
    mem.start()
    health = _HealthPoller(backend.port)
    health.start()
    try:
        job_id_1 = _post_job(backend.port, "rebuild", "2024-01-01", "2024-01-01")
        job1 = _poll_job_to_terminal(backend.port, job_id_1, timeout_s=1800.0)
        assert job1.get("status") in ("ok", "partial"), f"rebuild job did not succeed: {job1}"

        job_id_2 = _post_job(backend.port, "backfill", "2010-07-15", "2010-07-15")
        job2 = _poll_job_to_terminal(backend.port, job_id_2, timeout_s=600.0)
        assert job2.get("status") in ("ok", "partial"), f"second backfill job did not succeed: {job2}"

        time.sleep(3.0)  # settle window so any tail allocation/gc shows up in the sampled peak too
    finally:
        mem.stop()
        mem.join(timeout=5)
        health.stop()
        health.join(timeout=5)

    peak_vmpeak = mem.peak("VmPeak")
    peak_vmsize = mem.peak("VmSize")
    assert mem.samples, "expected at least one /proc/<pid>/status sample across the whole run"
    assert peak_vmpeak < cap_kb, (
        f"peak VmPeak {peak_vmpeak} KB ({peak_vmpeak / 1024:.1f} MB) reached/exceeded the "
        f"{cap_kb} KB ({cfg.server.memory_cap_mb} MB) ulimit -v cap — the iter-7 regression is NOT resolved"
    )
    assert peak_vmsize < cap_kb, f"peak VmSize {peak_vmsize} KB reached/exceeded the {cap_kb} KB cap"

    assert health.results, "expected at least one GET /api/health poll across the whole run"
    non_200_or_error = [r for r in health.results if r["status"] != 200]
    assert not non_200_or_error, (
        f"expected EVERY health poll to be HTTP 200 with zero timeouts/hangs; got "
        f"{len(non_200_or_error)}/{len(health.results)} non-200-or-error polls: {non_200_or_error[:5]}"
    )
