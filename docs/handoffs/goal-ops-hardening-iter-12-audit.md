# goal-ops-hardening-iter-12 Audit Report

**Date:** 2026-07-23
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal — close J-06's two agent-owned evidence gaps (G1 transcription, G2 control re-measurement),
correct iter-11's cache-HIT-only TC-4 audit, and confirm J-05's contract intact — is achieved. G1, the TC-4
correction, and the `data_provider_runs` 120/121/122 / J-05-intact finding were delivered complete and
accurate (I re-verified `forward_testing.py:826`, the three `logs/backend.log` MemoryError tracebacks, the
three DB rows, and the `data_manager.py` aggregate-gating code against the actual sources — all match).
The one material defect — **G2's three control readings were never recorded in the canonical
`reports/perf-budgets.md` the spec/TC-2/goal.md require**, living only in the browser-qa evidence files
(and the browser-qa report even mis-claimed they were already in perf-budgets.md) — I fixed by
transcribing the already-captured readings into that file. Remaining items (golden-replay-lane flake, an
undisclosed working-tree edit to `J-05.json`, the carried-forward J-04 live-crash coverage gap, and the
standing out-of-scope AG-8 MemoryError) are documented and acceptable.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): G2's three control readings were absent from the canonical `reports/perf-budgets.md`**
DEFINITION OF DONE item 2 and TC-2 both require the three `GET /api/indexes?full=true` control readings
"recorded in `reports/perf-budgets.md`", and goal.md's J-06 acceptance treats that file as the sole
canonical home for budgets. The browser-qa Chrome-MCP pass captured all three readings (2257.7 / 2148.2 /
2138.7 ms, each idle-cross-checked) but recorded them **only** in
`reports/qa/goal-ops-hardening-iter-12-evidence/UT-02-reading1.txt` / `UT-03-reading2.txt` /
`UT-04-reading3.txt` and the merged `...ui-test-results.llm.md` (UT-02/03/04). The perf-budgets.md "G2"
section (was lines ~1827-1865) is the developer-pass *preparatory* cross-read only and explicitly states
"G2 is therefore NOT closed by this section." Worse, `...ui-test-results.llm.md:104` asserts "the actual
numbers are recorded in `reports/perf-budgets.md` by the dev handoff" — verifiably false (`grep -n
'2257.7|2148.2|2138.7' reports/perf-budgets.md` returned nothing before this audit). Left unfixed, J-06
could not be scored complete from its own canonical evidence source, which is the entire point of the
iteration.
**Fix applied:** appended a `### G2 (closure)` subsection to `reports/perf-budgets.md`
(new lines ~1866-1905) transcribing all three readings verbatim from the browser-qa evidence files — each
WARN-flagged over the ≤1.5s budget by 757.7 / 648.2 / 638.7 ms, with its `logs/backend.log`
no-concurrent-ingest confirmation and `logs/hwmon/hwmon.csv` load1 (1.48 / 1.63-1.66 / 1.83, all <2.0) /
mem_avail (~18.2-18.8 GB) cross-check at the exact request timestamp. This is transcription of
already-captured evidence, not a re-measurement (no host load, no service action). Verified: transcribed
durations/overages/load1/mem_avail/epochs match the source `UT-0{2,3,4}-reading*.txt` files exactly;
`git diff --stat -- apps/backend apps/frontend` remains empty.

**B2 — OBSERVATION (not fixed — explicit owner decision, out of scope): AG-8 `forward_aggregates` unbounded-load MemoryError reconfirmed live, 3-for-3**
`apps/backend/app/engine/forward_testing.py:826`
(`session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()`) materializes
every `ScannerResult` for any run carrying a forward return at the horizon; on the current DB it aborts
with `MemoryError`. I confirmed the terminal tracebacks: row 120's abort at `logs/backend.log:26920`
(terminates at `forward_testing.py:842` `stock_obs.append`, then cascades to a `GET /api/data` 500), row
121's at `:27185` and row 122's at `:27233` (both rooted at `forward_testing.py:826` → sqlalchemy
`fetchall` → `MemoryError`). All three DB rows (`data_provider_runs` 120/121/122) confirm
`aggregates_refreshed=['coverage','membership_timeline','research_hot_keys','drawdown_expectations']` with
`snapshots_created=0`. This is the critical, explicitly out-of-scope AG-8 owner decision — correctly named,
not fixed. It hard-blocks GOAL_ACHIEVED, but not J-06 or this iteration.

### Frontend Findings

**F1 — GAP (not fixed — carried forward, acceptable): J-04 steps 3-4 (HealthBadge/PreflightBanner live crash) not freshly verified**
UT-12 / UT-13 / UT-14 were SKIPPED because no operator-performed backend restart/crash was available this
session (agents cannot start/stop services; subagent-resume channel broken). Steps 3-4 rest on
"rendering code (`health-badge.tsx`, `preflight-banner.tsx`, `health.py`, `readiness.py`, `main.py`,
`warmup.py`) is `git diff`-empty since commit `d9c5e811`, pre-dating iter-9's accepted verification" —
sound but weaker than the fresh DOM/log proof the other J-04 steps got (steps 5-6 were freshly verified
live via `logs/backend.log` truncation and runs 124/119/114). This is evidence-by-absence, carried forward
unchanged from iter-9/iter-11, not newly introduced. The test plan itself authorizes the SKIP. Acceptable.

### Test Findings

