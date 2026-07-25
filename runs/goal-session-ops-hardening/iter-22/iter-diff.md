# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
diff --git a/docs/improvement-backlog.md b/docs/improvement-backlog.md
index f0230c05..cb59d4bf 100644
--- a/docs/improvement-backlog.md
+++ b/docs/improvement-backlog.md
@@ -3104,6 +3104,7 @@ Safe, always-available work for weak models; each card small, none touching deci
 | B-1104 | DB maintenance & size monitoring | P3 | Q3+ |
 | B-1105 | One-command rebuild with verification receipt | P2 | Q2+ |
 | B-1106 | runs/ retention policy | P3 | Q3+ |
+| B-1107 | Bound concurrent historical background computes | P2 | Q3+ |
 
 #### B-1101 · Performance budgets + regression checks *(condensed)*
 **What & why:** the 30y basis made pages heavier (goal.md flagged charts); set measured budgets for the hot paths (`/stocks`, stock detail incl. chart, `/market-phase`, factor lab) against the fixture DB in CI; fail on regression beyond tolerance. Generalizes J-10's chart-performance acceptance product-wide.
@@ -3135,6 +3136,18 @@ Safe, always-available work for weak models; each card small, none touching deci
 **How:** policy doc + archive script with dry-run + first supervised run. Size: ~1 iteration. ★ Fields: `N/A`/none/none. ★ **Do NOT touch:** `state/` ever; anything without a dry-run + owner ack.
 **Journey:** dry-run lists candidates correctly; state/ provably untouched; archive restorable. **Depends on:** none.
 
+#### B-1107 · Bound concurrent historical background computes *(condensed)*
+*(Added 2026-07-25 by owner sign-off during goal session `ops-hardening` iter-22 — a measured observation, not an invented idea. Status: `PROPOSED`. Difficulty: MEDIUM; ★ dominant failure mode: `scope-creep`.)*
+**What & why:** iter-20's fix dispatches a historical as-of forward-aggregate compute to a background thread, single-flight-guarded **per `(asof_key, dataset_version)` — not globally**. So viewing N uncomputed historical as-of dates dispatches N concurrent computes. Measured live (`reports/perf-budgets.md` § "Iteration 22", "Incidental finding"): with N=5, `VmPeak` plateaued **32 kB under the 6144 MB `ulimit -v` cap** (99.9995 % utilized), contention scaled worse than linearly (none of the 5 reached `ready` inside 180 s), and each window's per-horizon cadence stretched well past the ~14 s/horizon single-BCW baseline. Nothing crashed — every poll stayed HTTP 200 with `readiness: ready`, so J-07's no-wedge promise held — but a reachable UI pattern sitting at essentially zero memory headroom is a capital-safety risk on a box with a documented hard-reset history, not a curiosity.
+**How:** (1) add a global dispatch cap (semaphore/queue) around `ensure_historical_forward_aggregates_dispatched` — default a small N (1–2), config-surfaced; (2) requests beyond the cap keep returning the honest `refreshing` marker they already return (no new UI state, no blocking); (3) prove it with a live N-way probe reproducing the 5-date pattern and recording `VmPeak` + per-window completion vs the single-BCW baseline. Size: ~1 iteration; split at: cap mechanism vs the live N-way measurement.
+★ **Evidence Claim & ledger:** `N/A — this card must not introduce proven-language anywhere`.
+★ **Canonical value:** none — re-reads existing payloads; the cap changes scheduling only, never a served number.
+★ **Anti-goal boundary:** none.
+★ **Tests that will break:** the four `monkeypatch.setattr(..., "forward_aggregates_ingest_cached", ...)` tests in `apps/backend/tests/test_forward_testing_serving_split.py` (lines ~592/621/657/680) touch this dispatch area — note that those imports at `apps/backend/app/api/backtest.py:75` and `apps/backend/app/mcp/tools.py:38` are load-bearing `raising=True` targets and must NOT be "cleaned up" (verified iters 21–22).
+★ **Do NOT touch:** the compute itself, the per-key single-flight key, the `refreshing`/`ready` state machine (J-08), or any served value; this card bounds concurrency only.
+**Acceptance / DoD:** the N-way probe shows at most the configured number of concurrent computes; `VmPeak` stays under a recorded margin of the cap (not within kB of it); every poll still HTTP 200 with truthful readiness; a single-BCW window is unchanged versus its recorded baseline.
+**Journey:** N uncomputed historical dates viewed together dispatch at most the configured cap; memory margin and per-window completion are recorded in `reports/perf-budgets.md`; service stays honest and un-wedged throughout. **Depends on:** none (iter-20's dispatch mechanism already shipped).
+
 ---
 
 ## Track 12 — Investor workflow (the ritual around the engine)
```
