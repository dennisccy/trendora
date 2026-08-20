# Goal Iteration 5 — Manifest make-up run (light) + two host-safety guardrails + J-01 golden repair

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: the manifest freeze/integrity pipeline spans
  `data_manager.py` (ingest finalize), `compass.py` (writer + `POST /api/compass/regenerate`),
  `db.py`/`models.py` (schema), and the frontend manifest strip; this exact cross-cutting surface
  already produced one critical, auditor-only-caught bug (AG-12 export overwrite, iter-3), and this
  spec's own investigation surfaced a second subtle cross-cutting interaction (data-removal/backfill
  semantics vs. the append-only manifest store — see BACKGROUND) that needs audit + coherence eyes
  again, not just developer/reviewer eyes.
- **Frontend Present:** yes
- **Target journeys:** J-05, J-06
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
    **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
    values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha
    claims; never place or simulate orders. Candidate framing is "worth monitoring", never advice. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
    the manifest for close D derives only from state stored at or before D; never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the
    post-decompose gate. (This cycle introduces no Evidence Claims — the gate passes automatically.) *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never crash an existing
    page or exhaust memory — consumers of widened fields are re-validated, the UI degrades gracefully (contained
    error boundary, honest "—"/NA placeholder), and unbounded whole-table ORM loads are forbidden (the delta
    engine reads column-projected selects, never full record_json sweeps). *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local provider
    fixtures — no live external network calls or paid data services without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection), carried from ops-hardening:** heavy compute MUST be
    launched only via the project launch scripts, which MUST apply the host caps declared in
    `project-extensions/host-guard/host-guard.env` whenever present (CPU-affinity mask, BLAS/OMP thread caps)
    plus the `config.yaml` `server.memory_cap_mb` / `malloc_arena_max` values. Never remove, weaken, or bypass
    these caps; stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless of test
    outcomes. The ceiling VALUES are an owner-set envelope (current: `memory_cap_mb` 8192,
    `HOST_GUARD_MEMORY_HIGH` 12G, per the dated owner amendments recorded in
    `docs/archive/goal-ops-hardening.md`); only the owner may change them. *(critical)*
  - **AG-11 — No new composite candidate number:** no "fit", "conviction", "match", "probability of success",
    or any new blended score may be attached to candidates, the market, or the manifest; candidate presentation
    is limited to the existing three scores/buckets, config word maps, and structured reason/caution codes. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are never
    mutated or deleted by any later ingest, rebuild, data removal, config change, or code change; corrections
    happen only as new version rows; a historical view never substitutes a newer manifest. *(critical)*
  - **AG-13 — System-vs-market separation:** readiness/preflight vocabulary (Ready, Initializing, Backend
    unavailable, GO, DEGRADED, NO-GO) must never label market state, and regime/phase vocabulary must never
    label system state; the manifest's market and narrative blocks must contain no readiness tokens. *(critical)*
  - **AG-14 — No Tapeology coupling:** no imports from, network calls to, or writes into the tapeology
    repository or its services; the handoff is exclusively the local exported artifact and Trendora's own
    served API. *(critical)*
  - **AG-15 — No outcome-tuned selection:** the selection rule and its thresholds must not be chosen or revised
    from realized forward returns within this goal; no Evidence Claim is introduced for it; any future
    selection-edge claim goes through the pre-registration registry and referee. *(critical)*
  - **AG-16 — Cohorts are not controls:** the comparison cohort and the near-threshold shadow cohort are frozen
    non-selected pools, not matched or causal control groups; no surface, artifact, or narrative may present
    candidate-vs-cohort differences as causal, as expectancy, or as a certified edge; any incremental-value or
    threshold study over these cohorts requires its own pre-registered experiment (registry + referee) in a
    future goal, consuming only manifests with `prospective_eligible: true` — consumers must fail closed,
    treating anything other than `true` (including an absent field) as ineligible, verifying `manifest_hash`
    over the artifact bytes BEFORE trusting any field (a mismatch rejects the artifact for prospective use),
    and treating an individual downstream observation as prospective only when its event timestamp is
    strictly later than the manifest's `available_at_utc` — `prospective_eligible: true` is necessary but
    not sufficient per observation. *(critical)*

