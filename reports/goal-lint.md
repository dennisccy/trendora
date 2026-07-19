# goal-lint report — docs/goal.md

Run: 2026-07-19 · deterministic exit: 0 · semantic findings: 8

## Deterministic lint (goal_lint.py)
clean (exit 0, no output)

## Semantic findings

### Not independently runnable — line 204
> 1. Run an ingest job (fetch or backfill) that adds at least one new trading date
- **Problem:** On the current DB the newest trading date (2026-07-17) is already snapshotted (ground truth, line 298) and the product is offline, so `fetch` can never "add a new trading date"; a historical backfill *can*, but then step 2's freshness assertions on the **latest-keyed** aggregates (dashboard latest-date payload, market phase "for the latest as-of") are vacuous — nothing changed for that key — leaving the browser agent to guess which reading to enforce and the evaluator free to accept a hollow pass.
- **Suggested rewrite:**
  ```
  1. On `/data`, run a backfill covering exactly one unsnapshotted historical trading day
     (e.g. 2026-05-15 — any day `/scanner-runs` lacks; offline, `fetch` finds no new bars
     and is expected zero-work, so `backfill` is the ingest kind under test)
  2. Immediately after completion, assert (a) the aggregates keyed by the ingested as-of
     serve the new state from storage — `/scanner-runs` lists the date and its leaderboard
     renders the stored snapshot; market phase for that as-of responds from
     `market_phase_cache` without compute-on-read — and (b) the persisted run record lists
     which inventory aggregates its finalize hook refreshed (snapshot, coverage, membership
     timeline, market phase, research hot keys), and each latest-keyed aggregate still
     serves its stored value with no recompute triggered by the job
  ```
  If the team wants the *full* latest-as-of refresh demonstrated, add an explicit setup step that removes only the tip date's **snapshot** (never bars — unrecoverable offline) before re-ingesting it.

### Unobservable acceptance phrased measurably — line 189
> 5. Assert a persistent backend logfile exists and contains the boot and the crash events
- **Problem:** A SIGKILLed process writes nothing — under a true simulated crash there is no "crash event" in the log to see, so a literal evaluator fails a *correct* implementation (and a lenient one accepts anything); the observable evidence of a crash is the abruptly-truncated log, not a crash line.
- **Suggested rewrite:**
  ```
  5. Assert the persistent backend logfile (path documented in the dev handoff) contains the
     boot events; after the simulated crash, assert the log ends abruptly — boot entries
     present, no clean-shutdown entry — so the crash is evidenced by the truncated log plus
     the UI's unreachable presentation (a killed process writes no crash line)
  ```

