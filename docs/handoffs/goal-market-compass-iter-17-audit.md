# goal-market-compass-iter-17 Audit Report

**Date:** 2026-08-25
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The authorized slice of the owner's 2026-08-25 ruling was delivered in full and is genuinely correct: the AG-8 bounded query is real (I compiled the statement and read the emitted SQL), it provably retains `active IS NULL` rows, and its bound is *enforced* by a fail-closed branch rather than silently truncating. The arm/disarm entrypoints are production-shaped, scope-safe, and never reachable against the live file by omission. The STALLED live-arm sub-step is the expected, correct outcome and is named honestly.

The gaps are in how the evidence is *presented*, not in what was built. Three matter: the live boot-path exposure is materially understated (a boot today would both create the forbidden table **and** write a canonical `ScannerRun` for `2026-08-12`, a quarantined incident date that is simultaneously the max `daily_prices` date); QA's "Incident Date Verification" row verifies eleven dates that are not the incident dates, seven of which carry no data at all; and TC-13's headline A/B ratio is an algebraic identity of iteration 16's own correction formula rather than independent evidence. The `AVB-A` label itself, which I attacked hardest, is honestly derived.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap — not fixable within this iteration's authorization): the live boot-path exposure is understated; one boot both creates the forbidden table and writes a quarantined-date `ScannerRun`.**

Every artifact in this iteration records TC-11's `blocked: False` as a clean PASS (`docs/handoffs/goal-market-compass-iter-17-dev.md:17-27`, `reports/reviews/goal-market-compass-iter-17-review.md:12-18`, `reports/qa/goal-market-compass-iter-17-qa.md:114-121`). None states what that result means for the live system. Traced end to end:

- `apps/backend/main.py:84` calls `create_db_and_tables(engine)` → `apps/backend/app/db.py:226-231` → `SQLModel.metadata.create_all`. On the live DB this **mints `maintenance_boundaries`** — precisely the act `docs/goal.md`'s "BLOCKER ON RECORD" forbids ("do not create it and do not migrate to it").
- `apps/backend/main.py:100` then calls `ensure_latest_snapshot(engine, config)` → `apps/backend/app/engine/warmup.py:103` `latest_data_date(session)` → `apps/backend/app/engine/prices.py:66` = `max(daily_prices.date)`.
- Read-only probe of the live DB (recipe below): `max(daily_prices.date)` = **`2026-08-12`**, which is `j11_maintenance.INCIDENT_DATES[-1]` (`apps/backend/app/engine/j11_maintenance.py:74`) — a quarantined date. `max(scanner_runs.asof_date)` = `2026-07-23`. All eleven real incident dates carry **0** `scanner_runs`.
- With the table freshly created and empty, `evaluate_boundary_for_date` returns `blocked: False` at `apps/backend/app/engine/j11_preboot_guard.py:229-230`, so `apps/backend/app/engine/warmup.py:121` `run_scan(session, latest, cfg)` executes and writes a canonical `ScannerRun` for `2026-08-12`.

The only control preventing this is "do not boot the backend" — which the owner's implementation requirement 1 explicitly rejects: *"'Do not start the backend' is not an acceptable control."* This is not a regression introduced by iteration 17 and it is not fixable here (both table creation and arming are owner-blocked). But the honest statement of live state is not "the guard is merely not armed yet" — it is "iteration 16's boot-path hole is fully open, and the single date TC-11 probed is exactly the date a boot would write." I was unsure between IMPORTANT and GAP and took the higher level per the rubric, because a reader of the three green artifacts would not learn this.

Recipe (strictly read-only, `mode=ro` + `PRAGMA query_only=ON`, confirmed returning `1`):
```python
con = sqlite3.connect("file:apps/backend/data/trendora.db?mode=ro", uri=True)
con.execute("PRAGMA query_only=ON")
con.execute("SELECT max(date) FROM daily_prices").fetchone()          # ('2026-08-12',)
con.execute("SELECT max(asof_date) FROM scanner_runs").fetchone()     # ('2026-07-23',)
# GROUP BY over the 11 canonical INCIDENT_DATES returned [] -> 0 runs on every one
```

