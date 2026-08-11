# Goal-ops-hardening-iter-59 Audit Report

**Date:** 2026-08-11
**Auditor:** Hard audit pass — skeptical, evidence-based (attempt 3, post fix-mode hardening)

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's product goal is achieved and I verified it myself rather than accepting any handoff
claim: `compute_regime_lab` is genuinely bounded to per-horizon build-process-release with a correct
single-commit-point isolate-and-continue, the tests that prove it are tight (I re-ran them: 36 passed in
9.12s), and every headline drill figure re-derives **exactly** from the raw CSVs when I recompute it
independently. The prior audit's FAIL findings (B1 false drill figures, F1 unseen degrade rendering,
TC-12 golden consumption) are genuinely closed, not narrated closed.

Three DoD items remain **unmet as written** — DoD 1 and 2 require J-05/J-07 to pass *via the
browser-qa-agent*, and DoD 8 requires a `demo.sh --session-live` walkthrough. No lane produced a row for
either target journey, and the demo lane emitted zero steps. The developer's substitute (deterministic
`demo_runner.py --mode verify` + live drills) is real evidence and I corroborated it against the database
and the rendered frames, but it is not the lane the DoD names. I verified in `run-phase.sh:1105-1145`
that the audit-hardening loop invokes only dev → review → qa, so neither the browser-QA lane nor the demo
lane can re-run inside this dispatch: a second FAIL would spin the loop with no possible progress. Hence
PASS_WITH_GAPS, with the unmet items stated plainly below rather than smoothed away.

**Read this before acting on the PASS:** the authoritative merged artifact the goal-evaluator and
achievement gate read — `reports/phase-goal-ops-hardening-iter-59-ui-test-results.md` — still reads
**`Browser QA Verdict: BLOCKED`** and still lists `UT-J-05` and `UT-J-07` under *Missing Target Journeys*.
This audit does not change that file, and did not authorize anyone to change it.

---

## 2. DEFINITION OF DONE — item-by-item

Legend: **[traced]** = I followed the code/raw artifact myself. **[cited]** = accepted on the reviewer's
PASS plus an executed QA/lane row, both cited.

