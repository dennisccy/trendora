# Phase goal-market-compass-iter-19 — UI Test Plan

**Phase:** goal-market-compass-iter-19
**Date:** 2026-08-26
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Status

This iteration is **backend-only** (`Frontend Present: no`). Maintenance isolation is active — no
backend, frontend, browser QA, or replay lane ran, and this designer lane did not boot anything or issue
any HTTP request either (per the coordinator note: authoring only).
`reports/phase-goal-market-compass-iter-19-ui-surface-map.md` records no surface as opened or changed
this iteration ("No surface was opened or inspected"), so **Step 1 (new-surface smoke/happy-path/
validation/error/UX test-case generation) is suppressed — there is no UI surface map row to derive one
from.**

Per the ui-test-designer's Backend-only phase handling, that suppression does **not** extend to
regression coverage for this phase's own journey metadata. `docs/phases/goal-market-compass-iter-19.md`'s
own metadata lines read:
- `Target journeys: J-11`
- `Required-still-passing journeys: J-01, J-04, J-10`

Together these name exactly **4** distinct journeys — the same 4 named by iterations 17 and 18. Each
gets exactly one `UT-J-<id>` regression test case below, translated from that journey's own
"Steps:"/"Acceptance:" text in `docs/goal.md`'s "Must-have user journeys" section (read directly at
lines 203-236 for J-01, 301-351 for J-04, 589-938 for J-10, 939-2087 for J-11 — not re-derived from a
prior iteration's paraphrase alone).

**Read this before treating anything below as "nothing happened."** Unlike iteration 18 (which added one
new table and armed one boundary row — no scanner data), **this iteration performed the single largest
live write of the whole J-11 recovery so far**: it regenerated all 11 quarantined incident dates' derived
state (`ScannerRun` + `ScannerResult`/`SectorScoreRow`/`ThemeScoreRow` children) through the unmodified
canonical scanning engine, under one freshly frozen execution identity. Per the dev handoff
(`docs/handoffs/goal-market-compass-iter-19-dev.md`), the reviewer's independent re-verification
(`reports/reviews/goal-market-compass-iter-19-review.md`, verdict **PASS**, zero CRITICAL/MINOR issues),
and this iteration's own 13 evidence artifacts (`runs/goal-market-compass-iter-19/j11-stage-d-execute-*.json`),
the outcome is:

```
J-11 STAGE D AUTHORIZED: YES
J-11 STAGE D EXECUTED: YES
J-11 STAGE E COMPLETE: NO
J-11 STAGE F COMPLETE: NO
J-11 STAGE G VERIFIED: NO
J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE
J-11 MAINTENANCE BOUNDARY: ACTIVE
J-11 LIVE PRE-BOOT GUARD: ARMED
```

**`STAGE D EXECUTED: YES` is real success, not the same as "the incident is fixed."** Forward-return hole
repair (Stage E), cache invalidation (Stage F), and the full acceptance-gate verification (Stage G) have
not run. The 11 incident dates now have genuine derived data behind them for the first time since Stage C
cleared them, but they remain firewalled behind the still-`ACTIVE` boundary/guard and are **not** yet
servable through the UI — that is Stage G's job. Do not read any test below as proof the incident is
closed; it is proof Stage D specifically succeeded, cleanly, within its authorized scope.

**None of the steps below have been executed this iteration.** No browser-QA lane ran (maintenance
isolation is active) and this designer lane issued zero HTTP requests. This plan is written for a future
operator, or a future non-isolated iteration, to execute once the backend and frontend are booted and
maintenance isolation has lifted. Do not treat any step below as already passed. Steps that only read
this iteration's committed evidence files (see UT-J-11) are the exception — those can be verified today,
without booting anything, since this iteration's live-write deliverables are committed JSON artifacts
describing an already-completed database change.

---

## Global preconditions & safety notes (apply to multiple test cases below)

