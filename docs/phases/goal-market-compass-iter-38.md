# Goal Iteration 38 — "Not priority" names its real reason: advisory misses restored, near-miss names return

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 38
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — structural/cross-cutting: a brand-new, never-built full-stack journey whose
  interaction (backend advisory-reason computation rendered truthfully by the frontend) is covered by
  no existing test. The change touches `apps/backend/app/engine/compass.py` (`evaluate_selection`),
  `apps/frontend/components/compass-focus-section.tsx`, `apps/frontend/lib/api.ts`, and two backend
  test files — 5 modules whose combined behavior only this journey's own (not-yet-written) tests
  exercise together.
- **Frontend Present:** yes
- **Target journeys:** J-14
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. Candidate framing is "worth monitoring", never advice. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-11 — No new composite candidate number:** no "fit", "conviction", "match", "probability of success", or any new blended score may be attached to candidates, the market, or the manifest; candidate presentation is limited to the existing three scores/buckets, config word maps, and structured reason/caution codes. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change; corrections happen only as new version rows; a historical view never substitutes a newer manifest. *(critical)*
  - **AG-15 — No outcome-tuned selection:** the selection rule and its thresholds must not be chosen or revised from realized forward returns within this goal; no Evidence Claim is introduced for it; any future selection-edge claim goes through the pre-registration registry and referee. *(critical)*
  - **AG-16 — Cohorts are not controls:** the comparison cohort and the near-threshold shadow cohort are frozen non-selected pools, not matched or causal control groups; no surface, artifact, or narrative may present candidate-vs-cohort differences as causal, as expectancy, or as a certified edge; any incremental-value or threshold study over these cohorts requires its own pre-registered experiment (registry + referee) in a future goal. *(critical)*
  - **AG-17 — Repair never rewrites provenance (owner, 2026-08-20):** restoring deleted historical data MUST NOT retroactively change research provenance. A manifest that was retrospective or ineligible stays that way; `prospective_eligible` is never upgraded merely because historical data was later repaired; `available_at_utc`, manifest versions, `content_hash`/`manifest_hash`, and prior eligibility classifications remain immutable (AG-12 governs the rows and files themselves). *(critical)*

## GOAL

Make the Next-session focus section's "Not priority" list state each non-candidate's actual, true reason for exclusion — instead of falsely claiming 20 of 20 shown names "passed every qualifier" — and restore the near-miss names that a stale cap-only assumption currently makes unlistable no matter how close they came.

## BACKGROUND