## GOAL

Harden the two outstanding host-safety guardrails (memory-pressure test gating, `next build` worker
cap), repair the twice-cried-wolf J-01 replay golden, and exercise the already-built manifest
freeze/immutability pipeline (J-05, J-06) live against the running app for every step the current
data state can actually support — using the already-built fixture-scoped test suite, not a new live
drill, for the one flagship fact the production database can no longer produce.

## BACKGROUND

The iter-4 evaluator's binding next-step is to run the J-05/J-06 make-up drill at full depth
(auditor watching, since this exact feature already produced one critical, auditor-only-caught bug —
AG-12 export overwrite, iter-3) and carry three small jobs with it: goal.md Constraints (a)
memory-pressure test gating and (b) `next build` ≤4 workers (both "due before two backends run" per
`iteration-state.md`'s Do-Not-Redo list), plus a fix for the J-01 replay golden, which has now
produced the identical false FAIL twice on GRMN's line-wrapped "Consumer Discretionary" cell
(lesson iter-4: "A golden overturned twice must be repaired... in the next iteration that touches
the lane").

**Coordinator directive for this iteration:** a second, independent goal-mode engine is active on
this 26.7 GB host, which froze once already today from memory overcommit. Heavy drills
(remove+backfill, ingest-finalize, memory measurement) must stay as light as the acceptance evidence
allows. This spec is written accordingly — see NOTES for the concrete sequencing/lightness rules,
and see the finding below, which independently makes the live drill lighter than iter-3/iter-4
assumed it would need to be.

**Load-bearing finding (direct, read-only inspection of the live 7.8 GB DB, 2026-08-20, no service
started):** J-05 step 2's flagship claim — a manifest minted by `ingest_finalize` with
`mode: at_ingest`, `version: 1`, `prospective_eligible: true` — can only ever be computed for the
CURRENT bar frontier (the single latest `daily_prices` date), and `next_session_manifests` is
append-only / skip-if-exists (AG-12: no UPDATE path exists). `daily_prices` and `scanner_runs` both
currently max out at 2026-08-12 (`seed_latest_date`, per iter-1's finding — 2026-08-13/14 were
user-added bars with no committed seed beneath them and are permanently unrecoverable offline). But
2026-08-12 **already carries 5 `next_session_manifests` rows** — an iter-2-era placeholder version 1
(`mode` NULL, from the pre-freeze schema migration) plus four `at_ingest`/`frozen: true`/
`prospective_eligible: false` rows minted 2026-08-20 10:23–10:27 by regenerate-class calls during
iter-3's own build/testing. Because the writer is append-only and skip-if-exists, **no future
remove+backfill of 2026-08-11/2026-08-12 can ever mint a fresh version-1 row there again** — that
slot is permanently burned, independent of anything this iteration does. A full scan of
`next_session_manifests` confirms only 14 as-of dates carry any row at all (1996-02-01, 2001-04-17,
2005-04-01, 2020-03-20, 2022-06-15, 2025-04-15, 2026-03-30, 2026-03-31, 2026-04-01, 2026-07-23,
2026-08-05, 2026-08-10, 2026-08-11, 2026-08-12) — every OTHER scanner_run date (3,080 total) is
untouched, so J-05 step 7 / J-06 step 1's "another/old removed date" steps have abundant safe
choices; only the ONE frontier-eligible date is burned.

Advancing the real bar frontier past 2026-08-12 needs a live network fetch (AG-9 — requires an
explicit goal.md amendment, not authorized here). Clearing the stale rows would touch the spirit of
AG-12's append-only guarantee without owner sign-off. Neither is this iteration's call. Instead, this
spec routes the flagship mechanism proof to the ALREADY-BUILT, ALREADY-PASSING fixture-scoped test
suite (`test_manifest_invariants.py`'s `frontier_run`-fixture tests, including
`test_tc20_baseline_is_eligible`, and `test_ingest_finalize_compass.py`) — each of which builds its
OWN small, isolated SQLite fixture DB via `app.db.make_engine` and so has no burned-slot problem and
no 7.8 GB-file cost. This is not a workaround invented for host safety; it is exactly what goal.md's
own Constraints call for ("new tests are synthetic-fixture, file-scoped"). The live app is used for
every OTHER J-05/J-06 step the current data state can actually exercise. This reasoning is logged to
the assumption ledger (`runs/goal-session-market-compass/state/assumptions.md`, iter-5 entry).

**Lessons applied:** iter-1's seed-safety lesson (verify `seed_latest_date` before ANY Remove;
2026-08-13/14 are permanently gone) governs the exact dates used below. Iter-3's lesson ("plan the
remove+backfill drill as a first-class, budgeted step, or state up front that the journey cannot
close this round") is satisfied by stating precisely, per step, what closes this iteration and what
carries forward, with reasons. Iter-2's lesson (depth-divergence risk) means: if the engine dispatches
this at anything other than `full`, that is itself an ESCALATE-class signal for the evaluator, not a
silent downgrade to accept.

**Carried, unchanged owner-pending blockers** (not this iteration's job to resolve — restated for
visibility only): J-06 step 2's literal "the underlying run is unavailable" wording (auditor finding
B2 — opening the page quietly rebuilds the deleted day); J-01 steps 1–2 test-step rewording; whether
an empty "next-session focus" on the newest date is an acceptable honest result; the J-09 2.5 GB vs.
3.44 GB target ruling. None of these block this iteration's scope.

