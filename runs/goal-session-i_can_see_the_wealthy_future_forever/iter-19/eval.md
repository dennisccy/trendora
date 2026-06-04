# Iteration 19 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** lean (session complete — only a lean re-verify if ever resumed; nothing left to build)

## Summary

J-32 (the Research All-history ⟷ As-of-date point-in-time toggle) — **the last buildable must-have journey** — landed cleanly and is verified **passing** in source, live browser flows, and unit tests. With it, the entire **buildable set is 29/29 passing** (J-01…J-21, J-25…J-32). The principal anti-goal risk (J-18, "exactly one date selector") was re-confirmed **held** in source and live; nothing regressed (additive /research-only diff, scoring/snapshot path git-verified untouched, no DB regen); coherence is **COHERENCE-PASS**. J-22/J-23/J-24 remain externally data-walled, recorded honestly blocked (NA), and are **non-halting / non-vetoing** per the operator's re-scoped `docs/goal.md` (lines 99–103, 755–765, commit d723133). The goal is achieved on its defined success criteria.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| **J-32** (Research as-of/all-history toggle) | failing | **passing** | `reports/qa/…-iter-19-evidence/UT-05-asof-2022-10-07-reduced-n.png`, `UT-06-all-history-restored-fullsample.png`, `UT-03-asof-mode-at-latest.png`; browser 12/12; backend 476 passed |
| J-18 (one date control — principal risk) | passing | **passing** (re-verified source+live) | `UT-08-single-date-control-header.png` (1 date `<select>` in `<header>`, 0 in `<main>`; toggle = button group) |
| J-15 (read-path / no wasted refetch) | passing | **passing** (critical, network-asserted) | `UT-06-all-history-restored-fullsample.png` (All-history mode → 0 `/research/*` fetches on global-date change) |
| J-25 (decile + rank-IC) | passing | **passing** (re-points in As-of) | `UT-05-…`, `UT-11-leaderboard-setup-Actionable.png` |
| J-26 (composite combination cohort) | passing | **passing** (re-points; composite 244→25→NA honest) | `UT-05-…`, `UT-11-…` |
| J-27 (regime-conditioned effectiveness) | passing | **passing** (renders + re-points) | `UT-01-default-all-history.png`, `UT-11-…` |
| J-29 (event-study lab) | passing | **passing** (honest empty `n=0` at early date) | `UT-05-…`, `UT-11-…` |
| J-30 (volatility factor family) | passing | **passing** (renders + re-points) | `UT-01-…`, `UT-11-…` |
| J-31 (synthesis travel) | passing | **passing** (cross-link → `/stocks?setup=Actionable`) | `UT-11-leaderboard-setup-Actionable.png` |
| J-06 / J-07 (score consistency / Risk-Off gate) | passing | **passing** (byte-identical — scoring/snapshot path git-untouched, no DB regen) | `git status --porcelain` empty for scoring/scanner/regime/buckets/snapshot_serving |
| J-01–J-05, J-08, J-11–J-14, J-16, J-17, J-19–J-21, J-28 | passing | **passing** (carried — additive /research+api.ts-confined diff → no regression possible) | prior-iter evidence (iters 1/5/6/8/9/10/16/17) |
| **J-22** (~500-name universe) | failing | **failing — honestly blocked (NA), NON-HALTING** | externally Yahoo-429 data-walled; not re-probed (spec forbids); does not veto |
| **J-23** (intraday multi-timeframe bars) | failing | **failing — honestly blocked (NA), NON-HALTING** | unbuilt + data-walled (same wall as J-22); does not veto |
| **J-24** (chart timeframe selector) | failing | **failing — honestly blocked (NA), NON-HALTING** | unbuilt (depends on J-23 intraday data); does not veto |

