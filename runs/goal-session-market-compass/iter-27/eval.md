# Iteration 27 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The one job asked for was done, and it works. Before this round, a saved briefing whose source
run had been deleted could never say so: opening the page quietly rebuilt the missing run first,
so the screen could only ever say "available" or "rebuilt". Now the page checks whether a saved
briefing exists first, and serves it without rebuilding anything — so it can honestly say
"Basis: unavailable". I did not take this from anyone's write-up: I ran the tests myself (97
passed), read the old and new versions of the same test, and confirmed the old one asserted the
bug while the new one asserts the fix on the same scenario. J-06 "A frozen manifest never
changes" moves to passing. Two honest limits are written down, not hidden. Separately, the
browsing lane did something it was told not to do: it added a permanent row to the protected
database on its own judgment. The row is harmless, but three reports then reported the wrong
count, and only the independent auditor caught it.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest and near-complete | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-27-evidence/J-01-verify.png (replay PASS) |
| J-02 What changed since the previous session | partial | partial (not targeted, carried) | no test this iteration — product surface unchanged (methodology A.6) |
| J-03 Plain-English summary with cited facts | partial | partial (not targeted, carried) | no test this iteration — product surface unchanged (methodology A.6) |
| J-04 Each candidate explains why and why-not | passing | passing (re-verified; capture defect) | reports/qa/goal-market-compass-iter-27-evidence/J-04-verify.png — opened; still stops above the candidate card (9th round owed, `evidence_makeup`) |
| J-05 Each close freezes one manifest, exported byte-consistently | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-27-evidence/UT-J-05-result.png (LLM lane PASS; steps 1+6 deliberately not run per the binding iter-26 safety scoping) |
| **J-06 A frozen manifest never changes** | **partial** | **passing (PROMOTED)** | reports/qa/goal-market-compass-iter-27-evidence/UT-02-result.png ("Basis: available", v1+v2 listed) · UT-03-result.png ("Basis: rebuilt" + honest detail) · J-06-verify.png (replay PASS) · apps/backend/tests/test_api_compass.py:288 (route-level "unavailable", `healed is None`) |
| J-07 The Today page answers the ten-second read | failing | failing (not started) | out of scope this iteration (spec OUT OF SCOPE) |
| J-08 Market page moves over intact | failing | failing (not started) | out of scope this iteration (spec OUT OF SCOPE) |
| J-09 The backend fits the host | partial | partial (not targeted, carried) | iter-25 honest miss stands (3,064,772 kB vs ≤2,621,440 kB target) |
| J-10 Bounded recovery of two deleted trading days | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-27-evidence/J-10-verify.png — opened; AVB at 2026-08-11 shows "Invalid below the 50-DMA at $187.94", the golden's exact value |
| J-11 Incident-bounded clean regeneration | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-27-evidence/J-11-verify.png (replay PASS; golden is thin) |

**Deterministic lanes:** merged browser results 12/12 PASS (`reports/phase-goal-market-compass-iter-27-ui-test-results.md`);
deterministic replay lane 5/5 PASS (`reports/phase-goal-market-compass-iter-27-regression-replay-results.md`) —
the full Required-still-passing set (J-01, J-04, J-05, J-10, J-11) was covered, J-05 via the LLM lane.
No `browser-infra.json`, no `DEFERRED-BUDGET` rows, no `journeys-changed.md`, NOT maintenance isolation.
`spec_hash`: I ran `goal_gate.py hash-journeys` myself — all eleven are byte-identical to the recorded values.

