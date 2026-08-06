"""iter-47 (J-105) — the heavy-research forward-return read path is bounded/streamed (column-projected
`yield_per`) instead of materializing the whole `forward_returns` table as ORM rows. These tests pin the
NON-NEGOTIABLE contract of that refactor: **every served figure is byte-identical** to the prior
per-observation aggregation, and the streaming is **chunk-independent** (the batch size changes peak
memory, NEVER a value or an ordering).

The proofs drive the REAL builders/endpoints (no hand-rolled stand-in — iter-15 lesson), on a
DISCRIMINATING hand-built fixture where the iter-47 reorder (stream the subject-matching ScannerResults
first, then scan FR pruned to the needed runs) is LOAD-BEARING:

  - subject-matching results WITH forward returns at several horizons,
  - subject-matching results with FRs at ONE horizon only (the test_iter20 discriminator shape),
  - a subject-matching run with ZERO forward returns (must contribute nothing, never crash),
  - NON-subject symbols that DO have forward returns (must NOT leak into a subject cohort),
  - a run with forward returns but no subject match,
  - distinct return / mae / mfe / max_drawdown / sector / setup_status / pattern values per row,
  - mixed regimes across runs.

Chunk-independence is proven by recomputing each builder under `research.read_batch_size = 1` (one row per
streamed batch) and under a huge batch, asserting BOTH equal the real-config output — `json.dumps(...,
sort_keys=True)` byte-identity, the repo convention (cf. test_market_phase.py / test_research.py).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlmodel import Session, select

import app.engine.research as research_module
from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import data_manager
from app.engine.research import (
    RESEARCH_CAVEAT,
    SURVIVORSHIP_BIAS_LABEL,
    VIEW_EPISODES,
    VIEW_POOLED,
    _all_factor_observations_by_horizon,
    _combination_observations,
    _deciles,
    _event_study_members,
    _event_study_members_by_horizon,
    _factor_observations,
    _rank_ic,
    _regime_setup_pattern_observations,
    _severity_velocity_observation_set,
    compute_event_study,
    compute_factor_combination,
    compute_factor_lab,
    compute_factor_lab_all,
    factor_catalog,
    factor_lab_all_cached,
)
from app.models import EventStudyCache, ForwardReturn, ScannerResult, ScannerRun

H = 20


# --------------------------------------------------------------------------------------------------
# helpers (mirror the test_iter20_research_cluster builders so the rows are exact by construction)
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


def _add_result(
    session, run_id, ticker, rank, *, setup, sector, lead=50.0, eqs=50.0, risk=50.0,
    is_vcp=False, is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
):
    session.add(ScannerResult(
        run_id=run_id, ticker=ticker, name=ticker, sector=sector,
        leadership_score=lead, leadership_bucket="C",
        entry_quality_score=eqs, entry_quality_bucket="C",
        risk_score=risk, risk_bucket="C",
        setup_status=setup, rank=rank, record_json=json.dumps({"ticker": ticker, "name": ticker}),
        is_vcp=is_vcp, is_pullback_to_rising_dma=is_pullback_to_rising_dma,
        is_flat_base_breakout=is_flat_base_breakout,
    ))


def _add_fr(session, run_id, symbol, ret, *, horizon=H, mae, mfe, mdd):
    session.add(ForwardReturn(
        run_id=run_id, symbol=symbol, horizon=horizon, asof_date=date(2025, 1, 1),
        entry_close=100.0, measured_date=date(2025, 2, 1),
        realized_return=ret, mae=mae, mfe=mfe, max_drawdown=mdd,
    ))


@pytest.fixture()
def prune_engine(tmp_path):
    """A DISCRIMINATING dataset for the iter-47 reorder: subject-matching + non-matching results, a
    subject-matching run with ZERO FRs, non-subject symbols WITH FRs (must not leak), FRs at multiple
    horizons for some pairs and one horizon for others, mixed regimes, distinct value fields."""
    engine = make_engine(f"sqlite:///{tmp_path / 'prune.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        r1 = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        r2 = _add_run(session, date(2025, 2, 10), regime_label="Risk-off")
        r3 = _add_run(session, date(2025, 3, 10), regime_label="Risk-on")  # subject match, ZERO FRs
        session.flush()

        # run-1: VCP names (subject match) with FRs at 1/5/20; a non-VCP name; a non-subject symbol w/ FR.
        _add_result(session, r1.id, "AA", 1, setup="Actionable", sector="Technology",
                    lead=80.0, eqs=70.0, risk=20.0, is_vcp=True)
        _add_result(session, r1.id, "BB", 2, setup="Breakout-watch", sector="Energy",
                    lead=60.0, eqs=55.0, risk=40.0, is_vcp=True, is_pullback_to_rising_dma=True)
        _add_result(session, r1.id, "CC", 3, setup="Actionable", sector="Financials",
                    lead=40.0, eqs=45.0, risk=60.0, is_vcp=False)  # NOT a vcp subject member
        _add_result(session, r1.id, "ZZ", 4, setup="Breakout-watch", sector="Health",
                    lead=30.0, eqs=35.0, risk=70.0, is_vcp=False)  # non-subject symbol but HAS an FR
        for tkr, base in (("AA", 0.10), ("BB", 0.22), ("CC", -0.07), ("ZZ", 0.05)):
            for h, sc in ((1, 0.2), (5, 0.5), (20, 1.0)):
                _add_fr(session, r1.id, tkr, base * sc, horizon=h,
                        mae=-0.05 * sc, mfe=0.15 * sc, mdd=-0.08 * sc)

        # run-2: a VCP name with an FR at horizon 20 ONLY (the test_iter20 discriminator shape) + a
        # non-subject name with an FR; different regime.
        _add_result(session, r2.id, "DD", 1, setup="Actionable", sector="Technology",
                    lead=75.0, eqs=65.0, risk=25.0, is_vcp=True, is_flat_base_breakout=True)
        _add_result(session, r2.id, "EE", 2, setup="Breakout-watch", sector="Energy",
                    lead=50.0, eqs=50.0, risk=50.0, is_vcp=False)
        _add_fr(session, r2.id, "DD", 0.30, horizon=20, mae=-0.09, mfe=0.40, mdd=-0.11)
        _add_fr(session, r2.id, "EE", 0.04, horizon=20, mae=-0.02, mfe=0.06, mdd=-0.03)

        # run-3: a subject-matching result with ZERO forward returns (must contribute nothing, no crash).
        _add_result(session, r3.id, "FF", 1, setup="Actionable", sector="Technology",
                    lead=90.0, eqs=80.0, risk=10.0, is_vcp=True)
        session.commit()
    return engine


def _cfg_batch(batch: int, run_chunk: int | None = None):
    """The real config with `research.read_batch_size` overridden to `batch` (chunk-size probe), and
    `research.factor_join_run_chunk` (the iter-29-audit RUN-COUNT accumulator width — a DIFFERENT unit)
    overridden to `run_chunk`, defaulting to the same value so every existing probe keeps varying BOTH the
    `yield_per` row batch and the join-accumulator chunking exactly as it did before the two knobs split."""
    cfg = load_config()
    return cfg.model_copy(update={"research": cfg.research.model_copy(update={
        "read_batch_size": batch,
        "factor_join_run_chunk": batch if run_chunk is None else run_chunk,
    })})


def _eq(a, b) -> bool:
    return json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


# --------------------------------------------------------------------------------------------------
# 1. _event_study_members_by_horizon == per-horizon loop, on the discriminating reorder fixture
# --------------------------------------------------------------------------------------------------
def test_event_study_by_horizon_matches_per_horizon_loop_on_prune_fixture(prune_engine):
    """The batched/streamed `_event_study_members_by_horizon` is byte-identical per horizon to calling
    the streamed `_event_study_members` in a loop — on a fixture where the reorder + FR-prune is
    load-bearing (run-2 has a member at horizon 20 only; a non-subject symbol has FRs; a subject run has
    zero FRs)."""
    cfg = load_config()
    horizons = list(cfg.walk_forward.horizons)
    subject = {"key": "vcp", "kind": "pattern"}
    with Session(prune_engine) as session:
        batched = _event_study_members_by_horizon(session, subject, horizons)
        for h in horizons:
            per = _event_study_members(session, subject, h)
            assert batched[h] == per, f"horizon {h}: batched != per-horizon loop"
        # the non-subject symbol with FRs (ZZ / EE) MUST NOT leak into a vcp cohort.
        for h in horizons:
            tickers = {m["ticker"] for m in batched[h]}
            assert "ZZ" not in tickers and "EE" not in tickers, f"non-subject leak at horizon {h}"
            assert "CC" not in tickers, f"non-vcp result CC leaked at horizon {h}"
        # the subject run with zero FRs (FF) contributes nothing at every horizon.
        for h in horizons:
            assert "FF" not in {m["ticker"] for m in batched[h]}


# --------------------------------------------------------------------------------------------------
# 2. chunk-independence: read_batch_size = 1 vs huge vs default — byte-identical members
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("subject", [
    {"key": "vcp", "kind": "pattern"},
    {"key": "Actionable", "kind": "setup"},
])
def test_event_study_members_chunk_independent(prune_engine, subject):
    """The streamed `_event_study_members[_by_horizon]` output is identical whether the FR scan streams
    one row per batch or the whole table at once — proving the batch size changes only memory, never a
    value/order. The batch size is threaded via the `cfg` the builder reads."""
    horizons = list(load_config().walk_forward.horizons)
    with Session(prune_engine) as session:
        outputs = [
            _event_study_members_by_horizon(session, subject, horizons, cfg=_cfg_batch(b))
            for b in (1, 7, 1_000_000)
        ]
        assert _eq(outputs[0], outputs[1]) and _eq(outputs[1], outputs[2]), "batch size changed values"
        # the per-horizon builder is likewise chunk-independent.
        per_small = _event_study_members(session, subject, H, cfg=_cfg_batch(1))
        per_big = _event_study_members(session, subject, H, cfg=_cfg_batch(1_000_000))
        assert _eq(per_small, per_big), "per-horizon builder differs by batch"


# --------------------------------------------------------------------------------------------------
# 3. compute_event_study byte-identity: as_of=None / historical, pooled / episodes — chunk-independent
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("view", [VIEW_EPISODES, VIEW_POOLED])
@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_compute_event_study_chunk_independent(prune_engine, view, as_of):
    """The full event-study payload (matrix cells, mean/win-rate/N, every horizon) is byte-identical
    under read_batch_size=1 vs the real config — across all-history / historical as_of and pooled /
    episodes views (the no-lookahead + view legs)."""
    with Session(prune_engine) as session:
        small = compute_event_study(session, "vcp", H, _cfg_batch(1), as_of=as_of, view=view)
        big = compute_event_study(session, "vcp", H, _cfg_batch(1_000_000), as_of=as_of, view=view)
        assert _eq(small, big), f"event-study payload differs by batch (view={view}, as_of={as_of})"


def test_compute_event_study_zero_n_cohort_is_honest_not_crash(prune_engine):
    """A subject with ZERO members (no result carries the flag) returns an honest empty/NA study — never
    a crash, never a fabricated figure — under the streamed read path."""
    with Session(prune_engine) as session:
        # 'flat_base_breakout' matches only DD (1 FR at h=20); choose a subject matched by NO result with an
        # FR by scoping as_of before any snapshot -> zero observations.
        payload = compute_event_study(session, "vcp", H, _cfg_batch(1), as_of=date(2024, 1, 1))
        assert payload["n"] == 0
        for row in payload["by_horizon"]:
            assert row["n"] == 0
            assert row["mean_return"] is None  # honest NA, never a fabricated 0


# --------------------------------------------------------------------------------------------------
# 4. factor-lab + multi-factor combination byte-identity (chunk-independent), as_of legs
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_compute_factor_lab_chunk_independent(prune_engine, as_of):
    with Session(prune_engine) as session:
        small = compute_factor_lab(session, "leadership_score", H, _cfg_batch(1), as_of=as_of)
        big = compute_factor_lab(session, "leadership_score", H, _cfg_batch(1_000_000), as_of=as_of)
        assert _eq(small, big), f"factor-lab payload differs by batch (as_of={as_of})"


@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_compute_factor_combination_chunk_independent(prune_engine, as_of):
    cfg = load_config()
    conditions = [
        {"factor": c.factor, "side": c.side, "quantile": c.quantile}
        for c in cfg.research.factor_lab.combination.default_conditions
    ]
    with Session(prune_engine) as session:
        small = compute_factor_combination(session, conditions, H, _cfg_batch(1), as_of=as_of)
        big = compute_factor_combination(session, conditions, H, _cfg_batch(1_000_000), as_of=as_of)
        assert _eq(small, big), f"factor-combination payload differs by batch (as_of={as_of})"


def test_factor_observations_chunk_independent_and_no_leak(prune_engine):
    """Raw `_factor_observations` / `_combination_observations` lists are identical under batch=1 vs huge
    and exclude any factor-NULL / non-FR observation (the value-verbatim guard)."""
    cfg = load_config()
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
    factors2 = [f for f in cfg.research.factor_lab.factors if f.key in ("leadership_score", "risk_score")]
    with Session(prune_engine) as session:
        for builder, args in (
            (_factor_observations, (factor, H)),
            (_combination_observations, (factors2, H)),
        ):
            small = builder(session, *args, None, cfg=_cfg_batch(1))
            big = builder(session, *args, None, cfg=_cfg_batch(1_000_000))
            assert _eq(small, big), f"{builder.__name__} differs by batch"


# --------------------------------------------------------------------------------------------------
# 5. regime-setup-pattern + severity-velocity observation sets chunk-independent
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("view", [VIEW_EPISODES, VIEW_POOLED])
def test_regime_setup_pattern_observations_chunk_independent(prune_engine, view):
    with Session(prune_engine) as session:
        small = _regime_setup_pattern_observations(session, H, view, _cfg_batch(1))
        big = _regime_setup_pattern_observations(session, H, view, _cfg_batch(1_000_000))
        assert _eq(small, big), f"rsp observation set differs by batch (view={view})"


def test_severity_velocity_observation_set_chunk_independent(prune_engine):
    """The SPY-benchmark severity-velocity observation set (already symbol-bounded) is byte-identical
    under batch=1 vs huge after column-projection."""
    cfg = load_config()
    with Session(prune_engine) as session:
        small = _severity_velocity_observation_set(session, H, _cfg_batch(1))
        big = _severity_velocity_observation_set(session, H, _cfg_batch(1_000_000))
        assert _eq(small, big), "severity-velocity observation set differs by batch"


# ==================================================================================================
# iter-48 (J-105): the ScannerResult-side read in `_factor_observations` (research.py:216) and
# `_combination_observations` (research.py:421) is now ALSO `yield_per`-streamed (the live Factor-Lab
# MemoryError site — Factor Lab is UNCACHED so it recomputes the observation set every request). These
# proofs pin the NON-NEGOTIABLE byte-identity of that ScannerResult-side streaming:
#
#   1. The streamed FULL ORM row (NOT a column projection) keeps `record_json` available, so a COMPONENT
#      factor (which reads `record_json[block]["components"][name]["raw"]`) is byte-identical — a naive
#      narrow projection would drop `record_json` and silently change component-factor figures.
#   2. `.order_by(ScannerResult.id)` reproduces the prior implicit-`.all()` row order, so the observation
#      list (and every downstream decile / rank-IC / by_regime / composite / strict_overlap figure) is
#      byte-identical regardless of the streaming batch size.
#   3. A zero-N cohort stays an honest empty/NA result (never a crash, never a fabricated row).
# ==================================================================================================
def _component_record_json(ticker: str, rs_spy_3m: float, atr_pct: float) -> str:
    """A `record_json` blob carrying the two component factors used in the default combination conditions
    (`leadership.components.rs_spy_3m.raw` and `risk.components.atr_pct.raw`) — the EXACT shape
    `_extract_factor_value` reads for a `component` factor. This is what would be LOST by a narrow column
    projection, so it is the load-bearing payload for the byte-identity-with-record_json proof."""
    return json.dumps({
        "ticker": ticker, "name": ticker,
        "leadership": {"components": [
            {"name": "rs_spy_3m", "raw": rs_spy_3m},
            {"name": "ma_stack", "raw": 0.5},
        ]},
        "risk": {"components": [
            {"name": "atr_pct", "raw": atr_pct},
        ]},
    })


@pytest.fixture()
def component_engine(tmp_path):
    """A fixture whose `record_json` carries REAL component-factor blocks so a `component` factor
    (`rs_spy_3m`, `atr_pct`) produces a non-trivial, non-empty observation pool — the case where dropping
    `record_json` in a narrow projection would silently change figures. Multiple runs/rows across mixed
    regimes + distinct component values + a subject-matching run with zero FRs (zero-N leg)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'component.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        r1 = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        r2 = _add_run(session, date(2025, 2, 10), regime_label="Risk-off")
        r3 = _add_run(session, date(2025, 3, 10), regime_label="Risk-on")  # zero-FR run (zero-N leg)
        session.flush()

        # run-1: three names with distinct rs_spy_3m / atr_pct component values + a column-factor spread.
        rows1 = [
            ("AA", 1, 90.0, 10.0, 0.80, 0.012, 0.10),
            ("BB", 2, 60.0, 40.0, 0.40, 0.030, 0.04),
            ("CC", 3, 30.0, 70.0, 0.10, 0.055, -0.06),
        ]
        for tkr, rank, lead, risk, rs, atr, ret in rows1:
            session.add(ScannerResult(
                run_id=r1.id, ticker=tkr, name=tkr, sector="Technology",
                leadership_score=lead, leadership_bucket="C",
                entry_quality_score=55.0, entry_quality_bucket="C",
                risk_score=risk, risk_bucket="C",
                setup_status="Actionable", rank=rank,
                record_json=_component_record_json(tkr, rs, atr),
            ))
            _add_fr(session, r1.id, tkr, ret, horizon=H, mae=-0.05, mfe=0.15, mdd=-0.08)

        # run-2 (different regime): one name with an FR at horizon 20 only, distinct component values.
        session.add(ScannerResult(
            run_id=r2.id, ticker="DD", name="DD", sector="Energy",
            leadership_score=75.0, leadership_bucket="C",
            entry_quality_score=65.0, entry_quality_bucket="C",
            risk_score=25.0, risk_bucket="C",
            setup_status="Actionable", rank=1,
            record_json=_component_record_json("DD", 0.65, 0.020),
        ))
        _add_fr(session, r2.id, "DD", 0.30, horizon=H, mae=-0.09, mfe=0.40, mdd=-0.11)

        # run-3: a result with ZERO forward returns -> contributes nothing (zero-N leg).
        session.add(ScannerResult(
            run_id=r3.id, ticker="FF", name="FF", sector="Technology",
            leadership_score=88.0, leadership_bucket="C",
            entry_quality_score=80.0, entry_quality_bucket="C",
            risk_score=12.0, risk_bucket="C",
            setup_status="Actionable", rank=1,
            record_json=_component_record_json("FF", 0.95, 0.008),
        ))
        session.commit()
    return engine


