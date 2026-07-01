"""Read-only tool functions backing the Trendora MCP "window".

Each function takes a live DB ``Session`` + params and returns the SAME JSON-serializable dict the
matching ``GET /api`` read endpoint returns — by REUSING the exact engine / serving functions the
FastAPI routers call. Output PARITY with the HTTP API is the whole point, so NOTHING is recomputed
here: as-of resolution, snapshot reshaping, factor / event-study / sample aggregation, the market-phase
derivation and the backtest scorecard all delegate to ``app.engine.*`` (the single source of truth).

These functions are transport-free and unit-testable WITHOUT the MCP server: a caller just opens a
session (``Session(get_engine())``, the same way the app does) and calls them directly. The MCP
``server`` module is a thin wrapper that opens a session per tool call and delegates here.

Error semantics mirror the read path: as-of resolution reuses the routers' shared resolvers (so an
invalid / out-of-range ``asof`` raises exactly as the endpoint does), and the research / backtest /
samples tools surface the engines' own ``ValueError`` for an unknown selector (the same condition the
endpoints turn into a 422). Every tool is READ-ONLY — none writes user data; the only inserts are the
read-path *create-once* snapshot + forward-return population the matching endpoints already perform.
"""
from __future__ import annotations

import json
from datetime import date as date_cls
from typing import Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.config import get_config
from app.engine import ledger as ledger_mod
from app.engine import online_fdr
from app.engine.forward_testing import (
    backfill_run_forward_returns,
    benchmark_symbols,
    compute_forward_aggregates,
    compute_run_scorecard,
)
from app.engine.referee import (
    DEFAULT_ALPHA_BUDGET,
    DEFLATION_ONLINE_FDR,
    RefereeState,
    certify_edge,
)
from app.engine.indexes import compute_index_series  # raises UnknownRangeError verbatim on a bad preset
from app.engine.methodology import build_catalog
from app.engine.market_phase import (
    market_phase_default_payload,
    market_phase_full_cached,
    retrospective_cached,
)
from app.engine.prices import latest_data_date
from app.engine.regime_history import get_regime_history as _regime_history_series
from app.engine.research import (
    ALL_VIEWS,
    VIEW_EPISODES,
    compute_factor_lab,
    event_study_cached,
    factor_catalog,
    factor_lab_all_cached,
    subject_catalog,
)
from app.engine.samples import (
    ALL_KINDS,
    KIND_COMBINATION,
    KIND_DOWNTREND_OPPORTUNITY,
    KIND_EVENT_STUDY,
    KIND_PHASE_SEVERITY_LAB,
    KIND_RECOVERY_TURN,
    KIND_REGIME_LAB,
    KIND_REGIME_PHASE_FACTOR,
    KIND_REGIME_SETUP_PATTERN,
    compute_samples,
)
from app.engine.scanner import _latest_stored_run_date
from app.engine.triad_scan import scan_product_triad as _scan_product_triad
from app.engine.snapshot_serving import (
    dashboard_payload,
    resolved_date,
    resolved_run,
    sectors_payload,
    stock_detail_payload,
    stocks_payload,
    themes_payload,
)
from app.models import ForwardReturn, ScannerResult, ScannerRun
from app.seed_loader import DEFAULT_SEED_DIR, load_universe_screen_record

# The detected-pattern flag keys carried on every stored stock row (the `config.patterns` vocabulary).
# The `get_leaderboard` `pattern` filter matches a row whose `row[<pattern>]["flagged"]` is True.
_PATTERN_KEYS = ("vcp", "pullback_to_rising_dma", "flat_base_breakout")


# ==================================================================================================
# Snapshot-served reads — mirror /api/dashboard, /api/stocks(+/{ticker}), /api/sectors, /api/themes.
# Each resolves `asof` via the SAME `snapshot_serving.resolved_run` the routers use, then delegates to
# the SAME reshaper — so the dict is byte-identical to the endpoint payload for the resolved date.
# ==================================================================================================
def get_dashboard(session: Session, asof: Optional[str] = None) -> dict:
    """`GET /api/dashboard` — the market regime panel, universe-relative breadth, and the stored
    candidate counts for the resolved as-of date (latest stored run by default)."""
    return dashboard_payload(resolved_run(session, asof))


