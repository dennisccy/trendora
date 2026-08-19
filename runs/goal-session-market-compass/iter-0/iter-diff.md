# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
diff --git a/docs/goal.md b/docs/goal.md
index d72ac8ee..3c20e490 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -41,14 +41,22 @@ manifest artifact (it must be self-describing and self-caveating).
   next-session candidates each with structured reasons AND cautions; the most-nearly-eligible
   why-not names; and the manifest's mode and freeze timestamp.
 - Every at-ingest close produces exactly one frozen manifest version whose export file bytes
-  equal the stored payload, carrying schema/rule/engine/dataset/universe stamps, and the seven
+  equal the stored payload, carrying schema/rule/engine/dataset/universe stamps, and the twelve
   manifest invariants (time-safety, immutability, reproducibility, create-once, mode honesty,
-  cohort reproducibility, fail-closed prospective eligibility) are each covered by a named
-  passing test.
+  cohort reproducibility, fail-closed prospective eligibility, availability-fence validity,
+  artifact integrity, rule-identity separation, disposition partition, schema conformance) are
+  each covered by a named passing test.
 - Every manifest freezes three cohorts — the candidates, the comparison cohort (the full
   non-selected pool), and the near-threshold shadow — plus a `prospective_eligible` flag
   derived fail-closed at write time; a retrospective or regenerated manifest is never
-  `prospective_eligible: true`.
+  `prospective_eligible: true`; every comparison member carries the same frozen matching
+  context as the shadow rows plus a closed-vocabulary selection disposition whose tallies
+  partition the cohort exactly.
+- The manifest carries a conservative `available_at_utc` availability fence and dual
+  identities — `content_hash` (research-content reproducibility) and `manifest_hash`
+  (whole-artifact integrity) — split rule identities (`candidate_rule_hash`,
+  `cohort_rule_hash`), and validates against the committed machine-readable schema at
+  `docs/handoffs/trendora-next-session-manifest-v1.schema.json`.
 - Sector attribution covers ≥ 95% of resolved members on newly produced runs (from ~22%
   today), with unknown still rendered "Unassigned" and the current-only basis disclosed.
 - `/` joins `reports/perf-budgets.md` and stays within its committed budgets; warm
@@ -73,7 +81,11 @@ manifest artifact (it must be self-describing and self-caveating).
    (engine identity, rule hash, dataset stamp, universe basis), frozen at ingest for the
    frontier date, exported as a byte-consistent JSON artifact; survives rebuild/removal;
    freezes the candidates plus a comparison cohort (the full non-selected pool) and a