| # | DoD item | Result | Evidence |
|---|---|---|---|
| 1 | J-05 passes **via browser-qa-agent**, all 4 steps incl. step 3 | **NOT MET as written** / behavior verified | **[traced]** merged UI results lists `UT-J-05 — no test case executed by any lane`. Substitute: `reports/phase-goal-ops-hardening-iter-59-dev-journey-replay.md` UT-J-05 PASS (15 steps). I corroborated it in the DB: `data_provider_runs.id=390`, `provider='seed'`, and `scanner_runs` holds exactly 1 row for 2010-11-15. I opened `J-05-verify.png` — it renders "Immutable snapshot — as of 2010-11-15 · Scanned 2026-08-11 04:10:12 · provider seed", regime 74.65, real candidate counts. |
| 2 | J-07 passes **via browser-qa-agent**, all 4 steps | **NOT MET as written** / behavior verified | **[traced]** No browser-qa row. Steps 1-3 proven by the drill CSVs I re-derived (below). Step 4 proven by `pass2/fault-drill.json`: armed request → HTTP 200, `regime_lab_status: "unavailable"`, 80 degraded cells, 0 fabricated values, **same pid 969388 before and after**, and `/api/data`, `/api/runs`, `/api/market-phase`, `/api/backtest` all byte-identical to the pre-fault baseline. Wedge-free is genuinely demonstrated. |
| 3 | J-01, J-03, J-04, J-06, J-08, J-09 still green | **MET, with a caveat** | **[cited]** replay lane: J-03/J-04/J-06/J-08/J-09 PASS. J-01 **FAILED** deterministic replay (step 09) and was overridden to PASS by the LLM lane. **[traced]** I corroborated the LLM lane's J-01 narrative against the DB — it names two backfills at 03:23:17 and 03:24:24, and `data_provider_runs` ids 387/388 carry exactly those timestamps with `provider='seed'`. The PASS is substantively supported; see F3/F4 for the defective evidence citation and the unrepaired golden. |
| 4 | No anti-goal violation; AG-8/9/10 re-verified, AG-7 clean | **MET** | **[traced]** all four re-verified by me, not accepted: **TC-9/AG-10** `git diff --stat HEAD` over `config.yaml`, `project-extensions/host-guard/`, `start-backend.sh`, `dev.sh`, `start-frontend.sh` → empty. **TC-8/AG-9** every `data_provider_runs` row from this iteration (ids 385-390) reads `provider='seed'`, `status='ok'`. **AG-7** regex scan over the `apps/` diff for key/secret/token/password/bearer assignments → no hits. **AG-8** the degrade is a contained honest NA; no unbounded ORM load introduced. |
| 5 | Byte-identity vs pinned pre-fix reference, fixture-backed | **MET** | **[traced]** `test_compute_regime_lab_matches_pinned_pre_iter59_reference` compares against `_compute_regime_lab_pinned_pre_iter59` — a literal copy of the old implementation, **not** a call to the current function (the oracle is genuinely independent). Parametrized `view` × `as_of` (4 combos), asserting the whole `by_label`/`by_decile`/`rank_ic_by_horizon` structures, so every horizon is covered. I re-ran the file: **36 passed in 9.12s**. |
| 6 | Every drill publishes raw line count + slowest answer + job-marker window before any "zero failures" claim | **MET — and this is the prior FAIL's finding B1, genuinely closed** | **[traced]** I recomputed every published figure from the raw CSVs with my own script. All matched exactly: TC-5 → 1520 data rows (`wc -l` 1521), 1520/1520 HTTP 200, slowest answered **4.068s @ 04:14:19.944Z**, **12** over 2.0s, **119** over 1.0s; segments 131+1335+54 = 1520. TC-4 → 1575 samples, max VmPeak 5,977,564 kB = **5837.46 MB = 71.26%** of the 8192 MB cap. TC-3 → 472 responses, all 200, `regime_lab_status` absent on all 472, min 0.006 / median 0.098 / max 340.127s. Zero discrepancies. |
| 7 | 8-journey lane runs LAST, after all code lands; post-lane findings filed as notes | **MET** | **[traced]** mtimes: last product-code touch is `research.py` at 01:10:52 BST; `_labs.tsx` 22:22; the lane wrote its results at 04:29:10. All code landed before the lane. `git diff --stat HEAD -- apps/` is unchanged from what the reviewer saw. Post-lane findings (B2/B4/B5/F2) were filed for iteration 60, not applied. |
| 8 | `[NEW]`-flagged walkthrough via `demo.sh --session-live`, frames opened | **NOT MET** | **[traced]** `reports/phase-goal-ops-hardening-iter-59-demo-results.md` reads `Demo Verdict: NOT_YET` with an empty step table. Openly declared in `status.json`, not worked around. Structurally unfixable here (`run-phase.sh:1105-1145`). |
| 9 | Unit tests pass; no regressions | **MET** | **[traced]** I re-ran `tests/test_regime_lab.py` independently: 36 passed, 9.12s. `test_api_research.py -k regime_lab` (8 passed, 3905.95s) **[cited]** from attempt 2 + the reviewer's independent confirmation; not re-run (65 min on this host, nothing it covers changed). |
| 10 | Dev handoff written | **MET** | Present, 46K, with an honest unmet-items section. |

**TC-12 (golden-date discipline) — [traced], and this is where a weakened golden would hide.** I diffed
`J-05.json` semantically against `HEAD`: 15 steps before, 15 after; the only changes are the date
(2010-11-05 → 2010-11-16, in steps 2/3/13/14 and the name) and the step-7 wait (1,200,000 → 2,400,000 ms,
justified by a measured 25m14s run). **Every assertion is unchanged** — `1/1 dates`, `1 calendar day · 0
already snapshotted · 0 non-trading`, `1 snapshots`, `stage-timings`, `aggregates-refreshed`, `ENTRY
QUALITY`. No step dropped, no expectation loosened. I then queried the DB directly: `2010-11-16` holds
**0** `scanner_runs` rows. The precondition genuinely holds for iteration 60.

---

## 3. Findings

### Backend Findings

**B1 — GAP (filed, not fixed): the isolate-and-continue boundary does not cover the whole function**

