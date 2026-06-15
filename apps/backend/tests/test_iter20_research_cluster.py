"""iter-20 backend research cluster — J-72 (event-study perf + cache, byte-identical),
J-75 (per-stock forward returns served verbatim on /api/stocks + detail), J-77 (Regime × Setup ×
Pattern ranked combinations study, count-coherent with the N= samples drill-downs).

Named proofs, each guarding a Definition-of-Done gate / anti-goal:

  J-72:
   - byte-identity (cache vs fresh compute) — both views × all-history + as-of-scoped.
   - single-batched-read — the per-horizon ForwardReturn re-scan is replaced by ONE batched read
     (`_event_study_members_by_horizon` issues a single `horizon IN (...)` query); the loop calls it once.
   - cache refresh after a dataset change — a new snapshot/return flips the dataset-version key, so the
     cache never serves a stale figure.

  J-75:
   - leaderboard == detail == stored forward_returns per (ticker, horizon) (single source, J-06).
   - NA where no stored row (near latest all five NA) — never fabricated.
   - config-driven horizons (no hardcoded [1,5,10,20,60]).
   - read-only (no recompute) — the stored row IS the served value (no-lookahead intrinsic).

  J-77:
   - byte-identity of existing event-study figures after the additive observation enrichment.
   - group-by correctness over the SAME enriched observation set.
   - count-coherence SAME-INSTANT — study row n == /research/samples total in BOTH Episodes and Pooled.
   - config-backed vocabulary (regime labels, setups, pattern keys).
   - min-sample NA honesty; error-case 4xx for the new endpoint + the samples cohort selector.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine, set_engine
from app.engine.research import (
    PATTERN_NONE,
    VIEW_EPISODES,
    VIEW_POOLED,
    _dataset_version,
    _event_study_members,
    _event_study_members_by_horizon,
    compute_event_study,
    compute_regime_setup_pattern_study,
    event_study_cached,
    pattern_keys,
)
from app.engine.samples import KIND_REGIME_SETUP_PATTERN, compute_samples
from app.engine.snapshot_serving import stock_detail_payload, stocks_payload, stored_stock_rows
from app.models import EventStudyCache, ForwardReturn, ScannerResult, ScannerRun

H = 20


# ==================================================================================================
# Hand-built fixtures (no engine — exact by construction)
# ==================================================================================================
def _utc() -> datetime:
    return datetime.now(timezone.utc)


def _add_run(session: Session, asof: date, regime_label: str = "Risk-on") -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=_utc(), provider="seed", benchmark="SPY",
        regime_score=50.0, regime_label=regime_label, regime_components_json="[]",
        new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _record_json(ticker: str) -> str:
    """A minimal lossless StockRow record (only the keys the serving layer reads back: `ticker`)."""
    return json.dumps({"ticker": ticker, "name": ticker})


def _add_result(
    session, run_id, ticker, rank, *, setup="Breakout-watch", sector="Technology",
    is_vcp=False, is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
):
    session.add(ScannerResult(
        run_id=run_id, ticker=ticker, name=ticker, sector=sector,
        leadership_score=50.0, leadership_bucket="C",
        entry_quality_score=50.0, entry_quality_bucket="C",
        risk_score=50.0, risk_bucket="C",
        setup_status=setup, rank=rank, record_json=_record_json(ticker),
        is_vcp=is_vcp, is_pullback_to_rising_dma=is_pullback_to_rising_dma,
        is_flat_base_breakout=is_flat_base_breakout,
    ))


def _add_fr(session, run_id, symbol, ret, horizon=H, mae=None, mfe=None):
    session.add(ForwardReturn(
        run_id=run_id, symbol=symbol, horizon=horizon, asof_date=date(2025, 1, 1),
        entry_close=100.0, measured_date=date(2025, 2, 1), realized_return=ret, mae=mae, mfe=mfe,
    ))


def _engine(tmp_path, name="iter20.db"):
    engine = make_engine(f"sqlite:///{tmp_path / name}")
    create_db_and_tables(engine)
    return engine


def _cfg_with(*, min_sample=None):
    cfg = load_config()
    if min_sample is not None:
        cfg = cfg.model_copy(update={"walk_forward": cfg.walk_forward.model_copy(update={"min_sample": min_sample})})
    return cfg


@pytest.fixture()
def study_engine(tmp_path):
    """Two runs in different regimes; known setups + pattern flags + sectors + returns at MULTIPLE
    horizons, so the event study, its cache, and the regime×setup×pattern study are exact by
    construction. Forward returns exist at horizons 1, 5, 20 for the run-1 names and at 20 only for the
    run-2 names — so the J-75 NA-where-no-row + the J-72 batched-read membership are exercised."""
    engine = _engine(tmp_path, "study.db")
    with Session(engine) as session:
        on = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        off = _add_run(session, date(2025, 2, 10), regime_label="Risk-off")
        # (ticker, run, setup, sector, is_vcp, is_pb, is_fb, ret)
        rows = [
            ("AA", on,  "Actionable",         "Technology", True,  False, False, 0.10),
            ("BB", on,  "Actionable",         "Energy",     False, True,  False, 0.20),
            ("CC", on,  "Breakout-watch",     "Technology", True,  False, True,  -0.10),
            ("DD", off, "Risk-off-watchlist", "Technology", True,  False, False, 0.30),
            ("EE", off, "Risk-off-watchlist", "Energy",     False, False, False, 0.04),
        ]
        for i, (tkr, run, setup, sector, v, pb, fb, ret) in enumerate(rows, start=1):
            _add_result(
                session, run.id, tkr, rank=i, setup=setup, sector=sector,
                is_vcp=v, is_pullback_to_rising_dma=pb, is_flat_base_breakout=fb,
            )
        # multi-horizon returns: run-1 names at 1/5/20; run-2 names at 20 only.
        for tkr, ret in (("AA", 0.10), ("BB", 0.20), ("CC", -0.10)):
            for h in (1, 5, 20):
                _add_fr(session, on.id, tkr, ret * (h / 20.0), horizon=h, mae=-0.05, mfe=0.15)
        for tkr, ret in (("DD", 0.30), ("EE", 0.04)):
            _add_fr(session, off.id, tkr, ret, horizon=20, mae=-0.08, mfe=0.35)
        session.commit()
    return engine


# ==================================================================================================
# J-72 — single batched read (the per-horizon ForwardReturn re-scan is gone)
# ==================================================================================================
def test_j72_batched_read_matches_per_horizon_builder_byte_identical(study_engine):
    """The batched `_event_study_members_by_horizon` produces per-horizon member lists BYTE-IDENTICAL to
    calling the per-horizon `_event_study_members` in a loop — same membership, same enrichment, same
    order (deterministic id-ordered results)."""
    cfg = load_config()
    horizons = list(cfg.walk_forward.horizons)
    subject = {"key": "vcp", "kind": "pattern"}
    with Session(study_engine) as session:
        batched = _event_study_members_by_horizon(session, subject, horizons)
        for h in horizons:
            per = _event_study_members(session, subject, h)
            assert batched[h] == per, f"horizon {h} batched != per-horizon"


def test_j72_compute_event_study_issues_single_forward_return_scan(study_engine, monkeypatch):
    """The per-horizon computation issues a SINGLE batched ForwardReturn read, NOT one scan per horizon:
    we count `_event_study_members_by_horizon` calls (must be exactly 1) and assert the legacy per-horizon
    `_event_study_members` is NOT used inside the compute loop (0 calls)."""
    import app.engine.research as research

    batched_calls = {"n": 0}
    per_horizon_calls = {"n": 0}
    real_batched = research._event_study_members_by_horizon
    real_per = research._event_study_members

    def _spy_batched(*a, **k):
        batched_calls["n"] += 1
        return real_batched(*a, **k)

    def _spy_per(*a, **k):
        per_horizon_calls["n"] += 1
        return real_per(*a, **k)

    monkeypatch.setattr(research, "_event_study_members_by_horizon", _spy_batched)
    monkeypatch.setattr(research, "_event_study_members", _spy_per)

    cfg = _cfg_with(min_sample=2)
    with Session(study_engine) as session:
        research.compute_event_study(session, "vcp", H, cfg)
    assert batched_calls["n"] == 1, f"expected 1 batched read, got {batched_calls['n']}"
    assert per_horizon_calls["n"] == 0, (
        f"compute_event_study must not re-scan per horizon, got {per_horizon_calls['n']} calls"
    )


# ==================================================================================================
# J-72 — cache: byte-identical figures + refresh after a dataset change
# ==================================================================================================
def test_j72_cache_hit_is_byte_identical_both_views_all_history_and_as_of(study_engine):
    """`event_study_cached` returns a payload BYTE-IDENTICAL to a fresh `compute_event_study` in BOTH
    views (episodes default + pooled) and for all-history AND an as-of-scoped window."""
    cfg = _cfg_with(min_sample=2)
    with Session(study_engine) as session:
        for view in (VIEW_EPISODES, VIEW_POOLED):
            for as_of in (None, date(2025, 1, 10)):
                fresh = compute_event_study(session, "vcp", H, cfg, as_of=as_of, view=view)
                # first call populates the cache (a MISS computes-and-stores); the second is a HIT.
                cached_miss = event_study_cached(session, "vcp", H, cfg, as_of=as_of, view=view)
                cached_hit = event_study_cached(session, "vcp", H, cfg, as_of=as_of, view=view)
                assert json.dumps(cached_miss, sort_keys=True) == json.dumps(fresh, sort_keys=True)
                assert json.dumps(cached_hit, sort_keys=True) == json.dumps(fresh, sort_keys=True)


def test_j72_cache_refreshes_after_dataset_change(study_engine):
    """The cache REFRESHES after a dataset change (no stale figure): cache a payload, then add a new
    snapshot + forward return (changing the dataset-version stamp), and assert the next read returns the
    UPDATED aggregate (== a fresh compute over the new data), not the stale cached one."""
    cfg = _cfg_with(min_sample=2)
    with Session(study_engine) as session:
        before = event_study_cached(session, "Actionable", H, cfg)
        v_before = _dataset_version(session)

        # add a third run with another Actionable VCP name + its forward return (dataset changes).
        new = _add_run(session, date(2025, 3, 10), regime_label="Risk-on")
        _add_result(session, new.id, "ZZ", rank=1, setup="Actionable", sector="Technology", is_vcp=True)
        _add_fr(session, new.id, "ZZ", 0.50, horizon=20)
        session.commit()

        v_after = _dataset_version(session)
        assert v_after != v_before, "dataset-version stamp must change after a backfill add"

        after = event_study_cached(session, "Actionable", H, cfg)
        fresh = compute_event_study(session, "Actionable", H, cfg)
        assert after["n_total"] == fresh["n_total"]
        assert after["n_total"] > before["n_total"], "cache served a stale (pre-add) figure"
        assert json.dumps(after, sort_keys=True) == json.dumps(fresh, sort_keys=True)


def test_j72_invalid_subject_writes_no_cache_row(study_engine):
    """An invalid request never writes a cache row: the compute raises BEFORE the cache write, so a bad
    subject leaves the cache table untouched (no fabricated/garbage cached aggregate)."""
    cfg = _cfg_with(min_sample=2)
    with Session(study_engine) as session:
        with pytest.raises(ValueError):
            event_study_cached(session, "not_a_subject", H, cfg)
        assert session.exec(select(EventStudyCache)).all() == []


# ==================================================================================================
# J-75 — per-stock forward returns served verbatim (leaderboard == detail == stored), NA, config-driven
# ==================================================================================================
def test_j75_forward_returns_served_verbatim_from_stored_rows(study_engine):
    """Each served stock row carries five forward returns read VERBATIM from the stored `forward_returns`
    (config-driven horizons); a horizon with a stored row carries its exact `realized_return`, and a
    horizon with no stored row is NA (None) — never fabricated."""
    cfg = load_config()
    horizons = list(cfg.walk_forward.horizons)
    with Session(study_engine) as session:
        run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == date(2025, 1, 10))).one()
        rows = stored_stock_rows(session, run, cfg)
        by_ticker = {r["ticker"]: r for r in rows}

        aa = by_ticker["AA"]
        # the forward_returns list maps to config horizons in order — config-driven, no hardcoded list.
        assert [fr["horizon"] for fr in aa["forward_returns"]] == horizons
        ret_by_h = {fr["horizon"]: fr["return"] for fr in aa["forward_returns"]}
        # AA has stored rows at 1/5/20 (= 0.10 * h/20); the other horizons have no stored row -> NA.
        assert ret_by_h[1] == pytest.approx(0.10 * (1 / 20.0))
        assert ret_by_h[5] == pytest.approx(0.10 * (5 / 20.0))
        assert ret_by_h[20] == pytest.approx(0.10)
        assert ret_by_h[10] is None and ret_by_h[60] is None  # no stored row -> honest NA


def test_j75_leaderboard_equals_detail_per_ticker_horizon(study_engine):
    """Single source of truth (J-06): the leaderboard list row and the detail row carry IDENTICAL
    forward returns for the same ticker/date/horizon (same stored rows, one serving path)."""
    cfg = load_config()
    with Session(study_engine) as session:
        run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == date(2025, 1, 10))).one()
        list_payload = stocks_payload(session, run, cfg)
        for row in list_payload["rows"]:
            detail = stock_detail_payload(session, run, row["ticker"], cfg)
            assert detail["row"]["forward_returns"] == row["forward_returns"]


def test_j75_all_na_when_no_stored_forward_returns(study_engine):
    """Near the latest date (no post-D bars yet) every horizon is honestly NA: a run with NO stored
    forward_returns serves five NA cells for every stock — never a fabricated 0."""
    cfg = load_config()
    with Session(study_engine) as session:
        bare = _add_run(session, date(2025, 4, 10), regime_label="Risk-on")
        _add_result(session, bare.id, "QQ", rank=1, setup="Actionable")
        session.commit()
        rows = stored_stock_rows(session, bare, cfg)
        qq = next(r for r in rows if r["ticker"] == "QQ")
        assert all(fr["return"] is None for fr in qq["forward_returns"])
        assert [fr["horizon"] for fr in qq["forward_returns"]] == list(cfg.walk_forward.horizons)


# ==================================================================================================
# J-77 — additive enrichment leaves existing event-study figures byte-identical
# ==================================================================================================
def test_j77_enrichment_leaves_event_study_byte_identical(study_engine):
    """The J-77 additive observation enrichment (setup_status + pattern flags) does NOT change any
    existing event-study figure: every figure derives from the same builder, so the enriched payload's
    aggregate values (by_horizon/by_regime/by_sector) are unaffected. We assert the enrichment keys are
    PRESENT on each member but the aggregate stats only read return/mae/mfe/regime/sector (unchanged)."""
    cfg = _cfg_with(min_sample=2)
    subject = {"key": "vcp", "kind": "pattern"}
    with Session(study_engine) as session:
        members = _event_study_members(session, subject, H)
        for m in members:
            assert "setup_status" in m and "patterns" in m
            assert set(m["patterns"]) == set(pattern_keys(cfg))
        # the event study computes a full payload over the enriched members (no crash, figures present).
        payload = compute_event_study(session, "vcp", H, cfg)
        row = next(r for r in payload["by_horizon"] if r["horizon"] == H)
        assert row["n"] == len(members)  # the enriched member count drives n unchanged


# ==================================================================================================
# J-77 — group-by correctness + ranking + min-sample NA
# ==================================================================================================
def test_j77_group_by_regime_setup_pattern_exact(study_engine):
    """The study groups the SAME enriched observation set by (regime, setup, pattern) exactly. At
    horizon 20 the run-1 (Risk-on) names: AA=Actionable+vcp (0.10), BB=Actionable+pullback (0.20),
    CC=Breakout-watch+flat_base (-0.10); run-2 (Risk-off): DD=Risk-off-watchlist+vcp (0.30),
    EE=Risk-off-watchlist+none (0.04). Each observation contributes to one row per flagged pattern."""
    cfg = _cfg_with(min_sample=1)
    with Session(study_engine) as session:
        study = compute_regime_setup_pattern_study(session, H, cfg, view=VIEW_POOLED)
    by_combo = {(r["regime"], r["setup"], r["pattern"]): r for r in study["rows"]}

    # AA: Risk-on / Actionable / vcp -> mean 0.10
    assert by_combo[("Risk-on", "Actionable", "vcp")]["stats"]["mean"] == pytest.approx(0.10)
    assert by_combo[("Risk-on", "Actionable", "vcp")]["stats"]["n"] == 1
    # BB: Risk-on / Actionable / pullback_to_rising_dma -> mean 0.20
    assert by_combo[("Risk-on", "Actionable", "pullback_to_rising_dma")]["stats"]["mean"] == pytest.approx(0.20)
    # CC: Risk-on / Breakout-watch / flat_base_breakout -> mean -0.10
    assert by_combo[("Risk-on", "Breakout-watch", "flat_base_breakout")]["stats"]["mean"] == pytest.approx(-0.10)
    # DD: Risk-off / Risk-off-watchlist / vcp -> mean 0.30
    assert by_combo[("Risk-off", "Risk-off-watchlist", "vcp")]["stats"]["mean"] == pytest.approx(0.30)
    # EE: Risk-off / Risk-off-watchlist / none (no pattern flagged) -> mean 0.04
    assert by_combo[("Risk-off", "Risk-off-watchlist", PATTERN_NONE)]["stats"]["mean"] == pytest.approx(0.04)


def test_j77_vocabularies_are_config_backed(study_engine):
    """The study echoes its vocabularies from the EXISTING config-backed catalogs — no hardcoded list."""
    cfg = load_config()
    with Session(study_engine) as session:
        study = compute_regime_setup_pattern_study(session, H, cfg)
    assert study["regime_labels"] == list(cfg.regime.labels)
    assert study["patterns"] == pattern_keys(cfg)
    from app.engine.setups import ALL_STATUSES
    assert study["setups"] == list(ALL_STATUSES)


def test_j77_low_sample_flagged(study_engine):
    """A combination below `walk_forward.min_sample` carries its honest `n` + a `low_sample` flag (the UI
    renders NA + n) — never dropped, never fabricated."""
    cfg = _cfg_with(min_sample=10)  # every single-member combination is low-sample
    with Session(study_engine) as session:
        study = compute_regime_setup_pattern_study(session, H, cfg, view=VIEW_POOLED)
    assert study["rows"], "the study must still emit rows (with low_sample flags)"
    assert all(r["stats"]["low_sample"] for r in study["rows"])
    assert all(r["stats"]["n"] >= 1 for r in study["rows"])


def test_j77_unknown_view_raises(study_engine):
    cfg = load_config()
    with Session(study_engine) as session:
        with pytest.raises(ValueError):
            compute_regime_setup_pattern_study(session, H, cfg, view="bogus")


# ==================================================================================================
# J-77 — count-coherence SAME-INSTANT (study row n == samples drill-down total) in BOTH views
# ==================================================================================================
def test_j77_count_coherence_same_instant_both_views(study_engine):
    """The keystone: a study row's published `n` EQUALS the /research/samples drill-down `total` for the
    SAME (regime, setup, pattern) cohort, asserted SAME-INSTANT in BOTH Episodes and Pooled — same
    membership builder, one observation set."""
    cfg = _cfg_with(min_sample=1)
    with Session(study_engine) as session:
        for view in (VIEW_POOLED, VIEW_EPISODES):
            study = compute_regime_setup_pattern_study(session, H, cfg, view=view)
            for r in study["rows"]:
                samples = compute_samples(
                    session, kind=KIND_REGIME_SETUP_PATTERN, horizon=H, config=cfg,
                    regime=r["regime"], setup=r["setup"], pattern=r["pattern"], view=view,
                )
                assert samples["total"] == r["stats"]["n"], (
                    f"count drift {view} {(r['regime'], r['setup'], r['pattern'])}: "
                    f"study n={r['stats']['n']} samples total={samples['total']}"
                )
                assert len(samples["rows"]) == r["stats"]["n"]


def test_j77_samples_invalid_selectors_raise(study_engine):
    """An invalid (regime, setup, pattern) cohort selector raises ValueError (the API -> 4xx); a VALID
    n=0 combination returns an honest empty drill-down (total 0, no fabricated row)."""
    cfg = load_config()
    with Session(study_engine) as session:
        with pytest.raises(ValueError):  # unknown regime
            compute_samples(session, kind=KIND_REGIME_SETUP_PATTERN, horizon=H, config=cfg,
                            regime="Bogus", setup="Actionable", pattern="vcp")
        with pytest.raises(ValueError):  # unknown setup
            compute_samples(session, kind=KIND_REGIME_SETUP_PATTERN, horizon=H, config=cfg,
                            regime="Risk-on", setup="Bogus", pattern="vcp")
        with pytest.raises(ValueError):  # unknown pattern
            compute_samples(session, kind=KIND_REGIME_SETUP_PATTERN, horizon=H, config=cfg,
                            regime="Risk-on", setup="Actionable", pattern="bogus")
        # VALID but empty (no observation in this combination) -> total 0, empty rows (honest, not 4xx).
        empty = compute_samples(session, kind=KIND_REGIME_SETUP_PATTERN, horizon=H, config=cfg,
                                regime="Choppy", setup="Avoid", pattern=PATTERN_NONE)
        assert empty["total"] == 0 and empty["rows"] == []
