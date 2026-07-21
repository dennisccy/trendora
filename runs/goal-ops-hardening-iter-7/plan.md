# goal-ops-hardening-iter-7 Execution Plan

## Context (read before building)

This is a **lean, single-function, backend-only** iteration closing the ops-hardening session's LAST
non-passing Must-have journey, J-06 ("Pages load only what they need"). iter-6 fixed J-06's two real
frontend latency violations (Dashboard/Data Manager fetch contention) and, in a post-QA fix pass,
determined the previously-reported `/evidence` "555.97s regression" was a measurement-contamination
artifact — the real number is a **73.3s one-time cold recompute** on the accumulated live dev DB (vs 9.5s
on the committed seed), paid once per dataset change because the ingest finalize hook
(`_refresh_ingest_aggregates`, `app.engine.data_manager`) warms `event_study_cache`'s default research
hot key (`data_manager.py:3138`, `research_hot_keys` category) but never the per-claim
`drawdown_expectations` view slot the SAME table reserves for `/evidence`'s expectations panel. iter-6's
audit (finding B1) named the exact fix and this iteration implements it — nothing else.

Confirmed by reading the current code:
- `_refresh_ingest_aggregates` (`apps/backend/app/engine/data_manager.py:3044-3143`) already has the exact
  pattern to mirror twice over: the `forward_aggregates` warm loop (iter-5, lines 3120-3130, ticks `prog`
  once per horizon inside its own try/except) and the `research_hot_keys` warm block (iter-2, lines
  3132-3141, one try/except, appends the category only on success). `forward_testing` is already imported
  at module level (line 56) — `forward_testing.compute_drawdown_expectations_cached` needs no new import.
  `app.engine.evidence` is NOT currently imported here — `resolve_ledger_path`/`read_entries`/
  `FORWARD_WALK_TYPE` need a new import (from `app.engine.evidence` and/or `app.engine.ledger`, matching
  how `evidence.py` itself imports them at `evidence.py:42`).
- `build_evidence_payload` (`apps/backend/app/engine/evidence.py:113-160`) is the exact filter to mirror:
  `for entry in read_entries(ledger_path): if not isinstance(entry, dict) or entry.get("type") ==
  FORWARD_WALK_TYPE: continue` — then reads `row["claim"]` (the `_claim_row(entry)["claim"]` dict) and
  calls `compute_drawdown_expectations_cached(session, row["claim"], config)`. The warm loop must resolve
  the SAME claim dicts the same way (via `_claim_row` or equivalently `entry.get("claim")`) so the cache
  subject hash (`_drawdown_expectations_cache_subject`, keyed on the canonical JSON of the claim dict)
  matches exactly what `/api/evidence` will look up.
- `compute_drawdown_expectations_cached` (`forward_testing.py:1394+`) already returns `None` silently for
  an out-of-scope horizon or an unresolvable cohort, and persists a `None` result too (an honest cached
  miss) — never raises. The warm loop's own per-claim try/except is a second safety net for anything
  unexpected (e.g. a malformed ledger entry), per TC-4.
- `aggregates_refreshed`'s enumerated values and gating convention (`data_manager.py:3049-3052`, tested at
  `apps/backend/tests/test_data_manager.py:1042-1057,1159-1188`) is the exact honesty pattern to extend:
  append `"drawdown_expectations"` ONLY if at least one claim was actually warmed — never on an empty
  ledger (TC-5) or an all-unresolvable cohort set.
