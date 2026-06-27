"""Regime × Market-Phase/Severity × Factor 3-way decile study (iter-55, J-112) — the UNION of the Regime Lab
(J-110) and the Phase & Severity Lab (J-111) source paths, surfaced through the J-77/J-82 ranked-combination
pattern: for a SELECTED factor, a ranked combination table of `(regime-score decile, severity-score decile,
factor decile)` triples, each row carrying per EVERY config horizon the combination's mean realized forward
return + paired mean max-drawdown + n. A read-only re-surfacing of ALREADY-STORED canonical values — it
recomputes nothing:

  (a) the run's STORED `ScannerRun.regime_score` read VERBATIM (the J-80/J-110 path),
  (b) the snapshot date's SERVED 0–100 severity read VERBATIM from the `market_phase` causal timeline
      (`phase_context_by_date`, joined by snapshot date — the J-87/J-111 path, monkeypatched here to controlled
      values so the by-date join + grouping correctness is exact by construction), and
  (c) the SELECTED factor's STORED value read VERBATIM off the `ScannerResult` (the Factor-Lab source).

NON-NEGOTIABLE contracts proven here:

  - **Single computation path / count-coherence keystone (Single source of truth).** The all-horizons
    `compute_regime_phase_factor_study` per-(combination, horizon) mean return / mean max-drawdown / n is
    byte-identical to a reference aggregation over `_regime_phase_factor_observation_set(horizon, view, factor,
    as_of)` + `_assign_triple_deciles` — the SAME single-horizon builder + decile assignment the samples
    drill-down reads — across BOTH Episodes/Pooled views, BOTH All-history/As-of scopes, AND at least two
    distinct factors. The batched all-horizons builder and the single-horizon builder produce byte-identical
    per-horizon observation sets (no second derivation, no number recomputed).
  - **Read-verbatim provenance (No recompute in the read path).** Each observation's tagged regime_score equals
    the stored `ScannerRun.regime_score`; its tagged severity equals the SERVED `market_phase` timeline value
    for ITS snapshot date (asserted against `phase_context_by_date`, NOT a re-derivation); its tagged factor
    value equals the stored factor value — with the correct by-snapshot-date join; a warm-up-head date with no
    timeline value yields an honest unclassified (None) severity — never a fabricated value.
  - **Cache schema token + market-phase stamp + per-factor key (iter-38/39/44 + the J-111 twist).** A
    pre-iter-55 OLD-SHAPE cache row (keyed by the bare `_dataset_version`) is a guaranteed MISS and is PRUNED —
    tested against a real already-populated row, not a fresh compute. A real HIT returns byte-identical figures.
    The cache refreshes on a real dataset change AND on a market-phase `SCHEMA_VERSION`/dataset-stamp change,
    and distinguishes distinct `factor` values (no cross-factor cache bleed).
  - **Bounded read (J-105 / iter-46/47/48 OOM lesson).** The shared pool is built ONCE for all horizons (one
    heavy read), `yield_per`-streamed (no unbounded `.all()`), ordering the ScannerResult side by
    `(run_id, id)`. Chunk-independent (batch=1 vs huge).
  - **Samples count-coherence (J-51/J-65).** Every emitted combination's samples `total` equals its published n
    in BOTH views and BOTH scopes; every emitted combination resolves without a 4xx; an unknown factor /
    out-of-range decile / unknown view raises (an honest 4xx at the API).

The math runs on tiny hand-built in-memory data (the study READS stored rows — no engine run needed). The
fixture has 5 runs at consecutive monthly dates: ONE warm-up-head run with NO served severity (unclassified
observations) + four runs each a DISTINCT served severity + a distinct stored regime score, tickers split so
the Episodes collapse differs from Pooled, FRs at several horizons (with a paired max_drawdown), a horizon with
NO FRs (empty/NA), and a horizon whose FRs carry NO max_drawdown (NA-honest). Two distinct factors are stored
on each result (two typed score columns) so the byte-identity + per-factor-cache proofs are not vacuous.
"""
from __future__ import annotations

import inspect
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from statistics import mean

import pytest
from sqlmodel import Session, select

import app.engine.market_phase as market_phase
from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.research import (
    _REGIME_PHASE_FACTOR_SCHEMA_TOKEN,
    _REGIME_PHASE_FACTOR_SUBJECT,
    VIEW_EPISODES,
    VIEW_POOLED,
    _assign_triple_deciles,
    _dataset_version,
    _regime_phase_factor_cache_subject,
    _regime_phase_factor_cache_version,
    _regime_phase_factor_members_by_horizon,
    _regime_phase_factor_observation_set,
    _rpf_resolve_factor,
    compute_regime_phase_factor_study,
    regime_phase_factor_cached,
)
from app.engine.samples import KIND_REGIME_PHASE_FACTOR, compute_samples
from app.models import EventStudyCache, ForwardReturn, ScannerResult, ScannerRun

DEFAULT_H = 20  # config walk_forward.default_horizon
POPULATED_HORIZONS = (1, 5, 20)  # horizons with FRs AND a paired max_drawdown
NO_MDD_HORIZON = 60  # has FRs but max_drawdown=None (NA-honest mean-MDD leg)
EMPTY_HORIZON = 10  # no FRs at all (empty combination rows -> NA return AND NA drawdown)

