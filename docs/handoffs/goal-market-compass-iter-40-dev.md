# goal-market-compass-iter-40 Dev Handoff

**Phase:** goal-market-compass-iter-40
**Date:** 2026-09-02
**Agent:** developer
**Status:** complete

## What Was Built

J-15: the What-changed card's stock-kind accounting becomes complete and honest — every
bucket-crossing `_stock_changes` evaluates now lands in exactly one of shown / suppressed /
residual, "Suppressed moves" stops omitting the stock kind, and an above-threshold mover held
back by the display cap is disclosed as a residual instead of vanishing uncounted. Plus the two
declared golden repairs and the AG-8 gating passenger fix named in the spec.

### Step 0 — baseline (before any code change), per goal text step 1

Measured against the LIVE stored frontier pair `2026-08-11 → 2026-08-12` (the OLD code path,
before this iteration's fix — confirmed by reading the row through `GET /api/compass`, which
served the pre-existing stored row verbatim, `session_delta.stock_accounting` absent):
- 57 stock-kind bucket crossings evaluated total (`crossing_pairs`), 0 accounted anywhere.
- 14 clear `stock_score_min_change` (8.0); only 10 shown (`max_stock_items`); the other 4 —
  TRV (8.66), SJM (8.48), ALL (8.33), TTWO (8.14) — appear in neither `changes` nor `suppressed`.
- 43 below-threshold crossings never classified at all (0 stock-kind rows in the 36-entry
  `suppressed` list: sector 24 + theme 9 + breadth 2 + market 1).
Nothing was mutated or re-exported to gather this baseline (AG-12).

### Backend — `apps/backend/app/engine/session_delta.py`

`_stock_changes` now classifies the FULL `crossing_pairs` list against
`stock_score_min_change` (via the existing `_classify` helper, unchanged threshold semantics)
**before** the `max_stock_items` display bound is applied, then splits the classified list:
- `meets_threshold` (magnitude >= threshold) is sliced by the remaining display slots
  (`max_items - len(bounded_new)`, new-to-universe entries keep their pre-existing unconditional
  priority and are sliced first, unchanged behavior) into `shown_crossings` (displayed) and
  `residual_crossings` (met the threshold, bumped by the cap — count only, no per-name list).
- everything below threshold is `suppressed`, exactly as `_classify` already produced, but now
  over the FULL list instead of the pre-bound subset — so the existing flat
  `session_delta.suppressed` / `suppressed_count` now correctly include every below-threshold
  stock crossing.

