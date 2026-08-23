# Iteration 9 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The missing data is back. Of the 587 company codes the earlier drill deleted from 11 and 12 August,
585 now have their prices again — 20 restored two turns ago, 565 restored this turn. The other two,
EA and EQR, could not be restored and are named openly with the reason for each. Nothing was guessed
and no rule was bent to make the numbers look better. I did not take this from the reports: I ran my
own read-only checks on the database and confirmed every figure, including that no other day gained
or lost a single row and that the two named failures have no rows at all. J-10 "Bounded recovery of
the two deleted trading days" is now done at the raw-data level. The pages people look at are still
not repaired — that is the next journey, J-11.

Two things also went right that had gone wrong for three turns in a row. The careful full review mode
really ran, and the test lane that this project's own rules forbid — which had started servers and
overwritten protected evidence pictures twice before — did not run at all this time. I checked the
protected pictures byte for byte and they are untouched.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels are honest | passing | passing (carried, not re-verified) | reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png (opened as a stable spot-check; surfaces byte-unchanged) |
| J-02 What changed since the previous session | partial | partial (carried, not re-verified) | reports/qa/goal-market-compass-iter-4-evidence/J-02-verify.png (iter-4; blocker moved, not cleared) |
| J-03 Plain-English summary with cited facts | partial | partial (carried, not re-verified) | reports/qa/goal-market-compass-iter-4-evidence/J-03-verify.png (iter-4; blocker moved, not cleared) |
| J-04 Each candidate explains why and why-not | passing | passing (carried, not re-verified) | reports/qa/goal-market-compass-iter-4-evidence/J-04-verify.png (opened as a stable spot-check; surfaces byte-unchanged) |
| J-05 Each close freezes one manifest | partial | partial (not tested — out of scope, contract-gated) | reports/qa/goal-market-compass-iter-3-evidence/UT-02-manifest-historical-badges.png |
| J-06 A frozen manifest never changes | partial | partial (not tested — out of scope, contract-gated) | reports/qa/goal-market-compass-iter-3-evidence/UT-02-manifest-historical-badges.png |
| J-07 The Today page answers the ten-second read | failing | failing (not tested — out of scope) | reports/qa/goal-market-compass-iter-0-evidence/UT-J-07-fail.png |
| J-08 Market page moves over intact | failing | failing (not tested — out of scope) | reports/qa/goal-market-compass-iter-1-evidence/UT-J-08-fail.png |
| J-09 The backend fits the host | partial | partial (not re-measured — out of scope) | reports/perf-budgets.md:12114-12236 |
| **J-10 Bounded recovery of the two deleted days** | **partial** | **passing** (sole target; raw-layer terminal state) | runs/goal-market-compass-iter-9/j10-population-evidence.json (567 verdicts); docs/handoffs/goal-market-compass-iter-9-dev.md (step-4 provenance, step-5 (a)-(f), step-5a mutation table); docs/handoffs/goal-market-compass-iter-9-audit.md §1-2; my own read-only queries on apps/backend/data/trendora.db |
| J-11 Incident-bounded clean regeneration | unknown | unknown (never measured; prerequisite now satisfied) | none — spec-only |

**Maintenance isolation.** `reports/phase-goal-market-compass-iter-9-ui-test-results.md` is all-SKIPPED
with the declared reason "maintenance isolation" — the browser-QA and deterministic-replay lanes were
forbidden by this iteration's contract, not missing. Every journey therefore keeps its prior recorded
status, none was promoted on browser evidence (there is none), and J-01–J-09 went unverified this
iteration by design. I confirmed the isolation actually held: no `reports/qa/goal-market-compass-iter-9-evidence/`
directory, no replay-lane directory, no replay results file, and `scanner_runs` still shows
`MAX(created_at) = 2026-08-21 00:28` — no backend boot-warmup row was written today, unlike iteration 8.

