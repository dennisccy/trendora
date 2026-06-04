# goal-i_can_see_the_wealthy_future_forever-iter-19 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-19
**Date:** 2026-06-04
**Frontend Present:** yes

## Phase Goal

Add an **All-history ⟷ As-of-date** analysis-mode toggle to the `/research` labs that filters every Factor-Lab / event-study figure to only snapshots dated ≤ the existing global as-of date — a read-only point-in-time filter driven entirely by the single global switcher, introducing **no second date state** (J-18 is the principal anti-goal risk).

## Test Cases

### TC-01 — All-history byte-identical regression guard (`as_of=None == as_of=latest == current`)
**Type:** api (backend unit/integration)
**Preconditions:** Backend DB seeded; `apps/backend/tests/test_research.py` runnable.
**Steps:**
1. For each of `compute_factor_lab`, `compute_factor_combination`, `compute_event_study`, call with no `as_of`.
2. Call again with `as_of=<latest snapshot date>`.
3. Compare full result payloads against each other and against the pre-iter-19 all-history output.
**Expected outcome:** All three forms produce identical results.
**Pass criteria:** `as_of=None`, `as_of=latest`, and the prior all-history result are **byte-identical** for all three functions; `as_of=None` adds no SQL clause.

### TC-02 — As-of scoping pools only snapshots ≤ D (no future-run leak)
**Type:** api (backend)
**Preconditions:** Fixture with `ScannerRun` rows on multiple `asof_date`s.
**Steps:**
1. Call each lab function with an **early** `as_of=D`.
2. Compare `n_total` / per-cell `n` against the all-history call.
3. Confirm no `ForwardReturn` whose run has `ScannerRun.asof_date > D` contributes (assert via fixture or by comparing pooled counts across two cutoffs).
**Expected outcome:** Early cutoff yields a strictly smaller pool; no future run leaks in.
**Pass criteria:** Scoped `n_total`/cell `n` strictly less than all-history; cutoff reads canonical `ScannerRun.asof_date` (not denormalized `ForwardReturn.asof_date`); zero contribution from runs dated > D.

### TC-03 — Early-cutoff low-sample → NA + n (never fabricated)
**Type:** api (backend)
**Preconditions:** Early `as_of` producing thin samples.
**Steps:**
1. Call each lab with an early `as_of` so decile/cohort/regime cells fall below `walk_forward.min_sample`.
2. Inspect low-sample cells.
**Expected outcome:** Thin cells report NA with their `n`, never a fabricated value.
**Pass criteria:** Cells with `n < min_sample` show NA + `n`; survivorship/universe-relative label still present; no fabricated rows.

### TC-04 — As-of so early a lab has zero contributing snapshots → honest empty
**Type:** api (backend)
**Preconditions:** `as_of` before any snapshot for a lab.
**Steps:**
1. Call the lab function with that very early `as_of`.
**Expected outcome:** Honest empty/NA payload with `n=0`.
**Pass criteria:** Returns `n=0` empty/NA payload; no fabricated row; no 500.

### TC-05 — Endpoint `as_of` validation (422 / 400 / scoped 200)
**Type:** api
**Preconditions:** Backend on `http://localhost:8000`; valid historical date and latest date known.
**Steps:**
1. `curl "/research/factor-lab?...&as_of=not-a-date"` → expect 422.
2. `curl "/research/factor-lab?...&as_of=<future date > latest>"` → expect 400.
3. `curl "/research/factor-lab?...&as_of=<valid historical date>"` → expect 200 with scoped payload.
4. Repeat for `/research/factor-combination` and `/research/event-study`.
**Expected outcome:** Unparseable → 422, future → 400, valid historical → scoped 200 echoing resolved `asof_date`.
**Pass criteria:** Status codes match per route; validation reuses `resolved_date`/established snapshot-serving convention (not hand-rolled); 200 payload echoes the **resolved** `asof_date`.

