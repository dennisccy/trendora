# Goal Iteration 10 — J-11 Stages B/B1/B2: pre-reset inventory, manifest↔run schema reconciliation, frozen attempt identity

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 10
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — structural/cross-cutting: Stage B1's manifest↔ScannerRun schema-contract reconciliation and Stage B2's attempt-identity invariant touch ≥3 modules whose interaction is not covered by any single existing test (`app/models.py` field contract, `app/db.py` pragma/schema-creation path, `app/engine/compass.py` `basis_disclosure`/`get_or_create_manifest`, plus the fixture-DB test harness pattern from `test_manifest_invariants.py`) — and it is the evaluator's binding depth recommendation for this iteration.
- **Frontend Present:** no
- **Target journeys:** J-11
- **Required-still-passing journeys:** none — see BACKGROUND (Loop-mechanics lane gate)
- **Anti-goal reminders:**
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; the manifest for close D derives only from state stored at or before D; never introduce lookahead anywhere. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local provider fixtures — no live external network calls or paid data services without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection), carried from ops-hardening:** heavy compute MUST be launched only via the project launch scripts, which MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env` whenever present (CPU-affinity mask, BLAS/OMP thread caps) plus the `config.yaml` `server.memory_cap_mb` / `malloc_arena_max` values. Never remove, weaken, or bypass these caps; stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless of test outcomes. The ceiling VALUES are an owner-set envelope (current: `memory_cap_mb` 8192, `HOST_GUARD_MEMORY_HIGH` 12G, per the dated owner amendments recorded in `docs/archive/goal-ops-hardening.md`); only the owner may change them. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change; corrections happen only as new version rows; a historical view never substitutes a newer manifest. *(critical)*
  - **AG-17 — Repair never rewrites provenance (owner, 2026-08-20):** restoring deleted historical data MUST NOT retroactively change research provenance. A manifest that was retrospective or ineligible stays that way; **`prospective_eligible` is never upgraded merely because historical data was later repaired**; `available_at_utc`, manifest versions, `content_hash`/`manifest_hash`, and prior eligibility classifications remain immutable (AG-12 governs the rows and files themselves). Any manifest or artifact produced while the database was known to be damaged — everything dated from the iter-5 drill until **J-11 Stage G** passes (owner, 2026-08-21: extended from "J-10's post-recovery verification", because after J-10 the raw layer is repaired but the derived state is still knowingly pending J-11 normalization) — **remains marked unusable as prospective/out-of-sample evidence**; nothing is retroactively marked prospective merely because raw bars were repaired in J-10 or derived snapshots were regenerated in J-11 — historical causality is unchanged by either; only a separately regenerated artifact, minted after verified recovery under the existing create-once and version rules, may carry eligibility, and it remains subject to the same version and `prospective_eligible` contract as any other artifact. The incident record itself is evidence: the iter-5 drill result, its handoff, the reviewer/QA evidence already produced, and the explicit statement that the committed seed could not restore these dates MUST NOT be deleted, rewritten, or silently superseded. Repairing the database never rewrites historical causality. *(critical)*

## GOAL

Prove — with fixture tests and a read-only, byte-verified inventory of the live database — the three preconditions `docs/goal.md` requires before J-11's destructive derived-state clear may begin: a frozen pre-reset snapshot of everything the reset touches or must leave untouched, a manifest↔`ScannerRun` schema contract that survives a rebuilt/reused-id source run without relying on SQLite's disabled FK enforcement, and one frozen engine/config identity that the next iteration's regeneration attempt must be checked against.

## BACKGROUND

J-11 is the only actionable journey (iteration-state "Active blockers": J-10's raw layer is repaired — 585/587, `passing` — and every other product/research/browser lane stays shut under `docs/goal.md` Loop-mechanics until J-11 Stage G passes). J-11 itself is staged A→G by the owner, with an explicit hard gate: "Stage C may not begin until all six of [Stage B1's] items are proven," and Stage B/B2 (pre-reset inventory, frozen attempt identity) are their own precondition artifacts, not part of the destructive retry unit ("the unit of work is the whole 11-date set," scoped to Stage C onward). Splitting the journey at this exact boundary — B/B1/B2 (read-only + fixture-DB + model-declaration work, zero writes to `trendora.db`) this iteration, C→G (the real clear/regenerate/repair/cache-invalidate/verify, needing a single controlled writer with no boot warmup, browser QA, replay lane, or second backend) in a later one — mirrors how J-10 itself was safely chunked across iterations 7/8/9, keeps this iteration to one risk class, and is exactly what Stage C's own precondition demands regardless of how later work is chunked. This choice is logged to the assumption ledger (iter-10 entry) since `docs/goal.md` does not explicitly state stages B/B1/B2 must ship with C-G.

**Depth is full** — the evaluator's recommendation is binding, and it is independently justified (trigger 1): Stage B1 requires a contract that spans `app/models.py`, `app/db.py`, and `app/engine/compass.py`, verified by tests using the same isolated-fixture-DB pattern as `test_manifest_invariants.py`, plus a live read-only inventory of production `trendora.db`.

**Two lessons apply directly and must shape execution, not just be noted:**
- iters 6 and 8 (`lessons.md`): a `docs/goal.md`-declared lane gate is prose the pipeline has never mechanically enforced, and the forbidden browser/replay lane fired at full depth TWICE, once inside a re-dispatch explicitly commissioned to add missing review. The iter-8 lesson names this exact iteration by scope: "Applies to: ... all of J-11." **This iteration must not boot the application services and must not run the browser-qa or deterministic-replay lane at all** — `docs/goal.md` Loop-mechanics forbids any such lane, unconditionally, until J-11 Stage G passes; that gate does not depend on whether an iteration happens to write to the database (this one doesn't). Per goal-decomposer policy I do not self-declare `Maintenance isolation: required` in this spec (anti-pattern 25) — the human dispatcher should consider setting `CHAIN_MAINTENANCE_ISOLATION` for this run given the session's two prior recurrences of exactly this failure mode.
- iter-7 and iter-9 (`lessons.md`): a fail-closed gate proven only against complete fixtures silently agrees on an empty/degenerate input, and a population-wide "all N were X" claim is exactly where the one real counter-example hides. Both bite directly on Stage B1/B2's tests below: the FK-reconciliation tests must include the **degenerate case** a real incident already produced (2026-08-05 has 2 manifests with **zero** surviving source runs — an orphan, not merely a rebuilt one), and the attempt-identity invariant test must assert **per-run**, not just an aggregate "all matched" flag, exactly mirroring iter-9's AVB counter-example.

## IN SCOPE

### Backend

- [ ] `app/models.py`: on `NextSessionManifest.source_run_id`, drop the `foreign_key="scanner_runs.id"` declaration (model-declaration change only — no live-DB migration; `.claude/project-template.md` STACK confirms schema evolves only via additive `ALTER TABLE`/add-column, never destructively, so this cannot and must not attempt to rewrite the already-created live table). Add a code comment stating verbatim the "Intended end state" contract from `docs/goal.md` J-11 step 11: `source_run_id` is immutable historical provenance, never a durable live foreign-key identity, and is never used alone to prove current-run identity after a delete/rebuild — reconciliation is by `as_of` + `source_run_created_at` + frozen engine identity, and `basis_disclosure` already does this correctly and needs no change.
- [ ] New module `app/engine/j11_maintenance.py`: (a) `capture_pre_reset_inventory(session)` — Stage B — a read-only, column-projected query set producing: the exact 11 incident-date list; per-date row counts for `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`, `forward_returns`; `daily_prices` total row count + date range + a cheap SQL-side aggregate fingerprint (never a full ORM hydration of the 3.3M-row table — AG-8); manifest count + `content_hash`/`manifest_hash` list for the 4 incident dates carrying manifests; `data_provider_runs` row count; the certified-claims ledger file's sha256; the staging ledger file's sha256; `watchlist` row count. (b) `freeze_attempt_identity(session, cfg)` — Stage B2 — computes the current `app.engine.engine_identity` value plus the relevant config subset hash and returns them as a single frozen record. (c) `check_attempt_identity_consistency(frozen_identity, run_identity) -> bool` — the pure invariant helper Stage D will call per rebuilt run; no aggregate-only form (iter-9 lesson).
- [ ] New script `apps/backend/scripts/run_j11_pre_reset_inventory.py`: read-only CLI wrapping (a)+(b) above against the live `apps/backend/data/trendora.db` via the existing `app.db` session helpers (never a raw file copy); writes `runs/goal-market-compass-iter-10/j11-pre-reset-inventory.json` and `runs/goal-market-compass-iter-10/j11-frozen-identity.json`; asserts before/after `daily_prices` row count and fingerprint are unchanged by its own run (proving the capture step itself performed zero writes) and logs that assertion into the artifact.
- [ ] New tests `apps/backend/tests/test_j11_maintenance.py`, each against an isolated fixture DB built the same way `test_manifest_invariants.py` builds one (never the live 7.8 GB DB — the memory-pressure/copy-site rule in `docs/goal.md` Constraints already forbids copying it): (a) fresh DB with `PRAGMA foreign_keys=ON` explicitly issued, insert a `ScannerRun` + a `NextSessionManifest` referencing it, delete the `ScannerRun`, assert no FK violation and the manifest row is untouched; (b) same fixture, recreate the deleted run's `as_of` as a NEW `ScannerRun` row, assert `basis_disclosure` reports the rebuilt/unavailable-then-rebuilt state via `as_of` + `source_run_created_at` comparison and that `source_run_id`, both hashes, `version`, `available_at_utc`, `prospective_eligible` are unchanged on the manifest; (c) the **degenerate case** (iter-7 lesson): a manifest whose source run has been deleted with **no** replacement run created for that `as_of` at all — assert `basis_disclosure` reports the honest "underlying run unavailable" state, never a fabricated rebuilt/available state, and never raises; (d) the id-reuse trap named in `docs/goal.md` (mint manifest from run id N at T1, delete, recreate reusing numeric id N at a later T2), assert `basis_disclosure` reports `rebuilt` because `source_run_created_at != current_run.created_at` even though `source_run_id == N` unchanged in both directions; (e) `check_attempt_identity_consistency` unit tests: one run matching the frozen identity (consistent), one run with a **different** identity (iter-9 lesson — assert this specific mismatched case fails, not just an aggregate count).
- [ ] Dev handoff cites, from the produced inventory artifact and the fixture test run: the captured 11-date row counts, the manifest/hash list, and confirmation (mtime + fingerprint) that `apps/backend/data/trendora.db` received zero writes during this iteration.

### Frontend

None — this iteration has no UI surface (J-11's walkthrough is waived by `docs/goal.md`).

### New user-facing capability

None this iteration — Stages B/B1/B2 are read-only inventory capture, a schema-contract clarification, and a frozen-identity precondition; no UI, no served field, no user action changes.

### New information displayed

None.

### New user actions

None.

### UI surface changes

None.

### Product surface delta

None — purely internal maintenance/precondition work; no served endpoint, page, or displayed value changes for any journey this iteration.

### Blueprint conformance

No new surfaces; no edit to `runs/goal-session-market-compass/state/blueprint.md` this iteration (its J-05/J-06 manifest rows already register the Next-session manifest's FREEZE/INTEGRITY block and are unaffected — `source_run_id` stays internal provenance, never a displayed field).

### Data-contract additions

None.

## OUT OF SCOPE

- J-11 Stages C, D, E, F, G — the bounded derived-state clear, canonical regeneration of the 11 dates, forward-return hole repair, cache invalidation, and final verification. Deferred to a later iteration; that iteration will need a single controlled writer with no boot warmup, no browser QA, no replay lane, and no second backend/frontend (the human dispatcher decides the mechanical control for that).
- Any live network fetch of any kind — the J-10 AG-9 exception is exhausted; normal AG-9 applies.
- Any change to `daily_prices` row values, `next_session_manifests` row values, `data_provider_runs`, the certified-claims or staging ledgers, `watchlist`, or any other audit/user-state table.
- Any browser-QA run, deterministic-replay run, or booting the backend/frontend application services (Loop-mechanics gate; see BACKGROUND).
- Reopening J-10 (585/587 restored; EA/EQR unrestorable for evidenced external reasons — do not re-fetch, do not widen).
- Any change to `scanner.snapshot_cadence`, selection/scoring thresholds, or research logic.
- The five older non-blocking owner questions (J-09's 3.44 GB; J-06 "underlying run unavailable" wording; J-01 test-step rewording; empty next-session-focus; whether MNST joins the recovery list) — still open, still not this iteration's job.
- Touching AVB's dollar-volume scaling (`scoring._avg_dollar_volume`, `universe_resolver._adv_dollar`) — a Stage D/G concern once regeneration actually runs, not this iteration's.

## DEFINITION OF DONE

- [ ] Stage B pre-reset inventory artifact produced and its `daily_prices` figures independently re-verified read-only against the live database (TC-1, TC-2)
- [ ] Stage B1's six schema-contract acceptance items are each proven by a named fixture-DB test, including the degenerate no-source-run case and the id-reuse case (TC-3, TC-4, TC-5, TC-6)
- [ ] Stage B2 frozen engine/config identity is captured to an artifact and its invariant-checking helper is proven both for a matching run and a mismatched run (TC-7)
- [ ] `apps/backend/data/trendora.db` received zero writes during this iteration (TC-8)
- [ ] `runs/goal-market-compass-iter-10/depth-dispatched` reads `full`, matching this spec's `Depth: full` (TC-9)
- [ ] No browser-QA lane and no deterministic-replay lane executed; J-01, J-02, J-03, J-04, J-10 all keep their currently recorded status unchanged (TC-10)
- [ ] Unit tests pass; no regressions in `test_manifest_invariants.py` or `test_j10_recovery.py`
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-10-dev.md`

