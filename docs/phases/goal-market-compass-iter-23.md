# Goal Iteration 23 — J-11 disposable-clone serving/replay verification (final acceptance objective)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 23
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — cross-cutting: real backend + frontend + browser + replay execution against a live
  boot must exercise the interaction of ≥5 distinct engine modules at once (scanner, data_manager, compass,
  forward_testing, the seven J-11-classified cache tables) whose failure modes cross agent boundaries and
  are not covered end-to-end by any single existing journey's own test suite; this also matches the
  dispatch's own binding engine-computed depth recommendation for this iteration (`full`).
- **Frontend Present:** no (no frontend code changes are in scope; the existing Today/Market frontend is
  exercised read-only by browser QA as part of verification — see NOTES)
- **Target journeys:** J-11
- **Required-still-passing journeys:** J-01, J-04, J-10 (the full currently-`passing` set — only three
  journeys are `passing` session-wide, so this is simultaneously the rotating smoke set and a full
  regression, appropriate for the first real browser QA/replay execution in 14 iterations)
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's
    computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never crash an
    existing page or exhaust memory — consumers of widened fields are re-validated, the UI degrades
    gracefully (contained error boundary, honest "—"/NA placeholder), and unbounded whole-table ORM loads
    are forbidden (the delta engine reads column-projected selects, never full record_json sweeps).
    *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local
    provider fixtures — no live external network calls or paid data services without an explicit goal.md
    amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection), carried from ops-hardening:** heavy compute MUST
    be launched only via the project launch scripts, which MUST apply the host caps declared in
    `project-extensions/host-guard/host-guard.env` whenever present (CPU-affinity mask, BLAS/OMP thread
    caps) plus the `config.yaml` `server.memory_cap_mb` / `malloc_arena_max` values. Never remove, weaken,
    or bypass these caps; stripping a HOST-GUARD marked block from a launch script is a REGRESSION
    regardless of test outcomes. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are
    never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change;
    corrections happen only as new version rows; a historical view never substitutes a newer manifest.
    *(critical)*
  - **AG-17 — Repair never rewrites provenance (owner, 2026-08-20):** restoring deleted historical data
    MUST NOT retroactively change research provenance. A manifest that was retrospective or ineligible
    stays that way; **`prospective_eligible` is never upgraded merely because historical data was later
    repaired**; `available_at_utc`, manifest versions, `content_hash`/`manifest_hash`, and prior
    eligibility classifications remain immutable (AG-12 governs the rows and files themselves). Any
    manifest or artifact produced while the database was known to be damaged — everything dated from the
    iter-5 drill until **J-11 Stage G** passes (owner, 2026-08-21: extended from "J-10's post-recovery
    verification", because after J-10 the raw layer is repaired but the derived state is still knowingly
    pending J-11 normalization) — **remains marked unusable as prospective/out-of-sample evidence**;
    nothing is retroactively marked prospective merely because raw bars were repaired in J-10 or derived
    snapshots were regenerated in J-11 — historical causality is unchanged by either; only a separately
    regenerated artifact, minted after verified recovery under the existing create-once and version rules,
    may carry eligibility, and it remains subject to the same version and `prospective_eligible` contract
    as any other artifact. The incident record itself is evidence: the iter-5 drill result, its handoff,
    the reviewer/QA evidence already produced, and the explicit statement that the committed seed could
    not restore these dates MUST NOT be deleted, rewritten, or silently superseded. Repairing the database
    never rewrites historical causality. *(critical)*

## GOAL

Prove — through a real backend/frontend/browser/replay execution against a disposable, byte-faithful clone
of the repaired canonical database (never the canonical database itself) — that the J-11 database recovery
(Stages D through G, already accepted complete) actually SERVES correctly, so J-11 can close.

## BACKGROUND

