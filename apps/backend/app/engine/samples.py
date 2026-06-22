"""Research samples drill-down engine (Data Contract: app.engine.samples — J-51 / J-52).

A SELECT-only exposure of the SAME per-observation pools the three research labs already assemble. Every
published `N=` figure on `/research` is the count of one cohort slice; this module reproduces that exact
cohort and lists its member observations — one row per observation: ticker, snapshot (as-of) date, the
qualifying stored factor/indicator value(s) (or, for an event study, the matched setup/pattern), and the
stored realized forward return at the stated horizon. The drill-down `total` ALWAYS equals the published N
(count-coherence keystone — invariant 13), because membership is derived through the EXACT same code paths
the aggregates use:

  - factor cohorts          → `research._factor_observations` (+ `_decile_member_slice` for a per-decile
                              cohort; + the stored-`regime` filter for a by-regime cohort) — the SAME
                              ascending-by-factor ordering + quantile edges `compute_factor_lab` reads.
  - combination cohorts     → `research._combination_observations` (+ `_combination_cohort_members` for the
                              single/strict/composite index sets) — the SAME membership `compute_factor_
                              combination` publishes.
  - event-study cohorts     → `research._event_study_members` (+ the stored-`regime`/`sector` filter for a
                              by-regime / by-sector slice) — the SAME pool `compute_event_study` groups.

THREE non-negotiable disciplines (mirroring `app.engine.research`):

  1. READ-ONLY / NO RECOMPUTE. This module issues only SELECTs (the reused builders + a `run_id → asof_date`
     map) and pure index arithmetic. It recomputes NO factor, NO return, NO regime, NO membership rule —
     every displayed value is the stored per-observation value the aggregate consumed, read VERBATIM.

  2. SINGLE MEMBERSHIP RULE. A cohort's members come from the SAME builder + the SAME slicing helper the
     aggregate used (never a second "equivalent" filter), so `total == published N` by construction.

  3. NO FABRICATION. A VALID n=0 cohort (e.g. an empty strict-overlap) returns an empty list + `total` 0 —
     never a fabricated row. An INVALID cohort selector (unknown kind/factor/subject/horizon, decile out of
     range, malformed condition) raises `ValueError` — the API turns it into an explicit 4xx (never a silent
     empty 200, which is reserved for the valid n=0 case).

The optional `as_of` cutoff (J-32) is the SINGLE global as-of transmitted on the read — a pure membership
FILTER on the opening forward-return query (snapshots dated ≤ D), threaded into the SAME builders. It is a
mode, never a second date state (J-18). `as_of=None` ⇒ all-history.
"""
from __future__ import annotations

from datetime import date as date_cls
from typing import Optional

from sqlmodel import Session, select

from app.config import Config, get_config
from app.engine.forward_testing import SURVIVORSHIP_BIAS_LABEL
from app.engine.research import (
    ALL_DOWNTREND_DIMENSIONS,
    ALL_VIEWS,
    RESEARCH_CAVEAT,
    VIEW_EPISODES,
    _combination_cohort_members,
    _combination_observations,
    _decile_member_slice,
    _downtrend_dimension_catalog,
    _downtrend_member_dimension_value,
    _downtrend_opportunity_observation_set,
    _event_study_observation_set,
    _factor_observations,
    _recovery_turn_observation_set,
    _regime_setup_pattern_observations,
    _rsp_combination_filter,
    _rsp_combination_members,
    _severity_velocity_member_key,
    _severity_velocity_observation_set,
    factor_catalog,
    pattern_keys,
    subject_catalog,
)
from app.models import ScannerRun

# The analysis kinds a sample cohort can belong to (one per research lab) — a fixed structural vocabulary
# (not a tunable). The API validates `kind` against this set.
KIND_FACTOR = "factor"
KIND_COMBINATION = "combination"
KIND_EVENT_STUDY = "event-study"
KIND_REGIME_SETUP_PATTERN = "regime-setup-pattern"  # J-77 combination drill-down
KIND_RECOVERY_TURN = "recovery-turn"                 # J-90 recovery-turn edge drill-down
KIND_DOWNTREND_OPPORTUNITY = "downtrend-opportunity"  # J-91 downtrend-conditioned opportunity drill-down
KIND_SEVERITY_VELOCITY = "severity-velocity"          # J-103 severity-velocity × regime matrix drill-down
ALL_KINDS = (
    KIND_FACTOR, KIND_COMBINATION, KIND_EVENT_STUDY, KIND_REGIME_SETUP_PATTERN, KIND_RECOVERY_TURN,
    KIND_DOWNTREND_OPPORTUNITY, KIND_SEVERITY_VELOCITY,
)
# The recovery-turn-edge slice families (which published `N=` chip on the Recovery-Turn Edge lab was
# clicked). `total` is the whole signal-date pool at the horizon (== `n` / `n_total`); `phase` is the
# per-signal-phase row.
_RECOVERY_TURN_SLICES = ("total", "phase")

