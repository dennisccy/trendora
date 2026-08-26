# goal-market-compass-iter-19 Audit Report

**Date:** 2026-08-26
**Auditor:** Hard audit pass — skeptical, evidence-based
**Scope:** J-11 Stage D — the live, effectively irreversible canonical regeneration of the eleven incident dates
**Isolation:** maintenance isolation honoured throughout this audit — no service boot, no HTTP request, no
browser lane, no live-database write. All database verification used
`sqlite3 "file:/home/dennis-chan/Git/trendora/apps/backend/data/trendora.db?mode=ro"`.

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

Stage D genuinely did what it claims. I re-derived the outcome from the live database rather than from any
handoff, review, or QA claim: all eleven `INCIDENT_DATES` carry exactly one new `ScannerRun` (ids 3148–3158),
every one stamped with the same frozen identity, each with real `ScannerResult`/`SectorScoreRow`/`ThemeScoreRow`
children; `next_session_manifests` still holds exactly 24 rows across the same 4 incident dates; the 34
iteration-10-era and 3,083 NULL-stamped runs are untouched; `daily_prices` is byte-identical at 3,310,374 rows;
the maintenance boundary is still a single `active=1` row; and no service was ever listening on 8000/3000.

One IMPORTANT gap remains and cannot be closed in-lane: the frozen execution identity **equals** the
iteration-14 and iteration-16/17/18 readiness identities, which the owner ruling's item 2 names as values not to
be reused, and which DEFINITION OF DONE bullet 2 requires to be *distinct*. The mathematical explanation offered
by dev/reviewer/QA is correct and I verified it independently — but the explanation stops one step short of the
consequence that actually matters, and the residual risk lands on Stage G, not on this iteration. That is an
owner decision, not something an auditor should paper over or "fix" by editing hashed source.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap — owner decision required): the frozen Stage D execution identity equals two of the three historical identities the owner ruling forbids reusing, and cannot serve as a membership marker for the attempt.**

The evidence artifact is admirably honest about the fact —
`runs/goal-market-compass-iter-19/j11-stage-d-execute-historical-identity-comparison.json` records
`"any_historical_match": true` with `iteration_14` and `iteration_16_17_18_readiness` both `"matches_fresh": true`.
The issue is not concealment; it is that no artifact confronts the requirement the equality collides with.

*What the contract says.* The owner ruling in `docs/goal.md` ("OWNER RULING — J-11 Stage D through Stage G
recovery execution AUTHORIZED", item 2, commit `5fe72f5c`) states verbatim: "Do **not** reuse: the iteration-10
identity; the iteration-14 identity; the iteration-16/17/18 readiness identity; or any historical frozen
identity." The phase spec's DEFINITION OF DONE bullet 2
(`docs/phases/goal-market-compass-iter-19.md:233-236`) requires the identity be "proven (by independent
recomputation, never by copying a value) **distinct from every historical identity already on disk**".
The spec's own TC-3 (line 300-305) contradicts both, requiring only that it be "honestly compared (equal-or-not,
stated either way)". Dev, reviewer and QA all reasoned against TC-3, the weakest of the three, and never quoted
the other two.

*Verified independently, not accepted from the handoff.* `compute_engine_identity`
(`apps/backend/app/engine/engine_identity.py:44-66`) hashes exactly `config.yaml`'s
`provenance.engine_files` (`compass.py`, `session_delta.py`, `engine_identity.py`) plus `provenance.config_keys`
(`compass.selection`, `compass.delta`, `compass.manifest`) — I read the config block directly.
`git log -- apps/backend/app/engine/{compass,session_delta,engine_identity}.py` → last touch `a9e651c4`
(iteration 12); `git log -- config.yaml` → last touch iteration 4. The equality is therefore **mathematically
forced**, not a copied value: the procedural half of the requirement was met correctly
(`j11_stage_d_execute.py:294-306` calls `jsd.freeze_stage_d_attempt_identity` directly, never the
`readiness_time_only` wrapper, and `j11-stage-d-execute-check-a.json` shows an independent recomputation
matching byte-for-byte). Read as a *value* requirement, ruling item 2 is **unsatisfiable** without editing one
of those three files or three config keys — which the same ruling's item 6 forbids ("Do not: change scoring
formulas; add recovery-specific formulas; change thresholds"). So the procedural reading is the only coherent
one, and it was executed correctly.

