# Iteration 7 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The repair tool was pointed at the new supplier (Yahoo) and a new safety check was added: before
writing anything, compare prices the system already has against the same days from the new supplier.
The check ran for real, on 88 real price comparisons, and it said "these do not match closely enough"
— so the tool wrote nothing at all. I checked the database myself, read-only: the two missing days
are still missing, no new download record exists, and the database file has not been touched since
before this iteration started. The tool did not move the pass mark after seeing a near-miss, which is
the honest thing to do. The independent auditor then found a serious hole in that same safety check —
it would have said "they match" when it had compared **nothing at all** — reproduced it, and fixed it
inside this iteration with four new tests.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels are honest and nearly complete | passing | passing (carried, not re-tested — out of scope by design) | reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png (I opened it — spot-check A.4); scope: docs/phases/goal-market-compass-iter-7.md OUT OF SCOPE + TC-17 |
| J-02 What changed since the previous session | partial | partial (unchanged; blocker unmoved) | My own read-only query: `MAX(daily_prices.date)`=2026-08-10, 0 rows on 2026-08-11/12; docs/handoffs/goal-market-compass-iter-7-dev.md step 5(f) |
| J-03 Plain-English summary with cited facts | partial | partial (unchanged; blocker unmoved) | Same query as J-02; `GET /api/compass?as_of=2026-08-12` still HTTP 400 per dev handoff step 5(f) |
| J-04 Each candidate explains why and why-not | passing | passing (carried, not re-tested — out of scope by design) | reports/qa/goal-market-compass-iter-4-evidence/J-04-verify.png (I opened it — spot-check A.4) |
| J-05 Each close freezes one manifest | partial | partial (not tested — out of scope + contract-gated) | docs/phases/goal-market-compass-iter-7.md OUT OF SCOPE; goal.md Loop-mechanics insert #2 |
| J-06 A frozen manifest never changes | partial | partial (not tested — out of scope + contract-gated) | Same; incidental re-confirmation: 24 manifest rows, `MAX(as_of)`=2026-08-12 (my own query) |
| J-07 The Today page answers the ten-second read | failing | failing (not tested — out of scope) | docs/phases/goal-market-compass-iter-7.md OUT OF SCOPE; zero frontend files in the diff |
| J-08 Market page moves over intact | failing | failing (not tested — out of scope) | Same; coherence.md: `git diff … -- apps/backend/app/api apps/frontend` empty |
| J-09 The backend fits the host | partial | partial (not re-measured — out of scope) | docs/phases/goal-market-compass-iter-7.md OUT OF SCOPE; `config.yaml` absent from `git status` |
| J-10 Bounded recovery of the two deleted days | partial | **partial** (sole target; advanced, outcome still unmet) | docs/handoffs/goal-market-compass-iter-7-dev.md step 5 table; docs/handoffs/goal-market-compass-iter-7-audit.md §2 + §4; apps/backend/app/engine/j10_recovery.py:101, :259-261, :460-482 (read by me); my own read-only SQL |

No journey newly passing. No journey newly failing. **No regression.** Browser-QA lane did not run at
all (`reports/phase-goal-market-compass-iter-7-ui-test-results.md`: SKIPPED, 0/0, no evidence directory
created) — correct on two independent grounds: backend-only iteration, and the goal contract's
damaged-database lane gate. No `DEFERRED-BUDGET` rows; the Required-still-passing set was deliberately
empty this iteration. The ux-regression reviewer was shed by the wall-clock budget (non-blocking); the
audit, coherence, QA, review and closure lanes all ran.

`runs/goal-session-market-compass/iter-7/depth-dispatched` reads `full`, matching the spec's own
`**Depth:** full` line — the silent full→lean demotion that drove iteration 6's ESCALATE did **not**
recur, and the forbidden lane stayed off in both directions.

## Anti-goal Check

