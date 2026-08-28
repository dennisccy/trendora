# Goal Iteration 27 — J-06's last blocker: the live route can now honestly disclose a missing source run

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 27
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict was ESCALATE (mandatory full depth, no exceptions per the rules;
  the iter-26 evaluator escalated specifically because this exact fix needs the independent auditor lane)
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-04, J-05, J-10, J-11
- **Frontend Present:** no
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's
    computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars
    > as-of; the manifest for close D derives only from state stored at or before D; never introduce
    lookahead anywhere. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never crash an
    existing page or exhaust memory — consumers of widened fields are re-validated, the UI degrades
    gracefully (contained error boundary, honest "—"/NA placeholder), and unbounded whole-table ORM loads
    are forbidden (the delta engine reads column-projected selects, never full record_json sweeps).
    *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local
    provider fixtures — no live external network calls or paid data services without an explicit goal.md
    amendment. *(critical)* (dated recovery/diagnostic exceptions omitted here — not applicable; this
    iteration performs no live fetch of any kind)
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are
    never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change;
    corrections happen only as new version rows; a historical view never substitutes a newer manifest.
    *(critical)*
  - **AG-17 — Repair never rewrites provenance (owner, 2026-08-20):** restoring deleted historical data
    MUST NOT retroactively change research provenance. A manifest that was retrospective or ineligible
    stays that way; `prospective_eligible` is never upgraded merely because historical data was later
    repaired; `available_at_utc`, manifest versions, `content_hash`/`manifest_hash`, and prior eligibility
    classifications remain immutable (AG-12 governs the rows and files themselves). Any manifest or
    artifact produced while the database was known to be damaged — everything dated from the iter-5 drill
    until J-11 Stage G passes — remains marked unusable as prospective/out-of-sample evidence; nothing is
    retroactively marked prospective merely because raw bars were repaired in J-10 or derived snapshots
    were regenerated in J-11. Repairing the database never rewrites historical causality. *(critical)*

## GOAL

`GET /api/compass` can now honestly report a frozen manifest's underlying scanner run as
`basis.status == "unavailable"` when that run has been removed, instead of silently self-healing
(recreating) the run first and only ever being able to say "available" or "rebuilt" — closing J-06's
last unmet acceptance limb without touching the shared self-heal machinery any other page relies on.

## BACKGROUND

The iter-26 evaluator (ESCALATE) located this precisely, for the third time this session (iter-3 audit
finding B2, iter-26 dev + reviewer + evaluator all re-confirmed it live): `apps/backend/app/api/compass.py`
line 59 calls `resolved_run()` — which resolves to `scanner.resolve_run` → `run_scan`, and `run_scan`
self-heals (creates) a missing `ScannerRun` — BEFORE `get_or_create_manifest`/`basis_disclosure` ever run.
By the time `basis_disclosure` looks up "is the current run for this as-of present", the self-heal has
already recreated it, so a live request can only ever observe `"available"` or `"rebuilt"` — never
`"unavailable"` — and it has already recomputed, which J-06 step 2 explicitly forbids. This is
`apps/backend/tests/test_api_compass.py::test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run`,
which today PASSES while asserting the bug (`basis.status == "rebuilt"`, `healed is not None`) — a
documented, unit-tested-but-unreachable state, exactly the iter-26 lesson ("a green test on a branch no
request can reach is an honesty gap, not coverage"). This iteration flips that test to prove the FIX
through the real serving entry point, following the same lesson.

Design choice to bound blast radius: the fix confines itself to `app/api/compass.py`'s route-level call
ordering plus one new pure-read helper in `app/engine/compass.py`. `snapshot_serving.resolved_run` and
`scanner.run_scan` — the shared self-heal machinery every OTHER page (`/`, `/stocks`, `/sectors`,
`/themes`, dashboard, market-phase) depends on — are NOT modified; their self-heal behavior for every
other route is byte-identical to today. This directly answers the coordinator's stated risk (that
`resolved_run` "is the code path every page uses") without touching that shared function at all: the
compass route simply stops calling it when a manifest already exists for the resolved as-of.

