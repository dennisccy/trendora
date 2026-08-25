# Phase goal-market-compass-iter-14 — UI Test Plan

**Phase:** goal-market-compass-iter-14
**Date:** 2026-08-24
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Status

**Frontend Present: no.** This iteration is a non-destructive, read-only J-11 Stage D readiness
hardening pass — a fresh Stage D attempt identity, three fail-closed identity-comparison checks
(built and fixture-tested, not run live), added negative/precondition tests, a read-only AVB bridge
diagnostic, and an explicit `J-11 STAGE D READY` verdict — with **zero frontend files touched** and
**zero live database writes**. Maintenance isolation is ACTIVE this iteration: no application-service
boot, no browser automation, no deterministic-replay lane. Per the ui-test-designer's backend-only
handling, **no NEW-surface test cases are generated** — there is no UI surface map row this iteration
to derive one from (`reports/phase-goal-market-compass-iter-14-ui-surface-map.md` reads "Not mapped
this iteration").

Per the phase spec's own `Required-still-passing journeys:` metadata line (names J-01 through J-10,
carried unchanged "for evaluator awareness only" while maintenance isolation keeps the browser-QA and
deterministic-replay lanes shut) **and** its `Target journeys:` metadata line (names J-11, this
iteration's own scoped work), this plan still carries one regression test case per named journey —
**UT-J-01 through UT-J-11** — so none of the eleven ships this iteration on record with zero test
coverage. Each case is translated from that journey's own "Steps"/"Acceptance" text in `docs/goal.md`'s
"Must-have user journeys" section (read directly, lines 203–1611).

**None of these test cases have been executed this iteration.** They are written for an operator, or a
later Stage-G-permitted run, to execute once maintenance isolation lifts. Do not read any step below as
already performed or passed.

Three journeys — **J-09, J-10, J-11** — are explicitly `Walkthrough: waived` in `docs/goal.md`: they
have no UI surface of their own (J-09 is a backend memory-tuning journey; J-10 and J-11 are raw/derived
data-repair journeys). Their test cases below are read-only file/config/data checks (exact file paths,
exact JSON field names, exact expected values) rather than browser click-paths, per the "exact and
specific, never vague" rule applied to the medium that actually exists for each journey. The remaining
eight (J-01–J-08) do have UI surfaces and are written in exact-URL/click/expected format.

**Known mid-repair state — not a regression, do not test as a bug.** The 11 incident dates
(`2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03, 2026-08-05,
2026-08-10, 2026-08-11, 2026-08-12`) currently hold **zero** `scanner_runs` and zero derived children —
J-11 Stage C cleared them and Stage D has not yet regenerated them (Stage D is not authorized this
iteration). The newest surviving stored run is **2026-07-23**, so "Latest" currently resolves there, and
any surface asked for one of the 11 incident dates hits an honest missing-run path. This is the
authorized mid-repair state, re-derive it live at execution time rather than trusting this line — do
not write or read a test case that treats it as broken. Steps below that need a historical as-of
deliberately avoid the 11 incident dates for this reason.

---

## Test Cases

<!-- Test IDs use UT-J-XX for the journey-regression cases this backend-only iteration requires.
     Each test MUST have exact steps and specific expected results — no vague "verify it works". -->

---

### UT-J-01 — Sector attribution stays honest and near-complete (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`, `/methodology`, `GET /api/stocks`

**Preconditions:**
- Backend and frontend running via the project's prod launch scripts (only after maintenance isolation
  lifts — not this iteration)
- At least one stored run exists at the current Latest as-of (2026-07-23 as of this writing; re-check
  `GET /api/runs` at execution time, it may have advanced)

**Steps:**
1. Navigate to `http://localhost:3255/stocks` with no `?asof` parameter (Latest as-of).
2. Open the "Sector" filter control and select "Unassigned".
3. Read the filtered row count and the total resolved-member count shown on the page; compute the
   Unassigned share.
4. Pick one ticker known to be mapped via `config.stock_sectors` and one pool name not in that config;
   note the Sector cell text shown for each in the `/stocks` leaderboard row.
5. Click each ticker's symbol link to open its stock detail page; note the Sector value shown in the
   detail header.
6. Open `http://localhost:3255/methodology` and locate the universe/data section.

**Expected Result:**
- The Unassigned share computed in step 3 is at most 5% of resolved members.
- The Sector cell text noted in step 4 and the detail-header Sector value noted in step 5 are identical
  for each of the two spot-checked tickers, and both equal the `sector` field `GET /api/stocks` serves
  for the same ticker and as-of.