- `runs/goal-session-ops-hardening/state/blueprint.md` (Data Contract rows for "Backfill run-summary
  contract" and "Membership timeline / research hot-key caches") has ALREADY been updated by the
  goal-decomposer this iteration to add `"drawdown_expectations"` to the enumerated list and note
  `/evidence` as a served page of the existing row — no blueprint edit is needed from the developer, only
  confirmation of no drift (per the DoD).

## What to Build

- **Extend `_refresh_ingest_aggregates`** (`apps/backend/app/engine/data_manager.py`) with one more
  non-fatal warm step, placed after the existing `research_hot_keys` block (after line ~3141):
  1. Resolve the ledger path via `evidence.resolve_ledger_path()`.
  2. Read entries via `read_entries(ledger_path)`, excluding `type == FORWARD_WALK_TYPE` entries — the
     SAME filter `build_evidence_payload` applies (do not re-derive a different filter).
  3. For each remaining entry, extract its `claim` dict (mirror `_claim_row`'s `entry.get("claim")`
     extraction, or reuse `_claim_row` directly to guarantee byte-identical claim-dict shape to what
     `/api/evidence` resolves).
  4. Call `forward_testing.compute_drawdown_expectations_cached(session, claim, cfg)` for each claim,
     inside its OWN try/except (log + continue to the next claim — TC-4: one unresolvable/erroring claim
     must never block another or fail the ingest job).
  5. Add a `prog.tick()` heartbeat stamp before each claim's warm call (mirrors the `forward_aggregates`
     per-horizon tick pattern at `data_manager.py:3124`).
  6. Append `"drawdown_expectations"` to `refreshed` ONLY if at least one claim's warm call actually ran
     without raising (gate on "attempted at least one call," matching the existing
     `research_hot_keys`/`market_phase` "actually did something" convention) — an empty ledger (TC-5) or a
     ledger where every claim is out-of-scope/unresolvable must NOT report this category.
  7. Wrap the whole ledger-resolution step (steps 1-2) in its own top-level try/except too, so a missing/
     corrupt ledger file degrades to zero warm calls (honest omission), never an exception that aborts the
     rest of the finalize hook.
- **No new table, no new DB column, no new endpoint, no new computing module** — reuses the EXISTING
  `event_study_cache` table's reserved `drawdown_expectations` view slot and the EXISTING
  `compute_drawdown_expectations_cached` function verbatim, called with the SAME argument shape
  `/api/evidence` already uses.
- **Unit/integration tests** (extend `apps/backend/tests/test_data_manager.py`, mirroring the existing
  `finalize_hook_engine` fixture + `test_finalize_hook_warms_forward_aggregates_for_every_configured_
  horizon` / `test_finalize_hook_forward_aggregate_warm_avoids_recompute_on_subsequent_read` pattern used
  for the iter-5 `forward_aggregates` warm, and `apps/backend/tests/test_forward_testing.py`'s existing
  `dd_expectations_engine`/`_FACTOR_CLAIM` fixtures for `compute_drawdown_expectations_cached`):
  - TC-1: a non-empty ledger fixture (write a temp ledger file with 1-2 real claim entries, e.g. reusing
    `_FACTOR_CLAIM`-shaped JSON) → `_refresh_ingest_aggregates` returns `"drawdown_expectations"` in
    `refreshed`, and an `EventStudyCache` row exists per claim for the `drawdown_expectations` view before
    the job is marked completed.
  - TC-3: the warmed `EventStudyCache` row's deserialized payload is byte-identical to a fresh
    `compute_drawdown_expectations(session, claim, cfg)` call for the same claim (mirrors
    `test_finalize_hook_coverage_snapshot_byte_identical_to_fresh_compute`'s pattern).
  - TC-4: a claim whose `compute_drawdown_expectations_cached` call raises (monkeypatch to raise) — the
    loop logs and continues to the next claim, no exception propagates out of
    `_refresh_ingest_aggregates`; a claim whose cohort is unresolvable (returns `None`) is not an error —
    it just doesn't count toward "at least one warmed."
  - TC-5: an empty ledger (no file, or a file with zero non-`forward_walk` entries) → zero warm calls,
    `"drawdown_expectations"` NOT in `refreshed`.
  - Regression check: existing `test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates`'s
    `assert set(refreshed) == {...}` will need `"drawdown_expectations"` added to its expected set IF that
    fixture's ledger (real project ledger, read via `resolve_ledger_path()` with no env override) resolves
    non-empty claims — confirm which is true and update the assertion set accordingly rather than leaving
    a stale exact-set match that now silently fails or silently passes for the wrong reason.
- **Real-browser + curl re-measurement** (QA-owned, not dev-owned code, but the dev must leave the system
  in a state that supports it): after implementing the warm step, trigger a real ingest job (backfill/both/
  rebuild) against the running dev backend so the finalize hook actually runs, then measure `/evidence`'s
  FIRST view immediately afterward. Real browser preferred; a same-process cold `curl` taken immediately
  post-ingest is an explicitly acceptable, disclosed substitute per the spec's NOTES (state which method
  was used and why in `reports/perf-budgets.md` — do not silently substitute).