Worked from `iter-7/scan-report.md` (**CLEAN** — no secret, dependency or license finding on added
lines) plus `iter-7/iter-diff.md` (4 files: `apps/backend/app/engine/j10_recovery.py`,
`apps/backend/app/data_providers/yahoo_provider.py`, `apps/backend/tests/test_j10_recovery.py`, and
`docs/goal.md` — the owner's own amendment, not the developer's work).

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language | OK | No displayed value, endpoint or ledger entry touched; the module carries explicit disclaimers (`j10_recovery.py:36`, `:401`). |
| AG-2 decision-quality only | OK | No candidate/narrative/caution string in the diff; iter-2's minor note stays closed. |
| AG-3 displayed numbers correct | OK | Zero rows written (verified by me), so no served number could move. |
| AG-4 no overfit edges | OK | No pattern surfaced as proven; nothing added to the evidence ledger. |
| AG-5 determinism / no-lookahead | OK | Comparison window is 2026-08-04..2026-08-10, all ≤ the surviving frontier; no scoring path touched; zero writes. |
| AG-6 referee gate | OK | No Evidence Claim introduced this cycle. |
| AG-7 no hard-coded credentials | OK | scan-report CLEAN; `api_key` is an injected parameter defaulting to `None`, never persisted (`j10_recovery.py:507, :516-517`); Yahoo is `needs_key: false`. |
| AG-8 data-shape/scale resilience | OK | `_stored_closes` is a column-projected select bounded by the 20 sampled symbols × 5 dates; `_convention_check_window_dates` uses `LIMIT 5`; one provider call per symbol, held in memory. No full-table load. |
| AG-9 offline-deterministic ingest | **VIOLATED (critical) — found and FIXED inside this iteration; live fetch itself was authorized** | The 20 read-only comparison calls are expressly authorized by the owner's vendor addendum (already-surviving days ≤ 2026-08-10, held outside the database, never written) — that part is compliant, and no third vendor was attempted. The violation is the gate itself: `check_adjustment_convention` returned `agree` on **zero** compared pairs ("all 0 sampled pairs within 0.7500% relative delta"), which the then-current step 2a forbids ("if the comparison cannot be performed at all — insert nothing and STOP"). The auditor reproduced `run_gated_recovery` writing 4 `daily_prices` + 2 `data_provider_runs` rows on a fixture DB on that empty proof. Fixed at `j10_recovery.py:460-482` (minimum-evidence floor, placed after the mismatch branch — I read the code and confirmed the ordering) + 4 regression tests, 27/27 passing. **Never reached the real database** — see the verification block below. Recorded in the ledger as critical / `resolved: true`. |
| AG-10 host resource ceiling | OK | `config.yaml` is not in the diff (`git status` clean on it), so `memory_cap_mb` 8192, `malloc_arena_max`, `pool_size` 24, `max_overflow` 44 and `limit_concurrency` 64 are all byte-unchanged. No launch script touched. One backend started transiently, one test file at a time, `free -h` checked (dev handoff). |
| AG-11 no new composite candidate number | OK | The gate verdict is internal, never displayed, never attached to a candidate/market/manifest (coherence.md Data Contract row). |
| AG-12 manifest immutability | OK — independently re-verified by me | `next_session_manifests` = 24 rows, `MAX(as_of)` = 2026-08-12 (my read-only query); no manifest writer/reader/export path in the diff. |
| AG-13 system-vs-market separation | OK | No vocabulary surface touched. |
| AG-14 no Tapeology coupling | OK | No tapeology import, call or write anywhere in the diff. |
| AG-15 no outcome-tuned selection | OK — and honoured in spirit | The selection rule is untouched, and the precommitted 0.75% tolerance was **not** loosened after a borderline result (`assumptions.md` iter-7 developer entry; reviewer grep-verified). |
| AG-16 cohorts are not controls | OK | Untouched. |
| AG-17 repair never rewrites provenance | OK — verified by me | No repair occurred, so nothing could be rewritten. `reports/qa/goal-market-compass-iter-6-evidence/` is byte-unchanged (`git status` clean on that path; its `INVALID-damaged-database.md` marker still in place). No manifest eligibility upgraded. |

