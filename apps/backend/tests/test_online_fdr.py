"""PURE online-FDR (LORD++) unit tests (goal-mcp-loop iter-9).

`app.engine.online_fdr` is the injectable, DEFAULT-OFF *staging* deflation policy. These tests pin the
three contracts iter-9 depends on:
  * PURITY + DETERMINISM — no RNG, no I/O; the SAME (trial, rejection-history, tunables) always yields the
    SAME `test_level` (so it can never perturb the canonical Bonferroni bar it is fenced away from);
  * CORRECTNESS of the LORD++ allocation — the exact `test_level` is asserted on a known rejection sequence,
    the ζ normalizer matches the true Riemann zeta, and the wealth REPLENISHES (more rejections ⇒ a looser
    bar at the same trial — the whole point of the economy);
  * VALIDATION — every tunable is bounds-checked (a summable spending sequence needs `exponent > 1`, etc.),
    never a silent bad value.

Every number here is a FROZEN constant produced by the module itself, so an algorithm drift is caught (the
values are independently reproducible from the documented formula ``α_t = W₀γ_t + (α−W₀)γ_{t−τ₁} + αΣγ_{t−τⱼ}``).
"""
from __future__ import annotations

import pytest

from app.engine import online_fdr

# The canonical LORD++ tunables (mirror config.yaml `evidence.fdr`).
_KW = dict(alpha=0.05, w0_fraction=0.5, gamma_exponent=1.6, gamma_terms=1000)

# The true Riemann zeta ζ(1.6) = Σ_{k>=1} k^-1.6, to which the Euler–Maclaurin normalizer converges.
_ZETA_1_6 = 2.285765665680135


# ==================================================================================================
# The ζ normalizer converges to the true Riemann zeta (Σ γ_j = 1) — accurately even at few explicit terms.
# ==================================================================================================
def test_gamma_normalizer_matches_riemann_zeta():
    # accurate to ~machine precision because the Euler–Maclaurin tail absorbs the infinite remainder:
    # the estimate is stable across wildly different explicit-term counts.
    assert online_fdr._gamma_normalizer(1.6, 1000) == pytest.approx(_ZETA_1_6, abs=1e-12)
    assert online_fdr._gamma_normalizer(1.6, 100) == pytest.approx(_ZETA_1_6, abs=1e-9)
    # a different exponent gives a different, still-summable normalizer (ζ(2) = π²/6 ≈ 1.6449).
    assert online_fdr._gamma_normalizer(2.0, 2000) == pytest.approx(1.6449340668, abs=1e-8)


def test_gamma_weights_are_a_normalized_spending_sequence():
    norm = online_fdr._gamma_normalizer(1.6, 1000)
    # γ_j = j^-p / ζ(p): positive, strictly decreasing, and 0 for a non-positive lag.
    g1 = online_fdr._gamma(1, 1.6, norm)
    g2 = online_fdr._gamma(2, 1.6, norm)
    assert g1 > g2 > 0
    assert online_fdr._gamma(0, 1.6, norm) == 0.0
    assert online_fdr._gamma(-3, 1.6, norm) == 0.0
    assert g1 == pytest.approx(1.0 / norm, abs=1e-15)  # γ_1 = 1/ζ(p)


# ==================================================================================================
# PURE + DETERMINISTIC — the same inputs always yield the same level (no RNG, no I/O, no hidden state).
# ==================================================================================================
def test_test_level_is_deterministic():
    a = online_fdr.test_level(5, [1, 2, 4], **_KW)
    b = online_fdr.test_level(5, [1, 2, 4], **_KW)
    assert a == b  # byte-identical repeat — proves determinism / no RNG


def test_test_level_exact_frozen_values():
    # FROZEN: independently reproducible from the LORD++ formula; a drift in the algorithm is caught here.
    # t=1, no prior rejections: α_1 = W₀·γ_1 = (0.5·0.05)/ζ(1.6).
    assert online_fdr.test_level(1, [], **_KW) == pytest.approx(0.010937254144361815, abs=1e-15)
    # t=5 with the canonical rejection ordinals [1,2,4]: wealth replenished by three prior discoveries.
    assert online_fdr.test_level(5, [1, 2, 4], **_KW) == pytest.approx(0.027669279357088947, abs=1e-15)


def test_rejections_replenish_wealth_loosening_the_bar():
    """The economy's raison d'être: a trial that follows discoveries is judged at a LOOSER level than the
    same trial with no prior discoveries (Bonferroni could only ever tighten)."""
    no_rejections = online_fdr.test_level(5, [], **_KW)
    with_rejections = online_fdr.test_level(5, [1, 2, 4], **_KW)
    assert with_rejections > no_rejections
    # and each level stays a valid significance in (0, alpha] — never exceeds the target FDR level.
    assert 0.0 < no_rejections < with_rejections <= _KW["alpha"]


def test_future_and_present_rejection_offsets_are_ignored():
    """Only rejections STRICTLY BEFORE trial t contribute — so passing the whole PASS-ordinal history is
    safe (offsets >= t or < 1 are filtered), and the allocation for t depends only on its own past."""
    base = online_fdr.test_level(5, [1, 2, 4], **_KW)
    assert online_fdr.test_level(5, [1, 2, 4, 5, 9, 0, -2], **_KW) == base
    assert online_fdr.test_level(5, [4, 2, 1], **_KW) == base  # order-independent


# ==================================================================================================
# VALIDATION — every tunable is bounds-checked (never a silent bad value).
# ==================================================================================================
def test_invalid_tunables_raise():
    with pytest.raises(ValueError, match="t must be >= 1"):
        online_fdr.test_level(0, [], **_KW)
    with pytest.raises(ValueError, match="alpha must be in"):
        online_fdr.test_level(1, [], alpha=1.5, w0_fraction=0.5, gamma_exponent=1.6, gamma_terms=1000)
    with pytest.raises(ValueError, match="w0_fraction must be in"):
        online_fdr.test_level(1, [], alpha=0.05, w0_fraction=1.5, gamma_exponent=1.6, gamma_terms=1000)
    with pytest.raises(ValueError, match="summable"):
        online_fdr._gamma_normalizer(1.0, 1000)
    with pytest.raises(ValueError, match="gamma_terms must be >= 1"):
        online_fdr._gamma_normalizer(1.6, 0)