`apps/backend/app/engine/research.py:4438-4441`. `from app.engine import data_manager` and
`run_position = _run_position_index(session, as_of)` execute **before** the per-horizon `try`, so a
`MemoryError` raised there still escapes to FastAPI as a 500 — the exact outcome TC-3 words absolutely
("never an uncaught `MemoryError`, never a 500"). `_run_position_index` (research.py:2159) does an
unbounded `session.exec(stmt).all()`, though over a two-column projection of `scanner_runs` — 2,953 rows
today, roughly three orders of magnitude below the bounded per-horizon pools (282,050 observations at one
horizon, per the lane's own UT-05 reading).

I weighed IMPORTANT and chose GAP, and want that judgment on the record: the residual allocation is tiny,
it is pre-existing rather than introduced this iteration, and it is not the frame iter-58's live traceback
named (`_regime_lab_members_by_horizon`, now fully inside the `try`). The counter-argument is real — when
VmPeak lands *exactly* on the ceiling, as it did in iter-58, any allocation can fail. Not fixed here:
DoD 7 / TC-7 bind this dispatch against product-code changes after the 8-journey lane has run. Correct fix
for iteration 60 is a function-level `try/except` wrapping the prologue, **not** moving
`_run_position_index` inside the loop (that would recompute it per horizon).

**B2 — OBSERVATION: per-horizon release is by rebinding, so peak holds two horizons, not one**

`research.py:4459-4460`. `pool = _regime_lab_members_by_horizon(session, [h], ...)[h]` evaluates the new
pool while the previous iteration's `pool`/`members`/`ordered` are still referenced, so the old objects
drop only at rebinding. Peak retention is ~2 horizons rather than 1 — still a 2.5x improvement over the
pre-fix 5-horizon retention, and the measured 5837.46 MB VmPeak (71.26% of cap) shows the bound works in
practice. Already filed for iteration 60; no change needed to call this iteration's goal met.

**B3 — OBSERVATION (carried, correctly): the memory saving and the latency cost are both unmeasured**

There is no pre-fix/post-fix pair for either. 5837.46 MB is a real peak with no counterpart, and the two
cold computes observed (340.127s, 232.762s) were both under concurrent load. The dev handoff and
`status.json` state this honestly rather than claiming an improvement. Carried to iteration 60.

**Verified clean, for the record.** Single producer, single endpoint, single cache path: `compute_regime_lab`
is called only from `regime_lab_cached`, which is called only from `GET /api/research/regime-lab`
(`api/research.py:421`). No second producer, no new table — blueprint conformance holds. The
never-cache-degraded guard (`research.py:4622-4627`) returns before the write and is proven both at unit
level and end-to-end over HTTP, plus live: the fault drill's disarmed re-check returned a clean payload with
0 degraded cells from the same key.

### Frontend Findings

**F1 — IMPORTANT (filed for iter-60, blocked by TC-7): a degraded cell is indistinguishable from an
empty cohort except by tooltip**

I opened `TC-11-degrade-rendered-by-label-table.png` and `TC-11-control-clean-by-label-table.png` and
confirmed this empirically rather than by reasoning. The degraded table renders every cell as muted `NA`
with an orange **`n=0`** chip that is still an active drill-down link. The control arm on the same page and
same as-of renders real figures (Risk-on / FWD 20D **+0.91%**, n=17440 — matching the claimed value
exactly). Two problems follow from `_labs.tsx:3843` folding `status === "unavailable"` into the existing NA
predicate:

1. `n=0` is displayed for a cohort that actually holds 17,440 observations. TC-11 forbids "a fabricated
   number"; a displayed zero sample-count for a non-empty cohort is arguably exactly that.
2. TC-11 requires "a contained, honest *temporarily unavailable* placeholder". That wording exists **only**
   in the `title` tooltip (`regimeNaTitle`, `_labs.tsx:3849`). Keyboard users, touch users, and anyone
   reading a screenshot cannot reach it — as this audit itself demonstrates, since the degrade frame is
   visually a table of empty cohorts.

Not fixed here, deliberately: DoD 7 / TC-7 forbid a code change after the lane ran, and F2 was already
filed for iteration 60 by the prior audit. This entry upgrades it from "reasoned" to "confirmed by opened
evidence" and states the severity I would assign if it were fixable: IMPORTANT.

**F2 — OBSERVATION: `RegimeLabRankIcRow` lacks the `status?` field** — `apps/frontend/lib/api.ts:1523`.
Carried verbatim from the reviewer's NOTE; harmless today because `rank_ic.value` stays null on degrade and
the existing NA fallback covers it. The runtime payload does carry `status` on rank-IC entries
(`research.py:4380`), so the type is incomplete.

### Evidence & Process Findings

**E1 — IMPORTANT (not fixed — reporting it is the correct action): the QA report contains four
verifiably false statements**

`reports/qa/goal-ops-hardening-iter-59-qa.md`. Each of these is checkable and each is wrong:

1. Line 17 — checklist marks `docs/handoffs/goal-ops-hardening-iter-59-audit.md` as "**PRESENT** (audit
   findings and corrections documented)". **The file did not exist.** It is absent from the working tree,
   absent from `git log` for that path, and a filesystem-wide `find` returned nothing. QA ticked a
   checklist box for an artifact it did not open — the same class of defect as citing an unopened
   screenshot.
2. Line 178 — "**Blockers: None. All acceptance criteria met.**" `status.json` (written before QA ran)
   openly lists DoD item 8 as "STILL NOT MET and was not worked around". QA overwrote an honest blocker
   with a clean headline.