def _factor_observations_reference(session, factor, horizon, as_of, cfg):
    """A pre-iter-48 REFERENCE of `_factor_observations` that materializes the ScannerResult side with an
    eager `.all()` (NO `yield_per`, NO `.order_by`), mirroring the exact code the streaming fix replaced.
    The streamed builder must equal this byte-for-byte (this is the regression oracle for the refactor)."""
    from app.engine.research import _extract_factor_value, parse_factor_source
    from sqlmodel import select
    parsed = parse_factor_source(factor.source)
    batch = cfg.research.read_batch_size
    # iter-52 (J-109): the reference ALSO projects/carries the stored max_drawdown so it stays a byte-for-byte
    # oracle of the (now MDD-carrying) streamed `_factor_observations`.
    fr_stmt = select(
        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return, ForwardReturn.max_drawdown
    ).where(ForwardReturn.horizon == horizon)
    if as_of is not None:
        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
            ScannerRun.asof_date <= as_of
        )
    ret_by_run_symbol = {}
    runs_with_fr_set = set()
    for run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
        ret_by_run_symbol[(run_id, symbol)] = (realized_return, max_drawdown)
        runs_with_fr_set.add(run_id)
    runs_with_fr = sorted(runs_with_fr_set)
    run_rows = (
        session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
        if runs_with_fr else []
    )
    regime_by_run = {run.id: run.regime_label for run in run_rows}
    # the EXACT pre-fix read: eager `.all()`, no explicit order_by.
    results = (
        session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()
        if runs_with_fr else []
    )
    observations = []
    for res in results:
        fr = ret_by_run_symbol.get((res.run_id, res.ticker))
        if fr is None:
            continue
        realized, max_drawdown = fr
        value = _extract_factor_value(res, parsed)
        if value is None:
            continue
        observations.append({
            "run_id": res.run_id, "ticker": res.ticker, "factor": float(value), "return": realized,
            "max_drawdown": max_drawdown,
            "regime": regime_by_run.get(res.run_id),
        })
    return observations


@pytest.mark.parametrize("factor_key", ["leadership_score", "rs_spy_3m"])  # column AND component
@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_factor_observations_streamed_equals_eager_all_reference(component_engine, factor_key, as_of):
    """The `yield_per`-streamed `_factor_observations` (full ORM row + `.order_by(id)`) is byte-identical
    to the pre-iter-48 eager `.all()` reference — for a COLUMN factor (`leadership_score`) AND a COMPONENT
    factor (`rs_spy_3m`, read from `record_json`) — proving the stream keeps `record_json` available and
    reproduces the prior row order, across as-of / all-history."""
    cfg = load_config()
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == factor_key)
    with Session(component_engine) as session:
        streamed = _factor_observations(session, factor, H, as_of, cfg=_cfg_batch(1))
        streamed_big = _factor_observations(session, factor, H, as_of, cfg=_cfg_batch(1_000_000))
        reference = _factor_observations_reference(session, factor, H, as_of, cfg)
        assert _eq(streamed, reference), f"streamed != eager .all() reference ({factor_key}, {as_of})"
        assert _eq(streamed, streamed_big), f"batch size changed values ({factor_key}, {as_of})"
        # the component factor MUST actually read non-null values from record_json (not a degenerate
        # all-None / zero-N pool that would make the byte-identity vacuous).
        if factor_key == "rs_spy_3m" and as_of is None:
            assert streamed, "component-factor pool empty — record_json was not read"
            assert all(o["factor"] is not None for o in streamed)


@pytest.mark.parametrize("factor_key", ["leadership_score", "rs_spy_3m"])  # column AND component
@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_compute_factor_lab_chunk_independent_component(component_engine, factor_key, as_of):
    """The full `compute_factor_lab` payload (deciles, rank_ic, by_regime, n_total) is byte-identical under
    batch=1 vs huge — for a COLUMN and a COMPONENT factor — on the component-bearing fixture."""
    with Session(component_engine) as session:
        small = compute_factor_lab(session, factor_key, H, _cfg_batch(1), as_of=as_of)
        big = compute_factor_lab(session, factor_key, H, _cfg_batch(1_000_000), as_of=as_of)
        assert _eq(small, big), f"factor-lab payload differs by batch ({factor_key}, as_of={as_of})"


def test_factor_lab_zero_n_cohort_is_honest_not_crash(component_engine):
    """A factor-lab over an as_of BEFORE any snapshot yields an honest empty/NA payload (n_total 0, every
    decile mean None) — never a crash, never a fabricated row — under the streamed ScannerResult read."""
    with Session(component_engine) as session:
        payload = compute_factor_lab(session, "rs_spy_3m", H, _cfg_batch(1), as_of=date(2024, 1, 1))
        assert payload["n_total"] == 0
        for row in payload["deciles"]:
            assert row["n"] == 0
            assert row["mean_return"] is None  # honest NA, never a fabricated 0
        assert payload["rank_ic"]["value"] is None


