# goal-mcp-loop-iter-15 Audit Report

**Date:** 2026-07-01
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal is achieved and independently verified: the 7th referee-certified canonical edge
(`rs_spy_3m` D10 @ h60) is gate-appended to the ledger with byte-exact values, surfaces "Proven" on the
factor lab and as a new `/evidence` row through the **unchanged** general matcher, and stays signal-less so
no `/stocks` inline badge lights. No application source was touched (git-verified byte-identical), all tests
I re-ran are green, and the yellow-flagged +0.2134 edge is honestly surfaced (verbatim, referee-backed,
upper-bound framing). Two non-blocking gaps are documented: the screenshot evidence never captures the
rs_spy_3m "Proven" money frame (the pass rests on DOM assertions + the byte-exact ledger/unit-test triangle,
which the spec explicitly endorses), and the +0.2134 holdout magnitude remains implausibly large as a known
characteristic of the seeded data / out-of-scope engine.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (verified-correct): signal-less routing keeps `rs_spy_3m` out of `proven_signals`.**
`apps/backend/app/engine/evidence.py:66` defines `_SCORE_COLUMN_FACTORS = {leadership_score,
entry_quality_score, risk_score}`; `_resolve_signal` (`evidence.py:69-85`) returns `None` for `rs_spy_3m`
(explicit `signal` absent AND `factor ∉` the score columns), so `build_evidence_payload` (`evidence.py:128`,
`if row["proven"] and signal:`) never adds it to `proven_signals`. Row 7 IS added to `claims[]` (it is not a
`forward_walk` record — `evidence.py:123`), so it renders on `/evidence` but lights no `/stocks` badge. This
is the exact anti-goal-compliant no-leak behavior. No change required — the file is byte-identical to prior.

**B2 — OBSERVATION (verified-correct): ledger row 7 is gate-appended and byte-exact.**
`runs/goal-session-mcp-loop/state/certified-claims.jsonl:7` = `factor rs_spy_3m d10 h60`,
`ledger=canonical`, `status=PASS`, `deflation=bonferroni`, `deflation_divisor=7`,
`required_p=0.0071428571428571435`, `p_value=0.0004997501249375312`, `holdout_edge=control_excess=
0.21344270202534893`, `register_date=2026-07-01`, `block_length=87`, `seed=20240601`. `git diff --stat` on
the ledger shows exactly **1 insertion** (rows 1-6 byte-identical) — the gate wrote it; nothing was
hand-edited. The recorded `p` clears the divisor-7 bar by ~14× (`0.0004998 < 0.007143`), so the PASS is
genuine, not a forced/`FAIL`-appended pass. The honest-stop block path was not exercised because the gate
PASSED (correct outcome).

### Frontend Findings

**F1 — GAP (documented): the screenshot evidence never shows the `rs_spy_3m` h60 "Proven" money frame.**
Every factor-lab capture — `reports/qa/goal-mcp-loop-iter-15-evidence/TC-03-factor-lab-rs_spy_3m.png`,
`UT-06-factor-lab.png`, `UT-07-proven-chip.png` (all md5 `19e8d97f…`) and the one distinct
`UT-09-UT-11-factor-lab.png` (md5 `8a52a235…`) — is scrolled to the **top** of the table showing "Proximity
to 52-week high" and "Risk score", both entirely "Not yet proven"; the `rs_spy_3m` row is never in-frame.
The `/evidence` capture `TC-02-evidence-page.png` shows rows 1-3, not row 7. Several browser-lane result
captures (`UT-01/UT-02/UT-03-anchor/UT-05-rows4-6/UT-08` `-result.png`) are **5855-byte blank frames** —
the exact scrolled-headless-viewport failure the spec warned about (iter-14 lesson) — and there is heavy
md5 reuse across test ids. **Non-blocking** because the achievement is independently proven by the
byte-exact ledger row 7 + the verified-unchanged deterministic matcher code + the passing tight unit tests +
the browser lane's DOM-attribute assertions (`reports/phase-goal-mcp-loop-iter-15-ui-test-results.md` UT-07
records `data-proven="true"`, `text="Proven"`, `href="/evidence#factor-rs_spy_3m-d10-h60"` for h60 and
`data-proven="false"` for h1/h5/h10/h20; UT-02 extracted the row title/subtitle/edge/p/date/divisor text
matching the ledger). The spec explicitly endorses this triangle "when pixels are weak". No fix applied
(the feature works; regenerating screenshots needs the now-torn-down live services and is browser-QA work,
not a surgical code fix).

**F2 — OBSERVATION: the QA report overstates what its screenshots visually confirm.**
`reports/qa/goal-mcp-loop-iter-15-qa.md` TC-03 ("Rendered factor-lab screenshot confirms state per horizon")
and TC-02/TC-09 imply the referenced images show the rs_spy_3m elements, but the images show adjacent frames
(F1). The verdicts are correct (grounded in DOM assertions), but the "screenshot confirms" phrasing is not
supported by the pixels. Informational only.

### Test Findings