## TESTING REQUIREMENTS

- Browser: none — J-11's walkthrough is waived; no browser-QA lane runs this iteration (Loop-mechanics gate).
- Unit/integration: `apps/backend/tests/test_j11_maintenance.py` (new, fixture-DB only); `apps/backend/scripts/run_j11_pre_reset_inventory.py` exercised once read-only against the live DB with before/after zero-write proof; existing `test_manifest_invariants.py` and `test_j10_recovery.py` re-run unmodified to confirm no regression.
- Error cases: the degenerate orphaned-manifest case (no surviving source run at all) must not raise and must not report a fabricated "available"/"rebuilt" state; a mismatched-identity run must be rejected by `check_attempt_identity_consistency`, not silently accepted.

Test-first contract:

- TC-1: given the live `apps/backend/data/trendora.db` in its current post-J-10 state (585/587 symbols restored on 2026-08-11/12), when `run_j11_pre_reset_inventory.py` runs read-only, then it writes `runs/goal-market-compass-iter-10/j11-pre-reset-inventory.json` containing the 11 incident-date row counts for `scanner_runs`/`scanner_results`/`sector_scores`/`theme_scores`/`forward_returns`, the `daily_prices` total row count and date range, the manifest count/hash list for the 4 incident dates with manifests, the `data_provider_runs` row count, both ledger file sha256 values, and the `watchlist` row count.
- TC-2: given the artifact from TC-1, when an independent read-only spot-check query re-runs the same `daily_prices` count and date-range query a second time after capture, then the two counts and the two date ranges are identical, proving the capture step itself wrote nothing.
- TC-3: given a fresh fixture SQLite DB built from current SQLModel metadata with `PRAGMA foreign_keys=ON` explicitly issued, when a `ScannerRun` row and a `NextSessionManifest` row referencing it are inserted and the `ScannerRun` row is then deleted, then the delete succeeds with no FK violation and the `NextSessionManifest` row remains present with all fields unchanged.
- TC-4: given the same fixture after TC-3's delete, when a NEW `ScannerRun` row is inserted for the same `as_of` date, then `basis_disclosure` for that manifest reports the rebuilt state via `as_of` + `source_run_created_at` comparison, and `source_run_id`, `content_hash`, `manifest_hash`, `version`, `available_at_utc`, `prospective_eligible` are all unchanged from their TC-3 values.
- TC-5: given the same fixture but with NO replacement `ScannerRun` created for that `as_of` after TC-3's delete, when `basis_disclosure` is evaluated, then it returns the "underlying run unavailable" state without raising and without reporting a fabricated available or rebuilt state.
- TC-6: given a manifest minted from run id `N` created at `T1`, when that run is deleted and a replacement run reusing numeric id `N` is created with `created_at = T2 > T1`, then the manifest's `source_run_id` is still `N`, its bytes and both hashes are unchanged, and `basis_disclosure` reports `rebuilt` (not `original`) because `source_run_created_at != current_run.created_at`.
- TC-7: given `freeze_attempt_identity` computed once for this attempt, when `check_attempt_identity_consistency` is called with (a) a run stamped with that exact identity and (b) a run stamped with a different `engine_identity`, then (a) returns consistent/true and (b) returns inconsistent/false — the mismatch case is asserted explicitly, not inferred from an aggregate.
- TC-8: given `apps/backend/data/trendora.db`'s mtime and a full-DB row-count/date-range snapshot taken before this iteration's work starts, when the same snapshot is taken again after this iteration's work completes, then the mtime and every counted/ranged value are identical.
- TC-9: given this spec's `Depth: full` line, when the orchestrator dispatches this iteration, then `runs/goal-market-compass-iter-10/depth-dispatched` reads `full`.
- TC-10: given `docs/goal.md` Loop-mechanics forbids any browser-QA or deterministic-replay lane before J-11 Stage G passes, when this iteration completes, then no QA evidence directory or replay-results file dated to this iteration exists, and journey-history's recorded status for J-01, J-02, J-03, J-04, and J-10 is byte-identical to its value before this iteration.

## NOTES

- This is a deliberate sub-slice of J-11 (Stages B/B1/B2 of A-G); J-11's overall status is the evaluator's call, not asserted here — it should stay at least `partial`/`unknown` pending Stages C-G, which own the actual derived-state repair and the only place the four gated browser journeys (J-01/J-02/J-03 replay) may run.
- Assumption logged: `runs/goal-session-market-compass/state/assumptions.md` (iter-10 — goal-decomposer) records the choice to split J-11 at the B/B1/B2 → C-G boundary rather than deliver all seven stages in one iteration.
- Five older owner questions remain open and non-blocking (see OUT OF SCOPE); none require action this iteration.
- If Stage B1's fixture tests reveal that the FK-reconciliation contract cannot be made to hold under `PRAGMA foreign_keys=ON` without a genuinely destructive migration, `docs/goal.md` J-11 step 11 already directs: STOP before Stage C and surface it as an owner decision rather than guessing — do not weaken the acceptance items to force a pass.
