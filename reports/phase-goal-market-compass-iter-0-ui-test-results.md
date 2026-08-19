# Goal Iteration goal-market-compass-iter-0 — UI Test Results

**Phase:** goal-market-compass-iter-0
**Date:** 2026-08-19
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- This is iteration 0 of the market-compass goal session: a verify-only BASELINE pass with
     ZERO code changes (per docs/phases/goal-market-compass-iter-0.md). All 8 Must-have journeys
     (J-01..J-08) test a "Today compass" / next-session-manifest feature set that does not exist
     in the codebase yet — confirmed independently via openapi.json route listing, sidebar DOM,
     and full-page-text regex sweeps before any journey was scored. A FAIL verdict here is the
     HONEST and EXPECTED baseline finding, not a defect introduced this iteration. Per the iter
     spec: "no journey is skipped even though most are expected to be unimplemented (baseline
     must record the honest current state either way)." Zero golden replay scripts were written
     this run (none of the 8 journeys passed) — see Notes. -->

**Overall:** 0/8 tests passed (8 failed, 0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | J-01: Sector attribution is honest and near-complete on new runs | journey (baseline) | P1 | After remap+backfill, `/stocks` Unassigned share ≤5% of resolved members; spot-checked labels match across leaderboard/detail/API; `/methodology` discloses the two-source sector basis + current-only limitation; unmapped symbols honestly serve `sector: null`/"Unassigned" | No remap/backfill was run (zero code changes this iteration; sector wiring does not exist yet). Measured current state directly: `/stocks` Sector filter → "Unassigned" returns exactly 424 rows (live DOM `table tbody tr` count), matching `GET /api/stocks?asof=2026-08-14` = 424/541 null = 78.4% — far above the 5% target. Spot-check DELL (config.stock_sectors-mapped): "Technology" identical on leaderboard cell, stock-detail header badge, and API row. Spot-check GRMN (unmapped pool name): "Unassigned"/null identical on all three surfaces — single-source consistency already holds and unknowns render honestly (no fabrication). `/methodology` full-page text has zero matches for a two-source/curated/pool-fallback/current-only sector disclosure. | FAIL | `reports/qa/goal-market-compass-iter-0-evidence/UT-J-01-result.png` |
| UT-J-02 | J-02: "What changed" reports meaningful session-over-session deltas with honest empties | journey (baseline) | P1 | `/` shows a "What changed" card naming the prior stored session + gap, ordered market→breadth→sectors→themes→stocks, with a suppressed-moves disclosure and an explicit no-prior-run empty state at the earliest run | `/` renders the legacy "Dashboard" (heading literally "Dashboard") — regime/top-themes glance card, breadth stats, top sectors, candidate counts, market-phase & severity card, causal downtrend episode list, retrospective P(bear) filter. Full-page-text regex `/what changed/i` = false. No delta/session-comparison UI of any kind exists. | FAIL | `reports/qa/goal-market-compass-iter-0-evidence/UT-J-02-fail.png` |
| UT-J-03 | J-03: The plain-English summary is deterministic, cited, and never invents a cause | journey (baseline) | P1 | `/` shows a summary card (state/direction/breadth/focus-count sentences) plus a "Show cited facts" disclosure; goldens reproduce; banned-language list is clean; NA/no-comparison variants render; retrospective stamp on historical dates | No summary card and no "cited facts" disclosure anywhere on `/` — full-page-text regex `/cited facts/i` = false. Only pre-existing market-phase reason strings ("No recovery turn at this date", "No fresh downtrend exit…") are present, which are the existing (pre-compass) market-phase feature, not new compass narrative sentences. | FAIL | `reports/qa/goal-market-compass-iter-0-evidence/UT-J-03-fail.png` |
| UT-J-04 | J-04: Every next-session candidate explains why, why-not, and what would change it | journey (baseline) | P1 | `/` shows a "Next-session focus" section with candidate cards (reasons/cautions/checklist/what-would-change), Risk-off caution propagation, and an honest-zero `candidates_empty_reason` state | No "Next-session focus" section anywhere on `/` — full-page-text regex `/next-session focus/i` = false. No candidate cards, no eligibility checklist, no why-not list, no shadow-cohort concept exists on the page. | FAIL | `reports/qa/goal-market-compass-iter-0-evidence/UT-J-04-fail.png` |
| UT-J-05 | J-05: Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | journey (baseline) | P1 | `GET /api/compass` serves a frozen `mode: at_ingest`, `version: 1` manifest with full provenance/hash/cohort blocks; export file bytes match; ingest finalize discloses a "next-session manifest" phase; create-once + retrospective-on-GET semantics hold | `GET /api/compass?asof=2026-08-14` → **HTTP 404** `{"detail":"Not Found"}`, byte-identical on two consecutive requests. `/api/compass` is entirely absent from the backend's own `openapi.json` path listing (cross-checked against `/api/dashboard`, `/api/market-phase`, `/api/runs`, `/api/sectors`, `/api/stocks`, `/api/themes`, `/api/regime-history`, all of which exist). `/data`'s job-history "Refreshed:" lines (30+ recent jobs inspected live) list only pre-existing aggregate phases (availability heatmap, coverage, membership timeline, market phase, forward aggregates, index series, research hot keys, factor lab all, drawdown expectations, latest snapshot) — never "next-session manifest". No manifest producer exists in the running backend. | FAIL | `reports/qa/goal-market-compass-iter-0-evidence/UT-J-05-fail.png` |
| UT-J-06 | J-06: A frozen manifest never changes — later data, rebuilds, and regeneration are safe | journey (baseline, blocked by J-05) | P1 | Stored manifest survives further backfill/removal/rebuild verbatim; explicit regenerate mints version 2 with independent stamps; version 1 remains byte-identical | Cannot be exercised — there is no manifest to test immutability of (J-05 confirms the producer, table, and endpoint are entirely absent). `/scanner-runs` page text was also checked live and contains zero mentions of "manifest" or "engine_identity". Recorded FAIL with blocking reason per the iter-0 spec's explicit instruction to record this journey "as far as J-05's baseline result permits." | FAIL | `reports/qa/goal-market-compass-iter-0-evidence/UT-J-06-fail.png` |
| UT-J-07 | J-07: The Today page answers the ten-second read from served values only | journey (baseline) | P1 | `/` renders, top to bottom: market-state band, plain-English summary, What changed, Leadership rotation, Next-session focus, manifest strip (readiness/preflight chrome above the body); regime/phase tiles echo canonical endpoints; vocabulary separation; cross-view chart absent from `/`; perf budgets met | `/` (heading "Dashboard") currently renders: readiness badge + "GO — today's board is current" preflight strip (chrome, correctly kept separate from market vocabulary — no AG-13 collision observed), then the regime/top-themes glance card, breadth stats, top sectors, candidate-counts-by-setup, top themes, then the full "Market Phase & Severity" card **including the regime×phase cross-view chart** (still on `/` since `/market` does not exist yet — see J-08), a causal downtrend episode list, and the retrospective P(bear) filter panel. Combined full-page-text regex sweep for all six required compass sections (what changed / cited facts / next-session focus / manifest / leadership rotation / compass) returned false for every one. | FAIL | `reports/qa/goal-market-compass-iter-0-evidence/UT-J-07-fail.png` |
| UT-J-08 | J-08: The market surface relocates intact and history never lies | journey (baseline) | P1 | `/market` renders the complete relocated dashboard body; sidebar lists Today then Market; `?asof=D` scoping with retrospective manifest labeling on both pages; fresh-tab no-repaint; Latest reset | `GET /market` (frontend route) → Next.js **"404: This page could not be found."** (live nav + DOM heading "404"). Sidebar's actual current order, read live from the DOM across every page visited this run: Dashboard (`/`), Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Evidence, Watchlist, Methodology, Data Manager — first entry is "Dashboard" → `/`, not "Today"; no second "Market" entry exists anywhere in the sidebar. | FAIL | `reports/qa/goal-market-compass-iter-0-evidence/UT-J-08-fail.png` |

---

## Failed Tests

### UT-J-01 — Sector attribution is honest and near-complete on new runs
**Verdict:** FAIL
**Failure:** Unassigned share of resolved members is 78.4% (424/541) at the latest as-of (2026-08-14), far above the ≤5% Acceptance target. The `universe.pool_sector_aliases` fallback wiring described in the journey does not exist yet — `config.stock_sectors` is the only source consulted, matching goal.md's own recorded Ground Truth (measured 2026-08-19 @ 42167cf5).
**Evidence:** `reports/qa/goal-market-compass-iter-0-evidence/UT-J-01-result.png`

**Steps taken:**
1. Skipped the seed-safe Remove+backfill step (out of scope — zero code changes this iteration, and the underlying wiring the backfill would exercise does not exist yet).
2. Navigated to `/stocks`, opened the "Filter by sector" select (`aria-label="Filter by sector"`), selected "Unassigned".
3. Counted `document.querySelectorAll('table tbody tr').length` = 424.
4. Cross-checked `GET /api/stocks?asof=2026-08-14`: 541 rows total, 424 with `sector: null` = 78.4%.
5. Opened `/stocks/DELL` (mapped via `config.stock_sectors`) — header badge shows "Technology", matching the leaderboard cell and the API row.
6. Opened `/stocks/GRMN` (unmapped pool name) — header badge shows "Unassigned", matching the leaderboard cell and `sector: null` in the API.
7. Opened `/methodology`, read the full extracted page text (593 lines) — no mention of a two-source (curated-config + pool-fallback) sector basis or a current-only/point-in-time limitation disclosure.

**Expected:** ≤5% Unassigned share; methodology discloses the two-source basis.
**Actual:** 78.4% Unassigned; no methodology disclosure exists. (Single-source consistency and honest-NULL rendering already hold structurally — only the coverage wiring and the disclosure are missing.)

---

### UT-J-02 — "What changed" reports meaningful session-over-session deltas with honest empties
**Verdict:** FAIL
**Failure:** No "What changed" card, delta list, or session-comparison UI exists on `/` in any form.
**Evidence:** `reports/qa/goal-market-compass-iter-0-evidence/UT-J-02-fail.png`

**Steps taken:**
1. Navigated to `/` at the latest as-of (default "Latest" selector, 2026-08-14).
2. Read the full rendered page text.
3. Ran a case-insensitive regex check for `"what changed"` over `document.body.innerText` → `false`.

**Expected:** A "What changed" card naming the prior stored session date and the gap in days, entries ordered market→breadth→sectors→themes→stocks, a suppressed-moves disclosure, and an explicit no-prior-run state at the earliest run.
**Actual:** Section does not exist; `/` is the pre-existing legacy dashboard.

---

### UT-J-03 — The plain-English summary is deterministic, cited, and never invents a cause
**Verdict:** FAIL
**Failure:** No summary card and no "Show cited facts" disclosure exist on `/`.
**Evidence:** `reports/qa/goal-market-compass-iter-0-evidence/UT-J-03-fail.png`

**Steps taken:**
1. On the same `/` load as UT-J-02, ran a case-insensitive regex check for `"cited facts"` over the full page text → `false`.
2. Manually scanned the extracted markdown (92 lines) for any narrative/state sentence resembling a compass summary — only found the pre-existing market-phase reason strings ("No recovery turn at this date", "No fresh downtrend exit: P(bear) 0.00…"), which are part of the current Market Phase card, not the new compass feature.

**Expected:** A summary card with state/direction/breadth/focus-count sentences plus a cited-facts disclosure.
**Actual:** Neither exists.

---

### UT-J-04 — Every next-session candidate explains why, why-not, and what would change it
**Verdict:** FAIL
**Failure:** No "Next-session focus" section, candidate cards, eligibility checklist, or why-not list exist anywhere on `/`.
**Evidence:** `reports/qa/goal-market-compass-iter-0-evidence/UT-J-04-fail.png`

**Steps taken:**
1. On the same `/` load, ran a case-insensitive regex check for `"next-session focus"` over the full page text → `false`.
2. Confirmed no candidate-card, checklist, or shadow-cohort markup exists via the same full-text scan.

**Expected:** A "Next-session focus" section whose candidate count matches `GET /api/compass` and the summary sentence, each card with Leadership/Entry/Risk words, reasons/cautions with thresholds, an eligibility checklist, a "what would change this" panel, and a "Not priority" why-not list.
**Actual:** Section does not exist (downstream of J-05: there is no `GET /api/compass` to source it from).

---

### UT-J-05 — Each close freezes one provenance-stamped next-session manifest, exported byte-consistently
**Verdict:** FAIL
**Failure:** `GET /api/compass` returns HTTP 404 — the route, the manifest producer, and the `next_session_manifests` table do not exist in the running backend.
**Evidence:** `reports/qa/goal-market-compass-iter-0-evidence/UT-J-05-fail.png`

**Steps taken:**
1. `curl -i http://localhost:8255/api/compass?asof=2026-08-14` → `HTTP/1.1 404 Not Found`, body `{"detail":"Not Found"}`.
2. Repeated the identical request — byte-identical 404 response both times (satisfies the "either both succeed identically or both fail identically" baseline check).
3. Fetched `http://localhost:8255/openapi.json` and listed every path containing `compass|stocks|runs|market-phase|dashboard|sectors|themes|regime-history` — `/api/compass` is absent; `/api/dashboard`, `/api/market-phase`, `/api/regime-history`, `/api/runs`, `/api/runs/{run_id}`, `/api/sectors`, `/api/stocks`, `/api/stocks/{ticker}`, `/api/stocks/{ticker}/bars`, `/api/themes` are all present.
4. Navigated to `/data`, waited for the job-history list, and grepped 30+ "Refreshed:" lines for "manifest" — zero matches; the existing refreshed-phase vocabulary (availability heatmap, coverage, membership timeline, market phase, forward aggregates, index series, research hot keys, factor lab all, drawdown expectations, latest snapshot) contains nothing new.

**Expected:** A frozen `at_ingest` v1 manifest with `prospective_eligible`, dual hashes, split rule identities, three cohorts, and a byte-matching export.
**Actual:** No such endpoint, table, or producer exists.

---

### UT-J-06 — A frozen manifest never changes — later data, rebuilds, and regeneration are safe
**Verdict:** FAIL
**Failure:** Blocked entirely by J-05 — there is no manifest to test immutability of.
**Evidence:** `reports/qa/goal-market-compass-iter-0-evidence/UT-J-06-fail.png`

**Steps taken:**
1. Confirmed via UT-J-05 that the manifest producer, endpoint, and table are all absent.
2. Navigated to `/scanner-runs` and grepped the full page text for "manifest" and "engine_identity" — zero matches.
3. Per the iter-0 spec's explicit baseline-mode instruction ("record the verdict and the blocking reason if the manifest producer does not yet exist"), recorded this as a blocked FAIL rather than attempting the backfill/removal/regenerate sequence against a non-existent feature.

**Expected:** Version 1 survives further ingest/removal/rebuild verbatim; regenerate mints an independently-stamped version 2.
**Actual:** Not exercisable this iteration.

---

### UT-J-07 — The Today page answers the ten-second read from served values only
**Verdict:** FAIL
**Failure:** None of the six required compass body sections (market-state band, plain-English summary, What changed, Leadership rotation, Next-session focus, manifest strip) exist on `/`; the regime×phase cross-view chart is still on `/` rather than relocated.
**Evidence:** `reports/qa/goal-market-compass-iter-0-evidence/UT-J-07-fail.png`

**Steps taken:**
1. Loaded `/` and read the rendered section order top to bottom (readiness/preflight chrome → regime & top-themes glance card → breadth stats → top sectors card → candidate-counts-by-setup → top themes card → full Market Phase & Severity card with cross-view chart → causal downtrend episode list → retrospective P(bear) filter).
2. Ran a combined regex sweep over `document.body.innerText` for `what changed`, `cited facts`, `next-session focus`, `manifest`, `leadership rotation`, `compass` — every check returned `false`.
3. Confirmed readiness vocabulary ("Ready", "GO — today's board is current") is confined to the chrome strip above the body and does not appear inside market-state text (no AG-13 collision) — though this currently holds only because no market-state prose exists yet to collide with it.

**Expected:** All six sections present in the specified order; cross-view chart absent from `/`.
**Actual:** Zero of six sections present; cross-view chart still on `/` (this is also consistent with J-08's finding that `/market` does not exist yet to hold it).

---

### UT-J-08 — The market surface relocates intact and history never lies
**Verdict:** FAIL
**Failure:** `/market` does not exist (Next.js 404); the sidebar has no "Today"/"Market" split — it still opens with "Dashboard" → `/`.
**Evidence:** `reports/qa/goal-market-compass-iter-0-evidence/UT-J-08-fail.png`

**Steps taken:**
1. Navigated to `http://localhost:3255/market` — page heading rendered "404", body text "This page could not be found."
2. Read the sidebar DOM (present identically on every page visited this run: `/stocks`, `/stocks/DELL`, `/stocks/GRMN`, `/methodology`, `/`, `/data`, `/scanner-runs`): Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Evidence, Watchlist, Methodology, Data Manager, in that order, first entry `href="/"` labeled "Dashboard".

**Expected:** `/market` renders the full relocated dashboard body; sidebar lists Today (`/`) first, Market (`/market`) second.
**Actual:** `/market` 404s; sidebar is unchanged from the pre-compass ops-hardening state.

---

## Skipped Tests

None — all 8 target journeys (J-01 through J-08) were executed per the goal-mode lean dispatch instruction ("no journey is skipped even though most are expected to be unimplemented").

---

## Notes

- **This is the expected result for a baseline iteration.** `docs/phases/goal-market-compass-iter-0.md` is an explicit verify-only, zero-code-change iteration whose entire purpose is to record the honest pre-implementation state of all 8 Must-have journeys so the goal-evaluator can seed `journey-history.json` accurately before feature work begins in iteration 1+. Every FAIL above reflects a feature that has not been built yet, independently corroborated by: (a) the backend's own `openapi.json` route listing (no `/api/compass`), (b) live DOM sweeps of `/` (no compass sections), (c) the sidebar DOM (no Today/Market split), (d) the `/market` route (404), and (e) the `/stocks`+API sector-coverage numbers (78.4% Unassigned) — all of which match goal.md's own recorded Ground Truth section (measured 2026-08-19 @ `42167cf5`) exactly.
- **No golden replay scripts were written** to `runs/goal-session-market-compass/journey-scripts/` this run — the instruction is to write one only "for every journey you verify PASS," and zero of the 8 journeys passed at this baseline.
- No source files were edited or created by this agent; only `curl`, read-only Chrome MCP navigation/eval/select, and the report/evidence files listed above were produced.
- API cross-checks used the backend directly (`http://localhost:8255`) alongside the frontend (`http://localhost:3255`) to verify AG-3 ("displayed numbers are correct") wherever a comparison was possible.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (headless, pinned profile)
- **Test Date:** 2026-08-19
- **Evidence directory:** `reports/qa/goal-market-compass-iter-0-evidence/`
- **Latest stored run used as "latest as-of":** `run_id` 3051, `asof_date` 2026-08-14, 541 members (matches goal.md Ground Truth)
