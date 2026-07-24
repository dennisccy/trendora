"""ops-hardening iter-16 (J-08) — the forward-aggregate compute-vs-serve split.

The former single `forward_aggregates_cached` (ops-hardening iter-5, J-06) split into two roles:

  - `forward_aggregates_ingest_cached` — INGEST-ONLY compute-and-persist, the SOLE remaining caller of
    `compute_forward_aggregates`. Its single-flight guard is UNCHANGED by the split and is exercised by
    `test_forward_testing_concurrency.py`'s renamed tests (TC-17: the guard still holds post-split).
  - `resolved_forward_aggregate_evidence` — READ-ONLY serving, structurally incapable of calling
    `compute_forward_aggregates` under any circumstance. Exercised here.

This file proves:

  - completeness/cutover correctness (TC-3/4/5/18): a partial new-version warm never leaks a mixed row
    set; the read always serves ONE complete version's rows, never mixed; pruning only fires once the
    new version's configured-horizon set is complete; the completeness query is `asof_key`-filtered.
  - zero-compute correctness (TC-1/2/6/7/8): the read-only resolver AND the two request-serving entry
    points (`app.api.backtest.backtest`, `app.mcp.tools.query_backtest`, called directly as plain
    functions — no TestClient/`loaded_engine` app boot, per this session's host-guard-confined/targeted-
    tests-only constraint) never invoke `compute_forward_aggregates`, in every serving state.
  - byte-identity (TC-9, AG-3): a `ready` response's payload equals a direct fresh
    `compute_forward_aggregates` call for the same inputs.
  - the historical (`is_latest == False`) carve-out is unaffected (TC-13).

All fixtures here are small, hand-built SQLite engines (a handful of rows) — never the ~80-minute
`loaded_engine` seed+warm fixture (out of scope for this session; see docs/handoffs/goal-ops-hardening-
iter-16-dev.md).

iter-17 (audit B1) widens the resolver's fallback ACROSS `asof_key` boundaries: when the REQUESTED
identity has never had a complete version of its own, the resolver now searches strictly OLDER
identities and serves the most recent complete one, disclosing WHICH as-of via the new `evidence_asof`
field. The new tests below (iter-17 TC-1/2/4/5/6) all use an AS-OF-ADVANCING new `ScannerRun` — a
genuinely later date — never a historical gap date, per iter-16's own lesson that a gap date cannot
exercise this path (the identity resolved never changes, only the dataset stamp does).
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import event
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.forward_testing import (
    backfill_run_forward_returns,
    compute_forward_aggregates,
    compute_run_scorecard,
    forward_aggregates_ingest_cached,
    resolved_forward_aggregate_evidence,
)
from app.models import DailyPrice, ForwardAggregateCache, ForwardReturn, ScannerResult, ScannerRun

HORIZONS = load_config().walk_forward.horizons  # [1, 5, 10, 20, 60] today — read from config, never hard-coded


def _utc() -> datetime:
    return datetime.now(timezone.utc)


def _add_run(session: Session, asof: date, regime_label: str = "Risk-on") -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=_utc(), provider="seed", benchmark="SPY", regime_score=50.0,
        regime_label=regime_label, regime_components_json="[]", new_high_low_json="{}",
        candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _add_result(session: Session, run_id: int, ticker: str, rank: int = 1) -> None:
    session.add(ScannerResult(
        run_id=run_id, ticker=ticker, name=ticker, sector="Technology", leadership_score=50.0,
        leadership_bucket="A", entry_quality_score=50.0, entry_quality_bucket="B", risk_score=50.0,
        risk_bucket="C", setup_status="Actionable", rank=rank, record_json="{}", is_vcp=False,
        is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
    ))


def _add_fr_every_horizon(session: Session, run_id: int, asof: date, symbol: str, ret: float = 0.05) -> None:
    for h in HORIZONS:
        session.add(ForwardReturn(
            run_id=run_id, symbol=symbol, horizon=h, asof_date=asof, entry_close=100.0,
            measured_date=asof, realized_return=ret,
        ))


@pytest.fixture()
def evidence_engine(tmp_path):
    """ONE run (`asof`) with a stored forward return at EVERY configured horizon for ticker "AAA" — a
    small, fast fixture (not `loaded_engine`) sufficient to warm/serve one `ForwardAggregateCache`
    identity under test."""
    engine = make_engine(f"sqlite:///{tmp_path / 'evidence.db'}")
    create_db_and_tables(engine)
    asof = date(2025, 1, 10)
    with Session(engine) as session:
        run = _add_run(session, asof)
        _add_result(session, run.id, "AAA")
        _add_fr_every_horizon(session, run.id, asof, "AAA")
        session.commit()
    return engine, asof


# ======================================================================================================
# resolved_forward_aggregate_evidence — completeness / cutover / never-computed / byte-identity / TC-18
# ======================================================================================================
def test_evidence_not_yet_computed_before_any_warm(evidence_engine, monkeypatch):
    """TC-6: a store where no forward-aggregate warm has EVER completed for any version at this
    `asof_key` — the resolver returns the honest empty state (never a fabricated aggregate) with ZERO
    `compute_forward_aggregates` invocations."""
    import app.engine.forward_testing as ft_module

    engine, asof = evidence_engine
    cfg = load_config()
    call_count = {"n": 0}
    real = ft_module.compute_forward_aggregates

    def _counting(*a, **kw):
        call_count["n"] += 1
        return real(*a, **kw)

    monkeypatch.setattr(ft_module, "compute_forward_aggregates", _counting)
    with Session(engine) as session:
        evidence = resolved_forward_aggregate_evidence(session, asof, cfg)

    assert evidence == {
        "evidence_status": "not_yet_computed", "evidence_generated_at": None, "evidence_by_horizon": {},
        "evidence_asof": None,
    }
    assert call_count["n"] == 0


def test_evidence_ready_after_full_warm_is_byte_identical_and_zero_compute(evidence_engine, monkeypatch):
    """TC-1/TC-9: after the ingest warm covers every configured horizon, the resolver reports `ready`
    with a payload byte-identical to a direct fresh `compute_forward_aggregates` call for every horizon,
    and 10 repeated resolver calls invoke `compute_forward_aggregates` ZERO times."""
    import app.engine.forward_testing as ft_module

    engine, asof = evidence_engine
    cfg = load_config()
    with Session(engine) as session:
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
        session.commit()
        direct = {h: compute_forward_aggregates(session, h, cfg, as_of=asof) for h in HORIZONS}

    call_count = {"n": 0}
    real = ft_module.compute_forward_aggregates

    def _counting(*a, **kw):
        call_count["n"] += 1
        return real(*a, **kw)

    monkeypatch.setattr(ft_module, "compute_forward_aggregates", _counting)
    results = []
    for _ in range(10):
        with Session(engine) as session:
            results.append(resolved_forward_aggregate_evidence(session, asof, cfg))

    assert call_count["n"] == 0, f"expected 0 compute calls across 10 reads; got {call_count['n']}"
    for evidence in results:
        assert evidence["evidence_status"] == "ready"
        assert evidence["evidence_generated_at"] is not None
        assert evidence["evidence_by_horizon"] == direct
        # ops-hardening iter-17 (J-08, Data Contract): evidence_asof equals the requested as-of itself
        # when the served version IS the current stamp.
        assert evidence["evidence_asof"] == asof.isoformat()


def test_evidence_refreshing_serves_prior_complete_version_never_mixed(evidence_engine):
    """TC-3/TC-4: with V1 complete and V2's warm only 2-of-5 horizons done (a test-injected partial-warm
    state), the resolver serves V1's full row set byte-identically, labeled `refreshing` with V1's OWN
    generation timestamp — never a response mixing V1 and V2 horizon payloads."""
    engine, asof = evidence_engine
    cfg = load_config()
    with Session(engine) as session:
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
        session.commit()
        v1_rows = {
            row.horizon: (row.payload_json, row.created_at)
            for row in session.exec(
                select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == asof.isoformat())
            ).all()
        }
        assert set(v1_rows) == set(HORIZONS)

        # bump the GLOBAL dataset stamp via a genuinely new run+forward-returns dated AFTER `asof` (so it
        # never enters this asof_key's own expanding-window pool — only the cache identity/version shifts).
        run2 = _add_run(session, date(2025, 6, 1), "Risk-off")
        _add_result(session, run2.id, "BBB")
        _add_fr_every_horizon(session, run2.id, date(2025, 6, 1), "BBB", ret=0.10)
        session.commit()

        # warm only 2-of-5 horizons at the NEW version for the ORIGINAL asof_key (mirrors an ingest
        # finalize warm loop caught mid-flight).
        partial = HORIZONS[:2]
        for h in partial:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
        session.commit()

        rows_now = session.exec(
            select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == asof.isoformat())
        ).all()
        by_version: dict[str, set[int]] = {}
        for row in rows_now:
            by_version.setdefault(row.dataset_version, set()).add(row.horizon)
        # V1's full row set must survive (the cutover has not fired — V2 is not yet complete).
        assert set(HORIZONS) in by_version.values(), "V1's complete row set was pruned before V2 completed"

        evidence = resolved_forward_aggregate_evidence(session, asof, cfg)

    assert evidence["evidence_status"] == "refreshing"
    assert set(evidence["evidence_by_horizon"]) == set(HORIZONS)
    for h in HORIZONS:
        assert evidence["evidence_by_horizon"][h] == json.loads(v1_rows[h][0]), (
            f"horizon {h} did not come from V1 — a response mixed two dataset_versions"
        )
    # ops-hardening iter-17 (audit B3): evidence_generated_at now carries an explicit UTC designator —
    # attach it to the SAME raw (naive) created_at before formatting, mirroring the production fix, so
    # this expectation does not regress to the pre-B3 naive string.
    expected_generated_at = max(
        created_at for _payload, created_at in v1_rows.values()
    ).replace(tzinfo=timezone.utc).isoformat()
    assert evidence["evidence_generated_at"] == expected_generated_at
    # ops-hardening iter-17 (J-08, Data Contract): a SAME-asof_key stale version is still THIS date's own
    # evidence (an older compute of it, not a different date) — evidence_asof is unchanged from `asof`.
    assert evidence["evidence_asof"] == asof.isoformat()


def test_evidence_cutover_prunes_old_version_once_new_version_completes(evidence_engine):
    """TC-5: once V2's warm covers every configured horizon, the resolver flips to `ready` at V2 and
    V1's now-superseded rows for this `asof_key` are ALL pruned (0 remain for the old `dataset_version`)."""
    engine, asof = evidence_engine
    cfg = load_config()
    with Session(engine) as session:
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
        session.commit()
        v1_version = session.exec(
            select(ForwardAggregateCache.dataset_version)
            .where(ForwardAggregateCache.asof_key == asof.isoformat())
        ).first()

        run2 = _add_run(session, date(2025, 6, 1), "Risk-off")
        _add_result(session, run2.id, "BBB")
        _add_fr_every_horizon(session, run2.id, date(2025, 6, 1), "BBB", ret=0.10)
        session.commit()

        for h in HORIZONS:  # warm EVERY configured horizon at the new version -> completes it
            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
        session.commit()

        evidence = resolved_forward_aggregate_evidence(session, asof, cfg)
        remaining_old = session.exec(
            select(ForwardAggregateCache).where(
                ForwardAggregateCache.asof_key == asof.isoformat(),
                ForwardAggregateCache.dataset_version == v1_version,
            )
        ).all()

    assert evidence["evidence_status"] == "ready"
    assert remaining_old == [], "the superseded version's rows must be pruned once the new version completes"


