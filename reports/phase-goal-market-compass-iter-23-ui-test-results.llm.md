# Goal Iteration 23 (market-compass) — UI Test Results

**Phase:** goal-market-compass-iter-23
**Date:** 2026-08-27
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 2/2 tested journeys passed (0 failed). Lean-mode scope: J-10, J-11 only (J-01, J-04 covered by deterministic replay separately, not re-tested here).

---

## Scope note

This iteration's spec (`docs/phases/goal-market-compass-iter-23.md`) targets J-11's final
serving/replay acceptance objective, run against a **disposable clone** of the repaired
canonical database (`runs/goal-market-compass-iter-23/verify-clone/trendora-clone.db`),
served by the backend already running on port 8255 (pinned via `TRENDORA_CONFIG` to
`verify-clone/config.verify.yaml`) and the frontend on port 3255. Before testing, I
independently verified via `/proc/<pid>/fd` and `lsof` that the backend process (pid
1809182) has ONLY the clone DB files open — the canonical
`apps/backend/data/trendora.db` is not open anywhere. All browser navigation and DB
reads below were performed against the disposable clone only; the canonical DB was never
touched by this QA pass.

Per the dev handoff's explicit warning, the as-of switcher was never pointed at any of the
7 manifest-less incident dates (2026-05-12, 05-13, 07-10, 07-13, 07-24, 07-27, 08-03) —
only the frontier (2026-08-12) and one incident date that already carries a manifest
(2026-08-11) were exercised, per the dev handoff's own guidance on which dates are safe.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-11 | Incident-bounded clean regeneration of derived state — disposable-clone serving verification | smoke | P1 | `/` renders correctly at the frontier (2026-08-12) and at an already-manifested incident date (2026-08-11) with real repaired values, honest `Basis: rebuilt` disclosure, zero unacceptable side effects (no new ScannerRun, no minted manifest, manifest bytes/hashes unchanged), and named trap 1 (FK survival) holds live | `/` and `/?asof=2026-08-11` both rendered real served values, no error boundary; `Basis: rebuilt` correctly shown for the incident date; before/after DB checks confirm zero unacceptable side effects; `PRAGMA foreign_keys=ON` + `foreign_key_check(next_session_manifests)` returned 0 violations live | PASS | `reports/qa/goal-market-compass-iter-23-evidence/J-11-today-frontier-result.png`, `reports/qa/goal-market-compass-iter-23-evidence/J-11-incident-2026-08-11-result.png` |
| UT-J-10 | Bounded recovery of the two trading days the iter-5 drill deleted — repaired data serves correctly | smoke | P1 | AVB stock detail page renders correctly at as_of 2026-08-11 and 2026-08-12 (the two repaired dates) with real computed values (not NA/broken); the underlying repaired volumes exactly match the certified figures (554757.0 / 3706010.0) | AVB page rendered real computed risk/pattern metrics at both dates, no error boundary; `GET /api/stocks/AVB/bars?range=full` (the same endpoint the page consumes) returned volume 554757.0 for 2026-08-11 and 3706010.0 for 2026-08-12 — exact match | PASS | `reports/qa/goal-market-compass-iter-23-evidence/J-10-AVB-2026-08-12-result.png` |

---

## Passed Tests

### UT-J-11 — Incident-bounded clean regeneration of derived state (serving verification)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-23-evidence/J-11-today-frontier-result.png`, `reports/qa/goal-market-compass-iter-23-evidence/J-11-incident-2026-08-11-result.png`

Steps executed (from the goal file's J-11 journey + this iteration's spec TESTING REQUIREMENTS TC-3/TC-5/TC-6/TC-7/TC-8/TC-10, exercised via Chrome MCP against `http://localhost:3255`):