**Buildable set: 29/29 passing.** J-22/J-23/J-24 honestly blocked NA, non-halting per the re-scoped goal.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| **Exactly one date selector** (the principal risk this iter) | **OK — RESOLVED, re-confirmed held** | SOURCE: `research/page.tsx` `mode:"all"\|"asof"` is a string (no date state); `asofCutoff = mode==="asof" ? asOf : null`; `asOf` solely from `useAsOf()`; no `input[type=date]`/`DatePicker`. LIVE (UT-08): exactly 1 date `<select>` in `<header>`, 0 in `<main>`. The `?as_of=` transmitted is the single global date (MEMORY `j18-asof-on-stocks-fetch-is-correct`), not a 2nd control. |
| **No recompute in read path** / **Research lab read-only, not predictive** | OK | Forbidden-call grep (`run_scan`/`score_stocks`/`backfill*`/`forward_return`/`detect_*`/`score_regime`/`forward_excursions`) in `research.py` hits **only** docstrings (lines 12/15/498/499/876/879/880). As-of mode is a pure SELECT-only membership FILTER (`ScannerRun.asof_date <= as_of`); `as_of=None` adds no clause → byte-identical all-history. |
| **No lookahead** | OK | The as-of filter pools only `ScannerRun.asof_date <= D`; `..._no_future_run_leak` unit tests green for all 3 labs; cutoff reads canonical `ScannerRun.asof_date` (not denormalized `ForwardReturn.asof_date`). |
| **No fabricated data** / **Honest limitations** | OK | Early-cutoff low-sample cells render **NA + n** (composite 25 < min_sample 30 → NA; event-study honest empty `n=0`, no 500); survivorship/universe-relative banner persists in **both** modes (UT-05/UT-09). |
| **Snapshots immutable** / **No DB regen** | OK | Out-of-scope files git-verified untouched; no scoring/snapshot/forward_testing storage change → J-06/J-07 byte-identical. |
| **No secrets / No order-execution path** | OK | None introduced (read-only filter + query param + UI toggle). |

No anti-goal violation introduced. No critical anti-goal open. Coherence: **COHERENCE-PASS** (no structural veto).

## Next-Step Recommendation

**Halt — goal achieved.** No outstanding *buildable* work: the entire buildable set (J-01…J-21, J-25…J-32 = 29 journeys) is `passing` with directly-verified evidence, anti-goals hold, and coherence passes. The three remaining journeys (J-22/J-23/J-24) are externally Yahoo-429 data-walled and explicitly **non-halting / non-vetoing** per the re-scoped goal — they auto-heal via the committed finish runbook (no code change) once an operator confirms a reachable no-key OHLCV+market-cap (J-22) / intraday (J-23/J-24) egress. **Do NOT autonomously re-probe them.** If the session is ever resumed, only a lean re-verify is warranted — there is nothing left to build.

## Halt Justification

This iteration meets the goal's definition of success on every rule:

1. **Every *buildable* must-have journey is `passing`** (J-01…J-21, J-25…J-32, 29/29) — each with positive evidence (this iter's browser 12/12 + backend 476-passed for the /research set; prior-iter screenshots + a sound zero-regression structural carry for the rest, the diff being additive and the one shared file `api.ts` confined to the 3 research fetchers).
2. **J-22/J-23/J-24 do not block completion.** The operator-authored `docs/goal.md` was deliberately re-scoped (commit d723133) so these three data-dependent journeys, when the provider is unreachable, are "recorded as honestly blocked / limited-coverage (NA) and **MUST NOT halt the loop, drive a STALLED verdict, or veto GOAL_ACHIEVED**" (goal.md:755–765; reaffirmed at 99–103). This explicit, project-specific instruction takes precedence over the framework's generic "all journeys passing" guardrail, and the iter-19 spec documents the intended outcome verbatim ("after J-32 lands and nothing regresses → GOAL_ACHIEVED is reachable on the buildable set").
3. **No critical anti-goal violation exists** — the single historical minor one (one date selector) stays RESOLVED and was re-confirmed holding in source + live (the exact seam J-32 stressed most).
4. **Coherence is not COHERENCE-FAIL** — it is COHERENCE-PASS (no duplicate home, no second computation, no second date control).

The session has delivered a complete, coherent, evidence-tested product: a local-first leadership scanner with immutable walk-forward snapshots, three independent explainable scores, a single global as-of control governing every date-scoped page, as-of-scoped Backtest evidence, the full Research analytics suite (Factor Lab decile/IC/composite/regime/volatility + event-study), and now a point-in-time walk-forward toggle over those labs — all read-only over canonical stored values, with honest NA and survivorship labelling, and no lookahead / no fabrication / no order path.
