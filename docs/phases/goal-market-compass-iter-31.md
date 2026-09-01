# Goal Iteration 31 — Re-confirm J-02 "What changed" and J-03 "Plain-English summary" against the recovered database

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 31
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — structural/cross-cutting. J-02's What-changed card and J-03's Summary card each
  depend on LIVE cross-module interaction that no single journey's own fixture suite covers jointly:
  `session_delta.compute_delta` reads stored `scanner_runs`/`ScannerResult` scores+buckets, stored
  sector-rank rows, stored theme-rank rows, and the `market_phase_cached` severity timeline (≥4
  modules), and `build_narrative`'s cited facts cross-check `GET /api/dashboard`'s regime score against
  `GET /api/market-phase`'s severity. Fixture tests exercise each module in isolation
  (`test_session_delta.py`, `test_compass.py`); this is the FIRST live, end-to-end pass across all of
  them since the iter-5 incident and its J-10/J-11 recovery — the exact class of interaction a
  same-iteration code fix (if the live pass finds a real gap) could touch. The evaluator's own next-step
  additionally names `Depth: full` explicitly, citing 21 consecutive iterations where an independent
  later lane found what earlier lanes missed.
- **Frontend Present:** yes
- **Target journeys:** J-02, J-03
- **Required-still-passing journeys:** J-01, J-04, J-05, J-06, J-07, J-08, J-10, J-11 (the full current
  passing set — both target journeys live on the SAME `/` page as J-04/J-05/J-06/J-07's manifest strip
  and share the Next-session manifest CONTENT block's single producer with all of them; J-08/`/market`
  shares the as-of switcher; J-10/J-11 are the incident-recovery pair whose completion is the precondition
  this whole iteration relies on)
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; the manifest for close D derives only from state stored at or before D; never introduce lookahead anywhere. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never crash an existing page or exhaust memory — consumers of widened fields are re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder), and unbounded whole-table ORM loads are forbidden (the delta engine reads column-projected selects, never full record_json sweeps). *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local provider fixtures — no live external network calls or paid data services without an explicit goal.md amendment. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change; corrections happen only as new version rows; a historical view never substitutes a newer manifest. *(critical)*
  - **AG-13 — System-vs-market separation:** readiness/preflight vocabulary (Ready, Initializing, Backend unavailable, GO, DEGRADED, NO-GO) must never label market state, and regime/phase vocabulary must never label system state; the manifest's market and narrative blocks must contain no readiness tokens. *(critical)*
  - **AG-17 — Repair never rewrites provenance (owner, 2026-08-20):** restoring deleted historical data MUST NOT retroactively change research provenance. A manifest that was retrospective or ineligible stays that way; `prospective_eligible` is never upgraded merely because historical data was later repaired; `available_at_utc`, manifest versions, `content_hash`/`manifest_hash`, and prior eligibility classifications remain immutable (AG-12 governs the rows and files themselves). *(critical)*

## GOAL

Re-confirm J-02 "What changed since the previous session" and J-03 "Plain-English summary with cited
facts" — both built by iter-4 but frozen at `partial` since iter-6's incident-era downgrade and never
re-examined since — against the now fully-recovered live database, and ship the two `[NEW]`-flagged
walkthroughs their own acceptance text still owes.

## BACKGROUND

J-02 and J-03 were built and briefly verified `passing` at iter-4. iter-6 downgraded both to `partial`
because the live database was mid-incident at the time: the frontier was stuck at 2026-08-10,
`GET /api/compass?as_of=2026-08-12` returned HTTP 400, and J-02's verified assertion "vs 2026-08-11
(1 day ago)" was literally unsatisfiable (`docs/phases/goal-market-compass-iter-6.md` eval, rows 25-26).
J-10 (bounded recovery) and J-11 (incident-bounded clean regeneration) have both since reached `passing`
(iter-30, Stage G), and I confirmed read-only this round that the frontier now sits cleanly at
`2026-08-12` with 8 manifest versions (1-7 plus the pre-freeze legacy row) and a real preceding stored
run at `2026-08-11` — the exact condition that forced the iter-6 downgrade no longer holds. But the
journey-history digest is explicit: "Not targeted and NOT replayed... the limbs holding it partial have
not been re-examined" since iter-6 — 25 iterations ago.