-   near-threshold shadow cohort, with a fail-closed `prospective_eligible` flag.
+   near-threshold shadow cohort, with a fail-closed `prospective_eligible` flag; carries a
+   conservative `available_at_utc` availability fence, dual hashes (`content_hash` research
+   identity, `manifest_hash` artifact integrity), split rule identities
+   (`candidate_rule_hash` / `cohort_rule_hash`), and a committed machine-readable schema
+   contract.
 6. **Sector attribution coverage** — pool-sector wiring closing the 78%-Unassigned gap on
    new runs, descriptive-only, honestly disclosed.
 7. **Market page** — the relocated deep market context (cross-view chart, phase detail,
@@ -89,6 +101,9 @@ manifest artifact (it must be self-describing and self-caveating).
 - No LLM or generative text anywhere; no news/sentiment; no intraday/tick data.
 - No order placement, position sizing, portfolio logic, or trade simulation.
 - No modifications to the Tapeology repository, and no code/network coupling to it.
+- No cryptographic signing or PKI (the integrity hash detects corruption and accidental
+  mutation, not adversarial forgery — explicitly out of scope), and no exchange-calendar
+  subsystem (session-boundary prospectivity is owned by the future preregistered study).
 - No new factors, indicators, patterns, or macro-leg enablement; no new composite scores.
 - No incremental-value experiment yet — this cycle only records the prospective substrate
   (at-ingest manifests + frozen comparison and near-threshold cohorts); the experiment is a
@@ -141,9 +156,13 @@ manifest artifact (it must be self-describing and self-caveating).
   `app.engine.compass.build_manifest_payload`, persisted create-once in
   `next_session_manifests`, served only by `GET /api/compass`; the exported JSON file's
   bytes equal the stored `payload_json`. The session delta, narrative sentences, plain-word
-  labels, candidate set, reasons/cautions/trace, the comparison cohort (non-selected pool),
-  the near-threshold shadow cohort, and the `prospective_eligible` flag are all blocks
-  INSIDE this one document — no second producer, no client-side derivation.
+  labels, candidate set, reasons/cautions/trace, the comparison cohort (non-selected pool,
+  each member carrying its frozen matching context and `selection_disposition`), the
+  near-threshold shadow cohort, the `prospective_eligible` flag, the `available_at_utc`
+  fence, and both integrity hashes (`content_hash`, `manifest_hash`) are all blocks
+  INSIDE this one document — no second producer, no client-side derivation; the committed
+  schema at `docs/handoffs/trendora-next-session-manifest-v1.schema.json` is the
+  machine-readable contract every produced manifest must validate against.
 - **Engine identity**: computed only in `app.engine.engine_identity` from the config-listed
   file list + config subset; stamped on every manifest and on newly created `ScannerRun`
   rows (additive nullable column; old rows stay NULL as "pre-stamping"); displayed verbatim.
@@ -274,7 +293,9 @@ manifest artifact (it must be self-describing and self-caveating).
        rule table exists in frontend code (the trace rides the payload)
     6. Assert the "Not priority" entries each name their failed condition(s) with
        distances, and the aggregate exclusion counts partition member count minus
-       candidate count for the same as-of; assert the near-threshold shadow cohort
+       candidate count for the same as-of and equal the manifest's frozen
+       selection-disposition tallies (below the selection floor vs excluded only by the
+       candidate cap) re-read verbatim; assert the near-threshold shadow cohort
        appears nowhere in the focus section — not as a card, a pick, or an ordering
        input (it is visible only inside the manifest audit view under its explicit
        research-only label)
@@ -310,14 +331,23 @@ manifest artifact (it must be self-describing and self-caveating).
        and the run record's "Refreshed:" line names it
     2. Assert `GET /api/compass` for the frontier date serves a manifest with
        `mode: at_ingest`, `version: 1`, `frozen: true`, `prospective_eligible: true`,
-       `generation.producer: ingest_finalize`, a generation timestamp, the engine
-       identity, the selection-rule version and hash with its verbatim config subset, the
-       dataset stamp, and the universe block (pool hash, resolver gate values, member count)
+       `generation.producer: ingest_finalize`, a generation timestamp, a well-formed
+       `available_at_utc` fence not earlier than the generation timestamp plus the
+       configured margin, the engine identity, the split rule identities
+       (`candidate_rule_hash`, `cohort_rule_hash`) and the broad `manifest_config_hash` —
+       each with its verbatim config subset — the dataset stamp, the universe block (pool
+       hash, resolver gate values, member count), and both `content_hash` and
+       `manifest_hash`
     3. Assert the export file exists under the configured export directory and its bytes
-       equal the served `payload_json` (at-ingest exports only)
+       equal the served `payload_json` (at-ingest exports only), and that recomputing
+       `manifest_hash` over the exported bytes (hash field excluded per the canonical
+       rule) reproduces the embedded value
     4. Assert the manifest strip on `/` shows the same stamps and counts, and its expanded
        table equals the stored candidates, the comparison cohort (non-selected pool) whose
-       count equals member count minus candidate count, and the near-threshold shadow
+       count equals member count minus candidate count — each member carrying the same
+       frozen matching-context fields as the shadow rows plus a closed-vocabulary
+       `selection_disposition` whose tallies partition the cohort exactly — and the
+       near-threshold shadow
        cohort (members with leadership in the config band from `shadow.min_score` up to
        but excluding `leadership_min_score`) carrying its frozen per-name context fields
        under an explicit research-only label
@@ -330,24 +360,41 @@ manifest artifact (it must be self-describing and self-caveating).
        recorded frontier bar date exceeds its as-of and which carries
        `prospective_eligible: false` — and assert the frontier date's manifest can only be
        minted by the finalize freeze or an explicit regenerate, never by a plain GET
+    8. Cite in the dev handoff the passing schema-conformance test: the frozen at-ingest
+       manifest and the retrospective manifest both validate against the committed schema
+       `docs/handoffs/trendora-next-session-manifest-v1.schema.json`, whose required-field
+       set includes mode, producer, `available_at_utc`, `prospective_eligible`, both
+       hashes, both rule identities, the three cohorts, and the caveats block
   - Acceptance:
     - **Consistency (single source):** one producer (`compass.build_manifest_payload` +
       `persist_manifest`), one endpoint (`GET /api/compass`), one export whose bytes equal
       the stored payload; the finalize hook follows the existing honesty-gated
-      "Refreshed:" pattern.
+      "Refreshed:" pattern; the committed schema is the single machine-readable contract;
+      dispositions, cohort rows, and rule identities come from the same single selection
+      trace and identity helpers — never recomputed by the UI or the export.
     - **Correctness:** the content hash reproduces across rebuilds of the same inputs
       (fixture); stamps match the computed engine identity and rule-config hash; the
       data-driven mode rule assigns `at_ingest` only when no bar later than the as-of
       exists at generation; comparison and shadow membership reproduce exactly from the
-      frozen rule config plus the stored run (fixture).
+      frozen rule config plus the stored run (fixture); `content_hash` is invariant across
+      legitimate generation-metadata differences while `manifest_hash` changes when any
+      other field changes (fixture pair); disposition tallies partition member count minus
+      candidate count exactly.
     - **Honest status & anti-goals:** mode is never fabricated (fails toward
       retrospective); no future session DATE is fabricated — the manifest states
       "next session after the based-on close" semantically; the comparison cohort is
       explicitly labeled a frozen non-selected comparison pool — not a matched or causal
       control group; `prospective_eligible` is derived once at write from the recorded
       generation facts, fail-closed (any missing condition forces false; an absent field
-      reads as false); the artifact embeds its own evidence caveat ("Not yet proven —
-      attention rule, not a certified edge") and survivorship/sector-basis caveats.
+      reads as false); `available_at_utc` is a conservative fence — the canonical
+      serialization instant plus the configured `availability_margin_seconds` — so a
+      consumer never treats the artifact as available before durable publication, and
+      `prospective_eligible: true` additionally requires the fence present and well-formed
+      while remaining necessary but NOT sufficient for an individual downstream
+      observation (the observation's event timestamp must be strictly later than the
+      fence — the future study's rule); the artifact embeds its own evidence caveat ("Not
+      yet proven — attention rule, not a certified edge") and survivorship/sector-basis
+      caveats.
     - **Walkthrough:** a `[NEW]`-flagged walkthrough of ingest → freeze → stamps → export
       file, viewable via `demo.sh market-compass --session-live`.
 
@@ -365,17 +412,32 @@ manifest artifact (it must be self-describing and self-caveating).
     4. Trigger the explicit regenerate action for that as-of (confirm-gated); assert
        version 2 appears with its own mode and generation timestamp and carries
        `prospective_eligible: false` even when its mode computes `at_ingest` (only
-       version 1 minted by the finalize producer can ever be true), version 1 remains
-       readable and byte-identical with its flag unchanged, and the UI lists both
-       versions with their stamps
+       version 1 minted by the finalize producer can ever be true), its own
+       `available_at_utc` and its own `manifest_hash`, version 1 remains readable and
+       byte-identical with its flag unchanged, and the UI lists both versions with their
+       stamps
     5. Cite in the dev handoff the passing tests: time-safety (perturbing or deleting
        post-as-of bars leaves the content hash unchanged), rebuild survival
        (`clear_snapshot_set` and remove-data delete zero manifest rows), reproducibility
        (two builds of the same inputs produce identical content hashes), create-once
        concurrency (two simultaneous requests yield one row), cohort reproducibility
        (comparison + shadow membership reproduce from the frozen rule and stored run),
-       and prospective-eligibility derivation (each violated condition — mode, producer,
-       version, frozen, missing provenance — independently forces false)
+       prospective-eligibility derivation (each violated condition — mode, producer,
+       version, frozen, missing fence, missing provenance — independently forces false),
+       availability-fence conservatism (the recorded fence is never earlier than the
+       generation timestamp plus the configured margin), artifact tamper detection
+       (flipping any byte of a copied export — including `prospective_eligible` or a
+       provenance field — fails `manifest_hash` verification), hash-scope separation
+       (same content with different legitimate generation metadata yields an equal
+       `content_hash` and a different `manifest_hash`), identity-separation counter-tests
+       (changing the why-not display cap or a caution qualifier moves neither scientific
+       hash nor any membership; changing `shadow.min_score` moves `cohort_rule_hash`
+       only; changing `leadership_min_score` or `max_candidates` moves
+       `candidate_rule_hash`, the floor also moving `cohort_rule_hash` via the band
+       bound), disposition partition (every non-selected member carries exactly one
+       closed-vocabulary disposition and the tallies sum to the cohort count), and schema
+       conformance (produced manifests validate; a manifest missing any required
+       eligibility, fence, or hash field fails validation)
   - Acceptance:
     - **Consistency (single source):** the basis disclosure is a read-time comparison
       (source-run creation timestamp + engine identity), never a mutation; the dataset
@@ -515,7 +577,11 @@ manifest artifact (it must be self-describing and self-caveating).
   candidate-vs-cohort differences as causal, as expectancy, or as a certified edge; any incremental-value or
   threshold study over these cohorts requires its own pre-registered experiment (registry + referee) in a
   future goal, consuming only manifests with `prospective_eligible: true` — consumers must fail closed,
-  treating anything other than `true` (including an absent field) as ineligible. *(critical)*
+  treating anything other than `true` (including an absent field) as ineligible, verifying `manifest_hash`
+  over the artifact bytes BEFORE trusting any field (a mismatch rejects the artifact for prospective use),
+  and treating an individual downstream observation as prospective only when its event timestamp is
+  strictly later than the manifest's `available_at_utc` — `prospective_eligible: true` is necessary but
+  not sufficient per observation. *(critical)*
 
 ## Loop mechanics (for the iteration planner)
 
@@ -569,34 +635,70 @@ manifest artifact (it must be self-describing and self-caveating).
 - Mode rule is data-driven: `at_ingest` iff no bar dated later than the as-of exists at generation
   (`generation.frontier_bar_date` records the evidence); fails toward `retrospective`.
 - Serialize once: build payload → `json.dumps(sort_keys=True, default=str)` → store those bytes → export
-  those bytes; `content_hash` covers the content block only (excludes generated_at/mode/generation/dataset).
+  those bytes; `content_hash` covers the content block only (excludes generated_at, mode, the generation
+  block, the dataset block, `available_at_utc`, `prospective_eligible`, and `manifest_hash`) and remains
+  the research-content reproducibility identity. `manifest_hash` = sha256 over the canonical serialization
+  of the COMPLETE document with only the `manifest_hash` field excluded (a fixed placeholder during
+  computation), assembled before the INSERT so the stored and exported bytes carry it — the whole-artifact
+  integrity identity, distinct from `content_hash`; an integrity hash is not a signature: adversarial
+  forgery is out of scope (no signing/PKI in this goal).
 - Cohort blocks (all inside the one manifest document): `candidates` (unchanged);
   `comparison_cohort` — EVERY scored member of the source run not selected as a candidate,
-  compact field-array rows; its definition text carries verbatim "a frozen non-selected
-  comparison pool, not a matched or causal control group"; the shadow is a subset of it by
-  construction (shadow members are non-selected) and is never deduplicated out of it;
+  compact field-array rows carrying the SAME frozen matching-context fields as the shadow
+  rows (listed below) plus a `selection_disposition`; its definition text carries verbatim
+  "a frozen non-selected comparison pool, not a matched or causal control group"; the
+  shadow is a subset of it by construction (shadow members are non-selected) and is never
+  deduplicated out of it. `selection_disposition` — a closed vocabulary computed from the
+  same single `evaluate_selection` trace, exactly partitioning the non-selected set under
+  the frozen rule (floor → deterministic order → cap; nothing else excludes):
+  `below_selection_floor` (leadership below `leadership_min_score`) or `excluded_by_cap`
+  (met the floor, ordered out by `max_candidates`); tallies must sum to member count minus
+  candidate count; qualifiers annotate cautions and never gate inclusion today — if a
+  future rule makes a qualifier gating, the vocabulary and the candidate-rule scope must
+  extend together (rule_version bump), never by relabeling frozen rows.
   `near_threshold_shadow` — research-only substrate: scored members with leadership in
   `[shadow.min_score, leadership_min_score)` (half-open — a name at exactly the selection
   floor is candidate-eligible, never shadow), deterministic order (leadership desc,
   ticker), uncapped, taking no part in selection, display ranking, or the Today focus
-  section; each shadow row freezes contemporaneous context from the stored run row ONLY
-  (ticker, leadership/entry/risk score+bucket, setup_status, rank_in_run, sector, theme
+  section; its definition and the `caveats.cohort_semantics` note state that it is near
+  the LEADERSHIP selection floor specifically, not necessarily near the final
+  candidate-selection boundary (deterministic ordering, the candidate cap, and any future
+  gating qualifier also affect final inclusion) — never described as "near-selected".
+  Each cohort row freezes contemporaneous context from the stored run row ONLY (ticker,
+  leadership/entry/risk score+bucket, setup_status, rank_in_run, sector, theme
   memberships with that run's theme ranks, close, atr_pct value+percentile,
   high-proximity/distance-from-52w-high, gap p95, worst-20d, distance-to-invalidation,
-  ADV dollar figure — no new data sources); purpose note: it preserves a prospectively
-  frozen set of near-cutoff names for later better-matched or threshold-focused
+  ADV dollar figure — no new data sources); purpose note: the cohorts preserve a
+  prospectively frozen substrate for later better-matched or threshold-focused
   incremental-value studies without retrospective reconstruction.
 - `prospective_eligible` — derived ONCE at write, stored at the payload top level OUTSIDE
   the content-hash scope (generation-class metadata, like `mode`) plus a typed column for
   filtering; true iff ALL of: mode `at_ingest` with consistent frontier evidence
   (`generation.frontier_bar_date == based_on_close`), `generation.producer ==
-  "ingest_finalize"`, `version == 1`, `frozen: true`, and provenance complete (engine
-  identity, rule version+hash+verbatim config, dataset stamp, universe pool hash all
-  present). Never recomputed at read; a retrospective or regenerated manifest is always
-  false; consumers treat an absent field as false. `generation.preflight_verdict` is
-  recorded for later filtering but does NOT gate eligibility. The `generation` block gains
-  `producer: ingest_finalize / on_demand_get / regenerate`; the caveats block gains
-  `cohort_semantics` carrying the non-causal sentence.
+  "ingest_finalize"`, `version == 1`, `frozen: true`, a well-formed `available_at_utc`
+  present, and provenance complete (engine identity, `candidate_rule_hash` +
+  `cohort_rule_hash` + `manifest_config_hash` with their verbatim config subsets, dataset
+  stamp, universe pool hash, `manifest_hash` all present). Never recomputed at read; a
+  retrospective or regenerated manifest is always false; consumers treat an absent field
+  as false. `generation.preflight_verdict` is recorded for later filtering but does NOT
+  gate eligibility. The `generation` block gains `producer: ingest_finalize /
+  on_demand_get / regenerate`; the caveats block gains `cohort_semantics` carrying the
+  non-causal sentence and the shadow near-floor clarification.
+- `available_at_utc` — the authoritative downstream availability fence: the earliest
+  conservative timestamp at which the immutable artifact may be treated as available to a
+  downstream consumer. Recorded ONCE at write as the canonical-serialization instant PLUS
+  `compass.manifest.availability_margin_seconds` (default 60) so it never predates the
+  durable INSERT and export that follow within the same finalize phase — conservative by
+  construction (a too-late fence only shrinks the eligible window; a too-early fence would
+  fabricate prospectivity). Generation-class: outside `content_hash`, inside
+  `manifest_hash`; never back-dated or recomputed at read. It does NOT claim session-level
+  prospectivity: a stale local frontier can honestly yield `prospective_eligible: true`
+  with a fence days after `based_on_close` — the fence VALUE is what exposes it. Consumer
+  rule for future studies: an observation is prospective with respect to this manifest
+  only if its event timestamp is strictly later than `available_at_utc`; a claim that the
+  artifact was a full next-session prior must additionally establish that the fence
+  precedes the first included event/session boundary — session boundaries are the
+  preregistered study's responsibility (no exchange-calendar subsystem in Trendora).
 - Delta inputs: current vs previous stored run (indexed scalar select), the causal market-phase timeline
   from `market_phase_cached` (prev point of the SAME payload), stored sector/theme rank rows, and
   column-projected `ScannerResult` selects (ticker/scores/buckets/setup only — AG-8).
@@ -610,16 +712,35 @@ manifest artifact (it must be self-describing and self-caveating).
 - Config namespaces: `compass.selection` (rule_version, leadership_min_score 80.0, max_candidates,
   qualifiers entry_min_score 70.0 / risk_max_score 60.0, why_not floor 75.0 + cap,
   shadow.min_score 75.0 — the near-threshold band's own key, default equal to the why-not
-  display floor but independent of it so display tuning never moves the research band;
-  the whole `compass.selection` subtree is inside the rule-hash scope),
+  display floor but independent of it so display tuning never moves the research band),
   `compass.delta` (breadth_min_change_pts, rank_move_min, top_k, velocity_flat_band, pbear_bands,
   max_stock_items), `compass.vocabulary` (direction/level/score word maps),
-  `compass.manifest` (schema_version, export dir + modes: at_ingest only),
-  `provenance` (engine_files list, config_keys list), `universe.pool_sector_aliases` (default empty).
+  `compass.manifest` (schema_version, export dir + modes: at_ingest only,
+  availability_margin_seconds 60 — a publication-latency allowance, never a research
+  threshold — and the committed schema path), `provenance` (engine_files list, config_keys
+  list), `universe.pool_sector_aliases` (default empty). Identity scopes over
+  `compass.selection`: `candidate_rule_hash` covers ONLY membership/ordering-affecting
+  keys (rule_version, leadership_min_score, max_candidates, the declared ordering rule
+  "leadership desc, ticker asc"); `cohort_rule_hash` covers cohort semantics
+  (shadow.min_score, the shadow band's upper-bound VALUE — i.e. leadership_min_score, so a
+  floor change moves BOTH scientific hashes — the disposition vocabulary version, and the
+  cohort row field list); qualifiers (caution annotations) and why-not display keys live
+  ONLY in the broad `manifest_config_hash` over the whole `compass.selection` subtree — a
+  display or caution tweak never moves a scientific identity; each hash's config subset is
+  stored verbatim beside it.
   Env override for tests: `TRENDORA_COMPASS_EXPORT_DIR` (name only, never a value in files).
 - New engine modules join `CALC_FILES` in `apps/backend/tests/test_no_magic_numbers.py:19`.
 - Methodology: add the sector-basis disclosure and a "Next-session focus" entry whose thresholds ref the
   live `compass.selection.*` keys; TermInfo entries for every new word.
+- Handoff contract: a committed JSON Schema at
+  `docs/handoffs/trendora-next-session-manifest-v1.schema.json` (versioned in lockstep
+  with `schema_version`) defines required types/structures for mode, producer, the
+  generation block, `available_at_utc`, `prospective_eligible`, `content_hash`,
+  `manifest_hash`, engine/dataset/universe provenance, `candidate_rule_hash`,
+  `cohort_rule_hash`, the three cohorts (including disposition and the matching-context
+  field list), and the caveats block; fixture/contract tests prove every produced manifest
+  validates against it; a schema change is a NEW versioned file, never an in-place edit;
+  this is Trendora's producer-side contract only — no Tapeology importer in this goal.
 
 ### Traps (binding)
 - The producer must never read `forward_returns`, the fenced retrospective smoothing, or any bar later
@@ -634,6 +755,13 @@ manifest artifact (it must be self-describing and self-caveating).
 - `prospective_eligible` is write-once and version-shopping-proof by construction: only version 1 minted by
   the finalize producer can be true — a regenerate can never mint an eligible prior, even on the frontier
   with no new bars, and no read path recomputes the flag.
+- `available_at_utc` is never back-dated, never recomputed at read, and never derived from anything but the
+  write-time rule; its margin is a publication-latency allowance, never a research threshold — tuning it
+  from outcomes is forbidden like any threshold. Consumers verify `manifest_hash` BEFORE reading any field
+  and fail closed on a mismatch.
+- The disposition vocabulary is part of `cohort_rule_hash`'s scope: extending it (e.g. a future gating
+  qualifier) is a rule change carried by new manifests under a bumped rule_version — never a relabeling of
+  frozen rows.
 
 ### Future research enabled by this goal (explicitly NOT in scope)
 
@@ -644,5 +772,9 @@ Trendora candidate versus a comparable non-selected or near-threshold name? That
 is not part of this goal: it follows Tapeology's registration methodology (registration
 boundary, frozen denominators) plus Trendora's registry + referee, and it must consume only
 manifests with `prospective_eligible: true` (fail-closed — anything else, including an
-absent field, is ineligible). Until such a study passes, candidate-vs-cohort differences
-are descriptive only (AG-16).
+absent field, is ineligible), verify each artifact's `manifest_hash` before use, and count
+an observation as prospective only when its event timestamp is strictly later than that
+manifest's `available_at_utc` — artifact-level eligibility is necessary but not sufficient
+per observation, and establishing that the fence precedes the first included session
+boundary is the study's own preregistered rule (Trendora ships no exchange calendar).
+Until such a study passes, candidate-vs-cohort differences are descriptive only (AG-16).
```
