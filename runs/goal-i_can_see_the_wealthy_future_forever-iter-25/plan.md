# goal-i_can_see_the_wealthy_future_forever-iter-25 Execution Plan

This is the last buildable wave of the 39-journey goal. After J-37/J-38 land green offline and
J-39/J-35 capture green with nothing regressed, GOAL_ACHIEVED becomes reachable on the buildable set
(J-22/J-23/J-24 + any live-fetch outcome recorded honestly NA / non-halting).

## What to Build
- **J-37 Missing-data diagnostic (backend):** extend the EXISTING single coverage producer
  (`compute_coverage` / a new `_missing_data_diagnostic` helper) to emit, per affected universe member,
  three honest categories — (a) no-history (universe member, zero bars), (b) thin
  (`0 < bar_count < indicators.min_history_bars`), (c) intra-series gap (trading days missing inside the
  member's own first→last range, measured against the benchmark SPY-bar calendar the existing coverage
  `gaps`/walk-forward already use). Each row: symbol + category + EXACT shortfall (bars-have/bars-needed;
  missing-day count + `[first_gap, last_gap]`). A fine member appears in none. NO score/return/bucket
  recompute; thresholds + calendar from config (no magic number). Surface on the EXISTING `GET /api/data`
  `coverage` payload alongside the J-36 `per_symbol` table.
- **J-37 Pull-missing job constructor (backend):** a helper that, given a diagnostic row (or "pull all"),
  builds a fetch job whose `symbols` + `[start, end]` are EXACTLY the diagnosed `(symbol, date)` shortfall
  (not the whole universe/window) and dispatches through the EXISTING J-34 chunked/checkpointed/resumable
  path (`run_data_job` / `start_data_job` over the config-selected source). Per-`(symbol,date)` idempotent
  via the EXISTING INSERT-new-only `DailyPrice` guard. Session-only `api_key` threaded request-only via
  the EXISTING `make_provider(source, api_key=...)` + scrub path. Expose as a thin call on the EXISTING
  `POST /api/data/jobs` (request body = the diagnosed gap). NO second fetch engine.
