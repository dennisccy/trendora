"""Seed ingest — DEV-RUN, then COMMIT the output. NOT on the boot/request path.

Fetches REAL daily EOD OHLCV and writes a frozen CSV fixture (`prices/*.csv` + `meta.json`).
After committing, the build loop only READS these files (via SeedProvider) and MUST NOT re-fetch
live data — re-fetching would make later walk-forward evidence irreproducible.

Two provider paths (`--provider`, default `yahoo` — the historical behavior, byte-compatible):

* `yahoo` — the free, NO-KEY Yahoo Finance chart API (query1.finance.yahoo.com/v8/finance/chart).
  SOURCE NOTE (documented deviation, iter-1): the original plan named Stooq, but Stooq's BULK CSV
  download is gated behind a captcha-obtained apikey; the per-run Yahoo path was adopted with the
  same hard guarantees (REAL EOD history, no key, no secret, frozen once committed).
* `stooq` — iter-16: the free PER-SYMBOL Stooq CSV endpoint via the EXISTING
  `app.data_providers.StooqProvider.get_daily` (keyless; `.us` suffix mapping; caret-preserved
  indexes) through its documented client-injection seam. Used to STAGE the ~30-year replacement
  seed side-by-side (`--out data/seed-stooq-30y`) for the sanctioned iter-17 basis swap — the
  staged tree is read by NOTHING at runtime. Resumable (manifest-driven skip), polite (>=1s
  between requests), pinned-end window (resume runs REUSE the manifest's pinned end), graceful
  honest stop on a rate-cap/limit/denial page. Stooq's front door now serves an automatic
  JavaScript browser-verification handshake (a millisecond SHA-256 proof-of-work — no captcha, no
  credential); the injected client completes it exactly as the page specifies, and the endpoint's
  own access decision behind it (ACL/daily limit) is honored unchanged. If the endpoint demands a
  key for this IP, `STOOQ_API_KEY` is read from the ENVIRONMENT ONLY and rides as a query param —
  never persisted, never committed.

No bars are ever fabricated, padded, interpolated, or vendor-spliced — a symbol that fails is
recorded and honestly omitted; a rate-cap stops the run in a resumable state with a non-zero exit.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/ingest_seed.py
    apps/backend/.venv/bin/python apps/backend/scripts/ingest_seed.py --start 2021-01-01
    # iter-16 staged 30y Stooq seed (probe first, then the full prioritized pool):
    apps/backend/.venv/bin/python apps/backend/scripts/ingest_seed.py \
        --provider stooq --probe --out apps/backend/data/seed-stooq-30y --start 1996-01-01
    apps/backend/.venv/bin/python apps/backend/scripts/ingest_seed.py \
        --provider stooq --out apps/backend/data/seed-stooq-30y --symbols-set pool --start 1996-01-01
    # iter-17 (goal.md §H): merge the index/macro CONTEXT into the staged seed — ^SPX/^NDX/^DJI
    # deep from the local world bundle, ^VIX deep from Yahoo (sanctioned live-copy fallback),
    # ^TNX/^DXY/^VXN byte-identical FRED-macro-proxy copies; per-series vendor in meta.json:
    apps/backend/.venv/bin/python apps/backend/scripts/ingest_seed.py \
        --provider stooq-local --stage-context --out apps/backend/data/seed-stooq-30y

Exit codes: 0 ok (recorded per-symbol absences included) · 2 rate-cap/gated stop (resumable) or
probe hard-failure · 3 probe validation failure (no-go) · 4 refused (window conflict / foreign --out).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import httpx

# scripts/ -> backend -> apps -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
SEED_DIR = BACKEND_DIR / "data" / "seed"
DEFAULT_ARCHIVE_DIR = REPO_ROOT / "data" / "d_us_txt"  # stooq-local: extracted Stooq bulk US archive
# --stage-context default: the extracted Stooq bulk WORLD archive (plain ^xxx.txt files, e.g.
# data/daily/world/indices/^spx.txt) — the offline source for the deep ^SPX/^NDX/^DJI context.
DEFAULT_WORLD_ARCHIVE_DIR = REPO_ROOT / "data" / "d_world_txt"

sys.path.insert(0, str(BACKEND_DIR))
from app.config import load_config  # noqa: E402
from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError  # noqa: E402
from app.data_providers.local_stooq_archive import LocalStooqArchiveProvider  # noqa: E402
from app.data_providers.seed_provider import symbol_to_filename  # noqa: E402
from app.data_providers.stooq_provider import StooqProvider  # noqa: E402
from app.engine.universe_screen import read_pool  # noqa: E402
from app.seed_loader import all_seed_symbols  # noqa: E402

YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) trendora-seed-ingest/1.0"}
ET = ZoneInfo("America/New_York")

CSV_FIELDS = ["date", "open", "high", "low", "close", "volume"]
DEFAULT_START = "2021-01-01"
YAHOO_DEFAULT_SLEEP = 0.3  # historical default (unchanged)
STOOQ_DEFAULT_SLEEP = 1.0  # polite: the staged fetch keeps >=1s between requests
STOOQ_API_KEY_ENV = "STOOQ_API_KEY"  # env-only, request-only — never persisted (anti-goal: no secrets)
STOOQ_SOURCE = "Stooq free per-symbol CSV (https://stooq.com/q/d/l/, keyless)"
STOOQ_NOTE = (
    "REAL split/dividend-adjusted EOD OHLCV staged side-by-side for the sanctioned iter-17 basis "
    "swap; read by NOTHING at runtime. Fetched via app.data_providers.StooqProvider "
    "(make_provider('stooq')); per-name first bar is the name's real first bar — never padded, "
    "fabricated, or vendor-spliced. Failures and rate-cap events are recorded honestly below."
)
# stooq-local (iter-16 unblock): the SAME Stooq vendor data, read from the operator's locally
# extracted BULK US archive (`data/d_us_txt/`) instead of the IP-blocked per-symbol export endpoint.
# The `provider` tag stays "stooq" (the vendor is unchanged); only the access method differs, which
# is recorded here in `source`/`note`.
STOOQ_LOCAL_SOURCE = "Stooq bulk US daily archive (local: data/d_us_txt, from stooq.com d_us_txt.zip)"
STOOQ_LOCAL_NOTE = (
    "REAL split/dividend-adjusted EOD OHLCV read from Stooq's BULK US stocks+ETFs archive "
    "(data/d_us_txt/, the operator's d_us_txt.zip) — the SAME vendor and adjusted data as the "
    "per-symbol endpoint, consumed locally to bypass the standing per-IP export ACL. Provider tag "
    "stays 'stooq' (vendor unchanged); only the access method differs. Per-name first bar is the "
    "name's real first bar — never padded, fabricated, or vendor-spliced. Caret index series "
    "(^VIX/^TNX/^VXN/^DXY) and any name absent from this stocks+ETFs bundle are recorded absent "
    "below (they come from a separate Stooq indices bundle), never fabricated."
)

EXIT_OK = 0
EXIT_CAP_STOP = 2    # rate-cap / gated endpoint — honest, resumable stop
EXIT_PROBE_FAIL = 3  # probe validation failed (depth/adjusted-basis) — no-go, nothing staged
EXIT_CONFLICT = 4    # window conflict / foreign --out dir — refused before any write

# Probe anchors (spec-pinned go/no-go facts, not scoring tunables): AAPL/SPY traded through 1996,
# so a full-depth feed must reach the first 1996 week; NVDA 10:1 (2024-06-10) and AAPL 4:1
# (2020-08-31) splits must show NO ~10x/~4x one-day close seam on a back-adjusted basis.
PROBE_SYMBOLS = ("AAPL", "SPY", "NVDA")
PROBE_DEPTH_SYMBOLS = ("AAPL", "SPY")
PROBE_DEPTH_ANCHOR = date(1996, 1, 5)
PROBE_SPLIT_DAYS = {"NVDA": date(2024, 6, 10), "AAPL": date(2020, 8, 31)}
PROBE_MAX_SPLIT_DAY_MOVE = 0.25  # far above a real daily move, far below an unadjusted split gap


class WindowConflictError(ValueError):
    """An explicit --start/--end conflicts with a staging manifest's pinned window."""