- `/methodology`'s universe/data section discloses the two-source sector basis (curated
  `config.stock_sectors` first, pool snapshot fallback second) and states its current-only limitation
  (no point-in-time sector history).
- A symbol present in neither map serves `sector: null` from the API and renders as "Unassigned" on
  `/stocks` — never a fabricated sector label.

---

### UT-J-02 — "What changed" reports honest session-over-session deltas (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend and frontend running via prod scripts (post-isolation)
- At least two stored runs exist so a prior-session comparison is possible

**Steps:**
1. Navigate to `http://localhost:3255/` at Latest as-of.
2. Read the "What changed" card's header text — it should name a specific prior stored session date
   and the gap in days.
3. Call `GET http://localhost:3255/api/runs` and confirm the date named in step 2 equals the run
   immediately preceding the current Latest as-of in the returned list.
4. Click the drill-through link on one visible change entry.
5. Click the suppressed-moves disclosure control (e.g. "Show suppressed moves").

**Expected Result:**
- The header's prior date and gap match the API's adjacent-run relationship from step 3 exactly.
- Change entries are ordered market → breadth → sectors → themes → stocks, and each meets its kind's
  `compass.delta.*` threshold.
- Clicking the drill-through link in step 4 navigates to that surface with the current `?asof` value
  carried in the URL.
- The suppressed-moves disclosure in step 5 shows a count that equals the number of listed suppressed
  entries beneath it.

---

### UT-J-03 — Plain-English summary is deterministic and cited (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend and frontend running via prod scripts (post-isolation)

**Steps:**
1. Navigate to `http://localhost:3255/` at Latest as-of.
2. Read the summary card; it should show a state sentence plus direction, breadth, and focus-count
   sentences.
3. Click "Show cited facts" (or equivalent disclosure control).
4. Compare one displayed fact value against `GET http://localhost:3255/api/dashboard`'s regime score
   field for the same as-of, and a second fact against `GET http://localhost:3255/api/market-phase`'s
   severity field for the same as-of.
5. Read every rendered sentence for banned-language tokens (imperative trade verbs, forecast terms,
   causal-attribution phrases).

**Expected Result:**
- Each sentence in step 3's disclosure lists a template id and the facts backing it.
- The two spot-checked facts in step 4 are byte-identical to the canonical endpoint values.
- No sentence on the page contains a token from the committed banned-language list.
- (If Latest happens to be the earliest stored run) the no-comparison sentence variant renders instead
  of a fabricated delta.

---

### UT-J-04 — Every candidate explains why, why-not, and what would change it (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend and frontend running via prod scripts (post-isolation)
- At least one candidate exists at Latest as-of (if `candidates_empty_reason` renders instead, treat
  that as the honest-zero state, not a failure — see Expected Result)

**Steps:**
1. Navigate to `http://localhost:3255/` at Latest as-of.
2. Read the "Next-session focus" section's candidate count.
3. Call `GET http://localhost:3255/api/compass` for the same as-of and read its candidate count, plus
   the summary card's focus-count sentence.
4. Click one candidate card to expand it; read its Leadership/Entry/Risk words, reasons, cautions, and
   the "what would change this" panel.
5. Compare the expanded card's buckets/scores against `GET http://localhost:3255/api/stocks`'s row for
   the same ticker and as-of.
6. Scroll to the "Not priority" section and read two entries' stated failed condition(s).

**Expected Result:**
- The candidate counts from steps 2 and 3 (page, API, summary sentence) all agree, OR, if zero
  candidates clear the selection floor, the section renders the explicit `candidates_empty_reason`
  state — never a bare empty list.
- The expanded card's Leadership/Entry/Risk words are the config word-map values for the buckets shown,
  and its buckets/scores in step 4 equal the `GET /api/stocks` row values from step 5 exactly.
- Every reason/caution cites a threshold and the stored actual value (e.g. the ATR caution cites
  `risk_budget.atr_pct` and its percentile).
- Each "Not priority" entry in step 6 names its failed condition(s) with distances; the near-threshold
  shadow cohort never appears as a card or pick in the focus section.

---

### UT-J-05 — Each close freezes one provenance-stamped manifest (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `GET /api/compass`