def test_completeness_query_is_filtered_by_asof_key(evidence_engine):
    """TC-18: the completeness-lookup query `resolved_forward_aggregate_evidence` issues against
    `forward_aggregate_cache` is filtered by the requested `asof_key` — captured via SQLAlchemy's own
    `before_cursor_execute` event (the standard, non-invasive way to inspect the real SQL a call issues;
    TC-18 itself sanctions a "query plan ... assertion"), never an unfiltered scan of the whole table.
    Seeded with 50 OTHER historical identities' worth of rows so an unfiltered scan would be detectable."""
    engine, asof = evidence_engine
    cfg = load_config()
    with Session(engine) as session:
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
        for i in range(50):
            session.add(ForwardAggregateCache(
                horizon=HORIZONS[0], asof_key=f"1999-01-{(i % 28) + 1:02d}",
                dataset_version=f"other-{i}", payload_json="{}", created_at=_utc(),
            ))
        session.commit()

        total_rows = session.exec(select(ForwardAggregateCache)).all()
        assert len(total_rows) == len(HORIZONS) + 50  # sanity: the seeded "noise" is really there

        captured: list[str] = []

        def _capture(conn, cursor, statement, parameters, context, executemany):
            captured.append(statement)

        event.listen(engine, "before_cursor_execute", _capture)
        try:
            evidence = resolved_forward_aggregate_evidence(session, asof, cfg)
        finally:
            event.remove(engine, "before_cursor_execute", _capture)

    assert evidence["evidence_status"] == "ready"
    cache_selects = [
        stmt for stmt in captured
        if "forward_aggregate_cache" in stmt.lower() and stmt.strip().lower().startswith("select")
    ]
    assert cache_selects, "expected at least one SELECT against forward_aggregate_cache"
    assert all("asof_key" in stmt.lower() for stmt in cache_selects), (
        f"completeness query is not asof_key-filtered: {cache_selects}"
    )


# ======================================================================================================
# iter-17 (audit B1, the load-bearing fix) — the cross-`asof_key` last-good fallback. All three tests
# below use an AS-OF-ADVANCING new `ScannerRun` (a genuinely LATER date), never a historical gap date:
# iter-16's own lesson is that a gap-date live/unit test structurally cannot exercise this path, because
# the identity being resolved never changes — only the dataset stamp does.
# ======================================================================================================
def test_evidence_crosses_asof_key_boundary_when_newer_key_has_zero_rows(evidence_engine):
    """iter-17 TC-1: an older `asof_key` (2025-01-10) has a COMPLETE version; a NEWER `asof_key`
    (2025-01-13, a genuinely later `ScannerRun`) has ZERO forward-aggregate rows of any version — the
    common single-latest-date-backfill shape, where the newest trading day lands before its
    ingest-finalize warm has run. Resolving at the NEWER date must serve the older date's complete
    evidence, labeled `refreshing` with `evidence_asof` set to the OLDER date — never `not_yet_computed`."""
    engine, older_asof = evidence_engine  # 2025-01-10
    cfg = load_config()
    with Session(engine) as session:
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=older_asof)
        session.commit()
        older_rows = {
            row.horizon: (row.payload_json, row.created_at)
            for row in session.exec(
                select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == older_asof.isoformat())
            ).all()
        }
        assert set(older_rows) == set(HORIZONS)

        # a genuinely LATER run — the as-of identity itself advances, not just the dataset stamp.
        newer_asof = date(2025, 1, 13)
        run2 = _add_run(session, newer_asof, "Risk-off")
        _add_result(session, run2.id, "BBB")
        _add_fr_every_horizon(session, run2.id, newer_asof, "BBB", ret=0.10)
        session.commit()

        # sanity: the newer identity has ZERO ForwardAggregateCache rows of any version.
        assert session.exec(
            select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == newer_asof.isoformat())
        ).all() == []

        evidence = resolved_forward_aggregate_evidence(session, newer_asof, cfg)

    assert evidence["evidence_status"] == "refreshing"
    assert evidence["evidence_asof"] == older_asof.isoformat()
    assert set(evidence["evidence_by_horizon"]) == set(HORIZONS)
    for h in HORIZONS:
        assert evidence["evidence_by_horizon"][h] == json.loads(older_rows[h][0]), (
            f"horizon {h} did not come from the older asof_key's own stored rows"
        )


