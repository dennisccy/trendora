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

## iter-6 — 2026-06-02T02:30:00Z

**Verdict:** CONTINUE
**Lesson:** In a full-depth iter the `qa` agent (its own Chrome-MCP browser checks) and the `browser-qa-agent` can run CONCURRENTLY against the same shared single-tab Chrome (port 9222), which silently corrupts captures (a "Latest" nav came back showing the other agent's historical state; an eval landed on the other agent's `/backtest`). The browser-qa-agent recovered only by WAITING for the qa agent to vacate the browser, then running all flows on a dedicated tab and asserting live state (`data-testid="asof-indicator"`, URL, values) immediately before each capture. Separately, the qa agent's `TC-15-before/after` shots came back byte-identical (same sha256) — the iter-3 duplicate-shot bug recurring — so the defining proof had to come from the browser-qa-agent's distinct UT-shots + a no-refetch fetch spy.
**Applies to:** any full-depth goal iter where BOTH the qa agent and the browser-qa-agent perform Chrome-MCP checks — serialize browser access (one agent vacates before the other captures), de-dup evidence by sha256, and ground any "before/after" claim on distinct shots + a DOM/network assertion, never a single screenshot pair.

## iter-7 — 2026-06-02T06:00:00Z

**Verdict:** STALLED
**Lesson:** The Yahoo-429 data-provider constraint (episodic memory) is not a soft warning — it is a HARD pipeline blocker for any iteration that needs a NEW bulk fetch from this egress. iter-7's J-22 universe expansion built complete, tested, auto-healing infra (offline `screen_universe.py`, an honest gate in `api/methodology.py` that hides the Universe-Selection section until a real `data/seed/universe.json` exists, and a committed finish runbook) but could not fetch OHLCV+market-cap for ~280–380 new names: Yahoo 429 on both hosts + crumb, Stooq captcha, nasdaq empty, SEC has no prices. Three fix cycles re-confirmed the same wall — and the framework's halt-for-environment verdict (non-regression) is STALLED, not the lean→full ESCALATE. **Two takeaways:** (1) any future iter needing a fresh bulk external fetch (universe expansion, J-23/J-24 multi-timeframe intraday) should PROBE the feed with one polite request FIRST and gate the whole iteration on reachability, rather than burning a full pipeline that reproduces the 429; (2) when a deliverable depends on an external one-shot fetch, build it to AUTO-HEAL — separate the committed/testable infra from the data step and gate the UI honestly — so it completes later with zero code change. The unblockable fallback when the feed is down is the compute-only `/research` labs (J-25–J-31, no new fetch), but those need a human blueprint nav re-approval first — consider front-loading that approval so a data-feed outage never fully stalls the loop.
**Applies to:** any iter that performs a new bulk external data fetch (universe/seed expansion, multi-timeframe/intraday bars), and any environmentally-blocked deliverable — probe-and-gate first, build to auto-heal, and prefer STALLED over blind-retry once the block is re-confirmed.

## iter-8 — 2026-06-02T09:30:00Z

**Verdict:** CONTINUE
**Lesson:** "The immediate target is externally walled" is NOT the same as "the session is stalled" —
distinguish them before reaching for STALLED. iter-8 retried the J-22 universe fetch on the (plan-time-GREEN)
Yahoo feed; the dispatch-time re-probe re-walled (429 both halves), so J-22 made no progress — but the
session still has tractable autonomous work, so the verdict is CONTINUE, not a second STALLED. The
non-obvious carve-out: **J-28 (additional detected patterns) escapes BOTH blockers** — it is compute-only
over the already-stored seed (no external fetch, unlike J-22/J-23/J-24) AND its acceptance explicitly
allows the pattern-vs-non-pattern breakdown on "the Setup & Pattern Lab **(or System Health)**", so it
rides the EXISTING /stocks + /methodology + System Health surfaces and needs **no /research nav home and
no blueprint re-approval** (unlike J-25/J-26/J-27/J-29/J-30/J-31, which do). `engine/patterns.py` +
`config.patterns=['vcp']` already make a new pattern a pure config-driven extension. iter-7's evaluator had
lumped all of J-25–J-31 as blueprint-gated and missed this. Also: STALLED's remedy is "edit docs/goal.md,"
which is the wrong signal when the goal is well-formed and only a data-feed dependency is blocked — prefer
CONTINUE + a hard "do not retry the walled target; build the compute-only work" pivot (the run-goal.sh
stall-hash is the independent backstop if the loop genuinely can't progress).
**Applies to:** any goal-evaluator run where the dispatched target is externally/approval-blocked but other
failing journeys remain — enumerate each remaining journey's gate (data-wall vs blueprint-reapproval vs
none) before choosing STALLED; a journey that is both compute-only AND satisfiable on existing surfaces is
autonomous work that forbids STALLED. Especially any iter touching the J-22/J-23/J-24 (data-walled) vs
J-25–J-31 (compute-only) split, and any decomposer choosing the next non-walled target.

## iter-9 — 2026-06-02T12:00:00Z

**Verdict:** CONTINUE
**Lesson:** "Config-driven UI vocabulary" is only PARTIALLY satisfied on the leaderboard. `/methodology` glossary cards and the badge *meaning* tooltip auto-render from the config catalog (by key), but `apps/frontend/app/stocks/page.tsx`'s `PATTERNS`/`NEW_PATTERNS` registries hardcode the short badge label + the filter option list — so a future config-only pattern auto-documents in the glossary yet will NOT auto-appear as a leaderboard badge/filter without a frontend edit. The full-config-driven path needs a short badge label added to `config.patterns.<name>` and the registry derived from `catalog kind:"pattern"` entries. (Reviewer rated this a non-blocking enhancement; the iter-9 spec explicitly contemplated a frontend pattern list, so it is not a defect — but it is the seam to close if "add a pattern with zero frontend edits" ever becomes an acceptance bar.)
**Applies to:** any future iter that adds a detected pattern (J-28 allows >2) or claims fully config-driven leaderboard UI vocabulary.

## iter-9 — 2026-06-02T12:00:00Z (loop-behavior note)

**Verdict:** CONTINUE
**Lesson:** iter-10 is the FIRST iteration to hit a front-loaded blueprint re-approval pause. `state/blueprint.reapproval-requested` was written this iter, so `run-goal.sh` halts at iter-10's *pre_decomposer* step (run-goal.sh:804) awaiting human approval of the new `/research` nav home BEFORE the decomposer plans the first lab — the loop will NOT autonomously proceed into J-25. The operator approves by re-running with `--resume` (their review of `state/blueprint.md` is treated as approval). After J-28, the `/research` labs (J-25–J-31, compute-only over the stored seed) are the ONLY remaining autonomous track — the data-walled wave (J-22/23/24, Yahoo 429) is not part of this approval.
**Applies to:** the iter-10 decomposer/evaluator cycle and the operator resuming the session.
