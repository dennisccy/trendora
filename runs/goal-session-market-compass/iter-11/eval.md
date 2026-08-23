# Iteration 11 Evaluation

**Verdict:** REGRESSION
**Depth Recommendation For Next Iteration:** full

## Summary

The work this iteration set out to do was done, and I checked it myself instead of believing the
reports. The manifest table on the real 7.8 GB database no longer carries the link that blocked the
big repair, all 24 saved briefing records came through the change with every single value unchanged,
and the page code that used to claim "the original basis is intact" for records that never recorded a
basis now says "unverifiable" instead. That last one was a real honesty bug on a page people read, and
it is closed. But the one authorised change to that table did more than the owner allowed: besides
removing the link, it also dropped three "default value" rules and moved one column into a different
position. Nothing was lost and nothing is broken — I compared all 24 records, value by value, before
and after — but the owner's written permission said "this and nothing else", and that limit was
crossed on the live database, where it cannot be undone without a new permission. That is why this
iteration halts for the owner rather than moving on.

## Journey Results This Iteration

No browser test ran this iteration. `reports/phase-goal-market-compass-iter-11-ui-test-results.md`
reads `Browser QA Verdict: SKIPPED` with the declared reason "maintenance isolation is required for
this iteration", and `runs/goal-session-market-compass/iter-11/maintenance-isolation-refusals` records
the engine refusing the lane at 2026-08-23T22:40:28Z. Per the methodology's maintenance-isolation
rule, every journey therefore keeps its prior recorded status, no journey may be promoted on this
iteration, and nothing here is scored `unknown` on the strength of the missing lane.

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest and nearly complete | passing | passing (carried, not re-verified) | `reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png` (re-opened by me; iter-4 row) |
| J-02 What changed since the previous session | partial | partial (carried, not re-verified) | iter-6 row; blocker unchanged |
| J-03 Plain-English summary with cited facts | partial | partial (carried, not re-verified) | iter-6 row; blocker unchanged |
| J-04 Each candidate explains why and why-not | passing | passing (carried, not re-verified) | `reports/qa/goal-market-compass-iter-4-evidence/J-04-verify.png` (re-opened by me; capture defect recorded) |
| J-05 Each close freezes one manifest, exported byte-consistently | partial | partial (carried) | iter-3 row; its store was migrated this iteration — 24/24 rows unchanged, verified by me read-only |
| J-06 A frozen manifest never changes | partial | partial (carried) | iter-3 row; its basis disclosure gained the `unverifiable` value, verified by me on all 8 affected rows |
| J-07 The Today page answers the ten-second read | failing | failing (carried) | iter-0 row; never passed, not a regression |
| J-08 Market page moves over intact | failing | failing (carried) | iter-1 row; never passed, not a regression |
| J-09 The backend fits the host | partial | partial (carried) | `reports/perf-budgets.md:12114-12236`; re-measurement needs a backend boot, forbidden this iteration |
| J-10 Bounded recovery of the two deleted trading days | passing | **passing — re-verified against the CURRENT goal text** | `runs/goal-session-market-compass/iter-11/journeys-changed.md` flagged the drift; re-verified by my own read-only queries (585 symbols on each of 2026-08-11 and 2026-08-12; EA and EQR hold zero rows; latest price date still 2026-08-12; `data_provider_runs` still 549) plus `runs/goal-market-compass-iter-9/j10-population-evidence.json` |
| J-11 Incident-bounded clean regeneration of derived state | partial | partial (Stage B1 completed; Stage C still gated) | `runs/goal-market-compass-iter-11/j11-stage-b1-*.json` (10 artifacts, all re-derived by me read-only); `docs/handoffs/goal-market-compass-iter-11-audit.md` finding B1 |

**Goal-edit drift.** `journeys-changed.md` listed J-10 only (spec_hash `007e17cb…` → `42ad1807…`). The
changed text is the owner's dated "J-10 CLOSED — residual set accepted (2026-08-23)" block, which
accepts exactly the end state iteration 9 reached. I re-verified that state read-only against the live
database this iteration and recorded the new hash. No listed journey carries an old-text pass.

**What I re-derived myself, read-only** (`mode=ro` + `PRAGMA query_only=ON`; a write probe was refused
with "attempt to write a readonly database"; the database was never opened for write and never copied):