I read the current code before writing this spec. `app.engine.session_delta.compute_delta`,
`app.engine.compass.build_narrative`, `apps/frontend/components/compass-whatchanged-card.tsx`, and
`compass-summary-card.tsx` all appear feature-complete, including the suppressed-moves disclosure, the
"Show cited facts" audit view, the no-prior-run empty state, and the retrospective stamp.
`apps/backend/tests/test_session_delta.py` (12 tests) and `test_compass.py`'s narrative tests
(state-sentence-facts, no-prior-run variant, NA-velocity variant, retrospective stamp,
banned-language scan) already cover every acceptance step at the FIXTURE level, in isolated DBs. What
has never happened is a LIVE pass against the recovered data, or either journey's own required
`[NEW]`-flagged walkthrough (both still cite the stale iter-4 screenshot as their last evidence). This
iteration is therefore a genuine re-verification-and-close pass, not a rebuild: if a live spot-check
surfaces a real discrepancy the fixture suite didn't catch, fix it at its smallest surface and extend
the relevant test file; otherwise the deliverable is an honestly re-confirmed `passing` plus the two
owed walkthroughs.

The iter-30 evaluator's next-step recommendation targets exactly these two journeys ("the two oldest
unfinished journeys, both half-done since round 6, both about text a reader sees on the front page, and
both ordinary work needing no owner permission") and directs `Depth: full`, citing a 21-consecutive-
iteration pattern where an independent later lane found what earlier lanes missed.

