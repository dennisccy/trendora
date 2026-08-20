# Phase goal-market-compass-iter-1 — UI Test Results

**Phase:** goal-market-compass-iter-1
**Date:** 2026-08-20
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 7/12 tests passed (2 skipped, 3 failed)

**Why FAIL:** UT-03 (P1, happy-path — the required Remove+Backfill precondition) failed: the
"Backfill snapshots" job (the test plan's specified default Job kind) completed with status
"no new snapshots" instead of "ok", because the two target dates (2026-08-13 / 2026-08-14) turned
out to be entirely user-added bars with no committed-seed fallback beneath them (confirmed:
`seed_latest_date` is 2026-08-12) — removing them left zero bars for a bars-only backfill to work
from. This blocked UT-04 and UT-05 (both P1, SKIPPED) and the session's own target journey J-01
(FAILED — see below). Full root-cause evidence is under UT-03.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Stocks leaderboard loads | smoke | P1 | Heading "Stocks" + subtitle, `541/541` visible-count badge, Sector column header, no error card, no console errors | All present: heading/subtitle confirmed, `541 / 541` badge confirmed, SECTOR column header confirmed, no "Backend unavailable" card, no console errors observed | PASS | `reports/qa/goal-market-compass-iter-1-evidence/UT-01-result.png` |
| UT-02 | Methodology core content loads | smoke | P1 | Heading + subtitle, ≥1 entry card, Glossary section, no error, Universe Selection card absent (expected today) | All present: heading/subtitle, 6 setup/pattern entry cards, "Glossary — 125 terms across 6 categories" section; Universe Selection card correctly absent | PASS | `reports/qa/goal-market-compass-iter-1-evidence/UT-02-result.png` |
| UT-03 | Remove + Backfill precondition | happy-path | P1 | Preview shows bar/symbol count >0, no refused banner; Remove confirms with green line; Backfill job status reaches "ok" with snapshot/forward-return counts >0 | Preview and Remove succeeded exactly as specified (1174 bars / 587 symbols / cascade 18 snapshots + 30439 forward returns — matching the test plan's own live-preview numbers exactly). The subsequent Backfill job (Job kind left on its specified default, "Backfill snapshots") completed with status **"no new snapshots"**, `0/0` symbols, `0` snapshots — **not "ok"** — logged as "2 calendar days · 0 already snapshotted · **2 non-trading**". Root cause (confirmed via direct API + code read): `seed_latest_date` is `2026-08-12`; 2026-08-13/14 bars were entirely user-added (not committed seed), so removing them left zero bars for those dates system-wide — a post-hoc `POST /api/data/remove/preview` over the same range now returns `refused:true, reason:"no removable bars found in this scope"` with all counts 0. `_trading_days()` derives the trading calendar strictly from stored SPY bars (`apps/backend/app/engine/data_manager.py:158-165`), so a bars-only Backfill correctly refuses to fabricate a snapshot for a now-bar-less date. Producing a fresh run would require the "Fetch + backfill" job kind, which issues live HTTP calls to Yahoo Finance (`apps/backend/app/data_providers/yahoo_provider.py`) — outside both the test plan's specified steps and this agent's authority given AG-9 (no live external network calls without an explicit goal.md amendment) | **FAIL** | `reports/qa/goal-market-compass-iter-1-evidence/UT-03-fail.png` |
| UT-04 | Unassigned share ≤5% (TC-1) | happy-path | P1 | Unassigned share ≤5% of resolved members on the fresh run; UI badge count equals direct API count; GRMN resolves to a real sector | Not executable — no fresh run exists (UT-03 did not produce one). A supplementary, non-substitute API/CSV cross-check was run instead (see Skipped Tests section) | SKIP | none |
| UT-05 | Cross-surface consistency (TC-2) | happy-path | P1 | DELL and GRMN render the identical stored sector across leaderboard, detail page, and API on the fresh run | Not executable against a fresh run (UT-03 did not produce one); GRMN's fallback-driven change (Unassigned → Consumer Discretionary) could not be observed live this run | SKIP | none |
| UT-06 | Remove panel required-field guard | validation | P2 | Preview button disabled with only one date filled, and stays disabled with an invalid date; no modal opens | Confirmed exactly: `previewDisabled:true` with only To-date filled; stayed `true` after typing `2026-13-40` into From-date; no dialog opened at either point | PASS | `reports/qa/goal-market-compass-iter-1-evidence/UT-06-result.png` |
| UT-07 | Methodology graceful degradation | error | P2 | No console error referencing `sector_basis`/`universe_selection`; page renders with no visible gap where the card would sit | Confirmed: page renders fully (entries + glossary) with no broken layout gap; direct `GET /api/methodology` check confirms `universe_selection` key is absent entirely (top-level keys: `entries`, `intro`, `glossary`) | PASS | `reports/qa/goal-market-compass-iter-1-evidence/UT-07-result.png` |
| UT-08 | Curated sectors + scores unchanged (TC-4 spot-check) | regression | P1 | DELL's scores/sector unchanged; Setup filter narrows correctly; Sector column sort works with indicator | DELL confirmed Sector "Technology", Leadership B 81.30 / Entry Quality E 37.85 / Risk E 48.77 on the current run (2026-08-11); Setup filter "Avoid" narrowed `539/539` → `473/539` correctly; Sector-header click produced a `data-testid="sort-indicator"` and rows reordered alphabetically (Communication Services → Consumer Discretionary → …). Caveat: the "far fewer rows collapsed into Unassigned" part of this test's expected result could not be confirmed, since it depends on UT-03's fresh run, which did not materialize — this is the same blocked dependency, not a new finding | PASS | `reports/qa/goal-market-compass-iter-1-evidence/UT-08-result.png` |
| UT-09 | Sector filter discoverability | ux | P3 | Dashboard → Stocks in one click; Sector filter visible without scrolling on a standard desktop viewport, next to search | Confirmed at a 1440×900 viewport (resized from the tool's small default to genuinely test "standard desktop"): reached `/stocks` in one click; Sector select (`top:326,bottom:362`) fully within the 900px viewport, same row as the search box | PASS | `reports/qa/goal-market-compass-iter-1-evidence/UT-09-result.png` |
| UT-10 | Sector-basis disclosure content (TC-5) — informational, non-blocking | happy-path (informational) | P3 | Card absent today (expected, pre-existing gate); full disclosure text only once `data/seed/universe.json` exists | Confirmed absent exactly as documented: `document.querySelector('[data-testid="universe-selection"]')` and `[data-testid="universe-sector-basis"]` both `false` | PASS (matches documented "today" state) | `reports/qa/goal-market-compass-iter-1-evidence/UT-07-result.png` (same page state) |
| UT-J-01 | J-01: Sector attribution is honest and near-complete on new runs (goal-mode regression lane, target journey) | journey | target journey | All 6 journey steps hold: fresh run via Remove+Backfill, Unassigned ≤5%, DELL+GRMN cross-surface match, methodology two-source disclosure, honest null for an unmapped symbol, dev handoff cites the byte-identity fixture | Step 1 (Remove+Backfill) **FAILED** — see UT-03; without it, steps 2–3 (coverage ≤5%, GRMN cross-surface change) are unverifiable live this run. Step 4 (methodology disclosure) **not observable** — pre-existing, out-of-scope gate (`universe_selection` absent from `GET /api/methodology`; dev handoff's own "Known Issues" §1 documents this). Step 5 (honest null) — principle holds but has **zero live counterexamples today**: a CSV/API cross-check found all 422 currently-null-sector tickers in the resolved universe ARE present in `universe_pool.csv` with a real sector, so there is no "neither source" ticker to spot-check live in this data; the behavior itself is unit-tested via synthetic fixtures (TC-3/TC-7). Step 6 (dev handoff citation) **verified**: `docs/handoffs/goal-market-compass-iter-1-dev.md` cites `test_pool_sector_fallback_never_changes_any_score_bucket_or_setup` (TC-4) and `test_pool_sector_fallback_lifts_coverage_at_or_above_95_percent` (TC-1) by name, both reported passed | **FAIL** | `reports/qa/goal-market-compass-iter-1-evidence/UT-03-fail.png` |
| UT-J-08 | J-08: The market surface relocates intact and history never lies (goal-mode regression lane) | journey | regression lane | `/market` renders the relocated dashboard body; sidebar lists Today then Market; historical `?asof` shows that date's compass with a retrospective label | `/market` returns a **404** ("This page could not be found"); sidebar nav is unchanged (`Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Evidence, Watchlist, Methodology, Data Manager"` — no "Today"/"Market" entries). **Not a regression**: J-02–J-08 were already `failing` at the iter-0 baseline (0 passing / 1 partial / 7 failing), this iteration's IN SCOPE/OUT OF SCOPE sections explicitly defer J-08, and no file this iteration touched bears on `/market` or the sidebar | **FAIL** (pre-existing, not yet built — no regression) | `reports/qa/goal-market-compass-iter-1-evidence/UT-J-08-fail.png` |

---

## Passed Tests

### UT-01 — Stocks leaderboard loads
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-1-evidence/UT-01-result.png`
- Navigated to `/stocks`; heading "Stocks" and subtitle "Stock Leaderboard — ranked by Leadership, with independent Entry Quality and Risk (danger) scores, a setup status and a reason" both present.
- `data-testid="visible-count"` badge read `541 / 541` with no filters applied.
- Leaderboard table rendered with a "SECTOR" column header among others.
- No "Backend unavailable" card; no console errors observed (best-effort — this Chrome MCP build's console capture returned empty both via `get_console_messages` and the auto-captured `-console.txt` file, which itself contains a "Console logging not yet implemented" placeholder; treated as no-errors-observed rather than a confirmed clean console).

### UT-02 — Methodology core content loads
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-1-evidence/UT-02-result.png`
- Heading "Methodology" and subtitle "What every setup status and detected price pattern mean…" present.
- Six Setup/Pattern entry cards rendered (Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist, plus 3 pattern cards).
- Glossary section present near the bottom ("125 terms across 6 categories").
- No "Backend unavailable" card.
- Confirmed via direct API check that "Universe Selection" is correctly absent today (see UT-07/UT-10) — not treated as a failure per the test plan's explicit note.

### UT-06 — Remove panel requires both valid dates before enabling Preview
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-1-evidence/UT-06-result.png`
- With only "To date" filled (`2026-08-14`), `[data-testid="remove-preview-button"]` reported `disabled:true`.
- After typing the invalid value `2026-13-40` into "From date", the button remained `disabled:true`.
- No `[role="dialog"]` modal opened in either state.

### UT-07 — Methodology page degrades gracefully with today's gated payload
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-1-evidence/UT-07-result.png`
- Page rendered its full normal content (entries + glossary) with no visible gap or broken layout where a Universe Selection card would sit.
- Direct check: `curl http://localhost:8255/api/methodology` → top-level keys are exactly `['entries', 'intro', 'glossary']` — `universe_selection` is absent, confirming the conditional render fails safe rather than crashing.
- `document.querySelector('[data-testid="universe-selection"]')` → `false`; `[data-testid="universe-sector-basis"]` → `false`.

### UT-08 — Existing leaderboard behavior is unchanged: curated sectors, scores, filters
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-1-evidence/UT-08-result.png`
- Searched `DELL`: Sector cell read "Technology"; Leadership `B 81.30`, Entry Quality `E 37.85`, Risk `E 48.77` (current run, as of 2026-08-11).
- Cleared search, selected Setup filter = "Avoid": visible-count narrowed from `539 / 539` to `473 / 539`.
- Cleared Setup filter, clicked the "Sector" column header: a `data-testid="sort-indicator"` appeared next to "Sector" and the first rows reordered alphabetically (Communication Services ×3, then Consumer Discretionary ×5, …).
- Caveat recorded in the Results Table: the "far fewer Unassigned at one end" part of this test could not be confirmed because it depends on UT-03's fresh run, which did not materialize this run — same root cause as UT-03/UT-04/UT-05, not an independent finding.

### UT-09 — Sector filter is discoverable without any new navigation
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-1-evidence/UT-09-result.png`
- Note: the Chrome MCP tool's default viewport was a small 776×432 — not representative of "a standard desktop viewport" as this test specifically requires. Resized to 1440×900 before evaluating this test's assertions (a legitimate `set_viewport` call, not a profile/headed-mode change).
- From Dashboard, clicked "Stocks" in the sidebar: reached `/stocks` in exactly one click.
- Sector label/select sat in the same row as the search box (`top:326` for both), fully inside the 900px-tall viewport with `needsScroll:false`.

### UT-10 — Universe Selection "Stock sector labels" disclosure content (informational, non-blocking)
**Verdict:** PASS (observed state matches the test plan's documented "today, in this environment" expectation)
**Evidence:** `reports/qa/goal-market-compass-iter-1-evidence/UT-07-result.png` (same `/methodology` page state as UT-07; no separate screenshot needed)
- `[data-testid="universe-selection"]` and `[data-testid="universe-sector-basis"]` both confirmed absent — matches the test plan's explicit, pre-registered expectation for this environment (gated on the missing `apps/backend/data/seed/universe.json`, unrelated to this iteration).
- Per the test plan, this result is P3/non-blocking and does not gate the overall verdict either way.

---

## Failed Tests

### UT-03 — Precondition: seed-safe Remove + Backfill of the last two trading days
**Verdict:** FAIL
**Failure:** The Backfill job (Job kind left on the test plan's specified default, "Backfill snapshots") completed with status **"no new snapshots"** instead of the expected **"ok"**, and produced `0` new snapshots / `0` forward returns instead of counts `>0`.
**Evidence:** `reports/qa/goal-market-compass-iter-1-evidence/UT-03-fail.png` (shows Data Manager's "PRICE HISTORY: 1996-01-02 → 2026-08-12" — i.e. the dataset's latest bar is now 2026-08-12, not 2026-08-14, and the "Snapshot pending" banner)

**Steps taken:**
1. Navigated to `/data`. Filled "From date" = `2026-08-13`, "To date" = `2026-08-14`. Clicked "Preview removal".
2. Modal "Confirm data removal" opened showing `1174` bars / `587` affected symbols, range `2026-08-13 → 2026-08-14`, cascade `18 snapshots · 30439 forward returns`, no refused banner — matching the ui-test-plan's own live-preview numbers exactly. Clicked "Remove 1174 bars".
3. Confirmed via page text: "Removed 1174 user-added bars; cascade-removed 18 snapshots and 30439 forward returns." Run history logged this as `ok`.
4. In the "Start a fetch / backfill job" panel, set Start date = `2026-08-13`, End date = `2026-08-14`, left Job kind on its default "Backfill snapshots" (`value="backfill"`, confirmed via DOM read before submitting). Clicked "Start".
5. `data-testid="job-status"` read "running", then polled via the backend `/api/health` until `last_run_date` stabilized. Re-read the Run history table: newest row —

   ```
   2026-08-20 04:05:09  backfill  2026-08-13 → 2026-08-14  no new snapshots  0 / 0  0
   2 calendar days · 0 already snapshotted · 2 non-trading
   Refreshed: availability heatmap, coverage, membership timeline, forward aggregates, index series
   backfill: 0 snapshots over 0 dates, 0 forward returns
   ```

6. Investigated root cause with direct API/code checks (not speculation):
   - `GET /api/health` after the job: `last_run_date: 2026-08-11`, `seed_latest_date: 2026-08-12`.
   - `POST /api/data/remove/preview` re-run over the same range (`{"start":"2026-08-13","end":"2026-08-14"}`) now returns `refused:true, reason:"refused: no removable bars found in this scope."`, with `removable_bar_count/symbol_count` both `0` and `not_removable_bar_count:0` — i.e. **zero bars of any kind (user-added or seed) remain for these two dates**.
   - `apps/backend/app/engine/data_manager.py:158-165` (`_trading_days`): "The trading calendar = the benchmark's (SPY) seed bar dates… A date is a trading day iff SPY has a bar on it; this never fabricates a date." Since the benchmark's bars for 2026-08-13/14 were removed along with the other 586 symbols' bars, the app correctly (and honestly, per its own no-fabrication design) no longer treats those two dates as trading days for a bars-only Backfill.

**Expected:** Job status badge reads "ok"; text below reads "`<N>` snapshots · `<N>` forward returns inserted" with both `>0`.
**Actual:** Job status reads "no new snapshots"; `0` snapshots, `0` forward returns; the two dates are now reported "non-trading" because no bars exist for them at all.

**Assessment:** This is a genuine environment/test-design gap, not a defect in this iteration's product code. `2026-08-13`/`2026-08-14` were never part of the committed seed (`seed_latest_date` is `2026-08-12`) — they existed only as "user-added" bars from an earlier, unrelated live-fetch session (visible in the same Run history table: `2026-08-14 22:31:41  both  … Yahoo Finance …`). The test plan's UT-03/J-01 step 1 instructs leaving Job kind on "Backfill snapshots" (bars-only); that is insufficient to regenerate bars that were just deleted. Producing a fresh run for this exact range would require the "Fetch + backfill" job kind, which makes live HTTP calls to `https://query1.finance.yahoo.com/...` (confirmed by reading `apps/backend/app/data_providers/yahoo_provider.py`). Given AG-9 ("Offline-deterministic ingest… no live external network calls… without an explicit goal.md amendment", *critical*) and that this action is outside what the test plan itself specifies, this agent did not attempt it. **Recommendation for the next iteration/owner:** either amend the precondition to use a date range that still has committed-seed bars beneath it, or explicitly authorize a "Fetch + backfill" (or a local/offline fixture-backed provider) for this precondition specifically.

---

### UT-J-01 — J-01: Sector attribution is honest and near-complete on new runs
**Verdict:** FAIL
**Failure:** Step 1 of the journey (seed-safe Remove + Backfill to produce a fresh run) did not succeed — see UT-03 above, which is the identical action executed for this journey (not repeated, to avoid a second destructive operation in the same run). Without a fresh run, the journey's central live claims (coverage ≥95%, GRMN's cross-surface change) cannot be demonstrated in the browser this run.
**Evidence:** `reports/qa/goal-market-compass-iter-1-evidence/UT-03-fail.png`

**Steps taken / per-step findings:**
1. Remove + backfill on `/data` — **FAILED**, see UT-03 for full evidence. Reused rather than repeated in this same run.
2. Unassigned-share ≤5% check on `/stocks` — **not executable** (no fresh run). Supplementary check performed instead: cross-referenced every currently-null-sector ticker in `GET /api/stocks` (422 of the 539-member current run) against `apps/backend/data/seed/universe_pool.csv`'s `sector` column — **all 422** are present in the pool CSV with a real sector value (e.g. `GRMN → Consumer Discretionary`, matching the test plan's own stated expectation). This is consistent with — but not a live substitute for — the fallback lifting coverage above 95% once a fresh run exists; the dev handoff cites a passing unit test for exactly this claim (`test_pool_sector_fallback_lifts_coverage_at_or_above_95_percent`, TC-1).
3. Cross-surface spot-check — DELL confirmed "Technology" on the leaderboard (curated, unaffected by the fallback either way — a valid but non-diagnostic regression check). GRMN's fallback-driven change from "Unassigned" to "Consumer Discretionary" **could not be observed live** — the current run (2026-08-11) predates this iteration's code taking effect on any stored row.
4. Methodology two-source disclosure — **not observable**: `GET /api/methodology` omits the `universe_selection` key entirely (confirmed directly). This is a pre-existing, out-of-scope gate (missing `apps/backend/data/seed/universe.json`), documented identically by the dev handoff's own "Known Issues" §1 and by UT-02/UT-07/UT-10 above. The underlying code is implemented and unit-tested (`test_universe_selection_sector_basis_present_and_matches_config` et al., cited passing in the dev handoff) but not reachable through the live UI/API in this environment.
5. Honest-null check — the PRINCIPLE holds (unchanged from the iter-0 baseline's binding "Do not redo" note) but has **no live counterexample today**: the same 422-ticker cross-check found zero tickers absent from BOTH `config.stock_sectors` and the pool CSV in the current resolved universe. Verified instead via the dev handoff's cited synthetic-fixture unit tests (TC-3/TC-7).
6. Dev handoff citation — **verified**: `docs/handoffs/goal-market-compass-iter-1-dev.md` names `test_pool_sector_fallback_never_changes_any_score_bucket_or_setup` (TC-4, PASSED) and `test_pool_sector_fallback_lifts_coverage_at_or_above_95_percent` (TC-1, PASSED) explicitly.

**Expected:** All 6 steps hold, per goal.md's J-01 Acceptance criteria.
**Actual:** Step 1 failed (environment/data-availability gap, not a product defect); steps 2–3's live-browser claims are consequently unverifiable this run; step 4 is blocked by an unrelated pre-existing gate; step 5's principle holds with no live counterexample to show; step 6 holds. No golden replay script was written for this journey (only written for journeys verified PASS this run).

---

### UT-J-08 — J-08: The market surface relocates intact and history never lies
**Verdict:** FAIL (pre-existing — not yet built this session; NOT a regression)
**Failure:** `/market` returns a 404; the sidebar has not been reorganized into "Today"/"Market".
**Evidence:** `reports/qa/goal-market-compass-iter-1-evidence/UT-J-08-fail.png`

**Steps taken:**
1. Navigated to `http://localhost:3255/market` → page rendered "404: This page could not be found."
2. Read the sidebar nav: `["Dashboard","Stocks","Themes","Sectors","Scanner Runs","Backtest","Research","Evidence","Watchlist","Methodology","Data Manager"]` — no "Today" or "Market" entries; "Dashboard" still present at `/`.
3. Did not proceed to steps 3–6 (historical `?asof` / manifest-strip checks) since the target surfaces (`/market`, the relocated sidebar) do not exist to test against.

**Expected:** `/market` renders the relocated dashboard body; sidebar lists Today then Market.
**Actual:** `/market` is a 404; sidebar is unchanged from before this session.

**Assessment:** This is **not a regression**. goal.md's own iter-0 baseline already recorded J-02 through J-08 as `failing` (0 passing / 1 partial / 7 failing), and `docs/phases/goal-market-compass-iter-1.md`'s OUT OF SCOPE section explicitly defers "J-02 through J-08 (session delta engine, plain-English summary, next-session candidate selection, manifest freeze/immutability, Today page, Market relocation)". No file this iteration touched (config.py, config.yaml's `universe`/`methodology` blocks, `universe_screen.py`, `scoring.py`, `methodology.py`, and `apps/frontend/app/methodology/page.tsx`) bears on `/market`, the sidebar, or routing. J-08 remains exactly where it was at baseline; goal.md's own suggested build order places the J-05/J-06 freeze pair and this J-07/J-08 surface pair after the J-02/J-03/J-04 engine cluster, several iterations from now.

---

## Skipped Tests

### UT-04 — Sector coverage improves to ≤5% Unassigned at the new latest as-of (TC-1)
**Verdict:** SKIPPED
**Reason:** prerequisite data missing — UT-03's Remove+Backfill precondition did not produce a fresh run (job status "no new snapshots", not "ok"; see UT-03 for full evidence). No new `/stocks` run exists under this iteration's fallback code to measure coverage against. A non-substitute supplementary check (pool-CSV vs. current-API cross-reference, see UT-J-01 step 2) suggests the fallback would clear the ≤5% bar comfortably once a fresh run exists, but this is not a live browser/API verification of TC-1 itself.

### UT-05 — Cross-surface sector consistency for a curated and a pool-fallback ticker (TC-2)
**Verdict:** SKIPPED
**Reason:** prerequisite data missing — same root cause as UT-04. GRMN's fallback-driven sector change (Unassigned → Consumer Discretionary) cannot be observed on the leaderboard, detail page, or API without a fresh run produced under this iteration's code.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), viewport resized from the tool's small 776×432 default to 1440×900 for UT-09 and all tests from that point onward (a `set_viewport` call only — browser profile/CDP port/headed-mode were never changed)
- **Test Date:** 2026-08-20
- **Evidence directory:** `reports/qa/goal-market-compass-iter-1-evidence/`
- **Data-state note:** this run executed a real (seed-safe) Remove of 2026-08-13/2026-08-14 bars via `/data`, which did **not** get restored by the follow-up Backfill (see UT-03). As of report time, the dataset's latest bar/run is 2026-08-12 (bar) / 2026-08-11 (scanner run) — 591 symbols, `seed_latest_date: 2026-08-12`. No data outside the specified 2-day scope was touched; the committed seed itself is unaffected (the removal was confirmed "user-added" only, per the pre-removal preview).