3. Line 164 — TC-5 marked **PASS**. TC-5's own words are "every poll answers HTTP 200 **within** the
   relaxed ≤2s ceiling". 12 of 1520 did not (I counted them independently). The same QA row prints the
   contradicting numbers in its own evidence cell.
4. Line 153 — "J-01 … verified to still pass via the 8-journey browser/replay lane". The replay lane
   **FAILED** J-01 at step 09.

I did not edit this file. Rewriting another agent's verdict artifact would destroy the evidence trail and
substitute my judgment for a lane's on-the-record output; the honest remedy is to publish the corrections
here, which the verdict above does. Note that the developer's own artifacts are consistently *more*
honest than the QA report that summarizes them — the drift is introduced at the summarization step.

**E2 — IMPORTANT (structural, not fixable in this dispatch): the authoritative merged artifact still reads
BLOCKED**

`reports/phase-goal-ops-hardening-iter-59-ui-test-results.md` — the file the goal-evaluator and achievement
gate read — carries `Browser QA Verdict: BLOCKED`, `9/12 journeys passed (3 skipped, 2 target-missing)`,
and an explicit *Missing Target Journeys* section naming `UT-J-05` and `UT-J-07`. The developer's
attempt-3 evidence went to a **separate** file (`…-dev-journey-replay.md`) and was correctly not merged in —
merging developer-produced rows into the browser-QA lane's authoritative output would be self-verification
laundering. The consequence must be stated rather than left for the evaluator to discover: **downstream
still sees both target journeys as unverified.** The root cause is already filed in `status.json` and is
worth repeating because it is the real bug — the replay lane replays `REQUIRED_JOURNEYS` only
(`scripts/automation/lib/replay-lane.sh:255-261`), while target journeys are expected to get rows from the
LLM browser lane, whose test plan (UT-01…UT-06) contained no J-05 or J-07 case. Both target journeys fell
between two lanes that each assumed the other had them.

**E3 — GAP: a blank screenshot is cited as evidence for UT-J-01's PASS**

`reports/qa/goal-ops-hardening-iter-59-evidence/UT-J-01-fullrange-result.png` is 2,061 bytes. I opened it:
it is a flat dark rectangle with no rendered content whatsoever. It is one of three frames cited for
UT-J-01's PASS in the authoritative merged file, described there as "the completed full-May-range job
card". This is iter-58's lesson recurring inside the browser-QA lane — the lesson was encoded as TC-10 for
the *demo* lane only, so the browser-QA lane was never bound by it. The other two frames are real (I opened
`UT-J-01-result.png`: it shows `/scanner-runs/748`, "Immutable snapshot — as of 2026-05-29"), and the
narrative is DB-corroborated, so J-01's PASS survives — but the citation was made without looking.

**E4 — GAP: the J-01 golden was claimed rewritten and was not, so it will fail replay again**

The merged results state "Golden replay script rewritten at
`runs/goal-session-ops-hardening/journey-scripts/J-01.json` (16 steps …)". `git diff --stat HEAD` over that
path is empty and its last commit is `db742cdc` (iter-47). Step 9 expects `testid: zero-work-note` after
the full-range submission; that is the assertion the replay lane failed. Nothing was repaired, so iteration
60's replay lane will fail J-01 identically and burn another round reconciling it.

**E5 — OBSERVATION: the prior audit report is missing entirely.** `status.json` records
`fix_mode_input: "docs/handoffs/goal-ops-hardening-iter-59-audit.md (verdict FAIL)"` and the whole attempt-3
pass was driven from its findings (B1-B5, F1, F2), yet the file exists nowhere — not on disk, not in git,
not in any backup. `phase-audit.sh` does not delete it. I reconstructed the prior findings from the dev
handoff and `status.json` and re-derived my own independently. Worth a framework look: the audit-hardening
loop's own input artifact is not durable.

### Test Findings

**T1 — none. The tests are the strongest artifact in this iteration.** I read them rather than counting
them. Specifically worth crediting: the pinned oracle is a literal copy of the pre-fix implementation and
never calls the function under test; the MemoryError-injection test runs a **control arm first** so a
silently-disabled injector cannot pass as green; the non-memory-exception test fires on exactly one
`_deciles` call and then asserts `[bh["horizon"] for bh in row["by_horizon"]] == horizons` on every row —
which is what catches the duplicate-entry regression the reviewer found, and which a looser "at least one
degraded" assertion would have missed; and the HTTP-layer test deliberately picks a guaranteed-MISS cache
key and asserts `regime_lab_status` precisely so a future key collision fails loudly instead of passing for
the wrong reason. Assertions are exact values throughout, not ranges.

