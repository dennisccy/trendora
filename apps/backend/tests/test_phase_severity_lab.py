"""Market Phase & Severity Lab (iter-54, J-111) — the STRUCTURAL TWIN of the Regime Lab (J-110):
cross-sectional realized forward returns + paired max-drawdown grouped (a) by the five canonical market-PHASE
labels and (b) into deciles of the 0–100 SEVERITY score, at EVERY config horizon at once as paired (mean
forward-return, mean max-drawdown) columns, with the rank-IC of the severity score vs the forward return per
horizon. A read-only re-surfacing of ALREADY-STORED canonical values (stored `forward_returns.realized_return`
+ the J-86 `max_drawdown`, and the SERVED `market_phase` phase label + 0–100 severity read VERBATIM from the
causal timeline `phase_context_by_date`, joined by snapshot date) — it recomputes nothing.

The ONLY material difference from J-110: the grouping subject's SOURCE. J-110 read the regime VERBATIM off
the immutable `ScannerRun`; J-111 reads the phase label + severity LEVEL VERBATIM off the served `market_phase`
timeline, joined BY SNAPSHOT DATE. The timeline is monkeypatched here to controlled values so the join +
grouping correctness is exact by construction (isolated from the heavy market-phase derivation) — the SAME
isolation `test_severity_velocity.py` uses for the J-103 served-velocity join.

NON-NEGOTIABLE contracts proven here:

  - **Single computation path / count-coherence keystone (Single source of truth).** The all-horizons
    `compute_phase_severity_lab` per-(bucket, horizon) mean return / mean max-drawdown / n / rank-IC is
    byte-identical to a reference aggregation over `_phase_severity_lab_observation_set(horizon, view, as_of)`
    — the SAME single-horizon builder the samples drill-down reads — across BOTH Episodes/Pooled views and
    BOTH All-history/As-of scopes. The batched all-horizons builder and the single-horizon builder therefore
    produce byte-identical per-horizon observation sets (no second derivation, no number recomputed).
  - **Read-verbatim provenance (No recompute in the read path).** Each observation's tagged phase label +
    severity equals the SERVED `market_phase` timeline value for ITS snapshot date (asserted against
    `phase_context_by_date`, NOT a re-derivation), with the correct by-snapshot-date join; a warm-up-head date
    with no timeline value yields an honest unclassified (None) tag — never a fabricated phase/severity.
  - **Cache schema token + market-phase stamp (iter-38/39/44 + the J-111 twist).** A pre-iter-54 OLD-SHAPE
    cache row (keyed by the bare `_dataset_version`) is a guaranteed MISS and is PRUNED — tested against a real
    already-populated row, not a fresh compute. A real HIT returns byte-identical figures. The cache refreshes
    on a real dataset change AND on a market-phase `SCHEMA_VERSION`/dataset-stamp change (so a phase/severity
    refresh invalidates the lab — no stale phase tags).
  - **Bounded read (J-105 / iter-46/47/48 OOM lesson).** The shared pool is built ONCE for all horizons (one
    heavy read), `yield_per`-streamed (no unbounded `.all()`), ordering the ScannerResult side by
    `(run_id, id)`. Chunk-independent (batch=1 vs huge).
  - **Samples count-coherence (J-51/J-65).** Every displayable bucket's samples `total` equals its published
    n in BOTH views and BOTH scopes; every displayable bucket resolves without a 4xx; an unknown label /
    out-of-range decile / unknown view raises (an honest 4xx at the API).

The math runs on tiny hand-built in-memory data (the lab READS stored rows — no engine run needed). The
fixture has 5 runs at consecutive monthly dates: ONE warm-up-head run with NO served phase/severity
(unclassified observations) + four runs each a DISTINCT phase label + severity, tickers split so the Episodes
collapse differs from Pooled, FRs at several horizons (with a paired max_drawdown), a horizon with NO FRs
(empty/NA), and a horizon whose FRs carry NO max_drawdown (NA-honest mean-MDD).
"""
from __future__ import annotations

import inspect
import json
from datetime import date, datetime, timezone
from statistics import mean

import pytest
from sqlmodel import Session, select

