# Iteration 14 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

**Owner-facing lines (corrected by this evaluation):** `J-11 STAGE D READY: NO` · `J-11 STAGE D AUTHORIZED: NO`

## Summary

This iteration built the five things the owner asked for, wrote nothing to the real database, and I
checked that myself: the database file has the same timestamp, the same size and an empty write log
that it had when the last iteration finished. Four of the five pieces are sound. The fifth — the
check on the share-trading numbers for one company, AVB — answers a price-and-volume question using
price alone, and its own answer file says the matter is "proven" when only half of it was tested. The
owner's own rule says that half-tested state must produce a "not ready" answer, so the iteration's
headline "ready: yes" does not stand. Nothing broke, nothing was lost, and no journey changed. I am
halting because every way forward now needs a decision only the owner can make.

## Journey Results This Iteration

Maintenance isolation was active by contract (ruling A5/A13): no web server, no browser, no replay.
`reports/phase-goal-market-compass-iter-14-ui-test-results.md` is all-SKIPPED with `**Reason:**`
naming maintenance isolation, so every journey KEEPS its prior recorded status and none may be
promoted on this iteration's evidence. Nine journeys therefore went unverified this iteration.

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest on new runs | passing | passing (carried, not re-verified — maintenance isolation) | `reports/phase-goal-market-compass-iter-14-ui-test-results.md` (SKIPPED, contract) |
| J-02 What changed since previous session | partial | partial (carried, not re-verified) | same |
| J-03 Plain-English summary with cited facts | partial | partial (carried, not re-verified) | same |
| J-04 Each candidate explains why / why-not | passing | passing (carried, not re-verified) | same |
| J-05 Each close freezes one manifest | partial | partial (carried, not re-verified) | same |
| J-06 A frozen manifest never changes | partial | partial (carried, not re-verified) | same |
| J-07 Today page ten-second read | failing | failing (carried, not re-verified) | same |
| J-08 Market page moves over intact | failing | failing (carried, not re-verified) | same |
| J-09 Backend fits the host | partial | partial (carried, not re-verified) | same |
| J-10 Bounded recovery of the two deleted days | passing | passing (re-derived read-only by me; unchanged) | my own query: 585 symbols hold a 2026-08-11 row; AVB's 08-11/08-12 rows present; DB file mtime `1787591622.4277432` / size `8,365,871,104` unchanged since Stage C |
| J-11 Incident-bounded clean regeneration | partial | partial (advanced; Stage D preconditions built, readiness answer corrected to NO) | `runs/goal-market-compass-iter-14/j11-stage-d-preflight-gate.json` (11/11 pass), `j11-stage-d-attempt-identity.json`, `j11-avb-bridge-diagnostic.json`, `docs/handoffs/goal-market-compass-iter-14-audit.md` §5, plus my own read-only derivations below |

Spot-checks (methodology A.4), both outside any replay set because no replay lane ran: **J-10** —
re-derived from the live database read-only, consistent with its recorded `passing`. **J-01/J-04** —
no product code on their surfaces changed this iteration (`iter-diff.md` lists nine files, all backend
J-11 maintenance tooling and tests), so their prior evidence stays valid under evidence durability
(methodology A.6); no contradiction found.

## What this iteration got right (re-derived, not taken from any lane's prose)

- **Zero writes to the live database.** I ran `stat` myself after all lanes finished:
  mtime `1787591622.4277432`, size `8,365,871,104`, `-wal` size `0` — identical to the TRUE-start
  capture in `runs/goal-market-compass-iter-14/j11-stage-d-db-file-true-start.json` and to iteration
  13's Stage C end state.
- **The fresh attempt identity is genuinely recomputed**, not copied: the artifact records
  `53d2ffd1…`, and the live database still holds 0 runs stamped with it (nothing was created), 34 runs
  stamped with the older `6261ca17…` and 3,083 unstamped — none touched.
- **The eleven Stage D preflight checks all pass and all genuinely fire on drift** — the auditor
  exercised every one of the eleven negative branches by hand
  (`docs/handoffs/goal-market-compass-iter-14-audit.md` B4).
- **The evidence-corruption incident inside this iteration is genuinely closed.** A new test called the
  destructive Stage C command without naming an output folder, fell back to the committed iteration-13
  evidence folder, and overwrote three files. The reviewer caught it and failed the iteration; the files
  were restored from version control; the command now refuses to run at all without an explicit output
  folder; and the handoff retracted its first, wrong explanation by name. I verified the end state
  myself: `git status --porcelain runs/goal-market-compass-iter-13/` returns zero lines.

