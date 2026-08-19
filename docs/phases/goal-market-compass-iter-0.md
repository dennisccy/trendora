# Goal Iteration 0 — Baseline verification of all market-compass journeys

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08
- **Required-still-passing journeys:** None (baseline iteration — no journeys previously verified this session; all 8 Must-have journeys are targets)
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

Establish the honest baseline state of all 8 market-compass Must-have journeys (J-01–J-08) against
the current codebase, with zero code changes, so the evaluator can classify each as
already-passing, partial, or failing before any compass feature work begins.

## BACKGROUND

This is iteration 0 of a new goal session (`market-compass`) layered on top of the `ops-hardening`
session (GOAL_ACHIEVED 2026-08-14, 8/8 journeys, archived at `docs/archive/goal-ops-hardening.md`)
— the underlying research platform (scanner, dashboard, evidence ledger, data manager) is stable
and unchanged; this cycle adds a new decision surface (the Today compass + next-session manifest)
on top of it. Direct codebase inspection (grep/find across `apps/backend/app/engine/`,
`apps/backend/app/api/`, `apps/backend/app/models.py`, `apps/frontend/app/`,
`apps/frontend/components/sidebar.tsx`) confirms no `compass` engine module, no
`next_session_manifests` table, and no `/api/compass` route exist anywhere in the backend; no
`/market` route exists in the frontend; and the sidebar's nav array still opens with
`{ href: "/", label: "Dashboard" }`, not "Today". goal.md's own Ground Truth section (measured
2026-08-19 @ `42167cf5`) additionally records the known sector-attribution gap that J-01 targets
(424/541 = 78.4% of the latest run's members NULL under `config.stock_sectors` alone, confirmed at
`scoring.py:445`). Per the baseline-mode rubric this is a verify-only iteration: lean depth, the
developer agent is a no-op, and the value comes entirely from browser-qa-agent running all 8
journeys against current state so the evaluator can seed `journey-history.json` accurately. No
`lessons.md` or `assumptions.md` entries exist yet for this session (first iteration) — none to
apply.

## IN SCOPE

### Backend
- None — this is a verify-only baseline iteration; no code changes.

### Frontend
- None — this is a verify-only baseline iteration; no code changes.

### Verification (browser-qa-agent)
- [ ] With backend and frontend running via the project's prod scripts, execute J-01 (sector
      attribution honesty) against `/stocks`, the stock detail header, and `/methodology`; record
      the current Unassigned share and a pass/fail/partial verdict with evidence.
- [ ] Execute J-02 (what-changed deltas) against `/` at the latest as-of; record whether any
      What-changed card exists and its verdict.
- [ ] Execute J-03 (plain-English summary) against `/`; record whether any summary/cited-facts
      card exists and its verdict.
- [ ] Execute J-04 (next-session candidates, why/why-not) against `/`; record whether any
      Next-session focus section exists and its verdict.
- [ ] Execute J-05 (manifest freeze) against `GET /api/compass` and `/data`; record the HTTP
      result and verdict.
- [ ] Execute J-06 (manifest immutability) as far as J-05's baseline result permits; record the
      verdict and the blocking reason if the manifest producer does not yet exist.
- [ ] Execute J-07 (Today ten-second read) against `/` top to bottom; record which of the six
      required sections (state band, summary, what-changed, rotation, focus, manifest strip) are
      present today and which are not.
- [ ] Execute J-08 (market relocation + history) against `/market` and the sidebar; record the
      HTTP/route result and the current sidebar order.

### New user-facing capability
None this iteration — zero code changes.

### New information displayed
None this iteration — zero code changes.

### New user actions
None this iteration — zero code changes.

### UI surface changes
None this iteration — zero code changes.

### Product surface delta
None this iteration — the product experience is unchanged; this iteration only measures the
current experience against the 8 target journeys' acceptance criteria.

### Blueprint conformance
No new surfaces. `runs/goal-session-market-compass/state/blueprint.md` is drafted this iteration
as the target-state coherence contract (Information Architecture + Data Contract) that future
iterations build into — it is a planning artifact, not a shipped surface.

### Data-contract additions
None this iteration (zero code changes). The target-state contract values this session will
eventually introduce (next-session manifest, engine identity, extended stock-sector resolution)
are pre-registered in `blueprint.md`'s Data Contract table, each tagged `[TARGET]`, for the
iterations that build them.

## OUT OF SCOPE

- Implementing any compass engine module, the `next_session_manifests` table, `GET /api/compass`,
  or the `/`↔`/market` page relocation — that begins in iteration 1+ per the priority rubric
  (goal.md's own Loop mechanics section suggests: J-01 sector wiring first, then the engine
  cluster J-02/J-03/J-04, then the freeze/integrity pair J-05/J-06, then the surface pair
  J-07/J-08; the decomposer may re-order with reasons in later iterations).
