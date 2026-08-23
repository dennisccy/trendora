"""app.engine.j10_recovery — J-10's single-use, fail-closed bounded-recovery scope guard
(goal-market-compass iter-6, extended iter-7 with the vendor swap + fail-closed adjustment-convention
gate, REDESIGNED iter-8 to the owner's per-symbol path-agreement + stable-bridge contract).

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
third vendor without a new dated amendment). The addendum rode with a fail-closed gate (J-10 step 2a)
that, AS ORIGINALLY BUILT this iteration, required Yahoo's OWN split/dividend-adjusted series
(`YahooProvider.get_adjusted_close`) to agree with the stored bars on a documented sample within an
absolute-level tolerance (`CONVENTION_CHECK_TOLERANCE = 0.0075`, now removed — see "ITERATION 8
REDESIGN" below). The real run against the live database returned a genuine `mismatch` (CVX ~0.865%,
just over the 0.75% bar) and correctly wrote nothing.

ITERATION 8 REDESIGN (owner, 2026-08-20, after iteration 7's real run): the owner withdrew the
absolute-level tolerance test AFTER seeing it produce a technically-correct-but-uninformative
"mismatch" on two oil-dividend names (CVX ~0.865%, XOM ~0.643% — both deltas uniform WITHIN the
symbol across all 5 window days, the signature of a stale retroactive dividend adjustment, not a
convention disagreement: an "adjusted close" for a fixed past date is not a stable number — vendors
recompute it retroactively on every later corporate action, so a freshly-fetched series sits
uniformly below a stale stored one even under IDENTICAL conventions). `docs/goal.md` J-10 step 2a now
specifies a two-part test that is invariant to exactly that kind of uniform offset, evaluated PER
SYMBOL (not one aggregate verdict for the whole 587):
  1. PATH AGREEMENT — do the two series move the same way over the overlap window? Each series is
     rebased to 1.0 at the EARLIEST date that symbol has a comparable pair for (goal.md: "rebased to
     1.0 at the window's earliest date" — read per-symbol so a missing anchor date for one symbol
     never blocks judging that symbol on its own available evidence); the symbol's path-agreement
     metric is the WORST (max) relative deviation between the two rebased series over the remaining
     comparable dates.
  2. STABLE MULTIPLICATIVE BRIDGE — the per-day stored/fallback ratio across the same comparable
     dates; the symbol's bridge-dispersion metric is the relative range `(max-min)/mean` of those
     ratios.
A symbol passes ("agree") only if BOTH metrics are within their precommitted bounds AND the symbol has
at least `MIN_COMPARABLE_PAIRS_PER_SYMBOL` comparable pairs (the per-symbol form of iter-7 audit B1's
minimum-evidence floor — see below). Its bridge factor — the MEAN of its per-day ratios — is then
APPLIED: multiplied onto all four OHLC fields of its two fetched recovery-date bars (never volume)
before insert; never a raw fallback value written unchanged (goal.md: "Passing the gate does NOT
authorize inserting raw Yahoo adjusted-close values unchanged").

This redesign also resolves three findings the iter-7 audit flagged "close in the same turn"
(`docs/handoffs/goal-market-compass-iter-7-audit.md`):
  - B2 ("one series, end to end"): the iter-7 gate validated `get_adjusted_close` (Yahoo's adjusted
    close) while the SAME UNCHANGED restore path wrote `get_daily`'s raw close — a ~0.086% gap on
    AAPL the iter-7 developer measured directly. Rather than build a second parsing capability to
    derive an "adjusted OHLC" series, this redesign adopts the spec NOTES' offered simplification:
    calibrate the bridge on `get_daily`'s RAW close — the EXACT SAME method, called the same way, that
    `run_bounded_recovery_fetch` already uses to restore bars — so `check_adjustment_convention_
    per_symbol` and the restoration fetch read the identical provider method/field, symbol by symbol.
    One series, one code path; no crossover is possible because there is only one series in play at
    all. (Logged to `assumptions.md` per the spec NOTES' explicit ask.) `YahooProvider.get_adjusted_
    close`/`_parse_adjusted_close` stay in place — additive, unused by this module now, but tested
    (resolves T2) — in case a future iteration judges the adjusted-close comparison worth reviving.
  - B3 (persisted per-pair evidence): `run_gated_recovery` now persists `convention_evidence_to_dict`'s
    FULL per-pair record (every sampled symbol, every window date, stored close, fallback close,
    ratio) to `evidence_path` — a run artifact under `runs/goal-market-compass-iter-8/` on the real
    driver path — BEFORE a single verdict is used for anything else. That artifact, not prose, is the
    sole admissible calibration input (goal.md, verbatim: "Numbers that survive only as prose in a
    handoff are not calibration evidence").
  - B5 (non-overridable thresholds): `run_gated_recovery`'s signature no longer accepts a tolerance,
    dispersion-bound, sample, or window override AT ALL — contrast the iter-7 signature, which exposed
    all four as caller-settable parameters. `check_adjustment_convention_per_symbol` (one level below
    the production entry point) still accepts `sample_symbols`/`window_dates` for direct unit testing
    of the ladder logic in isolation — but `run_gated_recovery` itself calls it with neither override,
    on every real run, and accepts no threshold parameter of any kind.
  - B6 (cheap defence-in-depth, audit-recommended, not itself a finding): `_BridgeApplyingProvider` —
    the ONE place this iteration introduces a transforming write path — asserts every returned bar's
    date falls inside `[RECOVERY_START, RECOVERY_END]` before transforming/returning it.

Iter-7 audit B1's minimum-evidence floor is carried forward in PER-SYMBOL form
(`MIN_COMPARABLE_PAIRS_PER_SYMBOL`, evaluated in `_compute_symbol_verdict` AFTER the mismatch branch,
exactly as before, so a genuine per-symbol disagreement can never be downgraded to `"inconclusive"` by
a coverage gap): a symbol with fewer comparable pairs than the floor — including zero — is
`"inconclusive"`, never `"agree"`, no matter how clean the few available pairs look (goal.md: "Zero
usable pairs can NEVER produce agreement... is not evidence, it is the absence of evidence").

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

import json
from dataclasses import dataclass
from datetime import date as date_cls
from pathlib import Path
from typing import Literal, Optional, Sequence

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.config import Config
from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError
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
# authorized for this retry, gated behind check_adjustment_convention_per_symbol below. Stooq stays
# permanently excluded; a third vendor needs a new dated amendment.

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
    API layer maps a ValueError to an honest 4xx, never a silent no-op). iter-8: also raised by
    `_BridgeApplyingProvider` for the two internal-invariant conditions described on that class — a
    symbol with no passing bridge factor, or a bar dated outside the authorized window — both of
    which are "refuse to touch something outside authorized scope", the same family this error
    already names."""


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
# J-10 step 2a (iter-8 redesign): the fail-closed adjustment-convention check's own frozen literals.
# These are single-use incident-check constants for the SAME reason RECOVERY_DATES/RECOVERY_SYMBOLS
# above are (see the module docstring, "WHY THESE ARE LITERALS") — promoting them to config.yaml would
# misrepresent a one-time gate as a standing tunable. Fixed here BEFORE this iteration's live
# comparison run and never adjusted afterward (goal.md: loosening a threshold to convert a failure
# into a pass is forbidden, and doing so is itself a reportable violation).
# --------------------------------------------------------------------------------------------------
CONVENTION_CHECK_WINDOW_END: date_cls = date_cls(2026, 8, 10)  # RECOVERY_START minus one day — the last
# surviving trading day before the drill's gap (J-10 step 2a: "a small overlap window of already-
# surviving trading days (<= 2026-08-10)").
CONVENTION_CHECK_WINDOW_SIZE: int = 5  # "a small overlap window" (goal.md) — the N most recent surviving
# trading days on or before CONVENTION_CHECK_WINDOW_END, read LIVE from daily_prices (never hardcoded
# dates: the exact trading-day boundary is DB state, not a policy choice — see
# _convention_check_window_dates).

