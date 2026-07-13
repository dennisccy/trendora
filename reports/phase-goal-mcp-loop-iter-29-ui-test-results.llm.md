# Goal Iteration 29 — UI Test Results

**Phase:** goal-mcp-loop-iter-29
**Date:** 2026-07-13
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 5/5 tests passed (0 skipped)

**Scope note:** Per dispatch instructions, this run tests EXACTLY J-02, J-06, J-07, J-08, J-09 (the
five journeys re-scoped to outcome-neutral acceptance at the iter-28 plateau, commit `eb19cee`).
J-01, J-03, J-04, J-05, J-10, J-11, J-12, J-13, J-14 are intentionally NOT tested here — verified
separately by deterministic golden-script replay (see
`reports/phase-goal-mcp-loop-iter-29-regression-replay-results.md`).

**Data-state confirmation (load-bearing context):** `GET /api/evidence` was fetched directly before
browser testing began. `claims[]` has 7 entries, every `verdict.status` is `"FAIL"`, and
`proven_signals` is `{}` (zero PASS). This is the honest, sanctioned all-FAIL plateau the re-scoped
journeys exist to verify honest surfacing of — not a bug. Every percentage cited below as
"byte-matching" was cross-checked against this same raw JSON before the browser session started:

| Row (claim) | `control_excess` (raw) | Displayed % | Journey |
|---|---|---|---|
| `vcp_contraction` D10 h20 | -0.0037732016043003124 | -0.38% | J-06 |
| `vcp_contraction` D10 h60 | -0.016363899205616317 | -1.64% | J-07 |
| `rs_spy_3m:top:quintile × high_proximity:top:tertile` h20 | 8.030187730850894e-05 | +0.01% | J-08 |
| `rs_spy_3m` D10 h60 | -0.014155225763191797 | -1.42% | J-09 |

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | Drill into the evidence behind a score | regression | P1 | On `/stocks/{ticker}`, each score's inline evidence element honestly reads "Not yet proven", names the Evidence ledger as the audit path, and no proof panel renders | On `/stocks/AAPL`, all 3 scores (Leadership, Entry Quality, Risk) carry `data-testid="evidence-badge" data-proven="false"`, visible text "Not yet proven", tooltip "Not yet proven — no certified out-of-sample evidence backs this signal yet (see the Evidence ledger)." Badge is a non-interactive `<div>`; clicking it produced zero DOM change (verified by diffing pre/post-click HTML for "Why proven"/"holdout"/"control comparison"/"p-value" — all 0 occurrences, before and after). | PASS | `reports/qa/goal-mcp-loop-iter-29-evidence/J-02-stock-detail-badges.png` |
| UT-J-06 | vcp_contraction top-decile certified evidence outcome surfaced on Evidence + Research factor lab | regression | P1 | `/evidence` shows the vcp_contraction D10 h20 row badged FAIL with standard fields, byte-matching ≈-0.38%; `/research/factor-lab` vcp_contraction top-decile badge reads "Not yet proven" (`data-proven=false`) | `/evidence` row `id="factor-vcp_contraction-d10-h20"`: badge FAIL, "FAIL · holdout edge -0.38%", reason text byte-identical to API's `reason` field, Control comparison -0.38%, Registration date 2026-07-03, Forward-walk "Pending — monitored as new data matures", linkback "Backs: Research factor lab →" (href=/research/factor-lab). `/research/factor-lab` DOM: `data-testid="factor-evidence-badge" data-proven="false" data-factor="vcp_contraction" data-horizon="20"`. Page-wide: 0 occurrences of `data-proven="true"` or `>Proven<`. | PASS | `reports/qa/goal-mcp-loop-iter-29-evidence/J-06-evidence-row-vcp-h20.png` |
| UT-J-07 | Multi-horizon certified evidence outcome surfaced (the loop sees beyond the 20-day horizon) | regression | P1 | `/evidence` shows the vcp_contraction D10 h60 row badged FAIL, byte-matching ≈-1.64%; `/research/factor-lab` reads "Not yet proven" at EVERY horizon h1/h5/h10/h20/h60 | `/evidence` row `id="factor-vcp_contraction-d10-h60"`: badge FAIL, "FAIL · holdout edge -1.64%", reason byte-identical to API, Control comparison -1.64%, Registration date 2026-07-03, linkback "Backs: Research factor lab →". `/research/factor-lab` DOM: all 5 `data-factor="vcp_contraction"` badges (`data-horizon` = 1, 5, 10, 20, 60) carry `data-proven="false"` — confirmed by regex scan of the live DOM, and visually in the fullpage capture (1d/5d/10d/20d/60d all read "Not yet proven"). | PASS | `reports/qa/goal-mcp-loop-iter-29-evidence/J-07-factor-lab-expanded.png` |
| UT-J-08 | Multi-factor combination certified evidence outcome surfaced on the Combination lab + Evidence | regression | P1 | `/evidence` shows the composite (rs_spy_3m×high_proximity, h20) row badged FAIL, byte-matching ≈+0.01%, with "Backs: Multi-factor combination lab →"; `/research/factor-combination`, reproducing that exact combination, shows the composite badge reading "Not yet proven" and no combination anywhere reading "Proven" | `/evidence` row `id="combination-high_proximity-rs_spy_3m-h20"`: badge FAIL, "FAIL · holdout edge +0.01%", reason byte-identical to API, hypothesis `condition=rs_spy_3m:top:quintile,high_proximity:top:tertile`, Registration date 2026-07-03, linkback "Backs: Multi-factor combination lab →". Reproduced the exact cohort on `/research/factor-combination` (Condition 1 = Relative strength vs SPY (3m) / Top / Quintile, Condition 2 = Proximity to 52-week high / Top / Tertile, confirmed via the generated sample-drill URLs containing `condition=rs_spy_3m%3Atop%3Aquintile&condition=high_proximity%3Atop%3Atertile`): the "Combined (composite rank-blend)" badge carries `data-testid="combination-evidence-badge" data-proven="false" data-horizon="20" data-legs="rs_spy_3m:top:quintile,high_proximity:top:tertile"`, visible text "Not yet proven", tooltip explicitly naming the composite and the Evidence ledger. Page-wide: 0 occurrences of `data-proven="true"` or `>Proven<`. | PASS | `reports/qa/goal-mcp-loop-iter-29-evidence/J-08-factor-combination-lab.png` |
| UT-J-09 | Relative-strength (rs_spy_3m) 60-day-horizon certified evidence outcome surfaced on Evidence + Research factor lab | regression | P1 | `/evidence` shows the rs_spy_3m D10 h60 row badged FAIL, byte-matching ≈-1.42%, with the retired +21.34% value rendering NOWHERE; `/research/factor-lab` rs_spy_3m reads "Not yet proven" at all horizons | `/evidence` row `id="factor-rs_spy_3m-d10-h60"`: badge FAIL, "FAIL · holdout edge -1.42%", reason byte-identical to API, Control comparison -1.42%, Registration date 2026-07-03, linkback "Backs: Research factor lab →". Grepped the full `/evidence` page HTML for "21.34" and "+21.34%" — 0 occurrences (also 0 for the other retired values "0.0004998" and "6.36%"). `/research/factor-lab` DOM: all 5 `data-factor="rs_spy_3m"` badges (`data-horizon` = 1, 5, 10, 20, 60) carry `data-proven="false"` — confirmed by regex scan and visually in a dedicated crop showing all 5 horizon badges reading "Not yet proven". | PASS | `reports/qa/goal-mcp-loop-iter-29-evidence/J-09-factor-lab-rs-spy-3m-row.png` |

