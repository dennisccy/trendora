# Goal Iteration 35 — Make selection disposition truthful: leadership floor is the only inclusion gate

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 35
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-12
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. Candidate framing is "worth monitoring", never advice. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-11 — No new composite candidate number:** no "fit", "conviction", "match", "probability of success", or any new blended score may be attached to candidates, the market, or the manifest; candidate presentation is limited to the existing three scores/buckets, config word maps, and structured reason/caution codes. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change; corrections happen only as new version rows; a historical view never substitutes a newer manifest. *(critical)*
  - **AG-15 — No outcome-tuned selection:** the selection rule and its thresholds must not be chosen or revised from realized forward returns within this goal; no Evidence Claim is introduced for it; any future selection-edge claim goes through the pre-registration registry and referee. *(critical)*
  - **AG-16 — Cohorts are not controls:** the comparison cohort and the near-threshold shadow cohort are frozen non-selected pools, not matched or causal control groups; no surface, artifact, or narrative may present candidate-vs-cohort differences as causal, as expectancy, or as a certified edge; any incremental-value or threshold study over these cohorts requires its own pre-registered experiment (registry + referee) in a future goal, consuming only manifests with `prospective_eligible: true` — consumers must fail closed, treating anything other than `true` (including an absent field) as ineligible, verifying `manifest_hash` over the artifact bytes BEFORE trusting any field (a mismatch rejects the artifact for prospective use), and treating an individual downstream observation as prospective only when its event timestamp is strictly later than the manifest's `available_at_utc` — `prospective_eligible: true` is necessary but not sufficient per observation. *(critical)*
  - **AG-17 — Repair never rewrites provenance (owner, 2026-08-20):** restoring deleted historical data MUST NOT retroactively change research provenance. A manifest that was retrospective or ineligible stays that way; **`prospective_eligible` is never upgraded merely because historical data was later repaired**; `available_at_utc`, manifest versions, `content_hash`/`manifest_hash`, and prior eligibility classifications remain immutable (AG-12 governs the rows and files themselves). Any manifest or artifact produced while the database was known to be damaged — everything dated from the iter-5 drill until **J-11 Stage G** passes (owner, 2026-08-21) — **remains marked unusable as prospective/out-of-sample evidence**; nothing is retroactively marked prospective merely because raw bars were repaired in J-10 or derived snapshots were regenerated in J-11. Only a separately regenerated artifact, minted after verified recovery under the existing create-once and version rules, may carry eligibility. *(critical)*

## GOAL

Fix `app.engine.compass.evaluate_selection` so `leadership_min_score` is the ONLY candidacy inclusion
gate — as the goal file and the config's own comments already declare — so that no row clearing the
leadership floor is ever displayed with the false `below_selection_floor` disposition label again.

## BACKGROUND

Prior verdict (iter-34) was `GOAL_ACHIEVED` with all 11 then-existing Must-have journeys passing; the
evaluator's next-step recommendation and this dispatch's depth field both read `evidence` (walkthrough
capture only on already-passing work). Since that verdict, the goal-proposer appended two NEW Must-have
journeys to `docs/goal.md`'s AUTO block (2026-09-01): J-12 and J-13. Neither is recorded passing —
`Depth: evidence` is defined only for target journeys "already recorded passing" whose only deliverable
is capture, so it does not apply to either; picking up real, never-built work here follows the target
priority rubric's rule 3 (prefer a failing journey) and the hard rule that an evidence-only iteration is
never planned except when ALL target-journey work is capture on already-passing journeys — not the case
here. I verified J-12's cited defect directly rather than trusting the goal text: `evaluate_selection`
(`apps/backend/app/engine/compass.py:602-703`) currently builds `qualifying`/`non_qualifying` from ALL
THREE checks (leadership, entry, risk) via `_qualifier_checks`, so any row failing entry or risk while
still clearing the leadership floor is dumped into `non_qualifying` and unconditionally labeled
`below_selection_floor` (line 666) — confirmed on the committed frontier export
(`2026-08-12_v7.json`): 37 of 539 `comparison_cohort` rows carry `leadership_score >= 80.0` (up to HPE
at 92.71) yet are labeled `below_selection_floor`. `config.yaml:1434`'s own comment already states
"the ONLY candidacy gate on Leadership" — the code contradicts the config's stated intent and the goal
file's declared rule ("floor → deterministic order → cap; nothing else excludes").

