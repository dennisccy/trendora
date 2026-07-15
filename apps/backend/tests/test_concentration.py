"""app.engine.concentration — the ONE ENB / pairwise-correlation helper (iter-38, J-23 / B-204).

Pure math, DB-free — every expected value below is hand-derived so the test asserts an exact number
(anti-pattern: "something returned"). The B-204 fixture (two perfectly correlated synthetic return
series + one independent series -> ENB close to the intuitive "2 independent things") is the headline
sanity check the phase spec names explicitly.
"""
from __future__ import annotations

import numpy as np
import pytest

from app.engine.concentration import correlation_matrix, effective_number_of_bets


# --- correlation_matrix -----------------------------------------------------------------------
def test_correlation_matrix_perfect_positive():
    series = {"A": [1.0, 2.0, 3.0, 4.0, 5.0], "B": [2.0, 4.0, 6.0, 8.0, 10.0]}
    matrix = correlation_matrix(series)
    assert matrix["A"]["B"] == pytest.approx(1.0)
    assert matrix["B"]["A"] == pytest.approx(1.0)
    assert matrix["A"]["A"] == pytest.approx(1.0)
    assert matrix["B"]["B"] == pytest.approx(1.0)


def test_correlation_matrix_perfect_negative():
    series = {"A": [1.0, 2.0, 3.0, 4.0, 5.0], "B": [10.0, 8.0, 6.0, 4.0, 2.0]}
    matrix = correlation_matrix(series)
    assert matrix["A"]["B"] == pytest.approx(-1.0)
    assert matrix["B"]["A"] == pytest.approx(-1.0)


def test_correlation_matrix_zero_variance_is_honest_none_never_fabricated():
    series = {"A": [1.0, 2.0, 3.0], "FLAT": [5.0, 5.0, 5.0]}
    matrix = correlation_matrix(series)
    assert matrix["A"]["FLAT"] is None
    assert matrix["FLAT"]["A"] is None
    assert matrix["FLAT"]["FLAT"] is None  # self-correlation of a constant series is also undefined


def test_correlation_matrix_too_short_is_honest_none():
    series = {"A": [1.0], "B": [2.0]}
    matrix = correlation_matrix(series)
    assert matrix["A"]["B"] is None
    assert matrix["B"]["A"] is None


def test_correlation_matrix_empty_series_is_honest_none():
    series = {"A": [], "B": [1.0, 2.0, 3.0]}
    matrix = correlation_matrix(series)
    assert matrix["A"]["B"] is None


def test_correlation_matrix_aligns_on_trailing_overlap():
    # B (3 points, perfectly increasing) is aligned against A's LAST 3 points, which are ALSO
    # perfectly increasing — but A's FIRST 3 points are deliberately decreasing "noise" that must be
    # ignored by trailing-overlap alignment, or the correlation would come out negative instead of +1.
    a = [9.0, 5.0, 1.0, 10.0, 20.0, 30.0]  # last 3: [10, 20, 30] (increasing); first 3: decreasing
    b = [1.0, 2.0, 3.0]                     # increasing — matches a's LAST 3, not its first 3
    matrix = correlation_matrix({"A": a, "B": b})
    assert matrix["A"]["B"] == pytest.approx(1.0)


def test_correlation_matrix_single_name_self_pair_only():
    matrix = correlation_matrix({"A": [1.0, 2.0, 3.0]})
    assert matrix == {"A": {"A": pytest.approx(1.0)}}


# --- effective_number_of_bets -----------------------------------------------------------------
def test_enb_identity_matrix_equals_n_exactly():
    # N fully independent names: identity correlation matrix -> ENB == N exactly.
    identity = np.eye(4).tolist()
    assert effective_number_of_bets(identity) == pytest.approx(4.0)


def test_enb_all_ones_matrix_equals_one_exactly():
    # N fully redundant (perfectly correlated) names -> ENB == 1 exactly (one effective bet).
    ones = [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]
    assert effective_number_of_bets(ones) == pytest.approx(1.0)


def test_enb_two_names_zero_correlation_equals_two_exactly():
    matrix = [[1.0, 0.0], [0.0, 1.0]]
    assert effective_number_of_bets(matrix) == pytest.approx(2.0)


def test_enb_hand_derived_two_correlated_plus_one_independent():
    # matrix [[1,1,0],[1,1,0],[0,0,1]]: hand-derived eigenvalues {2, 0, 1} -> (Sum(lambda))^2 / Sum(lambda^2)
    # = 3^2 / (4+0+1) = 9/5 = 1.8 exactly — the B-204 fixture's exact target for an IDEALIZED
    # (correlation exactly 1.0 / exactly 0.0) two-correlated-plus-one-independent construction.
    matrix = [[1.0, 1.0, 0.0], [1.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    assert effective_number_of_bets(matrix) == pytest.approx(1.8)


def test_enb_single_name_is_one():
    assert effective_number_of_bets([[1.0]]) == 1.0


def test_enb_empty_is_none():
    assert effective_number_of_bets([]) is None


# --- B-204 fixture: full pipeline from synthetic RETURN series through both functions -----------
def test_b204_fixture_two_correlated_one_independent_series():
    """The phase-spec-named B-204 sanity check: two PERFECTLY correlated synthetic return series (B is
    an exact positive scalar multiple of A, so their Pearson correlation is exactly 1.0) plus one
    INDEPENDENT series (a fresh random draw) -> ENB close to the intuitive "2 independent things" (one
    correlated pair behaving as one bet, plus one independent name) — matching the hand-derived exact
    1.8 for the idealized {corr=1, corr=0} case (see test_enb_hand_derived_two_correlated_plus_one_independent)
    within a wide, justified tolerance for the real (not exactly 0) sample correlation of two
    independent 200-point draws (standard error ~1/sqrt(200) ~ 0.07, so the loose |corr| < 0.25 bound
    below is a >3-sigma margin — deterministically seeded, never flaky)."""
    rng = np.random.default_rng(20240601)  # the project's committed determinism seed
    base = rng.normal(0, 1, size=200).tolist()
    correlated_a = base
    correlated_b = [3.0 * v for v in base]  # a positive scalar multiple -> correlation exactly 1.0
    independent = rng.normal(0, 1, size=200).tolist()  # a fresh, unrelated draw

    matrix = correlation_matrix({"A": correlated_a, "B": correlated_b, "C": independent})
    assert matrix["A"]["B"] == pytest.approx(1.0, abs=1e-9)
    assert abs(matrix["A"]["C"]) < 0.25
    assert abs(matrix["B"]["C"]) < 0.25

    names = ["A", "B", "C"]
    enb_matrix = [[matrix[r][c] for c in names] for r in names]
    enb = effective_number_of_bets(enb_matrix)
    assert 1.5 < enb < 2.2  # close to the hand-derived idealized 1.8, never near 1 (fully redundant) or 3 (independent)
