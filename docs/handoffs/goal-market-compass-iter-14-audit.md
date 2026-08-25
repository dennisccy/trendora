# goal-market-compass-iter-14 Audit Report

**Date:** 2026-08-25
**Auditor:** Hard audit pass — skeptical, evidence-based
**Phase:** goal-market-compass-iter-14 (J-11 Stage D readiness hardening)
**Mode:** maintenance isolation ACTIVE — no service boot, no browser, no replay, no network, no Stage C/D
execution, no regeneration. Every live database access below used a `mode=ro` + `PRAGMA query_only=ON`
handle. **Live DB writes this audit: ZERO** (proven at the end of §7).

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration delivered all five Stage D preconditions and I re-derived every load-bearing claim
independently rather than accepting any lane's word: the frozen attempt identity is genuinely recomputed
(not hardcoded), the three identity checks are genuine fail-closed COMPARE call sites, all eleven Stage D
preflight checks pass against the live database *and* every one of them genuinely fires on drift (I
exercised all eleven negative branches myself), the iteration-13 evidence-corruption fix is real and the
corrected handoff is an honest retraction rather than a rewording, and zero live writes are proven four
independent ways. Three gaps remain and are documented, none of which compromises the phase goal: the AVB
diagnostic proves only the *close* half of the convention it declares proven (I closed the volume half
from the provider source and a pool-wide check — the AVB-B classification stands, but on audit evidence,
not on the artifact's own); the iteration's headline verdict artifact `j11-stage-d-readiness.json` has no
committed producer; and nine of the eleven Stage D gate checks carry no committed negative test.

**`J-11 STAGE D READY: YES`** — I concur, qualified (see §5).
**`J-11 STAGE D AUTHORIZED: NO`** — I concur, unconditionally (see §5).

---

## 2. DEFINITION OF DONE — verification

Risk-ranked per the auditor protocol. Every item below involves data mutation, provenance, or a gate that
guards a future destructive operation, so **every item got the full code trace**; the reviewer/QA
citations are recorded as corroboration, not as substitutes.

| # | DoD item | Result | How I verified it |
|---|---|---|---|
| 1 | Fresh attempt identity, recomputed live, all required fields (TC-1) | **MET** | Read `j11_stage_d.freeze_stage_d_attempt_identity:94-141`; ran `compute_engine_identity(load_config())` myself — returns `53d2ffd10cdb…f6c55`, **byte-identical** to the artifact's `engine_identity`, and not `6261ca17…`. Re-derived `j11_contract_hash` from today's `docs/goal.md` → `2dd97124…ae3f3` (matches). `git_head` `1b869561…` == current HEAD. All required fields present. `engine_identity.compute_engine_identity` is **not** memoized (reads `provenance.engine_files` off disk each call), so the recompute is a real second read, not a cached echo. |
| 2 | Three fail-closed identity checks are genuine COMPAREs (TC-2..7 / TC-ID-1..6) | **MET** (caveat F1) | Read all three (`j11_stage_d.py:149-217`); each delegates to `j11_maintenance.check_attempt_identity_consistency:231-241`, whose body is `run_identity is not None and run_identity == expected` — genuinely fail-closed on NULL. **Executed** Check (C) myself: NULL identity on an in-scope date → `ok: False, in_scope: True`. Each returns a per-call record, never an aggregate. |
| 3 | Stage D preflight built, executed read-only, proves all 6 things (TC-8..13) | **MET** | `j11-stage-d-preflight-gate.json` shows 11/11 `true`, `verdict.passed: true`. I re-derived every baseline from the live DB myself: 11 incident dates → **0** `scanner_runs`; `daily_prices` 3,310,374; manifests 24 rows, DDL sha256 `9f653c81…c501ee`, full-row sha256 `bb954b60…6d2a2e6`; `data_provider_runs` 549; `watchlist` 6; 34 runs stamped `6261ca17…`; 3,083 NULL-stamped; **0** runs stamped `53d2ffd1…` (confirming nothing was restamped). |
| 4 | Every genuinely-missing negative test added (TC-14..19) | **MET** (caveat T1) | Read the diff: 7 new tests in `test_j11_stage_c_preflight.py`, 4 in the new `test_j11_stage_c_cli_script.py`, 2 Stage-D-specific in `test_j11_stage_d.py`. Re-ran the targeted 7-file suite myself: **92 passed, 0 failed in 3.90s**. |
| 5 | AVB diagnostic: re-derives factor, classifies convention *from the stored series*, 3 representations, decision-impact trace, exactly one of A/B/C/D | **PARTIAL** | See **B1**/**B2**. Factor, pairs, representations, and the decision trace are all correct and genuinely derived; the *convention classifier* never reads volume, and one of the four labels is unreachable. |
| 6 | `J-11 STAGE D READY: YES/NO` recorded, AVB-C/D forces NO, `AUTHORIZED: NO` unconditional (TC-25) | **MET** (caveat B3) | `stage_d_readiness_verdict:393-418` — `authorized: False` is a **literal**, not derived from any input, so no branch can self-authorize; parametrized test covers all 6 (classification × gate) combinations; unknown classification raises. |
| 7 | Zero writes proven via TRUE-start/TRUE-end mtime + WAL (TC-26) | **MET** | Four independent captures (preflight start/end, AVB `zero_write_proof` start/end) all record mtime `1787591622.4277432` / size `8365871104` / WAL 0. I `stat`-ed the file myself before and after *all* of my own reads and the 92-test suite run: unchanged. |
| 8 | No anti-goal violation; AG-9's exhausted boundary not crossed | **MET** | No network call in any new module: `j11_avb_diagnostic` reads the committed `runs/goal-market-compass-iter-9/j10-population-evidence.json` and `daily_prices` only; no `j10_recovery` function is imported or called anywhere in the new code (grep-verified). Column-projected selects only (`fetch_avb_stored_series:126-131`) — AG-8 respected. `_BridgeApplyingProvider` is never touched. |
| 9 | Fixture-only tests; live DB never a fixture; no concurrent pytest | **MET** | Every test engine is `create_engine("sqlite://")`. The only non-fixture reads are two AVB tests against the committed J-10 evidence JSON — disclosed in that file's own docstring, and not the database. I ran exactly one pytest process. |
| 10 | All new code, tests, and evidence artifacts committed to git | **NOT MET (pending)** | `git status` shows every new module, test, script, and all seven `runs/goal-market-compass-iter-14/*.json` artifacts **untracked**; `git ls-files runs/goal-market-compass-iter-14` returns 0. Consistent with this session's pattern of committing at iteration close, so I treat it as pending rather than failed — but see **B5** for why it is not merely cosmetic here. |
| 11 | Dev handoff written | **MET** | `docs/handoffs/goal-market-compass-iter-14-dev.md`, cites every artifact, closes with both literal lines. |

---

## 3. Findings

### Backend Findings

**B1 — IMPORTANT (gap, not fixed): the AVB convention classifier never reads volume, and `bridged+compensating` is unreachable — the artifact declares proven what it never tested.**

`apps/backend/app/engine/j11_avb_diagnostic.py:159-267` (`classify_local_convention`). The whole point of
this diagnostic is a **price/volume** scale mismatch, yet the classifier's only inputs are closes: the
calibration window compares `stored["close"] / pair["fallback_close"]` (line 189), and both other windows
are classified purely by `_day_over_day_returns` (line 146-156), which reads `cur["close"]` and nothing
else. `fetch_avb_stored_series` computes `close_times_volume` for every row (line 139-141) and no code
path ever consumes it.

Consequences, all three real:

1. **The label `bridged+compensating` is structurally unreachable.** It appears exactly once in the whole
   module — in the docstring at line 174. The only values `classify_local_convention` can emit are
   `bridged+raw`, `raw+raw`, and `mixed/indeterminate`. The spec's four-way vocabulary (TC-21, Goal 4) is
   in practice a three-way one, and the missing branch is precisely the one that would flag a **volume**
   convention problem.
2. **The spec's per-window record is incomplete.** Goal 4 requires, verbatim, "for each window, close,
   volume, close×volume, and … the ratio". The persisted artifact carries close+ratio for the calibration
   window, nothing but `boundary_jumps` for the recovered window, nothing for the surrounding window;
   volume and close×volume appear only for the two recovered dates, via the representations block.
3. **The classification reasoning overstates its own evidence.** The committed
   `j11-avb-bridge-diagnostic.json` reads: *"the canonical stored convention (**bridged close,
   untransformed volume**) is proven internally consistent across AVB's own stored series"*. Only the
   close half was tested. `volume_a_equals_b: true` (line 314) is a **tautology** — `volume_b` is assigned
   `stored_volume` at line 288 — so it confirms nothing about J-10's behaviour, though the handoff cites
   it as "confirms J-10 never transformed volume".

**I closed the gap independently, and the conclusion survives.** The volume half is true, but the proof
lives outside this iteration's artifacts:

- `apps/backend/app/engine/j10_recovery.py:833-836` — `_BridgeApplyingProvider.get_daily` builds
  `Bar(date=…, open=b.open * factor, high=…, low=…, close=b.close * factor, **volume=b.volume**)`.
  The factor is applied to OHLC only; volume passes through unscaled. There is no code path that could
  have produced a compensating volume.
- `apps/backend/app/data_providers/yahoo_provider.py:351-369` — the fetch path reads the raw
  `indicators.quote` block (`quote["close"]`, `quote["volume"]`). The bridge factor was calibrated
  against a *different* series, `indicators.adjclose` (`get_adjusted_close`, lines 104-179), which
  carries no volume at all. So no adjustment-scaled volume can enter the database by construction.
- **Pool-wide empirical check (mine, read-only).** For all 582 symbols with rows in
  2026-07-13..2026-08-12, the ratio of recovered-date volume to that symbol's trailing median is
  **normal**: median 0.817 on 2026-08-11 and 0.848 on 2026-08-12 (p10-p90 ≈ 0.58-1.32). Only 9 of 582
  exceed 2.0× on 08-11 and 11 of 582 on 08-12. A systematic provider-side volume convention shift would
  have moved the whole pool; it did not.

Verdict on the classification: **`bridged+raw` → AVB-B is correct.** But it is correct on evidence this
audit supplied, not on the evidence the committed artifact presents.

**Not fixed, deliberately.** A real fix means feeding volume into `classify_local_convention`, making the
fourth branch reachable, persisting the per-window volume/close×volume table — and then **re-running the
live diagnostic**, which performs two full `score_stocks` passes against the 8.4 GB database. Maintenance
isolation, the coordinator's explicit "no regeneration", and AG-10's host-resource ceiling all forbid me
launching that. A code-only fix would be worse than none: it would leave the committed artifact no longer
reproducible from the committed code, which is exactly the provenance discipline this session exists to
enforce. Recommended as a precondition of Stage D authorization instead (§5).

**B2 — GAP (not fixed): the diagnostic fetched the stored series' most extreme datum and never looked at it.**

`j11_avb_diagnostic.py:120-143` fetches AVB's 50-row stored series and computes `close_times_volume` per
row; nothing examines it. Re-derived by me, read-only:

| Date | stored close | stored volume | close × volume |
|---|---|---|---|
| 2026-08-05..08-10 (calibration, never deleted) | 183.84-189.61 | 451k-666k | ~$83M-$125M |
| **2026-08-11** (recovered) | 181.76 | **1,549,436** (2.36× trailing median) | $281.6M |
| **2026-08-12** (recovered) | 179.79 | **10,350,885** (15.76× trailing median) | **$1,860,985,686** |

AVB's 2026-08-12 volume is its **3rd-highest in 5,397 rows of history** (21 years; 99.94th percentile,
behind only 2012-11-29 and 2009-03-10) and the **single largest volume ratio of all 582 pool symbols on
that date**. It lands on one of the two dates J-10 restored, for the one symbol out of 566 with a
materially non-unit bridge factor. The diagnostic never surfaces it.

**Decision impact is small, which is why this is a GAP and not IMPORTANT.** From
`j11-avb-bridge-diagnostic.json`'s own trace: the day lifts the 63-day ADV from $187.6M (08-11) to
$215.0M (08-12) — still far above the $50M `min_dollar_vol` floor; `admitted` stays True, `risk_bucket`
stays E, `setup_status` stays Avoid, `eligible` stays False on both dates and under both representations.
No Stage D decision changes. But iteration 9's own standing lesson — quoted in this iteration's own spec —
is *"a summary statistic of the form 'all N were X' is exactly where the single counter-example gets
erased"*, and this is that counter-example, in the series the module itself fetched.

**B3 — IMPORTANT (gap, not fixed): `j11-stage-d-readiness.json`, the iteration's headline verdict artifact, has no committed producer.**

`grep -rn "j11-stage-d-readiness\|stage_d_readiness_verdict" --include=*.py apps/ scripts/` returns
exactly three hits: the function definition (`j11_stage_d.py:393`) and two call sites, both in
`tests/test_j11_stage_d.py:333,340`. **No script writes this file.** Compare the other four artifacts,
each of which has a named producer (`run_j11_stage_d_preflight.py` writes the identity, preflight, and
gate; `run_j11_avb_bridge_diagnostic.py` writes the diagnostic).

The file's own content confirms it was hand-authored: it carries an `inputs` block (naming the two source
artifacts and the three test files) that `stage_d_readiness_verdict` does not emit — that function returns
only `generated_at`, `ready`, `preflight_gate_passed`, `preflight_gate_reason`, `avb_classification`,
`blocking_reasons`, `authorized`. Its `generated_at` (22:05:04Z) also matches the mtime of
`j11-stage-d-db-file-true-end.json`, so the same unrecorded ad-hoc command appears to have produced the
final zero-write end-capture too.

**The values are correct** — I checked each against its source: `preflight_gate_passed: true` /
`reason: "all_checks_passed"` match `j11-stage-d-preflight-gate.json`; `avb_classification: "AVB-B"`
matches the diagnostic's `classification.classification`; `blocking_reasons: []` and `authorized: false`
are what `stage_d_readiness_verdict` would return for that pair. So nothing is wrong today. What is
missing is any mechanism that would *keep* it right: a future readiness artifact could be hand-written
with `ready: true` while the gate said otherwise, and no committed code would object.

*I was genuinely unsure between IMPORTANT and GAP here — the spec asks only that the reasoning be
"persisted", never that a script persist it — and took the higher rating per the severity rule. It does
not block, because every input value is independently re-derived above.* Not fixed: writing a producer
script now would require re-running it to be meaningful, which would overwrite evidence generated during
the iteration (the coordinator's "no regeneration" constraint).

**B4 — GAP (not fixed): nine of the eleven Stage D gate checks have no committed negative test; I verified them by hand instead.**

`compare_stage_d_preflight_to_certified` (`j11_stage_d.py:317-373`) **duplicates** nine of
`j11_stage_c.compare_preflight_to_certified`'s comparison expressions rather than reusing them (compare
`j11_stage_d.py:333-353` against `j11_stage_c.py:276-308` — the DDL, index, `diff_dumps`, `source_run_id`,
provider-runs and watchlist expressions are line-for-line equivalents against a differently-shaped
baseline). The seven new negative tests (TC-14..18) exercise the **Stage C** function only;
`test_j11_stage_d.py` negative-tests just two of the Stage D gate's checks
(`daily_prices_fingerprint_unchanged`, `all_incident_dates_zero_scanner_runs`).

This is spec-conformant — Goal 3b explicitly assigns TC-14..18 to `compare_preflight_to_certified` — but
it leaves the gate that will actually guard Stage D's destructive regeneration with nine untested
branches, in an iteration whose stated purpose was closing exactly that class of hole ("a gate that cannot
compare is a gate that always passes").

**I exercised all eleven branches myself** against synthetic preflight/certified dicts, perturbing one
field at a time. Every one flips its own named check to `False` and sets `material_mismatch: True`:
`daily_prices_fingerprint_unchanged`, `manifest_row_count_unchanged`, `manifest_ddl_unchanged`,
`manifest_indexes_unchanged` (via both `index_names` and `index_sqls`), `manifest_values_unchanged`,
`source_run_id_values_unchanged`, `data_provider_runs_count_unchanged`, `watchlist_count_unchanged`,
`c1_date_set_boundary_ok`, `all_incident_dates_zero_scanner_runs`, `identity_check_a_ok`. **The gate is
correct; only its regression coverage is missing.** Recommended: port TC-14..18 to the Stage D comparator
before Stage D runs, or collapse the duplication so the existing tests cover both.

**B5 — GAP (correctly deferred, with a sharper reason than the one recorded): the `--evidence-dir` footgun survives in four more scripts, and iteration-14's own evidence is the *least* recoverable target.**

I concur with the developer and reviewer that
`apps/backend/scripts/run_j11_stage_d_preflight.py:49,86` (`DEFAULT_EVIDENCE_DIR` → an argparse default)
is correctly **deferred**, not a blocker: I confirmed by grep that no file under `apps/backend/tests/`
references that script at all, its `main()` is `__main__`-guarded, and unlike the Stage C script it is
read-only (`mode=ro` + `PRAGMA query_only=ON`), so its worst case is clobbering JSON, never the database.

But the framing in the handoff and review — "currently inert, nothing is corrupting anything now" —
understates the stakes in one specific way. The full inventory of the surviving pattern:

| Script | Default target | Committed? |
|---|---|---|
| `run_j11_stage_d_preflight.py:86` | `runs/goal-market-compass-iter-14/` | **NO — 0 tracked files** |
| `run_j11_avb_bridge_diagnostic.py:73` | `runs/goal-market-compass-iter-14/j11-avb-bridge-diagnostic.json` | **NO** |
| `run_j11_stage_b1_manifest_schema_migration.py:69` | `runs/goal-market-compass-iter-11/` | yes (14 files) |
| `run_j11_pre_reset_inventory.py:91-92` | `runs/goal-market-compass-iter-10/` | yes (7 files) |

The iteration-13 corruption was survivable **only because those files were committed** — the recovery was
`git checkout HEAD -- …`. `runs/goal-market-compass-iter-14/` has **zero tracked files** (DoD item 10),
and two of this iteration's own scripts write into it by default. The same accident today would be
**unrecoverable**, including the 6.2 MB `j11-stage-d-preflight.json` and the AVB diagnostic, neither of
which can be regenerated without another live pass. Note also that `run_j11_avb_bridge_diagnostic.py`'s
default was flagged by the reviewer only conditionally ("if it has an evidence-writing default") and never
confirmed by anyone — it does have one. **The cheap mitigation is not the code guard, it is committing
`runs/goal-market-compass-iter-14/`**, which the DoD already requires.

**B6 — OBSERVATION: a latent both-sides-null escape hatch in the DDL check.**
`j11_stage_d.py:333-335` compares `preflight[…]["table_sql"] or ""` against `certified[…]["table_sql"] or
""`, so two `None` DDLs (a dropped `next_session_manifests` table) compare equal and the check passes. I
confirmed this by execution. Fully subsumed in practice by `manifest_row_count_unchanged` (0 vs 24) and
`manifest_values_unchanged`, so no real exposure. Inherited verbatim from `j11_stage_c.py:276-277`.

**B7 — OBSERVATION: the out-of-scope vacuous pass returns `ok: True`, not a distinct "skipped" state.**
`check_identity_before_date` / `check_identity_after_persist` (`j11_stage_d.py:169-177, 197-206`) return
`{"in_scope": False, "ok": True}` for any date outside `INCIDENT_DATES`. This is exactly what TC-ID-6
mandates for the 34 surviving runs, and I verified the discrimination works (NULL identity on an
out-of-scope date → `ok: True, in_scope: False`; on an in-scope date → `ok: False`). The residual risk is
narrow but worth writing down: a future Stage D loop that aggregates `all(r["ok"] …)` without also
asserting `r["in_scope"]` would silently accept a run persisted on the *wrong* date. Consider returning
`ok: None` / an explicit `skipped` state when Stage D is wired up.

### Frontend Findings

None — no frontend file is touched, no service booted, no surface rendered (correct under maintenance
isolation, ruling A5/A13). Confirmed against `git status`: nothing under `apps/frontend/`.

### Test Findings

**T1 — GAP: coverage asymmetry (detailed in B4).** Nine of eleven Stage D gate branches untested in the
committed suite.

**Test quality otherwise: PASS, and better than the norm.** I looked specifically for tests that pass by
accident and did not find any:

- `test_classify_local_convention_detects_a_discontinuity_at_the_recovery_boundary`
  (`test_j11_avb_diagnostic.py:128-148`) injects a genuine ~2.79×-scale break at 2026-08-11 and asserts
  the classifier catches it — the classifier is not vacuous, it just never sees volume.
- `test_trace_universe_resolver_impact_detects_admission_change_when_b_crosses_the_floor` (lines 216-240)
  places `min_dollar_vol` precisely between A's and B's ADV and asserts the admission genuinely flips —
  this is the right way to prove a gate reacts rather than carrying a static value.
- `test_tc1_freeze_stage_d_attempt_identity_is_fresh_never_hardcoded` (lines 86-106) asserts equality
  against an *independent* `compute_engine_identity` call rather than a literal — correct, and the
  literal-avoidance is itself the point of TC-1.
- The CLI guard test patches `_write_json`, `get_engine`, `Session`, `db_file_fingerprint` **and**
  `clear_snapshot_dates` and asserts all five uncalled — a real assertion set, not a smoke test.

Assertions are tight (exact values, `pytest.approx` only where floats demand it). Fixtures use synthetic
`sqlite://` engines throughout; the two tests that read the committed J-10 evidence JSON disclose it in
the module docstring.

---

## 4. The three things the coordinator asked me to satisfy myself about

### 4.1 Is the iteration-13 evidence-corruption fix real?

**Yes — verified by source-order reading and by execution, not by the tests' mocks.**

The guard in `run_j11_stage_c_bounded_clear.py:109-117` (`if args.evidence_dir is None: … return 2`) sits
at line 109. Everything that could touch the database or the filesystem comes **after** it:
`load_config()` at 121, `resolve_database_url` at 122, `jsc.db_file_fingerprint` at 127, the first
`_write_json` at 128, `get_engine()` at 130. The `--confirm` refusal (100-107) precedes even that. So both
refusals return before any DB contact, as a matter of source order.

The failure paths are equally clean, again by source order: a certified-baseline row-count mismatch returns
at 158, a gate failure at 172, a C1 failure at 183 — **all before** `capture_intended_delete_set` (187) and
`clear_snapshot_dates` (207). A post-delete verification failure returns at 259, **before**
`build_completion_marker` (265) and before `j11-stage-c-complete.json` is written (266). A failed preflight
therefore reaches zero destructive call sites and writes no completion marker.

The offending test now passes `--evidence-dir str(tmp_path / "evidence")`
(`test_j11_stage_c_cli_script.py:160`) and still exercises the genuine gate-failure path
(`all_invariants_hold: False` → `clear_snapshot_dates` asserted un-called), asserting the pre-gate evidence
landed in `tmp_path` and only there — so it is not passing vacuously.

**Empirically re-verified.** I hashed all 52 files across `runs/goal-market-compass-iter-{9,11,12,13,14}`
before and after re-running the targeted 7-file suite (92 passed, 0 failed, 3.90s). Every one is
byte-identical; `git status --porcelain` on iterations 9/11/12/13 is empty; the database's mtime, size, and
0-byte WAL are unchanged.

### 4.2 Is the corrected handoff genuinely honest, or reworded?

**Genuinely honest.** Three independent signals:

1. **The retraction is specific and self-incriminating.** It names the exact test, the exact mechanism
   (argparse fallback to the committed directory), identifies the mocked values (`captured_at:
   "2026-01-01T00:00:00+00:00"`, `generated_at: "x"`, `material_mismatch: true`) as that test's own
   fingerprints, and — the part a rewording would omit — diagnoses its *own prior reasoning error* as a
   sequencing mistake (the 21:54Z preflight ran ten minutes before the 22:05:25Z pytest run). I confirmed
   both the mock values and the timeline against the test source and the artifacts.
2. **The manifest-fingerprint correction, made in the developer's own favour, is true.** I reproduced it:
   `sqlite3` `mode=ro` + `PRAGMA query_only=ON`, `sha256` over `repr(row)` for
   `SELECT * FROM next_session_manifests ORDER BY id` → **`bb954b60187e39a1aa8f59b1bf736be9808e25760d2a0494f176116416d2a2e6`**
   over 24 rows × 28 columns, exactly the cited value. (Both the coordinator's note and the handoff
   abbreviate this as "…a2a2e6"; the true tail is "…6d2a2e6" — a sloppy ellipsis, not a discrepancy. The
   full digests match.) The "method mismatch, not a data discrepancy" framing is correct.
3. **It reports a new defect against itself** (the sibling script's surviving default) rather than quietly
   patching or omitting it, and retains its two genuine limitations (second-order Risk-bucket effects
   unproven; `evaluate_selection` not replayable without a `ScannerRun`). Both limitations are real and I
   confirmed them.

One small inaccuracy, OBSERVATION-level: the handoff attributes `j11-stage-d-db-file-true-start.json` to
"the AVB diagnostic script's own start", but that file records `wal.exists: true` while the AVB artifact's
own embedded `db_file_true_start` records `wal.exists: false` — they are different captures. Immaterial:
the primary instrument (main-file mtime + size) is identical across all four captures and across my own
independent `stat` taken after everything.

### 4.3 Does the same footgun survive elsewhere?

Yes, in four more scripts — full inventory and the recoverability asymmetry in **B5**. The one the other
lanes did not confirm is `run_j11_avb_bridge_diagnostic.py:73`.

---

## 5. Stage D readiness — my own verdict

**`J-11 STAGE D READY: YES` — I concur with the developer, reviewer and QA, with one qualification.**

Every precondition holds on my own re-derivation, not on any lane's report: 11/11 preflight checks pass
against the live database *and* all 11 genuinely fire on drift; the eleven incident dates hold zero
`ScannerRun` rows; canonical inputs and all 24 manifests are byte-identical to iteration 13's certified
baseline; the fresh attempt identity is honestly recomputed and matches a fresh call today; the 11-date
set agrees with both `docs/goal.md` lists; the three identity checks are fail-closed; and the AVB
classification is AVB-B, which does not block.

Two qualifications the owner should read alongside the YES:

1. **AVB-B is correct, but the committed artifact does not prove all of it.** The "untransformed volume"
   half of the convention was established by *this audit* (from `j10_recovery.py:833-836`,
   `yahoo_provider.py:351-369`, and a pool-wide volume check), not by the diagnostic. Taken strictly on
   the artifact's own evidence, the volume convention is untested — which is AVB-D territory, and AVB-D
   forces NO. It is only the audit's external evidence that lands it on AVB-B. **Recommended: close B1
   (volume into the classifier, fourth branch reachable, per-window volume/close×volume persisted) and
   re-run the diagnostic before Stage D is authorized** — this costs nothing on the critical path, since
   Stage D already requires a separate owner instruction.
2. **"READY" means the preconditions hold and the checks exist — not that Stage D will call them.** Per
   Goal 2 the three identity checks are deliberately *built and unit-tested only*; no Stage D runner
   exists yet, so nothing currently guarantees a future regeneration loop invokes A, B and C at the three
   required points. Wiring them in is Stage D's own first obligation, and should be verified explicitly
   when it is authorized (see also B7 on the `ok: True` out-of-scope state).

**`J-11 STAGE D AUTHORIZED: NO` — I concur, unconditionally.** `stage_d_readiness_verdict` sets
`"authorized": False` as a literal at `j11_stage_d.py:417`, reachable from no branch that could set it
otherwise, and the parametrized test asserts it across all six cases. Per the established C10/A12 pattern,
a separate explicit owner instruction is required. Nothing in this iteration executed, started, or
prepared to start Stage D's regeneration: no `scanner.run_scan`, no `persist_run_payload`, no `ScannerRun`
INSERT anywhere in the new code (grep-verified), and the 0 rows stamped `53d2ffd1…` in the live database
independently confirm no run was created under the new attempt identity.

---

## 6. Domain Assessment

The core domain logic is sound and, unusually, composes rather than reimplements. The identity primitive
(`run_identity is not None and run_identity == expected`) is the right shape — fail-closed on NULL, per-run
rather than aggregate — and all three new call sites genuinely delegate to it instead of re-deriving
comparison logic, which is precisely the defect iteration 13's auditor found. `capture_stage_d_preflight`
exercises Check (A) against a **second, independent** `compute_engine_identity(cfg)` call rather than
comparing the artifact to itself; since `compute_engine_identity` is not memoized and re-reads
`provenance.engine_files` from disk on every call, that is a real second measurement, not a no-op.

The AVB decision-impact trace is the strongest piece of work in the iteration and deserves saying so: it
calls the *real* `score_stocks`, `_adv_dollar`, `resolve_candidate`, `_build_score`, `to_bucket`,
`classify_setup` and `_qualifier_checks` rather than reimplementing them, and it carries its own internal
falsifiable cross-check — `liquidity_raw_a_reproduces_served: true` and `percentile_a_reproduces_served:
true` prove the narrower re-derivation reproduces the real served output exactly. The `bar_count` bug the
developer caught while writing the fixture test (defaulting to the `adv_window_days`-bounded list, 63,
instead of AVB's true 5,396-bar history, which flipped `admitted` to the exact opposite of the truth) was a
genuine correctness bug found by a genuine test, and the fix mirrors production's own two-step pattern in
`resolve_with_reasons`. That is the process working.

The one domain weakness is the asymmetry described in B1: a diagnostic built to adjudicate a *price ×
volume* question that adjudicates it on price alone. Its conclusion is right, and I have said so on
independent evidence — but a reader of the artifact would believe more was tested than was.

---

## 7. Fixes Applied During This Audit

**None.** No source file, test, or artifact was modified by this audit.

| Finding | Severity | Why not fixed |
|---|---|---|
| B1 | Important | A real fix requires re-running the live AVB diagnostic (two full `score_stocks` passes over the 8.4 GB database). Forbidden by maintenance isolation, the coordinator's "no regeneration" instruction, and AG-10's host-resource ceiling. A code-only fix would desynchronise the module from the committed artifact — worse than the gap. |
| B3 | Important | Adding a producer script is meaningless without running it, and running it would overwrite evidence generated during the iteration. Documented and recommended instead. |
| B2, B4, B5, B6, B7 | Gap / Observation | Documenting is the correct treatment; fixing would be scope creep. B4's underlying code I verified correct by hand, so the risk is coverage, not behaviour. |

**Zero-write proof for this audit.** Every live access used `sqlite3.connect("file:…?mode=ro", uri=True)`
with `PRAGMA query_only=ON`. Before my first read and after the last (including the 92-test suite run):
`apps/backend/data/trendora.db` mtime `1787591622.4277432`, size `8,365,871,104`, `-wal` size `0` — all
three unchanged, matching iteration 13's Stage C values exactly. All 52 evidence files across
`runs/goal-market-compass-iter-{9,11,12,13,14}` are byte-identical before and after; `git status
--porcelain` on iterations 9/11/12/13 is empty. The database was never opened for write and never copied.

---

## 8. Recommended Next Step

**Proceed — Stage D's preconditions are met and independently re-derived. Do not authorize Stage D on this
report alone.**

Before any Stage D authorization, in priority order:

1. **Commit `runs/goal-market-compass-iter-14/`** and the new modules/tests/scripts (DoD item 10). This is
   both the outstanding DoD item and the cheapest mitigation for B5 — it converts an unrecoverable
   evidence directory into a `git checkout`-recoverable one, which is the only reason iteration 13
   survived the identical accident.
2. **Close B1** — feed volume and close×volume into `classify_local_convention`, make
   `bridged+compensating` reachable, persist the spec's per-window close/volume/close×volume table, and
   re-run the diagnostic under a normal (non-isolated) window. Fold in this audit's provider-source and
   pool-wide evidence so the artifact stands on its own. Also record B2's 2026-08-12 volume outlier as an
   explicit caveat on any Stage D output for that date.
3. **Close B3** — give `j11-stage-d-readiness.json` a committed producer so the headline verdict is
   reproducible from committed code rather than from an unrecorded command.
4. **Close B4** — port TC-14..18 to `compare_stage_d_preflight_to_certified`, or collapse the duplication
   between the two comparators so one test set covers both. Nine branches of the gate that guards a
   destructive operation should not rest on an auditor's ad-hoc script.
5. **Apply the `--evidence-dir` guard** to `run_j11_stage_d_preflight.py` and
   `run_j11_avb_bridge_diagnostic.py` **before** any test is written against either `main()` — the
   trigger condition, not the calendar, is what makes that guard urgent.

When Stage D is authorized, its first obligation is wiring Checks A, B and C into the regeneration loop at
the three points step 12/13 requires, and asserting `in_scope` alongside `ok` at every aggregation point
(B7). Stage D remains **NOT AUTHORIZED**; a separate, explicit owner instruction is required.