import app.engine.market_phase as market_phase
from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.research import (
    _PHASE_SEVERITY_LAB_SCHEMA_TOKEN,
    _PHASE_SEVERITY_LAB_SUBJECT,
    VIEW_EPISODES,
    VIEW_POOLED,
    _dataset_version,
    _deciles,
    _phase_severity_lab_cache_version,
    _phase_severity_lab_members_by_horizon,
    _phase_severity_lab_observation_set,
    _rank_ic,
    _severity_ordered,
    compute_phase_severity_lab,
    phase_severity_lab_cached,
)
from app.engine.samples import KIND_PHASE_SEVERITY_LAB, compute_samples
from app.models import EventStudyCache, ForwardReturn, ScannerResult, ScannerRun

DEFAULT_H = 20  # config walk_forward.default_horizon
POPULATED_HORIZONS = (1, 5, 20)  # horizons with FRs AND a paired max_drawdown
NO_MDD_HORIZON = 60  # has FRs but max_drawdown=None (NA-honest mean-MDD leg)
EMPTY_HORIZON = 10  # no FRs at all (empty decile / label rows -> NA return AND NA drawdown)

WARMUP = date(2025, 1, 10)  # the warm-up head: NO served phase/severity (unclassified observations)
# The four phased runs: (asof_date, served phase label, served 0–100 severity). Distinct severities so the
# decile split has spread; four DISTINCT labels (all in config.market_phase.labels) so the by-label table has
# multiple populated rows; "Recovery" (the fifth label) is left with NO run -> an honest empty by-label row.
PHASED_RUNS = [
    (date(2025, 2, 10), "Bear", 85.0),
    (date(2025, 3, 10), "Correction", 55.0),
    (date(2025, 4, 10), "Expansion", 10.0),
    (date(2025, 5, 10), "Pullback", 35.0),
]
# The served market-phase timeline (monkeypatched) — keyed by ISO date -> {phase, severity, p_bear}. The
# warm-up-head run is deliberately ABSENT (no entry) so its observations tag unclassified (None, None).
PHASE_CTX = {
    asof.isoformat(): {"phase": phase, "severity": severity, "p_bear": 0.0}
    for asof, phase, severity in PHASED_RUNS
}


def _utc() -> datetime:
    return datetime.now(timezone.utc)


