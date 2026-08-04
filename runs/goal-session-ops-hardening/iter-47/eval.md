# Iteration 47 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The code work this round did what it set out to do. I opened the Evidence page's own endpoint on the
running app and it answered in 0.012 seconds with all seven claim panels filled in. Last round the
same call took about 163 seconds when the app was idle and never finished at all when it was busy.
The check nobody ran is the problem. The browser test lane ran once, early, and then the code was
changed three more times — twice by fix passes and once by the auditor. The only browser report on
file says "BLOCKED" and states in its own words that neither of this round's two target journeys —
J-06 "Pages load only what they need" and J-07 "Heavy aggregates never take the service down" — was
tested by any lane. The six older journeys were "passed" by replay scripts that I read myself and
that check almost nothing: J-08's script loads one page and looks for one line of text. So this
round produced excellent product work and almost no trustworthy proof of it, on a round whose own
written rule (TC-7) said the test lane must run last.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | partial | partial (not re-verified) | Only row is UT-J-01 PASS from the pre-rebuild golden (`reports/phase-goal-ops-hardening-iter-47-regression-replay-results.md`, 13:05); I read that script — it asserts page text persisted history already satisfies. Rebuilt golden (16:05) never run. |
| J-03 No per-run range cap | partial | partial (not re-verified) | Same shape: old script asserts the page text "412 calendar days". Rebuilt golden 15:46, never run. |
| J-04 Non-blocking boot with visible status | partial | partial (not re-verified) | Old golden was two static page loads; now retired to `runs/goal-session-ops-hardening/retired-journey-scripts/J-04.json.retired`; the LLM lane that should carry it never ran. |
| J-05 Aggregates are precomputed at ingest | failing | **failing** (4th consecutive) | `reports/qa/goal-ops-hardening-iter-47-evidence/J-05-verify.png` — I opened it: it shows a snapshot "as of 2005-04-12 · Scanned 2026-07-30", four days older than this iteration. DB: `scanner_runs` has 0 rows for 2011-01-05; runs 299-303 all `interrupted`. Dev drill: snapshot created in ~12 s, then the run never leaves `running`. |
| J-06 Pages load only what they need | partial | partial | Merged results file: "UT-J-06 — no test case executed for J-06 by any lane". My own live probe: `/api/evidence` 200 in 0.012 s. Against that: `logs/backend.log:180945` and `:181041` — two MemoryErrors from `/research/regime-lab`, J-06's own step 11. |
| J-07 Heavy aggregates never take the service down | partial | partial | Merged results file: "UT-J-07 — no test case executed for J-07 by any lane". No wedge under real pressure (health 200 in 0.98 s at 84 kB under the cap); but 8 of 20 health polls over the 2 s ceiling (dev handoff B5). |
| J-08 Backtest evidence serves from storage only | passing | **passing** (durability + my spot-check) | J-08's own code untouched by this diff. Live: `GET /api/backtest` 200 in 0.023 s, 271 KB scorecard, `evidence_status: "refreshing"` — step 2's shape. Lane row is a one-step null test and is not what I scored on. |
| J-09 The backend discloses its own background-compute activity | passing | **passing** (durability + my spot-check) | Producer `get_background_compute_status` (`forward_testing.py:1700`) unchanged — I read it. Live: `background_compute {"active": [], "recent_outcomes": []}`. `J-09-verify.png` shows the badge "background compute running (1)". Open gap filed as iter-47/bi. |

