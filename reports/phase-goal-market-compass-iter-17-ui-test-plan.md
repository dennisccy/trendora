# Phase goal-market-compass-iter-17 — UI Test Plan

**Phase:** goal-market-compass-iter-17
**Date:** 2026-08-25
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Status

This iteration is **backend-only** (`Frontend Present: no`). Maintenance isolation is active — no
backend, frontend, browser QA, or replay lane ran. `reports/phase-goal-market-compass-iter-17-ui-surface-map.md`
records no surface as opened or changed this iteration ("No surface was opened or inspected"), so **Step
1 (new-surface smoke/happy-path/validation/error/UX test-case generation) is suppressed — there is no UI
surface map row to derive one from.**

Per the ui-test-designer's Backend-only phase handling, that suppression does **not** extend to
regression coverage for this phase's own journey metadata. The phase spec's own metadata lines
(`docs/phases/goal-market-compass-iter-17.md`) read:
- `Target journeys: J-11`
- `Required-still-passing journeys: J-01, J-04, J-10`

Together these name exactly **4** distinct journeys — narrower than iteration 16's plan, whose
`Required-still-passing journeys:` line carried an 11-journey "evaluator awareness" digest naming J-01
through J-11; iteration 17's line does not, and this plan follows iteration 17's own metadata exactly
rather than assuming the prior iteration's wider scope still applies. Each of the 4 gets exactly one
`UT-J-<id>` regression test case below, translated from that journey's own "Steps:"/"Acceptance:" text in
`docs/goal.md`'s "Must-have user journeys" section — never a generic "re-check journey X" placeholder.

This iteration's actual work (per `runs/goal-market-compass-iter-17/plan.md` and the phase spec): the
AG-8 fix bounding the whole-table load in `evaluate_boundary_for_date` (now correctly treats a
`NULL`-active row as blocking and a missing `maintenance_boundaries` table as a clean non-block); new
committed, production-capable arm and disarm entrypoints for the maintenance-boundary lifecycle (proven
only against disposable fixtures — **never invoked against the live DB**); the owner's 9 named tests
(A)-(I); a strictly read-only live verification confirming `maintenance_boundaries` is still absent and
`evaluate_boundary_for_date` still returns `blocked: False` for `2026-08-12`; a zero-live-writes proof
(DB file mtime/size/`-wal` size byte-identical at true start and true end); and a corrected AVB Stage D
readiness re-derivation (`AVB-B` → `AVB-A`, using `volume_override` in the counterfactual trace,
`READY: YES` unchanged). **This iteration makes zero live database writes of any kind** — stronger than
iteration 16, which made exactly one authorized live write (the AVB volume correction). None of this
iteration's work has any UI surface: J-11's own Acceptance text states "Walkthrough: waived — maintenance
repair of the derived layer with no UI surface of its own," and the phase spec itself states "New
user-facing capability: None... (walkthrough waived per docs/goal.md J-11 Acceptance)."

Because this iteration's diff touches none of `apps/backend/app/api/*`, `scoring.py`, `sectors.py`, or
`compass.py` (confirmed in the dev handoff per the execution plan's item 8), **UT-J-01, UT-J-04, and
UT-J-10 carry forward unchanged from iteration 16's plan** — none of their served values could have
moved. **UT-J-11 is substantially rewritten** to reflect this iteration's actual work.

**None of the steps below have been executed this iteration.** No browser-QA lane ran (maintenance
isolation is active). This plan is written for a future operator, or a future non-isolated iteration, to
execute once the backend and frontend are booted and maintenance isolation has lifted. Do not treat any
step below as already passed. Steps that only read this iteration's committed evidence files (see
UT-J-11) are the exception — those can be verified today, without booting anything.

---

## Global preconditions & safety notes (apply to multiple test cases below)

