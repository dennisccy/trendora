# Goal Mode Iter 14 — UI Test Results

**Phase:** goal-mcp-loop-iter-14
**Date:** 2026-07-01
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-08 | Multi-factor combination certified edge on Combination lab + Evidence | happy-path | P1 | "Proven" badge for rs_spy_3m×high_proximity, deep-link lands 6th /evidence row with all standard fields, byte-match edge +4.69%/p=0.0009995 | All verified: badge data-proven=true, anchor id resolved, element in viewport, all fields present, byte-match confirmed, no backend-unavailable pill, 0 combination badges on /stocks | PASS | `reports/qa/goal-mcp-loop-iter-14-evidence/UT-J-08-07-fullpage.png`, `reports/qa/goal-mcp-loop-iter-14-evidence/UT-J-08-12-evidence-fullpage.png` |

---

## Passed Tests

### UT-J-08 — Multi-factor combination certified edge surfaced on Combination lab + Evidence

**Verdict:** PASS

**Evidence:**
- Default state (Not yet proven): `reports/qa/goal-mcp-loop-iter-14-evidence/UT-J-08-02-default-not-yet-proven.png` (md5: e63c33d7b65003be69a3298e246321cc)
- Proven badge for certified selection (fullpage): `reports/qa/goal-mcp-loop-iter-14-evidence/UT-J-08-07-fullpage.png` (md5: 4c740ba870e54538df013ed679fa0ac1)
- Evidence page combination row (fullpage): `reports/qa/goal-mcp-loop-iter-14-evidence/UT-J-08-12-evidence-fullpage.png` (md5: 9bb1f0d79392e8e4f040137b5740bdc1)

All three md5 hashes are distinct. None is a page-top or "Backend unavailable" frame.

**Precondition verification:**
- `GET http://localhost:8255/api/evidence` returns exactly 6 claims
- Claim 6: `kind=combination`, `condition=["rs_spy_3m:top:quintile","high_proximity:top:tertile"]`, `horizon=20`, `proven=true`, `signal=null`, `holdout_edge=0.046931901591708916`, `p_value=0.0009995002498750624`, `register_date=2026-07-01`

**Step-by-step execution:**

1. Navigated to `/research/factor-combination` — page loaded with heading "Research — Multi-factor combination", "Ready" status, no "Backend unavailable" pill.

2. **Default (honest-marking) check:** Badge (`data-testid="combination-evidence-badge"`) inspected before changing selection:
   - `data-proven="false"`
   - `data-legs="rs_spy_3m:top:quintile,atr_pct:bottom:tertile"`
   - text: "Not yet proven"
   - Screenshot UT-J-08-02 captured with badge scrolled into view.

3. **Compose the certified selection:**
   - Changed `condition-factor-1` select to `high_proximity` (Proximity to 52-week high)
   - Clicked "Top" button in `condition-side-1` (leg 2 side changed from Bottom to Top)
   - `condition-quantile-1` was already `tertile` — no change needed
   - Leg 1 state confirmed: factor=`rs_spy_3m`, side=Top, quantile=`quintile` (aria-pressed="true")
   - Horizon confirmed: `20d` (aria-pressed="true")

4. **Proven badge verified:**
   - Badge element inspected: `data-proven="true"`, `data-legs="rs_spy_3m:top:quintile,high_proximity:top:tertile"`, text="Proven"
   - Badge `href="/evidence#combination-high_proximity-rs_spy_3m-h20"` (correct deep-link anchor)
   - Title attribute: "Proven — this composite (rs_spy_3m:top:quintile + high_proximity:top:tertile) beat SPY out-of-sample over the sealed holdout at the 20-day horizon (certified 2026-07-01). Click to audit the backing evidence."
   - Fullpage screenshot UT-J-08-07 captured showing "Proven" chip in the "Combined (composite rank-blend)" table row (selection clearly visible: Proximity to 52-week high / Top / Tertile (33%)).

5. **Deep-link navigation:**
   - Clicked `[data-testid="combination-evidence-badge"]` — browser navigated to `http://localhost:3255/evidence#combination-high_proximity-rs_spy_3m-h20` (confirmed via `window.location.href`)

6. **Evidence row scrolls into viewport:**
   - Element `id="combination-high_proximity-rs_spy_3m-h20"` found in DOM
   - `getBoundingClientRect().top = 591`, `viewportHeight = 900` → `inViewport: true`
   - Element text confirmed (full content):
     ```
     PASSrs_spy_3m × high_proximity — composite
     Backs: Multi-factor combination lab →
     Out-of-sample edge — multi-factor composite
     Hypothesis: cohort=composite, condition=rs_spy_3m:top:quintile,high_proximity:top:tertile,
                 direction=positive, horizon=20, kind=combination, ledger=canonical
     Out-of-sample verdict: PASS · holdout edge +4.69%
     certified: holdout edge +0.04693 beats the control out-of-sample and is significant after
     multiple-testing deflation (p=0.0009995 < alpha/6=0.008333)
     Control comparison (vs SPY): +4.69%
     Registration date: 2026-07-01
     Forward-walk score-to-date: Pending — monitored as new data matures
     ```
   - Fullpage screenshot UT-J-08-12 captured showing all 6 evidence rows including the combination row at the bottom.

7. **Byte-match (anti-goal #3):**
   - Displayed `+4.69%` matches ledger `holdout_edge=0.046931901591708916` (rounds to +4.69%)
   - Displayed `p=0.0009995` matches ledger `p_value=0.0009995002498750624`
   - Displayed `alpha/6=0.008333` matches `required_p=0.008333333333333333` (divisor 6)
   - Registration date `2026-07-01` matches ledger

8. **Linkback verified:**
   - "Backs: Multi-factor combination lab →" link href: `http://localhost:3255/research/factor-combination`

9. **No "Backend unavailable" pill:** `hasBackendUnavailable: false` throughout; `hasReady: true` confirmed.

10. **Anti-goal: no combination badge leakage to /stocks:**
    - `/stocks` page: `combination-evidence-badge` count = 0 (no leakage)
    - `evidence-badge` count = 360 (stocks badges unaffected)
    - `proven_signals = {leadership_score}` — combination does not affect per-stock badges

11. **Final backend state:** `GET /api/evidence` after the browser run still returns 6 claims with the same combination row. `certified-claims.jsonl` byte-identical (no new row added during this verification-only run).

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via Chrome MCP
- **Test Date:** 2026-07-01
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-14-evidence/`
- **Screenshot note:** Fullpage screenshots (UT-J-08-07, UT-J-08-12) were used for the asserted-state captures because Chrome MCP viewport screenshots render as black after programmatic `scrollIntoView` on the evidence page (a known session artifact). Fullpage screenshots correctly capture all content. The DOM assertions via `eval` confirm element presence and `inViewport: true` for the combination row.