1. **Navigated to `/` at the latest as-of (2026-08-12 — the frontier, itself one of the 11 incident dates).** Page rendered: market-state band (`Risk-on 73.24/100`, `Expansion`, severity `25.84`), plain-English summary, What-changed, sector/theme/stock rotation lists with real named entities (Home Construction, Regional Banks, Materials, SMCI/TOL/TER/... leadership-bucket moves), next-session focus (comparison cohort + near-threshold shadow tables with real tickers/scores), and manifest strip showing versions v1–v6, all correctly `not eligible` (honoring AG-17 — every manifest minted during the iter-5-drill-to-Stage-G window stays marked unusable as prospective evidence). No client error boundary. This matches the dev handoff's cited regime/phase/severity figures within rounding.
2. **Navigated to `/?asof=2026-08-11`** (an incident date that already carries a manifest, per dev handoff Known Issue #4 — safe to exercise). Page rendered a full retrospective compass view with a visible retrospective stamp ("This is a retrospective view, reconstructed under the CURRENT selection rule and config..."), real distinct values (regime 73.44, breadth 57.4%/69.7%), and — critically — the manifest strip's basis-disclosure badge read **`Basis: rebuilt`** with the caption "the source scanner run was recreated after this manifest was frozen." This is live proof that the A4/A4-bis `basis_disclosure` fail-closed fix (which the dev-handoff traced through Stage B1–G) is correctly reporting `rebuilt` for an incident-date manifest whose source `ScannerRun` really was destroyed and regenerated by Stage D — not a fabricated "available" claim.
3. **Navigated to `/market`.** Returned HTTP 404. This matches the dev handoff's documented pre-existing Known Issue #1 (J-08's `/market` route has not been built yet — out of scope for this iteration per the spec's own OUT OF SCOPE list). Not counted as a J-11 regression; noted below as a known gap.
4. **Zero-unacceptable-side-effect reconciliation** (ruling item 5 / TC-10), performed via before/after API calls and a direct read-only query against the clone DB file:
   - `GET /api/compass?as_of=2026-08-12`: version **6** / mode `at_ingest` / `manifest_hash 9bc08cfba04fc2dcab7eeb35f7b695834ef69da5ca3b6634acca4c605d5769c3` — identical before and after all browser navigation.
   - `GET /api/compass?as_of=2026-08-11`: version **3** / mode `retrospective` / `manifest_hash 212c5c0ebf6182f12e4c0200cbee6b7e98558827c558d725476aa4508c17f426` — identical before and after.
   - Direct read-only query on `trendora-clone.db`: `next_session_manifests` row count is **24** (unchanged); all 7 manifest-less incident dates (2026-05-12, 05-13, 07-10, 07-13, 07-24, 07-27, 08-03) still show **0** manifest rows — the manifest-minting trap was never triggered because the as-of switcher was never pointed at them.
   - `max(scanner_runs.id)` is still **3158** and the 11 incident dates still map 1:1 onto ids 3148–3158 — no new `ScannerRun` was created by this browsing session (backend boot warmup had already run before QA started, per the pump coordinator's handoff).
5. **Named trap 1** (manifest survival independent of FK enforcement), reproduced independently: `PRAGMA foreign_keys=ON` then `PRAGMA foreign_key_check(next_session_manifests)` on a fresh read-only connection to the clone → **0 violations**.

All checks in scope for this iteration's TESTING REQUIREMENTS (TC-3, TC-5, TC-6, TC-7, TC-8, TC-10) passed against the disposable clone. Combined with the dev handoff's own equivalent HTTP-level checks, this constitutes the "J-11 passes via browser-qa-agent" checkbox in the iteration's Definition of Done.

**Known issue (not a J-11 regression):** `/market` 404s — pre-existing gap, J-08 (the page that would create `/market`) has not been built yet; explicitly out of scope for this iteration (confirmed against the iter-23 spec's own OUT OF SCOPE list and the dev handoff's Known Issue #1). `/` is currently the sole real Today/Market-Compass serving surface and it fully exercises the repaired incident-date state.

### UT-J-10 — Bounded recovery of the two trading days the iter-5 drill deleted
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-23-evidence/J-10-AVB-2026-08-12-result.png`

J-10 is raw-layer-only with no UI surface of its own (goal.md: "Walkthrough: waived — raw-layer incident repair with no UI surface change of its own"), so the browser check here verifies that the repaired raw rows actually **serve** correctly through the real product, complementing this iteration's TC-9 requirement:

1. Navigated to `/stocks/AVB?asof=2026-08-12` — page rendered "AVB" stock detail with real computed values: `Avoid` classification, `Real Estate` sector, invalidation level `$187.89`, ATR% `2.01%` (p7 of universe), downside volatility `0.98%`, worst 20-day window `-89.37%`, and correctly-honest `NA` forward returns (no future bars exist past the frontier date — never fabricated). No error boundary.
2. Navigated to `/stocks/AVB?asof=2026-08-11` — page rendered distinct real values for that date (invalidation `$187.94`, different ATR/volatility percentiles), confirming the repaired 2026-08-11 raw bar drives a genuinely different, correctly computed derived state (not a stale/duplicate of 08-12).
3. Cross-checked the certified J-10 figures directly against `GET /api/stocks/AVB/bars?range=full` — the exact endpoint the (client-rendered) stock page consumes: `2026-08-11` volume **554757.0**, `2026-08-12` volume **3706010.0** — an **exact match** to the certified figures cited in the dev handoff and this iteration's TC-9.

The repaired AVB rows for both incident dates serve correctly end-to-end (raw bars → derived risk/pattern metrics → rendered page), with no client error and no fabricated/stale value.

---

## Failed Tests

None.

---

## Skipped Tests

None — J-01 and J-04 were intentionally excluded from this run per the lean-mode dispatch (covered by deterministic replay separately) and are not reported here as skipped test cases.

---

## Golden replay scripts written

- `runs/goal-session-market-compass/journey-scripts/J-10.json` — replays `/stocks/AVB?asof=2026-08-12` (expects `$187.89`) then `/stocks/AVB?asof=2026-08-11` (expects `$187.94`). Linted clean via `demo_runner.py --mode lint`.
- `runs/goal-session-market-compass/journey-scripts/J-11.json` — replays `/?asof=2026-08-12` and `/?asof=2026-08-11`, both expecting the `Basis: rebuilt` disclosure text. Linted clean via `demo_runner.py --mode lint`.

---

## Environment

- **Frontend URL:** http://localhost:3255 (booted against the disposable clone via `TRENDORA_CONFIG`)
- **Backend URL:** http://localhost:8255 (verified: only DB file descriptors open are the clone at `runs/goal-market-compass-iter-23/verify-clone/trendora-clone.db*`; canonical `apps/backend/data/trendora.db` not open)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned profile
- **Test Date:** 2026-08-27
- **Evidence directory:** `reports/qa/goal-market-compass-iter-23-evidence/`

## Reminder for whichever agent finishes this iteration last

Per the dev handoff's Known Issue #2: `runs/goal-market-compass-iter-23/verify-clone/` (the
7.8 GB disposable clone + verification config) should be discarded (`rm -rf`) once QA/audit
are done with it — I did NOT delete it, since the auditor may still need the same running
backend/clone for its own review pass.
