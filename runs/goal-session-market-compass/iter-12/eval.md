# Iteration 12 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

## Summary

This iteration did the four small clean-up jobs the owner asked for, and it did them without touching the
real database even once. I checked that myself rather than believing the reports: the database file has
not been written since the night of 23 August, which is before this iteration started, and every table
still holds exactly the number of rows it held before. The two safety fixes are real. The tool that
rebuilds a database table now copies the table's own real definition instead of guessing it from the
program's model, and it refuses to run at all if it cannot find the exact thing it is meant to remove. The
badge that tells a reader whether a saved briefing's underlying data is still trustworthy can no longer
say "trustworthy" when it has nothing to base that on. I re-counted the live badge results myself and got
the same answer the team reported: 8 cannot be verified, 9 were rebuilt, 5 are intact, 2 have no
underlying data. I am halting anyway. Nothing is broken and nothing is missing — the next step is the
destructive rebuild of eleven days of derived data, and the owner's own written rule says that step may
only start on the owner's explicit say-so.

## Journey Results This Iteration

The browser lane and the automatic replay lane were **forbidden by contract** this iteration
(maintenance isolation, ruling A5) — `reports/phase-goal-market-compass-iter-12-ui-test-results.md`
records `Browser QA Verdict: SKIPPED` with that reason, and
`runs/goal-session-market-compass/iter-12/maintenance-isolation-refusals` records the engine refusing the
browser-QA phase. No journey was verified by browser this iteration, so every journey keeps its prior
recorded status and none could be promoted.

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels are honest | passing | passing (carried, not re-verified — lane forbidden) | prior: `reports/qa/goal-market-compass-iter-4-evidence/` |
| J-02 What changed since the previous session | partial | partial (carried, not re-verified) | prior iter-6 gap record |
| J-03 Plain-English summary with cited facts | partial | partial (carried, not re-verified) | prior iter-6 gap record |
| J-04 Each candidate explains why and why-not | passing | passing (carried, not re-verified) | prior: `reports/qa/goal-market-compass-iter-4-evidence/` |
| J-05 Each close freezes one manifest | partial | partial (carried, not re-verified) | prior iter-3 gap record |
| J-06 A frozen manifest never changes | partial | partial (carried, not re-verified) | prior iter-3 gap record |
| J-07 The Today page ten-second read | failing | failing (carried, not re-verified) | prior iter-0 gap record |
| J-08 Market page moves over intact | failing | failing (carried, not re-verified) | prior iter-1 gap record |
| J-09 The backend fits the host | partial | partial (carried, not re-verified) | `reports/perf-budgets.md` |
| J-10 Bounded recovery of the two deleted days | passing | passing (unchanged; re-derived read-only by me) | my own read-only SQL on `apps/backend/data/trendora.db`: 585 symbols on 2026-08-11 and 585 on 2026-08-12, frontier still 2026-08-12, `daily_prices` 3,310,374 unchanged, `data_provider_runs` 549 (no new fetch) |
| J-11 Incident-bounded clean regeneration | partial | partial (advanced within `partial` — Stage B1 now complete and clean; Stages C-G not started) | `runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-diff.json`, `j11-stage-b1-live-reverification.json`; every load-bearing figure re-derived by me read-only (see below) |

**Spec-hash drift:** no `journeys-changed.md` was produced, and I confirmed why — I ran
`goal_gate.py hash-journeys` myself at the iteration's snapshot commit and at HEAD: J-01..J-10 hashes are
byte-identical at both points and identical to the stored values, so no recorded pass rests on changed
goal text. J-11's hash moved from `9124b395…` (iter-11) to `d3f6f105…` (the owner's 2026-08-24 rulings);
J-11 is not a passing journey, and I re-verified and re-stamped it from this iteration's evidence.

**What I re-derived myself, read-only, rather than taking from any report** (live
`apps/backend/data/trendora.db`, opened `mode=ro` with `PRAGMA query_only=1`):

- Manifest table DDL carries **no `FOREIGN KEY` clause**; sha256 of the DDL text is
  `9f653c8147c7c8931b07ea4a88d46ef1d6ddefb2ef5177b700d2b60e7fc501ee`.
