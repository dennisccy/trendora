"""app.engine.concentration — the ONE canonical effective-number-of-bets / pairwise-correlation
helper (goal-mcp-loop iter-38, J-23 / backlog B-204).

PURE module: no database, no I/O, no wall-clock dependency — every function takes plain numeric
inputs and returns plain numeric outputs. This is the SINGLE implementation of both computations in
the codebase (Data Contract keystone; B-204's "share B-104's helper" trap): the watchlist
concentration X-ray (`app.engine.watchlist_xray`) is the first consumer; the future B-104 evidence
correlation audit imports these SAME two functions rather than writing a second ENB/correlation
implementation. Do NOT add a second `effective_number_of_bets` or `correlation_matrix` anywhere else
in the codebase.

`correlation_matrix(series_by_name)` computes the pairwise Pearson correlation over every pair of
named return series. Two series of different lengths are aligned on their TRAILING overlap (the last
`min(len_a, len_b)` observations of each) — the natural alignment for return series that are both
bounded trailing windows ending at the same as-of date (see `app.engine.prices.bars_asof_window`, the
composer's bar source). An undefined pair — fewer than 2 overlapping observations, or either series
has zero variance over the overlap — renders an honest `None`, never a fabricated 0.0 (anti-goal: No
fabricated data).

`effective_number_of_bets(corr_matrix)` computes the classic ENB statistic `(Σλ)² / Σλ²` over the
eigenvalues of a CLEAN, real-valued, symmetric correlation matrix (every cell defined — the caller is
responsible for building this "honest sub-matrix" by excluding any name whose row/column carries an
undefined pairwise correlation; see `watchlist_xray.build_xray_payload`). A fully independent set of N
names yields ENB == N (identity matrix); a fully redundant set (every pair correlation 1.0) yields
ENB == 1 (one effective bet) — "how many genuinely independent positions this set behaves like."
"""
from __future__ import annotations

from typing import Optional, Sequence

import numpy as np


def _pair_correlation(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    """Pearson correlation between two return series, aligned on their TRAILING overlap (the last
    `min(len(x), len(y))` observations of each — both series are trailing windows ending at the same
    as-of date, so this is a real date alignment, not an arbitrary truncation). `None` (honest NA) when
    the overlap is under 2 observations or either series has zero variance over it — a correlation is
    mathematically undefined in both cases, never fabricated as 0.0."""
    n = min(len(x), len(y))
    if n < 2:
        return None
    xs = np.asarray(x[-n:], dtype=float)
    ys = np.asarray(y[-n:], dtype=float)
    if xs.std() == 0.0 or ys.std() == 0.0:
        return None
    corr = float(np.corrcoef(xs, ys)[0, 1])
    return None if np.isnan(corr) else corr


def correlation_matrix(series_by_name: dict[str, Sequence[float]]) -> dict[str, dict[str, Optional[float]]]:
    """The full pairwise Pearson correlation matrix over `series_by_name` (name -> return series).
    Returns a nested dict keyed both ways (`matrix[a][b] == matrix[b][a]`), every name present as both
    a row and a column, including the self pair (diagonal). An undefined pair (see `_pair_correlation`)
    is `None` — always render this as NA, never as 0.0 or 1.0."""
    names = list(series_by_name)
    return {a: {b: _pair_correlation(series_by_name[a], series_by_name[b]) for b in names} for a in names}


def effective_number_of_bets(corr_matrix: Sequence[Sequence[float]]) -> Optional[float]:
    """`(Σλ)² / Σλ²` over the eigenvalues of a clean NxN correlation matrix (`numpy.linalg.eigvalsh` —
    the matrix is real-symmetric by construction). The caller passes the "honest sub-matrix": only
    names with a fully-defined pairwise correlation against every other included name (see
    `watchlist_xray.build_xray_payload`) — this function does NOT itself handle `None`/NA cells.

    N == 0 -> `None` (nothing to measure). N == 1 -> `1.0` (a single name is trivially "1 independent
    bet" — handled directly rather than through the general eigenvalue ratio)."""
    arr = np.asarray(corr_matrix, dtype=float)
    n = arr.shape[0]
    if n == 0:
        return None
    if n == 1:
        return 1.0
    eigenvalues = np.linalg.eigvalsh(arr)
    sum_lambda = float(eigenvalues.sum())
    sum_lambda_sq = float(np.square(eigenvalues).sum())
    if sum_lambda_sq == 0.0:
        return None
    return (sum_lambda**2) / sum_lambda_sq
