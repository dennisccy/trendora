# Goal Iteration 36 (market-compass) — UI Test Results

**Phase:** goal-market-compass-iter-36
**Date:** 2026-09-01
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- Lean goal-mode dispatch: only J-13 was in scope for this run (target journey).
     J-02, J-04, J-05, J-06, J-07, J-08, J-12 are verified separately by deterministic golden replay. -->

**Overall:** 1/1 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-13 | Leadership rotation says which way, shows both directions, and stops repeating What-changed | happy-path | P1 | `/` renders a served `session_delta.rotation` block (not a client-side filter of `changes`) with two labelled, signed, both-directions sides per group kind (sector, theme), zero stock-kind rows, honest per-side empty states, complete accounting (`shown + suppressed + residual == configured_total`), signed `delta`/`direction_word` also on `session_delta.changes` sector/theme entries, What-changed unchanged, and an honest no-prior-run state at the earliest stored session | All assertions verified true against the live frontend (`http://localhost:3255/`) and cross-checked against `GET /api/compass`, `GET /api/sectors`, `GET /api/themes` on the backend (`:8255`) — see detail below | PASS | `reports/qa/goal-market-compass-iter-36-evidence/UT-J-13-rotation-both-directions.png` |

---

## Passed Tests

### UT-J-13 — Leadership rotation says which way, shows both directions, and stops repeating What-changed
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-36-evidence/UT-J-13-rotation-both-directions.png`

Steps executed (J-13 numbered steps from `docs/goal.md` / iteration-36 sliced goal, verified against the live frontier `as_of=2026-08-12`, prior `2026-08-11`, manifest v9):

1. **Served block, no stock rows.** Navigated to `/` (default, no `?asof`). The Leadership rotation section DOM (`data-testid="compass-leadership-rotation-section"`) contains only `compass-leadership-rotation-{sector,theme}-{gaining,losing}[-list|-empty]` and `-accounting` testids — inspected via `document.querySelectorAll('[data-testid]')` scoped to the section — zero stock-kind testids/rows present. Confirmed via `GET /api/compass` that `session_delta.rotation` is a genuinely served block (not a client-side derivation): `sector.gaining` has 5 rows, `sector.losing` 2, `theme.gaining` 1, `theme.losing` 1 — all present as first-class response fields.
2. **Two labelled sides per kind, capped, ordered, thresholded.** Rendered page shows "Sector rotation" with explicit "Gaining" (5 rows: Regional Banks (SPDR), Bitcoin Miners (Valkyrie), Real Estate, Banks (SPDR), Technology) and "Losing" (2 rows: Home Construction (iShares), Materials) sub-sections, each capped at `rotation_top_k=5` (config.yaml:1424) and ordered most-moved-first (|delta| 3,3,3,2,2 for gaining). "Theme rotation" shows Gaining (Ai Data Centre) and Losing (Homebuilders), 1 each — both under the cap. Every row's `|delta|` clears `rank_move_min=2` (config.yaml:1421).
3. **Signed delta + served direction_word.** Rows render e.g. "Regional Banks (SPDR) 13 → 10 (-3) · improving" and "Home Construction (iShares) 21 → 25 (+4) · deteriorating" — a falling rank number (13→10) is labelled "improving", a rising one (21→25) "deteriorating", matching the spec's polarity rule. Confirmed via `GET /api/compass` that the identical signed `delta` + `direction_word` values also ride on the corresponding `session_delta.changes[]` entries for sector/theme kind (e.g. `{"label":"Regional Banks (SPDR)","delta":-3,"direction_word":"improving"}` appears in both `session_delta.rotation.sector.gaining` and `session_delta.changes`), while `market`/`breadth`/`stock` kind change entries carry no such fields (scoped correctly per the iteration's logged assumption).
4. **Complete accounting.** Sector accounting text: "7 of 31 shown · 24 below threshold · 0 beyond the display cap." (7+24+0=31, matches `config.etfs.sector` 11 + `industry` 20 = 31). Theme accounting: "2 of 11 shown · 9 below threshold · 0 beyond the display cap." (2+9+0=11). Both close exactly against configured totals — no above-threshold mover silently dropped (the iteration's own measured pre-fix gap, 29/31 for sector, is now 31/31 accounted for, with 0 in residual on this particular frontier snapshot since no mover fell beyond the cap).
5. **Spot-check against `GET /api/sectors` / `GET /api/themes`.** Queried `as_of=2026-08-12` and `as_of=2026-08-11` directly:
   - Regional Banks (SPDR)/KRE: prev rank 13 → cur rank 10 (rotation row: from 13, to 10, delta -3, "improving") — exact match.
   - Home Construction (iShares)/ITB: prev rank 21 → cur rank 25 (rotation row: from 21, to 25, delta +4, "deteriorating") — exact match.
   - Ai Data Centre theme: prev rank 9 → cur rank 4 (rotation row: from 9, to 4, delta -5, "improving") — exact match.
   - Homebuilders theme: prev rank 5 → cur rank 10 (rotation row: from 5, to 10, delta +5, "deteriorating") — exact match.
   All four spot-checked rows equal the stored sector/theme rank rows served independently by their own canonical endpoints (AG-3 satisfied).
6. **What-changed unchanged.** The What-changed card above the rotation section still lists all 17 entries (5 sector, 2 theme, 10 stock) in `Sector → Theme → Stock` order (no market/breadth changes this session — consistent with market/breadth being "little changed" and below their own thresholds), same "Suppressed moves (36)" disclosure, values matching what the rotation section's own sector/theme rows report — no duplication removed any What-changed content, and no new content was added to it.
7. **No-prior-run state.** Navigated to `/?asof=1996-01-02` (earliest possible date given the committed seed's `daily_prices` starts 1996-01-02, so this as-of has no prior session by construction). Rendered page confirms: regime "Choppy 50.00/100 NA", market phase "Not enough history to derive a market phase for this date — reported NA, never fabricated", What-changed card: "This is the earliest stored session — there is no prior session to compare against." (Suppressed moves (0)), and Leadership rotation section: "This is the earliest stored session — there is no prior session to compare rotation against." — no deltas, no direction words, nothing fabricated, and consistent in wording/honesty with the What-changed card's own no-prior-run state (backend confirms `session_delta.prior_as_of` is `null` at this date and the frontend's `noPriorRun` branch, read from source, takes precedence over the separate "rotation not recorded" branch so no stale zeroed rotation object is ever rendered as if it were real data).

No console errors observed. No stray `AlertTriangle`/unavailable-backend state was hit at any point (backend on `:8255` reachable throughout).

**Dev-handoff citation (step 8, informational only — not a browser assertion):** not verified by this browser QA pass; that is a text-citation requirement on `docs/handoffs/goal-market-compass-iter-36-dev.md`, out of browser-QA's scope.

---

## Failed Tests

None.

---

## Skipped Tests

None. Per this run's lean dispatch, J-02, J-04, J-05, J-06, J-07, J-08, J-12 were explicitly excluded from this browser-QA pass (verified separately by deterministic golden replay) — they are not counted as SKIPPED here since testing them was out of scope for this dispatch, not blocked.

---

## Golden replay script

Wrote `runs/goal-session-market-compass/journey-scripts/J-13.json` (7 steps: sector/theme rotation heading + specific row text + both accounting strings on the default `/` view, then the no-prior-run empty state at `?asof=1996-01-02`). Linted clean:
`python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-market-compass/journey-scripts --journeys J-13` → `J-13 ok`.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (used directly for cross-check of served values; `NEXT_PUBLIC_API_URL`-style default port 8000 is NOT what this run uses)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned profile
- **Test Date:** 2026-09-01
- **Evidence directory:** `reports/qa/goal-market-compass-iter-36-evidence/`
- **Frontier manifest observed:** `as_of=2026-08-12`, `prior_as_of=2026-08-11`, manifest version 9 (at_ingest, not prospective-eligible)
