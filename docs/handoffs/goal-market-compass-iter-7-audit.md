# goal-market-compass-iter-7 Audit Report

**Date:** 2026-08-20
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's stated goal — swap the vendor to `yahoo`, gate the retry behind a fail-closed
adjustment-convention check, and either honestly restore the two dates or honestly stop with zero side
effects — was achieved: the gate fired on real evidence, the tolerance was not moved after the fact, and
I independently confirmed by direct read-only SQL that **zero rows were written anywhere**. But the gate
as delivered was **fail-OPEN on a degenerate sample**: with zero comparable pairs it returned `"agree"`
("all 0 sampled pairs within 0.7500% relative delta") and `run_gated_recovery` proceeded all the way
into the write-capable fetch — I reproduced this end-to-end on a fixture DB (4 `daily_prices` rows + 2
`data_provider_runs` rows written on a proof of nothing). That is fixed and regression-tested in this
audit (B1). Two IMPORTANT gaps remain unfixed and both are binding on the owner's planned redesign: the
gate validates a series (`adjclose`) that the restore path would never write (it writes raw
`quote.close` — B2), and the per-pair evidence the DEFINITION OF DONE requires was not persisted (B3).

---

## 2. Findings

### Backend Findings

**B1 — CRITICAL (fixed): `check_adjustment_convention` returned `"agree"` when nothing was actually
compared, opening the write path**

`apps/backend/app/engine/j10_recovery.py:419-432` skips any sampled `(symbol, date)` whose STORED close
is absent (`if stored_close is None: continue`) — correct in itself (never fabricate). But the verdict
ladder at the end of the function (pre-fix lines 439-463; now 439-486) had no floor under it: with `pairs == []` the
`incomparable` list is empty, the `failing` list is empty, and control fell straight through to
`verdict="agree"`. The reason string it produced is self-indicting: `"all 0 sampled pairs within
0.7500% relative delta"`.

This is not theoretical. I reproduced it directly (fixture DB, no network, no production DB):

| probe | precondition | pre-fix verdict | post-fix verdict |
|---|---|---|---|
| Q1 | window dates present, sampled symbol has no stored baseline | `agree` (0 pairs) | `inconclusive` |
| Q1b | **default** 20-symbol sample + live-derived window, no baselines | `agree` (0 pairs) | `inconclusive` |
| Q1c | 1 comparable pair out of a 2-symbol × 3-date sample | `agree` (1 pair) | `inconclusive` |
| Q2 | `run_gated_recovery` end-to-end on the Q1 precondition | **wrote 4 `daily_prices` + 2 `data_provider_runs` rows** | `stopped_reason` set, **0 rows** |

Q2 is the load-bearing one: the vacuous verdict is not merely a mislabel, it reaches
`run_bounded_recovery_fetch` (`j10_recovery.py:596`) and writes. The precondition is exactly the condition J-10
exists to repair — a database with rows unexpectedly missing — and the check's own window is derived
LIVE from that damaged database (`_convention_check_window_dates`, `j10_recovery.py:331`). The function's own
docstring also contradicted the behavior: it promised a missing *yahoo* value "is never silently
dropped from the sample and never counted as a pass", while a missing *stored* value was silently
dropped and the resulting vacuum counted as a pass.

**Fix applied** (`j10_recovery.py:460-482`): a minimum-evidence floor after the mismatch branch —
`"agree"` now additionally requires a non-empty comparison that covered EVERY sampled symbol; anything
less returns `"inconclusive"` with the coverage stated in `reason`. Placed deliberately AFTER the
`failing`/mismatch branch so a genuine out-of-tolerance pair is never downgraded to `inconclusive` by a
coverage gap elsewhere — this is what keeps the real 2026-08-20 run's recorded `mismatch` verdict
correct (12 of its 100 pairs had no stored baseline AND CVX exceeded tolerance). Docstring updated at
`j10_recovery.py:392-399`. Four regression tests added (see §4 for the verification run).

**B2 — IMPORTANT (gap): the gate proves a series that the restore path would never write**

