"""Deterministic triad scan over the factor cross-over space (the analyst loop's quantitative core).

The user's analyst habit: look across factors / deciles / regimes / horizons for a cohort that
*regularly* delivers **higher return, lower max-drawdown, and higher frequency (turnover)** — the
"triad". This module is the deterministic, reuse-only scan that surfaces those cohorts so the
``goal-proposer`` agent (which also surveys the rest of the product via the read tools) can turn the
survivors into enhancement proposals.

SINGLE SOURCE OF TRUTH — recomputes nothing. Every triad metric is read VERBATIM from the canonical
``app.engine.research.compute_factor_lab`` (the same numbers the ``/research`` Factor-Lab UI shows):
per (factor, horizon, decile) it already publishes ``mean_return``, the paired ``mean_max_drawdown``
(the stored J-86/J-109 column), ``n``, and the factor's Spearman ``rank_ic`` + by-regime split. The
scan just normalises those into a triad score and ranks the cells.

Then the top cells are run through the cheap out-of-sample ``triad_screen.screen_holdout`` — so only
cohorts whose return edge PERSISTS out-of-sample become proposal candidates. The screen NEVER writes
the certified-claims ledger (these are hypotheses-to-build, not "Proven" badges).

Config-driven (no magic numbers) via an OPTIONAL ``config.triad`` block; sensible module defaults are
used when it is absent, so the scan is robust regardless of config wiring.
"""
from __future__ import annotations

from datetime import date as date_cls
from statistics import mean, pstdev
from typing import Optional

from sqlmodel import select

from app.config import get_config
from app.engine.forward_testing import benchmark_symbols
from app.engine.research import compute_factor_lab, factor_catalog
from app.engine.samples import KIND_FACTOR, compute_samples
from app.engine.triad_screen import screen_holdout
from app.models import ForwardReturn, ScannerRun

# Module defaults (overridable via an optional `config.triad` block).
DEFAULT_WEIGHTS = {"return": 1.0, "drawdown": 1.0, "frequency": 0.5}
DEFAULT_TOP_K = 20
DEFAULT_SCREEN = {"base_edge_floor": 0.0, "haircut_coef": 0.001}


# --------------------------------------------------------------------------------------------------
# Config access — tolerant of an absent `triad` block (falls back to module defaults).
# --------------------------------------------------------------------------------------------------
def _triad_cfg(cfg):
    """Return ``(weights, top_k, screen, horizons)`` from the optional ``config.triad`` block, else
    module defaults. ``cfg.triad`` arrives as a plain dict (the Config model has ``extra="allow"``, so a
    scaffolded YAML section rides along untyped). Tolerant of an absent or partial block."""
    block = getattr(cfg, "triad", None)
    weights = dict(DEFAULT_WEIGHTS)
    top_k = DEFAULT_TOP_K
    screen = dict(DEFAULT_SCREEN)
    horizons: Optional[list[int]] = None
    if isinstance(block, dict):
        w = block.get("weights")
        if isinstance(w, dict):
            weights = {
                "return": float(w.get("return", weights["return"])),
                "drawdown": float(w.get("drawdown", weights["drawdown"])),
                "frequency": float(w.get("frequency", weights["frequency"])),
            }
        if block.get("top_k") is not None:
            top_k = int(block["top_k"])
        s = block.get("screen")
        if isinstance(s, dict):
            screen = {
                "base_edge_floor": float(s.get("base_edge_floor", screen["base_edge_floor"])),
                "haircut_coef": float(s.get("haircut_coef", screen["haircut_coef"])),
            }
        hz = block.get("horizons")
        if hz:
            horizons = [int(h) for h in hz]
    return weights, top_k, screen, horizons


def _zscores(values: list[float]) -> list[float]:
    """Population z-scores; all-zero when the spread is degenerate (deterministic, no NaN)."""
    if not values:
        return []
    mu = mean(values)
    sd = pstdev(values)
    if sd == 0:
        return [0.0 for _ in values]
    return [(v - mu) / sd for v in values]


# --------------------------------------------------------------------------------------------------
# Cell enumeration — read VERBATIM from compute_factor_lab (the canonical Factor-Lab read).
# --------------------------------------------------------------------------------------------------
def scan_factor_decile_cells(
    session, cfg, *, horizons: Optional[list[int]] = None,
    deciles_of_interest: Optional[list[int]] = None, as_of: Optional[date_cls] = None,
) -> list[dict]:
    """One cell per ``(factor, horizon, decile)`` (the extreme deciles by default) carrying the triad
    metrics read verbatim from ``compute_factor_lab``: ``mean_return``, ``mean_max_drawdown``, ``n``
    (frequency/turnover proxy), and the factor's ``rank_ic``. Low-sample / NA cells are skipped."""
    wf = cfg.walk_forward
    fl = cfg.research.factor_lab
    horizons = horizons or [wf.default_horizon]
    deciles_of_interest = deciles_of_interest or sorted({1, fl.deciles})  # bottom + top decile
    cells: list[dict] = []
    for f in factor_catalog(cfg):
        for h in horizons:
            lab = compute_factor_lab(session, f["key"], h, cfg, as_of=as_of)
            rank_ic = (lab.get("rank_ic") or {}).get("value")
            for dr in lab["deciles"]:
                if dr["decile"] not in deciles_of_interest:
                    continue
                if dr.get("low_sample") or dr.get("mean_return") is None:
                    continue
                cells.append({
                    "factor": f["key"],
                    "horizon": h,
                    "decile": dr["decile"],
                    "mean_return": dr["mean_return"],
                    "mean_max_drawdown": dr.get("mean_max_drawdown"),
                    "n": dr["n"],
                    "rank_ic": rank_ic,
                    # the claim-able selector that reproduces this exact cohort (for the screen + proposals)
                    "selector": {
                        "kind": KIND_FACTOR, "factor": f["key"],
                        "slice_kind": "decile", "decile": dr["decile"], "horizon": h,
                    },
                })
    return cells


