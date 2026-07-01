# goal-mcp-loop-iter-10 Audit Report

**Date:** 2026-07-01
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

Part B Phase 1 (open the multi-horizon aperture + run a pre-registered candidate set through the referee into the internal staging ledger under the online-FDR economy) is implemented correctly and completely. The honesty fence is real — the canonical `certified-claims.jsonl` is git-unmodified, the DO-NOT-EDIT default-path suites are unedited, and a canonical `verify_edge` reproduces strict Bonferroni even with `fdr.enabled=true`. I independently regenerated the committed staging ledger against the real app DB (1377 runs) and it is **byte-identical**, so the deliverable is genuinely reproducible, not hand-fabricated. One documented, non-blocking gap remains: the committed `staging-ledger.jsonl` is still git-untracked and must be staged at finalize.

---

## 2. Findings

### Backend Findings

**B1 — GAP (gap): committed staging ledger is git-untracked at audit time**
`runs/goal-session-mcp-loop/state/staging-ledger.jsonl` shows `??` in `git status`. The DoD requires it "committed with the iteration," and the frozen-golden test `test_committed_staging_ledger_is_the_frozen_multi_horizon_discovery` (`apps/backend/tests/test_staging_ledger_routing.py:345`) reads it by absolute repo path (`_STAGING_LEDGER`, line 42) — a clean checkout without the file would fail that test. Already flagged by the reviewer (NOTE) and QA (Note), and the file IS listed in `runs/goal-mcp-loop-iter-10/status.json:changed_files`, so the standard finalize `git add` will stage it. Not a code defect — a finalize/git step. Left to the release-manager (auditor runs pre-finalize; git-index mutation is out of the surgical-code-fix remit). Remediation: `git add runs/goal-session-mcp-loop/state/staging-ledger.jsonl` before the release commit.

**B2 — OBSERVATION: honesty fence verified end-to-end (no action)**
`app/mcp/tools.py:519` — `use_fdr = ledger == LEDGER_STAGING and fdr_cfg.enabled`. Canonical (the `verify_edge` default) never sets `test_level`, so `app/engine/referee.py:358` takes the `required_p = alpha_per_test / divisor` branch (strict Bonferroni). Confirmed in code, by `test_verify_edge_fdr_runs_in_staging_but_canonical_stays_bonferroni` (asserts canonical `required_p == 0.05/1` with FDR enabled), and by the empty `git diff` on `certified-claims.jsonl`. `explore_multi_horizon_staging` only ever calls `verify_edge(ledger="staging")` and has a fail-closed guard (`triad_scan.py:317-322`, tested) that raises if pointed at the canonical path. Zero staging references reach `app/engine/evidence.py`, `app/api/`, or `GET /api/evidence` (grep-verified).

**B3 — OBSERVATION (for iter-11, not an iter-10 defect): the three h60 PASSes sit at the bootstrap p-floor**
All three h60 PASS verdicts record `p_value = 0.0004997501249375312 = 1/(2000+1)` (zero of 2000 block-bootstrap resamples exceeded the observed holdout edge). `rs_spy_3m` h60 carries a very large `holdout_edge = +0.2134` over the SPY control at a 60-day horizon. This is honest discovery in the non-burning staging ledger — the referee recorded exactly what the data said, and the spec pre-labels `rs_spy_3m` as "the speculative member." No-lookahead is structurally preserved at h60 (the referee's purge/embargo scales with the horizon: `purged_in_sample` = 1361/751/1031 for the h60 cohorts). iter-11 should prefer the signal-less `vcp_contraction` h60 (edge +0.089, more modest) and treat the +0.21 `rs_spy_3m` edge with scrutiny before a canonical promotion.

### Frontend Findings

None — `Frontend Present: no`. Zero `apps/frontend/**` diff (confirmed). No UI, no badge, no `/evidence` change. Correct for a discovery-only iteration; J-07 stays `unknown` by design.

### Test Findings

**T1 — OBSERVATION: frozen-golden ledger test is a golden-artifact check, not a regenerate-and-compare**
`test_committed_staging_ledger_is_the_frozen_multi_horizon_discovery` reads the committed file and asserts its contents; it does not itself re-derive the ledger from the DB. The `required_p` column it pins is independently proven correct by the pure `test_online_fdr.py` LORD++ levels, but the `p_value` column (DB-dependent) is only anchored by the committed artifact. I closed that gap out-of-band: regenerating via `explore_multi_horizon_staging(session, reset=True)` against `apps/backend/data/trendora.db` produced a **byte-identical** ledger. Reproduce path documented here for iter-11.

**T2 — OBSERVATION: assertions are tight**
Multi-horizon enumeration asserts the exact set `[1,5,10,20,60]` and exactly 110 cells / 22 per horizon (`test_triad_scan.py:80,83,108`). The FDR levels are frozen to 1e-15 (`test_staging_ledger_routing.py:368-373`). The INSUFFICIENT error path (thin fixture) and the fail-closed canonical-path guard are both exercised. 95 iter-10-core tests pass on my run (155s); dev + QA reported 129 green across the wider suite.

---

## 3. Domain Assessment

The core domain logic is sound. The referee (`app/engine/referee.py`) is pure and deterministic (single seeded RNG), applies a sealed temporal holdout with per-horizon purge+embargo, and computes a one-sided block-bootstrap p-value floored at `1/(B+1)` — no spurious exact zeros. The multiple-testing deflation is an injectable policy whose default byte-identically reproduces strict Bonferroni; the LORD++ online-FDR allocator (`app/engine/online_fdr.py`) is a pure, stateless wealth-reconstruction from rejection ordinals, and the economy visibly replenishes across the four staging trials (`required_p` 0.0109 → 0.0036 → 0.0128 → 0.0267 — tightening before the first discovery, then loosening as PASSes land), which a strict Bonferroni divisor could never do. The anti-data-mining keystone holds: the exploration iterates ONLY the fixed 4-candidate `config.triad.candidates` set (never the `factor×horizon×decile` cross-product), mirrored with rationales into `project-extensions/proposer-guidance.md`. The discovery is honest end-to-end: `vcp_contraction` h10 genuinely FAILED (p≈0.057) and was recorded as such rather than massaged, and three h60 cohorts (two signal-less) cleared the eventual canonical divisor-5 bar (p<0.010) — exactly the referee-scored input iter-11 needs.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | None. No CRITICAL or IMPORTANT issues found; the single GAP (B1) is a finalize git-staging step owned by the release-manager, not a code fix. |

---

## 5. Recommended Next Step

Proceed to finalize, then iter-11. At finalize, the release-manager **must** stage the committed ledger (`git add runs/goal-session-mcp-loop/state/staging-ledger.jsonl`) — it is both the iter-11 promotion input and the fixture the frozen-golden test reads.

For iter-11 (surface J-07): read `staging-ledger.jsonl`, promote the **signal-less** `vcp_contraction` D10 @ h60 winner (p=0.00049975 < 0.010; more modest, more credible +0.089 edge than `rs_spy_3m`'s +0.21) via a canonical `## Evidence Claim` that sets `"ledger":"canonical"` **explicitly** (an omitted key defaults to staging and would silently never surface), certified at divisor 5 / required_p=0.010, then surface the `/evidence` row + factor-lab "Proven" badge and browser-verify J-07. Reproduce the staging ledger any time with `explore_multi_horizon_staging(session, reset=True)` against `apps/backend/data/trendora.db` (verified byte-identical this audit).
