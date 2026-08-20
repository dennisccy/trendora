# Goal Iteration 6 — Bounded recovery of 2026-08-11 / 2026-08-12 (J-10 only)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: the recovery touches the provider/fetch path, a new
  fail-closed scope guard (new code), the derived-state (ScannerRun) rebuild path, and provenance
  recording, and it must independently prove AG-12/AG-17 held across the whole manifest subsystem —
  four-plus interacting surfaces whose joint correctness is not covered by any single journey's
  existing tests, and the exact failure class (an agent silently widening a live-fetch scope) already
  happened once this session via a forked sub-agent (iter-5 dev handoff). Matches the evaluator's
  binding-full recommendation independently, not merely by citation.
- **Frontend Present:** no
- **Target journeys:** J-10
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04 (verified strictly AFTER recovery +
  verification complete — never against the damaged database; see Loop mechanics gate in BACKGROUND)
- **Anti-goal reminders:**
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use
    bars > as-of; the manifest for close D derives only from state stored at or before D; never
    introduce lookahead anywhere. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local
    provider fixtures — no live external network calls or paid data services without an explicit
    goal.md amendment. *(critical)*
    - **Dated exception (owner, 2026-08-20 — single-use, self-closing, incident response):** the
      bounded recovery fetch defined by **J-10** is authorized for exactly two calendar dates,
      **2026-08-11 and 2026-08-12**, and only for the symbol/row scope proven missing as a
      consequence of the iter-5 drill. It authorizes **nothing else**: no other date (in particular
      nothing on or after 2026-08-13), no refresh of unaffected historical data, no replacement of
      valid existing rows, no broad backfill, no advancement of the dataset to a newer market-data
      frontier, no change to candidate thresholds or research logic, and no unrelated data repair.
      The intent is **state restoration only, not dataset advancement**. If the implementation cannot
      prove a request stays inside this scope, it MUST stop rather than broaden the fetch. The
      exception is **exhausted** the moment J-10's post-recovery verification passes — normal AG-9
      then applies again automatically, and any later live fetch, **including of these same two
      dates**, requires a new dated goal.md amendment. The only retry permitted under this exception
      is a re-run of the same bounded, idempotent recovery after a failed or partial attempt, still
      confined to the proven missing set. This is not a standing "recovery fetch allowed" path.
  - **AG-10 — Host resource ceiling (hardware protection), carried from ops-hardening:** heavy compute
    MUST be launched only via the project launch scripts, which MUST apply the host caps declared in
    `project-extensions/host-guard/host-guard.env` whenever present (CPU-affinity mask, BLAS/OMP
    thread caps) plus the `config.yaml` `server.memory_cap_mb` / `malloc_arena_max` values. Never
    remove, weaken, or bypass these caps; stripping a HOST-GUARD marked block from a launch script is
    a REGRESSION regardless of test outcomes. The ceiling VALUES are an owner-set envelope (current:
    `memory_cap_mb` 8192, `HOST_GUARD_MEMORY_HIGH` 12G, per the dated owner amendments recorded in
    `docs/archive/goal-ops-hardening.md`); only the owner may change them. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are
    never mutated or deleted by any later ingest, rebuild, data removal, config change, or code
    change; corrections happen only as new version rows; a historical view never substitutes a newer
    manifest. *(critical)*
  - **AG-17 — Repair never rewrites provenance (owner, 2026-08-20):** restoring deleted historical
    data MUST NOT retroactively change research provenance. A manifest that was retrospective or
    ineligible stays that way; **`prospective_eligible` is never upgraded merely because historical
    data was later repaired**; `available_at_utc`, manifest versions, `content_hash`/`manifest_hash`,
    and prior eligibility classifications remain immutable (AG-12 governs the rows and files
    themselves). Any manifest or artifact produced while the database was known to be damaged —
    everything dated from the iter-5 drill until J-10's post-recovery verification passes — **remains
    marked unusable as prospective/out-of-sample evidence**; only a separately regenerated artifact,
    minted after verified recovery under the existing create-once and version rules, may carry
    eligibility, and it remains subject to the same version and `prospective_eligible` contract as
    any other artifact. The incident record itself is evidence: the iter-5 drill result, its handoff,
    the reviewer/QA evidence already produced, and the explicit statement that the committed seed
    could not restore these dates MUST NOT be deleted, rewritten, or silently superseded. Repairing
    the database never rewrites historical causality. *(critical)*

