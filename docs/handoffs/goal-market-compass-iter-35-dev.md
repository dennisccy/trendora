# goal-market-compass-iter-35 Dev Handoff

**Phase:** goal-market-compass-iter-35
**Date:** 2026-09-01
**Agent:** developer
**Status:** complete

## Headline result

`app.engine.compass.evaluate_selection` now enforces exactly what `config.yaml`'s own comment and the
goal file's declared rule always said: `leadership_min_score` is the ONLY candidacy gate;
`entry_min_score`/`risk_max_score` are advisory qualifiers that annotate a caution and the eligibility
checklist but never remove a row from candidacy. Verified live on the real frontier export
(`2026-08-12`): a freshly minted manifest version (v8, via the existing confirm-gated
`POST /api/compass/regenerate` action) shows **0 of 539 `comparison_cohort` rows mislabeled**
`below_selection_floor` at/above the floor (was **37 of 539**, HPE 92.71 highest — the pre-fix baseline,
reproduced below BEFORE any code change was made). The disposition tally now reads
`below_selection_floor: 502, excluded_by_cap: 27` against **10 candidates** — `502 + 27 + 10 = 539`,
matching the goal file's own predicted measured partition exactly.

## Pre-fix baseline (TC-1, reproduced BEFORE any code change)

Read directly from the committed, untouched export file
`apps/backend/data/exports/next_session_manifests/2026-08-12_v7.json`:

```
total comparison_cohort rows: 539
mislabeled (leadership_score >= 80.0 AND selection_disposition == "below_selection_floor"): 37
highest: HPE 92.71 (leadership_bucket A, rank_in_run 1) -- labelled below_selection_floor
disposition_tally (pre-fix): {"below_selection_floor": 539, "excluded_by_cap": 0}
candidates (pre-fix): 0
```

This exactly matches J-12's BACKGROUND text (37/539, HPE 92.71 highest). Cause confirmed by reading
`apps/backend/app/engine/compass.py:602-703` (pre-fix): `evaluate_selection` built `qualifying` /
`non_qualifying` from ALL THREE `_qualifier_checks` results (`if all(check["passed"] for check in
checks)`), so a row failing `entry_min_score` or `risk_max_score` while still clearing the leadership
floor was dumped into `non_qualifying` and unconditionally stamped `below_selection_floor`.

## What Was Built