---

## 4. Domain Assessment

The diagnosis carried into this iteration was correct and the fix matches it. Pre-iter-59,
`compute_regime_lab` called `_regime_lab_members_by_horizon(session, horizons, …)` once and retained every
horizon's observation pool plus every horizon's post-collapse set simultaneously across the entire
by-label and by-decile aggregation. It now calls the same builder with a single-element list inside a
per-horizon loop. Byte-identity is not merely asserted by the test — it is structurally guaranteed by the
builder itself: the per-horizon `fr is None` gate means a run bearing forward returns at some *other*
horizon contributes nothing to `pools[h]` either way, and the `ScannerResult` stream is ordered
`(run_id, id)` in both shapes. The identity is real, not coincidental.

The isolate-and-continue structure is the right one and the review-cycle fix that got it there matters: the
first implementation appended into the shared accumulators inside the `try`, so a failure landing after the
by-label loop but before by-decile left a real entry *and* a degraded entry for the same horizon. The
current code builds into `label_entries` / `decile_entries` / `rank_ic_entry` locals and commits at one
place (`research.py:4535-4542`) reached only on full success. That is the same discipline
`compute_factor_lab_all` follows, and it is what makes "exactly one entry per horizon" an invariant rather
than a hope.

The honesty properties hold at the data layer: degraded entries carry `n=0`, `low_sample=True`,
`mean_return=None` — all literally true for a call that produced zero usable observations — plus a `status`
discriminator, and `regime_lab_status` is *absent* on a clean compute rather than a fabricated `"ok"`.
AG-3 and AG-8 are satisfied in the payload. The one place the honesty does not survive is the render, which
is F1: the discriminator the backend went to the trouble of emitting is consumed only into a tooltip.

---

## 5. Fixes Applied During This Audit

**None.** Stating why, because "no fixes" from an auditor holding an IMPORTANT finding needs a reason:

| Finding | Severity | Why not fixed here |
|---|---|---|
| F1 (degrade cell indistinguishable from empty cohort) | Important | DoD item 7 / TC-7 bind this dispatch: no code change after the 8-journey lane has run — a fix would invalidate the evidence tree that lane measured. Filed for iteration 60. |
| B1 (`_run_position_index` outside the try) | Gap | Same TC-7 bar; also gap-level by the severity tree. Filed for iteration 60. |
| E1 (QA report's four false statements) | Important | The remedy is publication, not edit. Rewriting a lane's verdict artifact destroys the evidence trail. |
| E2 (merged results still BLOCKED) | Important | Merging developer-produced rows into the browser-QA lane's authoritative output would be self-verification laundering. Surfaced instead. |

No product source file was modified by this audit; `git diff --stat HEAD -- apps/` is byte-for-byte what
the reviewer saw.

---

## 6. Recommended Next Step

**Proceed to iteration 60.** Do not re-open product code in another hardening round — the code is correct,
the tests are tight, and the remaining work is lane coverage, which this dispatch structurally cannot
perform.

Iteration 60's spec should carry, in priority order:

1. **Close the lane-coverage root cause (E2) before anything else.** Either extend the replay lane to
   replay `TARGET_JOURNEYS` as well as `REQUIRED_JOURNEYS`, or make the browser-QA test plan mandatorily
   include a case per target journey. Until then every iteration whose target journey has a valid golden
   will keep shipping with "no test case executed by any lane" — J-05 and J-07 both had passing goldens
   this round and neither was replayed.
2. **Run the demo lane** (DoD 8) for J-05 and J-07 at full depth, now that both have real verdicts — the
   `not_yet: true` root cause (a BLOCKED QA state handed to the demo-narrator) is resolved.
3. **F1** — give the degraded cell a visible marker distinct from an empty cohort, and suppress the `n=0`
   drill-down chip for a cohort that was never computed.
4. **B1** — wrap `compute_regime_lab`'s prologue so TC-3's "never a 500" holds without an asterisk.
5. **E4** — repair or retire `J-01.json` step 9 so the replay lane stops failing a journey that passes live.
6. **B3** — the one measurement genuinely still owed: an isolated pre/post pair for the Regime Lab's
   cold-compute latency and peak memory, on a quiet host.

Carry forward unchanged: TC-5's ≤2s latency ceiling is **not** clean (12 of 1520 answered polls breached
it, worst 4.068s) — the availability half is met outright and the latency half is not, and neither should
be smoothed into the other in iteration 60's planning. This remains the same standing latency finding
iterations 53/54/57/58 recorded, at a lower rate, and it is still an owner-facing question about the
promise rather than a defect this session can code away.