### Journey contradictions (same metric, different denominators, no canonical pin) — line 117
> 3. Assert the job summary reports `dates_total` = 19 (every trading day in the range —
- **Problem:** J-01 pins `dates_total` to **trading** days (19 of a 28-calendar-day range) while J-02 step 2 requires exclusion counts that "sum to the days in the range" (**calendar** days — the weekend span's 2 are non-trading), and no Product Shape canonical value pins the run-summary schema, so the two journeys can be satisfied by two different, mutually inconsistent summary shapes on the same `/data` surface.
- **Suggested rewrite** (add under `### Canonical values (single source of truth)`, and change J-02 step 2 to "…sum to the calendar days in the range"):
  ```
  - **Backfill run-summary contract** — one persisted record per run: `dates_total` counts
    trading days in the requested range; the per-date exclusion breakdown partitions every
    calendar day in the range (non-trading / already-snapshotted / error-other), so
    non-trading + `dates_total` = calendar days and `snapshots_created` + already-snapshotted
    + error-other = `dates_total`. J-01 (19 trading of 28 calendar days) and J-02 (0 trading
    of 2) both read this one record.
  ```

### Steps that require guessing — line 180
> 1. Restart the backend via the documented start script; immediately poll `GET /api/health`
- **Problem:** "The documented start script" is unpinned while the habitual runner is `dev.sh` and J-06 explicitly bans `dev.sh` for measurements — the same ≤ 5 s boot budget row in `reports/perf-budgets.md` could be measured under dev mode here and prod mode in J-06, producing incomparable numbers for one canonical budget.
- **Suggested rewrite:**
  ```
  1. Restart the backend via `scripts/start-backend.sh` (prod mode — never `dev.sh`,
     matching J-06's measurement conditions); immediately poll `GET /api/health`
  ```

### Unobservable acceptance phrased measurably (timing) — line 183
> 3. While any background loading runs, assert the top-bar badge shows an explicit
- **Problem:** On the target architecture the warm boot finishes in seconds and steps 1–2 have the agent polling `curl`, not watching the browser — by the time it opens the page the initializing window is gone, so the assertion is conditional-and-flaky ("while any… runs") and QA will either miss it or wave it through unobserved.
- **Suggested rewrite:**
  ```
  3. With the frontend already open, restart the backend again; poll `GET /api/health` at
     ≤ 250 ms from process start and assert at least one pre-ready response carries the
     boot phase and progress n/m; assert the top-bar badge polled in that same window shows
     the same phase detail as an explicit initializing state — never a bare "Backend
     unavailable". Evidence: the captured pre-ready health payload plus a badge
     screenshot/DOM assertion from the same window
  ```

### Journey contradictions (cross-journey interference) — line 186
> 4. Kill the backend process (simulated crash); assert the UI transitions to an explicit
- **Problem:** J-03 deliberately leaves a multi-hour chunked job running beyond its QA window; when J-04's kill lands mid-flight, no journey defines the persisted run's post-crash presentation, so `/data` can show a forever-"running" row with no living process — a silent dishonest state in the one cycle whose thesis is honest self-reporting.
- **Suggested rewrite** (add as J-04 step 6, or an acceptance bullet):
  ```
  6. Restart the backend; on `/data` assert any job that was mid-flight at the kill now
     shows an explicit interrupted/error state with its last persisted progress — never a
     still-"running" row with no living process
  ```

### Mergeable journey pair (advisory) — line 138
> - **J-02: No silent zero-work jobs**
- **Problem:** J-01 and J-02 drive the same `/data` backfill form + history panel with the same risk class (job-engine honesty over the same persisted run record); as separate journeys they buy the engine two planning/verification units where one lean iteration covers both. Advisory only — splitting is never an error.
- **Suggested rewrite** (extend J-01 with the absorbed steps + one acceptance bullet per absorbed outcome; retire J-02 — never reuse its id):
  ```
  5. Start a second backfill over the weekend-only span 2026-05-02 → 2026-05-03; after
     completion assert the summary reports 0 snapshots created with a per-reason breakdown
     (2 non-trading days) consistent with the run-summary contract
  6. Reload the page; assert the persisted history panel still lists both runs with the
     same outcomes and reasons — never "no job started this session"
  7. Assert the zero-work outcome renders as an explanatory state, visually distinct from
     the productive run's success presentation
  Acceptance (added):
  - **Zero-work honesty:** the weekend-only run shows 2 non-trading / 0 eligible, persisted
    across reload, and is never rendered as unexplained success.
  ```
  Keep J-03 separate — different blast radius (config/validation removal + long-running execution).

### Risky surface with no anti-goal coverage — line 255
> ## Anti-goals
- **Problem:** The journeys run ingest jobs named `fetch` and the Constraints pin "offline against the committed seed", but no **anti-goal** (the veto class the evaluator enforces) bounds external network calls or paid data providers — an iteration could wire a live provider into the fetch path without tripping any veto.
- **Suggested rewrite** (add as an Anti-goals bullet):
  ```
  - **Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against
    the committed seed / local provider fixtures — no live external network calls or paid
    data services may be introduced without an explicit goal.md amendment. *(critical)*
  ```

## Summary

Structurally clean and unusually strong — canonical values pinned, acceptance bullets follow the proven four-class house style, dates internally consistent (19 trading days verified). The 8 findings are all about QA determinism: the highest-impact fix is **J-05 step 1/2** (line 204), which as written is either impossible (`fetch` offline) or vacuous (historical backfill vs latest-keyed aggregates) and is the journey most likely to produce a hollow pass or spurious fail; the run-summary denominator pin (line 117) is the cheapest insurance against the classic same-number-differs-across-pages failure. Side note: journeys cite anti-goals by implicit position ("#8", "#1/#4/#6") — unnumbered bullets make those references fragile to any future insertion; consider labeling them (`AG-1:` …).
