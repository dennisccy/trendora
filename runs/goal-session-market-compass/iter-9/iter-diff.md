# Iteration diff (bounded)

Files changed: 71. Shown in full: 43.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `incredible_auto_dev/docs/improvement-roadmap.md` (96 lines not shown)
- `incredible_auto_dev/scripts/automation/host-guard/reset-forensics.sh` (28 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/common.sh` (338 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh` (77 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/quota-retry.sh` (174 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/replay-lane.sh` (31 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/telemetry.sh` (52 lines not shown)
- `incredible_auto_dev/scripts/automation/qa-phase.sh` (144 lines not shown)
- `incredible_auto_dev/scripts/automation/run-evals.sh` (29 lines not shown)
- `incredible_auto_dev/scripts/automation/run-goal.sh` (383 lines not shown)
- `incredible_auto_dev/scripts/automation/run-judgment-evals.sh` (16 lines not shown)
- `incredible_auto_dev/scripts/automation/run-phase.sh` (54 lines not shown)
- `incredible_auto_dev/scripts/automation/ui-impact-phase.sh` (14 lines not shown)
- `incredible_auto_dev/scripts/automation/ux-regression-phase.sh` (17 lines not shown)
- `incredible_auto_dev/skills/goal-evaluation-methodology.md` (48 lines not shown)
- `incredible_auto_dev/skills/goal-interactive-dispatch.md` (20 lines not shown)
- `incredible_auto_dev/skills/phase-closure-gate.md` (15 lines not shown)
- `incredible_auto_dev/tests/automation/test-closure-gate.sh` (140 lines not shown)
- `incredible_auto_dev/tests/automation/test-doctor.sh` (57 lines not shown)
- `incredible_auto_dev/tests/automation/test-full-depth-required.sh` (365 lines not shown)
- `incredible_auto_dev/tests/automation/test-host-guard-browser.sh` (208 lines not shown)
- `incredible_auto_dev/tests/automation/test-host-guard.sh` (23 lines not shown)
- `incredible_auto_dev/tests/automation/test-maintenance-isolation.sh` (626 lines not shown)
- `incredible_auto_dev/tests/automation/test-output-style.sh` (597 lines not shown)
- `incredible_auto_dev/tests/automation/test-replay-lane.sh` (17 lines not shown)
- `incredible_auto_dev/tests/automation/test-reset-forensics.sh` (116 lines not shown)
- `incredible_auto_dev/tests/automation/test-review-verdict-event.sh` (86 lines not shown)
- `apps/backend/scripts/run_j10_population_recovery.py` (283 lines not shown)

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
diff --git a/docs/goal.md b/docs/goal.md
index a88116b4..8125124e 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -623,12 +623,26 @@ manifest artifact (it must be self-describing and self-caveating).
        same proven-missing row set, same fail-closed guard, same verification, same auto-close.
        Three conditions ride with it:
        - **Provenance-explicit.** Every restored row is recorded as `yahoo`-sourced through the
-         existing per-row/per-run vendor fields — never relabelled, back-dated, or blended into the
-         surrounding `stooq` history. The dataset after recovery is honestly mixed-vendor at exactly
-         two dates, and the handoff and `data_provider_runs` must both say so.
+         existing per-run vendor fields — never relabelled or back-dated.
+         **Factual correction (owner, 2026-08-21 — this bullet previously said the restored rows must
+         not be "blended into the surrounding `stooq` history" and that the dataset becomes "honestly
+         mixed-vendor at exactly two dates". Both were wrong):** the bars *adjacent* to 2026-08-11/12
+         are **not** Stooq's. The committed seed ends **2026-07-01**; every post-seed fetch in
+         `data_provider_runs` is `provider='yahoo'` (34 runs), and the single `stooq` run — id 541 —
+         **failed with 0 symbols**, so Stooq has never written a bar into this database. The correct
+         model is: **through 2026-07-01** the basis is the committed seed / Stooq historical data;
+         **post-seed recent history is Yahoo-sourced**; and **the 2026-08-11/12 recovery is Yahoo-
+         sourced** — i.e. the recovery is vendor-*continuous* with its immediate neighbours, not a
+         two-date mixed-vendor splice. (A broader historical vendor splice may exist at the seed
+         boundary itself; that is a separate, pre-existing question and **J-10 must not expand into
+         repairing or researching it.**) The handoff and `data_provider_runs` must still record the
+         `yahoo` provenance plainly.
        - **Fail closed: precommitted path-agreement + stable multiplicative bridge (owner, 2026-08-20
-         — supersedes the earlier absolute-level tolerance).** Stooq's bars are split/dividend-adjusted
-         (seed manifest: "REAL split/dividend-adjusted EOD OHLCV"). Before inserting anything, the
+         — supersedes the earlier absolute-level tolerance).** The stored historical basis is
+         split/dividend-adjusted (seed manifest: "REAL split/dividend-adjusted EOD OHLCV"); note per
+         the correction above that the *overlap window this gate actually samples* is Yahoo-stored,
+         not Stooq-stored, so the gate compares Yahoo raw close against stored Yahoo raw close and
+         does **not** test cross-vendor equivalence. Before inserting anything, the
          implementation MUST demonstrate agreement using the two-part test below. To make it possible —
          and for no other purpose — a **read-only comparison fetch** of a small overlap window of
          already-surviving trading days (≤ 2026-08-10) for a sample of the proven-missing symbols is
diff --git a/incredible_auto_dev/.claude/agents/goal-decomposer.md b/incredible_auto_dev/.claude/agents/goal-decomposer.md
index b49d78c5..ffaad6f7 100644
--- a/incredible_auto_dev/.claude/agents/goal-decomposer.md
+++ b/incredible_auto_dev/.claude/agents/goal-decomposer.md
@@ -4,8 +4,8 @@ description: Goal-mode iteration planner. Reads docs/goal.md (with Must-have use
 model: claude-sonnet-5
 tools: [Read, Glob, Grep, Bash, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 2.5.0
-last_updated: 2026-07-29
+version: 2.6.0
+last_updated: 2026-08-21
 ---
 
 # Goal Decomposer Agent
@@ -139,6 +139,8 @@ The `Frontend Present:` field is implicit — if any Frontend item is listed, do
 
 Every FULL-depth spec MUST carry the machine-parseable metadata line `Full trigger: <1|2|3|4> — <one-line reason>`, naming which numbered full-depth trigger (see "Picking depth") applies. The evaluator's depth recommendation (inlined in your prompt) is **BINDING by default**: plan the recommended depth unless one of the four escape conditions holds — prior ESCALATE/REGRESSION verdict, prior coherence-audit FAIL, hardening cadence due, or a brand-new full-stack journey (backend AND frontend work with real Data-contract additions for a never-implemented target journey). The engine's deterministic arbiter re-validates a full spec against those same independent signals: a `Full trigger:` line alone does NOT grant full, and an unjustified full spec is demoted to lean.
 
+Two metadata lines exist that you must **NEVER** emit: `Depth enforcement: required` and `Maintenance isolation: required`. They are operator-only engine controls, not planning fields — the first makes full depth a hard requirement the engine will halt on rather than downgrade (`AWAITING_FULL_DEPTH`), the second forbids application-service boot, browser QA and the deterministic replay lane for the whole iteration. A spec you wrote is the one input you also author, so a self-written safety declaration is exactly the governor bypass anti-pattern 25 describes (`.claude/anti-patterns/25-self-justifying-governor-bypass.md`; SPEED-10's `Full trigger:` arm was superseded for the same reason). When you believe an iteration needs either control — a destructive migration, a repair pass on damaged data — say so in **BACKGROUND** in plain prose ("this iteration rewrites persisted rows; it should not run with the app booted") and leave the line to the human, who adds it to the spec or sets `CHAIN_REQUIRE_FULL_DEPTH` / `CHAIN_MAINTENANCE_ISOLATION` for the run.
+
 ## Picking target journeys (priority rubric — apply top-down)
 
 1. **Regressed journeys first.** Anything `regressed` outranks all new work — a shrinking product is worse than a slowly-growing one.
@@ -242,7 +244,7 @@ Always restate the anti-goals from `docs/goal.md` verbatim under Goal Mode Metad
 1. **Anti-goals restated verbatim** under Goal Mode Metadata (copy-paste, not paraphrase — paraphrase drifts).
 2. **Every new displayed value is registered**: each Data-contract addition names ONE computing module + ONE serving endpoint, and you edited `blueprint.md` to match. "None" is written explicitly when true.
 3. **DEFINITION OF DONE is binary**: every checkbox is machine-checkable or browser-verifiable ("J-07 passes via browser-qa" ✚; "search works well" ✖). If you can't phrase a criterion binarily, the scope is too vague — narrow it.
-4. **Depth is justified**: the evaluator's depth recommendation is binding by default — a full spec against a lean/evidence recommendation must satisfy an escape condition (prior ESCALATE/REGRESSION, prior coherence FAIL, cadence due, or a brand-new full-stack journey), not merely cite a trigger. Full cites which numbered trigger (1-4) in BACKGROUND AND carries the matching `Full trigger: <1|2|3|4> — <one-line reason>` metadata line (the engine demotes a full spec without it to lean); lean states "no full trigger holds" — needing unit tests is never the cited reason. ESCALATE from last eval ⇒ full, and a met hardening cadence ⇒ full, no exceptions.
+4. **Depth is justified**: the evaluator's depth recommendation is binding by default — a full spec against a lean/evidence recommendation must satisfy an escape condition (prior ESCALATE/REGRESSION, prior coherence FAIL, cadence due, or a brand-new full-stack journey), not merely cite a trigger. Full cites which numbered trigger (1-4) in BACKGROUND AND carries the matching `Full trigger: <1|2|3|4> — <one-line reason>` metadata line (the engine demotes a full spec without it to lean); lean states "no full trigger holds" — needing unit tests is never the cited reason. ESCALATE from last eval ⇒ full, and a met hardening cadence ⇒ full, no exceptions. Neither `Depth enforcement:` nor `Maintenance isolation:` appears anywhere in the spec — they are operator-only lines and writing one is a self-granted exception (anti-pattern 25); the need goes in BACKGROUND prose instead.
 5. **Target selection followed the priority rubric** — if you deviated (e.g., skipped a regressed journey), the reason is stated in BACKGROUND.
 6. **Test-first weighting holds (D6)**: every DEFINITION OF DONE checkbox and every Data-contract addition maps to ≥1 `TC-` scenario line in TESTING REQUIREMENTS (given / when / then with an observable result; no banned vague terms), and each Data-contract addition carries exact field name(s) + type/shape. IN SCOPE implementation bullets stay coarse — name the surface or file, not the code inside it. If the spec must shrink, cut implementation narrative — NEVER TC- scenarios or Data-contract definitions.
 
diff --git a/incredible_auto_dev/.claude/agents/goal-evaluator.md b/incredible_auto_dev/.claude/agents/goal-evaluator.md
index 775d60e0..0ea0f2df 100644
--- a/incredible_auto_dev/.claude/agents/goal-evaluator.md
+++ b/incredible_auto_dev/.claude/agents/goal-evaluator.md
@@ -4,8 +4,8 @@ description: Goal-mode iteration evaluator. Reads iteration outputs (handoffs, b
 model: claude-opus-5
 tools: [Read, Glob, Grep, Bash, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.10.0
-last_updated: 2026-07-29
+version: 1.12.0
+last_updated: 2026-08-21
 ---
 
 # Goal Evaluator Agent
@@ -48,7 +48,7 @@ Follow methodology section A (evidence walk). In short: deterministic reports fi
 - Verify the screenshot in `reports/qa/<iter-name>-evidence/` actually shows the claimed end state
 - Cross-check against the prior journey state (inlined digest) to detect changes (newly passing, newly failing, regressed)
 
-Stable `passing`/`already_passing` journeys inside this iteration's **Required-still-passing set** are re-verified mechanically by the deterministic replay lane at BOTH depths — the lean executor and the full pipeline's browser-qa step (those with stored golden scripts; a required journey WITHOUT a golden is routed to the LLM browser-qa lane the same iteration). Their rows land in the merged `ui-test-results.md` you already read. The raw `regression-replay-results.md` is a lane artifact, not an input: where it disagrees with the merged file, the merged file wins — a dated reconciliation footer on the raw file records any replay FAIL the LLM lane overturned (golden-script false positive). A row whose verdict cell is `DEFERRED-BUDGET` (SPEED-15 trim rung 2) means the wall-clock iteration budget cut that journey's re-verification this run — it was NOT tested: the journey KEEPS its prior recorded status (never `regressed`/`failing`/`unknown` on that row alone), you note it as deferred, and the deterministic achievement gate blocks GOAL_ACHIEVED while any journey is deferred. Stable journeys OUTSIDE the set carry over unverified. Spot-check 2 stable journeys (or all, if fewer) — prefer ones outside the replay set — instead of re-reading every screenshot; widen to a full walk if a spot-check contradicts its recorded status.
+Stable `passing`/`already_passing` journeys inside this iteration's **Required-still-passing set** are re-verified mechanically by the deterministic replay lane at BOTH depths — the lean executor and the full pipeline's browser-qa step (those with stored golden scripts; a required journey WITHOUT a golden is routed to the LLM browser-qa lane the same iteration). Their rows land in the merged `ui-test-results.md` you already read. The raw `regression-replay-results.md` is a lane artifact, not an input: where it disagrees with the merged file, the merged file wins — a dated reconciliation footer on the raw file records any replay FAIL the LLM lane overturned (golden-script false positive). A row whose verdict cell is `DEFERRED-BUDGET` (SPEED-15 trim rung 2) means the wall-clock iteration budget cut that journey's re-verification this run — it was NOT tested: the journey KEEPS its prior recorded status (never `regressed`/`failing`/`unknown` on that row alone), you note it as deferred, and the deterministic achievement gate blocks GOAL_ACHIEVED while any journey is deferred. Stable journeys OUTSIDE the set carry over unverified. Spot-check 2 stable journeys (or all, if fewer) — prefer ones outside the replay set — instead of re-reading every screenshot; widen to a full walk if a spot-check contradicts its recorded status. A results table can also be empty because the lane was FORBIDDEN rather than cut: an all-SKIPPED `ui-test-results.md` whose `**Reason:**` line names **maintenance isolation** means this iteration kept full reviewer/QA/auditor/coherence depth while application-service boot, browser QA and the deterministic replay lane were prohibited by contract — not an infrastructure failure and not an absent frontend. Score it like `DEFERRED-BUDGET`: every journey KEEPS its prior recorded status (never `unknown`/`failing`/`regressed` on that basis alone), and the evaluation says outright that the iteration ran under maintenance isolation and which journeys therefore went unverified. It never runs the other way — an isolated iteration produced no browser evidence, so no journey may be promoted TO `passing`/`already_passing` on it, and a GOAL_ACHIEVED verdict here must name the earlier iteration whose evidence it rests on (the deterministic results gate counts only `FAIL` and `DEFERRED-BUDGET` cells, so an empty isolated table does not block you — that judgment is yours).
 
 Also read this iteration's `coherence.md` and note its verdict. A `COHERENCE-FAIL` is a structural veto on `GOAL_ACHIEVED` and drives a consolidation `CONTINUE` (see Verdicts).
 
@@ -278,9 +278,10 @@ or `CONTINUE`, `ESCALATE`, `REGRESSION`, `STALLED`.
 - Do NOT mark `GOAL_ACHIEVED` if any anti-goal violation is unresolved.
 - Do NOT mark `GOAL_ACHIEVED` if this iteration's `coherence.md` is `COHERENCE-FAIL`. A coherence failure is a structural veto — the product is incoherent (scattered navigation, a duplicate home, or the same value computed/served more than one way) even if all journeys pass. Drive a consolidation `CONTINUE` instead.
 - Do NOT mark `GOAL_ACHIEVED` if this iteration's `journeys-changed.md` lists any journey you did not re-verify against the current goal text this iteration — a pass earned on the old text is not a pass.
+- Do NOT mark `GOAL_ACHIEVED` on an iteration that ran under **maintenance isolation** on the strength of that iteration's own evidence — it produced none. If every Must-have journey was already passing beforehand, name the earlier iteration whose evidence the certification rests on (see the maintenance-isolation rule in step 1 and methodology A3's second carve-out).
 - Update `journey-history.json` atomically — write the full new state, do not partial-update.
 - Append to `evaluator-log.md` — never overwrite prior entries; this is the chronological record.
-- If you cannot find evidence for a journey (e.g., browser-qa-agent skipped it), set its status to `unknown` and note the gap in the evaluation. Do NOT guess.
+- If you cannot find evidence for a journey (e.g., browser-qa-agent skipped it), set its status to `unknown` and note the gap in the evaluation. Do NOT guess. The one exception is a lane withheld by contract: under maintenance isolation journeys keep their prior recorded status instead of going `unknown` (step 1).
 - Never recommend — and never score as blocking — a next iteration whose only content is evidence capture, screenshot retakes, or demo recording. Evidence gaps on working features ride the make-up lane (`evidence_makeup`, methodology A.7) or a `Depth: evidence` recommendation; prior evidence for unchanged code stays valid (methodology A.6). Goal-edit drift (`journeys-changed.md`) always outranks evidence durability.
 
 ## Token and Questioning Policy
diff --git a/incredible_auto_dev/.claude/anti-patterns/27-styled-verdict-cells-unparsed.md b/incredible_auto_dev/.claude/anti-patterns/28-styled-verdict-cells-unparsed.md
similarity index 96%
rename from incredible_auto_dev/.claude/anti-patterns/27-styled-verdict-cells-unparsed.md
rename to incredible_auto_dev/.claude/anti-patterns/28-styled-verdict-cells-unparsed.md
index fe14ebd1..6ff27703 100644
--- a/incredible_auto_dev/.claude/anti-patterns/27-styled-verdict-cells-unparsed.md
+++ b/incredible_auto_dev/.claude/anti-patterns/28-styled-verdict-cells-unparsed.md
@@ -1,4 +1,4 @@
-## 27. Markdown-styled verdict cells vanish from the machine parser and launder FAIL into PASS
+## 28. Markdown-styled verdict cells vanish from the machine parser and launder FAIL into PASS
 
 **Applies to:** any parser that extracts machine verdicts (PASS/FAIL/SKIP) from agent-written markdown, and any gate that consumes the parsed result.
 
diff --git a/incredible_auto_dev/.claude/anti-patterns/28-plan-line-suppresses-lane.md b/incredible_auto_dev/.claude/anti-patterns/29-plan-line-suppresses-lane.md
similarity index 96%
rename from incredible_auto_dev/.claude/anti-patterns/28-plan-line-suppresses-lane.md
rename to incredible_auto_dev/.claude/anti-patterns/29-plan-line-suppresses-lane.md
index 1058bd62..3cad7ad2 100644
--- a/incredible_auto_dev/.claude/anti-patterns/28-plan-line-suppresses-lane.md
+++ b/incredible_auto_dev/.claude/anti-patterns/29-plan-line-suppresses-lane.md
@@ -1,4 +1,4 @@
-## 28. A plan metadata line can silently suppress an entire verification lane
+## 29. A plan metadata line can silently suppress an entire verification lane
 
 **Applies to:** goal mode; any pipeline step whose execution is gated on a model-written metadata line rather than on the work the spec demands.
 
diff --git a/incredible_auto_dev/.claude/anti-patterns/README.md b/incredible_auto_dev/.claude/anti-patterns/README.md
index 02ec6267..a91cd441 100644
--- a/incredible_auto_dev/.claude/anti-patterns/README.md
+++ b/incredible_auto_dev/.claude/anti-patterns/README.md
@@ -3,7 +3,7 @@
 One file per numbered entry, split from the former monolith (CTX-12) so a reader loads
 only what matches the situation: scan this index, open the matching `<NN>-<slug>.md`,
 nothing else. Numbering is FROZEN forever — files keep their original `## <N>. <title>`
-headings; the next new entry takes the next free number (28) as `<NN>-<slug>.md` plus a
+headings; the next new entry takes the next free number (30) as `<NN>-<slug>.md` plus a
 row here (maintenance protocol §2).
 
 | # | Entry | Applies when | Rule (one line) |
@@ -35,3 +35,5 @@ row here (maintenance protocol §2).
 | 25 | [25-self-justifying-governor-bypass.md](25-self-justifying-governor-bypass.md) | gates on agent behavior | A governor must validate against signals the governed agent cannot author; a self-written justification line is a suggestion, not a gate |
 | 26 | [26-per-scope-caps-no-machine-aggregate.md](26-per-scope-caps-no-machine-aggregate.md) | resource caps on shared hardware | Per-scope ceilings need a machine-level aggregate over a registry of live consumers, plus verification of every host assumption they rest on |
 | 27 | [27-software-guards-without-reset-reason.md](27-software-guards-without-reset-reason.md) | a machine resets, freezes, or reboots itself | Read the platform's own postmortem registers (reset reason, pstore, RAS) BEFORE building another software guard; "unreadable" is never "clean" |
+| 28 | [28-styled-verdict-cells-unparsed.md](28-styled-verdict-cells-unparsed.md) | parsing machine verdicts out of agent-written markdown | Match verdict cells tolerantly (bold/backticks/annotations); an unparseable cell is UNKNOWN, never an implicit PASS |
+| 29 | [29-plan-line-suppresses-lane.md](29-plan-line-suppresses-lane.md) | gating a verification lane on model-written plan metadata | Gate lanes on what the spec demands (named user journeys), not on a model-authored `Frontend Present:` line |
diff --git a/incredible_auto_dev/.claude/architecture/configuration.md b/incredible_auto_dev/.claude/architecture/configuration.md
index 45baa060..7af1cb03 100644
--- a/incredible_auto_dev/.claude/architecture/configuration.md
+++ b/incredible_auto_dev/.claude/architecture/configuration.md
@@ -55,7 +55,7 @@ agents:
 
 After editing, run `python3 scripts/automation/sync-cli-assets.py --cli claude` and commit the regenerated `.claude/agents/*.md`.
 
-All agent invocations (phase mode and goal mode) go through `lib/quota-retry.sh::claude_with_quota_retry`, which passes `--effort max` and handles quota exhaustion by sleeping until reset and resuming. This is automatic — no per-agent flag is needed.
+All agent invocations (phase mode and goal mode) go through `lib/quota-retry.sh::claude_with_quota_retry`, which passes `--effort max` (plus `--settings '{"outputStyle":"<name>"}'` when the wave-1 output-style table resolves one, opt-in via `CHAIN_OUTPUT_STYLES=true`) and handles quota exhaustion by sleeping until reset and resuming. This is automatic — no per-agent flag is needed.
 
 ## config/install-security-policy.json
 
@@ -95,12 +95,18 @@ The `allow` list should be customized per project (e.g., add `Bash(alembic *)` f
 | `CHAIN_DISABLE_AUTO_WAIT` | `false` | Fail immediately on quota exhaustion |
 | `CHAIN_INSTALL_GATE_BYPASS` | (unset) | Bypass install security gate |
 | `CHAIN_CLAUDE_DISABLE_CACHE_HYGIENE` | `false` | When `true`, drop the `--exclude-dynamic-system-prompt-sections` flag from claude invocations. Default keeps it on (improves prompt-cache reuse across sessions). |
-| `CHAIN_TELEMETRY_TOKENS` | `false` | When `true`, route claude calls through `lib/claude_stream_renderer.py` to capture token usage and `total_cost_usd` into `claude_usage` telemetry events. See `docs/goal-mode-telemetry.md`. |
+| `CHAIN_TELEMETRY_TOKENS` | `true` | When `true` (the default for headless runs), route claude calls through `lib/claude_stream_renderer.py` to capture token usage and `total_cost_usd` into `claude_usage` telemetry events. See `docs/goal-mode-telemetry.md`. |
 | `CHAIN_TRACE_DIR` | (auto-set by entry scripts) | Directory where each successful claude invocation appends a record to `trace.jsonl` and copies its stdout to `<NNNN>-<agent>.log`. Phase mode auto-sets to `runs/<phase>/trace/`; goal mode auto-sets to `runs/goal-session-<sid>/trace/`. Inspect with `python3 scripts/automation/lib/replay_trace.py list <dir>`. |
 | `CHAIN_DISABLE_TRACE` | `false` | When `true`, the entry scripts skip auto-setting `CHAIN_TRACE_DIR` so no trace records are written. |
 | `CHAIN_DISABLE_PERMISSION_ISOLATION` | `false` | When `true`, skip the per-agent permission overlay applied by `lib/quota-retry.sh`. The overlay reads `lib/agent_permissions.py` and passes `--disallowedTools` to claude based on `CHAIN_CURRENT_AGENT` — by default, only `release-manager` can `git push`, `gh pr merge`, `gh release`, `git tag`, etc. |
+| `CHAIN_OUTPUT_STYLES` | `false` | STYLE-1 experiment: `true` arms the wave-1 table in `lib/agent_permissions.py` (`OUTPUT_STYLE_OVERRIDES`) — per-agent Claude Code output style on headless dispatches (`Concise` on developer/qa/browser-qa-agent/orchestrator/ui-impact-analyst/ux-regression-reviewer). Judges refused by construction; goal mode only. |
+| `CHAIN_AGENT_OUTPUT_STYLE` | (unset) | Per-agent output-style experiment map, e.g. `developer=Concise,qa=Concise` — same grammar as `CHAIN_AGENT_EFFORT`; judges refused. |
+| `CHAIN_OUTPUT_STYLE_OVERRIDE` | (unset) | Debug: forces one style on every agent including judges (loud NOTICE); wins over all other resolution; works outside goal mode too. |
 | `CHAIN_DEPTH_ARBITER` | `true` | SPEED-20 deterministic depth arbiter (evaluator depth recommendation binding by default; `false` restores the legacy SPEED-10 allowlist) |
 | `CHAIN_FULL_CADENCE_CAP` | `4` | Arbiter window cap: at most one full per W iterations (`0`/`1` disables the cap) |
+| `CHAIN_REQUIRE_FULL_DEPTH` | (unset) | **OPERATOR-SET ONLY.** Truthy (`true`/`TRUE`/`1`/`yes`/`on`) makes full depth a HARD requirement wherever an iteration already asks for it: it PREVENTS a `Depth: full` spec from being demoted (it outranks every cost rung of the arbiter, and the legacy-allowlist path pauses rather than demotes), and if full still cannot be dispatched the engine pauses `AWAITING_FULL_DEPTH` before dispatch instead of running lean. It does NOT promote a lean or evidence spec to full: the arbiter's precedence rung only runs for a spec that already asked for full, and the other guard sites (`depth-parse`, `full-dispatch`, `depth-legacy-allowlist`, `isolation-requires-full`) PAUSE rather than promote. Write `Depth: full` in the spec for the requirement to have something to protect. Per-iteration equivalent: a `Depth enforcement: required` line in the iteration spec. The decomposer is forbidden to emit that line (anti-pattern 25) — a human writes it. Default off: with neither present the arbiter behaves exactly as before |
+| `CHAIN_MAINTENANCE_ISOLATION` | (unset) | **OPERATOR-SET ONLY.** Truthy (`true`/`TRUE`/`1`/`yes`/`on`/`required`) declares the run a maintenance isolation: full reviewer/QA/auditor/coherence/evaluator depth REQUIRED, application-service boot, browser QA, the deterministic replay lane and the demo showcase FORBIDDEN. Enforced fail-closed at seven sites: `detect_frontend_in_plan` subordinates the `CHAIN_GOAL_TARGET_JOURNEYS` browser override, and `_boot_shared_services`, `ensure_services_running`, `browser-qa-phase.sh`, `replay_lane_partition_and_verify`, `demo-phase.sh` and `run-goal.sh`'s async showcase-join reap call `maintenance_isolation_refuse`, which appends to `iter-<N>/maintenance-isolation-refusals` and emits a `maintenance_isolation_refused` event (the six original chokepoints of the port, plus the showcase-join reap added on this side). Per-iteration equivalent: a `Maintenance isolation: required` line in the spec (decomposer forbidden — anti-pattern 25). Isolation is enforced only at FULL depth: it implies the full-depth requirement (`goal_full_depth_required`), so an isolated `Depth: full` spec is protected from every cost rung, and an isolated spec that resolves to lean/evidence pauses `AWAITING_FULL_DEPTH` (step `isolation-requires-full`) rather than being promoted or run |
+| `CHAIN_MAINTENANCE_ISOLATION_SOURCE` | (engine-set) | Provenance stamp written by `apply_maintenance_isolation_from_spec`: `spec` when this iteration's spec declared isolation (cleared and recomputed at the next iteration so it cannot leak forward), `env` when the operator declared it session-wide (never cleared). Diagnostic — do not set by hand |
 | `CHAIN_ITER_TIME_BUDGET_SECONDS` | `3600` | SPEED-15 wall-clock iteration budget (`0` disarms everything) |
 | `CHAIN_ITER_BUDGET_MODE` | `trim` | `warn` logs only; `trim` (default) sheds optional breadth in rung order — spine/gates never trimmed |
 | `CHAIN_DEV_FULL_GOAL` | `false` | TOKEN-10 hatch: `true` feeds executors the full `docs/goal.md` instead of the goal slice |
diff --git a/incredible_auto_dev/.claude/architecture/goal-mode.md b/incredible_auto_dev/.claude/architecture/goal-mode.md
index ddcafc4a..cc8c3af1 100644
--- a/incredible_auto_dev/.claude/architecture/goal-mode.md
+++ b/incredible_auto_dev/.claude/architecture/goal-mode.md
@@ -67,6 +67,8 @@ The synthetic phase name `goal-<sid>-iter-<N>` (where `<sid>` is the session id
 
 **Depth arbitration (SPEED-20).** The evaluator's depth recommendation is binding by default. A spec-requested `full` passes through a deterministic ladder in `run-goal.sh` (`CHAIN_DEPTH_ARBITER`, default on; iter-0 exempt): prior ESCALATE/REGRESSION or a prior COHERENCE-FAIL always keeps full; a previous-iteration `budget-breached` marker on an ordinary CONTINUE forces LEAN (the recovery pass — the SPEED-4 cadence re-promotion is suppressed that iteration); a cadence-due full is sanctioned; otherwise at most one full runs per `CHAIN_FULL_CADENCE_CAP` (default 4) window, and a full against an evaluator lean/evidence recommendation survives ONLY when the spec provably plans a brand-new full-stack journey (`goal_new_fullstack_journey`, fail-closed — see anti-pattern 25 for why the spec's own `Full trigger:` line is never sufficient). Grants and demotions are telemetered (`depth_full_granted`/`depth_demoted`); `CHAIN_DEPTH_ARBITER=false` restores the legacy SPEED-10 allowlist.
 
+**Hard depth requirements — the rung above cost (reverse-ported 2026-08-21).** Every rung of the arbiter above is a COST rung: budget-breach, full-cap, cadence and the evaluator's lean/evidence preference all answer *"is full depth worth the wall-clock here?"*. None of them answers *"can this engine execute full depth at all?"* — and only that second question may override a safety requirement. So an iteration for which full depth IS the control (its adversarial review/audit lane is what stands between a destructive write and an unreviewed mutation) declares the requirement — `CHAIN_REQUIRE_FULL_DEPTH` for the session, or a `Depth enforcement: required` line for one iteration — and `goal_full_depth_required` (`lib/common.sh`) resolves it to full ahead of every cost rung, recording the rung it overrode as `depth_cost_overridden` telemetry while leaving that rung's on-disk marker untouched (evidence, not behaviour). Where full still cannot be dispatched the engine FAILS CLOSED at all five demotion sites — the arbiter backstop (`depth-arbiter`), an unparseable spec `Depth:` line (`depth-parse`), a `run-phase.sh` without `--no-finalize` (`full-dispatch`), and the legacy SPEED-10 allowlist when it finds no qualifying `Full trigger:` (`depth-legacy-allowlist`) — pausing `AWAITING_FULL_DEPTH` BEFORE dispatch and removing `depth-dispatched` so a resume cannot inherit a stale lean decision. The fifth site, `isolation-requires-full`, pauses an isolated spec that resolved to lean/evidence before any executor runs. That fourth site matters because the precedence rung and its backstop both live INSIDE the arbiter's `if`: whenever the arbiter is skipped — `CHAIN_DEPTH_ARBITER=false`, or iter-0, which the arbiter exempts — a hard-required spec falls through to the allowlist, so the knob is never a way out of this pause; it deletes the guard, not the cause. The remedy is per-path, printed with the pause and stored as `remedy=` in `iter-<N>/depth-requirement-unmet`. The declaration is OPERATOR-authored by contract: the decomposer is forbidden to emit either line, because a governor reading the governed agent's own prose is not a governor (anti-pattern 25). Its companion control, `Maintenance isolation: required` / `CHAIN_MAINTENANCE_ISOLATION`, separates the two things "full depth" used to conflate — it keeps full reviewer/QA/auditor/coherence depth while FORBIDDING application-service boot, browser QA, the replay lane and the demo showcase, refusing fail-closed at each chokepoint instead of degrading. Both are default-OFF.
+
 **Wall-clock iteration budget (SPEED-15, armed).** `CHAIN_ITER_TIME_BUDGET_SECONDS` (default 3600; 0 disarms) + `CHAIN_ITER_BUDGET_MODE` (default trim) bound each iteration at step boundaries — never mid-agent, and never the spine (developer/reviewer/decomposer/evaluator, QA loop, audit, closure, gates, two-key confirm). Over budget, the trim ladder sheds optional breadth in rung order: defer demo+README to the tail; narrow the browser regression sweep to targets + replay-FAIL re-confirms (cut journeys get `DEFERRED-BUDGET` rows that keep their prior status and mechanically block GOAL_ACHIEVED until re-verified); skip full-pipeline test-plan generation when a test source exists; skip the non-blocking ux-regression reviewer. A breached iteration also writes the `budget-breached` marker that forces the NEXT iteration lean via the arbiter.
 
 ## Halt conditions
diff --git a/incredible_auto_dev/.claude/letter-to-future-sessions.md b/incredible_auto_dev/.claude/letter-to-future-sessions.md
index f7d3bb8a..eb358516 100644
--- a/incredible_auto_dev/.claude/letter-to-future-sessions.md
+++ b/incredible_auto_dev/.claude/letter-to-future-sessions.md
@@ -62,6 +62,15 @@ pain into its §16 staging section.
 - **The pump protocol changes but a running pump predates it.** Pump behavior (out files,
   model overrides, >8KB file-indirection) comes from `.claude/skills/goal-interactive-dispatch.md`
   loaded at pump start — after changing it, restart the pump session before resuming.
+- **A safety control ends up on a cost ladder.** Any ladder that can downgrade work has two
+  kinds of rung: "is this worth the wall-clock?" (budget, cadence, window caps) and "can this
+  engine execute it at all?" — and only the second may override a REQUIREMENT. SPEED-20's
+  depth arbiter had only the first kind, so a lean demotion quietly removed the adversarial
+  review lane an iteration existed to run and auto-armed a browser replay against a knowingly
+  damaged database. Before you add a rung, say out loud which question it answers: a control
+  a cost heuristic may trade away is not a control. Tripwire: `depth_cost_overridden` names
+  the rung that got outranked, and `AWAITING_FULL_DEPTH` must never mean "the cost ladder
+  preferred lean" (reverse-ported 2026-08-21 — `docs/improvement-roadmap.md` CAND-MAINT-ISO).
 
 ## Known limitations we chose NOT to fix (so you don't rediscover them as bugs)
 
diff --git a/incredible_auto_dev/.claude/model-orchestration.md b/incredible_auto_dev/.claude/model-orchestration.md
index 5137bb5d..8856df2b 100644
--- a/incredible_auto_dev/.claude/model-orchestration.md
+++ b/incredible_auto_dev/.claude/model-orchestration.md
@@ -34,6 +34,24 @@ readme-maintainer, demo-narrator, ux-regression-reviewer. Do not raise a medium
 "fix" quality — its work is procedural; and do not lower a max judge's effort to save tokens — lower the *context you feed it* instead
 (see `.claude/workflow.md` and the digest tools in `scripts/automation/lib/goal_gate.py`).
 
+Output style (STYLE-1, opt-in, default off): headless dispatches may also carry a Claude
+Code output style, resolved by the wave-1 table in `lib/agent_permissions.py`
+(`OUTPUT_STYLE_OVERRIDES`), armed by `CHAIN_OUTPUT_STYLES=true`. Wave 1 sets `Concise` on
+developer, qa, browser-qa-agent, orchestrator, ui-impact-analyst, ux-regression-reviewer —
+long, machine-consumed, non-judge steps. Judges (`JUDGE_AGENTS`) are refused by construction
+(D4 — never lower a judge's effort/output to save tokens); `Learning` is refused outright
+(it asks the human to write code, stalling headless runs); an unknown style name fails the
+dispatch loudly instead of the CLI's silent fallback to default. The interactive backend has
+no native style support for Agent-tool subagents, so a resolved style is emulated by
+appending a prompt block instead (trace records `<name>(emulated)`); Codex ignores the whole
+mechanism (no `--settings` equivalent). Every dispatch proves its effective style by reading
+the stream-json `init` event back into the trace/telemetry sidecar; a requested-vs-effective
+mismatch fires a loud `WARNING` and an `output_style_mismatch` telemetry event. The experiment
+knobs (`CHAIN_OUTPUT_STYLES`, `CHAIN_AGENT_OUTPUT_STYLE`) act only in goal mode
+(`GOAL_SESSION_DIR` set); the debug override (`CHAIN_OUTPUT_STYLE_OVERRIDE`) works in any
+mode. See `docs/goal-mode-quickstart.md` to try it and `docs/improvement-roadmap.md` §16
+CAND-STYLE for status.
+
 ## 2. The commander does not go into the field
 
 The main conversation (orchestrator/pump/interactive session) exists to route work and hold
@@ -135,7 +153,12 @@ An agent's claim about its own work is a hypothesis, not evidence.
 | `CHAIN_LEAN_PARALLEL_BROWSER_QA` | default `off` (SPEED-2 experiment — G4: no default flip with the knob); `replay` forks the browser-qa service boot + deterministic replay lane right after the developer step so it overlaps the ~21-min review, joined once review settles; a review-1 FAIL kills the fork and discards its lane files BEFORE any step invalidation; tripwire: attempt-1 review FAILs in ≥2 of the last 3 iterations persist `runs/goal-session-<sid>/state/parallel-bqa-disabled` (fork off for the rest of the session); `full` (SPEED-3) forks the WHOLE browser-qa section (LLM lane included) on HEADLESS backends only — the join re-raises an in-fork transport exit (70) as the usual resumable pause, and a review-1 FAIL kills the fork tree (in-flight dispatch included) then logs a `parallel_bqa_wasted_dispatch` cost event; on the interactive backend `full` demotes to `replay` with a warning (the cancellation gap is EXP-4's); the tripwire covers both stages | `goal-iter-lean.sh` |
 | `CHAIN_ASYNC_SHOWCASE` | default `true`; demo/summary/README/renders run in the background overlapping the next decomposer (CONTINUE/ESCALATE only; joined + committed before the next executor dispatch) | `run-goal.sh` |
 | `CHAIN_SESSION_RETRO` | default `true`; terminal halts (GOAL_ACHIEVED/STALLED/REGRESSION_HALT/BUDGET_EXHAUSTED) freeze a deterministic evidence snapshot to `state/retro-input.md` AND then dispatch the retro-analyst (light tier) to draft `reports/goal-session-<sid>-retro.md` improvement proposals from it (EVO-2); the drafting dispatch is skipped when the digest is missing; resumable pauses never fire either step; non-blocking — set `false` to disable both | `run-goal.sh`, `lib/retro_collect.sh` |
+| `CHAIN_REQUIRE_FULL_DEPTH` | default off (unset), **operator-set only**; truthy makes full depth a HARD requirement for a spec that already asks for it — it PREVENTS demotion (the arbiter resolves such an iteration to full ahead of every cost rung, recording the rung it overrode as `depth_cost_overridden`; the legacy-allowlist path pauses instead of demoting), and where full still cannot be dispatched the engine pauses `AWAITING_FULL_DEPTH` BEFORE dispatch instead of running lean. It never PROMOTES a lean/evidence spec: the precedence rung only runs for a spec that already asked for full, and every other guard site pauses instead — write `Depth: full` in the spec for the requirement to have something to protect. Per-iteration form: a `Depth enforcement: required` spec line — the decomposer is forbidden to emit it (anti-pattern 25) | `lib/common.sh`, `run-goal.sh`, `goal-iter-lean.sh` |
+| `CHAIN_MAINTENANCE_ISOLATION` | default off (unset), **operator-set only**; truthy (`true`/`1`/`yes`/`on`/`required`) keeps full reviewer/QA/auditor/coherence/evaluator depth while FORBIDDING application-service boot, browser QA, the deterministic replay lane and the demo showcase. Every chokepoint refuses fail-closed (`maintenance_isolation_refuse` → refusals marker + `maintenance_isolation_refused` event); `apply_maintenance_isolation_from_spec` materializes the spec form into the environment before any child dispatch and stamps `CHAIN_MAINTENANCE_ISOLATION_SOURCE=spec\|env`. Per-iteration form: a `Maintenance isolation: required` spec line (decomposer forbidden). Enforced only at FULL depth — isolation implies the full-depth requirement, so a non-full isolated spec pauses `AWAITING_FULL_DEPTH` (`isolation-requires-full`) instead of running | `lib/common.sh`, `run-goal.sh`, `run-phase.sh`, `qa-phase.sh`, `browser-qa-phase.sh`, `demo-phase.sh`, `lib/replay-lane.sh`, `lib/closure_gate.py` |
 | `CHAIN_AGENT_EFFORT` | opt-in experiment, e.g. `developer=high`; **judges are refused by a hardcoded guard**; auto-reverted by the telemetry tripwire on quality movement | `lib/agent_permissions.py` |
+| `CHAIN_OUTPUT_STYLES` | default `false`; `true` arms the wave-1 table in `lib/agent_permissions.py` (`OUTPUT_STYLE_OVERRIDES`) — goal mode only | `lib/agent_permissions.py`, `lib/quota-retry.sh`, `lib/interactive-dispatch.sh` |
+| `CHAIN_AGENT_OUTPUT_STYLE` | per-agent experiment map, e.g. `developer=Concise,qa=Concise` (same grammar as `CHAIN_AGENT_EFFORT`); judges refused | `lib/agent_permissions.py`, `lib/quota-retry.sh`, `lib/interactive-dispatch.sh` |
+| `CHAIN_OUTPUT_STYLE_OVERRIDE` | debug: forces one style on every agent incl. judges (loud NOTICE); wins over all; works in any mode | `lib/agent_permissions.py`, `lib/quota-retry.sh`, `lib/interactive-dispatch.sh` |
 | `CHAIN_DOCTOR` | default `true`; run-goal.sh prints the REL-2 preflight doctor table (PASS/WARN/FAIL environment truth) at engine start, WARN-ONLY BY CONSTRUCTION — crash/nonzero/hang all degrade to a log line and the session proceeds; gating exists only as the doctor CLI's own `--strict-doctor` flag (exit 1 on ≥1 FAIL; the engine never passes it) | `run-goal.sh`, `doctor.sh` |
 
 If you disable a gate/routing knob for an experiment, **re-enable it in the same session**
diff --git a/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md b/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
index 582f7872..2b6b12fe 100644
--- a/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
+++ b/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
@@ -34,7 +34,7 @@ your overall impression of the iteration.
      claim, including the dev handoff.
    - Record the citation (results row + screenshot filename). **No citation → the journey's
      status is `unknown`, and you say so.**
-   - **One carve-out (REL-14):** when the journey is listed in this iteration's
+   - **Two carve-outs. First (REL-14):** when the journey is listed in this iteration's
      `<iter-dir>/browser-infra.json` (the engine's browser-infra token: services/Chrome
      failed, NOT the product) and there is no fresh screenshot, score it `partial` with the
      gap noted as `pending-infra`, and set `pending_infra: true` on it in journey-history —
@@ -44,6 +44,21 @@ your overall impression of the iteration.
      the browser infrastructure itself is the blocker: treat it as a human-owned action
      (STALLED-class, decision tree C.2) instead of scheduling a third silent retry. A fresh
      screenshot this iteration — pass or fail — clears `pending_infra` and scores normally.
+   - **Second (maintenance isolation):** when this iteration's
+     `ui-test-results.md` is all-SKIPPED and its `**Reason:**` line names maintenance
+     isolation, the lane was FORBIDDEN by the iteration's contract, not missing — full
+     reviewer/QA/auditor/coherence depth was retained while application-service boot,
+     browser QA and the deterministic replay lane were prohibited. So this is neither an
+     absent citation nor an infra failure: EVERY journey KEEPS its prior recorded status
+     (never `unknown`, `failing` or `regressed` on that basis alone), you do NOT set
+     `pending_infra` (nothing is owed by the infrastructure — the contract withheld it),
+     and you state in the report that the iteration ran under maintenance isolation and
+     which journeys therefore went unverified. It never runs the other way: an isolated
+     iteration produced no browser evidence, so no journey may be promoted TO
+     `passing`/`already_passing` on it, and a `GOAL_ACHIEVED` verdict on such an iteration
+     must cite the earlier iteration whose evidence it rests on (the deterministic results
+     gate counts only `FAIL` and `DEFERRED-BUDGET` cells, so an empty isolated table will
+     not stop you — that judgment is yours).
 4. **Stable-journey spot-check.** Journeys with unchanged `passing`/`already_passing` status
    that are in this iteration's **Required-still-passing set** (and have a stored golden
    script) are re-verified mechanically by the replay lane (`demo_runner.py --mode verify`)
@@ -150,7 +165,11 @@ tests pass; marking passing." The results file has no row for J-07 (browser lane
 and there is no screenshot. Wrong: `passing` because the code "clearly works". Right: status
 `unknown`, gap noted ("browser lane skipped J-07 — no evidence"), verdict `CONTINUE` with
 next-step "re-run browser QA for J-07". Unit tests are never journey evidence (a routing typo
-can 404 the page while every unit test passes).
+can 404 the page while every unit test passes). *Contrast, and the one case where "no row" is
+NOT `unknown`:* if the results file is all-SKIPPED because its `**Reason:**` line names
+maintenance isolation, the lane was withheld by contract rather than skipped by accident, and
+every journey keeps its prior status (A3, second carve-out). The test is the DECLARED reason,
+never the bare absence of a row.
 
 ## E. Pre-finalize self-check (all five, in your head, before writing eval.md)
 
diff --git a/incredible_auto_dev/.claude/skills/goal-interactive-dispatch.md b/incredible_auto_dev/.claude/skills/goal-interactive-dispatch.md
index 1e25ebb5..7c3bea7b 100644
--- a/incredible_auto_dev/.claude/skills/goal-interactive-dispatch.md
+++ b/incredible_auto_dev/.claude/skills/goal-interactive-dispatch.md
@@ -1,6 +1,6 @@
 # Goal Mode — Interactive Dispatch (Pump Protocol)
 
-version: 3.0.0 (protocol v3 — pump pid-liveness ident; bump with every change to this file)
+version: 3.0.3 (protocol v3 — pump pid-liveness ident; bump with every change to this file)
 
 This skill defines how the foreground Claude Code session (the "pump") runs the
 existing goal-mode engine so that every agent executes as an interactive
@@ -274,6 +274,7 @@ is authoritative:
 - `AWAITING_GITHUB_AUTH` — ask the user to run `gh auth login`, then `/goal-resume`.
 - `AWAITING_DISK` — free disk still under the hard floor after automatic cleanup; run `bash scripts/automation/tmp-doctor.sh --aggressive` yourself (no user approval needed), then `/goal-resume`. Only involve the user if the doctor exits 2 (the machine is genuinely out of disk).
 - `AWAITING_PUMP` — the pump/session went away mid-iteration; re-open it and `/goal-resume` (it re-runs that iteration).
+- `AWAITING_FULL_DEPTH` — nothing was dispatched: the iteration declared full depth a HARD requirement (`CHAIN_REQUIRE_FULL_DEPTH`, a `Depth enforcement: required` line in its spec, or a `Maintenance isolation: required` line — isolation requires full depth by contract) and the engine could not dispatch it, so it halted BEFORE any developer mutation, browser lane or service boot. Report the engine's `reason:` line and `runs/goal-session-<sid>/iter-<N>/depth-requirement-unmet` — it records `requested`, `actual`, `reason`, `step` and `remedy`. Relay THAT remedy, which depends on `step`: `depth-arbiter` (the cost ladder could not grant full) — let the cadence window pass or re-run with `CHAIN_FULL_CADENCE_CAP=1`; `depth-parse` — fix the spec's `Depth:` line so it parses **before** resuming (a still-unparseable line makes `--resume` re-run the decomposer, which rewrites the spec and drops operator-only lines); `full-dispatch` — the installed `run-phase.sh` has no `--no-finalize` flag, so update/restore the framework checkout; `depth-legacy-allowlist` — add the qualifying `Full trigger: <1-4> — <reason>` line to the spec, or re-enable the deterministic arbiter (unset `CHAIN_DEPTH_ARBITER`; at iteration 0, which the arbiter exempts, only the `Full trigger:` line helps); `isolation-requires-full` — the spec declared maintenance isolation, which REQUIRES full depth, but resolved to lean/evidence: write `Depth: full` (plus a `Full trigger:` line when the arbiter is skipped) or drop the isolation declaration. Then `/goal-resume`. NEVER clear the requirement itself (unset `CHAIN_REQUIRE_FULL_DEPTH`, edit the spec line) to make the pause go away — the requirement is why the pause exists — and never suggest `CHAIN_DEPTH_ARBITER=false`, which removes the precedence rung and the guard rather than resolving anything.
 - `REGRESSION_HALT` — report the regression; resuming requires `--acknowledge-regression`.
 - `STALLED` or `BUDGET_EXHAUSTED` — report it and suggest editing `docs/goal.md` or raising `--max-iter`.
 - `ABORTED` — the run was interrupted; `/goal-resume` continues from the last iteration.
diff --git a/incredible_auto_dev/.claude/skills/phase-closure-gate.md b/incredible_auto_dev/.claude/skills/phase-closure-gate.md
index befab2f6..958a3ffc 100644
--- a/incredible_auto_dev/.claude/skills/phase-closure-gate.md
+++ b/incredible_auto_dev/.claude/skills/phase-closure-gate.md
@@ -26,7 +26,9 @@ For every phase, verify all exist and are non-empty:
 ## Vagueness Detection
 
 Reject any artifact that contains only:
-- Generic placeholders: "TBD", "TODO", "FILL IN", "N/A" where content is expected
+- Generic placeholders: "TBD", "TODO", "FIXME", "FILL IN", "N/A" where content is expected
+  — the marker tokens are matched case-sensitively (uppercase), so lowercase "todo"
+  in ordinary product prose ("a todo list app") is not a placeholder
 - Vague test steps: "Test the form", "Verify it works", "Check the page"
 - Empty sections with just headers
 - Fewer than 5 lines of actual content (excluding headers)
diff --git a/incredible_auto_dev/README.md b/incredible_auto_dev/README.md
index 418800e7..8ad01650 100644
--- a/incredible_auto_dev/README.md
+++ b/incredible_auto_dev/README.md
@@ -80,7 +80,7 @@ Optional flags: `--max-iter N` (optional hard cap on iterations; **unlimited by
 
 After baseline the decomposer drafts a coherence blueprint at `runs/goal-session-my-app/state/blueprint.md` and, **by default, auto-approves it and keeps running unattended** — a `coherence-auditor` then enforces the blueprint every iteration. If you'd rather review it first (~3 min: sane navigation? every shared value has one source?), start with `--require-blueprint-approval`: the loop pauses once (`AWAITING_BLUEPRINT_APPROVAL`), and you edit the file if needed then `--resume` (resuming counts as approval).
 
-**4. Inspect** `runs/goal-session-my-app/summary.md` when the loop halts. Halt verdicts: `GOAL_ACHIEVED` (success), `BUDGET_EXHAUSTED`, `STALLED`, `REGRESSION_HALT`, `ABORTED`, `AWAITING_BLUEPRINT_APPROVAL` (resumable pause for blueprint review — only with `--require-blueprint-approval`), `AWAITING_GITHUB_AUTH` (resumable pause — push-per-iter is on but `origin` won't authenticate; the run offers `gh auth login` when interactive, else `gh auth login && gh auth setup-git` then `--resume`).
+**4. Inspect** `runs/goal-session-my-app/summary.md` when the loop halts. Halt verdicts: `GOAL_ACHIEVED` (success), `BUDGET_EXHAUSTED`, `STALLED`, `REGRESSION_HALT`, `ABORTED`, `AWAITING_BLUEPRINT_APPROVAL` (resumable pause for blueprint review — only with `--require-blueprint-approval`), `AWAITING_GITHUB_AUTH` (resumable pause — push-per-iter is on but `origin` won't authenticate; the run offers `gh auth login` when interactive, else `gh auth login && gh auth setup-git` then `--resume`), `AWAITING_FULL_DEPTH` (resumable pause — the iteration declared full depth a HARD requirement via `CHAIN_REQUIRE_FULL_DEPTH`, a `Depth enforcement: required` spec line, or a `Maintenance isolation: required` spec line (isolation requires full depth) and the engine could not dispatch it, so nothing ran; the fix depends on which step caught it and the engine prints it with the pause — cadence window / `CHAIN_FULL_CADENCE_CAP=1`, a malformed `Depth:` line, a `run-phase.sh` without `--no-finalize`, a missing `Full trigger:` line on the legacy-allowlist path, or `isolation-requires-full` (write `Depth: full` or drop the isolation declaration) — then `--resume`; never clear the requirement, and note `CHAIN_DEPTH_ARBITER=false` is not a way out, it deletes the guard).
 
 Because per-iter push is on by default, goal mode checks at startup that a push to `origin` would authenticate, so an expired GitHub session can't stall a mid-run push on a credential prompt. Pushes are also run with `GIT_TERMINAL_PROMPT=0` so they fail fast (non-fatally) instead of hanging. Skip the startup check with `CHAIN_SKIP_GITHUB_PREFLIGHT=true`.
 
@@ -444,6 +444,7 @@ bash scripts/automation/render-summary.sh --session-index <sid>        # re-rend
 | `config/model-tiers.yaml` + `agents/*/agent.yaml` | Tier→model map + per-agent tier |
 | `config/install-security-policy.json` | Package allowlists and deny patterns |
 | `.claude/settings.json` | Claude Code tool permissions |
+| `lib/agent_permissions.py` → `OUTPUT_STYLE_OVERRIDES` | Per-agent Claude Code output style (wave-1: `Concise` on developer/qa/browser-qa-agent/orchestrator/ui-impact-analyst/ux-regression-reviewer); inert until `CHAIN_OUTPUT_STYLES=true` — see `.claude/model-orchestration.md` §7 |
 | `docs/goal.md` | Project vision and success criteria (goal mode also reads Must-have user journeys + Anti-goals) |
 | `runs/goal-session-<sid>/session.json` | Goal-mode session state (halt config, current iteration, last verdict) |
 | `runs/goal-session-<sid>/state/journey-history.json` | Per-journey pass/fail/regressed status across iterations |
@@ -464,6 +465,124 @@ This framework is designed to be added to project repos as a submodule or subtre
 
 All pending framework improvements — including the former "Token Optimization — Pending Work" and "Pipeline Hardening — Pending Work" backlogs that used to live here — are maintained in one canonical file: [`docs/improvement-roadmap.md`](docs/improvement-roadmap.md). It holds ~50 specified items (problem, file:line anchors, change spec, definition of done, verification commands, rollback) written so any maintainer session can execute one at a time, plus the executor ground rules and the process for adding new items. Every absorbed item from the old sections is traceable in that file's §17 ledger (several were already shipped and are marked as such).
 
+## Host incident 2026-08-07 — status + pending fix plan (GEEKOM A7 Max)
+
+> **Status 2026-08-08: C-state soak FALSIFIED on day 1 — unit removed; ladder → rung 3 (overnight
+> memtest86+ 08-08→09); goal mode PAUSED pending the verdict.** Fault reset #4 (12:48:17 boot)
+> fired with C2/C3 verifiably off in the dying boot (journal tag + `host_state`; 30 W / load1
+> 3.04 / 84 °C). Postmortem frozen pre-resume: `3f7c111ae8e94cdd8e39ad67cd0cff8b.md`. Memtest
+> errors → DIMM isolation → reseat/swap → RMA; clean → BIOS JEDEC baseline → fresh 7-day soak.
+> *(Previous status: fix EXECUTED — soak ACTIVE since 2026-08-07 21:02:21 BST.)* Phase 2 framework
+> code was committed 17:27 (`be57376` + vendored syncs). The Phase 1 unit was installed 17:26 but
+> left **un-enabled** (`sudo cp` only — the implementing session was killed by fault reset #3 at
+> 17:46, which fired **near-idle** in exactly that gap); enabled + verified 21:02:21 (journal tag
+> `iad-cstate-limit`, sysfs `state[23]/disable` 32×1, `is-enabled`) — that timestamp starts the
+> 7-day soak. Pump runs display-less under tmux user scope `goal-pump-tmux`; auto-resume unit
+> installed but **disarmed** (API-billing question stands). Daily journal:
+> `~/.cache/iad/host-guard/soak-log.md`. Plan files:
+> `~/.claude/plans/when-running-trendora-goal-drifting-floyd.md` (diagnosis + fix design),
+> `~/.claude/plans/just-after-implementing-the-majestic-sun.md` (execution + reset #3 forensics).
+
+### What happened (evidence-verified)
+
+Reported symptom: while trendora goal mode (session `ops-hardening`, iter 52) ran, the desktop
+froze and dropped to the GDM login screen. Investigation found **two distinct failures**:
+
+1. **The reported incident (15:13–15:18, no reboot):** `gnome-shell` logged
+   `Invalid sequence for VSYNC frame info` (15:13:15, UI freeze), then **SIGSEGV'd** (15:18:24,
+   `org.gnome.Shell@ubuntu.service: result 'core-dump'`); systemd tore down the graphical session →
+   login screen. The interactive pump (claude in ghostty) is a child of that session, so pump +
+   engine died as collateral (`engine_stop` 15:18:33; orphan `iter52_health_drill.py` left running).
+   Ruled out with hwmon/PSI data: memory pressure, oomd, CPU saturation, thermal trip (Tctl 84–89 °C,
+   gate 90). Contributing stress: pump-dispatched **browser-QA Chrome runs headed in the session**
+   (inherits `WAYLAND_DISPLAY`), spamming Wayland frame errors for hours.
+2. **Recurring hardware hard-resets (separate; 02:13, 11:12, then a 3rd at 17:46 that fired
+   NEAR-IDLE — 20–39 W, engine stopped, C-state unit installed-but-disabled; see Status):** 6 of the last
+   10 boots began from kernel reset-reason `0x08000800 — an uncorrected error caused a data fabric
+   sync flood event`. Settled 2026-07-30 (reset #7 fired with every software mitigation in force at
+   26–37 W / 65–74 °C): **hardware marginality**, not load. Boost-off/split-masks/engine-cap were
+   deliberately released 2026-07-30 — do **not** re-impose them. Failure 1's segfault is plausibly
+   collateral of the same marginal silicon.
+   Runbook status (`docs/host-guard.md` §"After a hardware reset", line 123): journald 15 s sync ✅,
+   rasdaemon ✅ (zero events — expected, non-ECC), pstore empty ✅; **C-state limiting never actually
+   in force** (volatile sysfs write, wiped by the daily resets); memtest86+ installed, never run;
+   **BIOS 1.26 (2025-09-15) is the latest — owner confirmed no newer firmware exists**.
+
+Evidence lives in: `~/.cache/iad/host-guard/postmortems/6f5ec77c93e0402d9629bf24a7a1a2b5.md` (the
+11:12 reset), `~/.cache/iad/host-guard/events.jsonl` (`host_state` events prove which mitigations
+were live), `~/.cache/iad/host-guard/hwmon/hwmon.csv` (1 Hz), journald boots -1/-2 of 2026-08-07.
+
+### Decisions already made by the owner (2026-08-07)
+
+- **Hardware sequencing: C-state limit first**, persistent, one-week soak; memtest → JEDEC →
+  reseat/RMA ladder only if resets continue. **No BIOS rung** (no newer firmware exists).
+- **Topology: keep the interactive pump; add auto-resume.** No permanent headless switch.
+
+### Pending fix plan (execute in order; [P] = propagate to all 5 copies*)
+
+*\*Propagation rule: neutral source `incredible_auto_dev/scripts/automation/...` + active copies in
+`trendora/` and `tapeology/` + vendored snapshots `{trendora,tapeology}/incredible_auto_dev/` —
+patch identical hunks, never whole-tree rsync; `cmp` before/after (all 5 currently byte-identical
+for the files below). Env files are machine/project-specific, never copied.*
+
+**Phase 0 — stabilization:** (1) kill orphan `iter52_health_drill.py` (was pid 291199 — verify cmdline
+first; stale after any reboot). (2) Stale dispatch `runs/goal-session-ops-hardening/dispatch/req.5-aC2vHX.*`
+(no `.res`): leave — `dispatch_channel_janitor` + `--resume` handle it; rm the trio only if the resumed
+pump stalls. (3) Reap escaped headed QA Chromes (`pgrep -af iad-qa-`). (4) [sudo] record pstore contents
+for the soak log.
+
+**Phase 1 — hardware soak ladder [sudo]:** (1) Install `/etc/systemd/system/iad-cstate-limit.service`
+(oneshot; `for f in /sys/devices/system/cpu/cpu*/cpuidle/state[2-9]/disable; do echo 1 > "$f"; done`
+plus a `logger` echo line; `WantedBy=multi-user.target` **and** the four sleep targets with matching
+`After=` so it re-asserts on resume), `enable --now`. Disables C2+C3 (acpi_idle). Self-verifying:
+every engine start's `host_state` event must show `cstate_disabled` `C2:1,C3:1`. Correct the stale
+"in flight" comment in `~/.config/iad/host-guard-host.env` (~line 76) to name the unit, dated.
+(2) Add `HOST_GUARD_MAX_ENGINES=1` there too, dated "revert on acceptance" (pauses tapeology's
+engine resumably during the soak). (3) If a FAULT reset occurs during week 1 → overnight MemTest86+
+(≥1 full pass; any error → rung 5). (4) Week 2 if still faulting: BIOS setup → JEDEC baseline
+(disable EXPO/XMP). (5) Escalation: SO-DIMM reseat → single-DIMM A/B → GEEKOM RMA.
+(6) **Acceptance** (runbook line 199): 7 consecutive days of `doctor.sh --only reset-reason` CLEAN;
+then revert (2).
+
+**Phase 2 — framework fixes [P]:** (1) `host-guard-adopt.sh:103-115` — the width-only early-exit is
+always taken at mask `0-15`, so the scope + `MemoryHigh`/`TasksMax` block (117–131) never runs and
+the 12G pump ceiling binds nothing. Add `_in_hg_scope()` (grep `/proc/<pid>/cgroup` for
+`chain-(pump|goal)-hostguard-`); early-exit only when in-scope AND width-ok, re-issuing
+`systemctl --user set-property` (idempotent refresh) on that path; always adopt when not in scope;
+skip the taskset walk at full width. Keep `MemoryHigh=12G`. (2) Mid-dispatch thermal defer:
+`host_guard_thermal_defer()` in `run-goal.sh` (~line 963), knob `HOST_GUARD_TCTL_DISPATCH_GATE`
+(default 0), poll until Tctl ≤ `TCTL_RESUME`, bound `HOST_GUARD_TCTL_DISPATCH_MAX_WAIT` (600 s,
+proceed loudly), emit `thermal_defer`; hook at top of `agent_with_quota_retry`
+(`lib/quota-retry.sh:1237`) via `declare -F … || true`. Defers next dispatch only. (3) `--headless`
+resume override in `run-goal.sh` (parse ~line 209; skip persisted-backend adoption at 291–304;
+document in usage header). (4) Optional: `HOST_GUARD_PUMP_HEADLESS_QA=1` → `unset DISPLAY
+WAYLAND_DISPLAY` in `host-guard-exec.sh` (~line 47). (5) Env values: trendora
+`project-extensions/host-guard/host-guard.env` → `HOST_GUARD_TCTL_PAUSE=85`, `TCTL_RESUME=75`,
+`TCTL_DISPATCH_GATE=1` (+ dated comment citing this incident); tapeology env → same; and a dated
+line in `docs/host-guard.md` §123 naming `iad-cstate-limit.service` [P]. **No mask/boost changes.**
+(6) `run-evals.sh` green + 5-copy `cmp` after patching.
+
+**Phase 3 — pump survives session death:** (1) QA Chrome headless for pump dispatches — supported
+via absent `DISPLAY`/`WAYLAND_DISPLAY` (`lib/common.sh:386-395`); delivered by the launch recipe
+below (`CHAIN_BQA_HEADED=1` stays the debug escape). (2) Standard launch becomes: `systemd-run
+--user --scope --unit=goal-pump-tmux env -u DISPLAY -u WAYLAND_DISPLAY tmux new-session -A -s
+goal-pump`, then `claude` + `/goal ops-hardening` inside — survives pty/SIGHUP cascade AND
+session-cgroup teardown (Linger=yes verified); after a compositor crash: re-login,
+`tmux attach -t goal-pump`. (3) Opt-in post-reset auto-resume: user unit
+`iad-goal-autoresume.service` gated on marker `~/.config/iad/goal-autoresume.armed`; if
+`session.json` status is `in_progress`/`AWAITING_HOST_GUARD`, exec `run-goal.sh --resume
+--session-id ops-hardening --headless`. **Verify first: headless spawns per-agent `claude -p` —
+API-key billing (`commands/goal.md:47-51`); if unacceptable, leave disarmed and resume via tmux.**
+
+**Verification:** C-state flags survive reboot + suspend/resume; `host_state` shows `C2:1,C3:1`;
+morning check = `doctor.sh --only reset-reason` CLEAN + no new postmortem + gapless hwmon.csv.
+Adopt fix: run adopt twice on a live pump → `systemctl --user show chain-pump-hostguard-<pid>.scope
+-p MemoryHigh -p TasksMax` = 12G/2048 both times. Thermal defer: throwaway session with
+`TCTL_PAUSE=1`, `DISPATCH_MAX_WAIT=10` → `thermal_defer` events, then proceeds. Session-kill drill:
+`pkill -f ghostty` + `loginctl terminate-session` mid-iteration → `tmux attach` shows pump alive,
+`engine.log` advancing. Headless QA: `pgrep -af iad-qa-` shows `--headless`, no new VSYNC lines in
+gnome-shell journal.
+
 ## Known Limitations
 
 1. **Service bootstrap**: QA expects `CHAIN_START_BACKEND_CMD` or `scripts/start-backend.sh`.
diff --git a/incredible_auto_dev/agents/goal-decomposer/agent.yaml b/incredible_auto_dev/agents/goal-decomposer/agent.yaml
index 77ce4f99..27dbcaf9 100644
--- a/incredible_auto_dev/agents/goal-decomposer/agent.yaml
+++ b/incredible_auto_dev/agents/goal-decomposer/agent.yaml
@@ -10,6 +10,6 @@ tools_allowed:
 - Grep
 - Bash
 - Write
-version: 2.5.0
-last_updated: '2026-07-29'
+version: 2.6.0
+last_updated: '2026-08-21'
 body: body.md
diff --git a/incredible_auto_dev/agents/goal-decomposer/body.md b/incredible_auto_dev/agents/goal-decomposer/body.md
index 5c9999c2..4bfb947e 100644
--- a/incredible_auto_dev/agents/goal-decomposer/body.md
+++ b/incredible_auto_dev/agents/goal-decomposer/body.md
@@ -130,6 +130,8 @@ The `Frontend Present:` field is implicit — if any Frontend item is listed, do
 
 Every FULL-depth spec MUST carry the machine-parseable metadata line `Full trigger: <1|2|3|4> — <one-line reason>`, naming which numbered full-depth trigger (see "Picking depth") applies. The evaluator's depth recommendation (inlined in your prompt) is **BINDING by default**: plan the recommended depth unless one of the four escape conditions holds — prior ESCALATE/REGRESSION verdict, prior coherence-audit FAIL, hardening cadence due, or a brand-new full-stack journey (backend AND frontend work with real Data-contract additions for a never-implemented target journey). The engine's deterministic arbiter re-validates a full spec against those same independent signals: a `Full trigger:` line alone does NOT grant full, and an unjustified full spec is demoted to lean.
 
+Two metadata lines exist that you must **NEVER** emit: `Depth enforcement: required` and `Maintenance isolation: required`. They are operator-only engine controls, not planning fields — the first makes full depth a hard requirement the engine will halt on rather than downgrade (`AWAITING_FULL_DEPTH`), the second forbids application-service boot, browser QA and the deterministic replay lane for the whole iteration. A spec you wrote is the one input you also author, so a self-written safety declaration is exactly the governor bypass anti-pattern 25 describes (`.claude/anti-patterns/25-self-justifying-governor-bypass.md`; SPEED-10's `Full trigger:` arm was superseded for the same reason). When you believe an iteration needs either control — a destructive migration, a repair pass on damaged data — say so in **BACKGROUND** in plain prose ("this iteration rewrites persisted rows; it should not run with the app booted") and leave the line to the human, who adds it to the spec or sets `CHAIN_REQUIRE_FULL_DEPTH` / `CHAIN_MAINTENANCE_ISOLATION` for the run.
+
 ## Picking target journeys (priority rubric — apply top-down)
 
 1. **Regressed journeys first.** Anything `regressed` outranks all new work — a shrinking product is worse than a slowly-growing one.
@@ -233,7 +235,7 @@ Always restate the anti-goals from `docs/goal.md` verbatim under Goal Mode Metad
 1. **Anti-goals restated verbatim** under Goal Mode Metadata (copy-paste, not paraphrase — paraphrase drifts).
 2. **Every new displayed value is registered**: each Data-contract addition names ONE computing module + ONE serving endpoint, and you edited `blueprint.md` to match. "None" is written explicitly when true.
 3. **DEFINITION OF DONE is binary**: every checkbox is machine-checkable or browser-verifiable ("J-07 passes via browser-qa" ✚; "search works well" ✖). If you can't phrase a criterion binarily, the scope is too vague — narrow it.
-4. **Depth is justified**: the evaluator's depth recommendation is binding by default — a full spec against a lean/evidence recommendation must satisfy an escape condition (prior ESCALATE/REGRESSION, prior coherence FAIL, cadence due, or a brand-new full-stack journey), not merely cite a trigger. Full cites which numbered trigger (1-4) in BACKGROUND AND carries the matching `Full trigger: <1|2|3|4> — <one-line reason>` metadata line (the engine demotes a full spec without it to lean); lean states "no full trigger holds" — needing unit tests is never the cited reason. ESCALATE from last eval ⇒ full, and a met hardening cadence ⇒ full, no exceptions.
+4. **Depth is justified**: the evaluator's depth recommendation is binding by default — a full spec against a lean/evidence recommendation must satisfy an escape condition (prior ESCALATE/REGRESSION, prior coherence FAIL, cadence due, or a brand-new full-stack journey), not merely cite a trigger. Full cites which numbered trigger (1-4) in BACKGROUND AND carries the matching `Full trigger: <1|2|3|4> — <one-line reason>` metadata line (the engine demotes a full spec without it to lean); lean states "no full trigger holds" — needing unit tests is never the cited reason. ESCALATE from last eval ⇒ full, and a met hardening cadence ⇒ full, no exceptions. Neither `Depth enforcement:` nor `Maintenance isolation:` appears anywhere in the spec — they are operator-only lines and writing one is a self-granted exception (anti-pattern 25); the need goes in BACKGROUND prose instead.
 5. **Target selection followed the priority rubric** — if you deviated (e.g., skipped a regressed journey), the reason is stated in BACKGROUND.
 6. **Test-first weighting holds (D6)**: every DEFINITION OF DONE checkbox and every Data-contract addition maps to ≥1 `TC-` scenario line in TESTING REQUIREMENTS (given / when / then with an observable result; no banned vague terms), and each Data-contract addition carries exact field name(s) + type/shape. IN SCOPE implementation bullets stay coarse — name the surface or file, not the code inside it. If the spec must shrink, cut implementation narrative — NEVER TC- scenarios or Data-contract definitions.
 
diff --git a/incredible_auto_dev/agents/goal-evaluator/agent.yaml b/incredible_auto_dev/agents/goal-evaluator/agent.yaml
index 860c3048..8659905d 100644
--- a/incredible_auto_dev/agents/goal-evaluator/agent.yaml
+++ b/incredible_auto_dev/agents/goal-evaluator/agent.yaml
@@ -10,6 +10,6 @@ tools_allowed:
 - Grep
 - Bash
 - Write
-version: 1.10.0
-last_updated: '2026-07-29'
+version: 1.12.0
+last_updated: '2026-08-21'
 body: body.md
diff --git a/incredible_auto_dev/agents/goal-evaluator/body.md b/incredible_auto_dev/agents/goal-evaluator/body.md
index 92f32755..2167ee5f 100644
--- a/incredible_auto_dev/agents/goal-evaluator/body.md
+++ b/incredible_auto_dev/agents/goal-evaluator/body.md
@@ -39,7 +39,7 @@ Follow methodology section A (evidence walk). In short: deterministic reports fi
 - Verify the screenshot in `reports/qa/<iter-name>-evidence/` actually shows the claimed end state
 - Cross-check against the prior journey state (inlined digest) to detect changes (newly passing, newly failing, regressed)
 
-Stable `passing`/`already_passing` journeys inside this iteration's **Required-still-passing set** are re-verified mechanically by the deterministic replay lane at BOTH depths — the lean executor and the full pipeline's browser-qa step (those with stored golden scripts; a required journey WITHOUT a golden is routed to the LLM browser-qa lane the same iteration). Their rows land in the merged `ui-test-results.md` you already read. The raw `regression-replay-results.md` is a lane artifact, not an input: where it disagrees with the merged file, the merged file wins — a dated reconciliation footer on the raw file records any replay FAIL the LLM lane overturned (golden-script false positive). A row whose verdict cell is `DEFERRED-BUDGET` (SPEED-15 trim rung 2) means the wall-clock iteration budget cut that journey's re-verification this run — it was NOT tested: the journey KEEPS its prior recorded status (never `regressed`/`failing`/`unknown` on that row alone), you note it as deferred, and the deterministic achievement gate blocks GOAL_ACHIEVED while any journey is deferred. Stable journeys OUTSIDE the set carry over unverified. Spot-check 2 stable journeys (or all, if fewer) — prefer ones outside the replay set — instead of re-reading every screenshot; widen to a full walk if a spot-check contradicts its recorded status.
+Stable `passing`/`already_passing` journeys inside this iteration's **Required-still-passing set** are re-verified mechanically by the deterministic replay lane at BOTH depths — the lean executor and the full pipeline's browser-qa step (those with stored golden scripts; a required journey WITHOUT a golden is routed to the LLM browser-qa lane the same iteration). Their rows land in the merged `ui-test-results.md` you already read. The raw `regression-replay-results.md` is a lane artifact, not an input: where it disagrees with the merged file, the merged file wins — a dated reconciliation footer on the raw file records any replay FAIL the LLM lane overturned (golden-script false positive). A row whose verdict cell is `DEFERRED-BUDGET` (SPEED-15 trim rung 2) means the wall-clock iteration budget cut that journey's re-verification this run — it was NOT tested: the journey KEEPS its prior recorded status (never `regressed`/`failing`/`unknown` on that row alone), you note it as deferred, and the deterministic achievement gate blocks GOAL_ACHIEVED while any journey is deferred. Stable journeys OUTSIDE the set carry over unverified. Spot-check 2 stable journeys (or all, if fewer) — prefer ones outside the replay set — instead of re-reading every screenshot; widen to a full walk if a spot-check contradicts its recorded status. A results table can also be empty because the lane was FORBIDDEN rather than cut: an all-SKIPPED `ui-test-results.md` whose `**Reason:**` line names **maintenance isolation** means this iteration kept full reviewer/QA/auditor/coherence depth while application-service boot, browser QA and the deterministic replay lane were prohibited by contract — not an infrastructure failure and not an absent frontend. Score it like `DEFERRED-BUDGET`: every journey KEEPS its prior recorded status (never `unknown`/`failing`/`regressed` on that basis alone), and the evaluation says outright that the iteration ran under maintenance isolation and which journeys therefore went unverified. It never runs the other way — an isolated iteration produced no browser evidence, so no journey may be promoted TO `passing`/`already_passing` on it, and a GOAL_ACHIEVED verdict here must name the earlier iteration whose evidence it rests on (the deterministic results gate counts only `FAIL` and `DEFERRED-BUDGET` cells, so an empty isolated table does not block you — that judgment is yours).
 
 Also read this iteration's `coherence.md` and note its verdict. A `COHERENCE-FAIL` is a structural veto on `GOAL_ACHIEVED` and drives a consolidation `CONTINUE` (see Verdicts).
 
@@ -269,9 +269,10 @@ or `CONTINUE`, `ESCALATE`, `REGRESSION`, `STALLED`.
 - Do NOT mark `GOAL_ACHIEVED` if any anti-goal violation is unresolved.
 - Do NOT mark `GOAL_ACHIEVED` if this iteration's `coherence.md` is `COHERENCE-FAIL`. A coherence failure is a structural veto — the product is incoherent (scattered navigation, a duplicate home, or the same value computed/served more than one way) even if all journeys pass. Drive a consolidation `CONTINUE` instead.
 - Do NOT mark `GOAL_ACHIEVED` if this iteration's `journeys-changed.md` lists any journey you did not re-verify against the current goal text this iteration — a pass earned on the old text is not a pass.
+- Do NOT mark `GOAL_ACHIEVED` on an iteration that ran under **maintenance isolation** on the strength of that iteration's own evidence — it produced none. If every Must-have journey was already passing beforehand, name the earlier iteration whose evidence the certification rests on (see the maintenance-isolation rule in step 1 and methodology A3's second carve-out).
 - Update `journey-history.json` atomically — write the full new state, do not partial-update.
 - Append to `evaluator-log.md` — never overwrite prior entries; this is the chronological record.
-- If you cannot find evidence for a journey (e.g., browser-qa-agent skipped it), set its status to `unknown` and note the gap in the evaluation. Do NOT guess.
+- If you cannot find evidence for a journey (e.g., browser-qa-agent skipped it), set its status to `unknown` and note the gap in the evaluation. Do NOT guess. The one exception is a lane withheld by contract: under maintenance isolation journeys keep their prior recorded status instead of going `unknown` (step 1).
 - Never recommend — and never score as blocking — a next iteration whose only content is evidence capture, screenshot retakes, or demo recording. Evidence gaps on working features ride the make-up lane (`evidence_makeup`, methodology A.7) or a `Depth: evidence` recommendation; prior evidence for unchanged code stays valid (methodology A.6). Goal-edit drift (`journeys-changed.md`) always outranks evidence durability.
 
 ## Token and Questioning Policy
diff --git a/incredible_auto_dev/benchmarks/experiments.md b/incredible_auto_dev/benchmarks/experiments.md
index 608807e1..058030b4 100644
--- a/incredible_auto_dev/benchmarks/experiments.md
+++ b/incredible_auto_dev/benchmarks/experiments.md
@@ -1014,3 +1014,98 @@ Entry format contract (grep-able; pinned by
   CHAIN_GOLDEN_AUTODERIVE=false / CHAIN_REPLAY_MASS_FAIL_BREAKER=false /
   CHAIN_UI_COMBINED=false / CHAIN_SKIP_TESTPLAN_IF_PRESENT=false — each knob
   reverts exactly one item.
+
+---
+
+## PRE bench-20260820-2246 · 2026-08-20T22:46:53Z
+- framework-sha: f8c98b95064070eba1a8f58df30e134749fde60d (dirty: false)
+- fixture: todo-app · max-iter 2
+- hypothesis: STYLE-1 G8 stage-1 ARM A = CONTROL at framework f8c98b9 (style knobs unset; same-sha baseline for arm B): chain reaches GOAL_ACHIEVED 3/3 within max-iter 2 with 0 attempt-1 review FAILs and 0 malformed verdicts; every claude_usage row reads output_style=default and carries no output_style_requested; zero iter_config / output_style_mismatch events; the developer iter-1 row is the baseline for arm B's token prediction. Deviation from the CAND-STYLE DoD, recorded: fixture A/B across two sessions instead of a same-session knob flip (both vendored real-session repos have live engines and HOST_GUARD_MAX_ENGINES=2), so the same-session cost guard is NOT exercised here; stage 2 = the real session after the next vendored sync.
+- metrics + prediction (mechanical --predict): journeys_passing_after>=3;final_status==GOAL_ACHIEVED;attempt1_review_fails==0;malformed_verdicts==0
+
+## POST bench-20260820-2246 · 2026-08-20T23:36:04Z
+- results: benchmarks/results/20260820-233604-f8c98b950640.json
+- headline: status=GOAL_ACHIEVED last_verdict=GOAL_ACHIEVED journeys=3/3 iters=2 engine_exit=0 wall=2951s cost=$15.16705
+- predicate: journeys_passing_after>=3 → true (journeys_passing_after=3)
+- predicate: final_status==GOAL_ACHIEVED → true (final_status='GOAL_ACHIEVED')
+- predicate: attempt1_review_fails==0 → true (attempt1_review_fails=0)
+- predicate: malformed_verdicts==0 → true (malformed_verdicts=0)
+- verdict-vs-prediction: CONFIRMED
+
+---
+
+## PRE bench-20260820-2337 · 2026-08-20T23:37:25Z
+- framework-sha: 3e165ba9a35f0216e8c742a8ac5c532184edd2a4 (dirty: false)
+- fixture: todo-app · max-iter 2
+- hypothesis: STYLE-1 G8 stage-1 ARM B = ARMED at framework f8c98b9 (CHAIN_OUTPUT_STYLES=true): every wave-1 dispatch (developer, qa, browser-qa-agent, orchestrator, ui-impact-analyst, ux-regression-reviewer) carries --settings outputStyle=Concise in its trace args AND reads back output_style=Concise from the init event; judges read output_style=default; zero output_style_mismatch; exactly one iter_config key=CHAIN_OUTPUT_STYLES per iteration; chain still GOAL_ACHIEVED 3/3 with 0 attempt-1 review FAILs, 0 malformed verdicts, 0 missing_evidence rows and no artifact-schema issues; developer iter-1 output_tokens -20..30 percent vs arm A with num_turns flat within 10 percent and cache_creation_input_tokens at most +25K per wave-1 dispatch; wall not worse than arm A +10 percent. Graded MANUAL with the CAND-STYLE read-out recipe; n=1 real iteration per arm, so the token clause is indicative only — the pass/fail clauses are the proof of mechanism.
+- metrics + prediction (mechanical --predict): journeys_passing_after>=3;final_status==GOAL_ACHIEVED;attempt1_review_fails==0;malformed_verdicts==0
+
+## POST bench-20260820-2337 · 2026-08-21T00:38:32Z
+- results: benchmarks/results/20260821-003832-3e165ba9a35f.json
+- headline: status=BUDGET_EXHAUSTED last_verdict=CONTINUE journeys=1/3 iters=2 engine_exit=0 wall=3667s cost=$19.847708
+- predicate: journeys_passing_after>=3 → false (journeys_passing_after=1)
+- predicate: final_status==GOAL_ACHIEVED → false (final_status='BUDGET_EXHAUSTED')
+- predicate: attempt1_review_fails==0 → true (attempt1_review_fails=0)
+- predicate: malformed_verdicts==0 → true (malformed_verdicts=0)
+- verdict-vs-prediction: MIXED
+- assessment 2026-08-21 (STYLE-1 G8 stage-1, arms A = bench-20260820-2246 control and
+  B = bench-20260820-2337 armed; same fixture, code-identical framework f8c98b9/3e165ba;
+  graded clause by clause, MANUAL for everything --predict cannot see):
+  (1) MECHANISM — PASSED on every clause: all six wave-1 agents (developer ×2, browser-qa-agent
+  ×2, orchestrator, ui-impact-analyst, qa, ux-regression-reviewer) requested `Concise` and read
+  back `output_style=Concise` from the CLI init event; every judge/showcase agent read back
+  `default`; `iter_config key=CHAIN_OUTPUT_STYLES` fired in both iterations; zero
+  `output_style_mismatch`, zero `missing_evidence`, zero `experiment_reverted`; tripwire quiet
+  in both arms; doctor `output-styles` PASS (armed) at engine boot; arm A's rows all
+  `default` with no `output_style_requested`. The `--settings` flag itself is not visible in
+  trace `args` (that field records the caller argv; injected flags such as --effort/--model
+  appear as separate fields) — graded by readback, follow-up filed.
+  (2) JOURNEYS 3/3 — REFUTED for arm B (1/3, BUDGET_EXHAUSTED after iter-1 ran FULL depth),
+  but NOT attributable to the style: arm A's browser-QA Chrome (profile
+  `superpowers/browser-profiles/iad-qa-scratch`, CDP 10133, started 23:56 during arm A)
+  outlived its engine and still held the pinned profile when arm B started, so arm B's Chrome
+  MCP lane got `ECONNREFUSED 127.0.0.1:10547` in BOTH iterations (iter-0 browser QA verdict
+  SKIPPED, iter-1 refused twice); the evaluator graded J-02/J-03 "partial" from the Playwright
+  demo walkthrough alone, whose step 4 (authored by the Default-styled demo-narrator) clicked
+  an already-done item's "✓" and never produced the mixed open+done state. The evaluator's own
+  checks (store probe, 14/14 tests, auditor stop/restart persistence) confirmed the product
+  works — "only the picture of it is missing". Same orphan class as the 2026-07-16 run-D/E
+  note; this time it cost the next session its browser lane.
+  (3) DEVELOPER TOKENS — MIXED (n=1 per cell): the only like-for-like cell, iter-0 (lean in
+  both arms): 14,967 → 8,416 output tokens (−44%), 35 → 28 turns (−20%), 184 → 109 s (−41%),
+  cache_creation 53.7K → 71.6K (+17.9K, inside the ≤+25K budget). iter-1 is depth-confounded
+  (arm A lean 29,518 tok / 45 turns / 292 s vs arm B FULL 33,098 / 46 / 325 s — the full-depth
+  developer consumes the orchestrator plan and a different input set). Session-level developer:
+  44,485 → 41,514 tokens (−7%), 80 → 74 turns, $2.70 → $2.82.
+  (4) FULL-DEPTH STYLED ROWS (first ever, n=1 each, no same-version control): orchestrator
+  7,991 tok / 11 turns (2026-07-16 unstyled, older framework: 18,570 / 22); qa 11,923 / 57
+  (14,186 / 74 over 2 invocations then); ui-impact-analyst 8,737 / 22 (4,352 / 15 — but the UI
+  step is now combined with test-plan authoring, so not comparable); ux-regression-reviewer
+  5,946 / 14 (3,456 / 11). Cross-version, indicative only.
+  (5) ARTIFACT THINNING — no deterministic signal fired (0 missing_evidence); dev handoff
+  iter-1 5,184 B (A) vs 4,307 B + 3,584 B frontend handoff (B, full depth); review PASS
+  attempt 1 in both arms (iter-0 of B; the full-depth iter-1 review emits no `review_verdict`
+  telemetry — pre-existing gap in review-phase.sh, so that metric is blind in full iterations);
+  audit PASS_WITH_GAPS with gaps "in evidence, not behaviour". WATCH ITEM: the styled QA report
+  claimed a Chrome screenshot confirmed the done treatment while its only screenshot showed an
+  unticked item — caught and corrected by the auditor and flagged by the styled
+  ux-regression-reviewer. n=1; cannot be attributed to Concise yet; count QA over-claims per
+  arm in stage 2. `artifact_schemas.py validate` flags the lean review reports and the QA report
+  in BOTH arms (`## Verdict` section rule vs the `**Verdict:**` first-line format) —
+  validator/format mismatch, pre-existing, not a style effect.
+  (6) WALL/COST — session wall 2951 s → 3667 s and $15.17 → $19.85, explained by the full-depth
+  iter-1 (7 extra agent rows ≈ $5.5 — auditor alone $3.69) and the blocked browser lane; iter-0
+  wall 14.7 m → 11.2 m (−24%).
+  (7) PRE-EXISTING DEFECTS SURFACED (framework, not style): (a) benchmark/browser-QA Chrome
+  outlives the engine and blocks the next session's pinned chrome-mcp profile; (b)
+  `closure_gate.py:66` matches the word "todo" case-insensitively as a TODO marker — the
+  closure gate fails on every iteration of a todo app (the evaluator correctly called it a
+  false alarm); (c) full-depth review emits no `review_verdict` telemetry; (d) injected
+  `--settings` not recorded in the trace row.
+  VERDICT: mechanism CONFIRMED; token clause indicative (−44% on the one like-for-like cell,
+  +18K cache creation); journey clause REFUTED for infrastructure reasons, not the style;
+  no flip decision from stage 1 (cross-session A/B, n=1, cost guard not exercised by design).
+  Stage 2 = the real same-session rollout per the CAND-STYLE DoD after the next vendored sync,
+  with the orphan-Chrome reap fixed first. Kept scratches:
+  /home/dennis-chan/.cache/iad/shared/bench-bench-20260820-2246.hC7Rqc (A),
+  /home/dennis-chan/.cache/iad/shared/bench-bench-20260820-2337.5aoUbc (B).
diff --git a/incredible_auto_dev/docs/READING-REPORTS.md b/incredible_auto_dev/docs/READING-REPORTS.md
index c87148eb..d7813590 100644
--- a/incredible_auto_dev/docs/READING-REPORTS.md
+++ b/incredible_auto_dev/docs/READING-REPORTS.md
@@ -109,6 +109,7 @@ terminal prints the same plain sentences next to them; this is the full list.
 | `AWAITING_GITHUB_AUTH` | Paused because the chain cannot push to GitHub (login missing or expired). Run `gh auth login`, then resume. |
 | `AWAITING_DISK` | Paused because this computer is low on disk space — the chain never builds in that state. Free space, then resume. |
 | `AWAITING_HOST_GUARD` | Paused because this computer's hardware protection is not in place — the chain never builds unprotected. Fix the printed reason (`project-extensions/host-guard/README.md`), then resume. |
+| `AWAITING_FULL_DEPTH` | Paused, not broken — this step needed its full, deeper review pass and could only have run a shorter one, so it stopped instead of checking less. Nothing was built or changed. Follow the reason printed in the terminal, then resume. |
 | `in_progress` | The session is running normally. |
 
 ### The evaluator's per-iteration verdict
diff --git a/incredible_auto_dev/docs/cli-providers.md b/incredible_auto_dev/docs/cli-providers.md
index dd67f4ea..d7059833 100644
--- a/incredible_auto_dev/docs/cli-providers.md
+++ b/incredible_auto_dev/docs/cli-providers.md
@@ -157,10 +157,13 @@ A goal-mode resume that passes a different `--cli` than the persisted value erro
 - **Claude is the default.** `CHAIN_CLI` defaults to `claude` if unset and no `--cli` flag is passed. Existing Claude-only callers see no behaviour change.
 - **`claude_with_quota_retry` is now an alias.** All step scripts continue to call it; behaviour now depends on `$CHAIN_CLI`.
 - **Codex's Claude-equivalent flags are translated.** The framework calls everything as `-p <prompt>`; `_codex_invoke` strips the `-p` and passes the prompt positionally to `codex exec`.
-- **Per-call env contracts (Claude-only).** `claude_with_quota_retry` reads two env vars before invoking the Claude CLI:
+- **Per-call env contracts (Claude-only).** `claude_with_quota_retry` reads these env vars before invoking the Claude CLI:
   - `CHAIN_CURRENT_AGENT=<name>` — set by each step-wrapper script (`dev-phase.sh`, `qa-phase.sh`, the inline orchestrator/iteration-summarizer/delivered blocks in `run-phase.sh` and `run-goal.sh`, etc.). Drives both the per-agent permission overlay (`agent_permissions.py disallowed/budget`) and the per-agent `--effort` resolution (`agent_permissions.py effort`).
   - `CHAIN_DISABLE_EFFORT_OVERRIDE=true` — restore `--effort max` for every agent regardless of the override map. Useful when troubleshooting whether the effort drop is degrading a structured agent's output.
-  Codex callers do not see these vars; the `--effort` flag is Claude-specific.
+  - `CHAIN_OUTPUT_STYLES=true` — arms the wave-1 table in `lib/agent_permissions.py` (`OUTPUT_STYLE_OVERRIDES`), sending a Claude Code output style with the invocation; default off, goal-mode only.
+  - `CHAIN_AGENT_OUTPUT_STYLE=<agent>=<Style>[,...]` — per-agent output-style experiment map, same grammar as `CHAIN_AGENT_EFFORT`; judges refused.
+  - `CHAIN_OUTPUT_STYLE_OVERRIDE=<Style>` — debug override, every agent including judges (loud NOTICE); wins over all other resolution; works outside goal mode too.
+  Codex callers do not see these vars; the `--effort` and `--settings` flags are Claude-specific.
 
 ---
 
diff --git a/incredible_auto_dev/docs/goal-mode-interactive.md b/incredible_auto_dev/docs/goal-mode-interactive.md
index 24565027..61e4e80f 100644
--- a/incredible_auto_dev/docs/goal-mode-interactive.md
+++ b/incredible_auto_dev/docs/goal-mode-interactive.md
@@ -122,8 +122,16 @@ programmatic path with an API key** (`run-goal.sh` without `--interactive`).
   the v2 skill landed (`skills/goal-interactive-dispatch.md`). The
   per-call hard timeout now *does* have an interactive equivalent —
   `CHAIN_DISPATCH_INFLIGHT_TIMEOUT` bounds a single claimed subagent (defaulting to
-  `CHAIN_CLAUDE_MAX_RUNTIME_SECONDS`). Per-agent tool/permission isolation and
-  per-agent model **are** preserved (via the agent frontmatter).
+  `CHAIN_CLAUDE_MAX_RUNTIME_SECONDS`). **Output styles are emulated, not native**:
+  Claude Code injects a style only into the default system prompt, which
+  Agent-tool subagents never receive — so when a style resolves (STYLE-1, opt-in)
+  the backend appends its body to the prompt under a
+  `# Output Style: <name> (engine-emulated on the interactive backend)` header,
+  and the trace row records `<name>(emulated)`. Only styles with a known body
+  (`Concise` plus any project `.claude/output-styles/*.md`) emulate; a valid style
+  without one warns, records `<name>(unemulated)`, and dispatches unstyled.
+  Per-agent tool/permission isolation and per-agent model **are** preserved (via
+  the agent frontmatter).
 - **Resume is iteration-level.** A session that stops mid-iteration re-runs that
   iteration from the decomposer on resume. `/goal-resume` first SIGTERMs any
   still-running prior engine for the session (via `runs/goal-session-<sid>/engine.pid`)
@@ -206,7 +214,9 @@ timestamped chain log is always at `runs/goal-session-<sid>/engine.log`.
 - **Richer in-session telemetry** — ~~the stream-json usage sidecar is absent in
   interactive mode~~ done (pump protocol v2 usage sidecar, TOKEN-5): per-agent
   token capture works interactively. Still reduced vs headless: no
-  `total_cost_usd` and no per-call `--effort` attribution.
+  `total_cost_usd`, no per-call `--effort` attribution, and output styles are
+  prompt-emulated rather than native (no `init.output_style` readback, so the
+  effective style cannot be proven per dispatch the way the headless path does).
 - **`.claude/` git retirement** — if the generated `.claude/` tree is later
   removed from git, ensure `.claude/commands/` is regenerated on setup (the
   runtime auto-sync keys on a single agent marker and will not create
diff --git a/incredible_auto_dev/docs/goal-mode-quickstart.md b/incredible_auto_dev/docs/goal-mode-quickstart.md
index 3c9f0b2b..a6beb1ff 100644
--- a/incredible_auto_dev/docs/goal-mode-quickstart.md
+++ b/incredible_auto_dev/docs/goal-mode-quickstart.md
@@ -110,6 +110,41 @@ Halt verdicts:
 - `AWAITING_INTENT_REVIEW` — only when you ran with `--intent-checkpoint` / `--intent-checkpoint-at N`: paused once mid-session for you to read `runs/goal-session-<sid>/intent-review.md` ("is this still the product you wanted?"); `--resume` to continue (counts as acknowledgment; fires once per session)
 - `AWAITING_GITHUB_AUTH` — paused at startup because per-iter push is on but a push to `origin` wouldn't authenticate (expired GitHub session, or no remote); fix auth (the run will offer to launch `gh auth login` for you when interactive) and `--resume`
 - `AWAITING_HOST_GUARD` — only on hosts that declare hardware caps (`project-extensions/host-guard/host-guard.env`): the hwmon forensics sampler could not be started, the engine's CPU-affinity wrap did not take effect, a declared launcher lost its HOST-GUARD cap block, or the interactive pump session could not be confined (the engine auto-confines a running pump in place first via `host-guard-adopt.sh`; relaunching through `scripts/automation/host-guard-exec.sh <cli>` is only needed if that fails); fix the printed reason and `--resume` — see `docs/host-guard.md`
+- `AWAITING_FULL_DEPTH` — only when full depth was declared a HARD requirement for the iteration (you set `CHAIN_REQUIRE_FULL_DEPTH=true`, or the spec carries a `Depth enforcement: required` line, or the iteration declared maintenance isolation — which requires full depth by contract) and the engine could not dispatch it. The engine halts BEFORE dispatch — no developer run, no browser/replay lane, no service boot, nothing changed — and writes `runs/goal-session-<sid>/iter-<N>/depth-requirement-unmet` with the reason, the step that caught it, and a `remedy=` line. The remedy depends on the step, and the engine prints it: `depth-arbiter` (the cost ladder could not grant full) — let the cadence window pass or re-run with `CHAIN_FULL_CADENCE_CAP=1`; `depth-parse` — fix the spec's `Depth:` line so it parses **before** resuming (a still-unparseable line makes `--resume` re-run the decomposer, which rewrites the spec and drops operator-only lines); `full-dispatch` — the installed `run-phase.sh` has no `--no-finalize` flag, so update/restore the framework checkout; `depth-legacy-allowlist` — add the qualifying `Full trigger: <1-4> — <reason>` line to the spec, or re-enable the deterministic arbiter (unset `CHAIN_DEPTH_ARBITER`; at iteration 0, which the arbiter exempts, only the `Full trigger:` line helps); `isolation-requires-full` — the spec declared maintenance isolation, which REQUIRES full depth, but resolved to lean/evidence: write `Depth: full` (plus a `Full trigger:` line when the arbiter is skipped) or drop the isolation declaration. Then `--resume`. Two things are NOT remedies: clearing `CHAIN_REQUIRE_FULL_DEPTH` or deleting the spec line (that deletes the check, not the cause), and `CHAIN_DEPTH_ARBITER=false` (it removes the precedence rung and the guard, and routes the iteration to the legacy allowlist)
+
+### Requiring full depth, or forbidding the app, for one iteration
+
+Two operator-only controls exist, both default-OFF. `Depth enforcement: required` makes full depth
+a hard requirement the engine pauses on rather than downgrades; `Maintenance isolation: required`
+keeps full reviewer/QA/auditor depth while forbidding application-service boot, browser QA, the
+deterministic replay lane and the demo showcase — for an iteration that repairs data the app would
+otherwise write to. Isolation implies the depth requirement, so an isolated spec must also say
+`Depth: full`; if it resolves to lean or evidence the engine pauses (`isolation-requires-full`)
+instead of running a lane it is not allowed to run.
+
+The **session-wide** form is the env one and is the only one with a guarantee that spans
+iterations: `CHAIN_REQUIRE_FULL_DEPTH=true` / `CHAIN_MAINTENANCE_ISOLATION=true` on the
+`run-goal.sh` command line. Note that the env form also binds iteration 0: the baseline
+spec is `Depth: lean` by contract, so a fresh session started with either env form set pauses
+`AWAITING_FULL_DEPTH` before the baseline runs — start the session without the env form and add
+it on the `--resume` that follows the baseline, or accept the pause and resume. The **per-iteration** form is a spec line, and the goal-decomposer is
+forbidden to write it (a governor that reads the governed agent's own prose is not a governor —
+anti-pattern 25), so a human adds it: let the loop pause once the decomposer checkpoint for that
+iteration exists, edit `docs/phases/goal-<sid>-iter-<N>.md` to add the line (and `Depth: full`),
+then `--resume`. Keep the spec's `Depth:` line parseable while you edit — a resume over an
+unparseable one re-runs the decomposer, which rewrites the whole spec and drops both operator-only
+lines (the engine warns loudly and records a `spec_regenerated` event when it is about to do that,
+but it cannot put the lines back).
+
+One boundary worth knowing: the background showcase tail forked at the END of iteration N−1 can
+still boot the app during iteration N's decomposer, until the engine reaps it at the
+showcase-join step. If you need NO app boot at all between two iterations, set the env form
+before the previous iteration ends, or run with `CHAIN_ASYNC_SHOWCASE=false`.
+
+Scope note: the FORBIDDEN half is enforced at the engine's own service and browser call sites, so
+nothing the pipeline drives can start the app. The developer/reviewer/auditor prompts do not yet
+carry the isolation note, so an agent asked to run the app by hand would not be told not to
+(tracked as a follow-up under CAND-MAINT-ISO).
 
 ## Common workflows
 
@@ -148,6 +183,30 @@ guard). Run ≥3 baseline iterations first; the telemetry tripwire auto-reverts
 the knob if a REGRESSION verdict, journey regression, or repeated first-attempt
 review FAILs appear while it is active.
 
+### Try the opt-in output-style experiment (guarded)
+
+```bash
+CHAIN_OUTPUT_STYLES=true ./scripts/automation/run-goal.sh --resume --session-id my-app
+```
+
+Arms the wave-1 table in `lib/agent_permissions.py` (`OUTPUT_STYLE_OVERRIDES`),
+sending Claude Code's built-in `Concise` output style to developer, qa,
+browser-qa-agent, orchestrator, ui-impact-analyst, and ux-regression-reviewer
+(judges are refused by a hardcoded guard). Run ≥3 baseline iterations with the
+knob OFF first — the cost tripwire needs that many same-session unstyled rows
+per agent to compute a baseline median before it can judge a styled one. It
+likewise needs ≥3 STYLED rows per agent before it can judge — expect no cost
+verdict before the third knob-on iteration. The telemetry tripwire auto-reverts
+the knob on a quality regression (as with `CHAIN_AGENT_EFFORT` above) AND on a
+cost regression (styled median `output_tokens` or `num_turns` more than 1.5x the
+unstyled baseline). Check for a style mismatch after a run:
+
+```bash
+jq -c 'select(.event=="output_style_mismatch")' runs/goal-session-my-app/telemetry.jsonl
+```
+
+An empty result means every dispatch's effective style matched what was requested.
+
 ### Recover from `BUDGET_EXHAUSTED`
 
 ```bash
diff --git a/incredible_auto_dev/docs/goal-mode-telemetry.md b/incredible_auto_dev/docs/goal-mode-telemetry.md
index a97e9d4a..41677c05 100644
--- a/incredible_auto_dev/docs/goal-mode-telemetry.md
+++ b/incredible_auto_dev/docs/goal-mode-telemetry.md
@@ -66,6 +66,7 @@ Records which pipeline was chosen for this iteration.
 |---|---|---|
 | `depth` | string | `lean` or `full` |
 | `target_journeys` | array of strings | Journey IDs this iteration targets (e.g., `["J-01","J-03"]`) |
+| `maintenance_isolation` | string | The RAW `${CHAIN_MAINTENANCE_ISOLATION:-false}` literal as it stands after `apply_maintenance_isolation_from_spec` has materialized any `Maintenance isolation: required` spec line — `"true"` when the spec declared it, `"false"` when unset, but any operator-set truthy value (`"1"`, `"yes"`, `"on"`, `"required"`, `"TRUE"`) is emitted verbatim, so consume it with the same truthy set the engine uses rather than `== "true"`. A string on both the jq and the jq-less path, never a boolean. The only per-iteration record that the app/browser lanes were withheld by contract |
 
 ### `agent_invocation_start`, `agent_invocation_end`
 Wrap each agent call inside an iteration (developer, reviewer, browser-qa-agent, etc.).
@@ -118,8 +119,9 @@ Written when a hard halt fires before normal `iter_end`.
 
 | Field | Type | Description |
 |---|---|---|
-| `reason` | string | `BUDGET_EXHAUSTED` \| `STALLED` \| `REGRESSION_HALT` \| `ABORTED` |
-| `detected_at_step` | string | Where the halt was detected (e.g., `pre_decomposer`, `post_evaluator`) |
+| `reason` | string | Includes `BUDGET_EXHAUSTED`, `STALLED`, `REGRESSION_HALT`, `ABORT_MALFORMED`, `DECOMPOSER_FAILED`, `GATE_BLOCKED_POST_DECOMPOSE`, `machine_reset`, and the resumable pauses `AWAITING_BLUEPRINT_APPROVAL`, `AWAITING_INTENT_REVIEW`, `AWAITING_PUMP`, `AWAITING_GITHUB_AUTH`, `AWAITING_DISK`, `AWAITING_HOST_GUARD`, `AWAITING_FULL_DEPTH`. `ABORTED` is a session *status* only — the SIGINT trap writes the summary, not a halt event. Not a closed enum: `grep -n 'record_telemetry_event "halt"' scripts/automation/run-goal.sh` is the ground truth |
+| `detected_at_step` | string | Where the halt was detected (e.g., `pre_decomposer`, `post_evaluator`; `AWAITING_FULL_DEPTH` uses `depth-arbiter`, `depth-parse`, `full-dispatch`, `depth-legacy-allowlist` or `isolation-requires-full` — the five sites that could otherwise have silently run at less than the required depth) |
+| `demotion_reason` | string | `AWAITING_FULL_DEPTH` only: why full depth could not be dispatched — `arbiter-demotion:<rung>`, `unparseable Depth line in <spec-path>`, `run-phase.sh lacks --no-finalize`, `legacy-allowlist:no-qualifying-trigger (…)`, or `maintenance isolation requires full depth but this spec resolved to <depth>`. Mirrors the `reason=` field of `iter-<N>/depth-requirement-unmet`, which also carries a `remedy=` line naming the one action that unblocks that specific step |
 
 ### `iter_push` (opt-in)
 Written by `run-goal.sh` after each iteration when `--push-per-iter` is enabled. One event per iteration. Captures whether the per-iter commit + push succeeded and which branch received the commit.
@@ -151,6 +153,9 @@ Written by `claude_with_quota_retry` after a successful Claude invocation when `
 | `num_turns` | number | Number of model turns (assistant/tool_use cycles) |
 | `is_error` | boolean | True if the result event was an error |
 | `subtype` | string | `success` \| `error_max_turns` \| etc. |
+| `output_style` | string \| null | The **effective** Claude Code output style, read from the stream-json `system/init` event by `lib/claude_stream_renderer.py` and carried in through the usage sidecar. `default` when no style is active; null on CLIs that do not report it (older `claude`, Codex) — null means *unknown*, never "default" |
+| `available_output_styles` | string \| null | Comma-joined list of the output styles Claude Code reports as available, read from the same stream-json `system/init` event by `lib/claude_stream_renderer.py` (`:189-190`) and carried in through the usage sidecar. null when the CLI does not report the field — observed on CLI 2.1.237 |
+| `output_style_requested` | string | The style the engine **requested** for this dispatch (STYLE-1; e.g. `Concise`). Absent when no style was requested. Interactive-backend rows read `<name>(emulated)` — subagents never receive a style natively, so the seam appends the emulation block to the prompt instead. Compare against `output_style` to know whether the arm actually ran. The trace row (`trace/trace.jsonl`) carries the same `output_style_requested` key next to its effective `output_style`. |
 
 Enabled by default headless; opt out with `export CHAIN_TELEMETRY_TOKENS=false`. To opt out of cache hygiene (`--exclude-dynamic-system-prompt-sections`): `export CHAIN_CLAUDE_DISABLE_CACHE_HYGIENE=true`.
 
@@ -165,11 +170,14 @@ python3 scripts/automation/lib/analyze_telemetry.py runs/goal-session-<sid>/tele
 |---|---|---|
 | `step_skipped` | `goal-iter-lean.sh`, `run-goal.sh`, `run-phase.sh` | `{step, iter_name|phase, reason}` — a step was skipped instead of dispatched. Reasons: `checkpoint` (resume reused a completed step), `zero-change` (SPEED-14), `iter-budget-trim` (SPEED-15 rungs 3a/3b: `test-plan`/`ux-regression`, payload key `phase`), `ui-combined` (SPEED-24: `ui-test-design` folded into the ui-impact dispatch, payload key `phase`) |
 | `dispatch_wait` | `lib/interactive-dispatch.sh` | `{agent, wait_seconds, run_seconds, status, rc}` — pickup-wait vs run split per interactive dispatch attempt (`ok` \| `pickup-timeout` \| `inflight-timeout` \| `inflight-timeout-requeued`) |
-| `review_verdict` | `goal-iter-lean.sh` | `{verdict, attempt, iter_name}` — reviewer outcome per attempt (feeds the tripwire) |
-| `iter_config` | `run-goal.sh` | `{key, value}` — an opt-in experiment knob (e.g. `CHAIN_AGENT_EFFORT`) was active this iteration |
+| `review_verdict` | `lib/telemetry.sh` `record_review_verdict` (called by `goal-iter-lean.sh` at both review attempts and by `run-phase.sh` Step 3 in full-depth iterations; the Step 7/9 hardening reviews of phase mode emit nothing) | `{verdict, attempt, iter_name}` — reviewer outcome per attempt (feeds the tripwire). `verdict` is `PASS` \| `PASS_WITH_NOTES` \| `FAIL`, or `""` when the dispatched reviewer returned without a parseable `**Verdict:**` line (quota pauses and resume-skipped reviews emit no event) |
+| `iter_config` | `run-goal.sh` | `{key, value}` — an opt-in experiment knob was active this iteration. One event per active knob: `CHAIN_AGENT_EFFORT` carries the effort map; `CHAIN_OUTPUT_STYLES` (STYLE-1) carries the whole arm string (`CHAIN_OUTPUT_STYLES=… CHAIN_AGENT_OUTPUT_STYLE=… CHAIN_OUTPUT_STYLE_OVERRIDE=…`, sanitized). Any `iter_config` event marks the iteration knob-active for the tripwire window |
 | `golden_coverage` | `goal-iter-lean.sh`, `browser-qa-phase.sh` (goal iterations) | `{passing, missing_goldens, iter_name}` — PASSing journeys still lacking a replay golden (also persisted to `state/golden-gaps`, SPEED-23) |
 | `experiment_reverted` | `run-goal.sh` | `{key, value}` — the tripwire auto-reverted an experiment knob |
+| `spec_regenerated` | `run-goal.sh` | `{iter_name, dropped}` — a resume re-ran the goal-decomposer over an existing spec that carried an operator-only line (`Maintenance isolation: required` / `Depth enforcement: required`), which regeneration destroys because the decomposer is forbidden to write them (anti-pattern 25). Paired with a loud `WARNING: regenerating … will DROP operator-only line(s)` on stderr. `dropped` names the operative line found; the probe uses the predicates, so when both are present the isolation one is named |
 | `depth_full_granted` / `depth_demoted` | `run-goal.sh` | `{reason, prior_verdict, prior_depth}` — the SPEED-20 deterministic depth arbiter granted a spec-requested full (`prior-verdict-*`, `prior-coherence-fail`, `cadence-due`, `new-fullstack-journey`) or demoted it to lean (`budget-breach`, `full-cap`, `evaluator-requested-*`, legacy `no-full-trigger`) |
+| `depth_cost_overridden` | `run-goal.sh` | `{requirement:"hard-full-required", overridden_cost_rung, prior_verdict, prior_depth}` — the iteration was hard-required full (`CHAIN_REQUIRE_FULL_DEPTH` or a `Depth enforcement: required` spec line) and the precedence rung overrode a COST rung that would otherwise have demoted it: `budget-breach`, `full-cap`, or `evaluator-requested-lean`/`evaluator-requested-evidence`. Evidence only — the overridden rung's on-disk marker (e.g. the previous iteration's `budget-breached`) is deliberately left untouched. Without jq the payload carries `requirement` + `overridden_cost_rung` only |
+| `maintenance_isolation_refused` | `lib/common.sh` `maintenance_isolation_refuse` (called from `_boot_shared_services`, `ensure_services_running`, `browser-qa-phase.sh`, `replay_lane_partition_and_verify`, `demo-phase.sh` and `run-goal.sh`'s showcase-join) | `{operation, detail}` — a path forbidden under maintenance isolation was reached and REFUSED rather than degraded. `operation` is the refusing site (`ensure_services_running`, `_boot_shared_services`, `browser-qa-phase`, `replay_lane_partition_and_verify`, `demo-phase`, `demo_runner`, `demo golden auto-derive`, `async-showcase-join`). The same call appends a tab-separated `<utc-timestamp>\toperation=…\tdetail=…` line to `runs/goal-session-<sid>/iter-<N>/maintenance-isolation-refusals`, so the refusal survives even where telemetry is unavailable |
 | `iter_budget` | `lib/common.sh` (any budget-aware script) | `{budget, elapsed, mode, at_step}` — first over-budget check of the process (SPEED-15; defaults 3600s/trim) |
 | `iter_budget_trim` | `run-goal.sh`, `goal-iter-lean.sh`, `run-phase.sh`, `browser-qa-phase.sh` | `{rung}` — a trim rung actually shed work (`showcase-defer`, `replay-narrow`, `testplan-skip`, `ux-regression-skip`) |
 | `goal_slice_fallback` | `lib/common.sh` (executor dispatch sites) | `{iter_name, rc}` — the TOKEN-10 executor goal-slice build failed; the dispatch fell back loudly to the full `docs/goal.md` |
@@ -178,13 +186,24 @@ python3 scripts/automation/lib/analyze_telemetry.py runs/goal-session-<sid>/tele
 | `replay_mass_fail_voided` / `replay_mass_fail_confirmed` | `lib/replay-lane.sh` / `goal-iter-lean.sh` | `{iter_name, journeys, canaries}` — SPEED-22 mass-false-FAIL breaker outcome: green canaries voided the replay FAILs (drift), or a canary failure kept the full re-confirm path |
 
 ### `missing_evidence` (REL-11 tripwire)
-Written when a dispatch returns — any exit code, including 0 — without its expected report artifact on disk: full-mode QA (`qa-phase.sh`), the lean browser-qa LLM lane (`goal-iter-lean.sh`; quota pauses excluded), and the retro-analyst (`run-goal.sh`). The telemetry counterpart of the loud `[missing-evidence]` stderr banner (`lib/common.sh` `warn_missing_evidence`). Non-blocking — a tripwire, never a gate.
+Written when a dispatch returns — any exit code, including 0 — without its expected report artifact on disk: full-mode QA (`qa-phase.sh`), the lean browser-qa LLM lane (`goal-iter-lean.sh`; quota pauses excluded), the retro-analyst (`run-goal.sh`), the developer's dev handoff (`goal-iter-lean.sh` lean, `dev-phase.sh` full), the ui-impact-analyst's user-visible-changes report (`ui-impact-phase.sh`, alongside the SKIPPED stub), and the ux-regression review (`ux-regression-phase.sh`). The telemetry counterpart of the loud `[missing-evidence]` stderr banner (`lib/common.sh` `warn_missing_evidence`). Non-blocking — a tripwire, never a gate.
 
 | Field | Type | Description |
 |---|---|---|
-| `agent` | string | Dispatching agent whose report is missing (`qa` \| `browser-qa-agent` \| `retro-analyst`) |
+| `agent` | string | Dispatching agent whose report is missing (`qa` \| `browser-qa-agent` \| `retro-analyst` \| `developer` \| `ui-impact-analyst` \| `ux-regression-reviewer`) |
 | `path` | string | The expected report path that was absent |
 
+### `output_style_mismatch` (STYLE-1)
+Written when the output style the engine requested for a dispatch is **not** the one that actually ran. The headless seam (`lib/quota-retry.sh`) compares the requested name against the effective `output_style` from the stream-json `init` event after each invocation — the CLI ignores an unknown or unapplied `--settings` style silently, so this readback is the only ground truth. The interactive seam (`lib/interactive-dispatch.sh`) writes it when a valid style has no emulation text and the dispatch therefore went out unstyled. Non-blocking — the work already happened — but **any occurrence invalidates that dispatch's membership in the arm**: exclude it before comparing styled vs unstyled numbers.
+
+| Field | Type | Description |
+|---|---|---|
+| `agent` | string | The agent context of the dispatch |
+| `requested` | string | The style the engine asked for (empty = none) |
+| `effective` | string | The style that actually ran (`default` when none; empty on the interactive backend, where there is nothing to read back) |
+| `backend` | string | `headless` \| `interactive` |
+| `reason` | string | Interactive only: `no-emulation-text` |
+
 ### Wall-time report and tripwire
 
 Where do the ~2 hours of an iteration go? Per-iteration wall breakdown (per-agent
@@ -200,8 +219,23 @@ full report in `runs/goal-session-<sid>/summary.md`; the per-iteration HTML page
 carries it as a "Timing" accordion.
 
 The experiment tripwire (exit 3 = TRIP) judges the last `--window` knob-active
-iterations; `run-goal.sh` runs it each iteration while `CHAIN_AGENT_EFFORT` is
-set and auto-reverts the knob on TRIP:
+iterations; `run-goal.sh` runs it each iteration while `CHAIN_AGENT_EFFORT` or
+any `CHAIN_OUTPUT_STYLE*` knob is set, and auto-reverts every active knob on
+TRIP (one `experiment_reverted` event per key):
+
+- **Quality dimension** — any `REGRESSION` verdict, any journey regression, an
+  unparseable review verdict, or first-attempt review `FAIL`s in ≥2 iterations of
+  the window. "Unparseable" is a `review_verdict` event with an empty `verdict`:
+  `goal-iter-lean.sh` (and `run-phase.sh` Step 3 in full-depth iterations, via
+  the same helper) writes one when the reviewer was dispatched and came back
+  without a parseable `**Verdict:**` line (quota pauses excluded, and a
+  resume-skipped review emits no event at all).
+- **Cost dimension** (ground rule D5: an earlier "be terser" change *increased*
+  turns and roughly doubled output tokens) — per agent, the median of
+  `usage.output_tokens` and of `num_turns` over the styled `claude_usage` rows
+  in the window (`output_style_requested` set) against the same agent's unstyled
+  rows in the session. TRIPs above **1.5×**, and only with **≥3 rows on each
+  side**. Reasons are prefixed `cost:`.
 
 ```bash
 python3 scripts/automation/lib/analyze_telemetry.py --tripwire --window 3 runs/goal-session-<sid>/telemetry.jsonl
diff --git a/incredible_auto_dev/docs/host-guard.md b/incredible_auto_dev/docs/host-guard.md
index 083d66d6..92cbce3c 100644
--- a/incredible_auto_dev/docs/host-guard.md
+++ b/incredible_auto_dev/docs/host-guard.md
@@ -28,7 +28,7 @@ disables everything.
 | `HOST_GUARD_REQUIRE_MARKERS` + `HOST_GUARD_MARKER_FILES` | require HOST-GUARD cap blocks in listed launcher scripts | project-specific |
 | `HOST_GUARD_TCTL_PAUSE` / `_RESUME` / `_MAX_WAIT` | thermal gate thresholds (°C, °C, s) | `90` / `80` / `1800` |
 | `HOST_GUARD_SAMPLER_INTERVAL` / `_MAX_BYTES` | forensics sampler cadence / csv ring size | `1` / `10485760` |
-| `HOST_GUARD_BROWSER_CONFINE` | `0` disables the QA-browser confinement pass | `1` (default) |
+| `HOST_GUARD_BROWSER_CONFINE` | `0` disables passes A–C of the QA-browser pass; `--reap` (pass D) is governed by `CHAIN_BQA_REAP` / `CHAIN_BQA_REAP_ON_EXIT` | `1` (default) |
 
 ## Machine-global aggregate budget
 
@@ -215,6 +215,43 @@ sysfs 32×`0`; per the rule above in reverse, later boots must show ZERO
 2026-08-08→09 — in progress**, then JEDEC baseline → SO-DIMM reseat/swap →
 GEEKOM RMA. Full record: `~/.cache/iad/host-guard/soak-log.md`.
 
+2026-08-09→11 OUTCOME — the physical ladder is exhausted short of RMA, and the
+owner has declined RMA. Rung 3 memtest86+: **CLEAN, 26 passes / 20.5 h at
+~90 °C** — RAM cells and IMC exonerated, and a discriminator: the memtest
+environment (no OS, no DF/UCLK P-state transitions) never resets, while Linux
+resets at near-idle and load alike. JEDEC rung moot (already at baseline 4800).
+SO-DIMM reseat 2026-08-09 did NOT hold: two more fault resets on 2026-08-10
+(hwmon-anchored 12:08:35 at 58 °C/16 W cooling, and 22:30:02 at 67 °C/22 W).
+Full-journal sweep found **16 fault resets since 2026-07-20**; authoritative
+table: `~/.cache/iad/host-guard/reset-ledger.md`.
+
+**Detector fix (2026-08-11).** The 22:30 reset exposed a blind spot: its decode
+line landed in an intermediate boot that was then shut down cleanly, and the
+old boot-0-only read reported CLEAN forever — never freezing the evidence.
+`reset-forensics.sh` now walks every boot newer than a persisted watermark
+(`~/.cache/iad/host-guard/reset-watermark`), reports the newest unprocessed
+fault, and `ensure-postmortem` writes one bundle per fault in the gap before
+advancing the watermark. `check` never writes. The `streak` subcommand keeps
+"has this host faulted recently" answerable after the freeze (doctor's
+ras-logging row uses it).
+
+**Mitigation rung A (2026-08-11, running): fabric-pin.** The last untested
+OS-active-only variable the discriminator points at: under `auto` DPM the
+fabric clock steps 500/1600/1960 MHz. The root unit `iad-fabric-pin.service`
+runs `scripts/automation/host-guard/fabric-pin.sh apply` at boot, pinning
+fclk/mclk/socclk at top P-state via `power_dpm_force_performance_level=high`
+(a few watts of idle cost; `release` or unit removal rolls back). Verify ONLY
+by tag + sysfs: `journalctl -t iad-fabric-pin -b 0` and the `*` on the TOP row
+of `pp_dpm_fclk`. Acceptance unchanged: seven consecutive CLEAN days at the
+usual ≥1-fault/day baseline. The BIOS-memory rung is UNAVAILABLE on this host
+(owner confirmed 2026-08-11: the GEEKOM BIOS locks memory/DF settings), so
+falsified → `pcie_aspm=off`, then accept-and-tolerate (~20 s self-recovery,
+manual engine resume). Note the soak boot also runs BIOS performance mode
+QUIET (Balanced→Quiet during the Aug 10→11 power-off; observed envelope
+44 W/61 °C vs 63 W/90 °C on Balanced), so the soak tests pin+Quiet combined —
+the owner's planned pin-disable at soak end A/Bs Quiet alone. Soak journal:
+`~/.cache/iad/host-guard/soak-log.md` §2026-08-11.
+
 `doctor.sh --only ras-logging` verifies what it can read without root (the
 journald drop-in and the rasdaemon unit) and stays silent on hosts that have no
 reset history.
@@ -283,14 +320,24 @@ uses), dropping GPU compositing and the raster thread pool. Screenshots are
 unaffected. `CHAIN_BQA_HEADED=1` restores a visible browser for debugging;
 `CHAIN_BQA_REAP=1` additionally terminates this project's QA browsers when an
 engine-mode phase finishes (default is leave-warm — a cold start costs seconds
-and an idle browser inside the mask costs nothing).
+and an idle browser inside the mask costs nothing). Without a `host-guard.env`,
+`browser-confine.sh` skips confinement but `--reap` still runs (G8 stage 1: a
+detached QA browser from a finished session blocked the next session's lane).
 
 | Var | Meaning | Default |
 |---|---|---|
-| `CHROME_WS_PROFILE` / `CHROME_WS_PORT` | pinned QA browser identity, per project and lane (`iad-qa-<project>` on `10000+hash`, the qa lane on `11000+hash`) | set by `ensure_qa_browser_env` |
+| `CHROME_WS_PROFILE` / `CHROME_WS_PORT` | pinned QA browser identity, per project path and lane (`iad-qa-<project>-<offset>` on `10000+offset`, the qa lane `iad-qa-<project>-<offset>-qa` on `11000+offset`; `<offset>` = the same path hash for both, so a name collision between two projects cannot split profile from port) | set by `ensure_qa_browser_env` |
 | `CHAIN_BQA_HEADED` | `1` keeps a visible browser in engine mode | `0` |
 | `CHAIN_BQA_REAP` | `1` reaps this project's QA browsers at phase end (engine mode only) | `0` |
-| `HOST_GUARD_BROWSER_CONFINE` | `0` disables the pass entirely | `1` |
+| `CHAIN_BQA_REAP_ON_EXIT` | `1` (default) reaps this project's QA browsers when the headless engine exits — leave-warm is about the next dispatch of the same engine, which at exit no longer exists; never in the interactive backend, and skipped when another goal-session engine lock in this checkout names a live pid. Reap-only (passes A–C never run at exit). Costs up to ~11 s of exit latency (a `flock -w 5` wait for a concurrent confine pass, then TERM→3 s→KILL per own browser, two lanes), incurred *after* the engine lock is released so it cannot refuse a resume | `1` |
+| `HOST_GUARD_BROWSER_CONFINE` | `0` disables passes A–C; `--reap` is governed by `CHAIN_BQA_REAP` / `CHAIN_BQA_REAP_ON_EXIT` | `1` |
+
+**One-time migration.** A browser still running under the pre-offset name
+(`iad-qa-<project>`) is *foreign* to the new pass — it is never reaped, yet it
+still holds the pinned DevTools port the new name will dial, which is exactly the
+split that ends in `ECONNREFUSED`. Close any old-name browsers once before the
+first post-upgrade session (or just restart them):
+`pgrep -af 'iad-qa-' | grep -v -- '-[0-9]\{1,3\}\( \|-qa\)'`.
 
 Pump sessions deliberately get **no** profile pin. A Claude Code `env` setting
 overrides the inherited process environment, so a pinned value there would clobber
diff --git a/incredible_auto_dev/docs/improvement-roadmap.md b/incredible_auto_dev/docs/improvement-roadmap.md
index a678f754..0699188f 100644
--- a/incredible_auto_dev/docs/improvement-roadmap.md
+++ b/incredible_auto_dev/docs/improvement-roadmap.md
@@ -88,10 +88,12 @@ do not resurrect them without new evidence):
 - **D5** Do not cap thinking/effort to cut cost — on ANY agent, not only judges (D4).
   Superpowers 6 measured the failure mode: capping thinking increased turn count and
   ~doubled output tokens (cost went UP, not down). Judges are hardcoded-refused
-  (`JUDGE_AGENTS`, `scripts/automation/lib/agent_permissions.py:262-264`); for
+  (`JUDGE_AGENTS`, `scripts/automation/lib/agent_permissions.py:296-298`); for
   non-judges the `CHAIN_AGENT_EFFORT` knob stays opt-in and must carry a COST tripwire
-  (REL-8) — the current quality-only tripwire (`lib/analyze_telemetry.py:441-466`)
-  cannot see this failure mode.
+  (REL-8) — the quality tripwire (`lib/analyze_telemetry.py:497-527`) cannot see the D5
+  failure mode; the STYLE-1 cost dimension (`evaluate_cost_tripwire`,
+  `lib/analyze_telemetry.py:550-581`) keys on `output_style_requested`, so it is blind
+  to `CHAIN_AGENT_EFFORT` — REL-8 still owed.
 - **D6** Do not impose word/length budgets on specs or plans. If a spec must shrink,
   cut implementation narrative — NEVER test scenarios or interface/data-contract
   definitions (Superpowers 6: a plan word-budget cut test content −62%; tests and
@@ -1202,8 +1204,11 @@ benchmark (or a real session's telemetry) before AND after (G8).
   allowlist's `Full trigger:` arm is self-certifying — the decomposer wrote a
   qualifying line into every spec and full ran 5-of-6 (anti-pattern 25).
   SPEED-20's deterministic arbiter is now the default path; this allowlist
-  survives verbatim as the arbiter's PRIOR_DEPTH=full rung and as the
-  `CHAIN_DEPTH_ARBITER=false` escape hatch.
+  survives as the arbiter's PRIOR_DEPTH=full rung and as the
+  `CHAIN_DEPTH_ARBITER=false` escape hatch — no longer verbatim: since
+  CAND-MAINT-ISO fix 1 it carries a fail-closed pause for hard-required specs
+  (`depth-legacy-allowlist`), because skipping the arbiter used to skip the
+  requirement with it.
 
 ### SPEED-11 · Lean replay-fork default flip (off→replay)
 - **Priority:** P1 · **Effort:** S · **Risk:** LOW-MED · **Status:** IN-PROGRESS —
@@ -1411,7 +1416,9 @@ benchmark (or a real session's telemetry) before AND after (G8).
 - **Verify:** `bash tests/automation/test-depth-arbiter.sh` (29 cases) ·
   `test-depth-cadence.sh` still green · run-evals.
 - **Files:** `run-goal.sh`, `lib/common.sh`, `agents/goal-decomposer/*`, tests.
-- **Rollback:** `CHAIN_DEPTH_ARBITER=false` (legacy SPEED-10 allowlist verbatim);
+- **Rollback:** `CHAIN_DEPTH_ARBITER=false` (legacy SPEED-10 allowlist — which now
+  carries a fail-closed pause for hard-required specs, so the knob is not an escape
+  from `AWAITING_FULL_DEPTH`);
   `CHAIN_FULL_CADENCE_CAP=0` removes just the window cap.
 - **Stop-and-ask:** a demoted full producing an ESCALATE, or the full ratio
   staying >1-in-4 over the next 6 real iterations (the PRE entry grades it).
@@ -2444,7 +2451,7 @@ benchmark (or a real session's telemetry) before AND after (G8).
   and ~doubled output — a COST backfire. Our tripwire watches quality only. Anchors
   verified 2026-07-07 @ `eb5c8f9`.
 - **Problem:** the `CHAIN_AGENT_EFFORT` experiment auto-reverts on quality signals only
-  (`evaluate_tripwire()`, `lib/analyze_telemetry.py:441-466`: any REGRESSION verdict,
+  (`evaluate_tripwire()`, `lib/analyze_telemetry.py:497-527`: any REGRESSION verdict,
   any regressed journey, ≥2-of-3 first-attempt review FAILs). If lowering an agent's
   effort doubles its output tokens — the measured Superpowers failure mode — the
   tripwire never fires and the "saving" quietly costs more than baseline.
@@ -2456,7 +2463,9 @@ benchmark (or a real session's telemetry) before AND after (G8).
   (`analyze_telemetry.py` `by_agent` `:96`, `output_tokens` `:53`, per-agent rows
   `:212`, JSON `:227`). The knob is headless-only (`agent_permissions.py:272-273`)
   and headless always emits `claude_usage` events — the data is guaranteed present
-  exactly when the knob is active.
+  exactly when the knob is active. STYLE-1 (2026-08-20) landed `evaluate_cost_tripwire`
+  (`lib/analyze_telemetry.py:550-581`) for the output-style knob, keyed on
+  `output_style_requested`; REL-8 generalizes it to the effort arm.
 - **Change spec:**
   1. In `evaluate_tripwire()`: parse which agents the knob names from the `iter_config`
      event payload; per knob-active iteration compute those agents' output-token
@@ -3779,6 +3788,415 @@ but appreciated.
 - **Verify idea:** run-evals + one fixture goal-iteration dry parse with a Reference
   line present and absent.
 
+### CAND-MAINT-ISO · Hard full-depth requirement + maintenance isolation (LANDED 2026-08-21 — reverse-ported from trendora)
+- **Priority:** P1 · **Effort:** M · **Risk:** LOW · **Status:** DONE 2026-08-21 on branch
+  `port/trendora-046dd956` — `bfa3a3f` (the port), `959b5fb` + `6555446` (integration
+  guards + tests), the docs/contract commit, and fix 1 (the legacy-allowlist guard +
+  per-path resume guidance found by review). BOTH features are default-OFF: with
+  `CHAIN_REQUIRE_FULL_DEPTH` and `CHAIN_MAINTENANCE_ISOLATION` unset and no spec line, every
+  path is the pre-port path (the one deliberate exception is the jq-less `iter_dispatch`
+  fallback, which now also emits `maintenance_isolation:"false"`). NOT yet exercised live —
+  the first operator-authored isolated iteration in a real session is still owed.
+- **Source:** four framework-only commits authored inside trendora's vendored copy of this
+  framework (branch `goal/market-compass`, 2026-08-21), reverse-synced file-by-file with
+  `git merge-file --diff3` against each file's OWN pre-change blob rather than copied:
+  `046dd956` (fail closed when `Depth: full` is required but only lean can be dispatched),
+  `29e53651` (framework hunks only — the precedence rung + its cases), `8a4a3a21`
+  (maintenance isolation), `933d5f79` (propagate isolation before child dispatch; reorder
+  QA).
+- **Problem:** the depth arbiter is a COST ladder with no notion of "full depth IS the
+  safety control here", and it had THREE silent full→lean paths, not one — the arbiter
+  ladder (`full-cap` / `budget-breach` / `evaluator-requested-lean`), the full dispatch site
+  when `run-phase.sh` lacks `--no-finalize`, and the depth parser on an unparseable `Depth:`
+  line. Once lean is chosen, `goal-iter-lean.sh` defaults `CHAIN_LEAN_PARALLEL_BROWSER_QA`
+  to `replay` and forks a browser-QA service boot plus a replay lane the moment
+  `developer.done` lands: that is how market-compass iterations 6 and 8 ran an ungated
+  browser replay against a knowingly damaged database. The same defect's other half:
+  "full depth" and "boot the app" were ONE thing, so a backend-only repair iteration could
+  not keep full reviewer/audit scrutiny without also starting services and a browser against
+  the data it was repairing (backend warm-up itself writes derived rows).
+- **Landed (`bfa3a3f`):** two predicates in `lib/common.sh`, each the single place its
+  marker regex lives — `goal_full_depth_required <spec>` (`CHAIN_REQUIRE_FULL_DEPTH` truthy,
+  or a `Depth enforcement: required` spec line) and `goal_maintenance_isolation_required
+  [spec]` (`CHAIN_MAINTENANCE_ISOLATION` truthy, incl. the literal `required`, or a
+  `Maintenance isolation: required` spec line). `_full_depth_pause()` in `run-goal.sh`
+  mirrors the `_host_guard_pause` idiom: resumable `AWAITING_FULL_DEPTH` BEFORE dispatch,
+  an `iter-<N>/depth-requirement-unmet` marker, and `depth-dispatched` REMOVED so a resume
+  cannot inherit a stale lean decision — wired at the demotion sites (`depth-arbiter`,
+  `depth-parse`, `full-dispatch`; a fourth, `depth-legacy-allowlist`, was added by fix 1 —
+  see Integration deltas (10)). A precedence rung resolves a hard-required iteration to
+  full ahead of every cost rung and records the rung it overrode as `depth_cost_overridden`
+  while leaving that rung's on-disk marker untouched, so the arbiter pause is a backstop
+  against a future reordering rather than a reachable path.
+  `apply_maintenance_isolation_from_spec` materializes the spec declaration into the
+  environment before any child dispatch — at BOTH entry points (`run-goal.sh`,
+  `run-phase.sh`) — unsets on an ordinary spec so isolation cannot leak forward, and stamps
+  `CHAIN_MAINTENANCE_ISOLATION_SOURCE=spec|env` so an operator's session-level declaration is
+  never cleared. Six chokepoints: `detect_frontend_in_plan` (subordinates the
+  `CHAIN_GOAL_TARGET_JOURNEYS` browser override), plus `_boot_shared_services`,
+  `ensure_services_running`, `browser-qa-phase.sh`, `replay_lane_partition_and_verify` and
+  `demo-phase.sh`, which refuse through `maintenance_isolation_refuse` (refusals marker +
+  `maintenance_isolation_refused` telemetry). `goal-iter-lean.sh` keeps the parallel
+  browser-QA/replay lane off under a hard requirement regardless of the knob;
+  `AWAITING_FULL_DEPTH` is registered in the `run-goal.sh` status header and in
+  `lib/plain-language.sh` (keys + explainer).
+- **Integration deltas added on THIS side (`959b5fb`, `6555446`)** — each one a path an
+  isolated iteration actually reaches here, or a defect inherited from trendora HEAD:
+  (1) `browser-qa-phase.sh`'s isolation SKIPPED artifact carries a `**Reason:**` line —
+  `closure_gate.py` accepts an all-SKIPPED browser-QA file only via `**Reason:**`,
+  `## Reason` or the browser-infra taxonomy, so the ported heredoc's `## Why this lane did
+  not run` closed the phase CLOSURE-FAIL. (2) `write_na_ui_artifacts` writes isolation
+  wording for ALL SIX N/A UI stubs from one shared reason string — under isolation
+  `detect_frontend_in_plan` refuses, so `run-phase.sh` takes its backend-only branches and
+  `browser-qa-phase.sh` is never entered, and the withheld lane was being reported to the
+  evaluator as "Backend-only phase (Frontend Present: no)". (3) `closure_gate.py`'s
+  `frontend_present()` gained the carve-out the bash predicate already had:
+  `maintenance_isolation_active()` reads the exported `CHAIN_MAINTENANCE_ISOLATION` (the SAME
+  literal truthy set bash accepts, deliberately not a case-insensitive superset) or a
+  `Maintenance isolation: required` plan line, so an isolated iteration's six stubs pass even
+  when the plan says `Frontend Present: yes`. (4) `run-goal.sh`'s showcase-join REAPS the
+  previous iteration's background tail (`_join_showcase_tail --kill` + an explicit
+  `kill_phase_servers`) instead of waiting for it — the tail forked during iteration N−1 and
+  carries the PRE-isolation environment, so joining it would boot the app mid-isolation.
+  (5) `AWAITING_FULL_DEPTH` added to `run-goal.sh`'s `--resume` status allowlist (inherited
+  gap: the pause is documented resumable, but `--resume` never reset the status, so the only
+  escape was deleting the requirement). (6) `demo-phase.sh` checks isolation BEFORE its
+  self-boot block and prints exactly ONE skip line via a dedicated `_runner_rc=90` — under
+  `set -e` the refusal from `ensure_services_running` killed the script ~120 lines before the
+  ported guard, and the runner's rc 3 would otherwise have followed a contract decision with
+  "Playwright not available"; documented, not changed: `_boot_shared_services` never exports
+  `CHAIN_SHARED_SERVICES=true` under isolation, because that flag means "the caller owns a
+  running app". (7) `qa-phase.sh` no longer appends the "backend did NOT become healthy after
+  retries" warning + dependency hint under isolation — `QA_BACKEND_UP=no` there because
+  nobody was ALLOWED to start a backend, and the prompt told the agent two stories about the
+  same service. (8) `iter_dispatch` carries `maintenance_isolation` on BOTH paths — the
+  port added it to the jq payload, and this side added it to the jq-less `printf` fallback,
+  which had silently dropped the only record that an iteration ran isolated. (9) `lib/replay-lane.sh`'s isolation guard fails CLOSED — `declare -F
+  <predicate> && <predicate>` read "not isolated" when `common.sh` was never sourced, making
+  the one state in which the contract is uncheckable the state that lets the browser run.
+  (10) **Fix 1 (2026-08-21, after review):** the legacy SPEED-10 allowlist gained the same
+  `goal_full_depth_required` guard — the precedence rung and the `_full_depth_pause` backstop both
+  live inside the arbiter's `if`, so whenever the arbiter is skipped (`CHAIN_DEPTH_ARBITER=false`,
+  or iter-0, which it exempts) a hard-required spec fell through to the allowlist, which demoted it
+  to lean with no pause when it named no `Full trigger:` line — while that same knob was documented as the way OUT
+  of `AWAITING_FULL_DEPTH`. It now pauses at `depth-legacy-allowlist`, `_full_depth_pause` prints a
+  PER-PATH remedy (also stored as `remedy=` in `depth-requirement-unmet`), and every doc that
+  offered the knob as a hatch now denies it explicitly.
+  (11) **Final review (2026-08-21):** isolation now IMPLIES the full-depth requirement.
+  `goal_full_depth_required` returns true under `goal_maintenance_isolation_required`, so an
+  isolated `Depth: full` spec is protected by the existing precedence rung (previously it could be
+  cost-demoted unless the operator ALSO wrote `Depth enforcement: required`) and
+  `goal-iter-lean.sh`'s fail-closed guard forces its parallel browser-QA/replay fork off. A spec
+  that resolved to lean/evidence under isolation now PAUSES before dispatch
+  (`isolation-requires-full`) — nothing is promoted. That path mattered: `goal-iter-lean.sh` has no
+  isolation handling at all (bare `ensure_services_running` in its boot unit), so with the fork on
+  the refusal was swallowed and `ui-test-results.md` blamed "frontend not running" — no
+  `**Reason:** maintenance isolation` line, so neither the evaluator carve-out nor
+  `closure_gate.py` could fire and journeys went `unknown`; with the fork off the executor aborted
+  under `set -e` only AFTER developer and reviewer had mutated the tree. Same commit: a resume that
+  regenerates a spec carrying an operator-only line warns loudly and emits `spec_regenerated`
+  (the decomposer is forbidden to rewrite those lines, so regeneration silently dropped them), and
+  the QA brief's product-specific database claim was made generic.
+  Agent/operator contract (this commit): the goal-evaluator scores an all-SKIPPED isolation
+  `ui-test-results.md` like `DEFERRED-BUDGET` (journeys keep their prior status, and no
+  journey may be promoted TO passing on an iteration that produced no browser evidence); the
+  goal-decomposer must NEVER emit `Depth enforcement:` or `Maintenance isolation:`;
+  `goal-interactive-dispatch` 3.0.0→3.0.1 gains the `AWAITING_FULL_DEPTH` bullet.
+- **Deliberately NOT done:** the decomposer cannot arm either control — a governor reading
+  the governed agent's own prose is not a governor (anti-pattern 25), so both lines are
+  operator-authored and the decomposer states the NEED in BACKGROUND prose instead. The
+  brief's proposed `GOAL_SESSION_DIR`/`GOAL_ITER_INDEX` fallback inside
+  `maintenance_isolation_refuse` was NOT written: `lib/common.sh` sources
+  `lib/checkpoint.sh`, and `goal_iter_dir` already PREFERS those two exported vars, so it
+  would have been dead code — the behaviour is pinned by a test instead. Trendora's other
+  un-upstreamed patches stay out (see §20 "Known gaps"): `lib/replay-lane.sh`'s rc=7
+  backend-unreachable handling and `resolve_backend_health_url`. No
+  `render_iteration_summary.py` badge for the new status yet.
+- **Known steady state (record it; do not "fix" it by accident):**
+  - A hard-required iteration may breach the SPEED-15 wall budget and then override its own
+    `budget-breached` marker on the NEXT iteration. That is the design — a safety
+    requirement outranks a cost rung — and it is visible as `depth_cost_overridden
+    {overridden_cost_rung:"budget-breach"}`; the marker itself is deliberately left on disk.
+  - A showcase tail reaped under isolation returns before the join path's commit/push block
+    (which only runs with `--push-per-iter`), so iteration N−1's summary / README / renders
+    can be partial and uncommitted; iteration N's own per-iter commit sweeps them up.
+  - **Iteration 0 is the sharp edge of both session-wide knobs**, because the arbiter exempts the
+    baseline and the baseline spec is verify-only. `CHAIN_REQUIRE_FULL_DEPTH=true` plus a baseline
+    spec that says `Depth: full` and names no `Full trigger:` halts at iteration 0
+    (`depth-legacy-allowlist`) — and "re-enable the arbiter" is inert there, so only the
+    `Full trigger:` line helps. `CHAIN_MAINTENANCE_ISOLATION=true` halts an ordinary verify-only
+    baseline at `isolation-requires-full`, since that spec asks for lean. Both are fail-closed by
+    design; declare the controls from iteration 1, or write the baseline spec to match.
+  - `closure_gate.py`'s backend-only WARN channel still reads "Plan says Frontend Present:
+    no but frontend-looking files changed this phase" for an isolation-declared plan that
+    says `yes`. Wording only — no verdict effect. Follow-up.
+  - The isolation carve-out now exists in TWO implementations — the bash predicate and the
+    python gate — agreeing on the truthy set by convention and comment, not by a shared
+    constant. A parity test (bash truthy set == `_ISOLATION_ENV_TRUTHY`) is a follow-up.
+- **Follow-ups (tracked, NOT done):**
+  - Deterministic GOAL_ACHIEVED refusal on an isolated iteration (`goal_gate_filter_verdict`,
+    ~5 lines). Today the rule is agent-side only: the evaluator body and methodology forbid
+    certifying on an isolated iteration's own evidence, but no gate enforces it. Whether the
+    gate should refuse outright is a design choice for the owner.
+  - `write_session_summary` and the HTML renderer have no badge/branch for
+    `AWAITING_FULL_DEPTH`; it renders as an unknown status.
+  - `async-showcase-join` records a refusal only when `_SHOWCASE_PID` is still set, which a
+    completed-but-unjoined tail clears only at the join — so a tail that finished on its own
+    leaves no refusal record even though the reap path was the contract-relevant one.
+  - `agents/phase-closure-auditor/body.md` has no isolation carve-out, so the LLM escape hatch
+    could still read six N/A stubs as an absent frontend.
+  - No parity test pins the bash truthy set against `closure_gate.py`'s `_ISOLATION_ENV_TRUTHY`;
+    they agree by comment and convention.
+  - The developer / reviewer / auditor prompts carry no isolation note. The FORBIDDEN half binds
+    the engine's own service and browser call sites, so nothing the pipeline drives can start the
+    app — but an agent told to run it by hand would not know it must not.
+  - (final-review residuals, 2026-08-21) The `isolation-requires-full` pause exits before the
+    showcase-join step's explicit `kill_phase_servers`, so app services an earlier showcase tail
+    had already started survive that pause (the EXIT trap reaps the tail itself; the services
+    predate the isolated iteration). `tests/automation/test-maintenance-isolation.sh` still carries
+    ten `awk|grep -q`-style pipelines under `pipefail` — the SIGPIPE flake pattern removed from its
+    sibling; route slices through files before it grows. `run-goal.sh`'s
+    `apply_maintenance_isolation_from_spec … || true` is now load-bearing for the isolation guard
+    (a silent failure there would disarm a spec-declared isolation; unreachable today).
+    `goal-iter-lean.sh`'s "Full depth is REQUIRED" line fires for isolation too (reason tag
+    `full-depth-required`; behaviour correct, message imprecise). The quickstart's "let the loop
+    pause once the decomposer checkpoint exists" does not say how (`/goal-pause` or Ctrl-C).
+- **Verify:** `bash tests/automation/test-maintenance-isolation.sh` (78) · `bash
+  tests/automation/test-full-depth-required.sh` (53) · `bash
+  tests/automation/test-closure-gate.sh` (29) · `bash tests/automation/test-depth-arbiter.sh`
+  (33) · `bash tests/automation/test-replay-lane.sh` (59) · `bash
+  tests/automation/test-plain-language.sh` (63) · `python3
+  scripts/automation/lib/closure_gate.py self-test` · `./scripts/automation/run-evals.sh`
+  (155 / 0). Semantic smoke without an engine run:
+
+  ```bash
+  source scripts/automation/lib/common.sh
+  CHAIN_MAINTENANCE_ISOLATION=true goal_maintenance_isolation_required && echo isolated
+  printf -- '- **Depth enforcement:** required\n' > /tmp/spec.md
+  goal_full_depth_required /tmp/spec.md && echo required
+  ```
+- **Rollback:** both features are default-OFF, so the live rollback is to stop declaring
+  them: `unset CHAIN_REQUIRE_FULL_DEPTH CHAIN_MAINTENANCE_ISOLATION` and remove any
+  `Depth enforcement:` / `Maintenance isolation:` spec line. `CHAIN_DEPTH_ARBITER=false`
+  additionally restores the legacy SPEED-10 allowlist. To remove the mechanism itself,
+  revert this branch's six commits — `bfa3a3f` (port), `959b5fb` + `6555446` (integration
+  guards), `f9f9624` (docs/contracts), `de23d27` (fix 1) and the final-review fix on top
+  (run-evals returns to 153 / 0). Those are THIS repo's commits; the four `Source` commits
+  above are trendora's and are not present here.
+
+### CAND-STYLE · Per-agent Claude Code output style (landed default-off; experiment pending)
+- **Priority:** P2 · **Effort:** M · **Risk:** LOW-MED · **Status:** IMPLEMENTED
+  2026-08-20 behind `CHAIN_OUTPUT_STYLES` (default off, G4); G8 stage 1 (fixture A/B)
+  run 2026-08-21 — mechanism confirmed, token win indicative (−44% on the one
+  like-for-like developer cell), journey clause refuted by an orphan-Chrome
+  infrastructure defect; stage 2 (same-session real rollout) pending.
+- **Problem:** long, machine-consumed pipeline steps (developer, qa,
+  browser-qa-agent, orchestrator, ui-impact-analyst, ux-regression-reviewer) pay
+  sonnet-priced tokens narrating a transcript no human reads. Claude Code's built-in
+  `Concise` output style is a zero-app-code lever for exactly this, but applying it
+  needed: name validation (the CLI silently ignores an unknown style and falls back
+  to default), a headless invocation seam, an interactive-backend emulation path
+  (Agent-tool subagents never receive a native style at all), proof that the
+  effective style actually matched what was requested, and — per **D5**'s precedent,
+  where an output cap increased turn count and ~doubled output tokens — a dedicated
+  cost tripwire, because "should save tokens" cannot ship unmeasured.
+- **Current state:** the Step 0 probe (2026-08-20, CLI 2.1.237) confirmed
+  `init.output_style="Concise"` survives `--exclude-dynamic-system-prompt-sections`,
+  and that inline `--settings` MERGES with project/user settings rather than
+  replacing them (hooks still fired); `available_output_styles` is absent from this
+  CLI version's `init` event. The assignment lives in a python table, not
+  `agents/<name>/agent.yaml`: vendored deployments (trendora, tapeology) symlink
+  `.claude/`, `config/`, `scripts/` but not `agents/`, and Claude Code ignores an
+  `output_style` frontmatter key for subagents regardless — a yaml-based assignment
+  would be invisible in one case and inert in the other.
+- **Change spec (landed):** resolver `output_style_for` in
+  `scripts/automation/lib/agent_permissions.py` beside `EFFORT_OVERRIDES`, same
+  precedence shape as `CHAIN_AGENT_EFFORT` (`CHAIN_OUTPUT_STYLE_OVERRIDE` global
+  debug > `CHAIN_AGENT_OUTPUT_STYLE` per-agent map > `OUTPUT_STYLE_OVERRIDES` table
+  gated by `CHAIN_OUTPUT_STYLES=true` > nothing); CLI subcommands `output-style`,
+  `output-style-text`, `output-styles-configured`, `output-style-check` (commit
+  `d2b9a19`). Headless seam: `_claude_invoke` appends `--settings
+  '{"outputStyle":"<name>"}'` when a style resolves; `_codex_invoke` drops the flag;
+  `run-judgment-evals.sh` carries the same parity lines (commit `da939e5`). The
+  interactive backend has no native style channel for Agent-tool subagents, so
+  `_interactive_invoke` appends an emulation block to the prompt instead — trace
+  records `<name>(emulated)` (commit `adaf89b`). Proof per dispatch: the renderer
+  stamps the EFFECTIVE `output_style` from the stream-json `init` event into the
+  usage sidecar, landing it in both `trace.jsonl` and the `claude_usage` telemetry
+  event; telemetry also carries `output_style_requested`; a requested-vs-effective
+  mismatch (case-insensitive, `""` ≡ `"default"`) fires `WARNING: output style
+  requested=<x> effective=<y>` plus an `output_style_mismatch` telemetry event —
+  this also catches an ambient `outputStyle` pin leaking in from the operator's own
+  settings (commit `da939e5`). Engine wiring: boot preflight `output-style-check`
+  (exit 2 on any invalid configured name); `session.json` gets an `output_styles`
+  reporting stamp; `iter_config {key:"CHAIN_OUTPUT_STYLES"}` fires per knob-active
+  iteration; the tripwire revert block was generalized to one `experiment_reverted`
+  event per active knob key (commits `6295302`, `1027695`). `analyze_telemetry.py
+  --tripwire` gained a cost dimension — styled vs. unstyled `claude_usage` rows for
+  the same agent in-session, tripping when the styled median of `output_tokens` or
+  `num_turns` exceeds 1.5x the baseline median (≥3 rows each side), reason prefix
+  `cost:` — plus an unparseable `review_verdict` trip reason and three new
+  `missing_evidence` emitters (developer handoff, ui-impact, ux-regression) so every
+  wave-1 artifact carries a deterministic "went missing" signal. `doctor.sh` gained
+  an `output-styles` row (20 checks total; commits `8d78ee7`, `15d10cc`). Wave 1
+  assigns `Concise` to developer, qa, browser-qa-agent, orchestrator,
+  ui-impact-analyst, ux-regression-reviewer; judges (`JUDGE_AGENTS`) are refused by
+  a hardcoded guard (D4), `Learning` is refused outright (asks the human to write
+  code), and the whole mechanism is inert outside goal mode (`GOAL_SESSION_DIR`
+  unset), except the debug override `CHAIN_OUTPUT_STYLE_OVERRIDE`, which works in
+  any mode.
+- **DoD (experiment):** pre-register predictions in `benchmarks/experiments.md`
+  (developer `output_tokens` −20..30%, `num_turns` flat ±10%, attempt-1 review FAIL
+  rate unchanged, `cache_creation_input_tokens` ≤ +25K per wave-1 dispatch, zero
+  `output_style_mismatch`); run ≥3 knob-off iterations on one real session, then
+  `CHAIN_OUTPUT_STYLES=true` for ≥3 more on the same session (G9 confirm — this
+  spends real tokens). The full-depth-only wave-1 agents (qa, orchestrator,
+  ui-impact-analyst, ux-regression-reviewer) accrue rows only in full-depth
+  iterations, so they are measured only when each arm includes ≥3 full-depth
+  iterations. The cost guard cannot fire before the styled side has ≥3 rows per
+  agent — not before the third knob-on iteration (second if a fix-mode retry
+  occurs); the first two armed iterations rely on the quality dimension and the
+  manual read-out. Flip the default to `true` in a SEPARATE change (G4) only if
+  developer's median output tokens drop ≥15% (primary metric) AND no wave-1
+  agent with ≥3 rows per arm trips the cost guard AND every tripwire is quiet
+  AND no artifact-schema issues; agents with <3 styled rows are listed as
+  UNMEASURED in the read-out — the flip covers the whole table only if the
+  unmeasured set is empty, otherwise that separate change flips only the
+  measured agents (edit `OUTPUT_STYLE_OVERRIDES` accordingly); if artifacts
+  thinned but tokens still dropped, ship arm 2 instead; otherwise record the
+  result here and leave the knob dormant.
+- **G8 stage-1 result (2026-08-21, fixture A/B — NOT the flip decision):** two
+  `run-benchmark.sh` arms on the todo-app fixture at framework `f8c98b9` (arm A control
+  `bench-20260820-2246`, arm B `CHAIN_OUTPUT_STYLES=true` `bench-20260820-2337`; full
+  grading in `benchmarks/experiments.md` under `POST bench-20260820-2337`). Run this way
+  because both real-session repos had live engines under `HOST_GUARD_MAX_ENGINES` and
+  run an older vendored framework copy; cross-session, so the same-session cost guard
+  was not exercised. **Mechanism CONFIRMED:** every wave-1 dispatch requested and read
+  back `output_style=Concise` (developer ×2, browser-qa-agent ×2, and — iter-1 ran full
+  depth — orchestrator, ui-impact-analyst, qa, ux-regression-reviewer); judges and
+  showcase agents `default`; `iter_config` per iteration; zero `output_style_mismatch`,
+  `missing_evidence`, `experiment_reverted`; tripwire quiet; doctor PASS armed at boot.
+  **Tokens (indicative, n=1 per cell):** the one like-for-like cell, developer iter-0
+  (lean/lean): 14,967 → 8,416 output tokens (−44%), 35 → 28 turns, 184 → 109 s,
+  cache_creation +17.9K (≤ +25K budget held); iter-1 depth-confounded (A lean 29,518 /
+  45 turns vs B FULL 33,098 / 46). **Journeys 3/3 REFUTED for arm B (1/3,
+  BUDGET_EXHAUSTED) for infrastructure reasons, not the style:** arm A's browser-QA
+  Chrome outlived its engine and held the pinned chrome-mcp profile, so arm B's browser
+  lane got `ECONNREFUSED :10547` in both iterations; the evaluator graded J-02/J-03
+  partial from the Playwright demo walkthrough alone (its step 4, authored by the
+  Default-styled demo-narrator, clicked an already-done item). **Watch item:** the styled
+  QA report over-claimed its screenshot evidence once (caught by the auditor and by the
+  styled ux-regression-reviewer) — count QA over-claims per arm in stage 2. Stage 2 =
+  the same-session real rollout above, after the next vendored sync and after the
+  orphan-Chrome reap (Follow-ups) is fixed.
+- **Verify:** `./scripts/automation/run-evals.sh` · `bash
+  tests/automation/test-output-style.sh` · `bash scripts/automation/doctor.sh --only
+  output-styles` · the G8 read-out (`T=runs/goal-session-<sid>/telemetry.jsonl`):
+
+  ```bash
+  jq -r 'select(.event=="claude_usage" and (.agent|IN("developer","qa","browser-qa-agent","orchestrator","ui-impact-analyst","ux-regression-reviewer"))) | [(.iter|tostring), .agent, (.output_style_requested // "none"), (.output_style // "?"), (.usage.output_tokens|tostring), (.num_turns|tostring), (.duration_ms|tostring), (.usage.cache_creation_input_tokens|tostring)] | @tsv' "$T" | column -t
+  jq -s 'map(select(.event=="claude_usage" and .agent=="developer")) | group_by(.output_style_requested // "none") | map({arm:(.[0].output_style_requested // "none"), n:length, out_med:(map(.usage.output_tokens)|sort|.[length/2|floor]), turns_med:(map(.num_turns)|sort|.[length/2|floor]), ms_avg:(map(.duration_ms)|add/length)})' "$T"
+  python3 scripts/automation/lib/analyze_telemetry.py --wall "$T"
+  python3 scripts/automation/lib/analyze_telemetry.py --tripwire --window 3 "$T"; echo "tripwire rc=$?"   # 0 = quiet
+  jq -c 'select(.event|IN("output_style_mismatch","missing_evidence","experiment_reverted"))' "$T"       # must be empty
+  jq -r 'select(.event=="review_verdict") | [.iter,.attempt,.verdict]|@tsv' "$T"                          # attempt-1 FAIL rate vs baseline
+  for f in reports/reviews/*-review.md reports/qa/*-qa.md runs/goal-session-<sid>/iter-*/eval.md; do python3 scripts/automation/lib/artifact_schemas.py validate "$f" >/dev/null 2>&1 || echo "SCHEMA-ISSUE $f"; done
+  ```
+- **Rollback:** `unset CHAIN_OUTPUT_STYLES CHAIN_AGENT_OUTPUT_STYLE
+  CHAIN_OUTPUT_STYLE_OVERRIDE` reverts any live session to unstyled immediately; to
+  remove the mechanism itself, revert the STYLE-1 commits or empty
+  `OUTPUT_STYLE_OVERRIDES`.
+- **Stop-and-ask:** any `output_style_mismatch` event in the first knob-on
+  iteration; wave-1 artifacts failing `artifact_schemas` validation, a
+  `missing_evidence` row appearing, or the attempt-1 review FAIL rate rising under
+  `Concise`; anyone styling a judge outside a debug `CHAIN_OUTPUT_STYLE_OVERRIDE`
+  run, or flipping the default in the same change that touches the knob (G4).
+- **Follow-ups:**
+  - Flip `CHAIN_OUTPUT_STYLES`'s default only in a separate change, after G8
+    evidence.
+  - (G8 stage-1 framework defects — FIXED 2026-08-21, STAGE2-PREREQ T1-T5) QA
+    browser profile now carries the path-hash offset (`iad-qa-<project>-<offset>`)
+    and the headless engine reaps its own QA browsers at exit
+    (`CHAIN_BQA_REAP_ON_EXIT`, default on; `browser-confine.sh --reap` runs without
+    host-guard); `record_review_verdict` emits `review_verdict` from the full-depth
... [diff_bound] incredible_auto_dev/docs/improvement-roadmap.md: 96 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
index aa56b426..2d37ac45 100755
--- a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
+++ b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
@@ -40,6 +40,41 @@ UI_TEST_PLAN="$REPO_ROOT/reports/phase-${PHASE}-ui-test-plan.md"
 UI_SURFACE_MAP="$REPO_ROOT/reports/phase-${PHASE}-ui-surface-map.md"
 UI_TEST_RESULTS="$REPO_ROOT/reports/phase-${PHASE}-ui-test-results.md"
 
+# FAIL-CLOSED: maintenance isolation forbids this entire lane — browser QA and
+# the deterministic replay it drives both start processes and read a database
+# this iteration has declared off-limits. Refuse BEFORE any service probe, any
+# replay partition, and any agent dispatch, and leave an honest SKIPPED artifact
+# so the merge/evaluator path sees a contract decision, not a silent gap.
+if goal_maintenance_isolation_required "$SPEC"; then
+  maintenance_isolation_refuse "browser-qa-phase" "browser QA + deterministic replay lane" || true
+  mkdir -p "$(dirname "$UI_TEST_RESULTS")" 2>/dev/null || true
+  cat > "$UI_TEST_RESULTS" <<EOF
+# Phase ${PHASE} — UI Test Results
+
+**Browser QA Verdict:** SKIPPED
+
+**Reason:** maintenance isolation is required for this iteration — application-service boot, browser QA and the deterministic replay lane are forbidden by contract, so no browser validation was executed.
+
+## Why this lane did not run
+
+This iteration declares **maintenance isolation**. Application-service boot,
+browser QA, and the deterministic replay lane are **forbidden by contract** for
+it — this is a deliberate contract decision, not an infrastructure failure and
+not an accidental gap.
+
+Full reviewer / QA / auditor / coherence / evaluator depth is unchanged and still
+required; only app-service and browser execution are withheld. No backend or
+frontend was started, no browser was opened, no replay was partitioned or run,
+and no golden replay script was written.
+
+No journey is marked PASS or FAIL here. A journey failure against the current
+dataset would be expected damage from a known, still-unrepaired condition rather
+than a regression, so recording either verdict from this lane would be misleading.
+EOF
+  echo "[browser-qa] SKIPPED by maintenance isolation — wrote $UI_TEST_RESULTS"
+  exit 0
+fi
+
 echo "[browser-qa] Running browser QA for: $PHASE"
 
 # Detect frontend
diff --git a/incredible_auto_dev/scripts/automation/demo-phase.sh b/incredible_auto_dev/scripts/automation/demo-phase.sh
index b96e20b4..f39fd207 100755
--- a/incredible_auto_dev/scripts/automation/demo-phase.sh
+++ b/incredible_auto_dev/scripts/automation/demo-phase.sh
@@ -153,6 +153,25 @@ EOF
 
 echo "[demo] Running product demo for: $ID (mode: $MODE)"
 
+# FAIL-CLOSED, and BEFORE the self-boot block below: ensure_services_running
+# refuses under maintenance isolation and returns 1, and this script runs under
+# `set -e`, so a guard placed after that call never executes — the session
+# walkthrough (MODE=session pins FRONTEND_PRESENT=yes) died on the refusal
+# instead of skipping as a documented decision. Skipping here also keeps the
+# skip message single and correct: the phase-mode backend-only branch below
+# would otherwise report a contract decision as "Backend-only iteration", and
+# the runner-stage guard would report it as a missing Playwright install.
+# Showcase, non-gating: exit 0 with a SKIPPED record, exactly like the
+# author-crash path.
+if goal_maintenance_isolation_required 2>/dev/null; then
+  maintenance_isolation_refuse "demo-phase" "app-service boot + Playwright showcase for ${ID}" || true
+  echo "[demo] SKIPPED — maintenance isolation forbids application-service boot and browser execution for this iteration."
+  if [[ "$MODE" == "record" ]]; then
+    _write_demo_skipped_stub "Maintenance isolation is required for this iteration — application-service boot and browser execution are forbidden by contract, not unavailable. No browser walkthrough was performed and no services were started."
+  fi
+  exit 0
+fi
+
 # Backend-only (phase mode) — write stubs and exit cleanly.
 if [[ "$MODE" != "session" && "$FRONTEND_PRESENT" == "no" ]]; then
   echo "[demo] Backend-only iteration — writing N/A stubs and skipping browser."
@@ -326,10 +345,24 @@ fi
 [[ "${CHAIN_DEMO_CAPTION:-}" =~ ^(1|true|yes|TRUE|YES)$ ]] && RUNNER_ARGS+=(--caption)
 
 _runner_rc=0
+if goal_maintenance_isolation_required 2>/dev/null; then
+  # FAIL-CLOSED: the demo runner drives Playwright against a live app. Refuse
+  # before launching a browser. Demo is non-gating showcase, so a skip here never
+  # blocks the pipeline — it simply produces no walkthrough for this iteration.
+  maintenance_isolation_refuse "demo_runner" "Playwright showcase for ${ID}" || true
+  echo "[demo] SKIPPED — maintenance isolation forbids browser/app execution for this iteration." >&2
+  # A dedicated rc, NOT the runner's 3 ("Playwright not available"): the case
+  # below must not follow a contract decision with an install hint. Unreachable
+  # while the guard above stands; kept as defence in depth for a direct call
+  # into this stage.
+  _runner_rc=90
+else
 python3 "$RUNNER" "${RUNNER_ARGS[@]}" || _runner_rc=$?
+fi
 
 case "$_runner_rc" in
   0) ;;
+  90) ;;   # maintenance isolation — already reported above, once
   3) echo "[demo] Playwright not available (see install hint above) — showcase skipped." >&2 ;;
   4) echo "[demo] Live demo needs a display. View the recorded gallery instead: ./scripts/automation/demo.sh $ID" >&2 ;;
   130|137|143)
@@ -343,7 +376,9 @@ esac
 # (lib/replay-lane.sh). Runs at both depths — demo-phase.sh is the one
 # recording hook the lean tail and the full pipeline share. Non-gating
 # showcase enrichment: any failure inside is contained.
-if [[ "$MODE" == "record" && $_runner_rc -eq 0 && "$ID" =~ ^goal-.+-iter-[0-9]+$ ]]; then
+if goal_maintenance_isolation_required 2>/dev/null; then
+  maintenance_isolation_refuse "demo golden auto-derive" "browser-driven showcase for ${ID}" || true
+elif [[ "$MODE" == "record" && $_runner_rc -eq 0 && "$ID" =~ ^goal-.+-iter-[0-9]+$ ]]; then
   source "$SCRIPT_DIR/lib/replay-lane.sh"
   # shellcheck disable=SC2034  # log prefix consumed by the lane lib
   REPLAY_LANE_TAG="demo"
diff --git a/incredible_auto_dev/scripts/automation/dev-phase.sh b/incredible_auto_dev/scripts/automation/dev-phase.sh
index 24e36877..4c38d929 100755
--- a/incredible_auto_dev/scripts/automation/dev-phase.sh
+++ b/incredible_auto_dev/scripts/automation/dev-phase.sh
@@ -129,6 +129,13 @@ When complete:
   This report is for operators, not developers — write in plain language, not code.
 - Update runs/${PHASE}/status.json with current_step: dev_complete" || _agent_rc=$?
 record_agent_invocation_end developer "$_agent_t0" "$_agent_rc"
+# REL-11: same deterministic "went missing" signal as the lean executor — the
+# dev handoff is what every downstream reader treats as proof of the build.
+# Non-blocking; quota exhaustion excluded (nothing was dispatched).
+_DEV_HANDOFF="$REPO_ROOT/docs/handoffs/${PHASE}-dev.md"
+if [[ ! -s "$_DEV_HANDOFF" && "$_agent_rc" -ne "${QUOTA_EXHAUSTED_EXIT_CODE:-75}" ]]; then
+  warn_missing_evidence "developer" "$_DEV_HANDOFF"
+fi
 (( _agent_rc == 0 )) || exit "$_agent_rc"
 
 echo "[dev-phase] Done."
diff --git a/incredible_auto_dev/scripts/automation/doctor.sh b/incredible_auto_dev/scripts/automation/doctor.sh
index 375126a6..f0b8d719 100755
--- a/incredible_auto_dev/scripts/automation/doctor.sh
+++ b/incredible_auto_dev/scripts/automation/doctor.sh
@@ -70,7 +70,7 @@ fi
 
 CHECKS=(python3 node playwright chrome-mcp gh-auth git-remote disk timeout jq
         pump-heartbeat engine-lock tmp-health chrome-exclusive mcp-affinity
-        host-guard cpu-boost reset-reason ras-logging ambient-env)
+        host-guard cpu-boost reset-reason ras-logging ambient-env output-styles)
 
 # Run a command under GNU/uutils timeout when available (network probes must
 # degrade, never hang). $1 = seconds, rest = command.
@@ -569,11 +569,10 @@ check_reset_reason() {
     RESET\|*)
       local hex cause streak prev
       IFS='|' read -r _ hex cause streak prev <<< "$verdict"
-      : "$prev"
       pm="$(_bounded 30 bash "$script" ensure-postmortem 2>/dev/null)"
       path="${pm#POSTMORTEM|}"; path="${path%|*}"
       [[ "$pm" == POSTMORTEM\|* ]] || path="(bundle unavailable: ${pm})"
-      echo "FAIL|the previous boot ended in a HARDWARE-asserted reset: $cause ($hex); $streak recent boots. No CPU mask or memory ceiling can prevent this — postmortem: $path (docs/host-guard.md § After a hardware reset)"
+      echo "FAIL|boot ${prev:-unknown} ended in a HARDWARE-asserted reset: $cause ($hex); $streak recent boots. No CPU mask or memory ceiling can prevent this — postmortem: $path (docs/host-guard.md § After a hardware reset)"
       ;;
     CLEAN\|*)  echo "PASS|${verdict#CLEAN|}" ;;
     UNKNOWN\|*) echo "WARN|${verdict#UNKNOWN|}" ;;
@@ -592,8 +591,18 @@ check_reset_reason() {
 # must not nag hosts that never had the incident.
 check_ras_logging() {
   local script="$SCRIPT_DIR/host-guard/reset-forensics.sh" hist=0 jdir ras missing=""
-  if [[ -f "$script" ]] && [[ "$(_bounded 20 bash "$script" check 2>/dev/null)" == RESET\|* ]]; then
-    hist=1
+  # "History" must mean fault boots in the recent window, not "an unprocessed
+  # fault right now": once ensure-postmortem has frozen the bundles and advanced
+  # the watermark, `check` reads CLEAN — on a host that faulted 16 times.
+  if [[ -f "$script" ]]; then
+    if [[ "$(_bounded 20 bash "$script" check 2>/dev/null)" == RESET\|* ]]; then
+      hist=1
+    else
+      case "$(_bounded 20 bash "$script" streak 2>/dev/null)" in
+        STREAK\|0/*) ;;
+        STREAK\|*)   hist=1 ;;
+      esac
+    fi
   fi
   jdir="${CHAIN_DOCTOR_JOURNALD_DIR:-/etc/systemd/journald.conf.d}"
   if ! grep -rqs 'SyncIntervalSec' "$jdir" 2>/dev/null; then
@@ -611,7 +620,7 @@ check_ras_logging() {
     return
   fi
   if (( hist == 0 )); then
-    echo "PASS|no hardware-reset history on this host — journald/rasdaemon hardening is optional (missing: ${missing%; })"
+    echo "PASS|no hardware-fault reset in this host's recent boot history — journald/rasdaemon hardening is optional (missing: ${missing%; })"
     return
   fi
   echo "WARN|this host HAS hardware-reset history but the next postmortem will be poorer: ${missing%; }— see docs/host-guard.md § After a hardware reset (both need one sudo command)"
@@ -651,6 +660,126 @@ check_ambient_env() {
   echo "WARN|$# ambient CHAIN_* var(s): ${list}— they silently alter engine behavior; measurement runs demand a clean env"
 }
 
+# STYLE-1 (2026-08-20): the output-style experiment is default-OFF and fully
+# offline-checkable — validate whatever IS configured (env knobs + the wave-1
+# table, the latter only when CHAIN_OUTPUT_STYLES=true) and warn on an ambient
+# `outputStyle` pin in settings.json, which would silently style EVERY
+# headless dispatch even with every knob off (a contaminated "knob-off" arm).
+# Never FAILs on drift or a pin — only a resolver crash or an invalid name is
+# a real config error; a name missing from the installed binary just means
+# Claude Code will silently run that agent as Default (see agent_permissions.py).
+check_output_styles() {
+  local conf rc=0
+  conf="$(cd "$ROOT" 2>/dev/null && python3 "$SCRIPT_DIR/lib/agent_permissions.py" output-styles-configured 2>&1)" || rc=$?
+  if [[ "$rc" -ne 0 ]]; then
+    # Collapse to one physical line BEFORE truncating: an embedded newline
+    # here would survive %.140s and split this FAIL row across lines, so
+    # run_check's "last line" parser would miss the "|" and report a generic
+    # "check crashed" instead of this diagnostic.
+    echo "FAIL|output-styles-configured crashed (rc=$rc): $(printf '%.140s' "$(printf '%s' "$conf" | tr '\n' ' ')")"
+    return
+  fi
+
+  # "armed" mirrors run-goal.sh's OWN gate (STYLE-1 boot check) exactly: the
+  # knob is engaged whether or not it currently resolves to anything.
+  local arm_word="dormant"
+  if [[ "${CHAIN_OUTPUT_STYLES:-false}" == "true" || -n "${CHAIN_AGENT_OUTPUT_STYLE:-}" \
+        || -n "${CHAIN_OUTPUT_STYLE_OVERRIDE:-}" ]]; then
+    arm_word="armed"
+  fi
+
+  local pins="" sf
+  for sf in "$HOME/.claude/settings.json" "$ROOT/.claude/settings.json" "$ROOT/.claude/settings.local.json"; do
+    [[ -f "$sf" ]] && grep -a -q -F -- '"outputStyle"' "$sf" 2>/dev/null && pins+="$sf, "
+  done
+  pins="${pins%, }"
+
+  if [[ -z "$conf" ]]; then
+    if [[ -z "$pins" ]]; then
+      echo "PASS|no output styles configured — $arm_word (CHAIN_OUTPUT_STYLES=${CHAIN_OUTPUT_STYLES-unset})"
+    else
+      echo "WARN|no output styles configured via the engine knobs — $arm_word, but outputStyle is pinned in: $pins — applies to EVERY headless dispatch (knob-off arm contaminated)"
+    fi
+    return
+  fi
+
+  local check_out
+  check_out="$(cd "$ROOT" 2>/dev/null && python3 "$SCRIPT_DIR/lib/agent_permissions.py" output-style-check 2>&1)" || rc=$?
+  if [[ "$rc" -ne 0 ]]; then
+    # output-style-check prints one WARNING line per judge entry (harmless —
+    # judges refuse at dispatch) ahead of the ERROR line(s) that actually
+    # explain the rc!=0. Prefer the ERROR line(s) so a judge WARNING can't
+    # crowd the real invalid-name diagnostic out of the 140-char budget; fall
+    # back to the full text if somehow no ERROR line is present (e.g. a raw
+    # traceback). Collapse to one physical line before truncating — same
+    # "last line" hazard as the step-1 crash branch above.
+    local err_lines
+    err_lines="$(printf '%s\n' "$check_out" | grep -F 'ERROR' || true)"
+    [[ -n "$err_lines" ]] || err_lines="$check_out"
+    echo "FAIL|invalid output style configured: $(printf '%.140s' "$(printf '%s' "$err_lines" | tr '\n' ' ')")"
+    return
+  fi
+
+  local claude_cmd bin ver
+  claude_cmd="$(command -v claude 2>/dev/null || true)"
+  bin=""
+  [[ -n "$claude_cmd" ]] && bin="$(readlink -f "$claude_cmd" 2>/dev/null || true)"
+  if [[ -z "$bin" || ! -r "$bin" ]]; then
+    echo "WARN|output style(s) configured ($arm_word) but no readable claude binary to verify against"
+    return
+  fi
+  ver="$(claude --version 2>/dev/null | head -n1)"
+  [[ -n "$ver" ]] || ver="unknown version"
+
+  # Dedupe configured names (the wave-1 table maps six agents to one style
+  # name) and drop "default" — it carries no binary marker to verify: the
+  # binary has no `# Default Style Active` literal.
+  local -a names=() missing=()
+  local name src already existing found
+  while IFS=$'\t' read -r name src; do
+    [[ -z "$name" ]] && continue
+    [[ "${name,,}" == "default" ]] && continue
+    already=false
+    for existing in "${names[@]}"; do
+      [[ "$existing" == "$name" ]] && { already=true; break; }
+    done
+    $already || names+=("$name")
+  done <<< "$conf"
+
+  for name in "${names[@]}"; do
+    found=false
+    if _bounded 10 grep -a -q -F -- "# $name Style Active" "$bin" 2>/dev/null; then
+      found=true
+    elif [[ -f "$ROOT/.claude/output-styles/$name.md" ]]; then
+      found=true
+    fi
+    $found || missing+=("$name")
+  done
+
+  if [[ "${#missing[@]}" -gt 0 ]]; then
+    local list="" m
+    for m in "${missing[@]}"; do
+      [[ -n "$list" ]] && list+=", "
+      list+="$m"
+    done
+    echo "WARN|built-in style(s) not found in claude $ver: $list — Claude Code ignores unknown names silently; the experiment would run as Default"
+    return
+  fi
+
+  local detail="${#names[@]} configured style(s) present in claude $ver ($arm_word)"
+  if [[ -n "$pins" ]]; then
+    # The engine's per-dispatch --settings is a session-level override that
+    # OUTRANKS a settings.json pin (verified via a Step-0 probe, CLI 2.1.237,
+    # 2026-08-20) — the pin never overrides a requested style. It only
+    # reaches dispatches the engine leaves unstyled: judges, Default-arm
+    # agents, and (see the empty-conf branch above) every dispatch when the
+    # knob itself is off.
+    echo "WARN|$detail but outputStyle is pinned in: $pins — the pin applies to every dispatch the engine leaves unstyled (judges, Default-arm agents), contaminating the control arm; the engine's --settings wins only where a style is requested"
+  else
+    echo "PASS|$detail"
+  fi
+}
+
 # ── Harness ─────────────────────────────────────────────────────────────────
 
 usage() {
diff --git a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
index fb560462..bc5e3f59 100755
--- a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
+++ b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
@@ -939,6 +939,14 @@ When complete:
 - Update runs/${ITER_NAME}/status.json with current_step: dev_complete
 " || _rc=$?
   record_agent_invocation_end "developer" "$_start" "$_rc"
+  # REL-11: the dev handoff is the reviewer's and the goal-evaluator's only
+  # account of what this iteration changed — a dispatch that returns without it
+  # reads downstream as "nothing happened". Loud banner + missing_evidence
+  # telemetry, never a gate (the caller's rc is untouched). Quota exhaustion is
+  # excluded: nothing was dispatched, so nothing went missing.
+  if [[ ! -s "$DEV_HANDOFF" && "$_rc" -ne "${QUOTA_EXHAUSTED_EXIT_CODE:-75}" ]]; then
+    warn_missing_evidence "developer" "$DEV_HANDOFF"
+  fi
   return $_rc
 }
 
@@ -1105,9 +1113,7 @@ else
   _rev_rc=0
   run_reviewer || _rev_rc=$?
   _pause_if_transport "$_rev_rc" "reviewer"
-  if _review_parses; then
-    record_telemetry_event "review_verdict" "$(jq -cn --arg v "$(_review_verdict)" --argjson a 1 --arg n "$ITER_NAME" '{verdict:$v, attempt:$a, iter_name:$n}' 2>/dev/null || printf '{"verdict":"%s","attempt":1}' "$(_review_verdict)")"
-  fi
+  record_review_verdict "$REVIEW_REPORT" 1 "$ITER_NAME" "$_rev_rc" || true
   if [[ "$_rev_rc" -eq 0 ]] && _review_parses; then
     step_mark_done review-1 --dir "$ITER_DIR" --verdict "$(_review_verdict)" "$REVIEW_REPORT"
   fi
@@ -1152,9 +1158,7 @@ Review report path: $REVIEW_REPORT
     _rev_rc=0
     run_reviewer || _rev_rc=$?
     _pause_if_transport "$_rev_rc" "reviewer (fix-mode)"
-    if _review_parses; then
-      record_telemetry_event "review_verdict" "$(jq -cn --arg v "$(_review_verdict)" --argjson a 2 --arg n "$ITER_NAME" '{verdict:$v, attempt:$a, iter_name:$n}' 2>/dev/null || printf '{"verdict":"%s","attempt":2}' "$(_review_verdict)")"
-    fi
+    record_review_verdict "$REVIEW_REPORT" 2 "$ITER_NAME" "$_rev_rc" || true
     if [[ "$_rev_rc" -eq 0 ]] && _review_parses; then
       step_mark_done review-2 --dir "$ITER_DIR" --verdict "$(_review_verdict)" "$REVIEW_REPORT"
     fi
diff --git a/incredible_auto_dev/scripts/automation/host-guard/browser-confine.sh b/incredible_auto_dev/scripts/automation/host-guard/browser-confine.sh
index 68a373e7..0d2902f6 100755
--- a/incredible_auto_dev/scripts/automation/host-guard/browser-confine.sh
+++ b/incredible_auto_dev/scripts/automation/host-guard/browser-confine.sh
@@ -24,8 +24,9 @@
 #      the next dispatch cold-starts instead of "reconnecting" to a corpse.
 #   D. Reap (--reap, opt-in) — TERM this project's own QA browsers at phase end.
 #
-# Absent/disabled host-guard.env (or HOST_GUARD_BROWSER_CONFINE=0) ⇒ no-op:
-# the framework stays project-neutral.
+# Absent/disabled host-guard.env (or HOST_GUARD_BROWSER_CONFINE=0) ⇒ passes A-C
+# are skipped: the framework stays project-neutral. Pass D still runs — a
+# project with no host-guard still leaks a detached QA browser at engine exit.
 #
 # Usage: browser-confine.sh [--reap]
 # Exit:  always 0 (advisory pass — never fail a QA phase over browser hygiene).
@@ -42,21 +43,35 @@ ROOT="${HOST_GUARD_ROOT:-$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null |
 ENV_FILE="$ROOT/project-extensions/host-guard/host-guard.env"
 # shellcheck disable=SC1090
 [[ -f "$ENV_FILE" ]] && source "$ENV_FILE" 2>/dev/null
+# CONFINE gates passes A-C (they need a CPU mask + taskset). Pass D (--reap)
+# needs neither: a project with no host-guard still leaves a detached QA
+# browser behind at engine exit, and reaping it is what keeps the NEXT
+# session's lane reachable (G8 stage 1, 2026-08-21).
+CONFINE=1
 if [[ "${HOST_GUARD_ENABLED:-0}" != "1" || -z "${HOST_GUARD_CPU_LIST:-}" \
       || "${HOST_GUARD_BROWSER_CONFINE:-1}" == "0" ]]; then
-  echo "[browser-confine] host-guard absent/disabled for $ROOT — nothing to do."
-  exit 0
-fi
-if ! command -v taskset >/dev/null 2>&1; then
+  if (( REAP )); then
+    echo "[browser-confine] host-guard absent/disabled for $ROOT — confinement skipped; reap only."
+    CONFINE=0
+  else
+    echo "[browser-confine] host-guard absent/disabled for $ROOT — nothing to do."
+    exit 0
+  fi
+elif ! command -v taskset >/dev/null 2>&1; then
   echo "[browser-confine] taskset unavailable — cannot confine browsers." >&2
-  exit 0
+  (( REAP )) || exit 0
+  CONFINE=0
 fi
 
-MASK="$HOST_GUARD_CPU_LIST"
+MASK="${HOST_GUARD_CPU_LIST:-}"
 PROFILE_ROOT="${CHROME_PROFILE_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/superpowers/browser-profiles}"
 _proj="$ROOT"; [[ "$_proj" == */incredible_auto_dev ]] && _proj="${_proj%/incredible_auto_dev}"
 BASE="$(basename "$_proj")"
-OWN_DIRS=( "$PROFILE_ROOT/iad-qa-$BASE" "$PROFILE_ROOT/iad-qa-$BASE-qa" )
+# Same derivation as lib/common.sh:_project_port_offset — keep the two in sync
+# (tests/automation/test-host-guard-browser.sh asserts the parity).
+_hex="$(printf '%s' "$_proj" | sha1sum | cut -c1-4)"
+OFFSET=$(( 16#$_hex % 1000 ))
+OWN_DIRS=( "$PROFILE_ROOT/iad-qa-$BASE-$OFFSET" "$PROFILE_ROOT/iad-qa-$BASE-$OFFSET-qa" )
 UID_SELF="$(id -u)"
 
 # ── helpers ──────────────────────────────────────────────────────────────────
@@ -147,68 +162,74 @@ n_qa=0; n_confined=0; n_kept=0; n_killed=0; n_mcp=0; n_mcp_confined=0; n_swept=0
 # ── Pass A: QA browsers ──────────────────────────────────────────────────────
 # Only MAIN browser processes: renderers/GPU helpers carry --type= and are
 # handled by the tree walk (they are children of the main process).
-for pid in $(_scan "$PROFILE_ROOT/"); do
-  cmd="$(_cmdline "$pid")"
-  [[ "$cmd" == *" --type="* ]] && continue
-  n_qa=$(( n_qa + 1 ))
-  allowed="$(_allowed "$pid")"
-  if _owned "$cmd"; then
-    # Ours: must sit exactly inside this project's mask.
-    _is_subset "$allowed" "$MASK" && { n_kept=$(( n_kept + 1 )); continue; }
-  else
-    # Someone else's QA profile (e.g. the other project's, or a legacy
-    # auto-disambiguated one). Only act when it is effectively unconfined —
-    # narrowing a browser another project already confined would be rude and
-    # pointless; leaving an all-CPU browser running is what resets the host.
-    (( $(_width "$allowed") <= $(_width "$MASK") )) && { n_kept=$(( n_kept + 1 )); continue; }
-  fi
-  if _confine_tree "$pid"; then
-    n_confined=$(( n_confined + 1 ))
-    echo "[browser-confine] confined QA chrome pid $pid to $MASK."
-    continue
-  fi
-  if _owned "$cmd"; then
-    echo "[browser-confine] pid $pid could not be confined — terminating (own profile)." >&2
-    if _terminate "$pid"; then
-      n_killed=$(( n_killed + 1 ))
-      for d in "${OWN_DIRS[@]}"; do
-        [[ "$cmd" == *"--user-data-dir=$d"* ]] && _sweep_profile_files "$d"
-      done
+if (( CONFINE )); then
+  for pid in $(_scan "$PROFILE_ROOT/"); do
+    cmd="$(_cmdline "$pid")"
+    [[ "$cmd" == *" --type="* ]] && continue
+    n_qa=$(( n_qa + 1 ))
+    allowed="$(_allowed "$pid")"
+    if _owned "$cmd"; then
+      # Ours: must sit exactly inside this project's mask.
+      _is_subset "$allowed" "$MASK" && { n_kept=$(( n_kept + 1 )); continue; }
+    else
+      # Someone else's QA profile (e.g. the other project's, or a legacy
+      # auto-disambiguated one). Only act when it is effectively unconfined —
+      # narrowing a browser another project already confined would be rude and
+      # pointless; leaving an all-CPU browser running is what resets the host.
+      (( $(_width "$allowed") <= $(_width "$MASK") )) && { n_kept=$(( n_kept + 1 )); continue; }
     fi
-  else
-    echo "[browser-confine] WARNING: chrome pid $pid ($allowed) is outside $MASK and is not ours to kill — close it manually." >&2
-  fi
-done
+    if _confine_tree "$pid"; then
+      n_confined=$(( n_confined + 1 ))
+      echo "[browser-confine] confined QA chrome pid $pid to $MASK."
+      continue
+    fi
+    if _owned "$cmd"; then
+      echo "[browser-confine] pid $pid could not be confined — terminating (own profile)." >&2
+      if _terminate "$pid"; then
+        n_killed=$(( n_killed + 1 ))
+        for d in "${OWN_DIRS[@]}"; do
+          [[ "$cmd" == *"--user-data-dir=$d"* ]] && _sweep_profile_files "$d"
+        done
+      fi
+    else
+      echo "[browser-confine] WARNING: chrome pid $pid ($allowed) is outside $MASK and is not ours to kill — close it manually." >&2
+    fi
+  done
+fi
 
 # ── Pass B: MCP servers (confine, never kill) ────────────────────────────────
 # HOST_GUARD_MCP_MATCH holds the cmdline tokens that identify a Chrome-MCP
 # server (ALL must match). It exists so tests can scope this pass to their own
 # fake server — pass B is deliberately profile-root-independent, so without the
 # seam a sandboxed run would reach the operator's real, live MCP server.
-read -r -a _mcp_match <<< "${HOST_GUARD_MCP_MATCH:-superpowers-chrome mcp/dist/index.js}"
-for pid in $(_scan "${_mcp_match[@]}"); do
-  n_mcp=$(( n_mcp + 1 ))
-  _is_subset "$(_allowed "$pid")" "$MASK" && continue
-  if _confine_tree "$pid"; then
-    n_mcp_confined=$(( n_mcp_confined + 1 ))
-    echo "[browser-confine] confined Chrome-MCP server pid $pid to $MASK (its future browsers inherit it)."
-  else
-    echo "[browser-confine] WARNING: Chrome-MCP server pid $pid stays outside $MASK — browsers it spawns will be unconfined." >&2
-  fi
-done
+if (( CONFINE )); then
+  read -r -a _mcp_match <<< "${HOST_GUARD_MCP_MATCH:-superpowers-chrome mcp/dist/index.js}"
+  for pid in $(_scan "${_mcp_match[@]}"); do
+    n_mcp=$(( n_mcp + 1 ))
+    _is_subset "$(_allowed "$pid")" "$MASK" && continue
+    if _confine_tree "$pid"; then
+      n_mcp_confined=$(( n_mcp_confined + 1 ))
+      echo "[browser-confine] confined Chrome-MCP server pid $pid to $MASK (its future browsers inherit it)."
+    else
+      echo "[browser-confine] WARNING: Chrome-MCP server pid $pid stays outside $MASK — browsers it spawns will be unconfined." >&2
+    fi
+  done
+fi
 
 # ── Pass C: stale meta/lock sweep ────────────────────────────────────────────
 # The age guard keeps a racing MCP server's freshly-written file: it records the
 # pid before the browser is up, so a <30s file with a dead pid may be mid-launch.
-for f in "$PROFILE_ROOT"/*.meta.json "$PROFILE_ROOT"/*.mcp.lock; do
-  [[ -e "$f" ]] || continue
-  age=$(( EPOCHSECONDS - $(stat -c %Y "$f" 2>/dev/null || echo "$EPOCHSECONDS") ))
-  (( age > 30 )) || continue
-  fpid="$(sed -n 's/.*"pid"[: ]*\([0-9][0-9]*\).*/\1/p' "$f" 2>/dev/null | head -n 1)"
-  [[ -n "$fpid" ]] || continue
-  [[ -d "/proc/$fpid" ]] && continue
-  rm -f "$f" 2>/dev/null && n_swept=$(( n_swept + 1 ))
-done
+if (( CONFINE )); then
+  for f in "$PROFILE_ROOT"/*.meta.json "$PROFILE_ROOT"/*.mcp.lock; do
+    [[ -e "$f" ]] || continue
+    age=$(( EPOCHSECONDS - $(stat -c %Y "$f" 2>/dev/null || echo "$EPOCHSECONDS") ))
+    (( age > 30 )) || continue
+    fpid="$(sed -n 's/.*"pid"[: ]*\([0-9][0-9]*\).*/\1/p' "$f" 2>/dev/null | head -n 1)"
+    [[ -n "$fpid" ]] || continue
+    [[ -d "/proc/$fpid" ]] && continue
+    rm -f "$f" 2>/dev/null && n_swept=$(( n_swept + 1 ))
+  done
+fi
 
 # ── Pass D: reap (opt-in, engine backend only) ───────────────────────────────
 if (( REAP )) && [[ "${CHAIN_BQA_REAP:-0}" == "1" && "${CHAIN_AGENT_BACKEND:-}" != "interactive" ]]; then
diff --git a/incredible_auto_dev/scripts/automation/host-guard/fabric-pin.sh b/incredible_auto_dev/scripts/automation/host-guard/fabric-pin.sh
new file mode 100755
index 00000000..38356479
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/host-guard/fabric-pin.sh
@@ -0,0 +1,108 @@
+#!/usr/bin/env bash
+# fabric-pin.sh — pin the AMD APU's fabric/memory/SoC clocks at their top
+# P-state. Mitigation rung A for the 0x08000800 incident (data fabric sync
+# flood, 16 hard resets on the GEEKOM A7 Max since 2026-07-20).
+#
+# WHY THIS KNOB: MemTest86+ ran 20.5 h at ~90 °C with ZERO resets — an
+# environment with no OS power management and no DF/UCLK P-state transitions —
+# while under Linux the machine resets at near-idle and under load alike
+# (58 °C/16 W and 67 °C/22 W deaths on 2026-08-10). CPU-core C-states were
+# falsified as a cause on 2026-08-08 with the limit verifiably active. The
+# remaining OS-active-only variable this host exposes is the fabric clock
+# visibly stepping 500/1600/1960 MHz under `auto` DPM. Writing `high` to
+# power_dpm_force_performance_level pins fclk/mclk/socclk at their top level,
+# eliminating those transitions. Cost: a few watts at idle. Rollback: `release`
+# (or remove the iad-fabric-pin.service unit and reboot).
+#
+# VERIFY ONLY by journal tag + sysfs (the standing host-guard lesson —
+# "installed" ≠ enabled ≠ ran):
+#   journalctl -t iad-fabric-pin -b 0
+#   grep '\*' /sys/class/drm/card*/device/pp_dpm_fclk   # star on the TOP row
+#
+# Usage: fabric-pin.sh apply | release | status
+# Needs root for apply/release (the pp sysfs nodes are root-writable).
+set -u
+
+TAG="iad-fabric-pin"
+
+_log() { logger -t "$TAG" -- "$*" 2>/dev/null; echo "[$TAG] $*"; }
+
+_card() { # the amdgpu device dir exposing the perf-level + fabric-clock knobs
+  local d
+  for d in /sys/class/drm/card*/device; do
+    [[ -f "$d/power_dpm_force_performance_level" && -f "$d/pp_dpm_fclk" ]] || continue
+    printf '%s\n' "$d"
+    return 0
+  done
+  return 1
+}
+
+_pinned() { # $1 device dir — 0 when the ACTIVE (*) fclk row is the last (top) row
+  local d="$1" starred top
+  starred="$(grep -n '\*' "$d/pp_dpm_fclk" 2>/dev/null | tail -n 1 | cut -d: -f1)"
+  top="$(wc -l < "$d/pp_dpm_fclk" 2>/dev/null)"
+  [[ -n "$starred" && -n "$top" && "$starred" == "$top" ]]
+}
+
+cmd_apply() {
+  local d="" i
+  # The unit starts at multi-user.target, but amdgpu may still be probing on a
+  # cold boot — wait for the sysfs nodes rather than failing the one shot.
+  for i in $(seq 1 30); do
+    d="$(_card)" && break
+    sleep 1
+  done
+  if [[ -z "$d" ]]; then
+    _log "apply FAILED: no amdgpu device with power_dpm_force_performance_level + pp_dpm_fclk after 30s"
+    return 1
+  fi
+  if ! printf 'high\n' > "$d/power_dpm_force_performance_level" 2>/dev/null; then
+    _log "apply FAILED: cannot write 'high' to $d/power_dpm_force_performance_level (need root)"
+    return 1
+  fi
+  # The SMU applies the forced level asynchronously on some boots.
+  for i in 1 2 3 4 5; do
+    _pinned "$d" && break
+    sleep 1
+  done
+  local lvl fclk mclk soc
+  lvl="$(cat "$d/power_dpm_force_performance_level" 2>/dev/null)"
+  fclk="$(tr '\n' ' ' < "$d/pp_dpm_fclk" 2>/dev/null)"
+  mclk="$(tr '\n' ' ' < "$d/pp_dpm_mclk" 2>/dev/null)"
+  soc="$(tr '\n' ' ' < "$d/pp_dpm_socclk" 2>/dev/null)"
+  if _pinned "$d"; then
+    _log "applied: perf_level=$lvl dev=$d fclk=[$fclk] mclk=[$mclk] socclk=[$soc]"
+    return 0
+  fi
+  _log "apply WROTE but fclk is NOT pinned at top: perf_level=$lvl fclk=[$fclk] — investigate before trusting this soak day"
+  return 1
+}
+
+cmd_release() {
+  local d
+  d="$(_card)" || { _log "release: no amdgpu pp sysfs found"; return 1; }
+  if printf 'auto\n' > "$d/power_dpm_force_performance_level" 2>/dev/null; then
+    _log "released: perf_level=auto dev=$d"
+    return 0
+  fi
+  _log "release FAILED: cannot write 'auto' to $d/power_dpm_force_performance_level (need root)"
+  return 1
+}
+
+cmd_status() {
+  local d
+  d="$(_card)" || { echo "no amdgpu pp sysfs found"; return 1; }
+  echo "device: $d"
+  echo "perf_level: $(cat "$d/power_dpm_force_performance_level" 2>/dev/null)"
+  echo "fclk:  $(tr '\n' ' ' < "$d/pp_dpm_fclk" 2>/dev/null)"
+  echo "mclk:  $(tr '\n' ' ' < "$d/pp_dpm_mclk" 2>/dev/null)"
+  echo "socclk: $(tr '\n' ' ' < "$d/pp_dpm_socclk" 2>/dev/null)"
+  if _pinned "$d"; then echo "verdict: PINNED (fclk active level is top)"; else echo "verdict: NOT PINNED"; fi
+}
+
+case "${1:-}" in
+  apply)   cmd_apply ;;
+  release) cmd_release ;;
+  status)  cmd_status ;;
+  *) echo "Usage: $0 {apply|release|status}" >&2; exit 2 ;;
+esac
diff --git a/incredible_auto_dev/scripts/automation/host-guard/reset-forensics.sh b/incredible_auto_dev/scripts/automation/host-guard/reset-forensics.sh
index 80118cc3..094b24fa 100755
--- a/incredible_auto_dev/scripts/automation/host-guard/reset-forensics.sh
+++ b/incredible_auto_dev/scripts/automation/host-guard/reset-forensics.sh
@@ -23,24 +23,39 @@
 #
 # Usage / stdout contract — exactly one line, ALWAYS exit 0 (advisory by
 # construction, like doctor.sh; a broken forensics reader must never stop a run):
-#   check              RESET|<hex>|<cause>|<hits>/<boots>|<prev_boot_id>
+#   check              RESET|<hex>|<cause>|<hits>/<boots>|<crashed_boot_id>
 #                      CLEAN|<why>
 #                      UNKNOWN|<why>
 #   ensure-postmortem  POSTMORTEM|<path>|new   POSTMORTEM|<path>|existing
 #                      NONE|<why>              UNKNOWN|<why>
+#   streak             STREAK|<hits>/<boots>   UNKNOWN|<why>
 #   report             print the newest bundle (rc 1 when there is none)
 #
 # NO-OP RULE (roadmap §20): a host whose kernel prints no reset-reason line —
 # every non-AMD box, and every AMD box that has never reset — reports CLEAN and
 # writes nothing at all. No config file is required for the read-only paths.
 #
+# BOOT-WALK + WATERMARK (fix for the 2026-08-10 crash-#16 blind spot): the
+# decode line is printed by the boot AFTER a crash, and the original detector
+# read ONLY boot 0's kernel log. A fault whose decode line lands in an
+# intermediate boot that is then shut down cleanly (crash 22:30 → short boot →
+# clean poweroff 22:54) was therefore invisible forever — and because
+# ensure-postmortem gates on the same read, its evidence was never frozen.
+# Now detection walks every boot NEWER than a persisted watermark (the last
+# boot already examined; bounded to the last $WINDOW boots when no watermark
+# is usable) and reports the newest unprocessed fault. `check` never writes;
+# `ensure-postmortem` freezes one bundle PER unprocessed fault, then advances
+# the watermark. The HOST_GUARD_RESET_KLOG_FILE seam keeps the original
+# register-anchored single-boot behavior and never touches the watermark.
+#
 # Injection seams (how tests fake the world — no root, no journal, no API):
 #   HOST_GUARD_RESET_KLOG_FILE       stands in for `journalctl -k -b 0`
 #   HOST_GUARD_RESET_KLOG_DIR        per-boot logs: <dir>/<boot-id>.klog (streak)
 #   HOST_GUARD_RESET_BOOTS_FILE      stands in for `journalctl --list-boots`
-#   HOST_GUARD_RESET_JOURNAL_TAIL_FILE  stands in for `journalctl -b -1 -n 80`
+#   HOST_GUARD_RESET_JOURNAL_TAIL_FILE  stands in for `journalctl -b <dead> -n 80`
 #   HOST_GUARD_POSTMORTEM_DIR        bundle dir (default <tmp-root>/host-guard/postmortems)
 #   HOST_GUARD_RESET_BOOT_WINDOW     how many recent boots the streak scans (10)
+#   HOST_GUARD_RESET_WATERMARK_FILE  last-examined-boot marker (default <tmp-root>/host-guard/reset-watermark)
 #   HOST_GUARD_REGISTRY_DIR / CHAIN_TMP_ROOT / HOST_GUARD_EVENTS_FILE (via the lib)
 #
 # COST: every kernel-log read is a STREAM into `grep -m1`/`grep -q`, which exits
@@ -81,6 +96,7 @@ WINDOW="${HOST_GUARD_RESET_BOOT_WINDOW:-10}"
 POSTMORTEM_DIR="${HOST_GUARD_POSTMORTEM_DIR:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/postmortems}"
 EVENTS_FILE="${HOST_GUARD_EVENTS_FILE:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/events.jsonl}"
 GLOBAL_HWMON="${HOST_GUARD_HWMON_GLOBAL_DIR:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/hwmon}/hwmon.csv"
+WATERMARK_FILE="${HOST_GUARD_RESET_WATERMARK_FILE:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/reset-watermark}"
 
 # ── Boot enumeration ────────────────────────────────────────────────────────
 
@@ -117,10 +133,38 @@ _boot_reset_line() { # $1 boot id → that boot's reset-reason line (empty if no
   return 0
 }
 
+_boot_first_epoch() { # $1 boot id → epoch of that boot's first entry ("" if unknown)
+  # Parsed from the boot list ("<idx> <bid> <Day> <date> <time> <tz> …") so it
+  # works through the BOOTS_FILE seam too. Degrades to "" — callers fall back
+  # to the current boot's btime, which is the pre-watermark behavior.
+  local bid="${1:-}" row
+  [[ -n "$bid" ]] || return 0
+  row="$(_boot_rows | awk -v b="$bid" '$2 == b {print; exit}')"
+  [[ -n "$row" ]] || return 0
+  date -d "$(awk '{print $4" "$5" "$6}' <<< "$row")" +%s 2>/dev/null || true
+}
+
+_wm_read() { [[ -r "$WATERMARK_FILE" ]] && head -n 1 "$WATERMARK_FILE" 2>/dev/null; return 0; }
+
+_wm_write() { # atomic-enough: a torn watermark must never mark a fault as seen
+  local bid="${1:-}"
+  [[ -n "$bid" ]] || return 0
+  mkdir -p "$(dirname "$WATERMARK_FILE")" 2>/dev/null || return 0
+  if printf '%s\n' "$bid" > "$WATERMARK_FILE.tmp.$$" 2>/dev/null; then
+    mv -f "$WATERMARK_FILE.tmp.$$" "$WATERMARK_FILE" 2>/dev/null
+  fi
+  rm -f "$WATERMARK_FILE.tmp.$$" 2>/dev/null
+  return 0
+}
+
 # ── Detection (sets globals; both subcommands share it) ─────────────────────
 
 _DET_STATUS="" _DET_LINE="" _DET_HEX="" _DET_CAUSE="" _DET_WHY=""
 _DET_HITS=0 _DET_TOTAL=0 _DET_PREV="" _DET_ROWS=""
+# Walk-mode extras: the boot that LOGGED the reported fault's decode line, the
+# full unprocessed-fault list ("<crashed>|<detecting>|<line>" per line), and the
+# newest enumerated boot (watermark target). All empty in KLOG_FILE legacy mode.
+_DET_DETBOOT="" _DET_FAULTS="" _DET_LAST_ROW_BID=""
 
 _streak() { # fills _DET_HITS/_DET_TOTAL/_DET_ROWS over the last $WINDOW boots
   # _DET_HITS counts FAULT-class boots only; a planned reboot is recorded in the
@@ -146,10 +190,37 @@ _streak() { # fills _DET_HITS/_DET_TOTAL/_DET_ROWS over the last $WINDOW boots
   return 0
 }
 
+_parse_fault_line() { # $1 decode line → _DET_HEX/_DET_CAUSE
+  _DET_HEX="$(sed -n 's/.*reset reason \[\([^]]*\)\].*/\1/p' <<< "${1:-}")"
+  _DET_CAUSE="$(sed -n 's/.*reset reason \[[^]]*\]:[[:space:]]*//p' <<< "${1:-}")"
+  [[ -n "$_DET_CAUSE" ]] || _DET_CAUSE="${1:-}"
+}
+
+_classify_current_line() { # register-anchored classification of _DET_LINE (legacy path)
+  if [[ -z "$_DET_LINE" ]]; then
+    _DET_STATUS="CLEAN"
+    _DET_WHY="no reset-reason line in this boot's kernel log — the previous shutdown was orderly (or this platform exposes no reset-reason register)"
+    return 0
+  fi
+  if _is_benign "$_DET_LINE"; then
+    _DET_STATUS="CLEAN"
+    _DET_WHY="previous boot ended in a software-initiated reboot, not a fault (${_DET_LINE#*: })"
+    return 0
+  fi
+  _DET_STATUS="RESET"
+  _parse_fault_line "$_DET_LINE"
+  _streak
+  _DET_PREV="$(_prev_boot_id)"
+  return 0
+}
+
 _detect() {
   _DET_STATUS="" _DET_LINE="" _DET_HEX="" _DET_CAUSE="" _DET_WHY=""
+  _DET_PREV="" _DET_DETBOOT="" _DET_FAULTS="" _DET_LAST_ROW_BID=""
   local n=0
 
+  # Seam: a single stand-in for the CURRENT boot's kernel log keeps the original
+  # register-anchored behavior — and never touches the watermark.
   if [[ -n "${HOST_GUARD_RESET_KLOG_FILE:-}" ]]; then
     if [[ ! -r "$HOST_GUARD_RESET_KLOG_FILE" ]]; then
       _DET_STATUS="UNKNOWN"
@@ -157,48 +228,99 @@ _detect() {
       return 0
     fi
     _DET_LINE="$(grep -i -m1 "$RESET_PAT" "$HOST_GUARD_RESET_KLOG_FILE" 2>/dev/null)"
-  elif command -v journalctl >/dev/null 2>&1; then
-    # Liveness probe first: journalctl can exist and still return nothing when
-    # this user cannot read the kernel log. Without the probe, "no permission"
-    # and "no reset line" would both look CLEAN — the exact false negative this
-    # whole script exists to prevent.
-    if [[ -z "$(journalctl -k -b 0 --no-pager -n 1 2>/dev/null)" ]]; then
+    _classify_current_line
+    return 0
+  fi
+
+  if [[ -z "${HOST_GUARD_RESET_KLOG_DIR:-}" ]]; then
+    if command -v journalctl >/dev/null 2>&1; then
+      # Liveness probe first: journalctl can exist and still return nothing when
+      # this user cannot read the kernel log. Without the probe, "no permission"
+      # and "no reset line" would both look CLEAN — the exact false negative this
+      # whole script exists to prevent.
+      if [[ -z "$(journalctl -k -b 0 --no-pager -n 1 2>/dev/null)" ]]; then
+        _DET_STATUS="UNKNOWN"
+        _DET_WHY="journalctl returned no kernel log for this boot — this user probably cannot read it; fix with: sudo usermod -aG systemd-journal \$USER (then log out and back in)"
+        return 0
+      fi
+    elif [[ -r /var/log/kern.log ]]; then
+      # kern.log carries history but cannot be scoped to THIS boot, so a hit here
+      # is not evidence that the LAST boot died. Report honestly, never guess.
+      n="$(grep -c -i "$RESET_PAT" /var/log/kern.log 2>/dev/null)"
+      [[ "$n" =~ ^[0-9]+$ ]] || n=0
+      _DET_STATUS="UNKNOWN"
+      _DET_WHY="journalctl is unavailable; /var/log/kern.log carries $n reset-reason line(s) but cannot be scoped to the current boot — install systemd-journal access for an authoritative read"
+      return 0
+    else
       _DET_STATUS="UNKNOWN"
-      _DET_WHY="journalctl returned no kernel log for this boot — this user probably cannot read it; fix with: sudo usermod -aG systemd-journal \$USER (then log out and back in)"
+      _DET_WHY="no readable kernel log (no journalctl, no /var/log/kern.log) — the platform reset-reason register cannot be read on this host"
       return 0
     fi
+  fi
+
+  # Boot-walk: examine every boot newer than the watermark (bounded to the last
+  # $WINDOW boots when no watermark is usable) for a non-benign decode line.
+  # A decode line in boot N is evidence that boot N-1 died — including decode
+  # lines that landed in an intermediate boot the operator later shut down
+  # cleanly, the case the old boot-0-only read was blind to.
+  local rows
+  rows="$(_boot_rows)"
+  if [[ -z "$rows" ]]; then
+    # No boot enumeration — degrade to the original single-boot read.
     _DET_LINE="$(journalctl -k -b 0 --no-pager 2>/dev/null | grep -i -m1 "$RESET_PAT")"
-  elif [[ -r /var/log/kern.log ]]; then
-    # kern.log carries history but cannot be scoped to THIS boot, so a hit here
-    # is not evidence that the LAST boot died. Report honestly, never guess.
-    n="$(grep -c -i "$RESET_PAT" /var/log/kern.log 2>/dev/null)"
-    [[ "$n" =~ ^[0-9]+$ ]] || n=0
-    _DET_STATUS="UNKNOWN"
-    _DET_WHY="journalctl is unavailable; /var/log/kern.log carries $n reset-reason line(s) but cannot be scoped to the current boot — install systemd-journal access for an authoritative read"
-    return 0
-  else
-    _DET_STATUS="UNKNOWN"
-    _DET_WHY="no readable kernel log (no journalctl, no /var/log/kern.log) — the platform reset-reason register cannot be read on this host"
+    _classify_current_line
     return 0
   fi
 
-  if [[ -z "$_DET_LINE" ]]; then
-    _DET_STATUS="CLEAN"
-    _DET_WHY="no reset-reason line in this boot's kernel log — the previous shutdown was orderly (or this platform exposes no reset-reason register)"
-    return 0
+  local total wm seen_wm=0 idx0=0 inset row bid prevbid="" line
+  total="$(awk 'END{print NR}' <<< "$rows")"
+  wm="$(_wm_read)"
+  if [[ -n "$wm" ]] && ! awk '{print $2}' <<< "$rows" | grep -qx "$wm"; then
+    wm=""  # watermark rotated out of journal retention — fall back to the window bound
   fi
-  if _is_benign "$_DET_LINE"; then
+  while IFS= read -r row; do
+    [[ -n "$row" ]] || continue
+    idx0=$(( idx0 + 1 ))
+    bid="$(awk '{print $2}' <<< "$row")"
+    if [[ -n "$wm" ]]; then
+      inset=$seen_wm                       # only boots AFTER the watermark boot
+      [[ "$bid" == "$wm" ]] && seen_wm=1
+    else
+      inset=$(( idx0 > total - WINDOW ? 1 : 0 ))
+    fi
+    if (( inset )); then
+      line="$(_boot_reset_line "$bid")"
+      if [[ -n "$line" ]] && ! _is_benign "$line"; then
+        _DET_FAULTS+="${prevbid:-unknown}|$bid|$line"$'\n'
+      fi
+    fi
+    prevbid="$bid"
+  done <<< "$rows"
+  _DET_LAST_ROW_BID="$prevbid"
+
+  if [[ -z "$_DET_FAULTS" ]]; then
     _DET_STATUS="CLEAN"
-    _DET_WHY="previous boot ended in a software-initiated reboot, not a fault (${_DET_LINE#*: })"
+    line="$(_boot_reset_line "$prevbid")"
+    if [[ -n "$line" ]] && _is_benign "$line"; then
+      _DET_WHY="previous boot ended in a software-initiated reboot, not a fault (${line#*: })"
+    else
+      _DET_WHY="no unprocessed fault reset in the examined boot history${wm:+ (watermark $wm)}"
+    fi
     return 0
   fi
 
+  # Report the NEWEST unprocessed fault; ensure-postmortem bundles every one.
+  # printf, not a herestring: _DET_FAULTS already ends in \n and <<< would add
+  # a second, making tail -n 1 return the empty line.
+  local newest rest
+  newest="$(printf '%s' "$_DET_FAULTS" | tail -n 1)"
+  _DET_PREV="${newest%%|*}"
+  rest="${newest#*|}"
+  _DET_DETBOOT="${rest%%|*}"
+  _DET_LINE="${rest#*|}"
   _DET_STATUS="RESET"
-  _DET_HEX="$(sed -n 's/.*reset reason \[\([^]]*\)\].*/\1/p' <<< "$_DET_LINE")"
-  _DET_CAUSE="$(sed -n 's/.*reset reason \[[^]]*\]:[[:space:]]*//p' <<< "$_DET_LINE")"
-  [[ -n "$_DET_CAUSE" ]] || _DET_CAUSE="$_DET_LINE"
+  _parse_fault_line "$_DET_LINE"
   _streak
-  _DET_PREV="$(_prev_boot_id)"
   return 0
 }
 
@@ -242,12 +364,14 @@ _render_records() { # section 3 — and harvest roots/sessions for 4 and 5
   return 0
 }
 
-_render_csv_tail() { # $1 csv path, $2 label — the samples that PRECEDE this boot
-  local csv="$1" label="$2" bt rows last mt
+_render_csv_tail() { # $1 csv path, $2 label, $3 upper-bound epoch — samples PRECEDING the detecting boot
+  local csv="$1" label="$2" bt="${3:-}" rows last mt
   [[ -f "$csv" ]] || return 0
-  bt="$(hg_boot_epoch)"
+  [[ -n "$bt" ]] || bt="$(hg_boot_epoch)"
   # Boot-relative, never a plain tail: a sampler that restarted after the reboot
   # keeps appending, and tailing it would label live idle data "time of death".
+  # For a late-detected fault the bound is the DETECTING boot's first entry, so
+  # samples from intermediate boots never masquerade as the dying breath.
   rows="$(awk -F, -v b="$bt" '$1 ~ /^[0-9]+$/ && $1 + 0 < b' "$csv" 2>/dev/null | tail -n 20)"
   printf '### %s\n\n' "$label"
   printf -- '- file: `%s`\n' "$csv"
@@ -264,12 +388,15 @@ _render_csv_tail() { # $1 csv path, $2 label — the samples that PRECEDE this b
 }
 
 _render() {
-  local now
+  local now before=""
   now="$(date '+%Y-%m-%d %H:%M:%S %Z')"
+  # Telemetry upper bound: the first entry of the boot that logged the decode
+  # line. Empty (→ current btime) in legacy mode or when the row is unparsable.
+  [[ -z "${_DET_DETBOOT:-}" ]] || before="$(_boot_first_epoch "$_DET_DETBOOT")"
 
   printf '# Machine reset postmortem — boot %s\n\n' "${_DET_PREV:-unknown}"
   printf 'Generated %s by `scripts/automation/host-guard/reset-forensics.sh`.\n\n' "$now"
-  printf 'The previous boot did not shut down. The platform reset-reason register says\n'
+  printf 'Boot `%s` did not shut down. The platform reset-reason register says\n' "${_DET_PREV:-unknown}"
   printf 'the HARDWARE asserted reset, so the kernel was never notified and no software\n'
   printf 'guard — CPU mask, memory ceiling, browser confinement — could have prevented\n'
   printf 'it. Remediation is firmware/hardware: see `docs/host-guard.md` §\n'
@@ -297,12 +424,12 @@ _render() {
   _render_records
 
   printf '## 4. Hardware telemetry, final seconds (1 Hz, fsync per line)\n\n'
-  _render_csv_tail "$GLOBAL_HWMON" "machine-global sampler"
+  _render_csv_tail "$GLOBAL_HWMON" "machine-global sampler" "$before"
   local root
   while read -r root; do
     [[ -n "$root" ]] || continue
-    _render_csv_tail "$root/logs/hwmon/hwmon.csv" "$(basename "$root")"
-    [[ -f "$root/logs/hwmon/hwmon.csv" ]] || _render_csv_tail "$root/logs/hwmon/hwmon.csv.1" "$(basename "$root") (rotated)"
+    _render_csv_tail "$root/logs/hwmon/hwmon.csv" "$(basename "$root")" "$before"
+    [[ -f "$root/logs/hwmon/hwmon.csv" ]] || _render_csv_tail "$root/logs/hwmon/hwmon.csv.1" "$(basename "$root") (rotated)" "$before"
   done <<< "$_STALE_ROOTS"
   printf 'Columns: `%s`\n\n' "epoch,tctl_c,gpu_edge_c,ppt_w,ppt_avg_w,nvme_c,dimm0_c,dimm1_c,acpitz_c,load1,mem_avail_mb,swap_free_mb,psi_cpu_avg10,psi_mem_avg10[,cpu_mhz]"
 
@@ -355,12 +482,16 @@ _render() {
   fi
 
   printf '## 7. Journal tail of the dead boot\n\n'
-  printf 'NOTE: journald syncs every 5 minutes by default, so the last minutes before a\n'
-  printf 'hard reset are usually MISSING here — trust §4 for the time of death.\n\n```\n'
+  printf 'NOTE: a quiet system can log NOTHING for many minutes before a hard reset\n'
+  printf '(and journald may also sync lazily) — trust §4 for the time of death.\n\n```\n'
   if [[ -n "${HOST_GUARD_RESET_JOURNAL_TAIL_FILE:-}" ]]; then
     tail -n 80 "$HOST_GUARD_RESET_JOURNAL_TAIL_FILE" 2>/dev/null
   elif command -v journalctl >/dev/null 2>&1; then
-    journalctl -b -1 -n 80 --no-pager 2>/dev/null
+    if [[ -n "${_DET_PREV:-}" && "$_DET_PREV" != "unknown" ]]; then
+      journalctl -b "$_DET_PREV" -n 80 --no-pager 2>/dev/null
+    else
+      journalctl -b -1 -n 80 --no-pager 2>/dev/null
+    fi
   fi
   printf '```\n\n'
 
@@ -394,7 +525,12 @@ cmd_check() {
 cmd_ensure_postmortem() {
   _detect
   case "$_DET_STATUS" in
-    CLEAN) printf 'NONE|%s\n' "$_DET_WHY"; return 0 ;;
+    CLEAN)
+      # Walk mode examined every boot in range and found nothing unprocessed —
+      # advance the watermark so the next run only pays for boots it has not
+      # seen. Legacy KLOG_FILE mode sets no _DET_LAST_ROW_BID and never writes.
+      [[ -z "${_DET_LAST_ROW_BID:-}" ]] || _wm_write "$_DET_LAST_ROW_BID"
+      printf 'NONE|%s\n' "$_DET_WHY"; return 0 ;;
     RESET) ;;
     *)     printf 'UNKNOWN|%s\n' "$_DET_WHY"; return 0 ;;
   esac
@@ -402,24 +538,59 @@ cmd_ensure_postmortem() {
   mkdir -p "$POSTMORTEM_DIR" 2>/dev/null \
     || { printf 'UNKNOWN|cannot create postmortem dir %s\n' "$POSTMORTEM_DIR"; return 0; }
 
-  local name="${_DET_PREV:-}"
-  [[ -n "$name" && "$name" != "unknown" ]] || name="prev-of-$(_hg_boot_id)"
-  local out="$POSTMORTEM_DIR/$name.md"
+  # One bundle PER unprocessed fault — a detection gap can span several resets
+  # (2026-08-10 had two in one day). Legacy mode carries exactly one fault, the
+  # current register, synthesized into the same record shape. Oldest first so
+  # latest.md ends on the newest bundle; the one-line output contract reports
+  # the newest fault's bundle.
+  local faults="${_DET_FAULTS:-}"
+  [[ -n "$faults" ]] || faults="${_DET_PREV:-unknown}|$(_hg_boot_id)|$_DET_LINE"$'\n'
+  local rec rest name out tmp result="" failed=0
+  while IFS= read -r rec; do
+    [[ -n "$rec" ]] || continue
+    _DET_PREV="${rec%%|*}"
+    rest="${rec#*|}"
+    _DET_DETBOOT="${rest%%|*}"
+    _DET_LINE="${rest#*|}"
+    _parse_fault_line "$_DET_LINE"
+    name="$_DET_PREV"
+    [[ -n "$name" && "$name" != "unknown" ]] || name="prev-of-$_DET_DETBOOT"
+    out="$POSTMORTEM_DIR/$name.md"
+    if [[ -f "$out" ]]; then
+      _link_latest "$out"
+      result="POSTMORTEM|$out|existing"
+      continue
+    fi
+    tmp="$out.tmp.$$"
+    _render > "$tmp" 2>/dev/null
+    if mv -f "$tmp" "$out" 2>/dev/null; then
+      _link_latest "$out"
+      result="POSTMORTEM|$out|new"
+    else
+      rm -f "$tmp" 2>/dev/null || true
+      failed=1
+      result="UNKNOWN|cannot write $out"
+    fi
+  done <<< "$faults"
 
-  if [[ -f "$out" ]]; then
-    _link_latest "$out"
-    printf 'POSTMORTEM|%s|existing\n' "$out"
-    return 0
+  # The watermark advances only when every bundle in the gap is on disk — a
+  # write failure must leave the fault visible to the next run.
+  if (( ! failed )) && [[ -n "${_DET_FAULTS:-}" && -n "${_DET_LAST_ROW_BID:-}" ]]; then
+    _wm_write "$_DET_LAST_ROW_BID"
   fi
+  printf '%s\n' "${result:-UNKNOWN|no bundle produced}"
+  return 0
+}
 
... [diff_bound] incredible_auto_dev/scripts/automation/host-guard/reset-forensics.sh: 28 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/scripts/automation/lib/agent_permissions.py b/incredible_auto_dev/scripts/automation/lib/agent_permissions.py
index f570566a..7cbfa730 100644
--- a/incredible_auto_dev/scripts/automation/lib/agent_permissions.py
+++ b/incredible_auto_dev/scripts/automation/lib/agent_permissions.py
@@ -24,6 +24,10 @@ CLI:
     python3 agent_permissions.py effort <agent>       # --effort value (max|medium)
     python3 agent_permissions.py model <agent>        # resolved model id or empty
     python3 agent_permissions.py tier-model <tier>    # tier's claude model id or empty
+    python3 agent_permissions.py output-style <agent>        # output style name or "" (rc 3 = invalid config)
+    python3 agent_permissions.py output-style-text <name>    # emulation body for the interactive backend (rc 4 = none known)
+    python3 agent_permissions.py output-styles-configured    # "<name>\t<source>" per configured style (env + table), unvalidated
+    python3 agent_permissions.py output-style-check          # validate every configured style; rc 3 on the first invalid one
     python3 agent_permissions.py self-test
 """
 from __future__ import annotations
@@ -336,6 +340,218 @@ def effort_for(agent: str) -> str:
     return EFFORT_OVERRIDES.get(agent, EFFORT_DEFAULT)
 
 
+# ── Output styles (STYLE-1 experiment, default off) ──────────────────────────
+# Claude Code has NO --output-style flag; the per-invocation form is
+# `--settings '{"outputStyle":"<name>"}'`. The CLI SILENTLY ignores names it
+# does not know (falls back to default), so validation lives here and a bad
+# name must FAIL the dispatch loudly — otherwise an experiment arm runs
+# mislabeled. Names are restricted to a JSON-safe alphabet because the shell
+# seam interpolates them into the settings literal verbatim.
+#
+# Precedence (output_style_for):
+#   CHAIN_OUTPUT_STYLE_OVERRIDE   global, EVERY agent (judges included — debug
+#                                 only; loud NOTICE per judge dispatch)
+#   CHAIN_AGENT_OUTPUT_STYLE      "developer=Concise,qa=Concise" — same grammar
+#                                 as CHAIN_AGENT_EFFORT; judge entries refused
+#   OUTPUT_STYLE_OVERRIDES        this table — ONLY when CHAIN_OUTPUT_STYLES=true
+#   ""                            = the CLI default; the seam passes no flag
+# Why a table and not agents/<name>/agent.yaml: vendored deployments have no
+# agents/ dir at CWD (only .claude/, config/, scripts/ are symlinked), and the
+# style is never rendered into frontmatter (subagents cannot use it anyway).
+OUTPUT_STYLE_BUILTINS: tuple[str, ...] = ("Default", "Proactive", "Concise", "Explanatory")
+OUTPUT_STYLE_REFUSED: dict[str, str] = {
+    "Learning": "it asks the human to write code (stalls headless runs)",
+}
+OUTPUT_STYLE_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 _-]*$")
+PROJECT_OUTPUT_STYLES_DIR = Path(".claude/output-styles")
+# Wave 1 (2026-08-20): the long, machine-consumed, non-judge steps. Judges
+# (JUDGE_AGENTS) must never appear here — the self-test asserts it (D4).
+# Human-facing writers (iteration-summarizer, demo-narrator, readme-maintainer,
+# retro-analyst, ui-test-designer) stay Default by design.
+OUTPUT_STYLE_OVERRIDES: dict[str, str] = {
+    "developer":              "Concise",
+    "qa":                     "Concise",  # both generate-mode and validate-mode
+    "browser-qa-agent":       "Concise",
+    "orchestrator":           "Concise",
+    "ui-impact-analyst":      "Concise",
+    "ux-regression-reviewer": "Concise",
+}
+# Emulation bodies for the interactive backend (Agent-tool subagents never see
+# the default system prompt, the only place Claude Code injects a style).
+# Rules 1-6 are verbatim from the CLI binary; the closing sentence replaces the
+# built-in's "these rules win" clause with an artifact-contract guard because
+# here the text lands in the USER turn, below the agent's system prompt.
+OUTPUT_STYLE_EMULATION_TEXT: dict[str, str] = {
+    "Concise": (
+        'The engine requested Claude Code\'s built-in "Concise" output style for this dispatch. '
+        "Subagents do not receive it natively, so apply it from here:\n"
+        "1. **Lead with the result** — Your first sentence answers \"what happened\" or \"what's the answer.\" "
+        "No preamble (\"Let me...\", \"Now I'll...\") and no closing recap of what you already said.\n"
+        "2. **Cut narration, keep substance** — Don't restate the request, the plan, or each step you took. "
+        "Report outcomes, decisions, and anything the user must act on.\n"
+        "3. **Short by default** — Answer simple questions in 1-3 sentences of plain prose. "
+        "Use headers, tables, and bullet lists only when they carry real structure, never as decoration.\n"
+        "4. **State things plainly** — Skip hedging boilerplate. Mention a caveat only when it changes what the user should do next.\n"
+        "5. **Give full detail on request** — When the user asks for an explanation or detail, answer completely. "
+        "Conciseness never means withholding requested information.\n"
+        "6. **Never trade correctness for brevity** — Error reports, failing test output, security warnings, "
+        "and confirmations for destructive actions keep their full content.\n"
+        "These rules shape only your chat/transcript prose. Every file, report section, table, verdict line, "
+        "and handoff that your agent instructions require must still be written in full."
+    ),
+}
+
+
+class OutputStyleError(ValueError):
+    """Invalid output-style configuration (unknown/refused/unsafe name)."""
+
+
+def _is_judge(agent: str) -> bool:
+    return agent in JUDGE_AGENTS or any(agent.startswith(j + "-") for j in JUDGE_AGENTS)
+
+
+def _custom_output_styles(styles_dir: Path = PROJECT_OUTPUT_STYLES_DIR) -> dict[str, str]:
+    """{name: body} for every project .claude/output-styles/*.md, keyed by file
+    stem AND frontmatter `name:` when present (the body doubles as emulation text)."""
+    out: dict[str, str] = {}
+    if not styles_dir.is_dir():
+        return out
+    for f in sorted(styles_dir.glob("*.md")):
+        try:
+            text = f.read_text(encoding="utf-8")
+        except OSError:
+            continue
+        body, fm = text, _parse_frontmatter(text)
+        if fm is not None:
+            end = text.find("\n---", 3)
+            body = text[end + 4:] if end != -1 else text
+        out[f.stem] = body.strip()
+        name = fm.get("name") if fm else None
+        if isinstance(name, str) and name.strip():
+            out[name.strip()] = body.strip()
+    return out
+
+
+def _canonical_output_style(raw: str, styles_dir: Path = PROJECT_OUTPUT_STYLES_DIR) -> str:
+    """Validate + canonicalize. "" = Default (pass nothing). Raises OutputStyleError."""
+    name = (raw or "").strip()
+    if not name:
+        return ""
+    if not OUTPUT_STYLE_NAME_RE.match(name):
+        raise OutputStyleError(
+            f"output style {raw!r}: names must match [A-Za-z][A-Za-z0-9 _-]* "
+            f"(interpolated verbatim into the --settings JSON)")
+    low = name.lower()
+    for refused, why in OUTPUT_STYLE_REFUSED.items():
+        if low == refused.lower():
+            raise OutputStyleError(f"output style {refused!r} is refused: {why}")
+    if low == "default":
+        return ""
+    for builtin in OUTPUT_STYLE_BUILTINS:
+        if low == builtin.lower():
+            return builtin
+    if name in _custom_output_styles(styles_dir):
+        return name
+    raise OutputStyleError(
+        f"unknown output style {raw!r}; allowed: {', '.join(OUTPUT_STYLE_BUILTINS)} or a project "
+        f"{styles_dir}/<name>.md (Claude Code ignores unknown names SILENTLY, so this layer refuses them)")
+
+
+def _experiment_output_style_override(agent: str) -> str | None:
+    """CHAIN_AGENT_OUTPUT_STYLE="developer=Concise[,agent=Style]" — grammar and
+    judge guard identical to _experiment_effort_override."""
+    raw = os.environ.get("CHAIN_AGENT_OUTPUT_STYLE", "").strip()
+    if not raw:
+        return None
+    for part in raw.split(","):
+        key, _, value = part.partition("=")
+        if key.strip() != agent or not value.strip():
+            continue
+        if _is_judge(agent):
+            print(f"[agent-permissions] CHAIN_AGENT_OUTPUT_STYLE refused for judge '{agent}' — "
+                  f"a judge's verdict prose is the product; judges never run under an output style (D4).",
+                  file=sys.stderr)
+            return None
+        return value.strip()
+    return None
+
+
+def output_style_for(agent: str, styles_dir: Path = PROJECT_OUTPUT_STYLES_DIR) -> str:
+    """Canonical style name for the agent, or "" (= CLI default; pass no flag).
+    Raises OutputStyleError on invalid config — callers must FAIL LOUD."""
+    override = os.environ.get("CHAIN_OUTPUT_STYLE_OVERRIDE", "").strip()
+    if override:
+        name = _canonical_output_style(override, styles_dir)
+        if name and _is_judge(agent):
+            print(f"[agent-permissions] NOTICE: CHAIN_OUTPUT_STYLE_OVERRIDE={name} is styling judge "
+                  f"'{agent}' — debug use only; never measure a judge under a style (D4).", file=sys.stderr)
+        return name
+    mapped = _experiment_output_style_override(agent)
+    if mapped is not None:
+        return _canonical_output_style(mapped, styles_dir)
+    if os.environ.get("CHAIN_OUTPUT_STYLES", "false").strip().lower() != "true":
+        return ""
+    raw = OUTPUT_STYLE_OVERRIDES.get(agent, "")
+    if not raw or _is_judge(agent):
+        return ""
+    return _canonical_output_style(raw, styles_dir)
+
+
+def output_style_text(name: str, styles_dir: Path = PROJECT_OUTPUT_STYLES_DIR) -> str:
+    """Emulation body (interactive backend). Raises when the name is invalid or no body is known."""
+    canonical = _canonical_output_style(name, styles_dir)
+    if not canonical:
+        raise OutputStyleError("Default has no emulation text (it is the absence of a style)")
+    if canonical in OUTPUT_STYLE_EMULATION_TEXT:
+        return OUTPUT_STYLE_EMULATION_TEXT[canonical]
+    custom = _custom_output_styles(styles_dir)
+    if custom.get(canonical):
+        return custom[canonical]
+    raise OutputStyleError(
+        f"no emulation text known for output style {canonical!r} — add it to "
+        f"OUTPUT_STYLE_EMULATION_TEXT (verbatim from the CLI binary) before using it on the interactive backend")
+
+
+def _soft_canonicalize(raw: str) -> str:
+    """Best-effort casing fix for configured_output_styles(), which is
+    deliberately UNVALIDATED: reuse _canonical_output_style (the same
+    case-insensitive builtin canonicalizer output_style_for() validates
+    against) but never raise and never collapse to "". An unknown/refused/
+    invalid name, a custom project style, or the literal "default" all pass
+    through UNCHANGED — those are left for output-style-check / the
+    binary-presence check below to validate or report; only a recognized
+    builtin (any casing) comes back rewritten to its exact spelling, e.g.
+    "concise" -> "Concise", so doctor's binary-marker grep (which does not
+    add -i — see check_output_styles) and any other consumer see one
+    canonical name."""
+    try:
+        canonical = _canonical_output_style(raw)
+    except OutputStyleError:
+        return raw
+    return canonical or raw
+
+
+def configured_output_styles() -> list[tuple[str, str]]:
+    """Every style configured anywhere, UNVALIDATED, as (name, source):
+    env:CHAIN_OUTPUT_STYLE_OVERRIDE · env:CHAIN_AGENT_OUTPUT_STYLE[<agent>] ·
+    table:<agent> (only when CHAIN_OUTPUT_STYLES=true). Builtin names are
+    casing-canonicalized (_soft_canonicalize); table values are already
+    canonical by construction (asserted in _self_test). For doctor + boot
+    preflight."""
+    out: list[tuple[str, str]] = []
+    override = os.environ.get("CHAIN_OUTPUT_STYLE_OVERRIDE", "").strip()
+    if override:
+        out.append((_soft_canonicalize(override), "env:CHAIN_OUTPUT_STYLE_OVERRIDE"))
+    for part in os.environ.get("CHAIN_AGENT_OUTPUT_STYLE", "").split(","):
+        key, _, value = part.partition("=")
+        if key.strip() and value.strip():
+            out.append((_soft_canonicalize(value.strip()), f"env:CHAIN_AGENT_OUTPUT_STYLE[{key.strip()}]"))
+    if os.environ.get("CHAIN_OUTPUT_STYLES", "false").strip().lower() == "true":
+        for agent, style in OUTPUT_STYLE_OVERRIDES.items():
+            out.append((style, f"table:{agent}"))
+    return out
+
+
 def timeout_for(agent: str, neutral_dir: Path = NEUTRAL_AGENTS_DIR) -> int | None:
     """Return the per-agent runtime cap in seconds, or None when the agent has
     no specific cap (callers fall back to the flat global).
@@ -553,6 +769,58 @@ def _cmd_timeout(args: list[str]) -> int:
     return 0
 
 
+def _cmd_output_style(args: list[str]) -> int:
+    """Print the style for the agent ("" = none). rc 3 on invalid config —
+    the shell seams treat ANY non-zero rc as "refuse to dispatch"."""
+    if not args:
+        print("Usage: agent_permissions.py output-style <agent>", file=sys.stderr); return 2
+    try:
+        print(output_style_for(args[0]))
+    except OutputStyleError as e:
+        print(f"[agent-permissions] ERROR: {e}", file=sys.stderr); return 3
+    return 0
+
+
+def _cmd_output_style_text(args: list[str]) -> int:
+    """rc 3 invalid name, rc 4 valid name without emulation text."""
+    if not args:
+        print("Usage: agent_permissions.py output-style-text <name>", file=sys.stderr); return 2
+    try:
+        _canonical_output_style(args[0])
+    except OutputStyleError as e:
+        print(f"[agent-permissions] ERROR: {e}", file=sys.stderr); return 3
+    try:
+        print(output_style_text(args[0]))
+    except OutputStyleError as e:
+        print(f"[agent-permissions] {e}", file=sys.stderr); return 4
+    return 0
+
+
+def _cmd_output_styles_configured(_args: list[str]) -> int:
+    for name, source in configured_output_styles():
+        print(f"{name}\t{source}")
+    return 0
+
+
+def _cmd_output_style_check(_args: list[str]) -> int:
+    """Validate every configured style. Judge entries → WARNING (seams refuse at
+    dispatch); invalid names → rc 3."""
+    bad = 0
+    for name, source in configured_output_styles():
+        try:
+            _canonical_output_style(name)
+        except OutputStyleError as e:
+            print(f"[agent-permissions] ERROR: {source}: {e}", file=sys.stderr); bad += 1; continue
+        agent = source.split(":", 1)[1].rstrip("]").split("[")[-1] if source != "env:CHAIN_OUTPUT_STYLE_OVERRIDE" else ""
+        if agent and _is_judge(agent):
+            print(f"[agent-permissions] WARNING: {source}: judge '{agent}' will refuse this style at dispatch (D4)",
+                  file=sys.stderr)
+    if bad:
+        return 3
+    print("output styles: OK")
+    return 0
+
+
 def _self_test() -> int:
     import tempfile
 
@@ -699,6 +967,54 @@ def _self_test() -> int:
         assert effort_for("browser-qa-agent") == "max", "browser-qa stays at max"
         assert effort_for("some-unknown-agent") == "max", "default must be max"
 
+        # Output styles (STYLE-1): table hygiene, precedence, validation, judge guard.
+        assert not (set(OUTPUT_STYLE_OVERRIDES) & JUDGE_AGENTS), "judges must never be in OUTPUT_STYLE_OVERRIDES (D4)"
+        for _v in OUTPUT_STYLE_OVERRIDES.values():
+            assert _canonical_output_style(_v) == _v, f"table value {_v!r} must be canonical"
+        custom_dir = d / "output-styles"; custom_dir.mkdir()
+        (custom_dir / "Terse.md").write_text("---\nname: Terse\ndescription: x\n---\nBe terse.\n", encoding="utf-8")
+        _keys = ("CHAIN_OUTPUT_STYLES", "CHAIN_AGENT_OUTPUT_STYLE", "CHAIN_OUTPUT_STYLE_OVERRIDE")
+        _saved = {k: os.environ.pop(k, None) for k in _keys}
+        try:
+            def _must_raise(fn, label):
+                try: fn()
+                except OutputStyleError: return
+                raise AssertionError(label)
+            kw = dict(styles_dir=custom_dir)
+            assert output_style_for("developer", **kw) == "", "knob off: table is dormant"
+            os.environ["CHAIN_OUTPUT_STYLES"] = "true"
+            assert output_style_for("developer", **kw) == "Concise", "knob on: table applies"
+            assert output_style_for("goal-evaluator", **kw) == "", "judge: never styled from the table"
+            assert output_style_for("browser-qa-replay", **kw) == "", "attribution names without an agent → default"
+            assert output_style_for("iteration-summarizer", **kw) == "", "human-facing writers stay Default"
+            os.environ["CHAIN_AGENT_OUTPUT_STYLE"] = "developer=explanatory,goal-evaluator=Concise,goal-evaluator-confirm=Concise,plain=Terse"
+            assert output_style_for("developer", **kw) == "Explanatory", "env map beats table + canonicalizes case"
+            assert output_style_for("goal-evaluator", **kw) == "", "judge guard: env map refused"
+            assert output_style_for("goal-evaluator-confirm", **kw) == "", "judge guard covers <judge>-* labels"
+            assert output_style_for("plain", **kw) == "Terse", "project custom style accepted"
+            os.environ["CHAIN_AGENT_OUTPUT_STYLE"] = "developer=Learning"
+            _must_raise(lambda: output_style_for("developer", **kw), "Learning must be refused")
+            os.environ["CHAIN_AGENT_OUTPUT_STYLE"] = "developer=Consise"
+            _must_raise(lambda: output_style_for("developer", **kw), "unknown name must raise")
+            del os.environ["CHAIN_AGENT_OUTPUT_STYLE"]
+            os.environ["CHAIN_OUTPUT_STYLE_OVERRIDE"] = "Proactive"
+            assert output_style_for("goal-evaluator", **kw) == "Proactive", "global override styles judges (debug, NOTICE)"
+            os.environ["CHAIN_OUTPUT_STYLE_OVERRIDE"] = "Default"
+            assert output_style_for("developer", **kw) == "", "explicit Default = pass nothing"
+            os.environ["CHAIN_OUTPUT_STYLE_OVERRIDE"] = 'Concise"}'
+            _must_raise(lambda: output_style_for("developer", **kw), "JSON-breaking name must be refused")
+            del os.environ["CHAIN_OUTPUT_STYLE_OVERRIDE"]
+            assert "Lead with the result" in output_style_text("Concise", styles_dir=custom_dir)
+            assert "these rules win" not in output_style_text("Concise", styles_dir=custom_dir)
+            assert output_style_text("Terse", styles_dir=custom_dir) == "Be terse."
+            _must_raise(lambda: output_style_text("Explanatory", styles_dir=custom_dir), "no emulation text must raise")
+            conf = configured_output_styles()
+            assert ("Concise", "table:developer") in conf, conf
+        finally:
+            for k, v in _saved.items():
+                if v is None: os.environ.pop(k, None)
+                else: os.environ[k] = v
+
     print("self-test passed")
     return 0
 
@@ -710,6 +1026,10 @@ _COMMANDS = {
     "model": _cmd_model,
     "tier-model": _cmd_tier_model,
     "timeout": _cmd_timeout,
+    "output-style": _cmd_output_style,
+    "output-style-text": _cmd_output_style_text,
+    "output-styles-configured": _cmd_output_styles_configured,
+    "output-style-check": _cmd_output_style_check,
     "self-test": lambda _args: _self_test(),
 }
 
diff --git a/incredible_auto_dev/scripts/automation/lib/analyze_telemetry.py b/incredible_auto_dev/scripts/automation/lib/analyze_telemetry.py
index a4146a09..84f6751d 100644
--- a/incredible_auto_dev/scripts/automation/lib/analyze_telemetry.py
+++ b/incredible_auto_dev/scripts/automation/lib/analyze_telemetry.py
@@ -25,6 +25,7 @@ from __future__ import annotations
 import argparse
 import json
 import os
+import statistics
 import sys
 import tempfile
 import time
@@ -280,6 +281,10 @@ def build_wall_report(paths: list[str]) -> dict[str, dict[str, Any]]:
         return sessions.setdefault(sid, {
             "iterations": [], "open": None, "halts": [],
             "paused_seconds": 0, "last_halt_ts": None,
+            # STYLE-1: flat per-dispatch cost rows for evaluate_cost_tripwire.
+            # Session-scoped (not per-iteration) because the baseline side is
+            # every unstyled row of the session, not just the recent window.
+            "usage_rows": [],
         })
 
     for path in paths:
@@ -333,9 +338,27 @@ def build_wall_report(paths: list[str]) -> dict[str, dict[str, Any]]:
                         "elapsed": int(event.get("elapsed") or 0),
                         "mode": event.get("mode") or "warn",
                         "at_step": event.get("at_step") or "?"}
+            elif kind == "claude_usage":
+                usage = event.get("usage")
+                if not isinstance(usage, dict):
+                    usage = {}
+                s["usage_rows"].append({
+                    "iter_name": (cur or {}).get("iter_name") or "",
+                    "agent": event.get("agent") or "unattributed",
+                    "output_style_requested": str(
+                        event.get("output_style_requested") or ""),
+                    "output_tokens": int(usage.get("output_tokens") or 0),
+                    "num_turns": int(event.get("num_turns") or 0)})
             elif kind == "review_verdict" and cur is not None:
+                # An empty verdict is DATA, not a formatting gap. goal-iter-lean
+                # emits review_verdict with verdict:"" when the reviewer was
+                # dispatched and returned WITHOUT a parseable `**Verdict:**` line
+                # (quota pauses excluded); resume-skipped reviews emit nothing at
+                # all. Keep the "" so evaluate_tripwire can see the gap — it used
+                # to be coerced to "?" and silently swallowed.
+                _rv = event.get("verdict")
                 cur["review_verdicts"].append({
-                    "verdict": event.get("verdict") or "?",
+                    "verdict": "" if _rv is None else str(_rv),
                     "attempt": int(event.get("attempt") or 0)})
             elif kind == "iter_config" and cur is not None:
                 cur["knob_active"] = True
@@ -460,13 +483,15 @@ def render_wall_json(report: dict[str, dict[str, Any]],
     return json.dumps(out, indent=2, default=str)
 
 
-# ── experiment tripwire (--tripwire) ─────────────────────────────────────────
+# ── experiment tripwire, quality dimension (--tripwire) ──────────────────────
 #
-# Guards opt-in speed experiments (e.g. CHAIN_AGENT_EFFORT=developer=high).
-# Looks at the last --window knob-active completed iterations and TRIPs when
-# quality moved: any REGRESSION verdict, any journey regression count > 0, or
-# first-attempt review FAILs in ≥2 of the window. Exit 3 on TRIP so shell
-# callers can auto-revert the knob.
+# Guards opt-in experiments (e.g. CHAIN_AGENT_EFFORT=developer=high,
+# CHAIN_OUTPUT_STYLES=true). Looks at the last --window knob-active completed
+# iterations and TRIPs when quality moved: any REGRESSION verdict, any journey
+# regression count > 0, an unparseable review verdict, or first-attempt review
+# FAILs in ≥2 of the window. Exit 3 on TRIP so shell callers can auto-revert the
+# knob. The cost dimension lives in evaluate_cost_tripwire below; --tripwire
+# runs both.
 
 
 def evaluate_tripwire(report: dict[str, dict[str, Any]], window: int = 3
@@ -486,6 +511,11 @@ def evaluate_tripwire(report: dict[str, dict[str, Any]], window: int = 3
             if int((rec["journey_deltas"] or {}).get("regressed") or 0) > 0:
                 tripped = True
                 reasons.append(f"{sid}/{rec['iter_name']}: journey regression recorded")
+            if any(rv["verdict"] == "" for rv in rec["review_verdicts"]):
+                tripped = True
+                reasons.append(
+                    f"{sid}/{rec['iter_name']}: unparseable review verdict "
+                    f"(verdict line missing)")
             if any(rv["verdict"] == "FAIL" and rv["attempt"] == 1
                    for rv in rec["review_verdicts"]):
                 fail_iters += 1
@@ -497,6 +527,60 @@ def evaluate_tripwire(report: dict[str, dict[str, Any]], window: int = 3
     return tripped, reasons
 
 
+# ── cost tripwire (--tripwire, second dimension) ─────────────────────────────
+#
+# Ground rule D5 (docs/improvement-roadmap.md): an earlier "be terser" change
+# INCREASED turn count and roughly doubled output tokens. A prose-shaping knob
+# (CHAIN_OUTPUT_STYLES) can fail the same way, and the quality dimension above
+# would never see it. So: compare the styled dispatches of the recent knob-active
+# window against the same agent's unstyled dispatches from the same session
+# (medians, so one runaway dispatch cannot trip it), and TRIP when the styled
+# side is more than 1.5x the baseline on output tokens or on turns.
+#
+# Both sides need >=3 rows; below that the medians are noise, not signal.
+
+_COST_RATIO = 1.5
+_COST_MIN_ROWS = 3
+
+
+def _fmt_med(v: float) -> str:
+    return str(int(v)) if float(v).is_integer() else f"{v:.1f}"
+
+
+def evaluate_cost_tripwire(report: dict[str, dict[str, Any]], window: int = 3
+                           ) -> tuple[bool, list[str]]:
+    reasons: list[str] = []
+    tripped = False
+    for sid, s in report.items():
+        rows = s.get("usage_rows") or []
+        if not rows:
+            continue
+        recent = {i["iter_name"] for i in
+                  [x for x in s["iterations"] if x["complete"] and x["knob_active"]][-window:]}
+        if not recent:
+            continue
+        styled_all = [r for r in rows
+                      if r["output_style_requested"] and r["iter_name"] in recent]
+        for agent in sorted({r["agent"] for r in styled_all}):
+            styled = [r for r in styled_all if r["agent"] == agent]
+            base = [r for r in rows
+                    if r["agent"] == agent and not r["output_style_requested"]]
+            if len(styled) < _COST_MIN_ROWS or len(base) < _COST_MIN_ROWS:
+                continue
+            style = ",".join(sorted({r["output_style_requested"] for r in styled}))
+            for metric in ("output_tokens", "num_turns"):
+                b = statistics.median([r[metric] for r in base])
+                v = statistics.median([r[metric] for r in styled])
+                if b <= 0 or v <= _COST_RATIO * b:
+                    continue
+                tripped = True
+                reasons.append(
+                    f"cost: {agent} median {metric} {_fmt_med(b)}→{_fmt_med(v)} "
+                    f"(+{int(round((v - b) / b * 100))}%) under {style} — D5 failure "
+                    f"mode (terse instructions → more turns/tokens)")
+    return tripped, reasons
+
+
 # ── self-test ────────────────────────────────────────────────────────────────
 
 _FIXTURE = [
@@ -599,6 +683,59 @@ _WALL_FIXTURE = [
 ]
 
 
+# STYLE-1 cost fixture: three unstyled (baseline) iterations followed by
+# `styled_iters` knob-active iterations whose developer rows carry
+# `output_style_requested`. Verdicts stay clean so ONLY the cost dimension can
+# trip. One claude_usage row per iteration → 3 baseline rows, `styled_iters`
+# styled rows (the ≥3-a-side floor is exercised by the styled_iters=2 variant).
+def _cost_fixture(sid: str, styled_tokens: int, styled_turns: int,
+                  styled_iters: int = 3) -> list[dict[str, Any]]:
+    ev: list[dict[str, Any]] = []
+
+    def _iter(n: int, styled: bool) -> None:
+        name = f"goal-c-iter-{n}"
+        ev.append({"event": "iter_start", "session_id": sid, "iter_name": name,
+                   "ts": f"2026-08-0{n}T10:00:00Z"})
+        if styled:
+            ev.append({"event": "iter_config", "session_id": sid,
+                       "key": "CHAIN_OUTPUT_STYLES",
+                       "value": "CHAIN_OUTPUT_STYLES=true",
+                       "ts": f"2026-08-0{n}T10:00:01Z"})
+        row: dict[str, Any] = {
+            "event": "claude_usage", "session_id": sid, "agent": "developer",
+            "num_turns": styled_turns if styled else 10,
+            "usage": {"output_tokens": styled_tokens if styled else 1000},
+            "ts": f"2026-08-0{n}T10:10:00Z"}
+        if styled:
+            row["output_style_requested"] = "Concise"
+        ev.append(row)
+        ev.append({"event": "iter_end", "session_id": sid, "iter_name": name,
+                   "verdict": "CONTINUE", "journey_deltas": {"regressed": 0},
+                   "ts": f"2026-08-0{n}T11:00:00Z"})
+
+    for n in range(1, 4):
+        _iter(n, styled=False)
+    for n in range(4, 4 + styled_iters):
+        _iter(n, styled=True)
+    return ev
+
+
+# STYLE-1: a knob-active iteration whose reviewer wrote no parseable verdict
+# line (_review_verdict() returned ""). Everything else is clean — only the
+# unparseable-verdict rule may fire here.
+_EMPTY_VERDICT_FIXTURE = [
+    {"event": "iter_start", "session_id": "e-1", "iter_name": "goal-e-iter-1",
+     "ts": "2026-08-10T10:00:00Z"},
+    {"event": "iter_config", "session_id": "e-1", "key": "CHAIN_OUTPUT_STYLES",
+     "value": "CHAIN_OUTPUT_STYLES=true", "ts": "2026-08-10T10:00:01Z"},
+    {"event": "review_verdict", "session_id": "e-1", "verdict": "", "attempt": 1,
+     "iter_name": "goal-e-iter-1", "ts": "2026-08-10T10:30:00Z"},
+    {"event": "iter_end", "session_id": "e-1", "iter_name": "goal-e-iter-1",
+     "verdict": "CONTINUE", "journey_deltas": {"regressed": 0},
+     "ts": "2026-08-10T11:00:00Z"},
+]
+
+
 def _self_test() -> int:
     with tempfile.TemporaryDirectory() as tmp:
         path = Path(tmp) / "telemetry.jsonl"
@@ -713,6 +850,53 @@ def _self_test() -> int:
         if tripped_q:
             print("FAIL: tripwire fired with no knob-active iterations", file=sys.stderr)
             return 1
+
+        # ── STYLE-1 cost dimension (D5: terse instructions → more turns) ─────
+        def _cost_report(name: str, tokens: int, turns: int,
+                         styled_iters: int = 3) -> dict[str, dict[str, Any]]:
+            cpath = Path(tmp) / name
+            cpath.write_text(
+                "\n".join(json.dumps(e) for e in
+                          _cost_fixture("c-1", tokens, turns, styled_iters)) + "\n",
+                encoding="utf-8")
+            return build_wall_report([str(cpath)])
+
+        creport = _cost_report("cost-trip.jsonl", 1800, 21)
+        if creport["c-1"]["usage_rows"][0]["output_tokens"] != 1000:
+            print("FAIL: usage_rows not collected by build_wall_report", file=sys.stderr)
+            return 1
+        ctripped, creasons = evaluate_cost_tripwire(creport, window=3)
+        if not ctripped:
+            print("FAIL: cost tripwire should TRIP on 1000→1800 tokens / 10→21 turns",
+                  file=sys.stderr)
+            return 1
+        if not any(r.startswith("cost: developer") for r in creasons):
+            print(f"FAIL: cost tripwire reasons: {creasons}", file=sys.stderr)
+            return 1
+        # The quality dimension must stay silent on this fixture — otherwise the
+        # cost assertions above would pass for the wrong reason.
+        if evaluate_tripwire(creport, window=3)[0]:
+            print("FAIL: quality tripwire fired on the clean cost fixture", file=sys.stderr)
+            return 1
+        if evaluate_cost_tripwire(_cost_report("cost-cheap.jsonl", 600, 8), window=3)[0]:
+            print("FAIL: cost tripwire fired when the styled arm got CHEAPER",
+                  file=sys.stderr)
+            return 1
+        if evaluate_cost_tripwire(_cost_report("cost-thin.jsonl", 1800, 21, 2),
+                                  window=3)[0]:
+            print("FAIL: cost tripwire fired with only 2 styled rows (<3 a side)",
+                  file=sys.stderr)
+            return 1
+
+        # ── STYLE-1: an unparseable review verdict is a quality trip ─────────
+        epath = Path(tmp) / "empty-verdict.jsonl"
+        epath.write_text(
+            "\n".join(json.dumps(e) for e in _EMPTY_VERDICT_FIXTURE) + "\n",
+            encoding="utf-8")
+        etripped, ereasons = evaluate_tripwire(build_wall_report([str(epath)]), window=3)
+        if not etripped or not any("unparseable review verdict" in r for r in ereasons):
+            print(f"FAIL: empty review verdict should TRIP: {ereasons}", file=sys.stderr)
+            return 1
     print("self-test passed")
     return 0
 
@@ -768,7 +952,7 @@ def main() -> int:
         "--tripwire",
         action="store_true",
         help=(
-            "evaluate the speed-experiment quality tripwire over the last "
+            "evaluate the experiment tripwire (quality + cost) over the last "
             "--window knob-active iterations; exit 3 when tripped"
         ),
     )
@@ -794,12 +978,14 @@ def main() -> int:
         report = build_wall_report(args.paths)
         if args.tripwire:
             tripped, reasons = evaluate_tripwire(report, window=args.window)
-            if tripped:
+            cost_tripped, cost_reasons = evaluate_cost_tripwire(
+                report, window=args.window)
+            if tripped or cost_tripped:
                 print("TRIPWIRE: TRIP")
-                for r in reasons:
+                for r in reasons + cost_reasons:
                     print(f"  - {r}")
                 return 3
-            print("TRIPWIRE: OK (no quality movement in the window)")
+            print("TRIPWIRE: OK (no quality or cost movement in the window)")
             return 0
         if args.json:
             print(render_wall_json(report, iter_filter=args.iter))
diff --git a/incredible_auto_dev/scripts/automation/lib/artifact_schemas.py b/incredible_auto_dev/scripts/automation/lib/artifact_schemas.py
index c0535f50..1ce4f8ab 100644
--- a/incredible_auto_dev/scripts/automation/lib/artifact_schemas.py
+++ b/incredible_auto_dev/scripts/automation/lib/artifact_schemas.py
@@ -56,15 +56,15 @@ SCHEMAS: tuple[ArtifactSchema, ...] = (
         artifact_type="review",
         path_pattern=re.compile(r"reports/reviews/.+-review\.md$"),
         verdict_enum=Verdict,
-        required_h2=("Verdict",),
-        description="Reviewer report — reports/reviews/<phase>-review.md",
+        required_h2=(),
+        description="Reviewer report — reports/reviews/<phase>-review.md (bold `**Verdict:**` line contract, no required H2)",
     ),
     ArtifactSchema(
         artifact_type="qa",
         path_pattern=re.compile(r"reports/qa/.+-qa\.md$"),
         verdict_enum=Verdict,
-        required_h2=("Verdict",),
-        description="QA validation report — reports/qa/<phase>-qa.md",
+        required_h2=(),
+        description="QA validation report — reports/qa/<phase>-qa.md (bold `**Verdict:**` line contract, no required H2)",
     ),
     ArtifactSchema(
         artifact_type="audit",
@@ -267,7 +267,12 @@ def _cmd_list(_argv: list[str]) -> int:
 _FIXTURES = {
     "review_pass": (
         "reports/reviews/phase-1-review.md",
-        "# Code Review Report\n\n## Verdict\n\n**Verdict:** PASS\n\n## Findings\n\nNone.\n",
+        "**Verdict:** PASS\n\n```yaml\nphase: phase-1\ndate: 2026-08-21\nreviewer: reviewer\nsummary: |\n  Implements the spec.\n```\n",
+        True,
+    ),
+    "review_pass_with_notes_lean": (
+        "reports/reviews/goal-demo-iter-1-review.md",
+        "**Verdict:** PASS_WITH_NOTES\n\n```yaml\nphase: goal-demo-iter-1\n```\n",
         True,
     ),
     "review_missing_verdict": (
@@ -277,7 +282,22 @@ _FIXTURES = {
     ),
     "review_invalid_verdict": (
         "reports/reviews/phase-1-review.md",
-        "# Code Review Report\n\n## Verdict\n\n**Verdict:** GOOD\n",
+        "**Verdict:** GOOD\n",
+        False,
+    ),
+    "review_h2_only_is_not_a_verdict": (
+        "reports/reviews/phase-1-review.md",
+        "# Code Review Report\n\n## Verdict\n\nPASS\n",
+        False,  # the H2 alone never satisfied the consumers (the bold line is the contract)
+    ),
+    "qa_pass": (
+        "reports/qa/phase-1-qa.md",
+        "**Verdict:** PASS\n\n## QA Validation Report\n\n| Test | Result |\n|---|---|\n| UT-01 | PASS |\n",
+        True,
+    ),
+    "qa_missing_verdict": (
+        "reports/qa/phase-1-qa.md",
+        "## QA Validation Report\n\nAll good.\n",
         False,
     ),
     "audit_missing_h2": (
diff --git a/incredible_auto_dev/scripts/automation/lib/claude_stream_renderer.py b/incredible_auto_dev/scripts/automation/lib/claude_stream_renderer.py
index c9cece61..54052bad 100644
--- a/incredible_auto_dev/scripts/automation/lib/claude_stream_renderer.py
+++ b/incredible_auto_dev/scripts/automation/lib/claude_stream_renderer.py
@@ -50,6 +50,15 @@ _AT_LINE_START = True
 # sidecar — telemetry and traces need per-model attribution.
 _SESSION_MODEL = ""
 
+# Output style observed in the system/init event (STYLE-1). This is the
+# EFFECTIVE style the CLI applied ("default" when none) — Claude Code ignores an
+# unknown `--settings '{"outputStyle":...}'` name SILENTLY, so the init event is
+# the only ground truth that the requested experiment arm actually ran. Stamped
+# into the usage sidecar, from where it rides into trace.jsonl and telemetry.
+_SESSION_OUTPUT_STYLE = ""
+# Comma-joined available_output_styles from init (absent on some CLI versions).
+_SESSION_STYLES_AVAILABLE = ""
+
 
 def _flush_dots() -> None:
     """Write a newline if we have unflushed progress dots, then reset."""
@@ -116,14 +125,23 @@ def _handle_event(event: dict[str, Any]) -> None:
         # Initial session info — usually one-line
         sub = event.get("subtype", "")
         if sub == "init":
-            global _SESSION_MODEL
+            global _SESSION_MODEL, _SESSION_OUTPUT_STYLE, _SESSION_STYLES_AVAILABLE
             model = event.get("model") or ""
             if model:
                 _SESSION_MODEL = model
+            style = event.get("output_style") or ""
+            if isinstance(style, dict):
+                style = style.get("name") or ""
+            if isinstance(style, str) and style:
+                _SESSION_OUTPUT_STYLE = style
+            available = event.get("available_output_styles") or []
+            if isinstance(available, (list, tuple)):
+                _SESSION_STYLES_AVAILABLE = ",".join(str(s) for s in available)
             sid = event.get("session_id") or ""
             if sid:
+                suffix = f" output_style={_SESSION_OUTPUT_STYLE}" if _SESSION_OUTPUT_STYLE else ""
                 sys.stderr.write(
-                    f"[claude] session={sid[:8]}... model={model}\n"
+                    f"[claude] session={sid[:8]}... model={model}{suffix}\n"
                 )
         return
 
@@ -168,6 +186,8 @@ def _write_sidecar(result_event: dict[str, Any]) -> None:
         "is_error": result_event.get("is_error", False),
         "subtype": result_event.get("subtype"),
         "model": result_event.get("model") or _SESSION_MODEL or None,
+        "output_style": _SESSION_OUTPUT_STYLE or None,
+        "available_output_styles": _SESSION_STYLES_AVAILABLE or None,
         "usage": result_event.get("usage", {}) or {},
     }
     try:
diff --git a/incredible_auto_dev/scripts/automation/lib/closure_gate.py b/incredible_auto_dev/scripts/automation/lib/closure_gate.py
index c8983f14..cd8dd48d 100644
--- a/incredible_auto_dev/scripts/automation/lib/closure_gate.py
+++ b/incredible_auto_dev/scripts/automation/lib/closure_gate.py
@@ -40,6 +40,7 @@ from __future__ import annotations
 
 import datetime
 import json
+import os
 import re
 import subprocess
 import sys
@@ -62,9 +63,24 @@ UI_ARTIFACTS = [
 ]
 
 # Objective placeholder markers (skill "Vagueness Detection" + SPEED-17 list).
-_PLACEHOLDER_RE = re.compile(
-    r"\bTODO\b|\bTBD\b|<fill|\bFILL IN\b|\blorem\b|\bxxx+\b", re.IGNORECASE
+# Marker TOKENS are case-sensitive: `TODO`/`FIXME`/`TBD`/`FILL IN` are how a
+# writer flags unfinished work; "todo"/"Todo" in prose is product vocabulary
+# (a todo app tripped the gate on every artifact — G8 stage 1, 2026-08-21).
+# The free-text placeholders stay case-insensitive.
+_PLACEHOLDER_RE_TOKENS = re.compile(r"\bTODO\b|\bFIXME\b|\bTBD\b|\bFILL IN\b")
+_PLACEHOLDER_RE_TEXT = re.compile(r"<fill|\blorem\b|\bxxx+\b", re.IGNORECASE)
+
+# Maintenance isolation, as the engine declares it. Same shape as the bash
+# marker regex (goal_maintenance_isolation_required, lib/common.sh): optional
+# list dash, optional bold, tolerant of `- **Maintenance isolation:** required`.
+_ISOLATION_MARKER_RE = re.compile(
+    r"^[ \t]*-?[ \t]*(?:\*\*)?maintenance[ -]isolation:?(?:\*\*)?[ \t]*:?[ \t]*(?:\*\*)?required",
+    re.IGNORECASE | re.MULTILINE,
 )
+# Deliberately the SAME literal set the bash predicate accepts — not a
+# case-insensitive superset. A value bash reads as "not isolated" (e.g. "True")
+# must not make this gate the more lenient of the two.
+_ISOLATION_ENV_TRUTHY = frozenset({"true", "TRUE", "1", "yes", "on", "required"})
 
 # Code spans are quoted evidence, not authored prose — a marker inside one is
 # something a tool said, not a placeholder the author left behind (owner
@@ -137,8 +153,32 @@ def content_lines(text: str) -> int:
     return n
 
 
+def maintenance_isolation_active(plan_text: str = "") -> bool:
+    """True when this phase/iteration declared maintenance isolation.
+
+    Read the two ways the feature propagates: the environment variable
+    run-goal.sh / run-phase.sh export once the spec is resolved
+    (apply_maintenance_isolation_from_spec), and the marker line itself for a
+    consumer that never inherited that environment — a hand re-run of closure,
+    say. The spec regex is NOT re-implemented against the spec file: this reads
+    the plan text the gate already has.
+    """
+    if os.environ.get("CHAIN_MAINTENANCE_ISOLATION", "") in _ISOLATION_ENV_TRUTHY:
+        return True
+    return bool(plan_text) and bool(_ISOLATION_MARKER_RE.search(plan_text))
+
+
 def frontend_present(plan_text: str) -> bool:
-    """Mirror of detect_frontend_in_plan (lib/common.sh)."""
+    """Mirror of detect_frontend_in_plan (lib/common.sh), including the
+    maintenance-isolation carve-out: isolation withholds browser execution, so
+    every UI artifact is legitimately an N/A stub and the frontend branch must
+    not demand real content for a lane the contract forbade. The bash function's
+    OTHER branch — the CHAIN_GOAL_TARGET_JOURNEYS override — is deliberately not
+    mirrored: it only ever ADDS the browser lane, and this gate reads artifacts
+    that the lane either produced or did not.
+    """
+    if maintenance_isolation_active(plan_text):
+        return False
     if re.search(r"frontend present:\s*yes", plan_text, re.IGNORECASE):
         return True
     return bool(re.search(r"frontend present\s*\n\s*yes", plan_text, re.IGNORECASE))
@@ -209,8 +249,9 @@ def placeholder_hits(text: str) -> list[str]:
         # character inside a code span cannot open a stray quoted span.
         scanned = _INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)
         scanned = _QUOTED_SPAN_RE.sub(lambda m: " " * len(m.group(0)), scanned)
-        for m in _PLACEHOLDER_RE.finditer(scanned):
-            hits.append(f"{m.group(0)} (line {i})")
+        for rx in (_PLACEHOLDER_RE_TOKENS, _PLACEHOLDER_RE_TEXT):
+            for m in rx.finditer(scanned):
+                hits.append(f"{m.group(0)} (line {i})")
     return hits
 
 
@@ -696,6 +737,24 @@ def _self_test() -> int:
         assert frontend_present("Frontend Present: yes")
         assert frontend_present("## Frontend Present\nyes")
         assert not frontend_present("Frontend Present: no")
+        # maintenance isolation carve-out (env + plan marker), and its default OFF
+        assert not maintenance_isolation_active("Frontend Present: yes")
+        assert maintenance_isolation_active("- **Maintenance isolation:** required")
+        assert maintenance_isolation_active("Maintenance-isolation: REQUIRED")
+        assert not frontend_present(
+            "Frontend Present: yes\n- **Maintenance isolation:** required\n"
+        )
+        _prev_env = os.environ.get("CHAIN_MAINTENANCE_ISOLATION")
+        try:
+            os.environ["CHAIN_MAINTENANCE_ISOLATION"] = "true"
+            assert not frontend_present("Frontend Present: yes")
+            os.environ["CHAIN_MAINTENANCE_ISOLATION"] = "False"
+            assert frontend_present("Frontend Present: yes")  # not a bash-truthy value
+        finally:
+            if _prev_env is None:
+                os.environ.pop("CHAIN_MAINTENANCE_ISOLATION", None)
+            else:
+                os.environ["CHAIN_MAINTENANCE_ISOLATION"] = _prev_env
         assert content_lines("# h\n\n---\n<!-- c -->\nreal\nreal2\n") == 2
         assert len(numbered_steps("1. a\n2) b\nx\n 3. c\n")) == 3
         assert classify_step("1. Test the form") == "blocking"
@@ -704,7 +763,17 @@ def _self_test() -> int:
         assert classify_step('4. Fill "Name" with "demo" — Expect: row appears') == "ok"
         assert classify_step("5. Verify the total updates correctly to $45") == "warn"
         assert placeholder_hits("real\nTODO: later\n") != []
+        assert placeholder_hits("real\nFIXME: wire up\n") != []
+        assert placeholder_hits("real\nTBD\n") != []
+        assert placeholder_hits("real\n<fill in the route>\n") != []
+        assert placeholder_hits("real\nLorem ipsum dolor\n") != []
         assert placeholder_hits("<!-- TBD template note -->\nreal\n") == []
+        # Product vocabulary is not a marker (G8 stage 1: a todo app tripped the gate).
+        assert placeholder_hits("Add a todo via the form\n") == []
+        assert placeholder_hits("state is stored in todo.json\n") == []
+        assert placeholder_hits("the heading 'Todo' is visible\n") == []
+        assert placeholder_hits("shows the todos list\n") == []
+        assert placeholder_hits("Fixme is a band name\n") == []
 
     def t_skip_detection():
         skipped = ("**Browser QA Verdict:** SKIPPED\n"
```