Row-count safety: per the binding `iter-26 — goal-decomposer` assumption-ledger entry, the literal live
remove+backfill drill stays routed to the isolated fixture suite — "the last two trading days" still
resolves to 2026-08-11/2026-08-12, the incident pair, and the AG-9 recovery exception is exhausted. This
iteration does not revisit that call; it extends the SAME fixture suite with the route-level proof the
iter-26 lesson demands, and keeps every live/canonical-DB action strictly read-only and additive-free
(regression checks only, on manifests that already exist and whose runs are already intact). TC-8 makes
explicit that the 7 manifest-less incident dates are never queried by this iteration's own test/browser-qa
plan, closing the coordinator's "cannot silently start minting" requirement. TC-6/7/8's before/after
row-count checks are read AFTER every lane finishes, per the iter-23b lesson (`.db`/`-wal` content can
change without the checksum moving; a mid-run snapshot is not proof).

Depth is `full` because the prior verdict was ESCALATE (mandatory, no exceptions). Separately: this is the
sixth+ time this session a full-depth spec risked demotion on cost grounds despite an owner note
(`docs/goal.md` "Loop mechanics") that `Depth: full` must never silently become `lean`, and the change
sits in the compass route every J-02/J-03/J-04/J-05/J-06 surface reads. If the owner wants this
guaranteed rather than merely requested, only the owner can add `Depth enforcement: required` to this
file — that line is intentionally not self-granted here (anti-pattern 25).

## IN SCOPE

### Backend
- [ ] `apps/backend/app/engine/compass.py`: add a pure read-only helper (e.g.
  `latest_manifest_for_date(session, as_of) -> Optional[NextSessionManifest]`) that returns the latest
  stored manifest version for a date, or `None` — no run lookup, no write. Have `get_or_create_manifest`'s
  existing-row check call this helper instead of its own inline duplicate query (single source, no second
  query shape for the same fact).
- [ ] `apps/backend/app/api/compass.py`, `compass()` (`GET /api/compass`, ~lines 54-70): resolve the as-of
  STRING to a concrete date via the already-imported `resolved_date` FIRST (this never creates a
  `ScannerRun` — it only validates against stored price bars). Look up `latest_manifest_for_date` for that
  resolved date. When a manifest already exists, serve it directly (`manifest_row_payload` +
  `_read_time_additions`, whose `basis_disclosure` call is already a pure read-only `ScannerRun` SELECT)
  WITHOUT calling `resolved_run`/`run_scan` at all. Only fall through to today's `resolved_run` +
  `get_or_create_manifest` path (unchanged) when no manifest exists yet for the resolved date — this is
  the only branch that may still create a `ScannerRun` or mint a manifest, exactly as today.
  `POST /api/compass/regenerate` is untouched — `regenerate_manifest` already reads the current run via a
  plain SELECT and never self-heals; it already behaves correctly for J-06 step 4 (iter-26 verified).
- [ ] `apps/backend/tests/test_api_compass.py::test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run`:
  flip its assertions to the FIXED behavior — `basis["status"] == "unavailable"`, and the removed
  `ScannerRun` stays absent (`healed is None`) after the `GET` call — and update the surrounding
  docstring/comment block, which currently documents the bug as a structural limitation of this route.
- [ ] Same file: add a restore-path test extending the scenario above — with the manifest still serving
  `"unavailable"`, re-create the `ScannerRun` for that as-of (a) with the SAME `created_at` the manifest
  recorded, asserting `basis.status` flips to `"available"`; and (b) with a DIFFERENT `created_at`,
  asserting `"rebuilt"` — in both cases the manifest's `manifest_hash`/`version`/full payload stay
  byte-identical to the pre-removal response (J-06 step 3).
