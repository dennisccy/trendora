"""ops-hardening iter-47 (AG-8, iter-46 audit B3) — a REAL, non-monkeypatched induction test for
`app.engine.samples._factor_samples`'s "decile" branch, the THIRD unbounded whole-cohort site the iter-46
audit found on the `/api/evidence` serving path (the sibling of the two accumulators iter-46 already
bounded in `research.py` / `forward_testing.py`): `observations = _factor_observations(...)` (the WHOLE
horizon population) then `sorted(observations, ...)` (a whole-list sort) just to discard 9/10 of it after
slicing one decile. `logs/backend.log` caught this exact call chain `MemoryError`-ing at 02:20:31 on
2026-08-04, reached via `evidence.py` -> `compute_drawdown_expectations_cached` -> `compute_samples` ->
`_factor_samples` for a decile-scoped certified claim (5 of the live ledger's 7 claims are decile-scoped
factor claims).

WHY A REAL SUBPROCESS INDUCTION, NOT A MONKEYPATCH: mirrors `test_evidence_drawdown_memory_pressure.py`'s
established rationale — a `monkeypatch`-injected `MemoryError` proves the exception HANDLER's code path but
never proves the mechanism actually triggers under genuine OS-level virtual-memory exhaustion. This spawns
real Python subprocesses under a genuinely tightened `ulimit -v` (RLIMIT_AS), running the PINNED pre-fix
reference (whole-population `_factor_observations` + whole `sorted()` + `_decile_member_slice`) against the
shipped two-pass bounded `research._factor_decile_observations`, both driving `GET /api/evidence`'s exact
real entry point (`compute_drawdown_expectations_cached`) for the live ledger's own leadership_score/decile
10/horizon 20 claim, on a disposable COPY of the live committed seed DB.

CALIBRATION (measured on this host, `.venv` Python 3.12, claim `{kind: factor, factor: leadership_score,
slice_kind: decile, decile: 10, horizon: 20}` against the live committed seed, no cap): the pinned
pre-fix reference peaks at PEAK_RSS_KB=1,036,216 (56.7 s); the shipped two-pass bounded implementation
peaks at PEAK_RSS_KB=692,836 (80.1 s, slower — the two DB passes trade CPU/IO for the bounded memory, the
same trade-off iter-46's by-phase accumulator fix already accepted) — a real ~344 MB / ~33% peak-RSS
reduction. A `ulimit -v` of 850,000 KB reproducibly discriminates: the reference aborts with a caught
`MemoryError`, the shipped implementation completes normally (re-confirmed directly on this host at cap
=850,000 KB: reference PEAK_RSS_KB=817,920 aborted; shipped PEAK_RSS_KB=692,404 completed). 600,000 KB
starves BOTH (shipped PEAK_RSS_KB=570,620 before its own caught abort) — proving the bound reduces failure
likelihood at a given pressure level, not immunity to arbitrarily severe pressure (mirrors the sibling
drill's own disclosed residual)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_DB = REPO_ROOT / "apps/backend/data/trendora.db"
BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)

# The live ledger's OWN leadership_score/decile-10/horizon-20 claim (`runs/goal-session-mcp-loop/state/
# certified-claims.jsonl`) — the real shape `compute_drawdown_expectations_cached` resolves for every
# `GET /api/evidence` request, and the exact call chain the iter-46 audit's live `MemoryError` traced.
_CLAIM = {
    "kind": "factor", "factor": "leadership_score", "decile": 10, "slice_kind": "decile", "horizon": 20,
    "direction": "positive",
}

# Measured this iteration (see module docstring): the window that reproducibly discriminates reference
# (whole-population sort, aborts) from shipped (two-pass bounded, completes) on this host.
TIGHT_CAP_KB = 850_000
# Deep enough that BOTH implementations starve — proves the shipped code still degrades honestly (never a
# crash/wedge) rather than merely moving the failure point.
STARVED_CAP_KB = 600_000
# Comfortably clears the whole claim compute for EITHER implementation — the CONTROL cap.
CONTROL_CAP_KB = 1_600_000
BOUNDED_TIMEOUT_S = 150.0


def _skip_if_no_real_db() -> None:
    if not REAL_DB.exists():
        pytest.skip(f"real committed seed DB not found at {REAL_DB} — nothing to reproduce against")


def _fresh_seed_copy(tmp_path: Path, name: str) -> Path:
    """A FRESH, never-cache-polluted disposable copy of the live committed seed DB, ONE PER CALL — mirrors
    `test_evidence_drawdown_memory_pressure.py`'s own rationale: `compute_drawdown_expectations_cached`
    WRITES an `EventStudyCache` row on a MISS, so a copy reused across probes would silently turn a later
    probe into a trivial cache HIT. Never touches the actual committed `apps/backend/data/trendora.db`."""
    _skip_if_no_real_db()
    dest = tmp_path / name
    shutil.copyfile(REAL_DB, dest)
    return dest


# --------------------------------------------------------------------------------------------------
# Child-process probe: drives the exact `/api/evidence` entry point (`compute_drawdown_expectations_cached`)
# wrapped in the SAME `except MemoryError` isolate-and-continue pattern `evidence.py` (UNTOUCHED by this
# iteration) applies, printing an honest sentinel either way. `--reference` swaps in the pinned pre-fix
# (whole-population sort + slice) `_factor_decile_observations` via a module-level monkeypatch BEFORE the
# call — `_factor_samples` resolves the name by plain module-level lookup each call, so the swap is picked
# up with no other change (the SAME technique the sibling drawdown-memory-pressure drill uses).
# --------------------------------------------------------------------------------------------------
_CHILD_PROBE_TEMPLATE = '''
import sys
sys.path.insert(0, "__BACKEND_ROOT__")
from sqlmodel import Session, select
from app.config import load_config
from app.db import make_engine
import app.engine.forward_testing as ft
import app.engine.research as research_mod
import app.engine.samples as samples_mod
from app.models import ForwardReturn

db_path = sys.argv[1]
mode = sys.argv[2]  # "reference" or "shipped"
claim = __CLAIM__

def _reference_factor_decile_observations(session, factor, horizon, as_of, deciles_count, decile, cfg=None):
    """Pinned pre-fix body: the FULL `_factor_observations` list, sorted WHOLE, then sliced — the exact
    `_factor_samples` decile branch this iteration replaced."""
    observations = research_mod._factor_observations(session, factor, horizon, as_of, cfg=cfg)
    ordered = sorted(observations, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))
    return research_mod._decile_member_slice(ordered, deciles_count, decile)

if mode == "reference":
    samples_mod._factor_decile_observations = _reference_factor_decile_observations

cfg = load_config()
engine = make_engine(f"sqlite:///{db_path}")

# mirrors app.engine.evidence.build_evidence_payload's UNTOUCHED isolate-and-continue guard exactly.
with Session(engine) as session:
    try:
        payload = ft.compute_drawdown_expectations_cached(session, claim, cfg)
    except MemoryError:
        print("RESULT=UNAVAILABLE_MEMORYERROR")
    except Exception as exc:  # noqa: BLE001
        print(f"RESULT=UNAVAILABLE_OTHER exc={exc!r}")
    else:
        has_panel = payload is not None and "by_phase" in payload
        print(f"RESULT=OK has_panel={has_panel}")

# same-process, fresh-session read afterward -- proves no leaked lock / open transaction blocks recovery.
with Session(engine) as session:
    n = len(session.exec(select(ForwardReturn.id).limit(1)).all())
print(f"SUBSEQUENT_READ_OK n={n}")
'''


def _write_child_probe(tmp_path: Path) -> Path:
    script_path = tmp_path / "_samples_mem_probe_child.py"
    text = _CHILD_PROBE_TEMPLATE.replace("__BACKEND_ROOT__", BACKEND_ROOT).replace("__CLAIM__", repr(_CLAIM))
    script_path.write_text(text)
    return script_path


def _run_child_probe(script_path: Path, db_path: Path, mode: str, cap_kb: int) -> subprocess.CompletedProcess:
    cmd = f"ulimit -v {cap_kb}; exec {sys.executable} {script_path} {db_path} {mode}"
    return subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=BOUNDED_TIMEOUT_S)


def test_tight_cap_reference_aborts_shipped_completes(tmp_path):
    """TC-4: at the SAME tight `ulimit -v` cap, the pinned pre-fix (whole-population sort) reference
    implementation aborts with a caught `MemoryError` (the exact live iter-46 audit finding, reproduced),
    while the shipped (two-pass bounded) implementation completes and serves the real computed panel — the
    measurable failure-rate reduction TC-4 asks for, at the real per-claim live-basis scale. Each sub-call
    gets its OWN fresh DB copy (never reused) so an earlier success can never turn a later probe into a
    trivial `EventStudyCache` hit."""
    script_path = _write_child_probe(tmp_path)

    ref_db = _fresh_seed_copy(tmp_path, "ref.db")
    ref_result = _run_child_probe(script_path, ref_db, "reference", TIGHT_CAP_KB)
    assert ref_result.returncode == 0, (
        f"the reference probe must never crash uncaught; stdout={ref_result.stdout!r} stderr={ref_result.stderr!r}"
    )
    assert "RESULT=UNAVAILABLE_MEMORYERROR" in ref_result.stdout, (
        f"expected the pre-fix reference to abort with a caught MemoryError under the tight cap "
        f"(cap may be miscalibrated too loose — a control-assertion failure, not a silent pass); "
        f"stdout={ref_result.stdout!r} stderr={ref_result.stderr!r}"
    )
    assert "SUBSEQUENT_READ_OK" in ref_result.stdout

    shipped_db = _fresh_seed_copy(tmp_path, "shipped.db")
    shipped_result = _run_child_probe(script_path, shipped_db, "shipped", TIGHT_CAP_KB)
    assert shipped_result.returncode == 0, (
        f"stdout={shipped_result.stdout!r} stderr={shipped_result.stderr!r}"
    )
    assert "RESULT=OK has_panel=True" in shipped_result.stdout, (
        f"expected the shipped two-pass bounded implementation to complete normally under the SAME tight "
        f"cap that aborted the reference (cap may be miscalibrated too tight for the shipped code); "
        f"stdout={shipped_result.stdout!r} stderr={shipped_result.stderr!r}"
    )
    assert "SUBSEQUENT_READ_OK" in shipped_result.stdout


def test_control_generous_cap_both_complete_normally(tmp_path):
    """Control assertion (mirrors the sibling drawdown-memory-pressure drill's own DoD requirement): the
    IDENTICAL claim/cohort, under a generous cap, completes normally for BOTH implementations — proving the
    tight-cap abort above is attributable to the cap, not an unrelated bug. A fresh DB copy per mode."""
    script_path = _write_child_probe(tmp_path)
    for mode in ("reference", "shipped"):
        db_copy = _fresh_seed_copy(tmp_path, f"control_{mode}.db")
        result = _run_child_probe(script_path, db_copy, mode, CONTROL_CAP_KB)
        assert result.returncode == 0, f"mode={mode} stdout={result.stdout!r} stderr={result.stderr!r}"
        assert "RESULT=OK has_panel=True" in result.stdout, (
            f"the generous CONTROL cap unexpectedly failed mode={mode} — the tight-cap result cannot be "
            f"trusted as cap-attributable until this is fixed; stdout={result.stdout!r} stderr={result.stderr!r}"
        )


def test_starved_cap_shipped_still_degrades_honestly_never_crashes(tmp_path):
    """Under pressure severe enough that the SHIPPED (bounded) implementation ALSO starves, it still
    degrades exactly as honestly as the reference — a caught MemoryError, never an uncaught crash/wedge —
    the residual this iteration's own docstring discloses rather than silently claiming full immunity (the
    two-pass bound reduces failure likelihood at a given pressure level; PASS 1's own lightweight
    `sort_keys` accumulator is still O(population), so severe enough pressure still starves it)."""
    script_path = _write_child_probe(tmp_path)
    db_copy = _fresh_seed_copy(tmp_path, "starved.db")
    result = _run_child_probe(script_path, db_copy, "shipped", STARVED_CAP_KB)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "RESULT=UNAVAILABLE_MEMORYERROR" in result.stdout, (
        f"expected the shipped implementation to ALSO honestly degrade under severe enough pressure "
        f"(never a silent success that would suggest an unrealistic full bound); "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "SUBSEQUENT_READ_OK" in result.stdout, (
        "expected the SAME process to still serve a fresh read after the caught MemoryError — never a "
        f"wedge; stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_shipped_survives_five_consecutive_tight_cap_runs(tmp_path):
    """TC-4 (binding iter-44 lesson — one green run is not proof): the shipped two-pass bounded
    implementation completes normally across 5 CONSECUTIVE independent subprocess runs at the SAME tight
    cap that reliably aborts the pre-fix reference — zero `MemoryError` escapes across all 5, each with its
    OWN fresh DB copy (never reused, so no run's success is a cache-hit artifact of a prior run)."""
    script_path = _write_child_probe(tmp_path)
    outcomes = []
    for i in range(5):
        db_copy = _fresh_seed_copy(tmp_path, f"five_run_{i}.db")
        result = _run_child_probe(script_path, db_copy, "shipped", TIGHT_CAP_KB)
        assert result.returncode == 0, f"run {i}: stdout={result.stdout!r} stderr={result.stderr!r}"
        outcomes.append(result.stdout)
        assert "RESULT=OK has_panel=True" in result.stdout, (
            f"run {i} of 5 failed at the tight cap — a flaky bound is not a bound "
            f"(binding iter-44 lesson); stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "SUBSEQUENT_READ_OK" in result.stdout, f"run {i}: no live post-call read"
    assert len(outcomes) == 5
    assert all("RESULT=OK has_panel=True" in o for o in outcomes), "not all 5 consecutive runs passed"
