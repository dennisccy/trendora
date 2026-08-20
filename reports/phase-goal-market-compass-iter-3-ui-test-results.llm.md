# goal-market-compass-iter-3 — UI Test Results

**Phase:** goal-market-compass-iter-3
**Date:** 2026-08-20
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 13/15 tests passed (2 skipped, 0 failed)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Dashboard loads with Manifest card present | smoke | P1 | Heading "Dashboard" + subtitle, Manifest card visible as 4th compass card, no console error | Heading "Dashboard", subtitle "The daily snapshot at a glance" present; `compass-manifest-strip` present and populated (not blank); card order confirmed Summary→What changed→Next-session focus→Manifest→dashboard body | PASS | `reports/qa/goal-market-compass-iter-3-evidence/UT-01-result.png` |
| UT-02 | Manifest card shows full badges + hash chips (historical date) | happy-path | P1 | Stepping ◀ once shows historical badges (mode/version/frozen/eligible), Frozen timestamp, 4 hash chips ending "…" with full hash in `title`, dataset/universe/members/profile lines, Basis badge | `asof-indicator`="Viewing as-of 2026-08-11 (historical)"; badges="retrospective, version 1, frozen, not prospective-eligible"; all 4 hash chips present, each `title` attr holds the full untruncated sha256; Basis: available; Members: 539; Profile: core; Dataset stamp present | PASS | `reports/qa/goal-market-compass-iter-3-evidence/UT-02-result.png` |
| UT-03 | Audit table expands (comparison cohort + shadow) | happy-path | P1 | Expand reveals cohort table (7 cols incl. Disposition, valid values only) + shadow table (6 cols, no Disposition) + 3 caveat sentences | `<details>` opened; "Comparison cohort (non-selected pool)" heading + non-causal caveat present; table 1 headers Ticker/Leadership/Entry/Risk/Setup/Sector/Disposition, 539 rows, all values in {"below selection floor","excluded by cap"} (0 invalid); shadow heading present, table 2 same 6 cols minus Disposition, 32 rows; evidence/survivorship/sector-basis caveats all present | PASS | `reports/qa/goal-market-compass-iter-3-evidence/UT-03-result.png` |
| UT-04 | Regenerate mints a new version in place | happy-path | P1 | Modal states mint-new/never-touched; confirm closes modal, no reload, version+1, not-eligible, new Frozen time, Versions list ≥2 rows | Modal text matched verbatim ("mints a NEW manifest version for 2026-08-11", "existing version is never touched, changed, or deleted"); after confirm: modal closed, URL unchanged (`?asof=2026-08-11`), version 1→2, "not prospective-eligible", Frozen time 12:14:33→12:37:04, Versions section shows 2 rows | PASS | `reports/qa/goal-market-compass-iter-3-evidence/UT-04-result.png` |
| UT-05 | Cancel regenerate modal creates no new version | validation | P2 | Both footer-Cancel and ✕-icon close the modal with version/timestamp unchanged | Footer "Cancel": modal closed, badges stayed "version 2 … Frozen 12:37:04" (identical to pre-click); repeated via `aria-label="Cancel"` ✕ icon: same result, version/timestamp unchanged both times | PASS | `reports/qa/goal-market-compass-iter-3-evidence/UT-05-result.png` |
| UT-06 | Regenerate hidden while on "Latest" | validation | P2 | On Latest: no Regenerate button, explanatory line shown instead | `asof-indicator`="Latest"; `compass-manifest-regenerate-button` absent; `compass-manifest-regenerate-unavailable` text exactly "Regenerate is available only for a stored historical date — step the as-of switcher off \"Latest\" first." | PASS | `reports/qa/goal-market-compass-iter-3-evidence/UT-06-result.png` |
| UT-07 | Manifest card "unavailable" state on backend down | error | P2 | Red-bordered unavailable box shown when `/api/compass` fails | Not executed — see Skipped Tests section | SKIP | none |
| UT-08 | Regenerate API rejects missing confirm / missing manifest | error | P2 | Missing `confirm=true` → 400 mentioning confirm=true, no row created; non-trading/no-manifest as-of → 4xx, never 200 | `POST /api/compass/regenerate?as_of=2026-08-05` (no confirm) → HTTP 400, `{"detail":"regenerate requires confirm=true — no row was created"}`; `POST …as_of=2026-08-08&confirm=true` (Saturday, no manifest) → HTTP 404, `{"detail":"no next-session manifest exists yet for 2026-08-08 — regenerate requires an existing manifest"}` | PASS | none (API-only test per plan; curl transcript in agent log) |
| UT-09 | Summary card cited facts render rounded | regression | P1 | Every numeric cited fact shows exactly 2 decimals, no raw float artifacts | Expanded "Show cited facts"; regex scan of the card found zero values with 3+ trailing decimal digits; confirmed `regime_score_delta:-0.20`, `regime_score:73.24`, `severity:25.84`, `breadth_above_50dma:59.84`, `breadth_above_200dma:66.39`, `candidate_count:0.00` — all exactly 2 decimals | PASS | `reports/qa/goal-market-compass-iter-3-evidence/UT-09-result.png` |
| UT-10 | ATR caution text has no advice-sounding tail | regression | P2 | ATR_RISK_BUDGET caution ends "of universe)." with no "sized risk accordingly"; REGIME_RISK_OFF caution also present on a Risk-off date | Stepped to `?asof=2025-04-15` (Risk-off regime, confirmed via API first); candidate card (MCD) shows "ATR_RISK_BUDGET: ATR is 2.99% of price (p6 of universe)."; phrase "sized risk accordingly" absent from the card; "REGIME_RISK_OFF: the market regime is Risk-off as of this date — every candidate here is context, not a signal to act." also present, unchanged | PASS | `reports/qa/goal-market-compass-iter-3-evidence/UT-10-result.png` |
| UT-11 | Pre-existing compass cards still render correctly | regression | P1 | Card order Summary→What changed→Next-session focus→Manifest→dashboard body unchanged; no card removed/broken | Measured DOM element positions: Summary (top 229) → What changed (522) → Next-session focus (1159) → Manifest (1337) → Market Phase & Severity (1800); Summary/What-changed/Next-session-focus all show their normal narrative/empty-state content alongside the new Manifest card | PASS | `reports/qa/goal-market-compass-iter-3-evidence/UT-11-result.png` |
| UT-12 | `/data` "Refreshed:" line shows hyphenated phase name | regression | P3 | A completed backfill's "Refreshed:" line includes "next-session manifest" (hyphenated) | Not executed — see Skipped Tests section | SKIP | none |
| UT-13 | Manifest card discoverable by scroll alone | ux | P2 | Reached by scrolling `/` only; badge words self-explanatory; no broken link/nav placeholder | Manifest card reached by scroll on the same `/` load as UT-01 (no menu/tab click); badge words "frozen", "version 5", "not prospective-eligible" visible without expanding anything; sidebar nav list (Dashboard/Stocks/Themes/Sectors/Scanner Runs/Backtest/Research/Evidence/Watchlist/Methodology/Data Manager) has no separate "Manifest" entry, broken link, or "coming soon" placeholder | PASS | `reports/qa/goal-market-compass-iter-3-evidence/UT-13-result.png` |
| UT-14 | Pre-freeze-era rows show honest empty state | ux | P3 | On Latest with a pre-freeze row: only the predates-freeze sentence, no fabricated badges; if Latest is already post-freeze, note not-applicable per the test's own fallback | `compass-manifest-pre-freeze-era` absent; Latest's badges already show full content (mode "at ingest", version 5, frozen, hash chips, versions list) — Latest has already been regenerated past the pre-freeze-era state since the developer's last live-verification. Per the test's explicit fallback clause this is recorded as **not applicable — Latest is already post-freeze**, not a failure; no fabricated content was observed either way | PASS | `reports/qa/goal-market-compass-iter-3-evidence/UT-14-result.png` |
| UT-J-01 | J-01: Sector attribution is honest and near-complete on new runs | regression (goal journey) | P1 | Unassigned share ≤5% on new runs; spot-checked names consistent across leaderboard/detail/API; `/methodology` discloses two-source basis + current-only limitation; unmapped symbol serves null/Unassigned honestly | `GET /api/stocks` (as_of 2026-08-12, 539 rows): 0 Unassigned (0.0%, well under 5%) — sector filter dropdown has no "Unassigned" option at all since none exist; GRMN="Consumer Discretionary" and HPE="Technology" identical across `/api/stocks` list, `/api/stocks/<TICKER>` detail, and the `/stocks` leaderboard Sector cell; `/methodology` "Stock sector labels → Data basis" discloses the curated-then-pool-fallback two-source order, the "never a fabricated value" Unassigned rule, and the CURRENT-only / no point-in-time-history limitation verbatim; replayed the exact flagged golden script (`/stocks?asof=2026-08-12` → search "GRMN" → expect "Consumer Discretionary") end-to-end and it passed cleanly — the prior replay FAIL was stale, not a real regression; golden script re-verified and re-saved unchanged | PASS | `reports/qa/goal-market-compass-iter-3-evidence/UT-J-01-result.png` |

