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
`test_forward_testing.py`'s session-scoped 30-year seed rebuild).

ops-hardening iter-9 (AG-10 launcher-cap closure) adds TC-7/TC-8/TC-9: real-process verification that
`scripts/start-backend.sh` AND `scripts/dev.sh`'s backend subshell apply the SMT-aware `taskset` CPU-
affinity mask + BLAS/OMP/numexpr thread caps declared in `project-extensions/host-guard/host-guard.env`
(TC-7/TC-8), that `dev.sh`'s frontend (`next dev`) subshell never receives any of them (TC-8), and that
both scripts still start cleanly with zero caps applied when host-guard.env is absent or disabled (TC-9).
Every TC-7/8/9 test resolves the launched process's PID via `lsof` on its listening port rather than
trusting a launching shell's own PID — `uvicorn --reload` (dev.sh) and `next dev` both fork a further
worker/server subprocess that is the one actually bound to the port, and CPU affinity / environment are
inherited across that `fork()` regardless of which PID in the chain is checked. Tests that need to prove
"no cap was added" compare against THIS TEST PROCESS'S OWN unmodified affinity/environment (not a
hardcoded assumption about the host's full CPU set or ambient env), since goal-mode's own engine-wrap can
already confine the whole session to the same mask host-guard.env declares — a coincidental match must
never be misread as "dev.sh applied it independently"."""
from __future__ import annotations

import csv
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
# A FOURTH pair of ports for the dev.sh launcher-cap test (TC-8) below.
_DEV_SCRIPT = REPO_ROOT / "scripts" / "dev.sh"
_DEVSCRIPT_BACKEND_PORT = 18700 + _offset
_DEVSCRIPT_FRONTEND_PORT = 19700 + _offset
# A FIFTH port for the "caps absent/disabled" launcher test (TC-9) below.
_NOCAP_TEST_PORT = 18800 + _offset

# ops-hardening iter-9 (AG-10): the real, committed host-guard config this project runs under.
HOST_GUARD_ENV_FILE = REPO_ROOT / "project-extensions" / "host-guard" / "host-guard.env"

# ops-hardening iter-9 (T4): the finalize hook's full aggregate-category vocabulary
# (`_refresh_ingest_aggregates`'s own docstring, `apps/backend/app/engine/data_manager.py`) — asserted
# complete for BOTH the rebuild and the backfill job below (iter-8's own live measurement observed all 7
# categories for both job kinds on this real DB; a job that early-aborted a warm loop on `MemoryError`
# would honestly omit one or more of these, which is exactly what this tightened assertion catches).
_ALL_AGGREGATE_CATEGORIES = frozenset(
    {
        "latest_snapshot",
        "coverage",
        "membership_timeline",
        "market_phase",
        "forward_aggregates",
        "research_hot_keys",
        "drawdown_expectations",
    }
)

# ops-hardening iter-9 AUDIT (T3): the two categories the finalize hook can only refresh when the job
# actually PERSISTED at least one new snapshot — `latest_snapshot` is gated on `if prog.new_snapshot_dates:`
# and `market_phase` iterates `for d in prog.new_snapshot_dates:` (`data_manager._refresh_ingest_aggregates`).
# A ZERO-WORK job (every requested date already snapshotted) therefore honestly reports only the other five;
# demanding all seven of it would be a FALSE regression signal, not a caught early-abort. The test below
# keeps the full seven-category bar wherever real snapshot work happened, and separately asserts that the
# backfill job it controls DID do real work — so "my scenario went stale" fails loudly and specifically
# instead of masquerading as a MemoryError early-abort.
_SNAPSHOT_DEPENDENT_CATEGORIES = frozenset({"latest_snapshot", "market_phase"})


def _expected_aggregate_categories(job: dict) -> frozenset[str]:
    """The categories `_refresh_ingest_aggregates` can honestly have refreshed for THIS job's outcome:
    all seven when the job created >= 1 new snapshot, otherwise the five that do not depend on
    `prog.new_snapshot_dates`."""
    return (
        _ALL_AGGREGATE_CATEGORIES
        if (job.get("snapshots_created") or 0) > 0
        else _ALL_AGGREGATE_CATEGORIES - _SNAPSHOT_DEPENDENT_CATEGORIES
    )


def _read_host_guard_env(path: Path) -> dict[str, str]:
    """Parse the plain `KEY=VALUE` (optionally quoted) lines of a host-guard.env-shaped file — no shell
    evaluation, just enough to compare a launched process's real /proc state against the declared values."""
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
    """Parse a `/proc/<pid>/status` `Cpus_allowed_list` (or a `HOST_GUARD_CPU_LIST`) value like
    `"0-3,8-11"` into the set of individual CPU indices `{0,1,2,3,8,9,10,11}`."""
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


