"""Factor Lab all-factors, ALL-HORIZONS view (iter-52, J-109) — one row per config-catalog factor, each
carrying its full decile table at EVERY config horizon as paired (mean forward-return + mean max-drawdown)
columns, plus the rank-IC + top-decile downside risk-adjusted figure at the FIXED `default_horizon`. Served
from a derived-once cached, bounded read path.

NON-NEGOTIABLE contracts proven here:

  - **Per-(factor, horizon, decile) byte-identity (load-bearing, Single source of truth).** Each factor's
    `by_horizon[h].deciles` EQUALS `compute_factor_lab(session, factor, h, as_of=cutoff)["deciles"]` for the
    same factor/horizon — produced by the SAME `_deciles` builder (now pairing `mean_return` +
    `mean_max_drawdown`) over the SAME per-horizon observation set (one computation path, no second
    derivation, no number recomputed). The entry's `rank_ic` / `risk_adjusted` / `n_total` at the default
    horizon equal `compute_factor_lab(factor, default_h)`'s. Proven across all-history + as-of + populated /
    component / zero-N factors and across the empty horizon (no FRs -> NA return AND NA drawdown).
  - **Paired max-drawdown column (J-109).** Every decile row carries `mean_max_drawdown`; the all-factors
    table cell per (factor, horizon) is that factor's top-decile (D10) mean return + mean max-drawdown.
    Proven non-vacuous (a populated horizon has a real negative drawdown; a drawdown-less horizon is honest
    NA, never a fabricated 0).
  - **Cache schema token (iter-38/39/44).** A pre-iter-52 OLD-SHAPE cache row (the bare-`dataset_version`,
    single-horizon `factors_table`) is a guaranteed MISS and is PRUNED on the next write — tested against a
    real already-populated old-schema row, not a fresh compute. HIT == MISS == fresh; refreshes on a real
    dataset change.
  - **Bounded read (J-105 / iter-46/47/48 OOM lesson).** The shared pools are built ONCE for all horizons
    (one heavy read), `yield_per`-streamed (no unbounded `.all()`), ordering the ScannerResult side by
    `(run_id, id)`. Chunk-independent.

The math runs on tiny hand-built in-memory data (the lab READS stored rows — no engine run needed). The
fixture mixes COLUMN factors, a COMPONENT factor (record_json), catalog factors with NO stored value
(zero-N), FRs at SEVERAL horizons (with a paired max_drawdown), a horizon with NO FRs (empty/NA), and a
horizon whose FRs carry NO max_drawdown (NA-honest mean-MDD).
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
    _ALL_FACTORS_SCHEMA_TOKEN,
    _ALL_FACTORS_SUBJECT,
    _ALL_FACTORS_VIEW,
    _all_factor_observations_by_horizon,
    _dataset_version,
    compute_factor_lab,
    compute_factor_lab_all,
    factor_catalog,
    factor_lab_all_cached,
)
from app.engine.samples import KIND_FACTOR, compute_samples
from app.models import EventStudyCache, ForwardReturn, ScannerResult, ScannerRun

DEFAULT_H = 20  # config walk_forward.default_horizon
POPULATED_HORIZONS = (1, 5, 20)  # horizons with FRs AND a paired max_drawdown
NO_MDD_HORIZON = 60  # has FRs but max_drawdown=None (NA-honest mean-MDD leg)
EMPTY_HORIZON = 10  # no FRs at all (empty decile rows -> NA return AND NA drawdown)


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
    `_extract_factor_value` reads for a component factor."""
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


def _add_fr(session, run_id, symbol, ret, horizon, mdd):
    session.add(ForwardReturn(
        run_id=run_id, symbol=symbol, horizon=horizon, asof_date=date(2025, 1, 1),
        entry_close=100.0, measured_date=date(2025, 2, 1), realized_return=ret, max_drawdown=mdd,
    ))