# The factor-cohort slice families (which published `N=` chip on the Factor Lab was clicked). `total` is
# `n_total` / rank-IC n (whole pool); `decile` is one D1…D10 bucket; `regime` is the per-regime split.
_FACTOR_SLICES = ("total", "decile", "regime")
# The combination cohort families (which published `N=` chip on the Combination Lab was clicked).
_COMBINATION_COHORTS = ("baseline", "single", "composite", "strict_overlap")
# The event-study slice families (which published `N=` chip on the Setup & Pattern Lab was clicked).
_EVENT_STUDY_SLICES = ("pooled", "regime", "sector")


def _run_date_map(session: Session) -> dict[int, str]:
    """`run_id → asof_date` (ISO string) over every immutable `scanner_runs` row — read VERBATIM (the
    snapshot date the observation came from; used for the row's snapshot date AND the J-52 `?asof` link).
    A single SELECT; recomputes nothing."""
    return {
        run.id: run.asof_date.isoformat()
        for run in session.exec(select(ScannerRun.id, ScannerRun.asof_date)).all()
    }


# --------------------------------------------------------------------------------------------------
# Factor cohort (Factor Lab — J-25 chips: n_total / rank-IC n / per-decile n / by-regime n)
# --------------------------------------------------------------------------------------------------
def _factor_samples(
    session: Session, cfg: Config, *, factor_key: str, horizon: int, slice_kind: str,
    decile: Optional[int], regime: Optional[str], as_of: Optional[date_cls],
) -> dict:
    """Reproduce a Factor-Lab cohort and list its member observations. `slice_kind`:
      - "total"  → the whole `_factor_observations` pool (== `n_total` == rank-IC n).
      - "decile" → the `decile`-th `_decile_member_slice` of the ascending-by-factor pool (== that decile's n).
      - "regime" → the pool filtered to the stored `regime` label (== that by-regime row's n).
    Each row: ticker, snapshot date, the qualifying stored factor value, the realized forward return."""
    fl = cfg.research.factor_lab
    factor = next((f for f in fl.factors if f.key == factor_key), None)
    if factor is None:
        raise ValueError(
            f"unknown factor {factor_key!r}; valid factors are {[f.key for f in fl.factors]}"
        )

    observations = _factor_observations(session, factor, horizon, as_of)

    if slice_kind == "total":
        members = observations
    elif slice_kind == "decile":
        if decile is None or not (1 <= decile <= fl.deciles):
            raise ValueError(
                f"decile {decile!r} out of range [1, {fl.deciles}] for a factor decile cohort"
            )
        # the SAME ascending-by-factor ordering + deterministic tie-break compute_factor_lab uses, then
        # the SAME quantile-edge slice — so this decile's member list reproduces the aggregate's n exactly.
        ordered = sorted(observations, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))
        members = _decile_member_slice(ordered, fl.deciles, decile)
    elif slice_kind == "regime":
        if regime is None or regime not in cfg.regime.labels:
            raise ValueError(
                f"regime {regime!r} is not a configured regime label {list(cfg.regime.labels)}"
            )
        # the SAME stored-regime grouping `_regime_effectiveness` uses (regime read verbatim, never recomputed)
        members = [o for o in observations if o["regime"] == regime]
    else:
        raise ValueError(f"unknown factor slice {slice_kind!r}; valid slices are {list(_FACTOR_SLICES)}")

    run_dates = _run_date_map(session)
    rows = [
        {
            "ticker": o["ticker"],
            "snapshot_date": run_dates.get(o["run_id"]),
            "regime": o["regime"],
            "values": [{"key": factor.key, "label": factor.label, "value": o["factor"]}],
            "forward_return": o["return"],
        }
        for o in members
    ]
    cohort = {
        "kind": KIND_FACTOR,
        "slice": slice_kind,
        "horizon": horizon,
        "factor": {
            "key": factor.key, "label": factor.label, "family": factor.family,
            "direction": factor.direction, "source": factor.source,
        },
        "decile": decile if slice_kind == "decile" else None,
        "regime": regime if slice_kind == "regime" else None,
        "deciles_count": fl.deciles,
    }
    return {"cohort": cohort, "rows": rows}


