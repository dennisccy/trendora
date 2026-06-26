# Iteration 49 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-106 (Proximity-to-52w-high leaderboard column) and J-108 (honest readiness-badge fix) both flip
unknown → passing on genuine, evaluator-VIEWED live browser-QA evidence (12/13 PASS, 1 non-blocking
SKIP). The diff matches the coherence snapshot exactly and is anti-goal-clean: a frontend-only
re-display of the already-served `high_proximity` component (no new `/api/stocks` field) plus a
host-aware client base + dev-only CORS widening; main.py changed only its CORS factory. This is NOT a
GOAL_ACHIEVED candidate — J-107 (the all-factors Factor Lab table) is the sole remaining unbuilt,
NOT-data-dependent buildable Must-have and was deliberately deferred to iter-50. Progress made, zero
regressions, COHERENCE-PASS → CONTINUE.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-106 (52w-high column) | unknown (queued) | passing | reports/qa/…iter-49-evidence/UT-01-result.png, UT-02, UT-04, UT-06 |
| J-108 (honest readiness badge) | unknown (queued) | passing | reports/qa/…iter-49-evidence/UT-09-result.png, UT-10, UT-01 |
| J-107 (all-factors Factor Lab) | (none) | unknown — not built (deferred to iter-50) | — |
| J-01 (dashboard hydrates) | passing | passing | UT-10-result.png |
| J-06 (score consistency, CRITICAL) | passing | passing | UT-02-result.png (MU -0.53% column==breakdown) |
| J-07 (Risk-Off gate, CRITICAL) | passing | passing | backend gate untouched; QA TC-15 |
| J-18 (one date control, CRITICAL) | passing | passing | QA TC-16 (0 native input[type=date]) |
| J-40 (honest readiness) | passing | passing | UT-09 (Unavailable when down) |
| J-48 (column sort = view transform) | passing | passing | UT-13-result.png |
| J-75 (forward-return columns) | passing | passing | UT-01 / QA UT-11 (20 headers) |
| J-80 (header regime/theme strip) | passing | passing | UT-01 / QA UT-11 |
| J-104 (research lab loads after API_BASE change) | passing | passing | TC-20-research-loads.png / UT-12 |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Single source of truth | OK | high-proximity.ts is a pure lookup into the served `leadership.components`; column and detail breakdown call the same helper → byte-identical (MU -0.53% both, UT-02) |
| No recompute in read path | OK | Backend untouched except the CORS factory in main.py; no scoring/return/bucket recompute |
| No fabricated data | OK | UT-09 (byte-distinct) shows honest "Backend unavailable — Nothing is fabricated"; NA cells render "NA" not a number |
| Readiness reported honestly | OK | Ready (UT-10/UT-01), Initializing (QA UT-10 "history 9/9"), Unavailable (UT-09) all distinct; resolveApiBase re-resolves host only, never fakes readiness |
| No magic numbers | OK | No scoring literal added; api-base.ts uses a hostname set, not a tunable constant |
| Risk-Off gates Actionable (CRITICAL) | OK | Backend scoring/regime/gate diff empty; QA TC-15 |
| Scores explainable | OK | Detail breakdown still shows the named component (now the raw distance rather than an opaque percentile) |
| Setup/pattern vocab config-driven | OK | Glossary tooltip rendered from the config catalog (`52-week high proximity`, config.yaml:1212) |
| Exactly one date selector (CRITICAL) | OK | J-106 adds a SortKey not date state; J-108 changes only fetch host; 0 native date inputs (TC-16) |
| No secrets in source | OK | CORS_ORIGIN_REGEX read from env, set only by dev.sh; no hardcoded credentials |

No new anti-goal violations. The lone ever-recorded violation (iter-20 minor magic-number) stays
resolved since iter-21.

## Next-Step Recommendation

iter-50 FULL — build J-107 (Factor Lab all-factors Rank-IC + risk-adjusted table with expandable
per-factor decile sort; supersedes the single-factor dropdown view, retires the per-regime
effectiveness table from that view). This touches the cached-aggregate / streamed research read path
— the iter-46/47/48 OOM-sensitive area — so: build on `EventStudyCache` + `_dataset_version`
(byte-identical figures), keep the read path streamed/column-projected per J-105 (no unbounded
`select(...).all()`), order ScannerResult reads by `(run_id, id)` not bare `id` (the iter-48
temp-sort / disk-full lesson; host disk ~93% full), and register any new table in test_db.py's
expected-tables guard (iter-12/20 trap). Required-still-passing: J-25/J-26/J-29/J-77/J-91/J-103
(the research labs J-107 reorganizes), J-51/J-63/J-65 (N= sample coherence), J-104 (labs load
reliably), J-06/J-18/J-07 (CRITICAL), J-106/J-108 (this iter). Gate iter-50's GOAL_ACHIEVED
candidacy on the FLUSHED full-suite `0 failed, EXIT 0` (pump nohup-async; never block the evaluator;
NEVER concurrently probe heavy /research while load-testing — pool-exhaustion lesson). Evidence-
hygiene: PLAN the Playwright fallback up front; md5sum the dir FIRST; resolve sort/decile/N= controls
by aria-label not text(). After J-107 lands green on live evidence with a flushed-GREEN suite +
COHERENCE-PASS + zero regression, the next evaluation is a sound GOAL_ACHIEVED candidate
(J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing per goal.md:105-108).

For the next iter-49 evidence carry-over, also (cheap): capture J-106's NA-last live leg at a
short-history as-of date if one is reachable (UT-05 was SKIPPED — no NA rows in the warm seed), and
capture the J-108 LAN-IP Ready frame so it is independently distinguishable from the localhost frame
(UT-08 was a byte-dup of UT-01; the flip is substantiated by the curl + CORS test + the byte-distinct
Unavailable frame, so this is hygiene only, not a re-open).
