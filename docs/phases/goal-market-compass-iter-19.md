# Goal Iteration 19 — J-11 Stage D: live canonical regeneration of the eleven incident dates

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 19
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Stage D's correctness is a cross-cutting invariant (one frozen engine identity
  stamped consistently across `ScannerRun` + 3 child tables for 11 dates, gated by live
  maintenance-boundary state, under a hard manifest-non-creation constraint) spanning `scanner.py`, the
  new Stage D execution module, `j11_maintenance.py`/`j11_stage_d.py`, and 4 tables — no single
  journey's existing test suite covers this interaction, and it is a live, effectively irreversible
  write to the production database. (This also matches the evaluator's binding `full` recommendation
  for this iteration; no escape condition was needed since the recommendation already says `full`.)
- **Frontend Present:** no
- **Target journeys:** J-11
- **Required-still-passing journeys:** J-01, J-04, J-10
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed
    by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating).
    Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals,
    or alpha claims; never place or simulate orders. Candidate framing is "worth monitoring", never
    advice. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's
    computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone.
    *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use
    bars > as-of; the manifest for close D derives only from state stored at or before D; never
    introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict
    from the post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never crash
    an existing page or exhaust memory — consumers of widened fields are re-validated, the UI degrades
    gracefully, and unbounded whole-table ORM loads are forbidden. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local
    provider fixtures — no live external network calls or paid data services without an explicit
    goal.md amendment. *(critical)* — all three dated exceptions (J-10 recovery fetch, its vendor
    addendum, and the AVB diagnostic fetch #2) are **exhausted**; none applies to Stage D, and Stage D
    authorizes **no** network fetch of any kind.
  - **AG-10 — Host resource ceiling:** heavy compute MUST be launched only via the project launch
    scripts, which MUST apply the host caps; never remove, weaken, or bypass these caps. *(critical)*
  - **AG-11 — No new composite candidate number:** no "fit", "conviction", "match", "probability of
    success", or any new blended score may be attached to candidates, the market, or the manifest.
    *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are
    never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change;
    corrections happen only as new version rows; a historical view never substitutes a newer manifest.
    *(critical)*
  - **AG-13 — System-vs-market separation:** readiness/preflight vocabulary must never label market
    state, and regime/phase vocabulary must never label system state. *(critical)*
  - **AG-14 — No Tapeology coupling:** no imports from, network calls to, or writes into the tapeology
    repository or its services. *(critical)*
  - **AG-15 — No outcome-tuned selection:** the selection rule and its thresholds must not be chosen or
    revised from realized forward returns within this goal. *(critical)*
  - **AG-16 — Cohorts are not controls:** the comparison cohort and the near-threshold shadow cohort are
    frozen non-selected pools, not matched or causal control groups. *(critical)*
  - **AG-17 — Repair never rewrites provenance:** restoring deleted historical data MUST NOT
    retroactively change research provenance. Any manifest or artifact produced while the database was
    known to be damaged — everything dated from the iter-5 drill until **J-11 Stage G passes** — remains
    marked unusable as prospective/out-of-sample evidence. The incident record itself is evidence and
    MUST NOT be deleted, rewritten, or silently superseded. *(critical)*
  - **AG-18 — The authorized manifest migration preserves everything:** the bounded
    `next_session_manifests` schema migration authorized in J-11 step 11 (ruling A1) removes the
    `source_run_id` foreign-key constraint and **nothing else**. No manifest may be regenerated,
    rebound, rehashed, upgraded, deleted, or newly minted by it or around it. *(critical)*

## GOAL

Execute the owner-authorized J-11 Stage D live regeneration of the eleven canonical incident dates'
derived state — `ScannerRun` + `ScannerResult`/`SectorScoreRow`/`ThemeScoreRow` children — through the
existing canonical scanner engine, all under one freshly frozen execution identity, with zero raw-input
mutation and zero manifest fabrication. This is a backend-only, no-user-visible-surface maintenance
iteration: on success it reports `J-11 STAGE D EXECUTED: YES`, while the overall incident honestly
remains `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE` until Stages E, F and G follow in
later iterations.

## BACKGROUND

Iteration 18 satisfied every pre-Stage-D safety gate (maintenance boundary ACTIVE, live guard ARMED, the
AVB-corrected raw baseline certified, `J-11 STAGE D READY: YES`) and halted STALLED for the seventh
iteration running — exactly as `docs/goal.md` required, because Stage D authorization was reserved for a
separate, later owner instruction. That instruction has now arrived: the 2026-08-26 owner ruling
*"J-11 Stage D through Stage G recovery execution AUTHORIZED"* (commit `5fe72f5c`) sets
`J-11 STAGE D AUTHORIZED: YES` and defines the exact Stage D write scope, the fresh-identity mechanism,
and whole-attempt failure semantics.

This spec scopes iteration 19 to **Stage D alone** — the canonical regeneration of the 11 incident
dates' Layer-2 derived rows — leaving Stage E (forward-return hole repair), Stage F (cache invalidation)
and Stage G (full verification, the only stage that may declare the incident repaired) to later
iterations. This is a deliberate scoping decision, logged to `assumptions.md`: it mirrors every prior
J-11 stage in this session (B1, Stage C, the AVB correction, the guard build, the table-create-and-arm)
each getting its own iteration, and it is exactly the honest checkpoint `docs/goal.md`'s own item-14
terminal-outcome contract for this ruling anticipates — `J-11 STAGE D EXECUTED: YES`, Stages E/F/G not
yet attempted, `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE`, boundary still `ACTIVE`. "There
is no third state" governs the vocabulary, not the dispatch granularity.

Depth is `full`, matching the evaluator's binding recommendation for this iteration (the eleventh
consecutive full-depth iteration in this session; 0 consecutive lean, so no hardening-cadence trigger
applies either way). The codebase already carries extensive Stage-D-adjacent scaffolding, built ahead of
time across iterations 14-18 specifically for this moment:
`j11_maintenance.freeze_attempt_identity`/`check_attempt_identity_consistency`,
`j11_stage_d.freeze_stage_d_attempt_identity` plus its three Check (A)/(B)/(C) identity-compare
functions, `capture_stage_d_preflight`/`compare_stage_d_preflight_to_certified`, and iteration 18's
generic `capture_full_table_sweep`/`diff_full_table_sweeps` mutation-accounting tool — all documented as
reusable **for** this execution; `j11_stage_d.py`'s own docstring states a real Stage D execution "must
call [`freeze_stage_d_attempt_identity`] fresh, immediately before its first write." This iteration is
therefore mostly about composing already-proven building blocks into the one piece that has never
existed anywhere in this codebase: the actual write path, plus running it for real, once, against the
live database.