**Zero-side-effect verification (my own read-only SQL, not taken from any report):**
`daily_prices` `MAX(date)` = 2026-08-10; 0 rows on 2026-08-11/2026-08-12; 0 rows after 2026-08-10;
`data_provider_runs` `MAX(id)`/`COUNT(*)` = 541/541 with row 541 still iteration 6's `stooq` failure
(`started_at` 2026-08-20 18:00:54, before iteration 7's 21:32 start); `next_session_manifests` 24 /
`MAX(as_of)` 2026-08-12; `scanner_runs` 3118 / `MAX(asof_date)` 2026-08-10. The database file's own
mtime (2026-08-20 18:01 UTC) predates this iteration entirely and its write-ahead log is empty — the
strongest available proof that nothing was written.

**Why this is not REGRESSION.** The critical finding was discovered and repaired *inside* the same
iteration by the audit lane, with regression tests, and I confirmed it never touched real data. My
halting rule is "an **unresolved** critical violation halts"; this one is resolved, and the ledger
carries it at `resolved: true`. This follows the precedent already set for iteration 3's AG-12 breach,
which was likewise found, fixed and recorded in-iteration without halting. No journey moved from
passing to failing.

**Coherence:** `iter-7/coherence.md` reads **COHERENCE-PASS** — no Data Contract or Information
Architecture violation, no second producer, no new route. No structural veto applies.

**Goal-edit drift:** no `journeys-changed.md` was produced, and I verified why — I ran
`goal_gate.py hash-journeys` and compared every hash against the recorded ones: J-01..J-09 are
byte-identical to their recorded values, and only J-10 changed. J-10 is not a recorded-passing journey,
so no prior pass was voided. I scored J-10 against the current text and stamped the current hash; it is
`partial` under both the old and the new wording, so the stamp claims nothing the evidence does not
support.

## Next-Step Recommendation

Build the owner's redesigned safety check, then run the repair — one iteration, at **full** depth,
J-10 "Bounded recovery of the two trading days the drill deleted" alone.

Plain terms, four things that must be true together:

1. **Compare shapes, not price levels.** The old check compared price levels and near-failed on two
   oil companies whose gap was almost exactly the same on every single day — the fingerprint of one
   dividend payment, not of two suppliers disagreeing. The owner has replaced that test: compare how
   the two price series *move* day to day, and separately measure the constant ratio between them.
   Fix the pass marks in code before running anything, and never change them afterwards.
2. **Convert before storing.** If a company passes, its new prices must be multiplied onto the scale
   of the prices already stored — all four price fields, not just the closing price — never stored
   raw. A company that does not pass is simply not restored, and is named in the record as not
   restored.
3. **Measure and store the same series.** Today the check looks at one version of Yahoo's price and
   the restore path would have saved a different one; the auditor measured those two differing by
   about 0.086% on Apple. Both must be the same series through one code path, or the conversion factor
   silently absorbs that difference.
4. **Write the comparison down.** This run's 88 comparisons were never saved to a file, and the
   summary in the handoff does not even add up (4+4+5+76 = 89, against 88 stated). Those numbers are
   now gone. Every future comparison must be saved as a per-row file before anyone reads the verdict,
   because that file is the only thing the conversion factor may be calculated from.

Also carry, cheaply, in the same turn: make the pass marks impossible for a caller to override (the
auditor's B5 — right now the discipline lives in the operator, not the code), and add the small
missing tests for the new price-reading code (B2/T2 from the reviewer and auditor).

Run it at **full** depth. The reason is concrete: the independent auditor found a hole this iteration
that both the reviewer and QA missed, and the next turn is the first time this session actually writes
into the main price table — with a brand-new conversion step. That is the moment to have the auditor
watching, not the moment to save time.

Only after those two days are back: iteration 9 re-checks J-01 "Sector labels are honest and nearly
complete", J-02 "What changed since the previous session", J-03 "Plain-English summary with cited
facts" and J-04 "Each candidate explains why and why-not" in the browser, records the four short
walkthrough videos that are now five turns overdue, and fixes the stored J-01 test script that has
twice reported a failure over a sector name that merely wraps onto two lines.

**Nothing here is blocked on the owner.** The owner already answered this iteration's open question by
rewriting the check's design in `docs/goal.md` while the iteration was running — so the next step is
engineering work, not a decision. Five older owner questions remain open and none of them block: whether
3.44 GB is acceptable for J-09; the J-06 "underlying run unavailable" wording; the rewording of J-01's
first two test steps; whether an empty "next-session focus" is an acceptable honest result; and whether
the company MNST should be added to the 587 names in the retry. One housekeeping note for the owner:
the `docs/goal.md` amendment is still uncommitted in the working tree.

**One sentence for approval:** approve building the redesigned price-comparison check exactly as the
goal file now describes it, and running the two-day repair behind it, with the full review chain
switched on.