- With `PRAGMA foreign_keys=ON`, `foreign_key_check(next_session_manifests)` returns **zero** rows.
- **24 rows × 28 columns** are value-identical to iter-11's persisted post-migration dump — 0 differences
  after normalising SQLite's datetime separator and boolean representation. The four orphan
  `source_run_id` values (3048, 3049, 3081, 3112) are stored unrebound. Exactly the three original
  indexes exist; `prospective_eligible` is false on all 24 rows.
- **The four accepted DDL residuals, re-derived from iter-11's captured pre-migration DDL:** the 28-column
  *set* is identical (pre-only `[]`, live-only `[]`); the pre-migration text carried 3 `DEFAULT` clauses
  and the live text carries 0; `version` sat at ordinal 9 and now sits at ordinal 3. Exactly the owner's
  enumerated set (A8/A9) and nothing more. No second live rewrite occurred.
- **Zero live writes:** db mtime `1787522416` (2026-08-23 23:00:16 — iter-11's own last write, *before*
  this iteration started at 10:25:29Z) and size `8,365,871,104`, identical before and after all my reads;
  the write-ahead log is 0 bytes, so no committed write reached the file by any route. Table counts equal
  iter-11's post-migration figures: `daily_prices` 3,310,374 · `scanner_runs` 3,121 · `forward_returns`
  6,800,539 · `data_provider_runs` 549 · `watchlist` 6. Stage C has not begun.