# The two SELECTED factors the study + samples are exercised over — typed score columns so the stored value is
# read verbatim off the ScannerResult (never NULL). Distinct enough that the factor-decile partition differs.
FACTOR_A = "leadership_score"
FACTOR_B = "entry_quality_score"

WARMUP = date(2025, 1, 10)  # the warm-up head: NO served severity (unclassified observations)
# The four classified runs: (asof_date, served 0–100 severity, stored regime score). Distinct severities AND
# distinct regime scores so both the severity-decile and regime-decile splits have spread.
CLASSIFIED_RUNS = [
    (date(2025, 2, 10), 85.0, 20.0),
    (date(2025, 3, 10), 55.0, 45.0),
    (date(2025, 4, 10), 10.0, 80.0),
    (date(2025, 5, 10), 35.0, 60.0),
]
# The served market-phase timeline (monkeypatched) — keyed by ISO date -> {phase, severity, p_bear}. The
# warm-up-head run is deliberately ABSENT (no entry) so its observations tag unclassified severity (None).
PHASE_CTX = {
    asof.isoformat(): {"phase": "Bear", "severity": severity, "p_bear": 0.0}
    for asof, severity, _score in CLASSIFIED_RUNS
}
REGIME_SCORE_BY_DATE = {asof.isoformat(): score for asof, _sev, score in CLASSIFIED_RUNS}


def _utc() -> datetime:
    return datetime.now(timezone.utc)


def _add_run(session: Session, asof: date, regime_score: float) -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=_utc(), provider="seed", benchmark="SPY",
        regime_score=regime_score, regime_label="Risk-on", regime_components_json="[]",
        new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _add_result(session, run_id, ticker, rank, lead, eq, sector="Technology"):
    # the two SELECTED factors are typed score columns (FACTOR_A=leadership_score, FACTOR_B=entry_quality_score)
    session.add(ScannerResult(
        run_id=run_id, ticker=ticker, name=ticker, sector=sector,
        leadership_score=lead, leadership_bucket="C",
        entry_quality_score=eq, entry_quality_bucket="C",
        risk_score=50.0, risk_bucket="C",
        setup_status="Breakout-watch", rank=rank, record_json="{}",
    ))


def _add_fr(session, run_id, symbol, ret, horizon, mdd):
    session.add(ForwardReturn(
        run_id=run_id, symbol=symbol, horizon=horizon, asof_date=date(2025, 1, 1),
        entry_close=100.0, measured_date=date(2025, 2, 1), realized_return=ret, max_drawdown=mdd,
    ))