- **Backend + frontend running** via the project's prod scripts, frontend reachable at
  `http://localhost:3255`. As of this writing (iteration 19, 2026-08-26) maintenance isolation is still
  externally active and booting is not authorized — every browser-based test case below presumes that
  has since changed through legitimate owner action.
- **Current known state (re-derive, do not assume stale — these are the values this iteration's own
  evidence recorded, per `j11-stage-d-execute-mutation-accounting.json`):**
  - `scanner_runs`: **3,128** total (was 3,117 before this iteration — **+11**, exactly the 11 newly
    regenerated incident dates; the pre-existing 34 `6261ca17…`-stamped legacy rows and 3,083
    NULL-stamped pre-stamping-era rows are proven byte-unchanged by direct query,
    `legacy_and_null_scanner_runs_unchanged: true`, exact counts 34/3,083/3,117 identical both sides).
  - `daily_prices`: **3,310,374** rows, fingerprint
    `80441b37f816d41c3182d9559f03095b89d6c7973acf781c18f12b77be5024cc`, `min_date 1996-01-02`,
    `max_date 2026-08-12` — all identical before and after this iteration's live write
    (`daily_prices_unchanged: true`). This iteration made **zero** writes to raw prices.
  - `next_session_manifests`: **24** rows, unchanged (`manifests_unchanged: true`).
  - `data_provider_runs`: **549**, unchanged. `watchlist`: **6**, unchanged.
  - `maintenance_boundaries`: **1** row, still `active=1`, same 11-date JSON array, unchanged
    (`maintenance_boundary_unchanged: true`) — this iteration did **not** deactivate, disarm, or
    otherwise touch the boundary armed in iteration 18.
  - The "Latest" as-of still sits at **2026-07-23**, carried forward unchanged since iteration 16/17/18 —
    Stage D never calls `compass.get_or_create_manifest` and never touches the frontier; nothing in this
    iteration's diff could have moved it.
- **NEW this iteration — 11 `ScannerRun` rows now exist for dates that had zero since Stage C** (ids
  **3148–3158**, ascending, one per `INCIDENT_DATES` value, all stamped with the single frozen identity
  `53d2ffd1…b7f6c55`). **Do not confuse this `scanner_runs` count (3,128) with `next_session_manifests`'
  unrelated count (24, unchanged) or with iteration 18's database table count (25, also unchanged this
  iteration — no schema/DDL migration ran)** — three different numbers, none of which this iteration
  conflates, but easy to conflate when reading quickly.
- **The 11 incident dates** (do not use ANY of these as a manually-chosen `?asof=` value in any test
  below): `2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03, 2026-08-05,
  2026-08-10, 2026-08-11, 2026-08-12`. **This rule is now more important than ever, not less** — these
  dates carry real, freshly-regenerated derived data for the first time, but Stage E (forward-return hole
  repair), Stage F (cache invalidation) and Stage G (the only stage that may declare them safe to serve)
  have not run. Manually visiting `?asof=` one of the 7 still-manifest-less dates would still mint a
  forbidden historical manifest against not-yet-fully-repaired state; visiting one of the 4 dates that
  already have a manifest (2026-08-05, -10, -11, -12) would still be exercising a serving path J-11's own
  Acceptance section reserves for Stage G ("Verification must not itself mint a manifest (trap)",
  `docs/goal.md:2025-2032`).
- **AVB's stored `daily_prices.volume`** was corrected in iteration 16 and classified `AVB-A` in
  iteration 17. **This iteration re-derived that classification fresh and read-only** (part of the
  preflight gate) and confirmed it is still exactly `AVB-A` — it did **not** touch the underlying data
  again (`daily_prices_unchanged: true`, fingerprint identical).
- **Do not repeat J-01's original delivery mechanism** (the seed-safe `/data` Remove panel + backfill
  over the last two trading days) to "test" sector attribution anywhere in this plan — that was a
  one-time setup step from the iteration that built the feature, not a repeatable regression check, and
  repeating it is a destructive action against committed data.

---

## Test Cases