def test_evidence_crosses_asof_key_boundary_picks_more_recent_of_two_older_complete_keys(evidence_engine):
    """iter-17 TC-4: with TWO older, independently-complete `asof_key`s (2025-01-08 and 2025-01-10) and
    the requested `asof_key` (2025-01-13) itself carrying zero rows, the served `evidence_asof` is the
    MORE RECENT of the two (2025-01-10) — never the older one (2025-01-08), and never a response mixing
    rows from both dates."""
    engine, asof_1_10 = evidence_engine  # 2025-01-10
    cfg = load_config()
    with Session(engine) as session:
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof_1_10)
        session.commit()
        rows_1_10 = {
            row.horizon: (row.payload_json, row.created_at)
            for row in session.exec(
                select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == asof_1_10.isoformat())
            ).all()
        }

        # a SECOND, independent older identity (2025-01-08, strictly before 2025-01-10) with its OWN
        # complete row set, from a different cohort so its aggregate genuinely differs from 2025-01-10's.
        asof_1_08 = date(2025, 1, 8)
        run_08 = _add_run(session, asof_1_08, "Risk-on")
        _add_result(session, run_08.id, "CCC")
        _add_fr_every_horizon(session, run_08.id, asof_1_08, "CCC", ret=0.02)
        session.commit()
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof_1_08)
        session.commit()

        # the requested identity: a genuinely later run, zero forward-aggregate rows of its own.
        newer_asof = date(2025, 1, 13)
        run_newer = _add_run(session, newer_asof, "Risk-off")
        _add_result(session, run_newer.id, "DDD")
        _add_fr_every_horizon(session, run_newer.id, newer_asof, "DDD", ret=0.10)
        session.commit()

        evidence = resolved_forward_aggregate_evidence(session, newer_asof, cfg)

    assert evidence["evidence_status"] == "refreshing"
    assert evidence["evidence_asof"] == asof_1_10.isoformat(), "must serve the MORE RECENT older key"
    for h in HORIZONS:
        assert evidence["evidence_by_horizon"][h] == json.loads(rows_1_10[h][0]), (
            f"horizon {h} leaked a row from the OTHER older asof_key (2025-01-08) — versions mixed across dates"
        )


def test_evidence_fallback_never_reads_a_row_dated_after_the_requested_as_of(evidence_engine):
    """iter-17 TC-5 (AG-5 no-lookahead): once the fallback crosses to older `asof_key`s, it never reads
    or serves a row dated AFTER the requested as-of — verified via the same `before_cursor_execute`
    SQL-inspection technique `test_completeness_query_is_filtered_by_asof_key` (TC-18) already uses.
    Seeded with a LATER-dated, fully-complete identity that must never be selected for an earlier
    request; the outcome assertion (`evidence_asof` resolving to the OLDER date, never the future one) is
    the strongest proof — if the future row had been read and let into the tie-break, it would win
    (its `asof_key` string sorts higher), so a wrong `evidence_asof` would itself expose a lookahead bug."""
    engine, older_asof = evidence_engine  # 2025-01-10
    cfg = load_config()
    with Session(engine) as session:
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=older_asof)
        session.commit()

        # a LATER-dated, fully complete identity that must NEVER be read for the earlier request below.
        future_asof = date(2025, 6, 1)
        run_future = _add_run(session, future_asof, "Risk-off")
        _add_result(session, run_future.id, "EEE")
        _add_fr_every_horizon(session, run_future.id, future_asof, "EEE", ret=0.20)
        session.commit()
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=future_asof)
        session.commit()

        # the actual request: a genuinely new latest run, strictly BETWEEN older_asof and future_asof,
        # with zero forward-aggregate rows of its own — must fall back to older_asof, never future_asof.
        requested_asof = date(2025, 2, 1)
        run_req = _add_run(session, requested_asof, "Risk-on")
        _add_result(session, run_req.id, "FFF")
        _add_fr_every_horizon(session, run_req.id, requested_asof, "FFF", ret=0.03)
        session.commit()

        captured: list[str] = []

        def _capture(conn, cursor, statement, parameters, context, executemany):
            captured.append(statement)

        event.listen(engine, "before_cursor_execute", _capture)
        try:
            evidence = resolved_forward_aggregate_evidence(session, requested_asof, cfg)
        finally:
            event.remove(engine, "before_cursor_execute", _capture)

    assert evidence["evidence_status"] == "refreshing"
    assert evidence["evidence_asof"] == older_asof.isoformat(), "must serve the older key, never the future one"

    cache_selects = [
        stmt for stmt in captured
        if "forward_aggregate_cache" in stmt.lower() and stmt.strip().lower().startswith("select")
    ]
    assert cache_selects, "expected at least one SELECT against forward_aggregate_cache"
    assert not any(">" in stmt for stmt in cache_selects), (
        f"a forward_aggregate_cache query used a >/>= comparison — possible lookahead: {cache_selects}"
    )
    assert any("<" in stmt for stmt in cache_selects), (
        "expected the widened fallback's completeness query to filter with asof_key < :requested"
    )


# ======================================================================================================
# iter-18 (cheap win, TC-5/TC-6) — the widened fallback's candidate-selection scan defers `payload_json`
# to a single winner-only follow-up query. SQL-inspected via the SAME `before_cursor_execute` technique
# `test_completeness_query_is_filtered_by_asof_key` (TC-18) and
# `test_evidence_fallback_never_reads_a_row_dated_after_the_requested_as_of` (iter-17 TC-5) already use.
# ======================================================================================================
def test_widened_fallback_defers_payload_json_to_a_single_winner_only_query(evidence_engine):
    """iter-18 TC-5/TC-6: with SEVERAL older `(asof_key, dataset_version)` candidates and exactly ONE
    complete, the widened fallback's initial candidate-selection scan (the `<`-filtered query) never
    names `payload_json`; exactly ONE follow-up query, filtered to the winning `(asof_key,
    dataset_version)` pair, selects it. Served evidence is byte-identical to the pre-iter-18 single-query
    shape (TC-6, a regression guard mirroring `test_evidence_crosses_asof_key_boundary_when_newer_key_
    has_zero_rows`'s own assertions) — same fixture pattern as that test, extended with two further
    INCOMPLETE older candidates so "several ... exactly one complete" is genuinely exercised."""
    engine, complete_asof = evidence_engine  # 2025-01-10 -- becomes the one COMPLETE older candidate
    cfg = load_config()
    with Session(engine) as session:
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=complete_asof)
        session.commit()
        complete_rows = {
            row.horizon: (row.payload_json, row.created_at)
            for row in session.exec(
                select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == complete_asof.isoformat())
            ).all()
        }
        assert set(complete_rows) == set(HORIZONS)

        # two further OLDER candidates, each genuinely INCOMPLETE (2-of-5 horizons only) -- "several"
        # candidates get scanned, but neither can ever win, so their payload is never needed.
        for i, partial_asof in enumerate((date(2025, 1, 2), date(2025, 1, 5))):
            prun = _add_run(session, partial_asof, "Risk-on")
            _add_result(session, prun.id, f"PP{i}")
            _add_fr_every_horizon(session, prun.id, partial_asof, f"PP{i}", ret=0.01)
            session.commit()
            for h in HORIZONS[:2]:
                forward_aggregates_ingest_cached(session, h, cfg, as_of=partial_asof)
            session.commit()

        # the requested identity: a genuinely later run, zero forward-aggregate rows of its own -- so
        # the widened fallback runs.
        requested_asof = date(2025, 1, 13)
        req_run = _add_run(session, requested_asof, "Risk-off")
        _add_result(session, req_run.id, "REQ")
        _add_fr_every_horizon(session, req_run.id, requested_asof, "REQ", ret=0.05)
        session.commit()

        captured: list[str] = []

        def _capture(conn, cursor, statement, parameters, context, executemany):
            captured.append(statement)

        event.listen(engine, "before_cursor_execute", _capture)
        try:
            evidence = resolved_forward_aggregate_evidence(session, requested_asof, cfg)
        finally:
            event.remove(engine, "before_cursor_execute", _capture)

    # TC-6: byte-identical served evidence (never mixed, never re-derived).
    assert evidence["evidence_status"] == "refreshing"
    assert evidence["evidence_asof"] == complete_asof.isoformat()
    assert set(evidence["evidence_by_horizon"]) == set(HORIZONS)
    for h in HORIZONS:
        assert evidence["evidence_by_horizon"][h] == json.loads(complete_rows[h][0]), (
            f"horizon {h} did not come from the winning candidate's own stored rows"
        )

    # TC-5: the query-shape assertion — the widened candidate scan never selects payload_json; exactly
    # one exact-match follow-up query (asof_key AND dataset_version, never a `<` range) does.
    cache_selects = [
        stmt for stmt in captured
        if "forward_aggregate_cache" in stmt.lower() and stmt.strip().lower().startswith("select")
    ]
    widened_scan_selects = [stmt for stmt in cache_selects if "<" in stmt]
    assert widened_scan_selects, "expected the widened fallback's candidate-selection scan to run"
    assert all("payload_json" not in stmt.lower() for stmt in widened_scan_selects), (
        f"the widened candidate-selection scan must not select payload_json: {widened_scan_selects}"
    )
    # `dataset_version = ?` (a comparison, not merely a selected column) is what distinguishes the
    # winner-only query from the pre-existing same-key query at the top of the function, which ALSO
    # selects `payload_json` + `dataset_version` as columns but never filters ON `dataset_version`.
    winner_selects = [stmt for stmt in cache_selects if "payload_json" in stmt.lower() and "dataset_version = ?" in stmt.lower()]
    assert len(winner_selects) == 1, (
        f"expected exactly one winner-only payload_json follow-up query; got {len(winner_selects)}: {winner_selects}"
    )
    assert "<" not in winner_selects[0], "the winner-only follow-up must be an exact-match filter, not a range scan"


