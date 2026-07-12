# Phase goal-mcp-loop-iter-28 — UI Test Results

**Phase:** goal-mcp-loop-iter-28
**Date:** 2026-07-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS rationale: iter-28 is a zero-code plateau-assessment iteration. The five
     evidence-frontier journeys under assessment (J-02, J-06, J-07, J-08, J-09) are
     genuinely all-FAIL on the referee ledger (7/7 canonical claims FAIL, confirmed
     live via GET /api/evidence: proven_signals={}) — this is the sanctioned, honest
     product state per iter-28's spec and anti-goal #1 (no unbacked "Proven"). Per
     the dispatch coordinator's explicit instruction, these journeys are judged on
     whether the UI HONESTLY reflects that state, not on whether an edge is Proven.
     All six tested journeys (J-01, J-02, J-06, J-07, J-08, J-09) verified PASS on
     that honest-state standard: every score/claim/cohort that is not proven reads
     "Not yet proven" (data-proven="false"), the Evidence ledger shows full,
     byte-matching FAIL-verdict cards for all 7 claims with correct linkbacks, and
     the specific cohorts targeted by J-06/J-07/J-08/J-09 are wired end-to-end
     (ledger row <-> lab badge) and correctly show "Not yet proven" rather than a
     fabricated "Proven". Nothing anywhere reads "Proven" without a backing PASS
     claim (grep-verified zero standalone "Proven" occurrences across /stocks,
     /stocks/MU, /evidence, /research/factor-lab, /research/factor-combination).
     All 6 journeys additionally passed a real, deterministic Playwright replay of
     their golden scripts against the live frontend (6/6, 0 failed) — objective,
     model-free confirmation. -->

**Overall:** 6/6 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Every score shows an evidence status | smoke | P1 | No score on the leaderboard is presented without a visible evidence status | `/stocks` rendered 541/541 rows; every Leadership/Entry Quality/Risk score cell carries an evidence badge; grep of the raw DOM found 3,246 "Not yet proven" badge instances and 0 standalone "Proven" instances — every score has a status, none lack one | PASS | `reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-01-stocks-leaderboard.png`, `J-01-verify.png` |
| UT-J-02 | Drill into the proof behind a score | happy-path | P1 | User can see why a score is considered proven/not-proven — the test, the controls, and the date | No "Proven" badge exists anywhere in the product (`GET /api/evidence` → `proven_signals={}`, confirmed live) — the drill-down mechanism is honest, not broken: `/stocks/MU`'s score badges are non-interactive `<div>`s with an honest tooltip ("Not yet proven — no certified out-of-sample evidence backs this signal yet"), and `/evidence` fully displays the drill-down structure for `leadership_score` (hypothesis tags, OUT-OF-SAMPLE VERDICT with holdout edge -0.03% byte-matching the API's -0.00031360673077383193, CONTROL COMPARISON (VS SPY), REGISTRATION DATE 2026-07-03, FORWARD-WALK) — the "why" is fully visible, it honestly says FAIL rather than fabricating PASS | PASS (see note) | `reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-02-J-05-J-06-J-07-J-09-evidence-ledger-full.png`, `J-02-verify.png` |
| UT-J-06 | vcp_contraction top-decile certified edge surfaced on Evidence + Research factor lab | happy-path | P1 | New vcp_contraction (D10, h20) claim renders on `/evidence` with standard fields + linkback; factor-lab cohort shows "Proven" only if PASS, else honestly "Not yet proven" | `/evidence` shows a `vcp_contraction — top decile (D10)` FAIL card: tags `decile=10 direction=positive factor=vcp_contraction horizon=20 kind=factor slice_kind=decile`, verdict "FAIL · holdout edge -0.38%" (byte-matches API `-0.0037732016043003124`), control comparison -0.38%, registration date 2026-07-03, "Backs: Research factor lab →". On `/research/factor-lab`, the vcp_contraction row's h20 evidence badge has `data-testid="factor-evidence-badge" data-proven="false" data-factor="vcp_contraction" data-horizon="20"` — correctly "Not yet proven", not fabricated | PASS (see note) | `reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-02-J-05-J-06-J-07-J-09-evidence-ledger-full.png`, `UT-J-06-factor-lab-loaded.png`, `J-06-verify.png` |
| UT-J-07 | Multi-horizon certified edge surfaced (non-20 horizon) | happy-path | P1 | Non-20-horizon claim (vcp_contraction h60) certified through the gate BEFORE code; renders on `/evidence`; factor-lab h60 cohort badge Proven only if PASS | `/evidence` shows a second `vcp_contraction — top decile (D10)` card subtitled "· 60-day hold", tags include `horizon=60` and `ledger=canonical`, verdict "FAIL · holdout edge -1.64%" (byte-matches API `-0.016363899205616317`), registration date 2026-07-03, "Backs: Research factor lab →". Factor-lab h60 badge: `data-proven="false" data-factor="vcp_contraction" data-horizon="60"` — honestly "Not yet proven" (uncertified horizons h1/h5/h10/h20 also correctly all "Not yet proven", confirmed via DOM scan) | PASS (see note) | `reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-02-J-05-J-06-J-07-J-09-evidence-ledger-full.png`, `UT-J-06-factor-lab-loaded.png`, `J-07-verify.png` |
| UT-J-08 | Multi-factor combination certified edge surfaced on Combination lab + Evidence | happy-path | P1 | Pre-registered combination claim renders on `/evidence`; Combination lab reproduces the exact legs and shows Proven only if PASS | `/evidence` shows `rs_spy_3m × high_proximity — composite`, tag `condition=rs_spy_3m:top:quintile,high_proximity:top:tertile`, verdict "FAIL · holdout edge +0.01%" (byte-matches API `8.030187730850894e-05`), "Backs: Multi-factor combination lab →". Live-reconfigured `/research/factor-combination` to the exact certified legs (leg1 rs_spy_3m/Top/Quintile default + leg2 changed to Proximity to 52-week high/Top/Tertile); the resulting "Combined (composite rank-blend)" badge has `data-proven="false" data-legs="rs_spy_3m:top:quintile,high_proximity:top:tertile" data-horizon="20"` — exact match to the certified cohort, honestly "Not yet proven" | PASS (see note) | `reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-08-combination-lab-initial.png`, `UT-J-08-combo-configured-recheck.png`, `J-08-verify.png` |
| UT-J-09 | Relative-strength (rs_spy_3m) 60-day-horizon certified edge surfaced on Evidence + Research factor lab | happy-path | P1 | rs_spy_3m h60 claim (promoted from staging) renders on `/evidence`; factor-lab h60 cohort badge Proven only if PASS, other horizons Not yet proven | `/evidence` shows `rs_spy_3m — top decile (D10)` subtitled "· 60-day hold", tags include `factor=rs_spy_3m horizon=60`, verdict "FAIL · holdout edge -1.42%" (byte-matches API `-0.014155...`), registration date 2026-07-03, "Backs: Research factor lab →". Factor-lab rs_spy_3m badge: all 5 horizons (1/5/10/20/60) confirmed `data-proven="false"` via DOM scan — honestly "Not yet proven" throughout, no stale +21.34% value rendered anywhere | PASS (see note) | `reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-02-J-05-J-06-J-07-J-09-evidence-ledger-full.png`, `J-09-verify.png` |

