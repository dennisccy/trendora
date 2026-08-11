"""Regime Lab (iter-53, J-110) — cross-sectional realized forward returns + paired max-drawdown grouped
(a) by the six canonical regime LABELS and (b) into deciles of the 0–100 regime SCORE, at EVERY config
horizon at once as paired (mean forward-return, mean max-drawdown) columns, with the rank-IC of the regime
score vs the forward return per horizon. A read-only re-surfacing of ALREADY-STORED canonical values
(stored `forward_returns.realized_return` + the J-86 `max_drawdown`, and the stored `ScannerRun`
`regime_score`/`regime_label`, J-80) — it recomputes nothing.

NON-NEGOTIABLE contracts proven here:

  - **Single computation path / count-coherence keystone (Single source of truth).** The all-horizons
    `compute_regime_lab` per-(bucket, horizon) mean return / mean max-drawdown / n / rank-IC is byte-identical
    to a reference aggregation over `_regime_lab_observation_set(horizon, view, as_of)` — the SAME single-
    horizon builder the samples drill-down reads — across BOTH Episodes/Pooled views and BOTH All-history/
    As-of scopes. The batched all-horizons builder and the single-horizon builder therefore produce
    byte-identical per-horizon observation sets (no second derivation, no number recomputed).
  - **Read verbatim (No recompute in the read path).** by-label means are independently re-derived with plain
    Python `statistics.mean` over the stored returns (proving the engine reads, not recomputes); the by-label
    mean max-drawdown is the mean over only members with a stored drawdown (NA-honest, never a fabricated 0).
  - **Cache schema token (iter-38/39/44).** A pre-iter-53 OLD-SHAPE cache row (keyed by the bare
    `_dataset_version`) is a guaranteed MISS and is PRUNED on the next write — tested against a real already-
    populated old-schema row, not a fresh compute. HIT == MISS == fresh; refreshes on a real dataset change.
  - **Bounded read (J-105 / iter-46/47/48 OOM lesson; iter-59 per-horizon bound).** The shared pool builder
    issues ONE batched heavy read per call, `yield_per`-streamed (no unbounded `.all()`), ordering the
    ScannerResult side by `(run_id, id)`; chunk-independent (batch=1 vs huge). Since iter-59
    `compute_regime_lab` calls that builder with a SINGLE-element horizons list inside its per-horizon loop
    (build → process → release one horizon at a time) instead of retaining every horizon's pool at once —
    byte-identically, per the builder's own single-horizon/all-horizons-slice identity, and with each
    horizon's rows committed to the shared accumulators in ONE atomic step only on success, so a horizon
    that degrades contributes exactly one honest `unavailable` entry and never a duplicate.
  - **Samples count-coherence (J-51/J-65).** Every displayable bucket's samples `total` equals its published
    n in BOTH views and BOTH scopes; every displayable bucket resolves without a 4xx; an unknown label /
    out-of-range decile / unknown view raises (an honest 4xx at the API).

The math runs on tiny hand-built in-memory data (the lab READS stored rows — no engine run needed). The
fixture has 4 runs at consecutive monthly dates with DISTINCT regime scores + labels, tickers split so the
Episodes collapse differs from Pooled, FRs at several horizons (with a paired max_drawdown), a horizon with
NO FRs (empty/NA), and a horizon whose FRs carry NO max_drawdown (NA-honest mean-MDD).
"""
from __future__ import annotations

import inspect
import json
from datetime import date, datetime, timezone
from statistics import mean

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import data_manager
from app.engine.research import (
    _REGIME_LAB_SCHEMA_TOKEN,
    _REGIME_LAB_SUBJECT,
    VIEW_EPISODES,
    VIEW_POOLED,
    _collapse_to_episodes,
    _dataset_version,
    _deciles,
    _rank_ic,
    _regime_lab_members_by_horizon,
    _regime_lab_observation_set,
    _regime_score_ordered,
    _run_position_index,
    compute_regime_lab,
    regime_lab_cached,
)
from app.engine.samples import KIND_REGIME_LAB, compute_samples
from app.models import EventStudyCache, ForwardReturn, ScannerResult, ScannerRun

DEFAULT_H = 20  # config walk_forward.default_horizon
POPULATED_HORIZONS = (1, 5, 20)  # horizons with FRs AND a paired max_drawdown
NO_MDD_HORIZON = 60  # has FRs but max_drawdown=None (NA-honest mean-MDD leg)
EMPTY_HORIZON = 10  # no FRs at all (empty decile / label rows -> NA return AND NA drawdown)

# The fixture's four runs: (asof_date, regime_score, regime_label). Distinct scores so the decile split has
# spread; distinct labels (all in config.regime.labels) so the by-label table has multiple populated rows.
RUNS = [
    (date(2025, 1, 10), 10.0, "Risk-off"),
    (date(2025, 2, 10), 30.0, "Defensive"),
    (date(2025, 3, 10), 60.0, "Risk-on"),
    (date(2025, 4, 10), 90.0, "Strong risk-on"),
]


def _utc() -> datetime:
    return datetime.now(timezone.utc)


def _add_run(session: Session, asof: date, regime_score: float, regime_label: str) -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=_utc(), provider="seed", benchmark="SPY",
        regime_score=regime_score, regime_label=regime_label, regime_components_json="[]",
        new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _add_result(session, run_id, ticker, rank, sector="Technology"):
    session.add(ScannerResult(
        run_id=run_id, ticker=ticker, name=ticker, sector=sector,
        leadership_score=50.0, leadership_bucket="C",
        entry_quality_score=50.0, entry_quality_bucket="C",
        risk_score=50.0, risk_bucket="C",
        setup_status="Breakout-watch", rank=rank, record_json="{}",
    ))


