# goal-mcp-loop-iter-27 Audit Report

**Date:** 2026-07-12
**Auditor:** Hard audit pass (re-audit after second fix pass) — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal is achieved. The full-universe (322-date × 541-member) "Rebuild snapshots" job now runs to a
verified completed state under the literal `ulimit -v 6291456` cap without exhausting memory or crashing the
backend — the exact anti-goal #8 violation that halted iter-26 and that my prior audit correctly FAILed on.
The crash is fixed and re-confirmed **live via the canonical browser-qa lane** (three consecutive rebuilds,
all `status:"ok"`, `VmPeak` flat at 5,147,876 KB with 1,116 MB margin, no `MemoryError`), satisfying the
iter-24 lesson that an engine-level fix alone is not sufficient. The second-pass change is byte-identity-
neutral (allocator/OS-return behavior only), which I confirmed by direct diff-reading plus an independent
import/config-validation exercise. Three documented, non-blocking gaps remain (a latent config-guard hole, two
pre-existing `/data` UX affordances, and a browser-lane SKIP of the cold-start/backend-down repro) — none
compromise the phase goal, hence PASS_WITH_GAPS rather than clean PASS.

---

## 2. Findings

### Backend Findings

**B1 — GAP (observation): `IndicatorsCfg._validate` guard omits `breadth_short_ma`/`breadth_long_ma` (carry-over B3)**
`apps/backend/app/config.py:318-327` — the `max_needed = max(...)` guard that enforces
`max_lookback_bars >= largest configured indicator window` does **not** include `breadth_short_ma` or
`breadth_long_ma`. As of iter-27, `regime._universe_stats` (`regime.py:73`) reads its breadth inputs through
`bars_asof_window(..., lookback=max_lookback_bars)`, i.e. its correctness now depends on
`max_lookback_bars >= breadth_long_ma`. Today this is byte-safe: `breadth_long_ma = 200` (config.yaml:644) is
already covered because `max(ma_periods) = 200` (config.yaml:634) is in the guard tuple, and
`max_lookback_bars = 320 >= 200`. The risk is purely latent: a future config that raised `breadth_long_ma`
above `max_lookback_bars` would silently truncate the breadth series (`_universe_stats` would compute the
long-DMA over only 320 bars instead of the configured window) with no load-time error. Byte-safe on the
committed config today; requires an out-of-scope config change to trigger. **Not fixed** — fixing it (adding
two entries to a `max()` tuple) is scope creep against a verification/memory-hardening pass, and the reviewer
already logged it as a MINOR carry-over. Recommend the next config-touching iteration close it.

**B2 — OBSERVATION: second-pass memory-hygiene is correctly non-swallowing and best-effort**
`apps/backend/app/engine/data_manager.py:2400-2402` (`_release_process_memory`) and `:2533-2580`
(`_do_backfill`'s new `try/finally`). Verified directly: the `finally` wraps the whole `prefilled_bar_cache`
block with **no `except`**, so it releases memory on every exit path (serial `return`, parallel fall-through,
and exception propagation) **without swallowing** any exception — a raised compute error still propagates.
`_release_process_memory` guards the glibc `malloc_trim` call in `try/except (OSError, AttributeError)` so it
degrades to a bare `gc.collect()` on non-glibc; I exercised it live and it ran without raising. No silent
failure or new escape hatch introduced by the fix.

### Frontend Findings

**F1 — GAP (observation): no `/data` re-rebuild guardrail; no client-side readiness-poll timeout (carry-over)**
No frontend source changed this iteration (verification-only; `git diff --stat HEAD -- apps/frontend/` empty,
independently confirmed by the ux-regression reviewer). Two pre-existing UX gaps remain open by design:
(a) `/data` gives no button-state/rate-limit signal discouraging a second back-to-back "Rebuild snapshots"
click — practically de-risked now that the backend genuinely sustains consecutive rebuilds (re-verified 3×
live), but still an affordance gap; (b) a wedged (TCP-accepting-but-unresponsive) backend would show a
perpetual "Checking backend…" skeleton rather than degrading to the iter-25 "Backend unavailable" contained
card, because the readiness poll has no client-side timeout. Both are pre-existing, non-blocking, and outside
this pass's scope. Document; do not fix.

### Test Findings

**T1 — GAP: browser-qa lane SKIPPED the cold-start/backend-down repros (UT-01 / UT-13 / UT-14)**
`reports/phase-goal-mcp-loop-iter-27-ui-test-results.md` — the canonical browser-qa agent was denied
permission to stop/restart the coordinator-managed backend, so the DoD's browser-lane "stop → cold-start →
`/data` as FIRST request ×2" (UT-01), the backend-down "Backend unavailable" contained-card (UT-13), and the
recovery-after-restart (UT-14) were SKIPPED (verified: no side effect occurred, PID/health unchanged). The
**cold-start OOM concern itself is covered** at HTTP level: QA and the dev pass both ran the cold
`GET /api/data`-first repro ×2 (both 200, VmPeak ~3.5 GB, byte-identical `capacity`; perf-budgets Item H).
What was NOT re-driven live this round is the browser-lane `/data`-page degradation UX (the iter-25 boundary
card). Since no frontend source changed, this diff introduces no regression risk to that path — but it is a
genuine DoD browser-lane coverage gap (only an untested path, not an observed failure). Non-blocking per the
coordinator's evidence; the next QA setup should grant backend-lifecycle permission or have the coordinator
perform the stop/cold-start on the agent's behalf.

**T2 — OBSERVATION: `malloc_arena_max` has no dedicated unit test**
`apps/backend/app/config.py:570` — no test directly asserts `malloc_arena_max`'s positive-int validation or
default, mirroring the equally-untested sibling `memory_cap_mb` (not a new gap this pass introduces). I
exercised it directly during this audit: `ServerOpsCfg(malloc_arena_max=0)` raises `ValidationError`, and
`load_config().server.malloc_arena_max == 2`. Behaviorally covered; a dedicated test is optional.

---

## 3. Domain Assessment

The core-domain risk in this iteration is not scoring math — it is **not changing** any computed value while
bounding memory. That gate holds.

- **Read-side windowing (first pass, kept):** `prices.bars_asof_window` computes `full[max(0,cut-lookback):cut]`
  (cache path) or `WHERE date <= d ORDER BY date DESC LIMIT lookback` + reverse (default path) — both
  mathematically equal to `bars_asof(...)[-lookback:]`, same rows, same ascending order, same `date <= d`
  no-lookahead boundary. `regime._index_ma_stack`/`_universe_stats` route through it at
  `lookback=max_lookback_bars` (320), which is `>= max(ma_periods)=200` and `>= high_window_52w=252`, so every
  consumer's trailing read is untouched; `_latest_vix` routes through the O(1) `close_on` (same "no bar → None"
  behavior). The byte-identity is genuinely gated, not asserted: `test_scoring_window.py` asserts exact
  `windowed == unwindowed` for `score_stocks` and `score_regime` over ≥3 deep-history cadence dates × full
  pool (with a vacuous-pass guard requiring a member with `> max_lookback_bars` bars), plus a short-history
  case; `test_bars_asof_window_matches_tail_slice_default_and_cached` asserts exact equality of
  `bars_asof_window` vs `bars_asof(...)[-lookback:]` across both paths and every boundary (`cut==0`,
  `cut==len(full)`, `lookback>cut`, no-bar symbol). These are tight tests, not loose ones.

