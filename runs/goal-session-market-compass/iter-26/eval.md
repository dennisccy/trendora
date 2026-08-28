# Iteration 26 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The iteration did what it promised, and I checked the important parts myself instead of trusting the
write-ups. J-05 "Each close freezes one next-session manifest, exported byte-consistently" is now
**passing**: I re-derived, read-only, that the saved file on disk is byte-for-byte the same as what the
page serves (355,711 bytes, matching security code), that every number on the manifest strip matches the
stored record, and that the group counts add up exactly. The one permanent write to the real database was
the single new manifest version the plan authorised, and nothing else in the database moved — I counted
every table that matters. J-06 "A frozen manifest never changes" made large progress but stays
**partial** for one honest reason: the app can never tell a user that the underlying run behind a frozen
briefing has gone missing, because opening the page quietly rebuilds that run first. I am escalating so
the next round runs with the deeper checks, because fixing that touches the code path every page uses.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest and near-complete | passing | passing (replay PASS) | reports/qa/goal-market-compass-iter-26-evidence/J-01-verify.png |
| J-02 What changed since the previous session | partial | partial (not tested this iteration) | — carried from iter-6 |
| J-03 Plain-English summary with cited facts | partial | partial (not tested this iteration) | — carried from iter-6 |
| J-04 Each candidate explains why and why-not | passing | passing (replay PASS; capture defect persists) | reports/qa/goal-market-compass-iter-26-evidence/J-04-verify.png |
| J-05 Each close freezes one manifest, exported byte-consistently | partial | **passing** | reports/qa/goal-market-compass-iter-26-evidence/UT-J-05-result.png + my own read-only re-derivation (below) |
| J-06 A frozen manifest never changes | partial | partial (step 4 proven live; step 2 unmet) | reports/qa/goal-market-compass-iter-26-evidence/UT-J-06-result.png |
| J-07 The Today page answers the ten-second read | failing | failing (not tested this iteration) | — carried from iter-0 |
| J-08 Market page moves over intact | failing | failing (not tested this iteration) | — carried from iter-1 |
| J-09 The backend fits the host | partial | partial (not tested this iteration) | — carried from iter-25 |
| J-10 Bounded recovery of the two deleted days | passing | passing (replay PASS) | reports/qa/goal-market-compass-iter-26-evidence/J-10-verify.png |
| J-11 Incident-bounded clean regeneration | passing | passing (replay PASS, thin golden) | reports/qa/goal-market-compass-iter-26-evidence/J-11-verify.png |

No `browser-infra.json`, no `DEFERRED-BUDGET` rows, no `journeys-changed.md`, and this was **not**
maintenance isolation — the real application booted and served both lanes. Merged browser results:
PASS, 6/6.

### What I verified myself (read-only, not taken from any handoff)

| Claim | My own check | Result |
|---|---|---|
| Export file equals served payload (J-05 step 3) | `compass._canonical_dumps(manifest_row_payload(v6))` vs `data/exports/next_session_manifests/2026-08-12_v6.json` | byte-equal, 355,711 both sides; `verify_manifest_hash` True on both; embedded hash `9bc08cfba04fc2dcab7eeb35…` reproduces |
| Strip numbers match the record (J-05 step 4, AG-3) | payload for `2025-04-15 v2` and `2026-08-12 v6` | members 531 / candidates 10 / cohort 521 / shadow 28, and 539 / 0 / 539 / 26 — every figure on both screenshots matches |
| Disposition tallies partition the cohort exactly | tally of `selection_disposition` | 513 `below_selection_floor` + 8 `excluded_by_cap` = 521 = 531 − 10 |
| Run stamping split (J-05 step 5) | `scanner_runs GROUP BY engine_identity IS NULL` | 45 stamped (newest) vs 3,083 pre-stamping NULL — the state the step asks for exists |
| Frozen version 1 not touched (J-06 step 4, AG-12) | row id 17 (`2025-04-15 v1`) | `manifest_hash` still verifies over its own payload; `created_at` still `2026-08-20 11:41:00.381102`; `content_hash` equal to v2's while `manifest_hash` differs |
| Only one row added anywhere | full row listing of `next_session_manifests` | 25 rows, ids 1–25 complete (nothing deleted); exactly one row created 2026-08-28 (id 25) |
| Nothing else moved | `daily_prices` 3,310,374 · `scanner_runs` 3,128, max id 3158, newest created 2026-08-26 | all unchanged — no run or price row created, including by the later browser and replay lanes |
| The new and changed tests really pass | ran the five new/changed tests myself | 5 passed in 0.98s |
| "Unavailable" is unreachable live (finding B2) | read `app/api/compass.py:59` and `basis_disclosure` | confirmed: `resolved_run()` runs first and recreates a missing run, so the check never sees it absent |

