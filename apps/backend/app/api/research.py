"""Research-lab API (Data Contract: app.engine.research). Three read-only endpoints, each returning the
canonical engine analysis VERBATIM — the view recomputes nothing; it serves aggregations of ALREADY-
STORED forward returns + factor values + excursions:

  - GET /api/research/factor-lab        — `compute_factor_lab` (per factor × horizon: decile table of
    mean forward return + downside risk-adjusted + n, plus rank-IC).
  - GET /api/research/factor-combination — `compute_factor_combination` (the headline composite
    rank-blend cohort + the secondary strict-overlap AND cohort vs baseline vs each single-factor cohort).
  - GET /api/research/event-study        — `compute_event_study` (J-29: per setup/pattern subject ×
    horizon, the forward-return distribution + expectancy + MAE/MFE + downside risk-adjusted ratios +
    best-exit-horizon + by-regime/by-sector slices, from stored values incl. the iter-14 excursions).

Each validates its selectors against the config-driven catalog / `walk_forward.horizons` (422 on an
unknown factor / subject / side / quantile / horizon — no fabricated input); `503` when no price data
exists at all (mirrors the Backtest evidence endpoint; anti-goal: No fabricated data — never an invented
evidence row).

iter-19 (J-32): each endpoint accepts the SINGLE global `as_of` as an OPTIONAL point-in-time scoping
cutoff (a MODE, not a second date state — it is the same global as-of transmitted on every snapshot-
served read, e.g. `/api/stocks?as_of=`). When set, the lab pools ONLY snapshots dated <= D (an expanding
walk-forward window) and echoes the resolved `asof_date`; omitted/null => the default all-history
aggregate (`asof_date` null). The `?as_of=` is validated by the SHARED snapshot-served resolver
(`resolved_date`: unparseable -> 422, future -> 400, before-history -> 400), never hand-rolled — so the
research read path stays consistent with `/api/stocks?as_of=` / `/bars?as_of=`. This is NOT a J-18
violation: the page holds no second/page-local date control; the cutoff is the single global as-of.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.config import Config, get_config
from app.db import get_session
from app.engine.prices import latest_data_date
from app.engine.research import (
    ALL_VIEWS,
    VIEW_EPISODES,
    compute_factor_lab,
    downtrend_opportunity_cached,
    event_study_cached,
    factor_catalog,
    factor_combination_cached,
    factor_lab_all_cached,
    recovery_turn_edge_cached,
    regime_setup_pattern_cached,
    severity_velocity_cached,
    subject_catalog,
)
from app.engine.samples import (
    ALL_KINDS,
    KIND_COMBINATION,
    KIND_DOWNTREND_OPPORTUNITY,
    KIND_EVENT_STUDY,
    KIND_FACTOR,
    KIND_RECOVERY_TURN,
    KIND_REGIME_SETUP_PATTERN,
    compute_samples,
)
from app.engine.snapshot_serving import resolved_date

router = APIRouter(tags=["research"])

# the two condition sides (a catalog factor's top or bottom quantile tail). A fixed structural
# vocabulary (not a tunable) — only the quantile fractions + condition limits + defaults are config.
_CONDITION_SIDES = ("top", "bottom")


@router.get("/research/factor-lab")
def factor_lab(
    factor: Optional[str] = Query(default=None, description="factor key; defaults to the first catalog factor"),
    horizon: Optional[int] = Query(default=None, description="forward window in trading days; defaults to config default_horizon"),
    all: bool = Query(
        default=False,
        description="when true (J-107) serve the ALL-FACTORS aggregate (one entry per catalog factor: family + rank-IC + downside risk-adjusted + decile table) instead of the single `factor`",
    ),
    as_of: Optional[str] = Query(
        default=None,
        description="optional point-in-time cutoff (YYYY-MM-DD) — the single global as-of; omitted = all-history",
    ),
    session: Session = Depends(get_session),
) -> dict:
    """Serve the Factor Lab. By default this is the single-factor view for the requested `factor` +
    `horizon` (defaults: first catalog factor / config default_horizon). When `all=true` (J-107) it serves
    the ALL-FACTORS aggregate on this SAME endpoint (no new endpoint): a `factors_table` block with one entry
    per config-catalog factor (family + Spearman rank-IC + the downside risk-adjusted figure + that factor's
    decile table), every figure BYTE-IDENTICAL to the single-factor view and served from the derived-once
    `EventStudyCache`. Validates `factor` (single-factor view only) + `horizon` against the config-driven
    catalog / `walk_forward.horizons` (422 otherwise); 503 when no price data exists. The optional `as_of`
    (J-32) scopes the pool to snapshots dated <= D (the single global as-of — a mode, not a second date
    state); omitted = all-history. The payload is the canonical analysis verbatim — never recomputed in the
    view."""
    cfg: Config = get_config()
    wf = cfg.walk_forward

    if latest_data_date(session) is None:
        raise HTTPException(status_code=503, detail="no price data available")

    resolved_horizon = wf.default_horizon if horizon is None else horizon
    if resolved_horizon not in wf.horizons:
        raise HTTPException(
            status_code=422,
            detail=f"unknown horizon {resolved_horizon}; valid horizons are {list(wf.horizons)}",
        )

    # iter-19 (J-32): the optional single global as-of scoping cutoff, validated by the SHARED
    # snapshot-served resolver (unparseable -> 422, future/before-history -> 400) — never hand-rolled.
    # Omitted/empty -> all-history (no cutoff). This is the same global as-of transmitted on a
    # snapshot-served read, NOT a second/page-local date state (J-18).
    cutoff = resolved_date(session, as_of, cfg) if as_of else None

    # J-107: the all-factors aggregate (the `factor` selector is N/A here — the table shows every catalog
    # factor at once). Served from the derived-once cache (byte-identical to a fresh compute; refreshes via
    # the dataset-version key) — never recomputed per request.
    if all:
        return factor_lab_all_cached(session, resolved_horizon, cfg, as_of=cutoff)

    valid_factors = [f["key"] for f in factor_catalog(cfg)]
    resolved_factor = valid_factors[0] if factor is None else factor
    if resolved_factor not in valid_factors:
        raise HTTPException(
            status_code=422,
            detail=f"unknown factor {resolved_factor!r}; valid factors are {valid_factors}",
        )

    return compute_factor_lab(session, resolved_factor, resolved_horizon, cfg, as_of=cutoff)


@router.get("/research/factor-combination")
def factor_combination(
    condition: Optional[list[str]] = Query(
        default=None,
        description="repeatable '<factor_key>:<side>:<quantile_key>'; defaults to config default_conditions",
    ),
    horizon: Optional[int] = Query(
        default=None, description="forward window in trading days; defaults to config default_horizon"
    ),
    as_of: Optional[str] = Query(
        default=None,
        description="optional point-in-time cutoff (YYYY-MM-DD) — the single global as-of; omitted = all-history",
    ),
    session: Session = Depends(get_session),
) -> dict:
    """Serve the multi-factor combination cohort analysis (J-26) for the requested `condition`s +
    `horizon` (the SINGLE canonical endpoint for this NEW value). Each `condition` is
    `"<factor_key>:<side>:<quantile_key>"`; an empty/omitted `condition` uses
    `config.research.factor_lab.combination.default_conditions`. Validates the condition count against
    `[min_conditions, max_conditions]`, each `factor_key` against the config-driven catalog, `side`
    against {top, bottom}, `quantile_key` against the config quantiles, and `horizon` against
    `walk_forward.horizons` (422 on any violation — no fabricated factor/side/quantile/horizon); 503 when
    no price data exists. The optional `as_of` (J-32) scopes the pool to snapshots dated <= D (the single
    global as-of — a mode, not a second date state); omitted = all-history. The payload is
    `compute_factor_combination(...)` verbatim — never recomputed in the view."""
    cfg: Config = get_config()
    comb = cfg.research.factor_lab.combination
    wf = cfg.walk_forward

    if latest_data_date(session) is None:
        raise HTTPException(status_code=503, detail="no price data available")

    # empty/omitted condition -> the config-driven canonical default; else parse each "f:side:q" triple.
    if not condition:
        conditions = [
            {"factor": c.factor, "side": c.side, "quantile": c.quantile}
            for c in comb.default_conditions
        ]
    else:
        conditions = []
        for spec in condition:
            parts = spec.split(":")  # exactly the 3 parts of "<factor_key>:<side>:<quantile_key>"
            if len(parts) != 3:
                raise HTTPException(
                    status_code=422,
                    detail=f"condition {spec!r} must be '<factor_key>:<side>:<quantile_key>'",
                )
            conditions.append({"factor": parts[0], "side": parts[1], "quantile": parts[2]})

    if not (comb.min_conditions <= len(conditions) <= comb.max_conditions):
        raise HTTPException(
            status_code=422,
            detail=(
                f"condition count {len(conditions)} must be in "
                f"[{comb.min_conditions}, {comb.max_conditions}]"
            ),
        )

    valid_factors = [f["key"] for f in factor_catalog(cfg)]
    valid_quantiles = [q.key for q in comb.quantiles]
    for c in conditions:
        if c["factor"] not in valid_factors:
            raise HTTPException(
                status_code=422,
                detail=f"unknown factor {c['factor']!r}; valid factors are {valid_factors}",
            )
        if c["side"] not in _CONDITION_SIDES:
            raise HTTPException(
                status_code=422,
                detail=f"unknown side {c['side']!r}; valid sides are {list(_CONDITION_SIDES)}",
            )
        if c["quantile"] not in valid_quantiles:
            raise HTTPException(
                status_code=422,
                detail=f"unknown quantile {c['quantile']!r}; valid quantiles are {valid_quantiles}",
            )

    resolved_horizon = wf.default_horizon if horizon is None else horizon
    if resolved_horizon not in wf.horizons:
        raise HTTPException(
            status_code=422,
            detail=f"unknown horizon {resolved_horizon}; valid horizons are {list(wf.horizons)}",
        )

    # iter-19 (J-32): the optional single global as-of scoping cutoff (shared resolver — 422/400; never
    # hand-rolled). Omitted/empty -> all-history. Not a second date state (J-18).
    cutoff = resolved_date(session, as_of, cfg) if as_of else None
    # J-104(a): serve from the persisted/cached derived aggregate (byte-identical to a fresh compute; the
    # cache refreshes after any dataset change via the dataset-version key) — never recomputed per request.
    return factor_combination_cached(session, conditions, resolved_horizon, cfg, as_of=cutoff)


@router.get("/research/event-study")
def event_study(
    subject: Optional[str] = Query(default=None, description="subject key (setup or pattern); defaults to the first catalog subject"),
    horizon: Optional[int] = Query(default=None, description="forward window in trading days; defaults to config default_horizon"),
    view: Optional[str] = Query(
        default=None,
        description="overlap-honesty view: episodes (default — first-trigger) | pooled (per-signal-day)",
    ),
    as_of: Optional[str] = Query(
        default=None,
        description="optional point-in-time cutoff (YYYY-MM-DD) — the single global as-of; omitted = all-history",
    ),
    session: Session = Depends(get_session),
) -> dict:
    """Serve the Setup & Pattern event study (J-29 / J-63) for the requested `subject` + `horizon` + `view`
    (defaults: the first catalog subject / config default_horizon / `episodes`). Validates `subject` against
    the config-driven subject catalog (setups + patterns), `horizon` against `walk_forward.horizons`, and
    `view` against {episodes, pooled} (422 otherwise); 503 when no price data exists — mirroring the
    factor-lab / factor-combination handlers exactly. `view` (J-63) is a cohort/MODE selector: `episodes`
    (the default) collapses each continuous run of a symbol triggering the subject into ONE first-trigger
    observation; `pooled` keeps every per-signal-day occurrence (byte-identical to the prior figures). It is
    orthogonal to `as_of` and the page analysis-mode — never a second date state (J-18). The optional
    `as_of` (J-32) scopes every member to snapshots dated <= D (the single global as-of — a mode, not a
    second date state); omitted = all-history. The payload is `compute_event_study(...)` verbatim — a
    read-only aggregation of ALREADY-STORED forward returns + excursions, never recomputed in the view."""
    cfg: Config = get_config()
    wf = cfg.walk_forward

    if latest_data_date(session) is None:
        raise HTTPException(status_code=503, detail="no price data available")

    valid_subjects = [s["key"] for s in subject_catalog(cfg)]
    resolved_subject = valid_subjects[0] if subject is None else subject
    if resolved_subject not in valid_subjects:
        raise HTTPException(
            status_code=422,
            detail=f"unknown subject {resolved_subject!r}; valid subjects are {valid_subjects}",
        )

    resolved_horizon = wf.default_horizon if horizon is None else horizon
    if resolved_horizon not in wf.horizons:
        raise HTTPException(
            status_code=422,
            detail=f"unknown horizon {resolved_horizon}; valid horizons are {list(wf.horizons)}",
        )

    # J-63: the optional overlap-honesty view (episodes default | pooled), validated to the two allowed
    # values (422 on anything else — same pattern as subject/horizon). A cohort/mode selector, not a date.
    resolved_view = VIEW_EPISODES if view is None else view
    if resolved_view not in ALL_VIEWS:
        raise HTTPException(
            status_code=422,
            detail=f"unknown view {resolved_view!r}; valid views are {list(ALL_VIEWS)}",
        )

    # iter-19 (J-32): the optional single global as-of scoping cutoff (shared resolver — 422/400; never
    # hand-rolled). Omitted/empty -> all-history. Not a second date state (J-18).
    cutoff = resolved_date(session, as_of, cfg) if as_of else None
    # J-72: serve from the persisted/cached derived aggregate (byte-identical to a fresh compute; the
    # cache refreshes after any dataset change via the dataset-version key) — never recomputed per request.
    return event_study_cached(
        session, resolved_subject, resolved_horizon, cfg, as_of=cutoff, view=resolved_view
    )


@router.get("/research/regime-setup-pattern")
def regime_setup_pattern(
    horizon: Optional[int] = Query(default=None, description="forward window in trading days; defaults to config default_horizon"),
    view: Optional[str] = Query(
        default=None,
        description="overlap-honesty view: episodes (default — first-trigger) | pooled (per-signal-day)",
    ),
    as_of: Optional[str] = Query(
        default=None,
        description="optional point-in-time cutoff (YYYY-MM-DD) — the single global as-of; omitted = all-history",
    ),
    session: Session = Depends(get_session),
) -> dict:
    """Serve the Regime × Setup × Pattern ranked combinations study (J-77) for the requested `horizon` +
    `view` (defaults: config default_horizon / `episodes`). Validates `horizon` against
    `walk_forward.horizons` and `view` against {episodes, pooled} (422 otherwise); 503 when no price data
    exists — mirroring the sibling research handlers exactly. The optional `as_of` (J-32) scopes the pool
    to snapshots dated <= D (the single global as-of — a mode, not a second date state); omitted =
    all-history. The payload is `compute_regime_setup_pattern_study(...)` verbatim — a read-only grouping
    of ALREADY-STORED forward returns + stored regime / setup / pattern flags, never recomputed in the
    view. Default ranked by the downside risk-adjusted figure."""
    cfg: Config = get_config()
    wf = cfg.walk_forward

    if latest_data_date(session) is None:
        raise HTTPException(status_code=503, detail="no price data available")

    resolved_horizon = wf.default_horizon if horizon is None else horizon
    if resolved_horizon not in wf.horizons:
        raise HTTPException(
            status_code=422,
            detail=f"unknown horizon {resolved_horizon}; valid horizons are {list(wf.horizons)}",
        )

    resolved_view = VIEW_EPISODES if view is None else view
    if resolved_view not in ALL_VIEWS:
        raise HTTPException(
            status_code=422,
            detail=f"unknown view {resolved_view!r}; valid views are {list(ALL_VIEWS)}",
        )

    cutoff = resolved_date(session, as_of, cfg) if as_of else None
    # J-104(a): serve from the persisted/cached derived aggregate (byte-identical to a fresh compute; the
    # cache refreshes after any dataset change via the dataset-version key) — never recomputed per request.
    return regime_setup_pattern_cached(
        session, resolved_horizon, cfg, as_of=cutoff, view=resolved_view
    )


@router.get("/research/severity-velocity")
def severity_velocity(
    horizon: Optional[int] = Query(default=None, description="forward window in trading days; defaults to config default_horizon"),
    as_of: Optional[str] = Query(
        default=None,
        description="optional point-in-time cutoff (YYYY-MM-DD) — the single global as-of; omitted = all-history",
    ),
    session: Session = Depends(get_session),
) -> dict:
    """Serve the Severity-velocity × Regime forward-return study (J-103) for the requested `horizon`
    (defaults: config default_horizon). Builds a regime-family × velocity-sign matrix of the stored
    benchmark (SPY) forward return (mean / win-rate / N per cell) by GROUPING the stored `forward_returns`
    joined to the served `severity_velocity` (J-102) + the stored regime label per snapshot date — it
    recomputes no canonical return / regime / slope (Single source of truth; No recompute in the read path).
    Validates `horizon` against `walk_forward.horizons` (422 otherwise); 503 when no price data exists —
    mirroring the sibling research handlers exactly. The optional `as_of` (J-32) scopes the pool + the served
    velocity to snapshots dated <= D (the single global as-of — a mode, not a second date state); omitted =
    all-history (the default aggregate). The payload is `severity_velocity_cached(...)` verbatim — a read-only
    grouping of ALREADY-STORED forward returns, never recomputed in the view. No order/execution affordance
    (research evidence only)."""
    cfg: Config = get_config()
    wf = cfg.walk_forward

    if latest_data_date(session) is None:
        raise HTTPException(status_code=503, detail="no price data available")

    resolved_horizon = wf.default_horizon if horizon is None else horizon
    if resolved_horizon not in wf.horizons:
        raise HTTPException(
            status_code=422,
            detail=f"unknown horizon {resolved_horizon}; valid horizons are {list(wf.horizons)}",
        )

    cutoff = resolved_date(session, as_of, cfg) if as_of else None
    return severity_velocity_cached(session, resolved_horizon, cfg, as_of=cutoff)


@router.get("/research/recovery-turn-edge")
def recovery_turn_edge(
    horizon: Optional[int] = Query(default=None, description="forward window in trading days; defaults to config default_horizon"),
    view: Optional[str] = Query(
        default=None,
        description="overlap-honesty view: episodes (default — first-trigger) | pooled (per-signal-day)",
    ),
    as_of: Optional[str] = Query(
        default=None,
        description="optional point-in-time cutoff (YYYY-MM-DD) — the single global as-of; omitted = all-history",
    ),
    session: Session = Depends(get_session),
) -> dict:
    """Serve the Recovery-Turn Edge study (J-90) for the requested `horizon` + `view` (defaults: config
    default_horizon / `episodes`). Pools the stored forward returns of every CAUSAL recovery-turn signal
    date (from the read-only `market_phase` derivation — never recomputed) and reports the per-horizon
    forward-return edge (distribution + expectancy + downside risk-adjusted + aggregate max-drawdown) plus
    the by-signal-phase conditioning slice. Validates `horizon` against `walk_forward.horizons` and `view`
    against {episodes, pooled} (422 otherwise); 503 when no price data exists — mirroring the sibling
    research handlers exactly. The optional `as_of` (J-32) scopes the pool to snapshots dated <= D (the
    single global as-of — a mode, not a second date state); omitted = all-history. The payload is
    `recovery_turn_edge_cached(...)` verbatim — a read-only aggregation of ALREADY-STORED forward returns,
    never recomputed in the view. No order/execution affordance (recovery-only descriptive evidence)."""
    cfg: Config = get_config()
    wf = cfg.walk_forward

    if latest_data_date(session) is None:
        raise HTTPException(status_code=503, detail="no price data available")

    resolved_horizon = wf.default_horizon if horizon is None else horizon
    if resolved_horizon not in wf.horizons:
        raise HTTPException(
            status_code=422,
            detail=f"unknown horizon {resolved_horizon}; valid horizons are {list(wf.horizons)}",
        )

    resolved_view = VIEW_EPISODES if view is None else view
    if resolved_view not in ALL_VIEWS:
        raise HTTPException(
            status_code=422,
            detail=f"unknown view {resolved_view!r}; valid views are {list(ALL_VIEWS)}",
        )

    cutoff = resolved_date(session, as_of, cfg) if as_of else None
    return recovery_turn_edge_cached(
        session, resolved_horizon, cfg, as_of=cutoff, view=resolved_view
    )


@router.get("/research/downtrend-opportunity")
def downtrend_opportunity(
    horizon: Optional[int] = Query(default=None, description="forward window in trading days; defaults to config default_horizon"),
    view: Optional[str] = Query(
        default=None,
        description="overlap-honesty view: episodes (default — first-trigger) | pooled (per-signal-day)",
    ),
    as_of: Optional[str] = Query(
        default=None,
        description="optional point-in-time cutoff (YYYY-MM-DD) — the single global as-of; omitted = all-history",
    ),
    session: Session = Depends(get_session),
) -> dict:
    """Serve the Downtrend Opportunity study (J-91) for the requested `horizon` + `view` (defaults: config
    default_horizon / `episodes`). Conditions the EXISTING forward-return evidence on the CAUSAL as-of
    downtrend state (phase / severity band / P(bear) band, all <= D, from the read-only `market_phase`
    derivation — never recomputed) and returns THREE angles: (a) held-up-best, (b) fell-hardest (EVIDENCE
    ONLY — no order/execution affordance), and (c) the J-90 recovery-turn edge (reused verbatim). Validates
    `horizon` against `walk_forward.horizons` and `view` against {episodes, pooled} (422 otherwise); 503
    when no price data exists — mirroring the sibling research handlers exactly. The optional `as_of` (J-32)
    scopes the pool + the causal context to snapshots dated <= D (the single global as-of — a mode, not a
    second date state); omitted = all-history. The payload is `downtrend_opportunity_cached(...)` verbatim —
    a read-only grouping of ALREADY-STORED forward returns by the causal conditioning tag, never recomputed
    in the view. ADDITIVE — J-29/J-63/J-77/J-90 figures stay byte-identical."""
    cfg: Config = get_config()
    wf = cfg.walk_forward

    if latest_data_date(session) is None:
        raise HTTPException(status_code=503, detail="no price data available")

    resolved_horizon = wf.default_horizon if horizon is None else horizon
    if resolved_horizon not in wf.horizons:
        raise HTTPException(
            status_code=422,
            detail=f"unknown horizon {resolved_horizon}; valid horizons are {list(wf.horizons)}",
        )

    resolved_view = VIEW_EPISODES if view is None else view
    if resolved_view not in ALL_VIEWS:
        raise HTTPException(
            status_code=422,
            detail=f"unknown view {resolved_view!r}; valid views are {list(ALL_VIEWS)}",
        )

    cutoff = resolved_date(session, as_of, cfg) if as_of else None
    return downtrend_opportunity_cached(
        session, resolved_horizon, cfg, as_of=cutoff, view=resolved_view
    )


@router.get("/research/samples")
def research_samples(
    kind: str = Query(description="analysis kind: factor | combination | event-study"),
    horizon: Optional[int] = Query(default=None, description="forward window in trading days; defaults to config default_horizon"),
    # factor-cohort selectors
    factor: Optional[str] = Query(default=None, description="factor key (factor kind)"),
    slice: Optional[str] = Query(default=None, description="factor: total|decile|regime · event-study: pooled|regime|sector"),
    decile: Optional[int] = Query(default=None, description="1..deciles_count (factor decile cohort)"),
    regime: Optional[str] = Query(default=None, description="a configured regime label (by-regime cohort)"),
    sector: Optional[str] = Query(default=None, description="a stored sector (event-study by-sector cohort)"),
    # combination-cohort selectors
    condition: Optional[list[str]] = Query(default=None, description="repeatable '<factor_key>:<side>:<quantile_key>' (combination kind)"),
    cohort: Optional[str] = Query(default=None, description="combination: baseline|single|composite|strict_overlap"),
    single_index: Optional[int] = Query(default=None, description="0-based condition index (combination single cohort)"),
    # event-study selector
    subject: Optional[str] = Query(default=None, description="subject key: setup or pattern (event-study kind)"),
    view: Optional[str] = Query(
        default=None,
        description="overlap-honesty view: episodes (default) | pooled (event-study & regime-setup-pattern kinds)",
    ),
    # regime-setup-pattern selector (J-77)
    setup: Optional[str] = Query(default=None, description="setup status (regime-setup-pattern kind)"),
    pattern: Optional[str] = Query(default=None, description="pattern key or 'none' (regime-setup-pattern kind)"),
    # recovery-turn selector (J-90) — reuses `slice` (total|phase); `phase` is a market-phase label
    phase: Optional[str] = Query(default=None, description="a market-phase label (recovery-turn by-phase cohort)"),
    # downtrend-opportunity selector (J-91) — `dimension` (phase|severity_band|pbear_band) + `cohort` (the
    # cohort key in that dimension's config catalog)
    dimension: Optional[str] = Query(default=None, description="downtrend conditioning dimension (phase|severity_band|pbear_band)"),
    # severity-velocity selector (J-103) — `family` (a regime family key) + `velocity_sign` (rising|flat|falling)
    family: Optional[str] = Query(default=None, description="a regime family key (severity-velocity kind)"),
    velocity_sign: Optional[str] = Query(default=None, description="a velocity sign key: rising|flat|falling (severity-velocity kind)"),
    as_of: Optional[str] = Query(
        default=None,
        description="optional point-in-time cutoff (YYYY-MM-DD) — the single global as-of; omitted = all-history",
    ),
    session: Session = Depends(get_session),
) -> dict:
    """Serve the Research samples drill-down (J-51 / J-52): the exact member observations behind ONE
    published `N=` figure on `/research`. SELECT-only — it reproduces the cohort the published N was
    counted from (same observation builder + same membership path) and lists its rows; the response
    `total` EQUALS that published N by construction (count-coherence keystone). Each row is ticker +
    snapshot (as-of) date + the qualifying stored value(s) + the realized forward return at the stated
    horizon. A VALID n=0 cohort returns an empty `rows` + `total` 0 (never a fabricated row); an INVALID
    selector (unknown kind/factor/subject/horizon, decile out of range, malformed condition) is an
    explicit 4xx (never a silent empty 200). The optional `as_of` (J-32) scopes the pool to snapshots
    dated <= D (the single global as-of — a mode, not a second date state); omitted = all-history."""
    cfg: Config = get_config()
    wf = cfg.walk_forward

    if latest_data_date(session) is None:
        raise HTTPException(status_code=503, detail="no price data available")

    if kind not in ALL_KINDS:
        raise HTTPException(status_code=422, detail=f"unknown kind {kind!r}; valid kinds are {list(ALL_KINDS)}")

    resolved_horizon = wf.default_horizon if horizon is None else horizon
    if resolved_horizon not in wf.horizons:
        raise HTTPException(
            status_code=422,
            detail=f"unknown horizon {resolved_horizon}; valid horizons are {list(wf.horizons)}",
        )

    # J-63: the overlap-honesty view (episodes default | pooled). Validated to the two allowed values for
    # the event-study AND regime-setup-pattern kinds (422 otherwise); ignored for other kinds. A cohort/
    # mode selector, not a date.
    resolved_view: Optional[str] = None
    if kind in (KIND_EVENT_STUDY, KIND_REGIME_SETUP_PATTERN, KIND_RECOVERY_TURN, KIND_DOWNTREND_OPPORTUNITY):
        resolved_view = VIEW_EPISODES if view is None else view
        if resolved_view not in ALL_VIEWS:
            raise HTTPException(
                status_code=422,
                detail=f"unknown view {resolved_view!r}; valid views are {list(ALL_VIEWS)}",
            )

    # parse the combination conditions (each "<factor_key>:<side>:<quantile_key>") up front so a malformed
    # triple is an explicit 422 before the engine runs (mirrors the factor-combination handler exactly).
    conditions: Optional[list[dict]] = None
    if kind == KIND_COMBINATION:
        if not condition:
            # the config-driven canonical default cohort (same as the Combination Lab's default chips)
            conditions = [
                {"factor": c.factor, "side": c.side, "quantile": c.quantile}
                for c in cfg.research.factor_lab.combination.default_conditions
            ]
        else:
            conditions = []
            for spec in condition:
                parts = spec.split(":")
                if len(parts) != 3:
                    raise HTTPException(
                        status_code=422,
                        detail=f"condition {spec!r} must be '<factor_key>:<side>:<quantile_key>'",
                    )
                conditions.append({"factor": parts[0], "side": parts[1], "quantile": parts[2]})

    # iter-7 (J-32): the optional single global as-of scoping cutoff, validated by the SHARED snapshot-
    # served resolver (unparseable -> 422, future/before-history -> 400) — never hand-rolled. Not a second
    # date state (J-18). All other invalid selectors raise ValueError in the engine -> 422 below.
    cutoff = resolved_date(session, as_of, cfg) if as_of else None
    try:
        return compute_samples(
            session, kind=kind, horizon=resolved_horizon, config=cfg, as_of=cutoff,
            factor_key=factor, slice_kind=slice, decile=decile, regime=regime, sector=sector,
            conditions=conditions, cohort_kind=cohort, single_index=single_index,
            subject_key=subject, view=resolved_view,
            setup=setup, pattern=pattern, phase=phase,
            dimension=dimension,
            family=family, velocity_sign=velocity_sign,
        )
    except ValueError as exc:
        # an unknown/out-of-range cohort selector is an explicit 4xx — never a silent empty 200 (which is
        # reserved for a VALID n=0 cohort). 422 mirrors the sibling research handlers.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
