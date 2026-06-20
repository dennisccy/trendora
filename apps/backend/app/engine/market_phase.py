"""Market Phase & drawdown-Severity derivation (iter-29 goal mode, J-87 + J-88).

A NEW read-only, STRICTLY CAUSAL layer that, for a resolved as-of date D, describes WHERE IN THE CYCLE
the market is — a discrete **phase** (Expansion / Pullback / Correction / Bear / Recovery), a 0-100
**severity** score with its **named component breakdown**, and a deterministic forward **FILTERED**
P(state=bear | observations <= D). It alters NO canonical stock score, bucket, setup, pattern, regime
score, or the Risk-Off->Actionable gate; it adds NO snapshot column and triggers NO rebuild.

Anti-goals enforced here:
  - **Strictly causal (<= D).** Every input used for date D is dated <= D: the benchmark's trailing peak
    is `max(close)` over the lookback window via `bars_asof` (date <= D); time-underwater counts only
    bars <= D; regime/breadth read VERBATIM from the stored `ScannerRun` rows dated <= D; the ^VIX gate
    reads the ^VIX close on/before D. The FILTERED probability is a forward recursion over ONLY
    observations dated <= D — the SMOOTHED (full-sample) probability is NEVER computed/served here (it is
    reserved for the later J-89 retrospective surface).
  - **No recompute of canonical values.** The regime score/label and the universe breadth-below-200DMA
    are read VERBATIM from the stored immutable `ScannerRun` rows (the SAME rows `regime_history` reads) —
    there is NO call into `app.engine.regime`; regime is never recomputed. No stock score/bucket/setup/
    pattern is touched.
  - **No magic numbers.** Every phase edge, severity weight, drawdown/VIX threshold, transition-matrix
    entry, and emission parameter comes from `config.market_phase` / `config.regime_switching` — this
    module carries NO threshold literal (it is in `test_no_magic_numbers`'s `CALC_FILES`). The only
    numbers are structural (0/1/2 indexing/arithmetic, 100 the percent unit).
  - **No fabricated data.** A window with insufficient benchmark history (< `min_history_bars` bars <= D)
    returns an explicit NA / partial — never a synthesized phase / severity / probability.
  - **Determinism.** Fixed config params + the stored bars/runs yield a byte-identical severity and a
    byte-identical filtered P(bear). The filter is a closed-form Hamilton recursion over committed config
    params — it is NEVER EM-fit at serve time.

The cached serving layer (`app.api.market_phase`) keys this derivation by the resolved as-of + the SAME
`dataset_version` stamp J-72 uses (single-sourced), so a read serves the stored aggregate and refreshes
after any dataset change — never a stale figure.
"""
from __future__ import annotations

import json
from datetime import date as date_cls, datetime, timedelta, timezone
from math import exp
from typing import Optional

from sqlmodel import Session, select

from app.config import (
    Config,
    MARKET_PHASE_WEIGHT_KEYS,
    REGIME_SWITCHING_STATES,
    get_config,
)
from app.engine.labels import label_for
from app.engine.prices import bar_cache, bars_asof, closes
from app.engine.research import _dataset_version  # single-sourced cache stamp (J-72) — never duplicated
from app.models import MacroSeries, MarketPhaseCache, ScannerRun

# The Recovery phase label (a STATE override applied after the severity->phase edge lookup): a still-
# underwater tape that has rebounded >= `recovery_min_off_trough_pct` off its trough reads Recovery
# rather than the deep edge band. A fixed structural label (it is one of the configured phase labels);
# the threshold that triggers it is config (`market_phase.recovery_min_off_trough_pct`).
PHASE_RECOVERY = "Recovery"

# iter-30 (J-89) — the two "deep" phase labels a CAUSAL downtrend episode groups on (Bear / Correction).
# Fixed structural labels (each is one of the configured `market_phase.labels`), referenced by name the
# SAME way `PHASE_RECOVERY` is — NOT a numeric tunable (the numbers that DEFINE these bands live in the
# config `phase_edges`; these constants only name the labels the edge lookup produces).
_PHASE_BEAR = "Bear"
_PHASE_CORRECTION = "Correction"

# The two regime-switching states, in a FIXED order (the filter's state vector index order). Read from
# the config-level vocabulary so there is no hard-coded state string in the recursion.
_BEAR, _RISK_ON = REGIME_SWITCHING_STATES


def _drawdown_components(closes_window: list[float], cfg: Config) -> dict:
    """The benchmark drawdown leg of the severity reading, over the causal lookback window `closes_window`
    (ascending closes with date <= D). Returns the trailing-peak peak-to-trough drawdown (negative %),
    the scaled `drawdown_depth` component in [0, 1] (full at `drawdown_full_severity_pct`), the
    `time_underwater` component in [0, 1] (fraction of bars below the running high-water mark), and the
    `off_trough_pct` rebound (% the last close sits above the post-peak trough). Pure arithmetic over the
    passed bars; recomputes nothing else."""
    mp = cfg.market_phase
    peak = max(closes_window)
    last = closes_window[-1]
    # peak-to-trough drawdown of the LAST close vs the trailing window peak (<= 0; 0 at a fresh high).
    drawdown_pct = (last / peak - 1) * 100 if peak > 0 else 0
    drawdown_depth = min(1, abs(drawdown_pct) / mp.drawdown_full_severity_pct)

    # time-underwater: fraction of bars below the RUNNING high-water mark (a steady uptrend resets the
    # mark each new high -> few underwater; a sustained decline stays underwater). Causal by construction.
    hwm = closes_window[0]
    underwater = 0
    for close in closes_window:
        if close >= hwm:
            hwm = close
        else:
            underwater += 1
    time_underwater = underwater / len(closes_window)

    # off-trough rebound: how far the last close has rebounded above the LOWEST close AFTER the window
    # peak (the recovery leg). 0 when the last close IS the post-peak low (no rebound yet).
    peak_index = closes_window.index(peak)
    post_peak = closes_window[peak_index:]
    trough = min(post_peak)
    off_trough_pct = (last / trough - 1) * 100 if trough > 0 else 0

    return {
        "drawdown_pct": drawdown_pct,
        "drawdown_depth": drawdown_depth,
        "time_underwater": time_underwater,
        "off_trough_pct": off_trough_pct,
    }


def _latest_vix_on_or_before(session: Session, d: date_cls, cfg: Config) -> Optional[float]:
    """The ^VIX close on/before D (date <= D, no lookahead), or None when no ^VIX bar exists. Reads the
    configured volatility symbol (`etfs.volatility[0]`, the SAME symbol the regime engine's VIX gate
    reads) via `bars_asof` — a pure causal read; recomputes nothing."""
    symbols = cfg.etfs.volatility
    if not symbols:
        return None
    series = closes(bars_asof(session, symbols[0], d))
    return series[-1] if series else None


def _macro_value_asof(session: Session, series_id: str, d: date_cls) -> Optional[float]:
    """The latest stored macro value for `series_id` whose `published_date <= D` (the publication-lag
    causal gate, J-92), read VERBATIM, or None when no such row exists. Using a value whose
    `published_date > D` would be forbidden lookahead — this filter forbids it by construction (a value
    is only usable once it was actually published on/before D). A pure causal read; recomputes nothing,
    never fabricates a value (a walled/uncommitted series simply has no rows -> None)."""
    rows = session.exec(
        select(MacroSeries)
        .where(MacroSeries.symbol == series_id, MacroSeries.published_date <= d)
        .order_by(MacroSeries.date)
    ).all()
    return rows[-1].value if rows else None


