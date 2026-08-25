# Iteration 15 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

**Owner-facing lines:** `J-11 STAGE D READY: NO` · `J-11 STAGE D AUTHORIZED: NO`

## Summary

The one question that blocked this repair is now answered with real measured data, and the answer is
"the two restored days are on the wrong scale". One company, AVB, had two trading days restored in an
earlier run. This run was allowed to make one small, read-only download to check them. It shows that
on the four surrounding days Trendora's own stored figures keep the money value of trading steady:
the price is multiplied by 2.793 and the share count is divided by the same 2.793. On the two
restored days the price was multiplied but the share count was left alone. So any figure that
multiplies price by share count reads exactly 2.793 times too high on those two days — 12 August
stores $1,860,985,686 where the outside source says $666,303,475. I checked every one of those
numbers myself against the database, read-only, instead of taking them from any report.

This run also did the honest housekeeping it was asked to do, and it did not write one byte to the
real 8.4 GB database — I confirmed that from the file itself, not from a report. The check that gave
the wrong answer last time is genuinely fixed and now compares two independent sources. Nothing that
worked before stopped working. The run stops here because every way forward is the owner's to
choose.

## Journey Results This Iteration

Browser checks and the automatic replay were **forbidden by contract** this iteration (maintenance
isolation). `reports/phase-goal-market-compass-iter-15-ui-test-results.md` is all-SKIPPED with that
declared reason, and `runs/goal-session-market-compass/iter-15/maintenance-isolation-refusals` records
the engine's own refusal at 2026-08-25T10:14:17Z. So **no journey was tested and every journey keeps
its prior recorded status.** No journey may be promoted on this iteration's evidence, and none is.

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest on new runs | passing | passing (carried, not re-verified) | prior: `reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png` — spot-checked: GRMN shows sector "Consumer Discretionary", not Unassigned; consistent with recorded status |
| J-02 What changed since previous session | partial | partial (carried, not re-verified) | prior: `reports/qa/goal-market-compass-iter-4-evidence/J-02-verify.png` |
| J-03 Plain-English summary with cited facts | partial | partial (carried, not re-verified) | prior: `reports/qa/goal-market-compass-iter-4-evidence/J-03-verify.png` |
| J-04 Candidate explains why and why-not | passing | passing (carried, not re-verified) | prior: `reports/qa/goal-market-compass-iter-4-evidence/J-04-verify.png` — spot-checked: summary card and "10 names worth monitoring next session" render with the retrospective stamp; consistent with recorded status |
| J-05 Each close freezes one manifest | partial | partial (carried, not re-verified) | prior: `reports/qa/goal-market-compass-iter-3-evidence/UT-02-manifest-historical-badges.png` |
| J-06 A frozen manifest never changes | partial | partial (carried, not re-verified) | prior: `reports/qa/goal-market-compass-iter-3-evidence/UT-02-manifest-historical-badges.png` |
| J-07 Today page ten-second read | failing | failing (carried, not re-verified) | prior: `reports/qa/goal-market-compass-iter-0-evidence/UT-J-07-fail.png` |
| J-08 Market page moves over intact | failing | failing (carried, not re-verified) | prior: `reports/qa/goal-market-compass-iter-1-evidence/UT-J-08-fail.png` |
| J-09 Backend fits the host | partial | partial (carried, not re-verified) | prior: `reports/perf-budgets.md:12114-12236` |
| J-10 Bounded recovery of two deleted days | passing | **passing, unchanged — with a new measured caveat recorded** | `runs/goal-market-compass-iter-15/j11-avb-provider-fetch-evidence.json` + my own read-only re-derivation against `apps/backend/data/trendora.db`; see "The AVB finding" below and the J-10 gap in `journey-history.json` |
| J-11 Incident-bounded clean regeneration | partial | **partial — advanced within `partial`; Stage D readiness now settled as NO on real evidence** | `runs/goal-market-compass-iter-15/j11-stage-d-readiness.json` (`ready:false`, `avb_classification:"AVB-C"`, `authorized:false`) + `j11-avb-bridge-diagnostic.json` + `j11-stage-d-preflight-gate.json` + `j11-whole-iteration-zero-write-proof.json`, every load-bearing figure re-derived by me |

