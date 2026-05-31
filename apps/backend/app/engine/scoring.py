"""Per-stock scoring engine — the canonical Leadership / Entry Quality / Risk scores AND the
setup status (Data Contract: app.engine.scoring), served by `GET /api/stocks` (list) and
`GET /api/stocks/{ticker}` (detail) from the SAME computation (anti-goal: Single source of
truth → J-06). The dashboard's candidate counts count THESE rows' statuses.

`score_stocks(session, asof)` produces, for every `config.universe.symbols` stock, its COMPLETE
canonical record in ONE pass: three independent scores, each a config-weighted blend of named,
cross-sectionally-normalized components, plus the setup status + reason, the invalidation level,
theme chips, and the VCP pattern flag. The VCP flag (iter-11) is composed onto the row ALONGSIDE
the setup status via `patterns.detect_vcp` — it is a separate DETECTED PATTERN, never a setup status
(it never touches `classify_setup`), so adding it changes no row's `setup_status`. It mirrors the proven
`sectors.py` pattern (cross-sectional percentile → weighted blend → 0-100 → `to_bucket`,
NA-graceful), and composes the canonical regime (read once, never recomputed) + the canonical
sector ranking (read once) for the two contextual Risk components.

Score directions (stated so comparisons stay consistent everywhere):
  - Leadership: higher = stronger.
  - Entry Quality: higher = a better (less-extended, better-located) entry.
  - Risk: higher = MORE dangerous (danger score). Setup classification & colour grading rely on this.

Component normalization is of two kinds:
  - CROSS-SECTIONAL components are ranked by percentile across the universe (leadership is relative).
    Each raw is oriented so a higher raw means more of that score's meaning.
  - CONTEXTUAL Risk components (`regime`, `sector_strength`) are shared macro factors; they are
    normalized DIRECTLY from the canonical 0-100 score they READ ((100 - score)/100 = more danger
    when weaker), never cross-sectionally (a constant across stocks has no peer percentile).
A component needing data absent from the seed (`gap_climax` → earnings) reports NA / available=false
and is excluded from the weighted sum — never fabricated. All bars read through `bars_asof` (no
lookahead). Numeric literals are structural only (0/1/2/4/100); every period/weight is from config.
"""
from __future__ import annotations

from datetime import date as date_cls
from typing import Optional

from sqlmodel import Session, select

from app.config import Config, get_config
from app.engine import indicators as ind
from app.engine.buckets import to_bucket
from app.engine.normalize import cross_sectional_percentiles
from app.engine.patterns import detect_vcp
from app.engine.prices import bars_asof, closes, highs, lows, volumes
from app.engine.regime import score_regime
from app.engine.sectors import score_sectors
from app.engine.setups import classify_setup
from app.engine.themes import basket_return, theme_name, total_return
from app.models import Sector, Stock

# Risk components normalized directly from a canonical score (not cross-sectionally peer-ranked).
CONTEXTUAL_KEYS = {"regime", "sector_strength"}
# Component requiring data absent from the seed (earnings gap) — always NA this session.
NA_KEYS = {"gap_climax"}

# Human labels for the leadership components, used to enrich the setup reason ("top driver").
_DRIVER_LABELS = {
    "rs_spy_1m": "RS vs SPY (1m)",
    "rs_spy_3m": "RS vs SPY (3m)",
    "rs_sector": "RS vs sector",
    "rs_theme": "RS vs theme",
    "ma_stack": "moving-average stack",
    "high_proximity": "proximity to 52-week high",
    "up_down_vol": "volume trend",
}


def _neg(value: Optional[float]) -> Optional[float]:
    return -value if value is not None else None


def _neg_abs(value: Optional[float]) -> Optional[float]:
    return -abs(value) if value is not None else None


def _pct_from_ma(last: Optional[float], ma: Optional[float]) -> Optional[float]:
    """Percent distance of `last` from a moving average `ma` (signed)."""
    if last is None or ma is None or ma == 0:
        return None
    return (last - ma) / ma * 100


def _avg_dollar_volume(series: list[float], vols: list[float], period: int) -> Optional[float]:
    """Mean close*volume over the last `period` bars — a liquidity proxy. NA if too short."""
    if len(series) < period or len(vols) < period:
        return None
    recent = list(zip(series[-period:], vols[-period:]))
    return sum(close * volume for close, volume in recent) / period


