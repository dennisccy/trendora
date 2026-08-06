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
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone

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

# Hang detector for the concurrency tests below. Deliberately FAR BELOW the shipped
# `research._FACTOR_LAB_ALL_WAIT_TIMEOUT_S` (900s): every scenario exercised here resolves in well under a
# second of real work, so a caller that is still alive after a minute has wedged — and this fails it as a
# hang instead of letting it "pass slowly" by riding the production wait ceiling.
BOUNDED_TIMEOUT_S = 60.0

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


def _cfg_batch(batch: int, run_chunk: int | None = None):
    """The real config with `research.read_batch_size` overridden to `batch` (the ROW-count `yield_per`
    probe) and `research.factor_join_run_chunk` (the iter-29 RUN-COUNT accumulator width — a DIFFERENT unit)
    overridden to `run_chunk`, defaulting to the same value so every pre-existing chunk-independence probe
    varies BOTH knobs (a huge value collapses the shared pool build back to the pre-iter-29 single sweep)."""
    cfg = load_config()
    return cfg.model_copy(update={"research": cfg.research.model_copy(update={
        "read_batch_size": batch,
        "factor_join_run_chunk": batch if run_chunk is None else run_chunk,
    })})


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


# ==================================================================================================
# 4b. iter-29 fix-2 (AG-8) — the JOIN ACCUMULATOR is run-chunked, not just the source streams
#
# Streaming both source queries was never enough: `fr_by_h` was one map per horizon holding every distinct
# (run_id, symbol) pair of the FULL history at once (~4.0M entries across the 5 config horizons on the live
# basis). That accumulator's fill site is where `logs/backend.log` recorded the live `MemoryError` that made
# `GET /research/factor-lab?all=true` return 500 on 4 of 4 visits — the page's ONLY consumer, since
# `FactorLabPage` requests `?all=true` on mount. The proofs below pin the bound at the SHIPPED width and
# pin that the chunking changed no value.
# ==================================================================================================
def _all_pools_reference_unchunked(session, factors, horizons, as_of, cfg):
    """A pinned copy of the PRE-FIX `_all_factor_observations_by_horizon` body: ONE unbounded `fr_by_h`
    accumulator built from a SINGLE un-sliced FR scan over the whole history, and ONE un-sliced
    `ScannerResult` sweep (no `_all_fr_slice_map`, no chunk loop). The regression oracle for the chunked
    rewrite's byte-identity proof — it calls the SAME unchanged `_extract_factor_value` /
    `parse_factor_source` helpers the real function still uses, so any divergence can only come from the
    chunking itself."""
    from app.engine.research import _extract_factor_value, parse_factor_source

    parsed_by_key = {f.key: parse_factor_source(f.source) for f in factors}
    batch = cfg.research.read_batch_size
    fr_stmt = select(
        ForwardReturn.horizon, ForwardReturn.run_id, ForwardReturn.symbol,
        ForwardReturn.realized_return, ForwardReturn.max_drawdown,
    ).where(ForwardReturn.horizon.in_(horizons))
    if as_of is not None:
        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
            ScannerRun.asof_date <= as_of
        )
    fr_by_h = {h: {} for h in horizons}
    runs_with_fr_set = set()
    for h, run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
        fr_by_h[h][(run_id, symbol)] = (realized_return, max_drawdown)
        runs_with_fr_set.add(run_id)
    runs_with_fr = sorted(runs_with_fr_set)
    res_stmt = (
        select(ScannerResult)
        .where(ScannerResult.run_id.in_(runs_with_fr))
        .order_by(ScannerResult.run_id, ScannerResult.id)
    )
    results = session.exec(res_stmt).yield_per(batch) if runs_with_fr else []
    pools = {h: [] for h in horizons}
    for res in results:
        values = None
        for h in horizons:
            fr = fr_by_h[h].get((res.run_id, res.ticker))
            if fr is None:
                continue
            if values is None:
                values = {key: _extract_factor_value(res, parsed) for key, parsed in parsed_by_key.items()}
            realized, max_drawdown = fr
            pools[h].append({
                "run_id": res.run_id, "ticker": res.ticker, "return": realized,
                "max_drawdown": max_drawdown, "values": values,
            })
    return pools


def _materialize_compact_pools(core_records, pools) -> dict:
    """iter-31 test-only adapter: expands the compact `(core_records, pools)` return shape back into the OLD
    pinned-reference shape (`{horizon: [{run_id, ticker, return, max_drawdown, values}, ...]}`) so the
    byte-identity oracle (`_all_pools_reference_unchunked`, deliberately left UNCHANGED — it is the pinned
    pre-fix reference, not something this iteration should touch) can compare like-for-like. `values` is
    rebuilt as a dict keyed positionally 0..N-1 (the pinned reference's `values` dict is keyed by factor
    KEY, not position — so this test instead compares the VALUES TUPLE contents in factor order, which is
    exactly what the pinned reference's dict.values() would iterate in, since both are built from the SAME
    `factors` list order). Proves the DATA is unchanged; the representation is intentionally different."""
    out: dict[int, list[dict]] = {}
    for h, pool in pools.items():
        rows = []
        for core_idx, ret, mdd in pool:
            run_id, ticker, values = core_records[core_idx]
            rows.append({
                "run_id": run_id, "ticker": ticker, "return": ret, "max_drawdown": mdd,
                "values": list(values),  # positional, factor-order — compared against the reference below
            })
        out[h] = rows
    return out


def _reference_as_positional(reference: dict, factors: list) -> dict:
    """Re-key the pinned reference's per-observation `values` dict (keyed by factor KEY) into the SAME
    factor-order positional list `_materialize_compact_pools` produces, so the two shapes compare byte-for-
    byte without asserting anything about dict-vs-tuple representation itself (iter-31 — representation is
    allowed to change; the underlying data must not)."""
    keys = [f.key for f in factors]
    out: dict[int, list[dict]] = {}
    for h, rows in reference.items():
        out[h] = [
            {
                "run_id": r["run_id"], "ticker": r["ticker"], "return": r["return"],
                "max_drawdown": r["max_drawdown"], "values": [r["values"][k] for k in keys],
            }
            for r in rows
        ]
    return out


@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_shared_pools_chunked_equal_the_pinned_unchunked_reference(lab_engine, as_of):
    """The run-chunked shared-pool build is byte-identical to the pinned pre-fix single-accumulator
    reference — same rows, same per-horizon order, same factor values — for all-history AND an as-of window
    that splits the fixture's two runs. iter-31: the chunked build now returns the compact
    `(core_records, pools)` shape (a return-value memory-representation redesign); materialized back to the
    old per-observation shape, the DATA is still byte-identical to the pinned reference."""
    cfg = _cfg_batch(2, run_chunk=1)  # 1 run id per slice over the fixture's 2 runs -> real chunking
    factors = list(cfg.research.factor_lab.factors)
    horizons = list(cfg.walk_forward.horizons)
    with Session(lab_engine) as session:
        core_records, pools = _all_factor_observations_by_horizon(session, factors, horizons, as_of, cfg=cfg)
        reference = _all_pools_reference_unchunked(session, factors, horizons, as_of, cfg)
    materialized = _materialize_compact_pools(core_records, pools)
    positional_reference = _reference_as_positional(reference, factors)
    assert _bytes(materialized) == _bytes(positional_reference), (
        f"chunked compact pools != pinned pre-fix pools (as_of={as_of})"
    )