## The decisive question: does the AVB classification stand? (my own adjudication)

**It does not. The honest label is AVB-D — evidence insufficient — which by the iteration's own rule
(TC-25 / Goal 5) forces `J-11 STAGE D READY: NO`.** I did not inherit the developer's label or the
auditor's qualification; six checks, each re-derived:

1. **The classifier never reads volume.** `apps/backend/app/engine/j11_avb_diagnostic.py:159-267`
   classifies from close ratios (`:189`) and close-to-close continuity (`:146-156`) only. The label
   `bridged+compensating` — the one that would name a volume problem — cannot be produced by any code
   path; only `bridged+raw`, `raw+raw` and `mixed/indeterminate` are reachable. `volume_a_equals_b:
   true` is true by construction (`volume_b = stored_volume`, `:288`). Representations A and B differ
   only in close, so the entire decision-impact trace measures the close bridge, not the volume
   convention. The artifact nevertheless states the convention "(bridged close, untransformed volume)
   is proven internally consistent".
2. **The auditor's rescue rests on a factual error.** The audit's B1 says the bridge was calibrated
   against `indicators.adjclose`, "which carries no volume at all", so no adjustment-scaled volume
   could enter "by construction". The code says the opposite: `apps/backend/app/engine/j10_recovery.py:643`
   calibrates with `provider.get_daily(...)`, and `apps/backend/app/data_providers/yahoo_provider.py:351-369`
   builds close **and** volume from the same `indicators.quote[0]` block. The iteration-8 redesign
   deliberately abandoned adjusted-close calibration (`j10_recovery.py:62-71`). So the 2.7930 factor
   measures a scale gap between the stored series and *exactly the series the volume came from* — which
   makes the volume question live, not closed.
3. **The pool-wide check cannot speak to AVB.** 565 of 566 symbols carry a bridge factor ≈ 1.0
   (`j11-avb-bridge-diagnostic.json` → `pool_bridge_factor_distribution`), so their volumes are on-basis
   trivially. AVB is the only symbol whose price series sits on a different scale, and it is the one
   symbol the pool test structurally cannot test.
4. **No persisted evidence can settle it.** `runs/goal-market-compass-iter-9/j10-population-evidence.json`
   records only `stored_close` / `fallback_close` / `ratio` per pair — I read every field of AVB's row;
   there is no volume anywhere in it, nor in `j10-population-summary.json`. The comparison fetch *did*
   return volumes (`get_daily` bars) and `j10_recovery.py:644` kept only `b.close`. The one measurement
   that would decide this existed in iteration 9 and was discarded; obtaining it now requires a network
   call, and AG-9's recovery exception is exhausted.
5. **My own read-only statistics point the other way on 2026-08-11.** Divided by exactly the bridge
   factor, AVB's stored volume that day (1,549,436 → 554,756) lands at the **39.8th percentile** of
   AVB's own 5,392-day distribution of "volume ÷ median of the prior five days", and inside the
   451,300-666,100 range of the four adjacent stored days. Undivided it is the **98.7th percentile** of
   that same distribution and ranks **579th of 582** pool symbols that day, on a day when the pool's
   median ratio was 0.826. (2026-08-12 is an outlier either way: 16.1× undivided, 5.8× divided.)
6. **The price side shows the provider re-based the series between ingests.** AVB's 2026-08-05..08-10
   rows were acquired after the seed window — their row ids are 3,308,006-3,308,009 against 1,010,918
   for AVB's 2026-07-01 row, and `docs/goal.md` records all post-seed acquisition as `provider='yahoo'`
   — yet iteration 9 asked the same provider for those same dates and received exactly 1/2.7930 of the
   stored closes. A provider that re-bases a price series normally re-bases its volume inversely. That
   is precisely the hypothesis the classifier cannot express.

**What I explicitly do NOT claim.** Not AVB-C: "inconsistent with the stored convention **and**
materially affects canonical Stage D output" is not established — the traced impact is small. Because
average dollar volume depends only on the product close × volume, the worst case of the volume question
is arithmetically identical to representation B, which *was* traced: universe admission unchanged (both
far above the $50M floor), Risk bucket E→E, setup status Avoid→Avoid, candidate eligibility False→False,
leadership untouched (it reads no volume at all), and 4 (08-11) / 35 (08-12) other pool names shifting
by one position in the liquidity ranking. Only 2 of the 11 dates Stage D will rebuild have a recovered
date inside their 63-day averaging window. So the open question is **small but open** — and the owner's
gate says an open one is a "no".