def _add_run(session: Session, asof: date) -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=_utc(), provider="seed", benchmark="SPY",
        regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
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
def lab_engine(tmp_path, monkeypatch):
    """5 runs at consecutive monthly dates: runs[0] is the warm-up head (NO served phase/severity), runs[1..4]
    each a DISTINCT served phase label + severity. Tickers T01..T06 appear in runs 1+2 (consecutive ordinals
    -> ONE episode at run 1); T07..T12 appear in runs 3+4 (-> ONE episode at run 3); W01..W03 appear in the
    warm-up-head run only (-> unclassified observations, dropped from every displayed bucket but present in the
    raw pool). So the Episodes collapse keeps strictly fewer than Pooled AND the as-of FILTER shrinks the set.
    Each (run, ticker) has FRs at the populated horizons (paired NEGATIVE max_drawdown), an FR with NO
    max_drawdown at horizon 60 (NA-honest), and NO FR at horizon 10 (empty/NA). The served `market_phase`
    timeline is monkeypatched to PHASE_CTX (honoring the as-of FILTER), so the by-snapshot-date join + grouping
    are exact by construction."""
    engine = make_engine(f"sqlite:///{tmp_path / 'phase_severity_lab.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        warmup = _add_run(session, WARMUP)
        phased = [_add_run(session, asof) for asof, _phase, _sev in PHASED_RUNS]
        # T01..T06 -> phased[0], phased[1] (consecutive) ; T07..T12 -> phased[2], phased[3] (consecutive)
        membership = {
            **{f"T{i:02d}": (phased[0], phased[1]) for i in range(1, 7)},
            **{f"T{i:02d}": (phased[2], phased[3]) for i in range(7, 13)},
            **{f"W{i:02d}": (warmup,) for i in range(1, 4)},  # warm-up-head only (unclassified)
        }
        for ticker, run_tuple in membership.items():
            i = int(ticker[1:])
            for run in run_tuple:
                _add_result(session, run.id, ticker, rank=i)
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

    # `_phase_severity_lab_members_by_horizon` lazily imports `phase_context_by_date` FROM the market_phase
    # module at call time, so the patch must target the source module (not the research namespace).
    monkeypatch.setattr(market_phase, "phase_context_by_date", _fake_phase_ctx)
    return engine


def _cfg_batch(batch: int):
    cfg = load_config()
    return cfg.model_copy(update={"research": cfg.research.model_copy(update={"read_batch_size": batch})})


def _bytes(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=str)


# ==================================================================================================
# Reference aggregation over the single-horizon `_phase_severity_lab_observation_set` (the samples builder)
# ==================================================================================================
def _reference(session, cfg, view, as_of):
    """A reference Phase & Severity-Lab payload computed over the SINGLE-horizon
    `_phase_severity_lab_observation_set` builder (the one the samples drill-down reads). by-label means are
    independently re-derived with plain Python `statistics.mean`; by-decile reuses the SAME
    `_severity_ordered`/`_deciles` quantile machinery (the count-coherence keystone — proving the batched
    all-horizons builder agrees with the single-horizon one)."""
    wf = cfg.walk_forward
    fl = cfg.research.factor_lab
    horizons = list(wf.horizons)
    labels = list(cfg.market_phase.labels)

    by_label = []
    for label in labels:
        by_horizon = []
        for h in horizons:
            obs = _phase_severity_lab_observation_set(session, h, view, as_of)
            lm = [m for m in obs if m["phase"] == label]
            returns = [m["return"] for m in lm]
            mdds = [m["max_drawdown"] for m in lm if m["max_drawdown"] is not None]
            by_horizon.append({
                "horizon": h, "n": len(lm), "low_sample": len(lm) < wf.min_sample,
                "mean_return": mean(returns) if returns else None,
                "mean_max_drawdown": mean(mdds) if mdds else None,
            })
        by_label.append({"phase": label, "by_horizon": by_horizon})

    decile_rows_by_h = {}
    rank_ic_by_horizon = []
    for h in horizons:
        obs = _phase_severity_lab_observation_set(session, h, view, as_of)
        ordered = _severity_ordered(obs)
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
@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
def test_compute_is_byte_identical_to_reference_over_observation_set(lab_engine, view, as_of):
    """For BOTH views and BOTH scopes, compute_phase_severity_lab's by_label / by_decile / rank_ic_by_horizon
    are byte-identical to the reference aggregation over the single-horizon
    `_phase_severity_lab_observation_set` — so the batched all-horizons builder and the single-horizon
    (samples) builder produce byte-identical per-horizon observation sets (Single source of truth; the
    count-coherence keystone)."""
    cfg = load_config()
    with Session(lab_engine) as session:
        got = compute_phase_severity_lab(session, cfg, view=view, as_of=as_of)
        ref = _reference(session, cfg, view, as_of)
        assert _bytes(got["by_label"]) == _bytes(ref["by_label"]), "by-label drift"
        assert _bytes(got["by_decile"]) == _bytes(ref["by_decile"]), "by-decile drift"
        assert _bytes(got["rank_ic_by_horizon"]) == _bytes(ref["rank_ic_by_horizon"]), "rank-IC drift"


def test_top_level_metadata_matches_config_and_has_no_single_horizon(lab_engine):
    """The payload echoes the config-driven horizons / default_horizon / decile count / min_sample +
    the config market-phase-label vocabulary + the honest labels, carries NO single `horizon` (the view shows
    every horizon at once), and exposes exactly the all-horizons paired shape (no fabricated field)."""
    cfg = load_config()
    fl = cfg.research.factor_lab
    wf = cfg.walk_forward
    with Session(lab_engine) as session:
        payload = compute_phase_severity_lab(session, cfg, view=VIEW_POOLED)
    assert "horizon" not in payload  # the all-horizons view has no single served horizon
    assert payload["view"] == VIEW_POOLED
    assert payload["horizons"] == list(wf.horizons)
    assert payload["default_horizon"] == wf.default_horizon
    assert payload["deciles_count"] == fl.deciles
    assert payload["min_sample"] == wf.min_sample
    assert payload["phase_labels"] == list(cfg.market_phase.labels)
    assert payload["asof_date"] is None
    assert "survivorship" in payload["survivorship_bias"].lower()
    assert "not a predictive model" in payload["descriptive_caveat"].lower()
    # one by-label row per configured market-phase label, in config order; one by-decile row D1..D`deciles`.
    assert [r["phase"] for r in payload["by_label"]] == list(cfg.market_phase.labels)
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
# 2. Read-verbatim provenance: tags == the served market_phase timeline value for the snapshot date (by-date
#    join), warm-up head is unclassified; figures are READ verbatim; the views/scopes really filter
# ==================================================================================================
def test_phase_severity_tags_are_the_served_timeline_value_for_the_snapshot_date(lab_engine):
    """Each observation's tagged phase label + severity equals the SERVED `market_phase` timeline value for
    ITS snapshot date (read VERBATIM via `phase_context_by_date`, NOT a re-derivation), with the correct
    by-snapshot-date join; a warm-up-head snapshot date with NO timeline value yields an honest unclassified
    (None, None) tag — never a fabricated phase/severity."""
    cfg = load_config()
    with Session(lab_engine) as session:
        served = market_phase.phase_context_by_date(session, None, cfg)  # the SAME accessor the lab reads
        run_dates = {run.id: run.asof_date.isoformat() for run in session.exec(select(ScannerRun)).all()}
        pools = _phase_severity_lab_members_by_horizon(session, list(cfg.walk_forward.horizons), None, cfg=cfg)
        seen_classified = False
        seen_warmup = False
        for h, members in pools.items():
            for m in members:
                iso = run_dates[m["run_id"]]
                ctx = served.get(iso)
                if ctx is None:
                    # warm-up head: no served value -> honest unclassified tag (never fabricated)
                    assert m["phase"] is None and m["severity"] is None
                    seen_warmup = True
                else:
                    assert m["phase"] == ctx["phase"], f"phase join drift @{iso} (h={h})"
                    assert m["severity"] == ctx["severity"], f"severity join drift @{iso} (h={h})"
                    seen_classified = True
        assert seen_classified, "no classified observation — the by-date provenance proof is vacuous"
        assert seen_warmup, "no warm-up-head observation — the unclassified-NA proof is vacuous"
    # the by-date join is non-trivial: distinct dates carry distinct phases (Bear @ Feb vs Expansion @ Apr)
    assert PHASE_CTX[PHASED_RUNS[0][0].isoformat()]["phase"] != PHASE_CTX[PHASED_RUNS[2][0].isoformat()]["phase"]


def test_warmup_observations_are_excluded_from_every_displayed_bucket(lab_engine):
    """The unclassified (warm-up-head) observations are present in the raw pool but EXCLUDED from every
    displayed bucket: they match no by-label phase (None != any configured label) and are dropped from the
    severity-decile split (NULL severity excluded) — so the displayed tables never carry a fabricated phase."""
    cfg = load_config()
    with Session(lab_engine) as session:
        pools = _phase_severity_lab_members_by_horizon(session, [DEFAULT_H], None, cfg=cfg)[DEFAULT_H]
        warmup_n = sum(1 for m in pools if m["phase"] is None)
        assert warmup_n > 0, "fixture has no warm-up observation — the exclusion proof is vacuous"
        payload = compute_phase_severity_lab(session, cfg, view=VIEW_POOLED)
        # the sum of by-label Ns at this horizon excludes the warm-up observations (no None-phase row exists)
        label_total = sum(
            b["n"] for r in payload["by_label"] for b in r["by_horizon"] if b["horizon"] == DEFAULT_H
        )
        decile_total = sum(
            b["n"] for r in payload["by_decile"] for b in r["by_horizon"] if b["horizon"] == DEFAULT_H
        )
        assert label_total == len(pools) - warmup_n, "warm-up observation leaked into a by-label row"
        assert decile_total == len(pools) - warmup_n, "warm-up (NULL-severity) observation leaked into a decile"
        assert "Recovery" in [r["phase"] for r in payload["by_label"]]  # the empty label row is still emitted


def test_by_label_means_match_independent_manual_aggregation(lab_engine):
    """Pooled, all-history: each populated by-label cell's mean_return equals a plain-Python mean over the
    stored returns of that label's members at that horizon, and its mean_max_drawdown the mean over only
    members with a stored drawdown — proving the engine READS the stored values (No recompute)."""
    cfg = load_config()
    with Session(lab_engine) as session:
        payload = compute_phase_severity_lab(session, cfg, view=VIEW_POOLED)
        rows_by_label = {r["phase"]: r for r in payload["by_label"]}
        saw_populated = False
        for h in POPULATED_HORIZONS:
            obs = _phase_severity_lab_observation_set(session, h, VIEW_POOLED, None)
            for label in cfg.market_phase.labels:
                lm = [m for m in obs if m["phase"] == label]
                cell = next(b for b in rows_by_label[label]["by_horizon"] if b["horizon"] == h)
                assert cell["n"] == len(lm)
                if lm:
                    assert cell["mean_return"] == pytest.approx(mean(m["return"] for m in lm))
                    assert cell["mean_max_drawdown"] == pytest.approx(mean(m["max_drawdown"] for m in lm))
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
        payload = compute_phase_severity_lab(session, cfg, view=VIEW_POOLED)

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
            len(_phase_severity_lab_observation_set(session, h, VIEW_POOLED, None)) for h in POPULATED_HORIZONS
        )
        episodes_total = sum(
            len(_phase_severity_lab_observation_set(session, h, VIEW_EPISODES, None)) for h in POPULATED_HORIZONS
        )
        asof_total = sum(
            len(_phase_severity_lab_observation_set(session, h, VIEW_POOLED, date(2025, 3, 15)))
            for h in POPULATED_HORIZONS
        )
    assert 0 < episodes_total < pooled_total, "episode collapse did not reduce the set"
    assert 0 < asof_total < pooled_total, "as-of did not shrink the observation set"


