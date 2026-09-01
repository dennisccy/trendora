# Project Goal

> This goal drives the **market-compass loop** for Trendora. Lineage: the original product
> goal is archived at [`docs/goal-product.md`](goal-product.md); the decision-quality/evidence
> goal (GOAL_ACHIEVED 2026-07-16, session `mcp-loop`) at
> [`docs/archive/goal-mcp-loop.md`](archive/goal-mcp-loop.md); the operational-hardening goal
> (GOAL_ACHIEVED 2026-08-14, 8/8 journeys, session `ops-hardening`) at
> [`docs/archive/goal-ops-hardening.md`](archive/goal-ops-hardening.md). This file evolves
> Trendora from *"operationally solid research platform"* to *"a simple, auditable
> next-session Market Compass over that platform"*. Session id: `market-compass`.

## Vision

Trendora's research platform is unchanged underneath. This cycle adds the decision surface
on top of it: a **Today** page that answers, in roughly ten seconds after the close, *what
kind of market this is, whether it is improving or deteriorating, what materially changed
since the previous session, where leadership is rotating, and which names deserve attention
next session — with the reasons, the cautions, and the why-nots stated*. Each close, that
prior is **frozen into an immutable, versioned, provenance-stamped next-session manifest**
(with frozen comparison and near-threshold shadow cohorts recorded for future prospective
evaluation, and a fail-closed prospective-eligibility flag) and exported as
a local JSON artifact that the owner's separate intraday project (Tapeology) can later
consume through its own rails. Everything is deterministic and template-generated from
stored values — no LLM, no new composite scores, no fabricated causes. The deep research
surfaces all remain, one click away.

## Target Users

The same self-directed, quant-minded owner — now in the role of an **evening
decision-maker** running a post-close ritual ("what is the market telling me; what deserves
attention tomorrow; what should Tapeology confirm or reject") and as the **operator of the
Trendora → Tapeology handoff**. Secondarily: any future machine consumer of the exported
manifest artifact (it must be self-describing and self-caveating).

## Success Criteria

- From `/` alone, without navigating, a reader (or browser agent) can identify: system
  readiness + preflight state; market regime label and score; market phase, severity, and
  stress direction; breadth level and direction; the material changes vs the named prior
  session (or an honest empty state); the top sector/theme movers in both directions; the
  next-session candidates each with structured reasons AND cautions; the most-nearly-eligible
  why-not names; and the manifest's mode and freeze timestamp.
- Every at-ingest close produces exactly one frozen manifest version whose export file bytes
  equal the stored payload, carrying schema/rule/engine/dataset/universe stamps, and the twelve
  manifest invariants (time-safety, immutability, reproducibility, create-once, mode honesty,
  cohort reproducibility, fail-closed prospective eligibility, availability-fence validity,
  artifact integrity, rule-identity separation, disposition partition, schema conformance) are
  each covered by a named passing test.
- Every manifest freezes three cohorts — the candidates, the comparison cohort (the full
  non-selected pool), and the near-threshold shadow — plus a `prospective_eligible` flag
  derived fail-closed at write time; a retrospective or regenerated manifest is never
  `prospective_eligible: true`; every comparison member carries the same frozen matching
  context as the shadow rows plus a closed-vocabulary selection disposition whose tallies
  partition the cohort exactly.
- The manifest carries a conservative `available_at_utc` availability fence and dual
  identities — `content_hash` (research-content reproducibility) and `manifest_hash`
  (whole-artifact integrity) — split rule identities (`candidate_rule_hash`,
  `cohort_rule_hash`), and validates against the committed machine-readable schema at
  `docs/handoffs/trendora-next-session-manifest-v1.schema.json`.
- Sector attribution covers ≥ 95% of resolved members on newly produced runs (from ~22%
  today), with unknown still rendered "Unassigned" and the current-only basis disclosed.
- `/` joins `reports/perf-budgets.md` and stays within its committed budgets; warm
  `GET /api/compass` reads perform zero producer calls (call-count instrumentation).
- Zero new proven-language anywhere; the language test (no imperative trade verbs, no
  forecast wording, no causal attribution beyond stored rule reasons) is green.
- Nothing is removed: `/market` renders the complete former dashboard inventory and every
  existing surface remains reachable.

## Key Capabilities

1. **Today compass** — the new default `/` page: system strip (existing), market state in
   plain words, deterministic summary, what-changed, leadership rotation, next-session
   focus with why/why-not, manifest strip.
2. **Session delta engine** — meaningful changes between consecutive stored runs
   (market / breadth / sector / theme / stock levels), config-thresholded, honest empties.
3. **Deterministic plain-English summary** — template sentences composed engine-side from
   stored facts, each carrying its template id and cited facts; golden-tested.
4. **Transparent next-session selection** — a config-versioned attention rule over stored
   scores with a full met/unmet trace, reasons, cautions, rule distances, and why-not.
5. **Immutable next-session manifest** — append-only, versioned, provenance-stamped
   (engine identity, rule hash, dataset stamp, universe basis), frozen at ingest for the
   frontier date, exported as a byte-consistent JSON artifact; survives rebuild/removal;
   freezes the candidates plus a comparison cohort (the full non-selected pool) and a
   near-threshold shadow cohort, with a fail-closed `prospective_eligible` flag; carries a
   conservative `available_at_utc` availability fence, dual hashes (`content_hash` research
   identity, `manifest_hash` artifact integrity), split rule identities
   (`candidate_rule_hash` / `cohort_rule_hash`), and a committed machine-readable schema
   contract.
6. **Sector attribution coverage** — pool-sector wiring closing the 78%-Unassigned gap on
   new runs, descriptive-only, honestly disclosed.
7. **Market page** — the relocated deep market context (cross-view chart, phase detail,
   breadth cards, top lists), intact.

## Non-Goals

- No companion / small-mid-cap universe this cycle (Track 7's B-701 audit is the future
  gate); the manifest carries a `universe_profile` slot defaulting to `core` so a future
  isolated profile needs no schema change.
- No stock-level short/weakness selection model (group-level weakening deltas only).
- No alerting or message delivery (B-302 stays in the backlog).
- No LLM or generative text anywhere; no news/sentiment; no intraday/tick data.
- No order placement, position sizing, portfolio logic, or trade simulation.
- No modifications to the Tapeology repository, and no code/network coupling to it.
- No cryptographic signing or PKI (the integrity hash detects corruption and accidental
  mutation, not adversarial forgery — explicitly out of scope), and no exchange-calendar
  subsystem (session-boundary prospectivity is owned by the future preregistered study).
- No new factors, indicators, patterns, or macro-leg enablement; no new composite scores.
- No incremental-value experiment yet — this cycle only records the prospective substrate
  (at-ingest manifests + frozen comparison and near-threshold cohorts); the experiment is a
  future goal following Tapeology's registration methodology, and no causal claim may be
  made from candidate-vs-cohort differences without that separately registered experiment.

## Constraints

- Local-first, deterministic, offline against the committed seed; **strict no-lookahead**
  preserved (scoring uses bars ≤ as-of; forward returns use bars > as-of; the manifest for
  close D derives only from the stored run at D and earlier stored state).
- **All "proven" status flows from the evidence ledger**; nothing in this cycle introduces
  proven-language or an Evidence Claim (the post-decompose referee gate passes automatically
  every iteration; AG-1/AG-4/AG-6 still veto).
- **Compute-at-ingest**: the manifest freeze and everything the compass serves are produced
  in the ingest finalize tail or by create-once, and served from storage; no request-path
  recompute (warm reads perform zero producer calls).
- **Config-only thresholds**: every new threshold, word map, band edge, cap, and path lives
  under `config.yaml` (`compass.*`, `provenance.*`, `universe.pool_sector_aliases`); the
  three new engine modules join `test_no_magic_numbers.CALC_FILES`.
- **Append-only manifest store**: `next_session_manifests` joins neither
  `clear_snapshot_set` nor the remove-data cascade; no UPDATE path may exist.
- New tests are synthetic-fixture, file-scoped (the full suite takes hours and is never run
  by pipeline agents); frontend logic tests are plain node scripts under
  `apps/frontend/lib/*.test.ts`.
- **Host resource-fit (owner, 2026-08-20 — binding, after the desktop-freeze incident)**:
  this is a 26.7 GB host shared with a desktop session and a sibling project; a goal-mode
  run froze it via memory overcommit + swap-thrash. Standing rules, to land in the nearest
  applicable slices (J-09 carries the config half):
  (a) the three `*_memory_pressure` test modules (`test_evidence_drawdown_memory_pressure.py`,
  `test_samples_memory_pressure.py`, `test_ingest_finalize_memory_pressure.py`) skip by
  default behind an explicit `TRENDORA_MEMORY_PRESSURE=1` opt-in, and — like
  `test_start_backend_script.py`'s three copy sites — must stop copying the live 7.8 GB
  `data/trendora.db` (synthesize or subset a small DB instead); a targeted run without the
  env completes in seconds as skips;
  (b) the production `next build` is bounded to ≤ 4 workers (`experimental.cpus` or the
  Next-15 equivalent in `next.config.mjs`) — today it fans out 16-way;
  (c) `_BarCache.prefill`'s cold path is re-bounded to a configured memory budget (AG-8
  restored) — read the iter-43 handoff FIRST and preserve whatever correctness reason
  motivated its unbounding; if that reason conflicts with the bound, stop and surface it
  for owner review instead of guessing.
- **Destructive-drill isolation (owner, 2026-08-20 — recorded defect + future direction, NOT this
  cycle's build):** iter-5 proved that a destructive QA drill can permanently mutate the canonical
  working dataset when the committed seed cannot completely restore it (the drill removed
  2026-08-11/2026-08-12; the seed window ends 2026-07-01, so nothing local could put them back).
  Destructive drills must not be able to do that. Preferred future direction: a disposable/sandbox
  DB, a transaction rollback, a snapshot/restore, a drill-specific fixture copy, or equivalent
  isolation. This is recorded as **evidence that drill isolation and recovery need hardening** — do
  NOT build that infrastructure as part of the J-10 recovery and do not expand scope to it, unless
  it is already trivial and explicitly inside a current slice.

## Design Direction

- Visual style: unchanged — minimal, data-dense, evidence-first, consistent with the
  existing Trendora UI (dark, calm, honest empty states).
- Mood: **plain words first, numbers second; change over levels; a why beside every list**.
  The compass reads like a briefing, not a terminal; every word is a served field.
- Reference: the existing glance cards, preflight banner, and methodology tooltips; the
  recovery-turn reason sentence is the voice of the narrative.

## Product Shape

### Navigation / information architecture
- Sidebar order: **Today (`/`)** | **Market (`/market`)** | Stocks | Themes | Sectors |
  Scanner Runs | Backtest | Research | Evidence | Watchlist | Methodology | Data Manager.
- `/` = the compass (state band, summary, what-changed, rotation, next-session focus,
  manifest strip). `/market` = the complete former dashboard body (glance cards, regime ×
  phase cross-view, More-detail content, full Market Phase & Severity card), relocated
  verbatim with its persisted toggles.
- The global as-of switcher governs both pages; historical dates show that date's stored
  (or labeled-retrospective) compass — never today's.

### Canonical values (single source of truth)
- **Next-session manifest** (one document per `(as_of, version)`): computed only by
  `app.engine.compass.build_manifest_payload`, persisted create-once in
  `next_session_manifests`, served only by `GET /api/compass`; the exported JSON file's
  bytes equal the stored `payload_json`. The session delta, narrative sentences, plain-word
  labels, candidate set, reasons/cautions/trace, the comparison cohort (non-selected pool,
  each member carrying its frozen matching context and `selection_disposition`), the
  near-threshold shadow cohort, the `prospective_eligible` flag, the `available_at_utc`
  fence, and both integrity hashes (`content_hash`, `manifest_hash`) are all blocks
  INSIDE this one document — no second producer, no client-side derivation; the committed
  schema at `docs/handoffs/trendora-next-session-manifest-v1.schema.json` is the
  machine-readable contract every produced manifest must validate against.
- **Engine identity**: computed only in `app.engine.engine_identity` from the config-listed
  file list + config subset; stamped on every manifest and on newly created `ScannerRun`
  rows (additive nullable column; old rows stay NULL as "pre-stamping"); displayed verbatim.
- **Stock sector label**: `ScannerResult.sector`, stored once at scan time
  (`config.stock_sectors` first, pool-CSV sector via `universe.pool_sector_aliases`
  fallback, else NULL); every surface re-reads the stored value.
- Existing canonical values unchanged: the three scores/buckets/setups, regime, phase &
  severity, breadth, sector/theme scores+ranks, readiness/preflight, evidence status,
  coverage payload, run-summary contract.

## Must-have user journeys

- **J-01: Sector attribution is honest and near-complete on new runs**
  - Steps:
    1. With backend and frontend running (prod scripts), on `/data` use the seed-safe
       Remove panel over the last two trading days of the committed basis (snapshots
       cascade away; committed bars are protected), then run a backfill over the same
       range so fresh snapshots are produced under the new mapping
    2. Visit `/stocks` at the latest as-of; select the Sector filter's "Unassigned"
       option; assert the Unassigned share of resolved members is at most 5% (it was
       ~78% before this journey)
    3. Spot-check two names — one mapped by `config.stock_sectors` and one previously
       unmapped pool name — and assert the leaderboard Sector cell, the stock detail
       header, and `GET /api/stocks` serve the same stored sector label
    4. Visit `/methodology`; assert the universe/data section now discloses the two-source
       sector basis (curated config first, pool snapshot fallback) and its current-only
       limitation (no point-in-time sector history)
    5. Assert at the API that a symbol absent from both maps still serves `sector: null`
       and renders "Unassigned" — never a fabricated sector
    6. Cite in the dev handoff the fixture test proving leadership/entry/risk scores,
       buckets, and setup statuses are byte-identical for the same as-of before and after
       the wiring (the mapping is descriptive only; `rs_sector` inputs untouched)
  - Acceptance:
    - **Consistency (single source):** `ScannerResult.sector` remains the one stored
      source, populated once at scan time in `scoring.score_stocks`; the alias map lives
      only in `universe.pool_sector_aliases`; every surface re-reads the stored value and
      no UI derives a sector.
    - **Correctness:** new-run coverage ≥ 95% of resolved members; spot-checked labels
      match their source rows; the byte-identity fixture passes.
    - **Honest status & anti-goals:** unknown stays NULL/"Unassigned" (NA over
      fabrication); the current-only basis is disclosed on `/methodology`; historical
      rows are not rewritten by this journey; B-114 (point-in-time sector honesty)
      remains open and referenced.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the shrunken Unassigned filter
      and the methodology disclosure, viewable via `demo.sh market-compass --session-live`.

- **J-02: "What changed" reports meaningful session-over-session deltas with honest empties**
  - Steps:
    1. Load `/` at the latest as-of; assert the What-changed card header names the prior
       stored session date and that date equals the run immediately preceding the current
       as-of in `GET /api/runs`, alongside the gap in days
    2. Assert every visible change entry meets its kind's config threshold
       (`compass.delta.*`), is ordered market → breadth → sectors → themes → stocks, and
       links to its drill surface carrying the current `?asof`
    3. Open the suppressed-moves disclosure; assert each suppressed entry sits below its
       kind's threshold and the suppressed count equals the number of listed entries
    4. Spot-check one sector-rank move against the stored ranks served by `GET /api/sectors`
       at the prior and current as-of dates, and one leadership-bucket crossing against
       `GET /api/stocks` rows at both dates
    5. Step the as-of switcher to the earliest stored run; assert the explicit
       no-prior-run state renders (no deltas, no direction words, a sentence naming the
       condition) — nothing fabricated
    6. Cite in the dev handoff the fixture test where a quiet pair of runs renders the
       "no meaningful changes" state with its suppressed-count disclosure, and where a
       name absent from the prior run is reported as new to the universe rather than as a
       score change
  - Acceptance:
    - **Consistency (single source):** deltas are produced once by
      `app.engine.session_delta` inside the manifest payload and served only via
      `GET /api/compass`; thresholds live only in `config.yaml`; the UI evaluates no
      threshold and computes no diff.
    - **Correctness:** spot-checked from/to values equal the stored rows for both as-of
      dates; the prior-session anchor is exactly the preceding stored run.
    - **Honest status & anti-goals:** the three empty/degraded states (no prior run,
      quiet-with-suppressed-count, NA velocity) are distinct and explicit; the prior date
      and gap are always disclosed (monthly-cadence history makes historical gaps up to a
      month); membership changes are never rendered as score deltas.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of a changes list, its suppressed
      disclosure, and the earliest-run empty state, viewable via
      `demo.sh market-compass --session-live`.

- **J-03: The plain-English summary is deterministic, cited, and never invents a cause**
  - Steps:
    1. On `/` at the latest as-of, assert the summary card renders the state sentence plus
       the direction, breadth, and focus-count sentences, each as served text
    2. Open the "Show cited facts" disclosure; assert every sentence lists its template id
       and its facts, and spot-check two fact values against the canonical endpoints for
       the same as-of (`GET /api/dashboard` regime score; `GET /api/market-phase` severity)
    3. Cite in the dev handoff the passing golden test: the same stored run pair and config
       reproduce byte-identical sentences (via the manifest `content_hash`)
    4. Assert no sentence contains a token from the committed banned-language list
       (imperative trade verbs, forecast terms, causal-attribution phrases) — the language
       test is green and its list file is committed
    5. At the earliest stored run assert the no-comparison sentence variant renders; cite
       the fixture for the NA-velocity variant (warm-up head) in the dev handoff
    6. On a retrospective compass view (any pre-frontier historical date), assert the
       summary carries the visible retrospective stamp naming that it was reconstructed
       under the current rule/config
  - Acceptance:
    - **Consistency (single source):** sentence templates and word maps live in config +
      the engine producer; sentences are stored in the manifest payload and rendered
      verbatim; no client-side text assembly.
    - **Correctness:** cited facts byte-match the canonical endpoint values for the same
      as-of; goldens reproduce exactly.
    - **Honest status & anti-goals:** every sentence's content is a stored fact or a
      config rule name — no causes appear that Trendora cannot observe; degraded variants
      render for missing comparanda; no imperative or forecast wording (AG-2 lineage).
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the summary and its cited-facts
      audit view, viewable via `demo.sh market-compass --session-live`.

- **J-04: Every next-session candidate explains why, why-not, and what would change it**
  - Steps:
    1. On `/` at the latest as-of, assert the focus section's candidate count equals the
       count served by `GET /api/compass` and the count named in the summary's focus
       sentence
    2. Open one candidate card; assert its Leadership/Entry/Risk words are the config
       word-map values for the served buckets, and its buckets and scores equal the
       `GET /api/stocks` row for that ticker at the same as-of
    3. Assert each reason and caution cites a threshold and the stored actual value;
       spot-check the ATR caution's value and percentile against the row's
       `risk_budget.atr_pct`, and assert the invalidation line renders the row's stored
       invalidation note verbatim
    4. Assert the eligibility checklist rows each carry a verdict from the fixed set
       (Pass / Miss / Supportive / Neutral / Unknown / NA) with threshold and actual, and
       that the rule-trace verdicts jointly reproduce the candidate's inclusion
    5. Assert the "what would change this" panel states each selection and qualifier rule
       with threshold, current value, and met/unmet — and cite the code-audit note that no
       rule table exists in frontend code (the trace rides the payload)
    6. Assert the "Not priority" entries each name their failed condition(s) with
       distances, and the aggregate exclusion counts partition member count minus
       candidate count for the same as-of and equal the manifest's frozen
       selection-disposition tallies (below the selection floor vs excluded only by the
       candidate cap) re-read verbatim; assert the near-threshold shadow cohort
       appears nowhere in the focus section — not as a card, a pick, or an ordering
       input (it is visible only inside the manifest audit view under its explicit
       research-only label)
    7. Using `GET /api/regime-history`, step `?asof` to a stored date whose regime label
       is Risk-off (the multi-decade history contains them; a synthetic fixture covers the
       branch otherwise); assert every candidate carries the `REGIME_RISK_OFF` caution,
       the market band reads Risk-off, and the list persists under the "worth monitoring
       next session" framing with zero entry-advice wording
    8. Cite in the dev handoff the fixture where no member clears the selection floor: the
       section renders the explicit `candidates_empty_reason` state, never a bare empty list
  - Acceptance:
    - **Consistency (single source):** the candidate set, reasons, cautions, checklist,
      and distances are all slices of the ONE `compass.evaluate_selection` trace computed
      at manifest build over stored run fields; the UI re-renders served structures and
      re-implements no rule; the existing Risk-off→no-Actionable entry gate in
      `classify_setup` is untouched.
    - **Correctness:** every cited score, bucket, percentile, and invalidation value
      equals the stored snapshot row for the same as-of; trace verdicts reproduce
      inclusion/exclusion for every spot-checked name; exclusion counts partition exactly.
    - **Honest status & anti-goals:** why-not is as visible as why; the honest-zero and
      Risk-off states are explanatory, never blank; no composite fit number exists
      anywhere; the shadow cohort is never rendered as a recommendation; no imperative
      trade verbs, no forecast language, no proven-language; the evidence chips continue
      to read their true ledger status ("Not yet proven" today).
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of one candidate's
      why/cautions/checklist/what-would-change, the why-not entries, and the Risk-off
      caution state, viewable via `demo.sh market-compass --session-live`.

- **J-05: Each close freezes one provenance-stamped next-session manifest, exported byte-consistently**
  - Steps:
    1. On `/data`, remove the last two trading days of snapshots (seed-safe) and backfill
       the same range; assert the job's finalize discloses a "next-session manifest" phase
       and the run record's "Refreshed:" line names it
    2. Assert `GET /api/compass` for the frontier date serves a manifest with
       `mode: at_ingest`, `version: 1`, `frozen: true`, `prospective_eligible: true`,
       `generation.producer: ingest_finalize`, a generation timestamp, a well-formed
       `available_at_utc` fence not earlier than the generation timestamp plus the
       configured margin, the engine identity, the split rule identities
       (`candidate_rule_hash`, `cohort_rule_hash`) and the broad `manifest_config_hash` —
       each with its verbatim config subset — the dataset stamp, the universe block (pool
       hash, resolver gate values, member count), and both `content_hash` and
       `manifest_hash`
    3. Assert the export file exists under the configured export directory and its bytes
       equal the served `payload_json` (at-ingest exports only), and that recomputing
       `manifest_hash` over the exported bytes (hash field excluded per the canonical
       rule) reproduces the embedded value
    4. Assert the manifest strip on `/` shows the same stamps and counts, and its expanded
       table equals the stored candidates, the comparison cohort (non-selected pool) whose
       count equals member count minus candidate count — each member carrying the same
       frozen matching-context fields as the shadow rows plus a closed-vocabulary
       `selection_disposition` whose tallies partition the cohort exactly — and the
       near-threshold shadow
       cohort (members with leadership in the config band from `shadow.min_score` up to
       but excluding `leadership_min_score`) carrying its frozen per-name context fields
       under an explicit research-only label
    5. Assert a `ScannerRun` created by this backfill carries `engine_identity` while an
       older run row shows the pre-stamping NULL state
    6. Re-run the identical backfill range; assert the zero-work outcome mints no new
       manifest version (create-once — still version 1)
    7. Request `GET /api/compass` for an old stored run date with no manifest; assert
       exactly one `retrospective` manifest is created (create-once on re-request) whose
       recorded frontier bar date exceeds its as-of and which carries
       `prospective_eligible: false` — and assert the frontier date's manifest can only be
       minted by the finalize freeze or an explicit regenerate, never by a plain GET
    8. Cite in the dev handoff the passing schema-conformance test: the frozen at-ingest
       manifest and the retrospective manifest both validate against the committed schema
       `docs/handoffs/trendora-next-session-manifest-v1.schema.json`, whose required-field
       set includes mode, producer, `available_at_utc`, `prospective_eligible`, both
       hashes, both rule identities, the three cohorts, and the caveats block
  - Acceptance:
    - **Consistency (single source):** one producer (`compass.build_manifest_payload` +
      `persist_manifest`), one endpoint (`GET /api/compass`), one export whose bytes equal
      the stored payload; the finalize hook follows the existing honesty-gated
      "Refreshed:" pattern; the committed schema is the single machine-readable contract;
      dispositions, cohort rows, and rule identities come from the same single selection
      trace and identity helpers — never recomputed by the UI or the export.
    - **Correctness:** the content hash reproduces across rebuilds of the same inputs
      (fixture); stamps match the computed engine identity and rule-config hash; the
      data-driven mode rule assigns `at_ingest` only when no bar later than the as-of
      exists at generation; comparison and shadow membership reproduce exactly from the
      frozen rule config plus the stored run (fixture); `content_hash` is invariant across
      legitimate generation-metadata differences while `manifest_hash` changes when any
      other field changes (fixture pair); disposition tallies partition member count minus
      candidate count exactly.
    - **Honest status & anti-goals:** mode is never fabricated (fails toward
      retrospective); no future session DATE is fabricated — the manifest states
      "next session after the based-on close" semantically; the comparison cohort is
      explicitly labeled a frozen non-selected comparison pool — not a matched or causal
      control group; `prospective_eligible` is derived once at write from the recorded
      generation facts, fail-closed (any missing condition forces false; an absent field
      reads as false); `available_at_utc` is a conservative fence — the canonical
      serialization instant plus the configured `availability_margin_seconds` — so a
      consumer never treats the artifact as available before durable publication, and
      `prospective_eligible: true` additionally requires the fence present and well-formed
      while remaining necessary but NOT sufficient for an individual downstream
      observation (the observation's event timestamp must be strictly later than the
      fence — the future study's rule); the artifact embeds its own evidence caveat ("Not
      yet proven — attention rule, not a certified edge") and survivorship/sector-basis
      caveats.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of ingest → freeze → stamps → export
      file, viewable via `demo.sh market-compass --session-live`.

- **J-06: A frozen manifest never changes — later data, rebuilds, and regeneration are safe**
  - Steps:
    1. With J-05's manifest stored, run a further backfill on another removed date; assert
       the stored manifest's payload bytes and version are unchanged (API read + export file)
    2. Run seed-safe remove-data over a range covering that manifest's as-of (its snapshots
       cascade away); assert `GET /api/compass` still serves the manifest verbatim with a
       read-time basis disclosure showing the underlying run is unavailable — never a 404,
       never a recompute
    3. Backfill the range back; assert the basis disclosure flips to available (and labels
       the run as rebuilt when its creation timestamp changed) while the manifest bytes
       remain identical
    4. Trigger the explicit regenerate action for that as-of (confirm-gated); assert
       version 2 appears with its own mode and generation timestamp and carries
       `prospective_eligible: false` even when its mode computes `at_ingest` (only
       version 1 minted by the finalize producer can ever be true), its own
       `available_at_utc` and its own `manifest_hash`, version 1 remains readable and
       byte-identical with its flag unchanged, and the UI lists both versions with their
       stamps
    5. Cite in the dev handoff the passing tests: time-safety (perturbing or deleting
       post-as-of bars leaves the content hash unchanged), rebuild survival
       (`clear_snapshot_set` and remove-data delete zero manifest rows), reproducibility
       (two builds of the same inputs produce identical content hashes), create-once
       concurrency (two simultaneous requests yield one row), cohort reproducibility
       (comparison + shadow membership reproduce from the frozen rule and stored run),
       prospective-eligibility derivation (each violated condition — mode, producer,
       version, frozen, missing fence, missing provenance — independently forces false),
       availability-fence conservatism (the recorded fence is never earlier than the
       generation timestamp plus the configured margin), artifact tamper detection
       (flipping any byte of a copied export — including `prospective_eligible` or a
       provenance field — fails `manifest_hash` verification), hash-scope separation
       (same content with different legitimate generation metadata yields an equal
       `content_hash` and a different `manifest_hash`), identity-separation counter-tests
       (changing the why-not display cap or a caution qualifier moves neither scientific
       hash nor any membership; changing `shadow.min_score` moves `cohort_rule_hash`
       only; changing `leadership_min_score` or `max_candidates` moves
       `candidate_rule_hash`, the floor also moving `cohort_rule_hash` via the band
       bound), disposition partition (every non-selected member carries exactly one
       closed-vocabulary disposition and the tallies sum to the cohort count), and schema
       conformance (produced manifests validate; a manifest missing any required
       eligibility, fence, or hash field fails validation)
  - Acceptance:
    - **Consistency (single source):** the basis disclosure is a read-time comparison
      (source-run creation timestamp + engine identity), never a mutation; the dataset
      stamp alone is never trusted as a rebuild detector (a rebuild can reproduce it).
    - **Correctness:** byte-identity assertions hold at every step; version numbering is
      dense and append-only.
    - **Honest status & anti-goals:** rebuilt/unavailable states are disclosed, old
      versions are never hidden or deleted, and no code path UPDATEs a manifest row
      (module audit cited in the handoff).
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of ingest-after-freeze, removal,
      restore, and regenerate-as-version-2, viewable via
      `demo.sh market-compass --session-live`.

- **J-07: The Today page answers the ten-second read from served values only**
  - Steps:
    1. Load `/`; assert the page body renders, in order: the market-state band, the
       plain-English summary, What changed, Leadership rotation, Next-session focus, and
       the manifest strip — with the readiness badge and preflight strip in the layout
       chrome above the body
    2. Assert the regime tile's label and score equal `GET /api/dashboard` for the same
       as-of, and the phase tile's phase, severity, and P(bear) equal
       `GET /api/market-phase`
    3. Assert the three direction words (regime, stress, breadth) equal the served
       compass fields, and each is consistent with its served input under the config rule
       (the stress word is the flat-band classification of the served severity velocity)
    4. Expand each tile's breakdown disclosure; assert component names and contributions
       equal the canonical endpoints' `components` arrays
    5. Assert vocabulary separation: readiness/preflight tokens ("Ready", "GO",
       "DEGRADED", "NO-GO") appear only inside the chrome elements, and regime/phase
       tokens appear nowhere inside the chrome
    6. Assert the regime × phase cross-view chart is absent from `/` and the named
       link-out navigates to `/market` where it renders
    7. Record `/`'s time-to-interactive and each on-load API latency in
       `reports/perf-budgets.md`; assert every measurement is within its committed budget,
       warm `GET /api/compass` reads perform zero producer calls (call-count
       instrumentation cited in the handoff), and `/` no longer fetches `/api/sectors`,
       `/api/themes`, or any full-history series on load
  - Acceptance:
    - **Consistency (single source):** every word, delta, and echo on `/` is a served
      field; word maps and thresholds live only in `config.yaml` and are applied only in
      the engine producer; the frontend performs no threshold comparison, delta
      computation, or word selection.
    - **Correctness:** tile values match the stored run for the same as-of; compass
      echoes are value-identical to the canonical endpoints' fields.
    - **Honest status & anti-goals:** NA inputs render their NA words, never a fabricated
      direction; no proven-language, imperative verbs, or forecast wording anywhere on
      `/`; system readiness and market state never share a surface or a vocabulary token.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the ten-second read top to
      bottom, viewable via `demo.sh market-compass --session-live`.

- **J-08: The market surface relocates intact and history never lies**
  - Steps:
    1. Visit `/market`; assert it renders the two glance cards, the regime × phase
       cross-view card (with its persisted hide toggle still keyed to the existing
       localStorage names), and the complete former More-detail inventory (three breadth
       cards, Top Sectors, Candidate Counts, Top Themes, the full Market Phase & Severity
       card) reading the same endpoints as before the move — no card dropped
    2. Assert the sidebar lists Today (`/`) first and Market (`/market`) second, with
       route-active highlighting correct for both
    3. Step `?asof` to a pre-feature historical run date D; assert the Today tiles show
       D's stored values, What-changed compares D against D's predecessor (header names
       that date), and the manifest strip serves a manifest whose as-of equals D with a
       visible `retrospective` label — never a newer manifest's contents
    4. Step to the J-05 frontier date; assert the strip shows the frozen `at_ingest`
       version-1 stamps
    5. Open `/?asof=D` in a fresh tab; assert the first rendered data is already D-scoped
       (no latest-then-D repaint) and sidebar links carry `?asof=D`
    6. Return to Latest; assert the parameter is gone and the strip shows the latest
       session's state (frozen, or the explicit not-yet-frozen state before the next
       ingest)
  - Acceptance:
    - **Consistency (single source):** the relocated surfaces reuse the existing
      components and endpoints unchanged; the as-of provider remains the sole `?asof`
      owner; there is exactly one manifest lookup path.
    - **Correctness:** for historical D, every displayed value equals D's stored values;
      the comparison anchor is D's predecessor run; the manifest served is exactly D's.
    - **Honest status & anti-goals:** nothing from the former dashboard is removed or
      hidden; retrospective reconstructions are visibly labeled; absence states are dated
      and explicit; a historical view never substitutes a newer manifest (AG-5 lineage).
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of `/market` intact plus a
      historical Today with that date's manifest, viewable via
      `demo.sh market-compass --session-live`.