def get_leaderboard(
    session: Session,
    asof: Optional[str] = None,
    sector: Optional[str] = None,
    theme: Optional[str] = None,
    pattern: Optional[str] = None,
    ticker: Optional[str] = None,
) -> dict:
    """`GET /api/stocks` — the per-stock leaderboard (three scores + buckets, setup, detected patterns,
    themes, and stored forward returns) for the resolved as-of date.

    With NO filter args this returns the endpoint payload byte-for-byte. The optional filters are a pure
    post-filter over the SAME stored rows (recomputing nothing — the read path the endpoint has no
    query params for, applied here as a convenience): `ticker` (exact, case-insensitive), `sector`
    (the row's stored sector name), `theme` (a theme slug or name on the row), and `pattern` (one of
    vcp / pullback_to_rising_dma / flat_base_breakout — kept when that detected pattern is `flagged`)."""
    payload = stocks_payload(session, resolved_run(session, asof))
    rows = payload["rows"]
    if ticker is not None:
        want = ticker.upper()
        rows = [r for r in rows if r["ticker"].upper() == want]
    if sector is not None:
        want_s = sector.lower()
        rows = [r for r in rows if (r.get("sector") or "").lower() == want_s]
    if theme is not None:
        want_t = theme.lower()
        rows = [
            r
            for r in rows
            if any(
                (t.get("slug", "").lower() == want_t or t.get("name", "").lower() == want_t)
                for t in r.get("themes", [])
            )
        ]
    if pattern is not None:
        key = pattern.lower()
        rows = [r for r in rows if isinstance(r.get(key), dict) and r[key].get("flagged") is True]
    if rows is payload["rows"]:
        return payload  # no filter applied -> byte-identical endpoint payload
    return {**payload, "rows": rows}


def get_stock_evidence(session: Session, ticker: str, asof: Optional[str] = None) -> dict:
    """`GET /api/stocks/{ticker}` — the SAME stored row the leaderboard serves for one ticker (J-06),
    carrying its stored forward returns. Raises for a ticker absent from the resolved run."""
    return stock_detail_payload(session, resolved_run(session, asof), ticker)


def get_sectors(session: Session, asof: Optional[str] = None) -> dict:
    """`GET /api/sectors` — the canonical Sector Score rows (score + bucket + components + the ETF's own
    stored forward returns) for the resolved as-of date."""
    return sectors_payload(session, resolved_run(session, asof))


def get_themes(session: Session, asof: Optional[str] = None) -> dict:
    """`GET /api/themes` — the canonical Theme Score rows (score + bucket + members + the equal-weight
    basket's stored forward returns) for the resolved as-of date."""
    return themes_payload(session, resolved_run(session, asof))


# ==================================================================================================
# Market phase — mirror /api/market-phase (the strictly-causal phase / severity / P(bear) derivation).
# ==================================================================================================
def get_market_phase(
    session: Session,
    asof: Optional[str] = None,
    retrospective: bool = False,
    full: bool = False,
) -> dict:
    """`GET /api/market-phase` — the Market Phase & Severity derivation for the resolved as-of date:
    the discrete phase, the 0-100 severity breakdown, the cycle legs, the forward filtered P(bear), the
    causal timeline + episodes + recovery-turn signal. `full=True` additively attaches the full-history
    `timeline_full` series; `retrospective=True` attaches the fenced (analysis-only, lookahead) smoothed
    P(bear) + true-bear dating under a `retrospective` key — exactly as the endpoint does."""
    resolved = resolved_date(session, asof, None)
    payload = (
        market_phase_full_cached(session, resolved)
        if full
        else market_phase_default_payload(session, resolved)
    )
    if retrospective:
        payload = {**payload, "retrospective": retrospective_cached(session, resolved)}
    return payload