# ==================================================================================================
# 3. Cache: HIT == MISS == fresh; schema token + market-phase stamp make an old/stale row a MISS and prune it
# ==================================================================================================
@pytest.mark.parametrize("view", [VIEW_EPISODES, VIEW_POOLED])
@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
def test_cache_hit_equals_miss_equals_fresh(lab_engine, view, as_of):
    cfg = load_config()
    with Session(lab_engine) as session:
        fresh = compute_phase_severity_lab(session, cfg, view=view, as_of=as_of)
        cached_miss = phase_severity_lab_cached(session, cfg, view=view, as_of=as_of)  # populates the cache
        cached_hit = phase_severity_lab_cached(session, cfg, view=view, as_of=as_of)   # served from the row
        assert _bytes(cached_miss) == _bytes(fresh)
        assert _bytes(cached_hit) == _bytes(fresh)
        rows = session.exec(
            select(EventStudyCache).where(
                EventStudyCache.subject == _PHASE_SEVERITY_LAB_SUBJECT,
                EventStudyCache.view == view,
            )
        ).all()
        assert len(rows) == 1  # exactly one current-shape row for this (subject, view, asof_key)


def test_episodes_and_pooled_cache_rows_do_not_collide(lab_engine):
    """The cache keys on the actual view, so the episodes and pooled payloads never collide (distinct rows,
    distinct payloads)."""
    cfg = load_config()
    with Session(lab_engine) as session:
        ep = phase_severity_lab_cached(session, cfg, view=VIEW_EPISODES)
        po = phase_severity_lab_cached(session, cfg, view=VIEW_POOLED)
        assert ep["view"] == VIEW_EPISODES and po["view"] == VIEW_POOLED
        assert _bytes(ep["by_label"]) != _bytes(po["by_label"]), "episodes/pooled collapsed to one payload"
        rows = session.exec(
            select(EventStudyCache).where(EventStudyCache.subject == _PHASE_SEVERITY_LAB_SUBJECT)
        ).all()
        assert {r.view for r in rows} == {VIEW_EPISODES, VIEW_POOLED}


