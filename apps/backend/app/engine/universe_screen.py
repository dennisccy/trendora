"""The pure universe-screen predicate + candidate-pool reader — the SINGLE source of the membership
threshold rule (J-22 / J-35).

This module holds the ONE definition of `screen_reasons`: the three-threshold liquidity/price/market-cap
screen that decides whether a candidate becomes a universe member. It is imported by BOTH the offline
one-shot runbook (`scripts/screen_universe.py`, which re-exports it) AND the on-demand `expand` job
(`app.engine.data_manager`) — so there is never a second copy of the rule (anti-goal: No magic numbers —
the threshold rule lives in ONE place and reads ONLY the passed-in `config.universe.filters` values).

It computes NO score/return and reads NO config of its own — the caller passes the resolved
`universe.filters` thresholds. The pool reader (`read_pool`) reads the committed, documented candidate
pool `data/seed/universe_pool.csv` (the membership-rule half of the screen — a transparent index listing,
NOT a hand-picked list).
"""
from __future__ import annotations

import csv
from pathlib import Path

# app/engine/universe_screen.py -> app/engine -> app -> backend ; the committed pool lives under data/seed.
BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SEED_DIR = BACKEND_DIR / "data" / "seed"
POOL_CSV_NAME = "universe_pool.csv"


def screen_reasons(
    reference_close: float | None,
    adv_dollar: float | None,
    market_cap: float | None,
    *,
    min_price: float,
    min_dollar_vol: float,
    min_market_cap: float,
) -> list[str]:
    """Pure screen predicate: the list of reasons a candidate FAILS the three config thresholds. An
    empty list == passes. A missing market cap is a failure ("no_market_cap") — the candidate is omitted,
    never fabricated. Reads ONLY the passed-in `universe.filters` values (no membership literal baked in
    here — the single source of the threshold rule, anti-goal: No magic numbers / No fabricated data)."""
    reasons: list[str] = []
    if market_cap is None:
        reasons.append("no_market_cap")
    elif market_cap < min_market_cap:
        reasons.append(f"market_cap {market_cap:.0f} < {min_market_cap:.0f}")
    if reference_close is None or reference_close < min_price:
        reasons.append(f"price {reference_close} < {min_price}")
    if adv_dollar is None or adv_dollar < min_dollar_vol:
        reasons.append(f"adv {adv_dollar} < {min_dollar_vol:.0f}")
    return reasons


def read_pool(seed_dir: Path | None = None) -> list[dict]:
    """Read the committed, documented candidate pool (`universe_pool.csv`) → a list of
    `{symbol, sector, source}` dicts (comment lines stripped). This is the membership-rule half of the
    screen (a transparent S&P 500 ∪ Nasdaq-100 ∪ prior-universe listing) the `expand` job screens against.
    Raises `FileNotFoundError` when the pool has not been built/committed yet (the caller surfaces it as an
    explicit job error — never a fabricated pool)."""
    path = Path(seed_dir or DEFAULT_SEED_DIR) / POOL_CSV_NAME
    if not path.exists():
        raise FileNotFoundError(
            f"candidate pool not found: {path} — run scripts/screen_universe.py --build-pool first"
        )
    out: list[dict] = []
    with path.open(newline="") as fh:
        for row in csv.DictReader(line for line in fh if not line.startswith("#")):
            if row.get("symbol"):
                out.append({"symbol": row["symbol"], "sector": row.get("sector"), "source": row.get("source")})
    return out