# ======================================================================================================
# Request-serving entry points (app.api.backtest.backtest, app.mcp.tools.query_backtest) — called
# directly as plain functions (no TestClient/`loaded_engine` app boot) to prove the WIRING: the
# `is_latest` branch reaches ONLY the read-only resolver, never `forward_aggregates_ingest_cached` (and
# therefore never `compute_forward_aggregates`), in every serving state.
# ======================================================================================================
@pytest.fixture()
def endpoint_engine(evidence_engine):
    """`evidence_engine` plus ONE `DailyPrice` bar — `resolved_run`'s `latest_data_date` check needs at
    least one bar to exist at all (`test_backtest_503_when_no_price_data` proves the 503 path with zero);
    `run_scan`'s existing-row fast path means no OTHER price data is needed since the run already exists."""
    engine, asof = evidence_engine
    with Session(engine) as session:
        session.add(DailyPrice(
            symbol="AAA", date=asof, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
        ))
        session.commit()
    return engine, asof


def test_backtest_route_is_latest_never_reaches_ingest_or_compute(endpoint_engine, monkeypatch):
    """TC-1/TC-8 (endpoint layer): for the LATEST view, `GET /api/backtest`'s route function calls ONLY
    the read-only resolver — it never calls `forward_aggregates_ingest_cached` (and therefore never
    `compute_forward_aggregates`), structurally, across 10 repeated `ready`-state requests."""
    import app.api.backtest as backtest_module

    engine, asof = endpoint_engine
    cfg = load_config()
    with Session(engine) as session:
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
        session.commit()

    def _boom(*a, **kw):
        raise AssertionError("the is_latest read path must never call the ingest/compute function")

    monkeypatch.setattr(backtest_module, "forward_aggregates_ingest_cached", _boom)
    responses = []
    for _ in range(10):
        with Session(engine) as session:
            responses.append(backtest_module.backtest(as_of=None, session=session))

    assert all(r["is_latest"] is True for r in responses)
    assert all(r["evidence_status"] == "ready" for r in responses)
    assert all(r["evidence_generated_at"] for r in responses)
    assert all(r["evidence_asof"] == asof.isoformat() for r in responses)
    first = responses[0]["evidence_by_horizon"]
    assert all(r["evidence_by_horizon"] == first for r in responses[1:])
    assert set(first) == set(HORIZONS)


def test_backtest_route_is_latest_not_yet_computed_is_honest_200(endpoint_engine, monkeypatch, caplog):
    """TC-6/TC-8 (endpoint layer, iter-16 numbering): a never-warmed store still answers (no exception,
    no fabricated evidence) with the honest empty state — and never calls the ingest/compute function.

    iter-18 TC-8 (added to this SAME test, its own separate numbering): instrumentation must never turn
    this honest-empty-state path into a 500 or silently skip logging on it — a timing log line is still
    emitted for the request."""
    import app.api.backtest as backtest_module

    engine, asof = endpoint_engine

    def _boom(*a, **kw):
        raise AssertionError("the is_latest read path must never call the ingest/compute function")

    monkeypatch.setattr(backtest_module, "forward_aggregates_ingest_cached", _boom)
    caplog.set_level(logging.INFO, logger="trendora.backtest")
    with Session(engine) as session:
        result = backtest_module.backtest(as_of=None, session=session)

    assert result["is_latest"] is True
    assert result["evidence_status"] == "not_yet_computed"
    assert result["evidence_by_horizon"] == {}
    assert result["evidence_generated_at"] is None
    assert result["evidence_asof"] is None

    # iter-18 TC-8: the honest empty state still emits a timing log line (never silently skipped).
    timing_records = [
        r for r in caplog.records if r.name == "trendora.backtest" and "backtest_timing" in r.getMessage()
    ]
    assert len(timing_records) == 1, (
        f"expected a timing log line even for the not_yet_computed empty state; got {len(timing_records)}"
    )


def test_query_backtest_mcp_tool_is_latest_never_reaches_ingest_or_compute(endpoint_engine, monkeypatch):
    """TC-2/TC-7 (MCP layer): mirrors the endpoint-layer proof above for the MCP `query_backtest` tool —
    the LATEST view never calls `forward_aggregates_ingest_cached`, across both the `ready` state (warmed
    first) and repeated calls."""
    import app.mcp.tools as tools_module

    engine, asof = endpoint_engine
    cfg = load_config()
    with Session(engine) as session:
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
        session.commit()

    def _boom(*a, **kw):
        raise AssertionError("the is_latest read path must never call the ingest/compute function")

    monkeypatch.setattr(tools_module, "forward_aggregates_ingest_cached", _boom)
    responses = []
    for _ in range(10):
        with Session(engine) as session:
            responses.append(tools_module.query_backtest(session, asof=None))

    assert all(r["is_latest"] is True for r in responses)
    assert all(r["evidence_status"] == "ready" for r in responses)
    assert all(r["evidence_asof"] == asof.isoformat() for r in responses)
    first = responses[0]["evidence_by_horizon"]
    assert all(r["evidence_by_horizon"] == first for r in responses[1:])


def test_query_backtest_mcp_tool_not_yet_computed_mirrors_endpoint(endpoint_engine, monkeypatch):
    """TC-7: the MCP tool's never-warmed shape mirrors the endpoint's (same `evidence_status` /
    `evidence_by_horizon` / `evidence_generated_at`), with zero `compute_forward_aggregates` calls."""
    import app.mcp.tools as tools_module

    engine, asof = endpoint_engine

    def _boom(*a, **kw):
        raise AssertionError("the is_latest read path must never call the ingest/compute function")

    monkeypatch.setattr(tools_module, "forward_aggregates_ingest_cached", _boom)
    with Session(engine) as session:
        result = tools_module.query_backtest(session, asof=None)

    assert result["is_latest"] is True
    assert result["evidence_status"] == "not_yet_computed"
    assert result["evidence_by_horizon"] == {}
    assert result["evidence_generated_at"] is None
    assert result["evidence_asof"] is None


def test_backtest_route_and_mcp_tool_serve_evidence_asof_identically(endpoint_engine):
    """iter-17 TC-2: given the SAME fixture, `GET /api/backtest`'s route function and the MCP
    `query_backtest` tool both surface `evidence_asof` — identically to each other, and equal to the
    resolved as-of date when the served version is the current (`ready`) stamp."""
    import app.api.backtest as backtest_module
    import app.mcp.tools as tools_module

    engine, asof = endpoint_engine
    cfg = load_config()
    with Session(engine) as session:
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
        session.commit()

    with Session(engine) as session:
        api_result = backtest_module.backtest(as_of=None, session=session)
    with Session(engine) as session:
        mcp_result = tools_module.query_backtest(session, asof=None)

    assert api_result["evidence_status"] == "ready"
    assert mcp_result["evidence_status"] == "ready"
    assert api_result["evidence_asof"] == asof.isoformat()
    assert mcp_result["evidence_asof"] == asof.isoformat()
    assert api_result["evidence_asof"] == mcp_result["evidence_asof"]