**Lessons applied** (from `lessons.md`): iter-9's population-wide-claim lesson —
`check_attempt_identity_consistency` already encodes "no aggregate-only all-N-matched claim without
per-date evidence," and this spec requires per-date Check (B)/(C) records, not a single boolean. Iter-12's
"mtime+WAL as the PRIMARY instrument, corroborated — never replaced — by a narrower fingerprint"
precedent governs the mutation-accounting requirement below. Iter-13/13b's identity-freezing discipline
for a multi-iteration attempt (state what each frozen field is compared against) and iter-15b's
frozen-fingerprint-without-a-recipe near-miss are why this spec requires the identity to be a
live-recomputed value from a named function, never a quoted hash pasted into a report.

**Maintenance isolation must remain active for the whole of this iteration** (no application-service
boot, no browser QA, no replay lane). This spec deliberately does **not** set a `Maintenance isolation:`
or `Depth enforcement:` metadata line — those are operator-only controls, and a self-written safety
declaration here would be exactly the governor-bypass anti-pattern 25 describes. Independently of this
spec, `docs/goal.md`'s own Stage D→G ruling (item 13) requires the human dispatching this run to supply
`CHAIN_MAINTENANCE_ISOLATION=true` and `CHAIN_REQUIRE_FULL_DEPTH=true` as **required launch conditions**
for "the next Goal Mode resume that executes this ruling," and to STOP and report rather than silently
demote depth or disable isolation if the engine cannot provide them. This is the same operator practice
already applied on every resume since roughly iteration 12.

