"""Lightweight out-of-sample hold-out screen for auto-mined triad patterns (the analyst loop).

This is the cheap honesty filter that sits between the deterministic triad scan
(:mod:`app.engine.triad_scan`) and a pattern becoming an enhancement PROPOSAL. An agent that
ranks thousands of cross-over cells by an in-sample triad (return / drawdown / frequency) will
surface flukes; this screen re-tests each candidate's return EDGE on a sealed temporal hold-out
and applies a batch multiple-testing haircut, so only patterns whose advantage PERSISTS
out-of-sample become proposals.

It is deliberately SEPARATE from the certification referee (:mod:`app.engine.referee`):
  * it REUSES the referee's exact sealed split (``purge_embargo_split``) and per-date excess
    (``_per_date_excess``) so the edge definition matches certification, BUT
  * it NEVER writes the certified-claims ledger and NEVER spends the scarce ~100-cert alpha
    budget — these are hypotheses-to-BUILD, not user-facing "Proven" badges. A built pattern that
    later warrants a badge still goes through the full referee separately.

Pure + deterministic: same observations + params ⇒ same verdict. No DB, no RNG, no I/O. The
"haircut" is a heuristic effect-size floor that tightens with the number of cells scanned together
(``base_edge_floor + haircut_coef · ln(batch_size)``) — a cheap proposal filter, NOT a formal FDR
(that remains the referee's job for badges).
"""
from __future__ import annotations

import math
from statistics import mean

from app.engine.referee import (
    DEFAULT_EMBARGO_FRACTION,
    DEFAULT_HOLDOUT_FRACTION,
    _per_date_excess,
    purge_embargo_split,
)

# Screen defaults (overridable via config ``triad.screen.*``). Conservative + cheap.
DEFAULT_MIN_HOLDOUT_DATES = 5
DEFAULT_MIN_INSAMPLE_DATES = 5
DEFAULT_BASE_EDGE_FLOOR = 0.0     # the holdout per-date excess must clear this (before the haircut)
DEFAULT_HAIRCUT_COEF = 0.0        # extra floor added per ln(batch_size) — the multiple-testing haircut


def required_holdout_edge(batch_size: int, base_edge_floor: float, haircut_coef: float) -> float:
    """The per-date holdout excess a candidate must clear to survive: a base floor plus a haircut that
    grows with the number of cells scanned together (``ln(batch_size)``). With ``haircut_coef = 0`` the
    bar is just ``base_edge_floor`` (the default = a positive edge must merely persist)."""
    return base_edge_floor + haircut_coef * math.log(max(1, int(batch_size)))


def screen_holdout(
    cohort_obs: list,
    control_obs: list,
    horizon: int,
    *,
    batch_size: int = 1,
    holdout_fraction: float = DEFAULT_HOLDOUT_FRACTION,
    embargo_fraction: float = DEFAULT_EMBARGO_FRACTION,
    min_holdout_dates: int = DEFAULT_MIN_HOLDOUT_DATES,
    min_insample_dates: int = DEFAULT_MIN_INSAMPLE_DATES,
    base_edge_floor: float = DEFAULT_BASE_EDGE_FLOOR,
    haircut_coef: float = DEFAULT_HAIRCUT_COEF,
) -> dict:
    """Screen ONE candidate cell's ``(cohort, control)`` observations for out-of-sample edge survival.

    ``cohort_obs`` / ``control_obs`` are ``[(date, forward_return)]`` — the same shape the referee
    consumes. ``batch_size`` is how many cells were scanned together this round (the multiple-testing
    context that sets the haircut). The candidate SURVIVES when the in-sample per-date excess edge is
    positive AND the sealed-holdout per-date excess edge clears the (batch-haircut) floor — i.e. the
    return advantage vs the SPY control PERSISTS out-of-sample. Returns ``survived`` plus diagnostics.

    Never writes the ledger; never spends alpha budget.
    """
    required = required_holdout_edge(batch_size, base_edge_floor, haircut_coef)
    base = {
        "survived": False,
        "in_sample_dates": 0,
        "holdout_dates": 0,
        "in_sample_edge": None,
        "holdout_edge": None,
        "required_holdout_edge": required,
        "batch_size": int(batch_size),
    }

    split = purge_embargo_split(cohort_obs, control_obs, horizon, holdout_fraction, embargo_fraction)
    if split is None:
        return {**base, "reason": "no-split"}

    in_excess = _per_date_excess(split.in_sample_cohort, split.in_sample_control)
    ho_excess = _per_date_excess(split.holdout_cohort, split.holdout_control)
    in_dates, ho_dates = len(in_excess), len(ho_excess)
    in_edge = mean(in_excess.values()) if in_excess else None
    ho_edge = mean(ho_excess.values()) if ho_excess else None

    if ho_dates < min_holdout_dates or in_dates < min_insample_dates:
        return {
            **base, "reason": "insufficient-dates",
            "in_sample_dates": in_dates, "holdout_dates": ho_dates,
            "in_sample_edge": in_edge, "holdout_edge": ho_edge,
        }

    survived = (in_edge is not None and in_edge > 0) and (ho_edge is not None and ho_edge >= required and ho_edge > 0)
    return {
        "survived": bool(survived),
        "reason": "edge-persisted" if survived else "edge-did-not-persist",
        "in_sample_dates": in_dates,
        "holdout_dates": ho_dates,
        "in_sample_edge": in_edge,
        "holdout_edge": ho_edge,
        "required_holdout_edge": required,
        "batch_size": int(batch_size),
    }
