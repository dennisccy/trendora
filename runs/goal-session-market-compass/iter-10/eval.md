# Iteration 10 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

## Summary

This iteration built the safety checks that must pass before the big repair job may start, and
they did their job: they showed the repair is not yet allowed to begin. The stock-price record
was measured in full and the measurements are correct — I re-checked every number myself
against the live database, reading only, and they all matched. But the goal file says the
repair may not start until six safety points are proven, and two of them are still false on the
real database. Nobody on the team can fix those two without a decision from the owner, and the
goal file itself says to stop and ask in exactly this situation. Nothing broke, no data was
touched, and the database is byte-for-byte the same as before this run started.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels are honest | passing | passing (carried, not tested) | maintenance isolation — `reports/phase-goal-market-compass-iter-10-ui-test-results.md` (all-SKIPPED, contract reason) |
| J-02 What changed since the previous session | partial | partial (carried, not tested) | same — lane forbidden until J-11 Stage G |
| J-03 Plain-English summary with cited facts | partial | partial (carried, not tested) | same |
| J-04 Each candidate explains why and why-not | passing | passing (carried, not tested) | same |
| J-05 Each close freezes one manifest | partial | partial (carried, not tested) | same |
| J-06 A frozen manifest never changes | partial | partial (carried, not tested) | same |
| J-07 The Today page ten-second read | failing | failing (carried, not tested) | same; never passed, not a regression |
| J-08 Market page moves over intact | failing | failing (carried, not tested) | same; never passed, not a regression |
| J-09 The backend fits the host | partial | partial (carried, not tested) | same; re-measuring needs a backend boot, which the contract forbids |
| J-10 Bounded recovery of two deleted days | passing | passing (carried, not re-verified) | re-confirmed unchanged by my own read-only query: `daily_prices` 3,310,374 rows, 1996-01-02 → 2026-08-12, zero rows after |
| J-11 Incident-bounded clean regeneration | unknown | **partial** (first measurement) | `runs/goal-market-compass-iter-10/j11-pre-reset-inventory.json` + `j11-frozen-identity.json` (every figure re-derived by me read-only); `apps/backend/tests/test_j11_maintenance.py` — 9/9 passing under my own run; `docs/handoffs/goal-market-compass-iter-10-audit.md` §1-3 |

Maintenance isolation was active: `ui-test-results.md` is all-SKIPPED with the declared reason
"Maintenance isolation is required for this iteration — application-service boot, browser QA and
the deterministic replay lane are forbidden by contract, not unavailable." Full reviewer, QA,
auditor and coherence depth was retained. Every journey therefore keeps its prior recorded
status; none was promoted on browser evidence, because none exists. I confirmed the isolation
held rather than trusting it: no `reports/qa/goal-market-compass-iter-10-evidence/` directory,
no replay artifact, `scanner_runs` still at count 3121 / MAX(id) 3150 / MAX(created_at)
2026-08-21 00:28:16 (no boot-warmup row), and `apps/backend/data/trendora.db` frozen at
mtime=1787482245 size=8365871104 throughout, including after my own checks.

J-11 moved `unknown → partial`, not to `passing`: it is a first measurement of a journey whose
walkthrough `docs/goal.md` waives, scored on the written evidence the goal file names in place
of a screenshot. The isolation rule bars promotion to `passing`, which I did not do.

### What I verified myself, read-only, rather than accepting from a report

- Every inventory figure matched: `daily_prices` 3,310,374 rows spanning 1996-01-02 to
  2026-08-12; per-date rows for the incident set (2026-05-12 run 3149 → 542/31/11 and 2,771 own
  forward returns; 2026-08-10 run 3114 → 539/31/11 and 20; 2026-08-11 run 3150 → 539/31/11 and
  20; 2026-08-12 run 3148 → 539/31/11 and 0); the measured-into-date forward-return counts for
  all 11 dates; 24 manifests with the 12 incident rows carrying exactly the recorded hashes and
  source run ids 3112/3048/3049/3081; `data_provider_runs` 549; `watchlist` 6.
- The blocking failure: the live table definition still ends in
  `FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)`, `PRAGMA foreign_keys` reads `0`,
  and `pragma_foreign_key_check('next_session_manifests')` returns **12** violations.
- The second defect the auditor found: the 2026-08-12 version-1 manifest has an empty
  `generation_json` (length 0) and its source run 3081 is gone, so the reading code at
  `apps/backend/app/engine/compass.py:1108-1109` reports its basis as `available` while its five
  sibling versions correctly report `rebuilt`.