# --------------------------------------------------------------------------------------------------
# Combination cohort (Combination Lab — J-26 chips: baseline / single / composite / strict-overlap n)
# --------------------------------------------------------------------------------------------------
def _combination_samples(
    session: Session, cfg: Config, *, conditions: list[dict], horizon: int, cohort_kind: str,
    single_index: Optional[int], as_of: Optional[date_cls],
) -> dict:
    """Reproduce a Combination-Lab cohort and list its member observations. `cohort_kind`:
      - "baseline"       → the whole pool (== `pool_n`).
      - "single"         → the `single_index`-th condition's membership (== that single's n).
      - "composite"      → the composite rank-blend cohort (== the composite's n).
      - "strict_overlap" → the exact AND-intersection (== the strict-overlap n; may be a valid 0).
    Membership is the SAME `_combination_cohort_members` `compute_factor_combination` publishes, so the
    drill-down total equals the published N. Each row carries EVERY referenced factor's stored value."""
    fl = cfg.research.factor_lab
    comb = fl.combination

    if not (comb.min_conditions <= len(conditions) <= comb.max_conditions):
        raise ValueError(
            f"condition count {len(conditions)} out of range "
            f"[{comb.min_conditions}, {comb.max_conditions}]"
        )

    resolved: list[dict] = []
    for cond in conditions:
        factor = next((f for f in fl.factors if f.key == cond.get("factor")), None)
        if factor is None:
            raise ValueError(
                f"unknown factor {cond.get('factor')!r}; valid factors are {[f.key for f in fl.factors]}"
            )
        side = cond.get("side")
        if side not in ("top", "bottom"):
            raise ValueError(f"unknown side {side!r}; valid sides are ['bottom', 'top']")
        quantile = next((q for q in comb.quantiles if q.key == cond.get("quantile")), None)
        if quantile is None:
            raise ValueError(
                f"unknown quantile {cond.get('quantile')!r}; valid quantiles are {[q.key for q in comb.quantiles]}"
            )
        resolved.append({"factor": factor, "side": side, "quantile": quantile})

    distinct_factors = list({c["factor"].key: c["factor"] for c in resolved}.values())
    pool = _combination_observations(session, distinct_factors, horizon, as_of)
    cohort_members = _combination_cohort_members(pool, resolved, comb)

    if cohort_kind == "baseline":
        indices = range(len(pool))
    elif cohort_kind == "single":
        if single_index is None or not (0 <= single_index < len(resolved)):
            raise ValueError(
                f"single condition index {single_index!r} out of range [0, {len(resolved) - 1}]"
            )
        indices = cohort_members["single"][single_index]
    elif cohort_kind == "composite":
        indices = cohort_members["composite"]
    elif cohort_kind == "strict_overlap":
        indices = cohort_members["strict"]
    else:
        raise ValueError(
            f"unknown combination cohort {cohort_kind!r}; valid cohorts are {list(_COMBINATION_COHORTS)}"
        )

    # order-stable member rows: every referenced factor's stored value, read verbatim from the pool obs.
    members = [pool[i] for i in sorted(indices)]
    label_by_key = {f.key: f.label for f in fl.factors}
    run_dates = _run_date_map(session)
    rows = [
        {
            "ticker": o["ticker"],
            "snapshot_date": run_dates.get(o["run_id"]),
            "regime": None,
            "values": [
                {"key": f.key, "label": label_by_key.get(f.key, f.key), "value": o["values"][f.key]}
                for f in distinct_factors
            ],
            "forward_return": o["return"],
        }
        for o in members
    ]
    cohort = {
        "kind": KIND_COMBINATION,
        "cohort": cohort_kind,
        "horizon": horizon,
        "single_index": single_index if cohort_kind == "single" else None,
        "conditions": [
            {
                "factor": {
                    "key": c["factor"].key, "label": c["factor"].label, "family": c["factor"].family,
                    "direction": c["factor"].direction, "source": c["factor"].source,
                },
                "side": c["side"],
                "quantile": {
                    "key": c["quantile"].key, "label": c["quantile"].label, "fraction": c["quantile"].fraction,
                },
            }
            for c in resolved
        ],
        "composite_quantile": {
            "key": comb.composite.quantile,
            "fraction": next(q.fraction for q in comb.quantiles if q.key == comb.composite.quantile),
        },
    }
    return {"cohort": cohort, "rows": rows}