### TC-06 — Payload echoes resolved cutoff; null/absent in all-history
**Type:** api
**Preconditions:** Backend running.
**Steps:**
1. Call each endpoint with no `as_of`; inspect `asof_date`.
2. Call each with `?as_of=D`; inspect `asof_date`.
**Expected outcome:** All-history → `asof_date` null/absent; scoped → resolved cutoff echoed.
**Pass criteria:** `asof_date` null/absent when unscoped; equals resolved cutoff when scoped; no other payload-shape change.

### TC-07 — Three `*_no_date_control_present` contract tests updated to J-32 truth
**Type:** api (backend, intentional acceptance update)
**Preconditions:** `apps/backend/tests/test_api_research.py`.
**Steps:**
1. Confirm `test_factor_lab_no_date_control_present`, `test_factor_combination_no_date_control_present`, `test_event_study_no_date_control_present`, and the module docstring (line 8) are **updated** (not deleted) to the new contract.
**Expected outcome:** Tests assert the new truth: endpoint accepts the single global `as_of` as optional scoping cutoff; default payload `asof_date` null/absent; **no second date param**.
**Pass criteria:** All three updated tests pass and encode the new contract; none silently deleted (iter-2 lesson).

### TC-08 — Read-only keystone: scoped path recomputes nothing
**Type:** api (backend)
**Preconditions:** Patch-to-raise test infrastructure exists.
**Steps:**
1. Extend the patch-to-raise test so the **scoped** (`as_of=D`) path is exercised with recompute functions patched to raise.
2. Grep `research.py` for `run_scan`/`score_stocks`/`backfill*`/`forward_return`/`detect_*`/`score_regime`.
**Expected outcome:** Scoped path serves stored values only; forbidden calls appear only in docstrings.
**Pass criteria:** Patched-to-raise test passes for scoped path; forbidden-call grep hits only docstrings/comments in `research.py`.

### TC-09 — Full backend suite green
**Type:** api (backend suite gate)
**Preconditions:** Run pytest **once** (~14-18 min — MEMORY `backend-test-suite-runtime`; do not run two pytest invocations concurrently).
**Steps:**
1. Run the project backend test command, capture full output.
**Expected outcome:** Suite passes.
**Pass criteria:** Exit code 0; no new failures; J-06/J-07 unaffected.

### TC-10 — J-32 end-to-end: As-of mode re-points figures with reduced n
**Type:** browser (Chrome MCP)
**Preconditions:** Clean hydrated build — confirm `GET /_next/static/chunks/main-app.js → 200` and health badge clears (MEMORY `browser-qa-dead-shell-next-cache`); do NOT `npm run build` against live dev `.next`. Frontend on `http://localhost:3000`.
**Steps:**
1. Open `/research` — confirm default **All history**; capture baseline decile/rank-IC + a combination cohort + an event-study table with their `n` (distinct sha256 screenshots + DOM/network assertions — iter-6 lesson).
2. Toggle to **As of date** (button group — click directly); set the global `<select>` to one of the **earliest** dates (bottom of the descending list — thin by date not horizon, iter-11) via native-setter + bubbling change event (MEMORY `react-controlled-select-needs-native-setter`).
3. DOM-assert each lab's figures change and `n` **drops**; early-date low-sample cells show NA + n.
4. Toggle back to **All history**; DOM-assert full-sample figures and larger `n` return.
**Expected outcome:** As-of mode re-points every figure to the point-in-time window with smaller n + honest NA; All-history restores full sample.
**Pass criteria:** Distinct sha256 screenshots; DOM shows `n` strictly drops in As-of @ early date and returns to full when toggled back; NA at early dates never fabricated; survivorship label persists in both modes.

