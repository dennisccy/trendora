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

import os
import subprocess
import sys
from pathlib import Path

import pytest

from _seed_subset import build_research_subset_db, real_db_available

REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_DB = REPO_ROOT / "apps/backend/data/trendora.db"
BACKEND_ROOT = str(Path(__file__).resolve().parent.parent)

# goal-market-compass iter-5 (goal.md Constraint (a) / host resource-fit, owner 2026-08-20): opt-in
# only — see test_evidence_drawdown_memory_pressure.py's sibling `pytestmark` for the full rationale.
# TC-1: WITHOUT the env var, every test below reports SKIPPED at setup, before any DB is touched.
pytestmark = pytest.mark.skipif(
    os.environ.get("TRENDORA_MEMORY_PRESSURE") != "1",
    reason="opt-in only — set TRENDORA_MEMORY_PRESSURE=1 to run this real-subprocess memory-pressure "
    "induction drill (multiple DB builds + ulimit -v subprocess spawns; run on an idle host)",
)

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
#
# ops-hardening iter-48 AUDIT (T2/T3) — RE-CALIBRATED 600_000 -> 420_000, with measurement. This constant
# is an INVERTED-POLARITY knob: the test asserts the shipped implementation FAILS, so it goes stale when
# the shipped code gets BETTER, and then reads as a regression. That is exactly what happened. QA's run
# and an independent reproduction both saw `RESULT=OK has_panel=True` at the old 600,000 KB cap — i.e.
# the shipped decile bound now fits UNDER 600 MB, so the "starved" cap had stopped starving anything.
# QA guessed "environmental flake"; it is not one — it reproduces, and it is good news, not a defect.
#
# Measured on this host (shipped mode, one fresh seed copy per probe, run strictly sequentially — never
# concurrently, which is the confound that muddied QA's own run):
#     600,000 KB -> COMPLETES        (the stale cap: no starvation, test's premise void)
#     500,000 KB -> starves honestly (MemoryError caught, SUBSEQUENT_READ_OK, rc=0)
#     420,000 KB -> starves honestly  x3 consecutive runs, 3/3 (binding iter-44 lesson: one run is not proof)
#     360,000 KB -> starves honestly
#     300,000 KB -> starves honestly (interpreter still boots — the floor is well below this)
# 420,000 sits with real margin on BOTH sides: ~30 % below the 600,000 boundary where starvation stops,
# and comfortably above the cap at which the child could no longer import and reach the guard at all
# (which would trip this test's `returncode == 0` assertion instead, a different failure).
STARVED_CAP_KB = 420_000
# Comfortably clears the whole claim compute for EITHER implementation — the CONTROL cap.
CONTROL_CAP_KB = 1_600_000
BOUNDED_TIMEOUT_S = 150.0


def _skip_if_no_real_db() -> None:
    if not real_db_available():
        pytest.skip(f"real committed seed DB not found at {REAL_DB} — nothing to reproduce against")


# goal-market-compass iter-5 (Constraint (a)): every claim in this file (decile/total/regime) is
# horizon=20 today (see `_CLAIM`/`_TOTAL_CLAIM`/`_REGIME_CLAIM` below) — resolved as a set so a future
# claim added at a different horizon is automatically carried into the subset instead of silently
# missing its population. Referenced (not defined) by `_fresh_seed_copy`, so its own definition further
# down the module is fine — Python resolves module globals at CALL time.
def _all_claim_horizons() -> list[int]:
    return sorted({_CLAIM["horizon"], _TOTAL_CLAIM["horizon"], _REGIME_CLAIM["horizon"]})


def _fresh_seed_copy(tmp_path: Path, name: str) -> Path:
    """A FRESH, never-cache-polluted disposable SUBSET DB, ONE PER CALL — goal-market-compass iter-5
    (Constraint (a)): built via `_seed_subset.build_research_subset_db` (an `ATTACH`-and-`INSERT
    ... SELECT` read-only extraction — see that helper's docstring), never a `shutil.copy*` of the live
    7.8 GB `apps/backend/data/trendora.db`. Mirrors `test_evidence_drawdown_memory_pressure.py`'s own
    rationale: `compute_drawdown_expectations_cached` WRITES an `EventStudyCache` row on a MISS, so a DB
    reused across probes would silently turn a later probe into a trivial cache HIT."""
    _skip_if_no_real_db()
    dest = tmp_path / name
    build_research_subset_db(dest, horizons=_all_claim_horizons())
    return dest


