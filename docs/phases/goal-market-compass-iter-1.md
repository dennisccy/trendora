# Goal Iteration 1 — Sector attribution: pool-CSV fallback + methodology disclosure (J-01)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 1
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — cross-cutting: the fallback wiring touches config (`UniverseCfg` + `config.yaml`), the engine's single sector-writing module (`scoring.score_stocks`), the methodology content producer (`app.engine.methodology`), and the `/methodology` frontend page — four modules whose combined interaction (alias resolution, staying descriptive-only/isolated from every score input, and disclosure rendering) has no single existing test today. (Triggers 3 and 4 were checked and do not hold: last verdict was CONTINUE, and the consecutive-lean counter is 0/6.)
- **Frontend Present:** yes
- **Target journeys:** J-01
- **Required-still-passing journeys:** none — no market-compass journey (J-01..J-08) is yet `passing` (iter-0 baseline: 0 passing / 1 partial / 7 failing); this iteration's own regression proof is the byte-identity fixture (TC-4) plus the existing backend unit suites for the modules it touches.
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

On `/stocks`, wire a pool-CSV fallback into the single stored sector field so at most 5% of resolved
members show "Unassigned" (down from 78.4%), and disclose the two-source sector basis on `/methodology`
— with every stock's leadership/entry/risk scores proven byte-identical before and after.

## BACKGROUND

iter-0's baseline (verdict CONTINUE) measured J-01 as the session's only `partial` journey: the honesty
rails already hold (`ScannerResult.sector` is the single stored source; unknown serves `null`/"Unassigned";
leaderboard, stock detail, and `GET /api/stocks` already agree — binding "Do not redo"), but coverage sits
at 21.6% resolved (78.4% "Unassigned") against the ≤5% target, and the `/methodology` two-source disclosure
is entirely absent. The evaluator's next-step recommendation explicitly named J-01 next, at full depth.
Per the priority rubric: no journey regressed (rule 1); no `coherence.md` exists yet, so no consolidation
gate applies (rule 2); J-01 is goal.md's own named unblocker ("unblocks candidate sector context" for
J-04's future candidate cards) (rule 3); it is the smallest well-scoped unit available next relative to the
J-02/J-03/J-04 engine cluster and the J-05/J-06 manifest pair (rule 4); it carries exactly one non-trivial
change surface — the descriptive sector fallback — so no risky-journey bundling occurs (rule 5); nothing is
human-blocked (rule 6); this is real code work, not evidence-only (rule 7).

Ground truth, confirmed live against the repo this iteration (not just goal.md's snapshot): `config.stock_sectors`
covers all 122 curated `universe.symbols` (config-validator enforced), but the SCORED run universe is the much
larger point-in-time-resolved candidate pool (`app.engine.universe_resolver.resolve_members`, 541 members in
the latest run) — pool-only names get `sector: null` today because `scoring.score_stocks` (`apps/backend/app/engine/scoring.py:445`)
reads only `cfg.stock_sectors`. `apps/backend/data/seed/universe_pool.csv` carries a `sector` column for all
548 pool names, and its 11 distinct sector names are confirmed identical, verbatim, to `config.etfs.sector`'s
11 values — so `universe.pool_sector_aliases` legitimately defaults to an empty/identity mapping today; the
fallback is a straight pool-CSV read unless a future pool refresh introduces a name mismatch. `/methodology`
(`app.engine.methodology._universe_selection`, served at `GET /api/methodology`) has no sector-basis content
at all yet — confirmed by a direct grep.

Lesson applied (iter-0, evidence quality): absence/coverage claims need a DOM sweep or API cross-check, not
a single screenshot. J-01's own steps already require exactly this — the Unassigned-share assertion, the
two-ticker cross-surface spot-check, and the null-symbol API check below (TC-1, TC-2, TC-3) all cross-check
against `GET /api/stocks` directly, never a screenshot alone.

Depth is full per the evaluator's binding recommendation. Trigger 3 (prior ESCALATE) and trigger 4 (hardening
cadence, currently 0/6) do not hold; trigger 1 (structural/cross-cutting) does — see the Full trigger line
above. This also happens to be the session's first-ever landed product change, matching goal.md's own
loop-mechanics rule ("full when an iteration first lands user-visible UI changes"); the reconciliation between
that framing and the numbered trigger used for the metadata line is logged in
`runs/goal-session-market-compass/state/assumptions.md` (iter-1 entry).

