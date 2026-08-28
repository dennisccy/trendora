# Iteration 25 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

Both halves of this iteration really happened, and I checked them myself rather than trusting the
write-ups. The memory measurement was re-taken on the real database and it missed its goal again: the
backend needs about 2.99 GB of memory where the goal asks for 2.5 GB or less. That is an honest miss,
recorded plainly and without moving the goalposts, and the goal file itself says a miss is an owner
question, not a reason to stop the loop. The three journeys that were meant to be re-checked last round
but silently were not — J-01 "Sector labels are honest and nearly complete", J-04 "Each next-session
candidate explains why and why-not", and J-10 "Bounded recovery of the two deleted trading days" — were
genuinely re-checked this time in a real browser and all three passed. Nothing that worked before stopped
working, and no rule in the goal file was broken.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest and near-complete | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-25-evidence/J-01-verify.png — row UT-J-01 PASS in reports/phase-goal-market-compass-iter-25-ui-test-results.md; opened: GRMN, stored sector "Consumer Discretionary", 1/539, regime 73.18, scores badged "Not yet proven" |
| J-02 What changed since previous session | partial | partial (not tested) | carried — product surface byte-unchanged |
| J-03 Plain-English summary with cited facts | partial | partial (not tested) | carried — product surface byte-unchanged |
| J-04 Candidate explains why and why-not | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-25-evidence/J-04-verify.png — row UT-J-04 PASS; capture-defect carried (see note below) |
| J-05 Close freezes one manifest, byte-consistent | partial | partial (not tested) | carried — product surface byte-unchanged |
| J-06 A frozen manifest never changes | partial | partial (not tested) | carried — product surface byte-unchanged |
| J-07 Today page answers the ten-second read | failing | failing (not tested) | carried — product surface byte-unchanged |
| J-08 Market page moves over intact | failing | failing (not tested) | carried — /market route still absent |
| J-09 Backend fits the host | partial | partial (re-measured, target missed) | reports/perf-budgets.md Addendum 41 + its "iter-25 AUDIT CORRECTION" block; docs/handoffs/goal-market-compass-iter-25-dev.md (walkthrough waived by J-09's own acceptance text) |
| J-10 Bounded recovery of two deleted days | passing | passing (re-verified) | reports/qa/goal-market-compass-iter-25-evidence/J-10-verify.png — row UT-J-10 PASS; opened: AVB at as-of 2026-08-11 renders "Invalid below the 50-DMA at $187.94", the exact value the golden asserts |
| J-11 Incident-bounded regeneration | passing | passing (spot-checked, not re-verified) | CLOSED by owner ruling; evaluator re-derived its certified state read-only (see Anti-goal check) |

Notes on the three status-relevant rows I opened myself:

- **J-04 keeps its capture defect** (7th iteration running). The picture is again the last step of the
  walkthrough at 2026-03-30 and stops just above the candidate card, so it does not itself show a
  why/why-not reason. What proves the journey is the replay's exact-value checks, which the independent
  auditor confirmed pin real numbers ("Strong leader (81.2)", "Not priority (20)" → TRV). Recorded as
  `evidence_makeup`, not as a product problem. A better picture rides the next browser round as a
  passenger, never as its own iteration.
- **J-09 has no browser row and should not have one.** Its own text in the goal file waives the
  walkthrough and replaces it with the dated measurement. The "Missing Target Journeys: UT-J-09" line in
  the merged results file records that waiver, not a skipped test.
- **The re-check lane genuinely ran this time.** Last round it was silently empty because of a
  text-reading bug. I re-ran the fixed reader myself over three real iteration documents: iteration 25
  correctly yields J-01 J-04 J-10, iteration 24 (the one that broke) now also yields J-01 J-04 J-10, and
  iteration 7 correctly yields nothing.

## Anti-goal Check

Worked from `iter-25/scan-report.md` (CLEAN) and `iter-25/iter-diff.md` (4 files, all inside the
automation harness), plus my own read-only queries against the live database. Every category answered.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials (AG-7) | OK | scan-report.md: CLEAN, no findings on added lines. Diff adds no config or env file. |
| Paid / external SaaS | OK | No manifest touched (no package.json / requirements / pyproject in the diff file list). |
| License changes | OK | scan-report.md: no license findings; no LICENSE file in the diff. |
| Fabricated / substituted data | OK | Zero application code changed — I confirmed `git diff --stat HEAD -- config.yaml apps/ project-extensions/` is empty. Screenshots show `provider: seed`. |
| AG-1 unproven values badged | OK | J-01 screenshot shows all three scores badged "Not yet proven". |
| AG-2 no advice / orders | OK | No product code or copy changed. |
| AG-3 displayed numbers correct | OK | J-10's page shows $187.94, the exact value its golden asserts; J-04's golden pins 81.2 / 20 / TRV; the 4-endpoint byte-identity check re-computes every md5 (auditor kept all 8 response bodies). |
| AG-4 / AG-5 / AG-6 / AG-11 / AG-13 / AG-15 / AG-16 | OK | No scoring, manifest, vocabulary or evidence-claim code changed — application tree byte-unchanged. |
| AG-8 data-shape resilience | OK | No data-shape change; frontier unchanged at 2026-08-12. |
| AG-9 offline-deterministic ingest | OK | No ingest job ran and no live fetch occurred. I confirmed the price frontier is still 2026-08-12 and the two recovered days still hold 585 rows each — no dataset advancement, and the spent exception was not re-entered. |
| AG-10 host resource ceiling | OK | I read the values myself: `cache_size -65536`, `pool_size 24`, `max_overflow 44`, `memory_cap_mb 8192`, `malloc_arena_max 2`, `limit_concurrency 64`; `host-guard.env` intact (CPU 0-15, BLAS 8, MEMORY_HIGH 12G). `git diff` on config.yaml is empty. Backend launched via `scripts/start-backend.sh`, the sanctioned script. The measured 2.99 GB sits well under the 8192 MB cap. |
| AG-12 manifest immutability | OK | My own read-only query: `next_session_manifests` still 24 rows, version spread 16/3/2/1/1/1 unchanged, newest `available_at_utc` still 2026-08-20 14:55:02. Nothing minted, nothing mutated. |
| AG-14 no Tapeology coupling | OK | No imports or calls added; diff is four shell files in the harness. |
| AG-17 repair never rewrites provenance | OK | `prospective_eligible` is true on ZERO of the 24 manifests — unchanged. |
| AG-18 migration preserves everything | OK | No schema migration this iteration; column set and row count unchanged. |
| Owner ruling — canonical database | OK | The database WAS booted and served ~2,614 read requests. This was sanctioned: ruling item 5 resumed normal work once the launcher fix landed (it did, at iteration 24), and item 6 tells the loop not to stop for recomputable cache residue. I checked what the boot actually left behind: 4 new rows in two recomputable cache tables, no new saved briefing (the hazard the iteration-22 note warned about), and no new day-record (`scanner_runs` max id still 3158, newest created 2026-08-26). None of the categories that still need owner approval — data repair, manifest mutation, schema change, network access, destructive change — was touched. |

Coherence: **COHERENCE-PASS** (`iter-25/coherence.md`). No goal-edit drift — I ran the hash tool myself
and all eleven journeys' hashes are byte-identical to the recorded ones, and no `journeys-changed.md`
exists. No `browser-infra.json`, no deferred rows, no maintenance isolation.

Anti-goal ledger unchanged: **8 entries, 0 unresolved.**

## Next-Step Recommendation

Build **J-05 "Each close freezes one next-session manifest, exported byte-consistently"** and **J-06 "A
frozen manifest never changes"** next. They are the goal file's own next pair, they need no permission
from the owner, and they are the last two items before the two page-building journeys J-07 and J-08.

Run the next round at **full depth**, with the independent auditor. This round is the reason: the auditor
found and fixed two real defects that the developer, the reviewer, the quality check and the coherence
check all passed over — including a text-reading bug in the engine's own safety machinery that would have
made it quietly re-test a journey nobody asked for. J-05 and J-06 are about frozen records never
changing, which is the most dangerous area in this whole goal, so the extra pair of eyes is worth it.
One practical warning: five times this session a plan asking for full depth was automatically downgraded
to a cheaper run on cost grounds. Only the owner can make full depth stick, by adding the line
`Depth enforcement: required` to the next plan. Neither the planner nor I may grant that to ourselves.

Three things to carry, none of them blocking:

1. **One owner question is now sharper.** The backend needs about 2.99 GB of memory; the goal asks for
   2.5 GB or less. It is better than the 3.44 GB measured back at iteration 4, but still over, and the
   reason for the improvement is genuinely unknown — the explanation first written down was checked and
   found to be false. The measurement also left no raw record behind, so the number rests on the
   measuring agent's own report. Please read it as a caveated figure, not a settled result, and tell the
   loop whether ~2.99 GB is acceptable.
2. **Future measurements must keep their raw evidence** — start and end times in UTC and the sampler
   output kept on disk. The byte-for-byte check in this same round did exactly that and is the model
   to copy.
3. **Two small carried items:** J-04's picture still needs re-taking so it includes the candidate card,
   and J-01's automated re-check script tests much less than the journey claims — worth strengthening the
   next time work legitimately touches J-01.

## Halt Justification (if halting)

Not halting.
