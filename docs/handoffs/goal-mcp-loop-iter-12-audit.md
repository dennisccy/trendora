# goal-mcp-loop-iter-12 Audit Report

**Date:** 2026-07-01
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

Iter-12 genuinely achieves its enablement goal: a FIXED, pre-registered set of three 2-factor combination hypotheses is registered in config, mirrored verbatim into `proposer-guidance.md` §4.2, and run through the **unchanged** referee into the internal staging ledger (4→7 entries), each combination verdict recording every field iter-13 needs to promote a winner. The load-bearing regression claim — that the shared certification engine was reused, not modified — is verified by a byte-for-byte 0-diff on `certified-claims.jsonl`, `referee.py`, `tools.py`, `samples.py`, `evidence.py`, `online_fdr.py`, and the three DO-NOT-EDIT suites. No critical or important gaps; no scope drift; no anti-goal violation.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION: `explore_combination_staging` is a clean, correct sibling of the single-factor explorer.**
`apps/backend/app/engine/triad_scan.py:365-450`. `_combination_staging_candidates` reads `config.triad.combination_candidates` VERBATIM and projects each entry to `{kind:"combination", cohort:"composite", condition:[legs], horizon, direction}` — no leg/horizon literal is enumerated in code (the anti-data-mining keystone holds; only `kind` + `cohort:"composite"` are structural constants, exactly as the single-factor sibling fixes `slice_kind="decile"`). `explore_combination_staging` carries the same fail-closed canonical-path guard (`triad_scan.py:427-432`, abspath equality → `ValueError`) and calls `verify_edge(session, claim, ledger_path, ledger=LEDGER_STAGING)` only. The deliberate parallel-sibling choice (not a shared refactor) correctly protects the byte-frozen single-factor entries #1-4 — `git diff` on the ledger shows +3/-0 (only the 3 combination lines appended).

**B2 — OBSERVATION (verified, not a defect): the "REUSE UNCHANGED" claim is real.**
The referee cert path that assembles + validates the combination cohort is byte-identical to HEAD: `git diff HEAD` on `app/mcp/tools.py`, `app/engine/samples.py`, `app/engine/referee.py`, `app/engine/online_fdr.py`, `app/engine/evidence.py`, `app/api/evidence.py` = **0 lines**. `_CLAIM_SELECTOR_KEYS` (`tools.py:395`) already forwards `condition`+`cohort`; `drill_samples` (`tools.py:342-346`) already parses the legs; `_combination_samples` (`samples.py:197-253`) already resolves the composite cohort. The developer added nothing to the writer path — `verify_edge` stays the SOLE ledger writer.

**B3 — OBSERVATION: the error-case tests are backed by real validation, not stubs.**
The three `ValueError` paths asserted by the malformed-candidate test resolve to live code: unknown factor → `samples.py:221`; malformed leg (not 3 colon-parts) → `tools.py:345`; unknown quantile → `samples.py:229`. These fire inside the reused referee path, so a bad combination candidate raises loudly *before* any staging write (the test also asserts no partial file is left). Fail-loud, not silent-skip — spec-compliant.

**B4 — OBSERVATION (informational for iter-13): `holdout_edge == control_excess` on every ledger entry.**
In all 7 verdicts the two fields carry the identical value (e.g. winner: both `0.046931901591708916`). This is inherent to the unchanged referee (the holdout edge *is* the same-dates excess over the SPY control), not something iter-12 introduced. iter-13's tiebreak should lean on `p_value` + `holdout_edge` magnitude; `control_excess` adds no independent information. Referee.py is 0-diff, so this is pre-existing behavior.

### Frontend Findings

**F1 — N/A: Frontend Present: no.** No UI surface this iteration; the staging ledger is internal-only (never served by `GET /api/evidence`, never displayed). The blueprint's additive iter-12 clarification (`blueprint.md`, +2 lines) documents exactly this and re-affirms byte-identity — additive documentation, no data-contract drift. Correctly no browser lane (mirrors iter-9/iter-10).

### Test Findings