- **Backend + frontend running** via the project's prod scripts, frontend reachable at
  `http://localhost:3255`. As of this writing (iteration 17, 2026-08-25) maintenance isolation is still
  externally active and booting is not authorized — every browser-based test case below presumes that
  has since changed through legitimate owner action.
- **Current known state (re-derive, do not assume stale):** `scanner_runs` = 3,117 rows across 3,117
  distinct as-of dates, none of them an incident date; `daily_prices` = 3,310,374 rows; 24 manifests. The
  "Latest" as-of still sits at **2026-07-23**. These figures are carried forward unchanged from iteration
  16's writing (2026-08-25) because this iteration's own TC-12 zero-live-writes proof (DB file mtime,
  size, and `-wal` size byte-identical at true start and true end, matching the decomposer's
  independently-captured baseline: mtime `1787670395`, size `8365871104` bytes, `-wal` `0` bytes, table
  count `24`) confirms nothing in the live database moved during this iteration either. Treat these as
  the values observed when this plan was written, not a fixed forever-expectation.
- **The 11 incident dates** (do not use ANY of these as a manually-chosen `?asof=` value in any test
  below unless the test explicitly says otherwise): `2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13,
  2026-07-24, 2026-07-27, 2026-08-03, 2026-08-05, 2026-08-10, 2026-08-11, 2026-08-12`. Requesting
  `GET /api/compass?as_of=<date>` (which the frontend's `?asof=` param drives) on one of the 7 that
  currently carry no manifest would **mint a brand-new historical manifest**, an artifact J-11's contract
  forbids outside its own Stage G verification (not yet reached, not authorized). **Do not navigate to
  any of these 11 dates as a general-purpose regression check** — UT-J-11 below is the one test case that
  deliberately checks the app's behavior around this boundary without crossing it.
- **AVB's stored `daily_prices.volume`** was corrected in iteration 16 (the one live write that
  iteration made): the `2026-08-11`/`2026-08-12` cells moved from `1,549,436`/`10,350,885` to
  `554,757`/`3,706,010` (OHLC unchanged). **This iteration does not touch that data again** — it only
  re-derives a diagnostic classification label (`AVB-B` → `AVB-A`) from the already-corrected value using
  a more accurate counterfactual trace; see UT-J-11.
- **Do not repeat J-01's original delivery mechanism** (the seed-safe `/data` Remove-panel + backfill
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

---

### UT-J-10 — Raw price recovery still doesn't destabilize normal serving (regression)

**Type:** regression
**Priority:** P1
**Surface:** none of its own — J-10's own Acceptance text states "Walkthrough: waived — raw-layer
incident repair with no UI surface change of its own... Final repaired-state `GET /api/compass` serving
and the J-01/J-02/J-03 replay belong exclusively to J-11 Stage G" (not yet reached; this iteration's own
conclusion remains `J-11 STAGE D READY: YES` / `J-11 STAGE D AUTHORIZED: NO`). Indirectly verified via
`/stocks` and stock detail pages, which read the `daily_prices` table J-10 wrote into.

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
- This iteration (17) makes **zero** live database writes of any kind (TC-12), and its AVB Stage D
  reclassification (see UT-J-11) is a read-only diagnostic re-derivation, not a raw-data change — neither
  reopens nor affects J-10's closed recovery in any way.

---

### UT-J-11 — Maintenance-boundary lifecycle hardened in code; live app provably untouched (regression)

