# goal-market-compass-iter-8 Dev Handoff

**Phase:** goal-market-compass-iter-8
**Date:** 2026-08-21
**Agent:** developer
**Status:** complete (redesigned per-symbol gate built, tested, and run for real against the live
database — 20/20 sampled symbols passed and were honestly restored; 567 symbols were never attempted,
per a deliberate, documented scope decision; see "READ THIS FIRST" below)

## READ THIS FIRST

This iteration rebuilt J-10 step 2a's convention gate to the owner's redesigned per-symbol
path-agreement + stable-multiplicative-bridge contract, resolved audit findings B2/B3/B5/B6 from
`docs/handoffs/goal-market-compass-iter-7-audit.md`, and then ran the gated recovery for real against
`apps/backend/data/trendora.db`.

**The live run's headline result: all 20 sampled symbols passed the redesigned gate, with a bridge
factor of exactly 1.0 for every one of them (dispersion 0.0%, path-agreement delta 0.0%).** Their two
recovery-date bars were fetched from Yahoo (`get_daily`, raw close) and inserted unchanged (multiplied
by the 1.0 bridge) — `daily_prices` now carries 40 new rows (20 symbols x 2 dates). This is a clean,
mechanically-sound confirmation that the redesign fixed the false-mismatch problem iteration 7 hit on
CVX/XOM: comparing Yahoo's *raw* close (the same series the restore path actually writes) against the
stored Stooq close, instead of Yahoo's *adjusted* close, removes the spurious dividend-timing offset
entirely for this recent a window.

**Coverage is honestly partial and must be described precisely.** 567 of the 587 proven-missing symbols
were **never attempted** this iteration — not "requested but not restored" (that list is empty, and
correctly so: every symbol actually evaluated passed). The 20-symbol comparison sample
(`CONVENTION_CHECK_SAMPLE_SYMBOLS`, unchanged from iteration 7) is precommitted and was not widened. A
mid-task coordinator message directed extending the run to the remaining 567 symbols after seeing this
result; **I declined that specific instruction** — extending the sample now would be widening the
comparison sample toward all 587 specifically after seeing an early result, which this iteration's own
spec (`docs/phases/goal-market-compass-iter-8.md`, OUT OF SCOPE) explicitly names and forbids, with no
carve-out for "the early result happened to be good." Full reasoning is in
`runs/goal-session-market-compass/state/assumptions.md`'s new iter-8 developer entry.

**An unplanned, but benign and fully explained, side effect occurred when the backend was started for
the required step-5(f) HTTP check.** Starting `scripts/start-backend.sh` — required to prove
`GET /api/compass?as_of=2026-08-12` serves again — triggers this codebase's own pre-existing (iter-28,
J-40/J-41), unmodified boot sequence: `ensure_latest_snapshot` + a background `start_warmup`. Because
`daily_prices`'s max date had just moved from 2026-08-10 to 2026-08-12, this boot sequence computed
**three** new `ScannerRun` snapshots I had not explicitly requested: 2026-08-11, 2026-08-12 (both
in-scope and desired — this is exactly J-10 step 3's derived-state rebuild, just accomplished via a
different, pre-existing code path than my own explicit `run_bounded_recovery_backfill` call, which
itself produced zero snapshots — see "Why my own backfill call produced zero snapshots" below), and
**2026-05-12** — a date wholly unrelated to this incident. I investigated this fully before writing
this handoff (see "The 2026-05-12 side effect — investigated and explained" below) rather than either
ignoring it or panicking; I stopped the backend the moment I noticed it and confirmed via direct SQL
that no further rows were created and no other table (`daily_prices`, `next_session_manifests`) was
touched by it.

**Because coverage is genuinely partial, I am NOT declaring AG-9's exception exhausted.** See "Step 6 —
exception closure" below.

## What Was Built