- **Second pass (the actual fix for the live crash):** `server.malloc_arena_max=2` (exported as
  `MALLOC_ARENA_MAX` by `start-backend.sh` **before** `ulimit -v` and `exec uvicorn` — correct order, verified)
  plus per-job `gc.collect()` + `malloc_trim(0)` in `_do_backfill`'s `finally`. This targets the diagnosed root
  cause (cross-job glibc-arena VSZ retention, not a leaked Python object), is allocator/OS-return behavior only,
  and changes no stored or served value. The reviewer independently re-ran the byte-identity suite (4/4, plus
  config 111/111) and confirmed `prices.py`/`regime.py`/`scoring.py` are untouched this pass, so windowing
  byte-identity is preserved by construction.

- **Live resolution of the halting defect:** browser-qa drove the exact previously-crashing path — a second
  (and third) consecutive full-universe rebuild in one long-lived process — through the real `/data` UI. All
  three reached `status:"ok"` 322/322 with `/api/health` 200 at every poll including the deep-history tail
  dates where the pre-fix crash occurred, and `/stocks` rendered 541/541 rows afterward (proving the process,
  not just individual requests, survived). Job progress was monotonic and never "done early" (UT-03). This is
  the canonical-lane confirmation the iter-24 lesson requires; anti-goal #8 is legitimately `resolved=true` on
  the driven journey path. Determinism and no-lookahead are preserved.

The memory measurement honesty is a strength worth noting: the dev/QA reports and perf-budgets Items G/H are
explicit that the isolated harness (~3–3.8 GB) cannot reproduce the live 6 GB ceiling and therefore cannot, by
itself, prove the fix — deferring the authoritative claim to the live lane, which then delivered it. Ambiguous
evidence was surfaced honestly rather than overclaimed.

---

## 4. Fixes Applied During This Audit

None. The state is confirmed-good and byte-identity-neutral; the only open items are GAP/OBSERVATION-level
(B1, F1, T1, T2), which are out of scope to fix per the severity rubric and the coordinator's explicit
instruction not to apply a speculative fix that could break the confirmed-good state. No CRITICAL or IMPORTANT
finding survived verification.

---

## 5. Recommended Next Step

**Proceed** — close iter-27 as PASS_WITH_GAPS. The unresolved critical anti-goal #8 that blocked iter-26 is
resolved and live-verified; all 8 required-still-passing journeys are re-verified live PASS. Carry these
documented, non-blocking gaps forward (do not bundle into this pass):

1. **B1** — add `breadth_short_ma`/`breadth_long_ma` to `IndicatorsCfg._validate`'s `max_needed` tuple the
   next time config is touched (latent guard hole; byte-safe today).
2. **T1 / F1** — the next iteration's QA setup should grant the browser-qa agent backend-lifecycle permission
   (or have the coordinator perform the stop/cold-start) so the cold-start-first `/data` and backend-down
   "Backend unavailable" contained-card repros (UT-01/13/14) are re-driven by the canonical lane; optionally
   add the `/data` re-rebuild guardrail and a client-side readiness-poll timeout.

Per the spec's own reachability note, GOAL_ACHIEVED remains out of reach after this pass — J-02/J-06/J-07/
J-08/J-09 stay sanctioned-partial (the separate priority-2 evidence work), which is correct and not a
regression.