def _raw_components(
    session: Session,
    asof: date_cls,
    ticker: str,
    spy_closes: list[float],
    sector_closes: Optional[list[float]],
    sector_score: Optional[float],
    regime_score: float,
    theme_basket_3m: Optional[float],
    cfg: Config,
) -> dict:
    """Oriented raw value per component for one stock (higher raw = more of the score's meaning).
    Contextual keys (`regime`, `sector_strength`) carry the underlying canonical score; `gap_climax`
    is NA (earnings data absent). NA propagates so short-history stocks degrade gracefully."""
    icfg = cfg.indicators
    ma_sorted = sorted(icfg.ma_periods)
    ma_short, ma_mid = ma_sorted[0], ma_sorted[1]  # 20-DMA, 50-DMA from config (not literals)
    window_1m = icfg.rs_windows["1m"]
    window_3m = icfg.rs_windows["3m"]

    bars = bars_asof(session, ticker, asof)
    series = closes(bars)
    vols = volumes(bars)
    hi, lo = highs(bars), lows(bars)
    last = series[-1] if series else None

    rs_1m = ind.rs_vs(series, spy_closes, window_1m)
    rs_3m = ind.rs_vs(series, spy_closes, window_3m)
    rs_sector = ind.rs_vs(series, sector_closes, window_3m) if sector_closes else None
    stock_ret_3m = total_return(series, window_3m)
    rs_theme = (
        stock_ret_3m / theme_basket_3m
        if (stock_ret_3m is not None and theme_basket_3m not in (None, 0))
        else None
    )
    ma_stack = ind.ma_stack(series, icfg.ma_periods)
    dist_high = ind.dist_from_high(series, icfg.high_window_52w)  # <= 0; NA if short history
    vol_trend = ind.vol_trend(vols, icfg.vol_avg_period)
    atr = ind.atr_pct(hi, lo, series, icfg.atr_period)
    dist_from_short = _pct_from_ma(last, ind.sma(series, ma_short))
    dist_from_mid = _pct_from_ma(last, ind.sma(series, ma_mid))
    adv = _avg_dollar_volume(series, vols, icfg.vol_avg_period)
    reward_risk = (abs(dist_high) / atr) if (dist_high is not None and atr not in (None, 0)) else None
    rs_deterioration = (rs_3m - rs_1m) if (rs_1m is not None and rs_3m is not None) else None

    return {
        # leadership (higher = stronger)
        "rs_spy_1m": rs_1m,
        "rs_spy_3m": rs_3m,
        "rs_sector": rs_sector,
        "rs_theme": rs_theme,
        "ma_stack": ma_stack,
        "high_proximity": dist_high,
        "up_down_vol": vol_trend,
        # entry quality (higher = better entry)
        "dist_rising_20": _neg_abs(dist_from_short),
        "contraction": _neg(atr),
        "support_nearby": _neg_abs(dist_from_mid),
        "structure": ma_stack,
        "reward_risk": reward_risk,
        # risk (higher = MORE dangerous)
        "extension": dist_from_mid,
        "atr_pct": atr,
        "liquidity": _neg(adv),
        "regime": regime_score,           # contextual (underlying canonical score)
        "sector_strength": sector_score,  # contextual (underlying canonical score)
        "gap_climax": None,               # NA — earnings data absent this session
        "below_ma": _neg(ma_stack),
        "rs_deterioration": rs_deterioration,
    }