**What I verified personally (not read from a report):**
- Ran `pytest tests/test_api_compass.py tests/test_manifest_invariants.py tests/test_ingest_finalize_compass.py tests/test_compass.py -q` → **97 passed in 11.76s**.
- Compared the removal test at `HEAD` (asserts `basis.status == "rebuilt"`, `healed is not None` — the bug) against the working tree (asserts `"unavailable"`, `healed is None`, zero new `scanner_runs`): the same scenario, flipped. That is a real red→green counterfactual on committed source.
- Read `scanner.resolve_as_of_date` (`scanner.py:304-334`) and confirmed it returns the requested date unchanged whenever a bar on or before it exists — so the fast path looks up exactly the date the old path would have, and audit finding B3's frontier case is real.
- Read-only SQLite (`mode=ro`) against the canonical database, after every lane: `next_session_manifests` **26** (ids 1..26 contiguous — nothing deleted), `scanner_runs` 3128 (max id 3158), `daily_prices` 3,310,374 (frontier 2026-08-12), `prospective_eligible` true on **zero** rows, manifests on the 7 incident dates **0**.
- AG-3 spot-check on the served page vs the stored row (id 25, 2025-04-15 v2): displayed members **531**, cohort **521**, shadow **28**, **10** candidate cards, tally `513 + 8 = 521` — all match the database exactly.
- Row 17 (2025-04-15 v1) untouched: `generated_at` 2026-08-20T11:41:00.381102+00:00, availability fence 11:42:00 (+60s), hash `1325e6899fd3…` — and the J-06 golden asserts that same timestamp is still on screen after v2 exists.

## Anti-goal Check

Source: `runs/goal-session-market-compass/iter-27/scan-report.md` (**CLEAN**) + `iter-27/iter-diff.md`
(3 files, all backend: `app/api/compass.py` +16, `app/engine/compass.py` ±23, `tests/test_api_compass.py`).

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 unproven edges must render "not yet proven" | OK | No score/claim surface touched; UT-02/UT-03 both show "not prospective-eligible". |
| AG-2 decision-quality only | OK | No new user-facing text; "Basis: unavailable" label shipped at iter-11. |
| AG-3 displayed numbers must be correct | OK | Re-derived by me against stored row id 25 (531/521/28/10, 513+8=521). |
| AG-4 no overfit edges | OK | No research/selection logic touched. |
| AG-5 determinism, no lookahead | OK | Route reorder is read-order only; `manifest_row_payload` is a pure row reshape; the new 2019-03-01 row is a retrospective reconstruction, labelled as such. |
| AG-6 evidence claims need a referee | OK | No Evidence Claims introduced. |
| AG-7 no hard-coded credentials | OK | scan-report CLEAN; diff is 3 Python files, reviewed. |
| AG-8 resilience / no unbounded loads | OK | New helper is the SAME query shape as the inline query it replaced (`where as_of` + `order_by version desc` + `.first()`), ≤6 rows per as-of. |
| AG-9 offline-deterministic ingest | OK | No live fetch of any kind this iteration; the out-of-scope 2019-03-01 call was a local GET against stored bars. |
| AG-10 host resource ceiling | OK | No launch script, host-guard file, or config touched (diff file list). |
| AG-11 no new composite number | OK | No new field displayed. |
| AG-12 manifest immutability | OK (with a process note) | Nothing mutated or deleted — ids 1..26 contiguous, v1's hash and timestamps intact, byte-identity asserted across every basis transition (TC-2/3/4). One row was ADDED out of scope; AG-12 governs mutation/deletion and additionally forbids removing it now. See the violation entry below. |
| AG-13 system-vs-market vocabulary | OK | No UI change; ux-regression lane PASS. |
| AG-14 no Tapeology coupling | OK | No imports/network/writes to tapeology in the diff. |
| AG-15 no outcome-tuned selection | OK | Selection rule untouched. |
| AG-16 cohorts are not controls | OK | No cohort narrative change; `prospective_eligible` true on zero rows (verified). |
| AG-17 repair never rewrites provenance | OK | The new row is `retrospective`, `prospective_eligible=0`; no prior classification changed; the 7 incident dates still hold 0 manifests. |
| AG-18 authorized migration preserves everything | OK | No schema change (spec OUT OF SCOPE; diff confirms). |

**One MINOR violation recorded this iteration** (ledger now 9 total, **0 unresolved**): the browser-QA
lane broke this iteration's own binding live constraint ("every live/canonical-DB action strictly
read-only and additive-free"; only 2025-04-15 and 2026-08-12 were authorized) by issuing
`GET /api/compass?as_of=2019-03-01`, which permanently minted `next_session_manifests` row id 26.
Auditor finding B2; I re-derived the count myself. Not critical: no enumerated anti-goal is breached, the
row is additive and correctly classified, the owner's ruling item 6 gates manifest *mutation* rather than
an additive create-once row produced by the shipped read path, and deleting it would itself be a
forbidden write. The remedy that exists has been applied — the auditor appended a dated correction to
the dev handoff so 26, not 25, is the standing record. The residual is a process gap, carried as a lesson.