def _add_fr(session, run_id, symbol, ret, horizon, mdd):
    session.add(ForwardReturn(
        run_id=run_id, symbol=symbol, horizon=horizon, asof_date=date(2025, 1, 1),
        entry_close=100.0, measured_date=date(2025, 2, 1), realized_return=ret, max_drawdown=mdd,
    ))


@pytest.fixture()
def lab_engine(tmp_path):
    """4 runs at consecutive monthly dates, each a DISTINCT regime score + label. Tickers T01..T06 appear in
    runs 1+2 (consecutive ordinals -> ONE episode at run 1); T07..T12 appear in runs 3+4 (-> ONE episode at
    run 3). So the Episodes collapse keeps strictly fewer than Pooled AND spans two labels. Each (run,ticker)
    has FRs at the populated horizons (paired NEGATIVE max_drawdown), an FR with NO max_drawdown at horizon
    60 (NA-honest), and NO FR at horizon 10 (empty/NA)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'regime_lab.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        runs = [_add_run(session, asof, score, label) for asof, score, label in RUNS]
        # T01..T06 -> runs[0], runs[1] (consecutive) ; T07..T12 -> runs[2], runs[3] (consecutive)
        membership = {
            **{f"T{i:02d}": (runs[0], runs[1]) for i in range(1, 7)},
            **{f"T{i:02d}": (runs[2], runs[3]) for i in range(7, 13)},
        }
        for ticker, run_pair in membership.items():
            i = int(ticker[1:])
            for run in run_pair:
                _add_result(session, run.id, ticker, rank=i)
                for h in POPULATED_HORIZONS:
                    _add_fr(session, run.id, ticker, ret=(i - 6) / 100.0 * h + run.id / 1000.0,
                            horizon=h, mdd=-(i / 200.0))
                _add_fr(session, run.id, ticker, ret=(i - 6) / 50.0, horizon=NO_MDD_HORIZON, mdd=None)
        session.commit()
    return engine


def _cfg_batch(batch: int):
    cfg = load_config()
    return cfg.model_copy(update={"research": cfg.research.model_copy(update={"read_batch_size": batch})})


def _bytes(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=str)


# ==================================================================================================
# Reference aggregation over the single-horizon `_regime_lab_observation_set` (the samples builder)
# ==================================================================================================
def _reference(session, cfg, view, as_of):
    """A reference Regime-Lab payload computed over the SINGLE-horizon `_regime_lab_observation_set` builder
    (the one the samples drill-down reads). by-label means are independently re-derived with plain Python
    `statistics.mean`; by-decile reuses the SAME `_regime_score_ordered`/`_deciles` quantile machinery (the
    count-coherence keystone — proving the batched all-horizons builder agrees with the single-horizon one)."""
    wf = cfg.walk_forward
    fl = cfg.research.factor_lab
    horizons = list(wf.horizons)
    labels = list(cfg.regime.labels)

    by_label = []
    for label in labels:
        by_horizon = []
        for h in horizons:
            obs = _regime_lab_observation_set(session, h, view, as_of)
            lm = [m for m in obs if m["regime_label"] == label]
            returns = [m["return"] for m in lm]
            mdds = [m["max_drawdown"] for m in lm if m["max_drawdown"] is not None]
            by_horizon.append({
                "horizon": h, "n": len(lm), "low_sample": len(lm) < wf.min_sample,
                "mean_return": mean(returns) if returns else None,
                "mean_max_drawdown": mean(mdds) if mdds else None,
            })
        by_label.append({"regime": label, "by_horizon": by_horizon})

    decile_rows_by_h = {}
    rank_ic_by_horizon = []
    for h in horizons:
        obs = _regime_lab_observation_set(session, h, view, as_of)
        ordered = _regime_score_ordered(obs)
        decile_rows_by_h[h] = _deciles(ordered, fl.deciles, wf.min_sample)
        rank_ic_by_horizon.append({
            "horizon": h, "rank_ic": _rank_ic([(o["factor"], o["return"]) for o in ordered]),
        })
    by_decile = []
    for d in range(1, fl.deciles + 1):
        by_horizon = []
        for h in horizons:
            drow = decile_rows_by_h[h][d - 1]
            by_horizon.append({
                "horizon": h, "n": drow["n"], "low_sample": drow["low_sample"],
                "mean_return": drow["mean_return"], "mean_max_drawdown": drow["mean_max_drawdown"],
                "score_min": drow["factor_min"], "score_max": drow["factor_max"],
            })
        by_decile.append({"decile": d, "by_horizon": by_horizon})

    return {"by_label": by_label, "by_decile": by_decile, "rank_ic_by_horizon": rank_ic_by_horizon}


# ==================================================================================================
# 1. Byte-identity vs the reference over the single-horizon builder (load-bearing, count-coherence keystone)
# ==================================================================================================
@pytest.mark.parametrize("view", [VIEW_EPISODES, VIEW_POOLED])
@pytest.mark.parametrize("as_of", [None, date(2025, 2, 15)])
def test_compute_is_byte_identical_to_reference_over_observation_set(lab_engine, view, as_of):
    """For BOTH views and BOTH scopes, compute_regime_lab's by_label / by_decile / rank_ic_by_horizon are
    byte-identical to the reference aggregation over the single-horizon `_regime_lab_observation_set` — so
    the batched all-horizons builder and the single-horizon (samples) builder produce byte-identical per-
    horizon observation sets (Single source of truth; the count-coherence keystone)."""
    cfg = load_config()
    with Session(lab_engine) as session:
        got = compute_regime_lab(session, cfg, view=view, as_of=as_of)
        ref = _reference(session, cfg, view, as_of)
        assert _bytes(got["by_label"]) == _bytes(ref["by_label"]), "by-label drift"
        assert _bytes(got["by_decile"]) == _bytes(ref["by_decile"]), "by-decile drift"
        assert _bytes(got["rank_ic_by_horizon"]) == _bytes(ref["rank_ic_by_horizon"]), "rank-IC drift"


def test_top_level_metadata_matches_config_and_has_no_single_horizon(lab_engine):
    """The payload echoes the config-driven horizons / default_horizon / decile count / min_sample +
    the config regime-label vocabulary + the honest labels, carries NO single `horizon` (the view shows
    every horizon at once), and exposes exactly the all-horizons paired shape (no fabricated field)."""
    cfg = load_config()
    fl = cfg.research.factor_lab
    wf = cfg.walk_forward
    with Session(lab_engine) as session:
        payload = compute_regime_lab(session, cfg, view=VIEW_POOLED)
    assert "horizon" not in payload  # the all-horizons view has no single served horizon
    assert payload["view"] == VIEW_POOLED
    assert payload["horizons"] == list(wf.horizons)
    assert payload["default_horizon"] == wf.default_horizon
    assert payload["deciles_count"] == fl.deciles
    assert payload["min_sample"] == wf.min_sample
    assert payload["regime_labels"] == list(cfg.regime.labels)
    assert payload["asof_date"] is None
    assert "survivorship" in payload["survivorship_bias"].lower()
    assert "not a predictive model" in payload["descriptive_caveat"].lower()
    # one by-label row per configured regime label, in config order; one by-decile row D1..D`deciles`.
    assert [r["regime"] for r in payload["by_label"]] == list(cfg.regime.labels)
    assert [r["decile"] for r in payload["by_decile"]] == list(range(1, fl.deciles + 1))
    assert [r["horizon"] for r in payload["rank_ic_by_horizon"]] == list(wf.horizons)
    for r in payload["by_label"]:
        assert [b["horizon"] for b in r["by_horizon"]] == list(wf.horizons)
        for b in r["by_horizon"]:
            assert set(b) == {"horizon", "n", "low_sample", "mean_return", "mean_max_drawdown"}
    for r in payload["by_decile"]:
        for b in r["by_horizon"]:
            assert set(b) == {
                "horizon", "n", "low_sample", "mean_return", "mean_max_drawdown", "score_min", "score_max",
            }


# ==================================================================================================
# 2. The figures are READ verbatim (independent manual aggregation) + the views/scopes really filter
# ==================================================================================================
def test_by_label_means_match_independent_manual_aggregation(lab_engine):
    """Pooled, all-history: each populated by-label cell's mean_return equals a plain-Python mean over the
    stored returns of that label's members at that horizon, and its mean_max_drawdown the mean over only
    members with a stored drawdown — proving the engine READS the stored values (No recompute)."""
    cfg = load_config()
    with Session(lab_engine) as session:
        payload = compute_regime_lab(session, cfg, view=VIEW_POOLED)
        rows_by_label = {r["regime"]: r for r in payload["by_label"]}
        saw_populated = False
        for h in POPULATED_HORIZONS:
            obs = _regime_lab_observation_set(session, h, VIEW_POOLED, None)
            for label in cfg.regime.labels:
                lm = [m for m in obs if m["regime_label"] == label]
                cell = next(b for b in rows_by_label[label]["by_horizon"] if b["horizon"] == h)
                assert cell["n"] == len(lm)
                if lm:
                    assert cell["mean_return"] == pytest.approx(mean(m["return"] for m in lm))
                    assert cell["mean_max_drawdown"] == pytest.approx(
                        mean(m["max_drawdown"] for m in lm)
                    )
                    assert cell["mean_max_drawdown"] < 0  # a real negative drawdown, not a fabricated 0
                    saw_populated = True
                else:
                    assert cell["mean_return"] is None and cell["mean_max_drawdown"] is None
        assert saw_populated, "fixture has no populated by-label cell — the read-verbatim proof is vacuous"


def test_no_mdd_and_empty_horizons_are_honest_na(lab_engine):
    """The drawdown-less horizon (FRs but no stored max_drawdown) carries a REAL mean_return but NA
    mean_max_drawdown on populated cells (never a fabricated 0); the empty horizon (no FRs) carries NA
    return AND NA drawdown with n==0 everywhere (no fabricated bucket)."""
    cfg = load_config()
    with Session(lab_engine) as session:
        payload = compute_regime_lab(session, cfg, view=VIEW_POOLED)

    def cell(table_row, h):
        return next(b for b in table_row["by_horizon"] if b["horizon"] == h)

    populated = False
    for row in payload["by_label"] + payload["by_decile"]:
        no_mdd = cell(row, NO_MDD_HORIZON)
        if no_mdd["n"] > 0:
            assert no_mdd["mean_return"] is not None, "return wrongly NA'd on the no-mdd horizon"
            assert no_mdd["mean_max_drawdown"] is None, "fabricated MDD where none stored"
            populated = True
        empty = cell(row, EMPTY_HORIZON)
        assert empty["n"] == 0 and empty["mean_return"] is None and empty["mean_max_drawdown"] is None
    assert populated, "no-mdd horizon never populated — the NA-honest leg is vacuous"


def test_episodes_collapse_is_fewer_than_pooled_and_as_of_shrinks(lab_engine):
    """The Episodes view keeps strictly fewer observations than Pooled (the first-trigger collapse), and the
    As-of FILTER strictly shrinks the observation set (n decreases) — proving the view + scope really filter,
    never fabricate."""
    cfg = load_config()
    with Session(lab_engine) as session:
        pooled_total = sum(
            len(_regime_lab_observation_set(session, h, VIEW_POOLED, None)) for h in POPULATED_HORIZONS
        )
        episodes_total = sum(
            len(_regime_lab_observation_set(session, h, VIEW_EPISODES, None)) for h in POPULATED_HORIZONS
        )
        asof_total = sum(
            len(_regime_lab_observation_set(session, h, VIEW_POOLED, date(2025, 2, 15)))
            for h in POPULATED_HORIZONS
        )
    assert 0 < episodes_total < pooled_total, "episode collapse did not reduce the set"
    assert 0 < asof_total < pooled_total, "as-of did not shrink the observation set"


# ==================================================================================================
# 3. Cache: HIT == MISS == fresh; schema token makes an old-schema row a MISS and prunes it; refresh
# ==================================================================================================
@pytest.mark.parametrize("view", [VIEW_EPISODES, VIEW_POOLED])
@pytest.mark.parametrize("as_of", [None, date(2025, 2, 15)])
def test_cache_hit_equals_miss_equals_fresh(lab_engine, view, as_of):
    cfg = load_config()
    with Session(lab_engine) as session:
        fresh = compute_regime_lab(session, cfg, view=view, as_of=as_of)
        cached_miss = regime_lab_cached(session, cfg, view=view, as_of=as_of)  # populates the cache
        cached_hit = regime_lab_cached(session, cfg, view=view, as_of=as_of)   # served from the cache row
        assert _bytes(cached_miss) == _bytes(fresh)
        assert _bytes(cached_hit) == _bytes(fresh)
        rows = session.exec(
            select(EventStudyCache).where(
                EventStudyCache.subject == _REGIME_LAB_SUBJECT,
                EventStudyCache.view == view,
            )
        ).all()
        assert len(rows) == 1  # exactly one current-shape row for this (subject, view, asof_key)


def test_episodes_and_pooled_cache_rows_do_not_collide(lab_engine):
    """The cache keys on the actual view, so the episodes and pooled payloads never collide (distinct rows,
    distinct payloads)."""
    cfg = load_config()
    with Session(lab_engine) as session:
        ep = regime_lab_cached(session, cfg, view=VIEW_EPISODES)
        po = regime_lab_cached(session, cfg, view=VIEW_POOLED)
        assert ep["view"] == VIEW_EPISODES and po["view"] == VIEW_POOLED
        assert _bytes(ep["by_label"]) != _bytes(po["by_label"]), "episodes/pooled collapsed to one payload"
        rows = session.exec(
            select(EventStudyCache).where(EventStudyCache.subject == _REGIME_LAB_SUBJECT)
        ).all()
        assert {r.view for r in rows} == {VIEW_EPISODES, VIEW_POOLED}


def test_pre_iter53_old_schema_row_is_a_miss_and_is_pruned(lab_engine):
    """An already-populated OLD-SCHEMA cache row (keyed by the BARE `_dataset_version` WITHOUT the schema
    token) is never hit (the read computes the schema-token-folded stamp) and is PRUNED on the next write —
    so the cache can never serve the stale old-shape figure (iter-38/39/44). The schema-token MISS-then-
    populate proof against a REAL already-populated row, not a fresh compute."""
    cfg = load_config()
    with Session(lab_engine) as session:
        base_version = _dataset_version(session)  # the pre-iter-53 stamp (no schema token)
        session.add(EventStudyCache(
            subject=_REGIME_LAB_SUBJECT, view=VIEW_POOLED, asof_key="all",
            dataset_version=base_version, horizon=cfg.walk_forward.default_horizon,
            payload_json=json.dumps({"sentinel": "old-shape-must-not-be-served", "by_label": []}),
            created_at=_utc(),
        ))
        session.commit()

        served = regime_lab_cached(session, cfg, view=VIEW_POOLED)
        fresh = compute_regime_lab(session, cfg, view=VIEW_POOLED)
        assert _bytes(served) == _bytes(fresh), "served the stale old-schema cached payload"
        assert "sentinel" not in served
        assert served["by_label"], "served an empty old-shape table"

        remaining = session.exec(
            select(EventStudyCache).where(EventStudyCache.subject == _REGIME_LAB_SUBJECT)
        ).all()
        token_version = f"{base_version}-{_REGIME_LAB_SCHEMA_TOKEN}"
        assert all(r.dataset_version == token_version for r in remaining)
        assert any(r.dataset_version == token_version for r in remaining)


def test_cache_refreshes_after_dataset_change(lab_engine):
    """The cache REFRESHES after a dataset change: cache a payload, add a snapshot + forward return (bumping
    the dataset-version stamp), and the next read returns the UPDATED aggregate, not the stale one."""
    cfg = load_config()
    with Session(lab_engine) as session:
        before = regime_lab_cached(session, cfg, view=VIEW_POOLED)
        before_n = next(
            b for r in before["by_label"] if r["regime"] == "Risk-on"
            for b in r["by_horizon"] if b["horizon"] == DEFAULT_H
        )["n"]
        v_before = _dataset_version(session)

        new = _add_run(session, date(2025, 5, 10), 65.0, "Risk-on")
        _add_result(session, new.id, "Z01", rank=1)
        _add_fr(session, new.id, "Z01", ret=0.07, horizon=DEFAULT_H, mdd=-0.03)
        session.commit()
        assert _dataset_version(session) != v_before

        after = regime_lab_cached(session, cfg, view=VIEW_POOLED)
        after_n = next(
            b for r in after["by_label"] if r["regime"] == "Risk-on"
            for b in r["by_horizon"] if b["horizon"] == DEFAULT_H
        )["n"]
        assert after_n == before_n + 1, "cache served a stale (pre-add) figure"
        fresh = compute_regime_lab(session, cfg, view=VIEW_POOLED)
        assert _bytes(after) == _bytes(fresh)


# ==================================================================================================
# 4. Bounded read (J-105): one heavy read, yield_per-streamed, (run_id, id)-ordered, chunk-independent
# ==================================================================================================
def test_shared_pool_read_is_bounded_and_run_id_id_ordered():
    """Source-level guard (iter-46/47/48 OOM lesson): the shared pool builder streams with `yield_per`, orders
    the ScannerResult side by `(run_id, id)` (rides `ix_scanner_results_run_id` — no temp B-tree), and
    materializes NO unbounded `.all()` over the heavy tables."""
    src = inspect.getsource(_regime_lab_members_by_horizon)
    assert "yield_per" in src, "shared pool must stream with yield_per (bounded read)"
    assert ".order_by(ScannerResult.run_id, ScannerResult.id)" in src, "must order by (run_id, id)"
    # the real materialization call is `session.exec(...).all()` -> `).all()`; only code, never the docstring.
    assert ").all()" not in src, "shared pool must not materialize an unbounded .all()"


@pytest.mark.parametrize("view", [VIEW_EPISODES, VIEW_POOLED])
@pytest.mark.parametrize("as_of", [None, date(2025, 2, 15)])
def test_chunk_independent(lab_engine, view, as_of):
    """The full payload is byte-identical under read_batch_size=1 vs a huge batch — the stream changes peak
    memory only, never a value or an ordering."""
    with Session(lab_engine) as session:
        small = compute_regime_lab(session, _cfg_batch(1), view=view, as_of=as_of)
        big = compute_regime_lab(session, _cfg_batch(1_000_000), view=view, as_of=as_of)
        assert _bytes(small) == _bytes(big), f"payload differs by batch (view={view}, as_of={as_of})"


def test_single_horizon_builder_byte_identical_to_all_horizons_slice(lab_engine):
    """The single-horizon builder call (`_regime_lab_members_by_horizon([h])[h]`, as the samples drill-down
    uses) is byte-identical to that horizon's slice of the all-horizons build — the property count-coherence
    relies on (the extra streamed results for other-horizon-only runs are dropped by the per-horizon gate)."""
    cfg = load_config()
    horizons = list(cfg.walk_forward.horizons)
    with Session(lab_engine) as session:
        allp = _regime_lab_members_by_horizon(session, horizons, None, cfg=cfg)
        for h in horizons:
            one = _regime_lab_members_by_horizon(session, [h], None, cfg=cfg)[h]
            assert _bytes(one) == _bytes(allp[h]), f"single vs all-horizons builder drift @h={h}"


# ==================================================================================================
# 5. Samples count-coherence (J-51/J-65): total == published n in BOTH views + BOTH scopes; all resolve
# ==================================================================================================
@pytest.mark.parametrize("view", [VIEW_EPISODES, VIEW_POOLED])
@pytest.mark.parametrize("as_of", [None, date(2025, 2, 15)])
def test_samples_count_coherent_for_every_bucket(lab_engine, view, as_of):
    """The samples drill-down for EVERY displayable Regime-Lab bucket — each regime label, each regime-score
    decile, at EVERY horizon — has a `total` equal to the view's published n, in BOTH Episodes/Pooled and
    BOTH All-history/As-of, including NA/empty buckets (n==0 -> an honest empty cohort, never a 4xx)."""
    cfg = load_config()
    horizons = list(cfg.walk_forward.horizons)
    with Session(lab_engine) as session:
        payload = compute_regime_lab(session, cfg, view=view, as_of=as_of)
        checked = 0
        for row in payload["by_label"]:
            for b in row["by_horizon"]:
                s = compute_samples(
                    session, kind=KIND_REGIME_LAB, horizon=b["horizon"], config=cfg, as_of=as_of,
                    slice_kind="label", regime=row["regime"], view=view,
                )
                assert s["total"] == b["n"], f"label coherence drift {row['regime']}@{b['horizon']}"
                assert len(s["rows"]) == b["n"]
                checked += 1
        for row in payload["by_decile"]:
            for b in row["by_horizon"]:
                s = compute_samples(
                    session, kind=KIND_REGIME_LAB, horizon=b["horizon"], config=cfg, as_of=as_of,
                    slice_kind="decile", decile=row["decile"], view=view,
                )
                assert s["total"] == b["n"], f"decile coherence drift D{row['decile']}@{b['horizon']}"
                assert len(s["rows"]) == b["n"]
                checked += 1
        expected = len(horizons) * (len(cfg.regime.labels) + cfg.research.factor_lab.deciles)
        assert checked == expected


def test_samples_rows_carry_label_and_score_and_return(lab_engine):
    """A populated decile drill-down row carries the stored regime label + regime score + the realized
    forward return (read VERBATIM), and its snapshot date resolves — so a drill-down is never a bare count."""
    cfg = load_config()
    with Session(lab_engine) as session:
        payload = compute_regime_lab(session, cfg, view=VIEW_POOLED)
        # find a populated (decile, horizon) bucket.
        target = None
        for row in payload["by_decile"]:
            for b in row["by_horizon"]:
                if b["n"] > 0 and b["horizon"] in POPULATED_HORIZONS:
                    target = (row["decile"], b["horizon"], b["n"])
                    break
            if target:
                break
        assert target, "no populated decile bucket to drill into"
        decile, h, n = target
        s = compute_samples(
            session, kind=KIND_REGIME_LAB, horizon=h, config=cfg,
            slice_kind="decile", decile=decile, view=VIEW_POOLED,
        )
        assert s["total"] == n and len(s["rows"]) == n
        r0 = s["rows"][0]
        assert r0["snapshot_date"] is not None
        assert r0["regime"] in cfg.regime.labels
        keys = {v["key"] for v in r0["values"]}
        assert {"regime", "regime_score"} <= keys
        assert isinstance(r0["forward_return"], float)
        assert s["cohort"]["kind"] == KIND_REGIME_LAB and s["cohort"]["slice"] == "decile"


def test_samples_invalid_selectors_raise(lab_engine):
    """An unknown regime label, an out-of-range decile, an unknown slice, and an unknown view each raise
    ValueError (the API turns these into an honest 4xx — never a silent empty 200)."""
    cfg = load_config()
    fl = cfg.research.factor_lab
    with Session(lab_engine) as session:
        with pytest.raises(ValueError):
            compute_samples(session, kind=KIND_REGIME_LAB, horizon=DEFAULT_H, config=cfg,
                            slice_kind="label", regime="Not-a-regime", view=VIEW_POOLED)
        with pytest.raises(ValueError):
            compute_samples(session, kind=KIND_REGIME_LAB, horizon=DEFAULT_H, config=cfg,
                            slice_kind="decile", decile=0, view=VIEW_POOLED)
        with pytest.raises(ValueError):
            compute_samples(session, kind=KIND_REGIME_LAB, horizon=DEFAULT_H, config=cfg,
                            slice_kind="decile", decile=fl.deciles + 1, view=VIEW_POOLED)
        with pytest.raises(ValueError):
            compute_samples(session, kind=KIND_REGIME_LAB, horizon=DEFAULT_H, config=cfg,
                            slice_kind="not-a-slice", regime="Risk-on", view=VIEW_POOLED)
        with pytest.raises(ValueError):
            compute_samples(session, kind=KIND_REGIME_LAB, horizon=DEFAULT_H, config=cfg,
                            slice_kind="label", regime="Risk-on", view="not-a-view")


def test_compute_unknown_view_raises(lab_engine):
    """compute_regime_lab rejects an unknown view (the API pre-validates -> 422)."""
    cfg = load_config()
    with Session(lab_engine) as session:
        with pytest.raises(ValueError):
            compute_regime_lab(session, cfg, view="not-a-view")


# ==================================================================================================
# 6. Memory-bounded, isolate-and-continue per horizon (ops-hardening iter-59, J-07/AG-8)
#
# The pre-iter-59 `compute_regime_lab` called `_regime_lab_members_by_horizon` ONCE for every configured
# horizon and retained every horizon's pool (then every horizon's post-episode-collapse set) simultaneously
# for the whole by-label + by-decile aggregation — the confirmed iter-58 crash frame under a concurrent
# forward-aggregate warm (VmPeak landed exactly on the declared 8192 MB ceiling, live MemoryError traceback
# naming this function). iter-59 applies the SAME proven isolate-and-continue pattern iter-46/49/50/51
# already used for the Factor Lab's `compute_factor_lab_all`: build ONE horizon's pool, aggregate it,
# release it, before the next horizon starts; a horizon that fails degrades ONLY itself.
# ==================================================================================================
def _compute_regime_lab_pinned_pre_iter59(
    session: Session, config, *, view: str = VIEW_EPISODES, as_of=None,
) -> dict:
    """A byte-for-byte copy of `compute_regime_lab`'s PRE-iter-59 by-label / by-decile / rank-IC
    aggregation — the all-horizons-retained-`pools` shape iter-58's live incident implicated — pinned here
    as the reference oracle the iter-59 per-horizon bound is proven against. Deliberately does NOT call the
    current `compute_regime_lab` (that would prove nothing). Returns only the three aggregation keys the
    bound could possibly have changed (the top-level metadata fields are untouched by the refactor)."""
    cfg = config
    wf = cfg.walk_forward
    fl = cfg.research.factor_lab
    horizons = list(wf.horizons)
    labels = list(cfg.regime.labels)

    pools = _regime_lab_members_by_horizon(session, horizons, as_of, cfg=cfg)
    run_position = _run_position_index(session, as_of) if view == VIEW_EPISODES else None
    members_by_h: dict[int, list[dict]] = {}
    for h in horizons:
        members = pools[h]
        members_by_h[h] = members if view == VIEW_POOLED else _collapse_to_episodes(members, run_position)

    by_label: list[dict] = []
    for label in labels:
        by_horizon: list[dict] = []
        for h in horizons:
            label_members = [m for m in members_by_h[h] if m["regime_label"] == label]
            returns = [m["return"] for m in label_members]
            mdds = [m["max_drawdown"] for m in label_members if m["max_drawdown"] is not None]
            n = len(label_members)
            by_horizon.append({
                "horizon": h, "n": n, "low_sample": n < wf.min_sample,
                "mean_return": mean(returns) if returns else None,
                "mean_max_drawdown": mean(mdds) if mdds else None,
            })
        by_label.append({"regime": label, "by_horizon": by_horizon})

    decile_rows_by_h: dict[int, list[dict]] = {}
    rank_ic_by_horizon: list[dict] = []
    for h in horizons:
        ordered = _regime_score_ordered(members_by_h[h])
        decile_rows_by_h[h] = _deciles(ordered, fl.deciles, wf.min_sample)
        rank_ic_by_horizon.append({
            "horizon": h, "rank_ic": _rank_ic([(o["factor"], o["return"]) for o in ordered]),
        })
    by_decile: list[dict] = []
    for d in range(1, fl.deciles + 1):
        by_horizon = []
        for h in horizons:
            drow = decile_rows_by_h[h][d - 1]
            by_horizon.append({
                "horizon": h, "n": drow["n"], "low_sample": drow["low_sample"],
                "mean_return": drow["mean_return"], "mean_max_drawdown": drow["mean_max_drawdown"],
                "score_min": drow["factor_min"], "score_max": drow["factor_max"],
            })
        by_decile.append({"decile": d, "by_horizon": by_horizon})

    return {"by_label": by_label, "by_decile": by_decile, "rank_ic_by_horizon": rank_ic_by_horizon}


@pytest.mark.parametrize("view", [VIEW_EPISODES, VIEW_POOLED])
@pytest.mark.parametrize("as_of", [None, date(2025, 2, 15)])
def test_compute_regime_lab_matches_pinned_pre_iter59_reference(lab_engine, view, as_of):
    """TC-6 — the bounded (per-horizon build-process-release) `compute_regime_lab` is byte-identical to a
    PINNED COPY of the pre-iter-59 all-horizons-retained implementation, for every horizon's by-label /
    by-decile / rank-IC figures, both views, both all-history and a historical as_of — proving the iter-59
    memory bound changed only WHEN each horizon's pool is built and released, never a value or an ordering."""
    cfg = load_config()
    with Session(lab_engine) as session:
        got = compute_regime_lab(session, cfg, view=view, as_of=as_of)
        want = _compute_regime_lab_pinned_pre_iter59(session, cfg, view=view, as_of=as_of)
        assert _bytes(got["by_label"]) == _bytes(want["by_label"]), (
            "by-label diverges from the pinned pre-iter-59 reference"
        )
        assert _bytes(got["by_decile"]) == _bytes(want["by_decile"]), (
            "by-decile diverges from the pinned pre-iter-59 reference"
        )
        assert _bytes(got["rank_ic_by_horizon"]) == _bytes(want["rank_ic_by_horizon"]), (
            "rank-IC diverges from the pinned pre-iter-59 reference"
        )