- **`apps/backend/app/engine/compass.py`**
  - `_qualifier_checks` — each of the three checks now carries its own `"gating"` boolean: `True` for
    `leadership_min_score` only, `False` for `entry_min_score`/`risk_max_score`. This is the SINGLE
    source of truth both the partition logic and the candidate checklist read (never re-derived twice).
  - `evaluate_selection`'s partition loop — changed the candidacy predicate from "ALL THREE checks pass"
    to "the ONE gating check (`leadership_min_score`) passes" (`assert`-guarded to exactly one gating
    check, so a future accidental second gating check fails loudly rather than silently). This alone
    fixes the mislabel: every row that clears the leadership floor is now `qualifying` regardless of its
    entry/risk qualifier outcome, so it becomes a candidate or (if the cap binds) `excluded_by_cap` —
    never `below_selection_floor`. The `why_not` pool, `comparison_cohort`, and `near_threshold_shadow`
    construction downstream were NOT changed — they already partitioned off the SAME
    `non_qualifying`/`excluded_by_cap_pairs` lists, so correcting the partition upstream makes every
    downstream disposition truthful by construction, with zero additional code.
  - `_candidate_payload` — rewritten to build `reasons` (a "clears" statement) ONLY for checks that
    passed, and a new advisory `caution` (citing the threshold AND the row's actual stored value, e.g.
    `"ENTRY_QUALITY_QUALIFIER: Entry Quality score 21.5 is below the 70.0 qualifier (Weak entry) --
    advisory only; Leadership alone determines candidacy."`) for any ADVISORY check that failed — never
    a reason claiming a qualifier was cleared when it was not. The `checklist` rows now carry the same
    `"gating"` tag (`True` for `leadership_min_score`, `False` for the other two) so a caller can
    reproduce inclusion from the gating verdict alone (J-04 steps 4-5 / TC-14). `what_would_change` is
    unchanged (still a neutral met/not-met echo of all three checks, never a "reason").
  - New `_assert_disposition_predicate(comparison_cohort, sel)` — a runtime, per-row assertion (mirrors
    `_scan_selection_language`'s belt-and-suspenders posture) that fires on EVERY produced manifest
    before `evaluate_selection` returns: `below_selection_floor` implies `leadership_score <
    leadership_min_score`; `excluded_by_cap` implies `leadership_score >= leadership_min_score`. Makes
    the disposition truthful by construction, not merely by the surrounding code's good behavior.
  - `candidates_empty_reason` — rewritten to name ONLY the leadership gating rule
    (`"No stored member cleared the Leadership score floor (80.0) for this as-of -- the sole candidacy
    gate."`); no longer cites `entry_min_score`/`risk_max_score` as though they gated (TC-7).
- **`config.yaml`** — `compass.selection.rule_version` bumped `"v1"` -> `"v2"` (already inside BOTH
  `candidate_rule_hash`'s and `cohort_rule_hash`'s scope, per `_candidate_rule_subset`/
  `_cohort_rule_subset`), so manifests minted under the corrected rule are distinguishable from those
  minted under the old (buggy) one. **No threshold VALUE changed** — `leadership_min_score` (80.0),
  `entry_min_score` (70.0), `risk_max_score` (60.0), `max_candidates`, `why_not_floor`, `why_not_cap`,
  `shadow.min_score` are all byte-identical to before (AG-15: nothing here is chosen from realized
  forward returns — only which checks GATE vs. ANNOTATE changed).
- **Tests** (`apps/backend/tests/test_compass.py`, `test_manifest_invariants.py`, `test_api_compass.py`)
  — see "Tests Run" below for the full list of new/changed tests.

## Files Changed

- `apps/backend/app/engine/compass.py` -- `_qualifier_checks` gating tag; `evaluate_selection`'s
  candidacy predicate now reads the gating tag only; `_candidate_payload`'s reason/caution/checklist
  construction; new `_assert_disposition_predicate`; `candidates_empty_reason` text.
- `config.yaml` -- `compass.selection.rule_version`: `"v1"` -> `"v2"` (no threshold value changed).
- `apps/backend/tests/test_compass.py` -- `selection_run` fixture gained an HPE-shape row (L=92.7,
  E=21.5, R=58.9 -- clears leadership, fails entry); updated the several assertions whose candidate
  count/tickers shift as a result (`test_candidates_match_stored_scores_and_word_maps`,
  `test_checklist_verdicts_reproduce_inclusion`, `test_excluded_by_cap_get_empty_failed_conditions`,
  `test_excluded_by_cap_cohort_rows_carry_that_disposition`, `test_risk_off_regime_adds_caution_to_every_candidate`,
  `test_focus_count_sentence_matches_candidate_count`); extended
  `test_candidates_empty_reason_when_nothing_qualifies` to assert the new text names only leadership;
  added three new tests:
  `test_hpe_shape_row_clears_floor_never_below_selection_floor_and_carries_caution` (TC-2/TC-5/TC-9),
  `test_disposition_predicate_holds_for_every_comparison_cohort_row` (per-row predicate),
  `test_perturbing_advisory_qualifiers_leaves_hashes_membership_and_dispositions_unchanged` (TC-4/TC-15
  counter-test: hashes + candidate list + comparison_cohort + shadow cohort all unchanged when
  entry_min_score/risk_max_score are perturbed).
- `apps/backend/tests/test_manifest_invariants.py` -- `_mk_result` gained optional `e_score`/`e_bucket`/
  `r_score`/`r_bucket` params (defaults preserve every existing call site); added
  `test_tc24_leadership_min_score_is_the_only_gate_regardless_of_qualifiers` (an above-floor row failing
  both qualifiers is never `below_selection_floor`; a below-floor row clearing both qualifiers still is).
- `apps/backend/tests/test_api_compass.py` -- added `compass_engine_two_candidates` fixture (AAA +
  HPE-shape row) and `test_candidate_count_agrees_across_selection_and_narrative_focus_sentence` (TC-8:
  `selection.candidates` length agrees with the narrative's `focus_count` fact and text at the served
  response layer; also proves HPE is a served candidate, not a `comparison_cohort` row).
- `docs/handoffs/goal-market-compass-iter-35-dev.md` -- this handoff.

No database migration; no schema-file change (`selection_disposition`'s closed vocabulary stays exactly
`below_selection_floor` | `excluded_by_cap`; `docs/handoffs/trendora-next-session-manifest-v1.schema.json`
places no item schema on `candidates`/`why_not`, so the new `"gating"` checklist field needed no schema
edit -- confirmed by re-running TC-25's `jsonschema.validate` tests, and separately by validating the
live regenerated v8 document against the committed schema).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_compass.py -q`
Result: **40 passed** (37 pre-existing unchanged in intent + 3 new).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_manifest_invariants.py -q`
Result: **53 passed** (52 pre-existing + 1 new).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_api_compass.py -q`
Result: **18 passed** (17 pre-existing + 1 new).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_compass.py tests/test_manifest_invariants.py tests/test_api_compass.py tests/test_engine_identity.py tests/test_methodology.py tests/test_j11_avb_diagnostic.py -q`
Result: **171 passed** — combined run, confirming no cross-file regressions. `test_engine_identity.py`/
`test_methodology.py` reference `compass.selection.*` config paths generically (never a hardcoded
`"v1"` literal) — unaffected by the rule_version bump. `test_j11_avb_diagnostic.py` imports
`_qualifier_checks` directly (a historical J-11 diagnostic module, out of this iteration's scope) and
only reads the `"passed"` key — unaffected by the new `"gating"` key.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_no_magic_numbers.py -q`
Result: **1 passed, 1 failed** — the failure lists only `indicators.py`, `forward_testing.py`,
`research.py` (float literals `0.5`/`0.95`/`45.0`/`0.9`/`0.0`), none of which this iteration touches.
`compass.py` is NOT among the offenders. Pre-existing and unrelated (confirmed by file list alone,
matching the pattern this session's prior iterations have already recorded as out-of-scope).

## Live production verification (real committed-seed DB, not a synthetic fixture)

Started the backend via `scripts/start-backend.sh` (resolved port 8255), confirmed `/api/health` 200,
then:

1. **`GET /api/compass`** (no `asof`, frontier `2026-08-12`) served the EXISTING stored v7 manifest
   unchanged (create-once-on-GET never recomputes a stored row) — `candidates: 0`,
   `disposition_tally: {below_selection_floor: 539, excluded_by_cap: 0}`, 37/539 still mislabeled. This
   is the CORRECT, expected behavior (AG-12/AG-17): a code/config change alone mints nothing and never
   touches an existing row.
2. **`POST /api/compass/regenerate?as_of=2026-08-12&confirm=true`** (the existing iter-3/J-05-J-06
   confirm-gated action; a UI control for this already exists in `compass-manifest-strip.tsx`, so this
   is the same live action `demo.sh --session-live`/browser-QA will exercise) minted a NEW version:
   - `version: 8`, `mode: at_ingest`, `frozen: true`, `prospective_eligible: false` (correct —
     `_derive_prospective_eligible` is write-once-eligible only for `producer == "ingest_finalize"`
     version 1; `regenerate` is never eligible, matching the existing
     `test_regenerate_on_frontier_yields_state_band_and_prospective_eligible_false` precedent).
   - **`candidates: 10`** (was 0); **`disposition_tally: {below_selection_floor: 502, excluded_by_cap:
     27}`**; `502 + 27 + 10 = 539` = member_count — matches the goal file's own predicted measured
     partition ("502 + 27 + 10 = 539") EXACTLY (TC-3).
   - **Zero mislabeled rows**: 0 of 539 `comparison_cohort` rows have `leadership_score >= 80.0` AND
     `selection_disposition == "below_selection_floor"` (was 37) — TC-2 / TC-9.
   - **HPE is now a candidate** (`leadership_score: 92.71, entry_quality_score: 21.54, risk_score:
     58.85`), checklist shows `entry_min_score` verdict `Miss`, `gating: false`; `reasons` contains only
     the leadership and risk "clears" statements (no false entry-clears claim); `cautions` includes
     `"ENTRY_QUALITY_QUALIFIER: Entry Quality score 21.5 is below the 70.0 qualifier (Weak entry) --
     advisory only; Leadership alone determines candidacy."` — TC-5.
   - `near_threshold_shadow`: **25 rows in both v7 and v8, identical membership** — TC-10 (shadow
     semantics untouched by this journey).
   - `candidate_rule_hash` and `cohort_rule_hash` both changed v7 -> v8 (expected: `rule_version` is in
     both hash scopes) — TC-23-style separation confirmed live, not just in the synthetic unit tests.
   - `generation.engine_identity` changed v7 -> v8 (expected and disclosed per J-12 step 8:
     `provenance.config_keys` includes `compass.selection` and `provenance.engine_files` hashes
     `compass.py`, so the rule_version bump + code edit legitimately move engine identity on NEWLY
     created manifests/runs — never a backfill or re-stamp of existing rows).
   - The v8 document validates against `docs/handoffs/trendora-next-session-manifest-v1.schema.json`
     (`jsonschema.validate`, no error) and its `manifest_hash` verifies
     (`compass.verify_manifest_hash(...) is True`).
3. **AG-12/AG-17 byte-identity proof (TC-11/TC-12), all 28 pre-existing rows, all 7 pre-existing export
   files:**
   - Before touching anything, captured a combined checksum of every stored manifest row's
     `(as_of, version, content_hash, manifest_hash)` ordered by `(as_of, version)`: **28 rows**, md5
     `ffdbdf1273afb81478d6e4c84a0525ba` (read-only `sqlite3 "file:...?mode=ro"` query — never opened the
     8 GB DB for write, never copied it, per project-template.md's binding constraint).
   - After the regenerate action, re-ran the SAME query EXCLUDING the new `(2026-08-12, 8)` row: **28
     rows**, md5 `ffdbdf1273afb81478d6e4c84a0525ba` — **identical**. The DB now has exactly 29 rows
     (28 + the one new v8).
   - `2026-08-12_v7.json`'s export file md5 (`d905dcfeb7883d86602d64d4c24682ad`) is unchanged before and
     after; `apps/backend/data/exports/next_session_manifests/` gained exactly one new file
     (`2026-08-12_v8.json`); the other 6 export files were not touched (`git status --porcelain` on the
     gitignored exports dir shows nothing, and directory listing/timestamps confirm no other file's
     mtime moved).
   - Stopped the backend (`pkill -f "uvicorn main:app"`), confirmed via `ps aux` that no
     `uvicorn`/`start-backend.sh` process remains.

Frontend Present: **no** for this iteration (per the iter spec's Goal Mode Metadata) — no frontend
start/build was run; no frontend file was touched.

## Anti-goal checks (explicit, per Definition of Done)

- **AG-1** (proven-language gating): unaffected — this journey touches no evidence-ledger or
  proven/not-yet-proven surface. `_scan_selection_language` (unchanged) still scans every candidate
  reason/caution/invalidation/why-not string for banned language BEFORE `evaluate_selection` returns
  (`test_selection_language_scan_covers_candidate_and_why_not_strings` still passes); the new
  ENTRY_QUALITY_QUALIFIER/RISK_QUALIFIER caution strings were manually checked against
  `compass.vocabulary.banned_terms` and contain none of them.
- **AG-2** (decision-quality only): candidate framing unchanged — "worth monitoring" language and the
  fixed reason/caution namespace are the only vocabulary touched; no return promise, price target,
  buy/sell signal, or order action was introduced. The new caution text is fact-only ("is below the X
  qualifier ... advisory only"), mirroring the existing ATR_RISK_BUDGET caution's fact-only posture
  (TC-34 precedent) — no advice-sounding tail.
- **AG-3** (displayed numbers must be correct): verified live against the real engine computation for
  the same as-of date (2026-08-12) — see "Live production verification" above; every count/hash was
  read back from the actual served/stored document, not asserted from memory.
- **AG-11** (no new composite candidate number): no new field was added to a candidate payload beyond
  the existing three scores/buckets, the existing word maps, and a `"gating"` BOOLEAN tag on the
  existing checklist rows (a classification of an existing field, not a new number); `_qualifier_checks`
  and `_candidate_payload` were both re-run through `test_no_composite_score_field_anywhere` (still
  passes — asserts `numeric_keys <= {leadership_score, entry_quality_score, risk_score}` on every
  candidate).
- **AG-12** (manifest immutability): proven live, not just asserted — see the byte-identity proof above
  (28/28 pre-existing rows and their export files unchanged; exactly one new version row/file minted by
  an explicit confirm-gated action, never by the code/config change alone).
- **AG-15** (no outcome-tuned selection): confirmed no threshold VALUE changed (`leadership_min_score`,
  `entry_min_score`, `risk_max_score`, `max_candidates`, `why_not_floor`, `why_not_cap`,
  `shadow.min_score` are all byte-identical to before in `config.yaml`) — only which checks GATE vs.
  ANNOTATE changed, and that change was read directly off the goal file's own already-declared rule and
  `config.yaml`'s own pre-existing comment, never derived from realized forward returns. No Evidence
  Claim is introduced.
- **AG-16** (cohorts are not controls): `comparison_cohort`'s definition text and
  `caveats.cohort_semantics` were not touched by this change; no candidate-vs-cohort comparison was
  presented as causal or as expectancy anywhere in this diff.
- **AG-17** (repair never rewrites provenance): the pre-fix mislabeled `2026-08-12_v7` version's stored
  `selection_disposition` values and `prospective_eligible` classification are proven unchanged (byte
  md5-identical file, byte-identical DB row) — the correction appears ONLY in v8, minted strictly after
  the `rule_version` bump.

No anti-goal violation found. No conflict between the documented rule and any anti-goal or any
currently-passing journey was encountered during implementation, so the "STOP and surface for owner
review" clause in J-12's own Acceptance text was never triggered.

## Known Issues

1. `test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` fails on 3 pre-existing,
   unrelated files (`indicators.py`, `forward_testing.py`, `research.py`) — confirmed NOT caused by this
   iteration (none of those files were touched; `compass.py` is not among the reported offenders). Not
   fixed here (out of scope — this iteration is confined to `compass.py` + `config.yaml` + the three
   named test files).
2. This iteration deliberately did **not** modify `docs/handoffs/trendora-next-session-manifest-v1
   .schema.json` — the schema places no item constraints on `selection.candidates`/`selection.why_not`
   rows, so the new `"gating"` checklist field is schema-safe without a version bump (confirmed by
   `jsonschema.validate` on both a synthetic fixture and the real regenerated v8 document).
3. J-13 (Leadership rotation duplication/direction/completeness) is a separate journey, explicitly out
   of scope this iteration, and was not started.
4. The pre-existing mislabeled `2026-08-12_v7` manifest remains readable and displayable exactly as
   frozen — a historical/as-of view of `2026-08-12` reading v7 (rather than the newly minted v8) will
   still show the old, mislabeled dispositions, by design (AG-12/AG-17: correction applies only to
   manifests minted after the rule_version bump, never by relabeling a frozen row). If the product wants
   the FRONTIER's default view to show the corrected v8 immediately (rather than requiring a manual
   regenerate action or waiting for a fresh ingest finalize past this frontier), that is an owner/product
   decision outside this iteration's scope — `GET /api/compass` already serves whichever version is
   LATEST for that as_of (`latest_manifest_for_date`), so once v8 exists (as it now does, from this
   session's live verification) it is what a fresh `GET /api/compass?as_of=2026-08-12` call will return.

## Pre-handoff verification

- **Service startup:** `scripts/start-backend.sh` started cleanly (port 8255, `/api/health` 200 within
  1s), served the live verification calls above, then was stopped cleanly (`pkill -f "uvicorn
  main:app"`; confirmed no stray process via `ps aux`). Frontend was not started (Frontend Present: no
  for this iteration; no frontend file touched).
- **External integrations:** N/A — no new adapter/scraper/external API; the only live calls were local
  HTTP requests to the already-running backend against the committed offline seed DB (AG-9 unaffected).
- **Native dependency binaries:** N/A — no new dependency was added.

## Handoff to reviewer

Scope is confined exactly to the IN SCOPE list: one engine module (`compass.py`), one config value
(`compass.selection.rule_version`), and the three named test files. No frontend file was touched; no
schema file was touched; no threshold VALUE changed; no existing manifest row/export file was mutated.
Live verification against the real committed-seed DB (not just synthetic fixtures) confirms the fix
behaves exactly as J-12's Acceptance text and TC-1..TC-13 describe, including the exact numeric
partition (502 + 27 + 10 = 539) the goal file predicted.