def _delete_copy(path: Path) -> None:
    """ops-hardening iter-48 (pre-iter-5: sized against the old raw-file-copy fixture, ~8.4 GB per
    copy): the total/regime drills below run TWICE as many DB-build probes as the existing decile drill
    (two variants x the same battery), so each build is deleted immediately after its probe subprocess
    returns rather than left for `tmp_path`'s end-of-session cleanup — still worth doing even at the
    iter-5 subset DB's much smaller size (many probes x this file's own battery still adds up).
    Best-effort: a failed cleanup must never fail the test that already got its result."""
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(path) + suffix)
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass


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


# ==================================================================================================
# ops-hardening iter-48 (AG-8, iter-47 next-step item 5) — the SAME real-subprocess induction pattern
# above, extended to `_factor_samples`'s "total" and "regime" branches (`samples.py:161`/`:168`-169`
# pre-fix). Neither branch is exercised by any LIVE certified claim today (the 7-claim ledger's factor
# claims are all decile-scoped) — these drills construct their OWN claim dicts, exactly as the decile
# drill above already does, so the bound is proven for the code path regardless of what the ledger
# happens to hold right now.
#
# Calibrated on this host through the REAL entry point (`compute_drawdown_expectations_cached`, the SAME
# call the test bodies below drive — NOT an isolated sub-call; an earlier calibration pass measured only
# `_factor_observations`/`_factor_regime_observations` in isolation and its caps were too tight once the
# full pipeline's OWN additional overhead — `phase_context_by_date`, the ticker-chunked `stored_by_key`
# accumulators, the by-phase distribution accumulators — is included, which a live run caught: the
# "shipped" implementation was hitting its OWN `ulimit -v` cap under the isolated-calibration numbers).
# `.venv` Python 3.12, real committed seed (fresh copy per probe — `compute_drawdown_expectations_cached`
# WRITES an `EventStudyCache` row on a MISS, so a reused copy would trivially cache-HIT a later probe),
# leadership_score, horizon 20, no `ulimit -v`:
#
#   TOTAL   population 1,261,493 observations — pre-fix PEAK_RSS_KB=1,658,248, shipped PEAK_RSS_KB=
#           1,444,820 (~12.9% reduction)
#   REGIME=Risk-on (fixture's largest bucket, 458,772 of 1,261,493) — pre-fix PEAK_RSS_KB=986,608,
#           shipped PEAK_RSS_KB=833,576-836,696 (~15.2-15.5% reduction)
#
# `has_panel=True` and member counts byte-identical between pre-fix and shipped for both branches in
# every calibration run — confirmed both by this live measurement and by `test_research_streaming.py`'s
# pinned-reference unit tests.
# ==================================================================================================
_TOTAL_CLAIM = {
    "kind": "factor", "factor": "leadership_score", "slice_kind": "total", "horizon": 20,
    "direction": "positive",
}
_REGIME_CLAIM = {
    "kind": "factor", "factor": "leadership_score", "slice_kind": "regime", "regime": "Risk-on",
    "horizon": 20, "direction": "positive",
}

# TOTAL: old (double materialization) aborts, shipped (in-place row build) completes with margin.
TOTAL_TIGHT_CAP_KB = 1_550_000
TOTAL_STARVED_CAP_KB = 1_100_000
TOTAL_CONTROL_CAP_KB = 2_000_000

# REGIME=Risk-on: old (whole-population-then-filter) aborts, shipped (bounded, filters during the walk)
# completes with margin.
REGIME_TIGHT_CAP_KB = 900_000
REGIME_STARVED_CAP_KB = 650_000
REGIME_CONTROL_CAP_KB = 1_100_000

