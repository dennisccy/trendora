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

## iter-10 — 2026-06-02T15:00:00Z

**Verdict:** CONTINUE
**Lesson:** `status.json` for this goal session is written to the PHASE-namespace path `runs/goal-<sid>-iter-N/status.json` (e.g. `runs/goal-i_can_see_the_wealthy_future_forever-iter-10/status.json`), NOT the goal-session path `runs/goal-session-<sid>/iter-N/status.json` that the goal-evaluator's artifact list cites (which holds only `coherence.md` + `snapshot-sha`). Several prior iters were logged as "no status.json produced" partly because of this — it was likely present at the phase path all along. A stale no-`_forever` twin (`runs/goal-i_can_see_the_wealthy_future-iter-10/`) also exists and is cross-session noise. The QA agent's "status.json present ✅" can therefore be correct even when the session/iter-N dir lacks it.
**Applies to:** any future goal-evaluator iter in this session checking for `status.json` / `plan.md` — check BOTH `runs/goal-<sid>-iter-N/` and `runs/goal-session-<sid>/iter-N/` before concluding an artifact is absent; the phase-namespace path is the real one for status.json/plan.md.

## iter-11 — 2026-06-02T17:30:00Z

**Verdict:** CONTINUE
**Lesson:** In this seed, forward-return observations exist for nearly the same snapshots at every horizon (`n_total` 1218 at 5d vs 1217 at 60d), so per-regime/per-cohort `n` is almost horizon-independent — you CANNOT reliably thin samples to exercise an NA / low-sample path by lengthening the horizon (the browser test's "60d → smaller n → more ⚠" expectation was only minimally hit). The honest-NA evidence instead had to come from (a) genuinely empty regimes with `n=0` (Strong risk-on, Defensive) and (b) the downside-only-undefined case (Risk-off: raw spread +16.50% numeric but `risk_adjusted_spread` NA because the top decile had no downside). Future /research lab tests should target those two NA sources directly, not horizon length.
**Applies to:** any future `/research` lab iteration (J-26 combination cohorts, J-29 event study, J-30 volatility family, J-31 synthesis) whose browser/unit tests must prove honest NA + n on low-sample cells — design the NA fixture around empty regime/cohort membership or the downside-undefined ratio, not around horizon-driven sample shrinkage.

## iter-14 — 2026-06-03T02:30:00Z

**Verdict:** CONTINUE
**Lesson:** J-31 (the final synthesis journey) step 4 says "open one on Stock Detail **across timeframes**" — but the timeframe selector (J-24) is unbuilt and externally Yahoo-429 data-walled. The next decomposer must scope J-31's acceptance to the **canonical daily timeframe** (which works) and treat intraday as honestly coverage-limited, NOT let the J-24 data wall block J-31. J-31 is otherwise compute-only over the seed on already-approved surfaces (no new computation expected — it is navigation/cross-linking + leaderboard filters reading canonical stored values), so it should add no read-path recompute; verify that seam in source as usual.
**Applies to:** iter-15 (J-31 synthesis) and any future iter whose journey text references a timeframe/intraday sub-step while J-23/J-24 remain data-walled.

## iter-15 — 2026-06-03T05:30:00Z

**Verdict:** CONTINUE
**Lesson:** The iteration's own DoD step `cd apps/frontend && npm run build` (a production build) clobbered the running `next dev` server's shared `.next/` — the dev server kept emitting HTML pointing at unhashed dev chunks (`/_next/static/chunks/main-app.js`) while disk now held only content-hashed PROD artifacts → framework-chunk 404 → a dead, un-hydrated SSR shell on EVERY route ("Checking backend…", 0 rows). This blocked browser-QA entirely (SKIPPED, not FAIL — reproduced in a clean isolated browser), so a clean, correct, statically-verified build of the **capstone** journey (J-31) could not be confirmed at its **defining multi-step browser flow** and had to be recorded `partial`, not `passing`. The smoking-gun check: `.next/static/chunks/main-app.js` ABSENT while `main-app-<hash>.js` + `BUILD_ID` + `build-diagnostics.json:static-generation` are PRESENT (matches MEMORY `browser-qa-dead-shell-next-cache`). The pipeline-ordering root cause: running the prod build against the same `.next` the live dev server serves from. Fix before re-verify: stop `next dev`, `rm -rf apps/frontend/.next`, restart, and run `npm run build` against a separate dir or before the dev server starts.
**Applies to:** any iter whose acceptance is a browser flow AND whose DoD runs `npm run build` against the live dev server's `.next` (especially capstone/cross-page journeys whose only proof is the captured travel) — confirm `GET /_next/static/chunks/main-app.js` → 200 and the health badge clears before driving UI tests; a dead-shell browser-QA SKIP is environmental, never a code FAIL/regression.

## iter-16 — 2026-06-03T08:30:00Z

**Verdict:** STALLED
**Lesson:** When the LAST buildable journey converts in the same iteration that exhausts the autonomous runway, the correct verdict is **STALLED**, not CONTINUE — even though ≥1 journey newly passed (which the literal CONTINUE rule matches). The operative STALLED signal is "I cannot identify productive next work," decoupled from the script's no-progress stall-hash. Returning CONTINUE here would dispatch a next iteration whose only options are a forbidden data-wall re-probe or a no-op, wasting a pipeline before stalling anyway. The J-31 progress is still preserved in journey-history regardless of the halt verdict, so STALLED costs no signal.
**Applies to:** any goal-mode iteration where the target was the final autonomous deliverable and the only remaining failing journeys are externally blocked (data feed, paid egress, human approval); also any session whose remainder is gated on operator action rather than code.

## iter-17 — 2026-06-04T04:00:00Z

**Verdict:** CONTINUE
**Lesson:** When the operator re-scopes `docs/goal.md` mid-session (here commit `d723133` after the iter-16 STALLED), it can (a) RAISE an already-`passing` journey's acceptance bar and (b) ADD new journeys — neither is visible in code or in the diff. J-26 was `passing` since iter-14 (strict AND-intersection) but the re-scope now demands a non-empty composite percentile-rank blend, so its current impl no longer meets the *headline* acceptance → I re-classified it `partial` (some steps pass, the new key step doesn't). This is a **re-scope bar-raise, NOT a REGRESSION** (the code is unchanged and still works; the goalpost moved) — do not emit a REGRESSION verdict for it, and do not let it carry on its old `passing` status on faith. Also added J-32 (newly tracked `failing`). Practically: after any goal.md edit, re-read the Must-have journeys and re-check every previously-passing journey against the NEW acceptance, and confirm new J-IDs are added to journey-history (the goal had grown to J-32 while history still listed J-01..J-31).
**Applies to:** any iteration whose `docs/goal.md` was edited since the last eval (operator re-scope / `--resume` after STALLED); any journey the iter spec lists as a *future* target while journey-history still marks it `passing`; the goal-evaluator's GOAL_ACHIEVED gate (must count against the current, possibly-raised, acceptance bar).