- Fixing the sector-attribution gap or any other issue this baseline surfaces — this iteration
  only records state, it does not remediate it.
- Running the full backend pytest suite — goal.md's Constraints section states new tests are
  "synthetic-fixture, file-scoped (the full suite takes hours and is never run by pipeline
  agents)"; there is nothing to test this iteration since no code changes.
- Editing `blueprint.md` beyond this iteration's initial baseline draft.

## DEFINITION OF DONE

- [ ] J-01 through J-08 each executed via browser-qa-agent against the current running app and
      each recorded as passing, failing, or partial with cited evidence (screenshot and/or API
      response) — TC-1 through TC-8
- [ ] No anti-goal violation observed in current UI/API text during the verification pass — TC-9
- [ ] Zero backend/frontend files modified this iteration (`git status --porcelain apps/` is
      empty) — TC-10
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-0-dev.md` stating "no code
      changes — baseline verification only" plus a pointer to the browser-qa evidence — TC-11

## TESTING REQUIREMENTS

- Browser: J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08 — run all 8 against the current app; no
  journey is skipped even though most are expected to be unimplemented (baseline must record the
  honest current state either way).
- Unit/integration: none — verify-only iteration, zero code changes, nothing new to test.
- Error cases: none — no new code paths introduced.

Test-first contract:

- TC-1: given the latest stored scanner run, when `/stocks` is opened and its Sector filter is set
  to "Unassigned" while `GET /api/stocks` is queried at the same as-of, then the Unassigned share
  of resolved members and the count of rows with `sector: null` are both recorded as the baseline
  figures.
- TC-2: given `/` is loaded at the latest as-of, when the page finishes rendering, then the
  browser-qa-agent records whether a "What changed" card is present in the DOM; its absence is
  recorded as a concrete finding (current `/` is the legacy dashboard, not the compass).
- TC-3: given `/` is loaded at the latest as-of, when the page finishes rendering, then the
  browser-qa-agent records whether a plain-English summary card with a "Show cited facts"
  disclosure is present in the DOM.
- TC-4: given `/` is loaded at the latest as-of, when the page finishes rendering, then the
  browser-qa-agent records whether a "Next-session focus" section with candidate cards is present
  in the DOM.
- TC-5: given the backend is running, when `GET /api/compass?asof=<latest>` is requested, then the
  HTTP status code and response body are recorded (a 404 or route-not-found result is a valid,
  concrete baseline finding).
- TC-6: given TC-5's result, when a second `GET /api/compass` request is issued for the same
  as-of, then either both responses are byte-identical (manifest exists) or both fail identically
  with the same status (manifest producer absent) — either observable outcome is recorded.
- TC-7: given `/` is loaded, when its rendered section order is read top to bottom, then each of
  the six required sections (market-state band, plain-English summary, What changed, Leadership
  rotation, Next-session focus, manifest strip) is individually recorded as present or absent.
- TC-8: given the app is running, when `/market` is requested in the browser and the sidebar DOM
  is inspected, then the HTTP/route result for `/market` and the current first-listed sidebar
  entry's label and href are both recorded.
- TC-9: given the current running app, when browser-qa-agent captures the visible text of `/`,
  `/stocks`, `/methodology`, and `/evidence`, then the count of occurrences of banned anti-goal
  tokens (imperative trade verbs, forecast wording, composite-score words such as
  "conviction"/"fit"/"match", and readiness tokens "Ready"/"GO"/"DEGRADED"/"NO-GO" appearing
  outside system chrome) is recorded and is zero.
- TC-10: given the iteration pipeline completes, when `git status --porcelain apps/` is run, then
  its output is empty.
- TC-11: given the iteration pipeline completes, when
  `docs/handoffs/goal-market-compass-iter-0-dev.md` is read, then it exists and its text states
  that no code changes were made and links to the browser-qa evidence for J-01–J-08.

## NOTES

- Depth is lean per baseline-mode rules (no triggers evaluated at baseline) and matches the
  evaluator's binding recommendation for this iteration — no conflict.
- The lean cycle for baseline is developer (no-op) → reviewer (no-op) → browser-qa-agent; the
  browser-qa-agent's 8-journey pass is the entire deliverable.
- Start backend and frontend via the project's prod scripts (per `.claude/project-template.md`
  Service Start Commands) before running browser-qa — J-01 step 1 in goal.md explicitly requires
  "backend and frontend running (prod scripts)" and the other journeys assume the same running
  state.
- `runs/goal-session-market-compass/state/blueprint.md` was drafted this iteration per baseline
  instructions; it is auto-approved by default (pass `--require-blueprint-approval` to pause for
  human review before iteration 1).
- Escalation flag: none. This is a routine baseline pass; no blocker or ambiguity was found that
  needs owner attention before iteration 1 can be planned.
