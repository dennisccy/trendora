# Iteration diff (bounded)

Files changed: 12. Shown in full: 9.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/j10_recovery.py` (451 lines not shown)
- `apps/backend/tests/test_j10_recovery.py` (415 lines not shown)
- `docs/goal.md` (289 lines not shown)

```diff
diff --git a/apps/backend/app/data_providers/yahoo_provider.py b/apps/backend/app/data_providers/yahoo_provider.py
index b42b868d..4311498e 100644
--- a/apps/backend/app/data_providers/yahoo_provider.py
+++ b/apps/backend/app/data_providers/yahoo_provider.py
@@ -12,8 +12,12 @@ Resolved ONLY by the on-demand Data Manager fetch path via the provider factory
 
 `get_adjusted_close` (iter-7, J-10 step 2a) is an additive, read-only capability alongside `get_daily`:
 it returns Yahoo's split/dividend-ADJUSTED close series (`indicators.adjclose`), not `get_daily`'s
-plain `quote.close` — used ONLY by `app.engine.j10_recovery.check_adjustment_convention`'s fail-closed
-gate, never by the ordinary fetch/import path. See that method's own docstring.
+plain `quote.close`. iter-8: the redesigned J-10 gate (`app.engine.j10_recovery.check_adjustment_
+convention_per_symbol`) calibrates on `get_daily`'s raw close instead (so calibration and restoration
+read the identical series — resolves audit finding B2, "one series end to end"; see that module's
+docstring). This method stays in place, additive and still synthetic-payload tested
+(`test_provider_clients.py`), unused by the live gate for now — never by the ordinary fetch/import
+path either way.
 """
 from __future__ import annotations
 
diff --git a/apps/backend/app/engine/j10_recovery.py b/apps/backend/app/engine/j10_recovery.py
index 54a599c1..23e6cfdb 100644
--- a/apps/backend/app/engine/j10_recovery.py
+++ b/apps/backend/app/engine/j10_recovery.py
@@ -1,5 +1,6 @@
 """app.engine.j10_recovery — J-10's single-use, fail-closed bounded-recovery scope guard