## GOAL

Restore exactly the `daily_prices` bars for 2026-08-11 and 2026-08-12 that iteration 5's destructive
drill deleted — and only those two dates — through a fail-closed, proven-scope, idempotent live fetch,
so `GET /api/compass?as_of=2026-08-12` serves again and J-01/J-02/J-03's live replay passes clean.

## BACKGROUND

Iteration 5's own in-scope drill (remove+backfill believing 2026-08-11/2026-08-12 were seed-safe)
permanently deleted those two dates' price bars — the committed seed's real boundary is 2026-07-01
(`apps/backend/data/seed/meta.json`), five to six weeks earlier than iteration 5's spec assumed — and
was superseded before evaluation once discovered (full account: the iter-5 dev handoff's "READ THIS
FIRST" section, `runs/goal-market-compass-iter-5/status.json`, and
`runs/goal-session-market-compass/state/incident-2026-08-20-iter-5-superseded.md`). The owner then
amended `docs/goal.md` same-day: **J-10** (this bounded recovery), a dated single-use AG-9 exception
scoped to it, **AG-17** (repair never rewrites provenance), a recorded-but-deferred destructive-drill-
isolation defect note, and a **Loop mechanics** insert stating **no lane may run against the knowingly
damaged database before J-10's post-recovery verification passes**. This iteration targets **J-10
alone** per that explicit owner instruction — this is fully consistent with priority rubric rule 1
(regressed journeys first): J-01/J-02/J-03 are functionally regressed right now (a live replay fails
for all three per the iter-5 dev handoff's post-drill re-verification), even though
`journey-history.json` still reads them "passing" because iteration 5 was never evaluated. No other
journey is bundled in (rubric rule 5: exactly one risky journey per iteration; J-05/J-06's make-up,
J-07, J-08, and J-09's open owner decision all stay OUT — the loop-mechanics gate forbids running them
against the damaged DB anyway).

**Why full depth (matches the evaluator's binding recommendation independently):** this is not routine
feature work. It combines a live-network write against production data, a brand-new fail-closed scope
guard whose ENTIRE job is refusing to repeat exactly the mistake that caused this incident, a
derived-state rebuild, and a hard requirement to prove AG-12/AG-17 held across the whole manifest
subsystem afterward — cross-cutting interactions no single journey's existing tests cover (Full
trigger 1). The iter-5 dev handoff also records a directly relevant process hazard: a forked sub-agent
dispatched for a narrow, unrelated research task inherited the full parent dispatch context and
independently executed its own pass at the same live drill against the same running backend/database —
concurrently and without coordination. Full depth's auditor lane exists precisely to catch this class
of scope violation (it already caught a real AG-12 breach in iter-3), and this iteration needs that
independent check more than most.

**Evidence already in hand (no fresh discovery work needed for the missing-set proof's starting
point):** iter-5's own `POST /api/data/remove/preview` call (before removal) recorded
`removable_bar_count: 1132`, `removable_symbol_count: 587` for the exact 2026-08-11..2026-08-12 range —
usable as a cross-check input to this iteration's own fresh derivation, not a substitute for it. The
same handoff also found the destructive removal's `remove_data` cascade rule removed `ScannerRun`
snapshots for **eleven** dates whose forward-return window touched the deleted range — not just the
two named dates: 2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03,
2026-08-05, 2026-08-10, 2026-08-11, 2026-08-12. J-10's own text ("restores exactly what was deleted and
nothing else", acceptance "no third date is touched") deliberately scopes this iteration to only the
two NAMED dates; the other nine stay unrepaired by this iteration (their price bars are intact — only
their derived snapshot is gone — so a plain offline backfill COULD fix them with no AG-9 exception
needed, but that is new scope the owner did not authorize here). See NOTES and the assumption-ledger
entry for the reasoning and the residual risk this narrow reading carries.

**Existing mechanism reuse — no new fetch mechanism should be built:** `POST /api/data/jobs` already
supports `kind: "fetch"` with an explicit `symbols` list that scopes the fetch to EXACTLY those
diagnosed-gap symbols instead of the whole universe (the J-37 "pull-missing" pattern,
`apps/backend/app/api/data.py`'s `JobCreate`) — this is "the project's existing provider path" J-10
step 2 names. The vendor is `stooq` per goal.md's own amendment text ("the same vendor the affected
rows came from (`stooq`, per the seed manifest)") — the iter-5 dev handoff's own speculative mention of
"yahoo" is superseded by this more precise, owner-written sourcing; follow goal.md, not the handoff's
hedge. `data_provider_runs` (`apps/backend/app/models.py`) already carries `provider`, `started_at`,
`finished_at`, `symbols_ok`, `symbols_failed`, `status`, `message`, `job_id` — the existing provenance
surface J-10 step 4 says to extend, not replace.

## IN SCOPE

### Backend
- [ ] Pre-recovery missing-set derivation: re-derive (not merely copy) the exact missing `(date,
      symbol)` rows for 2026-08-11 and 2026-08-12 from the named surviving evidence — the frozen
      `next_session_manifests` payloads for those two `as_of` dates, `data_provider_runs`, the iter-5
      dev handoff and `runs/goal-market-compass-iter-5/status.json`, the surviving coverage/
      availability tables, and the universe membership in force on those dates — and record a
      pre-recovery missing-row count per date and per symbol in the new dev handoff, before any
      network call is made.
- [ ] A new, narrow, fail-closed scope guard that sits in front of the fetch call: it must reject, in
      code, any date outside `{2026-08-11, 2026-08-12}`, any symbol/row outside the derived missing
      set, and any row that already exists in `daily_prices` — never by convention or operator
      discipline alone. Treat the two dates and the derived symbol list as incident-specific literals
      scoped to this single-use guard, not a new reusable `config.yaml` tunable (see NOTES).
- [ ] The bounded fetch itself, via the existing `POST /api/data/jobs` `kind: "fetch"` +
      `symbols=<derived list>` + `source: "stooq"` path (or the equivalent direct
      `data_manager.start_data_job` call) — additive only, idempotent (a re-run after a partial/failed
      attempt restores only what is still missing, never duplicates or overwrites a row).
- [ ] Once 2026-08-11/2026-08-12 bars exist, rebuild ONLY those two dates' `ScannerRun` snapshots (and
      their forward returns) through the normal ingest/backfill path — no other as-of date's stored
      run is created, deleted, or modified by this step.
- [ ] Provenance recording via the EXISTING conventions only (`data_provider_runs` fields + a dated
      section in the new dev handoff) — no new provenance table/framework: authorization basis (this
      AG-9 amendment), exact dates fetched, symbols/rows restored, provider, start/completion
      timestamps, pre-recovery missing-row count, post-recovery restored-row count, any row requested
      but not restored, and the resulting dataset/frontier state.
- [ ] Post-recovery verification suite (J-10 step 5, all six checks) executed and recorded: restored
      coverage for the two dates; no other historical date modified (diffed against the recorded
      pre-recovery baseline); no surviving row overwritten; frontier not advanced past 2026-08-12; the
      project's existing data/DB-integrity checks pass; `GET /api/compass?as_of=2026-08-12` serves
      again and J-01/J-02/J-03 replay clean. If byte-for-byte restoration cannot be proven (vendor
      archive not itself immutable), state that limitation plainly and verify the named practical
      invariants instead (per-symbol row presence, OHLCV shape, expected session count, no gap against
      surrounding trading days).
- [ ] Exception-closure statement in the dev handoff: once verification passes, record that AG-9's
      dated exception is exhausted and normal offline-deterministic ingest applies again automatically.
- [ ] All recovery work stays on `goal/market-compass`; `main` is not touched.

### New user-facing capability
None — data-layer repair only. No new page, panel, control, or displayed field.

### New information displayed
None. The user-visible effect is that already-shipped surfaces (J-01 `/stocks`, J-02/J-03 `/`) resume
serving correct data for the dates that were broken; nothing new is exposed.

### New user actions
None.

### UI surface changes
None — J-10's own Walkthrough note is explicitly waived ("data-layer repair with no UI surface change
of its own").

### Product surface delta
None from the user's viewpoint beyond "the thing that was broken (compass and stock data for
2026-08-11/2026-08-12) works again" — no new surface, no relocated surface, no changed layout.

