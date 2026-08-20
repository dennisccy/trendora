# goal-market-compass-iter-7 Dev Handoff

**Phase:** goal-market-compass-iter-7
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete (vendor swapped to `yahoo`; the new fail-closed adjustment-convention gate was
built, tested, and run for real against the live database — it correctly returned **mismatch** on
real evidence and correctly stopped before any write. Zero database side effects; zero scope
violations. See "READ THIS FIRST" below.)

## READ THIS FIRST — the convention gate worked exactly as designed and correctly refused to write

This iteration swapped `RECOVERY_SOURCE` from `"stooq"` to `"yahoo"` and built J-10 step 2a's new
fail-closed adjustment-convention check (`check_adjustment_convention`) plus the causal-ordering
orchestrator (`run_gated_recovery`) that makes the check a genuine, structurally-enforced gate — no
code path can reach `run_bounded_recovery_fetch`/`run_bounded_recovery_backfill` on any verdict other
than `"agree"`.

**The real run against the live database returned `mismatch`.** 88 sampled (symbol, date) pairs were
compared (20 large-cap `RECOVERY_SYMBOLS` tickers x the 5 most recent surviving trading days,
2026-08-04..2026-08-10). 76 pairs matched Stooq's stored close exactly (relative delta 0.0). XOM's 4
pairs all showed a uniform ~0.6433% delta (within the 0.75% tolerance). **CVX's 5 pairs all showed a
uniform ~0.8652% delta — just over the 0.75% tolerance**, with a spread of only ~0.00004 percentage
points across five independent trading days (the signature of one real, proportionally-applied
dividend adjustment, not noise). This is genuinely persuasive evidence that Yahoo's `adjclose`
convention matches Stooq's, and that 0.75% is simply tighter than CVX's actual quarterly-dividend
magnitude — **but I did not adjust the tolerance after seeing this result.** `CONVENTION_CHECK_TOLERANCE`
was fixed at goal.md's own proposed default (0.75%) in code before any real-DB run; changing it now,
however well-reasoned the justification, would be indistinguishable in process terms from the exact
"loosen a failing tolerance to force a pass" anti-pattern the spec explicitly forbids. See
`runs/goal-session-market-compass/state/assumptions.md`'s new iter-7 developer entry for the full
reasoning.

**What this means concretely:**
- `daily_prices` still has **zero** rows for 2026-08-11/2026-08-12 (unchanged) — max date is still
  2026-08-10. `run_bounded_recovery_fetch`/`run_bounded_recovery_backfill` were **never called**.
- `GET /api/compass?as_of=2026-08-11` and `?as_of=2026-08-12` both still return **HTTP 400**
  (byte-identical error message to the pre-iteration state).
- **Zero unintended side effects.** All 24 `next_session_manifests` rows are unchanged (same count,
  same `MAX(as_of)`, every `content_hash`/`manifest_hash` value re-verified); `data_provider_runs`
  `MAX(id)` is still 541 — the SAME row iter-6 recorded (verified field-for-field), proving no new
  provider-run row was created (structurally impossible anyway: the convention check never calls
  `data_manager.create_job`/`run_data_job`); `daily_prices`/`scanner_runs` outside the recovery window
  are unchanged (aggregate count/sum checks below).
- **AG-9's exception is NOT exhausted** — it closes only "the moment J-10's post-recovery verification
  passes," and verification did not pass. It remains open for exactly its one permitted use: a re-run
  of this same bounded, idempotent recovery.
- Neither Stooq nor a third vendor was attempted, per the explicit instruction not to.
- **This needs owner input.** See "Recommendation for owner review" at the end.

## What Was Built

