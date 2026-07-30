"""ops-hardening iter-37 (J-07 closure) — the shared-cache fix for the last unbounded whole-table
`daily_prices` prefill on the multi-date backfill finalize path.

Root cause (iter-36/l): `_do_backfill` (`data_manager.py:2888`) and `_persist_per_date_coverage_snapshots`
(`data_manager.py:3191`, invoked from `_refresh_ingest_aggregates` for the SAME job) each opened their OWN
independent `prefilled_bar_cache` — the whole `daily_prices` table (~1.13 GB at the live basis) was loaded
TWICE per K-date backfill job instead of once (`test_bar_cache.py::test_kdate_backfill_loads_each_symbol_
at_most_once` measured this directly: every symbol loaded exactly 2x pre-fix). This iteration's fix has
`_do_backfill` stash its already-loaded `_BarCache` onto `JobProgress._shared_bar_cache`, and
`_persist_per_date_coverage_snapshots` (plus every other warm call `_refresh_ingest_aggregates` drives —
market-phase, forward-aggregates, research hot-keys, index-series, drawdown-expectations) ATTACH that same
pre-loaded cache instead of opening a fresh one.

Named proofs (binding iter-29/32 lesson: pin the OLD code TEXT for a byte-identity oracle — never call the
NEW code from both sides of the comparison; binding iter-29/31/32 lesson: a byte-identity oracle must also
prove it is load-bearing via a mutation that would NOT be caught if the fix were reverted):

  TC-7 byte-identity  — the pinned PRE-FIX body of `_persist_per_date_coverage_snapshots` (`git show
                        HEAD:apps/backend/app/engine/data_manager.py` at the iter-37 dispatch commit —
                        ALWAYS opened its own independent `prefilled_bar_cache`, `prog._shared_bar_cache`
                        did not exist) produces a BYTE-IDENTICAL persisted `CoverageSnapshot` payload to
                        the shipped implementation (which attaches a pre-loaded shared cache via
                        `prog._shared_bar_cache`), for the SAME K real snapshot dates.
  TC-8 mutation-style — poisoning ONE symbol's series inside the shared cache handed to the SHIPPED
                        function changes its persisted output relative to a clean run (proving the shipped
                        code genuinely READS bar values FROM `prog._shared_bar_cache`, not from a silent
                        independent reload that would mask a broken wiring); the SAME poisoned cache handed
                        to the PINNED REFERENCE (which never looks at `_shared_bar_cache` at all) produces
                        the SAME output as an unpoisoned reference run — proving this exact mutation would
                        NOT be caught if the shared-cache fix were reverted to the old always-own-prefill
                        behavior (the oracle is load-bearing, not a rubber stamp).

`test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` (separate file, unmodified this
iteration) independently covers the load-COUNT invariant this fix targets (max 1 load per symbol for the
whole job) via a full end-to-end `run_data_job` — this module isolates the coverage-warm VALUE correctness
specifically, calling `_persist_per_date_coverage_snapshots` directly per the plan's documented test-compat
contract ("any test that calls `_persist_per_date_coverage_snapshots` directly, without going through
`_do_backfill` first, keeps working unchanged").
"""
from __future__ import annotations

import json
import logging

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import data_manager
from app.engine import universe_resolver
from app.engine.data_manager import (
    JobProgress,
    _release_process_memory,
    _resolve_coverage_asof,
    _trading_days,
    create_job,
    refresh_coverage_snapshot_for,
    run_data_job,
)
from app.engine.prices import _BarCache, prefilled_bar_cache
from app.engine.universe_screen import read_pool
from app.models import CoverageSnapshot

logger = logging.getLogger(__name__)


