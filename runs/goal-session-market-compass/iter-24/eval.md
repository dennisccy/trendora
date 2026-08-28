# Iteration 24 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The one job the owner authorised was done, and it works. The engine can no longer quietly
switch to a different database part-way through a run: it now decides once, at the start,
which start-up command to use, and refuses any later start-up that does not match. I did not
take this from anyone's write-up — I ran the new safety test myself (18 checks, all passed)
and watched the refusal happen. I also proved the protected database was never opened: its
three files have not changed at all since yesterday, while the throw-away copy was the one
written to during this run.

ONE FINDING IS MINE ALONE, and it is why I am asking for a deeper next run. This iteration's
own re-test of the three working journeys never happened, and nothing reported it. The plan
document mentions the phrase "Required-still-passing" once in a sentence before it reaches
the real list, and the engine reads only the FIRST line containing that phrase. So the list
of journeys to re-test came out empty, the re-test lane quietly did nothing, and the log said
only "replay: no", which reads like "nothing to do". No journey is harmed — none of the app's
code changed this run, so yesterday's proof still stands — but the safety net silently went
missing, in the very iteration whose purpose was to close a silent safety hole. Separately,
this iteration asked for the deeper review and was automatically downgraded to the lighter
one, so no independent auditor looked at a change to the engine's own start-up machinery.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels are honest | passing | passing (NOT re-tested) | Held on iter-23 evidence: `reports/qa/goal-market-compass-iter-23-evidence/J-01-verify.png` — I opened it as a spot-check: GRMN shows a real stored sector "Consumer Discretionary", 1/539, regime 73.18 Risk-on, scores badged "Not yet proven". Consistent. |
| J-02 What changed since previous session | partial | partial (not tested) | Out of scope; no product code changed |
| J-03 Plain-English summary with cited facts | partial | partial (not tested) | Out of scope; no product code changed |
| J-04 Candidates explain why / why-not | passing | passing (NOT re-tested) | Held on iter-23 evidence: `reports/qa/goal-market-compass-iter-23-evidence/J-04-verify.png`; keeps `evidence_makeup: true` (6th iteration — the capture still crops above the candidate card) |
| J-05 Close freezes one manifest | partial | partial (not tested) | Out of scope; no product code changed |
| J-06 A frozen manifest never changes | partial | partial (not tested) | Out of scope; no product code changed |
| J-07 Today page ten-second read | failing | failing (not tested) | Out of scope; no product code changed |
| J-08 Market page moves over intact | failing | failing (not tested) | Out of scope; no product code changed |
| J-09 Backend fits the host | partial | partial (not tested) | Out of scope; next iteration's target |
| J-10 Bounded recovery of two trading days | passing | passing (NOT re-tested) | Held on iter-23 evidence: `reports/qa/goal-market-compass-iter-23-evidence/J-10-AVB-2026-08-12-result.png` — I opened it as a spot-check: AVB at 2026-08-12 renders Leadership 26.22 / Entry Quality 52.07 / Risk 34.39, chart volume 3.71M, 1254 bars. Consistent. |
| J-11 Incident-bounded regeneration | passing (goal text drifted) | passing — drift resolved | `journeys-changed.md` flagged `spec_hash 55ef995c… → 012568db…`. I read the whole `docs/goal.md` delta: ONE hunk at `:2194`, +46/-0, purely additive, whose operative content is the owner's ruling "J-11 STATUS: PASSING — CLOSED" plus an instruction NOT to re-verify (item 1). No acceptance criterion added or tightened. I confirmed the state J-11 certifies is byte-intact (`apps/backend/data/trendora.db` 8365871104/mtime 1787822829, `-wal` 2599752/1787862368, `-shm` 32768/1787863696 — all identical to iter-23), and that ruling items 2/3/4 hold. New hash recorded; see the assumption ledger. |