def _macro_severity_legs(session: Session, d: date_cls, cfg: Config) -> dict[str, dict]:
    """The OPTIONAL macro severity legs for date D (J-92 — consumed ONLY when `cfg.macro.enable.severity`).
    For each configured series carrying a positive `weight` + a `stress_gate`, read the publication-lag-
    causal macro value (<= D) and scale it to a [0, 1] stress reading `min(1, abs(value) / stress_gate)`
    (the SAME clamp shape the ^VIX gate uses). Returns `{component_name: {"value": [0,1]|None, "weight":
    w}}` — a series with no published value <= D contributes `value=None` (excluded from the blend like a
    missing ^VIX, never fabricated). Returns `{}` when the severity leg is DISABLED, so the disabled path
    adds NO component and is byte-identical to the price/breadth/VIX-only severity (the byte-identity
    keystone). No magic number — every gate/weight is config."""
    if not cfg.macro.enable.severity:
        return {}
    legs: dict[str, dict] = {}
    for series in cfg.macro.series:
        if series.weight <= 0 or series.stress_gate is None:
            continue  # a series with no severity-leg scaling configured contributes nothing
        value = _macro_value_asof(session, series.id, d)
        scaled = min(1, abs(value) / series.stress_gate) if value is not None and series.stress_gate else None
        legs[f"macro_{series.id}"] = {"value": scaled, "weight": series.weight}
    return legs


def _severity_reading(
    session: Session, run: ScannerRun, cfg: Config
) -> Optional[dict]:
    """The single causal [0, 1] stress reading + its named component breakdown for ONE stored run (its
    `asof_date` is the causal cutoff). Blends the five config-weighted named components — benchmark
    drawdown depth, time-underwater, the STORED regime score inverted to risk, the universe breadth-below-
    200DMA (1 - the stored breadth), and the ^VIX gate — each in [0, 1], read causally (<= the run's
    date) and the regime/breadth read VERBATIM from the stored run (never recomputed).

    Returns `None` when the benchmark window has insufficient history (< `min_history_bars` bars <= D) —
    an honest NA, never a fabricated reading. An individual component that is NA (e.g. ^VIX missing, or
    breadth NULL on a short-history run) is EXCLUDED from the weighted blend (its weight drops out of the
    denominator, mirroring the regime engine's available-weight renormalization) — never fabricated.

    The returned `reading` (a [0, 1] float) is BOTH the severity fraction at this date AND the filter's
    observation at this date (J-88 shares J-87's inputs); `components` is the disclosed per-component
    breakdown (value + weight + contribution); `drawdown_pct` / `off_trough_pct` describe the cycle leg."""
    mp = cfg.market_phase
    bench = cfg.etfs.index[0]  # the benchmark (SPY) — the SAME first index ETF the RS benchmark uses
    d = run.asof_date

    start = d - timedelta(days=mp.lookback_days)
    window = [bar for bar in bars_asof(session, bench, d) if bar.date >= start]
    if len(window) < mp.min_history_bars:
        return None  # insufficient benchmark history -> NA / partial (never fabricated)
    closes_window = closes(window)

    dd = _drawdown_components(closes_window, cfg)

    # the STORED regime score inverted to a [0, 1] risk reading (read VERBATIM; regime is never recomputed).
    regime_risk = (100 - run.regime_score) / 100
    # the universe breadth BELOW the 200-DMA = 1 - the stored breadth fraction (read VERBATIM); NA when
    # the stored breadth is NULL (a short-history run) — excluded from the blend, never fabricated.
    breadth_below = (1 - run.breadth_above_200dma / 100) if run.breadth_above_200dma is not None else None
    # the ^VIX stress gate: the causal ^VIX close relative to the config gate (full at the gate, scales
    # below). NA when no ^VIX bar exists -> excluded from the blend (never fabricated).
    vix_close = _latest_vix_on_or_before(session, d, cfg)
    vix_gate = min(1, vix_close / mp.vix_gate) if vix_close is not None and vix_close > 0 else None

    raw = {
        "drawdown_depth": dd["drawdown_depth"],
        "time_underwater": dd["time_underwater"],
        "regime_risk": regime_risk,
        "breadth_below_200dma": breadth_below,
        "vix_gate": vix_gate,
    }
    # iter-32 (J-92): the OPTIONAL macro severity legs (config-default-OFF — `_macro_severity_legs` returns
    # `{}` when disabled, so every line below is byte-identical to the price/breadth/VIX-only path). When
    # enabled, each leg adds a [0,1] macro stress reading at its config weight, folded into the SAME
    # available-weight renormalization (a NA macro leg drops out of the denominator like a missing ^VIX).
    macro_legs = _macro_severity_legs(session, d, cfg)
    weights = dict(mp.weights)
    for name, leg in macro_legs.items():
        raw[name] = leg["value"]
        weights[name] = leg["weight"]
    available = {name: value for name, value in raw.items() if value is not None}
    available_weight = sum(weights[name] for name in available)
    reading = (
        sum(value * weights[name] for name, value in available.items()) / available_weight
        if available_weight
        else 0
    )

    # the disclosed per-component breakdown (explainable — never a bare number). Iterate the canonical
    # weight-key set so every configured component appears (even when NA), in a stable order; then append
    # any enabled macro legs (J-92) after the canonical components so the disabled path is byte-identical.
    component_names = sorted(MARKET_PHASE_WEIGHT_KEYS) + sorted(macro_legs)
    components = []
    for name in component_names:
        value = raw[name]
        weight = weights[name]
        if value is None:
            components.append({
                "name": name, "value": None, "weight": weight,
                "contribution": None, "available": False,
            })
        else:
            contribution = (value * weight / available_weight) * 100 if available_weight else 0
            components.append({
                "name": name, "value": round(value, 4), "weight": weight,
                "contribution": round(contribution, 2), "available": True,
            })
    # surface the ^VIX raw close beside its scaled component so the panel can render "VIX 31.4" honestly.
    vix_disclosure = {
        "name": "vix_level",
        "value": round(vix_close, 2) if vix_close is not None else None,
        "threshold": mp.vix_gate,
        "available": vix_close is not None,
    }

    # iter-32 (J-88/J-92): the FILTER observation for date D. By default it IS the severity reading (J-88
    # shares J-87's inputs). When the macro regime-switching leg is ENABLED, blend the publication-lag-
    # causal macro stress into the observation (config-default-OFF: `_regime_switching_observation` returns
    # the reading UNCHANGED when disabled, so the filter input — and thus every J-87..J-91 figure — is
    # byte-identical to the price/breadth/VIX-only path).
    observation = _regime_switching_observation(reading, session, d, cfg)

    return {
        "reading": reading,
        "observation": observation,
        "components": components,
        "vix_level": vix_disclosure,
        "drawdown_pct": round(dd["drawdown_pct"], 2),
        "off_trough_pct": round(dd["off_trough_pct"], 2),
    }


def _regime_switching_observation(
    reading: float, session: Session, d: date_cls, cfg: Config
) -> float:
    """The J-88 filter observation for date D (J-92 optional macro leg). By default returns the severity
    `reading` UNCHANGED (config-default-OFF — so the closed-form Hamilton filter ingests the SAME [0,1]
    stress reading it always has, and every J-87..J-91 figure stays byte-identical). When
    `cfg.macro.enable.regime_switching`, blend the publication-lag-causal macro stress legs into the
    observation by the SAME available-weight scheme `_severity_reading` uses: the observation becomes the
    weighted average of the severity reading (the structural base, weight 1) and each enabled macro leg's
    [0,1] reading at its config weight (a NA macro leg drops out — never fabricated). No magic number — the
    only structural constant is the integer base weight 1 on the severity reading itself (like the rest of
    the engine's structural 0/1/2)."""
    if not cfg.macro.enable.regime_switching:
        return reading  # DISABLED -> byte-identical (the filter ingests the unchanged severity reading)
    # when the severity leg is already enabled the macro stress is ALREADY in `reading`; the regime leg
    # then adds NO further adjustment (avoids double-counting the macro stress) — the reading is the blend.
    if cfg.macro.enable.severity:
        return reading
    # otherwise the regime-switching leg can be enabled independently: blend the configured macro legs into
    # the observation. A leg's value may be None (no causal value <= D) -> excluded, never fabricated.
    legs = _macro_severity_legs(session, d, cfg)
    base_weight = 1  # structural integer base weight on the severity reading (No magic numbers)
    available = {"_severity": (reading, base_weight)}
    for name, leg in legs.items():
        if leg["value"] is not None:
            available[name] = (leg["value"], leg["weight"])
    total_weight = sum(w for _v, w in available.values())
    if not total_weight:
        return reading
    return sum(v * w for v, w in available.values()) / total_weight