**T1 — GAP (not fixed — framework-maintainer item; LLM evidence credible): deterministic golden-replay lane FAILED, overturned by the LLM lane**
`reports/phase-goal-ops-hardening-iter-12-regression-replay-results.md` records FAIL for J-01/J-03/J-05
("step 02 could not perform fill: `Locator.wait_for` timeout" — a `fill` on `job-start-date`, before any
journey-specific value matters), reconciled as a "golden-script false positive" and overturned by the LLM
browser-qa lane's fresh, DB-cross-checked evidence. The flake characterization is credible: the LLM lane
demonstrably filled that exact field successfully many times the same session (UT-05/UT-06/UT-J-01), so
the step-02 fill-timeout is a harness/timing artifact, not a product regression. The journeys genuinely
pass on independent evidence. This is a recurring, low-severity pattern (this pipeline's automated replay
needing a human/LLM tiebreaker before being trusted) — a framework-maintainer concern, correctly out of a
product iteration's remit; noted, not fixed.

**T2 — GAP (not fixed — do not revert; disclosure-hygiene note): `J-05.json` golden replay script edited in the working tree, undisclosed in the dev handoff**
`runs/goal-session-ops-hardening/journey-scripts/J-05.json` is modified (uncommitted): `default_timeout_ms`
20000→30000, the backfill date 2021-09-15→2025-05-15, and the verify target `/scanner-runs/1193` (`as of
2021-09-15`)→`/scanner-runs/1436` (`as of 2025-05-15`). The dev handoff states "zero source files changed"
and `status.json`'s `changed_files` omits it, so this edit is undisclosed. It is a test fixture (not
product source), and it did **not** rescue the replay (the replay still FAILED on step 02, upstream of the
edited date), so it created no false pass. Updating a stale golden-script date/run-id is legitimate test
maintenance and reverting it would only re-stale the fixture — so I did not revert. Flagged for disclosure
hygiene: fixture edits during a "zero source change" iteration should appear in `changed_files` and the
handoff.

---

## 3. Domain Assessment

The core domain logic under audit this iteration is *evidence correctness*, and it holds up under direct
source verification:

- **TC-4 correction is precise.** `forward_testing.py:826` is exactly the quoted unbounded
  `session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()`; it sits on the
  MISS/compute path inside `compute_forward_aggregates` (def line 781), reached from
  `forward_aggregates_cached` (def line 939) at its line-987 compute call — distinct from the cache-HIT /
  bounded reads iter-11's audit actually examined. Named, not modified (`git diff` on the file is empty).
- **The J-05-intact finding is correct.** `_refresh_ingest_aggregates` appends `latest_snapshot` only
  `if prog.new_snapshot_dates:` and `market_phase` only inside `for d in prog.new_snapshot_dates:`; with
  `snapshots_created=0` on all three rows that list is empty, so both skips are design-consistent, not
  defects. `forward_aggregates` is appended only `if forward_aggregates_warmed`, which a horizon-1
  `MemoryError` (caught, `break`) leaves `False` — precisely why it is absent from every sampled row.
  goal.md's J-05 acceptance names five aggregates; `forward_aggregates`/`drawdown_expectations` are
  J-06-scoped additions (iter-5/iter-7), correctly outside J-05's contract. J-05 is intact.
- **G2's control is now honest and complete.** The three fresh, cache-disabled, idle-cross-checked readings
  land consistently at 2.1-2.3s (43-51% over the ≤1.5s budget), ruling out iter-11's "ambient contention"
  hypothesis for this endpoint. After the B1 fix these are recorded in the canonical artifact, WARN-flagged,
  none omitted or averaged.

Architecture remains local-first and minimal (zero product-source diff), failure handling is explicit
(MemoryError caught per-horizon with honest partial reporting; the over-budget endpoint degrades to an
honest loading state, never a blank/frozen frame), and ambiguous/adverse data is surfaced honestly rather
than smoothed away.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/perf-budgets.md` | Appended a `### G2 (closure)` subsection transcribing the three browser-qa control readings (2257.7 / 2148.2 / 2138.7 ms) with per-reading `logs/backend.log` + `logs/hwmon/hwmon.csv` idle cross-checks, each WARN-flagged over the ≤1.5s budget — recording them in the canonical artifact where DoD item 2 / TC-2 require them (they had existed only in the browser-qa evidence files). Verbatim from `UT-0{2,3,4}-reading*.txt`; no re-measurement, no product-source change. |

Verification of the fix: transcribed durations/overages/load1/mem_avail/epochs match the source evidence
files exactly (cross-checked via `grep`); `git diff --stat -- apps/backend apps/frontend` remains empty;
the transcription is honestly WARN-flagged (introduces no favorable-only or fabricated number). The dev
handoff's claims remain valid — it correctly stated G2 was not closed by the developer pass and remained
browser-qa-agent's pass; this fix closes it in the canonical artifact and does not invalidate any dev
claim.

---

## 5. Recommended Next Step

J-06's G1/G2 gaps and the TC-4 audit correction are now complete and honest in the canonical
`reports/perf-budgets.md`; J-01/J-03/J-04/J-05 are verified still-passing (LLM lane, with the documented
J-04 steps 3-4 code-diff-zero carry-forward). **J-06 may be scored `passing` on this now-complete
evidence.** Proceed to the evaluator, but note that GOAL_ACHIEVED remains hard-blocked by three standing
owner decisions unchanged this iteration: (1) the critical AG-8 `forward_aggregates_cached` →
`compute_forward_aggregates` unbounded-load MemoryError (reconfirmed live 3-for-3, B2); (2)
`HOST_GUARD_REQUIRE_MARKERS`; (3) the J-05/J-06 `demo.sh --session-live` walkthrough (no autonomous
production mechanism). Additionally: the newly-confirmed `GET /api/indexes?full=true` 2.1-2.3s over-budget
endpoint should be added to the backlog as an explicit future target (raise the committed budget to match
reality, or scope a query/endpoint fix). Framework-maintainer follow-ups (T1 golden-replay-lane
reliability; T2 fixture-edit disclosure in `changed_files`) are noted for a maintenance pass, not a product
iteration.