`check_adjustment_convention` compares Yahoo's `get_adjusted_close` (`indicators.adjclose`,
`yahoo_provider.py:96-134`) against the stored closes. `run_bounded_recovery_fetch` (`j10_recovery.py:499`)
restores through the unchanged `data_manager.run_data_job` → `provider.get_daily`
(`data_manager.py:3036`), i.e. Yahoo's raw `quote.close`. So even a passing gate authorizes writing a
**different quantity than the one it validated**, into `daily_prices.close`, a column `models.py:101`
documents as "split/dividend-adjusted". The developer's own live probe quantifies the divergence — AAPL
raw-vs-adjusted differed by 0.0862% on four of the five window days (dev handoff lines 108-121) — and
the developer flagged it honestly (Known Issue #3, handoff lines 123-132).

This is not a defect of the implementation: the spec ordered `run_bounded_recovery_fetch` "existing,
unchanged" four separate times (spec lines 34-38, 156-161; plan lines 34-38), and no write occurred. It
is a defect the phase *inherits*, and it is the single most important thing the planned
path-agreement + multiplicative-bridge redesign **must not inherit**: a bridge that is measured on
`adjclose` and then applied to values fetched via `get_daily` would encode the raw-vs-adjusted gap as if
it were the bridge. Whatever series the gate measures must be the series that is transformed and
inserted, through one code path.

**B3 — IMPORTANT (gap, unfixable in this audit): the per-pair evidence the DEFINITION OF DONE requires
was not recorded**

DoD item 2 requires the verdict "with **every sampled pair's observed delta** recorded in the dev
handoff". The handoff (lines 166-178) records a 4-row per-symbol summary — AAPL, XOM, CVX, and an
aggregate `(all other 16 symbols) | 76 pairs | 0.0%` — plus min/max/mean, and states "Full per-pair
evidence ... is preserved in the run artifact". **No such artifact exists**: `runs/goal-market-compass-iter-7/`
holds only `plan.md`, `status.json`, `review-packet.md` and the two goal-slice files, and a repo-wide
grep for the recorded delta values finds them only in the handoff, the QA report and `assumptions.md` —
all prose restatements of each other. The summary is also internally inconsistent with itself: 4 + 4 + 5
+ 76 = 89, against the 88 pairs stated three lines above it, and "all other 16 symbols" should be 17
(20 minus the 3 named).

Under `.claude/judgment-rubrics.md` §5, "Data/metric is X" requires the computing artifact, never prose.
This matters beyond bookkeeping: these 88 deltas are the entire evidentiary basis for the owner's
pending tolerance decision AND for calibrating the redesign's multiplicative bridge, and the one number
that would falsify the "uniform per-symbol dividend adjustment" reading — the intra-symbol spread of the
76 "exact match" pairs — is unrecoverable. `assumptions.md:552-553` claims the handoff recorded "every
sampled pair's observed delta"; it did not.

Not fixed here: regenerating it requires re-running the live comparison fetch, which this audit is
explicitly forbidden from doing. **Remedy for the next iteration:** `ConventionCheckResult.pairs`
already carries every field (`symbol`, `trading_date`, `stored_close`, `yahoo_adjusted_close`,
`relative_delta`, `within_tolerance`); the driver should serialize that tuple to a JSON artifact under
`runs/goal-market-compass-iter-<N>/` on every run before interpreting the verdict. That is a file, not a
DB write, so it stays inside AG-9's "held outside the database, never written" bound.

**B4 — OBSERVATION: `TypeError` in the mismatch reason string when every failing pair has a zero stored
close**

`j10_recovery.py:428` sets `relative_delta = None` when `stored_close` is falsy, while line 431 still
marks the pair `within_tolerance=False`. If `failing` contains ONLY such pairs, `worst.relative_delta` is
`None` and the f-string `delta={worst.relative_delta:.4%}` (line 457) raises `TypeError`. It fails
closed — the exception propagates out of `run_gated_recovery` before any write — so it is a reporting
crash, not a correctness hole. Left unfixed deliberately (OBSERVATION-level; fixing it is scope creep).

**B5 — GAP: the precommitted tolerance and documented sample are caller-overridable**

`run_gated_recovery` exposes `convention_tolerance`, `convention_sample_symbols` and
`convention_window_dates` as parameters (`j10_recovery.py:571-573`), and the real run was driven by an
ad-hoc standalone script that is not a tracked file. The literal `CONVENTION_CHECK_TOLERANCE = 0.0075`
is therefore a default, not a binding gate: a future driver can pass a wider tolerance with no code diff
to review. The developer's discipline here was exemplary (handoff lines 26-32, `assumptions.md:544-556`
— the tolerance was fixed before the run and not moved after a borderline result), which is precisely
why the *mechanism* deserves the note: the discipline currently lives in the operator, not the code.
`ConventionCheckResult.tolerance` does carry the value actually used, so recording the result object
(see B3's remedy) makes the override auditable. Flagged for the redesign: a "precommitted" threshold a
caller can silently override is a convention, not a gate.

**B6 — GAP: `data_manager` does not clamp written bar dates to the requested window**

`data_manager.py` (the `_run_chunked_fetch` insert loop) writes `bar.date` for every bar the provider
returns, filtered only by `_existing_dates(session, symbol, ws, we)` — a bar dated outside `[ws, we]`
would never appear in that set and would be inserted unconditionally. The J-10 scope guard holds anyway
because `YahooProvider._parse` filters to `[start, end]` itself, and I confirmed the symbol scope is
exact (`symbols_override` is used verbatim — `data_manager.py:5749-5750`, no union with the seed set,
dates from the job's own `RECOVERY_START`/`RECOVERY_END`). Pre-existing unchanged code, explicitly out of
this iteration's scope; noted only because the redesign introduces a *transforming* write path, where a
defence-in-depth `ws <= bar.date <= we` assertion at the insert would be cheap insurance.

### Frontend Findings

None — `Frontend Present: no`, and the iteration correctly produced no UI surface. I confirmed the
forbidden-lane rule held in both directions: `reports/phase-goal-market-compass-iter-7-ui-test-results.md`
records the browser-QA lane as SKIPPED with "No browser or Chrome MCP session was opened", the demo lane
emitted `NOT_YET` with zero steps (`phase-goal-market-compass-iter-7-demo.json`: `"steps": []`), no
`reports/qa/goal-market-compass-iter-7-evidence/` directory exists, and
`reports/qa/goal-market-compass-iter-6-evidence/` is byte-unchanged (`git status`/`git diff` clean; last
touched by commit `e58b773b`). The iter-6 depth-demotion incident did **not** recur:
`runs/goal-session-market-compass/iter-7/depth-dispatched` reads `full`, matching the spec.

### Test Findings

**T1 — IMPORTANT (fixed): no test exercised a degenerate or empty comparison sample**

The nine new tests cover the three verdicts, the never-writes property and the orchestration gate with
tight assertions (exact verdicts, exact `requested_symbols` ordering, exact stored values, `pytest.fail`
guards proving `get_daily` is never called by the check). None of them constructed a sample the DB could
not answer — which is exactly how B1 survived reviewer and QA. Every existing test seeds a stored row
for every sampled symbol, so the fail-open path had no coverage at all. Four regression tests added in
§4, including `test_convention_check_still_reports_a_genuine_mismatch_over_a_coverage_gap`, which pins
the ordering that preserves the real run's recorded `mismatch` verdict.

**T2 — GAP (not fixed): `_parse_adjusted_close` has no synthetic-payload tests**

Confirms the reviewer's MINOR issue (`yahoo_provider.py:135`). Every branch — chart `error`, missing
`result`, empty `timestamp`, absent `adjclose` block, malformed shape, null skip — is evidenced only by
a one-time, non-repeatable live probe. I traced them all by code read and they are correctly fail-closed
(`RateLimitError` subclasses `ProviderUnavailableError` at `base.py:21`, so a Yahoo 429 during the check
yields `inconclusive` rather than an escape), but "correct by inspection" is not the same as pinned.
Left unfixed: GAP-level, and the reviewer already filed it with the exact remedy.

---

## 3. Domain Assessment

The core domain judgment of this iteration is sound and, in one respect, better than the spec asked for.
The developer identified that comparing Yahoo's raw `quote.close` against the stored adjusted closes
would have produced false mismatches, verified it live before wiring anything (AAPL raw-vs-adjusted
0.0862%), and built `get_adjusted_close` as a genuinely additive method — `get_daily`'s request shape,
parsing and callers are untouched (confirmed by diff and by the 44/44 `test_provider_clients.py` run).
Both parsers derive dates identically (`datetime.fromtimestamp(ts, tz=timezone.utc).date()`), so the
comparison is date-aligned; the 76 exactly-0.0% pairs on the real run are strong empirical confirmation
of that alignment.

The causal ordering in `run_gated_recovery` is genuine: the fetch/backfill calls sit textually below an
unconditional `return` on any non-`"agree"` verdict, and every exception class I could construct —
`ProviderUnavailableError`, `RateLimitError`, a duck-typing `AttributeError` from a provider without
`get_adjusted_close`, a `TypeError` from a malformed payload — propagates out *before* those lines. The
scope guard is exact on both axes (symbols verbatim, dates from module constants). The single defect was
not in the ordering but in the *definition of the verdict itself*: the gate answered "was agreement
contradicted?" when the goal requires it to answer "was agreement positively demonstrated?". Those
coincide on a healthy dataset and diverge precisely on a damaged one.

On process discipline: the developer's refusal to move a tolerance after seeing a 0.865%-vs-0.750%
result — while simultaneously documenting, in detail, why the evidence suggests the tolerance is the
thing that is wrong — is exactly the behavior `.claude/judgment-rubrics.md` §4 and §6 ask for, and the
owner's subsequent redesign vindicates the reasoning rather than the number. That judgment is why this
audit found a fail-open in an unreached branch instead of an unjustified 1132-row write.

One honest limitation of my own coverage: I verified that the real convention run left the database
untouched and that its claimed timing is consistent with the DB's session artifacts, but the run's
per-pair outputs themselves are unverifiable (B3) — I am reporting the developer's numbers as
uncorroborated-but-uncontradicted, not as confirmed.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `apps/backend/app/engine/j10_recovery.py:460-482` | Minimum-evidence floor: `"agree"` now requires a non-empty comparison covering every sampled symbol; otherwise `"inconclusive"` with the coverage stated. Placed after the mismatch branch so a genuine out-of-tolerance pair is never downgraded. |
| 2 | Critical | `apps/backend/app/engine/j10_recovery.py:392-399` | Docstring updated to state the floor (the prior text promised a no-silent-pass property the stored-side path did not honor). |
| 3 | Critical | `apps/backend/tests/test_j10_recovery.py` (+4 tests) | `test_convention_check_is_inconclusive_when_nothing_was_actually_compared`, `..._when_a_sampled_symbol_has_no_stored_baseline`, `test_convention_check_still_reports_a_genuine_mismatch_over_a_coverage_gap`, `test_gated_recovery_never_writes_when_the_sample_proved_nothing`. |

**Post-fix verification (evidence):**

1. `cd apps/backend && .venv/bin/python -m pytest tests/test_j10_recovery.py -q` → **27 passed in 2.11s**
   (23 pre-existing, all still green, + 4 new). Single targeted file, one pytest process, per the
   resource contract.
2. Behavioral re-proof of the fixed path — the same fixture probe re-run after the fix: Q1 `agree`(0
   pairs) → `inconclusive`; Q1b default-sample `agree` → `inconclusive`; Q1c 1-pair `agree` →
   `inconclusive`; Q2 end-to-end `4 daily_prices + 2 data_provider_runs rows written` → **0 rows
   written**, `fetch reached = False`. Table in B1.
3. Diff re-read: the change is confined to one branch inserted into `check_adjustment_convention` plus
   its docstring paragraph, and four appended tests. `RECOVERY_SOURCE`, the scope guard,
   `run_bounded_recovery_fetch`, `run_bounded_recovery_backfill`, `run_gated_recovery`'s ordering, and
   `yahoo_provider.py` are untouched by this audit.
4. No new finding introduced: the new branch can only convert a former `"agree"` into `"inconclusive"` —
   strictly more conservative, no new write path, no silenced error, and the ordering test pins that a
   genuine `mismatch` still outranks it. No dev-handoff claim was invalidated (its factual claims all
   concern the real run, whose recorded `mismatch` verdict is preserved by construction), so the handoff
   was left unedited — as was `reports/qa/goal-market-compass-iter-6-evidence/` (AG-17).

**Independently re-verified, not trusted from any report (direct read-only SQL against
`apps/backend/data/trendora.db`):**

| Check | Result |
|---|---|
| `daily_prices` `MAX(date)` | `2026-08-10` ✓ |
| rows on 2026-08-11 / 2026-08-12 / anything after 2026-08-10 | `0` / `0` / `0` ✓ |
| `data_provider_runs` `MAX(id)` / `COUNT(*)` | `541` / `541` (no gaps, no new row) ✓ |
| id=541 | `stooq`, `failed`, `2026-08-20 18:00:54.819857`, `de9f…92` — iter-6's own row ✓ |
| newest `data_provider_runs.started_at` overall | `2026-08-20 18:00:54` — predates iter-7's 21:32 start ✓ |
| newest `provider='yahoo'` run | id 533, `2026-08-14` — pre-existing, nothing new ✓ |
| `next_session_manifests` `COUNT(*)` / `MAX(as_of)` | `24` / `2026-08-12` (AG-12 held) ✓ |
| `scanner_runs` `COUNT(*)` / `MAX(asof_date)` | `3118` / `2026-08-10` ✓ |

Step 5(f)'s HTTP 400 claim is entailed by that state: `scanner.py:326` emits
`"as_of … is after the latest data date {latest}"`, and `latest` is the verified `2026-08-10`. TC-12
re-verified by grep: the only occurrences of "interchangeable"/"equivalent" in the changed code and the
handoff are the explicit *dis*claimers (`j10_recovery.py:36`, `:401`).

---

## 5. Recommended Next Step

Proceed — but the next iteration must not be a straight re-run of the retry.

1. **Do not authorize any write until B2 is resolved.** The redesign (path-agreement + stable
   multiplicative bridge) must measure and insert the *same* series through *one* path. As currently
   wired, a passing gate validates `adjclose` and the restore writes `get_daily`'s raw close; a bridge
   calibrated on one and applied to the other would silently bake in the raw-vs-adjusted gap. Carry the
   B1 floor into that design: a bridge computed from zero or partial overlap must be `inconclusive`, and
   "stable" needs a stated minimum number of comparable pairs per symbol, not merely a low variance
   across whatever pairs happened to survive.
2. **Persist the per-pair evidence on every run** (B3), before interpreting the verdict — the result
   object already carries it. The next live comparison fetch is the last cheap chance to capture the
   88-pair baseline that this iteration's decisions rest on.
3. **Make the threshold and sample structurally binding** (B5) — if a driver can pass its own tolerance,
   "precommitted" is unenforceable; at minimum, record the `ConventionCheckResult.tolerance` and
   `sample_symbols` actually used into the persisted artifact from (2).
4. Optional, cheap: the reviewer's `_parse_adjusted_close` synthetic-payload tests (T2), following the
   existing `test_provider_clients.py::test_yahoo_error_payload_raises` pattern.

Two DEFINITION OF DONE items could not be closed by me and remain open for the pipeline, not for the
developer: the coherence-auditor and evaluator had not run at audit time, and DoD item 2's per-pair
recording is not met (B3) — the review report's `definition_of_done: complete` should be read with that
one exception noted.