def _phase_for(severity: float, off_trough_pct: float, drawdown_pct: float, cfg: Config) -> str:
    """Map a 0-100 severity to a discrete phase via the config edges, then apply the Recovery STATE
    override: a still-underwater tape (drawdown below 0) that has rebounded >= `recovery_min_off_trough_pct`
    off its trough reads Recovery rather than the deep edge band — the rebound leg of the cycle. At/near a
    fresh high (drawdown ~ 0) the override never fires, so a calm tape reads Expansion from the edge lookup.
    No phase literal lives here — `label_for` + the config edges + the config recovery threshold decide."""
    base = label_for(severity, cfg.market_phase.phase_edges)
    mp = cfg.market_phase
    # Recovery override: only while genuinely still underwater (drawdown strictly below 0) AND rebounded
    # enough off the trough. A fresh-high tape (drawdown == 0) is an uptrend, not a recovery.
    if drawdown_pct < 0 and off_trough_pct >= mp.recovery_min_off_trough_pct:
        return PHASE_RECOVERY
    return base


def _gaussian_kernel(x: float, mean: float, std: float) -> float:
    """An UNNORMALIZED Gaussian likelihood kernel `(1/std) * exp(-((x-mean)^2) / (2 * std^2))`. The
    `sqrt(2*pi)` constant is dropped because it is identical across the two states and cancels in the
    filter's per-step normalization — the `1/std` factor is kept so states with different spreads weigh
    correctly. The only numbers are structural (the `2` of the Gaussian exponent and the squares)."""
    z = (x - mean) / std
    return (1 / std) * exp(-(z * z) / 2)


def _filtered_bear_path(observations: list[float], cfg: Config) -> list[float]:
    """The deterministic forward Hamilton FILTER over the [0, 1] stress `observations` (ascending by
    date, ALL dated <= D). Returns the per-step filtered P(state=bear | observations up to that step) —
    a closed-form recursion using the config transition matrix + per-state Gaussian emissions VERBATIM
    (NEVER EM-fit at serve time). The LAST element is the served P(bear) at D; earlier elements are the
    filtered values at each prior observation (used only to PROVE causality — a later observation never
    changes an earlier element). Empty in -> empty out (the caller maps that to NA)."""
    rs = cfg.regime_switching
    trans = rs.transition
    em = rs.emissions
    # the prior over (bear, risk_on) at the first observation, from config — no hard-coded prior.
    prior = {_BEAR: rs.initial_bear, _RISK_ON: 1 - rs.initial_bear}

    path: list[float] = []
    posterior = prior
    for index, obs in enumerate(observations):
        if index == 0:
            predicted = prior  # the configured prior governs the first step
        else:
            # one-step Markov prediction: P(next=s) = sum over prev of P(prev) * transition[prev][s].
            predicted = {
                s: sum(posterior[prev] * trans[prev][s] for prev in REGIME_SWITCHING_STATES)
                for s in REGIME_SWITCHING_STATES
            }
        # Bayesian update with this observation's per-state likelihood, then normalize across the 2 states.
        likelihood = {
            s: _gaussian_kernel(obs, em[s].mean, em[s].std) for s in REGIME_SWITCHING_STATES
        }
        unnormalized = {s: predicted[s] * likelihood[s] for s in REGIME_SWITCHING_STATES}
        total = sum(unnormalized.values())
        if total > 0:
            posterior = {s: unnormalized[s] / total for s in REGIME_SWITCHING_STATES}
        else:
            # a degenerate step (both likelihoods underflow to 0) keeps the predicted distribution rather
            # than fabricating a value — honest, deterministic, never a divide-by-zero.
            posterior = predicted
        path.append(posterior[_BEAR])
    return path


def _stored_runs_through(session: Session, d: date_cls) -> list[ScannerRun]:
    """Every immutable `ScannerRun` row dated <= D, ascending by `asof_date` (the SAME rows
    `regime_history` reads). The point-in-time observation set the filter ingests and the latest of which
    supplies the served-date severity. A single SELECT; recomputes nothing."""
    return list(
        session.exec(
            select(ScannerRun).where(ScannerRun.asof_date <= d).order_by(ScannerRun.asof_date)
        ).all()
    )


# ==================================================================================================
# iter-30 (J-89) — the CAUSAL market-phase history timeline + dated downtrend episodes, and (J-90) the
# causal recovery/turn signal. All three are STRICTLY causal derivations over the SAME single per-date
# series `compute_market_phase` already builds (the SAME `_filtered_bear_path` p_bear at each step + the
# SAME `_phase_for` phase per reading). They read no future bar, recompute no canonical value, and carry
# no threshold literal (every cutoff is a `config.market_phase` key). The SMOOTHED retrospective is a
# SEPARATE backward pass below — fenced, never consumed here.
# ==================================================================================================
def _timeline_series(
    readings: list[dict], filtered_path: list[float], cfg: Config
) -> list[dict]:
    """The per-snapshot-date CAUSAL timeline series `[{date, phase, p_bear, severity}]` (J-89). It reads
    the SAME single derivation the served panel value reads — the per-date FILTERED `p_bear` is the i-th
    element of the EXACT `_filtered_bear_path` the panel's served P(bear) is the LAST element of (single
    source: the timeline and the panel read ONE series, never a second computation), and the per-date
    `phase`/`severity` are the SAME `_phase_for(_severity_reading)` the served-date phase is. `readings`
    is the per-valid-run `{date, reading_obj}` list (ascending by date, ALL dated <= D); it is the SAME
    set, in the SAME order, the `observations`/`filtered_path` are built from, so element i of each lines
    up. Pure in-memory mapping over already-computed values; recomputes nothing."""
    series: list[dict] = []
    for index, entry in enumerate(readings):
        reading = entry["reading_obj"]
        severity = round(reading["reading"] * 100, 2)
        phase = _phase_for(severity, reading["off_trough_pct"], reading["drawdown_pct"], cfg)
        series.append({
            "date": entry["date"],
            "phase": phase,
            "p_bear": round(filtered_path[index], 6),
            "severity": severity,
        })
    return series


def _is_downtrend_date(point: dict, cfg: Config) -> bool:
    """Whether ONE causal timeline point is IN a downtrend (J-89): its phase is one of the deep phases
    (Bear / Correction) OR its filtered P(bear) is at/above `market_phase.downtrend_pbear_threshold`. A
    fixed structural phase membership test (the deep-phase labels come from the config edges) + the config
    P(bear) threshold — no magic number. Observed from the point's own (<= its date) information only."""
    mp = cfg.market_phase
    if point["phase"] in (_PHASE_BEAR, _PHASE_CORRECTION):
        return True
    return point["p_bear"] >= mp.downtrend_pbear_threshold