- **`basis_disclosure` distribution over all 24 live manifests, computed by my own implementation of
  ruling A4-bis's table (not by calling the product code):** `unverifiable 8 / rebuilt 9 / available 5 /
  unavailable 2` — matching the reported figures exactly. All 8 rows with degenerate `generation_json` are
  `unverifiable`; none reports `available`.
- **`preFreezeEra` overlap (A11a):** 8 rows have degenerate `generation_json`, 8 rows have `mode IS NULL`,
  and the overlap is **complete 8/8**. Reading `apps/frontend/components/compass-manifest-strip.tsx:123`,
  `:146-149` and `:186`: the branch renders one sentence and never reaches `BasisLine`. It asserts no basis
  status at all — honest, not fail-open.
- **Targeted tests re-run by me**, one process at a time: `test_j11_stage_b1_migration.py` 14 passed,
  `test_manifest_invariants.py` 48 passed. The db mtime was unchanged before and after.

## Anti-goal Check

Worked from `runs/goal-session-market-compass/iter-12/scan-report.md` (**CLEAN** — no secret, dependency or
license findings) plus `iter-diff.md`'s 10-file list and my own greps over each changed file.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 no unproven "proven/confident" claim | OK | The only served-value change *reduces* AG-1 exposure: `basis_disclosure` can no longer return `available` without a recorded timestamp that parses and matches. Verified by reading `compass.py:1131-1178` and by my own 24-row re-derivation (8 degenerate rows all `unverifiable`). |
| AG-2 decision-quality only | OK | No candidate, narrative or config string in the diff; no new displayed text. |
| AG-3 displayed numbers correct | OK | No displayed number changed; the one changed served field's live values are unchanged (my A/B check: the 5 `available` rows all carry parseable matching `+00:00` timestamps). |
| AG-4 / AG-6 referee-backed claims | OK | No Evidence Claim introduced; ledger untouched (`data_provider_runs` and evidence files unchanged). |
| AG-5 determinism / no-lookahead | OK | No scoring, forward-return or as-of code touched. |
| AG-7 no hard-coded credentials | OK | scan-report CLEAN; my own grep for `api[_-]?key|secret|token|password` over all 9 changed source files found only unrelated words ("token" in a DDL comment, a pre-existing `api_key` docstring in `models.py:153` outside the diff). |
| AG-8 data-shape resilience | OK | Improved: the new degenerate branches return a status instead of raising (a non-dict `generation_json` used to be able to escape as a 500). |
| AG-9 offline-deterministic ingest | OK | No network import or call in any changed file (`requests`/`urllib`/`httpx`/`yfinance`/`socket` all absent); `data_provider_runs` still 549 — no fetch happened. |
| AG-10 host resource ceiling | OK | No launch script, `config.yaml`, or `host-guard` file in the diff; no full-suite run; no copy of the 8.4 GB database. |
| AG-11 no new composite number | OK | No new score or blended value anywhere in the diff. |
| AG-12 manifest immutability | OK | 24 rows × 28 columns value-identical to iter-11's dump — verified by me, per row and per column, not in aggregate. |
| AG-13 system-vs-market vocabulary | OK | No frontend file changed; no readiness token added to any served field. |
| AG-14 no Tapeology coupling | OK | My grep for `tapeology` over all changed files: no match. |
| AG-15 no outcome-tuned selection | OK | No threshold and no `compass.selection` key changed (`config.yaml` is not in the diff). |
| AG-16 cohorts are not controls | OK | No cohort text or semantics touched. |
| AG-17 repair never rewrites provenance | OK | No manifest regenerated, rebound, rehashed or minted; `prospective_eligible` is false on all 24 rows; no incident-evidence file deleted or rewritten (the diff adds only new iter-12 files). |
| AG-18 authorized migration preserves everything | **Resolved (was the iter-11 breach)** | No migration ran live this iteration. The iter-11 breach is now **resolved by explicit owner acceptance**, not by repair: `docs/goal.md` J-11 step 11 "OWNER RULING — iter-11 DDL residual accepted" + A8/A9 and AG-18's "Bounded exception on record" accept exactly the four differences and decline a second rewrite. I re-derived that the residual is exactly those four and nothing more. Recorded honestly: the acceptance is **not** a general waiver, **not** a precedent, and **does not** make iter-11 compliant (A8); iter-11's REGRESSION verdict stands (A14). Ledger: 5 total, **0 unresolved**. |

**Coherence:** `runs/goal-session-market-compass/iter-12/coherence.md` = **COHERENCE-PASS** (one non-blocking
advisory: a one-off diagnostic script mirrors part of `basis_disclosure`'s shape-guard for bucketing, and
never computes the served status itself). No structural veto.

**Pipeline health:** review PASS, QA PASS, audit PASS_WITH_GAPS, depth dispatched `full` (matching the
spec's `Depth: full`) — the silent full→lean demotion did not recur, for the fourth iteration running.

## Ruling A12 — Stage C readiness, re-derived by me from the goal file, not from the developer's summary

| # | A12 item | My finding | My evidence |
|---|---|---|---|
| 1 | J-10 terminal, no stale operative `20/567` wording | HOLDS | 585 symbols on each of the two dates, read-only, by me. The `20/587` text at `docs/goal.md:749` now carries the owner's own "HISTORICAL … spent … must not be read as authorizing further recovery work" annotation; the J-11 prerequisite bullet reads "SATISFIED". No operative use remains. |
| 2 | B / B1 / B2 complete or re-verified | HOLDS, with an honest note | B1's live end state (ruling A9) re-verified by me in full this iteration. B (pre-reset inventory) and B2 (frozen engine identity) were delivered in iter-10 and are **not** re-derived here — J-11 step 13 requires the C attempt to re-freeze the identity and re-inventory at its own start anyway, so nothing is lost. |
| 3 | Live manifest FK absent | HOLDS | No `FOREIGN KEY` in the DDL; `foreign_key_check` with enforcement ON returns 0 rows. |
| 4 | 24 manifest values preserved | HOLDS | 24 rows × 28 columns identical to iter-11's dump, checked per row and per column. |
| 5 | Exact residual DDL acceptance encoded | HOLDS | `docs/goal.md` A8/A9 table; `models.py:820-843` names all four; `j11_schema_migration.py`'s docstring keeps the residual section as historical fact. I re-derived the residual independently. |
| 6 | No broader AG-18 waiver | HOLDS | AG-18's "Bounded exception on record" states it is not generalized and not a precedent; `models.py` repeats that framing; no other table's schema changed (I compared every table's row count and the manifest DDL myself). |
| 7 | Corrected migration utility tested | HOLDS | `create_shadow_table` transforms the captured `sqlite_master` text (`j11_schema_migration.py:270-289`) and fails closed unless the exact clause matches once (`:111-133`). 14/14 tests passed under my own run. |
| 8 | `basis_disclosure` failing closed | HOLDS | Validate-then-compare ordering read at `compass.py:1152-1178`; 48/48 tests passed under my own run; my independent 24-row distribution matches. |
| 9 | `models.py` comment honest | HOLDS | Read `models.py:820-874`: it quotes the withdrawn claim as FALSE, states the referential-contract-vs-physical-DDL distinction, and names all four residuals. |
| 10 | Maintenance isolation active | HOLDS | Browser lane SKIPPED by contract; refusals file records the engine's refusal; no evidence directory exists; no service was started by me either. |
| 11 | Zero live-database writes in iteration 12 | HOLDS | db mtime and size unchanged since iter-11's own last write, 0-byte write-ahead log, every table count identical. This is stronger than the persisted before/after fingerprint, which (as the auditor correctly noted) brackets only 101 seconds of a 90-minute iteration. |
| 12 | All targeted tests passing | HOLDS | 62 re-run by me across the two changed test files; developer, reviewer and auditor each independently ran all five (107 passed). One **pre-existing, unrelated** failure is disclosed in the handoff (`test_no_magic_numbers.py`, on literals in `indicators.py`/`forward_testing.py`/`research.py`) — not introduced here, not in the targeted set. |
| 13 | No new blocker discovered | HOLDS | See the two paragraphs below. |

**Auditor finding B1 — my own independent judgement (not accepted on the auditor's word).** The row copy
(`j11_schema_migration.py:301`, `cols = [c.name for c in NextSessionManifest.__table__.columns]`) and the
final equality proof (`verify_and_finalize`, which dumps `NextSessionManifest.__table__`) both read the
*model's* column list, while the shadow table's body now comes from the captured live DDL. So a live column
the model does not declare would be silently emptied **and** silently unverified. The defect is real. It is
**not** a Stage C blocker, and here is the exact reason rather than an assertion: **there is no causal path
from Stage C to this code.** Stage C clears and rebuilds `scanner_runs` / `scanner_results` /
`sector_scores` / `theme_scores` / `forward_returns` for eleven dates; it performs no schema rebuild of any
table. I checked every call site myself — outside its own tests, `create_shadow_table` /
`copy_rows_to_shadow` / `verify_and_finalize` / `rebuild_manifest_table` are referenced only by the
standalone script `apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py`, and
`app/engine/j11_maintenance.py` (which owns the Stage C machinery) does not import the migration module at
all. Additionally, the fixed utility now **fails closed against today's live table**: the FK clause it
looks for is absent, so a match count of 0 raises `MigrationDdlShapeError` before anything is created. B1
is therefore recorded as a **precondition on any future authorized live migration run**, exactly as the
auditor filed it — not a blocker.

**Deferred Stage G items — do they make Stage C unsafe? No, and I checked both.** (a) The `preFreezeEra`
branch masks the new `unverifiable` badge on the same 8 rows (overlap 8/8, re-derived by me), but it
asserts no basis status at all, so nothing false is displayed and AG-1 is not engaged; Stage C runs with no
application booted, so no badge is read during it. (b) The export-file discrepancies: I found 3
DB-recorded export files missing on disk (2026-08-12 v2/v3/v4) and 4 on-disk exports with no manifest row
(2024-06-08, 2024-07-01, 2024-07-08, 2024-08-01, all with mtime 2026-08-20 12:10) — all four days older
than this work. Stage C deletes neither manifests nor export files (J-11 step 2 lists both as
never-deleted immutable evidence), so it cannot worsen this. Both stay Stage G items.

**My answer to the owner-facing line: `J-11 STAGE C READY: YES`** — on my own re-derived evidence, and
concurring with the developer, reviewer and auditor. Ready does not mean started: ruling A12's own last
sentence keeps Stage C waiting for the owner.

## Next-Step Recommendation

**One thing is needed from the owner, and it is a single word: go, or not yet.** Every safety condition the
owner wrote for the big repair is now met, and I checked all thirteen of them myself against the real
database rather than reading anyone's summary. The next step is the destructive one — delete and rebuild
eleven days of calculated results — and the owner's own rule says it may not start without an explicit
instruction. That is why this halts here rather than rolling on.

**When the owner says go, the next iteration is J-11 Stages C through G, at full depth, alone.** Full depth
is required, not preferred: the goal file forbids the destructive rebuild in the light mode, and the
careful mode's independent auditor has now caught something real that the other lanes missed in four
iterations running. Five things must travel with it:

1. **One writer only.** No web server, no browser tests, no background warm-up. Boot warm-up is exactly how
   an unwanted day got recreated once before.
2. **Clear both stale layers, not one.** The stored daily summaries for 11 and 12 August were built when
   only 20 companies had prices, while six background caches were refreshed over all 585 — rebuilding only
   the summaries leaves the mixture in place.
3. **Watch AVB.** Its restored prices were converted onto the stored scale but its trading volume
   deliberately was not, so any figure multiplying price by volume reads about 2.79 times too high on those
   two days. Check what that does to its ranking in the rebuilt results.
4. **Do not re-run the recovery script.** Permission for live downloads is used up and the script has no
   guard of its own.
5. **Do not run the table-rebuild tool against the real database.** It is fixed for future use and is
   deliberately untested against the live file; before any future authorized live run, the owner should
   first require the fix for the gap named above (the copy and the proof must read the real table's
   columns, not the program model's).

**Three small, optional items**, none worth an iteration of its own, all for the next time those files are
touched: the plain-language summary at
`reports/phase-goal-market-compass-iter-12-implementation-summary.md:19` calls the four accepted database
differences "harmless", while the owner's own words are "not desirable … merely accepted" — that wording
should be softened to match; an aside comment in `models.py` still credits only the earlier half of the
badge fix; and the badge test set has no case for a recorded timestamp that is a number rather than text
(the code handles it correctly — I confirmed the branch exists).

**One framework note, new and non-blocking, that the owner should know about.** The automatic check that is
supposed to notice when the owner edits a journey's text does not cover the whole of J-10: I probed it line
by line and it only reads the last sixty lines of that journey's block. The owner's 24 August edit to J-10
sits outside that window, so the drift alarm stayed silent. It caused no harm this time — the edit only
marks a finished instruction as historical, and I re-checked J-10 against the database anyway — but the
alarm is quieter than it looks. The cause appears to be a nested bullet inside J-10 that begins with the
same `- **J-10` shape as a journey heading.

**Five older owner questions remain open and still do not block anything:** whether 3.44 GB is acceptable
for J-09; J-06's "underlying run unavailable" wording; the rewording of J-01's first two test steps;
whether an empty "next-session focus" is acceptable; and whether MNST joins the recovery list. **One
standing framework note, unchanged since iteration 8:** the defect that once let a forbidden browser lane
run is still not cured in `scripts/automation/`; four iterations running have avoided it with the
maintenance-isolation contract instead.

## Halt Justification

**This halt does not mean something is wrong or missing.** Every one of the owner's thirteen readiness
conditions holds, and I verified each one against the real database myself. I am halting because the only
remaining way forward is an owner decision, which is what a halt is for.

The next step is the destructive clear and rebuild of eleven days of calculated results on the canonical
8.4 GB database — the same class of action that permanently destroyed two days of data in iteration 5. The
owner's own written rule (`docs/goal.md`, ruling A12) ends with: *"Stage C is still NOT executed in that
iteration — it waits for an explicit owner instruction to resume."* Every way to unblock it is the owner's
to take, and there are exactly three:

- **(a) Say go.** Reply with the instruction to start Stage C, then `--resume`. The readiness answer this
  iteration was asked to produce is `J-11 STAGE C READY: YES`.
- **(b) Ask for the future-migration gap to be closed first.** The table-rebuild tool's copy step and its
  proof step both read the program model's column list rather than the real table's. It cannot cause harm
  today and has no path into Stage C, but the owner may prefer it fixed before Stage C rather than after.
- **(c) Change the plan in `docs/goal.md`** — reword the gate, narrow Stage C, or stop J-11 here.

**There is no other legal work to do in the meantime.** The goal file closes every other product, research
and browser lane until J-11's final stage passes, so the eight other unfinished journeys cannot be worked
on. The remaining engineering items are all either explicitly forbidden to widen (the owner's ruling says
this acceptance is "NOT permission to broaden Stage B1") or too small to be an honest iteration goal.
Scheduling one of those would be motion that does not move the blocker.

**Why not CONTINUE?** Continuing would let the engine plan iteration 13, and iteration 13 can only be Stage
C — starting an irreversible destructive step without the sanction the owner's own ruling requires.

**Why not REGRESSION?** Nothing that worked stopped working, no stored value changed, no critical rule was
broken this iteration, and the one outstanding breach — iteration 11's schema overreach — is now closed by
the owner's dated written acceptance. Iteration 11's REGRESSION verdict stands unchanged, as ruling A14
requires; this iteration did not earn one of its own.

**Why not ESCALATE?** Escalation means "run the next turn in the careful mode". This turn already ran that
way, and the careful mode is exactly what produced the useful findings.