PATH_AGREEMENT_TOLERANCE: float = 0.005  # max relative deviation, at ANY single comparable date, of
# the fallback series rebased to 1.0 at its earliest comparable date vs. the stored series rebased the
# same way — "do the two series move together", invariant to a uniform multiplicative offset by
# construction (goal.md step 2a, part 1). Deliberately a bit TIGHTER than goal.md's own 0.75% figure
# for the now-superseded absolute-level test: rebasing specifically cancels the dominant source of
# "ordinary cross-vendor noise" that 0.75% was calibrated for (a roughly-constant per-symbol offset —
# exactly what a stale-adjustment/ex-dividend gap looks like, and exactly what rebasing removes), so
# the residual this test actually measures should be materially smaller. iter-7's real-run evidence
# supports generous headroom even at this tighter bound: CVX/XOM's per-day delta printed identical to
# 5 decimal places across all 5 independent trading days (< 0.00001 percentage points of spread) — a
# rebased-path residual several orders of magnitude below 0.5%. Precommitted before this iteration's
# live run; never adjusted after seeing a result (see `assumptions.md`'s iter-8 developer entry for
# the full reasoning, including why this and BRIDGE_DISPERSION_BOUND are deliberately NOT the same
# magnitude).
BRIDGE_DISPERSION_BOUND: float = 0.015  # max relative range `(max(ratio) - min(ratio)) / mean(ratio)`
# of the per-day stored/fallback ratio across a symbol's comparable window dates (goal.md step 2a,
# part 2 — "stable... its dispersion across the window within a precommitted bound"). DELIBERATELY
# LOOSER than PATH_AGREEMENT_TOLERANCE — not an arbitrary choice: for a small (5-day) window these two
# metrics are mathematically close cousins (a per-day ratio that is stable necessarily makes the
# rebased paths agree, and a single-date perturbation moves both statistics by a similar order of
# magnitude — verified numerically while building this module's tests), so using two thresholds close
# in value would make one nearly always redundant with the other, defeating goal.md's explicit intent
# that these be two INDEPENDENTLY meaningful tests (TC-4: a symbol can fail path agreement while its
# bridge dispersion stays low). Bridge dispersion is also the anchor-INDEPENDENT statistic (it does not
# single out whichever date happens to be earliest, unlike path agreement) — modest extra headroom
# avoids penalizing that robustness. 1.5% stays far below the "tens of percent" scale of an actual
# split/convention mismatch, though a marginal within-window corporate-action shift close to CVX/XOM's
# own ~0.6-0.9% scale might not by itself trip this bound — path agreement, being the tighter
# threshold, is the first line of defense for that case; this tradeoff is stated honestly, not hidden.
MIN_COMPARABLE_PAIRS_PER_SYMBOL: int = 3  # of the CONVENTION_CHECK_WINDOW_SIZE=5 window dates, a
# symbol needs comparable evidence (both sides present and strictly positive) on a CLEAR MAJORITY
# (3 of 5) before "agree" may ever be reported — the per-symbol form of iter-7 audit B1's "zero pairs
# can never mean agree", extended with an explicit floor above zero: 1-2 pairs cannot show a genuine
# repeated "shape" (rebasing to a single other point proves nothing about a pattern, and a 2-point
# dispersion stat is easily coincidence). No iter-7 precedent anchors this exact number (the old
# aggregate gate had no per-symbol floor) — a documented judgment call, precommitted before the live
# run (see assumptions.md).

