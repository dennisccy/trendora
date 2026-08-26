# Phase goal-market-compass-iter-18 — UI Test Plan

**Phase:** goal-market-compass-iter-18
**Date:** 2026-08-26
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Status

This iteration is **backend-only** (`Frontend Present: no`). Maintenance isolation is active — no
backend, frontend, browser QA, or replay lane ran. `reports/phase-goal-market-compass-iter-18-ui-surface-map.md`
records no surface as opened or changed this iteration ("No surface was opened or inspected"), so **Step
1 (new-surface smoke/happy-path/validation/error/UX test-case generation) is suppressed — there is no UI
surface map row to derive one from.**

Per the ui-test-designer's Backend-only phase handling, that suppression does **not** extend to
regression coverage for this phase's own journey metadata. The phase spec's own metadata lines
(`docs/phases/goal-market-compass-iter-18.md`) read:
- `Target journeys: J-11`
- `Required-still-passing journeys: J-01, J-04, J-10`

Together these name exactly **4** distinct journeys — the same 4 named by iteration 17's phase spec.
Each gets exactly one `UT-J-<id>` regression test case below, translated from that journey's own
"Steps:"/"Acceptance:" text in `docs/goal.md`'s "Must-have user journeys" section (read directly at
lines 203-236 for J-01, 301-351 for J-04, 589-938 for J-10, 939-1932 for J-11 — not re-derived from a
prior iteration's paraphrase alone).

**Read this before treating anything below as "nothing happened."** Unlike iteration 17 (which made
**zero** live database writes), this iteration made **exactly two authorized, permanent writes** to the
real production database (`apps/backend/data/trendora.db`): it created a new `maintenance_boundaries`
table and armed exactly one `j11-incident-recovery` row inside it. Per the dev handoff
(`docs/handoffs/goal-market-compass-iter-18-dev.md`) and this iteration's own live evidence
(`runs/goal-market-compass-iter-18/j11-iter18-live-preboot-guard-verification.json`,
`j11-iter18-full-table-sweep-diff.json`), the eleven incident-quarantine dates are now genuinely blocked
at the database level, through both boot-initiated code paths that could previously reach the canonical
`run_scan` (the named background-warmup cadence loop, plus a second, previously-unnoticed call site
inside `forward_testing._backfill`'s own cadence loop, found by re-deriving the boot/warmup call graph
this iteration). None of this has, or could have, any browser-visible effect yet — the app was never
booted this iteration (maintenance isolation, same discipline as iterations 13-17) — but the underlying
database state genuinely changed, and stays changed until a future, separately-authorized maintenance
action disarms it (not this iteration's job, and not attempted).

Because this iteration's diff touches none of `apps/backend/app/api/*`, `scoring.py`, `sectors.py`, or
`compass.py` (confirmed in the dev handoff's "Files Changed" section), **UT-J-01 and UT-J-04 carry
forward unchanged** from iteration 17's plan — none of their served values could have moved. **UT-J-10
is lightly updated** (this iteration is no longer a zero-live-write iteration, so its framing must say
so precisely). **UT-J-11 is substantially rewritten** to reflect this iteration's actual live-arm work.

**None of the steps below have been executed this iteration.** No browser-QA lane ran (maintenance
isolation is active). This plan is written for a future operator, or a future non-isolated iteration, to
execute once the backend and frontend are booted and maintenance isolation has lifted. Do not treat any
step below as already passed. Steps that only read this iteration's committed evidence files (see
UT-J-11) are the exception — those can be verified today, without booting anything, and unlike iteration
17's equivalent steps, they now prove a real, live change to production data, not merely an absence of
one.

---

## Global preconditions & safety notes (apply to multiple test cases below)

- **Backend + frontend running** via the project's prod scripts, frontend reachable at
  `http://localhost:3255`. As of this writing (iteration 18, 2026-08-26) maintenance isolation is still
  externally active and booting is not authorized — every browser-based test case below presumes that
  has since changed through legitimate owner action.
- **Current known state (re-derive, do not assume stale):** `scanner_runs` = 3,117 rows,
  `daily_prices` = 3,310,374 rows, `next_session_manifests` = 24 rows — all three confirmed **unchanged**
  and **content-fingerprint-identical** before vs. after this iteration's live sequence
  (`runs/goal-market-compass-iter-18/j11-iter18-full-table-sweep-before.json` vs. `-after.json`,
  `sweep.per_table.<table>.count` and `.fingerprint`). The "Latest" as-of still sits at **2026-07-23**,
  carried forward unchanged since iteration 16/17 — nothing in this iteration's diff touches a path that
  could move it. Treat these as the values observed when this plan was written, not a fixed
  forever-expectation.
- **NEW this iteration — the live database's table count moved from 24 to 25** (the one new
  `maintenance_boundaries` table; `j11-iter18-full-table-sweep-before.json`'s `sweep.table_count` is `24`,
  `-after.json`'s is `25`, and the diff file's `expected_new_tables_present` names exactly
  `["maintenance_boundaries"]` with `changed_existing_tables: []`). **Do not confuse this DB-level table
  count with the `/data` page's manifest count**, which is still `24` — a `next_session_manifests` row
  count, a different metric that happened to share the same number as the old table count purely by
  coincidence, and which this iteration did not touch.
