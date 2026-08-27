# Phase goal-market-compass-iter-22 — UI Test Plan

**Phase:** goal-market-compass-iter-22
**Date:** 2026-08-27
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255 (NOT reachable this iteration — see Scope note)

---

## Scope note (backend-only phase, maintenance isolation held for the whole iteration)

This phase spec's metadata carries `Frontend Present: no`. Iteration 22 executed J-11 Stage G — the
terminal, full incident-cleanliness acceptance gate — entirely under maintenance isolation: no
application-service boot, no browser, no HTTP request against `:3255`/`:8000`/`:8255` was permitted
or performed, and **none is permitted while this document is authored either** — the coordinator
dispatch is explicit that nothing may be started. The UI surface map report confirms nothing was
mapped this iteration. Per the backend-only handling rule, this plan therefore contains **zero
new-surface smoke/happy-path/validation/error/UX cases** — there is no UI surface map row to derive
one from.

It DOES contain one regression case per journey named on the phase spec's own metadata lines:
- `Required-still-passing journeys: J-01, J-04, J-10`
- `Target journeys: J-11`

Together these name four distinct journeys — J-01, J-04, J-10, J-11 — each gets exactly one test
case below, ID `UT-J-<n>` (not the sequential `UT-01` scheme), Type `regression`, Priority `P1`.