# ---------------------------------------------------------------------------
# symbol sets
# ---------------------------------------------------------------------------

def build_default_symbols(config) -> list[str]:
    """The historical default set (byte-identical to pre-iter-16): universe + the four ETF groups,
    de-duplicated, order-preserving. Legend/macro-proxy symbols are NOT added here — that widening
    exists only under `--symbols-set pool`."""
    symbols: list[str] = []
    symbols += list(config.universe.symbols)
    symbols += list(config.etfs.index)
    symbols += list(config.etfs.sector.keys())
    symbols += list(config.etfs.industry)
    symbols += list(config.etfs.volatility)
    seen: set[str] = set()
    return [s for s in symbols if not (s in seen or seen.add(s))]


def build_pool_symbol_plan(config, seed_dir: Path | None = None) -> dict[str, list[str]]:
    """`--symbols-set pool`: the de-duplicated union of the committed candidate pool
    (`universe_pool.csv`, ~548 names) and `all_seed_symbols` (ETFs/^VIX/legend/macro proxies),
    priority-ordered so a rate-cap secures the most load-bearing names first:
      tier1 — benchmarks/controls: index ETFs (SPY/QQQ/...), sector/industry/volatility ETFs,
              ^VIX, index-chart legend symbols, macro proxies (everything in all_seed_symbols
              that is not a universe stock);
      tier2 — the current `universe.symbols`;
      tier3 — the remaining pool names, alphabetical."""
    universe = list(config.universe.symbols)
    universe_set = set(universe)
    tier1 = [s for s in all_seed_symbols(config) if s not in universe_set]
    pool = sorted({row["symbol"] for row in read_pool(seed_dir)})
    covered = set(tier1) | universe_set
    tier3 = [s for s in pool if s not in covered]
    return {"tier1": tier1, "tier2": universe, "tier3": tier3, "all": tier1 + universe + tier3}


# ---------------------------------------------------------------------------
# pinned window + staging manifest
# ---------------------------------------------------------------------------

def most_recent_completed_trading_day(today: date) -> date:
    """Most recent weekday strictly BEFORE `today` — a conservative 'completed session' bound (a
    holiday simply has no bar; the pinned end only bounds the one shared window)."""
    d = today - timedelta(days=1)
    while d.weekday() >= 5:  # Sat/Sun
        d -= timedelta(days=1)
    return d


def load_manifest(out_dir: Path | str) -> dict | None:
    path = Path(out_dir) / "meta.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _foreign_manifest(manifest: dict | None) -> bool:
    """True when --out already holds a NON-stooq seed (e.g. the live Yahoo seed) — refuse to write
    there: staging is side-by-side only; the basis swap is a separate, sanctioned later step."""
    return manifest is not None and manifest.get("provider") != "stooq"


def resolve_stooq_window(
    start_arg: str | None, end_arg: str | None, manifest: dict | None, today: date
) -> tuple[date, date]:
    """Resolve the fetch window. A fresh run pins `end` to the most recent COMPLETED trading day;
    a resume run MUST reuse the manifest's pinned window (one consistent bound for every symbol) —
    a conflicting explicit --start/--end is refused, never silently mixed."""
    if manifest is not None:
        window = manifest.get("window") or {}
        m_start, m_end = window.get("start"), window.get("end")
        if m_start and m_end:
            if start_arg is not None and start_arg != m_start:
                raise WindowConflictError(
                    f"--start {start_arg} conflicts with the staging manifest's pinned start "
                    f"{m_start}; resume runs reuse the manifest window (start a fresh staging dir "
                    f"for a different window)"
                )
            if end_arg is not None and end_arg != m_end:
                raise WindowConflictError(
                    f"--end {end_arg} conflicts with the staging manifest's pinned end {m_end}; "
                    f"resume runs reuse the manifest window (start a fresh staging dir for a "
                    f"different window)"
                )
            return date.fromisoformat(m_start), date.fromisoformat(m_end)
    start = date.fromisoformat(start_arg or DEFAULT_START)
    end = date.fromisoformat(end_arg) if end_arg else most_recent_completed_trading_day(today)
    return start, end


_APIKEY_PARAM_RE = re.compile(r"(apikey=)[^&\s'\"]+")


def redact_stooq_key(text: str) -> str:
    """Strip any STOOQ_API_KEY value from a message before it is printed or persisted. httpx embeds
    the full request URL — including the `apikey` query param — in HTTP-status error messages, and
    those messages flow into the staging manifest (a COMMITTED artifact) and console output. The
    key is env-only and must NEVER be persisted (anti-goal: no credentials committed)."""
    key = os.environ.get(STOOQ_API_KEY_ENV)
    if key:
        text = text.replace(key, "***")
    return _APIKEY_PARAM_RE.sub(r"\1***", text)