Deferred (`DEFERRED-BUDGET`): none. No `browser-infra.json` (this is not a browser-infrastructure
failure — the lane was simply never re-run). No `journeys-changed.md`; all 8 `spec_hash`es match
`goal_gate hash-journeys`, which I ran. `pending_infra` and `evidence_makeup`: cleared everywhere.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language backed by the ledger | OK | No claim-status code changed; the new `/evidence` label reads "refreshing", never a proven/confidence claim. Frontend diff is one `Badge variant="warn"` plus one disclosure sentence (`apps/frontend/app/evidence/page.tsx:375-397`). |
| AG-2 decision-quality only | OK | No return promise, price target, signal, or order path anywhere in the diff. |
| AG-3 displayed numbers correct | OK | The auditor proved byte-identity of BOTH changed read paths at live scale with his own SHA-256 comparison against a both-fixes-neutralised reference; unit tests pin byte-identity against a pre-fix oracle. The stale-serve branch returns one whole cache row, never a merge of two generations (`forward_testing.py:2700`). |
| AG-4 no overfit edges | OK | No referee, holdout, or claim-registration code touched. |
| AG-5 determinism / no-lookahead | OK | No scoring or forward-return window logic changed; the date filter narrows rows read, never the as-of boundary. |
| AG-6 referee gate | OK | Ops iteration, no Evidence Claims (goal.md loop mechanics). |
| AG-7 no hard-coded credentials | OK | `iter-47/scan-report.md` CLEAN — no secret, dependency, or license findings on added lines. |
| AG-8 memory/resilience *(critical)* | **VIOLATED — minor, 3 entries** | iter-47/bc (RESOLVED in-audit: the new re-warm doubled concurrent heavy compute alongside the boot warm; mutation-verified fix). iter-47/bd (open: same gap versus the ingest finalize tail). iter-47/be (open: `/research/regime-lab` reached the 8192 MB wall — `logs/backend.log:180945`, `:181041`). Also still false: "no unbounded whole-table ORM materialization remains" — `samples.py:161` and `:168` still call the unbounded `_factor_observations`. |
| AG-9 offline-deterministic ingest *(critical)* | **Recorded — minor, 1 entry** | iter-47/bh: `data_provider_runs` id=297, a `both` job for 2026-08-03, ran with `provider='yahoo'` (a real HTTP client) and moved the working DB's latest bar to 2026-08-03. Scored minor: pre-existing sanctioned import path (`config.yaml:12-16`, `:30-33`), 27 such runs since 2026-07-20, nothing introduced by this diff, real data, DB untracked. Reasoning and the opposite reading are in `assumptions.md`. |
| AG-10 host resource ceiling *(critical)* | OK | `git diff <snapshot>..HEAD` over `config.yaml`, `project-extensions/`, `scripts/` and `incredible_auto_dev/scripts/` is EMPTY — I ran it. Every launch banner reads `memory_cap_mb=8192 malloc_arena_max=2` with `host-guard: cpu_list=0-15 blas_threads=8`. |

Ledger after this iteration: **71 total, 24 unresolved, 0 unresolved critical.** Three carried items
closed with this round's evidence (iter-46/av the Evidence-page cold tail; iter-46/aw the two bare log
calls; and iter-46/au updated to PARTLY closed rather than resolved). Pipeline: scan CLEAN ·
coherence **COHERENCE-PASS** (zero blocking, two advisories) · review **PASS_WITH_NOTES** (1 MINOR,
1 NOTE) · QA **PASS** · audit **PASS_WITH_GAPS** (1 IMPORTANT fixed in-audit, 4 gaps open) ·
browser QA **BLOCKED** (2 target journeys with no row) · closure **CLOSURE-FAIL** · ux-regression
SKIPPED (wall-clock trim) · demo RECORDED_WITH_NOTES.

## Next-Step Recommendation

Full depth. Give the next round this order.

1. **Run the eight journey checks FIRST, before writing any new code.** The app has not been checked
   since three code changes ago, so nobody knows what today's app really does. The services are
   already up and healthy for it. Two journeys — "Pages load only what they need" (J-06) and "Heavy
   aggregates never take the service down" (J-07) — have no check at all and no picture. Do not start
   a new data job while another one is still finishing, and expect "Aggregates are precomputed at
   ingest" (J-05) to come out red; that is the honest answer.
2. **Before that run, add one line to the J-05 check** so it cannot pass by accident: make it require
   "1 snapshots" on the job card. The auditor wrote the exact fix. Today the check passes even when
   the job does no work at all.
3. **Then make adding one old day of history finish.** The day's snapshot is written in about twelve
   seconds; what never ends is the clean-up work that follows, so the job row sits on "running"
   forever. This is the fourth round in a row this journey has failed and it is the only remaining
   product fault on a must-have journey.
4. **Stop one page from being able to eat the whole machine.** Opening the Regime Lab page took the
   app to its 8 GB limit twice this round and left the background warm-up stuck at three of seven
   panels for twenty minutes. This has been put off twelve times; it is now measured, on a page a
   normal user can open.
5. Smaller, already written down: two more places on the same Evidence page still read a whole
   cohort at once (`samples.py:161` and `:168`); the app can still run two identical warm-ups at the
   same time when a data job is finishing (audit B2 — one shared "warm in progress" flag fixes it);
   the health check answered slower than its 2-second promise on 8 of 20 tries while a job was
   finishing; the new background worker does not show up on the page that is supposed to list
   background work.
6. Carried, untouched: iter-29/b and the badge wording after a failed warm-up (nineteen rounds
   unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az
   (the ~29 s first answer after start, still unmeasured on a quiet machine); iter-46/ba.
7. Capture only, never a round's goal: J-07's `[NEW]` walkthrough (seventeenth round unrecorded) and
   J-05's acceptance frames.
8. For the owner: nothing needs a decision, but three facts belong in front of him. The Evidence page
   went from about three minutes to about one hundredth of a second, which is this round's real win.
   The app was never checked end to end after that win landed, for the second round running. And a
   data job in this round pulled real prices from Yahoo over the internet rather than from the
   committed offline copy — that is how the product has been built since July and nothing was saved
   into version control, but it is worth him knowing, because this project's promise is to run
   offline.
