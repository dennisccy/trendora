# Goal Iteration 22 (J-11 Stage G) Audit Report

**Date:** 2026-08-27
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

Stage G's substantive repair claim holds. I re-derived the core evidence independently against the live
database (read-only) rather than accepting it: the 11 incident dates map 1:1 onto `ScannerRun` ids
3148–3158, every one stamped `53d2ffd10cdbf89e…`; `daily_prices` fingerprints byte-identical to the
certified post-AVB baseline; 24 manifests with zero rows for the 7 manifest-less incident dates; the five
explicit-delete caches at 0; `index_series_cache` stamp equal; mutation accounting reconciling with zero
unexplained table; and the boundary row preserved at `id=1, active=0`. I also mutation-tested all 14
verification functions myself — 12 were already caught by the suite, and the 2 that survived
(`verify_operational_isolation`, `confirm_no_network_capable_import`) I proved are genuinely falsifiable
and then closed with negative tests, so the suite is now 14/14.

The gaps are in the **completeness and honesty of the acceptance framing**, not in the repair. Two of the
18 named traps return an unconditional `ok: True` with no query behind them, and four trap citations point
at tests that assert something else — inside the `named_traps` category that gated the irrevocable
boundary write. And `FULLY REPAIRED` was declared without the repaired-state serving / J-01/J-02/J-03
replay that `docs/goal.md:1408` names as Stage G's own verification, because ruling item 4 forbade the boot
that would make it possible. None of these, corrected, changes a single structural repair fact — but the
terminal claim is broader than the evidence behind it, and that must be on the record.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): 2 of the 18 named traps pass unconditionally, inside the category that gated the boundary write**

`j11_stage_g_verify.py:1029` (formerly two `elif` branches at the same site). The traps
`j10_closed_before_j11_stage_c_ever_ran` and `this_iteration_is_stage_g_per_its_own_spec` resolved to a
bare `entry.update({"live_spot_check": check_name, "ok": True})` — no query, no comparison, no derived
value. `verify_named_traps` aggregates with `ok = bool(per_trap) and all(t["ok"] …) and len(per_trap) == 18`
(`:1074`), and `named_traps` is one of `stage_g_verdict`'s twelve gating categories (`:1333`). So two
constituents of the gate that authorized `finalize_stage_g`'s irrevocable `active: 1 → 0` write could never
fail. This is the same defect class as the reviewer's own CRITICAL this iteration, and as iteration 20's —
its third appearance.

Worse than the unfailability itself: both were emitted under the **`live_spot_check`** key. In
`runs/goal-market-compass-iter-22/j11-stage-g-verify-named-traps.json` they appear as
`{"live_spot_check": …, "ok": true}` with none of the `observed` / `observed_date_count` /
`boundary_recheck_ok` payload the four genuine probes carry — so the evidence artifact presents an
assertion as a measurement. The handoff then generalised all six as "a fresh live spot-check".

The unfailability is not fixable by code: both are facts about the iteration history, not rows the module
can read. **Fix applied:** the two are hoisted into a named `_PROCEDURAL_ONLY_TRAP_CHECKS` table
(`:858`) and now emit `procedural_fact` / `live_check_performed: False` /
`evidence_class: "procedural_not_live_verifiable"` / a `rationale` string, and no longer carry the
`live_spot_check` key at all. **The `ok` boolean is deliberately unchanged** — relabelling must not
silently restate a completed live gate's verdict. Locked by a new test
(`test_j11_stage_g_verify.py:713`) that pins both the labelling and the count at exactly two, so a third
unconditional pass cannot be added without failing.

**B2 — IMPORTANT (gap): four trap citations point at tests that assert a different property, and the resolver cannot detect it**

`_test_function_exists` (`j11_stage_g_verify.py:831`) parses the cited test file's AST and returns True if
*a function of that name exists*. It never runs the test and never inspects its assertions. So a citation
aimed at the wrong test passes silently. I read all four of these cited tests directly:

| Trap | Cited test | What the test actually asserts |
|---|---|---|
| `schema_identity_retry` 7 — "a simulated failure **after a subset of dates are rebuilt** leaves the attempt incomplete" | `j11_stage_g_verify.py:914` → `test_j11_stage_d_execute.py:406` | Seeds a pre-existing run at `LOOP_DATES[0]` and asserts `calls == []` — `run_scan` was **never called**, i.e. **zero** dates rebuilt. The exact opposite scenario. |
| `schema_identity_retry` 9 — "immutable manifests and audit evidence survive **a retry** byte-unchanged" | `:925` → `test_j11_stage_c_preflight.py:220` | Asserts the preflight gate flags drift in `daily_prices` fingerprint, `data_provider_runs` count and `watchlist` count. Touches **no manifest**, no audit evidence, and involves **no retry**. |
| `j10_j11_sequencing` 1 — "completing remaining J-10 raw rows does not falsely imply the 2026-08-11/12 `ScannerRun`s were recomputed" | `:937` → `test_j10_recovery.py:604` | A convention-check *evidence-persistence* test: asserts an evidence JSON is written on a stop path. Nothing about `ScannerRun`s, create-once, or those two dates. |
| `j10_j11_sequencing` 3 — "J-11 **cannot start** before J-10 raw recovery reaches terminal state" | `:948` → `test_j11_stage_c_preflight.py:140` | A self-diff of an unchanged DB asserting the gate **PASSES**. Wrong polarity: a pass-case cannot prove a "cannot start" negative. The stop-case sibling sits 10 lines below at `:150` and was not cited. |

**Not fixed, deliberately.** Choosing which existing test evidences which owner-authored trap is an
evidence-mapping decision, and a second wrong guess would be worse than a named, visible gap. Recorded in
the module's own trap-table header (`:843-857`) so the next lane cannot miss it. Mitigating: the dev and
the reviewer each executed all 7 citation files out-of-band (238 passed, 1 failed — the failure is
`test_manifest_invariants.py::test_tc15_no_update_statement_targets_next_session_manifests`, a broad static
heuristic that also flags untouched files, so it is pre-existing), so the cited *functions* are known
green — that is simply not evidence the production check gathers.

**B3 — IMPORTANT (gap): `FULLY REPAIRED` was declared without the repaired-state serving/replay verification goal.md assigns to Stage G**

`docs/goal.md:1408` defines the stage sequence as "… F (dependency-aware cache handling) → **G (final
serving/replay verification)**", and `:1978-1985` gates on Stage G the assertions that "rebuilt
`ScannerRun`s serve the current complete raw basis; J-01/J-02/J-03 replay clean; Market Compass historical
serving is internally consistent". None of that was performed. Trap `j10_j11_sequencing` 5 — "the final
repaired-state J-01/J-02/J-03 replay belongs to J-11 Stage G" — was resolved `ok: True` on the reasoning
"this module IS the Stage G verification module". I grepped the module: it contains no `GET /api/compass`
check, no replay, and no historical-serving consistency check of any kind.

This is a genuine contradiction inside `docs/goal.md`, not a developer defect: ruling item 4 (`:1793-1800`)
holds that through Stage G "browser QA remains **OFF**; replay remains **OFF**; … ordinary API requests
remain **forbidden**", and forbids deactivating the boundary "before Stage G has passed all required
verification". Stage G cannot perform a verification that is forbidden until Stage G passes. The phase spec
resolved it explicitly and defensibly (DoD line 470: J-01/J-04/J-10 "**not** re-verified via browser QA or
replay this iteration (impossible under maintenance isolation)"; instead, zero-diff on `scoring.py`,
`compass.py`, `j10_recovery.py` — which I confirmed directly, all three empty against both `HEAD` and the
pre-iteration commit `5768c930`).

What was wrong was resolving it **silently** with a passing trap rather than surfacing it. Now labelled
ASSERTED-NOT-VERIFIED (fix B1). The substantive consequence: `FULLY REPAIRED` rests on
structural/database-level evidence, which is strong, and **not** on end-to-end serving evidence. With the
boundary now inactive, that verification is finally possible and is the natural first act of the next,
owner-gated iteration.

**B4 — IMPORTANT (fixed): the dev handoff misattributed ruling item 5's second named gap, and the error propagated**