def test_pre_iter54_old_schema_row_is_a_miss_and_is_pruned(lab_engine):
    """An already-populated OLD-SCHEMA cache row (keyed by the BARE `_dataset_version` WITHOUT the schema
    token + market-phase stamp) is never hit (the read computes the composite stamp) and is PRUNED on the next
    write — so the cache can never serve the stale old-shape figure (iter-38/39/44). The schema-token MISS-
    then-populate proof against a REAL already-populated row, not a fresh compute."""
    cfg = load_config()
    with Session(lab_engine) as session:
        base_version = _dataset_version(session)  # the pre-iter-54 stamp (no token, no mp stamp)
        session.add(EventStudyCache(
            subject=_PHASE_SEVERITY_LAB_SUBJECT, view=VIEW_POOLED, asof_key="all",
            dataset_version=base_version, horizon=cfg.walk_forward.default_horizon,
            payload_json=json.dumps({"sentinel": "old-shape-must-not-be-served", "by_label": []}),
            created_at=_utc(),
        ))
        session.commit()

        served = phase_severity_lab_cached(session, cfg, view=VIEW_POOLED)
        fresh = compute_phase_severity_lab(session, cfg, view=VIEW_POOLED)
        assert _bytes(served) == _bytes(fresh), "served the stale old-schema cached payload"
        assert "sentinel" not in served
        assert served["by_label"], "served an empty old-shape table"

        remaining = session.exec(
            select(EventStudyCache).where(EventStudyCache.subject == _PHASE_SEVERITY_LAB_SUBJECT)
        ).all()
        token_version = _phase_severity_lab_cache_version(session)
        assert all(r.dataset_version == token_version for r in remaining)
        assert any(r.dataset_version == token_version for r in remaining)