# The convention-check sample (J-10 step 2a): >= 15 RECOVERY_SYMBOLS tickers, hardcoded for the same
# "single-use incident constant" reason as RECOVERY_SYMBOLS itself — a deterministic, documented,
# diffable sample, never re-derived per run. 20 large-cap, highly-liquid RECOVERY_SYMBOLS members
# spanning a mix of established dividend payers and growth-oriented names, so the sample can plausibly
# exercise the raw-close-vs-adjusted-close gap the module docstring's load-bearing technical finding
# warns about, not just names where the two series would trivially coincide. UNCHANGED from iter-7
# (kept, not re-derived — deliberately: this iteration's job is to prove the REDESIGNED gate mechanism
# on real evidence, not to chase coverage by widening the sample; goal.md's own host-safety note asks
# for a "modest" sample, and OUT OF SCOPE forbids widening it to chase coverage after seeing results —
# choosing a fresh, larger, still-precommitted sample up front was considered and declined for this
# iteration, see assumptions.md). Sorted alphabetically for determinism; a TUPLE (not a set) so
# iteration order — and therefore the fetch-call order — is fixed.
CONVENTION_CHECK_SAMPLE_SYMBOLS: tuple[str, ...] = (
    "AAPL", "AMZN", "BAC", "CSCO", "CVX", "DIS", "GOOGL", "HD", "INTC", "JNJ",
    "JPM", "KO", "META", "MRK", "MSFT", "NVDA", "PEP", "PG", "WMT", "XOM",
)


@dataclass(frozen=True)
class ConventionCheckPair:
    """One (symbol, window-date) comparison point — the atomic evidence unit persisted verbatim to the
    run artifact (B3) so a bridge factor is traceable to specific rows, never merely asserted in prose.
    `fallback_close`/`ratio` are `None` only when this window date had a stored baseline but no usable
    fallback value (a provider gap, or a non-positive close on either side) — recorded, never silently
    dropped. A window date with NO stored baseline at all is never even turned into a pair (nothing to
    anchor a comparison to — see `_compute_symbol_verdict`)."""

    symbol: str
    trading_date: date_cls
    stored_close: float
    fallback_close: Optional[float]
    ratio: Optional[float]  # stored_close / fallback_close — the per-day bridge estimate


@dataclass(frozen=True)
class SymbolConventionVerdict:
    """One sampled symbol's two-part gate outcome (J-10 step 2a, iter-8 redesign). `verdict` is
    exactly one of "agree" / "mismatch" / "inconclusive"; `bridge_factor` is set ONLY on "agree" — the
    mean per-day stored/fallback ratio, the single number `_BridgeApplyingProvider` multiplies onto
    every OHLC field of this symbol's two recovery-date bars before insert (never a raw fallback
    value, never volume)."""

    symbol: str
    verdict: Literal["agree", "mismatch", "inconclusive"]
    reason: str
    pairs: tuple[ConventionCheckPair, ...]
    comparable_pair_count: int
    path_agreement_max_delta: Optional[float]
    bridge_dispersion: Optional[float]
    bridge_factor: Optional[float]


@dataclass(frozen=True)
class ConventionCheckBatchResult:
    """The whole live comparison run's result — one `SymbolConventionVerdict` per sampled symbol
    (deterministic sample order), plus the precommitted thresholds actually applied (recorded here,
    not only in module source, so the persisted evidence artifact is self-describing without
    cross-referencing code)."""

    path_agreement_tolerance: float
    bridge_dispersion_bound: float
    min_comparable_pairs: int
    sample_symbols: tuple[str, ...]
    window_dates: tuple[date_cls, ...]
    verdicts: tuple[SymbolConventionVerdict, ...]


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


