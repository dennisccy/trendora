# Iteration 3 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

This iteration built the sealed daily briefing, and the part that is finished is genuinely good. I
opened the pictures myself: the home page now carries a "Manifest" card that shows the record is
frozen, which version it is, when it was sealed, four fingerprint codes, the data and universe stamps,
539 members, and an audit table listing all 539 names that were not picked, each with the reason
"below selection floor" and the plain warning that this list is not a control group. But the two
journeys this iteration existed to finish are **not finished**. The test lane never ran the half that
matters most — the part where a real market close seals the record — so the headline claim of J-05
"Each close freezes one next-session manifest" has never been watched happening. The automatic gate
agreed and stopped the iteration (`CLOSURE-FAIL`). The independent auditor found and repaired a real
bug on the way: the file writer could silently overwrite a sealed record, which is exactly what the
rules forbid. It also found one promise the product cannot keep today: J-06 "A frozen manifest never
changes" says that after you delete a day's data the page must say "the underlying run is
unavailable", and it can never say that, because simply opening the page quietly rebuilds the deleted
day. The four older journeys were all re-checked and still work.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Sector labels honest and near-complete | passing | passing | `reports/qa/goal-market-compass-iter-3-evidence/UT-J-01-result.png` (opened: /stocks @2026-08-12, GRMN = "Consumer Discretionary", 1/539, chips read "Not yet proven"); merged row UT-J-01 PASS — replay FAIL overturned as a stale golden, reconciliation footer in `reports/phase-goal-market-compass-iter-3-regression-replay-results.md` |
| J-02 What changed since previous session | passing | passing | `reports/qa/goal-market-compass-iter-3-evidence/J-02-verify.png` (opened: honest-empty "earliest stored session" state); merged row UT-J-02 PASS |
| J-03 Plain-English summary with cited facts | passing | passing | `reports/qa/goal-market-compass-iter-3-evidence/J-03-verify.png`; merged row UT-J-03 PASS; float-artifact fix confirmed in `UT-09-result.png` |
| J-04 Candidate why and why-not | passing | passing | `reports/qa/goal-market-compass-iter-3-evidence/J-04-verify.png`; merged row UT-J-04 PASS; `UT-10-result.png` (opened: MCD/T cards, reworded ATR caution, Risk-off caution) |
| **J-05 Close freezes one manifest, exported byte-consistently** | failing | **partial** | `reports/qa/goal-market-compass-iter-3-evidence/UT-02-manifest-historical-badges.png` + `UT-03-audit-table-expanded.png` (both opened — see gaps below). Merged file: "Missing Target Journeys: UT-J-05 — no test case executed for J-05 by any lane"; headline BLOCKED |
| **J-06 A frozen manifest never changes** | failing | **partial** | Merged rows UT-04/UT-05/UT-08 (regenerate → v2, confirm gate, honest 4xx); control visible in `UT-02-manifest-historical-badges.png`. Merged file: "UT-J-06 — no test case executed for J-06 by any lane". Step 2 demonstrably unmet — audit finding B2 |
| J-07 Today page ten-second read | failing | failing (not tested — out of scope) | carried; `reports/qa/goal-market-compass-iter-0-evidence/UT-J-07-fail.png` |
| J-08 Market page relocation | failing | failing (not tested — out of scope) | carried; `reports/qa/goal-market-compass-iter-1-evidence/UT-J-08-fail.png` |
| J-09 Backend fits the host (owner, new) | — (not in history) | **unknown** | none — added to `docs/goal.md` at commit `f6c31afc` (2026-08-20 10:26), after this iteration's spec (07:38) and snapshot (08:22); never measured |

### What is verified for J-05 / J-06, and what is not