-(goal-market-compass iter-6, 2026-08-20 incident response).
+(goal-market-compass iter-6, extended iter-7 with the vendor swap + fail-closed adjustment-convention
+gate, REDESIGNED iter-8 to the owner's per-symbol path-agreement + stable-bridge contract).
 
 Iteration 5's own live drill (remove+backfill of 2026-08-11/2026-08-12, believing them seed-safe)
 permanently deleted those two dates' `daily_prices` bars: the committed seed's real boundary is
@@ -24,16 +25,73 @@ challenge instead of CSV, a vendor-side block, not a per-symbol or transient fai
 `docs/handoffs/goal-market-compass-iter-6-dev.md`). The owner responded the same day with a vendor
 addendum to AG-9's exception: `RECOVERY_SOURCE` below is now `"yahoo"` — Stooq stays PERMANENTLY
 EXCLUDED from this recovery (do not retry it, do not attempt to defeat its challenge, do not add a
-third vendor without a new dated amendment). The addendum rides with a new fail-closed gate (J-10
-step 2a, `check_adjustment_convention` below): Stooq's stored bars are split/dividend-adjusted, so
-before a single byte may be written under the `yahoo` source, this module must POSITIVELY PROVE that
-Yahoo's OWN split/dividend-adjusted series (`YahooProvider.get_adjusted_close`, NOT `get_daily`'s
-plain `quote.close` — see that method's own docstring) agrees with the stored bars on a documented
-sample of already-surviving days, within a stated tolerance. `run_gated_recovery` is the one entry
-point that enforces this ordering: a `mismatch`/`inconclusive` verdict returns immediately with zero
-calls capable of writing to `daily_prices`/`scanner_runs`/`data_provider_runs`. A passing check is
-evidence THIS sample agreed within THIS tolerance — it is NOT evidence that Yahoo and Stooq bars are
-interchangeable generally (goal.md AG-9 step 2a); no surface in this module claims otherwise.
+third vendor without a new dated amendment). The addendum rode with a fail-closed gate (J-10 step 2a)
+that, AS ORIGINALLY BUILT this iteration, required Yahoo's OWN split/dividend-adjusted series
+(`YahooProvider.get_adjusted_close`) to agree with the stored bars on a documented sample within an
+absolute-level tolerance (`CONVENTION_CHECK_TOLERANCE = 0.0075`, now removed — see "ITERATION 8
+REDESIGN" below). The real run against the live database returned a genuine `mismatch` (CVX ~0.865%,
+just over the 0.75% bar) and correctly wrote nothing.
+
+ITERATION 8 REDESIGN (owner, 2026-08-20, after iteration 7's real run): the owner withdrew the
+absolute-level tolerance test AFTER seeing it produce a technically-correct-but-uninformative
+"mismatch" on two oil-dividend names (CVX ~0.865%, XOM ~0.643% — both deltas uniform WITHIN the
+symbol across all 5 window days, the signature of a stale retroactive dividend adjustment, not a
+convention disagreement: an "adjusted close" for a fixed past date is not a stable number — vendors
+recompute it retroactively on every later corporate action, so a freshly-fetched series sits
+uniformly below a stale stored one even under IDENTICAL conventions). `docs/goal.md` J-10 step 2a now
+specifies a two-part test that is invariant to exactly that kind of uniform offset, evaluated PER
+SYMBOL (not one aggregate verdict for the whole 587):
+  1. PATH AGREEMENT — do the two series move the same way over the overlap window? Each series is
+     rebased to 1.0 at the EARLIEST date that symbol has a comparable pair for (goal.md: "rebased to
+     1.0 at the window's earliest date" — read per-symbol so a missing anchor date for one symbol
+     never blocks judging that symbol on its own available evidence); the symbol's path-agreement
+     metric is the WORST (max) relative deviation between the two rebased series over the remaining
+     comparable dates.
+  2. STABLE MULTIPLICATIVE BRIDGE — the per-day stored/fallback ratio across the same comparable
+     dates; the symbol's bridge-dispersion metric is the relative range `(max-min)/mean` of those
+     ratios.
+A symbol passes ("agree") only if BOTH metrics are within their precommitted bounds AND the symbol has
+at least `MIN_COMPARABLE_PAIRS_PER_SYMBOL` comparable pairs (the per-symbol form of iter-7 audit B1's
+minimum-evidence floor — see below). Its bridge factor — the MEAN of its per-day ratios — is then
+APPLIED: multiplied onto all four OHLC fields of its two fetched recovery-date bars (never volume)
+before insert; never a raw fallback value written unchanged (goal.md: "Passing the gate does NOT
+authorize inserting raw Yahoo adjusted-close values unchanged").
+
+This redesign also resolves three findings the iter-7 audit flagged "close in the same turn"
+(`docs/handoffs/goal-market-compass-iter-7-audit.md`):
+  - B2 ("one series, end to end"): the iter-7 gate validated `get_adjusted_close` (Yahoo's adjusted
+    close) while the SAME UNCHANGED restore path wrote `get_daily`'s raw close — a ~0.086% gap on
+    AAPL the iter-7 developer measured directly. Rather than build a second parsing capability to
+    derive an "adjusted OHLC" series, this redesign adopts the spec NOTES' offered simplification:
+    calibrate the bridge on `get_daily`'s RAW close — the EXACT SAME method, called the same way, that
+    `run_bounded_recovery_fetch` already uses to restore bars — so `check_adjustment_convention_
+    per_symbol` and the restoration fetch read the identical provider method/field, symbol by symbol.
+    One series, one code path; no crossover is possible because there is only one series in play at
+    all. (Logged to `assumptions.md` per the spec NOTES' explicit ask.) `YahooProvider.get_adjusted_
+    close`/`_parse_adjusted_close` stay in place — additive, unused by this module now, but tested
+    (resolves T2) — in case a future iteration judges the adjusted-close comparison worth reviving.
+  - B3 (persisted per-pair evidence): `run_gated_recovery` now persists `convention_evidence_to_dict`'s
+    FULL per-pair record (every sampled symbol, every window date, stored close, fallback close,
+    ratio) to `evidence_path` — a run artifact under `runs/goal-market-compass-iter-8/` on the real
+    driver path — BEFORE a single verdict is used for anything else. That artifact, not prose, is the
+    sole admissible calibration input (goal.md, verbatim: "Numbers that survive only as prose in a
+    handoff are not calibration evidence").
+  - B5 (non-overridable thresholds): `run_gated_recovery`'s signature no longer accepts a tolerance,
+    dispersion-bound, sample, or window override AT ALL — contrast the iter-7 signature, which exposed
+    all four as caller-settable parameters. `check_adjustment_convention_per_symbol` (one level below
+    the production entry point) still accepts `sample_symbols`/`window_dates` for direct unit testing
+    of the ladder logic in isolation — but `run_gated_recovery` itself calls it with neither override,
+    on every real run, and accepts no threshold parameter of any kind.
+  - B6 (cheap defence-in-depth, audit-recommended, not itself a finding): `_BridgeApplyingProvider` —
+    the ONE place this iteration introduces a transforming write path — asserts every returned bar's
+    date falls inside `[RECOVERY_START, RECOVERY_END]` before transforming/returning it.
+
+Iter-7 audit B1's minimum-evidence floor is carried forward in PER-SYMBOL form
+(`MIN_COMPARABLE_PAIRS_PER_SYMBOL`, evaluated in `_compute_symbol_verdict` AFTER the mismatch branch,
+exactly as before, so a genuine per-symbol disagreement can never be downgraded to `"inconclusive"` by
+a coverage gap): a symbol with fewer comparable pairs than the floor — including zero — is
+`"inconclusive"`, never `"agree"`, no matter how clean the few available pairs look (goal.md: "Zero
+usable pairs can NEVER produce agreement... is not evidence, it is the absence of evidence").
 
 WHY THESE ARE LITERALS, NOT `config.yaml` TUNABLES (goal.md NOTES, "Config-vs-literal judgment
 call"): the two recovery dates and the derived 587-symbol missing set are INCIDENT-SPECIFIC
@@ -79,15 +137,17 @@ owner-review flag.
 """
 from __future__ import annotations
 
+import json
 from dataclasses import dataclass
 from datetime import date as date_cls
+from pathlib import Path
 from typing import Literal, Optional, Sequence
 
 from sqlalchemy.engine import Engine
 from sqlmodel import Session, select
 
 from app.config import Config
-from app.data_providers.base import PriceProvider, ProviderUnavailableError
+from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError
 from app.engine import data_manager
 from app.models import DailyPrice
 
@@ -100,8 +160,8 @@ RECOVERY_START: date_cls = min(RECOVERY_DATES)
 RECOVERY_END: date_cls = max(RECOVERY_DATES)
 RECOVERY_SOURCE: str = "yahoo"  # goal.md's 2026-08-20 vendor addendum (Stooq is blocked by its own
 # proof-of-work challenge — see the module docstring's "ITERATION 7 RETRY" paragraph). The sole vendor
-# authorized for this retry, gated behind check_adjustment_convention below. Stooq stays permanently
-# excluded; a third vendor needs a new dated amendment.
+# authorized for this retry, gated behind check_adjustment_convention_per_symbol below. Stooq stays
+# permanently excluded; a third vendor needs a new dated amendment.
 
 # The 587-symbol derived missing set (J-10 step 1) — see the module docstring for the evidence
 # trail. Sorted for a deterministic, diffable literal.
@@ -211,42 +271,15 @@ RECOVERY_SYMBOLS: frozenset[str] = frozenset({
 # cite the exact exclusion by name instead of it being an unexplained absence.
 EXCLUDED_UNPROVEN_SYMBOLS: frozenset[str] = frozenset({"MNST"})
 
-# --------------------------------------------------------------------------------------------------
-# J-10 step 2a (iter-7 addendum): the fail-closed adjustment-convention check's own frozen literals.
-# These are single-use incident-check constants for the SAME reason RECOVERY_DATES/RECOVERY_SYMBOLS
-# above are (see the module docstring, "WHY THESE ARE LITERALS") — promoting them to config.yaml would
-# misrepresent a one-time gate as a standing tunable.
-# --------------------------------------------------------------------------------------------------
-CONVENTION_CHECK_WINDOW_END: date_cls = date_cls(2026, 8, 10)  # RECOVERY_START minus one day — the last
-# surviving trading day before the drill's gap (J-10 step 2a: "a small overlap window of already-
-# surviving trading days (<= 2026-08-10)").
-CONVENTION_CHECK_WINDOW_SIZE: int = 5  # "a small overlap window" (goal.md) — the N most recent surviving
-# trading days on or before CONVENTION_CHECK_WINDOW_END, read LIVE from daily_prices (never hardcoded
-# dates: the exact trading-day boundary is DB state, not a policy choice — see
-# _convention_check_window_dates).
-CONVENTION_CHECK_TOLERANCE: float = 0.0075  # 0.75% relative delta on close price — goal.md's OWN
-# proposed default (spec NOTES): tight enough to catch a genuine convention mismatch (a full split is
-# tens of percent) while tolerating ordinary cross-vendor rounding noise. Adopted UNCHANGED as the
-# final tolerance (see the dev handoff for the empirical per-pair deltas observed on the real run) —
-# never loosened after seeing a result, the same discipline J-09 already established.
-
-# The convention-check sample (J-10 step 2a): >= 15 RECOVERY_SYMBOLS tickers, hardcoded for the same
-# "single-use incident constant" reason as RECOVERY_SYMBOLS itself — a deterministic, documented,
-# diffable sample, never re-derived per run. 20 large-cap, highly-liquid RECOVERY_SYMBOLS members
-# spanning a mix of established dividend payers and growth-oriented names, so the sample can plausibly
-# exercise the raw-close-vs-adjusted-close gap the module docstring's load-bearing technical finding
-# warns about, not just names where the two series would trivially coincide. Sorted alphabetically for
-# determinism; a TUPLE (not a set) so iteration order — and therefore the fetch-call order — is fixed.
-CONVENTION_CHECK_SAMPLE_SYMBOLS: tuple[str, ...] = (
-    "AAPL", "AMZN", "BAC", "CSCO", "CVX", "DIS", "GOOGL", "HD", "INTC", "JNJ",
-    "JPM", "KO", "META", "MRK", "MSFT", "NVDA", "PEP", "PG", "WMT", "XOM",
-)
-
 
 class RecoveryScopeError(ValueError):
     """Raised when a recovery request falls outside the single-use J-10 authorization. A ValueError
     subclass — mirrors `data_manager.validate_job_request`'s existing error-mapping convention (the
-    API layer maps a ValueError to an honest 4xx, never a silent no-op)."""
+    API layer maps a ValueError to an honest 4xx, never a silent no-op). iter-8: also raised by
+    `_BridgeApplyingProvider` for the two internal-invariant conditions described on that class — a
+    symbol with no passing bridge factor, or a bar dated outside the authorized window — both of
+    which are "refuse to touch something outside authorized scope", the same family this error
+    already names."""
 
 
 def validate_recovery_scope(
@@ -298,34 +331,124 @@ def still_missing_symbols(session: Session) -> list[str]:
 
 
 # ==================================================================================================
-# J-10 step 2a (iter-7 addendum): the fail-closed adjustment-convention check
-# ==================================================================================================
+# J-10 step 2a (iter-8 redesign): the fail-closed adjustment-convention check's own frozen literals.
+# These are single-use incident-check constants for the SAME reason RECOVERY_DATES/RECOVERY_SYMBOLS
+# above are (see the module docstring, "WHY THESE ARE LITERALS") — promoting them to config.yaml would
+# misrepresent a one-time gate as a standing tunable. Fixed here BEFORE this iteration's live
+# comparison run and never adjusted afterward (goal.md: loosening a threshold to convert a failure
+# into a pass is forbidden, and doing so is itself a reportable violation).
+# --------------------------------------------------------------------------------------------------
+CONVENTION_CHECK_WINDOW_END: date_cls = date_cls(2026, 8, 10)  # RECOVERY_START minus one day — the last
+# surviving trading day before the drill's gap (J-10 step 2a: "a small overlap window of already-
+# surviving trading days (<= 2026-08-10)").
+CONVENTION_CHECK_WINDOW_SIZE: int = 5  # "a small overlap window" (goal.md) — the N most recent surviving
+# trading days on or before CONVENTION_CHECK_WINDOW_END, read LIVE from daily_prices (never hardcoded
+# dates: the exact trading-day boundary is DB state, not a policy choice — see
+# _convention_check_window_dates).
+
+PATH_AGREEMENT_TOLERANCE: float = 0.005  # max relative deviation, at ANY single comparable date, of
+# the fallback series rebased to 1.0 at its earliest comparable date vs. the stored series rebased the
+# same way — "do the two series move together", invariant to a uniform multiplicative offset by
+# construction (goal.md step 2a, part 1). Deliberately a bit TIGHTER than goal.md's own 0.75% figure
+# for the now-superseded absolute-level test: rebasing specifically cancels the dominant source of
+# "ordinary cross-vendor noise" that 0.75% was calibrated for (a roughly-constant per-symbol offset —
+# exactly what a stale-adjustment/ex-dividend gap looks like, and exactly what rebasing removes), so
+# the residual this test actually measures should be materially smaller. iter-7's real-run evidence
+# supports generous headroom even at this tighter bound: CVX/XOM's per-day delta printed identical to
+# 5 decimal places across all 5 independent trading days (< 0.00001 percentage points of spread) — a
+# rebased-path residual several orders of magnitude below 0.5%. Precommitted before this iteration's
+# live run; never adjusted after seeing a result (see `assumptions.md`'s iter-8 developer entry for
+# the full reasoning, including why this and BRIDGE_DISPERSION_BOUND are deliberately NOT the same
+# magnitude).
+BRIDGE_DISPERSION_BOUND: float = 0.015  # max relative range `(max(ratio) - min(ratio)) / mean(ratio)`
+# of the per-day stored/fallback ratio across a symbol's comparable window dates (goal.md step 2a,
+# part 2 — "stable... its dispersion across the window within a precommitted bound"). DELIBERATELY
+# LOOSER than PATH_AGREEMENT_TOLERANCE — not an arbitrary choice: for a small (5-day) window these two
+# metrics are mathematically close cousins (a per-day ratio that is stable necessarily makes the
+# rebased paths agree, and a single-date perturbation moves both statistics by a similar order of
+# magnitude — verified numerically while building this module's tests), so using two thresholds close
+# in value would make one nearly always redundant with the other, defeating goal.md's explicit intent
+# that these be two INDEPENDENTLY meaningful tests (TC-4: a symbol can fail path agreement while its
+# bridge dispersion stays low). Bridge dispersion is also the anchor-INDEPENDENT statistic (it does not
+# single out whichever date happens to be earliest, unlike path agreement) — modest extra headroom
+# avoids penalizing that robustness. 1.5% stays far below the "tens of percent" scale of an actual
+# split/convention mismatch, though a marginal within-window corporate-action shift close to CVX/XOM's
+# own ~0.6-0.9% scale might not by itself trip this bound — path agreement, being the tighter
+# threshold, is the first line of defense for that case; this tradeoff is stated honestly, not hidden.
+MIN_COMPARABLE_PAIRS_PER_SYMBOL: int = 3  # of the CONVENTION_CHECK_WINDOW_SIZE=5 window dates, a
+# symbol needs comparable evidence (both sides present and strictly positive) on a CLEAR MAJORITY
+# (3 of 5) before "agree" may ever be reported — the per-symbol form of iter-7 audit B1's "zero pairs
+# can never mean agree", extended with an explicit floor above zero: 1-2 pairs cannot show a genuine
+# repeated "shape" (rebasing to a single other point proves nothing about a pattern, and a 2-point
+# dispersion stat is easily coincidence). No iter-7 precedent anchors this exact number (the old
+# aggregate gate had no per-symbol floor) — a documented judgment call, precommitted before the live
+# run (see assumptions.md).
+
+# The convention-check sample (J-10 step 2a): >= 15 RECOVERY_SYMBOLS tickers, hardcoded for the same
+# "single-use incident constant" reason as RECOVERY_SYMBOLS itself — a deterministic, documented,
+# diffable sample, never re-derived per run. 20 large-cap, highly-liquid RECOVERY_SYMBOLS members
+# spanning a mix of established dividend payers and growth-oriented names, so the sample can plausibly
+# exercise the raw-close-vs-adjusted-close gap the module docstring's load-bearing technical finding
+# warns about, not just names where the two series would trivially coincide. UNCHANGED from iter-7
+# (kept, not re-derived — deliberately: this iteration's job is to prove the REDESIGNED gate mechanism
+# on real evidence, not to chase coverage by widening the sample; goal.md's own host-safety note asks
+# for a "modest" sample, and OUT OF SCOPE forbids widening it to chase coverage after seeing results —
+# choosing a fresh, larger, still-precommitted sample up front was considered and declined for this
+# iteration, see assumptions.md). Sorted alphabetically for determinism; a TUPLE (not a set) so
+# iteration order — and therefore the fetch-call order — is fixed.
+CONVENTION_CHECK_SAMPLE_SYMBOLS: tuple[str, ...] = (
+    "AAPL", "AMZN", "BAC", "CSCO", "CVX", "DIS", "GOOGL", "HD", "INTC", "JNJ",
+    "JPM", "KO", "META", "MRK", "MSFT", "NVDA", "PEP", "PG", "WMT", "XOM",
+)
+
+
 @dataclass(frozen=True)
 class ConventionCheckPair:
-    """One sampled (symbol, date) comparison — the atomic evidence unit the dev handoff cites verbatim
-    (goal.md: "every sampled pair's observed delta recorded in the dev handoff"). `within_tolerance` is
-    `None` only when no comparable yahoo value was obtained for this pair (never a fabricated pass)."""
+    """One (symbol, window-date) comparison point — the atomic evidence unit persisted verbatim to the
+    run artifact (B3) so a bridge factor is traceable to specific rows, never merely asserted in prose.
+    `fallback_close`/`ratio` are `None` only when this window date had a stored baseline but no usable
+    fallback value (a provider gap, or a non-positive close on either side) — recorded, never silently
+    dropped. A window date with NO stored baseline at all is never even turned into a pair (nothing to
+    anchor a comparison to — see `_compute_symbol_verdict`)."""
 
     symbol: str
     trading_date: date_cls
     stored_close: float
-    yahoo_adjusted_close: Optional[float]
-    relative_delta: Optional[float]
-    within_tolerance: Optional[bool]
+    fallback_close: Optional[float]
+    ratio: Optional[float]  # stored_close / fallback_close — the per-day bridge estimate
 
 
 @dataclass(frozen=True)
-class ConventionCheckResult:
-    """J-10 step 2a's one evidenced return value — held entirely in memory, never partially written.
-    `verdict` is exactly one of "agree" / "mismatch" / "inconclusive"; `reason` is the human-readable
-    summary the caller (and the dev handoff) cites verbatim."""
+class SymbolConventionVerdict:
+    """One sampled symbol's two-part gate outcome (J-10 step 2a, iter-8 redesign). `verdict` is
+    exactly one of "agree" / "mismatch" / "inconclusive"; `bridge_factor` is set ONLY on "agree" — the
+    mean per-day stored/fallback ratio, the single number `_BridgeApplyingProvider` multiplies onto
+    every OHLC field of this symbol's two recovery-date bars before insert (never a raw fallback
+    value, never volume)."""
 
+    symbol: str
     verdict: Literal["agree", "mismatch", "inconclusive"]
-    tolerance: float
+    reason: str
+    pairs: tuple[ConventionCheckPair, ...]
+    comparable_pair_count: int
+    path_agreement_max_delta: Optional[float]
+    bridge_dispersion: Optional[float]
+    bridge_factor: Optional[float]
+
+
+@dataclass(frozen=True)
+class ConventionCheckBatchResult:
+    """The whole live comparison run's result — one `SymbolConventionVerdict` per sampled symbol
+    (deterministic sample order), plus the precommitted thresholds actually applied (recorded here,
+    not only in module source, so the persisted evidence artifact is self-describing without
+    cross-referencing code)."""
+
+    path_agreement_tolerance: float
+    bridge_dispersion_bound: float
+    min_comparable_pairs: int
     sample_symbols: tuple[str, ...]
     window_dates: tuple[date_cls, ...]
-    pairs: tuple[ConventionCheckPair, ...]
-    reason: str
+    verdicts: tuple[SymbolConventionVerdict, ...]
 
 
 def _convention_check_window_dates(session: Session) -> list[date_cls]:
@@ -356,136 +479,224 @@ def _stored_closes(
     return {(sym, d): close for sym, d, close in rows}
 
 
-def check_adjustment_convention(
+def _compute_symbol_verdict(
+    symbol: str,
+    window_dates: Sequence[date_cls],
+    stored: dict[date_cls, float],
+    fallback: dict[date_cls, float],
+) -> SymbolConventionVerdict:
+    """The per-symbol two-part verdict ladder (J-10 step 2a, iter-8 redesign) — a PURE function (no
+    I/O), so every degenerate-input scenario (zero pairs, below-floor coverage, one-test-only failure)
+    is directly unit-testable with hand-built dicts, no DB/provider fixture required.
+
+    `stored`/`fallback` are keyed by date, already scoped to `symbol` and to `window_dates` by the
+    caller (`check_adjustment_convention_per_symbol`). A pair is COMPARABLE only when BOTH sides are
+    present and strictly positive (a non-positive price is never a real quote — defensive, never
+    fabricated). Ladder, in order:
+      1. Fewer than 2 comparable pairs -> "inconclusive" (cannot compute ANY metric: path agreement
+         needs an anchor plus at least one more point; a "dispersion" over a single ratio is a vacuous
+         zero-spread that proves nothing — the exact B1 trap, in per-symbol form).
+      2. Compute path-agreement (the max, over every non-anchor comparable date, of the relative
+         difference between the two series each rebased to 1.0 at the EARLIEST comparable date) and
+         bridge-dispersion (the relative range `(max-min)/mean` of the per-day stored/fallback ratio
+         across every comparable date). EITHER exceeding its precommitted bound -> "mismatch" —
+         checked BEFORE the evidence floor below, so a genuine disagreement is never downgraded to
+         "inconclusive" by a coverage gap elsewhere (iter-7 audit B1, carried into per-symbol form —
+         TC-6).
+      3. Fewer comparable pairs than MIN_COMPARABLE_PAIRS_PER_SYMBOL (but >= 2, or the ladder would
+         already have stopped at step 1) -> "inconclusive" — the available evidence didn't contradict
+         agreement, but "not contradicted" is not "proven" (goal.md: "zero usable pairs can NEVER
+         produce agreement"; the same reasoning extended to "too few").
+      4. Otherwise -> "agree"; the recorded bridge factor is the MEAN of the per-day stored/fallback
+         ratios (the "stable" ratio the dispersion check just proved is nearly constant across the
+         window, so mean/median/anchor-ratio would all but coincide numerically — mean chosen as the
+         simplest, tie-free central-tendency statistic)."""
+    pairs: list[ConventionCheckPair] = []
+    for d in window_dates:
+        stored_close = stored.get(d)
+        if stored_close is None:
+            continue  # nothing stored to compare against — never fabricated, never recorded as a pair
+        fallback_close = fallback.get(d)
+        ratio = (
+            stored_close / fallback_close
+            if fallback_close is not None and fallback_close > 0 and stored_close > 0
+            else None
+        )
+        pairs.append(ConventionCheckPair(
+            symbol=symbol, trading_date=d, stored_close=stored_close,
+            fallback_close=fallback_close, ratio=ratio,
+        ))
+
+    comparable = [p for p in pairs if p.ratio is not None]
+    if len(comparable) < 2:
+        return SymbolConventionVerdict(
+            symbol=symbol, verdict="inconclusive",
+            reason=(
+                f"only {len(comparable)} comparable pair(s) (both sides present and positive) — need "
+                f"at least 2 to evaluate path agreement or bridge stability at all"
+            ),
+            pairs=tuple(pairs), comparable_pair_count=len(comparable),
+            path_agreement_max_delta=None, bridge_dispersion=None, bridge_factor=None,
+        )
+
+    ratios = [p.ratio for p in comparable]
+    mean_ratio = sum(ratios) / len(ratios)
+    bridge_dispersion = (max(ratios) - min(ratios)) / mean_ratio
+
+    anchor = comparable[0]  # earliest comparable date — `comparable` preserves window_dates' ascending order
+    path_deltas = []
+    for p in comparable[1:]:
+        rebased_stored = p.stored_close / anchor.stored_close
+        rebased_fallback = p.fallback_close / anchor.fallback_close
+        path_deltas.append(abs(rebased_fallback - rebased_stored) / rebased_stored)
+    path_agreement_max_delta = max(path_deltas)  # len(comparable) >= 2 guarantees >= 1 delta
+
+    path_fails = path_agreement_max_delta > PATH_AGREEMENT_TOLERANCE
+    bridge_fails = bridge_dispersion > BRIDGE_DISPERSION_BOUND
+    if path_fails or bridge_fails:
+        failed: list[str] = []
+        if path_fails:
+            failed.append("path agreement")
+        if bridge_fails:
+            failed.append("bridge stability")
+        return SymbolConventionVerdict(
... [diff_bound] apps/backend/app/engine/j10_recovery.py: 451 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_j10_recovery.py b/apps/backend/tests/test_j10_recovery.py
index 5340f52a..53634e91 100644
--- a/apps/backend/tests/test_j10_recovery.py
+++ b/apps/backend/tests/test_j10_recovery.py
@@ -1,5 +1,6 @@
 """app.engine.j10_recovery — the J-10 bounded-recovery scope guard (goal-market-compass iter-6,
-extended iter-7 with the vendor swap + fail-closed adjustment-convention gate).
+extended iter-7 with the vendor swap + fail-closed adjustment-convention gate, REDESIGNED iter-8 to
+the owner's per-symbol path-agreement + stable-bridge contract).
 
 Fixture-scoped, file-scoped, synthetic-data only (docs/goal.md: "the full suite takes hours and is
 never run by pipeline agents"). Proves:
@@ -12,14 +13,17 @@ never run by pipeline agents"). Proves:
   - the backfill step is hardcoded to exactly [RECOVERY_START, RECOVERY_END] and cannot create a
     ScannerRun for any other date (TC-8's scope half; the snapshot-content assertions belong to the
     real end-to-end recovery run, not this synthetic fixture);
-  - iter-7: `RECOVERY_SOURCE` is now "yahoo" ("stooq" is the now-rejected vendor); the adjustment-
-    convention check (`check_adjustment_convention`) returns "agree"/"mismatch"/"inconclusive" with
-    zero writes in every outcome, using an injected fake `get_adjusted_close` provider — never live
-    network; and `run_gated_recovery` never reaches the write-capable fetch/backfill calls on any
-    verdict other than "agree" (TC-4 through TC-6, plus the orchestration-level proof).
+  - iter-8: the redesigned per-symbol gate (`_compute_symbol_verdict`, a pure ladder function, plus
+    its DB/provider orchestration `check_adjustment_convention_per_symbol`) returns "agree"/"mismatch"/
+    "inconclusive" PER SAMPLED SYMBOL, calibrating exclusively on `get_daily`'s raw close (never
+    `get_adjusted_close` — B2/TC-9); the persisted evidence artifact (`convention_evidence_to_dict`,
+    B3); the bridge-applying transform (`_BridgeApplyingProvider`, TC-8/B6); and `run_gated_recovery`'s
+    redesigned signature, which accepts NO tolerance/dispersion/sample/window override (B5) and fetches
+    ONLY the symbols that passed the gate.
 """
 from __future__ import annotations
 
+import json
 from datetime import date
 
 import pytest
@@ -30,15 +34,20 @@ from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError
 from app.db import create_db_and_tables, make_engine
 from app.engine import j10_recovery
 from app.engine.j10_recovery import (
+    BRIDGE_DISPERSION_BOUND,
     CONVENTION_CHECK_SAMPLE_SYMBOLS,
+    CONVENTION_CHECK_WINDOW_END,
     EXCLUDED_UNPROVEN_SYMBOLS,
+    MIN_COMPARABLE_PAIRS_PER_SYMBOL,
+    PATH_AGREEMENT_TOLERANCE,
     RECOVERY_DATES,
     RECOVERY_END,
     RECOVERY_SOURCE,
     RECOVERY_START,
     RECOVERY_SYMBOLS,
     RecoveryScopeError,
-    check_adjustment_convention,
+    check_adjustment_convention_per_symbol,
+    convention_evidence_to_dict,
     run_bounded_recovery_backfill,
     run_bounded_recovery_fetch,
     run_gated_recovery,
@@ -139,9 +148,8 @@ def test_rejects_mnst_explicitly_the_documented_ambiguous_exclusion():
 
 
 def test_rejects_wrong_source():
-    """iter-7: RECOVERY_SOURCE is now "yahoo" (goal.md's vendor addendum) — "stooq" (this retry's
-    permanently excluded original vendor, blocked by its own proof-of-work challenge) is the wrong
-    source now."""
+    """RECOVERY_SOURCE is "yahoo" (goal.md's vendor addendum) — "stooq" (this retry's permanently
+    excluded original vendor, blocked by its own proof-of-work challenge) is the wrong source now."""
     with pytest.raises(RecoveryScopeError, match="source must be"):
         validate_recovery_scope(
             start=RECOVERY_START, end=RECOVERY_END, symbols=["AAPL"], source="stooq"
@@ -227,6 +235,28 @@ def test_fetch_restores_only_the_missing_rows_and_never_touches_survivors(tmp_pa
     assert msft_end.close == 10.5
 
 
+def test_fetch_symbols_param_intersects_with_still_missing_for_idempotency(tmp_path, monkeypatch):
+    """iter-8: the new `symbols=` restriction on `run_bounded_recovery_fetch` (added so
+    `run_gated_recovery` can fetch only the symbols that passed the per-symbol gate) is intersected
+    with LIVE `still_missing_symbols()`, not used verbatim — a symbol the caller names that is already
+    fully restored is excluded, preserving idempotency."""
+    monkeypatch.setattr(j10_recovery, "RECOVERY_SYMBOLS", frozenset({"AAPL", "MSFT"}))
+    engine = _engine(tmp_path)
+    cfg = _cfg()
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="AAPL", date=RECOVERY_START, open=1, high=1, low=1, close=1.0, volume=1))
+        session.add(DailyPrice(symbol="AAPL", date=RECOVERY_END, open=1, high=1, low=1, close=1.0, volume=1))
+        session.commit()
+
+    provider = _RecordingProvider()
+    with Session(engine) as session:
+        # caller names BOTH symbols, but AAPL is already fully restored
+        outcome = run_bounded_recovery_fetch(session, engine, cfg, provider=provider, symbols=["AAPL", "MSFT"])
+
+    assert outcome.requested_symbols == ["MSFT"]
+    assert provider.requested_symbols == ["MSFT"]
+
+
 def test_second_invocation_after_full_recovery_is_a_true_zero_work_noop(tmp_path):
     """Re-running the recovery after everything is already restored makes ZERO provider calls and
     inserts ZERO rows — the idempotent-retry contract (TC-5)."""
@@ -314,13 +344,123 @@ def test_data_provider_run_538_is_the_authoritative_removal_record_shape():
 
 
 # ==================================================================================================
-# check_adjustment_convention — J-10 step 2a's fail-closed gate (iter-7, TC-4/TC-5/TC-6)
+# _compute_symbol_verdict — the per-symbol two-part ladder (iter-8 redesign), a PURE function: every
+# degenerate-input scenario is directly unit-testable with hand-built {date: value} dicts, no DB/
+# provider fixture required (the iter-7 lesson: "a guard is only proven fail-closed when a test
+# constructs the degenerate input the guard will actually meet in production... all nine [prior]
+# tests seeded a complete fixture").
 # ==================================================================================================
-class _FakeAdjustedCloseProvider(PriceProvider):
-    """The convention-check's own injection point: `get_daily` fails the test if ever called (the check
-    must use `get_adjusted_close` exclusively — the load-bearing technical finding this iteration exists
-    to honor); `get_adjusted_close` returns a canned {date: close} series per symbol, or raises
-    ProviderUnavailableError for any symbol named in `fail_for` (TC-6)."""
+_W = [date(2026, 8, 4), date(2026, 8, 5), date(2026, 8, 6), date(2026, 8, 7), date(2026, 8, 10)]
+
+
+def test_symbol_verdict_agrees_when_path_and_bridge_are_both_stable():
+    """TC-2: a perfectly stable 1.002 ratio across all 5 window dates -> "agree"; the recorded bridge
+    factor equals the computed stable ratio exactly."""
+    stored = {d: 200.0 + i for i, d in enumerate(_W)}
+    fallback = {d: (200.0 + i) / 1.002 for i, d in enumerate(_W)}
+    v = j10_recovery._compute_symbol_verdict("AAPL", _W, stored, fallback)
+    assert v.verdict == "agree"
+    assert v.comparable_pair_count == 5
+    assert v.bridge_factor == pytest.approx(1.002, rel=1e-9)
+    assert v.path_agreement_max_delta == pytest.approx(0.0, abs=1e-9)
+    assert v.bridge_dispersion == pytest.approx(0.0, abs=1e-9)
+
+
+def test_symbol_verdict_mismatch_when_bridge_dispersion_exceeds_bound():
+    """TC-3: a monotonically drifting ratio (1.00 -> ~1.053 across the window) exceeds
+    BRIDGE_DISPERSION_BOUND -- "mismatch", excluded from the fetch, with the measured dispersion cited
+    in the reason."""
+    stored = {d: 100.0 for d in _W}
+    fallback = {_W[0]: 100.0, _W[1]: 99.0, _W[2]: 98.0, _W[3]: 97.0, _W[4]: 95.0}
+    v = j10_recovery._compute_symbol_verdict("DRIFT", _W, stored, fallback)
+    assert v.verdict == "mismatch"
+    assert v.bridge_factor is None
+    assert v.bridge_dispersion > BRIDGE_DISPERSION_BOUND
+    assert "bridge stability" in v.reason
+
+
+def test_symbol_verdict_mismatch_when_path_agreement_fails_despite_stable_bridge():
+    """TC-4: engineered so bridge-ratio dispersion stays comfortably under BRIDGE_DISPERSION_BOUND (a
+    single date's ratio drifts only ~0.6%, diluted across the 5-date range/mean) while THAT SAME
+    date's path-agreement delta -- measured relative to the anchor date specifically, not diluted by
+    the other four dates -- exceeds the tighter PATH_AGREEMENT_TOLERANCE. Passing only one of the two
+    required tests is insufficient: the verdict is still "mismatch"."""
+    stored = {d: 100.0 for d in _W}
+    fallback = {d: 100.0 for d in _W[:-1]}
+    fallback[_W[-1]] = 100.0 / 1.006  # a lone ~0.6% ratio drift on the LAST window date only
+    v = j10_recovery._compute_symbol_verdict("PATHBUG", _W, stored, fallback)
+    assert v.bridge_dispersion < BRIDGE_DISPERSION_BOUND  # bridge dispersion ALONE would pass
+    assert v.path_agreement_max_delta > PATH_AGREEMENT_TOLERANCE  # path agreement ALONE fails
+    assert v.verdict == "mismatch"
+    assert "path agreement" in v.reason
+    assert v.bridge_factor is None
+
+
+def test_symbol_verdict_inconclusive_with_zero_comparable_pairs():
+    """TC-5 (zero pairs): stored has data but the fallback provider returned nothing at all for this
+    symbol -> "inconclusive", never "agree" -- and the stored-only rows are still recorded as pairs
+    (fallback_close=None), never silently dropped."""
+    stored = {d: 100.0 for d in _W}
+    v = j10_recovery._compute_symbol_verdict("NOFALLBACK", _W, stored, {})
+    assert v.verdict == "inconclusive"
+    assert v.comparable_pair_count == 0
+    assert len(v.pairs) == len(_W)
+    assert all(p.fallback_close is None and p.ratio is None for p in v.pairs)
+
+
+def test_symbol_verdict_inconclusive_with_one_comparable_pair():
+    """TC-5 (one pair -- still below the >=2 floor needed to compute ANY metric): a single comparable
+    date cannot prove a "shape" or a "dispersion", so the verdict is "inconclusive" even though the
+    lone pair happens to match exactly."""
+    v = j10_recovery._compute_symbol_verdict("ONEPAIR", _W, {_W[0]: 100.0}, {_W[0]: 100.0})
+    assert v.verdict == "inconclusive"
+    assert v.comparable_pair_count == 1
+    assert v.path_agreement_max_delta is None and v.bridge_dispersion is None
+
+
+def test_symbol_verdict_inconclusive_below_evidence_floor_despite_clean_data():
+    """TC-5 (partial coverage: 2 comparable pairs, below MIN_COMPARABLE_PAIRS_PER_SYMBOL=3): both
+    metrics are PERFECT (identical series) yet the verdict must still be "inconclusive" -- "not
+    contradicted" is not "proven"."""
+    stored = {_W[0]: 100.0, _W[1]: 101.0}
+    fallback = {_W[0]: 100.0, _W[1]: 101.0}
+    v = j10_recovery._compute_symbol_verdict("BELOWFLOOR", _W, stored, fallback)
+    assert v.comparable_pair_count == 2 < MIN_COMPARABLE_PAIRS_PER_SYMBOL
+    assert v.verdict == "inconclusive"
+    assert v.bridge_factor is None
+    assert "evidence floor" in v.reason
+
+
+def test_symbol_verdict_mismatch_still_wins_over_a_coverage_gap():
+    """TC-6 (per-symbol carry-forward of audit B1's ordering): only 2 comparable pairs (below the
+    3-pair floor) but they clearly disagree -- the genuine mismatch must NOT be downgraded to
+    "inconclusive" by the coverage gap."""
+    stored = {_W[0]: 100.0, _W[1]: 100.0}
+    fallback = {_W[0]: 100.0, _W[1]: 50.0}  # a 2:1 split-away value
+    v = j10_recovery._compute_symbol_verdict("GAPMISMATCH", _W, stored, fallback)
+    assert v.comparable_pair_count == 2 < MIN_COMPARABLE_PAIRS_PER_SYMBOL
+    assert v.verdict == "mismatch"
+
+
+def test_symbol_verdict_never_fabricates_a_pair_when_stored_is_absent():
+    """A window date with no STORED baseline at all is never even turned into a pair (nothing to
+    anchor a comparison to) -- distinct from a stored-but-no-fallback pair, which IS recorded."""
+    stored = {_W[0]: 100.0, _W[2]: 102.0}  # _W[1], _W[3], _W[4] have no stored row at all
+    fallback = {d: 100.0 for d in _W}
+    v = j10_recovery._compute_symbol_verdict("SPARSE", _W, stored, fallback)
+    assert len(v.pairs) == 2
+    assert {p.trading_date for p in v.pairs} == {_W[0], _W[2]}
+
+
+# ==================================================================================================
+# check_adjustment_convention_per_symbol — orchestration (DB + injected fake provider), iter-8 redesign
+# ==================================================================================================
+class _FakeDailyProvider(PriceProvider):
+    """Returns canned OHLC bars per symbol from a `{symbol: {date: close}}` series -- open/high/low are
+    each offset from close by a FIXED, DISTINCT amount (never equal to close or to each other) so a
+    test can verify ALL FOUR fields get bridge-transformed independently, not just close. Raises
+    ProviderUnavailableError for any symbol named in `fail_for`. Records every symbol requested, in
+    call order."""
 
     def __init__(self, series: dict[str, dict[date, float]], *, fail_for: frozenset[str] = frozenset()):
         self._series = series
@@ -328,362 +468,312 @@ class _FakeAdjustedCloseProvider(PriceProvider):
         self.requested_symbols: list[str] = []
 
     def get_daily(self, symbol, start=None, end=None):
-        pytest.fail(f"get_daily called for {symbol} — the convention check must use get_adjusted_close")
-
-    def get_adjusted_close(self, symbol, start=None, end=None):
         self.requested_symbols.append(symbol)
         if symbol in self._fail_for:
-            raise ProviderUnavailableError(f"synthetic adjusted-close failure for {symbol!r}")
-        return dict(self._series.get(symbol, {}))
-
+            raise ProviderUnavailableError(f"synthetic get_daily failure for {symbol!r}")
+        bars = []
+        for d, close in sorted(self._series.get(symbol, {}).items()):
+            if start is not None and d < start:
+                continue
+            if end is not None and d > end:
+                continue
+            bars.append(Bar(date=d, open=close - 0.5, high=close + 1.0, low=close - 1.0, close=close, volume=777.0))
+        return bars
 
-def test_convention_check_default_sample_is_documented_and_in_scope():
-    """The default sample (>= 15 tickers per goal.md) is a real subset of RECOVERY_SYMBOLS, deterministic
-    (a tuple, not a set), MNST-free, and duplicate-free — a cheap constant-sanity check, no DB/network."""
-    assert len(CONVENTION_CHECK_SAMPLE_SYMBOLS) >= 15
-    assert isinstance(CONVENTION_CHECK_SAMPLE_SYMBOLS, tuple)
-    assert set(CONVENTION_CHECK_SAMPLE_SYMBOLS) <= RECOVERY_SYMBOLS
-    assert "MNST" not in CONVENTION_CHECK_SAMPLE_SYMBOLS
-    assert len(set(CONVENTION_CHECK_SAMPLE_SYMBOLS)) == len(CONVENTION_CHECK_SAMPLE_SYMBOLS)
 
+def test_per_symbol_check_uses_get_daily_never_get_adjusted_close(tmp_path):
+    """Resolves B2/TC-9: the redesigned gate calibrates on get_daily's raw close -- a provider whose
+    get_adjusted_close raises if ever called proves no code path uses it."""
+    class _RaisesIfAdjustedCloseCalled(_FakeDailyProvider):
+        def get_adjusted_close(self, symbol, start=None, end=None):
+            pytest.fail(f"get_adjusted_close called for {symbol} — iter-8's gate must use get_daily only")
 
-def test_convention_check_agree_when_all_sampled_pairs_within_tolerance(tmp_path):
-    """TC-4: every sampled pair's fake adjusted-close equals the stored daily_prices close exactly (well
-    within tolerance) -> "agree", and zero rows are written to any table."""
     engine = _engine(tmp_path)
-    symbols = ["AAPL", "MSFT"]
-    window = [date(2026, 8, 6), date(2026, 8, 7), date(2026, 8, 10)]
+    window = [date(2026, 8, 6), date(2026, 8, 7)]
     with Session(engine) as session:
-        for sym, base in (("AAPL", 200.0), ("MSFT", 400.0)):
-            for i, d in enumerate(window):
-                session.add(DailyPrice(
-                    symbol=sym, date=d, open=base, high=base, low=base, close=base + i, volume=1.0
-                ))
+        session.add(DailyPrice(symbol="AAPL", date=window[0], open=1, high=1, low=1, close=200.0, volume=1))
+        session.add(DailyPrice(symbol="AAPL", date=window[1], open=1, high=1, low=1, close=201.0, volume=1))
         session.commit()
 
-    series = {
-        "AAPL": {window[0]: 200.0, window[1]: 201.0, window[2]: 202.0},
-        "MSFT": {window[0]: 400.0, window[1]: 401.0, window[2]: 402.0},
-    }
-    provider = _FakeAdjustedCloseProvider(series)
+    provider = _RaisesIfAdjustedCloseCalled({"AAPL": {window[0]: 200.0, window[1]: 201.0}})
     with Session(engine) as session:
-        result = check_adjustment_convention(
-            session, provider=provider, sample_symbols=symbols, window_dates=window,
+        result = check_adjustment_convention_per_symbol(
+            session, provider=provider, sample_symbols=["AAPL"], window_dates=window,
         )
-
-    assert result.verdict == "agree"
-    assert len(result.pairs) == 6
-    assert all(p.within_tolerance for p in result.pairs)
-    assert provider.requested_symbols == ["AAPL", "MSFT"]  # one call per symbol, never per (symbol, date)
-
-    with Session(engine) as session:
-        assert len(session.exec(select(DailyPrice)).all()) == 6  # only the 6 seeded rows — nothing new
-        assert session.exec(select(ScannerRun)).all() == []
-        assert session.exec(select(DataProviderRun)).all() == []
+    assert result.verdicts[0].symbol == "AAPL"
+    assert provider.requested_symbols == ["AAPL"]
 
 
-def test_convention_check_mismatch_when_a_sampled_pair_exceeds_tolerance(tmp_path):
-    """TC-5: one sampled pair (AAPL's second date) diverges by far more than the tolerance — a synthetic
-    2:1 split-away value — so the verdict is "mismatch"; every OTHER pair is still compared (the dev
-    handoff needs every sampled pair's observed delta, not just the first failure), and zero rows are
-    written anywhere."""
+def test_per_symbol_check_judges_each_symbol_independently(tmp_path):
+    """A mixed batch: one symbol agrees, one symbol's fallback fetch fails outright -- each symbol's
+    verdict reflects only its OWN evidence, and a failure on one does not stop the batch (deliberately
+    different from iter-7's aggregate 'stop on first failure')."""
     engine = _engine(tmp_path)
-    symbols = ["AAPL", "MSFT"]
-    window = [date(2026, 8, 6), date(2026, 8, 7)]
+    window = [date(2026, 8, 6), date(2026, 8, 7), date(2026, 8, 10)]
     with Session(engine) as session:
         for sym, base in (("AAPL", 200.0), ("MSFT", 400.0)):
-            for d in window:
-                session.add(DailyPrice(symbol=sym, date=d, open=base, high=base, low=base, close=base, volume=1.0))
+            for i, d in enumerate(window):
+                session.add(DailyPrice(symbol=sym, date=d, open=base, high=base, low=base, close=base + i, volume=1.0))
         session.commit()
 
-    series = {
-        "AAPL": {window[0]: 200.0, window[1]: 100.0},  # a 2:1 split-away value, far outside tolerance
-        "MSFT": {window[0]: 400.0, window[1]: 400.0},
-    }
-    provider = _FakeAdjustedCloseProvider(series)
+    series = {"AAPL": {window[0]: 200.0, window[1]: 201.0, window[2]: 202.0}}  # exact match -> agree
+    provider = _FakeDailyProvider(series, fail_for=frozenset({"MSFT"}))
     with Session(engine) as session:
-        result = check_adjustment_convention(
-            session, provider=provider, sample_symbols=symbols, window_dates=window,
+        result = check_adjustment_convention_per_symbol(
+            session, provider=provider, sample_symbols=["AAPL", "MSFT"], window_dates=window,
         )
-
-    assert result.verdict == "mismatch"
-    assert len(result.pairs) == 4  # both symbols' both dates were still compared
-    mismatched = [p for p in result.pairs if p.within_tolerance is False]
-    assert len(mismatched) == 1
-    assert mismatched[0].symbol == "AAPL" and mismatched[0].trading_date == window[1]
-    assert provider.requested_symbols == ["AAPL", "MSFT"]  # MSFT still fetched — full evidence gathered
-
-    with Session(engine) as session:
-        assert len(session.exec(select(DailyPrice)).all()) == 4  # only the 4 seeded rows
-        assert session.exec(select(ScannerRun)).all() == []
-        assert session.exec(select(DataProviderRun)).all() == []
+    by_symbol = {v.symbol: v for v in result.verdicts}
+    assert by_symbol["AAPL"].verdict == "agree"
+    assert by_symbol["MSFT"].verdict == "inconclusive"
+    assert "fetch failed" in by_symbol["MSFT"].reason
+    assert provider.requested_symbols == ["AAPL", "MSFT"]  # MSFT was still attempted, not skipped
 
 
-def test_convention_check_inconclusive_when_provider_fails(tmp_path):
-    """TC-6: a provider failure on one sampled symbol yields "inconclusive" — NEVER a false "agree" —
-    and zero rows are written anywhere. The failure stops further comparison fetches (a systemic
-    failure gives no reason to expect the next call would succeed)."""
+def test_per_symbol_check_never_writes_to_any_table(tmp_path):
+    """A direct restatement of the DoD's own read-only requirement across a mismatching symbol."""
     engine = _engine(tmp_path)
-    symbols = ["AAPL", "MSFT"]
-    window = [date(2026, 8, 6)]
+    window = [date(2026, 8, 6), date(2026, 8, 7)]
     with Session(engine) as session:
-        for sym in symbols:
-            session.add(DailyPrice(symbol=sym, date=window[0], open=1, high=1, low=1, close=100.0, volume=1))
+        session.add(DailyPrice(symbol="AAPL", date=window[0], open=1, high=1, low=1, close=200.0, volume=1))
+        session.add(DailyPrice(symbol="AAPL", date=window[1], open=1, high=1, low=1, close=201.0, volume=1))
         session.commit()
 
-    provider = _FakeAdjustedCloseProvider(
-        {"AAPL": {window[0]: 100.0}}, fail_for=frozenset({"AAPL"}),
-    )
+    provider = _FakeDailyProvider({"AAPL": {window[0]: 100.0, window[1]: 50.0}})  # forces mismatch
     with Session(engine) as session:
-        result = check_adjustment_convention(
-            session, provider=provider, sample_symbols=symbols, window_dates=window,
+        check_adjustment_convention_per_symbol(
+            session, provider=provider, sample_symbols=["AAPL"], window_dates=window,
         )
-
-    assert result.verdict == "inconclusive"
-    assert "AAPL" in result.reason
-    assert provider.requested_symbols == ["AAPL"]  # stopped at the first failure — MSFT never attempted
-
     with Session(engine) as session:
         assert len(session.exec(select(DailyPrice)).all()) == 2  # only the 2 seeded rows
         assert session.exec(select(ScannerRun)).all() == []
         assert session.exec(select(DataProviderRun)).all() == []
 
 
... [diff_bound] apps/backend/tests/test_j10_recovery.py: 415 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_provider_clients.py b/apps/backend/tests/test_provider_clients.py
index 36d160e4..471ed1dd 100644
--- a/apps/backend/tests/test_provider_clients.py
+++ b/apps/backend/tests/test_provider_clients.py
@@ -192,6 +192,72 @@ def test_yahoo_reported_error_and_empty_result_still_raise():
         YahooProvider(client=_FakeClient(payload={"chart": {"error": None, "result": []}})).get_daily("ZZZZ")
 
 
+# ==================================================================================================
+# Yahoo get_adjusted_close / _parse_adjusted_close (J-10 step 2a, iter-7) — resolves T2 (iter-7 audit):
+# every failure branch gets its own synthetic-payload test, mirroring the get_daily tests above (no
+# branch was previously pinned — only a one-time, non-repeatable live probe). iter-8's redesigned J-10
+# gate no longer calls this method (it calibrates on get_daily's raw close instead — see
+# j10_recovery.py's module docstring, "ITERATION 8 REDESIGN"); it stays an additive, tested capability.
+# ==================================================================================================
+def test_yahoo_adjusted_close_reported_error_raises():
+    """Branch: chart.error."""
+    provider = YahooProvider(client=_FakeClient(payload={"chart": {"error": "Not Found", "result": None}}))
+    with pytest.raises(ProviderUnavailableError):
+        provider.get_adjusted_close("ZZZZ")
+
+
+def test_yahoo_adjusted_close_missing_result_raises():
+    """Branch: empty/missing result list."""
+    provider = YahooProvider(client=_FakeClient(payload={"chart": {"error": None, "result": []}}))
+    with pytest.raises(ProviderUnavailableError):
+        provider.get_adjusted_close("ZZZZ")
+
+
+def test_yahoo_adjusted_close_empty_timestamp_returns_empty_dict_not_an_error():
+    """Branch: empty timestamp array. Mirrors get_daily's empty-window allowance (an honest zero-rows
+    answer, never a fault) — here the return shape is a dict, so the honest empty answer is `{}`."""
+    payload = {"chart": {"error": None, "result": [{
+        "meta": {"symbol": "SATS"}, "indicators": {"adjclose": [{}], "quote": [{}]},
+    }]}}
+    provider = YahooProvider(client=_FakeClient(payload=payload))
+    assert provider.get_adjusted_close("SATS", start=date(2026, 8, 3), end=date(2026, 8, 14)) == {}
+
+
+def test_yahoo_adjusted_close_absent_adjclose_block_raises():
+    """Branch: absent adjclose block. A response with a `quote` block but NO `adjclose` block at all —
+    the load-bearing failure mode this method exists to guard against (never silently fall back to the
+    raw close)."""
+    payload = {"chart": {"error": None, "result": [{
+        "timestamp": [_unix(date(2024, 1, 2))],
+        "indicators": {"quote": [{"close": [185.5]}]},  # no "adjclose" key anywhere
+    }]}}
+    with pytest.raises(ProviderUnavailableError) as exc:
+        YahooProvider(client=_FakeClient(payload=payload)).get_adjusted_close("AAPL")
+    assert "adjclose" in str(exc.value)
+
+
+def test_yahoo_adjusted_close_malformed_shape_raises():
+    """Branch: malformed shape. `indicators.adjclose` is present but its own inner block carries no
+    "adjclose" key — an unexpected-shape KeyError, surfaced honestly rather than fabricated."""
+    payload = {"chart": {"error": None, "result": [{
+        "timestamp": [_unix(date(2024, 1, 2))],
+        "indicators": {"adjclose": [{}], "quote": [{"close": [185.5]}]},
+    }]}}
+    with pytest.raises(ProviderUnavailableError) as exc:
+        YahooProvider(client=_FakeClient(payload=payload)).get_adjusted_close("AAPL")
+    assert "unparseable" in str(exc.value)
+
+
+def test_yahoo_adjusted_close_skips_null_cell_never_fabricates():
+    """Branch: null-cell skip. A null adjusted close is a provider gap — SKIPPED, never back-filled."""
+    payload = {"chart": {"error": None, "result": [{
+        "timestamp": [_unix(date(2024, 1, 2)), _unix(date(2024, 1, 3))],
+        "indicators": {"adjclose": [{"adjclose": [185.1, None]}]},
+    }]}}
+    series = YahooProvider(client=_FakeClient(payload=payload)).get_adjusted_close("AAPL")
+    assert series == {date(2024, 1, 2): 185.1}
+
+
 # ==================================================================================================
 # Tiingo (key-aware)
 # ==================================================================================================
diff --git a/docs/goal.md b/docs/goal.md
index c4eccb0b..a88116b4 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -654,7 +654,9 @@ manifest artifact (it must be self-describing and self-caveating).
             bound. That stability IS the convention-agreement evidence; a drifting or erratic ratio
             means the two series are not on one consistent scale and the symbol fails.
          **A passing bridge MUST then be applied.** Restored values are the fallback provider's fields
-         **transformed by that symbol's bridge factor onto the existing Stooq historical scale** —
+         **transformed by that symbol's bridge factor onto the existing STORED historical scale**
+         (see the vendor-provenance correction in Acceptance: the stored bars in the overlap region
+         are not necessarily Stooq's) —
          applied consistently to every price field (open/high/low/close, not close alone, or the bar
          becomes internally inconsistent; volume is not a price and is not scaled). **Passing the gate
          does NOT authorize inserting raw Yahoo adjusted-close values unchanged** — an untransformed
@@ -702,6 +704,42 @@ manifest artifact (it must be self-describing and self-caveating).
          claim would need its own pre-registered experiment (AG-4/AG-15). If Yahoo also proves
          unreachable or fails the convention check, that is an honest miss — stop and report it;
          do not try a third vendor without a new amendment.
+    2b. **Validation sample vs recovery population — two different things (owner, 2026-08-21).**
+       Iteration 8 restored 20 of 587 symbols and then declined to continue, reading the
+       anti-goodharting rule as a cap on coverage. That reading conflates two distinct populations,
+       and the distinction is now explicit:
+       - **The methodology-validation sample** exists to establish *whether the fallback-provider
+         convention/bridge methodology is admissible* under the fixed fail-closed rules. Its
+         composition is **frozen for that methodological test**. The anti-goodharting prohibition
+         stands unchanged and in full force: it must never be enlarged, redrawn, filtered,
+         substituted, cherry-picked, expanded toward easier names, or otherwise changed **for the
+         purpose of converting a failing or inconclusive methodology verdict into a passing one**.
+         The evidence already obtained from that sample remains the evidence for the methodology
+         decision. Nothing here permits re-running alternative samples until one passes.
+       - **The authorized recovery population** exists to *restore the exact rows independently
+         proven missing* by the iter-5 drill. It was established **before** the fallback methodology
+         result, from the drill's own audit record — it is not a sample selected after seeing an
+         outcome — and it currently holds **587 symbols over the two authorized dates**.
+       **Binding invariant:** *the prohibition on widening or redrawing the methodology-validation
+       sample does not restrict execution over the already frozen J-10 recovery population. Once the
+       recovery methodology is admissible, every member of the independently established recovery
+       population must be evaluated under the same fixed per-symbol gate.* The anti-goodharting rule
+       therefore does **not** cap recovery at the first 20 symbols.
+    2c. **No population-level pass, ever.** The 20 successful symbols do **not** authorize insertion
+       for the other 567. Each remaining symbol must independently satisfy the same precommitted
+       fail-closed requirements under the existing fixed methodology, including as applicable: exact
+       authorized symbol/date membership; same-series validation; minimum usable evidence;
+       path/bridge agreement; bridge-factor stability; field-level convention compatibility;
+       deterministic ticker mapping; no out-of-scope row overwrite; no threshold override; persisted
+       pair-level evidence; and a bridge calibration reproducible from that persisted evidence.
+       For any symbol: **`mismatch` or `inconclusive` ⇒ zero rows written for that symbol.** Do not
+       loosen thresholds after seeing failures. Do not substitute a different methodology for
+       troublesome symbols without a later explicit goal amendment.
+    2d. **Continue from 20/587 — do not restart.** The 20 already-restored symbols stay restored if
+       they satisfy the corrected J-10 contract and the audit findings. Do not delete or revert them
+       merely to restart the recovery. Treat current state as **20 validly restored · 567 still
+       pending individual evaluation**, and make the next recovery pass **idempotent** over the
+       restored 20 (already-complete symbols are skipped, never re-fetched or overwritten).
     3. **Never overwrite a survivor.** Insert only missing rows; every surviving row stays
        byte-unchanged. Derived state for those two dates (`scanner_runs` and their snapshots) is
        rebuilt through the normal ingest path once the bars are present, and must not touch any
@@ -718,22 +756,86 @@ manifest artifact (it must be self-describing and self-caveating).
        2026-08-12 is restored; (b) no other historical date was modified — compare against the
        recorded pre-recovery state; (c) surviving rows were not overwritten unnecessarily;
        (d) the dataset frontier did **not** advance past 2026-08-12 as a result of the repair;
-       (e) the project's data/DB-integrity checks pass; (f) the original destructive condition is
-       gone — `GET /api/compass?as_of=2026-08-12` serves again and J-01/J-02/J-03 replay clean.
+       (e) the project's data/DB-integrity checks pass; (f) the RAW-layer destructive condition is
+       gone — canonical price coverage exists for both dates.
+       **Scope correction (owner, 2026-08-21): the final derived-state cleanliness claim does NOT
+       belong to J-10.** `GET /api/compass?as_of=2026-08-12` serving cleanly and J-01/J-02/J-03
+       replaying clean are now **J-11 Stage G** criteria, because the derived state those checks read
+       is exactly what J-11 exists to regenerate. J-10 verifies raw-layer facts and safe DB state only,
+       and may report: rows restored; canonical price coverage restored; no unauthorized overwrite or
+       date expansion; and that temporary recovery-era `ScannerRun`s remain pending J-11. J-10 must
+       **not** claim the derived state is clean, and must not require create-once APIs to refresh runs
+       they cannot refresh (see step 5b).
+    5b. **Completing the remaining raw rows does NOT refresh the existing 2026-08-11/12 ScannerRuns
+       (owner, 2026-08-21 — verified against the implementation).** J-10's rebuild step is a
+       **create-once no-op** when a snapshot already exists: `run_bounded_recovery_backfill`'s own
+       docstring states *"A true no-op (create-once) if a snapshot already exists for both dates"*
+       (`j10_recovery.py:756-761`), and it routes through `scanner.persist_run_payload`, which opens
+       with `existing = get_run_for_date(...); if existing is not None: return existing  # immutable:
+       never re-create or overwrite an existing run` (`scanner.py:95-97`). Iteration 8 already created
+       runs for both dates while only **20 of 587** symbols were restored, so:
+       > Completing the remaining 567 raw-price rows does not automatically refresh the already-existing
+       > 2026-08-11 / 2026-08-12 `ScannerRun`s. They remain derived from the partial raw basis until
+       > J-11 deliberately clears and regenerates them.
+       They are therefore **not** final reconstructed snapshots, and J-10 must not describe them as
+       such. **Status of those rows, recorded explicitly:**
+       > Any `ScannerRun` for 2026-08-11 or 2026-08-12 created before J-10's final raw-input recovery
+       > completes is **known temporary / recovery-era derived state**. It is non-authoritative for the
+       > repaired dataset until J-11 clears and recreates the full incident set.
+       Do **not** delete those runs inside J-10 merely to satisfy J-10 acceptance — their deliberate
+       removal belongs to J-11 Stage C. Do **not** mint new manifests to reflect this status, and do
+       **not** mutate existing ones.
        If byte-for-byte restoration cannot be demonstrated because the vendor archive is not itself
        immutable, **state that limitation plainly** and verify the strongest practical invariants
        instead (per-symbol row presence, OHLCV shape, expected session count, no gap against the
        surrounding trading days).
+    5a. **Account for every mutation the verification itself causes (owner, 2026-08-21).**
+       Iteration 8's step-5(f) check required starting the backend, and this codebase's boot warmup
+       created an unrelated `ScannerRun` for **2026-05-12**. Investigation showed it benign — no
+       `daily_prices` row changed, no manifest changed, no network fetch, computed from
+       already-committed data — so it is *not* equivalent to unauthorized price-data recovery. It is
+       still an unexpected persistent write outside the intended verification scope, and
+       verification must stop being blind to that class of write. Recovery verification MUST
+       reconcile **all** database mutations caused by the verification procedure itself, classifying
+       each as:
+       - **an authorized recovery write** — the intended recovery-date price rows, plus the
+         explicitly expected derived-state rebuild for those two dates; or
+       - **an incidental product write** — e.g. backend boot warmup creating an unrelated scanner
+         run. Incidental writes MUST be **detected, recorded, and explained**, and MUST be
+         **excluded from any claim that verification was side-effect-free**.
+       **A verification step must never claim "no out-of-scope writes" if the application itself
+       produced an unrelated persistent row during that verification.** Where practical within the
+       existing architecture, prefer a verification path that suppresses or isolates automatic boot
+       warmup writes — but do NOT turn this into a broad redesign of application startup within this
+       goal. If suppression or isolation is not trivial, record the known side effect as a defect
+       and require exact before/after mutation accounting for every J-10 verification run.
     6. **Close the exception.** Once verification passes, record in the handoff that AG-9's dated
        exception is **exhausted**; normal offline-deterministic ingest applies again automatically.
+       "Verification passes" means the recovery is complete per the completion rule in Acceptance —
+       a partial restoration does not exhaust the exception, because the remaining authorized
+       symbols still need it.
     7. All recovery work stays on the session branch `goal/market-compass`; `main` is not touched.
   - Acceptance:
     - **Consistency (single source):** restored rows enter through the existing ingest/provider
       path — no second write path, no hand-edited rows, no new provenance framework; the missing
       set is computed once and is the sole input to the fetch.
+    - **Responsibility boundary (owner, 2026-08-21) — J-10 and J-11 must not be circular.**
+      > **J-10 repairs canonical inputs. J-11 repairs the derived state built from those inputs.**
+      J-10's terminal state is **raw-layer only**: every symbol in the frozen 587 population is either
+      restored under the fixed per-symbol gate or explicitly classified fail-closed/unrestorable under
+      the owner-authorized completion policy; `daily_prices` for 2026-08-11/12 carries the strongest
+      provable intended coverage; surviving price rows were not overwritten; no third date was fetched
+      or modified; raw OHLCV/provider-convention invariants pass; provider and recovery provenance are
+      recorded; and AG-9's live-fetch exception is exhausted when those raw criteria pass.
+      **J-10 must NOT require J-11's clean derived-state regeneration to be complete before J-10 can
+      close** — requiring it would deadlock, since J-11 is itself gated behind J-10's terminal state.
+      J-11 owns: clearing the 11-date incident derived state; recreating runs and child rows under one
+      engine generation; forward-return hole repair; dependency-aware cache invalidation/rewarm;
+      manifest/run schema reconciliation; and final incident-wide serving consistency.
     - **Correctness:** the two dates are restored, no third date is touched, no surviving row is
-      overwritten, the frontier is unchanged at 2026-08-12, and J-01/J-02/J-03 pass a live replay
-      again. If the restoration is cross-vendor (step 2a), the path-agreement test passed on
+      overwritten, and the frontier is unchanged at 2026-08-12. (Final repaired-state J-01/J-02/J-03
+      replay is a **J-11 Stage G** criterion, not a J-10 one — see step 5a/5b.) If the restoration is
+      cross-vendor (step 2a), the path-agreement test passed on
       precommitted criteria, every restored symbol had a stable bridge that was actually applied to
       all four price fields (no raw fallback value inserted unchanged), any symbol without one is
       listed as not-restored, and every restored row carries its true `yahoo` provenance.
@@ -743,9 +845,456 @@ manifest artifact (it must be self-describing and self-caveating).
       2026-07-01) could not restore these dates. AG-17 governs what the repair may NOT do to
       provenance. If any part of the recovery cannot be proven to stay inside the authorized scope,
       the iteration stops for owner review rather than broadening the fetch.
-    - **Walkthrough:** waived — data-layer repair with no UI surface change of its own; the demo
-      requirement is replaced by the provenance record, the verification evidence, and the
-      J-01/J-02/J-03 live replay that proves the damage is gone.
+    - **Completion rule (owner, 2026-08-21):** J-10 does **NOT** close merely because the recovery
+      mechanism has been demonstrated on 20 names. The goal is recovery of the proven deletion, not
+      a pilot implementation. J-10 remains **incomplete** while the majority of the authorized
+      recovery population is neither (a) restored under the fixed gate, nor (b) explicitly
+      classified as fail-closed/unrestorable under a goal-authorized completion policy. **Do not
+      invent a partial-completion threshold** — there is no "enough symbols" number, and none may be
+      introduced without an owner amendment. If some symbols ultimately cannot be restored under the
+      fixed methodology, surface the **exact residual set and the per-symbol reasons** for
+      owner/reviewer decision rather than silently lowering the coverage requirement.
+    - **Recorded finding — the one-series rule worked, and a vendor-provenance correction
+      (iteration 8; corrected 2026-08-21 by the out-of-band audit — read the correction, it changes
+      what the result means):** running the comparison and the restore through the same raw-close
+      series produced bridge factors of **exactly 1.0** for every restored symbol, and iteration 7's
+      ~0.865% CVX "mismatch" was indeed a **series-crossover artifact** — `adjclose` compared against
+      a stored raw close — which the one-series rule correctly eliminated. That conclusion stands.
+      **But the earlier attribution of this file was wrong and is corrected here: the stored bars in
+      the overlap window are NOT Stooq's — they are Yahoo's.** The committed seed ends 2026-07-01;
+      every post-seed fetch in `data_provider_runs` is `provider='yahoo'` (34 runs from 2026-07-17
+      onward), and the single `stooq` run, id 541, **failed with 0 symbols**. Consequences that every
+      future iteration must reason from:
+      - The gate compared **Yahoo against Yahoo** over that window, so the 1.0 factors were expected
+        by construction and the check **could not have failed** there. This makes the write *safer*
+        (no scale discontinuity is possible), but it is **NOT** cross-vendor validation evidence and
+        may never be cited as such.
+      - Iteration 7's crossover was therefore **within a single vendor** (`adjclose` vs raw close),
+        which is exactly why both offenders were dividend payers.
+      - "Bridge onto the existing scale" means the **stored** scale, whatever vendor produced it —
+        not "the Stooq scale". A genuinely cross-vendor overlap (pre-2026-07-01 seed region) has
+        never been exercised by this gate.
+      This finding is evidence that the corrected gate tests the intended property — it is **NOT**
+      grounds for removing, weakening, or skipping the convention gate, and must never be cited as
+      such.
+    - **Keep the closed audit findings closed:** generalizing recovery from 20 symbols to the full
+      authorized population must not regress **B2** (no raw/adjusted series crossover), **B3**
+      (persisted per-pair comparison evidence), **B5** (thresholds not caller-overridable), **B6**
+      (explicit authorized-date assertion), or the rule that **zero usable pairs can never return
+      `agree`**.
+    - **Traps this journey must actually prove** (each is a required check, not a nice-to-have):
+      1. the methodology-validation sample cannot be enlarged or redrawn after seeing its outcome to
+         chase a pass;
+      2. the full frozen 587-symbol recovery population is nevertheless eligible for processing;
+      3. a passing methodology sample gives untested symbols **no** automatic pass;
+      4. every restored symbol has its own persisted evidence and verdict;
+      5. previously restored valid symbols are idempotently skipped, never overwritten;
+      6. a failing or inconclusive symbol produces **zero** writes for that symbol;
+      7. fixed thresholds remain structurally non-overridable;
+      8. recovery cannot leave J-10 complete at `20/587`;
+      9. every database mutation caused during recovery verification is reconciled, **including
+         incidental `ScannerRun` creation** by backend boot warmup;
+      10. `Depth: full` cannot silently become `lean` without an explicit unmet-requirement record.
+    - **Walkthrough:** waived — **raw-layer** incident repair with no UI surface change of its own.
+      The J-10 demo requirement is replaced by the raw-recovery provenance record, bounded-scope
+      verification, canonical price-coverage evidence, and complete mutation reconciliation. **Final
+      repaired-state `GET /api/compass` serving and the J-01/J-02/J-03 replay belong exclusively to
+      J-11 Stage G** (owner, 2026-08-21 — this bullet previously claimed the replay as J-10's own
+      proof "that the damage is gone", which contradicted the J-10/J-11 responsibility boundary and
+      could pull the final derived-state check back into J-10).
+
+- **J-11: Incident-bounded clean regeneration of derived state (owner, 2026-08-21)**
+  - Why: the iter-5 drill's cascade left the derived layer for its incident dates in four *different*
+    conditions at once — rows that survived, rows still missing, rows incidentally recreated by
+    backend boot warmup, and rows partially rebuilt during J-10. Repairing each condition separately
+    is per-date archaeology with a large surface for error. Within the incident boundary those
+    derived rows are **deterministic outputs of preserved canonical inputs**, so they are disposable:
+    clear them and regenerate the whole incident set uniformly through the CURRENT canonical engines,
+    leaving one internally consistent derivation from one engine generation. The immutable evidence
+    layer stays separate and untouched. This deliberately removes the need to reason about old-vs-new
+    snapshot row format inside the incident set.
+  - **Prerequisite — J-10 first, hard gate.** J-11 does NOT replace or bypass J-10. J-10 still owns
+    restoration of the canonical `daily_prices` rows for 2026-08-11 and 2026-08-12 across the proven
+    587-symbol population (**currently 20 restored / 567 pending**). J-11 may not begin until **the
+    authorized J-10 raw-input recovery has reached its accepted terminal state and the canonical
+    daily-price coverage needed by every incident date has been verified.** Never run the derived
+    rebuild against a knowingly incomplete price layer, and never lower J-10's acceptance criteria to
+    unblock this journey.
+  - **The incident date set — all 11, not the 8 currently absent.** From the authoritative removal
+    audit (`data_provider_runs` id=538, whose own cascade record lists them):
+    `2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03, 2026-08-05,
+    2026-08-10, 2026-08-11, 2026-08-12`.
+    Scoping to only the absent dates would preserve exactly the inconsistency this journey exists to
+    remove: 2026-05-12 was incidentally rebuilt by boot warmup, and 2026-08-11/2026-08-12 were
+    partially rebuilt during J-10. Verified current state (read-only, 2026-08-21) — 2026-05-12: 1 run
+    / 0 manifests · 2026-05-13, 07-10, 07-13, 07-24, 07-27, 08-03: 0 runs / 0 manifests · **2026-08-05:
+    0 runs / 2 manifests (orphaned — its source run was destroyed)** · 2026-08-10: 1 run / 1 manifest ·
+    2026-08-11: 1 run / 3 manifests · 2026-08-12: 1 run / 6 manifests. **This authorizes no deletion of
+    raw price rows for these or any other dates.**
+  - Steps:
+    1. **Do NOT call `clear_snapshot_set()` (`app/engine/data_manager.py:2212`).** That helper is
+       correct for what it does — it deletes `ForwardReturn` → `ScannerResult` → `SectorScoreRow` →
+       `ThemeScoreRow` → `ScannerRun` children-before-parents, whole-row only, never referencing
+       `DailyPrice`, and asserts `bars_before == bars_after` — but it takes **no date filter and
+       clears the ENTIRE historical snapshot set** (J-85 semantics). A full-history reset would not be
+       a neutral repair: `config.yaml` `scanner.snapshot_cadence` is `deep_cadence: monthly` with
+       `daily_start: 2026-06-01`, and the config itself records a surviving create-once **daily stretch
+       2021-01→2021-04** that today's cadence does not imply — a wholesale rebuild would silently
+       discard real point-in-time density. Specify instead a narrow mechanism conceptually equivalent
+       to **`clear_snapshot_dates(EXACT_INCIDENT_DATE_SET)`**, reusing the SAME child-before-parent
+       deletion semantics, whole-row-delete discipline, and price-untouched assertion as
+       `clear_snapshot_set` rather than inventing different semantics. J-11 is incident-bounded, never
+       a cadence reset.
+    2. **Classify before deleting — explicit allowlist, produced by inspecting the live model graph,
+       never `DELETE FROM <everything except prices>`.** The classification below is the verified
+       starting point; the developer must re-derive it against the current models and extend it if
+       inspection finds more:
+       - **Canonical input — never deleted:** `daily_prices`; the reference/universe tables (`stocks`,
+         `etfs`, `sectors`, `industries`, `themes`, `theme_members`); `macro_series`. The reset MUST
+         assert the `daily_prices` row count **and** a content fingerprint/coverage measure are
+         identical immediately before and after the deletion step.
+       - **Immutable / audit evidence — never deleted, rewritten, or re-created as newly historical:**
+         `next_session_manifests` and their export artifacts; `data_provider_runs`; `import_checkpoints`;
+         the certified-claims ledger (`runs/goal-session-mcp-loop/state/certified-claims.jsonl`), the
+         staging ledger, pre-registrations, and graveyard/rejected-hypothesis history; the recovery and
+         audit artifacts including all iter-5 and iter-8 evidence; existing goal/session audit history.
+       - **User state — never deleted:** `watchlist`, plus any other user-authored rows inspection finds.
+       - **Rebuildable incident-derived state — cleared and regenerated for the 11 dates only:**
+         `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`, and the associated
+         canonical derived forward-return state as the real dependency graph requires.
+    3. **Regenerate through the canonical engines only.** Rebuild the 11 dates through the same
+       production computation paths normal snapshots use — `scanner.run_scan` (`scanner.py:226`) and
+       the canonical `persist_run_payload` (`scanner.py:85`) — plus the canonical forward-return
+       helpers. Introduce **no** recovery-specific scoring, regime, sector, theme, setup, pattern or
+       return formula, and no second computation implementation. Rebuilt runs then carry the current
+       engine identity and current additive schema naturally, because the normal production path
+       stamps them. Do **not** hand-patch current-format columns onto legacy rows when deleting and
+       canonically recreating makes that unnecessary. Do not apply current cadence to choose a
+       different historical date universe — regenerate exactly the 11 incident dates.
+    4. **Mint NO new historical manifests (critical).** The ingest-finalize tail calls
+       `compass.get_or_create_manifest(session, run_for_date, cfg, producer="ingest_finalize")` for
+       **every** date in `prog.new_snapshot_dates` (`data_manager.py:4526-4538`). During an ordinary
+       backfill that legitimately creates a retrospective manifest — here it must not. **7 of the 11
+       incident dates currently have no manifest at all** (2026-05-13, 07-10, 07-13, 07-24, 07-27,
+       08-03, and 05-12), so an unguarded rebuild would manufacture 7 immutable "historical" decision
+       artifacts that never existed at their supposed historical time. Binding rule:
+       > **Incident-rebuild snapshot creation must not mint a `NextSessionManifest` for an as-of that
+       > did not already have one before the maintenance operation.**
+       For the 4 dates that DO have manifests (2026-08-05, 08-10, 08-11, 08-12): do not regenerate
+       them, and do not change `version`, `source_run_id`, `available_at_utc`, `content_hash`,
+       `manifest_hash`, or `prospective_eligible`. The existing read-time **basis disclosure** is the
+       sanctioned mechanism for surfacing that a stored source run was rebuilt or is unavailable
+       relative to the manifest's recorded source-run timestamp — note 2026-08-05 already carries 2
+       manifests with **zero** surviving runs, so it exercises exactly that path. A maintenance rebuild
+       must never create an apparently historical prior that did not actually exist at that time.
+       **Add a named test for this.**
+    5. **Repair the full forward-return damage, not just the rebuilt runs.** Rebuilding 11 runs is not
+       sufficient. The removal path's defensive consistency sweep
+       (`data_manager.py:2185-2192`) deletes **any** `ForwardReturn` whose `measured_date` falls on a
+       removed bar date — *including rows whose originating `ScannerRun` was never removed*. So holes
+       exist on retained runs. After J-10 has restored the raw bars and the 11 snapshots are
+       regenerated, run the existing **create-once** canonical forward-return machinery
+       (`forward_testing.backfill_forward_returns` / `backfill_run_forward_returns`, whose
+       `_insert_run_forward_returns` is create-once) over the retained + rebuilt snapshot set to fill
+       every derivable missing row. Do **not** recompute or overwrite surviving rows, and do **not**
+       introduce a second return formula. The post-rebuild audit must distinguish three populations:
+       (a) forward returns belonging to the 11 rebuilt runs; (b) holes on otherwise-retained runs
+       caused by the original 2026-08-11/12 bar deletion; (c) genuinely not-yet-mature horizons, which
+       **must remain absent/NA**. Never fabricate a forward return to reach row-count parity.
+    6. **Invalidate caches explicitly — the same-stamp collision is real, not hypothetical.**
+       `research._dataset_version()` (`research.py:2517`) returns `f"r{max_run_id}-f{fr_count}"` — the
+       max `scanner_runs.id` plus the `forward_returns` row count. A delete-and-recreate that restores
+       the same row counts, and reuses SQLite rowids (no `AUTOINCREMENT`), can therefore produce a
+       **byte-identical stamp**, and every dependent cache would keep serving its stale pre-reset
+       payload while appearing current. `_membership_dataset_version` (`research.py:2535`) is narrower
+       — the snapshot/`asof_date` set, bars manifest, history threshold — and collides just as easily
+       once the same date set is restored. Before implementation, classify **every** cache that depends
+       directly or transitively on `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`
+       or `forward_returns`, deriving the set from the current models rather than copying this list.
+       Verified today, all seven key on a dataset-version stamp: `event_study_cache`
+       (`subject, view, asof_key, dataset_version`), `market_phase_cache` (`asof_key, dataset_version`),
+       `forward_aggregate_cache` (`horizon, asof_key, dataset_version`), `index_series_cache`
+       (`range_key, full, dataset_version`), `availability_cache` (`dataset_version`),
+       `membership_timeline_cache` (`dataset_version`, narrow stamp), `coverage_snapshot`
+       (`asof_key, dataset_version`). For each, document one of: (1) its key is *guaranteed* to change
+       and cleanly invalidates; (2) explicitly delete the affected rows; or (3) explicitly regenerate
+       through the canonical producer. **Prefer deterministic explicit invalidation** wherever
+       delete/recreate could reproduce the same key. No stale cache may survive while appearing
+       current; do not delete a cache unrelated to the changed dependency graph.
+       **Classify by ACTUAL data dependency, not by table name or the mere presence of a
+       dataset-version field (owner, 2026-08-21).** Carrying a version stamp does not by itself mean a
+       payload depends on anything J-11 changes. Worked example, verified: `index_series_cache` stores
+       `indexes.compute_index_series(...)`, which hydrates the configured `index_chart.symbols` ETFs'
+       stored **`daily_prices`** — and J-11 modifies no price row at all, so its payload is unaffected
+       even though it carries a stamp; it may legitimately need no destructive invalidation. The
+       required disposition for every cache is therefore one of: **prove it unaffected and leave it
+       alone**; explicitly invalidate; or regenerate through the canonical producer. **Do not
+       blanket-delete the named caches for convenience** — a needless cache wipe is its own
+       (recoverable, but real) availability and compute cost, and it obscures which dependency the
+       repair actually touched.
+    7. **Preserve the evidence history and do not reinterpret it.** The canonical certified-claims
+       ledger currently holds **7 entries, all `FAIL`** (verified 2026-08-21; the staging ledger
+       likewise holds 7, all `FAIL`). Preserve both exactly. Do **not** reset trial count, Bonferroni
+       history, alpha-spend history, or rejected claims, and do **not** re-run old claims as part of
+       this maintenance. Record the semantic distinction: *old referee entries are historical verdict
+       records produced from the dataset that existed at their registration time; a later maintenance
+       regeneration must never be described as the dataset those historical verdicts originally
+       evaluated.* There is currently no PASS claim to invalidate — **that is not permission to rewrite
+       the history.** Two concrete write/reinterpret paths must stay shut for the whole of J-11:
+       `app/mcp/tools.py`'s `verify_edge` **appends** to a ledger (`ledger.append_entry`, `tools.py:660`)
+       and would consume a trial and spend alpha; and `app/engine/forward_walk.py` **re-scores** existing
+       claims — running it against the regenerated dataset is exactly the reinterpretation this rule
+       forbids. Neither may run as part of the maintenance. (`app/engine/evidence.py` is read-only —
+       `build_evidence_payload` serves the ledger and recomputes nothing — so the read side is safe.) (Note for implementers: `ledger.py`'s `rejection_offsets` docstring still says the
+       live ledger is `[1, 2, 4] PASS` — that comment is **stale**; the file itself is 7×FAIL. Trust the
+       file.) **If implementation discovers a current PASS/proven claim in any canonical source not
+       identified here, STOP and surface the conflict** rather than silently carrying a Proven label
+       across a materially changed research dataset. This journey is a repair, never a new
+       certification or research experiment.
+    8. **Do not bootstrap a fresh database from the committed seed.** A fresh DB is not equivalent to
+       the current canonical raw dataset: the seed window ends **2026-07-01**, while the live database
+       holds post-seed acquired history (all of it `provider='yahoo'` — 34 runs from 2026-07-17 on;
+       the single `stooq` run, id 541, failed with 0 symbols). Deleting `trendora.db` and re-seeding
+       would discard valid canonical input. Use the **current repaired `daily_prices` layer** as the
+       input to the bounded regeneration. A separate dataset-epoch migration may be designed later if
+       ever wanted; it is not required to resolve this incident.
+    9. **Isolate the maintenance run from normal app boot side effects.** Boot warmup itself writes —
+       `warmup.ensure_latest_snapshot` calls `run_scan`, and `_warm_membership_timeline` /
+       `_warm_coverage_snapshot` populate caches — which is exactly how 2026-05-12 got recreated. The
+       destructive clear and regeneration must therefore run with: **one controlled writer**; no boot
+       warmup racing the mutation; no browser QA; no replay lane; no second backend or frontend; no
+       network fetch anywhere in J-11; and no unrelated producer writing while the
+       deletion/regeneration is being reasoned about. Prefer a bounded maintenance command or module
+       calling the existing canonical engine functions over using the UI merely to trigger a rebuild.
+       Add no second computation implementation.
+    10. **Depth gate — fail closed before any destructive write.** The `Depth: full → lean` demotion is
+       unresolved (iters 2, 6, 8). Before any J-11 destructive write executes: **if the goal or spec
+       requests `Depth: full` and the actually dispatched depth is not full, stop before the mutation.**
+       A lean fallback must not launch the parallel replay, start browser QA, start another
+       backend/frontend, execute the destructive reset, or be treated as equivalent to full. If fixing
+       this needs an `incredible_auto_dev` framework change outside this repository, **report that
+       dependency and keep the engine paused rather than bypassing it.**
+    11. **Stage B1 — reconcile the manifest↔ScannerRun referential contract BEFORE any incident run is
+       deleted (hard precondition, owner 2026-08-21).** The schema and the design currently disagree,
+       and the disagreement is load-bearing for this journey. `models.py:820` declares
+       `source_run_id: int = Field(foreign_key="scanner_runs.id", index=True)` and the live DDL carries
+       `FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)`, while the Market Compass design
+       requires manifests to survive snapshot deletion and rebuild. Today that works **only because
+       enforcement is off** — `db._apply_sqlite_pragmas` never issues `PRAGMA foreign_keys=ON`, SQLite
+       defaults it OFF (`PRAGMA foreign_keys` reads `0` on the live DB), and
+       `PRAGMA foreign_key_check(next_session_manifests)` already reports **12 violations**, all on the
+       four incident dates that carry manifests. **The observed 2026-08-05 orphan is therefore NOT
+       proof the schema contract is sound — it is proof the constraint is unenforced.**
+       **J-11 must not rely on SQLite foreign-key enforcement being disabled as part of its safety
+       model.** The intended semantic contract, to be made true by schema/contract rather than by
+       accident:
+       > `source_run_id` is the **immutable historical row-id VALUE recorded when the manifest was
... [diff_bound] docs/goal.md: 289 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
index 52d2d43f..fb560462 100755
--- a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
+++ b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
@@ -602,6 +602,18 @@ case "$_BQA_REQUESTED" in
     echo "[goal-iter-lean] CHAIN_LEAN_PARALLEL_BROWSER_QA='$_BQA_REQUESTED' is not off|replay|full — using off." >&2
     _BQA_MODE="off" ;;
 esac
+# FAIL-CLOSED belt-and-braces: when full depth is a hard requirement, this lean
+# path must never have been reached at all — run-goal.sh pauses AWAITING_FULL_DEPTH
+# before dispatch. If some other caller reaches lean anyway, the parallel
+# browser-QA/replay lane stays OFF regardless of the knob: that lane is exactly
+# what ran against a knowingly damaged database in the incident this guard exists
+# to prevent (it forks service boots + a replay the moment developer.done lands).
+if [[ "$_BQA_MODE" != "off" ]] && declare -F goal_full_depth_required >/dev/null 2>&1 \
+   && goal_full_depth_required "${SPEC:-}"; then
+  echo "[goal-iter-lean] Full depth is REQUIRED for this iteration — forcing CHAIN_LEAN_PARALLEL_BROWSER_QA=off (no replay, no browser QA, no second backend/frontend)." >&2
+  _BQA_MODE="off"
+  _BQA_OFF_REASON="full-depth-required"
+fi
 if [[ "$_BQA_MODE" == "replay" || "$_BQA_MODE" == "full" ]]; then
   _tw_rc=0
   _bqa_tripwire_active || _tw_rc=$?
diff --git a/incredible_auto_dev/scripts/automation/lib/common.sh b/incredible_auto_dev/scripts/automation/lib/common.sh
index 53220802..28d96ae3 100644
--- a/incredible_auto_dev/scripts/automation/lib/common.sh
+++ b/incredible_auto_dev/scripts/automation/lib/common.sh
@@ -1138,6 +1138,36 @@ goal_full_ran_in_window() {
   return 1
 }
 
+# goal_full_depth_required <spec_path>
+# True iff full depth is a HARD REQUIREMENT for this iteration rather than a
+# preference the arbiter may trade away for wall-clock. The arbiter above is a
+# COST ladder: it demotes a spec's `Depth: full` to lean whenever a full already
+# ran in the cadence window ("full-cap"), which is correct for ordinary feature
+# work and WRONG when full depth is the safety control itself — e.g. an
+# iteration whose adversarial audit lane is the thing standing between a
+# destructive database write and an unreviewed mutation. In that case a silent
+# demotion removes the very check the iteration exists to satisfy, and lean depth
+# additionally auto-enables the parallel browser-QA replay lane
+# (goal-iter-lean.sh: CHAIN_LEAN_PARALLEL_BROWSER_QA defaults to `replay`).
+#
+# Two independent ways to declare the requirement — either is sufficient:
+#   * CHAIN_REQUIRE_FULL_DEPTH=true|1  — session-level (set by the operator for
+#     a run whose contract makes full depth mandatory);
+#   * the iteration spec carries a `Depth enforcement: required` line — so a
+#     decomposer can mark a single destructive iteration without pinning the
+#     whole session.
+# Default OFF: with neither present the arbiter keeps its existing behaviour
+# exactly, so ordinary projects and legitimately lean iterations are unaffected.
+goal_full_depth_required() {
+  local spec_path="${1:-}"
+  case "${CHAIN_REQUIRE_FULL_DEPTH:-}" in
+    true|TRUE|1|yes|on) return 0 ;;
+  esac
+  [[ -n "$spec_path" && -f "$spec_path" ]] || return 1
+  grep -qiE '^[[:space:]]*-?[[:space:]]*(\*\*)?Depth[ -]enforcement:?(\*\*)?[[:space:]]*:?[[:space:]]*(\*\*)?required' \
+    "$spec_path" 2>/dev/null
+}
+
 # goal_new_fullstack_journey <spec_path> <journey_history>
 # True iff the spec plans a genuinely NEW full-stack journey: ≥1 concrete
 # Backend bullet AND ≥1 concrete Frontend bullet under IN SCOPE, a non-"none"
diff --git a/incredible_auto_dev/scripts/automation/lib/plain-language.sh b/incredible_auto_dev/scripts/automation/lib/plain-language.sh
index bc359fa1..99684316 100644
--- a/incredible_auto_dev/scripts/automation/lib/plain-language.sh
+++ b/incredible_auto_dev/scripts/automation/lib/plain-language.sh
@@ -30,6 +30,7 @@ AWAITING_PUMP
 AWAITING_GITHUB_AUTH
 AWAITING_DISK
 AWAITING_HOST_GUARD
+AWAITING_FULL_DEPTH
 KEYS
   return 0
 }
@@ -112,6 +113,11 @@ explain_goal_status() {
       echo "  The chain paused because this computer's hardware protection is not in place — it never builds unprotected."
       echo "  Follow the reason printed above (project-extensions/host-guard/README.md), then resume."
       ;;
+    AWAITING_FULL_DEPTH)
+      echo "  The chain paused because this step required its full, deeper review pass and could only have run a shorter one."
+      echo "  It stopped instead of quietly doing less checking — nothing was built or changed."
+      echo "  Follow the reason printed above, then resume."
+      ;;
   esac
   echo "  Read more: ${PLAIN_LANG_GUIDE}  (what each status and verdict means)"
   if [[ -n "$_sid" && -n "$_root" && -f "$_root/reports/goal-session-${_sid}-index.html" ]]; then
diff --git a/incredible_auto_dev/scripts/automation/run-evals.sh b/incredible_auto_dev/scripts/automation/run-evals.sh
index 55a74b0d..2f77662b 100755
--- a/incredible_auto_dev/scripts/automation/run-evals.sh
+++ b/incredible_auto_dev/scripts/automation/run-evals.sh
@@ -184,7 +184,7 @@ fi
 
 # ── 2c. Standalone unit-test scripts (API-free by design) ────────────────────
 _log "2c. tests/automation unit tests"
-for _t in tests/automation/test-escalation-warn.sh tests/automation/test-quota-retry.sh tests/automation/test-goal-inline-tail.sh tests/automation/test-install-gate.sh tests/automation/test-goal-checkpoints.sh tests/automation/test-goal-async-tail.sh tests/automation/test-intent-checkpoint.sh tests/automation/test-doc-drift.sh tests/automation/test-github-preflight.sh tests/automation/test-tmp-cleanup.sh tests/automation/test-goal-retro.sh tests/automation/test-benchmark-runner.sh tests/automation/test-goal-parallel-bqa.sh tests/automation/test-project-template-slice.sh tests/automation/test-phase-telemetry.sh tests/automation/test-testplan-skip.sh tests/automation/test-summary-dedupe.sh tests/automation/test-depth-cadence.sh tests/automation/test-depth-arbiter.sh tests/automation/test-goal-context-slice.sh tests/automation/test-golden-autoderive.sh tests/automation/test-ui-combined.sh tests/automation/test-audit-rerun-cap.sh tests/automation/test-review-packet.sh tests/automation/test-replay-lane.sh tests/automation/test-replay-lane-full.sh tests/automation/test-browser-infra-makeup.sh tests/automation/test-doctor.sh tests/automation/test-engine-lock.sh tests/automation/test-pump-liveness.sh tests/automation/test-goal-iteration-state.sh tests/automation/test-plain-language.sh tests/automation/test-zero-change-guard.sh tests/automation/test-evidence-depth.sh tests/automation/test-closure-gate.sh tests/automation/test-iter-budget.sh tests/automation/test-host-guard.sh tests/automation/test-host-guard-browser.sh tests/automation/test-reset-forensics.sh; do
+for _t in tests/automation/test-escalation-warn.sh tests/automation/test-quota-retry.sh tests/automation/test-goal-inline-tail.sh tests/automation/test-install-gate.sh tests/automation/test-goal-checkpoints.sh tests/automation/test-goal-async-tail.sh tests/automation/test-intent-checkpoint.sh tests/automation/test-doc-drift.sh tests/automation/test-github-preflight.sh tests/automation/test-tmp-cleanup.sh tests/automation/test-goal-retro.sh tests/automation/test-benchmark-runner.sh tests/automation/test-goal-parallel-bqa.sh tests/automation/test-project-template-slice.sh tests/automation/test-phase-telemetry.sh tests/automation/test-testplan-skip.sh tests/automation/test-summary-dedupe.sh tests/automation/test-depth-cadence.sh tests/automation/test-depth-arbiter.sh tests/automation/test-full-depth-required.sh tests/automation/test-goal-context-slice.sh tests/automation/test-golden-autoderive.sh tests/automation/test-ui-combined.sh tests/automation/test-audit-rerun-cap.sh tests/automation/test-review-packet.sh tests/automation/test-replay-lane.sh tests/automation/test-replay-lane-full.sh tests/automation/test-browser-infra-makeup.sh tests/automation/test-doctor.sh tests/automation/test-engine-lock.sh tests/automation/test-pump-liveness.sh tests/automation/test-goal-iteration-state.sh tests/automation/test-plain-language.sh tests/automation/test-zero-change-guard.sh tests/automation/test-evidence-depth.sh tests/automation/test-closure-gate.sh tests/automation/test-iter-budget.sh tests/automation/test-host-guard.sh tests/automation/test-host-guard-browser.sh tests/automation/test-reset-forensics.sh; do
   if bash "$_t" >/dev/null 2>&1; then
     _pass "unit: $_t"
   else
diff --git a/incredible_auto_dev/scripts/automation/run-goal.sh b/incredible_auto_dev/scripts/automation/run-goal.sh
index b08582a8..327c4c2c 100755
--- a/incredible_auto_dev/scripts/automation/run-goal.sh
+++ b/incredible_auto_dev/scripts/automation/run-goal.sh
@@ -77,6 +77,14 @@
 #                      budget is exceeded by the concurrently running sessions, or CPU boost was
 #                      re-enabled); fix per the printed reason (docs/host-guard.md,
 #                      project-extensions/host-guard/README.md), then --resume
+#   AWAITING_FULL_DEPTH - an iteration declared full depth a HARD requirement
+#                      (CHAIN_REQUIRE_FULL_DEPTH=true or a spec `Depth enforcement: required`
+#                      line) but the deterministic depth arbiter could only grant lean. The
+#                      engine halts BEFORE dispatch: no developer mutation, no lean parallel
+#                      browser-QA/replay lane, no second backend/frontend, no DB or network
+#                      action, and no depth-dispatched marker is written (so a resume cannot
+#                      inherit a stale lean decision). Widen CHAIN_FULL_CADENCE_CAP, set
+#                      CHAIN_DEPTH_ARBITER=false, or let the cadence window pass — then --resume
 #
 # Quota exhaustion is NOT a halt: claude_with_quota_retry transparently sleeps
 # until the quota resets and resumes.
@@ -1048,6 +1056,52 @@ _host_guard_reset_forensics() {
   hg_event reset_detected "$(printf '{"code":"%s","streak":"%s"}' "$hex" "$streak")"
   return 0
 }
+_full_depth_pause() { # $1 reason, $2 detected_at_step — pause AWAITING_FULL_DEPTH (resumable) and exit
+  # FAIL-CLOSED depth guard. Reached only when full depth is a HARD requirement
+  # (goal_full_depth_required) and the engine was about to run the iteration at
+  # a lesser depth. We halt BEFORE dispatch, so by construction this iteration
+  # performs no developer mutation, forks no lean parallel browser-QA/replay
+  # lane, starts no second backend/frontend, and touches no database or network.
+  # The requirement is recorded as UNMET rather than silently rewritten: the
+  # depth-dispatched marker is NOT written, so a resume cannot inherit a stale
+  # `lean` decision for this iteration.
+  local reason="$1" step="${2:-depth-arbiter}"
+  echo "[run-goal] Full depth is REQUIRED for this iteration but could not be dispatched — pausing (AWAITING_FULL_DEPTH)."
+  echo "[run-goal]   reason: $reason"
+  echo "[run-goal]   no fallback: the iteration did NOT run at lean depth, nothing was dispatched, and no mutation occurred."
+  rm -f "$ITER_DIR/depth-dispatched" 2>/dev/null || true
+  mkdir -p "$ITER_DIR" 2>/dev/null || true
+  printf 'requested=full\nactual=UNMET\nreason=%s\nstep=%s\n' "$reason" "$step" \
+    > "$ITER_DIR/depth-requirement-unmet" 2>/dev/null || true
+  python3 - <<PY
+import json, datetime
+d = json.load(open("$SESSION_JSON"))
+d["status"] = "AWAITING_FULL_DEPTH"
+d["updated_at"] = datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00','Z')
+import os as _os, tempfile as _tf
+_fd, _tmp = _tf.mkstemp(dir=_os.path.dirname("$SESSION_JSON") or ".", suffix=".sjtmp")
+with _os.fdopen(_fd, "w") as _f:
+    json.dump(d, _f, indent=2)
+    _f.write("\n")
+_os.replace(_tmp, "$SESSION_JSON")
+PY
+  record_telemetry_event "halt" "$(printf '{"reason":"AWAITING_FULL_DEPTH","detected_at_step":"%s","demotion_reason":"%s"}' "$step" "$reason")"
+  echo ""
+  echo "Full depth was required but the deterministic arbiter could not grant it."
+  echo "Resolve by one of:"
+  echo "  * let the cadence window pass (the cap is CHAIN_FULL_CADENCE_CAP, default 4), or"
+  echo "  * raise/disable the cap for this run: CHAIN_FULL_CADENCE_CAP=1, or"
+  echo "  * restore the legacy allowlist: CHAIN_DEPTH_ARBITER=false"
+  echo "then resume:"
+  echo "  ./scripts/automation/run-goal.sh --resume --session-id $SESSION_ID"
+  echo "Do NOT clear CHAIN_REQUIRE_FULL_DEPTH to make this pause go away — the"
+  echo "requirement exists because lean depth would skip the lane that gates a"
+  echo "destructive write."
+  explain_goal_status "AWAITING_FULL_DEPTH" "$SESSION_ID" "$REPO_ROOT"
+  echo "════════════════════════════════════════════════════════════════════"
+  exit 0
+}
+
 _host_guard_pause() { # $1 reason, $2 detected_at_step — pause AWAITING_HOST_GUARD (resumable) and exit
   local reason="$1" step="${2:-preflight}"
   echo "[run-goal] Host-guard check failed — pausing (AWAITING_HOST_GUARD)."
@@ -2396,6 +2450,14 @@ Do NOT write code or implement anything. The iteration spec and any blueprint ed
     DEPTH="lean"
   fi
   if [[ "$DEPTH" != "lean" && "$DEPTH" != "full" && "$DEPTH" != "evidence" ]]; then
+    # THIRD demotion site: an unparseable Depth line silently defaults to lean.
+    # Harmless normally, but under a hard full-depth requirement it is the same
+    # silent degradation the guard exists to stop — a malformed spec line must
+    # not be the reason an adversarial audit lane is skipped. (A spec that
+    # legitimately parses as `lean` never reaches here.)
+    if goal_full_depth_required "$ITER_SPEC_PATH"; then
+      _full_depth_pause "unparseable Depth line in $ITER_SPEC_PATH" "depth-parse"
+    fi
     echo "[run-goal] Could not parse Depth (expected 'lean', 'full', or 'evidence') from $ITER_SPEC_PATH. Defaulting to lean." >&2
     DEPTH="lean"
   fi
@@ -2424,7 +2486,34 @@ Do NOT write code or implement anything. The iteration spec and any blueprint ed
       _prev_coh_file="$GOAL_SESSION_DIR_LOCAL/iter-$((CURRENT_ITER - 1))/coherence.md"
       _prev_budget_marker="$GOAL_SESSION_DIR_LOCAL/iter-$((CURRENT_ITER - 1))/budget-breached"
       _arb_decision="" _arb_reason=""
-      if [[ "${PRIOR_VERDICT:-}" == "ESCALATE" || "${PRIOR_VERDICT:-}" == "REGRESSION" ]]; then
+      if goal_full_depth_required "$ITER_SPEC_PATH"; then
+        # ── PRECEDENCE: a hard full-depth requirement outranks COST policy ─────
+        # Everything below this rung is a cost/performance heuristic answering
+        # "is full depth worth the wall-clock here?" — budget-breach, full-cap,
+        # cadence, and the evaluator's lean preference. None of them answers
+        # "can this engine execute full depth?", which is the only question that
+        # may override a safety requirement. When an iteration is hard-required
+        # full (CHAIN_REQUIRE_FULL_DEPTH, or a spec `Depth enforcement: required`
+        # line) the adversarial review/audit lane IS the control standing between
+        # a destructive write and an unreviewed mutation, so cost may not trade
+        # it away. The cost rungs stay fully intact for every ordinary iteration.
+        _arb_decision="full"; _arb_reason="hard-full-required"
+        # Evidence, not behaviour: record which cost rung WOULD have demoted this
+        # iteration, so the budget/cadence signal is preserved in telemetry
+        # rather than silently discarded. Markers on disk are never touched.
+        _overridden=""
+        if [[ -f "$_prev_budget_marker" && "${PRIOR_VERDICT:-}" == "CONTINUE" ]]; then
+          _overridden="budget-breach"
+        elif goal_full_ran_in_window "$GOAL_SESSION_DIR_LOCAL" "$CURRENT_ITER"; then
+          _overridden="full-cap"
+        elif [[ "$PRIOR_DEPTH" == "lean" || "$PRIOR_DEPTH" == "evidence" ]]; then
+          _overridden="evaluator-requested-${PRIOR_DEPTH}"
+        fi
+        if [[ -n "$_overridden" ]]; then
+          echo "[run-goal] Depth arbiter: HARD full-depth requirement overrides the cost rung '$_overridden' (the signal is recorded, not acted on; its marker is preserved)."
+          record_telemetry_event "depth_cost_overridden" "$(jq -cn --arg o "$_overridden" --arg pv "${PRIOR_VERDICT:-}" --arg pd "${PRIOR_DEPTH:-}" '{requirement:"hard-full-required", overridden_cost_rung:$o, prior_verdict:$pv, prior_depth:$pd}' 2>/dev/null || printf '{"requirement":"hard-full-required","overridden_cost_rung":"%s"}' "$_overridden")"
+        fi
+      elif [[ "${PRIOR_VERDICT:-}" == "ESCALATE" || "${PRIOR_VERDICT:-}" == "REGRESSION" ]]; then
         _arb_decision="full"; _arb_reason="prior-verdict-${PRIOR_VERDICT}"
       elif grep -qE '^\*\*Verdict:\*\* COHERENCE-FAIL' "$_prev_coh_file" 2>/dev/null; then
         _arb_decision="full"; _arb_reason="prior-coherence-fail"
@@ -2454,6 +2543,15 @@ Do NOT write code or implement anything. The iteration spec and any blueprint ed
         # to the legacy SPEED-10 allowlist for the trigger check.
         _use_legacy_allowlist=1
       fi
+      if [[ "$_arb_decision" == "lean" ]] && goal_full_depth_required "$ITER_SPEC_PATH"; then
+        # Defence in depth. With the precedence rung above, a hard-required
+        # iteration always resolves to full, so this is unreachable by design —
+        # AWAITING_FULL_DEPTH must mean "the engine cannot execute full depth",
+        # never "the cost ladder preferred lean". It stays as a backstop so a
+        # future edit that reorders or adds a cost rung cannot silently
+        # reintroduce the demotion this guard exists to stop.
+        _full_depth_pause "arbiter-demotion:${_arb_reason}" "depth-arbiter"
+      fi
       if [[ "$_arb_decision" == "lean" ]]; then
         echo "[run-goal] Depth arbiter: spec asked FULL but the deterministic ladder demotes it to LEAN (reason: $_arb_reason; prior verdict: ${PRIOR_VERDICT:-none}; evaluator depth recommendation: ${PRIOR_DEPTH:-none}). Set CHAIN_DEPTH_ARBITER=false to restore the legacy allowlist."
         record_telemetry_event "depth_demoted" "$(jq -cn --arg r "$_arb_reason" --arg pv "${PRIOR_VERDICT:-}" --arg pd "${PRIOR_DEPTH:-}" '{from:"full", to:"lean", reason:$r, prior_verdict:$pv, prior_depth:$pd}' 2>/dev/null || printf '{"from":"full","to":"lean","reason":"%s"}' "$_arb_reason")"
@@ -2588,6 +2686,11 @@ PYEOF
       bash "$SCRIPT_DIR/run-phase.sh" "$ITER_NAME" "${_full_extra_args[@]}" || _exec_rc=$?
       _engine_step_done
     else
+      # SECOND demotion site: an older run-phase.sh without --no-finalize used to
+      # silently fall back to lean here too. Same fail-closed rule applies.
+      if goal_full_depth_required "$ITER_SPEC_PATH"; then
+        _full_depth_pause "run-phase.sh lacks --no-finalize" "full-dispatch"
+      fi
       echo "[run-goal] run-phase.sh does not yet support --no-finalize. Falling back to lean for safety." >&2
       printf 'lean' > "$ITER_DIR/depth-dispatched"
       _engine_step_begin "lean-pipeline"
diff --git a/incredible_auto_dev/tests/automation/test-depth-arbiter.sh b/incredible_auto_dev/tests/automation/test-depth-arbiter.sh
index 678da9a6..c3d61ee0 100644
--- a/incredible_auto_dev/tests/automation/test-depth-arbiter.sh
+++ b/incredible_auto_dev/tests/automation/test-depth-arbiter.sh
@@ -253,7 +253,11 @@ grep -q 'BINDING by default' "$RG" \
 
 # TARGET_JOURNEYS must be parsed BEFORE the arbiter consumes it.
 _tj_line="$(grep -n 'Target journeys:\\\*\\\*' "$RG" | head -1 | cut -d: -f1)"
-_arb_line="$(grep -n 'CHAIN_DEPTH_ARBITER' "$RG" | head -1 | cut -d: -f1)"
+# Anchor on the ladder's actual gate expression, not any mention of the knob:
+# the status-header docs and the AWAITING_FULL_DEPTH pause both name
+# CHAIN_DEPTH_ARBITER in prose (and sit earlier in the file), which would make a
+# bare token grep report a false ordering failure.
+_arb_line="$(grep -n '"${CHAIN_DEPTH_ARBITER:-true}"' "$RG" | head -1 | cut -d: -f1)"
 if [[ -n "$_tj_line" && -n "$_arb_line" && "$_tj_line" -lt "$_arb_line" ]]; then
   assert "wiring: TARGET_JOURNEYS parsed before the arbiter ladder" "pass"
 else
diff --git a/incredible_auto_dev/tests/automation/test-full-depth-required.sh b/incredible_auto_dev/tests/automation/test-full-depth-required.sh
new file mode 100755
index 00000000..cdd219a5
--- /dev/null
+++ b/incredible_auto_dev/tests/automation/test-full-depth-required.sh
@@ -0,0 +1,295 @@
+#!/usr/bin/env bash
+# test-full-depth-required.sh — fail-closed depth guard.
+#
+# THE INCIDENT THIS PREVENTS: run-goal.sh's depth arbiter is a COST ladder. When
+# a full pass already ran inside the cadence window it demotes a spec's explicit
+# `Depth: full` to lean ("full-cap", run-goal.sh) and dispatches goal-iter-lean.sh,
+# which defaults CHAIN_LEAN_PARALLEL_BROWSER_QA to `replay` and forks a browser-QA
+# service boot + replay lane the moment developer.done lands. That is correct for
+# ordinary feature work. It is WRONG when full depth is the safety control itself
+# — it silently removes the adversarial audit lane gating a destructive database
+# write, and starts extra services against a knowingly damaged dataset.
+#
+# Logic under test:
+#   lib/common.sh   goal_full_depth_required <spec_path>
+#                     -> true iff CHAIN_REQUIRE_FULL_DEPTH is truthy OR the spec
+#                        carries a `Depth enforcement: required` line. Default OFF,
+#                        so ordinary projects and genuinely lean iterations are
+#                        untouched.
+#   run-goal.sh     _full_depth_pause  -> AWAITING_FULL_DEPTH before dispatch
+#   goal-iter-lean.sh -> belt-and-braces: replay lane forced off under the requirement
+#
+# Structural assertions are grep/order based on purpose: cases 3-6 ("no mutation",
+# "no replay", "no browser QA", "no second backend") are guaranteed by the guard
+# halting BEFORE any dispatch, so the test proves the ORDERING and the exit rather
+# than booting an engine (which would violate this repo's host-resource rules).
+set -euo pipefail
+
+SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+ENGINE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
+RG="$ENGINE_ROOT/scripts/automation/run-goal.sh"
+LEAN="$ENGINE_ROOT/scripts/automation/goal-iter-lean.sh"
+
+PASS=0
+FAIL=0
+assert() {
+  if [[ "$2" == "pass" ]]; then echo "  PASS  $1"; PASS=$((PASS + 1)); else echo "  FAIL  $1"; FAIL=$((FAIL + 1)); fi
+}
+
+WORK="$(mktemp -d)"
+trap 'rm -rf "$WORK"' EXIT
+
+source "$ENGINE_ROOT/scripts/automation/lib/common.sh"
+unset CHAIN_REQUIRE_FULL_DEPTH || true
+
+SPEC_PLAIN="$WORK/spec-plain.md"
+SPEC_REQ="$WORK/spec-required.md"
+printf -- '- **Depth:** full\n- **Full trigger:** 1\n' > "$SPEC_PLAIN"
+printf -- '- **Depth:** full\n- **Depth enforcement:** required\n' > "$SPEC_REQ"
+
+# ── 1/8. default OFF: ordinary specs and other goals behave exactly as before ──
+if goal_full_depth_required "$SPEC_PLAIN"; then
+  assert "default: a plain 'Depth: full' spec does NOT trigger the guard (arbiter unchanged)" "fail"
+else
+  assert "default: a plain 'Depth: full' spec does NOT trigger the guard (arbiter unchanged)" "pass"
+fi
+if goal_full_depth_required ""; then
+  assert "default: absent spec path does not trigger the guard (fail-open for unrelated goals)" "fail"
+else
+  assert "default: absent spec path does not trigger the guard (fail-open for unrelated goals)" "pass"
+fi
+
+# ── 2. the requirement is detectable both ways ────────────────────────────────
+if goal_full_depth_required "$SPEC_REQ"; then
+  assert "spec marker: 'Depth enforcement: required' triggers the guard" "pass"
+else
+  assert "spec marker: 'Depth enforcement: required' triggers the guard" "fail"
+fi
+if CHAIN_REQUIRE_FULL_DEPTH=true goal_full_depth_required "$SPEC_PLAIN"; then
+  assert "env: CHAIN_REQUIRE_FULL_DEPTH=true triggers the guard session-wide" "pass"
+else
+  assert "env: CHAIN_REQUIRE_FULL_DEPTH=true triggers the guard session-wide" "fail"
+fi
+if CHAIN_REQUIRE_FULL_DEPTH=false goal_full_depth_required "$SPEC_PLAIN"; then
+  assert "env: CHAIN_REQUIRE_FULL_DEPTH=false leaves the arbiter alone" "fail"
+else
+  assert "env: CHAIN_REQUIRE_FULL_DEPTH=false leaves the arbiter alone" "pass"
+fi
+
+# ── wiring: the guard runs at BOTH demotion sites, before dispatch ────────────
+_line() { grep -n "$1" "$2" | head -1 | cut -d: -f1; }
+
+if grep -q 'goal_full_depth_required "$ITER_SPEC_PATH"' "$RG"; then
+  assert "wiring: run-goal.sh consults goal_full_depth_required" "pass"
+else
+  assert "wiring: run-goal.sh consults goal_full_depth_required" "fail"
+fi
+
+# NOTE: `DEPTH="lean"` appears at several unrelated sites (evidence-micro-path
+# remap, parse default). Anchor on the arbiter's OWN substitution — the line
+# immediately after its demotion banner — not the first match in the file.
+_arb_guard="$(_line '_full_depth_pause "arbiter-demotion' "$RG")"
+_arb_banner="$(_line 'the deterministic ladder demotes it to LEAN' "$RG")"
+if [[ -n "$_arb_guard" && -n "$_arb_banner" && "$_arb_guard" -lt "$_arb_banner" ]]; then
+  assert "site 1 (arbiter): the fail-closed guard precedes the arbiter's DEPTH=\"lean\" substitution" "pass"
+else
+  assert "site 1 (arbiter): the fail-closed guard precedes the arbiter's DEPTH=\"lean\" substitution" "fail"
+fi
+
+# ── site 3: an unparseable Depth line must not silently become lean either ────
+_parse_guard="$(_line '_full_depth_pause "unparseable Depth' "$RG")"
+_parse_default="$(_line "Could not parse Depth" "$RG")"
+if [[ -n "$_parse_guard" && -n "$_parse_default" && "$_parse_guard" -lt "$_parse_default" ]]; then
+  assert "site 3 (parse default): the guard precedes the 'Defaulting to lean' fallback" "pass"
+else
+  assert "site 3 (parse default): the guard precedes the 'Defaulting to lean' fallback" "fail"
+fi
+
+_nofin_guard="$(_line '_full_depth_pause "run-phase.sh lacks' "$RG")"
+_nofin_fallback="$(_line 'does not yet support --no-finalize' "$RG")"
+if [[ -n "$_nofin_guard" && -n "$_nofin_fallback" && "$_nofin_guard" -lt "$_nofin_fallback" ]]; then
+  assert "site 2 (--no-finalize): the guard precedes the legacy lean fallback" "pass"
+else
+  assert "site 2 (--no-finalize): the guard precedes the legacy lean fallback" "fail"
+fi
+
+# ── 3-6. the halt happens BEFORE any dispatch, so nothing can be launched ─────
+_pause_def="$(_line '_full_depth_pause() {' "$RG")"
+_dispatch="$(_line 'Dispatching FULL pipeline via run-phase.sh' "$RG")"
+if [[ -n "$_arb_guard" && -n "$_dispatch" && "$_arb_guard" -lt "$_dispatch" ]]; then
+  assert "halt ordering: guard fires before ANY pipeline dispatch (no dev mutation, no replay, no QA, no 2nd backend)" "pass"
+else
+  assert "halt ordering: guard fires before ANY pipeline dispatch (no dev mutation, no replay, no QA, no 2nd backend)" "fail"
+fi
+if awk "NR>=$_pause_def && NR<=$((_pause_def + 45))" "$RG" | grep -q '^  exit 0$'; then
+  assert "halt: the pause exits (never falls through to a lean dispatch)" "pass"
+else
+  assert "halt: the pause exits (never falls through to a lean dispatch)" "fail"
+fi
+if awk "NR>=$_pause_def && NR<=$((_pause_def + 45))" "$RG" | grep -qE 'bash .*(goal-iter-lean|run-phase)\.sh'; then
+  assert "halt: the pause body launches no pipeline" "fail"
+else
+  assert "halt: the pause body launches no pipeline" "pass"
+fi
+
+# ── 7. requirement recorded as UNMET, never silently rewritten ────────────────
+if awk "NR>=$_pause_def && NR<=$((_pause_def + 45))" "$RG" | grep -q 'depth-requirement-unmet'; then
+  assert "record: an explicit depth-requirement-unmet marker is written" "pass"
+else
+  assert "record: an explicit depth-requirement-unmet marker is written" "fail"
+fi
+if awk "NR>=$_pause_def && NR<=$((_pause_def + 45))" "$RG" | grep -q 'AWAITING_FULL_DEPTH'; then
+  assert "record: session status becomes AWAITING_FULL_DEPTH (resumable)" "pass"
+else
+  assert "record: session status becomes AWAITING_FULL_DEPTH (resumable)" "fail"
+fi
+
+# ── 10. a resume cannot inherit a stale lean dispatch decision ────────────────
+if awk "NR>=$_pause_def && NR<=$((_pause_def + 45))" "$RG" | grep -q 'rm -f "$ITER_DIR/depth-dispatched"'; then
+  assert "resume: the pause clears depth-dispatched so a retry cannot inherit stale 'lean'" "pass"
+else
+  assert "resume: the pause clears depth-dispatched so a retry cannot inherit stale 'lean'" "fail"
+fi
+
+# ── 4/9. replay lane: forced off under the requirement, untouched otherwise ───
+if grep -q 'full-depth-required' "$LEAN"; then
+  assert "replay guard: goal-iter-lean.sh forces the parallel browser-QA lane off under the requirement" "pass"
+else
+  assert "replay guard: goal-iter-lean.sh forces the parallel browser-QA lane off under the requirement" "fail"
+fi
+if grep -q '_BQA_REQUESTED="${CHAIN_LEAN_PARALLEL_BROWSER_QA:-replay}"' "$LEAN"; then
+  assert "replay guard: legitimate lean replay default ('replay') is NOT globally disabled" "pass"
+else
+  assert "replay guard: legitimate lean replay default ('replay') is NOT globally disabled" "fail"
+fi
+_bqa_default="$(_line '_BQA_REQUESTED="${CHAIN_LEAN_PARALLEL_BROWSER_QA:-replay}"' "$LEAN")"
+_bqa_guard="$(_line 'full-depth-required' "$LEAN")"
+if [[ -n "$_bqa_guard" && -n "$_bqa_default" && "$_bqa_guard" -gt "$_bqa_default" ]]; then
+  assert "replay guard: the override runs after mode resolution, so it wins" "pass"
+else
+  assert "replay guard: the override runs after mode resolution, so it wins" "fail"
+fi
+
+# ── status registration ──────────────────────────────────────────────────────
+if "$ENGINE_ROOT/scripts/automation/lib/plain-language.sh" >/dev/null 2>&1 || true; then :; fi
+if grep -q 'AWAITING_FULL_DEPTH' "$ENGINE_ROOT/scripts/automation/lib/plain-language.sh"; then
+  assert "status: AWAITING_FULL_DEPTH is registered in the plain-language keys + explainer" "pass"
+else
+  assert "status: AWAITING_FULL_DEPTH is registered in the plain-language keys + explainer" "fail"
+fi
+
+
+# ══════════════════════════════════════════════════════════════════════════════
+# PRECEDENCE: a hard full-depth requirement outranks the COST ladder.
+#
+# These cases EXECUTE the real arbiter text rather than grepping it: the ladder
+# is inline in run-goal.sh, so we slice it out between two stable anchors and
+# eval it in a sandbox with the external predicates stubbed. That proves actual
+# branch behaviour without booting an engine (host-safe, no services, no DB).
+# ══════════════════════════════════════════════════════════════════════════════
+_arb_start="$(grep -n '_arb_decision="" _arb_reason=""' "$RG" | head -1 | cut -d: -f1)"
+_arb_end="$(grep -n 'PRIOR_DEPTH==full: the evaluator itself asked for full' "$RG" | head -1 | cut -d: -f1)"
+_arb_end=$(( _arb_end + 3 ))   # ..through the ladder's closing `fi`
+awk -v s="$_arb_start" -v e="$_arb_end" 'NR>=s && NR<=e' "$RG" > "$WORK/arb-block.sh"
+if bash -n "$WORK/arb-block.sh" 2>/dev/null; then
+  assert "harness: the arbiter ladder slices out as a syntactically complete block" "pass"
+else
+  assert "harness: the arbiter ladder slices out as a syntactically complete block" "fail"
+fi
+
+# run_arb <hard:0|1> <budget_marker:0|1> <full_in_window:0|1> <prior_verdict> <prior_depth>
+# -> echoes "<decision>:<reason>"
+run_arb() {
+  local hard="$1" budget="$2" inwin="$3" pv="$4" pd="$5"
+  (
+    set +e
+    PRIOR_VERDICT="$pv"; PRIOR_DEPTH="$pd"
+    CURRENT_ITER=8; LEAN_STREAK=0
+    GOAL_SESSION_DIR_LOCAL="$WORK/sess"; JOURNEY_HISTORY="$WORK/jh.json"
+    ITER_SPEC_PATH="$WORK/spec.md"; _budget_demoted=""; _use_legacy_allowlist=""
+    mkdir -p "$WORK/sess/iter-7"
+    _prev_coh_file="$WORK/sess/iter-7/coherence.md"
+    _prev_budget_marker="$WORK/sess/iter-7/budget-breached"
+    rm -f "$_prev_budget_marker"; [[ "$budget" == 1 ]] && : > "$_prev_budget_marker"
+    printf -- '- **Depth:** full\n- **Full trigger:** 1\n' > "$ITER_SPEC_PATH"
+    [[ "$hard" == 1 ]] && printf -- '- **Depth enforcement:** required\n' >> "$ITER_SPEC_PATH"
+    goal_full_ran_in_window() { [[ "$inwin" == 1 ]]; }
+    goal_cadence_forces_full() { return 1; }
+    goal_new_fullstack_journey() { return 1; }
+    record_telemetry_event() { :; }
+    # shellcheck disable=SC1090
+    . "$WORK/arb-block.sh" >/dev/null 2>&1
+    printf '%s:%s' "$_arb_decision" "$_arb_reason"
+  )
+}
+
+# 1. ordinary full + budget-breach -> still demoted to lean (cost policy intact)
+r="$(run_arb 0 1 0 CONTINUE full)"
+[[ "$r" == "lean:budget-breach" ]] \
+  && assert "ordinary: Depth full + budget-breach -> lean (cost arbiter unchanged)" "pass" \
+  || assert "ordinary: Depth full + budget-breach -> lean (got '$r')" "fail"
+
+# 2. hard-required + budget-breach -> stays FULL
+r="$(run_arb 1 1 0 CONTINUE full)"
+[[ "$r" == "full:hard-full-required" ]] \
+  && assert "precedence: hard-required + budget-breach -> FULL" "pass" \
+  || assert "precedence: hard-required + budget-breach -> FULL (got '$r')" "fail"
+
+# 3. hard-required + full-cap -> stays FULL
+r="$(run_arb 1 0 1 CONTINUE full)"
+[[ "$r" == "full:hard-full-required" ]] \
+  && assert "precedence: hard-required + full-cap -> FULL" "pass" \
+  || assert "precedence: hard-required + full-cap -> FULL (got '$r')" "fail"
+
+# 4. hard-required + evaluator recommends lean -> stays FULL
+r="$(run_arb 1 0 0 CONTINUE lean)"
+[[ "$r" == "full:hard-full-required" ]] \
+  && assert "precedence: hard-required + evaluator-recommends-lean -> FULL" "pass" \
+  || assert "precedence: hard-required + evaluator-recommends-lean -> FULL (got '$r')" "fail"
+
+# 9. ordinary full-cap and evaluator-lean demotions still fire for normal iters
+r="$(run_arb 0 0 1 CONTINUE full)"
+[[ "$r" == "lean:full-cap" ]] \
+  && assert "ordinary: Depth full + full-cap -> lean (cost arbiter unchanged)" "pass" \
+  || assert "ordinary: Depth full + full-cap -> lean (got '$r')" "fail"
+r="$(run_arb 0 0 0 CONTINUE lean)"
+[[ "$r" == "lean:evaluator-requested-lean" ]] \
+  && assert "ordinary: Depth full + evaluator-lean -> lean (cost arbiter unchanged)" "pass" \
+  || assert "ordinary: Depth full + evaluator-lean -> lean (got '$r')" "fail"
+
+# sanctioned fulls still win for ordinary iterations
+r="$(run_arb 0 1 1 ESCALATE lean)"
+[[ "$r" == "full:prior-verdict-ESCALATE" ]] \
+  && assert "ordinary: prior ESCALATE still grants full ahead of cost rungs" "pass" \
+  || assert "ordinary: prior ESCALATE still grants full ahead of cost rungs (got '$r')" "fail"
+
+# 6. AWAITING_FULL_DEPTH is no longer reachable from a COST demotion
+r="$(run_arb 1 1 1 CONTINUE lean)"
+[[ "$r" == full:* ]] \
+  && assert "no cost-driven pause: hard-required never resolves lean, so the arbiter cannot pause on cost" "pass" \
+  || assert "no cost-driven pause: hard-required never resolves lean (got '$r')" "fail"
+
+# 5/8. genuine INABILITY still pauses: the --no-finalize and unparseable-depth
+# guards are capability failures, not cost policy, and remain wired.
+if grep -q '_full_depth_pause "run-phase.sh lacks --no-finalize"' "$RG" \
+   && grep -q '_full_depth_pause "unparseable Depth' "$RG"; then
+  assert "genuine inability: capability guards (--no-finalize, unparseable depth) still pause" "pass"
+else
+  assert "genuine inability: capability guards (--no-finalize, unparseable depth) still pause" "fail"
+fi
+
+# 7. the historical budget marker is read, never written/removed by the arbiter
+if grep -qE '(rm|mv|:) *> *"\$_prev_budget_marker"' "$RG"; then
+  assert "evidence: arbiter never deletes/overwrites the budget-breached marker" "fail"
+else
+  assert "evidence: arbiter never deletes/overwrites the budget-breached marker" "pass"
+fi
+if grep -q 'depth_cost_overridden' "$RG"; then
+  assert "evidence: the overridden cost rung is recorded in telemetry" "pass"
+else
+  assert "evidence: the overridden cost rung is recorded in telemetry" "fail"
+fi
+
+echo ""
+echo "  ${PASS} passed, ${FAIL} failed"
+[[ "$FAIL" -eq 0 ]]
```
