# goal-market-compass-iter-16 Audit Report

**Date:** 2026-08-25
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The owner-ordered sequence executed correctly and in order. I re-derived the entire mutation-isolation
proof independently — raw `sqlite3` (`mode=ro` + `PRAGMA query_only=ON`), no project imports — and every
figure holds: all three isolating hashes are byte-identical to the coordinator's pre-resume true-start
capture, every table count matches, and the two AVB rows carry exactly `round(provider_volume /
bridge_factor)` with OHLC untouched. `J-11 STAGE D READY: YES` is **correct** — my own independent
recompute of the classifier's inputs rules out AVB-C and AVB-D — and `AUTHORIZED: NO` is unconditional
in code.

Two IMPORTANT gaps remain, neither of which flips the gate and neither of which I could fix inside this
iteration's authorization: the pre-boot guard is **inert against the live database** (it is built, wired
and proven, but no boundary is registered there, so booting the backend still re-arms the exact trap the
owner ruling exists to prevent), and the Stage-D decision-impact trace ran with a **scale-inconsistent
representation B**, so the "material signal" that separates AVB-B from AVB-A — and the causal claim built
on it in the dev handoff — is an artifact rather than a finding.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap): the decision-impact trace's representation B is scale-inconsistent after the correction; the AVB-B "material signal" is an artifact, and the handoff's causal claim about it is unsupported.**

`apps/backend/scripts/run_j11_iter16_stage_d_readiness.py:247-248` calls
`trace_universe_resolver_impact` / `trace_scoring_and_selection_impact` **without** `volume_override`.
Both funnel into `apps/backend/app/engine/j11_avb_diagnostic.py:629-654`
(`_build_bars_with_transformed_close`), which — with no override — substitutes **close only**
(`close / bridge_factor`) and passes volume straight through from the stored bars.

Before this iteration that was coherent: A was `bridged close × RAW volume`, B was
`provider close × provider volume`. After the write, the stored volume is on the *compensating* scale,
so B is now `provider-scale close × Trendora-scale volume` — a hybrid that exists in no representation
of reality.

I measured it directly from the live corrected rows and iteration-15's provider evidence:

| date | A (stored close × stored volume) | B **as actually run** | A/B | B **with the fetched volume** | A/B |
|---|---|---|---|---|---|
| 2026-08-11 | 100,832,640.51 | 36,101,910.52 | **2.7930001226** | 100,832,616.50 | 1.0000002382 |
| 2026-08-12 | 666,303,563.75 | 238,561,952.92 | **2.7930001226** | 666,303,474.64 | 1.0000001337 |

The as-run A/B ratio is *exactly* `bridge_factor` on both dates — the signature of a one-sided rescale.
With the fetched volume supplied, A and B are identical to ~2e-7, so ADV would be unchanged, no other
pool ticker's liquidity percentile would move, and `classify_avb`
(`j11_avb_diagnostic.py:872-939`) would return **AVB-A**, not AVB-B.

Consequences:
- The `material_signals` recorded in `runs/goal-market-compass-iter-16/j11-avb-bridge-diagnostic.json`
  ("1 OTHER pool ticker(s)' liquidity percentile shifted" on 08-11, "11" on 08-12) are produced by the
  scale mismatch, not by the correction.
- The dev handoff's Known Issues states: *"correcting AVB's volume measurably shifts other pool tickers'
  cross-sectional liquidity percentile (1 ticker on 08-11, 11 on 08-12)."* **That is not what was
  measured.** The effect of the correction itself is A(pre) vs A(post), which iteration 15 measured as 4
  and 35 tickers. The 1/11 figures are the effect of dividing the close by the bridge factor while
  leaving the already-compensated volume in place.
- **The gate does not move.** `_AVB_READY_CLASSIFICATIONS = ("AVB-A", "AVB-B")`
  (`j11_stage_d.py:507`) and `ready = preflight_passed and not avb_blocks` (`j11_stage_d.py:520`), so
  `READY: YES` holds under either label.

