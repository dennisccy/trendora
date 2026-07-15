"""app.engine.watchlist_xray — the watchlist concentration X-ray composer (goal-mcp-loop iter-38,
J-23 / backlog B-204).

`build_xray_payload(session, cfg, tickers, asof)` is a PURE-COMPOSITION read: it re-reads price bars
via the bounded `app.engine.prices.bars_asof_window` (bars <= as-of, NEVER a whole-table load) and the
SAME canonical snapshot rows `GET /api/stocks` serves (`app.engine.snapshot_serving.filtered_stock_rows`),
and composes them with the ONE canonical ENB/correlation helper (`app.engine.concentration`) into the
additive `xray` field `GET /api/watchlist` attaches to its EXISTING response. It recomputes NO
already-registered value — sector / themes / setup status are read verbatim from the canonical row;
price history goes through the SAME bounded accessor every other bounded reader uses; setup counts
reuse `app.engine.setups.summarize_candidates` (the dashboard's own candidate-count tally) rather than
a second tally.

Honesty floor: a ticker whose OWN trailing return series (over `watchlist.xray.corr_window_days`) has
fewer than `watchlist.xray.min_overlap_days` observations is excluded from every correlation/cluster/
ENB computation — its row/column in the served matrix is `None` throughout (never a fabricated
correlation). `effective_number_of_bets` is computed over the "honest sub-matrix": only tickers whose
correlation against EVERY OTHER included ticker is defined (this also excludes a zero-variance series).

Sector concentration groups by the RAW stored `sector` (including `None`) — it does NOT bucket a null
sector to a literal "Unassigned" string here; that display mapping is the EXISTING frontend
`sectorLabel()` helper's job (`lib/sector-label.ts`, the single place that maps null -> "Unassigned",
iter-19). This module only guarantees the null-sector group is counted like any other, never dropped,
never a crash.

Fewer than 2 watchlist tickers -> `status: "insufficient"` (a correlation view needs at least a pair);
every list/matrix field is empty and no price/snapshot read is attempted.
"""
from __future__ import annotations

from datetime import date as date_cls
from typing import Iterable, Optional

from sqlmodel import Session

from app.config import Config
from app.engine.concentration import correlation_matrix, effective_number_of_bets
from app.engine.prices import bars_asof_window, closes
from app.engine.setups import ALL_STATUSES, summarize_candidates
from app.engine.snapshot_serving import filtered_stock_rows, resolved_run

# A correlation view is only meaningful with at least a pair — not a config tunable, a mathematical floor.
_MIN_TICKERS_FOR_MATRIX = 2


def _returns(closes_: list[float]) -> list[float]:
    """Day-over-day simple returns, ascending — one entry shorter than the input close series. A
    non-positive prior close (impossible for real equity data, but defended against so a corrupt/odd
    bar never raises a division error — anti-goal: never crash on a data-shape surprise) is honestly
    skipped rather than fabricating a return."""
    out: list[float] = []
    for i in range(1, len(closes_)):
        prior = closes_[i - 1]
        if prior and prior > 0:
            out.append(closes_[i] / prior - 1)
    return out


def _connected_components(
    tickers: list[str], matrix: dict[str, dict[str, Optional[float]]], threshold: float
) -> list[list[str]]:
    """Deterministic correlation-threshold clustering (connected components; no ML — B-204). An edge
    joins two DIFFERENT tickers when their correlation is defined and `>= threshold` (POSITIVE
    correlation only — the concentration risk this X-ray discloses is names moving TOGETHER; a strongly
    negative correlation is diversifying, not concentrating). A ticker with no qualifying edge
    (including every NA/insufficient-history ticker) is its own singleton cluster. Clusters and their
    members are sorted for a fully deterministic, byte-identical output regardless of input order."""
    parent = {t: t for t in tickers}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i, a in enumerate(tickers):
        for b in tickers[i + 1 :]:
            corr = matrix[a][b]
            if corr is not None and corr >= threshold:
                union(a, b)

    groups: dict[str, list[str]] = {}
    for t in tickers:
        groups.setdefault(find(t), []).append(t)
    clusters = [sorted(members) for members in groups.values()]
    clusters.sort(key=lambda members: members[0])
    return clusters


def _sector_concentration(canonical_rows: dict[str, dict], tickers: list[str]) -> list[dict]:
    """Sector concentration over the watchlist's OWN tickers, grouped by the raw stored `sector`
    (nullable, single-valued — every ticker contributes to exactly one bucket, so `pct` always sums to
    1.0 across the returned entries). A missing canonical row (defensive — should not happen for a
    validated watchlist entry) degrades to the same null-sector bucket, never a crash."""
    total = len(tickers)
    counts: dict[Optional[str], int] = {}
    for ticker in tickers:
        row = canonical_rows.get(ticker)
        sector = row["sector"] if row else None
        counts[sector] = counts.get(sector, 0) + 1
    entries = [{"sector": sector, "count": count, "pct": count / total} for sector, count in counts.items()]
    # Deterministic order: highest count first; the null-sector bucket sorts after every named sector
    # (the `sector is None` boolean sorts True-after-False), then alphabetically among ties.
    entries.sort(key=lambda e: (-e["count"], e["sector"] is None, e["sector"] or ""))
    return entries