---

## Passed Tests

### UT-01 — Dashboard loads with the Manifest card present
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-3-evidence/UT-01-result.png`
- Heading "Dashboard" and subtitle "The daily snapshot at a glance" render; `[data-testid="compass-manifest-strip"]` exists and is populated (badges text non-empty), not blank/broken.
- Note: this Chrome MCP build's console-log capture is a stub ("Console logging not yet implemented" — confirmed by reading the auto-captured `*-console.txt` file), so "no uncaught exception" was verified by the practical proxy of no visible error boundary / blank page / red error text anywhere on the loaded page, rather than by reading console output directly. Flagging this as a tooling limitation, not a product defect.

### UT-02 — Manifest card shows full freeze/integrity badges + hash chips on a historical date
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-3-evidence/UT-02-result.png`
- One click of `asof-step-prev` from Latest (2026-08-12) stepped to 2026-08-11 and create-once minted a fresh `retrospective` version-1 manifest (first-ever view of that date).
- All required badges/lines/chips present and correctly worded; hash-chip `title` attributes hold the full untruncated sha256 values (verified programmatically — the same value a hover/long-press tooltip would reveal).

### UT-03 — Audit table expands to reveal comparison cohort + near-threshold shadow tables
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-3-evidence/UT-03-result.png`
- Comparison cohort table: 539 rows (= 539 members − 0 candidates), disposition values are a closed set of exactly `{"below selection floor"}` in this sample (0 candidates were selected on this date, so no member was cap-excluded) with 0 rows outside the closed vocabulary.
- Shadow table: 32 rows, columns identical minus "Disposition". All three caveat sentences (evidence / survivorship / sector-basis) present below both tables.

### UT-04 — Confirm-gated regenerate mints a new manifest version in place
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-3-evidence/UT-04-result.png`
- Modal body text matched both required verbatim phrases. Post-confirm: no navigation (URL stayed `?asof=2026-08-11`), version 1→2, eligibility correctly stayed "not prospective-eligible", Frozen timestamp advanced, Versions list grew to 2 rows.

