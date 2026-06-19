"""The per-as-of-date point-in-time universe resolver (J-93 / J-94) — the SINGLE source of "which
candidate names are universe MEMBERS as of a date D".

This is the keystone of the dynamic, point-in-time universe. For a given as-of date D it reads the
committed candidate pool (`universe_screen.read_pool`) and admits each candidate that, **from bars
dated <= D only** (`prices.bars_asof`, the backward no-lookahead boundary), clears THREE config gates:

  1. trailing-bar count  >= `indicators.min_history_bars`  (the J-94 minimum-history / warm-up gate),
  2. as-of close (bars[-1].close) >= `universe.filters.min_price`,
  3. average daily dollar volume over `universe.filters.adv_window_days`
     (the SAME measure the offline `expand` screen uses: mean of close*volume over the trailing
     window) >= `universe.filters.min_dollar_vol`.

The **market-cap criterion is DROPPED** from the per-date screen. Market cap is a current-only scalar
with no committed point-in-time series; applying it per-historical-date would be lookahead-or-
fabrication. The candidate pool is still BUILT by the market-cap-gated offline screen
(`universe_screen.screen_reasons` / the `expand` job — that is where `config.universe.symbols` comes
from); this resolver then screens THAT pool on the three point-in-time-safe criteria.

No magic numbers: every cutoff is sourced from the passed `Config` (added to
`test_no_magic_numbers.CALC_FILES`). The only literals here are structural (0/1 indexing, the empty
shortcut). No score/return/bucket is computed — only membership-at-D is resolved.

No lookahead (anti-goal, unit-asserted by tail-invariance): admission at D reads ONLY `bars_asof`
(date <= D). Removing any bar dated > D never changes D's resolved members — exactly the property the
`forward_return` tail-invariance test asserts.

The resolved member set IS the set `scoring.score_stocks` iterates, and the persisted `ScannerResult`
rows for the run ARE the membership (single source of truth; no second universe computation, no read-
path recompute). The per-date coverage diagnostic (`data_manager`) calls `resolve_with_reasons` to
report the admitted count + the excluded-by-reason counts against the candidate-pool denominator.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_cls
from typing import Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.config import Config, get_config
from app.engine.prices import active_bar_cache, bars_asof
from app.engine.universe_screen import read_pool
from app.models import DailyPrice

# The excluded-by-reason vocabulary (string labels, not tunables) — reused by the J-94 coverage
# diagnostic and the J-96 membership timeline. Aligned with the existing coverage vocabulary
# (`no_history`/`thin`) so the UI speaks one language.
REASON_BELOW_HISTORY = "below_history"  # < indicators.min_history_bars trailing bars (incl. zero bars)
REASON_BELOW_PRICE = "below_price"      # as-of close < universe.filters.min_price
REASON_BELOW_ADV = "below_adv"          # trailing ADV$ < universe.filters.min_dollar_vol
EXCLUSION_REASONS = (REASON_BELOW_HISTORY, REASON_BELOW_PRICE, REASON_BELOW_ADV)


@dataclass(frozen=True)
class CandidateResolution:
    """One candidate's point-in-time resolution at D: `admitted` plus, when excluded, the FIRST gate it
    failed (history -> price -> ADV, evaluated in that order). `bars` is the trailing-bar count read
    from bars <= D (descriptive — never fabricated)."""

    symbol: str
    admitted: bool
    reason: Optional[str]  # None when admitted; one of EXCLUSION_REASONS otherwise
    bars: int


def _adv_dollar(bars: list, adv_window_days: int) -> Optional[float]:
    """Average daily dollar volume over the trailing `adv_window_days` bars — the SAME liquidity
    measure the offline screen computes (`mean(close*volume)` over the window). None when no usable
    bar exists. Reads ONLY the passed bars (date <= D); introduces no threshold literal."""
    window = bars[-adv_window_days:]
    pairs = [b.close * b.volume for b in window if b.close is not None and b.volume is not None]
    if not pairs:
        return None
    return sum(pairs) / len(pairs)


def resolve_candidate(bars: list, symbol: str, cfg: Config) -> CandidateResolution:
    """Resolve ONE candidate from its already-fetched bars-as-of-D list (ascending, date <= D). Pure:
    no DB access, no config of its own beyond the passed `cfg`. The gates are checked in a fixed order
    (history -> price -> ADV) so the recorded `reason` is the FIRST unmet criterion (deterministic)."""
    filters = cfg.universe.filters
    min_history = cfg.indicators.min_history_bars
    bar_count = len(bars)

    if bar_count < min_history:
        return CandidateResolution(symbol, False, REASON_BELOW_HISTORY, bar_count)

    last_close = bars[-1].close
    if last_close is None or last_close < filters.min_price:
        return CandidateResolution(symbol, False, REASON_BELOW_PRICE, bar_count)

    adv = _adv_dollar(bars, filters.adv_window_days)
    if adv is None or adv < filters.min_dollar_vol:
        return CandidateResolution(symbol, False, REASON_BELOW_ADV, bar_count)

    return CandidateResolution(symbol, True, None, bar_count)


def resolve_with_reasons(
    session: Session,
    asof: date_cls,
    config: Optional[Config] = None,
    *,
    seed_dir=None,
) -> dict:
    """Resolve the full candidate pool at `asof` → the descriptive resolution the J-94 diagnostic /
    J-96 timeline serve:

      {
        "asof": "YYYY-MM-DD",
        "candidate_pool_count": <int>,         # the committed pool size (the denominator)
        "admitted": [<symbol>, ...],           # the resolved members at D (alphabetical)
        "admitted_count": <int>,
        "excluded_counts": {below_history, below_price, below_adv},
        "resolutions": [CandidateResolution-as-dict, ...]  # one per pool candidate, alphabetical
      }

    Reads ONLY `bars_asof` (date <= D) per candidate — no lookahead. Recomputes no score/return; this
    is descriptive membership metadata over the stored bars + config thresholds."""
    cfg = config or get_config()
    pool = read_pool(seed_dir)
    symbols = sorted({row["symbol"] for row in pool})
    min_history = cfg.indicators.min_history_bars

    # PERFORMANCE: the trailing-bar count (date <= asof) per priced symbol — only a symbol that clears
    # the history gate can possibly be admitted, so we fetch the FULL bar list (for the price/ADV check)
    # ONLY for those; the (often hundreds of) un-fetched pool names are trivially `below_history` from the
    # count alone (no per-symbol full-series query). Byte-identical to resolving each candidate
    # individually (the same gate order, the same admission), just far cheaper.
    #
    # iter-36 (J-96 cold-miss bound): when a `bar_cache`/`prefilled_bar_cache` context is active (the
    # multi-date membership-timeline derivation runs inside one), source the count from the ONCE-loaded
    # series via `trailing_count` — eliminating ONE grouped-count DB round-trip PER DATE (the O(dates)
    # cost that made the cold `GET /api/data` hang). `trailing_count` is byte-identical to the grouped
    # count (the `(symbol, date)` unique constraint means the bisect equals the row count exactly), so the
    # admitted/excluded results are unchanged. With NO active context (the default per-request resolve)
    # the original grouped-count query runs — that path is completely unchanged / byte-identical.
    cache = active_bar_cache(session)
    if cache is not None:
        bar_count_by_symbol = {sym: cache.trailing_count(session, sym, asof) for sym in symbols}
    else:
        counts_rows = session.exec(
            select(DailyPrice.symbol, func.count(DailyPrice.id))
            .where(DailyPrice.symbol.in_(symbols))
            .where(DailyPrice.date <= asof)
            .group_by(DailyPrice.symbol)
        ).all()
        bar_count_by_symbol = {sym: int(n or 0) for sym, n in counts_rows}

    resolutions: list[CandidateResolution] = []
    for symbol in symbols:
        bar_count = bar_count_by_symbol.get(symbol, 0)
        if bar_count < min_history:
            # below the history gate — the first gate; no need to materialize the full series.
            resolutions.append(
                CandidateResolution(symbol, False, REASON_BELOW_HISTORY, bar_count)
            )
            continue
        bars = bars_asof(session, symbol, asof)
        resolutions.append(resolve_candidate(bars, symbol, cfg))

    admitted = sorted(r.symbol for r in resolutions if r.admitted)
    excluded_counts = {reason: 0 for reason in EXCLUSION_REASONS}
    for r in resolutions:
        if r.reason is not None:
            excluded_counts[r.reason] += 1

    return {
        "asof": asof.isoformat(),
        "candidate_pool_count": len(symbols),
        "admitted": admitted,
        "admitted_count": len(admitted),
        "excluded_counts": excluded_counts,
        "resolutions": [
            {"symbol": r.symbol, "admitted": r.admitted, "reason": r.reason, "bars": r.bars}
            for r in resolutions
        ],
    }


def resolve_members(
    session: Session,
    asof: date_cls,
    config: Optional[Config] = None,
    *,
    seed_dir=None,
) -> list[str]:
    """The resolved universe MEMBERS at `asof` — the alphabetical list of candidates that clear all
    three point-in-time gates from bars <= D. This is the SINGLE membership set `scoring.score_stocks`
    iterates (the persisted `ScannerResult` rows for the run ARE this membership). An early date before
    the warm-up boundary honestly returns a small/empty list (no fabricated members)."""
    return resolve_with_reasons(session, asof, config, seed_dir=seed_dir)["admitted"]