Between J-12 and J-13 (both new, both unbuilt), this iteration targets J-12 only (rubric rule 4,
smallest spec wins ties, and rule 5, never bundle two risky journeys): J-12 is confined to one backend
engine module (`compass.py`) plus a `config.yaml` `rule_version` bump plus tests — no frontend code
change, since the existing candidate/why-not/checklist/manifest-strip components already render
whatever fields the engine serves. J-13 (Leadership rotation duplication/direction/completeness) needs
backend AND frontend work and is deferred to a future iteration. No FULL-depth trigger holds: J-12's own
Acceptance text rules out a data-model migration ("no new producer, no new route, no new Data Contract
value"); the change is confined to one module, not clearly cross-cutting; the prior verdict is
`GOAL_ACHIEVED`, not `ESCALATE`; and consecutive lean iterations are at 0 of a 6-iteration hardening
cadence. No full trigger holds — this is depth `lean`. Last coherence verdict was `COHERENCE-PASS`, so
no consolidation pass is required. This deviation from the dispatched `evidence` depth, and the choice
of J-12 over J-13, is logged in `runs/goal-session-market-compass/state/assumptions.md` (`iter-35 —
goal-decomposer`). A `blueprint.md` note (iter-35) has been added documenting this plan against the
already-registered "Next-session manifest — CONTENT block" Data Contract row — no IA or Data Contract
change results, since the fix reads/writes the same producer and endpoint.

**Binding "Do not redo" carried from iter-34 (unaffected by this iteration):** J-09 stays closed — do
not touch `warmup.py`/`prices.py`; the harness fix's correctness stays proven — only its wiring is an
outstanding, non-blocking, out-of-goal tooling item; Constraints (a)/(b)/(c) stay landed; the six carried
walkthrough-attribution items and J-04's screenshot crop stay evidence-make-up passengers, never this
iteration's goal; `.steps/*.done` is not a depth signal — verify depth from `iter-35/depth-dispatched`
and the `Depth arbiter:` line in `engine.log`.

## IN SCOPE

### Backend
- [ ] `apps/backend/app/engine/compass.py`: change `evaluate_selection`'s partition logic so only the
      `leadership_min_score` check determines `qualifying` vs. `non_qualifying` (candidacy gate);
      `entry_min_score`/`risk_max_score` become advisory qualifiers that never remove a row from
      candidacy.
- [ ] Same file: make `selection_disposition` truthful by construction per row — every non-candidate
      row that clears the leadership floor is `excluded_by_cap`; every row below the leadership floor
      is `below_selection_floor`; add an assertion/test that each label's own predicate holds.
- [ ] Same file: update `_candidate_payload`/checklist construction so each qualifier check
      (`leadership_min_score`, `entry_min_score`, `risk_max_score`) is tagged `gating` or `advisory`;
      a candidate that misses an advisory qualifier renders a **caution** citing the threshold and the
      row's actual stored value, never a "reason" claiming it clears that qualifier.
- [ ] Same file: fix `candidates_empty_reason` so it names only the gating rule (leadership), never
      entry/risk as though they gated.
- [ ] `config.yaml`: bump `compass.selection.rule_version` so manifests minted under the corrected rule
      are distinguishable from those minted under the old one; change no threshold VALUE.
- [ ] `apps/backend/tests/test_compass.py` / `test_manifest_invariants.py`: add the fixture row the
      suite lacks (leadership above floor, entry/risk qualifier failing — the real HPE shape,
      L≈92.7 / E≈21.5 / R≈58.9) and complete the qualifier counter-test — perturbing
      `entry_min_score`/`risk_max_score` must leave `candidate_rule_hash`, `cohort_rule_hash`, the
      candidate list, `comparison_cohort` membership, every `selection_disposition`, and the shadow
      cohort unchanged.
- [ ] `apps/backend/tests/test_api_compass.py`: assert `GET /api/compass`'s `selection.candidates`
      count agrees with the Next-session focus section's count and the summary's focus-count sentence
      at the frontier as-of.

### New user-facing capability
None — this is a correctness fix to data already displayed by existing, already-built UI (Next-session
focus section, manifest strip's expanded table, candidate why/why-not cards).

### New information displayed
None — no new field; existing `selection_disposition`, caution, and checklist fields become truthful.

### New user actions
None.

### UI surface changes
None — no frontend code changes; existing components re-render corrected data from the same endpoint.

### Product surface delta
The Next-session focus section, manifest strip's expanded table, and candidate why/why-not cards on `/`
(and on historical as-of views reading manifests minted after the `rule_version` bump) display
`excluded_by_cap` instead of `below_selection_floor` for any row that clears the leadership floor but is
cut only by the candidate cap, and show an advisory caution (not a false "clears" reason) for any
candidate that misses an entry/risk qualifier.

### Blueprint conformance
Today (`/`) — Next-session focus section / manifest strip, the already-registered canonical home for
J-04/J-05/J-06 per `state/blueprint.md`'s Information Architecture table. No new page or nav entry.

### Data-contract additions
None. This fix reads/writes the SAME "Next-session manifest — CONTENT block" Data Contract row
(computed by `app.engine.compass.build_manifest_payload`/`evaluate_selection`, served only by
`GET /api/compass`) — no new field, no new producer, no new endpoint, no schema-file version bump.
`state/blueprint.md` carries a dated iter-35 note on this existing row recording the `rule_version` bump
and the truthful-disposition invariant, per J-12's own Acceptance requirement.

## OUT OF SCOPE

- Any change to `next_session_manifests`' schema, any new endpoint, or any new Data Contract value.
- Mutating, deleting, re-exporting, or re-hashing any EXISTING stored manifest row or export file
  (AG-12) — pre-fix mislabeled versions (e.g. `2026-08-12_v7`) keep their original
  `selection_disposition`/`prospective_eligible` values exactly (AG-17); the correction applies only to
  manifests minted after the `rule_version` bump.
- Any new versioned JSON schema file or `schema_version` bump; the `selection_disposition` closed
  vocabulary stays exactly `below_selection_floor` | `excluded_by_cap`.
- Changing any threshold VALUE (`leadership_min_score`, `entry_min_score`, `risk_max_score`) — only
  which checks GATE vs. ANNOTATE changes (AG-15); nothing here is chosen from realized forward returns.
- Any frontend component change — existing components already render whatever fields the engine serves.
- J-13 (Leadership rotation duplication/direction/completeness) — a separate, larger, full-stack
  journey; deferred to a future iteration (rubric rule 5: never bundle two risky journeys).
- Re-litigating J-09's memory closure or touching `warmup.py`/`prices.py` (binding "Do not redo").
- The harness fix's wiring gap (waived-evidence exemption not invoked by the merge step) — non-blocking,
  outside this goal.
- J-04's screenshot crop re-take and the six journeys' owed walkthrough attribution (J-02/J-03/J-05/
  J-06/J-07/J-08) — evidence make-up passengers, never a standalone iteration goal.
- The five older carried owner questions and the mechanical "confirm it lands" item — unrelated to J-12.

## DEFINITION OF DONE

- [ ] J-12 passes via browser-qa-agent (walkthrough of the corrected disposition table, a caution-
      qualifier candidate, and the Next-session focus section under the corrected rule)
- [ ] Required-still-passing journeys J-01..J-08 remain green (deterministic replay + LLM fallback)
- [ ] No anti-goal violation introduced (AG-1, AG-2, AG-3, AG-11, AG-12, AG-15, AG-16, AG-17 all checked
      explicitly in the dev handoff)
- [ ] Unit tests pass, including the new qualifier counter-test (hash + membership invariance) and the
      per-row disposition-predicate test; no regressions on untouched test files
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-35-dev.md`, recording the pre-fix
      baseline (37/539 mislabeled rows, HPE 92.71 highest) BEFORE any code change

## TESTING REQUIREMENTS

- Browser: J-12 (target); J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08 (required-still-passing,
  deterministic replay with LLM fallback where no golden exists)
- Unit/integration: `apps/backend/tests/test_compass.py` (qualifier gating logic, per-row disposition
  predicate, counter-test hash+membership invariance, new HPE-shape fixture row),
  `test_manifest_invariants.py` (byte-identity / AG-12 / AG-17 on pre-existing rows),
  `test_api_compass.py` (candidate-count agreement across focus section, summary sentence, and
  `GET /api/compass`)
- Error cases: a row below the leadership floor must never appear as a candidate or `excluded_by_cap`
  regardless of its entry/risk scores; a row above the leadership floor that fails BOTH entry and risk
  must still be included as a candidate or `excluded_by_cap` (never `below_selection_floor`)

Test-first contract:

- TC-1: given the committed frontier export `apps/backend/data/exports/next_session_manifests/2026-08-12_v7.json`, when `comparison_cohort` rows are counted for `leadership_score >= 80.0` AND `selection_disposition == "below_selection_floor"`, then the count is 37 of 539 rows with HPE at `leadership_score` 92.71 the highest — recorded in the dev handoff as the pre-fix baseline before any code change.
- TC-2: given the corrected `evaluate_selection` and a new manifest minted under the bumped `rule_version`, when the same count is run on the new manifest's `comparison_cohort`, then zero rows have `leadership_score >= leadership_min_score` AND `selection_disposition == "below_selection_floor"`.
- TC-3: given the new manifest's `disposition_tally`, when the two counts are summed, then `below_selection_floor + excluded_by_cap` equals member count minus candidate count exactly (record the measured values, e.g. 502 + 27 + 10 = 539, if today's data has moved).
- TC-4: given the qualifier counter-test fixture (the existing below-floor row plus the new HPE-shape row, leadership above floor but a qualifier failing), when `entry_min_score` and `risk_max_score` are perturbed in the test, then `candidate_rule_hash`, `cohort_rule_hash`, the candidate list, `comparison_cohort` membership, every `selection_disposition`, and the near-threshold shadow cohort are all unchanged between the perturbed and unperturbed runs.
- TC-5: given the HPE-shape fixture row (leadership above floor, `entry_quality_score` below `entry_min_score`), when `evaluate_selection` runs, then the row is included as a candidate or `excluded_by_cap` (never `below_selection_floor`) and carries an advisory caution citing `entry_min_score` and the row's actual `entry_quality_score` value.
- TC-6: given a candidate row that fails an advisory qualifier, when the eligibility checklist is rendered, then that check's verdict is one of {Pass, Miss, Supportive, Neutral, Unknown, NA} and is tagged `advisory` (never `gating`), while the leadership check alone is tagged `gating`.
- TC-7: given a synthetic fixture where zero members clear the leadership floor, when `candidates_empty_reason` is generated, then its text cites only the leadership-floor rule and contains no reference to `entry_min_score` or `risk_max_score` as a gating cause.
- TC-8: given the frontier as-of `2026-08-12` after a new manifest version is minted under the corrected rule and `/` is loaded with no `asof` param, then the Next-session focus section's candidate count, the plain-English summary's focus-count sentence, and `GET /api/compass`'s `selection.candidates` array length all report the same number.
- TC-9: given the same frontier view, when the manifest strip's expanded table is opened, then no row with `leadership_score >= 80.0` displays `below_selection_floor` — every such row shows `excluded_by_cap`, matching TC-2's zero-mislabel result.
- TC-10: given the near-threshold shadow cohort measured before this iteration's code change, when compared to the shadow cohort measured after, then membership (leadership in `[shadow.min_score, leadership_min_score)`) is identical (same 25 rows) since `cohort_rule_hash`'s shadow-band semantics are untouched by this journey.
- TC-11: given all pre-existing `next_session_manifests` rows and their exported files, when byte-compared before and after this iteration's code change, then every row and file is byte-identical (0 differing) and no new version is minted by the code change alone — only an explicit, separately-authorized freeze/regenerate action mints one.
- TC-12: given the pre-fix mislabeled manifest version `2026-08-12_v7`, when read after the fix ships, then its stored `selection_disposition` values and `prospective_eligible` classification remain exactly as originally frozen (AG-17) — the correction applies only to manifests minted after the `rule_version` bump.
- TC-13: given the J-12 demo capture, when `demo.sh market-compass --session-live` runs, then the recording shows, each attributed to J-12: (a) an above-floor name no longer labelled "below the selection floor", (b) a candidate carrying an advisory-qualifier caution, and (c) the Next-session focus section under the corrected rule.
- TC-14: given J-04's why/why-not acceptance limbs (steps 4-5, unchanged by this journey), when re-run via deterministic replay, then the gating verdicts alone still reproduce inclusion/exclusion for every spot-checked name, matching J-04's existing passing status.
- TC-15: given J-06's stated counter-test ("changing a caution qualifier moves neither hash nor any membership"), when the new fixture from TC-4 runs, then the assertion holds on BOTH hashes AND on membership — not merely on the hashes as before.

## NOTES

- Applies the "Do not redo" and prior lessons unaffected by this iteration (see BACKGROUND); none of
  iters 28-34's lessons concern `compass.py`'s selection logic directly, so no additional lesson applies
  here beyond the general caution (iter-33's ESCALATE reasoning) that changes to code shared by many
  downstream readers warrant a wide, relevance-based regression set — reflected in the 8-journey
  Required-still-passing list above (every journey reading the same "Next-session manifest" Data
  Contract row or hosted on the Today/Market pages this fix's output feeds).
- If step 2's rule conformance is found, during implementation, to conflict with any anti-goal or to
  regress a currently-passing journey, the developer must STOP and surface it for owner review rather
  than widening the rule — per J-12's own Acceptance text.
- J-13 is the natural next target once J-12 lands; it is NOT started this iteration.