- **J-09: The backend fits the host — standing memory halves with zero behavior change
  (owner, 2026-08-20)**
  - Why: on 2026-08-20 a goal-mode run froze this 26.7 GB host into swap-thrash and killed
    the desktop session. The single biggest measured block is the SQLite pool page cache:
    `database.pragmas.cache_size: -262144` (256 MB **per connection**) × `pool_size 24 +
    max_overflow 44` ⇒ 6.1 GB steady / 17.4 GB worst in ONE backend — measured 4,837,420 kB
    VmPeak at standing warm (`reports/perf-budgets.md`: the pool's own connection warm-up IS
    the peak) — and full-depth iterations run TWO backends.
  - Steps:
    1. In `config.yaml`, change `database.pragmas.cache_size` from `-262144` to `-65536`
       (256 MB → 64 MB page cache per connection). Change NOTHING else in the `database:`
       block: `pool_size 24` / `max_overflow 44` stay exactly as they are — ops-hardening
       iter-72 sized the pool sum (68) to clear `server.limit_concurrency` (64) after a real
       pool-starvation outage; do not "helpfully" shrink the pool while touching the file
    2. Re-run the standing-warm measurement that recorded 4,837,420 kB VmPeak (the
       perf-budget drill's pool warm-up path) against a backend started via
       `bash scripts/start-backend.sh`; read the backend's `VmPeak` from `/proc/<pid>/status`
       and assert it is ≤ 2.5 GB
    3. Append a dated re-measurement line to `reports/perf-budgets.md` (append beside the
       old figure — never overwrite the recorded history)
    4. Re-run the iter-71-class concurrent-load check: a request burst at
       `server.limit_concurrency` completes with zero `QueuePool` TimeoutError (the pool
       arithmetic is untouched; only the per-connection cache shrank)
    5. Cite in the dev handoff a same-as-of spot-check that served values are byte-identical
       before and after the change (`cache_size` is performance-only; no displayed value may
       move)
  - Acceptance:
    - **Consistency (single source):** the value changes only in `config.yaml`
      (`database.pragmas.cache_size`); no code path overrides or re-states it (anti-goal:
      no magic numbers).
    - **Correctness:** measured backend VmPeak at standing warm ≤ 2.5 GB (was 4,837,420 kB);
      the concurrent-load check passes; the byte-identity spot-check holds.
    - **Honest status & anti-goals:** the new measurement is appended dated next to the old
      one; if the ≤ 2.5 GB target is missed, record the honest measured figure and stop for
      owner review — never widen the target to pass. AG-10's resource contract is the
      governing rule.
    - **Walkthrough:** waived — deliberately backend-only (no UI surface changes); the
      demo requirement is replaced by the dated VmPeak measurement and drill citations in
      the dev handoff.

- **J-10: Bounded recovery of the two trading days the iter-5 drill deleted
  (owner, 2026-08-20 — incident response; state restoration only, never dataset advancement)**
  - Why: iter-5's remove+backfill drill ran against **2026-08-11 and 2026-08-12** believing them
    seed-safe. They were not: `apps/backend/data/seed/meta.json` ends at **2026-07-01**, so those
    two days came from earlier live fetches and "backfill" has nothing local to read back. Verified
    post-drill state — `daily_prices` maximum date is now 2026-08-10 (NVDA/AAPL/GRMN spot-checked);
    `scanner_runs` maximum `asof_date` is now 2026-08-10 (the 08-11 and 08-12 runs are gone);
    `next_session_manifests` still holds 24 rows reaching as_of 2026-08-12 with their export files
    byte-intact, so **AG-12 held at the storage layer** — the manifests survived, their source data
    did not. Consequence: `GET /api/compass?as_of=2026-08-12` now 400s, and J-01/J-02/J-03 —
    previously passing — fail a live replay. This journey restores exactly what was deleted and
    nothing else.
  - Steps:
    1. **Prove the missing set BEFORE any network call (fail-closed).** Derive, from surviving
       evidence only, the exact rows the drill removed: the frozen `next_session_manifests`
       payloads for as_of 2026-08-11/2026-08-12 (they carry the sealed member/candidate/cohort
       lists), `docs/handoffs/goal-market-compass-iter-5-dev.md` and
       `runs/goal-market-compass-iter-5/status.json`, the surviving coverage/availability tables,
       `data_provider_runs`, and the universe membership in force on those dates. Record a
       pre-recovery missing-row count per date and per symbol. If that set cannot be established
       from evidence, **STOP and surface it for owner review** — never fetch a guess.
    2. **Fetch only that set.** Use the project's existing provider path. Request **only 2026-08-11
       and 2026-08-12**, and only the symbols in the proven missing set. A request that would touch
       any other date — in particular anything on or after **2026-08-13** — or any row that still
       exists, is a bug: the implementation must refuse it in code, not by convention. The
       operation must be **idempotent**: re-running it after a partial or failed attempt restores
       only what is still missing.
    2a. **Vendor (owner amendment, 2026-08-20 — after the Stooq block).** The original vendor
       (`stooq`, per the seed manifest) is no longer reachable from this environment: iteration 6
       dispatched the authorized fetch and all 587 requests returned HTTP 404 because Stooq now
       serves a SHA-256 proof-of-work JavaScript challenge instead of CSV (confirmed vendor-side,
       not per-symbol or transient; the offline `LocalStooqArchiveProvider` bundle ends 2026-07-01,
       the same gap). **`yahoo` is authorized as a recovery source for these already-proven missing
       rows, and for nothing else.** Every other bound in this journey is unchanged: same two dates,
       same proven-missing row set, same fail-closed guard, same verification, same auto-close.
       Three conditions ride with it:
       - **Provenance-explicit.** Every restored row is recorded as `yahoo`-sourced through the
         existing per-run vendor fields — never relabelled or back-dated.
         **Factual correction (owner, 2026-08-21 — this bullet previously said the restored rows must
         not be "blended into the surrounding `stooq` history" and that the dataset becomes "honestly
         mixed-vendor at exactly two dates". Both were wrong):** the bars *adjacent* to 2026-08-11/12
         are **not** Stooq's. The committed seed ends **2026-07-01**; every post-seed fetch in
         `data_provider_runs` is `provider='yahoo'` (34 runs), and the single `stooq` run — id 541 —
         **failed with 0 symbols**, so Stooq has never written a bar into this database. The correct
         model is: **through 2026-07-01** the basis is the committed seed / Stooq historical data;
         **post-seed recent history is Yahoo-sourced**; and **the 2026-08-11/12 recovery is Yahoo-
         sourced** — i.e. the recovery is vendor-*continuous* with its immediate neighbours, not a
         two-date mixed-vendor splice. (A broader historical vendor splice may exist at the seed
         boundary itself; that is a separate, pre-existing question and **J-10 must not expand into
         repairing or researching it.**) The handoff and `data_provider_runs` must still record the
         `yahoo` provenance plainly.
       - **Fail closed: precommitted path-agreement + stable multiplicative bridge (owner, 2026-08-20
         — supersedes the earlier absolute-level tolerance).** The stored historical basis is
         split/dividend-adjusted (seed manifest: "REAL split/dividend-adjusted EOD OHLCV"); note per
         the correction above that the *overlap window this gate actually samples* is Yahoo-stored,
         not Stooq-stored, so the gate compares Yahoo raw close against stored Yahoo raw close and
         does **not** test cross-vendor equivalence. Before inserting anything, the
         implementation MUST demonstrate agreement using the two-part test below. To make it possible —
         and for no other purpose — a **read-only comparison fetch** of a small overlap window of
         already-surviving trading days (≤ 2026-08-10) for a sample of the proven-missing symbols is
         authorized; its rows are held in memory or a temp file, compared against the stored bars, and
         **never written to the database, never cached, never used to repair anything**.
         *Why the earlier absolute-level test was wrong:* an "adjusted close" for a fixed past date is
         not a stable number — vendors recompute it retroactively on every later corporate action. A
         single intervening ex-dividend makes a freshly fetched series sit uniformly below a stale
         stored one **even when both vendors use an identical convention**, which is exactly what
         iteration 7 measured (CVX ~0.865%, XOM ~0.643%, both near-zero spread *within* the symbol,
         both high-yield energy names). A level tolerance therefore tests dividend timing, not
         convention, in both directions: it fails clean data and could pass a real level-shift bug.
         The replacement tests the relationship instead:
         1. **Path agreement (precommitted).** Compare the *shape* of the two series over the overlap
            window — day-over-day returns, or each series rebased to 1.0 at the window's earliest
            date — which is invariant to any uniform multiplicative offset. The acceptance criteria
            and every threshold MUST be fixed in code **before** the comparison runs and MUST NOT be
            adjusted after seeing a result; loosening a threshold to convert a failure into a pass is
            forbidden, and doing so is itself a reportable violation.
         2. **Stable multiplicative bridge.** For each symbol compute the per-day ratio of the stored
            value to the fallback value across the overlap window. The bridge is the ratio itself, and
            it passes **only if it is stable** — its dispersion across the window within a precommitted
            bound. That stability IS the convention-agreement evidence; a drifting or erratic ratio
            means the two series are not on one consistent scale and the symbol fails.
         **A passing bridge MUST then be applied.** Restored values are the fallback provider's fields
         **transformed by that symbol's bridge factor onto the existing STORED historical scale**
         (see the vendor-provenance correction in Acceptance: the stored bars in the overlap region
         are not necessarily Stooq's) —
         applied consistently to every price field (open/high/low/close, not close alone, or the bar
         becomes internally inconsistent; volume is not a price and is not scaled). **Passing the gate
         does NOT authorize inserting raw Yahoo adjusted-close values unchanged** — an untransformed
         insert would leave a scale discontinuity at exactly these two dates, corrupting every
         downstream return, gap and score that spans them.
         **Fail closed, per symbol.** Path disagreement, an unstable bridge, too few comparable pairs
         to judge, or a comparison that cannot be performed at all ⇒ that symbol is **not restored**;
         it is recorded in the "requested but not restored" provenance list (step 4) rather than
         inserted on a guessed factor. If no symbol passes, or the comparison cannot run at all,
         **insert nothing and STOP for owner review.**
         **Zero usable pairs can NEVER produce agreement.** An empty or below-floor comparison set is
         `inconclusive`, never `agree` — "all 0 pairs were within tolerance" is not evidence, it is
         the absence of evidence. A minimum count of genuinely compared pairs (both sides present and
         numeric) MUST be required per symbol before any verdict of agreement, and that floor is
         evaluated **after** the disagreement branch so a real out-of-tolerance pair can never be
         downgraded to `inconclusive` by it. This is contract, not merely implementation: iteration 7
         shipped a gate that returned `agree` on an empty pair list — a sampled row whose *stored*
         side was missing was silently skipped — and the audit reproduced it writing rows on a proof
         of nothing. The trigger condition is "rows are unexpectedly missing", which is precisely the
         condition this journey exists to repair. It must not recur.
         **One series, end to end.** The bridge MUST be measured on, and applied to, the **same
         provider series that is actually inserted** — one field, one code path, no crossover. A
         bridge calibrated on an adjusted series and applied to a raw series (or vice versa) silently
         encodes the raw-vs-adjusted difference as if it were the bridge factor; iteration 7's gate
         compared `adjclose` while its restore path would have written `get_daily`'s raw close, and
         the developer's own probe measured those two quantities differing by ~0.086% on AAPL. If the
         restore path cannot read the same series the check validated, fix that before restoring —
         do not bridge across the gap.
         **Persisted evidence is the only admissible calibration input.** Every comparison run MUST
         persist its **per-pair** record (symbol, date, stored value, fallback value, computed ratio
         or delta) as a run artifact — not a summary. **That persisted artifact is the sole auditable
         input to bridge calibration:** a bridge factor may be derived only from pairs recorded in
         it, and any tolerance, floor, or bound cited in a handoff must be traceable to rows within
         it. Numbers that survive only as prose in a handoff are not calibration evidence and may not
         be used as such — iteration 7's 88 deltas were never persisted, its surviving summary does
         not reconcile (4+4+5+76 = 89 ≠ 88), and the figures behind the tolerance decision are now
         unrecoverable without a re-run.
       - **No interchangeability claim.** A successful cross-vendor restoration is evidence that a
         stable scale relationship held for those symbols over one short overlap window, and that the
         restored bars were transformed onto the existing scale — **it is NOT evidence that Yahoo and
         Stooq bars are interchangeable**, not for these symbols, not generally. A passing bridge is a
         measured conversion factor, never a statement of vendor equivalence. No surface,
         artifact, narrative, methodology page, or future study may cite this recovery as
         vendor-equivalence evidence, and no vendor-comparison claim may be derived from it; such a
         claim would need its own pre-registered experiment (AG-4/AG-15). If Yahoo also proves
         unreachable or fails the convention check, that is an honest miss — stop and report it;
         do not try a third vendor without a new amendment.
    2b. **Validation sample vs recovery population — two different things (owner, 2026-08-21).**
       Iteration 8 restored 20 of 587 symbols and then declined to continue, reading the
       anti-goodharting rule as a cap on coverage. That reading conflates two distinct populations,
       and the distinction is now explicit:
       - **The methodology-validation sample** exists to establish *whether the fallback-provider
         convention/bridge methodology is admissible* under the fixed fail-closed rules. Its
         composition is **frozen for that methodological test**. The anti-goodharting prohibition
         stands unchanged and in full force: it must never be enlarged, redrawn, filtered,
         substituted, cherry-picked, expanded toward easier names, or otherwise changed **for the
         purpose of converting a failing or inconclusive methodology verdict into a passing one**.
         The evidence already obtained from that sample remains the evidence for the methodology
         decision. Nothing here permits re-running alternative samples until one passes.
       - **The authorized recovery population** exists to *restore the exact rows independently
         proven missing* by the iter-5 drill. It was established **before** the fallback methodology
         result, from the drill's own audit record — it is not a sample selected after seeing an
         outcome — and it currently holds **587 symbols over the two authorized dates**.
       **Binding invariant:** *the prohibition on widening or redrawing the methodology-validation
       sample does not restrict execution over the already frozen J-10 recovery population. Once the
       recovery methodology is admissible, every member of the independently established recovery
       population must be evaluated under the same fixed per-symbol gate.* The anti-goodharting rule
       therefore does **not** cap recovery at the first 20 symbols.
    2c. **No population-level pass, ever.** The 20 successful symbols do **not** authorize insertion
       for the other 567. Each remaining symbol must independently satisfy the same precommitted
       fail-closed requirements under the existing fixed methodology, including as applicable: exact
       authorized symbol/date membership; same-series validation; minimum usable evidence;
       path/bridge agreement; bridge-factor stability; field-level convention compatibility;
       deterministic ticker mapping; no out-of-scope row overwrite; no threshold override; persisted
       pair-level evidence; and a bridge calibration reproducible from that persisted evidence.
       For any symbol: **`mismatch` or `inconclusive` ⇒ zero rows written for that symbol.** Do not
       loosen thresholds after seeing failures. Do not substitute a different methodology for
       troublesome symbols without a later explicit goal amendment.
    2d. **Continue from 20/587 — do not restart.** *(HISTORICAL, owner 2026-08-24: this instruction was
        executed and is spent — iteration 9 carried 20/587 to the terminal 585/587. J-10 is CLOSED; this
        paragraph is not a live instruction and must not be read as authorizing further recovery work.)*
        The 20 already-restored symbols stay restored if
       they satisfy the corrected J-10 contract and the audit findings. Do not delete or revert them
       merely to restart the recovery. Treat current state as **20 validly restored · 567 still
       pending individual evaluation**, and make the next recovery pass **idempotent** over the
       restored 20 (already-complete symbols are skipped, never re-fetched or overwritten).
    3. **Never overwrite a survivor.** Insert only missing rows; every surviving row stays
       byte-unchanged. Derived state for those two dates (`scanner_runs` and their snapshots) is
       rebuilt through the normal ingest path once the bars are present, and must not touch any
       other date's stored run. AG-12 continues to govern: no stored manifest row or export file is
       mutated or deleted by this recovery.
    4. **Record provenance** using the existing conventions (`data_provider_runs` plus a dated
       section in the iteration's dev handoff — do NOT introduce a new provenance framework):
       why the fetch was authorized (this amendment), exactly which dates were fetched, which
       symbols/rows were restored, the provider used, recovery start and completion timestamps,
       the pre-recovery missing-row count, the post-recovery restored-row count, any row requested
       but not restored, and the resulting dataset/frontier state.
    5. **Verify before any normal lane resumes**, using deterministic checks where they already
       exist (row counts, coverage summaries, hashes): (a) expected coverage for 2026-08-11 and
       2026-08-12 is restored; (b) no other historical date was modified — compare against the
       recorded pre-recovery state; (c) surviving rows were not overwritten unnecessarily;
       (d) the dataset frontier did **not** advance past 2026-08-12 as a result of the repair;
       (e) the project's data/DB-integrity checks pass; (f) the RAW-layer destructive condition is
       gone — canonical price coverage exists for both dates.
       **Scope correction (owner, 2026-08-21): the final derived-state cleanliness claim does NOT
       belong to J-10.** `GET /api/compass?as_of=2026-08-12` serving cleanly and J-01/J-02/J-03
       replaying clean are now **J-11 Stage G** criteria, because the derived state those checks read
       is exactly what J-11 exists to regenerate. J-10 verifies raw-layer facts and safe DB state only,
       and may report: rows restored; canonical price coverage restored; no unauthorized overwrite or
       date expansion; and that temporary recovery-era `ScannerRun`s remain pending J-11. J-10 must
       **not** claim the derived state is clean, and must not require create-once APIs to refresh runs
       they cannot refresh (see step 5b).
    5b. **Completing the remaining raw rows does NOT refresh the existing 2026-08-11/12 ScannerRuns
       (owner, 2026-08-21 — verified against the implementation).** J-10's rebuild step is a
       **create-once no-op** when a snapshot already exists: `run_bounded_recovery_backfill`'s own
       docstring states *"A true no-op (create-once) if a snapshot already exists for both dates"*
       (`j10_recovery.py:756-761`), and it routes through `scanner.persist_run_payload`, which opens
       with `existing = get_run_for_date(...); if existing is not None: return existing  # immutable:
       never re-create or overwrite an existing run` (`scanner.py:95-97`). Iteration 8 already created
       runs for both dates while only **20 of 587** symbols were restored, so:
       > Completing the remaining 567 raw-price rows does not automatically refresh the already-existing
       > 2026-08-11 / 2026-08-12 `ScannerRun`s. They remain derived from the partial raw basis until
       > J-11 deliberately clears and regenerates them.
       **(Status update, owner 2026-08-24: those 567 rows WERE completed in iteration 9 — J-10 is closed
       at 585 restored. Nothing here is outstanding work. The conclusion nevertheless still binds: those
       two `ScannerRun`s were created over the partial basis and are STILL stale, so J-11 Stage C/D must
       clear and regenerate them. Read this paragraph as the reason they are stale, never as a claim that
       raw-price rows remain to be fetched.)**
       They are therefore **not** final reconstructed snapshots, and J-10 must not describe them as
       such. **Status of those rows, recorded explicitly:**
       > Any `ScannerRun` for 2026-08-11 or 2026-08-12 created before J-10's final raw-input recovery
       > completes is **known temporary / recovery-era derived state**. It is non-authoritative for the
       > repaired dataset until J-11 clears and recreates the full incident set.
       Do **not** delete those runs inside J-10 merely to satisfy J-10 acceptance — their deliberate
       removal belongs to J-11 Stage C. Do **not** mint new manifests to reflect this status, and do
       **not** mutate existing ones.
       If byte-for-byte restoration cannot be demonstrated because the vendor archive is not itself
       immutable, **state that limitation plainly** and verify the strongest practical invariants
       instead (per-symbol row presence, OHLCV shape, expected session count, no gap against the
       surrounding trading days).
    5a. **Account for every mutation the verification itself causes (owner, 2026-08-21).**
       Iteration 8's step-5(f) check required starting the backend, and this codebase's boot warmup
       created an unrelated `ScannerRun` for **2026-05-12**. Investigation showed it benign — no
       `daily_prices` row changed, no manifest changed, no network fetch, computed from
       already-committed data — so it is *not* equivalent to unauthorized price-data recovery. It is
       still an unexpected persistent write outside the intended verification scope, and
       verification must stop being blind to that class of write. Recovery verification MUST
       reconcile **all** database mutations caused by the verification procedure itself, classifying
       each as:
       - **an authorized recovery write** — the intended recovery-date price rows, plus the
         explicitly expected derived-state rebuild for those two dates; or
       - **an incidental product write** — e.g. backend boot warmup creating an unrelated scanner
         run. Incidental writes MUST be **detected, recorded, and explained**, and MUST be
         **excluded from any claim that verification was side-effect-free**.
       **A verification step must never claim "no out-of-scope writes" if the application itself
       produced an unrelated persistent row during that verification.** Where practical within the
       existing architecture, prefer a verification path that suppresses or isolates automatic boot
       warmup writes — but do NOT turn this into a broad redesign of application startup within this
       goal. If suppression or isolation is not trivial, record the known side effect as a defect
       and require exact before/after mutation accounting for every J-10 verification run.
    6. **Close the exception.** Once verification passes, record in the handoff that AG-9's dated
       exception is **exhausted**; normal offline-deterministic ingest applies again automatically.
       "Verification passes" means the recovery is complete per the completion rule in Acceptance —
       a partial restoration does not exhaust the exception, because the remaining authorized
       symbols still need it.
    7. All recovery work stays on the session branch `goal/market-compass`; `main` is not touched.
  - Acceptance:
    - **Consistency (single source):** restored rows enter through the existing ingest/provider
      path — no second write path, no hand-edited rows, no new provenance framework; the missing
      set is computed once and is the sole input to the fetch.
    - **Responsibility boundary (owner, 2026-08-21) — J-10 and J-11 must not be circular.**
      > **J-10 repairs canonical inputs. J-11 repairs the derived state built from those inputs.**
      J-10's terminal state is **raw-layer only**: every symbol in the frozen 587 population is either
      restored under the fixed per-symbol gate or explicitly classified fail-closed/unrestorable under
      the owner-authorized completion policy; `daily_prices` for 2026-08-11/12 carries the strongest
      provable intended coverage; surviving price rows were not overwritten; no third date was fetched
      or modified; raw OHLCV/provider-convention invariants pass; provider and recovery provenance are
      recorded; and AG-9's live-fetch exception is exhausted when those raw criteria pass.
      **J-10 must NOT require J-11's clean derived-state regeneration to be complete before J-10 can
      close** — requiring it would deadlock, since J-11 is itself gated behind J-10's terminal state.
      J-11 owns: clearing the 11-date incident derived state; recreating runs and child rows under one
      engine generation; forward-return hole repair; dependency-aware cache invalidation/rewarm;
      manifest/run schema reconciliation; and final incident-wide serving consistency.
    - **Correctness:** the two dates are restored, no third date is touched, no surviving row is
      overwritten, and the frontier is unchanged at 2026-08-12. (Final repaired-state J-01/J-02/J-03
      replay is a **J-11 Stage G** criterion, not a J-10 one — see step 5a/5b.) If the restoration is
      cross-vendor (step 2a), the path-agreement test passed on
      precommitted criteria, every restored symbol had a stable bridge that was actually applied to
      all four price fields (no raw fallback value inserted unchanged), any symbol without one is
      listed as not-restored, and every restored row carries its true `yahoo` provenance.
    - **Honest status & anti-goals:** the incident is preserved, not rewritten — iter-5's drill
      result, its handoff, and any reviewer/QA evidence already produced remain in place, alongside
      an explicit incident/recovery record stating that the committed seed (window ending
      2026-07-01) could not restore these dates. AG-17 governs what the repair may NOT do to
      provenance. If any part of the recovery cannot be proven to stay inside the authorized scope,
      the iteration stops for owner review rather than broadening the fetch.
    - **Completion rule (owner, 2026-08-21):** J-10 does **NOT** close merely because the recovery
      mechanism has been demonstrated on 20 names. The goal is recovery of the proven deletion, not
      a pilot implementation. J-10 remains **incomplete** while the majority of the authorized
      recovery population is neither (a) restored under the fixed gate, nor (b) explicitly
      classified as fail-closed/unrestorable under a goal-authorized completion policy. **Do not
      invent a partial-completion threshold** — there is no "enough symbols" number, and none may be
      introduced without an owner amendment. If some symbols ultimately cannot be restored under the
      fixed methodology, surface the **exact residual set and the per-symbol reasons** for
      owner/reviewer decision rather than silently lowering the coverage requirement.
    - **J-10 CLOSED — residual set accepted (owner, 2026-08-23).** The owner/reviewer decision the
      completion rule above calls for has now been made. **J-10 is raw-layer terminal at 585 restored
      / 2 explicitly unrestorable.** The final fail-closed residual set is exactly:
      - **EA** — Yahoo has no trading data past 2026-08-10; a real delisting, not a gate failure.
      - **EQR** — only 1 comparable calibration pair, below the fixed 3-pair floor; the gate correctly
        refused to write.
      This is an acceptance of a **named, per-symbol-reasoned residual set**, NOT a partial-completion
      threshold: no "enough symbols" number is introduced, and the ban on inventing one stands. Do not
      reopen J-10 to retry EA or EQR, do not fetch further data for them under J-10, and do not treat
      this acceptance as licence to lower coverage for any future population. AG-9's live-fetch
      exception for J-10 is **exhausted** — it authorizes nothing further.
    - **Recorded finding — the one-series rule worked, and a vendor-provenance correction
      (iteration 8; corrected 2026-08-21 by the out-of-band audit — read the correction, it changes
      what the result means):** running the comparison and the restore through the same raw-close
      series produced bridge factors of **exactly 1.0** for every restored symbol, and iteration 7's
      ~0.865% CVX "mismatch" was indeed a **series-crossover artifact** — `adjclose` compared against
      a stored raw close — which the one-series rule correctly eliminated. That conclusion stands.
      **But the earlier attribution of this file was wrong and is corrected here: the stored bars in
      the overlap window are NOT Stooq's — they are Yahoo's.** The committed seed ends 2026-07-01;
      every post-seed fetch in `data_provider_runs` is `provider='yahoo'` (34 runs from 2026-07-17
      onward), and the single `stooq` run, id 541, **failed with 0 symbols**. Consequences that every
      future iteration must reason from:
      - The gate compared **Yahoo against Yahoo** over that window, so the 1.0 factors were expected
        by construction and the check **could not have failed** there. This makes the write *safer*
        (no scale discontinuity is possible), but it is **NOT** cross-vendor validation evidence and
        may never be cited as such.
      - Iteration 7's crossover was therefore **within a single vendor** (`adjclose` vs raw close),
        which is exactly why both offenders were dividend payers.
      - "Bridge onto the existing scale" means the **stored** scale, whatever vendor produced it —
        not "the Stooq scale". A genuinely cross-vendor overlap (pre-2026-07-01 seed region) has
        never been exercised by this gate.
      This finding is evidence that the corrected gate tests the intended property — it is **NOT**
      grounds for removing, weakening, or skipping the convention gate, and must never be cited as
      such.
    - **Keep the closed audit findings closed:** generalizing recovery from 20 symbols to the full
      authorized population must not regress **B2** (no raw/adjusted series crossover), **B3**
      (persisted per-pair comparison evidence), **B5** (thresholds not caller-overridable), **B6**
      (explicit authorized-date assertion), or the rule that **zero usable pairs can never return
      `agree`**.
    - **Traps this journey must actually prove** (each is a required check, not a nice-to-have):
      1. the methodology-validation sample cannot be enlarged or redrawn after seeing its outcome to
         chase a pass;
      2. the full frozen 587-symbol recovery population is nevertheless eligible for processing;
      3. a passing methodology sample gives untested symbols **no** automatic pass;
      4. every restored symbol has its own persisted evidence and verdict;
      5. previously restored valid symbols are idempotently skipped, never overwritten;
      6. a failing or inconclusive symbol produces **zero** writes for that symbol;
      7. fixed thresholds remain structurally non-overridable;
      8. recovery cannot leave J-10 complete at `20/587`;
      9. every database mutation caused during recovery verification is reconciled, **including
         incidental `ScannerRun` creation** by backend boot warmup;
      10. `Depth: full` cannot silently become `lean` without an explicit unmet-requirement record.
    - **Walkthrough:** waived — **raw-layer** incident repair with no UI surface change of its own.
      The J-10 demo requirement is replaced by the raw-recovery provenance record, bounded-scope
      verification, canonical price-coverage evidence, and complete mutation reconciliation. **Final
      repaired-state `GET /api/compass` serving and the J-01/J-02/J-03 replay belong exclusively to
      J-11 Stage G** (owner, 2026-08-21 — this bullet previously claimed the replay as J-10's own
      proof "that the damage is gone", which contradicted the J-10/J-11 responsibility boundary and
      could pull the final derived-state check back into J-10).

- **J-11: Incident-bounded clean regeneration of derived state (owner, 2026-08-21)**
  - Why: the iter-5 drill's cascade left the derived layer for its incident dates in four *different*
    conditions at once — rows that survived, rows still missing, rows incidentally recreated by
    backend boot warmup, and rows partially rebuilt during J-10. Repairing each condition separately
    is per-date archaeology with a large surface for error. Within the incident boundary those
    derived rows are **deterministic outputs of preserved canonical inputs**, so they are disposable:
    clear them and regenerate the whole incident set uniformly through the CURRENT canonical engines,
    leaving one internally consistent derivation from one engine generation. The immutable evidence
    layer stays separate and untouched. This deliberately removes the need to reason about old-vs-new
    snapshot row format inside the incident set.
  - **Prerequisite — J-10 first, hard gate.** J-11 does NOT replace or bypass J-10. J-10 still owns
    restoration of the canonical `daily_prices` rows for 2026-08-11 and 2026-08-12 across the proven
    587-symbol population. **J-10 prerequisite SATISFIED (owner, 2026-08-24): the raw layer is terminal
    at 585 restored, with EA and EQR explicitly accepted as unrestorable, and AG-9's recovery-fetch
    authorization is exhausted** — see the "J-10 CLOSED — residual set accepted" bullet in J-10. The
    superseded status line this bullet used to carry ("currently 20 restored / 567 pending") described
    the state at iteration 6 and is **stale**; it is corrected here rather than deleted so the lineage
    stays legible. **J-10 is closed and MUST NOT be reopened** — not by the decomposer, not to retry EA
    or EQR, not to "finish the remaining 567", which no longer exist. The original gate still binds for
    its own sake: never run the derived rebuild against a knowingly incomplete price layer, and never
    lower J-10's acceptance criteria to unblock this journey.
  - **The incident date set — all 11, not the 8 currently absent.** From the authoritative removal
    audit (`data_provider_runs` id=538, whose own cascade record lists them):
    `2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03, 2026-08-05,
    2026-08-10, 2026-08-11, 2026-08-12`.
    Scoping to only the absent dates would preserve exactly the inconsistency this journey exists to
    remove: 2026-05-12 was incidentally rebuilt by boot warmup, and 2026-08-11/2026-08-12 were
    partially rebuilt during J-10. Verified current state (read-only, 2026-08-21) — 2026-05-12: 1 run
    / 0 manifests · 2026-05-13, 07-10, 07-13, 07-24, 07-27, 08-03: 0 runs / 0 manifests · **2026-08-05:
    0 runs / 2 manifests (orphaned — its source run was destroyed)** · 2026-08-10: 1 run / 1 manifest ·
    2026-08-11: 1 run / 3 manifests · 2026-08-12: 1 run / 6 manifests. **This authorizes no deletion of
    raw price rows for these or any other dates.**
  - Steps:
    1. **Do NOT call `clear_snapshot_set()` (`app/engine/data_manager.py:2212`).** That helper is
       correct for what it does — it deletes `ForwardReturn` → `ScannerResult` → `SectorScoreRow` →
       `ThemeScoreRow` → `ScannerRun` children-before-parents, whole-row only, never referencing
       `DailyPrice`, and asserts `bars_before == bars_after` — but it takes **no date filter and
       clears the ENTIRE historical snapshot set** (J-85 semantics). A full-history reset would not be
       a neutral repair: `config.yaml` `scanner.snapshot_cadence` is `deep_cadence: monthly` with
       `daily_start: 2026-06-01`, and the config itself records a surviving create-once **daily stretch
       2021-01→2021-04** that today's cadence does not imply — a wholesale rebuild would silently
       discard real point-in-time density. Specify instead a narrow mechanism conceptually equivalent
       to **`clear_snapshot_dates(EXACT_INCIDENT_DATE_SET)`**, reusing the SAME child-before-parent
       deletion semantics, whole-row-delete discipline, and price-untouched assertion as
       `clear_snapshot_set` rather than inventing different semantics. J-11 is incident-bounded, never
       a cadence reset.
    2. **Classify before deleting — explicit allowlist, produced by inspecting the live model graph,
       never `DELETE FROM <everything except prices>`.** The classification below is the verified
       starting point; the developer must re-derive it against the current models and extend it if
       inspection finds more:
       - **Canonical input — never deleted:** `daily_prices`; the reference/universe tables (`stocks`,
         `etfs`, `sectors`, `industries`, `themes`, `theme_members`); `macro_series`. The reset MUST
         assert the `daily_prices` row count **and** a content fingerprint/coverage measure are
         identical immediately before and after the deletion step.
       - **Immutable / audit evidence — never deleted, rewritten, or re-created as newly historical:**
         `next_session_manifests` and their export artifacts; `data_provider_runs`; `import_checkpoints`;
         the certified-claims ledger (`runs/goal-session-mcp-loop/state/certified-claims.jsonl`), the
         staging ledger, pre-registrations, and graveyard/rejected-hypothesis history; the recovery and
         audit artifacts including all iter-5 and iter-8 evidence; existing goal/session audit history.
       - **User state — never deleted:** `watchlist`, plus any other user-authored rows inspection finds.
       - **Rebuildable incident-derived state — cleared and regenerated for the 11 dates only:**
         `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`, and the associated
         canonical derived forward-return state as the real dependency graph requires.
    3. **Regenerate through the canonical engines only.** Rebuild the 11 dates through the same
       production computation paths normal snapshots use — `scanner.run_scan` (`scanner.py:226`) and
       the canonical `persist_run_payload` (`scanner.py:85`) — plus the canonical forward-return
       helpers. Introduce **no** recovery-specific scoring, regime, sector, theme, setup, pattern or
       return formula, and no second computation implementation. Rebuilt runs then carry the current
       engine identity and current additive schema naturally, because the normal production path
       stamps them. Do **not** hand-patch current-format columns onto legacy rows when deleting and
       canonically recreating makes that unnecessary. Do not apply current cadence to choose a
       different historical date universe — regenerate exactly the 11 incident dates.
    4. **Mint NO new historical manifests (critical).** The ingest-finalize tail calls
       `compass.get_or_create_manifest(session, run_for_date, cfg, producer="ingest_finalize")` for
       **every** date in `prog.new_snapshot_dates` (`data_manager.py:4526-4538`). During an ordinary
       backfill that legitimately creates a retrospective manifest — here it must not. **7 of the 11
       incident dates currently have no manifest at all** (2026-05-13, 07-10, 07-13, 07-24, 07-27,
       08-03, and 05-12), so an unguarded rebuild would manufacture 7 immutable "historical" decision
       artifacts that never existed at their supposed historical time. Binding rule:
       > **Incident-rebuild snapshot creation must not mint a `NextSessionManifest` for an as-of that
       > did not already have one before the maintenance operation.**
       For the 4 dates that DO have manifests (2026-08-05, 08-10, 08-11, 08-12): do not regenerate
       them, and do not change `version`, `source_run_id`, `available_at_utc`, `content_hash`,
       `manifest_hash`, or `prospective_eligible`. The existing read-time **basis disclosure** is the
       sanctioned mechanism for surfacing that a stored source run was rebuilt or is unavailable
       relative to the manifest's recorded source-run timestamp — note 2026-08-05 already carries 2
       manifests with **zero** surviving runs, so it exercises exactly that path. A maintenance rebuild
       must never create an apparently historical prior that did not actually exist at that time.
       **Add a named test for this.**
    5. **Repair the full forward-return damage, not just the rebuilt runs.** Rebuilding 11 runs is not
       sufficient. The removal path's defensive consistency sweep
       (`data_manager.py:2185-2192`) deletes **any** `ForwardReturn` whose `measured_date` falls on a
       removed bar date — *including rows whose originating `ScannerRun` was never removed*. So holes
       exist on retained runs. After J-10 has restored the raw bars and the 11 snapshots are
       regenerated, run the existing **create-once** canonical forward-return machinery
       (`forward_testing.backfill_forward_returns` / `backfill_run_forward_returns`, whose
       `_insert_run_forward_returns` is create-once) over the retained + rebuilt snapshot set to fill
       every derivable missing row. Do **not** recompute or overwrite surviving rows, and do **not**
       introduce a second return formula. The post-rebuild audit must distinguish three populations:
       (a) forward returns belonging to the 11 rebuilt runs; (b) holes on otherwise-retained runs
       caused by the original 2026-08-11/12 bar deletion; (c) genuinely not-yet-mature horizons, which
       **must remain absent/NA**. Never fabricate a forward return to reach row-count parity.
    6. **Invalidate caches explicitly — the same-stamp collision is real, not hypothetical.**
       `research._dataset_version()` (`research.py:2517`) returns `f"r{max_run_id}-f{fr_count}"` — the
       max `scanner_runs.id` plus the `forward_returns` row count. A delete-and-recreate that restores
       the same row counts, and reuses SQLite rowids (no `AUTOINCREMENT`), can therefore produce a
       **byte-identical stamp**, and every dependent cache would keep serving its stale pre-reset
       payload while appearing current. `_membership_dataset_version` (`research.py:2535`) is narrower
       — the snapshot/`asof_date` set, bars manifest, history threshold — and collides just as easily
       once the same date set is restored. Before implementation, classify **every** cache that depends
       directly or transitively on `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`
       or `forward_returns`, deriving the set from the current models rather than copying this list.
       Verified today, all seven key on a dataset-version stamp: `event_study_cache`
       (`subject, view, asof_key, dataset_version`), `market_phase_cache` (`asof_key, dataset_version`),
       `forward_aggregate_cache` (`horizon, asof_key, dataset_version`), `index_series_cache`
       (`range_key, full, dataset_version`), `availability_cache` (`dataset_version`),
       `membership_timeline_cache` (`dataset_version`, narrow stamp), `coverage_snapshot`
       (`asof_key, dataset_version`). For each, document one of: (1) its key is *guaranteed* to change
       and cleanly invalidates; (2) explicitly delete the affected rows; or (3) explicitly regenerate
       through the canonical producer. **Prefer deterministic explicit invalidation** wherever
       delete/recreate could reproduce the same key. No stale cache may survive while appearing
       current; do not delete a cache unrelated to the changed dependency graph.
       **Classify by ACTUAL data dependency, not by table name or the mere presence of a
       dataset-version field (owner, 2026-08-21).** Carrying a version stamp does not by itself mean a
       payload depends on anything J-11 changes. Worked example, verified: `index_series_cache` stores
       `indexes.compute_index_series(...)`, which hydrates the configured `index_chart.symbols` ETFs'
       stored **`daily_prices`** — and J-11 modifies no price row at all, so its payload is unaffected
       even though it carries a stamp; it may legitimately need no destructive invalidation. The
       required disposition for every cache is therefore one of: **prove it unaffected and leave it
       alone**; explicitly invalidate; or regenerate through the canonical producer. **Do not
       blanket-delete the named caches for convenience** — a needless cache wipe is its own
       (recoverable, but real) availability and compute cost, and it obscures which dependency the
       repair actually touched.
    7. **Preserve the evidence history and do not reinterpret it.** The canonical certified-claims
       ledger currently holds **7 entries, all `FAIL`** (verified 2026-08-21; the staging ledger
       likewise holds 7, all `FAIL`). Preserve both exactly. Do **not** reset trial count, Bonferroni
       history, alpha-spend history, or rejected claims, and do **not** re-run old claims as part of
       this maintenance. Record the semantic distinction: *old referee entries are historical verdict
       records produced from the dataset that existed at their registration time; a later maintenance
       regeneration must never be described as the dataset those historical verdicts originally
       evaluated.* There is currently no PASS claim to invalidate — **that is not permission to rewrite
       the history.** Two concrete write/reinterpret paths must stay shut for the whole of J-11:
       `app/mcp/tools.py`'s `verify_edge` **appends** to a ledger (`ledger.append_entry`, `tools.py:660`)
       and would consume a trial and spend alpha; and `app/engine/forward_walk.py` **re-scores** existing
       claims — running it against the regenerated dataset is exactly the reinterpretation this rule
       forbids. Neither may run as part of the maintenance. (`app/engine/evidence.py` is read-only —
       `build_evidence_payload` serves the ledger and recomputes nothing — so the read side is safe.) (Note for implementers: `ledger.py`'s `rejection_offsets` docstring still says the
       live ledger is `[1, 2, 4] PASS` — that comment is **stale**; the file itself is 7×FAIL. Trust the
       file.) **If implementation discovers a current PASS/proven claim in any canonical source not
       identified here, STOP and surface the conflict** rather than silently carrying a Proven label
       across a materially changed research dataset. This journey is a repair, never a new
       certification or research experiment.
    8. **Do not bootstrap a fresh database from the committed seed.** A fresh DB is not equivalent to
       the current canonical raw dataset: the seed window ends **2026-07-01**, while the live database
       holds post-seed acquired history (all of it `provider='yahoo'` — 34 runs from 2026-07-17 on;
       the single `stooq` run, id 541, failed with 0 symbols). Deleting `trendora.db` and re-seeding
       would discard valid canonical input. Use the **current repaired `daily_prices` layer** as the
       input to the bounded regeneration. A separate dataset-epoch migration may be designed later if
       ever wanted; it is not required to resolve this incident.
    9. **Isolate the maintenance run from normal app boot side effects.** Boot warmup itself writes —
       `warmup.ensure_latest_snapshot` calls `run_scan`, and `_warm_membership_timeline` /
       `_warm_coverage_snapshot` populate caches — which is exactly how 2026-05-12 got recreated. The
       destructive clear and regeneration must therefore run with: **one controlled writer**; no boot
       warmup racing the mutation; no browser QA; no replay lane; no second backend or frontend; no
       network fetch anywhere in J-11; and no unrelated producer writing while the
       deletion/regeneration is being reasoned about. Prefer a bounded maintenance command or module
       calling the existing canonical engine functions over using the UI merely to trigger a rebuild.
       Add no second computation implementation.
    10. **Depth gate — fail closed before any destructive write.** The `Depth: full → lean` demotion is
       unresolved (iters 2, 6, 8). Before any J-11 destructive write executes: **if the goal or spec
       requests `Depth: full` and the actually dispatched depth is not full, stop before the mutation.**
       A lean fallback must not launch the parallel replay, start browser QA, start another
       backend/frontend, execute the destructive reset, or be treated as equivalent to full. If fixing
       this needs an `incredible_auto_dev` framework change outside this repository, **report that
       dependency and keep the engine paused rather than bypassing it.**
    11. **Stage B1 — reconcile the manifest↔ScannerRun referential contract BEFORE any incident run is
       deleted (hard precondition, owner 2026-08-21).** The schema and the design currently disagree,
       and the disagreement is load-bearing for this journey. `models.py:820` declares
       `source_run_id: int = Field(foreign_key="scanner_runs.id", index=True)` and the live DDL carries
       `FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)`, while the Market Compass design
       requires manifests to survive snapshot deletion and rebuild. Today that works **only because
       enforcement is off** — `db._apply_sqlite_pragmas` never issues `PRAGMA foreign_keys=ON`, SQLite
       defaults it OFF (`PRAGMA foreign_keys` reads `0` on the live DB), and
       `PRAGMA foreign_key_check(next_session_manifests)` already reports **12 violations**, all on the
       four incident dates that carry manifests. **The observed 2026-08-05 orphan is therefore NOT
       proof the schema contract is sound — it is proof the constraint is unenforced.**
       **J-11 must not rely on SQLite foreign-key enforcement being disabled as part of its safety
       model.** The intended semantic contract, to be made true by schema/contract rather than by
       accident:
       > `source_run_id` is the **immutable historical row-id VALUE recorded when the manifest was
       > created**. It is retained as provenance, but it is **not a durable live foreign-key identity**,
       > and it must never be used alone to prove that a current `ScannerRun` is the original source
       > run after a delete/rebuild. A manifest remains valid and immutable even if that `ScannerRun`
       > is later removed and canonically rebuilt — under a different row id **or the same one**.
       **Why "or the same one" is not paranoia (verified 2026-08-21):** `scanner_runs.id` is a plain
       SQLite **rowid alias** — `id INTEGER` PRIMARY KEY with **no `AUTOINCREMENT`**, and the database
       has no `sqlite_sequence` table at all — so SQLite allocates `max(rowid)+1` and **freely reuses
       the ids of deleted rows**. This is live, not hypothetical: the three highest ids in the whole
       table (**3148, 3149, 3150**) are all incident-date runs, so J-11 Stage C's deletion drops the
       max to **3147** and the regeneration re-issues **3148–3158** — very likely binding those exact
       ids to *different* `as_of` dates than they hold today, since recreation order need not match
       original creation order. The reassuring half, recorded honestly: the currently orphaned
       manifests point at ids **3048, 3049, 3081, 3112**, all below 3147, so **none** falls inside the
       re-issue range and no existing manifest would be silently re-bound by this particular rebuild.
       That is an accident of today's id distribution, **not a guarantee** — a retry, a different
       recreation order, or any future incident could collide. **Never reason about source identity by
       id equality.**
       **Effective historical source identity is compound**, made of the already-immutable fields:
       `as_of` + recorded `source_run_id` + recorded `source_run_created_at` + frozen engine identity.
       Do not invent a new manifest field for this unless implementation proves one is required. The
       operative rule is simply: **row-id equality alone is insufficient after delete/recreate.**
       `basis_disclosure` must continue to resolve the CURRENT run by `as_of` and compare its
       `created_at` against the manifest's frozen `source_run_created_at` — that design is strictly
       stronger than id equality and remains authoritative.
       Therefore: do **not** mutate any existing manifest to point at a rebuilt run; do **not** "fix
       up" `source_run_id` after a rebuild; and do **not** change `source_run_id`,
       `source_run_created_at` (carried inside `generation_json`), the hashes, `version`,
       `available_at_utc`, or `prospective_eligible`. The implementer must determine the safest
       schema/migration strategy and **prove it before the destructive phase**. This repository has no
       Alembic, so a table rewrite must not be prescribed casually — any approach must be shown to
       preserve every historical artifact byte-for-byte. The read path's **design** is right and stays
       authoritative: `compass.basis_disclosure` (`compass.py:1100-1115`) resolves the current run **by
       `as_of`** and compares the recorded `source_run_created_at` against that run's `created_at` — it
       never dereferences `source_run_id`. **Correction (owner, 2026-08-23): its implementation is
       nevertheless defective and must be fixed — the earlier "needs no change" reading is withdrawn.**
       `compass.py:1108-1109` short-circuits to `{"status": "available"}` when `generation_json` is
       empty, so a manifest with no recorded basis reports its original basis as intact. Verified live:
       the 2026-08-12 version-1 manifest (recorded source run 3081, long gone; current run 3148) reports
       `available` while its five sibling versions correctly report `rebuilt`, and **8 of 24 live
       manifests carry `generation_json` NULL** (count corrected 2026-08-23 from the "10" first recorded
       by the iteration-10 evaluator; re-verified read-only: 24 rows total, 8 NULL, 0 empty-string).
       `basis_disclosure` rides on every `GET /api/compass` payload,
       so this is a fabricated-state defect on a served surface — precisely the class AG-1 forbids.
       **Stage C may not begin until all six of these are proven:**
       1. the live schema's manifest/run relationship matches the documented
          manifest-survives-rebuild contract;
       2. deleting an authorized `ScannerRun` does not require deleting or rewriting any existing
          manifest;
       3. existing manifest rows remain byte-for-byte semantically unchanged;
       4. the solution holds **by schema/contract, not merely because SQLite FK checking is off**;
       5. a future backend with enforced FK semantics — including Postgres-compatible behaviour —
          would not render J-11's intended deletion logically invalid;
       6. `basis_disclosure` still determines rebuilt/unavailable status from the current run for the
          same `as_of`, never by mutating historical manifest linkage.
       **Intended end state, stated precisely:** `source_run_id` remains **stored historical
       provenance**; it is **not** required to dereference to a live `ScannerRun` forever; manifest
       survival must not depend on foreign-key enforcement being off; current-run reconciliation is by
       `as_of` + frozen source timing/provenance, **never** by FK rebinding; a rebuilt run may
       legitimately carry a different id; and **even when it reuses the same numeric id it is still a
       rebuilt run** whenever the frozen timestamp/provenance differs. Never mutate a manifest to
       "repair" an orphaned foreign key.
       **If this contradiction cannot be resolved safely inside the current repository without a risky
       migration, STOP before J-11 and surface it as an owner decision.**
       **That STOP fired at iteration 10 and the owner has now decided (owner, 2026-08-23).** Verified
       live at that point: the table DDL still ends in `FOREIGN KEY(source_run_id) REFERENCES
       scanner_runs (id)`, `PRAGMA foreign_keys` reads `0`, and `pragma_foreign_key_check` returns 12
       violations — so acceptance items 1 and 4 were false on the live database, and the iter-10
       `models.py` declaration change fixed only metadata-built databases, not the live file Stage C
       deletes from. The ruling:
       - **A1 — Bounded live-schema migration is AUTHORIZED.** A narrowly bounded live-schema migration
         of `next_session_manifests` **only** is authorized, for the **sole** purpose of removing the
         `source_run_id -> scanner_runs.id` foreign-key constraint. SQLite cannot drop a constraint in
         place, so the mechanical table rebuild (create constraint-free table → copy rows → drop old →
         rename) is authorized **as a mechanical relocation**. No other table's schema may be altered
         under this authorization, and this is the **only** destructive-schema operation authorized
         anywhere in this goal. It is not a precedent for any other table or any later convenience.
       - **A2 — Absolute preservation.** All **24** manifest rows and **every stored value** must
         survive **exactly**. `source_run_id` **values are preserved as stored historical provenance**
         — only the constraint is removed — including the orphaned ids (3048, 3049, 3081, 3112), which
         must keep their recorded values and must **not** be nulled, rebound, or "repaired". **No
         manifest may be regenerated, rebound, rehashed, upgraded, deleted, or newly minted** (see
         AG-18). AG-12 and AG-17 are **not** waived: the rebuild is byte-preserving relocation, never
         mutation. Any changed stored value is an AG-12 violation and a REGRESSION, not a fixable note.
       - **A3 — Proof obligations, all on the LIVE database, all before Stage C.**
         1. **Pre/post full-row equality:** dump all 24 rows × all columns to a persisted evidence
            artifact **before** the migration, re-dump **after**, and prove equality per row and per
            column (not an aggregate-only check — iteration 9's lesson). Row count 24 → 24.
         2. The six acceptance items above are then re-proven against the live database, not against a
            fixture. Item 4 in particular must be demonstrated with `PRAGMA foreign_keys=ON`, since
            "it works because FK checking is off" is exactly what item 4 excludes.
         3. `sqlite_master` DDL for `next_session_manifests` contains no `FOREIGN KEY` clause, and
            `pragma_foreign_key_check(next_session_manifests)` returns **zero** rows.
         4. Mutation accounting: prove no table other than `next_session_manifests` was written.
       - **A4 — `basis_disclosure` fail-closed fix is a Stage C precondition.** Before Stage C, fix the
         defect recorded above so the read path **fails closed**: when `generation_json` is missing,
         empty, or malformed, or when `source_run_created_at` is absent, `basis_disclosure` must **never**
         report `available`. It must return an explicit unverifiable/unknown state and the UI must render
         the honest "not yet proven"-class placeholder — never a confident claim that the original basis
         is intact (AG-1). Cover each degenerate input with its own test, and re-verify read-only against
         the 8 live manifests that carry `generation_json` NULL. Treat the *count* as evidence to
         re-derive, not to trust: verify it yourself read-only rather than quoting this line.
         **A4-bis — the recorded-timestamp cases must also fail closed (owner, 2026-08-24).** The iter-11
         fix closed the missing/empty/malformed/non-object/key-absent branches but left the *value* of
         `source_run_created_at` unchecked: `recorded = generation.get(...)` followed by
         `if recorded is not None and recorded != current: return rebuilt` / `return available` means a
         key present with value `null` falls through to **`available`** — still fail-open — and an empty
         or unparseable string is reported as **`rebuilt`**, which asserts a rebuild that was never
         established. A key whose value is `null` does not provide a verifiable source timestamp. Required
         behaviour, complete:
         | recorded `source_run_created_at` | status |
         |---|---|
         | absent | `unverifiable` |
         | `null` | `unverifiable` |
         | empty / unusable | `unverifiable` |
         | present but unparseable as the expected timestamp representation | `unverifiable` |
         | valid timestamp ≠ current run's | `rebuilt` |
         | valid timestamp = current run's | `available` |
         | no current `ScannerRun` for the `as_of` | `unavailable` |
         **Never report `available` unless an actual recorded timestamp exists and matches the current
         run.** Do not compare arbitrary strings as though they were valid timestamps — validate the
         recorded value into the same canonical UTC representation the writer and the current-run
         comparison use; if it cannot be parsed, the answer is `unverifiable`, **not** `rebuilt` and
         certainly not `available`. The semantic question is whether the original basis can be *proven*;
         unreadable provenance means unverifiable. Keep this change narrow. Test at minimum: NULL, `""`,
         malformed JSON, `[]`, `{}`, `{"source_run_created_at": null}`, `{"source_run_created_at": ""}`,
         `{"source_run_created_at": "garbage"}`, valid-mismatched, valid-matched, and no-current-run. Then
         re-run the read-only classification across all 24 live manifests without mutating them and report
         the exact new distribution — the live count is evidence to re-derive, never a hardcoded expectation.
       - **A5 — Maintenance isolation stays ACTIVE.** No application-service boot, no browser-QA lane,
         and no deterministic-replay lane, unchanged, until Stage G. The migration iteration is the
         **single** authorized exception to "zero writes to `trendora.db`", and its writes are bounded to
         the `next_session_manifests` rebuild alone. One controlled writer, no backend warmup, and the
         7.8 GB file is never copied or opened for write by anything else.
       - **A6 — Hard gate on Stage C.** **Stage C may not begin until BOTH the schema migration and the
         `basis_disclosure` fix have passed reviewer, QA, and auditor review AND live read-only
         verification.** This gate is **in addition to** the six acceptance items, not a substitute for
         them. Reviewer and QA marking the DoD "complete" is not sufficient evidence — at iteration 10
         both did so while two acceptance items were false on the live database; the claim must be
         re-derived from the live database by the verifying agent.
       - **A7 — Failure semantics.** If pre/post row equality cannot be proven, roll the table back to
         its pre-migration state, write the evidence, and STOP for owner review. Never proceed to Stage C
         from a partially migrated or unproven table.
       This work is **Stage B1-completion**, a separate iteration (or iterations) before Stage C — it is
       not part of the Stage C destructive unit and does not start it.

       **OWNER RULING — iter-11 DDL residual accepted (owner, 2026-08-24).** The iter-11 live migration
       successfully removed the unwanted `source_run_id -> scanner_runs.id` foreign key and preserved all
       24 manifest rows and every stored value, **but it also changed four DDL properties beyond the
       original A1/AG-18 authorization.** The owner accepts **exactly** these four already-materialized
       residual differences, and nothing else:
       | # | property | before | after |
       |---|---|---|---|
       | 1 | `version` | `INTEGER NOT NULL DEFAULT 1` | `INTEGER NOT NULL` |
       | 2 | `frozen` | `BOOLEAN NOT NULL DEFAULT 0` | `BOOLEAN NOT NULL` |
       | 3 | `prospective_eligible` | `BOOLEAN NOT NULL DEFAULT 0` | `BOOLEAN NOT NULL` |
       | 4 | `version` column ordinal | 9 | 3 |
       **A second live rewrite is NOT authorized** merely to restore those historical DDL details. The
       reason for accepting rather than rewriting is risk minimization, all independently verified: all 24
       rows survived; all 24 × 28 stored cells were proven identical; every `source_run_id` value is
       unchanged; the unwanted live FK is gone; FK enforcement can be enabled with zero manifest/run
       violations; the three removed defaults are not required by the current canonical SQLModel writer;
       the ordinal change carries no intended semantic meaning; and a second destructive table rewrite
       would add live operational risk for low-value restoration of historical DDL shape.
       - **A8 — What this acceptance is NOT.** It is a narrow, enumerated, post-incident acceptance of
         four known residual differences. It is **NOT** a general waiver of AG-18; **NOT** permission for
         further schema drift; **NOT** permission to mutate any manifest value; **NOT** permission to
         perform another live rewrite; **NOT** permission to broaden Stage B1; and **NOT** a claim that
         the migration originally stayed within its authorization. **The iter-11 migration DID exceed the
         original A1/AG-18 schema bound — record that fact honestly.** The four residual differences are
         **not desirable**; they are merely accepted as the current bounded end state. The accepted
         residual set **must not become a precedent**.
       - **A9 — B1 live end state (the operative contract).**
         > manifest values unchanged · `source_run_id` FK absent · original indexes preserved ·
         > known four-item DDL residual accepted · no second corrective live rewrite required
       - **A10 — Migration implementation must derive from captured live DDL (future safety only).** Root
         cause of the residual: `j11_schema_migration.py` captured the original live DDL but then built
         the replacement table from `NextSessionManifest.__table__.to_metadata(...)`, reconstructing MODEL
         shape rather than LIVE historical shape. A future migration must produce **the original live
         `CREATE TABLE`, MINUS ONLY the `FOREIGN KEY(source_run_id) REFERENCES scanner_runs(id)` clause**:
         take the captured original DDL as the authoritative physical schema source, transform only that
         one FK clause, create the shadow table from the transformed DDL, copy rows by explicit column
         name, and reissue the original indexes verbatim. Never generate the table body from SQLModel
         metadata; never hand-author the replacement schema independently. Column names, order, types,
         nullability, server defaults, primary key, unrelated constraints and indexes must all be
         untouched. **The transformation fails closed** if the expected FK clause cannot be identified
         exactly — no broad regex that could silently remove an unrelated constraint. This fix is for
         correctness, testability and future retry safety; **it must NOT be run against the live database.**
       - **A11 — Deferred to Stage G, not blockers, not to be mutated.** (a) The `preFreezeEra` branch in
         the manifest strip currently masks the new `unverifiable` badge on live rows. If that branch
         remains honest and fail-closed it is a **Stage G product-verification item**, not a Stage C
         blocker, and no UI/browser work may be pulled forward into a cleanup iteration; if it is actually
         misleading or fail-open, surface the exact contradiction and STOP rather than broadening
         silently. (b) Manifest export-file discrepancies (recorded `export_path` values with no file on
         disk; files on disk for dates with no manifest row) predate this work: do **not** repair or
         delete files, mint manifests, or change `export_path`. Record it as an immutable-evidence
         reconciliation item for Stage G; only if inspection shows it makes Stage C unsafe should it be
         surfaced as a blocker.
       - **A12 — Stage C READY gate.** Stage C may be marked READY only when ALL of these hold, and the
         iteration must return the explicit owner-facing line `J-11 STAGE C READY: YES / NO`:
         J-10 closed with no stale `20/567` operative wording remaining; the exact four-item DDL residual
         accepted and documented; the live manifest FK still absent; 24 manifest rows still unchanged; the
         migration utility fixed for future exact-DDL-minus-FK behaviour; `basis_disclosure` null/malformed
         timestamp cases failing closed; the `models.py` comment no longer falsely claiming an exact
         physical match; maintenance isolation still active; all targeted tests passing; **zero live-database
         writes** in the cleanup iteration; and no new blocker discovered. **Stage C is still NOT executed
         in that iteration** — it waits for an explicit owner instruction to resume.
       - **A13 — Live database is READ-ONLY for the B1 cleanup iteration.** Expected live writes: **ZERO**.
         No further `DROP TABLE`, table swap, corrective `ALTER`, ordinal reconstruction, manifest-row copy,
         or any schema mutation to `next_session_manifests`. Verify before and after — `daily_prices`,
         `scanner_runs`, manifest row count, manifest values, manifest live DDL, indexes, `forward_returns`,
         provider runs, and any user state already tracked in the Stage B inventory — using the strongest
         practical read-only fingerprinting the J-11 evidence framework already provides. **Do not claim
         "no write" from row counts alone.**
       - **A14 — iter-11's REGRESSION verdict stands.** Do not rewrite or delete it. This acceptance
         resolves only whether the already-materialized residual must be undone; it does **not**
         retroactively turn iter-11 into a clean PASS. The honest lineage to preserve is: *iter-11
         migration — primary goal succeeded, stored state preserved, unauthorized DDL residual detected,
         REGRESSION recorded, owner later accepted the exact residual instead of ordering a second rewrite.*

       ## OWNER AUTHORIZATION — J-11 Stage C (owner, 2026-08-24)

       **Stage C is AUTHORIZED.** Iteration 12's evaluator independently re-derived all thirteen of
       ruling A12's readiness conditions, found no unresolved technical blocker, and halted STALLED
       solely because A12 reserves the destructive step for an explicit owner instruction. This is that
       instruction. **The authorization is narrow.** It authorizes ONLY the incident-bounded destructive
       clear already defined by this J-11 contract, for the exact 11 incident dates. It does **NOT**
       authorize Stage D or any later stage, automatically or by implication.
       - **C1 — Date-set boundary.** The authorized set is EXACTLY the 11 dates enumerated in the
         "**The incident date set — all 11, not the 8 currently absent**" bullet above. For the avoidance
         of doubt they are `2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27,
         2026-08-03, 2026-08-05, 2026-08-10, 2026-08-11, 2026-08-12`. **If this restatement and that
         authoritative bullet ever disagree, STOP** — do not reconcile them by choosing one. No date may
         be added, inferred from current cadence, selected from a range, or reached by historical-density
         backfill. No "all affected-looking dates". No full-history clear. **The exact 11-date set is the
         sole authorization boundary.**
       - **C2 — Fresh preflight is mandatory, before the first destructive statement.** Re-run the Stage C
         preflight required by step 13 and re-derive live state; do NOT trust iteration-10/11/12 counts
         merely because they were certified. Freeze a NEW Stage C attempt identity. Capture at minimum:
         current git HEAD; the goal.md / J-11 contract identity hash; engine identity; config identity;
         the exact 11-date set; `daily_prices` fingerprint; `scanner_runs` inventory by exact incident
         date; `scanner_results`, `sector_scores`, `theme_scores` inventories; the `forward_returns`
         inventory relevant to affected runs/dates; manifest row count, full-row fingerprint, DDL
         fingerprint and index set; provider-run state; watchlist/user-state counts and fingerprints
         already protected by J-11; and the ledger/prereg/evidence fingerprints already defined. Persist
         it as Stage C pre-delete evidence. **If the fresh preflight materially differs from the certified
         iteration-12 state, or any B/B1/B2 invariant no longer holds, STOP before deletion.**
       - **C3 — Manifest preconditions re-proven before deletion.** 24 rows; no live FK on
         `source_run_id`; values unchanged from the certified state; the four owner-accepted DDL residuals
         unchanged; the three original indexes unchanged; `source_run_id` provenance values unchanged; no
         manifest regenerated, rebound or upgraded since certification. Do **not** treat `source_run_id`
         as a live relational identity and do **not** "repair" orphan values.
       - **C4 — Layer boundary. Stage C clears Layer 2 ONLY.** Layer 1 (canonical inputs — `daily_prices`
         and provider provenance) is **preserved**; Layer 2 (`scanner_runs`, `scanner_results`,
         `sector_scores`, `theme_scores`, and the associated forward-return derived state) is the
         **authorized incident-bounded clear**; Layer 3 (manifests, audits, recovery provenance, ledgers,
         preregistrations, incident evidence) is **preserved**. Expected new canonical-input writes:
         **ZERO**. Do not modify stock/universe reference data, ETFs, sectors, industries, themes, theme
         membership, macro series, provider source rows, or J-10 recovery evidence. **No Yahoo/Stooq or
         any network work belongs in Stage C. J-10 is CLOSED and MUST NOT reopen.**
       - **C5 — Immutable evidence and user state.** Do not delete, mint, regenerate, version-increment,
         rehash or re-export manifests; do not modify `source_run_id`, `source_run_created_at` or
         `prospective_eligible`; do not rewrite evidence ledgers, referee history, preregistration state,
         incident evidence, J-10 provenance, or historical evaluator verdicts. **Iteration 11's REGRESSION
         remains historical truth.** Do not touch the watchlist, user configuration/state, saved
         selections, or unrelated caches with no dependency on cleared derived state — classify before
         touching if a dependency is uncertain. "Cleanup" is never permission for a broad reset.
       - **C6 — Bounded mechanism only.** Use `clear_snapshot_dates(EXACT_INCIDENT_DATE_SET)` or the
         narrowest canonical equivalent already prescribed above — **never** `clear_snapshot_set()` or any
         path semantically equivalent to clearing the whole snapshot/forward-return history. The clear must
         be **mechanically constrained** to the 11 dates. Re-derive actual FK/dependency ordering from the
         current code and schema and use the safest bounded child-before-parent order; do not guess
         ownership from table names. Invariant: after Stage C **no surviving derived object may falsely
         claim to be authoritative for one of the 11 incident dates on the strength of pre-repair run
         state** — but do not delete unrelated derived history merely because it references an affected
         measured date unless this contract explicitly classifies it as part of the incident repair.
       - **C7 — Forward returns.** Clear only what must be removed before canonical Stage D/E
         reconstruction, following this contract exactly. **Do not perform the final global/create-once
         forward-return repair in Stage C** unless this contract explicitly assigns that action to Stage C.
         The sequence stays C (bounded clear) → D (exact 11-date canonical regeneration) → E (canonical
         forward-return hole repair) → F (dependency-aware cache handling) → G (final serving/replay
         verification). **Do not collapse C→G into one developer action.**
       - **C8 — No manifest creation during Stage C. Stage C is deletion only.** Any regeneration path
         capable of calling `get_or_create_manifest(...)` must NOT run. No historical manifest may be
         created for the seven incident dates that currently have none, and no new version minted for the
         four dates that already carry manifests. Existing manifests stay byte/value invariant.
       - **C9 — Restart safety.** Freeze the attempt identity, record pre-state, record the exact intended
         delete set, record actual delete counts, and persist a completion marker **only after
         verification**. Never infer "resume from halfway" from partial table counts. If Stage C fails
         mid-flight: STOP, inventory actual live state, do not continue to Stage D, and do not pretend
         Stage C completed — then follow the restart/retry contract in step 13.
       - **C10 — Stage C stands alone, and STOPS.** The Stage C iteration must be scoped to Stage C only;
         **if the decomposer combines C with D or broader J-11 work, the decomposition must be corrected
         before developer execution.** Maintenance isolation, `Depth: full` and depth enforcement remain
         in force throughout — full depth means developer, reviewer, static/file-scoped QA, auditor,
         coherence and evaluator, **not** application-service execution. After the bounded clear completes
         and is independently verified, **STOP THE ENGINE** and return exactly
         `J-11 STAGE C COMPLETE: YES/NO` and `J-11 STAGE D AUTHORIZED: NO`. Successful Stage C is **not**
         implicit authorization for Stage D: no ScannerRun regeneration, no sector/theme rebuild, no
         forward-return backfill, no cache invalidation or re-warm, no service start, no `GET /api/compass`,
         no J-01/J-02/J-03, no Stage G. The owner inspects Stage C mutation accounting first.
       - **C11 — Two recorded framework findings stay out of Stage C.** (a) The `goal_gate.py` duplicate
         J-ID journey-hashing defect (a nested `- **J-NN ...` bullet is read as a journey heading, letting a
         later duplicate block overwrite the earlier one) is REAL: it does not block this already-ratified
         Stage C, but it **must be fixed before any future reliance on journey-hash drift for edited
         J-10/J-11 text, and before GOAL_ACHIEVED certification**. Do not pull that fix into the Stage C
         destructive iteration unless the Stage C decomposer itself must edit J-10/J-11 contract text in a
         way whose safety depends on that gate. (b) The manifest-migration live-vs-model column-list defect
         is REAL but **not a Stage C blocker** — the migration does not run in Stage C and the live/model
         column sets are known equal; it is a **mandatory precondition/fix before any future live
         manifest-table migration**. **Do not touch the manifest migration in Stage C.**
       - **C12 — No redesign.** This run executes the already-ratified contract. Do not redesign J-10,
         J-11, candidate thresholds, manifest semantics, research architecture, Tapeology integration, or
         the prospective/OOS rules. No speculative goal hardening.

       *The two rulings below are new and Stage-D-facing. They stand on their own — they are NOT part of
       the Stage C authorization above, which remains exhausted and unchanged, and they revoke nothing
       already recorded.*

       ### OWNER RULING — AVB two-row raw-volume correction before Stage D
       *(owner, 2026-08-25 — binding, narrowly scoped)*

       Iteration 15 settled the previously open AVB convention question with the single-use AG-9 dated
       exception #2. The committed evidence proves that AVB's **2026-08-11** and **2026-08-12** recovered
       rows are internally inconsistent with Trendora's own stored AVB convention:
       - surrounding stored AVB bars are **`bridged price + compensating volume`**;
       - the two J-10 recovered bars are **`bridged price + raw volume`**;
       - their dollar volume is therefore inflated by approximately the persisted bridge factor
         **`2.7930001225759193`**;
       - the resulting classification is **AVB-C** and J-11 Stage D is **NOT ready**.

       **The owner authorizes one bounded corrective raw-layer mutation BEFORE Stage D readiness may be
       reconsidered.** Authorized mutation scope is exactly:
       - table: **`daily_prices`**
       - symbol: **`AVB`**
       - dates: **`2026-08-11`, `2026-08-12`**
       - mutable field: **`volume` only**

       No other symbol, date, OHLC field, table, row, provider record, manifest, `ScannerRun`, forward
       return, provenance row or historical artifact may be modified under this ruling.

       The corrected values must be derived **deterministically** from the already-committed iteration-15
       provider evidence and the proven surrounding stored convention. **No new network fetch is
       authorized. AG-9 dated exception #2 remains exhausted.**

       This does **NOT** reopen J-10 as a recovery programme. **J-10 remains historically closed at its
       recorded terminal state** (585 restored; EA and EQR accepted unrestorable; AG-9's recovery-fetch
       authorization exhausted). This is a narrowly authorized post-J-10 correction of a defect discovered
       by the later J-11 readiness audit.

       The existing J-11 rule that `daily_prices` must remain unchanged is **narrowly amended** as follows:
       > Before Stage D, exactly the two authorized AVB `volume` cells above may be corrected **once**.
       > Their before/after values and derivation must be persisted as mutation evidence. After that
       > correction passes verification, the corrected `daily_prices` state becomes the **new certified
       > raw-input baseline** for J-11. From that point onward J-11 again treats `daily_prices` as
       > immutable.

       All other J-11 raw-input protections remain unchanged. **If the exact correction cannot be derived
       and verified fail-closed from the committed evidence, STOP for owner review rather than guessing.**

       **Even if the subsequent readiness evaluation returns `J-11 STAGE D READY: YES`, STOP for owner
       review.** Stage D is **NOT** authorized by this ruling and requires a separate explicit owner
       instruction before J-11 Stage D execution may begin.

       ### OWNER RULING — pre-boot incident guard required
       *(owner, 2026-08-25 — binding)*

       Iteration 15 proved that the current normal backend startup path can itself violate the J-11
       quarantine: `ensure_latest_snapshot()` resolves the latest stored price date and calls the
       canonical scan producer; while the latest date is an incident date intentionally holding zero
       `ScannerRun`s, **merely booting the backend can recreate derived state before Stage D begins.**

       **Operator discipline alone is no longer sufficient.**

       Before any normal backend, browser, replay or Stage-G application lane is allowed to resume, the
       implementation must provide and test a **fail-closed pre-boot guard** that prevents canonical
       producer writes for dates explicitly quarantined by an active maintenance/incident-recovery
       boundary.

       The guard must be **reusable and state-driven, not hardcoded** to AVB or 2026-08-12, and must
       preserve normal latest-snapshot startup behaviour once the maintenance boundary is legitimately
       cleared.

       **Until that guard is proven on disposable test state, maintenance isolation remains ACTIVE and the
       live backend must not be booted.**

       **Sequencing (unambiguous, and it does not start Stage D):** AVB bounded correction → verify the
       new raw-input baseline → implement and prove the pre-boot guard → re-run Stage D readiness → if
       `J-11 STAGE D READY: YES`, **STOP for owner authorization**. **Stage D remains forbidden until a
       later explicit owner instruction.**

       ### OWNER RULING — J-11 maintenance-boundary lifecycle AUTHORIZED
       *(owner, 2026-08-25 — binding; supersedes nothing, revokes nothing)*

       Iteration 16 delivered the pre-boot guard as *code* and proved it on disposable fixture state, but
       the evaluator's adjudication stands: **"proven on disposable test state" is necessary, not
       sufficient.** On the live database `evaluate_boundary_for_date()` returns `blocked=False` for every
       date, for the trivial reason that **no `MaintenanceBoundary` row has ever been registered there.**
       A guard that protects nothing is not a guard. Iteration 16's own status line was therefore honest
       and remains correct: `J-11 LIVE PRE-BOOT GUARD: NOT ARMED`.

       **I authorize an explicit persisted J-11 maintenance-boundary lifecycle.** Its sole purpose is to
       make the pre-boot quarantine guard *effective on the live database* rather than merely
       fixture-proven. This authorization is **operational safety state only** — it buys quarantine
       enforcement, and nothing else.

       **AUTHORIZATION MATRIX — read these two lines as separate facts:**

       | Item | Status |
       |---|---|
       | **J-11 maintenance-boundary lifecycle** (create/activate, later deactivate) | **AUTHORIZED** |
       | **J-11 Stage D execution** (derived-state regeneration for the 11 dates) | **NOT AUTHORIZED** |

       `J-11 STAGE D AUTHORIZED` must remain **NO**. **A `J-11 STAGE D READY: YES` readiness verdict is
       not, and must never be rendered as, Stage D authorization.** Readiness is a measurement;
       authorization is an owner act. Nothing in this ruling starts Stage D, plans Stage D, or licenses a
       Stage D spec.

       **Exact boundary scope.** The boundary must cover exactly these eleven dates and no others:

       > `2026-05-12` · `2026-05-13` · `2026-07-10` · `2026-07-13` · `2026-07-24` · `2026-07-27` ·
       > `2026-08-03` · `2026-08-05` · `2026-08-10` · `2026-08-11` · `2026-08-12`

       This set is identical to `app.engine.j11_maintenance.INCIDENT_DATES` (verified equal on
       2026-08-25). Membership must continue to be **sourced from that constant, never re-typed as a fresh
       literal** — the same trap step 11 already flagged. Arming must fail rather than broaden the
       quarantine scope accidentally.

       **Authorized live writes are limited to maintenance-boundary state only.** Do **not** write to
       `daily_prices`, `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`,
       `forward_returns`, `next_session_manifests`, `data_provider_runs`, provenance, or any other
       research/business table. Expected live mutation this iteration: **exactly one maintenance-boundary
       row**, and nothing else.

       **No schema migration.** Do not migrate, ALTER, or rewrite any table. **If the maintenance-boundary
       table or the required schema does not already exist exactly as required, STOP and report the
       blocker — do not create it and do not migrate to it.**

       **Lifecycle — deactivate, do not delete.** After the J-11 repair/rebuild lifecycle is eventually
       complete, the same boundary may be deactivated **only** after the relevant final
       release/unquarantine gate passes. Prefer deactivation (`active=False`) over deletion so the
       maintenance history stays auditable. **Do not clear or deactivate the boundary during this
       iteration merely to prove the code works** — a disarm proven on disposable state is sufficient
       evidence; disarming the live boundary is not.

       **Implementation requirements (binding).**

       1. **Make the production boot guard actually effective.** The safety property must hold as *code +
          persisted state*, not operator discipline: quarantined J-11 date → backend boot / warmup →
          maintenance-boundary check → **blocked** → **no `run_scan` write**. "Do not start the backend"
          is not an acceptable control.
       2. **Keep fail-closed semantics.** Malformed, contradictory, unexpectedly duplicated, or
          otherwise unevaluable boundary state must fail **closed**. Ambiguous maintenance state is never
          silently treated as "not blocked".
       3. **Fix AG-8 — remove the unbounded `MaintenanceBoundary` load from the shared boot path.** The
          current `select(MaintenanceBoundary)` at `apps/backend/app/engine/j11_preboot_guard.py:143` is a
          whole-table ORM load on a path every boot crosses. Replace it with a query explicitly
          constrained to the minimum relevant **active** state: filter to active/relevant rows, project
          only the fields the decision needs where practical, apply a deterministic finite bound (or an
          equivalent design), and **fail closed if the bound is exceeded or the state is unexpectedly
          ambiguous**. No whole-table ORM loading on boot. Preserve correct behaviour for the current
          J-11 boundary. Choose the simplest robust implementation — **do not build a generic policy
          engine.**
       4. **Provide an explicit arm path.** A committed, production-capable path for
          registering/activating the J-11 boundary. It must be idempotent, must avoid duplicate active
          boundaries, must validate the exact incident-date set, must write only authorized
          maintenance-boundary state, must make a second identical invocation safe, and must fail rather
          than broaden scope. **It must not live only inside a test fixture or a one-off Python snippet.**
          If it is a CLI/admin command, require explicit invocation and make its mutation obvious.
       5. **Provide a future disarm/deactivation path.** Production-capable, scoped to exactly the J-11
          boundary, must not delete unrelated maintenance history. **Do not invoke it now.**
       6. **Tests (committed, disposable state only).** At minimum: **(A)** empty/unarmed state does not
          falsely demonstrate protection; **(B)** once armed, all 11 incident dates are blocked;
          **(C)** a normal non-incident date is not blocked by this boundary; **(D)** duplicate arm
          invocation is idempotent; **(E)** unexpected duplicate/ambiguous active state fails closed;
          **(F)** the bounded-query guard does not require loading the whole `MaintenanceBoundary` table;
          **(G)** boot/warmup cannot reach `run_scan` for a quarantined date while the boundary is active;
          **(H)** no forbidden research/business-table writes occur while arming; **(I)** the deactivation
          path is correctly scoped — **without** deactivating the live boundary.
       7. **Live verification (read-only, after tests pass).** Confirm: the expected J-11 boundary exists
          and is active; it covers exactly the 11 approved dates; no unrelated active boundary was
          modified; the boot guard evaluates the quarantined dates as blocked; no `ScannerRun` or other
          forbidden J-11 state was created; no `daily_prices` value changed; no Stage D work occurred.
          **Do not boot the live backend merely as an unsafe experiment.** If the boot path cannot be
          verified without risking forbidden writes, verify through the same production guard entry point
          using a non-writing diagnostic/test harness **and report that limitation clearly.**

       **Stop conditions — return `STALLED` rather than expanding scope if:** schema migration would be
       required; any write outside maintenance-boundary state would be required; the exact incident-date
       set cannot be represented safely; the live boundary cannot be armed without touching forbidden
       state; boot safety cannot be made fail-closed; or delivering this would require starting Stage D.
       **These stop conditions are not permission to redesign Stage D or to continue broader J-11
       research.**

       **BLOCKER ON RECORD — the live table does not exist (verified read-only, 2026-08-25).** Before any
       implementation work, the live database was inspected read-only (`mode=ro` + `PRAGMA
       query_only=ON`): it holds **exactly 24 tables and `maintenance_boundaries` is not among them**
       (`SELECT count(*) FROM sqlite_master WHERE type='table' AND name='maintenance_boundaries'` → `0`).
       The `MaintenanceBoundary` model was added in iteration 16, but the live table is normally minted by
       `main.py`'s ordinary `create_db_and_tables()` → `SQLModel.metadata.create_all` on **boot** — and
       booting is precisely what maintenance isolation forbids. **The table's absence is a consequence of
       the quarantine itself.** Therefore the arm step of requirement 4 and all of requirement 7 are
       **BLOCKED**, and this ruling's own stop condition applies: the live arm must return `STALLED` with
       the blocker named. **Creating the table is NOT authorized** by this ruling — the text above says
       "do not create it" explicitly, and no agent may reinterpret an additive `CREATE TABLE` on the live
       8.4 GB database as exempt because it is "purely additive". Requirements 1, 2, 3, 5, 6 and the
       committed (but un-invoked) arm path of requirement 4 are **NOT blocked** and must still be
       delivered in full. Until the owner separately authorizes the table's creation:
       `J-11 MAINTENANCE BOUNDARY: NOT ACTIVE` and `J-11 LIVE PRE-BOOT GUARD: NOT ARMED` are the only
       honest status lines, **maintenance isolation remains ACTIVE, and the live backend must not be
       booted.**

       ### OWNER RULING — J-11 exact maintenance-boundary table creation and live arm AUTHORIZED
       *(owner, 2026-08-25 — binding; supersedes the previous prohibition on creating
       `maintenance_boundaries` only to the exact extent stated below)*

       **Chronology — iteration 17 was right, and stays on the record.** The "BLOCKER ON RECORD"
       paragraph immediately above, and iteration 17's `STALLED` live-arm outcome, are **correct and
       are preserved verbatim for auditability.** Iteration 17 stopped exactly as the owner contract
       *in force at that time* required: the table was absent, creating it was forbidden by name, so it
       named the blocker and halted rather than reinterpreting an additive `CREATE TABLE` as exempt.
       That was the right call and must not be re-described as a mistake, softened, or edited away.
       **This ruling is a strictly later owner authorization that removes exactly that one blocker** —
       it changes what is permitted from now on; it does not change what was permitted then.

       **Scope of the override — narrow and exact.** This ruling overrides the earlier sentence
       *"do not create it and do not migrate to it"* **ONLY** for the *exact creation of the single
       `maintenance_boundaries` table through the bounded operation described below.* It revokes
       **nothing** else: the prohibition on arbitrary migrations, `ALTER`s, table rewrites, schema
       cleanup, and broad schema mutation stands in full, as does AG-18 and the iter-11 DDL-residual
       ruling.

       **1. Exact schema creation is now authorized.** A future J-11 iteration is authorized to create
       exactly one missing additive table on the live Trendora database: **`maintenance_boundaries`**.
       It must be created from the already-committed canonical
       **`app.models.MaintenanceBoundary.__table__`**, or an equivalently exact schema-derived
       operation. **Do not hand-author an independent duplicate schema** if the committed SQLModel
       table can be used directly. The resulting live table must exactly match the committed model the
       J-11 guard requires. **If the table already exists:** inspect it first; if it exactly matches
       the required schema, do **not** recreate it; if it does **not** exactly match, **STOP** — do not
       `ALTER` it, do not migrate it, do not repair it by guesswork.

       **2. Broad startup/schema machinery is NOT authorized for this operation.** Do **not** use
       ordinary backend startup as the mechanism. Do **not** invoke the broad production
       `create_db_and_tables()` for the purpose of this J-11 schema operation. Do **not** rely on
       `SQLModel.metadata.create_all()` over the *complete* application metadata if that could create
       additional missing tables or trigger other startup schema/index maintenance. The authorized
       mutation boundary is exactly:
       > create `maintenance_boundaries` only.
       No unrelated table, index, column, migration, schema cleanup, or startup mutation is authorized
       by this ruling. **A dedicated confirm-gated maintenance entrypoint must perform the exact
       bounded operation.**

       **3. Live J-11 boundary activation is authorized immediately after successful exact table
       creation.** Once the exact table exists and its schema is verified, the same future iteration is
       authorized to register or activate exactly one J-11 boundary row: **`j11-incident-recovery`**.
       Its quarantined date set must be sourced from the existing canonical
       **`app.engine.j11_maintenance.INCIDENT_DATES`** — **never** retype a second independent date
       list into production registration logic. The persisted row must be **active**, **auditable**,
       **idempotently registered by name**, and **scoped exactly to the canonical J-11 incident date
       set**. **No duplicate boundary row may be created.**

       **4. Exact allowed live mutations.** For the table-create-and-arm iteration, expected live
       mutation is limited to: (1) creation of the single missing `maintenance_boundaries` table, if
       absent; (2) creation or activation of the single `j11-incident-recovery` row. **Nothing else.**
       The iteration must capture before/after evidence proving no unrelated application state changed.
       In particular it must **not** mutate `daily_prices`, `scanner_runs`, `scanner_results`, sector
       scores, theme scores, `forward_returns`, `next_session_manifests`, `data_provider_runs`,
       watchlist state, or existing canonical research outputs. **No incident-date `ScannerRun` may be
       created as a side effect.**

       **5. Maintenance isolation stays ACTIVE during creation and arming.** The live backend remains
       **OFF** throughout the table-creation and boundary-activation procedure. Do not boot the app
       until: the table exists; the J-11 row is active; and a direct live guard probe proves the latest
       quarantined date is blocked. Creation and arming must occur through **explicit maintenance
       tooling, not ordinary product boot.**

       **6. The live guard must be proven ARMED before normal backend boot is allowed.** After
       activation, verify directly against the live database that: the persisted J-11 boundary exists;
       `active=True`; the persisted quarantined date set **exactly equals** the canonical J-11 incident
       dates; `evaluate_boundary_for_date(...)` returns **blocked** for the relevant quarantined dates;
       the current latest stored incident date is **blocked**; and **no `ScannerRun` was created during
       the verification**. Only after that evidence is recorded may the status become
       `J-11 MAINTENANCE BOUNDARY: ACTIVE` and `J-11 LIVE PRE-BOOT GUARD: ARMED`.

       **7. Close the boot-path coverage gap before calling the guard generally safe.** The synchronous
       latest-snapshot path already checks the maintenance boundary before its `run_scan`. **However
       the background historical warmup also contains boot-initiated canonical `run_scan` calls.** A
       future implementation iteration must ensure **every** boot-initiated path capable of creating a
       canonical `ScannerRun` respects the same persisted maintenance-boundary contract — at minimum
       the historical background warmup cadence loop. **Do not solve this with a second hardcoded J-11
       date conditional**; the protection must remain **state-driven from the persisted boundary**.
       Required behaviour: active matching boundary → skip/refuse the protected canonical write;
       ambiguous or unreadable relevant boundary state → **fail closed**; explicitly cleared boundary →
       normal behaviour resumes; no registered boundary in an ordinary healthy system → normal
       behaviour **unchanged**. This requirement exists so the guard stays correct **after the latest
       stored date moves beyond the current incident window.**

       **8. Preserve current J-11 readiness and authorization semantics.** The Stage D readiness result
       may remain `J-11 STAGE D READY: YES` — but **READY is not authorization.** This ruling does
       **NOT** authorize Stage D. Throughout the next table-create / arm / guard-completion iteration,
       `J-11 STAGE D AUTHORIZED: NO` must remain true. Do **not**: start Stage D; rebuild incident-date
       `ScannerRun`s; generate incident-date manifests; freeze a reusable Stage D execution identity;
       or treat successful guard arming as implicit Stage D permission.

       **9. Required stop point.** The future implementation iteration must stop when it can truthfully
       report:
       ```text
       J-11 MAINTENANCE BOUNDARY: ACTIVE
       J-11 LIVE PRE-BOOT GUARD:  ARMED
       J-11 STAGE D READY:        YES
       J-11 STAGE D AUTHORIZED:   NO
       ```
       If any of the first three cannot be established, **report the exact blocker and STOP.** **Even
       if all three are established, STOP.** Actual Stage D execution requires a separate later
       explicit owner authorization.

       **10. Fresh Stage D identity rule remains binding.** Do **not** freeze or reuse a Stage D
       execution identity during the maintenance-boundary iteration. Any future owner-authorized
       Stage D execution must freeze a **fresh** execution identity immediately before its first
       authorized Stage D write, under the final code, config, data baseline and guard state.

       ### OWNER RULING — J-11 Stage D through Stage G recovery execution AUTHORIZED
       *(owner, 2026-08-26 — binding)*

       Iteration 18 satisfied the owner-required pre-Stage-D safety gate:

       - the J-11 maintenance boundary is **ACTIVE**;
       - the live pre-boot guard is **ARMED**;
       - all eleven canonical incident dates are blocked by the persisted boundary;
       - the corrected raw-input baseline is **certified**;
       - `J-11 STAGE D READY: YES`;
       - no Stage D rebuild has yet occurred.

       The owner now **explicitly authorizes execution of the already-defined J-11 recovery sequence
       from Stage D through Stage G.** This authorization covers **only** the existing J-11 sequence:
       > Stage D canonical regeneration
       > → Stage E forward-return hole repair
       > → Stage F dependency-aware cache invalidation / refresh
       > → Stage G full verification

       This ruling does **not** authorize any broader recovery, redesign, provider fetch, exploratory
       cleanup or normal Market Compass work.

       **1. Stage D is now explicitly authorized.** Set the authoritative contract state to
       `J-11 STAGE D AUTHORIZED: YES`. Stage D may regenerate **exactly** the canonical eleven incident
       dates already defined by `app.engine.j11_maintenance.INCIDENT_DATES`. **No additional date may be
       added. No incident date may be omitted and represented as a successful attempt.** The
       clean-regeneration unit remains the **complete eleven-date set**.

       **2. Fresh execution identity immediately before the first Stage D write.** Immediately before
       the first actual Stage D write, compute and persist the **fresh current** J-11 attempt identity
       using the canonical engine-identity mechanism already defined by this goal. Do **not** reuse: the
       iteration-10 identity; the iteration-14 identity; the iteration-16/17/18 readiness identity; or
       any historical frozen identity. The identity must represent the **actual code, config and
       certified data baseline used by this Stage D attempt.** All eleven newly rebuilt `ScannerRun`s
       from the same successful attempt must carry that same frozen identity. If the relevant
       engine/config identity changes before Stage G completes, the attempt is **incomplete** and must
       follow the existing full-attempt retry semantics rather than continuing piecemeal.

       **3. Raw inputs remain immutable.** The post-AVB-correction certified `daily_prices` state is the
       authoritative J-11 raw-input baseline. Stages D through G **must not modify `daily_prices`**. **No
       provider/network fetch is authorized. AG-9 remains closed.** No additional recovery of J-10 raw
       inputs is authorized; **J-10 remains historically closed.**

       **4. Maintenance isolation remains mandatory through Stage G.** The active `j11-incident-recovery`
       maintenance boundary must remain **ACTIVE** throughout Stages D, E, F and G. **Do NOT deactivate
       or clear it before Stage G has passed all required verification.** Throughout the D → G attempt:
       normal backend remains **OFF**; frontend remains **OFF** where it would require the backend;
       browser QA remains **OFF**; replay remains **OFF**; Data Manager remains **OFF**; ordinary API
       requests remain **forbidden**; **no** normal application warmup may run; and **no** unrelated
       producer may operate concurrently. Only the explicitly authorized J-11 recovery tooling and
       verification paths may write during this window.

       **5. Ordinary request / Data-Manager guard gaps are recorded but deferred.** Iteration 18
       established that some ordinary, non-maintenance `ScannerRun` creation paths do **not** yet consult
       the persisted maintenance boundary, including: `scanner.resolve_run()` for an explicit `?as_of=`
       request; and ordinary Data Manager persistence paths capable of calling `run_scan()` or
       `persist_run_payload()`. **These are real hardening gaps and must not be erased or described as
       resolved.** However, they are **NOT a blocker** to the controlled Stage D → G attempt, because this
       ruling keeps every such ordinary path **unreachable** through mandatory maintenance isolation.
       **Do not expand the Stage D recovery iteration into a generalized `ScannerRun` writer redesign. Do
       not patch read pages, Data Manager, or introduce a new generic persistence architecture merely to
       satisfy this ruling.** Record these gaps as **post-J-11 maintenance-boundary hardening work after
       Stage G.** If any ordinary application writer becomes reachable during D → G, **STOP** rather than
       relying on the known gaps.

       **6. Stage D write scope remains exact.** Stage D may create **only** the canonical derived state
       required for the eleven authorized incident dates, through the **existing canonical scanner path.**
       Do **not**: change scoring formulas; add recovery-specific formulas; change thresholds; hand-edit
       `ScannerRun` rows or child rows; rewrite surviving historical `ScannerRun`s outside the eleven-date
       set; restamp surviving runs; mutate raw prices; or fetch external market data. The existing J-11
       acceptance criteria and allowlists remain binding.

       **7. Stage E is authorized only as already defined.** After a successful Stage D regeneration,
       Stage E may execute the already-defined **global create-once forward-return hole repair.** It may:
       fill derivable missing forward-return rows; and repair holes caused by the incident according to
       the existing J-11 contract. It may **not**: overwrite surviving forward-return rows; fabricate
       immature horizons; restamp `ScannerRun`s; alter `daily_prices`; or broaden into unrelated
       historical cleanup.

       **8. Stage F is authorized only as already defined.** After Stage E, Stage F may execute the
       existing **dependency-aware cache invalidation and refresh** required by J-11. It must remain
       scoped to caches affected by the recovery. **No unrelated rebuild, broad application
       initialization or ordinary backend boot is authorized merely to perform Stage F.** Use the
       existing safe maintenance paths.

       **9. Stage G is authorized and is the acceptance gate.** Stage G must execute the **full existing
       J-11 verification contract. Only Stage G may declare the incident fully repaired.** At minimum,
       the already-defined J-11 acceptance requirements remain binding, including: exactly the eleven
       incident dates rebuilt; no `ScannerRun` outside that set rewritten; all eleven rebuilt runs carry
       the single fresh attempt identity; corrected raw baseline unchanged; no network fetch;
       forward-return holes repaired according to the existing contract; immutable manifests preserved;
       no unauthorized manifest creation; caches consistent with the rebuilt state; surviving historical
       state untouched where required; no stale derived state remains for the incident set; and full
       before/after and mutation evidence reconciles. **Do not weaken an acceptance gate merely to obtain
       a passing result.**

       **10. Failure semantics remain whole-attempt semantics.** Existing J-11 failure/retry rules remain
       fully binding. If any failure occurs from Stage D onward before Stage G passes: mark the attempt
       **incomplete**; preserve all evidence; keep the maintenance boundary **ACTIVE**; keep normal
       application operation **paused**; do **not** resume from the next unfinished date; do **not**
       accept partial Stage D/E/F/G work as progress. The next authorized retry follows the existing
       **B/B1/B2 re-verification and complete C → G restart semantics for all eleven dates. Do not
       silently improvise a partial recovery strategy.**

       **11. Do not clear the boundary merely because Stage D succeeds.** Successful Stage D alone is not
       enough. Successful Stage E alone is not enough. Successful Stage F alone is not enough. The
       maintenance boundary remains active until **Stage G** establishes the full incident-cleanliness
       claim. Only after Stage G passes may the recovery workflow perform the already-authorized boundary
       **deactivation/release** action according to the existing lifecycle contract. **Preserve the
       boundary row as audit history; deactivate rather than delete.**

       **12. Normal Market Compass work remains blocked until Stage G.** The existing loop-mechanics rule
       remains unchanged:
       > J-10 raw recovery → J-11 clean regeneration → Stage G passes → normal Market Compass work
       > resumes.

       Do **not** use this authorization to work on J-01 through J-09, J-07/J-08 UI work, research
       features or unrelated product backlog while J-11 remains incomplete.

       **13. Launch conditions for Goal Mode recovery execution.** The next Goal Mode resume that
       executes this ruling **must preserve the recovery environment explicitly.** The owner requires
       `CHAIN_MAINTENANCE_ISOLATION=true` and `CHAIN_REQUIRE_FULL_DEPTH=true`. **These must be treated as
       required launch conditions for the D → G recovery execution, not as optional ambient shell
       state.** If the engine cannot provide the required maintenance isolation or full-depth
       review/audit mode, **STOP and report the unmet launch requirement** rather than silently demoting
       depth or disabling isolation. **Do not treat `lean` as equivalent to the required full-depth
       execution.**

       **14. Required terminal outcomes.** The recovery attempt must end in **one of two honest states.**

       SUCCESS:
       ```text
       J-11 STAGE D EXECUTED: YES
       J-11 STAGE E COMPLETE: YES
       J-11 STAGE F COMPLETE: YES
       J-11 STAGE G VERIFIED: YES
       J-11 INCIDENT STATUS: FULLY REPAIRED
       ```

       INCOMPLETE (any failure, refusal or unmet gate from Stage D onward before Stage G passes):
       ```text
       J-11 STAGE D EXECUTED: YES/NO
       J-11 STAGE E COMPLETE: YES/NO
       J-11 STAGE F COMPLETE: YES/NO
       J-11 STAGE G VERIFIED: NO
       J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE
       J-11 MAINTENANCE BOUNDARY: ACTIVE
       ```
       In the INCOMPLETE state, report the exact blocker, preserve all evidence, leave the maintenance
       boundary **ACTIVE**, leave normal application operation **paused**, and STOP. **There is no third
       state.** Do **not** invent an intermediate "partially repaired" status, do **not** report partial
       Stage D/E/F work as progress toward the claim, and do **not** describe an INCOMPLETE attempt in
       language that implies the incident is repaired. `J-11 INCIDENT STATUS: FULLY REPAIRED` may be
       written **only** when Stage G has verified it under §9.
    12. **Stage B2 — freeze ONE engine identity for the whole attempt (owner, 2026-08-21).** J-11's
       claim is that the incident set ends up as one internally consistent current-engine derivation;
       that claim must be testable. Before Stage C, freeze the intended current engine identity and
       the relevant config/rule identity into the pre-reset inventory for **this attempt**. Invariant:
       > Every `ScannerRun` recreated by one J-11 regeneration attempt MUST carry the same
       > `engine_identity`, equal to the identity frozen in that attempt's pre-reset inventory.
       **Clarification — which attempt, and which frozen identity (owner, 2026-08-24).** Read "that
       attempt's" strictly: **Stage D begins a FRESH regeneration attempt from the successfully cleared
       Stage C baseline; its frozen identity is computed immediately before Stage D and applies only to
       the 11 rebuilt incident-date runs. Surviving historical runs retain their existing stamps.**
       Iteration 10's frozen value (`6261ca17…`) is the historical identity of an EARLIER attempt; the
       drift away from it is real and code-side (`compass.py` is a configured `provenance.engine_files`
       member and changed after that freeze, while `config_subset_hash` is unchanged). That drift does
       **not** invalidate the completed Stage C boundary. Therefore: do **not** force the new runs to
       use `6261ca17…`; do **not** mutate, restamp or otherwise touch the 34 surviving runs that carry
       it — they are not members of the new 11-date attempt; do **not** rewrite manifests; and do
       **not** redo Stage C merely because the old attempt identity drifted. The new attempt's identity
       must be recomputed with the canonical `app.engine.engine_identity.compute_engine_identity` at
       freeze time and recorded honestly, never hardcoded. Stage E/F/G may cite that same attempt
       identity for provenance, but Stage E's forward-return repair gets **no** permission to restamp
       any `ScannerRun`.
       A run of "dates 1–5 under engine A → code or config changes → dates 6–11 under engine B" is
       **not** a successful clean regeneration and must not be recorded as one. If the code or config
       identity changes before an attempt finishes, the attempt must **not** be resumed piecemeal — it
       is restarted under one identity per the failure semantics below. This does not relax anything
       already required: the canonical scoring path stands, no recovery-specific formulas, no
       threshold changes, and no hand-editing of regenerated rows.
    13. **Failure and retry semantics — the unit of work is the whole 11-date set (owner, 2026-08-21).**
       The stages say what should happen; they must also say what happens when the process dies after
       the bounded clear or midway through recreating the dates. Without this, a failed attempt leaves
       exactly the per-date archaeology J-11 exists to eliminate — some dates rebuilt, some absent,
       some caches refreshed, some forward returns repaired, and boot warmup free to recreate another
       date behind the operator's back. **Once the destructive phase (Stage C) has begun, if the
       attempt fails before final verification:** keep the engine and app paused for normal operation;
       do **not** boot normal backend warmup over the partial state; do **not** treat partially rebuilt
       dates as accepted progress; preserve the attempt's audit and mutation evidence; delete no
       immutable manifest or audit evidence; fetch no additional market data under J-11; and do **not**
       silently continue from "the next unfinished date". The next authorized retry restarts the whole
       unit: (1) re-verify the J-10 raw-input prerequisite still holds; (2) re-freeze the current
       intended engine/config identity; (3) re-inventory the exact 11-date incident state; (4) re-clear
       the exact allowlisted rebuildable derived state for **all 11 dates**; (5) regenerate all 11
       under the one frozen identity; (6) re-run the canonical missing-forward-return repair;
       (7) explicitly invalidate/refresh affected caches; (8) run the full verification suite.
       > A failed J-11 attempt may be retried idempotently, but **the clean-regeneration unit is the
       > complete 11-date incident set, not an individual date checkpoint.**
       Retry never deletes canonical raw inputs or immutable evidence.
    14. **Transaction expectations — stated honestly (owner, 2026-08-21).** The current machinery does
       **not** offer one atomic transaction across the 11-date clear and rebuild:
       `scanner.run_scan` is a thin compose of `compute_run_payload` + `persist_run_payload`, and
       `persist_run_payload` performs its own flush/commit per run behind its create-once
       IntegrityError guards (`scanner.py:85-130`) — i.e. **the rebuild commits per date**. The goal
       therefore does not claim transactional rollback it cannot deliver. J-11's real safety model is
       the combination of: maintenance isolation (one controlled writer, no warmup race), bounded
       destructive scope (11 dates, allowlisted tables), complete-attempt restart semantics (above),
       pre/post inventories, and fail-closed verification. Do not specify or imply "transaction
       rollback" unless and until the implementation actually supports it.
  - Sequencing (explicit; **operative form as of 2026-08-24** — the pre-iteration-9 form began "finish
    J-10's canonical input repair (567 remaining)", which is now stale and satisfied): **A** J-10 terminal
    prerequisite **already satisfied** (585 restored; EA/EQR accepted unrestorable; AG-9 exhausted; the
    temporary fetch authorization is closed) → **B/B1/B2 completed in iterations 10-11, to be re-verified
    rather than redone** →
    **B** freeze a read-only pre-reset inventory (the exact 11-date target set; row counts by relevant
    table and date; `daily_prices` coverage/fingerprint; manifest count and hashes; manifest export
    fingerprints where practical; `data_provider_runs` audit state; the certified-ledger file hash;
    user-state counts; current engine and config identity — an audit checkpoint, **not** a second
    historical database) → **B1** reconcile the manifest↔`ScannerRun` schema contract and prove its six
    acceptance items (step 11) → **B2** freeze the one intended engine/config identity for this attempt
    (step 12) → **C** bounded derived-state clear (allowlisted tables, 11 dates, no price / manifest /
    audit / user-state deletion) → **D** canonical regeneration of exactly those 11 dates →
    **E** global create-once forward-return hole repair → **F** dependency-aware cache invalidation and
    re-warm → **G** verification. Only after G passes is the incident repaired.
    **On any failure from C onward:** mark the attempt **incomplete**, preserve its audit evidence,
    keep the normal app paused, and have the next retry restart at **B/B1/B2** and redo **C→G for all
    11 dates**. A partial C→G execution is never represented as accepted J-11 progress.
    **Stage G now owns the final incident-cleanliness claim (owner, 2026-08-21).** Moved here from
    J-10, because the derived state these checks read is precisely what J-11 regenerates. Only after
    Stage G may the system assert the repaired-state equivalents of: rebuilt `ScannerRun`s serve the
    **current complete raw basis**; J-01/J-02/J-03 replay clean; Market Compass historical serving is
    internally consistent; and **no stale derived state remains for the 11-date incident set** — in
    particular the recovery-era 2026-08-11/12 runs have been replaced, not merely re-read. The
    manifest-minting verification trap still applies in full: `GET /api/compass` can mint a missing
    historical manifest, so use only the safe verification paths defined in the Acceptance section.
    **The full recovery sequence, unambiguously:** J-10 restores/classifies the whole authorized
    raw-price population → verifies canonical raw input → closes the live-fetch exception ⇒ **RAW LAYER
    RECOVERED, derived incident state still quarantined** → J-11 B/B1/B2 (inventory + schema
    reconciliation + frozen engine identity) → J-11 C→G (clear the exact 11-date derived state, rebuild
    all 11, repair forward returns, refresh affected caches, full verification) ⇒ **INCIDENT FULLY
    REPAIRED** → normal Market Compass lanes resume.

       ### OWNER RULING — J-11 database recovery accepted; one final serving verification remains
       *(owner, 2026-08-27 — binding)*

       This is a **later** owner decision that resolves the serving/replay circularity recorded above.
       It does not revise any earlier ruling, evidence or Stage-G result — all prior J-11 history stands
       as written.

       **1. Accept the completed recovery.** Stages D through G are accepted as **COMPLETE at the
       database / data-repair level**. The following must **NOT** be reopened merely because the J-11
       journey is still recorded `partial`: Stage D canonical regeneration; Stage E forward-return
       repair; Stage F dependency-aware cache handling; Stage G database-level acceptance verification;
       the certified `daily_prices` baseline; the rebuilt eleven incident-date `ScannerRun`s; the
       completed forward-return repair; the completed cache dispositions; the Stage-G database
       acceptance result. Authoritative status:
       ```
       J-11 DATA RECOVERY: COMPLETE
       J-11 DATABASE ACCEPTANCE: COMPLETE
       ```
       The residual `partial` exists **only** because the goal also required serving/replay verification
       that could not legally run while the application-off recovery contract was active. **Do not
       reinterpret that circularity as evidence that the database recovery failed.**

       **2. Exactly one acceptance objective remains:** prove that the repaired Trendora state serves
       correctly through the real application and browser/replay paths. This is a **product
       verification** task, not another recovery programme. Do not broaden it into maintenance-boundary
       architecture, request-path redesign, Goal Mode framework work, or unrelated hardening.

       **3. The canonical repaired DB stays protected.** Do **NOT** use the canonical repaired database
       as the first serving-verification target. Create a disposable, byte-faithful SQLite
       snapshot/clone of the repaired post-Stage-G database using a consistent SQLite backup mechanism,
       and record enough evidence to prove the verification DB began from the repaired canonical state.
       The canonical database remains **OFF** and must not be mutated by this verification.
       Backend/frontend/browser verification runs against the **disposable verification DB only**.

       **4. Run the real product verification.** Against the disposable repaired DB, run the minimum
       real serving/replay verification needed to close J-11 — at minimum establishing that: Trendora
       boots successfully; the Today / Market Compass serving path works; repaired incident-date state
       reads/renders correctly where the existing J-11 acceptance contract requires it; existing
       immutable manifests remain correct; the repaired `ScannerRun`s and forward-return state serve
       consistently; and the product does not rely on fabricated or stale pre-repair state. Use real
       backend/frontend/browser/replay behaviour — do **not** substitute another database-only proof.

       **5. Zero writes on the disposable DB is NOT required.** Its purpose is to observe real
       application behaviour safely, so a normal, intended cache refresh or other already-designed
       disposable serving-side state change is not automatically a failure. Classify actual mutations
       by **meaning**. Serving verification MUST nevertheless **fail** if ordinary page/read behaviour
       causes an unacceptable canonical-data side effect — creating an unexpected `ScannerRun`; minting
       a historical `NextSessionManifest` merely because a page was read, where that violates the
       compute-at-ingest / manifest contract; changing `daily_prices`; rewriting repaired forward
       returns; modifying an existing immutable manifest; rewriting the rebuilt incident-date canonical
       results; or any other mutation contradicting the Market Compass data contracts. **Do not weaken
       an existing product invariant simply because the DB is disposable.**

       **6. Fix only a defect actually demonstrated by serving verification.** The enumerated open
       writer paths remain useful evidence but are **NOT** an instruction to refactor them. Do **not**
       proactively guard or redesign all seven, and do **not** centralize the persistence architecture
       for completeness. If the verification demonstrates that one specific reachable path causes an
       unacceptable side effect, the next Goal Mode work may make the **minimum targeted fix** for that
       demonstrated defect and re-run the verification on a fresh disposable clone. Paths that are not
       reached and do not block serving acceptance stay deferred. **Evidence-driven hardening, not
       speculative hardening.**

       **7. Explicitly deferred — not J-11 closure blockers:** `journey_history_hash` / stall-detector
       redesign; generic Goal Mode anti-tautology framework changes; generic maintenance-boundary
       redesign; blanket hardening of all known writer call sites; auditor trap-citation remapping
       unless it directly prevents final serving acceptance; unrelated product/refactor work. **Do not
       spend another J-11 iteration improving automation infrastructure instead of verifying Trendora.**

       **8. J-11 closure rule.** If the disposable repaired-state serving/replay verification passes
       without an unacceptable product-data side effect, set:
       ```
       J-11 SERVING/REPLAY VERIFICATION: PASS
       J-11 STATUS: PASSING
       ```
       and consider the J-11 incident **CLOSED**; normal Market Compass journey work then resumes per
       the existing goal. **No further owner authorization is required merely to mark J-11 passing**
       once this explicitly authorized verification succeeds. If verification exposes a real product
       defect, keep J-11 `partial` and report **only** the concrete defect that blocked acceptance — do
       **not** reopen the already-passed D/E/F/G recovery stages.

       **9. Scope discipline.** The owner wants the shortest credible path back to the actual Trendora
       product goal: maximum emphasis on proving the repaired Market Compass works; infrastructure
       perfection is not the objective; theoretical future hazards that do not affect this verification
       remain backlog. No broad cleanup, no unrelated research, no new provider/network recovery, no
       re-litigation of J-10/J-11 historical evidence. The next Goal Mode resume should decompose toward
       this final serving verification and then return to normal Market Compass product work.

       #### Post-Stage-G launch-condition clarification
       *(owner, 2026-08-27 — binding; clarifies THIS ruling, does not revise or delete anything earlier)*

       The launch conditions in item **13. Launch conditions for Goal Mode recovery execution** of the
       earlier "OWNER RULING — J-11 Stage D through Stage G recovery execution AUTHORIZED" (hereafter
       §13) — `CHAIN_MAINTENANCE_ISOLATION=true` and `CHAIN_REQUIRE_FULL_DEPTH=true` — applied
       **specifically to the now-completed Stage D → G live recovery execution**. Those requirements are
       **SPENT**. They are **NOT** launch requirements for the separately authorized post-Stage-G
       disposable-DB serving/replay verification defined in items 2-4 above. For that final verification:

       - `CHAIN_MAINTENANCE_ISOLATION=true` **MUST NOT** be required, because the authorized task
         explicitly requires real backend/frontend/browser/replay execution against the disposable
         verification database — the exact activity maintenance isolation forbids.
       - The canonical repaired database remains **OFF** and protected exactly as item 3 requires.
         Backend/frontend/browser/replay may operate **only** against the disposable repaired-state clone.
       - `CHAIN_REQUIRE_FULL_DEPTH=true` is **NOT** required for this final product verification; normal
         Goal Mode evaluation depth may be used.
       - Do **not** interpret removal of those D→G launch conditions as permission to boot or mutate the
         canonical database.
       - Do **not** reopen Stage D, E, F or G database recovery.

       This clarification supersedes §13 **only** for the new post-Stage-G disposable serving-verification
       task. §13 remains historically correct, preserved and unrevised as the launch requirement that
       applied to the completed D → G execution. The sole purpose of this clarification is to prevent the
       decomposer/evaluator from treating the completed recovery's launch environment as a blocker to the
       one remaining browser/replay verification.

  - Acceptance:
    - Every item below is a required check, proven by named tests **plus** live read-only
      verification — not by narrative assertion in a handoff.
    - **Raw inputs:** `daily_prices` unchanged by J-11 (count and fingerprint identical either side of
      the clear); no network fetch occurred during J-11; the price frontier is unchanged by J-11;
      J-10's recovered rows remain intact. **Single narrow exception (owner, 2026-08-25):** the one
      authorized AVB two-cell `volume` correction for 2026-08-11/12 — see "OWNER RULING — AVB two-row
      raw-volume correction before Stage D" in step 11. That correction changes exactly two `volume`
      cells and no row count; once it is verified, the **post-correction fingerprint becomes the new
      certified J-11 raw-input baseline**, and every check above is evaluated against that new baseline.
      Stage D and all later J-11 stages must preserve it unchanged. Raw-input immutability is otherwise
      **not** relaxed: no other cell, row, symbol, date or table may change, and "J-10's recovered rows
      remain intact" continues to hold for every value except those two authorized `volume` cells.
    - **Snapshot scope:** exactly the 11 authorized incident dates were cleared and recreated; **no
      `ScannerRun` outside that set was deleted or rewritten**; rebuilt runs went through the current
      canonical engine path; all required child rows reconcile with their rebuilt parent runs.
    - **Forward returns:** every derivable hole caused by the incident is refilled — including holes on
      **retained** runs from the `measured_date` sweep; surviving rows were not overwritten; genuinely
      immature horizons remain honestly absent.
    - **Manifests:** manifest row count unchanged by J-11 (24 at the time of writing); every pre-J-11
      manifest byte/hash identical; **no new historical manifest appears merely because a snapshot was
      rebuilt**; no `prospective_eligible`, version, or availability-timestamp change; basis disclosure
      correctly identifies a rebuilt or unavailable source-run basis where relevant.
    - **Audit / evidence / user state:** `data_provider_runs` historical rows preserved; certified and
      staging ledgers preserved; trial/alpha history preserved; pre-registrations and graveyard
      preserved; watchlist and user state preserved.
    - **Caches:** no cache claims freshness against a stale pre-reset payload; affected caches either
      provably invalidate or are re-warmed through their canonical producer; **the same-count/same-ID
      stamp collision is explicitly tested** (a test that reproduces an identical `r{max_id}-f{count}`
      stamp across a clear-and-recreate and proves the cache still refreshes).
    - **Operational isolation:** one writer only; no boot warmup inside the destructive window; no
      browser or replay lane; no second backend; no unexplained DB mutation — every write during J-11
      and its verification is reconciled and classified per J-10 step 5a.
    - **Verification must not itself mint a manifest (trap).** `compass.get_or_create_manifest`
      create-once-mints for any **historical** (non-frontier) as-of *regardless of caller*
      (`compass.py:1050-1053`), so a `GET /api/compass?as_of=<incident date>` check would manufacture
      the very artifact this journey forbids and then "prove" immutability against it. For the 7
      incident dates with **no** pre-existing manifest, verify reconstructed scanner/serving state
      through genuinely read-only routes or direct DB assertions. For a date that already has one, it
      is acceptable to confirm the existing artifact still serves unchanged **provided the test proves
      no new manifest or version was created**.
    - **Named traps for the schema/identity/retry blockers (owner, 2026-08-21)** — each is a required
      test, in addition to the ten traps already listed for J-10:
      1. **manifest survival does not depend on FK enforcement being off** — the contract holds with
         `PRAGMA foreign_keys=ON` (or equivalent enforced-FK semantics), not merely with it disabled;
      2. deleting and rebuilding an incident `ScannerRun` does **not** rewrite its historical manifest;
      3. `source_run_id` remains historical provenance and is **never** rebound to the new run's id;
      4. `basis_disclosure` still reports `rebuilt` / `unavailable` correctly once the schema contract
         is reconciled (it resolves by `as_of`, so this must survive the reconciliation unchanged);
      5. all 11 rebuilt runs in one successful attempt share the frozen `engine_identity`;
      6. an engine/config identity change mid-attempt **prevents** piecemeal continuation;
      7. a simulated failure after a subset of dates are rebuilt leaves the attempt **incomplete** —
         never recorded as partial progress;
      8. a retry re-clears and rebuilds the **full 11-date set** rather than resuming from one date;
      9. immutable manifests and audit evidence survive a retry byte-unchanged;
      10. an unrelated cache is **not** invalidated solely because it happens to carry a version field.
    - **Named traps for the J-10/J-11 sequencing boundary (owner, 2026-08-21)** — each a required test:
      1. completing the remaining J-10 raw rows does **not** falsely imply the existing 2026-08-11/12
         `ScannerRun`s were recomputed (the create-once backfill is a proven no-op for them);
      2. J-10 can reach its raw-recovery terminal state **without** J-11 having run — no circularity;
      3. J-11 cannot start before J-10 raw recovery reaches terminal state;
      4. normal product/research lanes remain blocked **after** J-10 and **before** J-11 Stage G;
      5. the final repaired-state J-01/J-02/J-03 replay belongs to J-11 Stage G, not J-10 acceptance;
      6. the stale recovery-era 2026-08-11/12 runs are explicitly recognized as temporary until J-11
         replaces them — never reported as final reconstructed snapshots;
      7. `source_run_id` equality alone **never** proves original-source identity after a rebuild;
      8. **exact numeric id reuse still yields `basis_disclosure = rebuilt`** when the frozen source
         timestamp differs. Construct the case directly: mint a manifest from run id `N` created at
         `T1`; delete and rebuild that run; arrange for the replacement to reuse numeric id `N` with
         `created_at = T2`; then assert the manifest's `source_run_id` is still `N`, its bytes and
         hashes are unchanged, the replacement is **not** treated as the original source merely because
         its id matches, and `basis_disclosure` reports `rebuilt` because
         `source_run_created_at != current_run.created_at`. Id reuse is reachable here — `scanner_runs.id`
         is a rowid alias with no `AUTOINCREMENT` and no `sqlite_sequence` — so this must be proven, not
         assumed away; if a future backend makes reuse genuinely impossible, **prove that instead**.
    - **Honest status & anti-goals:** this journey deliberately does not preserve the accidental
      mixture of incident states — original surviving rows, missing rows, warmup-recreated rows, and
      partial J-10 reconstructions. Inside the 11-date boundary those derived rows are disposable
      deterministic outputs of preserved canonical inputs, and the clean current-engine regeneration
      becomes the one serving derived state for those dates. The immutable historical evidence layer
      remains separate and untouched. Non-goals, explicitly: no full-history rebuild of every
      `ScannerRun`; no change to `scanner.snapshot_cadence`; no change to the snapshot universe outside
      the incident set; no delete/recreate of the whole DB; no deletion of canonical raw prices or
      manifests; no regeneration of old manifests; no evidence-ledger reset; no re-certification; no
      change to trading/research thresholds; no change to the Yahoo/raw-close recovery methodology; no
      widening of J-10's dates; no new data providers.
    - **Walkthrough:** waived — maintenance repair of the derived layer with no UI surface of its own;
      the demo requirement is replaced by the pre/post inventory, the mutation reconciliation, the
      cache-invalidation proof, and the manifest-immutability evidence.

       ### OWNER RULING — J-11 CLOSED; one authorized launcher fix, then normal work resumes
       *(owner, 2026-08-27 — binding)*

       A **later** owner decision than the acceptance ruling above. It closes J-11 and sets the
       continuation policy for this goal. It revises no earlier ruling, evidence or Stage result.

       **1. J-11 is CLOSED.** The final serving/replay verification ran against the disposable clone
       and passed. J-11 is accepted as **PASSING**. Do **not** reopen J-11 recovery or J-11 serving
       verification.
       ```
       J-11 STATUS: PASSING — CLOSED
       ```

       **2. The accidental iteration-23 canonical-DB boot is a historical HARNESS contract violation,
       not a Trendora product-data regression.** The 10 resulting rows across the five recomputable
       derived cache tables are **accepted in place**. Do not delete them. Do not perform cleanup
       writes merely to restore the pre-verification cache state. Do not manually delete or alter
       `trendora.db-wal`.

       **3. Exactly one narrow Goal Mode tooling fix is AUTHORIZED** — the demonstrated launcher
       defect in `incredible_auto_dev/scripts/automation/goal-iter-lean.sh`. Scope, exhaustively:
       - when an iteration supplies an alternate `TRENDORA_CONFIG` and/or `CHAIN_START_BACKEND_CMD`,
         every browser-QA, deterministic-replay, retry and restart backend launch MUST preserve that
         same launch context;
       - it MUST never silently fall back to the canonical database while an alternate
         verification/QA database is in force;
       - missing required launch context MUST fail closed **before** backend boot;
       - add a focused regression test reproducing the iteration-23 failure.
       No broader Goal Mode refactor, stall-detector redesign, depth-system redesign or unrelated
       automation cleanup is authorized.

       **4. The iteration-23 disposable clone** (`runs/goal-market-compass-iter-23/verify-clone/`) is
       kept only until this launcher fix is verified. It may then be deleted as disposable evidence
       infrastructure.

       **5. Normal Market Compass product work resumes immediately** once the launcher defect is fixed
       and verified. No further owner authorization is needed for ordinary non-destructive product
       iterations.

       **6. Owner continuation policy for this goal (binding).** Do **not** STALL merely for reversible
       cleanup choices, disposable-artifact cleanup, or correctly recomputable derived-cache residue —
       prefer the non-destructive / no-cleanup default, record it, and continue. Owner approval is
       still REQUIRED for: raw/canonical data repair; immutable-manifest mutation; schema migration;
       new network/provider access; destructive user-state changes; or another genuinely irreversible
       product-contract decision.

<!-- Continuous-improvement auto-journeys: the goal-proposer appends NEW Must-have journeys ONLY
     between the two markers below (see the goal-self-extension skill). The human-authored journeys
     above and the Anti-goals below are never machine-edited. An empty block = nothing auto-proposed yet. -->
<!-- AUTO:journeys -->

- **J-12: Every frozen selection disposition is true — the leadership floor is the only inclusion
  gate, and a caution qualifier moves no membership (goal-proposer, 2026-09-01)**
  - Why: measured on the committed at-ingest export
    `apps/backend/data/exports/next_session_manifests/2026-08-12_v7.json` (the frontier as-of, i.e.
    the default `/` view): **37 of the 539 `comparison_cohort` rows carry
    `leadership_score >= compass.selection.leadership_min_score` (80.0) — up to 92.71 (HPE,
    `leadership_bucket` A, `rank_in_run` 1) — yet every one of them is frozen with
    `selection_disposition: "below_selection_floor"`**, and `disposition_tally` reads
    `{below_selection_floor: 539, excluded_by_cap: 0}`. The label is false on its face: a downstream
    consumer filtering `below_selection_floor` would conclude these names had weak leadership when the
    opposite is true, and the mislabel is sealed inside the hash-covered artifact this whole cycle
    exists to freeze. Cause (`apps/backend/app/engine/compass.py`): `_qualifier_checks` returns three
    checks and `evaluate_selection` admits a member only `if all(check["passed"] ...)`, so
    `entry_min_score` and `risk_max_score` **gate** inclusion; every non-qualifying row is then stamped
    `_DISPOSITION_BELOW_FLOOR` regardless of which check failed. That contradicts this goal file's own
    Improvement direction, which defines the frozen rule as "floor → deterministic order → cap;
    **nothing else excludes**", defines `below_selection_floor` as "leadership below
    `leadership_min_score`", and states that "qualifiers annotate cautions and **never gate inclusion
    today**" — and it makes J-06's stated counter-test ("changing … a caution qualifier moves neither
    scientific hash **nor any membership**") currently FALSE. The suite cannot see it: the only
    qualifier-failing row in `apps/backend/tests/test_compass.py`'s `selection_run` fixture (CCC,
    L=77) is *also* below the 80 floor, and `test_manifest_invariants.py`'s
    `test_tc23_why_not_and_qualifier_changes_move_only_manifest_config_hash` perturbs `why_not_cap`
    only — it never perturbs a qualifier and never asserts the "nor any membership" half.
  - Steps:
    1. Before changing anything, reproduce and record the violation from the committed artifact:
       count the `comparison_cohort` rows whose `leadership_score` is at or above
       `compass.selection.leadership_min_score` and whose `selection_disposition` is
       `below_selection_floor` in `2026-08-12_v7.json` (expected 37 of 539; highest HPE at 92.71), and
       record that pre-fix baseline in the dev handoff. Do NOT mutate, relabel, re-hash, re-export or
       delete that file or any stored manifest row (AG-12/AG-17) — the incident record is evidence
    2. Conform `compass.evaluate_selection` to the rule this goal file already declares:
       `leadership_min_score` is the ONLY inclusion gate; `entry_min_score` and `risk_max_score` become
       advisory qualifiers that annotate cautions and the eligibility checklist and never remove a
       member. Deterministic ordering (leadership desc, ticker asc) and `max_candidates` are unchanged.
       Bump `compass.selection.rule_version` (already inside `candidate_rule_hash`'s scope) so manifests
       minted under the corrected rule are distinguishable from those minted under the old one. Change
       no threshold VALUE — nothing here is chosen from realized forward returns (AG-15)
    3. Make the disposition truthful by construction and assert it per row, not merely in aggregate:
       every non-candidate that cleared the floor is `excluded_by_cap`, every other is
       `below_selection_floor`, and a test asserts each label's own predicate holds
       (`below_selection_floor` ⇒ `leadership_score < leadership_min_score`). The closed vocabulary stays
       two members and the committed schema's `selection_disposition` enum is unchanged — no new
       versioned schema file and no `schema_version` bump
    4. Fix the sentences the correction makes false: `candidates_empty_reason` names only the gating
       rule (never entry/risk as though they gated); a candidate that misses an advisory qualifier
       renders a **caution** citing that threshold and the stored actual value, never a reason claiming
       it "clears" that qualifier; each eligibility-checklist row's verdict comes from the existing
       fixed set (Pass / Miss / Supportive / Neutral / Unknown / NA) and marks the check as gating or
       advisory, so the gating verdicts ALONE reproduce inclusion/exclusion for every spot-checked name
       (J-04 steps 4-5 stay satisfied)
    5. Complete the counter-test J-06 already specifies but the suite never implemented: perturb
       `entry_min_score` and `risk_max_score` and assert that neither `candidate_rule_hash` nor
       `cohort_rule_hash` moves AND that the candidate list, the comparison-cohort membership, every
       `selection_disposition`, and the near-threshold shadow cohort are all identical. Add the fixture
       row the suite lacks — a member ABOVE the leadership floor that fails a qualifier (the real HPE
       shape: L≈92.7 / E≈21.5 / R≈58.9)
    6. Prove nothing frozen moved: the stored `next_session_manifests` rows and their export files are
       byte-identical before and after (AG-12), the code change alone mints no new version, and the
       pre-fix mislabeled versions remain readable exactly as they are with their eligibility unchanged
       (AG-17) — the correction appears only in manifests minted after the `rule_version` bump
    7. Re-verify end to end at the frontier as-of: the Next-session focus section, the summary's
       focus-count sentence and `GET /api/compass` agree on the candidate count; the manifest strip's
       expanded table shows the corrected dispositions; the disposition tallies still partition member
       count minus candidate count exactly (on today's data expect 502 `below_selection_floor` + 27
       `excluded_by_cap` + 10 candidates = 539 members — record the measured partition if the data has
       moved); and the shadow cohort's membership (leadership in `[shadow.min_score,
       leadership_min_score)`, 25 rows today) is unchanged, since nothing in this journey touches
       `cohort_rule_hash`'s semantics
    8. Cite in the dev handoff the disclosure that `provenance.config_keys` includes
       `compass.selection` and `provenance.engine_files` hashes `compass.py`, so the `rule_version` bump
       and the code edit legitimately move `generation.engine_identity` on NEWLY created manifests and
       runs — an expected, disclosed identity change, never a backfill or re-stamp of existing rows
  - Acceptance:
    - **Consistency (single source):** the candidate set, dispositions, cohorts, reasons, cautions and
      checklist remain slices of the ONE `compass.evaluate_selection` trace computed inside
      `build_manifest_payload` and served only by `GET /api/compass` — no new producer, no new route,
      no new Data Contract value, and no client-side rule; `state/blueprint.md` records a dated note on
      the existing Next-session manifest CONTENT / FREEZE-INTEGRITY rows stating the `rule_version`
      bump and the truthful-disposition invariant.
    - **Correctness:** after the fix, ZERO `comparison_cohort` rows labelled `below_selection_floor`
      have `leadership_score >= leadership_min_score` (was 37 of 539); the tallies still partition
      member count minus candidate count exactly; the qualifier counter-test passes on both scientific
      hashes AND on membership; `content_hash` still reproduces across two builds of the same inputs
      and is still invariant to perturbation of post-as-of bars.
    - **Honest status & anti-goals:** no threshold VALUE is tuned and nothing is chosen from realized
      returns (AG-15); no new composite or blended candidate number appears (AG-11); frozen rows and
      export bytes are untouched and no manifest is regenerated, rebound or re-hashed by this journey
      (AG-12), with pre-fix manifests keeping their `prospective_eligible` value exactly (AG-17);
      candidate framing stays "worth monitoring next session" with cautions — no imperative verbs, no
      forecast wording, no proven-language, and the evidence chips keep reading their true ledger
      status (AG-1/AG-2). If conforming to the documented rule would violate any anti-goal or regress a
      passing journey, STOP and surface it for owner review rather than widening the rule.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the corrected disposition table (an above-floor
      name no longer labelled "below the selection floor"), a candidate carrying an advisory-qualifier
      caution, and the focus section under the corrected rule, viewable via
      `demo.sh market-compass --session-live`.

- **J-13: "Leadership rotation" says which way, shows both directions, and stops repeating
  What-changed (goal-proposer, 2026-09-01)**
  - Why: the Vision promises `/` answers "where leadership is rotating" and the Success Criteria
    require that from `/` alone a reader can identify "the top sector/theme movers **in both
    directions**", but no Must-have journey asserts that section's CONTENT (J-07 step 1 asserts only
    that it renders in page order), and three measured defects sit behind it.
    **(a) It is a duplicate.** `apps/frontend/components/compass-leadership-rotation-section.tsx`
    renders `compass.session_delta.changes.filter(kind ∈ {sector, theme, stock})` — a client-side
    subset of the SAME array `compass-whatchanged-card.tsx` renders in full. On the frontier manifest
    (`2026-08-12_v7.json`, the default `/` view) `changes` holds 17 entries — 5 sector, 2 theme, 10
    stock, 0 market, 0 breadth — so the rotation section repeats **all 17 rows** the card directly
    above it already showed.
    **(b) It has no direction.** A change entry is `{from, to, magnitude}` with an UNSIGNED magnitude
    and no direction field, so "Home Construction (iShares) 21 → 25" (worse) and "Regional Banks (SPDR)
    13 → 10" (better) look identical; the reader must know that a lower rank number is better and that
    leadership bucket E → D is an improvement. The iter-28 `state_band` block already established the
    correct served shape — a signed `delta` plus a `direction_word` from
    `compass.vocabulary.direction_words` — and the change entries never got it.
    **(c) Both directions are not guaranteed, and an above-threshold mover can vanish uncounted.**
    `session_delta._sector_changes` / `_theme_changes` sort by `abs(rank move)` and return
    `changes[: compass.delta.top_k]` (5) while returning the FULL `suppressed` list, so one direction
    can be cut away entirely and an above-threshold mover ranked beyond `top_k` is dropped from
    `changes` AND never counted in `suppressed`. Measured on the frontier: theme accounts for 2 + 9 =
    11 of its 11 configured themes, but sector accounts for only 5 + 24 = **29 of the 31** configured
    sector/industry ETFs (`config.etfs.sector` 11 + `industry` 20) — two sector rows unaccounted for,
    while the card's "Suppressed moves (36)" disclosure claims to say what was held back.
  - Steps:
    1. On `/` at the latest as-of, assert the Leadership rotation section renders a **served**
       `session_delta.rotation` block rather than a client-side filter of `session_delta.changes`, and
       that it contains no stock-kind row — stock leadership-bucket crossings stay in the What-changed
       card above (this journey adds no stock-level weakness view; Non-Goals: group-level only)
    2. Assert the block carries, for each group kind (sector and theme), two explicitly labelled sides
       — gaining leadership and losing leadership — each ordered most-moved first, each capped by a new
       config-only key `compass.delta.rotation_top_k`, each entry still gated by the existing
       `compass.delta.rank_move_min` threshold, and each side rendering its own honest empty state
       ("no sector lost ground beyond the threshold this session") rather than a blank
    3. Assert every rotation row carries a **signed** delta and a served `direction_word` taken from
       the existing `compass.vocabulary.direction_words` map, with the polarity resolved engine-side (a
       rank number that FALLS is "improving"); assert the same signed delta + direction word ride on
       the `session_delta.changes` entries so the What-changed card can show them too, and assert the
       frontend selects no word, computes no sign, and applies no threshold
    4. Assert the group accounting is complete and disclosed: for each group kind, the entries shown on
       the two sides plus the disclosed suppressed (below-threshold) count plus any disclosed
       "further movers not shown" residual equals the full configured group count (31 sector/industry,
       11 theme) — an above-threshold mover beyond `rotation_top_k` is never silently dropped
    5. Spot-check one gaining and one losing sector row against the stored ranks served by
       `GET /api/sectors` at the prior and current as-of dates, and one theme row against
       `GET /api/themes`: the from/to values and the signed delta equal the stored rows
    6. Assert the What-changed card is unchanged by this journey — same entries, same
       market → breadth → sectors → themes → stocks order, same thresholds, same suppressed count as
       before the change, so every J-02 assertion still holds
    7. Step the as-of switcher to the earliest stored run; assert the rotation block renders its
       no-prior-run state consistent with What-changed's — no deltas, no direction words, nothing
       fabricated
    8. Cite in the dev handoff the fixture test where one side is empty (every threshold-crossing mover
       is a gainer): the losing side renders its explicit empty state and the gaining side is
       unaffected; and the fixture where an above-threshold mover falls beyond `rotation_top_k` and is
       disclosed in the residual count rather than dropped
  - Acceptance:
    - **Consistency (single source):** `session_delta.rotation` and the signed `delta`/`direction_word`
      fields are computed ONCE by the existing `app.engine.session_delta.compute_delta` inside
      `app.engine.compass.build_manifest_payload` and served only by the existing `GET /api/compass` —
      no new producer and no new route; they are registered as added fields of the "Next-session
      manifest — CONTENT block" Data Contract row in `state/blueprint.md` with a dated note, exactly as
      iter-28 registered `state_band`; the direction word reuses `compass.vocabulary.direction_words`
      (never a second word map) and `rotation_top_k` is config-only (`session_delta.py` and
      `compass.py` are already `test_no_magic_numbers.CALC_FILES` entries, so no literal may appear).
    - **Correctness:** from/to values and signed deltas equal the stored sector/theme rank rows for both
      as-of dates; every displayed row meets `rank_move_min`; both sides are populated whenever both
      sides have a threshold-crossing mover; the per-kind accounting closes against the configured group
      counts; and every produced manifest still validates against the committed schema at
      `docs/handoffs/trendora-next-session-manifest-v1.schema.json` with NO `schema_version` bump and no
      new versioned schema file (`session_delta` is an open object there, so this extension is additive).
    - **Honest status & anti-goals:** no new composite or blended rotation score is introduced (AG-11) —
      a rotation row carries only the stored ranks and their signed difference; no existing
      `compass.delta` threshold VALUE is retuned (`rotation_top_k` is a new display cap, never a
      revision of `rank_move_min`); empty sides, the residual count and the no-prior-run state are
      explicit and dated, never blank and never fabricated; no imperative, forecast or proven-language
      (AG-1/AG-2); and `candidate_rule_hash`, `cohort_rule_hash`, candidate membership and both cohorts
      are provably unmoved by this journey while frozen manifests and export bytes stay untouched
      (AG-12).
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the both-directions rotation section — a gaining
      side, a losing side, one empty side with its honest state, and the direction words — viewable via
      `demo.sh market-compass --session-live`.

<!-- /AUTO:journeys -->

## Anti-goals

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
  - **Dated exception (owner, 2026-08-20 — single-use, self-closing, incident response):** the bounded
    recovery fetch defined by **J-10** is authorized for exactly two calendar dates, **2026-08-11 and
    2026-08-12**, and only for the symbol/row scope proven missing as a consequence of the iter-5 drill.
    It authorizes **nothing else**: no other date (in particular nothing on or after 2026-08-13), no
    refresh of unaffected historical data, no replacement of valid existing rows, no broad backfill, no
    advancement of the dataset to a newer market-data frontier, no change to candidate thresholds or
    research logic, and no unrelated data repair. The intent is **state restoration only, not dataset
    advancement**. If the implementation cannot prove a request stays inside this scope, it MUST stop
    rather than broaden the fetch. The exception is **exhausted** the moment J-10's post-recovery
    verification passes — normal AG-9 then applies again automatically, and any later live fetch,
    **including of these same two dates**, requires a new dated goal.md amendment. The only retry
    permitted under this exception is a re-run of the same bounded, idempotent recovery after a failed
    or partial attempt, still confined to the proven missing set. This is not a standing
    "recovery fetch allowed" path.
  - **Vendor addendum (owner, 2026-08-20, after iteration 6's Stooq block):** the exception's vendor
    is widened from `stooq` to **`stooq` or `yahoo`**, and to no other provider. It additionally
    covers the **read-only comparison fetch** defined in J-10 step 2a — a small overlap window of
    already-surviving days, held outside the database, used solely to prove the adjustment
    convention matches, never written and never used to repair anything. Every other bound is
    unchanged (the same two dates, the same proven-missing rows, fail-closed, idempotent,
    self-closing on verification). A third vendor requires a new dated amendment.
  - **Dated exception #2 — AVB convention diagnostic (owner, 2026-08-25 — single-use, self-closing,
    DIAGNOSTIC ONLY).** J-11 Stage D readiness is blocked at **AVB-D** because the persisted J-10
    evidence kept close-comparison data but **discarded the corresponding provider volume**, so the
    price/volume convention for AVB's two recovered bars cannot be settled from anything already on
    disk. This authorizes **exactly one** bounded, read-only comparison fetch to settle it, and
    **nothing else**:
    - **Symbol:** `AVB` only. **Dates:** exactly `2026-08-05, 2026-08-06, 2026-08-07, 2026-08-10,
      2026-08-11, 2026-08-12` — six dates, no others, none inferred from a range or cadence.
    - **Fields:** `date`, `close`, `volume` only. Use the **canonical Yahoo provider path Trendora
      already uses**, so the comparison is like-for-like; vendor is `yahoo` (the vendor addendum above
      also permits `stooq`, but **no retry into another provider** is authorized here beyond that).
    - **Purpose:** compare provider close and volume against the already-stored Trendora close and
      volume and the persisted J-10 bridge factor, to determine whether the stored representation is
      raw+raw, bridged price + raw volume, bridged price + compensating volume, or indeterminate.
    - **This is NOT ingest and NOT recovery.** No write to `daily_prices` or **any** database table; no
      persistence, no backfill, no repair, no normalization, no "improvement" of AVB data, no dataset
      advancement, no population-wide fetch. **J-10 is NOT reopened** — its own exception stays
      exhausted and this amendment grants it nothing. The observations live **only** in a new
      iteration-15 evidence artifact outside the database.
    - **Auditable provenance required** in that artifact: provider, symbol, requested dates/window,
      raw returned close, raw returned volume, capture timestamp, the bridge factor used, and the
      comparison formulas applied.
    - **Fail closed.** If the provider cannot supply sufficient evidence, classify honestly as
      **AVB-D** and stop — do not guess, do not substitute adjacent-day statistics for the direct
      comparison, and do not broaden the fetch to make an answer available.
    - **Exhausted** the moment that comparison artifact is written. Normal AG-9 applies again
      automatically; any later live fetch, **including of these same six dates**, requires a new dated
      amendment. This is not a standing "diagnostic fetch allowed" path.
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
- **AG-17 — Repair never rewrites provenance (owner, 2026-08-20):** restoring deleted historical data MUST
  NOT retroactively change research provenance. A manifest that was retrospective or ineligible stays that
  way; **`prospective_eligible` is never upgraded merely because historical data was later repaired**;
  `available_at_utc`, manifest versions, `content_hash`/`manifest_hash`, and prior eligibility
  classifications remain immutable (AG-12 governs the rows and files themselves). Any manifest or artifact
  produced while the database was known to be damaged — everything dated from the iter-5 drill until
  **J-11 Stage G** passes (owner, 2026-08-21: extended from "J-10's post-recovery verification", because
  after J-10 the raw layer is repaired but the derived state is still knowingly pending J-11 normalization)
  — **remains marked unusable as prospective/out-of-sample evidence**; nothing is retroactively marked
  prospective merely because raw bars were repaired in J-10 or derived snapshots were regenerated in J-11 —
  historical causality is unchanged by either;
  only a separately regenerated artifact, minted after verified recovery under the existing create-once and
  version rules, may carry eligibility, and it remains subject to the same version and
  `prospective_eligible` contract as any other artifact. The incident record itself is evidence: the iter-5
  drill result, its handoff, the reviewer/QA evidence already produced, and the explicit statement that the
  committed seed could not restore these dates MUST NOT be deleted, rewritten, or silently superseded.
  Repairing the database never rewrites historical causality. *(critical)*
- **AG-18 — The authorized manifest migration preserves everything (owner, 2026-08-23):** the bounded
  `next_session_manifests` schema migration authorized in J-11 step 11 (ruling A1) removes the
  `source_run_id` foreign-key constraint and **nothing else**. No manifest may be **regenerated,
  rebound, rehashed, upgraded, deleted, or newly minted** by it or around it. All 24 rows and every
  stored column value — `as_of`, `source_run_id` (orphans included), `generation_json`, `content_hash`,
  `manifest_hash`, `version`, `available_at_utc`, `prospective_eligible` — survive exactly, proven by
  persisted pre/post per-row evidence. No other table's schema may be altered under that authorization.
  A changed stored value is a REGRESSION, never a note.
  **Bounded exception on record (owner, 2026-08-24) — narrowing nothing.** The iter-11 migration **did
  exceed** this rule: it removed three server-side defaults (`version`, `frozen`, `prospective_eligible`)
  and moved `version` from column ordinal 9 to 3. That event was **detected** (by the auditor, after the
  developer, reviewer and QA all missed it), **enumerated** exactly, **reviewed**, and **accepted by the
  owner after the fact** as an already-materialized end state — explicitly in preference to a second
  live rewrite, on risk grounds. It is **not generalized**. AG-18 continues to prohibit schema drift
  beyond an explicitly authorized migration; future migrations remain subject to strict schema-delta
  proof, must derive the replacement table body from the captured live DDL rather than from ORM metadata
  (ruling A10), and must fail closed when the targeted clause cannot be identified exactly. **The
  accepted residual set is not a precedent and may not be cited as one.** *(critical)*

## Loop mechanics (for the iteration planner)

- No journey in this cycle carries an Evidence Claim — the post-decompose referee gate passes automatically
  every iteration; AG-1/AG-4/AG-6 still veto any proven-language regression.
- Suggested build order: J-01 (sector wiring — unblocks candidate sector context), then the engine cluster
  (J-02 delta + J-03 narrative + J-04 selection — one manifest producer), then the freeze/integrity pair
  (J-05, J-06), then the surface pair (J-07 Today, J-08 relocation). The decomposer may re-order with reasons.
- **2026-08-20 owner insert: J-09 (host resource-fit) jumps the queue — build it as the NEXT slice** before
  continuing J-05/J-06: it is small (one config value + measurements), and it is what lets full-depth
  iterations (two backends) fit this host without freezing it. The Constraints "Host resource-fit" rules
  (memory-pressure test gating, `next build` worker bound, prefill re-bound) ride the nearest applicable
  slices after it. *(J-09's config half landed in iter-4 as an honest miss — VmPeak 3,439,100 kB against a
  ≤ 2.5 GB target, −28.9% from baseline, no owner-only cap touched; (a) and (b) landed in iter-5.)*
- **2026-08-20 owner insert #2 (incident response): J-10 (bounded recovery) jumps the queue ahead of
  everything, including the J-05/J-06 make-up.** The iter-5 drill left the canonical database damaged.
  **No developer, reviewer, QA, browser-QA, evaluator, coherence, research or proposer lane may run
  against the knowingly damaged database before J-11 Stage G passes** — the only work that proceeds is
  the recovery itself and its verification.
  **Extended 2026-08-21 (was "before J-10's post-recovery verification passes" — insufficient).** A
  successful J-10 raw repair must NOT reopen the normal pipeline: after J-10 the database still
  intentionally contains derived state known to need J-11 normalization, including the recovery-era
  2026-08-11/12 `ScannerRun`s that J-10's create-once backfill cannot refresh (J-10 step 5b). The gate
  therefore runs:
  > J-10 raw-input recovery complete → **J-11 incident-bounded clean regeneration** → **J-11 Stage G
  > passes** → normal Market Compass work resumes.
  Between those two points the honest description of the database is: **raw-input recovered,
  derived-state repair pending; not yet clean for normal research or evaluation lanes.** Only work
  needed to execute and verify J-10/J-11 — plus explicit prerequisites such as the depth/safety
  control — may run in that window. Artifacts already produced from the
  damaged state (iter-5's dev handoff, its `status.json`, and any reviewer/QA output) are preserved as
  incident evidence and are never treated as clean research evidence (AG-17). If the recovery cannot be
  completed inside AG-9's authorized scope, stop and surface it for owner review rather than resuming
  normal evaluation on damaged data.
- Depth: lean by default; full when an iteration first lands user-visible UI changes.
- **`Depth: full` must never silently become `lean` (owner, 2026-08-21).** This session has had an
  explicit `Depth: full` spec dispatched as `lean` three times (iters 2, 6, 8) — including iteration
  8, the one that performed the first real writes to the production database, and including
  iteration 6, where the demotion also let an ungated browser-QA replay run against the damaged
  dataset. That is not acceptable for a recovery path whose correctness depends on adversarial
  review and audit. **When the goal or an iteration spec requires `Depth: full`, inability to run the
  required full-depth lanes MUST be surfaced explicitly and MUST NOT silently fall back to `lean`.**
  For any J-10 iteration that can write recovery data, the intended full audit/review depth is
  required before the iteration may be treated as fully accepted. If the infrastructure cannot
  provide `full`: mark the depth requirement **unmet**, preserve the implementation and recovery
  evidence, do **not** pretend `lean == full`, and surface it for owner/evaluator decision. Never
  fabricate an audit result to satisfy this. Do **not** re-run destructive or network actions merely
  to obtain another depth marker, unless the existing idempotent recovery design makes that provably
  safe and this goal explicitly allows it.
- Backlog cards partially pulled forward (mark `IN-GOAL.MD (scoped, market-compass)` in
  `docs/improvement-backlog.md`): B-306 (engine-identity stamping — scoped to manifests + new runs),
  B-802 (rule distances — realized as the selection trace), B-804 (score diff — scoped to bucket/status/rank
  crossings), B-1205 (stamped exports — scoped to the manifest artifact). Their full forms stay in the backlog.
- `docs/improvement-backlog.md` remains the owner-governed idea registry; the goal-proposer writes only
  between the AUTO markers above.

## Improvement direction (engineering) — freeze the prior, expose the change, keep one producer

### Ground truth (measured 2026-08-19 on main @42167cf5)
- Committed seed: `daily_prices` 3,311,510 rows / 591 symbols / 1996-01-02 → 2026-08-14;
  `scanner_runs` 3,080 dates with consecutive DAILIES 2026-08-05 → 2026-08-14 (delta engine has real
  prior-session pairs offline); every run stores 31 sector/industry + 11 theme rank rows.
- Latest run (2026-08-14, id 3051): 541 members; setups Avoid 482 / Breakout-watch 51 / Extended 8 /
  **Actionable 0**; leadership buckets A 0 / B 27 / C 76 / D 82 / E 356 — the selection floor
  (leadership ≥ 80) yields a full candidate list today, while Actionable/A-bucket rules would yield none.
- Sector: `config.stock_sectors` maps 122 names; 424/541 rows (78.4%) NULL at the latest run;
  `apps/backend/data/seed/universe_pool.csv` carries a sector for all 548 pool names (its 11 sector names
  verified identical to `config.etfs.sector` names today ⇒ `universe.pool_sector_aliases` defaults empty).
- Provenance today: `scanner_runs` has created_at/provider/benchmark only — no engine/rule/code stamps;
  `research._dataset_version` = counter stamps that a rebuild can reproduce byte-identically.
- Evidence: canonical ledger 7 entries, all FAIL ⇒ every score reads "Not yet proven" (correct display).

### Integration map (where the new work plugs in)
- Finalize hook: insert the "next-session manifest" phase in `_refresh_ingest_aggregates`
  (`apps/backend/app/engine/data_manager.py`, between the market-phase warm ~:4509 and forward
  aggregates ~:4528) — after the phase warm (the delta reads the causal timeline cache), before the long
  aggregate phase (liveness); own try/except + `enter_finalize_phase` + honesty-gated
  `refreshed.append("next_session_manifest")`. Freeze fires only when the frontier date is in
  `prog.new_snapshot_dates` and no manifest exists for it.
- Create-once writer mirrors `scanner.persist_run_payload`'s two IntegrityError guards
  (`apps/backend/app/engine/scanner.py:118-130, :204-218`); read path reuses
  `snapshot_serving`'s as-of error mapping. **Create-once-on-GET applies only to as-of dates strictly
  before the data frontier**; the frontier's manifest is minted only by the freeze or an explicit
  confirm-gated regenerate.
- `next_session_manifests` joins NEITHER `clear_snapshot_set` (`data_manager.py:2223-2227`) nor the
  remove-data cascade (`:2170-2177`); `source_run_created_at` + `engine_identity` are the rebuild
  detectors, never the dataset stamp alone.
  **CORRECTION (owner, 2026-08-21 — this line previously read "no foreign key to `scanner_runs`
  (rebuild recreates ids)", which is FALSE and load-bearing).** `apps/backend/app/models.py:820`
  declares `source_run_id: int = Field(foreign_key="scanner_runs.id", index=True)`, and the live
  SQLite DDL carries `FOREIGN KEY(source_run_id) REFERENCES scanner_runs (id)`. The behaviour the
  design relies on — manifests outliving their source run — currently works only because
  **enforcement is off**: `db._apply_sqlite_pragmas` sets `journal_mode`, `synchronous`,
  `busy_timeout`, `cache_size`, `mmap_size` and `temp_store` but never `PRAGMA foreign_keys=ON`, and
  SQLite defaults it OFF. Measured on the live database 2026-08-21: `PRAGMA foreign_keys` reads `0`,
  and `PRAGMA foreign_key_check(next_session_manifests)` reports **12 existing violations** — every
  manifest on the four incident dates that carry one (2026-08-05 ×2, 2026-08-10 ×1, 2026-08-11 ×3,
  2026-08-12 ×6), while all 12 non-incident manifests dereference cleanly. Half the manifest table is
  already in a state a foreign-key-enforcing backend would reject. See **J-11 Stage B1**, which makes
  reconciling this a hard precondition of any incident-run deletion.
- `ScannerRun.engine_identity` = additive nullable column via `db._ADDITIVE_COLUMNS`
  (`apps/backend/app/db.py:108-145`), stamped only in `persist_run_payload`; old rows stay NULL
  ("pre-stamping era"), never backfilled.
- Mode rule is data-driven: `at_ingest` iff no bar dated later than the as-of exists at generation
  (`generation.frontier_bar_date` records the evidence); fails toward `retrospective`.
- Serialize once: build payload → `json.dumps(sort_keys=True, default=str)` → store those bytes → export
  those bytes; `content_hash` covers the content block only (excludes generated_at, mode, the generation
  block, the dataset block, `available_at_utc`, `prospective_eligible`, and `manifest_hash`) and remains
  the research-content reproducibility identity. `manifest_hash` = sha256 over the canonical serialization
  of the COMPLETE document with only the `manifest_hash` field excluded (a fixed placeholder during
  computation), assembled before the INSERT so the stored and exported bytes carry it — the whole-artifact
  integrity identity, distinct from `content_hash`; an integrity hash is not a signature: adversarial
  forgery is out of scope (no signing/PKI in this goal).
- Cohort blocks (all inside the one manifest document): `candidates` (unchanged);
  `comparison_cohort` — EVERY scored member of the source run not selected as a candidate,
  compact field-array rows carrying the SAME frozen matching-context fields as the shadow
  rows (listed below) plus a `selection_disposition`; its definition text carries verbatim
  "a frozen non-selected comparison pool, not a matched or causal control group"; the
  shadow is a subset of it by construction (shadow members are non-selected) and is never
  deduplicated out of it. `selection_disposition` — a closed vocabulary computed from the
  same single `evaluate_selection` trace, exactly partitioning the non-selected set under
  the frozen rule (floor → deterministic order → cap; nothing else excludes):
  `below_selection_floor` (leadership below `leadership_min_score`) or `excluded_by_cap`
  (met the floor, ordered out by `max_candidates`); tallies must sum to member count minus
  candidate count; qualifiers annotate cautions and never gate inclusion today — if a
  future rule makes a qualifier gating, the vocabulary and the candidate-rule scope must
  extend together (rule_version bump), never by relabeling frozen rows.
  `near_threshold_shadow` — research-only substrate: scored members with leadership in
  `[shadow.min_score, leadership_min_score)` (half-open — a name at exactly the selection
  floor is candidate-eligible, never shadow), deterministic order (leadership desc,
  ticker), uncapped, taking no part in selection, display ranking, or the Today focus
  section; its definition and the `caveats.cohort_semantics` note state that it is near
  the LEADERSHIP selection floor specifically, not necessarily near the final
  candidate-selection boundary (deterministic ordering, the candidate cap, and any future
  gating qualifier also affect final inclusion) — never described as "near-selected".
  Each cohort row freezes contemporaneous context from the stored run row ONLY (ticker,
  leadership/entry/risk score+bucket, setup_status, rank_in_run, sector, theme
  memberships with that run's theme ranks, close, atr_pct value+percentile,
  high-proximity/distance-from-52w-high, gap p95, worst-20d, distance-to-invalidation,
  ADV dollar figure — no new data sources); purpose note: the cohorts preserve a
  prospectively frozen substrate for later better-matched or threshold-focused
  incremental-value studies without retrospective reconstruction.
- `prospective_eligible` — derived ONCE at write, stored at the payload top level OUTSIDE
  the content-hash scope (generation-class metadata, like `mode`) plus a typed column for
  filtering; true iff ALL of: mode `at_ingest` with consistent frontier evidence
  (`generation.frontier_bar_date == based_on_close`), `generation.producer ==
  "ingest_finalize"`, `version == 1`, `frozen: true`, a well-formed `available_at_utc`
  present, and provenance complete (engine identity, `candidate_rule_hash` +
  `cohort_rule_hash` + `manifest_config_hash` with their verbatim config subsets, dataset
  stamp, universe pool hash, `manifest_hash` all present). Never recomputed at read; a
  retrospective or regenerated manifest is always false; consumers treat an absent field
  as false. `generation.preflight_verdict` is recorded for later filtering but does NOT
  gate eligibility. The `generation` block gains `producer: ingest_finalize /
  on_demand_get / regenerate`; the caveats block gains `cohort_semantics` carrying the
  non-causal sentence and the shadow near-floor clarification.
- `available_at_utc` — the authoritative downstream availability fence: the earliest
  conservative timestamp at which the immutable artifact may be treated as available to a
  downstream consumer. Recorded ONCE at write as the canonical-serialization instant PLUS
  `compass.manifest.availability_margin_seconds` (default 60) so it never predates the
  durable INSERT and export that follow within the same finalize phase — conservative by
  construction (a too-late fence only shrinks the eligible window; a too-early fence would
  fabricate prospectivity). Generation-class: outside `content_hash`, inside
  `manifest_hash`; never back-dated or recomputed at read. It does NOT claim session-level
  prospectivity: a stale local frontier can honestly yield `prospective_eligible: true`
  with a fence days after `based_on_close` — the fence VALUE is what exposes it. Consumer
  rule for future studies: an observation is prospective with respect to this manifest
  only if its event timestamp is strictly later than `available_at_utc`; a claim that the
  artifact was a full next-session prior must additionally establish that the fence
  precedes the first included event/session boundary — session boundaries are the
  preregistered study's responsibility (no exchange-calendar subsystem in Trendora).
- Delta inputs: current vs previous stored run (indexed scalar select), the causal market-phase timeline
  from `market_phase_cached` (prev point of the SAME payload), stored sector/theme rank rows, and
  column-projected `ScannerResult` selects (ticker/scores/buckets/setup only — AG-8).
- Narrative voice: the `market_phase._recovery_turn_signal` reason branches
  (`apps/backend/app/engine/market_phase.py:618-638`) and `setups._REASONS` string-table shape are the
  precedents; every sentence ships `{template_id, text, facts}`.
- Frontend: `/` recomposed; `/market` receives the current dashboard body verbatim
  (`apps/frontend/app/page.tsx` sections; keep localStorage keys `trendora.dashboard.phaseCrossView`,
  `trendora.dashboard.moreDetail` so preferences survive); sidebar NAV order in
  `apps/frontend/components/sidebar.tsx`; the as-of provider stays the sole `?asof` owner.
- Config namespaces: `compass.selection` (rule_version, leadership_min_score 80.0, max_candidates,
  qualifiers entry_min_score 70.0 / risk_max_score 60.0, why_not floor 75.0 + cap,
  shadow.min_score 75.0 — the near-threshold band's own key, default equal to the why-not
  display floor but independent of it so display tuning never moves the research band),
  `compass.delta` (breadth_min_change_pts, rank_move_min, top_k, velocity_flat_band, pbear_bands,
  max_stock_items), `compass.vocabulary` (direction/level/score word maps),
  `compass.manifest` (schema_version, export dir + modes: at_ingest only,
  availability_margin_seconds 60 — a publication-latency allowance, never a research
  threshold — and the committed schema path), `provenance` (engine_files list, config_keys
  list), `universe.pool_sector_aliases` (default empty). Identity scopes over
  `compass.selection`: `candidate_rule_hash` covers ONLY membership/ordering-affecting
  keys (rule_version, leadership_min_score, max_candidates, the declared ordering rule
  "leadership desc, ticker asc"); `cohort_rule_hash` covers cohort semantics
  (shadow.min_score, the shadow band's upper-bound VALUE — i.e. leadership_min_score, so a
  floor change moves BOTH scientific hashes — the disposition vocabulary version, and the
  cohort row field list); qualifiers (caution annotations) and why-not display keys live
  ONLY in the broad `manifest_config_hash` over the whole `compass.selection` subtree — a
  display or caution tweak never moves a scientific identity; each hash's config subset is
  stored verbatim beside it.
  Env override for tests: `TRENDORA_COMPASS_EXPORT_DIR` (name only, never a value in files).
- New engine modules join `CALC_FILES` in `apps/backend/tests/test_no_magic_numbers.py:19`.
- Methodology: add the sector-basis disclosure and a "Next-session focus" entry whose thresholds ref the
  live `compass.selection.*` keys; TermInfo entries for every new word.
- Handoff contract: a committed JSON Schema at
  `docs/handoffs/trendora-next-session-manifest-v1.schema.json` (versioned in lockstep
  with `schema_version`) defines required types/structures for mode, producer, the
  generation block, `available_at_utc`, `prospective_eligible`, `content_hash`,
  `manifest_hash`, engine/dataset/universe provenance, `candidate_rule_hash`,
  `cohort_rule_hash`, the three cohorts (including disposition and the matching-context
  field list), and the caveats block; fixture/contract tests prove every produced manifest
  validates against it; a schema change is a NEW versioned file, never an in-place edit;
  this is Trendora's producer-side contract only — no Tapeology importer in this goal.

### Traps (binding)
- The producer must never read `forward_returns`, the fenced retrospective smoothing, or any bar later
  than the as-of — the time-safety test perturbs post-as-of bars and asserts an unchanged content hash.
- Never auto-version manifests on rebuild (mass churn); skip-if-exists at finalize + explicit regenerate only.
- The words are computed at freeze INTO the payload — historical reads stay stable across config changes;
  a retrospective recomputation must say so on the surface.
- Reason/caution codes get their own namespace; never reuse "…-watch" setup strings or the word
  "watchlist" for the focus list.
- The compass narrative may cite data-quality FACTS (coverage %, staleness) but never readiness/preflight
  verdict tokens; the preflight verdict is recorded only in the manifest `generation` block (at-ingest only).
- `prospective_eligible` is write-once and version-shopping-proof by construction: only version 1 minted by
  the finalize producer can be true — a regenerate can never mint an eligible prior, even on the frontier
  with no new bars, and no read path recomputes the flag.
- `available_at_utc` is never back-dated, never recomputed at read, and never derived from anything but the
  write-time rule; its margin is a publication-latency allowance, never a research threshold — tuning it
  from outcomes is forbidden like any threshold. Consumers verify `manifest_hash` BEFORE reading any field
  and fail closed on a mismatch.
- The disposition vocabulary is part of `cohort_rule_hash`'s scope: extending it (e.g. a future gating
  qualifier) is a rule change carried by new manifests under a bumped rule_version — never a relabeling of
  frozen rows.

### Future research enabled by this goal (explicitly NOT in scope)

The frozen candidate, comparison, and near-threshold shadow cohorts exist so that a FUTURE,
separately pre-registered study can ask: does the same Tapeology setup show better net
expectancy / MFE / MAE / failure characteristics when it occurs in a prospectively selected
Trendora candidate versus a comparable non-selected or near-threshold name? That experiment
is not part of this goal: it follows Tapeology's registration methodology (registration
boundary, frozen denominators) plus Trendora's registry + referee, and it must consume only
manifests with `prospective_eligible: true` (fail-closed — anything else, including an
absent field, is ineligible), verify each artifact's `manifest_hash` before use, and count
an observation as prospective only when its event timestamp is strictly later than that
manifest's `available_at_utc` — artifact-level eligibility is necessary but not sufficient
per observation, and establishing that the fence precedes the first included session
boundary is the study's own preregistered rule (Trendora ships no exchange calendar).
Until such a study passes, candidate-vs-cohort differences are descriptive only (AG-16).