`docs/goal.md:1802-1805` names ruling item 5's two deferred gaps as (1) "`scanner.resolve_run()` for an
explicit `?as_of=` request" and (2) "ordinary Data Manager persistence paths capable of calling
`run_scan()` or `persist_run_payload()`" — i.e. `data_manager.py:3762 _do_backfill._persist`. The handoff's
Known Issues instead named them as `scanner.py::resolve_run` and `compass.py::get_or_create_manifest`,
substituting a path that ruling item 5 does not name, and dropping the real second gap from the prose
entirely. The **production module gets this right** — `WRITE_PATH_CLASSIFICATION`
(`j11_stage_g_verify.py:199-215`) records `_do_backfill._persist` as "ruling item 5's SECOND named deferred
gap" and `app/api/compass.py::compass` as "the SAME species … but not itself named by ruling item 5's
text". The handoff contradicted its own module, and its own Files Changed section. The error propagated:
the QA report's "Deferred Write-Path Gaps" list and the implementation summary's "two specific, narrow
situations (both requiring an unusual manual URL request)" both omit `_do_backfill._persist`, which is an
ingest-job path, not a URL request. Ruling item 5 says these gaps "must not be **erased**". **Fix applied:**
the handoff now carries the corrected, fully enumerated 7-item deferred list with the ruling attribution
right, and flags the downstream propagation.

**B5 — IMPORTANT (fixed): operational isolation is a two-port probe presented as the whole claim**

The spec's IN SCOPE bullet asks `verify_operational_isolation()` to "read the engine's own dispatch-refusal
log for this iteration and confirm application-service boot, browser-qa-agent, and the replay lane were
each refused/never dispatched". The implementation (`j11_stage_g_verify.py:1084`) does a point-in-time TCP
`connect_ex` against ports 8000/3000 and nothing else. The module's docstring is honest about this ("This
module has no access to the goal-mode engine's own dispatch-refusal log"); the handoff dropped that
disclaimer and presented the probe flatly as "Operational isolation", producing a circular chain — the
module defers the browser-QA/replay half to the handoff's attestation, and the handoff presents the
module's `operational_isolation: true` as the evidence.

**I supplied the missing evidence independently.** The engine's own marker at
`runs/goal-session-market-compass/iter-22/maintenance-isolation-refusals` records
`2026-08-27T13:25:03Z operation=browser-qa-phase detail=browser QA + deterministic replay lane` — both
lanes refused by contract — plus `2026-08-27T08:36:29Z operation=async-showcase-join`. With
`status.json`'s `browser_checks_run: false` and nothing listening on 8000/3000 (I re-probed), **the
isolation claim holds on real evidence**; it was simply not the evidence this module gathered. **Fix
applied:** the handoff now states the probe's true scope and cites the refusal log.

**B6 — OBSERVATION: one conjunct of the write-path check is true by construction**

`j11_stage_g_verify.py:1187`: `guarded_still_open_and_deferred_and_authorized_only = all(c["classification"]
in ("guarded", "stage_d_authorized_write", "still_open_and_deferred") for c in classified)`. Every entry in
`classified` was drawn from `WRITE_PATH_CLASSIFICATION`, whose values are exactly those three strings — so
this can never be False. Harmless: the other two conjuncts (`not unclassified`, `not stale_table_entries`)
carry the real weight and are genuinely failable in both directions, and the mutation run caught this
function. Not fixed — removing dead-but-defensive logic is not worth touching a terminal-gate module for.

**B7 — OBSERVATION: population (b)'s evidence naming invites a misreading**

`j11-stage-g-verify-forward-returns.json` records `recorded_population_b_pre_total: 16614` while the spec's
binding fact says "population (b) = 0 is the correct answer". These are not in conflict — 16,614 is the
count of forward-return rows that *exist* on retained runs measured on incident dates, and the check that
matters is `population_b_delta_from_pre_stage_e_baseline == 0` (zero holes needed filling, zero rows lost),
backed by `population_b_never_decreased`. I traced this through
`j11_stage_e_execute.live_verify_three_populations:375-386` to be sure. The check is genuinely falsifiable
and has a dedicated negative test. Only the field naming reads as if it contradicts the spec.

**B8 — OBSERVATION: Stage G is not idempotent, in a fail-closed direction**

