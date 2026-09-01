# Iteration 31 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The round did what it set out to do, and I checked it myself rather than taking anyone's word.
The two oldest unfinished journeys — J-02 "What changed since the previous session" and J-03
"Plain-English summary with cited facts" — have been stuck half-done since round 6, when the
database was still broken. The database is healthy again, and both now work. I opened the pictures
of the page and I also read the saved record straight out of the database, read-only, and the
numbers on the screen match the stored numbers exactly. Ten journeys out of eleven now pass. Only
one is left: J-09 "The backend fits the host", about how much memory the program uses. I am
escalating because the last piece is the riskiest one in the whole project — it deliberately puts
the owner's computer under load, on the same machine this project once froze — and this round ran
in light mode with no independent checker, even though its own plan asked for the full team.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest and near-complete | passing | passing | reports/qa/goal-market-compass-iter-31-evidence/J-01-verify.png |
| J-02 "What changed" since previous session | partial | **passing** | reports/qa/goal-market-compass-iter-31-evidence/J-02-whatchanged-suppressed.png + J-02-verify.png |
| J-03 Plain-English summary with cited facts | partial | **passing** | reports/qa/goal-market-compass-iter-31-evidence/J-03-summary-citedfacts.png + J-03-verify.png |
| J-04 Candidate explains why and why-not | passing | passing | reports/qa/goal-market-compass-iter-31-evidence/J-04-verify.png (capture defect, 13th round) |
| J-05 Close freezes one manifest | passing | passing | reports/qa/goal-market-compass-iter-31-evidence/J-05-verify.png |
| J-06 A frozen manifest never changes | passing | passing | reports/qa/goal-market-compass-iter-31-evidence/J-06-verify.png |
| J-07 Today page answers the ten-second read | passing | passing | reports/qa/goal-market-compass-iter-31-evidence/J-07-verify.png (spot-check) |
| J-08 Market page intact, history honest | passing | passing | reports/qa/goal-market-compass-iter-31-evidence/J-08-verify.png |
| J-09 Backend fits the host | partial | partial | not targeted; reports/perf-budgets.md Addendum 41 + its iter-25 AUDIT CORRECTION |
| J-10 Bounded recovery of two trading days | passing | passing | reports/qa/goal-market-compass-iter-31-evidence/J-10-verify.png |
| J-11 Incident-bounded clean regeneration | passing | passing | reports/qa/goal-market-compass-iter-31-evidence/J-11-verify.png |

Merged results: `reports/phase-goal-market-compass-iter-31-ui-test-results.md` — **10/10 PASS, 0
skipped**. No `DEFERRED-BUDGET` rows, no `browser-infra.json`, no `journeys-changed.md`, NOT
maintenance isolation. All eleven `spec_hash` values are byte-identical to the recorded ones (I ran
`goal_gate.py hash-journeys` and compared every one), so no goal text moved under a recorded pass.

### What I verified myself, rather than accepting

- **J-02 / J-03 against the stored record.** Read-only from manifest row id 28 (as_of 2026-08-12,
  version 7): `prior_as_of` 2026-08-11, `gap_days` 1; `changes` = 17 entries in the order
  sector(5) → theme(2) → stock(10), with **zero** entries failing their threshold; `suppressed` = 36
  entries = `suppressed_count`, with **zero** entries at or above their threshold; every
  `drill_href` carries `?asof=2026-08-12`. The narrative holds exactly 4 sentences whose text and
  facts match the screen word for word. I counted the 36 suppressed rows in the screenshot myself
  and they match.
- **The two facts J-03 step 2 requires.** `regime_score` 73.18 and `severity` 25.85 in the cited-facts
  panel are the same values printed on the Regime and Market-phase cards higher up the *same*
  screenshot — an on-screen cross-check, not just a claim about an API.
- **The steps no lane checked.** The browser lane wrote, twice, that the dev-handoff citation steps
  were "outside browser-QA scope; not verified here", and the handoff never made those citations. I
  found the four tests and ran them: `test_quiet_pair_yields_no_changes_but_nonzero_suppressed`,
  `test_new_to_universe_reported_distinctly_never_as_score_change`,
  `test_content_hash_stable_across_identical_rebuilds`,
  `test_direction_na_velocity_variant_when_phase_unavailable` — **4 passed**.
- **The database was never written to.** `apps/backend/data/trendora.db` still carries mtime
  2026-09-01 01:32:31, which is *before* this iteration started (02:56), and its write-ahead log is
  0 bytes. Not one byte changed.

## Anti-goal Check