## IN SCOPE

### Backend
- [ ] New Stage D execution orchestration — e.g. `apps/backend/app/engine/j11_stage_d_execute.py` (a
  **new** module; `j11_stage_d.py` is deliberately readiness-only per its own docstring, "It performs NO
  Stage D execution," and stays unchanged). It must:
  - re-run a fresh live preflight before any write, composing the EXISTING
    `j11_stage_d.capture_stage_d_preflight` / `compare_stage_d_preflight_to_certified` /
    `stage_d_preflight_verdict`, plus a fresh read-only re-derivation of the AVB classification via the
    EXISTING `j11_avb_diagnostic` module (never a second implementation), and confirm the maintenance
    boundary is `active=1` with exactly `app.engine.j11_maintenance.INCIDENT_DATES` and the live guard
    blocks all 11 dates (read-only re-verification only — never re-arms, never disarms);
  - freeze ONE fresh execution attempt identity via `j11_stage_d.freeze_stage_d_attempt_identity` called
    directly (not the `readiness_time_only` wrapper), immediately before the first write;
  - for each of the 11 `INCIDENT_DATES`, in ascending chronological order: confirm no `ScannerRun`
    already exists for that date; run Check (B) `check_identity_before_date`; call `scanner.run_scan`
    directly (never through `data_manager`'s backfill/ingest-finalize path, never through
    `warmup`/`forward_testing`); run Check (C) `check_identity_after_persist`; STOP the whole attempt
    immediately at the first failing check or unmet precondition, with no further date attempted;
  - perform post-execution mutation accounting via `j11_maintenance.capture_full_table_sweep` /
    `diff_full_table_sweeps` (before/after), plus the whole-file mtime/size/WAL bracket captured at the
    true process start and true process end as the primary instrument.
- [ ] A `--confirm`-gated CLI script — e.g. `apps/backend/scripts/run_j11_stage_d_execute.py` — mirroring
  `run_j11_stage_c_bounded_clear.py`'s idiom exactly: zero database interaction of any kind without
  `--confirm`; `--evidence-dir` required with no implicit default; evidence persisted at every checkpoint
  before the destructive step; a completion/outcome marker written only after full post-execution
  verification passes.
- [ ] The confirmed live execution itself: run the script once against `apps/backend/data/trendora.db`
  under maintenance isolation, producing the full evidence set and the exact status lines listed in
  DEFINITION OF DONE.
- [ ] Fixture-scoped unit/integration tests for the new module and CLI script (never against the live
  database) covering every scenario in TESTING REQUIREMENTS.

### New user-facing capability
None — backend-only maintenance; no page, route, or UI element changes this iteration.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None this iteration. (Once Stage G eventually passes, the 11 incident dates become servable through the
existing, already-built UI — J-11 needs no surface of its own, matching its "Walkthrough: waived" status
in `docs/goal.md`.)

### Blueprint conformance
No new surfaces. Stage D regenerates existing canonical derived state
(`ScannerRun`/`ScannerResult`/`SectorScoreRow`/`ThemeScoreRow`) through the SAME already-registered
computing module (`scanner.run_scan`/`persist_run_payload`) and the same eventual serving endpoints
already listed in `blueprint.md`'s Data Contract — no second producer, no new endpoint, no new page.
`runs/goal-session-market-compass/state/blueprint.md` is **not** edited this iteration (nothing to
register).

### Data-contract additions
None.

## OUT OF SCOPE

- Stage E (global create-once forward-return hole repair), Stage F (dependency-aware cache invalidation),
  and Stage G (full verification / the acceptance gate) — deferred to later iterations (scoping decision
  logged to `assumptions.md`).
- Deactivating or clearing the `j11-incident-recovery` maintenance boundary — forbidden until Stage G
  passes; it must remain `active=1` at the end of this iteration, whatever the outcome.
- Re-creating or re-arming `maintenance_boundaries`/the boundary row — already LIVE, ARMED, VERIFIED
  ("do not redo" per iteration-state digest); this iteration only re-**verifies** it, read-only.
- Any provider/network fetch — AG-9 remains closed; no dated exception applies to Stage D.
- Any `daily_prices` write — raw inputs remain immutable through Stage G.
- The ordinary request-path guard gap (`scanner.resolve_run`, `scanner.py:348`) and the Data Manager
  write-path guard — explicitly recorded-but-deferred by the new ruling (item 5) to post-Stage-G
  hardening work. Do not touch `app/api/*` or `data_manager.py`'s write paths this iteration.
- The remaining small jobs from iteration 18's recommendation (the health-badge wording decision,
  considering the Data Manager guard, annotating iteration 17's QA report, fixing the mutation-accounting
  proof method to a true content hash) — deferred (scoping decision logged to `assumptions.md`); none is
  bundled into this destructive-write iteration.