def test_shared_pool_accumulator_is_chunk_bounded_at_the_shipped_config(tmp_path, monkeypatch):
    """The all-horizons join accumulator is bounded at the SHIPPED `research.factor_join_run_chunk` — no
    `_cfg_batch` override, because an override is exactly how the first iter-29 bound shipped inert. Builds
    a fixture with (shipped width + 3) runs so real chunking is REQUIRED, then asserts the builder made >= 2
    slice reads and that no single slice's maps ever held the whole fixture's (run_id, symbol) pairs."""
    import app.engine.research as research

    cfg = load_config()  # the REAL config.yaml — deliberately NOT overridden
    width = cfg.research.factor_join_run_chunk
    n_runs, tickers = width + 3, ("AA", "BB")
    engine = make_engine(f"sqlite:///{tmp_path / 'all_shipped_chunk.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for i in range(n_runs):
            run = _add_run(session, date(2025, 1, 1) + timedelta(days=i), regime_label="Risk-on")
            for j, base in enumerate(tickers):
                ticker = f"{base}{i}"
                _add_result(session, run.id, ticker, rank=j + 1, lead=float(50 + (i % 7) + j),
                            entry=float(40 + j), risk=float(30 + j),
                            rs_spy_3m=float(j) / 10.0, atr_pct=float(j) / 100.0)
                for h in POPULATED_HORIZONS:
                    _add_fr(session, run.id, ticker, ret=0.01 * (i + 1), horizon=h, mdd=-0.03)
        session.commit()

    observed_sizes: list[int] = []
    real_slice_map = research._all_fr_slice_map

    def _wrapped(session, horizons, slice_run_ids, batch):
        result = real_slice_map(session, horizons, slice_run_ids, batch)
        observed_sizes.append(sum(len(m) for m in result.values()))
        return result

    monkeypatch.setattr(research, "_all_fr_slice_map", _wrapped)
    factors = list(cfg.research.factor_lab.factors)
    horizons = list(cfg.walk_forward.horizons)
    with Session(engine) as session:
        _core_records, pools = research._all_factor_observations_by_horizon(
            session, factors, horizons, None, cfg=cfg
        )

    total_pairs = n_runs * len(tickers) * len(POPULATED_HORIZONS)
    assert sum(len(p) for p in pools.values()) == total_pairs, "sanity: every fixture pair must surface"
    assert len(observed_sizes) >= 2, (
        f"the SHIPPED config produced {len(observed_sizes)} chunk(s) over {n_runs} runs — the all-horizons "
        f"accumulator bound is inert at the real configuration (width={width})"
    )
    assert max(observed_sizes) <= width * len(tickers) * len(POPULATED_HORIZONS), (
        f"a slice exceeded its configured run-chunk width: {max(observed_sizes)} entries"
    )
    assert max(observed_sizes) < total_pairs, (
        "the live accumulator must never hold the WHOLE fixture's pairs at once under the shipped config"
    )


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


# ==================================================================================================
# 5. iter-31 (AG-8, deferred-twice finding) — the RETURN-VALUE pool bound + the `factor_lab_all_cached`
# single-flight guard (audit B5). Two causally-linked fixes: a concurrent duplicate compute doubles the
# exact peak the pool bound is trying to create, so this iteration closes both together (session rule 5).
# ==================================================================================================

# Live basis measured 2026-07-29 (apps/backend/data/trendora.db, ~4.97 GB): per-horizon forward_returns /
# pool sizes range from 771,629 (h=60) to 804,372 (h=1) across the 5 configured horizons — the SAME figures
# documented in `config.yaml`'s `factor_pool_max_observations` comment (781,965 scanner_results total,
# 781,417 with a realized return at >= 1 horizon). A ceiling BELOW this range would fire the AG-8 disclosure
# warning on every normal request (noise, not signal); a ceiling so large it could never realistically bind
# (e.g. 10**12) would be a disconnected, meaningless "shipped-config" number in the same spirit as the
# iter-29 lesson. This bounds the shipped value to a sane window.
_LIVE_POOL_OBSERVATIONS_MAX = 804_372
_MAX_MEANINGFUL_POOL_CEILING = _LIVE_POOL_OBSERVATIONS_MAX * 20


def test_shipped_factor_pool_max_observations_actually_covers_the_live_basis():
    """iter-31 TC-6: the SHIPPED `research.factor_pool_max_observations` must sit ABOVE today's live
    per-horizon observation count (documented above) — otherwise the AG-8 disclosure warning would fire on
    EVERY normal request (noise, not signal) — but not so large it is a disconnected, meaningless number.
    Mirrors `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis`'s shipped-vs-fixture-width
    convention (`test_research_streaming.py`), applied to a CEILING instead of a chunk WIDTH: no
    `_cfg_batch`-style override, the REAL `config.yaml` value, checked against the REAL measured basis."""
    research_cfg = load_config().research
    cap = research_cfg.factor_pool_max_observations
    assert _LIVE_POOL_OBSERVATIONS_MAX <= cap <= _MAX_MEANINGFUL_POOL_CEILING, (
        f"research.factor_pool_max_observations={cap} does not sanely cover the live basis "
        f"({_LIVE_POOL_OBSERVATIONS_MAX} observations measured on the live DB, 2026-07-29): it must satisfy "
        f"{_LIVE_POOL_OBSERVATIONS_MAX} <= cap <= {_MAX_MEANINGFUL_POOL_CEILING}"
    )


def test_factor_pool_cap_exceeded_logs_a_warning_and_never_truncates(lab_engine, caplog):
    """iter-31: when a horizon's pool genuinely exceeds the configured `factor_pool_max_observations`
    ceiling, `_all_factor_observations_by_horizon` logs a WARNING naming the horizon/count/cap — and still
    returns the FULL, untruncated pool (AG-8: disclosure only; truncating would break the byte-identity
    contract the whole module exists to preserve). Uses a tiny overridden cap on the cheap `lab_engine`
    fixture — the SEPARATE test above proves the SHIPPED value's real-world adequacy; this one proves the
    mechanism actually fires and never truncates."""
    cfg = load_config()
    tiny_cap_cfg = cfg.model_copy(update={"research": cfg.research.model_copy(update={
        "factor_pool_max_observations": 1,
    })})
    factors = list(tiny_cap_cfg.research.factor_lab.factors)
    horizons = list(tiny_cap_cfg.walk_forward.horizons)
    with Session(lab_engine) as session:
        with caplog.at_level("WARNING", logger="trendora.research"):
            core_records, pools = _all_factor_observations_by_horizon(
                session, factors, horizons, None, cfg=tiny_cap_cfg
            )
    # sanity: the fixture genuinely exceeds the tiny cap at every populated horizon (test not vacuous).
    for h in POPULATED_HORIZONS:
        assert len(pools[h]) > 1, f"fixture too small to exceed cap=1 at horizon {h} — test is vacuous"
    assert "factor_pool_max_observations exceeded" in caplog.text, (
        "expected a WARNING when a horizon's pool exceeds the configured cap"
    )
    # never truncated: full pools + full core_records are returned untouched by the disclosure net.
    assert core_records, "core_records must not be truncated away by the disclosure net"
    for h in POPULATED_HORIZONS:
        assert len(pools[h]) > tiny_cap_cfg.research.factor_pool_max_observations, (
            f"horizon {h} pool was truncated down to the tiny cap — must never truncate"
        )


def test_factor_lab_all_cached_single_flight_dedups_concurrent_miss_to_one_compute(lab_engine):
    """iter-31 TC-3 (audit B5, AG-8): N concurrent `factor_lab_all_cached` MISS callers for the SAME identity
    trigger the underlying heavy `compute_factor_lab_all` EXACTLY ONCE (call-count instrumentation, mirrors
    `test_forward_aggregates_ingest_cached_dedups_concurrent_same_key_miss_to_one_compute` in
    `test_forward_testing_concurrency.py`) — not merely that concurrent callers happen to agree on an
    answer. All N callers still return byte-identical payloads, and none hangs."""
    import app.engine.research as research

    cfg = load_config()
    n_callers = 5
    call_count = {"n": 0}
    real = research.compute_factor_lab_all

    def _counting(*args, **kwargs):
        call_count["n"] += 1
        return real(*args, **kwargs)

    def _caller():
        with Session(lab_engine) as session:
            return research.factor_lab_all_cached(session, cfg)

    research.compute_factor_lab_all = _counting
    try:
        with ThreadPoolExecutor(max_workers=n_callers) as pool:
            futures = [pool.submit(_caller) for _ in range(n_callers)]
            results = [f.result() for f in as_completed(futures, timeout=BOUNDED_TIMEOUT_S)]
    finally:
        research.compute_factor_lab_all = real

    assert len(results) == n_callers, "not every caller completed — a caller hung"
    assert call_count["n"] == 1, (
        f"expected compute_factor_lab_all to run exactly once for {n_callers} concurrent same-key MISSes; "
        f"it ran {call_count['n']} times — the single-flight de-dup did not hold (audit B5 regression)"
    )
    first = _bytes(results[0])
    for payload in results[1:]:
        assert _bytes(payload) == first, "concurrent callers returned DIFFERENT payloads for the same key"


# The bounded wait a NON-owner caller spends before giving up and computing independently must exceed
# THIS call's own compute duration, not a sibling module's. One full cold-MISS `compute_factor_lab_all` on
# the live deep basis, under the mandatory host-guard CPU caps (AG-10, permanent on this host), was measured
# at ~2-4 min and ~4-5 min across two independent backend restarts (2026-07-29, iter-31 dev handoff) —
# worst observed ~300s. The FIRST cut of the guard shipped a 45s wait copied from
# `forward_testing._FORWARD_AGG_WAIT_TIMEOUT_S` (a much faster compute): with 45s << 300s EVERY waiter would
# have timed out mid-compute and started its own duplicate compute — the guard would have been inert
# exactly where audit B5 needed it. The two tests below lock that in: the shipped constant against the
# measured duration, and the de-dup behaviour across a compute that runs PAST the old 45s ceiling.
_MEASURED_LIVE_COLD_MISS_S = 300.0
_PRE_FIX_WAIT_TIMEOUT_S = 45.0
_MAX_MEANINGFUL_WAIT_S = 60.0 * 60.0


def test_shipped_factor_lab_all_wait_timeout_covers_the_measured_live_cold_miss_compute():
    """iter-31 (review fix): the SHIPPED `_FACTOR_LAB_ALL_WAIT_TIMEOUT_S` must sit ABOVE the MEASURED live
    cold-MISS compute duration (~300s worst observed), with headroom — otherwise a waiter gives up while the
    owner is still legitimately computing and starts the duplicate compute audit B5 requires eliminated.
    Same shipped-value-vs-live-measurement convention as
    `test_shipped_factor_pool_max_observations_actually_covers_the_live_basis` above and
    `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis` (`test_research_streaming.py`):
    the REAL shipped constant, checked against a REAL measurement, not a fixture-sized proxy. The upper
    bound keeps it a bounded wait rather than an effectively-infinite one (the failure path must stay
    reachable within an hour, never a hang)."""
    import app.engine.research as research

    shipped = research._FACTOR_LAB_ALL_WAIT_TIMEOUT_S
    assert shipped > _PRE_FIX_WAIT_TIMEOUT_S, (
        f"_FACTOR_LAB_ALL_WAIT_TIMEOUT_S={shipped}s is back at (or below) the rejected pre-fix 45s value "
        f"copied from forward_testing — it must be sized against THIS call's own compute duration"
    )
    assert shipped >= 2 * _MEASURED_LIVE_COLD_MISS_S, (
        f"_FACTOR_LAB_ALL_WAIT_TIMEOUT_S={shipped}s leaves no margin over the measured live cold-MISS "
        f"compute ({_MEASURED_LIVE_COLD_MISS_S}s, 2026-07-29): a waiter would time out mid-compute and "
        f"start a duplicate compute (audit B5 regression). Require >= {2 * _MEASURED_LIVE_COLD_MISS_S}s."
    )
    assert shipped <= _MAX_MEANINGFUL_WAIT_S, (
        f"_FACTOR_LAB_ALL_WAIT_TIMEOUT_S={shipped}s is so large the wait is no longer meaningfully bounded; "
        f"the independent-compute fallback must stay reachable (<= {_MAX_MEANINGFUL_WAIT_S}s)"
    )


def test_factor_lab_all_single_flight_holds_across_a_compute_past_the_pre_fix_timeout(lab_engine):
    """iter-31 (review fix), SLOW BY DESIGN (~48s): the de-dup must hold across a compute that lasts LONGER
    than the rejected 45s wait — the property TC-3 above cannot prove, because its owner compute finishes in
    milliseconds and never approaches the ceiling. The owner's compute here is stretched past the pre-fix
    timeout with a real sleep while the SHIPPED wait constant is left untouched; the waiter must still be
    waiting when the owner persists, so `compute_factor_lab_all` runs EXACTLY ONCE. Teeth: at the pre-fix
    45s value the waiter would wake at 45s, find no persisted row, and compute independently — this test
    would then observe 2 computes and fail. Real time is used deliberately (no patched clock, no scaled
    proxy): the finding was that the constant was untested against a realistic duration."""
    import time

    import app.engine.research as research

    cfg = load_config()
    slow_compute_s = _PRE_FIX_WAIT_TIMEOUT_S + 3.0
    hang_after_s = slow_compute_s + BOUNDED_TIMEOUT_S
    owner_claimed = threading.Event()
    call_count = {"n": 0}
    real = research.compute_factor_lab_all

    def _slow_compute(*args, **kwargs):
        call_count["n"] += 1
        owner_claimed.set()
        time.sleep(slow_compute_s)  # stand-in for the real ~2-5 min live cold-MISS compute
        return real(*args, **kwargs)

    results: dict[str, dict] = {}

    def _call(tag: str):
        with Session(lab_engine) as session:
            results[tag] = research.factor_lab_all_cached(session, cfg)

    research.compute_factor_lab_all = _slow_compute
    start = time.monotonic()
    try:
        owner_thread = threading.Thread(target=_call, args=("owner",))
        owner_thread.start()
        assert owner_claimed.wait(timeout=BOUNDED_TIMEOUT_S), "owner never entered the compute"
        waiter_thread = threading.Thread(target=_call, args=("waiter",))
        waiter_thread.start()
        owner_thread.join(timeout=hang_after_s)
        waiter_thread.join(timeout=hang_after_s)
    finally:
        research.compute_factor_lab_all = real
    elapsed = time.monotonic() - start

    assert not owner_thread.is_alive() and not waiter_thread.is_alive(), "a caller hung"
    assert call_count["n"] == 1, (
        f"compute_factor_lab_all ran {call_count['n']} times for one slow ({slow_compute_s}s) same-key "
        f"MISS: the waiter's bounded wait elapsed BEFORE the owner finished and it started a duplicate "
        f"compute — the single-flight guard is inert at this call's real compute duration (audit B5)"
    )
    assert elapsed < 2 * slow_compute_s, (
        f"resolution took {elapsed:.1f}s for a single {slow_compute_s}s compute — the waiter serialised "
        f"behind a SECOND compute instead of sharing the owner's result"
    )
    assert set(results) == {"owner", "waiter"}, "a caller returned nothing"
    assert _bytes(results["waiter"]) == _bytes(results["owner"]), (
        "the waiter's payload differs from the owner's for the same cache identity"
    )


def test_factor_lab_all_cached_waiter_does_not_deadlock_when_owner_raises(lab_engine):
    """iter-31 TC-4 (audit B5): when the OWNER of a same-key MISS's in-flight computation raises, a
    concurrent WAITING caller for that SAME key never blocks past the bounded timeout — it either raises its
    own clean, isolated error or independently recomputes and returns a byte-identical payload. Mirrors
    `test_forward_aggregates_ingest_cached_waiter_does_not_deadlock_when_owner_raises`. Proves the
    single-flight fix's failure path cannot wedge a waiter (its `finally` releases the in-flight slot and
    wakes waiters on ANY exit, success or failure)."""
    import time

    import app.engine.research as research

    cfg = load_config()
    owner_started = threading.Event()
    owner_may_raise = threading.Event()
    real = research.compute_factor_lab_all
    call_count = {"n": 0}

    def _owner_then_recover(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            owner_started.set()
            owner_may_raise.wait(timeout=10)
            raise RuntimeError("forced owner failure (iter-31 TC-4 probe)")
        return real(*args, **kwargs)

    owner_result: dict = {}
    waiter_result: dict = {}

    def _owner_call():
        with Session(lab_engine) as session:
            try:
                research.factor_lab_all_cached(session, cfg)
            except Exception as exc:  # noqa: BLE001 — captured for the assertion below, never swallowed
                owner_result["error"] = exc

    def _waiter_call():
        with Session(lab_engine) as session:
            try:
                waiter_result["payload"] = research.factor_lab_all_cached(session, cfg)
            except Exception as exc:  # noqa: BLE001
                waiter_result["error"] = exc

    research.compute_factor_lab_all = _owner_then_recover
    start = time.monotonic()
    try:
        owner_thread = threading.Thread(target=_owner_call)
        waiter_thread = threading.Thread(target=_waiter_call)
        owner_thread.start()
        assert owner_started.wait(timeout=10), "owner never claimed the in-flight slot"
        waiter_thread.start()
        time.sleep(0.2)  # let the waiter register as a non-owner before the owner is allowed to raise
        owner_may_raise.set()
        owner_thread.join(timeout=BOUNDED_TIMEOUT_S)
        waiter_thread.join(timeout=BOUNDED_TIMEOUT_S)
    finally:
        research.compute_factor_lab_all = real
    elapsed = time.monotonic() - start

    assert not owner_thread.is_alive(), "owner thread did not finish — treat as a hang"
    assert not waiter_thread.is_alive(), "waiter thread did not finish — treat as a hang"
    assert elapsed < BOUNDED_TIMEOUT_S, f"resolution took {elapsed:.1f}s — treat as a hang, not a slow pass"
    assert "error" in owner_result, "expected the owner's own forced exception to propagate to its caller"

    assert "error" in waiter_result or "payload" in waiter_result, (
        "the waiter neither raised a clean error nor returned a payload — the failure path is broken"
    )
    if "payload" in waiter_result:
        with Session(lab_engine) as session:
            direct = real(session, cfg)
        assert _bytes(waiter_result["payload"]) == _bytes(direct), (
            "waiter's fallback payload was not byte-identical to a direct compute"
        )


def test_already_waiting_caller_is_served_the_cooldown_not_a_second_doomed_compute(lab_engine):
    """ops-hardening iter-50 AUDIT (finding B1) — the memory-pressure cooldown must also cover the
    single-flight WAITER path, not just callers that arrive after the degrade.

    The B4 cooldown is checked only at the TOP of `factor_lab_all_cached`, before the single-flight slot.
    A caller that was ALREADY waiting when the owner degrades wakes on the owner's `finally`, re-checks the
    persisted cache (empty by construction — a degraded payload is deliberately never persisted) and, before
    this fix, fell straight through into its OWN full-scale multi-GB compute inside the process that had
    just run out of memory. That is the exact amplification the cooldown exists to stop, on the exact path
    the 2026-08-05 outage took (five waiters fell through in 2m16s, each starting an independent compute).

    Teeth: the heavy read is a COUNTING spy. Without the fix the waiter recomputes and the count reaches 2;
    with it the waiter is served the owner's honest degraded payload and the count stays at 1. The ordering
    assertion below proves the waiter really was a waiter (it entered before the owner degraded, so the
    top-of-function cooldown check could not have short-circuited it)."""
    import time

    import app.engine.research as research

    cfg = load_config()
    calls = {"n": 0}
    owner_may_fail = threading.Event()
    stamps: dict = {}

    def _counting_boom(*_a, **_k):
        calls["n"] += 1
        if calls["n"] == 1:
            owner_may_fail.wait(timeout=BOUNDED_TIMEOUT_S)
            stamps["owner_raised"] = time.monotonic()
        raise MemoryError("simulated memory pressure (iter-50 audit B1 probe)")

    owner_result: dict = {}
    waiter_result: dict = {}

    def _owner_call():
        with Session(lab_engine) as session:
            owner_result["payload"] = research.factor_lab_all_cached(session, cfg)

    def _waiter_call():
        stamps["waiter_entered"] = time.monotonic()
        with Session(lab_engine) as session:
            waiter_result["payload"] = research.factor_lab_all_cached(session, cfg)

    real = research._all_factor_observations_by_horizon
    research._all_factor_observations_by_horizon = _counting_boom
    try:
        owner_thread = threading.Thread(target=_owner_call)
        waiter_thread = threading.Thread(target=_waiter_call)
        owner_thread.start()
        # the owner is parked inside the (spied) heavy read, holding the in-flight slot
        deadline = time.monotonic() + BOUNDED_TIMEOUT_S
        while calls["n"] == 0 and time.monotonic() < deadline:
            time.sleep(0.01)
        assert calls["n"] == 1, "owner never entered the compute — the probe never armed"
        waiter_thread.start()
        time.sleep(0.5)  # let the waiter register as a non-owner before the owner degrades
        owner_may_fail.set()
        owner_thread.join(timeout=BOUNDED_TIMEOUT_S)
        waiter_thread.join(timeout=BOUNDED_TIMEOUT_S)
    finally:
        research._all_factor_observations_by_horizon = real
        with research._FACTOR_LAB_ALL_LOCK:
            research._FACTOR_LAB_ALL_DEGRADED.clear()

    assert not owner_thread.is_alive() and not waiter_thread.is_alive(), "a caller hung"
    assert stamps.get("waiter_entered") is not None and stamps.get("owner_raised") is not None
    assert stamps["waiter_entered"] < stamps["owner_raised"], (
        "the waiter entered AFTER the owner had already degraded — it was served by the top-of-function "
        "cooldown check, so this run never exercised the waiter path (vacuous)"
    )
    assert owner_result["payload"]["factors_status"] == "unavailable", "the owner must degrade honestly"
    assert waiter_result.get("payload", {}).get("factors_status") == "unavailable", (
        "the waiter must be served the owner's honest degraded payload, not an error and not a stale hit"
    )
    assert calls["n"] == 1, (
        f"the already-waiting caller started a SECOND full-scale compute in a memory-exhausted process "
        f"(compute attempts: {calls['n']}) — the cooldown must be re-checked after the single-flight wait"
    )


# ==================================================================================================
# 6. iter-31 AUDIT — the two proofs the shipped suite was missing:
#    (a) TC-6 as the phase spec actually words it ("observes the peak resident size of the RETURNED pools
#        structure and asserts it is bounded — proven against the real run count, not a fixture-sized
#        width"). The shipped `test_shipped_factor_pool_max_observations_actually_covers_the_live_basis`
#        only range-checks a config INTEGER; it never looks at the returned structure at all, so a revert
#        of the compact encoding would leave it green.
#    (b) The AG-8 disclosure line must actually reach `logs/backend.log` in the scenario `config.yaml`'s
#        comment promises to pre-announce — a data-scale widening whose build dies part-way.
# ==================================================================================================

# The live basis measured 2026-07-29 (dev handoff "Live verification" + `config.yaml`'s
# `factor_pool_max_observations` comment): 781,417 ScannerResults with a realized return at >= 1 horizon,
# and these per-horizon pool row counts. The projection below is expressed in THESE numbers, never in the
# fixture's own width — the iter-29 shipped-vs-fixture lesson.
_LIVE_CORE_RECORDS = 781_417
_LIVE_POOL_ROWS_BY_HORIZON = (804_372, 802_156, 799_381, 793_837, 771_629)
# The returned structure is ONE resident object among many (SQLAlchemy identity map, the per-(factor,
# horizon) `obs`/`sorted` lists `compute_factor_lab_all` builds on top of it, the JSON payload, the boot
# warm-up's own retained state). Requiring it to fit inside this fraction of the process's whole
# `ulimit -v` keeps the rest of that budget intact; the pre-fix representation is what blew it.
_POOL_STRUCTURE_CAP_FRACTION = 0.35
# The compact encoding must be a MATERIAL reduction over the pre-fix `{5-key dict per horizon-observation}`
# shape, not a cosmetic one — a revert (or re-inlining identity into the per-horizon rows) must fail here.
_MIN_REDUCTION_VS_PRE_FIX = 1.5


def _deep_size(obj) -> int:
    """Resident bytes of an object graph: every container AND the scalars it references, deduped BY IDENTITY
    (so a shared `values` tuple, an interned ticker, or a cached small int is counted ONCE — exactly how the
    process holds them). Deterministic: no clock, no GC timing, no tracemalloc sampling.

    ops-hardening iter-50 AUDIT FIX (finding B3): the walker now descends into `__slots__` objects too.
    Without this it would stop at `sys.getsizeof(<_FactorCoreRecords instance>)` — a few dozen bytes of
    object header, none of the buffers it points at — and every projection assertion built on it would pass
    VACUOUSLY for any structure whose payload hangs off slots. `array.array` / `bytearray` report their whole
    buffer through `sys.getsizeof`, so descending one level into the slots charges every byte the process
    actually holds."""
    seen: set[int] = set()
    stack = [obj]
    total = 0
    while stack:
        o = stack.pop()
        if id(o) in seen:
            continue
        seen.add(id(o))
        total += sys.getsizeof(o)
        if isinstance(o, dict):
            stack.extend(o.keys())
            stack.extend(o.values())
        elif isinstance(o, (list, tuple, set, frozenset)):
            stack.extend(o)
        else:
            for cls in type(o).__mro__:
                for slot in getattr(cls, "__slots__", ()):
                    try:
                        stack.append(getattr(o, slot))
                    except AttributeError:
                        pass
    return total


def test_returned_pool_structure_projected_to_the_live_basis_stays_under_the_memory_cap(lab_engine):
    """iter-31 TC-6 (audit): measure the ACTUAL resident cost of the structure
    `_all_factor_observations_by_horizon` RETURNS, per core record and per pool row, then project those
    measured per-item costs onto the REAL live basis (781,417 core records / 3,971,375 pool rows measured
    2026-07-29) and assert the projection fits inside a stated fraction of `server.memory_cap_mb` — the
    `ulimit -v` the crash was hitting. Also rebuilds the PRE-FIX per-observation shape from the SAME data
    and asserts the shipped encoding is a material reduction over it, so reverting the redesign (or
    re-inlining run_id/ticker/values into the per-horizon rows) fails this test rather than passing a
    config-integer range check.

    Conservative by construction: the fixture charges one distinct ticker string to nearly every core
    record, while the live basis shares ~591 tickers across 781,417 records — so the projected per-core cost
    OVERSTATES the live one."""
    cfg = load_config()
    factors = list(cfg.research.factor_lab.factors)
    horizons = list(cfg.walk_forward.horizons)
    with Session(lab_engine) as session:
        core_records, pools = _all_factor_observations_by_horizon(session, factors, horizons, None, cfg=cfg)

    pool_rows = sum(len(p) for p in pools.values())
    assert core_records and pool_rows, "fixture produced no observations — the measurement would be vacuous"

    per_core = _deep_size(core_records) / len(core_records)
    per_pool_row = _deep_size(pools) / pool_rows

    # the pre-fix shape, rebuilt from the SAME returned data: one 5-key dict per horizon-observation, each
    # inlining run_id/ticker on top of a `values` dict shared across that result's horizons.
    old_values_by_core = [{f.key: v for f, v in zip(factors, values)} for _rid, _tk, values in core_records]
    old_pools = {
        h: [
            {
                "run_id": core_records[i][0], "ticker": core_records[i][1], "return": ret,
                "max_drawdown": mdd, "values": old_values_by_core[i],
            }
            for (i, ret, mdd) in pool
        ]
        for h, pool in pools.items()
    }
    old_per_pool_row = _deep_size(old_pools) / pool_rows
    old_per_core = _deep_size(old_values_by_core) / len(old_values_by_core)

    live_pool_rows = sum(_LIVE_POOL_ROWS_BY_HORIZON)
    to_mb = lambda b: b / (1024 * 1024)  # noqa: E731
    projected_mb = to_mb(per_core * _LIVE_CORE_RECORDS + per_pool_row * live_pool_rows)
    pre_fix_projected_mb = to_mb(old_per_core * _LIVE_CORE_RECORDS + old_per_pool_row * live_pool_rows)

    cap_mb = cfg.server.memory_cap_mb
    budget_mb = cap_mb * _POOL_STRUCTURE_CAP_FRACTION
    assert projected_mb <= budget_mb, (
        f"the returned (core_records, pools) structure projects to {projected_mb:.0f} MB at the live basis "
        f"({_LIVE_CORE_RECORDS} core records, {live_pool_rows} pool rows) — above the "
        f"{_POOL_STRUCTURE_CAP_FRACTION:.0%} share ({budget_mb:.0f} MB) of server.memory_cap_mb={cap_mb} MB "
        f"this one structure may occupy"
    )
    assert projected_mb * _MIN_REDUCTION_VS_PRE_FIX <= pre_fix_projected_mb, (
        f"the shipped encoding projects to {projected_mb:.0f} MB vs the pre-fix shape's "
        f"{pre_fix_projected_mb:.0f} MB — less than the required {_MIN_REDUCTION_VS_PRE_FIX}x reduction. "
        f"The iter-31 return-value redesign has been reverted or diluted (identity re-inlined into the "
        f"per-horizon rows?)"
    )


# ops-hardening iter-50 AUDIT FIX (finding B3). The projection test above guards the iter-31 redesign
# against a revert to the PRE-iter-31 dict shape — but reverting only iter-50's columnar encoding back to
# iter-31's boxed tuples still clears its 1.5x floor comfortably, so it has no teeth on THIS fix. These
# floors pin the columnar encoding specifically, measured against the iter-31 tuple encoding rebuilt from
# the SAME returned data (so any divergence can only come from the encoding itself).
#
# Both are deliberately well BELOW the measured margins because this fixture understates the win: with 20
# core records and 80 pool rows, the fixed ~64-byte header of each `array`/`bytearray` is amortised over
# almost nothing, while at the live basis (781,417 core records / 3,971,375 pool rows) it vanishes and the
# per-pool-row cost approaches its raw 8+8+1+8+1 = 26 bytes against the tuple encoding's ~128. Reverting to
# the tuple encoding scores exactly 1.0x on both and fails here.
_MIN_REDUCTION_VS_ITER31_TOTAL = 1.35    # measured on this fixture: ~1.67x
_MIN_REDUCTION_VS_ITER31_POOL_ROW = 1.6  # measured on this fixture: ~2.03x


def test_returned_pool_structure_is_columnar_not_boxed_python_objects(lab_engine):
    """iter-50 audit B3 — the accumulators `_all_factor_observations_by_horizon` RETURNS must be columnar
    fixed-width buffers, not one boxed Python object per row.

    WHY THIS TEST EXISTS: iter-50 shipped believing this function was "already bounded … unaffected by this
    defect" (its own phase spec's carve-out). The live evidence said otherwise — five real, un-injected
    `MemoryError`s on 2026-08-05 (23:28:44 / 23:37:53 / 23:38:25 / 23:42:07 / 23:44:52) carry the identical
    traceback ending at `pools[h].append(...)` in THIS function, and none at the per-(factor,horizon)
    transient the iteration actually bounded. "Chunked source reads" bounded the QUERY side only; the
    RETURN VALUE was O(observations) in boxed Python objects and stayed resident for the whole call.

    Two independent teeth: a structural assertion (the buffers really are `array`/`bytearray`, so an
    encoding that merely renames the tuples cannot pass) and a measured one (the resident cost per pool row
    and the whole-structure projection must both beat the iter-31 tuple encoding by a stated factor)."""
    from array import array as _array

    cfg = load_config()
    factors = list(cfg.research.factor_lab.factors)
    horizons = list(cfg.walk_forward.horizons)
    with Session(lab_engine) as session:
        core_records, pools = _all_factor_observations_by_horizon(session, factors, horizons, None, cfg=cfg)

    pool_rows = sum(len(p) for p in pools.values())
    assert core_records and pool_rows, "fixture produced no observations — the measurement would be vacuous"

    # --- structural: fixed-width buffers, not per-row Python objects ------------------------------------
    assert isinstance(core_records.run_ids, _array), "core-record run ids must be a fixed-width array"
    assert all(isinstance(c, _array) for c in core_records.value_cols), "factor values must be array columns"
    assert all(isinstance(m, bytearray) for m in core_records.value_present), "null masks must be bytearrays"
    for h, pool in pools.items():
        assert isinstance(pool.core_idx, _array), f"horizon {h}: pool core_idx must be a fixed-width array"
        assert isinstance(pool.returns, _array), f"horizon {h}: pool returns must be a fixed-width array"
        assert isinstance(pool.max_drawdowns, _array), f"horizon {h}: pool drawdowns must be an array"

    # --- measured: beat the iter-31 boxed-tuple encoding rebuilt from the SAME data ---------------------
    iter31_core = [(cr[0], cr[1], cr[2]) for cr in core_records]
    iter31_pools = {h: [(i, ret, mdd) for (i, ret, mdd) in pool] for h, pool in pools.items()}

    per_core = _deep_size(core_records) / len(core_records)
    per_pool_row = _deep_size(pools) / pool_rows
    iter31_per_core = _deep_size(iter31_core) / len(iter31_core)
    iter31_per_pool_row = _deep_size(iter31_pools) / pool_rows

    assert per_pool_row * _MIN_REDUCTION_VS_ITER31_POOL_ROW <= iter31_per_pool_row, (
        f"a pool row costs {per_pool_row:.1f} B columnar vs {iter31_per_pool_row:.1f} B as an iter-31 boxed "
        f"tuple — less than the required {_MIN_REDUCTION_VS_ITER31_POOL_ROW}x reduction at the very "
        f"`pools[h].append` site all five live MemoryError tracebacks land on"
    )

    live_pool_rows = sum(_LIVE_POOL_ROWS_BY_HORIZON)
    projected = per_core * _LIVE_CORE_RECORDS + per_pool_row * live_pool_rows
    iter31_projected = iter31_per_core * _LIVE_CORE_RECORDS + iter31_per_pool_row * live_pool_rows
    assert projected * _MIN_REDUCTION_VS_ITER31_TOTAL <= iter31_projected, (
        f"the columnar structure projects to {projected / (1024 * 1024):.0f} MB at the live basis vs the "
        f"iter-31 tuple encoding's {iter31_projected / (1024 * 1024):.0f} MB — less than the required "
        f"{_MIN_REDUCTION_VS_ITER31_TOTAL}x reduction. iter-50's audit-B3 columnar encoding has been "
        f"reverted or diluted (boxed per-row objects re-introduced?)"
    )


def test_columnar_accumulators_carry_null_and_value_exactly(lab_engine):
    """iter-50 audit B3 — the columnar encoding stores `None` through a companion presence mask, never a
    0.0 or NaN sentinel. Teeth: the catalog's unpopulated factors are genuinely NULL in this fixture, so an
    encoding that conflated NULL with 0.0 would turn an EXCLUDED factor-NULL observation into a real 0.0
    observation and silently change every decile it lands in (AG-3)."""
    cfg = load_config()
    factors = list(cfg.research.factor_lab.factors)
    horizons = list(cfg.walk_forward.horizons)
    with Session(lab_engine) as session:
        core_records, pools = _all_factor_observations_by_horizon(session, factors, horizons, None, cfg=cfg)

    # at least one factor column is entirely NULL in this fixture (the catalog's volatility columns) and at
    # least one is populated — otherwise the null-carrying assertion below would be vacuous.
    null_cols = [j for j in range(len(factors)) if not any(core_records.value_present[j])]
    populated_cols = [j for j in range(len(factors)) if all(core_records.value_present[j])]
    assert null_cols and populated_cols, "fixture must mix NULL and populated factor columns"
    for j in null_cols:
        for i in range(len(core_records)):
            assert core_records.factor_value(i, j) is None, (
                f"factor column {j} is NULL for every record but reads back "
                f"{core_records.factor_value(i, j)!r} — a NULL was conflated with a value"
            )

    # `max_drawdown` is nullable per horizon: NO_MDD_HORIZON's FRs carry None, the populated ones carry a
    # real negative figure. Both must round-trip exactly.
    assert all(pools[NO_MDD_HORIZON].max_drawdown(k) is None for k in range(len(pools[NO_MDD_HORIZON]))), (
        "horizon with no stored max_drawdown must read back None, never 0.0"
    )
    populated = pools[POPULATED_HORIZONS[0]]
    assert len(populated) > 0 and all(
        populated.max_drawdown(k) is not None and populated.max_drawdown(k) < 0
        for k in range(len(populated))
    ), "a populated horizon's stored negative max_drawdowns must round-trip exactly"


def test_factor_pool_cap_warning_lands_even_when_the_sweep_dies_part_way(lab_engine, caplog):
    """iter-31 (audit fix): `config.yaml` promises the ceiling turns a future data-scale widening into "an
    observable log line in logs/backend.log, not another opaque crash". That promise is only true if the
    check runs INSIDE the run-chunk sweep: a widening big enough to exhaust memory raises MID-BUILD, so an
    after-the-loop check would never execute on the very crash it disclaims. Here the second run-chunk's
    slice read raises MemoryError (the real frame's own failure mode); the WARNING for the first chunk's
    overflow must ALREADY be in the log when it propagates. Teeth: with the check after the loop, caplog is
    empty and this fails."""
    import app.engine.research as research

    base = load_config()
    cfg = base.model_copy(update={"research": base.research.model_copy(update={
        "read_batch_size": 2,
        "factor_join_run_chunk": 1,   # 1 run per slice over the fixture's 2 runs -> 2 chunks
        "factor_pool_max_observations": 1,  # every populated horizon overflows on the FIRST chunk
    })})
    factors = list(cfg.research.factor_lab.factors)
    horizons = list(cfg.walk_forward.horizons)

    real_slice_map = research._all_fr_slice_map
    calls = {"n": 0}

    def _dies_on_the_second_chunk(session, hs, slice_run_ids, batch):
        calls["n"] += 1
        if calls["n"] > 1:
            raise MemoryError("simulated data-scale widening exhausts memory mid-sweep")
        return real_slice_map(session, hs, slice_run_ids, batch)

    research._all_fr_slice_map = _dies_on_the_second_chunk
    try:
        with caplog.at_level("WARNING", logger="trendora.research"):
            with Session(lab_engine) as session:
                with pytest.raises(MemoryError):
                    research._all_factor_observations_by_horizon(
                        session, factors, horizons, None, cfg=cfg
                    )
    finally:
        research._all_fr_slice_map = real_slice_map

    assert calls["n"] == 2, "the fixture did not produce a second run-chunk — the scenario is vacuous"
    assert "factor_pool_max_observations exceeded" in caplog.text, (
        "the AG-8 disclosure WARNING never reached the log before the sweep died — the ceiling check must "
        "run inside the run-chunk loop, not after it (config.yaml's own documented promise)"
    )
    # one line per overflowing horizon, never a per-chunk storm.
    assert caplog.text.count("factor_pool_max_observations exceeded") <= len(horizons), (
        "the disclosure warning is repeating per chunk — it must be emitted once per horizon"
    )


# ==================================================================================================
# 12. iter-50 audit B4 — AG-8 data-shape tolerance of the columnar encoding
#
# The B3 columnar accumulators store factor values into `array("d")`, which accepts ONLY a real number.
# A component factor's value is `record_json[<block>]["components"][i]["raw"]` — FREE-FORM JSON — so a
# record shape that writes `"raw": "3.5"` (a string) rather than `3.5` used to be served fine (the sole
# consumer coerced with `float(...)` downstream) and, after the columnar rewrite, raised `TypeError` out
# of `_all_factor_observations_by_horizon`, where the only handlers on the request path were
# `except MemoryError` — so it 500'd the WHOLE `?all=true` response. AG-8 forbids exactly that
# ("must never crash an existing page ... never a blank application-error page").
# ==================================================================================================
def _string_raw_engine(tmp_path, *, raw_for):
    """The SAME shape as `lab_engine` but with each result's `leadership.components.rs_spy_3m.raw` produced
    by `raw_for(numeric_value)` — so a caller can build the numeric-raw basis and a string-raw (or
    non-numeric-raw) basis that are otherwise identical row for row."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    engine = make_engine(f"sqlite:///{tmp_path / 'lab_all_shape.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        r1 = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        for i in range(1, 13):
            session.add(ScannerResult(
                run_id=r1.id, ticker=f"A{i:02d}", name=f"A{i:02d}", sector="Technology",
                leadership_score=float(i * 5), leadership_bucket="C",
                entry_quality_score=float(100 - i * 3), entry_quality_bucket="C",
                risk_score=float(i * 4), risk_bucket="C",
                setup_status="Breakout-watch", rank=i,
                record_json=json.dumps({
                    "leadership": {"components": [
                        {"name": "rs_spy_3m", "raw": raw_for(float(i) / 10.0), "available": True},
                    ]},
                    "risk": {"components": [
                        {"name": "atr_pct", "raw": float(i) / 100.0, "available": True},
                    ]},
                }),
            ))
            for h in POPULATED_HORIZONS:
                _add_fr(session, r1.id, f"A{i:02d}", ret=(i - 6) / 100.0 * h, horizon=h, mdd=-(i / 200.0))
        session.commit()
    return engine


def _rs_spy_3m_entry(payload: dict) -> dict:
    return next(e for e in payload["factors_table"] if e["key"] == "rs_spy_3m")


def test_string_typed_component_raw_is_served_identically_to_a_numeric_raw(tmp_path):
    """iter-50 audit B4 — a `record_json` component whose `raw` is the STRING `"0.7"` must produce the
    byte-identical served figures to the same value written as the number `0.7`, exactly as the
    pre-columnar path did (it stored the raw object and coerced with `float(...)` at the point of use).

    Teeth: without the coercion at the columnar `append` site this does not merely differ — it raises
    `TypeError: must be real number, not str` out of `_all_factor_observations_by_horizon`, which no
    handler on the request path catches, so `GET /api/research/factor-lab?all=true` returns 500 for
    EVERY viewer (AG-8's "never a blank application-error page")."""
    numeric = _string_raw_engine(tmp_path / "num", raw_for=lambda v: v)
    stringy = _string_raw_engine(tmp_path / "str", raw_for=lambda v: str(v))
    cfg = load_config()

    with Session(numeric) as session:
        numeric_payload = compute_factor_lab_all(session, cfg, as_of=None)
    with Session(stringy) as session:
        string_payload = compute_factor_lab_all(session, cfg, as_of=None)

    numeric_entry, string_entry = _rs_spy_3m_entry(numeric_payload), _rs_spy_3m_entry(string_payload)
    assert numeric_entry["n_total"] > 0, "fixture produced no rs_spy_3m observations — the proof is vacuous"
    assert _bytes(string_entry) == _bytes(numeric_entry), (
        "a string-typed component `raw` must serve byte-identically to the same numeric value — the "
        "columnar encoding must not narrow the data shapes this endpoint tolerates (AG-8)"
    )
    # and nothing was quietly dropped: every observation still counted.
    assert all(
        bh["n_total"] == next(n["n_total"] for n in numeric_entry["by_horizon"] if n["horizon"] == bh["horizon"])
        for bh in string_entry["by_horizon"]
    ), "string-typed raws changed an observation count — values must be coerced, never excluded"


@pytest.mark.parametrize("bad_raw", ["n/a", [0.7], {"value": 0.7}])
def test_non_numeric_component_raw_is_excluded_as_factor_null_never_a_500(tmp_path, caplog, bad_raw):
    """iter-50 audit B4 — a component `raw` that is not a real number AT ALL is excluded exactly like a
    factor-NULL observation (`_extract_factor_value`'s own "never fabricated" convention), disclosed by an
    AG-8 WARNING, and the response still renders every OTHER factor. It must never fabricate a value and
    must never raise out of the shared pool builder.

    Teeth: the OTHER catalog factors in the same fixture stay fully populated, so a handler that blanked
    the whole response (or a `float()` that fabricated 0.0) fails here."""
    engine = _string_raw_engine(tmp_path, raw_for=lambda v: bad_raw)
    cfg = load_config()

    with caplog.at_level("WARNING", logger="trendora.research"):
        with Session(engine) as session:
            payload = compute_factor_lab_all(session, cfg, as_of=None)

    entry = _rs_spy_3m_entry(payload)
    assert entry["n_total"] == 0 and entry["rank_ic"]["n"] == 0, (
        f"a non-numeric raw ({bad_raw!r}) must be EXCLUDED as a factor-NULL observation, never coerced "
        f"into a fabricated number — got n_total={entry['n_total']}"
    )
    assert all(d["mean_return"] is None for d in entry["by_horizon"][0]["deciles"]), (
        "an all-excluded factor must render honest NA deciles, never fabricated figures (AG-3)"
    )
    leadership = next(e for e in payload["factors_table"] if e["key"] == "leadership_score")
    assert leadership["n_total"] > 0, (
        "one factor's unusable stored shape blanked the OTHER factors' entries — AG-8 requires the "
        "contained degrade, not a whole-response failure"
    )
    assert "were EXCLUDED as factor-NULL observations" in caplog.text, (
        "the AG-8 data-shape exclusion must be disclosed in the log, never silent"
    )


def test_one_entry_s_non_memory_failure_degrades_only_that_entry(lab_engine, monkeypatch, caplog):
    """iter-50 audit B4 (second half) — `compute_factor_lab_all`'s per-(factor,horizon) loop carried ONLY
    an `except MemoryError`, so any OTHER exception from ONE entry still propagated and 500'd the whole
    `?all=true` response for all 11 factors. `evidence.py`'s per-claim convention — the precedent this loop
    already cites for its MemoryError catch — pairs that catch with a broader one, degrading the single
    failing unit to an honest `status: "unavailable"` and continuing.

    Teeth: the fault fires on exactly ONE `_deciles` call, so a handler that blanked the whole response
    (or no handler at all — the pre-fix behavior, which raises straight out of this function) fails both
    the "one entry degraded" and the "every other entry still real" assertions below."""
    import app.engine.research as research

    cfg = load_config()
    real_deciles = research._deciles
    calls = {"n": 0}
    fault_on_call = 3  # a specific (factor, horizon) entry, deterministically

    def _boom_on_one_entry(ordered, n_deciles, min_sample):
        calls["n"] += 1
        if calls["n"] == fault_on_call:
            raise RuntimeError("simulated non-memory failure inside one (factor,horizon) entry")
        return real_deciles(ordered, n_deciles, min_sample)

    monkeypatch.setattr(research, "_deciles", _boom_on_one_entry)
    with caplog.at_level("ERROR", logger="trendora.research"):
        with Session(lab_engine) as session:
            payload = compute_factor_lab_all(session, cfg, as_of=None)

    degraded = [
        (e["key"], bh["horizon"]) for e in payload["factors_table"]
        for bh in e["by_horizon"] if bh.get("status") == "unavailable"
    ]
    assert calls["n"] > fault_on_call, (
        "the loop stopped at the injected failure instead of continuing to the next entry — "
        "isolate-and-continue means CONTINUE"
    )
    assert len(degraded) == 1, (
        f"exactly the faulted (factor,horizon) entry must degrade; got {degraded!r}"
    )
    assert any(
        bh.get("status") != "unavailable" and bh["n_total"] > 0
        for e in payload["factors_table"] for bh in e["by_horizon"]
    ), "no entry survived — the isolation is not contained, which is the failure this test forbids"
    assert "isolate-and-continue" in caplog.text, (
        "the isolated failure must be logged, never swallowed silently"
    )
