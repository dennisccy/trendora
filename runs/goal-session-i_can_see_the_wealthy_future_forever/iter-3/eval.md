# Iteration 3 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

J-17 (Data Manager — grow the dataset by date / date range), the **last unbuilt must-have**, landed and is **passing**: a new `/data` page orchestrates the canonical scan/return paths to backfill immutable snapshots from committed seed bars, surfaces live progress + a final summary, makes new as-of dates selectable in the global switcher without a hard reload, and grows the System Health sample (n). The required-still-passing set (J-07, J-08, J-09, J-13, J-14) was re-verified green and coherence is **COHERENCE-PASS**. **Not GOAL_ACHIEVED**: five journeys (J-02, J-06, J-11, J-15, J-16) remain `partial` — they were deliberately out of scope this iter and are the target of the next closure/re-verify pass.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| **J-17** Grow the dataset (Data Manager) | failing | **passing** | UT-07-UT-06-after-backfill.png; TC-16-5-system-health-n-grew.png |
| J-07 Risk-Off suppresses Actionable | already_passing | passing (re-verified) | TC-18-scanner-runs-new-immutable.png |
| J-08 Immutable scanner-run history | already_passing | passing (re-verified) | TC-18-scanner-runs-new-immutable.png |
| J-09 System Health forward-tested evidence | passing | passing (re-verified) | TC-16-5-system-health-n-grew.png |
| J-13 Global as-of switcher | passing | passing (re-verified) | UT-08-dashboard-backfilled-date.png |
| J-14 Backtest per-date scorecard | passing | passing (re-verified via backfilled date) | UT-08-dashboard-backfilled-date.png |
| J-18 One date control (no duplicate) | passing | passing (re-verified — J-17 risk) | UT-11-form-date-changed-asof-unchanged.png |
| J-02 / J-06 / J-11 / J-15 / J-16 | partial | partial (carried — out of scope) | iter-2 evidence (unchanged) |
| J-01, J-03, J-04, J-05, J-10, J-12, J-19 | passing / already_passing | unchanged (not retested) | carried over |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Live fetch is real-data-only *(critical)* | OK | UT-10/TC-17: forced Stooq failure → explicit `failed` badge, `0/158 ok · 158 failed · 0 new bars`, "(no data fabricated)". `_do_fetch` (data_manager.py:207-240) inserts only NEW `(symbol,date)` rows; on `ProviderUnavailableError` persists zero bars. |
| Range backfill / on-demand snapshots immutable & lookahead-free *(critical)* | OK | `_do_backfill` (data_manager.py:243-259) targets only `d not in snapshot_dates` (create-once), calls canonical `scanner.run_scan` (≤D) + `forward_testing.backfill_run_forward_returns` (>D). Re-run no-op verified (TC-08; live re-run `snapshots_created:0`). |
| No second computation path *(extends Single source of truth)* | OK | No score/bucket/return math in `data_manager.py` — verified by grep (only the two canonical calls at :254-255). Test asserts stored == fresh `score_stocks(D)` verbatim. |
| No fabricated data | OK | UT-10 zero fabrication on failure; UT-08 shows honest "NA / universe-relative" breadth on an early backfilled date (insufficient look-back), not a fabricated number. |
| Exactly one date selector *(critical, J-18)* | OK | `/data` imports `useAsOf` for `refresh` only (page.tsx:54), never `setAsOf`; date inputs are local `useState` job params. `refresh()` re-fetches runs and never mutates `asOf` (asof-provider.tsx:47-66). The pre-existing minor violation stays RESOLVED. |
| No recompute in read path | OK | `GET /api/data*` are thin wrappers over `compute_coverage`/`recent_runs`/`get_job`; coverage is descriptive metadata only. |
| Default boot path unchanged | OK | `main.py` lifespan still only `bootstrap_runs` + `backfill_forward_returns`; `data.router` added additively (line 79). No live provider reachable on boot. |
| No magic numbers | OK | Job limits read from `config.data_manager.{max_range_days,gap_preview,live_provider,run_history_limit}`; `test_no_magic_numbers` green. |
| No secrets in source | OK | grep of stooq_provider / data.py / data_manager.py for key/token/secret → empty; any provider key is env-only. |
| No order/execution path *(critical)* | OK | grep across all new files for broker/order/execute → NONE. |

## Next-Step Recommendation

Run the planned **closure / re-verify pass at lean depth** to convert the five remaining `partial` journeys via their **full** acceptance flows (not a single-screenshot surface check — the iter-2 lesson):

- **J-02** — Stock Leaderboard: apply the Sector filter (rows reduce to that sector) **and** the Setup-status="Actionable" filter (only Actionable rows, or explicit empty-state).
- **J-06** — Coherence: note NVDA's three scores on `/stocks`, open `/stocks/NVDA`, assert all three (and A–E buckets) are byte-identical.
- **J-11** — Watchlist: add ANET with a reason, confirm date-added/score/setup/price-since-added/invalidation, then **restart the backend** and confirm the entry persists.
- **J-15** — Warm-load timing: measure `/stocks` warm reach-interactive against the < ~1.5 s budget; confirm values match Stock Detail.
- **J-16** — VCP: filter → flagged rows show badge+reason+invalidation → open one detail → glossary entry → System Health VCP-vs-non-VCP breakdown with n.

If all five convert and nothing regresses (J-17/J-18/J-19 and the rest stay green, coherence stays PASS), the next iteration's verdict is **GOAL_ACHIEVED**. Escalate to full only if a "partial" turns out to be a genuine functional gap needing code (not just unverified). Lean is right because no new feature code is expected — this is browser-QA-driven verification of already-built surfaces.

## Process Notes (non-blocking; verdict unaffected)

- **No `status.json` and no audit handoff** were produced for this full-depth iter (only `coherence.md` + `snapshot-sha` exist under `iter-3/`). This recurs from iter-2. The QA report references a `status.json` that is not on disk. I substituted my own source-level verification of every critical anti-goal seam; the structural gate (coherence-auditor → COHERENCE-PASS) and review/QA/browser-QA all passed. Gap logged for the framework owner; it did not change the verdict.
- **Evidence-hygiene bug:** `TC-16-2-progress-running.png` and `TC-16-3-summary-ok.png` are byte-identical (same md5) — the "final summary" screenshot is a duplicate of the running-state one. The final-summary claim is still well-grounded: the distinct browser-QA shots (`UT-05-job-running.png`, `UT-07-UT-06-after-backfill.png`) and the API ground truth (run id=8: `status:ok`, 5 snapshots, 3200 forward returns) corroborate it. Future QA should de-dup evidence before recording.
