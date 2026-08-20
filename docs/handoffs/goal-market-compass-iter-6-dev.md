# goal-market-compass-iter-6 Dev Handoff

**Phase:** goal-market-compass-iter-6
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete (recovery attempt executed exactly as authorized; the underlying vendor is
currently unreachable from this environment — an HONEST MISS, not a code defect. See "READ THIS
FIRST" below. Zero database side effects; zero scope violations.)

## READ THIS FIRST — the live fetch was correctly attempted and correctly failed; the DB is unharmed

This iteration built and used a fail-closed scope guard (`app/engine/j10_recovery.py`) to derive the
exact 587-symbol missing set for 2026-08-11/2026-08-12 from surviving evidence, then dispatched
**exactly one** live fetch through the project's existing fetch engine, scoped to precisely that
envelope. **The fetch itself failed cleanly: all 587 symbols were rejected by Stooq's server with
HTTP 404.** A direct diagnostic probe (see "Root-cause diagnosis" below) shows Stooq now gates this
endpoint behind a JavaScript proof-of-work bot-verification challenge that no non-browser HTTP client
— including the project's own provider and a plain `curl` request — can solve. This is a vendor-side
access problem, not a bug in the recovery code, not a scope violation, and not a data-quality issue.

**What this means concretely:**
- `daily_prices` still has **zero** rows for 2026-08-11/2026-08-12 (unchanged from the pre-iteration
  damaged state) — max date is still 2026-08-10.
- `GET /api/compass?as_of=2026-08-12` still returns **HTTP 400** (unchanged).
- J-01/J-02/J-03 were **not** replayed this iteration — the Loop-mechanics gate ("no lane may run
  against the knowingly damaged database before J-10's post-recovery verification passes") still
  applies, because verification did **not** pass.
- **Zero unintended side effects.** Verified byte-for-byte: all 24 `next_session_manifests` rows and
  their existing export files are hash-identical before/after; the full `scanner_runs` as-of-date list
  is identical before/after; `daily_prices` row count/min/max are identical before/after. The failed
  fetch's own `data_provider_runs` row (id=541) is the only new row anywhere in the database.
- **AG-9's exception is NOT exhausted** — per its own text, it is exhausted only "the moment J-10's
  post-recovery verification passes." Verification did not pass, so the exception remains open for
  exactly what it already permits: a re-run of this same bounded, idempotent recovery. It does **not**
  authorize substituting a different vendor — that needs a new, separate owner decision.
- **This needs owner input**, not further unilateral action from a pipeline agent. See "Recommendation
  for owner review" at the end of this document for the concrete options.

I judged this important enough to lead with. The full evidence trail, the code, and the tests follow.

## What Was Built

- **`apps/backend/app/engine/j10_recovery.py`** (new) — the fail-closed, single-use J-10 recovery
  scope guard + orchestration:
  - `RECOVERY_DATES`/`RECOVERY_START`/`RECOVERY_END` = frozen literals `{2026-08-11, 2026-08-12}`.
  - `RECOVERY_SOURCE = "stooq"` (goal.md's own named vendor).
  - `RECOVERY_SYMBOLS` = the derived 587-symbol missing set (evidence below).
  - `EXCLUDED_UNPROVEN_SYMBOLS = {"MNST"}` — the one symbol deliberately left out on conflicting
    evidence (see "Missing-set derivation" below).
  - `validate_recovery_scope(...)` — raises `RecoveryScopeError` (a `ValueError` subclass) for ANY
    date outside `RECOVERY_DATES`, ANY symbol outside `RECOVERY_SYMBOLS`, or a wrong `source` —
    **in code**, before any network call can happen.
  - `still_missing_symbols(session)` — read-only; the idempotent "what's actually still missing right
    now" computation a retry uses, so an already-restored symbol is never re-requested.
  - `run_bounded_recovery_fetch(...)` — the ONE entry point for the live fetch: computes
    still-missing, validates through the guard, dispatches through the EXISTING
    `data_manager.run_data_job` (the same engine `POST /api/data/jobs` uses) — no second fetch path.
    A true no-op (zero network calls) when nothing is missing.
  - `run_bounded_recovery_backfill(...)` — hardcoded to `[RECOVERY_START, RECOVERY_END]` so the
    derived-state rebuild step can never touch a third date. **Not exercised against the real DB this
    iteration** (nothing to backfill — the fetch restored zero bars); proven correct against a fixture
    in `test_j10_recovery.py`.
- **`apps/backend/tests/test_j10_recovery.py`** (new) — 15 tests, all passing (see "Tests Run").

## Files Changed

- `apps/backend/app/engine/j10_recovery.py` (new) — scope guard + orchestration, see above.
- `apps/backend/tests/test_j10_recovery.py` (new) — unit tests for the guard + idempotency.
- `runs/goal-session-market-compass/state/assumptions.md` — two new dated entries: the MNST
  exclusion judgment call, and the vendor-unreachable finding (same evidence as this handoff, in the
  project's established assumption-ledger format).
- `docs/handoffs/goal-market-compass-iter-6-dev.md` (this file).

No other file was touched. `docs/phases/goal-market-compass-iter-5.md`,
`docs/handoffs/goal-market-compass-iter-5-dev.md`,
`runs/goal-market-compass-iter-5/status.json`, and
`runs/goal-session-market-compass/state/incident-2026-08-20-iter-5-superseded.md` were read-only
referenced, never edited (verified below).

## J-10 step-by-step account

### Step 1 — Missing-set derivation (BEFORE any network call)

Per J-10's own instruction, the derivation used only surviving evidence, gathered read-only (`sqlite3
-readonly` / a read-only Python `sqlite3` connection against the live 8.3 GB DB file — never copied,
never opened for write) before the fetch driver ever ran:

1. **`data_provider_runs` id=538 — the ACTUAL removal's own audit record** (the strongest evidence:
   a machine-recorded outcome, not a preview):
   ```
   provider=seed, status=ok, symbols_ok=587
   message: {"kind": "remove", "removed_bar_count": 1132, "removed_symbol_count": 587,
             "removed_first": "2026-08-11", "removed_last": "2026-08-12",
             "not_removable_bar_count": 0,
             "cascade": {"snapshot_count": 11, "snapshot_dates": [2026-05-12, 2026-05-13,
               2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03, 2026-08-05,
               2026-08-10, 2026-08-11, 2026-08-12], "forward_return_count": 16566}}
   ```
   This exactly corroborates the iter-6 spec's own BACKGROUND (the same 11 cascade dates) and confirms
   the removal touched exactly 587 symbols for exactly the 2026-08-11..2026-08-12 range.
2. **iter-5's own pre-removal preview** (`docs/handoffs/goal-market-compass-iter-5-dev.md`):
   `removable_bar_count: 1132, removable_symbol_count: 587, not_removable_bar_count: 0` — an
   independent measurement (taken moments before removal) that agrees exactly with source 1.
3. **Live `daily_prices` on the last surviving date, 2026-08-10** (read-only query): exactly 587
   distinct symbols. Verified this equals the 2026-08-07 set (588 symbols, itself matching
   2026-08-03/05/06) minus exactly one symbol — no new arrivals either direction:
   `SELECT symbol FROM daily_prices WHERE date='2026-08-07' EXCEPT SELECT symbol FROM daily_prices
   WHERE date='2026-08-10'` → `MNST` (only row). `2026-08-10 EXCEPT 2026-08-07` → empty.

Three independent sources, two of them contemporaneous machine-recorded facts about the removal
itself, converge on **587 symbols**. The full derived list is embedded verbatim in
`RECOVERY_SYMBOLS` in `apps/backend/app/engine/j10_recovery.py` (its module docstring carries this
same evidence trail for future readers).

**MNST — the one row the evidence could not settle, excluded per TC-16.** MNST appears in the frozen
`next_session_manifests` comparison-cohort JSON for BOTH 2026-08-11 (3 versions, all identical
membership) and 2026-08-12 (5 versions, all identical membership) with real close values — $45.53 and
$45.98 — roughly half MNST's contemporaneous $90–97 range on 2026-08-07, consistent with an
unadjusted stock-split discontinuity landing around 2026-08-10 (which is also MNST's own current last
date in `daily_prices` — it has no row for 2026-08-10, 2026-08-11, or 2026-08-12 today). Since
removal is a plain `[start, end]` range wipe with no per-symbol filter, if MNST had held a bar in
scope at removal time it would have been counted and removed exactly like every other symbol — but
BOTH contemporaneous removal-time measurements (sources 1 and 2, which agree with each other) say 587,
not 588. This is a genuine, irreconcilable (from available evidence) conflict between an older frozen
scoring snapshot and two newer, closer-to-the-event, machine-recorded facts. Per J-10 step 1 / TC-16
("if that set cannot be established from evidence... stop... rather than fetching an unproven
guess"), **MNST was excluded** from `RECOVERY_SYMBOLS`. Full reasoning is in the module docstring and
in `runs/goal-session-market-compass/state/assumptions.md`'s new "MNST excluded on conflicting
evidence" entry. This is recorded for owner review, not resolved unilaterally.

### Step 2 — The bounded fetch (executed; failed cleanly)

Dispatched via `app.engine.j10_recovery.run_bounded_recovery_fetch`, which:
1. Computed `still_missing_symbols()` against the LIVE database — returned all 587 (zero rows existed
   for either date, confirmed by a direct pre-flight query: `SELECT COUNT(*) FROM daily_prices WHERE
   date IN ('2026-08-11','2026-08-12')` → `0`).
2. Validated the request through `validate_recovery_scope` (passed — the computed request is by
   construction inside the authorized envelope).
3. Called `data_manager.validate_job_request("fetch", 2026-08-11, 2026-08-12, cfg, source="stooq",
   api_key=...)` (the SAME gate `POST /api/data/jobs` applies) — passed.
4. Dispatched through `data_manager.create_job` + `data_manager.run_data_job` — the identical engine
   `POST /api/data/jobs` uses, with `symbols=<the 587>`, `kind="fetch"`, `source="stooq"`. Run
   synchronously from a standalone driver script (not via HTTP) using the backend's own
   `app.db.get_engine()` / `app.config.get_config()` — the same live DB file, no copy, no second
   connection mechanism. Launched detached (`setsid nohup`) since duration was unknown in advance;
   completed in 37.9s.

**Outcome — `data_provider_runs` id=541** (the honest, machine-recorded audit trail):
```
provider=stooq, started_at=2026-08-20 18:00:54.819857 UTC, finished_at=2026-08-20 18:01:32.704829 UTC
job_id=de9f13209b174890a728f837ef008e92
status=failed, symbols_ok=0, symbols_failed=587, bars_fetched=0
message: "fetched 0/587 symbols (587 failed)"
```
Every one of the 587 requests failed identically:
`stooq request failed for '<SYMBOL>': Client error '404 Not Found' for url
'https://stooq.com/q/d/l/?s=<symbol>.us&i=d&d1=20260811&d2=20260812'`
(sample from `AAPL`, `MSFT`-class tickers through `^VXN` — the errors are uniform across the whole
requested set, not clustered on any particular subset of symbols.)

### Root-cause diagnosis (why it failed)

A single diagnostic `curl -v` to the identical Stooq URL (`https://stooq.com/q/d/l/?s=aapl.us&i=d
&d1=20260811&d2=20260812`), independent of the app's `httpx` client, returned **HTTP 200** — but the
body was not CSV data:
```html
<!DOCTYPE html><html><head>...<meta name="robots" content="noindex,nofollow"></head><body>
<noscript>This site requires JavaScript to verify your browser...</noscript>
<script>... a SHA-256 leading-zero proof-of-work puzzle, then POST the answer to /__verify ...</script>
</body></html>
```
Stooq now gates this endpoint behind an active JS bot-verification challenge — the TLS handshake
itself confirmed the real-world date is genuinely 2026-08-20 (server cert `Date:` header), ruling out
any "future date" concern. No non-browser HTTP client (the project's `httpx`-based `StooqProvider`,
or a plain `curl`) can solve a JavaScript proof-of-work challenge — this is a structural, vendor-side
access block, not a transient rate limit, not a per-symbol gap, and not something a header/retry
change can fix. `AAPL` — one of the most liquid, universally-carried tickers that exists — failing
identically to every other symbol corroborates this is not a data-availability issue.

This matches (and appears to be a newer manifestation of) a problem this project already hit once
before: `config.yaml` marks `stooq` `needs_key: true` with the comment *"free CSV nominally, but
key-gated for this IP (iter-3 lesson) — honest"*, and `app/data_providers/local_stooq_archive.py`'s
own docstring says *"Stooq's per-symbol CSV export endpoint is IP-blocked ('Access denied')"* — which
is why iter-16 built a local bulk-archive reader as a workaround for offline seed-building. **That
local archive was checked as a possible alternate path and does not help**: its on-disk data for AAPL
ends 2026-07-01 (file mtime 2026-07-02) — it is the exact same one-time historical download already
fully incorporated into the committed seed, five to six weeks short of the dates needed here.

**No workaround was attempted.** Building a JS-challenge-solving HTTP client would mean engineering
new anti-bot-circumvention capability with no precedent in this codebase, is questionable against the
vendor's own terms, and is far outside "the project's existing provider path" (J-10 step 2's explicit
instruction). Substituting a different vendor (`yahoo`, which `data_provider_runs` ids 527-533 show
DID succeed from this environment as recently as 2026-08-14) was considered and NOT done, because
AG-9's dated exception names `stooq` specifically — using a different vendor is a scope decision for
the owner, not something this iteration is authorized to decide unilaterally.

### Step 3 — Derived-state rebuild (NOT executed — nothing to rebuild)

Not run against the real database: `daily_prices` still has zero rows for 2026-08-11/2026-08-12, so
there is nothing for a backfill to snapshot. `run_bounded_recovery_backfill` exists and is proven
correct on a synthetic fixture (`test_backfill_creates_snapshots_only_for_the_two_recovery_dates`) —
ready to run the moment bars exist.

### Step 4 — Provenance (existing conventions only)

Recorded via the two conventions J-10 names — no new framework:
- **`data_provider_runs` id=541** (machine-readable half, shown above in full).
- **This dev handoff** (human-readable half): authorization basis = `docs/goal.md` AG-9's dated
  2026-08-20 exception scoped to J-10; dates targeted = exactly 2026-08-11 and 2026-08-12; provider =
  stooq; symbols targeted = 587 (the derived set, one — MNST — deliberately excluded, see above);
  start/completion = 2026-08-20T18:00:54.819857Z / 2026-08-20T18:01:32.704829Z; pre-recovery
  missing-row count = 1132 bars / 587 symbols (from `data_provider_runs` id=538, the removal's own
  record); post-recovery restored-row count = **0** (every request failed); rows requested but not
  restored = **all 587** (vendor unreachable — see root-cause diagnosis); resulting dataset/frontier
  state = **unchanged**, `daily_prices` max date still 2026-08-10.

### Step 5 — Post-recovery verification suite (all six checks, executed and recorded honestly)

| # | Check | Result |
|---|---|---|
| (a) | Expected coverage for 2026-08-11/2026-08-12 restored | **NOT MET** — 0 of 1132 target bars restored (vendor unreachable) |
| (b) | No other historical date modified | **PASS** — full `scanner_runs.asof_date` list (3118 rows) is byte-identical before/after (`diff` clean); `daily_prices` COUNT/MIN/MAX identical (3,309,204 / 1996-01-02 / 2026-08-10) before/after |
| (c) | Surviving rows not overwritten unnecessarily | **PASS** — all 24 `next_session_manifests` rows hash-identical (full-row SHA-256, every column) before/after; all existing export files (`2026-08-12_v5.json`, `_v6.json`) hash-identical; zero `daily_prices` rows touched (fetch wrote nothing) |
| (d) | Dataset frontier did not advance past 2026-08-12 | **PASS** (trivially — frontier is still 2026-08-10, unchanged, not advanced) |
| (e) | Project's existing data/DB-integrity checks pass | **PASS** — `PRAGMA quick_check` → `ok`; `GET /api/health` `preflight.components.integrity` → `{"ok": true, "detail": "The database and all ledger/registry files are reachable and parse."}`; `db_ok: true` |
| (f) | Original destructive condition gone (`GET /api/compass?as_of=2026-08-12` serves; J-01/J-02/J-03 replay clean) | **NOT MET** — `GET /api/compass?as_of=2026-08-12` still returns HTTP 400 (`"as_of 2026-08-12 is after the latest data date 2026-08-10"`, byte-identical message to the pre-iteration state). J-01/J-02/J-03 replay was **not attempted** — the Loop-mechanics gate forbids running any lane (including browser-QA replay) against the still-damaged database until verification passes, and it did not pass here. |

Byte-for-byte restoration could not be evaluated because zero bytes were restored — this is a
complete miss, stated plainly, not a partial one dressed up as complete.

### Step 6 — Exception closure

**NOT closed.** Per AG-9's own text, the dated exception "is exhausted the moment J-10's
post-recovery verification passes" — verification did not pass (checks (a) and (f) above are
unmet), so the exception remains open, exactly as written, for its one remaining permitted use: "a
re-run of the same bounded, idempotent recovery after a failed or partial attempt, still confined to
the proven missing set." It does **not** authorize a different vendor or a wider scope — that
requires a new, separately dated amendment.

### Step 7 — Branch confinement

All work happened on `goal/market-compass` (confirmed via `git branch --show-current` before and
after). `main` was never touched. No commits were made by this developer step (per this pipeline's
convention, commits happen at a later pipeline stage).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_j10_recovery.py -v`
Result: **15 passed**, 0 failed, 0.91s.

Covers: guard rejection of an out-of-window date (including the explicit 2026-08-13 boundary and a
range that only partially overlaps the window), rejection of a symbol outside the derived set,
rejection of the wrong source, rejection of an empty symbol list, the positive (in-scope) case,
`still_missing_symbols`'s read-only idempotent computation, the fetch's idempotent re-invocation
(seeded survivor untouched, only the genuinely-missing row requested — verified both via the returned
`requested_symbols` list AND via a spy provider's own call log), the backfill's date-scope hard bound
(a third seeded date gets no snapshot), the MNST exclusion (asserted both as a constant and as a
guard-rejection), and the module's constant shape (587 symbols, correct dates/source).

Targeted regression re-run (nothing in these files was touched, but the guard module now exists
alongside them — confirming zero interaction):
- `test_manifest_invariants.py` — **37 passed**, 3.13s.
- `test_api_compass.py` — **8 passed**, 1.47s.

Per Constraints, these were run one file at a time, never concurrently; `free -h` was checked before
each run (available memory stayed ≥ 19 GB throughout this iteration; swap used stayed ≤ 250 MB — well
inside the ~3G/~2G abort thresholds, so no step was aborted for host-safety reasons).

## Pre-handoff verification checklist

- [x] **Service startup**: `bash scripts/start-backend.sh` started cleanly (health check `ok`,
  `db_ok: true`, `readiness: ready`, preflight `GO`) on its computed port (8255 for this repo path).
  Stopped cleanly afterward (`pkill -f "uvicorn main:app"`; confirmed no uvicorn process remains).
  Frontend was not started this iteration — not needed (no UI surface, and the required-still-passing
  replay is correctly gated off by the Loop-mechanics rule since verification didn't pass).
- [x] **External integration tested live, not mocked**: this whole iteration's core action WAS the
  live integration test — a real network fetch against the real `stooq` endpoint, through the real
  provider code, against the real 8.3 GB database. It failed, and that failure (plus its full
  root-cause diagnosis) is documented above and in `data_provider_runs` id=541, per this checklist's
  own instruction to document a live-integration failure rather than rely on mocks alone.
- [x] **No new native dependency** added.

## Known Issues

1. **CRITICAL — the recovery could not be completed this iteration.** The authorized vendor (stooq)
   is currently unreachable from this environment (JS bot-verification challenge blocks all
   non-browser HTTP clients). Zero bars restored. `daily_prices` remains at its damaged frontier
   (2026-08-10); `GET /api/compass?as_of=2026-08-12` still 400s; J-01/J-02/J-03 remain unverified
   against a live replay (not attempted, per the Loop-mechanics gate). See "Recommendation for owner
   review" below.
2. The pre-existing gap in `apps/backend/data/exports/next_session_manifests/` (only 2 of 6 versions
   of the 2026-08-12 manifest have an export file on disk; `export_path` is recorded for versions
   2/3/4 but no file exists there) predates this iteration and was found only as a side effect of
   building the before/after integrity baseline. Verified byte-identical before vs. after this
   iteration's (failed) recovery attempt — not something this iteration changed or needs to fix — but
   flagged since it is directly adjacent to AG-12/manifest-integrity concerns and the reviewer/auditor
   should know it predates this work, not follow from it.
3. The 2026-08-04 dip to 463 `daily_prices` symbols (vs. the surrounding week's 588) is a pre-existing
   data-quality artifact noticed while establishing the missing-set baseline. Unrelated to J-10's
   scope (outside the 2026-08-11/2026-08-12 window); not investigated further; flagged for whoever
   next works on data quality.
4. Starting the backend for verification (Step 5 above) refreshed the shared, config-declared
   drift-report cache (`config.yaml`'s `report_path: runs/goal-session-ops-hardening/state/
   drift-report.json` — a cross-cutting operational cache file, not a canonical business-data table
   or a session-scoped artifact, despite the legacy directory name from when it was introduced) — its
   `reference` field moved from `2026-08-14` to `2026-08-12`, `status` stayed `clean`, `affected`
   stayed `[]`. This is the drift mechanism's normal boot-time behavior, not something this iteration
   changed deliberately, and it carries no canonical value (AG-12 does not govern it). Flagged only
   for full disclosure of every file this iteration's actions touched.
5. `EXCLUDED_UNPROVEN_SYMBOLS = {"MNST"}` is a deliberate, evidence-based exclusion, not a bug —
   see "Missing-set derivation" above and the two new entries in
   `runs/goal-session-market-compass/state/assumptions.md`. If a future owner review resolves the
   evidence conflict in MNST's favor, adding it to `RECOVERY_SYMBOLS` and re-running the (already
   idempotent, already-tested) fetch is the correct, minimal follow-up — nothing else in this
   iteration's code needs to change.

## Recommendation for owner review

Recovery is stopped, not abandoned — the guard/orchestration code is complete, tested, and ready to
run the instant the blocker clears. Three honest paths forward, all requiring an owner decision (none
of them is something this iteration is authorized to pick on its own):

1. **Authorize an alternate vendor** for this same bounded recovery via a new dated goal.md amendment.
   `yahoo` has direct, recent proof of working from this environment (`data_provider_runs` ids
   527-533, successfully fetching through 2026-08-14, `symbols_ok` 587-588 of ~591 each time). This
   would need only a new `RECOVERY_SOURCE`-equivalent authorization in goal.md — the guard code
   already supports any single named source via `validate_recovery_scope`'s `source` check.
2. **Accept 2026-08-10 as the frontier** going forward and let a future fresh ingest naturally move
   past this gap when new dates become available; re-baseline J-01/J-02/J-03's affected goldens in a
   later iteration instead of restoring these exact two historical dates.
3. **An out-of-band restore**: if the owner has another means of obtaining these two dates' bars for
   the 587 symbols (e.g., a manual browser-based download solving Stooq's challenge by hand, similar
   in spirit to how `data/d_us_txt/` was originally obtained for the committed seed), the existing
   `LocalStooqArchiveProvider` pattern (or a small equivalent reader) could ingest it offline with no
   further live-fetch exception needed — this is new work, not something to build unilaterally here.

Whichever path the owner picks, the retry itself is a single call:
`app.engine.j10_recovery.run_bounded_recovery_fetch(session, engine, config)` — idempotent, already
proven correct, and it will automatically pick up wherever `still_missing_symbols` finds gaps.