def test_cache_refreshes_after_dataset_change(lab_engine):
    """The cache REFRESHES after a dataset change: cache a payload, add a snapshot + forward return (bumping
    the dataset-version stamp), and the next read returns the UPDATED aggregate, not the stale one."""
    cfg = load_config()
    with Session(lab_engine) as session:
        before = phase_severity_lab_cached(session, cfg, view=VIEW_POOLED)
        before_n = next(
            b for r in before["by_label"] if r["phase"] == "Bear"
            for b in r["by_horizon"] if b["horizon"] == DEFAULT_H
        )["n"]
        v_before = _dataset_version(session)

        # add a new result + FR on the existing Bear run (date 2025-02-10) so its by-label n grows by 1.
        bear_run = session.exec(
            select(ScannerRun).where(ScannerRun.asof_date == PHASED_RUNS[0][0])
        ).first()
        _add_result(session, bear_run.id, "Z01", rank=1)
        _add_fr(session, bear_run.id, "Z01", ret=0.07, horizon=DEFAULT_H, mdd=-0.03)
        session.commit()
        assert _dataset_version(session) != v_before

        after = phase_severity_lab_cached(session, cfg, view=VIEW_POOLED)
        after_n = next(
            b for r in after["by_label"] if r["phase"] == "Bear"
            for b in r["by_horizon"] if b["horizon"] == DEFAULT_H
        )["n"]
        assert after_n == before_n + 1, "cache served a stale (pre-add) figure"
        fresh = compute_phase_severity_lab(session, cfg, view=VIEW_POOLED)
        assert _bytes(after) == _bytes(fresh)


def test_cache_refreshes_after_market_phase_schema_version_change(lab_engine, monkeypatch):
    """The J-111 single-source twist: because the phase label + severity are read from the served
    `market_phase` timeline (cached behind its OWN `SCHEMA_VERSION` + dataset stamp), a phase/severity refresh
    MUST invalidate the lab. Cache a payload, bump `market_phase.SCHEMA_VERSION` (simulating a phase/severity
    schema refresh), and assert the previously-cached row is no longer hit (the composite key changed) and the
    new row is keyed under the new market-phase stamp — so no stale phase tag is ever served."""
    cfg = load_config()
    with Session(lab_engine) as session:
        phase_severity_lab_cached(session, cfg, view=VIEW_POOLED)  # populate under the current mp stamp ("s2")
        version_before = _phase_severity_lab_cache_version(session)
        rows_before = session.exec(
            select(EventStudyCache).where(
                EventStudyCache.subject == _PHASE_SEVERITY_LAB_SUBJECT, EventStudyCache.view == VIEW_POOLED,
            )
        ).all()
        assert [r.dataset_version for r in rows_before] == [version_before]

        # simulate a phase/severity schema refresh (the s1->s2 class of bump) — the lab key MUST change.
        monkeypatch.setattr(market_phase, "SCHEMA_VERSION", "s99-test")
        version_after = _phase_severity_lab_cache_version(session)
        assert version_after != version_before, "market-phase stamp not folded into the lab cache key"

        # the next read MISSES the old-stamp row, computes fresh, and prunes the stale row.
        served = phase_severity_lab_cached(session, cfg, view=VIEW_POOLED)
        fresh = compute_phase_severity_lab(session, cfg, view=VIEW_POOLED)
        assert _bytes(served) == _bytes(fresh)
        rows_after = session.exec(
            select(EventStudyCache).where(
                EventStudyCache.subject == _PHASE_SEVERITY_LAB_SUBJECT, EventStudyCache.view == VIEW_POOLED,
            )
        ).all()
        assert [r.dataset_version for r in rows_after] == [version_after], "stale-phase row not refreshed/pruned"


