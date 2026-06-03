# goal-i_can_see_the_wealthy_future_forever-iter-15 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-15
**Date:** 2026-06-03
**Frontend Present:** yes

## Phase Goal

Make synthesis journey **J-31** navigable end-to-end: from Factor/Setup-Pattern Lab evidence on `/research`, click a new cross-link to land on `/stocks` **pre-filtered** to the names expressing that subject, then open one on Stock Detail — all reading canonical stored values, frontend-only (deep-linkable filter URLs + one lab→leaderboard `Link`), with **no backend change, no second date state, no recompute/fabrication**.

## Test Cases

### TC-01 — Lab → leaderboard cross-link renders for a resolved subject
**Type:** browser
**Preconditions:** Frontend on :3000, backend reachable, a date resolved in the global as-of provider.

**Steps:**
1. Navigate to `http://localhost:3000/research`.
2. Scroll to the **Setup & Pattern Lab** (`EventStudyLab`); select a data-rich subject (e.g. pattern `pullback_to_rising_dma` or setup `Breakout-watch`).
3. Confirm the event study renders (distribution / expectancy / MAE-MFE / best-exit-horizon / by-regime / by-sector with n + honest NA).
4. Locate the cross-link **"View the names expressing this on the leaderboard →"**.

**Expected outcome:** The cross-link is present and points at the correct filter for the resolved `subject.kind`: pattern → `/stocks?pattern=<key>__only`; setup → `/stocks?setup=<key>`.
**Pass criteria:** Link visible; `href` exactly matches the kind-derived encoding (URL-encoded key); link renders even for a low-sample NA subject.

---

### TC-02 — Full J-31 travel: lab evidence → cross-link → pre-filtered leaderboard → Stock Detail
**Type:** browser
**Preconditions:** As TC-01; choose a subject with ≥1 expressing name at the current as-of (e.g. `pullback_to_rising_dma` ~9 names, or setup `Breakout-watch`).

**Steps:**
1. On `/research` Factor Lab, read a factor's decile mean fwd return + downside risk-adjusted column + rank-IC + n (J-25/J-30) and its by-regime split + n (J-27).
2. On the Setup & Pattern Lab, read the aligned subject's event study (J-29).
3. Click **"View the names expressing this on the leaderboard →"** (in-app nav, no hard reload).
4. On `/stocks`, DOM-assert the active filter control reflects the subject (e.g. Pattern = "Pullback only" / Setup = "Breakout-watch") and the `visible / total` count is the narrowed subset.
5. Click a row → `/stocks/[ticker]`; confirm the pattern badge (pivot/invalidation) or setup status + the three A–E scores + invalidation render.

**Expected outcome:** Each step lands correctly; leaderboard arrives pre-filtered; a real flagged row opens on detail showing badge + 3 scores + invalidation on the daily chart.
**Pass criteria:** Active filter DOM-asserted; narrowed `visible < total` and each visible row genuinely expresses the subject; detail scores byte-consistent with that leaderboard row (J-06); full travel captured (not isolated renders) with distinct screenshots.

---

### TC-03 — Shareable deep-link opens pre-filtered (direct nav)
**Type:** browser
**Preconditions:** Frontend running.

**Steps:**
1. Open `http://localhost:3000/stocks?pattern=pullback_to_rising_dma__only` in a fresh in-app nav.
2. Observe the Pattern filter control and row count.
3. Repeat with `http://localhost:3000/stocks?setup=Breakout-watch`.
4. Repeat with `http://localhost:3000/stocks?sector=Energy`.

**Expected outcome:** On each load the corresponding filter is pre-applied from the URL and rows are narrowed accordingly.
**Pass criteria:** Filter control reflects the URL param on first paint; visible rows match the filter; no crash; no console error about missing Suspense.

---

### TC-04 — Filter change reflects back into the URL (no refetch)
**Type:** browser
**Preconditions:** On `/stocks` with no filter params.

**Steps:**
1. Open DevTools Network tab; note the single `GET /api/stocks` fetch on load.
2. Change the Pattern (or Setup/Sector) dropdown to a non-`__all__` value.
3. Inspect the address bar and the Network tab.

**Expected outcome:** URL updates (shallow `router.replace`, no scroll jump) to encode the chosen filter; `__all__` values are omitted from the query string; NO new `/api/stocks` fetch fires.
**Pass criteria:** URL query reflects filter verbatim (existing encodings); zero additional `/api/stocks` network requests after the filter change (warm load J-15 unchanged); page does not scroll-jump.

---

### TC-05 — J-18: exactly one date selector; no `as_of` query param (PRINCIPAL RISK)
**Type:** browser
**Preconditions:** On `/stocks` deep-linked with a filter (e.g. `?pattern=pullback_to_rising_dma__only`).

**Steps:**
1. Capture a screenshot and record the active filter + URL.
2. Toggle the global as-of switcher to a different date.
3. Capture a second (distinct) screenshot; inspect the URL and the Network requests.