- **J-38 Unified Unfinished-imports view (backend):** a read-only union served on `GET /api/data`
  (new `unfinished_imports` array generalizing the existing `resumable_imports`) of every import that did
  not finish cleanly — `ImportCheckpoint` rows with `status == "resumable"` + `DataProviderRun` rows with
  `status` in (`partial`, `failed`), minus any soft-dismissed. Each row carries a plain-language state
  explanation ("Paused — hit a provider rate-limit (429); progress saved", "Partial — 142/158 symbols ok,
  16 failed", "Failed — every symbol failed; provider unreachable") + done/remaining/failed counts +
  chunk progress where applicable. Reads durable job-control state; recomputes NO canonical value.
- **J-38 Resume / Retry / Remove actions (backend + API):** Resume = the EXISTING
  `POST /api/data/jobs/{import_id}/resume` (`start_resume_job`) for a genuinely resumable checkpoint.
  Retry remaining/failed = re-dispatch ONLY outstanding/failed `(symbol,date)` work through the SAME
  import engine, per-`(symbol,date)` idempotent (no duplicate bar/row). Remove/Dismiss = drop ONLY the
  actionable job-control record — delete a resumable `ImportCheckpoint` row, OR set a new soft-dismiss
  flag (`dismissed: bool` column) on `DataProviderRun`. Add `POST /api/data/jobs/{id}/retry` and
  `POST /api/data/jobs/{id}/dismiss`. Retry/Resume of a needs-key source re-accepts the session-only key
  (request-only, redacted-URL + scrub path). MUST NOT delete/mutate any immutable
  `scanner_runs`/`scanner_results`/`*_scores`/`forward_returns` row OR the append-only
  `data_provider_runs` audit entry — a dismissed run still appears in Run history.
- **Frontend J-37 panel:** a Missing-data diagnostic panel on the EXISTING `/data` page (additive,
  alongside the J-36 Coverage panel) rendering the three categories with per-row symbol + category +
  exact shortfall (re-format backend values only). A per-row "Pull the missing data" button + a
  "Pull all missing" button that POST the EXISTING job-start path with the diagnosed gap, then surface
  live progress + final summary; on completion the row clears/shrinks and the J-36 coverage table
  reflects new bars. On provider failure show the explicit error / rate-limited state — fabricate nothing.
- **Frontend J-38 panel:** generalize the EXISTING ResumableImportsPanel into one unified
  Unfinished-imports section listing resumable + partial + failed, each with plain-language state +
  counts + chunk progress; Resume on resumable rows, Retry on partial/failed rows, Remove/Dismiss on
  every row (row leaves the list; Run-history table below is unchanged). Re-prompt for the session-only
  key on a needs-key Resume/Retry (request-only — never stored/echoed).
- **Re-capture only (NO code change expected):** J-39 Remove-data confirm-preview (preview path on the
  live host — never destructive confirm on a real symbol) and J-35 injected-provider expand end-to-end.
  Env-fix first: stop strays by port (no broad pkill), `rm -rf apps/frontend/.next`, restart `next dev`,
  confirm `GET /_next/static/chunks/main-app.js` → 200 and the health badge cleared BEFORE driving UI.

## Agents Required
- backend-data: yes -- J-37 diagnostic + gap-exact pull constructor, J-38 unfinished-imports union +
  Retry/Dismiss endpoints + soft-dismiss column, all reusing the existing coverage producer and J-34
  import engine. No second fetch path, no recompute.
- frontend-ux: yes -- two additive `/data` panels (Missing-data diagnostic with Pull buttons; unified
  Unfinished-imports with Resume/Retry/Remove), session-key re-prompt, no new route/nav.
- developer: yes -- the above (backend + frontend are one developer agent in this chain).

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/engine/data_manager.py` -- add `_missing_data_diagnostic` (3 honest categories,
  config threshold + benchmark calendar, exact shortfalls) wired into `compute_coverage`; add the
  gap-exact pull-job constructor reusing `start_data_job`/`run_data_job`; add `unfinished_imports` union
  (generalize `resumable_imports` + partial/failed `DataProviderRun`, minus dismissed) with
  plain-language state strings; add `retry_job` (re-dispatch outstanding/failed only) and `dismiss_run`
  (soft-dismiss / checkpoint delete) helpers.
- `apps/backend/app/api/data.py` -- accept the diagnosed-gap pull body on `POST /api/data/jobs`; add
  `POST /api/data/jobs/{id}/retry` and `POST /api/data/jobs/{id}/dismiss` (404 unknown id; 400/409
  needs-key without key); add `unfinished_imports` to the `GET /api/data` payload.
- `apps/backend/app/models.py` -- add `dismissed: bool = False` column to `DataProviderRun` (mutable
  job-control column, not a new table).
- `apps/backend/tests/test_db.py` -- verify the expected-tables set at line ~37 stays correct (a column
  adds no table; assert green in the SAME change — iter-22 lesson).
- `apps/backend/tests/test_data_manager.py` -- J-37 diagnostic per-category exact-shortfall +
  threshold-from-config + calendar-based gap + fine-member-absent + empty-dataset + no-recompute tests;
  J-37 pull constructor gap-exact + idempotent + reuses-J34 + provider-failure tests; J-38 union +
  state-strings + Retry-outstanding-only + Dismiss-preserves-audit tests.
- `apps/backend/tests/test_api_data.py` -- pull/retry/dismiss endpoint shapes + 4xx cases + the CRITICAL
  key-leak regression (REAL httpx error via `httpx.MockTransport` through the J-37 pull and J-38 retry →
  assert the sentinel key + `?token=`/`?apikey=` ABSENT from job-status `errors[]`, `unfinished_imports`,
  the checkpoint, and run history — MEMORY `httpx-error-leaks-url-query-key`).
- `apps/frontend/lib/api.ts` -- `MissingDataDiagnostic` types on `DataCoverage`; `UnfinishedImport` type;
  pull-missing, retry, dismiss API clients.
- `apps/frontend/app/data/page.tsx` -- Missing-data diagnostic panel (Pull / Pull-all); unified
  Unfinished-imports panel (Resume/Retry/Remove) replacing the ResumableImportsPanel; session-key
  re-prompt.

## UI Evolution
- New user-facing capability: read a plain-language Missing-data diagnostic naming every universe member
  insufficient for analysis (no-history / thin / intra-series gap) with its exact shortfall and pull
  exactly that gap with one click (J-37); see every unfinished import in one place with a plain-language
  state explanation and Resume / Retry / Remove it (J-38).
- New information displayed: the three honest diagnostic categories with per-row symbol + category +
  exact shortfall; a unified Unfinished-imports list (paused/resumable + partial + failed) each with a
  state explanation + done/remaining/failed counts + chunk progress.
- New user actions: "Pull the missing data" (per row) + "Pull all missing"; "Resume" (resumable),
  "Retry remaining/failed" (partial/failed), "Remove/Dismiss" (every unfinished row).
- UI surface changes: two additive panels on the EXISTING `/data` Data Manager page (Missing-data
  diagnostic; unified Unfinished-imports generalizing the existing Resumable-imports panel).
- Navigation changes: none. No new page, route, or sidebar entry — all additive on `/data`; no blueprint
  re-approval.

## Visual Requirements
- Component patterns: reuse the existing `/data` `Card` panels for both new sections; render the
  diagnostic and the unfinished-imports list as compact tables/rows (the project has no `Dialog`
  primitive — the J-39 panel uses a `Card` + overlay modal; reuse that pattern for any confirm/key
  re-prompt). Pull/Resume/Retry/Dismiss as buttons on each row; live progress reuses the existing job
  progress treatment.
- Layout: additive panels in the existing sidebar + main-content `/data` layout, beneath/alongside the
  J-36 Coverage panel and the existing import controls; dense, dark analytical workstation aesthetic.
- Key visual effects: match the existing `/data` panels (no new effects). thin/missing rows use the
  amber/muted treatment already established by the J-36 per-symbol table; failed imports use the danger
  treatment, resumable/paused amber.
- States to handle: loading (job polling), empty (no missing data → empty diagnostic, no spurious pull;
  no unfinished imports → empty section), error (provider-unreachable pull/retry → explicit
  error/rate-limited state, fabricate nothing; needs-key without key → explicit re-prompt).

## Key Test Scenarios
- **J-37 (browser, clean hydrated build):** the diagnostic renders all three categories with exact
  shortfalls against an injected-fixture dataset (a no-history member, a thin member, an intra-series-gap
  member); "Pull the missing data" constructs a job whose symbols/range == the diagnosed shortfall
  (assert the constructed job scope, not the whole universe/window); the offline injected-provider pull
  completes → the row clears/shrinks → the J-36 coverage table reflects new bars; a forced
  provider-unreachable pull surfaces an explicit error / rate-limited state, fabricating no bar.
- **J-38 (browser):** paused/partial/failed rows each show a plain-language state + counts + chunk
  progress; Resume continues from `next_chunk_index` (survives restart); Retry re-runs only
  outstanding/failed work (no duplicate bar/row); Remove/Dismiss drops the row while the Run-history
  audit log below is unchanged.
- **J-39 (browser, preview path on live host):** Remove-data confirm-preview (removable bars + range +
  protected committed-seed breakdown + dependent cascade) + seed-only refusal. Never run destructive
  confirm against a real symbol (MEMORY `j39-live-host-has-user-added-nvda-bars`).
- **J-35 (browser):** injected-provider expand end-to-end → passers + omitted-with-reason → grown
  `universe-count`.
- **J-18 (browser):** re-confirm exactly one date `<select>` per page across `/data` after the two new
  panels — pull/retry date inputs are job parameters, not a viewing-date control.
- **Unit/integration:** J-37 each category exact shortfall vs fixture, thin threshold from
  `indicators.min_history_bars` (no literal), gaps vs benchmark calendar, fine member in no category,
  empty dataset graceful, no `run_scan`/`score_stocks`/`forward_return`/`detect_*`/`score_regime`
  reachable from the diagnostic; pull constructor gap-exact + idempotent + reuses J-34 + provider-failure
  → explicit error/resumable; J-38 union (resumable + partial + failed minus dismissed), state strings,
  Resume from `next_chunk_index`, Retry outstanding-only no-duplicate, **Dismiss deletes ONLY the
  job-control record and leaves every snapshot/score/forward-return row AND the `data_provider_runs`
  audit entry intact**; **CRITICAL key-leak regression** via REAL httpx error through the full
  job-status→UI surface; `tests/test_db.py` green.
- **Error cases:** unknown `import_id` on resume/retry/dismiss → 404; resume/retry of a needs-key source
  with no key → explicit 400/409; pull/retry over a walled provider → explicit error/rate-limited, no
  fabricated bar; empty/no-gap diagnostic → empty diagnostic, no spurious pull.
- **Authoritative full backend suite green at the QA gate, run ONCE** (~14 min; do not run two pytest
  invocations concurrently — MEMORY `backend-test-suite-runtime`).

## Scope / Coherence Guardrails (flagged)
- **No second fetch/coverage path.** J-37 reads the SAME stored bars + `indicators.min_history_bars` +
  benchmark calendar the J-36 table/walk-forward use, and dispatches through the EXISTING J-34
  `start_data_job`/`run_data_job`. J-38 reads the canonical `ImportCheckpoint` + `DataProviderRun` rows
  and reuses the canonical `start_resume_job`. No rival module/endpoint/computation.
- **Two cascade boundaries stay strictly separate.** J-38 Remove/Dismiss drops ONLY a job-control record
  (a resumable checkpoint, or a `dismissed` flag on a run) — deletes NO price bar and NO snapshot. J-39
  Remove deletes user-added bars + their derived cascade and touches NO checkpoint. Do not conflate them.
- **Out of scope (exclude):** any new page/route/nav/nav-skeleton change; any change to
  scoring/scanner/regime/patterns/buckets/forward_testing/research/snapshot_serving or to any page other
  than `/data`, or `components/asof-provider.tsx`; no DB regen; re-implementing the J-39 cascade or J-35
  expand (only re-capture their browser flows); persisting/logging/echoing any pasted key; autonomously
  re-probing J-22/J-23/J-24 (Yahoo-429 data-walled, NON-HALTING/NON-VETOING — recorded honestly NA).
- **Dev handoff** at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-25-dev.md` — describe
  the code actually changed with the diff; do NOT restate the goal vision as implemented capability
  (iter-20 lesson).