# ==================================================================================================
# Backtest — mirror /api/backtest (per-date forward-test scorecard + as-of-scoped evidence aggregate).
# ==================================================================================================
def query_backtest(session: Session, asof: Optional[str] = None) -> dict:
    """`GET /api/backtest` — the per-date forward-test scorecard (cohort return + excess vs SPY/QQQ/
    sector + the control cohorts, each with sample size `n`) plus the as-of-scoped `evidence_by_horizon`
    aggregate and `is_latest`. Mirrors the endpoint exactly, including the read-path *create-once*
    population of this run's realized forward returns (INSERT-only into the append-only table; a no-op
    once warmed) — it recomputes no score / bucket / return."""
    cfg = get_config()
    run = resolved_run(session, asof, cfg)
    backfill_run_forward_returns(session, run, cfg)  # create-once realized forward returns (as the endpoint does)
    card = compute_run_scorecard(session, run, cfg)
    evidence_by_horizon = {
        h: compute_forward_aggregates(session, h, cfg, as_of=run.asof_date)
        for h in cfg.walk_forward.horizons
    }
    return {
        **card,
        "is_latest": run.asof_date == _latest_stored_run_date(session),
        "evidence_by_horizon": evidence_by_horizon,
    }


# ==================================================================================================
# Research lab — mirror the key /api/research sub-endpoints (factor-lab, event-study, samples).
# Validation mirrors the routers; an unknown selector raises ValueError (the same condition the
# endpoints turn into a 422). `asof` reuses the routers' shared `resolved_date` cutoff.
# ==================================================================================================
def query_factor_lab(
    session: Session,
    factor: Optional[str] = None,
    horizon: Optional[int] = None,
    all_factors: bool = False,
    asof: Optional[str] = None,
) -> dict:
    """`GET /api/research/factor-lab` — the canonical Factor Lab. Single-factor view by default (decile
    table of mean forward return + downside risk-adjusted + n, the Spearman rank-IC, and the by-regime
    effectiveness split) for `factor` (default: first catalog factor) at `horizon` (default: config
    default_horizon). `all_factors=True` serves the all-factors aggregate (the endpoint's `?all=true`).
    Optional `asof` scopes the pool to snapshots dated <= D (the single global as-of); omitted =
    all-history. Raises ValueError for an unknown factor / horizon (the endpoint's 422)."""
    cfg = get_config()
    wf = cfg.walk_forward
    if latest_data_date(session) is None:
        raise ValueError("no price data available")
    resolved_horizon = wf.default_horizon if horizon is None else horizon
    if resolved_horizon not in wf.horizons:
        raise ValueError(f"unknown horizon {resolved_horizon}; valid horizons are {list(wf.horizons)}")
    cutoff = resolved_date(session, asof, cfg) if asof else None
    if all_factors:
        return factor_lab_all_cached(session, cfg, as_of=cutoff)
    valid_factors = [f["key"] for f in factor_catalog(cfg)]
    resolved_factor = valid_factors[0] if factor is None else factor
    if resolved_factor not in valid_factors:
        raise ValueError(f"unknown factor {resolved_factor!r}; valid factors are {valid_factors}")
    return compute_factor_lab(session, resolved_factor, resolved_horizon, cfg, as_of=cutoff)


def query_event_study(
    session: Session,
    subject: Optional[str] = None,
    horizon: Optional[int] = None,
    view: Optional[str] = None,
    asof: Optional[str] = None,
) -> dict:
    """`GET /api/research/event-study` — the Setup & Pattern event study for `subject` (a setup or
    pattern key; default: first catalog subject) at `horizon` (default: config default_horizon) under
    `view` (`episodes` first-trigger default | `pooled` per-signal-day). Forward-return distribution +
    expectancy + MAE/MFE + downside risk-adjusted + best-exit-horizon + by-regime/by-sector slices, all
    from already-stored values. Optional `asof` scopes to snapshots dated <= D. Raises ValueError for an
    unknown subject / horizon / view (the endpoint's 422)."""
    cfg = get_config()
    wf = cfg.walk_forward
    if latest_data_date(session) is None:
        raise ValueError("no price data available")
    valid_subjects = [s["key"] for s in subject_catalog(cfg)]
    resolved_subject = valid_subjects[0] if subject is None else subject
    if resolved_subject not in valid_subjects:
        raise ValueError(f"unknown subject {resolved_subject!r}; valid subjects are {valid_subjects}")
    resolved_horizon = wf.default_horizon if horizon is None else horizon
    if resolved_horizon not in wf.horizons:
        raise ValueError(f"unknown horizon {resolved_horizon}; valid horizons are {list(wf.horizons)}")
    resolved_view = VIEW_EPISODES if view is None else view
    if resolved_view not in ALL_VIEWS:
        raise ValueError(f"unknown view {resolved_view!r}; valid views are {list(ALL_VIEWS)}")
    cutoff = resolved_date(session, asof, cfg) if asof else None
    return event_study_cached(
        session, resolved_subject, resolved_horizon, cfg, as_of=cutoff, view=resolved_view
    )


