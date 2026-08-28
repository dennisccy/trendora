# Goal Iteration 26 — Make up the J-05/J-06 freeze/immutability pair for real, safely

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 26
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — structural/cross-cutting: this iteration must prove one contract (manifest
  freeze + immutability) across the ingest-finalize hook, the writer/reader in `compass.py`, the
  `GET /api/compass` + `POST /api/compass/regenerate` routes, and the existing frontend manifest
  strip — none of these interactions is covered end-to-end by any single journey's own fixture
  suite, and this is the first LIVE write to the canonical `next_session_manifests` table this
  session outside J-11's already-closed recovery work.
- **Frontend Present:** no (existing manifest-strip UI is exercised, not changed)
- **Target journeys:** J-05, J-06
- **Required-still-passing journeys:** J-01, J-04, J-10, J-11
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; the manifest for close D derives only from state stored at or before D; never introduce lookahead anywhere. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local provider fixtures — no live external network calls or paid data services without an explicit goal.md amendment. *(critical)* — its J-10 recovery exception for 2026-08-11/2026-08-12 is EXHAUSTED; any later live fetch of those two dates needs a new dated amendment.
  - **AG-10 — Host resource ceiling:** heavy compute MUST be launched only via the project launch scripts, which MUST apply the host caps. Never remove, weaken, or bypass these caps. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change; corrections happen only as new version rows; a historical view never substitutes a newer manifest. *(critical)*
  - **AG-17 — Repair never rewrites provenance:** `prospective_eligible` is never upgraded merely because historical data was later repaired; artifacts produced while the database was known to be damaged remain marked unusable as prospective/out-of-sample evidence. *(critical)*
  - **AG-18 — The authorized manifest migration preserves everything:** no manifest may be regenerated, rebound, rehashed, upgraded, deleted, or newly minted outside the explicit J-11 migration authorization; a changed stored value is a REGRESSION, never a note. *(critical)*

## GOAL

Move J-05 ("each close freezes one provenance-stamped next-session manifest, exported
byte-consistently") and J-06 ("a frozen manifest never changes") from `partial` toward `passing` by
closing the concrete gaps left open since iter-3 — a false-positive test regression, a missing
export byte-equality proof, missing API-level removed-run/basis coverage — and by producing real,
safe browser-qa evidence for the manifest strip and the confirm-gated regenerate action, without
repeating the destructive remove+backfill drill that caused this session's core incident at iter-5.

## BACKGROUND

The evaluator's iter-25 verdict (CONTINUE, depth recommendation `full`) explicitly names J-05+J-06 as
the next build, at full depth, because "frozen records never changing... is the most dangerous area
in this goal" — this spec follows that binding recommendation. Per `journey-history.json`, both
journeys have been stuck `partial` since `iter-3`: the engine, schema, routes, and frontend manifest
strip are already built (86/87 relevant fixture tests pass today — I ran
`test_manifest_invariants.py test_ingest_finalize_compass.py test_api_compass.py test_compass.py`
myself), but iter-3's evaluator found no browser-qa evidence for either journey (`UT-J-05`/`UT-J-06`
never executed) plus three concrete gaps: (B1, already fixed) an export-overwrite bug; (B2) an
unresolved question about whether the "underlying run unavailable" basis state is reachable; (B3) no
automated export-byte-equality test. Those gaps were never revisited because the iter-5 QA drill for
this exact make-up work is what triggered the incident that consumed iterations 5-25 (J-09/J-10/J-11).