def _downtrend_episodes(timeline: list[dict], as_of: date_cls, cfg: Config) -> list[dict]:
    """The dated CAUSAL downtrend episodes (J-89): a deterministic grouping of the (<= D) timeline into
    MAXIMAL consecutive runs of downtrend dates (`_is_downtrend_date`). Each episode carries its
    `first_trigger_date`, the `severity_at_trigger` (the severity on that first date — observed on its
    own information only), the `last_date` (the most recent downtrend date in the run), the worst-seen
    `peak_p_bear` / `peak_severity` over the run, and whether it is `open` at D (its last date is the
    LATEST timeline date — i.e. still in a downtrend as of the resolved as-of) or `closed`. Empty/early
    history -> honest empty list (never a fabricated episode). Pure in-memory grouping of the already-
    derived causal series; recomputes nothing, reads no future bar (the timeline is already <= D)."""
    if not timeline:
        return []
    latest_date = timeline[-1]["date"]
    episodes: list[dict] = []
    current: Optional[dict] = None
    for point in timeline:
        if _is_downtrend_date(point, cfg):
            if current is None:
                current = {
                    "first_trigger_date": point["date"],
                    "severity_at_trigger": point["severity"],
                    "last_date": point["date"],
                    "peak_p_bear": point["p_bear"],
                    "peak_severity": point["severity"],
                }
            else:
                current["last_date"] = point["date"]
                current["peak_p_bear"] = max(current["peak_p_bear"], point["p_bear"])
                current["peak_severity"] = max(current["peak_severity"], point["severity"])
        else:
            if current is not None:
                episodes.append(current)
                current = None
    if current is not None:
        episodes.append(current)

    # an episode is OPEN at D iff its last downtrend date is the latest timeline date (still in a downtrend
    # as of the resolved as-of); otherwise it CLOSED on its last date (the tape left the downtrend after).
    for episode in episodes:
        episode["open"] = episode["last_date"] == latest_date
    return episodes


def _trailing_ma_reclaimed(session: Session, as_of: date_cls, cfg: Config) -> Optional[bool]:
    """Whether the benchmark close on/before D has RECLAIMED its trailing moving average over the config
    `recovery_trailing_ma_days` window (J-90 confirmation leg). Reads ONLY bars dated <= D via `bars_asof`
    (no lookahead): the last close vs the mean close over the trailing window. None when there is no bar
    on/before D (an honest gap — the caller treats a missing reclaim as no-signal, never fabricated). A
    pure causal read; recomputes nothing, carries no literal (the window is the config key)."""
    mp = cfg.market_phase
    bench = cfg.etfs.index[0]
    start = as_of - timedelta(days=mp.recovery_trailing_ma_days)
    window = [bar for bar in bars_asof(session, bench, as_of) if bar.date >= start]
    series = closes(window)
    if not series:
        return None
    trailing_ma = sum(series) / len(series)
    return series[-1] >= trailing_ma


def _recovery_turn_signal(
    session: Session, timeline: list[dict], as_of: date_cls, cfg: Config
) -> dict:
    """The CAUSAL recovery/turn signal for the resolved as-of D (J-90), computed from data <= D ONLY (no
    future bar). The signal is a config-defined downtrend-EXIT transition: the latest timeline date's
    filtered P(bear) has crossed BELOW `market_phase.recovery_signal_pbear_exit` while the PRIOR date was
    still at/above it (a fresh exit, not a sustained calm) AND the benchmark has reclaimed its trailing MA
    (`_trailing_ma_reclaimed`). Returns `{is_recovery_turn, available, reason, p_bear, prev_p_bear,
    exit_threshold, ma_reclaimed, ma_window_days}` — explainable (the triggering reason in words), never a
    bare flag. A single-date timeline (no prior date) or a missing benchmark bar -> honest non-signal with
    its reason. Reads the SAME causal series + a causal trailing-MA read; recomputes no canonical value and
    carries no threshold literal (every cutoff is a config key)."""
    mp = cfg.market_phase
    exit_threshold = mp.recovery_signal_pbear_exit
    base = {
        "is_recovery_turn": False,
        "available": True,
        "exit_threshold": exit_threshold,
        "ma_window_days": mp.recovery_trailing_ma_days,
    }
    if not timeline:
        return {**base, "available": False, "reason": "No causal timeline at this date.",
                "p_bear": None, "prev_p_bear": None, "ma_reclaimed": None}
    last = timeline[-1]
    p_bear = last["p_bear"]
    if len(timeline) < 2:
        return {**base, "reason": "Only one snapshot date — no prior P(bear) to confirm a downtrend exit.",
                "p_bear": p_bear, "prev_p_bear": None, "ma_reclaimed": None}
    prev_p_bear = timeline[-2]["p_bear"]
    ma_reclaimed = _trailing_ma_reclaimed(session, as_of, cfg)

    # a FRESH downtrend exit: P(bear) now below the exit threshold while the prior date was still at/above
    # it (a crossing, not a sustained calm), confirmed by the trailing-MA reclaim.
    crossed_below = p_bear < exit_threshold <= prev_p_bear
    is_turn = crossed_below and bool(ma_reclaimed)

    if is_turn:
        reason = (
            f"Filtered P(bear) crossed below the recovery exit ({exit_threshold:.2f}) — "
            f"{prev_p_bear:.2f} → {p_bear:.2f} — and the index reclaimed its "
            f"{mp.recovery_trailing_ma_days}-day trailing MA: a causal downtrend-exit / recovery turn."
        )
    elif crossed_below and ma_reclaimed is False:
        reason = (
            f"P(bear) crossed below the exit ({exit_threshold:.2f}) but the index has NOT reclaimed its "
            f"{mp.recovery_trailing_ma_days}-day trailing MA — not yet a confirmed recovery turn."
        )
    elif crossed_below and ma_reclaimed is None:
        reason = (
            f"P(bear) crossed below the exit ({exit_threshold:.2f}) but no benchmark bar is available to "
            "confirm the trailing-MA reclaim — not signalled (never fabricated)."
        )
    else:
        reason = (
            f"No fresh downtrend exit: P(bear) {p_bear:.2f} (prior {prev_p_bear:.2f}) vs the exit "
            f"threshold {exit_threshold:.2f}."
        )

    return {
        **base,
        "is_recovery_turn": is_turn,
        "reason": reason,
        "p_bear": p_bear,
        "prev_p_bear": prev_p_bear,
        "ma_reclaimed": ma_reclaimed,
    }


def _recovery_turn_dates_with_context(
    session: Session, timeline: list[dict], cfg: Config
) -> dict[str, dict]:
    """The set of CAUSAL recovery-turn signal DATES over the timeline (J-90), each mapped to its causal
    context `{phase, severity, p_bear, prev_p_bear}` AT THE SIGNAL DATE (read from the SAME single timeline
    derivation, <= that date — never recomputed). A date `timeline[i]` is a recovery turn iff the SAME
    rule `_recovery_turn_signal` applies at that point: a fresh P(bear) crossing below the config exit
    (`timeline[i].p_bear < exit <= timeline[i-1].p_bear`) confirmed by the trailing-MA reclaim of the
    benchmark on that date. The first timeline date can never be a turn (no prior P(bear)). Keyed by the
    ISO signal date so the J-90 edge study can join the stored `forward_returns` of THOSE dates' runs.
    Reads the SAME causal series + a causal trailing-MA read; recomputes no canonical value, no future bar."""
    mp = cfg.market_phase
    exit_threshold = mp.recovery_signal_pbear_exit
    out: dict[str, dict] = {}
    for i in range(1, len(timeline)):
        point = timeline[i]
        prev = timeline[i - 1]
        if not (point["p_bear"] < exit_threshold <= prev["p_bear"]):
            continue
        d = date_cls.fromisoformat(point["date"])
        if not _trailing_ma_reclaimed(session, d, cfg):
            continue
        out[point["date"]] = {
            "phase": point["phase"],
            "severity": point["severity"],
            "p_bear": point["p_bear"],
            "prev_p_bear": prev["p_bear"],
        }
    return out