@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_combination_observations_streamed_chunk_independent_component(component_engine, as_of):
    """The streamed `_combination_observations` (full ORM row + `.order_by(id)`) is batch-independent on a
    multi-factor set that mixes a COLUMN factor and a COMPONENT (`record_json`) factor — proving the
    factor-combination cold-miss path keeps `record_json` and the prior row order."""
    cfg = load_config()
    # a column factor + a component factor (read from record_json) -> exercises both extract paths.
    factors = [f for f in cfg.research.factor_lab.factors if f.key in ("leadership_score", "rs_spy_3m")]
    with Session(component_engine) as session:
        small = _combination_observations(session, factors, H, as_of, cfg=_cfg_batch(1))
        big = _combination_observations(session, factors, H, as_of, cfg=_cfg_batch(1_000_000))
        assert _eq(small, big), f"_combination_observations differs by batch (as_of={as_of})"
        if as_of is None:
            assert small, "combination pool empty — record_json was not read"
            assert all("rs_spy_3m" in o["values"] for o in small)


@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_compute_factor_combination_chunk_independent_component(component_engine, as_of):
    """The full `compute_factor_combination` payload (composite + strict_overlap + baseline + singles) is
    byte-identical under batch=1 vs huge on the component-bearing fixture (the default config conditions
    reference `rs_spy_3m` + `atr_pct`, both component factors read from `record_json`)."""
    cfg = load_config()
    conditions = [
        {"factor": c.factor, "side": c.side, "quantile": c.quantile}
        for c in cfg.research.factor_lab.combination.default_conditions
    ]
    with Session(component_engine) as session:
        small = compute_factor_combination(session, conditions, H, _cfg_batch(1), as_of=as_of)
        big = compute_factor_combination(session, conditions, H, _cfg_batch(1_000_000), as_of=as_of)
        assert _eq(small, big), f"factor-combination payload differs by batch (as_of={as_of})"


# ==================================================================================================
# iter-52 (J-109): the all-factors ALL-HORIZONS shared pool builder is the OOM-sensitive UNCACHED-cold
# factor-lab read site. It reads `realized_return` AND `max_drawdown` for EVERY horizon in ONE streamed,
# column-projected sweep (NO unbounded `.all()` over `ForwardReturn` / `ScannerResult`). These proofs pin:
#   1. Per-horizon BYTE-IDENTITY: a factor's non-null subset of `pools[h]` (preserving order) EQUALS the
#      streamed `_factor_observations(factor, h)` row-for-row — the property compute_factor_lab_all relies on
#      so each (factor, horizon, decile) figure is byte-identical to the single-horizon view.
#   2. Chunk-independence: the one-sweep all-horizons read is identical under batch=1 vs huge (cold probe).
# ==================================================================================================
@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_all_factor_observations_by_horizon_matches_per_factor_per_horizon(prune_engine, as_of):
    """For EVERY catalog factor and EVERY config horizon, the all-horizons shared pool's non-null subset at
    horizon h (with `max_drawdown` dropped — it rides additively) equals `_factor_observations(factor, h)`
    row-for-row on the discriminating reorder fixture (multi-horizon FRs, a non-subject symbol with FRs, a
    factor-NULL column). Proves the one-sweep all-horizons read is byte-identical per (factor, horizon).
    iter-31: `_all_factor_observations_by_horizon` now returns the compact `(core_records, pools)` shape (a
    return-value memory-representation redesign) — `core_records[core_idx]` is `(run_id, ticker, values)`
    with `values` a TUPLE positioned by `factors` order (never a dict keyed by factor.key)."""
    cfg = load_config()
    factors = list(cfg.research.factor_lab.factors)
    horizons = list(cfg.walk_forward.horizons)
    factor_index = {f.key: i for i, f in enumerate(factors)}
    with Session(prune_engine) as session:
        core_records, pools = _all_factor_observations_by_horizon(session, factors, horizons, as_of, cfg=cfg)
        for factor in factors:
            idx = factor_index[factor.key]
            for h in horizons:
                subset = []
                for core_idx, ret, mdd in pools[h]:
                    run_id, ticker, values = core_records[core_idx]
                    factor_value = values[idx]
                    if factor_value is None:
                        continue
                    subset.append({
                        "run_id": run_id, "ticker": ticker, "factor": float(factor_value),
                        "return": ret, "max_drawdown": mdd, "regime": None,
                    })
                per = _factor_observations(session, factor, h, as_of, cfg=cfg)
                # compare on the shared keys (the all-horizons pool carries no per-obs regime label, which
                # compute_factor_lab_all does not use); assert the factor/return/max_drawdown identity.
                got = [
                    {"run_id": o["run_id"], "ticker": o["ticker"], "factor": o["factor"],
                     "return": o["return"], "max_drawdown": o["max_drawdown"]}
                    for o in subset
                ]
                want = [
                    {"run_id": o["run_id"], "ticker": o["ticker"], "factor": o["factor"],
                     "return": o["return"], "max_drawdown": o["max_drawdown"]}
                    for o in per
                ]
                assert _eq(got, want), f"all-horizons subset != _factor_observations ({factor.key}@{h})"


def _materialize_shared_pools(built) -> dict:
    """iter-50 audit B3: the shared-pool builder now returns COLUMNAR accumulators
    (`_FactorCoreRecords` / `_FactorObsPool`) instead of `list[tuple]`. Expand them through their sequence
    protocol into plain nested lists so the byte-identity comparison below stays a comparison of DATA — a
    raw `json.dumps(..., default=str)` on the objects themselves would compare `repr()`s (memory addresses),
    which is never equal and would silently turn this proof into a tautological failure."""
    core_records, pools = built
    return {
        "core_records": [[run_id, ticker, list(values)] for run_id, ticker, values in core_records],
        "pools": {h: [list(row) for row in pool] for h, pool in pools.items()},
    }


@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_all_factor_observations_by_horizon_chunk_independent(prune_engine, as_of):
    """The all-horizons shared pool read is byte-identical under read_batch_size=1 vs a huge batch — the
    bounded/streamed cold probe (the batch changes only peak memory, never a value/order)."""
    cfg = load_config()
    factors = list(cfg.research.factor_lab.factors)
    horizons = list(cfg.walk_forward.horizons)
    with Session(prune_engine) as session:
        small = _all_factor_observations_by_horizon(session, factors, horizons, as_of, cfg=_cfg_batch(1))
        big = _all_factor_observations_by_horizon(
            session, factors, horizons, as_of, cfg=_cfg_batch(1_000_000)
        )
        small_rows, big_rows = _materialize_shared_pools(small), _materialize_shared_pools(big)
        assert small_rows["core_records"], "fixture produced no observations — the comparison is vacuous"
        assert _eq(small_rows, big_rows), f"all-horizons pool differs by batch (as_of={as_of})"


@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_compute_factor_lab_all_chunk_independent_component(component_engine, as_of):
    """The full all-factors, all-horizons payload (every factor × every horizon decile table, paired MDD) is
    byte-identical under batch=1 vs huge on the component-bearing fixture — proving the cold uncached
    factor-lab-all read keeps `record_json` (component factors) and the prior order across the stream."""
    with Session(component_engine) as session:
        small = compute_factor_lab_all(session, _cfg_batch(1), as_of=as_of)
        big = compute_factor_lab_all(session, _cfg_batch(1_000_000), as_of=as_of)
        assert _eq(small, big), f"factor-lab-all payload differs by batch (as_of={as_of})"


# ==================================================================================================
# ops-hardening iter-50 (J-07): `compute_factor_lab_all`'s per-(factor,horizon) obs-build + sort is the
# CONFIRMED live crash frame from iter-49's own traceback (`research.py:1051`'s `sorted(obs, ...)`, an
# uncaught MemoryError that killed the backend). Two proofs:
#   1. TC-3: the bounded implementation (a `__slots__` `_FactorLabAllObs` stand-in for the old list-of-
#      dicts) is byte-identical to a PINNED COPY of the pre-iter-50 dict-based implementation — mirrors
#      this file's own established "pinned pre-fix reference oracle" pattern (see the `_fr_slice_map`
#      TC-2 block above).
#   2. TC-2 (fast/deterministic leg): a MemoryError injected at the confirmed crash frame via the SAME
#      test-only `_fault_inject_memory_error` hook the ingest finalize-tail fault-injection suite already
#      uses (test_ingest_finalize_fault_injection.py) is caught by the isolate-and-continue convention —
#      never crashes the process, never raises out of `compute_factor_lab_all` /
#      `factor_lab_all_cached`. A REAL `ulimit -v` drill proves the SAME contract under genuine memory
#      pressure (test_start_backend_script.py).
# ==================================================================================================
def _compute_factor_lab_all_pinned_pre_iter50(session: Session, config, *, as_of=None) -> dict:
    """A byte-for-byte copy of `compute_factor_lab_all`'s PRE-iter-50 obs-build + sort — the plain
    list-of-dicts implementation iter-49's own traceback identified as the live crash frame — pinned here
    as the reference oracle TC-3 proves the iter-50 `_FactorLabAllObs`-based bound against. Deliberately
    does NOT call the current `compute_factor_lab_all` (that would prove nothing)."""
    cfg = config
    fl = cfg.research.factor_lab
    wf = cfg.walk_forward
    catalog = factor_catalog(cfg)
    factors = list(fl.factors)
    horizons = list(wf.horizons)
    default_h = wf.default_horizon

    core_records, pools = _all_factor_observations_by_horizon(session, factors, horizons, as_of, cfg=cfg)
    factor_index = {f.key: i for i, f in enumerate(factors)}

    factors_table: list[dict] = []
    for factor in factors:
        idx = factor_index[factor.key]
        by_horizon: list[dict] = []
        dh_rank_ic: dict = {"value": None, "n": 0}
        dh_risk_adjusted = None
        dh_n_total = 0
        for h in horizons:
            obs = []
            for core_idx, ret, max_drawdown in pools[h]:
                factor_value = core_records[core_idx][2][idx]
                if factor_value is None:
                    continue
                run_id, ticker, _values = core_records[core_idx]
                obs.append({
                    "run_id": run_id, "ticker": ticker,
                    "factor": float(factor_value), "return": ret, "max_drawdown": max_drawdown,
                })
            ordered = sorted(obs, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))
            deciles = _deciles(ordered, fl.deciles, wf.min_sample)
            by_horizon.append({"horizon": h, "n_total": len(obs), "deciles": deciles})
            if h == default_h:
                dh_rank_ic = _rank_ic([(o["factor"], o["return"]) for o in obs])
                dh_risk_adjusted = deciles[-1]["risk_adjusted"]
                dh_n_total = len(obs)
        factors_table.append({
            "key": factor.key, "label": factor.label, "family": factor.family,
            "direction": factor.direction,
            "n_total": dh_n_total,
            "rank_ic": dh_rank_ic,
            "risk_adjusted": dh_risk_adjusted,
            "by_horizon": by_horizon,
        })

    return {
        "asof_date": as_of.isoformat() if as_of is not None else None,
        "factors": catalog,
        "horizons": horizons,
        "default_horizon": default_h,
        "deciles_count": fl.deciles,
        "min_sample": wf.min_sample,
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "descriptive_caveat": RESEARCH_CAVEAT,
        "factors_table": factors_table,
    }


@pytest.mark.parametrize("as_of", [None, date(2025, 1, 31)])
def test_compute_factor_lab_all_matches_pinned_pre_iter50_reference(prune_engine, as_of):
    """TC-3 (AG-3) — the bounded `compute_factor_lab_all` is byte-identical to the pinned pre-iter-50
    reference oracle above, for every (factor, horizon, decile) figure, both all-history and a historical
    as_of — proving the `_FactorLabAllObs` memory bound changed only the internal representation, never a
    value or an ordering."""
    cfg = load_config()
    with Session(prune_engine) as session:
        got = compute_factor_lab_all(session, cfg, as_of=as_of)
        want = _compute_factor_lab_all_pinned_pre_iter50(session, cfg, as_of=as_of)
        assert _eq(got, want), (
            f"bounded compute_factor_lab_all diverges from the pinned pre-iter-50 reference (as_of={as_of})"
        )


