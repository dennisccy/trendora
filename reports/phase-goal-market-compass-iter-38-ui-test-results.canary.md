# Goal iter-38 — UI Test Results (regression check: J-02, J-03)

**Phase:** goal-market-compass-iter-38
**Date:** 2026-09-01
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: a required-still-passing journey (J-02) regressed to a hard page crash on a step
     required by its own Acceptance criteria; J-03 regressed the same way. -->

**Overall:** 0/2 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | regression | P1 | Steps 1-5 all render correctly, including the explicit no-prior-run state at the earliest stored session | Steps 1-4 verified correct (header, ordering, thresholds, suppressed-count, spot-checked sector rank + stock bucket move). Step 5 (navigate to the earliest stored run) crashes the entire page with a client-side TypeError instead of rendering the no-prior-run state | FAIL | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-02-fail.png` |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | regression | P1 | Steps 1-2 render correctly on the latest as-of; step 6 (retrospective view) shows the retrospective stamp | Steps 1-2 verified correct (summary sentences render, "Show cited facts" discloses template ids + facts, spot-checked regime_score and severity byte-match `/api/dashboard` and `/api/market-phase`). Step 6 (retrospective as-of, e.g. `?asof=2025-04-15`) crashes the entire page with the same TypeError instead of showing the summary + retrospective stamp | FAIL | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-03-fail.png` |

---

## Passed Tests

None — both tests reached a hard failure on a step required by their own Acceptance criteria.

Partial verification recorded for the record (not sufficient for a PASS verdict):

- **UT-J-02 steps 1-4** (latest as-of `2026-08-12`): What-changed header reads "vs 2026-08-11 (1 day ago)", matching `GET /api/runs` (prior run 2026-08-11, gap 1 day). Visible change entries ordered sector → theme → stock (market/breadth had no above-threshold entries this pair), each linking with `?asof=2026-08-12`. "Suppressed moves (36)" disclosure expanded to exactly 36 listed entries, each of the form `actual < threshold`. Spot-checked "Home Construction (iShares)" sector rank 21→25 against `GET /api/sectors?as_of=2026-08-11` (rank 21) and `?as_of=2026-08-12` (rank 25) — byte match. Spot-checked SMCI leadership bucket E→D against `GET /api/stocks/SMCI` at both dates (score 34.18→62.51, bucket E→D) — byte match.
- **UT-J-03 steps 1-2** (latest as-of `2026-08-12`): Summary card renders all four sentences (state/direction/breadth/focus_count) exactly as served. "Show cited facts" discloses each sentence's `template_id` and facts. Spot-checked `regime_score` (73.18) against `GET /api/dashboard?as_of=2026-08-12` and `severity` (25.85) against `GET /api/market-phase?as_of=2026-08-12` — both byte match.

---

## Failed Tests