**Lessons applied:** iter-24/iter-24b (a journey-set label in prose before its own bullet defeats the
replay-lane parser — the Required-still-passing bullet below is clean, one line, J-NN tokens only) and
iter-25 (cross-check `reports/phase-goal-market-compass-iter-31-regression-replay-results.md` exists
whenever a non-empty Required-still-passing set is named — "replay: no" is never benign). iter-27/iter-27b
(a plain GET can mint a permanent row; the authorized-inputs list is stated explicitly below, and every
row-count claim must be re-derived AFTER every lane finishes, via a read-only DB connection, never
delegated to an earlier snapshot). iter-28b (cross-lane claims about whether another lane ran must be
checked against artifact mtimes, not accepted as fact). iter-29b/iter-30's second lesson (a golden
written AFTER the replay lane ran is not coverage) — applied directly to
`journey-scripts/J-11.json`, rewritten 2026-09-01T01:51:59Z and never yet executed: it must run FIRST in
this iteration's replay lane, its real result reported verbatim, and it must not be edited again this
round regardless of outcome (also the inlined iteration-state's binding "dev-owned, ride-along" item).

## IN SCOPE

### Backend
- [ ] Re-verify `app.engine.session_delta.compute_delta` end-to-end against the live recovered database
      at the authorized `as_of` set (frontier `2026-08-12` / default, `2025-04-15`, `1996-02-01`) plus
      the non-manifest spot-check date `2026-08-11`; if a live discrepancy against the fixture-proven
      behavior (`test_session_delta.py`) is found, fix it at its smallest surface and extend that file.
- [ ] Re-verify `app.engine.compass.build_narrative` (state/direction/breadth/focus-count sentences,
      cited facts, banned-language scan, retrospective stamp, no-comparison variant) end-to-end against
      the same authorized `as_of` set; if a live discrepancy against the fixture-proven behavior
      (`test_compass.py`) is found, fix it at its smallest surface and extend that file.
- [ ] Confirm, via a read-only DB connection (`mode=ro`) opened AFTER every lane in this iteration
      finishes — iter-27b's method, a control `CREATE TABLE` on that connection must be refused — that
      `next_session_manifests` still holds exactly 28 rows across the same 18 `as_of` dates recorded in
      the iter-31 blueprint note. Zero new mints from any lane this iteration.
- [ ] Run `runs/goal-session-market-compass/journey-scripts/J-11.json` (rewritten
      2026-09-01T01:51:59Z, never yet executed) FIRST in this iteration's deterministic replay lane;
      record its real pass/fail result verbatim in the dev handoff and the merged results file; do not
      edit the golden again this round regardless of outcome.

### Frontend
- [ ] Re-verify `CompassWhatChangedCard` (`apps/frontend/components/compass-whatchanged-card.tsx`) and
      `CompassSummaryCard` (`apps/frontend/components/compass-summary-card.tsx`) render the served
      `session_delta`/`narrative` fields byte-identically against live recovered data at the same
      authorized `as_of` set, including the suppressed-moves and cited-facts disclosures; fix any
      rendering discrepancy found at its smallest surface.
- [ ] Confirm each What-changed entry's `drill_href` carries the current `?asof` to its target surface
      (`/sectors`, `/themes`, `/stocks`) and resolves to a live page.
- [ ] Record the two still-owed `[NEW]`-flagged walkthroughs J-02's and J-03's own acceptance text
      require: J-02 — a changes list, its suppressed disclosure, and the earliest-run empty state; J-03 —
      the summary card and its cited-facts audit view. Both viewable via
      `demo.sh market-compass --session-live`. This is required acceptance content for these TARGET
      journeys, not a passenger task.

### New user-facing capability
None new — What-changed and Summary already render on `/`. This iteration confirms (and, if a live gap
is found, repairs) that both render the served fields byte-identically against the now fully-recovered
database, and produces their first real walkthrough evidence.

### New information displayed
None new.

### New user actions
None new — the existing "Show cited facts" and "Suppressed moves (N)" disclosures are already built.

### UI surface changes
None — same `/` page, same two existing cards (`CompassWhatChangedCard`, `CompassSummaryCard`).

### Product surface delta
J-02 and J-03 move from "built but frozen at `partial` since an incident-era downgrade, never
re-examined in 25 iterations" to "re-confirmed correct against the recovered live database, with real
walkthrough evidence" — closing this session's two oldest open journeys.

### Blueprint conformance
Today (`/`) — What-changed card (J-02) and Summary card (J-03); both existing Information Architecture
rows from baseline; no new surface.

### Data-contract additions
None. `session_delta` and `narrative` are already registered inside the Next-session manifest CONTENT
block (blueprint baseline row), computed by `app.engine.compass.build_manifest_payload` (composing
`app.engine.session_delta.compute_delta` and the narrative sentence builder) and served by
`GET /api/compass`. This iteration reads and re-verifies them; it introduces no new field, module, or
endpoint. Blueprint updated with an informational iter-31 note recording this (no IA or Data Contract row
change).

## OUT OF SCOPE

- Any new `next_session_manifests` mint beyond the three already-manifested `as_of` values named above
  (binding "Do not redo"; see `assumptions.md` `iter-31 — goal-decomposer`) — no backfill of the other
  non-word-bearing dates, no re-regeneration of `2025-04-15`, `2026-08-03`, or `2026-08-12`.
- Any change to `build_state_band`, `build_manifest_payload`, `_derive_prospective_eligible`,
  `_severity_at`, or `compass.vocabulary.direction_words` (binding "Do not redo" — J-07 is closed).
- Reopening J-11 recovery or serving verification (owner ruling, 2026-08-27, `docs/goal.md`).
- J-09 "The backend fits the host" — separate `partial` journey, not targeted this iteration.
- J-04's candidate-card screenshot retake (12th round owed), and J-05/J-06/J-08's recorded
  walkthroughs — passenger tasks; ride along only if genuinely incidental, never blocking this
  iteration's Definition of Done.
- The "What-changed vs Leadership-rotation duplicate list" question — owner decision, not a build item.
- `test_no_magic_numbers.py`'s pre-existing red failure (`indicators.py`/`forward_testing.py`/
  `research.py`, untouched since `0c445647`) — carried, unrelated surface; fix-or-waive remains the
  owner's call.
- The 2026-08-12 "Basis: rebuilt" vs "Basis: available" display question (J-11's open item, iter-30
  next-step item (a)) — owner decision pending, a display-only fix if ever authorized.