### UT-05 — Cancelling the regenerate confirm modal creates no new version
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-3-evidence/UT-05-result.png`
- Verified both cancel paths (footer "Cancel" button and the `aria-label="Cancel"` ✕ icon) leave version and Frozen timestamp byte-identical to the pre-click state.

### UT-06 — Regenerate control is replaced by an explanatory line while viewing "Latest"
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-3-evidence/UT-06-result.png`
- No Regenerate button in the DOM at all while on Latest; the exact gating sentence renders instead.

### UT-08 — Regenerate API rejects a missing confirm flag and an as-of with no manifest
**Verdict:** PASS
**Evidence:** none (API-only test per the plan's own instructions — verified via curl, not a UI screenshot)
- Both sub-cases returned the expected honest 4xx with no fabricated 200.

### UT-09 — Summary card's cited facts render rounded, not raw floats
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-3-evidence/UT-09-result.png`
- Programmatic regex scan of the whole cited-facts panel found zero occurrences of a 3+-decimal-digit float; every numeric value found was exactly 2 decimals.

### UT-10 — Candidate card ATR caution states the fact only, no advice-sounding tail
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-3-evidence/UT-10-result.png`
- Used the API first (read-only) to locate a Risk-off date with real candidates (2025-04-15), then confirmed the same text in the rendered UI candidate card.

### UT-11 — Pre-existing compass cards still render correctly beside the new Manifest card
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-3-evidence/UT-11-result.png`
- Card vertical order measured directly from DOM `getBoundingClientRect()` positions, not just visual scan.

### UT-13 — Manifest card is discoverable without extra navigation
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-3-evidence/UT-13-result.png`
- Reached by scroll alone on the same page load used for UT-01; no separate nav entry exists for it.

### UT-14 — Legacy pre-freeze-era manifest rows show the honest empty state, never fabricated badges
**Verdict:** PASS (not-applicable outcome, per the test's own documented fallback)
**Evidence:** `reports/qa/goal-market-compass-iter-3-evidence/UT-14-result.png`
- Latest's manifest row has already been regenerated to version 5 (mode `at_ingest`, frozen) since the developer's own live-verification pass, so the pre-freeze-era (`mode: null`) state is not currently reproducible on Latest. The test plan explicitly instructs recording this as "not applicable — Latest is already post-freeze" rather than a failure, which is what happened — no badges/chips were fabricated for a row that lacks them (the row in question simply no longer lacks them). No other live as-of date was hunted for a pre-freeze row, since the applicability check is scoped to "Latest" only per the test's preconditions.

### UT-J-01 — J-01: Sector attribution is honest and near-complete on new runs (goal-mode regression re-check)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-3-evidence/UT-J-01-result.png`
- Re-verified the journey's observable acceptance state on current live data rather than repeating its destructive step-1 remove+backfill (deliberately not re-run — see rationale below).
- Unassigned coverage is 0.0% today (539/539 resolved), stronger than the journey's ≤5% bar; the leaderboard's sector-filter dropdown has no "Unassigned" entry at all as a direct consequence.
- Spot-checked GRMN ("Consumer Discretionary") and HPE ("Technology") for identical values across `/api/stocks`, `/api/stocks/<TICKER>`, and the `/stocks` leaderboard UI.
- `/methodology` discloses the two-source basis and current-only limitation verbatim.
- Replayed the exact stored golden script (`runs/goal-session-market-compass/journey-scripts/J-01.json`) step-by-step in the browser and it passed cleanly end-to-end, proving the deterministic-replay lane's flagged "possible regression" was stale, not a real regression — nothing in iter-3's scope touches sector attribution (confirmed against the surface map's Backend-Only-Changes list). Golden script re-linted (`demo_runner.py --mode lint`) and re-saved.
- Not independently re-verified: journey step 5 ("a symbol absent from both maps still serves `sector: null`") — not reproducible against current live data since coverage is 0% Unassigned right now (no such symbol exists in the current run to sample). This is a pre-existing/orthogonal code path untouched by iter-3 and outside what a non-destructive re-check can exercise; noted here rather than silently assumed.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-07 — Manifest card shows an honest "unavailable" state when the backend is unreachable
**Verdict:** SKIPPED
**Reason:** This test requires either stopping the backend process or blocking the `GET /api/compass` request via browser devtools request-blocking. Both are unavailable to this agent in this environment: (1) the browser-qa-agent rules explicitly forbid restarting/stopping the app ("Never debug or restart the app — that is a SKIPPED with reason"), and the backend is a shared service the coordinator confirmed is in active use by this pipeline run — stopping it was not an option; (2) the Chrome MCP tool exposed to this session (`mcp__plugin_superpowers-chrome_chrome__use_browser`) has no network-request-blocking/interception action in its schema (checked via `action: "help"` — no `network`/`block` action exists). The remaining alternative (registering a Service Worker to intercept `/api/compass` client-side) was rejected as unsafe: it would persist on the shared, pinned Chrome profile beyond this test and could leak into other concurrent agents' testing, conflicting with the coordinator's "keep ONE clean browser context" instruction. No attempt was made to degrade the shared backend to force this state.

### UT-12 — `/data` "Refreshed:" line shows the hyphenated "next-session manifest" phase name
**Verdict:** SKIPPED
**Reason:** The test plan permits skipping this P3 test "if no backfill can safely be run during this QA pass," and requires using an already-scheduled/available job rather than skipping only when one exists. Checked `/data`'s Run History first (non-destructively): none of the ~40 visible completed jobs' "Refreshed:" lines mention "next-session manifest" or "next session manifest" in either form — all recent backfills ran over date ranges that either weren't the frontier date or already had a manifest, so the honesty-gated compass phase never fired for them. Producing a qualifying job would require actively running the seed-safe Remove + Backfill flow (the same destructive/heavy operation UT-12 and J-01-step-1 share) against the current frontier date. Given the coordinator's explicit standing memory-safety guidance for this run (host froze this morning from memory overcommit/swap-thrash; a second goal-mode engine is concurrently active on this host) and the browser-qa-agent's rule against debugging/restarting or otherwise destabilizing shared app state, this agent chose not to initiate a new backfill job. No qualifying job was available to inspect instead.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned profile — single browser context/tab used throughout, no new tabs opened
- **Test Date:** 2026-08-20
- **Evidence directory:** `reports/qa/goal-market-compass-iter-3-evidence/`
- **Golden replay scripts written/repaired this run:** `runs/goal-session-market-compass/journey-scripts/J-01.json` (re-verified passing, re-saved, linted clean)
- **Known tooling limitation:** this Chrome MCP build's console-message capture is unimplemented (`get_console_messages` / the auto-captured `*-console.txt` files both report "Console logging not yet implemented"); console-error-based checks fell back to DOM/visual verification instead.