### UT-J-02 — "What changed" reports meaningful session-over-session deltas with honest empties
**Verdict:** FAIL
**Failure:** Step 5 ("Step the as-of switcher to the earliest stored run; assert the explicit no-prior-run state renders") instead produces a full client-side crash. Navigating to `http://localhost:3255/?asof=1996-02-01` (a stored run per `GET /api/runs`, and the same date this journey's own committed golden script `runs/goal-session-market-compass/journey-scripts/J-02.json` uses) renders only the Next.js error boundary: "Something went wrong on this page — An unexpected error stopped this page from rendering." No What-changed card, no no-prior-run sentence, nothing else on the page renders either.

**Root cause (confirmed):** `GET /api/compass?as_of=1996-02-01` returns a `selection` object with keys `['candidates', 'why_not', 'disposition_tally', 'candidates_empty_reason']` — no `why_not_totals` key, because this manifest was minted before iter-38 added that field and `GET /api/compass` serves the immutable STORED manifest row verbatim (by design, AG-12) rather than recomputing it. `apps/frontend/components/compass-focus-section.tsx:194-197` unconditionally reads `selection.why_not_totals.excluded_by_cap_uncapped` / `.below_floor_in_band_uncapped` in the "Not priority" `Disclosure` summary string, with no guard for a manifest that predates this iteration's schema addition. Browser console:
```
TypeError: Cannot read properties of undefined (reading 'excluded_by_cap_uncapped')
    at M (http://localhost:3255/_next/static/chunks/app/page-fdc656068190ecb4.js:1:16378)
```
Because AG-12 makes every pre-iter-38 manifest permanently immutable, this is not a one-time transient state — every historical as-of whose manifest predates iter-38 will crash the whole Today page indefinitely, not just the "Not priority" card.

**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/UT-J-02-fail.png` (1683×1260, 68434 bytes, 5294 distinct colors — measured with `PIL.Image.getcolors()`, confirming a real rendered error page, not a blank capture)

**Steps taken:**
1. Navigated to `/` (as-of 2026-08-12) — verified header/ordering/thresholds/suppressed-count/spot-checks (all correct, see Passed Tests above).
2. Navigated to `/?asof=1996-02-01` (earliest-session golden URL) — page rendered only the error boundary.
3. Read browser console via `get_console_messages` — captured the exact `TypeError` and stack trace above.
4. Cross-checked `GET /api/compass?as_of=1996-02-01` directly — confirmed `selection.why_not_totals` is absent from the stored payload.
5. Located the unguarded access at `apps/frontend/components/compass-focus-section.tsx:194-197`.

**Expected:** The page renders normally with the What-changed card showing "This is the earliest stored session — there is no prior session to compare against" (or equivalent honest no-prior-run sentence), consistent with `narrative.sentences[1].text` = "This is the earliest stored session — no prior-session comparison is available." served by the API.
**Actual:** Entire page crashes; nothing renders except the generic Next.js error boundary.

---

### UT-J-03 — The plain-English summary is deterministic, cited, and never invents a cause
**Verdict:** FAIL
**Failure:** Step 6 ("On a retrospective compass view (any pre-frontier historical date), assert the summary carries the visible retrospective stamp") instead produces the identical full-page crash. Navigating to `http://localhost:3255/?asof=2025-04-15` (the date this journey's own committed golden script `runs/goal-session-market-compass/journey-scripts/J-03.json` uses, and confirmed a `frozen: true`, `version: 2` stored manifest via `GET /api/compass?as_of=2025-04-15`) renders only "Something went wrong on this page." No summary card, no retrospective stamp, nothing else renders. Step 5 (no-comparison sentence variant at the earliest stored run) is blocked by the exact same crash, since the earliest run is also a pre-iter-38 stored manifest.

**Root cause:** Identical to UT-J-02 — `GET /api/compass?as_of=2025-04-15` returns `selection` without a `why_not_totals` key (pre-iter-38 stored manifest, `frozen: true`), and `compass-focus-section.tsx:194-197`'s unguarded read throws, which crashes the whole page via React's error boundary — including the summary card this journey needs to inspect.

**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/UT-J-03-fail.png` (1683×1260, 68478 bytes, 5249 distinct colors — measured with `PIL.Image.getcolors()`)

**Steps taken:**
1. Navigated to `/` (as-of 2026-08-12) — verified summary sentences, "Show cited facts" disclosure with template ids + facts, and spot-checked `regime_score`/`severity` against `/api/dashboard` and `/api/market-phase` (all correct, see Passed Tests above).
2. Navigated to `/?asof=2025-04-15` (retrospective golden URL) — page rendered only the error boundary.
3. Confirmed via `GET /api/compass?as_of=2025-04-15` that the served `selection` object lacks `why_not_totals` (pre-iter-38 frozen manifest, version 2).

**Expected:** The page renders normally with the summary card and a visible retrospective stamp naming that it was reconstructed under the current selection rule/config.
**Actual:** Entire page crashes; nothing renders except the generic Next.js error boundary.

---

## Skipped Tests

None.

---

## Regression note for the dev/review chain

This is a single root cause breaking both dispatched journeys (and, by the same mechanism, almost certainly J-06/J-07/J-08's historical-view paths and any other surface reading `selection.why_not_totals` against a pre-iter-38 manifest — not verified here, out of this dispatch's scope of J-02/J-03 only). Fix belongs in `apps/frontend/components/compass-focus-section.tsx` around line 194: guard the "Not priority" summary string against a `selection.why_not_totals` that is `undefined`/`null` (e.g. fall back to `selection.why_not.length` alone, or omit the two-count breakdown, for a manifest minted before this field existed) rather than crashing the whole page. This does not require touching the backend or any stored manifest (AG-12 stays intact) — it is a frontend defensive-rendering fix for reading an additive field that legitimately does not exist on older, immutable rows.

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (headless, pinned profile)
- **Test Date:** 2026-09-01
- **Evidence directory:** `reports/qa/goal-market-compass-iter-38-evidence/`
