**Verdict:** PASS

# QA Report — goal-i_can_see_the_wealthy_future-iter-12

**Phase:** goal-i_can_see_the_wealthy_future-iter-12 (J-12 — Methodology / Glossary; the goal-completing iteration)
**Date:** 2026-05-31
**Agent:** qa (MODE 2: QA Validation)
**Frontend Present:** yes

## Summary

J-12 was validated end-to-end against a live stack and the full test suite. The single config-backed
methodology catalog is served by `GET /api/methodology`, rendered at `/methodology`, and reused inline
on `/stocks` (setup + VCP badge tooltips + the catalog-sourced Setup filter). All 17 functional test
cases pass. The full backend suite is **248 passed, 0 failed**; the frontend build is clean with the new
`/methodology` route (12 routes). The empty-diff guarantee holds for every pre-existing engine/model/router
file, so the 15 other journeys cannot structurally regress — re-confirmed live (J-02 filter narrows,
J-07 risk-off → 0 Actionable, J-13 as-of switching changes results, J-16 VCP entry present).

## Note on the "backend not healthy" runner warning

This is the chronic **runner-script debt** documented in the spec (NON-gating), not a product defect.
The QA runner probes `GET /health` (404) instead of the project's `GET /api/health` (200), and it tore
the managed services down before this validation. Per the spec's explicit guidance (iter-7/iter-10
precedent), I **self-produced live evidence**: started the backend with `CORS_ORIGINS=http://localhost:3835`
on :8835 (became healthy in ~3s via `/api/health`), and the frontend with `NEXT_PUBLIC_API_URL=http://localhost:8835`
on :3835. Both servers were killed by port at the end (Step 5b). No product issue.

## Step 1 — Artifact verification

| Artifact | Status |
|----------|--------|
| `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-12-dev.md` | ✅ present |
| `reports/reviews/goal-i_can_see_the_wealthy_future-iter-12-review.md` | ✅ present — **PASS_WITH_NOTES** (2 optional NOTEs, no blockers) |
| `runs/goal-i_can_see_the_wealthy_future-iter-12/status.json` | ✅ present (`current_step: review_passed`) |
| `reports/qa/goal-i_can_see_the_wealthy_future-iter-12-test-plan.md` | ✅ present — executed below |

## Step 2 — Backend tests (exact output)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Log: `reports/qa/goal-i_can_see_the_wealthy_future-iter-12-test.log`

```
........................................................................ [ 29%]
........................................................................ [ 58%]
........................................................................ [ 87%]
................................                                         [100%]
248 passed in 950.38s (0:15:50)
EXIT=0
```

Fast targeted re-run (no seeded DB) of the iteration's own suites:
`test_methodology.py + test_api_methodology.py + test_no_magic_numbers.py + test_config.py + test_config_engine.py` → **62 passed in 2.62s**.

## Step 3 — Frontend build (TC-16)

Command: `cd apps/frontend && NEXT_PUBLIC_API_URL=http://localhost:8835 npm run build`

```
✓ Compiled successfully
   Checking validity of types ...
 ✓ Generating static pages (12/12)
Route (app) … ├ ○ /methodology   3 kB   116 kB
```

Clean typecheck + compile; the new `○ /methodology` route is present (12 app routes). No new dependency.

