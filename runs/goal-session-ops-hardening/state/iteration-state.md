# Iteration State — ops-hardening

**After iteration:** 53 · **Date:** 2026-08-08 · **Verdict:** CONTINUE

## Journeys

5 passing (J-01 J-03 **J-04** J-08 J-09) · 3 partial (J-05 J-06 J-07) · 0 failing — 8 total. J-04 newly passing (first status move since iter-45); J-06 not re-verified this round (carried from iter-52).

## Active blockers

- **dev — `market_phase.py:217` and `:554`:** fetch `lookback_days` bars BY COUNT, then filter a `lookback_days + 1` day CALENDAR range, so the oldest qualifying bar can drop. Unreachable at the committed config (measured: 255 bars max in any `[d-365,d]` vs a 365 fetch; 37 vs 50) but the "byte-identical" claim in comment/handoff/Addendum 15 is false. Fix: `+1` each, plus a REAL TC-3 test — the 3 new market-phase tests compare treated-vs-treated and structurally cannot detect it.
- **dev — verification bookkeeping:** `UT-J-04`/`UT-J-05`/`UT-J-07` have no journey-level row for the 3rd round; `runs/goal-session-ops-hardening/journey-scripts/J-05.json` EXISTS and was not replayed; J-04 and J-07 have no golden at all.
- **dev — last stall:** 1 `/api/health` non-answer in 1,643 during a data job, inside `per_date_coverage_warm` (`_persist_per_date_coverage_snapshots`) — untreated, same fix shape as the two just fixed.
- **dev — `market_phase.py:1168`** `_benchmark_close_on_or_before` still does a full-history read ~2,900x per request on `/api/market-phase/retrospective`; `close_on` is already imported in that file.
- **pipeline honesty:** QA says PASS while the merged browser lane says BLOCKED; QA's TC-6 tick cites screenshots that post-date the QA report by 14-45 min. 4th round of this class.
- **human (owner), unanswered since iter-50/51:** (a) may heavy compute move off-process? (b) does the 1,200s finalize-tail budget bind while the app serves traffic, or only when idle?

## Last 2 verdicts

- iter 53: CONTINUE — J-04 newly passing (badge/crash/interrupted captured, plus logfile chain and DB row verified independently); TC-9 held for the first time in 7 rounds; audit found a latent off-by-one no other lane caught.
- iter 52: ESCALATE — the round's own fix landed AFTER its lane ran (TC-9 breach), so no journey moved.

## Do not redo

- **J-04's boot/badge/crash/interrupted behavior is proven code AND now proven by evidence** — do not rebuild it; only its `[NEW]` walkthrough is owed (capture-only, `evidence_makeup: true`).
- **The two named finalize-tail phases are DONE**: `coverage_membership_timeline_refresh` 46.05→40.54s and `market_phase_warm` 26.26→0.73s, both at **zero** non-answers (perf-budgets.md Addendum 15).
- **AG-10 frozen surfaces are clean** — do not re-diff `config.yaml`, `host-guard.env`, `start-backend.sh`, `dev.sh`, `start-frontend.sh`; both `git diff` and `git status` over all five are empty.
- **The lane-runs-last rule works when written into the spec's DoD** — keep iter-53's DoD-5/TC-7 wording ("audit files a note for the next iter, never a code-changing fix"); do not re-litigate it.
- **`forward_aggregates_warm` and `factor_lab_all_warm` are NOT regressions** — Addendum 15's worse 1,559.30s total is scheduling luck on untouched phases; do not chase it as a bug.
- Deferred a 19th time, still out of scope unless the owner promotes it: iter-33/g the Regime Lab (its data call MemoryErrors; its golden asserts only the page heading — iter-52/cl, iter-52/cn).
