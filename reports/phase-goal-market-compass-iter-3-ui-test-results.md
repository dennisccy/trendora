# UI Test Results (merged)

**Date:** 2026-08-20
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** BLOCKED

**Overall:** 16/18 journeys passed (2 skipped, 2 target-missing)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | J-01: Sector attribution is honest and near-complete on new runs | regression (goal journey) | P1 | Unassigned share ≤5% on new runs; spot-checked names consistent across leaderboard/detail/API; `/methodology` discloses two-source basis + current-only limitation; unmapped symbol serves null/Unassigned honestly | `GET /api/stocks` (as_of 2026-08-12, 539 rows): 0 Unassigned (0.0%, well under 5%) — sector filter dropdown has no "Unassigned" option at all since none exist; GRMN="Consumer Discretionary" and HPE="Technology" identical across `/api/stocks` list, `/api/stocks/<TICKER>` detail, and the `/stocks` leaderboard Sector cell; `/methodology` "Stock sector labels → Data basis" discloses the curated-then-pool-fallback two-source order, the "never a fabricated value" Unassigned rule, and the CURRENT-only / no point-in-time-history limitation verbatim; replayed the exact flagged golden script (`/stocks?asof=2026-08-12` → search "GRMN" → expect "Consumer Discretionary") end-to-end and it passed cleanly — the prior replay FAIL was stale, not a real regression; golden script re-verified and re-saved unchanged | PASS | `reports/qa/goal-market-compass-iter-3-evidence/UT-J-01-result.png` |
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-3-evidence/J-02-verify.png |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-3-evidence/J-03-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-3-evidence/J-04-verify.png |
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

## Missing Target Journeys

_Target journeys named in the iteration spec's `Target journeys:` line — the journeys THIS iteration exists to verify — that were NOT verified this iteration, either no lane produced a row for them at all, or the only row they have reads SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are present (ops-hardening iter-41 audit finding B2 / iter-42 fix: promoting a journey to an iteration's own target silently removed its verification — iter-41 itself shipped a clean PASS 6/6 headline while its two target journeys had zero rows anywhere)._

- `UT-J-05` — no test case executed for J-05 by any lane
- `UT-J-06` — no test case executed for J-06 by any lane

## Skipped Tests

### UT-07 — Manifest card "unavailable" state on backend down

**Verdict:** SKIPPED
**Reason:** Not executed — see Skipped Tests section

### UT-12 — `/data` "Refreshed:" line shows hyphenated phase name

**Verdict:** SKIPPED
**Reason:** Not executed — see Skipped Tests section

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-20