def _build_score(
    ticker: str,
    weights: dict[str, float],
    raws: dict,
    percentiles: dict[str, dict[str, float]],
) -> dict:
    """Assemble one score (0-100 + bucket + components) for a stock from its components' subscores
    in [0,1]: cross-sectional percentile for peer-ranked components, direct (100-score)/100 for
    contextual ones. NA components are excluded from the weighted sum (never fabricated)."""
    rows = []  # (name, raw_for_display, subscore_or_None, weight)
    for name, weight in weights.items():
        if name in NA_KEYS:
            rows.append((name, None, None, weight))
        elif name in CONTEXTUAL_KEYS:
            underlying = raws.get(name)
            subscore = ((100 - underlying) / 100) if underlying is not None else None
            rows.append((name, underlying, subscore, weight))
        else:
            subscore = percentiles[name].get(ticker)
            rows.append((name, raws.get(name), subscore, weight))

    available_weight = sum(weight for _, _, subscore, weight in rows if subscore is not None)
    if available_weight:
        score01 = sum(subscore * weight for _, _, subscore, weight in rows if subscore is not None) / available_weight
    else:
        score01 = 0
    score = round(score01 * 100, 2)

    components = []
    for name, raw, subscore, weight in rows:
        if subscore is None:
            components.append({
                "name": name, "raw": None, "percentile": None,
                "weight": weight, "contribution": None, "available": False,
            })
        else:
            contribution = round((subscore * weight / available_weight) * 100, 2) if available_weight else 0
            components.append({
                "name": name, "raw": round(raw, 4) if raw is not None else None,
                "percentile": round(subscore, 4), "weight": weight,
                "contribution": contribution, "available": True,
            })
    return {"score": score, "components": components}


def _invalidation(basis: str, ma_period: int, level: Optional[float], price: Optional[float]) -> dict:
    """The per-stock invalidation level (where the long thesis is wrong), built ONCE here so the
    human note ships from the backend verbatim (single source — the UI never assembles the "$X"
    string). `level` is the canonical `sma(closes_asof, ma_period)` — the SAME 50-DMA value that
    ends the `/bars` chart series and feeds the scoring extension/support components. Short history
    yields an honest NA note and `level: None`, never a fabricated price (anti-goal: No fabricated data)."""
    if level is None:
        note = "Invalidation level NA — insufficient history"
    else:
        note = f"Invalid below the {basis} at ${level:.2f}"
    return {"basis": basis, "ma_period": ma_period, "level": level, "price": price, "note": note}


def _enriched_reason(base_reason: str, leadership_components: list[dict]) -> str:
    """Append the stock's top leadership driver to the setup reason (reason ← top component + status)."""
    available = [c for c in leadership_components if c["available"]]
    if not available:
        return base_reason
    top = max(available, key=lambda c: c["contribution"])
    return f"{base_reason} Top driver: {_DRIVER_LABELS.get(top['name'], top['name'])}."