# ====================================================================================================
# Pinned PRE-FIX reference implementation of `_persist_per_date_coverage_snapshots`
# (`git show HEAD:apps/backend/app/engine/data_manager.py` at the iter-37 dispatch commit — the tree
# BEFORE this iteration's shared-cache edits), verbatim body. Binding iter-29/32 lesson: pin the OLD code
# TEXT, never call the NEW code from both sides of a byte-identity comparison. `prog._shared_bar_cache`
# did not exist pre-fix, so this reference NEVER reads it — it always opens its own independent cache.
# ====================================================================================================
def _reference_persist_per_date_coverage_snapshots(
    session: Session, cfg, dates: list, prog: JobProgress
) -> None:
    if not dates:
        return
    current = _resolve_coverage_asof(session, None, cfg)
    todo = [d for d in dates if d != current]
    if not todo:
        return  # the only newly-created date IS the current stamp (already persisted) — no extra load
    pool_symbols = {row["symbol"] for row in read_pool()}
    aborted_for_memory = False
    with prefilled_bar_cache(session, expected_symbols=pool_symbols):
        for d in todo:
            prog.tick()
            try:
                refresh_coverage_snapshot_for(session, cfg, d)
            except MemoryError as exc:
                logger.exception(
                    "ingest per-date coverage warm aborted at %s — memory pressure, stopping remaining "
                    "dates in this loop: %s", d, exc,
                )
                _release_process_memory()
                aborted_for_memory = True
                break
            except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date
                logger.exception("ingest per-date coverage warm failed for %s (non-fatal): %s", d, exc)
    if aborted_for_memory:
        _release_process_memory()


def _read_coverage_payloads(session: Session, cfg, dates: list) -> dict:
    """Read back the persisted `CoverageSnapshot.payload_json` for each date (keyed by ISO date), parsed
    to a dict so the comparison is over VALUES, not JSON-string formatting."""
    dataset_version = data_manager._membership_dataset_version(session, cfg)
    out = {}
    for d in dates:
        row = session.exec(
            select(CoverageSnapshot).where(
                CoverageSnapshot.asof_key == d.isoformat(),
                CoverageSnapshot.dataset_version == dataset_version,
            )
        ).first()
        assert row is not None, f"expected a persisted CoverageSnapshot row for {d.isoformat()}"
        out[d.isoformat()] = json.loads(row.payload_json)
    return out


@pytest.fixture(scope="module")
def snapshot_dates_engine(tmp_path_factory):
    """A seeded DB with K=3 REAL snapshot dates already committed via a real, unmodified backfill job
    (`run_data_job` — its per-date compute/persist logic, `scanner.compute_run_payload` /
    `scanner.persist_run_payload`, is untouched by this iteration's fix; only the bar-cache ACQUISITION
    mechanism changed). The 3 dates are comfortably before the resolved 'current' as-of (the latest
    trading day), so `_persist_per_date_coverage_snapshots`'s own `todo` filter keeps all three across
    every test below. Module-scoped: built once; `CoverageSnapshot` rows are idempotent upserts, so the
    tests below repeatedly overwrite (never accumulate) the same keys."""
    cfg = load_config()
    _sc = cfg.scanner.model_copy(
        update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})}
    )
    cfg = cfg.model_copy(update={"scanner": _sc})
    from app.seed_loader import load_seed

    db_path = tmp_path_factory.mktemp("shared_cache_seed") / "sc.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    load_seed(engine, cfg)
    with Session(engine) as session:
        trading = _trading_days(session, cfg)
    daily_start = cfg.scanner.snapshot_cadence.daily_start or trading[0]
    daily_idx = next(i for i, d in enumerate(trading) if d >= daily_start)
    assert daily_idx + 3 <= len(trading)
    r_start, r_end = trading[daily_idx], trading[daily_idx + 2]
    dates = [d for d in trading if r_start <= d <= r_end]
    assert len(dates) == 3
    assert trading[-1] not in dates, "sanity: the picked dates must exclude the resolved current as-of"

    job = create_job("backfill", r_start, r_end)
    summary = run_data_job(job.job_id, config=cfg, engine=engine)
    assert summary["status"] == "ok"
    assert summary["snapshots_created"] == 3
    return engine, cfg, dates