def _causal_timeline(
    session: Session, as_of: Optional[date_cls], cfg: Config
) -> list[dict]:
    """The FULL per-snapshot-date CAUSAL timeline `[{date, phase, p_bear, severity}]` over the stored
    snapshot history, optionally scoped to runs dated <= `as_of` (the J-32 point-in-time mode — a FILTER,
    never a second date state). Builds the SAME single causal derivation `compute_market_phase` /
    `recovery_turn_dates` read (the SAME `_severity_reading` -> `_filtered_bear_path` -> `_timeline_series`
    -> `_phase_for`), then returns the un-truncated timeline. `as_of=None` -> all stored runs (all-history).
    Recomputes nothing the panel doesn't already compute; reads no future bar (every entry is <= its date,
    and the whole timeline is <= `as_of` when scoped). Shared verbatim by `recovery_turn_dates` and the
    J-91 `phase_context_by_date` accessor so there is ONE causal series, never a second computation."""
    runs = _stored_runs_through(session, as_of) if as_of is not None else list(
        session.exec(select(ScannerRun).order_by(ScannerRun.asof_date)).all()
    )
    readings: list[dict] = []
    observations: list[float] = []
    with bar_cache(session):
        for run in runs:
            reading = _severity_reading(session, run, cfg)
            if reading is None:
                continue
            readings.append({"date": run.asof_date.isoformat(), "reading_obj": reading})
            # the FILTER observation (J-88) — the macro-aware observation (== the severity reading when the
            # macro regime-switching leg is disabled, so byte-identical to the price/breadth/VIX-only path).
            observations.append(round(reading["observation"], 6))
    filtered_path = _filtered_bear_path(observations, cfg)
    return _timeline_series(readings, filtered_path, cfg)


def phase_context_by_date(
    session: Session, as_of: Optional[date_cls] = None, config: Optional[Config] = None
) -> dict[str, dict]:
    """The public read-only accessor the J-91 Downtrend Opportunity study calls: for EVERY stored snapshot
    date (optionally <= `as_of` — the J-32 point-in-time FILTER, never a second date state) the CAUSAL
    market-phase context at that date, keyed by the ISO date -> `{phase, severity, p_bear}`. Read from the
    SAME single causal timeline `compute_market_phase` reads (the SAME `_filtered_bear_path` FILTERED
    p_bear at each step + the SAME `_phase_for` phase per reading) — strictly causal (each entry uses only
    its own <= D information), and NEVER the J-89 SMOOTHED/true-bear retrospective (those stay fenced and
    feed no as-of value). `as_of=None` -> all stored runs (all-history). Recomputes nothing; reads no
    future bar. The study joins THIS context to each observation's snapshot date (the additive conditioning
    tag), so a tag is set only by <= D information (no-lookahead by construction)."""
    cfg = config or get_config()
    timeline = _causal_timeline(session, as_of, cfg)
    return {
        point["date"]: {
            "phase": point["phase"],
            "severity": point["severity"],
            "p_bear": point["p_bear"],
        }
        for point in timeline
    }


def recovery_turn_dates(
    session: Session, as_of: Optional[date_cls] = None, config: Optional[Config] = None
) -> dict[str, dict]:
    """The public read-only accessor the J-90 Recovery-Turn Edge study calls: the CAUSAL recovery-turn
    signal dates (with their causal context) over the stored snapshot history, optionally scoped to runs
    dated <= `as_of` (the J-32 point-in-time mode — a FILTER, never a second date state). Builds the SAME
    single causal timeline `compute_market_phase` reads (the SAME `_filtered_bear_path` + `_phase_for`),
    then derives the turn dates from it (`_recovery_turn_dates_with_context`). `as_of=None` -> all stored
    runs (all-history). Recomputes nothing the panel doesn't already compute; reads no future bar."""
    cfg = config or get_config()
    timeline = _causal_timeline(session, as_of, cfg)  # the SAME single causal series the panel reads
    return _recovery_turn_dates_with_context(session, timeline, cfg)


def compute_market_phase(
    session: Session, as_of: date_cls, config: Optional[Config] = None
) -> dict:
    """The SINGLE canonical Market Phase & Severity derivation (Data Contract value, J-87 + J-88) for the
    resolved as-of date `as_of`. STRICTLY causal: it reads only stored `ScannerRun` rows + index/^VIX bars
    dated <= D. Returns the discrete `phase`, the 0-100 `severity` with its named `components` breakdown,
    the cycle legs (`drawdown_pct` / `off_trough_pct`), and the forward FILTERED `p_bear` with its disclosed
    `observations` vector (one [0, 1] stress reading per stored run <= D). It recomputes NO canonical value
    (regime/breadth read verbatim) and adds no snapshot column.

    NA / partial: when there is no stored run <= D, or the latest such run's benchmark window has
    insufficient history, the payload carries `available: False` with `phase`/`severity`/`p_bear` = None —
    an honest empty/partial treatment, never a fabricated figure. The filtered `p_bear` is None when the
    observation vector is empty (no run with a valid reading <= D)."""
    cfg = config or get_config()

    runs = _stored_runs_through(session, as_of)

    # build the causal observation vector: the [0, 1] stress reading at each stored run <= D (skipping a
    # run whose window has insufficient history — an honest gap, not a fabricated reading). Each carries
    # the run's date + reading for disclosure (J-88 observation vector). The `bar_cache` context (J-46)
    # loads each benchmark/^VIX series ONCE and slices `date <= d` in memory, so a many-run host
    # (daily-history backfill) does NOT issue one full-series query per run — byte-identical to the
    # uncached per-request path (the cache only changes WHERE the bars are loaded, never WHICH bars).
    observations: list[dict] = []
    readings: list[dict] = []  # the FULL per-valid-run reading (for the per-date timeline phase, J-89)
    latest_reading: Optional[dict] = None
    with bar_cache(session):
        for run in runs:
            reading = _severity_reading(session, run, cfg)
            if reading is None:
                continue
            observations.append({
                "date": run.asof_date.isoformat(),
                "reading": round(reading["reading"], 6),
                # the FILTER input (J-88) — the macro-aware observation (== `reading` when the macro
                # regime-switching leg is disabled, so byte-identical to the price/breadth/VIX-only path).
                "observation": round(reading["observation"], 6),
            })
            readings.append({"date": run.asof_date.isoformat(), "reading_obj": reading})
            latest_reading = reading  # the last valid reading is the served-date severity source

    asof_iso = as_of.isoformat()

    # NA / partial: no stored run <= D with a valid window -> honest empty payload (never fabricated).
    if latest_reading is None:
        return {
            "asof_date": asof_iso,
            "available": False,
            "phase": None,
            "severity": None,
            "p_bear": None,
            "drawdown_pct": None,
            "off_trough_pct": None,
            "components": [],
            "observations": [],
            "min_history_bars": cfg.market_phase.min_history_bars,
            "labels": list(cfg.market_phase.labels),
            # iter-30 (J-89 / J-90): an honest empty timeline / episode list and an honest non-signal on a
            # window with no derivable phase — never a fabricated episode/probability/signal.
            "timeline": [],
            "episodes": [],
            "recovery_turn": {
                "is_recovery_turn": False,
                "available": False,
                "reason": "No derivable market phase for this date (insufficient history).",
            },
            # iter-38 (J-97): honest-empty full series too (the cross-view bottom pane renders empty, never a
            # fabricated band/line). Stripped from the default card payload like the available path.
            "timeline_full": [],
        }

    severity = round(latest_reading["reading"] * 100, 2)
    phase = _phase_for(
        severity, latest_reading["off_trough_pct"], latest_reading["drawdown_pct"], cfg
    )

    # the forward filtered P(bear) over the FULL causal observation vector (EVERY reading <= D, in date
    # order) — the served P(bear) consumes them all (strictly causal, deterministic). The filter ingests
    # the macro-aware `observation` (== `reading` when the regime-switching leg is disabled — byte-identical).
    obs_values = [o["observation"] for o in observations]
    filtered_path = _filtered_bear_path(obs_values, cfg)
    p_bear = round(filtered_path[-1], 6) if filtered_path else None

    # disclose only the MOST RECENT `observation_disclosure_limit` observations in the payload (the filter
    # still consumed all of them above) — so a daily-history host serves a bounded, readable tail rather
    # than thousands of chips; `total_observations` discloses the full causal count honestly. Each disclosed
    # observation additionally carries its filtered P(bear) at that step (the tail of `filtered_path`). The
    # internal `observation` key (the macro-aware filter input) is stripped from the disclosed payload so it
    # stays byte-identical to the price/breadth/VIX-only path when the macro leg is disabled.
    limit = cfg.market_phase.observation_disclosure_limit
    disclosed = [
        {"date": obs["date"], "reading": obs["reading"], "p_bear": round(filtered_path[index], 6)}
        for index, obs in enumerate(observations)
    ][-limit:]

    # iter-30 (J-89): the per-snapshot-date CAUSAL timeline series {date, phase, p_bear} — the SAME single
    # derived series the panel reads (the SAME `_filtered_bear_path` p_bear at each step + the SAME
    # `_phase_for` phase per reading). The timeline and the panel read ONE derivation, never a second
    # computation (single source). Bounded to the SAME most-recent disclosure tail so a daily-history host
    # serves a readable series; `total_timeline_dates` discloses the full causal count.
    timeline_full = _timeline_series(readings, filtered_path, cfg)
    timeline = timeline_full[-limit:]

    # iter-30 (J-89): the dated CAUSAL downtrend episodes grouped from the FULL (un-truncated) timeline —
    # each {first_trigger_date, severity_at_trigger, last_date, open|closed at D}. Observed on its dates
    # only (no future bar); empty/early history -> honest empty list. Disclose the FULL set (episodes are
    # few even on a daily-history host).
    episodes = _downtrend_episodes(timeline_full, as_of, cfg)

    # iter-30 (J-90): the causal recovery/turn signal for the resolved as-of D, computed from data <= D
    # only (the filtered P(bear) crossing below the config exit while the index reclaims its trailing MA).
    recovery_turn = _recovery_turn_signal(session, timeline_full, as_of, cfg)

    return {
        "asof_date": asof_iso,
        "available": True,
        "phase": phase,
        "severity": severity,
        "p_bear": p_bear,
        "drawdown_pct": latest_reading["drawdown_pct"],
        "off_trough_pct": latest_reading["off_trough_pct"],
        "components": latest_reading["components"],
        "vix_level": latest_reading["vix_level"],
        # the disclosed (bounded, most-recent) observation tail the filter ingested (date + [0, 1] reading
        # + the step's filtered P(bear)), ascending by date; `total_observations` is the full causal count.
        "observations": disclosed,
        "total_observations": len(observations),
        "min_history_bars": cfg.market_phase.min_history_bars,
        "labels": list(cfg.market_phase.labels),
        # iter-30 (J-89 / J-90) ADDITIVE causal fields (read from the SAME single derived series above —
        # no second computation, no second value). The SMOOTHED retrospective lives ONLY behind the separate
        # `retrospective` field (a sibling read), never here.
        "timeline": timeline,
        "total_timeline_dates": len(timeline_full),
        "episodes": episodes,
        "recovery_turn": recovery_turn,
        # iter-38 (J-97): the FULL-history causal timeline series, carried in the canonical payload (so the
        # SAME `market_phase_cached` row + `dataset_version` stamp serves it — no new cache, no recompute).
        # It is the SAME `timeline_full` the bounded `timeline` tail above is sliced from (single source).
        # The default `GET /api/market-phase` endpoint STRIPS this key so the card payload stays
        # byte-identical to today; only the J-97 cross-view chart opts in via `?full=true`. Strictly causal
        # per point (every point read from its own ≤ D snapshot) — no smoothed/true-bear value lives here.
        "timeline_full": timeline_full,
    }