- [ ] Same file: add a warm-path regression test — with an existing manifest and its run intact, two
  consecutive `GET` calls through the route function return byte-identical responses and add zero new
  `ScannerRun` rows (proves the new fast-path branch is inert on the common, already-working case).
- [ ] Dev handoff: enumerate (via a read-only query against the live DB, never hardcoded) the manifest-less
  as-of dates inside the incident window from `next_session_manifests`/`scanner_runs`, and record that
  this iteration's own test/browser-qa plan never issues a `GET`/`POST` against any of them (TC-8).

### Frontend
None. `basis.status === "unavailable"` is an already-shipped, already-tested rendered state
(`apps/frontend/lib/basis-disclosure-label.ts` → `{variant: "danger", label: "Basis: unavailable"}`,
covered by `apps/frontend/lib/basis-disclosure-label.test.ts`) — this iteration only fixes when the
backend can honestly reach that state; no frontend file changes.

### New user-facing capability
None new. An existing, already-documented manifest-strip state ("Basis: unavailable") becomes reachable
in production for a frozen manifest whose underlying scanner run has since been removed, instead of being
silently masked by an unrequested recompute.

### New information displayed
None new — the `"unavailable"` member of `basis.status` has existed since iter-11's fail-closed fix; this
iteration only fixes WHEN it can be observed through the live route.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
On `/` (and `/?asof=<date>`), a frozen manifest whose source scanner run has been removed now honestly
shows "Basis: unavailable" instead of silently rebuilding the run behind the scenes and showing "Basis:
rebuilt" (or "available").

### Blueprint conformance
Today (`/`) — manifest strip / basis disclosure, per `blueprint.md`'s Information Architecture row
"J-05 / J-06 manifest freeze + immutability" (Nav section: Today). No new page, no new nav entry.

### Data-contract additions
None. This iteration changes only the internal read-time control-flow ORDER of the already-registered
FREEZE/INTEGRITY block row (`GET /api/compass`, computed by `app.engine.compass.build_manifest_payload` /
`basis_disclosure`) — no new computing module, no new serving endpoint, no new displayed field. See the
`blueprint.md` iter-27 note added alongside this spec.

## OUT OF SCOPE

- The literal live remove+backfill drill on the canonical database — still routed to the isolated fixture
  suite per the binding `iter-26 — goal-decomposer` assumption-ledger entry; "the last two trading days"
  still resolves to 2026-08-11/2026-08-12, and the AG-9 recovery exception is exhausted.
- J-07 ("The Today page answers the ten-second read") and J-08 ("Market page moves over intact") — the
  next pieces after J-06 closes, per `docs/goal.md`'s own suggested order; not started this iteration.
- The reviewer's cited MINOR (`test_manifest_invariants.py:155`'s AST scanner matches only the literal
  identifier `update` and scans only `app/engine/`) — carried forward, unrelated to this fix.
- J-04's screenshot re-take and the J-05/J-06 walkthrough recordings — passenger tasks only, never an
  iteration goal on their own.
- The five/four open, non-blocking owner questions (J-09's ~2.99 GB acceptability, J-06's "underlying run
  unavailable" wording, J-01's first two test steps, an empty "next-session focus", whether MNST joins the
  recovery list) — no action this iteration.
- Any change to `snapshot_serving.resolved_run` / `scanner.run_scan`'s self-heal behavior for any OTHER
  route (`/`, `/stocks`, `/sectors`, `/themes`, dashboard, market-phase) — those keep self-healing exactly
  as today; only the compass route's call ordering changes.
- Any change to the `next_session_manifests` schema (no columns, no constraints, no indices) — AG-12/AG-18
  unaffected.

## DEFINITION OF DONE