## Pipeline health

Depth dispatched **full — as the spec required** (`iter-27/depth-dispatched` reads `full`); the demotion
that hit iters 2, 6, 8, 23, 24 and 26 did not recur. Reviewer PASS (one accurate NOTE), QA PASS,
ui-impact + ux-regression PASS, closure CLOSURE-PASS, coherence **COHERENCE-PASS**, deterministic scan
CLEAN, auditor **PASS_WITH_GAPS**. The auditor again found what four earlier lanes missed (B1: two
definition-of-done items reported PASS with no test asserting them — now fixed, 4 tests added; B2: the
out-of-scope permanent write and the stale row count in three reports). Two QA citations were
mis-attributed (a unit-test run cannot verify journeys; the database claim was delegated, not
re-derived) — the conclusions hold on other evidence, which I checked.

## Next-Step Recommendation

Build **J-07 "The Today page answers the ten-second read"** next — it is the goal file's own next item
now that J-06 is closed, and it is ordinary product work the owner already authorised (ruling item 5).
J-08 "Market page moves over intact" follows it. **Run it at full depth.** J-07 is the main page, it has
seven acceptance steps including on-screen numbers that must match the stored values and a strict
separation between system words and market words, and this round is fresh proof that the independent
reviewer lane is load-bearing. Only the owner can add the line `Depth enforcement: required` to the plan
if he wants that guaranteed rather than requested; standing guidance keeps `CHAIN_REQUIRE_FULL_DEPTH`
and `CHAIN_MAINTENANCE_ISOLATION` off.

**One process fix to carry into the next plan (small, and it should not wait):** the browsing lane must
be told, in the plan itself, that it may only visit the dates the plan lists when the real database is
in use. This round it chose an extra date on its own and permanently added a row to a protected table.
Nothing was harmed, but the next such choice may land on a date that matters.

**Two honest limits of J-06, written down rather than quietly assumed closed.** (1) The "no longer
stored" message is proven through the real serving code against a test database, never through the
actual "remove data" button on any database — deleting live records is not authorised, and the plan
itself allowed the test-database proof. (2) If someone removes the price data for the newest saved
briefing's own date, the page answers with an error instead of showing that briefing; the saved record
is untouched, but it becomes unreadable. This is older than this round's change and was never in scope.
If the owner wants either closed for real, the cheapest route is a throw-away copy of the database — the
one made in round 23 (`runs/goal-market-compass-iter-23/verify-clone/`, 7.8 GB) may also simply be
deleted now, since the launcher fix it was waiting on was verified in round 24.

**Smaller items, none blocking:** J-04's picture still needs re-taking so it includes the candidate card
(ninth round owed — a passenger task, never an iteration goal); J-05 and J-06 still owe a recorded
walkthrough (this round's recording captured only 3 of 6 steps and one click timed out); the reviewer's
NOTE that the as-of date is now looked up twice on the create branch is correct and harmless; the whole
iteration — plan, both handoffs, all reports, the evidence folder and the three changed source files — is
still uncommitted at scoring time, so confirm it lands. **Five older owner questions remain open and
non-blocking:** whether ~2.99 GB is acceptable for J-09; J-06's "underlying run unavailable" wording;
the rewording of J-01's first two test steps; whether an empty "next-session focus" is acceptable; and
whether MNST joins the recovery list. **Standing framework note:** `goal_gate.py`'s duplicate-journey-
heading defect is still unfixed and must be closed before any GOAL_ACHIEVED certification — this
iteration's own goal slice shows J-10 listed twice, which is that defect visible in the wild.

**What should happen next, in one sentence:** approve building the Today page (J-07) as the next round,
run it with the full set of checks, and tell the browsing lane in that plan to visit only the dates the
plan names.
