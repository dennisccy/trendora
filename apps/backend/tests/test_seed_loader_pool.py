"""iter-18 (J-12) — the POOL-BROADENED price load.

`seed_loader.load_prices` loads bars for `read_pool(seed_dir) ∪ all_seed_symbols(config)` — the
548-name candidate pool PLUS the existing ETF/^VIX/legend/macro-proxy context set (the union, so no
currently-loaded context symbol is dropped). A pool name with no committed CSV is skipped honestly
(a missing fixture is not a failure — never fabricated). The ordered union lives in the pure
`price_load_symbols` helper so it is unit-testable without a full seed load.
"""
from __future__ import annotations

from pathlib import Path

from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.models import DailyPrice
from app.seed_loader import all_seed_symbols, load_prices, price_load_symbols


def _write_pool(seed_dir: Path, symbols: list[str]) -> None:
    seed_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# test pool", "symbol,sector,source"]
    lines += [f"{s},Technology,test" for s in symbols]
    (seed_dir / "universe_pool.csv").write_text("\n".join(lines) + "\n")


def _write_price_csv(seed_dir: Path, symbol: str, days: int = 3) -> None:
    prices = seed_dir / "prices"
    prices.mkdir(parents=True, exist_ok=True)
    rows = ["date,open,high,low,close,volume"]
    for i in range(days):
        rows.append(f"2024-01-{i + 2:02d},10.0,11.0,9.0,10.5,100")
    (seed_dir / "prices" / f"{symbol}.csv").write_text("\n".join(rows) + "\n")


def test_price_load_symbols_is_context_union_pool_deduped(tmp_path):
    """The ordered load set = all_seed_symbols(config) FIRST (order-preserving — no context symbol
    dropped), then the pool names not already present (pool order), de-duplicated."""
    cfg = load_config()
    seed_dir = tmp_path / "seed"
    # NVDA is already a context (universe) symbol — it must NOT appear twice; AA1/ZZ9 are pool-only.
    _write_pool(seed_dir, ["AA1", "NVDA", "ZZ9"])
    symbols = price_load_symbols(cfg, seed_dir)

    context = all_seed_symbols(cfg)
    assert symbols[: len(context)] == context          # the context prefix is preserved verbatim
    assert symbols[len(context):] == ["AA1", "ZZ9"]    # pool-only names appended in pool order
    assert len(symbols) == len(set(symbols))           # de-duplicated (NVDA appears once)


def test_price_load_symbols_on_the_committed_seed_covers_the_full_pool(seed_dir, config):
    """On the REAL committed seed the load set covers the whole candidate pool AND the whole context
    set — the union the 30-year basis loads (548-pool ∪ 162-context = 588 names)."""
    from app.engine.universe_screen import read_pool

    symbols = price_load_symbols(config, seed_dir)
    pool = {row["symbol"] for row in read_pool(seed_dir)}
    context = set(all_seed_symbols(config))
    assert pool <= set(symbols)
    assert context <= set(symbols)
    assert set(symbols) == pool | context


def test_load_prices_loads_pool_names_and_skips_missing_csvs_honestly(tmp_path):
    """`load_prices` loads a pool-only name's committed bars into daily_prices, and a pool name with
    NO committed CSV is skipped (counted failed) — never fabricated."""
    cfg = load_config()
    seed_dir = tmp_path / "seed"
    _write_pool(seed_dir, ["AA1", "MISSING"])
    _write_price_csv(seed_dir, "AA1", days=3)

    engine = make_engine(f"sqlite:///{tmp_path / 'p.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        ok, failed = load_prices(session, cfg, seed_dir)
        rows = session.exec(select(DailyPrice).where(DailyPrice.symbol == "AA1")).all()
        missing_rows = session.exec(
            select(DailyPrice).where(DailyPrice.symbol == "MISSING")
        ).all()

    # the pool-only name IS loaded (3 committed bars), the CSV-less pool name is skipped honestly
    assert len(rows) == 3
    assert missing_rows == []
    assert ok == 1  # only AA1 has a committed CSV in this synthetic seed dir
    # every OTHER union symbol (the context set + MISSING) has no CSV here → counted failed, not fabricated
    assert failed == len(price_load_symbols(cfg, seed_dir)) - 1