def drill_samples(
    session: Session,
    kind: str,
    horizon: Optional[int] = None,
    *,
    factor: Optional[str] = None,
    slice_kind: Optional[str] = None,
    decile: Optional[int] = None,
    regime: Optional[str] = None,
    sector: Optional[str] = None,
    condition: Optional[list[str]] = None,
    cohort: Optional[str] = None,
    single_index: Optional[int] = None,
    subject: Optional[str] = None,
    view: Optional[str] = None,
    setup: Optional[str] = None,
    pattern: Optional[str] = None,
    phase: Optional[str] = None,
    dimension: Optional[str] = None,
    family: Optional[str] = None,
    velocity_sign: Optional[str] = None,
    regime_decile: Optional[int] = None,
    severity_decile: Optional[int] = None,
    factor_decile: Optional[int] = None,
    asof: Optional[str] = None,
) -> dict:
    """`GET /api/research/samples` — the research samples drill-down: the exact member observations
    behind ONE published `N=` figure on `/research`. SELECT-only; the response `total` equals the
    published N by construction. `kind` selects the lab (factor | combination | event-study |
    regime-setup-pattern | recovery-turn | downtrend-opportunity | severity-velocity | regime-lab |
    phase-severity-lab | regime-phase-factor); the per-kind selectors reproduce the exact cohort slice.
    Optional `asof` scopes the pool to snapshots dated <= D. Mirrors the endpoint's validation: raises
    ValueError for an unknown kind / horizon / view / malformed condition or any out-of-range selector
    (the endpoint's 422); a VALID n=0 cohort returns an empty `rows` + `total` 0 (never fabricated)."""
    cfg = get_config()
    wf = cfg.walk_forward
    if latest_data_date(session) is None:
        raise ValueError("no price data available")
    if kind not in ALL_KINDS:
        raise ValueError(f"unknown kind {kind!r}; valid kinds are {list(ALL_KINDS)}")
    resolved_horizon = wf.default_horizon if horizon is None else horizon
    if resolved_horizon not in wf.horizons:
        raise ValueError(f"unknown horizon {resolved_horizon}; valid horizons are {list(wf.horizons)}")
    # the overlap-honesty view (episodes default | pooled) — validated for the view-aware kinds only.
    resolved_view: Optional[str] = None
    if kind in (
        KIND_EVENT_STUDY, KIND_REGIME_SETUP_PATTERN, KIND_RECOVERY_TURN, KIND_DOWNTREND_OPPORTUNITY,
        KIND_REGIME_LAB, KIND_PHASE_SEVERITY_LAB, KIND_REGIME_PHASE_FACTOR,
    ):
        resolved_view = VIEW_EPISODES if view is None else view
        if resolved_view not in ALL_VIEWS:
            raise ValueError(f"unknown view {resolved_view!r}; valid views are {list(ALL_VIEWS)}")
    # parse the combination conditions ("<factor_key>:<side>:<quantile_key>") up front, as the router does.
    conditions: Optional[list[dict]] = None
    if kind == KIND_COMBINATION:
        if not condition:
            conditions = [
                {"factor": c.factor, "side": c.side, "quantile": c.quantile}
                for c in cfg.research.factor_lab.combination.default_conditions
            ]
        else:
            conditions = []
            for spec in condition:
                parts = spec.split(":")
                if len(parts) != 3:
                    raise ValueError(f"condition {spec!r} must be '<factor_key>:<side>:<quantile_key>'")
                conditions.append({"factor": parts[0], "side": parts[1], "quantile": parts[2]})
    cutoff = resolved_date(session, asof, cfg) if asof else None
    # compute_samples raises ValueError for any unknown/out-of-range selector (the endpoint -> 422).
    return compute_samples(
        session, kind=kind, horizon=resolved_horizon, config=cfg, as_of=cutoff,
        factor_key=factor, slice_kind=slice_kind, decile=decile, regime=regime, sector=sector,
        conditions=conditions, cohort_kind=cohort, single_index=single_index,
        subject_key=subject, view=resolved_view,
        setup=setup, pattern=pattern, phase=phase,
        dimension=dimension,
        family=family, velocity_sign=velocity_sign,
        regime_decile=regime_decile, severity_decile=severity_decile, factor_decile=factor_decile,
    )


