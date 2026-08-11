# goal-ops-hardening-iter-63 Audit Report

**Date:** 2026-08-11
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's engineering is real, profiled and honestly reported — but **DEFINITION OF DONE item 1
(TC-1, "ZERO polls over 2.0 s") is NOT met** and the dev/review/QA chain says so plainly, so nothing is
being passed off as closed. The audit's own load-bearing finding is elsewhere: **the J-05 golden's
rotation target was consumed by THIS SAME iteration's replay lane** (`scanner_runs.id=2960` for
`2010-11-18`, created `2026-08-11T16:34:50.378Z`, ~50 minutes after the dev pass rotated the golden onto
it) — i.e. the exact verification-substrate defect this iteration existed to remove was live again at
iteration end and would have produced a false FAIL on a required-still-passing journey next round. That
is fixed here (rotated to a live-verified `2010-11-22`), and the record's one unsupported claim (the 52
new `factor_lab_all_warm` breaches called "pre-existing") is corrected. **J-07 must NOT be read as
passing on this round's evidence**: its own acceptance metric measured *worse* than the previous round
(53 breaching polls vs 1), with the cause unattributed.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap, not fixed): TC-1 / DoD item 1 is not met — one 2.420 s `GET /api/health` breach
remains inside `coverage_membership_timeline_refresh`.**
`runs/goal-ops-hardening-iter-63/evidence-drill/reconciliation.md:38` records `2026-08-11T15:55:48.120Z |
200 | 2.420s | coverage_membership_timeline_refresh`, inside the phase's own OPEN/CLOSED span
(15:55:43.907Z → 15:55:50.957Z, same file line 96). The DoD line requires zero. Independently re-derived
from the raw poll log (`tc5-health-poll.csv`, 983 data rows + header = the 984 the reconciler asserts):
max 4.181 s, 53 polls > 2.0 s. The dev handoff ("TC-1 result — read honestly, not as a clean pass"),
`reports/perf-budgets.md` Addendum 29 and the reviewer (`spec_alignment.definition_of_done: partial`,
MINOR issue at `data_manager.py:330`) all state this; no lane over-claimed. **Not fixable inside an
audit**: closing it needs a new profile of `_missing_data_diagnostic` *under live concurrent load* plus
another ~18-minute drill to prove, and it partly hangs on the owner's still-open ≤2 s-applicability
question. Carried, with the dev's own next-step note intact.

**B2 — IMPORTANT (fixed — in the record): "the 52 other breaching polls … are a PRE-EXISTING, well-carried
gap" is not supported by the session's own most comparable measurement.**
Dev handoff ("Known Issues", bullet 2) and Addendum 29 dismiss 52 `factor_lab_all_warm` breaches by citing
Addendum 19 (a different phase, older tree). But Addendum 28 — same reconciler, same 1 Hz poller, same
client ceiling, same host, 7.5 h earlier — explicitly recorded **zero** breaches in that same phase across
its own 561.68 s (`reports/perf-budgets.md:10152`). Re-derived by this audit directly from the two raw
CSVs: iter-61 n=1078, median 0.101 s, p90 0.911 s, p99 1.259 s, max 2.849 s, 66 > 1 s, **1 > 2 s**;
iter-63 n=983, median 0.080 s, p90 1.475 s, p99 3.002 s, max 4.181 s, 160 > 1 s, **53 > 2 s**. The idle
pre-job baselines are equivalent (first-30-poll median 0.011 s vs 0.013 s), so "the host was just busier"
is not evidenced either. This iteration's diff is very unlikely to be the cause (it adds a `time.sleep(0)`
in a phase that CLOSED ~10 minutes before the first `factor_lab_all_warm` breach; zero `research.py` lines
touched) — but "pre-existing" overstates what was measured, and it matters because this is J-07's own
acceptance metric. **Fix applied:** a `Correction (iter-63 audit)` paragraph appended to
`reports/perf-budgets.md` Addendum 29 (the same inline-correction convention Addendum 28 already carries
from the iter-61 audit), plus a corrective bullet in the dev handoff's Known Issues. The measurement
question is recorded as **unattributed / open**, not as a carried-and-understood gap.

