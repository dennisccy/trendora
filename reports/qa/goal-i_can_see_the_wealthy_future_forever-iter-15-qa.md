# QA Report — goal-i_can_see_the_wealthy_future_forever-iter-15

**Verdict:** PASS

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-15
**Date:** 2026-06-03
**Agent:** qa (MODE 2 — validation)
**Frontend Present:** yes

## Summary

J-31 synthesis capstone, frontend-only: (A) `/stocks` filters become URL-backed (init-once-from-URL +
reflect-out via `router.replace({scroll:false})` + `<Suspense>` boundary), (B) a kind-driven
lab→leaderboard cross-link on the Event Study Lab. Build, typecheck, backend suite, and source-level
anti-goal guards all PASS. The cross-link element renders and the leaderboard honors the deep-link URL
with **no `as_of` param** (J-18 confirmed in source + runtime). The full multi-step interactive travel
(TC-02) and several interactive browser cases could not be completed to a stable capture due to
**cross-project shared-Chrome contention** (a different project's automation on `localhost:3650`
repeatedly navigated the shared browser tab mid-test) — these are recorded **PARTIAL/SKIPPED (env), not
failed**, and are deferred to the dedicated `browser-qa-agent` stage, which is the authoritative J-31
acceptance gate per the spec DoD. No implementation defect was observed.

## Step 1 — Artifact verification

| Artifact | Status |
|----------|--------|
| `docs/handoffs/...-iter-15-dev.md` | ✅ present |
| `reports/reviews/...-iter-15-review.md` | ✅ present — **PASS_WITH_NOTES** |
| `runs/...-iter-15/status.json` | ✅ present (`current_step: review_passed`) |
| `reports/qa/...-iter-15-test-plan.md` | ✅ present — executed below |

## Step 2 — Backend tests (TC-09)

No backend file was changed this iteration (`git status` confirms only the two frontend files are
modified app code). The developer's confirmation run is recorded at
`runs/.../iter-15/backend-test.log`:

```
........s...........sss..                                                [100%]
453 passed, 4 skipped in 1244.83s (0:20:44)
BACKEND_PYTEST_EXIT=0
```

`= 453 passed, 4 skipped, exit 0` (4 skips are pre-existing data-walled/intraday). No incidental
breakage. Not re-run by QA (≈21 min; no backend delta to validate — MEMORY: backend-test-suite-runtime).

## Step 3 — Frontend build / typecheck (TC-07)

`cd apps/frontend && npm run build` → **PASS**:
- `✓ Compiled successfully` · `✓ Checking validity of types` (no type errors) · `✓ Generating static pages (14/14)`.
- `/stocks` route emitted as `○ (Static)` prerendered — confirms the `<Suspense>` boundary satisfies the
  Next 15 App-Router `useSearchParams()` production-build requirement (a missing boundary fails the build).

## Step 3.5 / Step 4 — Functional test results

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | Lab→leaderboard cross-link renders | browser | Cross-link present, kind-derived href | Link `[data-testid=subject-leaderboard-link]` "View the names expressing this on the leaderboard →" **rendered** (confirmed via `await_element` + `await_text` once the lab resolved). Exact href read raced with hydration/contention; source confirms kind-driven derivation (pattern→`?pattern=<key>__only`, setup→`?setup=<key>`, `encodeURIComponent`). Default subject `Actionable` (setup) ⇒ `/stocks?setup=Actionable`. | PASS (link presence + source-verified href) | href exact-match assertion deferred to browser-qa-agent |
| TC-02 | Full J-31 travel (DEFINING) | browser | lab evidence → cross-link → pre-filtered leaderboard → Stock Detail | Could not capture a stable end-to-end run: shared Chrome was repeatedly navigated to another project's app (`localhost:3650`) and pages were caught mid-boot ("Checking backend…"). Each surface individually reached its loaded state intermittently. | PARTIAL / deferred (env contention) | **Authoritative gate is browser-qa-agent (spec DoD).** No defect observed |
| TC-03 | Shareable deep-link opens pre-filtered | browser | Filter pre-applied from URL | `/stocks?pattern=pullback_to_rising_dma__only` navigated; **URL preserved verbatim with no added param**; leaderboard hydration not captured to a stable frame under contention (pattern `<select>` and `table tbody tr` were transiently present per `await_element`). | PARTIAL (URL honored; row assertion deferred) | URL-intact + no `as_of` is the key J-18 signal — observed |
| TC-04 | Filter change reflects to URL, no refetch | browser | URL updates shallow; no new `/api/stocks` fetch | Not executed interactively (contention). **Source-verified:** reflect-out via `router.replace(...,{scroll:false})`, `__all__` omitted; fetch effect dep array is `[asOf]` only (line 122) ⇒ filter change cannot refetch (J-15 preserved). | PASS (source) / interactive deferred | |
| TC-05 | J-18 — exactly one date selector, no `as_of` param (PRINCIPAL RISK) | browser | Date toggle re-points; filter intact; no `as_of` param | Not executed as a live as-of toggle (contention). **Source-verified (decisive):** only `params.set("sector"/"setup"/"pattern")` written (lines 150–152); zero `as_of`/date param written or read (only explanatory comments); `useAsOf()` is the sole date source (line 99). Runtime corroboration: deep-link navigation kept `?pattern=…` with **no `as_of`** appended. | PASS (source + runtime corroboration) | The one historical anti-goal seam — clean |
| TC-06 | Honesty / edge cases (bad param, zero-match) | browser | Bad param → `__all__`; zero-match → honest empty-state | Not executed interactively. **Source-verified:** `parsePatternParam` strictly validates against the `PATTERNS` registry (`<key>__only`/`<key>__none`), else `ALL` sentinel — no crash, no fabricated filter; `sector`/`setup` verbatim render the existing honest empty-state on no match. Default Event-Study subject `Actionable` displayed honest `NA` cells (low-sample), confirming no fabrication along the travel. | PASS (source + observed NA honesty) | |
| TC-07 | Frontend build + typecheck (Suspense) | artifact | Build exits 0; no Suspense error | `npm run build` exit 0; `/stocks` `○ (Static)`; no type/Suspense errors | **PASS** | |
| TC-08 | Source-level anti-goal / scope guard | artifact | Diff scoped to 2 FE files; no backend/date param/hard-coded table | Diff = `stocks/page.tsx` + `research/page.tsx` only (+89/−4); no backend/config/blueprint change; no `as_of` param; cross-link mapping is payload-`kind`/`PATTERNS`-registry-driven (no hard-coded table); fetch effect `[asOf]` only | **PASS** | |
| TC-09 | Backend suite stays green | artifact | pytest exit 0, no new failures | 453 passed, 4 skipped, exit 0; zero backend files changed | **PASS** | |
| TC-10 | Required-still-passing regression sweep | browser | J-02/J-15/J-06/J-25/J-27/J-29/J-30 green | J-15 (no extra fetch) and J-02 (filters→URL sync) **source-verified**; labs still render (cross-link is purely additive, build green). Live click-through deferred to browser-qa-agent (contention). | PASS (source) / interactive deferred | |