# ==================================================================================================
# Triad scan — the analyst loop's quantitative core. READ-ONLY (never writes the ledger, never spends
# the certification alpha budget): ranks factor cross-over cohorts by the triad and hold-out-screens
# the top out-of-sample, so the goal-proposer can turn survivors into enhancement proposals.
# ==================================================================================================
def scan_product_triad(
    session: Session,
    horizons: Optional[list[int]] = None,
    top_k: Optional[int] = None,
    asof: Optional[str] = None,
) -> dict:
    """The analyst-loop triad scan over the factor cross-over space. Ranks ``(factor, horizon, decile)``
    cohorts by the triad (higher mean forward return / shallower mean max-drawdown / higher frequency),
    hold-out-screens the top cohorts out-of-sample, and returns the screened table + the ``survivors``
    (proposal candidates whose return edge persisted). REUSES ``compute_factor_lab`` verbatim (the
    canonical Factor-Lab read — recomputes nothing, so the scan's numbers match the /research UI).
    READ-ONLY: never writes the certified-claims ledger and never spends the certification alpha budget.
    Optional ``asof`` scopes the pool to snapshots dated <= D. Raises ValueError when no price data."""
    cfg = get_config()
    if latest_data_date(session) is None:
        raise ValueError("no price data available")
    cutoff = resolved_date(session, asof, cfg) if asof else None
    return _scan_product_triad(session, cfg, horizons=horizons, top_k=top_k, as_of=cutoff)


# ==================================================================================================
# Edge certification — the referee. The ONLY tool that writes (the append-only certified-claims
# ledger ONLY; it is READ-ONLY w.r.t. the snapshot DB). It assembles the claim cohort's observations
# (REUSING `drill_samples` -> `compute_samples`, the exact membership the research labs publish) plus a
# same-dates benchmark control (the engine's stored SPY forward returns), reads the cumulative
# n_trials + remaining alpha budget from the ledger, calls the PURE referee, appends the verdict, and
# returns it. The snapshot DB is never mutated — the sole write is the ledger append.
# ==================================================================================================
# The claim selectors mirror `drill_samples` (the cohort is ONE published research `N=` slice).
_CLAIM_SELECTOR_KEYS = (
    "factor", "slice_kind", "decile", "regime", "sector", "condition", "cohort", "single_index",
    "subject", "view", "setup", "pattern", "phase", "dimension", "family", "velocity_sign",
    "regime_decile", "severity_decile", "factor_decile", "asof",
)


def _benchmark_control_observations(
    session: Session, cfg, horizon: int, cohort_dates: set
) -> list[tuple]:
    """The CONTROL cohort: the benchmark SPY's stored realized forward returns at `horizon`, one per
    snapshot (as-of) date, restricted to the dates the claim cohort spans (the same-dates control). This
    REUSES the engine's already-stored `forward_returns` (SELECT-only) and the config benchmark symbol —
    it recomputes nothing. Each observation is ``(asof_date, realized_return)`` keyed to the canonical
    `ScannerRun.asof_date` (so it date-aligns to the cohort rows, which carry that same snapshot date)."""
    spy = benchmark_symbols(cfg)["spy"]
    stmt = (
        select(ScannerRun.asof_date, ForwardReturn.realized_return)
        .join(ScannerRun, ScannerRun.id == ForwardReturn.run_id)
        .where(ForwardReturn.symbol == spy, ForwardReturn.horizon == horizon)
    )
    out: list[tuple] = []
    for asof_date, realized in session.exec(stmt).all():
        if realized is None:
            continue
        if cohort_dates and asof_date not in cohort_dates:
            continue
        out.append((asof_date, realized))
    return out


