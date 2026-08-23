# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

```diff
diff --git a/apps/backend/app/data_providers/base.py b/apps/backend/app/data_providers/base.py
index 0e1e714b..5e083f51 100644
--- a/apps/backend/app/data_providers/base.py
+++ b/apps/backend/app/data_providers/base.py
@@ -10,7 +10,7 @@ from __future__ import annotations
 from abc import ABC, abstractmethod
 from dataclasses import dataclass
 from datetime import date as date_cls
-from typing import Optional, Sequence
+from typing import ClassVar, Optional, Sequence
 
 
 class ProviderUnavailableError(Exception):
@@ -40,6 +40,16 @@ class Bar:
 
 
 class PriceProvider(ABC):
+    # goal-market-compass iter-9 (J-10 gap #2, audit B5): an OPTIONAL provider-identity label — `None`
+    # for every provider that doesn't declare one (no behavior change for any pre-existing subclass).
+    # A subclass that names a real, distinct vendor SHOULD set this to that vendor's catalog id (e.g.
+    # `YahooProvider.source = "yahoo"`) so a caller comparing two provider INSTANCES can tell whether
+    # they are the same vendor without importing every concrete provider class. This is the minimal,
+    # non-invasive field `app.engine.j10_recovery.run_gated_recovery`'s `fetch_provider`/
+    # `convention_provider` mismatch guard reads (`getattr(provider, "source", None)`) — added ONLY for
+    # that guard; it does not change `get_daily`'s contract or any other caller.
+    source: ClassVar[Optional[str]] = None
+
     @abstractmethod
     def get_daily(
         self,
diff --git a/apps/backend/app/data_providers/stooq_provider.py b/apps/backend/app/data_providers/stooq_provider.py
index bbd25a27..04e6879f 100644
--- a/apps/backend/app/data_providers/stooq_provider.py
+++ b/apps/backend/app/data_providers/stooq_provider.py
@@ -40,6 +40,10 @@ def to_stooq_symbol(symbol: str) -> str:
 
 
 class StooqProvider(PriceProvider):
+    # goal-market-compass iter-9 (J-10 gap #2): the provider-identity label `run_gated_recovery`'s
+    # fetch_provider/convention_provider mismatch guard compares (`base.PriceProvider.source`).
+    source = "stooq"
+
     def __init__(
         self,
         *,
diff --git a/apps/backend/app/data_providers/yahoo_provider.py b/apps/backend/app/data_providers/yahoo_provider.py
index 4311498e..71761002 100644
--- a/apps/backend/app/data_providers/yahoo_provider.py
+++ b/apps/backend/app/data_providers/yahoo_provider.py
@@ -64,6 +64,10 @@ QUOTE_BATCH = 40
 
 
 class YahooProvider(PriceProvider):
+    # goal-market-compass iter-9 (J-10 gap #2): the provider-identity label `run_gated_recovery`'s
+    # fetch_provider/convention_provider mismatch guard compares (`base.PriceProvider.source`).
+    source = "yahoo"
+
     def __init__(self, *, client: Optional[httpx.Client] = None, timeout: float = HTTP_TIMEOUT_SECONDS):
         self._client = client
         self._timeout = timeout
diff --git a/apps/backend/app/engine/j10_recovery.py b/apps/backend/app/engine/j10_recovery.py
index 23e6cfdb..1002a975 100644
--- a/apps/backend/app/engine/j10_recovery.py
+++ b/apps/backend/app/engine/j10_recovery.py
@@ -735,7 +735,15 @@ def run_bounded_recovery_fetch(
     a prior partial attempt is excluded even if the caller's list still names it). `None` (the
     default) preserves the exact original behavior — every pre-iter-8 caller/test is unaffected. This
     is how `run_gated_recovery` restricts the real fetch to only the symbols that passed the per-
-    symbol convention gate, without a second write/request path."""
+    symbol convention gate, without a second write/request path.
+
+    iter-9 (J-10 gap #3 / audit B6): EVERY requested symbol must already carry a recorded passing
+    bridge factor — i.e. `provider` must be a `_BridgeApplyingProvider` built from a passing verdict
+    for that symbol, or the whole call raises `RecoveryScopeError` before any network call. A raw/
+    unwrapped provider (including the `provider=None` catalog-resolved default) has zero recorded
+    factors, so it can no longer insert anything for a recovery-scope symbol. The only legitimate way
+    to reach this function with a real recovery-scope request is through `run_gated_recovery` /
+    `run_gated_population_recovery`, which always supply a `_BridgeApplyingProvider`."""
     missing = still_missing_symbols(session)
     target = sorted(set(symbols) & set(missing)) if symbols is not None else missing
     if not target:
@@ -743,6 +751,24 @@ def run_bounded_recovery_fetch(
     validate_recovery_scope(
         start=RECOVERY_START, end=RECOVERY_END, symbols=target, source=RECOVERY_SOURCE
     )
+    # iter-9 (J-10 gap #3 / audit B6): close the un-gated back door. `provider` only ever carries a
+    # RECORDED passing bridge factor for a symbol when it is a `_BridgeApplyingProvider` built from a
+    # passing convention-check verdict (the ONLY place this module constructs one — inside
+    # `_run_gated_recovery_core`, run_gated_recovery's/run_gated_population_recovery's shared body). Any
+    # other provider (a raw client, or none at all) has recorded bridge factors for ZERO symbols, so
+    # EVERY requested symbol is "ungated" and the whole request is refused before any network call —
+    # this function can no longer insert an untransformed row for a recovery-scope symbol that never
+    # passed the per-symbol path-agreement + stable-bridge gate, structurally, not by caller discipline.
+    gated_factors = provider._bridge_factors if isinstance(provider, _BridgeApplyingProvider) else {}
+    ungated = sorted(s for s in target if s not in gated_factors)
+    if ungated:
+        raise RecoveryScopeError(
+            f"J-10 recovery: refusing {len(ungated)} symbol(s) with no passing bridge factor on "
+            f"record: {ungated[:10]}{' ...' if len(ungated) > 10 else ''} -- run_bounded_recovery_fetch "
+            f"only ever inserts a symbol that reached verdict=='agree' through the per-symbol convention "
+            f"gate (call run_gated_recovery / run_gated_population_recovery instead of this function "
+            f"directly for a real recovery-scope fetch)"
+        )
     data_manager.validate_job_request(
         "fetch", RECOVERY_START, RECOVERY_END, config, source=RECOVERY_SOURCE, api_key=api_key,
     )
@@ -828,47 +854,73 @@ class GatedRecoveryOutcome:
     stopped_reason: Optional[str] = None
 
 
-def run_gated_recovery(
+def _check_fetch_provider_source_matches(
+    convention_provider: PriceProvider, fetch_provider: Optional[PriceProvider]
+) -> None:
+    """iter-9 (J-10 gap #2 / audit B5): closes B2's "one series, end to end" rule at the CALL BOUNDARY,
+    not just by docstring. `fetch_provider is None` (the default -> `convention_provider` itself) is
+    always fine — trivially the same object, so this check is skipped entirely (an omitted
+    `fetch_provider` "must keep working exactly as today", per goal.md). When a caller DOES supply a
+    distinct `fetch_provider`, its `.source` (see `base.PriceProvider.source`) must equal
+    `convention_provider`'s — a mismatch means the bridge would be CALIBRATED on one vendor's series
+    and APPLIED to fetch a DIFFERENT vendor's series, silently re-introducing the exact crossover risk
+    B2 closed for the method/field axis. Neither provider's `get_daily` is ever called by this check
+    (a pure attribute comparison) — the refusal happens before any convention check or fetch."""
+    if fetch_provider is None:
+        return
+    convention_source = getattr(convention_provider, "source", None)
+    fetch_source = getattr(fetch_provider, "source", None)
+    if fetch_source != convention_source:
+        raise RecoveryScopeError(
+            f"J-10 recovery: fetch_provider source {fetch_source!r} does not match "
+            f"convention_provider source {convention_source!r} — refusing before any convention check "
+            f"or fetch (B2: calibration and restoration must read the same vendor's series, end to end)"
+        )
+
+
+def _run_gated_recovery_core(
     session: Session,
     engine: Engine,
     config: Config,
     *,
     convention_provider: PriceProvider,
-    fetch_provider: Optional[PriceProvider] = None,
-    api_key: Optional[str] = None,
-    evidence_path: Optional[Path] = None,
+    fetch_provider: Optional[PriceProvider],
+    api_key: Optional[str],
+    evidence_path: Path,
+    sample_symbols: Optional[Sequence[str]],
 ) -> GatedRecoveryOutcome:
-    """The ONE J-10 retry entry point (steps 2a->3), iter-8 REDESIGN. B5: the ONLY parameters this
-    production entry point accepts are provider OBJECTS, the optional `api_key`, and the optional
-    evidence-artifact write location — no tolerance, dispersion-bound, sample, or window override
-    exists here at all (contrast the iter-7 signature, which exposed all four). `check_adjustment_
-    convention_per_symbol` is always called with its own default (module-constant) sample and a LIVE
-    DB-derived window — there is no code path by which a caller loosens either without a source diff
-    to review.
+    """The shared body of BOTH J-10 production entry points (`run_gated_recovery`'s frozen 20-name
+    methodology sample, `run_gated_population_recovery`'s live recovery-population remainder) — the ONE
+    place the causal ordering gate (check -> persist evidence -> collect passing -> fetch -> backfill),
+    the B2 provider-mismatch guard, and the mandatory evidence artifact are implemented, so both entry
+    points enforce every closed gap identically instead of duplicating the logic (and risking one
+    getting the fix and the other not). `sample_symbols=None` defers to `check_adjustment_convention_
+    per_symbol`'s own default (the frozen `CONVENTION_CHECK_SAMPLE_SYMBOLS`); a caller-supplied sequence
+    (the population pass) overrides it — this function applies NO threshold/dispersion/window override
+    either way, exactly like the iter-8 production entry point it replaces.
 
     Order of operations, structurally enforced (not by convention):
-      1. Run the per-symbol check against `convention_provider` (read-only, in-memory).
-      2. If `evidence_path` is given, persist the FULL per-pair evidence (B3) — BEFORE a single
-         verdict is used for anything else (TC-7). The real driver ALWAYS passes a real path; most
-         tests omit it (no filesystem side effect) unless they specifically test persistence.
-      3. Collect symbols with verdict=="agree" and their bridge factors. Zero -> stop, `stopped_reason`
-         set, no fetch/backfill call of any kind (TC-10) — the fetch/backfill calls below sit
-         textually inside the `if not passing` branch's fallthrough, so no code path below the
-         verdict check can reach them when nothing passed.
-      4. Otherwise: fetch ONLY the passing symbols (intersected with what's still actually missing,
-         for idempotency) through a `_BridgeApplyingProvider` wrapping `fetch_provider` (defaulting to
-         `convention_provider` itself — the SAME instance/method used for calibration, reinforcing
-         B2), via the EXISTING `run_bounded_recovery_fetch` -> `data_manager.run_data_job` write path
-         (no second insert path), then run the existing backfill.
-
-    `fetch_provider` defaulting to `convention_provider` when omitted is a DELIBERATE change from the
-    iter-7 signature (there, omitting it meant "let data_manager resolve its own catalog provider" —
-    that is no longer possible here, because the bridge transform must wrap a CONCRETE provider
-    instance). Every current caller passes both explicitly anyway."""
-    check = check_adjustment_convention_per_symbol(session, provider=convention_provider)
-    if evidence_path is not None:
-        evidence_path.parent.mkdir(parents=True, exist_ok=True)
-        evidence_path.write_text(json.dumps(convention_evidence_to_dict(check), indent=2, sort_keys=True))
+      1. Refuse a `fetch_provider`/`convention_provider` source mismatch (B2/B5, iter-9) — before
+         anything else runs.
+      2. Run the per-symbol check against `convention_provider` (read-only, in-memory) over
+         `sample_symbols`.
+      3. Persist the FULL per-pair evidence (B3) to the now-MANDATORY `evidence_path` — BEFORE a single
+         verdict is used for anything else (TC-7/iter-9 gap #1).
+      4. Collect symbols with verdict=="agree" and their bridge factors. Zero -> stop, `stopped_reason`
+         set, no fetch/backfill call of any kind (TC-10).
+      5. Otherwise: fetch ONLY the passing symbols (intersected with what's still actually missing, for
+         idempotency) through a `_BridgeApplyingProvider` wrapping `fetch_provider` (defaulting to
+         `convention_provider` itself), via the EXISTING `run_bounded_recovery_fetch` ->
+         `data_manager.run_data_job` write path (no second insert path), then run the existing
+         backfill."""
+    _check_fetch_provider_source_matches(convention_provider, fetch_provider)
+    check = check_adjustment_convention_per_symbol(
+        session, provider=convention_provider, sample_symbols=sample_symbols
+    )
+    # iter-9 (gap #1 / audit B4): evidence_path is now a REQUIRED Path (see both public signatures
+    # below) — persistence is no longer conditional on the caller remembering to pass one.
+    evidence_path.parent.mkdir(parents=True, exist_ok=True)
+    evidence_path.write_text(json.dumps(convention_evidence_to_dict(check), indent=2, sort_keys=True))
 
     passing = {v.symbol: v.bridge_factor for v in check.verdicts if v.verdict == "agree"}
     if not passing:
@@ -885,3 +937,76 @@ def run_gated_recovery(
     )
     backfill = run_bounded_recovery_backfill(session, engine, config)
     return GatedRecoveryOutcome(convention_check=check, fetch=fetch, backfill=backfill)
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
+    evidence_path: Path,
+) -> GatedRecoveryOutcome:
+    """The J-10 METHODOLOGY-VALIDATION entry point (steps 2a->3), iter-8 REDESIGN, iter-9 hardened.
+    Always runs the per-symbol gate over the FROZEN `CONVENTION_CHECK_SAMPLE_SYMBOLS` (20 names) — never
+    the recovery population; that is `run_gated_population_recovery`'s job, a fully distinct axis
+    (goal.md step 2b's binding invariant: the methodology-validation sample is never re-run/re-widened
+    as a validation exercise). B5: the ONLY parameters this production entry point accepts are provider
+    OBJECTS, the optional `api_key`, and the (now mandatory, iter-9 gap #1) evidence-artifact write
+    location — no tolerance, dispersion-bound, sample, or window override exists here at all (contrast
+    the iter-7 signature, which exposed all four).
+
+    iter-9: `evidence_path` lost its default — omitting it is refused by Python's own argument binding
+    before this function's body (and therefore the convention check) ever executes (TC-6/gap #1). A
+    `fetch_provider` whose `.source` does not match `convention_provider`'s is refused before any
+    convention check or fetch (TC-7/gap #2, see `_check_fetch_provider_source_matches`).
+    `fetch_provider` defaulting to `convention_provider` when omitted is unchanged from iter-8 (there is
+    no code path by which `run_bounded_recovery_fetch` — see its own iter-9 docstring update — can be
+    reached with an ungated symbol either, gap #3)."""
+    return _run_gated_recovery_core(
+        session, engine, config,
+        convention_provider=convention_provider, fetch_provider=fetch_provider,
+        api_key=api_key, evidence_path=evidence_path, sample_symbols=None,
+    )
+
+
+def run_gated_population_recovery(
+    session: Session,
+    engine: Engine,
+    config: Config,
+    *,
+    convention_provider: PriceProvider,
+    fetch_provider: Optional[PriceProvider] = None,
+    api_key: Optional[str] = None,
+    evidence_path: Path,
+) -> GatedRecoveryOutcome:
+    """iter-9's NEW J-10 POPULATION entry point — runs the SAME fixed per-symbol gate
+    (`_compute_symbol_verdict`, the SAME `PATH_AGREEMENT_TOLERANCE`/`BRIDGE_DISPERSION_BOUND`/
+    `MIN_COMPARABLE_PAIRS_PER_SYMBOL`, the SAME live window derivation) as `run_gated_recovery`, but
+    over the LIVE recovery-population remainder (`still_missing_symbols()`) instead of the frozen
+    20-name `CONVENTION_CHECK_SAMPLE_SYMBOLS` — a fully distinct axis from that methodology-validation
+    sample, which this function never reads, widens, or re-derives (goal.md step 2b's binding
+    invariant: "the prohibition on widening or redrawing the methodology-validation sample does not
+    restrict execution over the already frozen J-10 recovery population").
+
+    Idempotent by construction: `still_missing_symbols()` is computed FRESH at call time (BEFORE the
+    convention check runs), so a symbol already fully restored (the 20 from iteration 8, or any
+    population member a prior population-pass invocation already restored) is excluded from the SAMPLE
+    itself — never re-calibrated, never re-fetched, never re-evaluated (TC-4/TC-9). Every symbol in the
+    computed sample gets exactly one recorded verdict (TC-1); an `agree` verdict is restored (bridge-
+    transformed, both recovery-date bars, idempotently); a `mismatch`/`inconclusive` verdict yields zero
+    rows and its `SymbolConventionVerdict.reason` is the "requested but not restored" explanation
+    (TC-3) — the caller (the committed driver script) reads `outcome.convention_check.verdicts` to build
+    that list; this function persists the raw evidence, not a human-facing summary.
+
+    Same B2/B5/B6 guarantees as `run_gated_recovery` (delegates to the SAME `_run_gated_recovery_core`):
+    `evidence_path` is mandatory, a `fetch_provider` source mismatch is refused before any work, and
+    `run_bounded_recovery_fetch` itself refuses any symbol without a recorded passing bridge factor."""
+    population = still_missing_symbols(session)
+    return _run_gated_recovery_core(
+        session, engine, config,
+        convention_provider=convention_provider, fetch_provider=fetch_provider,
+        api_key=api_key, evidence_path=evidence_path, sample_symbols=population,
+    )
diff --git a/apps/backend/tests/test_j10_recovery.py b/apps/backend/tests/test_j10_recovery.py
index 53634e91..ba157211 100644
--- a/apps/backend/tests/test_j10_recovery.py
+++ b/apps/backend/tests/test_j10_recovery.py
@@ -50,6 +50,7 @@ from app.engine.j10_recovery import (
     convention_evidence_to_dict,
     run_bounded_recovery_backfill,
     run_bounded_recovery_fetch,
+    run_gated_population_recovery,
     run_gated_recovery,
     still_missing_symbols,
     validate_recovery_scope,
@@ -209,14 +210,19 @@ def test_fetch_restores_only_the_missing_rows_and_never_touches_survivors(tmp_pa
         ))
         session.commit()
 
-    provider = _RecordingProvider()
+    inner = _RecordingProvider()
+    # iter-9 (gap #3): run_bounded_recovery_fetch now refuses any symbol with no recorded passing
+    # bridge factor -- wrap the recording provider in a _BridgeApplyingProvider with factor 1.0 (a
+    # no-op transform) so this test's own fetch-mechanics assertions (missing-only, survivor-untouched)
+    # are exercised through the SAME gated path the real driver uses.
+    provider = j10_recovery._BridgeApplyingProvider(inner, {"MSFT": 1.0})
     with Session(engine) as session:
         # iter-7: RECOVERY_SOURCE ("yahoo") is needs_key: false in the config catalog — no api_key needed.
         outcome = run_bounded_recovery_fetch(session, engine, cfg, provider=provider)
 
     assert outcome.already_complete is False
     assert outcome.requested_symbols == ["MSFT"]  # AAPL fully covered — never re-requested
-    assert provider.requested_symbols == ["MSFT"]  # the provider itself was only asked for MSFT
+    assert inner.requested_symbols == ["MSFT"]  # the underlying provider was only asked for MSFT
 
     with Session(engine) as session:
         aapl_start = session.exec(
@@ -248,13 +254,16 @@ def test_fetch_symbols_param_intersects_with_still_missing_for_idempotency(tmp_p
         session.add(DailyPrice(symbol="AAPL", date=RECOVERY_END, open=1, high=1, low=1, close=1.0, volume=1))
         session.commit()
 
-    provider = _RecordingProvider()
+    inner = _RecordingProvider()
+    # iter-9 (gap #3): same gating requirement as the sibling test above -- wrap in a no-op (factor 1.0)
+    # _BridgeApplyingProvider so this idempotency test still exercises the real, now-gated fetch path.
+    provider = j10_recovery._BridgeApplyingProvider(inner, {"AAPL": 1.0, "MSFT": 1.0})
     with Session(engine) as session:
         # caller names BOTH symbols, but AAPL is already fully restored
         outcome = run_bounded_recovery_fetch(session, engine, cfg, provider=provider, symbols=["AAPL", "MSFT"])
 
     assert outcome.requested_symbols == ["MSFT"]
-    assert provider.requested_symbols == ["MSFT"]
+    assert inner.requested_symbols == ["MSFT"]
 
 
 def test_second_invocation_after_full_recovery_is_a_true_zero_work_noop(tmp_path):
@@ -670,7 +679,9 @@ def test_gated_recovery_stops_when_zero_symbols_pass(tmp_path, monkeypatch):
 
     provider = _FakeDailyProvider({"AAPL": {d0: 200.0, d1: 100.0}})  # ratio drifts 1.0 -> 2.0: mismatch
     with Session(engine) as session:
-        outcome = run_gated_recovery(session, engine, cfg, convention_provider=provider)
+        outcome = run_gated_recovery(
+            session, engine, cfg, convention_provider=provider, evidence_path=tmp_path / "evidence.json",
+        )
 
     by_symbol = {v.symbol: v for v in outcome.convention_check.verdicts}
     assert by_symbol["AAPL"].verdict == "mismatch"
@@ -714,7 +725,9 @@ def test_gated_recovery_restores_only_passing_symbols_leaves_failing_ones_missin
         },
     })
     with Session(engine) as session:
-        outcome = run_gated_recovery(session, engine, cfg, convention_provider=provider)
+        outcome = run_gated_recovery(
+            session, engine, cfg, convention_provider=provider, evidence_path=tmp_path / "evidence.json",
+        )
 
     by_symbol = {v.symbol: v for v in outcome.convention_check.verdicts}
     assert by_symbol["AAPL"].verdict == "agree"
@@ -757,11 +770,17 @@ def test_gated_recovery_second_invocation_after_partial_success_only_refetches_m
     all_dates = window + [RECOVERY_START, RECOVERY_END]
     provider = _FakeDailyProvider({"AAPL": {d: 200.0 for d in all_dates}})
     with Session(engine) as session:
-        first = run_gated_recovery(session, engine, cfg, convention_provider=provider)
+        first = run_gated_recovery(
+            session, engine, cfg, convention_provider=provider,
+            evidence_path=tmp_path / "evidence-1.json",
+        )
     assert first.fetch.requested_symbols == ["AAPL"]
 
     with Session(engine) as session:
-        second = run_gated_recovery(session, engine, cfg, convention_provider=provider)
+        second = run_gated_recovery(
+            session, engine, cfg, convention_provider=provider,
+            evidence_path=tmp_path / "evidence-2.json",
+        )
     assert second.fetch.already_complete is True
     assert second.fetch.requested_symbols == []
     # get_daily was called 3 times total: calibration(1), restore(1), calibration(2) -- never restore(2)
@@ -777,3 +796,275 @@ def test_gated_recovery_has_no_threshold_or_scope_override_parameters():
     assert params == {
         "session", "engine", "config", "convention_provider", "fetch_provider", "api_key", "evidence_path",
     }
+
+
+# ==================================================================================================
+# iter-9 gap #1: evidence_path is now REQUIRED on both production entry points -- each test constructs
+# an ACTUAL missing-argument call (the iter-7 lesson: a guard is only proven fail-closed when a test
+# meets the exact degenerate input it will meet in production), not a signature inspection alone.
+# ==================================================================================================
+def test_run_gated_recovery_requires_evidence_path_missing_arg_refused(tmp_path):
+    """TC-6: omitting evidence_path is refused by Python's own keyword-argument binding BEFORE
+    run_gated_recovery's body -- and therefore the convention check or any fetch -- ever executes."""
+    engine = _engine(tmp_path)
+    cfg = _cfg()
+    provider = _NeverCalledProvider()  # fails the test immediately if get_daily is ever reached
+    with Session(engine) as session:
+        with pytest.raises(TypeError, match="evidence_path"):
+            run_gated_recovery(session, engine, cfg, convention_provider=provider)  # type: ignore[call-arg]
+
+
+def test_run_gated_population_recovery_requires_evidence_path_missing_arg_refused(tmp_path):
+    """TC-6, population entry point: the identical missing-argument refusal -- both public functions
+    delegate to the same `_run_gated_recovery_core`, so both must enforce this identically."""
+    engine = _engine(tmp_path)
+    cfg = _cfg()
+    provider = _NeverCalledProvider()
+    with Session(engine) as session:
+        with pytest.raises(TypeError, match="evidence_path"):
+            run_gated_population_recovery(session, engine, cfg, convention_provider=provider)  # type: ignore[call-arg]
+
+
+# ==================================================================================================
+# iter-9 gap #2: the fetch_provider/convention_provider source-mismatch guard (B2/B5 at the call
+# boundary). Pure unit tests on the helper itself (the exact degenerate conditions), plus one
+# integration test proving it is actually wired into run_gated_recovery.
+# ==================================================================================================
+class _YahooLikeProvider(PriceProvider):
+    source = "yahoo"
+
+    def get_daily(self, symbol, start=None, end=None):
+        raise AssertionError(f"get_daily called for {symbol!r} -- never reached by these unit tests")
+
+
+class _StooqLikeProvider(PriceProvider):
+    source = "stooq"
+
+    def get_daily(self, symbol, start=None, end=None):
+        raise AssertionError(f"get_daily called for {symbol!r} -- never reached by these unit tests")
+
+
+def test_check_fetch_provider_source_matches_skips_when_fetch_provider_omitted():
+    """TC-7 regression half: fetch_provider=None (the default -> convention_provider itself) is ALWAYS
+    accepted, regardless of convention_provider's declared source -- 'must keep working exactly as
+    today.'"""
+    j10_recovery._check_fetch_provider_source_matches(_YahooLikeProvider(), None)  # must not raise
+
+
+def test_check_fetch_provider_source_matches_accepts_the_same_source():
+    j10_recovery._check_fetch_provider_source_matches(
+        _YahooLikeProvider(), _YahooLikeProvider()
+    )  # two distinct instances, same declared source -- must not raise
+
+
+def test_check_fetch_provider_source_matches_refuses_a_mismatch():
+    """TC-7: the exact degenerate condition -- a fetch_provider whose source disagrees with
+    convention_provider's."""
+    with pytest.raises(RecoveryScopeError, match="does not match"):
+        j10_recovery._check_fetch_provider_source_matches(_YahooLikeProvider(), _StooqLikeProvider())
+
+
+def test_run_gated_recovery_refuses_a_fetch_provider_source_mismatch_end_to_end(tmp_path):
+    """TC-7, integration: the mismatch guard is actually wired into run_gated_recovery -- refused
+    BEFORE any convention check or fetch runs (neither provider's get_daily is ever called, and no
+    evidence file is written)."""
+    engine = _engine(tmp_path)
+    cfg = _cfg()
+    evidence_path = tmp_path / "evidence.json"
+    with Session(engine) as session:
+        with pytest.raises(RecoveryScopeError, match="does not match"):
+            run_gated_recovery(
+                session, engine, cfg,
+                convention_provider=_YahooLikeProvider(), fetch_provider=_StooqLikeProvider(),
+                evidence_path=evidence_path,
+            )
+    assert not evidence_path.exists()  # refused before evidence was ever persisted
+
+
+# ==================================================================================================
+# iter-9 gap #3 (audit B6): run_bounded_recovery_fetch's un-gated back door -- closed structurally.
+# ==================================================================================================
+def test_run_bounded_recovery_fetch_refuses_a_raw_unwrapped_provider(tmp_path, monkeypatch):
+    """TC-8: a direct call with a raw, non-bridge-gated provider (including provider=None's catalog
+    default) is refused before any network call -- the back door can no longer insert an untransformed
+    row for a symbol that never passed the per-symbol convention gate."""
+    monkeypatch.setattr(j10_recovery, "RECOVERY_SYMBOLS", frozenset({"AAPL"}))
+    engine = _engine(tmp_path)
+    cfg = _cfg()
+    with Session(engine) as session:
+        with pytest.raises(RecoveryScopeError, match="no passing bridge factor"):
+            run_bounded_recovery_fetch(session, engine, cfg, provider=_NeverCalledProvider())
+    with Session(engine) as session:
+        assert session.exec(select(DailyPrice)).all() == []
+
+
+def test_run_bounded_recovery_fetch_refuses_a_bridge_provider_missing_this_symbols_factor(tmp_path, monkeypatch):
+    """TC-8: even a legitimate _BridgeApplyingProvider refuses a REQUESTED symbol it has no recorded
+    factor for -- the check is per-symbol, not merely per-provider-type. AAPL has a passing factor;
+    MSFT (also requested in the same call) does not -- the WHOLE call is refused, zero rows for
+    either symbol (never a partial insert of only the gated ones)."""
+    monkeypatch.setattr(j10_recovery, "RECOVERY_SYMBOLS", frozenset({"AAPL", "MSFT"}))
+    engine = _engine(tmp_path)
+    cfg = _cfg()
+    gated = j10_recovery._BridgeApplyingProvider(_NeverCalledProvider(), {"AAPL": 1.0})
+    with Session(engine) as session:
+        with pytest.raises(RecoveryScopeError, match="no passing bridge factor"):
+            run_bounded_recovery_fetch(session, engine, cfg, provider=gated, symbols=["AAPL", "MSFT"])
+    with Session(engine) as session:
+        assert session.exec(select(DailyPrice)).all() == []
+
+
+# ==================================================================================================
+# run_gated_population_recovery — iter-9: the SAME fixed gate evaluated over the LIVE recovery-
+# population remainder (still_missing_symbols()), a fully distinct axis from the frozen 20-name
+# CONVENTION_CHECK_SAMPLE_SYMBOLS methodology sample (goal.md step 2b's binding invariant).
+# ==================================================================================================
+def test_gated_population_recovery_has_no_threshold_or_scope_override_parameters():
+    """Structural mirror of run_gated_recovery's own signature pin -- the population entry point
+    accepts the identical parameter set; the population is ALWAYS still_missing_symbols(), computed
+    internally -- no sample/threshold override is exposed to any caller."""
+    import inspect
+    params = set(inspect.signature(run_gated_population_recovery).parameters)
+    assert params == {
+        "session", "engine", "config", "convention_provider", "fetch_provider", "api_key", "evidence_path",
+    }
+
+
+def test_population_recovery_samples_still_missing_symbols_never_the_frozen_sample(tmp_path, monkeypatch):
+    """The population entry point's sample is still_missing_symbols(), never
+    CONVENTION_CHECK_SAMPLE_SYMBOLS -- monkeypatch the frozen constant to a symbol OUTSIDE the
+    (also monkeypatched) RECOVERY_SYMBOLS universe; if the population pass ever read it, the provider
+    would be asked for a symbol this test never seeded, proving the axes really are distinct."""
+    monkeypatch.setattr(j10_recovery, "RECOVERY_SYMBOLS", frozenset({"AAPL", "MSFT"}))
+    monkeypatch.setattr(j10_recovery, "CONVENTION_CHECK_SAMPLE_SYMBOLS", ("NVDA",))
+    engine = _engine(tmp_path)
+    cfg = _cfg()
+    window = [date(2026, 8, 6), date(2026, 8, 7), CONVENTION_CHECK_WINDOW_END]
+    with Session(engine) as session:
+        for sym in ("AAPL", "MSFT"):
+            for d in window:
+                session.add(DailyPrice(symbol=sym, date=d, open=1, high=1, low=1, close=200.0, volume=1))
+        session.commit()
+
+    provider = _FakeDailyProvider({"AAPL": {d: 200.0 for d in window}, "MSFT": {d: 200.0 for d in window}})
+    with Session(engine) as session:
+        outcome = run_gated_population_recovery(
+            session, engine, cfg, convention_provider=provider, evidence_path=tmp_path / "evidence.json",
+        )
+    sampled = {v.symbol for v in outcome.convention_check.verdicts}
+    assert sampled == {"AAPL", "MSFT"}
+    # both symbols agree (identical stored/fallback series) and are therefore also fetched -- so each
+    # appears twice (calibration + restoration); the load-bearing assertion is that NVDA (the frozen
+    # methodology sample, monkeypatched here) is never requested at all.
+    assert set(provider.requested_symbols) == {"AAPL", "MSFT"}
+    assert "NVDA" not in provider.requested_symbols
+
+
+def test_population_recovery_restores_agree_leaves_mismatch_and_inconclusive_missing(tmp_path, monkeypatch):
+    """The core population-pass proof: three still-missing symbols get three independent verdicts --
+    AAPL agrees (exact-match series), MSFT mismatches (a drifting ratio), GOOG is inconclusive (zero
+    fallback data at all). Only AAPL is restored; MSFT/GOOG get zero rows and a named, reasoned
+    verdict (the "requested but not restored" record the driver reads). SPY is seeded directly with
+    both recovery dates already present so it is excluded from the population and only serves as the
+    backfill's benchmark."""
+    monkeypatch.setattr(j10_recovery, "RECOVERY_SYMBOLS", frozenset({"AAPL", "MSFT", "GOOG", "SPY"}))
+    engine = _engine(tmp_path)
+    cfg = _cfg()
+    window = [date(2026, 8, 6), date(2026, 8, 7), CONVENTION_CHECK_WINDOW_END]
+    with Session(engine) as session:
+        for sym, price in (("AAPL", 200.0), ("MSFT", 90.0), ("GOOG", 150.0), ("SPY", 500.0)):
+            for d in window:
+                session.add(DailyPrice(symbol=sym, date=d, open=price, high=price, low=price, close=price, volume=1))
+        for d in (RECOVERY_START, RECOVERY_END):
+            session.add(DailyPrice(symbol="SPY", date=d, open=500, high=500, low=500, close=500.0, volume=1))
+        session.commit()
+
+    provider = _FakeDailyProvider({
+        "AAPL": {**{d: 200.0 for d in window}, RECOVERY_START: 201.0, RECOVERY_END: 202.0},  # exact -> agree
+        "MSFT": {window[0]: 45.0, window[1]: 44.0, window[2]: 40.0},  # drifting ratio -> mismatch
+        # GOOG: deliberately absent from the fallback series entirely -> inconclusive (zero pairs)
+    })
+    with Session(engine) as session:
+        outcome = run_gated_population_recovery(
+            session, engine, cfg, convention_provider=provider, evidence_path=tmp_path / "evidence.json",
+        )
+
+    by_symbol = {v.symbol: v for v in outcome.convention_check.verdicts}
+    assert by_symbol["AAPL"].verdict == "agree"
+    assert by_symbol["MSFT"].verdict == "mismatch" and by_symbol["MSFT"].reason
+    assert by_symbol["GOOG"].verdict == "inconclusive" and by_symbol["GOOG"].reason
+    assert outcome.fetch.requested_symbols == ["AAPL"]
+
+    with Session(engine) as session:
+        aapl_rows = session.exec(
+            select(DailyPrice).where(DailyPrice.symbol == "AAPL", DailyPrice.date >= RECOVERY_START)
+        ).all()
+        msft_rows = session.exec(
+            select(DailyPrice).where(DailyPrice.symbol == "MSFT", DailyPrice.date >= RECOVERY_START)
+        ).all()
+        goog_rows = session.exec(
+            select(DailyPrice).where(DailyPrice.symbol == "GOOG", DailyPrice.date >= RECOVERY_START)
+        ).all()
+    assert sorted(r.close for r in aapl_rows) == [201.0, 202.0]
+    assert msft_rows == [] and goog_rows == []
+
+
+def test_population_recovery_excludes_a_symbol_already_fully_restored(tmp_path, monkeypatch):
+    """TC-4 (population form): a symbol with BOTH recovery dates already present is excluded from the
+    population SAMPLE itself -- never re-calibrated, never re-fetched, never re-evaluated. Proves the
+    "already-restored symbols are excluded" guarantee generalizes to any complete population member,
+    not just the frozen 20 from iteration 8."""
+    monkeypatch.setattr(j10_recovery, "RECOVERY_SYMBOLS", frozenset({"AAPL", "MSFT"}))
+    engine = _engine(tmp_path)
+    cfg = _cfg()
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="AAPL", date=RECOVERY_START, open=1, high=1, low=1, close=100.0, volume=1))
+        session.add(DailyPrice(symbol="AAPL", date=RECOVERY_END, open=1, high=1, low=1, close=101.0, volume=1))
+        # MSFT needs at least one stored row on/before CONVENTION_CHECK_WINDOW_END so the LIVE window
+        # (derived from daily_prices, never hardcoded) is non-empty -- otherwise the whole batch would
+        # short-circuit to zero verdicts regardless of which symbols are sampled, and this test would
+        # prove nothing about AAPL's exclusion specifically.
+        session.add(DailyPrice(
+            symbol="MSFT", date=CONVENTION_CHECK_WINDOW_END, open=1, high=1, low=1, close=90.0, volume=1
+        ))
+        session.commit()
+
+    class _FailsIfAaplRequested(PriceProvider):
+        def get_daily(self, symbol, start=None, end=None):
+            if symbol == "AAPL":
+                pytest.fail("AAPL is already fully restored -- must never be re-sampled or re-fetched")
+            return []
+
+    with Session(engine) as session:
+        outcome = run_gated_population_recovery(
+            session, engine, cfg, convention_provider=_FailsIfAaplRequested(),
+            evidence_path=tmp_path / "evidence.json",
+        )
+    sampled = {v.symbol for v in outcome.convention_check.verdicts}
+    assert sampled == {"MSFT"}  # AAPL excluded from the sample entirely
+
+    with Session(engine) as session:
+        aapl_rows = session.exec(select(DailyPrice).where(DailyPrice.symbol == "AAPL")).all()
+    assert sorted(r.close for r in aapl_rows) == [100.0, 101.0]  # byte-unchanged
+
+
+def test_population_recovery_is_a_clean_noop_when_nothing_is_missing(tmp_path, monkeypatch):
+    """TC-9 at the unit level: when still_missing_symbols() is already empty (every RECOVERY_SYMBOLS
+    member fully restored), run_gated_population_recovery stops honestly -- zero convention-check
+    calls, zero fetch, zero backfill -- the idempotent re-run guarantee the real driver relies on."""
+    monkeypatch.setattr(j10_recovery, "RECOVERY_SYMBOLS", frozenset({"AAPL"}))
+    engine = _engine(tmp_path)
+    cfg = _cfg()
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="AAPL", date=RECOVERY_START, open=1, high=1, low=1, close=1, volume=1))
+        session.add(DailyPrice(symbol="AAPL", date=RECOVERY_END, open=1, high=1, low=1, close=1, volume=1))
+        session.commit()
+
+    with Session(engine) as session:
+        outcome = run_gated_population_recovery(
+            session, engine, cfg, convention_provider=_NeverCalledProvider(),
+            evidence_path=tmp_path / "evidence.json",
+        )
+    assert outcome.convention_check.verdicts == ()
+    assert outcome.stopped_reason is not None
+    assert outcome.fetch is None and outcome.backfill is None
diff --git a/apps/backend/tests/test_provider_clients.py b/apps/backend/tests/test_provider_clients.py
index 471ed1dd..caf9bdbd 100644
--- a/apps/backend/tests/test_provider_clients.py
+++ b/apps/backend/tests/test_provider_clients.py
@@ -88,6 +88,20 @@ _YAHOO_OK = {
 }
 
 
+def test_yahoo_and_stooq_declare_distinct_source_labels():
+    """goal-market-compass iter-9 (J-10 gap #2): the minimal, non-invasive provider-identity field
+    `app.engine.j10_recovery.run_gated_recovery`'s fetch_provider/convention_provider mismatch guard
+    reads (`base.PriceProvider.source`). A provider that doesn't declare one (the base class default,
+    and every other concrete provider in this catalog) stays `None` -- unchanged behavior."""
+    from app.data_providers.base import PriceProvider
+    from app.data_providers.stooq_provider import StooqProvider
+
+    assert YahooProvider.source == "yahoo"
+    assert StooqProvider.source == "stooq"
+    assert PriceProvider.source is None
+    assert TiingoProvider.source is None  # a provider that declares no source keeps the base default
+
+
 def test_yahoo_parses_valid_json_into_sorted_bars():
     client = _FakeClient(payload=_YAHOO_OK)
     bars = YahooProvider(client=client).get_daily("AAPL", start=date(2024, 1, 2), end=date(2024, 1, 4))
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-market-compass-iter-9/status.json        | 41 +++++++++++--
 .../goal-session-market-compass/.engine.lock/epoch |  2 +-
 runs/goal-session-market-compass/.engine.lock/pid  |  2 +-
 runs/goal-session-market-compass/engine.pid        |  2 +-
 .../iter-9/goal-slice.md                           | 24 ++++++--
 runs/goal-session-market-compass/session.json      |  3 +-
 .../state/assumptions.md                           | 64 ---------------------
 .../state/assumptions.md.archive.md                | 67 ++++++++++++++++++++++
 runs/goal-session-market-compass/state/lessons.md  | 33 +----------
 .../state/lessons.md.archive.md                    | 43 ++++++++++++++
 runs/goal-session-market-compass/telemetry.jsonl   | 24 ++++++++
 runs/goal-session-market-compass/trace/.next-step  |  2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |  2 +
 .../state/preflight-verdict-history.jsonl          | 10 ++++
 14 files changed, 210 insertions(+), 109 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