Two further gaps I confirmed myself and agree with: `j11-stage-d-readiness.json`, the headline verdict
file, has **no committed producer** (`stage_d_readiness_verdict` at `j11_stage_d.py:393` is called only
from `tests/test_j11_stage_d.py:333,340` — verified by grep), so the headline answer is not reproducible
from committed code; and `git ls-files runs/goal-market-compass-iter-14/` returns **0** while eleven
artifacts sit there untracked and two of this iteration's own scripts default into that folder. The
engine's close-of-iteration commit is expected to capture them — iteration 13's identical folder is
tracked and that is the only reason this iteration's accident was recoverable — so I score DoD item 10
**pending, not met**, and it must be confirmed rather than assumed.

## Anti-goal Check

Worked from `runs/goal-session-market-compass/iter-14/scan-report.md` (CLEAN) and `iter-diff.md`
(9 files: two new backend engine modules, two new read-only scripts, four test files, one script edit).

| Category / Anti-goal | Status | Notes |
|-----------------------|--------|-------|
| Secrets / credentials (AG-7) | OK | scan-report: no secret findings on added lines; no config or env file in the diff |
| Paid / external SaaS | OK | no dependency manifest changed; scan-report has no dependency finding |
| License changes | OK | no LICENSE or license-field change in the diff |
| Fabricated / substituted data | OK, with a defect noted | no data was ingested, served, substituted or written. The AVB artifact **over-claims its own evidence** (see above) — that is the same class of honesty failure but it is not an AG-1 breach: AG-1 governs scores/rankings/edges presented as proven on served surfaces against the evidence ledger, and this is an internal maintenance file behind no endpoint |
| AG-9 offline-deterministic ingest | OK | zero network calls: the two new modules import no provider and no HTTP client (verified by reading their import blocks); the diagnostic reads only the committed iteration-9 evidence file and stored prices; J-10 was not reopened |
| AG-5 no-lookahead | OK | the diagnostic calls the real `score_stocks(session, asof, cfg)` for a given as-of; no post-as-of bar is introduced; nothing is written |
| AG-8 data-shape resilience | OK | `fetch_avb_stored_series` (`:126-131`) is a column-projected select; the pool-wide percentile work uses projected queries, no whole-table ORM load |
| AG-10 host resource ceiling | OK | no launch script changed, no HOST-GUARD block touched; the bounded maintenance-script pattern is the one `docs/goal.md` J-11 step 9 itself prefers and iterations 10-13 established |
| AG-12 / AG-17 / AG-18 (manifests, provenance, schema) | OK | zero live writes proven four ways plus my own `stat`; 24 manifest rows, DDL and full-row values byte-identical to iteration 13's certified baseline; no schema change |
| AG-17 (incident evidence must not be rewritten) | **Breached in-iteration, fully reversed, resolved** | a new CLI test overwrote three committed iteration-13 Stage C evidence files. Detected by the reviewer (FAIL), restored from version control byte-for-byte, root cause fixed (the command now refuses to run without an explicit output folder and exits before touching the database), misattribution retracted. Verified by me: `git status --porcelain runs/goal-market-compass-iter-13/` → 0 lines. Recorded in the ledger as critical / resolved |
| AG-2, AG-4, AG-6, AG-11, AG-13, AG-14, AG-15, AG-16 | OK | no served surface, no new score or composite number, no selection-rule or threshold change, no Tapeology coupling, no evidence claim, no cohort/causal language — nothing in the diff touches any of these |

**Ledger after this iteration: 6 total, 0 unresolved.**

Coherence: **COHERENCE-PASS** (`runs/goal-session-market-compass/iter-14/coherence.md`).
Deterministic scan: **CLEAN**. Review: **PASS_WITH_NOTES** (after an in-iteration FAIL that the fix
pass closed). QA: **PASS**. Audit: **PASS_WITH_GAPS** (B1/B3 IMPORTANT, B2/B4/B5 gaps, B6/B7
observations).

## Next-Step Recommendation