def score_stocks(session: Session, asof: date_cls, config: Optional[Config] = None) -> dict:
    """Compute every universe stock's complete canonical record as of `asof`. Deterministic on
    the frozen seed. The ONE producer read by `/api/stocks`, `/api/stocks/{ticker}`, and the
    dashboard's candidate counts — so no view can diverge (single source / J-06)."""
    cfg = config or get_config()
    benchmark = cfg.etfs.index[0]  # SPY
    spy_closes = closes(bars_asof(session, benchmark, asof))
    # invalidation MA basis from config (one of indicators.ma_periods) — no literal in calc code
    inv_period = cfg.decision_rules.invalidation.ma_period
    inv_basis = f"{inv_period}-DMA"

    # canonical macro context — computed ONCE here, never recomputed per stock (single source)
    regime = score_regime(session, asof, cfg)
    regime_score = regime["score"]
    regime_label = regime["label"]
    sector_result = score_sectors(session, asof, cfg)
    sector_score_by_etf = {row["ticker"]: row["score"] for row in sector_result["rows"]}

    # resolve each stock's sector ETF (Stock.sector_id -> Sector.etf_ticker) for rs_sector / sector_strength
    sector_etf_by_id = {s.id: s.etf_ticker for s in session.exec(select(Sector)).all()}
    stock_sector_etf = {
        s.ticker: sector_etf_by_id.get(s.sector_id) for s in session.exec(select(Stock)).all()
    }

    window_3m = cfg.indicators.rs_windows["3m"]
    sector_closes_cache: dict[str, list[float]] = {}

    def sector_closes_for(etf: Optional[str]) -> Optional[list[float]]:
        if etf is None:
            return None
        if etf not in sector_closes_cache:
            sector_closes_cache[etf] = closes(bars_asof(session, etf, asof))
        return sector_closes_cache[etf]

    # primary theme per ticker (first theme in config order that contains it) + its 3m basket return
    theme_basket_3m: dict[str, Optional[float]] = {
        slug: basket_return(session, members, asof, window_3m) for slug, members in cfg.themes.items()
    }
    primary_theme: dict[str, str] = {}
    for slug, members in cfg.themes.items():
        for ticker in members:
            primary_theme.setdefault(ticker, slug)

    # ALL theme memberships per ticker, in config order — the chips on each stock's row. This is
    # the REVERSE of the SAME `config.themes` map `score_themes` ranks (no second theme definition).
    themes_by_ticker: dict[str, list[str]] = {}
    for slug, members in cfg.themes.items():
        for member in members:
            themes_by_ticker.setdefault(member, []).append(slug)

    # pass 1: oriented raw components per stock
    raws_by_ticker: dict[str, dict] = {}
    for ticker in cfg.universe.symbols:
        sector_etf = stock_sector_etf.get(ticker)
        slug = primary_theme.get(ticker)
        raws_by_ticker[ticker] = _raw_components(
            session, asof, ticker, spy_closes,
            sector_closes_for(sector_etf),
            sector_score_by_etf.get(sector_etf),
            regime_score,
            theme_basket_3m.get(slug) if slug else None,
            cfg,
        )

    # pass 2: cross-sectional percentile per cross component (over stocks where it is available)
    all_cross_keys = (
        set(cfg.scores.leadership.weights)
        | set(cfg.scores.entry_quality.weights)
        | set(cfg.scores.risk.weights)
    ) - CONTEXTUAL_KEYS - NA_KEYS
    percentiles: dict[str, dict[str, float]] = {}
    for component in all_cross_keys:
        present = {t: raws[component] for t, raws in raws_by_ticker.items() if raws.get(component) is not None}
        percentiles[component] = cross_sectional_percentiles(present)

    # pass 3: assemble each stock's complete canonical record
    rows: list[dict] = []
    for ticker in cfg.universe.symbols:
        raws = raws_by_ticker[ticker]
        leadership = _build_score(ticker, cfg.scores.leadership.weights, raws, percentiles)
        entry_quality = _build_score(ticker, cfg.scores.entry_quality.weights, raws, percentiles)
        risk = _build_score(ticker, cfg.scores.risk.weights, raws, percentiles)
        for block in (leadership, entry_quality, risk):
            block["bucket"] = to_bucket(block["score"], cfg)

        setup = classify_setup(
            {"leadership": leadership["score"], "entry_quality": entry_quality["score"], "risk": risk["score"]},
            regime_label,
            cfg,
        )
        setup["reason"] = _enriched_reason(setup["reason"], leadership["components"])

        # as-of bars read ONCE (date <= asof, no lookahead), reused for BOTH the invalidation level
        # and the VCP detector — no extra DB round-trip.
        bars = bars_asof(session, ticker, asof)
        inv_closes = closes(bars)
        # invalidation level: the canonical `sma` over the config invalidation period (the level ==
        # the chart's MA-series endpoint).
        invalidation = _invalidation(
            inv_basis, inv_period,
            ind.sma(inv_closes, inv_period),
            inv_closes[-1] if inv_closes else None,
        )
        # VCP flag composed onto the row ALONGSIDE setup/invalidation/themes — a separate detected
        # pattern, NOT a setup status (it never touches `classify_setup` or `setup`). Computed once
        # here from the same as-of bars; stored in `record_json` + mirrored to `ScannerResult.is_vcp`.
        vcp = detect_vcp(inv_closes, highs(bars), lows(bars), volumes(bars), cfg.patterns.vcp)
        themes = [{"slug": slug, "name": theme_name(slug)} for slug in themes_by_ticker.get(ticker, [])]

        rows.append({
            "ticker": ticker,
            "name": ticker,
            "sector": cfg.stock_sectors.get(ticker),
            "leadership": leadership,
            "entry_quality": entry_quality,
            "risk": risk,
            "setup": setup,
            "themes": themes,
            "invalidation": invalidation,
            "vcp": vcp,
            "rank": None,
        })

    # ranked leaderboard: by Leadership descending (tie-break ticker for determinism)
    rows.sort(key=lambda row: (-row["leadership"]["score"], row["ticker"]))
    for index, row in enumerate(rows):
        row["rank"] = index + 1

    return {"asof_date": asof.isoformat(), "benchmark": benchmark, "rows": rows}
