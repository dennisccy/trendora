# goal-mcp-loop-iter-23 Execution Plan

Frontend Present: yes

## Context (why this iteration exists)

iter-22 shipped J-14 (deep, vendor-labeled `^SPX`/`^NDX`/`^DJI`/`^VIX`/`^TNX` context on the Dashboard
chart + a new `/data` vendor-disclosure panel) correctly — confirmed independently by the reviewer, the
"qa" agent, and the auditor (`PASS_WITH_GAPS`). But the canonical `browser-qa-agent` report
(`ui-test-results.md`) and `ux-regression-reviewer` report were **never re-run** after the mid-iteration
`minBarSpacing: 0.02` fix, so both still record their pre-fix FAIL, and `phase-closure` correctly returned
`CLOSURE-FAIL` on that evidentiary gap (see `reports/phase-goal-mcp-loop-iter-22-closure-verdict.md`). This
iteration's entire job is to re-run those lanes clean against the already-fixed build. **Zero new feature
code is in scope.**

## What to Build

- **Nothing new.** This is a verification-only re-run. No backend or frontend source changes beyond what
  iter-22 already committed.
- **Pre-verified fact (do not re-litigate):** contrary to the phase spec's own NOTES section (written at
  iter-22-eval time, saying the fix was "uncommitted in the working tree"), `minBarSpacing: 0.02` **is
  already committed** — `apps/frontend/components/phase-cross-view-chart.tsx:162`, landed in commit
  `20f90b0` ("goal(mcp-loop): iter 22 — CONTINUE"). Verified just now: `git diff HEAD` for this file is
  empty and `git status` shows no modified tracked files (only the 3 new iter-23 untracked files). No
  commit action is needed — just confirm no local drift before serving the build.
- **Pre-verified fact:** the local `apps/backend/data/trendora.db` (gitignored build artifact) already
  carries the 3 deep index symbols from iter-22's remediation — live-queried just now: 590 distinct
  symbols in `daily_prices`, `^SPX`/`^NDX`/`^DJI` = 7,674 rows each from `1996-01-02`. **No DB rebuild is
  needed or wanted** (a rebuild on this 30-year basis is expensive and would only re-derive what's already
  correct).
- Environment prep before any browser QA: `rm -rf apps/frontend/.next` (the known iter-20/21
  staleness-stamp trap — `start-frontend.sh`'s freshness check only looks at the backend URL and can
  silently serve a stale pre-fix bundle), then bring up `scripts/start-backend.sh` (:8255) and
  `scripts/start-frontend.sh` (:3255) and confirm HTTP 200 on both before dispatching browser-qa-agent.
- Re-run the canonical `browser-qa-agent` LIVE (execute, not code-inspect) against a freshly generated
  `reports/qa/goal-mcp-loop-iter-23-test-plan.md` / `reports/phase-goal-mcp-loop-iter-23-ui-test-plan.md`
  that mirrors iter-22's 19 cases (UT-01..UT-19 in
  `reports/phase-goal-mcp-loop-iter-22-ui-test-plan.md`) — since the only code delta since then is the
  one-line chart fix — **plus one new dedicated J-13 replay case** (see Key Test Scenarios). Regenerate
  `reports/phase-goal-mcp-loop-iter-23-ui-test-results.md` to a PASS with md5-distinct, correctly labeled
  full-page/element-clip screenshots.
- Live-replay the required-still-passing set (J-01, J-03, J-04, J-05, J-10, J-11, J-12) against each
  journey's own golden script in `runs/goal-session-mcp-loop/journey-scripts/`.
- Re-run `ux-regression-reviewer` against the fresh evidence → expect UX-REGRESSION-PASS (its sole
  blocking finding was the F1 default-view defect, which is the fix already applied — it just needs fresh
  evidence, not a new fix) and have it reconcile the `user-visible-changes.md` "renders automatically"
  wording per the closure verdict's Issue #3.
- Re-run `phase-closure` → expect CLOSURE-PASS; reconcile `status.json`/`qa.md` so no `-fail-`-named
  artifact sits under a `blockers: []` claim.
- The one **permitted** test-fixture refresh (see Files section below).

## Agents Required

- backend-data: no -- no backend source changes; no new endpoints, migrations, or engine logic.
- frontend-ux: no -- no frontend source changes; no new components; no chart-config change beyond the
  already-committed `minBarSpacing` fix; no new UI.
- developer: yes, but thin/verification-only -- confirm the fix-commit and DB state (both already
  confirmed above — just avoid re-deriving from scratch), do the `rm -rf .next` + dual-service HTTP-200
  check, apply the ONE permitted `journey-scripts/J-13.json` refresh if still stale, run the targeted
  regression test files listed below, and write `docs/handoffs/goal-mcp-loop-iter-23-dev.md` documenting
  this as a zero-application-diff verification pass.
- reviewer: yes -- confirm the diff really is zero-app-source (only the permitted fixture line, if
  touched) and that the dev handoff accurately reflects a verification-only pass. Should be fast.
- qa / browser-qa-agent / ux-regression-reviewer / auditor / phase-closure-auditor: dispatched by the
  standard pipeline as usual (not gated by this plan) — see Key Test Scenarios for what each must confirm.

## Files to Create/Modify

