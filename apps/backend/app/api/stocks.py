"""GET /api/stocks (+ /{ticker}) — the CANONICAL and only endpoint for the per-stock scores
(Data Contract: app.engine.scoring).

iter-8: re-pointed to serve from the persisted IMMUTABLE snapshot for the resolved as-of date
(anti-goal: No recompute in the read path). Both routes resolve `?as_of=` to its stored `ScannerRun`
(latest by default; create-once for a not-yet-stored date) and serve that run's per-stock results
rehydrated from the lossless `record_json`. The list row and the detail row come from the SAME stored
row, so they are byte-identical (anti-goal: Single source of truth -> J-06). Because `run_scan` stored
faithful copies of `score_stocks`, the latest-date payload is byte-identical to the former on-request
compute. `503` when no price data exists, `404` for an unknown ticker, `4xx` for an invalid `as_of` —
never a fabricated row (anti-goal: No fabricated data).

`/stocks/{ticker}/bars` serves the raw price/MA/volume series. Raw bars are NOT a recomputed score, so
the chart endpoint needs no snapshot row — only the as-of slice (`bars_asof`, date <= D, no lookahead)
and the canonical server MA series. It accepts and validates `?as_of=` identically (the as-of chart).
iter-6 (J-20): an opt-in `?through=latest` extends the SAME series DISPLAY-ONLY through the symbol's
latest seed bar (`bars_through_latest`) with an as-of boundary marker (`latest_date` + per-bar
`is_forward`); the post-D bars/MA are visualization only and never feed a score/bucket/VCP — the
default contract (no `through`) stays byte-identical at <= D.

iter-18 (J-10 performance, the 30-year basis): the SAME endpoint gains presentation bounding — no new
endpoint, no new computed value. Ticker validation broadens from `config.universe.symbols` to the
pool-broadened load set (`price_load_symbols` = candidate pool ∪ context set) with a stored-bars
fallback, so a post-swap leaderboard member never 404s its chart. A `?range=` param bounds what is
SHOWN: the default is the trailing `chart_bars.default_years` window before the resolved as-of (the
chart never ships every deep bar by default); `range=full` is the explicit whole-real-history opt-in,
with bars older than `chart_bars.downsample_beyond_years` before the as-of sampled at weekly density.
Every served bar is a REAL stored daily bar (sampling shows fewer bars — it never synthesizes or
aggregates one; the series' real first bar is always kept) and each MA value is the canonical DAILY
`sma_series` value at that bar's position in the FULL series (never recomputed over the sample). The
no-lookahead boundary is untouched in every mode (bars <= D unless the J-20 forward extension is
explicitly requested).
"""
from __future__ import annotations

from datetime import date as date_cls
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, select

from app.config import Config, get_config
from app.db import get_session
from app.engine.indicators import sma_series
from app.engine.prices import bars_asof, bars_through_latest, closes
from app.engine.snapshot_serving import resolved_date, resolved_run, stock_detail_payload, stocks_payload
from app.models import DailyPrice
from app.seed_loader import DEFAULT_SEED_DIR, price_load_symbols

router = APIRouter(tags=["stocks"])

# The two presentation ranges (structural vocabulary, not tunables — the SPANS come from config).
RANGE_DEFAULT = "default"
RANGE_FULL = "full"


@router.get("/stocks")
def stocks(as_of: Optional[str] = None, session: Session = Depends(get_session)) -> dict:
    return stocks_payload(session, resolved_run(session, as_of))


@router.get("/stocks/{ticker}")
def stock_detail(ticker: str, as_of: Optional[str] = None, session: Session = Depends(get_session)) -> dict:
    # the SAME stored row the leaderboard serves — never recomputed per-ticker (J-06)
    return stock_detail_payload(session, resolved_run(session, as_of), ticker)


def _years_before(d: date_cls, years: int) -> date_cls:
    """The calendar date `years` whole years before `d` (Feb-29 snaps to Feb-28) — structural calendar
    arithmetic for the config-driven window bounds; the `years` values themselves come from config."""
    try:
        return d.replace(year=d.year - years)
    except ValueError:  # Feb 29 in a non-leap target year
        return d.replace(year=d.year - years, day=28)


def resolve_servable_symbol(session: Session, ticker: str, cfg: Config) -> str:
    """iter-18 — broadened, case-insensitive ticker validation (shared by the chart endpoint and the
    watchlist add): the pool-broadened load set (`price_load_symbols` — the SAME union `load_prices`
    loads) first, then a stored-bars fallback (any symbol with real committed bars in `daily_prices` is
    honestly servable — raw bars are not a recomputed score). Raises 404 for a truly unknown ticker —
    never a fabricated row. Replaces the retired `config.universe.symbols`-only check so a post-swap
    broadened leaderboard member never 404s its chart or its watchlist add."""
    target = ticker.upper()
    for sym in price_load_symbols(cfg, DEFAULT_SEED_DIR):
        if sym.upper() == target:
            return sym
    stored = session.scalar(
        select(func.count()).select_from(DailyPrice).where(DailyPrice.symbol == target)
    )
    if stored:
        return target
    raise HTTPException(status_code=404, detail=f"unknown ticker: {ticker}")