**Spot-checks (2, per methodology A.4):** J-01 and J-04's prior screenshots both opened and both
consistent with their recorded status. No widening required. The frontend and API are untouched this
iteration (12 product files, all under `apps/backend/app/engine/j11_*`, `apps/backend/scripts/run_j11_*`
and `apps/backend/tests/test_j11_*` — my own `git diff --stat`), so evidence durability keeps the
prior captures valid.

### The AVB finding — re-derived by me, not inherited

Read-only against `apps/backend/data/trendora.db` (`mode=ro` + `PRAGMA query_only=ON`), combined with
this iteration's fetch artifact. `bridge_factor = 2.7930001225759193`; `1/bridge_factor = 0.358037936`.

| date | stored close | provider close | close ratio | stored volume | provider volume | volume ratio | dollar ratio | label |
|---|---|---|---|---|---|---|---|---|
| 2026-08-05 | 189.610001 | 67.887573 | 2.793000 | 591,600 | 1,652,268 | 0.358053 | 1.000043 | bridged+compensating |
| 2026-08-06 | 186.550003 | 66.791977 | 2.793000 | 642,300 | 1,794,050 | 0.358017 | 0.999941 | bridged+compensating |
| 2026-08-07 | 187.550003 | 67.150017 | 2.793000 | 666,100 | 1,860,448 | 0.358032 | 0.999984 | bridged+compensating |
| 2026-08-10 | 183.839996 | 65.821693 | 2.793000 | 451,300 | 1,260,545 | 0.358020 | 0.999949 | bridged+compensating |
| 2026-08-11 | 181.760015 | 65.076981 | 2.793000 | 1,549,436 | 1,549,436 | **1.000000** | **2.793000** | bridged+raw |
| 2026-08-12 | 179.790007 | 64.371643 | 2.793000 | 10,350,885 | 10,350,885 | **1.000000** | **2.793000** | bridged+raw |

My figures match the artifact and the coordinator's statement exactly. **AVB-C is mechanically
reached, not label-patched.** I traced the path: `classify_date_from_provider_comparison`
(`j11_avb_diagnostic.py:384-415`) decides from four symmetric `_within_relative_tolerance` tests
against `1.0`, `bridge_factor` and `1/bridge_factor` at one shared 1% band;
`classify_local_convention_with_volume_evidence` (`:418-542`) requires every date in a window to agree;
two determinate windows disagree ⇒ `internally_consistent: False` ⇒ `classify_avb` (`:910-914`) ⇒
AVB-C. No AVB-specific constant, no hardcoded label, no date special-casing, no prior answer encoded.
It is tolerance-robust: the calibration ratios sit within 6e-5 relative of `1/bridge`, the recovered
ones are exactly 1.0. It fails closed: a `None`/zero target is never "within tolerance", a missing
provider record forces `evidence_available: False` with `B.close`/`B.volume` `None` and
`volume_a_equals_b` `None` — never a stored-volume copy, never a silent fall-back to the old
price-only method.

**Iteration 14's tautology is genuinely fixed.** `volume_a_equals_b` is now `False` on all four
calibration dates (591,600 vs 1,652,268 and so on) and `True` only on the two recovered dates, where
two independently-sourced values genuinely coincide. It is a real cross-source comparison now, and it
demonstrably can be false.

**One deviation, in the safe direction:** `classify_avb` reaches AVB-C from inconsistency *alone*,
before consulting material impact — stricter than the spec's literal "for a window that materially
affects Stage D output". Moot here: material impact exists anyway (4 other pool tickers' liquidity
percentile shifted on 08-11, 35 on 08-12).

**Honest nuance I re-derived rather than inherited.** Calling 12 August's volume purely a "scale
artifact" overstates it. Deflating 10,350,885 by the bridge factor gives 3,706,006, still AVB's
~96.9th-percentile share day across 5,397 stored bars (raw it reads 99.96th). So 12 August *was* a
genuinely heavy day; only its **dollar** volume is unambiguously 2.793× overstated. 11 August is the
one that is almost entirely a scale artifact (83rd percentile raw, 17th deflated).

**The `0257c56d…0b11cd` fingerprint is reproducible.** The developer honestly recorded it as unknown
and the auditor (B4) concluded after nine attempts that it "matches nothing on disk". Both are wrong on
the reproducibility point, and no data discrepancy exists: `sha256` over the concatenated `repr()` of
`(symbol,date,open,high,low,close,volume)` for all 5,397 AVB rows ordered by date yields
`0257c56dbd671c8191250130f8619ea045c3f26fece6ab8338dae048b60b11cd` exactly. I recomputed it. The spec
quoted a fingerprint without its recipe; that is an evidence-hygiene fault upstream of the developer.