def test_compute_regime_lab_builds_one_horizon_at_a_time():
    """Source-level guard: `compute_regime_lab` no longer retains every horizon's pool simultaneously — it
    calls the shared builder with a SINGLE-element horizons list inside its per-horizon loop, so at most one
    horizon's pool is alive at once (the iter-59 memory bound)."""
    src = inspect.getsource(compute_regime_lab)
    assert "_regime_lab_members_by_horizon(session, [h]" in src, (
        "compute_regime_lab must build each horizon's pool with a single-element horizons list"
    )
    assert "_regime_lab_members_by_horizon(session, horizons" not in src, (
        "compute_regime_lab must not retain every horizon's pool via one all-horizons call"
    )


def test_compute_regime_lab_isolates_memory_pressure_per_horizon(lab_engine, monkeypatch):
    """TC-3 (fast/deterministic leg) — a MemoryError injected at the confirmed iter-58 crash frame (reached
    via the per-horizon `_fault_inject_memory_error("regime_lab")` hook, the SAME test-only convention
    `compute_factor_lab_all` uses) is caught by the per-horizon isolate-and-continue bound: THAT horizon
    alone degrades to an honest `status: "unavailable"` entry on every by-label/by-decile row and the
    rank-IC row — `compute_regime_lab` itself never raises, so a live request can still answer. Control arm
    first (env unset -> no `status`/`regime_lab_status` anywhere, proving a silently-disabled injector
    cannot pass as a green result), then the armed leg (the injector fires unconditionally on every call, so
    EVERY horizon degrades — exercising the catch under maximum, repeated, consecutive stress)."""
    cfg = load_config()

    with Session(lab_engine) as session:
        control = compute_regime_lab(session, cfg, view=VIEW_POOLED)
    assert "regime_lab_status" not in control, "control run must have no degraded horizons"
    for row in control["by_label"] + control["by_decile"]:
        for bh in row["by_horizon"]:
            assert "status" not in bh, f"control run must have no degraded entries; got {bh}"

    monkeypatch.setenv(data_manager._FAULT_INJECT_MEMORY_ERROR_ENV, "regime_lab")
    with Session(lab_engine) as session:
        payload = compute_regime_lab(session, cfg, view=VIEW_POOLED)  # must not raise

    assert payload["regime_lab_status"] == "unavailable"
    assert payload["by_label"], "the label vocabulary must still be listed even when every horizon degrades"
    assert payload["by_decile"], "the decile vocabulary must still be listed even when every horizon degrades"
    for row in payload["by_label"] + payload["by_decile"]:
        for bh in row["by_horizon"]:
            assert bh["status"] == "unavailable"
            assert bh["n"] == 0
            assert bh["mean_return"] is None and bh["mean_max_drawdown"] is None
    for r in payload["rank_ic_by_horizon"]:
        assert r["status"] == "unavailable"
        assert r["rank_ic"] == {"value": None, "n": 0}