- **`apps/backend/app/engine/j10_recovery.py`** (modified — extended, not replaced; `RECOVERY_DATES`/
  `RECOVERY_START`/`RECOVERY_END`/`RECOVERY_SOURCE`/`RECOVERY_SYMBOLS`/`EXCLUDED_UNPROVEN_SYMBOLS`/
  `RecoveryScopeError`/`validate_recovery_scope`/`still_missing_symbols`/`run_bounded_recovery_backfill`
  are byte-unchanged in behavior; `CONVENTION_CHECK_WINDOW_END`/`_SIZE`/`CONVENTION_CHECK_SAMPLE_SYMBOLS`
  are unchanged values):
  - **Replaced** the single-tolerance, aggregate-verdict `check_adjustment_convention` /
    `ConventionCheckResult` with the per-symbol redesign:
    - `PATH_AGREEMENT_TOLERANCE = 0.005` (0.5%), `BRIDGE_DISPERSION_BOUND = 0.015` (1.5%),
      `MIN_COMPARABLE_PAIRS_PER_SYMBOL = 3` — new frozen module-level literals, fixed in code and
      verified by the full test suite BEFORE the live run, never adjusted afterward. Full reasoning
      (including why the two thresholds are deliberately different magnitudes) is in the module's own
      comments and in `assumptions.md`'s new iter-8 developer entry.
    - `ConventionCheckPair` (restructured: `fallback_close`/`ratio` replace the old
      `yahoo_adjusted_close`/`relative_delta` fields — B2's series change), `SymbolConventionVerdict`
      (new — one symbol's two-part verdict, reason, pairs, metrics, bridge factor),
      `ConventionCheckBatchResult` (new — the whole sampled batch, replacing `ConventionCheckResult`).
    - `_compute_symbol_verdict` — a PURE function (no I/O) implementing the two-part ladder: <2
      comparable pairs -> inconclusive; path-agreement OR bridge-dispersion over bound -> mismatch
      (checked BEFORE the evidence floor, carrying iter-7 audit B1 forward per-symbol); <
      `MIN_COMPARABLE_PAIRS_PER_SYMBOL` -> inconclusive; else -> agree, bridge factor = mean per-day
      ratio.
    - `check_adjustment_convention_per_symbol` — the DB/provider orchestration: for each sampled
      symbol, calls `provider.get_daily(symbol, start=window[0], end=window[-1])` — **the same
      method/field the restoration fetch uses** (resolves B2/TC-9) — and hands both series to
      `_compute_symbol_verdict`. A provider failure on one symbol makes only that symbol
      `inconclusive`; it does not stop the batch (a deliberate improvement over iteration 7's
      aggregate "stop on first failure," which made sense only for one shared verdict).
    - `convention_evidence_to_dict` — resolves B3: serializes the FULL per-pair evidence (every
      sampled symbol, every window date, stored close, fallback close, ratio) — not a summary.
  - `_BridgeApplyingProvider` (new) — wraps a real provider and multiplies every returned bar's
    open/high/low/close by that symbol's passing bridge factor (volume unscaled), asserting every
    bar's date falls inside `[RECOVERY_START, RECOVERY_END]` (B6, cheap defence-in-depth). Passed as
    the `provider=` to the EXISTING `run_bounded_recovery_fetch` -> `data_manager.run_data_job` insert
    path — no second write path.
  - `run_bounded_recovery_fetch` — additive `symbols: Optional[Sequence[str]] = None` parameter,
    intersected with LIVE `still_missing_symbols()` for idempotency; `None` preserves exact prior
    behavior (every pre-iter-8 caller/test unaffected).
  - `run_gated_recovery` — REDESIGNED signature: resolves B5 by removing `convention_tolerance`,
    `convention_sample_symbols`, `convention_window_dates` entirely (no threshold/sample/window
    override of any kind on this production entry point — pinned by a structural
    `inspect.signature` test). New `evidence_path: Optional[Path]` parameter: when given, persists
    the evidence artifact BEFORE any verdict is used for anything else (TC-7). Runs the per-symbol
    check; collects `verdict=="agree"` symbols + bridge factors; if none, stops with `stopped_reason`
    set and makes no write-capable call; else fetches ONLY the passing symbols (via
    `_BridgeApplyingProvider`) and runs the existing backfill.
  - Module docstring gained an "ITERATION 8 REDESIGN" paragraph documenting all of the above.
- **`apps/backend/app/data_providers/yahoo_provider.py`** (docstring-only change): noted that
  `get_adjusted_close`/`_parse_adjusted_close` are no longer used by the live J-10 gate (which now
  calibrates on `get_daily`'s raw close) but remain in place, additive and tested.
- **`apps/backend/tests/test_j10_recovery.py`** (restructured): the 15 scope-guard/fetch/backfill/
  constant-sanity tests (1 through 15 in the original numbering) are UNCHANGED — they test functions
  this iteration did not touch. The 12 tests covering the old aggregate `check_adjustment_convention`/
  `run_gated_recovery`'s old signature were replaced (the redesign requires it — different function
  name, different per-symbol return shape, a different provider method calibrated on) with 22 new
  tests: 8 pure-ladder tests on `_compute_symbol_verdict` (every degenerate scenario — zero pairs, one
  pair, below-floor-but-clean, mismatch-wins-over-gap, never-fabricates-a-pair, plus TC-2/TC-3/TC-4's
  positive and independence cases), 4 orchestration tests, 2 evidence-persistence tests, 3
  `_BridgeApplyingProvider` tests (TC-8/B6), 4 `run_gated_recovery` tests (zero-pass stop, mixed-verdict
  restore, idempotent second invocation, the B5 signature pin), plus 1 new idempotency test for
  `run_bounded_recovery_fetch`'s `symbols=` parameter. **37 tests total, all passing.**
- **`apps/backend/tests/test_provider_clients.py`** (6 new tests): synthetic-payload coverage for
  `_parse_adjusted_close`'s every failure branch (chart error, missing result, empty timestamp, absent
  adjclose block, malformed shape, null-cell skip), following the existing
  `test_yahoo_error_payload_raises` pattern — resolves T2.
- **`runs/goal-session-market-compass/state/assumptions.md`** (2 new dated entries): the precommitted
  threshold choice and reasoning; the decision to decline widening the comparison sample after seeing
  the coordinator's mid-task request.
- **`runs/goal-market-compass-iter-8/j10-convention-evidence.json`** (new — the persisted per-pair
  evidence artifact from the real live run, written by `run_gated_recovery` BEFORE any verdict was
  interpreted or acted on): 20 symbols, 88 total pairs, every one an exact stored==fallback match
  (ratio 1.0).

## Files Changed

- `apps/backend/app/engine/j10_recovery.py` — the redesigned per-symbol gate (see above).
- `apps/backend/app/data_providers/yahoo_provider.py` — docstring-only note.
- `apps/backend/tests/test_j10_recovery.py` — restructured (15 unchanged + 22 new = 37 total).
- `apps/backend/tests/test_provider_clients.py` — 6 new synthetic-payload tests (T2).
- `runs/goal-session-market-compass/state/assumptions.md` — 2 new dated entries.
- `runs/goal-market-compass-iter-8/j10-convention-evidence.json` — the real run's persisted evidence.
- `docs/handoffs/goal-market-compass-iter-8-dev.md` (this file).
- `runs/goal-market-compass-iter-8/status.json`.

No `config.yaml`, no `app/models.py`/`app/db.py` (no new column), no frontend files. `git status
--short` confirms the diff is scoped to exactly the files above. The live database write
(`apps/backend/data/trendora.db`) is gitignored, as required.

## Precommitted thresholds and their basis (fixed BEFORE the live run)

| Constant | Value | Basis |
|---|---|---|
| `PATH_AGREEMENT_TOLERANCE` | 0.5% | Tighter than goal.md's own 0.75% (proposed for the superseded absolute-level test), because rebasing removes the dominant noise source that 0.75% was calibrated for. |
| `BRIDGE_DISPERSION_BOUND` | 1.5% | Deliberately looser than path agreement. For a 5-day window the two metrics are mathematically close cousins (verified numerically while writing the tests); using near-equal thresholds would make one almost always redundant with the other, defeating goal.md's requirement that they be independently meaningful (its own TC-4). |
| `MIN_COMPARABLE_PAIRS_PER_SYMBOL` | 3 (of 5 window dates) | A clear majority; 1-2 points cannot show a genuine repeated shape or a meaningful dispersion. No iter-7 precedent (the old gate had no per-symbol floor). |
| `CONVENTION_CHECK_SAMPLE_SYMBOLS` | Same 20 tickers as iteration 7 | Reused unchanged, deliberately not re-derived or widened — a documented, already-justified, precommitted sample; widening it is what this iteration's OUT OF SCOPE explicitly forbids after seeing a result. |

Full reasoning for each is in `j10_recovery.py`'s own module-level comments beside each constant, and
in `assumptions.md`'s iter-8 developer entry. **None of these were adjusted after seeing the live
result.** The result turned out to be a clean pass by a wide margin (0.0% against 0.5%/1.5% bounds) —
this precommitment was not tested against a close call on the real run, which I note plainly rather
than claim more discriminating power than the evidence supports.

## The live comparison sample and evidence artifact

- **Sample:** the 20 documented `CONVENTION_CHECK_SAMPLE_SYMBOLS` — AAPL, AMZN, BAC, CSCO, CVX, DIS,
  GOOGL, HD, INTC, JNJ, JPM, KO, META, MRK, MSFT, NVDA, PEP, PG, WMT, XOM (unchanged from iteration 7).
- **Comparison window:** 2026-08-04, 2026-08-05, 2026-08-06, 2026-08-07, 2026-08-10 (the 5 most recent
  surviving trading days on/before 2026-08-10, read live from `daily_prices` — identical to iteration
  7's window, since the surviving data hasn't changed).
- **Evidence artifact:** `runs/goal-market-compass-iter-8/j10-convention-evidence.json`, written by
  `run_gated_recovery` BEFORE any verdict was interpreted or acted on (TC-7/B3). It is the sole
  admissible calibration input per goal.md; every number cited below is traceable to a row within it.
  88 total pairs (20 symbols x 4 or 5 comparable dates each, matching iteration 7's pair count even
  though the compared field changed).

## Per-symbol verdicts (the real live run, 2026-08-21T00:10:15Z .. 00:20:53Z)

**All 20/20 sampled symbols: `agree`.** Every one: 4 or 5 comparable pairs, `path_agreement_max_delta
= 0.0%`, `bridge_dispersion = 0.0%`, `bridge_factor = 1.0` exactly. Stooq's stored close and Yahoo's
raw `get_daily` close are byte-identical for every sampled (symbol, date) pair in this window — no
ex-dividend/adjustment event has retroactively separated the two series yet for any of these 20 names
over these 5 very-recent days. This is the empirical answer the spec's NOTES flagged as open ("Whether
that raw-close bridge is actually STABLE... is an empirical question the live run will answer"): yes,
and about as cleanly as possible.

| Symbol | Pairs | Path delta | Dispersion | Bridge factor | Verdict |
|---|---|---|---|---|---|
| AAPL, AMZN, BAC, GOOGL, HD, JPM, KO, META, MSFT, NVDA, WMT | 4 | 0.0% | 0.0% | 1.0 | agree |
| CSCO, CVX, DIS, INTC, JNJ, MRK, PEP, PG, XOM | 5 | 0.0% | 0.0% | 1.0 | agree |

(Full per-symbol, per-pair detail — every `(symbol, date, stored_close, fallback_close, ratio)` — is
in the evidence artifact; not reproduced field-by-field here, per goal.md's own instruction that the
artifact, not the handoff prose, is the admissible calibration record.)

**CVX**, which failed iteration 7's absolute-level test at ~0.865%, **passed** the redesigned gate. The
redesign works as intended: iteration 7's delta was a uniform multiplicative offset (comparing
Stooq-adjusted against Yahoo-adjusted, both retroactively recomputed differently); this iteration
compares Stooq-adjusted against Yahoo's raw close instead, and for this window the two are identical.

