# Goal Iteration 30 — Make J-07's direction words real on the page users actually land on

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 30
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict was ESCALATE (mandatory, no exceptions). iter-29's evaluator
  ESCALATEd because the front page still contradicts itself (state-band badges read "NA" at the
  default landing view while the Summary card one line below reports a real change) and the proven
  next step is another permanent, additive write to the protected `next_session_manifests` table on
  the frontier date — the same class of sensitive action that has been silently demoted to `lean`
  seven times this session (iters 2, 6, 8, 23, 24, 26, 28). This iteration must not repeat that gap.
- **Frontend Present:** yes
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-04, J-05, J-06, J-08, J-10, J-11 (widened to the full
  passing set — same rule iter-29 applied under its own ESCALATE-driven full depth: a live write to
  the shared `next_session_manifests` table warrants re-checking every journey that reads it or
  shares its page)
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; the manifest for close D derives only from state stored at or before D; never introduce lookahead anywhere. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local provider fixtures — no live external network calls or paid data services without an explicit goal.md amendment. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change; corrections happen only as new version rows; a historical view never substitutes a newer manifest. *(critical)*
  - **AG-13 — System-vs-market separation:** readiness/preflight vocabulary (Ready, Initializing, Backend unavailable, GO, DEGRADED, NO-GO) must never label market state, and regime/phase vocabulary must never label system state; the manifest's market and narrative blocks must contain no readiness tokens. *(critical)*
  - **AG-17 — Repair never rewrites provenance (owner, 2026-08-20):** restoring deleted historical data MUST NOT retroactively change research provenance. A manifest that was retrospective or ineligible stays that way; `prospective_eligible` is never upgraded merely because historical data was later repaired; `available_at_utc`, manifest versions, `content_hash`/`manifest_hash`, and prior eligibility classifications remain immutable (AG-12 governs the rows and files themselves). *(critical)*

## GOAL

Close J-07's last gap by minting exactly one new, already-proven version of the FRONTIER manifest
(`as_of=2026-08-12`) so the three direction badges show real words on `/` at the default landing
view — the page a user actually lands on — instead of on a hand-picked historical date one click
away.

## BACKGROUND

iter-28 built `state_band` correctly; iter-29 proved it renders real, config-correct words at
`/?asof=2026-08-03` — but the evaluator held J-07 at `partial` both rounds because `docs/goal.md`'s
own Success Criteria require direction "**from `/` alone, without navigating**", and `/` with no
`asof` param (2026-08-12, the frontier — confirmed live: `SELECT MAX(asof_date) FROM scanner_runs`)
still shows "NA" on all three badges while the Summary card one line below states a real comparison.
I re-confirmed this myself, read-only: `next_session_manifests` holds 27 rows; `as_of=2026-08-12`
carries 6 versions (1–6), every one with `state_band_json` NULL; a stored `ScannerRun` exists for
both 2026-08-12 (id 3158) and its immediately preceding date 2026-08-11 (id 3157), so a regenerated
version has real prior-run data to compute deltas from — nothing here is unproducible.

The evaluator's next-step is exact and unambiguous: mint a NEW VERSION of the 2026-08-12 manifest via
the confirm-gated `POST /api/compass/regenerate` action iter-3 shipped and iter-26 already proved live
on a different date (`as_of=2025-04-15`, v1→v2). `regenerate_manifest` (`app/engine/compass.py:1185`)
never touches an existing version — it inserts version N+1 through the SAME `_freeze_manifest` writer
`build_manifest_payload`/`build_state_band` already use, and unconditionally sets
`prospective_eligible=False` (producer `"regenerate"` fails `_derive_prospective_eligible`'s
`producer == "ingest_finalize"` / `version == 1` checks) — so AG-12 and AG-17 hold by construction, not
by discipline. No date choice is needed this round — the evaluator named the date directly (the
frontier itself), removing the ambiguity iter-29's date-selection decision had to resolve, so no new
assumption-ledger entry is required here.

**Lessons applied:** iter-28's lesson (a manifest-content field ships dark until a fresh freeze
happens — plan the freeze in the SAME iteration that needs to observe the field) — this time the
freeze must land on the LANDING date itself, not a convenient side date (iter-29's second lesson:
"picking a convenient manifest-less historical date proves the producer and leaves the journey open").
iter-27's lesson (a plain GET can write; state the authorized-inputs list to the issuing lane;
re-derive row counts after every lane finishes) and iter-29's own correction of it (the constraint
binds NEW MINTS specifically, not merely "which dates get visited" — replay goldens legitimately
revisit already-manifested dates) both shape the safe-set wording below. iter-23b's lesson (a `.db`
sha256 alone does not prove immutability under WAL — bracket `.db` + `-wal` + `-shm`, captured AFTER
the last lane finishes) governs the AG-12 re-derivation this round. iter-29b's lesson (a golden written
AFTER replay is not coverage) governs the `J-07.json` fix below — it must be updated to check the
`compass-state-band-*-direction` testids BEFORE the replay lane runs this round, per the auditor's T1
finding carried from iter-28/iter-29.