Iteration 37 closed the session at 13/13 Must-have journeys `passing` and returned `GOAL_ACHIEVED`. The dispatch's evaluator depth recommendation for this iteration ("evidence") was computed against that closed state — but `docs/goal.md`'s `AUTO:journeys` block now carries two new journeys the continuous-improvement loop appended the same day (goal-proposer, 2026-09-01): **J-14** (this iteration's target) and **J-15** (queued next). Neither has any entry in `journey-history.json` — both are genuinely never-built. Per this agent's own rules, the evidence-only exception (rule 7) applies only "when the prior evaluator's next-step asks ONLY for evidence on already-passing journeys" — that no longer describes the state once measured, cited, unbuilt failing-journey work exists, so the recommendation does not bind here; the brand-new-full-stack-journey escape condition controls instead (logged to the assumption ledger). `docs/goal.md`'s own loop-mechanics rule independently supports `full`: "Depth: lean by default; full when an iteration first lands user-visible UI changes" — J-14 is exactly that.

J-14's own measurement (reproduced directly against the committed `2026-08-12_v9.json` export and `apps/backend/app/engine/compass.py:842-850`) is concrete and severe: **all 20 served `why_not` entries carry an empty `failed_conditions`**, and `compass-focus-section.tsx:119-121` turns that emptiness into the sentence "— passed every qualifier, cut only by the focus-list cap." for every one of them — but 20 of 20 of those same names fail the advisory `entry_min_score` qualifier (four also fail `risk_max_score`) per the SAME manifest's `comparison_cohort` rows. This is a live false claim rendered on the page, not a hypothetical. Separately, because `why_not_pool.extend((row, []) for row, _checks in excluded_by_cap_pairs)` discards `_checks` and the pool is leadership-sorted before the `why_not_cap` (20) truncation, the entire visible why-not list is made of `excluded_by_cap` names only — none of the 25 non-candidates in the `[why_not_floor 75.0, leadership_min_score 80.0)` near-miss band, the names that most literally "just missed" the only real gate, can ever appear. Root cause: a J-12-era (iter-35) correction made `entry_min_score`/`risk_max_score` advisory-only but left this cap-exclusion line's now-stale comment and behavior ("passed everything, cut by cap") untouched, and the one fixture that could catch it (`test_excluded_by_cap_get_empty_failed_conditions`) only ever exercises rows that truly do pass everything — the exact "fixture confounds two hypotheses" failure mode iter-35's own lesson names, applying one level further down the same function.

Per the priority rubric (rule 5, never bundle two risky journeys), **this iteration targets J-14 alone**; J-15 (the stock-kind "Suppressed moves" undercount) is comparably sized, independent, and queued for the next iteration rather than bundled — a joint failure between two engine-level accounting fixes would be undiagnosable. Required-still-passing is widened to all thirteen other Must-have journeys because the touched function, `evaluate_selection` (part of `app.engine.compass.build_manifest_payload`), is the SAME producer already registered for J-02/J-04/J-05/J-06/J-07/J-12/J-13, and this iteration must prove `candidate_rule_hash`, `cohort_rule_hash`, candidate membership, and all prior stored manifests are provably unmoved — following the same full-regression pattern iter-37 used for the same producer.

**Lesson applied (iter-35, `apps/backend/tests/test_compass.py` / `test_manifest_invariants.py`):** a multi-condition gate's fixture must isolate each condition — a row that fails two conditions at once cannot prove either failure is detected on its own. J-14 step 7 already requires two isolating fixture rows (an above-floor, qualifier-failing, cap-excluded row shaped like DXCM, and a below-floor near-miss); this spec's TESTING REQUIREMENTS bind that requirement explicitly so it is not silently dropped the way TC-24's fixture confound survived 34 iterations.

**Lesson applied (iter-36):** a screenshot can be present, correctly named, and cited in a PASS row while showing nothing — measure any new capture (`PIL.Image.getcolors()` or equivalent; compare file size to sibling captures), never credit it from its filename.

## IN SCOPE

### Backend
- [ ] `apps/backend/app/engine/compass.py`, `evaluate_selection`: stop discarding the advisory qualifier checks for cap-excluded rows; carry each row's true evaluation (gating vs advisory, reusing the existing `gating` tag from `_qualifier_checks` — no new vocabulary) into its `why_not` entry's `failed_conditions`.
- [ ] Same function: add a `reason` field to each `why_not` entry using the existing `_DISPOSITION_EXCLUDED_BY_CAP` / `_DISPOSITION_BELOW_FLOOR` closed vocabulary (already used by `comparison_cohort.selection_disposition`) — no new label set.
- [ ] Same function: restore near-miss names — the why-not pool must represent BOTH exclusion reasons (cap-excluded and below-floor-in-band) rather than being dominated entirely by cap-excluded names before the `why_not_cap` truncation; add the disclosed uncapped per-reason pool counts described in Data-contract additions below, computed from the same partitions the disposition tally already computes (no new query, no full-universe pass).
- [ ] For cap-excluded entries, add the row's leadership rank among qualifying (above-floor) rows and the configured cap value, so the frontend can name "ranked N of the above-floor names, cap C" instead of a bare "cut by cap".
- [ ] Any new threshold/config the split needs (if any) lives under the existing `compass.selection` namespace in `config.yaml`; `compass.py` stays a `test_no_magic_numbers.CALC_FILES` entry — no literal threshold in code.
- [ ] Prove non-interference: `candidate_rule_hash`, `cohort_rule_hash`, `disposition_tally`, `candidates`, `comparison_cohort`, and `near_threshold_shadow` are byte-identical before/after on the same as-of; only `manifest_config_hash` and `content_hash` move on newly minted manifests (matching the goal's own scope rule that why-not display keys live only in the broad `manifest_config_hash`).
- [ ] `apps/backend/tests/test_manifest_invariants.py`: extend `test_tc23_why_not_and_qualifier_changes_move_only_manifest_config_hash` to cover the new `why_not` keys.
- [ ] `apps/backend/tests/test_compass.py`: replace/extend `test_excluded_by_cap_get_empty_failed_conditions` with the two isolating fixtures from J-14 step 7 (an above-floor, qualifier-failing, cap-excluded row shaped like the real DXCM row — L≈84.98/E≈26.53/R≈57.63 — alongside a below-floor near-miss); assert no entry is served as passing a qualifier its stored row fails, and both reason classes appear together when both exist in the fixture universe.
- [ ] Do not mutate, relabel, re-hash, re-export, or delete `apps/backend/data/exports/next_session_manifests/2026-08-12_v9.json` or any stored manifest row (AG-12/AG-17) — it is baseline evidence, read-only.

### Frontend
- [ ] `apps/frontend/lib/api.ts`: correct the `WhyNotEntry`/`WhyNotFailedCondition` TypeScript interfaces and their doc comments (currently false, at `~1048-1050`) to add `reason`, `gating` (per failed condition), and the cap-rank/cap fields, and to state the truthful contract — an empty `failed_conditions` means the row genuinely passed every qualifier, never inferred from `reason` alone.
- [ ] `apps/frontend/components/compass-focus-section.tsx`, `WhyNotList`: remove the false "— passed every qualifier, cut only by the focus-list cap." sentence for any entry with a non-empty `failed_conditions`; render `reason`-appropriate text — a cap-excluded entry names its rank and the cap plus any advisory misses (threshold/actual/distance), a below-floor entry names the leadership floor with its actual/distance (as today) plus any additional advisory misses; keep the existing "— passed every qualifier, cut only by the focus-list cap." sentence ONLY for entries that truly have zero failed conditions.
- [ ] Same component: disclose the two uncapped per-reason pool counts near the "Not priority" `Disclosure` summary (e.g., alongside the existing `(${selection.why_not.length})` count) so a reader sees how many were held back by each reason, not just how many are shown.
- [ ] No client-side threshold, no client-side rule, no client-side derivation of `reason`/`gating`/rank — every word rendered is a served field (matches the file's own existing "re-renders served structures, implements no rule" comment).

### New user-facing capability
A reader expanding "Not priority" on the Today page sees each name's real, true reason for exclusion — which qualifier it actually failed (with threshold, actual value, and distance) or, if it truly passed everything, that it was cut only by the candidate cap and where it ranked — plus the two disclosed counts of how many names were held back by each reason.

### New information displayed
- Per why-not entry: `reason` (cap-excluded vs below-floor), each failed condition's `gating` flag, and (for cap-excluded entries) the row's rank among qualifying names and the cap value.
- Two disclosed uncapped pool counts: how many non-candidates were held back by the cap, and how many below-floor near-misses sit in the why-not band.

### New user actions
None — the "Not priority" `Disclosure` already exists; this iteration corrects and extends what it renders. No new button or control.

### UI surface changes
`apps/frontend/components/compass-focus-section.tsx`'s existing "Not priority" disclosure on the Today page (`/`) only — no new card, panel, or route.

### Product surface delta
The "Not priority" list stops making a claim its own stored data contradicts, and previously-unlistable below-floor near-miss names can now appear. No new page, no new nav entry, no new card.

### Blueprint conformance
Lives entirely under the already-registered Information-Architecture home "Today (`/`)" and the already-registered Data-Contract row "Next-session manifest — CONTENT block" (`selection.why_not`, part of `selection.*`) — see the iter-38 note appended to `state/blueprint.md`. No new page, no new nav entry, no new Data-Contract row.

### Data-contract additions
All additive fields on the ALREADY-REGISTERED "Next-session manifest — CONTENT block" row (single computing module `app.engine.compass.evaluate_selection`, called from `app.engine.compass.build_manifest_payload`; single serving endpoint `GET /api/compass`; no second producer, no new route):

- `selection.why_not[].reason: "excluded_by_cap" | "below_selection_floor"` — reuses the EXISTING closed vocabulary already used by `comparison_cohort[].selection_disposition` (`_DISPOSITION_EXCLUDED_BY_CAP` / `_DISPOSITION_BELOW_FLOOR` constants) — no new vocabulary.
- `selection.why_not[].failed_conditions[].gating: bool` — new field on the EXISTING `failed_conditions` item shape (`condition: string, threshold: number, actual: number, distance: number`), reusing the `gating` tag `_qualifier_checks` already produces per check.
- `selection.why_not[].cap_rank: int >= 1 | null` — the row's 1-based leadership rank among all qualifying (above-floor) rows; non-null only when `reason == "excluded_by_cap"`.
- `selection.why_not[].cap: int >= 1 | null` — the configured `compass.selection.max_candidates` value at manifest-build time; non-null only when `reason == "excluded_by_cap"`.
- `selection.why_not_totals: { excluded_by_cap_uncapped: int >= 0, below_floor_in_band_uncapped: int >= 0 }` — the two full pool counts BEFORE the existing `why_not_cap` (20) truncation is applied; on today's committed frontier, measured 27 and 25 respectively (record the iteration's own measured values in the dev handoff if the frontier has moved).

No `schema_version` bump: `selection.why_not` and its entries are an unconstrained array in `docs/handoffs/trendora-next-session-manifest-v1.schema.json`, so every addition above is additive.

## OUT OF SCOPE

- **J-15** (stock-kind "Suppressed moves" undercount, `session_delta.py`) — independent, comparably risky, queued for the next iteration per rule 5 (never bundle two risky journeys).
- Any change to `compass.selection.leadership_min_score`, `entry_min_score`, or `risk_max_score` VALUES — this journey only makes existing evaluation visible, never retunes a threshold (AG-15).
- Any change to candidate membership, `disposition_tally`, `comparison_cohort` membership, or `near_threshold_shadow` — all must remain byte-identical (J-12's "Do not redo" stands).
- Regenerating, re-exporting, or re-hashing any existing stored `next_session_manifests` row or export file (AG-12/AG-17).
- The six queued evidence-capture walkthroughs (J-02, J-03, J-05, J-06, J-07, J-12) — non-blocking, ride as passengers or a future `Depth: evidence` round, never this iteration's purpose.
- Any of the "THREE SMALL CARRIED ITEMS" from iter-37's eval (pre-existing failing test on untouched files, the 7.8 GB iter-23 throwaway copy, `.next-verify/` tracked in git) or the "TWO UPSTREAM FIXES" (framework-level, not this session's product) — out of this iteration's scope; carried forward untouched.
- The five older owner questions (J-06 wording, J-01's first two test steps, empty next-session-focus acceptability, MNST recovery-list membership, 12-August "rebuilt" note) — none blocks this work; not addressed here.

## DEFINITION OF DONE

- [ ] J-14 passes via browser-qa-agent, including a measured (not filename-trusted) screenshot of the corrected "Not priority" list per the iter-36 lesson.
- [ ] Required-still-passing journeys J-01–J-13 remain green (deterministic replay + LLM fallback where no golden exists).
- [ ] No anti-goal violation introduced — AG-11/AG-12/AG-15/AG-16/AG-17 explicitly re-checked in the dev handoff.
- [ ] Unit tests pass; no regressions; the two isolating fixtures from J-14 step 7 are present and each isolates its own condition (iter-35 lesson).
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-38-dev.md`, citing the pre-fix baseline counts (20/20 empty `failed_conditions`, 27 cap-excluded above floor, 25 below-floor-in-band) and the post-fix measured counts.

## TESTING REQUIREMENTS

- Browser: J-14 (Today page, "Not priority" disclosure expanded).
- Unit/integration: `apps/backend/tests/test_compass.py` (isolating fixtures per J-14 step 7), `apps/backend/tests/test_manifest_invariants.py` (TC-23 extension for the new keys; hash-stability assertions).
- Error cases: a why-not pool with zero cap-excluded names (all near-misses purely below-floor) and zero below-floor-in-band names (all near-misses purely cap-excluded) must each still serve correct, non-crashing `why_not_totals` (explicit zero, never a missing field or a crash) — mirrors the J-15-adjacent "explicit zeros, never blank" pattern already required elsewhere in this goal.

- TC-1: given the DXCM-shaped fixture row (leadership ≈84.98, above the 80.0 gating floor; entry ≈26.53, below the 70.0 entry qualifier; risk ≈57.63, below the 60.0 risk ceiling) ranked beyond `max_candidates`, when `evaluate_selection` runs, then its `why_not` entry has `reason == "excluded_by_cap"`, `failed_conditions` containing exactly one entry for `entry_min_score` with `gating: false`, threshold `70.0`, and non-null `cap_rank`/`cap`.
- TC-2: given a fixture row that clears leadership, entry, AND risk qualifiers but is ranked beyond `max_candidates`, when `evaluate_selection` runs, then its `why_not` entry has `reason == "excluded_by_cap"`, `failed_conditions == []`, and non-null `cap_rank`/`cap`.
- TC-3: given a fixture row below `leadership_min_score` but at/above `why_not_floor`, when `evaluate_selection` runs, then its `why_not` entry has `reason == "below_selection_floor"`, `failed_conditions` containing the `leadership_min_score` check with `gating: true` and its threshold/actual/distance, and `cap_rank`/`cap` both `null`.
- TC-4: given the committed 2026-08-12 frontier data (or the iteration's own freshly measured baseline if the frontier has moved), when `GET /api/compass?as_of=2026-08-12` is called, then `selection.why_not_totals.excluded_by_cap_uncapped` and `selection.why_not_totals.below_floor_in_band_uncapped` equal the measured baseline counts and their sum is `>=` the number of distinct non-candidate leadership scores at or above `why_not_floor`.
- TC-5: given `evaluate_selection` run twice on the same as-of, once before and once after this change, when `candidate_rule_hash`, `cohort_rule_hash`, `disposition_tally`, `candidates`, `comparison_cohort`, and `near_threshold_shadow` are compared, then all six are byte-identical.
- TC-6: given the Next-session focus section rendered in a browser against the corrected `/api/compass` response, when the "Not priority" disclosure is expanded, then zero entries whose stored row fails an advisory qualifier display the sentence "passed every qualifier, cut only by the focus-list cap." — each such entry instead displays its named qualifier(s) with threshold, actual, and distance.
- TC-7: given the same rendered disclosure, when its summary/header is read, then it shows both disclosed totals (`excluded_by_cap_uncapped` and `below_floor_in_band_uncapped`) alongside the existing shown-count.
- TC-8: given `apps/frontend/lib/api.ts`'s `WhyNotEntry`/`WhyNotFailedCondition` doc comments, when read after this change, then they no longer state "an EMPTY failed_conditions means the member passed every qualifier and was excluded only by the focus-list cap" as a universal claim, and instead document `reason`, `gating`, `cap_rank`, and `cap`.
- TC-9: given a newly minted manifest carrying the new `why_not` fields, when validated against `docs/handoffs/trendora-next-session-manifest-v1.schema.json`, then validation passes with no `schema_version` bump.
- TC-10: given a `next_session_manifests` row/export minted BEFORE this change ships, when re-read after this change ships, then its stored bytes are byte-identical to before (AG-12).
- TC-11: given a fixture universe with zero cap-excluded names among the why-not pool, when `evaluate_selection` runs, then `selection.why_not_totals.excluded_by_cap_uncapped == 0` explicitly (not a missing/null field) and no entry is fabricated.

## NOTES

- **Assumption logged:** the evaluator's "evidence" depth recommendation for this iteration predates J-14/J-15's addition to `docs/goal.md` by the continuous-improvement loop; this spec treats the brand-new-full-stack-journey escape condition as controlling instead. Full entry in `runs/goal-session-market-compass/state/assumptions.md` under `## iter-38 — goal-decomposer`.
- **iter-35 lesson (binding here):** a multi-condition gate's fixture must isolate each failing condition on its own row — this spec's TC-1/TC-2/TC-3 and IN SCOPE's fixture requirement exist specifically so the DXCM-shaped row and the below-floor row each isolate exactly one condition, rather than repeating the TC-24 confound.
- **iter-36 lesson (binding here):** never credit a why-not screenshot from its filename or a PASS row — measure it (distinct-colour count or file-size comparison against sibling captures) before citing it as J-14 acceptance evidence.
- **iter-31/32 lesson (context, not directly triggered here):** before recording anything as an "owner-gated" blocker, re-read the underlying artifact — not applicable this iteration (no blocker is being carried), noted for the next evaluator pass.
- J-15 is next in queue; its own baseline (57 stock crossings evaluated, only 10 shown, 0 stock-kind suppressed rows, 4 named above-threshold movers — TRV/SJM/ALL/TTWO — vanishing from both lists) is already fully measured in `docs/goal.md` and needs no re-derivation when its turn comes.