def score_cells(cells: list[dict], weights: dict) -> list[dict]:
    """Attach a ``triad_score`` = ``w_ret·z(return) + w_dd·z(drawdown) + w_freq·z(frequency)`` and return
    the cells ranked best-first. ``mean_max_drawdown ≤ 0`` so a SHALLOWER drawdown is a LARGER value →
    ``z(drawdown)`` already rewards low drawdown without a sign flip. Deterministic tie-break."""
    if not cells:
        return []
    zr = _zscores([c["mean_return"] for c in cells])
    zd = _zscores([(c["mean_max_drawdown"] if c["mean_max_drawdown"] is not None else 0.0) for c in cells])
    zn = _zscores([float(c["n"]) for c in cells])
    for c, a, b, e in zip(cells, zr, zd, zn):
        c["triad_score"] = (
            weights["return"] * a + weights["drawdown"] * b + weights["frequency"] * e
        )
    return sorted(cells, key=lambda c: (-c["triad_score"], c["factor"], c["horizon"], c["decile"]))


# --------------------------------------------------------------------------------------------------
# Observation assembly for the hold-out screen — mirrors mcp.tools assembly but stays in the engine
# layer (no mcp import → no circular dependency). Reads stored values only; recomputes nothing.
# --------------------------------------------------------------------------------------------------
def _spy_control_observations(session, cfg, horizon: int, cohort_dates: set) -> list[tuple]:
    """SPY's stored realized forward returns at ``horizon``, one per as-of date, restricted to the
    cohort's dates (the same-dates control). Mirrors ``mcp.tools._benchmark_control_observations``."""
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


def _assemble_cell_observations(session, cfg, selector: dict) -> tuple[list, list]:
    """``(cohort_obs, control_obs)`` for a cell, reusing ``compute_samples`` (the exact published cohort
    membership) + the same-dates SPY control. Both are ``[(date, forward_return)]`` for the screen."""
    samples = compute_samples(
        session, kind=selector["kind"], horizon=selector["horizon"], config=cfg,
        factor_key=selector.get("factor"), slice_kind=selector.get("slice_kind"),
        decile=selector.get("decile"),
    )
    cohort = [
        (date_cls.fromisoformat(r["snapshot_date"]), r["forward_return"])
        for r in samples["rows"]
        if r.get("snapshot_date") and r.get("forward_return") is not None
    ]
    cohort_dates = {d for d, _ in cohort}
    control = _spy_control_observations(session, cfg, selector["horizon"], cohort_dates)
    return cohort, control


# --------------------------------------------------------------------------------------------------
# The public scan: rank cells by the triad, screen the top K out-of-sample, return survivors.
# --------------------------------------------------------------------------------------------------
def scan_product_triad(
    session, config=None, *, horizons: Optional[list[int]] = None,
    top_k: Optional[int] = None, as_of: Optional[date_cls] = None,
) -> dict:
    """Scan the factor cross-over space, rank by the triad, hold-out-screen the top ``top_k`` cells, and
    return the screened table + the survivors (cohorts whose return edge persisted out-of-sample).

    Deterministic given the DB + config. READ-ONLY: never writes the certified-claims ledger and never
    spends the certification alpha budget — the screen is an ephemeral honesty filter for proposals.
    """
    cfg = config or get_config()
    weights, cfg_top_k, screen_params, cfg_horizons = _triad_cfg(cfg)
    horizons = horizons or cfg_horizons or [cfg.walk_forward.default_horizon]
    top_k = top_k if top_k is not None else cfg_top_k

    ranked = score_cells(scan_factor_decile_cells(session, cfg, horizons=horizons, as_of=as_of), weights)
    batch_size = len(ranked)  # the multiple-testing context for the screen haircut

    screened: list[dict] = []
    for cell in ranked[:top_k]:
        cohort_obs, control_obs = _assemble_cell_observations(session, cfg, cell["selector"])
        result = screen_holdout(
            cohort_obs, control_obs, cell["horizon"], batch_size=batch_size,
            base_edge_floor=screen_params["base_edge_floor"], haircut_coef=screen_params["haircut_coef"],
        )
        screened.append({**cell, "screen": result, "oos_survived": result["survived"]})

    survivors = [c for c in screened if c["oos_survived"]]
    return {
        "as_of": as_of.isoformat() if as_of is not None else None,
        "horizons": list(horizons),
        "weights": weights,
        "n_cells": len(ranked),
        "n_screened": min(top_k, len(ranked)),
        "n_survivors": len(survivors),
        "batch_size": batch_size,
        "cells": screened,        # the top-K, each annotated with its screen result, ranked best-first
        "survivors": survivors,   # the subset whose edge persisted out-of-sample (proposal candidates)
    }
