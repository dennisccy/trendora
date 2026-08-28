# UI Test Results (merged)

**Date:** 2026-08-28
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 12/12 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-27-evidence/J-01-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-27-evidence/J-04-verify.png |
| UT-J-10 | Bounded recovery of the two trading days the iter-5 drill deleted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-27-evidence/J-10-verify.png |
| UT-J-11 | Incident-bounded clean regeneration of derived state (disposable-clone serving verification) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-27-evidence/J-11-verify.png |
| UT-J-06 | A frozen manifest never changes — later data, rebuilds, and regeneration are safe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-27-evidence/J-06-verify.png |
| UT-01 | Today page loads with Manifest card | smoke | P1 | Page renders, "Manifest" card heading visible below the compass cards, no crash | Page rendered normally; a `Manifest` card-title element found in DOM (`text-sm font-semibold` card-title styling); no React error boundary text; console-log capture unsupported by this Chrome MCP build (`# TODO: Console logging not yet implemented`) so absence of errors could not be independently confirmed via console API, but no visible error UI appeared | PASS | `reports/qa/goal-market-compass-iter-27-evidence/UT-01-result.png` |
| UT-02 | "Basis: available" regression (intact manifest+run) | regression | P1 | Badge reads exactly "Basis: available" in green/positive style, no gray detail text, "version 2"/"retrospective" nearby | `[data-testid="compass-manifest-basis"]` = `<div class="...border-pos bg-surface-2 text-pos">Basis: available</div>` with no sibling detail span; page text shows "Manifest / retrospective / version 2 / frozen / not prospective-eligible" | PASS | `reports/qa/goal-market-compass-iter-27-evidence/UT-02-result.png` |
| UT-03 | "Basis: rebuilt" regression (frontier manifest) | regression | P1 | Badge reads exactly "Basis: rebuilt" in amber/warn style with detail text; "version 6"/"at ingest" nearby | `[data-testid="compass-manifest-basis"]` = `<div class="...border-warn bg-surface-2 text-warn">Basis: rebuilt</div><span class="text-text-faint">the source scanner run was recreated after this manifest was frozen</span>`; "version 6" and "at ingest" both present in DOM | PASS | `reports/qa/goal-market-compass-iter-27-evidence/UT-03-result.png` |
| UT-04 | "Basis: unavailable" — not live-reproducible, automated substitute | happy-path | P1 | `test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run` PASSES | Ran `cd apps/backend && .venv/bin/python -m pytest tests/test_api_compass.py -v -k "never_404s_and_manifest_bytes_survive"` → `1 passed, 10 deselected in 0.44s`. Confirmed honestly not reproducible live (no as-of date in the canonical DB currently has a frozen manifest with a deleted backing ScannerRun, and manufacturing one is out of scope/forbidden this iteration) | PASS | none (pytest evidence only, per test plan) |
| UT-05 | "Regenerate manifest" control unaffected | regression | P2 | Modal opens with confirm-regenerate text; Cancel closes it with badges/versions unchanged | Clicked `[data-testid="compass-manifest-regenerate-button"]` → modal `[data-testid="compass-manifest-regenerate-confirm-modal"]` opened with text "This mints a NEW manifest version for 2025-04-15 from the current selection rule and config."; clicked Cancel → modal closed, `Basis: available` unchanged, no "v3" text found, DB row count for `as_of='2025-04-15'` confirmed still 2 (unchanged) | PASS | `reports/qa/goal-market-compass-iter-27-evidence/UT-05-result.png` (+ `UT-05-modal.png` interim) |
| UT-06 | Unknown/future `?asof` degrades safely | error | P2 | No blank/crash; `?asof` stripped from URL; Manifest card shows current "Latest" frontier data | Navigated to `/?asof=2099-01-01`; `window.location.href` settled to `http://localhost:3255/` (param stripped); Manifest card showed the frontier's "version 6" / "Basis: rebuilt" state (same as UT-03's Latest data), not an error | PASS | `reports/qa/goal-market-compass-iter-27-evidence/UT-06-result.png` |
| UT-J-05 | J-05: Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | journey (goal-mode regression) | P1 (Must-have journey) | See goal.md J-05 steps/acceptance — see notes below | Verified via a mix of browser + read-only backend checks; steps 1 and 6 (which require a live remove+backfill of the "last two trading days") were deliberately NOT executed this run — see Notes. All other steps verified. See detail below. | PASS (with one documented, safety-driven scope limitation) | `reports/qa/goal-market-compass-iter-27-evidence/UT-J-05-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-28