- **The 11 incident dates** (do not use ANY of these as a manually-chosen `?asof=` value in any test
  below unless the test explicitly says otherwise): `2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13,
  2026-07-24, 2026-07-27, 2026-08-03, 2026-08-05, 2026-08-10, 2026-08-11, 2026-08-12`. Of these, only
  **2026-08-11 and 2026-08-12** actually lost raw `daily_prices` data the committed seed could not
  restore (J-10's now-closed recovery); the other nine only had their derived `scanner_runs` cleared by
  the same removal cascade (corrected reporting per this iteration's rider 6c, now reflected in
  `reports/phase-goal-market-compass-iter-17-ui-test-plan.md`).
  **Important nuance, unchanged by this iteration:** the newly-armed boundary gates only the two
  **boot-initiated** `run_scan` call sites (background historical warm-up's cadence loop and its
  `forward_testing._backfill` sub-call). It does **not** gate `compass.get_or_create_manifest`, the
  on-demand manifest-minting path a manual `?asof=` browser visit triggers — 7 of the 11 dates still
  have no manifest, and requesting one via the URL bar would still mint a forbidden historical manifest
  today, exactly as before this iteration. Arming the boundary closes the silent-boot-overwrite risk; it
  was never scoped to make manual `?asof=` navigation to an incident date safe. **Do not navigate any
  test below to `?asof=` one of these 11 dates.**
- **AVB's stored `daily_prices.volume`** was corrected in iteration 16 (`2026-08-11`/`2026-08-12` moved
  to `554,757`/`3,706,010`, OHLC unchanged) and re-classified (not re-derived) in iteration 17. **This
  iteration does not touch that data again** — the mutation-accounting sweep confirms `daily_prices`'
  row count and content fingerprint are identical before and after this iteration's live sequence.
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
- **Corroborating evidence (executable today, no boot needed):** this iteration's diff (per the dev
  handoff's "Files Changed" list) touches none of `scoring.py`, `sectors.py`, `apps/backend/app/api/*`;
  the mutation-accounting sweep additionally confirms `scanner_runs` (where `ScannerResult.sector` is
  stored) is row-count- and fingerprint-identical before/after — this journey's stored data could not
  have moved.

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
  `apps/backend/app/api/*`, `scoring.py`, `sectors.py`, or `compass.py` — the single source computing
  this journey's candidate trace (`compass.evaluate_selection`) is untouched, and the mutation-accounting
  sweep confirms `scanner_runs` and `next_session_manifests` are unchanged.

---

### UT-J-10 — Raw price recovery still doesn't destabilize normal serving (regression)