def assemble_claim_observations(
    session: Session, claim: dict
) -> tuple[list[tuple], list[tuple], int]:
    """Assemble ONE claim's ``(cohort_obs, control_obs, horizon)`` from CURRENT snapshot data — the SHARED
    cohort-assembly seam used by BOTH `verify_edge` (certification) and the forward-walk monitor
    (`app.engine.forward_walk`, the *renewing holdout* that re-scores certified claims as new data arrives).

    Both lists are ``[(asof_date: date, forward_return: float)]``, ready for the PURE referee:
      * the COHORT is the exact published-research membership of the claim's slice, via `drill_samples`
        -> `compute_samples` (the same selectors + validation the research labs publish);
      * the CONTROL is the SAME-DATES benchmark (SPY) realized forward returns.

    Reading the LIVE DB is deliberate and is what makes the forward walk work: as new snapshots are
    ingested and forward returns MATURE, this same claim re-assembles to a LARGER cohort that spans dates
    which did not exist at registration — so a later re-score is judged against a genuinely renewed
    out-of-sample window. Mirrors `verify_edge`'s validation: an unknown kind / horizon / selector raises
    `ValueError`."""
    cfg = get_config()
    if latest_data_date(session) is None:
        raise ValueError("no price data available")
    kind = claim.get("kind")
    if kind not in ALL_KINDS:
        raise ValueError(f"unknown kind {kind!r}; valid kinds are {list(ALL_KINDS)}")
    horizon = claim.get("horizon", cfg.walk_forward.default_horizon)

    # cohort observations — REUSE drill_samples (the exact published-cohort membership + validation).
    selectors = {key: claim[key] for key in _CLAIM_SELECTOR_KEYS if key in claim}
    samples = drill_samples(session, kind=kind, horizon=horizon, **selectors)
    cohort_obs = [
        (date_cls.fromisoformat(row["snapshot_date"]), row["forward_return"])
        for row in samples["rows"]
        if row.get("snapshot_date") and row.get("forward_return") is not None
    ]
    cohort_dates = {d for d, _ in cohort_obs}
    control_obs = _benchmark_control_observations(session, cfg, horizon, cohort_dates)
    return cohort_obs, control_obs, horizon


# The two multiple-testing economies `verify_edge` may run under. CANONICAL is the user-facing
# `/evidence` ledger and is ALWAYS strict Bonferroni (its "Proven" badge keeps its family-wise guarantee).
# STAGING is the INTERNAL exploration ledger; it runs the configured online-FDR economy ONLY when
# `evidence.fdr.enabled` is true, else it too stays Bonferroni (default-off ⇒ byte-identical to canonical).
LEDGER_CANONICAL = "canonical"
LEDGER_STAGING = "staging"