### Why J-05 was promoted, and the one thing that is fixture-only

Every step of J-05 now has evidence, and three of them I confirmed live on the real database (steps 3, 4
and 5 above). One limb is proven only by an isolated test: step 2's flagship state — a freshly closed day
whose manifest reads "at ingest, version 1, usable as forward-looking evidence". That state **can no
longer be produced on this database at all**: the newest day's version 1 is an old pre-freeze record, its
later versions were rebuilt during the incident and are correctly marked not usable, and no new trading
day can arrive because live data fetching is forbidden. The test that proves it does so at the real
request level (`test_api_compass.py::test_compass_route_serves_every_new_field_directly`), and nothing in
the live evidence contradicts it. Holding J-05 open forever for a state the data can never show again
would be an endless loop, so I promoted it and wrote the interpretation into the assumption ledger for the
owner to overrule if he disagrees. The walkthrough recording J-05 also asks for was not made; that is a
recording task, so J-05 carries `evidence_makeup: true` rather than being held back for it.

### Why J-06 was not promoted

J-06 step 2 says the page must keep serving a frozen briefing and say plainly that the run behind it is
**no longer stored** — "never a 404, never a recompute". The product cannot do this. Opening the page
calls `resolved_run()` first (`apps/backend/app/api/compass.py:59`), which silently recreates the missing
run, so by the time the honesty check looks, the run is back and the page says "rebuilt" instead. That is
also a recompute, which the same step forbids. This was first found at iteration 3, was re-checked
empirically this round, and is still open. Everything else in J-06 is now proven, much of it live. So the
journey stays `partial` with one small, named, fixable gap.

## Anti-goal Check

Deterministic scan (`iter-26/scan-report.md`): **CLEAN**. Product diff this iteration is two test files
only — `apps/backend/tests/test_api_compass.py` and `apps/backend/tests/test_manifest_invariants.py`
(+258/−8). No production code, no frontend, no config, no dependency manifest.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 unproven values must read "not yet proven" | OK | No score surface changed. Both screenshots show honest badges ("not prospective-eligible", "retrospective view, reconstructed under the CURRENT selection rule"). |
| AG-2 decision-quality only | OK | Candidate cards read "worth monitoring" plus cautions ("every candidate here is context, not a signal to act"); no diff touches narrative strings. |
| AG-3 displayed numbers are correct | OK — actively verified | Every figure on both screenshots re-derived by me from the stored record (table above). |
| AG-4 no overfit edges | OK | No claim, ledger entry or study introduced. |
| AG-5 determinism / no lookahead | OK | No engine change. Live corroboration: regenerating 2025-04-15 eight days later reproduced an identical `content_hash` (`125a11d500e16b67…`). |
| AG-6 evidence claims need a referee | OK | No Evidence Claim introduced (goal file states the gate passes automatically this cycle). |
| AG-7 no hard-coded credentials | OK | scan-report CLEAN; both changed files are tests with no literals of that kind. |
| AG-8 resilience to data-shape change | OK | No data-shape or scale change; no new query path. |
| AG-9 offline-deterministic ingest | OK | No ingest job and no external network call. Confirmed by data: `daily_prices` and `scanner_runs` counts and the newest run timestamp are all unchanged. The exhausted 2026-08-11/12 exception was not touched. |
| AG-10 host resource ceiling | OK | Services started through the project launch scripts; no cap touched (diff is two test files). |
| AG-11 no new composite number | OK | No new field; no production code changed. |
| AG-12 manifest immutability | OK — actively verified | Version 1 intact and self-consistent; nothing deleted (ids 1–25 complete); the export writer still refuses to overwrite; the new version-2 row is the sanctioned "corrections happen only as new version rows" mechanism. |
| AG-13 system vs market vocabulary | OK | Unchanged surfaces; screenshots keep "Ready/GO" in the chrome and "Risk-on/Expansion" in the market tiles. |
| AG-14 no Tapeology coupling | OK | No such import, call or path in the diff. |
| AG-15 no outcome-tuned selection | OK | No threshold or rule change. |
| AG-16 cohorts are not controls | OK | Cohort labelling unchanged; the non-causal caveat test still passes. |
| AG-17 repair never rewrites provenance | OK — actively verified | All 25 stored manifests read `prospective_eligible = 0`, including the new version 2; version 1's flag unchanged. |
| AG-18 authorized migration preserves everything | OK | No migration ran. AG-18's prohibition is scoped to the J-11 schema migration ("by it or around it"); the confirm-gated regenerate is a separate, shipped product feature that J-06 step 4 itself requires exercising. |

