# goal-market-compass-iter-9 Audit Report

**Date:** 2026-08-23
**Auditor:** Hard audit pass — skeptical, evidence-based
**Mode:** maintenance isolation ACTIVE — no service started, no browser automation, no replay lane.
All verification below is read-only SQLite (`file:...?mode=ro`), artifact inspection, static code
reading, and one targeted two-file pytest invocation.

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal was genuinely achieved: 585 of 587 `RECOVERY_SYMBOLS` now carry both recovery-date
bars (independently re-counted in the live DB), the two residuals are honestly named with evidenced
reasons, the three named audit gaps are closed by real guards with real degenerate-input tests, the
committed driver exists, and AG-9/AG-12/AG-17 hold. The database is correct — I found no wrong,
missing, or out-of-scope row.

What I did find is that the **required provenance record misstates how the data was produced in two
material ways**, both of which passed the reviewer and QA unchallenged because both agents repeated
the handoff's framing instead of re-deriving it. The handoff claimed every restored symbol was
bridge-transformed by a factor of 1.0 — one symbol (AVB) was transformed by **2.793**, and it is the
*only* symbol in the batch whose restored prices were actually produced by the bridge arithmetic. It
also claimed the idempotency re-run was a "verified zero-write no-op" while its own mutation table
counted that run's writes. Both are corrected in the handoff by this audit. The remaining items are
documented gaps, not blockers.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the provenance record erased the one symbol the bridge actually
transformed.**

`docs/handoffs/goal-market-compass-iter-9-dev.md` stated, in the required J-10 step-4 provenance
section, that the 565 symbols restored this iteration were *"bridge-transformed by a factor of 1.0
for every one onto the stored scale"*, and in its C1 restatement that the batch showed
*"`bridge_factor == 1.0` (566/566 agree verdicts …)"*. That is false.

`runs/goal-market-compass-iter-9/j10-population-evidence.json`, the mandatory evidence artifact,
records **`AVB` with `bridge_factor = 2.7930001225759193`** over 4 comparable pairs (per-day
stored/fallback ratios 2.79300012–2.79300017, dispersion 2.87e-08). AVB's stored series sits at ~$186
across the calibration window while Yahoo's current `get_daily` series for the same window sits at
~$67.9 — a real ~2.79× scale discontinuity, which is precisely the condition
`_BridgeApplyingProvider` (`apps/backend/app/engine/j10_recovery.py:793-837`) exists to correct.

Independent structural confirmation, not taken from any artifact: of the **1,170** recovery-date rows
in `daily_prices`, **exactly 2 — both AVB — hold OHLC values that are not exactly float32-
representable**. Every other restored row is float32-exact, i.e. a raw provider value inserted
unchanged. AVB is demonstrably the sole symbol whose values passed through a real multiplication.

Why this rises above bookkeeping: the handoff's entire safety argument is *"factor 1.0 everywhere ⇒
a Yahoo-vs-Yahoo tautology ⇒ no scale discontinuity is possible"*. AVB is the single counter-example,
and the single row whose correctness depends on the bridge math being right — exactly the case a
reviewer or owner would want to look at. Erasing it removed the only material risk from view. The
reviewer (`reports/reviews/goal-market-compass-iter-9-review.md`, `issues: []`) and QA
(`reports/qa/goal-market-compass-iter-9-qa.md`, TC-2 row) both repeated the "all 1.0" framing.

**The transform itself is correct**, verified independently: AVB stored close 183.84 (2026-08-10) →
restored 181.76 (08-11) → 179.79 (08-12), i.e. −1.1% and −1.1%, continuous. Un-bridged insertion
would have written ~$65 bars — a 2.79× break in AVB's own history. Had the corporate action fallen
*between* 08-10 and 08-11 (the one case the gate cannot detect), the ×2.793 would have produced a
~2.79× discontinuity instead; it did not, so the calibration window and the target dates are on the
same side of the action.

*Fix applied:* the handoff's C1 paragraph and its "Symbols restored this iteration" provenance bullet
now state the real distribution (565 of 566 agree verdicts at 1.0, AVB at 2.793), carry the AVB
evidence, and carry the float32 confirmation. No code changed — the code was right.

---