The spec itself sanctioned the omission (Goal 8: *"these may read the corrected stored rows directly
rather than requiring the in-memory `volume_override` substitution"*), which is why the developer,
reviewer and QA all passed it — but the reasoning is mistaken: `volume_override` never fed
representation A, it fed representation B.

**Not fixed.** The fix is one argument (`volume_override={d: provider_volume}` at
`run_j11_iter16_stage_d_readiness.py:247-248`), but applying it means re-running Goal 8's producer,
which regenerates this iteration's headline artifacts and would change the recorded label — beyond an
audit's remit, against the iteration's unconditional STOP, and it does not change `ready`. Recommended
for a future iteration.

---

**B2 — IMPORTANT (gap): the pre-boot guard is built, wired and proven — but inert against the live database. Booting the backend today still re-arms the trap the owner ruling exists to prevent.**

`evaluate_boundary_for_date` returns `blocked=False` when no boundary row exists at all
(`apps/backend/app/engine/j11_preboot_guard.py:143-145`) — the documented, correct no-incident
behaviour. The live database has **no such row, and not even the table**: I independently confirmed the
live schema still holds exactly **24 tables**, with no `maintenance_boundaries`. Grep confirms
`register_j11_incident_boundary` (`j11_preboot_guard.py:109-119`) is invoked from **no production or
script code path** — only from its own tests and a docstring reference in `app/models.py:1013`.

The live boot order makes the consequence concrete:

1. `apps/backend/main.py:84` — `create_db_and_tables(engine)` → `SQLModel.metadata.create_all` creates
   `maintenance_boundaries` **empty**.
2. `apps/backend/main.py:100` — `ensure_latest_snapshot(engine, config)`.
3. `apps/backend/app/engine/warmup.py:103` resolves `latest = MAX(daily_prices.date) = 2026-08-12`.
4. `warmup.py:107` → guard finds zero rows → `blocked=False`.
5. `warmup.py:121` → `run_scan(session, 2026-08-12, cfg)` writes a `ScannerRun` for an incident date
   currently held at zero runs.

That is exactly the unauthorized Stage-D-class write the "pre-boot incident guard required" ruling was
written to stop. The guard changes nothing operationally until a boundary is registered in the live
database.

Disclosure quality: the dev handoff records the table's absence but frames it as *"correct per this
iteration's scope"* without stating the operational consequence; the review report does not mention it;
the QA report's "Pre-Boot Guard: Fail-Closed & State-Driven ✓" section reads as though the boot path is
now protected. A reader could reasonably conclude the ruling's precondition for resuming application
lanes is satisfied. It is not.

**Not fixed.** Registering the boundary requires creating a table and inserting a row in the live
database — a write outside the single `daily_prices.volume` authorization and explicitly out of scope
(and the coordinator's own true-start capture expects the live schema to stay at 24 tables). This needs
a separate, explicit owner authorization.

**Recommendation: maintenance isolation must stay ACTIVE.** The owner ruling's gate ("proven on
disposable test state") is met; its *operational* purpose is not. Before any application/browser/replay
lane resumes, a separately authorized step must register the J-11 boundary against
`apps/backend/data/trendora.db` and re-verify — and the first boot after that will also, correctly, add
the 25th table, which future preflight captures should expect.

---

**B3 — GAP: the post-correction re-classification cannot disconfirm the correction it is testing.**

The correction is `corrected_volume = round(provider_volume / bridge_factor)`
(`j11_avb_correction.py:413-414`). The classifier then tests
`volume_ratio = stored_volume / provider_volume ≈ 1 / bridge_factor`
(`j11_avb_diagnostic.py:404-412`). Substituting one into the other leaves an arithmetic identity whose
only error term is the rounding — the check cannot fail for *any* value derived by that formula.

The numbers show the fingerprint of construction rather than measurement. Distance from
`expected_inverse_volume_ratio = 0.3580379363`:

| date | volume_ratio | relative distance | source |
|---|---|---|---|
| 2026-08-05 | 0.3580532940 | 4.3e-05 | genuine measurement |
| 2026-08-06 | 0.3580167777 | 5.9e-05 | genuine measurement |
| 2026-08-07 | 0.3580320439 | 1.6e-05 | genuine measurement |
| 2026-08-10 | 0.3580197454 | 5.1e-05 | genuine measurement |
| **2026-08-11** | **0.3580380216** | **2.4e-07** | constructed |
| **2026-08-12** | **0.3580379842** | **1.3e-07** | constructed |

The two corrected dates agree with the target roughly **180× more tightly than any real calibration
measurement does**. Note also that `provider_volume` equals the pre-correction `stored_volume` exactly
on both dates (1,549,436 and 10,350,885), so the correction is literally `round(stored_volume /
bridge_factor)`.

This is not a defect — the owner authorized precisely this transform, `_RATIO_RELATIVE_TOLERANCE = 0.01`
is untouched and reused from the diagnostic rather than redefined, and `j11_avb_diagnostic.py` is
blob-identical to HEAD. It is recorded so the owner does not read the re-run as *independent
corroboration*: `READY: YES` rests on the **pre-correction** evidence chain — iteration 15's genuine
provider fetch, J-10's persisted `bridge_factor`, and the untouched calibration window's demonstrated
`bridged+compensating` convention — not on the post-correction re-classification.

---

**B4 — OBSERVATION: `PRAGMA wal_checkpoint(TRUNCATE)`'s returned triple carries no information, contrary to `checkpoint_wal`'s docstring.**

`j11_avb_correction.py:462-476` records `(busy, log_pages, checkpointed_pages)` and reasons about them.
I reproduced the behaviour on a scratch SQLite database: a TRUNCATE checkpoint returns **`(0, 0, 0)` on
success** whether it moved pages or was a complete no-op, because the WAL is reset to zero length before
the counters are read. The persisted `{busy:0, log_pages:0, checkpointed_pages:0}` is therefore exactly
what a genuine first invocation returns — it is **not** evidence of a skipped or no-op checkpoint, which
resolves the reviewer's NOTE. The load-bearing proof is the `-wal` file returning to 0 bytes and the main
file's mtime moving, and the evidence carries both.

The same reproduction independently produced **exactly 4152 bytes** of WAL for a two-row, one-column
`UPDATE`, and left the main file's **size unchanged while its mtime moved** — corroborating both figures
the handoff reports.

---

**B5 — OBSERVATION: the handoff's "first invocation" narrative is not reconstructible from any artifact — but the write it could have concealed is positively excluded.**

Reconstructed timeline from the persisted artifacts plus live file metadata:

| UTC | event | source |
|---|---|---|
| 2026-08-24T17:13:42.428Z | live DB last written (end of iter-15) | true-start `db_file.mtime` |
| 2026-08-25T15:06:18.408Z | true-start capture completes; `-wal` 0 bytes | `j11-avb-correction-true-start.json` |
| 2026-08-25T15:06:18.427Z | derivation persisted (19 ms later) | `j11-avb-correction-derivation.json` |
| **2026-08-25T15:06:35.652Z** | **live DB mtime moves — the only move** | live `stat`, true-end `db_file.mtime` |
| 2026-08-25T15:09:50.256Z | true-end capture completes (~3.2 min of hashing) | `j11-avb-correction-true-end.json` |

The mtime move sits 17 s after the derivation persist and 3.2 min before the true-end capture — exactly
where `checkpoint_wal` is called (`run_j11_avb_correction.py:187`), and *not* where a process-exit
auto-checkpoint of a separate earlier run would land. A prior failing run against the live database is
therefore excluded: its write would have moved the mtime before 15:06:18, and the true-start capture read
the 08-24 value with a 0-byte WAL. Whatever the "first invocation" was, it did not write to
`apps/backend/data/trendora.db`. The narrative is unverifiable; the risk it might have hidden is not.

I re-`stat`ed the database after all of my own work: mtime `1787670395`, size `8365871104`, `-wal` 0 —
still exactly one lifetime move.

---

**B6 — OBSERVATION: `evaluate_boundary_for_date`'s `row.active is None` branch (`j11_preboot_guard.py:150`) is unreachable.**

`MaintenanceBoundary.active` is declared non-optional, so the column is `NOT NULL`. I confirmed this by
attempting an explicit NULL insert against an in-memory fixture: `sqlite3.IntegrityError: NOT NULL
constraint failed: maintenance_boundaries.active`. The branch is harmless defensive code; the absence of
a test for it is therefore not a real coverage gap.

---

**B7 — OBSERVATION: `select(MaintenanceBoundary)` (`j11_preboot_guard.py:143`) is an unbounded whole-table ORM load on the boot path.**

AG-8 forbids unbounded whole-table ORM loads. In practice this table holds one row per named boundary
and is read once per boot, so the impact is nil — but the pattern is worth naming since it now sits on
the shared boot path every journey depends on.

### Test Findings

**T1 — GAP: no test confronts the live-shaped scenario "table present, empty, latest date is an incident date".**

Test quality is otherwise genuinely high, and notably resistant to the failure modes this session has
been catching:

- `test_avb_other_dates_hash_moves_if_a_non_target_avb_date_changes` and
  `test_non_avb_hash_moves_if_a_non_avb_row_changes` prove the isolating hashes *can* move — these are
  gates that can fail, not gates that always pass (iteration 13's lesson, applied).
- Six `test_build_mutation_evidence_fails_when_*` tests prove each mutation check can fail independently.
- The three CLI refusal tests assert `get_engine` and `Session` are **never called** (`mock.assert_not_called`),
  not merely that the exit code is non-zero.
- The guard's warmup tests call the **real** `warmup.ensure_latest_snapshot` with `run_scan` monkeypatched
  to a recording stub, asserting `calls == []` when blocked and `calls == [TEST_DATE]` when cleared or
  unregistered — real behavioural proof that no `ScannerRun` is created.

The gap: `test_tc25_no_boundary_registered_is_a_true_noop` and
`test_tc25_ensure_latest_snapshot_byte_identical_when_no_boundary_registered` are framed as the benign
"common no-incident case", but they are simultaneously an exact model of the live database's current
state (B2). No test names that overlap, so the suite never surfaces it to a reader. This is the test-side
reflection of B2, not an additional defect.

### Process Findings

**P1 — GAP: the review packet advertised completeness while hiding 100% of the new code.**

`runs/goal-market-compass-iter-16/review-packet.md:8` states *"Files changed: 5. Shown in full: 5"*, and
its header promises *"Truncations and exclusions are NAMED below."* Seven new untracked files were
neither shown nor named, because `git diff HEAD` cannot see untracked files:

```
apps/backend/app/engine/j11_avb_correction.py      <- the derivation + the write function
apps/backend/app/engine/j11_preboot_guard.py       <- the entire guard
apps/backend/scripts/run_j11_avb_correction.py     <- the ONE live-write CLI
apps/backend/scripts/run_j11_iter16_stage_d_readiness.py
apps/backend/tests/test_j11_avb_correction.py
apps/backend/tests/test_j11_avb_correction_cli_script.py
apps/backend/tests/test_j11_preboot_guard.py
```

Everything that performs the authorized live write, everything that gates every future boot, and every
test proving either was invisible to the packet, while the packet asserted full coverage. The reviewer
evidently read beyond it (they report re-running the 12-file suite and independently checking the live
table count), so no harm landed this iteration — but a packet that claims "shown in full" while omitting
the entire substance of an iteration is a recurring hazard worth fixing:
`build_review_packet` should union `git ls-files --others --exclude-standard` into its file set, or at
minimum name the untracked set as an explicit exclusion.

---

## 3. Domain Assessment

**The bounded write is exact and provably isolated.** I re-derived every figure with raw `sqlite3`,
importing nothing from the project, so nothing under audit could influence the result:

| check | independently derived | expected (coordinator true-start) | |
|---|---|---|---|
| AVB OHLC-only hash (5,397 rows) | `757c3c63…c8fd3` | `757c3c63…c8fd3` | unchanged |
| AVB other-dates full-row hash (5,395 rows) | `53bca571…c14f` | `53bca571…c14f` | unchanged |
| non-AVB full-row hash (3,304,977 rows) | `78146554…4997` | `78146554…4997` | unchanged |
| manifest row-dump hash (24 rows) | `bb954b60187e39a1…16d2a2e6` | `bb954b60…6d2a2e6` | prefix/suffix match |
| manifest DDL hash | `9f653c81…c501ee` | `9f653c81…c501ee` | unchanged |
| `daily_prices` rows | 3,310,374 | 3,310,374 | ✓ |
| `scanner_runs` | 3,117 (34 `6261ca17…` + 3,083 NULL + 0 other) | same | ✓ |
| `forward_returns` total / measured-into-incident | 6,797,728 / 16,614 | same | ✓ |
| `data_provider_runs` / manifests / `watchlist` | 549 / 24 / 6 | same | ✓ |
| `ScannerRun`s on the 11 incident dates | 0 | 0 | ✓ |
| live table count | 24 (no `maintenance_boundaries`) | 24 | ✓ |
| db size / `-wal` | 8,365,871,104 / 0 | same / 0 | ✓ |

The two target rows now read `(183.22001534990548, 184.13001191846783, 181.7100027790582,
181.76001476703186, **554757.0**)` and `(181.08999902870366, 182.0900043902787, 179.45999604273928,
179.79000697488598, **3706010.0**)` — OHLC byte-identical to the pre-write capture, and each volume
exactly `round(provider_volume / bridge_factor)` with `bridge_factor = 2.7930001225759193`
(554756.8678840555 → 554757; 3706009.5043796916 → 3706010). `ohlcv_sum` moved from
52,367,106,488,426.56 to 52,367,098,848,872.56 — a delta of exactly **7,639,554.0**, matching
`(1549436 − 554757) + (10350885 − 3706010)` to the unit. The three isolating hashes matching the
pre-resume capture is the strong half of the proof: it is the counts that did *not* move, per iteration
13's lesson.

`apply_avb_volume_correction` (`j11_avb_correction.py:479-502`) assigns exactly one attribute —
`row.volume` at line 498, the only assignment in the function — scoped by `symbol == 'AVB' AND date IN
TARGET_DATES`, and raises before writing anything if the matched row count is not exactly 2. The
refusal gates (`run_j11_avb_correction.py:100-118`) both precede `get_engine()` at line 128.

**The certified-baseline supersession is a genuine gate, not a recorded value.** Only
`daily_prices_fingerprint` changed; I hashed each of the other five composed fields (`manifest_ddl`,
`manifest_dump`, `manifest_row_count`, `data_provider_runs_count`, `watchlist_count`) in both the new
baseline and iteration 13's source artifacts and confirmed they are identical. The superseded
fingerprint's `pre_correction` value (`572691772b…3451a`) matches iteration 13's *and* iteration 15's
preflight captures, and the `post_correction` value (`80441b37…24cc`) matches this iteration's fresh
preflight capture — sourced, not copied. The gate genuinely moves: against the OLD baseline exactly one
of eleven checks is `False` (`daily_prices_fingerprint_unchanged`) with the other ten `True`; against the
NEW baseline all eleven are `True`. `j11_stage_d.py`'s diff is a single purely additive 50-line insertion
at line 385 — `compare_stage_d_preflight_to_certified`, `stage_d_readiness_verdict`,
`produce_stage_d_readiness_artifact` and `capture_stage_d_preflight` are untouched.

**`j11_avb_diagnostic.py` is untouched — confirmed structurally, not from the claim.** Its worktree blob
hashes to `ad0ac0ac6d11ea457f3ac173b17eef454d1a1690`, identical to `HEAD:apps/backend/app/engine/
j11_avb_diagnostic.py`; its last commit is iteration 15's `17eb97ce`. The classifier, its labels and its
1% tolerance were not modified this iteration.

**The classification is mechanically reachable and the gate is correct.** Recomputing every ratio myself
from the live corrected rows and iteration-15's provider evidence, with my own tolerance arithmetic:
all four calibration dates and both recovered dates classify `bridged+compensating`, so
`indeterminate=False` and `internally_consistent=True`. Per `classify_avb`'s branch order that
**excludes AVB-D and AVB-C outright** — the only two labels that would block. The residual ambiguity is
AVB-A vs AVB-B (B1), and both are in `_AVB_READY_CLASSIFICATIONS`. The preflight gate passes all eleven
checks. `ready = True` is therefore correct on the evidence, subject to B3's qualification about what
that evidence can and cannot prove.

**Anti-goals hold.** Zero network-capable imports or calls in any new or changed backend file (the one
`requests` grep hit in `warmup.py:223` is narrative prose in a docstring) — AG-9's dated exception #2
stays exhausted. The manifest row-dump and DDL hashes are unchanged and no manifest row was touched
(AG-12/AG-17). Iteration 15's `j11-stage-d-readiness.json` still reads `AVB-C` / `ready: false` on disk,
never edited (AG-17). No lookahead is introduced — the guard only ever *declines* to write, and the
correction touches historical volume only. The new modules add no decision thresholds and are outside
`test_no_magic_numbers.CALC_FILES`, consistent with the existing J-11 maintenance modules.

**Housekeeping.** I confirmed `git status --porcelain` returns zero lines on
`runs/goal-market-compass-iter-9/` through `-iter-15/` — both before and again *after* running the
targeted suite myself (TC-39 holds). TC-40 (this iteration's code/evidence committed) is not yet
satisfied: `HEAD` is still `346ed65a`, the owner-rulings commit, and all iteration-16 work is untracked
or unstaged. This is expected pipeline ordering — the commit belongs to the finalize step, after audit —
so it is noted as pending rather than as a defect, but it remains unverified by this audit.

**Independent test run.** I re-ran the same twelve targeted files in a single pytest process:
`209 passed in 12.04s`, matching the dev handoff and QA report exactly. No full-suite run, no concurrent
pytest, no database copy, no service boot, no network, no `/api/compass` request, and no re-run of the
correction script.

---

## 4. Fixes Applied During This Audit

**None.**

Both IMPORTANT findings are gaps I deliberately did not fix, for reasons that are part of the finding:

| # | Finding | Why not fixed |
|---|---------|---------------|
| B1 | Representation B scale-inconsistent | The fix is one argument, but applying it requires re-running Goal 8's producer, which regenerates this iteration's headline artifacts and changes the recorded classification. That exceeds an audit's remit, contradicts the iteration's unconditional STOP, and does not change `ready`. |
| B2 | Guard inert on the live DB | Registering the boundary requires creating a table and inserting a row in `apps/backend/data/trendora.db` — a write outside the single `daily_prices.volume` authorization, explicitly out of scope, and contrary to the expected 24-table live schema. Requires separate owner authorization. |

I also did not edit the dev handoff to correct B1's unsupported causal claim: I applied no code fix that
would invalidate it, and rewriting the developer's own record would muddy the evidence trail. This report
is the correction of record.

---

## 5. Recommended Next Step

**Concurrence with the other lanes, stated plainly:**

- **`J-11 STAGE D READY: YES` — I concur.** Reached mechanically, not hand-picked, not tolerance-tuned,
  not reverse-engineered: `j11_avb_diagnostic.py` is blob-identical to HEAD, the 1% tolerance is reused
  rather than redefined, and my own from-scratch recompute of every ratio gives
  `internally_consistent=True`, which rules out both blocking labels. I did **not** get AVB-A, AVB-C or
  AVB-D as the gate answer — the gate answer is YES under every label the evidence can support. My one
  qualification is B3: this is confirmation that the authorized correction landed, not independent
  validation that it was the right correction. That rests on iteration 15's fetch, J-10's bridge factor
  and the untouched calibration window.
- **`J-11 STAGE D AUTHORIZED: NO` — confirmed, unconditionally.** `stage_d_readiness_verdict`
  (`j11_stage_d.py:535`) hard-codes `"authorized": False`; the artifact carries it; and I found no Stage
  D work, no `ScannerRun` creation, no cache invalidation, and no iteration-17 planning or scoping
  anywhere in the diff, the artifacts or the handoff.

**Before anything else — do not boot the backend.** B2 means the pre-boot guard, despite being correct,
proven and wired, currently protects nothing on the live database. Maintenance isolation must remain
externally ACTIVE. Treat "the guard is proven" and "the boot path is protected" as two separate states;
only the first is true today.

**Recommended sequence for the next owner instruction, in order:**

1. **Activate the guard** — a narrowly authorized step that registers the J-11 incident boundary in the
   live database via `register_j11_incident_boundary` (creating `maintenance_boundaries` as the 25th
   table), then re-verifies that `evaluate_boundary_for_date(2026-08-12)` returns `blocked=True` against
   the live state, and re-captures the isolating hashes to prove `daily_prices` was untouched by the
   registration. Only after this is the ruling's operational purpose met and any application/browser/
   replay lane safe to resume.
2. **Re-run the decision-impact trace correctly** (B1) — pass `volume_override` built from the
   already-committed iteration-15 provider volumes, and record the corrected classification. Expect
   AVB-A and `READY: YES` unchanged. This also supersedes the handoff's unsupported claim about
   cross-sectional percentile shifts.
3. **Then, and only then, decide on Stage D** with the evidence correctly characterised.

**Also carry forward:** commit this iteration's code, tests and evidence (TC-40, still pending at audit
time); and fix `build_review_packet` to include or explicitly name untracked files (P1), so the review
lane cannot again be handed a packet that claims "shown in full" while omitting an iteration's entire
substance.