**T1 — OBSERVATION (verified-correct): frontend cases (ee/ff) are tight and byte-match the ledger.**
`apps/frontend/lib/evidence.test.ts:839-866` (`rsSpy3mH60Row()`) byte-matches `certified-claims.jsonl:7`
(`cohort_n=12026`, `control_n=1101`, holdout/control `0.21344270202534893`, `p 0.0004997501249375312`).
Check (ee) (`:879-911`) asserts exact `href="/evidence#factor-rs_spy_3m-d10-h60"`, exact verbatim verdict
values, and loops h∈[1,5,10,20] asserting "Not yet proven" (no cross-horizon leak) plus a distinct
vcp_contraction h60 href (no cross-factor leak). Check (ff) (`:916-936`) pins the honest title/subtitle/
linkback + the `factor-rs_spy_3m-d10-h60` anchor + `signal=null`. Reconciled case (o) (`:461-474`) now
resolves against the 7-entry ledger and turns the former unbacked-`rs_spy_3m` line into a stronger
no-h60→h20-leak negative. I re-ran the suite: **39/39 pass** against the UNCHANGED `evidence.ts` — proof the
general matcher lights the new cohort with no special-casing (iter-8 lesson upheld).

**T2 — OBSERVATION (verified-correct): backend golden refresh is TEST-ONLY and correct.**
`apps/backend/tests/test_evidence.py` (`test_canonical_ledger_frozen_golden`) updates count 6→7,
statuses/divisors to `[1..7]`, factor/kind lists, adds a byte-exact `entries[6]` block (incl.
`assert "signal" not in rs["claim"]`), and keeps `proven_signals == {leadership_score}`.
`apps/backend/tests/test_staging_ledger_routing.py` updates only the two live-canonical reads
(`[1,2,4,5,6]/6 → [1,2,4,5,6,7]/7`); the staging determinism assertions (`[2,3,4,7]/7`) are UNTOUCHED,
preserving the FDR-fenced-to-staging honesty invariant. No `app/**` change. I re-ran: evidence **14/14**,
the two changed staging tests **2/2**.

---

## 3. Domain Assessment

The core domain logic is correct and honest. Proven-ness flows solely from `verdict.status == "PASS"` in the
gate-written ledger; the UI recomputes nothing. The general `resolveCohortEvidence`
(`apps/frontend/lib/evidence.ts:451-480`) matches on `factor + slice_kind + decile + horizon + direction`,
so `rs_spy_3m` h60 lights "Proven" via row 7 while its uncertified horizons stay dark — and `factorHorizonBadges`
(`apps/frontend/lib/factor-lab-evidence.ts:49-74`) wires that matcher per-horizon for every catalog factor
(`rs_spy_3m` confirmed at `config.yaml:806`). `claimAnchorId` (`evidence.ts:418-430`) makes the badge href
and the `/evidence` row id agree, so the deep-link lands.

**Yellow flag (the designated audit focus) — honestly handled, documented as a GAP.** The +0.2134 (21.34%)
60-day holdout edge is implausibly large and exceeds its own in-sample edge (~2.04%, `certified-claims.jsonl:7`
`in_sample_edge=0.020376…`) by ~10× — the opposite of the usual out-of-sample shrinkage, flagged by the
iter-10 auditor (B3). This is acceptable to surface because: (1) it is a genuine referee PASS certified
out-of-sample against the SPY control at strict Bonferroni divisor 7 (not hand-edited — B2); (2) the magnitude
is a property of the seeded synthetic data (seed 20240601) + the engine, both **out of scope** this iteration
(byte-identical, anti-goal #5 determinism); (3) the surfacing is honest — the value is displayed verbatim (no
inflation), backed by a passing certified-claim (anti-goal #1), with the factor lab's prominent "descriptive,
not a predictive model … read the edge as an upper bound, not a guarantee" framing (visible in TC-03) and no
buy/sell/return language (anti-goal #2). The implausible magnitude is not a defect introduced by this
iteration; it is a known data characteristic surfaced with the correct caveats.

**Regression posture is strong.** Engine/referee/ledger/`evidence.py`/`tools.py`/`evidence.ts`/
`factor-lab-evidence.ts`/`_labs.tsx`/`evidence/page.tsx`/`config.yaml` are all git-verified byte-identical;
the only touched files are three test files. J-01..J-08 non-regression is corroborated by the browser lane
(UT-11 vcp_contraction h20/h60 still `data-proven="true"`; UT-05 first 6 rows intact; UT-12/UT-13
`/stocks` columns unchanged, zero `rs_spy_3m`, `proven_signals` keys `["leadership_score"]`).

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issue was found. All source is byte-identical, all re-run tests are green, and
the logic is correct. The two documented gaps (F1 screenshot hygiene, yellow-flag magnitude) are non-blocking
and not surgical code defects, so per the auditor rules they are recorded, not "fixed".

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied |

---

## 5. Recommended Next Step

**Proceed.** J-09 is genuinely delivered — the 7th canonical edge is certified, byte-exact, and surfaced
honestly with no signal leak and no regression, verified independently of the weak screenshots. Two items to
carry forward (non-blocking):

1. **Screenshot hygiene (recurring — iter-11/13/14/15).** The browser lane keeps producing 5855-byte blank
   frames and top-of-table captures that miss the certified row. A future hardening iteration should make the
   browser-qa step capture an **element-clip of the actual "Proven" chip / row 7** (or fail the capture), so
   the visual artifact matches the (correct) DOM assertions instead of relying on the ledger/unit-test triangle.
2. **Yellow-flag magnitude.** The +0.2134 edge remains implausibly large; it is honest to surface but the
   underlying seeded-data / engine characteristic is worth a dedicated look if/when the engine is ever in
   scope — strictly out of scope here (determinism), noted for the backlog.
