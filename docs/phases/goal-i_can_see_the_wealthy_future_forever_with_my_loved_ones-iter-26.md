# Goal Iteration 26 — Expand-universe market-cap fetch authenticates with Yahoo (cookie + crumb); systemic auth failure pauses resumable (J-84)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 26
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-84
- **Required-still-passing journeys:** J-35, J-34, J-38, J-33, J-39, J-69, J-08, J-18, J-06, J-40, J-41, J-66, J-59
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere; the default seed path requires none, and any live-provider key is read only from the environment.
  - **Import keys are env-or-session, never persisted.** The import provider catalog and each provider's key-requirement + env-var name MUST come from config (no hardcoded provider list in code); a provider key MUST be read from the environment, or — if the user pastes one into the import UI — held **in memory for that run only**, **never written to disk, the run log, the DB, or any committed file, and never echoed back** in any response. The import's date inputs are **job parameters, not a second date control** (the single global as-of switcher stays the only date selector).
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Live fetch is real-data-only.** The Data Manager MUST use the config-selected live provider to fetch real EOD bars; on a provider failure it MUST surface an explicit error and MUST NOT synthesize prices to fill a gap or force a successful run.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Exactly one date selector** — the global as-of control drives every date-scoped page; the import/expand/remove dates are job/action parameters, never a second date state.

## GOAL

The Data Manager Expand-universe job's market-cap reference authenticates with Yahoo via the no-key cookie + crumb flow (so real caps return instead of HTTP-401-omitting all 548 candidates), and a systemic auth/limit failure pauses the job resumable instead of silently recording the whole universe as empty.

## BACKGROUND

This is the next queued buildable Must-have after iter-25 shipped J-83 (passing). The iter-25 evaluator and last coherence verdict (COHERENCE-PASS, no consolidation owed) both recommend running **J-84 at FULL depth** as the cleanest of the three remaining queued journeys (J-84/J-85/J-86), because it touches the live `YahooProvider` market-cap path + the J-34/J-35 resumable-import machinery, so the full ~790-test pytest suite becomes the gate. The root cause is concrete and already source-verified: `apps/backend/app/data_providers/yahoo_provider.py:get_market_cap` issues `GET /v7/finance/quote?symbols=…` with NO cookie/crumb → Yahoo returns HTTP-401 → `_http._provider_error` maps non-429 statuses (incl. 401) to `ProviderUnavailableError`, so `_screen_one_candidate` records every candidate `market_cap_fetch_failed` → 0 passers of 548. The committed `apps/backend/scripts/screen_universe.py` already contains the working runbook to port (`_yahoo_crumb` at `screen_universe.py:296` — visits `finance.yahoo.com` for the cookie, then `/v1/test/getcrumb` with a browser-like UA; `fetch_market_caps` at `:308` — batched `/v7/finance/quote?...&crumb=…`). The expand loop ALREADY pauses resumable on `RateLimitError` (`data_manager.py:_run_expand_screen` ~line 1922), so the systemic-failure leg is a classification change (whole-batch auth/limit failure → the resumable-pause signal), not new pause machinery. **J-84 is partly data-dependent / non-halting** (goal.md:2186–2192): the cookie+crumb auth, batched-quote, and pause-resumable-on-systemic-failure legs are buildable + fully testable OFFLINE with an injected provider stub (returns caps, or raises 401/429); only an actual successful REAL Yahoo screen (and thus J-22 fully green via J-35) is data-gated and is recorded honestly blocked-NA — it must NOT halt, drive STALLED, or veto GOAL_ACHIEVED.

## IN SCOPE

