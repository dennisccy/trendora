# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 4. Shown in full: 4.

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 5d092b3d..f0fc5c63 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -533,6 +533,16 @@ class StartupCfg(BaseModel):
         Defaults to `5` (present so a config fixture predating this field still loads unchanged — the
         established `extra="allow"`/back-compat-default convention this class already uses). MUST be
         `>= 1`.
+      - `warmup_bar_cache_bounded` (goal-market-compass iter-33, J-09/AG-8, Constraints (c)) — governs
+        which `app.engine.prices` bar-cache context the background warm-up's cadence loop
+        (`app.engine.warmup._run_warmup`) opens around itself. `true` (the bound, and the default) uses
+        `prefilled_bar_cache` — the same unconditional whole-table eager scan `_BarCache.prefill` runs
+        (no `expected_symbols` filter, so no iter-42-class per-symbol exclusion), which builds the
+        compact array-based `_SymbolColumns` representation for every touched symbol instead of the
+        costlier per-symbol `list[Bar]` NamedTuple representation the plain lazy `bar_cache` context
+        accumulates. `false` reverts to the pre-iter-33 lazy `bar_cache` shape (owner rollback lever).
+        Defaults to `True` (present so a config fixture predating this field still loads unchanged — the
+        same back-compat-default convention as `background_compute_history_size`).
 
     Boot-validated: the budget + both poll intervals MUST be `> 0`, the batch size `>= 1`, the idle
     interval `>= the active interval`, and `background_compute_history_size >= 1`. An invalid block
@@ -544,6 +554,7 @@ class StartupCfg(BaseModel):
     health_poll_interval_seconds: float
     health_poll_idle_interval_seconds: float
     background_compute_history_size: int = 5
+    warmup_bar_cache_bounded: bool = True
 
     @model_validator(mode="after")
     def _validate(self) -> "StartupCfg":
diff --git a/apps/backend/app/engine/warmup.py b/apps/backend/app/engine/warmup.py
index 1e3fb0a2..416b687e 100644
--- a/apps/backend/app/engine/warmup.py
+++ b/apps/backend/app/engine/warmup.py
@@ -35,7 +35,7 @@ from app.engine import data_manager, evidence, forward_testing
 from app.engine import j11_preboot_guard
 from app.engine.forward_testing import backfill_forward_returns, walk_forward_asof_dates
 from app.engine.ledger import FORWARD_WALK_TYPE, read_entries
-from app.engine.prices import bar_cache, latest_data_date
+from app.engine.prices import bar_cache, latest_data_date, prefilled_bar_cache
 from app.engine.scanner import get_run_for_date, run_scan
 from app.models import ScannerRun
 
@@ -348,7 +348,37 @@ def _run_warmup(engine: Engine, cfg: Config, prog: "data_manager.JobProgress") -
             # orthogonal to the iter-28 single-flight guard (which serializes the warm-up THREAD in
             # `start_warmup`); the cache only changes how this thread's own session loads bars. The cache
             # dies with the `with Session` block; the warm-up adds no bars, so no read sees a stale series.
