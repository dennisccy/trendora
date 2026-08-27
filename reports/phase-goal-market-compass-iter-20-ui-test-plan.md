# Phase goal-market-compass-iter-20 — UI Test Plan

**Phase:** goal-market-compass-iter-20
**Date:** 2026-08-26
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255 (NOT reachable this iteration — see Scope note)

---

## Scope note (backend-only phase, maintenance isolation active)

This phase spec's metadata carries `Frontend Present: no`. Iteration 20 executed J-11 Stage E — a
live, additive-only `forward_returns` repair — entirely under maintenance isolation: no
application-service boot, no browser, no HTTP request against `:3255`/`:8000`/`:8255` was permitted
or performed, and none is permitted while this document is authored. The UI surface map report
confirms nothing was mapped this iteration. Per the backend-only handling rule, this plan therefore
contains **zero new-surface smoke/happy-path/validation/error/UX cases** — there is no UI surface
map row to derive one from.

It DOES contain one regression case per journey named on the phase spec's own metadata lines,
because those lines name journeys, not `none`:
- `Required-still-passing journeys: J-01, J-04, J-10`
- `Target journeys: J-11`

Together these name four distinct journeys — J-01, J-04, J-10, J-11 — each gets exactly one test
case below, ID `UT-J-<n>` (not the sequential `UT-01` scheme).

Two of the four (J-10, J-11) carry a `Walkthrough: waived` status in `docs/goal.md` — both are
backend incident-recovery journeys with **no UI surface of their own** ("waived — raw-layer incident
repair with no UI surface change of its own" for J-10; "waived — maintenance repair of the derived
layer with no UI surface of its own... the demo requirement is replaced by the pre/post inventory,
the mutation reconciliation, the cache-invalidation proof, and the manifest-immutability evidence"
for J-11). Their test cases below are therefore read-only file/database verifications, not click
paths — inventing a fake browser walkthrough for a journey the goal contract itself says has none
would be a fabrication, not a translation. The other two (J-01, J-04) DO have real UI walkthroughs;
their test cases below are genuine click paths translated from their own `docs/goal.md` Steps, but
are currently **blocked** by this iteration's maintenance isolation and must be deferred to the next
iteration that authorizes application-service boot.

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
  against the running app for the whole of iteration 20. This case cannot be executed now — file it
  as deferred verification for the next iteration that authorizes app boot, not as "already checked
  live" this iteration.
- When it IS run: backend and frontend started via the project's prod launch scripts; at least one
  `ScannerRun` exists at a recent as-of date (satisfied — iteration 20's own mutation-accounting
  evidence shows `scanner_runs` unchanged at 3,128 rows; see Expected Result).
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
  `docs/handoffs/goal-market-compass-iter-20-dev.md` "Files Changed" section records that
  `git status --porcelain -uall` grepped against `app/api/*`, `scoring.py`, `sectors.py`,
  `compass.py`, `data_manager.py` returned **zero matches**, both before and after the live Stage E
  write — none of J-01's canonical files were touched by this iteration, so there is no code-level
  regression risk to find when the above steps are eventually run.

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
  card renders) — untouched by iteration 20, confirmed by `git status --porcelain -uall`.

---

### UT-J-10 — Raw price recovery stays terminal and unmutated (regression carry-forward)

**Type:** regression
**Priority:** P1
**Surface:** none — `daily_prices` table only. J-10 carries `Walkthrough: waived — raw-layer
incident repair with no UI surface change of its own` in `docs/goal.md`; there is no click path to
translate.

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
  pre- and post-iteration-20 figures recorded in
  `runs/goal-market-compass-iter-20/j11-stage-e-execute-mutation-accounting.json`
  (`daily_prices.pre` and `.post` are byte-identical: same fingerprint
  `80441b37f816d41c3182d9559f03095b89d6c7973acf781c18f12b77be5024cc`, same row count, same min/max
  date). Iteration 20 wrote zero rows to this table — J-10 stays closed and untouched.
- Step 2/3: NVDA, AAPL, GRMN are present on both 2026-08-11 and 2026-08-12 (part of the 585-symbol
  restored population); EA and EQR are absent from both, each for its recorded, owner-accepted
  reason (EA: no Yahoo trading data past 2026-08-10, a real delisting; EQR: only 1 comparable
  calibration pair, below the fixed 3-pair floor) — not reopened, not retried, not silently widened.
- No third date shows any row change; the price frontier remains 2026-08-12.

---

### UT-J-11 — Stage E forward-return hole repair, verified against this iteration's own live evidence (target journey)

**Type:** regression
**Priority:** P1
**Surface:** none — `forward_returns` / `scanner_runs` / `next_session_manifests` tables only. J-11
carries `Walkthrough: waived` in `docs/goal.md`: "maintenance repair of the derived layer with no UI
surface of its own; the demo requirement is replaced by the pre/post inventory, the mutation
reconciliation, the cache-invalidation proof, and the manifest-immutability evidence." This case IS
that pre/post-inventory and mutation-reconciliation check, applied to this iteration's own artifacts.