def test_backtest_route_and_mcp_tool_serve_older_evidence_asof_across_boundary(endpoint_engine):
    """iter-18 TC-7: the ONE missing endpoint-level test for the iter-17 widened cross-`asof_key`
    fallback — an OLDER `evidence_asof` survives end-to-end through BOTH `GET /api/backtest`'s route
    function and the MCP `query_backtest` tool (today's cross-boundary coverage is resolver-level only —
    every existing test exercising this shape calls `resolved_forward_aggregate_evidence` directly).
    Mirrors `test_evidence_crosses_asof_key_boundary_when_newer_key_has_zero_rows`'s fixture shape,
    calling the endpoint functions the way `test_backtest_route_and_mcp_tool_serve_evidence_asof_
    identically` (directly above) does."""
    import app.api.backtest as backtest_module
    import app.mcp.tools as tools_module

    engine, older_asof = endpoint_engine  # 2025-01-10, already has a DailyPrice bar for "AAA"
    cfg = load_config()
    with Session(engine) as session:
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=older_asof)
        session.commit()

        # a genuinely LATER run — the LATEST as-of identity itself, with zero forward-aggregate rows of
        # its own (the common single-latest-date-backfill shape the iter-17 fix targets).
        newer_asof = date(2025, 1, 13)
        run2 = _add_run(session, newer_asof, "Risk-off")
        _add_result(session, run2.id, "BBB")
        session.add(DailyPrice(
            symbol="BBB", date=newer_asof, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
        ))
        session.commit()

    with Session(engine) as session:
        api_result = backtest_module.backtest(as_of=None, session=session)
    with Session(engine) as session:
        mcp_result = tools_module.query_backtest(session, asof=None)

    assert api_result["is_latest"] is True
    assert mcp_result["is_latest"] is True
    assert api_result["evidence_status"] == "refreshing"
    assert mcp_result["evidence_status"] == "refreshing"
    assert api_result["evidence_asof"] == older_asof.isoformat()
    assert mcp_result["evidence_asof"] == older_asof.isoformat()
    assert api_result["evidence_asof"] == mcp_result["evidence_asof"]


def test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior(endpoint_engine, monkeypatch):
    """TC-13: a historical (`is_latest == False`) `?as_of=` request still computes-once-and-caches on
    first view (UNCHANGED, the explicit carve-out) — a SECOND, older run with no forward-aggregate warm
    at all is requested (is_latest is False since a later run exists): a real compute happens once per
    configured horizon on the FIRST call and NOT AT ALL on the second (cached) call."""
    import app.api.backtest as backtest_module
    import app.engine.forward_testing as ft_module

    engine, latest_asof = endpoint_engine
    older_asof = date(2024, 1, 10)
    with Session(engine) as session:
        older_run = _add_run(session, older_asof, "Risk-on")
        _add_result(session, older_run.id, "AAA")
        # No post-snapshot bar exists for "AAA" after `older_asof` in this minimal fixture, so
        # `backfill_run_forward_returns` (called inside the route, unchanged) inserts nothing — this test
        # asserts only the COMPUTE-CALL-COUNT behavior (TC-13's actual claim), not non-empty content.
        session.add(DailyPrice(
            symbol="AAA", date=older_asof, open=90.0, high=91.0, low=89.0, close=90.0, volume=1.0,
        ))
        session.commit()

    call_count = {"n": 0}
    real = ft_module.compute_forward_aggregates

    def _counting(*a, **kw):
        call_count["n"] += 1
        return real(*a, **kw)

    monkeypatch.setattr(ft_module, "compute_forward_aggregates", _counting)
    with Session(engine) as session:
        first = backtest_module.backtest(as_of=older_asof.isoformat(), session=session)
    first_calls = call_count["n"]
    with Session(engine) as session:
        second = backtest_module.backtest(as_of=older_asof.isoformat(), session=session)

    assert first["is_latest"] is False
    assert second["is_latest"] is False
    assert first_calls == len(HORIZONS), "expected one real compute per configured horizon on first view"
    assert call_count["n"] == first_calls, "the second (cached) view must trigger zero MORE computes"
    assert first["evidence_status"] == "ready"
    assert first["evidence_asof"] == older_asof.isoformat()
    assert second["evidence_by_horizon"] == first["evidence_by_horizon"]


def test_historical_asof_still_computes_once_even_when_older_fallback_evidence_exists(
    endpoint_engine, monkeypatch
):
    """iter-17 TC-6 (regression guard, mirrors `test_historical_asof_keeps_pre_iter16_create_once_and_
    cache_behavior` above): a historical (`is_latest == False`) `?as_of=` request still computes-once-
    and-caches ITS OWN evidence on first view, and must NEVER be short-circuited by the iter-17 widened
    fallback finding an UNRELATED older `asof_key`'s complete evidence first. `backtest.py`'s audit-B5
    gate is `evidence_status != "ready"` — which `"refreshing"` also satisfies — deliberately NOT
    `== "not_yet_computed"`, which would wrongly skip the ensure-loop and serve the fallback's stale,
    wrong-date evidence instead of computing this date's own."""
    import app.api.backtest as backtest_module
    import app.engine.forward_testing as ft_module

    engine, _latest_asof = endpoint_engine
    cfg = load_config()

    # an OLDER, fully-warmed complete identity the iter-17 widened fallback WOULD find first for any
    # request whose own asof_key has zero forward-aggregate rows.
    fallback_asof = date(2024, 1, 5)
    with Session(engine) as session:
        fallback_run = _add_run(session, fallback_asof, "Risk-on")
        _add_result(session, fallback_run.id, "GGG")
        _add_fr_every_horizon(session, fallback_run.id, fallback_asof, "GGG")
        session.commit()
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=fallback_asof)
        session.commit()

    # the requested historical date: strictly AFTER fallback_asof (so the widened fallback lands on it)
    # and strictly BEFORE the fixture's own latest date (so is_latest stays False); its own
    # forward-aggregate cache is EMPTY, so the resolver's FIRST read must land on "refreshing" via the
    # widened fallback to fallback_asof, never "ready", before the ensure-loop below ever runs.
    requested_asof = date(2024, 6, 1)
    with Session(engine) as session:
        req_run = _add_run(session, requested_asof, "Risk-off")
        _add_result(session, req_run.id, "HHH")
        session.add(DailyPrice(
            symbol="HHH", date=requested_asof, open=50.0, high=51.0, low=49.0, close=50.0, volume=1.0,
        ))
        session.commit()

    call_count = {"n": 0}
    real = ft_module.compute_forward_aggregates

    def _counting(*a, **kw):
        call_count["n"] += 1
        return real(*a, **kw)

    monkeypatch.setattr(ft_module, "compute_forward_aggregates", _counting)
    with Session(engine) as session:
        first = backtest_module.backtest(as_of=requested_asof.isoformat(), session=session)
    first_calls = call_count["n"]
    with Session(engine) as session:
        second = backtest_module.backtest(as_of=requested_asof.isoformat(), session=session)

    assert first["is_latest"] is False
    assert first_calls == len(HORIZONS), "expected one real compute per configured horizon on first view"
    assert call_count["n"] == first_calls, "the second (cached) view must trigger zero MORE computes"
    assert first["evidence_status"] == "ready"
    assert first["evidence_asof"] == requested_asof.isoformat(), (
        "the historical view must serve ITS OWN freshly computed evidence, never the fallback's older date"
    )
    assert second["evidence_status"] == "ready"
    assert second["evidence_asof"] == requested_asof.isoformat()
    assert second["evidence_by_horizon"] == first["evidence_by_horizon"]