**Not re-tested this iteration — the finding above.** J-01, J-04 and J-10 were named in the
spec's Required-still-passing set and have valid golden scripts on file
(`runs/goal-session-market-compass/journey-scripts/J-01.json`, `J-04.json`, `J-10.json`), but
`replay_lane_spec_journeys` (`scripts/automation/lib/replay-lane.sh:75-77`) does
`grep -iE 'Required-still-passing' "$SPEC" | head -1` — first matching line wins. In
`docs/phases/goal-market-compass-iter-24.md` the first match is **line 21**, a prose
cross-reference inside the *Target journeys* bullet ("…see Required-still-passing and TESTING"),
which contains no `J-NN` token. The real bullet is line 23. I reproduced the exact parse:
`REQUIRED_JOURNEYS=[]`. So `R_REPLAY` was empty, `_use_replay=no`, and no
`reports/phase-goal-market-compass-iter-24-regression-replay-results.md` was ever written
(iter-23's spec put the bullet first and parsed `J-01 J-04 J-10` correctly). Their status is
held under evidence durability, not promoted: `apps/` is byte-untouched this iteration
(`git diff 1885c1cb -- apps/ config.yaml` empty; no untracked product files), so the iter-23
evidence remains valid. `last_verified_iter` deliberately stays at iter-23 for all three.

## Pipeline Health

- **Coherence:** `iter-24/coherence.md` = **COHERENCE-PASS** — no structural veto. Its two advisory notes
  are correct and I confirmed the substantive one myself: `scripts/` and `tests/` are tracked symlinks
  (mode `120000`) into `incredible_auto_dev/`, so the spec's "two copies of `goal-iter-lean.sh` need the
  identical patch" premise was wrong — there is one file, patched once.
- **Review:** PASS with 2 NOTEs. No fail-open (the review did not FAIL). I checked the second NOTE myself:
  REL-5/REL-14 wrap `ensure_services_running` in `|| true`, so a refusal there logs and records but does
  not abort — that is the SAFE direction (a refusal means no backend was started), so the guarantee holds.
- **Deterministic scan:** CLEAN. **Browser QA:** SKIPPED — declared reason is "no target journeys", NOT
  maintenance isolation, so the A.3 isolation carve-out does not apply; statuses are held under A.6
  evidence durability instead, on a verified-zero product-surface delta.
- **Lanes that never ran:** QA agent, independent auditor, closure lane — the spec asked for full depth and
  the arbiter demoted it. No `browser-infra.json` token exists, so nothing is `pending_infra`.

## Anti-goal Check

Worked from `iter-24/scan-report.md` (**CLEAN**) + `iter-24/iter-diff.md` (5 files, all
goal-mode automation) plus my own greps. Product surface delta is **zero** — I verified
`apps/` and `config.yaml` are untouched, tracked and untracked.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 unproven scores presented as proven | OK | No product code changed; spot-check screenshots still show "Not yet proven" badges |
| AG-2 no return promises / buy-sell signals | OK | No product code, no copy changed |
| AG-3 displayed numbers correct | OK | No computing or serving code changed |
| AG-4 no overfit edges | OK | No scoring/referee code changed |
| AG-5 determinism / no-lookahead | OK | No engine code changed |
| AG-6 evidence claims need referee verdict | OK | No evidence-derived claim shipped |
| AG-7 no hard-coded credentials *(critical)* | OK | scan-report CLEAN; I grepped the new test + both changed scripts for key/secret/token/password/bearer assignments — none |
| AG-8 data-shape / data-scale resilience | OK | No ORM or query code changed |
| AG-9 offline-deterministic ingest *(critical)* | OK | scan-report CLEAN; I grepped `test-backend-launch-context.sh` for curl/wget/requests/urllib/non-local URLs — none. Every scenario uses `echo` stubs and a spied `_start_service_with_retries` |
| AG-10 host resource ceiling | OK | Launch path unchanged in substance; `scripts/start-backend-j11-verify.sh` still `exec`s the standard `scripts/start-backend.sh`, so host-guard caps apply. Live boot logged `memory_cap_mb=8192 malloc_arena_max=2` |
| AG-11 no new composite candidate number | OK | No product code changed |
| AG-12 manifest immutability *(critical)* | OK | No database write at all — canonical `.db`/`-wal`/`-shm` byte-identical to iter-23; the only DB written this run was the disposable clone |
| AG-13 system-vs-market separation | OK | No UI copy changed |
| AG-14 no Tapeology coupling | OK | I grepped the diff and the new test: the only "tapeology" hits are pre-existing goal-vision prose re-rendered into the session HTML report, not code |
| AG-15 no outcome-tuned selection | OK | No selection code changed |
| AG-16 cohorts are not controls | OK | No cohort code changed |
| AG-17 repair never rewrites provenance *(critical)* | OK | No repair ran; no provenance row touched |
| AG-18 authorized manifest migration preserves everything *(critical)* | OK | No migration ran |
| Paid / external SaaS | OK | No manifest touched (`package.json`, `requirements*`, `pyproject`) — I checked the changed-file list |
| License | OK | No LICENSE or license field in the diff |
| Fabricated / substituted data | OK | No ingest, fixture, or provider path changed |

**Ledger:** 8 entries, **0 unresolved** (was 1). The iteration-23 owner-ruling breach is now
marked resolved on two grounds I verified myself: the owner's ruling items 2 and 3 disposed of
it in writing, and the authorised remedy landed and works (my own test run: 18 passed, 0 failed;
refusal observed firing; no further harm — canonical database byte-identical).

**Recorded residual, not a violation:** the new guard enforces launch-context *consistency*
with whatever was locked at iteration start — not canonical-database *protection*. With no
override set at start-up the locked value IS the ordinary launcher (the test's own
"override active: no" case), so an iteration that needs an isolated copy must still supply
`CHAIN_START_BACKEND_CMD`/`TRENDORA_CONFIG` in the engine's environment BEFORE the iteration
begins — which is what the owner did by hand this run. That same ambient setting means this
run's live boot does **not** by itself prove the fix: I read the pre-fix code
(`git show HEAD:…/goal-iter-lean.sh`, lines 254-261) and it would have honoured the same
ambient variable. The proof of the fix is the regression test, not the live boot.

## Next-Step Recommendation

Go back to normal product work, but run the next round with the deeper checks turned on.

1. **Build J-09 "The backend fits the host"** — the goal file's own next item, and the smallest
   one (a configuration value plus a measurement). The owner's ruling item 5 says work resumes
   with no further permission needed.
2. **Fix the plan-reading bug I found, in the same round.** The engine reads only the first
   line containing "Required-still-passing", so a passing mention of that phrase earlier in the
   document silently empties the re-test list. Two ways, and the cheap one should be done
   regardless: never let that phrase appear in the plan before the real list; and, better,
   make the engine prefer the line that actually contains journey numbers
   (`scripts/automation/lib/replay-lane.sh:75-77`). Add a check that a non-empty re-test list
   which produces no re-test results is reported as a problem instead of a quiet "replay: no".
3. **Re-test J-01, J-04 and J-10 for real next round** — they were skipped this time through no
   fault of their own, and next round is the first to touch the app again since the database
   incident.
4. **Ask the plan to say `Depth enforcement: required`.** This iteration asked for the deeper
   review and was automatically downgraded because a deep review had run recently. That switch
   is the only in-document way to make the deeper review stick, and it does not need any
   environment variable turned back on.
5. **Small, non-blocking:** the 7.8 GB throw-away copy at
   `runs/goal-market-compass-iter-23/verify-clone/` may now be deleted (owner ruling item 4 —
   the fix is verified); J-04's screenshot still needs re-taking to include the candidate card;
   the developer's own checklist marked "J-01/J-04/J-10 remain green" as done while its prose
   said they were not re-tested, and the reviewer passed over it — worth one line in the next
   review prompt.

In one sentence: approve the next round to build J-09 and to fix the plan-reading bug that
silently skipped this round's safety re-tests, and let it run with the deeper checks on.

## Halt Justification (if halting)

Not halting. ESCALATE continues the loop; it only requires the next iteration to run the full
pipeline (independent auditor, QA agent and closure lane), which is what this iteration asked
for and did not get.

Why not STALLED: nothing is waiting on the owner. His ruling item 5 states in writing that
normal work resumes once this fix lands and is verified — it landed and I verified it — and
item 6 tells the loop not to stop for reversible cleanup. Why not REGRESSION: no journey moved
from working to broken, no enumerated anti-goal was broken, and the one unresolved critical
ledger entry is now properly closed by the owner's own ruling plus a remedy I tested myself.
Why not plain CONTINUE: a lean run just lost its entire regression safety net without reporting
it, while modifying the engine's shared start-up machinery with no independent auditor present —
that is exactly the cross-cutting case the escalation rule exists for. It is also the only
lever that works: this iteration's spec asked for full depth and the arbiter demoted it anyway
(`reason: full-cap`), whereas a prior ESCALATE verdict is ranked ABOVE that cost rule
(`scripts/automation/run-goal.sh:2638`), so the next iteration genuinely gets the auditor.