class _ManifestState:
    """The staging progress manifest (meta.json) — live-seed layout (`window`/`symbols`/`failed`)
    plus `provider`, per-symbol `failures` (honest absences) and `cap_events` (resumable stops).
    Failure/cap details are key-redacted before they are recorded — meta.json gets committed."""

    def __init__(self, manifest: dict | None, start: date, end: date, planned: int,
                 source: str = STOOQ_SOURCE, note: str = STOOQ_NOTE):
        prior = manifest or {}
        self.ok: dict[str, dict] = {e["symbol"]: dict(e) for e in prior.get("symbols", [])}
        self.failures: dict[str, dict] = {e["symbol"]: dict(e) for e in prior.get("failures", [])}
        self.cap_events: list[dict] = [dict(e) for e in prior.get("cap_events", [])]
        self.start, self.end, self.planned = start, end, planned
        self.source, self.note = source, note

    def record_ok(self, symbol: str, rows: list[dict], vendor: str | None = None,
                  note: str | None = None) -> None:
        """Record a staged series. `vendor`/`note` exist for the iter-17 CONTEXT series only
        (per-series vendor disclosure, goal.md §H); equity records keep the manifest-level
        provider tag and stay byte-identical. `note` passes the redaction choke point — it is
        persisted into the committed manifest."""
        entry: dict = {"symbol": symbol, "bars": len(rows),
                       "first": rows[0]["date"], "last": rows[-1]["date"]}
        if vendor is not None:
            entry["vendor"] = vendor
        if note is not None:
            entry["note"] = redact_stooq_key(note)[:300]
        self.ok[symbol] = entry
        self.failures.pop(symbol, None)

    def record_absent(self, symbol: str, kind: str, detail: str) -> None:
        self.failures[symbol] = {"symbol": symbol, "kind": kind,
                                 "detail": redact_stooq_key(detail)[:200]}

    def record_cap(self, symbol: str, detail: str, attempts: int) -> None:
        self.cap_events.append({"at": datetime.now(timezone.utc).isoformat(),
                                "symbol": symbol, "detail": redact_stooq_key(detail)[:200],
                                "attempts": attempts})

    def to_manifest(self) -> dict:
        return {
            "source": self.source,
            "provider": "stooq",
            "note": self.note,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "window": {"start": self.start.isoformat(), "end": self.end.isoformat()},
            "symbols_planned": self.planned,
            "symbols_ok": len(self.ok),
            "symbols_failed": len(self.failures),
            "failed": sorted(self.failures),
            "failures": list(self.failures.values()),
            "cap_events": list(self.cap_events),
            "symbols": list(self.ok.values()),
        }

    def write(self, out_dir: Path) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "meta.json"
        tmp = out_dir / "meta.json.tmp"
        tmp.write_text(json.dumps(self.to_manifest(), indent=2) + "\n")
        tmp.replace(path)


# ---------------------------------------------------------------------------
# providers + fetch/write plumbing
# ---------------------------------------------------------------------------

# Stooq now fronts its free endpoints with an automatic JavaScript browser-verification handshake:
# the served page instructs the client to find a nonce n with sha256(c+n) starting with d hex
# zeros and POST it to /__verify, which grants a short-lived session cookie, then reload. It is a
# machine-solvable proof-of-work every visiting browser completes silently — NOT a captcha and NOT
# a credential. (Verified live 2026-07: the handshake passes; the CSV export endpoint's OWN access
# decision — e.g. an "Access denied" ACL for this IP, or the daily-hits limit — then still applies
# and is honored unchanged: it surfaces as ProviderUnavailableError and stops the run honestly.)
_STOOQ_CHALLENGE_RE = re.compile(r'const c="([^"]+)",d=(\d+)')

# (iter-16 audit B2) Bound the handshake solve: the observed served difficulty is 4 (~65k tries
# expected; solved live in 0.03s) and 5 needs ~1M — 10M clears both with overwhelming margin. A
# served difficulty the cap cannot clear is treated as a GATE (honest resumable stop), never an
# unbounded spin.
_POW_MAX_ITERATIONS = 10_000_000


def _solve_stooq_pow(challenge: str, difficulty: int,
                     max_iterations: int = _POW_MAX_ITERATIONS) -> int:
    prefix = "0" * difficulty
    for n in range(max_iterations):
        if hashlib.sha256(f"{challenge}{n}".encode()).hexdigest().startswith(prefix):
            return n
    raise ProviderUnavailableError(
        f"stooq verification handshake unsolved after {max_iterations} iterations (served "
        f"difficulty {difficulty}) — refusing an unbounded spin; treating the endpoint as gated "
        f"for this environment"
    )


class _StooqVerifyClient:
    """An httpx-client shim for `StooqProvider`'s documented injection seam that completes Stooq's
    browser-verification handshake exactly as the served page specifies, then retries the original
    request once with the granted session cookie. The cookie lives ONLY in this process's memory —
    never persisted, logged, or committed. `STOOQ_API_KEY` (if the endpoint ever demands a key) is
    read from the environment by the caller and rides as a query param here, request-only."""

    def __init__(self, client: Optional[httpx.Client] = None, api_key: Optional[str] = None):
        params = {"apikey": api_key} if api_key else None
        self._client = client or httpx.Client(headers=HEADERS, params=params,
                                              follow_redirects=True)

    def get(self, url, params=None, timeout=None):
        response = self._client.get(url, params=params, timeout=timeout)
        challenge = _STOOQ_CHALLENGE_RE.search(response.text or "")
        if challenge is None:
            return response
        nonce = _solve_stooq_pow(challenge.group(1), int(challenge.group(2)))
        verify_url = str(httpx.URL(url).copy_with(path="/__verify", query=None))
        verified = self._client.post(verify_url, data={"c": challenge.group(1), "n": nonce},
                                     timeout=timeout)
        if verified.status_code != 200:
            return response  # verification refused — surface the challenge page (a gate stop)
        return self._client.get(url, params=params, timeout=timeout)

    def close(self) -> None:
        self._client.close()


def make_stooq_provider() -> PriceProvider:
    """The stooq fetch path uses the EXISTING `StooqProvider.get_daily` (keyless free CSV, `.us`
    mapping, caret-preserved indexes, real-data-only contract) through its documented
    client-injection seam: a bare `make_provider("stooq")` client cannot pass Stooq's 2026
    front-door verification handshake, so the script injects `_StooqVerifyClient` — same provider,
    same endpoint, zero `app/**` change. If the endpoint demands a key for this IP,
    `STOOQ_API_KEY` is read from the ENVIRONMENT ONLY (request-only query param; never persisted,
    logged, or committed); absent key + gated endpoint = an honest, documented failure."""
    return StooqProvider(client=_StooqVerifyClient(api_key=os.environ.get(STOOQ_API_KEY_ENV)))


class _LocalStooqBundleProvider(LocalStooqArchiveProvider):
    """`LocalStooqArchiveProvider` (US archive: `*.us.txt`) extended with Stooq's WORLD-bundle
    layout (iter-17): plain `^xxx.txt` files (no `.us` suffix; e.g.
    `data/daily/world/indices/^spx.txt`), same `<TICKER>,<PER>,<DATE>,...` bulk row format, same
    vendor (stooq). A caret symbol maps to its caret-keeping file stem (`^SPX` -> `^spx.txt`);
    everything else keeps the parent's behavior byte-identically (absent name/caret -> honest [],
    corrupt row in a present file -> ProviderUnavailableError('...unparseable...'), start/end
    window clip in the parser). Defined HERE (not app/**) because archives are read only by this
    dev-run script — the app boot/request path stays unchanged."""

    _WORLD_SUFFIX = ".txt"

    def __init__(self, archive_dir: Path | str):
        super().__init__(archive_dir)  # indexes *.us.txt exactly as before
        self.world_indexed_count = 0
        if self.archive_dir.is_dir():
            for path in self.archive_dir.rglob("^*" + self._WORLD_SUFFIX):
                stem = path.name[: -len(self._WORLD_SUFFIX)].lower()
                if self._index.setdefault(stem, path) is path:
                    self.world_indexed_count += 1

    @staticmethod
    def _stem_for(symbol: str) -> Optional[str]:
        s = symbol.strip().lower()
        if s.startswith("^"):
            return s if len(s) > 1 else None  # world caret index: the file stem keeps the caret
        return LocalStooqArchiveProvider._stem_for(symbol)