---

## Passed Tests

### UT-J-01 — Every score shows an evidence status
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-01-stocks-leaderboard.png`

Visited `/stocks`. The leaderboard rendered 541/541 rows. Every row's Leadership, Entry
Quality, and Risk score each carry a small badge directly beneath the score number reading
"Not yet proven" (grey/muted styling, non-clickable `<div>`, tooltip: "Not yet proven — no
certified out-of-sample evidence backs this signal yet (see the Evidence ledger)."). Raw DOM
scan: 3,246 instances of the exact text "Not yet proven", 0 instances of a standalone
"Proven" badge. This matches the honest all-FAIL ledger state (`GET /api/evidence` →
`proven_signals={}`). No score is missing a status badge.

### UT-J-02 — Drill into the proof behind a score
**Verdict:** PASS (see note)
**Evidence:** `reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-02-J-05-J-06-J-07-J-09-evidence-ledger-full.png`

**Note on the literal test-plan wording:** J-02's steps assume a score carries a "Proven"
badge to click. I confirmed directly (`GET /api/evidence` → `"proven_signals": {}`, plus a
full-page DOM/HTML scan of `/stocks`, `/stocks/MU`, and `/evidence`) that **no such badge
currently exists anywhere in the product** — all 7 canonical claims are FAIL. This is the
correct, sanctioned state for this iteration (iter-28 is a verify-only plateau-assessment
pass that registers zero new evidence claims; the coordinator's explicit instruction is not
to fail this class of journey merely because no edge is Proven). What I verified instead is
that the underlying "prove it" *mechanism* is itself honest and complete, not broken or
fabricated:
- On `/stocks/MU`, each score's evidence badge is a non-interactive `<div>` (not a link/
  button — confirmed via DOM: `isLink:false`, no `href`) whose `title` attribute honestly
  explains the absence of proof: "Not yet proven — no certified out-of-sample evidence backs
  this signal yet (see the Evidence ledger)." There is no fake "Why proven?" panel.
- On `/evidence`, the `leadership_score` claim card displays the FULL drill-down structure
  the journey asks for — HYPOTHESIS tags, OUT-OF-SAMPLE VERDICT ("FAIL · holdout edge
  -0.03%", with the full reason string), CONTROL COMPARISON (VS SPY) "-0.03%", REGISTRATION
  DATE "2026-07-03", and FORWARD-WALK SCORE-TO-DATE — i.e. the test, the controls, and the
  date are all visible and auditable; the answer to "why" is honestly "it failed
  out-of-sample," not a fabricated confident number.
- Values byte-match the live API: `-0.00031360673077383193 * 100 = -0.0314%` rounds to the
  displayed "-0.03%".

### UT-J-06 — vcp_contraction top-decile certified edge surfaced on Evidence + Research factor lab
**Verdict:** PASS (see note)
**Evidence:** `reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-02-J-05-J-06-J-07-J-09-evidence-ledger-full.png`, `UT-J-06-factor-lab-loaded.png`

**Note:** the vcp_contraction D10/h20 candidate FAILED the referee on the 30-year basis
(confirmed both via the iter-28 spec's recorded evidence table and live via `GET
/api/evidence`), so the factor-lab cohort correctly reads "Not yet proven," not "Proven" —
this is the honest, expected outcome, not a defect. Verified:
- `/evidence` renders a `vcp_contraction — top decile (D10)` card: `FAIL` badge, tags
  `decile=10 direction=positive factor=vcp_contraction horizon=20 kind=factor
  slice_kind=decile`, "OUT-OF-SAMPLE VERDICT: FAIL · holdout edge -0.38%" (reason: "holdout
  edge -0.003773 is not in the claimed positive direction / does not beat the control
  out-of-sample" — byte-matches the API's `-0.0037732016043003124`), CONTROL COMPARISON (VS
  SPY) "-0.38%", REGISTRATION DATE "2026-07-03", "Backs: Research factor lab →" linkback.
- Opened `/research/factor-lab` (all-history mode; the page's server-side compute takes
  ~45-60s to return on this deep 30-year/548-symbol basis — waited for it). DOM-inspected the
  vcp_contraction row's evidence badges for all 5 horizons: every one carries
  `data-testid="factor-evidence-badge" data-proven="false" data-factor="vcp_contraction"`
  with `data-horizon` 1/5/10/20/60 — the h20 badge (this journey's target) correctly reads
  "Not yet proven," matching the FAIL verdict; it is never mislabeled "Proven".

### UT-J-07 — Multi-horizon certified edge surfaced (the loop sees beyond the 20-day horizon)
**Verdict:** PASS (see note)
**Evidence:** `reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-02-J-05-J-06-J-07-J-09-evidence-ledger-full.png`, `UT-J-06-factor-lab-loaded.png`

**Note:** same honest-plateau caveat as UT-J-06 — the vcp_contraction D10/h60 candidate
(this journey's non-20-horizon claim, registered `ledger=canonical`) FAILED the referee, so
"Not yet proven" is the correct render, not "Proven". Verified:
- `/evidence` renders a second, distinct `vcp_contraction — top decile (D10)` card subtitled
  "Out-of-sample edge — factor top decile · 60-day hold", tags include `horizon=60` and
  `ledger=canonical`, "OUT-OF-SAMPLE VERDICT: FAIL · holdout edge -1.64%" (byte-matches the
  API's `-0.016363899205616317`), registration date 2026-07-03, "Backs: Research factor lab
  →" — confirming the machine-readable non-20-horizon claim mechanism from the loop mechanics
  section is intact and correctly wired to the canonical ledger (not a new endpoint/module).
- `/research/factor-lab` vcp_contraction row, h60 column: `data-proven="false"
  data-horizon="60"` — honestly "Not yet proven"; h1/h5/h10/h20 columns for the same factor
  also all correctly `data-proven="false"` (none is fabricated Proven).

### UT-J-08 — Multi-factor combination certified edge surfaced on the Combination lab + Evidence
**Verdict:** PASS (see note)
**Evidence:** `reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-08-combination-lab-initial.png`, `UT-J-08-combo-configured-recheck.png`

**Note:** the pre-registered `rs_spy_3m:top:quintile × high_proximity:top:tertile`
composite FAILED the referee (holdout edge ~zero: +8.03e-05, p=0.494 vs required 0.0083), so
"Not yet proven" is the correct, expected render. Verified:
- `/evidence` renders `rs_spy_3m × high_proximity — composite`: `FAIL` badge, tags
  `cohort=composite condition=rs_spy_3m:top:quintile,high_proximity:top:tertile
  direction=positive horizon=20 kind=combination ledger=canonical`, "OUT-OF-SAMPLE VERDICT:
  FAIL · holdout edge +0.01%" (byte-matches API `8.030187730850894e-05`), registration date
  2026-07-03, "Backs: Multi-factor combination lab →".
- Live-reconfigured `/research/factor-combination`: leg 1 defaults to "Relative strength vs
  SPY (3m)" / Top / Quintile (20%) (matches leg 1 of the certified cohort by default); changed
  leg 2's factor dropdown from ATR% to "Proximity to 52-week high" and toggled its side from
  Bottom to Top (Tertile 33% stayed default) — reproducing the exact pre-registered cohort.
  Confirmed via DOM attribute inspection (not just the visual toggle, which briefly lagged
  behind a re-render) that the resulting "Combined (composite rank-blend)" badge carries
  `data-testid="combination-evidence-badge" data-proven="false"
  data-legs="rs_spy_3m:top:quintile,high_proximity:top:tertile" data-horizon="20"` — an exact
  match to the certified claim's `condition` array, honestly reading "Not yet proven" with
  tooltip "Not yet proven — no certified out-of-sample evidence backs this composite
  (rs_spy_3m:top:quintile + high_proximity:top:tertile) at the 20-day horizon yet (see the
  Evidence ledger)."

### UT-J-09 — Relative-strength (rs_spy_3m) 60-day-horizon certified edge surfaced on Evidence + Research factor lab
**Verdict:** PASS (see note)
**Evidence:** `reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-02-J-05-J-06-J-07-J-09-evidence-ledger-full.png`

**Note:** the rs_spy_3m D10/h60 candidate (promoted from the staging multi-horizon winner
per `proposer-guidance.md` §4.1 #3) FAILED the referee on the 30-year canonical re-run
(holdout edge -1.42%, wrong-direction vs the old retired-window +21.34%), so "Not yet proven"
is the correct render — the stale +21.34% value from before the iter-18 data-basis reset does
NOT appear anywhere. Verified:
- `/evidence` renders `rs_spy_3m — top decile (D10)` subtitled "· 60-day hold", tags include
  `factor=rs_spy_3m horizon=60 decile=10 direction=positive kind=factor slice_kind=decile`,
  "OUT-OF-SAMPLE VERDICT: FAIL · holdout edge -1.42%" (byte-matches API's `-0.014155...`),
  registration date 2026-07-03, "Backs: Research factor lab →". Grepped the full page for the
  old retired-window value "+21.34%" — zero occurrences.
- `/research/factor-lab` rs_spy_3m row: DOM-scanned all 5 horizon badges — every one
  (1/5/10/20/60) carries `data-proven="false"`; the h60 badge (this journey's target) is
  honestly "Not yet proven," matching the FAIL verdict.

### Deterministic replay confirmation (all 6 journeys)
Wrote self-contained golden replay scripts for all six journeys to
`runs/goal-session-mcp-loop/journey-scripts/{J-01,J-02,J-06,J-07,J-08,J-09}.json` and ran
them through the real, model-free Playwright runner (`demo_runner.py --mode verify`) against
the live frontend (`http://localhost:3255`). Result: **6/6 journeys passed, 0 failed**
(`[demo_runner] verify: 6 journey(s), 0 failed (verdict: PASS)`). This is an independent,
objective confirmation of every assertion above (exact ledger text, byte-matching percentage
values, linkback text) — not just my own browser observations. The J-06/J-07/J-08/J-09
scripts deliberately assert only against `/evidence` (fast, <1s) rather than the
`/research/factor-lab` / `/research/factor-combination` pages (which take 45-60s to compute
on the deep 30-year/548-symbol basis — well past the replay runner's 20s hard per-step
timeout cap) so future replays stay reliable; the slow-page `data-proven` checks were
performed live in this session (see notes above) and are not part of the golden scripts.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (both confirmed up: `/api/health`, `/api/evidence`
  → 200; research-lab endpoints are heavy on the 30-year/548-symbol basis, ~45-60s, per the
  coordinator's note — generous timeouts were used)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`) for live
  investigation; Chromium via Playwright (`demo_runner.py --mode verify`) for the
  deterministic golden-script replay
- **Test Date:** 2026-07-12
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-28-evidence/`
- **Data state (load-bearing context):** all 7 canonical `certified-claims.jsonl` entries are
  FAIL (`GET /api/evidence` → `"proven_signals": {}`) — the honest, sanctioned plateau state
  this iteration exists to assess, per `docs/phases/goal-mcp-loop-iter-28.md`. No `##
  Evidence Claim` was registered or tested this iteration (out of scope per the iteration
  spec); this QA pass did not submit anything to the referee and did not touch the ledger.
- **Journeys intentionally NOT tested this run** (per dispatch instructions — verified
  separately by deterministic replay): J-03, J-04, J-05, J-10, J-11, J-13.