- [ ] J-06 passes via browser-qa-agent: the fixed-behavior route-level fixture tests (TC-1..TC-5, TC-9,
  TC-10) all pass and are cited in the dev handoff, PLUS a live canonical-DB regression screenshot of the
  manifest strip showing "Basis: available" for an intact manifest+run pair (TC-6/TC-7). Per the standing
  `iter-26` DB-safety scoping, the "unavailable" state itself is proven only at the fixture/route level —
  no live `ScannerRun` deletion is authorized this iteration, so browser-qa cannot reproduce it live; the
  evaluator scores J-06 from the combined fixture + live-regression evidence, as it did for J-05 in iter-26.
- [ ] Required-still-passing journeys J-01, J-04, J-05, J-10, J-11 remain green (deterministic replay lane
  + LLM fallback, mechanically verified)
- [ ] No anti-goal violation introduced — AG-12 (manifest bytes byte-identical across every basis
  transition, TC-2/3/4), AG-9 (no live fetch of any kind this iteration), AG-17 (no incident-date manifest
  minted, TC-8), AG-8 (no unbounded loads added)
- [ ] Unit tests pass; no regressions — `test_api_compass.py`, `test_manifest_invariants.py`,
  `test_ingest_finalize_compass.py`, `test_compass.py` (file-scoped runs only; never the full suite)
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-27-dev.md`, citing every TC below plus
  the existing J-06 test list (time-safety, rebuild survival, reproducibility, create-once concurrency,
  cohort reproducibility, prospective-eligibility derivation, availability-fence conservatism, artifact
  tamper detection, hash-scope separation, identity-separation counter-tests, disposition partition, schema
  conformance) that this iteration does NOT re-touch, confirming they still pass unmodified

## TESTING REQUIREMENTS

- Browser: J-06 — regression-only live check on the canonical database (TC-6, TC-7); do not attempt to
  reproduce the "unavailable" state live; no `ScannerRun` deletion against the canonical database is
  authorized this iteration.
- Unit/integration: fixture-DB route-level tests in `apps/backend/tests/test_api_compass.py`, calling the
  real `app.api.compass.compass` route FUNCTION directly with a session (the file's existing pattern) —
  TC-1 through TC-5, TC-9, TC-10.
- Error cases: TC-9 (unparseable/future `as_of` still map to their existing 4xx/503 status), TC-10 (the
  current frontier with no manifest yet still 404s via `ManifestNotYetFrozen`, unchanged).

Test-first contract:

- TC-1: given an isolated fixture DB with a frozen manifest for as_of=D whose underlying `ScannerRun` is
  intact, when `GET /api/compass?as_of=D` is called through the real route function, then the response is
  200, `basis.status == "available"`, and the `scanner_runs` row count is identical before and after the
  call.
- TC-2: given the fixture DB from TC-1, when the `ScannerRun` row for as_of=D is deleted directly in the
  fixture (never the canonical DB) and `GET /api/compass?as_of=D` is called again, then the response is
  200 (never 404), `basis.status == "unavailable"`, `basis.detail` states the underlying run is no longer
  stored, the manifest's `content_hash`, `manifest_hash`, `version`, and full cohort/candidate fields are
  byte-identical to the TC-1 response, and the `scanner_runs` row count is UNCHANGED from immediately
  before the call (no self-heal fired).
- TC-3: given the state left by TC-2, when the `ScannerRun` for as_of=D is re-created with the SAME
  `created_at` value the manifest's `generation.source_run_created_at` recorded, and
  `GET /api/compass?as_of=D` is called, then `basis.status == "available"` again and the manifest payload
  bytes are unchanged from TC-1.
- TC-4: given the state left by TC-2, when the `ScannerRun` for as_of=D is instead re-created with a
  DIFFERENT `created_at`, and `GET /api/compass?as_of=D` is called, then `basis.status == "rebuilt"`,
  `basis.detail` states the source run was recreated after the manifest was frozen, and the manifest
  payload bytes remain unchanged from TC-1 (only the read-time `basis` field differs).
- TC-5: given the fixture DB with NO manifest yet for a historical (non-frontier) as_of=E and no prior
  `GET`, when `GET /api/compass?as_of=E` is called twice in sequence, then the first call mints exactly
  one manifest row (`mode: retrospective`, 200) and the second call adds ZERO further rows to
  `next_session_manifests` (still exactly one row for as_of=E) — proving the reorder preserves the
  pre-existing create-once-on-GET path unmodified.
- TC-6: given the live canonical database's 2025-04-15 manifest (frozen in iter-26, its underlying run
  intact), when `GET /api/compass?as_of=2025-04-15` is requested twice, then both responses are 200,
  `basis.status == "available"`, the two responses are byte-identical, and read-only row counts on
  `next_session_manifests`, `scanner_runs`, and `daily_prices` taken AFTER the requests equal the counts
  taken immediately before them (zero rows added, removed, or changed).
- TC-7: given the live canonical database's 2026-08-12 frontier manifest (`mode: at_ingest`, `version: 1`),
  when `GET /api/compass?as_of=2026-08-12` is requested, then the response is 200 with its previously
  recorded `mode`/`version`/`manifest_hash` unchanged, and before/after row counts on
  `next_session_manifests`, `scanner_runs`, and `daily_prices` are identical.
- TC-8: given the live canonical database's manifest-less as-of dates inside the incident window
  (enumerated read-only by the dev handoff, never hardcoded in the spec), when this iteration's full
  test/browser-qa plan runs to completion, then none of those dates is ever requested via
  `GET /api/compass`, `?asof=` on `/`, or `POST /api/compass/regenerate`, and a read-only count of
  `next_session_manifests` rows WHERE `as_of` is one of those dates is identical (and zero-growth) before
  and after the iteration.
- TC-9: given the reordered route, when `GET /api/compass?as_of=not-a-date` and
  `GET /api/compass?as_of=<a date after the latest data date>` are each requested, then the response
  status codes are unchanged from pre-fix behavior (422 unparseable / 400 future respectively) for both
  the fast (existing-manifest) and slow (create) branches.
- TC-10: given the fixture DB's current frontier as-of with no manifest minted yet, when a non-finalize
  `GET /api/compass` call is made for that as-of, then it still raises `ManifestNotYetFrozen` and the route
  still returns HTTP 404 — proving `get_or_create_manifest`'s J-05-step-7 frontier guard is unaffected by
  the refactor.

## NOTES

- Lessons applied: iter-26 ("a green unit test on a branch no request can reach is an honesty gap, not
  coverage" — this spec requires proving TC-2 through the literal route function, not a new isolated unit
  branch); iter-23b (a `.db` file checksum alone does not prove no mutation — TC-6/7/8's row counts must be
  taken AFTER every lane finishes, bracketing `.db`/`-wal`/`-shm` if a file-level check is also used);
  iter-24/24b (a spec's own prose can silently break the replay-lane journey parser — `Target journeys:`
  and `Required-still-passing journeys:` above are each kept on one physical line with their `J-NN` ids on
  that line, per the pump coordinator's note).
- Carry-forward, none blocking, none in scope this iteration: TC-15 AST scanner strengthening
  (`test_manifest_invariants.py:155`); J-04's screenshot re-take (ninth round owed); J-05/J-06 walkthrough
  recordings; the four leftover export files (must NOT be deleted, per the TC-10 finding carried in
  "Do not redo"); J-09's ~2.99 GB acceptability question; the four older owner questions (J-06 wording,
  J-01 test steps, empty "next-session focus", MNST).
- Standing framework note carried forward: `goal_gate.py`'s duplicate-journey-heading defect is still
  unfixed and must be closed before any `GOAL_ACHIEVED` certification (not this session's product code).
- `CHAIN_REQUIRE_FULL_DEPTH` and `CHAIN_MAINTENANCE_ISOLATION` remain OFF per standing guidance; this spec
  does not set `Depth enforcement: required` or `Maintenance isolation: required` — see BACKGROUND for why
  the owner may want to add the former given the depth-demotion history this session.
