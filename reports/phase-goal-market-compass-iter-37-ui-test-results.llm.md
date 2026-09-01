# Goal Iteration 37 (market-compass) — UI Test Results

**Phase:** goal-market-compass-iter-37
**Date:** 2026-09-01
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- Goal-mode dispatch: this run tested UT-J-09 (explicitly required regression journey,
     dispatched via goal-slice-bqa.md) and UT-J-13 (this iteration's evidence target — the
     ui-test-plan requires a freshly captured, measured-non-blank acceptance screenshot
     because iter-36's own capture was a failed single-colour PNG). J-01, J-02, J-03, J-04,
     J-05, J-06, J-07, J-08, J-10, J-11, J-12 were explicitly excluded from this browser-QA
     pass per the dispatch's "GOAL-MODE REGRESSION LANES" instruction — deterministic golden
     replay already re-verified them this run; their rows merge in separately. -->

**Overall:** 2/2 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-09 | The backend fits the host (regression — evidence-based, walkthrough waived) | regression | P1 | (1) live `/proc/<pid>/status` `VmPeak_kB` ≤ 2,621,440 kB; (2) `reports/perf-budgets.md`'s newest addendum is still Addendum 45 (2026-09-01, market-compass iter-34, "J-09 closing re-measurement"), recording ≤ 2,621,440 kB, no addendum regressed or went missing; (3) `git diff --stat reports/perf-budgets.md` shows zero diff this iteration | (1) Live backend (pid 68389, port 8255, `uvicorn main:app --host 0.0.0.0 --port 8255`): `VmPeak: 2292200 kB` — 329,240 kB (12.56%) under the 2,621,440 kB target. (2) `grep -n "^## Addendum" reports/perf-budgets.md` confirms Addendum 45 (line 12822) is still the last/newest heading in the file (46 addenda total, sequential, none missing) — its developer-run table states 2,307,092 kB (-11.99% vs target) and its auditor-run subsection states 2,305,668 kB (-12.05% vs target), both well under the bar. (3) `git status --porcelain -- reports/perf-budgets.md` and `git diff --stat HEAD -- reports/perf-budgets.md` are both empty — zero diff. Additionally confirmed this iteration's actual code touch is scoped exactly as the precondition states: `git diff --stat HEAD -- apps/backend/ config.yaml` shows only `apps/backend/app/engine/compass.py` (18 lines) and `apps/backend/tests/test_manifest_invariants.py` (47 lines) changed — `config.yaml`, `warmup.py`, `prices.py` untouched, so no memory-affecting code path moved this round. | PASS | none (evidence-based journey — no UI acceptance state to screenshot, per this journey's own `docs/goal.md` "Walkthrough: waived" marker and the test plan's own framing) |
| UT-J-13 | Leadership rotation shows both directions with signed deltas — this iteration's evidence target (fresh screenshot required) | regression | P1 | `/` renders a served `session_delta.rotation` block (not a client-side filter of `changes`) with two labelled, signed, both-directions sides per group kind (sector, theme), zero stock-kind rows, honest per-side empty states, complete accounting (`shown + suppressed + residual == configured_total`), signed `delta`/`direction_word` also on `session_delta.changes` sector/theme entries, What-changed unchanged, an honest no-prior-run state at the earliest stored session, and — specifically this iteration — a freshly captured acceptance screenshot that `PIL.Image.getcolors()` measures as more than one distinct colour | All assertions verified true against the live frontend (`http://localhost:3255/`) and cross-checked against `GET /api/compass`, `GET /api/sectors?as_of=`, `GET /api/themes?as_of=` on the backend (`:8255`) — see detail below. The acceptance screenshot was re-captured this iteration and measured: 1683×4320 px, **13,647 distinct colours** (`PIL.Image.getcolors()`), 693,670 bytes — comparable to healthy sibling captures in the same evidence directory and definitively NOT the iter-36 single-colour failure. | PASS | `reports/qa/goal-market-compass-iter-37-evidence/UT-J-13-rotation-both-directions.png` |

---

## Passed Tests

### UT-J-09 — The backend fits the host
**Verdict:** PASS
**Evidence:** none (evidence-based journey — no UI surface; `reports/perf-budgets.md` and the live backend process are the evidence, per this journey's own `docs/goal.md` "Walkthrough: waived" marker)

Steps executed (numbered steps from J-09's own `docs/goal.md` Acceptance, via `runs/goal-market-compass-iter-37/goal-slice-bqa.md`):

1. **Live VmPeak read.** `pgrep -af uvicorn` found one running backend: pid 68389, `uvicorn main:app --host 0.0.0.0 --port 8255 --app-dir .../apps/backend --limit-concurrency 64 --timeout-keep-alive 65 --timeout-graceful-shutdown 120` (also confirmed live via `GET /api/health` → `{"status":"ok","db_ok":true,...}`). `grep -E "VmPeak|VmRSS" /proc/68389/status` → `VmPeak: 2292200 kB`, `VmRSS: 934000 kB`. `2,292,200 ≤ 2,621,440` — PASS, 329,240 kB / 12.56% of margin under the 2.5 GB target.
2. **Newest addendum check.** `grep -n "^## Addendum" reports/perf-budgets.md` lists 46 sequential addenda (Addendum 16 through Addendum 45, no gaps in the visible numbering, no duplicate/renumbered entries) with Addendum 45 (line 12822, "2026-09-01T06:50:54Z-06:57:03Z UTC developer run, market-compass iter-34 — J-09 closing re-measurement") still the LAST heading in the 13,064-line file — nothing newer was appended and nothing was removed. Its own tables record 2,307,092 kB (developer run, -11.99% vs the 2,621,440 kB target) and 2,305,668 kB (auditor run, -12.05% vs target), both clearing the bar with wide margin, consistent with (and slightly better than) today's fresh live read.
3. **Zero diff this iteration.** `git status --porcelain -- reports/perf-budgets.md` → empty (clean). `git diff --stat HEAD -- reports/perf-budgets.md` → empty (no diff). Confirms this closing/regression round did not touch the file. Cross-checked the precondition's own scope claim: `git diff --stat HEAD -- apps/backend/ config.yaml` shows exactly the two files the test plan names (`compass.py` 18 lines, `test_manifest_invariants.py` 47 lines) changed this iteration — `config.yaml` (where `database.pragmas.cache_size` lives) and the warmup/prices engine files are untouched, so nothing in this iteration's own diff could have moved the measured figure.

All three Expected-Result bullets hold. No memory-affecting code path or perf-budget record was touched this iteration; the live measurement independently reconfirms Addendum 45's closed state.

---

### UT-J-13 — Leadership rotation shows both directions with signed deltas
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-37-evidence/UT-J-13-rotation-both-directions.png` (1683×4320, 13,647 distinct colours, 693,670 bytes — full-page capture)

**Screenshot-capture note (relevant to why this journey needed a fresh pass this iteration):** the browser tool's `screenshot` action returned a single-colour (background-only) frame every time it was taken after a JS-driven scroll (`element.scrollIntoView()`, `window.scrollTo()`) or after the tool's own `scroll`/`hover` actions moved the page to bring the Leadership rotation section into the normal 1683×1260 viewport — reproducing the exact iter-36 failure signature (verified: those attempts measured 1 distinct colour, background RGB `(18,22,27)`, ~9.4 KB, matching iter-36's failed file almost byte-for-byte). CDP-level `scroll` additionally errored outright (`Page session timeout: Input.dispatchMouseEvent`) in this environment. The reliable fix: `set_viewport` to `1683×4320` (the page's full document height, capped by the tool's 4320 px viewport ceiling) so the ENTIRE page — including the Leadership rotation section — renders inside one screenshot with no scroll involved at all. That capture is valid (13,647 distinct colours) and is the evidence filed above. This is recorded as a tooling finding for future iterations, not a product defect — the live DOM/API content was correct throughout, only the screenshot mechanism needed a different capture strategy.

Steps executed (J-13 numbered steps from `docs/goal.md` / the iter-37 sliced goal and the test plan's UT-J-13, verified against the live frontier `as_of=2026-08-12`, prior `2026-08-11`, manifest v9):

1. Navigated to `/` (no `?asof`). Confirmed via `GET /api/compass` that `session_delta.rotation` is a genuinely SERVED top-level field (`rotation` key present with `sector`/`theme` sub-objects, each `{gaining:[...], losing:[...], shown_count, suppressed_count, residual_count, configured_total}`) — not a client-side filter of `session_delta.changes`. No `stock` key exists under `rotation` (only `sector`/`theme`), matching "zero stock-kind rows"; the page DOM likewise shows only Sector rotation / Theme rotation subsections, no stock rows, under the "Leadership rotation" heading.
2. "Sector rotation" subsection shows explicit "Gaining" (5 rows: Regional Banks (SPDR), Bitcoin Miners (Valkyrie), Real Estate, Banks (SPDR), Technology) and "Losing" (2 rows: Home Construction (iShares), Materials) badge-labelled columns side by side (`grep -c "Gaining\|Losing"` on the rendered HTML found exactly 2 of each — one Gaining/Losing pair for Sector, one for Theme). "Theme rotation" shows Gaining (Ai Data Centre) and Losing (Homebuilders), 1 each.
3. Row text format confirmed exactly as specified: **"Regional Banks (SPDR) 13 → 10 (-3) · improving"** (signed delta, falling rank = improving) and **"Home Construction (iShares) 21 → 25 (+4) · deteriorating"** (signed delta, rising rank = deteriorating) — both read verbatim off the rendered page and cross-checked byte-for-byte against `GET /api/compass`'s `rotation.sector.gaining[0]` (`{label:"Regional Banks (SPDR)", from:13, to:10, delta:-3, direction_word:"improving"}`) and `rotation.sector.losing[0]` (`{label:"Home Construction (iShares)", from:21, to:25, delta:4, direction_word:"deteriorating"}`).
4. Accounting lines read exactly: sector **"7 of 31 shown · 24 below threshold · 0 beyond the display cap."** (7+24+0=31, matches `config.etfs.sector` 11 + `industry` 20); theme **"2 of 11 shown · 9 below threshold · 0 beyond the display cap."** (2+9+0=11) — both close exactly against the configured group totals returned by the API's own `shown_count`/`suppressed_count`/`residual_count`/`configured_total` fields (7/24/0/31 and 2/9/0/11 respectively).
5. Spot-checked against `GET /api/sectors?as_of=<date>` and `GET /api/themes?as_of=<date>` directly (note: the query param is `as_of`, not `asof` — the frontend's own `?asof=` route param is a separate, page-level convention):
   - Regional Banks (SPDR) (ticker KRE): `rank` 13 at `as_of=2026-08-11` → 10 at `as_of=2026-08-12` — exact match to the rotation row (delta -3, improving).
   - Home Construction (iShares): `rank` 21 at `as_of=2026-08-11` → 25 at `as_of=2026-08-12` — exact match (delta +4, deteriorating).
   - Ai Data Centre theme: `rank` 9 at `as_of=2026-08-11` → 4 at `as_of=2026-08-12` — exact match (delta -5, improving).
   - Homebuilders theme: `rank` 5 at `as_of=2026-08-11` → 10 at `as_of=2026-08-12` — exact match (delta +5, deteriorating).
   All four spot-checked rows equal the stored sector/theme rank rows served independently by their own canonical endpoints (AG-3 satisfied).
6. What-changed card confirmed unchanged: still lists all 17 entries (5 sector, 2 theme, 10 stock — 0 market, 0 breadth this session) in Market → Breadth → Sectors → Themes → Stocks order, "Suppressed moves (36)" disclosure present, and the same signed `delta`/`direction_word` fields ride on the sector/theme `session_delta.changes[]` entries too (confirmed via API: `changes` entries of `kind:"sector"`/`"theme"` carry `delta`+`direction_word`; `market`/`breadth`/`stock` kind entries do not) — no duplication removed or altered What-changed's own content.
7. No-prior-run state: navigated to `/?asof=1996-01-02` (earliest possible date given the committed seed's `daily_prices` starts 1996-01-02). Rendered page text confirms all three honest empty-state sentences present and consistent: the regime/phase card's own no-comparison sentence, What-changed's **"This is the earliest stored session — there is no prior session to compare against."**, and Leadership rotation's own **"This is the earliest stored session — there is no prior session to compare rotation against."** — no deltas, no direction words, nothing fabricated.
8. Re-read the What-changed card at the default `/` view (step 8's re-check) — entries, ordering, and suppressed count unchanged from step 1's read, consistent with UT-J-02's own baseline.

No console errors observed (console-message capture reported "not yet implemented" in this browser-tool build, so this is an honest "not measured" rather than a confirmed-clean read — noted, not glossed over). No stray unavailable-backend state was hit at any point (backend on `:8255` reachable throughout, `readiness: ready` / preflight `GO` per `/api/health`).

---

## Failed Tests

None.

---

## Skipped Tests

None. Per this run's goal-mode dispatch, J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-10, J-11, J-12 were explicitly excluded from this browser-QA pass (already re-verified this run by deterministic golden replay from stored scripts) — they are not counted as SKIPPED here since testing them was out of scope for this dispatch, not blocked. Their rows merge into the combined results separately.

---

## Golden replay script

Re-verified and re-wrote `runs/goal-session-market-compass/journey-scripts/J-13.json` (7 steps: sector/theme rotation heading + specific row text + both accounting strings on the default `/` view, then the no-prior-run empty state at `?asof=1996-01-02`) — content is unchanged from the iter-36 version (this iteration's product code for J-13 is binding "Do not redo"), but every one of its 7 `expect` strings was independently re-confirmed against the live page and the live API this pass, and the file was overwritten so its mtime now reflects an actually-executed verification (unlike the pre-iter-37 state, where the script's mtime postdated the last replay that was meant to cover it). Linted clean:
`python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-market-compass/journey-scripts --journeys J-13` → `J-13 ok`.

No golden script was written for UT-J-09 — it is an evidence-based journey with no UI surface (backend process + `/proc` + a markdown report), which is out of scope for the browser-driven replay format.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (used directly for cross-check of served values and for the UT-J-09 process check; pid 68389)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned profile
- **Test Date:** 2026-09-01
- **Evidence directory:** `reports/qa/goal-market-compass-iter-37-evidence/`
- **Frontier manifest observed:** `as_of=2026-08-12`, `prior_as_of=2026-08-11`, manifest version 9 (at_ingest, not prospective-eligible)