**Preconditions:**
- Backend and frontend running via prod scripts (post-isolation)
- The Latest as-of already has a frozen `at_ingest` manifest (i.e. do not trigger a new ingest/backfill
  for this check — verify the existing frozen state only)

**Steps:**
1. Call `GET http://localhost:3255/api/compass` for the Latest frontier as-of.
2. Read the response's manifest fields: `mode`, `version`, `frozen`, `prospective_eligible`,
   `generation.producer`, the generation timestamp, `available_at_utc`, the engine identity,
   `candidate_rule_hash`, `cohort_rule_hash`, `manifest_config_hash`, `content_hash`, `manifest_hash`.
3. Navigate to `http://localhost:3255/` and locate the manifest strip.
4. Expand the manifest strip's table.

**Expected Result:**
- `mode` is `at_ingest`, `version` is a positive integer, `frozen` is `true`, `prospective_eligible` is
  a boolean derived from the recorded facts (never a placeholder), `available_at_utc` is a well-formed
  timestamp not earlier than the generation timestamp plus the configured margin.
- The manifest strip on `/` shows the same version/frozen/stamp values read in step 2 — no discrepancy
  between the API payload and the rendered strip.
- The expanded table's comparison-cohort row count equals the resolved member count minus the candidate
  count for the same as-of, and the near-threshold shadow cohort carries an explicit research-only
  label.

---

### UT-J-06 — A frozen manifest never changes (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `GET /api/compass`

**Preconditions:**
- Backend and frontend running via prod scripts (post-isolation)
- A stored historical as-of exists that is NOT one of the 11 incident dates and is earlier than the
  current Latest — confirm via `GET /api/runs` before starting

**Steps:**
1. Call `GET http://localhost:3255/api/compass` for the Latest frontier as-of; record `version`,
   `content_hash`, and `manifest_hash`.
2. Navigate to `http://localhost:3255/` and confirm the manifest strip shows the same version/stamps
   recorded in step 1.
3. Use the as-of switcher on `/` to step to the historical date confirmed in Preconditions (call it D);
   confirm the manifest strip now shows D's own manifest with a visible `retrospective` label if D
   predates the feature, and never the frontier's contents.
4. Return to Latest (clear `?asof`); call `GET /api/compass` again for the frontier as-of.

**Expected Result:**
- The `version`, `content_hash`, and `manifest_hash` values from step 4 are byte-identical to those
  recorded in step 1 — visiting a historical date and returning must not mutate or regenerate the
  frontier manifest.
- Step 3's strip never substitutes the frontier manifest's contents for D's — the as-of shown in the
  strip always equals the URL's `?asof` value.

---

### UT-J-07 — The Today page answers the ten-second read from served values only (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend and frontend running via prod scripts (post-isolation)
- Note: J-11's status is `failing` in `runs/goal-session-market-compass/state/journey-history.json` as
  of this writing — this test case exists to re-verify (and re-diagnose) that status at execution time,
  not to assert in advance that it will pass or fail.

**Steps:**
1. Navigate to `http://localhost:3255/`.
2. Read the page body top to bottom.
3. Compare the regime tile's label/score against `GET http://localhost:3255/api/dashboard` for the same
   as-of, and the phase tile's phase/severity/P(bear) against
   `GET http://localhost:3255/api/market-phase` for the same as-of.
4. Look for a regime × phase cross-view chart on `/`; then click the named link-out to `/market`.
5. Scan the readiness badge / preflight strip in the page chrome and the market-state band in the body
   for vocabulary overlap.

**Expected Result:**
- The body renders, in order: market-state band, plain-English summary, What changed, Leadership
  rotation, Next-session focus, manifest strip — with the readiness badge and preflight strip in the
  chrome above the body, not inside it.
- The regime and phase tile values from step 3 are value-identical to the two canonical endpoints for
  the same as-of.
- The regime × phase cross-view chart is absent from `/` itself and renders only after navigating to
  `/market` in step 4.
- Readiness/preflight tokens ("Ready", "GO", "DEGRADED", "NO-GO") appear only in the chrome elements
  scanned in step 5; regime/phase tokens appear nowhere inside the chrome.

---

### UT-J-08 — The market surface relocates intact and history never lies (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/market`, `/`

**Preconditions:**
- Backend and frontend running via prod scripts (post-isolation)
- A stored historical as-of D confirmed via `GET /api/runs` that is NOT one of the 11 incident dates
  (`2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27, 2026-08-03, 2026-08-05,
  2026-08-10, 2026-08-11, 2026-08-12`) and earlier than the current Latest