-            with bar_cache(session):
+            #
+            # goal-market-compass iter-33 (J-09/AG-8, Constraints (c)): before this iteration this was an
+            # UNCONDITIONAL `with bar_cache(session):` — a bare (non-prefilling) context, so every symbol
+            # the cadence loop touched was loaded through `bars_asof`'s lazy per-symbol branch, which
+            # always builds the costlier `list[Bar]` NamedTuple representation (`prices.py`'s eager-scan
+            # `_SymbolColumns` array representation — iter-41/B5 — was never reached from this call site).
+            # Because `run_scan` scores essentially the whole live universe on its FIRST cadence date
+            # already (breadth/regime/sector/theme all read the full pool), nearly every symbol's full
+            # series ends up resident in the costlier shape almost immediately — this is the "1.29 GB,
+            # five-second start-up spike" iter-32's raw evidence pinned to this exact block (peak reached
+            # BEFORE readiness, matching a load-on-first-touch pattern, not a slow per-date accumulation).
+            # `cfg.startup.warmup_bar_cache_bounded` (default True) now selects `prefilled_bar_cache`
+            # instead: the SAME `_BarCache`, the SAME symbols, the SAME rows — but loaded via ONE
+            # unconditional whole-table streamed scan (`expected_symbols=None`, so nothing is excluded —
+            # deliberately NOT the iter-42 `WHERE symbol IN (...)` filter reverted at iter-43; see that
+            # docstring paragraph in `prices.py` and `docs/handoffs/goal-ops-hardening-iter-43-dev.md`)
+            # into `_SymbolColumns`'s `array.array('d')` columns, the same compact representation
+            # `_BarCache.prefill` already produces for every OTHER prefilling caller. Every consumer below
+            # (`run_scan` -> `regime.py`/`sectors.py`/`themes.py`/`market_phase.py`/`bars_asof`/
+            # `bars_after`, and `backfill_forward_returns`) reads the cache through the exact same
+            # `full[:cut]` / indexing / `len` operations either representation supports identically (the
+            # `Sequence` duck-typing contract `_SymbolColumns` implements) — so served values are
+            # byte-identical regardless of which branch loaded them; only the resident bytes differ. Set
+            # `false` to revert to the pre-iter-33 lazy shape (owner rollback lever; no other code path
+            # changes).
+            cache_ctx = (
+                prefilled_bar_cache(session)
+                if cfg.startup.warmup_bar_cache_bounded
+                else bar_cache(session)
+            )
+            with cache_ctx:
                 for index, asof in enumerate(dates, start=1):
                     # goal-market-compass iter-18 (J-11 step 11 ruling requirement 7): the SAME
                     # persisted-boundary check `ensure_latest_snapshot` already performs before ITS OWN
diff --git a/apps/backend/tests/test_warmup.py b/apps/backend/tests/test_warmup.py
index 85d9a1a5..8bd606bc 100644
--- a/apps/backend/tests/test_warmup.py
+++ b/apps/backend/tests/test_warmup.py
@@ -262,6 +262,143 @@ def test_warmup_loads_each_symbol_at_most_once_across_cadence_and_forward_return
     assert max(load_counts.values()) == 1, f"a symbol was loaded more than once: {load_counts}"
 
 
