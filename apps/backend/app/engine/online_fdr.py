"""PURE online-FDR (**LORD++**) deflation policy — the *staging* trial economy's significance allocator.

This module answers ONE question, deterministically and with NO state, RNG or I/O: **what significance
level `α_t` should trial `t` be judged at**, given the ordinals of the trials that were rejected
(certified) before it? It is the injectable, DEFAULT-OFF alternative to the referee's strict-Bonferroni
divisor, and it runs ONLY in the internal *staging* ledger (goal-mcp-loop iter-9, engineering direction
Part A). The user-facing canonical `/evidence` bar is ALWAYS Bonferroni and never consults this module.

WHY AN ONLINE-FDR ECONOMY
=========================
Bonferroni deflation (`required_p = alpha_per_test / n_trials`) tightens PERMANENTLY with every probe —
pass or fail — so a wide, sustained search eventually cannot certify anything (a single global counter
that only ever grows). LORD++ (Ramdas et al. 2017, "Online control of the FDR with decaying memory";
the "++" refinement of Javanmard & Montanari's LORD) instead controls the false-discovery *RATE* with a
replenishing **alpha-wealth**: each REJECTION (a certified discovery) earns back testing capacity, so an
economy that keeps finding real edges keeps affording new tests. It is weaker than family-wise control —
which is EXACTLY why it is fenced to staging and never touches the canonical "Proven" badge.

THE LORD++ RULE (the exact allocation — documented so it can be audited)
=======================================================================
For trial `t` (1-based) with prior rejection ordinals ``τ₁ < τ₂ < … < t``::

    α_t = W₀·γ_t  +  (α − W₀)·γ_{t−τ₁}  +  α·Σ_{j≥2} γ_{t−τⱼ}

where

  * ``α`` is the target FDR level (config ``fdr.alpha``);
  * ``W₀ = w0_fraction·α`` is the initial alpha-wealth, ``0 ≤ W₀ ≤ α`` (config ``fdr.w0_fraction``);
  * ``τ₁, τ₂, …`` are the ordinals of the trials REJECTED before `t` (the "rejection offsets"); the
    wealth is RECONSTRUCTED purely from these times — no running budget is stored (zero migration);
  * ``γ`` is a non-negative **spending sequence** summing to 1, here the normalized polynomial
    ``γ_j = j^{-p} / ζ(p)`` for ``j ≥ 1`` (``γ_j = 0`` for ``j ≤ 0``), decay exponent ``p > 1`` from
    config (``fdr.gamma_exponent``), normalized by the Riemann zeta ``ζ(p)`` (computed deterministically,
    see ``_gamma_normalizer``). Only the (α − W₀) weight on the FIRST rejection distinguishes LORD++
    from plain LORD.

PURITY: every tunable is injected (no magic number lives here); there is no database, no clock, no RNG.
Same inputs ⇒ same output, so the whole policy is trivially unit-testable and determinism-preserving —
the same discipline the referee (`app.engine.referee`) already holds.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Sequence


@lru_cache(maxsize=64)
def _gamma_normalizer(exponent: float, n_terms: int) -> float:
    """``ζ(exponent) = Σ_{k≥1} k^{-exponent}`` — the spending sequence's normalizer, so ``Σ_j γ_j = 1``.

    Computed DETERMINISTICALLY as an explicit ``n_terms`` partial sum plus an Euler–Maclaurin tail
    correction for the infinite remainder (accurate to ~machine precision for ``n_terms`` in the hundreds,
    ``exponent > 1``). Pure — ``exponent`` + ``n_terms`` are config, no magic number. Cached because the
    same (exponent, n_terms) recurs across trials, and the function is a deterministic map.

    Tail (with ``f(x)=x^{-s}``, ``N=n_terms``):
    ``Σ_{k>N} f(k) ≈ ∫_N^∞ f dx − ½f(N) + (s/12)N^{-s-1} = N^{1-s}/(s-1) − ½N^{-s} + (s/12)N^{-s-1}``."""
    if exponent <= 1.0:
        raise ValueError(f"gamma_exponent must be > 1 for a summable spending sequence, got {exponent}")
    if n_terms < 1:
        raise ValueError(f"gamma_terms must be >= 1, got {n_terms}")
    s = float(exponent)
    partial = 0.0
    for k in range(1, n_terms + 1):
        partial += k ** (-s)
    n = float(n_terms)
    tail = n ** (1.0 - s) / (s - 1.0) - 0.5 * n ** (-s) + (s / 12.0) * n ** (-(s + 1.0))
    return partial + tail


def _gamma(j: int, exponent: float, normalizer: float) -> float:
    """The spending-sequence weight ``γ_j = j^{-exponent} / ζ(exponent)`` for ``j ≥ 1``; ``0`` for
    ``j ≤ 0`` (a lag into the future/present contributes nothing to the allocation)."""
    if j < 1:
        return 0.0
    return (j ** (-float(exponent))) / normalizer


def test_level(
    t: int,
    rejection_offsets: Sequence[int],
    *,
    alpha: float,
    w0_fraction: float,
    gamma_exponent: float,
    gamma_terms: int,
) -> float:
    """The LORD++ significance level ``α_t`` for trial `t` (1-based) given the prior rejection ordinals.

    ``α_t = W₀·γ_t + (α − W₀)·γ_{t−τ₁} + α·Σ_{j≥2} γ_{t−τⱼ}`` (see the module docstring). `rejection_offsets`
    are the ordinals of trials rejected BEFORE `t`; any entry ``>= t`` (or ``< 1``) is ignored, so passing
    the whole PASS-ordinal history is safe. Deterministic + pure: no RNG, no I/O, wealth reconstructed
    entirely from the rejection times. Every tunable is supplied by the caller (from ``config.evidence.fdr``)."""
    if t < 1:
        raise ValueError(f"trial ordinal t must be >= 1, got {t}")
    if not (0.0 < alpha < 1.0):
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    if not (0.0 <= w0_fraction <= 1.0):
        raise ValueError(f"w0_fraction must be in [0, 1], got {w0_fraction}")
    w0 = w0_fraction * alpha
    normalizer = _gamma_normalizer(float(gamma_exponent), int(gamma_terms))

    def g(j: int) -> float:
        return _gamma(j, gamma_exponent, normalizer)

    taus = sorted(int(x) for x in rejection_offsets if 1 <= int(x) < t)
    level = w0 * g(t)
    if taus:
        level += (alpha - w0) * g(t - taus[0])            # LORD++ weight on the FIRST rejection
        for tau in taus[1:]:
            level += alpha * g(t - tau)                    # full-α weight on every later rejection
    return level