| Claim | My result |
|---|---|
| Live `CREATE TABLE next_session_manifests` has no `FOREIGN KEY` clause | Confirmed; the live text equals `j11-stage-b1-postmigration-ddl.json` exactly |
| `PRAGMA foreign_keys=ON` then `foreign_key_check` | pragma reads `1`; zero violation rows; `foreign_key_list` empty |
| 24 rows × 28 columns unchanged | 24 rows; zero substantive differences against the pre-migration dump AND against the live table now (only the dump's `T` date separator differs) |
| Orphans 3048 / 3049 / 3081 / 3112 | All four still stored, unrebound, unresolvable against `scanner_runs` |
| Index set | Exactly the three original indexes; no extra, none dropped |
| No other table written | All 24 tables' row counts equal the pre-migration snapshot; no leftover shadow table; zero views, zero triggers |
| Stage C has not begun | `scanner_runs` 3121 · `scanner_results` 1327944 · `sector_scores` 96751 · `theme_scores` 34331 · `forward_returns` 6800539 — all unchanged |
| Fail-closed fix on real rows | 8 manifests carry `generation_json` NULL (ids 1-8), each with a live run for its as-of: every one returned the fabricated `available` before and returns `unverifiable` now |
| Residual schema delta | Confirmed: three `DEFAULT` clauses dropped, `version` moved from ordinal 9 to 3 |
| Targeted tests | `96 passed` in one process (the five named test files, never the full suite) |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials (AG-7) | OK | `iter-11/scan-report.md`: CLEAN, no secret findings on added lines; the 12 changed files are Python/TypeScript modules, tests, and JSON evidence dumps of market data |
| Paid / external SaaS (AG-9) | OK | No dependency manifest changed; no network call this iteration; `data_provider_runs` still 549 (verified by me), so the exhausted J-10 fetch exception was not re-used |
| License changes | OK | No LICENSE or license field in the diff file list |
| Fabricated / substituted data (AG-1, AG-3) | OK — improved | This iteration REMOVES a fabricated-state defect on a served surface: 8 manifests that claimed "basis available" with no recorded basis now report `unverifiable` (I derived this per row) |
| AG-12 manifest immutability | OK | No manifest row mutated or deleted; 24/24 rows byte-equal; the export directory's own mtime is 2026-08-20 15:50, i.e. untouched since three days before this iteration |
| AG-17 provenance never rewritten | OK | `prospective_eligible` is 0 on all 24 rows, versions and both hashes unchanged; nothing upgraded |
| **AG-18 authorized migration preserves everything** | **VIOLATED (critical, unresolved)** | The "removes the FK constraint and **nothing else**" bound was exceeded: `version INTEGER NOT NULL DEFAULT 1`, `frozen BOOLEAN NOT NULL DEFAULT 0` and `prospective_eligible BOOLEAN NOT NULL DEFAULT 0` lost their defaults, and `version` moved from column ordinal 9 to 3. Cause: `apps/backend/app/engine/j11_schema_migration.py:172-192` rebuilt the table from the ORM model instead of the live DDL it had already captured. **AG-18's stored-value clause is NOT triggered** — no value changed, no manifest was regenerated, rebound, rehashed, upgraded, deleted or minted, and no other table's schema moved. The breach is of the authorization's scope, it is materialised on the live database, and it is not undone. |
| AG-10 host resource ceiling | OK | No launch script touched; no full test suite; no second copy of the 7.8 GB database (explicitly out of scope in the spec) |
| AG-2, AG-11, AG-13, AG-15, AG-16 | OK | No scoring, selection, composite number, or vocabulary change; the only user-visible wording added is the neutral badge "Basis: unverifiable" |
| AG-5 no-lookahead | OK | No scoring or forward-return code touched; no data written outside the manifest table |
| AG-8 resilience | OK | The new status has an explicit exhaustiveness guard and a neutral variant (`apps/frontend/lib/basis-disclosure-label.ts:32-48`); the backend guard now returns a status instead of raising on malformed input |
| AG-14 no Tapeology coupling | OK | No import, call, or write toward that repository anywhere in the diff |
| A5 maintenance isolation | Held | No service booted; browser and replay lanes refused by the engine and recorded; the only database write was the authorized migration |

Coherence: `runs/goal-session-market-compass/iter-11/coherence.md` = **COHERENCE-PASS** (one producer,
one endpoint, one renderer for `basis.status`; no new page or nav entry). Review: PASS. QA: PASS.
Audit: PASS_WITH_GAPS.

## Next-Step Recommendation

**One decision is needed from the owner, and nothing else may start before it.** The single authorised
change to the manifest table did more than the permission allowed. Besides removing the link it was
meant to remove, it also dropped three "default value" rules and moved one column. Pick one:

1. **Accept it in writing** in `docs/goal.md`, with the reassuring facts recorded: I compared all 24
   records value by value and nothing changed; the dropped defaults are never read (every write goes
   through the application layer, and no raw insert targets this table); the table now has exactly the
   shape a freshly built database has always had; and the start-up routine will not try to re-add
   anything, because all the columns already exist (I read that code).
2. **Order a corrective rebuild** that puts the three defaults and the original column order back —
   this is a second write to the live 7.8 GB database and needs its own written permission, its own
   before/after evidence and its own audit. My recommendation is against it: it doubles the risk to
   restore rules nothing reads.
3. **Record it as an accepted deviation** and move on, which is option 1 in a shorter form.

**After the owner answers**, the next iteration is the big repair — J-11 stages C to G — at full
depth, alone: one writer, no web server, no browser tests. Four things must travel with it, unchanged
from last time: clear both stale layers (the stored daily summaries for 11 and 12 August and the
caches built over different data); watch AVB, whose restored prices were converted onto the stored
scale while its trading volume was not, so any figure multiplying price by volume reads about 2.79
times too high on those two days; do not re-run the recovery script (permission for live downloads is
used up and the script has no guard); and make sure this iteration's migration script, its ten evidence
files and the fixes actually reach version control — as of now none of them are committed, and the
quality check wrongly stated that they were.

**Three smaller items ride along.** Fix the iteration metadata that says a frontend is present while
the test designer worked as if it were not. When the browser lane finally reopens at Stage G, re-check
J-05 "Each close freezes one manifest", J-06 "A frozen manifest never changes" and J-08 "Market page
moves over intact" first, in that order — and note that the new "unverifiable" badge has never been
shown by a browser, because the eight records that would trigger it are hidden behind an older,
also-honest message. **One new non-blocking observation from my own check:** three manifest export
files recorded in the database (versions 2, 3 and 4 for 12 August) are missing from disk, and four
export files exist for dates that have no manifest record at all. Both conditions predate this
iteration by three days — the export folder has not been touched since 20 August — so nothing here
caused them, but the Stage G verification should reconcile them.

**Five older owner questions remain open and non-blocking:** whether 3.44 GB is acceptable for J-09
"The backend fits the host"; J-06's "underlying run unavailable" wording; the rewording of J-01's
first two test steps; whether an empty "next-session focus" is acceptable; and whether MNST joins the
recovery list. **One standing framework note:** the defect that let a forbidden test lane run three
times is still unfixed in `scripts/automation/`; three iterations running have avoided it with the
maintenance-isolation contract rather than curing it.

## Halt Justification

I am halting because a critical rule in `docs/goal.md` was broken and the break is still in place.
AG-18, written by the owner one day before this iteration ran, says the authorised change to the
manifest table "removes the `source_run_id` foreign-key constraint and **nothing else**". The change
that ran also dropped three default-value rules and moved one column, on the live database. I did not
take that from the audit report: I read the recorded before-picture of the table
(`runs/goal-market-compass-iter-11/j11-stage-b1-premigration-ddl.json`) and the live table definition
myself and compared them.

What is **not** wrong, and I proved each point myself, read-only: no stored value changed anywhere in
the 24 records (24 × 28 values compared, twice — against the recorded before-picture and against the
live table now); the four "orphan" references the owner insisted must be kept are stored exactly as
before; no record was created, rebuilt, re-hashed, upgraded or deleted; no other table changed in any
way; the destructive repair stage has not started; and the honesty fix on the page works on all eight
affected records. No journey stopped working, and nothing that was passing is failing.

I chose REGRESSION over STALLED because the halt is not merely "waiting for an answer". The state of
the live production database is outside the written permission, and that cannot be undone inside this
session's rules. The owner should acknowledge that explicitly before the most dangerous step of the
whole session — the destructive clear of derived data, the same class of action that permanently lost
data in iteration 5 — is allowed to begin. Ruling A6's gate on Stage C is therefore **not** cleared,
and Stage C is **not** recorded as unblocked.

To resume: write the ruling (accept, correct, or defer) into `docs/goal.md`, then resume with
`--acknowledge-regression`. Nothing needs to be repaired first if the ruling is "accept" — the
practical risk today is nil, and the evidence for that judgement is listed above.
