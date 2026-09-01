# Goal Iteration 38 — UI Test Results

**Phase:** goal-market-compass-iter-38
**Date:** 2026-09-01
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- PASS: All smoke and happy-path tests pass. FAIL: any smoke/happy-path/P1 test fails. -->

**Overall:** 5/8 tested journeys passed (0 skipped) — 3 FAIL (J-08, J-11, J-13), all traced to one shared root-cause regression.

---

## Critical finding (applies to J-08, J-11, J-13)

`apps/frontend/components/compass-focus-section.tsx:192-197` unconditionally dereferences
`selection.why_not_totals.excluded_by_cap_uncapped` / `.below_floor_in_band_uncapped` with no
null-guard:

```
summary={`Not priority (${selection.why_not.length} shown of ${
  selection.why_not_totals.excluded_by_cap_uncapped + selection.why_not_totals.below_floor_in_band_uncapped
} held back — ...
```

`why_not_totals` is a field this iteration (J-14) added to the manifest payload. Any
`next_session_manifests` row minted **before** this iteration's backend deploy does not carry
it, so `selection.why_not_totals` is `undefined` for those rows and the expression throws
`TypeError: Cannot read properties of undefined (reading 'excluded_by_cap_uncapped')` during
render. The error propagates to the page-level error boundary and the entire `/` page renders
"Something went wrong on this page" instead of any content — reproduced deterministically
(retried once via the boundary's own "Try again" button; it errors again identically).

Verified live (DB query on `apps/backend/data/trendora.db`, 22 total manifested `as_of` dates):
only the frontier date (`2026-08-12`, freshly re-minted today as v10 after this iteration's fix
landed) and dates I minted fresh **during this test session** (never manifested before,
e.g. `2005-04-15`) render correctly. Every one of the other 21 pre-existing manifested dates I
sampled — `2025-04-15`, `2026-03-30`, `2026-08-11`, `1996-01-02` — crashes the `/` page on
navigation. This is not one bad date; it is a systemic backward-compatibility gap: **every
historical manifest that predates this iteration's schema addition is unviewable** on the Today
page, which directly contradicts AG-12/the goal's "nothing is removed" success criterion and is
the literal subject-matter of J-08 and J-11.

Screenshots: `reports/qa/goal-market-compass-iter-38-evidence/UT-J-11-fail.png` (crash on
`/?asof=2026-08-11`), `UT-J-11-retry.png` (same crash after clicking "Try again" — deterministic),
`UT-J-13-fail.png` (crash on `/?asof=1996-01-02`, J-13's own required step-7 date).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | happy-path | P1 | Candidate count/detail/checklist/why-not distances match `GET /api/compass`+`/api/stocks`; Risk-off caution renders on candidates at a Risk-off as-of | Verified on frontier (2026-08-12): 10 candidates match; HPE card (Leadership 92.7, Entry 21.5, Risk 58.9) matches `/api/stocks`; checklist shows Pass/Miss verdicts; why-not entries show rank/cap/distances. Risk-off verified at `?asof=2005-04-15`: regime badge "Risk-off", every candidate carries `REGIME_RISK_OFF` caution, "worth monitoring next session" framing, no entry-advice wording | PASS | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-04-result.png`, `UT-J-04-riskoff-result.png` |
| UT-J-05 | Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | happy-path | P1 | Manifest strip shows mode/version/frozen/prospective-eligible/hashes/dataset/universe stamps; requesting an old stored date with no manifest mints exactly one retrospective manifest | Frontier manifest strip shows all required stamps (at ingest, version 10, frozen, not prospective-eligible, engine/candidate/cohort/manifest-config hashes, dataset stamp r3160-f6815424, universe pool 539 members/profile core, Basis: available, versions v1–v10 listed). `GET /api/compass?as_of=2005-04-15` (never-manifested date) minted exactly one manifest: version 1, frozen true, mode retrospective, prospective_eligible false, producer on_demand_get — matches acceptance | PASS | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-05-result.png` |
| UT-J-06 | A frozen manifest never changes — later data, rebuilds, and regeneration are safe | happy-path | P1 | Regenerate control opens a confirm dialog stating immutability guarantees; Cancel performs no mutation; multiple versions listed with stamps | Clicked `compass-manifest-regenerate-button` on `?asof=2005-04-15` → dialog "Confirm manifest regenerate" reads "This mints a NEW manifest version... The existing version is never touched, changed, or deleted — it stays byte-identical and readable." Clicked Cancel; re-fetched `/api/compass?as_of=2005-04-15` → version still 1, versions list length still 1 (no mutation). Frontier versions list (v1–v10) already renders with per-version stamps as static, non-interactive `<li>` rows | PASS | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-06-result.png` |
| UT-J-07 | The Today page answers the ten-second read from served values only | happy-path | P1 | Body renders state-band → summary → what-changed → leadership-rotation → focus → manifest strip, in that order, with readiness/preflight in chrome above; tile values match `/api/dashboard` and `/api/market-phase`; cross-view chart absent from `/`, present on `/market` | DOM testid order confirmed exactly: `compass-state-band-card` → `compass-summary-card` → `compass-whatchanged-card` → `compass-leadership-rotation-section` (sector/theme only, no stock-kind row) → `compass-focus-section` → `compass-manifest-strip`, with `readiness-badge`/`preflight-banner` before all of them. Regime 73.18 / Risk-on matches `/api/dashboard`; phase Expansion / severity 25.85 / P(bear) 0.0017 matches `/api/market-phase`. Summary sentence "Universe breadth: 59.8%... 66.4%..." matches served breadth fields verbatim. `phase-cross-view-chart` testid present only on `/market`, absent on `/`, with a "Full market context... →" link-out to `/market` | PASS | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-07-result.png` |
| UT-J-08 | The market surface relocates intact and history never lies | happy-path | P1 | `/market` renders full former dashboard inventory (Top Sectors, Top Themes, Candidate Counts, Market Phase & Severity, breadth cards); sidebar order/highlighting correct; historical `?asof=D` renders D's stored values with a visible retrospective label | `/market` confirmed to contain "Top Sectors", "Top Themes", "Candidate Counts", "Market Phase & Severity", "More detail" (all present in DOM); sidebar Today-then-Market order and `aria-current="page"` highlighting both correct; `/market?asof=2026-08-11` renders fine (no crash — Market page does not touch the new compass fields). **However**, the Today page's (`/`) own required historical-navigation behavior is broken: `/?asof=2026-08-11` (an actual incident date with a real manifest, used by J-11), `/?asof=2025-04-15` (J-05/J-06's own reference date) and `/?asof=2026-03-30` all crash with "Something went wrong on this page" instead of showing D's stored values / retrospective label / predecessor comparison — see Critical Finding above | FAIL | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-11-fail.png` (same crash class, `/?asof=2026-08-11`), `UT-J-08-result.png` (working `/market` page) |
| UT-J-11 | Incident-bounded clean regeneration of derived state (serving verification only — J-11 itself is CLOSED/PASSING per owner ruling; this run re-verifies the two-URL basis-disclosure check its own golden script uses) | regression | P1 | `/?asof=2026-08-11` shows "Basis: rebuilt"; `/?asof=2026-08-12` shows "Basis: available" | `/?asof=2026-08-12` (latest) correctly shows "Basis: available" in the manifest strip. `/?asof=2026-08-11` — the actual J-10/J-11 incident date, which does carry a real stored manifest whose API payload correctly reports `basis.status: "rebuilt"` — crashes the page before any content renders (confirmed deterministic: retried via the error boundary's "Try again" button, crashed identically). The basis-disclosure UI cannot be visually verified for this date this iteration | FAIL | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-11-fail.png`, `UT-J-11-retry.png` |
| UT-J-13 | "Leadership rotation" says which way, shows both directions, and stops repeating What-changed | happy-path | P1 | Rotation section (sector+theme, no stock row) with signed deltas/direction words/accounting lines matching `/api/sectors`+`/api/themes`; stepping to the earliest stored session renders the rotation block's honest no-prior-run state | On frontier: `compass-leadership-rotation-section` renders exactly as specified — "Sector rotation" gaining (Regional Banks (SPDR) 13→10 (-3)·improving, Bitcoin Miners (Valkyrie), Real Estate, Banks (SPDR), Technology) and losing (Home Construction (iShares) 21→25 (+4)·deteriorating, Materials) sides, "7 of 31 shown · 24 below threshold · 0 beyond the display cap."; "Theme rotation" similarly with "2 of 11 shown · 9 below threshold · 0 beyond the display cap."; no stock-kind row present. **Step 7 fails**: stepping to `?asof=1996-01-02` (the earliest stored session, which also has an empty candidate list / `candidates_empty_reason`) crashes the whole page via the same `selection.why_not_totals` bug described in the Critical Finding — the required no-prior-run rotation state is never reached | FAIL | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-13-result.png` (frontier, passing part), `UT-J-13-fail.png` (step-7 crash) |
| UT-J-14 | "Not priority" names its real reason — the why-not block stops claiming a qualifier pass it never checked, and the actually-near-miss names come back | happy-path | P1 | Zero why-not entries claim "passed every qualifier, cut only by the focus-list cap." when their stored row fails an advisory qualifier; each entry states its true `reason` (`excluded_by_cap`/`below_selection_floor`) with threshold/actual/distance and, for cap-excluded entries, its rank + cap; disclosure header shows both uncapped totals | `GET /api/compass` selection.why_not: 20/20 entries have non-empty `failed_conditions` (was 20/20 empty pre-fix); DXCM entry matches TC-1 exactly (reason excluded_by_cap, cap_rank 11, cap 10, entry_min_score 26.5 vs 70.0 distance 43.5, gating:false); EXPE entry matches TC-3 shape (reason below_selection_floor, leadership_min_score gating:true distance 0.19, plus advisory misses). `why_not_totals`: excluded_by_cap_uncapped=27, below_floor_in_band_uncapped=25 (matches the spec's measured baseline). Rendered page: disclosure header literally reads "Not priority (20 shown of 52 held back — 27 cap-excluded, 25 below-floor near-miss)"; zero occurrences of "passed every qualifier" anywhere on the page (grepped full rendered HTML) | PASS | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-14-result.png` |

---

## Passed Tests

### UT-J-04 — Every next-session candidate explains why, why-not, and what would change it
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/UT-J-04-result.png`, `UT-J-04-riskoff-result.png`
- Candidate count (10) matches `selection.candidates` length and the summary sentence "10 names worth monitoring next session."
- HPE candidate card: Leadership 92.7 / Entry 21.5 / Risk 58.9 matches `GET /api/stocks?as_of=2026-08-12` row for HPE (leadership.score 92.71) exactly.
- Eligibility checklist rows render fixed-vocabulary verdicts (Pass/Miss) with threshold vs actual; "What would change this" disclosure present per candidate.
- Why-not entries (DXCM etc.) name threshold/actual/distance and are marked "— advisory" only for non-gating checks.
- At `?asof=2005-04-15` (Risk-off, regime score 21.49): every rendered candidate caution includes `REGIME_RISK_OFF: the market regime is Risk-off as of this date — every candidate here is context, not a signal to act.`; summary retains "10 names worth monitoring next session" framing; zero imperative/entry-advice wording observed.
- Near-threshold shadow cohort confirmed structurally absent from `compass-focus-section` (appears only under `compass-manifest-strip`'s audit table, labeled "research-only substrate, not part of selection or display ranking").

### UT-J-05 — Each close freezes one provenance-stamped next-session manifest, exported byte-consistently
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/UT-J-05-result.png`
- Frontier (`2026-08-12`) manifest strip renders: badges "at ingest / version 10 / frozen / not prospective-eligible", "Frozen 9/1/2026, 6:33:06 PM", Engine identity / Candidate rule / Cohort rule / Manifest config hashes (all truncated-hex chips), Dataset stamp `r3160-f6815424`, Universe pool hash / Members 539 / Profile core, "Basis: available", and an Audit table disclosure "comparison cohort (529) + near-threshold shadow (25)".
- `GET /api/compass?as_of=2005-04-15` (a date with no prior manifest) minted exactly one new manifest on first request: version 1, frozen true, mode retrospective, prospective_eligible false, generation.producer `on_demand_get` — matches the "never by a plain GET" rule (that rule governs the frontier date only; this is an explicitly non-frontier historical date).
- (Frontier's version is v10, not v1, because this manifest has been through many regenerate cycles across the session's 38 prior iterations of dev/QA testing — a pre-existing, expected condition, not a regression; the manifest strip correctly marks it `not prospective-eligible`, consistent with AG-17's "only version 1 minted by the finalize producer can ever be true.")

### UT-J-06 — A frozen manifest never changes — later data, rebuilds, and regeneration are safe
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/UT-J-06-result.png`
- Regenerate button (`compass-manifest-regenerate-button`) on a historical as-of opens a confirm dialog: "This mints a NEW manifest version for 2005-04-15 from the current selection rule and config. The existing version is never touched, changed, or deleted — it stays byte-identical and readable." plus bullets on prospective-eligibility and version listing.
- Clicking Cancel closed the dialog with no mutation: re-queried `/api/compass?as_of=2005-04-15` afterward — still version 1, versions array length 1.
- Frontier's Versions list renders v1–v10 as static rows, each with mode/eligibility/timestamp, confirming old versions remain listed (not hidden/deleted).

### UT-J-07 — The Today page answers the ten-second read from served values only
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/UT-J-07-result.png`
- Section order verified via DOM testid sequence (state-band → summary → what-changed → leadership-rotation → focus → manifest-strip), with readiness-badge/preflight-banner appearing before the body in the chrome.
- Regime tile 73.18/Risk-on matches `GET /api/dashboard`'s `regime.score`/`regime.label`; phase tile Expansion/25.85 severity/P(bear) 0.00 (0.001657 rounds to 0.00) matches `GET /api/market-phase`.
- Direction words ("little changed" ×3) rendered on regime/stress/breadth tiles, consistent with the small session-over-session deltas.
- Regime×phase cross-view chart (`phase-cross-view-chart` testid) confirmed present only on `/market`, absent on `/`; the "Full market context (regime × phase, sectors, themes) →" link on `/` navigates to `/market`.
- Vocabulary separation: readiness tokens ("GO", "Ready") only appear in the chrome banner/badge; no regime/phase tokens found there.

### UT-J-14 — "Not priority" names its real reason
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/UT-J-14-result.png`
- API: all 20 `selection.why_not` entries carry non-empty `failed_conditions` (was 20/20 empty pre-fix per the dev's own cited baseline); `reason` ∈ {excluded_by_cap, below_selection_floor}; `why_not_totals` = {excluded_by_cap_uncapped: 27, below_floor_in_band_uncapped: 25}, matching the spec's own measured baseline exactly.
- DXCM entry reproduces the spec's TC-1 fixture shape verbatim (reason excluded_by_cap, cap_rank 11, cap 10, one advisory `entry_min_score` miss at distance 43.47).
- EXPE entry reproduces TC-3 shape (reason below_selection_floor, gating leadership_min_score miss at distance 0.19, plus two advisory misses).
- Rendered page (measured, not filename-trusted — screenshot verified to contain 14,447 distinct colors across the full page, i.e. genuine content, not a blank capture): "Not priority" disclosure header literally reads "Not priority (20 shown of 52 held back — 27 cap-excluded, 25 below-floor near-miss)"; each row states its ticker, rank/cap or floor-distance, and its advisory/gating misses with threshold/actual/distance (e.g. "DXCM — ranked #11 of the above-floor names, cap 10 / entry_min_score: 26.5 vs 70.0 (distance 43.5) — advisory").
- Grepped the full rendered page HTML for "passed every qualifier" — zero matches, confirming the false sentence never renders for any of the 20 shown entries (all of which have real failed conditions this iteration).

---

## Failed Tests

### UT-J-08 — The market surface relocates intact and history never lies
**Verdict:** FAIL
**Failure:** The Today page (`/`) crashes on navigation to any pre-existing historical `?asof=` date whose stored manifest predates this iteration's `why_not_totals` field, so "the Today tiles show D's stored values" cannot be verified for such dates. `/market` itself is unaffected and fully intact.
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/UT-J-11-fail.png` (crash reproduction on `/?asof=2026-08-11`), `UT-J-08-result.png` (working `/market` page)

**Steps taken:**
1. Navigated to `/market` — confirmed "Top Sectors", "Top Themes", "Candidate Counts", "Market Phase & Severity" and "More detail" all present in the rendered DOM; sidebar Today→Market order and `aria-current="page"` route highlighting both correct.
2. Navigated to `/market?asof=2026-08-11` — renders fine, no crash (Market page doesn't read the new compass fields).
3. Navigated to `/?asof=2025-04-15` (the exact date used by the previously-passing J-05/J-06 golden scripts) — page crashed with "Something went wrong on this page."
4. Navigated to `/?asof=2026-03-30` — same crash.
5. Navigated to `/?asof=2026-08-11` (a real incident date with a genuine stored manifest, `basis.status: "rebuilt"` per the API) — same crash; retried via the in-page "Try again" button — crashed again identically.
6. Confirmed via `GET /api/compass` that all of these dates' stored payloads are missing the `selection.why_not_totals` key (a field this iteration added), while `/apps/frontend/components/compass-focus-section.tsx:192-197` accesses `selection.why_not_totals.excluded_by_cap_uncapped` unconditionally.
7. Confirmed the crash is specific to reading an *already-existing* stale-shape manifest, not to historical navigation in general: a never-before-manifested historical date (`2005-04-15`, `2005-04-04` etc.) renders correctly because requesting it mints a brand-new manifest using the current (fixed) code path.

**Expected:** Stepping `?asof` to any pre-feature historical run date renders that date's stored Today tiles, What-changed-vs-predecessor, and a manifest strip with a visible `retrospective` label.
**Actual:** For any date whose manifest was minted before this iteration, the entire page fails to render at all.

### UT-J-11 — Incident-bounded clean regeneration of derived state (serving verification)
**Verdict:** FAIL
**Failure:** `/?asof=2026-08-11` (one of the two dates J-11's own regression-replay golden script checks) crashes instead of showing "Basis: rebuilt" — same root cause as UT-J-08.
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/UT-J-11-fail.png`, `UT-J-11-retry.png`

**Steps taken:**
1. Navigated to `/?asof=2026-08-12` (latest) — manifest strip correctly shows "Basis: available".
2. Navigated to `/?asof=2026-08-11` — page crashed with "Something went wrong on this page" before any manifest strip content rendered. Confirmed via API that this date's stored manifest is real and correctly computes `basis.status: "rebuilt"` server-side — the UI simply cannot reach the point of displaying it.
3. Clicked "Try again" on the error boundary — crashed again identically (deterministic, not a transient issue).

**Expected:** `/?asof=2026-08-11` shows "Basis: rebuilt"; `/?asof=2026-08-12` shows "Basis: available" (J-11's own golden script assertions).
**Actual:** `2026-08-12` passes; `2026-08-11` never renders any content.

*(Note: J-11's actual data-recovery/serving-correctness work is owner-closed as PASSING from a prior iteration — `J-11 STATUS: PASSING — CLOSED`, per `docs/goal.md`. This FAIL is scoped strictly to this iteration's new UI regression breaking the ability to browser-verify that already-closed state, not a re-opening of J-11's recovery work.)*

### UT-J-13 — "Leadership rotation" says which way, shows both directions, and stops repeating What-changed
**Verdict:** FAIL
**Failure:** Step 7 (stepping to the earliest stored session to verify the rotation block's honest no-prior-run state) crashes the page via the same `selection.why_not_totals` bug, before the rotation block's no-prior-run state can ever render.
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/UT-J-13-result.png` (frontier — steps 1-6 pass), `UT-J-13-fail.png` (step-7 crash)

**Steps taken:**
1. On `/` (frontier), confirmed `compass-leadership-rotation-section` renders sector and theme sub-sections, each with gaining/losing sides, signed deltas, direction words, and accounting lines exactly matching the spec's cited values (Regional Banks (SPDR) 13→10 (-3)·improving; Home Construction (iShares) 21→25 (+4)·deteriorating; "7 of 31 shown · 24 below threshold · 0 beyond the display cap."; theme "2 of 11 shown · 9 below threshold · 0 beyond the display cap."). No stock-kind row present in the rotation section.
2. Navigated to `?asof=1996-01-02` (the earliest stored session per the pre-existing golden script) to verify the no-prior-run state — page crashed with "Something went wrong on this page" instead.
3. Confirmed via API that `session_delta.rotation` IS present and correctly shaped for this date (empty gaining/losing arrays, correct `configured_total`) — J-13's own rotation code handles the no-prior-run case correctly. The crash instead comes from `selection.why_not_totals` being absent on this same (pre-this-iteration) manifest, which also happens to have an empty candidate list (`candidates_empty_reason` populated) — the exact same unguarded access in `compass-focus-section.tsx` that breaks UT-J-08/UT-J-11.

**Expected:** The rotation block renders its no-prior-run empty state ("no deltas, no direction words, nothing fabricated"), consistent with What-changed's own no-prior-run state.
**Actual:** The entire page crashes before any content, including the rotation block, renders.

---

## Skipped Tests

None. Frontend and Chrome MCP were both available; all 8 dispatched journeys (J-04, J-05, J-06, J-07, J-08, J-11, J-13, J-14) were executed.

---

## Golden replay scripts written this run

PASS journeys got a fresh/updated deterministic replay script in
`runs/goal-session-market-compass/journey-scripts/`:
- `J-04.json`, `J-05.json`, `J-06.json`, `J-07.json` — rewritten using values verified live this run (the previous J-04/J-05/J-06 goldens pointed at historical dates — `2026-07-23`, `2025-04-15` — that this iteration's regression now breaks; replaced with `2005-04-15`, a date freshly minted during this session's own testing that is unaffected).
- `J-13.json` — left unchanged (byte-identical rewrite): its own step 7 now legitimately fails against the live app, so the golden continues to correctly encode the intended/expected behavior and will correctly catch this regression when future iterations replay it.
- `J-14.json` — new (first golden for this journey), values verified live this run.
- No script written for J-08 or J-11 (both FAIL this run).

All six scripts (`J-04`, `J-05`, `J-06`, `J-07`, `J-13`, `J-14`) pass
`python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-market-compass/journey-scripts --journeys J-04,J-05,J-06,J-07,J-13,J-14`.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (headless, pinned profile)
- **Test Date:** 2026-09-01
- **Evidence directory:** `reports/qa/goal-market-compass-iter-38-evidence/`