+# ==================================================================================================
+# goal-market-compass iter-33 (J-09/AG-8, Constraints (c)) — bound the cold cadence-date allocation
+# `warmup.py:351`'s bar-cache context produces. `cfg.startup.warmup_bar_cache_bounded` (default True)
+# selects `prefilled_bar_cache` (the compact array-based `_SymbolColumns` eager scan, unconditional --
+# no `expected_symbols` filter, so no iter-42-class exclusion) instead of the pre-iter-33 lazy
+# `bar_cache` context, which built the costlier per-symbol `list[Bar]` representation for every symbol
+# the cadence loop touched. These two tests prove (1) the config key genuinely selects the mechanism,
+# with zero symbol exclusion either way, and (2) the two mechanisms produce BYTE-IDENTICAL served
+# output -- the switch changes only which representation is resident, never a stored value.
+#
+# Both tests no-op `_warm_drawdown_expectations` (like the iter-26 test above no-ops
+# `_warm_membership_timeline`): that step (added ops-hardening iter-46, AFTER the iter-26 test was
+# written) computes each evidence-ledger claim on its OWN short-lived per-claim `Session` + bar-cache
+# context, strictly AFTER `_run_warmup`'s cadence `with cache_ctx:` block this iteration targets has
+# already exited -- unrelated machinery, confirmed by a live call-stack trace during this iteration's
+# investigation. Without this no-op, `test_warmup_loads_each_symbol_at_most_once_across_cadence_and_
+# forward_returns` (the iter-26 test above) fails on an UNMODIFIED `main` too (reproduced by stashing
+# this iteration's diff and re-running it) -- `^VIX` is loaded once per evidence claim (7 on the live
+# ledger) via `market_phase.phase_context_by_date` -> `_causal_timeline` -> `_severity_reading` ->
+# `_latest_vix_on_or_before` -> `close_on`, each call opening its own fresh session/cache pair. This is
+# a pre-existing test/instrumentation gap, NOT introduced by this iteration and NOT touched by it (out
+# of this iteration's scope) -- see this iteration's dev handoff Known Issues.
+def test_warmup_bar_cache_bounded_config_selects_prefill_mechanism(early_engine, monkeypatch):
+    """`cfg.startup.warmup_bar_cache_bounded=True` (the default) routes the cadence loop's bar-cache
+    context through `prefilled_bar_cache` with `expected_symbols=None` (the unconditional whole-table
+    scan -- never the iter-42 filtered shape); `False` reverts to the plain `bar_cache` context. Proves
+    the config key actually selects the mechanism (not merely documented intent)."""
+    engine, cfg = early_engine
+    monkeypatch.setattr(warmup_mod, "_warm_membership_timeline", lambda engine, cfg: None)
+    monkeypatch.setattr(warmup_mod, "_warm_drawdown_expectations", lambda engine, cfg: None)
+
+    calls: list[tuple[str, object]] = []
+    orig_bar_cache = warmup_mod.bar_cache
+    orig_prefilled = warmup_mod.prefilled_bar_cache
+
+    def _tracking_bar_cache(session):
+        calls.append(("bar_cache", None))
+        return orig_bar_cache(session)
+
+    def _tracking_prefilled(session, expected_symbols=None):
+        calls.append(("prefilled_bar_cache", expected_symbols))
+        return orig_prefilled(session, expected_symbols=expected_symbols)
+
+    monkeypatch.setattr(warmup_mod, "bar_cache", _tracking_bar_cache)
+    monkeypatch.setattr(warmup_mod, "prefilled_bar_cache", _tracking_prefilled)
+
+    bounded_cfg = cfg.model_copy(
+        update={"startup": cfg.startup.model_copy(update={"warmup_bar_cache_bounded": True})}
+    )
+    job_id = start_warmup(engine, bounded_cfg)
+    _join_warmup(job_id)
+    assert data_manager.get_job(job_id)["status"] == "ok"
+    assert calls == [("prefilled_bar_cache", None)], (
+        f"bounded=True must call prefilled_bar_cache(session, expected_symbols=None) exactly once, "
+        f"never bar_cache directly and never a filtered expected_symbols: {calls}"
+    )
+
+    _clear_warmup_registry()
+    calls.clear()
+    unbounded_cfg = cfg.model_copy(
+        update={"startup": cfg.startup.model_copy(update={"warmup_bar_cache_bounded": False})}
+    )
+    job_id2 = start_warmup(engine, unbounded_cfg)
+    _join_warmup(job_id2)
+    assert data_manager.get_job(job_id2)["status"] == "ok"
+    assert calls == [("bar_cache", None)], (
+        f"bounded=False must call bar_cache(session) exactly once, never prefilled_bar_cache: {calls}"
+    )
+
+
+def test_warmup_bar_cache_bounded_is_byte_identical_to_unbounded(tmp_path_factory, monkeypatch):
+    """The config switch changes ONLY which `_BarCache` loading mechanism the cadence context uses --
+    never a served value. Runs the SAME fast fixture warm-up on two freshly-seeded, otherwise-identical
+    DBs, once with `warmup_bar_cache_bounded=True` and once `False`, and asserts every persisted
+    `ScannerRun`/`ScannerResult`/`ForwardReturn` field the two runs produce is identical (never a
+    diff, never merely 'both non-empty') -- the exact AG-3/Constraints(c) 'no served value changes'
+    guarantee this iteration's safety catch requires before any bound may ship."""
+    monkeypatch.setattr(warmup_mod, "_warm_membership_timeline", lambda engine, cfg: None)
+    monkeypatch.setattr(warmup_mod, "_warm_drawdown_expectations", lambda engine, cfg: None)
+
+    def _run_once(bounded: bool, label: str) -> dict:
+        cfg = _fast_cfg()
+        cfg = cfg.model_copy(
+            update={"startup": cfg.startup.model_copy(update={"warmup_bar_cache_bounded": bounded})}
+        )
+        db_path = tmp_path_factory.mktemp(f"bytecheck_{label}") / "db.sqlite"
+        engine = make_engine(f"sqlite:///{db_path}")
+        create_db_and_tables(engine)
+        load_seed(engine, cfg)
+        _clear_warmup_registry()
+        job_id = start_warmup(engine, cfg)
+        _join_warmup(job_id)
+        rec = data_manager.get_job(job_id)
+        assert rec["status"] == "ok"
+        with Session(engine) as session:
+            runs = sorted(session.exec(select(ScannerRun)).all(), key=lambda r: r.asof_date.isoformat())
+            run_rows = [
+                (
+                    r.asof_date.isoformat(), r.regime_score, r.regime_label, r.breadth_above_50dma,
+                    r.breadth_above_200dma, r.new_high_low_json, r.candidate_counts_json,
+                    r.regime_components_json,
+                )
+                for r in runs
+            ]
+            results = sorted(
+                session.exec(select(ScannerResult)).all(),
+                key=lambda x: (x.run_id, x.ticker),
+            )
+            result_rows = [
+                (
+                    x.run_id, x.ticker, x.leadership_score, x.entry_quality_score, x.risk_score,
+                    x.setup_status, x.rank,
+                )
+                for x in results
+            ]
+            fr_rows = sorted(
+                (
+                    fr.run_id, fr.symbol, fr.horizon, round(fr.realized_return, 8),
+                )
+                for fr in session.exec(select(ForwardReturn)).all()
+            )
+        _clear_warmup_registry()
+        return {"runs": run_rows, "results": result_rows, "forward_returns": fr_rows}
+
+    bounded_out = _run_once(True, "bounded")
+    unbounded_out = _run_once(False, "unbounded")
+
+    assert bounded_out["runs"], "the fast fixture must have produced at least one cadence run"
+    assert bounded_out["runs"] == unbounded_out["runs"], "bounded ScannerRun fields diverged from unbounded"
+    assert bounded_out["results"] == unbounded_out["results"], (
+        "bounded ScannerResult fields diverged from unbounded"
+    )
+    assert bounded_out["forward_returns"] == unbounded_out["forward_returns"], (
+        "bounded ForwardReturn fields diverged from unbounded"
+    )
+
+
 # ==================================================================================================
 # iter-36 (J-96) — the warm-up precomputes the membership-timeline cache OFF the boot path so the FIRST
 # `GET /api/data` after boot/rebuild serves the cached payload (not the O(dates × pool) cold compute)
