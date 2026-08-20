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
from collections.abc import Iterable, Mapping
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


# J-95(b): the candidate pool's EXPLICIT survivorship-bias caveat. The committed `universe_pool.csv`
# is a CURRENT-constituent listing (today's S&P 500 ∪ Nasdaq-100 ∪ prior universe) — NOT an as-of-date
# constituent set. A true point-in-time index-membership feed is offered only as a data-dependent,
# non-halting enhancement and is NEVER faked; when absent the pool stays this documented current-
# constituent listing with this honest label, and the as-of-dependent membership (J-93) is screened
# from it. This caveat is served verbatim beside the membership timeline (no re-typed copy in the UI).
POOL_SURVIVORSHIP_LABEL = (
    "Candidate pool = CURRENT index constituents (today's S&P 500 ∪ Nasdaq-100 ∪ the prior committed "
    "universe), not as-of-date constituents. The point-in-time resolver REDUCES survivorship bias by "
    "admitting a name only once it has the required history/price/liquidity from bars on or before each "
    "date, but residual pool-survivorship remains: a name delisted before today is not in this pool. A "
    "true point-in-time index-membership feed would remove that residual; it is a data-dependent "
    "enhancement and is never fabricated."
)


def pool_survivorship(seed_dir: Path | None = None) -> dict:
    """J-95(b): the candidate pool's honest survivorship descriptor served on the coverage surface — the
    explicit current-constituent caveat + the pool size + whether a true point-in-time constituent feed
    is present (always False here — it is the data-walled enhancement, never faked). Read-only; no key."""
    try:
        pool = read_pool(seed_dir)
        pool_count = len({row["symbol"] for row in pool})
    except FileNotFoundError:
        pool_count = 0
    return {
        "label": POOL_SURVIVORSHIP_LABEL,
        "basis": "current_constituent",  # not as_of_date_constituent
        "pool_count": pool_count,
        # the true point-in-time index-membership feed is the data-dependent, non-halting J-95 enhancement.
        # It is NEVER fabricated; absent → the pool stays the documented current-constituent listing.
        "point_in_time_feed_available": False,
    }


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


# --- J-01 (goal-market-compass iter-1): the pool-CSV sector fallback ------------------------------
# `scoring.score_stocks` reads `cfg.stock_sectors` FIRST (the curated 122-name mapping — untouched by
# this module) and falls back to `pool_sector_map`'s result only when a resolved-at-D member has no
# curated entry. Both helpers read NO config of their own (mirrors `screen_reasons` above) — the
# caller passes the resolved `universe.pool_sector_aliases` / `etfs.sector` values, so this module
# stays a pure normalization seam, never a second config reader.

def resolve_pool_sector(
    raw_sector: str | None, *, aliases: Mapping[str, str], valid_sectors: Iterable[str]
) -> str | None:
    """Normalize ONE `universe_pool.csv` raw sector name through the caller's alias map (identity
    today — no alias entry resolves anything yet) and validate the normalized name is a member of the
    caller's valid sector set (`etfs.sector`'s values). A missing/blank raw sector, or one that fails
    alias+validity resolution, returns `None` — never raises, never a fabricated or stray sector
    string (AG-8 resilience; honesty: NA over fabrication)."""
    if not raw_sector:
        return None
    normalized = aliases.get(raw_sector, raw_sector)
    return normalized if normalized in set(valid_sectors) else None


def pool_sector_map(
    *, aliases: Mapping[str, str], valid_sectors: Iterable[str], seed_dir: Path | None = None
) -> dict[str, str]:
    """Ticker -> resolved pool-CSV sector, built ONCE from the SAME `read_pool()` parser (never a
    second CSV reader) — the pool-CSV fallback half of J-01's two-source sector basis. Only tickers
    that resolve to a valid sector are present; an unresolvable or missing pool sector is simply
    absent (the caller's `.get(ticker)` then honestly returns `None` — never a fabricated value). A
    not-yet-built pool (`FileNotFoundError`) degrades to an empty map, the same honest-empty contract
    `read_pool`'s other callers already tolerate."""
    try:
        pool = read_pool(seed_dir)
    except FileNotFoundError:
        return {}
    out: dict[str, str] = {}
    for row in pool:
        resolved = resolve_pool_sector(row.get("sector"), aliases=aliases, valid_sectors=valid_sectors)
        if resolved is not None:
            out[row["symbol"]] = resolved
    return out