# ==================================================================================================
# 4. Bounded read (J-105): one heavy read, yield_per-streamed, (run_id, id)-ordered, chunk-independent
# ==================================================================================================
def test_shared_pool_read_is_bounded_and_run_id_id_ordered():
    """Source-level guard (iter-46/47/48 OOM lesson): the shared pool builder streams with `yield_per`, orders
    the ScannerResult side by `(run_id, id)` (rides `ix_scanner_results_run_id` — no temp B-tree), and
    materializes NO unbounded `.all()` over the heavy tables."""
    src = inspect.getsource(_phase_severity_lab_members_by_horizon)
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
        small = compute_phase_severity_lab(session, _cfg_batch(1), view=view, as_of=as_of)
        big = compute_phase_severity_lab(session, _cfg_batch(1_000_000), view=view, as_of=as_of)
        assert _bytes(small) == _bytes(big), f"payload differs by batch (view={view}, as_of={as_of})"


def test_single_horizon_builder_byte_identical_to_all_horizons_slice(lab_engine):
    """The single-horizon builder call (`_phase_severity_lab_members_by_horizon([h])[h]`, as the samples
    drill-down uses) is byte-identical to that horizon's slice of the all-horizons build — the property
    count-coherence relies on (the extra streamed results for other-horizon-only runs are dropped by the
    per-horizon gate)."""
    cfg = load_config()
    horizons = list(cfg.walk_forward.horizons)
    with Session(lab_engine) as session:
        allp = _phase_severity_lab_members_by_horizon(session, horizons, None, cfg=cfg)
        for h in horizons:
            one = _phase_severity_lab_members_by_horizon(session, [h], None, cfg=cfg)[h]
            assert _bytes(one) == _bytes(allp[h]), f"single vs all-horizons builder drift @h={h}"


# ==================================================================================================
# 5. Samples count-coherence (J-51/J-65): total == published n in BOTH views + BOTH scopes; all resolve
# ==================================================================================================
@pytest.mark.parametrize("view", [VIEW_EPISODES, VIEW_POOLED])
@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
def test_samples_count_coherent_for_every_bucket(lab_engine, view, as_of):
    """The samples drill-down for EVERY displayable Phase & Severity-Lab bucket — each market-phase label, each
    severity-score decile, at EVERY horizon — has a `total` equal to the view's published n, in BOTH
    Episodes/Pooled and BOTH All-history/As-of, including NA/empty buckets (n==0 -> an honest empty cohort,
    never a 4xx)."""
    cfg = load_config()
    horizons = list(cfg.walk_forward.horizons)
    with Session(lab_engine) as session:
        payload = compute_phase_severity_lab(session, cfg, view=view, as_of=as_of)
        checked = 0
        for row in payload["by_label"]:
            for b in row["by_horizon"]:
                s = compute_samples(
                    session, kind=KIND_PHASE_SEVERITY_LAB, horizon=b["horizon"], config=cfg, as_of=as_of,
                    slice_kind="label", phase=row["phase"], view=view,
                )
                assert s["total"] == b["n"], f"label coherence drift {row['phase']}@{b['horizon']}"
                assert len(s["rows"]) == b["n"]
                checked += 1
        for row in payload["by_decile"]:
            for b in row["by_horizon"]:
                s = compute_samples(
                    session, kind=KIND_PHASE_SEVERITY_LAB, horizon=b["horizon"], config=cfg, as_of=as_of,
                    slice_kind="decile", decile=row["decile"], view=view,
                )
                assert s["total"] == b["n"], f"decile coherence drift D{row['decile']}@{b['horizon']}"
                assert len(s["rows"]) == b["n"]
                checked += 1
        expected = len(horizons) * (len(cfg.market_phase.labels) + cfg.research.factor_lab.deciles)
        assert checked == expected


