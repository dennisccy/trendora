# Iteration State — ops-hardening

**After iteration:** 48 · **Date:** 2026-08-05 · **Verdict:** ESCALATE

## Journeys

4 passing (J-01 J-03 J-08 J-09) · 1 failing (J-05, 5th consecutive) · 3 partial (J-04 —
DEFERRED-BUDGET, untested; J-06; J-07 — zero lane rows, 2nd round) — 8 total. J-01/J-03 promoted on
REAL `data_provider_runs` rows (305/306/307) the replay itself created.

## Active blockers

- **J-05 (dev):** a historical-gap backfill still never terminates — id=308 sat non-terminal 2h43m.
  This round's fix IS proven (id=304 reached `ok` in 13m52s, full 7-category `aggregates_refreshed`);
  the residual is two OTHER phases in `data_manager.py:3784-4127` — `forward_aggregates_warm`
  (102s / 153s / **1334s**; worst alone over TC-1's 1200s) + `drawdown_expectations_warm`. Bound both.
- **Regime Lab, 15th deferral (dev):** 2 new `MemoryError`s at `research.py:3630`/`:3640`
  (`_regime_lab_members_by_horizon`) INSIDE the J-06 replay window — blocks J-06 moving up.
- **Unrun checks (lane):** J-05's golden (rotated to 2012-01-05, confirmed unsnapshotted) never
  executed; J-04 deferred; J-07 has no row. **No owner blockers.** Ledger: 77 total, 28 unresolved,
  **0 unresolved critical**. scan CLEAN, coherence PASS.

## Last 2 verdicts

- iter 48: ESCALATE — J-05 failed a 5th round; two journeys moved up on real job rows; this round's
  own fix is proven but two older tail phases still block the job.
- iter 47: ESCALATE — J-05 failed a 4th round; the browser lane never re-ran after two fix passes.

## Do not redo

- **`samples.py` `total`/`regime` bound DONE** (`samples.py:159-216` + new
  `research._factor_regime_observations`) — byte-identity pinned, 5/5 pressure runs; iter-46/au CLOSED.
- **Gap-insert reuse branch DONE and correct** (`data_manager.py:891-917`), mutation-proven per-date
  keying (audit T1). Do NOT touch `_membership_timeline_incremental`/`append_forward`.
- **Finalize-tail phase timing EXISTS** (log lines) — use it. **AG-10 caps verified
  untouched/enforced** (`config.yaml` 8192/2, launch banners) — never re-tune.
- **J-01/J-03 goldens are genuine end-to-end drills now** — do not rewrite them; J-05's and J-06's
  are the weak ones (J-06 asserts headings only).
- **Evidence capture is never an iteration goal** — J-07 walkthrough (18 rounds), J-05 frames and the
  UT-05 retake ride the showcase / `Depth: evidence` lane.