def _read_proc_limits_max_address_space_bytes(pid: int) -> int:
    """Parse `/proc/<pid>/limits`'s "Max address space" row -> the soft limit in bytes (RLIMIT_AS)."""
    with open(f"/proc/{pid}/limits") as fh:
        for line in fh:
            if line.startswith("Max address space"):
                parts = line.split()
                # "Max address space         <soft>         <hard>         bytes"
                return int(parts[3])
    raise AssertionError(f"no 'Max address space' row in /proc/{pid}/limits")


def _read_proc_limits_max_address_space_raw(pid: int) -> str:
    """Like `_read_proc_limits_max_address_space_bytes`, but returns the RAW soft-limit field
    ("unlimited" or a byte string) instead of parsing it as an int — for callers that only need to
    compare against/detect the unrestricted case, which is not itself a number."""
    with open(f"/proc/{pid}/limits") as fh:
        for line in fh:
            if line.startswith("Max address space"):
                return line.split()[3]
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
                row["ts"] = time.time()
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


def _write_run_evidence(base: Path, mem: "_MemSampler", health: "_HealthPoller") -> None:
    """ops-hardening iter-9 (DoD item 5): retain THIS run's raw samples as CSV next to the iteration's
    other artifacts. `base` is the path named by TRENDORA_HEAVY_INGEST_SAMPLER_CSV; the health-poll
    timings are written beside it as `<stem>-health.csv`. Written from the test's `finally` block, so the
    evidence survives a failing assertion (a failed heavy run is exactly when the samples matter most)."""
    base.parent.mkdir(parents=True, exist_ok=True)
    with base.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["epoch", "vmpeak_kb", "vmsize_kb", "vmrss_kb", "vmhwm_kb"])
        for s in mem.samples:
            w.writerow([f"{s.get('ts', 0):.3f}", s.get("VmPeak", ""), s.get("VmSize", ""),
                        s.get("VmRSS", ""), s.get("VmHWM", "")])
    health_csv = base.with_name(base.stem + "-health.csv")
    with health_csv.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["poll_index", "http_status", "elapsed_s", "error"])
        for i, r in enumerate(health.results):
            w.writerow([i, r.get("status", ""), f"{r.get('elapsed', 0):.3f}", r.get("error", "")])