# --------------------------------------------------------------------------------------------------
# Event-study cohort (Setup & Pattern Lab — J-29 chips: per-horizon n / pooled n_total / by-regime / by-sector)
# --------------------------------------------------------------------------------------------------
def _event_study_samples(
    session: Session, cfg: Config, *, subject_key: str, horizon: int, slice_kind: str,
    regime: Optional[str], sector: Optional[str], as_of: Optional[date_cls],
    view: str = VIEW_EPISODES,
) -> dict:
    """Reproduce an event-study cohort and list its member occurrences UNDER THE SELECTED `view` (J-63).
    `view` (default `episodes`) selects the observation set via the SAME builder `compute_event_study`
    uses (`_event_study_observation_set`): in `episodes` the rows are the first-trigger episode collapse
    (one row per continuous run, at its first trigger date); in `pooled` they are every per-signal-day
    occurrence (byte-identical to the pre-J-63 drill-down). So the drill-down total EQUALS the published
    `n` for the SAME `(subject, horizon, view)` cohort in BOTH modes (count-coherence keystone — one
    membership rule, never a second grouping path). `slice_kind`:
      - "pooled" → the whole observation set at this horizon (== per-horizon n / `n` / pooled n_total).
      - "regime" → the set filtered to the stored `regime` label (== that by-regime row's n).
      - "sector" → the set filtered to the stored `sector` (== that by-sector row's n).
    Each row: ticker, snapshot date, the matched setup/pattern (the subject), the realized forward return."""
    if view not in ALL_VIEWS:
        raise ValueError(f"unknown view {view!r}; valid views are {list(ALL_VIEWS)}")
    subjects = subject_catalog(cfg)
    subject = next((s for s in subjects if s["key"] == subject_key), None)
    if subject is None:
        raise ValueError(
            f"unknown subject {subject_key!r}; valid subjects are {[s['key'] for s in subjects]}"
        )

    # the SAME observation builder compute_event_study reads — episode collapse in `episodes`, the raw
    # per-signal-day pool in `pooled` (one membership rule → total == published n in both modes).
    members = _event_study_observation_set(session, subject, horizon, view, as_of)

    if slice_kind == "pooled":
        pass
    elif slice_kind == "regime":
        if regime is None or regime not in cfg.regime.labels:
            raise ValueError(
                f"regime {regime!r} is not a configured regime label {list(cfg.regime.labels)}"
            )
        members = [m for m in members if m["regime"] == regime]
    elif slice_kind == "sector":
        if sector is None:
            raise ValueError("a by-sector event-study cohort requires a `sector`")
        # stored sector read verbatim; a sector with no members is a valid n=0 (empty list, never fabricated)
        members = [m for m in members if m["sector"] == sector]
    else:
        raise ValueError(
            f"unknown event-study slice {slice_kind!r}; valid slices are {list(_EVENT_STUDY_SLICES)}"
        )

    run_dates = _run_date_map(session)
    rows = [
        {
            "ticker": m["ticker"],
            "snapshot_date": run_dates.get(m["run_id"]),
            "regime": m["regime"],
            "sector": m["sector"],
            # the matched setup/pattern — the subject itself (read-only; the member IS an occurrence of it)
            "values": [{"key": subject["key"], "label": subject["label"], "value": subject["label"]}],
            "forward_return": m["return"],
        }
        for m in members
    ]
    cohort = {
        "kind": KIND_EVENT_STUDY,
        "slice": slice_kind,
        "horizon": horizon,
        "subject": subject,
        "view": view,  # J-63: the resolved overlap-honesty view (episodes default | pooled)
        "regime": regime if slice_kind == "regime" else None,
        "sector": sector if slice_kind == "sector" else None,
    }
    return {"cohort": cohort, "rows": rows}