### Auditor B1 — confirmed independently, and it outranks the auditor's own priority for it

`apps/backend/main.py:100` calls `warmup.ensure_latest_snapshot` on **every** boot;
`apps/backend/app/engine/warmup.py:89-92` resolves `latest_data_date(session)` and calls
`run_scan(session, latest, cfg)`. I ran `SELECT MAX(date) FROM daily_prices` read-only: **2026-08-12**
— an incident date currently holding **zero** `ScannerRun` rows. `scanner.py:235-239` shows `run_scan`
falls through to `compute_run_payload` + `persist_run_payload` when no run exists, i.e. an INSERT,
**before any request arrives**. `GET /api/compass` on an incident as-of then create-once-mints
AG-12-immutable manifests for the **7** incident dates that have none — I enumerated them read-only:
2026-05-12, 05-13, 07-10, 07-13, 07-24, 07-27, 08-03. Both effects are irreversible: Stage C's clear
is on the binding "do not redo" list, and AG-12 forbids deleting a manifest row. **A request-level
guard cannot help — the guard must be pre-boot,** and it must exist before Stage G reopens the browser
and replay lanes. Today the only protection is an operator convention, not code. This is also the
retroactive justification for six iterations of maintenance isolation.

### Safety envelope — re-derived read-only by me

DB mtime `1787591622`, size `8,365,871,104`, `-wal` 0 bytes at true start, true end, **and after my own
queries**. All 11 incident dates at zero `ScannerRun`s. `daily_prices` 3,310,374 · `scanner_runs` 3,117
(34 stamped `6261ca17…`, 3,083 NULL, 0 other) · `forward_returns` 6,797,728 with 16,614 measured into
incident dates · `data_provider_runs` 549 (the fetch left no database trace at all) · manifests 24 with
values/DDL/indexes unchanged · `watchlist` 6. AVB's own bars byte-identical (fingerprint above). Zero
live writes. Historical evidence dirs iter-9/11/12/13/14 all 0 dirty; `git stash list` empty.

### Process deviations — confirmed clean by my own checks, not inherited

