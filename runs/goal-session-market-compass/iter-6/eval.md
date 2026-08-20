# Iteration 6 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This iteration built the tool that repairs the two days of price data the earlier drill deleted, and
then tried to use it. The tool is right; the data supplier is gone. The one permitted download asked
the supplier (Stooq) for exactly the two missing days and exactly the 587 missing company codes, and
every single one of the 587 requests came back "not found" — because Stooq now shows a puzzle page
for robots instead of data. Nothing was restored, and nothing was damaged: I ran my own read-only
check on the database and confirmed the latest price date is still 2026-08-10, there are still no
rows for the two missing days, and all 24 sealed briefing records are still there. I am escalating
because this iteration was planned to run in the careful "full" mode and the engine quietly ran it in
the light "lean" mode instead — and that swap had a real cost: it switched on a browser test lane
that the goal file expressly forbids while the data is broken, so that lane's results had to be
thrown away.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels are honest and nearly complete | passing | passing (carried, NOT validly re-verified) | Durability basis: `runs/goal-session-market-compass/iter-6/iter-diff.md` (3 files; the new module is imported by nothing). Prior evidence `reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png`. The iter-6 `UT-J-01` PASS row was DISCARDED (damaged-DB lane, AG-17). |
| J-02 What changed since the previous session | passing | **partial** | Merged row `UT-J-02` = SKIP (`reports/phase-goal-market-compass-iter-6-ui-test-results.md:19`). Downgrade basis is my own read-only query: `MAX(daily_prices.date)` = 2026-08-10, 0 rows for 2026-08-11/12, `MAX(scanner_runs.asof_date)` = 2026-08-10 — so its verified assertion "vs 2026-08-11 (1 day ago)" is unsatisfiable. |
| J-03 Plain-English summary with cited facts | passing | **partial** | Merged row `UT-J-03` = SKIP (same file:20). Same first-hand basis; `GET /api/compass?as_of=2026-08-12` returns HTTP 400 (`docs/handoffs/goal-market-compass-iter-6-dev.md` Step 5 check (f)). |
| J-04 Each candidate explains why and why-not | passing | passing (carried, NOT validly re-verified) | Same durability basis as J-01. Prior evidence `reports/qa/goal-market-compass-iter-4-evidence/J-04-verify.png`. The iter-6 `UT-J-04` PASS row was DISCARDED (damaged-DB lane, AG-17). |
| J-05 Each close freezes one manifest | partial | partial (not tested — out of scope + contract-gated) | `docs/phases/goal-market-compass-iter-6.md` OUT OF SCOPE; goal.md Loop mechanics insert #2. |
| J-06 A frozen manifest never changes | partial | partial (not tested — out of scope + contract-gated) | Same. Incidentally re-confirmed: 24 manifest rows hash-identical through a failed fetch. |
| J-07 The Today page answers the ten-second read | failing | failing (not tested — out of scope) | `docs/phases/goal-market-compass-iter-6.md` OUT OF SCOPE. |
| J-08 Market page moves over intact | failing | failing (not tested — out of scope) | Same; zero `apps/frontend/*` files in the diff (`coherence.md` IA table). |
| J-09 The backend fits the host | partial | partial (not tested — out of scope) | `docs/phases/goal-market-compass-iter-6.md` OUT OF SCOPE; owner decision still open. |
| J-10 Bounded recovery of the two deleted days | unknown (new) | **partial** | `docs/handoffs/goal-market-compass-iter-6-dev.md` Step 5 table; `data_provider_runs` id=541 (`stooq`, `status=failed`, `symbols_ok=0`, `symbols_failed=587`) — read by me directly from the live DB. Merged row `UT-J-10` = SKIP (walkthrough waived in goal.md; not a UI-testable journey). |

