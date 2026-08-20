# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/apps/backend/app/data_providers/yahoo_provider.py b/apps/backend/app/data_providers/yahoo_provider.py
index a1626e67..b42b868d 100644
--- a/apps/backend/app/data_providers/yahoo_provider.py
+++ b/apps/backend/app/data_providers/yahoo_provider.py
@@ -9,6 +9,11 @@ real-data-only). A row whose price fields are null (a provider gap) is SKIPPED,
 
 Resolved ONLY by the on-demand Data Manager fetch path via the provider factory from the config
 `data_manager.providers` catalog; the default boot/runtime provider stays the offline `SeedProvider`.
+
+`get_adjusted_close` (iter-7, J-10 step 2a) is an additive, read-only capability alongside `get_daily`:
+it returns Yahoo's split/dividend-ADJUSTED close series (`indicators.adjclose`), not `get_daily`'s
+plain `quote.close` — used ONLY by `app.engine.j10_recovery.check_adjustment_convention`'s fail-closed
+gate, never by the ordinary fetch/import path. See that method's own docstring.
 """
 from __future__ import annotations
 
@@ -88,6 +93,84 @@ class YahooProvider(PriceProvider):
         )
         return self._parse(symbol, data, start, end)
 
+    def get_adjusted_close(
+        self,
+        symbol: str,
+        start: Optional[date_cls] = None,
+        end: Optional[date_cls] = None,
+    ) -> dict[date_cls, float]:
+        """J-10 step 2a's additive capability (goal-market-compass iter-7): the split/dividend-ADJUSTED
+        close series (Yahoo's `indicators.adjclose[0].adjclose`), keyed by date — NOT `get_daily`'s
+        plain/raw `quote.close` above. Live-confirmed (2026-08-20): the SAME chart endpoint and request
+        shape `get_daily` already uses returns `indicators.quote` AND `indicators.adjclose` side by side
+        in one response with no extra query parameter — so this is a parallel, read-only, additive
+        method for the J-10 convention-check gate only; it does NOT change `get_daily`'s own contract,
+        request shape, or callers.
+
+        Raises `ProviderUnavailableError` (never a fabricated series) on ANY failure — a network/HTTP
+        error, a chart `error` payload, a missing/empty result, or a response whose `indicators` block
+        carries no `adjclose` at all. This method deliberately does NOT fall back to the raw `quote.close`
+        in that last case — a caller comparing this against an adjusted series must know when it could
+        not get one, not silently receive the wrong field (the exact silent-mismatch risk
+        `app.engine.j10_recovery`'s module docstring documents). A date whose adjusted close is null (a
+        provider gap) is omitted from the returned dict, exactly like `get_daily` skips a null-priced bar.
+        """
+        params: dict[str, object] = {"interval": "1d"}
+        if start is not None and end is not None:
+            params["period1"] = int(datetime(start.year, start.month, start.day, tzinfo=timezone.utc).timestamp())
+            params["period2"] = int(datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=timezone.utc).timestamp())
+        else:
+            params["range"] = "1y"
+        data = fetch_json(
+            _YAHOO_CHART_URL + symbol,
+            symbol=symbol,
+            label="yahoo",
+            params=params,
+            headers=_HEADERS,
+            client=self._client,
+            timeout=self._timeout,
+        )
+        return self._parse_adjusted_close(symbol, data, start, end)
+
+    def _parse_adjusted_close(
+        self, symbol: str, data: object, start: Optional[date_cls], end: Optional[date_cls]
+    ) -> dict[date_cls, float]:
+        try:
+            chart = data["chart"]  # type: ignore[index]
+            if chart.get("error"):
+                raise ProviderUnavailableError(f"yahoo returned an error for {symbol!r}: {chart['error']}")
+            result = chart["result"]
+            if not result:
+                raise ProviderUnavailableError(f"yahoo returned no result for {symbol!r}")
+            block = result[0]
+            if not block.get("timestamp"):
+                return {}  # a well-formed empty range (see get_daily._parse) — honest zero rows, not a fault
+            timestamps = block["timestamp"]
+            adjclose_blocks = block["indicators"].get("adjclose")
+            if not adjclose_blocks:
+                raise ProviderUnavailableError(
+                    f"yahoo response for {symbol!r} carries no adjclose series — cannot verify the "
+                    f"adjustment convention from this response"
+                )
+            closes = adjclose_blocks[0]["adjclose"]
+        except (KeyError, IndexError, TypeError) as exc:  # unexpected shape — surface, never fabricate
+            raise ProviderUnavailableError(f"yahoo adjclose response unparseable for {symbol!r}: {exc}") from exc
+
+        out: dict[date_cls, float] = {}
+        try:
+            for ts, c in zip(timestamps, closes):
+                if c is None:
+                    continue  # a provider gap (null adjusted close) is skipped — never back-filled
+                d = datetime.fromtimestamp(ts, tz=timezone.utc).date()
+                if start is not None and d < start:
+                    continue
+                if end is not None and d > end:
+                    continue
+                out[d] = float(c)
+        except (ValueError, TypeError) as exc:  # malformed cell — surface, never fabricate
+            raise ProviderUnavailableError(f"yahoo adjclose response unparseable for {symbol!r}: {exc}") from exc
+        return out
+
     def get_market_cap(self, symbol: str) -> Optional[float]:
         """REAL market-cap reference for ONE symbol (J-35 expand capability, behind the same abstraction;
         yahoo is `supports_market_cap: true`). Authenticates with the no-key cookie+crumb flow (acquired
diff --git a/apps/backend/app/engine/j10_recovery.py b/apps/backend/app/engine/j10_recovery.py
index 85de620e..ab713187 100644
--- a/apps/backend/app/engine/j10_recovery.py
+++ b/apps/backend/app/engine/j10_recovery.py
@@ -17,6 +17,24 @@ through `validate_recovery_scope` first, and `still_missing_symbols` computes th
 idempotent remaining request from LIVE `daily_prices` state so a retry after a partial/failed
 attempt re-requests only what is still missing (never a duplicate, never an overwrite).
 
+ITERATION 7 RETRY (vendor swap + fail-closed convention gate): iteration 6 dispatched this exact
+authorization against `stooq` (the seed manifest's original vendor) and made ZERO writes — all 587
+fetch requests came back HTTP 404 because Stooq now serves a SHA-256 proof-of-work JavaScript
+challenge instead of CSV, a vendor-side block, not a per-symbol or transient failure (full account:
+`docs/handoffs/goal-market-compass-iter-6-dev.md`). The owner responded the same day with a vendor
+addendum to AG-9's exception: `RECOVERY_SOURCE` below is now `"yahoo"` — Stooq stays PERMANENTLY
+EXCLUDED from this recovery (do not retry it, do not attempt to defeat its challenge, do not add a
+third vendor without a new dated amendment). The addendum rides with a new fail-closed gate (J-10
+step 2a, `check_adjustment_convention` below): Stooq's stored bars are split/dividend-adjusted, so
+before a single byte may be written under the `yahoo` source, this module must POSITIVELY PROVE that
+Yahoo's OWN split/dividend-adjusted series (`YahooProvider.get_adjusted_close`, NOT `get_daily`'s
+plain `quote.close` — see that method's own docstring) agrees with the stored bars on a documented
+sample of already-surviving days, within a stated tolerance. `run_gated_recovery` is the one entry
+point that enforces this ordering: a `mismatch`/`inconclusive` verdict returns immediately with zero
+calls capable of writing to `daily_prices`/`scanner_runs`/`data_provider_runs`. A passing check is
+evidence THIS sample agreed within THIS tolerance — it is NOT evidence that Yahoo and Stooq bars are
+interchangeable generally (goal.md AG-9 step 2a); no surface in this module claims otherwise.
+
 WHY THESE ARE LITERALS, NOT `config.yaml` TUNABLES (goal.md NOTES, "Config-vs-literal judgment
 call"): the two recovery dates and the derived 587-symbol missing set are INCIDENT-SPECIFIC
 constants, not a reusable threshold — promoting them to config would misrepresent a single dated
@@ -63,13 +81,13 @@ from __future__ import annotations
 
 from dataclasses import dataclass
 from datetime import date as date_cls
-from typing import Optional, Sequence
+from typing import Literal, Optional, Sequence
 
 from sqlalchemy.engine import Engine
 from sqlmodel import Session, select
 
 from app.config import Config
-from app.data_providers.base import PriceProvider
+from app.data_providers.base import PriceProvider, ProviderUnavailableError
 from app.engine import data_manager
 from app.models import DailyPrice
 
@@ -80,7 +98,10 @@ from app.models import DailyPrice
 RECOVERY_DATES: frozenset[date_cls] = frozenset({date_cls(2026, 8, 11), date_cls(2026, 8, 12)})
 RECOVERY_START: date_cls = min(RECOVERY_DATES)
 RECOVERY_END: date_cls = max(RECOVERY_DATES)
-RECOVERY_SOURCE: str = "stooq"  # goal.md's own text: "the same vendor the affected rows came from"
+RECOVERY_SOURCE: str = "yahoo"  # goal.md's 2026-08-20 vendor addendum (Stooq is blocked by its own
+# proof-of-work challenge — see the module docstring's "ITERATION 7 RETRY" paragraph). The sole vendor
+# authorized for this retry, gated behind check_adjustment_convention below. Stooq stays permanently
+# excluded; a third vendor needs a new dated amendment.
 
 # The 587-symbol derived missing set (J-10 step 1) — see the module docstring for the evidence
 # trail. Sorted for a deterministic, diffable literal.
@@ -190,6 +211,37 @@ RECOVERY_SYMBOLS: frozenset[str] = frozenset({
 # cite the exact exclusion by name instead of it being an unexplained absence.
 EXCLUDED_UNPROVEN_SYMBOLS: frozenset[str] = frozenset({"MNST"})
 
+# --------------------------------------------------------------------------------------------------
+# J-10 step 2a (iter-7 addendum): the fail-closed adjustment-convention check's own frozen literals.
+# These are single-use incident-check constants for the SAME reason RECOVERY_DATES/RECOVERY_SYMBOLS
+# above are (see the module docstring, "WHY THESE ARE LITERALS") — promoting them to config.yaml would
+# misrepresent a one-time gate as a standing tunable.
+# --------------------------------------------------------------------------------------------------
+CONVENTION_CHECK_WINDOW_END: date_cls = date_cls(2026, 8, 10)  # RECOVERY_START minus one day — the last
+# surviving trading day before the drill's gap (J-10 step 2a: "a small overlap window of already-
+# surviving trading days (<= 2026-08-10)").
+CONVENTION_CHECK_WINDOW_SIZE: int = 5  # "a small overlap window" (goal.md) — the N most recent surviving
+# trading days on or before CONVENTION_CHECK_WINDOW_END, read LIVE from daily_prices (never hardcoded
+# dates: the exact trading-day boundary is DB state, not a policy choice — see
+# _convention_check_window_dates).
+CONVENTION_CHECK_TOLERANCE: float = 0.0075  # 0.75% relative delta on close price — goal.md's OWN
+# proposed default (spec NOTES): tight enough to catch a genuine convention mismatch (a full split is
+# tens of percent) while tolerating ordinary cross-vendor rounding noise. Adopted UNCHANGED as the
+# final tolerance (see the dev handoff for the empirical per-pair deltas observed on the real run) —
+# never loosened after seeing a result, the same discipline J-09 already established.
+
+# The convention-check sample (J-10 step 2a): >= 15 RECOVERY_SYMBOLS tickers, hardcoded for the same
+# "single-use incident constant" reason as RECOVERY_SYMBOLS itself — a deterministic, documented,
+# diffable sample, never re-derived per run. 20 large-cap, highly-liquid RECOVERY_SYMBOLS members
+# spanning a mix of established dividend payers and growth-oriented names, so the sample can plausibly
+# exercise the raw-close-vs-adjusted-close gap the module docstring's load-bearing technical finding
+# warns about, not just names where the two series would trivially coincide. Sorted alphabetically for
+# determinism; a TUPLE (not a set) so iteration order — and therefore the fetch-call order — is fixed.
+CONVENTION_CHECK_SAMPLE_SYMBOLS: tuple[str, ...] = (
+    "AAPL", "AMZN", "BAC", "CSCO", "CVX", "DIS", "GOOGL", "HD", "INTC", "JNJ",
+    "JPM", "KO", "META", "MRK", "MSFT", "NVDA", "PEP", "PG", "WMT", "XOM",
+)
+
 
 class RecoveryScopeError(ValueError):
     """Raised when a recovery request falls outside the single-use J-10 authorization. A ValueError
@@ -245,6 +297,164 @@ def still_missing_symbols(session: Session) -> list[str]:
     return sorted(s for s in RECOVERY_SYMBOLS if have.get(s, set()) != RECOVERY_DATES)
 
 
+# ==================================================================================================
+# J-10 step 2a (iter-7 addendum): the fail-closed adjustment-convention check
+# ==================================================================================================
+@dataclass(frozen=True)
+class ConventionCheckPair:
+    """One sampled (symbol, date) comparison — the atomic evidence unit the dev handoff cites verbatim
+    (goal.md: "every sampled pair's observed delta recorded in the dev handoff"). `within_tolerance` is
+    `None` only when no comparable yahoo value was obtained for this pair (never a fabricated pass)."""
+
+    symbol: str
+    trading_date: date_cls
+    stored_close: float
+    yahoo_adjusted_close: Optional[float]
+    relative_delta: Optional[float]
+    within_tolerance: Optional[bool]
+
+
+@dataclass(frozen=True)
+class ConventionCheckResult:
+    """J-10 step 2a's one evidenced return value — held entirely in memory, never partially written.
+    `verdict` is exactly one of "agree" / "mismatch" / "inconclusive"; `reason` is the human-readable
+    summary the caller (and the dev handoff) cites verbatim."""
+
+    verdict: Literal["agree", "mismatch", "inconclusive"]
+    tolerance: float
+    sample_symbols: tuple[str, ...]
+    window_dates: tuple[date_cls, ...]
+    pairs: tuple[ConventionCheckPair, ...]
+    reason: str
+
+
+def _convention_check_window_dates(session: Session) -> list[date_cls]:
+    """The live comparison window (J-10 step 2a): the CONVENTION_CHECK_WINDOW_SIZE most recent trading
+    days actually stored in `daily_prices` at or before CONVENTION_CHECK_WINDOW_END — read LIVE (never
+    hardcoded), because the exact surviving trading-day boundary is DB state, not a policy choice.
+    Read-only: makes no network call and writes nothing. Ascending order (oldest first)."""
+    rows = session.exec(
+        select(DailyPrice.date)
+        .where(DailyPrice.date <= CONVENTION_CHECK_WINDOW_END)
+        .distinct()
+        .order_by(DailyPrice.date.desc())
+        .limit(CONVENTION_CHECK_WINDOW_SIZE)
+    ).all()
+    return sorted(rows)
+
+
+def _stored_closes(
+    session: Session, symbols: Sequence[str], dates: Sequence[date_cls]
+) -> dict[tuple[str, date_cls], float]:
+    """The stored `daily_prices.close` for exactly the sampled (symbol, date) pairs — a small,
+    column-projected select (AG-8: never a full-table/whole-row sweep). Read-only."""
+    rows = session.exec(
+        select(DailyPrice.symbol, DailyPrice.date, DailyPrice.close)
+        .where(DailyPrice.symbol.in_(list(symbols)))
+        .where(DailyPrice.date.in_(list(dates)))
+    ).all()
+    return {(sym, d): close for sym, d, close in rows}
+
+
+def check_adjustment_convention(
+    session: Session,
+    *,
+    provider: PriceProvider,
+    sample_symbols: Optional[Sequence[str]] = None,
+    window_dates: Optional[Sequence[date_cls]] = None,
+    tolerance: float = CONVENTION_CHECK_TOLERANCE,
+) -> ConventionCheckResult:
+    """J-10 step 2a's fail-closed gate: BEFORE any write, prove that `provider`'s split/dividend-
+    ADJUSTED close series for a documented sample of already-surviving days agrees with the stored
+    (Stooq-sourced) `daily_prices` closes within `tolerance`. Read-only / in-memory ONLY — this
+    function itself never writes to any table and never persists its fetched comparison values beyond
+    its own call frame (goal.md: "held in memory... never written to the database, never cached").
+
+    `provider` must implement `get_adjusted_close(symbol, start=..., end=...) -> dict[date, float]` —
+    the additive Yahoo capability (`YahooProvider.get_adjusted_close`), NOT `get_daily`'s plain/raw
+    `quote.close` (see the module docstring's load-bearing technical finding: comparing the wrong field
+    would let a real mismatch pass silently, or flag a false one). A test fake implements the same
+    method name.
+
+    One call per sampled symbol (never per (symbol, date) pair), covering the whole window in one
+    request. A provider failure for ANY sampled symbol makes the WHOLE verdict "inconclusive" (never a
+    false "agree") and stops further comparison fetches immediately — a systemic failure gives no
+    reason to expect the next call would succeed, and this is a single-use incident check, not a
+    resilient production import path; every pair compared before the failure is still recorded.
+    Otherwise every sampled (symbol, date) pair with BOTH a stored close and a returned yahoo value is
+    compared; "mismatch" is returned if ANY pair's relative delta exceeds `tolerance` (every pair is
+    still compared — the dev handoff needs every sampled pair's observed delta, not just the first
+    failure); "agree" only if every sampled symbol was fetched and every compared pair is within
+    tolerance. A pair with no comparable yahoo value (a date genuinely absent from the returned series)
+    is recorded with `within_tolerance=None` and also forces "inconclusive" — never silently dropped
+    from the sample and never counted as a pass.
+
+    A passing ("agree") result is evidence that THIS sample agreed within THIS tolerance — it is NOT
+    evidence that Yahoo and Stooq bars are interchangeable generally (goal.md AG-9 step 2a; see also
+    the module docstring)."""
+    symbols = tuple(sample_symbols) if sample_symbols is not None else CONVENTION_CHECK_SAMPLE_SYMBOLS
+    dates = tuple(window_dates) if window_dates is not None else tuple(_convention_check_window_dates(session))
+    if not symbols or not dates:
+        return ConventionCheckResult(
+            verdict="inconclusive", tolerance=tolerance, sample_symbols=symbols, window_dates=dates,
+            pairs=(), reason="empty sample-symbol list or comparison window — nothing to compare",
+        )
+
+    stored = _stored_closes(session, symbols, dates)
+    pairs: list[ConventionCheckPair] = []
+    inconclusive_reason: Optional[str] = None
+    for symbol in symbols:
+        try:
+            yahoo_series = provider.get_adjusted_close(symbol, start=dates[0], end=dates[-1])
+        except ProviderUnavailableError as exc:
+            inconclusive_reason = f"yahoo adjusted-close fetch failed for {symbol!r}: {exc}"
+            break
+        for d in dates:
+            stored_close = stored.get((symbol, d))
+            if stored_close is None:
+                continue  # this (symbol, date) isn't actually stored — nothing to compare, never fabricated
+            yahoo_close = yahoo_series.get(d)
+            if yahoo_close is None:
+                pairs.append(ConventionCheckPair(symbol, d, stored_close, None, None, None))
+                continue
+            delta = (abs(yahoo_close - stored_close) / abs(stored_close)) if stored_close else None
+            pairs.append(ConventionCheckPair(
+                symbol, d, stored_close, yahoo_close, delta,
+                (delta is not None and delta <= tolerance),
+            ))
+
+    if inconclusive_reason is not None:
+        return ConventionCheckResult(
+            verdict="inconclusive", tolerance=tolerance, sample_symbols=symbols, window_dates=dates,
+            pairs=tuple(pairs), reason=inconclusive_reason,
+        )
+    incomparable = [p for p in pairs if p.within_tolerance is None]
+    if incomparable:
+        return ConventionCheckResult(
+            verdict="inconclusive", tolerance=tolerance, sample_symbols=symbols, window_dates=dates,
+            pairs=tuple(pairs),
+            reason=(
+                f"{len(incomparable)}/{len(pairs)} sampled pair(s) had no comparable yahoo value "
+                f"(a window date missing from the fetched series)"
+            ),
+        )
+    failing = [p for p in pairs if not p.within_tolerance]
+    if failing:
+        worst = max(failing, key=lambda p: p.relative_delta or 0.0)
+        return ConventionCheckResult(
+            verdict="mismatch", tolerance=tolerance, sample_symbols=symbols, window_dates=dates,
+            pairs=tuple(pairs),
+            reason=(
+                f"{len(failing)}/{len(pairs)} sampled pair(s) exceeded {tolerance:.4%} relative delta "
+                f"(worst: {worst.symbol} {worst.trading_date} delta={worst.relative_delta:.4%})"
+            ),
+        )
+    return ConventionCheckResult(
+        verdict="agree", tolerance=tolerance, sample_symbols=symbols, window_dates=dates,
+        pairs=tuple(pairs), reason=f"all {len(pairs)} sampled pairs within {tolerance:.4%} relative delta",
+    )
+
+
 @dataclass
 class RecoveryOutcome:
     """One recovery-driver call's honest summary — feeds the dev handoff's provenance section.
@@ -301,3 +511,57 @@ def run_bounded_recovery_backfill(session: Session, engine: Engine, config: Conf
     data_manager.validate_job_request("backfill", RECOVERY_START, RECOVERY_END, config)
     job = data_manager.create_job("backfill", RECOVERY_START, RECOVERY_END, source=None)
     return data_manager.run_data_job(job.job_id, config=config, engine=engine)
+
+
+# ==================================================================================================
+# run_gated_recovery — the ONE J-10 retry entry point (iter-7): the causal ordering gate
+# ==================================================================================================
+@dataclass
+class GatedRecoveryOutcome:
+    """The top-level J-10 retry outcome (steps 2a-3): the convention check's own result, PLUS — only
+    when it returned "agree" — the fetch and backfill outcomes. `stopped_reason` is set (with `fetch`/
+    `backfill` left None) for every non-agree verdict, so a caller can tell "restored" from "honestly
+    stopped" without separately inspecting three return values."""
+
+    convention_check: ConventionCheckResult
+    fetch: Optional[RecoveryOutcome] = None
+    backfill: Optional[dict] = None
+    stopped_reason: Optional[str] = None
+
+
+def run_gated_recovery(
+    session: Session,
+    engine: Engine,
+    config: Config,
+    *,
+    convention_provider: PriceProvider,
+    fetch_provider: Optional[PriceProvider] = None,
+    api_key: Optional[str] = None,
+    convention_sample_symbols: Optional[Sequence[str]] = None,
+    convention_window_dates: Optional[Sequence[date_cls]] = None,
+    convention_tolerance: float = CONVENTION_CHECK_TOLERANCE,
+) -> GatedRecoveryOutcome:
+    """The ONE J-10 retry entry point (steps 2a->3): run the adjustment-convention check FIRST; only a
+    verdict of EXACTLY "agree" reaches `run_bounded_recovery_fetch` / `run_bounded_recovery_backfill` —
+    every other verdict returns immediately with `stopped_reason` set and makes NO call capable of
+    writing to `daily_prices`/`scanner_runs`/`data_provider_runs`. This is the textual and causal gate
+    goal.md step 2a demands: no code path below the verdict branch can reach the write-capable calls on
+    a non-agree verdict. `convention_provider` and `fetch_provider` are separate injection points (they
+    are the SAME `YahooProvider()` instance in production — `get_adjusted_close` for the check,
+    `get_daily` for the fetch — kept separate here only so tests can inject independent fakes for each
+    concern)."""
+    check = check_adjustment_convention(
+        session,
+        provider=convention_provider,
+        sample_symbols=convention_sample_symbols,
+        window_dates=convention_window_dates,
+        tolerance=convention_tolerance,
+    )
+    if check.verdict != "agree":
+        return GatedRecoveryOutcome(
+            convention_check=check,
+            stopped_reason=f"adjustment-convention check returned {check.verdict!r}: {check.reason}",
+        )
+    fetch = run_bounded_recovery_fetch(session, engine, config, provider=fetch_provider, api_key=api_key)
+    backfill = run_bounded_recovery_backfill(session, engine, config)
+    return GatedRecoveryOutcome(convention_check=check, fetch=fetch, backfill=backfill)
diff --git a/apps/backend/tests/test_j10_recovery.py b/apps/backend/tests/test_j10_recovery.py
index 94791734..b91cfd1f 100644
--- a/apps/backend/tests/test_j10_recovery.py
+++ b/apps/backend/tests/test_j10_recovery.py
@@ -1,4 +1,5 @@
-"""app.engine.j10_recovery — the J-10 bounded-recovery scope guard (goal-market-compass iter-6).
+"""app.engine.j10_recovery — the J-10 bounded-recovery scope guard (goal-market-compass iter-6,
+extended iter-7 with the vendor swap + fail-closed adjustment-convention gate).
 
 Fixture-scoped, file-scoped, synthetic-data only (docs/goal.md: "the full suite takes hours and is
 never run by pipeline agents"). Proves:
@@ -10,7 +11,12 @@ never run by pipeline agents"). Proves:
   - MNST is deliberately excluded from `RECOVERY_SYMBOLS` (the documented ambiguous-evidence case);
   - the backfill step is hardcoded to exactly [RECOVERY_START, RECOVERY_END] and cannot create a
     ScannerRun for any other date (TC-8's scope half; the snapshot-content assertions belong to the
-    real end-to-end recovery run, not this synthetic fixture).
+    real end-to-end recovery run, not this synthetic fixture);
+  - iter-7: `RECOVERY_SOURCE` is now "yahoo" ("stooq" is the now-rejected vendor); the adjustment-
+    convention check (`check_adjustment_convention`) returns "agree"/"mismatch"/"inconclusive" with
+    zero writes in every outcome, using an injected fake `get_adjusted_close` provider — never live
+    network; and `run_gated_recovery` never reaches the write-capable fetch/backfill calls on any
+    verdict other than "agree" (TC-4 through TC-6, plus the orchestration-level proof).
 """
 from __future__ import annotations
 
@@ -20,10 +26,11 @@ import pytest
 from sqlmodel import Session, select
 
 from app.config import load_config
-from app.data_providers.base import Bar, PriceProvider
+from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError
 from app.db import create_db_and_tables, make_engine
 from app.engine import j10_recovery
 from app.engine.j10_recovery import (
+    CONVENTION_CHECK_SAMPLE_SYMBOLS,
     EXCLUDED_UNPROVEN_SYMBOLS,
     RECOVERY_DATES,
     RECOVERY_END,
@@ -31,8 +38,10 @@ from app.engine.j10_recovery import (
     RECOVERY_START,
     RECOVERY_SYMBOLS,
     RecoveryScopeError,
+    check_adjustment_convention,
     run_bounded_recovery_backfill,
     run_bounded_recovery_fetch,
+    run_gated_recovery,
     still_missing_symbols,
     validate_recovery_scope,
 )
@@ -130,9 +139,12 @@ def test_rejects_mnst_explicitly_the_documented_ambiguous_exclusion():
 
 
 def test_rejects_wrong_source():
+    """iter-7: RECOVERY_SOURCE is now "yahoo" (goal.md's vendor addendum) — "stooq" (this retry's
+    permanently excluded original vendor, blocked by its own proof-of-work challenge) is the wrong
+    source now."""
     with pytest.raises(RecoveryScopeError, match="source must be"):
         validate_recovery_scope(
-            start=RECOVERY_START, end=RECOVERY_END, symbols=["AAPL"], source="yahoo"
+            start=RECOVERY_START, end=RECOVERY_END, symbols=["AAPL"], source="stooq"
         )
 
 
@@ -191,7 +203,8 @@ def test_fetch_restores_only_the_missing_rows_and_never_touches_survivors(tmp_pa
 
     provider = _RecordingProvider()
     with Session(engine) as session:
-        outcome = run_bounded_recovery_fetch(session, engine, cfg, provider=provider, api_key="test-only")
+        # iter-7: RECOVERY_SOURCE ("yahoo") is needs_key: false in the config catalog — no api_key needed.
+        outcome = run_bounded_recovery_fetch(session, engine, cfg, provider=provider)
 
     assert outcome.already_complete is False
     assert outcome.requested_symbols == ["MSFT"]  # AAPL fully covered — never re-requested
@@ -284,7 +297,7 @@ def test_recovery_constants_shape():
     assert RECOVERY_DATES == {date(2026, 8, 11), date(2026, 8, 12)}
     assert RECOVERY_START == date(2026, 8, 11)
     assert RECOVERY_END == date(2026, 8, 12)
-    assert RECOVERY_SOURCE == "stooq"
+    assert RECOVERY_SOURCE == "yahoo"  # iter-7: goal.md's vendor addendum (Stooq stays excluded)
     assert len(RECOVERY_SYMBOLS) == 587
     assert RECOVERY_SYMBOLS.isdisjoint(EXCLUDED_UNPROVEN_SYMBOLS)
 
@@ -298,3 +311,275 @@ def test_data_provider_run_538_is_the_authoritative_removal_record_shape():
         "removed_first": "2026-08-11", "removed_last": "2026-08-12", "not_removable_bar_count": 0,
     }
     assert recorded["removed_symbol_count"] == len(RECOVERY_SYMBOLS)
+
+
+# ==================================================================================================
+# check_adjustment_convention — J-10 step 2a's fail-closed gate (iter-7, TC-4/TC-5/TC-6)
+# ==================================================================================================
+class _FakeAdjustedCloseProvider(PriceProvider):
+    """The convention-check's own injection point: `get_daily` fails the test if ever called (the check
+    must use `get_adjusted_close` exclusively — the load-bearing technical finding this iteration exists
+    to honor); `get_adjusted_close` returns a canned {date: close} series per symbol, or raises
+    ProviderUnavailableError for any symbol named in `fail_for` (TC-6)."""
+
+    def __init__(self, series: dict[str, dict[date, float]], *, fail_for: frozenset[str] = frozenset()):
+        self._series = series
+        self._fail_for = fail_for
+        self.requested_symbols: list[str] = []
+
+    def get_daily(self, symbol, start=None, end=None):
+        pytest.fail(f"get_daily called for {symbol} — the convention check must use get_adjusted_close")
+
+    def get_adjusted_close(self, symbol, start=None, end=None):
+        self.requested_symbols.append(symbol)
+        if symbol in self._fail_for:
+            raise ProviderUnavailableError(f"synthetic adjusted-close failure for {symbol!r}")
+        return dict(self._series.get(symbol, {}))
+
+
+def test_convention_check_default_sample_is_documented_and_in_scope():
+    """The default sample (>= 15 tickers per goal.md) is a real subset of RECOVERY_SYMBOLS, deterministic
+    (a tuple, not a set), MNST-free, and duplicate-free — a cheap constant-sanity check, no DB/network."""
+    assert len(CONVENTION_CHECK_SAMPLE_SYMBOLS) >= 15
+    assert isinstance(CONVENTION_CHECK_SAMPLE_SYMBOLS, tuple)
+    assert set(CONVENTION_CHECK_SAMPLE_SYMBOLS) <= RECOVERY_SYMBOLS
+    assert "MNST" not in CONVENTION_CHECK_SAMPLE_SYMBOLS
+    assert len(set(CONVENTION_CHECK_SAMPLE_SYMBOLS)) == len(CONVENTION_CHECK_SAMPLE_SYMBOLS)
+
+
+def test_convention_check_agree_when_all_sampled_pairs_within_tolerance(tmp_path):
+    """TC-4: every sampled pair's fake adjusted-close equals the stored daily_prices close exactly (well
+    within tolerance) -> "agree", and zero rows are written to any table."""
+    engine = _engine(tmp_path)
+    symbols = ["AAPL", "MSFT"]
+    window = [date(2026, 8, 6), date(2026, 8, 7), date(2026, 8, 10)]
+    with Session(engine) as session:
+        for sym, base in (("AAPL", 200.0), ("MSFT", 400.0)):
+            for i, d in enumerate(window):
+                session.add(DailyPrice(
+                    symbol=sym, date=d, open=base, high=base, low=base, close=base + i, volume=1.0
+                ))
+        session.commit()
+
+    series = {
+        "AAPL": {window[0]: 200.0, window[1]: 201.0, window[2]: 202.0},
+        "MSFT": {window[0]: 400.0, window[1]: 401.0, window[2]: 402.0},
+    }
+    provider = _FakeAdjustedCloseProvider(series)
+    with Session(engine) as session:
+        result = check_adjustment_convention(
+            session, provider=provider, sample_symbols=symbols, window_dates=window,
+        )
+
+    assert result.verdict == "agree"
+    assert len(result.pairs) == 6
+    assert all(p.within_tolerance for p in result.pairs)
+    assert provider.requested_symbols == ["AAPL", "MSFT"]  # one call per symbol, never per (symbol, date)
+
+    with Session(engine) as session:
+        assert len(session.exec(select(DailyPrice)).all()) == 6  # only the 6 seeded rows — nothing new
+        assert session.exec(select(ScannerRun)).all() == []
+        assert session.exec(select(DataProviderRun)).all() == []
+
+
+def test_convention_check_mismatch_when_a_sampled_pair_exceeds_tolerance(tmp_path):
+    """TC-5: one sampled pair (AAPL's second date) diverges by far more than the tolerance — a synthetic
+    2:1 split-away value — so the verdict is "mismatch"; every OTHER pair is still compared (the dev
+    handoff needs every sampled pair's observed delta, not just the first failure), and zero rows are
+    written anywhere."""
+    engine = _engine(tmp_path)
+    symbols = ["AAPL", "MSFT"]
+    window = [date(2026, 8, 6), date(2026, 8, 7)]
+    with Session(engine) as session:
+        for sym, base in (("AAPL", 200.0), ("MSFT", 400.0)):
+            for d in window:
+                session.add(DailyPrice(symbol=sym, date=d, open=base, high=base, low=base, close=base, volume=1.0))
+        session.commit()
+
+    series = {
+        "AAPL": {window[0]: 200.0, window[1]: 100.0},  # a 2:1 split-away value, far outside tolerance
+        "MSFT": {window[0]: 400.0, window[1]: 400.0},
+    }
+    provider = _FakeAdjustedCloseProvider(series)
+    with Session(engine) as session:
+        result = check_adjustment_convention(
+            session, provider=provider, sample_symbols=symbols, window_dates=window,
+        )
+
+    assert result.verdict == "mismatch"
+    assert len(result.pairs) == 4  # both symbols' both dates were still compared
+    mismatched = [p for p in result.pairs if p.within_tolerance is False]
+    assert len(mismatched) == 1
+    assert mismatched[0].symbol == "AAPL" and mismatched[0].trading_date == window[1]
+    assert provider.requested_symbols == ["AAPL", "MSFT"]  # MSFT still fetched — full evidence gathered
+
+    with Session(engine) as session:
+        assert len(session.exec(select(DailyPrice)).all()) == 4  # only the 4 seeded rows
+        assert session.exec(select(ScannerRun)).all() == []
+        assert session.exec(select(DataProviderRun)).all() == []
+
+
+def test_convention_check_inconclusive_when_provider_fails(tmp_path):
+    """TC-6: a provider failure on one sampled symbol yields "inconclusive" — NEVER a false "agree" —
+    and zero rows are written anywhere. The failure stops further comparison fetches (a systemic
+    failure gives no reason to expect the next call would succeed)."""
+    engine = _engine(tmp_path)
+    symbols = ["AAPL", "MSFT"]
+    window = [date(2026, 8, 6)]
+    with Session(engine) as session:
+        for sym in symbols:
+            session.add(DailyPrice(symbol=sym, date=window[0], open=1, high=1, low=1, close=100.0, volume=1))
+        session.commit()
+
+    provider = _FakeAdjustedCloseProvider(
+        {"AAPL": {window[0]: 100.0}}, fail_for=frozenset({"AAPL"}),
+    )
+    with Session(engine) as session:
+        result = check_adjustment_convention(
+            session, provider=provider, sample_symbols=symbols, window_dates=window,
+        )
+
+    assert result.verdict == "inconclusive"
+    assert "AAPL" in result.reason
+    assert provider.requested_symbols == ["AAPL"]  # stopped at the first failure — MSFT never attempted
+
+    with Session(engine) as session:
+        assert len(session.exec(select(DailyPrice)).all()) == 2  # only the 2 seeded rows
+        assert session.exec(select(ScannerRun)).all() == []
+        assert session.exec(select(DataProviderRun)).all() == []
+
+
+def test_convention_check_never_writes_regardless_of_verdict(tmp_path):
+    """A direct restatement of the DoD's own wording ("provably read-only... in every outcome") across
+    all three verdicts, asserting on the stored DailyPrice VALUE (not just row count) to prove no stored
+    close was mutated either — using the exact same seeded row through agree/mismatch/inconclusive."""
+    engine = _engine(tmp_path)
+    window = [date(2026, 8, 6)]
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="AAPL", date=window[0], open=1, high=1, low=1, close=123.45, volume=1))
+        session.commit()
+
+    providers = (
+        _FakeAdjustedCloseProvider({"AAPL": {window[0]: 123.45}}),            # would agree
+        _FakeAdjustedCloseProvider({"AAPL": {window[0]: 1.0}}),               # would mismatch
+        _FakeAdjustedCloseProvider({}, fail_for=frozenset({"AAPL"})),         # would be inconclusive
+    )
+    for provider in providers:
+        with Session(engine) as session:
+            check_adjustment_convention(
+                session, provider=provider, sample_symbols=["AAPL"], window_dates=window,
+            )
+        with Session(engine) as session:
+            row = session.exec(select(DailyPrice).where(DailyPrice.symbol == "AAPL")).one()
+        assert row.close == 123.45  # byte-unchanged across every verdict
+
+
+# ==================================================================================================
+# run_gated_recovery — the causal ordering gate (iter-7): agree -> fetch+backfill; anything else -> stop
+# ==================================================================================================
+class _NeverCalledFetchProvider(PriceProvider):
+    """Wired in as the fetch-side provider on a non-agree verdict — fails the test if
+    run_bounded_recovery_fetch (or anything downstream of it) ever calls get_daily."""
+
+    def get_daily(self, symbol, start=None, end=None):
+        pytest.fail(f"get_daily called for {symbol} — the fetch step must never run on a non-agree verdict")
+
+
+def test_gated_recovery_stops_on_mismatch_before_any_write_capable_call(tmp_path):
+    engine = _engine(tmp_path)
+    cfg = _cfg()
+    window = [date(2026, 8, 6)]
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="AAPL", date=window[0], open=1, high=1, low=1, close=200.0, volume=1))
+        session.commit()
+
+    convention_provider = _FakeAdjustedCloseProvider({"AAPL": {window[0]: 100.0}})  # forces mismatch
+    with Session(engine) as session:
+        outcome = run_gated_recovery(
+            session, engine, cfg,
+            convention_provider=convention_provider,
+            fetch_provider=_NeverCalledFetchProvider(),
+            convention_sample_symbols=["AAPL"],
+            convention_window_dates=window,
+        )
+
+    assert outcome.convention_check.verdict == "mismatch"
+    assert outcome.fetch is None
+    assert outcome.backfill is None
+    assert outcome.stopped_reason is not None and "mismatch" in outcome.stopped_reason
+
+    with Session(engine) as session:
+        assert session.exec(select(ScannerRun)).all() == []
+        assert session.exec(select(DataProviderRun)).all() == []
+
+
+def test_gated_recovery_stops_on_inconclusive_before_any_write_capable_call(tmp_path):
+    engine = _engine(tmp_path)
+    cfg = _cfg()
+    window = [date(2026, 8, 6)]
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="AAPL", date=window[0], open=1, high=1, low=1, close=200.0, volume=1))
+        session.commit()
+
+    convention_provider = _FakeAdjustedCloseProvider({}, fail_for=frozenset({"AAPL"}))
+    with Session(engine) as session:
+        outcome = run_gated_recovery(
+            session, engine, cfg,
+            convention_provider=convention_provider,
+            fetch_provider=_NeverCalledFetchProvider(),
+            convention_sample_symbols=["AAPL"],
+            convention_window_dates=window,
+        )
+
+    assert outcome.convention_check.verdict == "inconclusive"
+    assert outcome.fetch is None
+    assert outcome.backfill is None
+    assert outcome.stopped_reason is not None
+
+    with Session(engine) as session:
+        assert session.exec(select(ScannerRun)).all() == []
+        assert session.exec(select(DataProviderRun)).all() == []
+
+
+def test_gated_recovery_reaches_fetch_and_backfill_on_agree(tmp_path, monkeypatch):
+    """The positive path: an "agree" verdict reaches BOTH run_bounded_recovery_fetch (restoring the one
+    genuinely missing row, mirroring test_fetch_restores_only_the_missing_rows_and_never_touches_survivors)
+    AND run_bounded_recovery_backfill (creating ScannerRun rows for both recovery dates)."""
+    monkeypatch.setattr(j10_recovery, "RECOVERY_SYMBOLS", frozenset({"AAPL", "MSFT"}))
+    engine = _engine(tmp_path)
+    cfg = _cfg()
+    window = [date(2026, 8, 6)]
+    with Session(engine) as session:
+        for sym, price in (("SPY", 500.0), ("AAPL", 200.0)):
+            for d in (window[0], RECOVERY_START, RECOVERY_END):
+                session.add(DailyPrice(symbol=sym, date=d, open=price, high=price, low=price, close=price, volume=1.0))
+        session.add(DailyPrice(symbol="MSFT", date=window[0], open=90, high=90, low=90, close=90.0, volume=1.0))
+        session.add(DailyPrice(symbol="MSFT", date=RECOVERY_START, open=90, high=90, low=90, close=90.0, volume=1.0))
+        # MSFT has no RECOVERY_END row yet — the one genuinely missing row this test restores
+        session.commit()
+
+    convention_provider = _FakeAdjustedCloseProvider({"AAPL": {window[0]: 200.0}, "MSFT": {window[0]: 90.0}})
+    fetch_provider = _RecordingProvider()
+
+    with Session(engine) as session:
+        outcome = run_gated_recovery(
+            session, engine, cfg,
+            convention_provider=convention_provider,
+            fetch_provider=fetch_provider,
+            convention_sample_symbols=["AAPL", "MSFT"],
+            convention_window_dates=window,
+        )
+
+    assert outcome.convention_check.verdict == "agree"
+    assert outcome.stopped_reason is None
+    assert outcome.fetch is not None
+    assert outcome.fetch.requested_symbols == ["MSFT"]  # AAPL already fully covered
+    assert outcome.backfill is not None
+
+    with Session(engine) as session:
+        snapshot_dates = set(session.exec(select(ScannerRun.asof_date)).all())
+        msft_end = session.exec(
+            select(DailyPrice).where(DailyPrice.symbol == "MSFT", DailyPrice.date == RECOVERY_END)
+        ).one()
+    assert RECOVERY_START in snapshot_dates and RECOVERY_END in snapshot_dates
+    assert msft_end.close == 10.5  # the _RecordingProvider's canned bar value
```

## Excluded-path stat (dependency/lockfile visibility)

 .../state/assumptions.md                           | 31 ++++++++++++++++++++++
 runs/goal-session-market-compass/telemetry.jsonl   | 11 ++++++++
 runs/goal-session-market-compass/trace/.next-step  |  2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |  2 ++
 4 files changed, 45 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