With the `membership_timeline_cache` row now deleted, a re-run's `verify_membership_timeline_preserved_row`
(`:669`) returns `row_present: False, disposition: "explicit_delete", ok: True` ("vacuously fine"), but
`confirm_membership_timeline_deletion_matches_verification` (`:779`) then computes
`matches = deleted and row_confirmed_absent` = `False and …` = False, failing the whole verdict. An internal
inconsistency introduced by the fix pass, but it errs strictly toward refusing to pass, and a re-run is
already blocked twice over (the evidence-dir collision guard, and the preflight's boundary-ACTIVE
requirement). Not fixed.

### Frontend Findings

None — `Frontend Present: no`, zero UI surface this iteration, no frontend file touched. Correct.

### Test Findings

**T1 — IMPORTANT (fixed): 2 of 14 verification functions could be hardwired to always-pass with the whole suite still green**

I ran my own mutation audit: for each of the 14 functions that produce an `ok` / `proceed` / `clean`
boolean, I replaced that boolean with a literal `True` and re-ran both Stage G suites. **12 mutants were
caught.** Two survived:

| Mutated | Result before fix |
|---|---|
| `verify_operational_isolation.ok` → `True` | `71 passed` — whole suite green |
| `confirm_no_network_capable_import.clean` → `True` | `71 passed` — whole suite green |

Both feed the gate (`operational_isolation` is a category of its own; the network scan feeds
`verify_raw_inputs.ok`, which carries AG-9 — a *critical* anti-goal). The suite's only coverage of each was
a pass-case assertion, so no test could distinguish the real function from an unconditional pass. I first
confirmed the **functions themselves are falsifiable** — binding a real loopback listener made
`verify_operational_isolation` report `ok: False`, and a file importing `requests`/`urllib` made
`confirm_no_network_capable_import` report `clean: False, network_hits: ['requests','urllib']` — so this was
a test gap, not a logic tautology. **Fix applied:** two negative tests added
(`test_j11_stage_g_verify.py:164` and `:931`, the latter parametrized over backend/frontend). Re-running the
same two mutations after the fix: **both now CAUGHT** (`2 failed, 67 passed` and `1 failed, 68 passed`).
Mutation coverage is now 14/14.

**T2 — OBSERVATION: a stale test name**

`test_membership_timeline_no_stored_row_is_a_vacuous_pass_no_write` still says "vacuous pass", but the
fix pass made that scenario a verdict FAIL (see B8). The test's assertions are correct; only the name is now
misleading.

---

## 3. Domain Assessment

The domain logic is sound and, where it matters most, better than its handoff describes.

**The one code edit is exactly right.** `data_manager.py:1554` wraps the `coverage_from_storage` self-heal
INSERT in `j11_preboot_guard.evaluate_boundary_for_date_fail_closed`, which I read end-to-end
(`j11_preboot_guard.py:273-298`): it genuinely fails closed, returning `blocked: True, ambiguous: True` on
any exception rather than treating an unevaluable boundary as clear. The diff against the pre-iteration
commit is exactly two hunks — one import, one `if not boundary["blocked"]:` wrap — with zero change to
`_cascade_targets`, `remove_price_data`, or anything else in a ~4,700-line file. `scanner.py`,
`app/api/compass.py`, `app/engine/compass.py`, `scoring.py` and `j10_recovery.py` are byte-identical to both
`HEAD` and `5768c930`. TC-16/17/18 cover blocked / ordinary / already-persisted-read, and `test_api_data.py`
(55 tests, which I ran) passes unchanged.

**The B2 cache-staleness finding is real, and I corroborated its causal story rather than accepting it.**
The check recomputed 2026-08-10's membership-timeline `exits` as `['MARA']` against a stored `['AMSC','MARA']`.
AMSC has continuous `daily_prices` rows across 2026-08-10/11/12 — so during the window when 08-11 and 08-12
were deleted (the 2026-08-12 frontier data-loss incident), AMSC would correctly have looked like an exit,
and after J-10 recovered those rows it no longer is. The stored value is exactly the pre-repair-era artifact
the check was designed to catch, and Stage F's preserve decision — made on a performance/branch-selection
proof that never examined content — was wrong on content. Iteration 21's auditor was right to flag it, and
turning that "consider" into a required check is the strongest thing this iteration did.