_TOTAL_REGIME_CHILD_PROBE_TEMPLATE = '''
import sys
sys.path.insert(0, "__BACKEND_ROOT__")
from sqlmodel import Session, select
from app.config import load_config
from app.db import make_engine
import app.engine.forward_testing as ft
import app.engine.samples as samples_mod
from app.models import ForwardReturn, ScannerRun

db_path = sys.argv[1]
mode = sys.argv[2]  # "reference" or "shipped"
variant = sys.argv[3]  # "total" or "regime"
claim = __TOTAL_CLAIM__ if variant == "total" else __REGIME_CLAIM__

def _reference_factor_samples(session, cfg, *, factor_key, horizon, slice_kind, decile, regime, as_of):
    """Pinned pre-fix `_factor_samples` body for the "total"/"regime" branches ONLY (the exact shape
    iter-48 replaced): the FULL `_factor_observations` list, filtered afterward for "regime", and a
    SEPARATE full `rows` list built via list comprehension for "total" (never reusing `members` in
    place) -- both retain two population-sized structures at once at their peak."""
    from app.engine.research import _factor_observations
    fl = cfg.research.factor_lab
    factor = next(f for f in fl.factors if f.key == factor_key)
    if slice_kind == "total":
        members = _factor_observations(session, factor, horizon, as_of)
    else:
        members = [o for o in _factor_observations(session, factor, horizon, as_of) if o["regime"] == regime]
    run_dates = {
        run.id: run.asof_date.isoformat()
        for run in session.exec(select(ScannerRun.id, ScannerRun.asof_date)).all()
    }
    rows = [
        {
            "ticker": o["ticker"], "snapshot_date": run_dates.get(o["run_id"]), "regime": o["regime"],
            "values": [{"key": factor.key, "label": factor.label, "value": o["factor"]}],
            "forward_return": o["return"],
        }
        for o in members
    ]
    cohort = {
        "kind": samples_mod.KIND_FACTOR, "slice": slice_kind, "horizon": horizon,
        "factor": {"key": factor.key, "label": factor.label, "family": factor.family,
                   "direction": factor.direction, "source": factor.source},
        "decile": None, "regime": regime if slice_kind == "regime" else None, "deciles_count": fl.deciles,
    }
    return {"cohort": cohort, "rows": rows}

if mode == "reference":
    samples_mod._factor_samples = _reference_factor_samples

cfg = load_config()
engine = make_engine(f"sqlite:///{db_path}")

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

with Session(engine) as session:
    n = len(session.exec(select(ForwardReturn.id).limit(1)).all())
print(f"SUBSEQUENT_READ_OK n={n}")
'''


def _write_total_regime_child_probe(tmp_path: Path) -> Path:
    script_path = tmp_path / "_total_regime_mem_probe_child.py"
    text = (
        _TOTAL_REGIME_CHILD_PROBE_TEMPLATE
        .replace("__BACKEND_ROOT__", BACKEND_ROOT)
        .replace("__TOTAL_CLAIM__", repr(_TOTAL_CLAIM))
        .replace("__REGIME_CLAIM__", repr(_REGIME_CLAIM))
    )
    script_path.write_text(text)
    return script_path


def _run_total_regime_child_probe(
    script_path: Path, db_path: Path, mode: str, variant: str, cap_kb: int,
) -> subprocess.CompletedProcess:
    cmd = f"ulimit -v {cap_kb}; exec {sys.executable} {script_path} {db_path} {mode} {variant}"
    return subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=BOUNDED_TIMEOUT_S)


@pytest.mark.parametrize(
    "variant,tight_cap",
    [("total", TOTAL_TIGHT_CAP_KB), ("regime", REGIME_TIGHT_CAP_KB)],
)
def test_total_regime_tight_cap_reference_aborts_shipped_completes(tmp_path, variant, tight_cap):
    """The "total"/"regime" sibling of `test_tight_cap_reference_aborts_shipped_completes`: at the SAME
    tight `ulimit -v` cap, the pinned pre-fix (double-materialization / whole-population-then-filter)
    reference aborts with a caught `MemoryError`, while the shipped (bounded / in-place) implementation
    completes and serves the real computed panel."""
    script_path = _write_total_regime_child_probe(tmp_path)

    ref_db = _fresh_seed_copy(tmp_path, f"{variant}_ref.db")
    try:
        ref_result = _run_total_regime_child_probe(script_path, ref_db, "reference", variant, tight_cap)
    finally:
        _delete_copy(ref_db)
    assert ref_result.returncode == 0, (
        f"variant={variant}: the reference probe must never crash uncaught; "
        f"stdout={ref_result.stdout!r} stderr={ref_result.stderr!r}"
    )
    assert "RESULT=UNAVAILABLE_MEMORYERROR" in ref_result.stdout, (
        f"variant={variant}: expected the pre-fix reference to abort under the tight cap; "
        f"stdout={ref_result.stdout!r} stderr={ref_result.stderr!r}"
    )

    shipped_db = _fresh_seed_copy(tmp_path, f"{variant}_shipped.db")
    try:
        shipped_result = _run_total_regime_child_probe(script_path, shipped_db, "shipped", variant, tight_cap)
    finally:
        _delete_copy(shipped_db)
    assert shipped_result.returncode == 0, (
        f"variant={variant}: stdout={shipped_result.stdout!r} stderr={shipped_result.stderr!r}"
    )
    assert "RESULT=OK has_panel=True" in shipped_result.stdout, (
        f"variant={variant}: expected the shipped implementation to complete under the SAME tight cap "
        f"that aborted the reference; stdout={shipped_result.stdout!r} stderr={shipped_result.stderr!r}"
    )