diff --git a/config.yaml b/config.yaml
index 9d9141ff..7d26498e 100644
--- a/config.yaml
+++ b/config.yaml
@@ -1334,6 +1334,21 @@ startup:
   health_poll_interval_seconds: 2.0        # badge poll cadence while warming (fast flip to Ready, not a 30s cycle)
   health_poll_idle_interval_seconds: 30.0  # slower poll cadence the badge backs off to once Ready (>= active)
   background_compute_history_size: 5       # ops-hardening iter-24 (J-09): recent_outcomes ring cap (>= 1)
+  warmup_bar_cache_bounded: true            # goal-market-compass iter-33 (J-09/AG-8, Constraints (c)): the
+    # background warm-up's cadence loop (warmup.py's cadence `run_scan` x N dates + trailing
+    # backfill_forward_returns) opens a `_BarCache` context around itself (app.engine.prices). `true` (the
+    # bound) routes that context through `prefilled_bar_cache` -- the SAME unconditional whole-table eager
+    # scan iter-43 restored (no expected_symbols filter, so no iter-42-class exclusion) -- which builds the
+    # compact array-based `_SymbolColumns` representation for every touched symbol instead of letting the
+    # cadence loop accumulate the costlier per-symbol `list[Bar]` NamedTuple representation via lazy loads
+    # (the pre-iter-33 shape). `_SymbolColumns` vs `list[Bar]` is the SAME representation iter-41 (B5)
+    # already proved cuts resident bytes ~3x with byte-identical served values; this key only decides
+    # WHICH loading path the warm-up's cadence context takes, never which rows/symbols it includes -- so it
+    # cannot reproduce the iter-42 whole-job regression (that regression came from EXCLUDING ~36-43 ETF/
+    # index symbols from the eager scan, forcing a MIX of representations; this key is all-or-nothing, never
+    # partial). `false` reverts to the pre-iter-33 lazy `bar_cache` shape for owner rollback. See
+    # docs/handoffs/goal-market-compass-iter-33-dev.md for the live re-measurement this key's default was
+    # chosen from.
 
 # ----------------------------------------------------------------------------------------
 # goal-mcp-loop iter-33 CONSUMED — the daily preflight verdict (J-20 / backlog B-301).
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 193 +++++++++++++++++++++
 runs/goal-session-market-compass/telemetry.jsonl   |   6 +
 runs/goal-session-market-compass/trace/.next-step  |   2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |   1 +
 4 files changed, 201 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