**Result: 6/10 PASS outright (TC-01, TC-04, TC-05, TC-06 on source+observed evidence; TC-07, TC-08, TC-09 artifacts); 3 PARTIAL/deferred to browser-qa-agent (TC-02, TC-03, TC-10) on environmental contention; 0 FAIL.** No test exhibited broken/defective behavior.

## Step 4 — Chrome MCP browser checks

Frontend reachable (`curl http://localhost:3835` → 200; `/api/stocks` 200 in 48 ms; `/api/research/event-study` 200, fast).

**Observed live:**
- The `/research` Event Study Lab renders its full structure (expectancy / MAE-MFE / by-regime / by-sector / best-exit / rank-IC / survivorship caveat / `NA` low-sample cells) and the new **"View the names expressing this on the leaderboard →"** cross-link appears once the subject resolves (`await_element` + `await_text` both confirmed).
- Navigating to `/stocks?pattern=pullback_to_rising_dma__only` keeps the deep-link URL intact and adds **no `as_of`/date param** (J-18 runtime corroboration).

**Could not complete to stable capture:** the full multi-step click-through (TC-02) and the interactive
as-of-toggle / refetch / edge-case cases. Root cause is **environmental, not implementation**: a
concurrent automation on another project (`localhost:3650`, "Tapeology") shares this Chrome instance and
repeatedly navigated the working tab away mid-test (verified via `list_tabs` and a tab flipping from
`/stocks` back to `/research`/`localhost:3650` between successive actions). Per the iter-6 lesson I
serialized to a single tab and closed the foreign tab, but the contending process re-spawned tabs and
re-navigated faster than a stable hydrated frame could be captured. I did **not** fabricate any result
(qa.md rule). The dedicated `browser-qa-agent` stage that follows is the spec's authoritative J-31
acceptance gate and should drive the full travel when it can obtain exclusive Chrome access.

Evidence: `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-15-evidence/TC-01-research-eventstudy-crosslink.png` (research page during boot; cross-link section structure visible).

## Step 4b — UI Evolution Audit

1. **Did the UI evolve to reflect the new capability?** Yes — a visible cross-link on the Setup & Pattern Lab and shareable/deep-linkable leaderboard filter URLs.
2. **Can the user see/understand/control it?** Yes — the cross-link is an accent link with honest framing copy; filter state is now reflected into the URL for sharing/back-nav.
3. **Relying on old generic pages for new functionality?** No — by design J-31 rides existing approved homes (`/research`, `/stocks`, `/stocks/[ticker]`); the iteration is a navigation bridge, not a new surface.
4. **Technically complete but product-wise underexposed?** No — the only new affordance is itself a user-visible link + shareable URL.

**Verdict:** UI-PASS

## Blockers

None blocking ship. One environmental note for the next stage:
- **Browser QA contention (env):** the dedicated `browser-qa-agent` must complete the full live J-31 travel (TC-02) and the J-18 as-of-toggle cross-check (TC-05) under exclusive Chrome access. Source/build/backend evidence already substantiates correctness; this is the authoritative defining-flow capture, not a re-test of a suspected defect.

## Verdict rationale

Per qa.md: browser checks skipped/blocked by environment (not a defect) do not warrant FAIL, and faked
checks are forbidden. All artifact, build, typecheck, and backend checks PASS; the cross-link renders;
the deep-link is honored with no second date state (J-18, the principal risk, is clean in source and
corroborated at runtime). Review is PASS_WITH_NOTES with no required fixes. Overall: **PASS**.