## IN SCOPE

### Backend
- [ ] Execute exactly ONE authorized live `POST /api/compass/regenerate?as_of=2026-08-12&confirm=true`
      request against the running canonical backend. No other `as_of` value may trigger a NEW mint
      anywhere in this iteration (dev verification, deterministic replay, or browser-qa) — see
      TESTING REQUIREMENTS TC-7.
- [ ] Confirm the resulting new `next_session_manifests` row (`as_of=2026-08-12`, `version=7`) carries
      a non-null `state_band_json` with real (non-null) words and deltas for all three bands and
      `prospective_eligible=false` — produced entirely by the existing `build_manifest_payload` /
      `build_state_band` / `_derive_prospective_eligible` producers. No code change to any of them, to
      `_severity_at`, or to `compass.vocabulary.direction_words` (binding "Do not redo").
- [ ] Add one unit test (fixture-scoped, isolated DB — never the live database) asserting that a
      REGENERATED version on a frontier-shaped as-of still yields `state_band` populated with real
      words AND `prospective_eligible: false` in the same call — closing the coverage gap the auditor
      found at iter-29 (T1: a golden written after replay is not coverage; the existing 11 state_band
      tests never exercised the regenerate path together with state_band).
- [ ] Update `runs/goal-session-market-compass/journey-scripts/J-07.json`'s regression golden so its
      assertions target the three `compass-state-band-regime-direction` /
      `compass-state-band-stress-direction` / `compass-state-band-breadth-direction` testids' rendered
      text at the default `/` view (no `asof` param) — not only a narrative sentence. Write/update this
      BEFORE the deterministic replay lane executes this round (iter-29b lesson: a golden edited after
      the replay ran is not coverage).
- [ ] Re-derive, AFTER every lane in this iteration finishes (dev, replay, browser-qa — never
      delegated to an earlier snapshot), the row count for `as_of=2026-08-12` (must be 7) and versions
      1–6's complete column values (`id`, `content_hash`, `manifest_hash`, `prospective_eligible`,
      `available_at_utc`, and every other column — must be byte-identical to their iter-29-recorded
      state), checked against the `.db` file AND any `-wal`/`-shm` sibling (iter-23b lesson).
- [ ] Re-run `test_manifest_invariants.py` and the existing state_band route/fixture suite (11 tests,
      unchanged since iter-28) against the post-mint database to confirm continued green.

### Frontend
- [ ] No code changes. Verify via browser-qa that the already-built
      `apps/frontend/components/compass-state-band-card.tsx` (iter-28, "Do not redo") renders all
      three direction badges as real words — not "NA" — when loading `/` with NO `asof` param (the
      default landing view), sourced verbatim from `GET /api/compass`'s `state_band` field.

### New user-facing capability
On the DEFAULT landing view (`/`, no `asof` param — the page every user actually lands on), the three
direction badges now answer "improving or deteriorating" in real words instead of "NA", completing
J-07's ten-second-read capability on the page where it is actually read.

### New information displayed
None new — the badges and their underlying `state_band` field already existed since iter-28; this
iteration makes their non-NA rendering observable on the frontier/default date for the first time.

### New user actions
None.

### UI surface changes
None — same `/` page, same components as iter-28/iter-29; no new page, panel, or card.

### Product surface delta
J-07 moves from "real words exist only on one manually-chosen historical date, one click away from
the page users actually load" to "the words are real on the page a user actually lands on by
default" — closing the exact contradiction (badges "NA" beside a Summary card reporting a real
change on the same screen) that both the iter-28 and iter-29 evaluators cited for holding J-07 at
`partial`.

### Blueprint conformance
Today (`/`) — whole page, top to bottom (existing IA row from baseline/iter-28; no new surface).

### Data-contract additions
None. `state_band` (fields `regime`, `stress`, `breadth`, each `{direction_word: string, delta:
float|null}`) was already registered in the blueprint's iter-28 update, computed by
`app.engine.compass.build_manifest_payload` and served by `GET /api/compass`. This iteration adds no
new field, module, or endpoint — it exercises the existing confirm-gated regenerate action
(`POST /api/compass/regenerate`, registered iter-3) on the frontier date so the already-registered
field is observable where the journey is actually read. Blueprint updated with an informational
iter-30 note recording this (no IA or Data Contract row change).

## OUT OF SCOPE

- Any code change to `build_state_band`, `_severity_at`, `compass.vocabulary.direction_words`,
  `build_manifest_payload`, or `_derive_prospective_eligible` (binding "Do not redo" —
  iteration-state.md) — only the golden/test additions above touch this surface.