def _compute_symbol_verdict(
    symbol: str,
    window_dates: Sequence[date_cls],
    stored: dict[date_cls, float],
    fallback: dict[date_cls, float],
) -> SymbolConventionVerdict:
    """The per-symbol two-part verdict ladder (J-10 step 2a, iter-8 redesign) — a PURE function (no
    I/O), so every degenerate-input scenario (zero pairs, below-floor coverage, one-test-only failure)
    is directly unit-testable with hand-built dicts, no DB/provider fixture required.

    `stored`/`fallback` are keyed by date, already scoped to `symbol` and to `window_dates` by the
    caller (`check_adjustment_convention_per_symbol`). A pair is COMPARABLE only when BOTH sides are
    present and strictly positive (a non-positive price is never a real quote — defensive, never
    fabricated). Ladder, in order:
      1. Fewer than 2 comparable pairs -> "inconclusive" (cannot compute ANY metric: path agreement
         needs an anchor plus at least one more point; a "dispersion" over a single ratio is a vacuous
         zero-spread that proves nothing — the exact B1 trap, in per-symbol form).
      2. Compute path-agreement (the max, over every non-anchor comparable date, of the relative
         difference between the two series each rebased to 1.0 at the EARLIEST comparable date) and
         bridge-dispersion (the relative range `(max-min)/mean` of the per-day stored/fallback ratio
         across every comparable date). EITHER exceeding its precommitted bound -> "mismatch" —
         checked BEFORE the evidence floor below, so a genuine disagreement is never downgraded to
         "inconclusive" by a coverage gap elsewhere (iter-7 audit B1, carried into per-symbol form —
         TC-6).
      3. Fewer comparable pairs than MIN_COMPARABLE_PAIRS_PER_SYMBOL (but >= 2, or the ladder would
         already have stopped at step 1) -> "inconclusive" — the available evidence didn't contradict
         agreement, but "not contradicted" is not "proven" (goal.md: "zero usable pairs can NEVER
         produce agreement"; the same reasoning extended to "too few").
      4. Otherwise -> "agree"; the recorded bridge factor is the MEAN of the per-day stored/fallback
         ratios (the "stable" ratio the dispersion check just proved is nearly constant across the
         window, so mean/median/anchor-ratio would all but coincide numerically — mean chosen as the
         simplest, tie-free central-tendency statistic)."""
    pairs: list[ConventionCheckPair] = []
    for d in window_dates:
        stored_close = stored.get(d)
        if stored_close is None:
            continue  # nothing stored to compare against — never fabricated, never recorded as a pair
        fallback_close = fallback.get(d)
        ratio = (
            stored_close / fallback_close
            if fallback_close is not None and fallback_close > 0 and stored_close > 0
            else None
        )
        pairs.append(ConventionCheckPair(
            symbol=symbol, trading_date=d, stored_close=stored_close,
            fallback_close=fallback_close, ratio=ratio,
        ))

    comparable = [p for p in pairs if p.ratio is not None]
    if len(comparable) < 2:
        return SymbolConventionVerdict(
            symbol=symbol, verdict="inconclusive",
            reason=(
                f"only {len(comparable)} comparable pair(s) (both sides present and positive) — need "
                f"at least 2 to evaluate path agreement or bridge stability at all"
            ),
            pairs=tuple(pairs), comparable_pair_count=len(comparable),
            path_agreement_max_delta=None, bridge_dispersion=None, bridge_factor=None,
        )

    ratios = [p.ratio for p in comparable]
    mean_ratio = sum(ratios) / len(ratios)
    bridge_dispersion = (max(ratios) - min(ratios)) / mean_ratio

    anchor = comparable[0]  # earliest comparable date — `comparable` preserves window_dates' ascending order
    path_deltas = []
    for p in comparable[1:]:
        rebased_stored = p.stored_close / anchor.stored_close
        rebased_fallback = p.fallback_close / anchor.fallback_close
        path_deltas.append(abs(rebased_fallback - rebased_stored) / rebased_stored)
    path_agreement_max_delta = max(path_deltas)  # len(comparable) >= 2 guarantees >= 1 delta

    path_fails = path_agreement_max_delta > PATH_AGREEMENT_TOLERANCE
    bridge_fails = bridge_dispersion > BRIDGE_DISPERSION_BOUND
    if path_fails or bridge_fails:
        failed: list[str] = []
        if path_fails:
            failed.append("path agreement")
        if bridge_fails:
            failed.append("bridge stability")
        return SymbolConventionVerdict(
            symbol=symbol, verdict="mismatch",
            reason=(
                f"failed {' and '.join(failed)}: path_agreement_max_delta={path_agreement_max_delta:.4%} "
                f"(tolerance {PATH_AGREEMENT_TOLERANCE:.4%}), bridge_dispersion={bridge_dispersion:.4%} "
                f"(bound {BRIDGE_DISPERSION_BOUND:.4%}), over {len(comparable)} comparable pair(s)"
            ),
            pairs=tuple(pairs), comparable_pair_count=len(comparable),
            path_agreement_max_delta=path_agreement_max_delta, bridge_dispersion=bridge_dispersion,
            bridge_factor=None,
        )

    # AUDIT B1, carried into per-symbol form: neither test was contradicted, but that alone is not
    # proof — a below-floor sample must not be reported "agree" merely because it happened not to fail.
    if len(comparable) < MIN_COMPARABLE_PAIRS_PER_SYMBOL:
        return SymbolConventionVerdict(
            symbol=symbol, verdict="inconclusive",
            reason=(
                f"only {len(comparable)} comparable pair(s) (< the {MIN_COMPARABLE_PAIRS_PER_SYMBOL}-pair "
                f"evidence floor); path agreement and bridge stability both held on what little evidence "
                f"existed, but that is insufficient to call agreement PROVEN (goal.md: 'not contradicted' "
                f"is not evidence)"
            ),
            pairs=tuple(pairs), comparable_pair_count=len(comparable),
            path_agreement_max_delta=path_agreement_max_delta, bridge_dispersion=bridge_dispersion,
            bridge_factor=None,
        )
    return SymbolConventionVerdict(
        symbol=symbol, verdict="agree",
        reason=(
            f"path agreement (max delta {path_agreement_max_delta:.4%} <= {PATH_AGREEMENT_TOLERANCE:.4%}) "
            f"and a stable bridge (dispersion {bridge_dispersion:.4%} <= {BRIDGE_DISPERSION_BOUND:.4%}) "
            f"over {len(comparable)} comparable pairs"
        ),
        pairs=tuple(pairs), comparable_pair_count=len(comparable),
        path_agreement_max_delta=path_agreement_max_delta, bridge_dispersion=bridge_dispersion,
        bridge_factor=mean_ratio,
    )