def test_compute_factor_lab_all_isolates_memory_pressure_per_factor_horizon(component_engine, monkeypatch):
    """TC-2 (fast/deterministic leg) — a MemoryError injected at the confirmed iter-49 crash frame is
    caught by the per-(factor,horizon) isolate-and-continue convention: THAT entry alone degrades to an
    honest `status: "unavailable"` (empty deciles, n_total 0) — `compute_factor_lab_all` itself never
    raises, so a live request can still answer. Control arm first (env unset -> no `status` key anywhere,
    proving a silently-disabled injector cannot pass as a green result), then the armed leg."""
    cfg = load_config()

    with Session(component_engine) as session:
        control = compute_factor_lab_all(session, cfg, as_of=None)
    for entry in control["factors_table"]:
        for bh in entry["by_horizon"]:
            assert "status" not in bh, f"control run must have no degraded entries; got {bh}"

    monkeypatch.setenv(data_manager._FAULT_INJECT_MEMORY_ERROR_ENV, "factor_lab_all")
    with Session(component_engine) as session:
        payload = compute_factor_lab_all(session, cfg, as_of=None)  # must not raise

    # the injector fires unconditionally on every call, so EVERY (factor, horizon) entry degrades —
    # exercising the catch under maximum, repeated, consecutive stress (never accumulates, never escapes).
    assert payload["factors_table"], "the factor catalog must still be listed even when every entry degrades"
    for entry in payload["factors_table"]:
        assert entry["n_total"] == 0
        assert entry["rank_ic"] == {"value": None, "n": 0}
        assert entry["risk_adjusted"] is None
        for bh in entry["by_horizon"]:
            assert bh["status"] == "unavailable"
            assert bh["deciles"] == []
            assert bh["n_total"] == 0


def test_factor_lab_all_cached_degrades_honestly_on_memory_error_outside_the_per_entry_loop(
    component_engine, monkeypatch,
):
    """The OUTER safety net in `factor_lab_all_cached`: a MemoryError raised OUTSIDE the per-(factor,
    horizon) loop (e.g. the shared pool builder) is still caught — degrading the WHOLE response honestly
    (`factors_status: "unavailable"`, empty `factors_table`) instead of propagating to FastAPI. Never
    cached (no EventStudyCache row persisted), and the single-flight slot is not left wedged — a
    follow-up call with the fault removed succeeds normally."""
    cfg = load_config()

    def _boom(*_a, **_k):
        raise MemoryError("simulated — outside the per-entry loop")

    monkeypatch.setattr(research_module, "_all_factor_observations_by_horizon", _boom)
    with Session(component_engine) as session:
        degraded = factor_lab_all_cached(session, cfg, as_of=None)
        assert degraded["factors_status"] == "unavailable"
        assert degraded["factors_table"] == []
        rows = session.exec(
            select(EventStudyCache).where(EventStudyCache.view == "factors_table")
        ).all()
        assert rows == [], "a degraded response must never be persisted to the cache"

    monkeypatch.undo()  # restore the real _all_factor_observations_by_horizon
    # iter-50 AUDIT FIX (B4): the memory-pressure cooldown is what makes "never cached" safe — without it,
    # every viewer restarts a doomed multi-GB compute. Expire it explicitly here so this test keeps proving
    # exactly what it always proved (the single-flight slot is not wedged and a real compute still works),
    # rather than silently measuring the cooldown instead.
    _expire_factor_lab_cooldown()
    with Session(component_engine) as session:
        recovered = factor_lab_all_cached(session, cfg, as_of=None)  # must not hang — slot not wedged
    assert recovered["factors_table"], "a follow-up call after the fault clears must compute normally"
    assert "factors_status" not in recovered


def test_factor_lab_all_cached_never_persists_a_per_entry_degraded_payload(component_engine, monkeypatch):
    """A payload where a per-(factor,horizon) entry degraded under memory pressure (the INNER isolate-
    and-continue inside `compute_factor_lab_all`, which returns NORMALLY rather than raising) must NEVER
    be persisted to the cache — otherwise a LATER request under the SAME dataset-version stamp would be
    served this stale degraded payload until the next dataset change, instead of getting a fresh attempt
    once the memory pressure has actually cleared. Proven by injecting the fault for exactly one call,
    confirming the served response is honestly degraded, confirming NO EventStudyCache row was written,
    then clearing the fault and confirming the NEXT call computes fresh (not a stale degraded HIT)."""
    cfg = load_config()

    monkeypatch.setenv(data_manager._FAULT_INJECT_MEMORY_ERROR_ENV, "factor_lab_all")
    with Session(component_engine) as session:
        degraded = factor_lab_all_cached(session, cfg, as_of=None)
    assert any(
        bh["status"] == "unavailable"
        for entry in degraded["factors_table"]
        for bh in entry["by_horizon"]
    ), "fixture sanity: the injected fault must actually degrade at least one entry"
    with Session(component_engine) as session:
        rows = session.exec(
            select(EventStudyCache).where(EventStudyCache.view == "factors_table")
        ).all()
    assert rows == [], "a per-entry-degraded payload must never be persisted to the cache"

    monkeypatch.delenv(data_manager._FAULT_INJECT_MEMORY_ERROR_ENV, raising=False)
    # iter-50 AUDIT FIX (B4): expire the in-process memory-pressure cooldown so this test still measures
    # the cache (its subject), not the cooldown — the cooldown's own behaviour is pinned separately below.
    _expire_factor_lab_cooldown()
    with Session(component_engine) as session:
        recovered = factor_lab_all_cached(session, cfg, as_of=None)
    assert all(
        "status" not in bh for entry in recovered["factors_table"] for bh in entry["by_horizon"]
    ), "the next call (fault cleared) must compute fresh, never serve a stale degraded HIT from the cache"


# ==================================================================================================
# ops-hardening iter-50 AUDIT FIX (finding B4) — the degrade path's TERMINATION CONDITION.
#
# "Never cache a degraded payload" is correct in intent, but on its own it removed the only thing that
# used to stop the retries: with no persisted row, no negative cache, no backoff and no cap on concurrent
# computes, EVERY subsequent view of `/research/factor-lab` started another full-scale, multi-minute,
# multi-GB compute that could not succeed while the pressure lasted. On 2026-08-05 that turned one failed
# page view into a 12-15 minute service wedge, amplified by five single-flight waiters timing out mid-
# compute (the 900s ceiling sat inside the real 780-875s compute band) and each starting an INDEPENDENT
# compute inside an already-exhausted process.
# ==================================================================================================
def _expire_factor_lab_cooldown() -> None:
    """Force every open memory-pressure cooldown window to be expired — the deterministic stand-in for
    "wait `_FACTOR_LAB_ALL_DEGRADED_COOLDOWN_S` seconds" (no clock manipulation, no sleep)."""
    with research_module._FACTOR_LAB_ALL_LOCK:
        for key, (_deadline, payload) in list(research_module._FACTOR_LAB_ALL_DEGRADED.items()):
            research_module._FACTOR_LAB_ALL_DEGRADED[key] = (float("-inf"), payload)


@pytest.fixture(autouse=True)
def _clean_factor_lab_cooldown():
    """The cooldown registry is MODULE state (deliberately: it must survive across requests inside one
    process). Clear it around every test in this file so no test can leak a window into another."""
    research_module._FACTOR_LAB_ALL_DEGRADED.clear()
    yield
    research_module._FACTOR_LAB_ALL_DEGRADED.clear()


def test_memory_pressure_cooldown_stops_every_viewer_restarting_a_doomed_compute(
    component_engine, monkeypatch,
):
    """iter-50 audit B4 — after a compute degrades under memory pressure, the NEXT viewer of the same key
    is served that honest degraded payload from the in-process cooldown instead of launching another
    full-scale compute. Teeth: `_all_factor_observations_by_horizon` is wrapped in a COUNTING spy, so a
    second heavy compute cannot hide — the count must stay at exactly 1 across the repeat views."""
    cfg = load_config()
    calls = {"n": 0}
    real = research_module._all_factor_observations_by_horizon

    def _counting_boom(*a, **k):
        calls["n"] += 1
        raise MemoryError("simulated memory pressure")

    monkeypatch.setattr(research_module, "_all_factor_observations_by_horizon", _counting_boom)
    with Session(component_engine) as session:
        first = factor_lab_all_cached(session, cfg, as_of=None)
    assert first["factors_status"] == "unavailable"
    assert calls["n"] == 1, "the first view must actually attempt the compute"

    # three more views inside the cooldown window — each served the honest degrade, none recomputing.
    for i in range(3):
        with Session(component_engine) as session:
            repeat = factor_lab_all_cached(session, cfg, as_of=None)
        assert repeat["factors_status"] == "unavailable", f"repeat {i}: must stay honestly degraded"
        assert calls["n"] == 1, (
            f"repeat {i}: the cooldown must serve the degraded payload, not restart the compute "
            f"(compute attempts so far: {calls['n']})"
        )

    # still NEVER persisted — the cooldown is in-process only, never an EventStudyCache row.
    with Session(component_engine) as session:
        rows = session.exec(select(EventStudyCache).where(EventStudyCache.view == "factors_table")).all()
    assert rows == [], "the cooldown must not persist a degraded payload to the cache"

    # once the window expires, the next view retries for real — the cooldown is a backoff, not a wedge.
    _expire_factor_lab_cooldown()
    monkeypatch.setattr(research_module, "_all_factor_observations_by_horizon", real)
    with Session(component_engine) as session:
        recovered = factor_lab_all_cached(session, cfg, as_of=None)
    assert recovered["factors_table"] and "factors_status" not in recovered, (
        "after the cooldown window expires the next view must compute for real, not stay degraded forever"
    )


def test_memory_pressure_cooldown_is_per_key_and_cleared_by_a_successful_compute(
    component_engine, monkeypatch,
):
    """iter-50 audit B4 — two independent guarantees.

    (1) PER KEY: a cooldown opened for the all-history key must not silence a DIFFERENT as-of key. The key
        already carries the dataset-version stamp, so a dataset change can never be masked either.
    (2) CLEARED ON SUCCESS: a clean, fully-computed payload closes any window the key still carries, so
        recovery is immediate and never has to wait out a window opened by an earlier failure."""
    cfg = load_config()
    other_as_of = date(2025, 3, 31)

    monkeypatch.setattr(
        research_module, "_all_factor_observations_by_horizon",
        lambda *a, **k: (_ for _ in ()).throw(MemoryError("simulated")),
    )
    with Session(component_engine) as session:
        degraded = factor_lab_all_cached(session, cfg, as_of=None)
    assert degraded["factors_status"] == "unavailable"

    # (1) a DIFFERENT as-of key is untouched by the all-history key's window.
    monkeypatch.undo()
    with Session(component_engine) as session:
        other = factor_lab_all_cached(session, cfg, as_of=other_as_of)
    assert "factors_status" not in other, (
        "a cooldown opened for one key must never silence a different as-of key"
    )
    with Session(component_engine) as session:
        still_cooled = factor_lab_all_cached(session, cfg, as_of=None)
    assert still_cooled["factors_status"] == "unavailable", "the original key's window must still be open"

    # (2) a successful compute for the key CLOSES its window immediately.
    _expire_factor_lab_cooldown()
    with Session(component_engine) as session:
        recovered = factor_lab_all_cached(session, cfg, as_of=None)
    assert "factors_status" not in recovered
    assert not research_module._FACTOR_LAB_ALL_DEGRADED, (
        "a clean compute must clear the key's cooldown window, so recovery never waits out a stale one"
    )