# --------------------------------------------------------------------------------------------------
# Regime × Setup × Pattern cohort (J-77 — the combination table's per-row N= chip)
# --------------------------------------------------------------------------------------------------
def _regime_setup_pattern_samples(
    session: Session, cfg: Config, *, regime: Optional[str], setup: Optional[str],
    pattern: Optional[str], horizon: int, as_of: Optional[date_cls], view: str = VIEW_EPISODES,
) -> dict:
    """Reproduce ONE (regime, setup, pattern) combination cohort from the J-77 study and list its member
    observations UNDER THE SELECTED `view` (J-63). Membership is the SAME `_regime_setup_pattern_
    observations` builder + the SAME `_rsp_combination_filter` predicate `compute_regime_setup_pattern_
    study` aggregates, so the drill-down `total` EQUALS the row's published `n` in BOTH Episodes and
    Pooled modes (count-coherence keystone — one membership rule, never a second grouping).

    J-82(c) — VALIDATION RECONCILIATION: acceptance is reconciled to EXACTLY the set of combinations
    `compute_regime_setup_pattern_study` actually EMITS (the same observation set keyed by the SAME
    `_rsp_combination_members` rule the study groups by) — NOT a re-derived vocabulary cross-product. This
    accepts every row the study renders, INCLUDING a `pattern = none` (PATTERN_NONE) row and any groupable
    regime value the study tie-breaks on (the study uses `r["regime"] or ""`, so an empty/None displayable
    regime must not 4xx), while a genuinely non-emitted combination still raises `ValueError` -> an honest
    4xx (acceptance widened, validation NOT disabled). Vocabularies stay config-backed (the keys come from
    the stored observations' verbatim regime / setup / pattern flags); recomputes nothing. Each row:
    ticker, snapshot date, the matched combination, the realized forward return."""
    if view not in ALL_VIEWS:
        raise ValueError(f"unknown view {view!r}; valid views are {list(ALL_VIEWS)}")

    p_keys = pattern_keys(cfg)
    observations = _regime_setup_pattern_observations(session, horizon, view, cfg, as_of)

    # The EXACT set of (regime, setup, pattern) combinations the study emits — derived ONCE from the SAME
    # observation set via the SAME `_rsp_combination_members` rule the study groups by (count-coherence by
    # construction). A requested combination not in this set is genuinely non-emitted -> honest 4xx.
    emitted = {key for obs in observations for key in _rsp_combination_members(obs, p_keys)}
    if (regime, setup, pattern) not in emitted:
        raise ValueError(
            f"combination (regime={regime!r}, setup={setup!r}, pattern={pattern!r}) is not emitted by "
            f"the regime-setup-pattern study for horizon {horizon} (view={view})"
        )

    members = [
        obs for obs in observations
        if _rsp_combination_filter(obs, regime, setup, pattern, p_keys)
    ]

    run_dates = _run_date_map(session)
    rows = [
        {
            "ticker": m["ticker"],
            "snapshot_date": run_dates.get(m["run_id"]),
            "regime": m["regime"],
            "sector": m["sector"],
            "setup": m["setup_status"],
            "pattern": pattern,
            # the matched combination is the qualifying "value" — read-only (the member IS an occurrence)
            "values": [
                {"key": "regime", "label": "Regime", "value": m["regime"]},
                {"key": "setup", "label": "Setup", "value": m["setup_status"]},
                {"key": "pattern", "label": "Pattern", "value": pattern},
            ],
            "forward_return": m["return"],
        }
        for m in members
    ]
    cohort = {
        "kind": KIND_REGIME_SETUP_PATTERN,
        "horizon": horizon,
        "regime": regime,
        "setup": setup,
        "pattern": pattern,
        "view": view,
    }
    return {"cohort": cohort, "rows": rows}