<!-- Test IDs use UT-J-<journey-id> per the Backend-only phase handling rule: every journey named on
     the phase spec's Required-still-passing / Target journeys lines gets exactly one regression row,
     Type regression, Priority P1. There are no sequential UT-01.. NEW-surface cases this iteration. -->

---

### UT-J-01 — Sector attribution stays honest and near-complete (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`, `/methodology`, stock detail page

**Preconditions:**
- Backend + frontend running.
- At least one completed scan run already has `ScannerResult.sector` populated (true today) — this
  regression check re-verifies already-landed behavior and does **not** require a fresh Remove/backfill
  drill (see the safety note above).

**Steps:**
1. Navigate to `http://localhost:3255/stocks` with no `?asof` parameter (Latest as-of).
2. Find the Sector filter control and select its `"Unassigned"` option.
3. Note the number of rows shown and the total resolved-member count (visible elsewhere on the same
   page, e.g. an unfiltered count).
4. Clear the Sector filter. Click through to any single ticker's stock detail page.
5. Note the Sector value shown in that page's header.
6. Navigate to `http://localhost:3255/methodology`.

**Expected Result:**
- Step 3: Unassigned rows ÷ total resolved members is **≤ 5%** (it was ~78% before the journey that
  built this feature; a regression back toward that range is a fail).
- Step 5: the Sector value on the stock detail header equals the Sector cell shown for that same ticker
  on the `/stocks` leaderboard — one stored value, never two different labels for the same symbol.
- Step 6: the universe/data section on `/methodology` discloses the two-source sector basis (curated
  `config.stock_sectors` mapping first, pool-snapshot fallback second) and states its current-only
  limitation (no point-in-time sector history).
- No symbol anywhere shows a fabricated (non-null, non-"Unassigned") sector label when neither source
  maps it — an unmapped symbol must read `null`/"Unassigned", never a guess.
- **Corroborating evidence (executable today, no boot needed) — read this carefully, it is NOT the same
  claim iteration 18 made:** this iteration's diff (per the dev handoff's "Files Changed" list, confirmed
  by TC-17's `git status --porcelain -uall` grep against `app/api/*`, `scoring.py`, `sectors.py`,
  `compass.py` — zero matches) touches none of the code that computes or serves sector attribution. The
  pre-existing 3,117 `ScannerRun` rows are proven **byte-unchanged** by direct query, not by diff absence
  (`legacy_and_null_scanner_runs_unchanged: true` in `j11-stage-d-execute-mutation-accounting.json`) — so
  J-01's already-verified sector coverage on every previously-existing run is untouched. **Unlike
  iteration 18, this iteration's live write DID add 11 new `ScannerRun` rows** (ids 3148–3158) with their
  own `ScannerResult` rows, produced through the SAME unchanged `scoring.score_stocks` path (the new
  `j11_stage_d_execute.py` module calls `scanner.run_scan`, which internally calls the untouched scoring
  code — only the orchestration wrapper is new, never the scoring logic itself) — so the same
  single-source-of-truth guarantee this journey requires applies to those 11 dates too. Those 11 dates
  remain behind the still-`ACTIVE` boundary and are not yet visitable through the UI (see safety note) —
  do not attempt to spot-check their sector values via `?asof=` navigation.

---

### UT-J-04 — Candidate why/why-not explanations stay complete (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend + frontend running.

**Steps:**
1. Navigate to `http://localhost:3255/` (Latest as-of).
2. Count the cards in the "Next-session focus" section and compare against the candidate count named in
   the summary card's focus sentence.
3. Open one candidate card.
4. Read its Leadership/Entry/Risk word labels, buckets, scores, reasons, and cautions.
5. Read its eligibility checklist.
6. Read its "what would change this" panel.
7. Scroll to the `"Not priority"` section and read a few entries.
8. Note the current market-state band's regime word (visible at the top of `/`).

**Expected Result:**
- Step 2: the two counts match exactly.
- Step 4: each reason and caution line cites both a threshold AND a stored actual value — never a bare
  claim with no number behind it.