---

## Passed Tests

### UT-J-02 — Drill into the evidence behind a score
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-29-evidence/J-02-stock-detail-badges.png`

- Navigated `/stocks` → clicked through to `/stocks/AAPL`.
- All three score cards (Leadership "E" 55.78, Entry Quality "D" 69.70, Risk "E" 33.12) carry an
  inline badge: `<div data-testid="evidence-badge" data-proven="false" title="Not yet proven — no
  certified out-of-sample evidence backs this signal yet (see the Evidence ledger).">Not yet
  proven</div>`. The badge is a plain `<div>` (not a button/link) — non-interactive by construction.
- Clicked the first badge directly (`[data-testid="evidence-badge"]`); the interactive-element count
  (6 buttons / 1 input / 13 links) and the full-page HTML were unchanged before vs. after (diffed the
  two captured HTML snapshots for `Why proven`, `proof panel`, `>Proven<`, `certified-claim`,
  `holdout`, `control comparison`, `p-value` — all 0 both times). No proof panel or fabricated proof
  ever rendered.
- "Evidence ledger" (the audit-path text) appears exactly 3 times on the page (once per badge
  tooltip); "Evidence" is reachable in 1 click from anywhere via the persistent left nav.
- Matches the re-scoped J-02 acceptance exactly: honest "Not yet proven" state, correct explanatory
  text naming the ledger, no drill-down fabricated since no PASS claim backs any of the three scores
  (confirmed against the live `GET /api/evidence` payload fetched moments earlier: 0 PASS entries).

### UT-J-06 — vcp_contraction top-decile certified evidence outcome surfaced on Evidence + Research factor lab
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-29-evidence/J-06-evidence-row-vcp-h20.png` (dedicated
element crop) + `reports/qa/goal-mcp-loop-iter-29-evidence/evidence-ledger-fullpage.png` (full
`/evidence` ledger, all 7 rows) + `reports/qa/goal-mcp-loop-iter-29-evidence/J-06-J-07-J-09-factor-lab-fullpage.png`
(full `/research/factor-lab` table)