# --------------------------------------------------------------------------------------------------
# Recovery-Turn cohort (Recovery-Turn Edge Lab — J-90 chips: per-horizon n / pooled n_total / by-phase n)
# --------------------------------------------------------------------------------------------------
def _recovery_turn_samples(
    session: Session, cfg: Config, *, horizon: int, slice_kind: str, phase: Optional[str],
    as_of: Optional[date_cls], view: str = VIEW_EPISODES,
) -> dict:
    """Reproduce a Recovery-Turn Edge cohort and list its member observations UNDER THE SELECTED `view`
    (J-63). Membership is the SAME `_recovery_turn_observation_set` builder `compute_recovery_turn_edge`
    aggregates, so the drill-down `total` EQUALS the published `n` for the SAME `(horizon, view)` cohort in
    BOTH Episodes and Pooled modes AND BOTH All-history and As-of scopes (count-coherence keystone — one
    membership rule, never a second grouping path). `slice_kind`:
      - "total" → the whole signal-date observation set at this horizon (== per-horizon n / `n` / n_total).
      - "phase" → the set filtered to the causal signal-date `phase` (== that by-phase row's n).
    Each row: ticker, snapshot (signal) date, the causal signal-date phase/severity/P(bear), and the
    realized forward return at the stated horizon (read VERBATIM — recomputes nothing)."""
    if view not in ALL_VIEWS:
        raise ValueError(f"unknown view {view!r}; valid views are {list(ALL_VIEWS)}")

    members = _recovery_turn_observation_set(session, horizon, view, cfg, as_of)

    if slice_kind == "total":
        pass
    elif slice_kind == "phase":
        if phase is None or phase not in cfg.market_phase.labels:
            raise ValueError(
                f"phase {phase!r} is not a configured market-phase label {list(cfg.market_phase.labels)}"
            )
        # the SAME causal signal-phase grouping `_recovery_turn_by_phase` uses (phase read from the
        # derivation, never recomputed) — so this by-phase row's member list reproduces the aggregate's n.
        members = [m for m in members if m["signal_phase"] == phase]
    else:
        raise ValueError(
            f"unknown recovery-turn slice {slice_kind!r}; valid slices are {list(_RECOVERY_TURN_SLICES)}"
        )

    run_dates = _run_date_map(session)
    rows = [
        {
            "ticker": m["ticker"],
            "snapshot_date": run_dates.get(m["run_id"]),
            "regime": m["regime"],
            "sector": m["sector"],
            "values": [
                {"key": "signal_date", "label": "Signal date", "value": m["signal_date"]},
                {"key": "signal_phase", "label": "Phase at signal", "value": m["signal_phase"]},
                {"key": "signal_p_bear", "label": "P(bear) at signal", "value": m["signal_p_bear"]},
            ],
            "forward_return": m["return"],
        }
        for m in members
    ]
    cohort = {
        "kind": KIND_RECOVERY_TURN,
        "slice": slice_kind,
        "horizon": horizon,
        "phase": phase if slice_kind == "phase" else None,
        "view": view,
    }
    return {"cohort": cohort, "rows": rows}


# --------------------------------------------------------------------------------------------------
# Downtrend Opportunity cohort (J-91 — the three-angle study's per-row N= chip). A cohort is ONE
# (dimension, cohort-key) conditioned group at a horizon/view: e.g. (severity_band, severe) or (phase,
# Bear) or (pbear_band, extreme). Angles (a) held-up-best + (b) fell-hardest rank the SAME cohorts, so a
# chip from EITHER angle drills into the SAME (dimension, cohort) group — count-coherent in both.
# --------------------------------------------------------------------------------------------------
def _downtrend_opportunity_samples(
    session: Session, cfg: Config, *, dimension: Optional[str], cohort_key: Optional[str],
    horizon: int, as_of: Optional[date_cls], view: str = VIEW_EPISODES,
) -> dict:
    """Reproduce ONE (dimension, cohort) conditioned cohort from the J-91 study and list its member
    observations UNDER THE SELECTED `view` (J-63). Membership is the SAME
    `_downtrend_opportunity_observation_set` builder + the SAME `_downtrend_member_dimension_value`
    predicate `compute_downtrend_opportunity_study` aggregates, so the drill-down `total` EQUALS the row's
    published `n` in BOTH Episodes and Pooled modes AND BOTH All-history and As-of scopes (count-coherence
    keystone — one membership rule, never a second grouping).

    VALIDATION RECONCILIATION (the J-82 lesson): `dimension` must be one of the three conditioning
    dimensions; `cohort_key` must be one the dimension's config-backed catalog actually lists (so EVERY
    displayable row — even an n=0 cohort the study emits as honest NA — resolves 2xx, while a genuinely
    non-catalogued cohort raises `ValueError` -> an honest 4xx). Vocabularies stay config-backed. Each row:
    ticker, snapshot (signal) date, the causal signal-date phase/severity/P(bear), the realized forward
    return at the stated horizon (read VERBATIM — recomputes nothing)."""
    if view not in ALL_VIEWS:
        raise ValueError(f"unknown view {view!r}; valid views are {list(ALL_VIEWS)}")
    if dimension not in ALL_DOWNTREND_DIMENSIONS:
        raise ValueError(
            f"unknown downtrend dimension {dimension!r}; valid dimensions are {list(ALL_DOWNTREND_DIMENSIONS)}"
        )
    catalog = _downtrend_dimension_catalog(cfg)
    valid_keys = [entry["key"] for entry in catalog[dimension]]
    if cohort_key is None or cohort_key not in valid_keys:
        raise ValueError(
            f"cohort {cohort_key!r} is not a {dimension!r} cohort the downtrend-opportunity study emits "
            f"(valid: {valid_keys})"
        )

    observations = _downtrend_opportunity_observation_set(session, horizon, view, cfg, as_of)
    members = [
        obs for obs in observations
        if _downtrend_member_dimension_value(obs, dimension) == cohort_key
    ]

    run_dates = _run_date_map(session)
    rows = [
        {
            "ticker": m["ticker"],
            "snapshot_date": run_dates.get(m["run_id"]),
            "regime": m["regime"],
            "sector": m["sector"],
            "values": [
                {"key": "signal_phase", "label": "Phase at signal", "value": m["signal_phase"]},
                {"key": "signal_severity", "label": "Severity at signal", "value": m["signal_severity"]},
                {"key": "signal_p_bear", "label": "P(bear) at signal", "value": m["signal_p_bear"]},
            ],
            "forward_return": m["return"],
        }
        for m in members
    ]
    cohort = {
        "kind": KIND_DOWNTREND_OPPORTUNITY,
        "horizon": horizon,
        "dimension": dimension,
        "cohort": cohort_key,
        "view": view,
    }
    return {"cohort": cohort, "rows": rows}