**B2 — GAP (documented, deliberately not fixed): AVB's restored bars mix two scales — price on the
stored scale, volume on Yahoo's current scale.**

`_BridgeApplyingProvider.get_daily` (`apps/backend/app/engine/j10_recovery.py:833-836`) multiplies
open/high/low/close by the factor and passes `volume=b.volume` through unscaled. That is exactly what
`docs/goal.md` mandates ("volume is not a price and is not scaled") and what DoD TC-2 requires, so
the implementation is correct and **I did not change it** — fixing it would violate the spec.

The consequence is nonetheless real and undisclosed. AVB volumes: 606,300 / 591,600 / 642,300 /
666,100 / 451,300 on 2026-08-03..08-10, then **1,549,436** (08-11) and **10,350,885** (08-12).
1,549,436 ÷ 2.793 = 554,760 — squarely inside the prior range, confirming the restored volume is on
the post-adjustment scale while the restored price is on the pre-adjustment scale. Anything
multiplying the two reads AVB ~2.79× high: `scoring.py:86-91` (`_avg_dollar_volume`, `close *
volume`), `universe_resolver.py:73-78` (`_adv_dollar`), and the liquidity cut in
`universe_screen.py:47-48` (`adv_dollar < min_dollar_vol`). Only AVB is affected — every other
restored symbol has factor 1.0, so its price and volume are on the same scale.

*Not fixed (spec-mandated behavior). Recorded in the handoff so J-11 can account for it when it
regenerates derived state from this basis.*

---

**B3 — IMPORTANT (fixed): TC-9's "verified zero-write no-op" is contradicted by the handoff's own
mutation table.**

The population-run table claimed the third (idempotency) invocation produced *"0 — **verified
zero-write no-op**"*. The same document's mutation-reconciliation table simultaneously counts
`data_provider_runs` +6 across **3** driver invocations and `import_checkpoints` +3, "one per fetch
job" — i.e. it counts the third run's writes while the table above says there were none.

Read-only verification of what that invocation actually did: it wrote `data_provider_runs` **548**
(`yahoo`, fetch, 10:50:44.207) and **549** (`seed`, backfill, 10:50:44.462), `import_checkpoints`
**37** (`symbol_plan_json = ["EA"]`, 10:50:44.207), and refreshed 4 derived aggregate caches
(`forward_aggregates`, `research_hot_keys`, `factor_lab_all`, `drawdown_expectations` — run 549's own
`aggregates_refreshed` list). It also made 3 live Yahoo calls (calibration `get_daily` for EA and
EQR, plus the EA fetch job).

What *was* verified, and does hold, is **zero `daily_prices` writes** — row count 3,310,374 before
and after — which is the property idempotency actually needs. The overclaim is the word "zero-write".

*Fix applied:* the table row and a correction note in the handoff now state precisely what was
verified and enumerate the writes that occurred.

---

**B4 — GAP (documented): the committed driver's zero-work path is unreachable, so every future
re-run performs a live fetch — after AG-9's exception is declared exhausted.**