def check_adjustment_convention_per_symbol(
    session: Session,
    *,
    provider: PriceProvider,
    sample_symbols: Optional[Sequence[str]] = None,
    window_dates: Optional[Sequence[date_cls]] = None,
) -> ConventionCheckBatchResult:
    """J-10 step 2a's fail-closed gate, iter-8 REDESIGN — PER SYMBOL, not one aggregate verdict (see
    the module docstring's "ITERATION 8 REDESIGN" paragraph for the full rationale). For every sampled
    symbol, independently: fetch `provider.get_daily(symbol, start=window[0], end=window[-1])` — the
    EXACT SAME method/field `run_bounded_recovery_fetch` uses to restore the recovery-date bars (B2 /
    TC-9: one series, end to end, no crossover with an adjusted-close series) — and hand the two
    series to `_compute_symbol_verdict`, the pure ladder function.

    A provider failure (`ProviderUnavailableError`, including its `RateLimitError` subclass) on ONE
    symbol makes only THAT symbol "inconclusive" and does not stop the batch — deliberately different
    from the iter-7 aggregate gate's "stop the whole check on the first failure", which made sense
    only when a single failure poisoned one shared verdict. A per-symbol design lets every OTHER
    sampled symbol's evidence stand on its own; a systemic Yahoo outage still naturally yields an
    all-"inconclusive" batch — an honest zero-restored outcome (TC-10) — with no special-casing
    needed.

    Read-only / in-memory ONLY: makes no write to any table and persists nothing itself (the caller,
    `run_gated_recovery`, is responsible for persisting the evidence artifact — B3). `sample_symbols`/
    `window_dates` are test-injection points ONLY; they are NOT exposed on `run_gated_recovery`, the
    production entry point (B5) — this function is one level below it."""
    symbols = tuple(sample_symbols) if sample_symbols is not None else CONVENTION_CHECK_SAMPLE_SYMBOLS
    dates = tuple(window_dates) if window_dates is not None else tuple(_convention_check_window_dates(session))
    if not symbols or not dates:
        return ConventionCheckBatchResult(
            path_agreement_tolerance=PATH_AGREEMENT_TOLERANCE,
            bridge_dispersion_bound=BRIDGE_DISPERSION_BOUND,
            min_comparable_pairs=MIN_COMPARABLE_PAIRS_PER_SYMBOL,
            sample_symbols=symbols, window_dates=dates, verdicts=(),
        )

    stored = _stored_closes(session, symbols, dates)
    verdicts: list[SymbolConventionVerdict] = []
    for symbol in symbols:
        symbol_stored = {d: stored[(symbol, d)] for d in dates if (symbol, d) in stored}
        try:
            bars = provider.get_daily(symbol, start=dates[0], end=dates[-1])
            symbol_fallback = {b.date: b.close for b in bars if b.date in dates}
        except ProviderUnavailableError as exc:
            verdicts.append(SymbolConventionVerdict(
                symbol=symbol, verdict="inconclusive",
                reason=f"fallback fetch failed: {exc}",
                pairs=(), comparable_pair_count=0,
                path_agreement_max_delta=None, bridge_dispersion=None, bridge_factor=None,
            ))
            continue
        verdicts.append(_compute_symbol_verdict(symbol, dates, symbol_stored, symbol_fallback))

    return ConventionCheckBatchResult(
        path_agreement_tolerance=PATH_AGREEMENT_TOLERANCE,
        bridge_dispersion_bound=BRIDGE_DISPERSION_BOUND,
        min_comparable_pairs=MIN_COMPARABLE_PAIRS_PER_SYMBOL,
        sample_symbols=symbols, window_dates=dates, verdicts=tuple(verdicts),
    )


def convention_evidence_to_dict(result: ConventionCheckBatchResult) -> dict:
    """B3: the FULL per-pair evidence, serialized — the sole admissible calibration input (goal.md:
    "Numbers that survive only as prose in a handoff are not calibration evidence and may not be used
    as such"). Every field on every dataclass is included (no summarization), so the persisted
    artifact alone — with no cross-reference to a handoff or this module's source — can answer any
    question about how a bridge factor was derived. Pure / no I/O: the caller (`run_gated_recovery`)
    decides where, and whether, to write this."""
    return {
        "path_agreement_tolerance": result.path_agreement_tolerance,
        "bridge_dispersion_bound": result.bridge_dispersion_bound,
        "min_comparable_pairs": result.min_comparable_pairs,
        "sample_symbols": list(result.sample_symbols),
        "window_dates": [d.isoformat() for d in result.window_dates],
        "symbols": [
            {
                "symbol": v.symbol,
                "verdict": v.verdict,
                "reason": v.reason,
                "comparable_pair_count": v.comparable_pair_count,
                "path_agreement_max_delta": v.path_agreement_max_delta,
                "bridge_dispersion": v.bridge_dispersion,
                "bridge_factor": v.bridge_factor,
                "pairs": [
                    {
                        "trading_date": p.trading_date.isoformat(),
                        "stored_close": p.stored_close,
                        "fallback_close": p.fallback_close,
                        "ratio": p.ratio,
                    }
                    for p in v.pairs
                ],
            }
            for v in result.verdicts
        ],
    }


@dataclass
class RecoveryOutcome:
    """One recovery-driver call's honest summary — feeds the dev handoff's provenance section.
    `data_provider_runs` already records the machine-readable half of the audit trail (the existing
    convention this iteration reuses, per J-10 step 4); this is only the human-readable return value
    the caller uses to WRITE that section, never a second provenance store."""

    requested_symbols: list[str]
    already_complete: bool  # True iff the target scope was empty BEFORE this call (zero-work, zero network calls)
    job_summary: Optional[dict] = None  # data_manager.run_data_job's return value, or None if already_complete


