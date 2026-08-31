# Goal Iteration 29 — Make J-07's direction words observable on real data

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 29
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict was ESCALATE (mandatory, no exceptions). iter-28's evaluator
  ESCALATEd explicitly because a `Depth: full` spec ran `lean` for the 7th time this session and
  permanently altered the protected `next_session_manifests` table with no independent checker
  present; this iteration performs the same class of action (a live, permanent, additive mint on
  that same table) and must not repeat that gap.
- **Frontend Present:** yes
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-04, J-05, J-06, J-08, J-10, J-11 (widened to the full
  passing set per the ESCALATE-widens-regression rule)
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; the manifest for close D derives only from state stored at or before D; never introduce lookahead anywhere. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local provider fixtures — no live external network calls or paid data services without an explicit goal.md amendment. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change; corrections happen only as new version rows; a historical view never substitutes a newer manifest. *(critical)*
  - **AG-13 — System-vs-market separation:** readiness/preflight vocabulary (Ready, Initializing, Backend unavailable, GO, DEGRADED, NO-GO) must never label market state, and regime/phase vocabulary must never label system state; the manifest's market and narrative blocks must contain no readiness tokens. *(critical)*
  - **AG-17 — Repair never rewrites provenance (owner, 2026-08-20):** restoring deleted historical data MUST NOT retroactively change research provenance. A manifest that was retrospective or ineligible stays that way; `prospective_eligible` is never upgraded merely because historical data was later repaired; `available_at_utc`, manifest versions, `content_hash`/`manifest_hash`, and prior eligibility classifications remain immutable (AG-12 governs the rows and files themselves). *(critical)*

## GOAL

Close J-07's one remaining gap — the three direction badges reading "NA" everywhere — by making
exactly one authorized, already-shipped, create-once-on-GET call that mints a manifest for a date
that has none, and proving live that the real words render correctly and stay consistent with the
rest of the page, under full-depth review with an independent auditor present.

## BACKGROUND