`apps/backend/scripts/run_j10_population_recovery.py:149-153` returns early ("nothing missing -- true
zero-work no-op") only when `still_missing_symbols()` is empty. EA and EQR can never be restored, so
that set is permanently non-empty and the early return is dead code in practice. Every future
invocation re-calibrates EA/EQR against live Yahoo and dispatches an EA fetch job. Since the same
handoff declares AG-9's dated exception **exhausted**, re-running the committed driver would itself
be an AG-9 violation absent a new dated amendment — and the script contains no exhaustion guard and
will not refuse.

*Not fixed:* an exhaustion guard needs a persisted authorization flag, which is an owner/`goal.md`
decision, not an audit edit; and gating the driver would work against DoD TC-9's own reproducibility
requirement. Recorded in the handoff as an explicit warning instead.

---

**B5 — GAP (documented): the provider-mismatch guard fails open when neither provider declares a
`source`, and is not anchored to the authorized vendor.**

`_check_fetch_provider_source_matches` (`apps/backend/app/engine/j10_recovery.py:857-878`) compares
`getattr(provider, "source", None)` on both sides. `PriceProvider.source` defaults to `None`
(`apps/backend/app/data_providers/base.py:43-51`), and the iteration's own new provider test asserts
that a provider declaring nothing (e.g. `TiingoProvider`) keeps `None` — so **two different vendors
that both leave `source` unset compare equal and are accepted**. Separately, nothing checks
`convention_provider.source` against `RECOVERY_SOURCE`: `validate_recovery_scope` and
`data_manager.validate_job_request` are both called with the hardcoded string `RECOVERY_SOURCE`
(`j10_recovery.py:751-753, 772-774`), so a caller supplying a non-Yahoo provider object would fetch
from that vendor while the provenance row records `yahoo`.

Neither path is reachable from committed production code: the only real caller constructs
`_ProgressLoggingYahooProvider`, a `YahooProvider` subclass inheriting `source = "yahoo"`, and omits
`fetch_provider` entirely. The spec's gap #2 asked only for pair-matching, and pair-matching works
(4 tests, including the end-to-end wiring test that asserts no evidence file is written on refusal).
Recommended hardening for a future iteration: treat `None` as never-matching, and assert
`convention_provider.source == RECOVERY_SOURCE`.

---

**B6 — GAP (documented): derived state is now mixed-basis, which is more than the handoff's "stale
snapshots" framing.**

Backfill run 545 recorded `already_snapshotted: 2, snapshots_created: 0, forward_returns_inserted: 0`
— the ScannerRun snapshots for 2026-08-11/08-12 were left as iter-8 created them (verified:
`scanner_runs` max `created_at` is 2026-08-21 00:28, count 3121, and the two recovery-date rows date
from 2026-08-21 00:26/00:28, i.e. when only 20 of 587 symbols had bars). But the same run refreshed
**six** derived aggregate caches over the now 585-symbol basis: `availability_heatmap`,
`forward_aggregates`, `index_series`, `research_hot_keys`, `factor_lab_all`,
`drawdown_expectations`.

The handoff's mutation table discloses the refresh and Known Issue #4 discloses the stale snapshots,
but neither states the combination: the derived layer now holds aggregates computed over the repaired
basis sitting alongside scanner snapshots computed over the 20-symbol basis. This is pre-existing
ingest-finalize behavior, not new work, and the spec's OUT OF SCOPE forbade *adding* cache-
invalidation work rather than forbidding this side effect — so it is not a violation. J-11 must clear
both layers, not only the snapshots.

---

**B7 — OBSERVATION: the back door is closed against every production path but not against a
hand-built wrapper.**

`run_bounded_recovery_fetch` (`j10_recovery.py:762-771`) keys the gate on
`isinstance(provider, _BridgeApplyingProvider)` plus that instance's `_bridge_factors`. A caller can
still construct `_BridgeApplyingProvider(raw, {"AAPL": 1.0})` by hand and insert on a guessed factor.
The module docstring acknowledges this ("if a future caller is ever wired up wrong",
`j10_recovery.py:806-809`). DoD TC-8's wording is "cannot be reached **in production code**", and no
production caller does this — the requirement is met.

### Frontend Findings

None. `Frontend Present: no`; no frontend file appears in the diff (`git status --short` confirms the
change set is backend, tests, script, and run artifacts only). Correctly scoped.

### Test Findings

**T1 — OBSERVATION: no population-level test exercises a non-unity bridge factor end to end.**

All three population tests in `apps/backend/tests/test_j10_recovery.py` seed stored and fallback
series that are identical, so every factor is 1.0 and the transform is a no-op; the assertions on
restored closes (`[201.0, 202.0]`) would pass whether or not the multiplication happened. Non-unity
coverage exists only at the wrapper level
(`test_bridge_applying_provider_transforms_all_four_price_fields_not_volume`, factor 1.01, which does
assert all four OHLC fields scale and volume does not). Given AVB was the one real case, an
end-to-end population test with a non-unity factor is the natural place this iteration's narrative
error (B1) would have surfaced. Not a correctness defect.

**T2 — POSITIVE: the gap-closing tests are genuinely degenerate-input tests, not happy-path
fixtures** — the iter-7 lesson the spec asked for was applied. TC-6 uses a `_NeverCalledProvider` that
fails on any `get_daily`; TC-7's end-to-end test additionally asserts `not evidence_path.exists()`,
proving refusal precedes persistence; TC-8's second test proves the check is per-symbol (a gated
provider holding AAPL's factor still refuses a request that also names MSFT, with zero rows for
either — no partial insert).