## Step 3.5 — Functional test plan results

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | `GET /api/methodology` shape | api | 200, entries≥7, required keys, row=value⊕text | 200; 7 entries; all keys present; every row exactly one of value/text | PASS | live :8835 |
| TC-02 | Completeness: 6 statuses + VCP | api | 6 setup entries (ALL_STATUSES) + 1 VCP pattern; VCP not a setup | setups = Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist; pattern = vcp; VCP absent from setups | PASS | anti-goal: VCP is a pattern, not a status |
| TC-03 | Matching-config keystone | api | every displayed value == live config ref | 15 ref rows checked via `resolve_ref`; **0 mismatches** (Actionable 80/70/60; VCP 2/35/0.9/12/8/0.9) | PASS | no hard-coded copy, no drift |
| TC-04 | Config-only extra entry renders | artifact | unit test passes (no code change) | `test_config_only_extra_entry_renders_with_no_code_change` ✅ | PASS | in test_methodology.py |
| TC-05 | Unresolvable `ref` → ConfigError | artifact | test passes | `test_unresolvable_ref_raises_config_error` + `test_methodology_unresolvable_ref_raises` ✅ | PASS | honest-failure |
| TC-06 | `methodology.py` in CALC_FILES | artifact | no magic-number test passes | `methodology.py` in CALC_FILES; `test_no_magic_numbers` ✅ | PASS | |
| TC-07 | MINIMAL_VALID + methodology loads | artifact | from-scratch fixture validates | `test_methodology_minimal_valid_loads` ✅; MINIMAL_VALID has methodology block | PASS | |
| TC-08 | Full backend suite | artifact | 0 failures | **248 passed, 0 failed** | PASS | 15m50s (walk-forward boot) |
| TC-09 | Empty-diff of canonical files | artifact | byte-unchanged | `git diff --stat HEAD` empty for models/scanner/scoring/setups/patterns/forward_testing + all existing routers; order/broker/secret greps empty | PASS | no structural regression |
| TC-10 | `/methodology` renders full catalog | browser | 7 entries w/ meaning+thresholds+example; spot-check matches config | All 7 render; Actionable ≥80/≥70/≤60; VCP thresholds match | PASS | TC-10-methodology.png (1905×1810) |
| TC-11 | `/stocks` setup-badge tooltip = catalog meaning | browser | click reveals meaning == `/methodology`; dismissible | Click "Definition of Extended" → role=tooltip text **exactly** matches `/methodology` Extended meaning; Escape dismisses (0 tooltips after) | PASS | TC-11 png; not title-only |
| TC-12 | `/stocks` VCP badge exposes catalog VCP meaning (J-16 #4) | browser | per-row reason + catalog VCP meaning both reachable | role=tooltip shows catalog VCP meaning; per-row reason ("3 contractions tightening…") still present as title | PASS | TC-12 png |
| TC-13 | Setup filter catalog-sourced + graceful degrade (J-02) | browser | options = 6 catalog statuses in order; narrows rows; degrades on catalog fail | Options = 6 catalog statuses in catalog order; "Extended" → 122→11 rows, all Extended; fallback code present | PASS | filter narrows correctly |
| TC-14 | Sidebar "Methodology" after Watchlist | browser | nav routes to `/methodology` | Sidebar has `{href:/methodology, BookOpen}` after Watchlist; click from /watchlist → `/methodology` (heading "Methodology") | PASS | |
| TC-15 | Backend-unavailable error state | browser | explicit error, no fabricated copy | Backend stopped → `/methodology` shows **"Backend unavailable"**; no synthesized thresholds | PASS | TC-15 png |
| TC-16 | Frontend build clean, 12 routes | artifact | clean build, `/methodology` listed | ✓ compiled, types valid, `/methodology` present, 12 routes | PASS | |
| TC-17 | 16-journey regression sweep | browser | all surfaces render canonical values | `/ /stocks /themes /sectors /scanner-runs /system-health /backtest /watchlist` all 200; system-health has by_bucket/setup/regime/by_vcp/excess/control_group + survivorship label; J-07 risk-off (2022-10-07) → 0 Actionable; J-13 as-of varies Actionable (1 on 2026-02-27, 0 on risk-off dates) | PASS | TC-17 dashboard + system-health pngs |

**17/17 test cases passed.**

## Step 4 — Chrome MCP browser checks

Performed against the self-started live stack (see note above). Evidence in
`reports/qa/goal-i_can_see_the_wealthy_future-iter-12-evidence/` — 6 PNGs, all md5-distinct:

- `TC-10-methodology.png` (1905×1810) — `/methodology` full catalog (Surface 1)
- `TC-11-stocks-setup-tooltip.png` (1920×870) — `/stocks` setup badge inline definition (Surface 2)
- `TC-12-stocks-vcp-tooltip.png` (1920×870) — `/stocks` VCP badge catalog meaning + per-row reason
- `TC-15-methodology-backend-unavailable.png` — explicit error state
- `TC-17-dashboard.png`, `TC-17-system-health.png` — regression surfaces

Two distinct J-12 surfaces (methodology page + stocks tooltip) captured with distinct md5sums and
dimensions, satisfying the two-surface evidence requirement.

## Step 4b — UI Evolution Audit

1. **Did the UI evolve to reflect the new capability?** Yes — a NEW `/methodology` page, a NEW sidebar
   entry, and NEW inline badge tooltips on `/stocks` all surface the catalog.
2. **Can the user see, understand, and control it?** Yes — the glossary explains all six statuses + VCP
   with config-matching thresholds and worked examples; badges reveal the same definition inline on
   hover/focus/click and are dismissible.
3. **Still relying on old generic pages?** No — the new capability has a dedicated home, and the
   `/stocks` Setup filter vocabulary is now catalog-sourced (hard-coded list removed).
4. **Technically complete but under-exposed?** No — both the page and the inline tooltips are reachable
   and discoverable; the matching-config keystone proves the displayed numbers are the live config values.

**Verdict:** UI-PASS

## Blockers

None.

## Notes

- Review verdict was PASS_WITH_NOTES; both NOTEs are optional hardening (pop-over clip near the table edge;
  `resolve_ref` scalar assertion) — neither blocks, and the matching-config test guards drift. The pinned
  pop-over still mounts its content in the DOM and is fully visible on `/methodology`.
- Anti-goals re-checked clean: no `order`/`broker`/capital-deployment path, no secrets, no `localStorage`
  token use; VCP is a pattern (not a 7th status); read-only catalog, no score/return/bucket recompute;
  thresholds resolved live from config (no fabricated/placeholder number — unresolvable ref fails boot).
- Services I started were killed by port at completion (Step 5b); nothing left listening on :8835/:3835.