**B2 — OBSERVATION (examined and cleared): the new table-absent branch is a behavior change, but not a fail-closed → fail-open regression.**

Worth recording because it reads like a critical reversal and is not. The pre-iteration code raised `OperationalError: no such table: maintenance_boundaries` on a table-absent DB (verified directly), which `apps/backend/app/engine/warmup.py:106-112` converts to `blocked=True`. The new pre-check at `apps/backend/app/engine/j11_preboot_guard.py:215-216` returns `blocked=False` instead. On the **real boot path the branch is unreachable**: `main.py:84` creates the table before `main.py:100` reaches the guard, so the old code would have seen an empty table and returned `blocked=False` too. Net real-boot behavior is unchanged. The branch only affects out-of-boot callers — today, this iteration's own read-only diagnostic.

Residual worth the owner's attention (not actionable here): if the boundary were ever armed and the table later dropped, the guard would now allow silently rather than raise into warmup's fail-closed wrapper.

Minor imprecision: the module docstring at `j11_preboot_guard.py:45-47` says the `OperationalError` "is checked for explicitly rather than allowed to propagate". The implementation does not catch it — it pre-empts it with `sa_inspect(...).has_table(...)`. The inline comment at `j11_preboot_guard.py:209-214` describes the real mechanism accurately.

**B3 — GAP: `run_j11_iter17_stage_d_readiness.py` can overwrite three committed iteration-16 evidence artifacts if `--evidence-dir` is mistyped.**

`apps/backend/scripts/run_j11_iter17_stage_d_readiness.py:160`, `:176` and `:326` write `j11-stage-d-preflight.json`, `j11-stage-d-preflight-gate.json` and `j11-avb-bridge-diagnostic.json` into whatever `--evidence-dir` names. All three filenames already exist in `runs/goal-market-compass-iter-16/`. The script hash-guards iteration 16's `j11-stage-d-readiness.json` (`:134`, `:362`) but not these three, and has no refusal guard on the destination. There is **no default** pointing at a real evidence directory — `--evidence-dir` defaults to `None` and refuses (`:125-131`), correctly honoring iteration 14's lesson — so this requires a deliberate typed path. Recording it because iteration 14 lost committed evidence to a near-identical shape.

### Frontend Findings

None — backend-only iteration; no frontend file is touched. Verified: no path under `apps/frontend/` appears in the tracked diff or the untracked file list.

### Test Findings

**T1 — IMPORTANT (gap): QA's "Incident Date Verification" row verifies the wrong dates, seven of which hold no data at all.**