---

## 3. Domain Assessment

The per-symbol gate is sound and, importantly, **honest about its own weakness**. The verdict ladder
(`_compute_symbol_verdict`, `j10_recovery.py:482-599`) checks mismatch *before* the evidence floor, so
a genuine disagreement can never be laundered into "inconclusive" by a coverage gap — the iter-7 B1
lesson correctly carried into per-symbol form. Both refusal branches were exercised for real: EQR hit
the `<2 comparable pairs` branch (its evidence row shows stored closes on all 5 window dates but a
Yahoo fallback on only 2026-08-06), and it was refused despite Yahoo actually holding EA-style target-
date data. Refusing on under-evidenced calibration when the target data is available is the gate
behaving exactly as designed.

Two domain-level cautions the artifacts understate:

1. **The population result is a same-source tautology almost everywhere.** Across 567 symbols the
   maximum path-agreement delta is 1.65e-08 and the maximum bridge dispersion is 2.87e-08 — stored
   and fallback closes are bit-identical for essentially the entire population, because the stored
   overlap-window bars are themselves Yahoo's. The handoff states this (C1), and it is the right
   framing: this run validated *scope and plumbing*, not vendor agreement. AVB is the one place the
   gate did real work, which is what makes B1's erasure of it consequential.

2. **EA's `agree` verdict is degenerate.** Its evidence row shows stored close = fallback close =
   209.6999969482422 on all five window dates — a flat line. Path agreement over a constant series is
   trivially 0.0% and dispersion is trivially 0.0%, so the gate returns `agree` on what is really "no
   price movement to compare". No harm resulted (Yahoo returned zero target-date bars, so nothing was
   inserted), but a flat-series guard is worth considering if this gate is ever reused.

Scope discipline was excellent. Every frozen constant is byte-unchanged (verified: the 20 symbols in
`CONVENTION_CHECK_SAMPLE_SYMBOLS` are exactly `RECOVERY_SYMBOLS` minus the evidence artifact's 567,
so the population axis and the methodology axis are provably disjoint). The provider changes are
three lines plus comments and change no existing behavior. `_run_gated_recovery_core` is the right
refactor — one place enforces all three guards for both entry points, so they cannot drift.

### DEFINITION OF DONE — verification

Risk-class items (data mutation/persistence/scope) were fully traced by me. Mechanical items already
executed against the running system by QA are accepted with citation.