- Step 5: every checklist row carries exactly one verdict from the fixed set {Pass, Miss, Supportive,
  Neutral, Unknown, NA} plus a threshold and an actual value.
- Step 6: the panel lists each selection/qualifier rule with threshold, current value, and met/unmet.
- Step 7: each `"Not priority"` entry names its failed condition(s) with distances; nowhere on the page
  (not as a card, not as a pick, not in any ordering) does a near-threshold "shadow cohort" name appear —
  it may only exist inside a separate manifest audit view under an explicit research-only label.
- Step 8: if the band reads Risk-off, every focus candidate carries a `REGIME_RISK_OFF` caution and the
  list is framed as "worth monitoring next session" with zero entry-advice wording. If the band is not
  Risk-off on the day this is run, record this sub-check as **not exercised today** rather than failed —
  it is conditional on market state, not always reachable.
- **Corroborating evidence (executable today, no boot needed):** this iteration's diff touches none of
  `apps/backend/app/api/*`, `scoring.py`, `sectors.py`, or `compass.py` (TC-17 grep, zero matches) — the
  single source computing this journey's candidate trace (`compass.evaluate_selection`) is untouched.
  Stronger than iteration 18's equivalent claim: this iteration's own identity-comparison finding
  independently confirms `compass.py`, `session_delta.py`, and `engine_identity.py` have been byte-
  unchanged since iteration 12 (`git log`, cited in the dev handoff's "Identity comparison finding") — the
  same three files `compass.evaluate_selection`'s selection/delta/manifest logic depends on. The "Latest"
  as-of this journey reads from (2026-07-23) is not one of the 11 dates this iteration touched, so its
  served manifest and trace are additionally untouched in fact, not merely in code.

---

### UT-J-10 — Raw price recovery still doesn't destabilize normal serving (regression)

**Type:** regression
**Priority:** P1
**Surface:** none of its own — J-10's own Acceptance text states "Walkthrough: waived — raw-layer
incident repair with no UI surface change of its own... Final repaired-state `GET /api/compass` serving
and the J-01/J-02/J-03 replay belong exclusively to J-11 Stage G" (`docs/goal.md:931-937`; not yet
reached — this iteration's own conclusion is `J-11 STAGE D EXECUTED: YES` but `J-11 STAGE G VERIFIED:
NO`). Indirectly verified via `/stocks` and stock detail pages, which read the `daily_prices` table J-10
wrote into.

**Preconditions:**
- Backend + frontend running.
- J-10 is closed (owner, 2026-08-23): 585/587 symbols restored, `EA` and `EQR` explicitly accepted as
  fail-closed unrestorable residuals. This check re-verifies serving stability of that closed recovery,
  not the recovery procedure itself.

**Steps:**
1. Navigate to `http://localhost:3255/stocks` at the current Latest as-of.
2. Locate one of the symbols J-10's own verification record names as recovered/spot-checked (e.g. NVDA,
   AAPL, GRMN, AVB) and open its stock detail page.