# ======================================================================================================
# ops-hardening iter-19 (J-06/J-07/J-08 shared latency blocker) — `backfill_run_forward_returns`'s new
# zero-write guard (forward_testing.py ~line 1365). Iter-18's operator-supervised TC-9 re-measurement
# (966 requests, host-guard-confined) pinned this function as the phase costing 881ms mean / 999ms max
# under 6x concurrency (82.2% of each slow request) — it was invoked UNCONDITIONALLY on every
# `GET /api/backtest` / MCP `query_backtest` request, including the common case where the run's forward
# returns are ALREADY fully backfilled (the ingest finalize path, data_manager.py:2918, already does this
# at creation). The fix: skip the write-lock-acquiring commit entirely when the pre-existing idempotency
# check (`_insert_run_forward_returns`'s own return count) finds zero rows missing — no new query. The
# genuinely-missing case is UNCHANGED (still inserts + commits synchronously, idempotent, race-tolerant).
#
# TC-1/TC-2/TC-3/TC-5 below; TC-4 (the mandatory concurrency proof) lives in
# test_forward_testing_concurrency.py, co-located with but DISTINCT from that file's existing
# forward-*aggregate* concurrency tests (this guards forward-*returns* — a different table/function).
# ======================================================================================================
def test_backtest_route_zero_write_when_forward_returns_already_complete(endpoint_engine, caplog):
    """iter-19 TC-1: given a run whose forward returns are already fully backfilled for every configured
    horizon (the scored ticker "AAA" — the benchmark ETFs have no price data in this fixture, so they
    contribute nothing: an honest NA gap, never a partial insert), `GET /api/backtest`'s route function
    issues ZERO INSERT/UPDATE/DELETE statements during the request (SQL-inspected via the SAME
    `before_cursor_execute` technique `test_completeness_query_is_filtered_by_asof_key` already uses),
    HTTP 200 (a clean plain-function return), and the extended `backtest_timing` log line records the
    write as skipped (`write_taken=False`)."""
    import app.api.backtest as backtest_module

    engine, asof = endpoint_engine  # "AAA" already has a ForwardReturn row at every configured horizon
    cfg = load_config()
    with Session(engine) as session:
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
        session.commit()

    captured: list[str] = []

    def _capture(conn, cursor, statement, parameters, context, executemany):
        captured.append(statement)

    caplog.set_level(logging.INFO, logger="trendora.backtest")
    with Session(engine) as session:
        event.listen(engine, "before_cursor_execute", _capture)
        try:
            result = backtest_module.backtest(as_of=None, session=session)
        finally:
            event.remove(engine, "before_cursor_execute", _capture)

    assert result["is_latest"] is True
    write_statements = [
        stmt for stmt in captured if stmt.strip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
    ]
    assert write_statements == [], (
        f"expected zero write statements on the already-complete path; got {write_statements}"
    )

    timing_records = [
        r for r in caplog.records if r.name == "trendora.backtest" and "backtest_timing" in r.getMessage()
    ]
    assert len(timing_records) == 1, f"expected exactly one timing log line; got {len(timing_records)}"
    assert "write_taken=False" in timing_records[0].getMessage(), (
        f"expected the timing log to record the skipped write; got {timing_records[0].getMessage()!r}"
    )


def test_query_backtest_mcp_tool_zero_write_when_forward_returns_already_complete(endpoint_engine, caplog):
    """iter-19 TC-2: mirrors TC-1 for the MCP `query_backtest` tool — zero write statements on the
    already-complete path, the timing log records `write_taken=False` too, and its returned scorecard +
    evidence_* fields are byte-identical to `GET /api/backtest`'s response for the SAME inputs (the two
    callers share the exact same underlying guarded function; this proves cross-entry-point parity
    survives the new guard)."""
    import app.api.backtest as backtest_module
    import app.mcp.tools as tools_module

    engine, asof = endpoint_engine
    cfg = load_config()
    with Session(engine) as session:
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
        session.commit()

    with Session(engine) as session:
        api_result = backtest_module.backtest(as_of=None, session=session)

    captured: list[str] = []

    def _capture(conn, cursor, statement, parameters, context, executemany):
        captured.append(statement)

    caplog.set_level(logging.INFO, logger="trendora.mcp_backtest")
    with Session(engine) as session:
        event.listen(engine, "before_cursor_execute", _capture)
        try:
            mcp_result = tools_module.query_backtest(session, asof=None)
        finally:
            event.remove(engine, "before_cursor_execute", _capture)

    write_statements = [
        stmt for stmt in captured if stmt.strip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
    ]
    assert write_statements == [], (
        f"expected zero write statements on the already-complete path; got {write_statements}"
    )
    assert mcp_result["is_latest"] is True
    assert mcp_result == api_result, "MCP query_backtest must serve byte-identical output to the API route"

    timing_records = [
        r for r in caplog.records
        if r.name == "trendora.mcp_backtest" and "query_backtest_timing" in r.getMessage()
    ]
    assert len(timing_records) == 1
    assert "write_taken=False" in timing_records[0].getMessage()


def test_backfill_still_inserts_when_genuinely_missing_then_zero_write_on_repeat(tmp_path, caplog):
    """iter-19 TC-3: given a run whose forward returns have NEVER been backfilled, `GET /api/backtest`
    still INSERTs the missing rows exactly as before this iteration (idempotent, INSERT-only — the one
    scored ticker "AAA" has sufficient post-snapshot bars for every configured horizon, so its row count
    equals `len(HORIZONS)`; the benchmark ETFs have no price data in this fixture, an honest NA gap, not
    a partial insert), and a SECOND call for the SAME as-of issues ZERO further write statements (the new
    guard's zero-write path) — with the timing log recording `write_taken=True` on the first call and
    `write_taken=False` on the second."""
    import app.api.backtest as backtest_module

    engine = make_engine(f"sqlite:///{tmp_path / 'tc3_missing.db'}")
    create_db_and_tables(engine)
    asof = date(2025, 1, 10)
    max_h = max(HORIZONS)
    with Session(engine) as session:
        run = _add_run(session, asof)
        run_id = run.id
        _add_result(session, run_id, "AAA")
        session.add(DailyPrice(
            symbol="AAA", date=asof, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
        ))
        for i in range(1, max_h + 1):
            session.add(DailyPrice(
                symbol="AAA", date=asof + timedelta(days=i), open=100.0, high=101.0, low=99.0,
                close=100.0 + i, volume=1.0,
            ))
        session.commit()

    caplog.set_level(logging.INFO, logger="trendora.backtest")
    first_captured: list[str] = []

    def _capture_first(conn, cursor, statement, parameters, context, executemany):
        first_captured.append(statement)

    with Session(engine) as session:
        event.listen(engine, "before_cursor_execute", _capture_first)
        try:
            first = backtest_module.backtest(as_of=asof.isoformat(), session=session)
        finally:
            event.remove(engine, "before_cursor_execute", _capture_first)

    insert_statements = [s for s in first_captured if s.strip().upper().startswith("INSERT")]
    assert insert_statements, "expected the genuinely-missing case to still INSERT forward-return rows"

    with Session(engine) as session:
        fr_rows = session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run_id)).all()
    assert len(fr_rows) == len(HORIZONS), (
        f"expected exactly one row per configured horizon for the one scored ticker with price data "
        f"(benchmarks have no price data in this fixture, an honest NA gap); got {len(fr_rows)}"
    )
    assert {fr.horizon for fr in fr_rows} == set(HORIZONS)
    assert {fr.symbol for fr in fr_rows} == {"AAA"}

    first_timing = [
        r for r in caplog.records if r.name == "trendora.backtest" and "backtest_timing" in r.getMessage()
    ]
    assert len(first_timing) == 1
    assert "write_taken=True" in first_timing[0].getMessage(), (
        f"expected the first (genuinely-missing) call to record a taken write; got "
        f"{first_timing[0].getMessage()!r}"
    )

    caplog.clear()
    second_captured: list[str] = []

    def _capture_second(conn, cursor, statement, parameters, context, executemany):
        second_captured.append(statement)

    with Session(engine) as session:
        event.listen(engine, "before_cursor_execute", _capture_second)
        try:
            second = backtest_module.backtest(as_of=asof.isoformat(), session=session)
        finally:
            event.remove(engine, "before_cursor_execute", _capture_second)

    second_write_statements = [
        s for s in second_captured if s.strip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
    ]
    assert second_write_statements == [], (
        f"expected zero write statements on the second (repeat) view; got {second_write_statements}"
    )
    second_timing = [
        r for r in caplog.records if r.name == "trendora.backtest" and "backtest_timing" in r.getMessage()
    ]
    assert len(second_timing) == 1
    assert "write_taken=False" in second_timing[0].getMessage()
    assert first["is_latest"] is True
    assert second["is_latest"] is True
    assert second["scorecard"] == first["scorecard"], "the repeat view must serve the SAME stored scorecard"