### Blueprint conformance
No new surfaces. `runs/goal-session-market-compass/state/blueprint.md` requires no edit this
iteration: no new displayed value, no new page, and no change to any registered Data-Contract row's
computing module or serving endpoint — this iteration restores missing INPUT data for values that are
already registered and already read from their existing canonical source.

### Data-contract additions
None. This iteration introduces no new displayed value, no new computing module, and no new serving
endpoint. It restores rows in `daily_prices` (an upstream input, not itself a blueprint-tracked
displayed value) so that already-registered values (compass content, sector labels, dashboard/
market-phase fields) resolve correctly again for 2026-08-11/2026-08-12 through their existing,
unchanged producers and endpoints.

## OUT OF SCOPE

- J-05/J-06's make-up run (real close seals a manifest; delete/restore/regenerate drill) — explicitly
  gated behind this journey by the owner's Loop-mechanics insert; plan it only in a later iteration.
- J-07, J-08 — still failing, untouched.
- J-09's open owner decision (accept 3.44 GB VmPeak vs. re-bound `_BarCache.prefill` vs. a new target)
  and Constraint (c) (`_BarCache.prefill` re-bound) — untouched; nothing this iteration depends on it.
- Destructive-drill isolation/sandbox infrastructure (disposable DB, transaction rollback, snapshot/
  restore, fixture copy) — Constraints explicitly record this as a defect + future direction and say
  NOT to build it as part of J-10 recovery.