- `runs/goal-session-mcp-loop/journey-scripts/J-13.json` -- step 1 currently pins
  `"expect": {"text": "587 symbols"}`; refresh to `"590 symbols"` (verified live above: 590 is the current,
  correct, honest count after iter-22's additive load of `^SPX`/`^NDX`/`^DJI`). This is the phase spec's
  own explicitly sanctioned exception ("Permitted test-fixture refresh") — confirm it is still stale before
  touching it, and touch nothing else in the file.
- `docs/handoffs/goal-mcp-loop-iter-23-dev.md` -- new dev handoff (verification-only, zero application
  diff, environment-setup steps performed, targeted test results, explicit confirmation that
  `test_api_indexes.py` finished green this time).
- **No files under `apps/backend/` or `apps/frontend/` should change.** Any diff touching engine/scoring/
  referee/ledger code, chart config beyond what's already committed, or any new UI is out of scope for
  this iteration and should be rejected by review.

## UI Evolution

- New user-facing capability: none — J-14's Dashboard overlay + `/data` vendor panel already shipped in
  iter-22; this iteration only re-proves them through the canonical QA lane.
- New information displayed: none.
- New user actions: none.
- UI surface changes: none — surfaces exercised are the EXISTING Dashboard `/` "Regime × phase cross-view"
  card and the EXISTING `/data` page (vendor-disclosure panel + availability heatmap).
- Navigation changes: none.

## Visual Requirements

- Component patterns: no new components. Re-exercise the existing `PhaseCrossViewCard`
  (lightweight-charts pane, 10-line legend with vendor suffixes) and the existing `/data` panels
  (`IndexVendorPanel`, `AvailabilityHeatmap`, both `Card`/`PanelTitle`-based).
- Layout: unchanged — Dashboard `/` chart card; `/data` sidebar panel stack.
- Key visual effects: none new. Reconfirm the already-shipped 10-slot categorical line palette (validated
  against the `dataviz` skill in iter-22, zero duplicate colors) and the availability heatmap's monotonic
  non-amber density ramp + violet snapshot ring render as specified.
- States to handle: reconfirm existing loading/error/empty states on `/data` (whole-backend-down → honest
  message; provenance panel's own isolated failure → its own error state) — no new states to add.

## Key Test Scenarios

- **J-14 (target):** default (no zoom/pan) Dashboard chart view shows a deep `^SPX` line starting at/near
  1996-01-02, well before SPY's 2005 first bar. Capture full-page or element-clip evidence (never a
  scrolled viewport) and md5-check the deep line is actually in-frame — a PASS label or DOM-text legend
  line is not proof (iter-3/11/13/14 lesson). Legend/tooltip show all three vendor categories
  (Stooq/Yahoo/FRED-macro proxy). `/data` vendor panel byte-matches `meta.json` (`^SPX` first=1996-01-02/
  Stooq, `^VIX`=Yahoo, `^TNX`/`^DXY`/`^VXN` labeled "FRED-macro proxy" — never a market index, ETF rows
  carry no vendor tag).
- **J-13 (dedicated replay — the gap iter-22 left open, last dedicated pixel was iter-21):** two-group
  legend ("Price data — cell fill" vs "Scored snapshot — indicator"), monotonic non-amber density ramp,
  violet snapshot ring, a md5-distinct hover-tooltip pair (a bars-but-no-snapshot date vs. a snapshot
  date), pool coverage reflecting 590 total stored symbols (live-confirmed above).
- **Required-still-passing, graded against each journey's own golden script (iter-21 lesson — not against
  test-plan wording):** J-01 (`/stocks` 541/541, zero leaked index-caret rows), J-03 (all scores read "Not
  yet proven"), J-04 (Dashboard regime card + evidence link intact), J-05 (`/evidence` all-FAIL ledger rows
  auditable), J-10 (Full ↔ Recent history toggle on `/stocks/{ticker}`, no crash), J-11 (no stale
  pre-refresh edge value resurfaces; both ledgers still all-FAIL), J-12 (`/data` universe count == `/stocks`
  count).
- **Regression / shared-surface:** the 5 pre-existing ETF lines/colors/order on the Dashboard chart are
  byte-identical to pre-iter-22; zero console errors; `/stocks` and `/evidence` show no leaked carets or
  fabricated "Proven" claims.
- **Backend tests (targeted, not the full suite):** re-run `test_indexes.py`, `test_api_indexes.py` (audit
  finding T2 left this one unconfirmed-finished last iteration — explicitly confirm it passes this time),
  `test_data_manager.py`, `test_load_missing_index_symbols.py`, `test_bar_cache.py`, and the two evidence
  frozen-golden suites (`test_evidence.py`, `test_staging_ledger_routing.py`) — expect all green,
  byte-identical, no assertion changes needed anywhere except the one permitted journey-script line.
  `test_api_indexes.py` shares the expensive session-scoped `loaded_engine` fixture (full 30-year/
  590-symbol bootstrap) that ran 60+ minutes mid-iter-22 without finishing before that handoff — budget
  for this; a long-running-but-progressing run is not a hang. Do NOT run the full `pytest tests/` suite
  (~10-11h on this basis per project lesson) — targeted files only.
- **Frontend:** `npx tsc --noEmit` clean (no source changed; this should be a no-op confirmation).
- **Error cases:** backend-down and cold-start states still degrade honestly (contained state, honest
  "—"/NA, never a blank error page) on the exercised pages; an ETF series with no `meta.json` vendor
  record still renders no fabricated label.
- **Gate outcomes:** `ux-regression-reviewer` → UX-REGRESSION-PASS. `phase-closure` → CLOSURE-PASS,
  `status.json` not `blocked`, no stale `-fail-`-named artifact left standing under a `blockers: []` claim.
  Both ledgers (`certified-claims.jsonl` 7/7 FAIL, `staging-ledger.jsonl` 7/7 FAIL) must remain
  byte-unchanged — this iteration carries no `## Evidence Claim`, so the post-decompose gate passes
  automatically.
