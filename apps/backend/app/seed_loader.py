"""Idempotent first-boot seed load.

Populates the reference tables (sectors, stocks, etfs, themes, theme_members) from
`config.yaml` — keeping config the single source for the universe/themes — and loads the
committed frozen price fixture into `daily_prices` via the deterministic `SeedProvider`.
A `data_provider_runs` row records the load. Idempotent: the price load is a no-op once prices
exist; reference data (incl. the `Stock.sector_id` backfill) is ensured every boot via guarded
upserts, so restarting never duplicates.

(The `industries` reference table is created but not populated this iteration — industry-group
scoring lands in iter-2; industry ETFs are still loaded into `etfs` with kind='industry'.)
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import func, insert, select
from sqlalchemy.engine import Engine
from sqlmodel import Session

from app.config import Config, load_config
from app.data_providers.base import ProviderUnavailableError
from app.data_providers.seed_provider import SeedProvider
from app.models import (
    DailyPrice,
    DataProviderRun,
    ETF,
    MacroSeries,
    Sector,
    Stock,
    Theme,
    ThemeMember,
)

# seed_loader.py -> app -> backend
BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SEED_DIR = BACKEND_DIR / "data" / "seed"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def all_seed_symbols(config: Config) -> list[str]:
    """Every symbol that should have a committed price fixture (stocks + ETFs + ^VIX + the J-44
    index-chart legend symbols), de-duplicated and order-preserving.

    The `index_chart.symbols` legend set (J-44) is included so a committed bar fixture for a legend-only
    symbol (e.g. DIA, after its one-shot fetch) is loaded into `daily_prices` and rendered in the chart.
    A legend symbol with NO committed CSV is simply skipped by `load_prices` (a missing fixture is not a
    failure) and stays honestly omitted from the chart — so listing it here never data-gates the boot."""
    symbols: list[str] = []
    symbols += list(config.universe.symbols)
    symbols += list(config.etfs.index)
    symbols += list(config.etfs.sector.keys())
    symbols += list(config.etfs.industry)
    symbols += list(config.etfs.volatility)
    symbols += [entry.symbol for entry in config.index_chart.symbols]  # J-44 legend (DIA, etc.)
    # iter-32 (J-92): the OHLCV macro proxies (^TNX/^DXY/^VXN) ride the EXISTING daily_prices table beside
    # ^VIX (committed seed CSVs). A proxy with no committed CSV is simply skipped by `load_prices` (a
    # missing fixture is not a failure) — so listing them here never data-gates the boot.
    symbols += [s.proxy_symbol for s in config.macro.series if s.proxy_symbol]
    seen: set[str] = set()
    ordered: list[str] = []
    for sym in symbols:
        if sym not in seen:
            seen.add(sym)
            ordered.append(sym)
    return ordered


def load_universe_screen_record(seed_dir: Path) -> dict[str, float]:
    """Read the committed per-member screen-pass record (`universe.json`, written by the offline
    `scripts/screen_universe.py`) → {ticker: market_cap}. The reference market cap is RESOLVED ONCE at
    seed-build time and committed; the loader only READS it (single source / no recompute, J-22). A
    member with no recorded cap, or an absent record, simply yields no entry — `Stock.market_cap` stays
    NULL and is shown as NA, never fabricated (anti-goal: No fabricated data)."""
    path = Path(seed_dir) / "universe.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return {
        member["symbol"]: float(member["market_cap"])
        for member in data.get("members", [])
        if member.get("symbol") and member.get("market_cap") is not None
    }


def load_reference_data(
    session: Session, config: Config, market_caps: Optional[dict[str, float]] = None
) -> None:
    """Insert sectors / stocks / etfs / themes / theme_members from config (idempotent). `market_caps`
    (the committed screen record) populates `Stock.market_cap` read-only (single source); absent ⇒ NULL."""
    caps = market_caps or {}
    # session.scalar(select(Model)) returns the model instance (or None) directly — unlike
    # session.exec(...).first(), which yields a SQLAlchemy Row that the prior tuple-guard didn't
    # unwrap (latent on fresh DBs; surfaced once reference data is ensured on a populated DB).
    sector_id_by_name: dict[str, int] = {}
    for etf_ticker, sector_name in config.etfs.sector.items():
        sector = session.scalar(select(Sector).where(Sector.etf_ticker == etf_ticker))
        if sector is None:
            sector = Sector(name=sector_name, etf_ticker=etf_ticker)
            session.add(sector)
            session.flush()
        sector_id_by_name[sector_name] = sector.id

    stock_id_by_ticker: dict[str, int] = {}
    for ticker in config.universe.symbols:
        # stock -> GICS sector (reference data from config.stock_sectors); used for the
        # rs_sector / sector_strength scoring components (iter-3).
        sector_id = sector_id_by_name.get(config.stock_sectors.get(ticker))
        market_cap = caps.get(ticker)  # committed screen-pass reference cap (None ⇒ NULL/NA)
        stock = session.scalar(select(Stock).where(Stock.ticker == ticker))
        if stock is None:
            stock = Stock(ticker=ticker, name=ticker, sector_id=sector_id,
                          market_cap=market_cap, is_common=True, active=True)
            session.add(stock)
            session.flush()
        else:
            # idempotent backfill from the committed single source for a pre-existing stock row
            if stock.sector_id is None and sector_id is not None:
                stock.sector_id = sector_id
            if market_cap is not None and stock.market_cap != market_cap:
                stock.market_cap = market_cap
            session.add(stock)
        stock_id_by_ticker[ticker] = stock.id

    def add_etf(ticker: str, kind: str, tracks_sector_id: Optional[int] = None, name: Optional[str] = None) -> None:
        if session.scalar(select(ETF).where(ETF.ticker == ticker)) is None:
            session.add(ETF(ticker=ticker, name=name or ticker, kind=kind, tracks_sector_id=tracks_sector_id))

    for ticker in config.etfs.index:
        add_etf(ticker, "index")
    for ticker, sector_name in config.etfs.sector.items():
        add_etf(ticker, "sector", sector_id_by_name.get(sector_name))
    # J-58: `etfs.industry` is now a {ticker: {name, description}} catalog — seed each industry ETF's
    # honest config display name (was the bare ticker). The canonical leaderboard name still comes from
    # the stored SectorScoreRow.name (resolved in score_sectors); this just keeps the ETF table honest.
    for ticker, entry in config.etfs.industry.items():
        add_etf(ticker, "industry", name=entry.name)
    for ticker in config.etfs.volatility:
        add_etf(ticker, "volatility")

    for slug, members in config.themes.items():
        theme = session.scalar(select(Theme).where(Theme.slug == slug))
        if theme is None:
            theme = Theme(slug=slug, name=slug.replace("_", " ").title())
            session.add(theme)
            session.flush()
        for ticker in members:
            stock_id = stock_id_by_ticker.get(ticker)
            if stock_id is None:
                continue
            already = session.scalar(
                select(ThemeMember).where(
                    ThemeMember.theme_id == theme.id, ThemeMember.stock_id == stock_id
                )
            )
            if already is None:
                session.add(ThemeMember(theme_id=theme.id, stock_id=stock_id))

    session.commit()


def load_prices(session: Session, config: Config, seed_dir: Path) -> tuple[int, int]:
    """Bulk-load every symbol's committed bars into daily_prices. Returns (ok, failed)."""
    provider = SeedProvider(seed_dir)
    symbols_ok = 0
    symbols_failed = 0
    for symbol in all_seed_symbols(config):
        try:
            bars = provider.get_daily(symbol)
        except ProviderUnavailableError:
            symbols_failed += 1
            continue
        if not bars:
            symbols_failed += 1
            continue
        rows = [
            {
                "symbol": symbol,
                "date": bar.date,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
            for bar in bars
        ]
        session.execute(insert(DailyPrice.__table__), rows)
        symbols_ok += 1
    session.commit()
    return symbols_ok, symbols_failed


def _price_count(session: Session) -> int:
    return int(session.scalar(select(func.count()).select_from(DailyPrice)) or 0)


def _macro_count(session: Session) -> int:
    return int(session.scalar(select(func.count()).select_from(MacroSeries)) or 0)


def load_macro_seed(session: Session, config: Config, seed_dir: Path) -> int:
    """Load the committed FRED macro seed (iter-32, J-92) into the STANDALONE `macro_series` table from
    `<seed_dir>/macro/<series_id>.csv` (header `date,value`). Idempotent: a no-op once macro rows exist.
    For each configured series the value's `published_date = reference_date + publication_lag_days` (so a
    macro value is usable for a causal date D only when `published_date <= D` — the publication-lag gate;
    using the reference-date value on D is forbidden lookahead). A series with no committed CSV is simply
    skipped (a missing fixture is not a failure — the live FRED pull supplies it, honestly blocked-NA until
    then). Returns the number of rows inserted. The macro proxies (^TNX/^DXY/^VXN) ride `load_prices` via
    `all_seed_symbols` — NOT here (they are plain DailyPrice bars). Macro ships config-default-OFF, so even
    with these rows loaded every J-87..J-91 figure stays byte-identical until a leg is enabled in config."""
    if _macro_count(session) > 0:
        return 0
    import csv

    macro_dir = Path(seed_dir) / "macro"
    inserted = 0
    rows: list[dict] = []
    for series in config.macro.series:
        path = macro_dir / f"{series.id}.csv"
        if not path.exists():
            continue  # no committed fixture for this series — skipped, never fabricated
        with path.open(newline="") as fh:
            reader = csv.DictReader(fh)
            for raw in reader:
                try:
                    ref_date = datetime.strptime(raw["date"], "%Y-%m-%d").date()
                    value = float(raw["value"])
                except (KeyError, ValueError, TypeError):
                    continue  # an unparseable row is skipped, never fabricated
                published = ref_date + timedelta(days=series.publication_lag_days)
                rows.append({
                    "symbol": series.id,
                    "date": ref_date,
                    "value": value,
                    "source": "seed",  # provenance only — NO key value (anti-goal: no secrets in source)
                    "published_date": published,
                })
                inserted += 1
    if rows:
        session.execute(insert(MacroSeries.__table__), rows)
        session.commit()
    return inserted


def load_seed(
    engine: Engine,
    config: Optional[Config] = None,
    seed_dir: Optional[str | Path] = None,
    *,
    force: bool = False,
) -> dict:
    """Load the seed if the DB has no prices (idempotent). Returns a summary dict."""
    config = config or load_config()
    seed_dir = Path(seed_dir) if seed_dir else DEFAULT_SEED_DIR
    with Session(engine) as session:
        existing = _price_count(session)
        # Reference data is idempotent (guarded upserts, no new rows on re-run); ensure it on every
        # boot so a DB created before `stock_sectors` existed gets Stock.sector_id backfilled. Only
        # the PRICE load is gated on emptiness (re-fetching frozen bars would be wasteful). The
        # committed screen record (universe.json) populates Stock.market_cap read-only (J-22).
        load_reference_data(session, config, load_universe_screen_record(seed_dir))
        # iter-32 (J-92): ensure the committed macro seed on every boot (idempotent — a no-op once macro
        # rows exist), so the macro-conditioned features are buildable + testable OFFLINE. Macro ships
        # config-default-OFF, so loading it changes NO J-87..J-91 figure until a leg is enabled in config.
        load_macro_seed(session, config, seed_dir)
        if existing and not force:
            return {"loaded": False, "reason": "already populated", "price_rows": existing}

        started = _utcnow()
        symbols_ok, symbols_failed = load_prices(session, config, seed_dir)
        status = "ok" if symbols_failed == 0 else ("failed" if symbols_ok == 0 else "partial")
        session.add(
            DataProviderRun(
                provider=config.provider,
                started_at=started,
                finished_at=_utcnow(),
                symbols_ok=symbols_ok,
                symbols_failed=symbols_failed,
                status=status,
                message=f"seed load: {symbols_ok} symbols ok, {symbols_failed} failed",
            )
        )
        session.commit()
        return {
            "loaded": True,
            "symbols_ok": symbols_ok,
            "symbols_failed": symbols_failed,
            "status": status,
            "price_rows": _price_count(session),
        }