- `/evidence` row `id="factor-vcp_contraction-d10-h20"` (`data-testid="evidence-claim-row"`):
  hypothesis tags `decile=10 direction=positive factor=vcp_contraction horizon=20 kind=factor
  slice_kind=decile`; "Out-of-sample verdict: FAIL · holdout edge -0.38%"; reason text
  "holdout edge -0.003773 is not in the claimed positive direction / does not beat the control
  out-of-sample" — byte-identical to the `reason` field in the raw `GET /api/evidence` JSON; Control
  comparison (vs SPY) -0.38%; Registration date 2026-07-03; Forward-walk score-to-date "Pending —
  monitored as new data matures"; linkback `<a href="/research/factor-lab"
  data-testid="evidence-claim-linkback">Backs: Research factor lab →</a>`.
- `/research/factor-lab` "Volatility contraction (VCP-style)" row, h20 cell:
  `data-testid="factor-evidence-badge" data-proven="false" data-factor="vcp_contraction"
  data-horizon="20"`, visible "Not yet proven".
- Whole-page scan of `/research/factor-lab`: 110 occurrences of "Not yet proven", 55 of
  `data-proven="false"`, **0** of `data-proven="true"` and **0** of `>Proven<` — no factor's cohort
  anywhere on the page reads "Proven".
- Matches the re-scoped J-06 acceptance: single source (`GET /api/evidence`), byte-matching numbers,
  honest "Not yet proven" state, linkback present.

### UT-J-07 — Multi-horizon certified evidence outcome surfaced (the loop sees beyond the 20-day horizon)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-29-evidence/J-07-factor-lab-expanded.png` +
`reports/qa/goal-mcp-loop-iter-29-evidence/evidence-ledger-fullpage.png` +
`reports/qa/goal-mcp-loop-iter-29-evidence/J-06-J-07-J-09-factor-lab-fullpage.png`

- `/evidence` row `id="factor-vcp_contraction-d10-h60"`: horizon tag `horizon=60`, subtitle
  "Out-of-sample edge — factor top decile · 60-day hold"; "FAIL · holdout edge -1.64%"; reason
  "holdout edge -0.01636 is not in the claimed positive direction / does not beat the control
  out-of-sample" — byte-identical to the API; Control comparison -1.64%; Registration date
  2026-07-03; linkback "Backs: Research factor lab →".