- Any manifest mint beyond `as_of=2026-08-12` version 7 — no second date, no broad backfill of other
  historical dates, no re-regeneration of `2025-04-15` or `2026-08-03`.
- Resolving the "What-changed vs Leadership-rotation duplicate list" question the iter-28/29
  evaluators raised for the owner ("keep, merge, or narrow") — an owner decision point, not a build
  item.
- J-02, J-03, J-09 — partial, not targeted this iteration.
- Any AG-9 external network fetch. `regenerate_manifest` reads only already-ingested internal state
  (no provider call); this is ordinary, already-shipped action-endpoint behavior (iter-3/iter-26), not
  a new dated exception.
- The J-04 screenshot retake (12th round owed) and the J-05/J-06/J-07/J-08 recorded walkthroughs —
  passenger tasks, never an iteration goal (binding "Do not redo").
- `test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers`'s pre-existing red failure
  (`indicators.py`/`forward_testing.py`/`research.py`, untouched since `0c445647`) — carried,
  non-blocking, owner fix-or-waive item, unrelated to this iteration's surface.
- Deleting the iter-23 7.8 GB throwaway clone — owner housekeeping item, not a journey.
- `goal_gate.py`'s duplicate-journey-heading defect — standing framework note, not this iteration's
  scope.

## DEFINITION OF DONE

- [ ] J-07 passes via browser-qa (all 7 steps verified live at the DEFAULT `/` landing view — no
      `asof` param — with real direction words, not "NA", and no contradiction against the Summary
      card)
- [ ] Required-still-passing journeys J-01, J-04, J-05, J-06, J-08, J-10, J-11 remain green
      (deterministic replay + LLM fallback where no golden exists)
- [ ] No anti-goal violation introduced — AG-12 (versions 1–6 byte-identical after every lane, `.db`
      + `-wal`/`-shm` bracketed), AG-17 (version 7 `prospective_eligible=false`, no eligibility
      upgrade to any earlier repaired data), AG-9 (zero external network calls), AG-13 (chrome/market
      vocabulary separation holds) — all re-verified independently
- [ ] Unit tests pass; no regressions (`test_manifest_invariants.py`, the 11 existing state_band
      tests plus the new regenerate+state_band test, `test_no_magic_numbers.py` unchanged coverage)