def test_single_flight_wait_ceiling_clears_the_measured_cold_compute(component_engine):
    """iter-50 audit B4 (second half) — the single-flight bounded wait must sit ABOVE the real cold-compute
    duration, not inside it. The pre-fix ceiling was 300 x 3 = 900s while a live cold compute measured
    780.2s and 874.7s (`reports/perf-budgets.md` Addendum 8), so waiters routinely timed out MID-compute
    and fell through to compute independently — `logs/backend.log` recorded five such fall-throughs in
    2m16s during the outage window, each starting an additional independent multi-GB compute.

    A source-level pin, deliberately: the real failure needs a 13-minute compute to reproduce, and a test
    that sleeps for that is not a test. Teeth: restoring the old 300s base fails this."""
    measured = research_module._FACTOR_LAB_ALL_MEASURED_COLD_MISS_S
    ceiling = research_module._FACTOR_LAB_ALL_WAIT_TIMEOUT_S
    worst_observed_live_cold_compute_s = 874.7  # 2026-08-05, reports/perf-budgets.md Addendum 8
    assert measured >= worst_observed_live_cold_compute_s, (
        f"the measured-cold-miss base ({measured}s) is below the worst observed live cold compute "
        f"({worst_observed_live_cold_compute_s}s) — waiters will time out mid-compute and duplicate it"
    )
    assert ceiling > worst_observed_live_cold_compute_s, (
        f"the single-flight wait ceiling ({ceiling}s) must clear the real compute duration "
        f"({worst_observed_live_cold_compute_s}s); it is reached only by a genuinely wedged owner"
    )
    assert research_module._FACTOR_LAB_ALL_DEGRADED_COOLDOWN_S >= worst_observed_live_cold_compute_s, (
        "the degrade cooldown must be at least one full compute duration — a retry started sooner cannot "
        "observe a recovered host, only add load to an exhausted one"
    )


# ==================================================================================================
# ops-hardening iter-29 (AG-8): `_factor_observations`'s join accumulator (`ret_by_run_symbol`) used to
# hold ONE entry per distinct (run_id, symbol) pair across the FULL horizon's `forward_returns` history for
# as_of=None (803,042 pairs / 3,964,725 rows measured live at iter-28) even though the SOURCE query was
# already `yield_per`-streamed — an unbounded whole-history materialization in substance (AG-8). The fix
# chunks `runs_with_fr` (the sorted distinct run-id list, now discovered via a lightweight DISTINCT query
# instead of as a side effect of building the full accumulator) into bounded slices, rebuilding the
# accumulator ONE slice at a time via the new `_fr_slice_map` helper — so its LIVE size is bounded by
# (chunk width x symbols-per-run), never by the full history's distinct-pair count. These proofs pin:
#   1. TC-1: the live accumulator (`_fr_slice_map`'s return value) never holds more than one chunk's worth
#      of entries at any point during a call, on a fixture whose rows span more than one chunk across >=2
#      distinct run ids.
#   2. TC-2: the chunked rewrite is byte-identical to a pinned copy of the PRE-FIX (single-accumulator)
#      implementation, for both as_of=None and a historical as_of=D.
#   3. TC-3: the as_of=D call returns zero observations from a run dated after D (no-lookahead preserved).
# ==================================================================================================
@pytest.fixture()
def chunked_accumulator_engine(tmp_path):
    """5 distinct ScannerRuns (one per month, Jan-May 2025), each with 3 tickers carrying a forward return
    at horizon H — 15 total distinct (run_id, symbol) pairs, spanning 5 distinct run ids. Dedicated (not
    reused from `prune_engine`/`component_engine`) so the chunk-boundary proof (TC-1) and the as_of cutoff
    proof (TC-3) have a fixture shaped exactly for them: enough runs to force multiple chunks at a small
    `read_batch_size`, and dates that cleanly split into an early/late group around a chosen as_of."""
    engine = make_engine(f"sqlite:///{tmp_path / 'chunked.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        runs = [
            _add_run(session, date(2025, m, 10), regime_label="Risk-on" if m % 2 else "Risk-off")
            for m in range(1, 6)  # r0=Jan .. r4=May 2025
        ]
        session.flush()
        for i, run in enumerate(runs):
            for j, base in enumerate(("AA", "BB", "CC")):
                ticker = f"{base}{i}"  # distinct symbol per run -> 15 genuinely distinct (run_id, symbol) pairs
                _add_result(session, run.id, ticker, j + 1, setup="Actionable", sector="Technology",
                            lead=50.0 + i + j)
                _add_fr(session, run.id, ticker, 0.01 * (i + 1) + 0.001 * j, horizon=H,
                        mae=-0.02, mfe=0.05, mdd=-0.03 - 0.001 * j)
        session.commit()
    return engine


def _factor_observations_reference_unchunked(session, factor, horizon, as_of, cfg):
    """A pinned copy of iter-29's PRE-FIX `_factor_observations` body: ONE unbounded `ret_by_run_symbol`
    accumulator built from a SINGLE un-sliced `fr_stmt` covering the FULL `runs_with_fr` set at once (no
    `_fr_slice_map`, no chunk loop) — the regression oracle for the iter-29 chunked rewrite's byte-identity
    proof (TC-2). Calls the SAME unchanged helpers (`parse_factor_source`, `_extract_factor_value`) the real,
    rewritten function still uses, so any divergence can only come from the chunking itself."""
    from app.engine.research import _extract_factor_value, parse_factor_source
    parsed = parse_factor_source(factor.source)
    batch = cfg.research.read_batch_size
    fr_stmt = select(
        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return, ForwardReturn.max_drawdown
    ).where(ForwardReturn.horizon == horizon)
    if as_of is not None:
        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
            ScannerRun.asof_date <= as_of
        )
    ret_by_run_symbol = {}
    runs_with_fr_set = set()
    for run_id, symbol, realized_return, max_drawdown in session.exec(fr_stmt).yield_per(batch):
        ret_by_run_symbol[(run_id, symbol)] = (realized_return, max_drawdown)
        runs_with_fr_set.add(run_id)
    runs_with_fr = sorted(runs_with_fr_set)
    run_rows = (
        session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
        if runs_with_fr else []
    )
    regime_by_run = {run.id: run.regime_label for run in run_rows}
    res_stmt = (
        select(ScannerResult)
        .where(ScannerResult.run_id.in_(runs_with_fr))
        .order_by(ScannerResult.run_id, ScannerResult.id)
    )
    results = session.exec(res_stmt).yield_per(batch) if runs_with_fr else []
    observations = []
    for res in results:
        fr = ret_by_run_symbol.get((res.run_id, res.ticker))
        if fr is None:
            continue
        realized, max_drawdown = fr
        value = _extract_factor_value(res, parsed)
        if value is None:
            continue
        observations.append({
            "run_id": res.run_id, "ticker": res.ticker, "factor": float(value), "return": realized,
            "max_drawdown": max_drawdown,
            "regime": regime_by_run.get(res.run_id),
        })
    return observations


def test_factor_observations_accumulator_is_chunk_bounded(chunked_accumulator_engine, monkeypatch):
    """TC-1: `_factor_observations`'s join accumulator (`_fr_slice_map`'s return value, wrapped/observed via
    monkeypatch) never holds more entries than ONE bounded chunk at any point during the call — never one
    entry per distinct (run_id, symbol) pair in the whole fixture (15 pairs across 5 run ids)."""
    factor = next(f for f in load_config().research.factor_lab.factors if f.key == "leadership_score")
    observed_sizes: list[int] = []
    real_fr_slice_map = research_module._fr_slice_map

    def _wrapped(session, horizon, slice_run_ids, batch):
        result = real_fr_slice_map(session, horizon, slice_run_ids, batch)
        observed_sizes.append(len(result))
        return result

    monkeypatch.setattr(research_module, "_fr_slice_map", _wrapped)
    with Session(chunked_accumulator_engine) as session:
        # chunk width = 2 run ids/slice over 5 distinct run ids -> 3 slices (2, 2, 1 run ids each)
        observations = research_module._factor_observations(session, factor, H, None, cfg=_cfg_batch(2))

    total_pairs = 15  # 5 runs x 3 tickers, by fixture construction
    assert len(observations) == total_pairs, "sanity: every fixture pair must surface as an observation"
    assert len(observed_sizes) == 3, f"expected 3 chunks (5 run ids at width 2), got {len(observed_sizes)}"
    assert max(observed_sizes) <= 6, (
        f"a single slice must never exceed 2 run ids x 3 tickers = 6 entries, got {max(observed_sizes)}"
    )
    assert max(observed_sizes) < total_pairs, (
        "the live accumulator must never hold the WHOLE fixture's pairs at once"
    )


@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
def test_factor_observations_chunked_equals_unchunked_reference(chunked_accumulator_engine, as_of):
    """TC-2: the iter-29 chunked `_factor_observations` is byte-identical to the pinned pre-fix
    (single-accumulator) reference — for as_of=None (all-history) AND a historical as_of=D (2025-03-15) that
    splits the 5-run fixture into an early (Jan-Mar) / late (Apr-May) group."""
    cfg = _cfg_batch(2)
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
    with Session(chunked_accumulator_engine) as session:
        chunked = _factor_observations(session, factor, H, as_of, cfg=cfg)
        reference = _factor_observations_reference_unchunked(session, factor, H, as_of, cfg)
    assert _eq(chunked, reference), f"chunked output != pinned pre-fix reference (as_of={as_of})"


def test_factor_observations_chunked_as_of_excludes_runs_after_cutoff(chunked_accumulator_engine):
    """TC-3: for the as_of=D-scoped chunked call, zero returned observations reference a run dated after D
    (no-lookahead preserved through the chunk rewrite)."""
    d = date(2025, 3, 15)  # between run r2 (Mar 10) and run r3 (Apr 10)
    factor = next(f for f in load_config().research.factor_lab.factors if f.key == "leadership_score")
    with Session(chunked_accumulator_engine) as session:
        observations = _factor_observations(session, factor, H, d, cfg=_cfg_batch(2))
        run_dates = {run.id: run.asof_date for run in session.exec(select(ScannerRun)).all()}
    assert observations, "sanity: the early-group runs (Jan-Mar) must still contribute observations"
    for obs in observations:
        assert run_dates[obs["run_id"]] <= d, f"observation from run {obs['run_id']} dated after {d}"


# ==================================================================================================
# iter-29 AUDIT (AG-8): the two proofs above pin the chunking MECHANISM, but both drive it through an
# artificially small `_cfg_batch(2)` override — so they pass no matter what the SHIPPED config does. As
# first shipped, iter-29's loop reused `research.read_batch_size` (2000, a ROW count) as its RUN-COUNT
# chunk width; the live basis carries only 1,812-1,871 distinct runs per horizon, so the loop produced
# exactly ONE chunk and the accumulator still held every pair at once (792,507 measured at h=20 via
# `SELECT ... WHERE horizon=20 AND run_id IN (<first 2000 sorted run ids>)` — 0% below the pre-fix peak,
# i.e. a bound that bound nothing). The two tests below pin the property at the REAL configuration, which
# is what AG-8 is actually about.
# ==================================================================================================

# The live basis measured during the iter-29 audit: 1,812-1,871 distinct scanner runs per horizon, ~429
# symbols per run. A run-chunk width at/above the run count degenerates to a single chunk, so the shipped
# width must stay well below it with room for years of further daily-cadence growth; 500 is the loosest
# ceiling that still forces real chunking on today's basis (>=4 chunks) and would have caught the shipped
# 2000. Peak accumulator = width x symbols-per-run, so the shipped 100 holds ~43-55K pairs, not ~800K.
_MAX_MEANINGFUL_RUN_CHUNK = 500


def test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis():
    """The SHIPPED `research.factor_join_run_chunk` must be small enough to produce real chunking against
    a multi-year daily-cadence basis. This is the regression guard for the iter-29 audit finding: a width
    of 2000 runs (the row knob, reused) against 1,812-1,871 live runs per horizon meant one chunk and zero
    peak reduction, while every unit proof still passed because it overrode the knob to 2."""
    research_cfg = load_config().research
    width = research_cfg.factor_join_run_chunk
    assert 1 <= width <= _MAX_MEANINGFUL_RUN_CHUNK, (
        f"research.factor_join_run_chunk={width} cannot bound the join accumulator on the live basis "
        f"(1,812-1,871 distinct runs/horizon): it must be <= {_MAX_MEANINGFUL_RUN_CHUNK}"
    )


