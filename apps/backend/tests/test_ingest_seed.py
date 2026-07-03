"""Iter-16 ingest tooling tests — `scripts/ingest_seed.py` grows `--provider stooq`, `--out`,
`--symbols-set pool`, a pinned-end manifest, priority ordering, resume-skip, and a graceful
rate-cap stop. ALL offline (a stubbed injected httpx client — `StooqProvider` is client-injectable);
the one real-network check for this iteration is the live probe run documented in the dev handoff.

Honesty contract under test (anti-goal: No fabricated data):
  * a rate-limit / limit-page / non-CSV body stops the run GRACEFULLY (manifest written, non-zero
    exit) with NO partial or fabricated CSV row;
  * an unknown-symbol "N/D" is recorded as an honest failure and the run CONTINUES (the symbol is
    simply omitted — never padded);
  * resume runs REUSE the manifest's pinned end (one consistent window bound) and fetch ONLY the
    symbols not yet complete;
  * the default Yahoo invocation (no flags) keeps its current behavior byte-compatibly.
"""
from __future__ import annotations

import json
from datetime import date, timedelta

import httpx
import pytest

from app.data_providers.base import ProviderUnavailableError
from app.data_providers.local_stooq_archive import LocalStooqArchiveProvider
from app.data_providers.stooq_provider import StooqProvider
from scripts.ingest_seed import (
    CSV_FIELDS,
    DEFAULT_START,
    EXIT_CAP_STOP,
    EXIT_CONFLICT,
    EXIT_PROBE_FAIL,
    STOOQ_API_KEY_ENV,
    WindowConflictError,
    _POW_MAX_ITERATIONS,
    _StooqVerifyClient,
    _solve_stooq_pow,
    build_default_symbols,
    build_parser,
    build_pool_symbol_plan,
    classify_stooq_failure,
    load_manifest,
    main,
    make_local_stooq_provider,
    make_stooq_provider,
    most_recent_completed_trading_day,
    resolve_stooq_window,
    run_context_merge,
    run_probe,
    run_stooq_ingest,
)

# ---------------------------------------------------------------------------
# stub client (the StooqProvider injection seam) + canned bodies
# ---------------------------------------------------------------------------

_VALID_CSV = (
    "Date,Open,High,Low,Close,Volume\n"
    "2024-01-02,185.0,186.0,184.0,185.5,1000\n"
    "2024-01-03,186.0,188.0,185.0,187.25,1200\n"
    "2024-01-04,187.0,187.5,183.0,184.0,1500\n"
)
_LIMIT_PAGE = "Exceeded the daily hits limit"  # Stooq's rate-cap body (non-CSV)


class _FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self) -> None:  # canned 200
        return None


class _FakeStooqClient:
    """Keyed stub: `bodies` maps the requested stooq symbol (params['s']) to a canned CSV body or an
    exception to raise. An UNEXPECTED symbol request is a test failure (proves e.g. that a symbol
    after a cap-stop is never requested)."""

    def __init__(self, bodies: dict[str, str | Exception]):
        self.bodies = bodies
        self.calls: list[dict] = []

    def get(self, url, params=None, timeout=None):
        self.calls.append(dict(params or {}))
        key = (params or {}).get("s")
        if key not in self.bodies:
            raise AssertionError(f"unexpected stooq request for {key!r}")
        body = self.bodies[key]
        if isinstance(body, Exception):
            raise body
        return _FakeResponse(body)

    def requested(self) -> list[str]:
        return [c.get("s") for c in self.calls]


def _stooq_body(rows) -> str:
    return "Date,Open,High,Low,Close,Volume\n" + "".join(
        f"{d},{o},{h},{l},{c},{v}\n" for (d, o, h, l, c, v) in rows
    )


# full-span probe fixtures: real-shaped depth anchors + the two split-continuity days
_AAPL_FULLSPAN = _stooq_body([
    ("1996-01-02", 0.24, 0.25, 0.23, 0.2425, 400000000),
    ("2020-08-28", 124.0, 125.0, 123.0, 124.81, 100000),
    ("2020-08-31", 127.0, 130.0, 126.0, 129.04, 120000),  # 4:1 split day — adjusted ⇒ small move
    ("2026-06-30", 210.0, 212.0, 208.0, 211.0, 90000),
])
_SPY_FULLSPAN = _stooq_body([
    ("1996-01-02", 45.0, 45.5, 44.8, 45.2, 1000000),
    ("2026-06-30", 610.0, 612.0, 605.0, 611.5, 50000000),
])
_NVDA_FULLSPAN = _stooq_body([
    ("1999-01-22", 0.04, 0.05, 0.039, 0.041, 2000000),
    ("2024-06-07", 120.0, 121.5, 118.0, 120.89, 300000),
    ("2024-06-10", 121.0, 123.0, 119.0, 121.79, 310000),  # 10:1 split day — adjusted ⇒ small move
    ("2026-06-30", 170.0, 172.0, 168.0, 171.2, 200000),
])


# ---------------------------------------------------------------------------
# symbol sets
# ---------------------------------------------------------------------------

def test_default_symbol_set_unchanged(config):
    """The default symbol set is byte-identical to the pre-iter-16 builder: universe + the four ETF
    groups, de-duplicated and order-preserving — NO legend/macro-proxy additions (that widening
    exists only under --symbols-set pool)."""
    expected: list[str] = []
    expected += list(config.universe.symbols)
    expected += list(config.etfs.index)
    expected += list(config.etfs.sector.keys())
    expected += list(config.etfs.industry)
    expected += list(config.etfs.volatility)
    seen: set[str] = set()
    expected = [s for s in expected if not (s in seen or seen.add(s))]

    got = build_default_symbols(config)
    assert got == expected
    assert "DIA" not in got and "^TNX" not in got  # legend/macro proxies stay OUT of the default


def test_pool_symbol_plan_priority_order(config):
    """--symbols-set pool = pool ∪ all_seed_symbols, priority-ordered: tier1 benchmarks/controls
    (index/sector/industry/volatility ETFs, ^VIX, legend, macro proxies), tier2 the current universe
    symbols, tier3 the remaining pool names alphabetical. No duplicates across tiers."""
    plan = build_pool_symbol_plan(config)
    tier1, tier2, tier3 = plan["tier1"], plan["tier2"], plan["tier3"]

    # tier1 leads with the index ETFs (SPY/QQQ first) and carries every control set
    assert tier1[: len(config.etfs.index)] == list(config.etfs.index)
    assert set(config.etfs.sector.keys()) <= set(tier1)
    assert set(config.etfs.industry) <= set(tier1)
    assert "^VIX" in tier1
    assert "DIA" in tier1  # index-chart legend symbol
    assert {"^TNX", "^VXN", "^DXY"} <= set(tier1)  # macro proxies
    assert not (set(tier1) & set(config.universe.symbols))

    # tier2 is exactly the current universe
    assert tier2 == list(config.universe.symbols)

    # tier3: remaining pool names, alphabetical, disjoint from tiers 1-2
    assert tier3 == sorted(tier3)
    assert not (set(tier3) & (set(tier1) | set(tier2)))
    assert "AAPL" not in tier3  # a universe member fetches in tier2, not tier3

    ordered = plan["all"]
    assert ordered == tier1 + tier2 + tier3
    assert len(ordered) == len(set(ordered))
    assert len(ordered) >= 580  # ~548 pool ∪ ~40 non-universe controls ≈ ~590


# ---------------------------------------------------------------------------
# pinned end + manifest window reuse
# ---------------------------------------------------------------------------

def test_most_recent_completed_trading_day():
    assert most_recent_completed_trading_day(date(2026, 7, 1)) == date(2026, 6, 30)  # Wed -> Tue
    assert most_recent_completed_trading_day(date(2026, 7, 6)) == date(2026, 7, 3)   # Mon -> Fri
    assert most_recent_completed_trading_day(date(2026, 7, 5)) == date(2026, 7, 3)   # Sun -> Fri