@pytest.fixture()
def lab_engine(tmp_path):
    """A multi-run, mixed-regime fixture with column factors AND a component factor populated across enough
    names to build deciles + a numeric rank-IC, with forward returns at SEVERAL horizons. Each populated
    horizon carries a paired NEGATIVE max_drawdown; horizon 60 carries FRs with NO max_drawdown (NA-honest
    mean-MDD); horizon 10 has NO FRs (empty/NA). The catalog's volatility columns + unpopulated component
    factors stay NULL -> zero-N cohorts."""
    engine = make_engine(f"sqlite:///{tmp_path / 'lab_all.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        r1 = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        r2 = _add_run(session, date(2025, 2, 10), regime_label="Risk-off")
        for i in range(1, 13):  # run-1: 12 names
            _add_result(
                session, r1.id, f"A{i:02d}", rank=i,
                lead=float(i * 5), entry=float(100 - i * 3), risk=float(i * 4),
                rs_spy_3m=float(i) / 10.0, atr_pct=float(i) / 100.0,
            )
            for h in POPULATED_HORIZONS:
                _add_fr(session, r1.id, f"A{i:02d}", ret=(i - 6) / 100.0 * h, horizon=h, mdd=-(i / 200.0))
            _add_fr(session, r1.id, f"A{i:02d}", ret=(i - 6) / 50.0, horizon=NO_MDD_HORIZON, mdd=None)
        for i in range(1, 9):  # run-2 (different regime): 8 names so as-of scoping changes n
            _add_result(
                session, r2.id, f"B{i:02d}", rank=i,
                lead=float(i * 7), entry=float(80 - i * 2), risk=float(i * 6),
                rs_spy_3m=float(i) / 8.0, atr_pct=float(i) / 80.0,
            )
            for h in POPULATED_HORIZONS:
                _add_fr(session, r2.id, f"B{i:02d}", ret=(i - 4) / 80.0 * h, horizon=h, mdd=-(i / 160.0))
            _add_fr(session, r2.id, f"B{i:02d}", ret=(i - 4) / 40.0, horizon=NO_MDD_HORIZON, mdd=None)
        session.commit()
    return engine


def _cfg_batch(batch: int):
    cfg = load_config()
    return cfg.model_copy(update={"research": cfg.research.model_copy(update={"read_batch_size": batch})})


def _bytes(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=str)


# ==================================================================================================
# 1. Per-(factor, horizon, decile) byte-identity vs the single-horizon compute_factor_lab (load-bearing)
# ==================================================================================================
@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_all_horizons_per_factor_is_byte_identical_to_compute_factor_lab(lab_engine, as_of):
    """For EVERY config-catalog factor and EVERY config horizon, the all-factors `by_horizon[h]` decile table
    is byte-identical to `compute_factor_lab(factor, h, as_of)["deciles"]` — across all-history + an as-of
    window, populated / component / zero-N factors, and the empty horizon. The entry's rank_ic /
    risk_adjusted / n_total at the default horizon equal `compute_factor_lab(factor, default_h)`'s."""
    cfg = load_config()
    horizons = list(cfg.walk_forward.horizons)
    catalog = factor_catalog(cfg)
    with Session(lab_engine) as session:
        allp = compute_factor_lab_all(session, cfg, as_of=as_of)
        table = {e["key"]: e for e in allp["factors_table"]}
        # one entry per catalog factor, in catalog order (no factor dropped, none invented).
        assert [e["key"] for e in allp["factors_table"]] == [c["key"] for c in catalog]

        saw_populated = False
        saw_zero_n = False
        for c in catalog:
            key = c["key"]
            entry = table[key]
            by_h = {b["horizon"]: b for b in entry["by_horizon"]}
            # exactly one block per config horizon, in horizon order.
            assert [b["horizon"] for b in entry["by_horizon"]] == horizons
            for h in horizons:
                lab = compute_factor_lab(session, key, h, cfg, as_of=as_of)
                assert _bytes(by_h[h]["deciles"]) == _bytes(lab["deciles"]), f"deciles drift {key}@{h}"
                assert by_h[h]["n_total"] == lab["n_total"], f"n_total drift {key}@{h}"
            # the default-horizon relabelled figures.
            lab_dh = compute_factor_lab(session, key, DEFAULT_H, cfg, as_of=as_of)
            assert _bytes(entry["rank_ic"]) == _bytes(lab_dh["rank_ic"]), f"rank-IC drift {key}"
            assert entry["risk_adjusted"] == lab_dh["deciles"][-1]["risk_adjusted"], f"ra drift {key}"
            assert entry["n_total"] == lab_dh["n_total"], f"entry n_total drift {key}"
            assert entry["family"] == c["family"] and entry["label"] == c["label"]
            if lab_dh["n_total"] > 0:
                saw_populated = True
            else:
                saw_zero_n = True
        assert saw_populated, "fixture has no populated factor — byte-identity would be vacuous"
        assert saw_zero_n, "fixture has no zero-N factor — the NA-honesty leg is untested"


def test_top_level_metadata_matches_config_and_has_no_single_horizon(lab_engine):
    """The all-factors block echoes the config-driven horizons / default_horizon / decile count / min_sample
    + the honest labels — and carries NO single `horizon` field (the view shows every horizon at once). Each
    entry carries exactly the all-horizons re-presentation shape (no by_regime, no fabricated field)."""
    cfg = load_config()
    fl = cfg.research.factor_lab
    wf = cfg.walk_forward
    with Session(lab_engine) as session:
        allp = compute_factor_lab_all(session, cfg)
    assert "horizon" not in allp  # the all-horizons view has no single served horizon
    assert allp["horizons"] == list(wf.horizons)
    assert allp["default_horizon"] == wf.default_horizon
    assert allp["deciles_count"] == fl.deciles
    assert allp["min_sample"] == wf.min_sample
    assert allp["asof_date"] is None
    assert "survivorship" in allp["survivorship_bias"].lower()
    assert "not a predictive model" in allp["descriptive_caveat"].lower()
    for e in allp["factors_table"]:
        assert set(e) == {"key", "label", "family", "direction", "n_total", "rank_ic", "risk_adjusted", "by_horizon"}
        assert [b["horizon"] for b in e["by_horizon"]] == list(wf.horizons)
        for b in e["by_horizon"]:
            assert set(b) == {"horizon", "n_total", "deciles"}
            assert len(b["deciles"]) == fl.deciles
            for d in b["deciles"]:
                # each decile row pairs mean_return + mean_max_drawdown (J-109).
                assert set(d) == {
                    "decile", "factor_min", "factor_max", "mean_return", "risk_adjusted",
                    "mean_max_drawdown", "n", "low_sample",
                }


# ==================================================================================================
# 2. The paired max-drawdown column is real (populated) AND honest-NA where absent
# ==================================================================================================
def test_paired_max_drawdown_is_populated_and_honest_na(lab_engine):
    """A populated horizon's top-decile cell carries a REAL negative mean max-drawdown (not None/0); the
    drawdown-less horizon (FRs but no stored max_drawdown) carries mean_max_drawdown None on populated
    deciles (NA, never a fabricated 0) while its mean_return stays a real number; the empty horizon carries
    NA return AND NA drawdown."""
    cfg = load_config()
    with Session(lab_engine) as session:
        allp = compute_factor_lab_all(session, cfg)
    lead = next(e for e in allp["factors_table"] if e["key"] == "leadership_score")
    by_h = {b["horizon"]: b for b in lead["by_horizon"]}

    # a populated horizon: at least one decile has a real negative mean max-drawdown.
    pop = by_h[POPULATED_HORIZONS[-1]]["deciles"]
    populated_mdds = [d["mean_max_drawdown"] for d in pop if d["n"] > 0]
    assert any(m is not None and m < 0 for m in populated_mdds), "paired MDD column never populated"

    # the drawdown-less horizon: a populated decile has a real mean_return but NA mean_max_drawdown.
    no_mdd = by_h[NO_MDD_HORIZON]["deciles"]
    populated = [d for d in no_mdd if d["n"] > 0]
    assert populated, "drawdown-less horizon has no populated decile — NA leg vacuous"
    assert all(d["mean_max_drawdown"] is None for d in populated), "fabricated MDD where none stored"
    assert any(d["mean_return"] is not None for d in populated), "return wrongly NA'd"

    # the empty horizon: every decile is NA return AND NA drawdown (no fabricated bucket).
    empty = by_h[EMPTY_HORIZON]["deciles"]
    assert all(d["n"] == 0 and d["mean_return"] is None and d["mean_max_drawdown"] is None for d in empty)


def test_zero_n_factor_is_honest_na_not_fabricated(lab_engine):
    """A catalog factor with NO stored value (a volatility column never set) yields, at EVERY horizon, empty
    decile rows (n 0, mean_return None, mean_max_drawdown None) + NA rank-IC + NA risk-adjusted — never a
    fabricated number."""
    cfg = load_config()
    with Session(lab_engine) as session:
        allp = compute_factor_lab_all(session, cfg)
    hv = next(e for e in allp["factors_table"] if e["key"] == "hv")
    assert hv["n_total"] == 0
    assert hv["rank_ic"]["value"] is None and hv["rank_ic"]["n"] == 0
    assert hv["risk_adjusted"] is None
    for b in hv["by_horizon"]:
        for d in b["deciles"]:
            assert d["n"] == 0 and d["mean_return"] is None and d["mean_max_drawdown"] is None


# ==================================================================================================
# 3. Cache: HIT == MISS == fresh; the schema token makes a pre-iter-52 row a MISS and prunes it
# ==================================================================================================
@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_cache_hit_equals_miss_equals_fresh(lab_engine, as_of):
    cfg = load_config()
    with Session(lab_engine) as session:
        fresh = compute_factor_lab_all(session, cfg, as_of=as_of)
        cached_miss = factor_lab_all_cached(session, cfg, as_of=as_of)  # populates the cache
        cached_hit = factor_lab_all_cached(session, cfg, as_of=as_of)   # served from the cache row
        assert _bytes(cached_miss) == _bytes(fresh)
        assert _bytes(cached_hit) == _bytes(fresh)
        rows = session.exec(
            select(EventStudyCache).where(
                EventStudyCache.subject == _ALL_FACTORS_SUBJECT,
                EventStudyCache.view == _ALL_FACTORS_VIEW,
            )
        ).all()
        assert len(rows) == 1  # exactly one current-shape row for this (subject, view, asof_key)


def test_pre_iter52_old_schema_row_is_a_miss_and_is_pruned(lab_engine):
    """An already-populated OLD-SCHEMA cache row (the pre-iter-52 single-horizon `factors_table` shape, keyed
    by the BARE `_dataset_version` WITHOUT the schema token) is never hit (the read computes the
    schema-token-folded stamp) and is PRUNED on the next write — so the cache can never serve the stale
    old-shape figure field-less (iter-38/39/44). This is the schema-token MISS-then-populate proof against a
    real populated row, not a fresh compute."""
    cfg = load_config()
    with Session(lab_engine) as session:
        base_version = _dataset_version(session)  # the pre-iter-52 stamp (no schema token)
        # seed a real already-populated old-schema row under the bare stamp with a sentinel payload.
        session.add(EventStudyCache(
            subject=_ALL_FACTORS_SUBJECT, view=_ALL_FACTORS_VIEW, asof_key="all",
            dataset_version=base_version, horizon=cfg.walk_forward.default_horizon,
            payload_json=json.dumps({"sentinel": "old-shape-must-not-be-served", "factors_table": []}),
            created_at=_utc(),
        ))
        session.commit()

        served = factor_lab_all_cached(session, cfg)
        fresh = compute_factor_lab_all(session, cfg)
        assert _bytes(served) == _bytes(fresh), "served the stale old-schema cached payload"
        assert "sentinel" not in served
        assert served["factors_table"], "served an empty old-shape table"

        # the old-schema (bare-version) row was pruned; the remaining rows all carry the schema token.
        remaining = session.exec(
            select(EventStudyCache).where(EventStudyCache.subject == _ALL_FACTORS_SUBJECT)
        ).all()
        token_version = f"{base_version}-{_ALL_FACTORS_SCHEMA_TOKEN}"
        assert all(r.dataset_version == token_version for r in remaining)
        assert any(r.dataset_version == token_version for r in remaining)


def test_cache_refreshes_after_dataset_change(lab_engine):
    """The cache REFRESHES after a dataset change: cache a payload, add a snapshot + forward return (bumping
    the dataset-version stamp), and the next read returns the UPDATED aggregate, not the stale one."""
    cfg = load_config()
    with Session(lab_engine) as session:
        before = factor_lab_all_cached(session, cfg)
        before_n = next(e for e in before["factors_table"] if e["key"] == "leadership_score")["n_total"]
        v_before = _dataset_version(session)

        new = _add_run(session, date(2025, 3, 10), regime_label="Risk-on")
        _add_result(session, new.id, "C01", rank=1, lead=42.0, entry=42.0, risk=42.0,
                    rs_spy_3m=0.42, atr_pct=0.042)
        _add_fr(session, new.id, "C01", ret=0.07, horizon=DEFAULT_H, mdd=-0.03)
        session.commit()
        assert _dataset_version(session) != v_before

        after = factor_lab_all_cached(session, cfg)
        after_n = next(e for e in after["factors_table"] if e["key"] == "leadership_score")["n_total"]
        assert after_n == before_n + 1, "cache served a stale (pre-add) figure"
        fresh = compute_factor_lab_all(session, cfg)
        assert _bytes(after) == _bytes(fresh)


# ==================================================================================================
# 4. Bounded read (J-105): one heavy read, yield_per-streamed, (run_id, id)-ordered, chunk-independent
# ==================================================================================================
def test_shared_pool_read_is_bounded_and_run_id_id_ordered():
    """Source-level guard (iter-46/47/48 OOM lesson): the all-horizons shared pool builder streams with
    `yield_per`, orders the ScannerResult side by `(run_id, id)` (rides `ix_scanner_results_run_id` — no temp
    B-tree), and materializes NO unbounded `.all()` over the heavy tables."""
    src = inspect.getsource(_all_factor_observations_by_horizon)
    assert "yield_per" in src, "shared pool must stream with yield_per (bounded read)"
    assert ".order_by(ScannerResult.run_id, ScannerResult.id)" in src, "must order by (run_id, id)"
    # the real materialization call is `session.exec(...).all()` -> `).all()`; only code, never the docstring.
    assert ").all()" not in src, "shared pool must not materialize an unbounded .all()"


@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_all_factors_chunk_independent(lab_engine, as_of):
    """The full all-horizons payload is byte-identical under read_batch_size=1 vs a huge batch — the stream
    changes peak memory only, never a value or an ordering."""
    with Session(lab_engine) as session:
        small = compute_factor_lab_all(session, _cfg_batch(1), as_of=as_of)
        big = compute_factor_lab_all(session, _cfg_batch(1_000_000), as_of=as_of)
        assert _bytes(small) == _bytes(big), f"all-factors payload differs by batch (as_of={as_of})"


@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_samples_count_coherent_for_every_factor_horizon_decile(lab_engine, as_of):
    """The samples drill-down for the new (factor, horizon, decile) cohort is count-coherent at EVERY config
    horizon (J-51/J-65): for a populated factor, every decile chip's samples `total` equals the all-factors
    view's published `by_horizon[h].deciles[d].n` — in both all-history and as-of mode, including NA/low-
    sample deciles (n==0 -> an honest empty cohort, never a 4xx)."""
    cfg = load_config()
    horizons = list(cfg.walk_forward.horizons)
    with Session(lab_engine) as session:
        allp = compute_factor_lab_all(session, cfg, as_of=as_of)
        lead = next(e for e in allp["factors_table"] if e["key"] == "leadership_score")
        by_h = {b["horizon"]: b for b in lead["by_horizon"]}
        checked = 0
        for h in horizons:
            for d in by_h[h]["deciles"]:
                s = compute_samples(
                    session, kind=KIND_FACTOR, horizon=h, config=cfg, as_of=as_of,
                    factor_key="leadership_score", slice_kind="decile", decile=d["decile"],
                )
                assert s["total"] == d["n"], f"decile coherence drift @h={h} d={d['decile']}"
                assert len(s["rows"]) == d["n"]
                checked += 1
        assert checked == len(horizons) * cfg.research.factor_lab.deciles


def test_all_factors_fires_one_shared_pool_read_not_n(lab_engine, monkeypatch):
    """The all-factors view builds the observation pools ONCE for all N factors at ALL horizons (one heavy
    read), NOT once per factor or per horizon — the byte-identity-preserving performance keystone."""
    import app.engine.research as research

    calls = {"n": 0}
    real = research._all_factor_observations_by_horizon

    def _spy(*a, **k):
        calls["n"] += 1
        return real(*a, **k)

    monkeypatch.setattr(research, "_all_factor_observations_by_horizon", _spy)
    with Session(lab_engine) as session:
        research.compute_factor_lab_all(session, load_config())
    assert calls["n"] == 1, f"expected ONE shared pool read, got {calls['n']}"
