# Goal Session i_can_see_the_wealthy_future_forever — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-06-01T01:00:00Z

**Verdict:** CONTINUE
**Lesson:** When the Chrome-MCP tool layer is degraded, browser-QA's *negative* interaction findings are unreliable: this run QA marked J-18 PARTIAL claiming "no separate date dropdown" on `/backtest`, but `apps/frontend/app/backtest/page.tsx:53-58,112-208` clearly carries a page-local `BacktestDatePicker` with its own date state (and the evidence screenshot shows the dropdown) — a genuine "exactly one date selector" violation. Always confirm date-control / single-source-of-truth claims against frontend source, not just the browser-QA summary.
**Applies to:** any iter verifying J-13/J-18 or the "exactly one date selector" / single-source-of-truth anti-goals; any iter touching `apps/frontend/app/backtest/` or `components/asof-*`.


## iter-1 — 2026-06-01T08:30:00Z

**Verdict:** CONTINUE
**Lesson:** The global as-of date lives in an **in-memory app-shell provider** (`components/asof-provider.tsx`) with no localStorage/URL persistence by design — it survives client-side navigation (the path all the J-13/J-18 journeys take) but resets to Latest on a hard reload. Browser-QA must drive date journeys via in-app nav, not hard reloads; and any future feature that wants a shareable/deep-linkable or reload-surviving date (e.g. a J-17 Data Manager URL, or "share this date's view") will need to add URL/query-param persistence to the provider — it is not there today.
**Applies to:** any iter adding deep-link/shareable date URLs or expecting the as-of date to survive a hard reload; any browser-QA verifying J-13/J-18 (use client-side nav, not reload); iters touching `components/asof-provider.tsx`.

## iter-2 — 2026-06-01T10:30:00Z

**Verdict:** CONTINUE
**Lesson:** On `/backtest`, the J-19 distribution-panel mean is over the FULL observed set at the
selected horizon and legitimately differs from the scorecard's top-ranked-cohort mean shown directly
above it (different populations). The `distribution.mean == overall.mean` consistency invariant binds
ONLY the `/system-health` aggregate, where both are over the same observation set — asserted in
`test_forward_testing.py:527-529`. A future reviewer must NOT "fix" the per-date mismatch as an
inconsistency; doing so would break the honest cohort-vs-full-set semantics. Secondary: an opportunistic
single-screenshot re-verify (this iter's TC-17) confirms a surface exists but does NOT satisfy a
multi-step acceptance flow — J-02/J-06/J-11/J-15/J-16 stay `partial` until their full flows (filter
interaction, cross-page numeric compare, add+backend-restart, warm-load timing, VCP
filter→badge→detail→glossary) are actually exercised.
**Applies to:** any iter touching `app/engine/forward_testing.py` attribution/scorecard or the
`/backtest` vs `/system-health` mean displays; and any closure/re-verify iter intending to convert a
`partial` journey to `passing`.