def test_resolve_stooq_window_pins_end_and_reuses_manifest():
    today = date(2026, 7, 1)
    # fresh run: end pins to the most recent COMPLETED trading day
    start, end = resolve_stooq_window("1996-01-01", None, None, today)
    assert (start, end) == (date(1996, 1, 1), date(2026, 6, 30))
    # fresh run without --start falls back to the documented default
    start, _ = resolve_stooq_window(None, None, None, today)
    assert start == date.fromisoformat(DEFAULT_START)

    manifest = {"provider": "stooq", "window": {"start": "1996-01-01", "end": "2026-06-29"}}
    # resume: the manifest's pinned window WINS (one consistent bound across all symbols)
    start, end = resolve_stooq_window(None, None, manifest, today)
    assert (start, end) == (date(1996, 1, 1), date(2026, 6, 29))
    # matching explicit args are fine
    start, end = resolve_stooq_window("1996-01-01", "2026-06-29", manifest, today)
    assert (start, end) == (date(1996, 1, 1), date(2026, 6, 29))
    # a CONFLICTING explicit end/start is refused — never a mixed-window basis
    with pytest.raises(WindowConflictError):
        resolve_stooq_window(None, "2026-06-30", manifest, today)
    with pytest.raises(WindowConflictError):
        resolve_stooq_window("1997-01-01", None, manifest, today)


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------

def test_parser_defaults_preserve_yahoo_usage():
    """A bare invocation must mean exactly what it meant before iter-16."""
    args = build_parser().parse_args([])
    assert args.provider == "yahoo"
    assert args.out is None           # resolved to the live seed dir
    assert args.symbols_set == "default"
    assert args.start is None         # resolved to DEFAULT_START
    assert args.end is None
    assert args.sleep is None         # resolved per-provider (yahoo 0.3 / stooq 1.0)
    assert args.probe is False
    assert DEFAULT_START == "2021-01-01"


def test_provider_routing_stooq_cli(monkeypatch, tmp_path):
    """--provider stooq routes through the EXISTING StooqProvider fetch path (built by
    make_stooq_provider — the provider's documented client-injection seam)."""
    import scripts.ingest_seed as ingest_seed

    monkeypatch.delenv(STOOQ_API_KEY_ENV, raising=False)
    built: list[str] = []
    client = _FakeStooqClient({"aapl.us": _VALID_CSV})

    def _recording_provider():
        built.append("stooq")
        return StooqProvider(client=client)

    monkeypatch.setattr(ingest_seed, "make_stooq_provider", _recording_provider)
    monkeypatch.setattr(ingest_seed, "build_default_symbols", lambda cfg: ["AAPL"])

    rc = main([
        "--provider", "stooq", "--out", str(tmp_path), "--sleep", "0",
        "--start", "2024-01-02", "--end", "2024-01-04",
    ])
    assert rc == 0
    assert built == ["stooq"]
    assert (tmp_path / "prices" / "AAPL.csv").exists()


def test_env_key_client_injection_never_persisted(monkeypatch):
    """STOOQ_API_KEY is read from the ENVIRONMENT ONLY: when present it rides as a request-only
    query param on the injected verify client; when absent no key param exists anywhere. Either
    way the provider is the EXISTING StooqProvider (zero app change) and nothing is persisted."""
    monkeypatch.setenv(STOOQ_API_KEY_ENV, "test-key-not-a-real-secret")
    provider = make_stooq_provider()
    assert isinstance(provider, StooqProvider)
    assert isinstance(provider._client, _StooqVerifyClient)
    assert provider._client._client.params["apikey"] == "test-key-not-a-real-secret"
    provider._client.close()

    monkeypatch.delenv(STOOQ_API_KEY_ENV, raising=False)
    keyless = make_stooq_provider()
    assert isinstance(keyless, StooqProvider)
    assert isinstance(keyless._client, _StooqVerifyClient)
    assert "apikey" not in keyless._client._client.params  # keyless: no credential anywhere
    keyless._client.close()


def test_key_redacted_from_manifest_and_output_on_failure(monkeypatch, tmp_path, capsys):
    """(audit fix) httpx HTTP-status errors embed the FULL request URL — including the `apikey`
    query param the verify client rides — and that message flows into the staging manifest
    (`cap_events[].detail`, a COMMITTED artifact) and console output. The key must be redacted
    everywhere it could be persisted or printed (anti-goal: env-only, never persisted)."""
    monkeypatch.setenv(STOOQ_API_KEY_ENV, "test-secret-key-123")
    err = httpx.HTTPError(
        "Client error '401 Unauthorized' for url "
        "'https://stooq.com/q/d/l/?apikey=test-secret-key-123&s=aapl.us&i=d&d1=19960101'"
    )
    client = _FakeStooqClient({"aapl.us": err})
    rc = run_stooq_ingest(StooqProvider(client=client), ["AAPL"],
                          date(2024, 1, 2), date(2024, 1, 4), tmp_path, sleep_s=0, retries=2)
    assert rc == EXIT_CAP_STOP

    meta_text = (tmp_path / "meta.json").read_text()
    assert "test-secret-key-123" not in meta_text          # never persisted
    meta = json.loads(meta_text)
    assert "apikey=***" in meta["cap_events"][0]["detail"]  # evidence kept, secret stripped
    assert "test-secret-key-123" not in capsys.readouterr().out  # never printed either


# ---------------------------------------------------------------------------
# front-door verification handshake (offline — the live outcome is in the dev handoff)
# ---------------------------------------------------------------------------

_CHALLENGE_C = "itertest-challenge"
_CHALLENGE_PAGE = (
    '<!DOCTYPE html><html><body><noscript>This site requires JavaScript to verify your browser.'
    f'</noscript><script>(async()=>{{const c="{_CHALLENGE_C}",d=1,t="0".repeat(d);'
    '/* sha256 pow */fetch("/__verify")})();</script></body></html>'
)


class _FakeVerifyInner:
    """Stand-in for the wrapped httpx client: serves scripted GET bodies in order and records the
    /__verify POST."""

    def __init__(self, get_bodies: list[str], verify_status: int = 200):
        self._bodies = list(get_bodies)
        self._verify_status = verify_status
        self.gets: list[dict] = []
        self.posts: list[dict] = []

    def get(self, url, params=None, timeout=None):
        self.gets.append({"url": url, "params": dict(params or {})})
        return _FakeResponse(self._bodies.pop(0))

    def post(self, url, data=None, timeout=None):
        self.posts.append({"url": url, "data": dict(data or {})})
        response = _FakeResponse("")
        response.status_code = self._verify_status
        return response


def test_verify_client_solves_challenge_and_retries():
    """The verify client completes the served handshake EXACTLY as specified — sha256(c+n) with d
    leading hex zeros, POSTed to /__verify — then retries the original request once."""
    import hashlib

    inner = _FakeVerifyInner([_CHALLENGE_PAGE, _VALID_CSV])
    client = _StooqVerifyClient(client=inner)
    response = client.get("https://stooq.com/q/d/l/", params={"s": "aapl.us", "i": "d"})
    assert response.text == _VALID_CSV
    assert len(inner.gets) == 2 and inner.gets[0]["params"] == inner.gets[1]["params"]
    assert len(inner.posts) == 1
    assert inner.posts[0]["url"] == "https://stooq.com/__verify"
    posted = inner.posts[0]["data"]
    assert posted["c"] == _CHALLENGE_C
    digest = hashlib.sha256(f"{_CHALLENGE_C}{posted['n']}".encode()).hexdigest()
    assert digest.startswith("0")  # d=1 in the fixture


def test_verify_client_passthrough_without_challenge():
    inner = _FakeVerifyInner([_VALID_CSV])
    response = _StooqVerifyClient(client=inner).get("https://stooq.com/q/d/l/", params={"s": "aapl.us"})
    assert response.text == _VALID_CSV
    assert len(inner.gets) == 1 and inner.posts == []