def test_factor_observations_chunks_at_the_shipped_config(tmp_path, monkeypatch):
    """The accumulator is chunk-bounded under the SHIPPED config — no `_cfg_batch` override. Builds a
    fixture with (shipped width + 3) runs so real chunking is REQUIRED, then asserts `_factor_observations`
    made >= 2 slice reads and that no single slice ever held the whole fixture's (run_id, symbol) pairs."""
    cfg = load_config()  # the REAL config.yaml — deliberately NOT overridden
    width = cfg.research.factor_join_run_chunk
    n_runs, tickers = width + 3, ("AA", "BB")
    engine = make_engine(f"sqlite:///{tmp_path / 'shipped_chunk.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for i in range(n_runs):
            run = _add_run(session, date(2025, 1, 1) + timedelta(days=i), regime_label="Risk-on")
            session.flush()
            for j, base in enumerate(tickers):
                ticker = f"{base}{i}"
                _add_result(session, run.id, ticker, j + 1, setup="Actionable", sector="Technology",
                            lead=50.0 + (i % 7) + j)
                _add_fr(session, run.id, ticker, 0.01 * (i + 1) + 0.001 * j, horizon=H,
                        mae=-0.02, mfe=0.05, mdd=-0.03)
        session.commit()

    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
    observed_sizes: list[int] = []
    real_fr_slice_map = research_module._fr_slice_map

    def _wrapped(session, horizon, slice_run_ids, batch):
        result = real_fr_slice_map(session, horizon, slice_run_ids, batch)
        observed_sizes.append(len(result))
        return result

    monkeypatch.setattr(research_module, "_fr_slice_map", _wrapped)
    with Session(engine) as session:
        observations = research_module._factor_observations(session, factor, H, None, cfg=cfg)

    total_pairs = n_runs * len(tickers)
    assert len(observations) == total_pairs, "sanity: every fixture pair must surface as an observation"
    assert len(observed_sizes) >= 2, (
        f"the SHIPPED config produced {len(observed_sizes)} chunk(s) over {n_runs} runs — the accumulator "
        f"bound is inert at the real configuration (width={width})"
    )
    assert max(observed_sizes) <= width * len(tickers), "a slice exceeded its configured run-chunk width"
    assert max(observed_sizes) < total_pairs, (
        "the live accumulator must never hold the WHOLE fixture's pairs at once under the shipped config"
    )


# ==================================================================================================
# ops-hardening iter-46 (AG-8): `_combination_observations`'s join accumulator (`ret_by_run_symbol`) used
# to hold ONE entry per distinct (run_id, symbol) pair across the FULL horizon's `forward_returns` history
# for as_of=None (1,285,609 rows measured live at horizon=20) — the evidence-serving path's OTHER named
# `MemoryError` site (`research.py:777` pre-fix), `_factor_observations`'s own iter-29 sibling gap. The fix
# mirrors iter-29 exactly: `_runs_with_fr` discovers run ids once, `_fr_slice_map` (the SAME helper
# `_factor_observations` already uses) builds each bounded slice's join map, discarded before the next.
# These proofs pin, for `_combination_observations` specifically:
#   1. TC-1: the live accumulator (`_fr_slice_map`'s return value) never holds more than one chunk's worth
#      of entries at any point during a call.
#   2. TC-3: the chunked rewrite is byte-identical to a pinned copy of the PRE-FIX (single-accumulator)
#      implementation, for as_of=None AND a historical as_of=D — reproducing the live certified-claims
#      ledger's one `kind == "combination"` claim (`condition: ["rs_spy_3m:top:quintile",
#      "high_proximity:top:tertile"]`, `horizon: 20` — `runs/goal-session-mcp-loop/state/
#      certified-claims.jsonl`), both `leadership.components` factors read from `record_json`.
# ==================================================================================================
def _leadership_component_record_json(ticker: str, rs_spy_3m: float, high_proximity: float) -> str:
    """A `record_json` blob carrying the TWO component factors the live ledger's one `combination`-kind
    claim actually references (`leadership.components.rs_spy_3m.raw` and
    `leadership.components.high_proximity.raw`, `config.yaml:935/937`) — the exact shape
    `_extract_factor_value` reads for a `component` factor."""
    return json.dumps({
        "ticker": ticker, "name": ticker,
        "leadership": {"components": [
            {"name": "rs_spy_3m", "raw": rs_spy_3m},
            {"name": "high_proximity", "raw": high_proximity},
        ]},
    })


@pytest.fixture()
def combination_chunked_engine(tmp_path):
    """The SAME 5-run / 3-ticker-per-run shape as `chunked_accumulator_engine` (15 distinct (run_id,
    symbol) pairs spanning 5 distinct run ids — enough to force multiple slices at a small run-chunk
    width), but with `record_json` carrying real `rs_spy_3m` / `high_proximity` component values so the
    live ledger's one `combination`-kind claim can be reproduced exactly (TC-3)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'combination_chunked.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        runs = [
            _add_run(session, date(2025, m, 10), regime_label="Risk-on" if m % 2 else "Risk-off")
            for m in range(1, 6)  # r0=Jan .. r4=May 2025
        ]
        session.flush()
        for i, run in enumerate(runs):
            for j, base in enumerate(("AA", "BB", "CC")):
                ticker = f"{base}{i}"  # distinct symbol per run -> 15 genuinely distinct (run_id, symbol) pairs
                session.add(ScannerResult(
                    run_id=run.id, ticker=ticker, name=ticker, sector="Technology",
                    leadership_score=50.0 + i + j, leadership_bucket="C",
                    entry_quality_score=50.0, entry_quality_bucket="C",
                    risk_score=50.0, risk_bucket="C",
                    setup_status="Actionable", rank=j + 1,
                    record_json=_leadership_component_record_json(
                        ticker, rs_spy_3m=0.10 * (i + 1) + 0.01 * j, high_proximity=-0.05 * (i + 1) - 0.01 * j,
                    ),
                ))
                _add_fr(session, run.id, ticker, 0.01 * (i + 1) + 0.001 * j, horizon=H,
                        mae=-0.02, mfe=0.05, mdd=-0.03 - 0.001 * j)
        session.commit()
    return engine


def _combination_observations_reference_unchunked(session, factors, horizon, as_of, cfg):
    """A pinned copy of the PRE-iter-46 `_combination_observations` body: ONE unbounded
    `ret_by_run_symbol` accumulator built from a SINGLE un-sliced `fr_stmt` covering the FULL
    `runs_with_fr` set at once (no `_fr_slice_map`, no chunk loop) — the regression oracle for TC-3. Calls
    the SAME unchanged helpers (`parse_factor_source`, `_extract_factor_value`) the real, rewritten
    function still uses, so any divergence can only come from the chunking itself."""
    from app.engine.research import _extract_factor_value, parse_factor_source
    parsed_by_key = {f.key: parse_factor_source(f.source) for f in factors}
    batch = cfg.research.read_batch_size
    fr_stmt = select(
        ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.realized_return
    ).where(ForwardReturn.horizon == horizon)
    if as_of is not None:
        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
            ScannerRun.asof_date <= as_of
        )
    ret_by_run_symbol: dict[tuple[int, str], float] = {}
    runs_with_fr_set: set[int] = set()
    for run_id, symbol, realized_return in session.exec(fr_stmt).yield_per(batch):
        ret_by_run_symbol[(run_id, symbol)] = realized_return
        runs_with_fr_set.add(run_id)
    runs_with_fr = sorted(runs_with_fr_set)
    res_stmt = (
        select(ScannerResult)
        .where(ScannerResult.run_id.in_(runs_with_fr))
        .order_by(ScannerResult.run_id, ScannerResult.id)
    )
    results = session.exec(res_stmt).yield_per(batch) if runs_with_fr else []
    observations = []
    for res in results:
        realized = ret_by_run_symbol.get((res.run_id, res.ticker))
        if realized is None:
            continue
        values: dict[str, float] = {}
        for key, parsed in parsed_by_key.items():
            value = _extract_factor_value(res, parsed)
            if value is None:
                break
            values[key] = float(value)
        else:
            observations.append({
                "run_id": res.run_id, "ticker": res.ticker, "return": realized, "values": values,
            })
    return observations


def test_combination_observations_accumulator_is_chunk_bounded(combination_chunked_engine, monkeypatch):
    """TC-1: `_combination_observations`'s join accumulator (`_fr_slice_map`'s return value, wrapped via
    monkeypatch) never holds more entries than ONE bounded chunk at any point during the call — never one
    entry per distinct (run_id, symbol) pair in the whole fixture (15 pairs across 5 run ids)."""
    cfg = load_config()
    factors = [f for f in cfg.research.factor_lab.factors if f.key in ("rs_spy_3m", "high_proximity")]
    assert len(factors) == 2, "sanity: the live claim's two factors must resolve from the shipped catalog"
    observed_sizes: list[int] = []
    real_fr_slice_map = research_module._fr_slice_map

    def _wrapped(session, horizon, slice_run_ids, batch):
        result = real_fr_slice_map(session, horizon, slice_run_ids, batch)
        observed_sizes.append(len(result))
        return result

    monkeypatch.setattr(research_module, "_fr_slice_map", _wrapped)
    with Session(combination_chunked_engine) as session:
        # chunk width = 2 run ids/slice over 5 distinct run ids -> 3 slices (2, 2, 1 run ids each)
        observations = research_module._combination_observations(
            session, factors, H, None, cfg=_cfg_batch(2)
        )

    total_pairs = 15  # 5 runs x 3 tickers, by fixture construction
    assert len(observations) == total_pairs, "sanity: every fixture pair must surface as an observation"
    assert len(observed_sizes) == 3, f"expected 3 chunks (5 run ids at width 2), got {len(observed_sizes)}"
    assert max(observed_sizes) <= 6, (
        f"a single slice must never exceed 2 run ids x 3 tickers = 6 entries, got {max(observed_sizes)}"
    )
    assert max(observed_sizes) < total_pairs, (
        "the live accumulator must never hold the WHOLE fixture's pairs at once"
    )


@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
def test_combination_observations_chunked_equals_unchunked_reference(combination_chunked_engine, as_of):
    """TC-3: the iter-46 chunked `_combination_observations` is byte-identical to the pinned pre-fix
    (single-accumulator) reference — for as_of=None (all-history) AND a historical as_of=D (2025-03-15)
    that splits the 5-run fixture into an early (Jan-Mar) / late (Apr-May) group. Uses the live certified-
    claims ledger's own two-factor combination (`rs_spy_3m`, `high_proximity`) at its own horizon (20)."""
    cfg = _cfg_batch(2)
    factors = [f for f in cfg.research.factor_lab.factors if f.key in ("rs_spy_3m", "high_proximity")]
    with Session(combination_chunked_engine) as session:
        chunked = research_module._combination_observations(session, factors, H, as_of, cfg=cfg)
        reference = _combination_observations_reference_unchunked(session, factors, H, as_of, cfg)
    assert chunked, "sanity: the fixture must produce at least one observation"
    assert _eq(chunked, reference), f"chunked output != pinned pre-fix reference (as_of={as_of})"


def test_combination_observations_chunked_as_of_excludes_runs_after_cutoff(combination_chunked_engine):
    """No-lookahead guard: for the as_of=D-scoped chunked call, zero returned observations reference a run
    dated after D."""
    d = date(2025, 3, 15)  # between run r2 (Mar 10) and run r3 (Apr 10)
    cfg = load_config()
    factors = [f for f in cfg.research.factor_lab.factors if f.key in ("rs_spy_3m", "high_proximity")]
    with Session(combination_chunked_engine) as session:
        observations = research_module._combination_observations(session, factors, H, d, cfg=_cfg_batch(2))
        run_dates = {run.id: run.asof_date for run in session.exec(select(ScannerRun)).all()}
    assert observations, "sanity: the early-group runs (Jan-Mar) must still contribute observations"
    for obs in observations:
        assert run_dates[obs["run_id"]] <= d, f"observation from run {obs['run_id']} dated after {d}"


