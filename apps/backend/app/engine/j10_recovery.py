"""app.engine.j10_recovery — J-10's single-use, fail-closed bounded-recovery scope guard
(goal-market-compass iter-6, 2026-08-20 incident response).

Iteration 5's own live drill (remove+backfill of 2026-08-11/2026-08-12, believing them seed-safe)
permanently deleted those two dates' `daily_prices` bars: the committed seed's real boundary is
2026-07-01 (`apps/backend/data/seed/meta.json`), five to six weeks earlier than the drill's spec
assumed, so "backfill" had nothing local to read back (full account:
`docs/handoffs/goal-market-compass-iter-5-dev.md`,
`runs/goal-session-market-compass/state/incident-2026-08-20-iter-5-superseded.md`). `docs/goal.md`
AG-9 carries a DATED, SINGLE-USE, self-closing exception (owner, 2026-08-20) authorizing exactly
one bounded live fetch, scoped to exactly `RECOVERY_DATES` and exactly `RECOVERY_SYMBOLS` below —
nothing else: no other date (in particular nothing on or after 2026-08-13), no refresh of
unaffected history, no broad backfill, no frontier advancement. This module is the fail-closed
CODE gate the exception's own text demands ("the implementation must refuse it in code, not by
convention"): every call this iteration's recovery driver makes into the fetch engine passes
through `validate_recovery_scope` first, and `still_missing_symbols` computes the minimal,
idempotent remaining request from LIVE `daily_prices` state so a retry after a partial/failed
attempt re-requests only what is still missing (never a duplicate, never an overwrite).

ITERATION 7 RETRY (vendor swap + fail-closed convention gate): iteration 6 dispatched this exact
authorization against `stooq` (the seed manifest's original vendor) and made ZERO writes — all 587
fetch requests came back HTTP 404 because Stooq now serves a SHA-256 proof-of-work JavaScript
challenge instead of CSV, a vendor-side block, not a per-symbol or transient failure (full account:
`docs/handoffs/goal-market-compass-iter-6-dev.md`). The owner responded the same day with a vendor
addendum to AG-9's exception: `RECOVERY_SOURCE` below is now `"yahoo"` — Stooq stays PERMANENTLY
EXCLUDED from this recovery (do not retry it, do not attempt to defeat its challenge, do not add a
third vendor without a new dated amendment). The addendum rides with a new fail-closed gate (J-10
step 2a, `check_adjustment_convention` below): Stooq's stored bars are split/dividend-adjusted, so
before a single byte may be written under the `yahoo` source, this module must POSITIVELY PROVE that
Yahoo's OWN split/dividend-adjusted series (`YahooProvider.get_adjusted_close`, NOT `get_daily`'s
plain `quote.close` — see that method's own docstring) agrees with the stored bars on a documented
sample of already-surviving days, within a stated tolerance. `run_gated_recovery` is the one entry
point that enforces this ordering: a `mismatch`/`inconclusive` verdict returns immediately with zero
calls capable of writing to `daily_prices`/`scanner_runs`/`data_provider_runs`. A passing check is
evidence THIS sample agreed within THIS tolerance — it is NOT evidence that Yahoo and Stooq bars are
interchangeable generally (goal.md AG-9 step 2a); no surface in this module claims otherwise.

WHY THESE ARE LITERALS, NOT `config.yaml` TUNABLES (goal.md NOTES, "Config-vs-literal judgment
call"): the two recovery dates and the derived 587-symbol missing set are INCIDENT-SPECIFIC
constants, not a reusable threshold — promoting them to config would misrepresent a single dated
exception as a standing "recovery" feature, contrary to AG-9's own "not a standing... path"
framing. `test_no_magic_numbers.py`'s `CALC_FILES` list (scoring/threshold calculation modules)
deliberately does NOT include this file, for the same reason — nothing here is a scoring weight,
band edge, or decision cutoff.

`RECOVERY_SYMBOLS` was derived from surviving evidence BEFORE any network call (J-10 step 1),
cross-validated against THREE independent sources that all agree on the same 587 symbols:

  1. `data_provider_runs` id=538 — the ACTUAL removal's own audit record (read-only, verified
     2026-08-20): `{"kind": "remove", "removed_bar_count": 1132, "removed_symbol_count": 587,
     "removed_first": "2026-08-11", "removed_last": "2026-08-12", "not_removable_bar_count": 0,
     "cascade": {"snapshot_count": 11, "snapshot_dates": [... the same 11 dates the iter-6 spec's
     BACKGROUND names ...]}}`.
  2. iter-5's own PRE-removal preview (`POST /api/data/remove/preview`, the identical range):
     `removable_bar_count: 1132, removable_symbol_count: 587, not_removable_bar_count: 0`
     (`docs/handoffs/goal-market-compass-iter-5-dev.md`).
  3. The live `daily_prices` symbol set on 2026-08-10 (the last surviving date, untouched by the
     drill): 587 symbols, verified read-only to equal the 2026-08-07 set (588 symbols, itself
     matching 2026-08-03/05/06) minus exactly one symbol (MNST) — no new arrivals either way.

One symbol — MNST — is DELIBERATELY EXCLUDED despite appearing in the frozen
`next_session_manifests` comparison-cohort payloads for both 2026-08-11 and 2026-08-12 (proving it
had a real close price at each as-of when those runs were originally scored: $45.53 / $45.98 —
roughly half MNST's contemporaneous $90-97 range on 2026-08-07, consistent with an
un-adjusted stock-split discontinuity around 2026-08-10, which is also MNST's own current last
date in `daily_prices`). Sources 1 and 2 above are BOTH direct, contemporaneous, machine-recorded
measurements taken AT OR IMMEDIATELY BEFORE removal time, and neither includes MNST; removal
itself is a plain `[start, end]` range wipe with no per-symbol filter, so if MNST had held a bar in
scope at removal time it would have been counted and removed exactly like every other symbol. The
frozen manifest cohort is an OLDER snapshot (from whenever the run was originally scored, well
before 2026-08-20) and does not by itself prove MNST's bars survived to removal time. Because
sources 1/2/3 (all closer in time to the actual deletion) disagree with the manifest cohort on this
one symbol, MNST's absence CANNOT be proven a consequence of iter-5's drill — it may equally be a
separate, pre-existing, unrelated single-symbol gap (its 2026-08-10 absence is untouched by the
drill's range, since 2026-08-10 was never in scope). Per J-10 step 1 / TC-16 ("if that set cannot
be established from evidence... stop... rather than fetching an unproven guess"), MNST is left out
of `RECOVERY_SYMBOLS`. See the iter-6 dev handoff for the full evidence trail and the explicit
owner-review flag.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_cls
from typing import Literal, Optional, Sequence

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.config import Config
from app.data_providers.base import PriceProvider, ProviderUnavailableError
from app.engine import data_manager
from app.models import DailyPrice

# --------------------------------------------------------------------------------------------------
# The single-use authorized envelope (AG-9's dated 2026-08-20 exception, J-10). Frozen literals —
# see the module docstring for why these are not config.yaml tunables.
# --------------------------------------------------------------------------------------------------
RECOVERY_DATES: frozenset[date_cls] = frozenset({date_cls(2026, 8, 11), date_cls(2026, 8, 12)})
RECOVERY_START: date_cls = min(RECOVERY_DATES)
RECOVERY_END: date_cls = max(RECOVERY_DATES)
RECOVERY_SOURCE: str = "yahoo"  # goal.md's 2026-08-20 vendor addendum (Stooq is blocked by its own
# proof-of-work challenge — see the module docstring's "ITERATION 7 RETRY" paragraph). The sole vendor
# authorized for this retry, gated behind check_adjustment_convention below. Stooq stays permanently
# excluded; a third vendor needs a new dated amendment.

# The 587-symbol derived missing set (J-10 step 1) — see the module docstring for the evidence
# trail. Sorted for a deterministic, diffable literal.
RECOVERY_SYMBOLS: frozenset[str] = frozenset({
    "A", "AAPL", "ABBV", "ABNB", "ABT", "ACGL",
    "ACN", "ADBE", "ADI", "ADM", "ADP", "ADSK",
    "AEE", "AEP", "AES", "AFL", "AIG", "AIZ",
    "AJG", "AKAM", "ALB", "ALGN", "ALL", "ALLE",
    "ALNY", "AMAT", "AMCR", "AMD", "AME", "AMGN",
    "AMP", "AMSC", "AMT", "AMZN", "ANET", "AON",
    "AOS", "APA", "APD", "APH", "APO", "APP",
    "APTV", "ARE", "ARES", "ARM", "ASML", "ATO",
    "AVB", "AVGO", "AVY", "AWK", "AXON", "AXP",
    "AZO", "BA", "BAC", "BALL", "BAX", "BBY",
    "BDX", "BEN", "BF-B", "BG", "BIIB", "BKCH",
    "BKNG", "BKR", "BLDR", "BLK", "BMY", "BNY",
    "BOTZ", "BR", "BRK-B", "BRO", "BSX", "BX",
    "BXP", "C", "CAG", "CAH", "CARR", "CASY",
    "CAT", "CB", "CBOE", "CBRE", "CCEP", "CCI",
    "CCJ", "CCL", "CDNS", "CDW", "CEG", "CF",
    "CFG", "CHD", "CHRW", "CHTR", "CI", "CIBR",
    "CIEN", "CINF", "CL", "CLSK", "CLX", "CMCSA",
    "CME", "CMG", "CMI", "CMS", "CNC", "CNP",
    "COF", "COHR", "COIN", "COO", "COP", "COR",
    "COST", "CPAY", "CPB", "CPRT", "CPT", "CRH",
    "CRL", "CRM", "CRWD", "CSCO", "CSGP", "CSX",
    "CTAS", "CTSH", "CTVA", "CVNA", "CVS", "CVX",
    "D", "DAL", "DASH", "DD", "DDOG", "DE",
    "DECK", "DELL", "DG", "DGX", "DHI", "DHR",
    "DIA", "DIS", "DLR", "DLTR", "DNN", "DOC",
    "DOV", "DOW", "DPZ", "DRI", "DTE", "DUK",
    "DVA", "DVN", "DXCM", "EA", "EBAY", "ECL",
    "ED", "EFX", "EG", "EIX", "EL", "ELV",
    "EME", "EMR", "ENTG", "EOG", "EPAM", "EQIX",
    "EQR", "EQT", "ERIE", "ES", "ESS", "ETN",
    "ETR", "EVRG", "EW", "EXC", "EXE", "EXPD",
    "EXPE", "EXR", "F", "FANG", "FAST", "FCX",
    "FDS", "FDX", "FE", "FER", "FFIV", "FICO",
    "FIS", "FISV", "FITB", "FIX", "FOX", "FOXA",
    "FRT", "FSLR", "FTNT", "FTV", "GD", "GDDY",
    "GE", "GEHC", "GEN", "GEV", "GFS", "GILD",
    "GIS", "GL", "GLW", "GM", "GNRC", "GOOG",
    "GOOGL", "GPC", "GPN", "GRMN", "GS", "GWW",
    "HACK", "HAL", "HAS", "HBAN", "HCA", "HD",
    "HIG", "HII", "HLT", "HON", "HOOD", "HPE",
    "HPQ", "HRL", "HSIC", "HST", "HSY", "HUBB",
    "HUBS", "HUM", "HWM", "IBB", "IBKR", "IBM",
    "ICE", "IDXX", "IEX", "IFF", "IGV", "INCY",
    "INSM", "INTC", "INTU", "INVH", "IP", "IQV",
    "IR", "IRM", "ISRG", "IT", "ITA", "ITB",
    "ITW", "IVZ", "IWM", "J", "JBHT", "JBL",
    "JCI", "JKHY", "JNJ", "JPM", "KBE", "KBH",
    "KDP", "KEY", "KEYS", "KHC", "KIM", "KKR",
    "KLAC", "KMB", "KMI", "KO", "KR", "KRE",
    "KTOS", "KVUE", "L", "LDOS", "LEN", "LEU",
    "LH", "LHX", "LII", "LIN", "LITE", "LLY",
    "LMT", "LNT", "LOW", "LRCX", "LULU", "LUV",
    "LVS", "LYB", "LYV", "MA", "MAA", "MAR",
    "MARA", "MAS", "MCD", "MCHP", "MCK", "MCO",
    "MDB", "MDLZ", "MDT", "MELI", "MET", "META",
    "MGM", "MKC", "MLM", "MMM", "MO", "MOS",
    "MPC", "MPWR", "MRK", "MRNA", "MRSH", "MRVL",
    "MS", "MSCI", "MSFT", "MSI", "MSTR", "MTB",
    "MTD", "MTH", "MU", "NCLH", "NDAQ", "NDSN",
    "NEE", "NEM", "NET", "NFLX", "NI", "NKE",
    "NOC", "NOW", "NRG", "NSC", "NTAP", "NTRS",
    "NUE", "NVDA", "NVO", "NVR", "NVT", "NWS",
    "NWSA", "NXPI", "O", "ODFL", "OKE", "OKTA",
    "OMC", "ON", "ORCL", "ORLY", "OTIS", "OXY",
    "PANW", "PAYX", "PCAR", "PCG", "PDD", "PEG",
    "PEP", "PFE", "PFG", "PG", "PGR", "PH",
    "PHM", "PKG", "PLD", "PLTR", "PM", "PNC",
    "PNR", "PNW", "PODD", "POOL", "POWL", "PPG",
    "PPL", "PRU", "PSA", "PSKY", "PSX", "PTC",
    "PWR", "PYPL", "Q", "QCOM", "QLYS", "QQQ",
    "QRVO", "RCL", "REG", "REGN", "RF", "RIOT",
    "RJF", "RL", "RMD", "ROBO", "ROK", "ROL",
    "ROP", "ROST", "RPD", "RSG", "RSP", "RTX",
    "RVTY", "S", "SBAC", "SBUX", "SCHW", "SHOP",
    "SHW", "SJM", "SKYY", "SLB", "SMCI", "SMH",
    "SNA", "SNDK", "SNOW", "SNPS", "SO", "SOLV",
    "SOXX", "SPG", "SPGI", "SPY", "SRE", "STE",
    "STLD", "STT", "STX", "STZ", "SW", "SWK",
    "SWKS", "SYF", "SYK", "SYY", "T", "TAP",
    "TDG", "TDY", "TEAM", "TECH", "TEL", "TENB",
    "TER", "TFC", "TGT", "TJX", "TKO", "TMO",
    "TMUS", "TOL", "TPL", "TPR", "TRGP", "TRI",
    "TRMB", "TROW", "TRV", "TSCO", "TSLA", "TSM",
    "TSN", "TT", "TTD", "TTWO", "TXN", "TXT",
    "TYL", "UAL", "UBER", "UDR", "UEC", "UHS",
    "ULTA", "UNH", "UNP", "UPS", "URA", "URI",
    "URNM", "USB", "V", "VEEV", "VICI", "VKTX",
    "VLO", "VLTO", "VMC", "VRNS", "VRSK", "VRSN",
    "VRT", "VRTX", "VST", "VTR", "VTRS", "VZ",
    "WAB", "WAT", "WBD", "WDAY", "WDC", "WEC",
    "WELL", "WFC", "WGMI", "WM", "WMB", "WMT",
    "WRB", "WSM", "WST", "WTW", "WY", "WYNN",
    "XAR", "XBI", "XEL", "XHB", "XLB", "XLC",
    "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE",
    "XLU", "XLV", "XLY", "XOM", "XYL", "XYZ",
    "YUM", "ZBH", "ZBRA", "ZS", "ZTS", "^DJI",
    "^NDX", "^SPX", "^TNX", "^VIX", "^VXN",
})

# MNST is a PROVEN-AMBIGUOUS row, explicitly excluded — see the module docstring for the full
# evidence trail. Not part of RECOVERY_SYMBOLS; recorded here only so the dev handoff and tests can
# cite the exact exclusion by name instead of it being an unexplained absence.
EXCLUDED_UNPROVEN_SYMBOLS: frozenset[str] = frozenset({"MNST"})

# --------------------------------------------------------------------------------------------------
# J-10 step 2a (iter-7 addendum): the fail-closed adjustment-convention check's own frozen literals.
# These are single-use incident-check constants for the SAME reason RECOVERY_DATES/RECOVERY_SYMBOLS
# above are (see the module docstring, "WHY THESE ARE LITERALS") — promoting them to config.yaml would
# misrepresent a one-time gate as a standing tunable.
# --------------------------------------------------------------------------------------------------
CONVENTION_CHECK_WINDOW_END: date_cls = date_cls(2026, 8, 10)  # RECOVERY_START minus one day — the last
# surviving trading day before the drill's gap (J-10 step 2a: "a small overlap window of already-
# surviving trading days (<= 2026-08-10)").
CONVENTION_CHECK_WINDOW_SIZE: int = 5  # "a small overlap window" (goal.md) — the N most recent surviving
# trading days on or before CONVENTION_CHECK_WINDOW_END, read LIVE from daily_prices (never hardcoded
# dates: the exact trading-day boundary is DB state, not a policy choice — see
# _convention_check_window_dates).
CONVENTION_CHECK_TOLERANCE: float = 0.0075  # 0.75% relative delta on close price — goal.md's OWN
# proposed default (spec NOTES): tight enough to catch a genuine convention mismatch (a full split is
# tens of percent) while tolerating ordinary cross-vendor rounding noise. Adopted UNCHANGED as the
# final tolerance (see the dev handoff for the empirical per-pair deltas observed on the real run) —
# never loosened after seeing a result, the same discipline J-09 already established.

# The convention-check sample (J-10 step 2a): >= 15 RECOVERY_SYMBOLS tickers, hardcoded for the same
# "single-use incident constant" reason as RECOVERY_SYMBOLS itself — a deterministic, documented,
# diffable sample, never re-derived per run. 20 large-cap, highly-liquid RECOVERY_SYMBOLS members
# spanning a mix of established dividend payers and growth-oriented names, so the sample can plausibly
# exercise the raw-close-vs-adjusted-close gap the module docstring's load-bearing technical finding
# warns about, not just names where the two series would trivially coincide. Sorted alphabetically for
# determinism; a TUPLE (not a set) so iteration order — and therefore the fetch-call order — is fixed.
CONVENTION_CHECK_SAMPLE_SYMBOLS: tuple[str, ...] = (
    "AAPL", "AMZN", "BAC", "CSCO", "CVX", "DIS", "GOOGL", "HD", "INTC", "JNJ",
    "JPM", "KO", "META", "MRK", "MSFT", "NVDA", "PEP", "PG", "WMT", "XOM",
)


class RecoveryScopeError(ValueError):
    """Raised when a recovery request falls outside the single-use J-10 authorization. A ValueError
    subclass — mirrors `data_manager.validate_job_request`'s existing error-mapping convention (the
    API layer maps a ValueError to an honest 4xx, never a silent no-op)."""


def validate_recovery_scope(
    *, start: date_cls, end: date_cls, symbols: Sequence[str], source: str,
) -> None:
    """Fail-closed gate: raise RecoveryScopeError for ANY request that is not fully inside the
    authorized envelope — BEFORE the caller may make a network call. Every check below must pass or
    the whole request is refused; this function never narrows a bad request to salvage it and never
    widens it to be more permissive — it only ever says yes-to-everything-asked or no."""
    if source != RECOVERY_SOURCE:
        raise RecoveryScopeError(
            f"J-10 recovery scope: source must be {RECOVERY_SOURCE!r} (goal.md's named vendor), "
            f"got {source!r}"
        )
    if start > end:
        raise RecoveryScopeError(f"J-10 recovery scope: start {start} is after end {end}")
    if start not in RECOVERY_DATES or end not in RECOVERY_DATES:
        raise RecoveryScopeError(
            f"J-10 recovery scope: [{start}, {end}] is not within the authorized "
            f"{sorted(RECOVERY_DATES)} — AG-9's dated exception covers ONLY these two dates "
            f"(nothing on or after 2026-08-13, nothing before 2026-08-11)"
        )
    if not symbols:
        raise RecoveryScopeError("J-10 recovery scope: no symbols requested")
    unauthorized = sorted(set(symbols) - RECOVERY_SYMBOLS)
    if unauthorized:
        raise RecoveryScopeError(
            f"J-10 recovery scope: {len(unauthorized)} symbol(s) outside the proven missing set: "
            f"{unauthorized[:10]}{' ...' if len(unauthorized) > 10 else ''}"
        )


def still_missing_symbols(session: Session) -> list[str]:
    """The idempotent remaining scope (TC-5/TC-6): every `RECOVERY_SYMBOLS` symbol that is missing
    AT LEAST ONE of `RECOVERY_DATES` in the LIVE `daily_prices` table right now. A symbol with BOTH
    dates already present is excluded — never re-requested, never re-fetched, never re-written; this
    is how "reject any row that already exists" is enforced for a retry (by exclusion from the
    request, not by fetching then discarding). Read-only: makes no network call and writes nothing.
    Deterministic order (sorted) so a request built from this is reproducible / diffable."""
    rows = session.exec(
        select(DailyPrice.symbol, DailyPrice.date)
        .where(DailyPrice.symbol.in_(sorted(RECOVERY_SYMBOLS)))
        .where(DailyPrice.date.in_(sorted(RECOVERY_DATES)))
    ).all()
    have: dict[str, set[date_cls]] = {}
    for symbol, d in rows:
        have.setdefault(symbol, set()).add(d)
    return sorted(s for s in RECOVERY_SYMBOLS if have.get(s, set()) != RECOVERY_DATES)


# ==================================================================================================
# J-10 step 2a (iter-7 addendum): the fail-closed adjustment-convention check
# ==================================================================================================
@dataclass(frozen=True)
class ConventionCheckPair:
    """One sampled (symbol, date) comparison — the atomic evidence unit the dev handoff cites verbatim
    (goal.md: "every sampled pair's observed delta recorded in the dev handoff"). `within_tolerance` is
    `None` only when no comparable yahoo value was obtained for this pair (never a fabricated pass)."""

    symbol: str
    trading_date: date_cls
    stored_close: float
    yahoo_adjusted_close: Optional[float]
    relative_delta: Optional[float]
    within_tolerance: Optional[bool]


@dataclass(frozen=True)
class ConventionCheckResult:
    """J-10 step 2a's one evidenced return value — held entirely in memory, never partially written.
    `verdict` is exactly one of "agree" / "mismatch" / "inconclusive"; `reason` is the human-readable
    summary the caller (and the dev handoff) cites verbatim."""

    verdict: Literal["agree", "mismatch", "inconclusive"]
    tolerance: float
    sample_symbols: tuple[str, ...]
    window_dates: tuple[date_cls, ...]
    pairs: tuple[ConventionCheckPair, ...]
    reason: str


def _convention_check_window_dates(session: Session) -> list[date_cls]:
    """The live comparison window (J-10 step 2a): the CONVENTION_CHECK_WINDOW_SIZE most recent trading
    days actually stored in `daily_prices` at or before CONVENTION_CHECK_WINDOW_END — read LIVE (never
    hardcoded), because the exact surviving trading-day boundary is DB state, not a policy choice.
    Read-only: makes no network call and writes nothing. Ascending order (oldest first)."""
    rows = session.exec(
        select(DailyPrice.date)
        .where(DailyPrice.date <= CONVENTION_CHECK_WINDOW_END)
        .distinct()
        .order_by(DailyPrice.date.desc())
        .limit(CONVENTION_CHECK_WINDOW_SIZE)
    ).all()
    return sorted(rows)


def _stored_closes(
    session: Session, symbols: Sequence[str], dates: Sequence[date_cls]
) -> dict[tuple[str, date_cls], float]:
    """The stored `daily_prices.close` for exactly the sampled (symbol, date) pairs — a small,
    column-projected select (AG-8: never a full-table/whole-row sweep). Read-only."""
    rows = session.exec(
        select(DailyPrice.symbol, DailyPrice.date, DailyPrice.close)
        .where(DailyPrice.symbol.in_(list(symbols)))
        .where(DailyPrice.date.in_(list(dates)))
    ).all()
    return {(sym, d): close for sym, d, close in rows}


def check_adjustment_convention(
    session: Session,
    *,
    provider: PriceProvider,
    sample_symbols: Optional[Sequence[str]] = None,
    window_dates: Optional[Sequence[date_cls]] = None,
    tolerance: float = CONVENTION_CHECK_TOLERANCE,
) -> ConventionCheckResult:
    """J-10 step 2a's fail-closed gate: BEFORE any write, prove that `provider`'s split/dividend-
    ADJUSTED close series for a documented sample of already-surviving days agrees with the stored
    (Stooq-sourced) `daily_prices` closes within `tolerance`. Read-only / in-memory ONLY — this
    function itself never writes to any table and never persists its fetched comparison values beyond
    its own call frame (goal.md: "held in memory... never written to the database, never cached").

    `provider` must implement `get_adjusted_close(symbol, start=..., end=...) -> dict[date, float]` —
    the additive Yahoo capability (`YahooProvider.get_adjusted_close`), NOT `get_daily`'s plain/raw
    `quote.close` (see the module docstring's load-bearing technical finding: comparing the wrong field
    would let a real mismatch pass silently, or flag a false one). A test fake implements the same
    method name.

    One call per sampled symbol (never per (symbol, date) pair), covering the whole window in one
    request. A provider failure for ANY sampled symbol makes the WHOLE verdict "inconclusive" (never a
    false "agree") and stops further comparison fetches immediately — a systemic failure gives no
    reason to expect the next call would succeed, and this is a single-use incident check, not a
    resilient production import path; every pair compared before the failure is still recorded.
    Otherwise every sampled (symbol, date) pair with BOTH a stored close and a returned yahoo value is
    compared; "mismatch" is returned if ANY pair's relative delta exceeds `tolerance` (every pair is
    still compared — the dev handoff needs every sampled pair's observed delta, not just the first
    failure); "agree" only if every sampled symbol was fetched and every compared pair is within
    tolerance. A pair with no comparable yahoo value (a date genuinely absent from the returned series)
    is recorded with `within_tolerance=None` and also forces "inconclusive" — never silently dropped
    from the sample and never counted as a pass.

    MINIMUM-EVIDENCE FLOOR (audit iter-7, B1): "agree" additionally requires that the comparison was
    non-empty AND actually covered EVERY sampled symbol. A (symbol, date) whose STORED close is absent
    is skipped (nothing to compare, never fabricated), so a sample whose symbols have no stored baseline
    yields zero comparisons — which previously returned "agree" on an empty proof and let the caller
    proceed to the write-capable fetch. An unproven sample is now "inconclusive": this gate returns
    "agree" only when agreement was POSITIVELY demonstrated on the documented sample, never merely
    "not contradicted".

    A passing ("agree") result is evidence that THIS sample agreed within THIS tolerance — it is NOT
    evidence that Yahoo and Stooq bars are interchangeable generally (goal.md AG-9 step 2a; see also
    the module docstring)."""
    symbols = tuple(sample_symbols) if sample_symbols is not None else CONVENTION_CHECK_SAMPLE_SYMBOLS
    dates = tuple(window_dates) if window_dates is not None else tuple(_convention_check_window_dates(session))
    if not symbols or not dates:
        return ConventionCheckResult(
            verdict="inconclusive", tolerance=tolerance, sample_symbols=symbols, window_dates=dates,
            pairs=(), reason="empty sample-symbol list or comparison window — nothing to compare",
        )

    stored = _stored_closes(session, symbols, dates)
    pairs: list[ConventionCheckPair] = []
    inconclusive_reason: Optional[str] = None
    for symbol in symbols:
        try:
            yahoo_series = provider.get_adjusted_close(symbol, start=dates[0], end=dates[-1])
        except ProviderUnavailableError as exc:
            inconclusive_reason = f"yahoo adjusted-close fetch failed for {symbol!r}: {exc}"
            break
        for d in dates:
            stored_close = stored.get((symbol, d))
            if stored_close is None:
                continue  # this (symbol, date) isn't actually stored — nothing to compare, never fabricated
            yahoo_close = yahoo_series.get(d)
            if yahoo_close is None:
                pairs.append(ConventionCheckPair(symbol, d, stored_close, None, None, None))
                continue
            delta = (abs(yahoo_close - stored_close) / abs(stored_close)) if stored_close else None
            pairs.append(ConventionCheckPair(
                symbol, d, stored_close, yahoo_close, delta,
                (delta is not None and delta <= tolerance),
            ))

    if inconclusive_reason is not None:
        return ConventionCheckResult(
            verdict="inconclusive", tolerance=tolerance, sample_symbols=symbols, window_dates=dates,
            pairs=tuple(pairs), reason=inconclusive_reason,
        )
    incomparable = [p for p in pairs if p.within_tolerance is None]
    if incomparable:
        return ConventionCheckResult(
            verdict="inconclusive", tolerance=tolerance, sample_symbols=symbols, window_dates=dates,
            pairs=tuple(pairs),
            reason=(
                f"{len(incomparable)}/{len(pairs)} sampled pair(s) had no comparable yahoo value "
                f"(a window date missing from the fetched series)"
            ),
        )
    failing = [p for p in pairs if not p.within_tolerance]
    if failing:
        worst = max(failing, key=lambda p: p.relative_delta or 0.0)
        return ConventionCheckResult(
            verdict="mismatch", tolerance=tolerance, sample_symbols=symbols, window_dates=dates,
            pairs=tuple(pairs),
            reason=(
                f"{len(failing)}/{len(pairs)} sampled pair(s) exceeded {tolerance:.4%} relative delta "
                f"(worst: {worst.symbol} {worst.trading_date} delta={worst.relative_delta:.4%})"
            ),
        )
    # AUDIT (iter-7, B1) — the minimum-evidence floor. Reaching here with an EMPTY or partially-covered
    # `pairs` list means nothing (or not the documented sample) was actually compared: a (symbol, date)
    # whose stored close is absent is skipped above (correctly — it is never fabricated), so a sample
    # whose symbols have no stored baseline at all produced ZERO comparisons. Without this floor the
    # function returned "agree" ("all 0 sampled pairs within 0.7500% relative delta") on that vacuum and
    # `run_gated_recovery` proceeded to the write-capable fetch/backfill — a fail-OPEN gate on exactly
    # the damaged-database condition J-10 exists to repair (live-reproduced 2026-08-20: zero pairs ->
    # "agree" -> 4 daily_prices + 2 data_provider_runs rows written on a fixture DB). "Agree" must mean
    # "positively proven on the documented sample" (goal.md AG-9 step 2a / J-10 step 2a), never
    # "nothing contradicted it". Placed AFTER the mismatch branch on purpose: a genuine out-of-tolerance
    # pair is the stronger, more diagnostic signal and must never be downgraded to "inconclusive" by a
    # coverage gap elsewhere in the sample.
    uncovered = [s for s in symbols if not any(p.symbol == s for p in pairs)]
    if not pairs or uncovered:
        return ConventionCheckResult(
            verdict="inconclusive", tolerance=tolerance, sample_symbols=symbols, window_dates=dates,
            pairs=tuple(pairs),
            reason=(
                f"insufficient evidence to prove agreement: {len(pairs)} comparable pair(s) across "
                f"{len(symbols) - len(uncovered)}/{len(symbols)} sampled symbol(s)"
                + (f" — no stored baseline for {uncovered[:10]}" if uncovered else "")
            ),
        )
    return ConventionCheckResult(
        verdict="agree", tolerance=tolerance, sample_symbols=symbols, window_dates=dates,
        pairs=tuple(pairs), reason=f"all {len(pairs)} sampled pairs within {tolerance:.4%} relative delta",
    )


@dataclass
class RecoveryOutcome:
    """One recovery-driver call's honest summary — feeds the dev handoff's provenance section.
    `data_provider_runs` already records the machine-readable half of the audit trail (the existing
    convention this iteration reuses, per J-10 step 4); this is only the human-readable return value
    the caller uses to WRITE that section, never a second provenance store."""

    requested_symbols: list[str]
    already_complete: bool  # True iff still_missing_symbols() was empty BEFORE this call (zero-work, zero network calls)
    job_summary: Optional[dict] = None  # data_manager.run_data_job's return value, or None if already_complete


def run_bounded_recovery_fetch(
    session: Session,
    engine: Engine,
    config: Config,
    *,
    provider: Optional[PriceProvider] = None,
    api_key: Optional[str] = None,
) -> RecoveryOutcome:
    """The ONE entry point for J-10 step 2 (the live fetch). Idempotent (TC-5): computes the current
    still-missing scope from LIVE `daily_prices` state, validates it through
    `validate_recovery_scope` (fail-closed — raises before `data_manager.run_data_job` is ever
    reached if anything about the computed request is wrong), and — only if something is still
    missing — dispatches exactly ONE `fetch` job through the EXISTING chunked-fetch engine
    (`app.engine.data_manager.run_data_job`, the SAME engine `POST /api/data/jobs` uses; no second
    fetch path) for exactly the remaining symbols over exactly `[RECOVERY_START, RECOVERY_END]`.
    Makes NO network call when nothing is missing (true zero-work no-op). `provider`/`api_key` are
    test/session-only injection points — `api_key` is NEVER persisted (mirrors every other call site
    in `data_manager`); stooq's own HTTP call uses no credential (see `StooqProvider`'s docstring),
    the catalog's `needs_key` flag is this environment's IP-gate acknowledgment only."""
    symbols = still_missing_symbols(session)
    if not symbols:
        return RecoveryOutcome(requested_symbols=[], already_complete=True, job_summary=None)
    validate_recovery_scope(
        start=RECOVERY_START, end=RECOVERY_END, symbols=symbols, source=RECOVERY_SOURCE
    )
    data_manager.validate_job_request(
        "fetch", RECOVERY_START, RECOVERY_END, config, source=RECOVERY_SOURCE, api_key=api_key,
    )
    job = data_manager.create_job("fetch", RECOVERY_START, RECOVERY_END, source=RECOVERY_SOURCE)
    summary = data_manager.run_data_job(
        job.job_id, config=config, engine=engine, provider=provider, api_key=api_key, symbols=symbols,
    )
    return RecoveryOutcome(requested_symbols=symbols, already_complete=False, job_summary=summary)


def run_bounded_recovery_backfill(session: Session, engine: Engine, config: Config) -> dict:
    """J-10 step 3 (derived-state rebuild): once `daily_prices` bars exist for `RECOVERY_DATES`,
    rebuild ONLY their `ScannerRun` snapshots (+ forward returns) through the normal create-once
    backfill path — hardcoded to `[RECOVERY_START, RECOVERY_END]` (the SAME module constants the
    fetch step uses — one source of truth for the date bounds) so no other as-of date can be touched
    by this call (TC-8). A true no-op (create-once) if a snapshot already exists for both dates."""
    data_manager.validate_job_request("backfill", RECOVERY_START, RECOVERY_END, config)
    job = data_manager.create_job("backfill", RECOVERY_START, RECOVERY_END, source=None)
    return data_manager.run_data_job(job.job_id, config=config, engine=engine)


# ==================================================================================================
# run_gated_recovery — the ONE J-10 retry entry point (iter-7): the causal ordering gate
# ==================================================================================================
@dataclass
class GatedRecoveryOutcome:
    """The top-level J-10 retry outcome (steps 2a-3): the convention check's own result, PLUS — only
    when it returned "agree" — the fetch and backfill outcomes. `stopped_reason` is set (with `fetch`/
    `backfill` left None) for every non-agree verdict, so a caller can tell "restored" from "honestly
    stopped" without separately inspecting three return values."""

    convention_check: ConventionCheckResult
    fetch: Optional[RecoveryOutcome] = None
    backfill: Optional[dict] = None
    stopped_reason: Optional[str] = None