**Expected outcome:** Page re-points by DATE; the filter param stays intact in the URL; no `as_of`/date query param is ever added to the leaderboard URL or to a leaderboard fetch; exactly one date control exists on the page.
**Pass criteria:** Two distinct screenshots show a date change with filter preserved; no `?as_of`/date param appears in the URL or any `/api/stocks` request; only the global as-of control is present (no second date picker). Grounded on distinct shots + a network/DOM assertion (not a single pair).

---

### TC-06 — Honesty / edge cases: bad param fallback & zero-match empty-state
**Type:** browser
**Preconditions:** Frontend running.

**Steps:**
1. Open `http://localhost:3000/stocks?pattern=not_a_real_pattern__only`.
2. Open `http://localhost:3000/stocks?pattern=`.
3. Open a valid pattern deep-link known to match zero rows at the current as-of.

**Expected outcome:** Unrecognized/empty `pattern` (mode or key not in the `PATTERNS` registry) falls back to `__all__` with no crash; a valid filter matching zero rows shows the existing honest empty-state — never a fabricated row.
**Pass criteria:** No crash/console error; invalid param → unfiltered (`__all__`) view; zero-match → honest empty-state, no synthesized rows; low-sample lab cells along the travel stay NA + n.

---

### TC-07 — Frontend build + typecheck pass (Suspense boundary)
**Type:** artifact
**Preconditions:** Repo checked out at the iter-15 diff.

**Steps:**
1. Run `cd apps/frontend && npm run build`.

**Expected outcome:** Production build compiles and typechecks; the `useSearchParams` usage is wrapped in a `<Suspense>` boundary so the App-Router build does not error.
**Pass criteria:** Build exits 0; no "useSearchParams() should be wrapped in a suspense boundary" error; no type errors.

---

### TC-08 — Source-level anti-goal / scope guard
**Type:** artifact
**Preconditions:** iter-15 diff available.

**Steps:**
1. Inspect the diff: confirm only `apps/frontend/app/stocks/page.tsx` and `apps/frontend/app/research/page.tsx` (+ optional in-file `<Suspense>` wrapper / optional tiny `lib/` encode helper) changed.
2. Grep the changed files for `as_of`, a new date query param, `useState`-driven second date, any new `fetch`/endpoint, and any hard-coded subject↔filter table.
3. Confirm `useAsOf()` remains the sole date source and the `fetchStocks` effect dependency array stays `[asOf]` only.

**Expected outcome:** No backend file/endpoint/config/computation touched; no `as_of`/date query param; cross-link mapping derived from payload `kind` + `PATTERNS` registry (no hard-coded table); fetch effect keyed to `[asOf]` only.
**Pass criteria:** Diff scoped to the two frontend files (± Suspense wrapper/helper); zero new endpoints/computations; zero `as_of`/date params; mapping is config/kind-driven.

---

### TC-09 — Backend suite stays green (no incidental breakage)
**Type:** artifact
**Preconditions:** No backend change expected this iter.

**Steps:**
1. Run the backend suite once: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (full suite ~14 min — run ONCE, do not parallelize).

**Expected outcome:** Suite passes (trivially green — no backend change).
**Pass criteria:** pytest exits 0 with no new failures vs the prior iteration baseline.

---

### TC-10 — Required-still-passing journeys remain green (regression sweep)
**Type:** browser
**Preconditions:** Frontend running; TC-02..TC-05 captured.

**Steps:**
1. Confirm J-02 — the `/stocks` dropdown filters still work and now sync to the URL.
2. Confirm J-15 — warm load: navigating to `/stocks` fires no extra fetch beyond the single as-of-keyed call.
3. Confirm J-06 — a detail page's three A–E scores match the leaderboard row exactly.
4. Confirm J-25/J-27/J-29/J-30 — the `/research` labs still render their analytics; the cross-link is additive (lab figures unchanged).

**Expected outcome:** All listed journeys behave as before; the only additions are the cross-link and URL-backed filters.
**Pass criteria:** J-02 filters operate + reflect to URL; J-15 no extra fetch; J-06 scores byte-identical across views; labs render unchanged with the additive link present.

---

## Summary

Total test cases: **10**
- Browser tests: **6** (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-10) — note TC-10 is a browser regression sweep
- Artifact checks: **4** (TC-07 build, TC-08 source scope, TC-09 backend suite)

Counts by type: Browser = 6 (TC-01–06) + 1 regression sweep (TC-10) = 7 browser; Artifact = 3 (TC-07, TC-08, TC-09). API tests = 0 (no backend/endpoint change this iteration — J-31 reads existing endpoints only).

**Defining test:** TC-02 (full J-31 cross-page travel). **Principal-risk test:** TC-05 (J-18 — exactly one date selector, no `as_of` param).