**What is genuinely new this iteration — read this before the cases below.** J-11's status changed
this iteration, for the first time in the whole D→G arc (iterations 19-21 all ended `NOT REPAIRED —
ATTEMPT INCOMPLETE`): Stage G ran live, passed all 12 acceptance categories, and performed its one
authorized write — deactivating the `j11-incident-recovery` maintenance boundary (`active: 1 → 0`,
row `id=1` preserved, all 11 quarantined dates still listed). The terminal status is now
`J-11 INCIDENT STATUS: FULLY REPAIRED`. **This does NOT mean the application is now safe to boot.**
Two request-path write routes remain unguarded **by design** — `scanner.py::resolve_run` (named
verbatim by `docs/goal.md` ruling item 5's deferral) and `compass.py::get_or_create_manifest` (the
same species of gap, but — precisely — NOT itself named by ruling item 5's text; left open only
because this iteration's own scoping decision declined to broaden scope to a call site nobody named)
— both deferred to a future maintenance-boundary hardening pass; whether to authorize a boot is an
explicit owner decision that has **not** been made. UT-J-11 below reflects the repair honestly while
making this distinction unambiguous throughout.

**Accuracy notes, binding for this plan (carried forward from iterations 19-21's own corrections,
verified fresh against the live database and this iteration's evidence files, 2026-08-27):**
- No table below is asserted row-count-identical to a prior iteration where it legitimately changed.
  `membership_timeline_cache` went **1 → 0** this iteration (a genuine content-staleness finding, not
  a bug — see UT-J-11 step 3). Every count cited is the current, live value, independently
  re-confirmed via a read-only `sqlite3` query while authoring this plan, not copied from a report.
- **History this plan reflects accurately, per the coordinator's own instruction:** the first review
  of this iteration's work returned FAIL — `stage_g_verdict`'s `membership_timeline_reconciled`
  category was computed as `disposition == "preserve_for_incremental_reuse" or disposition ==
  "explicit_delete"`, the only two values the upstream function can ever return, making it an
  always-true tautology and not a real check; compounding this, the irrevocable boundary-deactivation
  write ran BEFORE the one real reconciliation check (whether the corrective delete actually landed)
  in the original script ordering. A same-day fix pass added a genuine, failable check
  (`confirm_membership_timeline_deletion_matches_verification`, requiring a live post-delete
  `COUNT(*) == 0`, not merely that the code branched into the delete path), reordered the script so
  that check runs BEFORE the boundary write, extended the tautology-guard test parametrization from
  11 to all 12 `stage_g_verdict` categories, and added mutation-proof tests. The re-review returned
  PASS after independently reproducing the mutation conclusion and replaying the original run's
  recorded evidence through the corrected logic — i.e., the `FULLY REPAIRED` outcome is safe because
  the underlying delete genuinely happened and was independently re-confirmed, not merely because the
  original (flawed) verdict file said so. 71 tests passing after the fix pass (up from 63 originally).
  **No database write occurred during the fix pass** — the live database still reflects only the
  original run's one authorized write (the boundary flip); see UT-J-11 step 2's note.

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
- **BLOCKED THIS ITERATION.** Even though Stage G deactivated the `j11-incident-recovery` boundary,
  the coordinator dispatch for this iteration is explicit: nothing may be started, and the owner has
  not yet decided whether booting the app is safe (two request-path write gaps remain open — see the
  Scope note above). This case cannot be executed now — file it as deferred verification for the
  iteration that is explicitly authorized to boot the app, not as "already checked live" this
  iteration.
- When it IS run: backend and frontend started via the project's prod launch scripts; at least one
  `ScannerRun` exists at a recent as-of date (satisfied — live read-only query this iteration shows
  `scanner_runs` at 3,128 rows, unchanged by Stage G's own read-only verification work).
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
- **Supporting evidence already gathered this iteration (no app boot required):** J-01's own file
  (`apps/backend/app/engine/scoring.py`) shows zero diff from HEAD — independently re-confirmed while
  authoring this plan via `git diff --stat -- apps/backend/app/engine/scoring.py` (empty output).
  Iteration 22 touched only `j11_stage_g_verify.py` (new), `data_manager.py` (one guarded edit to
  `coverage_from_storage` only — see UT-J-11), `run_j11_stage_g_verify.py` (new), and their tests —
  none of J-01's canonical code, so there is no code-level regression risk to find when the above
  steps are eventually run.

---

### UT-J-04 — Candidate why / why-not / what-would-change explanation stays consistent (regression carry-forward)

**Type:** regression
**Priority:** P1
**Surface:** `/` (home), `GET /api/compass`

**Preconditions:**
- **BLOCKED THIS ITERATION** — same reason as UT-J-01: nothing may be started this iteration, and
  booting remains an unmade owner decision even with the boundary now deactivated. Defer execution to
  the iteration that explicitly authorizes app boot.
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
- **Supporting evidence already gathered this iteration:** `apps/backend/app/engine/compass.py` (which
  computes the `evaluate_selection` trace this journey's whole card renders) shows zero diff from
  HEAD — independently re-confirmed via `git diff --stat -- apps/backend/app/engine/compass.py`
  (empty output) while authoring this plan. `compass.py` is also one of the two files explicitly named
  as out-of-scope this iteration (the `get_or_create_manifest` request-path gap it contains was
  deliberately left untouched — see UT-J-11 step 4).

---

### UT-J-10 — Raw price recovery stays terminal and unmutated (regression carry-forward)

**Type:** regression
**Priority:** P1
**Surface:** none — `daily_prices` table only. J-10 carries `Walkthrough: waived — raw-layer
incident repair with no UI surface change of its own` in `docs/goal.md`; there is no click path to
translate. (Final repaired-state serving belongs exclusively to J-11 Stage G, per J-10's own
Acceptance section, `docs/goal.md:931-937` — and Stage G is exactly what this iteration executed;
see UT-J-11.)

**Preconditions:**
- Requires only read-only access to `apps/backend/data/trendora.db` — NOT the running app, so unlike
  UT-J-01/UT-J-04 this case is **not** blocked by this iteration's operational constraints and can be
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
  figures independently re-verified this iteration (both by Stage G's own `verify_raw_inputs` check,
  which re-derived the fingerprint `80441b37f816d41c3182d9559f03095b89d6c7973acf781c18f12b77be5024cc`
  fresh via `j11_maintenance.capture_pre_reset_inventory(...)['daily_prices']['fingerprint']` and
  found it byte-identical to the certified post-AVB-correction baseline, and by this
  ui-test-designer's own independent read-only query while authoring this plan). Unchanged since
  iteration 20 — Stage G, like Stage F and Stage E before it, never writes to `daily_prices`. J-10
  stays closed and untouched; J-11 Stage G reaching `FULLY REPAIRED` does not reopen or change J-10's
  own terminal state in any way.
- Step 2/3: NVDA, AAPL, GRMN are present on both 2026-08-11 and 2026-08-12 (part of the 585-symbol
  restored population); EA and EQR are absent from both, each for its recorded, owner-accepted
  reason (EA: no Yahoo trading data past 2026-08-10, a real delisting; EQR: only 1 comparable
  calibration pair, below the fixed 3-pair floor) — not reopened, not retried, not silently widened.
- No third date shows any row change; the price frontier remains 2026-08-12.

---

### UT-J-11 — Stage G terminal verification: J-11 now reports FULLY REPAIRED (target journey)

**Type:** regression
**Priority:** P1
**Surface:** none for steps 1-6 (evidence-file / DB read-only) — deferred `/data` page
(`GET /api/data/availability`, the "Per-date availability" card) for step 7 only, once the owner
authorizes app boot. J-11 carries `Walkthrough: waived — maintenance repair of the derived layer with
no UI surface of its own` in `docs/goal.md` at the journey level; per that same Acceptance section,
"the demo requirement is replaced by the pre/post inventory, the mutation reconciliation, the
cache-invalidation proof, and the manifest-immutability evidence" — exactly what steps 1-6 verify.

**Preconditions:**
- Steps 1-6 require only reading files this iteration's completed live run already wrote, plus a
  handful of read-only `sqlite3` queries against `apps/backend/data/trendora.db` (never opened for
  write, never copied/moved) — no running app needed. **Not** blocked by this iteration's operational
  constraints; runnable right now.
- Evidence directory `runs/goal-market-compass-iter-22/` exists with the 26 `j11-stage-g-verify-*.json`
  files; dev handoff at `docs/handoffs/goal-market-compass-iter-22-dev.md` (includes a "Fix Notes"
  section documenting the post-review correction — see the note on step 2 below).
- Step 7 IS blocked this iteration and remains blocked until the owner explicitly authorizes app
  boot — deactivating the maintenance boundary is **not** that authorization; it only removes one
  structural precondition for a future decision. Do not attempt step 7 against a live backend now:
  two request-path write routes remain unguarded by design (`scanner.py::resolve_run`,
  `compass.py::get_or_create_manifest`), and 7 of the 11 formerly-quarantined dates currently have
  **zero** `next_session_manifests` row (confirmed live in step 5) — an uncontrolled request reaching
  `get_or_create_manifest` for one of those 7 dates would mint a real, immutable (AG-12) manifest for
  a historical date outside the normal freeze-at-close pipeline, tripping the exact "manifest-minting
  trap" this whole session's evidence-gathering has been careful never to trip.
- **Read this before running the case:** this is the FIRST iteration in the whole J-11 D→G arc
  (iterations 19, 20, 21 each ended `NOT REPAIRED — ATTEMPT INCOMPLETE`) where the terminal status is
  `FULLY REPAIRED`. Do not assert any cache table is row-count-identical to iteration 19, 20, or 21's
  figures — `membership_timeline_cache` legitimately went from 1 row to 0 this iteration (a genuine
  finding, not a bug — step 3). Every count below is the current, live value only.

**Steps:**
1. Open `docs/handoffs/goal-market-compass-iter-22-dev.md` and read its terminal status block
   (the five `J-11 ...` lines near the top).
2. Open `runs/goal-market-compass-iter-22/j11-stage-g-verify-verdict.json` and read
   `category_results`, `failing_categories`, and `full_pass`.
3. Open `runs/goal-market-compass-iter-22/j11-stage-g-verify-membership-timeline-check.json` and
   `runs/goal-market-compass-iter-22/j11-stage-g-verify-membership-timeline-delete-action.json`.
4. Open `runs/goal-market-compass-iter-22/j11-stage-g-verify-write-path-classification.json` and
   read `counts_by_classification` and the two `still_open_and_deferred` entries at
   `app/api/compass.py:61` and `app/engine/scanner.py:348`.
5. Run:
   `sqlite3 "file:apps/backend/data/trendora.db?mode=ro" "SELECT id, name, active, quarantined_dates_json FROM maintenance_boundaries; SELECT (SELECT COUNT(*) FROM scanner_runs), (SELECT COUNT(*) FROM forward_returns WHERE run_id BETWEEN 3148 AND 3158), (SELECT COUNT(*) FROM next_session_manifests), (SELECT COUNT(*) FROM daily_prices), (SELECT COUNT(*) FROM event_study_cache), (SELECT COUNT(*) FROM market_phase_cache), (SELECT COUNT(*) FROM forward_aggregate_cache), (SELECT COUNT(*) FROM coverage_snapshot), (SELECT COUNT(*) FROM availability_cache), (SELECT COUNT(*) FROM index_series_cache), (SELECT COUNT(*) FROM membership_timeline_cache);"`
6. Open `runs/goal-market-compass-iter-22/j11-stage-g-verify-mutation-accounting.json` and read
   `unexplained_by_sweep`, `boundary_diff.mismatches`, and `table_diff.changed_existing_tables`.
7. **DEFERRED — do not attempt now.** Once the owner explicitly authorizes app boot: start
   backend/frontend via the project's prod launch scripts, navigate to
   `http://localhost:3255/data`, and inspect the "Per-date availability" card
   (`data-testid="availability-heatmap"`) for each of the eleven formerly-quarantined dates.

**Expected Result:**
- Step 1: exactly these five lines, verbatim — the first time this exact combination has appeared in
  the D→G arc:
  ```
  J-11 STAGE D EXECUTED: YES
  J-11 STAGE E COMPLETE: YES
  J-11 STAGE F COMPLETE: YES
  J-11 STAGE G VERIFIED: YES
  J-11 INCIDENT STATUS: FULLY REPAIRED
  ```
- Step 2: `full_pass: true`, `failing_categories: []`, and all 12 `category_results` keys
  (`audit_evidence_and_user_state`, `cache_dispositions`, `evidence_reinterpretation_check`,
  `forward_returns`, `manifests`, `membership_timeline_reconciled`, `named_traps`,
  `operational_isolation`, `preflight_gate`, `raw_inputs`, `snapshot_scope`,
  `write_path_classification`) read `true`. **Important caveat, for an honest read of this file:**
  this JSON was written by the ORIGINAL live run, before the reviewer found
  `membership_timeline_reconciled` was computed by an always-true tautology (see the Scope note's
  History paragraph above). The fix pass that corrected the logic did **not** re-run the live
  `--confirm` execution (the boundary is already inactive, so a second run would immediately halt at
  its own preflight gate rather than re-exercise anything) — instead, the review independently
  replayed this run's own recorded evidence through the corrected check and confirmed the same `true`
  result holds for the real reason (the delete genuinely happened and a live post-delete count
  genuinely read 0), not merely because the original tautology said so. Treat `full_pass: true` here
  as verified-safe for that reason, not merely as a self-report.
- Step 3: the check recomputed all 4 already-cached incident dates (`2026-05-12`, `2026-08-10`,
  `2026-08-11`, `2026-08-12`) via `_membership_timeline` against current storage. Three matched
  exactly. One did not — `2026-08-10`'s stored `exits` field was `["AMSC", "MARA"]`; the fresh
  recompute is `["MARA"]` (`AMSC` no longer resolves as an exit on that date); `size`/`entries`/
  `excluded` all still match for that date. `disposition: "explicit_delete"`, `reason: "1 field
  mismatch(es) found -- the row is stale and must be deleted"`. The delete-action file reads
  `"deleted": true`. This is a genuine, real finding this iteration's own check caught and repaired —
  not a residual concern, and not evidence of any regression elsewhere (root-causing exactly which
  earlier date's membership state fed the divergence is out of this iteration's scope per the dev
  handoff).
- Step 4: `counts_by_classification` reads exactly `{"guarded": 4, "stage_d_authorized_write": 1,
  "still_open_and_deferred": 7}` across 12 total sites found, zero unclassified. The
  `app/engine/scanner.py:348` entry (`run_scan`, inside function `resolve_run`) reads
  `"classification": "still_open_and_deferred"` and its note cites this as `docs/goal.md` ruling item
  5's FIRST named deferred gap, verbatim. The `app/api/compass.py:61` entry (`get_or_create_manifest`,
  inside function `compass`) also reads `"still_open_and_deferred"`, but — precisely, per its own
  note field — it is "the SAME species of gap... but not itself named by ruling item 5's text," left
  open only because this iteration's scoping decision declined to fix an unnamed call site (see
  `assumptions.md`'s logged entry). Ruling item 5's actual SECOND named gap is a third site entirely
  — `app/engine/data_manager.py:3762` inside `_do_backfill._persist` (also `still_open_and_deferred`,
  noted as "ordinary Data Manager persistence paths capable of calling run_scan()"). All three are
  confirmed still open, confirmed NOT touched this iteration. This iteration's own new guarded entry
  is `app/engine/data_manager.py:1556` inside `coverage_from_storage`, calling
  `refresh_coverage_snapshot_for`.
- Step 5: `maintenance_boundaries` returns exactly `1|j11-incident-recovery|0|["2026-05-12",
  "2026-05-13", "2026-07-10", "2026-07-13", "2026-07-24", "2026-07-27", "2026-08-03", "2026-08-05",
  "2026-08-10", "2026-08-11", "2026-08-12"]` — `active=0`, row `id=1`, all 11 dates still listed
  (deactivated, never deleted). The second query returns exactly
  `3128|16592|24|3310374|0|0|0|0|0|1|0` — independently re-confirmed live, read-only, while authoring
  this plan (2026-08-27) and cross-matching the coordinator dispatch's own cited live figures exactly.
  Do NOT expect the five explicit-delete cache counts or `membership_timeline_cache` to match any
  prior iteration's figures; `scanner_runs` (3128), `forward_returns` on the 11 incident runs
  (16592), `next_session_manifests` (24), and `daily_prices` (3310374) are the expected unchanged
  carry-forward figures from iterations 19-21, because Stage G's only writes are the two conditional
  ones named in the phase spec (the boundary flip; the membership-timeline delete), neither of which
  touches any of these four.
- Step 6: `unexplained_by_sweep: []`; `boundary_diff.mismatches` shows exactly two changed columns
  for row `id=1` — `active` (`true → false`) and `updated_at` — nothing else on that row changed;
  `table_diff.changed_existing_tables` lists exactly 11 tables (`availability_cache`,
  `coverage_snapshot`, `event_study_cache`, `forward_aggregate_cache`, `forward_returns`,
  `market_phase_cache`, `membership_timeline_cache`, `scanner_results`, `scanner_runs`,
  `sector_scores`, `theme_scores`), reconciling to exactly Stage D (`scanner_runs` +11 and its
  `scanner_results`/`sector_scores`/`theme_scores` children — independently re-confirmed live while
  authoring this plan: 5,942/341/121 rows respectively scoped to run ids 3148-3158, NOT 11 each —
  the child tables hold one row per scored symbol/sector/theme per run, not one per run), Stage E
  (`forward_returns`, +16,592), Stage F (the five cache tables it emptied), and this iteration's own
  one conditional data write (`membership_timeline_cache`, 1 → 0) — with the boundary's `active` flip
  verified separately (a full-row dump/diff, not the rowid-based table sweep, since a same-row-count
  flag flip is invisible to a row-count sweep by design).
- Step 7 (once run, and only once authorized): because all five explicit-delete cache tables
  (including `availability_cache`) currently hold 0 rows, the card should initially show the honest
  empty state — an icon, the title **"No availability yet"**, and the description **"There are no
  stored trading days to chart. Fetch real EOD prices to populate the dataset, then the per-date
  availability appears here."** — for all eleven dates, UNLESS a normal ingest/warm-up job has
  already repopulated `availability_cache` through its canonical producer by the time this check
  actually runs, in which case a populated grid is legitimate PROVIDED it shows genuinely current,
  correct data for all eleven dates (matching the Stage-D-rebuilt `ScannerRun` ids 3148-3158, mapped
  1:1 onto the eleven dates in that exact order — `2026-05-12`→3148, `2026-05-13`→3149,
  `2026-07-10`→3150, `2026-07-13`→3151, `2026-07-24`→3152, `2026-07-27`→3153, `2026-08-03`→3154,
  `2026-08-05`→3155, `2026-08-10`→3156, `2026-08-11`→3157, `2026-08-12`→3158) — never the OLD
  pre-incident values — and it carries no `data-testid="availability-stale-notice"` banner unless one
  is genuinely warranted by a fresh, live-recomputed `dataset_version` mismatch. The specific failure
  mode this whole J-11 arc exists to prevent: a populated-looking grid for these eleven dates with
  **no** stale banner where the underlying values are actually still the pre-incident ones — i.e.,
  "stale-labelled-current" data. Stage G's own live evidence (steps 1-6 above) is the proof this
  should not happen now; step 7 is the deferred, browser-level confirmation of the same fact, exactly
  as iteration 21's equivalent deferred check anticipated for the (then materially different) Stage-F
  cache-cleared-but-not-yet-verified state.
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
| UT-J-11 | Stage G terminal verification: FULLY REPAIRED + deferred `/data` correctness check | regression | P1 | none for steps 1-6 (runnable now); `/data` for step 7 (blocked, deferred — owner authorization required) |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-J-01 and UT-J-04 cannot produce a
verdict until the owner explicitly authorizes app boot; UT-J-10 and UT-J-11 steps 1-6 are executable
immediately and were independently spot-checked while authoring this plan; UT-J-11 step 7 is deferred
to the same future app-bootable iteration as UT-J-01/UT-J-04. Deactivating the maintenance boundary
this iteration is real progress but is explicitly **not** the same thing as authorizing a boot — do
not treat it as such when scheduling any of the deferred steps above.