# ==================================================================================================
# ops-hardening iter-47 (AG-8, iter-46 audit B3): `app.engine.samples._factor_samples`'s "decile" branch
# used to build the FULL `_factor_observations` list (whole horizon population, up to ~800K observations
# measured live) and `sorted()` it WHOLE just to discard 9/10 of it after slicing one decile — the third
# unbounded whole-cohort materialization on the `/api/evidence` serving path (5 of the 7 live certified
# claims are decile-scoped factor claims; `logs/backend.log` caught it `MemoryError`-ing at 02:20:31 on
# 2026-08-04, reached via `evidence.py` -> `compute_drawdown_expectations_cached` -> `compute_samples` ->
# `_factor_samples`). `research._factor_decile_observations` (new) resolves the SAME decile membership in
# two BOUNDED passes (a lightweight population-wide sort-key pass, then a bounded rebuild restricted to the
# target decile's keys) instead of materializing + sorting the whole population's full dicts. These proofs
# pin byte-identity against the PRE-FIX approach (the exact `_factor_samples` decile branch used to run) —
# the memory-BOUND claim itself is proven live by `test_samples_memory_pressure.py`'s real subprocess
# induction (this repo's established convention for a boundedness claim, mirroring
# `test_evidence_drawdown_memory_pressure.py`).
# ==================================================================================================
def _factor_decile_observations_reference(session, factor, horizon, as_of, deciles_count, decile, cfg):
    """The PRE-FIX `_factor_samples` decile branch, pinned verbatim: the FULL `_factor_observations` list,
    sorted whole by the SAME tie-break key, then `_decile_member_slice`d — the regression oracle for the
    iter-47 two-pass bounded rewrite."""
    from app.engine.research import _decile_member_slice, _factor_observations

    observations = _factor_observations(session, factor, horizon, as_of, cfg=cfg)
    ordered = sorted(observations, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))
    return _decile_member_slice(ordered, deciles_count, decile)


@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
@pytest.mark.parametrize("decile", [1, 5, 10])
def test_factor_decile_observations_equals_pre_fix_reference(chunked_accumulator_engine, as_of, decile):
    """TC-4 (byte-identity leg): the bounded two-pass `_factor_decile_observations` is byte-identical to
    the pinned pre-fix (whole-population sort + slice) reference — across the first/middle/last decile and
    both all-history and a historical as_of that splits the 5-run fixture into an early/late group — under
    a chunk width small enough to force multiple slices in BOTH passes."""
    cfg = _cfg_batch(2)
    deciles_count = cfg.research.factor_lab.deciles
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
    with Session(chunked_accumulator_engine) as session:
        bounded = research_module._factor_decile_observations(
            session, factor, H, as_of, deciles_count, decile, cfg=cfg
        )
        reference = _factor_decile_observations_reference(
            session, factor, H, as_of, deciles_count, decile, cfg
        )
    assert _eq(bounded, reference), (
        f"bounded decile {decile} (as_of={as_of}) != pre-fix whole-population reference"
    )


def test_factor_decile_observations_union_covers_whole_pool_no_double_count(chunked_accumulator_engine):
    """Sanity/coherence companion to the byte-identity leg: the union of every D1..D10 bounded call's
    members equals the whole 15-pair fixture pool exactly once each — no member dropped, none duplicated,
    across the decile boundary arithmetic."""
    cfg = _cfg_batch(2)
    deciles_count = cfg.research.factor_lab.deciles
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
    seen: list[tuple[int, str]] = []
    with Session(chunked_accumulator_engine) as session:
        for d in range(1, deciles_count + 1):
            members = research_module._factor_decile_observations(
                session, factor, H, None, deciles_count, d, cfg=cfg
            )
            seen.extend((m["run_id"], m["ticker"]) for m in members)
    assert len(seen) == 15, f"expected all 15 fixture pairs covered exactly once, got {len(seen)}"
    assert len(set(seen)) == 15, "a (run_id, ticker) pair was double-counted across deciles"


def test_factor_decile_observations_chunk_independent(chunked_accumulator_engine):
    """The bounded decile resolution is batch/chunk-independent — read_batch_size AND
    factor_join_run_chunk both varied — never a value/order change, only a memory-shape change."""
    factor = next(f for f in load_config().research.factor_lab.factors if f.key == "leadership_score")
    with Session(chunked_accumulator_engine) as session:
        small = research_module._factor_decile_observations(
            session, factor, H, None, 10, 10, cfg=_cfg_batch(1, run_chunk=1)
        )
        big = research_module._factor_decile_observations(
            session, factor, H, None, 10, 10, cfg=_cfg_batch(1_000_000, run_chunk=1_000_000)
        )
    assert small, "sanity: decile 10 must be non-empty on this fixture"
    assert _eq(small, big), "bounded decile resolution differs by chunk width"


def test_factor_decile_pass1_retention_is_bounded_not_whole_population(chunked_accumulator_engine, monkeypatch):
    """ops-hardening iter-47 FIX PASS (audit finding B3): PASS 1 must not RETAIN one sort key per
    observation for the whole population (~1.25 M tuples ≈ 155 MB live) just to sort it whole — the
    "bounded READ, unbounded RETENTION" shape iter-40's lesson names, and the reason the audit judged
    `samples.py:156` reduced rather than bounded. Instrumenting the real `_BoundedRankWindow` records the
    live buffer length at every trim (its true momentary peak): the peak must stay inside `2 x capacity`
    and STRICTLY below the population, and `capacity` itself must be derived from the requested decile's
    own share — for D10 of 10 that is ~1/10 of the population, not the population."""
    cfg = _cfg_batch(2)
    deciles_count = cfg.research.factor_lab.deciles
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")

    peaks: list[int] = []
    caps: list[int] = []
    real_window = research_module._BoundedRankWindow

    class _ObservingWindow(real_window):
        def __init__(self, n_max, dc, d):
            super().__init__(n_max, dc, d)
            caps.append(self._capacity)

        def _trim(self):
            peaks.append(len(self._buf))  # the momentary peak: `add` trims the instant it is reached
            super()._trim()

    monkeypatch.setattr(research_module, "_BoundedRankWindow", _ObservingWindow)
    with Session(chunked_accumulator_engine) as session:
        members = research_module._factor_decile_observations(
            session, factor, H, None, deciles_count, deciles_count, cfg=cfg
        )
        population = len(_factor_observations(session, factor, H, None, cfg=cfg))

    assert members, "sanity: the top decile must be non-empty on this fixture"
    assert population == 15, f"sanity: this fixture's population is 15 observations, got {population}"
    assert caps == [2], (
        f"D10 of 10 over a 15-observation population must commit to a ~1/10 capacity, got {caps!r}"
    )
    assert peaks, "the window must actually trim (otherwise nothing is bounded)"
    assert max(peaks) <= 2 * caps[0], (
        f"peak retention {max(peaks)} exceeded the 2x-capacity bound ({2 * caps[0]})"
    )
    assert max(peaks) < population, (
        f"peak retention {max(peaks)} is not below the population {population} — this is the unbounded "
        f"whole-population accumulator the fix removes"
    )


def test_factor_decile_window_underflow_degrades_to_exact_computation(chunked_accumulator_engine, monkeypatch):
    """ops-hardening iter-47 FIX PASS (audit finding B3): the retention window is sized from a PROVEN
    upper bound, so it cannot underflow — but a truncated decile would be a WRONG SERVED NUMBER (AG-3),
    so the underflow branch degrades to the exact unbounded computation instead. Forced here with a
    deliberately too-small upper bound (1 against a 15-observation pool): the returned members must still
    be byte-identical to the pinned pre-fix reference, and the degrade must be logged, never silent."""
    cfg = _cfg_batch(2)
    deciles_count = cfg.research.factor_lab.deciles
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
    monkeypatch.setattr(research_module, "_decile_population_upper_bound", lambda *a, **kw: 1)

    records: list[str] = []
    monkeypatch.setattr(
        research_module.logger, "warning",
        lambda msg, *args, **kw: records.append(str(msg) % args if args else str(msg)),
    )
    with Session(chunked_accumulator_engine) as session:
        members = research_module._factor_decile_observations(
            session, factor, H, None, deciles_count, deciles_count, cfg=cfg
        )
        reference = _factor_decile_observations_reference(
            session, factor, H, None, deciles_count, deciles_count, cfg
        )
    assert members, "the degrade path must still return the decile's real members"
    assert _eq(members, reference), "the degraded (exact) path must stay byte-identical to the reference"
    assert any("window underflow" in r for r in records), (
        f"the degrade must be logged, never silent — got {records!r}"
    )


def test_factor_decile_population_upper_bound_is_never_below_the_real_population(chunked_accumulator_engine):
    """The window's capacity is only sound while `_decile_population_upper_bound(...) >= n`. Pinned
    directly against the real population this fixture produces (and against the as_of-scoped one, which
    the bound must track because it reads the SAME as_of-filtered run set)."""
    cfg = _cfg_batch(2)
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
    run_chunk = cfg.research.factor_join_run_chunk
    with Session(chunked_accumulator_engine) as session:
        for as_of in (None, date(2025, 3, 15)):
            runs = research_module._runs_with_fr(session, [H], as_of)
            bound = research_module._decile_population_upper_bound(session, runs, run_chunk)
            population = len(_factor_observations(session, factor, H, as_of, cfg=cfg))
            assert bound >= population, (
                f"upper bound {bound} < real population {population} at as_of={as_of} — the bounded "
                f"window could then discard a genuine decile member"
            )


def test_factor_decile_observations_zero_n_cohort_is_honest_empty(chunked_accumulator_engine):
    """An as_of before any snapshot resolves an honest empty decile — never a crash, never a fabricated
    member — under the two-pass bounded path (PASS 1's empty `sort_keys` short-circuits before PASS 2)."""
    cfg = _cfg_batch(2)
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
    with Session(chunked_accumulator_engine) as session:
        members = research_module._factor_decile_observations(
            session, factor, H, date(2024, 1, 1), cfg.research.factor_lab.deciles, 10, cfg=cfg
        )
    assert members == []


# ==================================================================================================
# ops-hardening iter-49 (J-05, drawdown_expectations_warm bound) — `_factor_decile_observations`'s two
# `res_stmt` reads used to `select(ScannerResult)` (the FULL ORM entity, every score/flag/date column plus
# the `record_json` blob) purely so `_extract_factor_value` could do a `getattr`/`.record_json` on a full
# row. Live profiling (a single decile-scoped drawdown-expectations claim on the real committed DB)
# measured >40s of a 63.9s call as SQLAlchemy/SQLModel ORM row construction alone — unrelated to
# `_extract_factor_value`'s own cheap `getattr`/`json.loads`. `_extract_factor_value_from_row` +
# `_factor_value_column` (new) column-project the read to `(run_id, ticker, <value column>)` instead —
# raw tuples, no ORM row built at all — for BOTH factor kinds ("column": the typed column selected
# directly; "component": `record_json` selected instead of the whole entity, so nothing the extractor
# reads is dropped). These proofs pin byte-identity against the PRE-FIX full-entity approach, for both
# kinds, mirroring `test_factor_decile_observations_equals_pre_fix_reference` above exactly.
# ==================================================================================================
def _factor_decile_observations_full_entity_reference(session, factor, horizon, as_of, deciles_count, decile, cfg):
    """The PRE-iter-49 `_factor_decile_observations` body, pinned verbatim (full-entity `select(ScannerResult)`
    in both passes, `_extract_factor_value` reading a real ORM row) — the regression oracle for the iter-49
    column-projection rewrite. Calls the SAME unchanged `_runs_with_fr` / `_fr_slice_map` /
    `_decile_population_upper_bound` / `_BoundedRankWindow` / `_extract_factor_value` helpers the real,
    rewritten function still uses, so any divergence can only come from the two `res_stmt` projections."""
    from app.engine.research import (
        _BoundedRankWindow, _decile_population_upper_bound, _extract_factor_value, _fr_slice_map,
        _runs_with_fr, parse_factor_source,
    )

    parsed = parse_factor_source(factor.source)
    research_cfg = cfg.research
    batch = research_cfg.read_batch_size
    run_chunk = research_cfg.factor_join_run_chunk
    runs_with_fr = _runs_with_fr(session, [horizon], as_of)
    n_max = _decile_population_upper_bound(session, runs_with_fr, run_chunk)
    window = _BoundedRankWindow(n_max, deciles_count, decile)

    n = 0
    for start in range(0, len(runs_with_fr), run_chunk):
        slice_run_ids = runs_with_fr[start:start + run_chunk]
        ret_by_run_symbol = _fr_slice_map(session, horizon, slice_run_ids, batch)
        res_stmt = (
            select(ScannerResult).where(ScannerResult.run_id.in_(slice_run_ids))
            .order_by(ScannerResult.run_id, ScannerResult.id)
        )
        for res in session.exec(res_stmt).yield_per(batch):
            if (res.run_id, res.ticker) not in ret_by_run_symbol:
                continue
            value = _extract_factor_value(res, parsed)
            if value is None:
                continue
            n += 1
            window.add((float(value), res.ticker, res.run_id))

    lo = (decile - 1) * n // deciles_count
    hi = decile * n // deciles_count
    ranked = window.slice(n, lo, hi)
    assert ranked is not None, "test fixture too small for the upper-bound invariant — widen it"
    target_keys = {(ticker, run_id) for _factor_val, ticker, run_id in ranked}
    if not target_keys:
        return []

    run_rows = (
        session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
        if runs_with_fr else []
    )
    regime_by_run = {run.id: run.regime_label for run in run_rows}

    members = []
    for start in range(0, len(runs_with_fr), run_chunk):
        slice_run_ids = runs_with_fr[start:start + run_chunk]
        ret_by_run_symbol = _fr_slice_map(session, horizon, slice_run_ids, batch)
        res_stmt = (
            select(ScannerResult).where(ScannerResult.run_id.in_(slice_run_ids))
            .order_by(ScannerResult.run_id, ScannerResult.id)
        )
        for res in session.exec(res_stmt).yield_per(batch):
            if (res.ticker, res.run_id) not in target_keys:
                continue
            fr = ret_by_run_symbol.get((res.run_id, res.ticker))
            if fr is None:
                continue
            realized, max_drawdown = fr
            value = _extract_factor_value(res, parsed)
            if value is None:
                continue
            members.append({
                "run_id": res.run_id, "ticker": res.ticker, "factor": float(value), "return": realized,
                "max_drawdown": max_drawdown,
                "regime": regime_by_run.get(res.run_id),
            })
    members.sort(key=lambda o: (o["factor"], o["ticker"], o["run_id"]))
    return members