**Verified in images I opened.** Manifest card @2026-08-11: badges `retrospective / version 1 /
frozen / not prospective-eligible`, "Frozen 8/20/2026, 12:14:33 PM", four hash chips (engine
`258bc5043c…`, candidate rule `5736cc25dd…`, cohort rule `7d50bdf029…`, manifest config `f26a4a5918…`),
dataset stamp `r3112-f6761224`, universe pool `4f7aeca5be…`, Members 539, Profile core, "Basis:
available", regenerate control present. Audit table: verbatim non-causal caveat + near-floor
clarification, 539 comparison rows = 539 members − 0 candidates (AG-3 cross-check holds inside the same
image, against the "No stored member cleared the selection rule" empty state on that page).

**Not verified.** (a) J-05 step 1 — the ingest-finalize "next-session manifest" disclosure: UT-12
SKIPPED for host safety. (b) J-05 step 2's flagship state — a real close producing `mode: at_ingest`,
`version: 1`, `producer: ingest_finalize`, `prospective_eligible: true` — was never observed live; the
dev handoff records the live frontier still serving a pre-freeze-era iter-2 row (`mode: null`), and
every `at_ingest` manifest seen came from regenerate (always `prospective_eligible: false`). (c) J-05
step 3's export byte-equality has no automated test (audit B3), only a manual check. (d) J-06 steps 1
and 3 (backfill-after-freeze, remove/restore basis flip) were run by no lane. (e) J-06 step 2 is
demonstrably unmet (audit B2, reproduced). (f) The shadow cohort is DOM-verified (32 rows) but absent
from the image, which truncates mid-cohort at ~29,500 px.

**Capture defects found by checksum (not product faults).** `UT-04-result.png` and `UT-05-result.png`
are the same 6 KB file (md5 `ad732856…`) and are visually blank; `UT-01/06/11/13/14-result.png` are one
identical 20 KB frame (md5 `e83381c1…`) showing only the as-of bar. Those five rows' claims rest on DOM
prose, not on their cited images. The load-bearing evidence above comes from the QA agent's full-page
captures instead.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 no unbacked "proven" | OK | `UT-J-01-result.png` (opened): every score chip reads "Not yet proven". `caveats.evidence` reads the same ledger producer as the existing chips (`coherence.md`, `compass.py:528-542`) — no second proven-ness computation |
| AG-2 decision-quality only | OK — iter-2 MINOR now closed | `UT-10-result.png` (opened): "ATR_RISK_BUDGET: ATR is 2.99% of price (p6 of universe)." — the "— sized risk accordingly" tail is gone; guard extended to candidate reason/caution/why-not strings (TC-35) |
| AG-3 displayed numbers correct | OK | In-image cross-check: card says Members 539 and "comparison cohort (539) + near-threshold shadow (32)"; the expanded table holds 539 rows, equal to members minus 0 candidates, matching the empty-focus state on the same page |
| AG-4 no overfit edges | OK | No pattern surfaced as proven; no Evidence Claim introduced; selection thresholds untouched |
| AG-5 determinism / no-lookahead | OK | My grep of `engine_identity.py`, `compass.py`, `api/compass.py` finds no `requests`/`httpx`/`urllib`/`http(s)://`; TC-29 AST scan and TC-14 time-safety test pass |
| AG-6 referee gate | OK | No Evidence Claim this cycle — gate passes automatically, per goal.md |
| AG-7 no credentials | OK | `iter-3/scan-report.md`: CLEAN, 136 untracked files scanned; my own grep for api_key/secret/token/password over the new + changed files returns nothing |
| AG-8 data-shape / scale resilience | OK | Cohort rows use bounded, column-projected per-run reads reusing `_record_json_by_ticker` (`coherence.md` → `compass.py:194-242`, `:155-170`); TC-30 passes. 539 rows are bounded by one run's member set, never a cross-run sweep |
| AG-9 offline-deterministic ingest | OK | No network imports added; no `requirements*/pyproject/package.json` change; the single new `install-decisions.jsonl` line records a grep, packages `[]` |
| AG-10 host resource ceiling | OK (untouched) | `git diff` over `project-extensions/`, `scripts/start-backend.sh`, `scripts/start-frontend.sh` is empty; the `config.yaml` diff adds only `compass.manifest` + `provenance` — no `memory_cap_mb`, `malloc_arena_max`, pool or `cache_size` change. J-09 now carries the owner's binding reduction and is correctly untouched here |
| AG-11 no new composite number | OK | Audit-table columns I opened are Ticker/Leadership/Entry/Risk/Setup/Sector/Disposition only — no blended field; TC-28 passes |
| AG-12 manifest immutability | **VIOLATED — reproduced and FIXED in-iteration (critical, resolved)** | Audit B1: `_write_export` (`compass.py:841`) overwrote an existing frozen artifact's bytes (probe: `2024-06-03_v1.json` `d2547fb2eb17` → `72b8e03a339f`, same path). Fixed: exclusive `open(path,"x")` (`compass.py:860`), per-run temp export dir fixture (`tests/conftest.py:31-45`), regression test (`test_manifest_invariants.py:138`); 37 + 46 tests pass, product export dir byte-unchanged. No real artifact was overwritten |
| AG-13 system-vs-market separation | OK | My grep finds no readiness token in `compass-manifest-strip.tsx`; its docstring (`:97-99`) records `preflight_verdict` is deliberately never rendered; TC-31 |
| AG-14 no Tapeology coupling | OK | Grep for "tapeology" over the changed backend/frontend files returns nothing; the export writes only a local JSON file |
| AG-15 no outcome-tuned selection | OK | `compass.selection` thresholds unchanged in the `config.yaml` diff; the empty-focus question is carried to the owner rather than tuned away |
| AG-16 cohorts are not controls | OK | `UT-03-audit-table-expanded.png` (opened) shows the verbatim "frozen non-selected comparison pool, not a matched or causal control group" and the shadow's near-floor clarification |