**The order-of-operations residue is genuinely closed, and I closed it independently rather than trusting
the reviewer.** The live run used the pre-fix ordering — confirmed by the absence of
`j11-stage-g-verify-membership-timeline-deletion-check.json` from the 26 evidence files, and by the
timestamps: check `.384648` → verdict `.653520` → delete `.659364` → finalize `.666663`. So the boundary was
deactivated on a verdict computed before the corrective delete. I replayed the **corrected**
`stage_g_verdict` over the original run's own persisted per-category evidence, feeding
`confirm_membership_timeline_deletion_matches_verification` the recorded `deleted: true` plus a **fresh live
read-only `COUNT(*)` = 0** I took myself: `full_pass: true`, `failing_categories: []`. Negative control —
the same replay with `deleted: False, count: 1` — returns `full_pass: False,
['membership_timeline_reconciled']`. The corrected gate would have reconciled this exact historical write
the same way, and it is genuinely failable. A full live re-run is infeasible in both directions (the CLI
refuses a populated evidence dir; the preflight requires the boundary ACTIVE), so this is the strongest
proof obtainable without a new owner authorization — and it is sufficient.

**Where the domain reasoning is weakest** is the trap layer (B1–B3): an 18-item acceptance list where 12
items are name-existence checks, 4 of those 12 point at the wrong test, and 2 items are assertions. That
layer contributes far less assurance than its `named_traps: true` suggests. It does not undermine the
repair — the repair is proven by the raw-input fingerprint, the id/identity mapping, the manifest dump
diff, the cache counts and the cross-iteration mutation accounting, all of which are real, live and
falsifiable — but it means the acceptance gate is narrower than 18/18 implies.