## IN SCOPE

### Backend
- [ ] Gate `test_evidence_drawdown_memory_pressure.py`, `test_samples_memory_pressure.py`, and
  `test_ingest_finalize_memory_pressure.py` behind an explicit `TRENDORA_MEMORY_PRESSURE=1` opt-in
  (skip by default); remove every `shutil.copyfile`/`copy2` call against the live
  `apps/backend/data/trendora.db` in these three files AND in `test_start_backend_script.py`'s three
  copy sites (`:425`, `:562`, `:1592`) — synthesize or subset a small DB fixture instead
  (goal.md Constraint (a))
- [ ] Repair the deterministic-replay text matcher (`scripts/automation/lib/replay-lane.sh` and
  whichever text-extraction step it invokes) so J-01 step 3's expectation
  (`runs/goal-session-market-compass/journey-scripts/J-01.json`, `expect.text: "Consumer
  Discretionary"`) matches the sector cell's own rendered text content (whitespace/newline-normalized),
  not a raw contiguous-substring scan of the full page — fixes the two-line-wrap false FAIL that has
  now recurred in iter-3 and iter-4
- [ ] Execute and honestly observe the J-05/J-06 live make-up drill against the running app, following
  the host-safety sequencing in NOTES: (i) remove+backfill the seed-safe last two trading days via
  `/data`; (ii) a further seed-safe backfill on a clean, never-manifested historical date (pick
  outside the 14-date burned list above); (iii) remove-data over the range covering the frontier
  manifest's source run, then backfill it back; (iv) one confirm-gated
  `POST /api/compass/regenerate` call. Record every observed outcome verbatim in the dev handoff,
  explicitly including any step whose literal wording the current data state cannot reach and why
- [ ] Run the named fixture-scoped test files targeted (never the full suite): `test_manifest_invariants.py`,
  `test_ingest_finalize_compass.py`, `test_api_compass.py`, `test_compass.py`; plus a skip-only check
  of the three memory-pressure files and `test_start_backend_script.py`'s copy sites (no
  `TRENDORA_MEMORY_PRESSURE` set). Cite pass results by name/file:line in the dev handoff

### Frontend
- [ ] Bound production `next build` to ≤4 workers in `apps/frontend/next.config.mjs`
  (`experimental.cpus` or the Next-15 equivalent — it fans out 16-way today) (goal.md Constraint (b))
- [ ] No UI code changes planned. `compass-manifest-strip.tsx` (existing, iter-3-built) is exercised
  as-is against the drill's live data; TC-8 and TC-15 name the exact stamps/counts/cohort-table and
  multi-version-list values it must display — verification only, not new UI