# ====================================================================================================
# TC-7 — byte-identity, real K-date snapshot inputs
# ====================================================================================================
def test_shared_cache_coverage_byte_identical_to_pinned_reference(snapshot_dates_engine):
    engine, cfg, dates = snapshot_dates_engine

    # REFERENCE: the pinned pre-iter-37 body — always opens its OWN independent prefilled_bar_cache.
    with Session(engine) as session:
        prog_ref = JobProgress(job_id="ref", kind="backfill", start=dates[0], end=dates[-1])
        _reference_persist_per_date_coverage_snapshots(session, cfg, dates, prog_ref)
        reference_payloads = _read_coverage_payloads(session, cfg, dates)

    # SHIPPED: reuses a pre-loaded shared cache via `prog._shared_bar_cache` — the iter-37 mechanism
    # `_do_backfill` wires up for real; here it is built directly, exercising the SAME attach path.
    with Session(engine) as session:
        pool_symbols = {row["symbol"] for row in read_pool()}
        with prefilled_bar_cache(session, expected_symbols=pool_symbols) as shared_cache:
            prog_shipped = JobProgress(job_id="shipped", kind="backfill", start=dates[0], end=dates[-1])
            prog_shipped._shared_bar_cache = shared_cache
            data_manager._persist_per_date_coverage_snapshots(session, cfg, dates, prog_shipped)
        shipped_payloads = _read_coverage_payloads(session, cfg, dates)

    assert shipped_payloads == reference_payloads, (
        "the shipped shared-cache _persist_per_date_coverage_snapshots diverged from the pinned pre-fix "
        "reference for the same K real snapshot-date inputs — the shared-cache fix must be a pure "
        "performance refactor (byte-identical persisted CoverageSnapshot payloads)"
    )


# ====================================================================================================
# TC-8 — mutation-style: the byte-identity oracle above is load-bearing, not a rubber stamp
# ====================================================================================================
def test_shared_cache_mutation_caught_as_failure(snapshot_dates_engine):
    engine, cfg, dates = snapshot_dates_engine
    pool_symbols = {row["symbol"] for row in read_pool()}

    with Session(engine) as session:
        # a victim symbol confirmed ADMITTED at the last target date — poisoning it must therefore be
        # observable as an admitted->excluded flip (universe_count / universe_diagnostic / membership
        # timeline all change), not a no-op against an already-excluded candidate.
        resolved = universe_resolver.resolve_with_reasons(session, dates[-1], cfg)
        assert resolved["admitted"], "sanity: the live pool must admit at least one candidate at this date"
        victim = resolved["admitted"][0]

        poisoned_cache = _BarCache()
        poisoned_cache.prefill(session, expected_symbols=pool_symbols)
        assert poisoned_cache._by_symbol.get(victim), "sanity: the victim symbol must have real bars"
        # poison EVERY bar of the victim's series into a worthless penny/no-volume stock — comfortably
        # below every configured `universe.filters` admission threshold (min_price / min_dollar_vol).
        poisoned_cache._by_symbol[victim] = [
            bar._replace(close=0.0001, open=0.0001, high=0.0001, low=0.0001, volume=1.0)
            for bar in poisoned_cache._by_symbol[victim]
        ]

        prog_shipped_poisoned = JobProgress(
            job_id="shipped-poisoned", kind="backfill", start=dates[0], end=dates[-1]
        )
        prog_shipped_poisoned._shared_bar_cache = poisoned_cache
        data_manager._persist_per_date_coverage_snapshots(session, cfg, dates, prog_shipped_poisoned)
        shipped_poisoned_payloads = _read_coverage_payloads(session, cfg, dates)

        # the SAME poisoned cache, handed to the PINNED REFERENCE — which never reads `_shared_bar_cache`
        # at all (the field did not exist pre-fix) and always opens its OWN independent, correct prefill.
        prog_ref_poisoned = JobProgress(
            job_id="ref-poisoned", kind="backfill", start=dates[0], end=dates[-1]
        )
        prog_ref_poisoned._shared_bar_cache = poisoned_cache
        _reference_persist_per_date_coverage_snapshots(session, cfg, dates, prog_ref_poisoned)
        reference_poisoned_payloads = _read_coverage_payloads(session, cfg, dates)

        # a clean reference run (no poisoning) — the "what an unpoisoned run looks like" baseline.
        prog_ref_clean = JobProgress(job_id="ref-clean", kind="backfill", start=dates[0], end=dates[-1])
        _reference_persist_per_date_coverage_snapshots(session, cfg, dates, prog_ref_clean)
        reference_clean_payloads = _read_coverage_payloads(session, cfg, dates)

    assert shipped_poisoned_payloads != reference_clean_payloads, (
        f"poisoning {victim!r} inside the shared cache produced NO observable change in the SHIPPED "
        f"function's persisted output — the byte-identity oracle above would not actually catch a broken "
        f"shared-cache wiring (either the shipped code never reads bar VALUES from `prog._shared_bar_cache`, "
        f"or the poisoning failed to cross an admission threshold)"
    )
    assert reference_poisoned_payloads == reference_clean_payloads, (
        "the PINNED pre-fix reference must be BLIND to a poisoned `prog._shared_bar_cache` (that field did "
        "not exist before this iteration's fix, and the reference body never reads it) — this exact "
        "mutation would therefore NOT be caught if the shared-cache fix were reverted to the old "
        "always-own-prefill behavior, proving the TC-7 oracle above is load-bearing, not a rubber stamp"
    )