**Type:** regression
**Priority:** P1
**Surface:** none of its own — J-10's own Acceptance text states "Walkthrough: waived — raw-layer
incident repair with no UI surface change of its own... Final repaired-state `GET /api/compass` serving
and the J-01/J-02/J-03 replay belong exclusively to J-11 Stage G" (`docs/goal.md:931-937`; not yet
reached — this iteration's own conclusion remains `J-11 STAGE D READY: YES` / `J-11 STAGE D AUTHORIZED:
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
   preconditions" above and UT-J-11 below) — J-10's raw recovery is not evidence that the derived/scored
   view for those dates is safe to render; that determination belongs to J-11 Stage G, still not reached.

**Expected Result:**
- Step 1: `/stocks` loads normally, with no missing-price gaps, error banners, or blank rows for
  previously-affected symbols.
- Step 2: the stock detail page loads without error and shows a continuous price history up to the
  Latest as-of with no unexplained gap.
- **This iteration is not a zero-live-write iteration** — unlike iteration 17, it made exactly two
  authorized writes to the live database (the new `maintenance_boundaries` table, and one row inside
  it). Neither write touches `daily_prices`, and the mutation-accounting sweep proves it directly:
  `daily_prices`' row count (`3,310,374`) and content fingerprint are byte-identical in
  `j11-iter18-full-table-sweep-before.json` and `-after.json`, and `changed_existing_tables` in the diff
  file is `[]`. J-10's closed recovery is therefore untouched by this iteration, and AVB's iteration-16
  volume correction (see UT-J-11) is likewise a read-only citation this iteration, not a re-derivation.

---

### UT-J-11 — Maintenance boundary now genuinely ACTIVE and ARMED on the live database (regression)

**Type:** regression
**Priority:** P1
**Surface:** none of its own — J-11's own Acceptance text states "Walkthrough: waived — maintenance
repair of the derived layer with no UI surface of its own; the demo requirement is replaced by the
pre/post inventory, the mutation reconciliation, the cache-invalidation proof, and the
manifest-immutability evidence." (`docs/goal.md:1923-1925`). This iteration's own new claims are verified
via evidence artifacts, not the browser: `docs/handoffs/goal-market-compass-iter-18-dev.md`,
`runs/goal-market-compass-iter-18/j11-iter18-live-preboot-guard-verification.json`,
`runs/goal-market-compass-iter-18/j11-iter18-full-table-sweep-before.json` / `-after.json` / `-diff.json`.

**Preconditions:**
- Steps 1-3 (browser) require backend + frontend running — meaning maintenance isolation has, by the
  time this runs, been legitimately lifted by the owner. As of this writing (iteration 18, 2026-08-26) it
  is still externally active.
- Steps 4-7 (evidence-artifact reads) require **only the repository checkout**, not a running app — they
  can be executed right now, even while maintenance isolation remains active, since this iteration's
  live-write deliverables are committed evidence files describing an already-completed database change,
  not a state you need a booted app to observe.
- **Hard safety note, unchanged from iteration 17, read before running any browser step:**
  `compass.get_or_create_manifest` mints a brand-new historical manifest for ANY non-frontier as-of with
  no pre-existing one, regardless of caller. 7 of the 11 incident dates still have no manifest, and this
  iteration's guard does not gate that path (see "Global preconditions" above). Do **not** manually
  navigate this test (or any other) to `?asof=` one of the 11 incident dates.
- **Framing note — this iteration is materially different from iteration 17's.** Iteration 17 extended
  the guard's logic and added arm/disarm tooling but proved everything on **disposable fixtures only** —
  the live database was untouched (`MAINTENANCE BOUNDARY: NOT ACTIVE`, `LIVE PRE-BOOT GUARD: NOT ARMED`).
  This iteration executed the authorized live sequence — table-create, then arm, then live verification —
  against the real `apps/backend/data/trendora.db`, backend OFF throughout. The boundary is now genuinely
  active and armed on production, not merely on test fixtures.

