"""Universe screen + single-source/consistency tests (iter-7, J-22).

Two layers:
  * PURE screen predicate (`scripts.screen_universe.screen_reasons`) — the three-threshold screen logic
    that resolves membership at build time. Tested with synthetic candidates: a passer passes; a
    candidate below ANY threshold (price / dollar-volume / market-cap), or with no market cap, is
    EXCLUDED with a reason (the failure path — anti-goal: No fabricated data — never silently kept).
  * SINGLE SOURCE / consistency over the REAL committed seed: the resolved universe size is ONE value,
    read identically by `/api/data` (universe_count), `/api/methodology` (universe_selection.resolved_size),
    and `len(config.universe.symbols)` — no drift, no recompute. When the committed screen record
    (`data/seed/universe.json`) is present, every member's stored reference values pass the screen and the
    stored `Stock.market_cap` equals the committed record (read from storage, never recomputed).
"""
from __future__ import annotations

import json

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.engine.data_manager import compute_coverage
from app.engine.methodology import build_catalog
from app.models import Stock
from app.seed_loader import DEFAULT_SEED_DIR, load_universe_screen_record
from scripts.screen_universe import screen_reasons

_FILTERS = dict(min_price=10.0, min_dollar_vol=50_000_000.0, min_market_cap=2_000_000_000.0)


# --- PURE screen predicate (build-time membership logic) ------------------------------------------
def test_screen_passes_a_qualified_candidate():
    assert screen_reasons(150.0, 9.0e8, 3.0e12, **_FILTERS) == []


def test_screen_excludes_below_min_price():
    reasons = screen_reasons(2.0, 9.0e8, 3.0e9, **_FILTERS)
    assert reasons and any("price" in r for r in reasons)


def test_screen_excludes_below_min_dollar_vol():
    reasons = screen_reasons(50.0, 1.0e6, 3.0e9, **_FILTERS)
    assert reasons and any("adv" in r for r in reasons)


def test_screen_excludes_below_min_market_cap():
    reasons = screen_reasons(50.0, 9.0e8, 1.0e9, **_FILTERS)
    assert reasons and any("market_cap" in r for r in reasons)


def test_screen_excludes_missing_market_cap():
    """A candidate whose market cap could not be fetched is omitted (never fabricated)."""
    assert "no_market_cap" in screen_reasons(50.0, 9.0e8, None, **_FILTERS)


def test_screen_reads_only_passed_thresholds():
    """The same candidate flips pass→fail purely from the config thresholds (the screen reads only
    `universe.filters` — no membership literal baked into the predicate)."""
    assert screen_reasons(12.0, 6.0e7, 3.0e9, **_FILTERS) == []
    strict = dict(min_price=15.0, min_dollar_vol=50_000_000.0, min_market_cap=2_000_000_000.0)
    assert screen_reasons(12.0, 6.0e7, 3.0e9, **strict)  # now excluded by the higher min_price


# --- SINGLE SOURCE / consistency over the committed config + seed --------------------------------
def test_universe_size_is_one_value_across_methodology_and_data(loaded_engine, config):
    """The resolved universe size is read identically by /api/methodology (resolved_size), /api/data
    (universe_count), and len(config.universe.symbols) — one source, no drift (J-22 / no recompute)."""
    resolved = len(config.universe.symbols)
    methodology_size = build_catalog(config)["universe_selection"]["resolved_size"]
    with Session(loaded_engine) as session:
        coverage = compute_coverage(session, config)
    assert methodology_size == resolved
    assert coverage["universe_count"] == resolved
    # universe_count is the screened universe, NOT the distinct priced-symbol count (which includes ETFs)
    assert coverage["symbol_count"] >= resolved


def test_committed_universe_members_all_pass_screen():
    """Every committed universe member passes all three config thresholds against its stored reference
    values (the recorded screen-pass record is internally consistent — no member sneaked in below a
    threshold). Skips only if the expanded seed record has not been built yet."""
    record_path = DEFAULT_SEED_DIR / "universe.json"
    if not record_path.exists():
        pytest.skip("universe.json (committed screen record) not present yet — run screen_universe.py")
    data = json.loads(record_path.read_text())
    filters = load_config().universe.filters
    members = data["members"]
    assert members, "committed universe record has no members"
    offenders = []
    for member in members:
        reasons = screen_reasons(
            member["reference_close"], member["adv_dollar"], member["market_cap"],
            min_price=filters.min_price, min_dollar_vol=filters.min_dollar_vol,
            min_market_cap=filters.min_market_cap,
        )
        if reasons:
            offenders.append((member["symbol"], reasons))
    assert not offenders, f"committed members that fail the screen: {offenders[:10]}"


def test_committed_record_matches_config_universe():
    """The committed screen record's members ARE the config universe (the build wrote both from the one
    resolved set — no drift between the seed record and config.universe.symbols)."""
    record_path = DEFAULT_SEED_DIR / "universe.json"
    if not record_path.exists():
        pytest.skip("universe.json not present yet")
    data = json.loads(record_path.read_text())
    record_symbols = {m["symbol"] for m in data["members"]}
    assert record_symbols == set(load_config().universe.symbols)


def test_stock_market_cap_read_from_committed_record(loaded_engine):
    """`Stock.market_cap` is populated from the committed screen record (read from storage, never
    recomputed in the API/view). Skips only until the record is built."""
    caps = load_universe_screen_record(DEFAULT_SEED_DIR)
    if not caps:
        pytest.skip("no committed market caps yet (universe.json absent)")
    with Session(loaded_engine) as session:
        sample = list(caps.items())[:25]
        for ticker, expected_cap in sample:
            stock = session.scalar(select(Stock).where(Stock.ticker == ticker))
            assert stock is not None, f"{ticker} missing from stocks table"
            assert stock.market_cap == expected_cap, (
                f"{ticker} stored market_cap {stock.market_cap} != committed record {expected_cap}"
            )