@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
@pytest.mark.parametrize("decile", [1, 5, 10])
def test_factor_decile_observations_column_projected_equals_full_entity_reference(
    chunked_accumulator_engine, as_of, decile,
):
    """TC-3 (byte-identity leg, "column"-kind factor): the iter-49 column-projected
    `_factor_decile_observations` is byte-identical to the pinned pre-iter-49 (full-entity `select
    (ScannerResult)`) reference — across the first/middle/last decile and both all-history and a
    historical as_of, under a chunk width small enough to force multiple slices in BOTH passes."""
    cfg = _cfg_batch(2)
    deciles_count = cfg.research.factor_lab.deciles
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
    with Session(chunked_accumulator_engine) as session:
        shipped = research_module._factor_decile_observations(
            session, factor, H, as_of, deciles_count, decile, cfg=cfg
        )
        reference = _factor_decile_observations_full_entity_reference(
            session, factor, H, as_of, deciles_count, decile, cfg
        )
    assert _eq(shipped, reference), (
        f"column-projected decile {decile} (as_of={as_of}) != full-entity pre-iter-49 reference"
    )


def test_factor_decile_observations_column_projected_equals_full_entity_reference_component_kind(
    component_engine,
):
    """TC-3 (byte-identity leg, "component"-kind factor): the SAME proof as above, for a factor whose value
    lives in `record_json` (never a typed column) — the case where a naive column projection dropping
    `record_json` would silently change figures. `_factor_value_column` selects `record_json` itself
    (not the whole entity) for this kind, so nothing `_extract_factor_value_from_row` reads is lost.
    `component_engine`'s 4 non-zero-FR observations (AA/BB/CC/DD) are split with a REDUCED `deciles=2` (the
    real `factor_lab.deciles` default of 10 would make every decile a singleton on this small fixture,
    a much weaker discriminator for the chunk-and-project rewrite)."""
    cfg = load_config()
    cfg = cfg.model_copy(update={"research": cfg.research.model_copy(update={
        "read_batch_size": 1, "factor_join_run_chunk": 1,
        "factor_lab": cfg.research.factor_lab.model_copy(update={"deciles": 2}),
    })})
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "rs_spy_3m")
    assert factor is not None, "sanity: rs_spy_3m must be a configured component-kind factor"
    with Session(component_engine) as session:
        for decile in (1, 2):
            shipped = research_module._factor_decile_observations(
                session, factor, H, None, 2, decile, cfg=cfg
            )
            reference = _factor_decile_observations_full_entity_reference(
                session, factor, H, None, 2, decile, cfg
            )
            assert _eq(shipped, reference), (
                f"component-kind column-projected decile {decile} != full-entity pre-iter-49 reference"
            )
        # sanity: the fixture's component values are genuinely non-trivial (not an accidental all-None
        # cohort that would make this proof vacuous).
        d1 = research_module._factor_decile_observations(session, factor, H, None, 2, 1, cfg=cfg)
        d2 = research_module._factor_decile_observations(session, factor, H, None, 2, 2, cfg=cfg)
    assert d1 and d2, "sanity: both component-kind deciles must be non-empty on this fixture"


def test_extract_factor_value_from_row_equals_extract_factor_value(chunked_accumulator_engine, component_engine):
    """Direct unit proof that `_extract_factor_value_from_row` (fed the pre-selected column/record_json)
    is byte-identical to `_extract_factor_value` (fed the full ORM row) for both factor kinds, on real
    stored rows from both fixtures — the primitive the two decile-observation proofs above exercise only
    indirectly through the full two-pass algorithm."""
    from app.engine.research import (
        _extract_factor_value, _extract_factor_value_from_row, _factor_value_column, parse_factor_source,
    )

    cfg = load_config()
    column_factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
    component_factor = next(f for f in cfg.research.factor_lab.factors if f.key == "rs_spy_3m")
    column_parsed = parse_factor_source(column_factor.source)
    component_parsed = parse_factor_source(component_factor.source)
    assert column_parsed["kind"] == "column"
    assert component_parsed["kind"] == "component"

    with Session(chunked_accumulator_engine) as session:
        for res in session.exec(select(ScannerResult)).all():
            col = _factor_value_column(column_parsed)
            raw_value = getattr(res, col.key)
            assert _extract_factor_value_from_row(raw_value, column_parsed) == _extract_factor_value(
                res, column_parsed
            )

    with Session(component_engine) as session:
        for res in session.exec(select(ScannerResult)).all():
            assert _extract_factor_value_from_row(res.record_json, component_parsed) == _extract_factor_value(
                res, component_parsed
            )


# ==================================================================================================
# ops-hardening iter-48 (AG-8, iter-47 next-step item 5) — `app.engine.samples._factor_samples`'s
# "regime" branch used to build the FULL `_factor_observations` list (whole horizon population) just to
# discard every observation NOT matching the requested regime label afterward — the SAME "bounded read,
# unbounded retention" shape the iter-47 fix already closed for the "decile" branch. Unlike a decile,
# regime membership is a per-observation predicate with no population-wide rank dependency, so
# `research._factor_regime_observations` bounds it in a SINGLE pass (not two): it filters INSIDE the
# SAME chunked join loop `_factor_observations` runs, discarding a non-matching observation immediately.
# ==================================================================================================
def _factor_regime_observations_reference(session, factor, horizon, as_of, regime, cfg):
    """The PRE-FIX `_factor_samples` regime branch, pinned verbatim: the FULL `_factor_observations` list,
    filtered afterward — the regression oracle for the iter-48 bounded rewrite."""
    from app.engine.research import _factor_observations

    return [o for o in _factor_observations(session, factor, horizon, as_of, cfg=cfg) if o["regime"] == regime]


@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
@pytest.mark.parametrize("regime", ["Risk-on", "Risk-off"])
def test_factor_regime_observations_equals_pre_fix_reference(chunked_accumulator_engine, as_of, regime):
    """The bounded `_factor_regime_observations` is byte-identical to the pinned pre-fix (whole-population
    filter) reference — for both fixture regimes and both all-history and a historical as_of."""
    cfg = _cfg_batch(2)
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
    with Session(chunked_accumulator_engine) as session:
        bounded = research_module._factor_regime_observations(session, factor, H, as_of, regime, cfg=cfg)
        reference = _factor_regime_observations_reference(session, factor, H, as_of, regime, cfg)
    assert _eq(bounded, reference), (
        f"bounded regime {regime!r} (as_of={as_of}) != pre-fix whole-population reference"
    )


def test_factor_regime_observations_union_covers_whole_pool_no_double_count(chunked_accumulator_engine):
    """Sanity/coherence companion: the union of the two fixture regimes' bounded calls equals the whole
    15-pair fixture pool exactly once each — no member dropped, none duplicated."""
    cfg = _cfg_batch(2)
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
    seen: list[tuple[int, str]] = []
    with Session(chunked_accumulator_engine) as session:
        for regime in ("Risk-on", "Risk-off"):
            members = research_module._factor_regime_observations(session, factor, H, None, regime, cfg=cfg)
            seen.extend((m["run_id"], m["ticker"]) for m in members)
    assert len(seen) == 15, f"expected all 15 fixture pairs covered exactly once, got {len(seen)}"
    assert len(set(seen)) == 15, "a (run_id, ticker) pair was double-counted across regimes"


def test_factor_regime_observations_chunk_independent(chunked_accumulator_engine):
    """The bounded regime resolution is batch/chunk-independent — read_batch_size AND
    factor_join_run_chunk both varied — never a value/order change, only a memory-shape change."""
    factor = next(f for f in load_config().research.factor_lab.factors if f.key == "leadership_score")
    with Session(chunked_accumulator_engine) as session:
        small = research_module._factor_regime_observations(
            session, factor, H, None, "Risk-on", cfg=_cfg_batch(1, run_chunk=1)
        )
        big = research_module._factor_regime_observations(
            session, factor, H, None, "Risk-on", cfg=_cfg_batch(1_000_000, run_chunk=1_000_000)
        )
    assert small, "sanity: Risk-on must be non-empty on this fixture"
    assert _eq(small, big), "bounded regime resolution differs by chunk width"


def test_factor_regime_observations_never_materializes_non_matching_chunk(chunked_accumulator_engine, monkeypatch):
    """Bound proof: a chunk containing NO run in the target regime never even issues the join/scan query
    (`_fr_slice_map` is not called for it) — the SAME chunk loop `_factor_observations` runs, but with a
    non-matching chunk skipped entirely rather than resolved-then-discarded."""
    cfg = _cfg_batch(1, run_chunk=1)  # 1 run id per chunk -> 5 chunks, each either all-Risk-on or all-Risk-off
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")

    calls: list[list[int]] = []
    real_fr_slice_map = research_module._fr_slice_map

    def _wrapped(session, horizon, slice_run_ids, batch):
        calls.append(list(slice_run_ids))
        return real_fr_slice_map(session, horizon, slice_run_ids, batch)

    monkeypatch.setattr(research_module, "_fr_slice_map", _wrapped)
    with Session(chunked_accumulator_engine) as session:
        run_ids_by_regime: dict[str, list[int]] = {}
        for run in session.exec(select(ScannerRun)).all():
            run_ids_by_regime.setdefault(run.regime_label, []).append(run.id)
        members = research_module._factor_regime_observations(
            session, factor, H, None, "Risk-on", cfg=cfg
        )

    assert members, "sanity: Risk-on must be non-empty on this fixture"
    called_run_ids = {rid for slice_ids in calls for rid in slice_ids}
    risk_off_ids = set(run_ids_by_regime.get("Risk-off", []))
    assert not (called_run_ids & risk_off_ids), (
        f"a Risk-off-only chunk was resolved even though it cannot contribute to a Risk-on cohort — "
        f"called run ids {sorted(called_run_ids)} intersect Risk-off ids {sorted(risk_off_ids)}"
    )


def test_factor_regime_observations_zero_n_cohort_is_honest_empty(chunked_accumulator_engine):
    """An as_of before any snapshot resolves an honest empty regime cohort — never a crash, never a
    fabricated member."""
    cfg = _cfg_batch(2)
    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
    with Session(chunked_accumulator_engine) as session:
        members = research_module._factor_regime_observations(
            session, factor, H, date(2024, 1, 1), "Risk-on", cfg=cfg
        )
    assert members == []