- Note: J-11's status is `failing` in journey-history.json as of this writing — this case re-verifies
  that status, it does not assume the outcome.

**Steps:**
1. Navigate to `http://localhost:3255/market`.
2. Read the page contents: the two glance cards, the regime × phase cross-view card, and the full
   former More-detail inventory (three breadth cards, Top Sectors, Candidate Counts, Top Themes, the
   full Market Phase & Severity card).
3. Look at the sidebar; confirm the order and route-active highlighting for "Today" and "Market" links.
4. On `/`, set `?asof=D` (the historical date from Preconditions) via the as-of switcher.
5. Open `http://localhost:3255/?asof=D` directly in a fresh browser tab.
6. Click "Latest" (or clear the as-of parameter) to return to the current frontier state.

**Expected Result:**
- `/market` renders every card listed in step 2 — none dropped — each reading the same endpoints as
  before the relocation.
- The sidebar lists "Today" (`/`) first and "Market" (`/market`) second; each link is highlighted active
  only on its own page.
- Step 4's Today tiles show D's stored values, "What changed" compares D against D's predecessor (header
  names that date), and the manifest strip shows a manifest whose as-of equals D with a visible
  `retrospective` label.
- Step 5's fresh tab renders D-scoped data immediately — no visible flash of Latest data before D loads
  — and sidebar links carry `?asof=D`.
- Step 6 removes the `?asof` parameter and the strip returns to the Latest session's state.

---

### UT-J-09 — The backend fits the host: standing memory halves with zero behavior change (regression)

**Type:** regression
**Priority:** P1
**Surface:** Backend only — `Walkthrough: waived` in `docs/goal.md` (no UI surface)

**Preconditions:**
- Read access to `apps/backend/config.yaml` and `reports/perf-budgets.md`
- Ability to start the backend via `bash scripts/start-backend.sh` (post-isolation only)

**Steps:**
1. Open `apps/backend/config.yaml` and read `database.pragmas.cache_size` under the `database:` block,
   plus `pool_size` and `max_overflow` in the same block.
2. Start the backend via `bash scripts/start-backend.sh`; after the standing-warm connection pool
   warm-up completes, read `VmPeak` from `/proc/<backend-pid>/status`.
3. Open `reports/perf-budgets.md` and locate the standing-warm VmPeak measurement history.
4. Run a request burst at `server.limit_concurrency` against the running backend.

**Expected Result:**
- `database.pragmas.cache_size` reads `-65536` (64 MB per connection) — not the earlier `-262144`
  (256 MB) — while `pool_size` (`24`) and `max_overflow` (`44`) remain unchanged.
- Step 2's measured `VmPeak` is ≤ 2.5 GB (2,621,440 kB) — the original measurement this journey exists
  to fix was 4,837,420 kB.
- `reports/perf-budgets.md` shows the new dated measurement appended beside the original figure, never
  overwriting it.
- Step 4's concurrent-load burst completes with zero `QueuePool` `TimeoutError`s.

---

### UT-J-10 — Bounded recovery of the two incident trading days stays closed and unregressed (regression)

**Type:** regression
**Priority:** P1
**Surface:** Backend only — `Walkthrough: waived` in `docs/goal.md` (no UI surface); read-only data
checks against `apps/backend/data/trendora.db`

**Preconditions:**
- Read-only DB access (never a write, never a copy of the 7.8+ GB file)
- J-10 is currently `passing` / `CLOSED` per `docs/goal.md`'s "J-10 CLOSED — residual set accepted
  (owner, 2026-08-23)" ruling: 585 of the 587-symbol authorized recovery population restored, EA and
  EQR explicitly accepted as unrestorable

**Steps:**
1. Query `daily_prices` coverage for 2026-08-11 and 2026-08-12 across the 587-symbol authorized recovery
   population.
2. Confirm which symbols, if any, lack rows for either date.
3. Query `data_provider_runs` for rows dated after the committed seed's 2026-07-01 boundary.
4. Confirm no `daily_prices` row dated 2026-08-13 or later was touched as part of the recovery, and
   that surviving rows for dates other than 2026-08-11/2026-08-12 are byte-unchanged.

**Expected Result:**
- Step 2 finds exactly two missing symbols, **EA** and **EQR**, and no others — matching the accepted
  residual set; a different missing-symbol set is a regression (J-10 was reopened or a restored row was
  lost).