iter-28 built `state_band` correctly (11 tests, coherence-clean, verified read-only by two
independent lanes) but the feature is invisible: `state_band_json` is non-null on 0 of 26 stored
manifests because every one predates the field and manifests are never backfilled (binding "Do not
redo" — do not touch `build_state_band` itself). The iter-28 evaluator ESCALATEd specifically
because this exact class of action — a live write to the protected `next_session_manifests` table —
shipped at `lean` depth with no independent auditor, for the 7th time this session (iters 2, 6, 8,
23, 24, 26, 28); per the goal-decomposer rules, a prior ESCALATE verdict makes `Depth: full`
mandatory here, no exceptions. Applying the iter-28 lesson directly ("plan that freeze IN the same
iteration that adds the field, or the iteration cannot demonstrate its own feature") and the
iter-27 lesson ("where a plain GET can write, the authorized-inputs list has to be stated to the
lane that issues the requests, and every row-count claim must be re-derived AFTER the browsing lane
finishes"), this iteration names ONE exact date in advance, forbids every other lane from touching
any other date, and requires the row-count/AG-12 proof to be re-derived after every lane — including
replay and browser-qa — finishes. I queried the live database read-only to select the date (see
NOTES); no code path is touched — `build_state_band`, `_severity_at`, and the vocabulary map are
already reviewed and green and stay exactly as they are. Given the session's repeated silent
lean-demotion pattern on exactly this kind of database-mutating spec, the owner may want to consider
setting `CHAIN_REQUIRE_FULL_DEPTH` for this one iteration — that decision and the metadata line
belong to the owner, not to this spec.

## IN SCOPE

### Backend
- [ ] Execute exactly ONE authorized live `GET /api/compass?as_of=2026-08-03` request against the
      running canonical backend. No other `as_of` value may trigger a create-once mint anywhere in
      this iteration (dev verification, deterministic replay, or browser-qa) — see TESTING
      REQUIREMENTS TC-6.
- [ ] Confirm the resulting new `next_session_manifests` row (`as_of=2026-08-03`, `version=1`)
      carries a non-null `state_band_json` with real words for all three bands, produced by the
      existing `build_state_band` producer — no code change to `build_state_band`, `_severity_at`,
      or `compass.vocabulary.direction_words` (binding "Do not redo").
- [ ] Re-derive, AFTER every lane in this iteration finishes (never delegated to an earlier
      snapshot — iter-27 lesson), the full `next_session_manifests` row count (must be 27) and the
      26 pre-existing rows' complete column values (must be byte-identical to their iter-28-recorded
      state) to prove AG-12 held.
- [ ] Re-run `test_manifest_invariants.py` and the existing `state_band` route/fixture suite (11
      tests, unchanged since iter-28) against the post-mint database to confirm continued green.

### Frontend
- [ ] No code changes. Verify via browser-qa that the already-built
      `apps/frontend/components/compass-state-band-card.tsx` (iter-28, "Do not redo") renders all
      three direction badges as real words — not "NA" — when loading `/?asof=2026-08-03`, sourced
      verbatim from `GET /api/compass?as_of=2026-08-03`'s `state_band` field.

### New user-facing capability
On the one now-frozen date `2026-08-03` (and, going forward, any future date whose manifest is
minted), the Today page's three direction badges answer "improving or deteriorating" in real words
instead of "NA" — completing J-07's ten-second-read capability, at least once, on real data.

### New information displayed
None new — the badges and their underlying field already existed since iter-28; this iteration makes
their non-NA rendering observable for the first time.

### New user actions
None.

### UI surface changes
None — same `/` page, same components as iter-28; no new page, panel, or card.

### Product surface delta
J-07 moves from "the headline feature is invisible on every servable date" to "at least one
byte-verified date shows the real words, consistent with the rest of the page" — closing the sole
gap the iter-28 evaluator cited for holding J-07 at `partial`.

### Blueprint conformance
Today (`/`) — whole page, top to bottom (existing IA row from baseline/iter-28; no new surface).

### Data-contract additions
None. `state_band` (fields `regime`, `stress`, `breadth`, each `{direction_word: string, delta:
float|null}`) was already registered in the blueprint's iter-28 update, computed by
`app.engine.compass.build_manifest_payload` and served by `GET /api/compass`. This iteration adds no
new field, module, or endpoint — it only exercises the existing create-once-on-GET path on a date
that previously had no row.

## OUT OF SCOPE

- Any code change to `build_state_band`, `_severity_at`, the vocabulary map, or any other part of
  the state-band producer (binding "Do not redo" — iteration-state.md).
- Any additional manifest mint beyond `as_of=2026-08-03` — no second date, no broad backfill of the
  other manifest-less historical dates.
- Resolving the "What-changed vs Leadership-rotation duplicate list" question the iter-28 evaluator
  raised for the owner ("keep, merge, or narrow") — an owner decision point, not a build item.
- J-02, J-03, J-09 — partial, not targeted this iteration.
- Any AG-9 external network fetch. This action reads only already-ingested internal state (no
  provider call); it is ordinary create-once-on-GET behavior already exercised at iter-26/27, not a
  new dated exception, and must not be treated or logged as one.
- The J-04 screenshot retake and the J-05/J-06/J-07/J-08 recorded walkthroughs — passenger tasks,
  never an iteration goal (binding "Do not redo").
- Deleting the iter-23 7.8 GB throwaway clone — owner housekeeping item, not a journey.
- `goal_gate.py`'s duplicate-journey-heading defect — standing framework note, not this iteration's
  scope.

## DEFINITION OF DONE

- [ ] J-07 passes via browser-qa (all 7 steps verified live; step 3 shows real words, not "NA")
- [ ] Required-still-passing journeys J-01, J-04, J-05, J-06, J-08, J-10, J-11 remain green
      (deterministic replay + LLM fallback where no golden exists)
- [ ] No anti-goal violation introduced — AG-12 (26 pre-existing rows byte-identical), AG-9 (zero
      external network calls), and the "declared safe `as_of` set only" process fix all hold,
      re-verified independently
- [ ] Unit tests pass; no regressions (`test_manifest_invariants.py` + the 11 state_band tests +
      `test_no_magic_numbers.py`)
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-29-dev.md`, citing the exact
      `as_of` used, the before/after row count, and every `as_of` value any lane actually requested

## TESTING REQUIREMENTS

- Browser: J-07 (all 7 steps, focused on step 3 at `?asof=2026-08-03`); regression smoke via
  deterministic replay for J-01, J-04, J-05, J-06, J-08, J-10, J-11.
- Unit/integration: `apps/backend/tests/test_manifest_invariants.py` (immutability across the new
  27-row table), the existing `state_band` route/fixture tests (11, unchanged), `test_no_magic_numbers.py`
  (unchanged coverage — no new config path this iteration).
- Error cases: any live `as_of` request outside the declared safe set (below) occurring in any lane
  this iteration is a process violation and must be flagged in the dev handoff, not silently absorbed
  (iter-27 lesson).

**Declared safe `as_of` set for this iteration (binding on every lane — dev, replay, browser-qa):**
`{no param (Latest), "2026-08-12", "2025-04-15", "2026-08-03"}`. No lane may request any other value
that would trigger a create-once mint.

Test-first contract:

- TC-1: given `next_session_manifests` has 26 rows and none for `as_of=2026-08-03`, when the
  developer issues exactly one `GET /api/compass?as_of=2026-08-03` against the running backend, then
  the table contains exactly 27 rows and a new row exists with `as_of=2026-08-03`, `version=1`.
- TC-2: given the new row from TC-1, when its `state_band_json` column is read directly, then it is
  non-null and deserializes to three bands (`regime`, `stress`, `breadth`), each carrying a
  `direction_word` drawn from `compass.vocabulary.direction_words` and a `delta` that is a float or
  `null`.
- TC-3: given the frontend loads `/?asof=2026-08-03` after TC-1, when the market-state band renders,
  then all three direction badges display the same three words returned by
  `GET /api/compass?as_of=2026-08-03`'s `state_band` field, byte-identical, and none reads "NA".
- TC-4: given the same page load, when the regime badge's word and the Summary card's
  regime-direction sentence are compared, then both are consistent with the same served
  `state_band.regime` / `session_delta` fields — no card stating a real comparison while another card
  on the same screen reads "NA" for the same comparison (the exact iter-28 finding must not recur).
- TC-5: given the mint in TC-1, when the 26 pre-existing `next_session_manifests` rows' complete
  column values are re-read AFTER every lane in this iteration finishes, then each (`id`, `as_of`,
  `version`, `content_hash`, `manifest_hash`, `prospective_eligible`, `available_at_utc`, and every
  other column) is byte-identical to its iter-28-recorded value.
- TC-6: given this iteration's dev, replay, and browser-qa lanes all run, when every `as_of` value
  any of them actually requests is logged, then the full set is a subset of `{no param (Latest),
  "2026-08-12", "2025-04-15", "2026-08-03"}` with zero exceptions, cited verbatim in the dev handoff.
- TC-7: given the widened Required-still-passing set (J-01, J-04, J-05, J-06, J-08, J-10, J-11), when
  the deterministic replay lane executes, then all seven journeys' goldens PASS and mint zero
  additional `next_session_manifests` rows beyond TC-1's one.
- TC-8: given `test_manifest_invariants.py` and the existing state_band fixture/route suite (11
  tests), when re-run against the post-mint database/fixtures, then all pass with zero failures and
  zero skips beyond the already-documented `TRENDORA_MEMORY_PRESSURE` opt-in skips.

## NOTES

- **Date selection (read-only DB query, iter-29 planning):** `2026-08-03` was chosen because it has
  a stored `ScannerRun` (id 3154, 539 scored results), a real prior stored run
  (`2026-07-27`, id 3153) for delta comparison, zero existing `next_session_manifests` rows, sits
  outside both the iter-5 incident window (2026-08-11/2026-08-12) and the AG-9 dated-exception #2
  AVB-diagnostic six-date list (2026-08-05/06/07/10/11/12), and is well before the data frontier so
  `resolve_as_of_date` resolves normally (no interaction with the open B3 residual, which only
  affects frontier-dated manifests). Full reasoning logged to the assumption ledger
  (`iter-29 — goal-decomposer`).
- **Lessons applied:** iter-28's lesson (a manifest-content field ships dark until a fresh freeze
  happens — plan the freeze in the SAME iteration that needs to observe the field) is the entire
  shape of this iteration. iter-27's lesson (a plain GET can write; state the authorized-inputs list
  to the issuing lane; re-derive row counts after the lane finishes) is enforced via the declared
  safe `as_of` set (TC-6) and the after-every-lane re-derivation requirement (TC-5).
- **Carried, non-blocking, from iter-28's next-step recommendation (not this iteration's scope):**
  the What-changed / Leadership-rotation duplicate-list question (owner decision); J-04's screenshot
  retake and the J-05/J-06/J-07/J-08 recorded walkthroughs (passenger tasks); the replay lane's own
  stored-golden dates vs. the plan's safe-set wording (this spec's TC-6 scopes the constraint to
  create-once MINTS specifically, since replay goldens already point at dates that already carry
  manifest rows and cannot mint); the `state_band_json` content-fingerprint note for future re-issues
  of old dates; the `/market` picture's collapsed cross-view chart; J-01's automated re-check
  asserting less than the journey claims. Five older owner questions (J-09 ~2.99 GB acceptability;
  J-06's "underlying run unavailable" wording; J-01's first two test steps; empty "next-session focus"
  acceptability; whether MNST joins the recovery list) remain open and non-blocking.
- **Standing framework note:** `goal_gate.py`'s duplicate-journey-heading defect (this session's own
  goal slice lists J-10 twice) is still unfixed and must be closed before any GOAL_ACHIEVED
  certification — carried forward, not this iteration's scope.