def verify_edge(
    session: Session,
    claim: dict,
    ledger_path: str,
    *,
    register_date: str,
    ledger: str = LEDGER_CANONICAL,
) -> dict:
    """Certify (or reject) a proposed edge and APPEND the verdict to the certified-claims ledger.

    `claim` selects ONE research cohort, mirroring `drill_samples`' selectors, plus a `horizon` and an
    optional claimed `direction` (default ``positive``) / `min_effect_size`::

        {"kind": "factor", "horizon": 20, "factor": "<key>", "slice_kind": "decile", "decile": 10,
         "direction": "positive"}      # or {"kind": "event-study", "subject": "<key>", "horizon": 20}

    `ledger` selects the multiple-testing ECONOMY the referee deflates under (iter-9). `"canonical"` (the
    default) is ALWAYS strict Bonferroni — the user-facing `/evidence` bar keeps its family-wise "Proven"
    guarantee. `"staging"` runs the configured online-FDR (LORD++) economy WHEN `evidence.fdr.enabled` is
    true, else it too stays Bonferroni (default-off ⇒ byte-identical). The economy is a POLICY choice; this
    function stays the SINGLE ledger writer (iter-1 lesson — one writer, routed to the target file), and the
    CALLER passes the target `ledger_path` (canonical vs staging) so the two economies never share a file.

    Procedure (READ-ONLY w.r.t. the snapshot DB — the SOLE write is the ledger append):
      (a) assemble the cohort + same-dates control observations via the shared
          `assemble_claim_observations` seam (also used by the forward-walk monitor);
      (b) read the cumulative `n_trials` + remaining alpha budget from THIS ledger, and (staging + FDR)
          the PASS-ordinal rejection history the online-FDR economy reconstructs its wealth from;
      (c) call the PURE referee under the selected deflation policy -> a `Verdict`;
      (d) append ``{claim, register_date, verdict}`` to THIS ledger (append-only);
      (e) return the verdict dict (+ the assembled context).

    Mirrors `drill_samples`' validation: an unknown kind / horizon / selector raises `ValueError`."""
    # (a) cohort + same-dates control observations — the SHARED assembly seam (reused by forward_walk).
    cohort_obs, control_obs, horizon = assemble_claim_observations(session, claim)

    # (b) cumulative testing state from THIS ledger (this claim's ordinal + remaining budget).
    prior_trials = ledger_mod.count_trials(ledger_path)
    spent = ledger_mod.alpha_spent(ledger_path)
    remaining = DEFAULT_ALPHA_BUDGET - spent
    n_trials = prior_trials + 1

    # (c) select the deflation policy. CANONICAL is ALWAYS Bonferroni (the honesty fence — FDR never touches
    # the user-facing bar). STAGING runs the configured online-FDR economy only when it is enabled; otherwise
    # it too falls back to Bonferroni (default-off preserves byte-identical behavior everywhere).
    cfg = get_config()
    fdr_cfg = cfg.evidence.fdr
    use_fdr = ledger == LEDGER_STAGING and fdr_cfg.enabled
    if use_fdr:
        test_level = online_fdr.test_level(
            n_trials,
            ledger_mod.rejection_offsets(ledger_path),
            alpha=fdr_cfg.alpha,
            w0_fraction=fdr_cfg.w0_fraction,
            gamma_exponent=fdr_cfg.gamma_exponent,
            gamma_terms=fdr_cfg.gamma_terms,
        )
        state = RefereeState(
            n_trials=n_trials, alpha_budget_remaining=remaining,
            deflation=DEFLATION_ONLINE_FDR, test_level=test_level,
        )
    else:
        state = RefereeState(n_trials=n_trials, alpha_budget_remaining=remaining)  # strict Bonferroni

    # the PURE referee — deterministic given the engine's reproducible control-group seed.
    direction = claim.get("direction", "positive")
    extra = {}
    if claim.get("min_effect_size") is not None:
        extra["min_effect_size"] = float(claim["min_effect_size"])
    verdict = certify_edge(
        cohort_obs, control_obs, horizon=horizon, state=state,
        seed=cfg.walk_forward.control_group.seed, direction=direction, **extra,
    )
    verdict_dict = verdict.to_dict()

    # (d) append the verdict to THIS append-only ledger (the ONLY write — the snapshot DB is untouched).
    context = {
        "claim": claim,
        "register_date": register_date,
        "horizon": horizon,
        "cohort_n": len(cohort_obs),
        "control_n": len(control_obs),
    }
    ledger_mod.append_entry(ledger_path, {**context, "verdict": verdict_dict})

    # (e) return the verdict (+ assembled context) to the caller.
    return {
        **context,
        "ledger_path": ledger_path,
        "ledger": ledger,
        "n_trials_before": prior_trials,
        "alpha_budget_remaining_before": remaining,
        "verdict": verdict_dict,
    }