## iter-18 — 2026-06-04T10:27:00Z

**Verdict:** CONTINUE
**Lesson:** The J-26 composite percentile-rank blend is "non-empty" but on a *cancelling* selection it
honestly collapses to the whole pool, NOT a differentiated cohort: when the same factor is added at both
`top` and `bottom` (the opposing-extremes fixture), each observation's two oriented ranks (`frac` and
`1−frac`) average to a flat ~0.5, so `_quantile_cutoff` includes everyone → `composite.n == pool_n` with
`mean == baseline.mean` (UT-08: composite n=1218 = baseline, while `strict_overlap` correctly shows n=0/NA).
This is the mathematically honest "no net signal" answer and it satisfies the bar-raise (non-empty + clears
`min_sample`), but it means **"composite non-empty" does NOT imply "composite differentiated from
baseline"** — judge the composite's value on *sensible* (non-cancelling) selections, where it yields a real
~`composite_fraction·pool_n` cohort distinct from baseline (default quintile → n≈244 vs baseline 1217,
+1.21% vs +2.03%). Don't mistake `composite n == baseline n` for a bug.
**Applies to:** any iter touching `compute_factor_combination` / the `_composite_scores` blend, and any
evaluator judging J-26 or the J-32 as-of-mode applied to the combination cohort — assert differentiation on
a non-cancelling selection, not just `n > 0`.

## iter-19 — 2026-06-04T13:30:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** GOAL_ACHIEVED can be correct even with journeys still in `failing` status — when the operator-authored `docs/goal.md` explicitly re-scopes specific journeys as non-halting/non-vetoing. Here J-22/J-23/J-24 stayed `failing` (externally Yahoo-429 data-walled) yet the goal text (commit d723133, lines 99-103 + 755-765) twice states they "MUST NOT halt the loop, drive a STALLED verdict, or veto GOAL_ACHIEVED." That project-specific instruction overrides the goal-evaluator's generic "do not mark GOAL_ACHIEVED if any journey is failing" guardrail. The correct gate became "every *buildable* journey passing (29/29) + no critical anti-goal + coherence not FAIL," not "all 32 passing." Confirm the carve-out is in goal.md itself (not just an evaluator's prior note) before treating blocked journeys as non-vetoing.
**Applies to:** any goal-mode session whose `docs/goal.md` declares a subset of must-have journeys "non-halting" / data-dependent; any final GOAL_ACHIEVED decision where some journeys remain blocked — read the goal's own halting semantics rather than applying the generic all-journeys-passing rule.

## iter-20 — 2026-06-04T22:15:28Z