### New user-facing capability
None net-new. The already-shipped manifest strip is proven against genuinely fresh drill data (new
`ScannerRun` engine-identity stamps, a new regenerate version, a basis-disclosure state change) for
the first time, rather than gaining new UI.

### New information displayed
None new.

### New user actions
None new — the existing `/data` Remove/Backfill controls and the existing confirm-gated Regenerate
action are exercised, not added.

### UI surface changes
None.

### Product surface delta
No visible page or navigation change. What changes is evidence: the manifest freeze/immutability
behavior becomes proven under real data-lifecycle events (removal, restore, regenerate) rather than
resting on code review and fixture tests alone.

### Blueprint conformance
`/` — Today. Matches blueprint.md's Information Architecture row: "J-05 / J-06 manifest freeze +
immutability | `/` — manifest strip... — no separate nav route exists for it". No new surface.

### Data-contract additions
None. This iteration verifies/exercises the already-registered FREEZE/INTEGRITY block (blueprint.md
Data Contract row 2) and the Engine identity row (row 3), both currently tagged
`[TARGET — iter-3 build in progress]`. Per blueprint.md's own rule, those rows flip to `[LIVE]` only
once the goal-evaluator confirms J-05/J-06 passing with evidence — that confirmation is the
evaluator's call, not this spec's. A short dated note is appended to blueprint.md recording this
iteration's burned-frontier-slot finding so a future decomposer does not have to re-derive it.

## OUT OF SCOPE

- J-07, J-08 — not targeted; still failing; untouched this iteration.
- J-09 target decision, re-measurement, and the `_BarCache.prefill` re-bound (Constraint (c)) — owner
  ruling still pending; binding "Do not redo" (no VmPeak re-measurement until a lever changes).
- Re-tuning `database.pragmas.cache_size`, `pool_size`, `max_overflow`, `memory_cap_mb`, or
  `malloc_arena_max` — binding "Do not redo".
- J-06 step 2's literal "the underlying run is unavailable" wording assertion — owner ruling pending
  (auditor finding B2); this iteration documents observed behavior but does not require the literal
  string to pass, and does not implement either of the two owner-decidable fixes (changing dated-page
  as-of resolution, or rewording the journey text).
- J-01 steps 1–2 test-step rewording; whether an empty "next-session focus" on the newest date is
  acceptable — owner rulings pending, unrelated to this iteration's target.
- Any new schema/migration beyond iter-3's already-built additive columns and composite index — none
  needed or planned.
- Advancing real bar/price history past 2026-08-12 via a live network fetch — requires an explicit
  AG-9 goal.md amendment; not authorized here.
- Clearing or deleting the pre-existing (burned) `next_session_manifests` rows for
  2026-08-05/08-10/08-11/08-12 or any other already-manifested date — not attempted; would risk the
  append-only spirit of AG-12 without explicit owner sign-off.
- Building a `database.url` env-var override (mirroring `TRENDORA_COMPASS_EXPORT_DIR`'s pattern) to
  run a live drill against an isolated small DB — a plausible FUTURE lever, flagged in NOTES, but new
  scope this iteration deliberately does not take on given today's host-safety priority.
- Running the full pytest suite or the ~31-minute heavy VmPeak drill.
- Fixing the demo/walkthrough tool's journey-tagging defect (assumption-ledger iter-3 note: an empty
  Journey column was observed) — framework tooling, flagged as a risk to watch in NOTES, not mandated
  to fix here.

## DEFINITION OF DONE

- [ ] Constraint (a) landed: `TRENDORA_MEMORY_PRESSURE` gate present on all 3 named memory-pressure
  files; zero `shutil.copy*` calls against the live DB remain in those 3 files or
  `test_start_backend_script.py`'s 3 copy sites (grep-verifiable)
- [ ] Constraint (b) landed: `next.config.mjs` reads ≤4 workers (grep-verifiable)
- [ ] J-01 replay golden repaired: a targeted replay of J-01 reports PASS against the unchanged UI
- [ ] J-05, J-06 verified via browser-qa-agent for every step this iteration's TESTING REQUIREMENTS
  mark live-testable; the flagship at-ingest-v1-eligible mechanism verified via the named
  fixture-scoped tests (scoped run, pass, cited by file:line in the dev handoff); J-06 step 2's
  literal wording assertion explicitly excluded per the carried owner-pending blocker
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04 remain green (deterministic replay + LLM
  fallback, mechanically verified)