**One decision is needed from the owner, and it is about one company's trading-volume numbers on two
days.** The team's answer file says AVB's restored prices and volumes are on a matching scale and
calls that proven. It is not proven: the check that produced it looks only at prices, and the one
label that could have flagged a volume problem can never be produced by that code. My own reading of
the stored numbers leans the other way for 11 August — dividing that day's volume by the exact bridge
factor puts it right in the middle of AVB's own normal range, while leaving it undivided makes it the
579th of 582 busiest names that day. The measurement that would settle it — the outside provider's
volume for a day we already hold — was fetched in an earlier iteration and thrown away, and fetching
it again is a live download, which the goal file currently forbids.

Pick one:

- **(a) Authorise a small, bounded, read-only comparison download** — one symbol (AVB), a handful of
  already-stored days, volume only, held outside the database and never written. That would settle the
  question outright. It needs a dated amendment to the goal file, because the download permission was
  used up when the earlier recovery finished.
- **(b) Accept the residual in writing, with a caveat on record.** The reassuring facts, all of which I
  verified: the worst case moves AVB's 63-day average dollar volume from about $215M to about $193M
  against a $50M floor, so the company stays admitted, its risk grade stays E, its setup stays "Avoid"
  and it stays a non-candidate; four names on 11 August and thirty-five on 12 August move by a single
  position in a liquidity ranking; and only 2 of the 11 days being rebuilt are affected at all.
- **(c) Order the small honesty fix first, then re-ask.** Feed volume into the check, make the missing
  fourth label reachable, record the per-window volume figures the specification asked for, give the
  headline answer file a real producer, and port the missing failure tests onto the gate that will guard
  the rebuild. This costs nothing on the critical path and it makes the artifact stand on its own — but
  it cannot change the answer, because the deciding measurement still will not exist. Expect it to
  return "not ready" honestly rather than "ready".
- **(d) Reword the gate** so that a volume question of this bounded size does not block the rebuild.

**Whatever is chosen, the rebuild itself still needs a separate, fresh instruction from the owner** —
that is the owner's own rule, and this iteration ends `J-11 STAGE D AUTHORIZED: NO`.

**Two mechanical items ride along, whichever option is picked.** First, confirm that this iteration's
eleven evidence files and its new code actually reach version control — right now none of them is
tracked, and two of this iteration's own scripts write into that same folder by default, so a repeat of
the accident this iteration already had would be unrecoverable. Second, when the rebuild is eventually
run, remember that 12 August is AVB's third-busiest day in twenty-one years of stored history; that
should be written down as a caveat on that day's rebuilt output, whichever way the volume question is
settled.

**Still open, unchanged and not blocking:** the five older owner questions (whether 3.44 GB is
acceptable for J-09 "The backend fits the host"; J-06's "underlying run unavailable" wording; the
rewording of J-01's first two test steps; whether an empty "next-session focus" is acceptable; whether
MNST joins the recovery list). **Standing framework note:** the defect that once let a forbidden test
lane run is still unfixed in `scripts/automation/`; six iterations running have avoided it with the
maintenance-isolation contract rather than curing it. The duplicate-journey-heading defect in
`goal_gate.py` also remains unfixed and must be closed before any GOAL_ACHIEVED certification.

## Halt Justification

Nothing is broken and nothing was lost. I am halting because every road forward belongs to the owner.
The rebuild of the eleven damaged days is the next step in the plan, and the owner's own written rule
reserves it for a separate, explicit instruction; the goal file also closes every other lane until the
repair's final stage passes, so there is no substitute work that moves this forward. On top of that,
the single question this iteration was asked to answer — is the rebuild ready to start — comes back
"no" once the volume evidence is read honestly, and the only ways to turn that into a "yes" are an
owner decision: allow a small download, accept the residual in writing, or change the rule. The one
piece of work that does not need the owner (making the check honest) cannot change the answer, so
running it silently would be motion without progress.

Why not REGRESSION: no journey that worked stopped working, no stored value moved, the database was
never written to, and the one anti-goal breach inside this iteration — a test overwriting committed
evidence — was caught by the review lane, fully reversed byte-for-byte, and independently confirmed
clean by me. Why not CONTINUE: continuing would let the engine plan iteration 15, and the natural
content of iteration 15 is the rebuild the owner has not authorised. Why not ESCALATE: this run
already used the careful full depth, and the careful depth is what surfaced the problem.
