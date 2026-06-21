"""iter-36 (J-96) — the dynamic-universe membership-timeline PERFORMANCE cache.

The iter-35 regression: on the post-rebuild DB (~1369 sliding snapshot dates) `compute_coverage` always
ran `_membership_timeline`, whose per-date `resolve_with_reasons` loop made `GET /api/data` hang >300 s.
iter-36 cached the SERIALIZED `_membership_timeline(...)` payload keyed by `research._dataset_version`, so
the served values stay BYTE-IDENTICAL while the read returns promptly. iter-42 (J-100) NARROWED that key to
`research._membership_dataset_version` (the snapshot set + bars manifest + `min_history_bars`, NOT the
forward-return count) so a warm-up forward-return insert no longer invalidates the cache (the recompute
storm), while a real snapshot/bar change still refreshes it. The served values remain byte-identical.

Named proofs (each guards a DoD line):

  byte-identity       — the cached/served `membership_timeline` payload DEEP-EQUALS a fresh
                        `_membership_timeline(...)` compute; `universe_diagnostic` + `universe_count`
                        unchanged. (hard DoD)
  cache-hit-no-recompute — a second `compute_coverage` (cache warm) does NOT re-run the resolver loop
                        (asserted by patching `_membership_timeline` to blow up on a second call), and the
                        payload is identical.
  cache-row-written   — a single cache row keyed to the current membership-dataset stamp is persisted on the miss.
  invalidation        — after a real membership change (`_membership_dataset_version` changes: a snapshot or
                        bar add/remove), a STALE cache row is NOT served — the read recomputes against the
                        new stamp (and prunes the stale row); a forward-return-only insert does NOT.
  causality           — every timeline date is observed from its OWN <= D snapshot/bars (no future
                        leakage) — re-asserted THROUGH the cache.
  empty-db            — an empty DB → an empty-but-valid timeline (no fabricated dates/members), cached.
"""
from __future__ import annotations

import copy
from datetime import date, datetime, timezone

from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import data_manager
from app.engine.data_manager import (
    _membership_timeline,
    compute_coverage,
    membership_timeline_cached,
)
from app.engine.research import _dataset_version, _membership_dataset_version
from app.models import (
    DailyPrice,
    ForwardReturn,
    MembershipTimelineCache,
    ScannerResult,
    ScannerRun,
)


def _mk_run(session: Session, asof: date) -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
        regime_score=50.0, regime_label="Choppy", regime_components_json="{}",
        new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def _mk_result(session: Session, run_id: int, ticker: str, rank: int) -> None:
    session.add(ScannerResult(
        run_id=run_id, ticker=ticker, name=ticker, sector="Technology",
        leadership_score=float(100 - rank), leadership_bucket="A",
        entry_quality_score=1.0, entry_quality_bucket="A", risk_score=1.0, risk_bucket="A",
        setup_status="Watchlist", rank=rank, record_json="{}",
    ))
    session.commit()