## IN SCOPE

### Backend
- [ ] Add `universe.pool_sector_aliases` (a `dict[str, str]`, default empty) to the `UniverseCfg` config
      model (`apps/backend/app/config.py`, ~line 56) and to `config.yaml`'s `universe:` block, per goal.md's
      Product Shape and Constraints sections.
- [ ] Add a ticker → pool-CSV-sector lookup alongside the existing `universe_screen.read_pool()` reader
      (`apps/backend/app/engine/universe_screen.py`) so `scoring.score_stocks` resolves the fallback from
      the ONE existing pool-CSV parser — never a second CSV-reading implementation.
- [ ] In `scoring.score_stocks`'s row assembly (`apps/backend/app/engine/scoring.py:445`, the `"sector"`
      field), fall back to the pool sector — passed through `universe.pool_sector_aliases` (identity today)
      — only when `config.stock_sectors` has no entry for the ticker. Leave `Stock.sector_id`,
      `stock_sector_etf`, and every `rs_sector` / score input completely untouched: this field stays
      descriptive-only, exactly as it is today for curated-map names.
- [ ] Extend the methodology universe/data section (`apps/backend/app/engine/methodology.py`,
      `_universe_selection` or a sibling section, served at `GET /api/methodology`) with the two-source
      sector-basis disclosure: curated `config.stock_sectors` first, `universe_pool.csv` fallback second,
      and the current-only limitation (no point-in-time sector history — B-114 stays open and is referenced,
      not implemented). Source the prose from config (`config.methodology.*`), following this module's
      existing config-ref pattern — never a hardcoded string outside config.

### Frontend
- [ ] Render the new methodology disclosure field/section on `/methodology`
      (`apps/frontend/app/methodology/page.tsx`), following the existing `UniverseSelectionCard`-style
      pattern for a new config-backed subsection.
- [ ] No change to `/stocks` (`apps/frontend/app/stocks/page.tsx`) — its Sector cell and "Unassigned" filter
      already read the stored value as-is (binding "Do not redo"); it will show materially fewer
      "Unassigned" rows once the backend fallback lands, with zero code change on that page.

### New user-facing capability
On `/stocks`, far fewer names show "Unassigned": pool-only names that were never in the curated sector list
now show their real sector, with the same honesty guarantee unchanged — a name absent from BOTH sources
still shows "Unassigned", never a guess.

### New information displayed
`/methodology`'s universe/data section gains a short, config-backed disclosure naming the two-source sector
basis (curated list first, pool-CSV fallback second) and stating it is current-only (no historical
point-in-time sector, B-114 referenced).

### New user actions
None — no new buttons, forms, or controls. This is a data-completeness and disclosure change over existing
surfaces.

### UI surface changes
`/methodology` universe/data section gains one new disclosure subsection (existing card, new content).
`/stocks` leaderboard Sector column and Sector filter are visually unchanged but populated far more
completely; the stock detail header is likewise unchanged in layout.

### Product surface delta
The product looks the same. The DATA behind `/stocks`' Sector column/filter is materially more complete
(≤5% Unassigned vs. 78.4% before), and `/methodology` is more transparent about how that data is sourced
and its current-only limitation.

### Blueprint conformance
No new page, route, or nav entry. This work lives entirely under `blueprint.md`'s existing "J-01 sector
attribution" row — canonical home `/stocks` (leaderboard Sector cell + "Unassigned" filter), stock detail
header, and `/methodology` (two-source disclosure) — under the Stocks / Methodology nav sections. No IA edit
needed.

