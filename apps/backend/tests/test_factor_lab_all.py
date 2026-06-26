"""Factor Lab all-factors view (iter-50, J-107) — one row per config-catalog factor (family + rank-IC +
downside risk-adjusted + the full decile table), served from a derived-once cached, bounded read path.

NON-NEGOTIABLE contracts proven here:

  - **Byte-identity (load-bearing, Single source of truth).** Every all-factors figure per factor EQUALS
    `compute_factor_lab(session, factor, horizon, as_of=cutoff)` for the same factor — produced by the SAME
    `_deciles` / `_rank_ic` builders over the SAME shared observation pool (one computation path, no second
    rank-IC / decile / risk-adjusted derivation, no new served value). Proven across all-history + as-of +
    zero-N / low-sample cohorts, asserting EXACT dict equality of the deciles + rank-IC.
  - **Cache correctness (J-72 idiom).** HIT == MISS == fresh compute; a stale-`dataset_version` row is a
    MISS and is PRUNED (tested against a real already-populated cache row, not only a fresh compute).
  - **Bounded read (J-105 / iter-48 lesson).** The shared pool is built ONCE (one heavy read for all N
    factors), is `yield_per`-streamed (no unbounded `.all()`), and orders the ScannerResult side by
    `(run_id, id)` (rides `ix_scanner_results_run_id` — no temp-B-tree disk spill). Chunk-independent.
  - **Honest NA.** A zero-N / all-NULL factor renders empty decile rows + NA rank-IC + NA risk-adjusted,
    never a fabricated number.

The math runs on tiny hand-built in-memory data (the lab READS stored rows — no engine run needed). The
fixture deliberately mixes COLUMN factors (leadership/risk/entry-quality scores), a COMPONENT factor read
from `record_json` (rs_spy_3m, atr_pct), and catalog factors with NO stored value (the volatility columns
+ unpopulated components) so the byte-identity proof spans populated, component, and zero-N cohorts.
"""
from __future__ import annotations

import inspect
import json
from datetime import date, datetime, timezone

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.research import (
    _ALL_FACTORS_SUBJECT,
    _ALL_FACTORS_VIEW,
    _all_factor_observations,
    _dataset_version,
    compute_factor_lab,
    compute_factor_lab_all,
    factor_catalog,
    factor_lab_all_cached,
)
from app.models import EventStudyCache, ForwardReturn, ScannerResult, ScannerRun

H = 20  # a real config horizon


# --------------------------------------------------------------------------------------------------
# Hand-built snapshot fixtures (no engine — exact values by construction)
# --------------------------------------------------------------------------------------------------
def _utc() -> datetime:
    return datetime.now(timezone.utc)


def _add_run(session: Session, asof: date, regime_label: str) -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=_utc(), provider="seed", benchmark="SPY",
        regime_score=50.0, regime_label=regime_label, regime_components_json="[]",
        new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _component_record_json(rs_spy_3m: float, atr_pct: float) -> str:
    """A `record_json` blob carrying the two component factors the byte-identity proof exercises
    (`leadership.components.rs_spy_3m.raw` + `risk.components.atr_pct.raw`) — the EXACT shape
    `_extract_factor_value` reads for a component factor (a list of {name, raw, available} dicts)."""
    return json.dumps({
        "leadership": {"components": [{"name": "rs_spy_3m", "raw": rs_spy_3m, "available": True}]},
        "risk": {"components": [{"name": "atr_pct", "raw": atr_pct, "available": True}]},
    })


def _add_result(session, run_id, ticker, rank, *, lead, entry, risk, rs_spy_3m, atr_pct, sector="Technology"):
    session.add(ScannerResult(
        run_id=run_id, ticker=ticker, name=ticker, sector=sector,
        leadership_score=lead, leadership_bucket="C",
        entry_quality_score=entry, entry_quality_bucket="C",
        risk_score=risk, risk_bucket="C",
        setup_status="Breakout-watch", rank=rank,
        record_json=_component_record_json(rs_spy_3m, atr_pct),
    ))