- Rebuilding `ScannerRun` snapshots for the nine OTHER cascade-collateral dates (2026-05-12, 2026-05-13,
  2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03, 2026-08-05, 2026-08-10) — their price
  bars are intact, only their derived snapshot is gone, but J-10's own acceptance text ("no third date
  is touched") scopes this iteration to exactly the two named dates. Left unrepaired this iteration.
- Any advancement of the effective dataset frontier past 2026-08-12.
- Any fetch of 2026-08-13 or later (already permanently gone from an earlier, iter-1-era drill; not
  covered by this AG-9 exception regardless).
- Redesigning the as-of resolver's "unavailable" basis-disclosure behavior (the carried J-06 step 2
  wording question) — untouched, still owner-pending.
- Rewording J-01's test steps or resolving the "empty next-session focus" acceptability question —
  untouched, still owner-pending.
- Any new provenance table/framework — use only the existing `data_provider_runs` + dev handoff
  conventions.
- Any frontend/UI change.

## DEFINITION OF DONE

- [ ] J-10 steps 1-7 satisfied with recorded evidence in the dev handoff (missing-set proof, bounded
      fetch, survivor protection, provenance record, verification suite, exception-closure statement,
      branch confinement to `goal/market-compass`)
- [ ] `daily_prices` maximum date equals 2026-08-12 exactly after recovery (frontier unchanged, not
      advanced)
- [ ] `GET /api/compass?as_of=2026-08-12` returns HTTP 200 after recovery (was HTTP 400)
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04 all report PASS via deterministic replay
      (LLM fallback where no golden exists), run strictly after recovery + verification complete
- [ ] All pre-existing `next_session_manifests` rows (24, reaching as_of 2026-08-12) and their export
      files remain byte-identical (hash-verified) before vs. after recovery; no row's
      `prospective_eligible` value changed — AG-12 and AG-17 held
- [ ] No `daily_prices` or `scanner_runs` row outside the proven `{2026-08-11, 2026-08-12}` missing
      scope is created, deleted, or modified this iteration — explicitly including the nine other
      cascade-collateral dates staying untouched
- [ ] `docs/phases/goal-market-compass-iter-5.md`, `docs/handoffs/goal-market-compass-iter-5-dev.md`,
      `runs/goal-market-compass-iter-5/status.json`, and the incident record remain byte-identical to
      their pre-iteration-6 state