**T1 — OBSERVATION: assertions are tight and independently re-run green.**
I re-ran `test_staging_ledger_routing.py` + `test_online_fdr.py` → **27 passed** (exit 0), independent of the QA report. The frozen-golden test pins exact values (winner `p_value == 0.0009995002498750624`, status sequence `[FAIL,FAIL,PASS]`, `required_p` levels to `abs=1e-15`, `rejection_offsets == [2,3,4,7]`, `count_trials == 7`, canonical still `[1,2,4,5]`/5 entries). Determinism, staging-isolation, canonical-refusal (both absolute + relative path), and 3 distinct malformed-candidate cases are all covered. QA's full 134-pass run corroborates.

**T2 — OBSERVATION (accepted pattern, not a gap): committed combination verdicts are anchored by a frozen-golden test, not recomputed in a fixture.**
The thin quarterly fixture records INSUFFICIENT (too few sealed-holdout dates), so the committed #5-7 p-values (0.727 / 0.791 / 0.0009995) rest on a one-time run against the committed production DB (`apps/backend/data/trendora.db`, 1377 runs) plus the frozen-golden anchor. This is the *same* strategy accepted for iter-10's #1-4 and is safe here because: the referee is a PURE deterministic function that is byte-identical-unchanged; the determinism mechanism is proven on the fixture; and the recorded values are internally self-consistent (PASS iff `p<required_p`; divisor progression 5→6→7; p at the block-bootstrap floor `≈1/1001` matches the strong `+0.0469` edge). Noted for transparency; does not lower the verdict.

---

## 3. Domain Assessment

The core domain logic is correct and, importantly, **honest**. The three registered pairs match the spec exactly (config `config.yaml:1091-1103`; §4.2 mirror `proposer-guidance.md:96-98`), each leg's `side` matches its factor-catalog direction (momentum/leadership/proximity `:top`, volatility `atr_pct:bottom`), all at horizon 20 / direction positive / composite cohort. The referee then did what the anti-goals demand: the two "obvious" anchor composites (low-ATR filter over momentum / over leadership) **FAILED** out-of-sample with negative holdout edge, and only `rs_spy_3m` leaders that are *also* near their 52-week high **PASSED** (raw block-bootstrap `p=0.0009995 < 0.05/6 ≈ 0.00833`, holdout `+0.0469`). That is the sealed-holdout + control + LORD++ multiple-testing machinery refusing a thin composite — anti-goal #1/#4 upheld, not engineered around. The winner gives iter-13 a genuine, recorded promotion basis; the honest-stop guard for the "none clears the bar" case is documented in both the spec and §4.2. J-08 correctly stays `unknown` (verified in `journey-history.json`); J-01..J-07 stay `passing`, proven by the byte-identity path rather than an editable expectation.

Scope discipline is exact: every OUT-OF-SCOPE item is respected — no canonical write (diff=0), no `/evidence` row or badge, no read-side matcher, no `/stocks` change, no `factor × pair × horizon` cross-product (only the 3 fixed candidates), no `ma_stack` leg, no new economy/endpoint. The honesty fence (`use_fdr = ledger==LEDGER_STAGING and evidence.fdr.enabled`) is untouched, so FDR stays fenced to staging and canonical stays strict Bonferroni.

---

## 4. Fixes Applied During This Audit

None. No critical or important issues were found; the implementation is correct, in-scope, and fully tested. All findings above are OBSERVATION-level.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes required |

---

## 5. Recommended Next Step

**Proceed to iter-13.** The staging ledger now carries the real, recorded basis iter-13 needs: promote the single surviving winner (`rs_spy_3m:top:quintile` + `high_proximity:top:tertile`, raw `p=0.0009995`) to the canonical ledger via an explicit `"ledger":"canonical"` `## Evidence Claim` (do NOT let the key default to staging), then surface J-08 on `/research/factor-combination` + `/evidence` as additional readers of the same `GET /api/evidence` payload. iter-13 should read the recorded staging verdict — not recompute — and honor the documented honest-stop guard (if the winner no longer clears the divisor-6 bar with margin against fresh data, report it rather than force an overfit promotion).