- Any J-01–J-09 product/UI work, and specifically J-07/J-08 — blocked by the Loop-mechanics gate until
  Stage G passes.
- Application-service boot, browser-qa-agent, the deterministic replay lane, a second backend or frontend
  process — all OFF for the whole iteration (maintenance isolation).
- Any schema/DDL migration — none authorized or needed this iteration.
- Re-running `run_j11_avb_correction.py` — spent and verified intact ("do not redo"); only a fresh
  READ-ONLY re-derivation of the classification (via the existing diagnostic module) is in scope.
- Restamping, mutating, or otherwise touching the 34 iteration-10-era `ScannerRun`s (identity
  `6261ca17…`) or any pre-stamping-era NULL-`engine_identity` row.
- Re-deriving the boot-path call graph for `warmup.py`/`forward_testing.py` — both gaps are already
  closed ("do not redo").

## DEFINITION OF DONE

- [ ] Fresh preflight (maintenance boundary state, live guard, all-11-dates-at-zero-`ScannerRun`, AVB
  classification, comparison against the certified Stage C baseline) is re-derived live and read-only
  immediately before any write; the attempt proceeds only if every check agrees with the certified state
  and `AVB-A` — otherwise it STOPs with the exact blocker named and zero writes performed.
- [ ] One fresh Stage D execution attempt identity is frozen immediately before the first write and
  proven (by independent recomputation, never by copying a value) distinct from every historical
  identity already on disk (iteration 10, iteration 14, the iteration-16/17/18 `readiness_time_only`
  observations).
- [ ] The attempt ends in exactly one of the two states `docs/goal.md`'s Stage D→G ruling (item 14)
  defines — never an invented third state — and the dev handoff states the outcome using its exact
  vocabulary: `J-11 STAGE D AUTHORIZED: YES`, `J-11 STAGE D EXECUTED: YES/NO`,
  `J-11 STAGE E COMPLETE: NO`, `J-11 STAGE F COMPLETE: NO`, `J-11 STAGE G VERIFIED: NO`,
  `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE`, `J-11 MAINTENANCE BOUNDARY: ACTIVE`,
  `J-11 LIVE PRE-BOOT GUARD: ARMED`.
- [ ] If `STAGE D EXECUTED: YES`: all 11 `INCIDENT_DATES` carry exactly one new `ScannerRun` each, every
  one stamped with the SAME frozen attempt identity, with matching `ScannerResult`/`SectorScoreRow`/
  `ThemeScoreRow` children — proven by live read-only query, not asserted from a diff.
- [ ] If `STAGE D EXECUTED: NO`: the attempt stopped at the first failing check with no further date
  attempted, full evidence preserved, and the handoff states explicitly that any retry requires the full
  C→G restart for all 11 dates (never a resume from the next unfinished date).