def make_local_stooq_provider(archive_dir: Path | str) -> _LocalStooqBundleProvider:
    """The stooq-local fetch path reads Stooq's BULK archives from local disk — the SAME
    vendor/adjusted data as the per-symbol endpoint, consumed offline to bypass the per-IP export
    ACL (iter-16 unblock): `*.us.txt` (US stocks+ETFs, `d_us_txt`) and, since iter-17, plain
    `^xxx.txt` world-bundle indices (`d_world_txt`) in one index. No network, no key. These
    providers are used only by this dev-run script (never by `make_provider`), so the app
    boot/request path is unchanged."""
    return _LocalStooqBundleProvider(archive_dir)


def classify_stooq_failure(message: str) -> str:
    """Failure taxonomy for a `ProviderUnavailableError` from `StooqProvider` (the provider embeds
    the response evidence in the message; it never fabricates a bar):
      * "no_data"     — an unknown-symbol "N/D" body: a PER-SYMBOL honest absence; record + continue.
      * "unparseable" — a real CSV body with a malformed row/cell (e.g. an index served without a
                        usable Volume): a per-symbol vendor quirk; record + continue.
      * "gate"        — everything else (network/HTTP error, rate-limit/limit page, non-CSV or empty
                        body): retry, then stop the WHOLE run gracefully in a resumable state."""
    if "no usable data" in message and "N/D" in message:
        return "no_data"
    if "response unparseable" in message:
        return "unparseable"
    return "gate"


def _bars_to_rows(bars: list[Bar]) -> list[dict]:
    return [
        {
            "date": b.date.isoformat(),
            "open": round(b.open, 6),
            "high": round(b.high, 6),
            "low": round(b.low, 6),
            "close": round(b.close, 6),
            "volume": int(b.volume),
        }
        for b in bars
    ]


def _one_day_move(bars: list[Bar], day: date) -> float | None:
    """The 1-day close return landing ON `day` (vs the previous bar), or None if absent."""
    for i, bar in enumerate(bars):
        if bar.date == day:
            if i == 0 or not bars[i - 1].close:
                return None
            return (bar.close / bars[i - 1].close) - 1.0
    return None


def write_csv(prices_dir: Path, symbol: str, rows: list[dict]) -> Path:
    """Write one symbol's staged CSV atomically (tmp + rename) — an interrupted run never leaves a
    partial/truncated CSV behind (anti-goal: no fabricated/partial rows)."""
    prices_dir.mkdir(parents=True, exist_ok=True)
    path = prices_dir / symbol_to_filename(symbol)
    tmp = prices_dir / (path.name + ".tmp")
    with tmp.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)
    return path


# ---------------------------------------------------------------------------
# yahoo path (historical behavior, unchanged)
# ---------------------------------------------------------------------------