*The consequence nobody stated.* `scanner.persist_run_payload` (`apps/backend/app/engine/scanner.py:118`)
stamps **every** newly created `ScannerRun` with `engine_identity.compute_engine_identity(cfg)` — the same
`53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55`. And `scanner.resolve_run`
(`apps/backend/app/engine/scanner.py:338-347`) reaches `run_scan` with no boundary consultation — the pre-boot
guard is wired only into `warmup.py:107`/`warmup.py:361` and `forward_testing.py:551`, never into `scanner.py`
(confirmed by grep across `apps/backend/app/`). So the first `?as_of=` request that resolves to a date with a
bar but no stored run — 2026-08-04, 2026-08-06 and 2026-08-07 all qualify — mints a twelfth `ScannerRun`
carrying the identical identity. The attempt identity is not a marker for this attempt; it is simply "the
current engine identity", which every future ordinary run will also carry. Ruling item 9 makes Stage G's
acceptance rest on "all eleven rebuilt runs carry the single fresh attempt identity" — a criterion that
`engine_identity` alone can no longer establish membership for.

*What is genuinely true today* (verified live): the eleven runs **are** unambiguous right now. The identity
breakdown across all 3,128 `scanner_runs` is `NULL` 3,083 / `6261ca17…` 34 / `53d2ffd1…` 11 — no other row on
disk carries the fresh value. Nothing is currently corrupted or mislabelled.