`_stock_changes` returns a third value, `stock_accounting = {evaluated_count, shown_count,
suppressed_count, residual_count}` (`evaluated_count == shown_count + suppressed_count +
residual_count`), computed in the SAME pass over the already-materialized `crossing_pairs` list
— no new query, no second materialization (AG-8). `compute_delta` threads this through as
`session_delta.stock_accounting`, present whenever `previous_run` is not `None` (absent for the
explicit no-prior-run early return, matching how `rotation` behaves — verified this does not
change `test_no_prior_run_state_is_explicit`'s exact-dict assertion).

`max_stock_items` keeps its VALUE (10) and becomes display-cap-only in behavior (AG-15 — no
threshold value changed); its `config.yaml` comment was corrected to say so, since the old
comment ("bounds both compute and display") was no longer accurate. No new config key — reuses
`compass.delta.stock_score_min_change` / `compass.delta.max_stock_items` only.
`session_delta.py` stays a `test_no_magic_numbers.CALC_FILES` entry (verified — see Tests Run).

No change to `_sector_changes`/`_theme_changes`/`build_rotation`, `evaluate_selection`,
candidate membership, or any `compass.selection.*`/`compass.delta.*` VALUE.

### Frontend

- `apps/frontend/lib/api.ts`: added `SessionDeltaStockAccounting` interface and
  `SessionDelta.stock_accounting?: SessionDeltaStockAccounting` (OPTIONAL — absent on every
  `next_session_manifests` row frozen before this ships, AG-12: never backfilled).
- `apps/frontend/lib/stock-accounting-summary.ts` (new) — two pure, dependency-free helpers
  (mirrors the `why-not-summary.ts` iter-39 extraction convention so the optional-field guard is
  unit-testable under this project's plain-node/`tsx` convention):
  - `stockResidualDisclosureText(stockAccounting?)` — `null` when absent; otherwise
    `"${residual_count} more stock move(s) held back by the display cap"`, rendered even at
    `residual_count === 0` (an explicit, honest zero — never a blank).
  - `stockShownCapDisclosureText(stockAccounting?)` — `null` when absent OR
    `residual_count === 0`; otherwise `"Showing the top ${shown_count} stock move(s)"`.
- `apps/frontend/components/compass-whatchanged-card.tsx`: renders both disclosures. The
  shown-cap line sits right after the changes list (before the "Suppressed moves" `Disclosure`);
  the residual line sits after it, with a data-testid (`compass-whatchanged-stock-residual`)
  visibly distinct from `compass-suppressed-list`, satisfying TC-4's "visibly different text from
  the suppressed line" with no per-name list (AG-8).
- `apps/frontend/components/compass-focus-section.tsx` + `lib/api.ts` (AG-8 gating passenger,
  iter-39 evaluator's next-step item 1): `WhyNotFailedCondition.gating` is now `gating?: boolean`
  (was required, though absent on all 21 pre-iter-38 stored dates). The truthiness read
  `{failed.gating ? "" : " — advisory"}` (mislabeled an absent `gating` "— advisory") is replaced
  by a `gatingSuffix()` 3-state function: `undefined` -> `" — not recorded"`, `true` -> `""`,
  `false` -> `" — advisory"`.

### Test golden repairs (declared in the spec before running, JSON fixture edits only)

- `runs/goal-session-market-compass/journey-scripts/J-04.json` step 2: click target updated from
  the stale `"Not priority (20)"` to the CURRENT rendered summary, verified live against
  `?asof=2026-07-23` (`why_not_totals` absent on that row -> `whyNotSummary()`'s degraded branch):
  `"Not priority (20 shown — held-back counts unavailable for this manifest version)"`. Target
  date unchanged (`2026-07-23`).
- `runs/goal-session-market-compass/journey-scripts/J-14.json`: inserted a new step 4 — click the
  "Not priority" summary to expand the `<details>` disclosure — before the existing entry-quality
  text assertion (old step 3 asserted text inside a collapsed disclosure right after a bare
  `goto`, per `components/ui/disclosure.tsx` having no `open` attribute). Old step 3's `expect`
  was changed to the same top-level "Not priority (...)" text step 1 already asserts (visible
  without expanding); the new step 4 carries the original entry-quality assertion. Target date
  unchanged (still the default `/`, no `asof`).

## Files Changed

- `apps/backend/app/engine/session_delta.py` — `_stock_changes` classifies the full crossing list
  before bounding and returns `stock_accounting`; `compute_delta` serves it; module docstring
  updated.
- `apps/backend/tests/test_session_delta.py` — 5 new tests (see Tests Run).
- `apps/frontend/lib/api.ts` — `SessionDeltaStockAccounting` (new) +
  `SessionDelta.stock_accounting?`; `WhyNotFailedCondition.gating` made optional.
- `apps/frontend/lib/stock-accounting-summary.ts` (new) — pure disclosure-text helpers.
- `apps/frontend/lib/stock-accounting-summary.test.ts` (new) — 8 checks.
- `apps/frontend/components/compass-whatchanged-card.tsx` — renders the two new disclosures.
- `apps/frontend/components/compass-focus-section.tsx` — `gatingSuffix()` 3-state render.
- `config.yaml` — `compass.delta.max_stock_items` comment corrected (display-cap-only; no value
  change).
- `runs/goal-session-market-compass/journey-scripts/J-04.json`,
  `runs/goal-session-market-compass/journey-scripts/J-14.json` — declared golden repairs above.

## Tests Run

- **Backend, targeted** (`cd apps/backend && .venv/bin/python -m pytest tests/test_session_delta.py
  tests/test_compass.py tests/test_manifest_invariants.py tests/test_api_compass.py -q`):
  **151 passed, 0 failed.**
  - `test_session_delta.py` (22 tests, 5 new): `test_stock_accounting_present_and_closes_exactly_on_two_runs_fixture`,
    `test_no_prior_run_state_has_no_stock_accounting_key`,
    `test_zero_stock_crossings_yields_explicit_zero_accounting` (goal step 8c), a `many_crossings_run`
    fixture (12 above-threshold + 3 below-threshold crossings, cap 10) exercising
    `test_more_crossings_than_cap_close_via_shown_suppressed_residual` (goal step 8a — asserts the
    exact `{evaluated:15, shown:10, suppressed:3, residual:2}` partition and that the two
    lowest-magnitude above-threshold movers are excluded from `changes` without appearing in
    `suppressed`), and `test_new_to_universe_reduces_available_display_slots_for_crossings` (goal
    step 8b — 2 new-to-universe + 12 crossings, asserts new members consume display slots ahead of
    crossings while staying outside `stock_accounting`).
  - `test_no_magic_numbers.py` (targeted, `-q`): 1 pre-existing failure on `indicators.py` /
    `forward_testing.py` / `research.py` (untouched files) — this is the carried, non-blocking
    issue named in the iter spec's NOTES section, not introduced by this change; `session_delta.py`
    itself is NOT among the offenders (verified in the failure output).
- **Frontend fixture tests** (`cd apps/frontend && npx --no-install tsx lib/<file>.test.ts` — this
  box's Node v22.22.1 lacks TS type-stripping (`ERR_NO_TYPESCRIPT` even with
  `--experimental-strip-types`); used `npx tsx`, the same fallback the iter-39 handoff's `why-not-
  summary.test.ts` precedent used a different way):
  - `stock-accounting-summary.test.ts`: **8 passed** (absent-field guard x3, residual > 0 x3
    including a singular/plural check, residual === 0 x2).
  - `why-not-summary.test.ts` (regression check, unchanged): **6 passed**.
- **Frontend TypeScript build**: `NEXT_DIST_DIR=.next-verify npx next build` — compiled
  successfully, zero type errors, all 30 routes generated (the live `.next` dir is guarded against
  a build without `NEXT_PUBLIC_API_URL`; used the project's documented throwaway-dir escape
  hatch). Build-artifact diffs under the already-tracked `apps/frontend/.next-verify/` (a carried,
  non-blocking issue per the spec's NOTES) were reverted / cleaned after verification so this
  diff carries no build noise.
- **Live, non-mocked verification** (both services started via `scripts/start-backend.sh` /
  `scripts/start-frontend.sh`; no process was on ports 8255/3255 before this session; both
  stopped and confirmed dead afterward, restart-then-stop cycle also verified clean —
  `ss -ltnp` / `ps aux` clean):
  - `POST /api/compass/regenerate?as_of=2026-08-12&confirm=true` (the standard authorized call
    named in the spec's own OUT OF SCOPE carve-out) minted a NEW version (v11, `mode: at_ingest`,
    `prospective_eligible: false` — correct, a regenerate never mints an eligible prior) exercising
    the new fields on the live frontier pair, without touching the pre-existing v10 row:
    - `session_delta.stock_accounting == {evaluated_count: 57, shown_count: 10,
      suppressed_count: 43, residual_count: 4}` — TC-1, TC-2, TC-3 exactly, matching the goal
      text's cited numbers (10 + 43 + 4 = 57).
    - `suppressed_count` (top-level) == 79 == sector 24 + theme 9 + breadth 2 + market 1 +
      stock 43 — TC-4.
    - TRV/SJM/ALL/TTWO confirmed absent from the shown `changes` list (all 4 in residual) — TC-2.
    - All 43 stock-kind `suppressed` entries confirmed `magnitude < threshold (8.0)` — TC-3.
    - `candidate_rule_hash`, `cohort_rule_hash`, `session_delta.rotation`,
      `selection.candidates`, `selection.disposition_tally`, and all non-stock `changes` entries
      compared byte-identical between the pre-change v10 row and the new v11 row; the 10 shown
      stock entries and their order are also identical — TC-7.
    - Spot-check (TC-8): `GET /api/stocks?as_of=2026-08-11` / `?as_of=2026-08-12` — TRV
      87.71 (B) -> 79.05 (C), magnitude 8.66, matches the residual classification exactly; SMCI
      34.18 (E) -> 62.51 (D), magnitude 28.33, one of the 10 shown entries.
    - Live document validated against `docs/handoffs/trendora-next-session-manifest-v1.schema.json`
      via `jsonschema.validate` — passes, no schema-version bump needed.
  - Real browser (system Playwright/Chromium, not just curl — this box's `trendora-window` MCP
    server was unavailable this session, connection closed):
    - `/` (frontier, v11 data): body text contained `"4 more stock moves held back by the display
      cap"`, `"Showing the top 10 stock moves"`, and `"Suppressed moves (79)"` — TC-4, TC-4b live.
    - `/?asof=2025-04-15` (older manifest, `stock_accounting` genuinely absent): NO "more stock
      move" / "Showing the top" text anywhere, `"Suppressed moves (37)"` rendered using only its
      pre-existing counts, full page render, no "not reachable" / "Application error" text — TC-5.
    - `/?asof=2001-04-17` (pre-iter-38 manifest, `gating` genuinely absent): expanding "Not
      priority" showed `"leadership_min_score: 79.4 vs 80.0 (distance 0.6) — not recorded"` — TC-9.
  - `GET /api/compass?as_of=2026-07-23` confirmed TRV present in `selection.why_not` (J-04 step-2
    golden's `expect: "TRV"` still holds) and `GET /api/compass?as_of=2026-08-12` (default,
    post-regenerate) confirmed the exact J-14 golden text (`"Not priority (20 shown of 52 held
    back — 27 cap-excluded, 25 below-floor near-miss)"`, DXCM `"entry_min_score: 26.5 vs 70.0
    (distance 43.5) — advisory"`, `gating: false`) still matches live data.

## Known Issues

- **Full deterministic replay of J-15 and the two repaired goldens (J-04, J-14) against the
  merged results file, plus the eight required-still-passing journeys**: not run by this agent —
  browser-qa-agent's job per established project convention (same precedent as iter-39's
  handoff). This handoff's own live verification (above) directly confirms every numeric TC (1-9)
  the spec lists, at the API and rendered-DOM level, but the formal replay-and-record step is
  downstream.
- **TC-6 (manifest-build query-count instrumentation, before/after)**: not run as an automated
  instrumented test — no query-count harness exists in this codebase for `build_manifest_payload`
  to hook into today. Verified structurally instead: `_stock_changes`' two `session.exec(...)`
  calls (current-run and previous-run column-projected selects) are byte-identical to the
  pre-change code (diff confirms no new `session.exec`/`select(...)` call was added anywhere in
  the touched functions), and the existing AG-8 guard test
  `test_column_projected_reads_only_no_full_record_json_sweep` still passes unchanged.
- **The three missing walkthrough frames (J-05/J-06/J-12), J-14's retaken step-08 frame, and the
  full-document-height viewport setting for screenshots**: none of these are code files in this
  repo (the viewport behavior lives in the browser-qa-agent's own Chrome-automation runtime, not
  in a committed config) — nothing for the developer to change; these ride as browser-qa-agent /
  demo-narrator passengers per the spec.
- `apps/frontend/.next-verify/` remains tracked in git (pre-existing, spec-acknowledged carried
  issue, unrelated to this iteration) — its verification-build diffs were cleaned before this
  handoff, so this diff carries none of that noise.
- One live database write this session beyond reads: the single authorized
  `POST /api/compass/regenerate?as_of=2026-08-12&confirm=true` call named above (append-only new
  version row, AG-12-compliant — verified the pre-existing v10 row's `session_delta` still lacks
  `stock_accounting`, i.e. was not touched).
- No new dependency, no new env var, no schema-file version bump, no external network call this
  iteration.