- [ ] Regression golden `journey-scripts/J-07.json` asserts the three
      `compass-state-band-*-direction` testids at the default `/` view, updated BEFORE the replay
      lane runs this round, and exercised successfully (mtime precedes its verify capture)
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-30-dev.md`, citing the exact
      before/after row count and column values for `as_of=2026-08-12`, and every `as_of` value any
      lane actually caused a new mint on this iteration

## TESTING REQUIREMENTS

- Browser: J-07 (all 7 steps, focused on step 3 at the DEFAULT `/` view — no `asof` param);
  regression smoke via deterministic replay for J-01, J-04, J-05, J-06, J-08, J-10, J-11.
- Unit/integration: `apps/backend/tests/test_manifest_invariants.py`, the existing `state_band`
  route/fixture tests (11, unchanged) plus one new regenerate+state_band test,
  `test_no_magic_numbers.py` (unchanged coverage — no new config path this iteration).
- Error cases: any lane this iteration causing a NEW manifest mint on an `as_of` value other than
  `2026-08-12` is a process violation and must be flagged explicitly in the dev handoff, not silently
  absorbed (iter-27/iter-29 lesson); a `POST /api/compass/regenerate` call without `confirm=true`
  must still return HTTP 400 and create no row (pre-existing, re-verify unchanged).

**Declared safe set for NEW MINTS this iteration (binding on every lane — dev, replay, browser-qa):**
the ONLY `as_of` value any lane may cause a NEW manifest mint on is `2026-08-12`, via exactly one
`POST /api/compass/regenerate?as_of=2026-08-12&confirm=true` call. This binds MINTS specifically, not
which dates get visited — the regression-replay goldens for J-01/J-04/J-05/J-06/J-08/J-10/J-11
legitimately revisit their own already-manifested dates (iter-29's corrected framing after its
auditor's B1 finding); any lane visiting a date must find (or itself only ever create, for
`2026-08-12`) an already-existing manifest row there, verified via
`SELECT as_of, version FROM next_session_manifests` before and after.

Test-first contract:

- TC-1: given `next_session_manifests` holds 6 versions for `as_of=2026-08-12` (all `state_band_json`
  null) and a stored `ScannerRun` exists for both 2026-08-12 and its immediately preceding date
  2026-08-11, when the developer issues exactly one
  `POST /api/compass/regenerate?as_of=2026-08-12&confirm=true` against the running canonical backend,
  then `next_session_manifests` contains exactly 28 rows total and a new row exists with
  `as_of=2026-08-12`, `version=7`.
- TC-2: given the new version-7 row from TC-1, when its `state_band_json` column is read directly,
  then it is non-null and deserializes to three bands (`regime`, `stress`, `breadth`), each carrying a
  `direction_word` drawn from `compass.vocabulary.direction_words` and a `delta` that is a float (not
  null, since a real preceding run at 2026-08-11 exists for every band's input).
- TC-3: given the frontend loads `/` with NO `asof` param after TC-1, when the market-state band
  renders, then all three direction badges (`compass-state-band-regime-direction`,
  `compass-state-band-stress-direction`, `compass-state-band-breadth-direction`) display the same
  three words returned by `GET /api/compass`'s `state_band` field, byte-identical, and none reads
  "NA".
- TC-4: given the same default-view page load, when the regime badge's word and the Summary card's
  regime-direction sentence are compared, then both are consistent with the same served
  `state_band.regime` / `session_delta` fields — no card stating a real comparison while another card
  on the same screen reads "NA" for the same comparison (the iter-28/iter-29 contradiction must not
  recur on the default view).
- TC-5: given the mint in TC-1, when versions 1–6 of the `as_of=2026-08-12` manifest are re-read AFTER
  every lane in this iteration finishes (dev, replay, browser-qa — never delegated to an earlier
  snapshot), then each (`id`, `version`, `content_hash`, `manifest_hash`, `prospective_eligible`,
  `available_at_utc`, and every other column) is byte-identical to its iter-29-recorded value, checked
  against both the `.db` file and any `-wal`/`-shm` sibling.
- TC-6: given version 7's `prospective_eligible` field, when `_derive_prospective_eligible` evaluates
  it, then it is `false` because `generation.producer == "regenerate"` (not `ingest_finalize`) —
  proven by the new unit test asserting a regenerated version on a frontier-shaped as-of still yields
  `prospective_eligible: false` in the same call that populates `state_band`.
- TC-7: given this iteration's dev, replay, and browser-qa lanes all run, when every `as_of` value any
  of them causes a NEW mint on is logged, then the only such value is `2026-08-12`, cited verbatim in
  the dev handoff; any lane visiting a different `as_of` value must find an already-existing manifest
  row there or the run is flagged as a process violation, not silently absorbed.
- TC-8: given the widened Required-still-passing set (J-01, J-04, J-05, J-06, J-08, J-10, J-11), when
  the deterministic replay lane executes, then all seven journeys' goldens PASS and mint zero
  additional `next_session_manifests` rows beyond TC-1's one.
- TC-9: given `journey-scripts/J-07.json`'s regression golden updated to assert the three
  `compass-state-band-*-direction` testids' text content at the default `/` view, when the
  deterministic replay lane executes it, then it PASSES against the post-mint database, and the
  golden file's mtime precedes the corresponding `J-07-verify.png` capture time (never the reverse).
- TC-10: given `test_manifest_invariants.py` and the existing state_band fixture/route suite (11
  tests) plus the new TC-6 test, when re-run against the post-mint database/fixtures, then all pass
  with zero failures and zero skips beyond the already-documented `TRENDORA_MEMORY_PRESSURE` opt-in
  skips.

## NOTES

- **Date is not a new decision:** the evaluator's next-step recommendation names `2026-08-12` (the
  frontier) directly, unlike iter-29 which had to choose an unnamed manifest-less date — no new
  assumption-ledger entry is warranted for the date itself. If the owner instead rules that showing
  the words correctly on one real historical date is sufficient and "NA" on the frontier landing view
  is acceptable (the open question logged at `state/assumptions.md`, `iter-29 — goal-evaluator`), that
  ruling supersedes this iteration's scope — but absent such a ruling, ESCALATE calls for the bounded
  action, not for waiting.
- **Carried, non-blocking, from iter-29's next-step recommendation (not this iteration's scope):** the
  What-changed / Leadership-rotation duplicate-list question (owner decision); J-04's screenshot
  retake and the J-05/J-06/J-07/J-08 recorded walkthroughs (passenger tasks); the `state_band_json`
  content-fingerprint note for future re-issues of old dates; the `/market` picture's collapsed
  cross-view chart; J-01's automated re-check asserting less than the journey claims. Five older
  owner questions (J-09 ~2.99 GB acceptability; J-06's "underlying run unavailable" wording; J-01's
  first two test steps; empty "next-session focus" acceptability; whether MNST joins the recovery
  list) remain open and non-blocking.
- **Standing framework note:** `goal_gate.py`'s duplicate-journey-heading defect (this session's own
  goal slice lists J-10 twice) is still unfixed and must be closed before any GOAL_ACHIEVED
  certification — carried forward, not this iteration's scope.