def test_scorecard_and_evidence_byte_identical_with_and_without_explicit_as_of(endpoint_engine):
    """iter-19 TC-5 (AG-3): `compute_run_scorecard` plus the evidence_* fields served by `GET
    /api/backtest` for the already-backfilled TC-1 fixture are byte-for-byte identical to a DIRECT,
    independent call to `compute_run_scorecard` / `resolved_forward_aggregate_evidence` for the same
    as-of — proving the new zero-write guard changes ONLY whether a redundant commit happens, never a
    served value. Checked BOTH with `as_of` omitted (defaults to latest) and with the SAME date passed
    explicitly, across every configured horizon."""
    import app.api.backtest as backtest_module

    engine, asof = endpoint_engine
    cfg = load_config()
    with Session(engine) as session:
        for h in HORIZONS:
            forward_aggregates_ingest_cached(session, h, cfg, as_of=asof)
        session.commit()
        run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == asof)).one()
        direct_card = compute_run_scorecard(session, run, cfg)
        direct_evidence = resolved_forward_aggregate_evidence(session, asof, cfg)

    with Session(engine) as session:
        omitted_result = backtest_module.backtest(as_of=None, session=session)
    with Session(engine) as session:
        explicit_result = backtest_module.backtest(as_of=asof.isoformat(), session=session)

    assert set(direct_evidence["evidence_by_horizon"]) == set(HORIZONS)
    for label, result in (("omitted", omitted_result), ("explicit", explicit_result)):
        assert result["scorecard"] == direct_card["scorecard"], f"{label}: scorecard differs"
        assert result["asof_date"] == direct_card["asof_date"], f"{label}: asof_date differs"
        assert result["min_sample"] == direct_card["min_sample"], f"{label}: min_sample differs"
        assert result["horizons"] == direct_card["horizons"], f"{label}: horizons differ"
        assert result["survivorship_bias"] == direct_card["survivorship_bias"], (
            f"{label}: survivorship_bias differs"
        )
        assert result["evidence_status"] == direct_evidence["evidence_status"], (
            f"{label}: evidence_status differs"
        )
        assert result["evidence_generated_at"] == direct_evidence["evidence_generated_at"], (
            f"{label}: evidence_generated_at differs"
        )
        assert result["evidence_asof"] == direct_evidence["evidence_asof"], f"{label}: evidence_asof differs"
        assert result["evidence_by_horizon"] == direct_evidence["evidence_by_horizon"], (
            f"{label}: evidence_by_horizon differs"
        )


def test_iter19_partial_backfill_run_is_detected_incomplete_and_completed(tmp_path):
    """iter-19 completeness-preservation (guards the column-projected idempotency read): the cheaper
    existence check must still detect a PARTIALLY-backfilled run as incomplete at the (symbol, horizon)
    grain and fill EXACTLY the gap — proving projecting `(symbol, horizon)` instead of materializing full
    `ForwardReturn` ORM rows did not change create-once / idempotent completeness semantics. A run is
    fully backfilled, a proper SUBSET of horizons is then deleted (simulating a partial backfill), and
    `backfill_run_forward_returns` must re-insert exactly the deleted keys (not all, not none), with a
    subsequent call inserting zero (the pure warm read the TC-6 fix targets)."""
    if len(HORIZONS) < 2:
        pytest.skip("needs >= 2 configured horizons to delete a proper subset")

    engine = make_engine(f"sqlite:///{tmp_path / 'iter19_partial.db'}")
    create_db_and_tables(engine)
    cfg = load_config()
    asof = date(2025, 1, 10)
    max_h = max(HORIZONS)
    deleted_horizons = set(HORIZONS[: len(HORIZONS) // 2])  # a non-empty proper subset, e.g. {1, 5}

    with Session(engine) as session:
        run = _add_run(session, asof)
        run_id = run.id
        _add_result(session, run_id, "AAA")
        # Entry close ON D plus max_h post-D bars so EVERY configured horizon can produce a row (only the
        # scored "AAA" has price data; benchmark ETFs are an honest NA gap, mirroring TC-3's fixture).
        session.add(DailyPrice(
            symbol="AAA", date=asof, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
        ))
        for i in range(1, max_h + 1):
            session.add(DailyPrice(
                symbol="AAA", date=asof + timedelta(days=i), open=100.0, high=101.0, low=99.0,
                close=100.0 + i, volume=1.0,
            ))
        session.commit()

    # 1. Full backfill: one row per configured horizon for the one scored ticker.
    with Session(engine) as session:
        run = session.exec(select(ScannerRun).where(ScannerRun.id == run_id)).one()
        full = backfill_run_forward_returns(session, run, cfg)
    assert full["rows_inserted"] == len(HORIZONS)

    # 2. Delete a proper SUBSET of horizons -> a genuinely partial run.
    with Session(engine) as session:
        for fr in session.exec(
            select(ForwardReturn).where(
                ForwardReturn.run_id == run_id,
                ForwardReturn.horizon.in_(sorted(deleted_horizons)),
            )
        ).all():
            session.delete(fr)
        session.commit()
        remaining = session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run_id)).all()
    assert len(remaining) == len(HORIZONS) - len(deleted_horizons)
    assert {fr.horizon for fr in remaining} == set(HORIZONS) - deleted_horizons

    # 3. Re-backfill: the projected existence read must detect the partial state and fill EXACTLY the gap.
    with Session(engine) as session:
        run = session.exec(select(ScannerRun).where(ScannerRun.id == run_id)).one()
        refill = backfill_run_forward_returns(session, run, cfg)
    assert refill["rows_inserted"] == len(deleted_horizons), (
        f"expected exactly the {len(deleted_horizons)} deleted (symbol, horizon) keys to be re-inserted; "
        f"got {refill['rows_inserted']}"
    )
    with Session(engine) as session:
        restored = session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run_id)).all()
    assert {fr.horizon for fr in restored} == set(HORIZONS)
    assert len(restored) == len(HORIZONS)
    assert {fr.symbol for fr in restored} == {"AAA"}

    # 4. A subsequent call is now a pure zero-write warm read (nothing missing -> inserted == 0).
    with Session(engine) as session:
        run = session.exec(select(ScannerRun).where(ScannerRun.id == run_id)).one()
        warm = backfill_run_forward_returns(session, run, cfg)
    assert warm["rows_inserted"] == 0


# ======================================================================================================
# iter-19 (attempt 3) — the PROVEN TC-6 latency fix: un-elapsed horizons are short-circuited GLOBALLY
# before the per-symbol loop, so a run within max(horizons) trading days of the data end (the default
# `/backtest` latest run) pays ZERO per-symbol close_on/bars_after fetches for horizons that cannot yet
# produce a row. These tests prove the short-circuit is byte-identical to the old unfiltered path while
# eliminating the wasted fetches (the ~1090 queries that were 82% of each request under 6x concurrency).
# ======================================================================================================
def _seed_run_with_post_window(engine, asof: date, symbol: str, n_post_bars: int) -> int:
    """Seed ONE run at `asof` with a single scored `symbol` carrying an entry bar ON asof (close 100.0)
    plus `n_post_bars` consecutive post-asof daily bars (close = 100 + i). These are the ONLY post-asof
    price rows in the DB, so the module's observable trading-day count for this run == min(n_post_bars,
    max_h). Benchmark ETFs are unseeded (an honest NA gap), mirroring the partial-backfill fixture."""
    with Session(engine) as session:
        run = _add_run(session, asof)
        rid = run.id
        _add_result(session, rid, symbol)
        session.add(DailyPrice(
            symbol=symbol, date=asof, open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
        ))
        for i in range(1, n_post_bars + 1):
            close = 100.0 + i
            session.add(DailyPrice(
                symbol=symbol, date=asof + timedelta(days=i), open=close, high=close + 1.0,
                low=close - 1.0, close=close, volume=1.0,
            ))
        session.commit()
    return rid


def _fr_rows_sorted(session, run_id: int) -> list:
    """A deterministic projection of EVERY stored ForwardReturn column for a run, sorted — the full
    served-value surface, for a byte-identity assertion between the filtered and unfiltered paths."""
    rows = session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run_id)).all()
    return sorted(
        (r.symbol, r.horizon, r.realized_return, r.entry_close, r.measured_date.isoformat(),
         r.mae, r.mfe, r.max_drawdown, r.underwater_days, r.time_to_recover_days)
        for r in rows
    )