# --------------------------------------------------------------------------------------------------
# Severity-velocity × Regime cohort (J-103 — the matrix's per-cell N= chip). A cohort is ONE (regime_family,
# velocity_sign) cell at a horizon: e.g. (risk_off, rising) or (risk_on, falling). The samples drill-down
# reproduces that exact cell from the SAME observation set + the SAME membership rule the study aggregates.
# --------------------------------------------------------------------------------------------------
def _severity_velocity_samples(
    session: Session, cfg: Config, *, family: Optional[str], velocity_sign: Optional[str],
    horizon: int, as_of: Optional[date_cls],
) -> dict:
    """Reproduce ONE (regime_family, velocity_sign) cell from the J-103 study and list its member SPY
    observations. Membership is the SAME `_severity_velocity_observation_set` builder + the SAME
    `_severity_velocity_member_key` rule `compute_severity_velocity_study` aggregates, so the drill-down
    `total` EQUALS the cell's published `n` in BOTH All-history and As-of scopes (count-coherence keystone —
    one membership rule, never a second grouping).

    VALIDATION RECONCILIATION (the J-82 lesson): `family` must be one the config-backed
    `research.severity_velocity.regime_families` lists, and `velocity_sign` one the `velocity_signs` lists,
    so EVERY displayable cell — even an n=0 cell the study emits as honest NA — resolves 2xx, while a
    genuinely non-catalogued family/sign raises `ValueError` -> an honest 4xx. Vocabularies stay config-backed.
    Each row: ticker (SPY), snapshot date, the stored regime label + served severity-velocity, the realized
    forward (market) return at the stated horizon (read VERBATIM — recomputes nothing)."""
    sv = cfg.research.severity_velocity
    valid_families = [f.key for f in sv.regime_families]
    valid_signs = [s.key for s in sv.velocity_signs]
    if family is None or family not in valid_families:
        raise ValueError(
            f"regime family {family!r} is not a configured severity-velocity family {valid_families}"
        )
    if velocity_sign is None or velocity_sign not in valid_signs:
        raise ValueError(
            f"velocity sign {velocity_sign!r} is not a configured velocity sign {valid_signs}"
        )

    observations = _severity_velocity_observation_set(session, horizon, cfg, as_of)
    members = [
        obs for obs in observations
        if _severity_velocity_member_key(obs) == (family, velocity_sign)
    ]

    rows = [
        {
            "ticker": m["ticker"],
            "snapshot_date": m["snapshot_date"],
            "regime": m["regime"],
            "values": [
                {"key": "regime", "label": "Regime", "value": m["regime"]},
                {"key": "severity_velocity", "label": "Severity-velocity", "value": m["severity_velocity"]},
            ],
            "forward_return": m["return"],
        }
        for m in members
    ]
    cohort = {
        "kind": KIND_SEVERITY_VELOCITY,
        "horizon": horizon,
        "family": family,
        "velocity_sign": velocity_sign,
    }
    return {"cohort": cohort, "rows": rows}


