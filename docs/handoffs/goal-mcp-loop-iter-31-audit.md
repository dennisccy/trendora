# goal-mcp-loop-iter-31 Audit Report

**Date:** 2026-07-13
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-19 (the negative-results graveyard) is genuinely delivered: the new pure read-compose module serves all 14 non-PASS verdicts (7 canonical + 7 staging) with correct selectors/verdict/date/deflation/lineage, the `ma_stack` closed FAIL carries its "permanent" marking, the revisit-protocol rule is served, and the honesty fence holds (only non-PASS, never the `accent`/"Proven" styling; `/evidence`, `proven_signals`, and all three ledger state files are byte-identical). The audit found and **fixed** the one real defect browser-QA caught — the lineage deep-link did not scroll to its target registry row on client-side navigation (UT-07, P1 FAIL) — and browser-verified the fix. Residual gaps are two minor browser sub-tests (empty-state, loading-skeleton) that were skipped but are covered by backend tests plus the passing backend-unavailable analog; they do not compromise the goal.

---

## 2. Findings

### Frontend Findings

**F1 — IMPORTANT (fixed): lineage deep-link did not scroll to the target registry row on SPA navigation**
`apps/frontend/app/research/graveyard/page.tsx:230` renders each Lineage link as a Next.js `<Link href=".../research/registry#registration-<id>">`. Browser-QA (UT-07, a P1 happy-path test) confirmed that clicking it navigated to the correct URL and the target `<tr id="registration-...">` existed, but `window.scrollY` stayed at `0` — no scroll to the row. The browser's native scroll-to-fragment fires only on a full/hard load; on a client-side route transition into `/research/registry`, the rows are fetched *after* the route commits (`apps/frontend/app/research/registry/page.tsx:32-41`, async `fetchRegistry` → `state.kind === "ok"`), so the fragment resolves to nothing and no scroll occurs. UT-13 proved the anchor mechanism itself (`id` + `scroll-mt-20` at `registry/page.tsx:133,135`) is sound on hard navigation. This is a spec-named user action ("a row's lineage link resolves to its registry row" — TESTING REQUIREMENTS; plan Assumption #4 "land on the exact row"), so it sits at the IMPORTANT/GAP boundary; per the rubric I treated it at the higher level and applied the fix the ux-regression report itself recommended.

*Fix applied* (`apps/frontend/app/research/registry/page.tsx:43-58`): a guarded `useEffect` keyed on `state.kind` that, once the rows have mounted, reads `window.location.hash` and (via one `requestAnimationFrame`, with cleanup) calls `document.getElementById(hash.slice(1))?.scrollIntoView({ block: "start" })`. No hash ⇒ no-op, so plain browsing is unchanged. This is the canonical Next.js fix, surgical (one effect), and lives in a file iter-31 already owns for its anchor change.

*Verification (real browser, backend+frontend live on 8255/3255; same `window.scrollY`/`getBoundingClientRect` method browser-QA used):*
- Deep-link path (UT-07 replication, viewport 1280×600): navigated to `/research/graveyard`, clicked the `ma_stack` lineage link (real anchor click → SPA nav). Result: URL `…/research/registry#registration-factor-ma_stack-d10-h20`, h1 "Pre-registration registry", 11 rows, **`scrollY: 584`** (was `0` at FAIL), target row **`getBoundingClientRect().top: 80`** — i.e. exactly just-below-the-sticky-header (the `scroll-mt-20` = 80px), `targetInViewport: true`.
- Regression path (UT-13 preservation): navigated to `/research/registry` with **no** hash → `scrollY: 0`, 11 rows, 5 columns — plain browsing unchanged, effect is a correct no-op.
- `npx tsc --noEmit` clean (exit 0); `test_graveyard.py` + `test_api_graveyard.py` + `test_registry.py` = 45 passed (frontend-only change, backend unaffected).

**F2 — GAP: two browser sub-tests skipped (empty-state UT-10, loading-skeleton UT-11)**
Browser-QA skipped UT-10 (missing/empty ledger → honest empty state) because renaming the live ledger files was correctly denied by the permission system, and UT-11 (loading skeleton under throttling). Neither was executed in-browser this iteration. Both are well-covered by other evidence, so this is a documented limitation, not a blocker: the empty/missing-ledger *logic* is proven by `test_graveyard.py::test_missing_ledger_files_degrade_to_empty_payload_no_crash` and `::test_empty_ledger_files_degrade_to_empty_payload_no_crash` (both pass) and `test_api_graveyard.py::test_graveyard_endpoint_200_empty_on_missing_ledger_files`; the `GraveyardEmptyState` (`graveyard/page.tsx:105-121`) and `GraveyardSkeleton` (`:270-278`) components exist and are wired (`:58,:72`); and UT-09 (backend-unavailable → contained error card, nav intact) PASSED in-browser, exercising the same degraded-render path. No fix applied (GAP-level).

### Backend Findings

