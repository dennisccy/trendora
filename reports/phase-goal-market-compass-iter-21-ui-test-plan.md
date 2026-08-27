# Phase goal-market-compass-iter-21 — UI Test Plan

**Phase:** goal-market-compass-iter-21
**Date:** 2026-08-27
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255 (NOT reachable this iteration — see Scope note)

---

## Scope note (backend-only phase, maintenance isolation active)

This phase spec's metadata carries `Frontend Present: no`. Iteration 21 executed J-11 Stage F — a
live, dependency-aware derived-cache invalidation across seven `dataset_version`-bearing cache
tables — entirely under maintenance isolation: no application-service boot, no browser, no HTTP
request against `:3255`/`:8000`/`:8255` was permitted or performed, and none is permitted while
this document is authored. The UI surface map report confirms nothing was mapped this iteration.
Per the backend-only handling rule, this plan therefore contains **zero new-surface
smoke/happy-path/validation/error/UX cases** — there is no UI surface map row to derive one from.

It DOES contain one regression case per journey named on the phase spec's own metadata lines:
- `Required-still-passing journeys: J-01, J-04, J-10`
- `Target journeys: J-11`

Together these name four distinct journeys — J-01, J-04, J-10, J-11 — each gets exactly one test
case below, ID `UT-J-<n>` (not the sequential `UT-01` scheme), Type `regression`, Priority `P1`.