**Preconditions:**
- Requires only reading files iteration 20's completed live run already wrote — no running app, no
  direct database access. Not blocked by maintenance isolation; can be run right now.
- Evidence directory `runs/goal-market-compass-iter-20/` exists with the `j11-stage-e-execute-*.json`
  files.
- **Read this before running the case:** iteration 20 executed Stage E ONLY. Stage F (cache
  invalidation) and Stage G (final verification/acceptance) remain outstanding. Per `docs/goal.md`'s
  Stage D→G ruling item 14, the incident stays `NOT REPAIRED — ATTEMPT INCOMPLETE` regardless of
  Stage E's own outcome. This case verifies Stage E's specific, bounded claim only — a PASS here is
  NOT evidence that J-11 as a whole now passes. Do not carry forward any assumption that
  `forward_returns` is row-count-identical to iteration 19's end state either — iteration 20
  legitimately grew it; distinguish the pre-existing 6,797,728 rows from the 16,592 rows this
  iteration added.

**Steps:**
1. Open `docs/handoffs/goal-market-compass-iter-20-dev.md` and read its terminal status block
   (the seven `J-11 ...` lines near the top).
2. Open `runs/goal-market-compass-iter-20/j11-stage-e-execute-mutation-accounting.json` and read
   `forward_returns_count`, `table_sweep_diff.changed_existing_tables`, `all_scanner_run_counts`,
   `manifest_diff`, and `maintenance_boundary_diff`.
3. Open `runs/goal-market-compass-iter-20/j11-stage-e-execute-population-report.json` and read
   `population_a_total_newly_inserted`, `population_a_rebuilt_incident_runs`,
   `population_b_retained_run_holes.pre_total` / `.post_total`, and
   `population_c_not_yet_mature.latest_run_check`.
4. Cross-check: does `population_a_total_newly_inserted` (step 3) equal
   `forward_returns_count.observed_delta` (step 2)?

**Expected Result:**
- Step 1: exactly these seven lines, verbatim, never a third or blended state:
  `J-11 STAGE D EXECUTED: YES` / `J-11 STAGE E COMPLETE: YES` / `J-11 STAGE F COMPLETE: NO` /
  `J-11 STAGE G VERIFIED: NO` / `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE` /
  `J-11 MAINTENANCE BOUNDARY: ACTIVE` / `J-11 LIVE PRE-BOOT GUARD: ARMED`.
- Step 2: `forward_returns_count.pre = 6797728`, `.post = 6814320`, `.observed_delta = 16592`,
  `.self_reported_total_inserted = 16592` (all four agree exactly);
  `table_sweep_diff.changed_existing_tables = ["forward_returns"]` and nothing else;
  `all_scanner_run_counts.pre = all_scanner_run_counts.post = 3128`; `manifest_diff.equal = true`
  with `pre_row_count = post_row_count = 24`; `maintenance_boundary_diff.equal = true` with
  `pre_row_count = post_row_count = 1`.
- Step 3: `population_a_total_newly_inserted = 16592`, matching the per-run breakdown for runs
  3148–3158 (2771, 2769, 2216, 2215, 1659, 1658, 1103, 1103, 549, 549, 0 — run 3158 correctly gets 0,
  the frontier date with no trading day after it); `population_b_retained_run_holes.pre_total`
  equals `.post_total` (both 16,614 — this hole population was already whole before Stage E ran;
  Stage E's obligation was to prove it never decreased, and it did not);
  `population_c_not_yet_mature.latest_run_check.forward_return_row_count = 0` with `ok: true`.
- Step 4: 16,592 = 16,592 — the loop's self-reported insert total reconciles exactly with the live
  `COUNT(*)` delta.
- If ANY of the above disagrees with what the files actually contain, or if the terminal status
  lines have changed since this plan was written, treat it as a finding, not a formality — these
  values were independently re-derived by the reviewer (PASS_WITH_NOTES verdict,
  `reports/reviews/goal-market-compass-iter-20-review.md`) against the live database, not merely
  copied from the module's own self-report.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-J-01 | Sector attribution carry-forward | regression | P1 | `/stocks`, `/methodology` (blocked this iteration — deferred) |
| UT-J-04 | Candidate why/why-not carry-forward | regression | P1 | `/` (blocked this iteration — deferred) |
| UT-J-10 | Raw price recovery stays terminal | regression | P1 | none — DB read-only (runnable now) |
| UT-J-11 | Stage E forward-return repair evidence | regression | P1 | none — evidence-file read-only (runnable now) |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-J-01 and UT-J-04 cannot produce a
verdict until maintenance isolation lifts and the app is bootable again; UT-J-10 and UT-J-11 are
executable immediately and should be run now.