# iter-39 (J-97 fix): a PAYLOAD-SCHEMA version token folded into the `MarketPhaseCache` key.
# `_dataset_version` tracks DATA changes (backfill add / removal) ONLY — NOT the payload SCHEMA. When an
# ADDITIVE field is added to the cached payload (iter-38 added `timeline_full`), every pre-existing row is
# keyed to the unchanged data stamp and is served VERBATIM without the new field (the bottom cross-view
# pane rendered empty at the live current as-of, a cache HIT). Bump this constant whenever the cached
# market-phase / retrospective payload SHAPE changes so every stale-schema row becomes a guaranteed MISS
# and is recomputed once WITH the new field. It is folded into the existing `dataset_version` STRING
# composite stored in the cache row (NOT a new DB column — that would need `db.py` `_ADDITIVE_COLUMNS` +
# the `test_db.py` guards on the live persistent DB). `s1` = the iter-38 `timeline_full` additive field.
SCHEMA_VERSION = "s1"


def _cache_version(session: Session) -> str:
    """The composite cache-key version: the J-72 data stamp PLUS the payload-SCHEMA token, so a payload
    shape change invalidates every stale-schema row independently of any data change. Single-sourced from
    `_dataset_version` (the data half) — never duplicates that stamp's logic."""
    return f"{_dataset_version(session)}|{SCHEMA_VERSION}"


def market_phase_cached(
    session: Session, as_of: date_cls, config: Optional[Config] = None
) -> dict:
    """Serve the Market Phase & Severity derivation from the J-87/J-88 cache (mirrors
    `research.event_study_cached`): on a cache HIT for the current `(asof_key, cache_version)` key,
    deserialize and return the stored payload (NO recompute); on a MISS, compute it ONCE via
    `compute_market_phase`, persist it under the current cache-version stamp, prune any stale rows for
    THIS as-of (older `dataset_version`), and return it. The returned payload is BYTE-IDENTICAL to
    `compute_market_phase(...)` — the cache is a pure performance layer (No recompute in the read path).
    The key carries the J-72 `_dataset_version` data stamp (single-sourced) PLUS the iter-39 payload
    `SCHEMA_VERSION` token (`_cache_version`), so the cache REFRESHES automatically after any dataset change
    (a backfill add or a removal) AND after any payload-shape change (an additive field) — a stale-data OR
    stale-SCHEMA row is never hit (iter-38 lesson: `timeline_full` was invisible at every already-cached
    row keyed to the bare data stamp)."""
    cfg = config or get_config()
    version = _cache_version(session)
    asof_key = as_of.isoformat()

    hit = session.exec(
        select(MarketPhaseCache).where(
            MarketPhaseCache.asof_key == asof_key,
            MarketPhaseCache.dataset_version == version,
        )
    ).first()
    if hit is not None:
        return json.loads(hit.payload_json)

    # MISS — compute once and persist under the current stamp.
    payload = compute_market_phase(session, as_of, cfg)

    # prune stale rows for THIS as-of (any older dataset_version) so the cache table does not grow
    # unbounded as the dataset matures; the current-version row is then inserted.
    stale = session.exec(
        select(MarketPhaseCache).where(
            MarketPhaseCache.asof_key == asof_key,
            MarketPhaseCache.dataset_version != version,
        )
    ).all()
    for row in stale:
        session.delete(row)

    session.add(MarketPhaseCache(
        asof_key=asof_key, dataset_version=version,
        payload_json=json.dumps(payload), created_at=datetime.now(timezone.utc),
    ))
    try:
        session.commit()
    except Exception:  # a concurrent writer raced us to the same key — the cache is best-effort, not a
        session.rollback()  # source of truth; the freshly computed payload is byte-identical, so return it
    return payload


# the additive J-97 full-series key. Stripped from the DEFAULT card payload so that response stays
# byte-identical to today; carried only when the J-97 cross-view chart opts in via `?full=true`.
_FULL_TIMELINE_KEY = "timeline_full"


def market_phase_full_cached(
    session: Session, as_of: date_cls, config: Optional[Config] = None
) -> dict:
    """iter-38 (J-97): serve the Market-Phase payload WITH the full-history causal `timeline_full` series
    attached, for the Dashboard two-pane cross-view (`GET /api/market-phase?full=true`).

    It reads the SAME `market_phase_cached` row under the SAME `dataset_version` stamp (no new cache, no
    new endpoint, no recompute) — the cached payload ALREADY carries `timeline_full` (the SAME series the
    bounded `timeline` tail is sliced from; single source). This function simply returns that cached payload
    verbatim with the full series present; the DEFAULT serve path (`market_phase_default_payload`) strips it
    so the card response stays byte-identical to today (the additive opt-in pattern, mirroring the
    `/api/indexes?full=true` + `/api/regime-history?full=true` J-49 clamp-optional precedent)."""
    return market_phase_cached(session, as_of, config)