- [ ] Zero `NextSessionManifest` rows created or changed: 24 rows before and after; the 4 incident-date
  rows byte/value-identical (`version`, `content_hash`, `manifest_hash`, `prospective_eligible`,
  `available_at_utc` unchanged); the 7 previously-manifest-less incident dates still at zero manifests —
  proven live and read-only.
- [ ] Zero writes to `daily_prices`, `data_provider_runs`, `watchlist`, `maintenance_boundaries`,
  `next_session_manifests`, and every table outside `scanner_runs`/`scanner_results`/`sector_scores`/
  `theme_scores` — proven by before/after full-table sweep plus the whole-file mtime/size/WAL bracket as
  the primary instrument.
- [ ] The 34 iteration-10-era `ScannerRun`s and the NULL-stamped pre-stamping-era rows are byte-unchanged
  — proven by a direct query, not by absence from the diff.
- [ ] Maintenance isolation held for the entire iteration — no application-service boot, no
  browser-qa-agent dispatch, no replay lane; the engine's refusal log (mirroring
  `iter-18/maintenance-isolation-refusals`) is the evidence.
- [ ] Required-still-passing journeys J-01, J-04, J-10 are **not** re-verified via browser QA or replay
  this iteration (both are impossible under maintenance isolation); instead their canonical files
  (`app/api/*`, `scoring.py`, `sectors.py`, `compass.py`, `data_manager.py`'s J-10 recovery code) are
  proven untouched via `git status --porcelain -uall` grepped against that file set — the same method
  iteration 18's coherence audit used.
- [ ] Fixture-scoped unit/integration tests (never against the live database) pass for every scenario in
  TESTING REQUIREMENTS.
- [ ] No anti-goal violation introduced; the ledger stays at its current total with zero new unresolved
  entries.
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-19-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** none this iteration. `browser-qa-agent` does not run — maintenance isolation forbids
  application-service boot for the whole of J-11 through Stage G (`docs/goal.md` Loop mechanics, and this
  ruling's own item 4).
- **Unit/integration:** the new execution module's preflight-gate composition, fresh-identity freeze,
  per-date Check (B)/Check (C) orchestration, whole-attempt stop-on-first-failure, manifest-non-creation
  invariant, out-of-scope-date vacuous pass, and the CLI script's `--confirm`/`--evidence-dir` gating —
  all fixture-scoped, reusing the isolated-engine pattern the sibling `test_j11_*` suites already use
  (`app.db.make_engine`, never the live `trendora.db`).
- **Error cases:** an identity mismatch at Check (A)/(B)/(C); a `ScannerRun` unexpectedly already existing
  for an incident date; a preflight drift against the certified Stage C baseline; an AVB classification
  other than `AVB-A`; a CLI invocation missing `--confirm`; a CLI invocation missing `--evidence-dir`.

Test-first contract — scenarios:

- TC-1: given the live database with Stage C's certified post-clear baseline (11 incident dates at zero
  `scanner_runs` rows, `runs/goal-market-compass-iter-13/j11-stage-c-*.json`) and the J-11 maintenance
  boundary `active=1` covering exactly `app.engine.j11_maintenance.INCIDENT_DATES` (certified in
  iteration 18), when the Stage D execution tooling's fresh preflight step runs before any write, then it
  re-derives every one of: the 11-date zero-`ScannerRun` state, the boundary's active status and exact
  date set, the live guard's `blocked=True` result for all 11 dates, and a freshly re-run AVB diagnostic
  classification — directly from the live database, never from a cached artifact — and reports
  `passed: true` only if all agree with the certified Stage C baseline and `AVB-A`.
- TC-2: given the fresh preflight detects any drift, an unmet precondition, or an AVB classification
  other than `AVB-A`, when the gate evaluates, then the script performs zero writes to any table, exits
  non-zero, and persists the exact blocking reason to the evidence directory.
- TC-3: given preflight passes, when the script computes the Stage D execution attempt identity by
  calling `j11_stage_d.freeze_stage_d_attempt_identity` directly (not the `readiness_time_only` wrapper)
  immediately before the first write, then the returned `engine_identity` is persisted to a new evidence
  artifact, and a test asserts it is independently recomputed (never copied) and honestly compared
  (equal-or-not, stated either way) against the iteration-10, iteration-14, and iteration-16/17/18
  readiness-time identity values already on disk.
- TC-4: given the frozen attempt identity, when the script iterates the 11 `INCIDENT_DATES` in ascending
  order, then for each date it first confirms no `ScannerRun` already exists for that date (STOP if one
  does), runs Check (B) `check_identity_before_date` and requires `ok: true`, calls `scanner.run_scan`
  directly (never via `data_manager`'s backfill/finalize path, never via `warmup`/`forward_testing`), and
  runs Check (C) `check_identity_after_persist` on the newly persisted row, requiring `ok: true` before
  advancing to the next date.
- TC-5: given any date's Check (B), Check (C), pre-existing-run guard, or compute/persist call fails or
  raises, when that happens, then the script stops immediately, attempts no further date, and the
  persisted evidence names the exact failing date and check — proving the whole-attempt,
  no-piecemeal-continuation rule by construction.
- TC-6: given a full run over all 11 dates with no failure, when it finishes, then `scanner_runs` carries
  exactly one new row per `INCIDENT_DATES` value (11 total), each `engine_identity` equal to the frozen
  attempt identity, and each has at least one linked `scanner_results`, `sector_scores`, and
  `theme_scores` row.
- TC-7: given the run has finished (full success or a clean stop), when `next_session_manifests` is
  re-queried live and read-only, then it still holds exactly 24 rows, the 4 rows whose `as_of` falls
  inside the 11-date set are byte-identical to their pre-execution values (`version`, `content_hash`,
  `manifest_hash`, `prospective_eligible`, `available_at_utc` unchanged), and the 7 previously
  manifest-less incident dates still have zero manifest rows.
- TC-8: given a synthetic fixture database (never `trendora.db`) seeded with a Stage-C-shaped state —
  some `INCIDENT_DATES` cleared, an active `MaintenanceBoundary` row, one incident date already carrying
  a manifest — when the fixture test suite runs the execution module end-to-end via `app.db.make_engine`'s
  isolated engine, then it reproduces TC-4 through TC-7's assertions without opening the real database
  file.
- TC-9: given the existing out-of-scope vacuous-pass rule for Check (B)/(C) (`j11_stage_d.py`'s own
  precedent), when a test evaluates a date outside `INCIDENT_DATES`, then the check returns
  `in_scope: False, ok: True` and performs no identity comparison and no write for that date.
- TC-10: given the CLI script is invoked without `--confirm`, when it runs, then it performs zero database
  interaction (not even a read) and exits non-zero.
- TC-11: given the CLI script is invoked without an explicit `--evidence-dir`, when it runs, then it
  refuses before any config/engine construction and exits non-zero — mirroring
  `run_j11_stage_c_bounded_clear.py`'s already-fixed footgun.
- TC-12: given a before-capture and an after-capture of `j11_maintenance.capture_full_table_sweep`
  bracketed by the whole-file mtime/size/WAL fingerprint at the true process start and end, when
  `diff_full_table_sweeps` compares them after the live run (full success or a clean stop), then
  `changed_existing_tables` is a subset of `{scanner_runs, scanner_results, sector_scores, theme_scores}`
  only, and `unexpected_new_tables`/`unexpected_removed_tables` are both empty.
- TC-13: given the 34 iteration-10-era `ScannerRun` rows stamped `6261ca17…` and the pre-stamping-era
  NULL-`engine_identity` rows, when the post-execution verification runs, then their count and
  `engine_identity` values are proven unchanged from the pre-execution capture by a direct query, not
  merely by absence from the diff.
- TC-14: given the live execution has run to its conclusion (full success or a clean stop), when the dev
  handoff and evidence artifacts report status, then they state exactly `J-11 STAGE D AUTHORIZED: YES`,
  `J-11 STAGE D EXECUTED: YES` or `NO` matching the true outcome, `J-11 STAGE E COMPLETE: NO`,
  `J-11 STAGE F COMPLETE: NO`, `J-11 STAGE G VERIFIED: NO`,
  `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE`, and `J-11 MAINTENANCE BOUNDARY: ACTIVE` — the
  exact terminal-outcome vocabulary `docs/goal.md`'s Stage D→G ruling (item 14) requires, never an
  invented intermediate status.
- TC-15: given maintenance isolation is active for the whole iteration, when any lane other than
  developer/reviewer/file-scoped-QA/auditor attempts to run (application-service boot, browser-qa-agent,
  the deterministic replay lane), then the engine refuses the dispatch and logs the refusal, mirroring
  `iter-18/maintenance-isolation-refusals`.
- TC-16: given `daily_prices`, `data_provider_runs`, `watchlist`, and `maintenance_boundaries` are outside
  Stage D's authorized write scope, when the post-execution mutation accounting is inspected, then all
  four show zero fingerprint change from the pre-execution capture.
- TC-17: given J-01 and J-04's passing status and J-10's passing status each rest on the untouched
  content of `app/api/*`, `scoring.py`, `sectors.py`, `compass.py`, and `data_manager.py`'s J-10 recovery
  code, when `git status --porcelain -uall` (tracked + untracked) is grepped against that exact file set
  after this iteration's changes are staged, then it returns zero matches — the same proof method
  iteration 18's coherence audit used, standing in for browser QA and replay, both forbidden this
  iteration by maintenance isolation.
- TC-18: given AG-9 forbids any live network call during Stage D and every one of its dated exceptions is
  exhausted, when the new execution module and CLI script are inspected (grep for network-capable imports
  and calls, mirroring the check iteration 18's anti-goal review already performed on its own new files),
  then zero network-capable call appears anywhere in the diff, and the live execution's evidence artifacts
  record zero outbound requests.

## NOTES

- **Assumption-ledger entries filed this iteration** (`runs/goal-session-market-compass/state/assumptions.md`):
  (1) scoping this iteration to Stage D alone rather than the full authorized D→G sequence; (2) excluding
  iteration 18's two remaining low-risk evidence-correction riders (annotating iteration 17's QA report;
  fixing the mutation-accounting proof method) from this destructive-write iteration; (3) requiring a
  fresh live preflight re-verification (including a re-derived AVB classification) immediately before
  Stage D's first write, despite the iteration-state digest's "Stage D readiness... do not re-derive"
  note — read as governing the planning question (settled), not the execution precondition (which
  `docs/goal.md`'s own Stage C precedent and `j11_stage_d.py`'s own docstring both require fresh,
  immediately before any destructive write).
- **Operational recommendation:** keep `run-goal.sh`'s pump running continuously with
  `CHAIN_MAINTENANCE_ISOLATION=true` and `CHAIN_REQUIRE_FULL_DEPTH=true` set across this iteration AND the
  subsequent Stage E/F/G iterations until `J-11 STAGE G VERIFIED: YES`. `docs/goal.md` item 13 frames the
  whole D→G execution as one continuous "Goal Mode resume"; stopping and restarting the environment
  between stages risks exactly the "ambient shell state" pitfall it warns against.
- **Escalation flag:** if the fresh preflight step (this iteration's own addition, see assumption entry 3
  above) finds ANY drift from the certified Stage C baseline, or an AVB classification other than
  `AVB-A`, the developer must STOP before any write and report the exact blocker — do not attempt to
  reconcile, re-derive a new baseline, or force through.
- **Framework items carried forward, out of this product iteration's scope** (per CLAUDE.md's mode
  separation, unchanged from prior iterations): the `scripts/automation/` forbidden-lane defect; and
  `goal_gate.py`'s duplicate-journey-heading defect, which must be fixed before any GOAL_ACHIEVED
  certification.
- If the reviewer, QA, or auditor lane finds that live execution cannot proceed safely for any reason not
  anticipated above, the correct action is the same as every prior J-11 stage in this session: stop,
  preserve evidence, and report — never force a write past a failing check to obtain a "complete" status.