**Ledger: 8 entries, 0 unresolved. No new entry this iteration.**

One governance note, stated plainly because it is permanent: this iteration deliberately added one row to
the real database — a second version of the 15 April 2025 briefing — and that row can never be removed by
design. I judge it authorized: the owner's ruling item 5 allows ordinary non-destructive product work
without further permission, nothing was destroyed, and J-06's own written step 4 requires this exact
action. It is recorded in the assumption ledger so the owner can disagree.

## Next-Step Recommendation

**Close J-06 "A frozen manifest never changes", and run it with the deeper checks on.** The work is one
small, well-understood change: when someone opens a page for an old date, the app must first notice
whether the run behind the frozen briefing still exists, and say so honestly, instead of quietly rebuilding
it and then reporting "rebuilt". Today the honest "no longer stored" message is written and tested but can
never appear to a user. The same quiet rebuild is what can silently create permanent records just by
someone viewing an old date, so this is worth doing carefully rather than quickly.

Run the next iteration at **full depth**. This one was planned as full and was automatically downgraded to
light for the sixth time this session, so no independent auditor and no separate quality check ever saw a
round that wrote permanently to the real database. The change now proposed sits in the code path that
every page uses. Only the owner can add the `Depth enforcement: required` line that outranks the cost rule
(standing guidance keeps `CHAIN_REQUIRE_FULL_DEPTH` and `CHAIN_MAINTENANCE_ISOLATION` off); this ESCALATE
verdict is the strongest in-loop lever available to me.

After J-06, the goal file's own order gives J-07 "The Today page answers the ten-second read" and J-08
"Market page moves over intact" — the last two pieces.

Smaller items, none blocking:
1. The reviewer's MINOR is real: the code check that proves nothing can overwrite a frozen briefing only
   recognises the plain name `update`, so an import written under a different name would slip past
   (`apps/backend/tests/test_manifest_invariants.py:155`). It also only scans one folder
   (`app/engine/`). I checked the rest of the backend by hand today and found nothing — but the automated
   check should cover it.
2. J-04's screenshot still stops above the candidate card, for the eighth round running. It rides the next
   browser round as a passenger, never as its own iteration.
3. J-05 and J-06 both still owe a recorded walkthrough. Also a passenger task.
4. Four leftover export files from old test runs remain on disk. The developer investigated and correctly
   left them alone; a follow-up could stop tests writing there at all.
5. Current cache-table baseline for the next round, so a future check can compare: `market_phase_cache` 6,
   `event_study_cache` 7, `availability_cache` 1, `index_series_cache` 1, `membership_timeline_cache` 1.

Owner questions still open and still non-blocking: whether roughly 2.99 GB is acceptable for J-09; the
wording of J-06's "underlying run unavailable" step; the rewording of J-01's first two test steps; whether
an empty "next-session focus" is acceptable; and whether MNST joins the recovery list. One standing
framework note: `goal_gate.py`'s duplicate-journey-heading defect is still unfixed and must be closed
before any final "goal achieved" certification.