def market_phase_default_payload(
    session: Session, as_of: date_cls, config: Optional[Config] = None
) -> dict:
    """The DEFAULT (card) Market-Phase payload — `market_phase_cached` with the J-97 `timeline_full` opt-in
    series STRIPPED, so the card response is byte-identical to today (the bounded `timeline` tail,
    `total_timeline_dates`, episodes, recovery-turn all unchanged). The full series is served only via
    `market_phase_full_cached` (the `?full=true` opt-in). The strip is a shallow copy that leaves the cached
    row untouched."""
    payload = market_phase_cached(session, as_of, config)
    if _FULL_TIMELINE_KEY in payload:
        payload = {k: v for k, v in payload.items() if k != _FULL_TIMELINE_KEY}
    return payload


# ==================================================================================================
# iter-30 (J-89) — the FENCED RETROSPECTIVE (full-sample / analysis-only) sub-view: the SMOOTHED P(bear)
# and the peak-to-trough "true bear dating". The SMOOTHED probability is LOOKAHEAD BY CONSTRUCTION (a
# backward pass conditions on FUTURE observations) and the peak-to-trough dating is future-aware (a trough
# is only known after the fact). Both live ONLY here, served behind a SEPARATE explicitly-named
# `retrospective` field/endpoint — NEVER consumed by `compute_market_phase`'s phase/severity/filtered-
# p_bear, the timeline, the episodes, the J-90 recovery-turn signal, or the J-90 edge study (the J-49
# fenced-context precedent). The fence is STRUCTURAL: no function above reads anything this section
# produces. The backward smoother reads the SAME `config.regime_switching` params VERBATIM (never EM-fit);
# the Bry-Boschan dater's cutoffs are config keys (no literal).
# ==================================================================================================
def _smoothed_bear_path(observations: list[float], cfg: Config) -> list[float]:
    """The deterministic full-sample SMOOTHED P(state=bear | ALL observations) via the Hamilton-Kim
    fixed-interval smoother over the [0, 1] stress `observations` (ascending by date) + the SAME
    `config.regime_switching` params VERBATIM (NEVER EM-fit). This is LOOKAHEAD BY CONSTRUCTION — the
    smoothed value at step t conditions on observations AFTER t — so it is served ONLY on the fenced
    retrospective surface and NEVER feeds any as-of value (the J-49 fence). Implementation: a forward
    filter pass (storing each step's filtered posterior + its one-step predicted distribution), then a
    backward recursion `smoothed[t] = filtered[t] * Σ_s smoothed[t+1][s] * trans[t->s] / predicted[t+1][s]`
    (the standard Kim smoother), returning the per-step smoothed P(bear). Empty in -> empty out. The only
    numbers are structural (0/1 probabilities, indexing); every param is config."""
    rs = cfg.regime_switching
    trans = rs.transition
    em = rs.emissions
    prior = {_BEAR: rs.initial_bear, _RISK_ON: 1 - rs.initial_bear}

    n = len(observations)
    if n == 0:
        return []

    # forward pass: store each step's filtered posterior + the one-step predicted distribution that fed it.
    filtered: list[dict] = []
    predicted_seq: list[dict] = []
    posterior = prior
    for index, obs in enumerate(observations):
        predicted = (
            prior if index == 0
            else {
                s: sum(posterior[prev] * trans[prev][s] for prev in REGIME_SWITCHING_STATES)
                for s in REGIME_SWITCHING_STATES
            }
        )
        likelihood = {s: _gaussian_kernel(obs, em[s].mean, em[s].std) for s in REGIME_SWITCHING_STATES}
        unnormalized = {s: predicted[s] * likelihood[s] for s in REGIME_SWITCHING_STATES}
        total = sum(unnormalized.values())
        posterior = (
            {s: unnormalized[s] / total for s in REGIME_SWITCHING_STATES} if total > 0 else predicted
        )
        filtered.append(posterior)
        predicted_seq.append(predicted)

    # backward pass: the last smoothed equals the last filtered; earlier steps mix in the future via the
    # Kim recursion. predicted_seq[t+1][s] is the prior P(state at t+1 = s | obs <= t) the smoother divides
    # by; a degenerate (0) predicted entry is skipped (its transition contribution is 0 anyway).
    smoothed: list[dict] = [dict(filtered[-1])]
    for t in range(n - 2, -1, -1):
        future = smoothed[0]
        pred_next = predicted_seq[t + 1]
        smoothed_t = {}
        for s in REGIME_SWITCHING_STATES:
            ratio_sum = 0  # structural accumulator (int 0 like the rest of the engine — No magic numbers)
            for s_next in REGIME_SWITCHING_STATES:
                denom = pred_next[s_next]
                if denom > 0:
                    ratio_sum += future[s_next] * trans[s][s_next] / denom
            smoothed_t[s] = filtered[t][s] * ratio_sum
        # renormalize (the Kim recursion preserves a proper distribution up to numerical drift) — honest,
        # deterministic; a degenerate all-zero step falls back to the filtered posterior (never fabricated).
        norm = sum(smoothed_t.values())
        smoothed_t = (
            {s: smoothed_t[s] / norm for s in REGIME_SWITCHING_STATES} if norm > 0 else dict(filtered[t])
        )
        smoothed.insert(0, smoothed_t)
    return [round(step[_BEAR], 6) for step in smoothed]


def _true_bear_episodes(dated_closes: list[dict], cfg: Config) -> list[dict]:
    """The peak-to-trough "true bear dating" over the benchmark closes at each snapshot date (J-89,
    retrospective / Bry-Boschan-NBER-style). `dated_closes` is `[{date, close}]` ascending by date (the
    benchmark close AS OF each stored snapshot date). FUTURE-AWARE BY CONSTRUCTION (a trough is only known
    once the tape rebounds), so this lives ONLY on the fenced retrospective surface. Deterministic dating:
    scan for each local peak the deepest subsequent trough BEFORE the close recovers back above the peak,
    emit a candidate `{peak_date, trough_date, peak_close, trough_close, drawdown_pct, duration_days}`,
    then CENSOR candidates shorter than `bry_boschan_min_phase_days` (calendar days, peak->trough) or
    shallower than `bry_boschan_min_amplitude_pct` (peak-to-trough drawdown %). Overlapping candidates are
    de-duplicated by keeping the FIRST (earliest-peak) of any pair whose spans overlap, so the 2022 bear
    surfaces as ONE dated phase. Pure in-memory arithmetic; the only literals are structural (0/1 indexing
    + the 100 percent unit) — the two cutoffs are config keys. Empty/short history -> honest empty list."""
    mp = cfg.market_phase
    n = len(dated_closes)
    if n < 2:
        return []

    closes_list = [d["close"] for d in dated_closes]
    candidates: list[dict] = []
    i = 0
    while i < n - 1:
        peak_close = closes_list[i]
        # require a local peak: the close is not lower than its immediate predecessor (a rising-into-peak
        # filter that avoids dating from mid-decline points). The very first bar is always a candidate peak.
        if i > 0 and closes_list[i] < closes_list[i - 1]:
            i += 1
            continue
        # find the deepest trough AFTER i, up to (and including) the bar where the close first recovers
        # back to/above the peak (the phase ends when the drawdown is fully retraced).
        trough_index = i
        trough_close = peak_close
        j = i + 1
        while j < n:
            if closes_list[j] >= peak_close:
                break  # the close recovered to/above the peak — the decline phase has ended
            if closes_list[j] < trough_close:
                trough_close = closes_list[j]
                trough_index = j
            j += 1
        if trough_index > i:
            drawdown_pct = (trough_close / peak_close - 1) * 100 if peak_close > 0 else 0
            duration_days = (dated_closes[trough_index]["date_obj"] - dated_closes[i]["date_obj"]).days
            candidates.append({
                "peak_date": dated_closes[i]["date"],
                "trough_date": dated_closes[trough_index]["date"],
                "peak_close": round(peak_close, 4),
                "trough_close": round(trough_close, 4),
                "drawdown_pct": round(drawdown_pct, 2),
                "duration_days": duration_days,
                "_peak_index": i,
                "_trough_index": trough_index,
            })
            i = trough_index + 1  # continue scanning after this decline's trough
        else:
            i += 1

    # CENSOR by the config Bry-Boschan cutoffs: a true-bear phase must be deep enough AND long enough.
    censored = [
        c for c in candidates
        if abs(c["drawdown_pct"]) >= mp.bry_boschan_min_amplitude_pct
        and c["duration_days"] >= mp.bry_boschan_min_phase_days
    ]
    # strip the internal index helpers from the served rows (kept above only for the scan continuation).
    return [
        {k: v for k, v in c.items() if not k.startswith("_")}
        for c in censored
    ]


