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

## iter-3 — 2026-06-01T13:00:00Z

**Verdict:** CONTINUE
**Lesson:** The config-selected live provider (`stooq`) is effectively unusable for live fetch in this environment — Stooq now gates its free daily-CSV endpoint behind an API key and returns an HTML "apikey required" page instead of CSV. `StooqProvider` correctly treats the non-CSV body as `ProviderUnavailableError` (fabricates nothing), so J-17's **live-fetch** half can only ever be proven by the forced-failure/no-fabrication path offline; the offline **backfill** path is what makes J-17 testable (and grows System Health `n` deterministically from committed seed bars). Any future iteration that needs *real* live data must first swap in a working free EOD provider behind the same `PriceProvider` interface (env-only key) — do not assume `stooq` live fetch works.
**Applies to:** any iter touching `apps/backend/app/data_providers/` or relying on the Data Manager live-fetch path / a "going-forward refresh" beyond the seed's last date (2026-05-28).

## iter-3 — 2026-06-01T13:00:00Z (process)

**Verdict:** CONTINUE
**Lesson:** Full-depth goal iters in this session keep finishing WITHOUT a `status.json` or an `auditor` handoff (recurred in iter-2 and iter-3); QA reports may even cite a `status.json` that is not on disk. Do not block on or trust those artifacts — verify the critical anti-goal seams yourself in source. Also de-dup QA evidence: iter-3 shipped two byte-identical screenshots (`TC-16-2`==`TC-16-3`), so a "final summary" claim rested on a copy of the "running" shot until cross-checked against the distinct browser-QA shots + API ground truth.
**Applies to:** any goal-evaluator run on a full-depth iter in this session (check `iter-<N>/` for status.json/audit before relying on them; md5 suspiciously equal-sized evidence).

## iter-4 — 2026-06-01T15:30:00Z

**Verdict:** CONTINUE
**Lesson:** The browser-QA agent can time out (exit 124) mid-run, leaving an auto-written **SKIPPED stub** `ui-test-results.md` *while having captured a partial set of real screenshots*. Do NOT take the stub at face value (it pre-suggests "ESCALATE") and do NOT trust a missing results file as "all failed" — inspect the evidence directory directly and read the screenshot timestamps to reconstruct how far the run got. Convert a `partial` ONLY if the journey's **defining step** was actually captured: here J-02/J-16 had complete flows (passed), but J-11's after-restart persistence shot and J-15's warm-load timing were never reached, and J-06's three-score cards were below the fold — so those three stay `partial` even though their earlier/structural evidence looks green. A timed-out QA step is a tooling failure → a hardened lean re-verify, NOT an ESCALATE (no functional gap, no code needed).
**Applies to:** any goal-mode closure/re-verify iter that depends on browser-QA full-flow evidence; any iter where `ui-test-results.md` is a SKIPPED/stub but the `*-evidence/` dir is non-empty — always reconcile the two before assigning journey statuses, and scope the re-run to the journeys whose defining step is unproven.