def _add_fr(session, run_id, symbol, ret, horizon=H):
    session.add(ForwardReturn(
        run_id=run_id, symbol=symbol, horizon=horizon, asof_date=date(2025, 1, 1),
        entry_close=100.0, measured_date=date(2025, 2, 1), realized_return=ret,
    ))


@pytest.fixture()
def lab_engine(tmp_path):
    """A multi-run, mixed-regime fixture with column factors (leadership/entry/risk scores) AND a component
    factor (rs_spy_3m / atr_pct via record_json) populated across enough names to build deciles + a numeric
    rank-IC; the catalog's volatility columns (hv/vcp_contraction/downside_vol) + the unpopulated component
    factors stay NULL -> their all-factors entries are honest zero-N cohorts."""
    engine = make_engine(f"sqlite:///{tmp_path / 'lab_all.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        r1 = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        r2 = _add_run(session, date(2025, 2, 10), regime_label="Risk-off")
        # run-1: 12 names with a monotone-ish spread of values + distinct returns.
        for i in range(1, 13):
            _add_result(
                session, r1.id, f"A{i:02d}", rank=i,
                lead=float(i * 5), entry=float(100 - i * 3), risk=float(i * 4),
                rs_spy_3m=float(i) / 10.0, atr_pct=float(i) / 100.0,
            )
            _add_fr(session, r1.id, f"A{i:02d}", ret=(i - 6) / 100.0)  # spans negatives (downside present)
        # run-2 (different regime): 8 more names so as-of scoping changes n.
        for i in range(1, 9):
            _add_result(
                session, r2.id, f"B{i:02d}", rank=i,
                lead=float(i * 7), entry=float(80 - i * 2), risk=float(i * 6),
                rs_spy_3m=float(i) / 8.0, atr_pct=float(i) / 80.0,
            )
            _add_fr(session, r2.id, f"B{i:02d}", ret=(i - 4) / 80.0)
        session.commit()
    return engine


def _cfg_batch(batch: int):
    cfg = load_config()
    return cfg.model_copy(update={"research": cfg.research.model_copy(update={"read_batch_size": batch})})


def _bytes(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=str)


# ==================================================================================================
# 1. Byte-identity: all-factors per factor == compute_factor_lab per factor (the load-bearing proof)
# ==================================================================================================
@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_all_factors_per_factor_is_byte_identical_to_compute_factor_lab(lab_engine, as_of):
    """For EVERY config-catalog factor, the all-factors entry's deciles + rank-IC + n_total are byte-
    identical to `compute_factor_lab(factor, H, as_of)` for the same factor — across all-history + an
    as-of-scoped window, and across populated / component / zero-N factors. The risk-adjusted column is the
    factor's OWN top-decile risk_adjusted (a re-presentation, not a new derivation)."""
    cfg = load_config()
    catalog = factor_catalog(cfg)
    with Session(lab_engine) as session:
        allp = compute_factor_lab_all(session, H, cfg, as_of=as_of)
        table = {e["key"]: e for e in allp["factors_table"]}
        # one entry per catalog factor, in catalog order (no factor dropped, none invented).
        assert [e["key"] for e in allp["factors_table"]] == [c["key"] for c in catalog]

        saw_populated = False
        saw_zero_n = False
        for c in catalog:
            key = c["key"]
            lab = compute_factor_lab(session, key, H, cfg, as_of=as_of)
            entry = table[key]
            # deciles + rank-IC are EXACTLY equal (the canonical compute_factor_lab outputs).
            assert _bytes(entry["deciles"]) == _bytes(lab["deciles"]), f"deciles drift for {key}"
            assert _bytes(entry["rank_ic"]) == _bytes(lab["rank_ic"]), f"rank-IC drift for {key}"
            assert entry["n_total"] == lab["n_total"], f"n_total drift for {key}"
            # family/label/direction re-presented from the catalog verbatim.
            assert entry["family"] == lab["factor"]["family"]
            assert entry["label"] == lab["factor"]["label"]
            assert entry["direction"] == lab["factor"]["direction"]
            # the risk-adjusted column is the factor's OWN top-decile risk_adjusted (re-presented).
            assert entry["risk_adjusted"] == lab["deciles"][-1]["risk_adjusted"], f"risk_adjusted drift {key}"
            if lab["n_total"] > 0:
                saw_populated = True
            else:
                saw_zero_n = True
        assert saw_populated, "fixture has no populated factor — byte-identity would be vacuous"
        assert saw_zero_n, "fixture has no zero-N factor — the NA-honesty leg is untested"


def test_all_factors_top_level_metadata_matches_config(lab_engine):
    """The all-factors block echoes the resolved horizon + config-driven horizons / default_horizon /
    decile count / min_sample + the honest survivorship & descriptive labels — no second value, no new
    canonical field (the figures live ONLY inside `factors_table`)."""
    cfg = load_config()
    fl = cfg.research.factor_lab
    wf = cfg.walk_forward
    with Session(lab_engine) as session:
        allp = compute_factor_lab_all(session, H, cfg)
    assert allp["horizon"] == H
    assert allp["horizons"] == list(wf.horizons)
    assert allp["default_horizon"] == wf.default_horizon
    assert allp["deciles_count"] == fl.deciles
    assert allp["min_sample"] == wf.min_sample
    assert allp["asof_date"] is None
    assert "survivorship" in allp["survivorship_bias"].lower()
    assert "not a predictive model" in allp["descriptive_caveat"].lower()
    # each entry carries exactly the re-presentation shape (no by_regime, no fabricated field).
    for e in allp["factors_table"]:
        assert set(e) == {"key", "label", "family", "direction", "n_total", "rank_ic", "risk_adjusted", "deciles"}
        assert len(e["deciles"]) == fl.deciles


def test_zero_n_factor_is_honest_na_not_fabricated(lab_engine):
    """A catalog factor with NO stored value (a volatility column never set in the fixture) yields empty
    decile rows (n 0, mean_return None) + NA rank-IC + NA risk-adjusted — never a fabricated number."""
    with Session(lab_engine) as session:
        allp = compute_factor_lab_all(session, H, load_config())
    hv = next(e for e in allp["factors_table"] if e["key"] == "hv")
    assert hv["n_total"] == 0
    assert hv["rank_ic"]["value"] is None and hv["rank_ic"]["n"] == 0
    assert hv["risk_adjusted"] is None
    for d in hv["deciles"]:
        assert d["n"] == 0 and d["mean_return"] is None  # honest NA, never a fabricated 0


# ==================================================================================================
# 2. Cache: HIT == MISS == fresh; stale dataset_version is a MISS and is pruned (real populated row)
# ==================================================================================================
@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_cache_hit_equals_miss_equals_fresh(lab_engine, as_of):
    cfg = load_config()
    with Session(lab_engine) as session:
        fresh = compute_factor_lab_all(session, H, cfg, as_of=as_of)
        cached_miss = factor_lab_all_cached(session, H, cfg, as_of=as_of)  # populates the cache
        cached_hit = factor_lab_all_cached(session, H, cfg, as_of=as_of)   # served from the cache row
        assert _bytes(cached_miss) == _bytes(fresh)
        assert _bytes(cached_hit) == _bytes(fresh)
        # exactly one current-version row was written for this (subject, view, asof_key, horizon).
        rows = session.exec(
            select(EventStudyCache).where(
                EventStudyCache.subject == _ALL_FACTORS_SUBJECT,
                EventStudyCache.view == _ALL_FACTORS_VIEW,
            )
        ).all()
        assert len(rows) == 1


def test_stale_dataset_version_row_is_a_miss_and_is_pruned(lab_engine):
    """A pre-existing cache row keyed to an OLD dataset_version is never hit (the read computes the CURRENT
    stamp) and is PRUNED on the next write — so the cache can never serve a stale figure (iter-38/39)."""
    cfg = load_config()
    with Session(lab_engine) as session:
        version = _dataset_version(session)
        stale_version = version + "-STALE"
        # seed a real already-populated row under a stale stamp with a sentinel payload.
        session.add(EventStudyCache(
            subject=_ALL_FACTORS_SUBJECT, view=_ALL_FACTORS_VIEW, asof_key="all",
            dataset_version=stale_version, horizon=H,
            payload_json=json.dumps({"sentinel": "stale-must-not-be-served"}),
            created_at=_utc(),
        ))
        session.commit()

        served = factor_lab_all_cached(session, H, cfg)
        fresh = compute_factor_lab_all(session, H, cfg)
        assert _bytes(served) == _bytes(fresh), "served the stale cached payload"
        assert "sentinel" not in served

        # the stale row was pruned; a fresh current-version row exists.
        remaining = session.exec(
            select(EventStudyCache).where(EventStudyCache.subject == _ALL_FACTORS_SUBJECT)
        ).all()
        assert all(r.dataset_version == version for r in remaining)
        assert any(r.dataset_version == version for r in remaining)


def test_cache_refreshes_after_dataset_change(lab_engine):
    """The cache REFRESHES after a dataset change: cache a payload, add a snapshot + forward return
    (bumping the dataset-version stamp), and the next read returns the UPDATED aggregate, not the stale one."""
    cfg = load_config()
    with Session(lab_engine) as session:
        before = factor_lab_all_cached(session, H, cfg)
        before_n = next(e for e in before["factors_table"] if e["key"] == "leadership_score")["n_total"]
        v_before = _dataset_version(session)

        new = _add_run(session, date(2025, 3, 10), regime_label="Risk-on")
        _add_result(session, new.id, "C01", rank=1, lead=42.0, entry=42.0, risk=42.0,
                    rs_spy_3m=0.42, atr_pct=0.042)
        _add_fr(session, new.id, "C01", ret=0.07)
        session.commit()
        assert _dataset_version(session) != v_before

        after = factor_lab_all_cached(session, H, cfg)
        after_n = next(e for e in after["factors_table"] if e["key"] == "leadership_score")["n_total"]
        assert after_n == before_n + 1, "cache served a stale (pre-add) figure"
        fresh = compute_factor_lab_all(session, H, cfg)
        assert _bytes(after) == _bytes(fresh)


# ==================================================================================================
# 3. Bounded read (J-105): one heavy read, yield_per-streamed, (run_id, id)-ordered, chunk-independent
# ==================================================================================================
def test_shared_pool_read_is_bounded_and_run_id_id_ordered():
    """Source-level guard (iter-48 disk-full lesson): the shared pool builder streams with `yield_per`,
    orders the ScannerResult side by `(run_id, id)` (rides `ix_scanner_results_run_id` — no temp B-tree),
    and materializes NO unbounded `.all()` over the heavy tables."""
    src = inspect.getsource(_all_factor_observations)
    assert "yield_per" in src, "shared pool must stream with yield_per (bounded read)"
    assert ".order_by(ScannerResult.run_id, ScannerResult.id)" in src, "must order by (run_id, id)"
    # the real materialization call is `session.exec(...).all()` -> `).all()`; the docstring prose uses
    # the back-ticked token "`.all()`" (no preceding paren), so `).all()` matches code only.
    assert ").all()" not in src, "shared pool must not materialize an unbounded .all()"


@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_all_factors_chunk_independent(lab_engine, as_of):
    """The full all-factors payload is byte-identical under read_batch_size=1 vs a huge batch — the stream
    changes peak memory only, never a value or an ordering."""
    with Session(lab_engine) as session:
        small = compute_factor_lab_all(session, H, _cfg_batch(1), as_of=as_of)
        big = compute_factor_lab_all(session, H, _cfg_batch(1_000_000), as_of=as_of)
        assert _bytes(small) == _bytes(big), f"all-factors payload differs by batch (as_of={as_of})"


def test_all_factors_fires_one_shared_pool_read_not_n(lab_engine, monkeypatch):
    """The all-factors view builds the observation pool ONCE for all N factors (one heavy read), NOT once
    per factor — the byte-identity-preserving performance keystone."""
    import app.engine.research as research

    calls = {"n": 0}
    real = research._all_factor_observations

    def _spy(*a, **k):
        calls["n"] += 1
        return real(*a, **k)

    monkeypatch.setattr(research, "_all_factor_observations", _spy)
    with Session(lab_engine) as session:
        research.compute_factor_lab_all(session, H, load_config())
    assert calls["n"] == 1, f"expected ONE shared pool read, got {calls['n']}"
