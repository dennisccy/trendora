"""ops-hardening iter-39 FIX PASS (audit finding B3 / J-07 step 4) — DETERMINISTIC proof that the two
NAMED per-item `MemoryError` isolation handlers inside the ingest finalize hook's aggregate-warm loops
actually fire, abort only their OWN loop, and leave `_refresh_ingest_aggregates` returning normally.

WHY THIS EXISTS ALONGSIDE `test_ingest_finalize_memory_pressure.py`:
that module induces a REAL, non-monkeypatched `MemoryError` under a genuine `ulimit -v` cap and is the
stronger proof for the mechanism it covers (`forward_aggregates`). What it cannot do — and what three
live calibration trials at 3420 / 2700 / 2650 MB this iteration also could not do (audit B3) — is reach
those handlers inside a LIVE server process: `_missing_data_diagnostic`'s whole-`daily_prices`
materialization runs EARLIER in the same finalize sequence, so any cap tight enough to threaten the
target loops exhausts the budget upstream first. Chasing that cap further is the wrong-direction pattern
in `.claude/judgment-rubrics.md` §4; J-07 step 4's own text sanctions the alternative verbatim ("Induce
memory pressure during a warm (TEST HOOK or a tightened cap in a throwaway process)").

So these tests drive `data_manager._fault_inject_memory_error` — the env-gated, test-only injector — at
the EXACT call sites the acceptance clause names, and assert WHICH stage aborted from a direct read of
that stage's own distinctive log line (never inferred from "a `MemoryError` fired somewhere" — the
binding iter-37/38 lesson). Every test carries its own control arm so a silently-disabled injector shows
up as a failure rather than a green pass.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone

import pytest
from sqlmodel import Session

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import data_manager, forward_testing, indexes
from app.engine.data_manager import JobProgress
from app.models import ScannerRun

ASOF = date(2020, 1, 2)
FAULT_ENV = data_manager._FAULT_INJECT_MEMORY_ERROR_ENV
# The two distinctive per-item abort log lines (`data_manager.py`) whose handlers J-07's acceptance names.
FORWARD_AGGREGATES_ABORT = "ingest forward-aggregate warm aborted at horizon"
DRAWDOWN_ABORT = "ingest drawdown-expectations warm aborted"


@pytest.fixture()
def finalize_session(tmp_path):
    """The smallest DB `_refresh_ingest_aggregates` needs to REACH both target loops: one `ScannerRun`, so
    `scanner._latest_stored_run_date()` is non-None and the per-horizon forward-aggregate loop runs. No
    price/result/return rows — the injection fires BEFORE any compute, so the loop's real cost is
    irrelevant to what is being proven here (that the handler catches, isolates, and returns honestly)."""
    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / 'finalize_fault.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(ScannerRun(
            asof_date=ASOF, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
            regime_score=50.0, regime_label=cfg.regime.labels[0], regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        ))
        session.commit()
    with Session(engine) as session:
        yield session, cfg


def _spy_release(monkeypatch) -> list[str]:
    """Record every `_release_process_memory()` call — the second half of the iter-8 isolation convention
    (stop the loop AND force freed memory back to the OS before moving on)."""
    calls: list[str] = []
    real = data_manager._release_process_memory

    def _spy() -> None:
        calls.append("released")
        real()

    monkeypatch.setattr(data_manager, "_release_process_memory", _spy)
    return calls


def _one_claim_ledger(monkeypatch) -> None:
    """Give the drawdown-expectations loop exactly ONE claim to iterate, deterministically — the loop is
    a no-op on an empty ledger, and the committed ledger's contents are not this test's subject."""
    monkeypatch.setattr(
        data_manager, "read_entries",
        lambda _path: [{"type": "claim", "claim": {"signal": "fault-injection-probe", "horizon": 21}}],
    )


# ==================================================================================================
# TC-1 — the NAMED forward-aggregate per-horizon handler (`data_manager.py`, iter-8 convention)
# ==================================================================================================
def test_forward_aggregate_warm_memory_error_is_caught_isolated_and_named(
    finalize_session, monkeypatch, caplog
):
    """TC-1: a `MemoryError` raised at the per-horizon forward-aggregate call site is caught by THAT
    loop's own `except MemoryError` — proven by its distinctive log line naming the horizon, not by a bare
    "a MemoryError happened". The category is honestly ABSENT from the refreshed list, the loop stops at
    the first horizon (never hammering the next allocation), `_release_process_memory()` runs, the function
    itself never raises, and the LATER aggregate categories still execute (the abort is isolated to this
    ONE loop, which is the whole point of the per-item convention)."""
    session, cfg = finalize_session
    release_calls = _spy_release(monkeypatch)
    _one_claim_ledger(monkeypatch)

    # Load-bearing isolation probe: did a LATER category still get a chance to run after the abort?
    # The probe target is `index_series` — the next category after forward-aggregates in the ESSENTIAL
    # half. It used to be drawdown-expectations, which now lives in `_refresh_deferred_hot_keys` (the
    # finalize hook was split so the UI hot-key warms stop holding the job open); probing a category in
    # a function this call no longer runs would assert nothing about isolation here.
    later_calls: list[str] = []
    monkeypatch.setattr(
        indexes, "index_series_cached_with_status",
        lambda *_a, **_k: later_calls.append("called") or ({}, False),
    )
    horizon_calls: list[int] = []
    monkeypatch.setattr(
        forward_testing, "forward_aggregates_ingest_cached",
        lambda *_a, **_k: horizon_calls.append(1),
    )

    monkeypatch.setenv(FAULT_ENV, "forward_aggregates")
    prog = JobProgress(job_id="fi-fwd-agg", kind="backfill", start=ASOF, end=ASOF)
    with caplog.at_level(logging.INFO, logger="trendora.data_manager"):
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must never raise

    assert FORWARD_AGGREGATES_ABORT in caplog.text, (
        "the forward-aggregate loop's OWN per-horizon MemoryError handler must be the one that fired — "
        f"its distinctive log line is absent; captured log was:\n{caplog.text}"
    )
    assert "forward_aggregates" not in refreshed, (
        f"an aborted warm must be honestly absent from the refreshed categories; refreshed={refreshed}"
    )
    assert horizon_calls == [], (
        "the injection fires BEFORE the real warm call, and the loop must stop at the first MemoryError — "
        f"the real per-horizon compute must never have been invoked; calls={horizon_calls}"
    )
    assert release_calls, "the iter-8 convention requires _release_process_memory() on the MemoryError path"
    assert later_calls, (
        "the abort must be isolated to the forward-aggregate loop — a LATER aggregate category "
        "(index-series) still had to run; it never did"
    )


def test_forward_aggregate_control_no_injection_completes_and_logs_no_abort(
    finalize_session, monkeypatch, caplog
):
    """Control for the test above (so a silently-disabled injector cannot pass as a green result): the
    IDENTICAL call with the env var UNSET logs NO forward-aggregate abort line and reports the category as
    refreshed. If this control ever fails, the tight-arm result above cannot be trusted."""
    session, cfg = finalize_session
    monkeypatch.delenv(FAULT_ENV, raising=False)
    monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", lambda *_a, **_k: None)

    prog = JobProgress(job_id="fi-fwd-agg-control", kind="backfill", start=ASOF, end=ASOF)
    with caplog.at_level(logging.INFO, logger="trendora.data_manager"):
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)

    assert FORWARD_AGGREGATES_ABORT not in caplog.text, (
        f"no injection was configured, so no abort may fire; captured log was:\n{caplog.text}"
    )
    assert "forward_aggregates" in refreshed, f"expected a normal warm without injection; refreshed={refreshed}"


# ==================================================================================================
# TC-1 (second named handler) — the per-claim drawdown-expectations loop
# ==================================================================================================
def test_drawdown_expectations_warm_memory_error_is_caught_isolated_and_named(
    finalize_session, monkeypatch, caplog
):
    """The SECOND per-item handler J-07's acceptance names (`data_manager.py`, per-claim drawdown
    expectations): an injected `MemoryError` is caught by that loop's own `except MemoryError`, proven by
    ITS distinctive log line — distinct from the forward-aggregate one, so the assertion cannot pass on
    the wrong stage aborting. The category is honestly absent, `_release_process_memory()` runs, and the
    hook returns normally.

    The per-claim drawdown loop now lives in `_refresh_deferred_hot_keys` (the finalize hook was split so
    the UI hot-key warms stop holding the job open), so this drives BOTH halves in their real order. That
    makes the isolation claim stronger than before, not weaker: the injected abort must leave the
    un-targeted forward-aggregate category refreshed ACROSS the split, not merely earlier in one
    function."""
    session, cfg = finalize_session
    release_calls = _spy_release(monkeypatch)
    _one_claim_ledger(monkeypatch)
    monkeypatch.setattr(forward_testing, "forward_aggregates_ingest_cached", lambda *_a, **_k: None)
    claim_calls: list[str] = []
    monkeypatch.setattr(
        forward_testing, "compute_drawdown_expectations_cached",
        lambda *_a, **_k: claim_calls.append("called") or None,
    )

    monkeypatch.setenv(FAULT_ENV, "drawdown_expectations")
    prog = JobProgress(job_id="fi-drawdown", kind="backfill", start=ASOF, end=ASOF)
    with caplog.at_level(logging.INFO, logger="trendora.data_manager"):
        # both halves, in the order `_run_job` calls them — neither may raise
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
        refreshed = refreshed + data_manager._refresh_deferred_hot_keys(session, cfg, prog)

    assert DRAWDOWN_ABORT in caplog.text, (
        "the per-claim drawdown-expectations loop's OWN MemoryError handler must be the one that fired; "
        f"captured log was:\n{caplog.text}"
    )
    assert FORWARD_AGGREGATES_ABORT not in caplog.text, (
        "only the TARGETED stage may abort — the forward-aggregate loop must have completed normally"
    )
    assert "forward_aggregates" in refreshed, (
        "the earlier, un-targeted category must still be refreshed (per-item isolation, not a cascade); "
        f"refreshed={refreshed}"
    )
    assert "drawdown_expectations" not in refreshed, f"aborted category must be absent; refreshed={refreshed}"
    assert claim_calls == [], f"the loop must stop before the real per-claim compute; calls={claim_calls}"
    assert release_calls, "the iter-8 convention requires _release_process_memory() on the MemoryError path"


# ==================================================================================================
# Injector contract — an unrecognized site name must NOT silently look like a configured drill
# ==================================================================================================
def test_unknown_fault_injection_site_is_ignored(monkeypatch):
    """A typo'd site name injects nothing. Without this, a mistyped drill env var would produce a clean
    run that reads exactly like "the handler was never needed" instead of "the drill never armed"."""
    monkeypatch.setenv(FAULT_ENV, "forward_aggregates")
    with pytest.raises(MemoryError):
        data_manager._fault_inject_memory_error("forward_aggregates")
    data_manager._fault_inject_memory_error("forwardaggregates")  # typo — recognized site list gates it
    data_manager._fault_inject_memory_error("drawdown_expectations")  # armed site is a different one


def test_fault_injection_is_a_no_op_when_env_is_unset(monkeypatch):
    """The production contract: with the env var absent, EVERY known site is a no-op — the hook adds no
    behavior to any real deployment."""
    monkeypatch.delenv(FAULT_ENV, raising=False)
    for site in sorted(data_manager._FAULT_INJECT_SITES):
        data_manager._fault_inject_memory_error(site)  # must not raise