- `goal_gate.py`'s duplicate-journey-heading defect — standing framework note, not this iteration's
  scope.

## DEFINITION OF DONE

- [ ] J-02 passes via browser-qa-agent (all 6 acceptance steps verified live at the authorized `as_of`
      set)
- [ ] J-03 passes via browser-qa-agent (all 6 acceptance steps verified live at the authorized `as_of`
      set)
- [ ] Both journeys' `[NEW]`-flagged walkthroughs recorded and viewable via
      `demo.sh market-compass --session-live`
- [ ] Required-still-passing journeys J-01, J-04, J-05, J-06, J-07, J-08, J-10, J-11 remain green
      (deterministic replay + LLM fallback where no golden exists)
- [ ] `journey-scripts/J-11.json` executed in this iteration's replay lane with its real result reported
      verbatim (not silently re-edited, per the binding "Do not redo" ride-along item)
- [ ] No anti-goal violation introduced — AG-3 (spot-checked values byte-match live endpoints for the
      same as-of), AG-5 (no lookahead in the delta/narrative producers), AG-8 (column-projected reads
      only), AG-9 (zero external network calls), AG-12 (zero new manifest mints beyond the pre-existing
      28 rows, all byte-identical before/after), AG-13 (chrome/market vocabulary separation), AG-17
      (no eligibility upgraded on any incident-window date) — each re-verified independently