**Steps:**
1. Navigate to `http://localhost:3255/` with **no** `?asof` parameter (Latest).
2. Note the as-of date shown.
3. Navigate to `http://localhost:3255/stocks`, search/filter for symbol `AVB`, and open its stock detail
   page. If the price/volume chart's visible date range extends to `2026-08-11` and `2026-08-12`, compare
   those two dates' volume bars against their immediate neighbors (`2026-08-05` through `2026-08-10`).
4. Open `docs/handoffs/goal-market-compass-iter-18-dev.md` and locate the "Final status (TC-16 —
   mandatory stop)" block and the "Before/after safety property" section at the top.
5. Open `runs/goal-market-compass-iter-18/j11-iter18-live-preboot-guard-verification.json` and locate the
   `armed`, `all_eleven_incident_dates_blocked`, `control_date_not_blocked`, `background_warmup_site_blocked`,
   `zero_scanner_runs_created_by_this_verification`, and `boundary_row.quarantined_dates_json` fields.
6. Open `runs/goal-market-compass-iter-18/j11-iter18-full-table-sweep-diff.json` and locate `clean`,
   `expected_new_tables_present`, `changed_existing_tables`, `unexpected_new_tables`, and
   `unexpected_removed_tables`.
7. Open `runs/goal-market-compass-iter-18/j11-iter18-full-table-sweep-before.json` and `-after.json` side
   by side and compare `sweep.table_count`, plus the `daily_prices`, `scanner_runs`, and
   `next_session_manifests` entries under `sweep.per_table` (their `count` and `fingerprint` fields).

**Expected Result:**
- Step 2: the Latest as-of is **not** one of the 11 incident dates. At the time this plan was written
  (2026-08-26) it was `2026-07-23`; expect that date or a later one as new normal sessions land — never
  one of the 11 listed dates. Seeing one of them as the normal Latest session would mean Stage D executed
  without authorization — a severe regression, not expected state.
- Step 3: **IF** the chart's range reaches these two dates, their volume bars still read consistent with
  the surrounding week (iteration 16's correction: `554,757`/`3,706,010`) — no re-introduced spike, no
  visible difference from iteration 16/17's figures (this iteration made zero writes to `daily_prices`,
  proven by the fingerprint match in step 7). **If the chart's range does not reach these dates**, record
  this sub-check as **not exercised**.
- Step 4: the Final status block reads **exactly**:
  ```
  J-11 MAINTENANCE BOUNDARY: ACTIVE
  J-11 LIVE PRE-BOOT GUARD: ARMED
  J-11 STAGE D READY: YES
  J-11 STAGE D AUTHORIZED: NO
  ```
  and the "Before/after safety property" section names, in prose, what starting Trendora could
  previously do (write a canonical `ScannerRun` onto `2026-08-12`, or any of the other ten quarantined
  dates, via either of two boot-initiated code paths) and what it can no longer do after this iteration's
  arm step.
- Step 5: `armed: true`; `all_eleven_incident_dates_blocked: true`; `control_date_not_blocked: true`
  (control date `2026-07-23`, i.e. `control_result.blocked: false`); `background_warmup_site_blocked:
  true` (proves the SECOND, previously-unguarded boot path is now covered too, not only the synchronous
  one); `zero_scanner_runs_created_by_this_verification: true`; `quarantined_dates_json` parses to
  exactly the eleven canonical dates listed in "Global preconditions" above — no more, no fewer.
- Step 6: `clean: true`; `expected_new_tables_present: ["maintenance_boundaries"]`;
  `changed_existing_tables: []`; `unexpected_new_tables: []`; `unexpected_removed_tables: []`.
- Step 7: `sweep.table_count` reads `24` in the before file and `25` in the after file (exactly +1);
  `daily_prices.count` = `3310374` in both, identical `fingerprint`; `scanner_runs.count` = `3117` in
  both, identical `fingerprint`; `next_session_manifests.count` = `24` in both, identical `fingerprint`;
  `maintenance_boundaries` is absent from the before file's `per_table` map and present in the after file
  with `count: 1`.