- **`apps/backend/app/engine/j10_recovery.py`** (modified — extended, not replaced):
  - `RECOVERY_SOURCE` changed from `"stooq"` to `"yahoo"` (a literal-constant swap, per the iter-6
    lesson). Stooq is now rejected by `validate_recovery_scope`; a third vendor is still out of scope.
  - Module docstring gained an "ITERATION 7 RETRY" paragraph documenting the Stooq block, the vendor
    swap, and the new gate — including an explicit non-interchangeability disclaimer.
  - New frozen literals: `CONVENTION_CHECK_WINDOW_END` (2026-08-10), `CONVENTION_CHECK_WINDOW_SIZE`
    (5), `CONVENTION_CHECK_TOLERANCE` (0.0075), `CONVENTION_CHECK_SAMPLE_SYMBOLS` (20 documented
    tickers, a tuple, all verified `RECOVERY_SYMBOLS` members, MNST-free, duplicate-free).
  - `ConventionCheckPair` / `ConventionCheckResult` (frozen dataclasses) — the evidenced per-pair and
    overall return shape.
  - `_convention_check_window_dates(session)` — read-only, live query for the comparison window.
  - `_stored_closes(session, symbols, dates)` — a small, column-projected select (AG-8).
  - `check_adjustment_convention(session, *, provider, sample_symbols=None, window_dates=None,
    tolerance=CONVENTION_CHECK_TOLERANCE)` — J-10 step 2a's gate. One `get_adjusted_close` call per
    sampled symbol (never per pair); a provider failure on any symbol makes the whole verdict
    `"inconclusive"` and stops further fetches; otherwise every pair is compared (never short-circuits
    on the first mismatch, so every pair's delta is recorded) and `"mismatch"` fires if any pair
    exceeds tolerance; `"agree"` only if every sampled symbol was fetched and every pair is within
    tolerance. Never writes to any table.
  - `GatedRecoveryOutcome` / `run_gated_recovery(...)` — the ONE J-10 retry entry point: runs the
    convention check FIRST; only `verdict == "agree"` reaches `run_bounded_recovery_fetch` +
    `run_bounded_recovery_backfill`. This is a textual and causal gate — the fetch/backfill calls sit
    inside the `if check.verdict != "agree": return ...` branch's fallthrough, so no code path below
    the verdict check can reach them on a non-agree verdict.
- **`apps/backend/app/data_providers/yahoo_provider.py`** (modified — additive only):
  - New method `get_adjusted_close(symbol, start=None, end=None) -> dict[date, float]` — fetches
    Yahoo's split/dividend-**adjusted** close series (`indicators.adjclose[0].adjclose`), confirmed
    live to be present in the SAME chart response `get_daily` already requests (no extra query
    parameter needed — verified by direct inspection of a real response, see "Technical verification"
    below). Raises `ProviderUnavailableError` (never falls back to raw close) if the response carries
    no `adjclose` block at all. `get_daily`'s own contract, request shape, and callers are **unchanged**.
- **`apps/backend/tests/test_j10_recovery.py`** (modified): updated `test_rejects_wrong_source`
  (now asserts `"stooq"` is rejected) and `test_recovery_constants_shape`
  (`RECOVERY_SOURCE == "yahoo"`); added 9 new fixture-scoped tests for the convention check's three
  verdicts and the orchestration gate, using an injected fake provider — zero live network calls in
  the automated suite.

## Files Changed

- `apps/backend/app/engine/j10_recovery.py` — vendor swap + convention-check gate + orchestrator (see above).
- `apps/backend/app/data_providers/yahoo_provider.py` — additive `get_adjusted_close` capability.
- `apps/backend/tests/test_j10_recovery.py` — updated 2 tests, added 9 new tests (23 total, all passing).
- `runs/goal-session-market-compass/state/assumptions.md` — one new dated entry (the tolerance
  discipline judgment call).
- `docs/handoffs/goal-market-compass-iter-7-dev.md` (this file).

No `config.yaml`, no `app/models.py`/`app/db.py` (no new column), no frontend files, no other
`app/engine/*` module was touched — confirmed via `git status --short`, scoped to exactly these
three source files plus the assumption ledger and this handoff.

## Technical verification: `get_adjusted_close` fetches the right field

Direct live probe (`AAPL`, 2026-08-04..2026-08-10, read-only, no DB involved) before wiring it into
the gate:

| date | raw `quote.close` (`get_daily`) | `adjclose` (`get_adjusted_close`) | relative delta |
|---|---|---|---|
| 2026-08-04 | 309.3800048828125 | 309.1134033203125 | 0.0862% |
| 2026-08-05 | 311.0 | 310.7320251464844 | 0.0862% |
| 2026-08-06 | 312.4100036621094 | 312.14080810546875 | 0.0862% |
| 2026-08-07 | 313.3299865722656 | 313.05999755859375 | 0.0862% |
| 2026-08-10 | 308.260009765625 | 308.260009765625 | 0.0% |

This confirms (a) the two Yahoo fields genuinely diverge — the load-bearing technical finding in the
spec's NOTES is real, not theoretical, and comparing the wrong field would have been a live bug; (b)
`indicators.adjclose` is present in Yahoo's default chart response with no extra query parameter,
which is why `get_adjusted_close` reuses the exact same request shape as `get_daily`; (c) the observed
raw-vs-adjusted gap for a very recent bar (AAPL, ~9 days old) is small (~0.086%), consistent with a
single intervening ex-dividend date rather than a stale/garbled field.

**Known, deliberate limitation carried forward (not this iteration's to fix):** `run_bounded_recovery_fetch`
still uses the existing, unchanged `get_daily` (raw `quote.close`) for the actual restore — per the
spec's explicit, repeated "existing (unchanged)" instruction. This means that *if* a future retry's
convention check passes, the restored 2026-08-11/2026-08-12 rows will carry Yahoo's raw close, not its
adjusted close. Because the recovery dates are only ~8-9 days before any realistic fetch time, the
raw-vs-adjusted gap for that specific 2-day window is expected to be small for most symbols (the same
order of magnitude as the convention-check tolerance itself, per the AAPL probe above) — but this was
not independently re-verified for the recovery dates themselves (doing so would mean an extra live
fetch beyond what this iteration executed). Flagged for the reviewer/auditor and for whoever runs a
future retry; not a defect in this iteration's own scope, since I built to the spec exactly as written.

## J-10 step-by-step account

### Step 1 — Missing-set derivation

Unchanged from iter-6 (`RECOVERY_SYMBOLS`, 587 symbols, MNST excluded) — re-verified read-only this
iteration: `daily_prices` still has 0 rows for 2026-08-11/2026-08-12 (confirmed by direct query, see
Step 5 table), so the missing set is unchanged and `still_missing_symbols()` still returns all 587.

### Step 2 — The bounded fetch — **NOT executed** (correctly gated off by step 2a)

`run_bounded_recovery_fetch` was never called. This is not an oversight — `run_gated_recovery`'s own
code structure makes it structurally unreachable once step 2a returns a non-`"agree"` verdict.

### Step 2a — The adjustment-convention check — **executed against the real live database**

Ran `check_adjustment_convention(session, provider=YahooProvider())` via a standalone driver script
(direct `Session`/`Engine` calls into `app.db.get_engine()`/`app.config.get_config()` — the same live
DB file, no copy, no second connection mechanism; mirrors iter-6's own driver pattern). No backend was
running for this step.

- **Sample:** the 20 documented `CONVENTION_CHECK_SAMPLE_SYMBOLS` — AAPL, AMZN, BAC, CSCO, CVX, DIS,
  GOOGL, HD, INTC, JNJ, JPM, KO, META, MRK, MSFT, NVDA, PEP, PG, WMT, XOM.
- **Comparison window:** the 5 most recent trading days already stored in `daily_prices` on or before
  2026-08-10 — 2026-08-04, 2026-08-05, 2026-08-06, 2026-08-07, 2026-08-10 (read live via
  `_convention_check_window_dates`, not hardcoded).
- **Pairs compared:** 88 of the possible 100 (20 symbols x 5 dates) — 12 (symbol, date) combinations
  had no comparable stored baseline (a pre-existing, benign per-symbol data-availability gap on
  specific dates within the window, unrelated to J-10; the check correctly skipped these rather than
  fabricating a comparison — see `check_adjustment_convention`'s own contract).
- **Verdict: `mismatch`.** Full per-pair evidence (every symbol's every date, `stored_close`,
  `yahoo_adjusted_close`, `relative_delta`, `within_tolerance`) is preserved in the run artifact; the
  summary by symbol showing a nonzero delta:

  | symbol | pairs | delta (min .. max) | within 0.75% tolerance |
  |---|---|---|---|
  | AAPL | 4 | 0.08617% .. 0.08617% | yes |
  | XOM | 4 | 0.64334% .. 0.64335% | yes |
  | CVX | 5 | 0.86517% .. 0.86517% | **no** |
  | (all other 16 symbols) | 76 pairs | 0.0% (exact match) | yes |

  Tolerance basis and empirical deltas (per NOTES' "record the honest measured outcome" requirement):
  min observed nonzero delta 0.0862% (AAPL), max 0.8652% (CVX), mean of nonzero deltas ≈0.457%. The
  0.75% default was fixed in code before this run; it was **not** adjusted afterward — see
  `assumptions.md`'s new iter-7 entry for the full reasoning on why I judged CVX's delta a genuine
  (if narrow) mismatch against the stated bar rather than grounds to move the bar.
- **Zero writes** — verified: `daily_prices`/`scanner_runs`/`data_provider_runs` row counts and
  content are identical to their pre-check state (Step 5 table below); `check_adjustment_convention`
  and its callees make no INSERT/UPDATE/DELETE statement anywhere (verifiable by direct code read —
  no `session.add`/`session.commit`/`session.exec` write statement appears in either function).

### Step 3 — Derived-state rebuild — **NOT executed** (nothing to rebuild; never reached)

### Step 4 — Provenance

No new `data_provider_runs` row exists for this iteration (the convention check never calls
`data_manager.create_job`/`run_data_job` — structurally, not just by outcome). Provenance is instead
this dev handoff itself, per J-10 step 4's "existing conventions" instruction:
- Authorization basis: `docs/goal.md` AG-9's dated 2026-08-20 exception + vendor addendum, scoped to J-10.
- Dates targeted: exactly 2026-08-11 and 2026-08-12 (never touched — the check stopped before them).
- Provider evaluated: `yahoo` (via `YahooProvider.get_adjusted_close`, read-only comparison fetch only).
- Symbols in the comparison sample: 20 (documented above); symbols in the (untouched) recovery scope: 587.
- Check start/completion: 2026-08-20T21:59:37Z / 2026-08-20T21:59:42Z (~4.3s wall time, 20 live calls).
- Pre-check missing-row count: 1132 bars / 587 symbols (unchanged from iter-6, `data_provider_runs` id=538).
- Post-check restored-row count: **0** (the check does not restore rows; it only compares).
- Rows requested but not restored: all 1132 bars / 587 symbols (recovery never reached — convention
  mismatch stopped it upstream).
- Resulting dataset/frontier state: **unchanged**, `daily_prices` max date still 2026-08-10.
- Dataset provenance honesty: no row anywhere in `daily_prices` is `yahoo`-sourced this iteration —
  nothing was written, so there is nothing to mislabel. The database remains entirely `stooq`-sourced
  for its live-fetched portion, exactly as before.

### Step 5 — Post-recovery verification suite (all six checks, executed and recorded honestly)

| # | Check | Result |
|---|---|---|
| (a) | Expected coverage for 2026-08-11/2026-08-12 restored | **NOT MET** — 0 of 1132 target bars restored (convention check stopped the recovery before any fetch) |
| (b) | No other historical date modified | **PASS** — `daily_prices` outside the recovery window: 3,309,204 rows, `SUM(close)`=481,248,846.44, `SUM(volume)`=52,333,196,452,311.0, `MAX(date)`=2026-08-10 (aggregate re-verified post-check); `scanner_runs`: 3,118 rows, `MAX(asof_date)`=2026-08-10 |
| (c) | Surviving rows not overwritten unnecessarily | **PASS** — `daily_prices` rows for 2026-08-11/2026-08-12: **0** (still fully missing, never touched); `scanner_runs` rows for those two dates: **0** |
| (d) | Dataset frontier did not advance past 2026-08-12 | **PASS** (trivially — frontier is still 2026-08-10, unchanged) |
| (e) | Project's existing data/DB-integrity checks pass | **PASS** — `GET /api/health` `preflight.components.integrity` → `{"ok": true, "detail": "The database and all ledger/registry files are reachable and parse."}`; `db_ok: true`; `preflight.verdict: "GO"` |
| (f) | Original destructive condition gone (`GET /api/compass?as_of=2026-08-12` serves; J-01/J-02/J-03 replay clean) | **NOT MET** — both `GET /api/compass?as_of=2026-08-11` and `?as_of=2026-08-12` return HTTP 400 (`"as_of <date> is after the latest data date 2026-08-10"`, byte-identical to the pre-iteration state). J-01/J-02/J-03 were **not** replayed — per this iteration's own explicit scope decision (deferred to iteration 8 regardless of outcome; see the spec's BACKGROUND) and because the underlying condition they'd be replayed against is unchanged. As a lighter sanity check (not a substitute for J-01/J-02/J-03's own acceptance), `GET /api/compass?as_of=2026-08-10` and `GET /api/dashboard?as_of=2026-08-10` (the latest surviving date) both returned HTTP 200, confirming the rest of the system is undamaged. |

Additional AG-12 re-verification (TC-18, not trusted from any prior report alone): `next_session_manifests`
still holds exactly 24 rows, `MAX(as_of)` is still 2026-08-12, and every row's `(as_of, version,
content_hash, manifest_hash)` tuple was read and matches the pre-iteration state (16 distinct as_of
dates, versions dense per date, e.g. 2026-08-12 versions 1-6, 2026-08-11 versions 1-3 — this
version-count spread predates this iteration, from earlier regenerate-testing activity, and this
iteration did not add, remove, or alter any of them). `data_provider_runs`: `MAX(id)` is still 541,
and that row's `(provider, status, started_at, job_id)` still exactly match iter-6's own recorded
values (`stooq`, `failed`, `2026-08-20 18:00:54.819857`, `de9f13209b174890a728f837ef008e92`) — direct
proof no new row was created.

### Step 6 — Exception closure

**NOT closed.** Per AG-9's own text, the dated exception "is exhausted the moment J-10's post-recovery
verification passes" — verification did not pass here either (checks (a) and (f) unmet), so the
exception remains open for its one remaining permitted use: a re-run of this same bounded, idempotent
recovery. It does not authorize a different vendor, a wider sample, or a different tolerance chosen
after seeing a result — any of those needs a new, separately dated owner decision.

### Step 7 — Branch confinement

All work happened on `goal/market-compass` (confirmed via `git branch --show-current`). `main` was
never touched. No commits were made by this developer step (commits happen at a later pipeline stage,
per this project's convention).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_j10_recovery.py -v`
Result: **23 passed**, 0 failed, 1.66s. (14 pre-existing tests, 2 updated for the vendor swap, 9 new:
the default-sample sanity check, the three convention-check verdict tests (agree/mismatch/inconclusive),
a byte-unchanged-across-all-verdicts test, and three orchestration-gate tests proving `run_gated_recovery`
never reaches the write-capable calls on a non-agree verdict and does reach them on agree.)

Targeted regression re-run (the touched `yahoo_provider.py` is exercised by this file; nothing else
was touched):
- `tests/test_provider_clients.py` — **44 passed**, 0.14s (covers `YahooProvider.get_daily` and every
  other provider client; confirms the additive `get_adjusted_close` method changed nothing about
  existing behavior).

Per Constraints, these were run one file at a time, never concurrently; `free -h` was checked before
each heavier step (available memory stayed ≥ 19 GB throughout this iteration; swap used stayed ≤ 1 GB
— well inside the ~3G/~2G abort thresholds, so no step was aborted for host-safety reasons).

## Pre-handoff verification checklist

- [x] **Service startup**: `bash scripts/start-backend.sh` started cleanly, detached
  (`setsid nohup ... &`, since the prior foreground `timeout` attempt blocked the whole call and had
  to be corrected — see Known Issues #1), on its computed port (8255 for this repo path — polled
  `/api/health` until `200`, ~1s). Stopped cleanly afterward (`kill -TERM` on the uvicorn PID;
  confirmed no uvicorn/start-backend process remains via `ps aux`). Frontend was not started this
  iteration — not needed (no UI surface, `Frontend Present: no`, and a second goal-mode engine may be
  active on this host per the host-safety note).
- [x] **External integration tested live, not mocked**: this iteration's core action WAS a live
  integration test — 20 real network calls to Yahoo's chart endpoint through the new
  `get_adjusted_close` capability, against the real live database's stored values. It returned a
  genuine, evidenced mismatch verdict; documented above and in the run artifact.
- [x] **No new native dependency** added.

## Known Issues

1. **Operational note, not a defect:** my first attempt to start the backend for step 5(f)
   (`timeout 90 bash scripts/start-backend.sh > log 2>&1`) ran the script in the foreground under
   `timeout`, which blocked my own shell for 90s and then killed it before I could issue any curl
   calls (the script's own `exec uvicorn ...` never backgrounds itself — it expects the caller to
   background it). Corrected by relaunching via `setsid nohup bash scripts/start-backend.sh > log
   2>&1 &`. No lingering process resulted from the first (killed) attempt; verified via `ps aux`
   before the second attempt.
2. **CRITICAL for the next iteration/owner review — the recovery could not be completed this
   iteration.** The convention check correctly and honestly returned `mismatch` on real evidence
   (CVX's ~0.865% delta, just over the 0.75% tolerance). Zero bars restored;
   `daily_prices`/`scanner_runs` remain at the 2026-08-10 frontier; `GET /api/compass` for both
   recovery dates still 400s; J-01/J-02/J-03 remain unverified against a live replay (out of this
   iteration's scope regardless of outcome, per its own BACKGROUND). See "Recommendation for owner
   review" below.
3. **Carried forward from Technical verification above:** a future successful retry (post-tolerance
   decision) will still restore rows via `get_daily`'s raw close, not `get_adjusted_close`'s adjusted
   close, per the spec's explicit unchanged-fetch-path instruction. This is documented, not fixed —
   not this iteration's call to make.
4. The pre-existing manifest-version spread noticed at iter-6 (multiple versions per as_of from
   earlier regenerate-testing activity, e.g. six versions of the 2026-08-12 manifest) is unchanged and
   was re-observed only as part of this iteration's own AG-12 re-verification, not caused by it.
5. No config, model, or frontend file was touched — the tolerance/sample/window literals live only in
   `j10_recovery.py`, per the same "single-use incident constant, not a config.yaml tunable" reasoning
   iter-6's `RECOVERY_DATES`/`RECOVERY_SYMBOLS` already established (goal-decomposer's iter-7 entry in
   `assumptions.md` records this explicitly).

## Recommendation for owner review

The gate did exactly its job: it caught a real (if narrow, single-symbol-driven) discrepancy and
refused to write anything rather than silently accept it. Three honest paths forward, all requiring an
owner decision:

1. **Review the tolerance.** The evidence (min 0.0862%, max 0.8652%, all deltas internally uniform per
   symbol — i.e., not noisy) suggests 0.75% may simply be tighter than an ordinary quarterly-dividend
   adjustment on a higher-yielding name like CVX. A dated, owner-approved tolerance change (this
   iteration deliberately did not pick a number and apply it) would let a re-run of this exact,
   already-idempotent, still-fully-missing scope pass the gate — no code changes beyond the single
   `CONVENTION_CHECK_TOLERANCE` literal would be needed.
2. **Widen or change the comparison sample**, if the owner judges 20 large-cap tickers (which happened
   to include a comparatively high-yielding name) an unrepresentative test of "does the convention
   generally match" versus "does this exact tolerance clear every possible dividend-driven case."
3. **Accept the honest miss and hold** at the 2026-08-10 frontier, exactly as iteration 6 already
   proposed as one of its own options, deferring this recovery further.

Whichever path the owner picks, the retry is unchanged: `run_gated_recovery(session, engine, config,
convention_provider=YahooProvider(), fetch_provider=YahooProvider())` — idempotent, already proven
correct on both the guard and the gate, and it will re-run the convention check fresh every time (no
stale "already checked" state to invalidate).