Iteration 22 halted `STALLED` because the only remaining J-11 work needed a browser and a decision only the
owner could make: may the app be booted? The owner answered on 2026-08-27 across two `docs/goal.md`-only
commits (`95ef430d`, `2bdd8ac1`) with a binding ruling: Stages D-G are accepted **COMPLETE at the database
level** (`J-11 DATA RECOVERY: COMPLETE` / `J-11 DATABASE ACCEPTANCE: COMPLETE`, not to be reopened) and
exactly one acceptance objective remains — real serving/replay verification, run against a **disposable
clone**, with the canonical repaired database staying OFF and unmutated throughout. The same ruling's
"Post-Stage-G launch-condition clarification" spends the §13 launch conditions
(`CHAIN_MAINTENANCE_ISOLATION=true` / `CHAIN_REQUIRE_FULL_DEPTH=true`) for the completed D→G execution only
— they are explicitly **not** requirements for this final verification, which by definition needs the
opposite: real app boot, browser QA, and replay. Per the memory carried into this session, both engine
flags are already OFF for this resume and must **not** be re-armed.

This makes J-11 the unambiguous priority-rubric pick: it is not regressed, the last coherence verdict was
`COHERENCE-PASS` (no consolidation forced), and it is the sole remaining **unblocker** — every other
partial/failing journey (J-02, J-03, J-05, J-06, J-07, J-08, J-09) can only be verified in a browser, and
the canonical database stays off-limits to browser QA until J-11 closes per the owner's own scope
discipline ("the next Goal Mode resume should decompose toward this final serving verification and then
return to normal Market Compass product work" — ruling item 9). Bundling any of those journeys into this
iteration would violate that explicit instruction and the "never bundle two risky changes" rubric rule, so
this iteration targets J-11 alone.

Three lessons from this session's own arc bind directly here. iter-19: "after any live rebuild, re-derive
what an ordinary request would now DO" — that re-derivation, live, through real requests, is exactly this
iteration's job. iter-21: "a cache-will-refresh-cheaply proof is not a content-correctness proof," and
emptying/preserving a cache is only durable if every write path back into it is enumerated — this iteration
is the first live exercise of the seven request-path writers goal.md names (`scanner.resolve_run`,
`compass.get_or_create_manifest`, `data_manager.coverage_from_storage`'s self-heal branch — closed by
iter-22 — plus four more), so it must watch all of them, not assume iter-22's one fix covers the rest.
iter-22 (twice): a gate boolean must be able to fail against the REAL module, and any proof must run BEFORE
the action it gates — relevant here because the closure rule (goal.md ruling item 8) gates an irreversible
status change (`J-11 STATUS: PASSING`); the evaluator, not this spec, makes that determination, and only
from live, falsifiable evidence.

## IN SCOPE

### Backend / Operations
- [ ] Create a disposable, byte-faithful clone of the canonical `apps/backend/data/trendora.db` using a
      consistent SQLite backup mechanism (e.g. the sqlite3 `.backup` command or `VACUUM INTO`, not a raw
      file copy while the DB might be open). Record clone-provenance evidence: `daily_prices` row count,
      `next_session_manifests` row count (24), `data_provider_runs` max id, and a whole-file checksum,
      compared against the canonical DB at clone time.
- [ ] Create a disposable verification-only config file (do NOT edit the committed `config.yaml`) whose
      only difference from it is `database.url` pointing at the clone path, loaded via the existing
      `TRENDORA_CONFIG` env-var override (`apps/backend/app/config.py:3147-3157`).
- [ ] Boot backend and frontend for QA using the project's standard launch scripts (so AG-10's host caps
      still apply) with `TRENDORA_CONFIG` pointed at the disposable verification config. Before and after
      the whole boot+verification window, checksum the canonical `apps/backend/data/trendora.db` file and
      assert it is byte-unchanged.
- [ ] Run the goal.md ruling item 4 minimum real verification against the disposable clone only: boot
      succeeds; Today (`/`) and Market (`/market`) serving paths render; repaired incident-date state (the
      11 rebuilt `ScannerRun`s, ids 3148-3158) reads/renders correctly wherever J-11's existing acceptance
      contract (goal-slice Acceptance block) requires it; the 24 pre-existing manifests remain byte/hash
      identical; repaired `ScannerRun`/forward-return state serves consistently; no fabricated or stale
      pre-repair state is served anywhere touched.