@pytest.fixture()
def lab_engine(tmp_path, monkeypatch):
    """5 runs at consecutive monthly dates: runs[0] is the warm-up head (NO served severity), runs[1..4] each a
    DISTINCT served severity + a distinct stored regime score. Tickers T01..T06 appear in runs 1+2 (consecutive
    ordinals -> ONE episode at run 1); T07..T12 appear in runs 3+4 (-> ONE episode at run 3); W01..W03 appear in
    the warm-up-head run only (-> unclassified-severity observations, dropped from every displayed combination
    but present in the raw pool). So the Episodes collapse keeps strictly fewer than Pooled AND the as-of FILTER
    shrinks the set. Each (run, ticker) has FRs at the populated horizons (paired NEGATIVE max_drawdown), an FR
    with NO max_drawdown at horizon 60 (NA-honest), and NO FR at horizon 10 (empty/NA). The served `market_phase`
    timeline is monkeypatched to PHASE_CTX (honoring the as-of FILTER)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'regime_phase_factor.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        warmup = _add_run(session, WARMUP, regime_score=50.0)
        classified = [_add_run(session, asof, score) for asof, _sev, score in CLASSIFIED_RUNS]
        membership = {
            **{f"T{i:02d}": (classified[0], classified[1]) for i in range(1, 7)},
            **{f"T{i:02d}": (classified[2], classified[3]) for i in range(7, 13)},
            **{f"W{i:02d}": (warmup,) for i in range(1, 4)},  # warm-up-head only (unclassified)
        }
        for ticker, run_tuple in membership.items():
            i = int(ticker[1:])
            for run in run_tuple:
                # the two factor values spread across tickers (distinct partitions for FACTOR_A vs FACTOR_B)
                _add_result(session, run.id, ticker, rank=i, lead=float(i), eq=float(100 - i))
                for h in POPULATED_HORIZONS:
                    _add_fr(session, run.id, ticker, ret=(i - 6) / 100.0 * h + run.id / 1000.0,
                            horizon=h, mdd=-(i / 200.0))
                _add_fr(session, run.id, ticker, ret=(i - 6) / 50.0, horizon=NO_MDD_HORIZON, mdd=None)
        session.commit()

    def _fake_phase_ctx(session, as_of=None, config=None):
        # honor the as-of FILTER exactly like the real accessor (only dates <= as_of)
        if as_of is None:
            return {d: dict(v) for d, v in PHASE_CTX.items()}
        return {d: dict(v) for d, v in PHASE_CTX.items() if date.fromisoformat(d) <= as_of}

    # `_regime_phase_factor_members_by_horizon` lazily imports `phase_context_by_date` FROM the market_phase
    # module at call time, so the patch must target the source module (not the research namespace).
    monkeypatch.setattr(market_phase, "phase_context_by_date", _fake_phase_ctx)
    return engine


def _cfg_batch(batch: int):
    cfg = load_config()
    return cfg.model_copy(update={"research": cfg.research.model_copy(update={"read_batch_size": batch})})


def _bytes(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=str)


# ==================================================================================================
# Reference aggregation over the single-horizon `_regime_phase_factor_observation_set` (samples builder)
# ==================================================================================================
def _reference_rows(session, cfg, factor_key, view, as_of):
    """A reference set of combination rows computed over the SINGLE-horizon
    `_regime_phase_factor_observation_set` builder + `_assign_triple_deciles` (the SAME path the samples
    drill-down reads). Means are independently re-derived with plain Python `statistics.mean` — proving the
    batched all-horizons builder agrees with the single-horizon one (the count-coherence keystone)."""
    wf = cfg.walk_forward
    fl = cfg.research.factor_lab
    horizons = list(wf.horizons)
    factor = _rpf_resolve_factor(cfg, factor_key)

    combos = {}
    for h in horizons:
        obs = _regime_phase_factor_observation_set(session, h, view, factor, as_of, cfg=cfg)
        bucketable = _assign_triple_deciles(obs, fl.deciles)
        grouped = defaultdict(lambda: {"returns": [], "mdds": []})
        for m in bucketable:
            key = (m["regime_decile"], m["severity_decile"], m["factor_decile"])
            grouped[key]["returns"].append(m["return"])
            if m["max_drawdown"] is not None:
                grouped[key]["mdds"].append(m["max_drawdown"])
        for key, bucket in grouped.items():
            combos.setdefault(key, {})[h] = bucket

    rows = []
    for (r_d, s_d, f_d), by_h in combos.items():
        by_horizon = []
        for h in horizons:
            bucket = by_h.get(h)
            if bucket is None:
                by_horizon.append({
                    "horizon": h, "n": 0, "low_sample": True,
                    "mean_return": None, "mean_max_drawdown": None,
                })
                continue
            returns = bucket["returns"]
            mdds = bucket["mdds"]
            by_horizon.append({
                "horizon": h, "n": len(returns), "low_sample": len(returns) < wf.min_sample,
                "mean_return": mean(returns) if returns else None,
                "mean_max_drawdown": mean(mdds) if mdds else None,
            })
        rows.append({"regime_decile": r_d, "severity_decile": s_d, "factor_decile": f_d, "by_horizon": by_horizon})
    # the same default order the study applies (decile-triple inner sort, then default-horizon return NA-last).
    rows.sort(key=lambda r: (r["regime_decile"], r["severity_decile"], r["factor_decile"]))

    def _rank(r):
        cell = next((b for b in r["by_horizon"] if b["horizon"] == wf.default_horizon), None)
        val = cell["mean_return"] if cell else None
        present = val is not None
        return ((present, val if present else present),)

    rows.sort(key=_rank, reverse=True)
    return rows


# ==================================================================================================
# 1. Byte-identity vs the reference over the single-horizon builder (load-bearing, count-coherence keystone)
# ==================================================================================================
@pytest.mark.parametrize("factor_key", [FACTOR_A, FACTOR_B])
@pytest.mark.parametrize("view", [VIEW_EPISODES, VIEW_POOLED])
@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
def test_compute_is_byte_identical_to_reference_over_observation_set(lab_engine, factor_key, view, as_of):
    """For BOTH factors, BOTH views and BOTH scopes, compute_regime_phase_factor_study's rows are byte-identical
    to the reference aggregation over the single-horizon `_regime_phase_factor_observation_set` +
    `_assign_triple_deciles` — so the batched all-horizons builder and the single-horizon (samples) builder
    produce byte-identical per-horizon combinations (Single source of truth; the count-coherence keystone)."""
    cfg = load_config()
    with Session(lab_engine) as session:
        got = compute_regime_phase_factor_study(session, factor=factor_key, view=view, as_of=as_of, config=cfg)
        ref = _reference_rows(session, cfg, factor_key, view, as_of)
        assert _bytes(got["rows"]) == _bytes(ref), "combination-row drift vs single-horizon reference"


def test_two_factors_produce_distinct_tables(lab_engine):
    """Switching the factor re-partitions the factor-decile dimension, so the two factors produce DISTINCT
    combination tables (the `factor` selector really drives the study — not a vacuous parameter)."""
    cfg = load_config()
    with Session(lab_engine) as session:
        a = compute_regime_phase_factor_study(session, factor=FACTOR_A, view=VIEW_POOLED, config=cfg)
        b = compute_regime_phase_factor_study(session, factor=FACTOR_B, view=VIEW_POOLED, config=cfg)
    assert a["factor"]["key"] == FACTOR_A and b["factor"]["key"] == FACTOR_B
    assert _bytes(a["rows"]) != _bytes(b["rows"]), "two factors collapsed to one table"


def test_top_level_metadata_matches_config_and_has_no_single_horizon(lab_engine):
    """The payload echoes the config-driven horizons / default_horizon / decile count / min_sample / page_size +
    the config factor catalog + the honest labels, carries NO single `horizon` (the view shows every horizon at
    once), and every row exposes exactly the all-horizons paired triple shape (no fabricated field)."""
    cfg = load_config()
    fl = cfg.research.factor_lab
    wf = cfg.walk_forward
    with Session(lab_engine) as session:
        payload = compute_regime_phase_factor_study(session, factor=FACTOR_A, view=VIEW_POOLED, config=cfg)
    assert "horizon" not in payload  # the all-horizons view has no single served horizon
    assert payload["view"] == VIEW_POOLED
    assert payload["horizons"] == list(wf.horizons)
    assert payload["default_horizon"] == wf.default_horizon
    assert payload["deciles_count"] == fl.deciles
    assert payload["min_sample"] == wf.min_sample
    assert payload["page_size"] == cfg.research.regime_phase_factor_page_size
    assert payload["factor"]["key"] == FACTOR_A
    assert [f["key"] for f in payload["factors"]] == [f.key for f in fl.factors]
    assert payload["asof_date"] is None
    assert "survivorship" in payload["survivorship_bias"].lower()
    assert "not a predictive model" in payload["descriptive_caveat"].lower()
    assert payload["rows"], "no combination rows emitted — the table is vacuous"
    for r in payload["rows"]:
        assert set(r) == {"regime_decile", "severity_decile", "factor_decile", "by_horizon"}
        assert 1 <= r["regime_decile"] <= fl.deciles
        assert 1 <= r["severity_decile"] <= fl.deciles
        assert 1 <= r["factor_decile"] <= fl.deciles
        assert [b["horizon"] for b in r["by_horizon"]] == list(wf.horizons)
        for b in r["by_horizon"]:
            assert set(b) == {"horizon", "n", "low_sample", "mean_return", "mean_max_drawdown"}


# ==================================================================================================
# 2. Read-verbatim provenance: tags == stored regime score / served severity / stored factor; warm-up NA
# ==================================================================================================
def test_observation_tags_are_read_verbatim_from_their_canonical_sources(lab_engine):
    """Each observation's regime_score equals the stored `ScannerRun.regime_score`; its severity equals the
    SERVED `market_phase` timeline value for ITS snapshot date (read VERBATIM via `phase_context_by_date`, NOT a
    re-derivation), with the correct by-snapshot-date join; its factor_value equals the stored factor column. A
    warm-up-head snapshot date with NO timeline value yields an honest unclassified (None) severity — never a
    fabricated value."""
    cfg = load_config()
    factor = _rpf_resolve_factor(cfg, FACTOR_A)  # leadership_score == the stored `lead` column we set
    with Session(lab_engine) as session:
        served = market_phase.phase_context_by_date(session, None, cfg)  # the SAME accessor the study reads
        runs = {run.id: run for run in session.exec(select(ScannerRun)).all()}
        pools = _regime_phase_factor_members_by_horizon(
            session, list(cfg.walk_forward.horizons), factor, None, cfg=cfg
        )
        seen_classified = False
        seen_warmup = False
        for h, members in pools.items():
            for m in members:
                run = runs[m["run_id"]]
                iso = run.asof_date.isoformat()
                assert m["regime_score"] == run.regime_score, f"regime join drift @{iso}"
                assert m["factor_value"] == float(int(m["ticker"][1:])), "factor value not read verbatim"
                ctx = served.get(iso)
                if ctx is None:
                    assert m["severity"] is None  # warm-up head: honest unclassified, never fabricated
                    seen_warmup = True
                else:
                    assert m["severity"] == ctx["severity"], f"severity join drift @{iso}"
                    seen_classified = True
        assert seen_classified, "no classified observation — the provenance proof is vacuous"
        assert seen_warmup, "no warm-up-head observation — the unclassified-NA proof is vacuous"


def test_warmup_observations_are_excluded_from_every_displayed_combination(lab_engine):
    """The unclassified (warm-up-head, NULL-severity) observations are present in the raw pool but EXCLUDED from
    every displayed combination (`_assign_triple_deciles` drops any observation missing a dimension) — so the
    sum of combination Ns at a horizon equals the bucketable (all-three-non-null) count, never including a
    fabricated combination."""
    cfg = load_config()
    factor = _rpf_resolve_factor(cfg, FACTOR_A)
    with Session(lab_engine) as session:
        pool = _regime_phase_factor_members_by_horizon(session, [DEFAULT_H], factor, None, cfg=cfg)[DEFAULT_H]
        warmup_n = sum(1 for m in pool if m["severity"] is None)
        assert warmup_n > 0, "fixture has no warm-up observation — the exclusion proof is vacuous"
        bucketable_n = sum(
            1 for m in pool
            if m["regime_score"] is not None and m["severity"] is not None and m["factor_value"] is not None
        )
        payload = compute_regime_phase_factor_study(session, factor=FACTOR_A, view=VIEW_POOLED, config=cfg)
        combo_total = sum(
            b["n"] for r in payload["rows"] for b in r["by_horizon"] if b["horizon"] == DEFAULT_H
        )
        assert combo_total == bucketable_n == len(pool) - warmup_n, "warm-up observation leaked into a combination"


def test_combination_means_match_independent_manual_aggregation(lab_engine):
    """Pooled, all-history: each populated combination cell's mean_return equals a plain-Python mean over the
    stored returns of that triple's members at that horizon, and its mean_max_drawdown the mean over only members
    with a stored drawdown — proving the engine READS the stored values (No recompute)."""
    cfg = load_config()
    factor = _rpf_resolve_factor(cfg, FACTOR_A)
    with Session(lab_engine) as session:
        payload = compute_regime_phase_factor_study(session, factor=FACTOR_A, view=VIEW_POOLED, config=cfg)
        saw_populated = False
        for h in POPULATED_HORIZONS:
            obs = _regime_phase_factor_observation_set(session, h, VIEW_POOLED, factor, None, cfg=cfg)
            bucketable = _assign_triple_deciles(obs, cfg.research.factor_lab.deciles)
            grouped = defaultdict(list)
            mdd_grouped = defaultdict(list)
            for m in bucketable:
                key = (m["regime_decile"], m["severity_decile"], m["factor_decile"])
                grouped[key].append(m["return"])
                if m["max_drawdown"] is not None:
                    mdd_grouped[key].append(m["max_drawdown"])
            for r in payload["rows"]:
                key = (r["regime_decile"], r["severity_decile"], r["factor_decile"])
                cell = next(b for b in r["by_horizon"] if b["horizon"] == h)
                expected = grouped.get(key, [])
                assert cell["n"] == len(expected)
                if expected:
                    assert cell["mean_return"] == pytest.approx(mean(expected))
                    assert cell["mean_max_drawdown"] == pytest.approx(mean(mdd_grouped[key]))
                    assert cell["mean_max_drawdown"] < 0  # a real negative drawdown, not a fabricated 0
                    saw_populated = True
        assert saw_populated, "no populated combination cell — the read-verbatim proof is vacuous"


def test_no_mdd_and_empty_horizons_are_honest_na(lab_engine):
    """The drawdown-less horizon (FRs but no stored max_drawdown) carries a REAL mean_return but NA
    mean_max_drawdown on populated cells (never a fabricated 0); the empty horizon (no FRs) carries NA return AND
    NA drawdown with n==0 on every row (no fabricated bucket)."""
    cfg = load_config()
    with Session(lab_engine) as session:
        payload = compute_regime_phase_factor_study(session, factor=FACTOR_A, view=VIEW_POOLED, config=cfg)

    def cell(row, h):
        return next(b for b in row["by_horizon"] if b["horizon"] == h)

    populated = False
    for row in payload["rows"]:
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
    factor = _rpf_resolve_factor(cfg, FACTOR_A)
    with Session(lab_engine) as session:
        pooled_total = sum(
            len(_regime_phase_factor_observation_set(session, h, VIEW_POOLED, factor, None, cfg=cfg))
            for h in POPULATED_HORIZONS
        )
        episodes_total = sum(
            len(_regime_phase_factor_observation_set(session, h, VIEW_EPISODES, factor, None, cfg=cfg))
            for h in POPULATED_HORIZONS
        )
        asof_total = sum(
            len(_regime_phase_factor_observation_set(session, h, VIEW_POOLED, factor, date(2025, 3, 15), cfg=cfg))
            for h in POPULATED_HORIZONS
        )
    assert 0 < episodes_total < pooled_total, "episode collapse did not reduce the set"
    assert 0 < asof_total < pooled_total, "as-of did not shrink the observation set"


# ==================================================================================================
# 3. Cache: HIT == MISS == fresh; schema token + market-phase stamp + per-factor key
# ==================================================================================================
@pytest.mark.parametrize("view", [VIEW_EPISODES, VIEW_POOLED])
@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
def test_cache_hit_equals_miss_equals_fresh(lab_engine, view, as_of):
    cfg = load_config()
    with Session(lab_engine) as session:
        fresh = compute_regime_phase_factor_study(session, factor=FACTOR_A, view=view, as_of=as_of, config=cfg)
        cached_miss = regime_phase_factor_cached(session, cfg, factor=FACTOR_A, view=view, as_of=as_of)
        cached_hit = regime_phase_factor_cached(session, cfg, factor=FACTOR_A, view=view, as_of=as_of)
        assert _bytes(cached_miss) == _bytes(fresh)
        assert _bytes(cached_hit) == _bytes(fresh)
        rows = session.exec(
            select(EventStudyCache).where(
                EventStudyCache.subject == _regime_phase_factor_cache_subject(FACTOR_A),
                EventStudyCache.view == view,
            )
        ).all()
        assert len(rows) == 1  # exactly one current-shape row for this (subject, view, asof_key)


def test_distinct_factors_do_not_share_a_cache_row(lab_engine):
    """The cache subject folds in the SELECTED factor, so two factors key to distinct rows (no cross-factor
    cache bleed) with distinct payloads."""
    cfg = load_config()
    with Session(lab_engine) as session:
        a = regime_phase_factor_cached(session, cfg, factor=FACTOR_A, view=VIEW_POOLED)
        b = regime_phase_factor_cached(session, cfg, factor=FACTOR_B, view=VIEW_POOLED)
        assert a["factor"]["key"] == FACTOR_A and b["factor"]["key"] == FACTOR_B
        assert _bytes(a["rows"]) != _bytes(b["rows"]), "two factors served the same cached table"
        subjects = {
            r.subject for r in session.exec(
                select(EventStudyCache).where(EventStudyCache.view == VIEW_POOLED)
            ).all()
        }
        assert _regime_phase_factor_cache_subject(FACTOR_A) in subjects
        assert _regime_phase_factor_cache_subject(FACTOR_B) in subjects


def test_episodes_and_pooled_cache_rows_do_not_collide(lab_engine):
    """The cache keys on the actual view, so the episodes and pooled payloads never collide (distinct rows)."""
    cfg = load_config()
    with Session(lab_engine) as session:
        ep = regime_phase_factor_cached(session, cfg, factor=FACTOR_A, view=VIEW_EPISODES)
        po = regime_phase_factor_cached(session, cfg, factor=FACTOR_A, view=VIEW_POOLED)
        assert ep["view"] == VIEW_EPISODES and po["view"] == VIEW_POOLED
        rows = session.exec(
            select(EventStudyCache).where(
                EventStudyCache.subject == _regime_phase_factor_cache_subject(FACTOR_A)
            )
        ).all()
        assert {r.view for r in rows} == {VIEW_EPISODES, VIEW_POOLED}


def test_pre_iter55_old_schema_row_is_a_miss_and_is_pruned(lab_engine):
    """An already-populated OLD-SCHEMA cache row (keyed by the BARE `_dataset_version` WITHOUT the schema token +
    market-phase stamp) is never hit (the read computes the composite stamp) and is PRUNED on the next write —
    so the cache can never serve the stale old-shape figure (iter-38/39/44). The schema-token MISS-then-populate
    proof against a REAL already-populated row, not a fresh compute."""
    cfg = load_config()
    with Session(lab_engine) as session:
        base_version = _dataset_version(session)  # the pre-iter-55 stamp (no token, no mp stamp)
        session.add(EventStudyCache(
            subject=_regime_phase_factor_cache_subject(FACTOR_A), view=VIEW_POOLED, asof_key="all",
            dataset_version=base_version, horizon=cfg.walk_forward.default_horizon,
            payload_json=json.dumps({"sentinel": "old-shape-must-not-be-served", "rows": []}),
            created_at=_utc(),
        ))
        session.commit()

        served = regime_phase_factor_cached(session, cfg, factor=FACTOR_A, view=VIEW_POOLED)
        fresh = compute_regime_phase_factor_study(session, factor=FACTOR_A, view=VIEW_POOLED, config=cfg)
        assert _bytes(served) == _bytes(fresh), "served the stale old-schema cached payload"
        assert "sentinel" not in served
        assert served["rows"], "served an empty old-shape table"

        remaining = session.exec(
            select(EventStudyCache).where(
                EventStudyCache.subject == _regime_phase_factor_cache_subject(FACTOR_A)
            )
        ).all()
        token_version = _regime_phase_factor_cache_version(session)
        assert all(r.dataset_version == token_version for r in remaining)
        assert any(r.dataset_version == token_version for r in remaining)


def test_cache_refreshes_after_dataset_change(lab_engine):
    """The cache REFRESHES after a dataset change: cache a payload, add a snapshot + forward return (bumping the
    dataset-version stamp), and the next read returns the UPDATED aggregate, not the stale one."""
    cfg = load_config()
    with Session(lab_engine) as session:
        before = regime_phase_factor_cached(session, cfg, factor=FACTOR_A, view=VIEW_POOLED)
        before_total = sum(b["n"] for r in before["rows"] for b in r["by_horizon"] if b["horizon"] == DEFAULT_H)
        v_before = _dataset_version(session)

        # add a new result + FR on an existing classified run (the 2025-02-10 run) so a combination n grows.
        run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == CLASSIFIED_RUNS[0][0])).first()
        _add_result(session, run.id, "Z01", rank=1, lead=3.0, eq=97.0)
        _add_fr(session, run.id, "Z01", ret=0.07, horizon=DEFAULT_H, mdd=-0.03)
        session.commit()
        assert _dataset_version(session) != v_before

        after = regime_phase_factor_cached(session, cfg, factor=FACTOR_A, view=VIEW_POOLED)
        after_total = sum(b["n"] for r in after["rows"] for b in r["by_horizon"] if b["horizon"] == DEFAULT_H)
        assert after_total == before_total + 1, "cache served a stale (pre-add) figure"
        fresh = compute_regime_phase_factor_study(session, factor=FACTOR_A, view=VIEW_POOLED, config=cfg)
        assert _bytes(after) == _bytes(fresh)


def test_cache_refreshes_after_market_phase_schema_version_change(lab_engine, monkeypatch):
    """The J-111/J-112 single-source twist: because the severity dimension is read from the served `market_phase`
    timeline (cached behind its OWN `SCHEMA_VERSION` + dataset stamp), a phase/severity refresh MUST invalidate
    the study. Cache a payload, bump `market_phase.SCHEMA_VERSION`, and assert the previously-cached row is no
    longer hit (the composite key changed) and the new row is keyed under the new market-phase stamp."""
    cfg = load_config()
    with Session(lab_engine) as session:
        regime_phase_factor_cached(session, cfg, factor=FACTOR_A, view=VIEW_POOLED)  # populate under "s2"
        version_before = _regime_phase_factor_cache_version(session)
        rows_before = session.exec(
            select(EventStudyCache).where(
                EventStudyCache.subject == _regime_phase_factor_cache_subject(FACTOR_A),
                EventStudyCache.view == VIEW_POOLED,
            )
        ).all()
        assert [r.dataset_version for r in rows_before] == [version_before]

        monkeypatch.setattr(market_phase, "SCHEMA_VERSION", "s99-test")
        version_after = _regime_phase_factor_cache_version(session)
        assert version_after != version_before, "market-phase stamp not folded into the study cache key"

        served = regime_phase_factor_cached(session, cfg, factor=FACTOR_A, view=VIEW_POOLED)
        fresh = compute_regime_phase_factor_study(session, factor=FACTOR_A, view=VIEW_POOLED, config=cfg)
        assert _bytes(served) == _bytes(fresh)
        rows_after = session.exec(
            select(EventStudyCache).where(
                EventStudyCache.subject == _regime_phase_factor_cache_subject(FACTOR_A),
                EventStudyCache.view == VIEW_POOLED,
            )
        ).all()
        assert [r.dataset_version for r in rows_after] == [version_after], "stale-severity row not refreshed/pruned"


# ==================================================================================================
# 4. Bounded read (J-105): one heavy read, yield_per-streamed, (run_id, id)-ordered, chunk-independent
# ==================================================================================================
def test_shared_pool_read_is_bounded_and_run_id_id_ordered():
    """Source-level guard (iter-46/47/48 OOM lesson): the shared pool builder streams with `yield_per`, orders
    the ScannerResult side by `(run_id, id)` (rides `ix_scanner_results_run_id` — no temp B-tree), and
    materializes NO unbounded `.all()` over the heavy tables."""
    src = inspect.getsource(_regime_phase_factor_members_by_horizon)
    assert "yield_per" in src, "shared pool must stream with yield_per (bounded read)"
    assert ".order_by(ScannerResult.run_id, ScannerResult.id)" in src, "must order by (run_id, id)"
    # the real materialization call is `session.exec(...).all()` -> `).all()`; only code, never the docstring.
    assert ").all()" not in src, "shared pool must not materialize an unbounded .all()"


@pytest.mark.parametrize("view", [VIEW_EPISODES, VIEW_POOLED])
@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
def test_chunk_independent(lab_engine, view, as_of):
    """The full payload is byte-identical under read_batch_size=1 vs a huge batch — the stream changes peak
    memory only, never a value or an ordering."""
    with Session(lab_engine) as session:
        small = compute_regime_phase_factor_study(
            session, factor=FACTOR_A, view=view, as_of=as_of, config=_cfg_batch(1)
        )
        big = compute_regime_phase_factor_study(
            session, factor=FACTOR_A, view=view, as_of=as_of, config=_cfg_batch(1_000_000)
        )
        assert _bytes(small) == _bytes(big), f"payload differs by batch (view={view}, as_of={as_of})"


def test_single_horizon_builder_byte_identical_to_all_horizons_slice(lab_engine):
    """The single-horizon builder call (`_regime_phase_factor_members_by_horizon([h])[h]`, as the samples
    drill-down uses) is byte-identical to that horizon's slice of the all-horizons build — the property
    count-coherence relies on (the extra streamed results for other-horizon-only runs are dropped by the
    per-horizon gate)."""
    cfg = load_config()
    factor = _rpf_resolve_factor(cfg, FACTOR_A)
    horizons = list(cfg.walk_forward.horizons)
    with Session(lab_engine) as session:
        allp = _regime_phase_factor_members_by_horizon(session, horizons, factor, None, cfg=cfg)
        for h in horizons:
            one = _regime_phase_factor_members_by_horizon(session, [h], factor, None, cfg=cfg)[h]
            assert _bytes(one) == _bytes(allp[h]), f"single vs all-horizons builder drift @h={h}"


# ==================================================================================================
# 5. Samples count-coherence (J-51/J-65): total == published n in BOTH views + BOTH scopes; all resolve
# ==================================================================================================
@pytest.mark.parametrize("view", [VIEW_EPISODES, VIEW_POOLED])
@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
def test_samples_count_coherent_for_every_combination(lab_engine, view, as_of):
    """The samples drill-down for EVERY emitted combination — each `(regime, severity, factor)` decile triple, at
    EVERY horizon — has a `total` equal to the study's published n, in BOTH Episodes/Pooled and BOTH
    All-history/As-of, including NA/empty cells (n==0 -> an honest empty cohort, never a 4xx)."""
    cfg = load_config()
    with Session(lab_engine) as session:
        payload = compute_regime_phase_factor_study(session, factor=FACTOR_A, view=view, as_of=as_of, config=cfg)
        checked = 0
        for r in payload["rows"]:
            for b in r["by_horizon"]:
                s = compute_samples(
                    session, kind=KIND_REGIME_PHASE_FACTOR, horizon=b["horizon"], config=cfg, as_of=as_of,
                    factor_key=FACTOR_A, regime_decile=r["regime_decile"],
                    severity_decile=r["severity_decile"], factor_decile=r["factor_decile"], view=view,
                )
                assert s["total"] == b["n"], (
                    f"coherence drift ({r['regime_decile']},{r['severity_decile']},{r['factor_decile']})"
                    f"@{b['horizon']}"
                )
                assert len(s["rows"]) == b["n"]
                checked += 1
        assert checked > 0, "no combination checked — the coherence proof is vacuous"


def test_samples_rows_carry_three_values_and_return(lab_engine):
    """A populated combination drill-down row carries the regime score + severity score + selected factor value
    (read VERBATIM) and the realized forward return, and its snapshot date resolves — so a drill-down is never a
    bare count."""
    cfg = load_config()
    with Session(lab_engine) as session:
        payload = compute_regime_phase_factor_study(session, factor=FACTOR_A, view=VIEW_POOLED, config=cfg)
        target = None
        for r in payload["rows"]:
            for b in r["by_horizon"]:
                if b["n"] > 0 and b["horizon"] in POPULATED_HORIZONS:
                    target = (r["regime_decile"], r["severity_decile"], r["factor_decile"], b["horizon"], b["n"])
                    break
            if target:
                break
        assert target, "no populated combination to drill into"
        r_d, s_d, f_d, h, n = target
        s = compute_samples(
            session, kind=KIND_REGIME_PHASE_FACTOR, horizon=h, config=cfg,
            factor_key=FACTOR_A, regime_decile=r_d, severity_decile=s_d, factor_decile=f_d, view=VIEW_POOLED,
        )
        assert s["total"] == n and len(s["rows"]) == n
        r0 = s["rows"][0]
        assert r0["snapshot_date"] is not None
        keys = {v["key"] for v in r0["values"]}
        assert {"regime_score", "severity", FACTOR_A} <= keys
        assert isinstance(r0["forward_return"], float)
        assert s["cohort"]["kind"] == KIND_REGIME_PHASE_FACTOR
        assert s["cohort"]["factor"]["key"] == FACTOR_A


def test_samples_invalid_selectors_raise(lab_engine):
    """An unknown factor, an out-of-range decile (each dimension), and an unknown view each raise ValueError
    (the API turns these into an honest 4xx — never a silent empty 200)."""
    cfg = load_config()
    fl = cfg.research.factor_lab
    with Session(lab_engine) as session:
        with pytest.raises(ValueError):
            compute_samples(session, kind=KIND_REGIME_PHASE_FACTOR, horizon=DEFAULT_H, config=cfg,
                            factor_key="not-a-factor", regime_decile=1, severity_decile=1, factor_decile=1,
                            view=VIEW_POOLED)
        for bad in ({"regime_decile": 0}, {"severity_decile": fl.deciles + 1}, {"factor_decile": None}):
            kwargs = {"regime_decile": 1, "severity_decile": 1, "factor_decile": 1, **bad}
            with pytest.raises(ValueError):
                compute_samples(session, kind=KIND_REGIME_PHASE_FACTOR, horizon=DEFAULT_H, config=cfg,
                                factor_key=FACTOR_A, view=VIEW_POOLED, **kwargs)
        with pytest.raises(ValueError):
            compute_samples(session, kind=KIND_REGIME_PHASE_FACTOR, horizon=DEFAULT_H, config=cfg,
                            factor_key=FACTOR_A, regime_decile=1, severity_decile=1, factor_decile=1,
                            view="not-a-view")


def test_in_range_but_unemitted_combination_is_honest_empty_not_4xx(lab_engine):
    """An in-range triple with no members at a horizon (a combination the study shows with n=0, or a sparse
    triple the partition never fills) is a VALID empty cohort — its drill-down returns total 0 + no rows, NEVER a
    4xx (every emitted/displayable combination resolves)."""
    cfg = load_config()
    fl = cfg.research.factor_lab
    with Session(lab_engine) as session:
        # the empty horizon has NO FRs, so EVERY triple is empty there — an honest empty cohort, not a 4xx.
        s = compute_samples(
            session, kind=KIND_REGIME_PHASE_FACTOR, horizon=EMPTY_HORIZON, config=cfg,
            factor_key=FACTOR_A, regime_decile=1, severity_decile=1, factor_decile=fl.deciles, view=VIEW_POOLED,
        )
        assert s["total"] == 0 and s["rows"] == []


def test_compute_unknown_view_or_factor_raises(lab_engine):
    """compute_regime_phase_factor_study rejects an unknown view and an unknown factor (the API pre-validates ->
    422)."""
    cfg = load_config()
    with Session(lab_engine) as session:
        with pytest.raises(ValueError):
            compute_regime_phase_factor_study(session, factor=FACTOR_A, view="not-a-view", config=cfg)
        with pytest.raises(ValueError):
            compute_regime_phase_factor_study(session, factor="not-a-factor", view=VIEW_POOLED, config=cfg)
