"""The **referee** — the statistical-honesty core of Trendora's decision-quality loop.

It certifies whether a proposed *edge* (a cohort's forward-return advantage over a control) is REAL —
out-of-sample, control-beating, and multiple-testing-corrected — or rejects it. Only a certified edge
may ship; this stops the loop from building decision-support on overfit noise.

This module is **PURE**: it has NO database, NO I/O, and NO wall-clock (`date.today()`) dependency — it
operates on plain observation lists and a small immutable `RefereeState`, and it is fully DETERMINISTIC
given a `seed` (every bootstrap draw + every Thresholdout noise sample is drawn from one seeded
``numpy.random.default_rng(seed)``). It uses **numpy only** (no scipy): the one place a Gaussian tail is
needed uses the stdlib ``math.erfc``.

THE PROCEDURE (the exact statistical choices — documented so they can be audited)
================================================================================
Inputs: a `cohort` observation list ``[(asof_date, forward_return)]``, a `control` observation list
(benchmark / random-same-sector returns over the SAME dates), the forward-return `horizon` (trading
days), a `RefereeState` carrying cumulative `n_trials` (this claim's ordinal) + `alpha_budget_remaining`,
and a `seed`.

a. **Sealed temporal holdout split.** Sort by date; the in-sample half is the earlier ~70% of
   observations and the holdout the later ~30%, split on a WHOLE-DATE boundary (no single date ever
   straddles the seal — observations sharing a date are never split across it). See
   `DEFAULT_HOLDOUT_FRACTION`.

b. **Purge + embargo.** An in-sample observation at date ``d`` whose forward window
   ``[d, d + horizon trading days]`` reaches into the holdout would leak future information, so it is
   PURGED. We convert the horizon to calendar days with ``_CALENDAR_DAYS_PER_TRADING_DAY`` (≈ 252 trading
   days / 365 calendar days) and additionally drop an EMBARGO buffer of
   ``embargo_fraction × forward_window`` days before the holdout start. Concretely: keep an in-sample
   observation only when ``d <= holdout_start − (forward_window + embargo)``.

c. **Edge.** ``edge = mean(cohort forward return) − mean(control forward return)``, measured as the mean
   of the PER-DATE excess (each date contributes one value ``mean(cohort_d) − mean(control_d)``, so a
   day with many cohort names is not over-weighted), computed SEPARATELY on the (purged) in-sample and on
   the sealed holdout.

d. **Out-of-sample gate.** The HOLDOUT edge must be in the claimed `direction`, beat the control
   (``edge > 0`` in the claimed direction), and exceed `min_effect_size`. Failing the gate ⇒ FAIL.

e. **Significance.** A one-sided p-value for the holdout edge from a **circular moving-BLOCK bootstrap**
   of the per-date holdout excess series, with the block length inferred from the data's own cadence
   (``block ≈ horizon / median date-gap``, so overlapping/autocorrelated forward windows are respected;
   for a cadence coarser than the horizon the block collapses to 1 — non-overlapping, independent). The
   null (edge = 0) is imposed by recentering the series; ``p = (1 + #{edge* ≥ edge_obs}) / (B + 1)``.

f. **Multiple-testing deflation (Bonferroni).** The required significance is tightened by the cumulative
   trial count: ``required_p = alpha_per_test / max(1, n_trials)``. More claims tested ⇒ a harder bar ⇒
   data-mining is defeated. (Bonferroni chosen over Benjamini–Hochberg for a per-claim online test where
   the full family is not known in advance — it needs only the running count, never the other p-values.)

g. **Thresholdout-style budget charge.** The alpha budget is CHARGED only when the holdout edge DISAGREES
   with the in-sample edge beyond ``instability_tolerance`` plus a small SEEDED noise term (the Dwork et
   al. *reusable holdout* mechanic): a STABLE edge (holdout confirms in-sample) confirms cheaply
   (``alpha_charged = 0``); an OVERFIT one (holdout diverges) costs ``alpha_charge``. When the budget is
   already exhausted (``alpha_budget_remaining <= 0``) the referee REFUSES — verdict INSUFFICIENT — and
   likewise when an unstable edge cannot afford its charge.

Output: a `Verdict` (status ∈ {PASS, FAIL, INSUFFICIENT}, reason, and the stats the loop records:
``in_sample_edge``, ``holdout_edge``, ``control_excess``, ``p_value``, ``effective_n``,
``n_trials_at_test``, ``alpha_charged`` — plus a few additive auditability fields). PURE: it never
stamps a time — the caller records `register_date`.

HONESTY CAVEAT: ``effective_n`` is the number of SEALED HOLDOUT DATES — the genuinely independent units
of a forward-return test, NOT the raw observation count (many same-date names are one correlated unit).
On a coarse cadence (e.g. quarterly snapshots) the holdout has only a handful of dates, so the referee
will return INSUFFICIENT rather than certify on a sample too thin to be believed.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date as date_cls
from datetime import timedelta
from statistics import mean, median
from typing import Optional

import numpy as np

# ---- verdict statuses (a fixed structural vocabulary, not tunables) ------------------------------
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_INSUFFICIENT = "INSUFFICIENT"

# ---- documented statistical defaults (the referee's hyperparameters; every one is overridable) ---
# Calendar days per trading day: markets trade ~252 of 365 days, so a trading-day horizon spans this
# many calendar days. Used ONLY to convert the purge/embargo window from trading days to the calendar
# dates the observations actually carry (the module never sees a trading calendar).
_CALENDAR_DAYS_PER_TRADING_DAY = 365.0 / 252.0
_EPS = 1e-9

DEFAULT_HOLDOUT_FRACTION = 0.30      # later ~30% of observations form the sealed holdout
DEFAULT_EMBARGO_FRACTION = 0.5       # embargo buffer = half the forward window, added to the purge gap
DEFAULT_ALPHA_PER_TEST = 0.05        # the per-test significance level, BEFORE Bonferroni deflation
DEFAULT_N_BOOTSTRAP = 2000           # block-bootstrap resamples for the holdout-edge p-value
DEFAULT_MIN_EFFECT_SIZE = 0.0        # minimum holdout edge (in return units) to clear the OOS gate
DEFAULT_MIN_HOLDOUT_DATES = 5        # need >= this many SEALED holdout dates, else INSUFFICIENT
DEFAULT_MIN_INSAMPLE_DATES = 5       # need >= this many purged in-sample dates, else INSUFFICIENT
DEFAULT_INSTABILITY_TOLERANCE = 0.01     # |holdout − in_sample| above this (+ noise) is "unstable"
DEFAULT_THRESHOLDOUT_NOISE_SCALE = 0.005  # std of the seeded Thresholdout noise added to the tolerance
DEFAULT_ALPHA_CHARGE = 0.05          # budget cost charged for one unstable (overfit) claim
DEFAULT_ALPHA_BUDGET = 1.0           # the total alpha budget a fresh ledger starts with
DEFAULT_SEED = 20240601              # deterministic default seed (matches the engine control-group seed)
DEFAULT_DIRECTION = "positive"       # the claimed edge direction; "negative" flips the sign of the gate


@dataclass(frozen=True)
class RefereeState:
    """The cumulative testing state the referee deflates against. `n_trials` is THIS claim's ordinal
    (1 for the first claim ever tested, 2 for the second, …) — the Bonferroni divisor. `alpha_budget_
    remaining` is the Thresholdout budget left (the ledger's starting budget minus all prior charges)."""

    n_trials: int = 1
    alpha_budget_remaining: float = DEFAULT_ALPHA_BUDGET


@dataclass(frozen=True)
class Verdict:
    """The referee's certification of one claimed edge. PURE data — no timestamp (the caller stamps the
    register date). `status` is one of {PASS, FAIL, INSUFFICIENT}; the remaining fields are the audit
    trail the certified-claims ledger records."""

    status: str
    reason: str
    in_sample_edge: Optional[float] = None
    holdout_edge: Optional[float] = None
    control_excess: Optional[float] = None
    p_value: Optional[float] = None
    effective_n: int = 0
    n_trials_at_test: int = 0
    alpha_charged: float = 0.0
    # --- additive auditability fields (not part of the minimal contract, but recorded for honesty) ---
    required_p: Optional[float] = None
    deflation_divisor: int = 1
    in_sample_dates: int = 0
    holdout_dates: int = 0
    cohort_n: int = 0
    control_n: int = 0
    purged_in_sample: int = 0
    block_length: int = 0
    direction: str = DEFAULT_DIRECTION
    seed: int = DEFAULT_SEED
    deflation: str = "bonferroni"

    @property
    def certified(self) -> bool:
        return self.status == STATUS_PASS

    def to_dict(self) -> dict:
        """A JSON-serializable dict of the full verdict (for the ledger + the MCP tool response)."""
        return asdict(self)


# ==================================================================================================
# (a) + (b)  Sealed temporal holdout split with purge + embargo
# ==================================================================================================
@dataclass(frozen=True)
class Split:
    """The sealed temporal split. The in-sample lists are POST-purge; the holdout lists are every
    observation on a date at/after `holdout_start`. `purged_in_sample` is how many in-sample cohort
    observations the purge+embargo dropped (overlapping forward windows)."""

    in_sample_cohort: list = field(default_factory=list)
    holdout_cohort: list = field(default_factory=list)
    in_sample_control: list = field(default_factory=list)
    holdout_control: list = field(default_factory=list)
    split_date: Optional[date_cls] = None
    holdout_start: Optional[date_cls] = None
    forward_window_days: int = 0
    embargo_days: int = 0
    purged_in_sample: int = 0


def purge_embargo_split(
    cohort: list,
    control: list,
    horizon: int,
    holdout_fraction: float = DEFAULT_HOLDOUT_FRACTION,
    embargo_fraction: float = DEFAULT_EMBARGO_FRACTION,
) -> Optional[Split]:
    """Split `cohort` + `control` into a sealed temporal holdout (steps a + b). Returns None when the
    cohort spans fewer than 2 distinct dates (no split possible) or the split leaves no holdout date.

    The boundary is chosen on the cohort's distinct dates: accumulate observations from the earliest
    date until the in-sample share reaches ``1 − holdout_fraction``; that date is the last in-sample
    date (`split_date`) and the next is the holdout start. Whole dates are never split across the seal.
    Then PURGE: keep an in-sample observation only when its date is at or before
    ``holdout_start − (forward_window + embargo)`` calendar days, where ``forward_window`` is the horizon
    converted to calendar days and ``embargo = embargo_fraction × forward_window``."""
    if not cohort:
        return None
    cohort_dates = sorted({d for d, _ in cohort})
    if len(cohort_dates) < 2:
        return None

    counts = Counter(d for d, _ in cohort)
    total = len(cohort)
    target_in = (1.0 - holdout_fraction) * total
    cum = 0
    split_idx = 0
    for i, d in enumerate(cohort_dates):
        cum += counts[d]
        split_idx = i
        if cum >= target_in:
            break
    if split_idx >= len(cohort_dates) - 1:
        return None  # the in-sample share consumed every date — no holdout remains

    split_date = cohort_dates[split_idx]
    holdout_start = cohort_dates[split_idx + 1]

    forward_window_days = math.ceil(horizon * _CALENDAR_DAYS_PER_TRADING_DAY)
    embargo_days = math.ceil(forward_window_days * embargo_fraction)
    purge_cutoff = holdout_start - timedelta(days=forward_window_days + embargo_days)

    holdout_cohort = [(d, r) for d, r in cohort if d >= holdout_start]
    holdout_control = [(d, r) for d, r in control if d >= holdout_start]
    in_raw_cohort = [(d, r) for d, r in cohort if d <= split_date]
    in_raw_control = [(d, r) for d, r in control if d <= split_date]
    in_sample_cohort = [(d, r) for d, r in in_raw_cohort if d <= purge_cutoff]
    in_sample_control = [(d, r) for d, r in in_raw_control if d <= purge_cutoff]

    return Split(
        in_sample_cohort=in_sample_cohort,
        holdout_cohort=holdout_cohort,
        in_sample_control=in_sample_control,
        holdout_control=holdout_control,
        split_date=split_date,
        holdout_start=holdout_start,
        forward_window_days=forward_window_days,
        embargo_days=embargo_days,
        purged_in_sample=len(in_raw_cohort) - len(in_sample_cohort),
    )


# ==================================================================================================
# (c)  Per-date excess (the edge, date-weighted so a many-name date is one unit)
# ==================================================================================================
def _per_date_excess(cohort: list, control: list) -> dict:
    """``{date: mean(cohort_d) − mean(control_d)}`` over every date that has BOTH a cohort and a control
    observation, ordered ascending by date. A date present on only one side contributes nothing (it has
    no defined excess), so the series is a clean per-date paired difference."""
    c_by_date: dict = defaultdict(list)
    k_by_date: dict = defaultdict(list)
    for d, r in cohort:
        c_by_date[d].append(r)
    for d, r in control:
        k_by_date[d].append(r)
    out: dict = {}
    for d in sorted(c_by_date):
        if c_by_date[d] and k_by_date.get(d):
            out[d] = mean(c_by_date[d]) - mean(k_by_date[d])
    return out


# ==================================================================================================
# (e)  Block length inference + the circular moving-block bootstrap p-value
# ==================================================================================================
def _infer_block_length(dates_sorted: list, horizon: int) -> int:
    """Block length ≈ how many CONSECUTIVE dated observations have overlapping forward windows =
    ``round(horizon_calendar_days / median_date_gap)``. A daily cadence with a 20-day horizon ⇒ a long
    block (heavy overlap); a quarterly cadence with the same horizon ⇒ block 1 (non-overlapping,
    independent). At least 1."""
    if len(dates_sorted) < 2:
        return 1
    gaps = [(dates_sorted[i + 1] - dates_sorted[i]).days for i in range(len(dates_sorted) - 1)]
    median_gap = median(gaps)
    if median_gap <= 0:
        return 1
    horizon_cal = horizon * _CALENDAR_DAYS_PER_TRADING_DAY
    return max(1, int(round(horizon_cal / median_gap)))


def _block_bootstrap_pvalue(
    rng: np.random.Generator,
    series: list,
    observed_edge: float,
    block_length: int,
    n_bootstrap: int,
    direction: str,
) -> float:
    """One-sided p-value for `observed_edge` from a circular moving-block bootstrap of `series` (the
    per-date holdout excess). The null (edge = 0) is imposed by recentering the series to mean 0; each
    resample concatenates ``ceil(T / L)`` length-`L` circular blocks, truncated to length T, and its
    mean is a null edge. ``p = (1 + #{null edge ≥ observed}) / (B + 1)`` (claimed-direction tail), so p
    is bounded in ``[1/(B+1), 1]`` (never a spurious exact 0)."""
    x = np.asarray(series, dtype=float)
    T = x.size
    if T == 0:
        return 1.0
    sign = 1.0 if direction == DEFAULT_DIRECTION else -1.0
    directed_obs = sign * observed_edge
    x0 = (x - x.mean()) * sign  # recenter to the null AND orient to the claimed direction
    L = min(max(1, block_length), T)
    n_blocks = int(math.ceil(T / L))
    starts = rng.integers(0, T, size=(n_bootstrap, n_blocks))           # seeded — deterministic
    offsets = np.arange(L)
    idx = (starts[:, :, None] + offsets[None, None, :]) % T              # circular block indices
    samples = x0[idx].reshape(n_bootstrap, n_blocks * L)[:, :T]
    boot_edges = samples.mean(axis=1)
    count = int(np.count_nonzero(boot_edges >= directed_obs))
    return (1 + count) / (n_bootstrap + 1)


# ==================================================================================================
# The single certification entry point
# ==================================================================================================
def _verdict(status: str, reason: str, **stats) -> Verdict:
    return Verdict(status=status, reason=reason, **stats)


def certify_edge(
    cohort: list,
    control: list,
    *,
    horizon: int,
    state: RefereeState,
    seed: int = DEFAULT_SEED,
    holdout_fraction: float = DEFAULT_HOLDOUT_FRACTION,
    embargo_fraction: float = DEFAULT_EMBARGO_FRACTION,
    min_effect_size: float = DEFAULT_MIN_EFFECT_SIZE,
    alpha_per_test: float = DEFAULT_ALPHA_PER_TEST,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
    min_holdout_dates: int = DEFAULT_MIN_HOLDOUT_DATES,
    min_insample_dates: int = DEFAULT_MIN_INSAMPLE_DATES,
    instability_tolerance: float = DEFAULT_INSTABILITY_TOLERANCE,
    thresholdout_noise_scale: float = DEFAULT_THRESHOLDOUT_NOISE_SCALE,
    alpha_charge: float = DEFAULT_ALPHA_CHARGE,
    direction: str = DEFAULT_DIRECTION,
) -> Verdict:
    """Certify (PASS) or reject (FAIL) a claimed edge, or refuse (INSUFFICIENT) when the sealed sample is
    too thin or the alpha budget is exhausted. Runs steps a–g above. PURE + DETERMINISTIC given `seed`.

    `cohort` / `control` are ``[(asof_date: date, forward_return: float)]`` lists; `state` carries this
    claim's ordinal `n_trials` (the Bonferroni divisor) and the remaining alpha budget."""
    rng = np.random.default_rng(seed)
    n_trials = max(1, int(state.n_trials))
    divisor = n_trials
    required_p = alpha_per_test / divisor
    base = dict(
        n_trials_at_test=state.n_trials,
        deflation_divisor=divisor,
        required_p=required_p,
        direction=direction,
        seed=seed,
        cohort_n=len(cohort),
        control_n=len(control),
    )

    # (g, first half) Budget gate — refuse before doing anything if the budget is already spent.
    if state.alpha_budget_remaining <= _EPS:
        return _verdict(
            STATUS_INSUFFICIENT,
            "alpha budget exhausted — refusing to certify any further claim (data-mining guard)",
            alpha_charged=0.0, **base,
        )

    # Clean inputs: drop NA returns, coerce to (date, float).
    cohort = [(d, float(r)) for d, r in cohort if r is not None]
    control = [(d, float(r)) for d, r in control if r is not None]
    if not cohort or not control:
        return _verdict(
            STATUS_INSUFFICIENT, "no usable observations in the cohort or the control",
            alpha_charged=0.0, **base,
        )

    # (a) + (b) Sealed temporal holdout split with purge + embargo.
    split = purge_embargo_split(cohort, control, horizon, holdout_fraction, embargo_fraction)
    if split is None:
        return _verdict(
            STATUS_INSUFFICIENT,
            "cannot form a sealed temporal holdout (need observations on >= 2 distinct dates)",
            alpha_charged=0.0, **base,
        )
    base.update(
        block_length=_infer_block_length(sorted({d for d, _ in cohort}), horizon),
        purged_in_sample=split.purged_in_sample,
    )

    # (c) Per-date excess on each side of the seal.
    is_excess = _per_date_excess(split.in_sample_cohort, split.in_sample_control)
    ho_excess = _per_date_excess(split.holdout_cohort, split.holdout_control)
    in_sample_edge = mean(is_excess.values()) if is_excess else None
    holdout_edge = mean(ho_excess.values()) if ho_excess else None
    base.update(
        in_sample_dates=len(is_excess),
        holdout_dates=len(ho_excess),
        effective_n=len(ho_excess),
        in_sample_edge=in_sample_edge,
        holdout_edge=holdout_edge,
        control_excess=holdout_edge,  # the holdout cohort's mean excess OVER its control (the edge)
    )

    # Effective-sample gate — refuse on a sample too thin to be believed (the honesty caveat).
    if len(ho_excess) < min_holdout_dates or len(is_excess) < min_insample_dates:
        return _verdict(
            STATUS_INSUFFICIENT,
            (
                f"sealed sample too small to certify: in_sample_dates={len(is_excess)} "
                f"(need >= {min_insample_dates}), holdout_dates={len(ho_excess)} "
                f"(need >= {min_holdout_dates})"
            ),
            alpha_charged=0.0, **base,
        )

    # (g, second half) Thresholdout charge — a stable edge confirms cheaply; an overfit one costs budget.
    noise = abs(float(rng.normal(0.0, thresholdout_noise_scale)))  # seeded — deterministic
    disagreement = abs(holdout_edge - in_sample_edge)
    charged = alpha_charge if disagreement > (instability_tolerance + noise) else 0.0
    if charged > 0.0 and state.alpha_budget_remaining + _EPS < charged:
        return _verdict(
            STATUS_INSUFFICIENT,
            (
                "insufficient alpha budget to certify an unstable (in-sample/holdout-divergent) edge: "
                f"need {charged:.4g}, have {state.alpha_budget_remaining:.4g}"
            ),
            alpha_charged=0.0, **base,
        )

    # (e) Significance — block-bootstrap p-value of the holdout edge.
    p_value = _block_bootstrap_pvalue(
        rng, list(ho_excess.values()), holdout_edge, base["block_length"], n_bootstrap, direction
    )
    base["p_value"] = p_value

    # (d) Out-of-sample gate — direction, beats control, and minimum effect size.
    directed_edge = holdout_edge if direction == DEFAULT_DIRECTION else -holdout_edge
    if directed_edge <= 0:
        return _verdict(
            STATUS_FAIL,
            f"holdout edge {holdout_edge:+.4g} is not in the claimed {direction} direction / does not "
            "beat the control out-of-sample",
            alpha_charged=charged, **base,
        )
    if directed_edge < min_effect_size:
        return _verdict(
            STATUS_FAIL,
            f"holdout edge {holdout_edge:+.4g} is below the minimum effect size {min_effect_size:.4g}",
            alpha_charged=charged, **base,
        )

    # (f) Deflated significance — Bonferroni against the cumulative trial count.
    if p_value < required_p:
        return _verdict(
            STATUS_PASS,
            (
                f"certified: holdout edge {holdout_edge:+.4g} beats the control out-of-sample and is "
                f"significant after multiple-testing deflation (p={p_value:.4g} < alpha/{divisor}="
                f"{required_p:.4g})"
            ),
            alpha_charged=charged, **base,
        )
    return _verdict(
        STATUS_FAIL,
        (
            f"holdout edge {holdout_edge:+.4g} is not significant after multiple-testing deflation "
            f"(p={p_value:.4g} >= alpha/{divisor}={required_p:.4g})"
        ),
        alpha_charged=charged, **base,
    )