- [ ] Execute the "verification must not itself mint a manifest" trap: for the 7 incident dates with no
      pre-existing manifest (2026-05-12, 05-13, 07-10, 07-13, 07-24, 07-27, 08-03), verify state through
      read-only routes or direct DB assertions only — never a `GET /api/compass?as_of=<that date>` request.
- [ ] Exercise the already-named schema/identity traps against the disposable clone (goal-slice Acceptance,
      "Named traps for the schema/identity/retry blockers"): manifest survival holds with
      `PRAGMA foreign_keys=ON`; deleting/rebuilding an incident `ScannerRun` does not rewrite its
      historical manifest; plus any further traps in that same named list relevant to a live-serving check.
- [ ] Enumerate and classify, by MEANING (goal.md ruling item 5), every write observed on the disposable
      clone during the whole verification window. Flag as FAIL any unacceptable canonical-data-contract
      side effect: an unexpected `ScannerRun`, a minted historical `NextSessionManifest`, a changed
      `daily_prices` row, a rewritten forward-return row, a modified immutable manifest field, or a
      rewritten incident-date `ScannerResult`/`SectorScoreRow`/`ThemeScoreRow`.
- [ ] If — and only if — verification demonstrates one specific, reachable defect: apply the minimum
      targeted fix for that demonstrated defect only (no proactive guarding/redesign of the other known
      open writer paths), then re-run the full verification on a fresh disposable clone. Any such fix must
      be proven against the real production module with a regression test that can actually fail
      (iter-22's lesson), never a hand-built fixture standing in for it.
- [ ] Discard the disposable clone DB file and verification config at the end of the iteration; confirm no
      committed artifact or launch script is left pointing default traffic at it.

### Frontend
- None planned. The existing Today (`/`) and Market (`/market`) pages are exercised read-only by browser
  QA/replay for verification; no frontend code change is in scope unless a demonstrated defect (see the
  targeted-fix bullet above) is frontend-side, in which case the fix stays minimum and targeted.

### New user-facing capability
None. This iteration proves the already-built Today/Market compass surfaces serve the already-repaired
data correctly; it adds no new capability.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — Today (`/`) and Market (`/market`) render exactly as already built; this iteration is a
verification pass, not a UI change.

### Product surface delta
None from the product's perspective. Operationally, this is the first real browser QA/replay execution in
14 iterations, run against a disposable clone rather than the canonical database.

### Blueprint conformance
Today (`/`) and Market (`/market`) — both already-registered Information-Architecture homes in
`blueprint.md`'s Navigation skeleton. No new page or nav entry. See `blueprint.md`'s iter-23 note.

### Data-contract additions
None. Every value exercised by this verification (Next-session manifest CONTENT + FREEZE/INTEGRITY blocks,
engine identity, stock sector label, regime/phase/breadth, sector/theme scores, evidence ledger status) is
already registered in `blueprint.md`'s Data Contract with its existing single computing module and serving
endpoint; this iteration reads them, never adds or duplicates a producer/endpoint.

## OUT OF SCOPE

- Reopening Stage D, E, F, or G database recovery — all four are accepted COMPLETE (ruling item 1) and must
  not be re-cleared, re-regenerated, or re-verified from scratch.
- Proactively guarding or redesigning any of the seven known-open request-path writers beyond the minimum
  targeted fix for an ACTUALLY DEMONSTRATED defect (ruling item 6) — evidence-driven hardening only, never
  speculative hardening.
- `journey_history_hash` / stall-detector redesign; generic Goal Mode anti-tautology framework changes;
  generic maintenance-boundary redesign; blanket hardening of all known writer call sites; auditor
  trap-citation remapping — unless any of these directly and demonstrably blocks this iteration's closure
  (ruling item 7).
- `goal_gate.py`'s duplicate-journey-heading defect and the `scripts/automation/` forbidden-lane defect —
  both explicitly eligible now that Stage G has passed, both explicitly NOT this iteration's job unless
  shown to block closure.
- Advancing J-02, J-03, J-05, J-06, J-07, J-08, or J-09 toward `passing` — normal Market Compass product
  work resumes in a LATER iteration, after J-11 closes (ruling item 9).
- Booting or mutating the canonical `apps/backend/data/trendora.db` for any purpose.
- The five older open owner questions (J-09 3.44 GB acceptability; J-06 wording; J-01 test-step wording;
  empty "next-session focus"; MNST) — non-blocking, untouched this iteration.
- Editing `docs/goal.md` — the owner already ruled; no ruling ambiguity remains that needs an owner edit.

## DEFINITION OF DONE

- [ ] A disposable, byte-faithful clone of the canonical repaired database exists with recorded provenance
      evidence proving it began from the canonical repaired state (row-count + checksum match at clone time)
- [ ] The canonical `apps/backend/data/trendora.db` is proven byte-unchanged (checksum identical) from
      immediately before cloning to the end of the iteration
- [ ] All items in goal.md ruling item 4's minimum verification list pass against the disposable clone
      (boot; Today/Market serving; repaired incident-date state renders correctly; the 24 manifests are
      unchanged; ScannerRun/forward-return state serves consistently; no fabricated/stale state served)
- [ ] The "verification must not itself mint a manifest" trap holds — zero new `NextSessionManifest` rows
      exist for the 7 manifest-less incident dates after verification
- [ ] Zero unacceptable canonical-data-contract side effects occur on the disposable clone (per the
      enumerated list in ruling item 5); if one occurs, it is the sole reported finding and Stages D-G are
      not reopened
- [ ] Target journey J-11 passes via browser-qa-agent against the disposable clone (or, if a real defect is
      found, stays `partial` with only that concrete defect reported — the evaluator's call, not a
      developer/reviewer self-declaration)
- [ ] Required-still-passing journeys J-01, J-04, J-10 remain green when exercised against the same
      disposable clone (deterministic replay + LLM fallback)
- [ ] No anti-goal violation introduced (AG-10 host caps still apply to the disposable-clone boot; AG-9 no
      live network fetch; AG-12/AG-17 manifest immutability and provenance honesty hold)
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-23-dev.md`

## TESTING REQUIREMENTS

- Browser: J-11 (target, against the disposable clone); J-01, J-04, J-10 (required-still-passing, same
  clone) — the full currently-passing set, appropriate given this is the first real browser QA/replay
  execution in 14 iterations.
- Unit/integration: no new production code is anticipated unless verification demonstrates a concrete
  defect. If a minimum targeted fix is applied (ruling item 6), the fixed module gains a regression test
  that mutates the REAL production module and is shown to fail without the fix (iter-22's lesson) —
  never a hand-built fixture standing in for it.
- Error cases: a launch attempt that omits the `TRENDORA_CONFIG` override (i.e., would default to the
  canonical DB) must be refused before any browser/replay execution proceeds; a request that would mint a
  manifest for a manifest-less incident date must be avoided by construction (read-only checks only) and,
  if accidentally triggered, must be caught and reported as a hard verification FAIL rather than silently
  absorbed or treated as a normal cache-refresh side effect.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps to at
least one concrete scenario line below.

- TC-1: given the canonical repaired database at `apps/backend/data/trendora.db` (post Stage G: 24
  manifests, `ScannerRun` ids up to 3158), when a byte-faithful SQLite backup/clone is created via a
  consistent backup mechanism, then the clone's `daily_prices` row count, `next_session_manifests` row
  count (24), and `data_provider_runs` max id equal the canonical DB's values at clone time, recorded as
  provenance evidence in the dev handoff.
- TC-2: given the disposable clone and a verification-only config overriding only `database.url`, when the
  backend is started via the standard launch script with `TRENDORA_CONFIG` set to that config's path, then
  the backend health endpoint reports ready and the canonical file `apps/backend/data/trendora.db`'s
  checksum is identical to its pre-boot value.
- TC-3: given the backend booted against the disposable clone, when `/` (Today) is loaded at the latest
  as-of, then the page renders HTTP 200 with the market-state band, summary, and manifest strip showing
  values matching the disposable clone's stored rows for that as-of, and no client error boundary fires.
- TC-4: given the backend booted against the disposable clone, when `/market` is loaded, then it renders
  HTTP 200 with every card from the former dashboard inventory present, reading the same endpoints as
  before relocation.
- TC-5: given an incident date that already carries a manifest (2026-08-05, 08-10, 08-11, or 08-12), when
  the Today/compass view is requested for that as-of, then the served manifest's payload bytes and
  `manifest_hash` are byte-identical to its recorded pre-verification value (no new version minted).
- TC-6: given one of the 7 incident dates with no pre-existing manifest (2026-05-12, 05-13, 07-10, 07-13,
  07-24, 07-27, 08-03), when verification checks that date's state, then it uses a read-only route or
  direct DB assertion — never a `GET /api/compass?as_of=<that date>` request — and the
  `next_session_manifests` row count for that date is 0 both before and after the check.
- TC-7: given the disposable clone's `next_session_manifests` table starts at 24 rows, when the full
  serving verification pass completes, then the table's row count is still 24 and every one of the 24
  pre-existing rows is field-identical across all columns to its recorded pre-verification value.
- TC-8: given `PRAGMA foreign_keys=ON` is set on the disposable clone's connection, when the manifest
  survival and rebuild-does-not-rewrite-history checks run, then both still pass (named traps 1-2 from
  goal-slice Acceptance).
- TC-9: given the disposable clone, when the required-still-passing smoke set is exercised (J-01: a stock
  detail page shows a real stored sector label, not "Unassigned", for a symbol proven to carry one; J-04: a
  next-session candidate card shows a structured why/why-not reason; J-10: 2026-08-11 and 2026-08-12 each
  show 585 `daily_prices` rows with AVB volumes 554757.0 / 3706010.0), then every rendered value matches the
  certified figures with zero client errors.
- TC-10: given the whole verification pass runs to completion, when every DB write observed on the
  disposable clone is enumerated and classified by meaning, then zero writes fall into the "unacceptable
  canonical-data side effect" category listed in ruling item 5; any that do are reported as the sole
  finding in the dev handoff.
- TC-11: given verification completes per TC-1 through TC-10 with zero unacceptable side effects, when the
  evaluator reviews the evidence, then it may record `J-11 SERVING/REPLAY VERIFICATION: PASS` and
  `J-11 STATUS: PASSING`; given instead a genuine defect is found, then the evaluator records only that
  concrete defect, J-11 stays `partial`, and Stages D-G are not reopened.
- TC-12: given the iteration completes (pass or fail), when the disposable clone directory and its
  verification config are inspected in the final diff, then neither is committed as tracked application
  state, and a final checksum of `apps/backend/data/trendora.db` still matches its value recorded at
  iteration start.

## NOTES

- Owner authorization: `docs/goal.md` commits `95ef430d` ("accept J-11 D-G database recovery; one serving
  verification remains") and `2bdd8ac1` ("clarify §13 launch conditions are spent post-Stage-G"), both
  2026-08-27, are the binding source for this entire iteration. Read the full ruling text in
  `docs/goal.md` (owner ruling "J-11 database recovery accepted; one final serving verification remains"
  and its "Post-Stage-G launch-condition clarification" subsection) before implementing — this spec
  summarizes it but the ruling's exact wording governs.
- Session memory carried into this resume: `CHAIN_MAINTENANCE_ISOLATION` and `CHAIN_REQUIRE_FULL_DEPTH` are
  already OFF for this run and must NOT be re-armed — consistent with the owner's launch-condition
  clarification above.
- `Depth: full` is chosen per the dispatch's own binding engine recommendation and independently justified
  under full-depth Trigger 1 (see Goal Mode Metadata); see `assumptions.md` iter-23 entry for the full
  reasoning, including why `TRENDORA_CONFIG` (not a `config.yaml` edit) is the sanctioned override lever.
- This spec deliberately does NOT set `Depth enforcement: required` or `Maintenance isolation: required` —
  the owner's ruling explicitly requires the OPPOSITE of isolation for this task (real app boot/browser
  QA/replay), scoped only to the disposable clone; those two lines are operator-only levers and are not
  written here per the governor-bypass anti-pattern (`.claude/anti-patterns/25-self-justifying-governor-
  bypass.md`).
- If the developer/reviewer/QA/audit chain finds ANY real defect during verification, the correct action is
  the minimum targeted fix plus a fresh re-run — not a broader hardening pass. Re-read ruling items 6, 7,
  and 9 before scoping any fix.
