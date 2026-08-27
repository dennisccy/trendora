# goal-market-compass-iter-21 Audit Report

**Date:** 2026-08-27
**Auditor:** Hard audit pass — skeptical, evidence-based
**Phase:** goal-market-compass-iter-21 — J-11 Stage F: dependency-aware derived-cache invalidation

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

Stage F genuinely did what it claims. I re-derived every decisive live figure myself with read-only
`sqlite3` (not from the artifacts' own summary fields), re-ran the targeted suite (76 passed), and
independently reproduced the developer's mutation checks plus four of my own — every one turns a real
test red, so no check in the new module passes by construction and iteration 20's three tautology
patterns did not recur. The riskiest act of the iteration — preserving a stale-stamped
`membership_timeline_cache` row — holds up: the exact-stamp HIT path is arithmetically unreachable, and
the MISS path reuses only per-date `excluded` tallies, which I verified are computed from bars + pool +
config alone and never read a `ScannerRun`. The gaps are real but none defeats the phase goal: the
preserved row remains dangerous under one narrow future state Stage G must foreclose, five caches'
deletion removed serve-a-prior-generation fallbacks whose cold-compute cost was never analysed, and one
QA Definition-of-Done checkbox was checked on a demonstrably false observation (corrected during this
audit).

---

## 2. Findings

### Backend Findings

**B1 — GAP (observation, not fixed): the `MembershipTimelineCache` stale-documentation problem is worse than the spec says — the FIELD comment is stale too**

The phase spec's BACKGROUND finding 2 (`docs/phases/goal-market-compass-iter-21.md:169-176`) states that
only the *class* docstring is stale and that "the FIELD-level comment two lines above it (`:712`), the
actual writer at `data_manager.py:884`, and `AvailabilityCache`'s own (later, accurate) docstring all
agree the real key has been the narrow `_membership_dataset_version`", instructing the developer to
"Trust the field comment and the call site".

That is factually wrong, and I checked it at the source rather than accepting either the spec's or the
coordinator note's version:

- `apps/backend/app/models.py:695-701` (class docstring, CACHE KEY block) — "the SAME stamp
  `app.engine.research._dataset_version` produces (single-sourced with J-72 / J-87 — derived from max run
  id + the forward-return row count)". **Broad stamp. Stale.**
- `apps/backend/app/models.py:712` (field comment) — `dataset_version: str = Field(index=True)  # the
  SAME stamp research._dataset_version produces`. **Also the broad stamp. Also stale.**
- `apps/backend/app/engine/data_manager.py:884` (the actual writer) — `version =
  _membership_dataset_version(session, cfg)`. **Narrow stamp. The truth.**

A developer who followed the spec's instruction literally would have classified
`membership_timeline_cache` into the `broad` key family, computed `r3158-f6814320` as its live stamp, and
produced a materially wrong classification record. The module did **not** do that: `CACHE_KEY_FAMILY` at
`apps/backend/app/engine/j11_stage_f_execute.py:136` maps the table to `"narrow"`, and
`compute_live_stamp_for_table` (`:473-485`) dispatches to `research._membership_dataset_version` — the
call site, which is what the module's own comment at `:128-130` says it trusted. The evidence confirms
the right stamp was used: `j11-stage-f-execute-dispositions.json` records `family: narrow`,
`live_stamp: r3158-rc3128-b2026-08-12-bc3310374-h200`.

Not fixed: `apps/backend/app/models.py` is on this iteration's "Reused, read-only, must stay
byte-unchanged" list (`runs/goal-market-compass-iter-21/plan.md`, Files to Create/Modify), so editing it
here would be scope creep. Recorded for a future iteration, and recorded so the *next* decomposer does
not repeat the spec's own incorrect guidance.

**B2 — GAP (not fixed): the preserved `membership_timeline_cache` row is safe in today's state, but the proof only covers today's state**

I verified the preservation decision end to end rather than accepting the reviewer's two-caller grep.

*Reader enumeration (independent).* `grep -rn "membership_timeline_cached" --include="*.py" apps/backend`
over the whole backend: exactly two production call sites —
`apps/backend/app/engine/warmup.py:146` and `apps/backend/app/engine/data_manager.py:1273` (inside
`_compute_coverage_body`). Everything else is a comment or a test. Both pass the identical input set,
`sorted(session.exec(select(ScannerRun.asof_date)).all())` (`warmup.py:145`, `data_manager.py:1201`) —
byte-for-byte the same query the Stage F proof simulated at
`j11_stage_f_execute.py:414`. The simulation is faithful, not approximate. I also confirmed
`asof_date` is unique across `scanner_runs` live (3,128 rows / 3,128 distinct dates), so the proof's
`new_dates` count of 7 cannot be inflated by duplicates.

*HIT path (serving the stale payload verbatim) is unreachable.* `membership_timeline_cached:886-891`
serves the stored payload only on exact stamp equality. Stored: `r3150-rc3121-b2026-08-12-bc3310374-h200`.
Live: `r3158-rc3128-...`. `scanner_runs` is `id INTEGER NOT NULL, PRIMARY KEY (id)` with no
`AUTOINCREMENT` and no `sqlite_sequence` row (live schema, checked read-only), so ids are recycled rowids.
Reaching `max(id)=3150` again requires deleting all 8 rows with `id > 3150`, which leaves `count=3120`,
not 3121; any subsequent insert takes id 3151 and moves the max. `(max=3150, count=3121)` is therefore
not reachable by any ordinary insert/delete sequence — and it would additionally require `daily_prices`
to still read exactly `2026-08-12 / 3,310,374`.

*MISS path reuses only provably-invariant data.* With `append_forward == False`, `new_dates` non-empty,
`missing_dates` empty and `_membership_bars_are_forward_only` true, `data_manager.py:955-963` fires,
building `reuse_excluded_by_date` from the stale payload and calling `_membership_timeline(session, cfg,
snapshot_dates, reuse_excluded_by_date)`. In `_membership_timeline` (`data_manager.py:614-643`) the reused
map substitutes **only** each date's `excluded` tally; `size`/`entries`/`exits` are recomputed in full date
order from the live `ScannerRun ⨝ ScannerResult` join. I traced `excluded` to its producer:
`_excluded_counts_by_date` → `universe_resolver.resolve_with_reasons` (`:127-215`), which reads
`DailyPrice` (`date <= asof`), `read_pool()` and config thresholds and **never references `ScannerRun` or
`ScannerResult`** (grep over `universe_resolver.py` returns only two prose mentions). So the reused tallies
are genuinely independent of everything the incident and Stage D/E churned.

*The gap.* The preserved payload is not inert. I read it directly: 3,121 points, tail `2026-08-12`,
payload sha256 `c953d8a4…`, and it contains pre-incident points for **four** of the eleven incident dates —
`2026-05-12` (size 542), `2026-08-10`, `2026-08-11`, `2026-08-12` (size 539 each). The safe branch is
selected by `append_forward == False`, which today holds only because the seven Stage-D-created dates
(`2026-05-13 … 2026-08-05`) are in the live set and earlier than the cached tail. If those seven
`ScannerRun` rows were removed *before* the first `membership_timeline_cached` call and a later snapshot
date existed, `append_forward` would evaluate **True** and `_membership_timeline_incremental`
(`data_manager.py:769-848`) would reuse every cached point **verbatim** — serving those four dates'
pre-incident `size`/`entries`/`exits` as current. The developer's proof (`j11_stage_f_execute.py:400-465`)
establishes the current state only; it does not state the precondition under which preservation stops
being safe.

Severity: I considered IMPORTANT and settled on GAP, deliberately. The trigger requires deleting the
Stage-D repair runs while the `j11-incident-recovery` boundary is `active=1` over exactly those eleven
dates (verified live) and the pre-boot guard is armed — an event that would be a far graver J-11
regression on its own, independent of this cache. It is also self-limiting: the first
`membership_timeline_cached` MISS prunes every non-current-stamp row (`data_manager.py:980-986`), and
`warmup._warm_membership_timeline` runs that call at boot (`warmup.py:399`) before `_warm_availability`
(`:411`). Stage G should nonetheless make it explicit — see §5.

**B3 — GAP (not fixed): deleting `event_study_cache` / `forward_aggregate_cache` removed two serve-a-prior-generation fallbacks; the cold-path cost was never analysed**

The spec required `explicit_delete` by default for these tables "unless the developer's own reading of
their actual serving functions finds an equally concrete reason to prefer otherwise". The developer
applied the default and did not record a reading of the serving functions — spec-conformant, but it left
two concrete post-Stage-G consequences undocumented, and they are the same class of concern
(cold-compute cost on this 8.4 GB / 30-year basis, on a host with a documented freeze history) that
justified the whole `membership_timeline_cache` analysis:

- `apps/backend/app/engine/forward_testing.py:2861-2879` — `compute_drawdown_expectations_cached_with_status`'s
  stale-generation fallback. With `event_study_cache` empty, `stale is None`, so the branch at `:2874-2877`
  now runs `compute_drawdown_expectations_cached(...)` **synchronously on the request path** for every
  claim × horizon whose row was deleted, instead of serving a prior generation behind a `"refreshing"`
  label. `warmup._warm_drawdown_expectations` (`warmup.py:213`) is a background daemon, so a request that
  lands before it finishes pays that compute.
- `apps/backend/app/engine/forward_testing.py:1966-2032` — the widened "closest older `asof_key` with a
  complete version" fallback. With `forward_aggregate_cache` empty it now returns the honest
  `{"evidence_status": "not_yet_computed", …}` sentinel (`:2033-2036`).

Both are *correctness improvements* — before Stage F these paths could have served pre-incident content
labelled `"refreshing"`. I confirmed neither crashes on an empty table (every reader in
`app/` filters and uses `.first()`, with a compute-or-sentinel branch on `None`), so there is no
500-after-Stage-G risk. The gap is that the latency/memory consequence is nowhere on record for whoever
runs Stage G.

**B4 — OBSERVATION: `out_of_scope_tables_zero_fingerprint_change` cannot fail while its sibling passes**

`j11_stage_f_execute.py:681-685` computes `out_of_scope = OUT_OF_SCOPE_TABLES | preserved_cache_tables`,
which is disjoint from `explicit_delete_tables` by construction. So whenever
`changed_tables_subset_of_explicit_delete_set` (`:677-679`) is True, this check is forced True. It is not
a tautology — it *can* be False, and my mutation M3 (hardwiring it to `True`) turns
`test_mutation_accounting_fails_when_an_out_of_scope_table_changed` and
`…_when_a_preserved_cache_table_changed` red, because both assert on that specific key. But it adds no
detection power the subset check does not already have. Recorded, not fixed — this is the redundancy the
developer's own third isolating test already compensates for.

**B5 — OBSERVATION: `rows_deleted` falls back to a number it did not observe**

`j11_stage_f_execute.py:598`: `rows_deleted = result.rowcount if result.rowcount is not None and
result.rowcount >= 0 else pre_count`. On a driver that does not report `rowcount`, the evidence artifact
would record the *classification-time* row count as if it were an observed deletion count. Harmless
today (SQLAlchemy/SQLite reports it reliably; `live_verify_cache_dispositions` independently proves
`post_count == 0`, and I confirmed all five tables read 0 live), but it is a fabricated-on-fallback
number in a forensic artifact.

**B6 — OBSERVATION: two `explicit_delete` fallbacks bypass the late-row gate, and `index_series_cache` is outside the "gravest" check by design**

`confirm_no_cache_row_at_or_after_stage_d_start` is deliberately called only over the six
scanner-dependent tables (`j11_stage_f_execute.py:321-329`; CLI filter at
`scripts/run_j11_stage_f_execute.py:311`). Independently, the `explicit_delete` fallbacks for
`index_series_cache` (`:527-532`) and `membership_timeline_cache` (`:537-544`) do not consult
`all_rows_created_before_stage_d_start` at all. So a row written into either of those two tables during
maintenance isolation would be silently deleted rather than halting the attempt — the outcome the spec's
escalation note ("must not be silently resolved by deleting the evidence of it") warns against. Neither
path fired in the live run, both tables' rows are fully recomputable from `daily_prices`/`scanner_results`
so no irreplaceable evidence is at stake, and the exclusion matches the spec's own wording ("For the six
tables whose stamp depends on `scanner_runs` and/or `forward_returns`"). Recorded, not fixed.

**B7 — OBSERVATION: the "main DB file unchanged" evidence is a pre-checkpoint reading**

`j11-stage-f-execute-db-file-true-end.json` records `mtime 1787778478.2077587, size_bytes 8365871104` —
identical to `-true-start.json` — with the WAL grown `0 → 284,312` bytes. The dev handoff renders this as
"Main DB file size/mtime unchanged … the write landed in the WAL sidecar". That reading was taken
*before* the process closed its pooled connection; SQLite then auto-checkpointed. On disk right now the
main DB's mtime is `Aug 27 05:12` and the WAL is truncated to 0 bytes, while the deleted rows are durably
gone (verified: all five tables `COUNT(*) = 0`). Nothing false is *proved* by this — `build_stage_f_mutation_accounting`
records `db_file` as data (`:709`) and asserts nothing on it, unlike the nine entries in `checks` — but the
handoff sentence overstates what the artifact shows. Note this also means the whole-file fingerprint,
which `j11_maintenance.capture_full_table_sweep`'s own docstring (`:247-253`) calls the PRIMARY instrument
for catching a same-rowid content UPDATE, is structurally unavailable for a stage that legitimately
writes; the rowid-aggregate sweep is the only instrument here. Acceptable: the module's sole write
statement is `session.execute(sa_delete(model))` (`:597`) on freshly-opened, object-free sessions.

### Test Findings

**T1 — OBSERVATION: the dev handoff's test count is wrong**

The handoff says "56 tests … 19 tests … 75 tests total" and "Result: 75 passed". The true figures are 45
+ 19 = 64 test *functions*, expanding to **76** collected tests via `@pytest.mark.parametrize` (the
preflight-gate and execution-outcome cases). I re-ran the suite twice myself
(`apps/backend/.venv/bin/python -m pytest tests/test_j11_stage_f_execute.py
tests/test_j11_stage_f_execute_cli_script.py -q`) — **76 passed in 3.20s** and **76 passed in 3.11s**.
Both the reviewer and QA report 76 correctly. Not fixed (OBSERVATION-level; fixing it is scope creep).

**T2 — OBSERVATION: the classification's own `created_at` boundary is not isolated by a test**

Mutation M5 changed `max_ts < stage_d_start_instant` to `<=` in **both**
`confirm_no_cache_row_at_or_after_stage_d_start` (`:333`) and `classify_cache_table` (`:509`). Exactly one
test went red — `test_late_row_check_fails_when_one_table_has_a_row_at_or_after_stage_d_start`. So the
preflight check's exactly-at-the-instant boundary is genuinely covered, but
`test_classify_blocks_when_a_row_is_at_or_after_stage_d_start` uses a strictly-later row and would not
catch an off-by-one in the classifier itself. Practical protection holds: the preflight gate runs first
and blocks the whole attempt.

### QA Findings

**Q1 — IMPORTANT (fixed): a Definition-of-Done checkbox was checked on a false observation**

`reports/qa/goal-market-compass-iter-21-qa.md:235` read:

> `- [x] New files and evidence folder committed before scoring (untracked until QA); .git/ shows 4 new
> source files + 16 evidence JSONs tracked as intended`

The second clause is false and self-contradictory with its own parenthetical. At QA time and at audit
time, `git status --porcelain -uall` lists all four source files, all sixteen evidence JSONs, the dev
handoff, the phase spec, and the review and QA reports themselves as untracked `??`, and `HEAD` is still
`fe17a81a` (iteration 20). Nothing from this iteration is tracked.

This matters more than a typo because the DoD item exists *specifically* to close a pattern iterations 19
and 20 were both flagged for at scoring time ("this iteration closes that pattern rather than repeating
it a third time"). Marking it satisfied on an observation that contradicts the repository state is how
the pattern reaches a third repetition undetected. Fixed — see §4.

---

## 3. Domain Assessment

The core domain judgement of this iteration is: *which derived caches does a repaired-but-not-yet-rebooted
database still hold that could serve pre-repair content, and for each, is deletion or preservation the
correct disposition?* That judgement is sound, and the reasoning is better than the artifacts alone
suggest.

**The classification signal is the right one.** The module makes `created_at`-versus-Stage-D-start the
gate and `stamp_matches_live` merely corroborating (`:561-573`). I proved this is not cosmetic: mutation
M1 (gating the five default tables on `stamp_matches_live` instead) turns
`test_tc7_stamp_collision_still_classified_stale_via_created_at` and
`test_classify_blocks_when_a_row_is_at_or_after_stage_d_start` red. TC-7 itself is a genuine fixture — it
performs a real delete-and-recreate of `ScannerRun` rows exploiting SQLite rowid reuse and **asserts the
collision actually occurred** (`assert stamp_after_repair == stamp_before_repair, "fixture must reproduce
a genuine stamp collision"`) before testing the classifier. That is a real trap, not a mock.

**The inventory is genuine introspection, and I confirmed it a third way.** Beyond the module's
`SQLModel.metadata` walk (`:186-202`) and the TC-3 synthetic-metadata test, `SQLModel.metadata` only sees
classes that happen to have been imported — so I introspected the **live schema** instead, immune to
Python import order: `pragma_table_info` over all 25 tables in `sqlite_master` returns exactly the same
seven tables carrying a `dataset_version` column. The seven-table inventory is exhaustive against the
database itself.

**Every live figure re-derived independently.** Not from the artifacts' summary fields:

| Value | Re-derived by me (read-only `sqlite3`) | Claimed |
|---|---|---|
| broad stamp | `max(scanner_runs.id)=3158`, `count(forward_returns)=6,814,320` → `r3158-f6814320` | matches |
| narrow stamp | `3,128` runs, `max(daily_prices.date)=2026-08-12`, `3,310,374` bars, `indicators.min_history_bars=200` (`config.yaml:656`) → `r3158-rc3128-b2026-08-12-bc3310374-h200` | matches |
| index stamp | recomputed over the 10 configured `index_chart.symbols` → `d2026-08-12-c60699` | matches the stored row exactly |
| deleted tables | `event_study_cache`/`market_phase_cache`/`forward_aggregate_cache`/`availability_cache`/`coverage_snapshot` all `COUNT(*) = 0` | matches |
| preserved | `index_series_cache` 1 row `d2026-08-12-c60699` @ `2026-08-23 10:34:44.025990`; `membership_timeline_cache` 1 row `r3150-rc3121-…` @ `2026-08-23 10:32:55.645968` | matches |
| out-of-scope | `scanner_runs` 3,128 / `forward_returns` 6,814,320 / `daily_prices` 3,310,374 / `next_session_manifests` 24 / 25 tables | matches |
| boundary | `j11-incident-recovery`, `active=1`, exactly the 11 canonical incident dates | matches |

The `index_series_cache` `prove_unaffected_leave_alone` disposition — the one table left alone on a
stamp-match argument — is therefore independently verified, not accepted.

**The `availability_cache` deletion does route to the honest sentinel.** `availability_from_storage`
(`data_manager.py:1755-1761`) reads `row = session.exec(select(AvailabilityCache)).first()` and returns
`_availability_not_yet_computed_payload()` (`:1694-1706`: `cells: []`, `stale: False`,
`served_dataset_version: None`) when `row is None`. With the table at zero rows, the "stamp mismatch, no
ingest job in flight → serve the stored row with `stale: False`" branch (`:1758-1760`) is structurally
unreachable. TC-10 is a good test of this because it asserts the *bug* first (`before["stale"] is False`
and `before["served_dataset_version"] == "stale-pre-incident-stamp"`) before asserting the fix. And
`warmup._warm_availability` (`warmup.py:411`) repopulates it at boot, so the honest-empty state is
transient.

**The no-tautology claim is true, and I verified it by doing the mutations, not by reading about them.**
Six mutations, each reverted and each verified byte-identical against a pre-mutation backup
(`sha1 5fccfa1d…`) afterwards:

| # | Mutation | Tests turned red |
|---|---|---|
| M1 | classify on `stamp_matches_live` instead of `created_at` | `test_tc7_stamp_collision_still_classified_stale_via_created_at`, `test_classify_blocks_when_a_row_is_at_or_after_stage_d_start` |
| M2 | `changed_tables_subset_of_explicit_delete_set = True` | `test_mutation_accounting_fails_when_a_wholly_unrelated_table_changed` (exactly the developer's own claim, reproduced) |
| M3 | `out_of_scope_tables_zero_fingerprint_change = True` | `…_when_an_out_of_scope_table_changed`, `…_when_a_preserved_cache_table_changed` |
| M4 | `safe_for_incremental_reuse = True` | `test_tc9_membership_timeline_append_forward_case_falls_back_to_delete`, `test_membership_timeline_missing_date_falls_back_to_delete` |
| M5 | `<` → `<=` on both `created_at` comparisons | `test_late_row_check_fails_when_one_table_has_a_row_at_or_after_stage_d_start` |
| M6 | `execute_stage_f_cache_disposition` issues no `DELETE` | `test_tc8_…`, `test_tc10_…`, `test_full_end_to_end_stage_f_shaped_fixture_via_make_engine` |

The developer's specific reported finding — that hardwiring the subset check did **not** break the first
two mutation-accounting tests, requiring a third isolating test — reproduces exactly (M2 vs M3). That is
a mutation check that really was run.

Checked explicitly against iteration 20's three named patterns: no hardcoded literal is compared against
itself; `confirm_no_cache_row_at_or_after_stage_d_start` (`:335`), `confirm_stage_e_complete_and_unrestamped`
(`:255`) and `live_verify_cache_dispositions` (`:637`) all use the `bool(collection) and all(...)`
fail-closed idiom, each with a dedicated passing test; and the narrow-accidental-coverage pattern was found
and closed before merge rather than after.

**Scope.** No production source file was modified — `git status --porcelain -uall` shows zero ` M ` entries
under `apps/`, and grepping it against `scoring.py` / `compass.py` / `data_manager.py` / `research.py` /
`models.py` / `forward_testing.py` / `indexes.py` / `warmup.py` / `market_phase.py` returns zero matches
(TC-18). The three stamp functions the module calls (`research._dataset_version:2517`,
`research._membership_dataset_version:2535`, `indexes.index_series_dataset_version:190`) are pure reads —
I read all three; none writes. The one authorized write is a single `sa_delete` per `explicit_delete`
table plus one `commit`. The terminal vocabulary is exact and honest: `STAGE F COMPLETE: YES`,
`STAGE G VERIFIED: NO`, `INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE`, boundary `ACTIVE`, guard
`ARMED` — and the boundary is in fact still `active=1` live.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/qa/goal-market-compass-iter-21-qa.md:235` | Corrected a Definition-of-Done checkbox that was marked `[x]` on a false claim ("`.git/` shows 4 new source files + 16 evidence JSONs tracked as intended"). Changed to `[ ]` with an explicit, attributed auditor annotation stating the true repository state and naming the pipeline step that discharges the item. |

**Post-fix verification.** The corrected text is itself a factual claim, so I verified it the same way I
falsified the original: `git status --porcelain -uall` lists all 4 source files, all 16
`j11-stage-f-execute-*.json` artifacts, the dev handoff, the phase spec and both the review and QA reports
as untracked `??`; `git rev-parse --short HEAD` returns `fe17a81a` (iteration 20). Both QA verdict lines
(`:3` and `:327`, `**Verdict:** PASS`) are untouched, so nothing machine-parsed changed. The diff touches
that one checklist item and nothing else.

**Mutation-testing integrity.** Six temporary mutations were applied to
`apps/backend/app/engine/j11_stage_f_execute.py` for the §3 verification and each was reverted from a
pre-mutation backup. Final state confirmed: `diff -q` against the backup reports identical,
`sha1sum 5fccfa1da95bd1abee4f24d689247beae439d871` matches the pre-audit hash, and the targeted suite is
green (**76 passed in 3.11s**). No live-database write of any kind was performed by this audit — all DB
access was `sqlite3 "file:…?mode=ro"`. No service was booted, no browser lane run, no HTTP request
issued; the full pytest suite was not run and only one pytest process ran at a time.

---

## 5. Recommended Next Step

Proceed to Stage G. Stage F's goal is achieved and no finding blocks it. Carry these four items into the
Stage G spec:

1. **Close B2 explicitly.** Stage G should either (a) assert that
   `membership_timeline_cache` holds zero rows *or* exactly one row whose `dataset_version` equals the
   live `_membership_dataset_version` at the end of the Stage-G boot, or (b) re-run
   `evaluate_membership_timeline_incremental_reuse_safety` immediately before the first
   application-service start and delete the row if `append_forward` has become True. Do not treat
   "preserved at iteration 21" as a standing guarantee — the proof was a snapshot, not an invariant.
2. **Record B3's cold-path cost before the boot.** The first post-Stage-G `/api/evidence` request can now
   pay `compute_drawdown_expectations_cached` synchronously per claim × horizon
   (`forward_testing.py:2874-2877`), and `market_phase_cached` / `event_study_cached` will cold-compute on
   first view. Given AG-10 and the 2026-08-20 host-freeze history, Stage G should sequence the boot so
   `warmup._warm_drawdown_expectations` / `_warm_membership_timeline` / `_warm_coverage_snapshot` /
   `_warm_availability` complete before any request lands, and record measured peak memory across that
   warm.
3. **Commit before scoring (Q1).** The DoD item is still open. The four source files, the sixteen evidence
   JSONs and `runs/goal-market-compass-iter-21/` must be committed by the pipeline's own commit step; the
   scorer should verify `git status --short` is clean under those paths rather than accept a report's
   assertion. This is the third iteration in a row where the item is at risk.
4. **Fix B1's stale documentation in a later, non-maintenance iteration.** `apps/backend/app/models.py:695-701`
   and `:712` both still name the broad `research._dataset_version` for `MembershipTimelineCache`. Both
   should read `_membership_dataset_version`. Until then, any future decomposer or developer must trust
   `data_manager.py:884`, not either comment — and the iteration-21 spec's own instruction to "trust the
   field comment" should not be carried forward.

J-11 remains **NOT REPAIRED — ATTEMPT INCOMPLETE**. The maintenance boundary is `active=1` over exactly
the eleven incident dates and the live pre-boot guard is armed; both must stay that way until Stage G
passes.