# ====================================================================================================
# AUDIT B1 — the deferred release must never leak the ~1.13 GB shared cache onto a retained JobProgress
# ====================================================================================================
def test_shared_cache_released_even_when_finalize_hook_never_runs(snapshot_dates_engine, monkeypatch):
    """iter-37 AUDIT (B1): `_do_backfill` no longer releases its shared `_BarCache` on the SUCCESS path —
    it stashes it on `prog._shared_bar_cache` and defers the release to `_refresh_ingest_aggregates`'s own
    `finally`. `_JOBS` never evicts a finished job, so if that hook is ever skipped after a SUCCESSFUL
    backfill (a `_finalize_checkpoint`/`record_stage` write or `Session(eng)` faulting between the two —
    e.g. a `MemoryError` under real pressure), the reference would pin the whole-table cache for the LIFE
    of the process. Simulates that exact window by making the finalize hook raise before it can release,
    and asserts the job runner still clears the reference (and that the failure stays non-fatal — the job
    is still `ok`, matching the hook's pre-existing log-and-continue contract)."""
    engine, cfg, dates = snapshot_dates_engine
    with Session(engine) as session:
        trading = _trading_days(session, cfg)
        snapshotted = set(session.exec(select(data_manager.ScannerRun.asof_date)).all())
    # a fresh (not-yet-snapshotted) date => >= 1 in-range target => `_do_backfill` really builds + stashes
    # the shared cache (a 0-target backfill returns before the prefill and stashes nothing).
    fresh_date = next(d for d in reversed(trading) if d not in snapshotted)

    def _boom(*_args, **_kwargs):
        raise MemoryError("simulated pressure between a successful backfill and the finalize hook")

    monkeypatch.setattr(data_manager, "_refresh_ingest_aggregates", _boom)

    job = create_job("backfill", fresh_date, fresh_date)
    summary = run_data_job(job.job_id, config=cfg, engine=engine)

    assert summary["snapshots_created"] == 1, "sanity: the backfill itself must have really done work"
    assert summary["status"] == "ok", (
        "a finalize-hook failure must stay non-fatal (pre-existing log-and-continue contract)"
    )
    assert job._shared_bar_cache is None, (
        "the shared whole-table `_BarCache` is STILL referenced by the finished job's retained "
        "`JobProgress` — `_JOBS` never evicts it, so this pins ~1.13 GB for the life of the process "
        "(AG-8/J-07 regression: the release must happen on EVERY exit path, not only when "
        "`_refresh_ingest_aggregates` runs to completion)"
    )