Commit `17eb97ce`: 30 files, 8,007 insertions / 71 deletions, touches **no** `docs/goal.md` and **no**
`iter-13`/`iter-14` path. `git stash list` empty. Iteration 14's `j11-stage-d-readiness.json` has
exactly one commit in its whole history (`b2c49192`, iteration 14's own), still reads AVB-B/`ready:true`,
0 dirty lines — byte-preserved and correctly marked superseded. The AG-9 amendment's file mtime is
09:17:29, genuinely before the spec (09:40:50), the plan (09:51:02) and the fetch (10:26:18), so the
authorization preceded the act. The amendment is the owner's uncommitted edit and is correctly absent
from the developer's commit. **One diff artifact worth naming so nobody misreads it:** the bounded diff
shows `docs/goal.md | 28 -`. That is because the snapshot `0f533c49` is an off-branch WIP commit of the
working tree (which held the owner's uncommitted amendment) compared against `HEAD` (which does not).
The amendment is present in the working tree — I grepped it. Nothing was deleted.

## Anti-goal Check

Worked from `runs/goal-session-market-compass/iter-15/scan-report.md` (**CLEAN** — no secret,
dependency or license findings) plus `iter-diff.md` and my own targeted greps over the 12 product
files. Every category answered explicitly.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language | OK | No served surface exists this iteration; no service booted; diagnostic artifacts are never rendered. `runs/…/coherence.md` grep-verified zero `apps/frontend`/`app/api` files in the diff. |
| AG-2 decision-quality only | OK | No trade verbs, promises or order paths added; diff is diagnostic tooling and tests only. |
| AG-3 displayed numbers correct | OK (not applicable now; a latent risk the gate is holding) | Nothing is displayed. The AVB dollar-volume overstatement would become an AG-3 problem only if Stage D regenerated against today's representation — which is exactly what AVB-C blocks. |
| AG-4 no overfit edges | OK | No pattern surfaced as proven; no referee entry. |
| AG-5 determinism / no-lookahead | OK | `_build_bars_with_transformed_close` (`j11_avb_diagnostic.py:629-654`) builds a new in-memory `Bar` list, never mutates ORM rows, never writes; the trace reuses the canonical `ur._adv_dollar`/`resolve_candidate`/`scoring` as-of-bounded paths. |
| AG-6 referee gate | OK | No Evidence Claim introduced; gate passes automatically. |
| AG-7 no hardcoded credentials | OK | scan-report CLEAN; my own grep for key/secret/token/password/Bearer over all 8 changed source files returns nothing. |
| AG-8 data-shape/scale resilience | OK | `fetch_avb_stored_series` (`:159-170`) is column-projected, date-bounded, single-symbol — no whole-table ORM load anywhere in the new code. |
| AG-9 offline-deterministic ingest | OK — this is the authorized use of dated exception #2 | Exactly **one** `.get_daily` call site (`j11_avb_provider_fetch.py:98`), exactly **one** live provider construction (`run_j11_avb_provider_fetch.py:78`), `fetch_call_count: 1`, symbol AVB only, the six permitted dates only (`discarded_dates_outside_permitted_set: []`), fields date/close/volume only, vendor `yahoo`, canonical `get_daily`. No database write: `data_provider_runs` still 549. Amendment (09:17) precedes the fetch (10:26). Exception now exhausted; the diagnostic requires `--provider-fetch-evidence-path` with no default, so nothing can re-fetch. J-10 not reopened. |
| AG-10 host resource ceiling | OK | No launch script, `host-guard.env`, `config.yaml`, or dependency manifest is in the diff (`git diff --name-only` checked). No full backend suite run; one targeted pytest process. |
| AG-11 no new composite score | OK | The ratios are diagnostic values in a JSON file; none is attached to a candidate, the market, or a manifest. |
| AG-12 manifest immutability | OK | 24 rows before and after (my own count), `manifest_dump_diff.equal: true`, `manifest_values_unchanged`/`manifest_ddl_unchanged`/`manifest_indexes_unchanged`/`source_run_id_values_unchanged` all `true`. No manifest minted, deleted, rebound or rehashed. |
| AG-13 system-vs-market separation | OK | No surface, no vocabulary change. |
| AG-14 no Tapeology coupling | OK | Grep for `tapeology` over all changed source files returns nothing. |
| AG-15 no outcome-tuned selection | OK | No threshold or selection rule changed; the 1% tolerance is a diagnostic sanity bound, documented as such and named at module level. |
| AG-16 cohorts are not controls | OK | No cohort or manifest touched. |
| AG-17 repair never rewrites provenance | OK | Iteration 14's artifact byte-preserved (one commit, 0 dirty); iter-9/11/12/13/14 evidence dirs all 0 dirty; the incident record is intact. The `docs/goal.md | 28 -` diffstat line is a snapshot-vs-commit artifact, not a deletion — verified. |
| AG-18 authorized migration preserves everything | OK | No schema migration ran; no `ALTER`/`DROP`/`CREATE TABLE` anywhere in the diff. |

**New violations this iteration: none.** Ledger unchanged: **6 total, 0 unresolved.**

Deterministic scan: CLEAN. Coherence: **COHERENCE-PASS**. Review: PASS_WITH_NOTES (one MINOR — wrong
per-file test counts in the handoff; the 157-passed aggregate is right). QA: PASS. Audit:
PASS_WITH_GAPS (B1 IMPORTANT; B2/B3 gaps; B4/B5/B6 observations; T1/T2 gaps; T3/T4 positive findings).

## Next-Step Recommendation

**One decision is needed from the owner, and one safety job should be done before anything starts the
application again.**

**First, the safety job — it is the only item that can go wrong on its own.** Right now, if anyone
starts the Trendora backend for any reason, it will immediately write a new day's results for
12 August into the real database, before anyone opens a page. Eleven days were deliberately emptied
and are waiting to be rebuilt properly; this would refill one of them by accident, and it cannot be
undone. Opening the Today page for one of those days would also create permanent saved briefings for
seven days that never had one. The only thing stopping this today is the human rule that nobody starts
the app — there is no check in the software. Ask for a proper guard, built into start-up, that refuses
to start normally while any of the eleven days is still empty. This must be in place before browser
testing is switched back on.

**Second, the decision.** One company's two restored days record the money value of trading 2.793
times too high. Pick one:
(a) **accept it in writing** and let the rebuild go ahead using today's stored figures, with a caveat
recorded against 11 and 12 August — the reassuring facts, all checked by me: only 2 of the 11 days are
affected, only one company, and the company's admission, risk grade and "avoid" status do not change;
(b) **order a correction first** — divide that company's stored share count on those two days by 2.793
so it matches Trendora's own convention. This is a write to the canonical price table, which the
current plan forbids outright, so it needs its own dated permission, its own evidence and its own
audit;
(c) **change the rule** so a bounded difference of this kind does not block the rebuild; or
(d) **change the plan** in `docs/goal.md`.

**Whatever is chosen, the rebuild still needs a separate, fresh instruction from the owner** — this
iteration ends `J-11 STAGE D AUTHORIZED: NO`, exactly as the plan requires.

**Three small jobs can ride along whenever the next run happens, none of them blocking:** make the
readiness check compare the database fingerprint and not just the clock (auditor B2); fix the message
that prints the wrong label when evidence is missing (auditor B3); and correct the per-file test counts
in the developer's notes — the total of 157 passing tests is right, the breakdown is not.

**One correction for the record:** the fingerprint the specification asked the team to match
(`0257c56d…0b11cd`) IS reproducible — I reproduced it — and AVB's stored data is identical to the
owner's capture. The specification quoted it without saying how it was calculated, which cost the
developer and the auditor real effort and produced a recorded "mismatch" that was never a data problem.
Future specifications should quote the recipe beside any fingerprint.

**Five older owner questions remain open and non-blocking, unchanged:** whether 3.44 GB is acceptable
for J-09 "The backend fits the host"; J-06 "A frozen manifest never changes"' wording for "underlying
run unavailable"; the rewording of J-01 "Sector labels are honest"' first two test steps; whether an
empty "next-session focus" is acceptable; and whether MNST joins the recovery list. **Two standing
framework notes:** the defect that once let a forbidden test lane run is still unfixed in
`scripts/automation/` — seven iterations running have avoided it with the maintenance-isolation
contract rather than curing it; and `goal_gate.py`'s duplicate-journey-heading defect is still unfixed
and must be closed before any GOAL_ACHIEVED certification.

**Next action for a non-programmer:** answer the safety question first ("yes, build the start-up
guard"), then pick one of (a), (b), (c) or (d) above and say so in `docs/goal.md`, then run
`--resume`.

## Halt Justification

The work asked for was done, done honestly, and changed nothing in the real database — I verified the
file itself, not a report about it. So why stop?

Because the blocker is now a **decision**, and every route through it belongs to the owner. The
measurement is finished and it is not in doubt: two restored days record the money value of trading
2.793 times too high. What to do about that — accept it in writing, correct the stored figures (a
write the current plan forbids outright), reword the rule, or change the plan — is a judgement about
the data the owner owns, not something any lane here may decide. On top of that, the rebuild itself
requires a separate, fresh owner instruction by the plan's own repeated pattern, and `docs/goal.md`
keeps every other product, research and browser lane shut until the final stage of this repair passes.
So there is no other lane legally open.

**Why not CONTINUE?** Continuing lets the engine plan iteration 16, and the only J-11 stage after this
one is the rebuild — the one step the owner has not authorised. Real non-owner work does exist and I
am not hiding it: the start-up guard, the two small fixes, the wrong test counts. But none of them can
change the answer the gate gives, and the start-up guard is itself a design decision about how the
application should behave — the auditor reached the same conclusion independently. Stopping is also
strictly safer for that guard: while the engine is stopped, nothing starts the backend.

**Why not REGRESSION?** Nothing that worked stopped working. No stored value moved. No journey was
tested this iteration, so none could fail. The AVB scale problem has been in the data since iteration
9 — this iteration measured it, it did not cause it — and `docs/goal.md`'s own owner ruling closed
J-10 "Bounded recovery of the two deleted trading days" and forbids reopening it. The finding is
recorded as a caveat on that closed journey's output and as the substance of the current block, which
is the honest place for it. No anti-goal was violated; the ledger stands at 6 entries, 0 unresolved.

**Why not ESCALATE?** This run already used full depth, and full depth is what produced the finding.

**Why not GOAL_ACHIEVED?** Two journeys are still failing (J-07 "The Today page answers the ten-second
read", J-08 "Market page moves over intact") and six are partial. Nothing close.