`reports/qa/goal-market-compass-iter-17-qa.md:100-101` claims *"All 11 incident dates confirmed at 0 scanner_runs"* and lists `2026-08-09, 08-10, 08-12, 08-14, 08-15, 08-16, 08-17, 08-19, 08-20, 08-21, 08-22`. The canonical set (`apps/backend/app/engine/j11_maintenance.py:63-75`, identical to the owner's ruling text in `docs/goal.md`) is `2026-05-12, 05-13, 07-10, 07-13, 07-24, 07-27, 08-03, 08-05, 08-10, 08-11, 08-12`. **Nine listed dates are not incident dates; nine real incident dates are missing.**

Worse, the check is vacuous for most of what it lists: `daily_prices` ends at `2026-08-12`, and the only stored dates after `2026-08-05` are `08-06, 08-07, 08-10, 08-11, 08-12`. Dates `08-14` through `08-22` do not exist in the database at all, so "0 runs" for them is trivially true and proves nothing.

The underlying fact does hold — I independently confirmed all eleven **real** incident dates carry 0 `scanner_runs` (recipe in B1). Severity is IMPORTANT because this is a functional-verification row in the pipeline's QA record that does not test what it claims, in the one place the quarantine invariant is supposed to be checked.

**T2 — GAP: the "J-01/J-04/J-10 code untouched" proof used a command blind to five of the seven changed files.**

Both `docs/handoffs/goal-market-compass-iter-17-dev.md:29-33` and `reports/qa/goal-market-compass-iter-17-qa.md:173` prove this with `git diff --name-only HEAD | grep -E '(app/api|scoring\.py|sectors\.py|compass\.py)'`. Five of the seven changed source files are **untracked**, so `git diff` cannot see them — the same blind spot that in iteration 16 let new code reach the evaluator unreviewed. I re-ran the check over tracked and untracked files together:

```bash
{ git diff --name-only HEAD; git status --porcelain | awk '{print $2}'; } | sort -u \
  | grep -E 'app/api|scoring\.py|sectors\.py|compass\.py'   # -> no matches
```

The claim is **true**; it was simply not validly proven by the command cited.

**T3 — GAP (agrees with the reviewer's filed MINOR): the two new evidence scripts have zero test coverage.**

`reports/reviews/goal-market-compass-iter-17-review.md:29-41` already filed this against `run_j11_iter17_stage_d_readiness.py` and `run_j11_iter17_live_preboot_guard_verification.py`. Confirmed — neither script has any test, not even the `--evidence-dir` refusal branch, unlike the precedent in `test_j11_stage_d_cli_scripts.py`. Not a spec gap (TESTING REQUIREMENTS names only the arm/disarm scripts), and it compounds B3: the refusal branch that keeps these scripts away from a real evidence directory is itself untested.

**T4 — OBSERVATION: test quality on the delivered slice is high, not ceremonial.**

Assertions are tight and several are adversarial in the right way. `test_iter17_tc5_...` does not settle for the resulting boolean — it compiles `guard._relevant_boundary_rows_statement()` and asserts the literal `LIMIT` bound. `test_iter17_bound_exceeded_fails_closed` exercises the overflow branch itself with 105 rows, proving the bound is *enforced* rather than silently truncating. `test_tc9_disarm_scoped_to_named_boundary_only` compares the untouched boundary's full `model_dump()` including `updated_at`. `test_null_active_row_is_not_constructible_through_the_normal_schema` records an honest negative finding rather than quietly bending the fixture. The mock-based refusal tests assert `make_engine.assert_not_called()`, which is the right invariant ("no database interaction, not even a read") rather than an exit-code-only check.

### Domain / Evidence Findings

**D1 — GAP: TC-13's headline A/B dollar-volume ratio is an algebraic identity of iteration 16's correction formula, not independent evidence.**

`apps/backend/scripts/run_j11_iter17_stage_d_readiness.py:270-274` computes `close_b = close_a / bridge_factor` and `volume_b = volume_override[date]`, so

```
ratio = (close_a · volume_a) / ((close_a / bf) · volume_b) = (volume_a · bf) / volume_b
```

`close_a` cancels exactly — the ratio carries no price information at all. And `volume_a` is *defined* as `volume_b` scaled by `bf`: `runs/goal-market-compass-iter-16/j11-avb-correction-derivation.json` records `formula = corrected_volume = round(provider_volume / bridge_factor)`. So the ratio cannot land anywhere except ≈1.0, off only by the rounding residual. Confirmed numerically: iteration 16's own `dollar_volume_ratio_after` values in that derivation artifact are `1.0000002381510753` and `1.000000133734225` — **digit-for-digit identical** to iteration 17's `ratio_a_over_b`. TC-13's "new" number is iteration 16's own correction cross-check, recomputed.

The persisted note at `run_j11_iter17_stage_d_readiness.py:286-288`, echoed into `j11-avb-bridge-diagnostic.json`, therefore overstates: A and B are not "genuinely independent" pairs — B is `(provider_close, provider_volume)` and A is its `bridge_factor`-scaled counterpart by construction. The dev handoff's surrounding framing (`docs/handoffs/goal-market-compass-iter-17-dev.md:161-171`) is accurate about iteration 16 and stops short of claiming independence, so this is an artifact-prose gap, not a false handoff claim.

**D2 — OBSERVATION (the label survives the attack): `AVB-A` is honestly derived, not reverse-engineered.**

I checked this specifically because iteration 16's `AVB-B` was adjudicated dishonest. The label is produced by `classify_avb` (`apps/backend/app/engine/j11_avb_diagnostic.py:872-939`), called unmodified at `run_j11_iter17_stage_d_readiness.py:292`; the only forced label in the script is the fail-*closed* `AVB-D` override at `:293-300`, which did not fire (`provider_fetch_evidence_sufficient: true`). `AVB-A` falls out of `material_signals == []`, and the flip from iteration 16 is fully explained by real trace output:

| | iter-16 (no override) | iter-17 (override) |
|---|---|---|
| ADV A vs B, 2026-08-12 | 193,208,569.01 vs 185,391,547.72 | 193,208,569.01 vs 193,208,567.21 |
| other-ticker percentile shifts | 1 and 11 | 0 and 0 |

The dollar-volume-driven half of that result is a consequence of the correction having been applied correctly (see D1), but the comparison is not entirely tautological: `close_b` is `65.08` against `close_a` of `181.76` — a 2.79× price difference — and risk bucket (`E`/`E`), setup status (`Avoid`/`Avoid`) and eligibility (`False`/`False`) are genuinely compared across it. `stage_d_ready_per_avb` is true for both `AVB-A` and `AVB-B`, so `READY: YES` did not move, exactly as the handoff states.

---

## 3. Domain Assessment

**The AG-8 fix is correct, and correct for the stated reasons.** I compiled the statement rather than trusting the description:

```
SELECT maintenance_boundaries.name, maintenance_boundaries.active,
       maintenance_boundaries.quarantined_dates_json, maintenance_boundaries.reason
FROM maintenance_boundaries
WHERE maintenance_boundaries.active IS NOT false
 LIMIT 101
```

Against a hand-built table holding a `NULL`-active row, an `active=0` row and an `active=1` row, the statement returns `[('null-row', None), ('active', True)]` — the `NULL` row is retained, the cleared row excluded, and the guard fails closed naming `null-row` with `ambiguous: True`. The three coordinator-flagged crux questions all resolve cleanly: the bound is `LIMIT 100+1` paired with a `len(rows) > 100` fail-closed return (`j11_preboot_guard.py:219-228`), so it enforces rather than truncates; `active IS NOT FALSE` does retain `NULL` so the fail-closed branch sees it; and table-absence is distinguished from ambiguity by a positive `has_table` pre-check rather than by swallowing an exception class (an inspection failure still propagates into warmup's fail-closed wrapper at `warmup.py:106-112`, which I verified exists and does treat any exception as blocked).

**The lifecycle entrypoints are production-shaped and scope-safe.** Both require `--confirm` and an explicit `--database-url` with no default, and refuse before constructing an engine — the mock tests prove `make_engine` is never called on the refusal paths. The arm script validates the code's `INCIDENT_DATES` against `docs/goal.md`'s own lists via the reused `check_c1_date_set_boundary` *before* touching a database (`run_j11_maintenance_boundary_arm.py:104-113`), and refuses with a named STALLED message if the table is absent (`:116-125`) rather than reaching for `create_all`. Idempotency is real, not test-scaffolded: `register_boundary` upserts on the unique `name` column. Disarm takes `--name` as required with no default and deactivates rather than deletes, matching the owner's "deactivate, do not delete" instruction. The only three references to `trendora.db` in the new scripts are in docstrings; none is a default.

**Mutation accounting independently reproduced.** My own `stat` of the live file: mtime `1787670395.652078900`, size `8365871104`, `-wal` size `0`, `-wal` mtime `1787670632.467415300` — matching the recorded true-start, true-end, the rider's own zero-write proof, and the decomposer's pre-iteration baseline. I recomputed iteration 16's artifact hashes with `sha256sum`: `e794dbf2…f7a0138` and `1e35942c…fedb57079`, both matching the handoff exactly. `maintenance_boundaries` is still absent from the live `sqlite_master`. Nothing wrote to the live database.

**Scope discipline held.** No file under `app/api/`, and no `scoring.py`/`sectors.py`/`compass.py`, appears in the tracked *or* untracked change set. No credentials in any new file. The `warmup.py` call site is unchanged, as the spec required.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | **None.** |

Deliberate, with reasoning, since the rules require fixing CRITICAL and IMPORTANT findings:

- **B1** cannot be fixed within this iteration's authorization. The real remedies — creating `maintenance_boundaries` on the live DB, or arming it — are both explicitly not authorized by the owner's ruling. The one code change available (making table-absence fail closed) would have **zero effect on the real boot path** (the branch is unreachable there, per B2), would directly contradict the spec's TC-11 and its committed evidence artifact, and would break `test_iter17_table_absent_evaluates_cleanly_as_unblocked`. Changing an explicit, owner-informed spec decision on my own authority is the scope creep the rules forbid. Recorded for the owner instead.
- **T1** is a defect in another agent's evidence artifact, not in source. Silently rewriting the QA report would destroy the record of what QA actually checked. The correction of record is this report, which supplies the canonical date set and the independently verified result.

No source file was modified, so no post-fix re-verification applies. Every test run cited below was executed against the code exactly as the developer left it.

**Verification I ran:**
- `cd apps/backend && .venv/bin/python -m pytest tests/test_j11_preboot_guard.py tests/test_j11_preboot_guard_cli_scripts.py -q` → **39 passed in 1.13s** (26 + 13; counts confirmed by `grep -c '^def test_'`).
- Statement compilation and `NULL`/cleared/active row-retention probe against a hand-built nullable-`active` schema (output in §3).
- Old-vs-new table-absent behavior probe (`OperationalError` vs clean allow).
- Read-only live-DB probe under `mode=ro` + `PRAGMA query_only=ON` (`query_only` confirmed `1`): frontier dates, incident-date run counts, table presence.
- `stat` of `trendora.db` / `trendora.db-wal`; `sha256sum` of both iteration-16 artifacts.

---

## 5. Recommended Next Step

**Proceed to the evaluator.** The authorized slice is complete and genuinely verified; the STALLED live-arm sub-step is the anticipated correct outcome and is named honestly in the handoff's status lines.

Carry these forward:

1. **Put B1 in front of the owner as the headline, not the footnote.** The decision now needed is not "shall we arm the boundary" but "the live backend cannot be booted at all without creating the forbidden table and writing a `ScannerRun` for `2026-08-12`." Requirement 1 already rejects "do not boot" as a control, so this is an open safety item under the owner's own standard, and it will keep being open at the start of iteration 18.
2. **Do not cite TC-13's ratio as independent evidence** (D1). `AVB-A` stands on the decision-impact trace — zero percentile shifts, unchanged risk bucket / setup / eligibility across a 2.79× close difference — not on a ratio that is ≈1.0 by construction. If a future iteration wants an independent check, it needs a quantity in which `close_a` does not cancel.
3. **Correct the incident-date set in the QA record** (T1) and stop proving the "untouched journeys" claim with `git diff` alone while most changed files are untracked (T2).
4. **Low-cost hardening for the next iteration that touches these scripts** (B3/T3): a smoke test per evidence script for the `--evidence-dir` refusal branch, plus a guard refusing an `--evidence-dir` that is not this iteration's directory — the iteration-14 failure shape is still reachable, just no longer by default.