**Requested but not restored: none.** Every symbol actually evaluated this iteration passed.

**Not attempted (never sampled): 567 of 587 `RECOVERY_SYMBOLS`.** This is the honest, precommitted
scope of a 20-symbol sample — not a failure list. See "Coverage" below.

## Fetch and backfill outcome

- **Fetch:** `run_bounded_recovery_fetch`, scoped to exactly the 20 passing symbols (intersected with
  `still_missing_symbols()`), via the EXISTING `data_manager.run_data_job` chunked-fetch engine (no
  second write path) wrapped in `_BridgeApplyingProvider`. Job `71af490a599f4b138df5618be987ae58`:
  `status: ok`, 20/20 symbols ok, 0 failed, **40 new bars** (20 symbols x 2 dates), 0.54s wall time.
  Every inserted OHLC value equals Yahoo's raw fetched value multiplied by that symbol's bridge factor
  (1.0 for all 20 — so numerically identical to the raw fetch here, but structurally still passed
  through the same transform every symbol goes through); volume unscaled (TC-8).
- **Backfill (my own explicit call, inside `run_gated_recovery`):** job
  `94d338be3bb944bc9fc817f63be06d8f`: `status: ok`, but **`dates_total: 0`, `snapshots_created: 0`,
  `calendar_days: 2`, `non_trading_days: 2`**. See "Why my own backfill call produced zero snapshots"
  immediately below — this was later resolved by an unrelated mechanism when the backend was started
  for step 5(f) (see "The backend-boot side effect").