- `/research/factor-lab` "Volatility contraction (VCP-style)" row: regex-scanned the live DOM for
  `data-testid="factor-evidence-badge" data-proven="false" data-factor="vcp_contraction"
  data-horizon="N"` across N = 1, 5, 10, 20, 60 — all five present, all `data-proven="false"`. The
  fullpage capture visually confirms all five horizon badges (1d/5d/10d/20d/60d) read "Not yet
  proven" for this factor.
- Matches the re-scoped J-07 acceptance: the non-20 (h60) claim row renders with the recorded FAIL
  verdict and byte-matching numbers, and EVERY horizon on the factor-lab badge reads "Not yet proven"
  (none reads "Proven").

### UT-J-08 — Multi-factor combination certified evidence outcome surfaced on the Combination lab + Evidence
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-29-evidence/J-08-factor-combination-lab.png` +
`reports/qa/goal-mcp-loop-iter-29-evidence/evidence-ledger-fullpage.png`

- `/evidence` row `id="combination-high_proximity-rs_spy_3m-h20"`: hypothesis tags
  `cohort=composite condition=rs_spy_3m:top:quintile,high_proximity:top:tertile direction=positive
  horizon=20 kind=combination ledger=canonical`; "FAIL · holdout edge +0.01%"; reason "holdout edge
  +8.03e-05 is not significant after multiple-testing deflation (p=0.4943 >= alpha/6=0.008333)" —
  byte-identical to the API; Control comparison +0.01%; Registration date 2026-07-03; linkback
  "Backs: Multi-factor combination lab →" (href=/research/factor-combination).
- On `/research/factor-combination`, reproduced the exact pre-registered cohort: set Condition 1 =
  Relative strength vs SPY (3m) / Top / Quintile (the page's default) and Condition 2 = Proximity to
  52-week high / Top / Tertile (changed the factor dropdown from the page's ATR% default, then
  toggled the Side control to Top — confirmed via the generated sample-drill links updating to
  `condition=rs_spy_3m%3Atop%3Aquintile&condition=high_proximity%3Atop%3Atertile`). The "Combined
  (composite rank-blend)" row's badge: `data-testid="combination-evidence-badge"
  data-proven="false" data-horizon="20" data-legs="rs_spy_3m:top:quintile,high_proximity:top:tertile"`,
  title "Not yet proven — no certified out-of-sample evidence backs this composite
  (rs_spy_3m:top:quintile + high_proximity:top:tertile) at the 20-day horizon yet (see the Evidence
  ledger)." Screenshot shows the badge reading "Not yet proven" beside the composite row.
- Whole-page scan of the reproduced `/research/factor-combination` view: **0** occurrences of
  `data-proven="true"` or `>Proven<` — no combination anywhere on the page reads "Proven".
- Matches the re-scoped J-08 acceptance: single source, byte-matching numbers, honest "Not yet
  proven" state on the exact pre-registered §4.2 cohort (never an ad-hoc data-mined one), linkback
  present.

### UT-J-09 — Relative-strength (rs_spy_3m) 60-day-horizon certified evidence outcome surfaced on Evidence + Research factor lab
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-29-evidence/J-09-factor-lab-rs-spy-3m-row.png`
(dedicated crop, all 5 horizons) + `reports/qa/goal-mcp-loop-iter-29-evidence/evidence-ledger-fullpage.png`

- `/evidence` row `id="factor-rs_spy_3m-d10-h60"`: hypothesis tags `decile=10 direction=positive
  factor=rs_spy_3m horizon=60 kind=factor ledger=canonical slice_kind=decile`; "FAIL · holdout edge
  -1.42%"; reason "holdout edge -0.01416 is not in the claimed positive direction / does not beat the
  control out-of-sample" — byte-identical to the API; Control comparison -1.42%; Registration date
  2026-07-03; linkback "Backs: Research factor lab →".
- Grepped the full rendered `/evidence` page for the retired pre-refresh values: "21.34" → 0
  occurrences, "+21.34%" → 0, "0.0004998" → 0, "6.36%" → 0. The retired value renders nowhere.