### Backend
- [ ] Port the committed `screen_universe.py` cookie+crumb runbook into `apps/backend/app/data_providers/yahoo_provider.py` `YahooProvider.get_market_cap` (and a batched helper if cleaner): acquire the no-key Yahoo cookie by visiting `finance.yahoo.com`, then obtain a crumb from `/v1/test/getcrumb` with a browser-like User-Agent, then call `/v7/finance/quote` with `crumb=…`. Acquire the cookie+crumb ONCE per provider session (not per symbol) and reuse it across the batch; prefer batching multiple symbols per quote request (a modest config-sourced batch size — no magic-number literal; reuse the `screen_universe.py` constant pattern or a `config.data_manager` knob). A symbol with no `marketCap` field still returns `None` (honest absent → `no_market_cap` omission, never fabricated). Parse failures still raise `ProviderUnavailableError` from a REDACTED URL (the existing `_http.fetch_json` redaction is preserved — no credential/cookie/crumb in any error string).
- [ ] Classify a **systemic** market-cap auth/limit failure (the whole cap batch failing — persistent 401 or 429 across all candidates, including the cookie/crumb acquisition itself failing) as a pause-resumable signal so it flows through the EXISTING `RateLimitError` → `_run_expand_screen` resumable branch (`data_manager.py` ~line 1922). The expand job sets status `resumable` with an honest operator message (e.g. "market-cap provider auth failed — Resume to retry"), records the durable checkpoint (J-59), and DOES NOT record all candidates omitted. A genuinely per-candidate absent/sub-threshold cap stays a normal honest omission (`no_market_cap` / threshold reason) — only a whole-batch systemic failure pauses. Distinguish "systemic" from "one capless symbol" without recomputing anything (e.g. a persistent 401/429 on the shared cookie/crumb acquisition or on the batched quote is systemic; a present-200 response missing `marketCap` for one symbol is a per-candidate omission).
- [ ] Resume after a systemic-failure pause continues with ZERO duplicate fetch (the OHLCV fetch checkpoint + completed-stages, J-59, are unchanged; the screen step re-runs from the durable checkpoint) and survives a backend restart — assert via the existing resumable-import test machinery with an injected provider.
- [ ] No new endpoint, no new stored column, no second fetch/screen path — reuse `screen_reasons` (the ONE screen predicate), the existing `data_manager` import engine, and the existing `DataProviderRun`/`import_checkpoints` job-control. The cookie/crumb are acquired at runtime and are NEVER stored, logged, committed to disk, written to the DB/run log, or echoed in any API response.

### Frontend (if applicable)
- [ ] No required code change. The existing `/data` Unfinished-imports / job-card surface (J-38/J-66) already renders a `resumable` job with its Resume affordance and the honest job message; confirm the systemic-auth-failure pause renders as a resumable job with the operator message (not a silent "0 members" success). If the job message is plumbed verbatim from the backend payload, this is verification-only; do NOT introduce a second status path or a new component.

### New user-facing capability
An operator can run an Expand-universe job against the Yahoo-capable source and have it actually screen real market caps (cookie+crumb authenticated) rather than silently omitting every candidate; if Yahoo systematically rejects auth, the job pauses with a clear Resume affordance instead of falsely reporting an empty universe.

### New information displayed
The expand job card / Unfinished-imports row shows an honest `resumable` state with a "market-cap provider auth failed — Resume to retry" message on systemic failure (instead of "0 passers, 548 omitted"). On success against a reachable provider, real member counts + real per-member caps in `universe.json` (data-gated leg).

### New user actions
None new — the existing Resume action (J-38) on the paused expand job.

### UI surface changes
None new — the existing `/data` Data Manager home (job card + Unfinished-imports panel).

### Product surface delta
The expand-universe operator flow becomes trustworthy: an auth outage is no longer mistaken for "the universe is empty"; with a reachable provider it would populate the ~500-name universe (the path that unblocks J-22 via J-35).

### Blueprint conformance
No new surfaces. J-84 lands on the existing **Data Manager `/data`** Information-Architecture home (the expand job + Unfinished-imports already live there). The Data Contract is updated additively (this iteration, already applied): the **"Universe membership + selection screen"** row gains the J-84 cookie+crumb-auth annotation, and the **"Import job control …"** row gains the J-84 systemic-failure-pause-resumable annotation. No nav-skeleton change → no re-approval requested.

### Data-contract additions
None — no NEW displayed value and no new endpoint. J-84 is a correctness fix to HOW the existing universe-membership market-cap reference is fetched (cookie+crumb auth) and HOW a systemic cap-fetch failure is classified (pause resumable). The single screen rule (`screen_universe.screen_reasons`), the `GET /api/data` universe/job payloads, and the `GET /api/methodology` universe rule are unchanged. The market cap remains REAL or absent — never fabricated.

## OUT OF SCOPE