def test_verify_client_honors_persistent_gate():
    """If the endpoint still refuses after one honest handshake (re-challenged, or /__verify
    refused), the client returns the gate response unchanged — the provider then raises and the
    run stops honestly. No loops, no evasion."""
    # re-challenged after a successful verify -> the second challenge page is surfaced
    inner = _FakeVerifyInner([_CHALLENGE_PAGE, _CHALLENGE_PAGE])
    response = _StooqVerifyClient(client=inner).get("https://stooq.com/q/d/l/", params={"s": "a"})
    assert "verify your browser" in response.text
    assert len(inner.gets) == 2 and len(inner.posts) == 1

    # /__verify refused -> the ORIGINAL challenge response is surfaced, no retry
    inner2 = _FakeVerifyInner([_CHALLENGE_PAGE], verify_status=403)
    response2 = _StooqVerifyClient(client=inner2).get("https://stooq.com/q/d/l/", params={"s": "a"})
    assert "verify your browser" in response2.text
    assert len(inner2.gets) == 1 and len(inner2.posts) == 1


# ---------------------------------------------------------------------------
# staging layout + manifest
# ---------------------------------------------------------------------------

def test_out_writes_staging_layout_exact(tmp_path):
    """--out stages the live-seed layout: prices/*.csv (canonical header, exact vendor values) +
    meta.json (provider, pinned window, per-symbol coverage)."""
    provider = StooqProvider(client=_FakeStooqClient({"aapl.us": _VALID_CSV}))
    rc = run_stooq_ingest(provider, ["AAPL"], date(2024, 1, 2), date(2024, 1, 4), tmp_path, sleep_s=0)
    assert rc == 0

    csv_path = tmp_path / "prices" / "AAPL.csv"
    lines = csv_path.read_text().strip().splitlines()
    assert lines[0] == ",".join(CSV_FIELDS)
    assert lines[1].split(",") == ["2024-01-02", "185.0", "186.0", "184.0", "185.5", "1000"]
    assert len(lines) == 1 + 3

    meta = json.loads((tmp_path / "meta.json").read_text())
    assert meta["provider"] == "stooq"
    assert meta["window"] == {"start": "2024-01-02", "end": "2024-01-04"}
    assert meta["symbols_ok"] == 1 and meta["symbols_failed"] == 0
    assert meta["failed"] == [] and meta["cap_events"] == []
    assert meta["symbols"] == [
        {"symbol": "AAPL", "bars": 3, "first": "2024-01-02", "last": "2024-01-04"}
    ]
    assert load_manifest(tmp_path) == meta


def test_resume_skips_complete_and_recorded_failures(tmp_path):
    """Resume fetches ONLY symbols not yet complete: a staged-ok symbol (manifest + CSV) is skipped,
    a recorded no-data symbol stays honestly omitted (not re-hammered), missing symbols fetch."""
    start, end = date(2024, 1, 2), date(2024, 1, 4)
    first = StooqProvider(client=_FakeStooqClient({"aapl.us": _VALID_CSV, "zzzz.us": "N/D"}))
    assert run_stooq_ingest(first, ["AAPL", "ZZZZ"], start, end, tmp_path, sleep_s=0) == 0

    client2 = _FakeStooqClient({"msft.us": _VALID_CSV})
    second = StooqProvider(client=client2)
    rc = run_stooq_ingest(second, ["AAPL", "ZZZZ", "MSFT"], start, end, tmp_path, sleep_s=0)
    assert rc == 0
    assert client2.requested() == ["msft.us"]  # AAPL complete + ZZZZ recorded-absent were skipped

    meta = load_manifest(tmp_path)
    assert [e["symbol"] for e in meta["symbols"]] == ["AAPL", "MSFT"]
    assert meta["failed"] == ["ZZZZ"]
    assert meta["symbols_ok"] == 2 and meta["symbols_failed"] == 1


def test_rate_limit_stops_gracefully_then_resumes(tmp_path):
    """A rate-limit/limit-page/non-CSV body stops the run: failure recorded as a cap event, progress
    manifest written, non-zero exit, NO partial CSV row, NO further symbol requested. A later resume
    picks up exactly where it stopped and reuses the pinned end."""
    start, end = date(2024, 1, 2), date(2024, 1, 4)
    client = _FakeStooqClient({
        "aapl.us": _VALID_CSV,
        "spy.us": _LIMIT_PAGE,
        "nvda.us": _VALID_CSV,  # present in the stub, but must NEVER be requested after the stop
    })
    rc = run_stooq_ingest(
        StooqProvider(client=client), ["AAPL", "SPY", "NVDA"], start, end, tmp_path,
        sleep_s=0, retries=3,
    )
    assert rc == EXIT_CAP_STOP
    assert (tmp_path / "prices" / "AAPL.csv").exists()
    assert not (tmp_path / "prices" / "SPY.csv").exists()   # no partial/fabricated CSV
    assert "nvda.us" not in client.requested()              # stopped, did not plow on
    assert client.requested().count("spy.us") == 3          # gate errors are retried, then stop

    meta = load_manifest(tmp_path)
    assert [e["symbol"] for e in meta["symbols"]] == ["AAPL"]
    assert meta["failed"] == []                             # a cap is NOT a permanent no-data failure
    assert len(meta["cap_events"]) == 1
    assert meta["cap_events"][0]["symbol"] == "SPY"
    assert "Exceeded the daily hits limit" in meta["cap_events"][0]["detail"]

    # resume: only SPY + NVDA are fetched; the same pinned window is reused
    client2 = _FakeStooqClient({"spy.us": _VALID_CSV, "nvda.us": _VALID_CSV})
    manifest = load_manifest(tmp_path)
    start2, end2 = resolve_stooq_window(None, None, manifest, date(2026, 7, 1))
    assert (start2, end2) == (start, end)
    rc2 = run_stooq_ingest(StooqProvider(client=client2), ["AAPL", "SPY", "NVDA"],
                           start2, end2, tmp_path, sleep_s=0)
    assert rc2 == 0
    assert client2.requested() == ["spy.us", "nvda.us"]
    meta2 = load_manifest(tmp_path)
    assert [e["symbol"] for e in meta2["symbols"]] == ["AAPL", "SPY", "NVDA"]
    assert len(meta2["cap_events"]) == 1  # the historical cap event stays recorded (honest history)


def test_nd_unknown_symbol_recorded_run_continues(tmp_path):
    """An unknown-symbol "N/D" response is a PER-SYMBOL honest absence: recorded once (no retries),
    then the run continues to the next symbol and still exits 0."""
    client = _FakeStooqClient({"zzzz.us": "N/D", "msft.us": _VALID_CSV})
    rc = run_stooq_ingest(StooqProvider(client=client), ["ZZZZ", "MSFT"],
                          date(2024, 1, 2), date(2024, 1, 4), tmp_path, sleep_s=0)
    assert rc == 0
    assert client.requested() == ["zzzz.us", "msft.us"]  # exactly one N/D attempt — not retried
    assert not (tmp_path / "prices" / "ZZZZ.csv").exists()
    assert (tmp_path / "prices" / "MSFT.csv").exists()

    meta = load_manifest(tmp_path)
    assert meta["failed"] == ["ZZZZ"]
    assert meta["failures"][0]["symbol"] == "ZZZZ"
    assert "N/D" in meta["failures"][0]["detail"]


def test_classify_stooq_failure():
    """Failure taxonomy: N/D = per-symbol absence (continue); an unparseable real-CSV row = per-symbol
    quirk (continue); anything else (network/HTTP error, limit page, non-CSV/empty body) = gate
    (retry, then resumable stop)."""
    assert classify_stooq_failure("stooq returned no usable data for 'ZZZZ': 'N/D'") == "no_data"
    assert classify_stooq_failure(
        "stooq returned no usable data for 'AAPL': 'Exceeded the daily hits limit'"
    ) == "gate"
    assert classify_stooq_failure("stooq returned no usable data for 'AAPL': ''") == "gate"
    assert classify_stooq_failure("stooq response unparseable for '^VIX': could not convert") == "unparseable"
    assert classify_stooq_failure("stooq request failed for 'AAPL': timeout") == "gate"