| Item | Verdict | How verified |
|---|---|---|
| TC-1 every still-missing symbol has exactly one verdict | PASS | **Traced.** Evidence artifact holds 567 unique symbol rows (566 agree + 1 inconclusive); `set(evidence) ∪ {20 iter-8 symbols} == RECOVERY_SYMBOLS` exactly, and `RECOVERY_SYMBOLS − (evidence ∪ restored)` is empty |
| TC-2 agree ⇒ both bars, OHLC × factor, volume unscaled | PASS (see B1/B2) | **Traced.** 1,170 recovery-date rows = 585 × 2; AVB's ×2.793 transform verified arithmetically and for continuity; all other restored rows float32-exact (factor 1.0); volume unscaled per spec |
| TC-3 mismatch/inconclusive ⇒ zero rows + named reason | PASS | **Traced.** `EA`/`EQR` hold 0 rows on either recovery date; both named with reasons in `j10-population-summary.json` and in the evidence artifact |
| TC-4 iter-8's 20 excluded, 40 rows byte-identical | PASS | **Traced.** `import_checkpoints` 35's `symbol_plan_json` (the actual fetch request) contains none of the 20; the calibration sample (evidence artifact) contains none of them either; all 1,170 recovery rows occupy a contiguous id tail 3,311,385–3,312,554 above every other row — a pure append, no rewrite |
| TC-5 out-of-scope date/symbol/source refused pre-network | PASS | **Traced** `validate_recovery_scope` (`j10_recovery.py:285-312`), called before `run_data_job`; 8 scope tests pass |
| TC-6 `evidence_path` required | PASS | Reviewer PASS (`spec_alignment: complete`, `issues: []`) + QA row "TC-6 … both tests"; re-confirmed by my own run of both `*_requires_evidence_path_missing_arg_refused` tests |
| TC-7 fetch/convention source mismatch refused | PASS (see B5) | Reviewer PASS + QA row "TC-7 … 4 tests"; re-confirmed in my run. B5 records the fail-open edge the spec did not require closing |
| TC-8 no ungated symbol reaches `run_bounded_recovery_fetch` | PASS (see B7) | **Traced** `j10_recovery.py:762-771` + both TC-8 tests |
| TC-9 driver committed + idempotent zero-write no-op | **PARTIAL → corrected** | **Traced.** Idempotency holds (zero `daily_prices` writes); "zero-write" was false — see B3/B4. Driver file exists at `apps/backend/scripts/run_j10_population_recovery.py`; it is still untracked at audit time and is committed only by the pipeline's release step (see A2) |
| TC-10 every DB write classified and disclosed | PASS after correction | **Traced.** `daily_prices` +1,130, `data_provider_runs` +6 (544-549), `import_checkpoints` +3 (35-37), aggregate-cache refreshes, `scanner_runs` +0, `next_session_manifests` +0 — all present in the mutation table; the third invocation's share of them was misstated until B3's fix |
| TC-11 depth `full`, no browser/replay lane | PASS | **Traced.** `runs/goal-session-market-compass/iter-9/depth-dispatched` = `full`; no `reports/qa/goal-market-compass-iter-9-evidence/`, no replay-lane dir; `scanner_runs` max `created_at` is 2026-08-21 — no boot-warmup row today, so isolation demonstrably held |
| TC-12 `data_provider_runs` agrees with the handoff | PASS | **Traced.** 544 `symbols_ok 566, bars_fetched 1130`; 546/548 `symbols_ok 1, bars_fetched 0`; 545/547/549 backfills `snapshots_created 0` — every figure matches |
| TC-13 AG-9 exhaustion statement | PASS | **Traced.** 585 restored + 2 named unrestorable = 587; both residuals carry evidenced, non-transient, external reasons; `true` is defensible |
| TC-14 all work on `goal/market-compass`, `main` unchanged | PASS | **Traced.** `main` = `21e97a44`, HEAD = `5a66a30a` on `goal/market-compass` |
| TC-15 targeted tests pass, zero regressions | PASS | **Re-run by me:** `cd apps/backend && .venv/bin/python -m pytest tests/test_j10_recovery.py tests/test_provider_clients.py -q` → **101 passed in 4.02s**, one process |
| TC-16 AG-12/AG-17 + iter-8 evidence byte-unchanged | PASS | **Traced.** `next_session_manifests`: 24 rows, `SUM(prospective_eligible)` = 0, `MAX(as_of)` 2026-08-12 — no eligibility upgraded. `reports/qa/goal-market-compass-iter-8-evidence/`: 5 tracked files, `git status` clean — byte-unchanged |
| Dev handoff written | PASS | Present; corrected by this audit |

Anti-goals: **AG-9 holds** (dates confined to {2026-08-11, 2026-08-12} — 0 rows on/after 2026-08-13,
`MAX(date)` still 2026-08-12; symbols confined to `RECOVERY_SYMBOLS`; vendor `yahoo` only; MNST
excluded; no third vendor attempted). **AG-12/AG-17 hold** (zero manifest mutation, zero eligibility
change). **No spec violation introduced.**

### Additional observations

**A1 — OBSERVATION: `j10-population-summary.json` is not purely driver-generated.** It carries `note`
and `idempotency_reverification_utc` keys that `main()`'s `summary_path.write_text` payload
(`run_j10_population_recovery.py:262-271`) never writes, and its EA/EQR `reason` strings differ from
the driver's canned `provider_empty_range` text (`:212-218`). Re-running the committed driver will
not reproduce this file. The canonical evidence artifact *is* driver-generated and does reproduce.