- Test run (targeted, single process): `apps/backend/tests/test_j11_maintenance.py` → 9 passed.
- Database untouched before and after my own work.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language | OK | No narrative, score, or display code in the diff; nothing served changed. |
| AG-2 decision-quality only | OK | No candidate/caution/narrative string anywhere in the 4-file diff. |
| AG-3 displayed numbers correct | OK (n/a) | Nothing displayed changed; `Product surface delta: None`, confirmed by coherence audit. |
| AG-4 no overfit edges | OK | No claim, ledger write, or research path touched; both ledger files hashed read-only only. |
| AG-5 determinism / no-lookahead | OK | No scoring, forward-return, or manifest-producer code changed; the new module only reads. |
| AG-6 referee gate | OK | No Evidence Claim introduced; gate passes automatically this cycle. |
| AG-7 no credentials | OK | `scan-report.md`: CLEAN — no secret, dependency, or license findings on added lines. |
| AG-8 data-shape/scale resilience | OK | The inventory uses column-projected `COUNT(*)` and one SQL-side aggregate; never an ORM hydration of the 3.3M-row price table (`j11_maintenance.py` `_count`, price aggregate). |
| AG-9 offline ingest | OK | Zero network calls. The single live-database interaction is a SELECT-only inventory script; the exhausted J-10 recovery driver is absent from the diff and was not run. |
| AG-10 host resource ceiling | OK | `git status --porcelain` empty for `config.yaml`, `scripts/start-backend.sh`, `scripts/start-frontend.sh`, `project-extensions/` — no cap moved. No service booted; tests run one process at a time. |
| AG-11 no new composite number | OK | No score, blend, or candidate number added. |
| AG-12 manifest immutability | OK | 24 manifest rows with unchanged hashes and source run ids (my own query); database byte-frozen. The change drops only the FK *declaration* in the model file — no row was written. |
| AG-13 system-vs-market vocabulary | OK (n/a) | No surface or served text changed. |
| AG-14 no Tapeology coupling | OK | No import, call, or write toward that repository in the diff. |
| AG-15 no outcome-tuned selection | OK | No threshold or selection rule touched. |
| AG-16 cohorts are not controls | OK | No cohort text, artifact, or study path touched. |
| AG-17 repair never rewrites provenance | OK | Quarantined iter-8 incident images re-hashed by me and unchanged (md5 `bd13782d…`, `9e9cc6fe…`, `eaacb597…`, `190d16c0…`). The forbidden browser/replay lane did not run for the second iteration running. No manifest eligibility, version, or timestamp changed. |

**New violations this iteration: none.** Ledger stays at 4 entries, all resolved.

**Coherence:** `runs/goal-session-market-compass/iter-10/coherence.md` reads **COHERENCE-PASS** —
no blocking violations, no new nav entries or pages, and the one registered value the diff touches
(engine identity) reuses its canonical computing function rather than duplicating it. No veto.

One honesty note, recorded but not scored as a violation: the review report records
`definition_of_done: complete` and the QA report ticks the same box for the six Stage B1
acceptance items, while two of those items are demonstrably false on the live database. That is
an evidence-quality miss by two lanes, caught by the independent auditor and confirmed by me —
not an anti-goal breach.

## Next-Step Recommendation

One decision is needed from the owner before any further work on the repair. The goal file says
the destructive clear may not start until six safety points are proven, and two of them are not
true on the real database: the real table still declares a link to the scanner runs, that link
is currently switched off rather than removed, and twelve existing rows already break it. The
code change made this run fixes the description of the table, not the table itself — and
changing the real table means writing to the 7.8 GB database, which this run was forbidden to do
and which the goal file says needs the owner's word.

Please pick one of the three options listed in the halt justification below. Once you answer, the
next iteration should be the full repair (stages C to G) at full depth, run alone with no web
server, no browser tests and one writer only — and it should carry three fixes with it: correct
the reading code so a manifest with no recorded history says "no recorded basis" instead of
falsely saying its original basis is intact; open the database in a true read-only mode for the
inventory step; and add an independent check at the end that all eleven rebuilt days really came
from one single version of the code, because today's identity check cannot see changes to the
scoring files.

Five older owner questions are still open and still not blocking: whether 3.44 GB is acceptable
for J-09 "The backend fits the host"; the wording of J-06's "underlying run unavailable" state;
the rewording of J-01's first two test steps; whether an empty "next-session focus" is
acceptable; and whether MNST joins the recovery list.

## Halt Justification

The work is blocked on a decision only the owner can make, and the goal file itself says so:
"If this contradiction cannot be resolved safely inside the current repository without a risky
migration, STOP before J-11 and surface it as an owner decision." This is that surfacing.

Every way forward is an owner action:

1. **Accept the current state in writing.** Add a dated note to `docs/goal.md` saying safety
   points 1 and 4 are satisfied at the code-description level only, and that the real table
   keeps a switched-off, already-broken link. Worth knowing before deciding: no manifest points
   at any of the four scanner runs the repair would delete — the four they do point at are
   already gone — so the practical risk today is nil. What blocks us is the literal wording of
   the gate plus the twelve standing violations.
2. **Authorise a small, bounded rewrite of the real table.** Twenty-four rows, but it is a write
   to the 7.8 GB canonical database, so it needs its own single-writer isolation and a
   byte-for-byte proof that every stored artifact survives unchanged.
3. **Reword the gate.** Change safety point 1 so it asks about the table the rebuild creates from
   the current code rather than the table as it stands on disk today.

Two smaller decisions ride along and can be answered at the same time: whether the fix to the
false "basis is intact" reading may land before the final verification stage (it changes what ten
manifests report, and the checking lanes that would confirm it are closed until then); and
whether the one-version-of-the-code check is allowed to stay blind to the scoring files, given
that a change to exactly those files is already planned for the repair stage.

No other work is available in the meantime: `docs/goal.md`'s Loop-mechanics gate shuts every
other product, research and browser lane until J-11 Stage G passes, so J-01 through J-09 cannot
legally be worked on or measured. Halting now is also the safe direction — the next step after
this decision is the destructive clear on the canonical database, and this session has already
lost data once to a destructive step that ran without a clean gate.