def test_refuses_out_dir_with_foreign_manifest(tmp_path):
    """Clobber guard: a stooq staging run REFUSES an --out dir whose meta.json is not a stooq staging
    manifest (e.g. the LIVE Yahoo seed dir) — the swap is iter-17's, staging is side-by-side only."""
    (tmp_path / "meta.json").write_text(json.dumps({
        "source": "Yahoo Finance chart API (query1.finance.yahoo.com/v8/finance/chart)",
        "window": {"start": "2021-01-04", "end": "2026-05-28"},
        "symbols": [{"symbol": "AAPL", "bars": 3, "first": "2021-01-04", "last": "2026-05-28"}],
    }))
    client = _FakeStooqClient({})  # any request would raise — none must happen
    rc = run_stooq_ingest(StooqProvider(client=client), ["AAPL"],
                          date(2024, 1, 2), date(2024, 1, 4), tmp_path, sleep_s=0)
    assert rc == EXIT_CONFLICT
    assert client.calls == []
    assert not (tmp_path / "prices").exists()


# ---------------------------------------------------------------------------
# probe (go/no-go)
# ---------------------------------------------------------------------------

def test_probe_pass_stages_csvs_and_manifest(tmp_path):
    """A passing probe verifies real-CSV/depth/schema/adjusted-basis on AAPL+SPY+NVDA and stages the
    three fetched CSVs + manifest so the full run resumes past them (no wasted refetch)."""
    provider = StooqProvider(client=_FakeStooqClient({
        "aapl.us": _AAPL_FULLSPAN, "spy.us": _SPY_FULLSPAN, "nvda.us": _NVDA_FULLSPAN,
    }))
    rc = run_probe(provider, tmp_path, date(1996, 1, 1), date(2026, 6, 30), sleep_s=0)
    assert rc == 0
    for name in ("AAPL", "SPY", "NVDA"):
        path = tmp_path / "prices" / f"{name}.csv"
        assert path.exists()
        assert path.read_text().splitlines()[0] == ",".join(CSV_FIELDS)
    meta = load_manifest(tmp_path)
    assert meta["provider"] == "stooq"
    assert meta["window"] == {"start": "1996-01-01", "end": "2026-06-30"}
    assert {e["symbol"] for e in meta["symbols"]} == {"AAPL", "SPY", "NVDA"}
    aapl = next(e for e in meta["symbols"] if e["symbol"] == "AAPL")
    assert aapl["first"] == "1996-01-02" and aapl["last"] == "2026-06-30" and aapl["bars"] == 4


def test_probe_fails_on_unadjusted_split_writes_nothing(tmp_path):
    """An UNADJUSTED basis (a ~10x one-day close gap across NVDA's 2024-06-10 split) is a probe
    validation FAILURE: exit 3 and NOTHING staged (no-go means no artifact to resume from)."""
    nvda_unadjusted = _stooq_body([
        ("1999-01-22", 0.04, 0.05, 0.039, 0.041, 2000000),
        ("2024-06-07", 1200.0, 1215.0, 1180.0, 1208.9, 300000),
        ("2024-06-10", 121.0, 123.0, 119.0, 121.79, 310000),  # -89.9% seam = unadjusted
        ("2026-06-30", 170.0, 172.0, 168.0, 171.2, 200000),
    ])
    provider = StooqProvider(client=_FakeStooqClient({
        "aapl.us": _AAPL_FULLSPAN, "spy.us": _SPY_FULLSPAN, "nvda.us": nvda_unadjusted,
    }))
    rc = run_probe(provider, tmp_path, date(1996, 1, 1), date(2026, 6, 30), sleep_s=0)
    assert rc == EXIT_PROBE_FAIL
    assert not (tmp_path / "meta.json").exists()
    assert not (tmp_path / "prices").exists()


def test_probe_gate_failure_exits_2_writes_nothing(tmp_path):
    """A gated/rate-capped endpoint at probe time is the honest-blocked outcome: exit 2, the exact
    response evidence surfaced in the error, nothing staged, no further symbol requested."""
    client = _FakeStooqClient({"aapl.us": _LIMIT_PAGE})
    rc = run_probe(StooqProvider(client=client), tmp_path,
                   date(1996, 1, 1), date(2026, 6, 30), sleep_s=0)
    assert rc == EXIT_CAP_STOP
    assert client.requested() and set(client.requested()) == {"aapl.us"}  # SPY/NVDA never requested
    assert not (tmp_path / "meta.json").exists()
    assert not (tmp_path / "prices").exists()


# ---------------------------------------------------------------------------
# Yahoo default path unregressed
# ---------------------------------------------------------------------------

def test_yahoo_path_unregressed_writes_live_layout(monkeypatch, tmp_path):
    """The default (Yahoo) invocation keeps its behavior: same symbol set builder, same CSV layout,
    same meta.json shape (source/note/window/symbols — and NO stooq staging keys)."""
    import scripts.ingest_seed as ingest_seed

    rows = [
        {"date": "2024-01-02", "open": 185.0, "high": 186.0, "low": 184.0, "close": 185.5, "volume": 1000},
        {"date": "2024-01-03", "open": 186.0, "high": 188.0, "low": 185.0, "close": 187.25, "volume": 1200},
    ]
    monkeypatch.setattr(ingest_seed, "fetch_symbol", lambda client, symbol, start, end: list(rows))
    monkeypatch.setattr(ingest_seed, "build_default_symbols", lambda cfg: ["AAPL"])

    rc = main(["--out", str(tmp_path), "--sleep", "0", "--start", "2024-01-02", "--end", "2024-01-03"])
    assert rc == 0
    csv_lines = (tmp_path / "prices" / "AAPL.csv").read_text().strip().splitlines()
    assert csv_lines[0] == ",".join(CSV_FIELDS)
    assert len(csv_lines) == 3

    meta = json.loads((tmp_path / "meta.json").read_text())
    assert meta["source"].startswith("Yahoo Finance chart API")
    assert meta["window"] == {"start": "2024-01-02", "end": "2024-01-03"}
    assert meta["symbols_ok"] == 1 and meta["symbols_failed"] == 0
    assert meta["symbols"] == [{"symbol": "AAPL", "bars": 2, "first": "2024-01-02", "last": "2024-01-03"}]
    assert "provider" not in meta and "cap_events" not in meta  # live-seed meta shape untouched


# ---------------------------------------------------------------------------
# stooq-local: the offline bulk-archive provider (iter-16 unblock)
# ---------------------------------------------------------------------------