3. Do **not** attempt to view any of the 11 incident dates for this symbol or any other (see "Global
   preconditions" above and UT-J-11 below) — J-10's raw recovery and this iteration's Stage D derived-data
   regeneration together are still not evidence that the served/scored view for those dates is safe to
   render; that determination belongs to J-11 Stage G, still not reached.

**Expected Result:**
- Step 1: `/stocks` loads normally, with no missing-price gaps, error banners, or blank rows for
  previously-affected symbols.
- Step 2: the stock detail page loads without error and shows a continuous price history up to the
  Latest as-of with no unexplained gap.
- **This iteration made exactly one authorized live write** — the Stage D regeneration of 11
  `ScannerRun`s and their children — and it did **not** touch `daily_prices` in any way. Proven directly,
  not merely by absence from a diff: `j11-stage-d-execute-mutation-accounting.json`'s `daily_prices`
  block shows `pre` and `post` with **identical** `row_count: 3310374`, `fingerprint:
  80441b37f816d41c3182d9559f03095b89d6c7973acf781c18f12b77be5024cc`, `min_date: 1996-01-02`, `max_date:
  2026-08-12`, `id_sum`, and `ohlcv_sum` — a stronger proof than a bare row-count match, since two
  different tables could coincidentally have the same row count but not the same content fingerprint.
  J-10's closed recovery is therefore untouched by this iteration, and AVB's iteration-16 volume
  correction (see UT-J-11) is likewise a read-only citation this iteration, not a re-derivation of the
  data itself.

---

### UT-J-11 — Stage D live regeneration succeeded, incident remains honestly unrepaired (regression)

**Type:** regression
**Priority:** P1
**Surface:** none of its own — J-11's own Acceptance text states "Walkthrough: waived — maintenance
repair of the derived layer with no UI surface of its own; the demo requirement is replaced by the
pre/post inventory, the mutation reconciliation, the cache-invalidation proof, and the
manifest-immutability evidence." (`docs/goal.md:2078-2080`). This iteration's own new claims are verified
via evidence artifacts, not the browser: `docs/handoffs/goal-market-compass-iter-19-dev.md`,
`reports/reviews/goal-market-compass-iter-19-review.md`, and the 13
`runs/goal-market-compass-iter-19/j11-stage-d-execute-*.json` files.

**Preconditions:**
- Steps 1-2 (browser) require backend + frontend running — meaning maintenance isolation has, by the
  time this runs, been legitimately lifted by the owner. As of this writing (iteration 19, 2026-08-26) it
  is still externally active.
- Steps 3-9 (evidence-artifact reads) require **only the repository checkout**, not a running app — they
  can be executed right now, even while maintenance isolation remains active.
- **Framing note — read before treating `EXECUTED: YES` as "the incident is fixed."** J-11's full
  Acceptance section (`docs/goal.md:1992-2080`) covers raw inputs, snapshot scope, **forward returns
  (Stage E)**, manifests, audit/evidence, **caches (Stage F)**, operational isolation, and the
  schema/identity/retry traps — spanning ALL of Stages D through G. This iteration proves only the
  Stage-D-scoped subset: raw inputs unchanged, exactly the 11-date snapshot scope regenerated under one
  frozen identity, manifests unchanged, and operational isolation held. Forward-return hole repair and
  cache invalidation are explicitly **not attempted** this iteration (Stage E/F, next iterations) — do
  not fail this test case for "forward returns not yet repaired"; that is the correct, honest, in-scope
  state today, not a defect.

**Steps:**
1. Navigate to `http://localhost:3255/` with **no** `?asof` parameter (Latest).
2. Note the as-of date shown.
3. Open `docs/handoffs/goal-market-compass-iter-19-dev.md` and locate the "Terminal status" block near
   the top.
4. Open `runs/goal-market-compass-iter-19/j11-stage-d-execute-gate-verdict.json` and locate
   `preflight_ok`, `boundary_ok`, `avb_ok`, `avb_classification`, `blocking_reasons`, and `proceed`.
5. Open `runs/goal-market-compass-iter-19/j11-stage-d-execute-historical-identity-comparison.json` and
   locate `fresh_engine_identity`, `any_historical_match`, and the three `comparisons.iteration_10` /
   `.iteration_14` / `.iteration_16_17_18_readiness` entries' `matches_fresh` values.
6. Open `runs/goal-market-compass-iter-19/j11-stage-d-execute-mutation-accounting.json` and locate the
   `checks` block (9 fields) and `table_sweep_diff.changed_existing_tables`.
7. Open the dev handoff's "Per-date regeneration" table (or
   `runs/goal-market-compass-iter-19/j11-stage-d-execute-regeneration.json`'s `completed`, `new_run_ids`,
   and `per_date_results` fields) and count the rows.
8. Open `runs/goal-market-compass-iter-19/j11-stage-d-execute-db-file-true-start.json` and
   `-db-file-true-end.json` side by side and compare `size_bytes` and `wal.size_bytes`.
9. Open `reports/reviews/goal-market-compass-iter-19-review.md` and confirm the verdict line.

