"""ops-hardening iter-36 (J-07 evidence-serving-path memory bound, ledger finding iter-35/k) — a REAL,
non-monkeypatched induction test for `compute_drawdown_expectations`'s `stored_by_key` read, the
`/api/evidence` serving-path `MemoryError` source iter-35's live run reproduced twice.

WHY A REAL SUBPROCESS INDUCTION, NOT A MONKEYPATCH: mirrors `test_ingest_finalize_memory_pressure.py`'s
established rationale (this module's sibling drill for the analogous ingest-finalize `MemoryError` catch) —
a `monkeypatch`-injected `MemoryError` proves the exception HANDLER's code path but never proves the
mechanism actually triggers under genuine OS-level virtual-memory exhaustion. This spawns real Python
subprocesses under a genuinely tightened `ulimit -v` (RLIMIT_AS), running the PINNED pre-fix reference
`compute_drawdown_expectations` body (unchunked `stored_by_key`) against the shipped chunked
implementation, both against a broad REAL claim's cohort on a disposable COPY of the live committed seed DB
(544 distinct tickers, 771,662 (ticker, snapshot-date) forward-return pairs at horizon=20 — the exact scale
class ledger finding iter-35/k's live run hit).

CALIBRATION (measured on this host, `.venv` Python 3.12, claim
`{kind: factor, factor: leadership_score, slice_kind: total, horizon: 20}` against the live committed seed):
an unbounded run measures peak RSS ~1,215,052 KB for the pinned reference (unchunked) vs ~1,165,092 KB for
the shipped (chunked, `research.drawdown_expectations_ticker_chunk=50`) implementation — a real but MODEST
~50 MB / ~4% reduction (unlike item 1's `_membership_timeline` fix, which is a large architectural bound;
this fix is the smaller, `.all()` -> chunked-`yield_per` idiom, and `compute_samples`'s own UNCHANGED
771,662-row materialization dominates the call's total footprint — the residual this iteration's own NOTES
section calls for disclosing rather than silently rounding away). A `ulimit -v` window of
1,210,000-1,220,000 KB reproducibly discriminates: the reference aborts with a caught `MemoryError`, the
shipped implementation completes normally, at EVERY cap tested in that window (repeated). This is a
NARROWER, more host-sensitive window than `test_ingest_finalize_memory_pressure.py`'s 300 MB window — the
absolute KB values are calibrated to THIS host/Python build, following that same module's own established
convention of host-measured absolute caps."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from _seed_subset import build_research_subset_db, real_db_available

REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_DB = REPO_ROOT / "apps/backend/data/trendora.db"
BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)

# goal-market-compass iter-5 (goal.md Constraint (a) / host resource-fit, owner 2026-08-20): this
# module's real-subprocess `ulimit -v` induction is a genuinely heavy drill (multiple fresh DB builds +
# subprocess spawns) — opt-in only, so a plain `pytest` collection of this file never pays that cost by
# accident. TC-1: WITHOUT the env var, every test below reports SKIPPED at setup, before any DB is
# touched, in seconds.
pytestmark = pytest.mark.skipif(
    os.environ.get("TRENDORA_MEMORY_PRESSURE") != "1",
    reason="opt-in only — set TRENDORA_MEMORY_PRESSURE=1 to run this real-subprocess memory-pressure "
    "induction drill (multiple DB builds + ulimit -v subprocess spawns; run on an idle host)",
)

_CLAIM = {"kind": "factor", "factor": "leadership_score", "slice_kind": "total", "horizon": 20, "direction": "positive"}

# Measured this iteration (see module docstring): the window that reproducibly discriminates reference
# (unchunked, aborts) from shipped (chunked, completes) on this host.
TIGHT_CAP_KB = 1_215_000
# Deep enough that BOTH implementations starve — proves the shipped code still degrades honestly (never a
# crash/wedge) rather than merely moving the failure point.
STARVED_CAP_KB = 1_000_000
# Comfortably clears the whole claim compute for EITHER implementation — the CONTROL cap.
CONTROL_CAP_KB = 1_600_000
BOUNDED_TIMEOUT_S = 120.0


def _skip_if_no_real_db() -> None:
    if not real_db_available():
        pytest.skip(f"real committed seed DB not found at {REAL_DB} — nothing to reproduce against")


def _fresh_seed_copy(tmp_path: Path, name: str) -> Path:
    """A FRESH, never-cache-polluted disposable SUBSET DB, ONE PER CALL — goal-market-compass iter-5
    (Constraint (a)): built via `_seed_subset.build_research_subset_db` (an `ATTACH`-and-`INSERT
    ... SELECT` read-only extraction of just the horizon=20 population this module's `_CLAIM` needs),
    never a `shutil.copy*` of the live 7.8 GB `apps/backend/data/trendora.db` — see that helper's
    docstring for exactly which rows/tables are carried and which are honestly dropped.
    `compute_drawdown_expectations_cached` (the real `/api/evidence` entry point this drill exercises)
    WRITES an `EventStudyCache` row on a MISS — so a DB REUSED across sub-calls would silently turn a
    later "reference"/"starved" probe into a trivial cache HIT (never re-invoking the compute this drill
    exists to pressure-test) the moment an EARLIER probe on the SAME copy succeeded. Each probe therefore
    gets its OWN fresh subset build."""
    _skip_if_no_real_db()
    dest = tmp_path / name
    build_research_subset_db(dest, horizons=[_CLAIM["horizon"]])
    return dest


# --------------------------------------------------------------------------------------------------
# Child-process probe: mirrors evidence.py's OWN isolate-and-continue guard (`build_evidence_payload`,
# UNTOUCHED by this iteration) — calls `compute_drawdown_expectations_cached` (the exact entry point
# `GET /api/evidence` uses) wrapped in the SAME `except MemoryError` pattern, printing an honest sentinel
# either way. `--reference` swaps in the pinned pre-fix (unchunked) implementation via a module-level
# monkeypatch BEFORE the call — `compute_drawdown_expectations_cached` resolves `compute_drawdown_
# expectations` by plain module-level name each call, so the swap is picked up with no other change.
# --------------------------------------------------------------------------------------------------
_CHILD_PROBE_TEMPLATE = '''
import sys, json
sys.path.insert(0, "__BACKEND_ROOT__")
from sqlmodel import Session, select
from app.config import load_config
from app.db import make_engine
import app.engine.forward_testing as ft
from app.models import ForwardReturn

db_path = sys.argv[1]
mode = sys.argv[2]  # "reference" or "shipped"
claim = __CLAIM__

def _reference_compute_drawdown_expectations(session, claim, config=None):
    """Pinned pre-fix body (git show HEAD:apps/backend/app/engine/forward_testing.py, iter-36 dispatch
    commit): ONE unchunked session.exec(fr_stmt).all() builds stored_by_key for the WHOLE cohort at once."""
    from collections import defaultdict
    cfg = config or ft.get_config()
    wf = cfg.walk_forward
    horizon = claim.get("horizon")
    if horizon not in wf.underwater_horizons:
        return None
    kwargs = ft._claim_samples_kwargs(claim)
    if kwargs is None:
        return None
    from app.engine.market_phase import phase_context_by_date
    from app.engine.samples import compute_samples
    try:
        samples = compute_samples(session, kind=claim.get("kind"), horizon=horizon, config=cfg, as_of=None, **kwargs)
    except ValueError:
        return None
    rows = [r for r in samples["rows"] if r.get("snapshot_date") and r.get("forward_return") is not None]
    if not rows:
        return None
    tickers = sorted({r["ticker"] for r in rows})
    fr_stmt = select(
        ForwardReturn.symbol, ForwardReturn.asof_date, ForwardReturn.max_drawdown,
        ForwardReturn.underwater_days, ForwardReturn.time_to_recover_days,
    ).where(ForwardReturn.horizon == horizon, ForwardReturn.symbol.in_(tickers))
    stored_by_key = {
        (symbol, asof_date.isoformat()): (mdd, uw, ttr)
        for symbol, asof_date, mdd, uw, ttr in session.exec(fr_stmt).all()
    }
    phases = phase_context_by_date(session, as_of=None, config=cfg)
    by_phase_mdd, by_phase_uw, by_phase_ttr, by_phase_returns = (defaultdict(list) for _ in range(4))
    for row in rows:
        date_iso = row["snapshot_date"]
        ctx = phases.get(date_iso)
        if ctx is None:
            continue
        phase = ctx["phase"]
        by_phase_returns[phase].append((date_iso, row["forward_return"]))
        stored = stored_by_key.get((row["ticker"], date_iso))
        if stored is None:
            continue
        mdd, uw, ttr = stored
        if mdd is not None: by_phase_mdd[phase].append(mdd)
        if uw is not None: by_phase_uw[phase].append(uw)
        if ttr is not None: by_phase_ttr[phase].append(ttr)
    by_phase = [
        {
            "phase": phase, "n": len(by_phase_returns.get(phase, [])),
            "max_drawdown": ft._distribution_cell(by_phase_mdd.get(phase, []), wf.min_sample),
            "underwater_days": ft._distribution_cell(by_phase_uw.get(phase, []), wf.min_sample),
            "time_to_recover_days": ft._distribution_cell(by_phase_ttr.get(phase, []), wf.min_sample),
            "loss_streak": ft._loss_streak_cell(by_phase_returns.get(phase, []), wf.streak_min_n),
        }
        for phase in cfg.market_phase.labels
    ]
    return {
        "horizon": horizon, "min_sample": wf.min_sample, "streak_min_n": wf.streak_min_n,
        "survivorship_bias": ft.SURVIVORSHIP_BIAS_LABEL, "method_note": ft.LOSS_STREAK_METHOD_NOTE,
        "by_phase": by_phase,
    }

if mode == "reference":
    ft.compute_drawdown_expectations = _reference_compute_drawdown_expectations

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
    script_path = tmp_path / "_dd_mem_probe_child.py"
    text = _CHILD_PROBE_TEMPLATE.replace("__BACKEND_ROOT__", BACKEND_ROOT).replace("__CLAIM__", repr(_CLAIM))
    script_path.write_text(text)
    return script_path


def _run_child_probe(script_path: Path, db_path: Path, mode: str, cap_kb: int) -> subprocess.CompletedProcess:
    cmd = f"ulimit -v {cap_kb}; exec {sys.executable} {script_path} {db_path} {mode}"
    return subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=BOUNDED_TIMEOUT_S)


def test_tight_cap_reference_aborts_shipped_completes(tmp_path):
    """TC-8: at the SAME tight `ulimit -v` cap, the pinned pre-fix (unchunked) reference implementation
    aborts with a caught `MemoryError` (the exact live iter-35 abort, reproduced), while the shipped
    (chunked) implementation completes and serves the real computed panel — the measurable failure-rate
    reduction TC-8 asks for, at the real per-claim live-basis scale (771,662 cohort rows / 544 tickers).
    Each sub-call gets its OWN fresh DB copy (never reused) so an earlier success can never turn a later
    probe into a trivial `EventStudyCache` hit."""
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
        f"expected the shipped chunked implementation to complete normally under the SAME tight cap that "
        f"aborted the reference (cap may be miscalibrated too tight for the shipped code); "
        f"stdout={shipped_result.stdout!r} stderr={shipped_result.stderr!r}"
    )
    assert "SUBSEQUENT_READ_OK" in shipped_result.stdout


def test_control_generous_cap_both_complete_normally(tmp_path):
    """Control assertion (mirrors the sibling ingest-finalize drill's own DoD requirement): the IDENTICAL
    claim/cohort, under a generous cap, completes normally for BOTH implementations — proving the tight-cap
    abort above is attributable to the cap, not an unrelated bug. A fresh DB copy per mode (see
    `_fresh_seed_copy`)."""
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
    """Under pressure severe enough that the SHIPPED (chunked) implementation ALSO starves, it still
    degrades exactly as honestly as the reference — a caught MemoryError, never an uncaught crash/wedge —
    the residual this iteration's NOTES section calls for disclosing rather than silently claiming a full
    bound (the chunking reduces failure likelihood at a given pressure level; it does not make the read
    immune to arbitrarily severe pressure, since `stored_by_key`'s FINAL size is unchanged by chunking)."""
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