def test_samples_rows_carry_phase_and_severity_and_return(lab_engine):
    """A populated decile drill-down row carries the served phase label + severity score + the realized
    forward return (read VERBATIM), and its snapshot date resolves — so a drill-down is never a bare count."""
    cfg = load_config()
    with Session(lab_engine) as session:
        payload = compute_phase_severity_lab(session, cfg, view=VIEW_POOLED)
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
            session, kind=KIND_PHASE_SEVERITY_LAB, horizon=h, config=cfg,
            slice_kind="decile", decile=decile, view=VIEW_POOLED,
        )
        assert s["total"] == n and len(s["rows"]) == n
        r0 = s["rows"][0]
        assert r0["snapshot_date"] is not None
        assert r0["phase"] in cfg.market_phase.labels
        keys = {v["key"] for v in r0["values"]}
        assert {"phase", "severity"} <= keys
        assert isinstance(r0["forward_return"], float)
        assert s["cohort"]["kind"] == KIND_PHASE_SEVERITY_LAB and s["cohort"]["slice"] == "decile"


def test_samples_invalid_selectors_raise(lab_engine):
    """An unknown phase label, an out-of-range decile, an unknown slice, and an unknown view each raise
    ValueError (the API turns these into an honest 4xx — never a silent empty 200)."""
    cfg = load_config()
    fl = cfg.research.factor_lab
    with Session(lab_engine) as session:
        with pytest.raises(ValueError):
            compute_samples(session, kind=KIND_PHASE_SEVERITY_LAB, horizon=DEFAULT_H, config=cfg,
                            slice_kind="label", phase="Not-a-phase", view=VIEW_POOLED)
        with pytest.raises(ValueError):
            compute_samples(session, kind=KIND_PHASE_SEVERITY_LAB, horizon=DEFAULT_H, config=cfg,
                            slice_kind="decile", decile=0, view=VIEW_POOLED)
        with pytest.raises(ValueError):
            compute_samples(session, kind=KIND_PHASE_SEVERITY_LAB, horizon=DEFAULT_H, config=cfg,
                            slice_kind="decile", decile=fl.deciles + 1, view=VIEW_POOLED)
        with pytest.raises(ValueError):
            compute_samples(session, kind=KIND_PHASE_SEVERITY_LAB, horizon=DEFAULT_H, config=cfg,
                            slice_kind="not-a-slice", phase="Bear", view=VIEW_POOLED)
        with pytest.raises(ValueError):
            compute_samples(session, kind=KIND_PHASE_SEVERITY_LAB, horizon=DEFAULT_H, config=cfg,
                            slice_kind="label", phase="Bear", view="not-a-view")


def test_empty_label_row_drilldown_is_honest_empty_not_4xx(lab_engine):
    """The configured-but-unused "Recovery" phase label is a VALID bucket the study DISPLAYS (n=0 row), so its
    drill-down returns an honest empty cohort (total 0, no rows), NEVER a 4xx — every displayable bucket
    resolves."""
    cfg = load_config()
    with Session(lab_engine) as session:
        s = compute_samples(
            session, kind=KIND_PHASE_SEVERITY_LAB, horizon=DEFAULT_H, config=cfg,
            slice_kind="label", phase="Recovery", view=VIEW_POOLED,
        )
        assert s["total"] == 0 and s["rows"] == []


def test_compute_unknown_view_raises(lab_engine):
    """compute_phase_severity_lab rejects an unknown view (the API pre-validates -> 422)."""
    cfg = load_config()
    with Session(lab_engine) as session:
        with pytest.raises(ValueError):
            compute_phase_severity_lab(session, cfg, view="not-a-view")