Three of the four carry a `Walkthrough: waived` status in `docs/goal.md` for the parts that have no
UI of their own: J-10 is raw-layer only ("waived — raw-layer incident repair with no UI surface
change of its own... Final repaired-state `GET /api/compass` serving and the J-01/J-02/J-03 replay
belong exclusively to J-11 Stage G"); J-11 itself is likewise "no UI surface of its own" at the
journey level. J-01 and J-04 DO have real UI walkthroughs, currently **blocked** by maintenance
isolation and deferred to the next app-bootable iteration. **J-11 is the one exception this
iteration**: Stage F's own write (deleting the stale `availability_cache` row) has a concrete,
specific, deferred-but-executable UI consequence on `/data` — see UT-J-11 step 7 — which this plan
captures explicitly rather than folding into the generic "no UI surface" framing.

**Accuracy notes carried forward from iterations 19/20's corrections, binding for this plan too:**
- No cache-table row count below is asserted identical to any prior iteration's figure. Stage F
  legitimately deleted 1,643 rows across five tables this iteration. Every count in UT-J-11 is the
  **current, live** value, independently re-queried read-only against
  `apps/backend/data/trendora.db` while authoring this plan (2026-08-27), not copied from a report.
- Stage F is **COMPLETE**, but J-11 as a whole is **NOT repaired** — Stage G is the only stage
  permitted to declare the incident repaired. No case below implies J-11 resolution; UT-J-11 says so
  explicitly in its Preconditions and Expected Result.

---

## Test Cases

<!-- Test IDs use UT-J-<journey-id> per the backend-only-phase regression rule, not the sequential
     UT-XX scheme (that scheme is reserved for new-surface cases, none of which exist this iteration). -->

---

### UT-J-01 — Sector attribution stays honest and near-complete (regression carry-forward)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`, `/methodology`, `GET /api/stocks`

**Preconditions:**
- **BLOCKED THIS ITERATION.** Maintenance isolation (`docs/goal.md` J-11 Stage D→G ruling item 4,
  binding through Stage G) forbids application-service boot, browser use, or any HTTP request
  against the running app for the whole of iteration 21. This case cannot be executed now — file it
  as deferred verification for the next iteration that authorizes app boot, not as "already checked
  live" this iteration.
- When it IS run: backend and frontend started via the project's prod launch scripts; at least one
  `ScannerRun` exists at a recent as-of date (satisfied — live read-only query this iteration shows
  `scanner_runs` at 3,128 rows, unchanged by Stage F; see UT-J-11).
- No login is required — `/stocks` carries no auth gate on this project.

**Steps:**
1. Navigate to `http://localhost:3255/stocks` at the latest as-of date.
2. Open the "Sector" filter control and select the "Unassigned" option.
3. Read the count of members shown under "Unassigned" against the total resolved-member count shown
   on the page.
4. Pick one symbol known to be mapped via `config.stock_sectors` and one previously-unmapped pool
   name; compare the Sector cell in the `/stocks` leaderboard row, the sector shown on that symbol's
   stock detail header, and the `sector` field returned by `GET /api/stocks` for the same symbol.
5. Navigate to `http://localhost:3255/methodology` and locate the universe/data section.
6. At `GET /api/stocks`, find a symbol absent from BOTH `config.stock_sectors` and the pool-CSV
   alias map (`universe.pool_sector_aliases`).

**Expected Result:**
- Step 3: Unassigned share of resolved members is at most 5% (it was ~78% before J-01 shipped).
- Step 4: all three surfaces — leaderboard Sector cell, stock detail header, `GET /api/stocks` —
  show the identical stored sector label for both symbols; no surface computes its own sector.
- Step 5: the methodology page discloses the two-source sector basis (curated config first,
  pool-snapshot fallback) and states its current-only limitation (no point-in-time sector history).
- Step 6: that symbol serves `sector: null` and renders as "Unassigned" on `/stocks` — never a
  fabricated sector value.
- **Supporting evidence already gathered this iteration (no app boot required):**
  `docs/handoffs/goal-market-compass-iter-21-dev.md` "Files Changed" section states `scoring.py`
  (J-01) is untouched, verified via `git status --porcelain -uall`. Independently re-confirmed while
  authoring this plan: `git status --porcelain -uall | grep -E "scoring\.py|compass\.py|data_manager\.py"`
  returned **zero matches** — none of J-01's canonical files were touched by this iteration, so there
  is no code-level regression risk to find when the above steps are eventually run.

---

### UT-J-04 — Candidate why / why-not / what-would-change explanation stays consistent (regression carry-forward)

**Type:** regression
**Priority:** P1
**Surface:** `/` (home), `GET /api/compass`

**Preconditions:**
- **BLOCKED THIS ITERATION** — same maintenance-isolation reason as UT-J-01. Defer execution to the
  next app-bootable iteration.
- When it IS run: backend and frontend running; the latest as-of has a manifest with a non-empty
  focus/candidate section (if none clears the selection floor, the explicit
  `candidates_empty_reason` empty state applies instead of a bare empty list — that state is itself
  part of what this case checks).

**Steps:**
1. Navigate to `http://localhost:3255/` at the latest as-of date.
2. Compare the focus section's displayed candidate count against the count returned by
   `GET /api/compass` and the count named in the page's plain-English summary sentence.
3. Click into one candidate card; note its Leadership/Entry/Risk words and its score/bucket values.
4. On that same card, read every listed reason and caution (including the ATR caution) and the
   invalidation line.
5. Open the "Not priority" / why-not section; note the failed condition(s) and distance shown for
   two or three excluded names, and the aggregate exclusion counts shown.
6. Confirm the near-threshold shadow cohort does not appear anywhere in the focus section — not as a
   card, a pick, or a ranking input.

**Expected Result:**
- Step 2: all three counts (focus section, `GET /api/compass`, summary sentence) are identical.
- Step 3: the card's Leadership/Entry/Risk words are the config word-map values for the buckets
  served by `GET /api/stocks` for that ticker at the same as-of, and its score/bucket values match
  that same API row exactly.
- Step 4: every reason/caution cites a threshold and the stored actual value (the ATR caution's
  value/percentile equals the row's `risk_budget.atr_pct`); the invalidation line is the row's
  stored invalidation note verbatim.
- Step 5: exclusion counts partition exactly — member count minus candidate count equals "below
  selection floor" plus "excluded only by candidate cap," matching the manifest's frozen
  selection-disposition tallies re-read verbatim.
- Step 6: the shadow cohort is visible only inside the manifest audit view under its explicit
  research-only label — never in the focus section.
- No "buy/sell," return-promise, price-target, or proven-language wording appears anywhere on the
  card (AG-2, AG-1).
- **Supporting evidence already gathered this iteration:** the same zero-touch file proof as
  UT-J-01 covers `compass.py` (which computes the `evaluate_selection` trace this journey's whole
  card renders) — untouched by iteration 21, independently re-confirmed via
  `git status --porcelain -uall` while authoring this plan (zero matches).

---

### UT-J-10 — Raw price recovery stays terminal and unmutated (regression carry-forward)

**Type:** regression
**Priority:** P1
**Surface:** none — `daily_prices` table only. J-10 carries `Walkthrough: waived — raw-layer
incident repair with no UI surface change of its own` in `docs/goal.md`; there is no click path to
translate. (Final repaired-state serving belongs exclusively to J-11 Stage G, per J-10's own
Acceptance section, `docs/goal.md:931-937`.)

**Preconditions:**
- Requires only read-only access to `apps/backend/data/trendora.db` — NOT the running app, so unlike
  UT-J-01/UT-J-04 this case is **not** blocked by this iteration's maintenance isolation and can be
  run right now.
- Use read-only mode ONLY (`sqlite3 "file:<path>?mode=ro" "..."` — sanctioned for verification per
  this run's operational guardrails). Never open the file for write, never copy or move it.

**Steps:**
1. Run:
   `sqlite3 "file:apps/backend/data/trendora.db?mode=ro" "SELECT COUNT(*), MIN(date), MAX(date) FROM daily_prices;"`
2. Run:
   `sqlite3 "file:apps/backend/data/trendora.db?mode=ro" "SELECT symbol FROM daily_prices WHERE date='2026-08-11' AND symbol IN ('NVDA','AAPL','GRMN','EA','EQR');"`
   and the same query with `date='2026-08-12'`.
3. Confirm the only two symbols named in `docs/goal.md`'s "J-10 CLOSED — residual set accepted"
   bullet (EA, EQR) are absent from both dates' results in step 2, and every other queried symbol is
   present.

**Expected Result:**
- Step 1: `COUNT(*) = 3310374`, `MIN(date) = '1996-01-02'`, `MAX(date) = '2026-08-12'` — exactly the
  figures independently re-verified this iteration in
  `runs/goal-market-compass-iter-21/j11-stage-f-execute-mutation-accounting.json`'s `daily_prices`
  block (`.pre` and `.post` are byte-identical: same fingerprint
  `80441b37f816d41c3182d9559f03095b89d6c7973acf781c18f12b77be5024cc`, same row count, same min/max
  date — unchanged since iteration 20, since Stage F reads `daily_prices` only to compute
  `index_series_cache`'s stamp and never writes to it). Iteration 21 wrote zero rows to this table —
  J-10 stays closed and untouched.
- Step 2/3: NVDA, AAPL, GRMN are present on both 2026-08-11 and 2026-08-12 (part of the 585-symbol
  restored population); EA and EQR are absent from both, each for its recorded, owner-accepted
  reason (EA: no Yahoo trading data past 2026-08-10, a real delisting; EQR: only 1 comparable
  calibration pair, below the fixed 3-pair floor) — not reopened, not retried, not silently widened.
- No third date shows any row change; the price frontier remains 2026-08-12.

---

### UT-J-11 — Stage F dependency-aware cache invalidation, verified against this iteration's own live evidence (target journey)

**Type:** regression
**Priority:** P1
**Surface:** none for steps 1-6 (evidence-file / DB read-only) — deferred `/data` page
(`GET /api/data/availability`, the "Per-date availability" card) for step 7 only, once app boot is
authorized. J-11 carries `Walkthrough: waived` in `docs/goal.md` at the journey level, but Stage F's
own write has one concrete, specific, deferred UI consequence — see step 7 — which is captured here
rather than dismissed as "no UI surface."

**Preconditions:**
- Steps 1-6 require only reading files this iteration's completed live run already wrote, plus one
  read-only `sqlite3` query against `apps/backend/data/trendora.db` (never opened for write, never
  copied/moved) — no running app needed. **Not** blocked by maintenance isolation; runnable right now.
- Evidence directory `runs/goal-market-compass-iter-21/` exists with the 16 `j11-stage-f-execute-*.json`
  files; dev handoff at `docs/handoffs/goal-market-compass-iter-21-dev.md`.
- Step 7 IS blocked this iteration and every iteration until app boot is authorized (no earlier than
  J-11 Stage G under the current ruling). Do not attempt it against a live backend now — per the
  coordinator's operational note for this run, `scanner.resolve_run` is unguarded from any `?as_of=`
  read path and `compass.get_or_create_manifest` mints a manifest on any ordinary
  `GET /api/compass?as_of=<date>` request; a single request against one of the 11 quarantined
  incident dates could permanently write bad data.
- **Read this before running the case:** iteration 21 executed Stage F ONLY. Stage G (the only stage
  that may declare the incident repaired) remains outstanding. Per `docs/goal.md`'s Stage D→G ruling
  item 14, the incident stays `NOT REPAIRED — ATTEMPT INCOMPLETE` regardless of Stage F's own
  outcome. This case verifies Stage F's specific, bounded claim only — a PASS here is **NOT**
  evidence that J-11 as a whole now passes. Do not assert any cache table is row-count-identical to
  iteration 19 or 20's figures — 1,643 rows were legitimately deleted this iteration; every count
  below is the current, live value only.

**Steps:**
1. Open `docs/handoffs/goal-market-compass-iter-21-dev.md` and read its terminal status block
   (the seven `J-11 ...` lines near the top).
2. Open `runs/goal-market-compass-iter-21/j11-stage-f-execute-preflight-gate.json` and read
   `proceed` and `blocking_reasons`.
3. Open `runs/goal-market-compass-iter-21/j11-stage-f-execute-execution-result.json` and read
   `per_table` (each table's `disposition`, `pre_count`/`rows_deleted` or `attempted_write: false`)
   and `total_rows_deleted`.
4. Open `runs/goal-market-compass-iter-21/j11-stage-f-execute-verification-result.json` and read
   `ok` and each table's `post_count`.
5. Run:
   `sqlite3 "file:apps/backend/data/trendora.db?mode=ro" "SELECT (SELECT COUNT(*) FROM event_study_cache), (SELECT COUNT(*) FROM market_phase_cache), (SELECT COUNT(*) FROM forward_aggregate_cache), (SELECT COUNT(*) FROM coverage_snapshot), (SELECT COUNT(*) FROM availability_cache), (SELECT COUNT(*) FROM index_series_cache), (SELECT COUNT(*) FROM membership_timeline_cache), (SELECT COUNT(*) FROM scanner_runs), (SELECT COUNT(*) FROM forward_returns);"`
6. Open `runs/goal-market-compass-iter-21/j11-stage-f-execute-mutation-accounting.json` and read
   `all_checks_pass`, `table_sweep_diff.changed_existing_tables`, `daily_prices`,
   `maintenance_boundary_diff`, `manifest_diff`.
7. **DEFERRED — do not attempt now.** Once app boot is authorized: start backend/frontend via the
   project's prod launch scripts, navigate to `http://localhost:3255/data`, and look at the
   "Per-date availability" card (`data-testid="availability-heatmap"`).

**Expected Result:**
- Step 1: exactly these seven lines, verbatim, never a third or blended state:
  `J-11 STAGE D EXECUTED: YES` / `J-11 STAGE E COMPLETE: YES` / `J-11 STAGE F COMPLETE: YES` /
  `J-11 STAGE G VERIFIED: NO` / `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE` /
  `J-11 MAINTENANCE BOUNDARY: ACTIVE` / `J-11 LIVE PRE-BOOT GUARD: ARMED`. `STAGE F COMPLETE: YES` is
  real progress, but do not read it as "the incident is fixed" — the very next line says it isn't.
- Step 2: `proceed: true`, `blocking_reasons: []` — the fresh preflight found zero drift (boundary,
  Stage E end-state, engine identity, manifest, inventory, late-row hygiene all agreed) before any
  write was made.
- Step 3: `total_rows_deleted: 1643`; five tables show `attempted_write: true` with `rows_deleted`
  equal to `pre_count`: `event_study_cache` 18, `market_phase_cache` 1290,
  `forward_aggregate_cache` 333, `coverage_snapshot` 1, `availability_cache` 1
  (18 + 1290 + 333 + 1 + 1 = 1643); `index_series_cache` and `membership_timeline_cache` both show
  `attempted_write: false`, `rows_deleted: 0`.
- Step 4: `ok: true`; `post_count` is `0` for `event_study_cache`, `market_phase_cache`,
  `forward_aggregate_cache`, `coverage_snapshot`, `availability_cache`; `post_count` is `1` for
  `index_series_cache` and `1` for `membership_timeline_cache` (each equal to its own
  `expected_unchanged_count`).
- Step 5: query returns exactly `0|0|0|0|0|1|1|3128|6814320` — independently re-confirmed live,
  read-only, while authoring this plan (2026-08-27). Do NOT expect these first seven values to match
  any prior iteration's cache-table counts; only `scanner_runs` (3128) and `forward_returns`
  (6814320) are expected to be unchanged carry-forward figures, because Stage F never writes to
  those two tables.
- Step 6: `all_checks_pass: true`; `changed_existing_tables` is exactly `["availability_cache",
  "coverage_snapshot", "event_study_cache", "forward_aggregate_cache", "market_phase_cache"]` and
  nothing else; `daily_prices.pre` and `.post` are byte-identical (fingerprint
  `80441b37f816d41c3182d9559f03095b89d6c7973acf781c18f12b77be5024cc`, `row_count: 3310374`,
  `min_date: "1996-01-02"`, `max_date: "2026-08-12"`); `maintenance_boundary_diff.equal: true` with
  `pre_row_count`/`post_row_count` both `1`; `manifest_diff.equal: true` with
  `pre_row_count`/`post_row_count` both `24`.
- Step 7 (once run): the card shows the empty state — an icon, the title **"No availability yet"**,
  and the description **"There are no stored trading days to chart. Fetch real EOD prices to
  populate the dataset, then the per-date availability appears here."** It must NOT show a populated
  heatmap grid with no `data-testid="availability-stale-notice"` banner above it — that specific
  combination (a fully-populated-looking grid with no stale notice) was the actual pre-Stage-F bug
  this iteration fixed: `data_manager.availability_from_storage`'s "row exists, stamp mismatched, no
  ingest job in flight" branch (`data_manager.py:1741-1747`/`:1760-1763`) served the stored
  PRE-INCIDENT row labeled `stale: False` — i.e., presented as current, with the 11 incident dates
  missing or wrong and no visual indication anything was off. Stage F deleted that row, so
  `availability_from_storage` now returns `_availability_not_yet_computed_payload()`
  (`cells: []`, `stale: False`, `served_dataset_version: None`), which
  `shouldShowAvailabilityEmptyState` (`lib/availability-empty-state.ts`) correctly renders as the
  honest empty state instead. Seeing that empty state here — rather than a silently-served stale
  grid — is the deferred, user-facing proof that Stage F's correctness fix took effect. (If a later
  iteration's ingest/warm has already repopulated `availability_cache` by the time step 7 actually
  runs, a populated grid IS then legitimate — check its own stale-notice state and served
  `dataset_version` against a fresh live-recomputed stamp instead of assuming either outcome.) This
  fixture-level behavior is already proven in `test_tc10_availability_from_storage_honest_after_deletion`
  per the dev handoff; step 7 is the deferred, browser-level confirmation of the same fact.
- If ANY of the above disagrees with what the files/query actually show, treat it as a finding, not
  a formality — these values were independently re-derived by the ui-test-designer directly against
  the live database and the dev handoff on 2026-08-27, not merely copied from the module's own
  self-report.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-J-01 | Sector attribution carry-forward | regression | P1 | `/stocks`, `/methodology` (blocked this iteration — deferred) |
| UT-J-04 | Candidate why/why-not carry-forward | regression | P1 | `/` (blocked this iteration — deferred) |
| UT-J-10 | Raw price recovery stays terminal | regression | P1 | none — DB read-only (runnable now) |
| UT-J-11 | Stage F cache-invalidation evidence + deferred `/data` correctness check | regression | P1 | none for steps 1-6 (runnable now); `/data` for step 7 (blocked, deferred) |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-J-01 and UT-J-04 cannot produce a
verdict until maintenance isolation lifts and the app is bootable again; UT-J-10 and UT-J-11 steps
1-6 are executable immediately and were independently spot-checked while authoring this plan;
UT-J-11 step 7 is deferred to the same future app-bootable iteration as UT-J-01/UT-J-04.