**How J-10 was scored without a screenshot.** `docs/goal.md` waives the walkthrough for J-10 and names
its substitute evidence set verbatim: the raw-recovery provenance record, bounded-scope verification,
canonical price-coverage evidence, and complete mutation reconciliation. All four exist and I
re-derived each one from primary sources. My own read-only checks: 585 rows on 2026-08-11 and 585 on
2026-08-12 with an INTERSECT of exactly 585 symbols; total `daily_prices` 3,310,374, so other-date rows
are 3,309,204 — identical to the pre-iteration count, meaning no other date moved; `MAX(date)` still
2026-08-12 with 0 rows on/after 2026-08-13; all 1,170 recovery rows in a contiguous id tail
3,311,385–3,312,554 with nothing else above 3,311,384 (a pure append — no survivor rewritten);
`import_checkpoints` 35 (this run's real fetch plan, 566 symbols) has an EMPTY intersection with
iteration 8's 20 restored names (they were never re-requested); `RECOVERY_SYMBOLS` parsed from source is
exactly 587 with MNST absent, the evidence artifact's 567 are a strict subset, and `RECOVERY_SYMBOLS`
minus restored is exactly `['EA','EQR']`. The frozen methodology was not touched: the diff carries zero
+/- lines for `RECOVERY_SYMBOLS`, `RECOVERY_DATES`, `RECOVERY_SOURCE`, `PATH_AGREEMENT_TOLERANCE` (0.005),
`BRIDGE_DISPERSION_BOUND` (0.015), `MIN_COMPARABLE_PAIRS_PER_SYMBOL` (3) or `CONVENTION_CHECK_SAMPLE_SYMBOLS`.
This scoring is an interpretation call and is recorded in `assumptions.md`.

**Pipeline health.** Review PASS, QA PASS, coherence COHERENCE-PASS, closure CLOSURE-PASS, audit
PASS_WITH_GAPS. `depth-dispatched` reads `full`, matching the spec's `Depth: full` + `Depth enforcement:
required` — no silent demotion this time (it happened in iters 2, 6 and 8). Targeted tests 101/101 pass,
independently re-run by the auditor in one process.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language | OK | No score, ranking or edge surfaced; no evidence-ledger file touched. `certified-claims.jsonl` still 7 lines, md5 8620eeb4b7e81c4071e92fc1196907af, not in `git status`. |
| AG-2 decision-quality only | OK | No UI, no narrative, no candidate surface in the diff (verified: `apps/frontend/` diff empty). |
| AG-3 displayed numbers correct | OK, with one recorded caveat | No displayed value changed. Caveat carried to J-11: AVB's two restored rows hold price on the stored scale and volume on Yahoo's current scale, so `close*volume` reads ~2.79× high for those two dates (audit B2 — spec-mandated, disclosed, not a violation). |
| AG-4 no overfit edges | OK | No pattern, claim or study introduced. |
| AG-5 determinism / no-lookahead | OK | No scoring or forward-return code touched; frontier unchanged at 2026-08-12 (my query). |
| AG-6 referee gate | OK | No Evidence Claim introduced; gate passes automatically this cycle. |
| AG-7 no hard-coded credentials | OK | `scan-report.md` CLEAN (secrets/deps/license, tracked + 1 untracked file). I also grepped all 6 changed product files plus the new script: `api_key` appears only as a function parameter, never a literal; the Yahoo crumb is documented as runtime-only and never stored. |
| AG-8 data-shape/scale resilience | OK | No consumer of widened fields changed; no unbounded ORM load added. |
| AG-9 offline-deterministic ingest | OK — inside the dated exception | Live Yahoo calls were made, authorized by the 2026-08-20 dated exception + vendor addendum. Scope verified by me: dates confined to {2026-08-11, 2026-08-12} (0 rows on/after 08-13, `MAX(date)` 2026-08-12), symbols a strict subset of `RECOVERY_SYMBOLS` (MNST absent), vendor `yahoo` only — `data_provider_runs` 544–549 are yahoo fetch / seed backfill pairs, no third vendor. **Forward risk (audit B4, not a violation today):** the exception is now declared exhausted while the committed driver has no exhaustion guard and its zero-work early return is unreachable, so any future run would breach AG-9. Do not re-run it. |
| AG-10 host resource ceiling | OK | `config.yaml`, `scripts/`, `project-extensions/` all byte-unchanged (I ran the diff). No launch script or cap touched. No service was started at all. |
| AG-11 no new composite number | OK | No score or blended value added. |
| AG-12 manifest immutability | OK | My own query: `next_session_manifests` 24 rows, `MAX(as_of)` 2026-08-12, `SUM(prospective_eligible)` 0 — unchanged. Zero manifest writes in the mutation table. |
| AG-13 system-vs-market separation | OK | No vocabulary or surface touched. |
| AG-14 no Tapeology coupling | OK | No import, call or write to Tapeology anywhere in the diff. |
| AG-15 no outcome-tuned selection | OK | No selection rule or threshold changed; the recovery thresholds are byte-identical to their pre-run values. |
| AG-16 cohorts are not controls | OK | No cohort claim made anywhere. |
| AG-17 repair never rewrites provenance | OK — and the recurring breach did NOT recur | The four quarantined iter-8 evidence files are byte-identical to the md5s recorded in iteration 8: `bd13782d00c37abd0a0ee4a17eeb852d`, `9e9cc6fe68e08e08ab496d6be6c081bd`, `eaacb5973639ca0dd96c695b968534fb`, `190d16c0f5f8f0df0ec38396a68ee418`. No manifest eligibility was upgraded. The forbidden lane that breached this in iterations 2, 6 and 8 did not run this iteration. |

**New violations this iteration: NONE.** Ledger unchanged at 4 entries, 0 unresolved.

**Two important honesty findings, both corrected inside the iteration by the auditor** (not by the
reviewer or QA, who both repeated the developer's framing): the provenance record claimed every restored
symbol was converted by a factor of exactly 1.0, which erased AVB — the one symbol actually converted, by
2.793, and the single row whose correctness depends on that arithmetic; and it called the third driver
run a "verified zero-write no-op" while its own table counted that run's writes. I re-derived both
corrections from the database and the evidence file myself. The record now reads correctly. These are
reporting defects, not data defects — the database is right.

## Next-Step Recommendation

Build J-11 "Incident-bounded clean regeneration of derived state" next, at full depth, and nothing else
alongside it. The raw data is repaired, but the pages people actually read still show results computed
from the old, incomplete data, so nothing the user sees is fixed yet. J-11 is the journey that fixes it,
and the owner has already written out exactly how, in stages A to G.

Four things must travel into that work:

1. **Clear both stale layers, not just one.** The stored daily summaries for 11 and 12 August are still
   the ones built when only 20 companies had prices, while six background summary caches were already
   refreshed using the full 585. Rebuilding only the first leaves the mixture in place.
2. **Watch AVB.** It is the only company whose restored prices were converted onto the stored scale. Its
   trading volume was deliberately left unconverted, so any calculation that multiplies price by volume
   will read AVB about 2.79 times too high on those two days. Check what that does to its ranking in the
   rebuilt results.
3. **Do not re-run the recovery script.** Permission for live downloads is now used up, and the script
   will still try to download if anyone runs it. It needs a written permission note from the owner first.
4. **Confirm the new script and the evidence file actually get saved into the repository.** Right now
   they exist on disk but are not yet under version control, and the goal file says the evidence file is
   the only acceptable record of how the prices were checked.

Full depth is required, not preferred: the goal file forbids the destructive rebuild from running in the
light mode, and the careful mode's independent auditor has now caught something real that the reviewer
and QA both missed three iterations in a row. The destructive part must also run alone — one writer, no
servers, no browser tests — and only after it finishes may the browser check of J-01 "Sector labels are
honest", J-02 "What changed since the previous session" and J-03 "Plain-English summary with cited facts"
run for the first time since the damage. Those three checks belong to stage G and to nothing earlier.

Five older owner questions are still open and still not blocking: whether 3.44 GB is acceptable for J-09;
J-06's "underlying run unavailable" wording; the rewording of J-01's first two test steps; whether an
empty "next-session focus" is an acceptable honest result; and whether MNST should ever join the recovery
list. One new non-blocking note: the framework defect that let the forbidden test lane run three times is
still unfixed in `scripts/automation/`; this iteration avoided it with the new maintenance-isolation
contract rather than by curing it.

## Halt Justification (if halting)

Not halting.