### Data-contract additions
None. The "Stock sector label" row already exists in `blueprint.md`'s Data Contract, already anticipating
this exact change (its Notes column already reads: "today: `config.stock_sectors` only ...; J-01 [TARGET]
adds a pool-CSV fallback via `universe.pool_sector_aliases`"). This iteration extends the SAME computing
module (`scoring.score_stocks`) and SAME serving endpoints (`GET /api/stocks`, `GET /api/stocks/{ticker}`)
in place — no second computation path, no new endpoint, no new field name. `blueprint.md` needs no edit;
the row's `[TARGET]` marker is a status the evaluator resolves after verifying this iteration, not something
this spec changes.

## OUT OF SCOPE

- J-02 through J-08 (session delta engine, plain-English summary, next-session candidate selection, manifest
  freeze/immutability, Today page, Market relocation) — deferred; goal.md's suggested build order runs the
  J-02/J-03/J-04 engine cluster next, after J-01.
- B-114 (point-in-time sector history) — stays open; this iteration only discloses the current-only
  limitation on `/methodology`, it does not implement historical sector tracking.
- Any change to `Stock.sector_id`, `stock_sector_etf`, or any `rs_sector` / leadership / entry_quality / risk
  score input — TC-4 (byte-identity fixture) is the proof this stayed untouched.
- Any change to `config.stock_sectors`'s curated 122-name mapping, `universe.symbols`, `universe.filters`
  screening thresholds, or the point-in-time membership resolver (`universe_resolver.resolve_members`) —
  none of these are implicated by a descriptive-field fallback.
- Backlog cards B-306 (engine-identity stamping), B-802 (rule distances), B-804 (score diff), B-1205
  (stamped exports) — scoped to this session's J-05 manifest work, not this iteration.
- The `compass.*` / `provenance.*` config namespaces and the manifest JSON schema file — J-05 territory.
- Populating any `universe.pool_sector_aliases` entries beyond the empty default — today's 11 pool sector
  names already equal `config.etfs.sector`'s 11 names verbatim; inventing alias entries that resolve nothing
  is unnecessary scope.

## DEFINITION OF DONE

- [ ] TC-1 through TC-8 all hold
- [ ] J-01 passes via browser-qa-agent (TC-1 coverage, TC-2 cross-surface consistency, TC-3 honest null,
      TC-5 methodology disclosure)
- [ ] Required-still-passing journeys: none tracked this iteration (see Goal Mode Metadata) — no regression
      check is owed beyond this iteration's own unit-test suite
- [ ] No anti-goal violation introduced (AG-3 correctness — TC-1/TC-2; AG-8 resilience — TC-7; AG-9
      offline-determinism — the pool CSV is a committed local file, no network call is added)
- [ ] Unit tests pass; no regressions (`test_scoring.py`, `test_sectors.py`, `test_methodology.py`,
      `test_api_methodology.py`)
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-1-dev.md`, citing TC-4 (byte-identity
      fixture) and TC-1 (coverage) by their actual test names

## TESTING REQUIREMENTS

- Browser: J-01 (all six steps — the seed-safe Remove of the last two trading days on `/data` followed by
  a backfill over the same range to produce a fresh run under the new mapping is a REQUIRED precondition
  for TC-1/TC-2/TC-5, using the existing `/data` panel, not new capability).
- Unit/integration: TC-1 (coverage), TC-2 (cross-surface consistency), TC-3 (honest null, both sources
  absent), TC-4 (byte-identity fixture over leadership/entry_quality/risk/bucket/setup_status), TC-5
  (methodology disclosure content), TC-6 (alias-identity no-op), TC-7 (resilience on an unresolvable pool
  sector name), TC-8 (historical rows unchanged).
- Error cases: a symbol in neither `config.stock_sectors` nor the pool CSV must serve `sector: null` (never
  a fabricated value — TC-3); a pool sector name that does not resolve to a valid `etfs.sector` value must
  degrade to "Unassigned" rather than crash or display an unrecognized string (TC-7, AG-8).

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps to at
least one concrete scenario line, numbered sequentially, of exactly this shape:

- TC-1: given the seed-safe Remove panel on `/data` has cleared the last two trading days of snapshots and a
  backfill has re-run that exact range, when `GET /api/stocks` is fetched at the new latest as-of, then the
  fraction of resolved members with `sector: null` is at most 0.05 (it was 0.784 before this iteration).
- TC-2: given ticker DELL (mapped in `config.stock_sectors`) and one previously-"Unassigned" pool-only
  ticker now covered by the fallback, when the `/stocks` leaderboard Sector cell, the `/stocks/{ticker}`
  detail header, and `GET /api/stocks` are each read for the same as-of, then all three surfaces render the
  identical stored sector string for each of the two tickers.
- TC-3: given a ticker present in neither `config.stock_sectors` nor `universe_pool.csv`'s sector column,
  when `GET /api/stocks` is fetched for that ticker, then the response field reads `sector: null` and the
  `/stocks` row renders "Unassigned".
- TC-4: given the same as-of date scored before and after the pool-CSV fallback is wired, when a fixture
  compares every stock's `leadership`, `entry_quality`, and `risk` score objects, `bucket` fields, and
  `setup_status` between the two runs, then every value is byte-identical.
- TC-5: given `GET /api/methodology` is fetched after this iteration, when the universe/data section of the
  response is inspected, then it contains a disclosure naming both sources (curated `config.stock_sectors`
  first, `universe_pool.csv` fallback second) and states the mapping is current-only with no point-in-time
  sector history.
- TC-6: given `universe.pool_sector_aliases` is left at its default empty mapping, when a pool-only ticker's
  fallback sector is resolved, then the served `sector` value equals the pool CSV's `sector` column value
  for that ticker unchanged (no alias substitution applied).
- TC-7: given a synthetic fixture where a pool sector name is not a member of `etfs.sector`'s valid set,
  when that ticker's descriptive sector is resolved, then the system serves `sector: null` / renders
  "Unassigned" rather than raising an exception or displaying an unrecognized string.
- TC-8: given a stored `ScannerResult` row from a run created BEFORE this iteration's backfill, when its
  sector is re-read after this iteration ships, then its stored value is unchanged from before (historical
  rows are not rewritten by this journey).

## NOTES

- Binding "Do not redo" from `iteration-state.md`: J-01's honesty half already holds — `ScannerResult.sector`
  is the single stored source, unknown serves `null`/"Unassigned", and leaderboard / stock detail /
  `GET /api/stocks` already agree (DELL, GRMN spot-checked at baseline). Do not re-verify or re-implement
  that half; this iteration is scoped to exactly the three remaining gaps iter-0 named: the pool-CSV fallback
  wiring, the `/methodology` two-source disclosure, and the score byte-identity fixture.
- `universe.pool_sector_aliases` is a required config namespace per goal.md's Constraints section even though
  it defaults to an empty/no-op mapping today (11/11 pool sector names already match `etfs.sector` verbatim)
  — it exists so a future pool-CSV refresh with a mismatched sector name has somewhere to be normalized
  without a code change.
- An assumption-ledger entry was appended this iteration
  (`runs/goal-session-market-compass/state/assumptions.md`, "iter-1 — goal-decomposer") recording how the
  Full-trigger numbering was reconciled with goal.md's own "first user-visible UI" full-depth rule.
- Suggested next iteration after this one (per goal.md's own build order and iter-0's evaluator
  recommendation): the J-02/J-03/J-04 engine cluster (session delta, plain-English summary, next-session
  selection) sharing one manifest producer, likely also full depth on first landing — or J-05/J-06 if the
  decomposer judges the cluster too large for one iteration at that time.