- [ ] Byte-identity of `/api/dashboard`, `/api/stocks`, `/api/market-phase` for as_of 2026-08-11 and
  2026-08-12 holds pre- vs. post-drill
- [ ] No anti-goal violation introduced; AG-12 tamper detection re-confirmed via a byte-flip check
- [ ] Targeted unit/integration tests pass (files named in TESTING REQUIREMENTS); the full suite is
  NOT run
- [ ] `[NEW]`-flagged walkthroughs exist for J-01 through J-06, each with a non-empty Journey
  column naming its own ID
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-5-dev.md`

## TESTING REQUIREMENTS

- Browser: J-05 (steps 1, 3, 4, 5, 6, 7 live-testable; step 2 routed to fixture tests — see below;
  step 8 is a doc citation), J-06 (steps 1, 3, 4 live-testable; step 2 excluded per the carried
  blocker; step 5 is a doc citation). Required-still-passing: J-01, J-02, J-03, J-04.
- Unit/integration (targeted files ONLY, never the full suite): `test_manifest_invariants.py`,
  `test_ingest_finalize_compass.py`, `test_api_compass.py`, `test_compass.py`,
  `test_evidence_drawdown_memory_pressure.py`, `test_samples_memory_pressure.py`,
  `test_ingest_finalize_memory_pressure.py`, `test_start_backend_script.py`.
- Error cases: `POST /api/compass/regenerate` without the confirm parameter/flag is rejected (4xx),
  never mints a version; a malformed or non-existent `as_of` on `GET /api/compass` and on regenerate
  is rejected with a clear error, never a 500 or a silently-fabricated manifest; a memory-pressure
  test run WITHOUT `TRENDORA_MEMORY_PRESSURE` set touches zero DB files and completes as skips within
  seconds.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps to
at least one concrete scenario line, numbered sequentially:

- TC-1: given the three `*_memory_pressure` test modules currently always run and copy the live
  `data/trendora.db`, when pytest collects them WITHOUT `TRENDORA_MEMORY_PRESSURE` set, then all
  three (`test_evidence_drawdown_memory_pressure.py`, `test_samples_memory_pressure.py`,
  `test_ingest_finalize_memory_pressure.py`) report SKIPPED and complete within seconds with zero
  `shutil.copyfile`/`copy2` calls against `apps/backend/data/trendora.db`.
- TC-2: given `TRENDORA_MEMORY_PRESSURE=1` is set, when the same three modules plus
  `test_start_backend_script.py`'s three copy sites run, then each builds its scratch DB from a
  synthesized/subset fixture, never `shutil.copy*`ing the full 7.8 GB file.
- TC-3: given `apps/frontend/next.config.mjs` today has no worker/CPU bound (fans out 16-way), when
  the Constraint-(b) edit lands, then the config's worker-count setting reads ≤4, verifiable by
  reading the file and by a build log showing ≤4 worker processes.
- TC-4: given the J-01 deterministic-replay golden (`runs/goal-session-market-compass/journey-scripts/J-01.json`
  step 3) has produced the identical false FAIL twice on GRMN's two-line-wrapped "Consumer
  Discretionary" cell, when the replay matcher is repaired to compare the cell's own rendered text
  content (whitespace/newline-normalized) instead of a raw contiguous-string page scan, then a
  targeted replay of J-01 against the current, unchanged UI passes with no product code touched.
- TC-5: given `daily_prices`/`scanner_runs` currently max out at 2026-08-12 and the committed seed
  covers through the same date (RECONFIRM via `GET /api/health`'s `seed_latest_date` immediately
  before removing anything — never touch 2026-08-13/2026-08-14, proven offline-unrecoverable in
  iter-1), when the last two trading days' snapshots (2026-08-11, 2026-08-12, as of this writing) are
  removed and backfilled via `/data`, then the job completes "ok" with bar/snapshot counts restored,
  and the actual finalize-phase disclosure for 2026-08-12 (whether "next-session manifest" appears in
  the run's Refreshed line) is recorded verbatim in the dev handoff — expected to read
  "already exists, skipped" rather than "refreshed", because `next_session_manifests` already holds 5
  rows for 2026-08-12 that the append-only, skip-if-exists writer cannot overwrite.
- TC-6: given the live production DB's only possible frontier date (2026-08-12) already carries
  manifest rows and can therefore never mint a fresh version-1 `at_ingest`/`prospective_eligible: true`
  row again, when `test_manifest_invariants.py::test_tc20_baseline_is_eligible` and the
  `frontier_run`-fixture tests in the same file (e.g. `test_tc15_export_writer_never_rewrites_an_existing_artifact`,
  `test_tc18_no_later_bar_resolves_at_ingest_mode`) are run scoped (targeted `pytest` invocation, not
  the full suite) against their own isolated fixture DB, then they pass and are cited by name and
  file:line in the dev handoff as the flagship mechanism proof, with the burned-live-slot finding
  stated alongside so the evaluator does not expect a live-production screenshot of this specific fact.
- TC-7: given a sealed manifest exists (any version) for the frontier date, when the export file under
  the configured export directory is read and compared to the served `payload_json`, then the bytes
  are identical, and recomputing `manifest_hash` over the exported bytes (hash field excluded per the
  canonical rule) reproduces the embedded value.
- TC-8: given the manifest strip renders on `/` at the frontier as-of, when the page is loaded and its
  expanded table is inspected, then the stamps/counts match the newest stored manifest row for that
  date, and the candidate rows, comparison-cohort rows (count = member count − candidate count, each
  carrying `selection_disposition`), and near-threshold shadow rows match the stored manifest exactly.
- TC-9: given the backfill in TC-5 creates new `ScannerRun` rows for 2026-08-11/2026-08-12, when those
  rows and an older row created before this iteration's drill (e.g., the pre-drill 2026-08-11 row) are
  read, then the new rows carry a non-null `engine_identity` and the untouched older row's
  `engine_identity` reads NULL.
- TC-10: given manifest rows already exist for the frontier date, when the identical backfill range
  from TC-5 is re-run with zero new work, then no new manifest version is minted and the run log shows
  a zero-work/no-op outcome.
- TC-11: given a scanner_run date with NO existing manifest row (pick from outside this exact list,
  which already carries rows as of this writing: 1996-02-01, 2001-04-17, 2005-04-01, 2020-03-20,
  2022-06-15, 2025-04-15, 2026-03-30, 2026-03-31, 2026-04-01, 2026-07-23, 2026-08-05, 2026-08-10,
  2026-08-11, 2026-08-12), when `GET /api/compass?as_of=<that date>` is called, then exactly one
  `retrospective` manifest is created with `prospective_eligible: false` and a
  `generation.frontier_bar_date` later than its `as_of`, and a second identical GET mints no
  additional row.
- TC-12: given a manifest already exists for the frontier date, when a further seed-safe backfill runs
  on a DIFFERENT already-populated date (not the frontier's as_of), then the frontier manifest's
  stored payload bytes and version are unchanged, verified via both the API read and the export file.
- TC-13: given that manifest's underlying run is removed via seed-safe remove-data, when
  `GET /api/compass` is called for that as-of, then the manifest is still served (never a 404) with
  unchanged bytes, and the actual basis-disclosure text observed is recorded verbatim in the dev
  handoff — the literal "the underlying run is unavailable" wording is a carried owner-pending
  blocker (auditor finding B2, iter-3) and is explicitly NOT required to match this iteration.
- TC-14: given the removed range from TC-13 is backfilled back, when `GET /api/compass` is called
  again for that as-of, then the basis disclosure reflects availability (labeling the run "rebuilt" if
  its creation timestamp changed) while the manifest's stored bytes remain byte-identical to their
  pre-removal state.
- TC-15: given a manifest at version 1 for some as-of, when the confirm-gated
  `POST /api/compass/regenerate` action is triggered for that as-of, then a new version row is created
  with its own generation timestamp, its own `available_at_utc`, its own `manifest_hash`, and
  `prospective_eligible: false` even where its computed mode is `at_ingest`; the prior version(s)
  remain byte-identical and readable with their `prospective_eligible` flags unchanged; and `/`'s
  manifest strip lists all versions with their stamps.
- TC-16: given J-01 through J-04 are unmodified by this iteration's changes, when each is re-verified
  via browser-qa against the post-drill data state, then all four still report passing with no value
  drift versus their last-passing evidence.
- TC-17: given `demo.sh market-compass --session-live` runs as part of this full-depth iteration, when
  the walkthrough capture completes, then `[NEW]`-flagged recordings exist for J-01, J-02, J-03,
  J-04, J-05, and J-06, each with a non-empty Journey column naming its own ID (not the
  empty-Journey-column defect noted in the iter-3 assumption log).
- TC-18: given a copied export file, when one byte is flipped (including inside
  `prospective_eligible` or a provenance field) and `manifest_hash` verification runs over the copy,
  then verification fails, confirming tamper detection (AG-12).
- TC-19: given the dev handoff is written at `docs/handoffs/goal-market-compass-iter-5-dev.md`, when
  it is read, then it cites: the Constraint (a)/(b) changes, the J-01 golden fix, the burned-frontier-
  slot finding with exact row evidence, the fixture-test names satisfying J-05's flagship mechanism
  proof, the J-06 named tests' scoped pass results, and the J-06-step-2 known-limitation citation.
- TC-20: given `/api/dashboard`, `/api/stocks`, and `/api/market-phase` are read for as_of=2026-08-11
  and as_of=2026-08-12 BEFORE the TC-5 remove+backfill and again AFTER, when the two snapshots are
  compared, then all three endpoints' served values are byte-identical pre- vs. post-drill, proving
  the drill is a pure reprocess of the same seed bars, not a data-altering event.

## NOTES

**Host-safety operating rules for this iteration (binding):**
- Do not run the full pytest suite; run ONLY the files named in TESTING REQUIREMENTS.
- Do not set `TRENDORA_MEMORY_PRESSURE=1` this iteration — the three memory-pressure files must be
  exercised only for their skip behavior (TC-1), never their heavy path.
- Apply Constraint (b) (`next.config.mjs` ≤4 workers) BEFORE any `next build` runs this iteration.
- Where the pipeline mechanics allow it, avoid running two backends longer than necessary — stop the
  dev-cycle backend before browser-qa starts its own fresh one (this is also standing best practice
  per iter-1's stale-backend lesson) rather than leaving both live simultaneously.
- Before starting the drill, check available host memory/headroom; a second, independent goal-mode
  engine may still be active on this host (it froze the machine once already today via memory
  overcommit). If headroom looks thin, prefer the lightest viable path — the fixture-scoped tests plus
  whichever live steps do not require two concurrent backends — and note the deferral rather than
  forcing the rest through.
- Do not re-tune `cache_size`/`pool_size`/`max_overflow`/`memory_cap_mb`/`malloc_arena_max` (binding
  "Do not redo"). Do not re-run the ~31-minute VmPeak drill; do not re-measure J-09 (binding
  "Do not redo" — no lever changed this iteration).

**On the depth-divergence risk (lesson, iter-2):** if the engine dispatches this iteration at
anything other than `full`, the evaluator should treat that divergence itself as an ESCALATE-class
signal (per the standing lesson), not a silent downgrade — the auditor and demo lanes are load-bearing
for this scope (walkthrough make-up, AG-12 re-confirmation).

**Assumption logged:** `runs/goal-session-market-compass/state/assumptions.md` carries this
iteration's entry on the burned-frontier-slot finding and the choice to route the flagship proof to
fixture tests rather than a forced/authorized live-production workaround.

**Risk to watch, not fixed here:** the demo/walkthrough tool has previously produced an empty Journey
column for an entire run (assumption-ledger iter-3 note) — if the same defect recurs, the evaluator
should treat the walkthrough gap as a tooling defect, not evidence the underlying journeys regressed.