**B3 — OBSERVATION: the fix's own added per-row CPU cost is never quantified, and the phase got slightly
slower between the two comparable drills.**
`apps/backend/app/engine/data_manager.py:325-331` adds `_diag_row_count += 1` and a modulo test on EVERY
row of a ~3.1 M-row scan. Measured by this audit (3 runs, best-of): a bare 3.1 M-iteration loop 0.053 s vs
0.259 s with the counter + modulo + `sleep(0)` every 2000 → **≈0.21 s of added CPU** on the phase's
dominant sub-step (isolated `_missing_data_diagnostic` = 1.426 s per Addendum 29). Consistent with the
live phase spans: **6.57 s (iter-61, pre-fix) → 7.05 s (iter-63, post-fix)** — Addendum 29 attributes the
7.05 s entirely to "concurrency-contention overhead" without netting out the fix's own cost. Not a defect
(the trade — more total CPU for shorter uninterrupted GIL holds — is the point of the construct), but the
next iteration should know a cheaper form exists: SQLAlchemy's `Result.partitions(size)` yields whole
chunks, giving the SAME chunk-boundary hand-off with **no per-row branch at all**.

**B4 — GAP: the spec's named error case was never exercised.**
TESTING REQUIREMENTS names `TRENDORA_FAULT_INJECT_MEMORY_ERROR=coverage_membership_timeline` as a
regression re-check. It was not re-run live (dev handoff lists no such run; browser-qa recorded J-07
step 4 as "NOT re-run this pass" for the fourth consecutive iteration), and it has no unit coverage:
`apps/backend/tests/test_ingest_finalize_fault_injection.py` contains zero occurrences of
`coverage_membership_timeline`. Risk is low — the probe site (`data_manager.py:4319`) and both `except`
handlers (`:4340-4346`) are untouched by this diff — and the file's 5 sibling tests pass (`5 passed in
0.90s`, run by this audit), but the named check was skipped rather than executed.

### Test-infrastructure Findings

**T1 — CRITICAL (fixed): the J-05 golden's rotation target was consumed by this same iteration's replay
lane; the next replay would have reported a false FAIL on a required-still-passing journey.**
(I weighed IMPORTANT vs CRITICAL and chose the higher: this defect class is one of the two things the
iteration's own GOAL statement exists to remove — "before they produce a false regression halt next
round" — and its recurrence re-arms exactly that halt on a currently-`passing` journey.)
Verified by direct read-only sqlite query, not from any lane's prose:
`scanner_runs` → `id=2960, asof_date=2010-11-18, created_at=2026-08-11 16:34:50.378326`. The creator is
this iteration's own deterministic replay lane: `runs/goal-session-ops-hardening/engine.log:10692-10693`
shows `17:33:58 [replay-lane] Waiting for backend readiness …` / `backend readiness == ready (0s)` (local
BST = 16:33:58Z), and the J-05 replay's backfill landed the snapshot 52 s later. `J-05.json` step 10
asserts `"1 calendar day · 0 already snapshotted · 0 non-trading"` — an assertion with teeth, which would
have rendered `1 already snapshotted` and FAILED on the next run.
**Fix applied:** rotated steps 2/3 (fill targets), steps 13/14 (goto-expect text, click target, and the
`Immutable snapshot — as of …` expect) and the journey `name` to `2010-11-22`, live-verified immediately
before the edit (`scanner_runs` 0 rows; `daily_prices` 467 bars; real SPY close 92.7195 — a genuine
trading day). `2010-11-19` is also off-limits (`scanner_runs.id=2959`, the dev pass's own TC-1 drill).
Dated rotation-history entry appended to `_notes` per the file's convention. Post-fix verification:
`demo_runner.py --mode lint --journeys J-05,J-07` → `J-05 ok / J-07 ok`; JSON re-parsed (15 steps, 5
occurrences of the new date in `steps`, 0 of the old).
**Structural note (not fixed — out of an audit's surgical scope):** this is the FOURTH consecutive
rotation consumed by the round that set it (iter-58, iter-59 ×2, iter-62/63, iter-63-audit). Hand-rotating
a date in a checked-in golden cannot hold while the same golden is replayed every round. The durable fix
is for the lane to select-and-persist a fresh unsnapshotted trading day at replay time (or to rotate the
golden immediately AFTER consuming it). Recommended as the next iteration's test-infrastructure item.

**T2 — GAP: the replay-lane readiness gate is correct and now behaviorally proven, but its 60 s budget is
the same order as the warm-up window that caused the incident it fixes.**
The reviewer's open NOTE ("syntax-checked and code-reviewed but not exercised") is **closed by this
audit**: the helper was extracted verbatim (`sed -n '/^_wait_for_backend_readiness() {/,/^}/p'`) and run
against local stub health endpoints — (a) `readiness:"initializing"` → blocked the full 9 s budget, logged
the warning, returned 1; (b) `readiness:"ready"` → returned 0 in 0 s; (c) empty URL → immediate 0 no-op;
(d) dead port → warned at the budget, returned 1. It never hangs and never hard-fails, exactly as
documented. It also fired for real this round (`engine.log:10692`) and all 7 required journeys replayed
PASS. **The gap:** the iter-62 incident had the lane starting ~60 s after boot with J-04 step 2 (a 20 s
`wait_for` on `[data-state="ready"]`) still failing — i.e. readiness was not ready ~80 s after restart —
while the new gate's default budget is 60 s (`common.sh:1434`, `replay-lane.sh:341`) and
`CHAIN_BACKEND_READY_WAIT_S` is set **nowhere** in the tree. On the same shape of incident the gate can
expire and proceed, and the false FAIL recurs. The sibling frontend gate already uses 90 s. Cheap
follow-up: raise the default (the gate returns instantly when the backend IS ready, so a larger budget
costs nothing in the common case). TC-4's exact reproduction (lane invoked within 60 s of a restart with a
genuinely NOT-ready backend) was still never executed end-to-end.

**T3 — GAP: the showcase demo lane launched a real, unrequested 5-date ingest that is still running.**
`reports/phase-goal-ops-hardening-iter-63-demo-results.md` records steps 03/04 as
"couldn't perform fill (unresolvable target …job-start-date/job-end-date)" — and step 05 clicked **Start**
anyway. The live consequence, read from the DB: `data_provider_runs.id=420`, `provider=seed`,
`status=running`, `started_at=2026-08-11T17:21:00.333Z`, message `{"kind":"backfill","start":
"2005-06-24","end":"2005-06-30","dates_total":5,"dates_done":0,…}` — still running 10.8 minutes later at
17:31:51Z, during this audit. A non-blocking showcase lane is therefore mutating the dataset every round
(each new snapshot date invalidates the dataset version and forces the whole finalize tail to re-warm),
which is (i) the same per-round ingest cost the session already has flagged as owner-gated for the replay
lane, and (ii) a live candidate cause for B2's unexplained baseline drift. A demo step whose precondition
failed should not proceed to the Start click.

### Test Findings

**TQ1 — OBSERVATION: the new byte-identity test proves less than its docstring claims.**
`apps/backend/tests/test_data_manager.py:6056-6112`. The docstring says the post-fix payload is compared
to "a PINNED pre-fix reference oracle … replicated here exactly as it ran before this iteration". What is
actually asserted is `diag_tiny_batch_with_yield == diag_default_batch` — post-fix code at
`read_batch_size=2` (yield fires 5×) vs post-fix code at the default 2000 (11 rows never reach a chunk
boundary, so the yield never fires). That IS a real differential (yield-fired vs yield-never-fired) and it
would catch a row-dropping or reordering regression, so the DoD's substance holds — but it is not a pinned
oracle. The `reference_dates` dict built from `.all()` is computed and then used only for
`assert sum(len(v) …) == 11`; its grouping — which the docstring calls point 1 — is never compared to
anything. Also, `monkeypatch.setattr("app.engine.data_manager.time.sleep", …)` patches the attribute on
the global `time` module (the module is imported, not aliased), not a module-local symbol; harmless here,
worth knowing. Verified green by this audit: `pytest tests/test_data_manager.py -k "diag" -q` →
**9 passed in 2.01 s**.

### Frontend Findings

None. The only frontend touch is the TC-6 header-comment correction in a non-shipping test file
(`apps/frontend/lib/data-overview-refresh.test.ts:1-12`); re-run by this audit:
`npx tsx lib/data-overview-refresh.test.ts` → **3 passed**.

---

## 3. DEFINITION OF DONE — item-by-item

| # | DoD item | Verdict | Evidence |
|---|---|---|---|
| 1 | TC-1 drill records ZERO polls > 2.0 s, reconciled | **NOT MET** | Full trace (risk + own leads): B1 — one 2.420 s breach, `reconciliation.md:38`; 983 rows reconciled against `wc -l` 984 |
| 2 | Bounded construct byte-identical to reference (TC-2/TC-5) | MET (caveat TQ1) | Full trace: diff is scheduling-only (`data_manager.py:325-331`, query/WHERE/order untouched); 9 diagnostic tests re-run by audit, 9 passed |
| 3 | `J-05.json` rotated off its consumed date, closing steps correct | **NOT MET at audit start → FIXED** | Full trace: T1 — `scanner_runs.id=2960` for `2010-11-18` created 16:34:50Z by this round's own replay; rotated to `2010-11-22`, lint `J-05 ok` |
| 4 | Replay lane no longer false-FAILs after a restart (TC-4) | PARTIALLY MET | Full trace: T2 — gate placed correctly before `_replay_lane_verify_once` (`replay-lane.sh:341`), behaviorally proven by audit (4 cases), fired live; exact reproduction never run, 60 s budget vs an observed >80 s window |
| 5 | `data-overview-refresh.test.ts` header documents the working command (TC-6) | MET | Mechanical — reviewer PASS (no issue filed) + QA report Step 3 row (3/3 checks); audit re-ran it: 3 passed |
| 6 | J-01, J-03, J-04, J-05, J-06, J-08, J-09 pass via replay + LLM fallback | MET | Mechanical — `…-regression-replay-results.md` 7/7 PASS; merged `…-ui-test-results.md` 8/8 incl. UT-J-07. (J-05's PASS is what consumed the golden's date — see T1) |
| 7 | No anti-goal violation (AG-3/5/8/9/10) | MET | AG-3/AG-5: no displayed value or date logic touched (3-line scheduling diff); AG-8: query unchanged, still `.yield_per`-streamed — no new whole-table load; AG-9: `data_provider_runs` 417-420 all `provider='seed'`; AG-10: `git status` clean for `config.yaml` and `project-extensions/host-guard/host-guard.env` |
| 8 | Unit tests pass; no regressions | MET | Audit-run: 9 diagnostic + 5 ingest-finalize fault-injection passed; QA row: `test_universe_resolver.py` 26 passed; dev's 218-pass run re-verified by the reviewer; the `test_no_magic_numbers` failure was confirmed pre-existing via `git stash` |
| 9 | Dev handoff written | MET | `docs/handoffs/goal-ops-hardening-iter-63-dev.md` (amended by this audit where its claims were invalidated) |

---

## 4. Domain Assessment

The domain work is sound and the discipline the spec demanded was actually followed. The fix was applied
*after* a stack-sampling profile, not force-fit from the session's prior constructs, and the profile ruled
OUT the two candidates the plan named first (`resolve_with_reasons`, `_trading_days`) rather than
confirming a guess. The stall location it did find is credible and I verified the call chain independently:
`_refresh_ingest_aggregates` → `refresh_coverage_snapshot` (`data_manager.py:4320`) →
`_compute_coverage_uncached` → `_compute_coverage_body` → `_missing_data_diagnostic`
(`data_manager.py:1260`) — the fix is genuinely inside the phase it claims to bound, not adjacent to it.
The profiling environment's 18-200× wall-time distortion is disclosed in the addendum rather than papered
over, and only the stall LOCATION is treated as signal — the right call.

The correctness bar is met: the change adds no query, no filter, no ordering, and cannot alter
`own_dates_by_symbol`; `read_batch_size` is validated `>= 1` (`app/config.py:1410-1411`), so the modulo can
never divide by zero. Determinism and no-lookahead (AG-5) are untouched by construction.

Where the domain reasoning is weaker is attribution, and it is worth naming precisely because the rest is
so careful: the headline "2.849 s → 2.420 s, ~50 % overage reduction" is **one poll from one run compared
to one poll from another run**, and the same pair of runs shows the phase itself getting *slower*
(6.57 s → 7.05 s) and the endpoint's whole-run tail getting dramatically worse (p99 1.259 s → 3.002 s).
The fix is defensible on mechanism; it is not yet demonstrated on measurement. J-07's promise — "health
stays responsive throughout ingest" — measured worse this round than last, and no one has yet explained
why.

---

## 5. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `runs/goal-session-ops-hardening/journey-scripts/J-05.json` | Rotated the consumed target `2010-11-18` → live-verified `2010-11-22` in steps 2/3, 13/14 and the journey `name`; appended a dated rotation-history `_notes` entry incl. the structural recommendation. Verified: live sqlite (0 `scanner_runs` rows, 467 bars, SPY 92.7195), `demo_runner.py --mode lint` → `J-05 ok`, JSON re-parse (5 new-date occurrences, 0 old) |
| 2 | Important | `reports/perf-budgets.md` (Addendum 29, appended) | `Correction (iter-63 audit)`: the 52 `factor_lab_all_warm` breaches are NOT established as pre-existing — Addendum 28 measured zero in that same phase; re-derived distribution stats for both drills; cause recorded as unattributed/open |
| 3 | Important | `docs/handoffs/goal-ops-hardening-iter-63-dev.md` | Two Known-Issues bullets updated where the audit invalidated their claims (the `2010-11-18` re-verify instruction is superseded; the "pre-existing" characterization is corrected), each pointing at the evidence |

No product code was changed by this audit.

---

## 6. Recommended Next Step

Do **not** promote J-07 on this round's evidence. The next iteration should, in priority order:

1. **Make the J-05 golden self-rotating** (lane selects and persists a fresh unsnapshotted trading day at
   replay time, or rotates immediately after consuming). Four consecutive hand-rotations have now been
   eaten by the round that set them; the fifth will be too. (T1)
2. **Explain the 1 → 53 breach change** before doing any more latency work on this surface: re-run the
   drill on the current tree with no code change and compare against Addendum 28/29 — that single control
   run distinguishes "dataset growth / host contention" from "a real regression nobody has attributed".
   (B2)
3. **Profile `_missing_data_diagnostic` under live concurrent load** (a probe thread alongside the real
   health poller + job, not an isolated call), and prefer `Result.partitions(size)` over the per-row
   modulo so the chunk-boundary hand-off costs nothing per row. (B1, B3)
4. Cheap hygiene, if a slot exists: raise the readiness gate's default budget past the observed
   post-restart warm-up window (T2); stop the demo lane from clicking Start after its own fill steps fail
   (T3); add a `coverage_membership_timeline` case to `test_ingest_finalize_fault_injection.py` (B4).

The owner's one-sentence policy question (does the ≤2 s ceiling apply to a 15-23-minute background window,
or only the "order ~30 s" window the amendment describes) is now **more** load-bearing than the iteration
assumed, not less: the fix did not make the answer moot, and this round's 53 breaches make the answer
decisive for whether J-07 can ever be marked passing.