- Step 3's post-seed rows are all `provider='yahoo'` (34+ runs), and the single `stooq` run (id 541)
  still shows 0 symbols restored — unchanged historical fact, never rewritten.
- Step 4 confirms the frontier is unchanged at 2026-08-12 and no surviving row was overwritten.

---

### UT-J-11 — Stage D readiness hardening: this iteration's own evidence is internally consistent (regression)

**Type:** regression
**Priority:** P1
**Surface:** Backend only — `Walkthrough: waived` in `docs/goal.md` (no UI surface); read-only file/JSON
checks, no app boot required — **this test case is currently executable without violating maintenance
isolation**

**Preconditions:**
- Read access to `runs/goal-market-compass-iter-14/` and `docs/handoffs/goal-market-compass-iter-14-dev.md`
- None of these files are modified by this check — read-only

**Steps:**
1. Open `runs/goal-market-compass-iter-14/j11-stage-d-attempt-identity.json`.
2. Open `runs/goal-market-compass-iter-14/j11-stage-d-preflight-gate.json`.
3. Open `runs/goal-market-compass-iter-14/j11-avb-bridge-diagnostic.json`.
4. Open `runs/goal-market-compass-iter-14/j11-stage-d-readiness.json`.
5. Open `docs/handoffs/goal-market-compass-iter-14-dev.md` and search for `STAGE D READY`.
6. Compare `runs/goal-market-compass-iter-14/j11-stage-d-db-file-true-start.json` against
   `runs/goal-market-compass-iter-14/j11-stage-d-db-file-true-end.json`.
7. Run `apps/backend/tests/test_j11_stage_d.py` and `apps/backend/tests/test_j11_avb_diagnostic.py` as
   the only pytest process active on the host (never alongside another pytest run).

**Expected Result:**
- Step 1: `engine_identity` reads `53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55` —
  the freshly recomputed value, never the earlier `6261ca17…` attempt's identity — and `attempt_id`
  begins with `j11-stage-d-`.
- Step 2: `verdict.passed` is `true`, `comparison.material_mismatch` is `false`, and every one of the 11
  incident dates under `comparison.per_date_scanner_run_present` reads `false` (zero `ScannerRun` rows).
- Step 3: `classification.classification` is `AVB-B` and `classification.stage_d_ready_per_avb` is
  `true`.
- Step 4: `ready` is `true` and `authorized` is `false`.
- Step 5: both literal lines `**J-11 STAGE D READY: YES**` and `**J-11 STAGE D AUTHORIZED: NO**` are
  present verbatim in the dev handoff, consistent with step 4's artifact.
- Step 6: `mtime` and `size_bytes` are identical between the true-start and true-end files, and
  `wal.size_bytes` reads `0` in both — proving zero live writes to `trendora.db` across the whole
  iteration.
- Step 7: both test files pass on fixture-only `sqlite://` databases (never the live DB).
- **A `YES` readiness verdict here does NOT authorize Stage D itself** — `J-11 STAGE D AUTHORIZED: NO`
  must remain present regardless of the READY value; a missing or flipped `AUTHORIZED` line, or a Stage
  D regeneration having actually run, is a critical regression.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-J-01 | Sector attribution honest & near-complete | regression | P1 | `/stocks`, `/methodology` |
| UT-J-02 | "What changed" honest deltas | regression | P1 | `/` |
| UT-J-03 | Plain-English summary deterministic & cited | regression | P1 | `/` |
| UT-J-04 | Candidate why/why-not/what-would-change | regression | P1 | `/` |
| UT-J-05 | Manifest freezes at close | regression | P1 | `/`, `GET /api/compass` |
| UT-J-06 | Frozen manifest never changes | regression | P1 | `/`, `GET /api/compass` |
| UT-J-07 | Today page ten-second read | regression | P1 | `/` |
| UT-J-08 | Market surface relocated intact | regression | P1 | `/market`, `/` |
| UT-J-09 | Backend memory ceiling holds | regression | P1 | backend only (waived) |
| UT-J-10 | Bounded recovery stays closed | regression | P1 | backend only (waived) |
| UT-J-11 | Stage D readiness evidence consistent | regression | P1 | backend only (waived) — executable now |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-J-01 through UT-J-10 require the
application to be started, which is forbidden under this iteration's maintenance isolation — they are
deferred to the first iteration permitted to boot the app. **UT-J-11 requires no app boot** and can be
executed immediately as a read-only file/JSON check.