- [ ] No destructive-drill-isolation infrastructure appears anywhere in this iteration's diff
- [ ] Unit tests for the new fail-closed scope guard pass (targeted/scoped run only — never the full
      suite; synthetic-fixture, file-scoped per Constraints); no regressions in a targeted re-run of
      `test_manifest_invariants.py` / `test_api_compass.py`
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-6-dev.md`, including the dated
      provenance section and the explicit "AG-9 exception exhausted" statement

## TESTING REQUIREMENTS

- Browser: J-01, J-02, J-03, J-04 (deterministic replay + LLM fallback), run ONLY after recovery and
  verification both complete — never against the damaged database. No browser-qa pass is required for
  J-10 itself (no UI surface; walkthrough waived per goal.md); J-10 is verified via the deterministic
  checks below and the dev handoff's provenance/verification record.
- Unit/integration: a fixture-scoped test module proves the recovery scope guard's fail-closed
  behavior (rejects an out-of-window date and an out-of-set symbol/row before any network call) and
  the fetch's idempotent re-invocation (no duplicate/overwritten rows on re-run); a targeted (not full-
  suite) re-run of `test_manifest_invariants.py` and `test_api_compass.py` confirms zero regression in
  manifest immutability/serving behavior.
- Error cases: a request naming any date outside `{2026-08-11, 2026-08-12}` is rejected before any
  network call; a request naming any symbol/row outside the derived missing set is rejected before any
  network call; a row that cannot be evidenced from the named sources halts that row's fetch for owner
  review rather than fetching an unproven guess for it.

Test-first contract:

- TC-1: given the pre-recovery database (`daily_prices` max date 2026-08-10, `next_session_manifests`
  holding 24 rows reaching as_of 2026-08-12), when the missing-set derivation runs over
  `data_provider_runs`, the frozen manifest payloads for as_of 2026-08-11/2026-08-12, the iter-5 dev
  handoff, `runs/goal-market-compass-iter-5/status.json`, and universe membership, then a written
  pre-recovery missing-row count exists in the iter-6 dev handoff, per date and per symbol, for
  2026-08-11 and 2026-08-12 only.
- TC-2: given the derived missing set from TC-1, when the recovery fetch is invoked, then its actual
  request parameters cover exactly `{2026-08-11, 2026-08-12}` and exactly the derived symbol list —
  no date on or after 2026-08-13 and no already-present row appears in the request.
- TC-3: given the scope guard is called with a date of 2026-08-13 or later, when it evaluates that
  input, then it raises/rejects before any network call is made (unit-level, no live network probe).
- TC-4: given the scope guard is called with a symbol or `(date, symbol)` pair outside the derived
  missing set, when it evaluates that input, then it raises/rejects before any network call is made.
- TC-5: given the recovery fetch has already run once (fully or partially), when it is re-invoked, then
  only rows still absent from `daily_prices` for 2026-08-11/2026-08-12 are inserted, and zero rows are
  duplicated or overwritten.
- TC-6: given the recovery fetch completes, when `daily_prices` is queried for 2026-08-11 and
  2026-08-12, then the restored row count equals the TC-1 derived missing-row count, or every shortfall
  row is named explicitly in the dev handoff.
- TC-7: given the recovery fetch completes, when every `daily_prices` row outside the
  `{2026-08-11, 2026-08-12}` × missing-symbol scope is re-queried, then its stored values are
  byte-unchanged from the recorded pre-recovery baseline (row-count and checksum comparison).
- TC-8: given bars for 2026-08-11 and 2026-08-12 are present, when the normal ingest/backfill path runs
  over exactly that date range, then a `ScannerRun` snapshot exists for 2026-08-11 and for 2026-08-12,
  and no `ScannerRun` row for any other as-of date is created, deleted, or modified.
- TC-9: given `next_session_manifests` held 24 rows reaching as_of 2026-08-12 before recovery, when the
  same table and its export files are re-queried/re-hashed after recovery, then all 24 rows are
  byte-identical to their pre-recovery values and no row's `prospective_eligible` value changed.
- TC-10: given recovery completes, when `data_provider_runs` and the dev handoff are inspected, then a
  dated record names the AG-9 exception as authorization, the exact two dates fetched, the restored
  symbols/rows, the provider (`stooq`), start/completion timestamps, the pre-recovery missing-row
  count, the post-recovery restored-row count, and any row requested but not restored.
- TC-11: given recovery completes, when `daily_prices`'s maximum date is queried, then the value is
  exactly 2026-08-12 (not earlier, not later).
- TC-12: given recovery completes, when `GET /api/compass?as_of=2026-08-12` is called, then it returns
  HTTP 200 with the previously-frozen manifest payload (not HTTP 400).
- TC-13: given recovery completes, when the J-01, J-02, J-03, and J-04 deterministic replay lane runs
  against the live app, then all four report PASS.
- TC-14: given recovery and verification both complete, when the dev handoff is inspected, then it
  states in writing that AG-9's dated exception is exhausted and normal offline-deterministic ingest
  applies again.
- TC-15: given the iteration completes, when `docs/phases/goal-market-compass-iter-5.md`,
  `docs/handoffs/goal-market-compass-iter-5-dev.md`, `runs/goal-market-compass-iter-5/status.json`, and
  the incident record are re-read, then their contents are byte-identical to their pre-iteration-6
  state.
- TC-16: given the pre-recovery missing-set cannot be fully established from the named evidence sources
  for some specific row, when the derivation step reaches that row, then the dev handoff records the
  gap explicitly and that row's fetch stops for owner review rather than fetching an unproven guess.
- TC-17: given byte-for-byte restoration cannot be proven because the vendor archive is not itself
  immutable, when TC-6's byte-level check cannot be completed, then the dev handoff states that
  limitation plainly and reports the practical invariants checked instead (per-symbol row presence,
  OHLCV shape, expected session count, no gap against the surrounding trading days).
- TC-18: given the iteration completes, when `scanner_runs` is queried for the nine other cascade-
  affected dates (2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03,
  2026-08-05, 2026-08-10), then none of them has a newly created row this iteration — their state is
  unchanged from the pre-recovery baseline (still absent).
- TC-19: given the iteration's file diff, when it is reviewed against the Constraints
  "Destructive-drill isolation" note, then no sandbox/rollback/snapshot-restore infrastructure for
  future drills is present in the diff.

## NOTES

- **Scope-precision caveat (see also the assumption-ledger entry for this iteration):** the original
  destructive removal's cascade touched eleven `ScannerRun` dates, not two, but goal.md's J-10 text
  ("restores exactly what was deleted and nothing else"; acceptance "no third date is touched") reads
  as scoping strictly to the two NAMED dates. If TC-13's post-recovery J-01/J-02/J-03 replay turns out
  to depend on one of the other nine dates' snapshot (e.g., a golden that steps through 2026-08-10's
  own predecessor chain), that is a J-10 acceptance-criterion (TC-12/TC-13) failure to surface for
  owner review — it is NOT license to expand the fetch or rebuild those nine dates preemptively.
- **Process caution (iter-5 dev handoff finding):** a forked sub-agent dispatched for a narrow,
  unrelated research task inherited the full parent dispatch context and independently executed its
  own pass at the live drill against the same running backend/database — concurrently, uncoordinated,
  and contributing to the very loss this iteration repairs. If any sub-agent/fork is dispatched this
  iteration, scope its instructions narrowly and do not hand it this iteration's full dispatch context;
  the recovery fetch must be one deliberate, auditable action, never a side effect of an unrelated task.
- **Config-vs-literal judgment call:** the two recovery dates and the derived symbol list are treated
  as incident-specific constants inside the single-use scope guard, not new `config.yaml` tunables —
  they are not a reusable threshold and promoting them to global config would misrepresent this as a
  standing "recovery" feature, contrary to AG-9's own "not a standing... path" framing. See the
  assumption-ledger entry.
- **Host safety:** this iteration starts a live backend (required for the fetch and for serving
  `/api/compass` during verification). J-09's `cache_size` reduction (`config.yaml`, already landed) is
  in effect. Launch only via project scripts (`scripts/start-backend.sh`), which apply the HOST-GUARD
  caps (AG-10) — never bypass them. If the required-still-passing replay for J-01–J-04 also needs a
  frontend, prefer sequencing it after the recovery+verification backend session rather than running a
  second backend concurrently, to avoid repeating the 2026-08-20 two-backend memory pattern that froze
  this host; exact process orchestration remains the executing agents' call.
- **Open owner questions carried, not this iteration's concern:** J-09's ≤2.5 GB vs. 3.44 GB
  acceptance, J-06 step 2's "underlying run unavailable" wording, and J-01's step 1-2 rewording all
  remain outstanding per `iteration-state.md`'s Active blockers — untouched and unaffected here.
- **Hard stop-and-ask reminder:** per J-10 step 1 and its "Honest status" acceptance bullet, if ANY
  part of the recovery cannot be proven to stay inside the authorized AG-9 scope, the developer MUST
  stop and surface it for owner review rather than broadening the fetch to compensate — this is a hard
  rule, not a soft preference, given this exact host already suffered one uncoordinated live-fetch
  incident today.