### TC-11 — J-18 principal anti-goal: exactly one date control, no second date state
**Type:** browser (Chrome MCP) + source
**Preconditions:** `/research` loaded; page source available.
**Steps:**
1. Live: assert exactly **one** date `<select>` on the page and it is a descendant of `<header>`, not `<main>`; confirm no page-local date input/picker.
2. In As-of mode, network-assert the research fetch carries the single global `?as_of=` (expected — MEMORY `j18-asof-on-stocks-fetch-is-correct`).
3. In All-history mode, move the global date and network-assert **no** research refetch / figures unchanged.
4. Source: confirm `/research/page.tsx` sources as-of solely from `useAsOf()` and holds no second date `useState`; each lab effect depends on the resolved `asofCutoff`, not raw `asOf`.
**Expected outcome:** One global date control; mode toggle is a mode, not a date control; `?as_of=` is the transmitted global date, not a second state.
**Pass criteria:** Exactly one date `<select>` (in `<header>`); no page-local date control; All-history mode does not refetch on global-date change (J-15 preserved); source has no second date state.

### TC-12 — Required-still-passing journeys unchanged in default mode
**Type:** browser (Chrome MCP)
**Preconditions:** `/research` and `/synthesis` reachable.
**Steps:**
1. In default All-history mode, verify J-25 (factor lab), J-26 (composite + strict overlap), J-27 (regime split), J-29 (event study), J-30 (volatility family) render their familiar full-sample figures.
2. Confirm J-31 synthesis cross-link/travel intact.
**Expected outcome:** All render unchanged in All-history mode and re-point correctly in As-of mode.
**Pass criteria:** J-25/J-26/J-27/J-29/J-30 figures match pre-iter-19 all-history values; J-31 travel works.

### TC-13 — Frontend build/typecheck clean
**Type:** artifact / build
**Preconditions:** `apps/frontend`.
**Steps:**
1. Run `npm run build`.
**Expected outcome:** Builds with no type errors.
**Pass criteria:** Build exits 0; no TS errors; `lib/api.ts` `asof` arg + `asof_date?` response fields typecheck.

### TC-14 — UI-visibility artifacts present
**Type:** artifact
**Preconditions:** Pipeline ran.
**Steps:**
1. Verify the 6 artifacts exist: implementation-summary, user-visible-changes, ui-surface-map, ui-test-plan, ui-test-results, what-to-click; plus dev handoff `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-19-dev.md`.
**Expected outcome:** All artifacts present and non-vague.
**Pass criteria:** Each file exists with substantive content.

### TC-15 — Blueprint annotated, no re-approval marker
**Type:** artifact
**Preconditions:** `runs/goal-session-i_can_see_the_wealthy_future_forever/state/blueprint.md`.
**Steps:**
1. Confirm iter-19 "NO skeleton change" note added and the three lab Data-Contract rows annotated with optional `as_of` cutoff.
2. Confirm **no** `blueprint.reapproval-requested` marker created.
**Expected outcome:** Additive annotation only; no re-approval requested.
**Pass criteria:** Blueprint shows iter-19 note + 3 annotated rows; no reapproval marker file present.

### TC-16 — Scoring/snapshot path git-untouched (J-06/J-07 byte-identical, no DB regen)
**Type:** artifact (git verify)
**Preconditions:** Diff available.
**Steps:**
1. `git diff` the out-of-scope files: `scoring.py`, `scanner.py`, `regime.py`, `patterns.py`, `buckets.py`, `forward_testing.py` storage, `snapshot_serving.py`, `asof-provider.tsx`, `stocks/page.tsx`, `backtest/page.tsx`.
**Expected outcome:** No changes to these files; no DB regen.
**Pass criteria:** Listed files unchanged in diff; J-06/J-07 byte-identical.

## Summary

Total test cases: 16
- API / backend tests: 9 (TC-01–TC-09)
- Browser tests: 4 (TC-10, TC-11, TC-12, and TC-11's live portion)
- Artifact checks: 4 (TC-13 build, TC-14, TC-15, TC-16)

Critical gates: TC-01 (all-history byte-identical regression guard), TC-10 (J-32 end-to-end), TC-11 (J-18 principal anti-goal — exactly one date control), TC-09 (full backend suite).