**Expected Result:**
- Step 2: the Latest as-of is **not** one of the 11 incident dates. At the time this plan was written
  (2026-08-26) it was `2026-07-23`; expect that date or a later normal-session date — never one of the 11
  listed dates. Seeing one of them as the normal Latest session would mean Stage G-level serving occurred
  without authorization — the single most severe possible regression on this journey.
- Step 3: the block reads **exactly** these 8 lines:
  ```
  J-11 STAGE D AUTHORIZED: YES
  J-11 STAGE D EXECUTED: YES
  J-11 STAGE E COMPLETE: NO
  J-11 STAGE F COMPLETE: NO
  J-11 STAGE G VERIFIED: NO
  J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE
  J-11 MAINTENANCE BOUNDARY: ACTIVE
  J-11 LIVE PRE-BOOT GUARD: ARMED
  ```
- Step 4: `preflight_ok: true`, `boundary_ok: true`, `avb_ok: true`, `avb_classification: "AVB-A"`,
  `blocking_reasons: []`, `proceed: true` — the fresh preflight gate agreed with the certified baseline
  and let the write proceed.
- Step 5: `fresh_engine_identity` starts `"53d2ffd1..."` (full value
  `53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55`); `any_historical_match: true`;
  `comparisons.iteration_10.matches_fresh: false` (differs from the legacy `6261ca17…` value — expected,
  it is a genuinely different attempt); `comparisons.iteration_14.matches_fresh: true` and
  `comparisons.iteration_16_17_18_readiness.matches_fresh: true` (equals the readiness-time values —
  **this is expected, not a red flag**: `compute_engine_identity` is a pure function of `compass.py`/
  `session_delta.py`/`engine_identity.py`, byte-unchanged since iteration 12 per `git log`, and neither
  iteration 14 nor 16/17 ever wrote a `ScannerRun`, so the equality creates no data ambiguity).
- Step 6: all 9 fields under `checks` read `true`
  (`changed_tables_subset_of_stage_d_write_tables`, `daily_prices_unchanged`,
  `data_provider_runs_unchanged`, `legacy_and_null_scanner_runs_unchanged`,
  `maintenance_boundary_unchanged`, `manifests_unchanged`, `no_unexpected_new_tables`,
  `no_unexpected_removed_tables`, `watchlist_unchanged`); `changed_existing_tables` is **exactly**
  `["scanner_results", "scanner_runs", "sector_scores", "theme_scores"]` — no other table appears.
  **Gotcha, do not misread:** the same file's `table_sweep_diff.clean` field reads **`false`** — this is
  correct and expected, not a failure. `clean` means "literally zero tables changed anywhere"; Stage D is
  *authorized* to change exactly those 4 tables, so `clean: false` combined with
  `changed_tables_subset_of_stage_d_write_tables: true` together are the PASS signal, not a contradiction.
