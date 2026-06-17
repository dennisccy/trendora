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
from app.models import MarketPhaseCache, ScannerRun

# The Recovery phase label (a STATE override applied after the severity->phase edge lookup): a still-
# underwater tape that has rebounded >= `recovery_min_off_trough_pct` off its trough reads Recovery
# rather than the deep edge band. A fixed structural label (it is one of the configured phase labels);
# the threshold that triggers it is config (`market_phase.recovery_min_off_trough_pct`).
PHASE_RECOVERY = "Recovery"

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
    weights = mp.weights
    available = {name: value for name, value in raw.items() if value is not None}
    available_weight = sum(weights[name] for name in available)
    reading = (
        sum(value * weights[name] for name, value in available.items()) / available_weight
        if available_weight
        else 0
    )

    # the disclosed per-component breakdown (explainable — never a bare number). Iterate the canonical
    # weight-key set so every configured component appears (even when NA), in a stable order.
    components = []
    for name in sorted(MARKET_PHASE_WEIGHT_KEYS):
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

    return {
        "reading": reading,
        "components": components,
        "vix_level": vix_disclosure,
        "drawdown_pct": round(dd["drawdown_pct"], 2),
        "off_trough_pct": round(dd["off_trough_pct"], 2),
    }


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
    latest_reading: Optional[dict] = None
    with bar_cache(session):
        for run in runs:
            reading = _severity_reading(session, run, cfg)
            if reading is None:
                continue
            observations.append(
                {"date": run.asof_date.isoformat(), "reading": round(reading["reading"], 6)}
            )
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
        }

    severity = round(latest_reading["reading"] * 100, 2)
    phase = _phase_for(
        severity, latest_reading["off_trough_pct"], latest_reading["drawdown_pct"], cfg
    )

    # the forward filtered P(bear) over the FULL causal observation vector (EVERY reading <= D, in date
    # order) — the served P(bear) consumes them all (strictly causal, deterministic).
    obs_values = [o["reading"] for o in observations]
    filtered_path = _filtered_bear_path(obs_values, cfg)
    p_bear = round(filtered_path[-1], 6) if filtered_path else None

    # disclose only the MOST RECENT `observation_disclosure_limit` observations in the payload (the filter
    # still consumed all of them above) — so a daily-history host serves a bounded, readable tail rather
    # than thousands of chips; `total_observations` discloses the full causal count honestly. Each disclosed
    # observation additionally carries its filtered P(bear) at that step (the tail of `filtered_path`).
    limit = cfg.market_phase.observation_disclosure_limit
    disclosed = [
        {**obs, "p_bear": round(filtered_path[index], 6)}
        for index, obs in enumerate(observations)
    ][-limit:]

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
    }


def market_phase_cached(
    session: Session, as_of: date_cls, config: Optional[Config] = None
) -> dict:
    """Serve the Market Phase & Severity derivation from the J-87/J-88 cache (mirrors
    `research.event_study_cached`): on a cache HIT for the current `(asof_key, dataset_version)` key,
    deserialize and return the stored payload (NO recompute); on a MISS, compute it ONCE via
    `compute_market_phase`, persist it under the current dataset-version stamp, prune any stale rows for
    THIS as-of (older `dataset_version`), and return it. The returned payload is BYTE-IDENTICAL to
    `compute_market_phase(...)` — the cache is a pure performance layer (No recompute in the read path).
    Because the key carries the SAME `_dataset_version` stamp J-72 uses (single-sourced), the cache
    REFRESHES automatically after any dataset change (a backfill add or a removal) — a stale row is never
    hit."""
    cfg = config or get_config()
    version = _dataset_version(session)
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
