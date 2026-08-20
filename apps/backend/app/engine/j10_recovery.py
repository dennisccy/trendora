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
from typing import Optional, Sequence

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.config import Config
from app.data_providers.base import PriceProvider
from app.engine import data_manager
from app.models import DailyPrice

# --------------------------------------------------------------------------------------------------
# The single-use authorized envelope (AG-9's dated 2026-08-20 exception, J-10). Frozen literals —
# see the module docstring for why these are not config.yaml tunables.
# --------------------------------------------------------------------------------------------------
RECOVERY_DATES: frozenset[date_cls] = frozenset({date_cls(2026, 8, 11), date_cls(2026, 8, 12)})
RECOVERY_START: date_cls = min(RECOVERY_DATES)
RECOVERY_END: date_cls = max(RECOVERY_DATES)
RECOVERY_SOURCE: str = "stooq"  # goal.md's own text: "the same vendor the affected rows came from"

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
