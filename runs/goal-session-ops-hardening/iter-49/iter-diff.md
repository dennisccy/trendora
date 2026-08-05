# Iteration diff (bounded)

Files changed: 7. Shown in full: 6.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_start_backend_script.py` (1 lines not shown)

```diff
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 1f886850..0d120c9f 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -3978,22 +3978,37 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
                         # block exactly as before (no regression to that existing behavior). On MemoryError
                         # this loop stops immediately (no further horizons attempted) and forces memory back
                         # to the OS.
+                        # ops-hardening iter-49 (J-05/J-07 TC-2): per-horizon sub-phase timing, additive to
+                        # the whole-phase log line below (byte-for-byte unchanged) — so a slow run's cost is
+                        # attributable to a SPECIFIC horizon, not just "the loop as a whole" (iter-48's own
+                        # coarser instrumentation could name only the phase, and its 102s/153s/1,334s
+                        # variance across three live runs could not be attributed further). Logged in a
+                        # `finally` so it fires whether this horizon succeeds, MemoryErrors (still logged
+                        # before the `break` takes effect), or a non-memory exception propagates to the
+                        # outer `except Exception` below (no change to that existing control flow).
+                        _horizon_t0 = time.monotonic()
                         try:
-                            # iter-39 (audit B3 / J-07 step 4): test-only injection point — a no-op unless
-                            # this process was started with the env var naming this site. See
-                            # `_fault_inject_memory_error`.
-                            _fault_inject_memory_error("forward_aggregates")
-                            forward_testing.forward_aggregates_ingest_cached(
-                                session, h, cfg, as_of=latest_run_date
+                            try:
+                                # iter-39 (audit B3 / J-07 step 4): test-only injection point — a no-op
+                                # unless this process was started with the env var naming this site. See
+                                # `_fault_inject_memory_error`.
+                                _fault_inject_memory_error("forward_aggregates")
+                                forward_testing.forward_aggregates_ingest_cached(
+                                    session, h, cfg, as_of=latest_run_date
+                                )
+                                forward_aggregates_warmed = True
+                            except MemoryError as exc:
+                                _log_isolation_failure(
+                                    "ingest forward-aggregate warm aborted at horizon %s — memory pressure, "
+                                    "stopping remaining horizons in this loop: %s", h, exc,
+                                )
+                                _release_process_memory()
+                                break
+                        finally:
+                            logger.info(
+                                "J-05 finalize-tail sub-phase timing: job=%s phase=%s horizon=%s elapsed=%.2fs",
+                                prog.job_id, "forward_aggregates_warm", h, time.monotonic() - _horizon_t0,
                             )
-                            forward_aggregates_warmed = True
-                        except MemoryError as exc:
-                            _log_isolation_failure(
-                                "ingest forward-aggregate warm aborted at horizon %s — memory pressure, "
-                                "stopping remaining horizons in this loop: %s", h, exc,
-                            )
-                            _release_process_memory()
-                            break
                     if forward_aggregates_warmed:
                         refreshed.append("forward_aggregates")
             except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
@@ -4090,37 +4105,95 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
 
             _phase_t0 = time.monotonic()
             drawdown_warmed = False
-            for entry in ledger_entries:
+            # ops-hardening iter-49 (J-05, drawdown_expectations_warm bound): `phase_context_by_date`'s
+            # all-history causal timeline is invariant across every claim in this loop (`as_of=None`
+            # always, `cfg` unchanged mid-loop) — computed ONCE here and threaded through
+            # `compute_drawdown_expectations_cached`'s new `phases` parameter, instead of once per claim (7x
+            # on the live ledger). Own try/except: a NON-MEMORY failure here degrades to every claim
+            # self-computing its own timeline below (`phases=None` falls back to the SAME per-claim
+            # behavior `compute_drawdown_expectations` always had) — never a reason to abort the whole warm.
+            _dd_phases_memory_abort = False
+            try:
+                _dd_phases = market_phase.phase_context_by_date(session, as_of=None, config=cfg)
+            # ops-hardening iter-49 AUDIT (finding B3 fix): a `MemoryError` here STOPS this phase — it does
+            # NOT fall through to the per-claim loop. Falling through set `phases=None`, which makes every
+            # one of the ledger's claims self-compute its own all-history timeline: degrading under memory
+            # pressure into the MORE allocating path, i.e. exactly the "hammering the next claim's
+            # allocation under pressure" the iter-8 convention (see the per-claim handler below) exists to
+            # prevent. Now this handler matches that convention in full — stop, release memory back to the
+            # OS, and report honestly: `drawdown_warmed` stays False, so `drawdown_expectations` is omitted
+            # from `aggregates_refreshed` rather than claimed for work that never ran.
+            except MemoryError as exc:
+                _log_isolation_failure(
+                    "ingest drawdown-expectations phase-context warm aborted — memory pressure, stopping "
+                    "the drawdown-expectations warm without attempting any claim: %s", exc,
+                )
+                _release_process_memory()
+                _dd_phases = None
+                _dd_phases_memory_abort = True
+            except Exception as exc:  # noqa: BLE001 — non-fatal: fall back to per-claim self-compute
+                _log_isolation_failure(
+                    "ingest drawdown-expectations phase-context warm failed (non-fatal, falling back to "
+                    "per-claim self-compute): %s", exc,
+                )
+                _dd_phases = None
+            # `()` (never `ledger_entries`) after a memory-pressure abort above — the loop is skipped
+            # entirely, per the iter-8 stop convention. Every other outcome (success, or a non-memory
+            # precompute failure that degraded to `phases=None`) iterates the ledger exactly as before.
+            for entry in (() if _dd_phases_memory_abort else ledger_entries):
                 if not isinstance(entry, dict) or entry.get("type") == FORWARD_WALK_TYPE:
                     continue
                 claim = entry.get("claim") if isinstance(entry.get("claim"), dict) else {}
                 prog.tick()  # heartbeat stamp before each claim's warm call — see docstring above.
+                # ops-hardening iter-49 (J-05/J-07 TC-2): a stable, honest per-claim identity for the
+                # sub-phase timing log below — kind + the claim's own discriminating selector (factor /
+                # event-study subject / combination cohort) + horizon, NEVER a raw loop index (an index is
+                # not diagnostic across runs whose ledger order can change).
+                _claim_id = "{}:{}:h{}".format(
+                    claim.get("kind", "?"),
+                    claim.get("factor") or claim.get("subject") or claim.get("cohort")
+                    or claim.get("signal") or "?",
+                    claim.get("horizon", "?"),
+                )
+                _claim_t0 = time.monotonic()
                 try:
-                    # iter-39 (audit B3 / J-07 step 4): test-only injection point — see
-                    # `_fault_inject_memory_error` (a no-op unless this process names this site in the env).
-                    _fault_inject_memory_error("drawdown_expectations")
-                    result = forward_testing.compute_drawdown_expectations_cached(session, claim, cfg)
-                    # gate on an ACTUAL non-None payload (never just "the call didn't raise") — an
-                    # out-of-scope horizon or an unresolvable cohort returns None honestly and must NOT be
-                    # reported as refreshed (mirrors the `market_phase`/`research_hot_keys` "actually did
-                    # something" convention above).
-                    if result is not None:
-                        drawdown_warmed = True
-                # ops-hardening iter-8 (J-05 REGRESSION fix): distinct from the generic per-claim isolate-and-
-                # continue below — a `MemoryError` stops THIS loop immediately (no further claims attempted)
-                # and forces memory back to the OS, instead of hammering the next claim's allocation under
-                # pressure. `drawdown_warmed` already honestly reflects any claim that succeeded before the
-                # abort.
-                except MemoryError as exc:
-                    _log_isolation_failure(
-                        "ingest drawdown-expectations warm aborted — memory pressure, stopping remaining "
-                        "claims in this loop: %s", exc,
-                    )
-                    _release_process_memory()
-                    break
-                except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next claim
-                    _log_isolation_failure(
-                        "ingest drawdown-expectations warm failed for one claim (non-fatal): %s", exc
+                    try:
+                        # iter-39 (audit B3 / J-07 step 4): test-only injection point — see
+                        # `_fault_inject_memory_error` (a no-op unless this process names this site in the
+                        # env).
+                        _fault_inject_memory_error("drawdown_expectations")
+                        result = forward_testing.compute_drawdown_expectations_cached(
+                            session, claim, cfg, phases=_dd_phases,
+                        )
+                        # gate on an ACTUAL non-None payload (never just "the call didn't raise") — an
+                        # out-of-scope horizon or an unresolvable cohort returns None honestly and must NOT
+                        # be reported as refreshed (mirrors the `market_phase`/`research_hot_keys` "actually
+                        # did something" convention above).
+                        if result is not None:
+                            drawdown_warmed = True
+                    # ops-hardening iter-8 (J-05 REGRESSION fix): distinct from the generic per-claim
+                    # isolate-and-continue below — a `MemoryError` stops THIS loop immediately (no further
+                    # claims attempted) and forces memory back to the OS, instead of hammering the next
+                    # claim's allocation under pressure. `drawdown_warmed` already honestly reflects any
+                    # claim that succeeded before the abort.
+                    except MemoryError as exc:
+                        _log_isolation_failure(
+                            "ingest drawdown-expectations warm aborted — memory pressure, stopping "
+                            "remaining claims in this loop: %s", exc,
+                        )
+                        _release_process_memory()
+                        break
+                    except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next claim
+                        _log_isolation_failure(
+                            "ingest drawdown-expectations warm failed for one claim (non-fatal): %s", exc
+                        )
+                finally:
+                    # per-claim sub-phase timing (TC-2), additive to the whole-phase log line below (byte-
+                    # for-byte unchanged) — logged in a `finally` so it fires on success, MemoryError
+                    # (before the `break` takes effect), or any other isolated per-claim failure.
+                    logger.info(
+                        "J-05 finalize-tail sub-phase timing: job=%s phase=%s claim=%s elapsed=%.2fs",
+                        prog.job_id, "drawdown_expectations_warm", _claim_id, time.monotonic() - _claim_t0,
                     )
             if drawdown_warmed:
                 refreshed.append("drawdown_expectations")
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index 71332197..ffde386d 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -623,7 +623,18 @@ class _ExactMeanAcc:
         self._count = 0
 
     def add(self, value: float) -> None:
-        numerator, denominator = value.as_integer_ratio()
+        self.add_ratio(*value.as_integer_ratio())
+
+    # ops-hardening iter-49 (J-05/J-07): `add` split into "compute the ratio" + "fold it in" so a caller
+    # that already has `value.as_integer_ratio()` (this module's own `compute_forward_aggregates` hot
+    # loop, which used to call `.as_integer_ratio()` independently inside EVERY one of an observation's
+    # up-to-7 accumulator adds -- overall + 6 groups, all fed the SAME `realized`/`max_drawdown` float --
+    # profiled live at 24.58M redundant calls, ~17% of one horizon's wall time) can skip the recompute.
+    # `add(value)` above is now a thin wrapper calling this with a freshly computed ratio -- byte-identical
+    # for every existing caller/test, since `as_integer_ratio()` is a pure, deterministic IEEE-754
+    # decomposition: computing it once and reusing the SAME (numerator, denominator) pair across every
+    # accumulator is bit-for-bit identical to each accumulator recomputing it independently.
+    def add_ratio(self, numerator: int, denominator: int) -> None:
         self._partials[denominator] = self._partials.get(denominator, 0) + numerator
         self._count += 1
 
@@ -654,6 +665,14 @@ class _GroupAcc:
         if mdd_value is not None:
             self.mdds.add(mdd_value)
 
+    # ops-hardening iter-49 (J-05): ratio-based sibling of `add`, mirroring `_ExactMeanAcc.add_ratio` --
+    # see that method's docstring for why. `add(r, m)` is byte-identical to
+    # `add_ratio(r.as_integer_ratio(), m.as_integer_ratio() if m is not None else None)`.
+    def add_ratio(self, return_ratio: tuple[int, int], mdd_ratio: Optional[tuple[int, int]]) -> None:
+        self.returns.add_ratio(*return_ratio)
+        if mdd_ratio is not None:
+            self.mdds.add_ratio(*mdd_ratio)
+
 
 def _accumulate_group(accs: dict, value, return_value: float, mdd_value: Optional[float]) -> None:
     """`_group_means`'s own `if value is not None: buckets[value].append(...)` gate, applied to a
@@ -662,6 +681,17 @@ def _accumulate_group(accs: dict, value, return_value: float, mdd_value: Optiona
         accs[value].add(return_value, mdd_value)
 
 
+# ops-hardening iter-49 (J-05): ratio-based sibling of `_accumulate_group`, taking a pre-computed
+# `(numerator, denominator)` pair instead of a raw float -- see `_ExactMeanAcc.add_ratio`'s docstring.
+# `_accumulate_group(accs, value, r, m)` is byte-identical to
+# `_accumulate_group_ratio(accs, value, r.as_integer_ratio(), m.as_integer_ratio() if m is not None else None)`.
+def _accumulate_group_ratio(
+    accs: dict, value, return_ratio: tuple[int, int], mdd_ratio: Optional[tuple[int, int]],
+) -> None:
+    if value is not None:
+        accs[value].add_ratio(return_ratio, mdd_ratio)
+
+
 def _group_means_from_accs(accs: dict, label_key: str, order, pad: bool) -> list[dict]:
     """`_group_means`'s exact row/order/pad contract (same ordering: `order` first -- padded to n=0/mean
     None when `pad` and a value is missing -- then any extra observed values in sorted order), sourced
@@ -1267,15 +1297,24 @@ def compute_forward_aggregates(
                 "is_pullback_to_rising_dma": is_pullback_to_rising_dma,
                 "is_flat_base_breakout": is_flat_base_breakout,
             }
-            overall_returns.add(realized)
-            if max_drawdown is not None:
-                overall_mdds.add(max_drawdown)
-            _accumulate_group(bucket_accs, obs["bucket"], realized, max_drawdown)
-            _accumulate_group(setup_accs, obs["setup"], realized, max_drawdown)
-            _accumulate_group(regime_accs, obs["regime"], realized, max_drawdown)
-            _accumulate_group(vcp_accs, obs["is_vcp"], realized, max_drawdown)
-            _accumulate_group(pullback_accs, obs["is_pullback_to_rising_dma"], realized, max_drawdown)
-            _accumulate_group(flat_base_accs, obs["is_flat_base_breakout"], realized, max_drawdown)
+            # ops-hardening iter-49 (J-05, forward_aggregates_warm bound): `realized`/`max_drawdown` are the
+            # SAME two float values fed to every one of this observation's up-to-7 accumulator adds below
+            # (overall + 6 groups) -- `.as_integer_ratio()` computed ONCE here and reused, instead of each
+            # accumulator's own `add()` recomputing the IDENTICAL ratio independently (profiled live:
+            # 24.58M redundant calls at horizon=20 on the live committed DB, ~17% of that one horizon's
+            # wall time). Byte-identical output (see `_ExactMeanAcc.add_ratio`'s docstring) -- changes only
+            # how many times an already-deterministic pure function runs, never what is computed.
+            _return_ratio = realized.as_integer_ratio()
+            _mdd_ratio = max_drawdown.as_integer_ratio() if max_drawdown is not None else None
+            overall_returns.add_ratio(*_return_ratio)
+            if _mdd_ratio is not None:
+                overall_mdds.add_ratio(*_mdd_ratio)
+            _accumulate_group_ratio(bucket_accs, obs["bucket"], _return_ratio, _mdd_ratio)
+            _accumulate_group_ratio(setup_accs, obs["setup"], _return_ratio, _mdd_ratio)
+            _accumulate_group_ratio(regime_accs, obs["regime"], _return_ratio, _mdd_ratio)
+            _accumulate_group_ratio(vcp_accs, obs["is_vcp"], _return_ratio, _mdd_ratio)
+            _accumulate_group_ratio(pullback_accs, obs["is_pullback_to_rising_dma"], _return_ratio, _mdd_ratio)
+            _accumulate_group_ratio(flat_base_accs, obs["is_flat_base_breakout"], _return_ratio, _mdd_ratio)
             attribution_acc.add(obs)
             chunk_obs_by_run[res_run_id].append(obs)
 
@@ -1498,6 +1537,17 @@ def forward_aggregates_ingest_cached(
         # the bounded wait without persisting — fall through and compute independently rather than
         # blocking indefinitely. Still byte-identical (the SAME sole producer); at worst this is one
         # redundant compute in a rare failure/timeout case, never a hang and never a second formula.
+        #
+        # ops-hardening iter-49 (J-05/J-07 diagnosis, hypothesis 3): this branch used to be silent, so a
+        # live TC-1 drill could not tell whether this fall-through ever actually fired — a concrete,
+        # checkable way to rule single-flight contention in or out as a driver of `forward_aggregates_warm`'s
+        # observed run-to-run variance (102s / 153s / 1,334s — reports/perf-budgets.md Item R). Logged, not
+        # raised: firing here is expected-rare behavior (TC-8), never a failure.
+        logger.info(
+            "forward-aggregate single-flight wait timed out — falling through to a redundant compute: "
+            "horizon=%s asof_key=%s dataset_version=%s wait_timeout_s=%.1f",
+            horizon, asof_key, version, _FORWARD_AGG_WAIT_TIMEOUT_S,
+        )
 
     # MISS (owner path, or the rare TC-8 fallback above) — compute once and persist.
     try:
@@ -2331,7 +2381,8 @@ def _drawdown_ticker_slice_map(
 
 
 def compute_drawdown_expectations(
-    session: Session, claim: dict, config: Optional[Config] = None
+    session: Session, claim: dict, config: Optional[Config] = None,
+    *, phases: Optional[dict[str, dict]] = None,
 ) -> Optional[dict]:
     """iter-41 (J-25) — the SINGLE canonical phase-conditional drawdown & dry-spell expectations payload
     for ONE certified-claims ledger `claim` (Data Contract value, additive on `GET /api/evidence`). For
@@ -2343,6 +2394,14 @@ def compute_drawdown_expectations(
     walk-forward-cadence longest-losing-streak cell. EVERY configured `market_phase.labels` value is
     emitted (padded, even at n=0) so a cohort that never saw a phase still discloses that honestly.
 
+    `phases` (ops-hardening iter-49, J-05) is an OPTIONAL pre-computed `phase_context_by_date(session,
+    as_of=None, config=cfg)` result — the all-history causal timeline, invariant across every claim for a
+    fixed `(session state, config)`. `None` (the default, every OTHER caller's behavior unchanged)
+    computes it internally exactly as before. A caller warming MULTIPLE claims in the SAME finalize-tail
+    invocation (`data_manager._refresh_ingest_aggregates`'s `drawdown_expectations_warm` loop) computes it
+    ONCE and passes it to every claim instead of paying the SAME all-history read once per claim (7x on
+    the live ledger) — byte-identical either way, since `phases` is looked up by date, never mutated.
+
     Returns None — the caller (`build_evidence_payload`) then omits the `expectations` key entirely, the
     honest 'no panel' signal — when: the claim's `horizon` is missing or outside the configured
     `walk_forward.underwater_horizons` scope, the cohort selectors are malformed/unresolvable (an unknown
@@ -2415,8 +2474,11 @@ def compute_drawdown_expectations(
         rows_by_ticker[row["ticker"]].append(row)
 
     # the SAME causal timeline `compute_market_phase` reads (all-history — the expectations panel is
-    # descriptive over the claim's WHOLE tested cohort, not scoped to a single "today" as-of).
-    phases = phase_context_by_date(session, as_of=None, config=cfg)
+    # descriptive over the claim's WHOLE tested cohort, not scoped to a single "today" as-of). Use the
+    # caller-supplied timeline when given (see the `phases` parameter docstring above); self-compute
+    # otherwise — byte-identical either way.
+    if phases is None:
+        phases = phase_context_by_date(session, as_of=None, config=cfg)
 
     by_phase_mdd: dict[str, list[float]] = defaultdict(list)
     by_phase_uw: dict[str, list[float]] = defaultdict(list)
@@ -2513,7 +2575,8 @@ def _drawdown_expectations_cache_subject(claim: dict) -> str:
 
 
 def compute_drawdown_expectations_cached(
-    session: Session, claim: dict, config: Optional[Config] = None
+    session: Session, claim: dict, config: Optional[Config] = None,
+    *, phases: Optional[dict[str, dict]] = None,
 ) -> Optional[dict]:
     """Serve `compute_drawdown_expectations` from the shared J-72 `EventStudyCache` (a pure performance
     layer — No recompute in the read path): a HIT for the current `(subject, view, asof_key,
@@ -2522,7 +2585,10 @@ def compute_drawdown_expectations_cached(
     cohort is still a stable answer for this dataset version, and caching it avoids re-paying the SAME
     expensive miss every request), prunes stale rows for this claim, and returns it. The returned payload
     is BYTE-IDENTICAL to a fresh `compute_drawdown_expectations(...)` call. `GET /api/evidence` calls THIS
-    function, never the uncached one directly."""
+    function WITHOUT `phases` (never the uncached one directly); the ingest finalize warm loop
+    (`data_manager._refresh_ingest_aggregates`) is the one caller that passes a pre-computed `phases` (see
+    `compute_drawdown_expectations`'s own `phases` docstring) — a pure pass-through, only reached on a
+    MISS, so a HIT still costs nothing beyond the cache read either way."""
     cfg = config or get_config()
     horizon = claim.get("horizon")
     if horizon not in cfg.walk_forward.underwater_horizons:
@@ -2548,7 +2614,7 @@ def compute_drawdown_expectations_cached(
         return json.loads(hit.payload_json)
 
     # MISS — compute once and persist under the current dataset-version stamp.
-    payload = compute_drawdown_expectations(session, claim, cfg)
+    payload = compute_drawdown_expectations(session, claim, cfg, phases=phases)
 
     # prune stale rows for THIS claim (any older dataset_version) so the cache table does not grow
     # unbounded as the dataset matures; the current-version row is then inserted.
diff --git a/apps/backend/app/engine/research.py b/apps/backend/app/engine/research.py
index 34a36d74..b3513c34 100644
--- a/apps/backend/app/engine/research.py
+++ b/apps/backend/app/engine/research.py
@@ -182,6 +182,51 @@ def _extract_factor_value(res: ScannerResult, parsed: dict) -> Optional[float]:
     return None
 
 
+# ops-hardening iter-49 (J-05, drawdown_expectations_warm bound): `_extract_factor_value`'s own body,
+# applied to an already COLUMN-PROJECTED raw value instead of a full `ScannerResult` ORM row.
+# `_factor_decile_observations` below used to stream whole `ScannerResult` entities (every score/flag/
+# date column plus the `record_json` blob) so `_extract_factor_value` could read ONE column or
+# `record_json` off a full row — but every OTHER field of that row goes unused for both branches. Live
+# profiling of a single decile-scoped drawdown-expectations claim (`compute_drawdown_expectations` ->
+# `compute_samples` -> `_factor_samples` -> `_factor_decile_observations`, the `leadership_score` D10 h=20
+# certified claim, on the live committed DB) measured 63.9s dominated by SQLAlchemy/SQLModel ORM row
+# construction (`_instance`/`new_instance`/`_populate_full`/pydantic `__new__`/private-attr init — >40s of
+# the 63.9s, 2.5M row instantiations across the 2-pass decile scan) — NOT by `_extract_factor_value`'s own
+# `getattr`/`json.loads` work, which is cheap. Selecting only `(run_id, ticker, <value column>)` returns
+# raw TUPLES (no ORM instance built at all — the SAME mechanism `_fr_slice_map`/`_forward_agg_slice_map`
+# already use elsewhere in this codebase for exactly this reason), eliminating that construction cost for
+# BOTH factor kinds: a "column" factor's `raw_value` IS the typed column (selected directly, e.g.
+# `ScannerResult.leadership_score`); a "component" factor's `raw_value` is `ScannerResult.record_json`
+# (selected instead of the whole entity — the `json.loads`/block lookup it still needs is unavoidable, but
+# the redundant instantiation of every OTHER column is not). Byte-identical value for value: both branches
+# are `_extract_factor_value`'s own bodies, copied verbatim, reading the pre-selected value instead of
+# `getattr(res, ...)`/`res.record_json`.
+def _extract_factor_value_from_row(raw_value, parsed: dict) -> Optional[float]:
+    if parsed["kind"] == "column":
+        return raw_value
+    try:
+        record = json.loads(raw_value)
+    except (ValueError, TypeError):
+        return None
+    block = record.get(parsed["block"]) if isinstance(record, dict) else None
+    if not isinstance(block, dict):
+        return None
+    for component in block.get("components", []):
+        if isinstance(component, dict) and component.get("name") == parsed["name"]:
+            return component.get("raw")
+    return None
+
+
+def _factor_value_column(parsed: dict):
+    """The single `ScannerResult` column `_extract_factor_value_from_row` will read for this parsed factor
+    source — the typed column itself for `kind == "column"`, `record_json` (the ONE column a `component`
+    factor needs) otherwise. A named helper (not inlined) so `_factor_decile_observations`'s two identical
+    `res_stmt` builds share one definition."""
+    if parsed["kind"] == "column":
+        return getattr(ScannerResult, parsed["column"])
+    return ScannerResult.record_json
+
+
 def _runs_with_fr(
     session: Session, horizons: list[int], as_of: Optional[date_cls],
 ) -> list[int]:
@@ -528,6 +573,11 @@ def _factor_decile_observations(
 
     runs_with_fr = _runs_with_fr(session, [horizon], as_of)
 
+    # ops-hardening iter-49 (J-05): the ONE column `_extract_factor_value_from_row` will read for THIS
+    # factor, resolved once up front — see that function's + `_factor_value_column`'s docstrings for why
+    # this replaces the full-entity `select(ScannerResult)` both passes below used to issue.
+    value_col = _factor_value_column(parsed)
+
     # PASS 0 (count-only, no rows materialized) — the retention window PASS 1 may size itself against.
     # See `_decile_population_upper_bound`: provably >= the observation count, measured at 0.03 s / 0.8%
     # slack on the live basis.
@@ -543,18 +593,18 @@ def _factor_decile_observations(
         slice_run_ids = runs_with_fr[start:start + run_chunk]
         ret_by_run_symbol = _fr_slice_map(session, horizon, slice_run_ids, batch)
         res_stmt = (
-            select(ScannerResult)
+            select(ScannerResult.run_id, ScannerResult.ticker, value_col)
             .where(ScannerResult.run_id.in_(slice_run_ids))
             .order_by(ScannerResult.run_id, ScannerResult.id)
         )
-        for res in session.exec(res_stmt).yield_per(batch):
-            if (res.run_id, res.ticker) not in ret_by_run_symbol:
+        for res_run_id, ticker, raw_value in session.exec(res_stmt).yield_per(batch):
+            if (res_run_id, ticker) not in ret_by_run_symbol:
                 continue
-            value = _extract_factor_value(res, parsed)
+            value = _extract_factor_value_from_row(raw_value, parsed)
             if value is None:
                 continue  # factor-NULL observation EXCLUDED (never bucketed) — mirrors _factor_observations
             n += 1
-            window.add((float(value), res.ticker, res.run_id))
+            window.add((float(value), ticker, res_run_id))
 
     lo = (decile - 1) * n // deciles_count
     hi = decile * n // deciles_count
@@ -592,24 +642,24 @@ def _factor_decile_observations(
         slice_run_ids = runs_with_fr[start:start + run_chunk]
         ret_by_run_symbol = _fr_slice_map(session, horizon, slice_run_ids, batch)
         res_stmt = (
-            select(ScannerResult)
+            select(ScannerResult.run_id, ScannerResult.ticker, value_col)
             .where(ScannerResult.run_id.in_(slice_run_ids))
             .order_by(ScannerResult.run_id, ScannerResult.id)
         )
-        for res in session.exec(res_stmt).yield_per(batch):
-            if (res.ticker, res.run_id) not in target_keys:
+        for res_run_id, ticker, raw_value in session.exec(res_stmt).yield_per(batch):
+            if (ticker, res_run_id) not in target_keys:
                 continue  # not a member of the target decile — discarded immediately, never retained
-            fr = ret_by_run_symbol.get((res.run_id, res.ticker))
+            fr = ret_by_run_symbol.get((res_run_id, ticker))
             if fr is None:
                 continue
             realized, max_drawdown = fr
-            value = _extract_factor_value(res, parsed)
+            value = _extract_factor_value_from_row(raw_value, parsed)
             if value is None:
                 continue
             members.append({
-                "run_id": res.run_id, "ticker": res.ticker, "factor": float(value), "return": realized,
+                "run_id": res_run_id, "ticker": ticker, "factor": float(value), "return": realized,
                 "max_drawdown": max_drawdown,
-                "regime": regime_by_run.get(res.run_id),
+                "regime": regime_by_run.get(res_run_id),
             })
 
     # sort the bounded members by the SAME ascending-by-factor tie-break (pass-2's own chunk order is
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index aed462b0..a41483b6 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -1480,11 +1480,11 @@ def test_finalize_hook_drawdown_expectations_isolates_claim_that_raises(
     real = forward_testing.compute_drawdown_expectations_cached
     calls = {"n": 0}
 
-    def _raise_first_then_real(session, claim, config=None):
+    def _raise_first_then_real(session, claim, config=None, *, phases=None):
         calls["n"] += 1
         if calls["n"] == 1:
             raise RuntimeError("forced claim-warm failure")
-        return real(session, claim, config)
+        return real(session, claim, config, phases=phases)
 
     monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _raise_first_then_real)
     with Session(engine) as session:
@@ -1843,10 +1843,10 @@ def test_finalize_hook_drawdown_expectations_memory_error_after_partial_success_
     real = forward_testing.compute_drawdown_expectations_cached
     calls = {"n": 0}
 
-    def _succeed_then_boom(session, claim, config=None):
+    def _succeed_then_boom(session, claim, config=None, *, phases=None):
         calls["n"] += 1
         if calls["n"] == 1:
-            return real(session, claim, config)
+            return real(session, claim, config, phases=phases)
         raise MemoryError("simulated memory pressure")
 
     monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _succeed_then_boom)
@@ -1890,11 +1890,11 @@ def test_finalize_hook_drawdown_expectations_isolates_claim_that_raises_non_memo
     real = forward_testing.compute_drawdown_expectations_cached
     calls = {"n": 0}
 
-    def _raise_first_then_real(session, claim, config=None):
+    def _raise_first_then_real(session, claim, config=None, *, phases=None):
         calls["n"] += 1
         if calls["n"] == 1:
             raise ValueError("forced non-memory claim-warm failure")
-        return real(session, claim, config)
+        return real(session, claim, config, phases=phases)
 
     monkeypatch.setattr(forward_testing, "compute_drawdown_expectations_cached", _raise_first_then_real)
     with Session(engine) as session:
@@ -1905,6 +1905,248 @@ def test_finalize_hook_drawdown_expectations_isolates_claim_that_raises_non_memo
     assert "drawdown_expectations" in refreshed
 
 
+# ==================================================================================================
+# ops-hardening iter-49 (J-05/J-07, TC-11) — error-case coverage for THIS iteration's own new code: the
+# once-per-finalize-invocation `phase_context_by_date` precomputation in the drawdown-expectations warm
+# loop (`data_manager.py`) and the column-projected read in `_factor_decile_observations`
+# (`research.py`) — both newly added this iteration, neither exercised by the pre-existing per-claim
+# MemoryError/non-memory tests above (which patch `compute_drawdown_expectations_cached` itself, a layer
+# above where these two new pieces of code actually run).
+# ==================================================================================================
+def test_finalize_hook_drawdown_phase_context_warm_non_memory_failure_falls_back_to_per_claim_self_compute(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch,
+):
+    """A genuine non-memory exception inside the NEW once-per-invocation `phase_context_by_date` warm
+    (`data_manager._refresh_ingest_aggregates`'s `drawdown_expectations_warm` block) is caught, logged,
+    and never aborts the finalize hook — it degrades to `phases=None`, so the single claim below falls
+    back to ITS OWN self-compute (`compute_drawdown_expectations`'s pre-iter-49 default: `if phases is
+    None: phases = phase_context_by_date(...)`), which still resolves a genuine payload here. The mock
+    fails ONLY on its first invocation (a transient failure, recovering on retry) — the pre-loop
+    precompute is call 1 (fails), the single claim's own internal fallback is call 2 (succeeds via the
+    real function), so BOTH calls fire and the claim's payload is still genuine."""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), {
+        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
+        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
+    })
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
+
+    real_phase_ctx = market_phase.phase_context_by_date
+    calls = {"n": 0}
+
+    def _boom_once_then_real(session, as_of=None, config=None):
+        calls["n"] += 1
+        if calls["n"] == 1:
+            raise RuntimeError("forced phase-context precompute failure (non-memory probe)")
+        return real_phase_ctx(session, as_of=as_of, config=config)
+
+    monkeypatch.setattr(market_phase, "phase_context_by_date", _boom_once_then_real)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="dd-phase-ctx-nonmem-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert calls["n"] == 2, (
+        "the pre-loop precompute (call 1, fails) plus the single claim's own internal self-compute "
+        "fallback (call 2, succeeds) must both have fired"
+    )
+    assert "drawdown_expectations" in refreshed, (
+        f"the per-claim self-compute fallback must still resolve a genuine payload; refreshed={refreshed}"
+    )
+
+
+def test_finalize_hook_drawdown_phase_context_warm_memory_error_releases_and_stops_before_any_claim(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch,
+):
+    """The SAME precompute step, but a `MemoryError` — caught by ITS OWN distinct handler applying the
+    iter-8 convention IN FULL: `_release_process_memory()` runs AND the per-claim loop is skipped entirely.
+
+    ops-hardening iter-49 AUDIT (finding B3): this test previously asserted the opposite (fall through to
+    per-claim self-compute). Falling through set `phases=None`, so every claim then self-computed its own
+    all-history timeline — under memory pressure the handler degraded to the MORE allocating path, the
+    exact behavior the iter-8 convention exists to prevent. The mock still fails only on its FIRST
+    invocation, so a fall-through would visibly succeed on call 2; asserting `calls["n"] == 1` therefore
+    proves the loop was genuinely skipped rather than merely erroring again, and `drawdown_expectations`
+    must be honestly ABSENT from the refreshed list (nothing was warmed)."""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), {
+        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
+        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
+    })
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
+    release_calls = []
+    monkeypatch.setattr(
+        data_manager, "_release_process_memory", lambda: release_calls.append("called"),
+    )
+
+    real_phase_ctx = market_phase.phase_context_by_date
+    calls = {"n": 0}
+
+    def _boom_once_then_real(session, as_of=None, config=None):
+        calls["n"] += 1
+        if calls["n"] == 1:
+            raise MemoryError("simulated memory pressure (phase-context precompute)")
+        return real_phase_ctx(session, as_of=as_of, config=config)
+
+    monkeypatch.setattr(market_phase, "phase_context_by_date", _boom_once_then_real)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="dd-phase-ctx-mem-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert release_calls, "the iter-8 convention requires _release_process_memory() on the MemoryError path"
+    assert calls["n"] == 1, (
+        "the per-claim loop must be skipped entirely after a memory-pressure abort in the precompute — a "
+        f"second phase_context_by_date call means a claim self-computed its own timeline anyway (calls={calls['n']})"
+    )
+    assert "drawdown_expectations" not in refreshed, (
+        f"nothing was warmed after the memory-pressure abort, so the category must be honestly omitted; "
+        f"refreshed={refreshed}"
+    )
+
+
+def test_finalize_hook_drawdown_expectations_column_projected_read_non_memory_failure_isolated(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch,
+):
+    """TC-11 — a genuine non-memory exception raised INSIDE `_factor_decile_observations`'s NEW
+    column-projected read (`research._extract_factor_value_from_row`, the iter-49 column-projection fix's
+    own new code) is caught by the SAME per-claim isolation convention every other claim-warm failure
+    already relies on: the finalize hook never raises, "drawdown_expectations" is honestly omitted for a
+    single-claim ledger, and the failure is logged.
+
+    Uses a DECILE-scoped claim (`slice_kind: "decile"`, mirroring the real live ledger's 5 decile-scoped
+    claims), NOT `_DD_LEDGER_CLAIM` (`slice_kind: "total"`, the "total"/`_factor_observations` branch this
+    iteration deliberately left untouched) — only the decile branch reaches
+    `_extract_factor_value_from_row` at all."""
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    decile_claim = {**_DD_LEDGER_CLAIM, "slice_kind": "decile", "decile": 10}
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), {
+        "claim": decile_claim, "register_date": "2024-06-01",
+        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
+    })
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
+
+    import app.engine.research as research_module
+
+    boom_calls = {"n": 0}
+
+    def _boom(*_a, **_k):
+        boom_calls["n"] += 1
+        raise RuntimeError("forced column-projected extractor failure (non-memory probe)")
+
+    monkeypatch.setattr(research_module, "_extract_factor_value_from_row", _boom)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="dd-col-proj-nonmem-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    # ops-hardening iter-49 AUDIT (T1): without this the proof is VACUOUS — "drawdown_expectations" is
+    # absent from `refreshed` for many reasons that have nothing to do with the injected fault (an
+    # unresolvable cohort, an out-of-scope horizon, a decile branch never reached on this fixture all
+    # produce the SAME observable). Asserting the injected extractor actually RAN is what makes the
+    # remaining assertion evidence of isolation rather than of a no-op.
+    assert boom_calls["n"] > 0, (
+        "the injected failure never fired — this claim never reached the new column-projected extractor, "
+        "so the isolation assertion below would pass vacuously"
+    )
+    assert "drawdown_expectations" not in refreshed, (
+        f"the single claim's own extractor failure must be honestly omitted, never fabricated; "
+        f"refreshed={refreshed}"
+    )
+
+
+# ops-hardening iter-49 AUDIT (finding T1) — TC-2's own regression guard, and the memoization guard the
+# suite was missing entirely. The phase spec's TESTING REQUIREMENTS ask for "per-horizon/per-claim
+# sub-phase timing tests"; before this test the ONLY evidence for TC-2 was three live-run log reads
+# (reports/perf-budgets.md Addendum 4/6) and nothing in the suite asserted either new log line, so a
+# refactor could silently drop the attribution this iteration exists to provide. The same gap covered the
+# iteration's actual bound: `phases` is threaded into every claim, but no test proved the timeline is
+# computed ONCE per finalize invocation rather than once per claim — and it cannot be caught by the
+# byte-identity proofs (both paths are byte-identical BY CONSTRUCTION; dropping `phases=_dd_phases`
+# restores the per-claim cost with every existing assertion still green).
+def test_finalize_hook_sub_phase_timing_names_each_horizon_and_claim_and_memoizes_phase_context(
+    finalize_hook_drawdown_engine, tmp_path, monkeypatch, caplog,
+):
+    """TC-2 + the `phases` memoization, on the SAME finalize-tail invocation.
+
+    TC-2: the per-horizon and per-claim sub-phase timing lines are emitted for EVERY configured horizon
+    and for the claim, each naming a specific horizon/claim identity (never a bare loop index, which is
+    not diagnostic across runs whose ledger order can change), and the pre-existing whole-phase lines for
+    both loops still fire unchanged alongside them.
+
+    Memoization: `phase_context_by_date` is called EXACTLY ONCE for a finalize invocation whose claim
+    genuinely computes a payload — proving the pre-loop precompute is what the claim consumed. Without
+    the threading (`phases=None` reaching `compute_drawdown_expectations`) this same fixture calls it
+    twice: once in the precompute, once in the claim's own self-compute.
+    """
+    engine, d = finalize_hook_drawdown_engine
+    cfg = load_config()
+    ledger = tmp_path / "certified-claims.jsonl"
+    append_entry(str(ledger), {
+        "claim": _DD_LEDGER_CLAIM, "register_date": "2024-06-01",
+        "verdict": {"status": "FAIL", "reason": "test fixture — not a real certification"},
+    })
+    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
+
+    # wrap (never replace) the fixture's own fake timeline so the payload below is still genuine.
+    fixture_phase_ctx = market_phase.phase_context_by_date
+    phase_ctx_calls = {"n": 0}
+
+    def _counting_phase_ctx(session=None, as_of=None, config=None):
+        phase_ctx_calls["n"] += 1
+        return fixture_phase_ctx(session, as_of=as_of, config=config)
+
+    monkeypatch.setattr(market_phase, "phase_context_by_date", _counting_phase_ctx)
+
+    with caplog.at_level("INFO", logger="trendora.data_manager"):
+        with Session(engine) as session:
+            prog = JobProgress(job_id="sub-phase-timing-probe", kind="backfill", start=d, end=d)
+            prog.new_snapshot_dates = [d]
+            refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+
+    lines = [r.getMessage() for r in caplog.records]
+    sub = [m for m in lines if m.startswith("J-05 finalize-tail sub-phase timing:")]
+    whole = [m for m in lines if m.startswith("J-05 finalize-tail phase timing:")]
+
+    # --- TC-2, forward_aggregates_warm: one line per CONFIGURED horizon, naming that horizon -------
+    for h in cfg.walk_forward.horizons:
+        assert any(
+            f"phase=forward_aggregates_warm horizon={h} elapsed=" in m for m in sub
+        ), f"no sub-phase timing line named horizon={h}; sub-phase lines seen: {sub}"
+
+    # --- TC-2, drawdown_expectations_warm: one line per claim, naming THAT claim -------------------
+    dd_lines = [m for m in sub if "phase=drawdown_expectations_warm" in m]
+    assert len(dd_lines) == 1, f"expected exactly one per-claim line for a 1-claim ledger; got {dd_lines}"
+    claim_token = dd_lines[0].split("claim=")[1].split(" elapsed=")[0]
+    assert claim_token == "factor:leadership_score:h20", (
+        f"the per-claim identity must name the claim's kind + discriminating selector + horizon; "
+        f"got {claim_token!r}"
+    )
+    # a bare loop index would satisfy "some identity" while being useless across runs (the log's own
+    # stated contract) — assert the token is not merely a number.
+    assert not claim_token.isdigit(), f"per-claim identity must never be a raw loop index: {claim_token!r}"
+    assert "elapsed=" in dd_lines[0]
+
+    # --- the pre-existing whole-phase lines are ADDITIVE-unchanged, not replaced ------------------
+    for phase in ("forward_aggregates_warm", "drawdown_expectations_warm"):
+        assert any(
+            f"phase={phase} elapsed=" in m for m in whole
+        ), f"the pre-existing whole-phase timing line for {phase} must still fire; whole-phase lines: {whole}"
+
+    # --- the memoization itself -------------------------------------------------------------------
+    assert "drawdown_expectations" in refreshed, (
+        "fixture sanity: the claim must genuinely compute a payload, otherwise the call-count assertion "
+        f"below proves nothing about a timeline that was never needed; refreshed={refreshed}"
+    )
+    assert phase_ctx_calls["n"] == 1, (
+        "the all-history timeline must be computed ONCE per finalize invocation and threaded into every "
+        f"claim; {phase_ctx_calls['n']} calls means a claim self-computed its own"
+    )
+
+
 # ==================================================================================================
 # ops-hardening iter-9 (B2): the resolved libc `CDLL` handle inside `_release_process_memory()` is
 # memoized module-level (first-call-cached) instead of re-resolved via `ctypes.util.find_library` +
diff --git a/apps/backend/tests/test_evidence.py b/apps/backend/tests/test_evidence.py
index 65b1b949..1a1e4421 100644
--- a/apps/backend/tests/test_evidence.py
+++ b/apps/backend/tests/test_evidence.py
@@ -15,6 +15,7 @@ fail-safe contract:
 """
 from __future__ import annotations
 
+import json
 from datetime import date, datetime, timedelta, timezone
 from pathlib import Path
 
@@ -607,6 +608,50 @@ def test_build_payload_session_provided_attaches_expectations(tmp_path, evidence
     assert exp_phase["n"] == 1
 
 
+# ops-hardening iter-49 AUDIT (finding T1) — TC-3's drawdown leg covered the column-projection change
+# (`test_research_streaming.py`, `_factor_decile_observations` vs a pinned full-entity reference) but NOT
+# the OTHER change shipped in the same iteration: the new, additive `phases` parameter on
+# `compute_drawdown_expectations`/`_cached`. The ingest finalize warm loop
+# (`data_manager._refresh_ingest_aggregates`) is the ONE caller that threads a pre-computed all-history
+# timeline through it, and every `event_study_cache` payload `/api/evidence` later SERVES is written by
+# exactly that path — so a divergence between the threaded and the self-computed timeline would silently
+# persist wrong drawdown/dry-spell figures behind a "proven" claim (AG-3). Nothing in the suite asserted
+# that equivalence; these two proofs pin it at both entry points.
+def test_compute_drawdown_expectations_precomputed_phases_is_byte_identical(evidence_dd_engine):
+    """The uncached producer returns a byte-identical payload whether the caller threads a pre-computed
+    `phase_context_by_date(session, as_of=None, config=cfg)` timeline (the ingest finalize warm loop's
+    shape) or lets it self-compute (`phases=None`, every other caller's shape)."""
+    cfg = load_config()
+    claim = _pass_entry("leadership_score")["claim"]
+    with Session(evidence_dd_engine) as session:
+        self_computed = forward_testing.compute_drawdown_expectations(session, claim, cfg)
+        precomputed = market_phase.phase_context_by_date(session, as_of=None, config=cfg)
+        threaded = forward_testing.compute_drawdown_expectations(session, claim, cfg, phases=precomputed)
+    assert self_computed is not None, "fixture sanity: this claim must resolve to a real payload"
+    assert self_computed["by_phase"], "fixture sanity: the payload must carry real per-phase rows"
+    assert json.dumps(threaded, sort_keys=True) == json.dumps(self_computed, sort_keys=True)
+
+
+def test_drawdown_expectations_cached_persists_same_payload_when_phases_threaded(evidence_dd_engine):
+    """The CACHED entry point the ingest warm actually calls persists (and returns) the SAME payload a
+    fresh, `phases`-less canonical computation produces — the stored `event_study_cache` row `/api/evidence`
+    serves is not a second, divergent computation."""
+    cfg = load_config()
+    claim = _pass_entry("leadership_score")["claim"]
+    with Session(evidence_dd_engine) as session:
+        canonical = forward_testing.compute_drawdown_expectations(session, claim, cfg)
+        precomputed = market_phase.phase_context_by_date(session, as_of=None, config=cfg)
+        # MISS -> computes with the threaded timeline and persists under the current dataset version.
+        written = forward_testing.compute_drawdown_expectations_cached(
+            session, claim, cfg, phases=precomputed
+        )
+        # HIT -> re-serves the persisted row (proving what was STORED, not just what was returned).
+        served = forward_testing.compute_drawdown_expectations_cached(session, claim, cfg)
+    assert canonical is not None, "fixture sanity: this claim must resolve to a real payload"
+    assert json.dumps(written, sort_keys=True) == json.dumps(canonical, sort_keys=True)
+    assert json.dumps(served, sort_keys=True) == json.dumps(canonical, sort_keys=True)
+
+
 def test_build_payload_session_provided_unresolvable_claim_no_expectations_key(tmp_path, evidence_dd_engine):
     """A session IS provided but the claim's cohort is unresolvable (an unknown factor) — the row still
     carries NO `expectations` key (graceful, matches the session-omitted case; never a crash, never a
diff --git a/apps/backend/tests/test_research_streaming.py b/apps/backend/tests/test_research_streaming.py
index 8a112900..7ee11d78 100644
--- a/apps/backend/tests/test_research_streaming.py
+++ b/apps/backend/tests/test_research_streaming.py
@@ -1167,6 +1167,187 @@ def test_factor_decile_observations_zero_n_cohort_is_honest_empty(chunked_accumu
     assert members == []
 
 
+# ==================================================================================================
+# ops-hardening iter-49 (J-05, drawdown_expectations_warm bound) — `_factor_decile_observations`'s two
+# `res_stmt` reads used to `select(ScannerResult)` (the FULL ORM entity, every score/flag/date column plus
+# the `record_json` blob) purely so `_extract_factor_value` could do a `getattr`/`.record_json` on a full
+# row. Live profiling (a single decile-scoped drawdown-expectations claim on the real committed DB)
+# measured >40s of a 63.9s call as SQLAlchemy/SQLModel ORM row construction alone — unrelated to
+# `_extract_factor_value`'s own cheap `getattr`/`json.loads`. `_extract_factor_value_from_row` +
+# `_factor_value_column` (new) column-project the read to `(run_id, ticker, <value column>)` instead —
+# raw tuples, no ORM row built at all — for BOTH factor kinds ("column": the typed column selected
+# directly; "component": `record_json` selected instead of the whole entity, so nothing the extractor
+# reads is dropped). These proofs pin byte-identity against the PRE-FIX full-entity approach, for both
+# kinds, mirroring `test_factor_decile_observations_equals_pre_fix_reference` above exactly.
+# ==================================================================================================
+def _factor_decile_observations_full_entity_reference(session, factor, horizon, as_of, deciles_count, decile, cfg):
+    """The PRE-iter-49 `_factor_decile_observations` body, pinned verbatim (full-entity `select(ScannerResult)`
+    in both passes, `_extract_factor_value` reading a real ORM row) — the regression oracle for the iter-49
+    column-projection rewrite. Calls the SAME unchanged `_runs_with_fr` / `_fr_slice_map` /
+    `_decile_population_upper_bound` / `_BoundedRankWindow` / `_extract_factor_value` helpers the real,
+    rewritten function still uses, so any divergence can only come from the two `res_stmt` projections."""
+    from app.engine.research import (
+        _BoundedRankWindow, _decile_population_upper_bound, _extract_factor_value, _fr_slice_map,
+        _runs_with_fr, parse_factor_source,
+    )
+
+    parsed = parse_factor_source(factor.source)
+    research_cfg = cfg.research
+    batch = research_cfg.read_batch_size
+    run_chunk = research_cfg.factor_join_run_chunk
+    runs_with_fr = _runs_with_fr(session, [horizon], as_of)
+    n_max = _decile_population_upper_bound(session, runs_with_fr, run_chunk)
+    window = _BoundedRankWindow(n_max, deciles_count, decile)
+
+    n = 0
+    for start in range(0, len(runs_with_fr), run_chunk):
+        slice_run_ids = runs_with_fr[start:start + run_chunk]
+        ret_by_run_symbol = _fr_slice_map(session, horizon, slice_run_ids, batch)
+        res_stmt = (
+            select(ScannerResult).where(ScannerResult.run_id.in_(slice_run_ids))
+            .order_by(ScannerResult.run_id, ScannerResult.id)
+        )
+        for res in session.exec(res_stmt).yield_per(batch):
+            if (res.run_id, res.ticker) not in ret_by_run_symbol:
+                continue
+            value = _extract_factor_value(res, parsed)
+            if value is None:
+                continue
+            n += 1
+            window.add((float(value), res.ticker, res.run_id))
+
+    lo = (decile - 1) * n // deciles_count
+    hi = decile * n // deciles_count
+    ranked = window.slice(n, lo, hi)
+    assert ranked is not None, "test fixture too small for the upper-bound invariant — widen it"
+    target_keys = {(ticker, run_id) for _factor_val, ticker, run_id in ranked}
+    if not target_keys:
+        return []
+
+    run_rows = (
+        session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
+        if runs_with_fr else []
+    )
+    regime_by_run = {run.id: run.regime_label for run in run_rows}
+
+    members = []
+    for start in range(0, len(runs_with_fr), run_chunk):
+        slice_run_ids = runs_with_fr[start:start + run_chunk]
+        ret_by_run_symbol = _fr_slice_map(session, horizon, slice_run_ids, batch)
+        res_stmt = (
+            select(ScannerResult).where(ScannerResult.run_id.in_(slice_run_ids))
+            .order_by(ScannerResult.run_id, ScannerResult.id)
+        )
+        for res in session.exec(res_stmt).yield_per(batch):
+            if (res.ticker, res.run_id) not in target_keys:
+                continue
+            fr = ret_by_run_symbol.get((res.run_id, res.ticker))
+            if fr is None:
+                continue
+            realized, max_drawdown = fr
+            value = _extract_factor_value(res, parsed)
+            if value is None:
+                continue
+            members.append({
+                "run_id": res.run_id, "ticker": res.ticker, "factor": float(value), "return": realized,
+                "max_drawdown": max_drawdown,
+                "regime": regime_by_run.get(res.run_id),
+            })
+    members.sort(key=lambda o: (o["factor"], o["ticker"], o["run_id"]))
+    return members
+
+
+@pytest.mark.parametrize("as_of", [None, date(2025, 3, 15)])
+@pytest.mark.parametrize("decile", [1, 5, 10])
+def test_factor_decile_observations_column_projected_equals_full_entity_reference(
+    chunked_accumulator_engine, as_of, decile,
+):
+    """TC-3 (byte-identity leg, "column"-kind factor): the iter-49 column-projected
+    `_factor_decile_observations` is byte-identical to the pinned pre-iter-49 (full-entity `select
+    (ScannerResult)`) reference — across the first/middle/last decile and both all-history and a
+    historical as_of, under a chunk width small enough to force multiple slices in BOTH passes."""
+    cfg = _cfg_batch(2)
+    deciles_count = cfg.research.factor_lab.deciles
+    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
+    with Session(chunked_accumulator_engine) as session:
+        shipped = research_module._factor_decile_observations(
+            session, factor, H, as_of, deciles_count, decile, cfg=cfg
+        )
+        reference = _factor_decile_observations_full_entity_reference(
+            session, factor, H, as_of, deciles_count, decile, cfg
+        )
+    assert _eq(shipped, reference), (
+        f"column-projected decile {decile} (as_of={as_of}) != full-entity pre-iter-49 reference"
+    )
+
+
+def test_factor_decile_observations_column_projected_equals_full_entity_reference_component_kind(
+    component_engine,
+):
+    """TC-3 (byte-identity leg, "component"-kind factor): the SAME proof as above, for a factor whose value
+    lives in `record_json` (never a typed column) — the case where a naive column projection dropping
+    `record_json` would silently change figures. `_factor_value_column` selects `record_json` itself
+    (not the whole entity) for this kind, so nothing `_extract_factor_value_from_row` reads is lost.
+    `component_engine`'s 4 non-zero-FR observations (AA/BB/CC/DD) are split with a REDUCED `deciles=2` (the
+    real `factor_lab.deciles` default of 10 would make every decile a singleton on this small fixture,
+    a much weaker discriminator for the chunk-and-project rewrite)."""
+    cfg = load_config()
+    cfg = cfg.model_copy(update={"research": cfg.research.model_copy(update={
+        "read_batch_size": 1, "factor_join_run_chunk": 1,
+        "factor_lab": cfg.research.factor_lab.model_copy(update={"deciles": 2}),
+    })})
+    factor = next(f for f in cfg.research.factor_lab.factors if f.key == "rs_spy_3m")
+    assert factor is not None, "sanity: rs_spy_3m must be a configured component-kind factor"
+    with Session(component_engine) as session:
+        for decile in (1, 2):
+            shipped = research_module._factor_decile_observations(
+                session, factor, H, None, 2, decile, cfg=cfg
+            )
+            reference = _factor_decile_observations_full_entity_reference(
+                session, factor, H, None, 2, decile, cfg
+            )
+            assert _eq(shipped, reference), (
+                f"component-kind column-projected decile {decile} != full-entity pre-iter-49 reference"
+            )
+        # sanity: the fixture's component values are genuinely non-trivial (not an accidental all-None
+        # cohort that would make this proof vacuous).
+        d1 = research_module._factor_decile_observations(session, factor, H, None, 2, 1, cfg=cfg)
+        d2 = research_module._factor_decile_observations(session, factor, H, None, 2, 2, cfg=cfg)
+    assert d1 and d2, "sanity: both component-kind deciles must be non-empty on this fixture"
+
+
+def test_extract_factor_value_from_row_equals_extract_factor_value(chunked_accumulator_engine, component_engine):
+    """Direct unit proof that `_extract_factor_value_from_row` (fed the pre-selected column/record_json)
+    is byte-identical to `_extract_factor_value` (fed the full ORM row) for both factor kinds, on real
+    stored rows from both fixtures — the primitive the two decile-observation proofs above exercise only
+    indirectly through the full two-pass algorithm."""
+    from app.engine.research import (
+        _extract_factor_value, _extract_factor_value_from_row, _factor_value_column, parse_factor_source,
+    )
+
+    cfg = load_config()
+    column_factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
+    component_factor = next(f for f in cfg.research.factor_lab.factors if f.key == "rs_spy_3m")
+    column_parsed = parse_factor_source(column_factor.source)
+    component_parsed = parse_factor_source(component_factor.source)
+    assert column_parsed["kind"] == "column"
+    assert component_parsed["kind"] == "component"
+
+    with Session(chunked_accumulator_engine) as session:
+        for res in session.exec(select(ScannerResult)).all():
+            col = _factor_value_column(column_parsed)
+            raw_value = getattr(res, col.key)
+            assert _extract_factor_value_from_row(raw_value, column_parsed) == _extract_factor_value(
+                res, column_parsed
+            )
+
+    with Session(component_engine) as session:
+        for res in session.exec(select(ScannerResult)).all():
+            assert _extract_factor_value_from_row(res.record_json, component_parsed) == _extract_factor_value(
+                res, component_parsed
+            )
+
+
 # ==================================================================================================
 # ops-hardening iter-48 (AG-8, iter-47 next-step item 5) — `app.engine.samples._factor_samples`'s
 # "regime" branch used to build the FULL `_factor_observations` list (whole horizon population) just to
diff --git a/apps/backend/tests/test_start_backend_script.py b/apps/backend/tests/test_start_backend_script.py
index f09fb8b4..5c303975 100644
--- a/apps/backend/tests/test_start_backend_script.py
+++ b/apps/backend/tests/test_start_backend_script.py
@@ -73,6 +73,9 @@ _DEVSCRIPT_FRONTEND_PORT = 19700 + _offset
 _NOCAP_TEST_PORT = 18800 + _offset
 # A SIXTH port for the ops-hardening iter-44 ServerOpsCfg-flags fast-shutdown test below.
 _FAST_SHUTDOWN_TEST_PORT = 18900 + _offset
+# A SEVENTH pair for the ops-hardening iter-49 J-04 boot/crash/restart tests at the end of this module
+# (`+ 1` is the scratch-DB crash/restart test's own port; their frontend ports are `+ 1000` as usual).
+_J04_TEST_PORT = 19100 + _offset
 
 # ops-hardening iter-9 (AG-10): the real, committed host-guard config this project runs under.
 HOST_GUARD_ENV_FILE = REPO_ROOT / "project-extensions" / "host-guard" / "host-guard.env"
@@ -856,15 +859,29 @@ _HISTORICAL_GAP_INSERT_TC1_BOUND_S = 1200.0
 @pytest.mark.xfail(
     strict=False,
     reason=(
-        "ops-hardening iter-48 AUDIT (T2, reviewer MINOR note): TC-1's END-TO-END 20-minute bound is not "
-        "met on this build because of TWO pre-existing finalize-tail phases this iteration's scope "
-        "explicitly excludes -- `forward_aggregates_warm` (102.48s / 153.07s / 1334.13s across three live "
-        "runs; the 1334.13s run ALONE exceeds the whole 1200s bound) and `drawdown_expectations_warm` "
-        "(667.30s in the one run that completed, unbounded in two others). This iteration's OWN fix "
-        "target, `coverage_membership_timeline_refresh`, is fast and bounded across all three runs "
-        "(9.18s / 24.10s / 21.01s). Marked xfail(strict=False) rather than deleted so the gap keeps "
-        "signalling without failing the suite, and so it XPASSes (never errors) the moment a future "
-        "iteration bounds those two phases -- at which point delete this marker."
+        "ops-hardening iter-49 (J-05/J-07): TC-1's own 1,200s termination bound IS now reliably met -- "
+        "`forward_aggregates_warm` and `drawdown_expectations_warm` (the two phases iter-48's audit named "
+        "as the residual blocker) are both bounded this iteration and the job reaches a terminal status "
+        "in 1012.71s / 1048.22s / 1044.77s across 3 independent live runs (well inside the 1,200s bound; "
+        "`reports/perf-budgets.md` Item R Addendum 4). This test is left xfail, NOT because TC-1 itself "
+        "fails, but because it bundles a SEPARATE, newly-surfaced defect into the SAME assertion block: "
+        "a reproducible ~10s `GET /api/health` timeout (2 of 3 runs, `poll_index` 21-22, httpx "
+        "`timeout=10.0`) during the EARLY backfill/`coverage_membership_timeline_refresh` boundary -- "
+        "BEFORE either phase this iteration bounds even starts, and unrelated to this iteration's own "
+        "diff (unchanged by `git diff`: `_do_backfill`'s scoring path, `_excluded_counts_by_date`). Status/"
+        "snapshots_created/aggregates_refreshed/VmPeak all passed in every run that reached the health "
+        "assertion (pytest stops at the first failing assert, and the health check is last), so this is "
+        "the health-poll gap alone, never a loosened TC-1 assertion. goal.md's own OUT OF SCOPE list "
+        "names this class of finding explicitly ('Health-poll ceiling breach re-measurement -- folded "
+        "into required-still-passing verification, no fix attempted this round'), so it is disclosed, "
+        "not fixed, here. AUDIT CORRECTION (see reports/perf-budgets.md Addendum 6): the ~10s timeouts "
+        "are at that boundary, but they are not the whole finding -- the >=2s ceiling is breached 6-9 "
+        "times per run in 3 of 3 runs, with a mid-run cluster inside this iteration's OWN "
+        "phase_context_by_date precompute and the two largest 200-OK stalls (7.9s/9.7s) inside the "
+        "un-optimised combination:composite claim, so the follow-up must cover all three sites. "
+        "Marked xfail(strict=False) so the "
+        "gap keeps signalling without failing the suite, and so it XPASSes (never errors) the moment the "
+        "health-poll gap is closed -- at which point delete this marker."
     ),
 )
 def test_start_backend_historical_gap_insert_reaches_terminal_status_within_bound(
@@ -920,7 +937,13 @@ def test_start_backend_historical_gap_insert_reaches_terminal_status_within_boun
 
     backend = spawned_backend_throwaway_db
     cfg = get_config()
+    cap_kb = cfg.server.memory_cap_mb * 1024
 
+    # ops-hardening iter-49 (TC-5): sample /proc/<pid>/status throughout the SAME drill so this one live
+    # run also proves the VmPeak margin against the declared memory_cap_mb, mirroring the sibling
+    # back-to-back-heavy-ingest test's own pattern — no need for a second, separate drill.
+    mem = _MemSampler(backend.pid)
+    mem.start()
     health = _HealthPoller(backend.port)
     health.start()
     elapsed_s = None
@@ -931,10 +954,17 @@ def test_start_backend_historical_gap_insert_reaches_terminal_status_within_boun
         job = _poll_job_to_terminal(backend.port, job_id, timeout_s=_HISTORICAL_GAP_INSERT_TC1_BOUND_S)
         elapsed_s = time.monotonic() - t0
     finally:
+        mem.stop()
+        mem.join(timeout=5)
         health.stop()
         health.join(timeout=5)
+        sampler_csv = os.environ.get("TRENDORA_HEAVY_INGEST_SAMPLER_CSV")
+        if sampler_csv:
+            _write_run_evidence(Path(sampler_csv), mem, health)
         print(
             f"\n[historical-gap-insert] elapsed_s={elapsed_s} "
+            f"peak_VmPeak_kb={mem.peak('VmPeak')} peak_VmSize_kb={mem.peak('VmSize')} "
+            f"cap_kb={cap_kb} "
             f"health_polls={len(health.results)} "
             f"health_non_200={len([r for r in health.results if r['status'] != 200])}"
         )
@@ -947,6 +977,17 @@ def test_start_backend_historical_gap_insert_reaches_terminal_status_within_boun
         f"job reached terminal status but took {elapsed_s:.1f}s, over TC-1's "
         f"{_HISTORICAL_GAP_INSERT_TC1_BOUND_S:.0f}s bound"
     )
+    # TC-5 — process VmPeak/VmSize stay under the declared server.memory_cap_mb cap throughout the SAME
+    # drill (AG-10 — never re-tuned by this iteration; the cap value itself is asserted unchanged
+    # elsewhere, TC-10).
+    peak_vmpeak = mem.peak("VmPeak")
+    peak_vmsize = mem.peak("VmSize")
+    assert mem.samples, "expected at least one /proc/<pid>/status sample across the whole run"
+    assert peak_vmpeak < cap_kb, (
+        f"peak VmPeak {peak_vmpeak} KB ({peak_vmpeak / 1024:.1f} MB) reached/exceeded the "
+        f"{cap_kb} KB ({cfg.server.memory_cap_mb} MB) ulimit -v cap"
+    )
+    assert peak_vmsize < cap_kb, f"peak VmSize {peak_vmsize} KB reached/exceeded the {cap_kb} KB cap"
     # scenario-integrity guard (mirrors the sibling heavy-ingest test): this date was picked specifically
     # because it had no snapshot, so it MUST have created one -- a zero-work no-op here would prove
     # nothing about the finalize-tail fix this test exists to measure.
@@ -1319,3 +1360,297 @@ def test_dev_script_host_guard_disabled_backend_starts_cleanly_with_no_caps():
                 proc.wait(timeout=10)
             except (ChildProcessError, subprocess.TimeoutExpired):
                 pass
+
+
+# ==================================================================================================
+# ops-hardening iter-49 AUDIT (finding F2 / phase-spec TC-9) — J-04's own EXECUTED row, produced by a
+# lane that is PERMITTED to restart services.
+#
+# J-04 ("Non-blocking boot with visible status") produced ZERO executed rows for three consecutive
+# rounds. Its assigned lane was the browser-qa agent, which is structurally forbidden from doing what
+# J-04's own steps require: "restarting/killing the backend is out of scope for this browser-only QA
+# agent" (`reports/phase-goal-ops-hardening-iter-49-ui-test-results.md`, UT-J-04 = SKIPPED). Writing
+# "non-negotiable" into a fifth spec cannot fix a lane that is not allowed to perform the action, so
+# the audit's recommendation 2 reassigns the row here — this module already spawns and SIGKILLs real
+# backends through the real `scripts/start-backend.sh`.
+#
+# Coverage of J-04's steps (`docs/goal.md`):
+#   1-2  boot -> first HTTP 200 within 5 s on the warm committed DB ......... test_j04_boot_serves_...
+#   3    a polled pre-ready payload carries the boot phase + progress n/m ... test_j04_crash_...
+#   4    a killed backend is UNREACHABLE (connection refused), categorically
+#        distinct from `initializing` (an HTTP 200 carrying a phase) ........ test_j04_crash_...
+#   5    persistent logfile carries boot events / ends abruptly after a
+#        crash .............................................................. ALREADY covered above by
+#        `test_start_backend_writes_persistent_logfile_with_boot_events` and
+#        `test_start_backend_logfile_ends_abruptly_after_simulated_crash` — deliberately not duplicated.
+#   6    after the restart, a job that was mid-flight at the kill reads back
+#        `interrupted` WITH its last persisted progress ..................... test_j04_crash_...
+# The UI-presentation halves of steps 3-4 (top-bar badge / preflight-banner rendering) stay browser-lane
+# work; everything the backend itself owns is proven here, live, against the real launch script.
+# ==================================================================================================
+_J04_BOOT_BUDGET_S = 5.0  # docs/goal.md Success Criteria + J-04 step 2 (warm committed DB)
+_J04_POLL_INTERVAL_S = 0.2  # J-04 step 3 requires polling at <= 250 ms from process start
+# The four honest readiness states `app.engine.readiness` can return (its own module docstring) — the
+# single Data-Contract producer for this value.
+_J04_READINESS_STATES = frozenset({"ready", "initializing", "unavailable", "awaiting_snapshot"})
+
+
+def _assert_health_payload_is_honest(payload: dict) -> None:
+    """Every HTTP 200 a booting backend serves must carry the readiness Data-Contract shape: one of the
+    four honest states, plus the warm-up progress the badge renders as "history n/m" (J-04 step 3's
+    "boot phase and progress n/m"). A `db_ok: false` payload must NEVER claim anything but
+    `unavailable` (J-04 acceptance: no "Ready" before real data is servable)."""
+    assert payload.get("readiness") in _J04_READINESS_STATES, (
+        f"readiness must be one of {sorted(_J04_READINESS_STATES)}; got {payload.get('readiness')!r}"
+    )
+    warm = payload.get("warmup")
+    assert isinstance(warm, dict), f"health must carry the warmup progress block; got {warm!r}"
+    done, total = warm.get("done"), warm.get("total")
+    assert isinstance(done, int) and isinstance(total, int), f"warmup done/total must be ints: {warm}"
+    assert warm.get("message") == f"history {done}/{total}", (
+        f"warmup message must be the 'n/m' progress the badge renders; got {warm.get('message')!r} "
+        f"for done={done} total={total}"
+    )
+    if payload.get("db_ok") is not True:
+        assert payload.get("readiness") == "unavailable", (
+            f"a payload whose DB read failed must report 'unavailable', never a fabricated state: {payload}"
+        )
+
+
+def _j04_poll_until_first_200(port: int, t0: float, timeout_s: float) -> tuple[float, dict, int]:
+    """Poll `GET /api/health` at `_J04_POLL_INTERVAL_S` from `t0` (taken immediately before the launch
+    script was spawned) until the FIRST HTTP 200. Returns (elapsed_to_first_200, payload, attempts)."""
+    attempts = 0
+    deadline = t0 + timeout_s
+    while time.monotonic() < deadline:
+        attempts += 1
+        try:
+            resp = httpx.get(f"http://127.0.0.1:{port}/api/health", timeout=2.0)
+            if resp.status_code == 200:
+                return time.monotonic() - t0, resp.json(), attempts
+        except Exception:  # noqa: BLE001 — a refused connect is the expected pre-listen state
+            pass
+        time.sleep(_J04_POLL_INTERVAL_S)
+    raise AssertionError(f"backend on :{port} served no HTTP 200 within {timeout_s}s ({attempts} polls)")
+
+
+def _j04_kill_and_wait(proc: subprocess.Popen, sig: int = signal.SIGKILL) -> None:
+    """SIGKILL (a simulated crash — no chance to run any shutdown code) and reap, mirroring the
+    `spawned_backend` fixture's own teardown."""
+    if _pid_alive(proc.pid):
+        os.kill(proc.pid, sig)
+        deadline = time.monotonic() + 10.0
+        while _pid_alive(proc.pid) and time.monotonic() < deadline:
+            time.sleep(0.1)
+    try:
+        proc.wait(timeout=10)
+    except (ChildProcessError, subprocess.TimeoutExpired):
+        pass
+
+
+def test_j04_boot_serves_first_health_200_within_5s_on_warm_db():
+    """J-04 steps 1-2 — start the REAL `scripts/start-backend.sh` (prod mode, never `dev.sh`) against the
+    REAL warm committed DB and poll `GET /api/health` at 200 ms from process start: the FIRST HTTP 200
+    must arrive within 5 s (`docs/goal.md` Success Criteria), and that first payload must already carry
+    the honest readiness state + "history n/m" progress rather than a blank or fabricated one.
+
+    The clock starts before `Popen`, so the measurement INCLUDES the launch script's own bash startup,
+    ulimit/host-guard setup and `exec` — strictly more than "process start", never less."""
+    if not SCRIPT.exists():
+        pytest.skip(f"{SCRIPT} not found")
+    if not REAL_DB.exists():
+        pytest.skip(f"real committed DB not found at {REAL_DB} — J-04's budget is defined on the WARM DB")
+
+    env = dict(os.environ)
+    env["CHAIN_BACKEND_PORT"] = str(_J04_TEST_PORT)
+    env["CHAIN_FRONTEND_PORT"] = str(_J04_TEST_PORT + 1000)
+    t0 = time.monotonic()
+    proc = subprocess.Popen(
+        ["bash", str(SCRIPT)], cwd=str(REPO_ROOT), env=env,
+        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
+    )
+    try:
+        elapsed, payload, attempts = _j04_poll_until_first_200(_J04_TEST_PORT, t0, timeout_s=60.0)
+        print(
+            f"\n[J-04] warm-DB boot -> first HTTP 200 in {elapsed:.2f}s after {attempts} poll(s) "
+            f"(budget {_J04_BOOT_BUDGET_S}s); readiness={payload.get('readiness')!r} "
+            f"warmup={payload.get('warmup')}"
+        )
+        assert elapsed <= _J04_BOOT_BUDGET_S, (
+            f"J-04 step 2: first HTTP 200 took {elapsed:.2f}s, over the {_J04_BOOT_BUDGET_S}s budget "
+            f"recorded in reports/perf-budgets.md"
+        )
+        _assert_health_payload_is_honest(payload)
+    finally:
+        _j04_kill_and_wait(proc)
+
+
+def _j04_build_scratch_db(scratch_dir: Path) -> tuple[Path, Path]:
+    """Build a TINY scratch DB + a scratch `config.yaml` pointing at it, and return both paths.
+
+    Why not the real DB: J-04 step 6 needs a `running` job row to exist at the moment of the crash, and
+    writing job rows into the shared committed DB would leave synthetic runs in the operator's own Run
+    History. Why not an EMPTY DB: an empty `daily_prices` makes the boot's `load_seed` load the whole
+    158 MB committed seed (minutes). One `DailyPrice` row is the smallest thing that makes `load_seed`'s
+    price load a no-op (`_price_count` non-zero) while leaving every OTHER boot step — table creation,
+    reference/macro seed, the J-60 orphan sweep, `ensure_latest_snapshot`, the background warm-up — running
+    exactly as in production against the REAL committed `config.yaml` (only `database.url` is rewritten)."""
+    from datetime import date as date_cls
+
+    from sqlmodel import Session
+
+    from app.db import create_db_and_tables, make_engine
+    from app.models import DailyPrice
+
+    scratch_dir.mkdir(parents=True, exist_ok=True)
+    db_path = scratch_dir / "j04-scratch.db"
+    engine = make_engine(f"sqlite:///{db_path}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        session.add(DailyPrice(
+            symbol="SPY", date=date_cls(2024, 3, 4), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
+        ))
+        session.commit()
+    engine.dispose()
+
+    config_path = scratch_dir / "j04-config.yaml"
+    new_cfg_text, n = re.subn(
+        r'url:\s*"sqlite:///apps/backend/data/trendora\.db"',
+        f'url: "sqlite:///{db_path}"',
+        REAL_CONFIG.read_text(),
+        count=1,
+    )
+    assert n == 1, "expected exactly one database.url line to rewrite in the real config.yaml"
+    config_path.write_text(new_cfg_text)
+    return db_path, config_path
+
+
+def test_j04_crash_with_midflight_job_restarts_to_interrupted_row_with_last_progress(tmp_path):
+    """J-04 steps 3, 4 and 6, end to end through the real launch script — the sequence the browser-only
+    lane is not permitted to perform.
+
+    1. Boot a backend on a scratch DB; every polled 200 carries the honest readiness state + "history
+       n/m" progress (step 3's backend half).
+    2. Write a `running` `DataProviderRun` row with its last persisted progress WHILE that backend is
+       alive, and confirm the live instance serves it as `running` with a null `finished_at` — i.e. the
+       row genuinely is mid-flight at the moment of the kill, not fabricated afterwards.
+    3. SIGKILL the backend (simulated crash) and confirm `GET /api/health` no longer connects at all —
+       unreachable is categorically distinct from `initializing`, which answered HTTP 200 with a phase
+       (step 4's backend half).
+    4. Restart on the SAME DB and assert `GET /api/data`'s run history now shows that SAME row id as
+       `interrupted` with a non-null `finished_at` and its progress fields UNCHANGED — never a still-
+       `running` row with no living process, and never a row whose progress was overwritten (step 6).
+    """
+    if not SCRIPT.exists():
+        pytest.skip(f"{SCRIPT} not found")
+
+    from sqlmodel import Session
+
+    from app.db import make_engine
+    from app.models import DataProviderRun
+
+    db_path, config_path = _j04_build_scratch_db(tmp_path / "j04")
+    port = _J04_TEST_PORT + 1
+    env = dict(os.environ)
+    env["CHAIN_BACKEND_PORT"] = str(port)
+    env["CHAIN_FRONTEND_PORT"] = str(port + 1000)
+    env["TRENDORA_CONFIG"] = str(config_path)
+
+    # ---- 1. first boot -------------------------------------------------------------------------
+    t0 = time.monotonic()
+    proc1 = subprocess.Popen(
+        ["bash", str(SCRIPT)], cwd=str(REPO_ROOT), env=env,
+        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
+    )
+    try:
+        elapsed1, payload1, _ = _j04_poll_until_first_200(port, t0, timeout_s=60.0)
+        _assert_health_payload_is_honest(payload1)
+        print(
+            f"\n[J-04] boot 1 (scratch DB) -> first HTTP 200 in {elapsed1:.2f}s; "
+            f"readiness={payload1.get('readiness')!r} warmup={payload1.get('warmup')}"
+        )
+
+        # ---- 2. a job goes mid-flight, then the process dies under it --------------------------
+        # The engine is opened, used and disposed here so the row is committed (and its lock released)
+        # BEFORE the kill — the crash must find a genuinely persisted `running` row, exactly as a real
+        # job's own create-at-start record would be.
+        detail = (
+            '{"kind": "backfill", "start": "2012-01-03", "end": "2012-01-09", "dates_total": 5, '
+            '"dates_done": 2, "snapshots_created": 2, "summary": "mid-flight when the process died"}'
+        )
+        engine = make_engine(f"sqlite:///{db_path}")
+        with Session(engine) as session:
+            row = DataProviderRun(
+                provider="seed", started_at=_j04_utcnow(), status="running", message=detail,
+                job_id="j04-midflight-probe",
+            )
+            session.add(row)
+            session.commit()
+            session.refresh(row)
+            run_id = row.id
+        engine.dispose()
+
+        live = httpx.get(f"http://127.0.0.1:{port}/api/data", timeout=60.0).json()
+        before = _j04_run_by_id(live, run_id)
+        assert before["status"] == "running", f"the seeded job must be mid-flight before the kill: {before}"
+        assert before["finished_at"] is None, f"a running job carries no finished_at yet: {before}"
+        assert (before["dates_done"], before["dates_total"], before["snapshots_created"]) == (2, 5, 2), (
+            f"the live instance must serve the row's own persisted progress: {before}"
+        )
+
+        # ---- 3. simulated crash ----------------------------------------------------------------
+        _j04_kill_and_wait(proc1)
+        assert not _pid_alive(proc1.pid), "the simulated-crash process should be gone after SIGKILL"
+        with pytest.raises(httpx.HTTPError):
+            # unreachable: the socket is gone, so this raises rather than answering ANY status code —
+            # categorically different from the `initializing` HTTP 200 asserted above.
+            httpx.get(f"http://127.0.0.1:{port}/api/health", timeout=5.0)
+    finally:
+        _j04_kill_and_wait(proc1)
+
+    # ---- 4. restart: the mid-flight row must read back as interrupted, progress intact ----------
+    t1 = time.monotonic()
+    proc2 = subprocess.Popen(
+        ["bash", str(SCRIPT)], cwd=str(REPO_ROOT), env=env,
+        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
+    )
+    try:
+        elapsed2, payload2, _ = _j04_poll_until_first_200(port, t1, timeout_s=60.0)
+        _assert_health_payload_is_honest(payload2)
+        after = _j04_run_by_id(
+            httpx.get(f"http://127.0.0.1:{port}/api/data", timeout=60.0).json(), run_id
+        )
+        print(
+            f"[J-04] boot 2 after crash -> first HTTP 200 in {elapsed2:.2f}s; run {run_id} "
+            f"status={after['status']!r} finished_at={after['finished_at']!r} "
+            f"progress={after['dates_done']}/{after['dates_total']}"
+        )
+        assert after["status"] == "interrupted", (
+            f"J-04 step 6: a job that was mid-flight at the crash must read back as an explicit "
+            f"interrupted state after the restart, never a still-'running' row with no living process: "
+            f"{after}"
+        )
+        assert after["finished_at"] is not None, (
+            f"an interrupted run is terminal and must carry a finished_at: {after}"
+        )
+        assert (after["dates_done"], after["dates_total"], after["snapshots_created"]) == (2, 5, 2), (
+            f"J-04 step 6: the interrupted row must keep its LAST PERSISTED progress, not a reset or "
+            f"recomputed one: {after}"
+        )
+    finally:
+        _j04_kill_and_wait(proc2)
+
+
+def _j04_utcnow():
+    from datetime import datetime, timezone
+
+    return datetime.now(timezone.utc).replace(tzinfo=None)
+
+
+def _j04_run_by_id(data_payload: dict, run_id: int) -> dict:
+    """The one run-history row with `id == run_id` from `GET /api/data`'s `runs` list (the SAME persisted
+    `data_provider_runs` history the `/data` page's Run history panel reads)."""
+    runs = data_payload.get("runs") or []
+    matches = [r for r in runs if r.get("id") == run_id]
+    assert len(matches) == 1, f"expected exactly one run row with id={run_id}; got {runs}"
... [diff_bound] apps/backend/tests/test_start_backend_script.py: 1 more diff lines omitted — Read the file for full detail
```