**B1 — OBSERVATION: honest-null lineage path is exercised only by fixtures (by design)**
All 14 real ledger entries currently match a registration, so `match_registration` returns non-null for every live row (verified by direct payload inspection: `lineage matched: 14 | honest-null: 0`). The `lineage: null` branch (`graveyard.py:100` → `graveyard/page.tsx:220-228` "No registration lineage") is therefore only covered by `test_graveyard.py::test_lineage_is_honest_none_for_an_unregistered_selector_set`, not live data. This is correct and intended (the iter-30 backfill is complete); noted only for transparency. No action.

### Test Findings

**T1 — OBSERVATION: the two "real ledger" tests rely on ambient env, not a delenv**
`test_graveyard.py::test_real_ma_stack_entry_round_trips_end_to_end` and `::test_real_graveyard_has_fourteen_entries_today_all_non_pass` (and the API analogs) read the committed state files via the resolvers without `monkeypatch.delenv` for `TRENDORA_LEDGER_PATH`/`STAGING_LEDGER_PATH`/`TRENDORA_REGISTRY_PATH`. Under a bare `pytest` (this audit: no such env set — confirmed) they read the committed files and pass. Under `run-goal.sh` those env vars point at the same committed state files anyway (per the resolver docstrings), so the tests stay consistent. Benign; noted only as a robustness observation. The test suite is otherwise tight — real-data round-trip assertions (`ma_stack` claim/verdict/date byte-match), status-derived counts (not a hardcoded "14"), and a single-source endpoint-equals-module assertion.

---

## 3. Domain Assessment

The core domain logic is correct and honest. `build_graveyard_payload` (`app/engine/graveyard.py`) is a faithful pure read-compose: it reads both ledgers via the existing `ledger.read_entries`, excludes forward-walk monitoring records (`type == FORWARD_WALK_TYPE`, mirroring `build_evidence_payload`), and filters status-driven (`verdict.status != STATUS_PASS`) — a future PASS row disappears automatically rather than by a hardcoded count. It recomputes nothing: `verdict` (including `deflation`/`deflation_divisor`) is re-displayed verbatim, and lineage comes from the **reused** `registry.match_registration` (loaded once, passed through), never a second matcher — the exact B-902 failure mode is avoided, and the drift-insurance test (`test_registry.py:293-294`, `registry._CLAIM_SELECTOR_KEYS == mcp.tools._CLAIM_SELECTOR_KEYS`) pins the one constant that could silently break it (verified byte-equal in source).

The honesty fence is intact and this is the highest-risk surface in the product: the graveyard shows only non-PASS rows; the frontend `verdictKindVariant` (`graveyard/page.tsx:152-156`) has **no** `accent` branch, so the "Proven" styling can never appear; the page carries no `proven`/`signal` fields (unlike `_claim_row`); and `GET /api/evidence`, `proven_signals`, the "Proven" badge, and all three ledger state files are byte-identical (git status empty; live payload inspection confirmed `/api/evidence` unchanged at 7 canonical FAIL claims, `proven_signals: {}`). The one deliberate contract evolution (staging non-PASS verdicts become browsable) is correctly scoped — staging carries 0 PASS today and any PASS would be filtered out here, never surfaced as proven. Missing/empty ledgers degrade to an empty payload with 200 (never 500), verified by tests and endpoint mounting without a DB/session.

Real-data verification (direct `build_graveyard_payload()` call): 14 entries (7 canonical + 7 staging), all `FAIL`, all lineage-matched, `ma_stack` lineage `status == "closed"`, `revisit_protocol.rule` present (288 chars, no proven-language). This matches the DoD's round-trip requirement (anti-goal #3).

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/frontend/app/research/registry/page.tsx` | Added a guarded `useEffect` (keyed on `state.kind`, rAF-deferred, cleanup) that scrolls a `#registration-<id>` deep-link target into view once the async rows have mounted — fixing UT-07 (lineage link did not scroll on SPA client-side navigation). Browser-verified: `scrollY 584` / target `top 80` on the deep-link path; `scrollY 0`, 11 rows/5 cols on the no-hash regression path. `tsc --noEmit` clean. |

No dev-handoff claim was invalidated (the dev/frontend handoffs correctly deferred lineage-scroll verification to browser-QA and did not assert it worked). The historical browser-QA UT-07 FAIL and the ux-regression WARN were accurate when written; a browser-QA re-run would now pass UT-07.

---

## 5. Recommended Next Step

**Proceed to the next iteration.** J-19's definition-of-done is met and the one browser-QA FAIL is resolved and browser-verified in this audit; the required-still-passing surfaces (J-18 registry plain-browse, `/evidence`) were re-confirmed unchanged. Optional, non-blocking follow-ups for a future pass: (a) a browser-QA re-run of UT-07 to record the now-passing evidence frame, and in-browser execution of the two skipped states (UT-10 empty-state, UT-11 skeleton) — both already logic-covered; (b) if a future iteration touches the registry page, consider hoisting the hash-scroll effect into a tiny shared hook if a second deep-linked table appears (currently a single, local consumer — no premature abstraction warranted). The audit fix is frontend-only and should be committed with the rest of iter-31.