@pytest.mark.parametrize(
    "variant,control_cap",
    [("total", TOTAL_CONTROL_CAP_KB), ("regime", REGIME_CONTROL_CAP_KB)],
)
def test_total_regime_control_generous_cap_both_complete(tmp_path, variant, control_cap):
    """Control assertion: under a generous cap BOTH implementations complete — the tight-cap abort is
    attributable to the cap, not an unrelated bug."""
    script_path = _write_total_regime_child_probe(tmp_path)
    for mode in ("reference", "shipped"):
        db_copy = _fresh_seed_copy(tmp_path, f"{variant}_control_{mode}.db")
        try:
            result = _run_total_regime_child_probe(script_path, db_copy, mode, variant, control_cap)
        finally:
            _delete_copy(db_copy)
        assert result.returncode == 0, f"variant={variant} mode={mode}: stdout={result.stdout!r}"
        assert "RESULT=OK has_panel=True" in result.stdout, (
            f"variant={variant} mode={mode}: the generous CONTROL cap unexpectedly failed; "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )


@pytest.mark.parametrize(
    "variant,starved_cap",
    [("total", TOTAL_STARVED_CAP_KB), ("regime", REGIME_STARVED_CAP_KB)],
)
def test_total_regime_starved_cap_shipped_still_degrades_honestly(tmp_path, variant, starved_cap):
    """Under pressure severe enough that the shipped implementation ALSO starves, it still degrades
    exactly as honestly as the reference — a caught MemoryError, never an uncaught crash/wedge."""
    script_path = _write_total_regime_child_probe(tmp_path)
    db_copy = _fresh_seed_copy(tmp_path, f"{variant}_starved.db")
    try:
        result = _run_total_regime_child_probe(script_path, db_copy, "shipped", variant, starved_cap)
    finally:
        _delete_copy(db_copy)
    assert result.returncode == 0, f"variant={variant}: stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "RESULT=UNAVAILABLE_MEMORYERROR" in result.stdout, (
        f"variant={variant}: expected the shipped implementation to ALSO honestly degrade under severe "
        f"pressure; stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "SUBSEQUENT_READ_OK" in result.stdout, (
        f"variant={variant}: expected the SAME process to still serve a fresh read after the caught "
        f"MemoryError — never a wedge; stdout={result.stdout!r}"
    )


@pytest.mark.parametrize(
    "variant,tight_cap",
    [("total", TOTAL_TIGHT_CAP_KB), ("regime", REGIME_TIGHT_CAP_KB)],
)
def test_total_regime_shipped_survives_five_consecutive_tight_cap_runs(tmp_path, variant, tight_cap):
    """TC-6 (binding iter-44 lesson — one green run is not proof): the shipped bounded implementation
    completes normally across 5 CONSECUTIVE independent subprocess runs at the SAME tight cap that
    reliably aborts the pre-fix reference — zero `MemoryError` escapes across all 5."""
    script_path = _write_total_regime_child_probe(tmp_path)
    outcomes = []
    for i in range(5):
        db_copy = _fresh_seed_copy(tmp_path, f"{variant}_five_run_{i}.db")
        try:
            result = _run_total_regime_child_probe(script_path, db_copy, "shipped", variant, tight_cap)
        finally:
            _delete_copy(db_copy)
        assert result.returncode == 0, f"variant={variant} run {i}: stdout={result.stdout!r}"
        outcomes.append(result.stdout)
        assert "RESULT=OK has_panel=True" in result.stdout, (
            f"variant={variant} run {i} of 5 failed at the tight cap — a flaky bound is not a bound "
            f"(binding iter-44 lesson); stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "SUBSEQUENT_READ_OK" in result.stdout, f"variant={variant} run {i}: no live post-call read"
    assert len(outcomes) == 5
    assert all("RESULT=OK has_panel=True" in o for o in outcomes), (
        f"variant={variant}: not all 5 consecutive runs passed"
    )