def _post_job(port: int, kind: str, start: str, end: str) -> str:
    resp = httpx.post(
        f"http://127.0.0.1:{port}/api/data/jobs", json={"kind": kind, "start": start, "end": end},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["job_id"]


def _pick_unsnapshotted_trading_day(port: int, cfg) -> str:
    """ops-hardening iter-9 AUDIT (T3) — choose the heavy backfill's target date AT RUN TIME instead of
    hardcoding one that silently goes stale.

    A hardcoded date (previously `2010-07-15`) stops being new work the moment anything snapshots it: the
    ingest orchestrator drops already-snapshotted dates from `targets` and returns early when none remain
    (`data_manager._backfill_snapshots`), so the job becomes a zero-work no-op that can never exercise the
    per-item warm loops this test exists to measure — and the seven-category completeness assertion below
    then fails for a reason that has nothing to do with a `MemoryError` early-abort.

    The candidate set is read from the SPAWNED INSTANCE's own `GET /api/data/availability`, i.e. the same
    benchmark trading calendar (`_trading_days`) and the same `ScannerRun.asof_date` snapshot set the
    orchestrator's target selection reads — never a second derivation here. Candidates keep at least
    `max(walk_forward.horizons)` trading days of calendar after them so the finalize hook's forward-return
    and forward-aggregate work is real rather than truncated at the end of the calendar, and the LATEST
    such day is chosen (maximum available history for the scan). No date literal, no magic number."""
    resp = httpx.get(f"http://127.0.0.1:{port}/api/data/availability", timeout=120.0)
    resp.raise_for_status()
    cells = resp.json().get("cells") or []
    lookahead = max(cfg.walk_forward.horizons)
    candidates = [
        c for c in cells[:-lookahead]
        if not c.get("snapshot_exists") and (c.get("symbols_with_bars") or 0) > 0
    ]
    if not candidates:
        pytest.skip(
            f"no unsnapshotted trading day with bars and >= {lookahead} trading days of following calendar "
            f"remains in this DB copy ({len(cells)} trading days) — there is no genuine new-snapshot work "
            "left for the second heavy job, so this run could only measure a zero-work no-op"
        )
    return candidates[-1]["date"]


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
    `backfill` for a genuine non-cadence historical date, SELECTED AT RUN TIME from the spawned instance's
    own availability map (ops-hardening iter-9 audit T3 — a hardcoded date silently decays into a zero-work
    no-op as soon as anything snapshots it), so this creates real new snapshot/forward-return work through
    the SAME finalize hook a second time in the SAME spawned process.
    `/proc/<pid>/status` is sampled every 0.25s throughout both jobs; `GET /api/health` is polled every 2s
    throughout. Asserts: both jobs reach status `"ok"` — NOT `"partial"` (ops-hardening iter-9, T4: a
    `"partial"` result here would mean a per-item warm loop silently early-aborted on `MemoryError` during
    THIS run, which is exactly the failure this test exists to catch, not tolerate) — with a COMPLETE
    `aggregates_refreshed` list for each job's kind, peak VmPeak/VmSize under `server.memory_cap_mb` with
    margin, and every health poll returning HTTP 200 (zero timeouts, zero hangs)."""
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
        # ops-hardening iter-9 (T4): reject "partial" — a partial status here means a per-item warm loop
        # early-aborted on MemoryError during THIS live run, which this test exists to catch, not accept.
        assert job1.get("status") == "ok", f"rebuild job did not reach status 'ok': {job1}"

        # ops-hardening iter-9 AUDIT (T3): pick the second job's date AFTER the rebuild has committed its
        # own snapshots, so the choice reflects the DB state this backfill will actually face.
        backfill_date = _pick_unsnapshotted_trading_day(backend.port, cfg)
        job_id_2 = _post_job(backend.port, "backfill", backfill_date, backfill_date)
        job2 = _poll_job_to_terminal(backend.port, job_id_2, timeout_s=600.0)
        assert job2.get("status") == "ok", f"second backfill job did not reach status 'ok': {job2}"
        # The scenario-integrity guard: this job was aimed at a date with no snapshot, so it MUST have
        # created one. A zero-work no-op here would exercise none of the per-item warm loops this test
        # measures — fail loudly on that, rather than letting it surface later as a missing-category error.
        assert (job2.get("snapshots_created") or 0) >= 1, (
            f"backfill of {backfill_date} created no snapshot ({job2.get('snapshots_created')}) — the "
            f"second heavy job did zero work, so this run proves nothing about warm-loop survival: {job2}"
        )

        time.sleep(3.0)  # settle window so any tail allocation/gc shows up in the sampled peak too
    finally:
        mem.stop()
        mem.join(timeout=5)
        health.stop()
        health.join(timeout=5)
        sampler_csv = os.environ.get("TRENDORA_HEAVY_INGEST_SAMPLER_CSV")
        if sampler_csv:
            _write_run_evidence(Path(sampler_csv), mem, health)
        print(
            f"\n[heavy-ingest] samples={len(mem.samples)} peak_VmPeak_kb={mem.peak('VmPeak')} "
            f"peak_VmSize_kb={mem.peak('VmSize')} peak_VmRSS_kb={mem.peak('VmRSS')} "
            f"cap_kb={cap_kb} health_polls={len(health.results)} "
            f"health_non_200={len([r for r in health.results if r['status'] != 200])} "
            f"health_max_elapsed_s={max((r['elapsed'] for r in health.results), default=0):.3f}"
        )

    # ops-hardening iter-9 (T4): each job's persisted `aggregates_refreshed` list must contain EVERY
    # category the finalize hook can refresh FOR THAT JOB'S OUTCOME — a partial list (even with status
    # "ok", which the honesty gate allows since aggregate-refresh failures are non-fatal to the job) would
    # mean one of the four per-item warm loops silently early-aborted on MemoryError during this run
    # without failing the job. The expected set is all seven whenever the job persisted a new snapshot and
    # the five snapshot-independent ones otherwise (audit T3 — see `_expected_aggregate_categories`); job2
    # is asserted above to have done real work, so it is always held to the full seven.
    missing_1 = _expected_aggregate_categories(job1) - set(job1.get("aggregates_refreshed") or [])
    assert not missing_1, (
        f"rebuild job's aggregates_refreshed is missing categories: {sorted(missing_1)} "
        f"(got {job1.get('aggregates_refreshed')}) — a per-item warm loop may have early-aborted"
    )
    missing_2 = _expected_aggregate_categories(job2) - set(job2.get("aggregates_refreshed") or [])
    assert not missing_2, (
        f"backfill job's aggregates_refreshed is missing categories: {sorted(missing_2)} "
        f"(got {job2.get('aggregates_refreshed')}) — a per-item warm loop may have early-aborted"
    )

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


# ==================================================================================================
# ops-hardening iter-9 (AG-10 launcher-cap closure) — TC-7 / TC-8 / TC-9.
# ==================================================================================================

_HOST_GUARD_BLAS_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")


def _owning_pid(port: int, timeout: float = 20.0) -> int:
    """The PID actually bound to `port`'s listening socket — the robust way to find the real worker
    process regardless of how many `fork`/`exec` hops a launcher's supervisor (uvicorn `--reload`,
    `next dev`) put between the launching shell and it. Tries `lsof` first (works for the uvicorn
    reloader/worker); a Next.js dev server's listening socket is not always attributable via `lsof -ti`
    on this platform, so `ss -tlnp` (own-process sockets are visible without root) is the fallback.
    Retries briefly either way: a dev frontend can briefly hand the listening socket to a different
    process right around its first response (HMR-related rebuild)."""
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


def _wait_for_port_answering(port: int, timeout: float) -> None:
    """Wait until ANY HTTP response (even non-200 — a dev frontend's first request can 404/redirect
    before it has fully settled) comes back from `port` — proof something is bound and serving."""
    deadline = time.monotonic() + timeout
    last_exc: Exception | None = None
    while time.monotonic() < deadline:
        try:
            httpx.get(f"http://127.0.0.1:{port}/", timeout=2.0)
            return
        except Exception as exc:  # noqa: BLE001 — keep polling until the deadline
            last_exc = exc
        time.sleep(0.5)
    raise AssertionError(f"nothing answered on :{port} within {timeout}s (last error: {last_exc})")


def test_start_backend_applies_host_guard_caps_when_enabled(spawned_backend):
    """TC-7 — with the committed `project-extensions/host-guard/host-guard.env` present and
    `HOST_GUARD_ENABLED=1`, `scripts/start-backend.sh`'s launched process's `Cpus_allowed_list` matches
    `HOST_GUARD_CPU_LIST` and its environment carries the BLAS/OMP/numexpr thread-cap vars set to
    `HOST_GUARD_BLAS_THREADS`."""
    if not HOST_GUARD_ENV_FILE.exists():
        pytest.skip(f"{HOST_GUARD_ENV_FILE} not present — host-guard is optional, nothing to verify")
    hg = _read_host_guard_env(HOST_GUARD_ENV_FILE)
    if hg.get("HOST_GUARD_ENABLED") != "1":
        pytest.skip("HOST_GUARD_ENABLED != 1 in the committed host-guard.env — nothing to verify")

    pid = spawned_backend.pid
    expected_cpus = _parse_cpu_list(hg["HOST_GUARD_CPU_LIST"])
    actual_cpus = _parse_cpu_list(_read_proc_status_cpus_allowed(pid))
    assert actual_cpus == expected_cpus, (
        f"expected Cpus_allowed_list to match HOST_GUARD_CPU_LIST {hg['HOST_GUARD_CPU_LIST']!r} "
        f"({sorted(expected_cpus)}), got {sorted(actual_cpus)}"
    )
    env = _read_proc_environ(pid)
    for var in _HOST_GUARD_BLAS_VARS:
        assert env.get(var) == hg["HOST_GUARD_BLAS_THREADS"], (
            f"expected {var}={hg['HOST_GUARD_BLAS_THREADS']!r} (HOST_GUARD_BLAS_THREADS), "
            f"got {env.get(var)!r}"
        )


def test_dev_script_applies_host_guard_caps_to_backend_only(request):
    """TC-8 — with the committed host-guard.env present and enabled, `scripts/dev.sh`'s backend subshell
    launches uvicorn under the SAME CPU-affinity mask + BLAS/OMP/numexpr thread caps as
    `scripts/start-backend.sh`, plus the mirrored `ulimit -v` / `MALLOC_ARENA_MAX` enforcement — while the
    SAME script's frontend (`next dev`) subshell shows none of the host-guard caps and no memory/arena
    restriction."""
    if not HOST_GUARD_ENV_FILE.exists():
        pytest.skip(f"{HOST_GUARD_ENV_FILE} not present — host-guard is optional, nothing to verify")
    hg = _read_host_guard_env(HOST_GUARD_ENV_FILE)
    if hg.get("HOST_GUARD_ENABLED") != "1":
        pytest.skip("HOST_GUARD_ENABLED != 1 in the committed host-guard.env — nothing to verify")
    if not _DEV_SCRIPT.exists():
        pytest.skip(f"{_DEV_SCRIPT} not found")
    if not (REPO_ROOT / "apps" / "frontend" / "node_modules").exists():
        pytest.skip("apps/frontend/node_modules not installed — cannot start the frontend for this check")

    from app.config import get_config

    cfg = get_config()
    expected_cap_bytes = cfg.server.memory_cap_mb * 1024 * 1024
    expected_arena = str(cfg.server.malloc_arena_max)
    expected_cpus = _parse_cpu_list(hg["HOST_GUARD_CPU_LIST"])

    env = dict(os.environ)
    env["CHAIN_BACKEND_PORT"] = str(_DEVSCRIPT_BACKEND_PORT)
    env["CHAIN_FRONTEND_PORT"] = str(_DEVSCRIPT_FRONTEND_PORT)
    proc = subprocess.Popen(
        ["bash", str(_DEV_SCRIPT)], cwd=str(REPO_ROOT), env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,  # own process group -> teardown kills the WHOLE tree, not just this PID
    )

    def _cleanup():
        try:
            pgid = os.getpgid(proc.pid)
        except ProcessLookupError:
            return
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(pgid, sig)
            except ProcessLookupError:
                return
            deadline = time.monotonic() + 10.0
            while time.monotonic() < deadline:
                try:
                    os.killpg(pgid, 0)
                except ProcessLookupError:
                    return
                time.sleep(0.2)
        try:
            proc.wait(timeout=10)
        except (ChildProcessError, subprocess.TimeoutExpired):
            pass

    request.addfinalizer(_cleanup)

    _wait_for_health(_DEVSCRIPT_BACKEND_PORT, timeout=60.0)
    backend_pid = _owning_pid(_DEVSCRIPT_BACKEND_PORT)

    actual_cpus = _parse_cpu_list(_read_proc_status_cpus_allowed(backend_pid))
    assert actual_cpus == expected_cpus, (
        f"dev.sh backend: expected Cpus_allowed_list {sorted(expected_cpus)}, got {sorted(actual_cpus)}"
    )
    backend_env = _read_proc_environ(backend_pid)
    for var in _HOST_GUARD_BLAS_VARS:
        assert backend_env.get(var) == hg["HOST_GUARD_BLAS_THREADS"], (
            f"dev.sh backend: expected {var}={hg['HOST_GUARD_BLAS_THREADS']!r}, "
            f"got {backend_env.get(var)!r}"
        )
    assert backend_env.get("MALLOC_ARENA_MAX") == expected_arena, (
        f"dev.sh backend: expected MALLOC_ARENA_MAX={expected_arena!r}, "
        f"got {backend_env.get('MALLOC_ARENA_MAX')!r}"
    )
    soft_limit = _read_proc_limits_max_address_space_bytes(backend_pid)
    assert soft_limit == expected_cap_bytes, (
        f"dev.sh backend: expected RLIMIT_AS {expected_cap_bytes} bytes, got {soft_limit}"
    )

    # Frontend: wait for it to actually answer, then assert NONE of the backend-only caps landed there.
    _wait_for_port_answering(_DEVSCRIPT_FRONTEND_PORT, timeout=90.0)
    frontend_pid = _owning_pid(_DEVSCRIPT_FRONTEND_PORT)
    frontend_env = _read_proc_environ(frontend_pid)
    assert "MALLOC_ARENA_MAX" not in frontend_env, (
        "dev.sh frontend subshell must never receive MALLOC_ARENA_MAX — that cap is backend-only"
    )
    # `Max address space` reads literally "unlimited" (not a number) when no ulimit is applied at all —
    # the expected frontend state — so this compares the RAW field rather than the numeric parser above
    # (which assumes a numeric value and would raise on "unlimited").
    frontend_limit_raw = _read_proc_limits_max_address_space_raw(frontend_pid)
    assert frontend_limit_raw != str(expected_cap_bytes), (
        f"dev.sh frontend subshell must not be constrained by the backend's memory_cap_mb ulimit "
        f"(got Max address space = {frontend_limit_raw!r})"
    )
    # No taskset call is ever issued for the frontend subshell, so its affinity must be exactly whatever
    # THIS test process itself already has (unmodified) — not assumed to be the host's full CPU set (this
    # test may itself run inside an outer engine-level taskset wrap) and not assumed to differ from
    # HOST_GUARD_CPU_LIST (a coincidental match on an already-narrowly-wrapped host is possible).
    own_cpus = os.sched_getaffinity(0)
    frontend_cpus = _parse_cpu_list(_read_proc_status_cpus_allowed(frontend_pid))
    assert frontend_cpus == own_cpus, (
        f"dev.sh frontend subshell's CPU affinity {sorted(frontend_cpus)} differs from this test "
        f"process's own unmodified affinity {sorted(own_cpus)} — dev.sh must not taskset the frontend"
    )


def test_start_backend_host_guard_absent_starts_cleanly_with_no_caps(tmp_path):
    """TC-9 (absent) — with `HOST_GUARD_ENV_FILE` pointing at a nonexistent path (simulating
    host-guard.env being absent, WITHOUT ever touching the real committed file — see the module
    docstring for why), `start-backend.sh` starts cleanly with no CPU-affinity restriction and no change
    to the BLAS/OMP/numexpr thread-cap vars beyond whatever this test process's own ambient env already
    carries."""
    missing = tmp_path / "no-such-host-guard.env"
    assert not missing.exists()
    own_cpus = os.sched_getaffinity(0)
    ambient_blas = {v: os.environ.get(v) for v in _HOST_GUARD_BLAS_VARS}

    env = dict(os.environ)
    env["CHAIN_BACKEND_PORT"] = str(_NOCAP_TEST_PORT)
    env["CHAIN_FRONTEND_PORT"] = str(_NOCAP_TEST_PORT + 1000)
    env["HOST_GUARD_ENV_FILE"] = str(missing)
    proc = subprocess.Popen(
        ["bash", str(SCRIPT)], cwd=str(REPO_ROOT), env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_health(_NOCAP_TEST_PORT, timeout=60.0)
        assert proc.poll() is None, "backend must still be running (no crash) with host-guard.env absent"
        cpus = _parse_cpu_list(_read_proc_status_cpus_allowed(proc.pid))
        assert cpus == own_cpus, (
            "no CPU-affinity restriction should be applied when host-guard.env is absent"
        )
        penv = _read_proc_environ(proc.pid)
        for var, ambient_val in ambient_blas.items():
            assert penv.get(var) == ambient_val, (
                f"host-guard.env absent must not change {var} (ambient {ambient_val!r}, "
                f"got {penv.get(var)!r})"
            )
    finally:
        if _pid_alive(proc.pid):
            os.kill(proc.pid, signal.SIGKILL)
            deadline = time.monotonic() + 10.0
            while _pid_alive(proc.pid) and time.monotonic() < deadline:
                time.sleep(0.1)
        try:
            proc.wait(timeout=10)
        except ChildProcessError:
            pass


def test_start_backend_host_guard_disabled_starts_cleanly_with_no_caps(tmp_path):
    """TC-9 (disabled) — with a scratch copy of the real host-guard.env whose ONLY change is
    `HOST_GUARD_ENABLED=0` (never the real committed file), `start-backend.sh` starts cleanly with no
    CPU-affinity restriction and no change to the BLAS/OMP/numexpr thread-cap vars."""
    if not HOST_GUARD_ENV_FILE.exists():
        pytest.skip(f"{HOST_GUARD_ENV_FILE} not present — nothing to disable")
    real_text = HOST_GUARD_ENV_FILE.read_text()
    disabled_text, n = re.subn(
        r"^HOST_GUARD_ENABLED=.*$", "HOST_GUARD_ENABLED=0", real_text, count=1, flags=re.MULTILINE
    )
    assert n == 1, "expected exactly one HOST_GUARD_ENABLED= line in the committed host-guard.env"
    scratch = tmp_path / "host-guard-disabled.env"
    scratch.write_text(disabled_text)

    own_cpus = os.sched_getaffinity(0)
    ambient_blas = {v: os.environ.get(v) for v in _HOST_GUARD_BLAS_VARS}

    env = dict(os.environ)
    env["CHAIN_BACKEND_PORT"] = str(_NOCAP_TEST_PORT + 1)
    env["CHAIN_FRONTEND_PORT"] = str(_NOCAP_TEST_PORT + 1001)
    env["HOST_GUARD_ENV_FILE"] = str(scratch)
    proc = subprocess.Popen(
        ["bash", str(SCRIPT)], cwd=str(REPO_ROOT), env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_health(_NOCAP_TEST_PORT + 1, timeout=60.0)
        assert proc.poll() is None, "backend must still be running (no crash) with host-guard disabled"
        cpus = _parse_cpu_list(_read_proc_status_cpus_allowed(proc.pid))
        assert cpus == own_cpus, "no CPU-affinity restriction should be applied when HOST_GUARD_ENABLED=0"
        penv = _read_proc_environ(proc.pid)
        for var, ambient_val in ambient_blas.items():
            assert penv.get(var) == ambient_val, (
                f"HOST_GUARD_ENABLED=0 must not change {var} (ambient {ambient_val!r}, "
                f"got {penv.get(var)!r})"
            )
    finally:
        if _pid_alive(proc.pid):
            os.kill(proc.pid, signal.SIGKILL)
            deadline = time.monotonic() + 10.0
            while _pid_alive(proc.pid) and time.monotonic() < deadline:
                time.sleep(0.1)
        try:
            proc.wait(timeout=10)
        except ChildProcessError:
            pass


def test_dev_script_host_guard_disabled_backend_starts_cleanly_with_no_caps():
    """TC-9 (dev.sh) — with a scratch, disabled copy of host-guard.env, `scripts/dev.sh`'s backend
    subshell starts cleanly with no CPU-affinity restriction and no change to the BLAS/OMP/numexpr
    thread-cap vars. Only the "disabled" sub-case is exercised here (not "absent" too, unlike
    start-backend.sh above): both branches share the exact same `if [[ -f ... ]] && [[ enabled ]]`
    no-op path in the identical HOST-GUARD block (see scripts/dev.sh), and a full dev.sh launch is a real
    frontend+backend startup — materially more expensive than start-backend.sh alone — so this proves the
    shared code path once rather than paying that cost twice for a byte-identical outcome."""
    if not HOST_GUARD_ENV_FILE.exists():
        pytest.skip(f"{HOST_GUARD_ENV_FILE} not present — nothing to disable")
    if not _DEV_SCRIPT.exists():
        pytest.skip(f"{_DEV_SCRIPT} not found")
    if not (REPO_ROOT / "apps" / "frontend" / "node_modules").exists():
        pytest.skip("apps/frontend/node_modules not installed — cannot start the frontend for this check")

    real_text = HOST_GUARD_ENV_FILE.read_text()
    disabled_text, n = re.subn(
        r"^HOST_GUARD_ENABLED=.*$", "HOST_GUARD_ENABLED=0", real_text, count=1, flags=re.MULTILINE
    )
    assert n == 1, "expected exactly one HOST_GUARD_ENABLED= line in the committed host-guard.env"

    import tempfile

    own_cpus = os.sched_getaffinity(0)
    ambient_blas = {v: os.environ.get(v) for v in _HOST_GUARD_BLAS_VARS}

    with tempfile.TemporaryDirectory() as td:
        scratch = Path(td) / "host-guard-disabled.env"
        scratch.write_text(disabled_text)

        env = dict(os.environ)
        env["CHAIN_BACKEND_PORT"] = str(_DEVSCRIPT_BACKEND_PORT + 1)
        env["CHAIN_FRONTEND_PORT"] = str(_DEVSCRIPT_FRONTEND_PORT + 1)
        env["HOST_GUARD_ENV_FILE"] = str(scratch)
        proc = subprocess.Popen(
            ["bash", str(_DEV_SCRIPT)], cwd=str(REPO_ROOT), env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid,
        )
        try:
            _wait_for_health(_DEVSCRIPT_BACKEND_PORT + 1, timeout=60.0)
            backend_pid = _owning_pid(_DEVSCRIPT_BACKEND_PORT + 1)
            cpus = _parse_cpu_list(_read_proc_status_cpus_allowed(backend_pid))
            assert cpus == own_cpus, (
                "no CPU-affinity restriction should be applied to dev.sh's backend when "
                "HOST_GUARD_ENABLED=0"
            )
            penv = _read_proc_environ(backend_pid)
            for var, ambient_val in ambient_blas.items():
                assert penv.get(var) == ambient_val, (
                    f"HOST_GUARD_ENABLED=0 must not change dev.sh backend's {var} "
                    f"(ambient {ambient_val!r}, got {penv.get(var)!r})"
                )
        finally:
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
                    while time.monotonic() < deadline:
                        try:
                            os.killpg(pgid, 0)
                        except ProcessLookupError:
                            break
                        time.sleep(0.2)
                    else:
                        continue
                    break
            try:
                proc.wait(timeout=10)
            except (ChildProcessError, subprocess.TimeoutExpired):
                pass
