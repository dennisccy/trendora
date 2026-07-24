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
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import event
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.forward_testing import (
    compute_forward_aggregates,
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