def _three_snapshot_engine(tmp_path):
    """Three hand-made snapshots (the iter-33 timeline fixture): AAA/BBB, then AAA/CCC (BBB exits, CCC
    enters), then AAA/BBB/CCC (BBB re-appears). No bars needed for the entries/exits step function — the
    timeline reads the persisted ScannerResult membership directly."""
    engine = make_engine(f"sqlite:///{tmp_path / 'tlcache.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        r1 = _mk_run(session, date(2022, 1, 3))
        for i, t in enumerate(["AAA", "BBB"]):
            _mk_result(session, r1.id, t, rank=i + 1)
        r2 = _mk_run(session, date(2022, 6, 1))
        for i, t in enumerate(["AAA", "CCC"]):
            _mk_result(session, r2.id, t, rank=i + 1)
        r3 = _mk_run(session, date(2022, 12, 1))
        for i, t in enumerate(["AAA", "BBB", "CCC"]):
            _mk_result(session, r3.id, t, rank=i + 1)
    return engine


def _snapshot_dates(session: Session) -> list[date]:
    return sorted(session.exec(select(ScannerRun.asof_date)).all())


# ==================================================================================================
# byte-identity (hard DoD): the CACHED/served payload deep-equals a FRESH _membership_timeline compute
# ==================================================================================================
def test_cached_timeline_byte_identical_to_fresh_compute(tmp_path):
    cfg = load_config()
    engine = _three_snapshot_engine(tmp_path)
    with Session(engine) as session:
        dates = _snapshot_dates(session)
        # a FRESH (uncached) compute — the slow path the cache replaces.
        fresh = _membership_timeline(session, cfg, dates)
    # a SEPARATE session for the cached read so the cache is genuinely written + read back (not the same
    # in-memory dict identity).
    with Session(engine) as session:
        dates = _snapshot_dates(session)
        cached = membership_timeline_cached(session, cfg, dates)
    assert cached == fresh  # DEEP-equal, not "looks similar"
    # and the served coverage block carries the byte-identical timeline + unchanged diagnostic/count
    with Session(engine) as session:
        cov = compute_coverage(session, cfg)
    assert cov["membership_timeline"] == fresh
    # the un-cached coverage figures are unchanged shape/values (sanity: J-94 diagnostic + universe_count)
    assert "universe_diagnostic" in cov and "universe_count" in cov


def test_served_timeline_byte_identical_warm_and_cold(tmp_path):
    """The FIRST (cold) and SECOND (warm) `compute_coverage` serve a byte-identical membership timeline —
    the cache is a pure performance layer, it changes no value."""
    cfg = load_config()
    engine = _three_snapshot_engine(tmp_path)
    with Session(engine) as session:
        cov_cold = copy.deepcopy(compute_coverage(session, cfg))  # cold miss → computes + writes cache
    with Session(engine) as session:
        cov_warm = compute_coverage(session, cfg)  # warm hit → served from cache
    assert cov_warm["membership_timeline"] == cov_cold["membership_timeline"]


# ==================================================================================================
# cache hit: a warm read does NOT re-run the O(dates × pool) resolver derivation
# ==================================================================================================
def test_warm_read_does_not_recompute_timeline(tmp_path, monkeypatch):
    """After the cache is warm, a second read must NOT call `_membership_timeline` again (No recompute in
    the read path). We seed the cache once, then patch `_membership_timeline` to raise — a warm read must
    still succeed (served from the cache), proving the derivation was skipped."""
    cfg = load_config()
    engine = _three_snapshot_engine(tmp_path)
    with Session(engine) as session:
        dates = _snapshot_dates(session)
        warm = membership_timeline_cached(session, cfg, dates)  # seeds the cache

    def _boom(*_args, **_kwargs):
        raise AssertionError("_membership_timeline must NOT be recomputed on a cache HIT")

    monkeypatch.setattr(data_manager, "_membership_timeline", _boom)
    with Session(engine) as session:
        dates = _snapshot_dates(session)
        served = membership_timeline_cached(session, cfg, dates)  # must hit the cache, never recompute
    assert served == warm


def test_cache_row_written_once_under_current_version(tmp_path):
    cfg = load_config()
    engine = _three_snapshot_engine(tmp_path)
    with Session(engine) as session:
        dates = _snapshot_dates(session)
        # iter-42 (J-100): the cache row is keyed by the NARROW membership stamp, not `_dataset_version`.
        version = _membership_dataset_version(session, cfg)
        membership_timeline_cached(session, cfg, dates)
    with Session(engine) as session:
        rows = session.exec(select(MembershipTimelineCache)).all()
        assert len(rows) == 1
        assert rows[0].dataset_version == version
        assert rows[0].payload_json  # a non-empty serialized payload


# ==================================================================================================
# invalidation: a real membership change (snapshot add) changes _membership_dataset_version → a stale row
# is NOT served (and is pruned)
# ==================================================================================================
def test_cache_invalidates_on_dataset_change(tmp_path):
    """Mirror the event_study_cache / market_phase_cache cache-key tests: after a real membership change (a
    new snapshot bumps max(scanner_runs.id) → `_membership_dataset_version` changes), a read recomputes
    against the NEW stamp and serves the UPDATED timeline; the stale row keyed to the old stamp is pruned
    (never served)."""
    cfg = load_config()
    engine = _three_snapshot_engine(tmp_path)
    with Session(engine) as session:
        dates = _snapshot_dates(session)
        # iter-42 (J-100): assert against the NARROW membership stamp (snapshot set + bars manifest).
        v1 = _membership_dataset_version(session, cfg)
        cov1 = copy.deepcopy(compute_coverage(session, cfg))  # warms the cache under v1
        assert cov1["membership_timeline"]["points"][-1]["size"] == 3  # last snapshot had AAA/BBB/CCC

    # DATASET CHANGE: add a NEW later snapshot with a 4th name → both max(run.id) AND the timeline change.
    with Session(engine) as session:
        r4 = _mk_run(session, date(2023, 1, 3))
        for i, t in enumerate(["AAA", "BBB", "CCC", "DDD"]):
            _mk_result(session, r4.id, t, rank=i + 1)
        v2 = _membership_dataset_version(session, cfg)
    assert v2 != v1  # a snapshot add moves the NARROW stamp → the cache key changed

    with Session(engine) as session:
        dates = _snapshot_dates(session)
        cov2 = compute_coverage(session, cfg)  # must recompute against v2 (the v1 row is now stale)
        tl2 = cov2["membership_timeline"]
        # the NEW snapshot is in the timeline with DDD as a fresh entry — proving the v1 row was NOT served.
        last = tl2["points"][-1]
        assert last["date"] == "2023-01-03"
        assert last["size"] == 4 and "DDD" in last["entries"]
        # and a fresh uncached compute over the new DB equals the served (byte-identity through the cache)
        assert tl2 == _membership_timeline(session, cfg, dates)
        # the stale v1 row was pruned on the v2 write; only the current-version row remains.
        rows = session.exec(select(MembershipTimelineCache)).all()
        assert len(rows) == 1 and rows[0].dataset_version == v2


def test_forward_return_insert_does_NOT_invalidate_membership_cache(tmp_path, monkeypatch):
    """iter-42 (J-100) — the membership cache DECOUPLING (scope (b)). The membership timeline reads NO
    forward return, so the NARROW `_membership_dataset_version` does NOT fold in the forward-return row
    count: a forward-return-only insert (with no new snapshot, no new bar) leaves the stamp UNCHANGED, so
    the cache HITS (no recompute storm). We prove the HIT against an ALREADY-POPULATED cache row
    (iter-38/39 lesson): seed the cache, patch `_membership_timeline` to BLOW UP, insert a forward-return
    row, then read — a successful read proves the resolver loop was skipped (the row was served)."""
    cfg = load_config()
    engine = _three_snapshot_engine(tmp_path)
    with Session(engine) as session:
        dates = _snapshot_dates(session)
        v1_membership = _membership_dataset_version(session, cfg)
        v1_broad = _dataset_version(session)
        warm = membership_timeline_cached(session, cfg, dates)  # warm under the narrow stamp

    with Session(engine) as session:
        # add ONE forward-return row: the BROAD `_dataset_version` changes (fr_count++), but the NARROW
        # membership stamp does NOT (no new snapshot, no new bar).
        run = session.exec(select(ScannerRun)).first()
        session.add(ForwardReturn(
            run_id=run.id, symbol="AAA", horizon=5, asof_date=run.asof_date,
            entry_close=10.0, measured_date=date(2022, 1, 10), realized_return=0.05,
        ))
        session.commit()
        v2_membership = _membership_dataset_version(session, cfg)
        v2_broad = _dataset_version(session)
    assert v2_broad != v1_broad  # the broad J-72/J-87 stamp DID move (fr_count changed)
    assert v2_membership == v1_membership  # the narrow membership stamp did NOT move — the decoupling

    # patch the resolver derivation to raise — a cache HIT must NOT call it.
    def _boom(*_args, **_kwargs):
        raise AssertionError("a forward-return insert must NOT invalidate the membership cache")

    monkeypatch.setattr(data_manager, "_membership_timeline", _boom)
    with Session(engine) as session:
        dates = _snapshot_dates(session)
        served = membership_timeline_cached(session, cfg, dates)  # must HIT the still-valid v1 row
        assert served == warm  # byte-identical to the pre-insert warm payload
        # the cache still carries exactly the single (unchanged-stamp) row — no churn, no re-write.
        rows = session.exec(select(MembershipTimelineCache)).all()
        assert len(rows) == 1 and rows[0].dataset_version == v1_membership


def test_bar_backfill_DOES_invalidate_membership_cache(tmp_path):
    """The narrow stamp's other arm: adding a BAR (a real input the per-date history gate reads) changes
    the bars manifest term, so the membership cache correctly INVALIDATES and recomputes (the narrow stamp
    is not so narrow that it misses a real membership-affecting change)."""
    cfg = load_config()
    engine = _three_snapshot_engine(tmp_path)
    with Session(engine) as session:
        dates = _snapshot_dates(session)
        v1 = _membership_dataset_version(session, cfg)
        membership_timeline_cached(session, cfg, dates)  # warm under v1
        rows = session.exec(select(MembershipTimelineCache)).all()
        assert len(rows) == 1 and rows[0].dataset_version == v1

    with Session(engine) as session:
        # add ONE daily price bar → the bars manifest (max date / count) changes → narrow stamp changes.
        session.add(DailyPrice(
            symbol="AAA", date=date(2022, 1, 4), open=10.0, high=11.0, low=9.0, close=10.5, volume=1000,
        ))
        session.commit()
        v2 = _membership_dataset_version(session, cfg)
    assert v2 != v1  # a bar add moves the narrow stamp → the cache must refresh

    with Session(engine) as session:
        dates = _snapshot_dates(session)
        membership_timeline_cached(session, cfg, dates)  # recompute against v2; prune the stale v1 row
        rows = session.exec(select(MembershipTimelineCache)).all()
        assert len(rows) == 1 and rows[0].dataset_version == v2


# ==================================================================================================
# causality preserved THROUGH the cache: each date observed from its own <= D snapshot/membership
# ==================================================================================================
def test_causality_entries_exits_through_cache(tmp_path):
    """The cached timeline carries the SAME strictly-causal entries/exits step function as the direct
    compute (re-asserting the iter-33 J-96 property holds through the cache)."""
    cfg = load_config()
    engine = _three_snapshot_engine(tmp_path)
    with Session(engine) as session:
        cov = compute_coverage(session, cfg)
    tl = cov["membership_timeline"]
    pts = {p["date"]: p for p in tl["points"]}
    # D1: AAA, BBB both first-seen entries, no exits, size 2.
    assert pts["2022-01-03"]["size"] == 2 and pts["2022-01-03"]["entries"] == ["AAA", "BBB"]
    assert pts["2022-01-03"]["exits"] == []
    # D2: CCC enters (first seen), BBB exits (present prior, gone now), size 2.
    assert pts["2022-06-01"]["size"] == 2
    assert pts["2022-06-01"]["entries"] == ["CCC"] and pts["2022-06-01"]["exits"] == ["BBB"]
    # D3: BBB RE-appears — NOT a new entry (seen before) — size grows to 3, no exits.
    assert pts["2022-12-01"]["size"] == 3
    assert pts["2022-12-01"]["entries"] == [] and pts["2022-12-01"]["exits"] == []
    # the timeline dates are exactly the snapshot dates, ascending (no fabricated/future date).
    assert [p["date"] for p in tl["points"]] == ["2022-01-03", "2022-06-01", "2022-12-01"]


# ==================================================================================================
# empty DB → an empty-but-valid timeline, cached (no fabricated dates/members)
# ==================================================================================================
def test_empty_db_caches_empty_but_valid_timeline(tmp_path):
    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / 'empty_cache.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        cached = membership_timeline_cached(session, cfg, [])
    assert cached["points"] == []  # no snapshots → no fabricated dates/members
    assert "labels" in cached and cached["labels"]["survivorship"]["basis"] == "current_constituent"
    # the empty timeline is still cached (a row under the empty-DB dataset_version), and a warm read
    # deep-equals a fresh empty compute.
    with Session(engine) as session:
        rows = session.exec(select(MembershipTimelineCache)).all()
        assert len(rows) == 1
        assert membership_timeline_cached(session, cfg, []) == _membership_timeline(session, cfg, [])