def run_bounded_recovery_fetch(
    session: Session,
    engine: Engine,
    config: Config,
    *,
    provider: Optional[PriceProvider] = None,
    api_key: Optional[str] = None,
    symbols: Optional[Sequence[str]] = None,
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
    the catalog's `needs_key` flag is this environment's IP-gate acknowledgment only.

    iter-8: `symbols`, when given, further restricts the request to `symbols ∩ still_missing_symbols()`
    — still computed FRESH from live state, so idempotency is preserved (a symbol already restored by
    a prior partial attempt is excluded even if the caller's list still names it). `None` (the
    default) preserves the exact original behavior — every pre-iter-8 caller/test is unaffected. This
    is how `run_gated_recovery` restricts the real fetch to only the symbols that passed the per-
    symbol convention gate, without a second write/request path.

    iter-9 (J-10 gap #3 / audit B6): EVERY requested symbol must already carry a recorded passing
    bridge factor — i.e. `provider` must be a `_BridgeApplyingProvider` built from a passing verdict
    for that symbol, or the whole call raises `RecoveryScopeError` before any network call. A raw/
    unwrapped provider (including the `provider=None` catalog-resolved default) has zero recorded
    factors, so it can no longer insert anything for a recovery-scope symbol. The only legitimate way
    to reach this function with a real recovery-scope request is through `run_gated_recovery` /
    `run_gated_population_recovery`, which always supply a `_BridgeApplyingProvider`."""
    missing = still_missing_symbols(session)
    target = sorted(set(symbols) & set(missing)) if symbols is not None else missing
    if not target:
        return RecoveryOutcome(requested_symbols=[], already_complete=True, job_summary=None)
    validate_recovery_scope(
        start=RECOVERY_START, end=RECOVERY_END, symbols=target, source=RECOVERY_SOURCE
    )
    # iter-9 (J-10 gap #3 / audit B6): close the un-gated back door. `provider` only ever carries a
    # RECORDED passing bridge factor for a symbol when it is a `_BridgeApplyingProvider` built from a
    # passing convention-check verdict (the ONLY place this module constructs one — inside
    # `_run_gated_recovery_core`, run_gated_recovery's/run_gated_population_recovery's shared body). Any
    # other provider (a raw client, or none at all) has recorded bridge factors for ZERO symbols, so
    # EVERY requested symbol is "ungated" and the whole request is refused before any network call —
    # this function can no longer insert an untransformed row for a recovery-scope symbol that never
    # passed the per-symbol path-agreement + stable-bridge gate, structurally, not by caller discipline.
    gated_factors = provider._bridge_factors if isinstance(provider, _BridgeApplyingProvider) else {}
    ungated = sorted(s for s in target if s not in gated_factors)
    if ungated:
        raise RecoveryScopeError(
            f"J-10 recovery: refusing {len(ungated)} symbol(s) with no passing bridge factor on "
            f"record: {ungated[:10]}{' ...' if len(ungated) > 10 else ''} -- run_bounded_recovery_fetch "
            f"only ever inserts a symbol that reached verdict=='agree' through the per-symbol convention "
            f"gate (call run_gated_recovery / run_gated_population_recovery instead of this function "
            f"directly for a real recovery-scope fetch)"
        )
    data_manager.validate_job_request(
        "fetch", RECOVERY_START, RECOVERY_END, config, source=RECOVERY_SOURCE, api_key=api_key,
    )
    job = data_manager.create_job("fetch", RECOVERY_START, RECOVERY_END, source=RECOVERY_SOURCE)
    summary = data_manager.run_data_job(
        job.job_id, config=config, engine=engine, provider=provider, api_key=api_key, symbols=target,
    )
    return RecoveryOutcome(requested_symbols=target, already_complete=False, job_summary=summary)


def run_bounded_recovery_backfill(session: Session, engine: Engine, config: Config) -> dict:
    """J-10 step 3 (derived-state rebuild): once `daily_prices` bars exist for `RECOVERY_DATES`,
    rebuild ONLY their `ScannerRun` snapshots (+ forward returns) through the normal create-once
    backfill path — hardcoded to `[RECOVERY_START, RECOVERY_END]` (the SAME module constants the
    fetch step uses — one source of truth for the date bounds) so no other as-of date can be touched
    by this call (TC-8). A true no-op (create-once) if a snapshot already exists for both dates."""
    data_manager.validate_job_request("backfill", RECOVERY_START, RECOVERY_END, config)
    job = data_manager.create_job("backfill", RECOVERY_START, RECOVERY_END, source=None)
    return data_manager.run_data_job(job.job_id, config=config, engine=engine)


class _BridgeApplyingProvider(PriceProvider):
    """iter-8 (B2/TC-8): wraps a real provider and transforms every returned bar's OHLC fields by that
    SYMBOL's passing bridge factor before the caller ever sees them — so the SINGLE existing
    `data_manager` chunked-fetch insert path (the one every other fetch job already uses) writes
    already-bridge-transformed values, with NO second write path (goal.md: "Passing the gate does NOT
    authorize inserting raw Yahoo adjusted-close values unchanged"). Volume passes through UNSCALED
    ("volume is not a price and is not scaled" — goal.md, verbatim).

    B6 (audit, cheap defence-in-depth): this is the ONE place iter-8 introduces a transforming write
    path, so the cheap extra check belongs here, closest to the insert it feeds — every returned bar's
    date is asserted inside `[RECOVERY_START, RECOVERY_END]` before it is transformed/returned.

    Raises `RecoveryScopeError` for a symbol with no passing bridge factor — an internal-invariant
    guard (the caller must only ever request symbols that passed the gate), not a normal runtime
    provider condition; this is what stands between "the gate said mismatch" and "inserted anyway on
    a guessed factor" if a future caller is ever wired up wrong (goal.md: "Never insert on a guessed
    factor to improve coverage")."""

    def __init__(self, inner: PriceProvider, bridge_factors: dict[str, float]):
        self._inner = inner
        self._bridge_factors = dict(bridge_factors)

    def get_daily(
        self, symbol: str, start: Optional[date_cls] = None, end: Optional[date_cls] = None,
    ) -> list[Bar]:
        if symbol not in self._bridge_factors:
            raise RecoveryScopeError(
                f"J-10 recovery: {symbol!r} has no passing bridge factor — refusing to fetch/insert an "
                f"untransformed bar for it (this must never happen on the real driver path: only "
                f"symbols with verdict=='agree' may ever reach this wrapper)"
            )
        factor = self._bridge_factors[symbol]
        bars = self._inner.get_daily(symbol, start=start, end=end)
        out: list[Bar] = []
        for b in bars:
            if not (RECOVERY_START <= b.date <= RECOVERY_END):
                raise RecoveryScopeError(
                    f"J-10 recovery: {symbol!r} returned a bar dated {b.date}, outside the authorized "
                    f"[{RECOVERY_START}, {RECOVERY_END}] window — refusing to transform/insert it (B6)"
                )
            out.append(Bar(
                date=b.date, open=b.open * factor, high=b.high * factor,
                low=b.low * factor, close=b.close * factor, volume=b.volume,
            ))
        return out


# ==================================================================================================
# run_gated_recovery — the ONE J-10 retry entry point (iter-7, redesigned iter-8): the causal
# ordering gate
# ==================================================================================================
@dataclass
class GatedRecoveryOutcome:
    """The top-level J-10 retry outcome (steps 2a-3): the per-symbol convention-check batch result,
    PLUS — only when at least one symbol passed — the fetch and backfill outcomes. `stopped_reason` is
    set (with `fetch`/`backfill` left None) exactly when zero symbols passed, so a caller can tell
    "restored" from "honestly stopped" without separately inspecting three return values."""

    convention_check: ConventionCheckBatchResult
    fetch: Optional[RecoveryOutcome] = None
    backfill: Optional[dict] = None
    stopped_reason: Optional[str] = None


def _check_fetch_provider_source_matches(
    convention_provider: PriceProvider, fetch_provider: Optional[PriceProvider]
) -> None:
    """iter-9 (J-10 gap #2 / audit B5): closes B2's "one series, end to end" rule at the CALL BOUNDARY,
    not just by docstring. `fetch_provider is None` (the default -> `convention_provider` itself) is
    always fine — trivially the same object, so this check is skipped entirely (an omitted
    `fetch_provider` "must keep working exactly as today", per goal.md). When a caller DOES supply a
    distinct `fetch_provider`, its `.source` (see `base.PriceProvider.source`) must equal
    `convention_provider`'s — a mismatch means the bridge would be CALIBRATED on one vendor's series
    and APPLIED to fetch a DIFFERENT vendor's series, silently re-introducing the exact crossover risk
    B2 closed for the method/field axis. Neither provider's `get_daily` is ever called by this check
    (a pure attribute comparison) — the refusal happens before any convention check or fetch."""
    if fetch_provider is None:
        return
    convention_source = getattr(convention_provider, "source", None)
    fetch_source = getattr(fetch_provider, "source", None)
    if fetch_source != convention_source:
        raise RecoveryScopeError(
            f"J-10 recovery: fetch_provider source {fetch_source!r} does not match "
            f"convention_provider source {convention_source!r} — refusing before any convention check "
            f"or fetch (B2: calibration and restoration must read the same vendor's series, end to end)"
        )


def _run_gated_recovery_core(
    session: Session,
    engine: Engine,
    config: Config,
    *,
    convention_provider: PriceProvider,
    fetch_provider: Optional[PriceProvider],
    api_key: Optional[str],
    evidence_path: Path,
    sample_symbols: Optional[Sequence[str]],
) -> GatedRecoveryOutcome:
    """The shared body of BOTH J-10 production entry points (`run_gated_recovery`'s frozen 20-name
    methodology sample, `run_gated_population_recovery`'s live recovery-population remainder) — the ONE
    place the causal ordering gate (check -> persist evidence -> collect passing -> fetch -> backfill),
    the B2 provider-mismatch guard, and the mandatory evidence artifact are implemented, so both entry
    points enforce every closed gap identically instead of duplicating the logic (and risking one
    getting the fix and the other not). `sample_symbols=None` defers to `check_adjustment_convention_
    per_symbol`'s own default (the frozen `CONVENTION_CHECK_SAMPLE_SYMBOLS`); a caller-supplied sequence
    (the population pass) overrides it — this function applies NO threshold/dispersion/window override
    either way, exactly like the iter-8 production entry point it replaces.

    Order of operations, structurally enforced (not by convention):
      1. Refuse a `fetch_provider`/`convention_provider` source mismatch (B2/B5, iter-9) — before
         anything else runs.
      2. Run the per-symbol check against `convention_provider` (read-only, in-memory) over
         `sample_symbols`.
      3. Persist the FULL per-pair evidence (B3) to the now-MANDATORY `evidence_path` — BEFORE a single
         verdict is used for anything else (TC-7/iter-9 gap #1).
      4. Collect symbols with verdict=="agree" and their bridge factors. Zero -> stop, `stopped_reason`
         set, no fetch/backfill call of any kind (TC-10).
      5. Otherwise: fetch ONLY the passing symbols (intersected with what's still actually missing, for
         idempotency) through a `_BridgeApplyingProvider` wrapping `fetch_provider` (defaulting to
         `convention_provider` itself), via the EXISTING `run_bounded_recovery_fetch` ->
         `data_manager.run_data_job` write path (no second insert path), then run the existing
         backfill."""
    _check_fetch_provider_source_matches(convention_provider, fetch_provider)
    check = check_adjustment_convention_per_symbol(
        session, provider=convention_provider, sample_symbols=sample_symbols
    )
    # iter-9 (gap #1 / audit B4): evidence_path is now a REQUIRED Path (see both public signatures
    # below) — persistence is no longer conditional on the caller remembering to pass one.
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(convention_evidence_to_dict(check), indent=2, sort_keys=True))

    passing = {v.symbol: v.bridge_factor for v in check.verdicts if v.verdict == "agree"}
    if not passing:
        return GatedRecoveryOutcome(
            convention_check=check,
            stopped_reason=(
                f"0/{len(check.verdicts)} sampled symbols passed the per-symbol path-agreement + "
                f"stable-bridge gate — nothing fetched, nothing inserted"
            ),
        )
    bridged_provider = _BridgeApplyingProvider(fetch_provider or convention_provider, passing)
    fetch = run_bounded_recovery_fetch(
        session, engine, config, provider=bridged_provider, api_key=api_key, symbols=sorted(passing),
    )
    backfill = run_bounded_recovery_backfill(session, engine, config)
    return GatedRecoveryOutcome(convention_check=check, fetch=fetch, backfill=backfill)


def run_gated_recovery(
    session: Session,
    engine: Engine,
    config: Config,
    *,
    convention_provider: PriceProvider,
    fetch_provider: Optional[PriceProvider] = None,
    api_key: Optional[str] = None,
    evidence_path: Path,
) -> GatedRecoveryOutcome:
    """The J-10 METHODOLOGY-VALIDATION entry point (steps 2a->3), iter-8 REDESIGN, iter-9 hardened.
    Always runs the per-symbol gate over the FROZEN `CONVENTION_CHECK_SAMPLE_SYMBOLS` (20 names) — never
    the recovery population; that is `run_gated_population_recovery`'s job, a fully distinct axis
    (goal.md step 2b's binding invariant: the methodology-validation sample is never re-run/re-widened
    as a validation exercise). B5: the ONLY parameters this production entry point accepts are provider
    OBJECTS, the optional `api_key`, and the (now mandatory, iter-9 gap #1) evidence-artifact write
    location — no tolerance, dispersion-bound, sample, or window override exists here at all (contrast
    the iter-7 signature, which exposed all four).

    iter-9: `evidence_path` lost its default — omitting it is refused by Python's own argument binding
    before this function's body (and therefore the convention check) ever executes (TC-6/gap #1). A
    `fetch_provider` whose `.source` does not match `convention_provider`'s is refused before any
    convention check or fetch (TC-7/gap #2, see `_check_fetch_provider_source_matches`).
    `fetch_provider` defaulting to `convention_provider` when omitted is unchanged from iter-8 (there is
    no code path by which `run_bounded_recovery_fetch` — see its own iter-9 docstring update — can be
    reached with an ungated symbol either, gap #3)."""
    return _run_gated_recovery_core(
        session, engine, config,
        convention_provider=convention_provider, fetch_provider=fetch_provider,
        api_key=api_key, evidence_path=evidence_path, sample_symbols=None,
    )


def run_gated_population_recovery(
    session: Session,
    engine: Engine,
    config: Config,
    *,
    convention_provider: PriceProvider,
    fetch_provider: Optional[PriceProvider] = None,
    api_key: Optional[str] = None,
    evidence_path: Path,
) -> GatedRecoveryOutcome:
    """iter-9's NEW J-10 POPULATION entry point — runs the SAME fixed per-symbol gate
    (`_compute_symbol_verdict`, the SAME `PATH_AGREEMENT_TOLERANCE`/`BRIDGE_DISPERSION_BOUND`/
    `MIN_COMPARABLE_PAIRS_PER_SYMBOL`, the SAME live window derivation) as `run_gated_recovery`, but
    over the LIVE recovery-population remainder (`still_missing_symbols()`) instead of the frozen
    20-name `CONVENTION_CHECK_SAMPLE_SYMBOLS` — a fully distinct axis from that methodology-validation
    sample, which this function never reads, widens, or re-derives (goal.md step 2b's binding
    invariant: "the prohibition on widening or redrawing the methodology-validation sample does not
    restrict execution over the already frozen J-10 recovery population").

    Idempotent by construction: `still_missing_symbols()` is computed FRESH at call time (BEFORE the
    convention check runs), so a symbol already fully restored (the 20 from iteration 8, or any
    population member a prior population-pass invocation already restored) is excluded from the SAMPLE
    itself — never re-calibrated, never re-fetched, never re-evaluated (TC-4/TC-9). Every symbol in the
    computed sample gets exactly one recorded verdict (TC-1); an `agree` verdict is restored (bridge-
    transformed, both recovery-date bars, idempotently); a `mismatch`/`inconclusive` verdict yields zero
    rows and its `SymbolConventionVerdict.reason` is the "requested but not restored" explanation
    (TC-3) — the caller (the committed driver script) reads `outcome.convention_check.verdicts` to build
    that list; this function persists the raw evidence, not a human-facing summary.

    Same B2/B5/B6 guarantees as `run_gated_recovery` (delegates to the SAME `_run_gated_recovery_core`):
    `evidence_path` is mandatory, a `fetch_provider` source mismatch is refused before any work, and
    `run_bounded_recovery_fetch` itself refuses any symbol without a recorded passing bridge factor."""
    population = still_missing_symbols(session)
    return _run_gated_recovery_core(
        session, engine, config,
        convention_provider=convention_provider, fetch_provider=fetch_provider,
        api_key=api_key, evidence_path=evidence_path, sample_symbols=population,
    )