**Note — a confusable but NOT contradictory evidence file:**
`runs/goal-market-compass-iter-18/j11-iter17-readiness-db-file-true-start.json` and `-true-end.json`
(leftover naming from the reused iter-17 script) are **identical to each other** (`mtime
1787701766.6272907` in both). Do **not** read that as "this iteration made zero writes" — it only
brackets the read-only verification script's own run (step 4 of the 5-step live sequence), which
correctly made no further writes *after* the table-create and arm steps (steps 2-3) had already
committed. The genuine whole-sequence before/after comparison is step 7 above, which shows the real
delta: `mtime` moved from `1787670395.6520789` (pre-iteration baseline, matching the decomposer's
independently-captured figure exactly) to `1787701766.6272907` — changed, as expected from the two
authorized writes — while `size_bytes` (`8365871104`) and the `-wal` size (`0`) stayed unchanged.

**Escalate, do not silently note as fixed/expected:**
(a) any of the 11 incident dates appears anywhere in the app as a normal, non-disclosed session with
fresh scored output;
(b) Step 4's status block reads anything other than the exact four lines above — **especially**
`MAINTENANCE BOUNDARY: NOT ACTIVE` or `LIVE PRE-BOOT GUARD: NOT ARMED` (would mean this iteration's live
arm silently failed or was later reverted) or `STAGE D AUTHORIZED` reading anything other than `NO`
(the single most severe possible finding — Stage D was never authorized this iteration, under any
framing, even given full success);
(c) step 6/7 shows a non-empty `changed_existing_tables`, any `unexpected_new_tables`, or a `per_table`
fingerprint/count mismatch on any table other than the one authorized `maintenance_boundaries` addition —
would mean the table-create or arm step touched something outside its authorized scope;
(d) `sweep.table_count` in the after file is anything other than exactly `25`, or the `maintenance_boundaries`
row count is anything other than exactly `1`;
(e) AVB's `2026-08-11`/`2026-08-12` volume looks spiked (~2.8x neighbors) or different from iteration
16's corrected figures — a real finding, report it, don't fix the data yourself.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-J-01 | Sector attribution stays honest & near-complete | regression | P1 | `/stocks`, `/methodology` |
| UT-J-04 | Candidate why/why-not explanations stay complete | regression | P1 | `/` |
| UT-J-10 | Raw price recovery doesn't destabilize normal serving | regression | P1 | `/stocks`, stock detail |
| UT-J-11 | Maintenance boundary now genuinely ACTIVE and ARMED on the live database | regression | P1 | none (evidence-artifact only) |

**All 4 test cases are P1**, per the ui-test-designer's Backend-only phase handling rule: every journey
named on the phase spec's `Target journeys:` line (J-11) or `Required-still-passing journeys:` line
(J-01, J-04, J-10) gets exactly one `UT-J-<id>` regression row. This phase spec names only these 4
journeys (verified directly against `docs/phases/goal-market-compass-iter-18.md`'s own metadata lines).
No new-surface (smoke/happy-path/validation/error/UX) cases exist this iteration: `Frontend Present: no`
and the UI surface map records no row to derive one from.

**None of these 4 cases have been executed.** UT-J-01 and UT-J-04 carry forward unchanged from iteration
17's plan — this iteration's diff touches none of `apps/backend/app/api/*`, `scoring.py`, `sectors.py`,
or `compass.py`, so none of their served values could have moved. UT-J-10 is lightly updated to state
precisely that this iteration is no longer zero-live-write (two authorized writes happened, proven
scoped to only the new table via the mutation-accounting fingerprint sweep). UT-J-11 is substantially
rewritten: unlike iteration 17 (fixture-only proof, live database untouched), this iteration executed the
authorized live sequence — table-create, arm, verify — against the real database, and the boundary is now
genuinely `ACTIVE`/`ARMED` in production. Steps 4-7 of UT-J-11 (evidence-artifact reads) are provable
**today**, without waiting for maintenance isolation to lift; steps 1-3 (browser) must wait for a future
boot. `J-11 STAGE D AUTHORIZED` remains `NO` regardless — this iteration proves the safety substrate is
now live, not that Stage D may proceed.