**Applying the iter-19/iter-20 lesson** ("re-derive a goal.md factual premise from the code before
treating it as a requirement to satisfy literally"): J-05 step 1's "remove the last two trading days
... (seed-safe)" premise, read literally today, resolves to 2026-08-11/2026-08-12 — the exact pair
whose removal caused the incident, and whose AG-9 recovery exception is now exhausted. I verified this
independently (frontier still 2026-08-12 in both `daily_prices` and `scanner_runs`; `remove_data()`
structurally can only ever target non-seed, post-2026-07-01 dates, so there is no other reading of
"the last two trading days"). This iteration therefore does NOT call `remove_data()` /
`clear_snapshot_dates()` / any backfill against the canonical database — see the assumption ledger
entry (`iter-26 — goal-decomposer`) for the full reasoning. The destructive-drill portions of J-05/J-06
are instead proven against the existing isolated-engine fixture suite (mirroring the iter-5
decomposer's own precedent of routing the at-ingest "burned slot" proof to fixtures), while real,
safe, additive-only live evidence comes from the manifest strip UI (read-only) and the confirm-gated
`POST /api/compass/regenerate` action (an authorized, AG-12-safe INSERT-only feature, unrelated to the
removal machinery that caused the incident) on `as_of=2025-04-15` — a clean retrospective manifest
with zero incident-window contact.

The one genuine, already-live test regression I found this iteration (not previously known):
`test_tc15_no_update_statement_targets_next_session_manifests` currently FAILS — its AST scanner flags
any `.update()` attribute call in a module that merely mentions `next_session_manifests`/
`NextSessionManifest` in text, which now false-positives on `hashlib.digest.update()` and
`dict.update()` calls inside the J-11 stage modules (`j11_disposable_clone.py`, `j11_stage_d.py`,
`j11_stage_g_verify.py`). This directly blocks J-06's own "no code path UPDATEs a manifest row" test
citation and is fixed in scope below.

## IN SCOPE

### Backend
- [ ] Narrow `test_tc15_no_update_statement_targets_next_session_manifests`'s AST scanner
      (`apps/backend/tests/test_manifest_invariants.py`) so it flags only a genuine SQLAlchemy
      Update-statement / ORM bulk-update call reachable against `NextSessionManifest` /
      `next_session_manifests`, not any `.update()` attribute call on an unrelated object (dict,
      hashlib digest) — re-run the test and confirm it both passes clean today AND still fails if a
      real `session.execute(update(NextSessionManifest)...)` call is temporarily introduced as a
      mutation-kills-it check.
- [ ] Add the missing automated export-byte-equality test (audit finding B3, iter-3): stored
      `payload_json` bytes equal the on-disk export file's bytes, and recomputing `manifest_hash` over
      the exported bytes (with the `manifest_hash` field excluded per the canonical rule) reproduces
      the embedded value — fixture-scoped (isolated engine), never against the canonical database.
- [ ] Add API-level (not just `basis_disclosure()` unit-level) fixture coverage: `GET /api/compass`
      for an `as_of` whose source `ScannerRun` has been removed returns 200 with `basis.status ==
      "unavailable"` (never 404, never a recompute), and after the run is restored with a different
      `created_at`, the same endpoint returns `basis.status == "rebuilt"` while the manifest's
      `payload_json`/`version` are unchanged — extend only if the current suite does not already
      isolate this exact route-level scenario (cite what already exists rather than duplicating it).
- [ ] Confirm and cite (do not rebuild) the existing fixture coverage for: the at-ingest flagship
      freeze (`mode=at_ingest`, `version=1`, `frozen=true`, `prospective_eligible=true`,
      `producer=ingest_finalize`, well-formed `available_at_utc`) versus a same-loop historical date
      resolving `mode=retrospective`/`prospective_eligible=false`; create-once idempotency on a
      repeated identical backfill; the retrospective-manifest create-once-on-GET path; schema
      conformance for both manifest kinds; and "an unrelated backfill elsewhere leaves a stored
      manifest's bytes/version unchanged" — list exact test names and pass counts in the dev handoff.
- [ ] Investigate (read-only) the four orphaned export files with no matching live
      `next_session_manifests` row (`2024-06-08_v1.json`, `2024-07-01_v1.json`, `2024-07-08_v1.json`,
      `2024-08-01_v1.json` under `apps/backend/data/exports/next_session_manifests/`) and record the
      honest finding in the dev handoff — leftover artifact from a prior DB state, versus a real AG-12
      concern. Never delete these files as part of this investigation.

### Live, safe, canonical-database verification (no code change — evidence-gathering)
- [ ] Read-only: `GET /api/compass?as_of=2026-08-12` (version 6, the current `at_ingest` row) served
      stamps + hashes match its on-disk export `2026-08-12_v6.json` byte-for-byte; recompute
      `manifest_hash` over the exported bytes and confirm it matches the embedded value.
- [ ] Read-only: load `/` with `?asof=2025-04-15`, open the manifest strip; confirm every badge/hash
      chip/dataset stamp/universe count equals `GET /api/compass?as_of=2025-04-15` verbatim, and the
      expanded audit table's comparison-cohort row count equals `universe.member_count` minus
      candidate count.
- [ ] One additive live write, explicitly bounded: trigger the confirm-gated "Regenerate manifest"
      control for `as_of=2025-04-15` (`POST /api/compass/regenerate`), producing version 2; confirm
      version 1's stored `payload_json`/`content_hash`/`manifest_hash`/`prospective_eligible` are
      byte-identical to their pre-regenerate values, and the manifest strip UI lists both versions.
- [ ] Before/after spot-check (dev handoff): `daily_prices` row count, `scanner_runs` row count, and
      `next_session_manifests` row count for every `as_of` OTHER than 2025-04-15 are identical before
      and after this iteration — the ONLY canonical-DB row this iteration adds is the single
      `next_session_manifests` version-2 row for `as_of=2025-04-15`.

### New user-facing capability
None — the manifest strip and regenerate control already exist; this iteration proves their
correctness with real evidence and closes two backend test gaps.

### New information displayed
None.

### New user actions
None — the confirm-gated regenerate control already exists; this iteration exercises it live for the
first time this session on a safe, non-incident date.

### UI surface changes
None.

### Product surface delta
None visible to a new user; this iteration is proof-and-fix work on an already-built surface.

### Blueprint conformance
J-05/J-06 live entirely under the existing **Today (`/`)** home — specifically the manifest strip row
already registered in `blueprint.md`'s Feature/journey homes table. No new page, no new nav entry.

### Data-contract additions
None — this iteration reads/verifies already-registered Data Contract rows ("Next-session manifest —
CONTENT block" and "— FREEZE/INTEGRITY block") and their already-registered computing module
(`app.engine.compass.build_manifest_payload` / `basis_disclosure`) and serving endpoints
(`GET /api/compass`, `POST /api/compass/regenerate`). No second producer or second endpoint is
introduced.

## OUT OF SCOPE

- Any `remove_data()` / `clear_snapshot_dates()` / backfill call against the canonical
  `apps/backend/data/trendora.db` (see BACKGROUND + assumption ledger — this is the deliberate,
  safety-motivated deviation from J-05 step 1 / J-06 steps 1-3's literal live-drill wording).
- Any write, removal, or fetch touching 2026-08-05, 2026-08-10, 2026-08-11, or 2026-08-12's
  `daily_prices`/`scanner_runs` rows (read-only GETs against these dates' already-stored data are
  fine and used above).
- Building any new drill-isolation infrastructure (disposable clone, sandbox DB, transaction
  rollback) — the goal's own "Destructive-drill isolation" constraint reserves this for a future cycle.
- J-07 / J-08 (the Today/Market page split, sidebar rename, `/market` route) — explicitly the next
  pair after this one per the goal file's own build order; no page-split or sidebar work this
  iteration.
- Re-opening J-11's recovery or serving verification (binding "Do not redo").
- Re-arming `CHAIN_MAINTENANCE_ISOLATION` or `CHAIN_REQUIRE_FULL_DEPTH`, or writing a
  `Depth enforcement:` line into this spec (operator-only; standing guidance keeps both off).
- Resolving the five older open owner questions (J-09's ~2.99 GB acceptability, J-01's weak golden
  script, etc.) — carried as-is, non-blocking.

## DEFINITION OF DONE

- [ ] `test_tc15_no_update_statement_targets_next_session_manifests` passes with the narrowed scanner,
      and a mutation check confirms it still catches a real UPDATE call (TC-1)
- [ ] A new automated export-byte-equality + `manifest_hash`-recompute fixture test passes (TC-2)
- [ ] The existing fixture suite's at-ingest-flagship and retrospective-mode coverage is cited by exact
      test name in the dev handoff, re-run green (TC-3, TC-4)
- [ ] Manifest strip renders `as_of=2025-04-15`'s stamps/counts/audit table matching
      `GET /api/compass` verbatim, verified live (TC-5)
- [ ] Confirm-gated regenerate mints version 2 for `as_of=2025-04-15` live; version 1 stays
      byte-identical; UI lists both versions (TC-6)
- [ ] "Unrelated backfill leaves an unrelated manifest unchanged" is cited or newly covered at the
      fixture level (TC-7)
- [ ] New API-level fixture tests prove `GET /api/compass` never 404s and reads `basis.status` correctly
      across removed-run / restored-run states (TC-8, TC-9)
- [ ] The four orphaned export files are investigated and the finding is recorded, not silently ignored
      or deleted (TC-10)
- [ ] Required-still-passing journeys J-01, J-04, J-10, J-11 remain green (deterministic replay + LLM
      fallback) (TC-11)
- [ ] Canonical-database row counts are identical before/after except the one authorized
      `next_session_manifests` version-2 insert for `as_of=2025-04-15` (TC-12)
- [ ] No anti-goal violation introduced (AG-9, AG-12, AG-17, AG-18 specifically re-checked)
- [ ] Unit tests pass; zero new regressions beyond the one fixed this iteration
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-26-dev.md`

## TESTING REQUIREMENTS

- Browser: J-05, J-06 (manifest strip render + regenerate-to-v2 on `as_of=2025-04-15`); regression
  replay for J-01, J-04, J-10, J-11
- Unit/integration: `apps/backend/tests/test_manifest_invariants.py`,
  `test_ingest_finalize_compass.py`, `test_api_compass.py`, `test_compass.py`, `test_session_delta.py`
  — all green, citing exact counts before/after in the dev handoff
- Error cases: `GET /api/compass` for a removed-run `as_of` never 404s (returns 200 with
  `basis.status=="unavailable"`); malformed/absent `generation_json` still returns `"unverifiable"`,
  never a 500; `POST /api/compass/regenerate` without the confirm flag returns an honest 4xx (already
  tested — cite it); regenerate on an `as_of` with no existing manifest returns an honest 404 (already
  tested — cite it, not exercised live this iteration)

Test-first contract:

- TC-1: given `test_tc15_no_update_statement_targets_next_session_manifests`'s current false-positive
  failure on `j11_disposable_clone.py`/`j11_stage_d.py`/`j11_stage_g_verify.py`'s dict/hashlib
  `.update()` calls, when the AST scanner is narrowed to real SQLAlchemy update targets, then the test
  passes with zero offenders reported for those three files, and a temporarily-injected
  `session.execute(update(NextSessionManifest)...)` call still trips the same test to failing.
- TC-2: given the live export file `apps/backend/data/exports/next_session_manifests/2026-08-12_v6.json`
  and its DB row's `payload_json`, when a new fixture test performs the same byte-for-byte comparison
  and `manifest_hash` recomputation pattern against an isolated-engine-produced manifest, then both the
  fixture test and the live read-only spot-check (cited in the dev handoff) confirm byte equality and
  hash reproduction.
- TC-3: given an isolated fixture DB with a frontier `ScannerRun` processed with
  `producer="ingest_finalize"`, when `compass.get_or_create_manifest` freezes it, then the stored row
  has `mode="at_ingest"`, `version=1`, `frozen=true`, `prospective_eligible=true`, and a well-formed
  `available_at_utc` not earlier than `generated_at + availability_margin_seconds`.
- TC-4: given the same isolated fixture DB with a second, non-frontier historical `ScannerRun`
  processed in the same finalize loop, when its manifest is created, then `mode="retrospective"` and
  `prospective_eligible=false`.
- TC-5: given the canonical database's stored `as_of=2025-04-15, version=1` manifest (`retrospective`,
  frozen, zero incident-window contact), when `/` is loaded with `?asof=2025-04-15` and the manifest
  strip's audit-table disclosure is opened, then every rendered badge/hash chip/dataset stamp/universe
  count equals `GET /api/compass?as_of=2025-04-15` verbatim, and the comparison-cohort row count equals
  `universe.member_count` minus candidate count.
- TC-6: given the same `as_of=2025-04-15` manifest at version 1, when the confirm-gated "Regenerate
  manifest" control is triggered live against the canonical database, then `POST
  /api/compass/regenerate?as_of=2025-04-15` mints a `version=2` row, version 1's
  `payload_json`/`content_hash`/`manifest_hash`/`prospective_eligible` read back byte-identical to
  their pre-regenerate values, and the manifest strip UI lists both versions with their own stamps.
- TC-7: given an isolated fixture DB with a stored, frozen manifest and a separate historical date
  backfilled afterward, when the stored manifest is re-read, then its `payload_json` bytes and
  `version` are byte-identical to their pre-backfill values — cited from existing coverage or newly
  isolated if the exact "another date's backfill" scenario is not already its own assertion.
- TC-8: given an isolated fixture DB where the `ScannerRun` a manifest's `source_run_created_at`
  points to has been removed, when `GET /api/compass?as_of=<that date>` is called, then the response
  is HTTP 200 (never 404) serving the manifest's payload unchanged, with `basis.status=="unavailable"`.
- TC-9: given the same fixture DB with that `ScannerRun` restored under a different `created_at`, when
  `GET /api/compass` is re-read, then `basis.status=="rebuilt"` and the manifest's
  `payload_json`/`version` remain unchanged from TC-8.
- TC-10: given the four orphaned export files with no matching live `next_session_manifests` row, when
  the developer reconciles them against AG-12, then the dev handoff records an explicit finding
  (leftover artifact from a prior DB state, or a real violation requiring escalation) — never silently
  ignored or deleted.
- TC-11: given J-01, J-04, J-10, J-11's stored golden scripts (or LLM browser-qa fallback where no
  golden is on file), when the regression replay lane runs this iteration, then all four report PASS
  with no regression.
- TC-12: given a `sqlite3` row-count read of `daily_prices`/`scanner_runs`/`next_session_manifests`
  taken before this iteration's canonical-DB actions and again after, when compared, then every count
  is identical except `next_session_manifests` gaining exactly one row (`as_of=2025-04-15, version=2`).

## NOTES

- Applies the iter-19/iter-20 lesson (re-derive a goal.md factual premise from the current code/data
  before treating it as literally executable) to J-05 step 1's "last two trading days" wording — see
  BACKGROUND and the `iter-26 — goal-decomposer` assumption-ledger entry for the full reasoning and the
  reversibility statement.
- Item 3 of the pump coordinator note (replay-lane parser trap): `Target journeys:` and
  `Required-still-passing journeys:` above are each kept on one physical line with their `J-NN` tokens
  on that same line, per the label's-own-bullet-is-authoritative fix.
- Standing guidance (memory + pump note): `CHAIN_MAINTENANCE_ISOLATION` and `CHAIN_REQUIRE_FULL_DEPTH`
  stay OFF; this spec does not request either, and does not self-grant `Depth enforcement:`. If the
  human operator judges the one live-write action (TC-6) warrants stronger isolation than the default
  full-depth pipeline provides, that is their call to add, not this spec's.
- The developer should re-verify (not merely re-cite) the iter-3 audit finding B2 ("opening the page
  quietly rebuilds a deleted run's data before the basis check can see it is gone") against CURRENT
  code before treating it as resolved-by-code-change or still-open — much has changed in the self-heal
  paths since iter-3 (iter-18/iter-21 lessons); TC-8/TC-9 are the fixture-level proof either way.
- The `test_tc15_no_update_statement_targets_next_session_manifests` failure found this iteration was
  NOT flagged by any prior evaluator — a fresh finding, not a known regression being re-litigated.