- J-85 (confirm-gated regenerate-from-scratch snapshot rebuild + coverage diagnostic) — separate FULL iteration after J-84.
- J-86 (max-drawdown columns everywhere; adds a `forward_returns.max_drawdown` column) — separate FULL iteration after J-84/J-85.
- Any actual real-network Yahoo fetch as an acceptance gate. The host's live Yahoo market-cap egress is rate-limited (MEMORY: data-provider-access-constraints) — the J-22 "≥500 real members" leg stays honestly blocked-NA / non-halting; do NOT block this iteration on a live screen.
- Any change to the OHLCV `get_daily` fetch path, the `screen_reasons` thresholds, or the committed price seed.
- Re-committing regenerated artifacts into the Capability-34 snapshot seed.

## DEFINITION OF DONE

- [ ] Target journey J-84 passes via browser-qa-agent for its OFFLINE-verifiable legs (auth path exercised with an injected provider; systemic-failure → resumable pause rendered on `/data`; Resume → zero-duplicate-fetch). The real-Yahoo-screen leg (J-22) is recorded honestly blocked-NA / non-halting if the provider is walled.
- [ ] Required-still-passing journeys remain green — especially J-35/J-34/J-38/J-59 (the import/resumable machinery J-84 rides), J-39/J-69 (seed-safe removal untouched), J-08 (snapshot immutability untouched), J-06/J-18 (single source / single date selector untouched), J-40/J-41 (boot + readiness — the backend is restarted to pick up the change and must boot Ready cleanly).
- [ ] No anti-goal violation introduced — verify by grep: NO cookie/crumb/secret string is written to disk, the DB, a run log, a committed file, or any API response; the crumb never appears in an error message (the `_http` redaction holds); the batched-quote size + any new knob come from config / a named constant (no magic-number literal in calc/engine code).
- [ ] Unit/integration tests pass; no regressions. The FULL backend pytest suite is the standing GOAL_ACHIEVED gate and MUST end `0 failed, EXIT_CODE=0` — hand it to the pump nohup-async; gate the next evaluator on the FLUSHED terminal summary line, NEVER on the in-flight stream (iter-11 lesson).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26-dev.md`.

## TESTING REQUIREMENTS

- **Browser (by ID):** J-84 — on `/data`, run an Expand-universe job against the Yahoo-capable source with an injected/stubbed cap provider (a) returning caps → real passers screened (non-empty members, real caps); (b) raising a systemic 401/429 → the job pauses `resumable` with the operator message (NOT "0 of 548 omitted"), the Unfinished-imports row offers Resume, and Resume continues with zero duplicate fetch and survives a restart. Plus the required-still-passing smoke: J-35/J-34/J-38 (the expand + chunked + unfinished-imports surfaces), J-39/J-69 (remove untouched), J-18 (single date selector unchanged on `/data` — import/expand dates are job params, never a second date state). NOTE for the QA dispatch: pass the goal.md J-84 acceptance text verbatim and md5sum the evidence dir FIRST (recurring shared-bytes / blank-capture smell — iters 3/5/7/9/10/13/15/17/18/25); the `/data` job-card surface is screenshot-fragile (live job state), so corroborate via the live job payload + the durable `data_provider_runs` / `import_checkpoints` rows when a capture degrades (iter-3/iter-15 pattern). The alpha_vantage `demo`-key throttle technique (MEMORY) can drive a real resumable pause for the live-evidence leg if an injected stub is not wired into the running app.
- **Unit/integration (code paths that MUST have tests):**
  - `YahooProvider.get_market_cap` cookie+crumb flow with an injected `httpx` client/transport: asserts the cookie is fetched (`finance.yahoo.com`) then the crumb (`/v1/test/getcrumb`) then `/v7/finance/quote` is called WITH `crumb=…` (batched); a 200 with `marketCap` → real float; a 200 without `marketCap` for a symbol → `None` (absent, not fabricated); the cookie/crumb fetched once and reused across the batch.
  - The expand systemic-failure classification: an injected provider raising persistent 401/429 (on the cookie/crumb acquisition or the batched quote) → `_run_expand_screen` sets status `resumable` and does NOT record all candidates omitted; a per-candidate present-but-capless symbol → normal `no_market_cap` omission. Drive the REAL `_run_expand_screen` / expand orchestration entry point, not a hand-rolled stand-in (iter-15 lesson: a regression test must hit the production orchestration path).
  - Resume after the systemic-failure pause: zero duplicate provider calls (counting-provider assertion, the J-59 pattern), survives a restart, durable checkpoint correct.
  - Secret-redaction guard: the crumb/cookie value never appears in the job `errors[]`, the job message, the `DataProviderRun`/`import_checkpoints` rows, or any `GET /api/data*` response (grep the job-status response, not just the DB — MEMORY: httpx-error-leaks-url-query-key).
- **Error cases that MUST be rejected / handled honestly:** a systemic 401 → resumable pause, NOT all-omitted and NOT a fabricated cap; a single symbol missing `marketCap` → honest omission, never a fabricated cap; a non-cap-capable source for an expand job → the existing explicit `supports_market_cap` 4xx rejection (J-35) unchanged; a parse-shape failure → `ProviderUnavailableError` from a redacted URL.

## NOTES

- **Depth = full** because J-84 touches backend provider + import-engine code, requires new offline tests beyond a browser smoke, and the full ~790-test pytest suite is the standing GOAL_ACHIEVED gate. This matches the iter-25 evaluator's explicit FULL recommendation; the last coherence verdict was COHERENCE-PASS so no consolidation pass is owed.
- **Lessons applied (episodic memory):**
  - *Suite-gate handling (iters 2/11):* the full backend suite is ~35–55 min and a dev-turn background run does NOT survive the turn ending — hand it to the pump (nohup-async) and gate the evaluator on the flushed `0 failed` line; NEVER block the evaluator dispatch on the in-flight suite (the failure that aborted iter-11's first run).
  - *Additive served field tripping a blanket guard (iters 20/23/24):* J-84 adds NO served field, so the `test_api_*_equals_engine_output` byte-equality guards should not fire — but if the expand/job payload shape changes at all, grep `apps/backend/tests` for the affected payload's equality/expected-shape asserts and update them in THIS iteration.
  - *New table/column guards (iters 12/20):* J-84 adds NO new table or column — do NOT touch `db.py` `_ADDITIVE_COLUMNS` or `test_db.py` expected-tables. (Those belong to the later J-86 iteration.)
  - *Secret leak via redacted URL (MEMORY: httpx-error-leaks-url-query-key + iter-21 leak fix):* the crumb rides as a query param on `/v7/finance/quote?...&crumb=…` — verify the existing `_http._redacted_url` redaction strips it from every error string, and that no error/job message embeds the raw quote URL. Grep the job-status RESPONSE, not just the DB.
  - *Regression test hits production path (iter-15):* drive the systemic-failure pause through the REAL `_run_expand_screen` / expand orchestration, not a stand-in.
  - *Browser env + evidence hygiene (iters 17/18/25):* confirm backend :8835 / frontend :3835 / Chrome :9222 reachability before QA; md5sum the evidence dir first; the `/data` job card is fragile (live state) — corroborate paused-resumable via the live job payload + the durable `data_provider_runs`/`import_checkpoints` rows when a capture degrades. Never upgrade J-84 to passing without positive evidence of the resumable-pause + zero-dup-resume legs.
  - *Dev-server cleanup by port (MEMORY):* this is a multi-project machine — restart backend/frontend by PORT, never a broad `pkill -f`.
- **Data-dependency honesty (goal.md:2186–2192, quoted in BACKGROUND):** the real Yahoo screen (J-22's ≥500 real members) is provider-walled on this host (MEMORY: data-provider-access-constraints). Record that single leg as honestly blocked-NA / rate-limited — it MUST NOT halt the loop, drive a STALLED verdict, or veto GOAL_ACHIEVED. J-22/J-23/J-24 remain non-vetoing blocked-NA.
- **Blueprint state:** the two additive Data-Contract annotations (universe-membership cookie+crumb auth; import-job-control systemic-failure pause) are already applied to `runs/goal-session-<sid>/state/blueprint.md`. No nav-skeleton change → no `blueprint.reapproval-requested` written.
- After J-84 lands green with a GREEN full suite, COHERENCE-PASS, and zero regression, the remaining queued buildable Must-haves are J-85 then J-86 (each FULL). GOAL_ACHIEVED becomes appropriate once all three pass with the full suite green (J-22/J-23/J-24 staying honestly blocked-NA, non-vetoing).
