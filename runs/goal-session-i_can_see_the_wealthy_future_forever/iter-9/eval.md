# Iteration 9 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-28 (more detected patterns beyond VCP) **newly passes** — the last fully-autonomous compute-only journey. Two config-driven detectors (`pullback_to_rising_dma`, `flat_base_breakout`) landed as an additive extension of the VCP seams: filterable on `/stocks` with badges + reason + invalidation, auto-documented on `/methodology` from the config catalog, and surfaced as `by_<name>` pattern-vs-non-pattern forward-return breakdowns with honest `n`/NA on `/system-health`. All required-still-passing journeys hold; no regression; COHERENCE-PASS. **Not GOAL_ACHIEVED** — 9 must-have journeys remain failing (J-22/23/24 externally data-walled; J-25/26/27/29/30/31 are the unbuilt `/research` labs, whose nav re-approval was front-loaded this iter and pauses iter-10 for human approval).

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| **J-28** (target) | failing | **passing** | `…iter-9-evidence/UT-03-after-pullback-only-9.png` (filter 9/122 DOM-asserted) + UT-04/UT-05/UT-10/UT-11 + 5 source seams verified |
| J-02 | passing | passing (re-verified) | `UT-14-sector-setup-composed.png` (Tech 58 → +Avoid 40 → reset 122) |
| J-05 | passing | passing (re-verified) | `UT-08-detail-TPH-header-badges.png` (detail renders; scores untouched by diff) |
| J-06 | passing | passing (re-verified) | `TC-15-detail-TPH.png` (pattern values byte-identical leaderboard↔detail; scores read verbatim) |
| J-07 | passing | passing (re-verified, CRITICAL) | `TC-20-riskoff-actionable-zero.png` (2025-04-04 Risk-off → Actionable=0; patterns never promote) |
| J-08 | passing | passing (structural re-verify) | `…iter-3…/TC-18-scanner-runs-new-immutable.png` (DB regen → immutable snapshots; mirror written once) |
| J-09 | passing | passing (re-verified) | `UT-10-system-health-pattern-panels.png` (by_<name> panels + n) |
| J-12 | passing | passing (re-verified, extended) | `UT-11-methodology-new-pattern-cards.png` (6 setups + 3 patterns auto-rendered) |
| J-15 | passing | passing (structural re-verify) | snapshot-served read path untouched; detectors only on scan path (grep); keystone patch-to-raise test |
| J-16 | passing | passing (re-verified UNCHANGED) | `UT-13-vcp-only-4rows.png` (VCP 4/122; card + by_vcp panel intact; row['vcp'] byte-identical) |
| J-01, J-03, J-04, J-10, J-11, J-13, J-14, J-17, J-18, J-19, J-20, J-21 | passing | passing (carried) | additive pattern diff — patterns ride alongside; no score/setup/regime/as-of/watchlist change → no regression possible |
| J-22, J-23, J-24 | failing | failing (carried, out of scope) | externally data-walled (Yahoo 429); J-22 auto-heals via runbook only on operator egress confirmation |
| J-25, J-26, J-27, J-29, J-30, J-31 | failing | failing (carried, out of scope) | unbuilt `/research` labs; nav re-approval FRONT-LOADED this iter (marker written) → pauses iter-10 pre_decomposer |

## Anti-goal Check

| Anti-goal | Status | Notes (verified in source, not handoff) |
|-----------|--------|------|
| New patterns are patterns, not statuses *(critical)* | OK | `scoring.py:353` sets `setup` independently; patterns attached as separate keys (356-358); detectors never touch `classify_setup`/`setup`; `test_new_patterns_are_patterns_not_statuses` PASSED |
| VCP is a pattern, not a status *(critical)* | OK | `row["vcp"]` byte-identical; VCP filter/badge/glossary/by_vcp regress cleanly (UT-13) |
| No lookahead *(critical)* | OK | detectors run on `inv_closes` from `bars_asof(session, ticker, asof)` (≤ D); grep confirms references ONLY in `patterns.py` (def) + `scoring.py` (call) — never `api/` or `forward_testing.py` |
| No magic numbers | OK | `patterns.py` reads only `cfg.patterns.<name>.*`; only structural literals (rounding/percent); `test_no_magic_numbers` PASSED with new sentinels 40/18/25/15; config catalog rows are `ref:` paths |
| Snapshots immutable *(critical)* | OK | two indexed bool mirrors written ONCE in the single `ScannerResult(...)` (`scanner.py:109-111`); append-only column additions, no row UPDATE; DB regenerated offline from frozen seed |
| No recompute in read path | OK | `forward_testing.py:558-559,604,608` read `res.is_<name>` via generic `_group_means([True,False], pad=True)`; keystone patch-to-raise test confirms read path serves stored values |
| Risk-Off gates Actionable *(critical)* | OK | 2025-04-04 Risk-off → Actionable=0 (TC-20); both bootstrap dates still label Risk-off post-regen |
| Config-driven UI vocabulary | OK | `/methodology` cards + badge tooltips auto-render from the config catalog (3 patterns, 6 setups); `build_catalog` boot-guard fires on a missing entry |
| Honest forward-test for partial windows / no fabricated data | OK | System Health shows `n` per cohort + ⚠ on VCP n=27<30; new cohorts (n=48–1170) real; no threshold loosened to manufacture flags/sample |
| Single source of truth | OK | frontend re-displays server values only; all browser-asserted values match the API verbatim |
| No order/execution path, no secrets *(critical)* | OK | diff is engine/config/models/tests/frontend only; no brokerage/order/credential code |

**Coherence:** COHERENCE-PASS (no Data-Contract or Information-Architecture violation; both new values registered in `blueprint.md:140-141`; one trivial advisory on per-surface label length). No structural veto.

**Anti-goal violations introduced this iter:** none. The single historical minor one (Exactly one date selector) stays RESOLVED (since iter-1; re-confirmed — no date control added).

## Next-Step Recommendation

**Next iteration: `full` depth.** With J-28 closing the autonomous compute-only wave, the only remaining autonomous work is the **`/research` labs (J-25–J-31)** — compute-only over the stored seed (NOT data-walled). The `/research` nav re-approval was front-loaded this iteration (`state/blueprint.reapproval-requested` written; `blueprint.md:67` lists `/research` as ⛔ PLANNED iter-10+), so **`run-goal.sh` will PAUSE at iter-10's pre_decomposer (run-goal.sh:804) for human approval before the first lab is built**. After approval, target **J-25 (Factor Lab — decile sort + rank-IC per factor, raw and risk-adjusted)** as the entry point: it establishes the new `/research` page + the read-only lab-analytics seam (derive once from stored per-observation forward returns + stored factor values; never recompute in the API/view; honest NA + survivorship-bias label; descriptive, not predictive). Full depth is warranted — a NEW page/route/nav home crossing backend (lab endpoints + factor analytics) + frontend (new page), requiring the full pipeline (coherence, ux-regression, closure). Do NOT autonomously re-dispatch J-22/23/24 (Yahoo 429 wall persists; J-22 auto-heals via its committed runbook only on operator confirmation of a reachable no-key egress).