- `/research/factor-lab` "Relative strength vs SPY (3m)" row: regex-scanned the live DOM —
  `data-testid="factor-evidence-badge" data-proven="false" data-factor="rs_spy_3m"
  data-horizon="N"` present and `false` for N = 1, 5, 10, 20, 60 (h60 AND the four untested
  horizons all honestly "Not yet proven"). The dedicated crop shows the full row: 1d/5d/10d/20d/60d
  all reading "Not yet proven".
- Matches the re-scoped J-09 acceptance: h60 claim row renders the recorded FAIL verdict with
  byte-matching numbers, the retired value is gone, and every horizon on the factor-lab badge is
  honestly "Not yet proven".

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Independent deterministic-replay confirmation

Wrote self-contained golden replay scripts for all five journeys to
`runs/goal-session-mcp-loop/journey-scripts/{J-02,J-06,J-07,J-08,J-09}.json` immediately after each
journey passed live. Linted all five (`demo_runner.py --mode lint`) — all OK — then ran them through
the real, model-free Playwright runner (`demo_runner.py --mode verify`) against the live frontend
(`http://localhost:3255`):

```
[demo_runner] verify: 5 journey(s), 0 failed (verdict: PASS)
```

This is an independent, objective confirmation of the exact ledger text and byte-matching values
above — not just my own browser observations. Per the iter-28 lesson, all five scripts deliberately
assert only against `/evidence` (fast, sub-second) rather than driving the `/research/factor-lab` /
`/research/factor-combination` UI interactions (select-dropdown + Top/Bottom toggle changes, which
the runner's `goto`/`click`/`fill` vocabulary cannot reproduce for `<select>` elements, and which take
tens of seconds to compute on the deep 30-year/548-symbol basis — well past the replay runner's
20-second hard per-step timeout). The slow-page `data-proven` checks (factor-lab all-horizon badges,
factor-combination composite badge) were performed live in this session via direct DOM/attribute
inspection (see per-test notes above) and are not part of the golden scripts.

**Note on the replay tool's own evidence screenshots:** `demo_runner.py --mode verify` additionally
wrote `J-02-verify.png` .. `J-09-verify.png` into the evidence directory. `J-06-verify.png`,
`J-07-verify.png`, `J-08-verify.png`, and `J-09-verify.png` are md5-identical to each other (and to
the unrelated `J-04-verify.png`/`J-05-verify.png` from the separate regression-replay run) — the
runner takes one end-state screenshot per journey and all four scripts end on the same unscrolled
`/evidence` page, so the captured frame is pixel-identical across journeys. This is expected tool
behavior, not a masked failure (the underlying text `expect` assertions inside each script are
independent, journey-specific, and all held — see the PASS verdict above), but per the
md5-distinctness requirement in the iteration spec, **the Evidence column above cites my own
dedicated captures** (`J-02-stock-detail-badges.png`, `J-06-evidence-row-vcp-h20.png`,
`J-07-factor-lab-expanded.png`, `J-08-factor-combination-lab.png`,
`J-09-factor-lab-rs-spy-3m-row.png`), which were confirmed md5-distinct from one another and from
every other file in the evidence directory before being cited.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (confirmed 200 on `/api/health` and `/api/evidence` before
  testing began; both services reported up and warm by the coordinator)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`) for live
  investigation; Chromium via Playwright (`demo_runner.py --mode verify`) for the deterministic
  golden-script replay
- **Test Date:** 2026-07-13
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-29-evidence/`
- **Journeys intentionally NOT tested this run** (per dispatch instructions — verified separately by
  deterministic golden-script replay): J-01, J-03, J-04, J-05, J-10, J-11, J-12, J-13, J-14.
- **No backend restart/rebuild was performed or requested.** No "Rebuild snapshots" job was
  triggered. No form submitted any data, no ledger file was written, no `## Evidence Claim` was
  registered — this was a read-only verification pass end to end, consistent with the iteration's
  zero-diff, verify-only scope.