def test_iter19_latest_run_unelapsed_horizons_short_circuit_no_price_fetches(tmp_path, monkeypatch):
    """iter-19 TC-6 mechanism (the k==0 case the reviewer named): for the LATEST run (asof == the data
    end, 0 observable post-D trading days) EVERY configured horizon is un-elapsed, so
    `backfill_run_forward_returns` must short-circuit the per-symbol loop with ZERO `close_on`/`bars_after`
    fetches and insert nothing — yet stay byte-identical to the OLD unfiltered path (which also inserted
    nothing here, only after paying the wasted per-symbol fetches)."""
    import app.engine.forward_testing as ft

    cfg = load_config()
    asof = date(2025, 1, 10)
    engine = make_engine(f"sqlite:///{tmp_path / 'iter19_latest.db'}")
    create_db_and_tables(engine)
    rid = _seed_run_with_post_window(engine, asof, "AAA", n_post_bars=0)  # 0 post-D bars -> k == 0

    counters = {"close_on": 0, "bars_after": 0}
    real_close, real_bars = ft.close_on, ft.bars_after

    def _count(name, fn):
        def wrapper(*a, **kw):
            counters[name] += 1
            return fn(*a, **kw)
        return wrapper

    monkeypatch.setattr(ft, "close_on", _count("close_on", real_close))
    monkeypatch.setattr(ft, "bars_after", _count("bars_after", real_bars))

    with Session(engine) as session:
        run = session.exec(select(ScannerRun).where(ScannerRun.id == rid)).one()
        result = ft.backfill_run_forward_returns(session, run, cfg)
    n_close, n_bars = counters["close_on"], counters["bars_after"]

    assert result["rows_inserted"] == 0
    assert n_close == 0, f"latest-run backfill must issue zero per-symbol close_on fetches, got {n_close}"
    assert n_bars == 0, f"latest-run backfill must issue zero per-symbol bars_after fetches, got {n_bars}"
    with Session(engine) as session:
        assert _fr_rows_sorted(session, rid) == []  # nothing stored

    # Byte-identity: the OLD unfiltered path (full horizons) on an identical fixture also inserts nothing
    # (it just pays the wasted close_on/bars_after fetches first) -> identical (empty) stored state.
    engine2 = make_engine(f"sqlite:///{tmp_path / 'iter19_latest_unfiltered.db'}")
    create_db_and_tables(engine2)
    rid2 = _seed_run_with_post_window(engine2, asof, "AAA", n_post_bars=0)
    with Session(engine2) as session:
        run2 = session.exec(select(ScannerRun).where(ScannerRun.id == rid2)).one()
        symbols = ft.forward_symbols_for_run(session, run2, cfg)
        unfiltered = ft._insert_run_forward_returns(session, run2, symbols, HORIZONS, max(HORIZONS), set())
        session.commit()
        assert unfiltered == 0
        assert _fr_rows_sorted(session, rid2) == []


def test_iter19_partially_elapsed_run_processes_only_elapsed_horizons_byte_identical(tmp_path, monkeypatch):
    """iter-19: a PARTIALLY-elapsed run (K observable post-D trading days, K == the second-largest
    horizon so the largest horizon is un-elapsed) inserts rows for ONLY the elapsed horizons (h <= K),
    byte-identical to the OLD unfiltered path; and a warm re-call issues ZERO `bars_after` fetches — the
    un-elapsed horizon no longer re-triggers a per-symbol price fetch on every request."""
    sorted_h = sorted(HORIZONS)
    if len(sorted_h) < 2 or sorted_h[-1] == sorted_h[-2]:
        pytest.skip("needs a strict largest horizon to leave >= 1 un-elapsed horizon")
    K = sorted_h[-2]  # observable window: elapsed = every horizon except the (strictly larger) max
    elapsed = [h for h in sorted_h if h <= K]
    unelapsed = [h for h in sorted_h if h > K]
    assert elapsed and unelapsed  # fixture sanity: both partitions non-empty

    cfg = load_config()
    asof = date(2025, 1, 10)
    engine = make_engine(f"sqlite:///{tmp_path / 'iter19_partial_elapsed.db'}")
    create_db_and_tables(engine)
    rid = _seed_run_with_post_window(engine, asof, "AAA", n_post_bars=K)  # exactly K post-D bars -> k == K

    with Session(engine) as session:
        run = session.exec(select(ScannerRun).where(ScannerRun.id == rid)).one()
        result = backfill_run_forward_returns(session, run, cfg)
    assert result["rows_inserted"] == len(elapsed), (
        f"only the {len(elapsed)} elapsed horizons {elapsed} should insert; the un-elapsed {unelapsed} "
        f"cannot produce a row with only K={K} post-D bars"
    )
    with Session(engine) as session:
        stored = session.exec(select(ForwardReturn).where(ForwardReturn.run_id == rid)).all()
    assert {r.horizon for r in stored} == set(elapsed)
    assert {r.symbol for r in stored} == {"AAA"}
    ret_by_h = {r.horizon: r.realized_return for r in stored}
    for h in elapsed:  # deterministic realized return: (100 + h)/100 - 1 == h/100
        assert ret_by_h[h] == pytest.approx(h / 100.0)

    # Byte-identity vs the OLD unfiltered path on an identical fixture (full horizons; the un-elapsed
    # horizon is dropped there by forward_return's per-symbol NA gate) -> identical stored rows.
    engine2 = make_engine(f"sqlite:///{tmp_path / 'iter19_partial_elapsed_unfiltered.db'}")
    create_db_and_tables(engine2)
    rid2 = _seed_run_with_post_window(engine2, asof, "AAA", n_post_bars=K)
    with Session(engine2) as session:
        run2 = session.exec(select(ScannerRun).where(ScannerRun.id == rid2)).one()
        import app.engine.forward_testing as ft
        symbols = ft.forward_symbols_for_run(session, run2, cfg)
        unfiltered = ft._insert_run_forward_returns(session, run2, symbols, HORIZONS, max(HORIZONS), set())
        session.commit()
        assert unfiltered == len(elapsed)
    with Session(engine) as s1, Session(engine2) as s2:
        assert _fr_rows_sorted(s1, rid) == _fr_rows_sorted(s2, rid2)

    # Warm re-call: the elapsed horizons are all stored and the un-elapsed horizon is filtered out, so the
    # scored symbol needs nothing -> ZERO bars_after fetches (WITHOUT the fix, needed == the un-elapsed
    # horizon for that symbol, forcing a per-symbol close_on+bars_after fetch every request).
    import app.engine.forward_testing as ft
    bars_after_calls = {"n": 0}
    real_bars = ft.bars_after

    def _count_bars(*a, **kw):
        bars_after_calls["n"] += 1
        return real_bars(*a, **kw)

    monkeypatch.setattr(ft, "bars_after", _count_bars)
    with Session(engine) as session:
        run = session.exec(select(ScannerRun).where(ScannerRun.id == rid)).one()
        warm = ft.backfill_run_forward_returns(session, run, cfg)
    assert warm["rows_inserted"] == 0
    assert bars_after_calls["n"] == 0, (
        f"warm re-call must not re-fetch for the un-elapsed horizon(s) {unelapsed}; "
        f"got {bars_after_calls['n']} bars_after calls"
    )


def test_iter19_fully_elapsed_run_processes_all_horizons_unaffected(tmp_path):
    """iter-19: an OLD, fully-elapsed run (>= max(horizons) observable post-D trading days) keeps
    processing EVERY configured horizon — the observable-horizon filter is a no-op (k >= max_h), so the
    genuinely-missing rows are all inserted exactly as before this iteration (no regression)."""
    cfg = load_config()
    asof = date(2025, 1, 10)
    engine = make_engine(f"sqlite:///{tmp_path / 'iter19_full_elapsed.db'}")
    create_db_and_tables(engine)
    rid = _seed_run_with_post_window(engine, asof, "AAA", n_post_bars=max(HORIZONS))  # k == max_h

    with Session(engine) as session:
        run = session.exec(select(ScannerRun).where(ScannerRun.id == rid)).one()
        result = backfill_run_forward_returns(session, run, cfg)
    assert result["rows_inserted"] == len(HORIZONS), "every configured horizon must still insert one row"
    with Session(engine) as session:
        stored = session.exec(select(ForwardReturn).where(ForwardReturn.run_id == rid)).all()
    assert {r.horizon for r in stored} == set(HORIZONS)
    assert {r.symbol for r in stored} == {"AAA"}
    ret_by_h = {r.horizon: r.realized_return for r in stored}
    for h in HORIZONS:  # deterministic realized return: (100 + h)/100 - 1 == h/100
        assert ret_by_h[h] == pytest.approx(h / 100.0)