Resource discipline held: `VmPeak` 1,010.5 MB against an 8,192 MB cap; my own work was read-only `sqlite3`
plus fixture-scoped pytest; the 8.4 GB database was never opened for write, copied or moved.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_j11_stage_g_verify.py:931` | Added `test_operational_isolation_FAILS_when_a_real_listener_occupies_a_probed_port` (parametrized backend/frontend) — binds a real loopback listener and asserts `ok is False`, then asserts it goes clean again. Kills the surviving mutant. |
| 2 | Important | `apps/backend/tests/test_j11_stage_g_verify.py:164` | Added `test_network_capable_import_check_FAILS_on_a_file_that_imports_a_network_library` — AG-9's self-check now has a negative case and a per-file (not global) assertion. Kills the surviving mutant. |
| 3 | Important | `apps/backend/app/engine/j11_stage_g_verify.py:858, :1029` | Hoisted the two evidence-free traps into `_PROCEDURAL_ONLY_TRAP_CHECKS`; they now emit `procedural_fact` / `live_check_performed: False` / `evidence_class` / `rationale` and no longer carry the `live_spot_check` key. **Zero verdict-logic change** — every `ok =` / `proceed =` / `full_pass =` / `"clean":` line is byte-identical to the pre-audit state (verified by diff). |
| 4 | Important | `apps/backend/tests/test_j11_stage_g_verify.py:713` | Added `test_named_traps_procedural_entries_are_labelled_asserted_not_verified` — pins the labelling, pins the procedural count at exactly 2 and the live-probe count at exactly 4, and asserts every live probe carries observed payload beyond a bare `ok`. |
| 5 | Important | `apps/backend/app/engine/j11_stage_g_verify.py:843-857` | Corrected the trap-table header's false "mirror … verbatim" claim (the descriptions are paraphrases) and recorded, in-source, that citation resolution is existence-only plus the four verified mis-citations from B2. |
| 6 | Important | `docs/handoffs/…-iter-22-dev.md` (named traps) | Replaced the false blanket claim with the honest 12-citation / 4-live-probe / 2-procedural taxonomy. |
| 7 | Important | `docs/handoffs/…-iter-22-dev.md` (operational isolation) | Stated the port probe's true scope, restored the module's own "no access to the dispatch-refusal log" disclaimer, and cited the engine refusal-log evidence I located. |
| 8 | Important | `docs/handoffs/…-iter-22-dev.md` (Known Issues) | Corrected ruling item 5's second named gap to `data_manager.py:3762 _do_backfill._persist`, enumerated all 7 deferred call sites, and flagged the propagation into the QA report and implementation summary. |
| 9 | Observation | `docs/handoffs/…-iter-22-dev.md:125, :132` | "full suite green again" → "targeted suite green again" — it contradicted the same document's own "the full backend suite was NOT run" policy statement 130 lines later. |

**Post-fix verification (commands run and results):**

- `pytest tests/test_j11_stage_g_verify.py tests/test_j11_stage_g_verify_cli_script.py -q` → **75 passed
  in 2.87s** (was 71; +4 from fixes 1, 2, 4).
- Re-mutation of the two previously-surviving checks after the fix → `verify_operational_isolation.ok = True`
  ⇒ **2 failed, 67 passed** (CAUGHT); `confirm_no_network_capable_import` ⇒ `clean: True`
  ⇒ **1 failed, 68 passed** (CAUGHT). Module restored byte-identical (md5 verified) after each.
- `pytest tests/test_j11_stage_g_verify.py tests/test_j11_stage_g_verify_cli_script.py tests/test_api_data.py -q`
  → **130 passed in 9.72s** — no regression in the guard edit's own regression file.
- `python scripts/run_j11_stage_g_verify.py` (no flags) → refuses, exit 2, zero DB interaction. Gate intact.
- Diff review of my own changes: 48 added / 18 removed lines in the module, all inside the trap-table
  comment block and the two procedural branches; `diff` of every `ok =` / `proceed =` / `full_pass =` /
  `"clean":` line against the pre-audit snapshot returns **identical** — no boolean I touched.
- **No database write of any kind was made by this audit.** All live reads via
  `sqlite3 "file:…?mode=ro"`. The boundary row is untouched: `1|j11-incident-recovery|0|…|2026-08-27 09:27:08.662797`.

---

## 5. Recommended Next Step

**Proceed.** J-11's incident repair is verified to the depth the maintenance-isolation contract permits, and
the boundary deactivation stands. Carry these forward, in priority order:

1. **Close B3 first, as the next iteration's opening act.** The repaired-state `GET /api/compass` serving
   and the J-01/J-02/J-03 replay that `docs/goal.md:1408` assigns to Stage G were never performed, because
   ruling item 4 forbade the boot until Stage G passed — a circular constraint goal.md never resolves. That
   boot is now permitted and is an **owner decision**. Until it happens, `FULLY REPAIRED` should be read as
   *"the database-level incident state is proven clean"*, not *"the product has been observed serving
   correctly on the repaired data"*. Recommend the owner authorize a supervised boot and replay as
   iteration 23's first task, and record its outcome against this gap by name.
2. **Re-point the four mis-cited traps (B2)** — `schema_identity_retry` 7 and 9, `j10_j11_sequencing` 1 and 3.
   Better still, make citation resolution mean something: `verify_named_traps` currently proves only that a
   function name exists. A future pass should either execute the cited tests or drop the word "passing" from
   the contract.
3. **The post-J-11 write-path hardening pass is now due**, and it is a family of **seven**, not two:
   `scanner.py::resolve_run` and `data_manager.py:3762 _do_backfill._persist` (ruling item 5's actual two),
   plus `app/api/compass.py::compass`, `scanner.py::_bootstrap`, `data_manager.refresh_coverage_snapshot`,
   `_persist_per_date_coverage_snapshots` and `_refresh_ingest_aggregates`. With the boundary inactive all
   seven are unguarded in fact — benign today (there is no quarantine to enforce) but the standing reason a
   future boundary would not hold. Treat this iteration's one closed gap as the template.
4. **Housekeeping before scoring:** the fix pass and this audit are tracked-but-uncommitted
   (`j11_stage_g_verify.py`, `run_j11_stage_g_verify.py`, `test_j11_stage_g_verify.py`, the dev handoff).
   Iterations 19–21 were each flagged for this at scoring time; commit them with the iteration.
5. **Not blocking:** the 10 pre-existing `test_data_manager.py` failures (warm loops and manifest-export
   collision, confirmed unrelated by the dev's stash-revert and untouched by this iteration) and
   `test_manifest_invariants.py::test_tc15_…`'s static-heuristic false positive remain open for a future
   maintenance pass.