def _visible_indices(series: list, rng: str, asof: date_cls, cfg: Config) -> tuple[list[int], bool]:
    """The indices of `series` (ascending bars) the response SHOWS for the selected range, plus whether
    deep-region sampling applied. Presentation-bounding only — pure index selection over already-served
    real bars; nothing is synthesized, aggregated, or reordered.

      * RANGE_DEFAULT — the trailing `chart_bars.default_years` window before the as-of. A symbol whose
        data ENDED before that window (a delisted name at a later as-of) falls back to the trailing
        window relative to ITS OWN last bar — real bars, never an empty or fabricated chart.
      * RANGE_FULL — every bar, except that bars older than `chart_bars.downsample_beyond_years` before
        the as-of keep only the LAST bar of each ISO week (weekly sampling; the series' real first bar
        is ALWAYS kept so the displayed first date is the symbol's real first bar)."""
    if rng == RANGE_FULL:
        deep_boundary = _years_before(asof, cfg.chart_bars.downsample_beyond_years)
        idx: list[int] = []
        for i, bar in enumerate(series):
            if bar.date >= deep_boundary:
                idx.append(i)
                continue
            nxt = series[i + 1] if i + 1 < len(series) else None
            # keep the LAST deep-region bar of each ISO week (a real stored daily bar, never a composite)
            if nxt is None or nxt.date >= deep_boundary or nxt.date.isocalendar()[:2] != bar.date.isocalendar()[:2]:
                idx.append(i)
        if idx and idx[0] != 0:
            idx.insert(0, 0)  # the real first bar is always shown (J-10: honest real depth per name)
        return idx, len(idx) < len(series)

    window_start = _years_before(asof, cfg.chart_bars.default_years)
    idx = [i for i, bar in enumerate(series) if bar.date >= window_start]
    if not idx:
        # the series ended before the default window — fall back to ITS OWN trailing window (real bars)
        own_start = _years_before(series[-1].date, cfg.chart_bars.default_years)
        idx = [i for i, bar in enumerate(series) if bar.date >= own_start]
    return idx, False


@router.get("/stocks/{ticker}/bars")
def stock_bars(
    ticker: str,
    as_of: Optional[str] = None,
    through: Optional[str] = None,
    range_: Optional[str] = Query(None, alias="range"),
    session: Session = Depends(get_session),
) -> dict:
    """Canonical price/MA/volume series for the Stock Detail chart, as-of the resolved date. OHLCV bars
    read ONLY via `bars_asof` (date <= as-of, no lookahead) unless the J-20 `?through=latest` display
    extension is explicitly requested; the `ma` map is keyed by every `config.indicators.ma_periods`
    entry and holds the canonical `sma_series` values (computed over the FULL daily series, served
    aligned 1:1 with the visible bars — a number, or `null`/NA where the daily series itself is in its
    warm-up prefix). The frontend plots this server series and never computes a moving average
    client-side. Mirrors the `/api/stocks/{ticker}` contract: `503` when no price data exists, `404`
    for a truly unknown ticker, `4xx` for an invalid `as_of` or `range` — never a fabricated row.

    iter-18 presentation bounding (J-10): `?range=` selects the SHOWN window — `default` (the trailing
    `chart_bars.default_years` before the as-of; the deep basis never ships every bar by default) or
    `full` (the explicit whole-real-history opt-in, weekly-sampled beyond
    `chart_bars.downsample_beyond_years`). The payload discloses `first_available_date` (the symbol's
    REAL first stored bar — honest per-name depth), the echoed `range`, `window_start` (first shown
    bar), and `downsampled`. DISPLAY-ONLY forward extension (J-20): `?through=latest` additionally
    renders the post-as-of path with `latest_date` + per-bar `is_forward`, exactly as before — the
    forward bars never feed a score/bucket/setup/VCP/factor/ranking."""
    cfg = get_config()
    asof = resolved_date(session, as_of, cfg)
    symbol = resolve_servable_symbol(session, ticker, cfg)

    # direct handler-level callers (tests) pass no `range_`, leaving FastAPI's Query default object —
    # only a real string is a caller-selected range; anything else means "default".
    rng = range_ if isinstance(range_, str) and range_ else RANGE_DEFAULT
    if rng not in (RANGE_DEFAULT, RANGE_FULL):
        raise HTTPException(
            status_code=422,
            detail=f"unknown range {rng!r}; expected {RANGE_DEFAULT!r} or {RANGE_FULL!r}",
        )

    full_path = through == "latest"
    series = bars_through_latest(session, symbol) if full_path else bars_asof(session, symbol, asof)
    if not series:
        raise HTTPException(status_code=503, detail=f"no price data for {symbol}")

    # MA is a TRAILING sma_series over the FULL daily series, so each visible value is the canonical
    # daily MA at that date — byte-identical whether or not the window/sample hides neighboring bars,
    # and (J-20) the forward extension never alters the <= D values.
    series_closes = closes(series)
    ma_full = {str(period): sma_series(series_closes, period) for period in cfg.indicators.ma_periods}

    visible, downsampled = _visible_indices(series, rng, asof, cfg)
    bars = [series[i] for i in visible]

    payload = {
        "asof_date": asof.isoformat(),
        "ticker": symbol,
        "range": rng,
        # the symbol's REAL first stored bar — the honest per-name depth (a post-IPO name stays short)
        "first_available_date": series[0].date.isoformat(),
        "window_start": bars[0].date.isoformat(),
        "downsampled": downsampled,
        "bars": [
            {
                "date": bar.date.isoformat(),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
            for bar in bars
        ],
        # one rolling MA series per configured period, aligned 1:1 with the visible bars (each value is
        # the canonical DAILY series value at that bar — no MA literal here; periods come from config)
        "ma": {period: [ma[i] for i in visible] for period, ma in ma_full.items()},
    }
    if full_path:
        # expose the as-of boundary so the chart can shade/label the post-D forward region (display only)
        for bar_payload, bar in zip(payload["bars"], bars):
            bar_payload["is_forward"] = bar.date > asof
        payload["latest_date"] = series[-1].date.isoformat()
    return payload