Deferred-budget rows: none. Browser-infra token: absent.
Coherence: **COHERENCE-PASS** (`runs/goal-session-market-compass/iter-6/coherence.md`) — no
structural veto. It verified the blueprint-unchanged claim directly rather than trusting it,
and confirmed a single write path (`grep -rln "run_data_job"` returns only `data_manager.py`
and the new `j10_recovery.py`). It also flagged, as work for the retry rather than a violation,
that the code predates the owner's step-2a amendment and still hardcodes `RECOVERY_SOURCE =
"stooq"` — I have carried that into the next-step recommendation and into J-10's recorded gap.
Goal-edit drift: no `journeys-changed.md` this iteration, and I confirmed it independently —
`goal_gate.py hash-journeys` returns hashes byte-identical to the recorded ones for J-01..J-09,
so only J-10 (new) carries a fresh `spec_hash`.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 no unproven "proven" language | OK | No narrative/UI string in the 3-file diff. Diagnostic frame shows every score chip still reading "Not yet proven". |
| AG-2 decision-quality only | OK | No candidate/reason/caution string touched; `evaluate_selection` and `config.yaml` are not in the diff. |
| AG-3 displayed numbers correct | OK | Zero displayed values changed (zero DB rows changed, my own query). `as_of=2026-08-12` honestly returns HTTP 400 rather than serving a substituted number. |
| AG-4 no overfit edges | OK | No pattern or claim shipped. |
| AG-5 determinism / no-lookahead | OK | Fetch scoped to dates at-or-below the frontier; frontier did NOT advance (`MAX(date)` = 2026-08-10, verified). `j10_recovery.py` imports no scoring/forward-return module. |
| AG-6 referee gate | OK | No Evidence Claim this cycle — gate passes automatically. |
| AG-7 no hard-coded credentials | OK (1 informational warn) | `scan-report.md`: 0 critical, 1 warn — `api_key="test-only"` at `apps/backend/tests/test_j10_recovery.py:194`. I opened the line: a literal placeholder passed to a test fixture, not a credential. |
| AG-8 data-shape/scale resilience | OK | `still_missing_symbols` (`j10_recovery.py:230-245`) is a column-projected `select(DailyPrice.symbol, DailyPrice.date)` double-filtered on indexed columns, bounded at 587x2 rows — not an unbounded ORM sweep. |
| AG-9 offline-deterministic ingest (dated exception) | OK — exception honoured, correctly left OPEN | Exactly ONE live-provider run exists (`data_provider_runs` id=541; 539/540 are offline `seed`), scoped to `{2026-08-11, 2026-08-12}` x the derived 587, refused in code by `validate_recovery_scope`. The developer did NOT substitute another vendor and did NOT try to defeat the bot challenge. Exception correctly NOT declared exhausted (verification did not pass). |
| AG-10 host resource ceiling | OK | No launch script or cap in the diff; `config.yaml` untouched this iteration. Tests run one file at a time with `free -h` checked; available memory stayed >=19 GB, swap <=250 MB. |
| AG-11 no new composite number | OK | No new score anywhere. |
| AG-12 manifest immutability | OK — stress-confirmed | My own query: `next_session_manifests` = 24 rows, max `as_of` 2026-08-12, matching the pre-iteration baseline. Developer hashed all 24 rows + export files before/after (identical); reviewer reproduced independently. |
| AG-13 system-vs-market separation | OK | No vocabulary or UI change. |
| AG-14 no Tapeology coupling | OK | `grep -rni tapeology` over both new files returns nothing. |
| AG-15 no outcome-tuned selection | OK | No threshold touched; `compass.selection` not in the diff. |
| AG-16 cohorts are not controls | OK | Frozen cohort payloads were READ (for the missing-set derivation) and not modified; no causal claim made. |
| AG-17 repair never rewrites provenance | OK — held, with one evidence-hygiene note | Held: `git status` shows the iter-5 spec, dev handoff, `status.json` and incident record byte-untouched; no `prospective_eligible` changed (nothing written); the invalid damaged-DB artifacts were LABELLED and KEPT, not deleted. NOTE (minor, process): the merged results file demoted the two damaged-DB FAILs to SKIP but left the two damaged-DB PASSes (`UT-J-01`, `UT-J-04`) standing as clean rows. That is a one-sided use of evidence the goal contract declares unusable. I did not rely on either PASS row. |

New anti-goal violations this iteration: **none**. Ledger unchanged at 2 entries, both resolved.

## Process finding (not an anti-goal — but the reason for this verdict)

The iteration spec sets `**Depth:** full` with a documented Full trigger 1. The engine dispatched it
as `lean` (`runs/goal-session-market-compass/iter-6/depth-dispatched` reads `lean`). Two concrete
consequences, both verified:

1. **The independent audit lane never ran** on the one change whose entire purpose is to stop a
   live-fetch scope violation from happening twice. That same lane caught a real critical AG-12
   breach in iteration 3 of this session. No `docs/handoffs/goal-market-compass-iter-6-audit.md`
   and no `reports/qa/goal-market-compass-iter-6-qa.md` exist.
2. **A forbidden lane ran.** Lean depth auto-enables the parallel browser-QA replay, which executed
   against the knowingly damaged database at 18:15-18:16Z — directly against goal.md's Loop
   mechanics owner insert #2, which names browser-QA as forbidden until J-10's verification passes.
   Its output is quarantined at `reports/qa/goal-market-compass-iter-6-evidence/INVALID-damaged-database.md`.
   The reviewer flagged the same thing (MINOR, `goal-market-compass-iter-6-review.md`).

Neither is the developer's fault (the replay fired after the developer's turn ended, and I confirmed
it mutated nothing). Both are why the next iteration must be binding-full rather than
advisory-full — this session has now demonstrated twice (iteration 2, iteration 6) that a spec's own
`full` request can be silently downgraded.

## Next-Step Recommendation

Retry the recovery with the newly permitted supplier, at **full** depth, targeting **J-10** alone.

The owner already removed the blocker during this iteration: `docs/goal.md` now allows `yahoo` as
well as `stooq` for these exact two days and nothing else. The work is concrete:

1. Change the supplier name in `apps/backend/app/engine/j10_recovery.py:83` from `stooq` to `yahoo`
   (this is the only line the code needs for the swap — the scope guard already checks the supplier
   by name). The project already has a working Yahoo reader, and its own records show Yahoo working
   from this machine as recently as 2026-08-14.
2. Build the new safety check the owner added as step 2a: before writing anything, download a few
   already-surviving days for a sample of companies, keep them in memory only, and prove Yahoo's
   prices follow the same split/dividend adjustment rule as the prices already stored. If they do
   not agree, or the check cannot be done at all, write nothing and stop. Never save those
   comparison rows.
3. Label every restored row honestly as coming from Yahoo, in both the row records and the handoff,
   and state plainly that the data is now mixed-supplier at exactly two dates.
4. Do not let any wording anywhere claim this proves Yahoo and Stooq prices are interchangeable —
   the owner forbids that claim explicitly.
5. After the two days are back, re-check J-01 "Sector labels are honest and nearly complete",
   J-02 "What changed since the previous session", J-03 "Plain-English summary with cited facts" and
   J-04 "Each candidate explains why and why-not" with the browser lane, which is finally allowed to
   run once the data is repaired. Also record the four short walkthrough videos that are now four
   turns overdue, and fix the stored J-01 test script that has wrongly failed twice on a sector name
   that simply wraps onto two lines.

Two safety points for whoever runs it. First, this machine froze once already from running two
backends at the same time, and a second automated session is running on it right now — so start the
repair backend, finish with it, stop it, and only then start anything the browser tests need. Never
both at once. Second, if Yahoo also turns out to be unreachable or fails the adjustment check, that
is an honest miss: stop and report it, and do not try a third supplier — the owner says that needs a
new written permission.

Still waiting on the owner, and still not blocking: whether 3.44 GB of memory is acceptable for
J-09 "The backend fits the host"; the wording of J-06's "underlying run unavailable" sentence; the
rewording of J-01's first two test steps; and whether an empty "next-session focus" on the newest
date is an acceptable honest result. One new question for the owner: the company MNST was left out
of the 587 on purpose because the surviving records disagree about it — the owner may want to decide
whether to include it in the retry.

**In one sentence:** approve running the next turn in full mode to re-attempt the two-day data
repair using Yahoo, with the new "same adjustment rule" safety check in place.