def _theme_concentration(canonical_rows: dict[str, dict], tickers: list[str]) -> list[dict]:
    """Theme concentration over the watchlist's OWN tickers. A stock may carry zero, one, or several
    themes (multi-membership, unlike sector) — `pct` is share-of-watchlist per theme, NOT a partition
    (entries need not sum to 100%). Only themes with >= 1 watchlist member are listed (the full theme
    catalog is not restated here)."""
    total = len(tickers)
    counts: dict[str, dict] = {}
    for ticker in tickers:
        row = canonical_rows.get(ticker)
        if not row:
            continue
        for theme in row.get("themes") or []:
            entry = counts.setdefault(theme["slug"], {"name": theme["name"], "count": 0})
            entry["count"] += 1
    entries = [
        {"slug": slug, "name": v["name"], "count": v["count"], "pct": v["count"] / total}
        for slug, v in counts.items()
    ]
    entries.sort(key=lambda e: (-e["count"], e["slug"]))
    return entries


def _setup_concentration(canonical_rows: dict[str, dict], tickers: list[str]) -> list[dict]:
    """Shared-setup count: how many watchlist names currently classify to each of the six canonical
    setup statuses (`app.engine.setups`), reusing the SAME `summarize_candidates` the dashboard's
    candidate counts use — never a second setup-status tally. Always all six statuses (0 where absent),
    mirroring `summarize_candidates`'s own "a number always renders" contract."""
    total = len(tickers)
    rows = [canonical_rows[t] for t in tickers if t in canonical_rows]
    counts = summarize_candidates(rows)
    return [
        {"status": status, "count": counts[status], "pct": counts[status] / total} for status in ALL_STATUSES
    ]


def _insufficient_payload(cfg: Config, tickers: list[str]) -> dict:
    xray_cfg = cfg.watchlist.xray
    return {
        "status": "insufficient",
        "window_days": xray_cfg.corr_window_days,
        "min_overlap_days": xray_cfg.min_overlap_days,
        "cluster_threshold": xray_cfg.cluster_threshold,
        "tickers": tickers,
        "history_days": {},
        "correlation_matrix": {},
        "clusters": [],
        "effective_number_of_bets": None,
        "enb_member_count": 0,
        "sector_concentration": [],
        "theme_concentration": [],
        "setup_concentration": [],
    }


def build_xray_payload(session: Session, cfg: Config, tickers: Iterable[str], asof: date_cls) -> dict:
    """The additive `xray` field `GET /api/watchlist` attaches to its existing response — see the
    module docstring for the full contract. `tickers` may be given in any order; the response is always
    deterministically sorted regardless (byte-identical across repeated calls with the same inputs)."""
    ticker_list = sorted({t for t in tickers if t})
    xray_cfg = cfg.watchlist.xray
    if len(ticker_list) < _MIN_TICKERS_FOR_MATRIX:
        return _insufficient_payload(cfg, ticker_list)

    # Bounded per-symbol reads (bars <= as-of, trailing corr_window_days) — never a whole-table load.
    history_days: dict[str, int] = {}
    returns_by_ticker: dict[str, list[float]] = {}
    for ticker in ticker_list:
        bars = bars_asof_window(session, ticker, asof, xray_cfg.corr_window_days)
        returns = _returns(closes(bars))
        history_days[ticker] = len(returns)
        returns_by_ticker[ticker] = returns

    # The honesty floor: only tickers with enough OWN history enter the correlation computation.
    sufficient = [t for t in ticker_list if history_days[t] >= xray_cfg.min_overlap_days]
    series_by_name = {t: returns_by_ticker[t] for t in sufficient}
    sub_matrix = correlation_matrix(series_by_name) if series_by_name else {}

    # Compose the FULL matrix over every watchlist ticker; any cell touching an insufficient-history
    # ticker (or a zero-variance pair `correlation_matrix` itself flagged) is honestly None.
    full_matrix: dict[str, dict[str, Optional[float]]] = {
        a: {b: sub_matrix.get(a, {}).get(b) for b in ticker_list} for a in ticker_list
    }

    clusters = _connected_components(ticker_list, full_matrix, xray_cfg.cluster_threshold)

    # The "honest sub-matrix" for ENB: sufficient tickers whose correlation against every OTHER
    # sufficient ticker is defined (excludes a zero-variance series, which `correlation_matrix` already
    # marked None throughout its row/column).
    enb_eligible = [t for t in sufficient if all(full_matrix[t][o] is not None for o in sufficient)]
    enb = None
    if enb_eligible:
        ordered = sorted(enb_eligible)
        enb_matrix = [[full_matrix[a][b] for b in ordered] for a in ordered]
        enb = effective_number_of_bets(enb_matrix)

    # Sector / theme / setup concentration read the SAME canonical rows GET /api/stocks serves —
    # recomputes no score/sector/setup/theme value.
    run = resolved_run(session, None, cfg)
    canonical_rows = {row["ticker"]: row for row in filtered_stock_rows(session, run, ticker_list, cfg)}

    return {
        "status": "ok",
        "window_days": xray_cfg.corr_window_days,
        "min_overlap_days": xray_cfg.min_overlap_days,
        "cluster_threshold": xray_cfg.cluster_threshold,
        "tickers": ticker_list,
        "history_days": history_days,
        "correlation_matrix": full_matrix,
        "clusters": clusters,
        "effective_number_of_bets": enb,
        "enb_member_count": len(enb_eligible),
        "sector_concentration": _sector_concentration(canonical_rows, ticker_list),
        "theme_concentration": _theme_concentration(canonical_rows, ticker_list),
        "setup_concentration": _setup_concentration(canonical_rows, ticker_list),
    }