**A2 — OBSERVATION: `runs/goal-market-compass-iter-9/j10-population-recovery.log` is listed under
"Files Changed" but is gitignored** (`.gitignore:3:*.log`), so it will not be committed and cannot
serve as repository evidence. At audit time the driver script and both JSON artifacts are also still
untracked; TC-9's "committed to the repository" is satisfied only once the pipeline's release step
runs — worth confirming it picks up `apps/backend/scripts/run_j10_population_recovery.py`.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `docs/handoffs/goal-market-compass-iter-9-dev.md` | Corrected the C1 paragraph: replaced "`bridge_factor == 1.0` (566/566)" with the real distribution and added an auditor-correction block carrying AVB's factor (2.793), its 4 comparable pairs, the ~2.79× stored-vs-Yahoo scale gap, the 08-10→08-12 continuity check, and the float32 confirmation that AVB's 2 rows are the only transformed values among 1,170 (B1) |
| 2 | Important | `docs/handoffs/goal-market-compass-iter-9-dev.md` | Corrected the "Symbols restored this iteration" provenance bullet, which read "bridge-transformed by a factor of 1.0 for every one" — now 564 at 1.0 plus AVB at 2.793 (B1) |
| 3 | Gap (disclosure) | `docs/handoffs/goal-market-compass-iter-9-dev.md` | Added the AVB volume-scale caveat with the affected call sites (`scoring._avg_dollar_volume`, `universe_resolver._adv_dollar`, `universe_screen`'s liquidity gate) so J-11 can account for it (B2) |
| 4 | Important | `docs/handoffs/goal-market-compass-iter-9-dev.md` | Corrected the population-run table's "verified zero-write no-op" to "zero `daily_prices` writes", and added a correction block enumerating the third invocation's actual writes (`data_provider_runs` 548/549, `import_checkpoints` 37, 4 aggregate-cache refreshes, 3 live Yahoo calls) (B3) |
| 5 | Gap (disclosure) | `docs/handoffs/goal-market-compass-iter-9-dev.md` | Added the warning that the driver's zero-work early return is unreachable while EA/EQR stay missing, so any future run performs live fetches and needs a new dated `goal.md` amendment now that AG-9's exception is exhausted (B4) |

**No product code was changed by this audit** — the code is correct; the claims about it were not.

**Post-fix verification.** Every corrected statement was re-derived from primary sources in one
consolidated read-only pass (evidence artifact + `file:data/trendora.db?mode=ro`): agree verdicts with
factor ≠ 1.0 → `[('AVB', 2.7930001225759193, 4)]`; agree total → 566; recovery rows 1,170 with
not-float32-exact = `[('AVB','2026-08-11'), ('AVB','2026-08-12')]`; AVB closes 183.84 → 181.76 →
179.79; AVB volumes 451,300 → 1,549,436 → 10,350,885; `data_provider_runs` 548/549 and
`import_checkpoints` 37 all timestamped 2026-08-23 10:50:44; `daily_prices` total 3,310,374. The
targeted suite was re-run after the edits: **101 passed** (`test_j10_recovery.py` +
`test_provider_clients.py`, one process). `git status` confirms the only file I touched is the dev
handoff — no source, test, or artifact file was modified.

---

## 5. Recommended Next Step

**Proceed to J-11.** J-10's raw-layer terminal state is genuinely reached and the AG-9 exhaustion
declaration is defensible on the evidence. Carry three items forward:

1. **J-11 must clear both derived layers, not just the snapshots** (B6): the two recovery-date
   `ScannerRun`s are on iter-8's 20-symbol basis while six aggregate caches have already been
   refreshed over the 585-symbol basis. Regenerating snapshots alone leaves the mixed state in place.
2. **Treat AVB as a named watch item** (B1/B2): its restored prices are the batch's only bridge-
   derived values, and its dollar volume reads ~2.79× high wherever `close * volume` is computed.
   Verify AVB's liquidity-gated behavior explicitly in J-11's regenerated output.
3. **Do not re-run `run_j10_population_recovery.py`** without a new dated `goal.md` amendment (B4) —
   it will perform live Yahoo calls and will not refuse on its own.

Non-blocking backlog: anchor the provider-source guard to `RECOVERY_SOURCE` and treat `None` as
never-matching (B5); add a population-level test with a non-unity bridge factor (T1); consider a
flat-series guard in the verdict ladder (Domain Assessment §2).
