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
         existing per-row/per-run vendor fields — never relabelled, back-dated, or blended into the
         surrounding `stooq` history. The dataset after recovery is honestly mixed-vendor at exactly
         two dates, and the handoff and `data_provider_runs` must both say so.
       - **Fail closed: precommitted path-agreement + stable multiplicative bridge (owner, 2026-08-20
         — supersedes the earlier absolute-level tolerance).** Stooq's bars are split/dividend-adjusted
         (seed manifest: "REAL split/dividend-adjusted EOD OHLCV"). Before inserting anything, the
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
    2d. **Continue from 20/587 — do not restart.** The 20 already-restored symbols stay restored if
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
       (e) the project's data/DB-integrity checks pass; (f) the original destructive condition is
       gone — `GET /api/compass?as_of=2026-08-12` serves again and J-01/J-02/J-03 replay clean.
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
    - **Correctness:** the two dates are restored, no third date is touched, no surviving row is
      overwritten, the frontier is unchanged at 2026-08-12, and J-01/J-02/J-03 pass a live replay
      again. If the restoration is cross-vendor (step 2a), the path-agreement test passed on
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
    - **Walkthrough:** waived — data-layer repair with no UI surface change of its own; the demo
      requirement is replaced by the provenance record, the verification evidence, and the
      J-01/J-02/J-03 live replay that proves the damage is gone.

<!-- Continuous-improvement auto-journeys: the goal-proposer appends NEW Must-have journeys ONLY
     between the two markers below (see the goal-self-extension skill). The human-authored journeys
     above and the Anti-goals below are never machine-edited. An empty block = nothing auto-proposed yet. -->
<!-- AUTO:journeys -->
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
  produced while the database was known to be damaged — everything dated from the iter-5 drill until J-10's
  post-recovery verification passes — **remains marked unusable as prospective/out-of-sample evidence**;
  only a separately regenerated artifact, minted after verified recovery under the existing create-once and
  version rules, may carry eligibility, and it remains subject to the same version and
  `prospective_eligible` contract as any other artifact. The incident record itself is evidence: the iter-5
  drill result, its handoff, the reviewer/QA evidence already produced, and the explicit statement that the
  committed seed could not restore these dates MUST NOT be deleted, rewritten, or silently superseded.
  Repairing the database never rewrites historical causality. *(critical)*

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
  against the knowingly damaged database before J-10's post-recovery verification passes** — the only
  work that proceeds is the recovery itself and its verification. Artifacts already produced from the
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
  remove-data cascade (`:2170-2177`); no foreign key to `scanner_runs` (rebuild recreates ids) —
  `source_run_created_at` + `engine_identity` are the rebuild detectors, never the dataset stamp alone.
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