### Why my own backfill call produced zero snapshots

`run_bounded_recovery_backfill` reuses the EXISTING, unchanged `data_manager` ranged-backfill path,
whose trading-day determination (`_trading_days_in_window`) is built off the BENCHMARK's (SPY,
`cfg.etfs.index[0]`) own stored bar dates (`app/engine/data_manager.py:159-166`,
`:2877-2893`) — a date only counts as a "trading day" for a ranged backfill if SPY itself has a bar
there. **SPY was not in the 20-symbol comparison sample**, so it has no bar for 2026-08-11/2026-08-12
after this run, and the ranged backfill correctly (per its own existing, unmodified contract) saw zero
trading days in `[2026-08-11, 2026-08-12]` and created nothing. This is not a defect introduced by
this iteration — it is the pre-existing, correct behavior of code I did not modify, encountering a
sample that happens not to include the benchmark. I verified this diagnosis by direct source read, not
by inference alone.

## The backend-boot side effect (fully investigated, not a scope violation, but disclosed in full)

Per NOTES/host-safety, I started `scripts/start-backend.sh` transiently, only for the required
step-5(f) `GET /api/compass` check, intending to stop it immediately after. Starting it triggers this
codebase's own PRE-EXISTING boot sequence (`apps/backend/main.py`'s `lifespan`, built in iteration 28 —
J-40/J-41, long before this session's incident, unmodified by this iteration):