**Type:** regression
**Priority:** P1
**Surface:** none of its own — J-11's own Acceptance text states "Walkthrough: waived — maintenance
repair of the derived layer with no UI surface of its own." This iteration adds a bounded-query fix, two
new CLI entrypoints, 9 new owner-named tests, and a corrected AVB diagnostic label — **none of it reaches
any page**, and this iteration made **zero** live database writes (TC-12). What this test case actually
verifies is the absence of any live-visible effect, plus the correctness of the artifacts this iteration
DID produce (which live as files, not UI). Indirectly verified via `/` (Latest as-of), AVB's stock detail
page (volume display, unchanged from iteration 16's correction), and `/data` (manifest count). This
iteration's own new claims are verified via evidence artifacts, not the browser:
`docs/handoffs/goal-market-compass-iter-17-dev.md`,
`runs/goal-market-compass-iter-17/j11-iter17-live-preboot-guard-verification.json`,
`runs/goal-market-compass-iter-17/j11-iter17-readiness-db-file-true-start.json` / `-true-end.json`, and
`runs/goal-market-compass-iter-17/j11-iter17-stage-d-readiness.json`.

**Preconditions:**
- Steps 1-4 (browser) require backend + frontend running — meaning maintenance isolation has, by the
  time this runs, been legitimately lifted by the owner. As of this writing (iteration 17, 2026-08-25) it
  is still externally active.
- Steps 5-7 (evidence-artifact reads) require **only the repository checkout**, not a running app — they
  can be executed right now, even while maintenance isolation remains active, since this iteration's
  deliverables are committed files, not live state.
- **Hard safety note, read before running any browser step:** `compass.get_or_create_manifest` mints a
  brand-new historical manifest for ANY non-frontier as-of with no pre-existing one, regardless of
  caller. 7 of the 11 incident dates currently have no manifest. Do **not** manually navigate this test
  (or any other) to `?asof=` one of the 11 incident dates — doing so would itself create the forbidden
  artifact this journey exists to prevent.
- **Framing note:** this iteration extended the fail-closed pre-boot guard (a bounded-query rewrite that
  correctly treats a `NULL`-active row as blocking and a missing `maintenance_boundaries` table as a
  clean non-block) and added committed, production-capable arm and disarm entrypoints — but proved every
  bit of it against **disposable fixture databases only**; the arm entrypoint has never been invoked
  against `apps/backend/data/trendora.db`, and nothing is armed there. The live DB was touched only by
  two strictly read-only queries (`mode=ro` + `PRAGMA query_only=ON`). More code existing is not, by
  itself, evidence that arming or booting is now safer or authorized — that remains an owner-controlled
  decision this iteration explicitly did not make.

**Steps:**
1. Navigate to `http://localhost:3255/` with **no** `?asof` parameter (Latest).
2. Note the as-of date shown.
3. Navigate to `http://localhost:3255/stocks`, search/filter for symbol `AVB`, and open its stock detail
   page. If the price/volume chart's visible date range extends to `2026-08-11` and `2026-08-12`, compare
   those two dates' volume bars against their immediate neighbors (`2026-08-05` through `2026-08-10`).
4. Navigate to `http://localhost:3255/data` and read the manifest count shown.
5. Open `docs/handoffs/goal-market-compass-iter-17-dev.md` and locate the four `J-11 ...` status lines
   and the paragraph discussing the live-arm sub-step of the owner's requirements 4 and 7.
6. Open `runs/goal-market-compass-iter-17/j11-iter17-live-preboot-guard-verification.json` and locate the
   `sqlite_master` table-count result and the `evaluate_boundary_for_date` result for `2026-08-12`.
7. Open `runs/goal-market-compass-iter-17/j11-iter17-readiness-db-file-true-start.json` and
   `-true-end.json` side by side and compare the `mtime`, `size`, and `-wal`-size fields.

**Expected Result:**
- Step 2: the Latest as-of is **not** one of the 11 incident dates. At the time this plan was written
  (2026-08-25) it was `2026-07-23`; expect that date or a later one as new normal sessions land — never
  one of the 11 listed dates. Seeing one of them as the normal Latest session would mean Stage D executed
  without authorization — a severe regression, not expected state.
- Step 3: **IF** the chart's range reaches these two dates, their volume bars still read consistent with
  the surrounding week (iteration 16's correction: `554,757`/`3,706,010`, down from
  `1,549,436`/`10,350,885`) — no re-introduced spike, and no visible difference from iteration 16's
  figures either (this iteration makes zero writes, so nothing should have moved again). **If the chart's
  range does not reach these dates**, record this sub-check as **not exercised**.
- Step 4: the manifest count is unchanged at 24.
- Step 5: the four lines read **exactly**:
  ```
  J-11 STAGE D READY: YES
  J-11 STAGE D AUTHORIZED: NO
  J-11 MAINTENANCE BOUNDARY: NOT ACTIVE
  J-11 LIVE PRE-BOOT GUARD: NOT ARMED
  ```
  and the live-arm sub-step of the owner's requirements 4 and 7 is explicitly named as blocked/`STALLED`
  by the table's absence — never silently omitted, never silently attempted.
- Step 6: the table-count query reads `0` (`maintenance_boundaries` still does not exist) and
  `evaluate_boundary_for_date` for `2026-08-12` reads `blocked: False` — both identical to the
  pre-iteration exposure, proving the guard's rewrite changed no live behavior because nothing is armed.
- Step 7: the `mtime`, `size`, and `-wal`-size fields are byte-identical between true-start and true-end,
  and true-start matches the independently-captured baseline exactly (`mtime 1787670395`,
  `size 8365871104`, `-wal 0`).
- **Escalate, do not silently note as fixed:** (a) any of the 11 incident dates appears anywhere in the
  app as a normal, non-disclosed session with fresh scored output; (b) any of the four status lines reads
  differently than specified — especially `MAINTENANCE BOUNDARY: ACTIVE` or `LIVE PRE-BOOT GUARD: ARMED`,
  which would mean the live table was created or a boundary was armed against production, explicitly not
  authorized this iteration; (c) the live-arm blocker is missing from the dev handoff rather than
  explicitly named; (d) the true-start/true-end DB fingerprints differ in any field, or true-start itself
  does not match the independently-captured baseline; (e) AVB's corrected volume figures are described
  anywhere as erroneous or pending further correction — the iteration-16 correction is the repair, not a
  new defect, and this iteration did not touch it again.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-J-01 | Sector attribution stays honest & near-complete | regression | P1 | `/stocks`, `/methodology` |
| UT-J-04 | Candidate why/why-not explanations stay complete | regression | P1 | `/` |
| UT-J-10 | Raw price recovery doesn't destabilize normal serving | regression | P1 | `/stocks`, stock detail |
| UT-J-11 | Maintenance-boundary lifecycle hardened in code; live app provably untouched | regression | P1 | `/`, AVB stock detail, `/data`, evidence artifacts |

**All 4 test cases are P1**, per the ui-test-designer's Backend-only phase handling rule: every journey
named on the phase spec's `Target journeys:` line (J-11) or `Required-still-passing journeys:` line
(J-01, J-04, J-10) gets exactly one `UT-J-<id>` regression row. This phase spec names only these 4
journeys (verified directly against `docs/phases/goal-market-compass-iter-17.md`'s own metadata lines) —
narrower than iteration 16's plan, whose `Required-still-passing journeys:` line carried an 11-journey
"evaluator awareness" digest; iteration 17's does not. No new-surface (smoke/happy-path/validation/error/
UX) cases exist this iteration: `Frontend Present: no` and the UI surface map records no row to derive
one from.

**None of these 4 cases have been executed.** UT-J-01, UT-J-04, and UT-J-10 carry forward unchanged from
iteration 16's plan — this iteration's diff touches none of `apps/backend/app/api/*`, `scoring.py`,
`sectors.py`, or `compass.py`, so none of their served values could have moved. UT-J-11 is substantially
rewritten to reflect this iteration's actual work: the AG-8 bounded-query fix, the new arm/disarm
entrypoints (fixture-proven only), the 9 owner-named tests, the corrected `AVB-A` Stage D classification,
and the exact dev-handoff status lines — all provable **today**, via steps 5-7 (evidence-artifact reads),
without waiting for maintenance isolation to lift; steps 1-4 (browser) must wait for a future boot.
