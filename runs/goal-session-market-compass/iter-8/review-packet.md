# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 4. Shown in full: 2.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/j10_recovery.py` (451 lines not shown)
- `apps/backend/tests/test_j10_recovery.py` (415 lines not shown)

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
```

## Excluded-path stat (dependency/lockfile visibility)

 .../state/assumptions.md                           | 71 ++++++++++++++++++++++
 runs/goal-session-market-compass/telemetry.jsonl   |  7 +++
 runs/goal-session-market-compass/trace/.next-step  |  2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |  1 +
 4 files changed, 80 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