- Step 7: exactly **11** rows, `ScannerRun` ids **3148–3158** (contiguous, ascending), one per
  `INCIDENT_DATES` value in chronological order, every row's `engine_identity` equal to the single frozen
  value from step 5, and every row has a non-zero `ScannerResult`/`SectorScoreRow`/`ThemeScoreRow` child
  count (539–542 results, 31 sectors, 11 themes per date, per the dev handoff's table).
- Step 8: `size_bytes` is **identical** in both files (`8365871104`) — SQLite WAL mode does not grow the
  main file on write; `wal.size_bytes` grew from `0` (true-start) to `5475512` (true-end) — real
  committed write activity, expected and harmless (already checkpointed-readable via the WAL, per the
  reviewer's independent live query confirmation).
- Step 9: verdict is **PASS**, `issues` contains zero CRITICAL or MINOR entries (one NOTE only, about a
  missing standalone maintenance-isolation-refusals log file, explicitly not blocking).

**What this test case does NOT claim (explicitly out of scope, do not escalate as a defect):**
- Forward-return holes are not yet repaired (Stage E, next iteration).
- Caches (`event_study_cache`, `market_phase_cache`, etc.) are not yet invalidated/rewarmed (Stage F,
  next iteration) — moot today since the backend was never booted, so nothing stale has been served.
- The 11 incident dates are not yet servable through `/` or `/stocks` at their own as-of (Stage G, not
  reached) — do not attempt to view them (see "Global preconditions" above).
- The whole-attempt stop-on-first-failure and full-restart-on-retry semantics (J-11's named traps 5-8,
  `docs/goal.md:2041-2047`) are proven by the **43 fixture tests** (`test_j11_stage_d_execute.py`), not
  by this live run — the live run had zero failures, so a genuine live exercise of the stop/retry path
  correctly did not occur.

**Escalate, do not silently note as fixed/expected:**
(a) any of the 11 incident dates appears anywhere in the app as a normal, non-disclosed session with
fresh scored output — the single most severe possible finding;
(b) Step 3's status block reads anything other than the exact 8 lines above — **especially**
`STAGE E COMPLETE`, `STAGE F COMPLETE`, or `STAGE G VERIFIED` reading anything other than `NO` (would mean
scope crept beyond Stage D), `INCIDENT STATUS` reading anything other than `NOT REPAIRED — ATTEMPT
INCOMPLETE` (Stage D succeeding does not mean the incident is closed), or `MAINTENANCE BOUNDARY` reading
anything other than `ACTIVE` (would mean the boundary was improperly cleared, forbidden by the owner
ruling's item 11);
(c) step 6 shows `changed_existing_tables` containing anything outside the 4 authorized tables, any
`checks` field `false`, or `no_unexpected_new_tables`/`no_unexpected_removed_tables` `false`;
(d) step 5 shows the fresh identity matching the iteration-10 legacy value (`6261ca17…`) instead of
differing from it — would mean a stale/wrong identity was frozen;
(e) step 7 shows any count other than exactly 11 new rows, any id outside the 3148–3158 range, or any row
whose `engine_identity` differs from the single frozen value — a mixed-identity write is a severe
correctness failure this journey exists specifically to prevent.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-J-01 | Sector attribution stays honest & near-complete | regression | P1 | `/stocks`, `/methodology` |
| UT-J-04 | Candidate why/why-not explanations stay complete | regression | P1 | `/` |
| UT-J-10 | Raw price recovery doesn't destabilize normal serving | regression | P1 | `/stocks`, stock detail |
| UT-J-11 | Stage D live regeneration succeeded, incident remains honestly unrepaired | regression | P1 | none (evidence-artifact only) |

**All 4 test cases are P1**, per the ui-test-designer's Backend-only phase handling rule: every journey
named on the phase spec's `Target journeys:` line (J-11) or `Required-still-passing journeys:` line
(J-01, J-04, J-10) gets exactly one `UT-J-<id>` regression row. This phase spec names only these 4
journeys (verified directly against `docs/phases/goal-market-compass-iter-19.md`'s own metadata lines).
No new-surface (smoke/happy-path/validation/error/UX) cases exist this iteration: `Frontend Present: no`
and the UI surface map records no row to derive one from.

**None of these 4 cases have been executed.** UT-J-01 and UT-J-04's browser steps carry forward unchanged
from iteration 18's plan — this iteration's diff touches none of `apps/backend/app/api/*`, `scoring.py`,
`sectors.py`, or `compass.py`, so none of their served values (at the unaffected Latest as-of) could have
moved; their evidence citations are updated to reflect that `scanner_runs` grew by exactly 11 rows this
time, all attributable to the newly-authorized Stage D write, not a code change. UT-J-10 is lightly
updated with this iteration's own fingerprint-level `daily_prices` proof. **UT-J-11 is substantially
rewritten**: unlike iteration 18 (boundary armed, zero scanner data touched), this iteration executed the
authorized live Stage D regeneration itself — all 11 incident dates now carry real derived data under one
frozen identity, independently re-verified live by the reviewer, with the honest terminal status
`J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE` correctly preserved because Stages E, F, and G
have not yet run.
