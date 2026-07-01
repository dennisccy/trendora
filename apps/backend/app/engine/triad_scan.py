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

import os
from datetime import date as date_cls
from statistics import mean, pstdev
from typing import Optional

from sqlmodel import select

from app.config import get_config
from app.engine.forward_testing import benchmark_symbols
from app.engine.research import compute_factor_lab, factor_catalog
from app.engine.samples import KIND_COMBINATION, KIND_FACTOR, compute_samples
from app.engine.triad_screen import screen_holdout
from app.models import ForwardReturn, ScannerRun

# Module defaults (overridable via an optional `config.triad` block).
DEFAULT_WEIGHTS = {"return": 1.0, "drawdown": 1.0, "frequency": 0.5}
DEFAULT_TOP_K = 20
DEFAULT_SCREEN = {"base_edge_floor": 0.0, "haircut_coef": 0.001}

# goal-mcp-loop iter-10 — the deterministic register date stamped on every staging exploration verdict.
# The referee is PURE (it never reads register_date), so a FIXED date makes a re-run byte-identical; it is
# only the ledger entry's `register_date` metadata. Overridable via `explore_multi_horizon_staging`'s param.
DEFAULT_STAGING_REGISTER_DATE = "2026-07-01"


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
    (frequency/turnover proxy), and the factor's ``rank_ic``. Low-sample / NA cells are skipped.

    Horizons: an explicit ``horizons=`` wins; otherwise the CONFIGURED aperture ``config.triad.horizons``
    (goal-mcp-loop iter-10, e.g. ``[1,5,10,20,60]``) is used, falling back to
    ``[walk_forward.default_horizon]`` only when the triad block declares none — so the multi-horizon
    aperture is honored whether the caller enters here directly or via ``scan_product_triad``."""
    wf = cfg.walk_forward
    fl = cfg.research.factor_lab
    if horizons is None:
        _, _, _, cfg_horizons = _triad_cfg(cfg)
        horizons = cfg_horizons or [wf.default_horizon]
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


# ==================================================================================================
# goal-mcp-loop iter-10 (Part B Phase 1) — the multi-horizon STAGING exploration.
#
# The ONLY writer-adjacent function in this module: it runs a FIXED, PRE-REGISTERED candidate set of
# multi-horizon single-factor hypotheses through the REFEREE (the full `verify_edge`, NOT the cheap
# `screen_holdout` above) into the INTERNAL **staging** ledger under the online-FDR (LORD++) economy. It
# NEVER touches the user-facing canonical `certified-claims.jsonl`: `verify_edge` stays the sole ledger
# writer and is called ONLY with `ledger="staging"`, and this function REFUSES to point at the canonical
# ledger path (a fail-closed guard). The discovered block-bootstrap p-values are what iter-11 reads to
# PROMOTE a winner (`p_value < 0.010`, the canonical divisor-5 bar) to canonical and surface J-07.
#
# Anti-data-mining keystone: the candidate set is PRE-REGISTERED in `config.triad.candidates` (mirrored
# into `project-extensions/proposer-guidance.md`, each with an economic rationale). The exploration
# iterates ONLY that fixed set — NEVER the full `factor × horizon × decile` cross-product.
# ==================================================================================================
def _staging_candidates(cfg) -> list[dict]:
    """The FIXED, PRE-REGISTERED multi-horizon candidate set from ``config.triad.candidates`` — each entry
    projected into a factor-decile claim dict mirroring ``/api/research/samples`` selectors
    (``{kind, factor, slice_kind, decile, horizon, direction}``). Returns ``[]`` when the block is absent
    (nothing to explore). Reads config VERBATIM — no cohort/horizon literal lives here (the anti-data-mining
    keystone: the hypothesis set is pre-registered in config, never enumerated in code)."""
    block = getattr(cfg, "triad", None)
    if not isinstance(block, dict):
        return []
    raw = block.get("candidates")
    if not raw:
        return []
    claims: list[dict] = []
    for c in raw:
        claims.append({
            "kind": KIND_FACTOR,
            "factor": str(c["factor"]),
            "slice_kind": "decile",
            "decile": int(c["decile"]),
            "horizon": int(c["horizon"]),
            "direction": str(c.get("direction", "positive")),
        })
    return claims


def explore_multi_horizon_staging(
    session,
    config=None,
    *,
    ledger_path: Optional[str] = None,
    register_date: str = DEFAULT_STAGING_REGISTER_DATE,
    reset: bool = False,
) -> dict:
    """Run the PRE-REGISTERED multi-horizon candidate set (``config.triad.candidates``) through the referee
    into the INTERNAL **staging** ledger, appending one verdict per candidate via
    ``app.mcp.tools:verify_edge(ledger="staging")`` under the online-FDR economy (when
    ``evidence.fdr.enabled``). Returns the per-candidate results (claim + verdict) so the caller can persist
    / report the discovered block-bootstrap p-values.

    Determinism: PURE given the DB + config + a fixed ``register_date`` and a fresh/``reset`` ledger — the
    referee is deterministic (seed = ``walk_forward.control_group.seed``), so a re-run yields byte-identical
    verdicts. ``reset=True`` truncates the target staging ledger first so a regeneration is idempotent (the
    fixed-candidate exploration is a clean re-derivation, not an online accumulator).

    Fences (honesty guards):
      * ``verify_edge`` is called ONLY with ``ledger="staging"`` — the canonical Bonferroni bar is never
        touched, and ``verify_edge`` remains the SOLE ledger writer;
      * this function REFUSES to operate on the canonical ledger path (``evidence.ledger_path``) — a
        ``ValueError`` fail-closed guard so a mis-wired call can never write/clear the user-facing ledger.
    """
    from app.mcp.tools import LEDGER_STAGING, verify_edge  # lazy import — breaks the tools<-triad_scan cycle

    cfg = config or get_config()
    # Resolve BOTH the target and the canonical path through the same repo-root convention (a relative path
    # -> repo root, an absolute path unchanged) so the fail-closed guard below compares like-for-like — a
    # relative canonical path passed verbatim is caught exactly as an absolute one is.
    ledger_path = _resolve_repo_path(ledger_path) if ledger_path else _resolve_repo_path(cfg.evidence.staging_ledger_path)

    # Fail-closed: NEVER let the staging exploration touch the user-facing canonical ledger.
    canonical = _resolve_repo_path(cfg.evidence.ledger_path)
    if os.path.abspath(ledger_path) == os.path.abspath(canonical):
        raise ValueError(
            "explore_multi_horizon_staging refuses to write the CANONICAL ledger "
            f"({ledger_path!r}); the staging exploration is fenced to the staging ledger only"
        )

    if reset and os.path.exists(ledger_path):
        os.remove(ledger_path)  # clean re-derivation of the fixed candidate set (staging file ONLY)

    candidates = _staging_candidates(cfg)
    results: list[dict] = []
    for claim in candidates:
        out = verify_edge(
            session, claim, ledger_path, register_date=register_date, ledger=LEDGER_STAGING
        )
        results.append(out)
    return {
        "ledger_path": ledger_path,
        "ledger": LEDGER_STAGING,
        "register_date": register_date,
        "n_candidates": len(candidates),
        "results": results,
    }


# ==================================================================================================
# goal-mcp-loop iter-12 (Part B Phase 1 — the deferred COMBINATIONS half) — the 2-factor COMBINATION
# STAGING exploration. The exact sibling of the single-factor `explore_multi_horizon_staging` above, but
# for pre-registered 2-factor COMPOSITE cohorts (`config.triad.combination_candidates`). It projects each
# registered pair into a `kind:"combination"` composite-cohort claim and certifies it through the SAME
# referee path (`verify_edge(ledger="staging")`) into the INTERNAL staging ledger under the online-FDR
# economy — the recorded block-bootstrap p-values are what iter-13 reads to PROMOTE a winner (raw
# `p_value < 0.00833`, the canonical divisor-6 bar) to canonical and surface J-08.
#
# The referee cert path is REUSED UNCHANGED: `assemble_claim_observations`->`drill_samples` already parse
# the `condition` legs and resolve the `composite` cohort (`condition`/`cohort` are in
# `_CLAIM_SELECTOR_KEYS`), so NOTHING in `verify_edge` is modified — it stays the SOLE ledger writer.
#
# DELIBERATELY a parallel sibling (NOT a shared refactor of `explore_multi_horizon_staging`): the
# single-factor exploration writes the byte-FROZEN committed staging entries #1-4, so it is left untouched
# so those bytes never move (the iter-9/iter-10 "protect the frozen artifact" lesson). The small guard/loop
# overlap is the deliberate cost of that isolation.
#
# Anti-data-mining keystone: the candidate set is PRE-REGISTERED in `config.triad.combination_candidates`
# (mirrored into `project-extensions/proposer-guidance.md` §4.2, each with an economic rationale), iterated
# VERBATIM — NEVER the full `factor × pair × horizon` cross-product.
# ==================================================================================================
def _combination_staging_candidates(cfg) -> list[dict]:
    """The FIXED, PRE-REGISTERED 2-factor combination candidate set from
    ``config.triad.combination_candidates`` — each entry projected into a combination COMPOSITE-cohort claim
    dict mirroring ``/api/research/samples`` selectors
    (``{kind:"combination", cohort:"composite", condition:[leg1, leg2], horizon, direction}``). Returns
    ``[]`` when the block is absent (nothing to explore). Reads config VERBATIM — no leg/horizon literal
    lives here; ``kind`` + ``cohort`` are the only structural constants (every registered combination is a
    composite cohort, exactly as ``_staging_candidates`` fixes ``slice_kind="decile"``). The anti-data-mining
    keystone: the hypothesis set is pre-registered in config, never enumerated in code."""
    block = getattr(cfg, "triad", None)
    if not isinstance(block, dict):
        return []
    raw = block.get("combination_candidates")
    if not raw:
        return []
    claims: list[dict] = []
    for c in raw:
        claims.append({
            "kind": KIND_COMBINATION,
            "cohort": "composite",
            "condition": [str(leg) for leg in c["condition"]],
            "horizon": int(c["horizon"]),
            "direction": str(c.get("direction", "positive")),
        })
    return claims


def explore_combination_staging(
    session,
    config=None,
    *,
    ledger_path: Optional[str] = None,
    register_date: str = DEFAULT_STAGING_REGISTER_DATE,
    reset: bool = False,
) -> dict:
    """Run the PRE-REGISTERED 2-factor combination candidate set (``config.triad.combination_candidates``)
    through the referee into the INTERNAL **staging** ledger, appending one verdict per candidate via
    ``app.mcp.tools:verify_edge(ledger="staging")`` under the online-FDR economy (when
    ``evidence.fdr.enabled``). Returns the per-candidate results (claim + verdict) so the caller can persist
    / report the discovered block-bootstrap p-values — the basis iter-13 PROMOTES a J-08 winner from.

    The exact sibling of ``explore_multi_horizon_staging`` — same determinism, same fences, same (unchanged)
    referee path — but for combination composite cohorts. Determinism: PURE given the DB + config + a fixed
    ``register_date`` and a fresh/``reset`` ledger (the referee seed is fixed), so a re-run yields
    byte-identical verdicts. ``reset=True`` truncates the target staging ledger first (a clean re-derivation
    of the fixed candidate set, staging file ONLY — NOT an online accumulator).

    Fences (honesty guards):
      * ``verify_edge`` is called ONLY with ``ledger="staging"`` — the canonical Bonferroni bar is never
        touched, and ``verify_edge`` remains the SOLE ledger writer;
      * this function REFUSES to operate on the canonical ledger path (``evidence.ledger_path``) — a
        ``ValueError`` fail-closed guard so a mis-wired call can never write/clear the user-facing ledger.
    """
    from app.mcp.tools import LEDGER_STAGING, verify_edge  # lazy import — breaks the tools<-triad_scan cycle

    cfg = config or get_config()
    # Resolve BOTH the target and the canonical path through the repo-root convention so the fail-closed
    # guard compares like-for-like (a relative canonical path passed verbatim is caught exactly as an
    # absolute one is) — identical to the single-factor explorer.
    ledger_path = _resolve_repo_path(ledger_path) if ledger_path else _resolve_repo_path(cfg.evidence.staging_ledger_path)

    # Fail-closed: NEVER let the combination staging exploration touch the user-facing canonical ledger.
    canonical = _resolve_repo_path(cfg.evidence.ledger_path)
    if os.path.abspath(ledger_path) == os.path.abspath(canonical):
        raise ValueError(
            "explore_combination_staging refuses to write the CANONICAL ledger "
            f"({ledger_path!r}); the staging exploration is fenced to the staging ledger only"
        )

    if reset and os.path.exists(ledger_path):
        os.remove(ledger_path)  # clean re-derivation of the fixed candidate set (staging file ONLY)

    candidates = _combination_staging_candidates(cfg)
    results: list[dict] = []
    for claim in candidates:
        out = verify_edge(
            session, claim, ledger_path, register_date=register_date, ledger=LEDGER_STAGING
        )
        results.append(out)
    return {
        "ledger_path": ledger_path,
        "ledger": LEDGER_STAGING,
        "register_date": register_date,
        "n_candidates": len(candidates),
        "results": results,
    }


def _resolve_repo_path(path: str) -> str:
    """Resolve a config ledger path against the repo root when relative (mirrors the evidence resolver's
    repo-root convention), so a relative ``evidence.*ledger_path`` points at the committed session-state
    file regardless of the caller's cwd. An absolute path is returned unchanged."""
    if os.path.isabs(path):
        return path
    # app/engine/triad_scan.py -> repo root is four parents up (repo/apps/backend/app/engine/…).
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    return os.path.join(repo_root, path)