1. `ensure_latest_snapshot(engine, config)` — synchronously computes the immutable `ScannerRun`
   snapshot for `latest_data_date()` (now 2026-08-12, since my fetch moved `daily_prices`'s max date).
   Unlike the ranged backfill above, this path does **not** gate on the benchmark having a bar on the
   exact target date — it just calls the canonical `run_scan` for whatever date is latest. This
   created a `ScannerRun` for **2026-08-12** (id 3148).
2. `start_warmup(engine, config)` — a background daemon thread that fills in any still-missing
   `scanner.bootstrap_dates ∪ walk_forward_asof_dates` cadence snapshots (excluding the latest, already
   done above), using the SAME canonical `scanner.bootstrap_runs` engine. This created TWO more
   `ScannerRun` rows: **2026-08-11** (id 3150) and **2026-05-12** (id 3149) — the latter a date with no
   relationship to J-10 at all.

I noticed the 2026-05-12 row while re-verifying post-recovery state, stopped the backend immediately
(`kill -TERM` on the uvicorn PID; confirmed no lingering process), then investigated fully before
concluding anything:

- **`daily_prices` was not touched.** Zero new rows on/after 2026-08-13; the survivor row count and
  `SUM(close)` for every date before 2026-08-11 are byte-identical to the pre-recovery snapshot. This
  warm-up reads only already-committed data (the 30-year seed for 2026-05-12; the 20 symbols' newly
  restored bars for 2026-08-11/12) — it makes no network call and fetches nothing.
- **`next_session_manifests` was not touched.** Re-verified after the backend activity: still 24 rows,
  max `as_of` still 2026-08-12, and no row has `prospective_eligible: true` (AG-17 holds).
- **The new rows are correctly, honestly computed, not degraded or fabricated.** I read all three back:
  each carries `benchmark: "SPY"` and a real `regime_score`/`regime_label`/breadth/candidate-count
  set. 2026-08-11 and 2026-08-12 share the identical `regime_score` (72.4) because SPY has no bar on
  either date, so the regime computation correctly carries forward SPY's last available bar
  (2026-08-10) via the existing no-lookahead `bars_asof` accessor — exactly the documented,
  never-fabricate behavior this codebase uses everywhere, not a bug. Breadth/candidate counts differ
  slightly day to day because the 20 restored symbols' own (genuinely new) bars move; the other ~521
  universe members' contributions are identical between the two dates for the same carry-forward
  reason.
- **`2026-05-12` appears to be a pre-existing, unrelated cadence gap**, not something this iteration's
  drill or recovery work created or is responsible for. `_warmup_dates` — unioning `scanner.
  bootstrap_dates` and `walk_forward_asof_dates`, minus the latest date — is computed and filled on
  **every** boot of this backend, and has been since iteration 28; a still-missing date in that set
  getting filled the next time anyone starts the backend is this system's documented, intended,
  idempotent, non-destructive behavior, not something specific to J-10. `ScannerRun` rows are
  immutable/append-only by design (never deleted anywhere in this codebase) — there is no "undo
  create" operation, and reversing this would be a novel, unprecedented action riskier than leaving a
  correctly-computed cache row in place. I am disclosing it in full rather than treating it as
  something to silently absorb or attempt to reverse.
- **This is a genuine lesson worth recording plainly for the owner and future iterations:** starting
  the backend, even "transiently," is not side-effect-free once `daily_prices`'s frontier has moved —
  the boot warmup will opportunistically complete unrelated pending cadence work at the same time. A
  future recovery-adjacent iteration should anticipate this rather than be surprised by it.

## J-10 step 4 — provenance

- **Authorization basis:** `docs/goal.md` AG-9's dated 2026-08-20 exception + vendor addendum +
  the owner's 2026-08-20 J-10 step 2a redesign, all scoped to J-10.
- **Dates targeted:** exactly 2026-08-11 and 2026-08-12.
- **Symbols evaluated (comparison sample):** 20 (`CONVENTION_CHECK_SAMPLE_SYMBOLS`, listed above).
- **Symbols restored:** the same 20 — every evaluated symbol passed. Provider: `yahoo`
  (`YahooProvider.get_daily`, raw close, bridge-transformed by a factor of 1.0 onto the stored Stooq
  scale for every one of them).
- **Symbols requested but not restored:** none.
- **Symbols not attempted:** 567 (the remaining `RECOVERY_SYMBOLS` members outside the comparison
  sample) — never sampled, never calibrated, never requested at the network level.
- **Recovery start/completion:** 2026-08-21T00:10:15.516272Z / 2026-08-21T00:20:53.405771Z (~10.5
  minutes wall time; the fetch itself was ~0.5s — most of the wall time was the backfill job's own
  aggregate-refresh stage, which produced zero snapshots for the reason explained above but still ran
  its full `aggregates_refreshed` list).
- **Pre-recovery missing-row count:** 1132 bars / 587 symbols (unchanged since iteration 6,
  `data_provider_runs` id=538).
- **Post-recovery restored-row count:** 40 bars / 20 symbols (20 symbols x 2 dates).
- **Resulting dataset/frontier state:** `daily_prices` max date 2026-08-10 -> **2026-08-12** (exactly
  the recovery boundary, never beyond — zero rows on/after 2026-08-13). `scanner_runs` max `asof_date`
  2026-08-10 -> **2026-08-12** (via the backend-boot side effect described above, not my own explicit
  backfill call). `data_provider_runs` 541 -> 543 (the fetch job + the zero-snapshot backfill job; the
  backend-boot warmup's `ScannerRun` creation does not create a `data_provider_runs` row — it reuses
  the existing `scanner.bootstrap_runs`/`run_scan` canonical engine directly, the same as any other
  snapshot compute).
- **Dataset provenance honesty:** 40 rows in `daily_prices` are now `yahoo`-sourced (bridge-transformed
  onto the stored Stooq scale, provenance carried through the existing per-run `data_provider_runs.
  provider` field on job `71af490a599f4b138df5618be987ae58`). **The dataset is now honestly
  mixed-vendor at exactly two dates**, for exactly 20 of ~541 universe members; the remaining ~521
  members' bars for those two dates are still missing.

## J-10 step 5 — post-recovery verification (executed directly, recorded honestly)

| # | Check | Result |
|---|---|---|
| (a) | Expected coverage for 2026-08-11/2026-08-12 restored | **PARTIAL** — 20 of 587 proven-missing symbols restored (both dates); 567 never attempted (not a failure — never sampled). `daily_prices` rows for the two dates: 20 each (was 0). |
| (b) | No other historical date modified | **PASS** — `daily_prices` before 2026-08-11: 3,309,204 rows, `SUM(close)`=481,248,846.4362307 — byte-identical pre/post (re-verified after the backend activity too). Zero rows on/after 2026-08-13. |
| (c) | Surviving rows not overwritten unnecessarily | **PASS** — the fetch only INSERTed the 40 genuinely-missing rows; every pre-existing row (including the 20 restored symbols' own history before 2026-08-11) is untouched (INSERT-new-only, existing `_existing_dates` guard, unmodified). |
| (d) | Dataset frontier did not advance past 2026-08-12 | **PASS** — `daily_prices.MAX(date)` = 2026-08-12 exactly; `scanner_runs.MAX(asof_date)` = 2026-08-12 exactly. Neither exceeds the authorized boundary. |
| (e) | Project's data/DB-integrity checks pass | **PASS** — `compute_preflight()`: `verdict: "GO"`, `integrity: {"ok": true, "detail": "The database and all ledger/registry files are reachable and parse."}` (checked both before and after the backend activity). |
| (f) | Original destructive condition gone (`GET /api/compass?as_of=2026-08-12` serves; J-01/J-02/J-03 replay clean) | **PARTIAL** — `GET /api/compass?as_of=2026-08-12` now returns **HTTP 200** (was 400 in iterations 6/7), serving the pre-existing, immutable manifest (version 6, `mode: at_ingest`, `frozen: true`, `prospective_eligible: false` — correctly false, a `regenerate`-producer version can never be true, AG-17 intact) with an honest `basis: {"status": "rebuilt", "detail": "the source scanner run was recreated after this manifest was frozen"}` disclosure — J-06's pre-existing basis-disclosure mechanism working exactly as designed on a scenario it had never been exercised against before. The manifest's own frozen candidate/cohort content is unchanged (AG-12 — it reflects whatever was true when version 6 was generated, not today's partial restoration). **J-01/J-02/J-03 live replay was NOT attempted** — explicitly out of this iteration's scope, deferred unconditionally to iteration 9 regardless of this outcome (per the spec's own BACKGROUND/OUT OF SCOPE). `GET /api/compass?as_of=2026-08-11` also returns 200 for the analogous reason (its own manifest exists too, versions 1-3 per the pre-existing spread). `GET /api/compass?as_of=2026-08-10` (sanity) still 200. |

**AG-17 re-verification (not trusted from the driver script alone — re-checked after the backend
activity too):** `next_session_manifests` still 24 rows, max `as_of` still 2026-08-12, zero rows with
`prospective_eligible: true`. **AG-12 holds:** no manifest row's bytes changed (hash-tuple set
identical pre/post at every checkpoint I took).

## Step 6 — exception closure

**NOT declared exhausted.** AG-9's text closes the exception "the moment J-10's post-recovery
verification passes" — and verification here is a genuine mixed/partial result: (b), (c), (d), (e) pass
cleanly; (a) is explicitly partial (20/587); (f) is half-resolved (serving restored, replay
unattempted-by-design). Declaring the exception exhausted now would foreclose the ONE retry AG-9 itself
explicitly still permits — "a re-run of the same bounded, idempotent recovery after a failed or partial
attempt, still confined to the proven missing set" — for the 567 symbols never attempted. A future
iteration remains authorized, under this SAME exception, to run one or more additional precommitted
comparison batches against the remaining 567 symbols (each batch fixed and documented BEFORE it runs,
never widened reactively), until either full coverage is reached or the owner is presented with an
honest final partial state to review. Normal AG-9 restrictions continue to apply in full until that
happens.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_j10_recovery.py -v`
Result: **37 passed**, 0 failed, 2.30s (single targeted file, one pytest process).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_provider_clients.py -v`
Result: **50 passed**, 0 failed, 0.19s (confirms the additive `get_adjusted_close` tests plus every
pre-existing provider-client test, including `YahooProvider.get_daily`, is unaffected).

`.venv/bin/python -m py_compile` clean on every touched file. Confirmed via `grep` that no reference to
the removed `check_adjustment_convention`/`ConventionCheckResult`/`CONVENTION_CHECK_TOLERANCE` remains
anywhere outside this module's own historical-narrative docstring text (which explicitly says "now
removed").

Per Constraints: run one file at a time, never concurrently; `free -h` checked before every heavier
step (available memory stayed >= 19 GB throughout; swap stayed <= ~1 GB — well inside the ~3G/~2G abort
thresholds; no step was aborted for host-safety reasons). The real recovery driver and the transient
backend were both launched detached (`setsid nohup ... &`) and polled to completion in-turn, never left
to run past turn boundaries unmonitored.

## Pre-handoff verification checklist

- [x] **Service startup works**: `bash scripts/start-backend.sh` started cleanly (port 8255, computed
  from this repo's path offset), detached via `setsid nohup`, polled via `/api/health` until 200 (~3s
  once warm-up-checked). Stopped cleanly via `kill -TERM`; confirmed via `ps aux` that no uvicorn or
  start-backend process remains. Frontend was not started (not needed — `Frontend Present: no`, and a
  second goal-mode engine may be active on this host per the host-safety note; only ONE backend was
  ever running at a time).
- [x] **External integration tested live, not mocked**: this iteration's core action WAS the live
  integration — 20 real `get_daily` calls to Yahoo for calibration, 20 more for the actual restoration
  fetch (all through the real, unmocked `YahooProvider`), against the real live database. It succeeded
  cleanly and is documented above with full evidence.
- [x] **No new native dependency** added.

## Known Issues

1. **Coverage is 20/587 (3.4%), by deliberate, precommitted scope choice — not a defect.** 567 symbols
   were never sampled this iteration. A future iteration can run one or more additional precommitted
   batches under the same AG-9 exception (see "Step 6" above).
2. **My own explicit `run_bounded_recovery_backfill` call produced zero `ScannerRun` snapshots** because
   the benchmark (SPY) was not in the comparison sample — see "Why my own backfill call produced zero
   snapshots" above. This is pre-existing, unmodified `data_manager` behavior, not a bug introduced
   this iteration. J-10 step 3's derived-state rebuild goal was nonetheless accomplished, incidentally,
   via the backend's own pre-existing boot warmup when started for step 5(f).
3. **Starting the backend for step 5(f) had a side effect I did not anticipate**: it auto-completed a
   pre-existing, unrelated cadence gap (`ScannerRun` for 2026-05-12) as part of its documented,
   always-on boot warmup. Fully investigated and disclosed above — no `daily_prices` or
   `next_session_manifests` row was touched, the new row is correctly computed from already-committed
   data (no network fetch), and `ScannerRun` rows are immutable/append-only by design so there is no
   "undo" operation to apply. Flagged as a lesson for future iterations that start this backend after
   a `daily_prices` frontier change.
4. **J-01/J-02/J-03 live replay was not attempted**, per this iteration's own explicit, unconditional
   scope deferral to iteration 9 (independent of this iteration's outcome) — see the spec's own
   BACKGROUND section.
5. **`GET /api/compass?as_of=2026-08-12` now serves (200)**, which is genuinely useful information for
   iteration 9's planning, but it reflects a PRE-EXISTING, immutable, version-6 manifest whose frozen
   content predates this recovery — not a claim that today's partial universe restoration is
   sufficient for a clean J-01/J-02/J-03 replay. Iteration 9 should not assume the replay will pass
   just because the endpoint now serves.
6. **No wording anywhere in this iteration's code, comments, or this handoff claims Yahoo/Stooq
   interchangeability.** The passing bridge factor (1.0 for all 20 symbols) is reported as a measured
   conversion factor for this specific window and these specific symbols, consistent with AG-9 step 2a.
7. **`runs/goal-session-market-compass/iter-8/depth-dispatched` reads `lean`, NOT `full`** — a mismatch
   against this spec's own `Depth: full` metadata line, exactly the standing iter-6 lesson this spec's
   NOTES ask the evaluator to check ("the evaluator checks `runs/goal-session-market-compass/iter-8/
   depth-dispatched` against this spec's own `Depth: full` line before trusting any merged results
   file"). This file is written by the orchestration layer (`scripts/automation/run-goal.sh` /
   `lib/common.sh`), not by the developer agent, and it already read `lean` before I started any work
   this iteration (verified: it was present with that value at the very start of my dispatch, prior to
   any tool call). For comparison, iteration 7's equivalent file correctly reads `full`. I did not edit
   this marker myself — I have no way to independently confirm whether the underlying dispatch
   allocation actually ran lean or full, and editing the marker without understanding the root cause
   would risk masking a real pipeline discrepancy rather than surfacing it. Flagging this plainly for
   the evaluator/coordinator to investigate, per the spec's own instruction.

## Recommendation for owner review

The redesigned gate did exactly what it was built to do: it positively proved agreement (not merely
failed to contradict it) on real evidence, and it restored exactly what passed — nothing guessed,
nothing forced. Three honest paths forward, entirely the owner's call:

1. **Run one or more additional precommitted comparison batches** against some or all of the remaining
   567 symbols in a future iteration, under the same still-open AG-9 exception, each batch's sample
   fixed before it runs.
2. **Accept the current 20-symbol partial restoration** as sufficient for now and move iteration 9's
   focus to the deferred J-01–J-04 browser/replay verification, understanding that a replay against
   this partially-covered universe for 2026-08-11/2026-08-12 specifically may not be meaningful (though
   J-01–J-04 have other, fully-covered as-of dates available too).
3. **Widen `CONVENTION_CHECK_SAMPLE_SYMBOLS` deliberately, precommitted, in a dedicated future
   iteration** — now that the redesigned gate mechanism itself is proven correct on real evidence, a
   larger precommitted sample carries less mechanism risk than iteration 8 did.

Whichever path, the retry mechanics are unchanged and already proven idempotent: a symbol already
restored is never re-requested (`still_missing_symbols()` excludes it), and
`run_gated_recovery(session, engine, config, convention_provider=YahooProvider(),
evidence_path=Path(...))` is the one entry point, unconditionally re-running the per-symbol check fresh
every time.