*Not fixed here, deliberately.* Every candidate fix is forbidden: changing the identity requires editing
`compass.py`/config (banned by ruling item 6, by the plan's Guardrails, and it is exactly the "manufacture a
different hash" anti-pattern `j11_stage_d_execute.py`'s own docstring warns against, lines 46-61), and
re-stamping rows requires a live write (banned by the isolation contract). Reported for the owner instead.
Zero-cost mitigation available: see §5.

*Severity note:* I was genuinely unsure between GAP and IMPORTANT and chose the higher one — a DEFINITION OF
DONE bullet is marked complete whose literal condition is unmet, and the shortfall silently weakens a later
acceptance gate.

**B2 — GAP (observation, explicitly deferred by this spec): the mutation-accounting sweep cannot detect a same-rowid in-place UPDATE outside the five specifically-dumped populations.**

`j11_maintenance.capture_full_table_sweep` (`apps/backend/app/engine/j11_maintenance.py:231-283`) fingerprints
only `COUNT(*), MIN(rowid), MAX(rowid), SUM(rowid)` per table — its own docstring says so plainly. The nominated
"PRIMARY instrument", the whole-file mtime/size/WAL bracket, proves only *that* the file changed, which it
necessarily did (`j11-stage-d-execute-mutation-accounting.json`: main file unchanged at 8,365,871,104 bytes,
`-wal` 0 → 5,475,512 bytes, main mtime 2026-08-25T23:49:26Z → 2026-08-26T10:53:02Z). It cannot localise *which*
table changed. Genuine content proof exists only for `next_session_manifests` and `maintenance_boundaries`
(full `migration.dump_table` + `diff_dumps`), the legacy/NULL `ScannerRun` population (full per-row fingerprint
over 3,117 rows), `daily_prices` (row_count + id_sum + min/max date + ohlcv_sum) and
`data_provider_runs`/`watchlist` (count + id list). Everything else — including `forward_returns` and the cache
tables — rests on the rowid sweep alone.

This is exactly the item iteration 18's recommendation raised ("fixing the mutation-accounting proof method to a
true content hash") and that this spec's OUT OF SCOPE section deliberately defers. Not a regression, and the
DoD bullet was implemented precisely as written. I closed most of the residual risk by code trace rather than by
argument: `scanner.compute_run_payload` (`scanner.py:57-81`) is documented and verified write-free, and its
entire callee set — `regime.py`, `sectors.py`, `themes.py`, `scoring.py`, `setups.py`, `indicators.py`,
`patterns.py`, `universe_resolver`, `universe_screen`, `normalize`, `buckets`, `labels`, `prices` — contains
zero `session.add/commit/delete/merge` (grep across `apps/backend/app/engine/*.py`; the only writing modules in
the package are `compass`, `data_manager`, `indexes`, `j11_preboot_guard`, `market_phase`, `scanner`,
`forward_testing`, `j11_avb_correction`, `research`, none of which is reachable from `compute_run_payload`).
`persist_run_payload` writes exactly `ScannerRun` plus the three child models. No Stage-D-reachable path can
UPDATE another table.

**B3 — GAP: the live write loop ran the bar cache's LAZY path over the full live bar table, in a bare Python process outside the host-cap launch wrapper.**

`execute_stage_d_regeneration` (`apps/backend/app/engine/j11_stage_d_execute.py:405`) wraps the write loop in
`prices.bar_cache(session)`. This was not in the plan, so I checked the justification rather than accepting it:
it holds. `scanner._bootstrap` (`apps/backend/app/engine/scanner.py:259`) already wraps a multi-date `run_scan`
loop in exactly this context, and the cache stores each symbol's **full** series and slices `date <= D` per call
(`prices.bars_asof`, ~line 613), so the no-lookahead boundary is preserved and values are byte-identical — AG-5
is safe. Stage D writes no price bars, so the "a fetch job that ADDS bars must run OUTSIDE any cache context"
caveat in `prices.py` does not apply.

The residual risk is memory, not correctness. The code uses `bar_cache`, not `prefilled_bar_cache`, so symbols
load through the lazy per-symbol `list[Bar]` path — which `prices.py`'s own iter-43 note documents as "~3.3x
more bytes/row" than the `_SymbolColumns` shape that itself holds "~1.1 GB" resident at this data basis. Roughly
540 pool symbols out of the 591 in `daily_prices` (3,310,374 rows) were loaded and held for the whole eleven-date
attempt, in a process launched without `scripts/start-backend.sh`'s `ulimit -v` cap, on the host with the
documented 2026-08-20 freeze. No cap was removed or weakened, so this is not an AG-10 violation, and it worked
(~102 s wall). But Stage E touches `forward_returns` (6,797,728 rows) and deserves either
`prefilled_bar_cache(session, expected_symbols=pool_symbols)` or a capped launcher.

**B4 — OBSERVATION: Check (B)/(C) vacuously pass for any date outside `INCIDENT_DATES`.**

`j11_stage_d.check_identity_before_date` / `check_identity_after_persist` return `in_scope: False, ok: True` for
an off-set date — required behaviour per spec TC-9, pre-existing, and `j11_stage_d.py` is byte-unchanged this
iteration. Structurally this means `execute_stage_d_regeneration` would call `scanner.run_scan` with **no**
identity verification at all if ever handed a different date tuple; `incident_dates` is a caller-supplied
parameter and the only call site (`run_j11_stage_d_execute.py:309`) passes `INCIDENT_DATES`.

I verified this escape hatch was **not** exercised in the live run rather than assuming it: all eleven per-date
records in `j11-stage-d-execute-regeneration.json` carry `check_b.in_scope: true` **and** `check_c.in_scope:
true`, with `ok: true` on both. Every check was a real comparison. Worth a hard assertion if Stage E/F reuse the
loop shape.

### Frontend Findings

None applicable. `Frontend Present: no`; no frontend file appears in `git status --porcelain -uall`; no UI
surface, route or component changed.

### Test Findings

**T1 — OBSERVATION: the only test that runs the real AVB pipeline asserts a tautology.**
`test_run_fresh_avb_reclassification_end_to_end_smoke_on_small_fixture`
(`apps/backend/tests/test_j11_stage_d_execute.py:229`) asserts
`result["classification"]["classification"] in ("AVB-A","AVB-B","AVB-C","AVB-D")` — the classifier's entire
codomain, so it can never fail. The docstring is honest about delegating label correctness to
`test_j11_avb_diagnostic.py`, the exact-`AVB-A` execution gate is separately and tightly covered by the
parametrised `test_gate_refuses_unless_every_condition_holds` (line 285-297, with `AVB-B` and `AVB-C` proving
refusal), and the same test does carry two genuinely tight assertions (`bridge_factor ==
approx(2.7930001225759193)` and an exact `volume_override_by_date` key set). Acceptable delegation, but the
composition's own classification output is unasserted.

**T2 — OBSERVATION: TC-2's "persists the exact blocking reason" is only half-asserted.**
`test_execution_gate_not_proceed_never_calls_regeneration`
(`apps/backend/tests/test_j11_stage_d_execute_cli_script.py:236-249`) asserts `outcome["reason"] ==
"execution_gate_did_not_proceed"` and that `freeze`/`regen` were never called, but never asserts the specific
blocker it seeded (`avb_classification_not_avb_a:AVB-B`) survives into the persisted artifact — even though the
real (unmocked) `stage_d_execution_outcome` copies `blocking_reasons` through. One extra assertion closes it.

**T3 — OBSERVATION: a leftover comment inside a test helper describes an approach that was abandoned.**
`jsde_bad_payload()` (`apps/backend/tests/test_j11_stage_d_execute.py:459-464`) carries a comment reasoning
toward "instead monkeypatch check_identity_after_persist's underlying comparison…", while the mechanism actually
used is `_stub_then_corrupt`. The test itself is correct and its assertions are exact
(`calls == [LOOP_DATES[0]]` proves the second date was never attempted).

**T4 — OBSERVATION: the fixture mutation-accounting test uses a different capture shape than production.**
`test_mutation_accounting_all_pass_when_only_stage_d_write_tables_changed` (lines 554-555) builds
`pre_provider_runs={"count": jm._count(session, DataProviderRun)}`, while production
(`run_j11_stage_d_execute.py:304-305`) passes `jsc.small_table_id_snapshot`, which returns `{"count", "ids"}`.
Both are compared with `==`, so the check's logic is exercised — but not against the payload shape the live run
actually used.

*Overall test quality: good.* Assertions are predominantly tight and behavioural rather than loose: exact
`stop_reason` strings, `calls == []` proving `run_scan` was never reached on a stop path, full-dict equality for
the TC-9 vacuous-pass shape, exact `reason` strings for all four failure branches of
`stage_d_execution_outcome`, and a static import-absence proof that the module cannot reach
`data_manager`/`warmup`/`forward_testing`. The per-date loop tests substitute `scanner.run_scan` with a stub
that calls the **real, unmodified** `scanner.persist_run_payload`, so the INSERT/commit/idempotent-guard/
identity-stamping code is genuinely exercised. I re-ran both files myself:
`cd apps/backend && .venv/bin/python -m pytest tests/test_j11_stage_d_execute.py
tests/test_j11_stage_d_execute_cli_script.py -q` → **43 passed in 2.20s**.

### Process Findings

**P1 — OBSERVATION: no QA functional test plan was generated.** `reports/qa/goal-market-compass-iter-19-test-plan.md`
does not exist; the QA report itself records "NO PLAN FILE FOUND" and substituted standard checks. QA
compensated well — it ran genuine live read-only database verification rather than re-reading the handoff — so
no coverage was actually lost, but the pipeline step did not produce its artifact.

**P2 — RESOLVED: the reviewer's open NOTE is now closed.** The review report flagged that iteration 19 had no
counterpart to iterations 11–18's maintenance-isolation refusal log. The file now exists:
`runs/goal-session-market-compass/iter-19/maintenance-isolation-refusals`, one entry —
`2026-08-26T14:01:10Z operation=browser-qa-phase detail=browser QA + deterministic replay lane`. TC-15 is
satisfied by engine-generated evidence, not only by the handoff's own `ss`/`ps` observation.

---

## 3. Domain Assessment

**Was the coordinator's specific flag (a) — the identical execution identity — a real problem?** Partly, and not
in the way it was framed. It is *not* evidence of a copied value or a broken freeze: I reproduced the provenance
inputs and git history myself and the equality is forced. The real problem is the one step further out, in B1:
the identity is not merely equal to prior *observations*, it is equal to what every future ordinary
`persist_run_payload` will stamp, so it cannot function as attempt-membership evidence for Stage G.

**Was the coordinator's specific flag (b) — the reviewer verdicting from an empty diff — justified?** No. The
review asserts facts that cannot be produced from an empty diff, and every one of them matched my own
independent queries exactly: `scanner_runs` 3128 = 3117 + 11 with ids 3148–3158; the 34 / 3,083 / 11 identity
breakdown; `daily_prices` 3,310,374; `data_provider_runs` 549; `watchlist` 6; a single active
`maintenance_boundaries` row; the `compute_engine_identity` recomputation; and the `git log` provenance for the
three hashed engine files. The reviewer read the code. Where its skepticism stopped short was not the diff — it
was accepting the mathematical explanation for the identity equality and marking `definition_of_done: complete`
without testing that explanation against the ruling's and the DoD's own wording (B1).

**Is the regenerated data actually correct — not merely present?** This is the AG-3 question, and it deserves an
explicit evidence floor because I could not recompute the runs independently (that would require multi-GB
compute under an isolation contract that forbids it). Two lines of evidence, both gathered directly:

1. *Path.* `run_scan` is the unmodified canonical producer. `apps/backend/app/engine/scanner.py`,
   `j11_stage_d.py`, `j11_maintenance.py`, `j11_preboot_guard.py`, `j11_avb_diagnostic.py`, `prices.py`,
   `engine_identity.py` and `config.yaml` are all byte-identical to HEAD (`git status --porcelain -uall` over
   that exact file set returns empty). No scoring formula, threshold, or recovery-specific code path was
   introduced — ruling item 6 holds.
2. *Continuity across the retained↔regenerated boundary.* Regenerated values join the surviving history
   smoothly, which a degraded or truncated compute would not produce. `2026-05-11` (retained, NULL identity)
   regime 72.85 / breadth₅₀ 63.11 → `2026-05-12` (regenerated) 71.21 / 62.30 → `2026-05-13` 71.62 / 60.66 →
   `2026-05-20` (retained) 71.68 / 61.48. `2026-07-09` (retained) 69.98 / 50.82 → `2026-07-10` (regenerated)
   69.53 / 52.46. `2026-07-23` (retained) 57.87 / 39.34 → `2026-07-24` (regenerated) 57.73 / 40.98. Per-run
   result counts (539–542) also sit inside the retained runs' own range. Raw inputs are intact on every incident
   date (585–590 symbols with bars per date; `max(date)` = 2026-08-12).

The preflight was real, live, and comprehensive — not a rubber stamp. `j11-stage-d-execute-preflight.json`
(`captured_at` 10:51:20Z, ~84 s before the first write) records `all_incident_dates_zero_scanner_runs: true`
alongside ten other invariants, all `true`, plus `maintenance_isolation_env: {present: true, value: "true"}`
captured from the developer's own process environment rather than asserted in prose. The gate composition is
correctly stricter than the readiness verdict it reuses (`stage_d_execution_gate_verdict` requires exactly
`AVB-A`, where `stage_d_readiness_verdict` accepts A-or-B), and the AVB re-derivation fails **closed** to
`AVB-D` on incomplete override evidence or an `sufficient_evidence: false` marker
(`j11_stage_d_execute.py:203-236`) rather than guessing. The CLI gating is genuinely fail-safe: no `--confirm`
means `get_engine`/`Session` are never touched; no `--evidence-dir` refuses before any config load; a collision
guard refuses a re-run into a populated directory — each proven by a test that asserts the mock was
`assert_not_called()`.

**The honest state of the system after this iteration.** Stage D succeeded; the incident is *not* repaired, and
the handoff says so in exactly the ruling's vocabulary. The eleven new runs currently carry **zero**
`forward_returns` rows (verified: `SELECT count(*) FROM forward_returns WHERE run_id BETWEEN 3148 AND 3158` = 0)
and their dependent caches are un-invalidated. That is the correct, spec'd state — Stages E and F own those —
but it means the database is now in a deliberately partial condition that only the still-ACTIVE boundary and the
still-OFF application keep safe. An owner disaster-recovery snapshot taken before the write exists
(`/home/dennis-chan/trendora-db-snapshots/trendora-pre-j11-stage-d-20260826T100159Z.db`, 8,365,871,104 bytes,
2026-08-26 ~10:02Z, with a manifest), which materially reduces the irreversibility risk of this iteration.

---

## 4. Fixes Applied During This Audit

**None.** This is the correct outcome, not an omission.

| # | Candidate | Why not applied |
|---|-----------|-----------------|
| 1 | B1 — make the attempt identity distinct | Would require editing `compass.py`/`session_delta.py`/`engine_identity.py` or the three `compass.*` config keys purely to move a hash. Forbidden by owner ruling item 6, by the plan's Guardrails, and it is the precise anti-pattern `j11_stage_d_execute.py:55` warns against. Any row-level alternative is a live DB write, forbidden by the isolation contract and the coordinator note. Escalated to the owner instead (§5). |
| 2 | B2 — true content hashes in the sweep | Explicitly deferred by this spec's OUT OF SCOPE list; fixing it here is scope creep, and the residual risk is closed by code trace above. |
| 3 | B3/B4/T1–T4 | GAP/OBSERVATION class. Documenting them is the contract; fixing them is scope creep. |

No source file, test, evidence artifact or database row was modified by this audit. Verification was read-only
throughout; the single command I executed that touches anything is the pytest re-run, which uses in-memory and
`tmp_path` fixtures only.

---

## 5. Recommended Next Step

**Proceed to Stage E — but carry B1 to the owner first, because it is cheap to settle now and expensive to
discover at Stage G.**

1. **Owner ruling on B1 (blocking for Stage G's design, not for Stage E's start).** Ask the owner to confirm the
   procedural reading of ruling item 2 — "recompute fresh, never copy" — is what they intended, given that the
   value reading is unsatisfiable without violating their own item 6. Record the answer in `docs/goal.md` so
   Stage G is not left to re-litigate it.
2. **Record attempt membership explicitly, since `engine_identity` cannot carry it.** The eleven runs of this
   attempt are, verified live and read-only:
   **run ids 3148–3158**, dates 2026-05-12, 05-13, 07-10, 07-13, 07-24, 07-27, 08-03, 08-05, 08-10, 08-11,
   08-12, `created_at` window **2026-08-26 10:52:55.552946 → 10:53:02.010362 UTC**, all stamped
   `53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55`.
   Stage G should verify eleven-date membership against **this recorded set**, not against `engine_identity`
   alone, and should additionally assert that no *twelfth* run carries the same identity — which is the check
   that would actually catch an accidental ordinary write during the maintenance window.
3. **Keep everything OFF, and treat `resolve_run` as live-armed.** The pre-boot guard is wired only into
   `warmup.py` and `forward_testing.py`; `scanner.resolve_run` is not guarded, and 2026-08-04/06/07 are runless
   dates with bars, so a single `?as_of=` request would mint an indistinguishable twelfth run. Deferring the fix
   is the owner's call (ruling item 5) — leaving the app off is what makes that deferral safe.
4. **For Stage E's implementation:** prefer `prefilled_bar_cache(session, expected_symbols=pool_symbols)` over
   the lazy `bar_cache` path (B3) given `forward_returns` is 6.8 M rows, and add a hard assertion that the
   date set handed to any per-date loop is exactly `INCIDENT_DATES` so the vacuous-pass branch (B4) can never be
   reached by a caller mistake.
5. **Cheap riders, if a later iteration wants them:** the four test observations (T1–T4) and the missing QA test
   plan (P1). None blocks anything.

The maintenance boundary must stay `ACTIVE` and the application `OFF` until Stage G passes — unchanged, and
correctly upheld by this iteration.
