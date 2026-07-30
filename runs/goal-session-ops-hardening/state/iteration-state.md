# Iteration State — ops-hardening

**After iteration:** 35 · **Date:** 2026-07-30 · **Verdict:** ESCALATE

## Journeys

6 passing (J-01 J-03 J-04 J-05 J-08 J-09) · 2 partial (J-06 J-07) · 0 failing · 0 unknown — 8 total. Both drops came from NEW live evidence, not from a code change (product tree byte-identical).

## Active blockers

- **iter-35 built nothing — process fault (framework/dev):** dispatched at `evidence` depth against a spec whose Definition of Done requires code; only `decomposer.done` + `browser-qa.done` ran. **Re-run `docs/phases/goal-ops-hardening-iter-35.md` at FULL depth — it needs executing, not rewriting.**
- **dev, FIRST AND BIGGEST (iter-29/d), now PROVEN LIVE:** `apps/backend/app/engine/prices.py:131-152` streams the whole `daily_prices` table into RAM (7-column `select`, NO WHERE, ~1.5 GB) on J-07's warm path via `_refresh_ingest_aggregates` → `refresh_coverage_snapshot` → `_compute_coverage_uncached` (`data_manager.py:814`) → `prefilled_bar_cache`. `docs/goal.md` forbids it verbatim. iter-35 measured VmPeak at **exactly** the 6,291,456 kB cap (zero margin) with 4 memory-pressure aborts → J-07 `partial`. The old "no memory is exhausted today" rationale is dead.
- **dev, cheap + structural (iter-33/h), now PROVEN LIVE:** `resolveLabLoadPanel` wired into `RegimeLabPage` only; `phase-severity-lab`, `regime-phase-factor`, `factor-lab`, `severity-velocity` keep the bare unlabelled `LabSkeleton` + no Retry. All four captured mid-slow-load showing blank grey placeholders (zero completed `/api/research/*` in the log window) → J-06 `partial`. Resolver is generic + exported: wiring only.
- **dev, NEW + small (iter-35/k):** `forward_testing.py:2325`'s unbounded `{(symbol, asof): (mdd, uw, ttr)}` dict on the `/api/evidence` per-claim path — failed twice live on a user-facing route.
- **dev:** J-07 step 3 requires the peak-memory margin in `reports/perf-budgets.md`; that file is untouched since iter-34, so iter-35's number exists only in `iter-35/eval.md`.
- **dev, carried, all minor:** iter-33/g (Regime Lab cold `view=pooled` 60-90 s + undiagnosed HTTP 200 "Internal Server Error"); `warmup.py:194` + badge wording after a failed warm-up (6 iterations unmade); iter-31/e; iter-32/f (WATCH only).
- **capture ride-alongs, never an iteration's goal:** the `[NEW]` walkthroughs J-06 and J-07 name — 5 iterations unrecorded (iter-35's demo lane emitted zero steps); `J-07.json`'s literal `1873` needs a provenance line.
- **OWNER, unchanged (iter-34/j):** `/api/health` ≤0.1 s budget vs 0/185 in-budget polls — ratify the honest-WARN convention, rescope the budget, or commission the cached-readiness fix.
- **OWNER, non-blocking (iter-33/i):** should `start-frontend.sh` join `HOST_GUARD_MARKER_FILES`?
- Ledger: **9 unresolved, 0 critical.**

## Last 2 verdicts

- iter 35: ESCALATE — nothing was built (wrong depth); the run proved two carried paper findings real, dropping J-06 and J-07 passing → partial. **Not a regression:** code byte-identical, health 506/506 200s, no crash, honest degradation, host caps contained everything.
- iter 34: CONTINUE — J-07 crossed to passing (drill + latency recorded); all 8 journeys green.

## Do not redo

- **Do NOT rewrite the iter-35 spec** — it already targets the right two items with the right proof obligations (TC-1/TC-2/TC-3: `git show HEAD`-pinned byte-identity oracle + mutation-style bound test). Execute it.
- **Do NOT read iter-35's browser-qa FAIL as a regression or as J-06 failing on `resolveLabLoadPanel`** — that Expected column quoted the spec's DoD, not J-06's goal text; the real basis is the four screenshots.
- **Do NOT re-run J-07's iter-34 memory-pressure drill from scratch** (`test_ingest_finalize_memory_pressure.py` + `perf-budgets.md:4330-4438`) — only re-verify against the new bounded path. J-07 step 2's latency is likewise DONE (`perf-budgets.md:4271-4329`).
- **Byte-frozen:** `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched`. **AG-10 marker files: zero diff, never weaken** — they contained iter-35's MemoryErrors inside one process.
- **Settled, do not re-open:** J-06's 11-page sweep (`perf-budgets.md:4099-4270`); `start-frontend.sh` prod mode; `merge_ui_test_results.py` `_ROW_RE`; the UT-11 fix for Regime Lab (extend, never rewrite); the `/api/health` budget as agent work (owner call).
- **Never make evidence capture an iteration's goal** — walkthroughs and screenshots ride along only.