# --------------------------------------------------------------------------------------------------
# The single canonical samples read (read-only exposure of the stored observation pools)
# --------------------------------------------------------------------------------------------------
def compute_samples(
    session: Session, *, kind: str, horizon: int, config: Optional[Config] = None,
    as_of: Optional[date_cls] = None,
    # factor cohort selectors
    factor_key: Optional[str] = None, slice_kind: Optional[str] = None,
    decile: Optional[int] = None, regime: Optional[str] = None, sector: Optional[str] = None,
    # combination cohort selectors
    conditions: Optional[list[dict]] = None, cohort_kind: Optional[str] = None,
    single_index: Optional[int] = None,
    # event-study cohort selector
    subject_key: Optional[str] = None,
    view: Optional[str] = None,
    # regime-setup-pattern cohort selector (J-77)
    setup: Optional[str] = None, pattern: Optional[str] = None,
    # recovery-turn cohort selector (J-90) — reuses `slice_kind` (total|phase) + `phase`
    phase: Optional[str] = None,
    # downtrend-opportunity cohort selector (J-91) — `dimension` (phase|severity_band|pbear_band) +
    # `cohort_kind` (the cohort key in that dimension's config catalog)
    dimension: Optional[str] = None,
    # severity-velocity cohort selector (J-103) — `family` (a regime family) + `velocity_sign`
    family: Optional[str] = None, velocity_sign: Optional[str] = None,
) -> dict:
    """The SINGLE canonical Research-samples read (Data Contract value, J-51 / J-52). Reproduces ONE
    published research cohort from the SAME stored per-observation data the aggregate used and returns its
    member observation rows + a `total` that EQUALS the published N (count-coherence keystone). SELECT-only;
    recomputes no factor / return / regime / membership.

    `kind` ∈ {factor, combination, event-study} selects the lab; the per-kind selectors reproduce the exact
    cohort slice. For the event-study kind, `view` (J-63, default `episodes`) selects the overlap-honesty
    observation set (the first-trigger episode collapse vs the raw per-signal-day pool) via the SAME builder
    `compute_event_study` reads — so the drill-down `total` equals the published `n` for the same
    `(subject, horizon, view)` in BOTH modes. Raises `ValueError` for any unknown/out-of-range selector (the
    API → 4xx); a VALID n=0 cohort returns an empty `rows` + `total` 0 (never a fabricated row). `as_of`
    (J-32) optionally scopes every pool to snapshots dated ≤ D (the single global as-of — a mode, not a
    second date state)."""
    cfg = config or get_config()

    if kind == KIND_FACTOR:
        built = _factor_samples(
            session, cfg, factor_key=factor_key, horizon=horizon,
            slice_kind=slice_kind or "total", decile=decile, regime=regime, as_of=as_of,
        )
    elif kind == KIND_COMBINATION:
        built = _combination_samples(
            session, cfg, conditions=conditions or [], horizon=horizon,
            cohort_kind=cohort_kind or "baseline", single_index=single_index, as_of=as_of,
        )
    elif kind == KIND_EVENT_STUDY:
        built = _event_study_samples(
            session, cfg, subject_key=subject_key, horizon=horizon,
            slice_kind=slice_kind or "pooled", regime=regime, sector=sector, as_of=as_of,
            view=view or VIEW_EPISODES,
        )
    elif kind == KIND_REGIME_SETUP_PATTERN:
        built = _regime_setup_pattern_samples(
            session, cfg, regime=regime, setup=setup, pattern=pattern, horizon=horizon,
            as_of=as_of, view=view or VIEW_EPISODES,
        )
    elif kind == KIND_RECOVERY_TURN:
        built = _recovery_turn_samples(
            session, cfg, horizon=horizon, slice_kind=slice_kind or "total", phase=phase,
            as_of=as_of, view=view or VIEW_EPISODES,
        )
    elif kind == KIND_DOWNTREND_OPPORTUNITY:
        built = _downtrend_opportunity_samples(
            session, cfg, dimension=dimension, cohort_key=cohort_kind, horizon=horizon,
            as_of=as_of, view=view or VIEW_EPISODES,
        )
    elif kind == KIND_SEVERITY_VELOCITY:
        built = _severity_velocity_samples(
            session, cfg, family=family, velocity_sign=velocity_sign, horizon=horizon, as_of=as_of,
        )
    else:
        raise ValueError(f"unknown kind {kind!r}; valid kinds are {list(ALL_KINDS)}")

    rows = built["rows"]
    return {
        "kind": kind,
        "horizon": horizon,
        # the resolved as-of scoping cutoff echoed (J-32) — ISO date when scoped, null in all-history mode
        "asof_date": as_of.isoformat() if as_of is not None else None,
        "cohort": built["cohort"],
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "descriptive_caveat": RESEARCH_CAVEAT,
        "total": len(rows),
        "rows": rows,
    }