def _write_bulk(path, ticker, rows):
    """Write one Stooq bulk-archive `.us.txt` file: the `<TICKER>,<PER>,...` header + YYYYMMDD rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["<TICKER>,<PER>,<DATE>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>,<OPENINT>"]
    for d, o, h, l, c, v in rows:
        lines.append(f"{ticker},D,{d},000000,{o},{h},{l},{c},{v},0")
    path.write_text("\n".join(lines) + "\n")


def _make_local_archive(tmp_path):
    """A tiny d_us_txt-shaped tree: a sharded stock, an ETF (hyphenated class share), an empty file."""
    us = tmp_path / "d_us_txt" / "data" / "daily" / "us"
    _write_bulk(us / "nasdaq stocks" / "1" / "aapl.us.txt", "AAPL.US", [
        ("19960102", 0.24, 0.25, 0.23, 0.2425, 400000000),
        ("20240103", 186.0, 188.0, 185.0, 187.25, 1200),
        ("20240104", 187.0, 187.5, 183.0, 184.0, 1500.5),  # fractional back-adjusted volume
    ])
    _write_bulk(us / "nyse etfs" / "2" / "brk-b.us.txt", "BRK-B.US", [
        ("20240103", 400.0, 402.0, 399.0, 401.0, 5000),
    ])
    empty = us / "nasdaq etfs" / "sats.us.txt"
    empty.parent.mkdir(parents=True, exist_ok=True)
    empty.write_text("")  # 0-byte file — an empty series (like the real SATS)
    return tmp_path / "d_us_txt"


def test_local_archive_indexes_and_reads_ascending(tmp_path):
    provider = LocalStooqArchiveProvider(_make_local_archive(tmp_path))
    assert provider.indexed_count == 3  # aapl, brk-b, sats (across shards)

    bars = provider.get_daily("AAPL", date(1996, 1, 1), date(2024, 1, 4))
    assert [b.date for b in bars] == [date(1996, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    assert bars[0].close == 0.2425
    assert bars[-1].volume == 1500.5  # fractional volume kept on the Bar (int() only at write time)


def test_local_archive_window_filter_inclusive(tmp_path):
    provider = LocalStooqArchiveProvider(_make_local_archive(tmp_path))
    bars = provider.get_daily("AAPL", date(2024, 1, 3), date(2024, 1, 3))
    assert [b.date for b in bars] == [date(2024, 1, 3)]


def test_local_archive_class_share_hyphen_mapping(tmp_path):
    provider = LocalStooqArchiveProvider(_make_local_archive(tmp_path))
    assert provider.get_daily("BRK.B")   # BRK.B -> brk-b.us.txt
    assert provider.get_daily("BRK-B")   # already hyphenated -> same file


def test_local_archive_missing_caret_empty_return_empty_not_raise(tmp_path):
    """A caret index (not in the stocks+ETFs bundle), an unknown name, and an empty file all return
    [] — the ingest loop records an honest absence and CONTINUES. They MUST NOT raise: a raised
    'no file' classifies as a rate-cap GATE and would abort the whole staged run (and ^VIX is an
    early tier-1 name)."""
    provider = LocalStooqArchiveProvider(_make_local_archive(tmp_path))
    assert provider.get_daily("^VIX") == []   # caret -> not in this bundle
    assert provider.get_daily("ZZZZ") == []   # unknown name
    assert provider.get_daily("SATS") == []   # 0-byte file


def test_local_archive_unparseable_row_raises(tmp_path):
    """A corrupt row in a PRESENT file surfaces as ProviderUnavailableError('...unparseable...') so
    the ingest classifies it as a per-symbol quirk (record absent + continue), never fabricating."""
    archive = tmp_path / "d_us_txt"
    bad = archive / "data" / "daily" / "us" / "nasdaq stocks" / "1" / "bad.us.txt"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text(
        "<TICKER>,<PER>,<DATE>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>,<OPENINT>\n"
        "BAD.US,D,NOTADATE,000000,1,2,3,4,5,0\n"
    )
    provider = LocalStooqArchiveProvider(archive)
    with pytest.raises(ProviderUnavailableError) as exc:
        provider.get_daily("BAD")
    assert "unparseable" in str(exc.value)


def test_local_archive_missing_dir_is_empty_not_error(tmp_path):
    provider = LocalStooqArchiveProvider(tmp_path / "does-not-exist")
    assert provider.indexed_count == 0
    assert provider.get_daily("AAPL") == []


def test_local_archive_feeds_run_stooq_ingest_end_to_end(tmp_path):
    """The provider drops into the UNCHANGED run_stooq_ingest: byte-format-identical staged CSV
    (round(6) OHLC, int volume) + a manifest tagged provider='stooq' with the local `source`, and
    caret/empty names recorded as honest absences (no CSV)."""
    out = tmp_path / "seed-stooq-30y"
    provider = LocalStooqArchiveProvider(_make_local_archive(tmp_path))
    rc = run_stooq_ingest(provider, ["AAPL", "^VIX", "SATS"], date(1996, 1, 1), date(2024, 1, 4),
                          out, sleep_s=0, source="test-local-source", note="test-local-note")
    assert rc == 0

    lines = (out / "prices" / "AAPL.csv").read_text().strip().splitlines()
    assert lines[0] == ",".join(CSV_FIELDS)
    assert lines[-1].split(",") == ["2024-01-04", "187.0", "187.5", "183.0", "184.0", "1500"]  # int(1500.5)

    meta = load_manifest(out)
    assert meta["provider"] == "stooq"                 # vendor tag preserved (validation requires it)
    assert meta["source"] == "test-local-source" and meta["note"] == "test-local-note"
    assert [e["symbol"] for e in meta["symbols"]] == ["AAPL"]
    assert set(meta["failed"]) == {"^VIX", "SATS"}     # honest absences
    assert not (out / "prices" / "_VIX.csv").exists()  # caret index never written


def test_parser_accepts_stooq_local_and_archive_dir():
    args = build_parser().parse_args(["--provider", "stooq-local", "--archive-dir", "/tmp/x"])
    assert args.provider == "stooq-local"
    assert args.archive_dir == "/tmp/x"


def test_stooq_local_probe_rejected(tmp_path):
    """--probe is the live-endpoint go/no-go (SPY<=1996 depth); it doesn't fit the bulk US-ETF
    archive, so stooq-local refuses it with EXIT_CONFLICT and stages nothing."""
    archive = _make_local_archive(tmp_path)
    rc = main(["--provider", "stooq-local", "--probe", "--out", str(tmp_path / "out"),
               "--archive-dir", str(archive), "--start", "1996-01-01"])
    assert rc == EXIT_CONFLICT
    assert not (tmp_path / "out").exists()


def test_stooq_local_missing_archive_dir_refused(tmp_path):
    rc = main(["--provider", "stooq-local", "--out", str(tmp_path / "out"),
               "--archive-dir", str(tmp_path / "nope"), "--start", "1996-01-01"])
    assert rc == EXIT_CONFLICT


def test_stooq_local_routes_through_main(monkeypatch, tmp_path):
    """--provider stooq-local builds the local archive provider and stages via run_stooq_ingest,
    with the bulk-archive source recorded in the manifest and the vendor tag kept 'stooq'."""
    archive = _make_local_archive(tmp_path)
    monkeypatch.setattr("scripts.ingest_seed.build_default_symbols", lambda cfg: ["AAPL", "^VIX"])
    rc = main(["--provider", "stooq-local", "--out", str(tmp_path / "out"),
               "--archive-dir", str(archive), "--start", "1996-01-01", "--end", "2024-01-04"])
    assert rc == 0
    meta = load_manifest(tmp_path / "out")
    assert meta["provider"] == "stooq"
    assert "d_us_txt" in meta["source"]
    assert [e["symbol"] for e in meta["symbols"]] == ["AAPL"]
    assert meta["failed"] == ["^VIX"]


# ---------------------------------------------------------------------------
# iter-17: world-bundle indexing (plain ^xxx.txt) in the stooq-local path
# ---------------------------------------------------------------------------

def _make_world_archive(tmp_path):
    """A tiny d_world_txt-shaped tree: plain `^xxx.txt` world indices (no `.us` suffix; the ^SPX
    file reaches back to 1789 with flat monthly rows, like the real bundle) PLUS one `*.us.txt`
    file in the same tree to prove the two layouts coexist in one index."""
    world = tmp_path / "d_world_txt" / "data" / "daily" / "world" / "indices"
    _write_bulk(world / "^spx.txt", "^SPX", [
        ("17890501", 0.51, 0.51, 0.51, 0.51, 0),        # flat monthly 18xx rows — MUST be clipped
        ("18710214", 4.86, 4.86, 4.86, 4.86, 0),
        ("19951229", 615.93, 616.7, 613.2, 615.93, 0),   # last pre-window row
        ("19960102", 620.73, 620.74, 613.17, 620.73, 350000),
        ("19960103", 621.32, 624.5, 619.1, 621.32, 360000),
        ("20260630", 7441.3, 7508.3, 7438.0, 7499.4, 3839254731),
        ("20260701", 7478.8, 7521.8, 7449.6, 7483.2, 2583762787),
    ])
    _write_bulk(world / "^ndx.txt", "^NDX", [
        ("19380103", 2.25, 2.29, 2.22, 2.24, 0),
        ("19960102", 576.23, 578.0, 570.1, 576.23, 0),   # index rows may carry volume 0
        ("20260701", 29914.28, 30084.78, 29787.41, 29809.13, 912401564),
    ])
    _write_bulk(world / "^dji.txt", "^DJI", [
        ("18960527", 29.39, 29.39, 29.39, 29.39, 0),
        ("19960102", 5177.45, 5194.2, 5130.0, 5177.45, 0),
        ("20260701", 52231.2, 52742.7, 52026.6, 52305.2, 429385567),
    ])
    us = tmp_path / "d_world_txt" / "data" / "daily" / "us" / "nasdaq stocks" / "1"
    _write_bulk(us / "aapl.us.txt", "AAPL.US", [
        ("19960102", 0.24, 0.25, 0.23, 0.2425, 400000000),
    ])
    return tmp_path / "d_world_txt"


def test_world_bundle_provider_indexes_carets_and_coexists(tmp_path):
    """The stooq-local provider discovers plain `^xxx.txt` world-bundle files alongside the
    `*.us.txt` US archive in ONE index; an absent caret stays an honest [] (never a raise —
    a raised 'no file' would gate-stop the whole run)."""
    provider = make_local_stooq_provider(_make_world_archive(tmp_path))
    assert provider.indexed_count == 4        # ^spx + ^ndx + ^dji + aapl.us
    assert provider.world_indexed_count == 3
    bars = provider.get_daily("^SPX", date(1996, 1, 1), date(2026, 7, 1))
    assert [b.date for b in bars][:2] == [date(1996, 1, 2), date(1996, 1, 3)]
    assert bars[-1].date == date(2026, 7, 1)
    assert provider.get_daily("AAPL", date(1996, 1, 1), date(2026, 7, 1))  # *.us.txt coexists
    assert provider.get_daily("^VIX") == []   # not in the world bundle — honest absence
    assert provider.get_daily("ZZZZ") == []


def test_world_bundle_window_clip_excludes_pre_1996(tmp_path):
    """The pinned-window clip is load-bearing: the world ^SPX file reaches 1789 (flat/monthly
    early rows) and NONE of that may leak into a staged CSV; the unclipped read still serves the
    deep rows (the clip is the caller's window, not data loss)."""
    provider = make_local_stooq_provider(_make_world_archive(tmp_path))
    bars = provider.get_daily("^SPX", date(1996, 1, 1), date(2026, 7, 1))
    assert all(b.date >= date(1996, 1, 1) for b in bars)
    assert len(bars) == 4                      # exactly the in-window fixture rows
    assert provider.get_daily("^SPX")[0].date == date(1789, 5, 1)  # archive depth intact


# ---------------------------------------------------------------------------
# iter-17: context-merge staging mode (--stage-context)
# ---------------------------------------------------------------------------

_STAGED_EQUITY_NOTE = "equities note (iter-16 staging)"
_STAGED_AAPL_ENTRY = {"symbol": "AAPL", "bars": 2, "first": "1996-01-02", "last": "2026-07-01"}


def _make_staged_equities_dir(tmp_path):
    """A miniature iter-16-shaped staged seed: one equity CSV + a manifest recording the four
    caret context series and SATS as honest absences (the real staged manifest's exact shape)."""
    out = tmp_path / "seed-stooq-30y"
    prices = out / "prices"
    prices.mkdir(parents=True)
    (prices / "AAPL.csv").write_text(
        "date,open,high,low,close,volume\n"
        "1996-01-02,0.24,0.25,0.23,0.2425,400000000\n"
        "2026-07-01,210.0,212.0,208.0,211.0,90000\n"
    )
    manifest = {
        "source": "Stooq bulk US daily archive (local: data/d_us_txt, from stooq.com d_us_txt.zip)",
        "provider": "stooq",
        "note": _STAGED_EQUITY_NOTE,
        "generated_at": "2026-07-02T11:51:25+00:00",
        "window": {"start": "1996-01-01", "end": "2026-07-01"},
        "symbols_planned": 6,
        "symbols_ok": 1,
        "symbols_failed": 5,
        "failed": ["SATS", "^DXY", "^TNX", "^VIX", "^VXN"],
        "failures": [
            {"symbol": "^VIX", "kind": "no_data", "detail": "empty CSV (no rows in window)"},
            {"symbol": "^TNX", "kind": "no_data", "detail": "empty CSV (no rows in window)"},
            {"symbol": "^VXN", "kind": "no_data", "detail": "empty CSV (no rows in window)"},
            {"symbol": "^DXY", "kind": "no_data", "detail": "empty CSV (no rows in window)"},
            {"symbol": "SATS", "kind": "no_data", "detail": "empty CSV (no rows in window)"},
        ],
        "cap_events": [],
        "symbols": [dict(_STAGED_AAPL_ENTRY)],
    }
    (out / "meta.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return out


_LIVE_CARET_CSVS = {
    "_VIX.csv": ("date,open,high,low,close,volume\n"
                 "2021-01-04,23.04,29.19,22.56,26.97,0\n"
                 "2026-05-28,16.76,16.85,15.61,15.74,0\n"),
    "_TNX.csv": ("date,open,high,low,close,volume\n"
                 "2021-01-04,4.8,4.8,4.8,4.8,0\n"
                 "2026-05-28,4.4,4.4,4.4,4.4,0\n"),
    "_DXY.csv": ("date,open,high,low,close,volume\n"
                 "2021-01-04,105.2,105.2,105.2,105.2,0\n"
                 "2026-05-28,104.1,104.1,104.1,104.1,0\n"),
    "_VXN.csv": ("date,open,high,low,close,volume\n"
                 "2021-01-04,28.9,28.9,28.9,28.9,0\n"
                 "2026-05-28,19.2,19.2,19.2,19.2,0\n"),
}


def _make_live_seed_fixture(tmp_path, include_vix=True):
    """A miniature live-seed dir carrying the caret series (the proxy-copy / _VIX-fallback
    sources). NEVER written by the merge — reads only."""
    live = tmp_path / "live-seed"
    prices = live / "prices"
    prices.mkdir(parents=True)
    for name, body in _LIVE_CARET_CSVS.items():
        if name == "_VIX.csv" and not include_vix:
            continue
        (prices / name).write_text(body)
    return live


def _deep_vix_rows(start=date(1996, 1, 2), end=date(2026, 6, 30)):
    """A synthetic DEEP, single-pull, continuous ^VIX series (weekly cadence — every gap is 7
    calendar days, inside the single-continuous-series bound)."""
    rows = []
    d = start
    while d <= end:
        rows.append({"date": d.isoformat(), "open": 20.0, "high": 21.0, "low": 19.0,
                     "close": 20.5, "volume": 0})
        d += timedelta(days=7)
    return rows


def test_context_merge_stages_and_merges_manifest(tmp_path):
    """The context merge stages _SPX/_NDX/_DJI (world bundle, window-clipped), byte-copies the
    three FRED-macro proxies, writes the deep ^VIX pull, and MERGES the coverage/vendor records
    into the existing staged manifest — 583-style equity records, pinned window, and provider
    identity all untouched; the caret failures resolve; accounting stays consistent."""
    out = _make_staged_equities_dir(tmp_path)
    live = _make_live_seed_fixture(tmp_path)
    provider = make_local_stooq_provider(_make_world_archive(tmp_path))
    deep = _deep_vix_rows()

    rc = run_context_merge(provider, out, live_seed_dir=live,
                           fetch_vix_rows=lambda start, end: list(deep))
    assert rc == 0

    # world indexes staged, window-clipped, caret -> _XXX.csv mapping
    spx_lines = (out / "prices" / "_SPX.csv").read_text().strip().splitlines()
    assert spx_lines[0] == ",".join(CSV_FIELDS)
    assert spx_lines[1].split(",")[0] == "1996-01-02"      # the 1789/1871/1995 rows were clipped
    assert spx_lines[-1].split(",")[0] == "2026-07-01"     # last bar == the manifest's pinned end
    assert len(spx_lines) == 1 + 4
    assert (out / "prices" / "_NDX.csv").exists() and (out / "prices" / "_DJI.csv").exists()

    # proxies byte-identical to the live seed; deep ^VIX written from the single pull
    for name in ("_TNX.csv", "_DXY.csv", "_VXN.csv"):
        assert (out / "prices" / name).read_bytes() == (live / "prices" / name).read_bytes()
    vix_lines = (out / "prices" / "_VIX.csv").read_text().strip().splitlines()
    assert vix_lines[1].split(",")[0] == "1996-01-02"
    assert len(vix_lines) == 1 + len(deep)

    meta = load_manifest(out)
    assert meta["provider"] == "stooq"
    assert meta["window"] == {"start": "1996-01-01", "end": "2026-07-01"}   # pins unchanged
    assert meta["symbols"][0] == _STAGED_AAPL_ENTRY                          # equity record untouched
    assert meta["source"].startswith("Stooq bulk US daily archive")         # source preserved
    assert meta["note"].startswith(_STAGED_EQUITY_NOTE)                      # note EXTENDED, not replaced
    assert "never presented as a market index" in meta["note"]
    assert meta["symbols_planned"] == 6 + 3                                  # +^SPX/^NDX/^DJI only
    assert meta["symbols_ok"] == 1 + 7 == len(meta["symbols"])
    assert meta["symbols_failed"] == 1 and meta["failed"] == ["SATS"]        # caret failures resolved

    by_symbol = {e["symbol"]: e for e in meta["symbols"]}
    for symbol, vendor in (("^SPX", "stooq"), ("^NDX", "stooq"), ("^DJI", "stooq"),
                           ("^VIX", "yahoo"), ("^TNX", "fred-macro-proxy"),
                           ("^DXY", "fred-macro-proxy"), ("^VXN", "fred-macro-proxy")):
        assert by_symbol[symbol]["vendor"] == vendor, symbol
    assert "vendor" not in by_symbol["AAPL"]           # equity records keep the manifest-level tag
    assert (by_symbol["^SPX"]["bars"], by_symbol["^SPX"]["first"], by_symbol["^SPX"]["last"]) == \
        (4, "1996-01-02", "2026-07-01")
    assert (by_symbol["^TNX"]["first"], by_symbol["^TNX"]["last"]) == ("2021-01-04", "2026-05-28")
    assert by_symbol["^VIX"]["first"] == "1996-01-02"

    # idempotent re-run: accounting stable, the note addendum appended exactly once
    rc2 = run_context_merge(provider, out, live_seed_dir=live,
                            fetch_vix_rows=lambda start, end: list(deep))
    assert rc2 == 0
    meta2 = load_manifest(out)
    assert meta2["symbols_planned"] == 9 and meta2["symbols_ok"] == 8
    assert meta2["note"].count("never presented as a market index") == 1


def test_context_merge_vix_falls_back_to_verbatim_live_copy(tmp_path):
    """Yahoo unreachable -> the SANCTIONED fallback: the live seed's _VIX.csv is copied VERBATIM
    (byte-identical, honestly short), recorded vendor=yahoo with the shortfall — never a partial
    or spliced series, and the merge still completes (iter-18 stays unblocked)."""
    out = _make_staged_equities_dir(tmp_path)
    live = _make_live_seed_fixture(tmp_path)
    provider = make_local_stooq_provider(_make_world_archive(tmp_path))

    def _unreachable(start, end):
        raise httpx.ConnectError("connection refused")

    rc = run_context_merge(provider, out, live_seed_dir=live, fetch_vix_rows=_unreachable)
    assert rc == 0
    assert (out / "prices" / "_VIX.csv").read_bytes() == \
        (live / "prices" / "_VIX.csv").read_bytes()
    meta = load_manifest(out)
    vix = next(e for e in meta["symbols"] if e["symbol"] == "^VIX")
    assert vix["vendor"] == "yahoo"
    assert (vix["first"], vix["last"]) == ("2021-01-04", "2026-05-28")  # honestly short, recorded
    assert "fallback" in vix.get("note", "")


def test_context_merge_shallow_or_stale_pull_falls_back_never_splices(tmp_path):
    """A pull that is NOT the deep series (shallow first bar) or that would LOSE coverage vs the
    live copy (stale last bar) is discarded IN FULL for the verbatim fallback — the two pulls are
    never merged/spliced into one series (anti-goal: no vendor-spliced bars)."""
    out = _make_staged_equities_dir(tmp_path)
    live = _make_live_seed_fixture(tmp_path)
    provider = make_local_stooq_provider(_make_world_archive(tmp_path))

    shallow = [{"date": "2021-01-04", "open": 23.0, "high": 29.2, "low": 22.6, "close": 26.97,
                "volume": 0},
               {"date": "2026-06-30", "open": 16.0, "high": 17.0, "low": 15.5, "close": 15.9,
                "volume": 0}]
    rc = run_context_merge(provider, out, live_seed_dir=live,
                           fetch_vix_rows=lambda start, end: list(shallow))
    assert rc == 0
    assert (out / "prices" / "_VIX.csv").read_bytes() == \
        (live / "prices" / "_VIX.csv").read_bytes()          # verbatim copy, NOT the shallow pull

    stale = _deep_vix_rows(end=date(2020, 1, 1))             # deep but ends before the live copy
    out2 = _make_staged_equities_dir(tmp_path / "second")
    rc2 = run_context_merge(provider, out2, live_seed_dir=live,
                            fetch_vix_rows=lambda start, end: list(stale))
    assert rc2 == 0
    assert (out2 / "prices" / "_VIX.csv").read_bytes() == \
        (live / "prices" / "_VIX.csv").read_bytes()


def test_context_merge_refuses_missing_or_foreign_manifest(tmp_path):
    """The merge targets an EXISTING stooq staging manifest only: a dir with no manifest (the
    equities staging hasn't run) and a dir with a foreign (live Yahoo) manifest are both REFUSED
    before any write."""
    provider = make_local_stooq_provider(_make_world_archive(tmp_path))
    live = _make_live_seed_fixture(tmp_path)

    empty = tmp_path / "empty-out"
    empty.mkdir()
    rc = run_context_merge(provider, empty, live_seed_dir=live,
                           fetch_vix_rows=lambda start, end: [])
    assert rc == EXIT_CONFLICT
    assert not (empty / "prices").exists()

    foreign = tmp_path / "live-shaped"
    foreign.mkdir()
    (foreign / "meta.json").write_text(json.dumps({
        "source": "Yahoo Finance chart API (query1.finance.yahoo.com/v8/finance/chart)",
        "window": {"start": "2021-01-04", "end": "2026-05-28"},
        "symbols": [],
    }))
    rc2 = run_context_merge(provider, foreign, live_seed_dir=live,
                            fetch_vix_rows=lambda start, end: [])
    assert rc2 == EXIT_CONFLICT
    assert not (foreign / "prices").exists()


def test_context_merge_window_conflict_refused(tmp_path):
    """An explicit --start/--end conflicting with the manifest's pinned window is refused (never
    a mixed-window basis) — nothing staged."""
    out = _make_staged_equities_dir(tmp_path)
    live = _make_live_seed_fixture(tmp_path)
    provider = make_local_stooq_provider(_make_world_archive(tmp_path))
    rc = run_context_merge(provider, out, end_arg="2026-06-30", live_seed_dir=live,
                           fetch_vix_rows=lambda start, end: [])
    assert rc == EXIT_CONFLICT
    assert not (out / "prices" / "_SPX.csv").exists()
    assert load_manifest(out)["symbols_planned"] == 6      # manifest untouched


def test_context_merge_absent_world_series_recorded_honestly(tmp_path):
    """A context series absent from its source is recorded as an honest manifest failure —
    never fabricated, and the rest of the merge still lands."""
    archive = tmp_path / "d_world_txt" / "data" / "daily" / "world" / "indices"
    _write_bulk(archive / "^spx.txt", "^SPX", [
        ("19960102", 620.73, 620.74, 613.17, 620.73, 350000),
        ("20260701", 7478.8, 7521.8, 7449.6, 7483.2, 2583762787),
    ])  # NO ^ndx.txt / ^dji.txt in this bundle
    out = _make_staged_equities_dir(tmp_path)
    live = _make_live_seed_fixture(tmp_path)
    provider = make_local_stooq_provider(tmp_path / "d_world_txt")

    rc = run_context_merge(provider, out, live_seed_dir=live,
                           fetch_vix_rows=lambda start, end: list(_deep_vix_rows()))
    assert rc == 0
    assert (out / "prices" / "_SPX.csv").exists()
    assert not (out / "prices" / "_NDX.csv").exists()
    meta = load_manifest(out)
    assert set(meta["failed"]) == {"SATS", "^NDX", "^DJI"}
    ndx = next(f for f in meta["failures"] if f["symbol"] == "^NDX")
    assert ndx["kind"] == "no_data" and "world" in ndx["detail"]


def test_regular_resume_preserves_merged_manifest_provenance(tmp_path):
    """A regular (non-context) resume over an ALREADY-MERGED staged manifest must not shrink
    `symbols_planned` or rewrite the note/source provenance — the iter-17 vendor addendum,
    accounting, and per-series vendor records survive later maintenance runs (the merge is
    never silently overwritten by a narrower invocation)."""
    out = _make_staged_equities_dir(tmp_path)
    live = _make_live_seed_fixture(tmp_path)
    provider = make_local_stooq_provider(_make_world_archive(tmp_path))
    assert run_context_merge(provider, out, live_seed_dir=live,
                             fetch_vix_rows=lambda start, end: list(_deep_vix_rows())) == 0
    merged = load_manifest(out)
    assert merged["symbols_planned"] == 9

    # a later regular run with a NARROW symbol set: everything already staged -> nothing fetched
    rc = run_stooq_ingest(provider, ["AAPL"], date(1996, 1, 1), date(2026, 7, 1), out, sleep_s=0,
                          source="narrow-run-source", note="narrow-run-note")
    assert rc == 0
    meta = load_manifest(out)
    assert meta["symbols_planned"] == 9                       # not shrunk to 1
    assert meta["note"] == merged["note"]                     # addendum survives
    assert meta["source"] == merged["source"]
    spx = next(e for e in meta["symbols"] if e["symbol"] == "^SPX")
    assert spx["vendor"] == "stooq"                           # vendor records survive


def test_context_merge_redacts_env_key_on_failure_path(monkeypatch, tmp_path):
    """(B1 discipline) The context merge's NEW failure-record path routes error/URL text through
    the redaction choke point: with STOOQ_API_KEY in the environment and a failing pull whose
    message embeds it, nothing env-sourced persists into the committed manifest."""
    monkeypatch.setenv(STOOQ_API_KEY_ENV, "ctx-secret-key-9")
    out = _make_staged_equities_dir(tmp_path)
    live = _make_live_seed_fixture(tmp_path, include_vix=False)   # no fallback copy available
    provider = make_local_stooq_provider(_make_world_archive(tmp_path))

    def _keyed_failure(start, end):
        raise httpx.HTTPError(
            "Client error '401 Unauthorized' for url "
            "'https://query1.finance.yahoo.com/v8/finance/chart/^VIX"
            "?apikey=ctx-secret-key-9&period1=820454400'"
        )

    rc = run_context_merge(provider, out, live_seed_dir=live, fetch_vix_rows=_keyed_failure)
    assert rc == 0                                    # honest absence recorded; suite is the gate
    meta_text = (out / "meta.json").read_text()
    assert "ctx-secret-key-9" not in meta_text        # never persisted (anti-goal: no secrets)
    meta = json.loads(meta_text)
    vix_failure = next(f for f in meta["failures"] if f["symbol"] == "^VIX")
    assert "apikey=***" in vix_failure["detail"]      # evidence kept, secret stripped


# ---------------------------------------------------------------------------
# iter-17: --stage-context CLI wiring
# ---------------------------------------------------------------------------

def test_parser_stage_context_flag_default_off():
    assert build_parser().parse_args([]).stage_context is False
    assert build_parser().parse_args(["--stage-context"]).stage_context is True


def test_stage_context_requires_stooq_local():
    """--stage-context reads the LOCAL world bundle; the yahoo and stooq-network providers refuse
    it (the ^VIX Yahoo leg is internal to the mode, never a manifest-writing yahoo run)."""
    assert main(["--stage-context"]) == EXIT_CONFLICT
    assert main(["--provider", "stooq", "--stage-context"]) == EXIT_CONFLICT


def test_stage_context_refuses_missing_or_worldless_archive(tmp_path):
    """Missing --archive-dir path -> REFUSED; an archive with NO ^xxx.txt world files (e.g. the
    US-only d_us_txt tree) -> REFUSED for context staging (wrong bundle, before any write)."""
    out = _make_staged_equities_dir(tmp_path)
    rc = main(["--provider", "stooq-local", "--stage-context", "--out", str(out),
               "--archive-dir", str(tmp_path / "nope")])
    assert rc == EXIT_CONFLICT

    us_only = _make_local_archive(tmp_path)           # *.us.txt files, zero ^xxx.txt
    rc2 = main(["--provider", "stooq-local", "--stage-context", "--out", str(out),
                "--archive-dir", str(us_only)])
    assert rc2 == EXIT_CONFLICT
    assert not (out / "prices" / "_SPX.csv").exists()


def test_stage_context_routes_through_main(monkeypatch, tmp_path):
    """Full CLI path: --provider stooq-local --stage-context stages the world indexes + proxies
    and takes the sanctioned _VIX fallback when Yahoo is unreachable — exit 0, swap-completeness
    material all staged."""
    import scripts.ingest_seed as ingest_seed

    out = _make_staged_equities_dir(tmp_path)
    live = _make_live_seed_fixture(tmp_path)
    archive = _make_world_archive(tmp_path)
    monkeypatch.setattr(ingest_seed, "SEED_DIR", live)

    def _unreachable(start, end):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(ingest_seed, "_fetch_yahoo_vix_rows", _unreachable)
    rc = main(["--provider", "stooq-local", "--stage-context", "--out", str(out),
               "--archive-dir", str(archive)])
    assert rc == 0
    for name in ("_SPX.csv", "_NDX.csv", "_DJI.csv", "_TNX.csv", "_DXY.csv", "_VXN.csv"):
        assert (out / "prices" / name).exists(), name
    assert (out / "prices" / "_VIX.csv").read_bytes() == \
        (live / "prices" / "_VIX.csv").read_bytes()


# ---------------------------------------------------------------------------
# iter-17: B2 carry-forward — the proof-of-work solve is bounded
# ---------------------------------------------------------------------------

def test_solve_stooq_pow_bounded_with_honest_failure():
    """(audit B2) `_solve_stooq_pow` is a bounded loop: real difficulties still solve (regression),
    and an unsolvable challenge raises an HONEST failure at the cap — classified as a gate stop
    (resumable, never an unbounded spin)."""
    import hashlib

    n = _solve_stooq_pow(_CHALLENGE_C, 1)             # regression: the served difficulty solves
    assert hashlib.sha256(f"{_CHALLENGE_C}{n}".encode()).hexdigest().startswith("0")

    with pytest.raises(ProviderUnavailableError) as exc:
        _solve_stooq_pow("unsolvable", 64, max_iterations=250)   # 64 leading zeros: impossible
    message = str(exc.value)
    assert "250" in message and "difficulty 64" in message
    assert classify_stooq_failure(message) == "gate"  # -> retry then honest resumable stop
    assert _POW_MAX_ITERATIONS >= 1_000_000           # the default cap clears real difficulties


# ---------------------------------------------------------------------------
# iter-17: live integration — the deep ^VIX Yahoo pull (the real-system check)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_yahoo_vix_deep_pull_live_or_skip():
    """Live integration (real-data-only): one deep-window ^VIX request against the real Yahoo
    chart API. Skips honestly when the host cannot reach Yahoo — the sanctioned verbatim-copy
    fallback covers staging either way; the honest outcome is documented in the dev handoff."""
    from scripts.ingest_seed import _fetch_yahoo_vix_rows

    try:
        rows = _fetch_yahoo_vix_rows(date(1996, 1, 1), date(1996, 3, 29))
    except Exception as exc:  # noqa: BLE001 — any live failure = the documented fallback branch
        pytest.skip(f"Yahoo chart API unreachable from this host: {exc}")
    assert rows, "Yahoo returned an empty ^VIX series for a window it is known to cover"
    assert rows[0]["date"] <= "1996-01-05"            # deep coverage exists at the window start
    assert rows[-1]["date"] <= "1996-03-29"           # clipped to the requested end
    dates = [r["date"] for r in rows]
    assert dates == sorted(set(dates))                # ascending, no duplicates
    assert all(float(r["close"]) > 0 for r in rows)
