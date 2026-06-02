"""One-shot, offline, DEV-RUN-ONCE universe screen + seed ingest (J-22). NOT on the boot/request path.

Replaces the hand-curated universe with a TRANSPARENT, REPRODUCIBLE, config-recorded screen over a
documented candidate pool of real US large/mid-cap index memberships. Two phases, both producing
COMMITTED artifacts the running app only READS (single source of truth; the request path never
recomputes membership or market cap):

  --build-pool : fetch the REAL constituents of the S&P 500 and the Nasdaq-100 from Wikipedia (each
                 table carries the ticker AND its GICS sector), union them with the prior committed
                 universe (so existing themed names remain candidates), and write the documented,
                 frozen candidate pool to `data/seed/universe_pool.csv` (symbol, sector, source).
                 This is the "membership rule" half of the screen — a transparent index listing, NOT a
                 hand-picked stock list. Run once; commit the CSV.

  --screen     : (default) read the committed pool, fetch REAL EOD OHLCV (Yahoo chart API, no key) AND
                 a REAL market cap (Yahoo quote API via the no-key cookie+crumb flow) for every
                 candidate, then APPLY the config screen from `universe.filters`
                 (min_price / min_dollar_vol / min_market_cap). Only passers (~400-500) become the
                 universe. A candidate that fails to fetch, returns an empty/partial series, lacks a
                 market cap, or fails any threshold is LOGGED and OMITTED — never fabricated (the CYBR
                 precedent). The ETFs + ^VIX are benchmarks: fetched, never screened. Writes the frozen
                 per-symbol price CSVs, the per-member screen-pass record `data/seed/universe.json`, and
                 refreshes `data/seed/meta.json` honestly. Run once; commit the output.

SOURCE NOTE (documented, no secret): OHLCV + market cap come from Yahoo's FREE, NO-KEY endpoints
(`query1.finance.yahoo.com/v8/finance/chart` for bars; `/v7/finance/quote` via the cookie+crumb flow
for `marketCap`). GICS sector comes from Wikipedia's index-constituent tables. No API key is used or
committed; the crumb is fetched at runtime, never stored. All data is REAL; nothing is fabricated.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/screen_universe.py --build-pool
    apps/backend/.venv/bin/python apps/backend/scripts/screen_universe.py            # --screen
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
SEED_DIR = BACKEND_DIR / "data" / "seed"
PRICES_DIR = SEED_DIR / "prices"
POOL_CSV = SEED_DIR / "universe_pool.csv"
UNIVERSE_JSON = SEED_DIR / "universe.json"

sys.path.insert(0, str(BACKEND_DIR))
from app.config import load_config  # noqa: E402
from app.data_providers.seed_provider import symbol_to_filename  # noqa: E402

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"
CRUMB_URL = "https://query1.finance.yahoo.com/v1/test/getcrumb"
COOKIE_URL = "https://finance.yahoo.com/"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
HEADERS = {"User-Agent": UA, "Accept": "application/json,text/plain,*/*", "Accept-Language": "en-US,en;q=0.9"}
WIKI_HEADERS = {"User-Agent": "trendora-seed-build/1.0 (research; offline seed; contact: dev@trendora.local)"}
ET = ZoneInfo("America/New_York")

# Wikipedia sector label -> the config `etfs.sector` name. The S&P 500 table uses GICS sector names
# ("Information Technology" -> the config's "Technology"/XLK; the other 10 match verbatim). The
# Nasdaq-100 table uses ICB Industry labels ("Technology", "Basic Materials" -> "Materials",
# "Telecommunications" -> "Communication Services"); the rest of ICB matches the config names. Most
# Nasdaq-100 names are also in the S&P 500 and take that GICS classification — only the marginal
# Nasdaq-100-only names use the ICB label. Reference mapping, not a scoring number (one-shot build tool).
WIKI_SECTOR_TO_CONFIG = {
    # GICS (S&P 500 table)
    "Information Technology": "Technology",
    "Financials": "Financials",
    "Energy": "Energy",
    "Health Care": "Health Care",
    "Industrials": "Industrials",
    "Consumer Discretionary": "Consumer Discretionary",
    "Consumer Staples": "Consumer Staples",
    "Utilities": "Utilities",
    "Materials": "Materials",
    "Real Estate": "Real Estate",
    "Communication Services": "Communication Services",
    # ICB (Nasdaq-100 table) extras / aliases
    "Technology": "Technology",
    "Basic Materials": "Materials",
    "Telecommunications": "Communication Services",
}

WIKI_PAGES = {
    "sp500": "List_of_S%26P_500_companies",
    "nasdaq100": "Nasdaq-100",
}

# Average-daily-dollar-volume window for the liquidity screen (trading days ~ 3 months). A build-time
# choice documented here; not a runtime scoring tunable (this script is not on the calc/request path).
ADV_WINDOW = 63
# Yahoo /v7/finance/quote batch size (symbols per request) — keep modest to be polite to the no-key API.
QUOTE_BATCH = 40


# --------------------------------------------------------------------------------------------------
# Wikipedia constituent-table parsing (stdlib only — lxml/bs4 are not installed)
# --------------------------------------------------------------------------------------------------
class _TableParser(HTMLParser):
    """Collect every HTML table as a list of rows, each row a list of plain-text cells (tags/refs
    stripped). Robust enough to read Wikipedia's constituent tables without lxml/bs4."""

    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._in_table = 0
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._cur_table: list[list[str]] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._in_table += 1
            if self._in_table == 1:
                self._cur_table = []
        elif self._in_table and tag == "tr":
            self._row = []
        elif self._in_table and tag in ("td", "th"):
            self._cell = []

    def handle_endtag(self, tag):
        if tag == "table" and self._in_table:
            if self._in_table == 1 and self._cur_table is not None:
                self.tables.append(self._cur_table)
                self._cur_table = None
            self._in_table = max(0, self._in_table - 1)
        elif tag == "tr" and self._row is not None:
            if self._cur_table is not None:
                self._cur_table.append(self._row)
            self._row = None
        elif tag in ("td", "th") and self._cell is not None:
            text = " ".join("".join(self._cell).split())
            if self._row is not None:
                self._row.append(text)
            self._cell = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def _fetch_wiki_constituents(client: httpx.Client, page: str) -> list[tuple[str, str]]:
    """Return [(ticker, wiki_gics_sector)] from a Wikipedia index-constituent page. Finds the table whose
    header has a Symbol/Ticker column AND a GICS-Sector column, then reads those two columns per row."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/html/{page}"
    resp = client.get(url, headers=WIKI_HEADERS, timeout=30.0)
    resp.raise_for_status()
    parser = _TableParser()
    parser.feed(resp.text)

    for table in parser.tables:
        if not table:
            continue
        header = [c.lower() for c in table[0]]
        sym_idx = next((i for i, h in enumerate(header) if h in ("symbol", "ticker")), None)
        # the sector column is GICS on the S&P 500 table, ICB Industry on the Nasdaq-100 table —
        # never the "* sub-industry"/"* subsector" column.
        sec_idx = next(
            (i for i, h in enumerate(header)
             if ("gics sector" in h or "icb industry" in h or h in ("sector", "industry"))
             and "sub" not in h),
            None,
        )
        if sym_idx is None or sec_idx is None:
            continue
        out: list[tuple[str, str]] = []
        for row in table[1:]:
            if len(row) <= max(sym_idx, sec_idx):
                continue
            ticker = row[sym_idx].strip().upper().replace(".", "-")  # BRK.B -> BRK-B (Yahoo convention)
            sector = row[sec_idx].strip()
            if ticker and sector:
                out.append((ticker, sector))
        if out:
            return out
    raise RuntimeError(f"no constituent table with Symbol+GICS-Sector columns found on {page!r}")


def build_pool() -> int:
    """Fetch S&P 500 + Nasdaq-100 constituents (ticker + GICS sector) from Wikipedia, union with the
    prior committed universe, and write the documented frozen candidate pool to universe_pool.csv."""
    config = load_config()
    valid_sectors = set(config.etfs.sector.values())
    pool: dict[str, dict] = {}  # ticker -> {sector, source}

    with httpx.Client(follow_redirects=True) as client:
        for source, page in WIKI_PAGES.items():
            rows = _fetch_wiki_constituents(client, page)
            print(f"[pool] {source}: {len(rows)} constituents from Wikipedia ({page})")
            for ticker, wiki_sector in rows:
                config_sector = WIKI_SECTOR_TO_CONFIG.get(wiki_sector)
                if config_sector is None or config_sector not in valid_sectors:
                    print(f"[pool]   skip {ticker}: unmapped GICS sector {wiki_sector!r}")
                    continue
                pool.setdefault(ticker, {"sector": config_sector, "source": source})

    # Union with the prior committed universe so existing themed names remain candidates (their sector
    # comes from the prior config when not present in either index table).
    prior_added = 0
    for ticker in config.universe.symbols:
        if ticker not in pool:
            sector = config.stock_sectors.get(ticker)
            if sector in valid_sectors:
                pool[ticker] = {"sector": sector, "source": "prior_universe"}
                prior_added += 1

    SEED_DIR.mkdir(parents=True, exist_ok=True)
    with POOL_CSV.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["# Trendora candidate pool — J-22. Membership rule: S&P 500 ∪ Nasdaq-100 "
                         "(real index constituents from Wikipedia) ∪ the prior committed universe."])
        writer.writerow([f"# Built {datetime.now(timezone.utc).date().isoformat()} from Wikipedia "
                         "REST constituent tables. The config screen (universe.filters) is applied to "
                         "this pool by --screen; only passers become universe.symbols."])
        writer.writerow(["symbol", "sector", "source"])
        for ticker in sorted(pool):
            writer.writerow([ticker, pool[ticker]["sector"], pool[ticker]["source"]])

    by_source: dict[str, int] = {}
    for meta in pool.values():
        by_source[meta["source"]] = by_source.get(meta["source"], 0) + 1
    print(f"[pool] wrote {len(pool)} unique candidates to {POOL_CSV}")
    print(f"[pool] by source: {by_source} (prior-only added: {prior_added})")
    return 0


# --------------------------------------------------------------------------------------------------
# Yahoo fetch — OHLCV (chart) + market cap (quote via cookie+crumb), with 429-aware backoff
# --------------------------------------------------------------------------------------------------
def _to_epoch(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def _get_json(client: httpx.Client, url: str, params: dict, *, max_retries: int = 6) -> dict:
    """GET JSON with 429-aware exponential backoff. Raises on persistent failure (never fabricates)."""
    last = None
    for attempt in range(max_retries):
        try:
            resp = client.get(url, params=params, headers=HEADERS, timeout=30.0)
            if resp.status_code == 429:
                last = "429 Too Many Requests"
                time.sleep(min(60, 8 * (attempt + 1)))
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # noqa: BLE001 — backoff then retry; raise after the loop
            last = repr(exc)
            time.sleep(min(60, 5 * (attempt + 1)))
    raise RuntimeError(f"request failed after {max_retries} retries ({url}): {last}")


def fetch_ohlcv(client: httpx.Client, symbol: str, start: date, end: date) -> list[dict]:
    """REAL split/dividend-adjusted daily OHLCV rows for one symbol (same path as ingest_seed.py)."""
    payload = _get_json(client, CHART_URL.format(symbol=symbol), {
        "period1": _to_epoch(start), "period2": _to_epoch(end), "interval": "1d", "events": "div,split",
    })
    result = payload["chart"]["result"]
    if not result:
        raise ValueError(f"no chart result for {symbol}")
    res = result[0]
    timestamps = res.get("timestamp") or []
    quote = res["indicators"]["quote"][0]
    adj = (res["indicators"].get("adjclose") or [{}])[0].get("adjclose")
    rows: list[dict] = []
    for i, ts in enumerate(timestamps):
        o, h, low, c, v = (quote["open"][i], quote["high"][i], quote["low"][i],
                           quote["close"][i], quote["volume"][i])
        if None in (o, h, low, c):
            continue  # skip incomplete bars — never interpolate/fabricate
        factor = (adj[i] / c) if (adj and adj[i] is not None and c) else 1.0
        d = datetime.fromtimestamp(ts, ET).date()
        rows.append({
            "date": d.isoformat(),
            "open": round(o * factor, 6), "high": round(h * factor, 6),
            "low": round(low * factor, 6), "close": round(c * factor, 6),
            "volume": int(v) if v is not None else 0,
        })
    by_date = {r["date"]: r for r in rows}
    return [by_date[d] for d in sorted(by_date)]


def _yahoo_crumb(client: httpx.Client) -> str:
    """Acquire the no-key cookie + crumb so /v7/finance/quote returns marketCap. The crumb is used at
    runtime only — never stored/committed (anti-goal: No secrets in source)."""
    client.get(COOKIE_URL, headers=HEADERS, timeout=30.0)  # sets the A1/A3 cookie
    for attempt in range(6):
        resp = client.get(CRUMB_URL, headers=HEADERS, timeout=30.0)
        if resp.status_code == 200 and resp.text.strip() and "Too Many" not in resp.text:
            return resp.text.strip()
        time.sleep(min(60, 8 * (attempt + 1)))
    raise RuntimeError("could not obtain Yahoo crumb (persistent 429 / empty)")


def fetch_market_caps(client: httpx.Client, symbols: list[str], crumb: str) -> dict[str, float]:
    """REAL market cap per symbol from /v7/finance/quote (batched). Missing caps are simply absent from
    the returned dict (the caller omits + logs that candidate — never fabricates a cap)."""
    caps: dict[str, float] = {}
    for i in range(0, len(symbols), QUOTE_BATCH):
        batch = symbols[i:i + QUOTE_BATCH]
        payload = _get_json(client, QUOTE_URL, {"symbols": ",".join(batch), "crumb": crumb})
        for row in (payload.get("quoteResponse") or {}).get("result") or []:
            sym = row.get("symbol")
            cap = row.get("marketCap")
            if sym and cap:
                caps[sym] = float(cap)
        time.sleep(0.5)
    return caps


# --------------------------------------------------------------------------------------------------
# Screen application
# --------------------------------------------------------------------------------------------------
def screen_reasons(
    reference_close: float | None,
    adv_dollar: float | None,
    market_cap: float | None,
    *,
    min_price: float,
    min_dollar_vol: float,
    min_market_cap: float,
) -> list[str]:
    """Pure screen predicate (importable + unit-tested): the list of reasons a candidate FAILS the
    three config thresholds. Empty list == passes. A missing market cap is a failure ("no_market_cap")
    — the candidate is omitted, never fabricated. Reads ONLY the passed-in `universe.filters` values."""
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


def _read_committed_csv(symbol: str, start: date, end: date) -> list[dict] | None:
    """Reuse an already-committed price CSV (within the window) instead of re-fetching it — so the
    proven existing bars (SPY/ETFs/prior names) are preserved and only NEW names hit the network. Each
    committed CSV is internally split/div-adjusted; the engine compares within-symbol returns/ratios, so
    mixing committed and freshly-fetched series is sound. Returns None if no committed CSV exists."""
    path = PRICES_DIR / symbol_to_filename(symbol)
    if not path.exists():
        return None
    rows: list[dict] = []
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            if start.isoformat() <= row["date"] <= end.isoformat():
                rows.append({
                    "date": row["date"], "open": float(row["open"]), "high": float(row["high"]),
                    "low": float(row["low"]), "close": float(row["close"]), "volume": float(row["volume"]),
                })
    return rows or None


def _write_csv(symbol: str, rows: list[dict]) -> Path:
    PRICES_DIR.mkdir(parents=True, exist_ok=True)
    path = PRICES_DIR / symbol_to_filename(symbol)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["date", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)
    return path


def _read_pool() -> list[dict]:
    if not POOL_CSV.exists():
        raise SystemExit(f"candidate pool not found: {POOL_CSV} — run --build-pool first")
    out: list[dict] = []
    with POOL_CSV.open(newline="") as fh:
        for row in csv.DictReader(line for line in fh if not line.startswith("#")):
            out.append(row)
    return out


def screen(start: date, end: date, sleep: float) -> int:
    config = load_config()
    filters = config.universe.filters
    pool = _read_pool()
    pool_symbols = [r["symbol"] for r in pool]
    sector_by_symbol = {r["symbol"]: r["sector"] for r in pool}
    source_by_symbol = {r["symbol"]: r["source"] for r in pool}

    # Benchmarks (ETFs + ^VIX) are always ingested, never screened.
    etf_symbols: list[str] = []
    etf_symbols += list(config.etfs.index)
    etf_symbols += list(config.etfs.sector.keys())
    etf_symbols += list(config.etfs.industry)
    etf_symbols += list(config.etfs.volatility)

    print(f"[screen] pool={len(pool_symbols)} candidates + {len(etf_symbols)} benchmark ETFs; "
          f"window {start}..{end}; thresholds price>={filters.min_price} "
          f"adv>={filters.min_dollar_vol} cap>={filters.min_market_cap}")

    with httpx.Client(follow_redirects=True) as client:
        print("[screen] acquiring Yahoo crumb for market caps...")
        crumb = _yahoo_crumb(client)
        print("[screen] fetching market caps...")
        caps = fetch_market_caps(client, pool_symbols, crumb)
        print(f"[screen] got market cap for {len(caps)}/{len(pool_symbols)} candidates")

        # 1) Benchmarks — reuse the committed CSV when present (no re-fetch), else fetch. No screen.
        bench_ok, bench_failed = [], []
        for sym in etf_symbols:
            try:
                rows = _read_committed_csv(sym, start, end)
                if rows is None:
                    rows = fetch_ohlcv(client, sym, start, end)
                    time.sleep(sleep)
                if not rows:
                    raise ValueError("empty series")
                _write_csv(sym, rows)
                bench_ok.append(sym)
            except Exception as exc:  # noqa: BLE001
                bench_failed.append(sym)
                print(f"[etf ] {sym:7s} FAILED: {exc!r}")

        # 2) Candidates — OHLCV (reuse committed or fetch), then apply the three-threshold screen
        # against REAL reference values.
        members: list[dict] = []
        omitted: list[dict] = []
        reused = fetched = 0
        for idx, sym in enumerate(pool_symbols, 1):
            rows = _read_committed_csv(sym, start, end)
            if rows is not None:
                reused += 1
            else:
                try:
                    rows = fetch_ohlcv(client, sym, start, end)
                    fetched += 1
                except Exception as exc:  # noqa: BLE001 — failed fetch: omit + log, never fabricate
                    omitted.append({"symbol": sym, "reason": f"fetch_failed: {exc!r}"[:120]})
                    print(f"[{idx:3d}/{len(pool_symbols)}] {sym:7s} OMIT fetch_failed")
                    time.sleep(sleep)
                    continue
                time.sleep(sleep)
            if not rows:
                omitted.append({"symbol": sym, "reason": "empty_series"})
                continue

            ref_close = rows[-1]["close"]
            adv_rows = rows[-ADV_WINDOW:]
            adv = sum(r["close"] * r["volume"] for r in adv_rows) / len(adv_rows)
            cap = caps.get(sym)

            reasons = screen_reasons(
                ref_close, adv, cap,
                min_price=filters.min_price, min_dollar_vol=filters.min_dollar_vol,
                min_market_cap=filters.min_market_cap,
            )

            if reasons:
                omitted.append({"symbol": sym, "reason": "; ".join(reasons)})
                print(f"[{idx:3d}/{len(pool_symbols)}] {sym:7s} OMIT {reasons}")
            else:
                _write_csv(sym, rows)
                members.append({
                    "symbol": sym,
                    "sector": sector_by_symbol[sym],
                    "source": source_by_symbol[sym],
                    "market_cap": round(cap, 2),
                    "reference_close": round(ref_close, 4),
                    "adv_dollar": round(adv, 2),
                    "bars": len(rows),
                    "first": rows[0]["date"],
                    "last": rows[-1]["date"],
                })
                print(f"[{idx:3d}/{len(pool_symbols)}] {sym:7s} PASS cap={cap/1e9:.1f}B "
                      f"px={ref_close:.2f} adv={adv/1e6:.0f}M ({len(rows)} bars)")
            time.sleep(sleep)

    members.sort(key=lambda m: m["symbol"])
    universe = {
        "membership_rule": ("Union of the S&P 500 and Nasdaq-100 index constituents (real memberships, "
                            "from Wikipedia) and the prior committed universe, then screened by the "
                            "config liquidity/price/market-cap filters (universe.filters)."),
        "screen_thresholds": {
            "min_market_cap": filters.min_market_cap,
            "min_dollar_vol": filters.min_dollar_vol,
            "min_price": filters.min_price,
            "adv_window_days": ADV_WINDOW,
        },
        "source": {
            "ohlcv": "Yahoo Finance chart API (query1.finance.yahoo.com/v8/finance/chart), no key",
            "market_cap": "Yahoo Finance quote API (/v7/finance/quote) via no-key cookie+crumb, no key",
            "sector": "Wikipedia S&P 500 / Nasdaq-100 GICS sector tables; prior config for prior-only names",
            "pool": str(POOL_CSV.relative_to(BACKEND_DIR)),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "member_count": len(members),
        "members": members,
        "omitted_count": len(omitted),
        "omitted": omitted,
        "benchmarks_ok": bench_ok,
        "benchmarks_failed": bench_failed,
    }
    UNIVERSE_JSON.write_text(json.dumps(universe, indent=2) + "\n")

    meta = {
        "source": "Yahoo Finance chart API (query1.finance.yahoo.com/v8/finance/chart)",
        "note": ("REAL split/dividend-adjusted EOD OHLCV; frozen + committed; no key/secret. Universe is "
                 "the config-recorded screen (universe.filters) applied to the documented candidate pool "
                 "(S&P 500 ∪ Nasdaq-100 ∪ prior universe); see universe.json for per-member "
                 "screen-pass values and omitted candidates."),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "symbols_ok": len(members) + len(bench_ok),
        "symbols_failed": len(bench_failed),
        "universe_members": len(members),
        "benchmarks": len(bench_ok),
        "failed": bench_failed,
        "omitted_candidates": len(omitted),
    }
    (SEED_DIR / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")

    print(f"\n[screen] DONE: {len(members)} universe members pass the screen, "
          f"{len(omitted)} candidates omitted, {len(bench_ok)} benchmark ETFs ok "
          f"({len(bench_failed)} failed). OHLCV reused-committed={reused}, freshly-fetched={fetched}.")
    print(f"[screen] wrote {UNIVERSE_JSON} and refreshed meta.json")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="J-22 universe screen + seed ingest (one-shot).")
    parser.add_argument("--build-pool", action="store_true", help="fetch + write the candidate pool, then exit")
    parser.add_argument("--start", default="2021-01-01", help="ISO start date (default 2021-01-01)")
    parser.add_argument("--end", default=None, help="ISO end date (default: latest ET trading date)")
    parser.add_argument("--sleep", type=float, default=0.4, help="seconds between symbol requests")
    args = parser.parse_args()

    if args.build_pool:
        return build_pool()
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end) if args.end else datetime.now(ET).date()
    return screen(start, end, args.sleep)


if __name__ == "__main__":
    raise SystemExit(main())