**Verdict:** CONTINUE
**Lesson:** A post-GOAL_ACHIEVED "finalization" iteration is a trap when the operator re-scoped `docs/goal.md` between iterations. Here commit d3e5076 added three new Must-have journeys (J-33/34/35) at 21:14; the goal-decomposer wrote a "session-complete, no-code" spec 93 s later (21:15) that ignored them, and dev/review/QA/coherence all dutifully reported "29/29 complete." The evaluator must ALWAYS evaluate against the *current* goal.md (read it fresh, diff for journeys absent from journey-history) and never inherit the iter spec's "buildable set complete" framing. Two corroborating traps: (1) the dev handoff *claimed* the Data Manager already had the new capabilities (source picker / resumable import / expand-universe) — it was restating the goal vision, not the code; the actual `JobCreate`/`JOB_KINDS`/config proved them absent. (2) "all required-still-passing journeys green" says nothing about newly-added journeys. Confirm new/claimed capabilities exist in source before trusting any "complete" verdict.
**Applies to:** any iteration immediately following a `docs/goal.md` re-scope commit; any "finalization" / post-GOAL_ACHIEVED iteration; any time a dev handoff asserts a capability without a code diff to back it. Cross-check: # of journeys in goal.md vs # tracked in journey-history.json.

## iter-21 — 2026-06-05T00:30:00Z

**Verdict:** CONTINUE
**Lesson:** A "secret-never-persisted" unit test that injects a *mocked* provider raising a *sanitized* error will pass green while the *real* client leaks the key — here `_http.py:42` wraps `str(httpx.HTTPStatusError)`, which embeds the full request URL incl. `?token=<key>`/`?apikey=<key>`, into `JobProgress.errors[]` → `GET /api/data/jobs/{id}` → the `/data` job card. The full backend suite (502 passed) never exercised the real httpx-URL-in-exception path, so dev+review+coherence all PASSED and only live QA/browser-QA caught it. When a key travels as a URL query param, the secret can leak through any error string built from the exception — grep the live job-status RESPONSE and the rendered UI, not just the DB/`/api/data`; and any "absent from X" anti-goal test MUST drive a *real* error (key-in-URL), not a sanitized mock. (Matches MEMORY `httpx-error-leaks-url-query-key`.)
**Applies to:** any iter adding/extending an external HTTP client that carries a credential (esp. as a URL query param), or asserting a secret is "never echoed/persisted" — verify with a real transport error through the full job-status→UI path, prefer header auth or a redacted-URL error message, and treat error strings as untrusted-for-secrets before serving. Directly relevant to iter-22 (J-34 chunked import threads the same key + surfaces richer per-chunk errors → inherits this leak unless fixed first).

## iter-22 — 2026-06-07T09:50:00Z

**Verdict:** CONTINUE
**Lesson:** Adding any new `table=True` model (here `import_checkpoints` for J-34) RED-fails `tests/test_db.py::test_create_all_produces_expected_tables`, which asserts `set(SQLModel.metadata.tables.keys()) == ITER1_TABLES | SNAPSHOT_TABLES | WATCHLIST_TABLES` (a hardcoded expected set at `test_db.py:37`). This is a stale schema-snapshot assertion, NOT a product defect — but it flips the whole-suite exit code to 1 and drove the QA agent to a FAIL verdict while dev/review/browser-qa were all green. Any iter that adds a table MUST update that expected set (add the new table name) in the same change, or the next evaluator has to reconcile a misleading suite-RED. The decisive evidence lives in the authoritative `ui-test-results.md` (browser-qa-agent), which can say PASS even when the QA report says FAIL/SKIPPED — read it directly, do not take the QA verdict at face value.
**Applies to:** any iter adding a new `table=True` SQLModel (fix `tests/test_db.py` expected-tables set in the same commit); any evaluator seeing a QA FAIL with dev/review green (check whether the single RED is a schema-snapshot/maintenance assertion vs a real product test).

## iter-22 — 2026-06-07T09:50:00Z (key-leak closure)

**Lesson:** The iter-21 session-key leak was finally closed AND proven by driving a REAL httpx error through the real `_http.py` path — both in a unit test (`httpx.MockTransport` + a real `httpx.Client` injected into Tiingo/Finnhub/AlphaVantage) and live in the browser (a real Tiingo HTTP 403, key-in-URL, sentinel `SENupKEY123` absent from the error). The earlier mocked-provider "key-never-persisted" test passed green for an entire iteration while the real client leaked, because the test's `_FakeResponse` hard-coded `http://x` (no key) as the request URL — `str(httpx.HTTPStatusError)` only embeds the credential when the exception carries a real `.request.url` with the query params. One honest, accepted residue remains and was deliberately NOT penalized (per the iter-22 spec): the third-party `httpx` library emits its own INFO `HTTP Request: GET <url-with-key>` line — that is the library's logger, not the app's error/persist/response path, and httpx INFO logging is off by default here.
**Applies to:** any iter touching `apps/backend/app/data_providers/` error handling or asserting a secret is absent from an error/response — assert against a REAL provider-client error (key-in-URL via MockTransport), never a sanitized mock; grep the live `GET /api/data/jobs/{id}` response + job card + checkpoint + run history for the sentinel, not just the DB (MEMORY `httpx-error-leaks-url-query-key`).
