# goal-mcp-loop-iter-11 Audit Report

**Date:** 2026-07-01
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

The phase goal is fully achieved and verified in code, not just in summaries. The canonical `vcp_contraction` D10 @ h60 claim is a real 5th ledger entry (PASS, Bonferroni divisor 5, required_p=0.010, holdout/control/p byte-exact); the factor lab renders honest per-horizon evidence chips sourced from served data; the browser-qa lane genuinely ran against a live backend and passed 15/15 with a real badge flip and scrolled-into-frame screenshots. No backend engine code was touched, no anti-goal is violated, and all unit/integration tests pass under independent re-run (backend 31/31, frontend 27+5, `tsc` clean). No critical or important gaps remain; no fixes were required.

---

## 2. Findings

### Backend / Data Findings

**B1 — OBSERVATION (verified): the 5th canonical ledger entry is correct and additive**
`runs/goal-session-mcp-loop/state/certified-claims.jsonl` line 5 is the promoted claim. `git diff HEAD` on the ledger shows **exactly one line appended** — the prior four rows are byte-identical (hunk `@@ -2,3 +2,4 @@`). Verified byte-exact: `status=PASS`, `holdout_edge=0.08909719710495288`, `control_excess=0.08909719710495288`, `p_value=0.0004997501249375312`, `deflation="bonferroni"`, `deflation_divisor=5`, `required_p=0.01`, `cohort_n=12026`, `control_n=1055`, `horizon=60`, `"ledger":"canonical"`, and **no `signal` key**. Matches the spec's Evidence Claim and expected verdict exactly.

**B2 — OBSERVATION (verified): zero engine/router/referee/ledger/evidence.py edits**
`git diff --name-only HEAD -- 'apps/backend/app/**'` returns empty. The only backend changes are test-only (`tests/test_evidence.py`, `tests/test_staging_ledger_routing.py`). The promotion is entirely via the post-decompose gate + the Evidence Claim, as the spec mandates. No second evidence data path was introduced.

**B3 — OBSERVATION (verified): `proven_signals` stays byte-identical `{leadership_score}`**
The signal-less h60 claim does not enter `proven_signals`. Proven both by the read-side derivation test (`_resolve_signal(h60 claim) is None`, `test_evidence.py:374`) and by the frozen-golden test that reads the **real on-disk ledger** and asserts `set(payload["proven_signals"].keys()) == {"leadership_score"}` (`test_evidence.py:509`). This is the airtight data-level guarantee that J-01/J-02/J-03 cannot regress and that no `/stocks` inline badge can appear for the h60 claim.

### Frontend Findings

**F1 — OBSERVATION (verified): per-horizon rendering is correct and data-sourced, not hardcoded**
`app/research/_labs.tsx:542` `horizons = data.horizons` and `:547` `topDecile = data.deciles_count` are read from the served payload — no hardcoded `[1,5,10,20,60]` list, no hardcoded decile. The Evidence cell (`:838-844`) maps `factorHorizonBadges(row.key, topDecile, horizons, evidenceClaims)` to one `FactorEvidenceBadge` per horizon. Both badge branches carry `data-horizon` (`:750` proven, `:774` not-proven), `data-proven`, `data-factor`, `data-testid`. The proven branch is a `<Link>` with `stopPropagation()` on click + keydown (`:751-752`), guarding the row's expand toggle (iter-5 hazard); the not-proven branch is a non-interactive `<Badge>` with no link.

**F2 — OBSERVATION (verified): `resolveCohortEvidence` is not special-cased; honesty preserved**
`lib/factor-lab-evidence.ts` is a pure wrapper that queries the **existing** `resolveCohortEvidence` per horizon with no factor-specific branching. Consequently `leadership_score` honestly reads "Proven" at h20 and deep-links to its real `signal-leadership_score` anchor (via `claimAnchorId`, `lib/evidence.ts:395`), exactly as the iter-8 lesson requires. The only `evidence.ts` change is the `claimSurface` subtitle gate on `DEFAULT_FACTOR_COHORT_HORIZON = 20` (`:231`, `:302`): h20 stays the bare iter-8 wording, h60 appends "· 60-day hold". `resolveEvidenceStatus`, `evidenceAnchor`, `cohortClaimId`, `claimAnchorId` are unchanged.

**F3 — OBSERVATION (verified): failure handling is explicit and honest**
Empty/failed `fetchEvidence` → every chip "Not yet proven", no link (browser UT-09 confirmed a "Backend unavailable" panel with "No figures are shown rather than fabricated values", no blank screen, no JS crash). Uncertified horizons h1/h5/h10 → "Not yet proven" (UT-07: `data-proven="false"`, tag=DIV, no href). Matched-but-non-PASS (ma_stack FAIL) → "Not yet proven" at every horizon (UT-08 + unit test). No escape hatch can fabricate proven-ness — the resolver returns "Not yet proven" for anything but a PASS-backed exact-cohort match.