def _benchmark_close_on_or_before(session: Session, d: date_cls, cfg: Config) -> Optional[float]:
    """The benchmark (SPY) close on/before D (date <= D, no lookahead) — the SAME first index ETF the
    severity drawdown leg reads. None when no bar exists. A pure causal read used to build the
    retrospective's per-snapshot-date close series; recomputes nothing."""
    bench = cfg.etfs.index[0]
    series = closes(bars_asof(session, bench, d))
    return series[-1] if series else None


def compute_retrospective(
    session: Session, as_of: date_cls, config: Optional[Config] = None
) -> dict:
    """The FENCED RETROSPECTIVE (full-sample / analysis-only) derivation (Data Contract value, J-89 — the
    SEPARATE retrospective field). For the resolved as-of D it returns the per-snapshot-date SMOOTHED
    P(bear) series (`_smoothed_bear_path`, lookahead by construction) and the peak-to-trough true-bear
    dating (`_true_bear_episodes`, future-aware). BOTH are analysis-only and are NEVER consumed by any
    as-of value — this is the single place the smoothed probability and the true-bear dating are computed,
    behind the structural fence. Strictly bounded to the SAME stored runs <= D the causal layer reads
    (so a historical as-of's retrospective is the full-sample analysis over the window UP TO D — the
    retrospective is "full-sample within the resolved window", future-aware WITHIN that window, never
    reading a run dated > D). Honest empty/NA on short history (never a fabricated smoothed value/episode).

    Returns `{asof_date, available, analysis_only, smoothed[], true_bear_episodes[], min_history_bars,
    min_phase_days, min_amplitude_pct}`. `analysis_only` is always True (a structural disclosure flag for
    the UI fence). Recomputes no canonical value; reads no run dated > D."""
    cfg = config or get_config()
    runs = _stored_runs_through(session, as_of)

    # the SAME causal observation vector + per-date benchmark close the causal layer reads (<= D only).
    observations: list[dict] = []
    dated_closes: list[dict] = []
    with bar_cache(session):
        for run in runs:
            reading = _severity_reading(session, run, cfg)
            if reading is None:
                continue
            # the FENCED retrospective smoother (J-89) ingests the SAME macro-aware filter observation the
            # causal layer uses (== the severity reading when the regime-switching leg is disabled). The
            # smoothed value remains analysis-only and is NEVER read by any as-of value (the J-49 fence).
            observations.append({"date": run.asof_date.isoformat(), "reading": reading["observation"]})
            close = _benchmark_close_on_or_before(session, run.asof_date, cfg)
            if close is not None:
                dated_closes.append({
                    "date": run.asof_date.isoformat(),
                    "date_obj": run.asof_date,
                    "close": close,
                })

    asof_iso = as_of.isoformat()
    if not observations:
        return {
            "asof_date": asof_iso,
            "available": False,
            "analysis_only": True,
            "smoothed": [],
            "true_bear_episodes": [],
            "min_history_bars": cfg.market_phase.min_history_bars,
            "min_phase_days": cfg.market_phase.bry_boschan_min_phase_days,
            "min_amplitude_pct": cfg.market_phase.bry_boschan_min_amplitude_pct,
        }

    obs_values = [o["reading"] for o in observations]
    smoothed_path = _smoothed_bear_path(obs_values, cfg)
    smoothed = [
        {"date": observations[index]["date"], "p_bear_smoothed": smoothed_path[index]}
        for index in range(len(observations))
    ]
    # bound the disclosed smoothed tail to the SAME most-recent disclosure limit the causal series uses.
    limit = cfg.market_phase.observation_disclosure_limit
    smoothed_disclosed = smoothed[-limit:]

    true_bear = _true_bear_episodes(dated_closes, cfg)

    return {
        "asof_date": asof_iso,
        "available": True,
        "analysis_only": True,
        "smoothed": smoothed_disclosed,
        "total_smoothed_dates": len(smoothed),
        "true_bear_episodes": true_bear,
        "min_history_bars": cfg.market_phase.min_history_bars,
        "min_phase_days": cfg.market_phase.bry_boschan_min_phase_days,
        "min_amplitude_pct": cfg.market_phase.bry_boschan_min_amplitude_pct,
    }


# The namespace prefix for the FENCED retrospective cache rows in the SHARED `MarketPhaseCache` table —
# so a retrospective payload never collides with the causal payload for the SAME as-of (the causal key is
# the bare ISO date). A fixed structural prefix (not a tunable); reusing the same table keeps the cache
# machinery single-sourced (no second cache mechanism, no new table — iter-20 lesson).
_RETRO_KEY_PREFIX = "retro:"


def retrospective_cached(
    session: Session, as_of: date_cls, config: Optional[Config] = None
) -> dict:
    """Serve the FENCED retrospective (J-89) from the SHARED `MarketPhaseCache` (mirrors
    `market_phase_cached`), keyed by `(_RETRO_KEY_PREFIX + asof_key, dataset_version)` so it reuses the
    SAME cache table + the SAME `_dataset_version` stamp (single-sourced, J-72) WITHOUT colliding with the
    causal payload for the same as-of. On a HIT, return the stored payload (NO recompute); on a MISS,
    compute it ONCE via `compute_retrospective`, persist under the current stamp, prune stale rows for THIS
    retrospective key, and return it. BYTE-IDENTICAL to a fresh compute (a pure performance layer). The
    SMOOTHED series + true-bear dating served here are analysis-only and never consumed by an as-of value
    (the structural fence). It carries the SAME iter-39 `SCHEMA_VERSION` token via `_cache_version` so any
    additive field added to the retrospective payload also invalidates every stale-schema row (the
    identical staleness risk the causal path had); the served payload stays byte-identical post-fix (the
    smoothed/true-bear fence is unchanged — only the cache KEY string changes)."""
    cfg = config or get_config()
    version = _cache_version(session)
    asof_key = _RETRO_KEY_PREFIX + as_of.isoformat()

    hit = session.exec(
        select(MarketPhaseCache).where(
            MarketPhaseCache.asof_key == asof_key,
            MarketPhaseCache.dataset_version == version,
        )
    ).first()
    if hit is not None:
        return json.loads(hit.payload_json)

    payload = compute_retrospective(session, as_of, cfg)

    stale = session.exec(
        select(MarketPhaseCache).where(
            MarketPhaseCache.asof_key == asof_key,
            MarketPhaseCache.dataset_version != version,
        )
    ).all()
    for row in stale:
        session.delete(row)

    session.add(MarketPhaseCache(
        asof_key=asof_key, dataset_version=version,
        payload_json=json.dumps(payload), created_at=datetime.now(timezone.utc),
    ))
    try:
        session.commit()
    except Exception:  # best-effort cache; a concurrent writer raced us — the payload is byte-identical
        session.rollback()
    return payload