- [ ] Unit tests pass; no regressions (`test_session_delta.py`, `test_compass.py`, `test_api_compass.py`,
      `test_no_magic_numbers.py` unchanged coverage)
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-31-dev.md`, citing every live
      spot-check performed and its source-of-truth comparison, plus the before/after
      `next_session_manifests` row count

## TESTING REQUIREMENTS

- Browser: J-02 (all 6 steps), J-03 (all 6 steps); regression smoke via deterministic replay for J-01,
  J-04, J-05, J-06, J-07, J-08, J-10, J-11.
- Unit/integration: `test_session_delta.py`, `test_compass.py` (narrative + state_band + selection
  tests), `test_api_compass.py`, `test_no_magic_numbers.py` (unchanged coverage — no new config path
  this iteration).
- Error cases: any lane causing a NEW manifest mint on an `as_of` value outside `{2026-08-12,
  2025-04-15, 1996-02-01}` is a process violation and must be flagged explicitly in the dev handoff,
  never silently absorbed (iter-27/iter-29 lesson).

**Declared safe set for NEW MINTS this iteration (binding on every lane — dev, replay, browser-qa):**
zero new mints are authorized or expected this iteration. Every live `/api/compass` call must resolve to
an already-existing row at one of `{2026-08-12 (default/no param), "2025-04-15", "1996-02-01"}` — all
three confirmed read-only against the live database to already carry manifest rows before this iteration
starts (28 rows across 18 distinct `as_of` dates). Non-manifest reads (`GET /api/runs`, `GET /api/sectors`,
`GET /api/stocks`) may additionally target `2026-08-11` for J-02 step 4's spot-checks — those endpoints
carry no manifest and cannot mint anything. Any lane observing a NEW row is a process violation to be
flagged explicitly, not silently absorbed.

Test-first contract:

- TC-1: given `/` is loaded with no `asof` param (frontier `2026-08-12`), when the page renders, then
  the What-changed card header shows `vs 2026-08-11 (1 day ago)`, matching the immediately preceding row
  returned by `GET /api/runs` and its computed gap in days.
- TC-2: given the same frontier view, when the What-changed list renders, then every visible entry's
  kind badge follows the order Market → Breadth → Sector → Theme → Stock, and each entry's `drill_href`
  carries `?asof=2026-08-12` and resolves to a live page.
- TC-3: given the same frontier view, when the "Suppressed moves (N)" disclosure is opened, then N
  equals the number of listed suppressed entries and each entry's magnitude is strictly less than its
  threshold.
- TC-4: given the frontier view's sector delta entries, when one sector-rank move is spot-checked, then
  its from/to ranks equal the values served by `GET /api/sectors?as_of=2026-08-11` and
  `GET /api/sectors?as_of=2026-08-12` respectively, byte match.
- TC-5: given the frontier view's stock delta entries, when one leadership-bucket crossing is
  spot-checked, then its from/to bucket equal the values served by `GET /api/stocks?as_of=2026-08-11`
  and `GET /api/stocks?as_of=2026-08-12`.
- TC-6: given `/` is loaded with `?asof=1996-02-01` (the true earliest stored run, already carrying a
  manifest row — zero new mint), when the page renders, then the What-changed card shows the explicit
  no-prior-run sentence, no delta list, and no fabricated direction word anywhere on the card.
- TC-7: given the frontier view, when the Summary card renders, then the state, direction, breadth, and
  focus-count sentences each appear with `data-testid="compass-sentence-<template_id>"`, populated
  verbatim from `narrative.sentences`.
- TC-8: given the Summary card's "Show cited facts" disclosure is opened at the frontier view, when two
  fact values are spot-checked, then the regime-score fact equals `GET /api/dashboard`'s regime score
  and the severity fact equals `GET /api/market-phase`'s severity, both for `as_of=2026-08-12`.
- TC-9: given `/` is loaded with `?asof=1996-02-01`, when the Summary card renders, then the
  no-comparison sentence variant is shown, matching the fixture-tested
  `test_direction_no_prior_run_variant` behavior reproduced live.
- TC-10: given `/` is loaded with `?asof=2025-04-15` (already-manifested historical date, zero new
  mint), when the Summary card renders, then a visible retrospective stamp names that the summary was
  reconstructed under the current rule/config.
- TC-11: given a read-only DB connection opened AFTER every lane in this iteration finishes, when
  `next_session_manifests` is queried, then it holds exactly 28 rows across the same 18 `as_of` dates
  recorded before this iteration started — zero new mints.
- TC-12: given `journey-scripts/J-11.json` (rewritten 2026-09-01T01:51:59Z, never yet executed), when it
  runs FIRST in this iteration's deterministic replay lane, then its real pass/fail result is recorded in
  the merged results file and reported verbatim in the dev handoff — and it is not edited again this
  round regardless of the outcome.
- TC-13: given the narrative language scan, when the Summary card's rendered sentences at every
  authorized `as_of` are checked, then none contains a token from the committed banned-language list
  (imperative trade verbs, forecast terms, causal-attribution phrases).
- TC-14: given the Required-still-passing set (J-01, J-04, J-05, J-06, J-07, J-08, J-10, J-11), when the
  deterministic replay + LLM fallback lane runs, then all eight report PASS with no regression and mint
  zero additional `next_session_manifests` rows.

## NOTES

- **Why this reads as verification, not a rebuild:** direct code inspection before writing this spec
  found `app.engine.session_delta`, `app.engine.compass.build_narrative`,
  `compass-whatchanged-card.tsx`, and `compass-summary-card.tsx` all feature-complete, with 12
  fixture tests in `test_session_delta.py` and a matching set in `test_compass.py` already covering
  every acceptance step at the isolated-DB level. If the live pass finds nothing wrong, the honest
  outcome is a re-confirmed `passing` plus the two owed walkthroughs — not manufactured extra scope.
- **Carried, non-blocking:** the What-changed / Leadership-rotation duplicate-list question (owner
  decision); J-04's screenshot retake and the J-05/J-06/J-08 recorded walkthroughs (passenger tasks);
  the 2026-08-12 "Basis: rebuilt" display question; whether the three direction words being real on
  only 2-of-18 saved dates is acceptable (THE NEXT ROUND MUST NOT fill in the other 16 on its own —
  16 permanent writes to the protected table needs owner sanction, and this iteration touches none of
  them). Five older owner questions remain open and non-blocking: J-09's ~2.99 GB acceptability; J-06's
  "underlying run unavailable" wording; J-01's first two test steps; whether an empty "next-session
  focus" is acceptable; whether MNST joins the recovery list.
- **Standing framework note:** `goal_gate.py`'s duplicate-journey-heading defect (this session's own
  goal slice lists J-10 twice) is still unfixed and must be closed before any GOAL_ACHIEVED
  certification — carried forward, not this iteration's scope.