def run_gated_recovery(
    session: Session,
    engine: Engine,
    config: Config,
    *,
    convention_provider: PriceProvider,
    fetch_provider: Optional[PriceProvider] = None,
    api_key: Optional[str] = None,
    convention_sample_symbols: Optional[Sequence[str]] = None,
    convention_window_dates: Optional[Sequence[date_cls]] = None,
    convention_tolerance: float = CONVENTION_CHECK_TOLERANCE,
) -> GatedRecoveryOutcome:
    """The ONE J-10 retry entry point (steps 2a->3): run the adjustment-convention check FIRST; only a
    verdict of EXACTLY "agree" reaches `run_bounded_recovery_fetch` / `run_bounded_recovery_backfill` —
    every other verdict returns immediately with `stopped_reason` set and makes NO call capable of
    writing to `daily_prices`/`scanner_runs`/`data_provider_runs`. This is the textual and causal gate
    goal.md step 2a demands: no code path below the verdict branch can reach the write-capable calls on
    a non-agree verdict. `convention_provider` and `fetch_provider` are separate injection points (they
    are the SAME `YahooProvider()` instance in production — `get_adjusted_close` for the check,
    `get_daily` for the fetch — kept separate here only so tests can inject independent fakes for each
    concern)."""
    check = check_adjustment_convention(
        session,
        provider=convention_provider,
        sample_symbols=convention_sample_symbols,
        window_dates=convention_window_dates,
        tolerance=convention_tolerance,
    )
    if check.verdict != "agree":
        return GatedRecoveryOutcome(
            convention_check=check,
            stopped_reason=f"adjustment-convention check returned {check.verdict!r}: {check.reason}",
        )
    fetch = run_bounded_recovery_fetch(session, engine, config, provider=fetch_provider, api_key=api_key)
    backfill = run_bounded_recovery_backfill(session, engine, config)
    return GatedRecoveryOutcome(convention_check=check, fetch=fetch, backfill=backfill)