Worked from `iter-31/scan-report.md` (**CLEAN**) and `iter-31/iter-diff.md` (**no changes**); I also
confirmed `git diff <snapshot>..HEAD -- apps config.yaml scripts` is empty with no untracked product
files, so **zero application source lines changed this iteration**.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 unproven claims | OK | No evidence-ledger claim introduced; zero code change. |
| AG-2 decision-quality only | OK | I read all four stored sentences: no order, target, forecast or buy/sell wording; page banner still "Research-only · decision support · no orders". |
| AG-3 displayed numbers correct | OK | Strongest form: I re-derived the What-changed and Summary content from stored manifest row 28 read-only and it byte-matches both screenshots (17 changes, 36 suppressed, 4 sentences, 73.18 / 25.85). |
| AG-4 no overfit edges | OK | Nothing new surfaced as proven; zero code change. |
| AG-5 determinism / no lookahead | OK | Zero code change; `test_no_forward_returns_or_lookahead_import` and `test_no_network_or_lookahead_imports_in_compass_module` sit inside the 49-passing set. |
| AG-6 evidence claims refereed | OK | No Evidence Claims this cycle. |
| AG-7 no hardcoded credentials | OK | scan-report CLEAN on added lines; product diff empty. |
| AG-8 resilience / column-projected reads | OK | Zero code change; `test_column_projected_reads_only_no_full_record_json_sweep` passing; the 1996-02-01 view degrades honestly ("reported NA, never fabricated"). |
| AG-9 offline-deterministic ingest | OK | `data_provider_runs` still 549 rows, newest 2026-08-23; `MAX(daily_prices.date)` still 2026-08-12; DB file untouched since before the iteration began. Zero external fetch. |
| AG-10 host resource ceiling | OK | `scripts/` unchanged; services launched via `scripts/start-backend.sh` / `start-frontend.sh` with the host guard active. |
| AG-11 no new composite number | OK | Zero code change; `test_no_composite_score_field_anywhere` passing. |
| AG-12 manifest immutability | OK | Re-derived read-only AFTER every lane: **28 rows, 18 distinct as_of, max id 28**, census byte-identical to the pre-iteration census. Zero mints, zero mutations. Control `CREATE TABLE` refused. |
| AG-13 system-vs-market separation | OK | From the captures: readiness words (GO, Ready) only in the chrome band; the body cards and all four stored sentences carry market vocabulary only. |
| AG-14 no Tapeology coupling | OK | Zero code change, no new imports. |
| AG-15 no outcome-tuned selection | OK | Selection rule explicitly out of scope and untouched. |
| AG-16 cohorts are not controls | OK | Cohort blocks unchanged; `prospective_eligible=1` count is 0, so consumers fail closed. |
| AG-17 repair never rewrites provenance | OK | Re-derived: `prospective_eligible=1` on **0 of 28** rows; newest `available_at_utc` is still iter-30's 2026-09-01 00:13:07. Nothing upgraded. |
| AG-18 migration preserves everything | OK | No migration ran; schema column list unchanged. |

**Ledger: 9 total, 0 unresolved — no new entries.** Considered and rejected as a ledger entry: the
replay lane again requested `?asof=2026-03-30`, outside this plan's declared safe set. Nothing
permanent resulted — that date already carried a manifest row and the post-lane census is unchanged
at 28 — the developer flagged it explicitly instead of absorbing it, and the browser lane then
repointed the golden to `2025-04-15`. A process note, not a breach.

## Findings A Later Lane Had To Catch (this round, again)

1. **The reviewer caught a real one.** The first handoff claimed "no discrepancy was found anywhere".
   That was wrong: J-03's stored replay script had two stale expected values, and the replay lane
   hard-failed on it. The developer corrected the script, re-ran the lane green, and rewrote the
   claim honestly. The fix loop worked as designed — this is not a fail-open.
2. **Nobody caught this one but me — the same mistake as last round, moved to a new place.** The
   browser lane overwrote both replay scripts *after* the replay lane had already run:
   `J-02.json` at 03:35:14 and `J-03.json` at 03:35:18, against replay results written at 03:31:03.
   Both were only syntax-checked, never executed. So the two journeys promoted today have no working
   automatic guard. This is the third round in a row for this pattern (J-07, then J-11, now J-02 and
   J-03) — and it is the very lesson this iteration's own plan quoted in writing.
   The good news: the plan's binding instruction on J-11 was honoured exactly — `J-11.json` ran first,
   passed on its first-ever execution, and its timestamp proves it was not edited afterwards. That
   closes last round's J-11 gap.