**Coherence:** `runs/goal-session-market-compass/iter-3/coherence.md` = **COHERENCE-PASS** (one writer
behind all three producer paths, one read endpoint, no client-side derivation). Two advisory notes
only: `engine_identity` is not yet exposed on `GET /api/runs`, and `caveats.sector_basis` re-reads the
config field instead of calling `methodology._sector_basis`. Neither vetoes anything.

**Goal-edit drift:** no `journeys-changed.md`. The `docs/goal.md` amendment at `f6c31afc` is 61
insertions and 0 deletions; I re-ran `goal_gate.py hash-journeys` and all eight stored `spec_hash`
values still match, so no recorded pass is void.

## Next-Step Recommendation

Do **J-09 "The backend fits the host"** next, on its own, in the light "lean" mode. The owner wrote it
into the goal this morning after the machine froze, and the goal file says plainly it jumps the queue
before any more work on J-05 and J-06. It is small: change one number in `config.yaml` so each database
connection keeps 64 MB of pages instead of 256 MB, then start the backend, read its peak memory, and
prove it is under 2.5 GB (it was 4.8 GB), append the new dated figure beside the old one, re-run the
burst-of-requests check, and show a stored day's numbers are unchanged. Do not touch the connection
pool sizes. This must come first for a practical reason: finishing J-05 and J-06 means running real
data rebuilds, and those are exactly the heavy jobs that helped freeze the machine.

After that, the next iteration should be a make-up run for J-05 "Each close freezes one next-session
manifest" and J-06 "A frozen manifest never changes": remove and re-add the last two trading days, and
this time actually watch the close seal the record — the sealed stamp reading "at ingest", version 1,
and "prospective-eligible" — then delete a day, restore it, and watch the "where this came from" line
change. Also re-take the pictures: five of this run's screenshots are the same blank frame, so five
claims have no image behind them, and the short recorded walkthroughs for the first four journeys are
still missing for a second run in a row.

Two things need the owner, not the robot. **First**, a decision: J-06 asks that after you delete a
day's data the page says "the underlying run is unavailable", but simply opening the page rebuilds the
deleted day, so that sentence can never appear. Either the compass page should look up the sealed
record before it resolves the date (a change to how every dated page behaves), or that wording in the
goal should change. **Second**, still unanswered from last time: please approve rewording J-01's first
two test steps, and say whether an empty "next-session focus" on the newest date is an acceptable
honest result — the rules forbid changing the cut-offs just to make names appear.