### Test Findings

**T1 — OBSERVATION (verified): assertions are tight and cover the failure paths**
Backend `test_canonical_ledger_frozen_golden` reads the real ledger and pins the full golden (`statuses [PASS,PASS,FAIL,PASS,PASS]`, `divisors [1,2,3,4,5]`, all bonferroni, factor sequence, `"signal" not in h60["claim"]`, edge/control/p byte-exact) — it would fail loudly on any reorder, rewrite, or stray signal. `test_build_payload_vcp_contraction_h60_factor_cohort_post_certification` builds the full 5-entry ledger and byte-checks every h60 field plus `proven_signals == {leadership_score}`. Frontend `evidence.test.ts` (27) + `factor-lab-evidence.test.ts` (5) cover h60→proven (correct href), h10→not-proven (no href), h20→proven (h20 entry), ma_stack FAIL→never proven, empty/null claims fail-safe, `formatEvidencePct(0.08909719710495288)==="+8.91%"`, and the subtitle disambiguation with h20 byte-identical. Independently re-ran: **all green**.

**T2 — OBSERVATION: QA report (step 7a) browser skips are superseded by the canonical lane**
The QA report skipped its 10 browser cases ("backend unavailable in QA environment") and its API checks leaned on the dev's live curl. This is by-design pipeline ordering — the canonical `browser-qa-agent` lane subsequently ran (`reports/phase-goal-mcp-loop-iter-11-ui-test-results.md`, 07:02) against a live backend at :8255 / frontend at :3255 and passed **15/15 with 0 skips**, satisfying the spec's REQUIRED browser lane. No action.

**T3 — OBSERVATION: `status.json` `browser_checks_run:false` is stale, not a real skip**
`status.json` was last written 06:08 (before the browser lane ran at 07:02); its `browser_checks_run:false` predates the real run. The spec NOTES explicitly warned against trusting this flag. The genuine evidence — the ui-test-results file, 11 timestamped screenshots (06:41–06:59), and the ux-regression report (07:08) citing individual UT verdicts — confirms the lane ran. No action.

---

## 3. Domain Assessment

The core domain contract is honesty of evidence, and it holds. Proven-ness flows exclusively from a PASS-backed certified-claim whose cohort selectors (factor + slice_kind + decile + horizon + direction) match exactly; nothing in the UI recomputes it. The displayed h60 numbers (+8.91% holdout, +8.91% vs SPY, p=0.0004998) byte-match `certified-claims.jsonl` line 5, satisfying the "displayed numbers are correct" anti-goal. The claim is intentionally signal-less and is correctly kept out of `proven_signals`, so it backs the factor lab only and never lights a `/stocks` score badge (anti-goal #1). The subtitle framing ("Out-of-sample edge — factor top decile · 60-day hold") is pure historical-evidence language — no return promise, price target, or buy/sell (anti-goal #2). Determinism and no-lookahead are preserved trivially because no engine code changed; the h60 verdict's in-sample/holdout split (`in_sample_dates=724`, `purged_in_sample=1361`, `holdout_dates=243`) is the gate's, reproduced verbatim. The promotion tightened the user-facing Bonferroni bar 4→5 permanently, and only the modest signal-less `vcp_contraction` +0.089 winner was promoted — the implausible `rs_spy_3m` +0.21 p-floor edge and the config-declared `leadership_score` fallback were correctly excluded (no scope creep; J-08 deferred).

---

## 4. Fixes Applied During This Audit

None required. No critical or important issues were found. The implementation matches the spec's exact scope with no drift.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes needed |

---

## 5. Recommended Next Step

**Proceed.** J-07 is complete and browser-verified end-to-end; every required-still-passing journey (J-06, J-05, J-01/J-02/J-03, J-04) is confirmed non-regressed at both the data-contract and browser levels. The next iteration (iter-12+) promotes the pre-registered 2-factor combination for J-08 on `/research/factor-combination` + `/evidence`, which will face the now-tightened Bonferroni divisor 6 (required_p ≈ 0.00833) that this iteration's canonical write established. GOAL_ACHIEVED becomes reachable once J-08 lands browser-verified.

**Minor, non-blocking follow-up (optional):** iter-12 browser-qa could capture one explicit `/stocks` screenshot to close the small observability gap the ux-regression reviewer noted — a `/stocks` regression is already architecturally impossible here (signal-less claim + unchanged `/stocks` code + `proven_signals` pinned byte-identical), so this is documentation completeness only, not a functional risk.