- **`reports/perf-budgets.md`**: new dated section — the post-warm `/evidence` first-view measurement
  (method disclosed) plus a fresh reconfirmation of all 11 J-06 pages' existing budgets (no loosened
  numbers; additive only, following the exact style of iter-6's "J-06 closeout" / "CORRECTION" sections
  already in the file at lines 1119+/1209+).
- **`blueprint.md` drift check**: confirm `runs/goal-session-ops-hardening/state/blueprint.md`'s Data
  Contract rows (already updated by the decomposer this iteration — see Context above) match the shipped
  code exactly; no edit expected unless something drifts.

## Explicitly OUT OF SCOPE (do not touch)

- `readiness.py`, `main.py`'s boot sequence, `warmup.py` — settled (J-04, "do not redo").
- `max_range_days`, `snapshot_cadence`, backfill range-cap logic — settled (J-03, "do not redo").
- A second computing module, a second endpoint, or a second cache table for `drawdown_expectations`,
  `event_study_cache`, or any other already-registered Data Contract value.
- Loosening any committed budget number in `reports/perf-budgets.md` — additive, honestly-measured rows
  only.
- Retroactively editing iter-6's own point-in-time artifacts (`reports/phase-goal-ops-hardening-iter-6-
  user-visible-changes.md` / `-ui-surface-map.md`) — historical record; this iteration's own fresh
  ui-impact-analyst/closure artifacts supersede them.
- The `[NEW]` `demo.sh ops-hardening --session-live` walkthrough — auto-produced by the session-mode
  demo-narrator step once J-06 flips to `passing`; not a developer/reviewer task.
- Any other lazy cache beyond `drawdown_expectations` (other `event_study_cache` non-default views,
  `market_phase_cache` beyond the latest key) — untouched this iteration.
- **No frontend file changes** — `/evidence`'s rendered payload is byte-identical before/after (same
  function, same values, only warm TIMING moves earlier). If the developer finds the fix alone does not
  close the gap, do NOT expand scope into a frontend change or a second backend path — stop and flag it in
  the dev handoff for a fresh decomposer pass (this session's established contingent-fix discipline).

## Agents Required

- backend-data: yes — extend `_refresh_ingest_aggregates` (`apps/backend/app/engine/data_manager.py`)
  with the one new non-fatal warm step described above; add/extend unit tests in
  `apps/backend/tests/test_data_manager.py` and, if needed, `apps/backend/tests/test_forward_testing.py`.
- frontend-ux: no — zero frontend file changes are in scope; `/evidence`'s rendered payload and every
  other page's behavior are unaffected by construction (only ingest-time warm TIMING changes).

## Frontend Present: yes

(No frontend code changes ship this iteration. `Frontend Present: yes` is set — per the phase spec's own
explicit statement — because J-06's acceptance requires a real-browser re-measurement across all 11 named
pages, including `/evidence`'s FIRST view immediately after a real ingest job, which only a live
browser-qa pass can confirm. QA must run the Chrome MCP browser checks even though no frontend diff
exists.)

## Files to Create/Modify

- `apps/backend/app/engine/data_manager.py` — extend `_refresh_ingest_aggregates` with the
  `drawdown_expectations` warm step (new import of `app.engine.evidence`/`app.engine.ledger` symbols;
  ~15-25 new lines mirroring the existing `research_hot_keys`/`forward_aggregates` blocks); update the
  function's own docstring enumeration of `["latest_snapshot", "coverage", "membership_timeline",
  "market_phase", "forward_aggregates", "research_hot_keys"]` to add `"drawdown_expectations"`.
- `apps/backend/tests/test_data_manager.py` — new tests (TC-1/TC-4/TC-5 above) using the existing
  `finalize_hook_engine` fixture pattern; update
  `test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates`'s expected `refreshed` set if it is
  affected by the real project ledger's contents.
- `apps/backend/tests/test_forward_testing.py` — extend only if a new byte-identity assertion (TC-3) needs
  a helper not already present; likely reuses `dd_expectations_engine`/`_FACTOR_CLAIM` as-is.
- `reports/perf-budgets.md` — new dated section: post-warm `/evidence` first-view measurement (method
  disclosed) + full 11-page reconfirmation.
- `docs/handoffs/goal-ops-hardening-iter-7-dev.md` — dev handoff; "Known Issues" must describe the
  CURRENT fixed first-view state, not restate iter-6's retracted "555.97s" framing.
- `runs/goal-session-ops-hardening/state/blueprint.md` — confirm only (already updated by the decomposer);
  edit only if a genuine drift is found between the shipped code and the already-written Data Contract
  rows.

No file under `apps/frontend/**` should appear in the diff.

## Key Test Scenarios

- TC-1: non-empty evidence ledger + a `backfill`/`both`/`rebuild`-shaped `JobProgress` →
  `_refresh_ingest_aggregates` returns `"drawdown_expectations"` in `refreshed`, and every ledger claim has
  an `EventStudyCache` row for the `drawdown_expectations` view before the job is marked completed.
- TC-2 (QA-owned, real browser or documented cold-curl substitute): first `/evidence` view immediately
  after a real ingest job completes loads within the committed WARM budget (≤3s page / Item I), not the
  prior ~73s cold miss.
- TC-3: the ingest-warmed value is diffed against a fresh, uncached `compute_drawdown_expectations` call
  for the same claim — byte-identical field-for-field.
- TC-4: a claim whose cohort is unresolvable (`compute_drawdown_expectations` returns `None`) — the loop
  continues to the next claim (no exception propagates), and that claim's `/evidence` row renders with no
  `expectations` panel, never a crash or fabricated value. A claim whose warm call raises mid-loop is
  logged and skipped, never blocking the rest of the loop or failing the ingest job.
- TC-5: empty evidence ledger at finalize time → zero warm calls, `"drawdown_expectations"` NOT appended
  to `refreshed`.
- TC-6 (QA-owned, real browser): all 11 J-06-named pages (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`,
  `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, one `/research` lab) load
  within their committed budgets under a warm prod-mode backend (`scripts/start-backend.sh`/
  `scripts/start-frontend.sh`, never `dev.sh`); results recorded in `reports/perf-budgets.md`.
- TC-7: `pytest apps/backend/tests/test_data_manager.py apps/backend/tests/test_forward_testing.py
  apps/backend/tests/test_api_backtest.py apps/backend/tests/test_mcp_window.py -v` runs to completion, 0
  failures, 0 errors (closes iter-6's named open item 4 — note: `test_api_backtest.py`/
  `test_mcp_window.py` together measured ~84 minutes in iter-6 due to the session-scoped `loaded_engine`
  fixture rebuilding the full 30-year seed; this is expected, not a hang — see the
  `trendora-30y-test-suite-slow-not-product` project lesson).
- TC-8 (QA-owned): J-01's and J-03's existing golden replay scripts PASS end-to-end with no step failures
  attributable to this iteration's diff (expected trivially true — zero frontend/data-jobs files touched).

## Environment Note (for the developer agent)

Before running any test or command that writes temp files, export:
```
export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-f8ba48e5.11312" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-f8ba48e5.11312" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-f8ba48e5.11312"
```
Per project convention (`goal-mode-pump-dont-run-full-suite` lesson), do not run the full backend test
suite — only the four named test files (TC-7) plus any other test directly touching changed code.