def test_compute_regime_lab_one_horizon_non_memory_failure_degrades_only_that_horizon(
    lab_engine, monkeypatch, caplog,
):
    """iter-59, mirrors `compute_factor_lab_all`'s iter-50 audit B4 (second half): the per-horizon loop
    pairs its MemoryError catch with a broader `except Exception` so any OTHER failure from ONE horizon's
    aggregation still degrades honestly instead of raising out and 500ing the whole all-horizons response.

    Teeth: the fault fires on exactly one `_deciles` call (one specific horizon, deterministically the
    first one processed), so a handler that blanked the whole response — or no handler at all, the pre-fix
    behavior, which raises straight out of this function — fails one of the assertions below."""
    import app.engine.research as research

    cfg = load_config()
    horizons = list(cfg.walk_forward.horizons)
    assert len(horizons) >= 2, "fixture sanity: need >= 2 horizons to prove isolation"
    real_deciles = research._deciles
    calls = {"n": 0}
    fault_on_call = 1  # the first horizon processed, deterministically

    def _boom_on_one_call(ordered, n_deciles, min_sample):
        calls["n"] += 1
        if calls["n"] == fault_on_call:
            raise RuntimeError("simulated non-memory failure inside one horizon's aggregation")
        return real_deciles(ordered, n_deciles, min_sample)

    monkeypatch.setattr(research, "_deciles", _boom_on_one_call)
    with caplog.at_level("ERROR", logger="trendora.research"):
        with Session(lab_engine) as session:
            payload = compute_regime_lab(session, cfg, view=VIEW_POOLED)

    assert calls["n"] > fault_on_call, (
        "the loop stopped at the injected failure instead of continuing to the next horizon — "
        "isolate-and-continue means CONTINUE"
    )
    # iter-59 REVIEW FIX (the regression this test previously missed): the fault fires AFTER the faulted
    # horizon's by-label rows are built but BEFORE its by-decile/rank-IC rows are — exactly the window in
    # which an implementation that appended into the shared accumulators during the try would leave the
    # horizon's REAL by-label entry in place and then append a SECOND, degraded entry for the same horizon.
    # Every row must carry EXACTLY one entry per configured horizon, in configured order, degraded or not.
    for row in payload["by_label"]:
        assert [bh["horizon"] for bh in row["by_horizon"]] == horizons, (
            f"by_label row {row['regime']!r} must carry exactly one entry per horizon in config order; "
            f"got {[bh['horizon'] for bh in row['by_horizon']]!r}"
        )
    for row in payload["by_decile"]:
        assert [bh["horizon"] for bh in row["by_horizon"]] == horizons, (
            f"by_decile row D{row['decile']} must carry exactly one entry per horizon in config order; "
            f"got {[bh['horizon'] for bh in row['by_horizon']]!r}"
        )
    assert [r["horizon"] for r in payload["rank_ic_by_horizon"]] == horizons, (
        "rank_ic_by_horizon must carry exactly one entry per horizon in config order; "
        f"got {[r['horizon'] for r in payload['rank_ic_by_horizon']]!r}"
    )
    degraded_horizons = {
        bh["horizon"] for row in payload["by_label"] for bh in row["by_horizon"]
        if bh.get("status") == "unavailable"
    }
    assert degraded_horizons == {horizons[0]}, (
        f"exactly the faulted (first) horizon must degrade; got {degraded_horizons!r}"
    )
    assert payload["regime_lab_status"] == "unavailable"
    assert any(
        bh.get("status") != "unavailable" and bh["horizon"] != horizons[0] and bh["horizon"] in horizons
        for row in payload["by_label"] for bh in row["by_horizon"]
    ), "no OTHER horizon survived — the isolation is not contained, which is the failure this test forbids"
    assert "isolate-and-continue" in caplog.text, (
        "the isolated failure must be logged, never swallowed silently"
    )