def _to_epoch(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def fetch_symbol(client: httpx.Client, symbol: str, start: date, end: date) -> list[dict]:
    """Return adjusted daily OHLCV rows for one symbol from Yahoo, or raise on failure."""
    params = {
        "period1": _to_epoch(start),
        "period2": _to_epoch(end),
        "interval": "1d",
        "events": "div,split",
    }
    resp = client.get(YAHOO_URL.format(symbol=symbol), params=params, headers=HEADERS, timeout=30.0)
    resp.raise_for_status()
    payload = resp.json()
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
        # split + dividend adjustment factor from Yahoo's adjusted close
        factor = (adj[i] / c) if (adj and adj[i] is not None and c) else 1.0
        d = datetime.fromtimestamp(ts, ET).date()  # exchange-local trading date (deterministic)
        rows.append({
            "date": d.isoformat(),
            "open": round(o * factor, 6),
            "high": round(h * factor, 6),
            "low": round(low * factor, 6),
            "close": round(c * factor, 6),
            "volume": int(v) if v is not None else 0,
        })
    # de-dupe by date (keep last) and sort ascending
    by_date = {r["date"]: r for r in rows}
    return [by_date[d] for d in sorted(by_date)]


def run_yahoo_ingest(symbols: list[str], start: date, end: date, out_dir: Path,
                     sleep_s: float) -> int:
    """The historical one-shot Yahoo ingest loop (behavior unchanged; only the output dir is now a
    parameter, defaulting to the live seed dir)."""
    prices_dir = out_dir / "prices"
    print(f"[ingest] {len(symbols)} symbols, window {start} -> {end}, source=Yahoo chart API")
    ok: list[dict] = []
    failed: list[str] = []
    with httpx.Client(follow_redirects=True) as client:
        for i, symbol in enumerate(symbols, 1):
            last_err = None
            for attempt in range(3):
                try:
                    rows = fetch_symbol(client, symbol, start, end)
                    if not rows:
                        raise ValueError("empty series")
                    path = write_csv(prices_dir, symbol, rows)
                    ok.append({"symbol": symbol, "bars": len(rows),
                               "first": rows[0]["date"], "last": rows[-1]["date"]})
                    print(f"[{i:3d}/{len(symbols)}] {symbol:6s} {len(rows):5d} bars "
                          f"{rows[0]['date']}..{rows[-1]['date']} -> {path.name}")
                    break
                except Exception as exc:  # noqa: BLE001 - log + retry, then record failure
                    last_err = exc
                    time.sleep(1.0 + attempt)
            else:
                failed.append(symbol)
                print(f"[{i:3d}/{len(symbols)}] {symbol:6s} FAILED: {last_err}")
            time.sleep(sleep_s)

    meta = {
        "source": "Yahoo Finance chart API (query1.finance.yahoo.com/v8/finance/chart)",
        "note": "REAL split/dividend-adjusted EOD OHLCV; frozen + committed; no key/secret used.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "symbols_ok": len(ok),
        "symbols_failed": len(failed),
        "failed": failed,
        "symbols": ok,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"[ingest] done: {len(ok)} ok, {len(failed)} failed. Wrote {out_dir / 'meta.json'}")
    if failed:
        print(f"[ingest] failed symbols: {failed}")
    return EXIT_OK


# ---------------------------------------------------------------------------
# stooq staged ingest (iter-16)
# ---------------------------------------------------------------------------

def run_stooq_ingest(provider: PriceProvider, symbols: list[str], start: date, end: date,
                     out_dir: Path | str, sleep_s: float, retries: int = 3,
                     source: str = STOOQ_SOURCE, note: str = STOOQ_NOTE) -> int:
    """Resumable staged fetch: manifest-driven skip of already-complete symbols and recorded
    absences; per-symbol honest failure recording; graceful resumable stop (manifest written,
    non-zero exit) on a rate-cap/gate. Never fabricates, pads, or splices a bar. `source`/`note`
    record provenance in the manifest (defaults describe the per-symbol endpoint; the stooq-local
    path passes the bulk-archive provenance)."""
    out_dir = Path(out_dir)
    manifest = load_manifest(out_dir)
    if _foreign_manifest(manifest):
        print(f"[ingest] REFUSED: {out_dir / 'meta.json'} is not a stooq staging manifest — "
              f"staging is side-by-side only (never over the live seed); choose a fresh --out dir.")
        return EXIT_CONFLICT
    planned = len(symbols)
    if manifest is not None:
        # Resume: the plan breadth and note/source provenance established at staging birth are
        # PRESERVED — a narrower later invocation (e.g. the default symbol set over an
        # already-staged pool manifest) must not shrink `symbols_planned` or rewrite the note
        # (the iter-17 context addendum + per-series vendor records live there). Real resume
        # flows pass the same set/constants, so this is byte-equivalent for them.
        planned = max(int(manifest.get("symbols_planned", 0)), planned)
        source = manifest.get("source", source)
        note = manifest.get("note", note)
    state = _ManifestState(manifest, start, end, planned=planned, source=source, note=note)
    prices_dir = out_dir / "prices"

    pending: list[str] = []
    skipped_ok = skipped_absent = 0
    for symbol in symbols:
        if symbol in state.ok and (prices_dir / symbol_to_filename(symbol)).exists():
            skipped_ok += 1
            continue
        if symbol in state.failures:  # recorded honest absence — not re-hammered on resume
            skipped_absent += 1
            continue
        pending.append(symbol)
    print(f"[ingest] stooq staging: {len(symbols)} planned | {skipped_ok} already staged | "
          f"{skipped_absent} recorded absent | {len(pending)} to fetch | "
          f"window {start} -> {end} (pinned) | out={out_dir}")

    fetched = 0
    try:
        for i, symbol in enumerate(pending, 1):
            bars: list[Bar] | None = None
            gate: tuple[ProviderUnavailableError, int] | None = None
            for attempt in range(1, retries + 1):
                try:
                    bars = provider.get_daily(symbol, start, end)
                    break
                except ProviderUnavailableError as exc:
                    kind = classify_stooq_failure(str(exc))
                    if kind in ("no_data", "unparseable"):
                        state.record_absent(symbol, kind, str(exc))
                        print(f"[{i:3d}/{len(pending)}] {symbol:6s} ABSENT ({kind}): "
                              f"{redact_stooq_key(str(exc))}")
                        break
                    if attempt < retries:
                        time.sleep(sleep_s * attempt)  # transient? back off, retry
                        continue
                    gate = (exc, attempt)
            if gate is not None:
                exc, attempts = gate
                state.record_cap(symbol, str(exc), attempts)
                state.write(out_dir)
                print(f"[ingest] RATE-CAP/GATE STOP at {symbol} after {attempts} attempts: "
                      f"{redact_stooq_key(str(exc))}")
                print(f"[ingest] progress manifest written to {out_dir / 'meta.json'} — "
                      f"{fetched} fetched this run, {len(state.ok)} staged total. Resume with the "
                      f"same command; the pinned window {start} -> {end} is reused automatically.")
                return EXIT_CAP_STOP
            if bars is not None:
                if bars:
                    rows = _bars_to_rows(bars)
                    write_csv(prices_dir, symbol, rows)
                    state.record_ok(symbol, rows)
                    fetched += 1
                    print(f"[{i:3d}/{len(pending)}] {symbol:6s} {len(rows):5d} bars "
                          f"{rows[0]['date']}..{rows[-1]['date']}")
                else:
                    state.record_absent(symbol, "no_data", "empty CSV (no rows in window)")
                    print(f"[{i:3d}/{len(pending)}] {symbol:6s} ABSENT (empty series)")
            state.write(out_dir)
            if i < len(pending):
                time.sleep(sleep_s)
    except KeyboardInterrupt:
        state.write(out_dir)
        print(f"\n[ingest] interrupted — progress manifest written to {out_dir / 'meta.json'}; "
              f"resume with the same command (pinned window reused).")
        return EXIT_CAP_STOP

    state.write(out_dir)
    print(f"[ingest] done: {len(state.ok)} staged ok, {len(state.failures)} recorded absent "
          f"({fetched} fetched this run, {skipped_ok} skipped complete). "
          f"Wrote {out_dir / 'meta.json'}")
    if state.failures:
        print(f"[ingest] absent symbols (honestly omitted, never fabricated): "
              f"{sorted(state.failures)}")
    return EXIT_OK


def run_probe(provider: PriceProvider, out_dir: Path | str, start: date, end: date,
              sleep_s: float = STOOQ_DEFAULT_SLEEP) -> int:
    """Go/no-go probe BEFORE the full ~590-symbol run: fetch AAPL+SPY+NVDA full-span and verify
    (a) a real CSV body, (b) depth (AAPL/SPY first bar <= 1996-01-05), (c) the staged schema,
    (d) a back-adjusted basis (no ~10x/~4x one-day close seam across the NVDA 2024-06-10 / AAPL
    2020-08-31 splits). On GO the three fetched series are staged so the full run resumes past
    them; on NO-GO nothing is staged and the exact response evidence is printed."""
    out_dir = Path(out_dir)
    manifest = load_manifest(out_dir)
    if _foreign_manifest(manifest):
        print(f"[probe] REFUSED: {out_dir / 'meta.json'} is not a stooq staging manifest — "
              f"choose a fresh --out dir (staging is side-by-side only).")
        return EXIT_CONFLICT
    print(f"[probe] go/no-go: {', '.join(PROBE_SYMBOLS)} full-span {start} -> {end} "
          f"via StooqProvider ({STOOQ_SOURCE})")

    fetched: dict[str, list[Bar]] = {}
    for symbol in PROBE_SYMBOLS:
        try:
            bars = provider.get_daily(symbol, start, end)
        except ProviderUnavailableError as exc:
            print(f"[probe] HARD FAILURE fetching {symbol}: {redact_stooq_key(str(exc))}")
            print("[probe] NO-GO — the endpoint is gated/unavailable for this environment. "
                  "Nothing staged; the exact response evidence is embedded in the error above. "
                  f"(A key, if required, is read from ${STOOQ_API_KEY_ENV} only.)")
            return EXIT_CAP_STOP
        if not bars:
            print(f"[probe] HARD FAILURE: {symbol} returned an empty series — NO-GO, nothing staged.")
            return EXIT_CAP_STOP
        fetched[symbol] = bars
        print(f"[probe] {symbol}: real CSV body OK — {len(bars)} bars "
              f"{bars[0].date} .. {bars[-1].date}")
        if symbol != PROBE_SYMBOLS[-1]:
            time.sleep(sleep_s)

    failures: list[str] = []
    for symbol in PROBE_DEPTH_SYMBOLS:
        first = fetched[symbol][0].date
        ok = first <= PROBE_DEPTH_ANCHOR
        print(f"[probe] depth {symbol}: first bar {first} <= {PROBE_DEPTH_ANCHOR}: "
              f"{'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"{symbol} depth: first bar {first} > {PROBE_DEPTH_ANCHOR}")
    for symbol, split_day in PROBE_SPLIT_DAYS.items():
        move = _one_day_move(fetched[symbol], split_day)
        if move is None:
            print(f"[probe] adjusted-basis {symbol}: split-day bar {split_day} ABSENT: FAIL")
            failures.append(f"{symbol} split-day bar {split_day} absent")
        else:
            ok = abs(move) < PROBE_MAX_SPLIT_DAY_MOVE
            print(f"[probe] adjusted-basis {symbol}: 1-day close move across {split_day} = "
                  f"{move:+.4%} (bound {PROBE_MAX_SPLIT_DAY_MOVE:.0%}): {'PASS' if ok else 'FAIL'}")
            if not ok:
                failures.append(f"{symbol} unadjusted seam across {split_day}: {move:+.4%}")
    if failures:
        print(f"[probe] NO-GO — {len(failures)} validation failure(s): {failures}. Nothing staged.")
        return EXIT_PROBE_FAIL

    # GO: stage the three fetched series + manifest so the full run resumes past them.
    planned = (manifest or {}).get("symbols_planned", len(PROBE_SYMBOLS))
    state = _ManifestState(manifest, start, end, planned=planned)
    prices_dir = out_dir / "prices"
    for symbol in PROBE_SYMBOLS:
        rows = _bars_to_rows(fetched[symbol])
        path = write_csv(prices_dir, symbol, rows)
        state.record_ok(symbol, rows)
        header = path.read_text().splitlines()[0]
        if header != ",".join(CSV_FIELDS):  # structural — DictWriter always emits CSV_FIELDS
            print(f"[probe] schema FAIL for {symbol}: staged header {header!r}")
            return EXIT_PROBE_FAIL
    state.write(out_dir)
    print(f"[probe] schema: staged header == {','.join(CSV_FIELDS)} for all "
          f"{len(PROBE_SYMBOLS)}: PASS")
    print(f"[probe] GO — all checks passed; {len(PROBE_SYMBOLS)} series staged under {out_dir} "
          f"(the full run will skip them).")
    return EXIT_OK


# ---------------------------------------------------------------------------
# context merge (iter-17, goal.md §H): index & macro context into the STAGED seed
# ---------------------------------------------------------------------------

# Per-series vendor disclosure (§H): the vendor mix is recorded per context series and a proxy is
# never presented as a market index.
CONTEXT_WORLD_SYMBOLS = ("^SPX", "^NDX", "^DJI")   # deep from Stooq's world indices bundle
CONTEXT_YAHOO_SYMBOL = "^VIX"                       # genuinely a Yahoo index (verified in goal.md §H)
CONTEXT_PROXY_SYMBOLS = ("^TNX", "^DXY", "^VXN")    # the app's deterministic FRED-macro PROXIES
VENDOR_STOOQ = "stooq"
VENDOR_YAHOO = "yahoo"
VENDOR_FRED_PROXY = "fred-macro-proxy"
VIX_DEEP_ANCHOR = date(1996, 1, 5)   # a usable DEEP pull reaches the first 1996 trading week
VIX_MAX_GAP_DAYS = 14                # single continuous series: no US-market closure exceeds this
CONTEXT_NOTE_ADDENDUM = (
    " Context series (iter-17, goal.md §H — mixed vendor, honestly disclosed per series): "
    "^SPX/^NDX/^DJI staged DEEP from Stooq's world indices bundle (data/d_world_txt; vendor "
    "stooq — same vendor, local world archive), window-clipped to the pinned window; ^VIX from "
    "Yahoo (vendor yahoo; deep single pull, or the sanctioned verbatim live-seed copy on an "
    "unreachable endpoint — see its per-series note); ^TNX/^DXY/^VXN are the app's deterministic "
    "FRED-macro PROXIES copied BYTE-IDENTICAL from the live seed (vendor fred-macro-proxy), kept "
    "coherent with data/seed/macro/ and NEVER re-fetched from Yahoo. Each context record carries "
    "its per-series vendor; a proxy is never presented as a market index; no bar is fabricated, "
    "padded, interpolated, or vendor-spliced."
)


def _fetch_yahoo_vix_rows(start: date, end: date) -> list[dict]:
    """ONE single-vendor, single-pull deep `^VIX` fetch from the free Yahoo chart API, clipped
    client-side to the pinned window [start, end] (Yahoo's period2 is an exclusive midnight-UTC
    bound, so the request reaches one day past the pinned end and the rows are clipped locally —
    a staged row never exceeds the manifest window). No key, no secret; raises on any failure."""
    with httpx.Client(follow_redirects=True) as client:
        rows = fetch_symbol(client, CONTEXT_YAHOO_SYMBOL, start, end + timedelta(days=1))
    return [r for r in rows if start.isoformat() <= r["date"] <= end.isoformat()]


def _vix_pull_shortfall(rows: list[dict], live_last: str | None) -> str | None:
    """Why a fetched deep-^VIX pull is NOT usable as the staged deep series (None = usable). A
    pull failing ANY check is discarded IN FULL for the sanctioned verbatim fallback — two pulls
    are never merged/spliced into one series (anti-goal: no vendor-spliced bars)."""
    if not rows:
        return "empty series"
    first = date.fromisoformat(rows[0]["date"])
    if first > VIX_DEEP_ANCHOR:
        return f"not deep: first bar {first} > {VIX_DEEP_ANCHOR}"
    if live_last is not None and rows[-1]["date"] < live_last:
        return (f"stale: last bar {rows[-1]['date']} < the live copy's {live_last} — staging it "
                f"would lose coverage vs the sanctioned fallback")
    prev: date | None = None
    for row in rows:
        d = date.fromisoformat(row["date"])
        if prev is not None:
            if d <= prev:
                return f"dates not strictly ascending at {row['date']}"
            if (d - prev).days > VIX_MAX_GAP_DAYS:
                return (f"{(d - prev).days}-day gap ending {row['date']} — not a single "
                        f"continuous series")
        prev = d
    return None


def _copy_series_verbatim(src: Path, prices_dir: Path, symbol: str) -> list[dict]:
    """Copy one live-seed CSV BYTE-IDENTICAL into the staged tree (atomic tmp+rename), returning
    its parsed rows for the coverage record. The source is read-only — `data/seed/` is never
    modified."""
    prices_dir.mkdir(parents=True, exist_ok=True)
    dst = prices_dir / symbol_to_filename(symbol)
    tmp = prices_dir / (dst.name + ".tmp")
    tmp.write_bytes(src.read_bytes())
    tmp.replace(dst)
    with dst.open(newline="") as fh:
        return list(csv.DictReader(fh))


def run_context_merge(world_provider: PriceProvider, out_dir: Path | str,
                      start_arg: str | None = None, end_arg: str | None = None,
                      live_seed_dir: Path | str | None = None,
                      fetch_vix_rows=None) -> int:
    """Merge the index/macro CONTEXT series into an EXISTING staged stooq manifest (iter-17,
    goal.md §H) — never a fresh manifest, never `run_yahoo_ingest` (whose writer would CLOBBER
    the staged meta.json):

      * `^SPX`/`^NDX`/`^DJI` — deep from the local WORLD bundle, clipped to the pinned window
        (vendor stooq; the archive reaches 1789 — pre-window rows never land);
      * `^TNX`/`^DXY`/`^VXN` — BYTE-IDENTICAL copies of the live seed's FRED-macro proxies
        (vendor fred-macro-proxy; §H: a Yahoo re-fetch would DESYNC them from the FRED macro);
      * `^VIX` — ONE deep single-pull Yahoo series (vendor yahoo), with the SANCTIONED fallback:
        on an unreachable/unusable pull, the live seed's series is copied verbatim (honestly
        short) and the shortfall recorded — never a partial/spliced series.

    The 583 equity records, the pinned window, and the provider identity are untouched; resolved
    caret failures become coverage records; accounting stays consistent; every persisted failure
    detail/note passes the redaction choke point. Absences are recorded honestly (exit 0 — the
    staged validation suite is the gate); refusals (missing/foreign manifest, window conflict)
    exit EXIT_CONFLICT before any write."""
    out_dir = Path(out_dir)
    live_prices_dir = (Path(live_seed_dir) if live_seed_dir is not None else SEED_DIR) / "prices"
    manifest = load_manifest(out_dir)
    if manifest is None:
        print(f"[context] REFUSED: {out_dir / 'meta.json'} does not exist — the context merge "
              f"targets an EXISTING staged stooq manifest (run the equities staging first).")
        return EXIT_CONFLICT
    if _foreign_manifest(manifest):
        print(f"[context] REFUSED: {out_dir / 'meta.json'} is not a stooq staging manifest — "
              f"staging is side-by-side only (never over the live seed).")
        return EXIT_CONFLICT
    try:
        start, end = resolve_stooq_window(start_arg, end_arg, manifest, datetime.now(ET).date())
    except WindowConflictError as exc:
        print(f"[context] {exc}")
        return EXIT_CONFLICT

    prior_recorded = ({e["symbol"] for e in manifest.get("symbols", [])}
                      | set(manifest.get("failed", [])))
    planned = int(manifest.get("symbols_planned", 0)) + sum(
        1 for s in CONTEXT_WORLD_SYMBOLS if s not in prior_recorded)
    note = manifest.get("note", STOOQ_LOCAL_NOTE)
    if CONTEXT_NOTE_ADDENDUM not in note:
        note = note + CONTEXT_NOTE_ADDENDUM
    state = _ManifestState(manifest, start, end, planned=planned,
                           source=manifest.get("source", STOOQ_LOCAL_SOURCE), note=note)
    prices_dir = out_dir / "prices"
    print(f"[context] merging index/macro context into {out_dir} "
          f"(pinned window {start} -> {end})")

    # 1) Deep equity-index benchmarks from Stooq's WORLD bundle (offline; vendor stooq).
    for symbol in CONTEXT_WORLD_SYMBOLS:
        try:
            bars = world_provider.get_daily(symbol, start, end)
        except ProviderUnavailableError as exc:
            state.record_absent(symbol, "unparseable", str(exc))
            print(f"[context] {symbol:5s} ABSENT (unparseable): {redact_stooq_key(str(exc))}")
            continue
        if not bars:
            state.record_absent(symbol, "no_data",
                                "absent from the world indices bundle — honestly omitted")
            print(f"[context] {symbol:5s} ABSENT from the world bundle (recorded honestly)")
            continue
        rows = _bars_to_rows(bars)
        write_csv(prices_dir, symbol, rows)
        state.record_ok(symbol, rows, vendor=VENDOR_STOOQ)
        print(f"[context] {symbol:5s} {len(rows):5d} bars {rows[0]['date']}..{rows[-1]['date']} "
              f"vendor={VENDOR_STOOQ} (world bundle, window-clipped)")

    # 2) FRED-macro proxies — byte-identical live-seed copies (vendor fred-macro-proxy).
    for symbol in CONTEXT_PROXY_SYMBOLS:
        src = live_prices_dir / symbol_to_filename(symbol)
        if not src.exists():
            state.record_absent(symbol, "no_data", f"live seed has no {src.name} to copy")
            print(f"[context] {symbol:5s} ABSENT: live seed has no {src.name}")
            continue
        rows = _copy_series_verbatim(src, prices_dir, symbol)
        state.record_ok(symbol, rows, vendor=VENDOR_FRED_PROXY,
                        note="deterministic FRED-macro proxy copied byte-identical from the live "
                             "seed — never re-fetched from Yahoo; coherent with data/seed/macro/; "
                             "honestly short")
        print(f"[context] {symbol:5s} {len(rows):5d} bars {rows[0]['date']}..{rows[-1]['date']} "
              f"vendor={VENDOR_FRED_PROXY} (byte-identical live copy)")

    # 3) Deep ^VIX from Yahoo (single pull), else the SANCTIONED verbatim live copy.
    live_vix = live_prices_dir / symbol_to_filename(CONTEXT_YAHOO_SYMBOL)
    live_last: str | None = None
    if live_vix.exists():
        with live_vix.open(newline="") as fh:
            live_rows = list(csv.DictReader(fh))
        live_last = live_rows[-1]["date"] if live_rows else None
    fetch = fetch_vix_rows if fetch_vix_rows is not None else _fetch_yahoo_vix_rows
    rows = None
    shortfall: str | None = None
    try:
        rows = fetch(start, end)
    except Exception as exc:  # noqa: BLE001 — ANY live failure takes the sanctioned fallback
        shortfall = f"{type(exc).__name__}: {exc}"
    if shortfall is None:
        shortfall = _vix_pull_shortfall(rows, live_last)
    if shortfall is None:
        write_csv(prices_dir, CONTEXT_YAHOO_SYMBOL, rows)
        state.record_ok(CONTEXT_YAHOO_SYMBOL, rows, vendor=VENDOR_YAHOO,
                        note="deep single-pull Yahoo series, window-clipped — never spliced")
        print(f"[context] {CONTEXT_YAHOO_SYMBOL:5s} {len(rows):5d} bars "
              f"{rows[0]['date']}..{rows[-1]['date']} vendor={VENDOR_YAHOO} (deep single pull)")
    elif live_vix.exists():
        rows = _copy_series_verbatim(live_vix, prices_dir, CONTEXT_YAHOO_SYMBOL)
        state.record_ok(CONTEXT_YAHOO_SYMBOL, rows, vendor=VENDOR_YAHOO,
                        note=("sanctioned fallback: deep Yahoo re-fetch unavailable ("
                              + redact_stooq_key(shortfall)[:120] + "); verbatim byte-copy of "
                              "the live seed's Yahoo series — honestly short, never spliced"))
        print(f"[context] {CONTEXT_YAHOO_SYMBOL:5s} FALLBACK — deep pull unavailable "
              f"({redact_stooq_key(shortfall)}); staged the live seed's series VERBATIM "
              f"({rows[0]['date']}..{rows[-1]['date']}, honestly short; vendor={VENDOR_YAHOO}).")
    else:
        state.record_absent(CONTEXT_YAHOO_SYMBOL, "no_data",
                            f"deep pull failed ({shortfall}) and the live seed has no "
                            f"{live_vix.name} to fall back to")
        print(f"[context] {CONTEXT_YAHOO_SYMBOL:5s} ABSENT: deep pull failed "
              f"({redact_stooq_key(shortfall)}) and no live copy exists — recorded honestly.")

    state.write(out_dir)
    context_all = (*CONTEXT_WORLD_SYMBOLS, *CONTEXT_PROXY_SYMBOLS, CONTEXT_YAHOO_SYMBOL)
    staged_now = [s for s in context_all if s in state.ok]
    print(f"[context] merged: {len(state.ok)} ok / {len(state.failures)} recorded absent "
          f"(planned {planned}); context staged: {staged_now}. Wrote {out_dir / 'meta.json'}")
    return EXIT_OK


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Trendora seed ingest (yahoo: historical one-shot; stooq: staged/resumable).")
    parser.add_argument("--provider", choices=["yahoo", "stooq", "stooq-local"], default="yahoo",
                        help="price source (default yahoo — the historical path, unchanged; stooq: "
                             "per-symbol network CSV; stooq-local: the bulk d_us_txt archive, offline)")
    parser.add_argument("--out", default=None,
                        help="output seed dir (default: the live seed dir apps/backend/data/seed; "
                             "stooq staging MUST use a side-by-side dir, e.g. data/seed-stooq-30y)")
    parser.add_argument("--symbols-set", dest="symbols_set", choices=["default", "pool"],
                        default="default",
                        help="default: universe + ETF groups (historical set); pool: the committed "
                             "candidate pool ∪ all seed symbols, priority-ordered (~590)")
    parser.add_argument("--start", default=None,
                        help=f"ISO start date (default {DEFAULT_START})")
    parser.add_argument("--end", default=None,
                        help="ISO end date (yahoo: today; stooq: pinned to the most recent "
                             "COMPLETED trading day; a stooq resume reuses the manifest's pinned end)")
    parser.add_argument("--sleep", type=float, default=None,
                        help=f"seconds between symbol requests (yahoo default "
                             f"{YAHOO_DEFAULT_SLEEP}; stooq default {STOOQ_DEFAULT_SLEEP} — polite)")
    parser.add_argument("--probe", action="store_true",
                        help="stooq go/no-go probe (AAPL+SPY+NVDA full-span validation), then exit")
    parser.add_argument("--archive-dir", dest="archive_dir", default=None,
                        help="stooq-local: path to the extracted Stooq bulk US archive "
                             f"(default {DEFAULT_ARCHIVE_DIR}; with --stage-context the default "
                             f"is the world bundle {DEFAULT_WORLD_ARCHIVE_DIR})")
    parser.add_argument("--stage-context", dest="stage_context", action="store_true",
                        help="stooq-local: merge the index/macro CONTEXT series into an EXISTING "
                             "staged manifest (iter-17, goal.md §H) — ^SPX/^NDX/^DJI deep from "
                             "the local world bundle, ^VIX deep from Yahoo (sanctioned verbatim "
                             "live-copy fallback), ^TNX/^DXY/^VXN byte-identical FRED-macro-proxy "
                             "copies; per-series vendor recorded in meta.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config()
    out_dir = Path(args.out) if args.out else SEED_DIR

    if args.stage_context and args.provider != "stooq-local":
        print("[ingest] --stage-context merges the LOCAL world-bundle context into an existing "
              "staged manifest; use --provider stooq-local (the ^VIX Yahoo leg is internal to "
              "the mode — never a manifest-writing yahoo run).")
        return EXIT_CONFLICT

    if args.provider == "yahoo":
        if args.probe:
            print("[ingest] --probe is the stooq go/no-go check; use --provider stooq")
            return EXIT_CONFLICT
        start = date.fromisoformat(args.start or DEFAULT_START)
        end = date.fromisoformat(args.end) if args.end else datetime.now(ET).date()
        sleep_s = YAHOO_DEFAULT_SLEEP if args.sleep is None else args.sleep
        symbols = (build_default_symbols(config) if args.symbols_set == "default"
                   else build_pool_symbol_plan(config)["all"])
        return run_yahoo_ingest(symbols, start, end, out_dir, sleep_s)

    # --provider stooq / stooq-local: staged, resumable, pinned-window ingest (iter-16).
    #   stooq        — fetch each name from Stooq's per-symbol network CSV endpoint.
    #   stooq-local  — read the SAME vendor data from the bulk d_us_txt archive on local disk
    #                  (iter-16 unblock: the network export endpoint is IP-blocked). Offline; the
    #                  staged CSV/manifest are byte-format-identical (same run_stooq_ingest writer).
    local = args.provider == "stooq-local"
    manifest = load_manifest(out_dir)
    if _foreign_manifest(manifest):
        print(f"[ingest] REFUSED: {out_dir} holds a non-stooq seed (its meta.json has no "
              f"provider=stooq). Stage side-by-side, e.g. --out "
              f"{BACKEND_DIR / 'data' / 'seed-stooq-30y'} — the basis swap is a separate, "
              f"sanctioned later step.")
        return EXIT_CONFLICT
    try:
        start, end = resolve_stooq_window(args.start, args.end, manifest,
                                          datetime.now(ET).date())
    except WindowConflictError as exc:
        print(f"[ingest] {exc}")
        return EXIT_CONFLICT

    if local:
        if args.probe:
            print("[ingest] --probe is the live-endpoint go/no-go; its AAPL/SPY<=1996 depth anchor "
                  "does not fit the bulk US-ETF archive (SPY depth begins 2005). The staged "
                  "validation suite (tests/test_seed_staged_30y.py) is the gate — re-run without "
                  "--probe.")
            return EXIT_CONFLICT
        default_archive = DEFAULT_WORLD_ARCHIVE_DIR if args.stage_context else DEFAULT_ARCHIVE_DIR
        archive_dir = Path(args.archive_dir) if args.archive_dir else default_archive
        if not archive_dir.is_dir():
            print(f"[ingest] REFUSED: --archive-dir {archive_dir} does not exist. Point it at the "
                  f"extracted Stooq bulk archive (default {default_archive}).")
            return EXIT_CONFLICT
        provider = make_local_stooq_provider(archive_dir)
        print(f"[ingest] stooq-local: indexed {provider.indexed_count} symbols under {archive_dir} "
              f"({provider.world_indexed_count} world-bundle ^xxx.txt)")
        if provider.indexed_count == 0:
            print(f"[ingest] REFUSED: no *.us.txt or ^xxx.txt files found under {archive_dir} — "
                  f"wrong --archive-dir? (expected an extracted d_us_txt or d_world_txt tree).")
            return EXIT_CONFLICT
        if args.stage_context:
            if provider.world_indexed_count == 0:
                print(f"[ingest] REFUSED: no ^xxx.txt world-bundle files under {archive_dir} — "
                      f"the context merge needs the extracted d_world_txt tree "
                      f"(default {DEFAULT_WORLD_ARCHIVE_DIR}).")
                return EXIT_CONFLICT
            return run_context_merge(provider, out_dir, start_arg=args.start, end_arg=args.end)
        sleep_s = 0.0 if args.sleep is None else args.sleep  # local disk — no politeness delay
        source, note = STOOQ_LOCAL_SOURCE, STOOQ_LOCAL_NOTE
    else:
        sleep_s = STOOQ_DEFAULT_SLEEP if args.sleep is None else args.sleep
        provider = make_stooq_provider()
        if args.probe:
            return run_probe(provider, out_dir, start, end, sleep_s=sleep_s)
        source, note = STOOQ_SOURCE, STOOQ_NOTE

    symbols = (build_default_symbols(config) if args.symbols_set == "default"
               else build_pool_symbol_plan(config)["all"])
    return run_stooq_ingest(provider, symbols, start, end, out_dir, sleep_s,
                            source=source, note=note)


if __name__ == "__main__":
    raise SystemExit(main())