# ==================================================================================================
# Additional read-only mirrors that round out the window over the rest of the read API.
# ==================================================================================================
def get_regime_history(session: Session, asof: Optional[str] = None, full: bool = False) -> dict:
    """`GET /api/regime-history` — the stored per-date `{date -> {label, score}}` market-regime series,
    bounded to dates <= the resolved as-of (read verbatim from the immutable runs; nothing recomputed).
    `full=True` serves the full stored series through the latest run (the endpoint's `?full=true`)."""
    return _regime_history_series(session, asof, get_config(), full=full)


def get_indexes(
    session: Session,
    range_key: Optional[str] = None,
    asof: Optional[str] = None,
    full: bool = False,
) -> dict:
    """`GET /api/indexes` — the server-side normalized-% lines for the config-listed index ETFs over the
    selected `range_key` preset (rebased to the range start). `full=True` extends through the latest
    stored bar (display-only). Raises `UnknownRangeError` for an unknown preset (the endpoint's 422)."""
    return compute_index_series(session, as_of=asof, range_key=range_key, full=full)


def get_methodology() -> dict:
    """`GET /api/methodology` — the config-backed Setup & Pattern catalog (the single source for the
    methodology page + the /stocks badge tooltips + the setup-filter vocabulary). No DB/session needed;
    suppresses the `universe_selection` section until the committed screen record exists, as the endpoint
    does."""
    catalog = build_catalog(get_config())
    if not load_universe_screen_record(DEFAULT_SEED_DIR):
        catalog.pop("universe_selection", None)
    return catalog


def list_runs(session: Session) -> dict:
    """`GET /api/runs` — the immutable as-of scanner-run history (descending by date), each with its
    stored regime label/score, candidate counts, and stock count. Reads STORED rows only.

    NOTE: `/api/runs` keeps its read inline in the router (no engine function to delegate to), so this
    is the one tool that MIRRORS the router's stored-row read rather than calling a shared engine helper
    — it still recomputes nothing (a plain SELECT over the immutable snapshot rows)."""
    if latest_data_date(session) is None:
        raise ValueError("no price data available")
    run_rows = session.exec(select(ScannerRun).order_by(ScannerRun.asof_date.desc())).all()
    out = []
    for run in run_rows:
        n_stocks = session.scalar(
            select(func.count()).select_from(ScannerResult).where(ScannerResult.run_id == run.id)
        )
        out.append(
            {
                "run_id": run.id,
                "asof_date": run.asof_date.isoformat(),
                "created_at": run.created_at.isoformat(),
                "regime": {"label": run.regime_label, "score": run.regime_score},
                "candidate_counts": json.loads(run.candidate_counts_json),
                "n_stocks": int(n_stocks or 0),
            }
        )
    return {"runs": out}


def get_run(session: Session, run_id: int) -> dict:
    """`GET /api/runs/{run_id}` — one run's full STORED snapshot: its regime panel, universe-relative
    breadth, candidate counts, and the ranked stored stock rows (rehydrated from `record_json` into the
    canonical StockRow shape). Reads STORED rows only; raises ValueError for an unknown run_id.

    NOTE: like `list_runs`, this mirrors the router's inline stored-row read (no engine helper to reuse)."""
    if latest_data_date(session) is None:
        raise ValueError("no price data available")
    run = session.get(ScannerRun, run_id)
    if run is None:
        raise ValueError(f"unknown run: {run_id}")
    results = session.exec(
        select(ScannerResult).where(ScannerResult.run_id == run_id).order_by(ScannerResult.rank)
    ).all()
    rows = [json.loads(result.record_json) for result in results]
    return {
        "run_id": run.id,
        "asof_date": run.asof_date.isoformat(),
        "created_at": run.created_at.isoformat(),
        "provider": run.provider,
        "benchmark": run.benchmark,
        "regime": {
            "label": run.regime_label,
            "score": run.regime_score,
            "components": json.loads(run.regime_components_json),
            "asof_date": run.asof_date.isoformat(),
        },
        "breadth": {
            "above_50dma_pct": run.breadth_above_50dma,
            "above_200dma_pct": run.breadth_above_200dma,
            "new_high_low": json.loads(run.new_high_low_json),
            "label": "universe-relative",
        },
        "candidate_counts": json.loads(run.candidate_counts_json),
        "rows": rows,
    }