3. **Nobody caught this one but me either.** The handoff recorded an alarming "Observation" that the
   comparison cohort and shadow cohort read back empty at the newest date. They do not. I read the
   stored row: 539 cohort entries and 25 shadow entries, exactly the counts printed on the page. The
   developer looked for them in the wrong place. Left uncorrected, this would have sent a future
   round hunting a bug that does not exist.
4. **The last open journey is not where we thought it was.** See below.

## Next-Step Recommendation

**Finish J-09 "The backend fits the host" — it is the only journey left, and its remaining work is
not what six earlier rounds recorded.** Every other journey now passes.

For a long time the record said J-09 was waiting on the owner: a memory measurement of about
2.99 GB against a 2.5 GB goal, with the goal's own words saying "stop for owner review" when the
target is missed. I read the measurement record and that is not the whole story. The audit note
attached to it says plainly that the 2.99 GB figure **is not independently corroborated — no
sampler log and no `/proc` capture from that run survives, so it rests on one agent's report** — that
a second, unrelated automated run was using the same computer throughout the measurement, and that
the machine was actually handling about twice the traffic the write-up describes. The journey itself
asks for a `/proc` reading. So the honest next step is ordinary work that needs nobody's permission:
**measure it again, properly, on a quiet machine, and keep the raw evidence this time.** Only if that
clean number still misses the target does the owner's decision become the only way forward.

**Run it at full depth.** Only the owner may add `Depth enforcement: required`, and standing guidance
keeps `CHAIN_REQUIRE_FULL_DEPTH` and `CHAIN_MAINTENANCE_ISOLATION` OFF.

**One safety point the owner should read before that round runs.** J-09's measurement deliberately
loads the computer with a burst of simultaneous requests. This is the same machine that a goal-mode
run froze on 20 August 2026. Nothing else should be running on it during that round.

**Two repair items that should ride along:** (1) run the rewritten J-02 and J-03 replay scripts and
report their real results out loud, and do not edit them again afterwards — they have never been
executed; (2) the new J-02 script checks for the exact words "Suppressed moves (36)", a number that
is specific to one date, so it will break if the data ever moves — worth loosening.

**Nine carried items, none blocking:** J-04's picture still needs re-taking to include the candidate
card (13th round owed); J-02, J-03, J-05, J-06 and J-08 all still owe a recorded walkthrough, and
J-07's is only four steps (all passenger tasks, never an iteration goal); one test is red on three
files untouched since an old commit and should be fixed or formally waived; the "What changed" and
"Leadership rotation" lists still show the identical rows and that is the owner's call; the
iteration-23 throw-away copy (7.8 GB) may still be deleted; `apps/frontend/.next-verify/` build
cache is tracked in git and dirties every diff; J-01's automatic re-check still asserts far less than
the journey claims; and the dev handoff omitted three fixture citations its own journey steps require
(I supplied them by running the tests).

**Five older owner questions remain open and non-blocking:** J-06's "underlying run unavailable"
wording; J-01's first two test steps; whether an empty "next-session focus" is acceptable; whether
MNST joins the recovery list; and whether 12 August should keep showing its "rebuilt" note.

**One mechanical item:** the whole iteration — plan, handoff, reports, evidence folder and both
rewritten replay scripts — is uncommitted at scoring time; confirm it lands.

**One standing framework note:** `goal_gate.py`'s duplicate-journey-heading defect is still unfixed
and must be closed before any GOAL_ACHIEVED certification.

## Halt Justification (if halting)

Not halting. ESCALATE keeps the loop running; it only requires the next round to use the full team.

Why not GOAL_ACHIEVED: J-09 "The backend fits the host" is still unfinished, so not every must-have
journey passes.

Why not REGRESSION: nothing that worked stopped working. No journey fell back, no saved briefing was
added, altered or removed — the count is 28 before and 28 after, and the database file was never
written to at all.

Why not STALLED: nothing waits on the owner. I found that the last journey's blocking measurement is
unsupported by any surviving raw evidence, which turns the next step back into ordinary work the
team can do on its own.

Why ESCALATE rather than CONTINUE, in plain terms: the plan for this round asked for the full team
and gave written reasons; the system ran the light version anyway, for the eighth time this session.
That matters here because a plain recommendation has now failed twice — round 27 asked for full and
round 28 ran light; round 30 asked for full and this round ran light — while an escalation has held
the depth every time it was used. And the work left is the most physically risky in the project: it
puts the owner's computer under deliberate load, on the machine this project already froze once, and
the rule that governs it is one only the owner may change. The last time that measurement was taken,
three of its claims were wrong and only the independent checker found them. This round, running
light, the reviewer caught a false "nothing is wrong" claim and I caught two more things no lane
caught. That is twenty-two rounds in a row where someone later found what the earlier checks missed.
The final journey should not be the one we check least.