def test_regime_lab_cached_never_persists_a_degraded_payload(lab_engine, monkeypatch):
    """A payload where at least one horizon degraded under memory pressure (the isolate-and-continue bound
    inside `compute_regime_lab`, which returns NORMALLY rather than raising) must NEVER be persisted to the
    cache — otherwise a LATER request under the SAME dataset-version stamp would be served this stale
    degraded payload until the next dataset change, instead of getting a fresh attempt once the memory
    pressure has actually cleared. Proven by injecting the fault for exactly one call, confirming the served
    response is honestly degraded, confirming NO EventStudyCache row was written, then clearing the fault
    and confirming the NEXT call computes fresh (not a stale degraded HIT)."""
    cfg = load_config()

    monkeypatch.setenv(data_manager._FAULT_INJECT_MEMORY_ERROR_ENV, "regime_lab")
    with Session(lab_engine) as session:
        degraded = regime_lab_cached(session, cfg, view=VIEW_POOLED)
    assert degraded["regime_lab_status"] == "unavailable", "fixture sanity: the injected fault must degrade"
    with Session(lab_engine) as session:
        rows = session.exec(
            select(EventStudyCache).where(EventStudyCache.subject == _REGIME_LAB_SUBJECT)
        ).all()
    assert rows == [], "a degraded response must never be persisted to the cache"

    monkeypatch.delenv(data_manager._FAULT_INJECT_MEMORY_ERROR_ENV, raising=False)
    with Session(lab_engine) as session:
        recovered = regime_lab_cached(session, cfg, view=VIEW_POOLED)  # must not hang, must not serve stale
    assert "regime_lab_status" not in recovered, "a follow-up call after the fault clears must compute fresh"
    with Session(lab_engine) as session:
        rows = session.exec(
            select(EventStudyCache).where(EventStudyCache.subject == _REGIME_LAB_SUBJECT)
        ).all()
    assert len(rows) == 1, "the clean recovered payload must be cached normally"
